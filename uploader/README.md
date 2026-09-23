# 資料上傳器（laoliu uploader）

一個跑在 Mac mini 上的小型上傳伺服器。使用者從瀏覽器丟檔案進來、選一個分類，
檔案就直接落在這台機器的工作目錄底下，成為之後開發工具的原始資料。

只用 Python 標準函式庫，**沒有任何外部套件**，macOS 內建的 `/usr/bin/python3` 就能跑。

## 為什麼不是純靜態網頁

GitHub Pages 是靜態的，沒辦法把檔案寫回 Mac mini；而且 https 頁面被瀏覽器擋著，
不能 POST 到 `http://192.168.88.127`（mixed content）。
所以網頁是由這支伺服器自己送出的，git 上架的是**程式碼**。

## 檔案放在哪

```
/Volumes/FCP 512GB/Claude/uploads/
├── <分類>/<YYYYmmdd-HHMMSS>__<原始檔名>
├── _manifest.jsonl     每筆上傳一行 JSON：分類、原始檔名、大小、sha256、標籤、備註、來源 IP
└── _categories.json    分類清單，可從網頁介面新增
```

`_manifest.jsonl` 是給之後寫工具用的索引，不需要再掃整個目錄。
上傳目錄在 repo 之外，所以不會被 git 追蹤。

用 `--root` 或環境變數 `UPLOAD_ROOT` 可以換位置。

## 啟動

```sh
./run.sh                       # 預設綁 0.0.0.0:8787
./run.sh --port 9000           # 換 port
```

第一次啟動會產生一組上傳密碼，存在 `~/.laoliu-uploader/token`（權限 600），
並印在終端機上。之後每次啟動都會沿用同一組。要自己指定就設 `UPLOAD_TOKEN`。

開機自動啟動：

```sh
./install-launchd.sh                                   # 安裝 launchd agent
launchctl bootout gui/$(id -u)/com.laoliu.uploader      # 停用
```

日誌在 `~/Library/Logs/laoliu-uploader/`。

## 怎麼用

**區網**：同一個 Wi-Fi 底下打開 `http://192.168.88.127:8787/`，輸入上傳密碼，
選分類 →（選填標籤與備註）→ 拖檔案進去。可多選，逐檔顯示進度。

**外網**：

```sh
brew install cloudflared     # 只需一次
./tunnel.sh                  # 印出一組 https://xxxx.trycloudflare.com 網址
```

這是 Cloudflare 的 quick tunnel，網址每次重跑都會變，適合臨時分享。
要固定網址就得去 Cloudflare 開具名 tunnel。

## 安全性

對外開放時，這個端點是「誰拿到網址就能寫檔進你的 Mac mini」，所以：

- 所有 API（除了 `/api/ping`）都要密碼，用 `hmac.compare_digest` 比對，失敗延遲 0.5 秒。
- 密碼存在家目錄而非 repo；`.gitignore` 另外擋一層。
- 檔名只取最後一段、去掉控制字元與路徑分隔符，`../../etc/pwned.txt` 會變成 `pwned.txt`。
- 分類只允許一層，`..` 與路徑分隔符直接 400；最終路徑還會再解析一次確認沒有跑出
  上傳目錄外，連 symlink 指出去也會被擋。
- 單檔上限 2 GiB，請求主體分塊寫入，寫到 `.part` 成功後才改名，中斷不會留半個檔。
- 伺服器只送自己 `static/` 底下的檔案，**不會**把上傳目錄當網頁根目錄送出去。

quick tunnel 的網址雖然不好猜，但終究是公開網際網路。長期對外請改用具名 tunnel
並在 Cloudflare Access 那層再加一道驗證。

## API

| 方法 | 路徑 | 說明 |
| --- | --- | --- |
| `GET` | `/api/ping` | 健康檢查，不需驗證 |
| `POST` | `/api/login` | `{"token": "..."}`，成功後種下 cookie |
| `GET` | `/api/config` | 分類清單、上傳目錄、大小上限 |
| `POST` | `/api/upload?category=&name=&tags=&note=` | 請求主體就是檔案原始位元組 |
| `POST` | `/api/category` | `{"name": "..."}` 新增分類 |
| `GET` | `/api/recent` | 最近 30 筆上傳紀錄 |

一個請求一個檔案、metadata 走 query string，所以不需要解析 multipart，
大檔也只佔幾百 KB 記憶體。用 `X-Upload-Token` 標頭就能從 curl 直接上傳：

```sh
curl -H "X-Upload-Token: $(cat ~/.laoliu-uploader/token)" \
     -X POST --data-binary @report.pdf \
     "http://192.168.88.127:8787/api/upload?category=research&name=report.pdf"
```
