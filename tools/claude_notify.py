#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Claude → Telegram 通知。

由 Claude Code 的 hook 觸發，只在兩種情況發訊息：
  1. 任務完成（Stop）—— 附上做了什麼的摘要
  2. 需要你決策（Notification）—— Claude 在等權限確認或輸入
兩種都會附上目前的用量。

設定（token 不會進 repo，這個 repo 是公開的）：
    ./claude_notify.py configure --token <BotFather 給的 token>
    ./claude_notify.py test

設定檔：~/.claude-monitor/telegram.json（權限 0600）

這支程式是 hook，**絕對不能讓 Claude 卡住或失敗**：所有例外都吞掉，永遠 exit 0。
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claude_monitor as cm   # noqa: E402  共用逐字稿解析

NOTIFY_VERSION = "1.0.0"
CONFIG_FILE = Path.home() / ".claude-monitor" / "telegram.json"
STATE_FILE = Path.home() / ".claude-monitor" / "notify-state.json"
APP_SUPPORT = Path.home() / "Library" / "Application Support" / "Claude"
PLAN_USAGE = APP_SUPPORT / "plan-usage-history.json"

TELEGRAM_TIMEOUT = 10
SUMMARY_LIMIT = 700           # Telegram 上限是 4096，但通知要能一眼看完
PLAN_USAGE_STALE_HOURS = 2    # 抽樣超過這麼久就標示「可能過舊」

DEFAULTS = {
    "bot_token": "",
    "chat_id": "",
    # 太短的回合不通知，否則每問一句話都會響
    "min_seconds": 60,
    "min_tool_calls": 5,
    # 只在你離開電腦超過這麼久才通知；0 = 一律通知
    "idle_only_minutes": 0,
    # 同一個工作階段這麼多秒內不重複發相同類型的通知
    "dedup_seconds": 45,
}


# ---------------------------------------------------------------- 設定

def load_config():
    cfg = dict(DEFAULTS)
    stored = cm.load_json(CONFIG_FILE, {}) or {}
    if isinstance(stored, dict):
        cfg.update(stored)
    cfg["bot_token"] = os.environ.get("TELEGRAM_BOT_TOKEN") or cfg["bot_token"]
    cfg["chat_id"] = os.environ.get("TELEGRAM_CHAT_ID") or cfg["chat_id"]
    return cfg


def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.parent / (CONFIG_FILE.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
    os.chmod(tmp, 0o600)
    tmp.replace(CONFIG_FILE)


# ---------------------------------------------------------------- Telegram

def telegram_call(token, method, params):
    url = "https://api.telegram.org/bot%s/%s" % (token, method)
    data = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TELEGRAM_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def send_message(cfg, text):
    if not cfg.get("bot_token") or not cfg.get("chat_id"):
        raise RuntimeError("還沒設定 bot_token / chat_id，先跑 configure")
    return telegram_call(cfg["bot_token"], "sendMessage", {
        "chat_id": cfg["chat_id"],
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    })


def esc(text):
    """Telegram HTML 模式只需要跳脫這三個字元。"""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def tidy_summary(text, limit=SUMMARY_LIMIT):
    """保留換行（摘要有結構才好讀），順手把 Markdown 記號拿掉。

    Telegram 不會渲染 **粗體** 或 `程式碼`，留著只是雜訊。
    """
    if not text:
        return None
    out = []
    blank = 0
    for line in str(text).replace("\r", "").split("\n"):
        line = line.rstrip()
        stripped = line.strip()
        if not stripped:
            blank += 1
            if blank > 1:
                continue            # 連續空行壓成一行
            out.append("")
            continue
        blank = 0
        stripped = stripped.replace("**", "").replace("`", "")
        if stripped.startswith("#"):
            stripped = stripped.lstrip("#").strip()
        out.append(stripped)
    joined = "\n".join(out).strip()
    if len(joined) <= limit:
        return joined
    cut = joined[:limit].rsplit("\n", 1)[0].rstrip()
    return (cut or joined[:limit]) + "\n…"


# ---------------------------------------------------------------- 用量

def plan_usage():
    """桌面 App 記錄的方案用量百分比。fh = 5 小時窗，sd = 7 天窗。

    這是 App 自己抽樣寫下的，App 沒在跑就不會更新，所以一律回報抽樣時間，
    讓訊息自己說清楚新鮮度，而不是假裝是即時數字。
    """
    data = cm.load_json(PLAN_USAGE, {}) or {}
    samples = data.get("samples") or []
    if not samples:
        return None
    last = samples[-1]
    used = last.get("u") or {}
    age_h = (time.time() - last.get("t", 0) / 1000.0) / 3600.0
    return {
        "five_hour": used.get("fh"),
        "seven_day": used.get("sd"),
        "sampled_at": cm.iso_ms(last.get("t")),
        "age_hours": age_h,
        "stale": age_h > PLAN_USAGE_STALE_HOURS,
    }


def format_usage(usage, turn):
    lines = []
    ctx = turn.get("context_tokens")
    out = turn.get("output_tokens")
    parts = []
    if ctx:
        parts.append("上下文 %s" % human_tokens(ctx))
    if out:
        parts.append("本回合輸出 %s" % human_tokens(out))
    if parts:
        lines.append("🔢 " + " · ".join(parts))

    if usage and (usage["five_hour"] is not None or usage["seven_day"] is not None):
        bits = []
        if usage["five_hour"] is not None:
            bits.append("5 小時 %d%%" % usage["five_hour"])
        if usage["seven_day"] is not None:
            bits.append("7 天 %d%%" % usage["seven_day"])
        note = ""
        if usage["stale"]:
            note = "（取樣於 %s，已 %d 小時沒更新，僅供參考）" % (
                local_clock(usage["sampled_at"]), int(usage["age_hours"]))
        lines.append("📊 方案用量 " + " · ".join(bits) + note)
    else:
        lines.append("📊 方案用量：讀不到（桌面 App 沒在跑就不會記錄）")
    return lines


def human_tokens(n):
    if not n:
        return "0"
    if n < 1000:
        return str(n)
    if n < 1000000:
        return "%.1fk" % (n / 1000.0)
    return "%.2fM" % (n / 1000000.0)


def human_duration(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return "%d 秒" % seconds
    if seconds < 3600:
        return "%d 分 %d 秒" % (seconds // 60, seconds % 60)
    return "%d 小時 %d 分" % (seconds // 3600, (seconds % 3600) // 60)


def local_clock(iso_text):
    if not iso_text:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_text.replace("Z", "+00:00"))
    except ValueError:
        return "—"
    return dt.astimezone().strftime("%m-%d %H:%M")


# ---------------------------------------------------------------- 回合分析

def is_human_prompt(rec):
    """是不是「人類真的打了字」，而不是工具結果或系統插入的內容。"""
    if rec.get("type") != "user" or rec.get("isSidechain"):
        return False
    msg = rec.get("message")
    if not isinstance(msg, dict):
        return False
    content = msg.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return False
        text = " ".join(b.get("text", "") for b in content
                        if isinstance(b, dict) and b.get("type") == "text")
    else:
        return False
    text = text.strip()
    return bool(text) and not text.startswith("<system-reminder>")


def analyse_turn(transcript):
    """看最後一個回合：做了多久、用了幾次工具、最後說了什麼。"""
    turn = {
        "summary": None, "prompt": None, "tool_calls": 0, "tools": [],
        "seconds": None, "context_tokens": None, "output_tokens": 0,
        "model": None, "cwd": None, "git_branch": None, "last_tool": None,
    }
    if not transcript:
        return turn
    records = cm.read_tail_records(transcript, limit=600)
    if not records:
        return turn

    start = 0
    for i in range(len(records) - 1, -1, -1):
        if is_human_prompt(records[i]):
            start = i
            break
    else:
        start = 0                       # 尾端看不到人類訊息就整段當一個回合

    first_ts = last_ts = None
    for rec in records[start:]:
        if rec.get("isSidechain"):
            continue
        ts = rec.get("timestamp")
        if ts:
            first_ts = first_ts or ts
            last_ts = ts
        if rec.get("cwd"):
            turn["cwd"] = rec["cwd"]
        if rec.get("gitBranch") and rec["gitBranch"] != "HEAD":
            turn["git_branch"] = rec["gitBranch"]
        msg = rec.get("message")
        if not isinstance(msg, dict):
            continue
        if is_human_prompt(rec) and turn["prompt"] is None:
            content = msg.get("content")
            turn["prompt"] = content if isinstance(content, str) else None
        if rec.get("type") != "assistant":
            continue
        turn["model"] = msg.get("model") or turn["model"]
        usage = msg.get("usage") or {}
        turn["output_tokens"] += int(usage.get("output_tokens") or 0)
        total = sum(int(usage.get(k) or 0) for k in
                    ("input_tokens", "cache_creation_input_tokens",
                     "cache_read_input_tokens"))
        if total:
            turn["context_tokens"] = total
        for block in msg.get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                turn["tool_calls"] += 1
                turn["last_tool"] = block.get("name")
                turn["tools"].append(block.get("name"))
            elif block.get("type") == "text" and block.get("text", "").strip():
                turn["summary"] = block["text"]

    if first_ts and last_ts:
        try:
            a = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
            b = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            turn["seconds"] = max(0, (b - a).total_seconds())
        except ValueError:
            pass
    return turn


def tool_breakdown(tools):
    counts = {}
    for name in tools:
        counts[name] = counts.get(name, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: -kv[1])[:4]
    return "、".join("%s×%d" % (n, c) for n, c in ordered)


# ---------------------------------------------------------------- 抑制條件

def user_idle_seconds():
    """使用者多久沒碰鍵盤滑鼠。問不到就回 None。"""
    code, out = cm.run(["/usr/sbin/ioreg", "-c", "IOHIDSystem", "-d", "4"], timeout=5)
    if code != 0:
        return None
    for line in out.splitlines():
        if "HIDIdleTime" in line:
            try:
                return int(line.split("=")[-1].strip()) / 1000000000.0
            except ValueError:
                return None
    return None


def should_skip(cfg, kind, session_id, turn):
    """回傳不通知的理由，None 代表要通知。"""
    if kind == "done":
        secs = turn.get("seconds") or 0
        calls = turn.get("tool_calls") or 0
        if secs < cfg["min_seconds"] and calls < cfg["min_tool_calls"]:
            return "回合太短（%.0f 秒 / %d 次工具），不值得打擾" % (secs, calls)

    idle_min = cfg.get("idle_only_minutes") or 0
    if idle_min:
        idle = user_idle_seconds()
        if idle is not None and idle < idle_min * 60:
            return "你就在電腦前（閒置 %.0f 秒）" % idle

    state = cm.load_json(STATE_FILE, {}) or {}
    key = "%s:%s" % (session_id, kind)
    last = (state.get("sent") or {}).get(key) or 0
    if time.time() - last < cfg["dedup_seconds"]:
        return "剛剛才發過同一則（%.0f 秒前）" % (time.time() - last)
    return None


def remember_sent(kind, session_id):
    state = cm.load_json(STATE_FILE, {}) or {}
    state.setdefault("sent", {})["%s:%s" % (session_id, kind)] = time.time()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.parent / (STATE_FILE.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh)
    tmp.replace(STATE_FILE)


# ---------------------------------------------------------------- 組訊息

def session_label(session_id):
    """把 session id 對回 Claude 給的短名字，例如 claude-7b。"""
    for path in (Path.home() / ".claude" / "sessions").glob("*.json"):
        rec = cm.load_json(path)
        if isinstance(rec, dict) and rec.get("sessionId") == session_id:
            return rec.get("name") or session_id[:8]
    return session_id[:8] if session_id else "未知階段"


def build_message(kind, payload, turn, cfg):
    name = session_label(payload.get("session_id"))
    # hook 給的 cwd 是工作階段的根目錄；逐字稿裡的是最後一個指令跑在哪，
    # shell 進出子目錄會讓後者變成 tools/ 之類的，當專案名會怪
    cwd = payload.get("cwd") or turn.get("cwd") or ""
    project = os.path.basename(cwd.rstrip("/")) if cwd else "—"
    branch = turn.get("git_branch")

    if kind == "done":
        head = "✅ <b>任務完成</b> · %s" % esc(name)
    else:
        head = "⏳ <b>需要你決策</b> · %s" % esc(name)

    lines = [head, "📁 %s%s" % (esc(project), esc(" · " + branch) if branch else "")]

    if kind == "decision":
        ask = payload.get("message") or "Claude 在等你回應"
        lines.append("")
        lines.append("❓ %s" % esc(cm.clip(ask, 300)))
        if turn.get("last_tool"):
            lines.append("最後動作：%s" % esc(turn["last_tool"]))
    else:
        summary = turn.get("summary")
        lines.append("")
        if summary:
            lines.append("<b>做了什麼</b>")
            lines.append(esc(tidy_summary(summary)))
        else:
            lines.append("<i>（這個回合沒有留下文字說明）</i>")
        stats = []
        if turn.get("seconds"):
            stats.append("耗時 %s" % human_duration(turn["seconds"]))
        if turn.get("tool_calls"):
            stats.append("%d 次工具" % turn["tool_calls"])
        if stats:
            detail = " · ".join(stats)
            if turn.get("tools"):
                detail += "（%s）" % tool_breakdown(turn["tools"])
            lines.append("")
            lines.append("⏱ " + esc(detail))

    lines.append("")
    lines.extend(esc_usage_lines(plan_usage(), turn))
    if turn.get("model"):
        lines.append("🤖 %s" % esc(turn["model"]))
    return "\n".join(lines)


def esc_usage_lines(usage, turn):
    """format_usage 產生的字串已經是安全的純文字，只有表情符號和數字。"""
    return [esc(line) for line in format_usage(usage, turn)]


# ---------------------------------------------------------------- hook 模式

EVENT_KINDS = {"Stop": "done", "SubagentStop": None, "Notification": "decision"}


def run_hook(dry_run=False):
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    payload = {}
    if raw.strip():
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {}

    event = payload.get("hook_event_name") or ""
    kind = EVENT_KINDS.get(event)
    if kind is None:
        log("忽略事件 %r" % event)
        return

    cfg = load_config()
    session_id = payload.get("session_id") or ""
    transcript = payload.get("transcript_path")
    if transcript and os.path.exists(transcript):
        transcript = Path(transcript)
    else:
        transcript = cm.find_transcript(session_id)

    turn = analyse_turn(transcript)
    reason = should_skip(cfg, kind, session_id, turn)
    if reason and not dry_run:
        log("不通知（%s）：%s" % (kind, reason))
        return

    text = build_message(kind, payload, turn, cfg)
    if dry_run:
        print(text)
        if reason:
            print("\n[dry-run] 正常情況下會被略過：%s" % reason)
        return
    send_message(cfg, text)
    remember_sent(kind, session_id)
    log("已通知（%s）：%s" % (kind, session_label(session_id)))


def log(text):
    try:
        path = Path.home() / "Library" / "Logs" / "claude-notify.log"
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("%s  %s\n" % (cm.iso(datetime.now(timezone.utc)), text))
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------- 設定指令

def prompt_secret(label):
    """讀一段不該留在畫面或 shell 歷史裡的字串。"""
    try:
        import getpass
        return getpass.getpass(label).strip()
    except Exception:  # noqa: BLE001 - 沒有終端機時退回一般輸入
        try:
            return input(label).strip()
        except EOFError:
            return ""


def cmd_configure(args):
    cfg = load_config()
    token = None
    chat = None
    for i, a in enumerate(args):
        if a == "--token" and i + 1 < len(args):
            token = args[i + 1]
        elif a == "--chat" and i + 1 < len(args):
            chat = args[i + 1]

    if not token:
        print("到 Telegram 找 @BotFather，在你的 bot 頁面按 Copy 複製 token。")
        token = prompt_secret("貼上 token（輸入時畫面不會顯示，貼完按 Enter）：")
    if not token:
        print("沒有拿到 token，中止。")
        return 1
    cfg["bot_token"] = token.strip()

    # 先確認 token 真的能用，也讓你看到接上的是不是預期的那個 bot
    try:
        me = telegram_call(cfg["bot_token"], "getMe", {})
    except Exception as exc:  # noqa: BLE001
        print("這個 token 連不上 Telegram：%s" % exc)
        print("（token 貼完整了嗎？格式長得像 123456789:AA... 這樣）")
        return 1
    if not me.get("ok"):
        print("Telegram 說這個 token 無效：%s" % me.get("description"))
        return 1
    bot_name = (me.get("result") or {}).get("username")
    print("✓ token 有效，接上的 bot 是 @%s" % bot_name)

    if chat:
        cfg["chat_id"] = chat.strip()
    else:
        cfg["chat_id"] = ""
        print("")
        print("接下來要知道「發給誰」。請在 Telegram 打開 @%s，對它說任何一句話"
              "（例如 hi）。" % bot_name)
        for attempt in range(1, 6):
            try:
                input("說完之後回到這裡按 Enter 繼續… ")
            except EOFError:
                break
            found = discover_chat_id(cfg["bot_token"])
            if found:
                cfg["chat_id"] = found
                print("✓ 找到你的 chat_id：%s" % found)
                break
            print("還是沒看到訊息（第 %d 次）。確認是對 @%s 說話，不是對 BotFather。"
                  % (attempt, bot_name))
        if not cfg["chat_id"]:
            print("找不到 chat_id。之後可以用 configure --chat <id> 直接指定。")
            return 1

    save_config(cfg)
    print("已寫入 %s（權限 0600，不在 repo 裡）" % CONFIG_FILE)
    print("")
    print("送一則測試訊息…")
    return cmd_test()


def discover_chat_id(token):
    try:
        result = telegram_call(token, "getUpdates", {"timeout": 0})
    except Exception as exc:  # noqa: BLE001
        print("getUpdates 失敗：%s" % exc)
        return None
    for update in reversed(result.get("result") or []):
        msg = update.get("message") or update.get("channel_post") or {}
        chat = msg.get("chat") or {}
        if chat.get("id"):
            return str(chat["id"])
    return None


def cmd_test():
    cfg = load_config()
    usage = plan_usage()
    lines = ["🔔 <b>測試通知</b>",
             "Claude → Telegram 通道通了。",
             ""]
    lines.extend(esc_usage_lines(usage, {}))
    try:
        send_message(cfg, "\n".join(lines))
    except Exception as exc:  # noqa: BLE001
        print("送不出去：%s" % exc)
        return 1
    print("已送出，去 Telegram 看看。")
    return 0


USAGE_TEXT = """用法：
  claude_notify.py                     hook 模式（從 stdin 讀事件 JSON）
  claude_notify.py --dry-run           hook 模式但只印出訊息，不發送
  claude_notify.py configure --token T [--chat C]
  claude_notify.py test                送一則測試訊息
  claude_notify.py show                顯示目前設定（token 會遮起來）
"""


def cmd_show():
    cfg = load_config()
    token = cfg.get("bot_token") or ""
    masked = (token[:8] + "…" + token[-4:]) if len(token) > 14 else ("（未設定）" if not token else "已設定")
    print("設定檔：%s" % CONFIG_FILE)
    print("  bot_token        : %s" % masked)
    print("  chat_id          : %s" % (cfg.get("chat_id") or "（未設定）"))
    print("  min_seconds      : %s  （回合短於這個秒數就不通知）" % cfg["min_seconds"])
    print("  min_tool_calls   : %s  （工具次數少於這個也不通知）" % cfg["min_tool_calls"])
    print("  idle_only_minutes: %s  （0 = 一律通知；>0 = 只在你離開這麼久才通知）" % cfg["idle_only_minutes"])
    print("  dedup_seconds    : %s" % cfg["dedup_seconds"])
    usage = plan_usage()
    print("方案用量：%s" % (usage if usage else "讀不到"))
    return 0


def main(argv):
    args = argv[1:]
    if args and args[0] == "configure":
        return cmd_configure(args[1:])
    if args and args[0] == "test":
        return cmd_test()
    if args and args[0] == "show":
        return cmd_show()
    if args and args[0] in ("-h", "--help", "help"):
        print(USAGE_TEXT)
        return 0
    run_hook(dry_run="--dry-run" in args)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - hook 絕不能讓 Claude 失敗
        log("例外：%r" % (exc,))
        sys.exit(0)
