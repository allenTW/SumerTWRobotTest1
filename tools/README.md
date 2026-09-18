# Claude 看板（工具中心第三個功能）

在公司只能看 GitHub 網頁時，用來確認 Mac mini 上的 Claude 在做什麼。**唯讀**，
看板上沒有任何可以下指令的東西。

## 組成

| 檔案 | 作用 |
|---|---|
| `claude_monitor.py` | 收集器。讀本機狀態檔，產生 `../claude-status.json`，commit 並推送 |
| `com.allentw.claude-monitor.plist` | launchd 排程，每 60 秒跑一次收集器 |
| `install-monitor.sh` | 安裝 / 移除 / 查看排程 |
| `../claude-status.html` | 看板頁面，每 60 秒重新抓一次 JSON |

## 安裝

```bash
cd "/Volumes/FCP 512GB/Claude/SumerTWRobotTest1/tools"
./install-monitor.sh            # 安裝並馬上跑一次
./install-monitor.sh status     # 確認有在跑
```

網址：<https://allentw.github.io/SumerTWRobotTest1/> → 工具中心 → 🖥 Claude 看板。

### 必要的一次性授權：完全取用磁碟

這個 repo 放在外接 USB 碟上。launchd 代理程式預設**沒有**存取外接碟的權限
（互動式終端機有，所以手動跑得動、排程跑不動），日誌會出現：

```
can't open file '.../claude_monitor.py': [Errno 1] Operation not permitted
```

在 Mac mini 上做一次就好：

1. 系統設定 → 隱私權與安全性 → **完全取用磁碟**
2. 按 ＋ → 在檔案選擇視窗按 `Cmd+Shift+G` → 貼上
   `/Library/Developer/CommandLineTools/usr/bin/python3`
3. 打開它的開關
4. `launchctl kickstart -k gui/$(id -u)/com.allentw.claude-monitor`

代價要知道：**這台機器上所有用這個 python3 執行的腳本都會拿到完整磁碟存取權**，
不只是這個收集器。

### 不授權的替代做法

不想給 python3 這麼大的權限，就把監控用的 clone 放進家目錄（家目錄不受這層保護）：

```bash
git clone https://github.com/allenTW/SumerTWRobotTest1.git ~/claude-status-repo
# 把 plist 裡的 CLAUDE_MONITOR_REPO 指過去，並把 ProgramArguments 的腳本路徑
# 也改成 ~/claude-status-repo/tools/claude_monitor.py
```

代價也要知道：從此有兩個 clone 在推同一個 branch，看板每分鐘推一次，
所以**外接碟上那個 clone 每次要推東西前都得先 `git pull --rebase`**，
不然一定被拒。日常發報告的摩擦會變大，所以預設選了上面那條路。

## 看板上的欄位

- **狀態** — `▶ 執行中`（Claude 正在處理）、`⏸ 閒置`（等你輸入）、
  `⚠ 停滯`（標成忙碌但 10 分鐘沒有新紀錄，通常是卡在權限確認或網路）、`■ 已結束`。
- **最後動作** — 最後一次呼叫的工具（Bash / Edit / WebFetch…）與多久以前。
- **上下文** — 目前這一輪送進模型的 token 數，接近上限時代表快要壓縮對話了。
- **累計** — 逐字稿筆數與工具呼叫次數。原本就很大的逐字稿會標「從監控啟動起算」，
  因為收集器不會回頭重算幾十 MB 的歷史。
- **程式庫狀態** — 分支、未提交檔案數、未推送 commit 數、最後一筆 commit。

資料時間超過 8 分鐘沒更新會出現黃色警告，超過 20 分鐘變紅色 —— 看板自己會告訴你
它壞了，不會安靜地顯示過期資料。

## 隱私

發佈目標 `SumerTWRobotTest1` 是**公開** repo，密碼閘只是裝飾。所以預設
`CLAUDE_MONITOR_DETAIL=standard`：只發佈中繼資料（工作階段名稱、專案路徑、
工具名稱、token 數、commit 標題），**不含任何對話內容**。

| 層級 | 內容 |
|---|---|
| `minimal` | 只有名稱、狀態、時間；路徑只留最後一層目錄 |
| `standard`（預設） | 加上完整路徑、分支、模型、工具名稱、token、commit 標題 |
| `verbose` | 再加上最後一則指示與回覆的摘錄 —— 等於把工作內容公開，請先想清楚 |

改法：編輯 plist 裡的 `CLAUDE_MONITOR_DETAIL`，再跑一次 `./install-monitor.sh`。

想完全不公開的話，把 `CLAUDE_MONITOR_REPO` 指到一個**私有** repo，在公司改用
GitHub 網頁看該 repo 裡的 `claude-status.json`（私有 repo 不能用 GitHub Pages，
所以看得到原始 JSON、看不到這個排版好的頁面）。

## 更新頻率：為什麼不是真的每分鐘

收集是每分鐘做一次（純本機，很便宜），但**發佈**被 GitHub 的免費靜態託管卡住：

| 來源 | 落後多久 | 原因 |
|---|---|---|
| GitHub Pages | 約 1–2 分鐘 | 每次推送都要重新建置（實測 35–65 秒），分支式流程還有每小時 10 次建置的軟性上限 |
| raw.githubusercontent | 最多 5 分鐘 | 不必建置，但 CDN 快取 300 秒，而且**會忽略查詢字串**，`?t=` 這種手法對它無效 |

所以看板同時問兩個來源、取比較新的那份，並且把推送節流成：**有變動最快 3 分鐘推一次，
沒變動每 10 分鐘送一次心跳**。實際看到的狀態大約落後 1–4 分鐘。

一分鐘推一次的話，建置會排隊互相蓋掉（實測已經出現 `errored` 的建置），
而且會排擠到你發報告時的建置 —— 這才是不設成一分鐘的主因。

想改：plist 裡的 `CLAUDE_MONITOR_MIN_PUSH`（秒）與 `CLAUDE_MONITOR_HEARTBEAT`（秒）。
真的要逼近一分鐘，就得把 Pages 換成 GitHub Actions 部署（`build_type=workflow`），
那條路沒有每小時建置上限 —— 但會動到現有報告網站的部署方式，弄壞就整站不更新，
所以沒有自作主張改。

commit 訊息一律是 `status: Claude 看板 N 執行中 / N 閒置`，之後要整理歷史很好篩。

## 疑難排解

- **看板說資料過期** — `./install-monitor.sh status` 看日誌；外接碟沒掛載時收集器
  會直接結束並在日誌留一行。
- **推送失敗** — 日誌會寫原因，看板也會顯示黃色橫幅。launchd 用的是登入使用者的
  鑰匙圈，Mac mini 登出後 HTTPS 認證可能拿不到；讓它保持登入狀態。
- **手動跑一次**：
  ```bash
  /usr/bin/python3 claude_monitor.py                      # 正常跑（會推送）
  CLAUDE_MONITOR_PUSH=0 /usr/bin/python3 claude_monitor.py # 只產生檔案，不推送
  ```
