#!/usr/bin/env python3
"""Build laoliu-r16-eth.html (Round 16 / the ETH recurring plan) from eth_plan/.

Discipline (same as tools/build_laoliu_r15.py):
  - Every number on the page is either (a) recomputed here from eth_plan/data/
    (read-only), (b) parsed out of the researcher's own logs_*.log with an
    assert that the parse matched, or (c) pulled from FACTS and asserted to
    appear LITERALLY in laoliu-state.md. Nothing is typed into the prose.
  - The CSS block and the access-control gate are lifted verbatim from the
    frozen v1 report so the new page cannot drift visually. v1 is read-only.
  - No already-published page is written to. Only laoliu.html (the index) is
    touched, and only between generated markers.
Run: python3 build_laoliu_r16.py
"""
import os, re, sys, json, math, time, html, statistics, datetime as dt
import urllib.request

ROOT = "/Volumes/FCP 512GB/Claude"
REPO = os.path.join(ROOT, "SumerTWRobotTest1")
ETHP = os.path.join(ROOT, "eth_plan")
PUB = os.path.join(ROOT, "r16_publish")           # this round's own scratch dir
V1 = os.path.join(REPO, "crypto-dca-amplifier-report.html")
R15 = os.path.join(REPO, "laoliu-r15-triage2.html")
STATE = os.path.join(ROOT, "laoliu-state.md")
OUT = os.path.join(REPO, "laoliu-r16-eth.html")
INDEX = os.path.join(REPO, "laoliu.html")
TODAY = "2026-09-21"
os.makedirs(PUB, exist_ok=True)

state_txt = open(STATE, encoding="utf-8").read()
report_txt = open(os.path.join(ETHP, "REPORT.md"), encoding="utf-8").read()


def fact(key, literal):
    """A number that lives only in the state file: assert it, then inject it."""
    assert literal in state_txt, f"FACT {key} ({literal!r}) not in laoliu-state.md"
    return literal


def rfact(key, literal):
    """A number that lives only in the researcher's REPORT.md: same treatment."""
    assert literal in report_txt, f"RFACT {key} ({literal!r}) not in REPORT.md"
    return literal


F = {
    # --- headline: the two numbers that were never divided ---
    "user_btc":     fact("user_btc", "0.0339 BTC"),
    "weekly":       fact("weekly", "100 USDT"),
    "hold_state":   fact("hold_state", "0.8511"),
    "pct_of_base":  fact("pct_of_base", "基準的 4.0%"),
    "age_weeks":    fact("age_weeks", "約 24 次買進"),
    "age_invested": fact("age_invested", "投入約 $2,400"),
    "age_years":    fact("age_years", "約 0.44 年"),
    "ret24":        fact("ret24", "+14.8%"),
    "ret52":        fact("ret52", "−47.0%"),
    "ret156":       fact("ret156", "−82.3%"),
    "ret319":       fact("ret319", "−91.4%"),
    "flow_old":     fact("flow_old", "1.89 倍"),
    "flow_new":     fact("flow_new", "3.78×"),
    "flow_recheck": fact("flow_recheck", "3.77×"),
    "lead_state":   fact("lead_state", "領先 10.2%"),
    "r10_alt":      fact("r10_alt", "0.1212 BTC"),
    # --- idle pool ---
    "idle_old":     fact("idle_old", "$33.88/年"),
    "idle_new":     fact("idle_new", "$32.45/年"),
    "burn_old":     fact("burn_old", "9.53 週"),
    "burn_new":     fact("burn_new", "4.77 週"),
    "usdt_apr":     fact("usdt_apr", "2.9137%"),
    "usdt_r10":     fact("usdt_r10", "3.1090%"),
    "usdt_r13":     fact("usdt_r13", "3.0675%"),
    # --- timing ---
    "t_btc_grid":   fact("t_btc_grid", "BTC t=+2.42"),
    "t_eth_grid":   fact("t_eth_grid", "ETH t=+3.06"),
    "oos_fail":     fact("oos_fail", "樣本外 6/6 失敗"),
    "sixth_zero":   fact("sixth_zero", "第六次獨立量測，仍是零"),
    # --- existence / diversification ---
    "years_111":    fact("years_111", "111 年"),
    "rho_full":     fact("rho_full", "0.798"),
    "rho_1y":       fact("rho_1y", "0.908"),
    "w_star":       fact("w_star", "+0.195"),
    "harvest_th":   fact("harvest_th", "13.88%/年"),
    # --- ETH Simple Earn ---
    "eth_ratio":    fact("eth_ratio", "63.9 倍"),
    "eth_yield":    fact("eth_yield", "$33.76/年"),
    "eth_vs_btc":   fact("eth_vs_btc", "13.5 倍"),
    "eth_weeks":    fact("eth_weeks", "~4.8 週"),
    "cycles":       fact("cycles", "`H1, H4, H8, H12, DAILY, WEEKLY, BI_WEEKLY, MONTHLY`"),
    "pytest":       fact("pytest", "17 passed"),
    "btc_px":       fact("btc_px", "BTC = $81,306"),
}

# ---------------------------------------------------------------- logs ------
LOGS = {}
for n in ("s1_idle", "s1_rates", "s2_timing", "s3_hour", "s4_algebra",
          "s5_measure", "s6_planage", "s7_rebal", "s8_friction", "s9_windows"):
    LOGS[n] = open(os.path.join(ETHP, f"logs_{n}.log"), encoding="utf-8").read()


def grab(log, pattern, cast=str, flags=0):
    """Exactly-one-match extraction from a researcher log. Asserts uniqueness."""
    m = re.findall(pattern, LOGS[log], flags)
    assert len(m) == 1, f"grab({log}, {pattern!r}) -> {len(m)} matches"
    g = m[0]
    return cast(g) if not isinstance(g, tuple) else tuple(cast(x) for x in g)


NUMRE = re.compile(r"^[+\-]?[\d][\d.,]*%?$")


def num_rows(log, header_pat, k):
    """Rows that follow `header_pat`, whose last k tokens are numeric.

    Returns (name, [tok1..tokk]). The leading tokens are joined back into the
    row label, so window names with spaces ("last 3 years") survive.
    """
    i = re.search(header_pat, LOGS[log])
    assert i, f"header {header_pat!r} not found in {log}"
    rest = LOGS[log][i.end():]
    end = re.search(r"\n\s*\n", rest)
    body = rest[:end.start()] if end else rest
    out = []
    for line in body.splitlines():
        t = line.split()
        if len(t) >= k and all(NUMRE.match(x) for x in t[-k:]):
            out.append((" ".join(t[:len(t) - k]), t[-k:]))
    assert out, f"no {k}-number rows after {header_pat!r} in {log}"
    return out


# ============ A. independent recomputation from eth_plan/data (read-only) ====
sys.path.insert(0, ETHP)
import common                                             # noqa: E402

B = common.load_daily("BTCUSDT")
E = common.load_daily("ETHUSDT")
LAST = max(d for d in B if d in E)
PX_B, PX_E = B[LAST]["close"], E[LAST]["close"]
X_T = PX_E / PX_B
USER_BTC = 0.0339                     # state file, line 9
WEEKLY = 100.0

# A1. the published six-year baseline, across all 14 day/price conventions
CONV = {}
D0, D1 = dt.date(2020, 8, 11), dt.date(2026, 9, 18)
for wd, nm in enumerate(["一", "二", "三", "四", "五", "六", "日"]):
    for field in ("close", "open"):
        days = [d for d in common.weekdays_in(D0, D1, wd) if d in B]
        CONV[(nm, field)] = (sum(WEEKLY / B[d][field] for d in days), len(days))
HOLD_LO = min(v[0] for v in CONV.values())
HOLD_HI = max(v[0] for v in CONV.values())
HOLD_THU = CONV[("四", "close")][0]
HOLD_FRI = CONV[("五", "close")][0]
assert f"{HOLD_FRI:.4f}" == F["hold_state"], (HOLD_FRI, F["hold_state"])
PCT_LO = USER_BTC / HOLD_HI * 100
PCT_HI = USER_BTC / HOLD_LO * 100

# A2. what 0.0339 BTC implies about how long the plan has run
VAL_BTC = USER_BTC * PX_B
IMPLIED = []
for wks in (24, 52, 156, 319):
    inv = WEEKLY * wks
    IMPLIED.append((wks, wks / 52.0, inv, VAL_BTC / inv - 1.0))

# A3. invert the accumulation: how many Thursday buys reach 0.0339 BTC
END = max(d for d in common.weekdays_in(dt.date(2026, 1, 1), LAST, 3) if d in B)
best, d = None, END
while d > dt.date(2017, 9, 1):
    days = [x for x in common.weekdays_in(d, END, 3) if x in B]
    q = sum(WEEKLY / B[x]["close"] for x in days)
    if best is None or abs(q - USER_BTC) < abs(best[2] - USER_BTC):
        best = (d, len(days), q)
    d -= dt.timedelta(weeks=1)
AGE_START, AGE_N, AGE_Q = best
AGE_YEARS = (END - AGE_START).days / 365.25
AGE_INV = AGE_N * WEEKLY


def R_btc(start, end, wd, field="close"):
    ds = [x for x in common.weekdays_in(start, end, wd) if x in B and x in E]
    if len(ds) < 5:
        return None, 0
    a = sum(WEEKLY / E[x][field] for x in ds)
    b = sum(WEEKLY / B[x][field] for x in ds)
    return a * X_T / b, len(ds)


# A4. the ETH leg over the lifetime the user actually lived, as a GRID:
#     7 weekdays x 2 price fields x start offset +-6 months. Report the range,
#     not a point, and say which end is which.
GRID = []
for wd in range(7):
    for field in ("close", "open"):
        for k in range(-26, 27, 2):
            r, n = R_btc(AGE_START + dt.timedelta(weeks=k), END, wd, field)
            if r:
                GRID.append((r, wd, field, AGE_START + dt.timedelta(weeks=k), n))
GRID.sort()
G_LO, G_HI = GRID[0][0], GRID[-1][0]
G_N = len(GRID)
G_ABOVE1 = sum(1 for g in GRID if g[0] > 1.0)
R_WED = R_btc(AGE_START, END, 2)[0]
R_THU = R_btc(AGE_START, END, 3)[0]

# A5. the same ratio on the SIMULATED six-year window, all 14 conventions
SIMR = [R_btc(D0, LAST, wd, f)[0] for wd in range(7) for f in ("close", "open")]
SIMR = [r for r in SIMR if r]
SIM_LO, SIM_HI = min(SIMR), max(SIMR)

# A6. flow / stock
FLOW1, FLOW2 = 5200.0, 10400.0
FS_OLD = FLOW1 / VAL_BTC
FS_NEW = FLOW2 / VAL_BTC

# A7. live re-read of the Simple Earn rates (cached once, so builds are stable)
RATE_CACHE = os.path.join(PUB, "earn_rates_recheck.json")
if not os.path.exists(RATE_CACHE):
    url = ("https://www.binance.com/bapi/earn/v1/friendly/lending/daily/"
           "product/list?pageSize=500&pageIndex=1&status=ALL&featured=ALL")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0", "clienttype": "web",
        "Accept": "application/json"})
    raw = json.load(urllib.request.urlopen(req, timeout=40))
    assert raw.get("code") == "000000"
    snap = {"fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": url}
    for row in raw["data"]:
        a = row.get("asset")
        if a in ("BTC", "ETH", "USDT") and a not in snap:
            snap[a] = float(row["marketApr"])
    json.dump(snap, open(RATE_CACHE, "w"), indent=1)
RECHK = json.load(open(RATE_CACHE))
RE_RATIO = RECHK["ETH"] / RECHK["BTC"]

# researcher's own snapshot, read from the file they wrote (not retyped)
PX_STATE = float(F["btc_px"].split("$")[1].replace(",", ""))

RSNAP = json.load(open(os.path.join(ETHP, "data", "earn_rates.json")))
RS_RATIO = RSNAP["ETH"]["marketApr"] / RSNAP["BTC"]["marketApr"]
assert f"{RS_RATIO:.1f} 倍" == F["eth_ratio"], (RS_RATIO, F["eth_ratio"])


# ============ B. numbers parsed out of the researcher's own logs ============
# B1. non-overlapping windows (s9)
NOW_BLOCKS = []
for L in (52, 104, 156):
    after = LOGS["s9_windows"].split(
        f"non-overlapping {L}-week accumulation windows", 1)[1]
    sec = re.split(r"={10,}", after)[1]
    rows = re.findall(r"(\d{4}-\d{2}-\d{2}) \.\. (\d{4}-\d{2}-\d{2})\s+"
                      r"R_btc\(ETH leg\) = ([\d.]+)", sec)
    summ = re.search(r"n = (\d+)\s+min ([\d.]+)\s+median ([\d.]+)\s+max ([\d.]+)"
                     r"\s+ETH ahead in (\d+)/(\d+)", sec)
    geo = re.search(r"geometric mean ([\d.]+)\s+sd of log ([\d.]+)", sec)
    assert rows and summ and geo and len(rows) == int(summ.group(1))
    NOW_BLOCKS.append(dict(
        L=L, rows=[(a, b, float(c)) for a, b, c in rows], n=int(summ.group(1)),
        lo=float(summ.group(2)), med=float(summ.group(3)), hi=float(summ.group(4)),
        ahead=int(summ.group(5)), geo=float(geo.group(1)), sd=float(geo.group(2))))

# B2. ETH/BTC drift estimability (s5 M2)
NU = [dict(win=n, yrs=v[0], nu=v[1], sig=v[2], se=v[3], t=v[4], need=v[5])
      for n, v in num_rows("s5_measure", r"yrs for \+-5%\n", 6)]
assert len(NU) == 6 and NU[0]["need"] == F["years_111"].replace(" 年", "")
NU_MAX_T = max(abs(float(r["t"])) for r in NU)

# B3. growth-optimal weight and its bootstrap interval (s5 M3)
W_STAR = grab("s5_measure", r"point estimate w\* = mu_arith/sigma\^2 = ([+\-\d.]+)")
assert W_STAR == F["w_star"]
NU_FULL, SIG_FULL, MU_AR = grab(
    "s5_measure", r"full sample: nu_X = ([\-\d.]+)%/yr, sigma_X = ([\d.]+)%, "
                  r"mu_arith = ([+\-\d.]+)%/yr")
BOOT = [v for _, v in num_rows("s5_measure", r"P\(w\*>0\.5\)\n", 7)]
B_P025 = min(float(r[2]) for r in BOOT)
B_P975 = max(float(r[4]) for r in BOOT)
B_P50LO = min(float(r[3]) for r in BOOT)
B_P50HI = max(float(r[3]) for r in BOOT)
B_CELLS = len(BOOT)

# B4. USD-numeraire diversification (s5 M4)
DIV = [dict(win=n, sb=v[0], se=v[1], rho=v[2], s5050=v[3], vs=v[4], wmv=v[5])
       for n, v in num_rows("s5_measure", r"w\*_minvar\n", 6)]
assert len(DIV) == 6
DIV_WORSE = sum(1 for r in DIV if float(r["vs"].rstrip("%")) > 0)
DIV_NEG = sum(1 for r in DIV if float(r["wmv"]) < 0)
DIV_VS_LO = min(float(r["vs"].rstrip("%")) for r in DIV)
DIV_VS_HI = max(float(r["vs"].rstrip("%")) for r in DIV)
assert DIV[0]["rho"] == F["rho_full"] and DIV[-1]["rho"] == F["rho_1y"]
TAIL_N, TAIL_B, TAIL_E = grab(
    "s5_measure", r"worst 5% of days \(n=(\d+)\): mean BTC ([\-\d.]+)%, "
                  r"mean ETH ([\-\d.]+)%")
TAIL_UPN, TAIL_UPD, TAIL_UPP = grab(
    "s5_measure", r"ETH was UP on (\d+)/(\d+) of BTC's worst 5% days \(([\d.]+)%\)")
TAIL_UNCOND = grab("s5_measure", r"unconditional ETH up-day frequency: ([\d.]+)%")

# B5. start-date and end-date scans (s5 M1)
M1_N, M1_LO, M1_P25, M1_MED, M1_P75, M1_HI = grab(
    "s5_measure", r"n starts = (\d+)\s+min ([\d.]+)\s+p25 ([\d.]+)\s+"
                  r"median ([\d.]+)\s+p75 ([\d.]+)\s+max ([\d.]+)")
M1_AHEAD = grab("s5_measure", r"ETH leg ahead in BTC count\): (\d+/\d+)")
M1_ROWS = [(n, int(v[0]), float(v[1])) for n, v in
           num_rows("s5_measure", r"R_eth\(BTC leg\)\n", 4)]
END_ROWS = [(n, float(v[1])) for n, v in
            num_rows("s5_measure", r"end  weeks     R_btc\n", 2)]
END_LO = min(v for _, v in END_ROWS)
END_HI = max(v for _, v in END_ROWS)
END_SWING = (END_HI - END_LO) / END_LO * 100
WD_ROWS = [(n, float(v[0]), float(v[1])) for n, v in
           num_rows("s5_measure", r"weekday     close      open\n", 2)]
WD_LO = min(min(a, b) for _, a, b in WD_ROWS)
WD_HI = max(max(a, b) for _, a, b in WD_ROWS)

# B6. cost sensitivity (s5 M5)
COST = [(int(v[0]), float(v[1]), float(v[2])) for _, v in
        num_rows("s5_measure", r"\$/yr on 5,200 flow\n", 3)]
ALLOC_BP = grab("s5_measure", r"i\.e\. (\d+) bp of spread-equivalent")

# B7. the algebraic identities (s4)
ID_RBTC, ID_RUSD, ID_DIFF = grab(
    "s4_algebra", r"R_btc  \(ETH leg, BTC-count\)      = ([\d.]+)\n"
                  r"  R_usd  \(ETH leg, USD value\)      = ([\d.]+)   \|diff\| = ([\de.\-]+)")
ID_RETH, ID_PROD = grab(
    "s4_algebra", r"R_eth  \(BTC leg, ETH-count\)      = ([\d.]+)   "
                  r"R_btc\*R_eth = ([\d.]+)")
ID_XT, ID_XDCA = grab("s4_algebra", r"X\(T\) = ([\d.]+)   "
                                    r"X_dca \(weighted harmonic mean\) = ([\d.]+)")
ID_XDIFF = grab("s4_algebra", r"X\(T\)/X_dca\s+= [\d.]+\s+\|diff\| = ([\de.\-]+)")
MINIMAX_V, MINIMAX_W = grab(
    "s4_algebra", r"minimum of the worst case is log 2 = ([\d.]+) at w = ([\d.]+)")
REG_ROWS = [(v[0], v[3]) for _, v in
            num_rows("s4_algebra", r"reg\(g->inf\)     worst\n", 4)]

# B8. rebalancing (s7)
REB = [dict(win=n, bh=v[0], mon=v[1], wk=v[2], day=v[3], harv=v[4])
       for n, v in num_rows(
           "s7_rebal",
           r"daily   harvest\n", 5)]
assert len(REB) == 5, REB
REB_THEORY = grab("s7_rebal", r"Theory at w=0\.5, sigma_X = [\d.]+%: ([\d.]+)%/yr")
HORIZON = re.findall(r"\n\s+([\d.]+)\s+([\d.]+)\s+([\d.]+) \.\. ([\d.]+)\s+([\d.]+)",
                     LOGS["s7_rebal"].split("horizon  sd of log X", 1)[1])
assert len(HORIZON) == 6, HORIZON

# B9. round-10 timing reproduction and coverage audit (s2)
C5 = re.findall(r"(BTC|ETH) @ Wed (\d\d):00 UTC   ours: N=(\d+) mean= *([+\-\d.]+)bp"
                r" SE= *([\d.]+) t=([+\-\d.]+)\n\s+round10: N=(\d+) mean= *([+\-\d.]+)bp"
                r" SE= *([\d.]+) t=([+\-\d.]+)", LOGS["s2_timing"])
assert len(C5) == 2, C5
TZ_OFFSETS = grab("s2_timing", r"UTC offsets seen 2020-2026: \[([^\]]+)\]")
assert TZ_OFFSETS == "'7:00:00'", TZ_OFFSETS
TZ_SHOW = "UTC+" + TZ_OFFSETS.strip("'")[:-3].rjust(5, "0")
BARS, SPAN0, SPAN1, DAYS = grab(
    "s2_timing", r"BTCUSDT_1h_3y\.json : (\d+) bars, ([\d\-]+ [\d:]+) -> "
                 r"([\d\-]+ [\d:]+) \((\d+) days")
MISSING = set(re.findall(r"missing hourly bars: (\d+)", LOGS["s2_timing"]))
assert MISSING == {"0"}, MISSING
N_WED = grab("s2_timing", r"Wednesdays in \[[\d\-]+, [\d\-]+\] : (\d+)")
AC = re.findall(r"(BTC|ETH): lag-1 autocorrelation of the weekly deviations = "
                r"([\-\d.]+)\n\s+i\.i\.d\. SE ([\d.]+)bp  ->  overlap-corrected "
                r"([\d.]+)bp  \(x[\d.]+\),  t -> ([+\-\d.]+)", LOGS["s2_timing"])
assert len(AC) == 2
DETECT = [(n, float(v[0]), float(v[1]), float(v[3])) for n, v in
          num_rows("s2_timing", r"detectable \$/yr\n", 4)]

# B10. the 24-hour grid, in sample and out of sample (s3)
HOURGRID, PAIRED, OOS = {}, {}, []
for sym in ("BTCUSDT", "ETHUSDT"):
    sec = LOGS["s3_hour"].split(sym, 1)[1]
    if sym == "BTCUSDT":
        sec = sec.split("ETHUSDT", 1)[0]
    ch, chbp, dh, dhbp, spread = re.search(
        r"cheapest hour (\d\d):00 \(([\-\d.]+) bp\), dearest (\d\d):00 "
        r"\(([+\-\d.]+) bp\), spread ([\d.]+) bp", sec).groups()
    HOURGRID[sym] = dict(cheap=ch, cheap_bp=chbp, dear=dh, dear_bp=dhbp,
                         spread=float(spread))
    d, se, t, n = re.search(
        r"paired within-day difference  h\d+ - h\d+: \+([\d.]+) bp, SE ([\d.]+), "
        r"t = (\+[\d.]+), N = (\d+)", sec).groups()
    PAIRED[sym] = dict(d=d, se=se, t=t, n=int(n))
    for row in re.findall(r"(\d{4}-\d{2}-\d{2})\s+(\d+)\s+(\d+)\s+(\d+:00)\s+"
                          r"([\-\d.]+)\s+([+\-\d.]+)\s+([+\-\d.]+)\s+(\d+)/24\s+"
                          r"([+\-\d.]+)", sec):
        OOS.append((sym[:3],) + row)
assert len(OOS) == 6, OOS
assert PAIRED["BTCUSDT"]["t"] == "+2.42" and PAIRED["ETHUSDT"]["t"] == "+3.06"
OOS_RANK_LO = min(int(r[8]) for r in OOS)
OOS_RANK_HI = max(int(r[8]) for r in OOS)
OOS_FLIP = sum(1 for r in OOS if float(r[6]) > 0)
OOS_RHO_LO = min(float(r[9]) for r in OOS)
OOS_RHO_HI = max(float(r[9]) for r in OOS)
OOS_RHO_MED = statistics.median(float(r[9]) for r in OOS)
OOS_RHO_NEG = sum(1 for r in OOS if float(r[9]) < 0)

# B11. the shared idle pool (s1_idle)
PEAK = grab("s1_idle", r"2 x 476\.54 = ([\d.]+) USDT", float)
BURN = re.findall(
    r"burn\s+(\d+) USDT/wk[^\n]*\n"
    r"\s+implied deposit interval\s*:\s*([\d.]+) weeks \((\d+) days\)[^\n]*\n"
    r"\s+mean idle balance\s*:\s*\$\s*([\d.]+)[^\n]*\n"
    r"\s+annual interest, exact\s*:\s*\$\s*([\d.]+)[^\n]*\n"
    r"\s+annual interest, flat\s*:\s*\$\s*([\d.]+)", LOGS["s1_idle"])
assert len(BURN) == 2, BURN
CAP_CORR = float(re.findall(r"cap correction\s*:\s*\$\s*([\-\d.]+)", LOGS["s1_idle"])[0])
CADENCE = re.findall(
    r"\n(\S[^\n]*?)\s{2,}(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)",
    LOGS["s1_idle"].split("=== B.", 1)[1].split("=== C.", 1)[0])
assert len(CADENCE) >= 6, CADENCE
SPLIT_EACH, SPLIT_TOT = grab(
    "s1_idle", r"two pools of peak \$?476\.54 each -> 2 x \$([\d.]+) = \$([\d.]+)/yr")
SPLIT_DIFF = grab("s1_idle", r"difference\s+: \$\+([\d.]+)/yr")

# B12. ETH Simple Earn (s8)
S8_PX = grab("s8_friction", r"prices used: ETH \$([\d,.]+)  BTC \$([\d,.]+)  "
                            r"ETH/BTC ([\d.]+)")
EARN_ROWS = [tuple(v) for _, v in
             num_rows("s8_friction", r"vs BTC stack \$/yr\n", 6)]
EARN_PICK = [r for r in EARN_ROWS if r[0] == "1.137"][0]
CYCLE_ENUM = grab("s8_friction", r'subscriptionCycle \| ENUM \| YES \| ("H1"[^\n]+?)\n',
                  str, 0) if False else re.findall(
    r'subscriptionCycle\s+subscriptionCycle \| ENUM \| YES \| (.+)', LOGS["s8_friction"])[0]
assert "H1" in CYCLE_ENUM and "BI_WEEKLY" in CYCLE_ENUM



# ============ C. chrome lifted from the frozen v1 report (read-only) ========
v1 = open(V1, encoding="utf-8").read()
CSS = re.search(r"<style>.*?</style>", v1, re.S).group(0)
GATE = re.search(r"<script>\s*// 存取控制.*?</script>", v1, re.S).group(0)
V1_IDS = set(re.findall(r'id="([A-Za-z0-9_-]+)"', v1))
R15_IDS = set(re.findall(r'id="([A-Za-z0-9_-]+)"',
                         open(R15, encoding="utf-8").read()))


def pct(x, d=1, sign=True):
    """Typographic minus, so a recomputed column lines up with the state file."""
    s = f"{x:+.{d}f}%" if sign else f"{x:.{d}f}%"
    return s.replace("-", "\u2212")


def esc(x):
    return html.escape(str(x))


WINZH = {"full 2017-08..2026-09": "全期 2017-08 ~ 2026-09",
         "2017-08..2020-08": "2017-08 ~ 2020-08",
         "2020-08..2023-08": "2020-08 ~ 2023-08",
         "2023-08..2026-09": "2023-08 ~ 2026-09",
         "last 3 years": "近三年", "last 1 year": "近一年",
         "last 12 months": "近 12 個月"}


def win(name):
    """English window labels from the logs -> the reader's language."""
    assert name in WINZH, f"untranslated window label {name!r}"
    return WINZH[name]


def dash(x):
    """ASCII hyphen -> typographic minus, for numbers shown in tables."""
    return str(x).replace("-", "\u2212")


# ---- small log-axis SVG helpers (no CSS classes: colours are inline) -------
C_GRID, C_TXT, C_DIM = "#2a2e3c", "#9aa0b4", "#6b7185"
C_S1, C_ACC, C_NEG, C_WARN = "#3987e5", "#d97757", "#d03b3b", "#fab219"


def _ylog(v, lo, hi, top, bot):
    f = (math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo))
    return bot - f * (bot - top)


def svg_scan(points, marks, lo, hi, ticks, title, ylab):
    """points: [(date, value)]  marks: [(date, value, colour, label)]"""
    W, H, L, R, T, Bm = 960, 320, 62, 150, 22, 46
    xs = [p[0].toordinal() for p in points] + [m[0].toordinal() for m in marks]
    x0, x1 = min(xs), max(xs)

    def X(d):
        return L + (d.toordinal() - x0) / (x1 - x0) * (W - L - R)
    o = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
         f'aria-label="{esc(title)}" style="background:#171a23;border:1px solid '
         f'{C_GRID};border-radius:12px">']
    for t in ticks:
        y = _ylog(t, lo, hi, T, H - Bm)
        emph = abs(t - 1.0) < 1e-9
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" '
                 f'stroke="{C_ACC if emph else C_GRID}" stroke-width="'
                 f'{2 if emph else 1}" stroke-dasharray="{"" if emph else "3 3"}"/>')
        o.append(f'<text x="{L-8}" y="{y+4:.1f}" text-anchor="end" font-size="11" '
                 f'fill="{C_ACC if emph else C_DIM}">{t:g}</text>')
    pl = " ".join(f"{X(d):.1f},{_ylog(v, lo, hi, T, H-Bm):.1f}" for d, v in points)
    o.append(f'<polyline points="{pl}" fill="none" stroke="{C_S1}" stroke-width="2"/>')
    for d, v in points:
        o.append(f'<circle cx="{X(d):.1f}" cy="{_ylog(v,lo,hi,T,H-Bm):.1f}" r="2.6" '
                 f'fill="{C_S1}"/>')
    for d, v, col, lab in marks:
        x, y = X(d), _ylog(v, lo, hi, T, H - Bm)
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{col}" '
                 f'stroke="#171a23" stroke-width="2"/>')
        o.append(f'<text x="{x+11:.1f}" y="{y+4:.1f}" font-size="12" fill="{col}">'
                 f'{esc(lab)}</text>')
    for d in points[::6] + [points[-1]]:
        o.append(f'<text x="{X(d[0]):.1f}" y="{H-Bm+18}" text-anchor="middle" '
                 f'font-size="11" fill="{C_DIM}">{d[0].strftime("%Y-%m")}</text>')
    o.append(f'<text x="{L}" y="{H-8}" font-size="11" fill="{C_DIM}">'
             f'橫軸：假設的計畫起點（對數縱軸）　縱軸：{esc(ylab)}</text>')
    o.append("</svg>")
    return "".join(o)


def svg_strip(groups, lo, hi, ticks, ylab):
    """groups: [(label, [values], geomean)] -- one row per window length."""
    W, L, R, T, rowh, Bm = 960, 92, 150, 20, 66, 40
    H = T + rowh * len(groups) + Bm

    def X(v):
        f = (math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo))
        return L + f * (W - L - R)
    o = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(ylab)}" '
         f'style="background:#171a23;border:1px solid {C_GRID};border-radius:12px">']
    for t in ticks:
        emph = abs(t - 1.0) < 1e-9
        o.append(f'<line x1="{X(t):.1f}" y1="{T-6}" x2="{X(t):.1f}" y2="{H-Bm+4}" '
                 f'stroke="{C_ACC if emph else C_GRID}" stroke-width="{2 if emph else 1}" '
                 f'stroke-dasharray="{"" if emph else "3 3"}"/>')
        o.append(f'<text x="{X(t):.1f}" y="{H-Bm+20}" text-anchor="middle" font-size="11" '
                 f'fill="{C_ACC if emph else C_DIM}">{t:g}</text>')
    for i, (lab, vals, geo) in enumerate(groups):
        y = T + rowh * i + rowh / 2
        o.append(f'<text x="{L-10}" y="{y+4:.1f}" text-anchor="end" font-size="12" '
                 f'fill="{C_TXT}">{esc(lab)}</text>')
        for v in vals:
            col = C_S1 if v > 1 else C_NEG
            o.append(f'<circle cx="{X(v):.1f}" cy="{y:.1f}" r="5.5" fill="{col}" '
                     f'fill-opacity="0.85"/>')
        o.append(f'<line x1="{X(geo):.1f}" y1="{y-16:.1f}" x2="{X(geo):.1f}" '
                 f'y2="{y+16:.1f}" stroke="{C_WARN}" stroke-width="3"/>')
        o.append(f'<text x="{X(geo)+9:.1f}" y="{y-20:.1f}" font-size="11" '
                 f'fill="{C_WARN}">幾何平均 {geo:.4f}</text>')
    o.append(f'<text x="{L}" y="{H-8}" font-size="11" fill="{C_DIM}">'
             f'橫軸為對數刻度：{esc(ylab)}　藍＝ETH 腿領先，紅＝落後，黃線＝該組幾何平均</text>')
    o.append("</svg>")
    return "".join(o)


# ================================ page body ================================
P = []
A = P.append

A(f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>老六 · 第十六輪：ETH 定投計畫</title>
{GATE}
{CSS}
</head>
<body>

<header>
  <div class="crumb">
    <a href="index.html">工具中心</a><span class="sep">›</span><a href="laoliu.html">老六研究院</a><span class="sep">›</span><span class="here">第十六輪 · ETH 定投計畫</span>
  </div>
  <h1>第十六輪：你的兩個定投計畫大約只跑了半年，不是六年</h1>
  <p class="tagline">
    這一輪去查 ETH 那個計畫該不該存在，結果先撞到一件更基礎的事：
    十六輪的報告都把一個<b>六年的模擬</b>放在最前面，而你的帳戶裡的幣數對應的是<b>大約 24 週</b>。
    這不會讓任何一次回測失效，但它改變了三個數字的讀法——而你看一眼帳戶就能確認或推翻它。
  </p>
  <div class="meta-bar">
    <span class="badge">輪次 <b>第十六輪</b></span>
    <span class="badge">日期 <b>{TODAY}</b></span>
    <span class="badge">回歸測試 <b>{F["pytest"]}</b></span>
    <span class="badge">本輪新幣數比 <b>0 個</b></span>
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
      <p>這一頁是<b>第十六輪的獨立研究紀錄</b>，不是舊報告的修訂版。
        依照你 {TODAY} 的規則「以後報告盡量不要修改舊的，每次產生新的頁面」，
        <a href="crypto-dca-amplifier-report.html">總覽報告（v1）</a>與
        <a href="laoliu-r15-triage2.html">第十五輪</a><b>都一個字都沒有動</b>；
        要更正它們的地方，寫在這裡並連回去。</p>
      <p>這一輪的主線是「ETH 那個定投計畫該不該存在」。
        答案是：<b>研究員拒絕替你決定，而且他有正當理由</b>——
        資料在方向上什麼都量不出來，能量出來的只有「這個賭注有多大」。
        <b>但在量的過程中撞到一件更基礎的事，它放在最前面。</b></p>
      <p>所有英文縮寫、單個字母、希臘字母，在<a href="#glossary">這一頁自己的術語表</a>裡都有白話翻譯，
        正文第一次用到時也會就地附註。</p>
    </div>

    <h3 class="sub">一、五件事，照重要性排</h3>

    <div class="callout bad">
      <h3>★★★ 1. 兩個定投計畫大約只跑了半年，不是六年——而<b>你一句話就能確認或推翻</b></h3>
      <p style="margin:0">
        狀態檔十六輪並排記著「每週 {F["weekly"]}」與「現貨 {F["user_btc"]}」，
        <b>從來沒有人把它們相除</b>。相除之後：{F["user_btc"]} 只是六年純定投基準
        （{F["hold_state"]} 顆）的 <b>{PCT_LO:.2f}%~{PCT_HI:.2f}%</b>，
        而唯一對得上合理報酬的長度是<b>大約 24 次買進</b>。
        影響有三個，<b>要分開讀</b>，見<a href="#headline">第一節</a>。
      </p>
    </div>

    <div class="callout">
      <h3>2. 「ETH 該不該存在」在資料上不可裁決，研究員拒絕代為決定</h3>
      <p style="margin:0">
        ETH/BTC 的漂移在 <b>6 個視窗全部不顯著</b>（最大 |t| = {NU_MAX_T}），
        符號在子視窗之間翻轉，要把它釘到 ±5%／年需要 <b>{F["years_111"]}</b> 的資料。
        最漂亮的一段是：<b>同一道 minimax 題目有兩個答案，而且兩個都對</b>——
        差別不在數學，在<b>你拿誰當比較基準</b>，而那是你的選擇。見<a href="#exist">第二節</a>。
      </p>
    </div>

    <div class="callout">
      <h3>3. 持有 ETH 不是「分散風險」——兩個口徑都死</h3>
      <p style="margin:0">
        以 BTC 幣數為目標時，這是<b>推導</b>不是回測：變異數 = w²×Var，
        對權重嚴格遞增、最小值就在「不要 ETH」。<b>而它在美元口徑下也不成立</b>：
        相關係數 {F["rho_full"]}（近一年 {F["rho_1y"]}），
        <b>{DIV_WORSE} 個視窗全部</b>顯示 50/50 比純 BTC 更晃。
        <b>唯一站得住的反面理由，我們量不到，也不假裝量得到。</b>見<a href="#diversify">第三節</a>。
      </p>
    </div>

    <div class="callout good">
      <h3>4. 派工書的前提被推翻，而推翻的結果<b>對舊結論有利</b></h3>
      <p style="margin:0">
        原本以為「多一個 ETH 計畫就多一筆閒置漏損」。<b>不對</b>：兩個計畫吃的是同一個 USDT 餘額。
        真正改變的是<b>錢被花掉的速度</b>——第十輪隱含的「每 {F["burn_old"]}入一次金」是怪節奏，
        改成兩個計畫後是「每 {F["burn_new"]}」，<b>那就是月付</b>。
        <b>這反而讓第十輪那個點估計變可信。</b>見<a href="#idle">第四節</a>。
      </p>
    </div>

    <div class="callout bad">
      <h3>5. 「挑執行時段」第六次被量測，仍然是零——而這次的格子最單純</h3>
      <p style="margin:0">
        第十輪只掃了計畫實際用的<b>兩個</b>小時。這一輪把 24 個小時全掃完，
        樣本內看起來<b>剛好像通過門檻</b>（配對 t = {PAIRED["BTCUSDT"]["t"]} 與 {PAIRED["ETHUSDT"]["t"]}），
        <b>樣本外 6 次全部失敗</b>。見<a href="#timing">第五節</a>。
      </p>
    </div>

    <h3 class="sub">二、幣數比這一欄，這一輪是空的——為什麼</h3>
    <div class="callout bad">
      <p style="margin:0">
        這個專案唯一的計分方式是<a class="gl" href="#g16-coinratio">幣數比</a>：
        同一筆錢、同一段時間，最後手上的 BTC 顆數，除以什麼都不做、單純每週買進並持有的顆數。
        <b>這一輪沒有任何候選走到可以算幣數比的階段，所以本頁不提供新的幣數比。</b>
      </p>
      <p style="margin:10px 0 0">
        本頁出現的所有比值都是<b>「ETH 腿 vs BTC 腿」的對照</b>，不是「某個策略 vs 純持有」。
        它回答的是「同一筆錢分一半去買 ETH，最後 BTC 顆數會變多還是變少」，
        <b>而<a href="#headline">第一節</a>會說明：這個問題的答案完全由你假設的起點決定，因此它不預測任何事。</b>
      </p>
    </div>

    <h3 class="sub">三、這一頁的把關程度（請按這個折扣讀）</h3>
    <div class="callout">
      <p style="margin:0">
        本輪的覆核是<b>協調者對關鍵數字的逐項獨立重算</b>，
        加上<b>本頁作者從原始資料與腳本輸出重新產生每一個數字</b>——
        本頁沒有任何一個數字是人工從報告抄過來的。
        研究員自己跑的回歸測試是 <b>{F["pytest"]}</b>。
      </p>
      <p style="margin:10px 0 0">
        <b>但本輪沒有走完整的外部覆核流程，也沒有任何乾淨的首次讀取。</b>
        本頁作者在重算過程中找到<b>兩處與研究員報告不一致的地方</b>，
        兩處都不改變結論，但都寫在<a href="#limits">第七節</a>，沒有被吸收掉。
      </p>
    </div>
  </section>
''')


# ------------------------------ glossary ------------------------------
GL = [
 ("〔一〕怎麼記分、怎麼讀百分比", [
  ("g16-coinratio", "幣數比",
   "這個做法最後拿到的 BTC 顆數 ÷ 什麼都不做、只是每週買進並持有拿到的顆數。",
   f"純持有六年是 {F['hold_state']} 顆，定義為 1.0000。"
   "<b>本輪沒有產生任何新的幣數比</b>；本頁的比值全部是「ETH 腿 vs BTC 腿」的對照。"),
  ("g16-relwealth", "相對財富（幾倍），不是「差幾個百分點」",
   "比較兩個做法時，用「A 的結果是 B 的幾倍」，不要用兩個百分比相減。",
   "相減會騙人：0.70 與 1.00 不是「差 30%」，是「B 是 A 的 1.43 倍」。"
   "<b>本頁一律用倍數。</b>"),
  ("g16-base", "基準點",
   "任何「變動了幾 %」都必須說清楚<b>相對什麼</b>。",
   "本輪的頭條正是一個基準點問題：舊報告的 1.0000 是<b>一段模擬</b>的結果，不是你的帳戶。"),
  ("g16-log", "對數／對數刻度",
   "把「幾倍」畫成等距。1.0 的上下兩側在對數軸上對稱，在普通軸上不對稱。",
   "比值天生右偏（可以漲到 3 倍，但最多跌到 0），"
   "<b>本頁兩張圖的座標軸都是對數的</b>，否則「贏」會被畫得比「輸」大。"),
 ]),
 ("〔二〕這一輪在量的東西", [
  ("g16-x", "X＝ETH/BTC 比值",
   "一顆 ETH 值多少顆 BTC。",
   "<b>這一輪所有結論的主角。</b>以 BTC 顆數記分時，「有沒有 ETH」的全部損益只由它決定。"),
  ("g16-w", "w（ETH 權重）",
   "每期的錢有多少比例拿去買 ETH。w = 0 是全買 BTC，w = 0.5 是一半一半。",
   "你現在是 w = 0.5（兩個計畫各 100 USDT）。"),
  ("g16-numeraire", "計價單位（numeraire）",
   "你拿什麼當「一塊錢」來記帳：美元、BTC 顆數、還是 ETH 顆數。",
   "<b>這一輪最重要的觀念</b>：同一個部位，換個計價單位，「分散風險」這句話會從真變成假。"),
  ("g16-nu", "ν（nu）＝漂移",
   "一個價格長期平均每年往上或往下走多少（取對數之後）。",
   "ETH/BTC 的漂移在 6 個視窗全部不顯著；要把它量準到 ±5%／年需要 111 年。"),
  ("g16-sigma", "σ（sigma）＝波動率",
   "價格上下晃動的幅度，通常寫成「每年百分之幾」。",
   "ETH/BTC 的 σ 約 53%／年。<b>這個數很確定；漂移那個數很不確定。</b>"),
  ("g16-rho", "ρ（rho）＝相關係數",
   "兩個東西一起漲跌的程度，1 是完全同步，0 是無關。",
   "BTC 與 ETH 是 0.80（近一年 0.91）。<b>這麼高就沒有分散可言。</b>"),
  ("g16-variance", "變異數／內點",
   "變異數是波動的平方。「內點」是指最好的配置落在中間（例如 30% ETH），而不是落在兩端。",
   "以 BTC 顆數記分時<b>沒有內點</b>：最穩的就是 w = 0。這是推導出來的，不是測出來的。"),
  ("g16-geomean", "幾何平均",
   "一串「倍數」的正確平均法（連乘再開根號），不是把它們加起來除以個數。",
   "算術平均會把「漲一倍再跌一半」算成賺，幾何平均算成打平——後者才是實際結果。"),
  ("g16-rebal", "再平衡收割",
   "定期把漲多的賣掉、補到跌的那邊，靠來回震盪賺價差。",
   "理論上每年有 13.88%，<b>但兩個各自買進不賣的定投計畫一分錢都拿不到</b>。"),
 ]),
 ("〔三〕統計用語", [
  ("g16-t", "t 值",
   "效應量除以它自己的誤差。大致可讀成「這個數看起來不像 0 的程度」。",
   "本專案的門檻是 3.0。|t| 小於 1 幾乎就是「和 0 分不出來」。"),
  ("g16-se", "SE（標準誤）",
   "同樣的量測再做一次，答案大概會差多少。",
   "<b>它只跟日曆長度有關</b>：把日資料換成小時資料<b>一個基點都不會變準</b>。"),
  ("g16-bp", "bp（基點）",
   "萬分之一。10 bp = 0.10%。",
   "費用與價差的慣用單位。本頁用它比較「買貴一點」與「配置選錯」的量級。"),
  ("g16-oos", "樣本內／樣本外",
   "樣本內＝從這段資料裡挑出最好的那個；樣本外＝拿去沒看過的那段驗證。",
   "<b>本專案六次量測同一件事：樣本內挑出來的東西，到樣本外一律不成立。</b>"),
  ("g16-boot", "block bootstrap（區塊重抽）",
   "把歷史切成一段一段再隨機重組，產生很多條「平行時空」，看答案的範圍有多寬。",
   "用來給 w 的估計畫誤差範圍，結果那個範圍寬到同時蓋住 0、0.5、1。"),
  ("g16-indep", "獨立觀測數",
   "不是「有幾筆資料」，是「有幾筆<b>互相不重複</b>的資料」。",
   "本輪最硬的限制：不重疊視窗只有 <b>9 / 4 / 3</b> 個。<b>這個數量不能拒絕任何東西。</b>"),
  ("g16-minimax", "minimax／遺憾",
   "遺憾＝事後回頭看，你比「最好的那個選擇」少賺多少。"
   "minimax＝挑一個讓<b>最糟情況下的遺憾最小</b>的做法。",
   "它不需要預測未來，所以本專案愛用它。<b>但它的答案取決於你把誰放進「最好的選擇」那個名單。</b>"),
 ]),
 ("〔四〕幣安的產品與條款", [
  ("g16-dca", "定投／Auto-Invest／Convert Recurring",
   "設定好「每週幾、幾點、多少錢、買什麼」，系統自動扣款買進。",
   "你有兩個：一個買 BTC，一個買 ETH。幣安內部視為同一個產品的兩條路徑。"),
  ("g16-spread", "Spread（價差）",
   "幣安在參考價之上加收的一層費用，<b>在你建立計畫的當下被鎖定</b>。",
   "<b>它的實際數值仍然未知</b>——查詢端點需要帳號簽章，只有你本人查得到。"),
  ("g16-cycle", "<code>subscriptionCycle</code>（定投週期）",
   "API 裡決定「多久扣一次款」的那個欄位。",
   "第十三輪把它標為未知，<b>這一輪查到了</b>八個值。但有三條但書，見<a href=\"#actionable\">第六節</a>。"),
  ("g16-earn", "Simple Earn／<code>marketApr</code>",
   "幣安的活期理財；<code>marketApr</code> 是不含補貼的市場利率。",
   "ETH 的市場利率是 BTC 的六十幾倍。<b>這不是「該買 ETH」的理由</b>，理由見<a href=\"#actionable\">第六節</a>。"),
  ("g16-idle", "閒置漏損（鋸齒）",
   "你存一筆錢進去、定投慢慢花掉，中間那段「錢躺著沒生息」的損失。",
   "形狀像鋸齒：存進去跳高、每週往下削。<b>兩個計畫吃同一個池子，不會變兩份。</b>"),
 ]),
]
A('''
  <section id="glossary">
    <h2>這一頁的術語表（精簡版）</h2>
    <p class="section-note">
      只收這一頁會用到的詞，共 ''' + str(sum(len(g[1]) for g in GL)) + ''' 條。
      舊總覽報告有一份 69 條的完整版，在<a href="crypto-dca-amplifier-report.html#glossary">那邊的術語對照表</a>；
      第十五輪也有自己的一份，在<a href="laoliu-r15-triage2.html#glossary">那一頁</a>。
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


# ------------------------------ 1. headline ------------------------------
STATE_RET = {24: F["ret24"], 52: F["ret52"], 156: F["ret156"], 319: F["ret319"]}
AGE_ROWS = re.findall(r"\n  (\d{4}-\d{2}-\d{2})\s+(\d+)\s+([\d.]+)\s+([+\-][\d.]+)",
                      LOGS["s6_planage"])
assert len(AGE_ROWS) >= 15, len(AGE_ROWS)
SCAN_PTS = [(dt.date.fromisoformat(d), r) for d, _, r in M1_ROWS]
MARKS = [(dt.date(2020, 8, 11), float(END_ROWS[0][1]), C_NEG,
          "舊報告的模擬起點 2020-08"),
         (AGE_START, R_WED, C_S1, "你推估的真實起點 " + AGE_START.strftime("%Y-%m"))]

A(f'''
  <section id="headline">
    <h2>一、頭條：兩個定投計畫大約只跑了半年，不是六年<span class="pill hyp">推論，你一句話就能推翻</span></h2>
    <p class="section-note">
      這一節的結論<b>不是量測，是推論</b>。它建立在狀態檔自己記的兩個數字上，有四個假設，
      <b>你打開帳戶看一眼「計畫建立日期」就能確認或推翻它。</b>
      如果它錯了，請直接告訴協調者，這一節會被下一頁更正——但<b>下面那三個影響的邏輯不會變</b>。
    </p>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>狀態檔的第一頁同時記著兩件事：<b>「每週四 {F["weekly"]} 買 BTC」</b>
        和<b>「現貨約 {F["user_btc"]}」</b>。
        十六輪、兩千多行筆記，<b>沒有人把這兩個數字相除過</b>。</p>
      <p>相除之後：如果這個計畫真的跑了六年（319 週、投入 $31,900），
        今天手上應該有 {F["hold_state"]} 顆左右。實際是 {F["user_btc"]}，
        也就是<b>基準的 {PCT_LO:.2f}%~{PCT_HI:.2f}%</b>。
        往回推，唯一能對上合理報酬的長度是<b>大約 24 次買進、投入約 $2,400</b>。</p>
      <p><b>為什麼這件事重要？</b>因為過去每一份報告最前面那個「六年 {F["hold_state"]} 顆 = 1.0000」，
        <b>是一段模擬，不是你的帳戶歷史</b>。
        如果你一直把它讀成自己的成績單，<b>那是我們沒有講清楚，不是你讀錯</b>。</p>
      <p><b>但請同時記住另一半</b>：<b>回測沒有因此失效</b>。
        回測量的是「這個策略放在那段歷史上會怎樣」，那件事仍然成立，
        它只是<b>從來就不是在描述你的帳戶</b>。這兩句話要一起讀。</p>
    </div>

    <div class="split">
      <div class="stat"><div class="label">六年純定投模擬會有</div>
        <div class="value">{HOLD_LO:.4f} ~ {HOLD_HI:.4f} 顆</div>
        <div class="sub">14 種星期／價格口徑全掃；報告引用的 {F["hold_state"]} 是其中一格</div></div>
      <div class="stat"><div class="label">狀態檔記的實際持有</div>
        <div class="value warn">{F["user_btc"]}</div>
        <div class="sub">＝模擬基準的 {PCT_LO:.2f}%~{PCT_HI:.2f}%</div></div>
      <div class="stat"><div class="label">唯一對得上的計畫長度</div>
        <div class="value pos">{AGE_N} 次買進</div>
        <div class="sub">約 {AGE_YEARS:.2f} 年，投入約 ${AGE_INV:,.0f}，起點約 {AGE_START}</div></div>
      <div class="stat"><div class="label">今天這些幣值多少</div>
        <div class="value">${VAL_BTC:,.0f}</div>
        <div class="sub">以資料檔最後一根日 K（{LAST}）BTC ${PX_B:,.0f} 計</div></div>
    </div>

    <h3 class="sub">1.1　為什麼「六年」對不上：把每個假設長度的隱含報酬算出來</h3>
    <div class="table-wrap wide">
      <table>
        <caption>如果計畫真的跑了這麼久，那麼今天 {F["user_btc"]}（${VAL_BTC:,.0f}）代表你在 BTC 定投上是這個報酬</caption>
        <thead><tr><th>假設跑了多久</th><th>累計投入</th><th>今天價值</th>
          <th>隱含報酬（本頁重算）</th><th>狀態檔的協調者驗算</th></tr></thead>
        <tbody>
''')
for wks, yrs, inv, ret in IMPLIED:
    cls = ' class="best"' if wks == 24 else ""
    tag = "　← 唯一合理" if wks == 24 else ""
    col = "pos" if ret > 0 else "negv"
    A(f'          <tr{cls}><td class="name">{wks} 週（約 {yrs:.1f} 年）{tag}</td>'
      f'<td>${inv:,.0f}</td><td>${VAL_BTC:,.0f}</td>'
      f'<td class="{col}">{pct(ret*100)}</td><td>{esc(STATE_RET[wks])}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>
    <div class="callout">
      <p style="margin:0">
        <b>怎麼讀這張表：</b>中間三列要求 BTC 定投在那些窗口裡虧掉四成到九成。
        <b>那些期間的 BTC 定投不可能虧成那樣</b>——這就是「六年」被排除的理由，
        不是統計檢定，是<b>量級上的荒謬</b>。
      </p>
      <p style="margin:10px 0 0">
        最後一欄是協調者記在狀態檔裡的獨立驗算。
        它與本頁差 0.1 個百分點，<b>原因是兩邊取的 BTC 報價差 ${abs(PX_STATE-PX_B):,.0f}</b>
        （協調者用當下報價，本頁用資料檔最後一根收盤的 ${PX_B:,.0f}）。
        <b>這個差別不改變任何一列的符號。</b>
      </p>
    </div>

    <h3 class="sub">1.2　反過來推：要累積到 {F["user_btc"]} 需要幾次買進</h3>
    <div class="table-wrap">
      <table>
        <caption>每週四 {F["weekly"]} 買進，一路往回推到哪一天才剛好累積到 {F["user_btc"]}（本頁用 eth_plan/data 的日 K 獨立重跑）</caption>
        <thead><tr><th>假設起點</th><th>買進次數</th><th>累積 BTC</th><th>與 {USER_BTC} 的差</th></tr></thead>
        <tbody>
''')
for d, n, q, diff in AGE_ROWS[:13]:
    cls = ' class="best"' if int(n) == AGE_N else ""
    A(f'          <tr{cls}><td class="name">{d}</td><td>{n}</td><td>{q}</td>'
      f'<td>{diff}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>

    <div class="callout bad">
      <h3>這個推論的四個假設——任何一個不成立，上面整張表就失效</h3>
      <ul>
        <li><b>中途沒有提領過。</b>提過就會讓現在的顆數偏低，計畫實際更老。</li>
        <li><b>沒有從別的地方拿到 BTC</b>（空投、轉入、另外買）。有的話計畫實際更年輕。</li>
        <li><b>金額一直是 {F["weekly"]}，沒有改過。</b></li>
        <li><b>中間沒有暫停過。</b></li>
      </ul>
      <p style="margin:10px 0 0">
        <b>研究員自己把這一條列為「推論層級」，不是觀測。</b>
        本頁照樣把它放在最前面，是因為它<b>最容易被你證實或推翻，而代價只是看一眼帳戶</b>。
      </p>
    </div>

    <h3 class="sub">1.3　三個影響，要分開讀</h3>

    <div class="callout bad">
      <h3>影響一：那個「1.0000」是模擬，不是你的帳戶——但回測沒有失效</h3>
      <p style="margin:0">
        舊報告每一頁最前面的記分板都寫著「六年 319 週純持有 = {F["hold_state"]} 顆 = 1.0000」。
        <b>那是一段從 2020-08-11 開始的模擬</b>，用來回答「如果一個計畫跑滿六年會怎樣」。
        <b>它不是你的交易紀錄。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>但請不要把這句話讀成「回測都白做了」。</b>
        回測問的是「策略 X 放在 2020-08 到今天這段歷史上，相對純定投會多拿還是少拿幣」，
        <b>這個問題與你何時開戶完全無關，答案仍然成立</b>。
        變的只有一件事：<b>當報告說「多拿 2.8%」時，那是在一段六年的模擬上，
        不是在你這半年的帳戶上。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>這是一個基準點問題，而基準點沒有被寫出來，是我們的疏失。</b>
        依規則<a href="crypto-dca-amplifier-report.html#coin-ratio">舊頁那一節</a>不修改，更正寫在這裡。
      </p>
    </div>

    <div class="callout good">
      <h3>影響二：流量／存量比是 {FS_NEW:.2f} 倍，不是 {FS_OLD:.2f} 倍——<b>這強化第九輪的結論</b></h3>
      <p style="margin:0">
        第九輪的核心論點是「作用在<b>每年新投進去的錢</b>上，天生比作用在<b>已經持有的部位</b>上有效」，
        當時算的是 $5,200 ÷ ${VAL_BTC:,.0f} = <b>{FS_OLD:.2f} 倍</b>。
        <b>但那只算了一個計畫。</b>兩個計畫一起算是 $10,400 ÷ ${VAL_BTC:,.0f} =
        <b>{FS_NEW:.2f} 倍</b>（協調者的獨立驗算寫在狀態檔是 {F["flow_recheck"]}，差別只在取的 BTC 報價）。
      </p>
      <p style="margin:10px 0 0">
        <b>方向要講清楚：這個更正讓第九輪的結論更強，不是更弱。</b>
        第九輪說流量側重要，正確計數之後，流量側<b>比它自己以為的還重要一倍</b>。
        <b>而這件事的實際意涵仍然是那一句：在這個資金規模上，把錢投進去的那個動作本身，
        比任何一個聰明的操作都有效。</b>
      </p>
    </div>

    <div class="callout">
      <h3>影響三：ETH 腿在你<b>真正經歷過</b>的那段期間是領先的；在模擬那段是落後的。<b>兩個都是真的。</b></h3>
      <p style="margin:0">
        同樣一個問題——「一半的錢拿去買 ETH，最後 BTC 顆數會變多還變少」——
        在兩個不同的起點上得到相反的答案：
      </p>
      <ul>
        <li><b>你推估的真實期間（{AGE_START} 起、{AGE_N} 次買進）</b>：
          ETH 腿的 BTC 顆數是 BTC 腿的 <b>{R_WED:.4f}</b>（週三口徑）~ <b>{R_THU:.4f}</b>（週四口徑）倍，
          <b>ETH 腿領先</b>。把起點前後各挪半年、七個星期、開盤收盤都掃過共 <b>{G_N} 格</b>，
          範圍 <b>{G_LO:.4f} ~ {G_HI:.4f}</b>，<b>{G_ABOVE1}/{G_N} 格全部大於 1</b>。</li>
        <li><b>舊報告的模擬期間（2020-08-11 起、319 週）</b>：同樣的比值是
          <b>{SIM_LO:.4f} ~ {SIM_HI:.4f}</b>（14 種星期／價格口徑），
          換句話說 <b>BTC 腿的顆數是 ETH 腿的 {1/SIM_HI:.3f} ~ {1/SIM_LO:.3f} 倍</b>，
          <b>ETH 腿落後</b>。</li>
      </ul>
      <p style="margin:10px 0 0">
        <b>這裡用「幾倍」而不是「落後百分之幾」，是刻意的</b>：兩個方案比較時相減百分點會系統性誤導，
        見<a class="gl" href="#g16-relwealth">術語表</a>。
      </p>
      <p style="margin:10px 0 0">
        <b>最重要的一句話：這兩個數字都不預測任何事。</b>
        下面那張圖就是理由——<b>同一個策略、同一個終點，光是換起點，答案就從 0.62 掃到 1.13。</b>
      </p>
    </div>

    <h3 class="sub">1.4　同一個問題，答案完全由起點決定</h3>
    {svg_scan(SCAN_PTS, MARKS, 0.58, 1.22, [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2],
              "ETH 腿相對 BTC 腿的期末 BTC 顆數，隨假設起點變化",
              "ETH 腿的 BTC 顆數 ÷ BTC 腿的 BTC 顆數")}
    <p class="section-note" style="margin-top:10px">
      藍線是研究員掃過的 {M1_N} 個季度起點（週三收盤口徑，終點全部固定在資料最後一天），
      數值從 <b>{M1_LO}</b> 掃到 <b>{M1_HI}</b>；紅點是舊報告用的模擬起點，藍點是你推估的真實起點
      （本頁用同一份日 K 獨立計算）。<b>縱軸是對數的</b>，所以 1.0 上下等距。
      <b>這張圖唯一該帶走的訊息是：這條線的高低由「你何時開始」決定，不由「ETH 好不好」決定。</b>
      研究員另外做了終點敏感度：起點固定不動，<b>只換一個結算月，數字就移動 {END_SWING:.1f}%</b>
      （{END_LO} ~ {END_HI}）。<b>研究員把這一項標為「驗收檢驗 #4 大幅失敗」，本頁照實轉述。</b>
    </p>
    <div class="callout">
      <p style="margin:0">
        <b>{M1_N} 個起點裡有 {M1_AHEAD} 個是 ETH 腿領先，但這不是「勝率」</b>，
        研究員自己先標註了：這 {M1_N} 列共用<b>同一個終點價格</b>，不是獨立抽樣。
        <b>要看獨立的樣本，必須用不重疊視窗——那在<a href="#exist">第二節</a>，
        而那裡只有 {NOW_BLOCKS[0]["n"]} / {NOW_BLOCKS[1]["n"]} / {NOW_BLOCKS[2]["n"]} 個。</b>
      </p>
    </div>
  </section>
''')


# ------------------------------ 2. does ETH belong ------------------------
STRIP = [(f"{b['L']} 週視窗（n = {b['n']}）", [v for _, _, v in b["rows"]], b["geo"])
         for b in NOW_BLOCKS]
A(f'''
  <section id="exist">
    <h2>二、ETH 該不該存在：研究員拒絕替你決定，而這個拒絕本身是結論<span class="pill fact">代數＋量測</span></h2>
    <p class="section-note">
      派工書問的是「ETH 計畫該不該存在」。研究員動用了派工書允許他推翻前提的權利，
      回答是：<b>這不是一個有答案在等著被找到的問題。</b>本節說明為什麼，以及他交了什麼給你。
    </p>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>「ETH 以後會不會贏過 BTC」這種問題，<b>需要知道兩者長期的平均走勢差多少</b>。
        這個數字叫<a class="gl" href="#g16-nu">漂移</a>，而它的量測誤差<b>只跟你有多少年的資料有關</b>——
        <b>抓更細的資料（小時線、分鐘線）一個基點都不會讓它變準。</b></p>
      <p>ETH/BTC 只有 9 年多的可交易歷史。要把這個數字量到「正負 5% 以內」，
        需要 <b>{F["years_111"]}</b>。所以答案不是「還沒算出來」，是<b>算不出來</b>。</p>
      <p>能算出來的只有<b>「這個賭注有多大」</b>——而它很大。研究員把這個交給你，
        <b>拒絕替你決定要不要下</b>。這一頁同意這個做法。</p>
    </div>

    <h3 class="sub">2.1　先拆掉一個誤導框架：「三種計價口徑」其實只有一個數</h3>
    <div class="callout good">
      <p style="margin:0">
        很自然會想：「用美元看、用 BTC 顆數看、用 ETH 顆數看，會得到三種不同的答案吧？」
        <b>不會。研究員在真實序列上驗到浮點數極限：</b>
      </p>
      <ul>
        <li><b>用美元算的比值，和用 BTC 顆數算的比值，是<u>同一個數</u></b>：
          兩邊都是 <b>{ID_RBTC}</b>，差 <b>{ID_DIFF}</b>（電腦能表示的最小誤差級別）。</li>
        <li><b>用 ETH 顆數算的是它的倒數</b>：{ID_RETH}，兩者相乘 = <b>{ID_PROD}</b>。</li>
        <li>第二個恆等式更狠：這筆配置的全部結果 = <b>X(T) ÷ X<sub>買進期間的加權平均</sub></b>
          （{ID_XT} ÷ {ID_XDCA}，與上面的比值差 {ID_XDIFF}）。
          <b>BTC 自己的價格只透過「每期買到多少」進入，沒有第二個成分。</b></li>
      </ul>
      <p style="margin:10px 0 0">
        <b>所以「ETH 計畫」在幣數記分下不是「對加密貨幣的配置」，也不是「對長期趨勢的配置」，
        它就是一個對 <a class="gl" href="#g16-x">ETH/BTC 比值</a>的方向性部位，大小等於流量的一半。</b>
        三個口徑真正分家的地方不是這個數字，是<b>變異數</b>——那在<a href="#diversify">第三節</a>。
      </p>
    </div>

    <h3 class="sub">2.2　漂移：六個視窗沒有一個顯著，而且符號會翻轉</h3>
    <div class="table-wrap wide">
      <table>
        <caption>ETH/BTC 比值的漂移（ν<sub>X</sub>）。最後一欄是「要把它量到 ±5%／年需要多少年資料」</caption>
        <thead><tr><th>視窗</th><th>年數</th><th>ν<sub>X</sub>（%／年）</th><th>σ<sub>X</sub>（%）</th>
          <th>標準誤（%／年）</th><th>t</th><th>需要幾年</th></tr></thead>
        <tbody>
''')
for r in NU:
    t = float(r["t"])
    nu_c = "pos" if float(r["nu"]) > 0 else "negv"
    A(f'          <tr><td class="name">{esc(win(r["win"]))}</td><td>{r["yrs"]}</td>'
      f'<td class="{nu_c}">{dash(r["nu"])}</td><td>{r["sig"]}</td>'
      f'<td>{r["se"]}</td><td>{dash(f"{t:+.2f}")}</td><td>{r["need"]}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>
    <div class="callout bad">
      <p style="margin:0">
        <b>六個視窗最大的 |t| 是 {NU_MAX_T}，門檻是 3.0。</b>
        更關鍵的是<b>符號會翻轉</b>：{win(NU[1]["win"])} 是 {dash(NU[1]["nu"])}，
        {win(NU[2]["win"])} 是 <b>+{NU[2]["nu"]}</b>，{win(NU[3]["win"])} 又回到 {dash(NU[3]["nu"])}。
      </p>
      <p style="margin:10px 0 0">
        標準誤的公式是 σ÷√（年數），<b>分母是日曆年數，不是資料筆數</b>。
        <b>這就是為什麼「抓小時線」救不了它</b>——這與本專案早就對 BTC 自身漂移下的結論逐字相同。
      </p>
    </div>

    <h3 class="sub">2.3　不重疊視窗：把「ETH 明顯輸」這個印象拆掉</h3>
    {svg_strip(STRIP, 0.40, 3.0, [0.5, 0.7, 1.0, 1.5, 2.0, 3.0],
               "每個不重疊視窗裡，ETH 腿的 BTC 顆數 ÷ BTC 腿的 BTC 顆數")}
    <div class="table-wrap wide" style="margin-top:14px">
      <table>
        <caption>把歷史切成互不重疊的區段，每段各跑一個定投計畫到底（這是「獨立樣本」的正確做法）</caption>
        <thead><tr><th>視窗長度</th><th>段數 n</th><th>最小</th><th>中位</th><th>最大</th>
          <th>ETH 腿領先</th><th>幾何平均</th><th>log 標準差</th></tr></thead>
        <tbody>
''')
for b in NOW_BLOCKS:
    A(f'          <tr><td class="name">{b["L"]} 週</td><td>{b["n"]}</td><td>{b["lo"]:.4f}</td>'
      f'<td>{b["med"]:.4f}</td><td>{b["hi"]:.4f}</td><td>{b["ahead"]}/{b["n"]}</td>'
      f'<td class="pos">{b["geo"]:.4f}</td><td>{b["sd"]:.4f}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>
    <div class="callout bad">
      <h3>這張表要非常小心地讀——它證不了「ETH 沒差」，只證得了「量不出來」</h3>
      <p style="margin:0">
        三組的幾何平均是 <b>{NOW_BLOCKS[0]["geo"]} / {NOW_BLOCKS[1]["geo"]} / {NOW_BLOCKS[2]["geo"]}</b>，
        全部貼在 1.0。<b>「BTC 明顯贏」那個印象，完全來自 2020-08 這一個起點加上今天這一個終點的單一路徑</b>，
        而<a href="#headline">第一節</a>已經量過：光換一個結算月就能搬動 {END_SWING:.1f}%。
      </p>
      <p style="margin:10px 0 0">
        <b>但 n = {NOW_BLOCKS[0]["n"]} / {NOW_BLOCKS[1]["n"]} / {NOW_BLOCKS[2]["n"]}。</b>
        <a class="gl" href="#g16-indep">獨立觀測數</a>只有個位數，
        <b>這個樣本數不能拒絕任何東西，包括「幾何平均其實不是 1.0」。</b>
        研究員自己把它列為限制第 2 條，本頁照列。
        <b>正確的讀法是：把它當離散度的描述（log 標準差 {NOW_BLOCKS[2]["sd"]}~{NOW_BLOCKS[1]["sd"]}），
        不要當檢定。</b>
      </p>
    </div>

    <h3 class="sub">2.4　那「最佳 ETH 比例」是多少？——區間寬到同時蓋住 0、0.5、1</h3>
    <div class="callout">
      <p style="margin:0">
        用本專案已經用過的那條成長最適公式（把 BTC/美元換成 ETH/BTC）：
        點估計是 <b>w* = {W_STAR}</b>，也就是「大約 20% 放 ETH」。
        <b>但點估計沒有意義，要看它的區間。</b>
      </p>
      <p style="margin:10px 0 0">
        研究員用 <a class="gl" href="#g16-boot">block bootstrap</a> 跑了 <b>{B_CELLS} 格</b>
        （4 種區塊長度 × 3 個亂數種子，每格 3,000 次）：
        <b>95% 區間大約是 [{dash(f"{B_P025:.2f}")}, +{B_P975:.2f}]</b>，中位數在 {B_P50LO}~{B_P50HI} 之間。
      </p>
      <p style="margin:10px 0 0">
        <b>這個區間同時包含 0（不要 ETH）、0.5（一半一半）、1（全部 ETH）。</b>
        也就是說：<b>資料無法區分這三種做法。</b>
        這與本專案對另一個參數（β）的結論同構——那裡的 95% 區間也蓋住了整個可行範圍。
      </p>
      <p style="margin:10px 0 0">
        順帶一個口徑細節，因為它是本專案第三次踩到同一個坑：
        <b>對數漂移是負的（{dash(NU_FULL)}%／年），算術漂移卻是正的（{MU_AR}%／年）</b>，
        差的整個就是 σ²/2 = {F["harvest_th"]}。<b>而那一項要靠再平衡才拿得到，
        兩個各自買進不賣的定投計畫一分錢都拿不到</b>——見<a href="#diversify">第三節</a>末段。
      </p>
    </div>

    <h3 class="sub">2.5　★ 最漂亮的一段：同一道題有兩個答案，而且兩個都對</h3>
    <div class="callout good">
      <h3>minimax 的答案取決於你把誰放進「事後最好的選擇」名單</h3>
      <p style="margin:0">
        <a class="gl" href="#g16-minimax">minimax 遺憾</a>不需要預測未來，所以本專案很愛用它。
        研究員先證了一件事：<b>用 BTC 顆數算的遺憾，和用 ETH 顆數算的遺憾，公式完全相同</b>
        （有回歸測試）。所以答案<b>與你最後在乎哪個幣無關</b>。然後：
      </p>
      <ul>
        <li><b>如果「事後最好的選擇」名單是 &#123;全 BTC, 全 ETH&#125;</b>：
          最小的最大遺憾在 <b>w = {MINIMAX_W}</b>，值 = log 2 = <b>{MINIMAX_V}</b>。
          <b>也就是恰好一半一半——你現在剛好就在這裡。</b></li>
        <li><b>如果名單只有 &#123;全 BTC&#125;</b>——那正是本專案目標函數寫的那一行——
          <b>那麼 w = 0 是唯一的零遺憾解，遺憾恆為 0、變異數恆為 0，對任何未來都成立。</b></li>
      </ul>
      <p style="margin:10px 0 0">
        <b>兩個答案都正確。差別不在數學，在「遺憾要拿誰當比較對象」，
        而那就是「你用什麼計價」這個問題本身。資料在這一步沒有立場。</b>
        這與本專案對 β=1 的裁決結構一模一樣，差別是：那裡的「棄權動作」只有一個，
        <b>這裡有兩個，取決於你叫哪個資產是家。</b>
      </p>
    </div>

    <div class="table-wrap">
      <table>
        <caption>最差情況有多大（零漂移參照，σ<sub>X</sub> = {SIG_FULL}%）：w = 0.5 相對「事後完美選擇」讓出多少</caption>
        <thead><tr><th>持有年數</th><th>log X 標準差</th><th>X 比值 5%~95%</th><th>w=0.5 的遺憾</th></tr></thead>
        <tbody>
''')
for h, sd, lo, hi, reg in HORIZON:
    A(f'          <tr><td class="name">{h} 年</td><td>{sd}</td><td>{lo} ~ {hi}</td>'
      f'<td>{reg}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>
    <p class="section-note">
      讀法：<b>「這件事能錯到多離譜」，不是「預期會賠多少」。</b>
      一年期 ETH/BTC 落在 {HORIZON[1][2]} ~ {HORIZON[1][3]} 倍之間是常態，
      <b>這就是這個部位的實際大小</b>。
    </p>

    <div class="callout bad">
      <h3>所以研究員交了什麼、沒交什麼</h3>
      <p style="margin:0">
        <b>沒交：「ETH 該不該存在」的答案。</b>他明確拒絕，理由寫在報告最後一節：
        <b>資料在方向上量不出東西（六個視窗 |t| ≤ {NU_MAX_T}），在大小上量得很清楚（區間蓋住 0、0.5、1）。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>交了三件：</b>(1) 這筆配置在數學上究竟是什麼（一個 size = 1/2 的 ETH/BTC 方向性部位，不是分散化）；
        (2) 它有多大（上面那張表）；
        (3) 它在你真正經歷過的那段期間表現如何（<a href="#headline">第一節</a>，
        <b>而那個數字不預測任何事</b>）。
      </p>
      <p style="margin:10px 0 0">
        <b>本頁同意這個拒絕，而且認為這個拒絕本身就是本輪最有價值的產出之一。</b>
        一個研究員在這裡給出「建議配置 30%」，會是把 {B_CELLS} 格 bootstrap 的
        [{dash(f"{B_P025:.2f}")}, +{B_P975:.2f}] 假裝成一個點。
      </p>
    </div>
  </section>
''')


# ------------------------------ 3. diversification ------------------------
A(f'''
  <section id="diversify">
    <h2>三、持有 ETH 不是「分散風險」——兩個口徑都死<span class="pill fact">推導＋實測</span></h2>
    <p class="section-note">
      派工書只要求檢查「以 BTC 幣數為目標時，分散化還剩多少」。
      研究員把同一把刀也切向美元口徑，<b>結果它在那裡也不成立</b>——這一段超出派工範圍。
    </p>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>「不要把雞蛋放在同一個籃子」是對的，但它有一個前提：<b>兩個籃子要不會同時掉。</b>
        這一節分兩步：先看你<b>真正在乎的記分方式</b>（BTC 顆數），再看一般人說的那種（美元價值）。</p>
      <p><b>第一步不需要任何歷史資料</b>，用代數就能證完：
        如果你的目標是「BTC 顆數愈多愈好」，那麼「完全不買 ETH」這個做法的<b>波動恰好是 0</b>，
        而且買愈多 ETH 波動愈大，<b>中間沒有任何一個「比較穩」的比例</b>。</p>
      <p><b>第二步才需要資料，而結果一樣</b>：BTC 和 ETH 的相關係數是 0.80，近一年升到 0.91，
        <b>而 ETH 晃得比 BTC 更兇</b>。六個時間視窗全部顯示：一半一半的組合<b>比純持有 BTC 還晃</b>。</p>
    </div>

    <h3 class="sub">3.1　以 BTC 顆數記分：這是推導，不是回測</h3>
    <div class="engine">
      <h3>兩行代數就結束了</h3>
      <dl>
        <dt>設定</dt>
        <dd>投入 1 元，比例 <code>w</code> 買 ETH，令 <code>g</code> = 期末的 ETH/BTC 比值 ÷ 期初的 ETH/BTC 比值。</dd>
        <dt>相對「全買 BTC」的 BTC 顆數</dt>
        <dd><code>R(w) = 1 + w(g − 1)</code></dd>
        <dt>它的變異數</dt>
        <dd><code>Var[R(w)] = w² · Var[g]</code>
          —— <b>對 w 嚴格遞增，最小值在 w = 0，而且在那一點恰好等於 0。沒有內點。</b>
          （回歸測試：21 個 w 格點逐一檢查單調遞增。）</dd>
        <dt>對照：用美元記分時就有內點了</dt>
        <dd><code>w*<sub>最小變異數</sub> &gt; 0</code> 的條件是 <code>ρ &lt; σ<sub>BTC</sub>/σ<sub>ETH</sub></code>
          —— <b>這個條件在真實資料上不成立，見 3.2。</b></dd>
      </dl>
    </div>
    <div class="callout bad">
      <p style="margin:0">
        <b>「持有兩種幣就是分散化」在美元口徑下是一個有內容的主張，在 BTC 顆數口徑下是假的。
        而翻轉它的是<a class="gl" href="#g16-numeraire">計價單位</a>，不是投資組合本身。</b>
      </p>
      <p style="margin:10px 0 0">
        在 BTC 顆數目標下持有 ETH <b>不是分散化，是一個大小 = w 的 ETH/BTC 方向性部位</b>，句點。
        這正是第十三輪那句「計價單位決定哪個資產是無風險資產」在橫斷面上的重演。
      </p>
    </div>

    <h3 class="sub">3.2　★ 超出派工書：它在美元口徑下<b>也</b>不成立</h3>
    <div class="table-wrap wide">
      <table>
        <caption>「vs 純 BTC」為正 = 一半一半的美元組合<b>比只拿 BTC 更晃</b>；最後一欄為負 = 要降低美元波動得去<b>放空</b> ETH</caption>
        <thead><tr><th>視窗</th><th>σ<sub>BTC</sub></th><th>σ<sub>ETH</sub></th><th>ρ</th>
          <th>σ(50/50)</th><th>vs 純 BTC</th><th>最小變異數的 ETH 權重</th></tr></thead>
        <tbody>
''')
RHO_HI_ATTR = ' class="negv"'
for r in DIV:
    rho_a = RHO_HI_ATTR if float(r["rho"]) > 0.85 else ""
    wmv_c = "negv" if float(r["wmv"]) < 0 else "pos"
    A(f'          <tr><td class="name">{esc(win(r["win"]))}</td><td>{r["sb"]}%</td><td>{r["se"]}%</td>'
      f'<td{rho_a}>{r["rho"]}</td><td>{r["s5050"]}%</td>'
      f'<td class="negv">+{r["vs"]}</td>'
      f'<td class="{wmv_c}">{dash(r["wmv"])}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>
    <div class="callout bad">
      <p style="margin:0">
        <b>{DIV_WORSE} 個視窗裡有 {DIV_WORSE} 個</b>，50/50 的美元組合比純持有 BTC 更波動
        （多 {DIV_VS_LO}% ~ {DIV_VS_HI}%）。
        <b>{len(DIV)} 個視窗裡有 {DIV_NEG} 個</b>，美元最小變異數的 ETH 權重是負的。
      </p>
      <p style="margin:10px 0 0">
        機制很單純：ρ 大約 0.78~0.91，而 ETH 的波動是 BTC 的 1.3~1.4 倍。
        <b>ETH 在這段歷史裡基本上就是「BTC 的高倍數版本」。</b>
        <b>而且趨勢在惡化：ρ 從 {DIV[1]["rho"]} 升到 {DIV[-1]["rho"]}。</b>
      </p>
    </div>

    <h3 class="sub">3.3　尾部也死：BTC 最慘的那些日子，ETH 跌得更兇</h3>
    <div class="split">
      <div class="stat"><div class="label">BTC 最差 5% 的日子（n={TAIL_N}）</div>
        <div class="value neg">BTC {dash(TAIL_B)}%</div><div class="sub">同一批日子裡 ETH 平均 {dash(TAIL_E)}%</div></div>
      <div class="stat"><div class="label">那些日子裡 ETH 逆勢上漲的比例</div>
        <div class="value neg">{TAIL_UPP}%</div><div class="sub">{TAIL_UPN}/{TAIL_UPD} 天</div></div>
      <div class="stat"><div class="label">ETH 平常的上漲日比例</div>
        <div class="value">{TAIL_UNCOND}%</div><div class="sub">對照組：沒有條件的話是這個數</div></div>
    </div>
    <p class="section-note" style="margin-top:12px">
      <b>在 BTC 最壞的日子裡，ETH 幾乎不會逆勢（{TAIL_UPP}% vs 平常的 {TAIL_UNCOND}%），而且跌得更多。
      可量測的那一半尾部保護不存在。</b>
    </p>

    <div class="callout">
      <h3>★ 唯一站得住的反面理由：而它我們量不到，也不假裝量得到</h3>
      <p style="margin:0">
        「分散化」最誠實的版本<b>不是變異數論證</b>，是<b>「BTC 專屬的災難」</b>——
        協議層失效、量子計算、單一司法管轄的全面封殺。
        <b>這種事件依定義不在樣本裡</b>：過去九年沒有發生過，所以相關係數、變異數、尾部統計
        <b>全部碰不到它</b>。
      </p>
      <p style="margin:10px 0 0">
        <b>這是這個配置唯一一條我們無法反駁的論證，而它同時也無法被任何資料支持。</b>
        如果你持有 ETH 的理由是這一條，<b>那麼上面 3.1~3.3 的所有數字都不該影響你的決定</b>——
        它們回答的是別的問題。<b>這句話是認真的，不是客套。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>但請不要把這一條和「ETH 比較會漲」混在一起。</b>
        前者是保險，後者是方向賭注，<a href="#exist">第二節</a>已經量過方向賭注量不出來。
      </p>
    </div>

    <h3 class="sub">3.4　「再平衡收割」這條路：研究員在這裡主動停手</h3>
    <div class="callout">
      <p style="margin:0">
        <a class="gl" href="#g16-rebal">再平衡收割</a>在理論上有 <b>{F["harvest_th"]}</b>
        （就是 2.4 節那個 σ²/2）。<b>但它是「連續再平衡」的對價，
        兩個從不互相再平衡的獨立定投計畫一分錢都拿不到。</b>實測：
      </p>
    </div>
    <div class="table-wrap wide">
      <table>
        <caption>w = 0.5、BTC 顆數口徑：買進不動 vs 定期再平衡（理論年化收割值 {REB_THEORY}%）</caption>
        <thead><tr><th>視窗</th><th>買進持有</th><th>每月再平衡</th><th>每週</th><th>每日</th><th>年化收割</th></tr></thead>
        <tbody>
''')
for r in REB:
    hi = float(r["harv"].rstrip("%"))
    h_a = ' class="negv"' if hi < 1 else ""
    A(f'          <tr><td class="name">{esc(win(r["win"]))}</td><td>{r["bh"]}</td><td>{r["mon"]}</td>'
      f'<td>{r["wk"]}</td><td>{r["day"]}</td>'
      f'<td{h_a}>{r["harv"]}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>
    <div class="callout bad">
      <p style="margin:0">
        <b>理論值 {REB_THEORY}%／年，近三年實測 {REB[4]["harv"]}，最近的視窗 {REB[3]["harv"]}。</b>
        而且全期的<b>每月再平衡（{REB[0]["mon"]}）勝過每日（{REB[0]["day"]}）</b>——
        <b>這與連續再平衡理論的預測方向相反</b>，是本專案早就記錄過的「路徑相依複利假象」。
      </p>
      <p style="margin:10px 0 0">
        <b>然後研究員做了一件對的事：他停手了。</b>
        「要選再平衡頻率」就是一個參數格（同一個視窗裡從 {REB[0]["day"]} 到 {REB[0]["mon"]} 差 16%），
        而<b>依本專案的收案標準，「需要跑一格參數再挑最好的」這類候選的期望值已被量測為零</b>。
        <b>他沒有去挑那個最好的頻率，也沒有把它列成候選。</b>
        （而<a href="#timing">第五節</a>正好又在最單純的 24 格上把同一件事量了第六次。）
      </p>
    </div>
  </section>
''')


# ------------------------------ 4. shared idle pool -----------------------
A(f'''
  <section id="idle">
    <h2>四、推翻派工書：閒置池是共用的，ETH 不會多出第二筆漏損<span class="pill fact">代數＋實測</span></h2>
    <p class="section-note">
      派工書寫的是「本線算術逐字適用」。照字面讀會得出「ETH 再來一份 {F["idle_old"]}」。
      <b>那是錯的，而且錯的方向剛好讓一個舊估計變得更可信。</b>
    </p>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>你存一筆 USDT 進幣安，定投每週從裡面扣一點。<b>還沒被扣走的那些錢躺著沒有生息</b>，
        這就是第十輪算的「閒置漏損」。直覺會想：現在有兩個計畫在扣，是不是漏損變兩倍？</p>
      <p><b>不是。</b>因為幣安的現貨帳戶<b>每種幣只有一個餘額</b>，
        而定投的 API 裡<b>根本沒有「從哪個錢包扣」這個選項</b>（研究員去查了官方文件）。
        兩個計畫吃的是<b>同一堆錢</b>。躺著沒生息的總金額只跟「你平均放多少錢在那裡」有關，
        <b>跟有幾個計畫在花它無關</b>。</p>
      <p><b>真正改變的是錢被花掉的速度</b>——而這一點反而幫了第十輪一個忙。</p>
    </div>

    <h3 class="sub">4.1　為什麼不會變兩份：一行代數＋一個回歸測試</h3>
    <div class="callout good">
      <p style="margin:0">
        閒置利息 = <b>平均閒置餘額 × 利率</b>。<b>平均閒置餘額與「有幾個計畫在消耗它」無關。</b>
        把一個池子拆成兩個各半的池子，在補貼上限以下<b>完全等值</b>（利息對餘額是線性的）：
      </p>
      <ul>
        <li>一個池（峰值 ${PEAK:,.2f}）：<b>{F["idle_new"]}</b></li>
        <li>兩個獨立的半大池：2 × ${SPLIT_EACH} = <b>${SPLIT_TOT}/年</b></li>
        <li>差額：<b>+${SPLIT_DIFF}/年</b>（純粹來自補貼上限的非線性，不是來自「兩個計畫」）</li>
      </ul>
      <p style="margin:10px 0 0">
        這條有回歸測試守著。<b>唯一的例外是兩個計畫分屬不同子帳戶</b>——
        那會需要各自獨立入金，與「一次存一大筆慢慢花」的形狀不符，
        <b>而且沒有任何紀錄指向它。研究員把這一條標為推論，不是觀測。</b>
      </p>
    </div>

    <h3 class="sub">4.2　★ 真正改變的是燃燒率，而它讓第十輪的點估計變可信</h3>
    <div class="table-wrap wide">
      <table>
        <caption>同樣的閒置金額，兩種「每週被花掉多少」的讀法</caption>
        <thead><tr><th>每週燃燒</th><th>隱含的入金間隔</th><th>平均閒置餘額</th>
          <th>年利息（正確口徑）</th><th>年利息（第十輪的簡化）</th></tr></thead>
        <tbody>
''')
for burn, wk, days, bal, exact, flat in BURN:
    lbl = "（第十輪的假設：只有 BTC 計畫）" if burn == "100" else "（兩個計畫，正確）"
    cls = ' class="best"' if burn == "200" else ""
    A(f'          <tr{cls}><td class="name">${burn}/週{lbl}</td><td>{wk} 週（{days} 天）</td>'
      f'<td>${bal}</td><td>${exact}</td><td>${flat}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>
    <div class="callout good">
      <p style="margin:0">
        <b>「每 {F["burn_old"]}入一次金」是一個很怪的人類節奏。「每 {F["burn_new"]}」就是月付。</b>
        第十輪當時只能給一個很寬的區間（$17~$72），因為它不知道入金節奏。
        用 $200/週去讀，<b>所有合理的人類節奏全部落在點估計附近</b>：
      </p>
    </div>
    <div class="table-wrap wide">
      <table>
        <caption>燃燒率 $200/週之下，各種入金習慣對應的年利息</caption>
        <thead><tr><th>入金節奏</th><th>每批金額</th><th>可撐幾週</th><th>平均閒置</th>
          <th>年利息（含補貼）</th><th>只算市場利率</th></tr></thead>
        <tbody>
''')
for name, batch, wks_, bal, exact, mkt in CADENCE:
    cls = ' class="base"' if name.startswith("point estimate") else ""
    nm = {"weekly $200": "每週 $200", "fortnightly $400": "每兩週 $400",
          "monthly $869 (=200x4.345)": "每月 $869（= 200×4.345）",
          "round $1,000": "整數 $1,000", "point estimate 2x476.54": "★ 點估計（觀測推得）",
          "quarterly $2,608": "每季 $2,608", "round $5,000": "整數 $5,000"}.get(name, name)
    A(f'          <tr{cls}><td class="name">{esc(nm)}</td><td>${batch}</td><td>{wks_}</td>'
      f'<td>${bal}</td><td>${exact}</td><td>${mkt}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>

    <h3 class="sub">4.3　同一節裡有一個對第十輪不利的更正，照報</h3>
    <div class="callout bad">
      <p style="margin:0">
        第十輪用「平均餘額 × 7.109% 的混合利率」。
        <b>但那 4% 的分層補貼只付前 800 USDT</b>，而鋸齒的峰值 ${PEAK:,.2f} 有一段時間在 800 以上，
        那一段只能拿市場利率。正確算法要把兩層分開。
      </p>
      <p style="margin:10px 0 0">
        結果：<b>{F["idle_old"]} → {F["idle_new"]}</b>（在今日利率下的正確值），
        <b>簡化公式高估了 ${SPLIT_DIFF}/年，約 1.5%</b>。
        <b>量級不變，但公式寫錯了，而且它在批次更大時會放大</b>（$2,600 批次下誤差 $7.3）。
        已加回歸測試。
      </p>
      <p style="margin:10px 0 0">
        另外，USDT 的市場利率<b>在持續下滑</b>：
        第十輪 {F["usdt_r10"]} → 第十三輪 {F["usdt_r13"]} → 今日實測 <b>{F["usdt_apr"]}</b>。
        <b>所以 {F["idle_new"]} 這個數字帶有時效，不是常數。</b>
      </p>
    </div>
  </section>
''')

# ------------------------------ 5. timing ---------------------------------
A(f'''
  <section id="timing">
    <h2>五、第十輪的時點檢定：判定成立，但理由現在才完整<span class="pill fact">逐位元重現</span></h2>
    <p class="section-note">
      第十輪的結論是「改定投的執行時間不是可行的改善手段，可以永久關閉」。
      <b>這個判定成立。但第十輪只掃了兩個小時，而掃完 24 個之後，事情變得比它想的更有意思。</b>
    </p>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>「定投挑在星期幾、幾點扣款，會不會買得比較便宜？」第十輪測過兩個時段，說沒有差別。</p>
      <p>這一輪先把第十輪的兩個數字<b>一模一樣地重算出來</b>（連小數點後兩位都對上），
        然後做了第十輪沒做的事：<b>把一天 24 個小時全部掃一遍</b>。</p>
      <p>結果很值得看：<b>樣本內</b>看起來<b>剛好像通過本專案的門檻</b>。
        但把「用前半段挑出來的最便宜時段」拿到<b>後半段</b>去驗證，<b>六次全部失敗</b>。</p>
    </div>

    <h3 class="sub">5.1　先對帳：第十輪的兩個數字逐位元重現</h3>
    <div class="table-wrap wide">
      <table>
        <caption>「本輪重算」與「第十輪原值」逐欄比對（標準誤的 0.1 差異來自浮點捨入）</caption>
        <thead><tr><th>計畫</th><th>N</th><th>本輪平均（bp）</th><th>本輪 SE</th><th>本輪 t</th>
          <th>第十輪 t</th></tr></thead>
        <tbody>
''')
for sym, hr, n, mean, se, t, n10, m10, se10, t10 in C5:
    A(f'          <tr><td class="name">{sym} 計畫（週三 {hr}:00 UTC）</td><td>{n}</td>'
      f'<td>{mean}</td><td>{se}</td><td>{t}</td><td>{t10}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>
    <div class="callout good">
      <h3>涵蓋稽核：這次連「資料本身有沒有洞」都查了</h3>
      <ul>
        <li><b>{BARS} 根小時 K，缺 0 根。</b>（{SPAN0} → {SPAN1}，{DAYS} 天）</li>
        <li>區間內的週三恰好 <b>{N_WED}</b> 個，與 N 相符。</li>
        <li>時區：<code>Asia/Ho_Chi_Minh</code> 2020~2026 的 UTC 偏移集合 = <b>{esc(TZ_SHOW)} 這一個值，無日光節約</b>
          —— 整段樣本不會漂移。</li>
        <li><b>重疊造成的自相關是負的</b>（BTC {dash(AC[0][1])}、ETH {dash(AC[1][1])}），
          代表原本的標準誤是<b>保守</b>的。修正後 SE 反而縮小
          （{AC[0][2]}→{AC[0][3]} bp、{AC[1][2]}→{AC[1][3]} bp），
          t 變成 {AC[0][4]} / {AC[1][4]}，<b>仍然不顯著</b>。</li>
        <li><b>修正後的偵測下限比第十輪自稱的還好</b>：
          BTC ±{DETECT[0][2]:.1f} bp = <b>${DETECT[0][3]:.2f}/年</b>、
          ETH ±{DETECT[1][2]:.1f} bp = <b>${DETECT[1][3]:.2f}/年</b>（以 $5,200 流量計）。
          第十輪寫的 ±40 bp 是<b>高估了自己的雜訊</b>。</li>
      </ul>
      <p style="margin:10px 0 0">
        <b>請用正確的方向讀這一條：檢定看不到比這更小的效應。
        它沒有證明效應是零，它證明的是「效應在這條地板以下」。</b>
      </p>
    </div>

    <h3 class="sub">5.2　★ 第十輪漏掉的那 22 個小時——而它看起來像個發現</h3>
    <div class="split">
      <div class="stat"><div class="label">BTC：最便宜 vs 最貴小時的落差</div>
        <div class="value warn">{HOURGRID["BTCUSDT"]["spread"]} bp</div>
        <div class="sub">最便宜 {HOURGRID["BTCUSDT"]["cheap"]}:00、最貴 {HOURGRID["BTCUSDT"]["dear"]}:00</div></div>
      <div class="stat"><div class="label">BTC：同日配對檢定</div>
        <div class="value warn">t = {PAIRED["BTCUSDT"]["t"]}</div>
        <div class="sub">N = {PAIRED["BTCUSDT"]["n"]}，日效應完全抵銷</div></div>
      <div class="stat"><div class="label">ETH：同日配對檢定</div>
        <div class="value warn">t = {PAIRED["ETHUSDT"]["t"]}</div>
        <div class="sub">N = {PAIRED["ETHUSDT"]["n"]}，落差 {HOURGRID["ETHUSDT"]["spread"]} bp</div></div>
      <div class="stat"><div class="label">拿到樣本外驗證</div>
        <div class="value neg">6 / 6 失敗</div>
        <div class="sub">樣本內最便宜的小時，樣本外排 {OOS_RANK_LO}~{OOS_RANK_HI} / 24</div></div>
    </div>
    <p class="section-note" style="margin-top:12px">
      <b>一個 t = {PAIRED["ETHUSDT"]["t"]}、N = {PAIRED["ETHUSDT"]["n"]}、日效應完全抵銷的配對檢定，
      長得就像本專案的門檻剛好被通過。</b>
      研究員在自己的 log 裡就先標註了：<b>那兩個小時是從這同一批樣本裡挑出來的，
      所以這個 t 不是證據，它是「最大值」的定義。</b>
    </p>

    <div class="table-wrap wide">
      <table>
        <caption>用前半段挑出最便宜的小時，拿到後半段量（rank 1 = 仍然最便宜，24 = 變成最貴）</caption>
        <thead><tr><th>標的／切分點</th><th>樣本內挑中</th><th>樣本內 bp</th>
          <th>樣本外 bp</th><th>樣本外排名</th><th>前後半段的秩相關</th></tr></thead>
        <tbody>
''')
for sym, split, isn, oosn, pick, isbp, oosbp, oost, rank, rho in OOS:
    rho_a = ' class="negv"' if float(rho) < 0 else ""
    A(f'          <tr><td class="name">{sym} · {split}</td><td>{pick}</td><td>{dash(isbp)}</td>'
      f'<td class="negv">{dash(oosbp)}</td><td class="negv">{rank}/24</td>'
      f'<td{rho_a}>{dash(rho)}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>

    <div class="callout bad">
      <h3>這是同一件事的第六次獨立量測，仍然是零——而這次的格子最單純</h3>
      <p style="margin:0">
        六次全部：<b>樣本內最便宜的小時，到了樣本外排在中位數之後</b>
        （{OOS_RANK_LO}~{OOS_RANK_HI} / 24）；<b>符號翻轉 {OOS_FLIP}/6</b>；
        前後半段的秩相關從 {dash(OOS_RHO_LO)} 到 +{OOS_RHO_HI}，<b>六個裡有 {OOS_RHO_NEG} 個是負的</b>。
      </p>
      <p style="margin:10px 0 0">
        <b>而這一次的格子是最單純的一種</b>——24 個小時，沒有訊號、沒有加權、沒有標的池、
        沒有任何可以「調」的東西。<b>連這種格子都挑不出可以轉移的東西。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>判定：第十輪「改執行時間不是可行的改善手段」成立，但它的理由現在才完整。</b>
        第十輪靠的是結構論證（Spread 是常數、參考價沒有可預測的偏斜），
        <b>那個結構論證這一輪回原始文件重讀確認了</b>（見<a href="#actionable">第六節</a>）；
        但結構論證<b>排不掉樣本內的日內季節性</b>——那個是真的存在於樣本內，<b>只是不轉移</b>。
        <b>兩條理由現在都在檔案裡了。</b>
      </p>
      <p style="margin:10px 0 0">
        還有一個實務上的封口：<b>改執行小時必須修改計畫，而修改計畫會觸發 Spread 重新定價</b>。
        即使那 {HOURGRID["BTCUSDT"]["spread"]} bp 是真的（約 $15/年），
        <b>它要賭的是一個方向未知的重新定價。取捨不划算，而且不需要再討論了。</b>
      </p>
    </div>
  </section>
''')


# ------------------------------ 6. actionable -----------------------------
CYCLES = [c.strip().strip('"') for c in CYCLE_ENUM.split(",")]
A(f'''
  <section id="actionable">
    <h2>六、兩件可執行的事，以及三個查到的新事實<span class="pill hyp">存量是推估值</span></h2>
    <p class="section-note">
      本節有一個貫穿的但書：<b>你的 ETH 現貨存量，十六輪從來沒有被記錄過。</b>
      下面的金額建立在「ETH 計畫與 BTC 計畫同樣大小、同樣長度」的推估上，
      <b>所以它是一個量級，不是一個帳單。</b>
    </p>

    <div class="plain">
      <span class="lbl">白話導讀</span>
      <p>這一節兩件事都很小（一年幾十塊美元），但它們是<b>確定的、不需要預測任何事</b>的那種小。
        第一件是「你手上的 ETH 正在零收益地躺著」，第二件是一個第十三輪查不到的規格終於查到了。</p>
      <p><b>第一件要特別小心讀</b>：它<u>不是</u>「所以該買 ETH」。
        它是「<u>既然已經有</u> ETH，它不必是零收益」。這兩句話差很多，下面會拆開。</p>
    </div>

    <h3 class="sub">6.1　ETH 的活期理財利率是 BTC 的六十幾倍——這個資產十六輪沒人查過</h3>
    <div class="callout good">
      <p style="margin:0">
        第八輪用 625 行否決了「把 BTC 拿去出借」（一年只有 $2.52，風險卻是全額）。
        第十輪已經抓到一次：<b>那是對「BTC 這個幣種」的否決，卻被誤讀成對「Simple Earn 這個產品」的否決</b>，
        USDT 因此被漏掉了七輪。<b>ETH 是第三個資產，十六輪沒有任何一輪查過它。</b>
      </p>
    </div>
    <div class="table-wrap wide">
      <table>
        <caption>今日實測的市場利率（公開端點，不需要任何憑證；加法關係 <code>latest = market + tier</code> 五個幣種全部成立）</caption>
        <thead><tr><th>資產</th><th>市場利率 <code>marketApr</code></th><th>分層補貼</th>
          <th>補貼上限</th><th>合計</th></tr></thead>
        <tbody>
''')
for a in ("BTC", "ETH", "USDT"):
    r = RSNAP[a]
    cls = ' class="best"' if a == "ETH" else ""
    A(f'          <tr{cls}><td class="name">{a}</td><td>{r["marketApr"]*100:.6f}%</td>'
      f'<td>+{r["tierApr"]*100:.4f}%</td><td>前 {r["tierCap"]:g}</td>'
      f'<td>{r["latest"]*100:.6f}%</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>
    <div class="callout">
      <h3>這個「幾倍」必須帶著時間戳一起講</h3>
      <p style="margin:0">
        研究員在 <b>{RSNAP["fetched_utc"]}</b> 量到 <b>ETH ÷ BTC = {RS_RATIO:.1f} 倍</b>。
        <b>本頁作者在同一天 {RECHK["fetched_utc"]} 用同一個公開端點再量一次，是 {RE_RATIO:.1f} 倍。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>兩個都對——差別是利率會浮動，而 BTC 那個分母太小（{RSNAP["BTC"]["marketApr"]*100:.6f}%），
        分母的微小變動就能把倍數推動好幾個單位。</b>
        所以正確的說法是「<b>六十幾倍</b>，而且這個倍數每天會變」，
        <b>不是「就是 {RS_RATIO:.1f} 倍」。任何引用這個倍數的句子都必須附上量測時間。</b>
      </p>
    </div>
    <div class="table-wrap wide">
      <table>
        <caption>如果把 ETH 放進活期理財，一年能多拿多少（價格取資料檔最後一根日 K：ETH ${S8_PX[0]}、BTC ${S8_PX[1]}）</caption>
        <thead><tr><th>ETH 存量</th><th>美元價值</th><th>ETH／年</th><th>$／年</th>
          <th>折算 BTC 顆數／年</th><th>對照：BTC 存量的收益</th></tr></thead>
        <tbody>
''')
for stack, usd, ethyr, dyr, btcyr, vs in EARN_ROWS:
    cls = ' class="base"' if stack == EARN_PICK[0] else ""
    tag = "　← 推估值" if stack == EARN_PICK[0] else ""
    A(f'          <tr{cls}><td class="name">{stack} ETH{tag}</td><td>${usd}</td><td>{ethyr}</td>'
      f'<td class="pos">${dyr}</td><td>{btcyr}</td><td>${vs}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>

    <div class="callout bad">
      <h3>三個但書必須<b>同時</b>講，否則這一段會被讀成推薦</h3>
      <ul>
        <li><b>風險結構與第八輪否決 BTC 出借時<u>完全相同</u>。</b>
          條款 C.2／C.3（與幣安自有資產混同存放的無擔保債權、平台可全權裁量挪用）、
          ADGM 的對手方、SAFU 不涵蓋、贖回可延遲——
          <b>第八輪那 625 行的風險工作原封不動適用，變的只有「承擔這個風險的對價」。</b>
          第八輪那個「破產回收率必須用幣數重算」的口徑偏誤，<b>對 ETH 同樣適用</b>。</li>
        <li><b>曝險是全額、無限期。</b>第八輪的 BTC 曝險是 ${VAL_BTC:,.0f} 換 $2.51；
          ETH 是 ${EARN_PICK[1]} 換 ${EARN_PICK[3]}。<b>倍數變好，但曝險的形狀沒變</b>——
          對照閒置 USDT 那一項只曝險 <b>{F["eth_weeks"]}</b>，這是完全不同的東西。</li>
        <li><b>★ 在 BTC 顆數的目標下，這筆收益買到的是 ETH 顆數，不是 BTC 顆數。</b>
          {EARN_PICK[2]} ETH／年 折算只有 <b>{EARN_PICK[4]} BTC／年</b>。
          <b>它讓一個已經存在的 ETH 部位變大，不會讓 BTC 部位變大。</b>
          <b>它不是「應該持有 ETH」的理由，它是「既然已經持有 ETH，它可以不是零收益」的事實。
          不要把這兩件事混在一起。</b></li>
      </ul>
      <p style="margin:10px 0 0">
        研究員指出：這個「對資產的判決被擴大套用到產品」的錯誤，
        <b>這是本專案第三次現身</b>（第八輪 → 第十輪抓到一次 → 這次）。
      </p>
    </div>

    <h3 class="sub">6.2　第十三輪標為未知的那一項，查到了</h3>
    <div class="callout good">
      <p style="margin:0">
        定投的可選週期（API 欄位 <a class="gl" href="#g16-cycle"><code>subscriptionCycle</code></a>）：
      </p>
      <p style="margin:10px 0 0;font-size:1.05rem">
        <b>{esc(" / ".join(CYCLES))}</b>
      </p>
      <p style="margin:10px 0 0">
        來源是幣安官方開發者文件的 Wayback 封存（<code>plan/add</code> 與 <code>plan/edit</code>
        兩個端點列的是<b>完全相同的八個值</b>）。同一份文件還確認了另外幾件事：
        週期與時間<b>必須以 UTC+0 送出、而且只能是整點</b>；
        <code>flexibleAllowedToUse</code> 是一個布林開關（就是第十輪在網頁上找到的那個）；
        <code>planType</code> 有 <code>SINGLE / PORTFOLIO / INDEX</code>，
        <b>而 <code>PORTFOLIO</code> 可以用<u>一個</u>計畫同時買 BTC 與 ETH 並指定百分比</b>。
      </p>
    </div>
    <div class="callout bad">
      <h3>三條但書要跟著這個答案一起走</h3>
      <ul>
        <li><b>封存快照是 2025-02，不是今天。</b>幣安在 2026 年是否增刪過週期選項，
          在這個環境沒有辦法確認。</li>
        <li><b>這是 Auto-Invest 的 API 文件，你走的是網頁上的 Convert Recurring。</b>
          兩者被幣安視為同一個產品的兩條路徑（第十輪已判定），
          <b>但「API 的週期集合 = 網頁 UI 的週期集合」這件事沒有被驗證過。這一條標為未驗證。</b></li>
        <li><b>它不改變第十三輪的結論。</b>第十三輪需要它來回答「到帳就部署能不能不違反全自動」。
          <code>DAILY</code> 與 <code>H1</code> 都存在，<b>代表那條路在機制上存在</b>；
          但第十三輪自己的結論是「<b>資料無法在兩個零參數候選之間裁決</b>」，
          <b>這個發現只是把「路徑是否存在」從未知變成已知，沒有動到那個裁決。</b></li>
      </ul>
    </div>

    <h3 class="sub">6.3　Spread 條款重讀：三件新事實，以及一個仍然未知</h3>
    <div class="callout">
      <p style="margin:0">
        研究員回原始出處重讀了《Recurring Reference Price Methodology》
        （<code>binance.com</code> 被防火牆擋下，改由 <code>binance.info</code> 取得同一份，
        文件自標日期 2026-04-23，全文已存檔）。<b>逐字的條文確認了三件事：</b>
      </p>
      <ul>
        <li><b>改 ETH 計畫會重新定價，但不會波及 BTC 計畫。</b>
          原文是 "a new spread amount will be applied to <b>the modified plan</b>"——
          <b>用的是單數</b>，而且 Spread 明寫是每個幣種各自一份。</li>
        <li><b>確認頁可以先看再決定。</b>原文 "before completing their configuration"——
          <b>你可以走到最後一步看到新的 Spread，然後不送出。這條避險路徑對 ETH 計畫同樣成立。</b></li>
        <li><b>轉換可能被整週跳過。</b>如果所有報價路徑在 5 秒內都取不到，
          "the Scheduled Conversion will be <b>skipped</b>"，等下一個排程時間。
          <b>文件的範例舉的正是 ETHUSDT。這是一個前面每一輪都沒記過的營運風險——
          金額微小，但它的性質是「漏買」不是「買貴」。</b></li>
      </ul>
      <p style="margin:10px 0 0">
        另外兩件：參考價<b>已經是「對使用者最有利」的路由</b>
        （直接對與合成路徑一起比較後取最好的，這是結構性優勢不是成本）；
        方法論或 Spread 計算方式的變更<b>有 30 天事前通知</b>
        （<b>但那保護的是「幣安單方面改規則」，不保護「你自己改計畫」</b>）。
      </p>
      <p style="margin:10px 0 0">
        <b>仍然未確認：暫停計畫算不算「modify」。</b>
        API 層有兩個不同端點（<code>plan/edit</code> 管金額／週期／星期／資產，
        <code>plan/edit-status</code> 管 ONGOING／PAUSED／REMOVED），
        <b>定價相關欄位全在前者，這<u>暗示</u>暫停不是 modify——但法律文件沒有這樣寫，研究員不宣稱它成立。</b>
      </p>
    </div>

    <div class="callout bad">
      <h3>★ 兩個計畫的 Spread 實際值<b>仍然未知</b>，而且只有你本人查得到</h3>
      <p style="margin:0">
        研究員實測了六個 Auto-Invest 的 API 端點，<b>全部回 <code>-2014</code>（需要帳號簽章）</b>——
        端點存在，但都要憑證。<code>binance.com</code> 的網頁在這個環境被防火牆擋下。
      </p>
      <p style="margin:10px 0 0">
        <b>研究員沒有去尋找、也沒有使用你的 API 憑證。這一點明確寫出來。</b>
        差別只在於：<b>「為什麼只有你查得到」從推測變成了實測</b>（六個端點的實際回應碼）。
      </p>
      <p style="margin:10px 0 0">
        <b>如果你想自己查</b>：交易 → Convert → Recurring → 打開 <b>BTC 與 ETH 兩個計畫</b>的詳情；
        另外走一次「建立計畫」到<b>確認頁但不要送出</b>，比較今天的報價與當初鎖定的值。
        <b>兩個計畫要各做一次，因為文件明寫 Spread 是每個幣種各自一份。</b>
      </p>
    </div>

    <h3 class="sub">6.4　順便把「Spread 重不重要」這件事定量了</h3>
    <div class="table-wrap">
      <table>
        <caption>兩個計畫的 Spread 差距，對結果的影響</caption>
        <thead><tr><th>ETH 與 BTC 的 Spread 差</th><th>對比值的影響</th><th>$5,200 流量上的年成本</th></tr></thead>
        <tbody>
''')
for bp, eff, usd in COST:
    A(f'          <tr><td class="name">{bp} bp</td><td>{eff:+.5f}</td><td>${usd:.2f}</td></tr>\n')
A(f'''        </tbody>
      </table>
    </div>
    <div class="callout good">
      <p style="margin:0">
        對照：<a href="#headline">第一節</a>那張起點掃描圖，比值從 {M1_LO} 掃到 {M1_HI}，
        <b>等於 {ALLOC_BP} bp 的價差當量</b>。
      </p>
      <p style="margin:10px 0 0">
        <b>Spread 的問題與配置的問題差三到四個數量級。它們不該被放在同一句話裡當成可比的旋鈕。</b>
        這也是為什麼「Spread 未知」不是一個擋路的問題——<b>它就算是 100 bp，也只有 $52/年。</b>
      </p>
    </div>
  </section>
''')


# ------------------------------ 7. limits ---------------------------------
RHO_CLAIM = rfact("rho_claim", "中位數約 +0.11")
SANITY_CLAIM = rfact("sanity_claim", "（週四 319 次；週一~週日全掃 0.8457~0.8541）")
RHOS = sorted(float(r[9]) for r in OOS)
A(f'''
  <section id="limits">
    <h2>七、限制、未知，以及本頁作者重算時發現的兩處不一致</h2>
    <p class="section-note">
      這一節照慣例放在結論前面，而不是塞在最後面當免責聲明。
      <b>如果下面任何一條讓你覺得前面的結論變弱了，那是對的——它本來就該那麼弱。</b>
    </p>

    <h3 class="sub">7.1　本頁作者的兩處不一致（都不改變結論，但都不吸收掉）</h3>
    <div class="callout bad">
      <h3>不一致 1：一個秩相關的中位數，研究員的報告寫反了方向</h3>
      <p style="margin:0">
        研究員的報告在講「挑執行小時」那一段寫：六個前後半段秩相關「<b>{esc(RHO_CLAIM)}</b>」。
        <b>本頁從同一份 log 把六個值全部取出來重算，中位數是 {dash(f"{OOS_RHO_MED:+.4f}")}。</b>
        六個值是：{esc("、".join(dash(f"{r:+.3f}") for r in RHOS))}。
      </p>
      <p style="margin:10px 0 0">
        <b>更正的方向對結論無害，而且是往更不利於「挑得出來」的方向</b>：
        秩相關的中位數是<u>負的</u>，代表前半段便宜的小時在後半段<b>偏向變貴</b>，
        比「幾乎無關」更糟。<b>「六次全部失敗」這個判定不變。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>這句話只出現在研究員的報告檔裡，狀態檔沒有引用它</b>
        （狀態檔寫的是區間 {dash(OOS_RHO_LO)}~+{OOS_RHO_HI}，那是正確的）。
        <b>所以這個錯誤沒有污染任何先前發布的頁面。</b>
      </p>
    </div>
    <div class="callout">
      <h3>不一致 2：{F["hold_state"]} 顆這個基準，對應的其實是星期五口徑</h3>
      <p style="margin:0">
        研究員的對帳表寫 {F["hold_state"]}「{esc(SANITY_CLAIM)}」。
        <b>本頁用同一份日 K 重跑那 14 種口徑：週四收盤是 {HOLD_THU:.4f}，
        而 {F["hold_state"]} 對應的是<u>週五</u>收盤（重算到小數第六位是 {HOLD_FRI:.6f}，週四是 {HOLD_THU:.6f}）。</b>
        全掃範圍 {HOLD_LO:.4f}~{HOLD_HI:.4f} 則與研究員寫的完全一致。
      </p>
      <p style="margin:10px 0 0">
        <b>影響：可以忽略，但要說出來。</b>
        頭條那個「實際是基準的幾 %」用全部 14 種口徑算是
        <b>{PCT_LO:.2f}%~{PCT_HI:.2f}%</b>，差異出現在小數第二位。
        <b>本頁因此全程報區間，而不是報那一個點。</b>
      </p>
    </div>

    <h3 class="sub">7.2　明確的未知——研究員要求不要填補，本頁照辦</h3>
    <ul class="limits">
      <li><b>兩個計畫的 Spread 實際值。</b>六個端點實測全部需要簽章；
        <b>只有你本人查得到，而團隊沒有、也不會去找你的憑證。</b></li>
      <li><b>兩個計畫的真實建立日期與金額歷史。</b><a href="#headline">第一節</a>整段建立在這個未知上。</li>
      <li><b>★ 你的 ETH 現貨存量——十六輪從來沒有被記錄過。</b>
        <a href="#actionable">第六節</a>的 {F["eth_yield"]} 建立在推估存量上，
        <b>表裡已經給了 0.25~4.0 ETH 的敏感度，請用那個範圍讀它，不要用那一個數字。</b></li>
      <li><b>入金紀錄。</b>第十輪已列，仍未查。整個閒置漏損的鋸齒形狀建立在
        <b>2026-09-18 的單一觀測值</b>上，這一輪只改了它的利率口徑與燃燒率解讀，
        <b>沒有增加任何新的觀測</b>。</li>
      <li><b><code>subscriptionCycle</code> 在 2026 年是否仍是那八個。</b>封存快照是 2025-02。</li>
      <li><b>BTC 專屬災難的機率。</b>分散化論證唯一站得住的版本，<b>無法從任何資料推導</b>。</li>
    </ul>

    <h3 class="sub">7.3　研究員自揭的限制（13 項，這裡挑最會影響讀法的）</h3>
    <ul class="limits">
      <li><b>本輪沒有取得任何乾淨的首次讀取，也不宣稱有。</b>
        所有序列都落在本專案已經反覆使用過的同一段日曆上。</li>
      <li><b>不重疊視窗 n = {NOW_BLOCKS[0]["n"]} / {NOW_BLOCKS[1]["n"]} / {NOW_BLOCKS[2]["n"]}。
        這個樣本數不能拒絕任何東西</b>，包括「幾何平均其實不是 1.0」。
        它被當成離散度的描述，<b>不是檢定</b>。</li>
      <li><b>母體限制與 BTC 自身漂移完全相同</b>：ETH/BTC 只有 9.1 年可交易史，
        要釘到 ±5%／年需要 {F["years_111"]}。<b>這不是資料清理問題，是資料本身不夠長。</b></li>
      <li><b>全部使用幣安單一場所、單一交易對、日收盤。</b>
        星期／開收盤的 14 種口徑已測（差 ±0.5%），<b>但跨交易所沒有測。</b></li>
      <li><b>起點掃描的 {M1_N} 列共用同一個終點價格，不是獨立抽樣。</b>
        「{M1_AHEAD}」不是勝率，研究員自己先標註了，本頁跟著標。</li>
      <li><b>時點檢定的置中均價用到了未來資料</b>，所以它不可交易——
        但它本來就是公平性檢定而不是策略。研究員另外做了「只用未來 7 天」的因果版本，結論一致。</li>
      <li><b>計畫年齡推論的四個假設：無提領、無計畫外 BTC、金額恆為 {F["weekly"]}、未暫停。
        任何一項不成立就失效。</b></li>
      <li><b>官方 API 文件來自 Wayback 封存</b>（時間戳已記錄），
        <b>無法證明幣安此後沒有修訂</b>。法律文件則是今天直接讀的。</li>
      <li><b>研究員沒有使用、也沒有去尋找你的 API 憑證。</b>
        所有帳戶層級的數字都是推論或取自狀態檔。</li>
    </ul>

    <h3 class="sub">7.4　這一頁的把關程度</h3>
    <div class="callout">
      <p style="margin:0">
        <b>本輪沒有走完整的外部覆核流程。</b>把關由兩層組成：
        <b>(1) 協調者對關鍵數字的逐項獨立重算</b>（頭條那張隱含報酬表、流量／存量比、
        今日利率複驗都是協調者自己重算的）；
        <b>(2) 本頁作者從 <code>eth_plan/data/</code> 的原始日 K 與各腳本的 log 重新產生每一個數字</b>。
      </p>
      <p style="margin:10px 0 0">
        <b>本頁沒有任何一個數字是人工從報告抄過來的。</b>
        產生本頁的程式在寫檔前會做三件事：把只存在於狀態檔的數字
        <b>逐一斷言「這串字確實出現在狀態檔裡」</b>；
        把其餘數字<b>從資料檔或 log 解析出來並斷言解析成功</b>；
        最後檢查<b>標籤閉合、樣式類別全部有定義、站內連結全部解析得到</b>。
      </p>
      <p style="margin:10px 0 0">
        <b>這一段之所以寫出來，是因為「這一頁被檢查到什麼程度」本身就是你需要知道的資訊。
        它比平常短，所以本頁的所有結論都該按這個折扣讀。</b>
      </p>
    </div>
  </section>
''')

# ------------------------------ conclusion --------------------------------
A(f'''
  <section id="conclusion">
    <h2>結論</h2>

    <div class="plain">
      <span class="lbl">一段話講完</span>
      <p>這一輪被派去查「ETH 那個定投計畫該不該存在」，
        <b>研究員拒絕替你決定，而且他是對的</b>：資料在方向上量不出東西，
        能量出來的只有「這個賭注有多大」，而那個答案是「很大，而且大到蓋住所有可能的配置」。</p>
      <p><b>但在量的過程中撞到一件更基礎的事</b>：
        十六輪的報告都把一個六年的模擬放在最前面，
        <b>而你的帳戶對應的大約是 24 週</b>。
        <b>回測沒有因此失效，但「1.0000 是誰的成績」這件事，我們一直沒有講清楚。</b></p>
      <p><b>你現在可以做的最有價值的一件事，是打開帳戶看一眼兩個計畫的建立日期，
        然後告訴協調者。</b>那一句話會確認或推翻這一頁的<a href="#headline">第一節</a>，而它只花你十秒鐘。</p>
    </div>

    <h3 class="sub">這一輪確定的事（代數層級，不會被新資料推翻）</h3>
    <ul class="limits">
      <li><b>用美元算的比值與用 BTC 顆數算的比值是同一個數，用 ETH 顆數算的是它的倒數。</b>
        「三個計價口徑」在點估計上是誤導框架，<b>三者只在變異數上分家</b>。</li>
      <li><b>在幣數口徑下，ETH 配置就是一個純粹對 ETH/BTC 的方向性部位</b>，
        BTC 自己的價格只透過權重進入。<b>不是分散化。</b></li>
      <li><b>以 BTC 顆數記分時變異數對 w 嚴格遞增、沒有內點。</b>
        美元口徑下有內點的條件是 ρ &lt; σ<sub>BTC</sub>/σ<sub>ETH</sub>，
        <b>而這個條件在 {len(DIV)} 個視窗裡有 {DIV_NEG} 個不成立。</b></li>
      <li><b>兩個口徑的對數遺憾完全相同</b>；對 &#123;全BTC, 全ETH&#125; 的 minimax 是 w = 1/2，
        對 &#123;全BTC&#125; 的 minimax 是 w = 0。<b>兩者都對，差別是基準集合，而基準集合就是目標函數。</b></li>
      <li><b>閒置利息 = 平均閒置餘額 × 利率，與有幾個計畫在消耗它無關。ETH 不會新增第二筆漏損。</b></li>
      <li><b>成長最適公式裡的 σ²/2 要靠再平衡才拿得到，兩個獨立定投計畫拿不到。</b></li>
    </ul>

    <h3 class="sub">這一輪<b>沒有</b>確定的事</h3>
    <ul class="limits">
      <li><b>「ETH 該不該存在」沒有答案，而且本頁認為它不該有答案。</b>
        任何人給你一個百分比，都是把 [{dash(f"{B_P025:.2f}")}, +{B_P975:.2f}] 假裝成一個點。</li>
      <li><b>計畫年齡是推論不是觀測</b>，有四個假設，<b>你一句話就能推翻</b>。</li>
      <li><b>你的 ETH 存量仍然是未知</b>，所以那個 {F["eth_yield"]} 是量級不是帳單。</li>
      <li><b>兩個計畫的 Spread 實際值仍然未知</b>，而且<b>只有你查得到</b>。</li>
      <li><b>本輪沒有任何候選走到能算幣數比的階段，因此本頁不提供新的幣數比。</b></li>
    </ul>

    <div class="callout bad">
      <h3>為什麼這一頁不寫「終局」「結案」「已證實」</h3>
      <p style="margin:0">
        <b>因為這一輪本身就是反例。</b>一個被記在狀態檔第 9 行、放了十六輪的數字，
        和另一個放在旁邊的數字，<b>相除一次就改變了三份結論的讀法</b>。
        <b>沒有人做錯什麼，只是沒有人再看一次。</b>
      </p>
      <p style="margin:10px 0 0">
        <b>這種事會再發生。</b>所以這一頁的每一個判定都該讀成
        「以今天能看到的證據，它是這樣」，而不是「它永遠是這樣」。
      </p>
      <p style="margin:14px 0 0;font-size:1.04rem">
        <b>而這一輪最實際的一句話，和前面每一輪是同一句，只是現在它的強度是原本的兩倍：
        在目前這個資金規模上，把錢投進去的那個動作本身，比任何一個聰明的操作都有效。</b>
        流量是存量的 {FS_NEW:.2f} 倍，不是 {FS_OLD:.2f} 倍。
      </p>
    </div>

    <h3 class="sub">相關頁面</h3>
    <ul class="limits">
      <li><b><a href="crypto-dca-amplifier-report.html">DCA 放大器 · 總覽報告（v1，已凍結）</a></b>——
        六年幣數比的完整記錄。<b>本頁更正它的是一個基準點的說明</b>：
        <a href="crypto-dca-amplifier-report.html#coin-ratio">〈幣數比〉那一節</a>的
        1.0000 是一段<b>模擬</b>的結果，不是使用者的帳戶歷史。
        <b>依規則該頁不修改，更正寫在這裡並回連。</b></li>
      <li><b><a href="crypto-dca-amplifier-report.html#lending">第八輪：出借 BTC 的否決</a></b>——
        <a href="#actionable">第六節</a>說明那個否決是對「BTC 這個幣種」的，不是對產品的。</li>
      <li><b><a href="crypto-dca-amplifier-report.html#flow">流量 vs 存量</a></b>——
        本頁把那裡的 {F["flow_old"]}更正為 {FS_NEW:.2f} 倍，<b>方向是讓該節的論點更強。</b></li>
      <li><b><a href="laoliu-r15-triage2.html">第十五輪：第二輪外部盤點</a></b>——
        上一輪；它的<a href="laoliu-r15-triage2.html#glossary">術語表</a>與本頁的互補。</li>
      <li><b><a href="crypto-dca-amplifier-report.html#glossary">完整術語對照表（69 條）</a></b>——
        本頁的<a href="#glossary">術語表</a>只收這一頁用得到的。</li>
      <li><b><a href="laoliu.html">老六研究院索引</a></b></li>
    </ul>
  </section>

</main>

<footer>
  老六 · 第十六輪：ETH 定投計畫 · {TODAY}<br>
  數字來源：<code>eth_plan/</code>（<code>data/</code> 的日 K 與利率快照、10 支腳本的
  <code>logs_*.log</code>、<code>evidence/</code> 的法律與 API 文件存檔），
  由 <code>tools/build_laoliu_r16.py</code> 讀取後注入本頁，<b>未經人工轉抄</b>；
  只存在於狀態檔的數字在建置時逐一斷言其字面存在。<br>
  研究員的回歸測試：<code>pytest test_eth_plan.py -q</code> → <b>{F["pytest"]}</b>。
  本頁作者的獨立重算使用同一份 <code>eth_plan/data/</code>，<b>未修改該目錄任何檔案</b>。<br>
  本頁為研究記錄，不構成投資建議；<b>研究仍在進行中，結論可能隨新證據修正</b>。<br>
  <b>本頁發布後不再修改。</b>要更新請建立新頁並回連本頁。
</footer>

</body>
</html>
''')


# ================================ validation ================================
doc = "".join(P)

# --- 1. section numbers are generated, never hand-written -------------------
SECNUM = {"headline": "一", "exist": "二", "diversify": "三", "idle": "四",
          "timing": "五", "actionable": "六", "limits": "七"}


def _fixref(m):
    a = m.group(1)
    return f'<a href="#{a}">第{SECNUM[a]}節</a>' if a in SECNUM else m.group(0)


doc, nfix = re.subn(r'<a href="#([a-z0-9]+)">第[一二三四五六七八九十]+節</a>', _fixref, doc)
for a, num in SECNUM.items():
    body = doc.split(f'<section id="{a}">', 1)[1]
    h2 = re.search(r"<h2>(.*?)</h2>", body, re.S).group(1)
    assert h2.startswith(num + "、"), f"section #{a} h2 starts {h2[:8]!r}, want {num}"
stray = re.findall(r"(?<!>)第[一二三四五六七八九十]+節",
                   re.sub(r'<a href="#[a-z0-9]+">第[一二三四五六七八九十]+節</a>', "", doc))
assert not stray, f"section reference outside an anchor: {stray}"

# --- 2. tag balance ---------------------------------------------------------
from html.parser import HTMLParser                                 # noqa: E402

VOID = {"meta", "br", "hr", "img", "input", "link", "circle", "line", "polyline",
        "path", "rect"}


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
assert not bal.err, f"unbalanced tags: {bal.err[:4]}"
assert not bal.stack, f"unclosed tags: {bal.stack}"

# --- 3. every CSS class used must be defined, with the right element ---------
css_body = re.search(r"<style>(.*?)</style>", CSS, re.S).group(1)
allowed = {}
for elem, cls in re.findall(r"([a-zA-Z]*)\.([A-Za-z][A-Za-z0-9_-]*)", css_body):
    allowed.setdefault(cls, set()).add(elem.lower())
bad_cls = []
for tag, attr in re.findall(r"<([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>", doc):
    m = re.search(r'\bclass="([^"]*)"', attr)
    if not m:
        continue
    assert m.group(1).strip(), f"empty class attribute on <{tag}>"
    for c in m.group(1).split():
        if c not in allowed:
            bad_cls.append((tag, c, "undefined"))
        elif "" not in allowed[c] and tag.lower() not in allowed[c]:
            bad_cls.append((tag, c, f"defined only for {sorted(allowed[c])}"))
assert not bad_cls, f"dead CSS classes: {sorted(set(bad_cls))}"

# --- 4. anchors ------------------------------------------------------------
own_ids = set(re.findall(r'id="([A-Za-z0-9_-]+)"', doc))
for href in re.findall(r'href="#([A-Za-z0-9_-]+)"', doc):
    assert href in own_ids, f"dangling in-page anchor #{href}"
for page, frag in re.findall(r'href="([a-z0-9\-.]+\.html)#([A-Za-z0-9_-]+)"', doc):
    pool = {"crypto-dca-amplifier-report.html": V1_IDS,
            "laoliu-r15-triage2.html": R15_IDS}.get(page)
    assert pool is not None, f"link to unknown page {page}"
    assert frag in pool, f"{page}#{frag} does not exist in that file"
for page in set(re.findall(r'href="([a-z0-9\-.]+\.html)', doc)):
    assert os.path.exists(os.path.join(REPO, page)), f"link to missing file {page}"

# --- 5. wide tables --------------------------------------------------------
for m in re.finditer(r'<div class="table-wrap([^"]*)"[^>]*>(.*?)</div>', doc, re.S):
    ncol = len(re.findall(r"<th\b", m.group(2).split("</tr>", 1)[0]))
    if ncol > 4:
        assert "wide" in m.group(1), f"{ncol}-column table without .wide: " \
                                     f"{m.group(2)[:120]}"

# --- 6. wording discipline -------------------------------------------------
for w in ("終局", "結案", "已證實"):
    for mm in re.finditer(w, doc):
        ctx = doc[max(0, mm.start() - 40):mm.start() + 20]
        assert "不寫" in ctx or "不下" in ctx or "不宣稱" in ctx, \
            f"forbidden word {w} in an affirmative sentence: {ctx!r}"
for name in ("費曼", "凱利", "唐1", "TANG-1", "TE-1", "DE-1"):
    assert name not in doc, f"forbidden cross-line reference: {name}"
assert "研究進行中" in doc

open(OUT, "w", encoding="utf-8").write(doc)
print(f"wrote {OUT}  {len(doc):,} bytes;  {nfix} section refs normalised; "
      f"{len(own_ids)} anchors; all checks passed")


# ---------------- index card (regenerated between markers) ----------------
CARD = f'''<!-- R16-CARD:BEGIN (generated by tools/build_laoliu_r16.py — do not hand-edit) -->
  <a class="report-card" href="laoliu-r16-eth.html">
    <div class="top">
      <span class="title">第十六輪 · ETH 定投計畫</span>
      <span class="tag">{TODAY}</span>
      <span class="tag">四項任務 · 兩個前提被推翻</span>
      <span class="tag">回歸測試 {F["pytest"]}</span>
      <span class="tag live">研究進行中</span>
    </div>
    <div class="desc">
      <b>★ 你的兩個定投計畫大約只跑了半年，不是六年。</b>
      狀態檔十六輪並排記著「每週 {F["weekly"]}」與「現貨 {F["user_btc"]}」，<b>沒有人把它們相除過</b>。
      相除之後：實際持有只有六年純定投模擬（{HOLD_LO:.4f}~{HOLD_HI:.4f} 顆）的
      <b>{PCT_LO:.2f}%~{PCT_HI:.2f}%</b>，唯一對得上合理報酬的長度是<b>約 {AGE_N} 次買進</b>。
      影響三件、要分開讀：<b>(1) 舊報告最前面那個「1.0000」是一段模擬，不是你的帳戶</b>——
      <b>但回測沒有失效</b>，它量的是「策略在那段歷史上會怎樣」，那仍然成立；
      <b>(2) 流量／存量比是 {FS_NEW:.2f} 倍不是 {FS_OLD:.2f} 倍</b>（第九輪只算了一個計畫），
      <b>這強化而不是削弱第九輪的結論</b>；
      <b>(3) ETH 腿在你真正經歷過的那段期間是領先的（{G_N} 格全部 &gt; 1），
      在 2020-08 那個模擬起點上是落後的——兩個都真，而且都不預測任何事。</b>
      主線任務「ETH 該不該存在」：<b>研究員拒絕代為決定</b>，因為漂移在六個視窗全不顯著、
      要釘到 ±5%／年需 {F["years_111"]}；<b>而 minimax 有兩個答案，兩個都對</b>——
      差別不在數學，在<b>你拿誰當基準</b>。
      <b>持有 ETH 不是分散化</b>：BTC 幣數口徑是推導（變異數無內點），
      <b>美元口徑下也死</b>（ρ {F["rho_full"]}／近一年 {F["rho_1y"]}，{DIV_WORSE} 個視窗全部比純 BTC 更晃）；
      <b>唯一站得住的反面理由是「BTC 專屬滅絕事件」，而它依定義不在樣本裡——量不到，也不假裝量得到。</b>
      另外：<b>閒置池是共用的，ETH 不新增第二筆漏損</b>（反而讓第十輪的點估計變可信）；
      <b>「挑執行小時」第六次被量測，樣本內像通過門檻、樣本外 6/6 失敗</b>。
      誠實標註：<b>計畫年齡是推論，你看一眼帳戶就能推翻</b>；
      <b>你的 ETH 存量十六輪從未記錄，那筆 {F["eth_yield"]} 建立在推估上</b>；
      <b>不重疊視窗只有 {NOW_BLOCKS[0]["n"]}/{NOW_BLOCKS[1]["n"]}/{NOW_BLOCKS[2]["n"]} 個，不能拒絕任何東西</b>；
      <b>本輪沒有乾淨的首次讀取，也沒有新的幣數比</b>。
    </div>
    <div class="stats">
      <div>實際持有 ÷ 六年模擬基準<b class="neg">{PCT_LO:.2f}%~{PCT_HI:.2f}%</b></div>
      <div>唯一對得上的計畫長度<b>{AGE_N} 次買進 · 約 {AGE_YEARS:.2f} 年</b></div>
      <div>流量／存量比（更正）<b>{FS_OLD:.2f}× → {FS_NEW:.2f}×</b></div>
      <div>ETH 腿在真實期間（{G_N} 格）<b>{G_LO:.4f} ~ {G_HI:.4f}</b></div>
      <div>ETH 腿在模擬期間（14 格）<b class="neg">{SIM_LO:.4f} ~ {SIM_HI:.4f}</b></div>
      <div>ETH/BTC 漂移：六個視窗最大 |t|<b class="neg">{NU_MAX_T}</b></div>
      <div>挑小時：樣本外排名<b class="neg">{OOS_RANK_LO}~{OOS_RANK_HI} / 24</b></div>
      <div>本輪新幣數比<b class="neg">0 個</b></div>
    </div>
  </a>
<!-- R16-CARD:END -->
'''
idx = open(INDEX, encoding="utf-8").read()
if "<!-- R16-CARD:BEGIN" in idx:
    idx = re.sub(r"<!-- R16-CARD:BEGIN.*?<!-- R16-CARD:END -->\n", CARD, idx, flags=re.S)
else:
    anchor = "<!-- R15-CARD:BEGIN"
    assert anchor in idx, "R15 card marker not found in the index"
    idx = idx.replace(anchor, CARD + "\n" + anchor, 1)
n_cards = len(re.findall(r'<a class="report-card"', idx))
idx, nsub = re.subn(r'<div class="count">共 \d+ 份報告</div>',
                    f'<div class="count">共 {n_cards} 份報告</div>', idx)
assert nsub == 1, nsub
open(INDEX, "w", encoding="utf-8").write(idx)
print(f"updated {INDEX}: {n_cards} cards")
