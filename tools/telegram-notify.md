# Claude → Telegram 通知

在公司收 Claude 的通知。只在兩種情況響：

| 情況 | 觸發 | 內容 |
|---|---|---|
| ✅ 任務完成 | `Stop` hook | 做了什麼的摘要、耗時、工具次數、用量 |
| ⏳ 需要你決策 | `Notification` hook | Claude 在等什麼、最後動作、用量 |

**不會**每問一句話就響：回合短於 60 秒**且**工具呼叫少於 5 次就安靜略過
（門檻可調，見下面的設定）。

## 設定（只做一次）

1. Telegram 裡找 **@BotFather**，送 `/newbot`，照它問的取名字，拿到 token。
2. 在 Mac mini 的終端機跑：

```bash
cd "/Volumes/FCP 512GB/Claude/SumerTWRobotTest1/tools"
./claude_notify.py configure
```

它會依序帶你做完：

- 要你貼上 token（**輸入時畫面不顯示**，也不會留在 shell 歷史裡）
- 用 `getMe` 驗證 token，並印出接上的是哪個 bot，讓你確認沒貼錯
- 要你去 Telegram 對那個 bot 說一句話，按 Enter 後自動撈出 chat_id
- 寫入設定並直接送一則測試訊息

手機收到測試訊息就完成了。

token 已經知道、也知道 chat_id 的話，可以一次給完跳過互動：
`./claude_notify.py configure --token <token> --chat <id>`
（這樣 token 會留在 shell 歷史裡，自己斟酌。）

**token 存在 `~/.claude-monitor/telegram.json`，權限 0600，不在這個 repo 裡** ——
這個 repo 是公開的，token 進來就等於公開。

## 它怎麼被觸發

`~/.claude/settings.json` 裡註冊了兩個 hook，Mac mini 上**所有** Claude Code
工作階段都會走到（不分目錄）：

```json
"hooks": {
  "Stop":         [{ "hooks": [{ "type": "command", "command": "...claude_notify.py ...", "async": true }] }],
  "Notification": [{ "hooks": [{ "type": "command", "command": "...claude_notify.py ...", "async": true }] }]
}
```

`async: true` 代表它在背景跑，不會拖慢 Claude。腳本本身也把所有例外吞掉、永遠
回傳 0 —— 通知壞掉絕不能讓你的工作階段跟著壞掉。改過 hook 之後要開一次
`/hooks` 或重開工作階段，設定才會重新載入。

## 訊息長什麼樣

```
✅ 任務完成 · claude-7b
📁 SumerTWRobotTest1 · main

做了什麼
（Claude 最後一則回覆的摘要，最多 700 字，保留換行）

⏱ 耗時 4 分 5 秒 · 12 次工具（Bash×8、Edit×3、Write×1）

🔢 上下文 201.9k · 本回合輸出 54.2k
📊 方案用量 5 小時 42% · 7 天 18%
🤖 claude-opus-5
```

## 用量數字的來源，以及它的限制

- **上下文 / 本回合輸出**：從逐字稿算的，準確且即時。
- **方案用量（5 小時 / 7 天 %）**：來自桌面 App 寫的
  `~/Library/Application Support/Claude/plan-usage-history.json`。
  **這是 App 自己抽樣寫下的，App 沒在跑就不會更新。** 超過 2 小時沒更新，
  訊息會直接標「已 N 小時沒更新，僅供參考」，不會假裝是即時數字。

CLI 的逐字稿裡沒有任何 rate-limit 欄位，`claude` 也沒有印用量的子指令
（`/usage` 只在工作階段內），所以目前拿不到比這更即時的方案額度。

## 調整

```bash
./claude_notify.py show      # 看目前設定
```

編輯 `~/.claude-monitor/telegram.json`：

| 欄位 | 預設 | 意思 |
|---|---|---|
| `min_seconds` | 60 | 回合短於這麼多秒就不通知 |
| `min_tool_calls` | 5 | 工具次數少於這麼多也不通知（和上面是「且」的關係） |
| `idle_only_minutes` | 0 | 設成 >0 就只在你離開電腦這麼久之後才通知；0 = 一律通知 |
| `dedup_seconds` | 45 | 同一階段這麼多秒內不重複發同類型通知 |

「需要你決策」不受 `min_seconds` / `min_tool_calls` 限制 —— 等你回應的事一律通知。

## 疑難排解

日誌在 `~/Library/Logs/claude-notify.log`，每次判斷都會寫一行，包含**不通知的理由**。

手動試跑，不會真的發送：

```bash
echo '{"hook_event_name":"Stop","session_id":"<某個 session id>"}' | ./claude_notify.py --dry-run
```

## 和 Claude 看板的關係

看板（`claude-status.html`）是「拉」：你主動去 GitHub 看。這個是「推」：有事才找你。
看板目前在工具中心的暫停區，沒有自動更新。兩者共用 `claude_monitor.py` 的逐字稿解析。
