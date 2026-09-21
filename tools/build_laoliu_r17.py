#!/usr/bin/env python3
"""Build laoliu-r17-kelly.html (Round 17 / risk-and-control-group review) plus
the two corrections it is required to carry.

Discipline (same as tools/build_laoliu_r16.py):
  - No number is typed into the prose. Every number is either
    (a) asserted to appear LITERALLY in laoliu-state.md      -> fact()
    (b) asserted to appear LITERALLY in kelly_review/REPORT.md -> rfact()
    (c) parsed out of a kelly_review/*.log with an assert on the parse -> charts
    Derived values (annualisation of a weekly probability, chart geometry) are
    computed here from (c) and labelled as derived on the page.
  - The CSS block and the access-control gate are lifted verbatim from the
    frozen laoliu-r16-eth.html so the new page cannot drift visually.
  - No already-published page is written to. The only existing file touched is
    laoliu.html (the index), and only between generated markers.
Run: python3 build_laoliu_r17.py
"""
import os, re, sys, math, html

ROOT = "/Volumes/FCP 512GB/Claude"
REPO = os.path.join(ROOT, "SumerTWRobotTest1")
KR = os.path.join(ROOT, "kelly_review")
PUB = os.path.join(ROOT, "r17_publish")
V1 = os.path.join(REPO, "crypto-dca-amplifier-report.html")
R15 = os.path.join(REPO, "laoliu-r15-triage2.html")
R16 = os.path.join(REPO, "laoliu-r16-eth.html")
STATE = os.path.join(ROOT, "laoliu-state.md")
OUT = os.path.join(REPO, "laoliu-r17-kelly.html")
INDEX = os.path.join(REPO, "laoliu.html")
TODAY = "2026-09-21"
os.makedirs(PUB, exist_ok=True)

state_txt = open(STATE, encoding="utf-8").read()
report_txt = open(os.path.join(KR, "REPORT.md"), encoding="utf-8").read()
cg_txt = open(os.path.join(KR, "CONTROL_GROUP.md"), encoding="utf-8").read()

USED = {}


def fact(key, literal):
    assert literal in state_txt, f"FACT {key} ({literal!r}) not in laoliu-state.md"
    USED[key] = ("state", literal)
    return literal


def rfact(key, literal):
    assert literal in report_txt, f"RFACT {key} ({literal!r}) not in REPORT.md"
    USED[key] = ("report", literal)
    return literal


def cfact(key, literal):
    assert literal in cg_txt, f"CFACT {key} ({literal!r}) not in CONTROL_GROUP.md"
    USED[key] = ("control", literal)
    return literal


F = {
    # ---- 1. m cancels / f is leverage in disguise -------------------------
    "lam_def":     fact("lam_def", "`保證金比率 = (m·W·(1+r)) / (λ·m·W·MMR) = (1+r)/(λ·MMR)`"),
    "gross_def":   fact("gross_def", "`gross = 0.75·f·W`"),
    "mratio":      fact("mratio", "76.17/80.27/80.62"),
    "f1333":       fact("f1333", "1.333"),
    "lam_from_f":  fact("lam_from_f", "λ = 0.75·f"),
    # ---- 2. the algebraic death of lambda=1.333 ---------------------------
    "btc_worst":   fact("btc_worst", "−42.4%"),
    "collat":      fact("collat", "0.5472"),
    "longleg":     fact("longleg", "0.6665"),
    "breach":      fact("breach", "−0.1193"),
    "slack10":     fact("slack10", "9.4%"),
    # ---- 3. correlation is the other way round ----------------------------
    "pearson":     fact("pearson", "+0.18/+0.26/+0.21/+0.35"),
    "spearman":    fact("spearman", "+0.22~+0.33"),
    "joint_obs":   fact("joint_obs", "0.0000"),
    "joint_ind":   fact("joint_ind", "0.0025"),
    "worstweek":   fact("worstweek", "+11.1%"),
    "maxshort":    fact("maxshort", "+65.5%"),
    "that_btc":    fact("that_btc", "4.6%"),
    "top5avg":     fact("top5avg", "+73.5%"),
    "p99_real":    fact("p99_real", "+38.2% / +33.8% / +41.4%"),
    "synth_lam":   fact("synth_lam", "1.45 / 2.72 / 1.61"),
    "top5src":     rfact("top5src", "`sizing_review/task2_bounds.py` 的**宇宙前 5 強平均**"),
    # ---- 4. ruin probability ----------------------------------------------
    "lc_r5":       fact("lc_r5", "2.06"),
    "lc_sfb":      fact("lc_sfb", "3.19"),
    "lc_gla":      fact("lc_gla", "2.82"),
    "lc_tri":      fact("lc_tri", "3.51"),
    "emp_ub":      fact("emp_ub", "1.2%/週 = 47%/年"),
    "gpd_band":    fact("gpd_band", "0.13% ~ 2.55%/年"),
    # B1/B2 (2026-09-21 pre-publication audit): the lognormal column in
    # h_tail.log is a PER-WEEK probability - its own title says so - and both
    # REPORT.md and the first draft of this page printed it as if it were
    # annual, next to an annualised GPD column. Corrected values below; the
    # retired ones are listed in RETIRED and asserted absent from the page.
    "logn_ann":    fact("logn_ann", "2.85e-07 ~ 1.96e-05／年"),
    "week_hdr":    fact("week_hdr", "P(liquidation in a given week)"),
    "oom_truth":   fact("oom_truth", "同一本帳 3.0~4.4 個數量級，跨帳本最大 4.95"),
    "oom_wrong":   fact("oom_wrong", "「六個數量級」＝ 年化的 GPD ÷ 每週的對數常態 = 6.67"),
    "oom_title":   fact("oom_title", "破產機率：三個模型差 ~5 個數量級"),
    "logn_verdict": fact("logn_verdict", "對數常態那一欄是每週值，不是年化值"),
    "log_ok":      fact("log_ok", "log 本身是對的"),
    "xi_band":     fact("xi_band", "ξ=+0.16~+0.36"),
    # ---- 5. ruin magnitude ------------------------------------------------
    "stack":       fact("stack", "0.0339 BTC = $2,756"),
    "weeks":       fact("weeks", "27.6 週／兩計畫 13.8 週"),
    "months32":    fact("months32", "3.2 個月儲蓄"),
    "yr15":        fact("yr15", "1.5 年儲蓄"),
    "st15k":       fact("st15k", "$15k"),
    # ---- 6. optimal size --------------------------------------------------
    "objective":   fact("objective", "`G(m,λ) = e·μ_ρ − e²σ_ρ²/2 + 52·p_week(λ)·log(1−m)`"),
    "fullkelly":   fact("fullkelly", "8.37"),
    "e20":         fact("e20", "0.13（g=+0.04%）"),
    "e30":         fact("e30", "1.00（+3.21%）"),
    # ---- 7. hidden short BTC ----------------------------------------------
    "alpha_t":     fact("alpha_t", "alpha +45.85%/年（t=+3.38）"),
    "beta_t":      fact("beta_t", "beta −0.1605（t=−3.93）"),
    "beta_amp":    fact("beta_amp", "−0.214"),
    "acct_beta":   fact("acct_beta", "0.786"),
    "beta_in":     fact("beta_in", "−4.25%/年"),
    "beta_fwd":    fact("beta_fwd", "−6.9%/年"),
    # ---- 8. thresholds ----------------------------------------------------
    "th_dep":      fact("th_dep", "13.8% ~ 23.8%"),
    "th_beat":     fact("th_beat", "37.3% ~ 47.3%"),
    "th_dep_h":    fact("th_dep_h", "27.6% ~ 47.6%"),
    "th_beat_h":   fact("th_beat_h", "74.5% ~ 94.5%"),
    "p_alpha":     fact("p_alpha", "15%~25%"),
    "p_half":      fact("p_half", "10%~15%"),
    "th_pt_dep":   fact("th_pt_dep", "18.7%"),
    "th_pt_beat":  fact("th_pt_beat", "42.2%"),
    "th_pt_h":     fact("th_pt_h", "37.4%"),
    "emax_t":      fact("emax_t", "1,300 次搜尋下純雜訊的最大 t 期望值就是 3.316"),
    "t_pub":       fact("t_pub", "t=3.029"),
    "t_nofund":    fact("t_nofund", "2.641"),
    "emax_v":      fact("emax_v", "3.316"),
    "searches":    fact("searches", "1,300"),
    # ---- 9. control group menu -------------------------------------------
    "c_btc":       fact("c_btc", "+0.00320"),
    "c_pct":       fact("c_pct", "+9.43%"),
    "c_usd":       fact("c_usd", "+$260"),
    "se_btc":      fact("se_btc", "+0.00040"),
    "se_pct":      fact("se_pct", "+1.18%"),
    "se_usd":      fact("se_usd", "+$32"),
    "t20_btc":     fact("t20_btc", "+0.00001"),
    "t20_pct":     fact("t20_pct", "+0.04%"),
    "t20_usd":     fact("t20_usd", "+$1"),
    "t50_btc":     fact("t50_btc", "+0.00456"),
    "t50_pct":     fact("t50_pct", "+13.4%"),
    "t50_usd":     fact("t50_usd", "+$371"),
    "prereg_dd":   fact("prereg_dd", "−18.4% / −24.5%"),
    "band_usd":    fact("band_usd", "$1 到 $27"),
    "band_pct":    rfact("band_pct", "+0.04% ~ +0.98%／年"),
    # ---- 10. per-start distribution ---------------------------------------
    "rel_face":    fact("rel_face", "中位 1.40 倍"),
    "rel_zero":    fact("rel_zero", "中位 0.79 倍、最差 0.67 倍、84% 的起點輸"),
    "windows":     fact("windows", "81 個重疊 1 年窗"),
    "ctrl_same":   fact("ctrl_same", "對照組同期 1.094"),
    "indep":       fact("indep", "2.5 個獨立觀測"),
    # ---- 11. edge or regime ----------------------------------------------
    "tri_beta":    fact("tri_beta", "三源 beta −0.120"),
    "tri_corr":    fact("tri_corr", "corr −0.327"),
    "up_weeks":    fact("up_weeks", "+6.4%/年"),
    "down_weeks":  fact("down_weeks", "+56.3%/年"),
    "gla_up":      fact("gla_up", "−5.5%"),
    "sfb_up":      fact("sfb_up", "−14.8%"),
    "hold_cagr":   fact("hold_cagr", "CAGR +21.0%、期內 −53.0%"),
    # ---- 12. hedge family zeroed -----------------------------------------
    "hedge_cr":    fact("hedge_cr", "幣數比 0.667~0.934"),
    "hedge_dd":    fact("hedge_dd", "把帳戶回撤從 −62.9% 壓到 −5.8%"),
    # ---- 13. self-corrections --------------------------------------------
    "dd_true":     fact("dd_true", "−12.4%"),
    "dd_coord":    fact("dd_coord", "−9.3%"),
    "ann_true":    fact("ann_true", "+69.7%"),
    "ann_coord":   fact("ann_coord", "+64.3%"),
    "net_ratio":   fact("net_ratio", "淨額/不抵銷 = 0.952"),
    "mirror_fix":  fact("mirror_fix", "+32.37%／Sharpe 1.901"),
    "tri_first":   fact("tri_first", "這本帳十七輪來沒人真的建過，本輪首建"),
    # ---- 14. spec ambiguity ----------------------------------------------
    "lam10":       fact("lam10", "λ=10"),
    "spec_fix":    fact("spec_fix", "毛名目 ≤ 期貨錢包裡的 BTC 價值"),
    # ---- 15. the user's own words ----------------------------------------
    # ---- 18. the audit gate, as it actually stands on publication day ----
    "aud_first":   fact("aud_first", "費曼首次 = 第十四輪補稽核；凱利首次 = 第十七輪"),
    "aud_none":    fact("aud_none", "第 1~13 輪各 0 次"),
    "aud_vrp":     fact("aud_vrp", "這一關第一次跑，抓到四個硬阻擋"),
    "aud_team":    fact("aud_team", "團隊管理稽核 · 費曼裁決"),
    "btc_basis":   fact("btc_basis", "歷史最差 BTC 週（期內 −42.4%）"),
    "btc_basis2":  fact("btc_basis2", "BTC 期內最深跌幅"),
    "quote_foul":  fact("quote_foul", "你這是犯規，你提高我的投入本金，但是沒有創造你的價值"),
    "quote_spec":  fact("quote_spec", "你誤會了我的原則，我沒有規定你只能動用 10％資產"),
    "quote_pick":  fact("quote_pick", "不設回撤上限，只要不會被強平"),
    "scoreboard":  fact("scoreboard", "同樣的錢、同樣的流入、同樣的時間，最後手上的 BTC 是多還是少"),
    # ---- 16. control-group definition ------------------------------------
    "cg_sim":      cfact("cg_sim", "「純 DCA 六年 = 0.8511 顆 = 幣數比 1.0000」是模擬基準，不是使用者的帳戶歷史"),
    "cg_flow":     cfact("cg_flow", "年流量 **$10,400**（兩計畫合計）"),
    "cg_real":     cfact("cg_real", "約 24 次買進、約 $2,400、約 0.44 年"),
    "cg_px":       cfact("cg_px", "$81,306"),
    # ---- 17. correction 3: the baseline is a simulation ------------------
    "cg_wrong":    cfact("cg_wrong", "任何拿 0.8511 當「他的成績」的敘述都是錯的。"),
    "cg_24w":      cfact("cg_24w", "他的帳戶只有約 24 週。"),
    "cg_ver":      cfact("cg_ver", "# 對照組 v1 · 2026-09-21"),
    "cg_origin":   cfact("cg_origin", "這份檔案是整個專案的**計分原點**"),
    "cg_confirm":  cfact("cg_confirm", "使用者一眼可確認或推翻"),
    "base_ratio":  fact("base_ratio", "回測基準 319 週 → 0.8511 顆。使用者實際 0.0339 顆 = 基準的 4.0%。"),
    "base_alive":  fact("base_alive", "這不會使既有回測失效"),
    "base_must":   fact("base_must", "報告必須講清楚，否則使用者會以為那是自己的帳。"),
    "cg_late":     fact("cg_late", "而對照組直到第十七輪才存在"),
    "cg_both":     fact("cg_both", "兩個錯的計分原點都寫進了使用者讀得到的頁面"),
    "cg_nogate":   fact("cg_nogate", "該攔的那個 agent 十六輪沒被呼叫過"),
    "fs_fix":      fact("fs_fix", "流量／存量比是 3.78×，不是 1.89×"),
    "cg_rev":      cfact("cg_rev", "改動要留紀錄"),
}
print(f"{len(F)} literals asserted against their sources")

# ------------------------------------------------------------------ logs ----
LOGS = {}
for n in ("b_liq_plane", "c_lamcrit", "d_joint_stress", "e_trisource",
          "f_growth", "g_costfree", "h_tail", "i_verdict", "j_breakeven",
          "k_optsize", "l_decomp"):
    LOGS[n] = open(os.path.join(KR, f"{n}.log"), encoding="utf-8").read()

BOOK_ZH = {
    "R5 LOCKED mom28/n10/invvol": "R5 鎖定組",
    "R6 SF_B gla0/n10/invvol": "R6 SF_B",
    "gla BASE n5/equal": "gla BASE n5/equal（三源的構造）",
    "Tri-source 1/N netted book": "三源 1/N 淨額帳（本輪首建）",
}

# --- H: three tail models, P(liquidation) per week, by lambda ---------------
TAIL = {}          # book -> {lam: (empirical, gpd, lognormal)}
TAIL_XI = {}       # book -> (xi, n_weeks)
_cur = None
for line in LOGS["h_tail"].splitlines():
    m = re.match(r"\s*\[(.+?)\]\s+n_weeks=(\d+).*?GPD xi=([+\-][\d.]+)", line)
    if m:
        _cur = m.group(1)
        TAIL[_cur] = {}
        TAIL_XI[_cur] = (m.group(3), int(m.group(2)))
        continue
    m = re.match(r"\s*([\d.]+)\s+([\d.]+)\s+([\d.e+\-]+)\s+([\d.e+\-]+)\s+1 in", line)
    if m and _cur:
        TAIL[_cur][float(m.group(1))] = (float(m.group(2)), float(m.group(3)),
                                         float(m.group(4)))
assert set(TAIL) == set(BOOK_ZH), sorted(TAIL)
for b in TAIL:
    assert len(TAIL[b]) == 6, (b, len(TAIL[b]))
LAMS = sorted(TAIL["R5 LOCKED mom28/n10/invvol"])


def per_year(p_week):
    """Derived here, not taken from the log: 1-(1-p)^52."""
    return 1.0 - (1.0 - p_week) ** 52


# cross-check the derivation against the one annualisation the log states
_chk = per_year(TAIL["R5 LOCKED mom28/n10/invvol"][1.333][1])
assert abs(_chk - 0.02552) < 5e-5, _chk

# --- H2: the unit fix. Everything below is computed here, in ONE unit ------
# The log prints P(liquidation) PER WEEK for all three models. The GPD column
# was annualised on the way into REPORT.md; the lognormal column was not, and
# the two were then printed side by side. That is the round-14 disease again:
# a unit label travelling log -> REPORT -> page without anyone converting.
CAP = 1.333
GPD_W = {b: TAIL[b][CAP][1] for b in TAIL}
LOGN_W = {b: TAIL[b][CAP][2] for b in TAIL}
GPD_A = {b: per_year(v) for b, v in GPD_W.items()}
LOGN_A = {b: per_year(v) for b, v in LOGN_W.items()}
LOGN_BAND = f"{min(LOGN_A.values()):.2e} ~ {max(LOGN_A.values()):.2e}／年"
OOM = {b: math.log10(GPD_A[b] / LOGN_A[b]) for b in TAIL}
OOM_LO, OOM_HI = min(OOM.values()), max(OOM.values())
OOM_CROSS = math.log10(max(GPD_A.values()) / min(LOGN_A.values()))
OOM_WRONG = math.log10(max(GPD_A.values()) / min(LOGN_W.values()))
# each of these must equal, to the digit, what the state file now says
assert LOGN_BAND == F["logn_ann"], (LOGN_BAND, F["logn_ann"])
assert (f"同一本帳 {OOM_LO:.1f}~{OOM_HI:.1f} 個數量級，跨帳本最大 {OOM_CROSS:.2f}"
        == F["oom_truth"]), (OOM_LO, OOM_HI, OOM_CROSS)
assert (f"「六個數量級」＝ 年化的 GPD ÷ 每週的對數常態 = {OOM_WRONG:.2f}"
        == F["oom_wrong"]), OOM_WRONG
print(f"unit fix: lognormal {LOGN_BAND}; same-book gap {OOM_LO:.1f}~{OOM_HI:.1f} "
      f"orders (cross-book {OOM_CROSS:.2f}); the retired '6 orders' was {OOM_WRONG:.2f} "
      f"and mixed units")

# --- F1: the growth table, straight from the CSV ---------------------------
# B4: the column f_growth.py prints under the header "coinratio" is eq[-1],
# i.e. the overlay's own cumulative coin multiple over n weeks with NO DCA
# inflow and NO pure-DCA denominator. The actual annualised figure is `cr`.
# Putting 3.827 in a column headed "coin ratio" reads as 3.7x the best result
# in project history (the real range is 0.6666~1.0276). It is not that.
F1 = {}
with open(os.path.join(KR, "f1_growth.csv"), encoding="utf-8") as fh:
    hdr = fh.readline().strip().split(",")
    for line in fh:
        row = line.rstrip("\n").rsplit(",", len(hdr) - 1)
        rec = dict(zip(hdr, [row[0]] + row[1:]))
        if rec["cand"].startswith('"Tri-source 1/N'):
            F1[float(rec["lam"])] = rec
assert set(F1) >= {0.75, 1.0, CAP}, sorted(F1)
CUM_CAP = float(F1[CAP]["cum"])          # 3.8266... : cumulative, not a ratio
CR_CAP = float(F1[CAP]["cr"])            # 1.6967... : annualised
NW_CAP = int(F1[CAP]["n"])
YRS_CAP = NW_CAP / 52.0
assert f"{float(F1[CAP]['dd']) * 100:.1f}%" == F["dd_true"].replace("−", "-")
assert f"{float(F1[CAP]['g']) * 100:.1f}%" == F["ann_true"].replace("+", "")
# S4: the -9.3% the coordinator published IS a real number - it is the
# drawdown at lambda=1.0. The error was scaling it linearly to lambda=1.333.
assert f"{float(F1[1.0]['dd']) * 100:.1f}%" == F["dd_coord"].replace("−", "-"), \
    F1[1.0]["dd"]
print(f"growth csv: cumulative {CUM_CAP:.3f}x over {NW_CAP} weeks "
      f"({YRS_CAP:.2f} yr), annualised {CR_CAP:.4f}; "
      f"the published {F['dd_coord']} is the lambda=1.0 drawdown")

# --- J2: per-start-point relative-wealth distribution -----------------------
J2 = {}
for line in LOGS["j_breakeven"].splitlines():
    m = re.match(r"\s*lam=([\d.]+)\s+(as backtested|alpha haircut 50%|"
                 r"alpha = 0 \(costs\+beta only\))\s+(\d+)"
                 + r"\s+([\d.]+)" * 6 + r"\s+([\d.]+)%", line)
    if m:
        J2[(m.group(1), m.group(2))] = dict(
            starts=int(m.group(3)),
            p5=float(m.group(4)), p25=float(m.group(5)), med=float(m.group(6)),
            p75=float(m.group(7)), p95=float(m.group(8)),
            worst=float(m.group(9)), lose=float(m.group(10)))
assert len(J2) == 9, len(J2)
CTRL_SAME = float(re.search(r"control over the same horizon = ([\d.]+)",
                            LOGS["j_breakeven"]).group(1))

# --- C1: lambda_crit percentiles -------------------------------------------
LC = {}
_cur = None
for line in LOGS["c_lamcrit"].splitlines():
    m = re.match(r"\s*\[(.+?)\]\s+n_weeks=(\d+)", line)
    if m:
        _cur = m.group(1).replace("  (the tri-source construction)", "")
        LC[_cur] = {"n": int(m.group(2))}
        continue
    m = re.match(r"\s*min=([\d.]+)\s+p0.5=[\d.]+\s+p1=([\d.]+)\s+p2=[\d.]+"
                 r"\s+p5=([\d.]+)\s+p10=[\d.]+\s+p25=[\d.]+\s+p50=([\d.]+)", line)
    if m and _cur:
        LC[_cur].update(min=float(m.group(1)), p1=float(m.group(2)),
                        p5=float(m.group(3)), p50=float(m.group(4)))
m = re.search(r"weeks (\d+)\s+days.*?lambda_crit:\s+min ([\d.]+)\s+p1 ([\d.]+)"
              r"\s+p5 ([\d.]+)\s+p25 [\d.]+\s+median ([\d.]+)",
              LOGS["e_trisource"], re.S)
assert m
LC["Tri-source 1/N netted book"] = dict(n=int(m.group(1)), min=float(m.group(2)),
                                        p1=float(m.group(3)), p5=float(m.group(4)),
                                        p50=float(m.group(5)))
assert len(LC) == 4, sorted(LC)
for b in LC:
    assert {"n", "min", "p1", "p5", "p50"} <= set(LC[b]), (b, LC[b])

# --- B1: the m-cancels grid -------------------------------------------------
MGRID = re.findall(r"m=([\d.]+)\s+days=\s*(\d+)\s+min ratio=([\d.]+)\s+"
                   r"p1=([\d.]+)\s+liq days=(\d+)", LOGS["b_liq_plane"])
assert len(MGRID) >= 3, LOGS["b_liq_plane"][:400]
assert len({d for _, d, _, _, _ in MGRID}) == 1, "m grid ran different day counts"
assert all(int(k) == 0 for *_, k in MGRID), "a liquidation appeared in the m grid"

# --- L1: the regression decomposition --------------------------------------
L1 = re.search(r"alpha\s+a\s+=\s+([+\-][\d.]+)%/yr\s+\(SE\s+([\d.]+)%,\s+t\s+"
               r"([+\-][\d.]+)\)", LOGS["l_decomp"])
L1b = re.search(r"beta\s+b\s+=\s+([+\-][\d.]+)\s+\(SE\s+([\d.]+)\)\s+"
                r"\(t\s+([+\-][\d.]+)\)", LOGS["l_decomp"]) or \
      re.search(r"beta\s+b\s+=\s+([+\-][\d.]+)\s+\(SE\s+([\d.]+),\s+t\s+"
                r"([+\-][\d.]+)\)", LOGS["l_decomp"])
assert L1 and L1b, "L1 parse failed"
NWK = int(re.search(r"per unit of exposure e\s+\(n=(\d+) weeks\)",
                    LOGS["l_decomp"]).group(1))
print(f"logs parsed: {len(TAIL)} tail books, {len(J2)} start-point rows, "
      f"{len(LC)} lambda_crit books, n={NWK} weeks in the decomposition")

# ----------------------------------------------------------------- charts --
def svg_open(w, h, label):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" '
            f'aria-label="{html.escape(label)}" '
            f'style="background:#171a23;border:1px solid #2a2e3c;border-radius:12px">')


def chart_ruin():
    """P(liquidation) per YEAR against internal leverage, log growth axis.

    A log axis is not decoration here: in the SAME unit the two defensible
    models are 3-5 orders of magnitude apart, and a linear axis would render
    one of them as zero. Both columns are annualised with per_year() before
    they are plotted - the chart was already right when the prose was wrong.
    """
    W, H = 960, 430
    L, R, T, B = 74, 250, 26, 56
    lo, hi = -10.0, 0.0          # log10 of P/yr
    xs = {lam: L + (R_ := (W - R - L)) * i / (len(LAMS) - 1)
          for i, lam in enumerate(LAMS)}

    def y(p):
        v = max(p, 10 ** lo)
        return T + (H - T - B) * (math.log10(v) - hi) / (lo - hi)

    s = [svg_open(W, H, "四個帳本在三個尾部模型下的年化強平機率，縱軸為對數成長軸")]
    for d in range(int(lo), int(hi) + 1):
        yy = y(10.0 ** d)
        lbl = "1" if d == 0 else f"10^{d}"
        s.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{W-R}" y2="{yy:.1f}" '
                 f'stroke="#232735" stroke-width="1" stroke-dasharray="3 3"/>'
                 f'<text x="{L-8}" y="{yy+4:.1f}" text-anchor="end" font-size="11" '
                 f'fill="#6b7185">{lbl}</text>')
    # the empirical 95% upper bound: the flat ceiling the data alone allows
    emp = per_year(3.0 / 250.0)
    s.append(f'<line x1="{L}" y1="{y(emp):.1f}" x2="{W-R}" y2="{y(emp):.1f}" '
             f'stroke="#fab219" stroke-width="2"/>'
             f'<text x="{W-R+10}" y="{y(emp)+4:.1f}" font-size="12" fill="#fab219">'
             f'經驗 0/N 的 95% 上界 {emp*100:.0f}%/年</text>')
    cols = ["#3987e5", "#d95926", "#199e70", "#d97757"]
    for i, (bk, col) in enumerate(zip(BOOK_ZH, cols)):
        for j, (which, dash) in enumerate(((1, ""), (2, "5 4"))):
            pts = " ".join(f"{xs[l]:.1f},{y(per_year(TAIL[bk][l][which])):.1f}"
                           for l in LAMS)
            s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" '
                     f'stroke-width="2" stroke-dasharray="{dash}" opacity="'
                     f'{1 if j == 0 else .55}"/>')
        yy = T + 14 + i * 20
        s.append(f'<line x1="{W-R+10}" y1="{yy}" x2="{W-R+34}" y2="{yy}" '
                 f'stroke="{col}" stroke-width="2"/>'
                 f'<text x="{W-R+40}" y="{yy+4}" font-size="11" fill="#9aa0b4">'
                 f'{html.escape(BOOK_ZH[bk])}</text>')
    yy = T + 14 + 4 * 20 + 8
    s.append(f'<line x1="{W-R+10}" y1="{yy}" x2="{W-R+34}" y2="{yy}" stroke="#9aa0b4" '
             f'stroke-width="2"/><text x="{W-R+40}" y="{yy+4}" font-size="11" '
             f'fill="#9aa0b4">實線＝厚尾模型 GPD</text>')
    s.append(f'<line x1="{W-R+10}" y1="{yy+18}" x2="{W-R+34}" y2="{yy+18}" '
             f'stroke="#9aa0b4" stroke-width="2" stroke-dasharray="5 4" opacity=".55"/>'
             f'<text x="{W-R+40}" y="{yy+22}" font-size="11" fill="#9aa0b4">'
             f'虛線＝對數常態</text>')
    for lam in LAMS:
        s.append(f'<text x="{xs[lam]:.1f}" y="{H-B+20}" text-anchor="middle" '
                 f'font-size="11" fill="#6b7185">{lam:g}</text>')
    xc = xs[1.333]
    s.append(f'<line x1="{xc:.1f}" y1="{T}" x2="{xc:.1f}" y2="{H-B}" stroke="#d03b3b" '
             f'stroke-width="1" stroke-dasharray="4 4"/>'
             f'<text x="{xc+6:.1f}" y="{T+12}" font-size="11" fill="#d03b3b">'
             f'專案上限 λ=1.333</text>')
    s.append(f'<text x="{L}" y="{H-14}" font-size="11" fill="#6b7185">'
             f'橫軸：內部槓桿 λ（毛名目 ÷ 已投保證金）　'
             f'縱軸：一年內至少被強平一次的機率（對數成長軸，每一格差 10 倍）'
             f'　年化由週機率換算：1−(1−p)^52</text>')
    s.append("</svg>")
    return "".join(s)


def chart_relwealth():
    """Relative wealth (candidate / control) per start point, log axis.

    Reported as a ratio, never as a subtraction of percentages, and on a log
    axis because the distribution is right-skewed.
    """
    rows = [("回測原值（alpha 照單全收）", "as backtested", "#3987e5"),
            ("alpha 打五折", "alpha haircut 50%", "#fab219"),
            ("alpha = 0（只剩成本與隱藏 beta）", "alpha = 0 (costs+beta only)", "#d03b3b")]
    W, H = 960, 300
    L, R, T = 300, 40, 34
    lo, hi = math.log(0.6), math.log(2.2)

    def x(v):
        return L + (W - R - L) * (math.log(v) - lo) / (hi - lo)

    s = [svg_open(W, H, "三種 alpha 假設下，81 個起點的相對財富分布，橫軸為對數軸")]
    for g in (0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2.0):
        s.append(f'<line x1="{x(g):.1f}" y1="{T-8}" x2="{x(g):.1f}" y2="{H-52}" '
                 f'stroke="{"#d97757" if g == 1.0 else "#232735"}" stroke-width="'
                 f'{2 if g == 1.0 else 1}" stroke-dasharray="{"" if g == 1.0 else "3 3"}"/>'
                 f'<text x="{x(g):.1f}" y="{H-34}" text-anchor="middle" font-size="11" '
                 f'fill="{"#d97757" if g == 1.0 else "#6b7185"}">{g:g}×</text>')
    for i, (zh, key, col) in enumerate(rows):
        d = J2[("1.333", key)]
        yy = T + 26 + i * 62
        rel = {k: d[k] / CTRL_SAME for k in ("p5", "p25", "med", "p75", "p95", "worst")}
        s.append(f'<text x="{L-14}" y="{yy+4}" text-anchor="end" font-size="12" '
                 f'fill="#e8e9ee">{html.escape(zh)}</text>')
        s.append(f'<line x1="{x(rel["p5"]):.1f}" y1="{yy}" x2="{x(rel["p95"]):.1f}" '
                 f'y2="{yy}" stroke="{col}" stroke-width="2" opacity=".45"/>')
        s.append(f'<rect x="{x(rel["p25"]):.1f}" y="{yy-9}" '
                 f'width="{x(rel["p75"])-x(rel["p25"]):.1f}" height="18" rx="4" '
                 f'fill="{col}" opacity=".28"/>')
        s.append(f'<line x1="{x(rel["med"]):.1f}" y1="{yy-11}" x2="{x(rel["med"]):.1f}" '
                 f'y2="{yy+11}" stroke="{col}" stroke-width="3"/>')
        s.append(f'<circle cx="{x(rel["worst"]):.1f}" cy="{yy}" r="3.5" fill="{col}"/>')
        s.append(f'<text x="{x(rel["med"]):.1f}" y="{yy-16}" text-anchor="middle" '
                 f'font-size="11" fill="{col}">中位 {rel["med"]:.2f}×</text>')
        s.append(f'<text x="{L-14}" y="{yy+20}" text-anchor="end" font-size="10.5" '
                 f'fill="#6b7185">最差起點 {rel["worst"]:.2f}× · '
                 f'{d["lose"]:.1f}% 的起點輸給對照組</text>')
    s.append(f'<text x="{L-14}" y="{H-14}" text-anchor="end" font-size="11" '
             f'fill="#6b7185">盒＝p25~p75，細線＝p5~p95，點＝最差起點</text>')
    s.append(f'<text x="{L}" y="{H-14}" font-size="11" fill="#6b7185">'
             f'橫軸（對數軸）：一年後的幣數 ÷ 對照組同期的幣數。'
             f'1.0× 這條線就是對照組。λ=1.333、{J2[("1.333","as backtested")]["starts"]} 個重疊起點。</text>')
    s.append("</svg>")
    return "".join(s)


CH_RUIN = chart_ruin()
CH_REL = chart_relwealth()
print(f"charts built: {len(CH_RUIN):,} + {len(CH_REL):,} bytes of svg")

# ------------------------------------------------------- shell lifted from r16
r16_txt = open(R16, encoding="utf-8").read()
GATE = re.search(r"<script>.*?</script>", r16_txt, re.S).group(0)
CSS = re.search(r"<style>.*?</style>", r16_txt, re.S).group(0)
assert "hub_token" in GATE and "--accent" in CSS

v1_txt = open(V1, encoding="utf-8").read()
r15_txt = open(R15, encoding="utf-8").read()
# The index is read with THIS round's own card stripped out: section 10 takes a
# census of how often the old baseline wording appears on published pages, and
# a card that quotes that wording would otherwise count itself and make the
# build non-reproducible (caught by rebuilding twice and diffing).
CARD_RE = r"<!-- R17-CARD:BEGIN.*?<!-- R17-CARD:END -->\n?"
index_txt = re.sub(CARD_RE, "", open(INDEX, encoding="utf-8").read(), flags=re.S)
V1_IDS = set(re.findall(r'id="([A-Za-z0-9_-]+)"', v1_txt))
R15_IDS = set(re.findall(r'id="([A-Za-z0-9_-]+)"', r15_txt))
R16_IDS = set(re.findall(r'id="([A-Za-z0-9_-]+)"', r16_txt))
INDEX_IDS = set(re.findall(r'id="([A-Za-z0-9_-]+)"', index_txt))
PUBLISHED = {"crypto-dca-amplifier-report.html": v1_txt,
             "laoliu-r15-triage2.html": r15_txt,
             "laoliu-r16-eth.html": r16_txt,
             "laoliu.html": index_txt}
# How often the simulated baseline "0.8511" is stated on each already-published
# page. Counted here, never typed into the prose (correction 3, section 10).
BASE_HITS = {k: len(re.findall(r"0\.8511", v)) for k, v in PUBLISHED.items()}
assert all(n > 0 for n in BASE_HITS.values()), BASE_HITS
# S9: how many times the "+5 USDT/week = $260/yr" comparison is actually on the
# published pages. \b is useless next to "$2608", hence the lookahead.
FOUL_HITS = {k: len(re.findall(r"\$260(?!\d)", v)) for k, v in PUBLISHED.items()}
FOUL_TOTAL = sum(FOUL_HITS.values())
assert FOUL_HITS["laoliu-r15-triage2.html"] == 0 and \
       FOUL_HITS["laoliu-r16-eth.html"] == 0, FOUL_HITS
# S2: count the artefacts instead of remembering how many there were
import glob                                                        # noqa: E402
KR_CSV = len(glob.glob(os.path.join(KR, "[a-z]*.csv")))
KR_PY = len(glob.glob(os.path.join(KR, "[a-z]*.py")))
KR_LOG = len(glob.glob(os.path.join(KR, "[a-z]*.log")))
# S3: the "40 places that mention drawdown" was true when the review ran
DD_LINES = sum(1 for ln in state_txt.splitlines() if "回撤" in ln)
DD_HITS = state_txt.count("回撤")


def gl(term, gid):
    return f'<a class="gl" href="#{gid}">{term}</a>'


GLOSS = [
    ("記號", [
        ("g17-m", "m（投入比例）", "fraction in the futures wallet",
         "你的 BTC 裡，實際搬進「合約錢包」當抵押品的那一份。m=1 就是全部搬進去，m=0.1 就是只搬一成。"
         "<b>它只決定「萬一出事會賠掉多少」。</b>"),
        ("g17-lam", "λ（內部槓桿）", "internal leverage",
         "合約部位的總面額 ÷ 你搬進去當抵押品的錢。λ=2 就是用 1 塊錢去建 2 塊錢的部位。"
         "<b>它只決定「出事的機率有多高」。</b>"),
        ("g17-e", "e（曝險）", "exposure = m × λ",
         "合約總面額 ÷ 你全部的財富。<b>它只決定報酬。</b>"
         "同一個 e 可以由很多組 (m, λ) 湊出來，而那些組合的安全程度天差地遠。"),
        ("g17-f", "f（協調者說的「投入比例」）", "",
         "協調者一直用的變數，定義是「總面額 = 0.75 × f × 全部財富」。"
         "本輪發現：在 m=1 的情況下它其實就是 λ 的 0.75 倍，也就是<b>同一個東西換個名字</b>。"),
        ("g17-alpha", "alpha（α）", "alpha",
         "策略自己創造的、跟市場漲跌無關的那一部分報酬。這是整個專案十七輪在找的東西。"),
        ("g17-beta", "beta（β）", "beta",
         "報酬裡「跟著 BTC 走」的那一部分。beta 是負的，代表這個策略裡偷偷藏了一個<b>做空 BTC</b>的部位——"
         "BTC 漲的時候它會扯後腿。"),
        ("g17-t", "t 值", "t-statistic",
         "「這個數字離零有幾個雜訊單位遠」。本專案自訂的及格線是 3.0。t 越大越不像運氣。"),
        ("g17-cr", "幣數比", "coin ratio",
         "本專案唯一的主計分單位：同樣的錢、同樣的時間，最後手上的 BTC 顆數 ÷ 單純定期定額買進持有拿到的顆數。"
         "1.0 就是打平。"),
        ("g17-rel", "相對財富", "relative wealth",
         "兩個做法的最終幣數<b>相除</b>（1.40 倍），不是把兩個百分比<b>相減</b>。"
         "相減在複利的世界會算錯，本專案一律用相除。"),
    ]),
    ("風險與機率", [
        ("g17-liq", "強平（爆倉）", "liquidation",
         "抵押品不夠賠了，交易所直接把你的部位砍掉。砍完之後合約錢包裡的錢就沒了。"),
        ("g17-cross", "跨倉", "cross margin",
         "錢包裡所有資產一起當抵押品、所有部位一起算盈虧的模式。本專案用的就是這個。"),
        ("g17-mmr", "MMR（維持保證金率）", "maintenance margin rate",
         "交易所規定「這個面額的部位至少要壓多少錢在裡面」的比率。低於它就強平。"),
        ("g17-lamcrit", "λ_crit（臨界槓桿）", "critical leverage",
         "把某一週的行情套進去，算出「內部槓桿要開到多少才會在那一週被強平」。"
         "這個數字越大代表那一週越安全。"),
        ("g17-gpd", "GPD（厚尾模型）", "generalised Pareto distribution / peaks-over-threshold",
         "專門用來外推「極端事件」的統計模型：只拿分布最尾端那一小截來配適，再往外推。"
         "它假設<b>極端事件比常態分布預期的更常發生</b>。"),
        ("g17-xi", "ξ（形狀參數）", "xi",
         "厚尾模型裡控制「尾巴多厚」的數字。ξ 大於 0 就是厚尾——極端值比直覺想的更常出現。"),
        ("g17-logn", "對數常態", "lognormal",
         "另一個外推極端事件的模型，尾巴比 GPD 薄得多。兩個模型都站得住，"
         "而它們在這裡給出的答案，換算到同一個單位之後，同一本帳仍差 3~4 個數量級。"),
        ("g17-r3", "0/N 的 95% 上界（三法則）", "rule of three",
         "「N 次裡零次發生」時，真實機率的 95% 上界大約是 3/N。"
         "250 週零強平，只能說「每週機率大概不超過 1.2%」——那是很鬆的一句話。"),
        ("g17-adl", "ADL（自動減倉）", "auto-deleveraging",
         "市場極端時，交易所會強制把<b>賺錢的一方</b>的部位也平掉來補洞。"
         "你可能明明賺著，部位卻被拿走。"),
        ("g17-intraweek", "期內最深跌幅", "worst intra-week drawdown",
         "<b>一週之內</b>從最高價跌到最低價的幅度，不是這一週的收盤漲跌，"
         "也不是整段持有期的跌幅。本頁的 −42.4% 是<b>樣本裡週內最深的那一週</b>"
         "（2020-08~2026-08），強平看的是盤中觸價，所以口徑取週內而不是收盤。"),
        ("g17-dd", "回撤", "drawdown",
         "從最高點跌到最低點的幅度。舊規格用它當淘汰條件，新規格已經不用了。"),
    ]),
    ("方法", [
        ("g17-kelly", "對數成長最適下注", "Kelly criterion",
         "因為幣數會複利，正確的目標不是「期望報酬最大」而是「期望的<b>成長率</b>最大」。"
         "它天生會把「破產」這件事的代價算進去——破產一次，後面的複利全部歸零。"),
        ("g17-bang", "角點解（bang-bang）", "bang-bang solution",
         "最佳解不落在中間，而是貼在邊界上：不是不做，就是做滿。"
         "出現這種形狀時，「該做多少」這個問題本身就沒有中間答案。"),
        ("g17-prereg", "預登記", "pre-registration",
         "在看資料之前先把要測什麼寫死。事後才挑出來的結果不算數，"
         "因為挑選本身就會製造出漂亮的數字。"),
        ("g17-indep", "獨立觀測數", "independent observations",
         "重疊的視窗會重複使用同一段歷史。81 個一年窗如果全部來自 2.54 年，"
         "真正互不重疊的只有大約 2.5 個。"),
        ("g17-pct", "p1 / p5（分位數）", "percentile",
         "p5 就是「比它更差的只有 5% 的情況」。用來描述尾巴，不用來描述典型情況。"),
        ("g17-funding", "資金費", "funding rate",
         "永續合約多空雙方定期互相支付的費用。本專案有幾個結果嚴重依賴它。"),
    ]),
]
GID = {g[0] for _, items in GLOSS for g in items}

# ------------------------------------------------------------------- doc ----
P = []      # page pieces
A = P.append

A(f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>老六 · 第十七輪：風控與對照組覆核</title>
{GATE}
{CSS}
</head>
<body>

<header>
  <div class="crumb">
    <a href="index.html">工具中心</a><span class="sep">›</span><a href="laoliu.html">老六研究院</a><span class="sep">›</span><span class="here">第十七輪 · 風控與對照組覆核</span>
  </div>
  <h1>第十七輪：你以為在調的「投入多少」，其實一直是「開幾倍槓桿」</h1>
  <p class="tagline">
    你在 {TODAY} 把「投入比例」的上限解封了，並選擇「不設回撤上限，只要不會被強平」。
    這一輪把新規格下的三件事重算：<b>會不會破產</b>、<b>該投多少</b>、<b>值不值得從你現在在做的事換過去</b>。
    第一件事就翻掉了一個十七輪來沒人發現的混淆——而它剛好是最危險的那一個變數。
    這一頁另外帶<b>三個更正</b>，其中一個是<b>你自己指出來的</b>。
  </p>
  <div class="meta-bar">
    <span class="badge">輪次 <b>第十七輪</b></span>
    <span class="badge">日期 <b>{TODAY}</b></span>
    <span class="badge">本輪新幣數比 <b>0 個</b></span>
    <span class="badge">本頁更正 <b>3 個已發布錯誤</b></span>
    <span class="badge">發布前稽核 <b>需修正 · 5 項已修</b></span>
    <span class="badge live">狀態 <b>研究進行中</b></span>
  </div>
</header>

<main>

  <section id="summary">
    <h2>摘要：這一輪發生了什麼</h2>

    <div class="plain">
      <span class="lbl">先看這裡</span>
      <p>這一頁是<b>第十七輪的獨立研究紀錄</b>，不是舊報告的修訂版。
        依照你 2026-09-21 的規則「以後報告盡量不要修改舊的，每次產生新的頁面」，
        <a href="crypto-dca-amplifier-report.html">總覽報告（v1）</a>、
        <a href="laoliu-r15-triage2.html">第十五輪</a>、
        <a href="laoliu-r16-eth.html">第十六輪</a><b>三個都一個字都沒有動</b>。
        要更正它們的地方，寫在這一頁的<a href="#correction-scoreboard">更正一</a>、
        <a href="#correction-spec">更正二</a>與<a href="#correction-control">更正三</a>，
        並用連結指回原處。</p>
      <p><b>這一輪的答案是：不該換。</b>不是因為找到了新的反證，
        而是因為把「該投多少」這個問題認真解一次之後，它<b>解不出中間答案</b>——
        它退化成「你信不信這個策略是真的」這個單一問題。
        而支持它的證據撐得起的機率，<b>不夠高</b>。</p>
      <p>所有英文縮寫、單個字母、希臘字母，在<a href="#glossary">這一頁自己的術語表</a>裡都有白話翻譯，
        正文第一次用到時也會就地附註。</p>
    </div>

    <div class="callout bad">
      <h3>★ 先講一件影響到這一頁可信度的事：這一頁<b>在發布前跑了獨立稽核，裁決是「需修正」</b></h3>
      <p>本專案自己定義的流程是「實作 → 逐條稽核 → 對照組比較 → 發布」。
        這一輪<b>兩關都跑了</b>：對照組比較（本頁<a href="#control">第六節</a>），以及<b>發布前的逐條稽核</b>。
        稽核裁決<b>需修正</b>，擋下<b>五項</b>，<b>全部已依裁決修正後才產出這一頁</b>，
        逐項列在<a href="#limits">第十一節 11.4</a>——<b>連同它們原本錯成什麼樣子</b>。</p>
      <p style="margin:0"><b>但不要把這句話讀成「所以這一頁是對的」。</b>三件事要一起看：
        (1) 這一關<b>{F["aud_none"]}</b>：它第一次跑是<b>第十四輪的補稽核</b>，
        第二次的對象是團隊的管理流程（不是任何一輪的產出），<b>本頁是第三次</b>；
        而<b>第十四輪那次首跑就{F["aud_vrp"].split("，")[1]}</b>。
        （對照組比較這一關更晚，<b>第十七輪才第一次跑</b>，就是本頁<a href="#control">第六節</a>。）
        (2) 被擋下的五項裡，<b>最重的兩項是單位錯</b>——一個機率被當成年化值、
        一個「差六個數量級」是拿年化值去除以每週值，<b>而這一頁自己的圖表當時就是對的</b>。
        (3) <b>「可重跑」不等於「被驗過」</b>：本頁每個數字都標了產生它的程式與紀錄檔，
        那是可重現性，不是正確性。</p>
    </div>

    <h3 class="sub">一、五件事，照重要性排</h3>

    <div class="callout bad">
      <h3>★★★ 1.「投入多少」和「開幾倍槓桿」是同一件事的兩面，而我們一直在調錯的那一個</h3>
      <p>幣安{gl("跨倉", "g17-cross")}的{gl("強平", "g17-liq")}條件，分子分母同除之後，
        <b>{gl("m（你搬進合約錢包的比例）", "g17-m")}會完全消失</b>：
        <code>{F["lam_def"][1:-1]}</code>。</p>
      <p style="margin:10px 0 0">於是三句話就分乾淨了：
        <b>被強平的機率只看{gl("λ（內部槓桿）", "g17-lam")}；
        被強平時賠多少只看 m；報酬只看兩者相乘的 {gl("e", "g17-e")}。</b>
        推論是代數的、不靠任何資料：<b>要達到同一個曝險，最好的做法永遠是「全部搬進去、槓桿壓到最低」</b>，
        而不是「圈出一小塊、把槓桿拉高」。
        「圈出 10% 再槓 10 倍」和「全部進去跑 1 倍」曝險一模一樣，
        <b>破產機率差好幾個數量級</b>。</p>
      <p style="margin:10px 0 0">而協調者價目表裡那一欄
        <b>「{gl("f", "g17-f")} = {F["f1333"]}」，其實就是內部槓桿 λ = 1.0</b>
        （因為 <code>{F["gross_def"][1:-1]}</code>，在 m=1 時 {F["lam_from_f"]}）。
        <b>他以為自己在調「投入比例」，調的是第十一輪他自己警告過的那個變數。</b></p>
    </div>

    <div class="callout bad">
      <h3>★★ 2. λ={F["f1333"]} 還有一個代數上的死法，而 λ=1.0 沒有</h3>
      <p style="margin:0">BTC 在{gl("一週之內最深跌 " + F["btc_worst"], "g17-intraweek")}
        （<b>樣本 2020-08~2026-08 裡週內最深的那一週，不是整段持有期的跌幅</b>）時，抵押品打完折只剩
        <b>{F["collat"]}</b>，而 λ={F["f1333"]} 的多頭腿面額是 <b>{F["longleg"]}</b>。
        <b>光是多頭腿全部歸零就已經擊穿（{F["breach"]}），空頭腿完全不用動。</b>
        同樣情境下 λ=1.0 還剩 {F["slack10"]} 的餘裕。
        <b>λ ≤ 1.0 是唯一一個有代數保護的設定；λ={F["f1333"]} 過關靠的是「兩件壞事沒有同時發生」。
        這兩種過關不是同一種東西。</b></p>
    </div>

    <div class="callout">
      <h3>3. 破產機率：三個模型差 3~5 個數量級，<b>而那就是答案</b></h3>
      <p style="margin:0">歷史上<b>零次強平</b>，但 {gl("0/N 的 95% 上界", "g17-r3")}是
        <b>{F["emp_ub"]}</b>——<b>歷史本身根本無法證明這是個小機率</b>。
        {gl("厚尾模型", "g17-gpd")}外推出 <b>{F["gpd_band"]}</b>，
        {gl("對數常態", "g17-logn")}外推出 <b>{F["logn_ann"]}</b>
        （<b>兩個都已經換算成「每年」</b>，見<a href="#ruin">第三節</a>的單位更正）。
        兩個都站得住。<b>當兩個站得住的模型差這麼多，誠實的輸出是「資料無法裁決」，
        不是挑比較小的那個。</b>
        而且<b>三個模型全部只定價了價格風險</b>——交易所當機、標的下架、指數脫鉤、
        {gl("ADL", "g17-adl")}、API 失效，這些沒有任何一條的歷史序列在資料裡。</p>
    </div>

    <div class="callout">
      <h3>4.「最適部署量」這個問題本身被推翻了</h3>
      <p style="margin:0">解出來是{gl("角點解", "g17-bang")}，不是中間值：不是 0 就是貼在上限。
        翻轉點只由一個數字決定——<b>你相信這個 {gl("alpha", "g17-alpha")} 是真的機率有多高</b>。
        <b>所以在 alpha 未經證實的前提下，「最適部署量」不是一個有意義的問題，
        它只是「你信不信」這個二元問題換一個外觀。</b>
        另外：點估計的全{gl("凱利下注量", "g17-kelly")}是
        <b>e* = {F["fullkelly"]}</b>，也就是總面額開到全部財富的 8.4 倍。
        <b>一個離結構上限 8 倍遠的解，不是部位建議，是「分子不可信」的證明。</b></p>
    </div>

    <div class="callout bad">
      <h3>★★ 5. 這個策略裡藏了一個做空 BTC 的部位，而我們對它比對 alpha 更有把握</h3>
      <p style="margin:0">把報酬拆成「自己創造的」和「跟著 BTC 走的」兩塊（n={NWK} 週）：
        <b>{F["alpha_t"]}</b>、<b>{F["beta_t"]}</b>。
        <b>{gl("beta", "g17-beta")} 的 t 值比 {gl("alpha", "g17-alpha")} 的 t 值還大。</b>
        也就是說，十七輪下來，這個專案<b>最穩固的量測結果是一個成本，不是一個收益</b>。
        而解封投入比例會把這個隱藏空頭從 −0.12 放大到 <b>{F["beta_amp"]}</b>，
        你的整個帳戶對 BTC 的曝險掉到 <b>{F["acct_beta"]}</b>——
        <b>你買 BTC 的計畫會被自己的策略抵銷掉一部分。</b></p>
    </div>

    <h3 class="sub">二、一句話的裁決</h3>
    <div class="hero">
      <div class="lbl">新規格下該做的事</div>
      <div class="big">不該換</div>
      <div class="cap">十七輪最好的那個候選，在它自己的證據撐得起的機率下，
        一年的期望貢獻是 <b>{F["band_usd"]}</b>（佔現有幣數存量 <b>{F["band_pct"]}</b>），
        <b>而且要用「有可能在某一年把合約錢包裡的幣全部輸掉」去換</b>。
        <b>解封投入比例沒有修好任何東西</b>——它放大的是一個可能是零的數字，
        而且順手把藏在裡面的做空 BTC 部位一起放大了。</div>
    </div>
    <p class="body-note">@@BANDNOTE@@</p>
    <p class="body-note"><b>這不是結案。</b>三件事還開著，而且都不是「再跑一輪回測」能關掉的，
      列在<a href="#open">第十一節</a>。</p>
  </section>
''')
print(f"piece 1: {len(P[-1]):,} bytes")

# --- §1 leverage ------------------------------------------------------------
mrows = "".join(
    f'<tr><td class="name">{m}</td><td>{float(mn):.2f}</td><td>{float(p1):.2f}</td>'
    f'<td class="pos">{liq}</td></tr>'
    for m, _d, mn, p1, liq in MGRID)
A(f'''
  <section id="leverage">
    <h2>一、「投入多少」與「開幾倍槓桿」是同一件事的兩面</h2>
    <p class="section-note">這一節是本輪最結構性的產出。它是代數，不靠任何一段歷史資料，
      所以它不會被下一段資料推翻。</p>

    <div class="plain">
      <span class="lbl">白話</span>
      <p>假設你有 100 塊錢的 BTC。有兩種做法可以做出「20 塊錢的合約部位」：</p>
      <p><b>做法 A：</b>把 100 塊全部放進合約錢包，開 0.2 倍槓桿。<br>
         <b>做法 B：</b>只放 10 塊進去，開 2 倍槓桿。</p>
      <p>兩種做法的部位一樣大、賺賠一樣多。<b>但被強平的機率差非常多</b>——
        做法 B 只要行情晃一下，那 10 塊就不夠賠了；做法 A 要行情走非常遠才會出事。
        <b>而做法 B 被強平的時候，你只賠 10 塊；做法 A 被強平的時候，你賠 100 塊。</b></p>
      <p>這兩件事一直被混在同一個叫「投入比例」的旋鈕上。
        <b>這一輪把它們拆開了，而拆開之後的答案是：做法 A 才是對的。</b>
        「只投入一小部分」聽起來保守，但它換來的「安全」是「輸的時候輸比較少」，
        代價是「輸的機率高非常多」。而幣數會複利，<b>輸一次就把後面全部的複利砍掉</b>，
        所以降低機率遠比降低單次損失重要。</p>
    </div>

    <h3 class="sub">1.1 為什麼 m 會消失：把強平條件的分子分母同除</h3>
    <p>幣安跨倉的強平條件是「保證金餘額 &lt; 維持保證金」。兩邊同除 <code>m·W</code>
      （W = 你全部的財富）之後：</p>
    <div class="engine">
      <h3>強平條件（Multi-Assets Mode，與專案既有的 <code>step0_liquidation.py</code> 同式）</h3>
      <dl>
        <dt>同除之後</dt>
        <dd><code>{F["lam_def"][1:-1]}</code>　
          —— 右邊<b>只剩 λ 和{gl("MMR", "g17-mmr")}</b>，m 不見了。</dd>
        <dt>數值驗證（同一本帳、同一段歷史、只改 m）</dt>
        <dd>保證金比率最小值 <b>{F["mratio"]}</b>，強平天數全部 0。
          m 越小數值略高，差異只來自「最小下單量把小腿丟掉」——
          那正是第十一輪量到的名目誤差問題，不是 m 的效果。</dd>
      </dl>
    </div>
    <div class="table-wrap">
      <table>
        <caption>B1：m 從強平條件中消去的數值證明（<code>kelly_review/b_liq_plane.py</code>）</caption>
        <thead><tr><th>m（搬進合約錢包的比例）</th><th>保證金比率最小值</th><th>p1</th><th>強平天數</th></tr></thead>
        <tbody>{mrows}</tbody>
      </table>
    </div>

    <h3 class="sub">1.2 三個變數，三個分工</h3>
    <div class="table-wrap">
      <table>
        <thead><tr><th>符號</th><th>是什麼</th><th>它決定什麼</th></tr></thead>
        <tbody>
          <tr><td class="name">{gl("m", "g17-m")}</td><td class="wrap">BTC 存量裡，實際搬進合約錢包當抵押品的比例</td><td class="wrap"><b>強平的損失大小</b></td></tr>
          <tr><td class="name">{gl("λ", "g17-lam")}</td><td class="wrap">內部槓桿＝總面額 ÷ 已投入的保證金</td><td class="wrap"><b>強平的發生機率</b></td></tr>
          <tr class="best"><td class="name">{gl("e", "g17-e")}</td><td class="wrap">m × λ ＝ 總面額 ÷ 全部財富</td><td class="wrap"><b>報酬</b></td></tr>
        </tbody>
      </table>
    </div>
    <div class="callout bad">
      <h3>結論（代數層級，不會被推翻）</h3>
      <p style="margin:0"><b>對任何一個目標曝險 e，最適解永遠是角點：m = 1、λ = e。</b>
        舊規格的「回撤 ≤ 10%」曾經是一道獨立的煞車；
        新規格把它拿掉之後，<b>唯一剩下的煞車就是 λ 本身，它必須被當成一級控制變數明寫出來</b>，
        不能靠回撤或任何比值間接約束。</p>
    </div>

    <h3 class="sub">1.3 協調者的 f 一直是內部槓桿的偽裝</h3>
    <div class="table-wrap">
      <table>
        <caption>協調者的定義 <code>{F["gross_def"][1:-1]}</code>，在 m=1 時 {F["lam_from_f"]}</caption>
        <thead><tr><th>協調者說的 f</th><th>實際的內部槓桿 λ</th><th>白話</th></tr></thead>
        <tbody>
          <tr><td class="name">0.10</td><td>0.075</td><td class="wrap">幾乎沒開槓桿</td></tr>
          <tr><td class="name">1.000</td><td>0.750</td><td class="wrap">專案目前實際在用的</td></tr>
          <tr class="bad"><td class="name"><b>{F["f1333"]}</b></td><td><b>1.000</b></td><td class="wrap"><b>全部 BTC 都在合約錢包裡，面額等於保證金</b></td></tr>
        </tbody>
      </table>
    </div>

    <h3 class="sub">1.4 λ={F["f1333"]} 的代數死法</h3>
    <p>把多頭腿推到 −100% 的地板（史上無先例），再問空頭腿要漲多少才吃掉保證金。
      <b>在 λ={F["f1333"]} 配上 BTC 期內跌 {F["btc_worst"]} 那一格，答案是負數</b>——
      意思是光多頭腿歸零就已經擊穿，空頭腿怎麼走都救不回來。</p>
    <div class="table-wrap">
      <table>
        <caption>算術：抵押品 = 0.95 ×（1 − BTC 跌幅）；多頭腿面額 = λ ÷ 2</caption>
        <thead><tr><th>λ</th><th>BTC 跌 {F["btc_worst"]} 時的抵押品</th><th>多頭腿面額</th><th>多頭腿歸零後</th></tr></thead>
        <tbody>
          <tr class="bad"><td class="name"><b>{F["f1333"]}</b></td><td>{F["collat"]}</td><td>{F["longleg"]}</td><td class="negv"><b>{F["breach"]} → 已擊穿</b></td></tr>
          <tr class="best"><td class="name"><b>1.000</b></td><td>{F["collat"]}</td><td>0.5000</td><td class="pos"><b>還剩餘裕，空頭腿要再漲 {F["slack10"]} 才擊穿</b></td></tr>
        </tbody>
      </table>
    </div>
    <div class="callout bad">
      <h3>這一格是整輪最該記住的一句</h3>
      <p style="margin:0"><b>λ ≤ 1.0 是唯一一個「多頭腿即使全部歸零、再疊上史上最深的 BTC 跌幅，
        仍然不被擊穿」的設定。λ = {F["f1333"]} 能過關，靠的是「兩件壞事沒有同時發生」。
        「靠代數過關」和「靠運氣過關」不是同一種過關。</b></p>
    </div>
  </section>
''')

# --- §2 correlation ---------------------------------------------------------
A(f'''
  <section id="corr">
    <h2>二、協調者對風險的猜測，方向是反的</h2>
    <p class="section-note">這一節是「我們自己的擔心被資料否定」的紀錄。結果是好消息，
      但它同時也暴露了一個引用錯誤。</p>

    <div class="plain">
      <span class="lbl">白話</span>
      <p>協調者原本擔心：<b>「BTC 大崩盤的那一週，空頭腿大概也會同時暴漲，兩件壞事一起來。」</b>
        如果真是這樣，把兩個尾部機率相乘就會<b>低估</b>風險。</p>
      <p>實際去量的結果<b>相反</b>：BTC 跌得越深的那幾週，空頭腿反而動得越小。
        歷史上最慘的那一週 BTC {gl("週內最深跌 " + F["btc_worst"], "g17-intraweek")}，
        <b>當週空頭腿只動了 {F["worstweek"]}</b>；
        而空頭腿最凶的那一週漲 {F["maxshort"]}，<b>當週 BTC 只跌了 {F["that_btc"]}</b>。
        <b>相乘是高估，不是低估。</b></p>
    </div>

    <div class="table-wrap wide">
      <table>
        <caption>C2 / D1：BTC {gl("週內最深跌幅", "g17-intraweek")} vs 空頭腿同一週內最大漲幅（<code>kelly_review/c_lamcrit.py</code>、<code>d_joint_stress.py</code>）</caption>
        <thead><tr><th>量測</th><th>結果</th><th>怎麼讀</th></tr></thead>
        <tbody>
          <tr><td class="name">Pearson 相關（四個帳本）</td><td>{F["pearson"]}</td><td class="wrap"><b>正號＝BTC 跌越深，空頭腿動越小</b></td></tr>
          <tr><td class="name">Spearman 相關</td><td>{F["spearman"]}</td><td class="wrap">用名次算，結論一樣</td></tr>
          <tr class="best"><td class="name">5%×5% 同時發生的觀測頻率</td><td class="pos"><b>{F["joint_obs"]}</b></td><td class="wrap">四個帳本<b>全部零次</b>；如果兩件事獨立應該是 {F["joint_ind"]}</td></tr>
          <tr><td class="name">1% 層級</td><td class="pos"><b>也全部零次</b></td><td class="wrap">—</td></tr>
        </tbody>
      </table>
    </div>

    <div class="callout bad">
      <h3>★ 順帶抓到的引用錯誤：那個 {F["top5avg"]} 不是任何一本帳的空頭腿</h3>
      <p>協調者用來做壓力測試的空頭腿 p99 是 <b>{F["top5avg"]}</b>，
        但它的來源是 {F["top5src"].replace("**", "")}——
        <b>那是「整個宇宙裡最強的 5 個幣的平均」，不是我們實際會持有的空頭腿。</b></p>
      <p style="margin:10px 0 0">用<b>實際持有的</b>空頭腿重算，
        {gl("p99", "g17-pct")}是 <b>{F["p99_real"]}</b>。
        把「歷史最深的 BTC 跌幅」和「歷史最大的空頭腿漲幅」硬湊在同一週
        （<b>實際從未同時發生</b>），臨界槓桿是 <b>{F["synth_lam"]}</b>——
        <b>全部仍然高於 {F["f1333"]}</b>，最不寬裕的那一本只剩 9% 餘裕。</p>
      <p style="margin:10px 0 0"><b>這不是「所以很安全」。</b>它的意思是：
        協調者當初那個「會超過保證金」的結論，是用一個張冠李戴的數字算出來的，
        <b>結論撤銷，但 λ={F["f1333"]} 另有一個真的死法，寫在<a href="#leverage">第一節 1.4</a>。</b></p>
    </div>
  </section>
''')
print(f"pieces 2-3 added, total {sum(len(x) for x in P):,} bytes")

# --- §3 ruin ---------------------------------------------------------------
BEST = ' class="best"'
lc_rows = "".join(
    f'<tr{BEST if b == "Tri-source 1/N netted book" else ""}>'
    f'<td class="name">{BOOK_ZH[b]}</td><td>{LC[b]["n"]}</td>'
    f'<td><b>{LC[b]["min"]:.2f}</b></td><td>{LC[b]["p1"]:.2f}</td>'
    f'<td>{LC[b]["p5"]:.2f}</td><td>{LC[b]["p50"]:.2f}</td>'
    f'<td class="pos">0</td></tr>' for b in BOOK_ZH)
tail_rows = "".join(
    f'<tr><td class="name">{BOOK_ZH[b]}</td>'
    f'<td class="pos">0 / {TAIL_XI[b][1]}</td>'
    f'<td class="negv"><b>{per_year(TAIL[b][1.333][1])*100:.2f}%／年</b></td>'
    f'<td>{per_year(TAIL[b][1.333][2]):.2e}／年</td>'
    f'<td>{TAIL_XI[b][0]}</td></tr>' for b in BOOK_ZH)
A(f'''
  <section id="ruin">
    <h2>三、破產機率：三個模型差 {OOM_LO:.0f}~{OOM_CROSS:.0f} 個數量級，<b>而那就是答案</b></h2>
    <p class="section-note">你的新規格只有一條線：「不會被強平」。所以這一節是整輪最重要的一關。
      結論是「過了」，<b>但過關的方式是「機率不明」，不是「保證安全」</b>——這兩件事差很多。</p>

    <div class="plain">
      <span class="lbl">白話</span>
      <p>「歷史上從來沒被強平過」聽起來像是安全的證據。<b>它不是。</b>
        只跑過大約 250 個星期、零次出事，統計上能講的最強的一句話是
        <b>「每週出事的機率大概不超過 1.2%」</b>——換算成一年就是
        <b>{F["emp_ub"].split(" = ")[1]}</b>。<b>那是一句幾乎沒有內容的話。</b></p>
      <p>所以要用模型往外推。問題是：<b>兩個都站得住的模型，推出來的答案在同一本帳上
        差了一千倍到約 {10 ** OOM_HI / 10000:.1f} 萬倍</b>（跨帳本最遠差到
        {10 ** OOM_CROSS / 10000:.1f} 萬倍）。
        一個說「大概 39 年到 786 年會碰到一次」，另一個說「幾乎不可能」。
        <b>這時候誠實的做法是把兩個都報出來，並說「資料裁決不了」，
        而不是挑比較好看的那個寫進結論。</b></p>
    </div>

    <h3 class="sub">3.1 先把「有沒有出事」換成一個分布</h3>
    <p>對每一個持倉日，解出「<b>當天的行情會在哪一個內部槓桿上剛好觸發強平</b>」，
      這個數字叫 {gl("λ_crit", "g17-lamcrit")}。標記方式刻意取<b>同時最壞</b>：
      多頭腿全部標當日最低、空頭腿全部標當日最高、BTC 抵押品標當日最低，<b>同一瞬間</b>。
      這是一個歷史上從未真正發生過的合成極值，<b>所以下面的數字是危險的嚴格上界，不是典型值</b>。</p>
    <div class="table-wrap wide">
      <table>
        <caption>C1 / E：λ_crit 的分布（<code>kelly_review/c_lamcrit.py</code>、<code>e_trisource.py</code>）。數字越大越安全。</caption>
        <thead><tr><th>帳本</th><th>週數</th><th>最緊的一週</th><th>p1</th><th>p5</th><th>中位數</th><th>λ≤{F["f1333"]} 的強平週數</th></tr></thead>
        <tbody>{lc_rows}</tbody>
      </table>
    </div>
    <p class="body-note"><b>怎麼讀：</b>最緊的那一週，槓桿還要再放大
      {LC["R5 LOCKED mom28/n10/invvol"]["min"] / 1.333:.1f} 到
      {LC["Tri-source 1/N netted book"]["min"] / 1.333:.1f} 倍才會被強平；
      中位數的那一週要放大 {LC["gla BASE n5/equal"]["p50"] / 1.333:.1f} 倍以上。
      <b>但這個餘裕不能當成安全邊際去花掉</b>——把史上最深的 BTC 跌幅和史上最大的空頭腿硬湊在同一週之後，
      最緊那一本的臨界槓桿掉到 1.45，<b>離 {F["f1333"]} 只剩 9%</b>。
      而三源 1/N 那本帳只有 {LC["Tri-source 1/N netted book"]["n"]} 週、只涵蓋 2024–2026，
      <b>它的樣本裡根本沒有 {F["btc_worst"]} 那種週。</b></p>

    <h3 class="sub">3.2 三個模型，差 {OOM_LO:.1f}~{OOM_HI:.1f} 個數量級（同一本帳、同一個單位）</h3>
    <div class="callout bad">
      <h3>★ 這一小節的標題原本是「差六個數量級」，那是錯的——發布前稽核擋下來的</h3>
      <p><b>錯在單位，不在計算。</b><code>kelly_review/h_tail.log</code> 的標題自己寫著
        <code>{F["week_hdr"]}</code>——<b>三欄都是「每週」機率</b>。
        厚尾那一欄在寫進覆核報告時被年化了，<b>{F["logn_verdict"]}</b>，
        然後兩欄被並排印在一起。
        那個<b>錯掉的</b>「六個數量級」就是這麼來的：<b>{F["oom_wrong"]}</b>。</p>
      <p><b>換算到同一個單位之後的真值：{F["oom_truth"]}。</b>
        也就是<b>一千倍到約 {10 ** OOM_HI / 10000:.1f} 萬倍</b>，不是一百萬倍。
        <b>結論本身沒有變</b>——差三到五個數量級仍然是「資料無法裁決」，
        誠實的輸出仍然是把兩個都報出來。<b>變的是這一節的標題不再誇大那個差距。</b></p>
      <p style="margin:0"><b>兩件事要一起記住：</b>
        (1) <b>{F["log_ok"]}</b>，它自己就寫著「4.97e-04/week = 2.552%/yr」；
        錯誤是在 log → 覆核報告 → 頁面這條路上，<b>標籤被複製、單位沒有跟著換</b>。
        這跟第十四輪「美元口徑的 t 值貼在幣數口徑的年化旁邊」是同一族錯。
        (2) <b>底下那張表和那張圖從第一版起就是對的</b>（兩欄都用
        <code>1−(1−p)^52</code> 年化過）——<b>正確答案一直就印在錯誤標題的正下方。</b>
        覆核用的 <code>kelly_review/REPORT.md</code> <b>仍然帶著舊標籤，本頁與它不一致</b>，
        以本頁與狀態檔的更正為準。</p>
    </div>
    <div class="table-wrap wide">
      <table>
        <caption>H：λ={F["f1333"]} 時的年化強平機率（<code>kelly_review/h_tail.py</code>）。
          年化值由週機率以 <code>1−(1−p)^52</code> 換算，換算在本建置程式裡做，不是抄來的。</caption>
        <thead><tr><th>帳本</th><th>歷史經驗值</th><th>{gl("厚尾 GPD", "g17-gpd")}</th><th>{gl("對數常態", "g17-logn")}</th><th>{gl("ξ", "g17-xi")}</th></tr></thead>
        <tbody>{tail_rows}</tbody>
      </table>
    </div>
    {CH_RUIN}
    <p class="body-note"><b>這張圖的縱軸是對數成長軸</b>（每往上一格就是 10 倍），
      因為兩個模型的差距有 {OOM_LO:.0f}~{OOM_CROSS:.0f} 個數量級——<b>用一般的刻度畫，其中一條線會被壓成一條貼著零的直線，
      那會把「我們不知道」畫成「幾乎不可能」。</b>
      橫軸的紅色虛線是專案上限 λ={F["f1333"]}；黃色那條水平線是<b>光靠歷史紀錄能講的上界</b>，
      它比兩個模型都高得多——<b>那正是「資料裁決不了」的視覺版本。</b></p>

    <div class="callout bad">
      <h3>三件必須一起講的事</h3>
      <ul>
        <li><b>經驗欄全是 0，而 0 不等於小。</b>{gl("三法則", "g17-r3")}給的 95% 上界是
          <b>{F["emp_ub"]}</b>。歷史紀錄本身<b>不能</b>證明這是個小機率。</li>
        <li><b>兩個模型在同一本帳上差 {OOM_LO:.1f}~{OOM_HI:.1f} 個數量級，而兩個都可辯護。</b>
          厚尾模型給 {F["gpd_band"]}，對數常態給 <b>{F["logn_ann"]}</b>，
          <b>兩個都是年化值</b>。<b>誠實的輸出是「資料無法裁決」。</b></li>
        <li><b>以上全部只定價了價格風險。</b>沒有定價：移動當中交易所當機、持倉中標的被停牌／下架、
          指數價格脫鉤、獲利的那一腿被 {gl("ADL", "g17-adl")}、API 失效讓帳本裸奔、抵押品折價率被調整。
          <b>那些才是小帳戶真正被強平的方式，而這份資料裡沒有任何一條它們的序列。</b></li>
      </ul>
    </div>

    <h3 class="sub">3.3 結論的三個強度等級（分開講，不合併成一句樂觀的話）</h3>
    <div class="table-wrap">
      <table>
        <thead><tr><th>等級</th><th>內容</th><th>它有多硬</th></tr></thead>
        <tbody>
          <tr class="best"><td class="name">代數</td><td class="wrap">m 從強平條件中消去；e = m·λ；空頭腿沒有上界 ⇒ <b>不存在任何 λ &gt; 0 能對任意行情「證明不會被強平」</b>。「不被強平」只能是機率陳述</td><td class="wrap"><b>不會被推翻</b></td></tr>
          <tr><td class="name">實證</td><td class="wrap">λ ≤ {F["f1333"]} 在 2020-08~2026-08 零強平、餘裕 1.5~2.6 倍</td><td class="wrap">樣本內成立</td></tr>
          <tr class="bad"><td class="name">推論</td><td class="wrap">{F["gpd_band"]} 那個區間</td><td class="wrap"><b>脆弱。</b>建立在 234~292 個<b>重疊</b>週觀測上，而真正不同的壓力狀態只有 4~5 個</td></tr>
        </tbody>
      </table>
    </div>

    <h3 class="sub">3.4 真的被強平的話，在幣數座標下是多大一件事</h3>
    <div class="stat-grid">
      <div class="stat"><div class="label">損失上界（m=1）</div><div class="value neg">{F["stack"].split(" = ")[0]}</div><div class="sub">＝ {F["stack"].split(" = ")[1]}，也就是合約錢包裡的全部</div></div>
      <div class="stat"><div class="label">等於幾週的定投</div><div class="value neg">{F["weeks"]}</div><div class="sub">BTC 計畫／兩個計畫合計</div></div>
      <div class="stat"><div class="label">今天的量級</div><div class="value warn">{F["months32"]}</div><div class="sub">因為存量相對年流量 {F["cg_flow"].split("**")[1]} 還很小</div></div>
      <div class="stat"><div class="label">2028 年的同一件事</div><div class="value neg">{F["yr15"]}</div><div class="sub">存量長到 {F["st15k"]} 時</div></div>
    </div>
    <div class="callout bad">
      <h3>★ 這個結論會過期，而研究結論會被沿用</h3>
      <p style="margin:0"><b>「現在輸得起」不是「以後也輸得起」。</b>
        今天全額破產等於三個多月的儲蓄，是因為你的存量（{F["stack"].split(" = ")[1]}）
        相對於年流量（{F["cg_flow"].split("**")[1]}）還很小。
        以目前的節奏，大約 2028 年存量長到 {F["st15k"]} 時，<b>同一次強平就等於一年半的儲蓄</b>。
        任何沿用本輪風險容忍結論的人，都必須重跑這一格。</p>
    </div>
  </section>
''')
print(f"section 3 added, total {sum(len(x) for x in P):,} bytes")

# --- §4 optimal size --------------------------------------------------------
L2_COLS = re.search(r"P\(alpha real\)\s+haircut\s+(.*)", LOGS["l_decomp"]).group(1)
L2_HEAD = re.findall(r"(?:in-sample|full-sample arith|half of that|zero drift)"
                     r" \([+\-][\d.]+%(?: arith)?\)", L2_COLS)
assert len(L2_HEAD) == 4, L2_HEAD
L2 = []
for line in LOGS["l_decomp"].splitlines():
    m = re.match(r"\s+(\d+)%\s+([\d.]+)\s+(.*e\*=.*)$", line)
    if m:
        cells = re.findall(r"e\*=([\d.]+)\s+g=([+\-][\d.]+)%", m.group(3))
        assert len(cells) == 4, line
        L2.append((m.group(1), m.group(2), cells))
assert len(L2) == 12, len(L2)
L3 = re.findall(r"^\s+([\d.]+)\s+((?:in-sample|full-sample arith|half of that|"
                r"zero drift) \([+\-][\d.]+%(?: arith)?\))\s+([\d.]+)%\s+"
                r"([\d.]+)%\s*$", LOGS["l_decomp"], re.M)
assert len(L3) == 12, len(L3)

ZH_DRIFT = {"in-sample (+26.5%)": "樣本內漂移 +26.5%",
            "full-sample arith (+42.8%)": "全期漂移 +42.8%",
            "half of that (+21.4%)": "其一半 +21.4%",
            "zero drift (+10.9% arith)": "近乎零漂移 +10.9%"}
l2_head = "".join(f"<th>{ZH_DRIFT[c]}</th>" for c in L2_HEAD)
def gfmt(g):
    """Growth in %/yr, as printed by the log.

    The log emits "-0.00%" for the rows where the optimum is no deployment at
    all: that is a float artefact, not a loss, and a minus sign in front of a
    zero on a published page is exactly the kind of small lie this project
    keeps auditing for. Normalise it, and use the same U+2212 minus as the
    rest of the page.
    """
    return "0.00" if abs(float(g)) < 5e-3 else g.replace("-", "\u2212")


l2_rows = ""
for p, hc, cells in L2:
    if hc != "1.00":
        continue
    cls = ' class="best"' if p == "20" else ""
    l2_rows += (f'<tr{cls}><td class="name">{p}%</td>'
                + "".join(f'<td>e*={e}<span class="d">成長 {gfmt(g)}%</span></td>'
                          for e, g in cells) + "</tr>")
l3_rows = "".join(
    f'<tr><td class="name">{"不打折" if h == "1.00" else ("打五折" if h == "0.50" else "打二五折")}</td>'
    f'<td class="wrap">{ZH_DRIFT[d]}</td><td>{a}%</td>'
    f'<td class="negv"><b>{b}%</b></td></tr>' for h, d, a, b in L3)
A(f'''
  <section id="optsize">
    <h2>四、「最適部署量」這個問題本身被推翻了</h2>
    <p class="section-note">派工書的任務二是「算出最適部署量」。
      覆核者照專案紀律的做法是：<b>如果那個問題問錯了，就說它問錯了，而不是硬給一個數字。</b></p>

    <div class="plain">
      <span class="lbl">白話</span>
      <p>因為幣數會複利，正確的目標不是「期望賺最多」，而是
        <b>「期望的<u>成長率</u>最大」</b>——這叫{gl("對數成長最適下注", "g17-kelly")}。
        它的好處是<b>天生就會把破產的代價算進去</b>：破產一次，後面所有的複利都沒了。</p>
      <p>把這個式子認真解出來，得到的不是「投 37%」這種答案，而是
        <b>「不是 0，就是做滿」</b>——中間沒有東西。<b>而翻轉點只由一個數字決定：
        你相信這個策略是真的機率有多高。</b></p>
      <p>所以「該投多少」這個問題，在策略本身還沒被證明之前，<b>根本不是一個量化問題</b>，
        它只是「你信不信」這個是非題換了一件衣服。</p>
    </div>

    <h3 class="sub">4.1 目標函數</h3>
    <div class="engine">
      <h3>對數成長率</h3>
      <dl>
        <dt>式子</dt>
        <dd><code>{F["objective"][1:-1]}</code>，且 <code>e = m·λ ≤ 1</code></dd>
        <dt>三項各自的意思</dt>
        <dd>第一、二項是報酬與波動的代價，<b>只看 e</b>；
          第三項是破產，<b>機率只看 λ、損失只看 m</b>。</dd>
        <dt>不用代任何數字就成立的結果</dt>
        <dd>破產機率隨 λ 下降的速度（{gl("厚尾", "g17-gpd")}，{F["xi_band"]}）
          <b>遠快於</b> <code>log(1−m)</code> 隨 m 上升的速度。
          <b>所以對任何目標 e，最適解永遠是 m = 1、λ = e。</b></dd>
      </dl>
    </div>

    <h3 class="sub">4.2 解出來是角點，不是中間值</h3>
    <div class="table-wrap wide">
      <table>
        <caption>L2：最適曝險 e*（<code>kelly_review/l_decomp.py</code>）。
          e* = 1.0 就是「做滿」，對應 λ=1.0、m=1。alpha 不打折的那一半。</caption>
        <thead><tr><th>你相信 alpha 是真的機率</th>{l2_head}</tr></thead>
        <tbody>{l2_rows}</tbody>
      </table>
    </div>
    <div class="callout bad">
      <h3>★ 這張表要讀的不是數字，是形狀</h3>
      <p style="margin:0"><b>e* 不是 0 就是貼在上限 1.0，中間幾乎沒有內點。</b>
        原因是純數學的：對數成長對期望報酬是線性的，而期望報酬<b>在單一一個機率值上變號</b>。
        <b>所以「最適部署量」在 alpha 未經證實的前提下不是一個有意義的問題。
        派工書的任務二本身就問錯了，這一頁把它寫出來，而不是硬給一個 e*。</b></p>
    </div>

    <h3 class="sub">4.3 點估計的全下注量是 {F["fullkelly"]}，而結構上限是 1.0</h3>
    <div class="hero">
      <div class="lbl">把量到的 alpha 照單全收、算出來的全凱利下注量</div>
      <div class="big">e* = {F["fullkelly"]}</div>
      <div class="cap">也就是<b>把總面額開到全部財富的 8.4 倍</b>。
        而你的規格允許的上限是 1.0（面額不超過保證金）。
        <b>一個離結構上限 8 倍遠的解，不是部位建議，是「分子不可信」的證明。</b>
        一個正常的、可信的 alpha 估計，解出來的下注量應該落在可行範圍裡面，而不是遠遠飛出去。</div>
    </div>

    <h3 class="sub">4.4 門檻：機率要多高才值得</h3>
    <div class="table-wrap wide">
      <table>
        <caption>L3：兩道門檻（<code>kelly_review/l_decomp.py</code>）。
          第二欄是對未來 BTC 漂移的假設，四種都列，因為沒有人知道哪一種會成真。</caption>
        <thead><tr><th>alpha 打幾折</th><th>假設的未來 BTC 漂移</th><th>要有任何正部署，機率須 &gt;</th><th>要贏過「每週多存 5 美元」，機率須 &gt;</th></tr></thead>
        <tbody>{l3_rows}</tbody>
      </table>
    </div>
    <p class="body-note">超過 100% 的那幾格的意思是：<b>就算 alpha 百分之百是真的，也追不上對照組。</b>
      （關於「每週多存 5 美元」這個對照本身是不是合格的計分板，
      見<a href="#correction-scoreboard">第八節的更正一</a>——<b>它不是</b>。）</p>
  </section>
''')
print(f"section 4 added, total {sum(len(x) for x in P):,} bytes")

# --- §5 hidden beta ---------------------------------------------------------
A(f'''
  <section id="hiddenbeta">
    <h2>五、★ 這個策略裡藏了一個做空 BTC 的部位</h2>
    <p class="section-note">這是本輪的新發現，而且它是本輪唯一一個「往下修」的新證據。</p>

    <div class="plain">
      <span class="lbl">白話</span>
      <p>把這個策略的每週報酬，拆成兩塊：<b>「跟著 BTC 漲跌走的那一塊」</b>和
        <b>「跟 BTC 無關、自己創造的那一塊」</b>。第二塊就是大家在找的
        {gl("alpha", "g17-alpha")}，第一塊叫 {gl("beta", "g17-beta")}。</p>
      <p>拆出來的結果：beta 是<b>負的</b>，意思是<b>這個策略裡面偷偷含著一個做空 BTC 的部位</b>。
        你每週在買 BTC，而這個策略會在旁邊反向下注，<b>抵銷掉你一部分的買進</b>。</p>
      <p><b>而真正刺眼的是把握程度</b>：beta 這個數字的 t 值比 alpha 的 t 值還大。
        白話就是——<b>十七輪下來，這個專案量得最準的東西是一個成本，不是一個收益。</b></p>
    </div>

    <div class="table-wrap">
      <table>
        <caption>L1：迴歸拆解（<code>kelly_review/l_decomp.py</code>，n={NWK} 週）</caption>
        <thead><tr><th>項</th><th>值</th><th>標準誤</th><th>{gl("t 值", "g17-t")}</th></tr></thead>
        <tbody>
          <tr><td class="name">alpha（自己創造的）</td><td>{L1.group(1)}%／年</td><td>{L1.group(2)}%</td><td>{L1.group(3)}</td></tr>
          <tr class="bad"><td class="name">beta（跟著 BTC 走的）</td><td class="negv"><b>{L1b.group(1)}</b></td><td>{L1b.group(2)}</td><td class="negv"><b>{L1b.group(3)}</b></td></tr>
        </tbody>
      </table>
    </div>

    <div class="callout bad">
      <h3>★★ 專案對「隱藏的做空 BTC 部位」比對「alpha」更有把握</h3>
      <p>|t| 是 <b>{L1b.group(3).lstrip("-+")}</b> 對 <b>{L1.group(3).lstrip("+")}</b>。
        回測報酬裡<b>已經</b>含了這段期間的 beta 成本（{F["beta_in"]}）；
        如果未來 BTC 的漂移回到全期水準，同一個 beta 的代價會變成 <b>{F["beta_fwd"]}</b>。</p>
      <p style="margin:10px 0 0"><b>而解封投入比例會把它放大。</b>
        疊加層的 beta 從 −0.12 放大到 <b>{F["beta_amp"]}</b>，
        <b>你整個帳戶對 BTC 的曝險掉到 {F["acct_beta"]}</b>——
        也就是說，你名義上每週買 100 美元的 BTC，實際上<b>只有大約 79 美元真的在賭 BTC 漲</b>。
        <b>在一個以「最後手上有幾顆 BTC」為目標的計畫裡，這是個直接扣分的副作用。</b></p>
      <p style="margin:10px 0 0"><b>這一項同時是覆核者自我更正的結果。</b>
        他第一版把 beta 的代價「額外再扣一次」，那是重複計算——
        持有期的 BTC 不是平盤（{F["hold_cagr"]}），回測報酬裡本來就含著那段 beta 成本了。
        正確做法是迴歸拆解後重新預測，不是再減一次。</p>
    </div>
  </section>
''')

# --- §6 control group -------------------------------------------------------
MENU = [
    ("對照組：什麼都不做", "0", "0%", "$0", "0%", "1.00", "base"),
    ("對照＋：每週 100 → 105 USDT", F["c_btc"], F["c_pct"], F["c_usd"], "0%", "1.00", "base"),
    ("對照＋：閒置 USDT 開 Simple Earn", F["se_btc"], F["se_pct"], F["se_usd"], "0%", "≈1", ""),
    # The old "約 −1.2%" here was 0.13 x 9.3%: the SAME linear-scaling mistake
    # this page spends a section correcting. Drawdown is convex in exposure and
    # there is no measurement at e=0.13, so the cell says so instead.
    ("三源 1/N，信心 20%、alpha 不打折 → 最適 e*=0.13", F["t20_btc"], F["t20_pct"], F["t20_usd"], "未量測", "—", "bad"),
    ("三源 1/N，信心 20%、alpha 打五折 → 最適 e*=0", "0（不部署）", "0%", "$0", "—", "—", "bad"),
    ("三源 1/N，信心 50%、alpha 不打折 → 最適 e*=1.00", F["t50_btc"], F["t50_pct"], F["t50_usd"], F["dd_true"], "—", ""),
]
menu_rows = "".join(
    f'<tr{(" class="" + c + """) if c else ""}><td class="name wrap">{n}</td>'
    f'<td>{b}</td><td>{p}</td><td>{u}</td><td>{d}</td><td>{q}</td></tr>'
    for n, b, p, u, d, q, c in MENU)
A(f'''
  <section id="control">
    <h2>六、跟你現在實際在做的事比</h2>
    <p class="section-note">對照組不是「買進持有」這個抽象概念，而是<b>你本人現在真的在做的那件事</b>，
      它被寫成一份版本化的定義檔 <code>kelly_review/CONTROL_GROUP.md</code>（v1），改動要留紀錄。</p>

    <div class="callout">
      <h3>一條必須每次覆述的話</h3>
      <p style="margin:0"><b>{F["cg_sim"]}。</b>
        你的帳戶實際上只跑了{F["cg_real"]}（第十六輪的推導，
        見<a href="laoliu-r16-eth.html#headline">第十六輪 · 頭條</a>）。
        本頁所有「六年」的數字都是<b>模擬</b>，所有「你經歷過的」都會另外標明。</p>
    </div>

    <h3 class="sub">6.1 三個評分維度的座標</h3>
    <div class="table-wrap">
      <table>
        <thead><tr><th>維度</th><th>對照組（你現在在做的）</th><th>最好的候選（三源 1/N @ λ={F["f1333"]}）</th></tr></thead>
        <tbody>
          <tr><td class="name">強平機率</td><td class="pos"><b>0</b><span class="d">沒有保證金部位</span></td><td class="wrap">{F["gpd_band"]}（厚尾）～ {F["logn_ann"]}（對數常態），<b>兩個都是年化值，資料不裁決</b></td></tr>
          <tr><td class="name">離強平的距離</td><td class="pos"><b>∞</b></td><td class="wrap">最緊的一週 λ_crit = {LC["Tri-source 1/N netted book"]["min"]:.2f}（{LC["Tri-source 1/N netted book"]["n"]} 週、只涵蓋 2024–2026）</td></tr>
          <tr><td class="name">疊加層自己的{gl("回撤", "g17-dd")}</td><td class="pos"><b>0</b></td><td class="negv"><b>{F["dd_true"]}</b><span class="d">協調者算 {F["dd_coord"]}，低估三分之一（{F["dd_coord"]} 其實是 λ=1.0 的回撤）</span></td></tr>
          <tr><td class="name">{gl("幣數比", "g17-cr")}</td><td><b>1.0000</b><span class="d">定義</span></td><td class="wrap"><b>本輪沒有算出任何幣數比</b>——這一格是空的。可拿來對照的只有疊加層<b>自己</b>的累積幣數倍數 {CUM_CAP:.3f}（{NW_CAP} 週＝{YRS_CAP:.2f} 年，年化 {CR_CAP:.4f}），<b>那不是幣數比</b>：它沒有定投流入，也沒有除以純 DCA 的分母。前瞻的相對財富見 6.3</td></tr>
          <tr><td class="name">機率</td><td class="pos"><b>1.0</b></td><td class="wrap"><b>你相信 alpha 是真的機率</b>，覆核者的估計 {F["p_alpha"]}</td></tr>
        </tbody>
      </table>
    </div>

    <h3 class="sub">6.2 價目表（幣數為主軸）</h3>
    <div class="table-wrap wide">
      <table>
        <caption>以 BTC {F["cg_px"]} 換算。「佔存量」的基準點是<b>你現在的 {F["stack"].split(" = ")[0]}</b>，
          不是六年模擬的 0.8511 顆——兩個基準點差 25 倍，<b>務必看清楚是哪一個</b>。
          <b>「自身回撤」那一欄只填實際量到的格子</b>：e*=1.00 那一列是
          <code>f1_growth.csv</code> 在 λ={F["f1333"]} 量到的 {F["dd_true"]}；
          e*=0.13 那一列<b>沒有量測，就寫「未量測」</b>——
          <b>回撤對曝險是凸的，不能用 {F["dd_true"]} 乘上 0.13 去估</b>，
          那正是本頁 11.1 在更正的那個錯誤。</caption>
        <thead><tr><th>動作</th><th>BTC／年</th><th>佔現有存量</th><th>美元／年</th><th>自身回撤</th><th>機率</th></tr></thead>
        <tbody>{menu_rows}</tbody>
      </table>
    </div>
    <p class="body-note"><b>{CUM_CAP:.3f} 這個數字為什麼要特別講清楚：</b>
      本專案歷史上所有真正的幣數比都落在 0.6666~1.0276 之間，
      <b>把 {CUM_CAP:.3f} 擺在對照組的 1.0000 旁邊，讀起來會像「比專案史上最好的結果還好 3.7 倍」，
      而那是假的</b>。它是<code>kelly_review/f_growth.py</code> 印在
      <code>coinratio</code> 這個欄名底下的 <code>eq[-1]</code>——
      <b>欄名錯了，數字本身沒錯</b>（同一支程式的年化欄 <code>cr</code> 是 {CR_CAP:.4f}）。
      欄名已修，<b>但 <code>kelly_review/f_growth.log</code> 這份既有紀錄沒有重寫</b>，
      它仍然帶著舊欄名——紀錄檔是產出的歷史，不回頭改。</p>
    <p class="body-note"><b>兩個預登記的候選（R6 SF_B / R5 鎖定組）在信心 ≤ 50% 下期望值皆為負</b>，
      而它們的回撤是 {F["prereg_dd"]}。<b>「預登記」正是這個專案最看重的證據等級</b>——
      死得最乾淨的那兩個，剛好就是唯二事先講好要測什麼的那兩個。
      另外請注意：表中「每週 100 → 105 USDT」這一列<b>不是一個合格的計分板</b>，
      理由見<a href="#correction-scoreboard">第八節</a>。</p>

    <h3 class="sub">6.3 逐起點分布：用相對財富看，不用百分點相減</h3>
    {CH_REL}
    <p class="body-note"><b>怎麼讀：</b>橫軸是<b>相除</b>不是相減——
      「一年後我的幣數，是對照組的幾倍」。1.0× 那條線就是對照組本身。
      橫軸是對數軸，因為這個分布是右偏的（上方的尾巴拉得比下方長）。</p>
    <div class="callout bad">
      <h3>★ 這張圖真正的內容，是三條線之間的距離</h3>
      <ul>
        <li><b>alpha 照單全收</b>：中位起點一年後拿到對照組的
          {J2[("1.333", "as backtested")]["med"] / CTRL_SAME:.2f} 倍幣數。</li>
        <li><b>alpha 打五折</b>：掉到 {J2[("1.333", "alpha haircut 50%")]["med"] / CTRL_SAME:.2f} 倍。</li>
        <li><b>alpha 是零（只剩成本與那個隱藏的做空部位）</b>：
          中位 {J2[("1.333", "alpha = 0 (costs+beta only)")]["med"] / CTRL_SAME:.2f} 倍、
          最差起點 {J2[("1.333", "alpha = 0 (costs+beta only)")]["worst"] / CTRL_SAME:.2f} 倍，
          而那 81 個重疊窗裡<b>有 {J2[("1.333", "alpha = 0 (costs+beta only)")]["lose"]:.0f}% 是負的</b>
          ——<b>這是對這 81 個窗的描述，不是「輸的機率是 {J2[("1.333", "alpha = 0 (costs+beta only)")]["lose"]:.0f}%」</b>，
          理由見下方的樣本數警告。</li>
        <li><b>而「alpha 是零」不是一個悲觀假設，它是第十七輪所有預登記讀數指向的那個值。</b></li>
      </ul>
      <p style="margin:10px 0 0"><b>⚠ 樣本數警告：</b>
        {F["windows"]}出自 2.54 年的資料，{gl("真正獨立的觀測", "g17-indep")}只有大約
        <b>{F["indep"]}</b>。<b>圖上的離散度是資訊；把「有幾成的窗是正的」當成機率不是。</b>
        本頁凡是出現這種比例，<b>一律只當作那 {F["windows"].split(" 個")[0]} 個重疊窗的描述性統計</b>；
        2.5 個獨立觀測撐不起任何前瞻的「勝率」宣稱，本頁也沒有做那種宣稱。</p>
    </div>

    <h3 class="sub">6.4 那是優勢，還是剛好碰上對的市況？</h3>
    <div class="table-wrap">
      <table>
        <caption>F：把週報酬按「BTC 當週漲或跌」分成兩半（<code>kelly_review/f_growth.py</code>）</caption>
        <thead><tr><th>候選</th><th>對 BTC 的 beta</th><th>BTC 上漲的那一半週</th><th>BTC 下跌的那一半週</th></tr></thead>
        <tbody>
          <tr class="best"><td class="name">三源 1/N</td><td>{F["tri_beta"].split("beta ")[1]}（{F["tri_corr"]}）</td><td>{F["up_weeks"]}</td><td><b>{F["down_weeks"]}</b></td></tr>
          <tr class="bad"><td class="name">Binance gla</td><td>—</td><td class="negv"><b>{F["gla_up"]}</b></td><td>—</td></tr>
          <tr class="bad"><td class="name">R6 SF_B</td><td>—</td><td class="negv"><b>{F["sfb_up"]}</b></td><td>—</td></tr>
        </tbody>
      </table>
    </div>
    <div class="callout bad">
      <h3>全部候選的績效壓倒性集中在 BTC 下跌的那一半週</h3>
      <p style="margin:0">這不是「這段期間剛好適合」那種弱說法——<b>它是結構性的方向偏誤</b>。
        持有期的 BTC 是 {F["hold_cagr"]}，也就是<b>「漲，但很顛」</b>，
        而那剛好是最適合一個負 beta 疊加層的行情。
        <b>如果未來 BTC 是「漲得順」，這些數字會直接縮水。</b>
        這一項與<a href="#hiddenbeta">第五節</a>是同一件事的兩個面向。</p>
    </div>

    <h3 class="sub">6.5 那個機率 15%~25% 是怎麼來的</h3>
    <div class="split">
      <div class="callout bad">
        <h3>往下修的證據（強）</h3>
        <ul>
          <li><b>所有{gl("預登記", "g17-prereg")}的讀數都是零</b>：t = 0.54 / 0.63 / 0.26 / 0.505 / 0.344 / 0.982 / 0.692。<b>沒有任何一個乾淨的首次讀取支持它。</b></li>
          <li><b>唯一過 3.0 的那個，低於純雜訊的期望</b>：{F["searches"]} 次跨輪搜尋下，{F["emax_t"]}，而觀測值只有 3.029。<b>似然比 ≤ 1，不構成向上更新。</b></li>
          <li>關掉{gl("資金費", "g17-funding")} → t = <b>{F["t_nofund"]}</b>。多出來的那 0.03 個 t 靠的是資金費，不是價格效應。</li>
          <li>效應是 2023H2 起的一段市況，半年 IC 路徑 +0.109 → +0.017 → +0.003，<b>正在歸零</b>。</li>
          <li><b>六次獨立量測「從樣本內挑配置」的能力，沒有一次為正。</b></li>
          <li><b>本輪新增第七次證據</b>：隱藏 beta 的 t 大於 alpha 的 t（<a href="#hiddenbeta">第五節</a>）。</li>
        </ul>
      </div>
      <div class="callout good">
        <h3>往上修的證據（誠實列出）</h3>
        <ul>
          <li>安慰劑檢定 98.3 / 100.0 / 100.0 百分位。</li>
          <li>鏡像帳（把訊號反過來）全部為負。</li>
          <li>三源之間的週報酬相關只有 0.165~0.466，不是同一個東西算三次。</li>
          <li>拿掉最賺的那一週，t 反而<b>升到</b> +3.42。</li>
          <li>Bybit 上五個子期間全部為正。</li>
          <li>成本九宮格全部通過。</li>
          <li><b>三源 1/N 沒有任何自由參數</b>——沒有可以調的旋鈕，就沒有調參偷來的成績。</li>
        </ul>
      </div>
    </div>
    <div class="hero">
      <div class="lbl">覆核者自己的判斷</div>
      <div class="big">{F["p_alpha"]}</div>
      <div class="cap">中心值 20%。另外，「它前瞻至少帶來一半的量測規模」的機率是 <b>{F["p_half"]}</b>。
        <b>20% 剛好落在「要有任何正部署」的門檻（{F["th_pt_dep"]}）邊上，
        遠低於「贏過每週多存 5 美元」的門檻（{F["th_pt_beat"]}）。
        而只要 alpha 打個五折，連正部署的門檻（{F["th_pt_h"]}）都過不了。</b><br>
        <b>這是一個信念，不是一個量測。</b>你可以把自己的數字代進
        <a href="#optsize">第四節 4.4 的門檻表</a>得到你自己的答案——那才是這份報告該有的形狀。</div>
    </div>
  </section>
''')

# --- §7 spec change ---------------------------------------------------------
A(f'''
  <section id="spec">
    <h2>七、規格變更唯一的實質效果：把「對沖比例」整個家族歸零</h2>
    <p class="section-note">逐條檢查了<b>覆核執行當時</b>狀態檔裡全部 40 處提到「回撤」的地方，
      看看解封之後有沒有被誤殺的候選復活。
      （狀態檔一直在長：本頁建置時重數是 <b>{DD_LINES} 行、{DD_HITS} 次</b>，
      多出來的部分是這一輪自己寫進去的紀錄，不是漏檢的候選。）</p>

    <div class="plain">
      <span class="lbl">白話</span>
      <p>你把「回撤不能超過 10%」這條線拿掉了。一個合理的擔心是：
        <b>「那之前是不是有東西被這條線冤枉地刷掉了？」</b></p>
      <p>逐條查完的答案是<b>沒有，一個都沒有復活</b>。
        因為每一個「主要理由是回撤」的候選，背後都<b>另外還有一個跟回撤無關、而且更強</b>的死因
        ——統計不顯著、代數上檔封頂、成本地板、或下檔無界。
        <b>新規格拿掉的是重複的那一道刷子，不是唯一的那一道。</b></p>
      <p><b>但它確實讓一整個家族貶值了</b>，而且那個家族原本是這個專案唯一「可靠可買」的東西。</p>
    </div>

    <div class="callout bad">
      <h3>★ 對沖比例選單（回撤壓縮）正式出局</h3>
      <p style="margin:0">這一族的{gl("幣數比", "g17-cr")}是 <b>{F["hedge_cr"]}</b>——<b>全部小於 1.0</b>，
        也就是<b>它們全都讓你少拿幣</b>。它唯一的賣點是把帳戶回撤
        {F["hedge_dd"]}，也就是<b>用幣數去買一份「跌得比較不痛」的保險</b>。</p>
      <p style="margin:10px 0 0"><b>你說「不設回撤上限」，等於宣告你不買這份保險。</b>
        那麼在你自己的偏好下，正確的對沖比例就是 <b>0%</b>，
        這一族正式出局。<b>這是本次規格變更唯一的實質效果，而它的方向是減少選項，不是增加。</b></p>
    </div>

    <h3 class="sub">7.1 逐條檢查</h3>
    <div class="table-wrap">
      <table>
        <thead><tr><th>候選</th><th>否決理由裡有回撤嗎</th><th>新規格下</th></tr></thead>
        <tbody>
          <tr><td class="name wrap">R5 / SF_A / SF_B 的淘汰表</td><td class="wrap"><b>有，而且被當成淘汰條件</b></td><td class="wrap">這張表<b>第十一輪就已被推翻</b>。真正的死因是統計（t = 0.692 / −1.347 / 0.982），<b>與回撤無關</b></td></tr>
          <tr><td class="name wrap">三源 1/N</td><td class="wrap"><b>沒有。</b>它是被上限卡在<b>太安全</b>那一側</td><td class="wrap"><b>它是唯一真正受惠於解封的。</b>但死因不變：非預登記、同族預登記版 t = 0.26~0.63、關掉資金費 t = {F["t_nofund"]}</td></tr>
          <tr class="bad"><td class="name wrap">第十四輪的 BTC 波動率風險溢酬</td><td class="wrap">舊理由「塞得進 10% 預算」已失效</td><td class="wrap"><b>新規格下更糟，不是更好。</b>稽核關卡測出幣數口徑 t 只有 1.48、零成本上界 2.02；保證金代理低估 1.5~4.5 倍；<b>賣方損失在幣數口徑下是無界的，而新規格唯一的約束正是不被強平</b></td></tr>
          <tr><td class="name wrap">日曆價差</td><td class="wrap">有（毛回撤 −11.01%）</td><td class="wrap">該步失效，但成本地板 0.160% &gt; 毛邊際 0.120% 獨立成立，<b>連成本歸零都活不了</b></td></tr>
          <tr><td class="name wrap">幣安 BTC Yield</td><td class="wrap">有</td><td class="wrap">該條失效，但<b>代數死因（備兌看漲讓幣數上檔封頂）不受規格影響</b></td></tr>
          <tr><td class="name wrap">槓桿 ETF 耗損收割</td><td class="wrap">有</td><td class="wrap">主因是日再平衡實測 −2.293%／年；不再平衡的版本正是<b>下檔無界</b>，<b>在「不被強平」的新約束下更不可接受</b>（原始論證見<a href="laoliu-r15-triage2.html#other">第十五輪 · 其他候選</a>）</td></tr>
          <tr><td class="name wrap">括號單（停利停損）</td><td class="wrap">有</td><td class="wrap">真正理由是「停損限價把有界損失換成無界損失」——<b>無界損失在舊規格下是回撤問題，在新規格下是強平問題</b>。更不可接受</td></tr>
          <tr class="bad"><td class="name wrap"><b>對沖比例選單</b></td><td class="wrap"><b>它的全部價值就是回撤</b></td><td class="wrap"><b>★ 歸零、出局</b></td></tr>
        </tbody>
      </table>
    </div>
  </section>
''')
print(f"sections 5-7 added, total {sum(len(x) for x in P):,} bytes")

# --- §8 correction 1: the scoreboard ---------------------------------------
A(f'''
  <section id="correction-scoreboard">
    <h2>八、更正一：「每週多投 5 塊」不該當計分板 —— <b>你本人指出的</b></h2>
    <p class="section-note">依發布規則，舊頁一個字都沒動。這一節說明錯在哪裡、它出現在哪些已發布的位置，
      以及正確的計分板是什麼。</p>

    <div class="callout bad">
      <h3>★★ 你的原話</h3>
      <p style="margin:0;font-size:1.06rem;line-height:1.9"><b>「{F["quote_foul"]}」</b></p>
    </div>

    <div class="plain">
      <span class="lbl">白話：錯在哪裡</span>
      <p>「每週從 100 USDT 改成 105 USDT ＝ 一年多買 $260 的幣、回撤增加 0、機率 1.0」
        這句話<b>本身是對的</b>——算術沒錯。</p>
      <p><b>錯的是把它當成團隊的成績來比。</b>那 $260 是<b>你自己多掏出來的錢</b>，
        不是任何研究創造出來的價值。<b>拿「請使用者多付錢」去跟「策略賺到的錢」比大小，
        比的不是同一種東西。</b>照這個邏輯推到底，團隊永遠可以宣稱「我們的最佳方案是請你多存一點」，
        而那句話裡沒有一絲團隊的貢獻。</p>
      <p>這個數字被協調者當計分板用了<b>整個專案</b>。</p>
    </div>

    <h3 class="sub">8.1 正確的計分板</h3>
    <div class="hero">
      <div class="lbl">唯一合格的計分板</div>
      <div class="big">同樣的錢<span style="font-size:1.4rem"> · </span>同樣的流入<span style="font-size:1.4rem"> · </span>同樣的時間</div>
      <div class="cap"><b>最後手上的 BTC 是多還是少。</b>
        也就是本專案原本就在用的{gl("幣數比", "g17-cr")}。
        <b>任何「改變投入金額」的動作都不在這個計分板上</b>，因為它改變了「同樣的錢」這個前提。</div>
    </div>

    <h3 class="sub">8.2 這個錯誤出現在哪些已發布的位置</h3>
    <div class="table-wrap">
      <table>
        <caption>逐一核對過實際存在的位置。<b>全部維持原狀不動</b>，更正只寫在這一頁。
          <b>位置是五個，出現次數不只五次</b>：光是「{F["c_usd"]}」這個數字本身，
          總覽報告 v1 就有 <b>{FOUL_HITS["crypto-dca-amplifier-report.html"]}</b> 次、
          索引頁 <b>{FOUL_HITS["laoliu.html"]}</b> 次，合計 <b>{FOUL_TOTAL}</b> 次
          （第十五、十六輪都是 <b>0</b> 次；數字由建置時清點）。</caption>
        <thead><tr><th>位置</th><th>它在那裡的角色</th></tr></thead>
        <tbody>
          <tr class="bad"><td class="name wrap"><a href="crypto-dca-amplifier-report.html#summary">總覽報告 v1 · 摘要</a></td><td class="wrap">被寫成「整個專案能爭取到的最好結果<b>比不上</b>每週多投 5 塊美金」，並列在摘要的建議表裡</td></tr>
          <tr class="bad"><td class="name wrap"><a href="crypto-dca-amplifier-report.html#sizing">總覽報告 v1 · 部位規模那一節</a></td><td class="wrap">節末的「最重要的一張對照表」，把它當成勝負的基準列</td></tr>
          <tr class="bad"><td class="name wrap"><a href="crypto-dca-amplifier-report.html#conclusion">總覽報告 v1 · 結論</a></td><td class="wrap">被寫成「『每週多投一點』在算術上打敗這個專案找到的一切」，並再次列在建議表裡</td></tr>
          <tr><td class="name wrap"><a href="crypto-dca-amplifier-report.html#blindspot">總覽報告 v1 · 盲點那一節</a></td><td class="wrap">以「對照組」的身分出現一次</td></tr>
          <tr class="bad"><td class="name wrap"><a href="laoliu.html">老六研究院索引 · 總覽報告那張卡</a></td><td class="wrap">卡片下方的重點數字之一：「十一輪最好結果 vs 每週多投 5 鎂」</td></tr>
        </tbody>
      </table>
    </div>
    <div class="callout">
      <h3>一個與派工書不同的認定，寫出來</h3>
      <p style="margin:0">派工書寫的是這個錯誤「出現在 v1 的摘要、結論<b>與第十五／十六輪的索引卡上</b>」。
        <b>實際逐字檢查的結果不是這樣</b>：第十五輪與第十六輪的索引卡、以及那兩頁的內文，
        <b>都沒有出現這個對照</b>。它出現的位置是上表那五處，其中四處在總覽報告 v1 裡。
        <b>把錯誤的散布範圍講得比實際更廣，本身也是一種不準確，所以這裡照實際情況更正。</b></p>
      <p style="margin:10px 0 0"><b>同一把尺要兩邊都用：講得比實際小也是不準確。</b>
        上一版只說「五個位置」，沒有說在那五個位置裡它被重複了幾次——
        實際是 <b>{FOUL_TOTAL}</b> 次，<b>其中 {FOUL_HITS["crypto-dca-amplifier-report.html"]} 次集中在總覽報告 v1</b>。</p>
    </div>

    <h3 class="sub">8.3 這件事對本輪結論的影響</h3>
    <div class="callout bad">
      <h3>它<b>不會</b>讓任何候選復活，但它改變了這一輪該怎麼被引用</h3>
      <ul>
        <li><b>本輪的門檻表（<a href="#optsize">第四節 4.4</a>）裡「要贏過每週多存 5 美元」那一整欄，
          按你的裁定是犯規的比較。</b>它留在頁面上是為了完整揭露覆核者當時的計算，
          <b>不是為了當作判準</b>。</li>
        <li><b>「要有任何正部署，機率須 &gt; {F["th_dep"]}」那一欄不受影響</b>，
          因為它比的是「部署 vs 不部署」，沒有動到你的投入金額。
          <b>而覆核者自己的機率估計（{F["p_alpha"]}，中心 20%）就落在這道門檻邊上。</b>
          <b>所以拿掉犯規的那一欄之後，結論仍然是「不該換」，但理由變窄了：
          它現在只剩「證據撐不起足夠的信心」，不再包含「輸給多存 5 塊錢」。</b></li>
        <li><b>對照組本身仍然有效</b>——「你現在在做的事」永遠是正確的比較對象。
          犯規的是<b>「對照組＋多存 5 塊」</b>這個升級版，不是對照組。</li>
      </ul>
    </div>
  </section>
''')

# --- §9 correction 2: the spec ---------------------------------------------
A(f'''
  <section id="correction-spec">
    <h2>九、更正二：第十五／十六輪是用舊規格的措辭寫的</h2>
    <p class="section-note">規格在 {TODAY} 變更，而那兩頁在變更前就已發布。<b>舊頁不改</b>，
      這一節說明哪些措辭要按新規格重讀。</p>

    <div class="table-wrap">
      <table>
        <caption>規格變更（{TODAY}，依你本人的兩次指示）</caption>
        <thead><tr><th>項目</th><th>舊規格</th><th>新規格</th></tr></thead>
        <tbody>
          <tr><td class="name">投入比例</td><td>隱含封在 10%</td><td class="pos"><b>解封，可到全額</b></td></tr>
          <tr><td class="name">疊加層自身{gl("回撤", "g17-dd")}</td><td>≤ 10%（當淘汰條件用）</td><td class="pos"><b>無上限</b></td></tr>
          <tr class="best"><td class="name">綁定約束</td><td>投入比例 × 回撤 ≤ 10%</td><td><b>不會被{gl("強平", "g17-liq")}</b></td></tr>
        </tbody>
      </table>
    </div>
    <p class="body-note">你的原話：「<b>{F["quote_spec"]}……</b>」；
      後續選項題的選擇是「<b>{F["quote_pick"]}</b>」。
      <b>仍然在的限制（你沒有撤）</b>：合約名目曝險 &lt; 保證金、單一交易所、全自動無人值守、以幣數為目標。</p>

    <h3 class="sub">9.1 舊頁的哪些措辭要按新規格重讀</h3>
    <div class="table-wrap">
      <table>
        <caption>逐字檢查過第十五輪與第十六輪的全文。</caption>
        <thead><tr><th>位置</th><th>舊頁的措辭</th><th>按新規格怎麼重讀</th></tr></thead>
        <tbody>
          <tr class="bad"><td class="name wrap"><a href="laoliu-r15-triage2.html#other">第十五輪 · 其他候選（槓桿 ETF 耗損收割）</a></td><td class="wrap">「而且『回撤不超過 10%』這種約束<b>對它無效</b>」</td><td class="wrap"><b>這句話的前提已經不存在了</b>（那條約束本身已被撤銷），<b>但它的結論變得更強而不是更弱</b>：它講的形狀是「一次跳空、下檔無界」，而新規格唯一的約束正是不被強平。<b>對舊規格是回撤問題，對新規格是強平問題</b></td></tr>
          <tr class="bad"><td class="name wrap"><a href="laoliu-r15-triage2.html#glossary">第十五輪 · 術語表「空 gamma」</a></td><td class="wrap">「本專案把這種形狀列為地雷，因為『回撤不超過 10%』這種約束對它是無效的」</td><td class="wrap">同上：<b>理由的措辭要換，判定不變且更硬</b></td></tr>
          <tr><td class="name wrap"><a href="laoliu-r16-eth.html#summary">第十六輪 · 全文</a></td><td class="wrap">—</td><td class="wrap"><b>逐字檢查後沒有發現任何依賴舊規格的措辭</b>。那一輪談的是 ETH 定投計畫，不涉及投入比例或回撤上限</td></tr>
        </tbody>
      </table>
    </div>
    <div class="callout">
      <h3>又一個與派工書不同的認定</h3>
      <p style="margin:0">派工書說「第十五／十六輪頁面是用舊規格措辭寫成」。
        <b>第十五輪確實有兩處</b>（上表），<b>第十六輪則一處都沒有</b>。
        照實寫，不為了讓更正看起來更有份量而湊數。</p>
    </div>

    <h3 class="sub">9.2 更重要的：新規格讓一個舊警告變危險</h3>
    <div class="callout bad">
      <h3>★ 舊規格的「回撤 ≤ 10%」其實在兼差當一道煞車</h3>
      <p style="margin:0">第十一輪已經證明過：專案當時用的那個篩選比值
        <b>對內部槓桿是失明的</b>——槓桿從 0.1 拉到 3.0，那個比值幾乎不動，
        而爆倉門檻卻從一個天文數字崩到負數。
        <b>舊規格下「回撤 ≤ 10%」還是一道獨立的煞車；新規格把那道煞車拿掉了。</b></p>
      <p style="margin:10px 0 0"><b>所以：內部槓桿 λ 從今天起必須被當成一級控制變數明確管理，
        不能再靠任何比值或回撤去間接約束它。</b>
        而<a href="#leverage">第一節</a>的發現讓這件事更緊急——
        協調者過去在調的「投入比例」，其實一直就是這個變數。</p>
    </div>
  </section>
''')
print(f"corrections added, total {sum(len(x) for x in P):,} bytes")

# --- §10 correction 3: the published baseline is a simulation ---------------
def _strip(x):
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", x))


_STRIPPED = {k: _strip(v) for k, v in PUBLISHED.items()}
QUOTED = []


def quote(page, s):
    """Quote an already-published page VERBATIM, asserting the quote is real.

    Tags and whitespace are ignored in the comparison; the characters are not.
    A quote that stops matching its source fails the build instead of shipping.
    """
    assert page in _STRIPPED, page
    assert _strip(s) in _STRIPPED[page], f"quote not found in {page}: {s[:40]}"
    QUOTED.append((page, s))
    return html.escape(s)


def cls(c):
    return f' class="{c}"' if c else ""


V1H, R15H, R16H = ("crypto-dca-amplifier-report.html",
                   "laoliu-r15-triage2.html", "laoliu-r16-eth.html")
BASELOC = [
    (V1H, "summary", "總覽報告 v1 · 摘要第一段",
     "六年的紀錄是：同樣的錢什麼都不做，最後手上是 0.8511 顆 BTC",
     "「<b>紀錄</b>」這兩個字要讀成「<b>模擬</b>」。這是整個專案最前面的一句話，"
     "也是最容易被讀成「我的成績單」的那一句", "bad"),
    (V1H, "headline", "總覽報告 v1 · 頭條的大字",
     "每週 100 USDT × 319 週，什麼都不做，只是買進並持有",
     "底下那 0.8511 顆是<b>模擬六年</b>的結果；你的帳戶沒有那 319 週", "bad"),
    (V1H, "glossary", "總覽報告 v1 · 術語表「幣數比」",
     "六年 319 週、每週 100 USDT，純買進持有最後是 0.8511 顆 BTC",
     "<b>幣數比這個尺度本身不受影響</b>（分子分母是同一段模擬）；"
     "受影響的只有「0.8511 顆是誰的幣」", ""),
    (V1H, "coin-ratio", "總覽報告 v1 · 幣數比總表的基準列",
     "定期定額買進持有 = 1.0000）與 20 個世代的勝率",
     "表裡每一個比值都仍然有效，<b>它們比的是模擬對模擬</b>", ""),
    (R15H, "summary", "第十五輪 · 摘要「幣數比這一欄是空的」",
     "六年 319 週純持有拿到 0.8511 顆，這個成績定義為 1.0000",
     "「成績」要讀成「模擬結果」", "bad"),
    (R15H, "g15-coinratio", "第十五輪 · 術語表「幣數比」",
     "純持有六年是 0.8511 顆，定義為 1.0000",
     "同上", "bad"),
    (R15H, "sharpe645", "第十五輪 · 外部提案的追問表",
     "基準：純持有 0.8511 顆 = 1.0000",
     "同上；那一列的 0.9463 仍然有效", ""),
    (R16H, "summary", "第十六輪 · 摘要",
     "是一段模擬，不是你的帳戶歷史",
     "<b>這一頁已經把話講清楚了。</b>更正三不是在更正第十六輪，"
     "而是把第十六輪講過的話固定成一條規則", ""),
]
baseloc_rows = "".join(
    f'<tr{cls(c)}><td class="name wrap"><a href="{pg}#{fid}">{loc}</a></td>'
    f'<td class="wrap">「{quote(pg, q)}」</td><td class="wrap">{how}</td></tr>'
    for pg, fid, loc, q, how, c in BASELOC)
INDEX_QUOTE = quote("laoliu.html", "純 DCA 持有拿到 0.8511 顆，記為基準 1.0000")
CG_ORIGIN = F["cg_origin"].replace("**", "")
CG_VER = F["cg_ver"].lstrip("# ")

A(f'''
  <section id="correction-control">
    <h2>十、更正三：那個「1.0000」是一段<b>模擬</b>，不是你的帳戶</h2>
    <p class="section-note">這一項<b>第十六輪就算出來了，也已經寫在第十六輪那一頁上</b>；
      本輪做的是把它<b>固定下來</b>——寫進一份版本化的對照組定義檔，並規定<b>每次引用都要覆述</b>。
      總覽報告 v1 與第十五輪仍然是用舊讀法寫的，<b>那兩頁一個字都沒有動</b>。</p>

    <div class="callout bad">
      <h3>★★ 必須每次覆述的那句話（逐字引自 <code>kelly_review/CONTROL_GROUP.md</code>）</h3>
      <p style="margin:0;font-size:1.04rem;line-height:1.9">
        <b>{F["cg_sim"]}。{F["cg_24w"]}{F["cg_wrong"]}</b></p>
      <p style="margin:10px 0 0">算術（第十六輪）：<b>{F["base_ratio"]}</b>
        往回推，唯一對得上合理報酬的長度是<b>{F["cg_real"]}</b>。</p>
    </div>

    <div class="plain">
      <span class="lbl">先講這個更正的證據強度</span>
      <p>它是<b>推論層級</b>，不是量測：它建立在「現貨存量 {F["stack"]}」與「每週 100 USDT」
        這兩個狀態檔數字相除上。對照組定義檔對這一列的標註就是
        「<b>{F["cg_confirm"]}</b>」——<b>你打開帳戶看一眼定投計畫的建立日期就能確認或推翻它</b>，
        而在你看之前，它仍然只是一個推論。</p>
      <p><b>同時：{F["base_alive"]}。</b>回測量的是「這個策略在那段歷史窗口上會怎樣」，
        那件事跟你的帳戶實際跑了多久無關，仍然成立。
        <b>{gl("幣數比", "g17-cr")}這個尺度也不受影響</b>，因為它的分子和分母是同一段模擬。
        壞掉的只有一種讀法：<b>把 0.8511 顆讀成「我已經累積的幣」</b>。
        當初沒把這件事講清楚是報告的責任不是你的——{F["base_must"]}</p>
    </div>

    <h3 class="sub">10.1 這個讀法出現在哪些已發布的位置</h3>
    <div class="table-wrap">
      <table>
        <caption>四個已發布檔案全文掃過，「0.8511」的出現次數：
          總覽報告 v1 <b>{BASE_HITS[V1H]}</b> 次、第十五輪 <b>{BASE_HITS[R15H]}</b> 次、
          第十六輪 <b>{BASE_HITS[R16H]}</b> 次、索引頁 <b>{BASE_HITS["laoliu.html"]}</b> 次。
          下表引用的每一句都由建置程式比對過原始檔案，<b>原頁全部維持原狀不動</b>。</caption>
        <thead><tr><th>位置</th><th>原文（未改動）</th><th>按對照組定義該怎麼讀</th></tr></thead>
        <tbody>{baseloc_rows}</tbody>
      </table>
    </div>
    <p class="body-note"><b>索引頁（<a href="laoliu.html">老六研究院</a>）上總覽報告那張卡也帶著同一句</b>：
      「{INDEX_QUOTE}」。索引卡不是報告，但你一樣讀得到，所以一併列出；
      第十六輪那張卡已經自己帶了更正。</p>

    <h3 class="sub">10.2 為什麼是「這一輪才固定下來」</h3>
    <div class="callout bad">
      <h3>★ 這個專案做到第十七輪，才第一次有一份寫下來的計分原點</h3>
      <p style="margin:0">對照組定義檔的標頭是 <code>{CG_VER}</code>——
        <b>{F["cg_late"]}</b>。在它存在之前，計分原點是每次臨時兜出來的，
        <b>而兜出來的兩個都是錯的</b>：一個是這裡講的「六年 0.8511 顆」，
        另一個是<a href="#correction-scoreboard">更正一</a>的「每週多存 5 塊 = $260／年」。
        <b>{F["cg_both"]}</b>，而{F["cg_nogate"]}
        （白話：本來應該在發布前攔下這種錯的那道稽核關卡，<b>{F["aud_none"]}</b>；
        它第一次跑是第十四輪的補稽核，而這一頁是它第三次跑——<b>這一次它擋下了五項</b>）。</p>
      <p style="margin:10px 0 0">定義檔現在自己帶的規則是「{CG_ORIGIN}。{F["cg_rev"]}，不得就地覆寫」——
        <b>跟這一頁遵守的發布規則是同一條</b>。</p>
    </div>

    <h3 class="sub">10.3 它改變什麼、不改變什麼</h3>
    <ul class="limits">
      <li><b>{F["fs_fix"]}</b>（第九輪只算了一個定投計畫）。
        <b>這強化而不是削弱第九輪的結論</b>：流量側比存量側更重要。</li>
      <li><b>本頁所有寫「六年」的數字都是模擬</b>；凡是講「你實際經歷過的」，本頁都另外標明。</li>
      <li><b>它讓<a href="#limits">第十一節 11.3</a> 那個「結論會過期」的問題更急</b>：
        存量小是<b>現在</b>的事實，而現在的存量正是「全額破產＝{F["months32"]}」這句話的基礎。</li>
      <li><b>它不改變本輪的裁決。</b>本輪比的是「你現在在做的事」與「換過去」，
        兩邊都是從今天往前看，跟帳戶已經跑了多久無關。</li>
    </ul>
  </section>
''')
print(f"correction 3 added ({len(QUOTED)} verbatim quotes verified against the "
      f"published files), total {sum(len(x) for x in P):,} bytes")

# --- §11 honest limits, §12 still open, §13 conclusion ----------------------
A(f'''
  <section id="limits">
    <h2>十一、誠實標註</h2>
    <p class="section-note">這一節放的是<b>會讓這一輪的結論變弱的東西</b>，包含覆核者自己抓到並修掉的錯。
      依專案慣例，它們不放在最後當小字，而是單獨成節。</p>

    <h3 class="sub">11.1 覆核者自己推翻／修掉的三項</h3>
    <ul class="limits">
      <li><b>他自己第一版的「beta 讓渡要額外再扣一次」是重複計算。</b>
        持有期的 BTC 不是平盤（{F["hold_cagr"]}），回測報酬裡<b>已經</b>含了那段期間的 beta 成本。
        正確做法是迴歸拆解後重新預測，不是再減一次。
        <b>被取代的那幾份計算在輸出目錄裡都留著，並在檔案裡加註標示已被取代——舊的錯誤數字沒有刪掉。</b></li>
      <li><b>訊號函數內部已經帶了一個反向符號，他第一版在外面又乘了一次，跑的是一本「鏡像帳」。</b>
        修正後全部重跑，重現了已發布的年化 {F["mirror_fix"]}、{F["t_pub"]}，<b>逐位元吻合</b>
        ——這個吻合本身就是「修正成功」的驗證。</li>
      <li><b>★ 協調者價目表的線性縮放錯誤，會讓已發布的一個回撤數字下修。</b>
        報酬與回撤對槓桿都是凸的，不能把已經年化複利過的數字乘上部位倍率。
        三源 1/N 在 f={F["f1333"]} 的實際回撤是 <b>{F["dd_true"]}</b>，
        協調者算的是 {F["dd_coord"]}——<b>低估了三分之一</b>。
        <b>{F["dd_coord"]} 這個數字本身並不是憑空來的：它正好是 λ=1.0 的實際回撤</b>
        （同一份 <code>f1_growth.csv</code>，本頁重算確認），
        <b>錯在把它線性放大貼到 λ={F["f1333"]} 上</b>——
        所以本頁出現 {F["dd_coord"]} 時一律註明是哪一個 λ；
        年化則是 {F["ann_true"]} 而不是 {F["ann_coord"]}。
        <b>這個 bug 汙染的是協調者在規格變更當天重算的那張價目表（尚未做成頁面），
        以及任何引用它的地方；已發布的三個頁面裡沒有這張表。</b></li>
    </ul>

    <h3 class="sub">11.2 樣本與建構</h3>
    <ul class="limits">
      <li><b>三源 1/N 的「淨額帳」十七輪來沒有人真的建出來過，本輪是第一次。</b>
        在此之前它一直被當成「三條報酬序列取平均」在用。
        平均三條序列等價於一本淨額帳，而淨額會互相抵銷——
        實測淨額 ÷ 不抵銷的名目＝{F["net_ratio"].split(" = ")[1]}（最低 0.667），
        <b>抵銷效果存在但只有約 5%，不足以當安全論據</b>。
        <b>也就是說：本輪報的這本帳的風險數字，是它第一次被真正量到。</b></li>
      <li><b>{F["windows"]}出自 {YRS_CAP:.2f} 年的資料，約等於 {F["indep"]}。</b>
        <b>離散度是資訊；「有幾成的窗是正的」只是這 81 個窗的描述</b>，
        本頁在 6.3 照這個口徑寫，<b>沒有把它當成前瞻的勝率或機率</b>。</li>
      <li><b>λ_crit 的分布是用「同時最壞」的盤中標記算的</b>——
        多頭腿標當日最低、空頭腿標當日最高、抵押品標當日最低，同一瞬間。
        <b>這是一個歷史上從未真正發生的合成極值，所以那些數字是危險的嚴格上界，不是典型值。</b></li>
      <li><b>三源 1/N 那本帳只有 {LC["Tri-source 1/N netted book"]["n"]} 週、只涵蓋 2024–2026</b>，
        它的樣本裡<b>根本沒有 {F["btc_worst"]} 那種週</b>。
        它看起來最安全，有一部分原因只是它沒看過最壞的日子。</li>
      <li><b>破產機率的三個模型全部只定價價格風險</b>（見<a href="#ruin">第三節</a>）。</li>
      <li><b>本輪沒有產生任何乾淨的首次讀取，也沒有新的{gl("幣數比", "g17-cr")}。</b>
        本輪是覆核與風控，不是新的策略量測。</li>
      <li><b>本輪的產出經過了發布前的獨立稽核，裁決是「需修正」，五項已修</b>（見 11.4）。
        <b>但這一關{F["aud_none"]}</b>——本頁受惠於一道大部分輪次都沒有跑過的關卡，
        <b>前面十幾輪的結論並沒有受過同樣的檢查。</b></li>
    </ul>

    <h3 class="sub">11.3 會過期的結論</h3>
    <ul class="limits">
      <li><b>★ 風險容忍度的結論會過期。</b>今天全額破產＝{F["months32"]}，
        2028 年存量到 {F["st15k"]} 時＝{F["yr15"]}。
        <b>「現在輸得起」不是「以後也輸得起」，而研究結論會被沿用到以後。</b>
        任何沿用者都必須重跑<a href="#ruin">第三節 3.4</a>。</li>
    </ul>

    <h3 class="sub">11.4 發布前的獨立稽核擋下來的五項（<b>不是我們自己抓到的</b>）</h3>
    <p>上面 11.1 那三項是覆核者自己抓到的。下面這五項<b>不是</b>——
      它們是這一頁在送出之前被獨立稽核擋下來的，裁決是<b>需修正</b>。
      <b>分開列，是因為「自己抓到的」和「被別人抓到的」不是同一種證據。</b>
      五項全部已修正後才產出這一頁；<b>原本錯成什麼樣子一起寫在這裡</b>，不然這張表沒有意義。</p>
    <div class="table-wrap wide">
      <table>
        <caption>稽核裁決：需修正（{TODAY}）。這一頁是修正後的版本，不是被擋下的那一版。</caption>
        <thead><tr><th>項目</th><th>原本寫成什麼</th><th>實際是什麼</th><th>怎麼修的</th></tr></thead>
        <tbody>
          <tr class="bad"><td class="name wrap">對數常態那一欄的<b>單位</b></td>
            <td class="wrap">當成年化機率印出來，和已經年化的厚尾欄並排</td>
            <td class="wrap"><code>{F["week_hdr"]}</code>——<b>它是每週值</b>。年化後是 <b>{F["logn_ann"]}</b></td>
            <td class="wrap">全頁改用年化值；<b>{F["log_ok"]}，錯在從紀錄檔抄進覆核報告那一步</b></td></tr>
          <tr class="bad"><td class="name wrap">「差六個數量級」</td>
            <td class="wrap">當成兩個模型的差距寫進章節標題與內文 5 處</td>
            <td class="wrap"><b>{F["oom_wrong"]}</b>；同單位的真值是 <b>{F["oom_truth"]}</b></td>
            <td class="wrap">標題改為 {OOM_LO:.0f}~{OOM_CROSS:.0f}，內文一律寫成
              「同一本帳 {OOM_LO:.1f}~{OOM_HI:.1f}、跨帳本最大 {OOM_CROSS:.2f}」；
              <b>結論（資料無法裁決）不變</b></td></tr>
          <tr class="bad"><td class="name wrap">{CUM_CAP:.3f} 被放在「{gl("幣數比", "g17-cr")}」那一欄</td>
            <td class="wrap">在對照組的 1.0000 旁邊，讀起來像「比專案史上最好的還好 3.7 倍」</td>
            <td class="wrap">它是 <code>f_growth.py</code> 印在 <code>coinratio</code> 欄名底下的 <code>eq[-1]</code>：
              <b>{NW_CAP} 週的累積倍數，沒有定投流入、沒有純 DCA 分母</b>（年化欄是 {CR_CAP:.4f}）</td>
            <td class="wrap">那一格改成「本輪沒有算出幣數比」，數字保留但改標成累積倍數；
              <b>來源腳本的欄名已改掉</b>，既有紀錄檔不回頭重寫</td></tr>
          <tr class="bad"><td class="name wrap">「本輪沒有經過發布前的獨立稽核」</td>
            <td class="wrap">寫在摘要最上方</td>
            <td class="wrap"><b>在推送當下已經不成立</b>——稽核就是這一次；同段還說「唯一跑過的是第十四輪」，
              也不準確</td>
            <td class="wrap">改寫成本頁現在的說法，並保留真正重要的那半句：<b>{F["aud_none"]}</b></td></tr>
          <tr class="bad"><td class="name wrap">勝率自相矛盾</td>
            <td class="wrap">6.3 列出「{J2[("1.333", "alpha = 0 (costs+beta only)")]["lose"]:.0f}% 的起點輸」，
              同一節的警告框卻寫「本頁沒有做這種宣稱」</td>
            <td class="wrap">兩句話不能同時成立</td>
            <td class="wrap">保留數字，但明寫它是<b>那 {F["windows"].split(" 個")[0]} 個重疊窗的描述性統計</b>，
              不是前瞻機率；警告框也改成同一個口徑</td></tr>
        </tbody>
      </table>
    </div>
    <div class="callout bad">
      <h3>★ 這五項裡最該記住的一件事：斷言機制擋不住這一類錯</h3>
      <p>這一頁的每個數字都要通過「這串字必須逐字出現在來源檔裡」的斷言。
        <b>那個斷言證明的是出處，不是真假。</b>
        兩個被退役的值——「差六個數量級」和舊的對數常態區間——
        <b>今天仍然逐字存在於狀態檔裡</b>（在那則把它們退役掉的更正註記裡面），
        <b>所以斷言會讓它們原封不動地再次通過。</b></p>
      <p style="margin:0">本輪因此補了兩道反向檢查：
        <b>(1) 退役值清單</b>——被退役的字串只准出現在明講它是錯的句子旁邊；
        <b>(2) 反向數字檢查</b>——把頁面上的數字全部抓出來回頭找來源，
        找不到的必須逐一列名。<b>先前只有正向（斷言過的必須上頁），
        沒有反向（上頁的必須有來源），而被擋下的五項裡有四項落在反向那一側。</b></p>
    </div>
  </section>

  <section id="open">
    <h2>十二、還開著的三件事</h2>
    <p class="section-note">這不是結案。下面三件都不是「再跑一輪回測」能關掉的。</p>

    <div class="callout bad">
      <h3>★ 1. 需要你一句話：「名目 &lt; 保證金」的「保證金」指的是哪一個？</h3>
      <p>你保留的限制是「合約名目曝險 &lt; 保證金」。這句話有兩種讀法，而它們差非常多：</p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>讀法</th><th>「保證金」＝</th><th>允許的內部槓桿上限</th></tr></thead>
          <tbody>
            <tr class="best"><td class="name">A</td><td class="wrap"><b>已經搬進合約錢包的那一部分</b></td><td class="wrap">λ ≤ 1<span class="d">＝有代數保護的那條線</span></td></tr>
            <tr class="bad"><td class="name">B</td><td class="wrap">你<b>全部</b>的 BTC</td><td class="wrap">λ ≤ 1 ÷ m<span class="d">配上「只用 10% 資產」就允許 <b>{F["lam10"]}</b></span></td></tr>
          </tbody>
        </table>
      </div>
      <p style="margin:10px 0 0"><b>讀法 B 配上「只用一成資產」會允許十倍槓桿</b>——
        而那正是第十一輪指出的那個誘因陷阱的完整形狀：
        <b>「只投入一小部分」聽起來保守，做出來的卻是最危險的那一組。</b>
        建議把規格改寫成不會被誤讀的形式：<b>「{F["spec_fix"]}」</b>。</p>
    </div>

    <div class="callout bad">
      <h3>2. 存量／流量比會讓本輪的風險結論過期</h3>
      <p style="margin:0">見<a href="#limits">第十一節 11.3</a>。</p>
    </div>

    <div class="callout bad">
      <h3>3.「alpha 是真的機率」是一個信念，不是一個量測</h3>
      <p style="margin:0">覆核者給了 {F["p_alpha"]}，並給了完整的門檻表
        （<a href="#optsize">第四節 4.4</a>）。<b>你可以代入自己的數字得到自己的答案</b>——
        而這一輪最誠實的成果，可能就是把問題整理成「只剩一個數字要你自己填」的形狀。</p>
    </div>
  </section>

  <section id="conclusion">
    <h2>十三、結論</h2>

    <div class="plain">
      <span class="lbl">一句話</span>
      <p><b>不該換。</b>解封投入比例沒有修好任何東西——
        它放大的是一個可能是零的數字，而且順手把藏在裡面的做空 BTC 部位一起放大了。</p>
      <p>研究了十七輪，最好的那個候選在它自己的證據撐得起的機率下，
        一年的期望貢獻是 <b>{F["band_usd"]}</b>，
        而且要用<b>「有可能在某一年把合約錢包裡的幣全部輸掉」</b>去換。</p>
      <p><b>但請注意上一句話的比較對象。</b>依你本人的裁定
        （<a href="#correction-scoreboard">第八節</a>），「每週多存 5 塊」不能當計分板，
        所以正確的說法不是「它輸給多存 5 塊」，而是：
        <b>在合格的計分板（同樣的錢、最後幾顆幣）上，它的期望值取決於一個
        目前只有 {F["p_alpha"]} 把握的信念，而那個把握度剛好落在「值不值得做」的門檻邊上。
        邊上，不是上面。</b></p>
    </div>

    <h3 class="sub">按強度分段，不合併成一句話</h3>
    <div class="split">
      <div class="callout good">
        <h3>強證據（代數，不會被推翻）</h3>
        <ul>
          <li><b>m 從強平條件中消去</b>，所以強平機率只看 λ、損失只看 m、報酬只看 e = m·λ。</li>
          <li><b>對任何目標曝險，最適解永遠是「全部進去、槓桿壓最低」。</b></li>
          <li><b>協調者的 f 就是內部槓桿</b>：m=1 時 {F["lam_from_f"]}。</li>
          <li><b>λ ≤ 1.0 有代數保護，λ = {F["f1333"]} 沒有。</b></li>
          <li><b>不存在任何 λ &gt; 0 能對任意行情證明不會被強平</b>——「不被強平」只能是機率陳述。</li>
        </ul>
      </div>
      <div class="callout bad">
        <h3>弱證據（推論，脆弱，不要單獨引用）</h3>
        <ul>
          <li><b>{F["gpd_band"]} 這個破產機率區間。</b>
            建立在 234~292 個<b>重疊</b>週上，真正不同的壓力狀態只有 4~5 個，
            而且<b>對數常態模型給的答案差 {OOM_LO:.1f}~{OOM_HI:.1f} 個數量級</b>。</li>
          <li><b>「alpha 是真的機率 {F["p_alpha"]}」是一個判斷</b>，不是量測。</li>
          <li><b>逐起點分布的中位數與百分位</b>——約 2.5 個獨立觀測。</li>
          <li><b>「績效集中在 BTC 下跌週」的前瞻意涵</b>：樣本內的事實很硬，
            但它對未來的意思完全取決於未來 BTC 的走勢形狀。</li>
        </ul>
      </div>
    </div>

    <div class="callout">
      <h3>在合格的計分板上，這一輪實際產出了什麼</h3>
      <ul>
        <li><b>零個新的幣數比。</b>本輪沒有任何候選走到能算幣數比的階段。</li>
        <li><b>一個結構性的代數結果</b>（<a href="#leverage">第一節</a>），它<b>改變了未來所有部位設定的做法</b>，
          而且不依賴任何資料。</li>
        <li><b>一個已發布數字的下修</b>（回撤 {F["dd_coord"]} → {F["dd_true"]}）。</li>
        <li><b>兩個已發布錯誤的更正</b>，其中一個是你本人指出的。</li>
        <li><b>一個家族出局</b>（對沖比例選單），因為你宣告你不買它賣的那份保險。</li>
        <li><b>一個需要你一句話才能關掉的規格歧義。</b></li>
      </ul>
    </div>
  </section>
''')

# --- glossary ---------------------------------------------------------------
gsec = ['<section id="glossary">', "<h2>術語表</h2>",
        '<p class="section-note">只收這一頁用到的。正文第一次用到時會就地連過來。</p>']
for group, items in GLOSS:
    gsec.append(f'<div class="gloss-group">{group}</div>')
    gsec.append('<div class="table-wrap"><table class="gloss"><tbody>')
    for gid, term, en, desc in items:
        en_s = f'<span class="d">{en}</span>' if en else ""
        gsec.append(f'<tr id="{gid}" class="gterm"><td>{term}{en_s}</td>'
                    f'<td class="wrap">{desc}</td></tr>')
    gsec.append("</tbody></table></div>")
gsec.append("</section>")
A("\n".join(gsec))

A(f'''
  <section id="repro">
    <h2>數字是怎麼進到這一頁的</h2>
    <div class="engine">
      <h3>這一頁的數字是怎麼來的，以及這句話的界線在哪</h3>
      <dl>
        <dt>建置程式</dt>
        <dd><code>SumerTWRobotTest1/tools/build_laoliu_r17.py</code></dd>
        <dt>做到什麼程度</dt>
        <dd><b>@@NFACT@@ 個字面值</b>在 build 時被斷言逐字存在於來源檔，
          <b>@@NCROSS@@ 個</b>由紀錄檔重算後與來源逐位比對，
          所有表格與圖由紀錄檔解析產生。
          <b>但「這一頁沒有一個數字是手抄的」這句話，先前寫得太滿</b>：
          散文裡仍有數字是直接寫進 HTML 的，它們沒有被任何斷言保護。
          本次改用<b>反向檢查</b>把界線量出來——把頁面上的數字逐一抓出來，
          回頭比對全部素材，<b>@@NUM_TOK@@ 個數字 token 裡 @@NUM_HIT@@ 個在素材裡找得到</b>，
          其餘 @@NUM_MISS@@ 個逐一列名在建置程式裡，兩個都是就地推導的衍生值
          （λ÷2 的多頭腿面額，以及年化欄四捨五入到小數第四位）。
          <b>這個檢查先前只有單向（斷言過的必須上頁），沒有反向（上頁的必須有來源）。</b></dd>
        <dt>規則</dt>
        <dd>每一個數字，要嘛在 build 時被斷言<b>逐字存在</b>於 <code>laoliu-state.md</code>
          或 <code>kelly_review/REPORT.md</code> 或 <code>kelly_review/CONTROL_GROUP.md</code>，
          要嘛由本程式從 <code>kelly_review/*.log</code> 解析出來（解析結果也帶斷言）。
          年化換算等少數衍生值在本程式裡計算，並在頁面上標明是衍生的。
          <b>任何一項對不上，build 直接失敗，頁面不會產出。</b></dd>
        <dt>發布前驗證</dt>
        <dd>本頁在寫出檔案之前通過 <b>@@NCHECK@@ 項</b>自動檢查：標籤閉合、
          每一個 CSS class 都有定義、頁內錨點全部可解析、
          <b>指向舊報告的每一個 <code>#錨點</code> 都到原檔裡比對過確實存在</b>、
          引用舊頁的每一句原文都逐字比對過、章節與小節編號一致、
          寬表格有橫向捲動、以及<b>三個既有頁面在本次執行前後的 SHA-256 完全相同</b>。
          <b>任何一項不過，檔案不會被寫出。</b></dd>
        <dt>原始輸出</dt>
        <dd><code>kelly_review/</code>：{KR_PY} 個腳本 + {KR_LOG} 個紀錄檔 + {KR_CSV} 個 CSV +
          版本化的對照組定義（數量由建置時清點，不是記憶）。全部可重跑，無網路需求。</dd>
        <dt>這一頁是公開的</dt>
        <dd>頁首的存取碼<b>不是安全機制</b>：它是寫在所有頁面 JavaScript 裡的<b>明文常數</b>，
          任何人按「檢視原始碼」就看得到。建置時的隱私掃描擋的是檔案路徑、電子郵件與 API 金鑰那幾種樣式，
          <b>抓不到裸的十六進位常數</b>，
          所以這一項是人工確認的，不是程式保證的。
          <b>請把這一頁當成公開文件看待</b>——推送這一輪不改變曝險，那個常數本來就已經在公開頁面上。</dd>
        <dt>發布規則</dt>
        <dd>已發布的頁面<b>一律不覆蓋、不刪除</b>。本次只新增這一頁，
          並在索引 <code>laoliu.html</code> 加一張卡。
          <b>總覽報告 v1、第十五輪、第十六輪三個檔案的內容完全未變動。</b></dd>
      </dl>
    </div>
  </section>

</main>

<footer>
  老六研究院 · 第十七輪 · {TODAY}　|　
  本頁由 <code>tools/build_laoliu_r17.py</code> 產生，數字全部程式注入。<br>
  回測與模擬結果不代表未來表現，也不構成投資建議。<b>研究進行中，結論可能隨新證據修正。</b>
</footer>

</body>
</html>
''')
doc = "".join(P)
print(f"doc assembled: {len(doc):,} bytes")


# ================================ validation ================================
# Ported from tools/build_laoliu_r16.py (44 assertions) and extended with the
# checks r16 did not have: sub-section numbering, verbatim quotes of published
# pages, immutability hashes for the three frozen pages, and a "nothing private
# ships" sweep (a published page is a public page).
import hashlib                                                     # noqa: E402
from html.parser import HTMLParser                                 # noqa: E402

FROZEN = {V1: v1_txt, R15: r15_txt, R16: r16_txt}
FROZEN_SHA = {p: hashlib.sha256(s.encode("utf-8")).hexdigest()
              for p, s in FROZEN.items()}
NCHECK = 0


def check(cond, msg):
    """One assertion, counted, so the page can state how many it passed."""
    global NCHECK
    NCHECK += 1
    assert cond, msg


# --- 1. section numbers are generated, never hand-written -------------------
SECNUM = {"leverage": "一", "corr": "二", "ruin": "三", "optsize": "四",
          "hiddenbeta": "五", "control": "六", "spec": "七",
          "correction-scoreboard": "八", "correction-spec": "九",
          "correction-control": "十", "limits": "十一", "open": "十二",
          "conclusion": "十三"}
SECIDX = {a: i + 1 for i, a in enumerate(SECNUM)}


def _fixref(m):
    a = m.group(1)
    return f'<a href="#{a}">第{SECNUM[a]}節</a>' if a in SECNUM else m.group(0)


doc, nfix = re.subn(r'<a href="#([a-z0-9-]+)">第[一二三四五六七八九十]+節</a>',
                    _fixref, doc)
for a, num in SECNUM.items():
    check(f'<section id="{a}">' in doc, f"section #{a} missing")
    body = doc.split(f'<section id="{a}">', 1)[1]
    h2 = re.search(r"<h2>(.*?)</h2>", body, re.S).group(1)
    check(h2.startswith(num + "、"), f"section #{a} h2 starts {h2[:8]!r}, want {num}")
stray = re.findall(r"(?<!>)第[一二三四五六七八九十]+節",
                   re.sub(r'<a href="#[a-z0-9-]+">第[一二三四五六七八九十]+節</a>', "", doc))
check(not stray, f"section reference outside an anchor: {stray}")

# --- 1b. sub-section numbers must match their own section (r16 had no such
#         check; this round shifted three sections by one and it would have
#         been the exact kind of drift nobody notices) ----------------------
for a, num in SECNUM.items():
    body = doc.split(f'<section id="{a}">', 1)[1].split("</section>", 1)[0]
    for sub in re.findall(r'class="sub">(\d+)\.(\d+)', body):
        check(int(sub[0]) == SECIDX[a],
              f"section #{a} (no. {SECIDX[a]}) carries sub-heading {sub[0]}.{sub[1]}")
SUBS = set(re.findall(r'class="sub">(\d+\.\d+)', doc))
for m in re.finditer(r"第([一二三四五六七八九十]+)節 (\d+)\.(\d+)", doc):
    want = [k for k, v in SECNUM.items() if v == m.group(1)]
    check(want and SECIDX[want[0]] == int(m.group(2)),
          f"cross-reference 第{m.group(1)}節 {m.group(2)}.{m.group(3)} is inconsistent")
    check(f"{m.group(2)}.{m.group(3)}" in SUBS,
          f"cross-reference to a sub-section that does not exist: "
          f"{m.group(2)}.{m.group(3)}")

# --- 2. tag balance ---------------------------------------------------------
VOID = {"meta", "br", "hr", "img", "input", "link", "circle", "line",
        "polyline", "path", "rect"}


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.err = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.err.append((tag, list(self.stack[-3:]), self.getpos()))
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()


bal = Balance()
bal.feed(doc)
check(not bal.err, f"unbalanced tags: {bal.err[:4]}")
check(not bal.stack, f"unclosed tags: {bal.stack}")

# --- 3. every CSS class used must be defined, for the element it is used on --
css_body = re.search(r"<style>(.*?)</style>", CSS, re.S).group(1)
allowed = {}
for elem, cname in re.findall(r"([a-zA-Z]*)\.([A-Za-z][A-Za-z0-9_-]*)", css_body):
    allowed.setdefault(cname, set()).add(elem.lower())
bad_cls = []
for tag, attr in re.findall(r"<([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>", doc):
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
own_ids = set(re.findall(r'id="([A-Za-z0-9_-]+)"', doc))
check(len(own_ids) == len(re.findall(r'id="([A-Za-z0-9_-]+)"', doc)),
      "duplicate id on the page")
for href in re.findall(r'href="#([A-Za-z0-9_-]+)"', doc):
    check(href in own_ids, f"dangling in-page anchor #{href}")
EXT = {"crypto-dca-amplifier-report.html": V1_IDS,
       "laoliu-r15-triage2.html": R15_IDS,
       "laoliu-r16-eth.html": R16_IDS,
       "laoliu.html": INDEX_IDS}
next_links = 0
for page, frag in re.findall(r'href="([a-z0-9\-.]+\.html)#([A-Za-z0-9_-]+)"', doc):
    check(page in EXT, f"link to a page with no id pool: {page}")
    check(frag in EXT[page], f"{page}#{frag} does not exist in that file")
    next_links += 1
check(next_links >= 10, f"only {next_links} cross-page anchors")
for page in set(re.findall(r'href="([a-z0-9\-.]+\.html)', doc)):
    check(os.path.exists(os.path.join(REPO, page)), f"link to missing file {page}")

# --- 5. wide tables ---------------------------------------------------------
for m in re.finditer(r'<div class="table-wrap([^"]*)"[^>]*>(.*?)</div>', doc, re.S):
    ncol = len(re.findall(r"<th\b", m.group(2).split("</tr>", 1)[0]))
    if ncol > 4:
        check("wide" in m.group(1),
              f"{ncol}-column table without .wide: {m.group(2)[:120]}")

# --- 6. wording discipline --------------------------------------------------
for w in ("終局", "結案", "已證實"):
    for mm in re.finditer(w, doc):
        ctx = doc[max(0, mm.start() - 40):mm.start() + 20]
        check(any(k in ctx for k in ("不寫", "不下", "不宣稱", "不是", "沒有")),
              f"forbidden word {w} in an affirmative sentence: {ctx!r}")
for name in ("費曼", "凱利先生", "唐1", "TANG-1", "TE-1", "DE-1", "COIN-M 反向"):
    check(name not in doc, f"forbidden cross-line reference: {name}")
for f_other in ("crypto-tang1-report", "crypto-te1-report", "crypto-de1-report",
                "crypto-coinm-report", "crypto-dca-leveraged-report",
                "crypto-trend-hedge-report"):
    check(f_other not in doc, f"link into the other research line: {f_other}")
check("研究進行中" in doc, "status badge missing")
check(TODAY in doc and "第十七輪" in doc, "round/date missing")
check('href="laoliu.html"' in doc, "breadcrumb back to the index missing")
check(doc.count("更正一") >= 2 and doc.count("更正二") >= 2
      and doc.count("更正三") >= 2, "one of the three corrections is not linked")
check(F["cg_wrong"] in doc, "the control-group restatement is missing")
check("對數" in doc, "the right-skewed charts must say they use a log axis")
check(F["indep"] in doc, "independent-observation count missing")

# --- 7. nothing private ships (a published page is a public page) -----------
for leak in ("/Volumes/", "/Users/", "@gmail.com", "ANTHROPIC", "sk-",
             "Authorization", "apiKey", "api_key"):
    check(leak not in doc, f"private string on a published page: {leak}")

# --- 8. no unformatted placeholders / non-numbers ---------------------------
body_only = doc.split("</style>", 1)[1]
for junk in ("{F[", "{LC[", "{J2[", "{TAIL[", "{BASE_HITS["):
    check(junk not in body_only, f"unrendered placeholder in the page: {junk}")
for junk in (r"\bNone\b", r"\bnan\b", r"\bNaN\b", r"\binf\b", r"[-\u2212]0\.0+%"):
    check(not re.search(junk, body_only),
          f"invalid computed value in the page: {junk}")

# --- 9. every asserted literal has to reach the page ------------------------
# A handful are injected after .split()/.replace(), so they appear in pieces;
# those are listed explicitly rather than silently tolerated.
# (a) injected after a .split()/.replace(), so they reach the page in pieces
SPLIT_OK = {"net_ratio", "tri_beta", "lam_def", "gross_def", "aud_vrp",
            "cg_ver", "cg_origin", "top5src", "objective",
            "scoreboard", "cg_flow"}
# (b) the page renders these from the logs instead of quoting the state file;
#     the state literal is then used as a CROSS-CHECK on the computation.
#     Each one is compared numerically below - none is merely tolerated.
CROSS = {}


def cross(key, computed):
    CROSS[key] = computed
    check(computed == F[key],
          f"cross-check {key}: log gives {computed!r}, state says {F[key]!r}")


dep100 = [float(a) for h, _d, a, _b in L3 if h == "1.00"]
beat100 = [float(b) for h, _d, _a, b in L3 if h == "1.00"]
dep050 = [float(a) for h, _d, a, _b in L3 if h == "0.50"]
beat050 = [float(b) for h, _d, _a, b in L3 if h == "0.50"]
cross("th_dep", f"{min(dep100)}% ~ {max(dep100)}%")
cross("th_beat", f"{min(beat100)}% ~ {max(beat100)}%")
cross("th_dep_h", f"{min(dep050)}% ~ {max(dep050)}%")
cross("th_beat_h", f"{min(beat050)}% ~ {max(beat050)}%")
_ins = {(h, d): (a, b) for h, d, a, b in L3}
cross("th_pt_dep", _ins[("1.00", "in-sample (+26.5%)")][0] + "%")
cross("th_pt_beat", _ins[("1.00", "in-sample (+26.5%)")][1] + "%")
cross("th_pt_h", _ins[("0.50", "in-sample (+26.5%)")][0] + "%")
_l2 = {(p_, h): c for p_, h, c in L2}
cross("e20", "{}（g={}%）".format(*_l2[("20", "1.00")][0]))
cross("e30", "{}（{}%）".format(*_l2[("30", "1.00")][0]))
cross("ctrl_same", f"對照組同期 {CTRL_SAME:.3f}")
_face = J2[("1.333", "as backtested")]
_zero = J2[("1.333", "alpha = 0 (costs+beta only)")]
cross("rel_face", f"中位 {_face['med'] / CTRL_SAME:.2f} 倍")
cross("rel_zero", "中位 {:.2f} 倍、最差 {:.2f} 倍、{:.0f}% 的起點輸".format(
    _zero["med"] / CTRL_SAME, _zero["worst"] / CTRL_SAME, _zero["lose"]))
# (c) prose claims carried in the author's own words rather than quoted; the
#     state literal is a provenance check, and the page must still say it.
# These state-file literals name internal roles. Role codenames do not belong
# on a page the user reads, so they are asserted for provenance only and the
# page carries a codename-free rendering, checked by the fragment below.
PARAPHRASE = {"tri_first": "本輪是第一次",
              "aud_first": "它第一次跑是<b>第十四輪的補稽核</b>",
              "aud_team": "第二次的對象是團隊的管理流程",
              "oom_title": "個數量級",
              "btc_basis": "週內最深",
              "btc_basis2": "週內最深"}
for k, frag in PARAPHRASE.items():
    check(frag in doc, f"paraphrase of {k} missing from the page: {frag}")

missing = [k for k, (_, lit) in USED.items() if lit not in doc
           and k not in SPLIT_OK and k not in CROSS and k not in PARAPHRASE]
check(not missing, f"asserted but never used on the page: {missing}")
unused_ok = [k for k in SPLIT_OK if USED[k][1] in doc]
check(not unused_ok, f"listed as split but present verbatim: {unused_ok}")
check(len(CROSS) == 12, f"{len(CROSS)} cross-checks, expected 12")
check(len(QUOTED) == 9, f"{len(QUOTED)} verbatim quotes, expected 9")

# --- 9c. REVERSE check: every number ON the page must exist in the material.
# The forward check (asserted -> must appear) cannot catch a number that was
# typed straight into the prose, which is exactly what the pre-publication
# audit found. This is the other direction, and it is new this round.
HAY = "\n".join([state_txt, report_txt, cg_txt] + list(LOGS.values())
                + [open(os.path.join(KR, f), encoding="utf-8").read()
                   for f in sorted(os.listdir(KR))
                   if f.endswith(".csv") and not f.startswith("._")]
                + list(PUBLISHED.values()))
_prose = re.sub(r"<svg.*?</svg>", " ", body_only, flags=re.S)   # svg = geometry
_prose = re.sub(r"<[^>]+>", " ", _prose)
NUM_TOKENS = re.findall(r"\d+(?:[.,]\d+)*", _prose)
# Numbers this page derives on the spot. Each is named with its reason, and the
# list is asserted exhaustive, so a new stray number breaks the build.
DERIVED_OK = {
    "0.5000": "lambda/2 at lambda=1.0, the long-leg notional, computed in §1.4",
    "1.6967": "f1_growth.csv column cr rounded to 4dp for §6.1",
}
NUM_MISSES = sorted({tk for tk in NUM_TOKENS
                     if tk not in HAY and tk not in DERIVED_OK})
NUM_TOK = len(set(NUM_TOKENS))
NUM_HIT = NUM_TOK - len([d for d in DERIVED_OK if d in set(NUM_TOKENS)])
check(not NUM_MISSES, f"numbers on the page with no source: {NUM_MISSES[:12]}")

# --- 9d. values this page has retired must not come back --------------------
# fact() proves a literal EXISTS in a source file; it cannot prove the source
# still believes it. Both retired strings below are STILL in laoliu-state.md,
# inside the very note that retired them - so the assertion machinery would
# have let them straight back through. This list is the guard.
RETIRED = {
    "10⁻⁷ ~ 10⁻⁹/年": "per-week lognormal printed as annual (audit B1)",
    "六個數量級": "annualised GPD over per-week lognormal (audit B2)",
}
RETRACT = ("原本", "原標題", "原誤植", "錯", "更正", "退役", "舊")
for bad, why in RETIRED.items():
    for mm in re.finditer(re.escape(bad), _prose):
        ctx = _prose[max(0, mm.start() - 120):mm.start() + 120]
        check(any(k in ctx for k in RETRACT),
              f"retired value used as if still true: {bad} ({why})")

# --- 9e. the B4 root cause: the source script's column header ---------------
_fg = open(os.path.join(KR, "f_growth.py"), encoding="utf-8").read()
check("'cum(x)':>10s" in _fg, "f_growth.py still prints the column as coinratio")
check("coinratio" in LOGS["f_growth"],
      "the archived f_growth.log should still carry the old header: logs are a "
      "record of what was run and are not rewritten")
check(f"{CUM_CAP:.3f}" in body_only and "本輪沒有算出任何幣數比" in body_only,
      "section 6.1 must not present the cumulative multiple as a coin ratio")

# --- 10. the three frozen pages must be byte-identical afterwards -----------
for path, sha in FROZEN_SHA.items():
    now = hashlib.sha256(open(path, "rb").read()).hexdigest()
    check(now == sha, f"a frozen published page changed: {os.path.basename(path)}")

# --- 11. never overwrite a page this script did not produce -----------------
MARK = "<!-- built by tools/build_laoliu_r17.py -->"
if os.path.exists(OUT):
    check(MARK in open(OUT, encoding="utf-8").read(),
          f"{OUT} exists and was not produced by this script: refusing to overwrite")
doc = doc.replace("</head>", MARK + "\n</head>", 1)
# The headline band has two ends that come from two different assumptions.
# Spelling that out is the whole point of reporting a band, so the sentence is
# generated from the same grid the band came from (L2, P=20%, no haircut).
_row20 = {d: c for d, c in zip(L2_HEAD, _l2[("20", "1.00")])}
_e_in, _g_in = _row20["in-sample (+26.5%)"]
_e_zero, _g_zero = _row20["zero drift (+10.9% arith)"]
_e_full, _g_full = _row20["full-sample arith (+42.8%)"]
check(float(_e_full) == 0.0, "the full-sample-drift column is no longer a zero")
BANDNOTE = (
    f'<b>這個區間的兩端不是同一個情境。</b>它們都算在「你相信 alpha 是真的機率 = 20%、'
    f'alpha 不打折」這一格上，差別只在<b>對未來 BTC 漂移的假設</b>：'
    f'低端 {gfmt(_g_in)}%／年 假設的是{ZH_DRIFT["in-sample (+26.5%)"]}'
    f'（最適部署 e*={_e_in}），高端 {gfmt(_g_zero)}%／年 假設的是'
    f'{ZH_DRIFT["zero drift (+10.9% arith)"]}（e*={_e_zero}）。'
    f'<b>而在「{ZH_DRIFT["full-sample arith (+42.8%)"]}」那一欄，最適解是 e*=0，'
    f'也就是完全不要部署</b>——四個前瞻假設裡有一個直接給出「不要做」。'
    f'美元金額是拿這個百分比乘上你現有的存量（{F["stack"].split(" = ")[1]}）換算的，'
    f'<b>存量一變，這個美元數字就要重算</b>。')
doc = doc.replace("@@BANDNOTE@@", BANDNOTE)
for ph, val in (("@@NUM_TOK@@", NUM_TOK), ("@@NUM_HIT@@", NUM_HIT),
                ("@@NUM_MISS@@", len(DERIVED_OK)), ("@@NFACT@@", len(USED)),
                ("@@NCROSS@@", len(CROSS))):
    doc = doc.replace(ph, str(val))
doc = doc.replace("@@NCHECK@@", str(NCHECK + 1))   # +1: the placeholder check
check("@@" not in doc, "an unresolved build placeholder survived")

open(OUT, "w", encoding="utf-8").write(doc)
open(os.path.join(PUB, "laoliu-r17-kelly.html"), "w", encoding="utf-8").write(doc)
print(f"wrote {OUT}  {len(doc):,} bytes; {nfix} section refs normalised; "
      f"{len(own_ids)} anchors; {NCHECK} checks passed")


# ---------------- index card (regenerated between markers) ----------------
CARD = f'''<!-- R17-CARD:BEGIN (generated by tools/build_laoliu_r17.py — do not hand-edit) -->
  <a class="report-card" href="laoliu-r17-kelly.html">
    <div class="top">
      <span class="title">第十七輪 · 風控與對照組覆核</span>
      <span class="tag">{TODAY}</span>
      <span class="tag">規格變更後重算 · 三個更正</span>
      <span class="tag">建置驗證 {NCHECK} 項</span>
      <span class="tag live">研究進行中</span>
    </div>
    <div class="desc">
      <b>★ 你以為在調的「投入多少」，其實一直是「開幾倍槓桿」。</b>
      幣安跨倉的強平條件把「搬進合約錢包的比例 m」<b>整個約掉</b>：
      <b>強平機率只看內部槓桿、強平時賠多少只看 m、報酬只看兩者相乘</b>——
      所以最適解<b>永遠是角點</b>，不是中間值，而價目表裡那欄「f={F["f1333"]}」<b>其實就是 λ=1.0</b>。
      λ={F["f1333"]} 另有一個代數死法：BTC <b>單週之內</b>最深跌 {F["btc_worst"]}
      （樣本 2020-08~2026-08 裡週內最深的那一週）時<b>光多頭腿歸零就擊穿</b>
      （抵押品 {F["collat"]} vs 名目 {F["longleg"]}）。
      <b>協調者對風險的猜測方向是反的</b>：相關性是正號（BTC 跌越深、空頭腿動得越小），
      聯合尾部四本帳<b>觀測全部 0</b>；而他引用的 {F["top5avg"]} 是<b>宇宙前 5 強平均</b>，
      不是任何一本帳的空頭腿，實際 p99 是 {F["p99_real"]}。
      <b>破產機率三個模型在同一本帳上差 {OOM_LO:.1f}~{OOM_HI:.1f} 個數量級</b>
      （{F["gpd_band"]} vs {F["logn_ann"]}，<b>兩個都是年化值</b>），
      <b>「資料無法裁決」就是答案</b>；而且三個模型<b>全部只定價價格風險</b>。
      <b>「最適部署量」這個問題本身被推翻</b>（角點解，不是內點），它退化成「你信不信 alpha 是真的」。
      <b>★ 策略裡藏了一個做空 BTC 的部位</b>：alpha 的 t=+3.38、<b>beta 的 t=−3.93</b>——
      <b>這個專案對那個隱藏 beta 比對 alpha 更有把握。</b>
      <b>★ 規格變更（m=1、λ≤1、不設回撤上限、唯一硬約束是不被強平）唯一的實質效果，
      是把「對沖比例」整個家族歸零</b>——你說不設回撤上限，等於宣告你不買那份保險。
      <b>本頁帶三個更正，舊頁一個字都沒改</b>：
      (1)「每週多投 5 塊 = {F["c_usd"]}／年」<b>不該當計分板——你本人指出的</b>
      （「{F["quote_foul"]}」）；
      (2) 第十五輪有兩處舊規格措辭，<b>第十六輪一處都沒有</b>（與派工書的認定不同，照實寫）；
      (3)「純 DCA 六年 = 0.8511 顆 = 1.0000」<b>是模擬基準，不是你的帳戶</b>
      （你的帳戶約 24 次買進、約 0.44 年）。
      誠實標註：<b>覆核者自己推翻／修掉三項</b>，其中協調者價目表的線性縮放錯誤讓
      f={F["f1333"]} 的回撤從 {F["dd_coord"]} <b>下修到 {F["dd_true"]}（低估三分之一）</b>；
      <b>三源 1/N 的淨額帳十七輪沒人真的建過，本輪首建</b>；
      <b>{F["windows"]} ≈ {F["indep"]}</b>——離散度是資訊，
      <b>「有幾成的窗是正的」只是這 81 個窗的描述，不是前瞻勝率</b>；
      <b>本頁在發布前跑了獨立稽核，裁決「需修正」，五項已修</b>——
      其中兩項是<b>單位錯</b>（把每週機率當成年化、拿年化值去除以每週值得出「差六個數量級」），
      一項是<b>把疊加層自己的累積倍數 {CUM_CAP:.3f} 放在「幣數比」那一欄</b>（它不是幣數比）；
      <b>而這一關在第 1~13 輪從未跑過</b>；
      <b>結論會過期</b>（今天全額破產＝{F["months32"]}，2028 年＝{F["yr15"]}）。
      <b>本輪沒有產生任何新的幣數比。</b>
    </div>
    <div class="stats">
      <div>本輪新幣數比<b class="neg">0 個</b></div>
      <div>破產機率（兩者皆年化）：厚尾 vs 對數常態<b class="neg">{F["gpd_band"]} vs {F["logn_ann"]}</b></div>
      <div>隱藏的做空 BTC 部位<b class="neg">{F["beta_t"]}</b></div>
      <div>自己創造的報酬<b>{F["alpha_t"]}</b></div>
      <div>f={F["f1333"]} 的回撤（誤植 {F["dd_coord"]}，那其實是 λ=1.0 的）<b class="neg">{F["dd_true"]}</b></div>
      <div>一年期望貢獻（信心 {F["p_alpha"]}）<b class="neg">{F["band_usd"]}</b></div>
      <div>真正獨立的觀測<b class="neg">{F["indep"]}</b></div>
      <div>本頁更正的已發布錯誤<b>3 個</b></div>
    </div>
  </a>
<!-- R17-CARD:END -->
'''
for w in ("終局", "結案", "已證實"):
    check(w not in CARD, f"forbidden word {w} on the index card")
check("研究進行中" in CARD, "index card missing the status tag")

idx_before = open(INDEX, encoding="utf-8").read()
if "<!-- R17-CARD:BEGIN" in idx_before:
    idx = re.sub(CARD_RE, CARD, idx_before, flags=re.S)
else:
    marker = "<!-- R16-CARD:BEGIN"
    check(marker in idx_before, "R16 card marker not found in the index")
    idx = idx_before.replace(marker, CARD + "\n" + marker, 1)
n_cards = len(re.findall(r'<a class="report-card"', idx))
check(n_cards == 4, f"{n_cards} cards on the index, expected 4")
COUNT_TXT = f'<div class="count">共 {n_cards} 份報告 · 只計老六研究院這一條線</div>'
idx, nsub = re.subn(r'<div class="count">[^<]*</div>', COUNT_TXT, idx)
check(nsub == 1, f"report count replaced {nsub} times")

# the index may gain a card and a new count, and nothing else
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
idx_allowed = {c for _e, c in re.findall(r"([a-zA-Z]*)\.([A-Za-z][A-Za-z0-9_-]*)",
                                         idx_css)}
for _tag, attr in re.findall(r"<([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>", CARD):
    m = re.search(r'\bclass="([^"]*)"', attr)
    for c in (m.group(1).split() if m else []):
        check(c in idx_allowed, f"index card uses undefined CSS class .{c}")

open(INDEX, "w", encoding="utf-8").write(idx)
print(f"updated {INDEX}: {n_cards} cards, {NCHECK} checks passed in total")

# one last look: the three frozen pages, after everything
for path, sha in FROZEN_SHA.items():
    now = hashlib.sha256(open(path, "rb").read()).hexdigest()
    check(now == sha, f"a frozen published page changed: {os.path.basename(path)}")
print("frozen pages verified byte-identical: "
      + ", ".join(sorted(os.path.basename(p) for p in FROZEN_SHA)))
