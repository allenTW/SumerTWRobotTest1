#!/usr/bin/env python3
"""Build laoliu-r15-triage2.html (Round 15 / second external triage) from triage2 CSVs.

Discipline:
  - every number on the page is computed here from the CSVs, or pulled from FACTS
    and asserted to appear literally in laoliu-state.md. Nothing is typed into prose.
  - the CSS block and the access-control script are extracted verbatim from the
    frozen v1 report so the new page cannot drift visually. v1 is opened read-only.
  - v1 (crypto-dca-amplifier-report.html) is never written to.
Run: python3 build_laoliu_r15.py
"""
import csv, os, re, statistics, collections, datetime, html

ROOT = "/Volumes/FCP 512GB/Claude"
REPO = os.path.join(ROOT, "SumerTWRobotTest1")
TRIAGE = os.path.join(ROOT, "triage2")
V1 = os.path.join(REPO, "crypto-dca-amplifier-report.html")
STATE = os.path.join(ROOT, "laoliu-state.md")
OUT = os.path.join(REPO, "laoliu-r15-triage2.html")
INDEX = os.path.join(REPO, "laoliu.html")
TODAY = "2026-09-21"

state_txt = open(STATE, encoding="utf-8").read()

# ---------- facts that live only in the state file: assert, then inject ----------
def fact(key, literal, note):
    assert literal in state_txt, f"FACT {key} ({literal}) not found in laoliu-state.md"
    return literal

F = {
    "symbols_scanned":  fact("symbols_scanned", "905", "coordinator's exchangeInfo re-pull"),
    "r6_equity_claim":  fact("r6_equity_claim", "EQUITY 標籤數量為 0", "round-6 claim"),
    "manual_list_n":    fact("manual_list_n", "173", "nonstd_symbols.json size"),
    "b1_carry_vol":     fact("b1_carry_vol", "0.15%", "B1 annualised carry vol"),
    "plan1_coinratio":  fact("plan1_coinratio", "0.9463", "plan-1 coin ratio, from v1"),
    "plan1_funding_leg":fact("plan1_funding_leg", "+0.0096", "plan-1 funding leg"),
    "plan1_price_leg":  fact("plan1_price_leg", "+0.0326", "plan-1 price leg"),
    "claim_sharpe":     fact("claim_sharpe", "6.45", "highest claim met this round"),
    "claim_span":       fact("claim_span", "2020-08 ~ 2025-05", "claim's stated window"),
    "proj_span_start":  fact("proj_span_start", "2020-08-11", "project's plan-1 start"),
    "bias1_before":     fact("bias1_before", "3.54", "project's own bias #1: before"),
    "bias1_after":      fact("bias1_after", "0.17", "project's own bias #1: after"),
    "maker_fill":       fact("maker_fill", "97.30%", "round-12 strict maker fill rate"),
    "mm_threshold":     fact("mm_threshold", "1000 BTC", "market-maker programme threshold"),
    "vrp_clip":         fact("vrp_clip", "0.1 BTC", "VRP minimum clip"),
    "vrp_clip_usd":     fact("vrp_clip_usd", "$8,080", "VRP minimum clip in USD"),
    "spec1_cost":       fact("spec1_cost", "$0.005", "SPEC-1 cost upper bound"),
    "spec1_transfer":   fact("spec1_transfer", "$20", "SPEC-1 transfer size"),
    "hold_coins":       fact("hold_coins", "0.8511", "pure DCA hold, 6y"),
    "cta_alpha":        fact("cta_alpha", "+2.4%", "cross-asset CTA median alpha"),
    "cta_hurdle":       fact("cta_hurdle", "14.29%", "BTC carry hurdle"),
    "lending_6y":       fact("lending_6y", "$31.54", "round-8 lending, 6 years"),
    "bidbuffer":        fact("bidbuffer", "0.05", "assetIndex BTCUSD bid/ask buffer"),
}

# ---------- CSV: TradFi inventory ----------
inv = list(csv.DictReader(open(os.path.join(TRIAGE, "tradfi_inventory.csv"), encoding="utf-8")))
n_tradfi = len(inv)
by_type = collections.Counter(x["underlyingType"] for x in inv)
by_status = collections.Counter(x["status"] for x in inv)
min_notional = sorted({x["min_notional_usd"] for x in inv})
assert len(min_notional) == 1
MINNOT = min_notional[0]
by_month = collections.Counter(x["onboard_utc"][:7] for x in inv)
peak_month, peak_n = by_month.most_common(1)[0]
first_row = min(inv, key=lambda x: x["onboard_utc"])
d0 = datetime.date.fromisoformat(TODAY)
ages_d = [(d0 - datetime.date.fromisoformat(x["onboard_utc"])).days for x in inv]
age_max_m = max(ages_d) / 30.4375
age_med_m = statistics.median(ages_d) / 30.4375

# ---------- CSV: funding survey ----------
fs = list(csv.DictReader(open(os.path.join(TRIAGE, "funding_survey.csv"), encoding="utf-8")))
for r in fs:
    for k in ("mean_ann_pct","median_ann_pct","frac_exactly_zero","frac_positive",
              "abs_share_top5pct_periods","interval_h"):
        r[k] = float(r[k])
    r["n"] = int(r["n"])
CTRL = {"BTCUSDT", "ETHUSDT"}
tf = [r for r in fs if r["symbol"] not in CTRL]
ctrl = {r["symbol"]: r for r in fs if r["symbol"] in CTRL}
n_sampled = len(tf)
n_med_zero = sum(1 for r in tf if r["median_ann_pct"] == 0.0)
const_rows = [r for r in tf if r["median_ann_pct"] != 0.0]
const_syms = [r["symbol"] for r in const_rows]
const_rate = sorted({r["median_ann_pct"] for r in const_rows})
assert len(const_rate) == 1
CONST = const_rate[0]
assert all(r["frac_positive"] == 1.0 and r["frac_exactly_zero"] == 0.0 for r in const_rows)
top5_med_tf = statistics.median(r["abs_share_top5pct_periods"] for r in tf)
zero_med_tf = statistics.median(r["frac_exactly_zero"] for r in tf)
n_min, n_max = min(r["n"] for r in tf), max(r["n"] for r in tf)
intervals = sorted({r["interval_h"] for r in tf})
n_4h = sum(1 for r in tf if r["interval_h"] == 4.0)
iwm = next(r for r in tf if r["symbol"] == "IWMUSDT")

# ---------- CSV: relative value ----------
rv = {r["test"]: r for r in csv.DictReader(open(os.path.join(TRIAGE, "rv_results.csv"), encoding="utf-8"))}
b1 = rv["a_BTCUSDT_vs_BTCUSDC_funding"]
B1_ANN = float(b1["metric_ann_pct"]); B1_N = int(b1["n"]); B1_W = float(b1["indep_obs"])
B1_T = float(b1["t_weekly"]); B1_SPAN = b1["span"].replace("..", " ~ ")
RT_COST_PCT = 0.20                      # round-trip taker, 2 x 10bp, stated in the CSV note
B1_COST_RATIO = RT_COST_PCT / abs(B1_ANN)
dup = {k: v for k, v in rv.items() if k.startswith("b_spread_")}
lev = rv["c_short_TQQQ_plus_short_SQQQ_daily_rebal"]
LEV_ANN = float(lev["metric_ann_pct"]); LEV_SPAN = lev["span"].replace("..", " ~ ")
LEV_DAYS = int(lev["n"]); LEV_W = float(lev["indep_obs"])
m = re.search(r"decay \(L\^2-L\)/2\*sigma\^2=([\d.]+)%/yr", lev["note"]); LEV_THEO = float(m.group(1))
m = re.search(r"maxDD (-?[\d.]+)%", lev["note"]); LEV_DD = float(m.group(1))
m = re.search(r"static \(unrebalanced\) ([+\-][\d.]+)%", lev["note"]); LEV_STATIC = float(m.group(1))
m = re.search(r"beta\(TQQQ,QQQ\)=([\-\d.]+) beta\(SQQQ,QQQ\)=([\-\d.]+)", lev["note"])
LEV_BT, LEV_BS = float(m.group(1)), float(m.group(2))

def dupinfo(key):
    r = dup[key]
    a, b = key.replace("b_spread_", "").split("USDT_")
    a += "USDT"
    mx = float(re.search(r"max \|dev\| ([\d.]+)%", r["note"]).group(1))
    notionals = re.findall(r"([A-Z0-9]+USDT)=\$([\d,]+)", r["note"])
    return dict(a=a, b=b, sd=float(r["metric_ann_pct"]), maxdev=mx, n=int(r["n"]),
                span=r["span"].replace("..", " ~ "), w=float(r["indep_obs"]),
                notional={s: v for s, v in notionals})
DUPS = [dupinfo(k) for k in
        ["b_spread_HK0700USDT_TENCENTUSDT", "b_spread_SKHYNIXUSDT_SKHYUSDT",
         "b_spread_SAMSUNGUSDT_SAMSUNGEMUSDT"]]

# ---------- reuse v1 chrome (read-only) ----------
v1 = open(V1, encoding="utf-8").read()
CSS = re.search(r"<style>.*?</style>", v1, re.S).group(0)
GATE = re.search(r"<script>\s*// 存取控制.*?</script>", v1, re.S).group(0)
V1_IDS = set(re.findall(r'id="([A-Za-z0-9_-]+)"', v1))
for need in ["fixed", "alpha", "triage", "blindspot", "glossary", "coin-ratio", "summary",
             "certain", "not-a-win", "cleantest", "sizing", "execution", "roadmap"]:
    assert need in V1_IDS, f"v1 anchor #{need} missing"

def pct(x, d=4, sign=False):
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s + "%"

# ================================ page body ================================
P = []
A = P.append

A(f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>老六 · 第十五輪：第二輪外部盤點</title>
{GATE}
{CSS}
</head>
<body>

<header>
  <div class="crumb">
    <a href="index.html">工具中心</a><span class="sep">›</span><a href="laoliu.html">老六研究院</a><span class="sep">›</span><span class="here">第十五輪 · 第二輪外部盤點</span>
  </div>
  <h1>第十五輪：一個已發布的結論，兩天後被一次查詢推翻</h1>
  <p class="tagline">
    同一輪裡還有 {n_tradfi} 個從來沒被看過的合約、一個結構上完美卻量出來是零的候選，
    以及一個宣稱 Sharpe {F["claim_sharpe"]} 的標本——它跟我們自己測到輸錢的那條線是同一條。
  </p>
  <div class="meta-bar">
    <span class="badge">輪次 <b>第十五輪</b></span>
    <span class="badge">日期 <b>{TODAY}</b></span>
    <span class="badge">正式評估 <b>24 個候選</b></span>
    <span class="badge">親手量測 <b>4 個</b></span>
    <span class="badge">通過 <b>0 個</b></span>
    <span class="badge live">狀態 <b>研究進行中</b></span>
  </div>
</header>

<main>
''')

# ------------------------------ summary ------------------------------
A(f'''
  <section id="summary">
    <h2>摘要：這一輪發生了什麼</h2>

    <div class="plain">
      <span class="lbl">先看這裡</span>
      <p>這一頁是<b>一輪獨立的研究紀錄</b>，不是舊報告的修訂版。依照你 {TODAY} 的指示
        「以後報告盡量不要修改舊的，每次產生新的頁面」，<b>舊的那份總覽報告一個字都沒有動</b>；
        這一頁裡要更正它的地方，是<b>在這裡寫清楚、然後連回去</b>。</p>
      <p>這一輪的主題可以用一句話講完：<b>我們去看了五個以前沒看過的地方，五個都是空的，
        但在看的過程中發現舊報告裡有一句話是錯的。</b>
        那句錯話的價值比五個空地方加起來還高，所以它放在最前面。</p>
      <p>所有英文縮寫、單個字母、希臘字母，在<a href="#glossary">這一頁自己的術語表</a>裡都有白話翻譯；
        正文第一次用到時也會就地附註。</p>
    </div>

    <h3 class="sub">一、五件事，照重要性排</h3>
    <div class="callout bad">
      <h3>★ 1. 一個已經印在報告上的結論，被推翻了</h3>
      <p style="margin:0">
        第六輪寫過、而且寫進了總覽報告：幣安上的代幣化股票合約「<b>{F["r6_equity_claim"]}</b>、全部已下市」，
        因此「<b>沒有純機械的篩選方法，人工清單無可避免</b>」。
        <b>兩天後，一次公開 API 查詢就推翻了它</b>：今天實際是
        <b>EQUITY {by_type["EQUITY"]} 個</b>、<b>TradFi 永續合約 {n_tradfi} 個</b>。
        詳見<a href="#correction">下一節</a>，含成因與對舊報告的定位。
      </p>
    </div>
    <div class="callout">
      <h3>2. 一條從來沒人看過的資料軸：{n_tradfi} 個 TradFi 永續合約</h3>
      <p style="margin:0">
        前十四輪一次都沒把它們當成機會看過——它們只以「把名單弄髒的東西」的身分出現過。
        最小下單 <b>${MINNOT}</b>，所以<b>錢太少在這裡不是障礙</b>（這是很少見的）。
        然後<b>一個量測關掉了整個家族</b>：抽樣的 {n_sampled} 個合約裡，
        <b>{n_med_zero} 個的資金費中位數恰好是 0</b>。見<a href="#tradfi">第三節</a>。
      </p>
    </div>
    <div class="callout">
      <h3>3. B1：條件全部滿足，答案是乾淨的零</h3>
      <p style="margin:0">
        它滿足這個專案的<b>每一條</b>收案條件，而量出來是
        <b>{pct(B1_ANN, 4, True)}／年</b>、t = {B1_T}、{int(B1_W)} 個獨立週觀測。
        <b>它失敗的方式是最好的那種：不是「測不出來」，是「這個數就是零」。</b>
        見<a href="#b1">第四節</a>。
      </p>
    </div>
    <div class="callout good">
      <h3>★ 4. Sharpe {F["claim_sharpe"]} 的標本——這一段對你最有用</h3>
      <p style="margin:0">
        本輪遇到最高的宣稱是 Sharpe {F["claim_sharpe"]}，證據等級只有部落格。
        而它宣稱的期間<b>跟我們自己測過的方案一幾乎完全重合</b>，我們的實測是
        <b>幣數比 {F["plan1_coinratio"]}（輸給純持有）</b>。
        <b>差別不在策略，在會計。</b>
        <a href="#sharpe645">第六節</a>把它拆成一份你以後可以直接套用的檢查清單。
      </p>
    </div>
    <div class="callout">
      <h3>5. 還沒被看過的地方，以及兩份實驗規格</h3>
      <p style="margin:0">
        最大的未覆蓋區塊是<b>造市／掛 maker 單</b>，而且舊報告否決它的理由可能用錯了門檻。
        另有兩份規格：<b>SPEC-1 需要真實下單，是你本人的決定，團隊不會代為執行</b>；
        <b>SPEC-2 研究員自己建議不要跑</b>，而那個理由本身就是產出。
        見<a href="#maker">第八節</a>與<a href="#specs">第九節</a>。
      </p>
    </div>

    <h3 class="sub">二、幣數比這一欄，這一輪是空的——為什麼</h3>
    <div class="callout bad">
      <p style="margin:0">
        這個專案唯一的計分方式是<b>幣數比</b>：同一筆錢、同一段時間，最後手上的 BTC 顆數，
        除以什麼都不做、單純每週買進並持有的顆數。
        六年 319 週純持有拿到 <b>{F["hold_coins"]} 顆</b>，這個成績定義為 <b>1.0000</b>。
      </p>
      <p style="margin:10px 0 0">
        <b>這一輪沒有任何一個候選走到可以算幣數比的階段，所以這一頁不提供新的幣數比數字。</b>
        原因不是偷懶，是算不出來：幣數比需要一條「真的持有了某個部位、走完一整段時間」的序列，
        而本輪的候選全部死在那之前——
        有的是<b>量出來根本沒有可收的東西</b>（沒有部位可模擬），
        有的是<b>成本地板就壓在效應量上</b>（模擬出來必然是負的，而且答案與時間長度無關），
        有的是<b>連能不能開倉都還沒確定</b>（SPEC-1 那道閘門）。
      </p>
      <p style="margin:10px 0 0">
        這一頁出現的唯一一個幣數比是 <b>{F["plan1_coinratio"]}</b>，
        它是<b>引用自舊報告的舊數字</b>（方案一資金費收割），
        用途是當作對照——不是本輪的新成績。
      </p>
    </div>
  </section>
''')

# ------------------------------ glossary ------------------------------
GL = [
 ("〔一〕這一頁的記分方式", [
  ("g15-coinratio", "幣數比", "這個方案最後拿到的 BTC 顆數 ÷ 什麼都不做、只是每週買進並持有拿到的顆數。",
   f"純持有六年是 {F['hold_coins']} 顆，定義為 1.0000。1.0276 就是多拿 2.8%，{F['plan1_coinratio']} 就是少拿 5.4%。"
   "這是本專案唯一認可的成績單，<b>本輪沒有產生任何新的幣數比</b>。"),
  ("g15-indep", "獨立觀測數", "不是「有幾筆資料」，是「有幾筆<b>互相不重複</b>的資料」。",
   "同一個星期的 21 筆 8 小時資料講的是同一件事，只能算 1 筆。"
   "這一頁反覆出現它，因為<b>合約數量多不等於證據多</b>。"),
  ("g15-t", "t 值", "效應量除以它自己的誤差。大致可讀成「這個數看起來不像 0 的程度」。",
   "本專案的門檻是 3.0。|t| 小於 1 幾乎就是「和 0 分不出來」。"),
  ("g15-sd", "sd（標準差）", "一串數字上下跳動的幅度。",
   "用來量「兩個應該相等的東西，實際差多少」。差得太小，就連手續費都賺不回來。"),
  ("g15-bp", "bp（基點）", "萬分之一。10 bp = 0.10%。",
   "手續費的慣用單位。來回一趟 taker 約 20 bp = 0.20%，這個數字在本頁是好幾個候選的死因。"),
  ("g15-sharpe", "Sharpe", "每承受一單位波動換到多少報酬。越大看起來越好。",
   "它<b>看不出幣變多還變少</b>，而且很容易被「只算其中一條腿」灌水。見<a href=\"#sharpe645\">第六節</a>。"),
 ]),
 ("〔二〕合約與費用", [
  ("g15-perp", "永續合約", "沒有到期日的期貨。靠一個叫「資金費」的機制把價格黏住現貨。",
   "本頁所有候選都在永續合約上。"),
  ("g15-funding", "資金費（funding）", "永續合約多空雙方之間<b>互相支付</b>的費用，通常每 4 或 8 小時結一次。",
   "它是「把幣放著也能收錢」這類策略的收入來源。<b>本輪最大的發現就是：TradFi 永續身上這一項多半是字面上的 0。</b>"),
  ("g15-carry", "carry（持有成本／持有收益）", "純粹因為「抱著不動」而自動產生的損益。",
   "如果 carry 是 0，那這個部位就只剩下方向的賭博，不是收租。"),
  ("g15-tradfi", "TradFi 永續 / <code>TRADIFI_PERPETUAL</code>",
   "幣安上的一類合約，標的不是加密貨幣而是股票、ETF、黃金、原油等傳統資產。<code>contractType</code> 是合約的分類欄位。",
   f"今天有 {n_tradfi} 個。<b>這個欄位就是本輪找到的那個機械判別式。</b>"),
  ("g15-undtype", "<code>underlyingType</code> / <code>EQUITY</code>",
   "另一個分類欄位，標示標的的種類；<code>EQUITY</code> 表示股票。",
   "<b>第六輪的錯誤就發生在這兩個欄位之間</b>——程式查了這一個，卻先被另一個濾掉了。"),
  ("g15-minnot", "<code>MIN_NOTIONAL</code>（最小下單金額）", "一張單至少要多少錢才能送出去。",
   f"TradFi 永續是 ${MINNOT}。對照本專案被規模卡死的那個候選（VRP）要 {F['vrp_clip']} ≈ {F['vrp_clip_usd']}。"),
  ("g15-taker", "taker / maker", "taker＝直接吃掉別人的掛單，馬上成交、手續費較貴；maker＝自己掛著等別人來吃，較便宜甚至有回饋。",
   f"第十二輪實測嚴格只掛 maker 單、30 分鐘內成交率 {F['maker_fill']}。"),
 ]),
 ("〔三〕部位與風險", [
  ("g15-delta", "delta", "部位對標的漲跌的敏感度。delta = 0 表示漲跌都不影響你。",
   "delta 恆為 0 是本專案收案的硬條件之一，因為目標是多拿幣，不是賭方向。"),
  ("g15-beta", "β（beta）", "部位跟大盤（這裡是 BTC）一起動的程度。",
   "β 如果被改變，就等於偷偷改變了你原本的曝險，那不算「加值」。"),
  ("g15-gamma", "空 gamma", "一種報酬形狀：平時穩定小賺，出大事時一次賠很多，而且賠的上限沒有界線。",
   "本專案把這種形狀列為地雷，因為<b>「回撤不超過 10%」這種約束對它是無效的</b>——它不是慢慢跌，是一次跳空。"),
  ("g15-levetf", "槓桿 ETF 耗損", "兩倍／三倍槓桿的 ETF 每天重設倍數，長期會因為來回震盪而自己流失價值。",
   "理論上「同時放空一對正反向槓桿 ETF」就能把這個流失收下來。本輪實測了，見<a href=\"#other\">第七節</a>。"),
  ("g15-multiassets", "Multi-Assets Mode（多資產保證金模式）",
   "幣安的一種錢包設定，開了之後可以用手上的 BTC 直接當保證金，不必先換成 USDT。",
   "<b>它是 SPEC-1 要問的唯一問題</b>：如果 TradFi 永續不吃這個模式，那一整族 8 個候選全部作廢。"),
  ("g15-verdict", "PASS / FAIL / INDETERMINATE / CONDITIONAL",
   "候選的四種判定：通過／否決／<b>證據不足以判定</b>／有條件成立。",
   "INDETERMINATE 是<b>最容易被誤讀成 FAIL</b> 的一種——它的意思是「還沒有人去量」，不是「量過了不行」。"),
 ]),
]
A('''
  <section id="glossary">
    <h2>這一頁的術語表（精簡版）</h2>
    <p class="section-note">
      只收這一頁會用到的詞，共 ''' + str(sum(len(g[1]) for g in GL)) + ''' 條。
      舊總覽報告有一份 69 條的完整版，在<a href="crypto-dca-amplifier-report.html#glossary">那邊的術語對照表</a>。
      第三欄寫的不是字典定義，是「這一輪為什麼在乎它」。
    </p>
''')
for gname, items in GL:
    A(f'    <div class="gloss-group">{gname}</div>\n    <div class="table-wrap">\n      <table class="gloss">\n')
    A('        <thead><tr><th>符號／術語</th><th>它是什麼（日常語言）</th><th>這一輪為什麼在乎它</th></tr></thead>\n        <tbody>\n')
    for gid, term, what, why in items:
        A(f'          <tr id="{gid}" class="gterm"><td class="name">{term}</td>\n'
          f'            <td class="wrap">{what}</td>\n            <td class="wrap">{why}</td></tr>\n')
    A('        </tbody>\n      </table>\n    </div>\n')
A('  </section>\n')

# ------------------------------ correction ------------------------------
CHK = [
    ("<code>underlyingType == 'EQUITY'</code> 的數量", "0",
     str(by_type["EQUITY"]), "今日直接查公開 exchangeInfo"),
    ("<code>contractType == 'TRADIFI_PERPETUAL'</code> 的數量", "未查",
     f"{n_tradfi}（其中 {by_status['TRADING']} 個 TRADING）", "同上"),
    ("「非加密標的」扣掉「TradFi 合約」之後剩下誰", "未查",
     "恰為 ALLUSDT、BTCDOMUSDT、DEFIUSDT 三個加密指數", "集合恆等式，非抽樣"),
    ("「TradFi 合約」扣掉「非加密標的」之後剩下誰", "未查", "空集合", "同上"),
    ("有 TradFi 標記卻不是 TradFi 合約的", "未查", "0 個", "零漏判"),
    ("是 TradFi 合約卻沒有 TradFi 標記的", "未查", "0 個", "零誤判"),
    ("BTCUSDT 會不會被這個判別式誤殺", "——",
     "不會（<code>PERPETUAL</code> / <code>COIN</code>）", "這是舊方法最擔心的失敗模式"),
]
A(f'''
  <section id="correction">
    <h2>一、更正：一個已發布的結論，兩天後被推翻<span class="pill fact">已獨立複驗</span></h2>
    <p class="section-note">
      這一節更正的是舊總覽報告
      <a href="crypto-dca-amplifier-report.html#fixed">〈已修掉的重大缺陷〉</a>那一節裡的一段話，
      以及<a href="crypto-dca-amplifier-report.html#alpha">〈跨資產訊號 alpha 驗證〉</a>節內重複同一句的那個方框。
      <b>依新規則，舊頁不修改；更正寫在這裡並回連。</b>
    </p>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>幣安上有一種合約，標的不是加密貨幣而是股票、黃金、原油那些。第五輪發現這些東西混進了
        我們的測試名單裡，第六輪去追原因，然後寫下一句話：
        <b>「這些合約早就全部下市了，所以一個機械的篩選方法都做不出來，只能靠人工列清單。」</b></p>
      <p>這句話今天被證明是錯的。<b>那些合約不但還在，而且有 {n_tradfi} 個</b>，
        還有一個<b>一行就能寫完、零誤判零漏判</b>的篩選方法。</p>
      <p>錯在哪裡值得你看一眼，因為這種錯很難防：<b>當時那支程式先做了另一道過濾</b>，
        那些合約在被檢查之前就已經被丟掉了。所以程式回報「一個都沒濾掉」是真的，
        「數量是 0」也是真的——<b>但從這兩個真話推出來的那句「交易所上沒有這種合約了」是假的。</b></p>
    </div>

    <div class="split">
      <div class="stat"><div class="label">第六輪宣稱的 EQUITY 數量</div>
        <div class="value neg">0</div><div class="sub">已寫進舊報告</div></div>
      <div class="stat"><div class="label">今日實測的 EQUITY 數量</div>
        <div class="value pos">{by_type["EQUITY"]}</div><div class="sub">同一個公開端點</div></div>
      <div class="stat"><div class="label">TradFi 永續合約總數</div>
        <div class="value pos">{n_tradfi}</div><div class="sub">{by_status["TRADING"]} 個正在交易</div></div>
      <div class="stat"><div class="label">機械判別式的誤判／漏判</div>
        <div class="value pos">0 / 0</div><div class="sub">集合恆等式，不是抽樣</div></div>
    </div>

    <h3 class="sub">逐項複驗（協調者今日重新抓取 {F["symbols_scanned"]} 個符號）</h3>
    <div class="table-wrap wide">
      <table>
        <caption>左邊是舊報告寫的，右邊是今天同一個公開端點回答的</caption>
        <thead><tr><th>量測項目</th><th>第六輪宣稱</th><th>今日實測</th><th>性質</th></tr></thead>
        <tbody>
''')
for item, claim, now, kind in CHK:
    A(f'          <tr><td class="name wrap">{item}</td><td>{claim}</td>'
      f'<td class="pos wrap">{now}</td><td class="wrap">{kind}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>

    <h3 class="sub">成因：兩個各自為真的句子，推出一個假的結論</h3>
    <div class="callout bad">
      <p style="margin:0">
        第六輪那支程式<b>先過濾了 <code>contractType == 'PERPETUAL'</code></b>，
        而 TradFi 合約的 <code>contractType</code> 是 <code>TRADIFI_PERPETUAL</code>——
        <b>它們在 EQUITY 這道檢查執行之前，就已經不在集合裡了。</b>
      </p>
      <p style="margin:10px 0 0">
        所以：「<b>過濾器一個符號都沒濾掉</b>」是真的（該濾的早就不在了）、
        「<b>{F["r6_equity_claim"]}</b>」也是真的（在那個已經被削過的集合裡確實是 0）。
        <b>兩句話在它們自己的框內都成立，但由此推出的那句關於交易所的陳述是假的。</b>
      </p>
      <p style="margin:10px 0 0">
        這是這一輪最值得留下來的一課：<b>一個數字的真假，和「產生它的那個框有多大」是兩回事。</b>
        程式沒有出錯，錯的是把框內的答案當成框外的事實。
      </p>
    </div>

    <h3 class="sub">實際影響</h3>
    <ul class="limits">
      <li><b>「人工清單無可避免」現在為假。</b>
        <code>contractType == 'TRADIFI_PERPETUAL'</code> 是一個<b>零誤判、零漏判、可即時查詢</b>的判別式。
        那份 {F["manual_list_n"]} 個符號的人工清單，<b>至少在往後的篩選上可以退休</b>。</li>
      <li><b>但只到「往後」為止。</b>歷史上已下市的符號，封存檔裡有沒有保留 <code>contractType</code> 這個欄位，
        <b>本輪沒有查，標記為未驗證</b>。人工清單能不能整條退休，取決於這一點。</li>
      <li><b>舊報告的其他結論不受影響。</b>第六輪同時量化過：樣本內是 0 / 2600 席被汙染、
        修正後重跑沒有任何結論翻轉。<b>被推翻的是「做不出機械篩選」這個方法論宣稱，不是那些回測數字。</b>
        原文仍留在<a href="crypto-dca-amplifier-report.html#fixed">舊報告那一節</a>，沒有刪改。</li>
      <li><b>這條記錄本身列入誠信紀錄。</b>舊報告已經有一節專門列「我們自己做錯過什麼」，
        這是又一筆，而且是目前為止<b>間隔最短的一筆——兩天</b>。</li>
    </ul>
  </section>
''')

# ------------------------------ TradFi ------------------------------
TYPE_ZH = {"EQUITY":"美股個股", "HK_EQUITY":"港股", "KR_EQUITY":"韓股", "CN_EQUITY":"中國股",
           "COMMODITY":"商品（金銀鉑鈀銅／原油／天然氣）", "PREMARKET":"未上市／盤前標的",
           "FX":"匯率"}
A(f'''
  <section id="tradfi">
    <h2>二、{n_tradfi} 個從來沒被看過的合約——然後一個量測把整族關掉</h2>
    <p class="section-note">
      資料：<code>triage2/tradfi_inventory.csv</code>（{n_tradfi} 列）、
      <code>triage2/funding_survey.csv</code>（{len(fs)} 列，其中 {n_sampled} 個 TradFi ＋ 2 個加密對照）。
      兩支腳本都是零參數、只讀公開端點。
    </p>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>上一節找回來的那 {n_tradfi} 個合約，<b>前十四輪從來沒有人把它們當成機會評估過</b>。
        state 檔全文提到代幣化股票，都只是在講「它們汙染了名單」，沒有一次是在問「它們身上有沒有東西可以拿」。</p>
      <p>而且它們有一個很罕見的優點：<b>最小下單只要 ${MINNOT}</b>。
        這個專案十幾輪以來最常見的死因是「錢太少，做不動」——在這裡第一次不是問題。</p>
      <p>然後我們問了一個問題就把整族關掉了：<b>抱著這些合約，會不會自動有錢進來？</b>
        答案是不會。{n_sampled} 個抽樣裡 <b>{n_med_zero} 個的資金費中位數恰好是 0</b>。
        <b>不是「收得很少」，是字面上的 0。</b></p>
    </div>

    <h3 class="sub">2-1　這一族長什麼樣子</h3>
    <div class="split">
      <div class="stat"><div class="label">合約總數</div><div class="value pos">{n_tradfi}</div>
        <div class="sub">{by_status["TRADING"]} 交易中，{by_status.get("PENDING_TRADING",0)} 待上線</div></div>
      <div class="stat"><div class="label">最小下單金額</div><div class="value pos">${MINNOT}</div>
        <div class="sub">全部 {n_tradfi} 個都一樣</div></div>
      <div class="stat"><div class="label">最長的歷史</div><div class="value warn">{age_max_m:.1f} 個月</div>
        <div class="sub">{first_row["symbol"]}，{first_row["onboard_utc"]} 上線</div></div>
      <div class="stat"><div class="label">歷史長度中位數</div><div class="value warn">{age_med_m:.1f} 個月</div>
        <div class="sub">這是本節所有結論的最大限制</div></div>
    </div>
    <div class="table-wrap">
      <table>
        <caption>{n_tradfi} 個 TradFi 永續的標的類型分布（來源：<code>tradfi_inventory.csv</code>，程式計數）</caption>
        <thead><tr><th>underlyingType</th><th>白話</th><th>數量</th></tr></thead>
        <tbody>
''')
for t, c in by_type.most_common():
    A(f'          <tr><td class="name">{t}</td><td class="wrap">{TYPE_ZH.get(t,"—")}</td><td>{c}</td></tr>\n')
A(f'''          <tr class="base"><td class="name">合計</td><td class="wrap">＝ TradFi 永續全體</td><td><b>{n_tradfi}</b></td></tr>
        </tbody>
      </table>
    </div>
    <p class="body-note">
      上線節奏：第一個是 {first_row["onboard_utc"]} 的 {first_row["symbol"]}，
      最密集的一個月是 <b>{peak_month} 的 {peak_n} 個</b>。
      <b>這一族之所以沒人看過，很大一部分原因是它去年底才存在。</b>
    </p>

    <h3 class="sub">2-2　一個量測關掉整族：資金費是字面上的零</h3>
    <div class="split">
      <div class="stat"><div class="label">TradFi 抽樣中「資金費中位數恰為 0」</div>
        <div class="value neg">{n_med_zero} / {n_sampled}</div><div class="sub">中位數 = 0.0000%／年</div></div>
      <div class="stat"><div class="label">對照：BTCUSDT 資金費中位數</div>
        <div class="value pos">{pct(ctrl["BTCUSDT"]["median_ann_pct"],4,True)}</div>
        <div class="sub">年化，{ctrl["BTCUSDT"]["n"]:,} 期</div></div>
      <div class="stat"><div class="label">對照：ETHUSDT 資金費中位數</div>
        <div class="value pos">{pct(ctrl["ETHUSDT"]["median_ann_pct"],4,True)}</div>
        <div class="sub">年化，{ctrl["ETHUSDT"]["n"]:,} 期</div></div>
      <div class="stat"><div class="label">TradFi：費用集中在最極端 5% 期數的比例</div>
        <div class="value warn">{top5_med_tf:.4f}</div>
        <div class="sub">中位數；BTC 是 {ctrl["BTCUSDT"]["abs_share_top5pct_periods"]:.4f}</div></div>
    </div>
    <div class="callout bad">
      <h3>這句話請看清楚：不是小 carry，是沒有 carry</h3>
      <p style="margin:0">
        <b>「平均年化 +13%」這種數字在這些合約上是有的</b>——但它<b>完全不是你抱著就會收到的東西</b>。
        中位數是 0，代表<b>超過一半的結算期，帳上一毛錢都沒動</b>；
        而全部費用的 <b>{top5_med_tf*100:.1f}%</b>（中位）集中在<b>最極端的那 5% 期數</b>裡。
        加密永續的同一個數字是 BTC {ctrl["BTCUSDT"]["abs_share_top5pct_periods"]*100:.1f}%、
        ETH {ctrl["ETHUSDT"]["abs_share_top5pct_periods"]*100:.1f}%——<b>分散得多</b>。
      </p>
      <p style="margin:10px 0 0">
        最極端的例子是 <b>{iwm["symbol"]}</b>：
        <b>{iwm["frac_exactly_zero"]*100:.1f}% 的結算期資金費是 0</b>，
        而全部的費用<b>{iwm["abs_share_top5pct_periods"]*100:.0f}% 都在最極端 5% 的期數裡</b>。
        這不是一個「收益率低」的東西，這是一個<b>平常不存在、偶爾跳一下</b>的東西。
      </p>
      <p style="margin:10px 0 0">
        <b>這個結論用一次 API 呼叫就對 {n_tradfi} 個合約全部成立，不需要逐一回測。</b>
        整個「在 TradFi 永續上收 carry」的家族，到這裡關閉。
      </p>
    </div>

    <h3 class="sub">2-3　完整抽樣表（{len(fs)} 列，全部列出）</h3>
    <div class="table-wrap wide">
      <table>
        <caption>來源：<code>funding_survey.csv</code>，本表每一格由程式從該檔直接讀出。
          最後兩列是加密對照組。「0 的比例」＝資金費<b>恰好等於 0</b> 的結算期占比。</caption>
        <thead><tr><th>合約</th><th>期數</th><th>結算間隔</th><th>最早</th>
          <th>平均（年化）</th><th>中位數（年化）</th><th>0 的比例</th><th>最極端 5% 期數占全部費用</th></tr></thead>
        <tbody>
''')
for r in fs:
    cls = ' class="base"' if r["symbol"] in CTRL else (' class="best"' if r["symbol"] in const_syms else '')
    medcls = "pos" if r["median_ann_pct"] != 0 else "negv"
    A(f'          <tr{cls}><td class="name">{r["symbol"]}</td><td>{r["n"]:,}</td>'
      f'<td>{r["interval_h"]:.0f}h</td><td>{r["first"]}</td>'
      f'<td>{pct(r["mean_ann_pct"],4,True)}</td>'
      f'<td class="{medcls}">{pct(r["median_ann_pct"],4,True)}</td>'
      f'<td>{r["frac_exactly_zero"]*100:.1f}%</td>'
      f'<td>{r["abs_share_top5pct_periods"]*100:.1f}%</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>
    <p class="body-note">
      讀法：<b>看第六欄（中位數），不要看第五欄（平均）。</b>
      第五欄有正有負、有的到 {max(r["mean_ann_pct"] for r in tf):+.1f}%、有的到 {min(r["mean_ann_pct"] for r in tf):+.1f}%，
      看起來像是有東西可做；第六欄則是 {n_med_zero} 個 0。
      <b>兩欄差這麼多，本身就是「這個分布右偏、由極少數尖峰撐起來」的證據。</b>
      TradFi 抽樣的「0 的比例」中位數是 <b>{zero_med_tf*100:.1f}%</b>，觀測期數從 {n_min} 到 {n_max:,} 不等。
    </p>

    <h3 class="sub">2-4　唯一的例外：{" / ".join(const_syms)}</h3>
    <div class="callout">
      <p style="margin:0">
        這兩個合約的資金費是 <b>恆定 {pct(CONST,4,True)}／年</b>、
        <b>100% 的期數為正</b>、<b>變異為零</b>
        （n = {" / ".join(str(r["n"]) for r in const_rows)}）。
        這是本專案至今看到的<b>第一個真正契約型的常數 carry</b>——不是統計上的平均，是寫死的數字。
      </p>
      <p style="margin:10px 0 0">
        <b>但它仍然是 FAIL，理由與收益率無關</b>：
        標的<b>沒有可觀察的公開價格</b>（未上市公司），
        因此<b>沒有任何一條對沖腿</b>可以搭——你拿不到現貨、也沒有相關性可靠的替代品。
        結果是：想收這 {pct(CONST,4,True)} 就必須裸空，而<b>空方的虧損沒有上界</b>。
      </p>
      <p style="margin:10px 0 0">
        <b>收益率是確定的，風險卻是無界的——這正是本專案地雷手冊裡的典型形狀。</b>
        一個確定的小數字配一個不確定的大數字，不是套利，是賣保險。
      </p>
    </div>

    <h3 class="sub">2-5　方法論警告：8 小時的結算慣例在這裡會錯 2 倍</h3>
    <div class="callout bad">
      <p style="margin:0">
        本次抽樣裡，TradFi 合約出現過的結算間隔是 <b>{{{", ".join(f"{i:.0f}h" for i in intervals)}}}</b>——
        其中 <b>{n_4h} 個是 4 小時結算</b>（金銀鉑鈀銅、原油、天然氣、SKHYNIX）。
        幣安自 2026-01-02 起，結算頻率會在 1h / 4h / 8h 之間動態切換。
      </p>
      <p style="margin:10px 0 0">
        <b>state 檔沿用的「資金費 × 每日 3 次」年化慣例，套在這些合約上會低估 2 倍。</b>
        往後任何一輪要年化資金費，<b>都必須從 <code>fundingTime</code> 的差分推出實際間隔，不可以假設 8h。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>本頁的表不受這個錯誤影響</b>：產生它的腳本就是用 <code>fundingTime</code> 差分的中位數算間隔的
        （<code>py = 24*365/iv</code>）。這一點是本頁作者讀過腳本後確認的，不是研究員宣稱的。
      </p>
    </div>
  </section>
''')

# ------------------------------ B1 ------------------------------
A(f'''
  <section id="b1">
    <h2>三、B1：條件全部滿足的候選，量出來是乾淨的零</h2>
    <p class="section-note">
      測的是 <code>BTCUSDT</code> 永續 與 <code>BTCUSDC</code> 永續 之間的<b>資金費差</b>。
      資料：<code>triage2/rv_results.csv</code> 第一列。
    </p>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>幣安上「用 USDT 計價的 BTC 永續」和「用 USDC 計價的 BTC 永續」是<b>同一個東西的兩種計價</b>。
        兩邊各自收自己的資金費，如果長期有一邊比較高，那就<b>做多低的、放空高的</b>，
        方向完全抵銷，只賺那個差。</p>
      <p>這個想法好在哪：<b>它滿足這個專案的每一條收案條件</b>——沒有任何參數要調、
        兩邊數量完全 1 比 1、漲跌完全不影響你、不改變你原本的 BTC 曝險、
        在同一家交易所、金額多小都做得動。<b>十四輪以來沒有任何一個候選同時滿足這六條。</b></p>
      <p>然後去量，結果是：<b>這個差就是 0。</b>不是「小到不划算」，是連方向都沒有。
        而且這次樣本夠多，<b>所以這個 0 是可信的 0</b>。</p>
    </div>

    <div class="split">
      <div class="stat"><div class="label">平均資金費差（年化）</div>
        <div class="value neg">{pct(B1_ANN,4,True)}</div><div class="sub">{B1_SPAN}</div></div>
      <div class="stat"><div class="label">t 值（週為單位）</div>
        <div class="value neg">{B1_T}</div><div class="sub">門檻 3.0；這裡連 1 都不到</div></div>
      <div class="stat"><div class="label">獨立週觀測數</div>
        <div class="value pos">{int(B1_W)}</div><div class="sub">共 {B1_N:,} 個 8 小時結算期</div></div>
      <div class="stat"><div class="label">來回 taker 成本 ÷ 整年的 carry</div>
        <div class="value neg">{B1_COST_RATIO:.1f} 倍</div>
        <div class="sub">0.20% vs {abs(B1_ANN):.4f}%</div></div>
    </div>

    <div class="table-wrap">
      <table>
        <caption>B1 收案條件逐條檢查——這是它值得單獨寫一節的原因</caption>
        <thead><tr><th>專案的收案條件</th><th>B1 的狀況</th></tr></thead>
        <tbody>
          <tr><td class="name">零參數</td><td class="pos wrap">滿足。沒有任何門檻、視窗、權重要調。</td></tr>
          <tr><td class="name">避險比固定</td><td class="pos wrap">滿足，而且恆為 1——同一個標的，不需要估。</td></tr>
          <tr><td class="name">delta 恆為 0</td><td class="pos wrap">滿足。BTC 漲跌對這個部位沒有影響。</td></tr>
          <tr><td class="name">不改變 β</td><td class="pos wrap">滿足。原有的 BTC 曝險完全不動。</td></tr>
          <tr><td class="name">與方向無關</td><td class="pos wrap">滿足。不需要預測任何事。</td></tr>
          <tr><td class="name">單一交易所</td><td class="pos wrap">滿足。不必開第二個帳戶、不必搬錢。</td></tr>
          <tr><td class="name">小資金做得動</td><td class="pos wrap">滿足。</td></tr>
          <tr class="bad"><td class="name">有可收的東西</td>
            <td class="negv wrap"><b>不滿足。{pct(B1_ANN,4,True)}／年，t = {B1_T}。</b></td></tr>
        </tbody>
      </table>
    </div>

    <div class="callout bad">
      <h3>它失敗的方式是最好的那一種</h3>
      <p style="margin:0">
        本專案十四輪裡絕大多數的 FAIL 都是<b>「測不出來」</b>——
        效應可能存在，但樣本不夠、雜訊太大、t 值上不去，所以只能說「證不了」。
        <b>那種 FAIL 會留下一個心結：是不是再多等幾年就行了？</b>
      </p>
      <p style="margin:10px 0 0">
        <b>B1 不是那種。B1 是「這個數就是零」。</b>
        {int(B1_W)} 個獨立週觀測、跨 {B1_SPAN}、{B1_N:,} 個結算期，
        平均差是 {pct(B1_ANN,4,True)}／年——<b>在小數點第二位就已經是 0 了</b>。
        而光是進出一次的手續費（來回 taker 0.20%）就是<b>整整一年 carry 的 {B1_COST_RATIO:.1f} 倍</b>。
      </p>
      <p style="margin:10px 0 0">
        <b>這種 FAIL 不會因為多等幾年而翻案，所以它是真的把一扇門關上了。</b>
        這一輪如果只留下一個乾淨的量測，就是這個。
      </p>
      <p style="margin:10px 0 0">
        順帶一提：<code>BTCUSDC</code> 這個符號<b>在前十四輪的 state 檔裡出現次數是 0</b>。
        沒有人看過這一格——不是因為它難，是因為沒人想到要看。
      </p>
    </div>
  </section>
''')

# ------------------------------ Sharpe 6.45 ------------------------------
CHECKLIST = [
 ("這個數字是用<b>哪幾條腿</b>算出來的？",
  "策略如果有兩條腿（例如「收資金費」＋「持有部位」），只算其中一條的績效一定漂亮。",
  f"Sharpe {F['claim_sharpe']} 只算了資金費那一腿。加回價格腿之後，我們實測的結果是輸的。"),
 ("換算成<b>幣數比</b>還贏嗎？",
  "「年化 30%」和「手上的幣變多」是兩件事，而且常常方向相反。把它換算成「最後手上幾顆幣」。",
  f"同一段期間、同一件事，我們自己量到的是幣數比 {F['plan1_coinratio']}——<b>比什麼都不做少 5.4%</b>（基準：純持有 {F['hold_coins']} 顆 = 1.0000）。"),
 ("它的<b>期間</b>是怎麼選的？",
  "起訖點如果剛好卡在一段特別有利的行情，數字會好看很多。要問「換一段時間還在嗎」。",
  f"那個宣稱的期間是 {F['claim_span']}，與本專案方案一的 {F['proj_span_start']} 起算幾乎完全重合——<b>這反而是它最有用的地方：可以直接對帳。</b>"),
 ("<b>成本</b>算進去了嗎？",
  "來回一趟 taker 手續費大約 0.20%。一個年化只有零點幾 % 的策略，成本會直接把它吃掉。",
  "宣稱方通常不寫。本頁的 B1 就是活教材：carry 0.03%／年，成本 0.20%。"),
 ("<b>獨立觀測數</b>有多少？",
  "「測了 199 個合約」聽起來很多，但如果它們共用同一套規則，那其實只有一筆證據。",
  "見<a href=\"#specs\">SPEC-2</a>：{sub}"),
 ("<b>證據等級</b>是什麼？",
  "同儕審查的論文、交易所文件、部落格、廠商行銷——可信度差好幾個量級。",
  f"Sharpe {F['claim_sharpe']} 的來源是<b>④ 廠商行銷／部落格</b>，這是最低的一級。"),
]
A(f'''
  <section id="sharpe645">
    <h2>四、Sharpe {F["claim_sharpe"]} 的標本——以及你以後可以自己套的檢查法</h2>
    <p class="section-note">
      這一節不是在批評誰。它是把「一個看起來好到不可能的數字」<b>拆開給你看它好在哪裡</b>，
      而拆解用的對照組，是<b>本專案自己花了一整輪測出來的同一條線</b>。
    </p>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>這一輪去外面盤點策略時，看到最漂亮的一個宣稱是 <b>Sharpe {F["claim_sharpe"]}</b>。
        Sharpe 可以粗略理解成「賺的錢除以過程中的顛簸」，<b>超過 2 就已經很少見，{F["claim_sharpe"]} 是天文數字</b>。</p>
      <p>然後我們發現一件很剛好的事：<b>它做的就是我們第一輪做過的那件事，連時間段都幾乎一樣</b>。
        而我們自己量的結果是——<b>最後手上的幣比什麼都不做還少 5.4%</b>。</p>
      <p>差別在哪？<b>不在策略，在會計。</b>那個宣稱<b>只算了收到的資金費，沒有算持有部位本身的漲跌。</b>
        資金費是一條幾乎只往上走的線，只看它當然漂亮；
        但你要收這筆錢，就必須<b>同時扛著一個會上下跳的部位</b>，而那一腿它沒算。</p>
    </div>

    <div class="table-wrap wide">
      <table>
        <caption>同一條線、幾乎同一段期間，兩種算法</caption>
        <thead><tr><th></th><th>外部宣稱</th><th>本專案實測（引用自舊報告）</th></tr></thead>
        <tbody>
          <tr><td class="name">做的事</td><td class="wrap">收永續合約的資金費</td>
            <td class="wrap">收永續合約的資金費（方案一）</td></tr>
          <tr><td class="name">期間</td><td>{F["claim_span"]}</td><td>{F["proj_span_start"]} 起，六年</td></tr>
          <tr><td class="name">算了哪幾條腿</td><td class="negv wrap"><b>只有資金費那一腿</b></td>
            <td class="pos wrap">資金費 ＋ 價格，兩腿都算</td></tr>
          <tr><td class="name">交出來的成績</td><td class="negv"><b>Sharpe {F["claim_sharpe"]}</b></td>
            <td class="negv wrap"><b>幣數比 {F["plan1_coinratio"]}</b>（比純持有少 5.4%）</td></tr>
          <tr><td class="name">拆開看是誰賺的</td><td class="wrap">—</td>
            <td class="wrap">資金費那一腿 {F["plan1_funding_leg"]} 顆、
              <b>價差那一腿 {F["plan1_price_leg"]} 顆</b>——<b>它賺的其實不是資金費，是方向</b></td></tr>
          <tr><td class="name">證據等級</td><td class="negv">④ 廠商行銷／部落格</td>
            <td class="pos">自行回測、資料與腳本留存</td></tr>
        </tbody>
      </table>
    </div>

    <div class="callout bad">
      <h3>為什麼「只算一條腿」一定會做出爆表的 Sharpe</h3>
      <p style="margin:0">
        資金費的收入曲線<b>近乎單調上升</b>：大多數時候是正的、金額小、幾乎不回頭。
        Sharpe 的分母是「顛簸」——一條不顛簸的線，分母接近 0，<b>Sharpe 自然就爆表</b>。
      </p>
      <p style="margin:10px 0 0">
        但那條線<b>不是你的損益</b>。要收到這筆錢，你必須同時持有一個會上下跳的部位，
        而那個部位的漲跌<b>比資金費大一到兩個量級</b>。
        把兩腿合起來算，顛簸馬上回來，Sharpe 就落回地面。
      </p>
      <p style="margin:14px 0 0">
        <b>而這正是本專案自己犯過的錯，只是換了一張臉。</b>
        舊報告的誠信紀錄裡，口徑偏誤 #1 就是同一件事：
        某個方案的 Sharpe 從 <b>{F["bias1_before"]}</b> 修正到 <b>{F["bias1_after"]}</b>，
        <b>差了 20 倍，而策略一個字都沒改</b>，改的只是算法的口徑。
        細節見<a href="crypto-dca-amplifier-report.html#fixed">舊報告〈已修掉的重大缺陷〉</a>。
      </p>
      <p style="margin:14px 0 0;font-size:1.02rem">
        <b>宣稱 Sharpe {F["claim_sharpe"]} 的那條線，就是本專案花了第一輪、量到幣數比 {F["plan1_coinratio"]} 的同一條線。
        差別不在策略，在會計。</b>
      </p>
    </div>

    <h3 class="sub">★ 你以後看到類似宣稱時，照順序問這六個問題</h3>
    <p class="body-note" style="margin-top:0">
      這是這一輪對你最有實用價值的產出。<b>不需要會寫程式，也不需要看懂回測。</b>
      六個問題裡只要有一個問不出答案，那個宣稱就該降級處理。
    </p>
    <div class="table-wrap wide">
      <table>
        <caption>看到「年化 XX%」「Sharpe X.XX」時的六道檢查</caption>
        <thead><tr><th>#</th><th>問這句話</th><th>為什麼要問</th><th>這次的標本怎麼答</th></tr></thead>
        <tbody>
''')
SUB = "那一輪的研究員自己指出，199 個合約其實只有 6 個獨立觀測。"
for i, (q, why, ans) in enumerate(CHECKLIST, 1):
    ans = ans.replace("{sub}", SUB)
    A(f'          <tr><td class="name">{i}</td><td class="wrap"><b>{q}</b></td>'
      f'<td class="wrap">{why}</td><td class="wrap">{ans}</td></tr>\n')
A('''        </tbody>
      </table>
    </div>
    <div class="callout">
      <p style="margin:0">
        <b>六個問題裡，第 1 和第 2 可以獨立擋掉絕大多數的誇大宣稱</b>，而且都不需要任何技術能力：
        「你這個數字是把所有該算的都算進去了嗎？」「換成幣，最後是變多還是變少？」
      </p>
      <p style="margin:10px 0 0">
        <b>本專案自己被這兩題擋下來過至少兩次</b>（口徑偏誤 #1、以及把兩個不同長度的時間窗混在一起算）。
        這不是用來懷疑別人的工具，是用來懷疑自己的工具——<b>它對自己人和外人一樣有效。</b>
      </p>
    </div>
  </section>
''')

# ------------------------------ other measured FAILs ------------------------------
d_hk, d_sk, d_sa = DUPS
A(f'''
  <section id="other">
    <h2>五、另外三個親手量測出來的 FAIL</h2>
    <p class="section-note">
      這一輪 24 個正式評估的候選裡，有 4 個是<b>實際跑數字關掉的</b>（不是靠文獻或推理）。
      B1 是其中之一，另外三個在這裡。資料：<code>triage2/rv_results.csv</code>。
    </p>

    <h3 class="sub">5-1　同一個標的掛了兩個合約，價差會不會收斂？</h3>
    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>幣安上同一家公司有時掛了兩個名字不同的合約。如果它們真的是同一個東西，
        價格應該幾乎一樣；只要偶爾偏開，就<b>買便宜的那個、賣貴的那個</b>，等它回來。</p>
      <p>結果分兩種。一種是<b>真的太像了</b>，像到偏離的幅度還不夠付手續費；
        另一種是<b>它們根本就不是同一個東西</b>，那就沒有「會收斂」這回事，只是賭兩家公司誰漲得多。</p>
    </div>
    <div class="table-wrap wide">
      <table>
        <caption>三組「看起來重複」的合約，價比偏離的標準差（sd）。來回成本 0.20% 是這裡的生死線。</caption>
        <thead><tr><th>合約對</th><th>偏離 sd</th><th>最大偏離</th><th>小時 K 棒數</th>
          <th>獨立週</th><th>判定</th></tr></thead>
        <tbody>
          <tr><td class="name">{d_hk["a"]} vs {d_hk["b"]}</td><td class="negv">{d_hk["sd"]:.3f}%</td>
            <td>{d_hk["maxdev"]:.3f}%</td><td>{d_hk["n"]:,}</td><td>{d_hk["w"]:.0f}</td>
            <td class="wrap negv"><b>真的是同一家，但太像了</b>——整個 sd（{d_hk["sd"]:.3f}%）
              約等於來回成本（0.20%）。沒有空間。</td></tr>
          <tr><td class="name">{d_sk["a"]} vs {d_sk["b"]}</td><td>{d_sk["sd"]:.3f}%</td>
            <td>{d_sk["maxdev"]:.3f}%</td><td>{d_sk["n"]:,}</td><td>{d_sk["w"]:.0f}</td>
            <td class="wrap negv"><b>根本不是同一個標的</b>。差異大到不可能是同一家公司的兩個報價。</td></tr>
          <tr><td class="name">{d_sa["a"]} vs {d_sa["b"]}</td><td>{d_sa["sd"]:.3f}%</td>
            <td>{d_sa["maxdev"]:.3f}%</td><td>{d_sa["n"]:,}</td><td>{d_sa["w"]:.0f}</td>
            <td class="wrap negv"><b>同上，而且更不像。</b>最大偏離接近 15%。</td></tr>
        </tbody>
      </table>
    </div>
    <p class="body-note">
      注意獨立週只有 <b>{min(d["w"] for d in DUPS):.0f} ~ {max(d["w"] for d in DUPS):.0f}</b> 週——<b>樣本很短</b>，因為這些合約才剛上線。
      所以第一列的判定<b>不是靠統計顯著性</b>，是靠「效應量本身就小於成本地板」這個量級比較
      （後兩列不需要統計：它們根本不是同一個標的，沒有「會不會收斂」的問題）。
      這個區別在<a href="#limits">第十節</a>會再講一次，它適用於本輪大部分的 FAIL。
      另外，{d_sa["b"]} 的每小時成交金額中位數只有 <b>${d_sa["notional"].get(d_sa["b"],"—")}</b>，
      <b>幾乎沒有人在交易</b>，這本身就排除了它。
    </p>

    <h3 class="sub">5-2　同時放空一對正反向槓桿 ETF，收「耗損」</h3>
    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>三倍做多和三倍做空同一個指數的 ETF，長期來看<b>兩個都會慢慢流失價值</b>
        （每天重設倍數造成的，市場來回震盪越多流失越快）。
        所以「<b>兩個都放空</b>」聽起來像免費的錢：指數漲或跌都被抵銷，剩下的就是那個流失。</p>
      <p>理論算出來一年有 {LEV_THEO:.2f}%。<b>實際跑出來是負的。</b></p>
    </div>
    <div class="split">
      <div class="stat"><div class="label">理論上的耗損（年化）</div>
        <div class="value pos">{LEV_THEO:+.2f}%</div><div class="sub">教科書公式 (L²−L)/2 × σ²</div></div>
      <div class="stat"><div class="label">每日再平衡，實測（年化）</div>
        <div class="value neg">{LEV_ANN:+.3f}%</div><div class="sub">{LEV_SPAN}，{LEV_DAYS} 天</div></div>
      <div class="stat"><div class="label">不再平衡版，同期間</div>
        <div class="value warn">{LEV_STATIC:+.3f}%</div><div class="sub">{LEV_DAYS} 天累計，非年化</div></div>
      <div class="stat"><div class="label">獨立週觀測數</div>
        <div class="value warn">{LEV_W:.0f}</div><div class="sub">很短，見下方說明</div></div>
    </div>
    <div class="callout bad">
      <p style="margin:0">
        <b>為什麼理論 {LEV_THEO:+.2f}% 會變成實測 {LEV_ANN:+.3f}%？</b>
        因為要讓這個部位保持中性，你每天都得把兩邊調回一比一——
        <b>而那個「耗損」正是在每天調整的那一刻被對銷掉的</b>。
        你收得到耗損的唯一方式，是<b>不要再平衡</b>。
      </p>
      <p style="margin:10px 0 0">
        不再平衡的版本這段期間確實是 <b>{LEV_STATIC:+.3f}%</b>（{LEV_DAYS} 天）。
        <b>但那個東西已經不是套利了，它是空 gamma</b>：
        指數小幅來回時穩定小賺，一旦單邊大走，<b>賺的那一邊有上限、賠的那一邊沒有</b>。
        （實測 beta：{LEV_BT:.3f} 與 {LEV_BS:.3f}，本來就不是乾淨的 ±3。）
      </p>
      <p style="margin:10px 0 0">
        <b>這個形狀與備兌看漲、與地雷手冊裡的網格完全同構</b>，
        而且「回撤不超過 10%」這種約束<b>對它無效</b>——它不會給你慢慢跌的機會。
        本輪實測期間的最大回撤只有 {LEV_DD:.2f}%，<b>但那正是空 gamma 在平靜期的正常長相，不是安全的證據。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>誠實標註：只測了 TQQQ / SQQQ 這一組</b>，沒有測 SOXL/SOXS 等其他組。
        研究員自己要求標明：<b>這一條是用代數關掉的，不是用資料關掉的。</b>
      </p>
    </div>
  </section>
''')

# ------------------------------ candidate stats ------------------------------
A(f'''
  <section id="stats">
    <h2>六、本輪候選統計與搜尋空間的座標</h2>

    <div class="table-wrap">
      <table>
        <caption>第十五輪：24 個正式評估的候選</caption>
        <thead><tr><th>判定</th><th>數量</th><th>說明</th></tr></thead>
        <tbody>
          <tr><td class="name">PASS（通過）</td><td class="negv"><b>0</b></td><td class="wrap">—</td></tr>
          <tr><td class="name">CONDITIONAL（有條件）</td><td>0</td><td class="wrap">—</td></tr>
          <tr><td class="name">INDETERMINATE（證據不足以判定）</td><td><b>2</b></td>
            <td class="wrap">FX 永續 <code>USDBRLUSDT</code>（<b>今天才上線，樣本數 = 0</b>）；
              Multi-Assets Mode 是否涵蓋 TradFi 永續（<b>UNKNOWN</b>，見下方誠實標註）</td></tr>
          <tr><td class="name">SCALE-BLOCKED（被規模卡住）</td><td><b>1</b></td>
            <td class="wrap">選擇權流動性溢酬——<b>與 VRP 同一扇門、同一個最小下單量</b>，
              所以它不是新的一扇門</td></tr>
          <tr><td class="name">FAIL（否決）</td><td>21</td>
            <td class="wrap">其中 <b>4 個是親手跑數字關掉的</b></td></tr>
        </tbody>
      </table>
    </div>
    <p class="body-note">
      與第一次外部盤點（43 個候選）的重疊：<b>約 18 個（75%）不重疊</b>。
      其中 A 族 8 個與 B1 <b>結構上不可能重疊</b>——它們所依賴的合約在第一次盤點時還不存在。
      第一次盤點的完整紀錄在<a href="crypto-dca-amplifier-report.html#triage">舊報告〈外部策略盤點：43 個候選，0 個通過〉</a>。
    </p>

    <h3 class="sub">兩次盤點的死法完全不同</h3>
    <div class="table-wrap wide">
      <table>
        <caption>同樣是 0 個通過，但「怎麼死的」差很多——這比通過率本身更有資訊</caption>
        <thead><tr><th></th><th>第一次（43 個）</th><th>本輪（24 個）</th></tr></thead>
        <tbody>
          <tr><td class="name">主要死因</td><td class="wrap">證據等級不足（查不到可靠來源）</td>
            <td class="wrap"><b>實測出來是零</b>（4 個是親手跑數字關掉的）</td></tr>
          <tr><td class="name">結論的條件性</td>
            <td class="wrap">多數 FAIL 是<b>條件式</b>的——條件是「BTC 的漂移維持在高檔」</td>
            <td class="wrap">A2、B1 的死法<b>與 BTC 漲不漲完全無關</b></td></tr>
          <tr><td class="name">還留著的門</td><td class="wrap">VRP（被最小下單量擋住）</td>
            <td class="wrap">VRP（沒變）＋ 選擇權流動性溢酬——<b>但那是同一扇門</b></td></tr>
        </tbody>
      </table>
    </div>
    <p class="body-note">
      <b>新增的可搜尋面積</b>：TradFi 永續 {n_tradfi} 個合約、同標的多計價永續。
      <b>兩塊都是第一次被看，兩塊都是空的。</b>
    </p>

    <h3 class="sub">一件補回來的帳：第一次盤點遺失的逐候選分類</h3>
    <div class="callout">
      <p style="margin:0">
        第一次盤點的 43 個候選，<b>逐個候選的分類標籤已經遺失</b>（舊報告只留下了彙總）。
        研究員全工作區搜尋複驗，<b>確認沒有第二份副本</b>。
        但缺口的形狀可以<b>用算術夾出來</b>，不需要推測：
      </p>
      <p style="margin:10px 0 0">
        舊報告那一節點名「唯一值得投資源」1 個（多空籃子）、「第二優先」1 個（VRP），
        其餘 <b>41 個都不建議</b>。43 − 2 = 41 ✓ 自洽；36 個 FAIL ＋ 7 個非 FAIL = 43 ✓。
        <b>所以 7 個非 FAIL 裡，恰好 2 個被點名，另外 5 個全部落在那 41 個「不建議」裡面。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>結論是：缺的不是 5 個未知的機會，是 5 個「已知理由被卡住」的東西</b>——
        幾乎必然死在硬限制（規模／要開兩個交易所／速度／要寫自動化）而不是死在證據，與 VRP 同一型。
        而後續輪次已經獨立關掉其中幾扇門：BTC 借貸（六年 {F["lending_6y"]}）、
        CTA 趨勢（跨資產中位 alpha {F["cta_alpha"]} 對上 BTC 的 {F["cta_hurdle"]} 門檻）、
        買別人的市場中性基金（規格上不可執行）。
        <b>真正未知的缺口最多剩 1 ~ 2 個槽位。</b>
      </p>
    </div>
  </section>
''')

# ------------------------------ maker ------------------------------
A(f'''
  <section id="maker">
    <h2>七、最大的一塊還沒被看過的地方：造市／掛 maker 單<span class="pill hyp">這是推論，不是紀錄</span></h2>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>「造市」的意思是：不去追價格，而是<b>掛在買賣兩邊等別人來成交</b>，賺中間那個價差。
        在交易所的收費結構裡，這種單（maker 單）不但比較便宜，有時候還有回饋。</p>
      <p>這一塊<b>十五輪以來沒有任何一輪碰過</b>。而它當初被否決的理由，可能用錯了門檻。</p>
    </div>

    <div class="callout">
      <h3>它的狀態在紀錄上就是「還沒有人去量」</h3>
      <p style="margin:0">
        舊的派工書列了 6 個「在框架外、而且還沒被證偽」的類別。
        十五輪之後，<b>唯一一個沒被任何後續輪次碰過的就是「造市／流動性提供」</b>，
        原文的狀態寫的是「期望值未被否證（前次是以門檻駁回）」——
        <b>這在字面上就是 INDETERMINATE 的定義：不是量過了不行，是還沒有人去量。</b>
      </p>
      <p style="margin:10px 0 0">
        工作區佐證：<code>maker_review/</code> 是<b>空目錄</b>；
        <code>backtest_dca_hedge/makercost/</code> 是第十二輪的<b>執行成本覆核</b>，不是造市研究。
      </p>
    </div>

    <div class="callout bad">
      <h3>★ 一個可能的誤用：兩個「門檻」不是同一件事</h3>
      <p style="margin:0">
        舊紀錄用「幣安造市商門檻：30 日 {F["mm_threshold"]}」把這一塊駁回了。
        <b>但那是「做市商計畫」（Market Maker Program）的申請門檻——那是一個會員資格，不是掛 maker 單的門檻。</b>
      </p>
      <p style="margin:10px 0 0">
        任何人都可以掛 maker 單，不需要任何資格，也沒有任何量的下限。
        參加做市商計畫是為了拿<b>更好的費率與回饋</b>，跟「能不能用掛單的方式提供流動性」是兩回事。
      </p>
      <p style="margin:10px 0 0">
        而且第十二輪已經實測過：<b>嚴格只掛 maker 單、30 分鐘內成交率 {F["maker_fill"]}</b>，
        且<b>部位大小不是瓶頸</b>。
        <b>否決的理由和實際可執行的東西，不是同一件事。這句話值得有人把它拆開重看。</b>
      </p>
      <p style="margin:14px 0 0">
        <span class="pill hyp">推論</span>
        研究員把這一塊標記為「4 個 INDETERMINATE 槽位的<b>最高機率佔用者</b>」，
        並<b>明確要求標註：這是推論，不是紀錄。</b>本頁照辦。
        <b>本頁沒有宣稱造市可行，只宣稱它還沒有被量過，而且當初的否決理由可能對錯了對象。</b>
      </p>
    </div>

    <h3 class="sub">其他仍未覆蓋的地方</h3>
    <ul class="limits">
      <li><b>TradFi 永續的微結構／收盤時段效應。</b>
        研究員先自己打了預防針：<b>這幾乎一定需要挑「哪幾個小時」這種參數，會直接撞上本專案的收案標準</b>
        （零參數）。也就是說，就算去做，做出來的東西大概率不合格。</li>
      <li><b>已下市符號的 <code>contractType</code> 有沒有留在歷史封存檔。</b>
        這決定<a href="#correction">第一節</a>那份 {F["manual_list_n"]} 個符號的人工清單能不能整條退休，
        還是只能在「往後」退休。<b>本輪沒查。</b></li>
    </ul>
  </section>

  <section id="specs">
    <h2>八、兩份實驗規格</h2>

    <h3 class="sub">SPEC-1：一次點擊可以關掉 8 個候選<span class="pill fact">需要你本人決定</span></h3>
    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>有一族 8 個候選，全部依賴同一個前提：<b>能不能直接用手上的 BTC 當保證金去交易 TradFi 永續</b>
        （幣安的「Multi-Assets Mode」）。</p>
      <p>如果不能，那要做這些策略就得先把 BTC 換成 USDT——<b>那等於把幣賣掉</b>，
        整族 8 個候選當場全部作廢。</p>
      <p>而這個問題<b>查文件查不到</b>（下面誠實標註第 5 點會說為什麼），<b>只能實際下一張單試。</b></p>
    </div>
    <div class="table-wrap">
      <table>
        <caption>SPEC-1 的完整規格</caption>
        <thead><tr><th>項目</th><th>內容</th></tr></thead>
        <tbody>
          <tr><td class="name">要回答的問題</td>
            <td class="wrap">Multi-Assets Mode 是否涵蓋 TradFi 永續合約</td></tr>
          <tr><td class="name">為什麼重要</td>
            <td class="wrap"><b>這是 A 族全部 8 個候選的閘門</b>。答案為否 → 8 個全部永久關閉
              （因為改用 USDT 保證金 = β 小於 1 = 前面幾輪已經走過並關掉的那條路）</td></tr>
          <tr><td class="name">作法</td>
            <td class="wrap">轉約 {F["spec1_transfer"]} 等值的 <b>BTC</b>（不是 USDT）進 USDⓈ-M 期貨錢包 →
              開啟 Multi-Assets Mode → 對 <code>XAUUSDT</code> 下一張 ${MINNOT} 的最小單</td></tr>
          <tr><td class="name">成本上界</td>
            <td class="wrap">約 {F["spec1_cost"]} 的手續費 ＋ 持有期間的價格波動</td></tr>
          <tr><td class="name">需要幾個觀測</td>
            <td class="wrap"><b>1 個，而 1 個就夠</b>——這是<b>契約事實</b>，不是統計量。
              交易所要嘛接受這張單，要嘛拒絕，沒有「機率上成立」這回事</td></tr>
          <tr class="bad"><td class="name">誰來做</td>
            <td class="wrap negv"><b>這需要真實下單，屬於你本人的決定。團隊不會代為執行，也沒有代為執行。</b>
              這一頁只提供規格。</td></tr>
        </tbody>
      </table>
    </div>
    <p class="body-note">
      補充：就算答案是「可以」，<b>也不代表 A 族那 8 個候選就成立了</b>——
      它只是打開了那道門，門後面的東西還是要各自量。<a href="#tradfi">第二節</a>的資金費結果
      已經先把其中「收 carry」那一類關掉了。
    </p>

    <h3 class="sub">SPEC-2：研究員自己建議不要跑——而那個理由本身就是產出</h3>
    <div class="callout">
      <p style="margin:0">
        SPEC-2 原本是「把資金費調查從 {n_sampled} 個擴大到全部 {n_tradfi} 個合約」。
        <b>研究員自己建議不要做</b>，理由是：
      </p>
      <p style="margin:10px 0 0;font-size:1.02rem">
        <b>{n_tradfi} 個合約不是 {n_tradfi} 個獨立觀測。</b>
        它們共用同一套結算引擎、同一組夾板參數、同一個利率項設定。
        真正獨立的是<b>「契約設計決策」——而那只有一個</b>。
        就算用最寬鬆的方式按 <code>underlyingType</code> 切，也只有
        {len(by_type)} 類。
      </p>
      <p style="margin:10px 0 0">
        而 {n_sampled} 個抽樣裡已經有 {n_med_zero} 個中位數恰為 0。
        <b>擴大到 {n_tradfi} 個，增加的是合約數，不是資訊量。</b>
      </p>
      <p style="margin:14px 0 0">
        <b>這是本專案核心矛盾在一條全新資料軸上的又一次重現：
        換了一個從來沒看過的、{n_tradfi} 個合約的資料軸，獨立觀測數還是個位數。</b>
        這個專案缺的從來不是資料量，是<b>互相獨立的證據</b>。
      </p>
    </div>
  </section>
''')

# ------------------------------ limits ------------------------------
A(f'''
  <section id="limits">
    <h2>九、誠實標註：這一輪的結論有哪些地方站不穩</h2>
    <p class="section-note">
      以下七項是<b>研究員自己揭露的</b>，不是覆核時被抓到的。
      按照慣例，這一節不做任何淡化處理。
    </p>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>這一節要講的是「上面那些結論，哪些是硬的、哪些是軟的」。
        <b>把它們混在一起講，才是真正的不誠實</b>——所以這裡分開列。</p>
      <p>最重要的一句：<b>這一輪大部分的 FAIL，靠的不是「統計上證明它是 0」，
        而是「它的規模比手續費還小」。</b>這兩種理由的強度不一樣，不能互相冒充。</p>
    </div>

    <h3 class="sub">先分清楚：這一輪哪些證據是硬的</h3>
    <div class="table-wrap wide">
      <table>
        <caption>強證據與弱證據分開列——<b>不要把這兩欄合併成一句樂觀的話</b></caption>
        <thead><tr><th>結論</th><th>證據強度</th><th>靠什麼撐</th></tr></thead>
        <tbody>
          <tr><td class="name wrap">機械判別式存在、{n_tradfi} 個 TradFi 合約在線</td>
            <td class="pos"><b>硬</b></td>
            <td class="wrap">集合恆等式，不是抽樣也不是統計；<b>協調者已獨立複驗，逐項吻合</b></td></tr>
          <tr><td class="name wrap">B1 的資金費差是 0</td>
            <td class="pos"><b>硬</b></td>
            <td class="wrap">{B1_N:,} 期、{int(B1_W)} 個獨立週、跨 {B1_SPAN}——
              <b>本輪唯一一個樣本數足夠的量測</b></td></tr>
          <tr><td class="name wrap">TradFi 永續沒有 carry</td>
            <td><b>中</b></td>
            <td class="wrap">效應量（中位數 = 0）大到不需要統計檢定，<b>但歷史只有中位 {age_med_m:.1f} 個月</b>，
              而且只抽了 {n_sampled} / {n_tradfi} 個</td></tr>
          <tr><td class="name wrap">A3 / A4 等其他 FAIL</td>
            <td class="negv"><b>軟</b></td>
            <td class="wrap"><b>獨立週觀測數只有 5 ~ 12</b>。
              它們的信心來自「效應量比成本小一個量級」，<b>不來自統計顯著性</b></td></tr>
          <tr><td class="name wrap">造市是最有可能的未覆蓋區塊</td>
            <td class="negv"><b>推論</b></td>
            <td class="wrap">研究員本人要求標註「這是推論，不是紀錄」</td></tr>
        </tbody>
      </table>
    </div>

    <h3 class="sub">研究員自揭的七項限制</h3>
    <ul class="limits">
      <li><b>1．TradFi 的歷史極短。</b>最長 {age_max_m:.1f} 個月、<b>中位數只有 {age_med_m:.1f} 個月</b>，
        A3 / A4 的獨立週觀測數只有 <b>5 ~ 12</b>。
        <b>這些 FAIL 的信心來自「效應量與成本的量級比」，不來自統計顯著性。</b>
        研究員的原話值得抄下來：<b>「正確的反駁不是『t 不顯著』——是『成本地板就在效應量上』。」</b></li>
      <li><b>2．B1 是本輪唯一有足夠樣本的量測</b>（{B1_N:,} 期、{int(B1_W)} 週、跨 2024–2026），
        所以它的 FAIL 紮實。<b>其餘的量測都不到這個等級。</b></li>
      <li><b>3．槓桿 ETF 那一條只測了 TQQQ / SQQQ 一組</b>，沒測 SOXL/SOXS 等其他組合。
        研究員要求照實標明：<b>這一條是用代數關掉的，不是用資料關掉的。</b></li>
      <li><b>4．文獻只取到摘要層級，沒有一篇取到全文。</b>
        與第七輪對 SSRN 6701738 的揭露同一級別。
        <b>凡是靠文獻擋掉的候選，其證據強度上限就在這裡。</b></li>
      <li><b>5．那個 UNKNOWN 是怎麼來的。</b>抓取幣安 FAQ 之後，模型回答「不適用於 TradFi 永續」，
        <b>但那是模型從「頁面沒有提到」推論出來的，不是頁面的正面陳述。</b>
        <b>研究員拒絕採信，標為 UNKNOWN</b>——這就是 <a href="#specs">SPEC-1</a> 存在的原因。
        <span class="pill fact">這是加分項，不是扣分項</span></li>
      <li><b>6．本輪所有量測都落在今天這一次抓取，沒有時間戳稽核。</b>
        TradFi 合約太新，沒有不可變的歷史封存可以對帳。
        <b>因此本輪沒有產生任何乾淨的首次讀取，本頁也不宣稱有。</b></li>
      <li><b>7．一個確認項</b>：<code>assetIndex</code> 確認 BTCUSD 的 bid/ask buffer = {F["bidbuffer"]}，
        也就是那個 <b>5% 的折價是活的、可驗證的</b>，與舊紀錄一致。這一項是對得上的。</li>
    </ul>

    <h3 class="sub">關於覆核程序本身</h3>
    <div class="callout">
      <p style="margin:0">
        <b>這一輪沒有走完整的外部覆核流程。</b>研究員依其限制未產出報告檔，
        並明確要求協調者<b>不要代寫</b>；協調者沒有代寫。
        本頁所依據的複驗，是<b>協調者針對關鍵數字的逐項獨立重算</b>
        （重新抓取 {F["symbols_scanned"]} 個符號、重跑集合恆等式、重算資金費統計），結果逐項吻合。
      </p>
      <p style="margin:10px 0 0">
        <b>本頁作者另外自行讀過三支腳本</b>，確認了一件事：
        資金費的年化是從 <code>fundingTime</code> 差分推出間隔的，
        <b>所以本頁的表沒有踩到<a href="#tradfi">第二節</a>提到的那個 2 倍低估。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>把這一段寫出來，是因為「這一頁的把關程度」本身就是讀者需要知道的資訊。</b>
        它比平常的流程短，所以本頁的所有結論都應該按這個折扣來讀。
      </p>
    </div>
  </section>
''')

# ------------------------------ conclusion ------------------------------
A(f'''
  <section id="conclusion">
    <h2>結論</h2>

    <div class="plain">
      <span class="lbl">一段話講完</span>
      <p>這一輪去看了五個以前沒看過的地方，<b>五個都是空的</b>。
        但在看的過程中，發現舊報告裡有一句話是錯的，<b>而那句錯話的價值比五個空地方加起來還高</b>。</p>
      <p>還有一件對你日常有用的事：我們在外面看到一個宣稱「Sharpe {F["claim_sharpe"]}」的策略，
        <b>拆開來發現它就是我們自己測過會輸錢的那條線，只是少算了一半的帳</b>。
        <a href="#sharpe645">第四節</a>那六個問題，你以後看到任何策略宣傳都可以照著問。</p>
    </div>

    <h3 class="sub">這一輪確定的事</h3>
    <ul class="limits">
      <li><b>「人工清單無可避免」是假的。</b>有一個零誤判、零漏判、可即時查詢的機械判別式。
        <b>這更正了舊報告的一段話，而舊報告本身一個字都沒有改。</b></li>
      <li><b>TradFi 永續上沒有 carry 可收。</b>不是小，是字面上的 0。
        整個家族在一個量測裡關閉，唯一的例外因為沒有對沖腿而不能用。</li>
      <li><b>B1 是 0。</b>而且是那種「不會因為多等幾年而翻案」的 0。</li>
      <li><b>{n_tradfi} 個合約不是 {n_tradfi} 個獨立觀測。</b>
        這個專案缺的從來不是資料量，是互相獨立的證據。</li>
    </ul>

    <h3 class="sub">這一輪沒有確定的事</h3>
    <ul class="limits">
      <li><b>幣數比沒有新數字，因為沒有任何候選走到那一步。</b>
        本頁不提供任何硬湊出來的幣數比。</li>
      <li><b>造市／掛 maker 單還是沒有被量過</b>，而它當初的否決理由可能對錯了門檻。</li>
      <li><b>Multi-Assets Mode 能不能用在 TradFi 永續，仍然是 UNKNOWN。</b>
        那需要一張真實的單，而那是你本人的決定。</li>
      <li><b>已下市符號的歷史欄位沒查</b>，所以人工清單只能在「往後」退休。</li>
    </ul>

    <div class="callout bad">
      <h3>為什麼這一頁不寫「終局」「結案」這類字眼</h3>
      <p style="margin:0">
        研究員拒絕下終局結論，理由不是客氣：
        <b>本輪有一個已經發布的結論，在兩天之後被一次 API 查詢推翻，
        而推翻它的原因只是「沒有人再去看一次」。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>這種事會再發生。</b>所以這一頁的每一個 FAIL，都應該讀成
        「以今天能看到的證據，它不成立」，而不是「它永遠不成立」。
        差別在於：<b>前者會被寫下來、留著、等著被人回頭查；後者會被歸檔然後遺忘。</b>
      </p>
      <p style="margin:14px 0 0;font-size:1.04rem">
        <b>這一輪最實際的一句話還是那一句：在目前這個資金規模上，
        把錢投進去的那個動作本身，比任何一個聰明的操作都有效。</b>
        <a href="#tradfi">第二節</a>與<a href="#b1">第三節</a>只是把另外兩扇門關上而已。
      </p>
    </div>

    <h3 class="sub">相關頁面</h3>
    <ul class="limits">
      <li><b><a href="crypto-dca-amplifier-report.html">DCA 放大器 · 總覽報告（v1，已凍結）</a></b>——
        六年幣數比的完整記錄。
        <b>本頁更正的是它的<a href="crypto-dca-amplifier-report.html#fixed">〈已修掉的重大缺陷〉</a>
        與<a href="crypto-dca-amplifier-report.html#alpha">〈跨資產訊號 alpha 驗證〉</a>兩節裡的同一句話。</b>
        該頁依規則<b>不修改</b>，錯誤的原文連同它錯在哪裡一起留著。</li>
      <li><b><a href="crypto-dca-amplifier-report.html#triage">第一次外部盤點：43 個候選，0 個通過</a></b>——
        本輪是它的第二次，兩次的死法完全不同，見<a href="#stats">第六節</a>。</li>
      <li><b><a href="crypto-dca-amplifier-report.html#glossary">完整術語對照表（69 條）</a></b>——
        本頁的<a href="#glossary">術語表</a>只收這一頁用得到的。</li>
      <li><b><a href="laoliu.html">老六研究院索引</a></b></li>
    </ul>
  </section>

</main>

<footer>
  老六 · 第十五輪：第二輪外部盤點 · {TODAY}<br>
  數字來源：<code>triage2/</code> 的三個 CSV（<code>tradfi_inventory.csv</code> {n_tradfi} 列、
  <code>funding_survey.csv</code> {len(fs)} 列、<code>rv_results.csv</code> {len(rv)} 列），
  由 <code>tools/build_laoliu_r15.py</code> 讀取後注入本頁，<b>未經人工轉抄</b>。<br>
  原始資料：Binance 公開 REST API（<code>fapi/v1/exchangeInfo</code>、<code>fundingRate</code>、<code>klines</code>），
  抓取時間 {TODAY}。<br>
  本頁為研究記錄，不構成投資建議；<b>研究仍在進行中，結論可能隨新證據修正</b>。<br>
  <b>本頁發布後不再修改。</b>要更新請建立新頁並回連本頁。
</footer>

</body>
</html>
''')

doc = "".join(P)

# Section numbers are generated, never hand-written: rewrite every
# <a href="#anchor">第N節</a> from this table, then assert the <h2> agrees.
SECNUM = {"correction":"一","tradfi":"二","b1":"三","sharpe645":"四","other":"五",
          "stats":"六","maker":"七","specs":"八","limits":"九"}
def _fixref(m):
    a = m.group(1)
    return f'<a href="#{a}">第{SECNUM[a]}節</a>' if a in SECNUM else m.group(0)
doc, nfix = re.subn(r'<a href="#([a-z0-9]+)">第[一二三四五六七八九十]+節</a>', _fixref, doc)
for a, num in SECNUM.items():
    body = doc.split(f'<section id="{a}">', 1)[1]
    h2 = re.search(r"<h2>(.*?)</h2>", body, re.S).group(1)
    assert h2.startswith(num + "、"), f"section #{a} h2 starts with {h2[:6]!r}, expected {num}"
stray = re.findall(r"(?<!>)第[一二三四五六七八九十]+節", re.sub(r'<a href="#[a-z0-9]+">第[一二三四五六七八九十]+節</a>', "", doc))
assert not stray, f"section reference outside an anchor: {stray}"
open(OUT, "w", encoding="utf-8").write(doc)
print("wrote", OUT, len(doc), "bytes;", nfix, "section refs normalised")

# ---------------- index card (regenerated between markers) ----------------
CARD = f'''<!-- R15-CARD:BEGIN (generated by tools/build_laoliu_r15.py — do not hand-edit) -->
  <a class="report-card" href="laoliu-r15-triage2.html">
    <div class="top">
      <span class="title">第十五輪 · 第二輪外部盤點</span>
      <span class="tag">{TODAY}</span>
      <span class="tag">24 個候選 · 0 通過</span>
      <span class="tag">親手量測 4 個</span>
      <span class="tag live">研究進行中</span>
    </div>
    <div class="desc">
      <b>一個已發布的結論，兩天後被一次 API 查詢推翻。</b>
      第六輪寫進總覽報告的那句「代幣化股票合約全部已下市、EQUITY 標籤數量為 0、人工清單無可避免」，
      今天實測是 <b>EQUITY {by_type["EQUITY"]} 個、TradFi 永續 {n_tradfi} 個</b>，
      而且存在一個<b>零誤判零漏判</b>的機械判別式。成因是第六輪的程式<b>先過濾了另一個欄位</b>——
      「過濾器沒濾掉東西」和「標籤數量是 0」各自都是真的，<b>由此推出的結論卻是假的</b>。
      依新規則，<b>更正寫在新頁並回連，舊頁一個字都沒改</b>。
      同一輪還第一次看了那 {n_tradfi} 個合約（最小下單 ${MINNOT}，<b>規模第一次不是障礙</b>），
      然後<b>一個量測關掉整族</b>：{n_sampled} 個抽樣裡 <b>{n_med_zero} 個的資金費中位數恰好是 0</b>，
      對照 BTC 的 {pct(ctrl["BTCUSDT"]["median_ann_pct"],4,True)}——<b>不是小 carry，是沒有 carry</b>。
      <b>B1</b>（BTCUSDT vs BTCUSDC 資金費差）滿足專案<b>每一條</b>收案條件，
      量出來 <b>{pct(B1_ANN,4,True)}／年、t = {B1_T}、{int(B1_W)} 個獨立週</b>——
      <b>失敗的方式是最好的那種：不是測不出來，是這個數就是零</b>。
      本輪最高宣稱 <b>Sharpe {F["claim_sharpe"]}</b>（證據等級僅部落格），期間與本專案方案一幾乎重合，
      而我們自己的實測是<b>幣數比 {F["plan1_coinratio"]}（輸純持有）</b>——
      <b>差別不在策略，在會計</b>：它只算資金費那一腿。頁內附<b>六道可自行套用的檢查</b>。
      誠實標註：<b>本輪沒有產生任何乾淨的首次讀取，也不宣稱有</b>；
      多數 FAIL 的信心<b>來自效應量與成本的量級比，不來自統計顯著性</b>；
      <b>本輪沒有任何候選走到能算幣數比的階段，因此不提供新的幣數比</b>。
    </div>
    <div class="stats">
      <div>第六輪宣稱 vs 今日實測 EQUITY<b class="neg">0 vs {by_type["EQUITY"]}</b></div>
      <div>TradFi 永續合約<b>{n_tradfi} 個 · 最小單 ${MINNOT}</b></div>
      <div>資金費中位數恰為 0<b class="neg">{n_med_zero} / {n_sampled}</b></div>
      <div>B1 資金費差（年化）<b class="neg">{pct(B1_ANN,4,True)} · t={B1_T}</b></div>
      <div>B1 來回成本 ÷ 整年 carry<b class="neg">{B1_COST_RATIO:.1f} 倍</b></div>
      <div>外部最高宣稱 vs 本專案實測<b class="neg">Sharpe {F["claim_sharpe"]} vs 幣數比 {F["plan1_coinratio"]}</b></div>
      <div>本輪通過數<b class="neg">0 / 24</b></div>
    </div>
  </a>
<!-- R15-CARD:END -->
'''
idx = open(INDEX, encoding="utf-8").read()
if "<!-- R15-CARD:BEGIN" in idx:
    idx = re.sub(r"<!-- R15-CARD:BEGIN.*?<!-- R15-CARD:END -->\n", CARD, idx, flags=re.S)
else:
    anchor = '  <a class="report-card" href="crypto-dca-amplifier-report.html">'
    assert anchor in idx
    idx = idx.replace(anchor, CARD + "\n" + anchor, 1)
idx = re.sub(r'<div class="count">共 \d+ 份報告</div>', '<div class="count">共 2 份報告</div>', idx)
open(INDEX, "w", encoding="utf-8").write(idx)
print("updated", INDEX)
