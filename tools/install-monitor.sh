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

    # launchd 代理程式預設沒有存取外接碟的權限，第一次安裝幾乎一定會卡在這裡
    for _ in 1 2 3 4 5 6; do
      grep -q "Operation not permitted" "$LOG" 2>/dev/null && break
      /bin/sleep 1
    done
    if grep -q "Operation not permitted" "$LOG" 2>/dev/null; then
      cat <<'HINT'

⚠ 排程跑起來了，但被 macOS 擋住讀取外接碟（日誌裡是 Operation not permitted）。
   這不是檔案權限問題，是「完全取用磁碟」的授權：launchd 代理程式預設拿不到
   外接 USB 碟的存取權，而互動式終端機有。

   解法（一次性，在 Mac mini 上操作）：
     1. 系統設定 → 隱私權與安全性 → 完全取用磁碟
     2. 按 ＋，在檔案選擇視窗按 Cmd+Shift+G，貼上：
          /Library/Developer/CommandLineTools/usr/bin/python3
     3. 加入後把它的開關打開
     4. 回到這裡執行：launchctl kickstart -k gui/$(id -u)/com.allentw.claude-monitor
     5. ./install-monitor.sh status 應該就會看到正常的輸出

   注意：這等於讓機器上所有用這個 python3 跑的腳本都拿到完整磁碟存取權。
   不想這樣授權的話，見 README 的「不授權的替代做法」。
HINT
    fi
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
