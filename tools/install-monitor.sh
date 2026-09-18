#!/bin/bash
# 安裝 / 解除安裝 Claude 看板的 launchd 排程（每分鐘跑一次 claude_monitor.py）。
#
#   ./install-monitor.sh            安裝並立刻跑一次
#   ./install-monitor.sh uninstall  停掉並移除排程（不會刪掉已發佈的資料）
#   ./install-monitor.sh status     看排程狀態與最近的日誌
set -euo pipefail

LABEL="com.allentw.claude-monitor"
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/$LABEL.plist"
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/claude-monitor.log"
DOMAIN="gui/$(id -u)"

case "${1:-install}" in
  install)
    mkdir -p "$HOME/Library/LaunchAgents"
    # plist 裡寫的是這個 repo 的絕對路徑；從 repo 實際位置產生，避免搬家後失效
    sed "s|<string>/Volumes/FCP 512GB/Claude/SumerTWRobotTest1/tools/claude_monitor.py</string>|<string>$HERE/claude_monitor.py</string>|" \
      "$SRC" > "$DEST"
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
    launchctl bootstrap "$DOMAIN" "$DEST"
    launchctl kickstart -k "$DOMAIN/$LABEL"
    echo "已安裝：$DEST"
    echo "日誌：$LOG"
    ;;
  uninstall)
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
    rm -f "$DEST"
    echo "已移除排程。claude-status.json 仍留在 repo 裡，需要的話自行刪除。"
    ;;
  status)
    launchctl print "$DOMAIN/$LABEL" 2>/dev/null | head -20 || echo "排程沒有載入。"
    echo "--- 最近 10 行日誌 ---"
    tail -n 10 "$LOG" 2>/dev/null || echo "（還沒有日誌）"
    ;;
  *)
    echo "用法：$0 [install|uninstall|status]" >&2
    exit 64
    ;;
esac
