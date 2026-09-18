#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Claude 看板 — 收集本機 Claude 工作階段狀態，產生 claude-status.json 並推送到 GitHub。

在 Mac mini 上由 launchd 每分鐘執行一次（見 com.allentw.claude-monitor.plist）。
只讀取本機狀態檔與逐字稿的中繼資料，不修改任何 Claude 的檔案。

隱私：預設 detail=standard，只發佈中繼資料（工作階段名稱、狀態、專案路徑、
工具名稱、token 用量）。對話內容不會被發佈，除非明確設成 detail=verbose。
發佈目標 SumerTWRobotTest1 是公開的 GitHub Pages 站，密碼閘只是裝飾。
"""

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

MONITOR_VERSION = "1.0.0"

HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
SESSIONS_DIR = CLAUDE_DIR / "sessions"
PROJECTS_DIR = CLAUDE_DIR / "projects"
APP_SUPPORT = HOME / "Library" / "Application Support" / "Claude"
DESKTOP_GLOBS = [
    "claude-code-sessions/*/*/local_*.json",
    "local-agent-mode-sessions/*/*/local_*.json",
]

REPO_DIR = Path(os.environ.get(
    "CLAUDE_MONITOR_REPO", "/Volumes/FCP 512GB/Claude/SumerTWRobotTest1"))
OUT_JSON = REPO_DIR / "claude-status.json"
STATE_FILE = HOME / ".claude-monitor" / "state.json"

# minimal = 只有名稱/狀態/時間；standard = 加上路徑、分支、工具名稱、token；
# verbose = 再加上最後一則訊息的摘錄（會把工作內容發佈到公開網頁，預設關閉）
DETAIL = os.environ.get("CLAUDE_MONITOR_DETAIL", "standard")

# 收集每分鐘做一次（很便宜，純本機），但推送要節制：GitHub Pages 每次推送都要重新
# 建置，每次 35-65 秒，而且分支式的舊流程有「每小時 10 次建置」的軟性上限。推太快
# 會排隊、互相蓋掉，還會排擠到發報告時的建置。所以內容有變也至少隔這麼久才推。
MIN_PUSH_SECONDS = int(os.environ.get("CLAUDE_MONITOR_MIN_PUSH", "180"))
# 內容沒變也至少每 HEARTBEAT_SECONDS 推一次，讓網頁能分辨「沒事發生」和「收集器掛了」
HEARTBEAT_SECONDS = int(os.environ.get("CLAUDE_MONITOR_HEARTBEAT", "600"))
PUSH = os.environ.get("CLAUDE_MONITOR_PUSH", "1") != "0"

DESKTOP_WINDOW_HOURS = 24      # 桌面版工作階段只列出這段時間內有活動的
STALL_MINUTES = 10             # busy 但這麼久沒有新紀錄 → 標成「停滯」
TAIL_BYTES = 262144            # 讀逐字稿尾端的位元組數
BACKLOG_CAP = 8 * 1024 * 1024  # 首次看到的逐字稿超過這個大小就不回頭全解析
TEXT_LIMIT = 160               # verbose 模式的訊息摘錄長度


# ---------------------------------------------------------------- 小工具

def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_ms(ms):
    if not ms:
        return None
    try:
        return iso(datetime.fromtimestamp(ms / 1000.0, timezone.utc))
    except (ValueError, OverflowError, OSError):
        return None


def run(args, cwd=None, timeout=20):
    """跑一個指令，回傳 (returncode, stdout)。失敗不丟例外。"""
    env = dict(os.environ)
    env["LC_ALL"] = "C"          # 日期格式要固定，中文 locale 的 ps 沒辦法解析
    try:
        p = subprocess.run(args, cwd=str(cwd) if cwd else None, timeout=timeout,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        return p.returncode, p.stdout.decode("utf-8", "replace").strip()
    except Exception as exc:  # noqa: BLE001 - 收集器不該因為子程序失敗而中斷
        return 1, str(exc)


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return default


def clip(text, limit=TEXT_LIMIT):
    if not text:
        return None
    flat = " ".join(str(text).split())
    return flat if len(flat) <= limit else flat[:limit - 1] + "…"


# ---------------------------------------------------------------- 行程

PID_START_TOLERANCE = 120        # 秒；行程啟動時間和狀態檔差這麼多就當成 PID 被回收了


def process_alive(pid, started_ms):
    """PID 還在，而且啟動時間吻合（避免 PID 被回收後把別的行程當成 Claude）。"""
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:  # noqa: BLE001
        return False
    if not started_ms:
        return True
    code, out = run(["/bin/ps", "-o", "lstart=", "-p", str(pid)], timeout=5)
    if code != 0 or not out:
        return True                # 問不到就相信 kill(0)，不要誤殺還活著的階段
    try:
        actual = time.mktime(time.strptime(out, "%a %b %d %H:%M:%S %Y"))
    except ValueError:
        return True                # 日期格式不如預期，同上
    return abs(actual - started_ms / 1000.0) <= PID_START_TOLERANCE


# ---------------------------------------------------------------- 逐字稿

def find_transcript(session_id):
    if not session_id:
        return None
    for path in PROJECTS_DIR.glob("*/%s.jsonl" % session_id):
        return path
    return None


def read_tail_records(path, limit=300):
    """讀逐字稿尾端並解析成紀錄；單筆紀錄很大時自動加大讀取範圍。"""
    for window in (TAIL_BYTES, TAIL_BYTES * 8):
        try:
            size = path.stat().st_size
            with open(path, "rb") as fh:
                if size > window:
                    fh.seek(size - window)
                blob = fh.read()
        except OSError:
            return []
        lines = blob.split(b"\n")
        if size > window and len(lines) > 1:
            lines = lines[1:]          # 開頭那行八成被切斷了
        records = []
        for line in lines[-limit:]:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line.decode("utf-8", "replace")))
            except ValueError:
                continue
        if records:
            return records
    return []


def summarize_transcript(path):
    """從逐字稿尾端取出「現在在做什麼」。"""
    info = {
        "last_activity": None, "model": None, "effort": None,
        "git_branch": None, "cwd": None, "version": None,
        "last_tool": None, "last_tool_at": None,
        "context_tokens": None, "last_text": None, "last_prompt": None,
    }
    for rec in read_tail_records(path):
        ts = rec.get("timestamp")
        if ts:
            info["last_activity"] = ts
        if rec.get("gitBranch") and rec["gitBranch"] != "HEAD":
            info["git_branch"] = rec["gitBranch"]   # 非程式庫目錄會回報 HEAD，沒意義
        if rec.get("cwd"):
            info["cwd"] = rec["cwd"]
        if rec.get("version"):
            info["version"] = rec["version"]
        msg = rec.get("message")
        if rec.get("type") == "assistant" and isinstance(msg, dict):
            info["model"] = msg.get("model") or info["model"]
            info["effort"] = rec.get("effort") or info["effort"]
            usage = msg.get("usage") or {}
            total = sum(int(usage.get(k) or 0) for k in
                        ("input_tokens", "cache_creation_input_tokens",
                         "cache_read_input_tokens"))
            if total:
                info["context_tokens"] = total
            for block in msg.get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    info["last_tool"] = block.get("name")
                    info["last_tool_at"] = ts
                elif block.get("type") == "text" and block.get("text"):
                    info["last_text"] = block["text"]
        elif rec.get("type") == "user" and isinstance(msg, dict):
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                info["last_prompt"] = content
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        info["last_prompt"] = block.get("text") or info["last_prompt"]
    if DETAIL != "verbose":
        info["last_text"] = None
        info["last_prompt"] = None
    else:
        info["last_text"] = clip(info["last_text"])
        info["last_prompt"] = clip(info["last_prompt"])
    return info


def update_counters(path, state):
    """增量統計逐字稿筆數與工具呼叫次數（只解析上次之後新增的位元組）。"""
    key = str(path)
    book = state.setdefault("transcripts", {}).setdefault(
        key, {"offset": 0, "records": 0, "tool_calls": 0,
              "output_tokens": 0, "counted_from": None, "partial": False})
    try:
        size = path.stat().st_size
    except OSError:
        return book
    if size < book["offset"]:                     # 檔案被截斷或換過，重來
        book.update({"offset": 0, "records": 0, "tool_calls": 0,
                     "output_tokens": 0, "partial": False})
    if book["offset"] == 0 and size > BACKLOG_CAP:
        # 一開始就很大的逐字稿不回頭全解析，只數行數，之後的才逐筆統計
        with open(path, "rb") as fh:
            book["records"] = sum(chunk.count(b"\n")
                                  for chunk in iter(lambda: fh.read(4 << 20), b""))
        book["offset"] = size
        book["partial"] = True
        book["counted_from"] = iso(now_utc())
        return book
    if size == book["offset"]:
        return book
    with open(path, "rb") as fh:
        fh.seek(book["offset"])
        blob = fh.read()
    lines = blob.split(b"\n")
    remainder = lines.pop()                        # 最後一行可能還沒寫完
    book["offset"] = size - len(remainder)
    if book["counted_from"] is None:
        book["counted_from"] = iso(now_utc())
    for line in lines:
        line = line.strip()
        if not line:
            continue
        book["records"] += 1
        try:
            rec = json.loads(line.decode("utf-8", "replace"))
        except ValueError:
            continue
        msg = rec.get("message")
        if rec.get("type") == "assistant" and isinstance(msg, dict):
            usage = msg.get("usage") or {}
            book["output_tokens"] += int(usage.get("output_tokens") or 0)
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    book["tool_calls"] += 1
    return book


# ---------------------------------------------------------------- 工作階段

def derive_status(raw_status, last_activity_iso):
    """把 busy/idle 加上「停滯」的判斷。"""
    if raw_status != "busy":
        return raw_status or "unknown"
    if not last_activity_iso:
        return "busy"
    try:
        last = datetime.fromisoformat(last_activity_iso.replace("Z", "+00:00"))
    except ValueError:
        return "busy"
    if (now_utc() - last).total_seconds() > STALL_MINUTES * 60:
        return "stalled"
    return "busy"


def shown_path(path):
    if not path:
        return None
    return os.path.basename(str(path).rstrip("/")) if DETAIL == "minimal" else str(path)


def collect_cli_sessions(state):
    """~/.claude/sessions/<pid>.json — 每個執行中的 Claude Code CLI 工作階段。"""
    out = []
    for path in sorted(SESSIONS_DIR.glob("*.json")):
        rec = load_json(path)
        if not isinstance(rec, dict):
            continue
        if not process_alive(rec.get("pid"), rec.get("startedAt")):
            continue                               # 殘留的狀態檔，行程已經結束
        session_id = rec.get("sessionId")
        transcript = find_transcript(session_id)
        detail = summarize_transcript(transcript) if transcript else {}
        counts = update_counters(transcript, state) if transcript else {}
        item = {
            "kind": "cli",
            "name": rec.get("name") or ("pid %s" % rec.get("pid")),
            "session_id": session_id,
            "pid": rec.get("pid"),
            "status": derive_status(rec.get("status"), detail.get("last_activity")),
            "raw_status": rec.get("status"),
            "status_updated_at": iso_ms(rec.get("statusUpdatedAt")),
            "started_at": iso_ms(rec.get("startedAt")),
            "last_activity": detail.get("last_activity"),
            "cwd": shown_path(rec.get("cwd")),
            "version": rec.get("version"),
            "entrypoint": rec.get("entrypoint"),
        }
        if DETAIL != "minimal":
            item.update({
                "model": detail.get("model"),
                "effort": detail.get("effort"),
                "git_branch": detail.get("git_branch"),
                "last_tool": detail.get("last_tool"),
                "last_tool_at": detail.get("last_tool_at"),
                "context_tokens": detail.get("context_tokens"),
                "records": counts.get("records"),
                "tool_calls": counts.get("tool_calls"),
                "output_tokens": counts.get("output_tokens"),
                "counts_partial": counts.get("partial"),
            })
        if DETAIL == "verbose":
            item["last_prompt"] = detail.get("last_prompt")
            item["last_text"] = detail.get("last_text")
        out.append(item)
    out.sort(key=lambda s: (s["status"] != "busy", s.get("started_at") or ""))
    return out


def collect_desktop_sessions(live_cli_ids):
    """桌面版 App（Cowork / 本機代理模式）的工作階段紀錄。"""
    cutoff_ms = (time.time() - DESKTOP_WINDOW_HOURS * 3600) * 1000
    out = []
    for pattern in DESKTOP_GLOBS:
        for path in APP_SUPPORT.glob(pattern):
            rec = load_json(path)
            if not isinstance(rec, dict) or rec.get("isArchived"):
                continue
            last_ms = rec.get("lastActivityAt") or rec.get("lastFocusedAt") or 0
            if last_ms < cutoff_ms:
                continue
            cli_id = rec.get("cliSessionId")
            live = cli_id in live_cli_ids
            transcript = find_transcript(cli_id)
            detail = summarize_transcript(transcript) if transcript else {}
            item = {
                "kind": "desktop",
                "name": rec.get("title") if DETAIL != "minimal" else "桌面工作階段",
                "session_id": rec.get("sessionId"),
                "cli_session_id": cli_id,
                "status": "busy" if live else "ended",
                "started_at": iso_ms(rec.get("createdAt")),
                "last_activity": iso_ms(last_ms),
                "cwd": shown_path(rec.get("cwd")),
                "permission_mode": rec.get("permissionMode"),
            }
            if DETAIL != "minimal":
                item.update({
                    "model": rec.get("model") or detail.get("model"),
                    "effort": rec.get("effort") or detail.get("effort"),
                    "last_tool": detail.get("last_tool"),
                    "context_tokens": detail.get("context_tokens"),
                })
            out.append(item)
    out.sort(key=lambda s: s.get("last_activity") or "", reverse=True)
    return out


# ---------------------------------------------------------------- 程式庫

def git_repo_status(repo):
    code, top = run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"])
    if code != 0 or not top:
        return None
    code_branch, branch = run(["git", "-C", top, "rev-parse", "--abbrev-ref", "HEAD"])
    code_st, porcelain = run(["git", "-C", top, "status", "--porcelain"])
    code_log, last = run(["git", "-C", top, "log", "-1", "--format=%h\x1f%s\x1f%cI"])
    branch = branch if code_branch == 0 else ""
    porcelain = porcelain if code_st == 0 else ""
    last = last if code_log == 0 else ""
    code_ahead, ahead = run(["git", "-C", top, "rev-list", "--count", "@{u}..HEAD"])
    parts = last.split("\x1f") if last else []
    dirty = len([ln for ln in porcelain.splitlines() if ln.strip()])
    return {
        "name": os.path.basename(top),
        "path": shown_path(top),
        "branch": branch or None,
        "dirty_files": dirty,
        "ahead": int(ahead) if code_ahead == 0 and ahead.isdigit() else None,
        "last_commit": {
            "hash": parts[0] if len(parts) > 0 else None,
            "subject": clip(parts[1], 90) if len(parts) > 1 and DETAIL != "minimal" else None,
            "at": parts[2] if len(parts) > 2 else None,
        } if parts else None,
    }


MAX_REPO_CANDIDATES = 24


def repo_candidates(sessions):
    """工作階段的 cwd，加上它底下一層的目錄 —— 常常是從專案的上層目錄開工的。"""
    roots = [s.get("cwd") for s in sessions if s.get("cwd")]
    roots.append(str(REPO_DIR))
    out = []
    for root in roots:
        if not root or root in out or not os.path.isdir(root):
            continue
        out.append(root)
        if os.path.isdir(os.path.join(root, ".git")):
            continue               # 本身就是程式庫，不用再往下找
        try:
            children = sorted(os.listdir(root))
        except OSError:
            continue
        for child in children:
            path = os.path.join(root, child)
            if child.startswith(".") or not os.path.isdir(os.path.join(path, ".git")):
                continue
            if path not in out:
                out.append(path)
    return out[:MAX_REPO_CANDIDATES]


def collect_repos(sessions):
    seen, repos = set(), []
    for cwd in repo_candidates(sessions):
        if not os.path.isdir(cwd):
            continue
        info = git_repo_status(cwd)
        if info and info["path"] not in seen:
            seen.add(info["path"])
            repos.append(info)
    repos.sort(key=lambda r: (r.get("last_commit") or {}).get("at") or "", reverse=True)
    return repos


# ---------------------------------------------------------------- 狀態與發佈

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.parent / (STATE_FILE.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh)
    tmp.replace(STATE_FILE)


def content_hash(payload):
    """排除每次都會變的欄位，才能判斷「內容真的有變」。"""
    volatile = {"generated_at", "monitor_version"}
    stable = {k: v for k, v in payload.items() if k not in volatile}
    blob = json.dumps(stable, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def publish(payload, state):
    """寫檔、必要時 commit 並推送。回傳這次做了什麼。"""
    pub = state.setdefault("publish", {})
    digest = content_hash(payload)
    since_last = time.time() - (pub.get("last_commit_ts") or 0)
    changed = digest != pub.get("hash")
    pub["last_run_ts"] = time.time()
    if not (changed and since_last >= MIN_PUSH_SECONDS) and since_last < HEARTBEAT_SECONDS:
        return "skipped"

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT_JSON.parent / (OUT_JSON.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    tmp.replace(OUT_JSON)

    result = "written"
    if PUSH:
        busy = sum(1 for s in payload["sessions"] if s["status"] == "busy")
        idle = len(payload["sessions"]) - busy
        run(["git", "-C", str(REPO_DIR), "add", "--", OUT_JSON.name])
        code, _ = run(["git", "-C", str(REPO_DIR), "diff", "--cached", "--quiet",
                       "--", OUT_JSON.name])
        if code != 0:                              # 真的有暫存的差異才 commit
            run(["git", "-C", str(REPO_DIR), "commit", "-m",
                 "status: Claude 看板 %s 執行中 / %s 閒置" % (busy, idle),
                 "--", OUT_JSON.name])
            result = "committed"
            branch = payload["host"].get("branch") or "main"
            for delay in (2, 4, 8, 16, 0):
                code, out = run(["git", "-C", str(REPO_DIR), "push", "-u",
                                 "origin", branch], timeout=120)
                if code == 0:
                    result = "pushed"
                    pub.pop("last_push_error", None)
                    break
                pub["last_push_error"] = clip(out, 200)
                if "fetch first" in out or "non-fast-forward" in out or "rejected" in out:
                    # 別的工作階段先推了。把這筆狀態 commit 疊到對方後面再試；
                    # --autostash 是因為當下工作目錄很可能有別人編輯到一半的檔案。
                    run(["git", "-C", str(REPO_DIR), "pull", "--rebase",
                         "--autostash", "origin", branch], timeout=120)
                if delay:
                    time.sleep(delay)
            else:
                result = "push-failed"

    pub["hash"] = digest
    pub["last_commit_ts"] = time.time()
    return result


# ---------------------------------------------------------------- 主流程

def main():
    if not REPO_DIR.is_dir():
        sys.stderr.write("找不到發佈用的程式庫：%s（外接碟沒掛載？）\n" % REPO_DIR)
        return 2

    state = load_json(STATE_FILE, {}) or {}
    cli = collect_cli_sessions(state)
    live_ids = set(s["session_id"] for s in cli)
    desktop = collect_desktop_sessions(live_ids)
    sessions = cli + desktop
    repos = collect_repos(cli)

    code, branch = run(["git", "-C", str(REPO_DIR), "rev-parse", "--abbrev-ref", "HEAD"])
    if code != 0:
        branch = ""
    payload = {
        "generated_at": iso(now_utc()),
        "monitor_version": MONITOR_VERSION,
        "detail": DETAIL,
        "interval_seconds": 60,
        "heartbeat_seconds": HEARTBEAT_SECONDS,
        "summary": {
            "busy": sum(1 for s in sessions if s["status"] == "busy"),
            "idle": sum(1 for s in sessions if s["status"] == "idle"),
            "stalled": sum(1 for s in sessions if s["status"] == "stalled"),
            "cli_total": len(cli),
            "desktop_total": len(desktop),
        },
        "sessions": sessions,
        "repos": repos,
        "host": {
            "hostname": os.uname().nodename,
            "branch": branch or "main",
            "last_push_error": (state.get("publish") or {}).get("last_push_error"),
        },
    }
    outcome = publish(payload, state)
    save_state(state)
    print("%s  %s  sessions=%d  %s" % (
        iso(now_utc()), outcome, len(sessions), payload["summary"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
