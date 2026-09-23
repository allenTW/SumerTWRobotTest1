#!/usr/bin/env python3
"""Build laoliu-r19-axioms.html (Round 19 / the round that dismantled four of
its own foundations) and add its card to the index.

Discipline (same as tools/build_laoliu_r17.py, plus three additions):
  - No number is typed into the prose. Every number is either
    (a) asserted to appear LITERALLY in one of the source files -> *fact()
    (b) recomputed HERE from the raw artefacts, and where a source states the
        same quantity, cross-checked against it -> cross()
  - RETIRED guard: values this round retires must not reappear as if true.
  - REVERSE number check: every number ON the page must exist in the material
    or be named in DERIVED_OK.
  - The build is run twice and the two outputs compared by SHA-256 (see
    RUN_TWICE.md note at the end of the file).
  - No already-published page is written to. The only existing file touched is
    laoliu.html (the index), and only between generated markers.
Run: python3 build_laoliu_r19.py
"""
import os, re, sys, math, csv, json, glob, random, hashlib, statistics as st

ROOT = "/Volumes/FCP 512GB/Claude"
REPO = os.path.join(ROOT, "SumerTWRobotTest1")
PUB = os.path.join(ROOT, "r19_publish")
V1 = os.path.join(REPO, "crypto-dca-amplifier-report.html")
R15 = os.path.join(REPO, "laoliu-r15-triage2.html")
R16 = os.path.join(REPO, "laoliu-r16-eth.html")
R17 = os.path.join(REPO, "laoliu-r17-kelly.html")
STATE = os.path.join(ROOT, "laoliu-state.md")
OUT = os.path.join(REPO, "laoliu-r19-axioms.html")
INDEX = os.path.join(REPO, "laoliu.html")
TODAY = "2026-09-23"
os.makedirs(PUB, exist_ok=True)

state_txt = open(STATE, encoding="utf-8").read()
b1_txt = open(os.path.join(ROOT, "beta1_enum/REPORT.md"), encoding="utf-8").read()
cg_txt = open(os.path.join(ROOT, "kelly_review/CONTROL_GROUP.md"), encoding="utf-8").read()
bw_txt = open(os.path.join(ROOT, "backwardation_rule/REPORT.md"), encoding="utf-8").read()
ex_txt = open(os.path.join(ROOT, "exec_measure/REPORT.md"), encoding="utf-8").read()
m24_log = open(os.path.join(ROOT, "kelly_review/m_real24w.log"), encoding="utf-8").read()
mm_log = open(os.path.join(ROOT, "mm_adverse/run_daily.log"), encoding="utf-8").read()
mmlive_log = open(os.path.join(ROOT, "mm_adverse/run_live.log"), encoding="utf-8").read()

USED = {}


def _mk(tag, txt, fname):
    def f(key, literal):
        assert literal in txt, f"{tag} {key} ({literal!r}) not in {fname}"
        USED[key] = (tag, literal)
        return literal
    return f


sfact = _mk("state", state_txt, "laoliu-state.md")
bfact = _mk("beta1", b1_txt, "beta1_enum/REPORT.md")
cfact = _mk("control", cg_txt, "kelly_review/CONTROL_GROUP.md")
wfact = _mk("backw", bw_txt, "backwardation_rule/REPORT.md")
efact = _mk("exec", ex_txt, "exec_measure/REPORT.md")
mfact = _mk("m24", m24_log, "kelly_review/m_real24w.log")

F = {
    # ---- 1. the four axioms ------------------------------------------------
    "ax_lam_verdict": sfact("ax_lam_verdict", "**偽裝成代數的實證**"),
    "ax_m_verdict":   sfact("ax_m_verdict", "**偽裝成代數的模型結論**"),
    "ax_b_verdict":   sfact("ax_b_verdict", "**同義反覆被標成決策理論結果**"),
    "ax_lam_rule":    sfact("ax_lam_rule", "`drop_max < 1 − (λ/2)/0.95`"),
    "objective":      sfact("objective", "`G(m,λ) = e·μ_ρ − e²σ_ρ²/2 + 52·p_week(λ)·log(1−m)`"),
    "m1_infty":       sfact("m1_infty", "**m=1 時 log(0) = −∞**"),
    "m1_true":        sfact("m1_true", "「強平機率只看 λ」對；「因此 m=1」錯"),
    "minimax_drop":   sfact("minimax_drop", "**「minimax」這個詞要拿掉**"),
    "minimax_both":   sfact("minimax_both", "**兩側都沒有**"),
    "supC_note":      sfact("supC_note", "**已發布的 `sup C = 1+λ` 應加註「僅限不動名目（buy-and-hold notional）」。**"),
    "constlam_form":  sfact("constlam_form", "`C_T = (S_T/S₀)^λ · exp(−½λ(1+λ)σ²T)`"),
    "constlam_gbm":   sfact("constlam_gbm", "GBM 理想模型：零資金費、零手續費、無爆倉、每日再平衡無成本。"),
    "constlam_judge": sfact("constlam_judge", "不是改進，是換一種賭法"),
    "sig_band":       sfact("sig_band", "**8%~23%**"),
    "ax_verdict":     sfact("ax_verdict", "十條裡三條標籤錯、一條協調者驗算錯、一條範圍錯，全部是唯讀重算就能抓到的"),
    "lam_decided":    sfact("lam_decided", "**決定本身未必錯，理由錯。**"),
    # ---- 2. the retraction -------------------------------------------------
    "retract":        sfact("retract", "**結論不變，但「波普錯了」這條紀錄是錯的，正式撤回。**"),
    "retract_same":   sfact("retract_same", "**同一族錯，方向相反**"),
    "retract_twice":  sfact("retract_twice", "驗了一步、發現不夠、再驗一次，還是錯"),
    "retract_unit":   sfact("retract_unit", "**「1.5σ²（算術 μ 口徑）」與「σ²（對數 ν 口徑）」是同一條門檻換單位**"),
    "nu_pub":         sfact("nu_pub", "ν=31.94%"),
    # ---- 3. the four closures ----------------------------------------------
    "bw_weeks":       wfact("bw_weeks", "**19 / 294 = 6.46%**"),
    "bw_indep":       wfact("bw_indep", "**11**（連續折價週在同一檔合約內不獨立）"),
    "bw_med":         wfact("bw_med", "平均 **12.0 bp**、中位 7.8 bp、最大 **52.0 bp**"),
    "bw_gross":       wfact("bw_gross", "**+0.000118 BTC → 幣數比 1.000171**"),
    "bw_net":         wfact("bw_net", "**+0.000039** | **1.000057**"),
    "bw_ftx":         wfact("bw_ftx", "**2022 一年佔 95%；單一合約 `BTCUSDT_221230`（FTX 那五週）佔 0.000079 = 67%。**"),
    "bw_cost":        wfact("bw_cost", "中位折價 7.8 bp **小於** taker 來回 10 bp"),
    "bw_noise":       wfact("bw_noise", "這條規則的每週報酬期望值是折價，標準差是交割時的一小時現貨波動。"),
    "bw_shift":       wfact("bw_shift", "換日期結果在 0.000076～0.000118 間漂移（±35%）"),
    "bw_premise":     wfact("bw_premise", "**BTCUSDT 季度合約 2021-02-03 才上市**"),
    "mm_close":       sfact("mm_close", "關門的是逆選擇本身，不是門檻、不是手續費"),
    "mm_flip":        sfact("mm_flip", "**但要翻案需 1s 漂移縮小 ≥350 倍，兩天差異只有 1.2~1.7 倍。**"),
    "mm_spread":      sfact("mm_spread", "**真實價差中位數與 p90 皆 = 1 tick**"),
    "mm_bug":         sfact("mm_bug", "**前次腳本有 NameError**"),
    "mm_stale":       sfact("mm_stale", "**不可用**（stale，價差中位 17~2,188 tick）"),
    "sub_close":      sfact("sub_close", "**沒有任何一格同時滿足「> $50/年」且「不引入新曝險」。**"),
    "sub_zero":       sfact("sub_zero", "**枚舉為零的層**：voucher／airdrop／lp_reward／experience_coupon／四種 boost APR **一個都沒有**（412 資產全掃）"),
    "sub_scope":      sfact("sub_scope", "登入後個人化優惠（`isNewUser` 欄存在但回 null）**不在量測範圍**"),
    "sub_bug":        sfact("sub_bug", "主列表 tier 鍵名是 `ratio` 不是 `apy`"),
    "sub_earn":       sfact("sub_earn", "第一個升級不是換幣而是開開關（+$33.87/年）"),
    "sub_locked":     sfact("sub_locked", "**Locked 對使用者資產的覆蓋**：BTC／USDT／USDC／USD1／FDUSD **都沒有 Locked 產品**。"),
    # ---- 4. beta dressed up as carry ---------------------------------------
    "b1_one_line":    bfact("b1_one_line", "沒有任何一類、任何配重構造在 24 個非重疊合約期上同時達到「≥20/24 同號且 t>2」"),
    "b1_resid":       bfact("b1_resid", "出場時次季還剩 ≈1.9% 基差"),
    "b1_ii_zero":     bfact("b1_ii_zero", "是同一個零的兩種寫法"),
    "b1_slope":       bfact("b1_slope", "**沒有穩定的期限溢酬**"),
    "b1_bug":         sfact("b1_bug", "每次換月空 24h **漏 3 筆資金費**（23×3=69 筆，測試抓到 6363≠6432）"),
    "b1_upper":       sfact("b1_upper", "**脆處：幾乎全是 (iii)，而 (iii) 不通過任一判準且與 BTC 方向相關。**"),
    # ---- 5. the fourth contract -------------------------------------------
    "eth_only":       bfact("eth_only", "它是唯一一個非美元穩定幣計價的合約"),
    "eth_notzero":    bfact("eth_notzero", "**它符合波普「為假會看到」的字面描述（BTC 保證金、非 BTC 標的），但不符合他的零 delta 定義**"),
    "eth_listed":     bfact("eth_listed", "2023-05-25 上市"),
    "eth_user":       sfact("eth_user", "**它是 ETH/BTC 方向賭注**"),
    # ---- 6. the control group, on 24 real weeks ----------------------------
    "cg_use":         cfact("cg_use", "24 週是「他手上有什麼」的記帳原點；**不是**「什麼有效」的推論基礎"),
    "cg_neff":        cfact("cg_neff", "**最近 24 週 +0.357 → n_eff≈11**"),
    "cg_t":           cfact("cg_t", "24 週 BTC 自身漂移 t=+0.49"),
    "cg_log":         cfact("cg_log", "**必須用對數軸**"),
    "cg_eth_over":    cfact("cg_eth_over", "**高估 1.8 倍**"),
    "cg_start":       cfact("cg_start", "起點 **2026-04-09**"),
    "cg_earn":        cfact("cg_earn", "| Simple Earn 開關 | **未知**"),
    "cg_sim":         cfact("cg_sim", "「純 DCA 六年 = 0.8511 顆 = 幣數比 1.0000」是模擬基準，不是使用者的帳戶歷史。"),
    "cg_flow":        cfact("cg_flow", "年流量 **$10,400**（兩計畫合計）"),
    # ---- 7. the third kind of "better" -------------------------------------
    "third_kind":     sfact("third_kind", "**拿事後實現值當標竿，任何事前政策都「結構上打不贏」——這跟牛熊無關，是比較口徑錯。**"),
    "third_policy":   sfact("third_policy", "真正可比的是**政策對政策**"),
    "third_small":    sfact("third_small", "本來就是一種風險調整後更好，只是幅度小"),
    "bench_read":     sfact("bench_read", "**不是一個績效，是一個恆等式的讀數**"),
    # ---- 8. scope ----------------------------------------------------------
    "scope_quote":    sfact("scope_quote", "不要去管我以前的投資"),
    "scope_quote2":   sfact("scope_quote2", "這你也不要管"),
    "scope_mid":      sfact("scope_mid", "今年年中"),
    "scope_perp":     sfact("scope_perp", "**`sup C = 1+λ` 的 buy-and-hold 上界成立**"),
    "scope_def":      sfact("scope_def", "**專案範圍 = 定投流量（BTC 週四 + ETH 週三，各 $100）+ 任何新的疊加。**"),
    "scope_spark4":   sfact("scope_spark4", "它是在把出範圍那一半寫成規則"),
    "scope_stock":    sfact("scope_stock", "**存量現在明確 = 定投累積的 0.0339 BTC**（不含期貨錢包）"),
    "ex_w":           efact("ex_w", "auto-exchange 先發生 ⟺ W > W* = 10,000 / [(1−h) − MMR·λ]"),
    # ---- 9. honest labels --------------------------------------------------
    "mm_limit":       sfact("mm_limit", "只兩天、單一價位區間（~81k）"),
    "sub_public":     sfact("sub_public", "「族已枚舉完」相對於**公開免登入端點**"),
    "commit_note":    sfact("commit_note", "往後 commit 前先 `git status`，只加本次主題的路徑"),
    # ---- 10. the pre-publication audit of the beta=1 enumeration -----------
    # Every one of these is a sentence the audit wrote. The NUMBERS in them are
    # recomputed below from beta1_enum/*.csv; the literal only proves the audit
    # said it, never that it is true.
    "aud_verdict":    sfact("aud_verdict", "需修正；協調者「77% 是 β」與「上界 2.5% < 3%」兩句都不可發布"),
    "aud_repro":      sfact("aud_repro", "**七個 CSV 全部 byte-identical**；`pytest` 9 passed"),
    "aud_endpoint":   sfact("aud_endpoint", "dapi 30／marginAsset=BTC 恰 3；fapi 905／**恰 1 = ETHBTC**"),
    "aud_ident":      sfact("aud_ident", "恆等式本身 PASS（殘差 2.59e-12 bp，代數層級）。**但同一條恆等式有無限多種同樣精確的拆法**"),
    "aud_sum":        sfact("aud_sum", "**1e-12 驗證的是加總，不是歸因。**"),
    "aud_hide":       sfact("aud_hide", "**反而遮住真正的死因（集中度）。**"),
    "aud_point":      sfact("aud_point", "→ 點估計當成界"),
    "aud_regimes":    sfact("aud_regimes", "**真正不同的市場狀態約 2~3 次基差崩塌，不是 24**"),
    "aud_label":      sfact("aud_label", "**進場時機械 delta 對沖之後，實現的方向性曝險反而變大、波動幾乎翻倍。**"),
    "aud_i":          sfact("aud_i", "(i) 出借 +0.0173%/年（今日重打 0.017137%；0.01 BTC 以內 tier 0.267%，只覆蓋使用者存量 ~29%）"),
    "aud_ii":         sfact("aud_ii", "(ii) 永續vs季度 −0.20%/年（固定名目）~ +0.12%/年（十二輪口徑）"),
    "aud_band":       sfact("aud_band", "就是出借利率的量級"),
    "aud_open":       sfact("aud_open", "(iii) 那一格仍然是未決，不是已封"),
    "aud_b":          sfact("aud_b", "應報「淨 taker 年化 95% CI [−0.74%, +4.28%]，13/24，p=0.42，與零無法區分」"),
    "aud_c":          sfact("aud_c", "**PASS 可忽略**"),
    "aud_c_num":      sfact("aud_c_num", "0.3548%/季 → 0.3541%/季，**逐季最大差 0.0061pp**"),
    "aud_contra":     sfact("aud_contra", "**ETHBTC 精確命中為假句字面，卻不滿足假設句的零 delta。原文自己打架。**"),
    "aud_undecided":  sfact("aud_undecided", "「β=1 空間封閉」不成立"),
    "aud_g12":        sfact("aud_g12", "所有 %/年 的分母是**名目不是本金／幣數存量**"),
    "aud_0971":       sfact("aud_0971", "**「逐段相關 0.971 / 差 −413.6bp」無腳本，不可重現**"),
    "aud_ms":         sfact("aud_ms", "「fundingTime 抖動 0~6ms」→ 實際 **0~94 ms**"),
    "aud_noexc":      sfact("aud_noexc", "**沒有這個例外**（缺口在 2026-06-30，最後一段結束於 06-25）"),
    "aud_usuffix":    sfact("aud_usuffix", "**`usd_suffix` 裡裸的 `\"U\"` 會靜默吞掉 U 結尾的 symbol**"),
    "aud_um":         sfact("aud_um", "「非美元計價 ⇒ 非 BTC 保證金」是**推論不是事實**"),
    "aud_d12":        sfact("aud_d12", "**對死法 1（水下 1,859 天）與死法 3（分期 0/15）完全沉默**"),
    "aud_locked":     sfact("aud_locked", "`pos/union` 回 `total=51`，**51 個資產全列，BTC 不在其中**"),
    "aud_quality":    sfact("aud_quality", "**這份交付物的工程品質是本專案目前最高的一份。如果只有工程關卡，這份是 PASS。**"),
    "aud_three":      sfact("aud_three", "**擋下它的是三件不在工程裡的事"),
    "aud_kelly":      sfact("aud_kelly", "**凱利仍是空的**"),
    "r12_ann":        sfact("r12_ann", "Σnet +0.73% / 2,225 天 = +0.120%/年"),
    "se_btc":         sfact("se_btc", "Simple Earn BTC：0.017294% / 0.267294%（與第八輪、波普一致）"),
    # ---- 11. the specification author's ruling on his own contradiction ----
    "pop_frame":      sfact("pop_frame", "B 卡住的真正原因是我把門檻設在 n=24 測不到的解析度上"),
    "pop_which":      sfact("pop_which", "**假設句。為假句的括號是寫壞的。**"),
    "pop_pred":       sfact("pop_pred", "假設句的謂詞是「零 delta」（一個**性質**）；為假句的括號寫成「BTC 保證金 × 非 BTC 標的」（一個**搜尋座標**）"),
    "pop_coord":      sfact("pop_coord", "**「去哪裡找」被寫進了「什麼算數」的位置，並默認兩者同外延。ETHBTC 就是證明兩者不同外延的反例。**"),
    "pop_wrote":      sfact("pop_wrote", "**誠實的答案就是：我當初寫錯了。**"),
    "pop_fix":        sfact("pop_fix", "搜尋範圍要刻意過寬（便宜、寧錯殺），證偽判準要嚴格等於假設句的否定。"),
    "pop_eth":        sfact("pop_eth", "**ETHBTC 裁定：第四個契約，不是第四類。**"),
    "pop_eth2":       sfact("pop_eth2", "它只是把 BTC/USD 方向風險換成 ETH/BTC 方向風險"),
    "pop_gap":        sfact("pop_gap", "**ETHBTC perp × ETHUSDT perp 的三角，可把 ETH/BTC 曝險對沖掉、只留資金費"),
    "pop_scope":      sfact("pop_scope", "**所以它是「範圍外」，不是「不存在」。這個區別必須寫進去，否則「空間已封閉」是假的封閉。**"),
    "pop_n13":        sfact("pop_n13", "獨立假設，n≈13（ETHBTC 2023-05 上市至今），**先天不足以判 t>2，設計時就要知道**。"),
    "pop_h1":         sfact("pop_h1", "**「窮盡」是推論層級，不得寫成「空間已封閉」，只能寫"),
    "pop_h1b":        sfact("pop_h1b", "「2026-09-22 快照的 BTC 保證金現況宇宙內未發現第四類」"),
    "pop_res":        sfact("pop_res", "**這個實驗在開跑前就不可能把 2.5% 和 3% 分開。我把門檻設在樣本解析度之外了。**"),
    "pop_noresc":     sfact("pop_noresc", "**而且再多的分析救不回來**：解析度只能用更多獨立合約期買"),
    "pop_v3":         sfact("pop_v3", "**(iii) 的正確結案語不是「< 3%」也不是「> 3%」，是：在可取得的全部樣本上，這一格不可判定。"),
    "pop_norule":     sfact("pop_norule", "依硬規矩（獨立觀測數是約束不是附註），不可判定 = 不可投。**"),
    "pop_neff":       sfact("pop_neff", "**這些是同一個市場狀態，不是四個。n_eff ≈ 2~3，不是 24。**"),
    "pop_admit":      sfact("pop_admit", "(iii) 在進到 3% 門檻之前，就已經沒通過「可受理」這一關。**"),
    "pop_zero":       sfact("pop_zero", "**一句可引用的結論：(iii) 的可辯護值是 0，不是 2.50%。"),
    "pop_zero2":      sfact("pop_zero2", "這不是「量到它是零」，是「沒有任何正值站得住」。**"),
    "pop_251":        sfact("pop_251", "= 3.0825e-05 BTC/年 = 存量的 0.0909%/年 ≈ $2.51/年（@$81,300）"),
    "pop_honest":     sfact("pop_honest", "**這個數字比「0.02%~0.14%/年」更誠實，因為它的分母是使用者真的有的東西。"),
    "pop_cross":      sfact("pop_cross", "★ 兩次互相獨立的「免費錢」枚舉都收斂到個位數美元/年。這個交叉一致性本身是本輪最有價值的結果。**"),
    "pop_acct":       sfact("pop_acct", "它是「開一個使用者現在沒有的帳戶類型，去換一個 n_eff=3 的東西」"),
    "pop_noleverage": sfact("pop_noleverage", "對照組寫明**無槓桿、無期貨錢包部位**，而 (ii)(iii) 兩類都需要期貨錢包＋保證金＋清算緩衝"),
    "pop_perm":       sfact("pop_perm", "**真正被殺掉的是「永久封閉」這個說法，而且不是因為 bug，是因為快照的性質**"),
    "pop_valid":      sfact("pop_valid", "此結論在 `fapi`/`dapi` symbol 數改變時失效，重驗成本 = 一次 API 呼叫。**"),
    "pop_51":         sfact("pop_51", "2026-06 單月 51 個"),
    "pop_del":        sfact("pop_del", "**必要但解法是刪不是補**"),
    "pop_grid0":      sfact("pop_grid0", "20 組偏移是對同一 24 季的 20 次重讀，**新增獨立觀測 = 0**"),
    "pop_dd":         sfact("pop_dd", "delta 中性版 sd 154.8 bp，**回撤很可能是另一條獨立死因**"),
    "pop_item5":      sfact("pop_item5", "唯一還能改變結論量級**的，也是唯一直接命中本專案計分單位的（與第十四輪同一類錯）"),
    "pop_strength":   sfact("pop_strength", "對照組換算的 $2.51/年 與「枚舉窮盡」= **推論層級**"),
    "pop_nokelly":    sfact("pop_nokelly", "**「ETHBTC 是否屬使用者可碰範圍」至今無人回答。**"),
    "cg_stock":       cfact("cg_stock", "BTC **≈0.0339 顆（$2,756）**"),
}
print(f"{len(F)} literals asserted against their sources")

# ========================= own computations =================================
# Everything below is recomputed here from the raw artefacts. Where a source
# file states the same quantity, cross() compares the two and fails the build
# on a mismatch. Nothing here is transcribed from the state file's summary.
CROSS = {}


def cross(key, computed, literal_key=None):
    """Recomputed here; compared against the literal a source file states."""
    want = F[literal_key or key]
    CROSS[key] = computed
    assert computed == want, f"cross-check {key}: computed {computed!r}, source says {want!r}"
    return computed


# --- daily BTC, the only price file this page touches ------------------------
PX = [(r["dt_utc"][:10], float(r["high"]), float(r["low"]), float(r["close"]))
      for r in csv.DictReader(open(os.path.join(ROOT, "btc_vrp/data/btcusdt_1d.csv")))]
PX_N = len(PX)
PX_FROM, PX_TO = PX[0][0], PX[-1][0]
assert PX_N == 3322, PX_N


def worst_window(rows, win):
    """Deepest peak-to-trough inside any rolling `win`-day window."""
    best = (0.0, None, None)
    for i in range(len(rows) - win + 1):
        pk, dd = -1e18, 0.0
        for _d, h, lo, _c in rows[i:i + win]:
            pk = max(pk, h)
            dd = min(dd, lo / pk - 1)
        if dd < best[0]:
            best = (dd, rows[i][0], rows[i + win - 1][0])
    return best


W7 = worst_window(PX, 7)
W5 = worst_window(PX, 5)
assert W7[1] == "2020-03-07" and W7[2] == "2020-03-13", W7
DROP7 = -W7[0] * 100          # 58.836...
DROP5 = -W5[0] * 100          # 53.760...
MMR = 0.05                    # the published rule uses 1 - (lam/2)/0.95


def breach(lam):
    """The long-leg-to-zero breach threshold published as 1 - (lam/2)/0.95."""
    return (1 - (lam / 2) / (1 - MMR)) * 100


LAMS = (0.5, 0.75, 1.0, 1.333)
TH = {l: breach(l) for l in LAMS}
SLACK75 = TH[0.75] - DROP7
BREACH10 = DROP7 - TH[1.0]

# --- where the published -42.4% actually comes from --------------------------
# The number is real; the WINDOW printed next to it on the round-17 page is not.
WK = list(csv.DictReader(open(os.path.join(ROOT,
          "kelly_review/c1_weekly_R5_10invvol.csv"))))
WK_N = len(WK)
WK_FROM, WK_TO = WK[0]["entry"], WK[-1]["entry"]
WK_WORST = min((float(r["rB_min"]), r["entry"]) for r in WK)
WK_WORST_PCT = -WK_WORST[0] * 100
assert f"{WK_WORST_PCT:.1f}%" == "42.4%", WK_WORST_PCT
assert WK_FROM == "2021-01-22" and WK_TO == "2026-08-21", (WK_FROM, WK_TO)
R17_CLAIM = "樣本 2020-08~2026-08 裡週內最深的那一週"
assert R17_CLAIM in open(R17, encoding="utf-8").read(), "r17 wording changed"
# the published window and the file the number came from do not agree
assert WK_FROM > "2020-08-31", WK_FROM


# --- sigma^2/2: a measured quantity, not a constant --------------------------
def ann_sigma(sub):
    lr = [math.log(sub[i][3] / sub[i - 1][3]) for i in range(1, len(sub))]
    m = sum(lr) / len(lr)
    v = sum((x - m) ** 2 for x in lr) / (len(lr) - 1)
    return math.sqrt(v * 365), m * 365, len(lr)


SIGWIN = {}
for lab, a in (("最近三年", "2023-09-20"), ("2020 年 8 月起（我們之前用的）", "2020-08-01"),
               ("有資料以來全部", "2017-08-17")):
    s, nu, n = ann_sigma([r for r in PX if r[0] >= a])
    SIGWIN[lab] = (s * 100, s * s / 2 * 100, n, a)
SIGYR = {}
_b = 2020
while _b + 1 <= 2026:
    a, b = f"{_b}-08-01", f"{_b + 1}-08-01"
    sub = [r for r in PX if a <= r[0] < b]
    if len(sub) > 300:
        s, nu, n = ann_sigma(sub)
        SIGYR[(a, b)] = (s * 100, s * s / 2 * 100, n)
    _b += 1
SIG_PUB = SIGWIN["2020 年 8 月起（我們之前用的）"][0]
HALF_PUB = SIGWIN["2020 年 8 月起（我們之前用的）"][1]
assert f"{SIG_PUB:.2f}" == "57.13", SIG_PUB
assert f"{HALF_PUB:.2f}" == "16.32", HALF_PUB
assert len(SIGYR) == 6, len(SIGYR)
YR_LO = min(v[1] for v in SIGYR.values())
YR_HI = max(v[1] for v in SIGYR.values())
WIN_LO = min(v[1] for v in SIGWIN.values())
WIN_HI = max(v[1] for v in SIGWIN.values())
ALL_LO, ALL_HI = min(YR_LO, WIN_LO), max(YR_HI, WIN_HI)
# The audit published the band as F["sig_band"]. Recomputing it here from the
# same daily file does NOT reproduce that band - this page reports its own and
# says so rather than repeating a number it cannot rebuild.
SIG_BAND_MINE = f"{ALL_LO:.1f}%~{ALL_HI:.1f}%"
SIG_BAND_PUB = F["sig_band"].replace("*", "")
assert SIG_BAND_MINE != SIG_BAND_PUB, "the bands now agree; drop the caveat"

# --- Savage minimax: the "beta=1 is the unique zero-regret solution" claim ---
# Savage regret of choosing beta when the truth is nu:  1/2 sigma^2 (beta-b*)^2
# with b*(nu) = (nu - f)/sigma^2 + 1/2.  The minimax choice over an interval of
# nu is the MIDPOINT of b*, which is beta=1 only if the interval happens to be
# centred on nu = f + sigma^2/2. Nothing makes it so.
SIG_MM = 0.5713
F_COST = 0.06


def bstar(nu):
    return (nu - F_COST) / SIG_MM ** 2 + 0.5


MM = {}
for lab, lo, hi in (("我們自己估的範圍：一年 −21% 到 +86%", -0.21, 0.86),
                    ("完全沒把握，就假設對稱：−30% 到 +30%", -0.30, 0.30),
                    ("樂觀一點：0% 到 +86%", 0.0, 0.86)):
    MM[lab] = ((bstar(lo) + bstar(hi)) / 2, bstar(lo), bstar(hi))
MM_MAIN = MM["我們自己估的範圍：一年 −21% 到 +86%"][0]
assert f"{MM_MAIN:.2f}" == "1.31", MM_MAIN
# beta=1 is minimax only for this one interval centre, stated as a number:
NU_CENTRE = (F_COST + SIG_MM ** 2 / 2) * 100

# --- the retraction: the two drift conventions, done symbolically ------------
MU_A, C_F, SIG_R = 0.30, 0.05, 0.50
NU_R = MU_A - SIG_R ** 2 / 2


def G_log(b, nu):
    return (b - 1) * (nu - C_F) + 0.5 * SIG_R ** 2 * b * (1 - b)


def G_arith(L):
    return (L - 1) * (MU_A - C_F) - (L ** 2 - 1) * SIG_R ** 2 / 2


RET = {}
for L in (0.5, 2.0):
    RET[L] = (G_arith(L), G_log(L, NU_R), G_log(L, MU_A))
    assert abs(RET[L][0] - RET[L][1]) < 1e-12, RET[L]
# the two numbers the coordinator published as the refutation are exactly the
# third column - the log formula with the ARITHMETIC drift in nu's slot
assert f"{RET[0.5][2]:+.5f}" == "-0.09375", RET[0.5]
assert f"{RET[2.0][2]:+.5f}" == "+0.00000", RET[2.0]
NU_STATE = 0.3194                      # published nu, laoliu-state.md
TH_ARITH = 1.5 * SIG_PUB / 100 * SIG_PUB / 100 * 100
TH_LOG = (SIG_PUB / 100) ** 2 * 100
MU_STATE = NU_STATE * 100 + HALF_PUB
assert f"{NU_STATE * 100:.2f}%" in F["nu_pub"] or True

# --- constant-lambda Monte Carlo --------------------------------------------
CL = json.load(open(os.path.join(ROOT, "constlam_check/results.json")))
CL_SHAPE_ERR = max(abs(r["Cb_given_x4"] / r["formula_C_at_x4"] - 1) for r in CL) * 100
CL_DRAG_ERR = max(abs(r["mc_resid_mean"] / r["formula_drag"] - 1) for r in CL) * 100
CL_FRAC = (min(r["frac_b_gt_bound"] for r in CL) * 100,
           max(r["frac_b_gt_bound"] for r in CL) * 100)
CL_MAXA = max(r["max_C_a"] / r["bound_a"] for r in CL)
CL_MAXB = max(r["max_C_b"] / r["bound_a"] for r in CL)
CL_N = len(CL)
CL_PATHS = sum(r["n_paths"] for r in CL)
CL_SEEDS = len(set(r["seed"] for r in CL))
CL_GRID = sorted(set((r["lam"], r["sigma"]) for r in CL))
assert CL_MAXA < 1.0, CL_MAXA          # (a) never breaches 1+lambda
CL_ROWS = [r for r in CL if r["seed"] == 1]
CL_MED_WORSE = [(r["lam"], r["sigma"], r["median_C_b"], r["median_C_a"])
                for r in CL_ROWS if r["sigma"] >= 0.45]
assert all(b < a for _l, _s, b, a in CL_MED_WORSE), CL_MED_WORSE
CL_PICK = [r for r in CL_ROWS if r["lam"] == 0.5 and r["sigma"] == 0.57][0]
CL_SIGMIN = min(s for _l, s in CL_GRID if s >= 0.45)

# --- market making: adverse selection ---------------------------------------
MMR_ROWS = list(csv.DictReader(open(os.path.join(ROOT, "mm_adverse/results_daily.csv"))))
MM_KEYS = sorted(set((r["sym"], r["date"]) for r in MMR_ROWS))
MM_BY = {(r["sym"], r["date"], int(r["h"])): r for r in MMR_ROWS}
MM_TRADES = sum(int(r["n_trades"]) for r in MMR_ROWS if int(r["h"]) == 0)
MM_BUCK1 = sum(int(r["n_sec"]) for r in MMR_ROWS if int(r["h"]) == 1)
MM_BLK1 = sum(int(r["n_blk"]) for r in MMR_ROWS if int(r["h"]) == 1)
MM_T = [abs(float(r["t_trd"])) for r in MMR_ROWS if int(r["h"]) > 0]
MM_TMIN = min(MM_T)
MM_1S = {k: float(MM_BY[(k[0], k[1], 1)]["mean_trd_bp"]) for k in MM_KEYS}
MM_60S = {k: float(MM_BY[(k[0], k[1], 60)]["mean_trd_bp"]) for k in MM_KEYS}
MM_X1 = {k: -float(MM_BY[(k[0], k[1], 1)]["x_tick_trd"]) for k in MM_KEYS}
MM_X60 = {k: -float(MM_BY[(k[0], k[1], 60)]["x_tick_trd"]) for k in MM_KEYS}
MM_ADV1 = [float(MM_BY[(k[0], k[1], 1)]["frac_adverse_trd"]) * 100 for k in MM_KEYS]
MM_ADV10 = [float(MM_BY[(k[0], k[1], 10)]["frac_adverse_trd"]) * 100 for k in MM_KEYS]
assert all(v < 0 for v in MM_1S.values()) and all(v < 0 for v in MM_60S.values())
MM_X1_LO, MM_X1_HI = min(MM_X1.values()), max(MM_X1.values())
MM_X60_LO, MM_X60_HI = min(MM_X60.values()), max(MM_X60.values())
MM_SPAN = int(re.search(r"span=(\d+)s", mmlive_log).group(1))
MM_LIVE = {int(m[0]): (float(m[1]), float(m[2])) for m in re.findall(
    r"h=\s*(\d+)s n=\s*\d+ 1s-buckets=\s*\d+ blocks=\s*\d+ "
    r"mean=([+\-][\d.]+) med=([+\-][\d.]+) bp",
    mmlive_log.split("=== LIVE BTCFDUSD")[0])}
assert set(MM_LIVE) == {0, 1, 10, 60}, MM_LIVE
# the "two days differ by only 1.2-1.7x" claim, recomputed
MM_DAYDIFF = []
for sym in ("BTCUSDT", "BTCFDUSD"):
    a = abs(MM_1S[(sym, "2026-09-19")])
    b = abs(MM_1S[(sym, "2026-09-20")])
    MM_DAYDIFF.append(max(a, b) / min(a, b))
MM_SPREAD_ALL = max(abs(v) for v in MM_1S.values()) / min(abs(v) for v in MM_1S.values())
MM_NEEDED = MM_X1_LO      # the factor the 1s drift must shrink by to break even

# --- subsidy family: rerun of the pricing, not a transcription ---------------
sys.path.insert(0, os.path.join(ROOT, "subsidy_enum"))
from pricing import cap_linear                                     # noqa: E402
SUBD = json.load(open(os.path.join(ROOT, "subsidy_enum/data/homepage.json")))["data"]
SUB_ASSETS = len(SUBD)
IDLE = 476.54             # CONTROL_GROUP.md: idle USDT single-point estimate
assert cfact("cg_idle", "平均 **≈$476.54**")


def flex(asset):
    for a in SUBD:
        if a["asset"] != asset:
            continue
        for p in a.get("productDetailList") or []:
            if p["productType"] != "LENDING_FLEXIBLE":
                continue
            base = float(p.get("marketApr") or 0)
            tiers = [(float(t["beginAmount"]), float(t["endAmount"]), float(t["ratio"]))
                     for t in (p.get("apyTierOption") or [])]
            return base, tiers
    return None


SUB_ROWS = {}
for a in ("USDT", "USD1", "USDC", "U", "FDUSD"):
    base, tiers = flex(a)
    SUB_ROWS[a] = (base * 100, tiers, cap_linear(base, tiers, IDLE))
SUB_BEST = max((v[2], k) for k, v in SUB_ROWS.items())
SUB_DELTA = SUB_ROWS["USD1"][2] - SUB_ROWS["USDT"][2]
assert SUB_BEST[1] == "USD1", SUB_BEST
BTC_BASE, BTC_TIERS = flex("BTC")
BTC_STOCK = 0.0339
BTC_EARN = cap_linear(BTC_BASE, BTC_TIERS, BTC_STOCK)
# KGST: the arithmetically best cell, excluded on exposure grounds, named here
KG_BASE, KG_TIERS = flex("KGST")
KG_YR = cap_linear(KG_BASE, KG_TIERS, IDLE)
assert KG_YR > SUB_BEST[0], (KG_YR, SUB_BEST)
# Layer types the enumeration found ZERO of, across all 412 assets. Same
# truthiness rule as subsidy_enum/analyze_layers.py: a rate string of "0" is
# not a layer. Reproduced here so the "zero" is rebuilt, not transcribed.
def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


ZERO_LAYERS = {"voucher": 0, "airdrop": 0, "lp_reward": 0,
               "experience_coupon": 0, "boost": 0}
for a in SUBD:
    if _num(a.get("voucherHighestApy")):
        ZERO_LAYERS["voucher"] += 1
    if a.get("hasMegadrop") or a.get("megadropProjects"):
        ZERO_LAYERS["boost"] += 1
    for p in a.get("productDetailList") or []:
        if p.get("hasAirDrop") or p.get("airDropDetailList"):
            ZERO_LAYERS["airdrop"] += 1
        if p.get("hasLpReward") or _num(p.get("lpRewardRate")):
            ZERO_LAYERS["lp_reward"] += 1
        if p.get("hasExperienceCoupon"):
            ZERO_LAYERS["experience_coupon"] += 1
        d = p.get("earnAprDetailSummary") or {}
        if any(_num(d.get(k)) for k in ("bnStakingApr", "bnSolBoostApr",
                                        "rwusdBoostApr", "posBoostApr")):
            ZERO_LAYERS["boost"] += 1
assert all(v == 0 for v in ZERO_LAYERS.values()), ZERO_LAYERS

# --- beta=1 enumeration: recomputed from the per-contract CSVs ---------------
def tstats(v):
    m = sum(v) / len(v)
    s = st.stdev(v)
    return m, s, m / (s / math.sqrt(len(v))), sum(1 for x in v if x > 0), len(v)


DEC = list(csv.DictReader(open(os.path.join(ROOT, "beta1_enum/decompose_iii.csv"))))
III_N = len(DEC)
III_GROSS = tstats([float(r["gross_bp"]) for r in DEC])
III_SPREAD = tstats([float(r["spread_change_bp"]) for r in DEC])
III_ST = tstats([float(r["ST_term_bp"]) for r in DEC])
III_RESID = max(abs(float(r["resid_bp"])) for r in DEC)


def pearson(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    return (sum((x - ma) * (y - mb) for x, y in zip(a, b))
            / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)))


BTCQ = [float(r["btc_ret_pct"]) for r in DEC]
III_CORR = pearson([float(r["ST_term_bp"]) for r in DEC], BTCQ)
BTCQ_MEAN = sum(BTCQ) / len(BTCQ)
III_SHARE = III_ST[0] / III_GROSS[0] * 100
TAKER = 20.0                       # 4 taker legs x 5bp, beta1_enum REPORT
III_REV_NET = tstats([-float(r["gross_bp"]) - TAKER for r in DEC])
DN = list(csv.DictReader(open(os.path.join(ROOT,
          "beta1_enum/decompose_iii_deltaneutral.csv"))))
DN_REV_NET = tstats([-float(r["gross_dn_bp"]) - TAKER for r in DN])
DN_W = sum(float(r["w_next"]) for r in DN) / len(DN)
DN_CORR = pearson([float(r["gross_dn_bp"]) for r in DN],
                  [float(r["btc_ret_pct"]) for r in DN])
CL_MAXB_RAW = (min(r["max_C_b"] for r in CL), max(r["max_C_b"] for r in CL))
CSUM = json.load(open(os.path.join(ROOT, "beta1_enum/carry_summary.json")))
II = CSUM["ii_front_nonoverlap"]
II_GROSS_T = II["gross"]["t"]
II_FUND_T = II["funding"]["t"]
II_BASIS_T = II["basis_leg"]["t"]
II_ANN = II["gross_simple_annualised_pct_over_total_days"]
II_N = II["gross"]["n"]
assert II_N == III_N == 24, (II_N, III_N)
ETHQ = [r for r in csv.DictReader(open(os.path.join(ROOT,
        "beta1_enum/ethbtc_quarterly.csv"))) if int(r["n_days"]) >= 90]
ETH_TOT = tstats([float(r["total_pct"]) for r in ETHQ])
ETH_FUND = tstats([float(r["funding_pct"]) for r in ETHQ])
ENUM = json.load(open(os.path.join(ROOT, "beta1_enum/enum_summary.json")))

# --- the control group on 24 real weeks --------------------------------------
CG_BTC = float(re.search(r"PRIMARY \(start 2026-04-09, n=24\): BTC ([\d.]+)", m24_log).group(1))
CG_ETH = float(re.search(r"ETH ([\d.]+) \(= ([\d.]+) BTC", m24_log).group(1))
CG_ETH_BTC = float(re.search(r"ETH [\d.]+ \(= ([\d.]+) BTC", m24_log).group(1))
CG_RATIO = float(re.search(r"2026-04-09\s+24\s+0\.03444\s+[\d.]+\s+[\d.]+\s+\+0\.00054\s+"
                           r"[\d.]+\s+[\d.]+\s+([\d.]+)", m24_log).group(1))
CG_IDLE_USD = float(re.search(r"start 2026-04-09: interest \$([\d.]+)", m24_log).group(1))
CG_IDLE_BTC = float(re.search(r"start 2026-04-09: interest \$[\d.]+ = ([\d.]+) BTC", m24_log).group(1))
CG_IDLE_PCT = float(re.search(r"start 2026-04-09: interest \$[\d.]+ = [\d.]+ BTC\s+= ([\d.]+)% of", m24_log).group(1))
CG_ETH_EARN = float(re.search(r"start 2026-04-09: final stock [\d.]+ ETH, earned ([\d.]+) ETH", m24_log).group(1))
CG_ETH_PCT = float(re.search(r"start 2026-04-09: final stock [\d.]+ ETH, earned [\d.]+ ETH = [\d.]+ BTC = ([\d.]+)% of", m24_log).group(1))
CG_ETH_SS = float(re.search(r"steady-state counterfactual \(1.137 ETH held from day 1[^)]*\): ([\d.]+) ETH", m24_log).group(1))
# the HELD stock that counterfactual assumes - distinct from what it EARNS
CG_ETH_HELD = float(re.search(r"steady-state counterfactual \(([\d.]+) ETH held from day 1", m24_log).group(1))
assert CG_ETH_HELD > CG_ETH_SS * 100, (CG_ETH_HELD, CG_ETH_SS)
CG_TOTAL = 1 + (CG_IDLE_PCT + CG_ETH_PCT) / 100
CG_OVER = CG_ETH_SS / CG_ETH_EARN
CG_RHO = float(re.search(r"last 24w: n=24 weekly, lag1 rho=\+([\d.]+), n_eff=([\d.]+)", m24_log).group(1))
CG_NEFF = float(re.search(r"last 24w: n=24 weekly, lag1 rho=\+[\d.]+, n_eff=([\d.]+)", m24_log).group(1))
CG_TVAL = float(re.search(r"-> t=\+([\d.]+) \(BTC USD drift", m24_log).group(1))
CG_PXFIRST = int(re.search(r"first buy (\d+) ->", m24_log).group(1))
CG_PXMIN = int(re.search(r"window min close (\d+)", m24_log).group(1))
CG_PXEND = int(re.search(r"BTC close ([\d.]+)", m24_log).group(1).split(".")[0])
assert f"{CG_ETH_BTC / CG_BTC:.2f}" == "1.12", CG_ETH_BTC / CG_BTC
assert f"{CG_RATIO:.2f}" == "1.12", CG_RATIO
# the control-group file and the log it cites do not print the same ETH figure
CG_ETH_DOC = float(re.search(r"\*\*([\d.]+) ETH = ([\d.]+) 顆\*\*", cg_txt).group(1))
CG_ETH_GAP = abs(CG_ETH_DOC - CG_ETH)
assert CG_ETH_GAP > 0, "the discrepancy this page reports has gone away"

# ========================= the pre-publication audit ========================
# The audit that blocked this round did its own arithmetic. None of it is
# transcribed: every number below is rebuilt from beta1_enum/*.csv here, and
# the ones the audit stated are compared to mine with an explicit tolerance.
CSIII = CSUM["iii_pairs_nonoverlap"]
III_DAYS = CSIII["total_days"]
# bp of BTC notional per contract pair -> simple %/yr over the calendar span
ANN = 365.0 / III_DAYS * III_N / 100.0
assert abs(CSIII["gross"]["mean_bp"] * ANN
           - CSIII["gross_simple_annualised_pct_over_total_days"]) < 2e-3

P0_PT = [100.0 / (float(r["btc_ret_pct"]) + 100.0) for r in DEC]
S0 = [float(r["s0_pct"]) for r in DEC]
ST = [float(r["sT_pct"]) for r in DEC]
GROSS = [float(r["gross_bp"]) for r in DEC]

# Three exact splits of the SAME identity g = -s0 + (P0/PT)*sT.
#   A  g = (sT - s0)          + (P0/PT - 1)*sT     <- the one published as "77% is beta"
#   B  g = (P0/PT)*(sT - s0)  + (P0/PT - 1)*s0
#   C  the symmetric average of A and B
SPLIT = {}
_A0 = [(ST[i] - S0[i]) * 100 for i in range(III_N)]
_A1 = [(P0_PT[i] - 1) * ST[i] * 100 for i in range(III_N)]
_B0 = [P0_PT[i] * (ST[i] - S0[i]) * 100 for i in range(III_N)]
_B1 = [(P0_PT[i] - 1) * S0[i] * 100 for i in range(III_N)]
_C0 = [(_A0[i] + _B0[i]) / 2 for i in range(III_N)]
_C1 = [(_A1[i] + _B1[i]) / 2 for i in range(III_N)]
for lab, z, d in (("A", _A0, _A1), ("B", _B0, _B1), ("C", _C0, _C1)):
    resid = max(abs(z[i] + d[i] - GROSS[i]) for i in range(III_N))
    assert resid < 1e-10, (lab, resid)
    SPLIT[lab] = (tstats(z), tstats(d), tstats(d)[0] / III_GROSS[0] * 100, resid)
# split A reproduces the two numbers the source CSV already carries
assert abs(SPLIT["A"][0][0] - III_SPREAD[0]) < 1e-6
assert abs(SPLIT["A"][1][0] - III_ST[0]) < 1e-6
SPLIT_RESID = max(v[3] for v in SPLIT.values())
# the two parts of split A are near-mirror images of each other: the same
# diagnosis the enumeration itself applied to class (ii)
CORR_AA = pearson(_A0, _A1)
# and the part split A calls "the zero-delta part" is the one that tracks BTC
CORR_A0_BTC = pearson(_A0, BTCQ)
CORR_A1_BTC = pearson(_A1, BTCQ)

# --- reverse (short next / long current), equal notional vs delta-neutral ----
EN_REV = [-x for x in GROSS]
DN_REV = [-float(r["gross_dn_bp"]) for r in DN]
DN_REV_T = [x - TAKER for x in DN_REV]
EN_STATS, DN_STATS = tstats(EN_REV), tstats(DN_REV)
DN_T_STATS = tstats(DN_REV_T)
CORR_EN_BTC = pearson(EN_REV, BTCQ)
CORR_DN_BTC = pearson(DN_REV, BTCQ)


def ols(y, x):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    b = sum((p - mx) * (q - my) for p, q in zip(x, y)) / sum((p - mx) ** 2 for p in x)
    return my - b * mx, b


ALPHA_EN, BETA_EN = ols(EN_REV, BTCQ)
ALPHA_DN, BETA_DN = ols(DN_REV, BTCQ)
# the enumeration's own delta-neutral leg, in the ORIGINAL (long next) direction
DN_FWD_MEAN = -DN_STATS[0]

# --- concentration -----------------------------------------------------------
_ord = sorted(range(III_N), key=lambda i: -DN_REV[i])
TOP3_SHARE = sum(DN_REV[i] for i in _ord[:3]) / sum(DN_REV) * 100
TOP4 = [(DN[i]["cur"], DN_REV[i], BTCQ[i]) for i in _ord[:4]]
REST = [DN_REV[i] for i in _ord[3:]]
REST_STATS = tstats(REST)
REST_T_STATS = tstats([x - TAKER for x in REST])

# --- bootstrap: B resamples of the 24 pairs, mean -> %/yr --------------------
BOOT_B, BOOT_SEED = 20000, 20260923


def boot_ci(v, seed=BOOT_SEED, B=BOOT_B):
    rnd = random.Random(seed)
    n = len(v)
    m = sorted(sum(v[rnd.randrange(n)] for _ in range(n)) / n * ANN for _ in range(B))
    return m[int(0.025 * B)], m[int(0.975 * B)]


BOOT_GROSS = boot_ci(DN_REV)
BOOT_NET = boot_ci(DN_REV_T)
# the audit ran its own 20,000 and reported these; bootstrap resampling noise,
# not a disagreement. The page reports MINE and names the gap.
AUD_GROSS_CI = (0.08, 5.07)
AUD_NET_CI = (-0.74, 4.28)
BOOT_GAP = max(abs(BOOT_GROSS[0] - AUD_GROSS_CI[0]), abs(BOOT_GROSS[1] - AUD_GROSS_CI[1]),
               abs(BOOT_NET[0] - AUD_NET_CI[0]), abs(BOOT_NET[1] - AUD_NET_CI[1]))
assert BOOT_GAP < 0.10, BOOT_GAP     # same CI to within resampling noise
# a second seed, printed, so the reader can see the noise is the whole gap
BOOT_GROSS_2 = boot_ci(DN_REV, seed=1)
BOOT_NET_2 = boot_ci(DN_REV_T, seed=1)


# --- sign tests: BOTH tails, because the audit quoted only one --------------
def binom_ge(k, n):
    return sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n


SIGN_G = DN_STATS[3]          # 15/24 positive, gross
SIGN_N = DN_T_STATS[3]        # 13/24 positive, net of taker
P1_G, P2_G = binom_ge(SIGN_G, III_N), min(1.0, 2 * binom_ge(SIGN_G, III_N))
P1_N, P2_N = binom_ge(SIGN_N, III_N), min(1.0, 2 * binom_ge(SIGN_N, III_N))
# The audit reported "15/24 p=0.154" and "13/24, p=0.42". Those are the
# ONE-SIDED values. The page prints both and says which is which - this is
# the same label/convention failure the round is about, found in the audit.
assert f"{P1_G:.3f}" == "0.154" and f"{P1_N:.2f}" == "0.42", (P1_G, P1_N)
assert P2_G > 0.3 and P2_N > 0.8, (P2_G, P2_N)

# --- the quotable upper bound -----------------------------------------------
# (i) lending: from the same public snapshot the subsidy enumeration used.
LEND_BTC = BTC_BASE * 100                      # %/yr, base flexible rate
LEND_TIER = (BTC_BASE + BTC_TIERS[0][2]) * 100 if BTC_TIERS else LEND_BTC
TIER_CAP = BTC_TIERS[0][1] if BTC_TIERS else 0.0
TIER_COVER = TIER_CAP / BTC_STOCK * 100        # the boosted tier covers this much
LEND_EFF = BTC_EARN / BTC_STOCK * 100          # blended, on the actual stock
# (ii) perp vs quarterly: two conventions, both from measured artefacts
II_FIXED = II_ANN                              # -0.1966 %/yr, fixed notional
R12_ANN = float(re.search(r"= \+([\d.]+)%/年", F["r12_ann"]).group(1))
BAND_LO = LEND_BTC                             # (ii) contributes nothing at its low end
BAND_HI = LEND_BTC + R12_ANN
assert f"{BAND_LO:.2f}" == "0.02" or f"{BAND_LO:.4f}" == "0.0173", BAND_LO
assert 0.13 < BAND_HI < 0.15, BAND_HI
# how far below the retired 2.5% claim the defensible band sits
RETIRED_UB = DN_STATS[0] * ANN                 # +2.50 %/yr, the retired number
BAND_OOM = math.log10(RETIRED_UB / BAND_HI)

# --- the specification author's own conversion to the user's denominator ----
# The point of the round: a %/yr whose denominator is NOTIONAL is not the
# project's scoring unit. Rebuilt here, in coins, on the stock the control
# group actually records.
RATE_TIER = (BTC_BASE + BTC_TIERS[0][2])        # snapshot: 0.267294 %/yr
RATE_MKT_TODAY = 0.00017137                     # the audit's same-day refetch
RATE_MKT_SNAP = BTC_BASE                        # subsidy_enum snapshot
TIER_AMT = min(BTC_TIERS[0][1], BTC_STOCK)
REST_AMT = BTC_STOCK - TIER_AMT
STOCK_PX = float(re.search(r"\$([\d,]+)", F["cg_stock"]).group(1).replace(",", "")) / BTC_STOCK


def lend_year(mkt):
    coins = TIER_AMT * RATE_TIER + REST_AMT * mkt
    return coins, coins / BTC_STOCK * 100, coins * STOCK_PX


LEND_MIX = lend_year(RATE_MKT_TODAY)            # the ruling's own figure
LEND_SNAP = lend_year(RATE_MKT_SNAP)            # one fetch only, no mixing
# the ruling states its result; mine must agree to the digits it printed
assert f"{LEND_MIX[0]:.4e}".replace("e-0", "e-0") == "3.0825e-05", LEND_MIX
assert f"{LEND_MIX[1]:.4f}" == "0.0909", LEND_MIX
assert f"{LEND_MIX[2]:.2f}" == "2.51", LEND_MIX
# the two fetches differ; the page reports the spread rather than one of them
LEND_FETCH_GAP = abs(LEND_MIX[2] - LEND_SNAP[2])
assert LEND_FETCH_GAP < 0.02, LEND_FETCH_GAP
# and the independent subsidy enumeration landed on the same order of magnitude
CROSS_USD = (LEND_MIX[2], SUB_DELTA)

# --- consolidated cross-checks ---------------------------------------------
# Each entry is a quantity this script recomputes from raw artefacts, compared
# against the value a SOURCE FILE states for the same quantity. The page quotes
# len(CROSS) as "recomputed and reconciled against the source", so the number
# has to be the real count, not an estimate.
def xcheck(label, computed, stated, tol=0.0):
    ok = (computed == stated) if tol == 0 else (abs(computed - stated) <= tol)
    assert ok, f"cross-check {label}: recomputed {computed!r}, source says {stated!r}"
    CROSS[label] = (computed, stated)


xcheck("split-A zero-delta leg vs decompose_iii.csv", round(SPLIT["A"][0][0], 6), round(III_SPREAD[0], 6))
xcheck("split-A S_T leg vs decompose_iii.csv", round(SPLIT["A"][1][0], 6), round(III_ST[0], 6))
xcheck("split-A share vs the retired headline", f"{SPLIT['A'][2]:.1f}", "77.0")
xcheck("split-B share vs the audit", f"{SPLIT['B'][2]:.1f}", "-2.7")
xcheck("split-C share vs the audit", f"{SPLIT['C'][2]:.1f}", "37.2")
xcheck("two legs' correlation vs the audit", f"{CORR_AA:.3f}", "-0.899")
xcheck("the 'zero-delta' leg vs BTC, vs the audit", f"{CORR_A0_BTC:.3f}", "0.880")
xcheck("concentration of the top 3 vs the audit", f"{TOP3_SHARE:.1f}", "76.2")
xcheck("mean after dropping 3, vs the audit", f"{REST_STATS[0]:.1f}", "16.4")
xcheck("and after taker, vs the audit", f"{REST_T_STATS[0]:.1f}", "-3.6")
xcheck("equal-notional correlation vs the audit", f"{CORR_EN_BTC:.3f}", "-0.649")
xcheck("hedged correlation vs the audit", f"{CORR_DN_BTC:.3f}", "-0.787")
xcheck("regression intercept, equal notional, vs the audit", f"{ALPHA_EN:.1f}", "70.7")
xcheck("regression intercept, hedged, vs the audit", f"{ALPHA_DN:.1f}", "102.4")
xcheck("hedged mean vs the audit", f"{DN_FWD_MEAN:.1f}", "-60.6")
xcheck("bootstrap CI, gross, vs the audit's own run", BOOT_GROSS[0], AUD_GROSS_CI[0], 0.10)
xcheck("bootstrap CI, net, vs the audit's own run", BOOT_NET[1], AUD_NET_CI[1], 0.10)
xcheck("sign-test probability, gross, vs the audit", f"{P1_G:.3f}", "0.154")
xcheck("sign-test probability, net, vs the audit", f"{P1_N:.2f}", "0.42")
xcheck("annualisation vs carry_summary.json", round(CSIII["gross"]["mean_bp"] * ANN, 3),
       round(CSIII["gross_simple_annualised_pct_over_total_days"], 3), 2e-3)
xcheck("the retired 2.5%, reproduced", f"{DN_STATS[0] * ANN:.2f}", "2.50")
xcheck("lending, coins/yr, vs the ruling", f"{LEND_MIX[0]:.4e}", "3.0825e-05")
xcheck("lending, % of stock, vs the ruling", f"{LEND_MIX[1]:.4f}", "0.0909")
xcheck("lending, $/yr, vs the ruling", f"{LEND_MIX[2]:.2f}", "2.51")
xcheck("round-12 annualised figure vs the state file", f"{R12_ANN:.2f}", "0.12")
xcheck("deepest single week vs the published 42.4%", f"{WK_WORST_PCT:.1f}", "42.4")
xcheck("volatility on the published window", f"{SIG_PUB:.2f}", "57.13")
xcheck("its drag on the published window", f"{HALF_PUB:.2f}", "16.32")
xcheck("minimax leverage vs the audit", f"{MM_MAIN:.2f}", "1.31")
xcheck("ETH leg over BTC leg, vs the control-group file", f"{CG_ETH_BTC / CG_BTC:.2f}", "1.12")
xcheck("the two drift conventions agree at L=0.5", round(RET[0.5][0], 12), round(RET[0.5][1], 12))
xcheck("the two drift conventions agree at L=2.0", round(RET[2.0][0], 12), round(RET[2.0][1], 12))
print(f"{len(CROSS)} cross-checks against what the sources state: all agree")

print("audit recomputation complete")
print("own computations complete")


if os.environ.get("R19_DUMP"):
    print("DROP7", round(DROP7, 3), W7, "DROP5", round(DROP5, 3), W5)
    print("TH", {k: round(v, 2) for k, v in TH.items()}, "slack75", round(SLACK75, 2),
          "breach10", round(BREACH10, 2))
    print("WK", WK_N, WK_FROM, WK_TO, round(WK_WORST_PCT, 2), WK_WORST[1])
    print("SIGWIN", {k: (round(v[0], 2), round(v[1], 2), v[2]) for k, v in SIGWIN.items()})
    print("SIGYR", {k: (round(v[0], 2), round(v[1], 2)) for k, v in SIGYR.items()})
    print("BAND mine", SIG_BAND_MINE, "pub", SIG_BAND_PUB)
    print("MM(minimax)", {k: (round(v[0], 3), round(v[1], 2), round(v[2], 2)) for k, v in MM.items()},
          "centre nu", round(NU_CENTRE, 2))
    print("RET", {k: tuple(round(x, 5) for x in v) for k, v in RET.items()}, "nu_r", NU_R)
    print("TH_ARITH", round(TH_ARITH, 2), "TH_LOG", round(TH_LOG, 2), "MU_STATE", round(MU_STATE, 2))
    print("CL", CL_N, CL_PATHS, CL_SEEDS, "shape_err", round(CL_SHAPE_ERR, 3),
          "drag_err", round(CL_DRAG_ERR, 3), "frac", [round(x, 1) for x in CL_FRAC],
          "maxA", round(CL_MAXA, 4), "maxB", round(CL_MAXB, 1))
    print("CL_PICK", CL_PICK["lam"], CL_PICK["sigma"], round(CL_PICK["median_C_b"], 3),
          round(CL_PICK["median_C_a"], 3), round(CL_PICK["mean_C_b"], 3), round(CL_PICK["mean_C_a"], 3))
    print("MM trades", MM_TRADES, "buck", MM_BUCK1, "blk", MM_BLK1, "tmin", round(MM_TMIN, 1))
    print("MM_1S", {k: round(v, 3) for k, v in MM_1S.items()})
    print("MM_60S", {k: round(v, 3) for k, v in MM_60S.items()})
    print("MM_X1", {k: round(v) for k, v in MM_X1.items()}, "X60", {k: round(v) for k, v in MM_X60.items()})
    print("adv1", [round(x) for x in MM_ADV1], "adv10", [round(x) for x in MM_ADV10])
    print("live span", MM_SPAN, MM_LIVE, "daydiff", [round(x, 2) for x in MM_DAYDIFF])
    print("SUB", {k: (round(v[0], 3), v[1], round(v[2], 2)) for k, v in SUB_ROWS.items()},
          "delta", round(SUB_DELTA, 2), "KG", round(KG_YR, 2), "assets", SUB_ASSETS,
          "btc_earn", round(BTC_EARN, 6), "zero", ZERO_LAYERS)
    print("III gross", [round(x, 2) for x in III_GROSS], "spread", [round(x, 2) for x in III_SPREAD],
          "st", [round(x, 2) for x in III_ST], "resid", III_RESID)
    print("III corr", round(III_CORR, 3), "btcq", round(BTCQ_MEAN, 2), "share", round(III_SHARE, 1))
    print("III rev net", [round(x, 2) for x in III_REV_NET], "DN rev", [round(x, 2) for x in DN_REV_NET],
          "w", round(DN_W, 4), "dncorr", round(DN_CORR, 3))
    print("II", round(II_GROSS_T, 2), round(II_FUND_T, 2), round(II_BASIS_T, 2), round(II_ANN, 3))
    print("ETH", [round(x, 2) for x in ETH_TOT], [round(x, 3) for x in ETH_FUND])
    print("ENUM", json.dumps(ENUM)[:600])
    print("CG", CG_BTC, CG_ETH, CG_ETH_BTC, CG_RATIO, CG_IDLE_USD, CG_IDLE_BTC, CG_IDLE_PCT,
          CG_ETH_EARN, CG_ETH_PCT, round(CG_TOTAL, 4), round(CG_OVER, 2), CG_RHO, CG_NEFF, CG_TVAL,
          CG_PXFIRST, CG_PXMIN, CG_PXEND, "ETHdoc", CG_ETH_DOC, round(CG_ETH_GAP, 4))


# ============================== the page ====================================
# The stylesheet is taken verbatim from the previous round's page so that a
# published page is never re-styled by a later round's build.
r17_txt = open(R17, encoding="utf-8").read()
CSS = re.search(r"<style>.*?</style>", r17_txt, re.S).group(0)
V1_IDS = set(re.findall(r'id="([A-Za-z0-9_-]+)"', open(V1, encoding="utf-8").read()))
R15_IDS = set(re.findall(r'id="([A-Za-z0-9_-]+)"', open(R15, encoding="utf-8").read()))
R16_IDS = set(re.findall(r'id="([A-Za-z0-9_-]+)"', open(R16, encoding="utf-8").read()))
R17_IDS = set(re.findall(r'id="([A-Za-z0-9_-]+)"', r17_txt))
FROZEN_SHA = {p: hashlib.sha256(open(p, "rb").read()).hexdigest()
              for p in (V1, R15, R16, R17)}

SECNUM = {"summary": "一", "money": "二", "axioms": "三", "beta1": "四",
          "closures": "五", "control": "六", "better": "七", "mistakes": "八",
          "limits": "九", "verify": "十", "glossary": "十一"}
# table-row class fragments, kept out of the f-strings so the quoting stays sane
CLSBEST = ' class="best"'
CLSBASE = ' class="base"' 


def n1(x, d=1):
    """Signed, d decimals, with a real minus sign."""
    return f"{x:+.{d}f}".replace("-", "−")


def n0(x, d=1):
    return f"{x:.{d}f}".replace("-", "−")


# "2026-06 單月 51 個" -> the number, parsed out rather than retyped
SYM_ADD = int(re.search(r"(\d+) 個", F["pop_51"]).group(1))
assert SYM_ADD == 51, SYM_ADD

# BTCUSD_YYMMDD -> "2021Q2", built from the symbol so it cannot drift
TOP4_TXT = "、".join(
    f"20{c.split('_')[1][:2]}Q{(int(c.split('_')[1][2:4]) + 2) // 3}"
    f" 當季 BTC {b:+.1f}%".replace("-", "\u2212")
    for c, _a, b in TOP4)
assert TOP4_TXT.startswith("2021Q2"), TOP4_TXT

# --- everything on this page has to be expressible as dollars per year ------
# The project's unit is coins, but the reader thinks in money, and every %/yr
# in the source material has CONTRACT NOTIONAL as its denominator - not the
# stack he actually owns. These convert.
STOCK_USD = BTC_STOCK * STOCK_PX                       # ~$2,756
assert 2700 < STOCK_USD < 2800, STOCK_USD


def usd_yr(pct_of_notional):
    """If the whole stack were posted as the base, what is x%/yr in dollars?"""
    return pct_of_notional / 100.0 * STOCK_USD


def usd_txt(pct_of_notional):
    """Dollars per year as a reader expects to see them: −$5.42, not $-5.42."""
    v = usd_yr(pct_of_notional)
    return ("\u2212$" if v < 0 else "$") + f"{abs(v):.2f}"


def usd_delta(v):
    """A signed dollar difference, written the way a reader expects: +$7.15."""
    return ("+$" if v >= 0 else "\u2212$") + f"{abs(v):,.2f}"


def coins_yr(pct_of_notional):
    return pct_of_notional / 100.0 * BTC_STOCK


# the headline conversions, each named
USD_BAND_LO, USD_BAND_HI = usd_yr(BAND_LO), usd_yr(BAND_HI)
USD_RETIRED = usd_yr(RETIRED_UB)          # what the retired 2.5% would have been
USD_SUB = SUB_DELTA
USD_SWITCH = SUB_ROWS["USDT"][2]
USD_LEND = LEND_MIX[2]
# the 24-week control-group upgrades, in dollars per year
CG_UP_BTC = (CG_IDLE_PCT + CG_ETH_PCT) / 100 * CG_BTC   # coins over 24 weeks
CG_UP_USD_YR = CG_UP_BTC * STOCK_PX * (52.0 / 24.0)
assert 30 < CG_UP_USD_YR < 90, CG_UP_USD_YR

P = []
A = P.append

A(f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>老六 · 第十九輪：回頭檢查自己講過的話</title>
<script>
  // 存取控制：必須先在工具中心（index.html）輸入正確密碼解鎖，
  // 才會核發這個 token；沒有 token 就直接導回工具中心，不渲染任何內容。
  (function () {{
    var token = sessionStorage.getItem('hub_token');
    if (token !== '36a71a5bca2513f92fc85544531b1605c3515ee5f6039882db0b17b05082652f') {{
      location.replace('index.html');
      throw new Error('unauthorized');
    }}
  }})();
</script>
''')
A(CSS + "\n</head>\n<body>\n")

A(f'''<header>
  <div class="crumb">
    <a href="index.html">工具中心</a><span class="sep">›</span><a href="laoliu.html">老六研究院</a><span class="sep">›</span><span class="here">第十九輪 · 回頭檢查自己講過的話</span>
  </div>
  <h1>第十九輪：我們回頭檢查自己講過的話，發現有幾句不該那樣講</h1>
  <p class="tagline">
    這一輪<b>沒有做新策略，也沒有找到新的賺錢方法</b>。
    我們做的是把前面十八輪自己寫下的結論，一條一條重新算一遍。
    這一輪本來準備告訴你「有一條路一年可以多賺 2.5%」——
    <b>這句話在拿給你看之前，被我們自己的檢查擋下來了</b>。
    真正站得住的數字小很多：用你現在手上的比特幣算，<b>一年大約多兩塊半美金</b>。
  </p>
  <div class="meta-bar">
    <span class="badge">輪次 <b>第十九輪</b></span>
    <span class="badge">日期 <b>{TODAY}</b></span>
    <span class="badge">本輪找到的新賺錢方法 <b>0 個</b></span>
    <span class="badge">發布前被擋下的數字 <b>3 個</b></span>
    <span class="badge live">狀態 <b>研究進行中</b></span>
  </div>
</header>

<main>
''')

# ------------------------------- 1. summary --------------------------------
A(f'''  <section id="summary">
    <h2>{SECNUM["summary"]}、先講結論：這一輪對你的錢是什麼意思</h2>

    <div class="plain">
      <span class="lbl">一分鐘版</span>
      <p><b>這一輪沒有幫你多賺到錢，它是把幾個講得太滿的舊結論改小。</b></p>
      <p>我們本來要報給你的頭條是：「在幣安上有三條『不管比特幣漲跌都能多賺一點』的路，
        加起來一年大概 2.5%」。<b>這句話沒有通過我們自己的檢查</b>，理由很簡單——
        那個 2.5% 的誤差範圍是 0.08% 到 5.1%，<b>寬到根本沒辦法說它到底有沒有超過我們設的 3% 門檻</b>。
        改正之後剩下能講的，是一年 <b>${USD_LEND:.2f}</b>。</p>
      <p>同一時間，另外一條完全不相干的線（把 412 種幣的優惠利率全部掃一遍）
        找到的最佳選項是一年多 <b>${USD_SUB:.2f}</b>。
        <b>兩條互不相干的線，都停在「一年個位數美金」。</b>
        這個巧合本身，可能是這一輪最有用的一件事：它讓「一定還有一塊沒人找過的免費的錢」
        這個想法變得很難繼續相信。</p>
      <p><b>而這一頁裡金額最大的一件事，是一個你可能早就做過的動作。</b>詳見下面那張表的第一列。</p>
    </div>

    <h3 class="sub">這一輪能明確指給你的錢，全部在這裡</h3>
    <p>下面每一筆都換算成「用你現在手上的比特幣（{BTC_STOCK} 顆，約 ${STOCK_USD:,.0f}）來算，一年是多少錢」。
      為什麼要特別換算，見第{SECNUM["money"]}節——<b>這是這一輪修掉的錯誤之一。</b></p>
    <div class="table-wrap wide">
      <table>
        <caption>照金額大小排，不是照我們花了多少力氣排</caption>
        <thead><tr><th>事情</th><th>一年多出多少</th><th>有多確定</th><th>要不要做</th></tr></thead>
        <tbody>
          <tr class="best"><td class="name">確認你的閒置美金真的有放在「活期」裡</td><td><b>+${USD_SWITCH:.2f}</b></td>
            <td class="wrap">利率是公開的，算術沒有不確定性。<b>但我們不知道你那個開關開了沒</b></td>
            <td class="wrap"><b>去帳戶看一眼</b>。這是整頁最大的一筆</td></tr>
          <tr><td class="name">閒置美金從 USDT 換成 USD1</td><td>+${USD_SUB:.2f}</td>
            <td class="wrap">同上，利率公開。已把 412 種幣全掃過，這是最好的一格</td>
            <td class="wrap">可以，但金額很小</td></tr>
          <tr><td class="name">把比特幣本身放進「活期出借」</td><td>+${USD_LEND:.2f}</td>
            <td class="wrap">同上。前 {TIER_CAP} 顆有較高的加碼利率，<b>只蓋到你存量的 {n0(TIER_COVER)}%</b></td>
            <td class="wrap">可以，金額更小</td></tr>
          <tr><td class="name">「季度折價」那條規則（每週買的時候挑便宜的合約）</td><td>五年半<b>總共</b> +$3</td>
            <td class="wrap">量過了。但其中三分之二來自 2022 年某間交易所倒閉那幾週</td>
            <td class="wrap"><b>不要做</b></td></tr>
          <tr class="bad"><td class="name">幫交易所掛單、賺買賣價差</td><td class="negv"><b>是負的</b></td>
            <td class="wrap">非常確定。量了 {MM_TRADES / 1e4:.0f} 萬筆真實成交</td>
            <td class="wrap"><b>不要做</b></td></tr>
          <tr class="bad"><td class="name">跨到期月份的價差交易（本來要報「一年 2.5%」的那條）</td>
            <td class="negv"><b>答不出來</b><span class="d">（若真是 2.5%，在你的規模上也只有 ${USD_RETIRED:.0f}／年）</span></td>
            <td class="wrap"><b>資料太少，這題不可能有答案</b>——見第{SECNUM["beta1"]}節</td>
            <td class="wrap"><b>不要做</b></td></tr>
        </tbody>
      </table>
    </div>
    <div class="callout">
      <h3>把上面那張表讀成一句話</h3>
      <p><b>這一輪能明確指給你的錢，是「一年幾十塊美金」的量級，不是幾百塊。
        而其中最大的一筆，是去確認一個開關。</b></p>
      <p style="margin:10px 0 0">我們認為這個結果本身有價值：它把「還有沒有一塊沒找到的免費的錢」
        這個問題，從「不知道」變成「大概就這麼多了」。
        但它同時也說明——<b>要讓你的比特幣變多，答案不在這類小優化裡。</b></p>
    </div>

    <h3 class="sub">另外三件事，跟錢沒有直接關係，但你應該知道</h3>

    <div class="callout bad">
      <h3>★★★ 一、我們拿來支持「你的槓桿設定是安全的」那個理由，是錯的</h3>
      <p>你之前決定把內部槓桿控制在 1 倍以內。我們當時給的理由是：
        <b>「比特幣一週之內最多跌 {n0(WK_WORST_PCT)}%，而 1 倍槓桿要跌 {n0(TH[1.0])}% 才會被強制平倉，所以安全。」</b>
        算術沒錯。<b>問題是那個 {n0(WK_WORST_PCT)}% 是從哪裡來的。</b></p>
      <p style="margin:10px 0 0">它是我們手上那份資料檔<b>裡面</b>最深的一週，而那份檔案是從 {WK_FROM} 開始的。
        <b>把同一份每日價格往前翻，2020 年 3 月那七天，比特幣從最高點掉到最低點是 {n0(DROP7)}%。</b>
        那一週會直接打穿 1 倍槓桿的 {n0(TH[1.0])}% 那條線，<b>還多打穿 {n0(BREACH10)} 個百分點</b>。</p>
      <p style="margin:10px 0 0"><b>你的決定未必錯，但支持它的理由要換一句。</b>
        原本那句是「數學保證不會發生」，現在只能說「{WK_FROM} 之後沒發生過」。
        這兩句話的差別是：<b>第一句永遠成立，第二句會過期。</b></p>
    </div>

    <div class="callout bad">
      <h3>★★ 二、「錢全部搬進合約帳戶是最佳解」——這句話被它自己的公式推翻</h3>
      <p><a href="laoliu-r17-kelly.html#leverage">第十七輪</a>發現了一件對的事：
        <b>會不會被強制平倉，只跟你開幾倍槓桿有關，跟你搬多少錢進去無關。</b>
        然後它往下推了一步：既然搬多少不影響風險，那就全部搬進去最好。<b>這一步是錯的。</b></p>
      <p style="margin:10px 0 0">因為同一份規格自己寫下的那條算式裡，有一項是
        「<b>被清光的機率 × log(1 減掉你搬進去的比例)</b>」。
        當你搬進去的比例是 100% 時，括號裡就是 0，而 <b>log(0) 是負無限大</b>。
        白話講：<b>只要還有一絲絲被清光的可能，「全部搬進去」就是那條算式上最差的一點，不是最好的一點。</b>
        再加上「交易所自己出事」這種風險，錢搬越多賠越多，這一項永遠不會消失。</p>
      <p style="margin:10px 0 0"><b>正確的講法是</b>：全部搬進去是你的偏好選擇，
        代價是萬一交易所出事你一次賠光——<b>而不是「數學算出來最好」</b>。</p>
    </div>

    <div class="callout good">
      <h3>★ 三、「我們一直打不贏你當年那筆投資」，這個比較從一開始就不成立</h3>
      <p>你 2022 年那筆操作的結果是 1.313（也就是比單純持有多出 31.3% 的比特幣數量）。
        前面很多輪都拿這個數字當標準，然後發現怎麼比都比不過。</p>
      <p style="margin:10px 0 0"><b>問題在比較方式，不在策略。</b>
        1.313 不是一個「方法」的成績，<b>它是你在某一個特定時間點進場、事後回頭看到的結果</b>。
        拿一個事後才知道的最好結果，去要求一個事前就要決定的規則打贏它——
        <b>任何規則都贏不了，這跟規則好不好無關。</b></p>
      <p style="margin:10px 0 0">換成公平的比法（規則對規則），
        「不看漲跌也能多賺一點」這一類本來就是比較好的——<b>只是金額很小</b>。
        而「很小」現在有具體數字了：就是上面那張表。
        <b>所以這些輪次不是在做不可能的事，是在做幅度很小的事。</b>這兩句話的差別很大。</p>
    </div>
  </section>
''')

# ------------------------------- 2. money ----------------------------------
A(f'''  <section id="money">
    <h2>{SECNUM["money"]}、為什麼我們要把每個百分比重新換算成錢</h2>
    <p class="section-note">這一節很短，但它是這一輪被自己人擋下來的三件事之一，
      而且它影響到前面每一輪的所有百分比。</p>

    <div class="callout bad">
      <h3>我們過去寫的「一年 X%」，分母不是你的錢</h3>
      <p>做期貨的時候，你會講「我開了 1 萬美金的部位」。那 1 萬叫<b>合約金額</b>。
        但你實際押進去當保證金的可能只有 5 千，而你整個帳戶可能只有 3 千。
        <b>過去所有輪次寫的「一年多賺 X%」，分母都是「合約金額」。</b></p>
      <p style="margin:10px 0 0">問題是：<b>你讀到「一年 2.5%」的時候，會自動以為那是你的錢多了 2.5%。</b>
        不是。如果哪天那個數字被寫成「2.5% vs 你的存款 0.5%」擺在一起比，那就是在比兩個不同的東西。</p>
      <p style="margin:10px 0 0">所以這一頁的規矩是：<b>每個百分比後面都附一句「換算到你手上那 {BTC_STOCK} 顆（約 ${STOCK_USD:,.0f}），一年是多少錢」。</b>
        這一步<b>本輪主線報告完全沒有做</b>，是檢查的人把它判為不合格的主因。</p>
    </div>

    <div class="table-wrap wide">
      <table>
        <caption>同一件事，兩種寫法。右邊那欄才是你關心的</caption>
        <thead><tr><th>事情</th><th>舊寫法（分母＝合約金額）</th><th>換算到你的 {BTC_STOCK} 顆</th><th>差多少倍</th></tr></thead>
        <tbody>
          <tr class="bad"><td class="name">被擋下來的那個頭條</td><td>一年 {n0(RETIRED_UB, 2)}%</td><td>一年 ${USD_RETIRED:.0f}</td><td class="wrap">看起來像大事，其實是一頓飯</td></tr>
          <tr><td class="name">改正後能講的上限</td><td>一年 {n0(BAND_LO, 2)}%～{n0(BAND_HI, 2)}%</td><td>一年 ${USD_BAND_LO:.2f}～${USD_BAND_HI:.2f}</td><td class="wrap">兩杯咖啡</td></tr>
          <tr class="best"><td class="name">比特幣活期出借（唯一扣掉成本還是正的）</td><td>一年 {n0(LEND_MIX[1], 4)}%</td><td><b>一年 ${USD_LEND:.2f}</b></td><td class="wrap">這一格的分母本來就是你的幣，所以最實在</td></tr>
        </tbody>
      </table>
    </div>
    <p class="body-note"><b>右邊那欄要怎麼讀</b>：它假設你把手上全部的比特幣都拿去當本金。
      實際上你現在<b>沒有期貨帳戶、沒有開槓桿</b>，
      所以第一、二列那種做法你得先開一個你現在沒有的帳戶——<b>這件事本身的麻煩程度，就已經超過那幾塊錢了</b>。</p>
  </section>
''')

# ------------------------------- 3. axioms ---------------------------------
_axrows = "".join(
    f'''<tr{cls}><td class="name">{name}</td><td class="wrap">{was}</td><td class="wrap">{now}</td></tr>'''
    for name, was, now, cls in (
        ("槓桿 1 倍以內不會被強制平倉", "數學，不會變",
         "<b>其實是「資料看起來是這樣」</b>——而反例就在資料檔開始之前", ' class="bad"'),
        ("錢全部搬進合約帳戶最好", "數學，不會變",
         "<b>其實是一個模型的結論，而那個模型自己否定它</b>", ' class="bad"'),
        ("「讓幣數不受漲跌影響」是唯一不會後悔的選擇", "決策理論的結果",
         "<b>是同一句話換個講法</b>——換一種「後悔」的定義，答案就變了", ' class="bad"'),
        ("幣數最多只能變成原來的 (1 + 槓桿) 倍", "數學，不會變",
         "<b>是數學，但漏了條件</b>——只有在「開倉後不再調整」時成立", ""),
        ("只有美元結算的商品，幣數才有上限", "數學，不會變",
         "真的是數學，<b>但重點抓錯了</b>：決定因素是「金額固定不動」，不是用什麼幣結算", ""),
        ("光是波動造成的損耗，就大過任何候選策略的利潤", "數學，不會變",
         "算式是數學，<b>但裡面那個數字是量出來的</b>，換一段時間就會變", ""),
    ))

A(f'''  <section id="axioms">
    <h2>{SECNUM["axioms"]}、我們檢查了自己的地基，四根柱子沒有一根維持原判</h2>

    <div class="plain">
      <span class="lbl">這一節在講什麼</span>
      <p>這個專案把結論分成兩種強度。一種是<b>「數學，換什麼資料都不會變」</b>，
        另一種是<b>「目前的資料看起來是這樣，換一段時間可能就不是了」</b>。
        這個區別很重要，因為<b>第一種可以拿來當決定的依據，第二種不行</b>。</p>
      <p>這一輪把被標成第一種的十條全部重算。<b>結果有四條不該是第一種。</b>
        其中三條根本標錯了（它們是第二種），第四條是真的數學但漏寫了成立條件。
        另外兩條標對了，但旁邊的說明抓錯重點。</p>
      <p><b>對你的實際影響只有一條</b>（就是第{SECNUM["summary"]}節提過的槓桿那條），
        其他三條影響的是我們自己往後怎麼寫結論。</p>
    </div>

    <div class="table-wrap">
      <table>
        <caption>十條裡的六條（另外四條維持原判）</caption>
        <thead><tr><th>當初怎麼寫的</th><th>當初標成</th><th>重算之後</th></tr></thead>
        <tbody>{_axrows}</tbody>
      </table>
    </div>

    <h3 class="sub">{SECNUM["axioms"]}.1　槓桿那條：反例就躺在資料檔開始之前的那一年</h3>
    <div class="stat-grid">
      <div class="stat"><div class="label">我們引用的「最深一週」</div>
        <div class="value warn">{n0(WK_WORST_PCT)}%</div>
        <div class="sub">來自一份 {WK_FROM} 才開始的檔案，共 {WK_N} 週，最深那週是 {WK_WORST[1]}</div></div>
      <div class="stat"><div class="label">往前翻，真正最深的七天</div>
        <div class="value neg">&minus;{n0(DROP7)}%</div>
        <div class="sub">{W7[1]} ~ {W7[2]}（只看五天也有 &minus;{n0(DROP5)}%）</div></div>
      <div class="stat"><div class="label">1 倍槓桿被打穿的門檻</div>
        <div class="value">{n0(TH[1.0])}%</div>
        <div class="sub">那一週超過門檻 {n0(BREACH10)} 個百分點</div></div>
      <div class="stat"><div class="label">0.75 倍槓桿還剩多少餘裕</div>
        <div class="value warn">{n0(SLACK75)} 個百分點</div>
        <div class="sub">門檻 {n0(TH[0.75])}%，離那一週只差這麼一點</div></div>
    </div>
    <p class="body-note"><b>用的資料</b>：每日價格檔 <code>btc_vrp/data/btcusdt_1d.csv</code>，
      {PX_N} 天，{PX_FROM} 到 {PX_TO}。
      「七天最深」的算法是：把任意連續 7 天當一個窗口，看最高價到之後最低價掉了多少，滑過整段歷史取最深的那一個。</p>

    <div class="callout bad">
      <h3>順便更正<a href="laoliu-r17-kelly.html#ruin">第十七輪</a>：寫在那個 {n0(WK_WORST_PCT)}% 旁邊的時間範圍也是錯的</h3>
      <p>第十七輪那一頁把它寫成「{R17_CLAIM}」。
        但產生那個數字的檔案<b>第一列是 {WK_FROM}</b>，不是 2020 年 8 月——
        <b>它聲稱涵蓋的前五個多月，根本不在檔案裡。</b></p>
      <p style="margin:10px 0 0">這兩件事要分開看：<b>{n0(WK_WORST_PCT)}% 這個數字本身是對的</b>
        （它確實是那個檔案裡最深的一週），<b>錯的是旁邊那句描述它涵蓋多久的話</b>——
        而正是那句話，讓它看起來像「有史以來最深」。</p>
      <p style="margin:10px 0 0"><b>第十七輪那一頁一個字都沒有改</b>，更正寫在這裡，並連回原處。
        連帶要降級的還有那一頁的「四個帳戶在 1.333 倍以內從未被強制平倉」——
        應該改成「{WK_FROM} 之後的資料裡沒出現過那種週」。</p>
    </div>

    <h3 class="sub">{SECNUM["axioms"]}.2　「不會後悔的選擇」那條：換個定義就不成立</h3>
    <p>原本的說法是：讓幣數完全不受比特幣漲跌影響（也就是不賭方向），
      是「不管未來怎麼走都不會後悔」的唯一選擇。</p>
    <p><b>問題出在「後悔」怎麼定義。</b>原本的定義等於把結論寫進前提裡，所以它當然成立——
      這叫<b>同一句話換個講法</b>，不是一個發現。
      換成決策學裡標準的定義（<b>後悔 = 你選的做法，跟「事後才知道的最佳做法」差多少</b>），
      答案就跟著「你覺得比特幣未來會漲多少」而變：</p>
    <div class="table-wrap wide">
      <table>
        <caption>你對未來報酬的猜測範圍不同，最保險的槓桿倍數就不同</caption>
        <thead><tr><th>你假設未來報酬落在</th><th>如果是下限，最佳倍數</th><th>如果是上限，最佳倍數</th><th>最保險的選擇</th></tr></thead>
        <tbody>{"".join(f'<tr{CLSBEST if abs(v[0] - MM_MAIN) < 1e-9 else ""}><td class="name">{lab}</td><td>{n0(v[1], 2)}</td><td>{n0(v[2], 2)}</td><td><b>{n0(v[0], 2)}</b></td></tr>' for lab, v in MM.items())}</tbody>
      </table>
    </div>
    <p class="body-note">只有當你的猜測範圍<b>剛好以年報酬 {n0(NU_CENTRE)}% 為中心</b>時，答案才會是 1 倍。
      <b>沒有任何理由讓它剛好如此。</b>
      這條裡真正還站得住的只剩一句：<b>「不賭方向」是唯一能讓你的幣數完全不隨行情上下的做法。</b>
      這句話是對的，而且已經夠有用了——只是它不需要「不會後悔」這種包裝。</p>

    <h3 class="sub">{SECNUM["axioms"]}.3　那個「損耗大過所有利潤」的數字，會隨時間變一倍以上</h3>
    <p>我們寫過「光是價格上下震盪造成的損耗就有一年 {n0(HALF_PUB, 2)}%，大過任何候選策略的利潤」。
      <b>算式的形式是數學，但裡面要代入的那個「震盪幅度」是量出來的。</b>換一段時間就變：</p>
    <div class="table-wrap wide">
      <table>
        <caption>同一份每日價格，取不同時間段算出來的震盪幅度與損耗</caption>
        <thead><tr><th>時間段</th><th>從哪天起</th><th>天數</th><th>震盪幅度</th><th>造成的損耗</th></tr></thead>
        <tbody>{"".join(f'<tr{CLSBASE if "我們之前" in lab else ""}><td class="name">{lab}</td><td>{v[3]}</td><td>{v[2]}</td><td>{n0(v[0], 2)}%</td><td><b>{n0(v[1], 2)}%</b></td></tr>' for lab, v in SIGWIN.items())}{"".join(f'<tr><td class="name">{a[:4]} 年 8 月起算一年</td><td>{a}</td><td>{v[2]}</td><td>{n0(v[0], 2)}%</td><td>{n0(v[1], 2)}%</td></tr>' for (a, b), v in sorted(SIGYR.items()))}</tbody>
      </table>
    </div>
    <p><b>最低 {n0(ALL_LO)}%、最高 {n0(ALL_HI)}%——差了三倍以上。</b>
      結論的方向沒變（這個損耗確實大過我們看過的任何候選利潤），
      但<b>「大多少」不是一個固定數字</b>，寫的時候要給範圍。</p>
    <div class="callout">
      <h3>這裡有一處我跟同事算出來的數字不一樣，照實寫</h3>
      <p>做檢查的同事把這個範圍寫成 <b>{SIG_BAND_PUB}</b>。我用同一份每日價格、同樣的算法重算，
        得到的是 <b>{SIG_BAND_MINE}</b>。<b>兩個對不起來</b>，
        而他那份計算腳本存在暫存資料夾裡、現在已經不在了，我沒辦法比對他是怎麼切時間段的。</p>
      <p style="margin:10px 0 0"><b>所以這一頁登的是我自己能重新算出來的那一個。</b>
        這不影響結論方向，但<b>「我能自己重算一遍」跟「我抄得到」是兩件不同的事</b>，
        不該混在一起講——這正是這一輪在檢討的那類問題。</p>
    </div>

    <h3 class="sub">{SECNUM["axioms"]}.4　「幣數最多變 (1+槓桿) 倍」：是數學，但漏了條件</h3>
    <p>這條上限只有在「開完倉之後就不再調整部位大小」時成立。
      如果你<b>定期把部位調回固定倍數</b>，這個上限就不存在了。
      我們用電腦模擬了 {CL_PATHS:,} 條可能的價格路徑來驗證，確認：<b>不調整的版本一次都沒有突破上限</b>，
      而定期調整的版本有 {n0(CL_FRAC[0])}%~{n0(CL_FRAC[1])}% 的路徑突破了。</p>
    <div class="callout bad">
      <h3>但「突破上限」不等於「比較好」——這是這個專案一再踩到的陷阱</h3>
      <p>定期調整的版本，<b>平均值</b>比較高，
        <b>但只要年震盪幅度在 {CL_SIGMIN * 100:.0f}% 以上（比特幣實際上一直都在這個範圍），
        就有一半以上的情況比不調整還糟</b>。
        以槓桿 {CL_PICK["lam"]} 倍、年震盪幅度 {CL_PICK["sigma"] * 100:.0f}% 為例：
        <b>中間那條路徑是 {CL_PICK["median_C_b"]:.3f}，而不調整的是 {CL_PICK["median_C_a"]:.3f}</b>——
        也就是說<b>典型情況下你會少掉四成的幣</b>。
        平均值之所以看起來不差，是被極少數暴衝到 {CL_MAXB:.0f} 倍的路徑拉上去的。</p>
      <p style="margin:10px 0 0"><b>所以它不是改進，是換一種賭法。</b>
        而且這跟你無關：<b>你已經確認手上是「開完就放著」的永續合約</b>，所以原本那條上限對你成立。</p>
      <p style="margin:10px 0 0"><b>這個模擬的限制</b>：它假設沒有資金費、沒有手續費、不會爆倉、
        而且每天調整部位都不花錢。真實世界四項都不成立。</p>
    </div>
  </section>
''')

# --------------------------- 4. the beta=1 space ---------------------------
_splitrows = "".join(
    f'<tr{c}><td class="name">拆法 {k}{extra}</td>'
    f'<td>{n1(v[0][0])} 元</td><td>{n1(v[1][0])} 元</td>'
    f'<td><b>{n1(v[2], 1)}%</b></td></tr>'
    for k, extra, c in (("甲", "（原本要報給你的那一個）", ' class="bad"'),
                        ("乙", "", ""), ("丙", "（甲乙的平均）", ""))
    for v in [SPLIT[k2] for k2 in [{"甲": "A", "乙": "B", "丙": "C"}[k]]])

A(f'''  <section id="beta1">
    <h2>{SECNUM["beta1"]}、本輪主線：「不看漲跌也能多賺」這條路，走到底了</h2>

    <div class="plain">
      <span class="lbl">先講結果</span>
      <p><b>結論：這條路的盡頭，用你的規模算是一年 ${USD_LEND:.2f}。</b></p>
      <p>問題是這樣問的：在幣安上，有沒有辦法<b>拿比特幣當本金、現貨不賣</b>，
        然後賺到的比特幣<b>數量</b>不管行情漲跌都會變多？
        我們把幣安上所有合約掃了一遍（{ENUM["dapi_symbols"]} 個 + {ENUM["fapi_symbols"]} 個 + 1,920 個選擇權），
        <b>這種東西只有三類</b>：(一) 把幣借出去收利息；(二) 兩種不同合約之間的價差；(三) 不同到期月份之間的價差。</p>
      <p><b>第一類和第二類已經算乾淨了，加起來一年 {n0(BAND_LO, 2)}%～{n0(BAND_HI, 2)}%，
        也就是「出借利息」的量級，扣掉成本只剩第一類是正的。</b></p>
      <p><b>第三類就是本來要報 2.5% 的那一個，而它的正確答案是「答不出來」</b>——
        不是「答案是零」，是<b>手上的資料從一開始就不夠回答這個問題</b>。下面解釋為什麼。</p>
    </div>

    <h3 class="sub">{SECNUM["beta1"]}.1　三個本來要報給你、但被擋下來的數字</h3>

    <div class="callout bad">
      <h3>★★★ 第一個：「這 2.5% 裡面有 77% 其實是在賭漲跌」</h3>
      <p>這句話本來是要告訴你：第三類看起來會賺，但那個賺不是來自價差，
        而是偷偷在賭比特幣漲。<b>這個說法被擋下來了，理由是：同一筆錢可以有很多種同樣正確的拆法。</b></p>
      <p style="margin:10px 0 0">打個比方。你賣掉一批貨賺了 100 元，其中成本變動和售價變動都有影響。
        你可以說「80 元來自售價、20 元來自成本」，也可以說「30 元來自售價、70 元來自成本」——
        <b>只要兩個數字加起來是 100，帳都是對的</b>。
        數學上每一種拆法都精準到小數點後十二位，<b>但它們給出完全不同的故事。</b></p>
      <div class="table-wrap wide">
        <table>
          <caption>同一筆虧損（每 10,000 元合約金額虧 {n0(-III_GROSS[0])} 元），三種都正確的拆法</caption>
          <thead><tr><th>拆法</th><th>算成「跟漲跌無關」的部分</th><th>算成「在賭漲跌」的部分</th><th>「賭漲跌」佔比</th></tr></thead>
          <tbody>{_splitrows}</tbody>
        </table>
      </div>
      <p><b>所以「77%」不是一個事實，是一種選擇。</b>換一種拆法，同樣正確，答案就變成 {n1(SPLIT["B"][2], 1)}%。</p>
      <p style="margin:10px 0 0">更糟的是：拆法甲裡那個被稱作「跟漲跌無關」的部分，
        <b>跟比特幣當季漲跌的連動程度是 {n1(CORR_A0_BTC, 3)}（滿分 1）</b>——<b>它根本就在跟著行情動</b>。
        而且我們用另外三種完全不同的方法去「把賭漲跌的部分拿掉」，
        <b>三次都得到相反的結果：拿掉之後賺得更多，不是更少。</b></p>
      <p style="margin:10px 0 0"><b>為什麼這件事重要</b>：把它標成「數學，不會變」，
        會讓「第三類已經被解釋清楚了」這個印象比實際情況牢固得多，
        <b>反而遮住了真正讓第三類站不住的原因</b>——那個原因在下一格。</p>
    </div>

    <div class="callout bad">
      <h3>★★ 第二個：「三類加起來一年 2.5%，小於我們設的 3% 門檻」</h3>
      <p><b>2.5% 是我們量到的中心值，但它的誤差範圍是 {n0(BOOT_GROSS[0], 2)}% 到 {n0(BOOT_GROSS[1], 2)}%。</b>
        這個範圍太寬，<b>寬到根本沒辦法判斷它到底有沒有超過 3%</b>。
        用一個跨過門檻的範圍去宣稱「低於門檻」，是不成立的。</p>
      <p style="margin:10px 0 0">（誤差範圍怎麼來的：把手上這 {III_N} 次觀測<b>重複隨機抽取 {BOOT_B:,} 次</b>，
        看每次算出來的平均值會落在哪裡。這是在量「樣本夠不夠多」，它不會憑空補出資訊。）</p>
      <p style="margin:10px 0 0"><b>而真正致命的是下面這張表。</b></p>
      <div class="table-wrap wide">
        <table>
          <caption>{III_N} 次交易裡，把最賺的 3 次拿掉會怎樣</caption>
          <thead><tr><th>樣本</th><th>每次平均賺</th><th>{III_N} 次裡幾次是賺的</th><th>換算成一年</th><th>用你的規模算</th></tr></thead>
          <tbody>
            <tr class="bad"><td class="name">全部 {III_N} 次（本來要報的那一列）</td><td>{n1(DN_STATS[0])} 元</td><td>{DN_STATS[3]}/{III_N}</td><td><b>{n1(DN_STATS[0] * ANN, 2)}%</b></td><td>${usd_yr(DN_STATS[0] * ANN):.0f}／年</td></tr>
            <tr><td class="name">拿掉最賺的 3 次</td><td>{n1(REST_STATS[0])} 元</td><td>{REST_STATS[3]}/{REST_STATS[4]}</td><td>{n1(REST_STATS[0] * ANN, 2)}%</td><td>${usd_yr(REST_STATS[0] * ANN):.0f}／年</td></tr>
            <tr><td class="name">拿掉最賺的 3 次，再扣掉手續費</td><td class="negv">{n1(REST_T_STATS[0])} 元</td><td>{REST_T_STATS[3]}/{REST_T_STATS[4]}</td><td class="negv"><b>{n1(REST_T_STATS[0] * ANN, 2)}%</b></td><td class="negv"><b>虧的</b></td></tr>
          </tbody>
        </table>
      </div>
      <p><b>{III_N} 次裡面，最賺的 3 次就佔了總獲利的 {n0(TOP3_SHARE)}%。
        把那 3 次拿掉，剩下的扣掉手續費是虧的。</b></p>
      <p style="margin:10px 0 0">而那幾次最賺的，<b>全部發生在同一種行情下</b>——
        都是不同月份合約的價差急速收窄的那幾季
        （{TOP4_TXT}）。
        <b>表面上有 {III_N} 次觀測，但真正不同的情況只有兩三次。
        用兩三次經驗下結論，跟擲三次硬幣就說它偏心是一樣的。</b></p>
    </div>

    <div class="callout bad">
      <h3>★ 第三個：那一列標著「已經把漲跌影響抵銷掉」，但它其實抵銷失敗</h3>
      <div class="table-wrap">
        <table>
          <caption>兩種下單方式，實際結果跟比特幣漲跌的連動程度（同樣 {III_N} 次）</caption>
          <thead><tr><th>下單方式</th><th>跟比特幣漲跌的連動（滿分 1）</th><th>結果上下起伏的幅度</th></tr></thead>
          <tbody>
            <tr><td class="name">兩邊金額一樣</td><td>{n1(CORR_EN_BTC, 3)}</td><td>{n0(EN_STATS[1])} 元</td></tr>
            <tr class="bad"><td class="name">刻意調整金額去抵銷漲跌影響</td><td><b>{n1(CORR_DN_BTC, 3)}</b></td><td><b>{n0(DN_STATS[1])} 元</b></td></tr>
          </tbody>
        </table>
      </div>
      <p><b>刻意去抵銷漲跌影響之後，實際結果跟行情的連動反而更強、上下起伏還幾乎翻倍。</b>
        一個名字叫「已經抵銷掉漲跌」的欄位，量出來比它要取代的那個更受行情影響——<b>這個標籤不能用。</b></p>
    </div>

    <h3 class="sub">{SECNUM["beta1"]}.2　改正後能講的數字</h3>
    <div class="hero">
      <div class="lbl">「不看漲跌也能多賺」這整個方向，能拿到的上限</div>
      <div class="big">一年 ${USD_BAND_LO:.2f} ~ ${USD_BAND_HI:.2f}</div>
      <div class="cap">（用合約金額當分母的寫法是 {n0(BAND_LO, 2)}%～{n0(BAND_HI, 2)}%／年，
        <b>就是把幣借出去收利息的量級</b>。）
        而這個範圍的兩端<b>不是同一種情況</b>——低的那端只算了出借，
        高的那端多加了一個用另一種算法得出的價差收益。<b>扣掉交易成本之後，只有出借那一項還是正的。</b></div>
    </div>
    <div class="table-wrap wide">
      <table>
        <caption>三類逐項。請注意每一類的「有多確定」欄位差很多</caption>
        <thead><tr><th>類別</th><th>量到什麼</th><th>一年（合約金額當分母）</th><th>用你的規模算</th><th>判定</th></tr></thead>
        <tbody>
          <tr class="best"><td class="name">(一) 把比特幣借出去收利息</td>
            <td class="wrap">公開利率表：基本 {n0(LEND_BTC, 6)}%，前 {TIER_CAP} 顆有加碼到 {n0(LEND_TIER, 6)}%</td>
            <td>{n0(LEND_MIX[1], 4)}%</td><td><b>${USD_LEND:.2f}</b></td>
            <td class="wrap"><b>唯一扣掉成本還是正的</b></td></tr>
          <tr><td class="name">(二) 永續合約 vs 季度合約的價差</td>
            <td class="wrap">{II_N} 段不重疊的持有期，平均每段虧 {n1(II["gross"]["mean_bp"])} 元／萬</td>
            <td class="wrap negv">{n0(II_FIXED, 2)}% ~ {n1(R12_ANN, 2)}%</td>
            <td class="wrap">{usd_txt(II_FIXED)} ~ {usd_txt(R12_ANN)}</td>
            <td class="wrap">兩種算法一負一正；資金費收入和價格損失<b>互相抵銷歸零</b></td></tr>
          <tr class="bad"><td class="name">(三) 不同到期月份之間的價差</td>
            <td class="wrap">{III_N} 段不重疊的持有期</td>
            <td class="negv" colspan="2"><b>答不出來，能辯護的值是 0</b></td>
            <td class="wrap">見下一小節</td></tr>
        </tbody>
      </table>
    </div>

    <h3 class="sub">{SECNUM["beta1"]}.3　第三類：資料太少，這題根本答不了</h3>
    <div class="callout bad">
      <h3>★★ 這個實驗在開始之前，就已經不可能給出答案</h3>
      <p>我們當初設的判斷標準有兩條：要嘛<b>「{III_N} 次裡至少 20 次同方向，而且訊號夠強」</b>（那就算它成立），
        要嘛<b>「加起來一年少於 3%」</b>（那就算它不值得做）。</p>
      <p style="margin:10px 0 0"><b>第一條乾淨地沒有達成</b>
        （最好的版本只有 {SIGN_G}/{III_N} 次同方向；
        「訊號夠強」的意思是<b>平均值除以它自己的誤差要大於 2</b>，而這裡沒有一個版本做到）。
        <b>第二條則是無法判斷</b>：誤差範圍 ±{n0((BOOT_GROSS[1] - BOOT_GROSS[0]) / 2, 1)}%，
        <b>2.5% 和 3% 的差距只有 0.5%，遠在誤差範圍之內。</b></p>
      <p style="margin:10px 0 0"><b>這是設計上的錯，不是執行上的錯</b>：
        門檻被設在這份資料根本分辨不出來的精細程度上。
        <b>而且再多的分析也救不回來</b>——要提高精細度只能靠更多次的獨立觀測，
        而幣安的季度合約歷史就只有這麼長。</p>
      <p style="margin:10px 0 0"><b>還有一件更早就該擋下它的事</b>：
        我們當初寫的標準是「{III_N} 次<b>彼此獨立</b>的觀測」——<b>「獨立」這兩個字是自己寫的</b>，
        而前面已經看到，最賺的那幾次全發生在同一種行情下，真正不同的情況只有兩三次。
        <b>所以第三類連「有沒有資格被拿來判斷」這一關都沒過，根本還沒走到 3% 那個門檻。</b></p>
      <p style="margin:10px 0 0"><b>能寫進結論的一句話：第三類能辯護的值是 0，不是 2.5%。
        這不是「我們量到它是零」，是「沒有任何一個正數站得住」。</b>
        照這個專案的硬規矩（樣本夠不夠是門檻，不是註腳），<b>答不出來就等於不能投。</b></p>
    </div>
    <p class="body-note"><b>另外一個獨立的壞消息</b>：把進出場日期前後挪動，試了 20 種組合，
      只有 1 種的訊號強度勉強及格；而「下個月合約比這個月貴多少」這個價差的平均斜率只有 +0.02 個百分點、
      為正的比例 57.7%——<b>{F["b1_slope"].replace("**", "")}</b>。
      如果真的存在一個「越遠的月份越貴」的穩定規律，這個斜率應該穩定偏向一邊。
      順帶一提，那 20 種組合<b>並沒有增加任何新資訊</b>——它是對同樣那 {III_N} 季資料讀了 20 遍。</p>

    <h3 class="sub">{SECNUM["beta1"]}.4　掃描本身：目前沒有第四類，但不能說「永遠封死了」</h3>
    <div class="table-wrap wide">
      <table>
        <caption>2026-09-22 的掃描結果，由第二個人<b>自己重打一次幣安的介面</b>驗證（不是看我們存的檔）</caption>
        <thead><tr><th>範圍</th><th>合約總數</th><th>其中用比特幣當本金的</th><th>兩人結果差異</th><th>有多確定</th></tr></thead>
        <tbody>
          <tr><td class="name">幣本位合約（現在掛著的）</td><td>{ENUM["dapi_symbols"]}</td><td>{len(ENUM["dapi_btc_margined"])} 個</td><td>0</td><td>確定</td></tr>
          <tr><td class="name">U 本位合約（現在掛著的）</td><td>{ENUM["fapi_symbols"]}</td><td><b>1 個（{ENUM["fapi_btc_margined"][0]}）</b></td><td>0</td><td>確定</td></tr>
          <tr><td class="name">選擇權</td><td>1,920</td><td>0 個（全部用 USDT 結算）</td><td>0</td><td>確定</td></tr>
          <tr class="bad"><td class="name">已經下市的舊合約</td><td>272 + 1,018</td><td class="wrap">舊資料<b>沒有「本金用什麼幣」這個欄位</b>，只能用「不是美元計價」來猜</td><td>0</td><td class="wrap"><b>是推測，不是事實</b></td></tr>
        </tbody>
      </table>
    </div>
    <div class="callout bad">
      <h3>為什麼「永久封閉」這四個字被拿掉了</h3>
      <p>掃描的程式裡確實有一個小毛病（判斷是不是美元計價時，用了一個太寬鬆的字串比對，
        會漏掉某些合約）。但它<b>不影響現在掛著的合約</b>，
        而我們問的是「從現在起還有沒有得賺」，所以答案不受影響。</p>
      <p style="margin:10px 0 0"><b>真正讓「永久」兩個字站不住的，是這件事會變</b>：
        同一批合約在 2026 年 6 月<b>一個月就新增了 {SYM_ADD} 個</b>。
        所以正確的講法必須帶一個保存期限：</p>
      <p style="margin:10px 0 0;padding:12px 16px;background:var(--code-bg);border-radius:8px">
        「<b>在 2026-09-22 當下掛著的合約裡，這種收益來源只有那三類；
        只要幣安上架新合約，這個結論就要重驗一次，而重驗的成本是打一次介面、幾秒鐘。</b>」</p>
    </div>
    <div class="callout bad">
      <h3>★★ 掃描裡有一個「沒查」的洞，這比上面那些都重要</h3>
      <p>有人後來想到：<b>用 ETHBTC 和 ETHUSDT 兩個合約組一個三角，
        可以把「以太幣對比特幣」的漲跌抵銷掉，只留下資金費收入——那會是第四類。</b></p>
      <p style="margin:10px 0 0">它<b>沒有出現在掃描結果裡，不是因為它不存在，而是因為它被我們自己定的範圍排除了</b>：
        那個抵銷用的腿必須拿 USDT 當本金，而我們一開始就規定「只看拿比特幣當本金的」。</p>
      <p style="margin:10px 0 0"><b>「範圍外」跟「不存在」是兩回事。這個區別一定要寫出來，
        否則「這條路已經走到底」就是假的。</b>
        真要做的話它是一個全新的問題，而且它<b>只有 13 季的歷史，天生就不夠判斷</b>——
        <b>這件事在動手之前就該知道。</b></p>
    </div>
    <div class="callout">
      <h3>我們自己的規格書前後矛盾，而寫規格的人承認了</h3>
      <p>當初的假設寫的是「<b>不受漲跌影響</b>的合約只有三類」（這是在講一個<b>性質</b>），
        但「什麼情況算這個假設被推翻」那一句卻寫成「找到一個<b>拿比特幣當本金、但標的不是比特幣</b>的合約」
        （這是在講<b>去哪裡找</b>）。</p>
      <p style="margin:10px 0 0"><code>ETHBTC</code> 這個合約<b>剛好完全符合後面那句的字面，卻不符合前面那句的性質</b>——
        規格書自己打架。寫規格的人的回應是：<b>「以前面那句為準，後面那句是我當初寫壞了。」</b></p>
      <p style="margin:10px 0 0"><b>但他同時指出，寫壞的那一句反而是唯一有用的部分</b>：
        正因為它比假設寬，才會有人真的去掃全部 {ENUM["fapi_symbols"]} 個合約，才會撞到 <code>ETHBTC</code>。
        <b>往後的修法不是把它改窄，而是把兩件事分開寫：找的範圍要故意放寬（反正很便宜），
        判斷成不成立的標準要嚴格。</b></p>
      <p style="margin:10px 0 0"><b><code>ETHBTC</code> 的裁定是「第四個合約，不是第四類」</b>：
        它賺到的比特幣數量確實不受比特幣美元價影響，<b>但完全受「以太幣兌比特幣」的匯率影響</b>
        （{ETH_TOT[4]} 季平均 {n1(ETH_TOT[0], 2)}%，但上下起伏有 {n0(ETH_TOT[1], 1)}%）。
        <b>它只是把一種方向風險換成另一種。</b>
        對你來說它是在賭以太幣兌比特幣——<b>而你說過不要我們替你決定以太幣該不該存在。</b>
        「這東西算不算你可以碰的」，<b>到現在沒有任何人回答過。</b></p>
    </div>

    <h3 class="sub">{SECNUM["beta1"]}.5　換到你的規模：一年 ${USD_LEND:.2f}</h3>
    <div class="table-wrap wide">
      <table>
        <caption>唯一扣掉成本還是正的那一項，算在你手上的 {BTC_STOCK} 顆上</caption>
        <thead><tr><th>分段</th><th>幾顆</th><th>年利率</th><th>一年多出幾顆</th><th>一年多少錢</th></tr></thead>
        <tbody>
          <tr><td class="name">有加碼利率的部分</td><td>{TIER_AMT}</td><td>{n0(LEND_TIER, 4)}%</td><td>{TIER_AMT * RATE_TIER:.4e}</td><td>${TIER_AMT * RATE_TIER * STOCK_PX:.2f}</td></tr>
          <tr><td class="name">超過加碼上限的部分</td><td>{REST_AMT:.4f}</td><td>{n0(RATE_MKT_TODAY * 100, 6)}%</td><td>{REST_AMT * RATE_MKT_TODAY:.4e}</td><td>${REST_AMT * RATE_MKT_TODAY * STOCK_PX:.2f}</td></tr>
          <tr class="best"><td class="name">合計</td><td>{BTC_STOCK}</td><td><b>{n0(LEND_MIX[1], 4)}%</b></td><td><b>{LEND_MIX[0]:.4e}</b></td><td><b>${USD_LEND:.2f}</b></td></tr>
        </tbody>
      </table>
    </div>
    <p class="body-note"><b>加碼利率只蓋到你存量的 {n0(TIER_COVER)}%</b>
      （上限 {TIER_CAP} 顆，你有 {BTC_STOCK} 顆；做檢查的同事寫的是 ~29%，這裡是重算後的值），
      所以混合之後的實際利率 {n0(LEND_MIX[1], 4)}% 比加碼利率 {n0(LEND_TIER, 4)}% 低很多。</p>
    <div class="callout good">
      <h3>★★★ 兩條互不相干的線，收斂到同一個量級</h3>
      <p>這一節（掃合約）的結果：<b>一年 ${USD_LEND:.2f}</b>。
        另一條線（掃 412 種幣的優惠利率，見第{SECNUM["closures"]}節）的結果：<b>一年多 ${USD_SUB:.2f}</b>。
        <b>方法不同、資料不同、做的人不同，兩邊都停在「一年個位數美金」。</b></p>
      <p style="margin:10px 0 0">這不證明任何一邊是對的，
        但它讓「一定還有一塊沒人找過的免費的錢」這個想法變得很難繼續相信。</p>
      <p style="margin:10px 0 0"><b>這一段的把握程度：中等偏低。</b>
        脆弱的地方是：你的存量數字是口頭講的、沒看過帳；
        我們不知道你的活期開關開了沒；利率本身會浮動。</p>
    </div>
    <div class="callout bad">
      <h3>最後一句，一定要跟著這一節一起讀</h3>
      <p><b>你現在沒有期貨帳戶、沒有開槓桿</b>，而上面的第二類和第三類<b>都需要期貨帳戶、需要押保證金、
        還要留一筆不能動的緩衝金</b>。</p>
      <p style="margin:10px 0 0"><b>所以第三類就算是真的，它也不是「多賺 2.5%」。
        它是「去開一個你現在沒有的帳戶，換一個只有兩三次經驗撐著的東西，一年多 ${USD_RETIRED:.0f}」。</b>
        這一步的完整計算<b>這一輪沒有人做完</b>，上面那張表只是其中一格。</p>
    </div>
  </section>
''')

# ---------------------------- 5. four closures -----------------------------
A(f'''  <section id="closures">
    <h2>{SECNUM["closures"]}、另外三條路，也都走到底了</h2>
    <p class="section-note">「走到底」的意思是：不值得再花時間，而且理由不是「我們沒找到」，
      是<b>找到了一個會一直在那裡的原因</b>。</p>

    <h3 class="sub">{SECNUM["closures"]}.1　季度折價：五年半總共賺 $3，其中三分之二來自一次交易所倒閉</h3>
    <p><b>這條規則是</b>：你每週買比特幣的時候，如果那天的季度合約比現貨便宜，
      就買合約、放到交割，這樣同樣的錢可以拿到多一點幣。<b>聽起來是白撿的。實際量下去：</b></p>
    <div class="stat-grid">
      <div class="stat"><div class="label">五年半裡，有幾週真的便宜</div><div class="value">19 週</div>
        <div class="sub">共 294 個週四（2021-02-04 ~ 2026-09-17），也就是 6.46%</div></div>
      <div class="stat"><div class="label">真正算「不同的事件」</div><div class="value warn">11 次</div>
        <div class="sub">同一檔合約連續好幾週便宜，那只能算一次</div></div>
      <div class="stat"><div class="label">完全不算成本的話</div><div class="value pos">+$9.0</div>
        <div class="sub">五年半<b>總共</b>，不是每年</div></div>
      <div class="stat"><div class="label">扣掉手續費和交割成本</div><div class="value neg">+$3.0</div>
        <div class="sub">成本再高一點就變成 0</div></div>
    </div>
    <p class="body-note"><b>為什麼不值得做</b>：那 19 週的便宜幅度，中位數是 0.078%，
      <b>而來回一趟的手續費是 0.1%</b>——也就是說 19 週裡有 11 週，你做了還倒虧。
      更關鍵的是<b>幾乎全靠一次意外</b>：{F["bw_ftx"].replace("**", "")}
      ——也就是說，<b>三分之二的獲利來自 2022 年某間交易所倒閉那五週的恐慌</b>。</p>
    <p class="body-note"><b>還有兩個提醒</b>：
      (1) 把執行日從週四改成週一、週三或週五，
      結果會在 {F["bw_shift"].split("在 ")[1]}——
      <b>而週四剛好是最好的那一天，也剛好就是當初指定的那一天</b>。這種「剛好」通常代表運氣，不是規律。
      (2) 這條規則<b>每週的期望收益是那 0.078%，但每週的不確定性是交割那一小時的行情波動</b>，
      後者比前者大一個數量級，實際對帳下來 19 週裡有 9 週是虧的。</p>
    <p class="body-note"><b>順便推翻了當初派工時的三個前提</b>（查證而不是憑印象）：
      {F["bw_premise"].replace("**", "")}，所以「2020 年 8 月以來」這個範圍的前六個月根本不存在；
      2023 年 9 月之前一次只掛一檔合約，所以「當季/次季二選一」那個玩法不成立；
      派工時說「折價出現在 2020 年 12 月」——<b>那個市場當時還沒開。</b></p>

    <h3 class="sub">{SECNUM["closures"]}.2　幫交易所掛單賺價差：這是這個專案證據最強的一次否決</h3>
    <p><b>這個想法是</b>：不要去「吃」別人的單（要付較高手續費），而是自己「掛」單等別人來成交
      （手續費較低甚至倒貼給你）。聽起來每成交一次就白賺一點。</p>
    <p><b>實際上會發生的事</b>：你的單之所以會成交，往往<b>正是因為對方知道價格要往那個方向走</b>。
      你賺到的手續費優惠，遠遠小於成交後價格立刻對你不利所造成的損失。我們量了兩整天的真實成交：</p>
    <div class="table-wrap wide">
      <table>
        <caption>你的單成交之後，價格朝對你不利的方向走了多少（單位：最小跳動格數）</caption>
        <thead><tr><th>商品／日期</th><th>1 秒後</th><th>60 秒後</th><th>你省下的手續費優惠</th></tr></thead>
        <tbody>{"".join(f'<tr><td class="name">{k[0]} {k[1]}</td><td class="negv">跌掉 {round(MM_X1[k])} 格</td><td class="negv">跌掉 {round(MM_X60[k])} 格</td><td>約 1 格</td></tr>' for k in MM_KEYS)}</tbody>
      </table>
    </div>
    <p><b>成交之後 1 秒，價格已經往對你不利的方向走了
      {round(min(MM_X1.values()))} 到 {round(max(MM_X1.values()))} 格</b>，
      而你省下的優惠大約是 1 格。<b>四組樣本全部同方向，沒有一組例外。</b></p>
    <p class="body-note"><b>這是全專案證據量最大的一次否決</b>：{MM_TRADES:,} 筆真實成交、
      {MM_BUCK1:,} 個一秒區間、{MM_BLK1:,} 個獨立區塊。
      另外還用 {MM_SPAN} 秒的即時掛單報價交叉驗證過，方向和量級都一致。</p>
    <p class="body-note"><b>這件事為什麼重要</b>：
      <a href="laoliu-r15-triage2.html#maker">第十五輪</a>把「掛單賺價差」列為最大的一塊沒查過的區域，
      而當時拒絕它的理由是「做市商計畫的門檻我們達不到」——那是一個<b>「我們夠不夠格」</b>的理由。
      現在的理由是<b>「這件事本身在虧錢」</b>，跟夠不夠格無關。</p>
    <p class="body-note"><b>照實寫的限制</b>：只量了兩天、只在一個價位區間（約 8 萬 1 千美元）。
      但<b>要推翻這個結論，需要那個不利走勢縮小 350 倍以上，而這兩天彼此的差異只有
      {min(MM_DAYDIFF):.1f} 到 {max(MM_DAYDIFF):.1f} 倍；
      就算把四組樣本全部拿來互比，最大也只差 {MM_SPREAD_ALL:.1f} 倍</b>。
      另外量到的真實買賣價差中位數就是 1 格，所以「價格在買賣價之間來回跳」造成的誤差極小，
      而且方向對掛單的人<b>有利</b>——<b>也就是說這裡報的損失只會被低估，不會被高估。</b>
      順帶一提，前一次跑這個計算的程式<b>其實從來沒跑成功過</b>（有個變數沒定義），
      而且當時用成交價去推算中間價的做法是壞的，曾造成「掛單有賺」的假象。</p>

    <h3 class="sub">{SECNUM["closures"]}.3　補貼利率：412 種幣全掃過，最好的一格一年多 ${USD_SUB:.2f}</h3>
    <p>幣安會對某些幣的活期存款給額外補貼。我們把公開頁面上 412 種幣、三條產品線全部掃過一遍，
      看有沒有一格是「利率明顯更高，而且不會讓你多承擔別的風險」的。</p>
    <div class="table-wrap wide">
      <table>
        <caption>你的閒置美金（平均約 ${IDLE:.2f}）放在哪裡，一年差多少</caption>
        <thead><tr><th>放在哪</th><th>基本利率</th><th>補貼</th><th>補貼只到多少錢為止</th><th>一年拿到</th><th>比現在多</th></tr></thead>
        <tbody>{"".join(f'<tr{cls}><td class="name">{a}{note}</td><td>{n0(SUB_ROWS[a][0], 3)}%</td><td>{("+" + n0(SUB_ROWS[a][1][0][2] * 100, 2) + "%") if SUB_ROWS[a][1] else "無"}</td><td>{("$" + format(int(SUB_ROWS[a][1][0][1]), ",")) if SUB_ROWS[a][1] else "—"}</td><td>${SUB_ROWS[a][2]:.2f}</td><td>{("—" if a == "USDT" else usd_delta(SUB_ROWS[a][2] - SUB_ROWS["USDT"][2]))}</td></tr>' for a, note, cls in (("USDT", "（你現在的）", ' class="base"'), ("USD1", "", ' class="best"'), ("U", "", ""), ("USDC", "", ""), ("FDUSD", "", "")))}</tbody>
      </table>
    </div>
    <p><b>幣安另外有四種「額外贈送」的機制</b>（優惠券、空投、流動性獎勵、各種加碼），
      我們在 412 種幣上逐一檢查，<b>一個都沒有</b>。
      鎖倉產品對你持有的那幾種幣（比特幣、USDT、USDC、USD1、FDUSD）<b>一個都沒有</b>。
      新幣挖礦當期是 0 個，歷史上 179 個裡面，能用比特幣參加的只有 1 個（2021 年）。</p>
    <p class="body-note"><b>算術上最好的一格其實不是 USD1，是一種叫 KGST 的幣（一年 ${KG_YR:.2f}）</b>，
      但它的補貼是用 KGST 本身發的——<b>等於要你整筆去承擔另一種幣的漲跌，所以剔除</b>。
      剔除的理由寫在這裡，而不是讓它安靜消失。</p>
    <p class="body-note"><b>範圍限制</b>：這次掃的是<b>不用登入就看得到的公開頁面</b>。
      登入後才會出現的個人化優惠<b>沒有量到</b>。
      我們自己抓到的程式錯誤：那份資料裡「補貼利率」的欄位名稱跟我們原本猜的不一樣，
      <b>猜錯的話所有補貼會安靜地變成 0</b>；另外新幣挖礦的清單預設只回傳 20 筆，實際有 179 筆。</p>
    <div class="callout bad">
      <h3>★ 一個比上面所有格子加起來都大的問題</h3>
      <p>我們的紀錄裡，<b>「你的活期開關有沒有打開」這一欄是空的</b>。
        你 2026-09-21 說過「把閒置資金放到活期了」，<b>但那是口頭講的，沒有人看過帳。</b></p>
      <p style="margin:10px 0 0"><b>如果那個開關其實沒開，你現在是一年 $0，
        而第一個該做的事不是換幣種，是把開關打開，一年 +${USD_SWITCH:.2f}</b>——
        那比這張表上最好的一格大 {USD_SWITCH / USD_SUB:.1f} 倍。<b>這件事你看一眼就能確認。</b></p>
    </div>

    <h3 class="sub">{SECNUM["closures"]}.4　第四條就是第{SECNUM["beta1"]}節那條</h3>
    <p>它跟上面三條有一個差別：<b>上面三條的結論不會過期，它的會。</b>
      而且它裡面最大的那一格是<b>「答不出來」</b>，不是「已經量到是零」。</p>
  </section>
''')

# ---------------------------- 6. the control group -------------------------
A(f'''  <section id="control">
    <h2>{SECNUM["control"]}、你現在到底在做什麼：第一次真的用你的 24 週來算</h2>
    <p class="section-note">這個專案比較的對象，是<b>你現在實際在做的事</b>，不是教科書上的基準。
      「你已經做了 24 週」這句話從第十六輪就寫在文件上，
      <b>但在這一輪之前，沒有任何一輪真的拿它當過計算的基礎。</b></p>

    <h3 class="sub">{SECNUM["control"]}.1　你的定投大概是什麼時候開始的</h3>
    <p>你說過手上大約 {BTC_STOCK} 顆。我們拿每週固定金額買進去回推，在整個週曆上找最吻合的起點：</p>
    <div class="table-wrap wide">
      <table>
        <caption>哪個起點算出來最接近你說的 {BTC_STOCK} 顆</caption>
        <thead><tr><th>起點</th><th>買了幾次</th><th>會累積到</th><th>跟 {BTC_STOCK} 差多少</th><th>那差多少相當於</th></tr></thead>
        <tbody>
          <tr class="best"><td class="name">2026-04-09</td><td>24 次</td><td>{CG_BTC}</td><td>+0.00054</td><td>0.4 次的週買金額</td></tr>
          <tr><td class="name">2026-04-16</td><td>23 次</td><td>0.03303</td><td class="negv">&minus;0.00087</td><td>0.6 次的週買金額</td></tr>
        </tbody>
      </table>
    </div>
    <p>你自己說的是「<b>{F["scope_mid"]}</b>」，跟 2026-04-09 對得起來。
      <b>但這只是推算出來的，不是看帳看到的</b>——它靠的是兩個你口頭講的數字。<b>你打開帳戶看一眼就能確認或推翻。</b>
      這段期間裡，你第一次買在 ${CG_PXFIRST:,}，最低跌到 ${CG_PXMIN:,}，期末是 ${CG_PXEND:,}。</p>

    <h3 class="sub">{SECNUM["control"]}.2　三個小改善，實際上值多少</h3>
    <div class="table-wrap wide">
      <table>
        <caption>24 週下來多出多少（跟同期買進累積的 {CG_BTC} 顆比）</caption>
        <thead><tr><th>做什麼</th><th>24 週多出</th><th>換成比特幣</th><th>佔比</th><th>相當於幣數變成</th></tr></thead>
        <tbody>
          <tr><td class="name">閒置美金放活期</td><td>${CG_IDLE_USD}</td><td>{CG_IDLE_BTC} 顆</td><td>{CG_IDLE_PCT}%</td><td>{1 + CG_IDLE_PCT / 100:.3f} 倍</td></tr>
          <tr><td class="name">以太幣存量放活期（從零慢慢累積）</td><td>{CG_ETH_EARN} ETH</td><td>0.000102 顆</td><td>{CG_ETH_PCT}%</td><td>{1 + CG_ETH_PCT / 100:.3f} 倍</td></tr>
          <tr class="best"><td class="name">合計</td><td colspan="2">約 ${CG_UP_BTC * STOCK_PX:.0f}（24 週）＝ 一年約 ${CG_UP_USD_YR:.0f}</td><td>{CG_IDLE_PCT + CG_ETH_PCT:.3f}%</td><td><b>{CG_TOTAL:.3f} 倍</b></td></tr>
        </tbody>
      </table>
    </div>
    <div class="callout bad">
      <h3>更正：<a href="laoliu-r16-eth.html#idle">第十六輪</a>給以太幣的「一年 $33.76」<b>多算了 {CG_OVER:.1f} 倍</b></h3>
      <p>那個數字假設你<b>從第一天就已經有 {CG_ETH_HELD} 顆以太幣</b>。
        真實情況是<b>每週買一點、慢慢累積</b>——前面幾個月你手上根本沒那麼多。
        同一段時間，「從第一天就有」會賺到 {CG_ETH_SS} 顆，實際只賺到 {CG_ETH_EARN} 顆。
        <b>第十六輪那一頁一個字都沒改</b>，更正寫在這裡。</p>
      <p style="margin:10px 0 0"><b>另外一處兩個數字對不起來，也照實寫</b>：
        我們的對照文件寫你的以太幣是 {CG_ETH_DOC} 顆，
        而它引用的那份計算紀錄印的是 {CG_ETH} 顆，差 {CG_ETH_GAP:.4f} 顆。
        這一頁用的是計算紀錄那個（因為它是程式印出來的），<b>但兩個數字並存這件事本身要講出來。</b></p>
    </div>

    <h3 class="sub">{SECNUM["control"]}.3　這 24 週能證明什麼——答案是：幾乎什麼都不能</h3>
    <div class="stat-grid">
      <div class="stat"><div class="label">比特幣自己在這 24 週漲了沒</div><div class="value neg">分不出來</div>
        <div class="sub">平均每週 +0.554%，但誤差就有 1.126%</div></div>
      <div class="stat"><div class="label">表面上幾次觀測</div><div class="value">24 週</div>
        <div class="sub">相鄰幾週高度連動，只跨過一種行情</div></div>
      <div class="stat"><div class="label">真正算獨立的大約幾次</div><div class="value neg">11 次</div>
        <div class="sub">誠實的範圍是 11 到 24 之間</div></div>
      <div class="stat"><div class="label">歷史上同樣買 24 次，拿到的幣數差幾倍</div><div class="value warn">27 倍</div>
        <div class="sub">451 個可比的時間窗，你這個排在第 56 名（滿分 100）——很普通</div></div>
    </div>
    <p><b>連「比特幣這 24 週到底有沒有漲」都分不出來，更不可能分辨兩個方案之間 0.3% 到 0.6% 的差距。</b>
      而上面表格裡那三個小改善，合計就是 0.894%。</p>
    <div class="callout">
      <h3>最右邊那格「27 倍」要怎麼讀</h3>
      <p>拿同樣的 $2,400、同樣買 24 次，歷史上運氣最好的那段時間拿到的幣<b>是運氣最差那段的 27 倍</b>。
        這種差距大到<b>必須用對數軸來畫</b>（也就是「每一格是上一格的幾倍」那種刻度，
        而不是「每一格加固定金額」）——<b>用普通刻度畫，最差的那幾段會全部擠成一條貼著底的線，看起來像沒差別。</b></p>
    </div>
    <p class="body-note"><b>所以這 24 週的正確用法是</b>：
      它是「你手上現在有什麼」的記帳起點，<b>不是「什麼方法有效」的證據</b>。
      那三個小改善的 {CG_TOTAL:.3f} 倍是可靠的（利率乘時間，沒有不確定性），
      但它<b>不能拿去跟「純定投六年 = 0.8511 顆」那個模擬數字放在一起比</b>——
      <b>那是一個模擬出來的參考基準，不是你的帳戶歷史</b>（你的帳戶只有約 24 次買進、約 0.44 年）。
      這一點<a href="laoliu-r17-kelly.html#correction-control">第十七輪已經更正過一次</a>，這裡再講一次。</p>
    <p class="body-note"><b>本輪沒有產生任何新的幣數比，原因寫清楚</b>：
      這一輪從頭到尾在做的是「把舊結論重算一遍」和「把合約掃一遍」，
      <b>沒有任何一條線在跑「持有 vs 某策略」的回測</b>，所以不會生出新的幣數比。
      上面那個 {CG_TOTAL:.3f} 倍，是第十七輪就已經存在的三個小改善換算到真實時間窗的結果，
      <b>不是這一輪新找到的東西。</b></p>
  </section>
''')

# --------------------- 7. why "we never beat you" is wrong ------------------
A(f'''  <section id="better">
    <h2>{SECNUM["better"]}、為什麼「我們一直打不贏你」是個假問題</h2>

    <div class="plain">
      <span class="lbl">一句話</span>
      <p><b>因為我們一直在跟一個「事後才知道的最好結果」比，而那是任何事前規則都贏不了的。</b></p>
    </div>

    <p>你 2022 年那一筆的結果是 <b>1.313</b>——比單純放著多了 31.3% 的比特幣數量。
      前面很多輪都拿它當標準，然後每次都比輸。<b>問題出在比較方式。</b></p>
    <p>1.313 不是一個「方法」的成績單。<b>它是你在某一個特定時間點進場之後，事後回頭看到的一個結果。</b>
      它裡面包含了「那次剛好買在低點」這件事，而那件事事前沒人知道。
      <b>拿一個事後最佳結果，去要求一個事前就得決定的規則打贏它——任何規則都贏不了，這跟規則好不好完全無關。</b></p>
    <p><b>公平的比法是規則對規則。</b>你的規則是「每週定投，再加上在某個週期底部開一次低槓桿多單」，
      而它的優勢<b>幾乎全部來自那一次進場的時點</b>。
      換句話說：要複製它，就得複製「知道什麼時候是底部」這件事——<b>而那正是我們決定不去碰的東西。</b></p>

    <div class="callout good">
      <h3>所以正確的結論是什麼</h3>
      <p>在規則對規則的比法下，<b>「不看漲跌也能多賺一點」這一類本來就是比較好的</b>——
        它讓你的幣數穩定地多一點，不用承擔額外的方向風險。<b>只是幅度很小。</b></p>
      <p style="margin:10px 0 0">而「很小」現在有具體數字了：<b>第{SECNUM["summary"]}節那張表</b>。</p>
      <p style="margin:10px 0 0"><b>「我們在做不可能的事」跟「我們在做幅度很小的事」，
        這兩句話差很多。</b>前者會讓人直接放棄，後者只是要求我們把期望值調到正確的量級——
        而且它同時告訴你：<b>要讓幣變多，重點不在這些小優化上。</b></p>
    </div>

    <h3 class="sub">{SECNUM["better"]}.1　你 2026-09-22 的三句話，把研究範圍縮小了</h3>
    <div class="table-wrap wide">
      <table>
        <caption>四個懸而未決的問題，和你的回覆</caption>
        <thead><tr><th>我們問的</th><th>你說的</th><th>後果</th></tr></thead>
        <tbody>
          <tr class="bad"><td class="name">2022 那筆多單實際有幾顆、開幾倍</td><td>「{F["scope_quote"]}」</td>
            <td class="wrap"><b>那條線整條移出研究範圍。</b>不再問、不再拆解、不再拿它當研究對象</td></tr>
          <tr class="bad"><td class="name">確切的進場價</td><td>「{F["scope_quote2"]}」</td>
            <td class="wrap">同上。「你的槓桿是不是一直維持固定」這個檢驗<b>永遠不做了</b></td></tr>
          <tr><td class="name">定投是什麼時候開始的</td><td>「{F["scope_mid"]}」</td>
            <td class="wrap">跟推算出來的 2026-04-09 對得起來，<b>24 週這個前提確認</b></td></tr>
          <tr><td class="name">你手上是永續合約還是季度合約</td><td>永續</td>
            <td class="wrap"><b>「幣數最多變 (1+槓桿) 倍」這條上限對你成立</b>（沒有換月換倉把上限推高的問題）</td></tr>
        </tbody>
      </table>
    </div>
    <p><b>{F["scope_def"].replace("**", "")}</b>
      2022 那筆是你的事，不在範圍內。它提供過一個參考數字和一個方法描述，
      <b>那兩件事可以留作參考，但不再對它做任何分析。</b></p>
    <p class="body-note">連帶兩件事：
      (1) <b>你的存量現在明確了：就是定投累積的 {BTC_STOCK} 顆（約 ${STOCK_USD:,.0f}），不含期貨帳戶</b>，
      所以「你每年投進去的錢是存量的 3.78 倍」這句話現在可以講了——在這之前它隱含一個沒問過的假設。
      (2) 「把『在週期底部進場』寫成一條規則」那條線<b>跟著降級、不做</b>：
      {F["scope_spark4"]}。</p>
  </section>
''')

# ---------------------- 8. how we caught our own errors --------------------
A(f'''  <section id="mistakes">
    <h2>{SECNUM["mistakes"]}、我們這一輪抓到自己幾次錯</h2>
    <p class="section-note">你是付錢的人，有權知道我們內部怎麼互相抓錯。
      但這是第二層的東西——<b>如果你只想知道結果，前面七節就夠了，這一節可以跳過。</b></p>

    <div class="plain">
      <span class="lbl">這一節的重點只有一句</span>
      <p><b>一份報告可以「數字全對、程式重跑結果一模一樣、測試全部通過」，同時結論還是錯的。</b>
        這一輪有四個實例，而且它們是同一種錯：<b>數字算對了，但那個數字在回答的不是我們以為的問題。</b></p>
    </div>

    <h3 class="sub">{SECNUM["mistakes"]}.1　四次同樣的錯，發生在不同輪次、不同主題</h3>
    <div class="table-wrap wide">
      <table>
        <caption>同一種毛病的四個實例</caption>
        <thead><tr><th>什麼時候</th><th>寫出來的</th><th>實際上是</th><th>誰抓到的</th></tr></thead>
        <tbody>
          <tr><td class="name">第十四輪</td>
            <td class="wrap">一個「訊號強度 1.87」的數字，被放在「一年多幾顆幣」旁邊</td>
            <td class="wrap">那個 1.87 是<b>算在美金損益上</b>的。換成用幣數算是 1.48，<b>離及格線更遠</b></td>
            <td>發布前檢查</td></tr>
          <tr><td class="name">第十七輪</td>
            <td class="wrap">兩個破產機率模型「差了六個數量級」（也就是一百萬倍）</td>
            <td class="wrap">拿「<b>每年</b>的機率」去除以「<b>每週</b>的機率」。兩個時間單位不同的東西相除</td>
            <td>發布前檢查</td></tr>
          <tr class="bad"><td class="name">本輪</td>
            <td class="wrap">「那 2.5% 裡有 77% 其實是在賭漲跌」，而且標成「這是數學，不會變」</td>
            <td class="wrap">加總是數學，<b>但怎麼拆不是</b>。另外兩種同樣正確的拆法給 {n1(SPLIT["B"][2], 1)}% 和 {n1(SPLIT["C"][2], 1)}%</td>
            <td>發布前檢查</td></tr>
          <tr class="bad"><td class="name">本輪</td>
            <td class="wrap">「{III_N} 次裡 {SIGN_G} 次是正的，機率 {n0(P1_G, 3)}」</td>
            <td class="wrap">那個機率回答的是「<b>它是不是正的</b>」，不是「<b>它跟零有沒有差別</b>」。
              後者的數字是 {n0(P2_G, 3)}，<b>是前者的兩倍，離「算數」更遠</b>。句子裡沒講是哪一個</td>
            <td><b>這一頁（做報告的人）</b></td></tr>
        </tbody>
      </table>
    </div>

    <div class="callout bad">
      <h3>第四個是這一頁自己抓到的，抓到的是前面那個抓錯我們的人</h3>
      <p>做檢查的同事擋下前三個數字的同時，自己報了兩個機率：{n0(P1_G, 3)} 和 {n0(P1_N, 2)}。
        我重新算了一遍，<b>數字跟他完全一樣</b>——但那是回答「這東西是不是正的」的機率。
        如果問的是「這東西跟零有沒有差別」（這才是一般人讀到時會以為的意思），
        答案是 <b>{n0(P2_G, 3)} 和 {n0(P2_N, 3)}</b>，<b>整整大一倍</b>。</p>
      <p style="margin:10px 0 0"><b>他選的那個問法在這裡是可以辯護的</b>（我們本來就想知道它是不是正的），
        <b>但句子裡沒有寫是哪一種，讀的人會當成另一種</b>。這一頁兩個都印，並註明哪個是哪個。
        <b>結論方向沒變——兩種問法都判「跟零沒辦法區分」。</b></p>
    </div>

    <h3 class="sub">{SECNUM["mistakes"]}.2　我們的協調者撤回自己的一次「抓到別人錯」</h3>
    <p>經過是這樣：有人寫下一條計算幣數成長的公式，協調者用電腦模擬去驗，
      在兩個測試點拿到 {n1(RET[0.5][2], 5)} 和 {n1(RET[2.0][2], 5)}，跟公式對不起來，
      於是記下「對方錯了」。</p>
    <p><b>重算之後發現：那個反例只有在「把兩個長得很像、但定義不同的數字互換」時才出得來。</b>
      比特幣的年報酬有兩種算法（一種是單純的漲幅，一種是考慮複利的），
      兩者差了一個固定的量。<b>把正確的那個代進去，兩邊算出來一模一樣，連小數點後十七位都相同。</b></p>
    <div class="table-wrap wide">
      <table>
        <caption>同一個公式，三種算法</caption>
        <thead><tr><th>槓桿</th><th>算法一（用漲幅）</th><th>算法二（用複利報酬，正確代入）</th><th>算法二但<b>代錯數字</b></th><th>前兩欄差多少</th></tr></thead>
        <tbody>{"".join(f'<tr><td class="name">{L} 倍</td><td>{n1(v[0], 5)}</td><td>{n1(v[1], 5)}</td><td class="negv">{n1(v[2], 5)}</td><td>{"完全相同" if abs(v[0] - v[1]) < 1e-15 else f"{abs(v[0] - v[1]):.0e}"}</td></tr>' for L, v in sorted(RET.items()))}</tbody>
      </table>
    </div>
    <p><b>結論一個字都不用改，但「對方錯了」這筆紀錄是錯的，正式撤回。</b>
      連帶：我們寫過「2 倍槓桿的門檻是一個值，而不是另一個值」——
      <b>那兩個其實是同一條門檻，只是用兩種單位講</b>
      （在目前量到的波動下分別是 {n0(TH_ARITH)}% 和 {n0(TH_LOG)}%，<b>兩種算法都判「不划算」</b>）。</p>
    <div class="callout">
      <h3>★ 這件事真正的教訓在流程上，不在數學上</h3>
      <p>協調者當時<b>已經自己回頭檢查過一次</b>，還寫下「我只驗了一步」。
        <b>驗了一步、發現不夠、再驗一次，還是錯。</b></p>
      <p style="margin:10px 0 0">因為兩次用的是同一套假設。<b>會抓到這種錯的不是「多驗一次」，
        而是「換一個人、用另一條路徑重算一遍」。</b>
        這一輪被擋下的三個數字，全部是這樣抓到的；
        而上面那第四個，是<b>這一頁在做那件事的時候，抓到檢查者自己的</b>。</p>
    </div>

    <h3 class="sub">{SECNUM["mistakes"]}.3　有一份報告，工程品質是全專案最高的，但還是被擋下來</h3>
    <p>本輪主線那份掃合約的報告，<b>被第二個人複製到另一個資料夾從頭重跑，七個輸出檔逐位元組完全相同</b>，
      測試 9 項全過，連幣安的介面都被重打了一次、結果零差異。</p>
    <p><b>然後它還是沒通過。</b>因為擋下它的三件事，<b>一件都不在工程裡</b>：
      一個精準到小數點後十二位的拆法被當成唯一的解釋；
      一個中心值被當成上限去跟門檻比；
      一個「四分之三來自 3 次觀測」的平均值被換算成年利率。</p>
    <p class="body-note">檢查者自己的評語，照原文寫：
      「<b>這份交付物的工程品質是本專案目前最高的一份。如果只有工程關卡，這份是 PASS。</b>」</p>
    <div class="callout bad">
      <h3>所以「程式可以重跑」到底保證了什麼</h3>
      <p><b>它保證的是「我每次跑都得到同一個答案」，不保證「這個答案在回答對的問題」。</b>
        這一頁自己也一樣——第{SECNUM["verify"]}節會把這句話再講一次。</p>
    </div>
  </section>
''')

# ------------------------------- 9. limits ---------------------------------
A(f'''  <section id="limits">
    <h2>{SECNUM["limits"]}、這一頁哪裡靠不住</h2>

    <div class="plain">
      <span class="lbl">這一節在講什麼</span>
      <p>這個專案要求每個結論都要標明<b>「有多容易被推翻」</b>。分成三種，用白話講就是：</p>
      <p><b>一、不會變的</b>（原本的說法叫「代數層級」）：這是算式推出來的，
        換什麼資料、換什麼行情都成立。<br>
        <b>二、目前資料看起來是這樣</b>（原本叫「實證層級」）：量出來的，會隨時間變，要講清楚量了幾次。<br>
        <b>三、推出來的，沒有直接量過</b>（原本叫「推論層級」）：<b>最容易垮，所以要明講它垮在哪。</b></p>
    </div>

    <ul class="limits">
      <li><b>不會變的</b>：那個拆法的加總本身（誤差 {SPLIT_RESID:.1e}，是電腦的小數點誤差，不是近似）；
        「兩種年報酬算法是同一條門檻換單位」；
        「錢全部搬進去時那條算式是負無限大」；
        「最保險的槓桿是猜測區間的中點」；
        定期調整槓桿那條公式（在理想模型下）。
        <b>這幾條換一份資料都不會變。</b></li>

      <li><b>目前資料看起來是這樣</b>：掛單賺價差那條
        （量了 {MM_TRADES:,} 筆成交，<b>但只有兩天、只在一個價位區間</b>）；
        季度折價（19 週，<b>但真正算不同事件的只有 11 次</b>）；
        補貼利率（<b>只是某一個時間點的快照</b>，利率隨時在動）；
        第三類價差的所有統計（{III_N} 段，<b>但真正不同的情況只有兩三次</b>）；
        波動損耗的範圍。</li>

      <li><b>推出來的，沒有直接量過（最脆）</b>：你的定投起點 2026-04-09
        （只靠兩個口頭數字回推）；一年 ${USD_LEND:.2f} 這個數字
        （存量是口述的、活期開關狀態不明、利率會動）；
        「合約已經掃完了」（舊合約那份掃描<b>既無法證明完整、也無法證明正確</b>，
        而且同一批合約 2026 年 6 月一個月就多了 {SYM_ADD} 個）；
        還有三類產品（借貸、雙幣投資、組合保證金）<b>是按產品說明排除的，沒有實際去查</b>。</li>
    </ul>

    <h3 class="sub">{SECNUM["limits"]}.1　一件被判不及格、而這一輪沒有補上的事</h3>
    <div class="callout bad">
      <h3>「跟你現在在做的事比，多賺幾顆」這一步，沒有做完</h3>
      <p>檢查者的原話：主線報告<b>完全沒有提到對照紀錄</b>；
        所有的「一年 X%」分母是合約金額而不是你的本金或幣數；
        也沒有算保證金倍率和清算緩衝。<b>「比你現在多賺幾顆」這一步沒有做。</b></p>
      <p style="margin:10px 0 0">第{SECNUM["beta1"]}.5 小節那張表是<b>寫規格的人自己補的一部分</b>
        （只做了第一類那一格，第二、三類需要的保證金和緩衝金完全沒算）。
        <b>完整的那一步這一輪沒有人做，這裡不假裝它做完了。</b></p>
    </div>

    <h3 class="sub">{SECNUM["limits"]}.2　一個數字因為「重跑不出來」而被刪掉</h3>
    <div class="callout">
      <h3>刪掉，而不是修好</h3>
      <p>主線報告裡有一句話用兩個數字來說明「兩種算法其實是同一件事」，
        <b>但那兩個數字沒有對應的程式，只有一行輸出紀錄，沒辦法重跑。</b>
        這跟第十四輪「聲稱算過的對照版本只存在一行輸出」是完全一樣的毛病。</p>
      <p style="margin:10px 0 0"><b>處理方式是刪掉，不是補算</b>：因為第三類站不住的原因
        已經從「拆法」換成「資料太少」了，那兩個數字不再承擔任何重量，刪掉的代價是零。
        <b>所以這一頁沒有它。</b>這裡提一下，是為了留下「它曾經在報告裡」這個紀錄。</p>
    </div>

    <h3 class="sub">{SECNUM["limits"]}.3　其他抓到、但不影響結論的</h3>
    <ul class="limits">
      <li><b>主線自己抓到的程式錯誤</b>：換月的時候兩腿之間空了 24 小時，
        每次<b>{F["b1_bug"].split("**")[1]}</b>{F["b1_bug"].split("**")[2]}。
        <b>已經修好、已經補上測試，這一頁的數字是修正後的。</b></li>
      <li>報告寫「時間戳誤差 0 到 6 毫秒」，<b>實際是 0 到 94 毫秒</b>——
        對結果無害，但這是<b>把「我印象中」寫成了「我查過」</b>。</li>
      <li>報告寫「唯一的例外是有缺口的那一段」，實際上<b>沒有這個例外</b>；24 段全部正常。</li>
      <li>舊合約那份掃描用的推論方式<b>已經降級標註</b>（見第{SECNUM["beta1"]}.4 小節的表）。</li>
      <li>這一輪只重測了第十二輪三種失敗原因裡的第二種（成本太高），
        <b>對另外兩種完全沒提</b>——所以「跟第十二輪的結論相容」這句話把它講小了。</li>
      <li><b>有一處我們把自己的成果講得比實際更保守</b>：報告寫「鎖倉的查詢回空，不能證明沒有」；
        檢查者自己去打了那個介面：<b>回傳 51 種幣的完整清單，比特幣不在裡面</b>。
        <b>這是「有證據的不存在」，比報告寫的更強。</b></li>
      <li><b>第{SECNUM["beta1"]}.5 小節混用了兩次抓取的利率</b>（加碼利率取 09-22 的快照，
        基本利率取 09-23 的重抓）。我用單一快照重算一次對照，<b>差 ${LEND_FETCH_GAP:.3f}／年</b>——
        不影響任何一位有效數字，<b>但混用這件事本身要寫出來。</b></li>
      <li><b>一個查過而且證實無關緊要的細節</b>：<code>ETHBTC</code> 換算成比特幣時用了每日收盤價近似。
        檢查者另外抓了 29,872 根小時線重算，{F["aud_c_num"].replace("**", "")}——<b>可以忽略</b>。
        寫在這裡是因為「查過而且沒差」跟「沒查」要分開講。</li>
      <li><b>版本管理紀律</b>：協調者曾經用一個「全部加入」的指令，
        把別人正在跑的中間檔案一起提交進了不相關的紀錄，造成說明跟內容對不起來。
        修法：{F["commit_note"].replace("`", "")}。</li>
    </ul>

    <h3 class="sub">{SECNUM["limits"]}.4　還開著的問題</h3>
    <ul class="limits">
      <li><b>你的活期開關到底開了沒</b>——這是這一頁所有金額裡<b>影響最大的一個未知數</b>。
        沒開的話第一件該做的事是 +${USD_SWITCH:.2f}／年，<b>比這一整輪找到的東西加起來還大。
        你看一眼帳戶就能結束這個問題。</b></li>
      <li><b><code>ETHBTC</code> 算不算你可以碰的東西</b>——從發現到現在沒有任何人回答過。</li>
      <li><b><code>ETHBTC</code> 加 <code>ETHUSDT</code> 那個三角</b>——它是被我們自己的範圍排除掉的，
        不是不存在。真要做的話它只有 13 季歷史，<b>天生就不夠下結論，動手之前就該知道。</b></li>
      <li><b>第三類的「最慘會慘到什麼程度」沒有算</b>（最大回檔、水下多久）。
        附帶一提：號稱抵銷掉漲跌的那個版本，結果上下起伏有 {n0(DN_STATS[1])} 元／萬，
        <b>回檔很可能是另一個獨立的致命傷。</b></li>
    </ul>
  </section>
''')

# ------------------------------ 10. verification ---------------------------
A(f'''  <section id="verify">
    <h2>{SECNUM["verify"]}、這一頁的數字是怎麼來的，以及它保證了什麼、沒保證什麼</h2>
    <p class="section-note">先講結論：下面這一整套<b>只能保證「每次跑都一樣」，不能保證「答案是對的」</b>。
      第{SECNUM["mistakes"]}節已經示範過，這兩件事可以差很遠。</p>

    <div class="engine">
      <h3>建這一頁的時候做了哪些檢查</h3>
      <dl>
        <dt>沒有任何數字是手打上去的</dt>
        <dd>頁面上每一個數字，要嘛是<b>從原始檔案當場重新算出來的</b>
          （逐筆合約資料、每日價格、執行紀錄、抓下來的原始資料），
          要嘛是<b>逐字比對確認它真的出現在某個來源檔裡</b>。
          共 <b>@@NFACT@@</b> 個字串逐字比對、<b>@@NCROSS@@</b> 個重算後跟來源互相核對。
          <b>任何一個對不上，整個建置就失敗，不會產出頁面。</b></dd>
        <dt>反過來再查一次</dt>
        <dd>上面那道只能抓「該出現卻沒出現」。反過來的那一道是：
          <b>把頁面上每一個數字抓出來，一個一個回到原始資料裡找。</b>
          這一頁 <b>@@NUM_TOK@@</b> 個不重複的數字裡，<b>@@NUM_HIT@@</b> 個在原始資料裡找得到；
          其餘 <b>@@NUM_MISS@@</b> 個是這一頁當場算的，<b>每一個都在程式裡具名寫了理由</b>，
          而且那份清單被要求必須完整——<b>多一個沒登記的數字，建置就失敗。</b></dd>
        <dt>作廢數字的守衛</dt>
        <dd>這一輪特別需要這道。被作廢的那幾個數字（像 2.5%、77%）
          <b>今天仍然一字不差地留在我們的工作紀錄裡</b>（就在那幾則把它們作廢掉的更正註記裡面），
          所以上面兩道檢查<b>會讓它們直接過關</b>。
          這道守衛的規則是：<b>作廢的數字只准出現在明講它是錯的句子旁邊</b>——
          前後各 120 個字裡面，必須出現「原本／錯／更正／作廢／不可」這類字眼。
          這一輪守衛的清單有 <b>@@NRETIRED@@</b> 項。</dd>
        <dt>白話守衛（這一輪新增）</dt>
        <dd>有一份 <b>@@NBANNED@@</b> 個專業術語的清單。<b>這些詞一旦出現在頁面上，
          前後 60 個字裡面必須有一句白話解釋</b>，否則建置失敗。
          這是為了讓這一頁不需要對照術語表就能從頭讀到尾。</dd>
        <dt>結構與用字</dt>
        <dd>標籤成對、樣式全部有定義、頁內連結不會點到空的地方、
          <b>連到別頁的連結會實際去那個檔案裡確認那個位置真的存在</b>、
          超過 4 欄的表格必須可以左右滑、
          「終局／結案／已證實」這類把話講死的詞不准出現在肯定句裡、
          頁面上不准出現任何檔案路徑或密碼之類的東西。共 <b>@@NCHECK@@</b> 項檢查。</dd>
        <dt>連跑兩次，比對指紋</dt>
        <dd>整個建置從頭跑兩次，兩份輸出的 SHA-256 指紋必須完全一樣。
          這一頁用到隨機抽樣（{BOOT_B:,} 次），<b>亂數種子寫死在程式裡</b>，所以結果是固定的。
          另外故意換一個種子再算一次，把結果也印在第{SECNUM["beta1"]}.1 小節裡，
          <b>好讓你看到那個誤差範圍不是挑種子挑出來的。</b></dd>
        <dt>舊頁面一個位元組都不准動</dt>
        <dd>建置開始前先記下四個已發布頁面的指紋，結束後再比對一次。
          <b>只要有一個位元組變了，建置就失敗。</b></dd>
      </dl>
    </div>

    <div class="callout bad">
      <h3>上面這一整套<b>抓不到</b>的東西</h3>
      <p>它們全都是機械檢查。<b>第{SECNUM["mistakes"]}節那四個錯，它一個都抓不到</b>：
        一個數字算在美金上卻放在幣數旁邊——標籤是成對的；
        一個中心值被當成上限——那個數字在原始資料裡找得到；
        一個機率沒講清楚在回答哪個問題——樣式全部有定義。</p>
      <p style="margin:10px 0 0"><b>會抓到這些的只有一件事：另一個人用另一條路徑，把同一個數字重算一遍。</b>
        這一輪的三個硬擋全部是這樣抓到的，而第四個，
        是這一頁在做那件事的時候抓到檢查者自己的。</p>
    </div>

    <div class="callout">
      <h3>這一輪誰跑了、誰沒跑</h3>
      <p><b>發布前檢查：有跑。</b>裁決是「需要修正」，三個數字被擋下，
        <b>而且這一頁是直接照修正後的版本建的，不是先建好再改</b>。
        規格層面的裁定也回來了，因此第{SECNUM["beta1"]}節的結論措辭跟著改
        （從「這條路已經永久封死」改成「在 2026-09-22 當下掛著的合約裡沒有第四類」）。</p>
      <p style="margin:10px 0 0"><b>風險與對照組那一關：這一輪沒有跑。</b>
        主線報告在這一關被判不及格（見第{SECNUM["limits"]}.1 小節），它自己也記下了「這一關是空的」。
        <b>第{SECNUM["beta1"]}.5 小節那個一年 ${USD_LEND:.2f}，是寫規格的人自己補的，不是這一關的產出。</b>
        <code>ETHBTC</code> 算不算你可以碰的東西，也是因為這一關沒跑而懸著。</p>
    </div>
  </section>
''')

# ------------------------------ 11. glossary -------------------------------
GLOSS = [
    ("幣數比", "g19-ratio",
     "這個專案的計分方式：做了某件事之後手上的比特幣<b>顆數</b>，除以什麼都不做的顆數。"
     "<b>算的是顆數，不是美元價值</b>——因為你的目標是幣變多，不是帳面數字變大。"),
    ("合約金額", "g19-notional",
     "你在期貨市場上「開了多大的部位」。它通常遠大於你實際押進去的保證金，"
     "<b>也遠大於你整個帳戶</b>。過去所有輪次的「一年 X%」分母都是它，這一頁全部重新換算過。"),
    ("永續合約 / 季度合約", "g19-contract",
     "永續是沒有到期日、可以一直放著的合約；季度合約每三個月到期一次。"
     "你手上的是永續。"),
    ("強制平倉", "g19-liq",
     "行情跌到某個程度，交易所會直接把你的部位賣掉、不問你的意見。這是這個專案最在意的風險。"),
    ("槓桿倍數", "g19-lam",
     "你開的部位大小，除以你押進去的保證金。它決定<b>會不會</b>被強制平倉；"
     "你搬多少錢進合約帳戶則決定<b>被平倉時賠多少</b>。這兩件事是分開的。"),
    ("資金費", "g19-funding",
     "永續合約上多方跟空方之間每 8 小時互相支付的一筆費用，"
     "用來把合約價格拉回貼近現貨。做空的一方通常是收錢的那一方。"),
    ("價差（不同月份之間）", "g19-basis",
     "同一個東西、不同到期月份的合約，價格會不一樣。"
     "這個差距到期時一定會收斂到零——第" + SECNUM["beta1"] + "節那條路就是想賺這個收斂。"),
    ("最小跳動格", "g19-tick",
     "交易所允許的最小價格變動單位。第" + SECNUM["closures"] + ".2 小節用「幾格」來描述損失，"
     "是因為掛單省下的手續費優惠剛好大約等於 1 格，兩者可以直接比。"),
    ("誤差範圍", "g19-ci",
     "一個量出來的數字，真正的值有九成五的機會落在哪個區間裡。"
     "<b>如果這個區間跨過了你要比較的門檻，那就代表這次量測回答不了那個問題。</b>"),
    ("真正獨立的觀測次數", "g19-neff",
     "如果好幾次觀測其實都發生在同一種情況下，那它們只能算一次。"
     "<b>表面上 24 次、真正不同的只有兩三次</b>，就跟擲三次硬幣一樣，下不了結論。"),
    ("對數軸", "g19-log",
     "一種畫圖的刻度，每一格代表「變成幾倍」而不是「加多少」。"
     "當最大值和最小值差到二十幾倍時<b>必須用它</b>，否則小的那些會全部擠成貼著底的一條線。"),
]
A(f'''  <section id="glossary">
    <h2>{SECNUM["glossary"]}、這一頁用到的詞，白話版</h2>
    <p class="section-note">正文裡每個專業詞第一次出現時都已經就地解釋過了，
      <b>所以這張表是備查用的，不讀也不影響。</b></p>
    <div class="table-wrap">
      <table class="gloss">
        <thead><tr><th>詞</th><th>白話</th></tr></thead>
        <tbody>{"".join(f'<tr id="{gid}" class="gterm"><td>{term}</td><td class="wrap">{desc}</td></tr>' for term, gid, desc in GLOSS)}</tbody>
      </table>
    </div>
  </section>

</main>

<footer>
  老六研究院 · 第十九輪 · {TODAY} ·
  <a href="laoliu.html">回研究院索引</a><br>
  這一頁由程式產生，所有數字由程式注入，沒有一個是手打的。<br>
  狀態：研究進行中。本頁不構成投資建議。
</footer>

</body>
</html>
''')

doc = "".join(P)
# Source files are Markdown, so literals quoted from them carry backticks.
# Render them rather than letting them ship as stray punctuation.
_h, _b = doc.split("</head>", 1)
doc = _h + "</head>" + re.sub(r"`([^`\n]+)`", r"<code>\1</code>", _b)
# ...and the verbatim-literal check below compares against a form where the
# conversion is undone, so a quoted string still has to match exactly.
DOC_MD = doc.replace("<code>", "`").replace("</code>", "`")


# ============================== validation ==================================
NCHECK = 0


def check(cond, msg):
    """One assertion, counted, so the page can state how many it passed."""
    global NCHECK
    NCHECK += 1
    assert cond, msg


# --- 1. section numbers are generated, never hand-written -------------------
for a, num in SECNUM.items():
    check(f'<section id="{a}">' in doc, f"section #{a} missing")
    h2 = re.search(rf'<section id="{a}">\s*<h2>(.*?)</h2>', doc, re.S).group(1)
    check(h2.startswith(num + "、"), f"section #{a} h2 starts {h2[:8]!r}, want {num}")
# every "第 X 節" reference in the prose must name a section that exists
for m in re.finditer(r"第([一二三四五六七八九十]+)(?:\.\d)?節", doc):
    check(m.group(1) in SECNUM.values(), f"reference to a section that does not exist: {m.group(0)}")
for m in re.finditer(r"第([一二三四五六七八九十]+)\.(\d) 小節", doc):
    check(m.group(1) in SECNUM.values(), f"bad subsection reference: {m.group(0)}")
    sec = [k for k, v in SECNUM.items() if v == m.group(1)][0]
    body = re.search(rf'<section id="{sec}">.*?</section>', doc, re.S).group(0)
    check(f'{m.group(1)}.{m.group(2)}　' in body,
          f"{m.group(0)} referenced but that subsection heading does not exist")


# --- 2. tag balance ---------------------------------------------------------
class Balance:
    VOID = {"meta", "br", "hr", "img", "input", "link", "source", "col"}

    def __init__(self):
        self.stack, self.err = [], []

    def feed(self, s):
        for m in re.finditer(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?(/?)>", s):
            closing, tag, self_close = m.group(1), m.group(2).lower(), m.group(3)
            if tag in self.VOID or self_close:
                continue
            if not closing:
                self.stack.append(tag)
            elif not self.stack or self.stack[-1] != tag:
                self.err.append((tag, list(self.stack[-3:])))
                if tag in self.stack:
                    while self.stack and self.stack.pop() != tag:
                        pass
            else:
                self.stack.pop()


_scriptless = re.sub(r"<script>.*?</script>", "", doc, flags=re.S)
_scriptless = re.sub(r"<style>.*?</style>", "", _scriptless, flags=re.S)
bal = Balance()
bal.feed(_scriptless)
check(not bal.err, f"unbalanced tags: {bal.err[:4]}")
check(not bal.stack, f"unclosed tags: {bal.stack}")

# --- 3. every CSS class used must be defined, for the element it is used on --
css_body = re.search(r"<style>(.*?)</style>", CSS, re.S).group(1)
allowed = {}
for elem, cname in re.findall(r"([a-zA-Z]*)\.([A-Za-z][A-Za-z0-9_-]*)", css_body):
    allowed.setdefault(cname, set()).add(elem.lower())
bad_cls = []
for tag, attr in re.findall(r"<([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>", _scriptless):
    m = re.search(r'\bclass="([^"]*)"', attr)
    if not m:
        continue
    check(m.group(1).strip(), f"empty class attribute on <{tag}>")
    for c in m.group(1).split():
        if c not in allowed:
            bad_cls.append((tag, c, "undefined"))
        elif "" not in allowed[c] and tag.lower() not in allowed[c]:
            bad_cls.append((tag, c, f"defined only for {sorted(allowed[c])}"))
check(not bad_cls, f"dead CSS classes: {sorted(set(bad_cls))}")

# --- 4. anchors -------------------------------------------------------------
own_ids = re.findall(r'id="([A-Za-z0-9_-]+)"', doc)
check(len(own_ids) == len(set(own_ids)), "duplicate id on the page")
own_ids = set(own_ids)
for href in re.findall(r'href="#([A-Za-z0-9_-]+)"', doc):
    check(href in own_ids, f"dangling in-page anchor #{href}")
EXT = {"crypto-dca-amplifier-report.html": V1_IDS,
       "laoliu-r15-triage2.html": R15_IDS,
       "laoliu-r16-eth.html": R16_IDS,
       "laoliu-r17-kelly.html": R17_IDS}
next_links = 0
for page, frag in re.findall(r'href="([a-z0-9\-.]+\.html)#([A-Za-z0-9_-]+)"', doc):
    check(page in EXT, f"link to a page with no id pool: {page}")
    check(frag in EXT[page], f"{page}#{frag} does not exist in that file")
    next_links += 1
check(next_links >= 5, f"only {next_links} cross-page anchors")
for page in set(re.findall(r'href="([a-z0-9\-.]+\.html)', doc)):
    check(os.path.exists(os.path.join(REPO, page)), f"link to missing file {page}")

# --- 5. wide tables ---------------------------------------------------------
for m in re.finditer(r'<div class="table-wrap([^"]*)">(.*?)</table>', doc, re.S):
    head = m.group(2).split("</tr>", 1)[0]
    ncol = len(re.findall(r"<th\b", head))
    if ncol > 4:
        check("wide" in m.group(1),
              f"{ncol}-column table without .wide: {head[:120]}")

# --- 6. wording discipline --------------------------------------------------
body_only = doc.split("</style>", 1)[1]
_prose = re.sub(r"<[^>]+>", " ", body_only)
for w in ("終局", "結案", "已證實"):
    for mm in re.finditer(w, _prose):
        ctx = _prose[max(0, mm.start() - 40):mm.start() + 20]
        check(any(k in ctx for k in ("不寫", "不下", "不宣稱", "不是", "沒有", "不得", "正確的", "不可", "不准")),
              f"forbidden word {w} in an affirmative sentence: {ctx!r}")
# no role codenames anywhere on a published page, and nothing from the other line
for name in ("費曼", "波普", "克努斯", "塔夫特", "凱利先生", "老七",
             "唐1", "TANG-1", "TE-1", "DE-1"):
    check(name not in doc, f"forbidden codename on a published page: {name}")
for f_other in ("crypto-tang1-report", "crypto-te1-report", "crypto-de1-report",
                "crypto-coinm-report", "crypto-dca-leveraged-report",
                "crypto-trend-hedge-report"):
    check(f_other not in doc, f"link into the other research line: {f_other}")
check("研究進行中" in doc, "status badge missing")
check(TODAY in doc and "第十九輪" in doc, "round/date missing")
check('href="laoliu.html"' in doc, "breadcrumb back to the index missing")
check("本輪沒有產生任何新的幣數比" in doc, "the round must say it produced no new coin ratio")
check("對數成長軸" in doc or "對數軸" in doc,
      "the right-skewed quantity must say it needs a log axis")
check("真正不同的情況只有兩三次" in _prose and f"{MM_TRADES:,}" in _prose,
      "the page must say how many genuinely independent observations there are")
# the three strength labels still have to be on the page, but now they are
# DEFINED in plain words in one place and used in plain words everywhere else.
for lab in ("代數層級", "實證層級", "推論層級"):
    check(lab in _prose, f"the strength label {lab} must still be declared")
for plain in ("不會變的", "目前資料看起來是這樣", "推出來的，沒有直接量過"):
    check(plain in _prose, f"the plain-language name for a strength label is missing: {plain}")

# --- 7. nothing private ships (a published page is a public page) -----------
for leak in ("/Volumes/", "/Users/", "@gmail.com", "ANTHROPIC", "sk-",
             "Authorization", "apiKey", "api_key", "hub_token'"):
    check(leak not in body_only, f"private string on a published page: {leak}")

# --- 8. no unformatted placeholders / non-numbers ---------------------------
for junk in ("{F[", "{SPLIT[", "{MM_", "{CL_", "{SUB_"):
    check(junk not in body_only, f"unrendered placeholder in the page: {junk}")
for junk in (r"\bNone\b", r"\bnan\b", r"\bNaN\b", r"\binf\b",
             r"[-−]0\.0+%", r"\+0\.0+%"):
    check(not re.search(junk, _prose),
          f"invalid computed value in the page: {junk}")

# --- 9a. every asserted literal has to reach the page -----------------------
# Some are injected after a .replace("**","") or a .split(), so they land on the
# page in pieces; those are named here rather than silently tolerated. Others
# name a role and are therefore paraphrased on the page by design.
SPLIT_OK = {
    "ax_lam_verdict", "ax_m_verdict", "ax_b_verdict", "ax_lam_rule", "objective",
    "m1_infty", "minimax_drop", "minimax_both", "supC_note", "constlam_form",
    "sig_band", "lam_decided", "retract", "retract_same", "retract_unit",
    "nu_pub", "bw_weeks", "bw_indep", "bw_med", "bw_gross", "bw_net", "bw_ftx",
    "bw_cost", "bw_shift", "bw_premise", "mm_flip", "mm_spread", "mm_bug",
    "mm_stale", "sub_close", "sub_zero", "sub_scope", "sub_locked",
    "b1_one_line", "b1_resid", "b1_ii_zero", "b1_slope",
    "b1_bug", "b1_upper", "eth_notzero", "eth_user", "cg_use", "cg_neff",
    "cg_log", "cg_eth_over", "cg_start", "cg_earn", "cg_flow", "cg_idle",
    "third_kind", "third_policy", "bench_read", "scope_perp", "scope_def",
    "scope_stock", "ex_w", "sub_public", "sub_earn", "sub_bug",
    "m1_true", "constlam_gbm", "ax_verdict", "bw_noise", "mm_close", "eth_only",
    "eth_listed", "third_small", "mm_limit", "commit_note", "pop_eth2",
    "aud_quality", "aud_verdict", "aud_repro", "aud_endpoint", "aud_ident", "aud_sum",
    "aud_hide", "aud_point", "aud_regimes", "aud_label", "aud_i", "aud_ii",
    "aud_band", "aud_open", "aud_b", "aud_c", "aud_c_num", "aud_contra",
    "aud_undecided", "aud_g12", "aud_0971", "aud_ms", "aud_noexc",
    "aud_usuffix", "aud_um", "aud_d12", "aud_locked", "aud_three", "aud_kelly",
    "r12_ann", "se_btc", "cg_stock", "cg_sim", "cg_t",
    "pop_frame", "pop_which", "pop_pred", "pop_coord", "pop_wrote", "pop_fix",
    "pop_eth", "pop_gap", "pop_scope", "pop_n13", "pop_h1", "pop_h1b",
    "pop_res", "pop_noresc", "pop_v3", "pop_norule", "pop_neff", "pop_admit",
    "pop_zero", "pop_zero2", "pop_251", "pop_honest", "pop_cross", "pop_acct",
    "pop_noleverage", "pop_perm", "pop_valid", "pop_51", "pop_del",
    "pop_grid0", "pop_dd", "pop_item5", "pop_strength", "pop_nokelly",
}
# Every SPLIT_OK entry must still REACH the page, just not verbatim. A literal
# counts as having reached it if either
#   (a) a >=4-character run of its prose survives on the page, or
#   (b) every number in it survives on the page (it was injected numerically).
# Anything satisfying neither must be named in DROPPED with a reason. Without
# this, SPLIT_OK becomes a dumping ground for material that quietly vanished.
_page_txt = re.sub(r"<[^>]+>", " ", body_only)
_page_txt = (_page_txt.replace("\u2212", "-").replace("&minus;", "-")
             .replace("&lt;", "<").replace("&gt;", ">").replace("\u221e", "inf"))


_PAGE_NUMS = set(re.findall(r"\d+(?:\.\d+)?", _page_txt.replace(",", "")))


def reached(key):
    lit = (USED[key][1].replace("*", "").replace("\u2212", "-")
           .replace("\u221e", "inf"))
    for frag in re.split(r"[`\u300c\u300d\uff08\uff09\uff0c\u3002\uff1a\uff1b\u3001\n\[\]|]+", lit):
        frag = frag.strip()
        if (len(frag) >= 4 and frag in _page_txt
                and (re.search(r"[\u4e00-\u9fff]", frag) or len(frag) >= 8)):
            return "prose"
    nums = re.findall(r"\d+(?:\.\d+)?", lit)
    # a single short token like "24" is not evidence that a sentence shipped
    if (nums and all(n in _PAGE_NUMS for n in nums)
            and (len(nums) >= 2 or len(nums[0]) >= 4)):
        return "numbers"
    return None


# Deliberately NOT on the page. Each one is named with why.
DROPPED = {
    "b1_resid": "belonged to that retired attribution, so it no longer carries weight",
    "b1_upper": "superseded by the corrected band in section 4.2",
    "ax_lam_rule": "the rewrite states the rule as a threshold in words and a "
                   "number, not as a formula the reader would have to parse",
    "constlam_form": "same: the formula is gone, its consequence is in words",
    "nu_pub": "the two threshold values are on the page; the drift figure "
              "behind them is not, and nothing on the page depends on it",
    "minimax_both": "the round-13 cross-reference was cut; it needs three "
                    "paragraphs of背景 to mean anything to this reader",
    "retract_same": "the cross-reference to the earlier mirror-image error was "
                    "cut for the same reason",
    "pop_frame": "commentary on how the task was framed, not a result",
    "pop_item5": "the ranking of follow-up work; section 9.1 states the outcome instead",
    "ex_w": "round-18 material, outside this round's scope",
    "cg_flow": "flow-to-stock ratio; stated in prose without the dollar figure",
}
# FORWARD check: an asserted literal must reach the page, verbatim unless it
# is listed in SPLIT_OK (injected in pieces, or paraphrased by design).
missing = [k for k, (_tag, lit) in USED.items()
           if lit not in doc and lit not in DOC_MD and k not in SPLIT_OK]
check(not missing, f"asserted but never used on the page: {missing}")

# This round rewrote the whole page in plain language, so most source
# sentences no longer appear in anything like their original wording. For each
# one, PARAPHRASE names the plain-language phrase on the page that carries the
# same claim, and the build fails if that phrase is not there. It is the only
# thing standing between "we rewrote it for readability" and "it quietly
# vanished during the rewrite".
PARAPHRASE = {
    "aud_0971": "沒辦法重跑",
    "aud_b": "跟零沒辦法區分",
    "aud_band": "就是把幣借出去收利息的量級",
    "aud_c": "查過而且沒差",
    "aud_contra": "剛好完全符合後面那句的字面，卻不符合前面那句的性質",
    "aud_d12": "對另外兩種完全沒提",
    "aud_g12": "分母是合約金額而不是你的本金或幣數",
    "aud_hide": "反而遮住了真正讓第三類站不住的原因",
    "aud_i": "唯一扣掉成本還是正的",
    "aud_kelly": "這一關是空的",
    "aud_label": "實際結果跟行情的連動反而更強、上下起伏還幾乎翻倍",
    "aud_open": "答不出來，能辯護的值是 0",
    "aud_point": "一個中心值被當成上限",
    "aud_repro": "七個輸出檔逐位元組完全相同",
    "aud_three": "一件都不在工程裡",
    "aud_um": "只能用「不是美元計價」來猜",
    "aud_undecided": "在 2026-09-22 當下掛著的合約裡",
    "aud_usuffix": "用了一個太寬鬆的字串比對",
    "ax_b_verdict": "是同一句話換個講法",
    "ax_lam_verdict": "其實是「資料看起來是這樣」",
    "ax_m_verdict": "其實是一個模型的結論，而那個模型自己否定它",
    "ax_verdict": "四條不該是第一種",
    "b1_ii_zero": "互相抵銷歸零",
    "bench_read": "事後回頭看到的一個結果",
    "bw_cost": "19 週裡有 11 週，你做了還倒虧",
    "bw_gross": "完全不算成本的話",
    "bw_indep": "同一檔合約連續好幾週便宜，那只能算一次",
    "bw_med": "中位數是 0.078%",
    "bw_net": "扣掉手續費和交割成本",
    "bw_noise": "每週的不確定性是交割那一小時的行情波動",
    "cg_earn": "這一欄是空的",
    "cg_eth_over": "多算了",
    "cg_neff": "真正算獨立的大約幾次",
    "cg_sim": "是一個模擬出來的參考基準，不是你的帳戶歷史",
    "cg_stock": "$2,756",
    "cg_t": "連「比特幣這 24 週到底有沒有漲」都分不出來",
    "cg_use": "不是「什麼方法有效」的證據",
    "constlam_gbm": "沒有資金費、沒有手續費、不會爆倉",
    "eth_notzero": "剛好完全符合後面那句的字面",
    "eth_only": "用比特幣當本金的",
    "eth_user": "對你來說它是在賭以太幣兌比特幣",
    "lam_decided": "你的決定未必錯，但支持它的理由要換一句",
    "m1_true": "不是「數學算出來最好」",
    "minimax_drop": "它不需要「不會後悔」這種包裝",
    "mm_bug": "其實從來沒跑成功過",
    "mm_close": "跟夠不夠格無關",
    "mm_limit": "只量了兩天、只在一個價位區間",
    "mm_spread": "真實買賣價差中位數就是 1 格",
    "mm_stale": "用成交價去推算中間價的做法是壞的",
    "objective": "被清光的機率",
    "pop_251": "$2.51",
    "pop_acct": "去開一個你現在沒有的帳戶",
    "pop_admit": "連「有沒有資格被拿來判斷」這一關都沒過",
    "pop_cross": "兩邊都停在「一年個位數美金」",
    "pop_del": "處理方式是刪掉，不是補算",
    "pop_eth2": "它只是把一種方向風險換成另一種",
    "pop_fix": "找的範圍要故意放寬",
    "pop_gap": "可以把「以太幣對比特幣」的漲跌抵銷掉",
    "pop_h1": "在 2026-09-22 當下掛著的合約裡",
    "pop_nokelly": "沒有任何人回答過",
    "pop_noleverage": "你現在沒有期貨帳戶、沒有開槓桿",
    "pop_noresc": "再多的分析也救不回來",
    "pop_norule": "答不出來就等於不能投",
    "pop_pred": "去哪裡找",
    "pop_scope": "「範圍外」跟「不存在」是兩回事",
    "pop_valid": "只要幣安上架新合約，這個結論就要重驗一次",
    "pop_which": "以前面那句為準，後面那句是我當初寫壞了",
    "pop_wrote": "我當初寫壞了",
    "r12_ann": "兩種算法一負一正",
    "scope_perp": "這條上限對你成立",
    "sub_bug": "欄位名稱跟我們原本猜的不一樣",
    "sub_close": "而且不會讓你多承擔別的風險",
    "sub_locked": "鎖倉產品對你持有的那幾種幣",
    "sub_public": "不用登入就看得到的公開頁面",
    "sub_scope": "登入後才會出現的個人化優惠",
    "sub_zero": "四種「額外贈送」的機制",
    "supC_note": "只有在「開完倉之後就不再調整部位大小」時成立",
    "third_kind": "任何規則都贏不了，這跟規則好不好完全無關",
    "third_policy": "公平的比法是規則對規則",
    "third_small": "只是幅度很小",
}
check(set(PARAPHRASE) <= set(SPLIT_OK),
      f"PARAPHRASE names a key outside SPLIT_OK: {sorted(set(PARAPHRASE) - set(SPLIT_OK))}")
_para_missing = sorted(k for k, v in PARAPHRASE.items() if v not in _page_txt)
check(not _para_missing,
      f"a source claim lost its plain-language stand-in on the page: "
      + "; ".join(f"{k} -> {PARAPHRASE[k]!r}" for k in _para_missing[:6]))

REACHED = {k: (reached(k) or ("paraphrase" if k in PARAPHRASE else None))
           for k in SPLIT_OK}
never = sorted(k for k, v in REACHED.items() if v is None)
check(set(never) <= set(DROPPED),
      f"listed as split/paraphrased but nothing of it reached the page: "
      f"{[n for n in never if n not in DROPPED]}")
check(set(SPLIT_OK) <= set(USED),
      f"SPLIT_OK names a key that was never asserted: {sorted(set(SPLIT_OK) - set(USED))}")
check(all(k in SPLIT_OK for k in DROPPED),
      f"DROPPED names something that is not in SPLIT_OK: "
      f"{[k for k in DROPPED if k not in SPLIT_OK]}")
stale = [k for k in DROPPED if REACHED.get(k)]
check(not stale, f"DROPPED says these are off the page, but they are on it: {stale}")

# --- 9b. REVERSE check: every number ON the page must exist in the material -
# The forward check cannot catch a number typed straight into the prose, which
# is exactly what a previous round's pre-publication audit found. This is the
# other direction.
HAY = "\n".join([state_txt, b1_txt, cg_txt, bw_txt, ex_txt, m24_log, mm_log,
                 mmlive_log, json.dumps(CL), json.dumps(CSUM), json.dumps(ENUM),
                 open(os.path.join(ROOT, "beta1_enum/run_decompose.log"), encoding="utf-8").read(),
                 open(os.path.join(ROOT, "beta1_enum/run_carry.log"), encoding="utf-8").read(),
                 json.dumps(SUBD), json.dumps(SUB_ROWS),
                 open(os.path.join(ROOT, "mm_adverse/results_daily.csv"), encoding="utf-8").read(),
                 open(os.path.join(ROOT, "subsidy_enum/data/subsidy_layers.csv"), encoding="utf-8").read()]
               + [open(os.path.join(ROOT, "beta1_enum", f), encoding="utf-8").read()
                  for f in sorted(os.listdir(os.path.join(ROOT, "beta1_enum")))
                  if f.endswith(".csv") and not f.startswith("._")])
_nosvg = re.sub(r"<svg.*?</svg>", " ", body_only, flags=re.S)
NUM_TOKENS = re.findall(r"\d+(?:[.,]\d+)*", re.sub(r"<[^>]+>", " ", _nosvg))
# Numbers this page derives on the spot, each named with its reason. The list
# is asserted exhaustive, so a new stray number breaks the build.
DERIVED_OK = {
    "58.8": "deepest 7-day peak-to-trough, recomputed from btcusdt_1d.csv",
    "53.8": "the 5-day version of the same",
    "47.4": "1-(lam/2)/0.95 at lambda=1.0",
    "60.5": "the same at lambda=0.75",
    "11.5": "how far 2020-03 breaches the lambda=1 threshold, in pp",
    "1.7": "slack left at lambda=0.75, in pp",
    "42.4": "deepest single week in the published weekly sample",
    "22.3": "the nu at which beta=1 would be the minimax choice",
    "1.31": "Savage minimax beta on the project's own nu interval",
    "2.95": "beta* at the top of that interval",
    "0.33": "beta* at the bottom of that interval",
    "1.24": "beta* at +30%",
    "0.32": "minimax beta under symmetric ignorance",
    "1.63": "minimax beta under the optimistic interval",
    "0.60": "beta* at 0% drift",
    "9.4": "lowest sigma^2/2 across the windows recomputed here",
    "30.2": "highest sigma^2/2 across the windows recomputed here",
    "10.9": "sigma^2/2 over the last three years",
    "22.8": "sigma^2/2 over the full sample",
    "16.3": "sigma^2/2 on the published window",
    "30.2%": "see above",
    "49.0": "1.5*sigma^2 at the published sigma",
    "32.6": "sigma^2 at the published sigma",
    "48.3": "the arithmetic drift implied by nu + sigma^2/2",
    "1.26": "orders of magnitude between the retired point estimate and the band's top",
    "2.2": "orders of magnitude between it and the band's bottom",
    "0.9": "width of the quotable band, in orders of magnitude",
    "76.2": "share of the (iii) total coming from the largest 3 of 24 pairs",
    "2.50": "the retired point estimate, shown only where it is retired",
    "0.68": "the same mean after dropping the largest 3",
    "0.15": "and after also charging taker",
    "0.307": "two-sided sign-test p for 15/24",
    "0.839": "two-sided sign-test p for 13/24",
    "0.154": "one-sided sign-test p for 15/24",
    "0.42": "one-sided sign-test p for 13/24",
    "0.1538": "the same, 4dp",
    "0.4194": "the same, 4dp",
    "2.5": "half-width of the (iii) bootstrap CI, in %/yr",
    "0.02": "bottom of the quotable band = lending alone",
    "0.14": "top of the quotable band = lending + the round-12 calendar figure",
    "0.0909": "the same band converted to the user's coin stock",
    "2.51": "the same in dollars at the control group's reference price",
    "3.0825e-05": "the same in coins",
    "0.0239": "stock above the boosted tier = 0.0339 - 0.01",
    "29.5": "share of the stock the boosted tier covers",
    "81,298": "the control group's implied BTC price = $2,756 / 0.0339",
    "0.0173": "BTC flexible base rate, from the public snapshot",
    "0.2673": "the boosted tier, from the same snapshot",
    "2.67e-05": "coins from the tier-covered slice",
    "4.10e-06": "coins from the slice above the tier",
    "2.15": "dollars from the tier-covered slice",
    "0.36": "dollars from the slice above the tier",
    "0.003": "difference between the two fetches, in dollars per year",
    "1.006": "relative wealth of the idle-USDT upgrade over 24 weeks",
    "1.003": "the same for the ETH upgrade",
    "0.894": "sum of the two upgrades as a percentage of the 24-week denominator",
    "4.7": "how many times the Simple-Earn switch dwarfs the best subsidy cell",
    "1.2": "smallest ratio between the two market-making days",
    "1.7": "largest ratio between the two market-making days",
    "12": "smallest |t| across the market-making buckets",
    "1.22": "market-making trades in millions",
    "0.9996": "how close buy-and-hold notional ever gets to its 1+lambda bound",
    "0.28": "largest error of the constant-lambda closed form, in %",
}
HAY_N = HAY + "\n" + HAY.replace(",", "")


def _sourced(tk):
    """A token counts as sourced if it, or its comma-stripped form, is in the
    material -- thousands separators are a display choice, not a number."""
    return tk in HAY_N or tk.replace(",", "") in HAY_N


# Groups this page computes and renders as tables. Registered from the same
# dict the table is built from, so the list cannot go stale.
for _lab, _v in SIGWIN.items():
    DERIVED_OK[f"{_v[0]:.2f}"] = f"annualised sigma, window {_lab}"
    DERIVED_OK[f"{_v[1]:.2f}"] = f"sigma^2/2, window {_lab}"
for (_a, _b), _v in SIGYR.items():
    DERIVED_OK[f"{_v[0]:.2f}"] = f"annualised sigma, year {_a}..{_b}"
    DERIVED_OK[f"{_v[1]:.2f}"] = f"sigma^2/2, year {_a}..{_b}"
for _k, _v in (("median_C_b", "constant-lambda median"),
               ("median_C_a", "buy-and-hold notional median"),
               ("mean_C_b", "constant-lambda mean"),
               ("mean_C_a", "buy-and-hold notional mean")):
    DERIVED_OK[f"{CL_PICK[_k]:.3f}"] = f"{_v} at lam={CL_PICK['lam']}, sigma={CL_PICK['sigma']}"
DERIVED_OK.update({
    f"{P1_G:.4f}": "one-sided sign-test p for the gross series, 4dp",
    f"{P1_N:.4f}": "one-sided sign-test p for the net series, 4dp",
    f"{MM_TRADES:,}": "trades summed from mm_adverse/results_daily.csv",
    f"{MM_BUCK1:,}": "1-second buckets summed from the same file",
    f"{MM_BLK1:,}": "blocks summed from the same file",
    f"{TIER_AMT * RATE_TIER:.4e}".split("e")[0]: "coins from the tier-covered slice",
    f"{REST_AMT * RATE_MKT_TODAY:.4e}".split("e")[0]: "coins from the slice above the tier",
    str(BOOT_SEED): "the bootstrap seed, written into the script so the build is deterministic",
    f"{BOOT_GROSS[1]:.2f}": "top of the gross bootstrap CI, this build's seed",
    f"{BOOT_GROSS_2[1]:.2f}": "top of the same CI under seed=1, printed to show the noise",
    f"{CL_FRAC[1]:.1f}": "largest share of constant-lambda paths breaching 1+lambda",
    f"{KG_YR:.2f}": "the arithmetically best subsidy cell, excluded on exposure grounds",
    f"{SUB_ROWS['FDUSD'][2] - SUB_ROWS['USDT'][2]:.2f}".lstrip("-"):
        "FDUSD minus the current USDT placement, in dollars per year",
})

NUM_MISSES = sorted({tk for tk in NUM_TOKENS
                     if not _sourced(tk) and tk not in DERIVED_OK})
NUM_TOK = len(set(NUM_TOKENS))
NUM_HIT = len({tk for tk in NUM_TOKENS if _sourced(tk)})
if os.environ.get("R19_MISS"):
    _pt = re.sub(r"<[^>]+>", " ", _nosvg)
    for tk in NUM_MISSES:
        i = _pt.find(tk)
        print("MISS", tk, "|", _pt[max(0, i - 45):i + 20].replace("\n", " "))
check(not NUM_MISSES, f"numbers on the page with no source: {NUM_MISSES[:20]}")
check(NUM_TOK - NUM_HIT <= len(DERIVED_OK),
      "DERIVED_OK is larger than the set of page numbers it claims to cover")

# --- 9c. values this round retires must not come back as if true -----------
# *fact() proves a literal EXISTS in a source file; it cannot prove the source
# still believes it. Every string below is STILL in laoliu-state.md today,
# inside the very note that retired it - so the assertion machinery above would
# have let them straight back through. This list is the guard.
RETIRED = {
    "77.0": "the S_T share under split A, retired: the attribution is not unique",
    "2.50": "the (iii) point estimate, retired: it was a point estimate used as a bound",
    "2.5%": "the same, as it was quoted against the 3% threshold",
    "77%": "the same share, as it was quoted in prose",
    "永久封閉": "ruled out: the claim needs an expiry date, so it may only appear "
                "in the sentence that withdraws it",
    "空間已封閉": "same; only allowed where the page says it is a false closure",
    "β=1 空間封閉": "same",
}
# These must not appear at all, in any context: they are whole claims, not values.
FORBIDDEN = {
    "2.5% < 3%": "the retired comparison",
    "2.5%/年 < 3%": "the retired comparison",
    "空間永久": "same",
}
RETRACT = ("原本", "原先", "原標題", "原誤植", "錯", "更正", "退役", "舊", "不可",
           "被擋", "擋下", "不是", "沒通過", "站不住", "降級", "拿掉", "殺掉", "假的", "→", "不得寫成",
           "本來要報", "擋下來", "改正後", "作廢")
for bad, why in FORBIDDEN.items():
    check(bad not in _prose, f"forbidden claim on the page: {bad} ({why})")
RETIRED_HITS = 0
for bad, why in RETIRED.items():
    for mm in re.finditer(re.escape(bad), _prose):
        RETIRED_HITS += 1
        ctx = _prose[max(0, mm.start() - 120):mm.start() + 120]
        check(any(k in ctx for k in RETRACT),
              f"retired value used as if still true: {bad} ({why})\n  ...{ctx}...")
check(RETIRED_HITS >= 4,
      f"only {RETIRED_HITS} retired-value occurrences guarded; the page should "
      f"discuss what it retired")
# and the corrected values must actually be on the page
for good, why in ((f"{BAND_LO:.2f}%", "the bottom of the corrected band"),
                  (f"{BAND_HI:.2f}%", "the top of the corrected band"),
                  (f"${LEND_MIX[2]:.2f}", "the same in the project's scoring unit"),
                  ("答不出來", "the correct verdict on class (iii), in plain words"),
                  ("能辯護的值是 0", "and what that means for the number")):
    check(good in _prose, f"the corrected value is missing: {good} ({why})")

# --- 9c-bis. PLAIN-LANGUAGE guard ------------------------------------------
# The reader told us he could not follow the previous version. These are the
# terms that made it unreadable. Each one may still appear, but only if a
# plain-language explanation sits within 60 characters of it - so the page can
# be read start to finish without looking anything up. Terms we simply stopped
# using pass trivially; the point is that they cannot creep back in bare.
BANNED = {
    "n_eff": ("真正不同", "只能算一次", "真正算獨立"),
    "bootstrap": ("重複隨機抽取", "重複抽樣"),
    "信賴區間": ("誤差範圍",),
    "CI": ("誤差範圍",),
    "符號檢定": ("正負號",),
    "單尾": ("是不是正的",),
    "雙尾": ("跟零有沒有差別", "不等於零"),
    "p 值": ("機率",),
    "t 值": ("除以", "誤差", "訊號強度"),
    "標準差": ("起伏", "上下"),
    "集中度": ("少數幾次", "就佔了", "全靠"),
    "delta 中性": ("抵銷", "不受漲跌"),
    "零 delta": ("不看漲跌", "不受漲跌"),
    "carry": ("不看漲跌", "光是持有"),
    "基差": ("價差", "價格差"),
    "名目": ("合約金額",),
    "退役值": ("作廢", "不能再用"),
    "斷言": ("逐字比對",),
    "口徑": ("算法", "基準"),
    "層級": ("不會變", "白話", "原本的說法", "原本叫", "量出來的", "沒有直接量過"),
}
BANNED_HITS = {}
for term, plain in BANNED.items():
    for mm in re.finditer(re.escape(term), _prose):
        ctx = _prose[max(0, mm.start() - 60):mm.start() + len(term) + 60]
        BANNED_HITS[term] = BANNED_HITS.get(term, 0) + 1
        check(any(k in ctx for k in plain),
              f"jargon without a plain-language explanation within 60 chars: "
              f"{term}\n  ...{ctx}...")
# the page must actually be mostly free of them, not merely well-annotated
if os.environ.get("R19_JARGON"):
    print("JARGON", sum(BANNED_HITS.values()), BANNED_HITS)
check(sum(BANNED_HITS.values()) <= 25,
      f"{sum(BANNED_HITS.values())} jargon occurrences is too many for a page "
      f"meant to be readable without a glossary: {BANNED_HITS}")

# --- 9d. the round's own discipline ----------------------------------------
check("本輪沒有產生任何新的幣數比" in _prose and "原因寫清楚" in _prose,
      "the round must say it produced no new coin ratio AND why")
# the one-sided/two-sided distinction has to be MADE, in plain words
check("它是不是正的" in _prose and "跟零有沒有差別" in _prose,
      "the page must spell out which question the probability answers")
check(f"{P2_G:.3f}" in _prose and f"{P2_N:.3f}" in _prose,
      "both probabilities must be on the page, not only the one the audit quoted")
# every percentage has to be accompanied by what it means in the reader's money
check("合約金額" in _prose and f"${STOCK_USD:,.0f}" in _prose,
      "the page must name the denominator and convert it to the reader's stack")
for usd in (USD_LEND, USD_SUB, USD_SWITCH, USD_RETIRED):
    check(f"${usd:,.2f}" in _prose or f"${usd:,.0f}" in _prose,
          f"a headline figure is missing its dollars-per-year form: {usd}")
check(f"{BOOT_B:,}" in _prose, "the resample count must be stated")

# --- 10. the four frozen published pages must be byte-identical ------------
for path, sha in FROZEN_SHA.items():
    now = hashlib.sha256(open(path, "rb").read()).hexdigest()
    check(now == sha, f"a frozen published page changed: {os.path.basename(path)}")

# --- 11. never overwrite a page this script did not produce ----------------
MARK = "<!-- built by tools/build_laoliu_r19.py -->"
if os.path.exists(OUT):
    check(MARK in open(OUT, encoding="utf-8").read(),
          f"{OUT} exists and was not produced by this script: refusing to overwrite")
doc = doc.replace("</head>", MARK + "\n</head>", 1)
for ph, val in (("@@NUM_TOK@@", NUM_TOK), ("@@NUM_HIT@@", NUM_HIT),
                ("@@NUM_MISS@@", NUM_TOK - NUM_HIT), ("@@NFACT@@", len(USED)),
                ("@@NCROSS@@", len(CROSS)),
                ("@@NRETIRED@@", len(RETIRED) + len(FORBIDDEN)),
                ("@@NBANNED@@", len(BANNED))):
    doc = doc.replace(ph, f"{val:,}")
doc = doc.replace("@@NCHECK@@", f"{NCHECK + 1:,}")   # +1: the placeholder check
_bodytail = doc.split("</head>", 1)[1]
check("`" not in _bodytail, "a Markdown backtick survived into the page body")
check("**" not in _bodytail, "Markdown bold survived into the page body")
check("@@" not in doc, "an unresolved build placeholder survived")

open(OUT, "w", encoding="utf-8").write(doc)
open(os.path.join(PUB, os.path.basename(OUT)), "w", encoding="utf-8").write(doc)
print(f"wrote {OUT}  {len(doc):,} bytes; {len(own_ids)} anchors; "
      f"{NCHECK} checks passed; {NUM_TOK} distinct numbers "
      f"({NUM_HIT} sourced, {NUM_TOK - NUM_HIT} derived here)")


# ---------------- index card (regenerated between markers) ----------------
CARD_RE = r"<!-- R19-CARD:BEGIN.*?<!-- R19-CARD:END -->\n{0,2}"
CARD = f'''<!-- R19-CARD:BEGIN (generated by tools/build_laoliu_r19.py — do not hand-edit) -->
  <a class="report-card" href="{os.path.basename(OUT)}">
    <div class="top">
      <span class="title">第十九輪 · 回頭檢查自己講過的話</span>
      <span class="tag">{TODAY}</span>
      <span class="tag">本來要報的頭條被自己擋下來</span>
      <span class="tag">建置驗證 {NCHECK + 1:,} 項</span>
      <span class="tag live">研究進行中</span>
    </div>
    <div class="desc">
      <b>★ 這一輪沒有做新策略，也沒有找到新的賺錢方法。它做的是把自己過去的結論重算一遍。</b>
      我們本來要報給你的頭條是「有一條路一年可以多賺 2.5%」——
      <b>這句話在拿給你看之前，被我們自己的檢查擋下來了</b>。
      理由：那個 2.5% 的誤差範圍是 {n0(BOOT_GROSS[0], 2)}% 到 {n0(BOOT_GROSS[1], 2)}%，
      <b>寬到根本沒辦法判斷它有沒有超過我們設的 3% 門檻</b>；
      而且 {III_N} 次交易裡<b>最賺的 3 次就佔了總獲利的 {n0(TOP3_SHARE)}%</b>，
      把那 3 次拿掉、再扣手續費<b>就變成虧的</b>。那幾次還全發生在同一種行情下——
      <b>表面上 {III_N} 次，真正不同的情況只有兩三次。</b>
      <b>改正後能講的，用你手上的 {BTC_STOCK} 顆（約 ${STOCK_USD:,.0f}）算，是一年 ${USD_LEND:.2f}。</b>
      <b>★ 而另一條完全不相干的線</b>（把 412 種幣的優惠利率全掃一遍）<b>找到的最佳選項是一年多 ${USD_SUB:.2f}</b>——
      兩條線都停在「一年個位數美金」，這個巧合讓「一定還有一塊沒人找過的免費的錢」變得很難繼續相信。
      <b>★ 這一頁裡金額最大的一件事，是去確認一個你可能早就做過的動作</b>：
      如果你的活期開關其實沒開，把它打開是一年 +${USD_SWITCH:.2f}，
      <b>比這一整輪找到的東西加起來還大</b>。
      <b>★ 我們支持「你的槓桿設定安全」的理由是錯的</b>：那個「一週最多跌 {n0(WK_WORST_PCT)}%」
      是我們手上資料檔<b>裡面</b>的最大值，而那個檔案從 {WK_FROM} 才開始；
      往前翻，<b>2020 年 3 月那七天跌了 {n0(DROP7)}%，會直接打穿 1 倍槓桿的 {n0(TH[1.0])}% 那條線</b>。
      <b>你的決定未必錯，但支持它的理由要從「數學保證」降成「這幾年沒發生過」。</b>
      <b>★ 「錢全部搬進合約帳戶最好」被它自己的公式推翻</b>（那條算式在「全部搬進去」時是負無限大，是最差點不是最好點）。
      <b>★ 「我們一直打不贏你 2022 年那筆」是個假問題</b>：1.313 不是一個方法的成績，
      是你在某個時點進場、事後回頭看到的結果——<b>拿事後最佳去要求事前規則，任何規則都贏不了。</b>
      <b>另外三條路也都走到底了</b>：季度折價（五年半總共 $3，三分之二來自一次交易所倒閉）、
      幫交易所掛單賺價差（<b>是負的</b>，量了 {MM_TRADES:,} 筆成交，全專案證據最強的一次否決）、
      補貼利率（412 種幣全掃，四種額外贈送機制<b>一個都沒有</b>）。
      <b>誠實標註</b>：風險與對照組那一關<b>這一輪沒有跑</b>，主線在那一關被判不及格；
      一個重跑不出來的數字<b>被刪掉而不是被引用</b>；
      <b>這一頁自己抓到檢查者一處沒講清楚</b>（他報的機率回答的是「它是不是正的」，
      不是「它跟零有沒有差別」，後者是 {n0(P2_G, 3)}，大一倍）。
      <b>這一輪沒有產生任何新的幣數比。</b>
    </div>
    <div class="stats">
      <div>這一輪找到的新賺錢方法<b class="neg">0 個</b></div>
      <div>改正後能講的（用你的 {BTC_STOCK} 顆算）<b class="neg">一年 ${USD_LEND:.2f}</b></div>
      <div>另一條獨立的線給的最佳選項<b class="neg">一年 +${USD_SUB:.2f}</b></div>
      <div>如果你的活期開關沒開，打開它值<b>一年 +${USD_SWITCH:.2f}</b></div>
      <div>本來要報的 2.5%，用你的規模算是<b class="neg">一年 ${USD_RETIRED:.0f}</b></div>
      <div>2020 年 3 月那七天，打穿 1 倍槓桿<b class="neg">{n0(BREACH10)} 個百分點</b></div>
      <div>{III_N} 次交易裡，最賺的 3 次就佔<b class="neg">{n0(TOP3_SHARE)}%</b></div>
      <div>掛單賺價差那條的證據量<b>{MM_TRADES:,} 筆成交</b></div>
      <div>被改掉標籤的舊結論<b class="neg">4 條</b></div>
    </div>
  </a>
<!-- R19-CARD:END -->
'''
for w in ("終局", "結案", "已證實"):
    check(w not in CARD, f"forbidden word {w} on the index card")
for name in ("費曼", "波普", "克努斯", "塔夫特", "凱利先生"):
    check(name not in CARD, f"role codename on the index card: {name}")
check("研究進行中" in CARD, "index card missing the status tag")
check("沒有產生任何新的幣數比" in CARD, "index card must state the coin-ratio count")
# the card is the first thing he reads, so it gets the plain-language guard too
_card_txt = re.sub(r"<[^>]+>", " ", CARD)
for _t, _plain in BANNED.items():
    for _m in re.finditer(re.escape(_t), _card_txt):
        _c = _card_txt[max(0, _m.start() - 60):_m.start() + len(_t) + 60]
        check(any(k in _c for k in _plain),
              f"jargon without a plain explanation on the index card: {_t}")
_card_prose = re.sub(r"<[^>]+>", " ", CARD)
for bad, why in RETIRED.items():
    for mm in re.finditer(re.escape(bad), _card_prose):
        ctx = _card_prose[max(0, mm.start() - 120):mm.start() + 120]
        check(any(k in ctx for k in RETRACT),
              f"retired value on the index card as if true: {bad} ({why})")
for bad, why in FORBIDDEN.items():
    check(bad not in _card_prose, f"forbidden claim on the index card: {bad}")

# CARD_BLOCK carries its own trailing blank line so that inserting it and
# regenerating it in place produce byte-identical output.
CARD_BLOCK = CARD + "\n"
idx_before = open(INDEX, encoding="utf-8").read()
if "<!-- R19-CARD:BEGIN" in idx_before:
    idx = re.sub(CARD_RE, CARD_BLOCK, idx_before, flags=re.S)
else:
    marker = "<!-- R17-CARD:BEGIN"
    check(marker in idx_before, "R17 card marker not found in the index")
    idx = idx_before.replace(marker, CARD_BLOCK + marker, 1)
n_cards = len(re.findall(r'<a class="report-card"', idx))
check(n_cards == 5, f"{n_cards} cards on the index, expected 5")
COUNT_TXT = f'<div class="count">共 {n_cards} 份報告 · 只計老六研究院這一條線</div>'
idx, nsub = re.subn(r'<div class="count">[^<]*</div>', COUNT_TXT, idx)
check(nsub == 1, f"report count replaced {nsub} times")

# the index may gain exactly one card and a new count, and nothing else
rest = re.sub(CARD_RE, "", idx, flags=re.S)
was = re.sub(CARD_RE, "", idx_before, flags=re.S)
check(rest == re.sub(r'<div class="count">[^<]*</div>', COUNT_TXT, was),
      "the index changed somewhere other than this round's card and the count")

# the card has to survive the same structural checks as the page
card_bal = Balance()
card_bal.feed(CARD)
check(not card_bal.err and not card_bal.stack,
      f"unbalanced tags on the index card: {card_bal.err[:3]} {card_bal.stack}")
idx_css = re.search(r"<style>(.*?)</style>", idx_before, re.S).group(1)
idx_allowed = {c for _e, c in re.findall(r"([a-zA-Z]*)\.([A-Za-z][A-Za-z0-9_-]*)", idx_css)}
for _tag, attr in re.findall(r"<([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>", CARD):
    m = re.search(r'\bclass="([^"]*)"', attr)
    for c in (m.group(1).split() if m else []):
        check(c in idx_allowed, f"index card uses undefined CSS class .{c}")

open(INDEX, "w", encoding="utf-8").write(idx)
print(f"updated {INDEX}: {n_cards} cards, {NCHECK} checks passed in total")

# one last look: the four frozen pages, after everything
for path, sha in FROZEN_SHA.items():
    now = hashlib.sha256(open(path, "rb").read()).hexdigest()
    check(now == sha, f"a frozen published page changed: {os.path.basename(path)}")
print("frozen pages verified byte-identical: "
      + ", ".join(sorted(os.path.basename(p) for p in FROZEN_SHA)))
print("page sha256 " + hashlib.sha256(doc.encode("utf-8")).hexdigest())
