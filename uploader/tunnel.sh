#!/bin/sh
# Expose the local uploader on a public https URL via a Cloudflare quick tunnel.
# The URL changes every run and is printed to stderr by cloudflared.
set -eu
PORT="${UPLOAD_PORT:-8787}"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared 未安裝。請先執行： brew install cloudflared" >&2
  exit 1
fi

if ! curl -fsS "http://127.0.0.1:${PORT}/api/ping" >/dev/null 2>&1; then
  echo "本機伺服器沒有在 ${PORT} 上回應。請先執行 ./run.sh 或啟用 launchd。" >&2
  exit 1
fi

exec cloudflared tunnel --url "http://127.0.0.1:${PORT}"
