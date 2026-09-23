#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""laoliu uploader: a dependency-free HTTP endpoint that drops uploaded files
onto this Mac mini, filed under a user-chosen category, as raw material for
later tooling work.

Layout on disk:
    <UPLOAD_ROOT>/<category-slug>/<YYYYmmdd-HHMMSS>__<original-name>
    <UPLOAD_ROOT>/_manifest.jsonl     one JSON object per upload
    <UPLOAD_ROOT>/_categories.json    category list, editable from the UI

The browser sends one file per request with the raw bytes as the body, so there
is no multipart parsing: the body streams straight to disk in fixed-size chunks
and a 2 GiB upload costs a few hundred KiB of memory.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import sys
import threading
import time
import unicodedata
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

HERE = Path(__file__).resolve().parent
STATIC_DIR = HERE / "static"

# The uploader lives at <working-dir>/SumerTWRobotTest1/uploader, and uploads
# belong in the working directory itself, one level up from the repo.
DEFAULT_UPLOAD_ROOT = HERE.parent.parent / "uploads"
TOKEN_FILE = Path.home() / ".laoliu-uploader" / "token"

DEFAULT_CATEGORIES = [
    "trade-logs",
    "statements",
    "research",
    "screenshots",
    "code",
    "datasets",
    "misc",
]

MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB
CHUNK = 1024 * 1024
MAX_NAME_LEN = 120
MANIFEST_LOCK = threading.Lock()
CATEGORY_LOCK = threading.Lock()

# Windows-reserved device names; harmless here but they make files awkward to
# move around later, so they get a suffix.
RESERVED_STEMS = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_CATEGORY_OK = re.compile(r"^[\w一-鿿][\w一-鿿 .-]*$", re.UNICODE)


class UploadError(Exception):
    """A client mistake worth reporting verbatim; never used for internals."""

    def __init__(self, status: HTTPStatus, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def safe_filename(raw: str) -> str:
    """Reduce a client-supplied name to a single, harmless path component.

    Unicode is preserved (Chinese filenames are normal here); only separators,
    control characters and traversal are stripped.
    """
    name = unicodedata.normalize("NFC", unquote(raw or "")).strip()
    name = name.replace("\\", "/").split("/")[-1]
    name = _CONTROL_CHARS.sub("", name).strip(" .")
    if not name:
        name = "unnamed"

    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    if stem.lower() in RESERVED_STEMS:
        stem += "_file"

    # Budget the length against the stem so the extension always survives.
    ext = ext[:16]
    keep = MAX_NAME_LEN - (len(ext) + 1 if ext else 0)
    stem = stem[:keep] or "unnamed"
    return f"{stem}.{ext}" if ext else stem


def safe_category(raw: str) -> str:
    """Validate a category into exactly one directory level."""
    cat = unicodedata.normalize("NFC", unquote(raw or "")).strip()
    cat = _CONTROL_CHARS.sub("", cat).strip(" .")
    if not cat:
        return "misc"
    if "/" in cat or "\\" in cat or cat in (".", ".."):
        raise UploadError(HTTPStatus.BAD_REQUEST, f"分類名稱不合法：{raw!r}")
    if len(cat) > 60 or not _CATEGORY_OK.match(cat):
        raise UploadError(HTTPStatus.BAD_REQUEST, f"分類名稱不合法：{raw!r}")
    return cat


def unique_path(directory: Path, filename: str) -> Path:
    """Pick a non-colliding path, appending -1, -2, ... before the extension."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    stem, dot, ext = filename.rpartition(".")
    if not dot:
        stem, ext = filename, ""

    for attempt in range(1000):
        suffix = "" if attempt == 0 else f"-{attempt}"
        base = f"{stamp}__{stem}{suffix}"
        candidate = directory / (f"{base}.{ext}" if ext else base)
        if not candidate.exists():
            return candidate
    raise UploadError(HTTPStatus.CONFLICT, "同名檔案過多，請改名後再試")


def resolve_within(root: Path, *parts: str) -> Path:
    """Join under root and refuse anything that escapes it, symlinks included."""
    candidate = root.joinpath(*parts)
    resolved_root = root.resolve()
    # The file itself does not exist yet, so resolve its parent.
    probe = candidate if candidate.exists() else candidate.parent
    resolved = probe.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise UploadError(HTTPStatus.BAD_REQUEST, "路徑不合法")
    return candidate


class Store:
    """Everything that touches UPLOAD_ROOT."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.manifest = root / "_manifest.jsonl"
        self.categories_file = root / "_categories.json"
        root.mkdir(parents=True, exist_ok=True)

    def categories(self) -> list:
        with CATEGORY_LOCK:
            try:
                data = json.loads(self.categories_file.read_text("utf-8"))
                if isinstance(data, list) and data:
                    return [str(c) for c in data]
            except (OSError, ValueError):
                pass
            self._write_categories(DEFAULT_CATEGORIES)
            return list(DEFAULT_CATEGORIES)

    def add_category(self, name: str) -> list:
        name = safe_category(name)
        with CATEGORY_LOCK:
            try:
                current = json.loads(self.categories_file.read_text("utf-8"))
                if not isinstance(current, list):
                    current = list(DEFAULT_CATEGORIES)
            except (OSError, ValueError):
                current = list(DEFAULT_CATEGORIES)
            if name not in current:
                current.append(name)
                self._write_categories(current)
            return [str(c) for c in current]

    def _write_categories(self, categories: list) -> None:
        tmp = self.categories_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(categories, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(self.categories_file)

    def record(self, entry: dict) -> None:
        line = json.dumps(entry, ensure_ascii=False)
        with MANIFEST_LOCK:
            with self.manifest.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    def recent(self, limit: int = 30) -> list:
        """Tail the manifest without reading the whole file."""
        try:
            size = self.manifest.stat().st_size
        except OSError:
            return []
        window = min(size, 256 * 1024)
        with self.manifest.open("rb") as fh:
            fh.seek(size - window)
            text = fh.read().decode("utf-8", "replace")
        if window < size:
            text = text.split("\n", 1)[-1]  # drop the partial first line

        entries = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue
        return entries[-limit:][::-1]


class Handler(BaseHTTPRequestHandler):
    server_version = "laoliu-uploader/1.0"
    protocol_version = "HTTP/1.1"

    store: Store
    token: str

    # ---- plumbing -------------------------------------------------------

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        sys.stderr.write(
            "[%s] %s %s\n" % (datetime.now().strftime("%H:%M:%S"),
                              self.address_string(), fmt % args)
        )

    def _send(self, status: HTTPStatus, body: bytes, ctype: str,
              extra_headers: dict = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: HTTPStatus, payload: dict,
              extra_headers: dict = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8", extra_headers)

    def _error(self, status: HTTPStatus, message: str) -> None:
        self._json(status, {"ok": False, "error": message})

    # ---- auth -----------------------------------------------------------

    def _presented_token(self) -> str:
        header = self.headers.get("X-Upload-Token")
        if header:
            return header.strip()
        raw_cookie = self.headers.get("Cookie")
        if raw_cookie:
            jar = SimpleCookie()
            try:
                jar.load(raw_cookie)
            except Exception:
                return ""
            if "ut" in jar:
                return jar["ut"].value
        return ""

    def _authorized(self) -> bool:
        return hmac.compare_digest(self._presented_token(), self.token)

    def _require_auth(self) -> bool:
        if self._authorized():
            return True
        # Slow down brute force a little; the token is 32 hex chars so this is
        # belt-and-braces rather than the actual defence.
        time.sleep(0.5)
        self._error(HTTPStatus.UNAUTHORIZED, "未授權，請先輸入上傳密碼")
        return False

    # ---- routes ---------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path in ("/", "/index.html"):
                return self._serve_static("index.html")
            if path == "/api/config":
                if not self._require_auth():
                    return
                return self._json(HTTPStatus.OK, {
                    "ok": True,
                    "categories": self.store.categories(),
                    "uploadRoot": str(self.store.root),
                    "maxBytes": MAX_UPLOAD_BYTES,
                })
            if path == "/api/recent":
                if not self._require_auth():
                    return
                return self._json(HTTPStatus.OK,
                                  {"ok": True, "items": self.store.recent()})
            if path == "/api/ping":
                return self._json(HTTPStatus.OK, {"ok": True})
            if path.startswith("/static/"):
                return self._serve_static(path[len("/static/"):])
            self._error(HTTPStatus.NOT_FOUND, "找不到頁面")
        except UploadError as exc:
            self._error(exc.status, exc.message)

    def do_HEAD(self) -> None:  # noqa: N802
        self.do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/login":
                return self._handle_login()
            if path == "/api/upload":
                if not self._require_auth():
                    return
                return self._handle_upload()
            if path == "/api/category":
                if not self._require_auth():
                    return
                return self._handle_add_category()
            self._error(HTTPStatus.NOT_FOUND, "找不到端點")
        except UploadError as exc:
            self._drain()
            self._error(exc.status, exc.message)

    # ---- handlers -------------------------------------------------------

    def _serve_static(self, relative: str) -> None:
        relative = unquote(relative).lstrip("/")
        if not relative or ".." in relative.split("/"):
            return self._error(HTTPStatus.NOT_FOUND, "找不到檔案")
        target = STATIC_DIR / relative
        try:
            resolved = target.resolve()
            resolved.relative_to(STATIC_DIR.resolve())
            body = resolved.read_bytes()
        except (OSError, ValueError):
            return self._error(HTTPStatus.NOT_FOUND, "找不到檔案")
        ctype, _ = mimetypes.guess_type(resolved.name)
        if ctype and ctype.startswith("text/"):
            ctype += "; charset=utf-8"
        self._send(HTTPStatus.OK, body, ctype or "application/octet-stream",
                   {"Cache-Control": "no-store"})

    def _read_body(self, limit: int) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length > limit:
            raise UploadError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "內容過大")
        return self.rfile.read(length) if length else b""

    def _drain(self) -> None:
        """Consume an unread body so the connection stays usable."""
        remaining = int(self.headers.get("Content-Length") or 0)
        while remaining > 0:
            chunk = self.rfile.read(min(CHUNK, remaining))
            if not chunk:
                break
            remaining -= len(chunk)

    def _handle_login(self) -> None:
        try:
            payload = json.loads(self._read_body(4096).decode("utf-8") or "{}")
        except ValueError:
            raise UploadError(HTTPStatus.BAD_REQUEST, "格式錯誤")
        supplied = str(payload.get("token", "")).strip()
        if not hmac.compare_digest(supplied, self.token):
            time.sleep(0.5)
            return self._error(HTTPStatus.UNAUTHORIZED, "上傳密碼錯誤")
        cookie = f"ut={self.token}; Path=/; Max-Age=2592000; HttpOnly; SameSite=Strict"
        self._json(HTTPStatus.OK, {"ok": True}, {"Set-Cookie": cookie})

    def _handle_add_category(self) -> None:
        try:
            payload = json.loads(self._read_body(4096).decode("utf-8") or "{}")
        except ValueError:
            raise UploadError(HTTPStatus.BAD_REQUEST, "格式錯誤")
        categories = self.store.add_category(str(payload.get("name", "")))
        self._json(HTTPStatus.OK, {"ok": True, "categories": categories})

    def _handle_upload(self) -> None:
        params = parse_qs(urlparse(self.path).query)
        first = lambda key: (params.get(key) or [""])[0]  # noqa: E731

        category = safe_category(first("category"))
        filename = safe_filename(first("name"))
        note = _CONTROL_CHARS.sub(" ", unquote(first("note")))[:500].strip()
        tags = [t.strip()[:40] for t in unquote(first("tags")).split(",") if t.strip()][:10]

        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            raise UploadError(HTTPStatus.BAD_REQUEST, "檔案是空的")
        if length > MAX_UPLOAD_BYTES:
            raise UploadError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                              f"檔案超過上限 {MAX_UPLOAD_BYTES // (1024 ** 3)} GiB")

        directory = resolve_within(self.store.root, category)
        directory.mkdir(parents=True, exist_ok=True)
        target = unique_path(directory, filename)
        partial = target.with_name(target.name + ".part")

        digest = hashlib.sha256()
        written = 0
        try:
            with partial.open("wb") as out:
                while written < length:
                    chunk = self.rfile.read(min(CHUNK, length - written))
                    if not chunk:
                        break
                    out.write(chunk)
                    digest.update(chunk)
                    written += len(chunk)
            if written != length:
                raise UploadError(HTTPStatus.BAD_REQUEST, "連線中斷，檔案不完整")
            partial.replace(target)
        except UploadError:
            partial.unlink(missing_ok=True)
            raise
        except OSError as exc:
            partial.unlink(missing_ok=True)
            self.log_message("write failed: %s", exc)
            raise UploadError(HTTPStatus.INTERNAL_SERVER_ERROR, "寫入失敗，請查看伺服器日誌")

        entry = {
            "uploadedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "category": category,
            "originalName": filename,
            "storedPath": str(target.relative_to(self.store.root)),
            "bytes": written,
            "sha256": digest.hexdigest(),
            "note": note,
            "tags": tags,
            "clientIp": self.address_string(),
        }
        self.store.record(entry)
        self.log_message("stored %s (%d bytes)", entry["storedPath"], written)
        self._json(HTTPStatus.OK, {"ok": True, "item": entry})


def load_token(explicit: str = "") -> str:
    """Resolve the upload token: flag, then env, then file, else generate one."""
    token = (explicit or os.environ.get("UPLOAD_TOKEN") or "").strip()
    if token:
        return token
    try:
        token = TOKEN_FILE.read_text("utf-8").strip()
        if token:
            return token
    except OSError:
        pass
    token = secrets.token_hex(16)
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    TOKEN_FILE.write_text(token + "\n", "utf-8")
    TOKEN_FILE.chmod(0o600)
    print(f"[uploader] 已產生新的上傳密碼並存到 {TOKEN_FILE}", file=sys.stderr)
    return token


def main() -> int:
    parser = argparse.ArgumentParser(description="laoliu uploader")
    parser.add_argument("--host", default=os.environ.get("UPLOAD_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int,
                        default=int(os.environ.get("UPLOAD_PORT", "8787")))
    parser.add_argument("--root", default=os.environ.get("UPLOAD_ROOT",
                                                         str(DEFAULT_UPLOAD_ROOT)))
    parser.add_argument("--token", default="")
    args = parser.parse_args()

    store = Store(Path(args.root).expanduser())
    token = load_token(args.token)

    Handler.store = store
    Handler.token = token

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    httpd.daemon_threads = True

    print(f"[uploader] 檔案存放位置：{store.root}", file=sys.stderr)
    print(f"[uploader] 本機：http://127.0.0.1:{args.port}/", file=sys.stderr)
    print(f"[uploader] 上傳密碼：{token}", file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[uploader] 停止", file=sys.stderr)
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
