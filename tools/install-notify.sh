#!/bin/bash
# 把通知器安裝到家目錄，並裝上靜默心跳的排程。
#
# 為什麼要複製而不是直接用 repo 裡的檔案：這個 repo 在外接 USB 碟上。
# 碟沒掛載時 hook 會安靜地失敗 —— 收不到通知，也收不到「通知壞了」的通知。
# 家目錄不會消失，所以執行用的副本放家目錄，repo 仍然是原始碼所在。
#
#   ./install-notify.sh            安裝 / 更新家目錄的副本與心跳排程
#   ./install-notify.sh uninstall  移除心跳排程（不動設定檔與 hook）
#   ./install-notify.sh status     看排程與最近的日誌
set -euo pipefail

LABEL="com.allentw.claude-notify-heartbeat"
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.claude-monitor/bin"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/claude-notify.log"
DOMAIN="gui/$(id -u)"

case "${1:-install}" in
  install)
    mkdir -p "$BIN" "$HOME/Library/LaunchAgents"
    # claude_notify.py 會 import claude_monitor 拿逐字稿解析，兩個都要帶過去
    cp "$HERE/claude_notify.py" "$HERE/claude_monitor.py" "$BIN/"
    chmod +x "$BIN/claude_notify.py"
    echo "已複製到 $BIN"

    cat > "$PLIST" <<PLIST_END
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$BIN/claude_notify.py</string>
    <string>heartbeat</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <!-- 每小時檢查一次，但只有安靜超過 heartbeat_hours 才真的送 -->
  <key>StartInterval</key>
  <integer>3600</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$LOG</string>
  <key>StandardErrorPath</key>
  <string>$LOG</string>
  <key>ProcessType</key>
  <string>Background</string>
</dict>
</plist>
PLIST_END

    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
    launchctl bootstrap "$DOMAIN" "$PLIST"
    echo "已裝上心跳排程：$PLIST"
    echo ""
    echo "接著把 ~/.claude/settings.json 的兩個 hook 指到家目錄這份："
    echo "  /usr/bin/python3 $BIN/claude_notify.py 2>/dev/null || true"
    ;;
  uninstall)
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
    rm -f "$PLIST"
    echo "已移除心跳排程。$BIN 的副本與 hook 設定沒有動。"
    ;;
  status)
    launchctl print "$DOMAIN/$LABEL" 2>/dev/null | grep -E "state =|runs =|last exit code" || echo "心跳排程沒有載入。"
    echo "--- 最近 10 行日誌 ---"
    tail -n 10 "$LOG" 2>/dev/null || echo "（還沒有日誌）"
    ;;
  *)
    echo "用法：$0 [install|uninstall|status]" >&2
    exit 64
    ;;
esac
