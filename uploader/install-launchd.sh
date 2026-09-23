#!/bin/sh
# Register the uploader as a login-time launchd agent so it survives reboots,
# mirroring how claude remote-control is kept alive on this machine.
set -eu
DIR=$(cd "$(dirname "$0")" && pwd)
LABEL="com.laoliu.uploader"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOGDIR="$HOME/Library/Logs/laoliu-uploader"

mkdir -p "$(dirname "$PLIST")" "$LOGDIR"

cat > "$PLIST" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$DIR/server.py</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$LOGDIR/out.log</string>
  <key>StandardErrorPath</key><string>$LOGDIR/err.log</string>
</dict>
</plist>
PLIST_EOF

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

echo "已安裝 $LABEL"
echo "日誌：$LOGDIR/err.log"
echo "停用：launchctl bootout gui/$(id -u)/$LABEL && rm $PLIST"
