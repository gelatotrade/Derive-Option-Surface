"""Write docs/paper2/NUMBERS.md and results/p2/summary.json from results/p2.

The number sheet is the single source of numbers for the Paper 2 manuscript. Run from anywhere after
`p2 infer` and the H4 run (`inference_p2_h4 run`):

    python3 scripts/p2_numbers.py [--results results/p2] [--out docs/paper2/NUMBERS.md]
                                  [--summary results/p2/summary.json] [--quiet]

Nothing about the data is written into this script: the cut-off is the last fill of the sample (``h4.json``
``sample``), cross-checked against the last day of H1, H3 and the reference book; every number comes from the
files in the results directory. ``summary.json`` is flat ({key: scalar}), sorted and deterministic. Its keys do not
depend on the data, except the ``event_<event id>_*`` family (one set per row of ``events.csv``). Slots that the
data do not fill (a currency without cells, an account label without days) are present with ``null``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results" / "p2"
OUT = REPO / "docs" / "paper2" / "NUMBERS.md"
SUMMARY_NAME = "summary.json"
SCHEMA = "p2-summary-1"

CCYS = ("BTC", "ETH", "HYPE")
MANAGERS = ("sm", "pm", "pm2")
LABELS = tuple(f"M{i}" for i in range(1, 11))       # the ten dominant maker subaccounts (p2ids rank labels)
DAY = 86_400
H4_ALPHA = 0.05                                       # preregistered one-sided level of the H4 test
TOL = 1e-9

REQUIRED = ("h1.json", "h1_cells.csv", "h2.json", "h3.json", "h4.json", "sensitivity.json", "sensitivity_h4.json",
            "capital_check.json", "validation_summary.json", "validation.csv", "events.csv", "reference_book.csv",
            "manager_oi_share.csv")

MANAGER_NAME = {"sm": "SM", "pm": "legacy PM", "pm2": "PM2"}
KIND_NAME = {"single": "single contract", "book": "book"}
STRUCT_NAME = {"BasisContingencyParameters": "basis", "OtherContingencyParameters": "contingencies",
               "VolShockParameters": "vol shock", "MarginParameters": "margin", "SkewShockParameters": "skew",
               "scenarios": "scenarios", "CollateralParameters": "collateral", "maxExpiries": "maxExpiries"}
SECTION_TITLE = {"a_maps": "(a) Maps under other managers", "b_mm": "(b) MM instead of IM",
                 "c_p1_net_edge": "(c) Net edge in the form of Paper 1 (fee and rebate undivided)",
                 "d_h2": "(d) H2 variants", "e_h3": "(e) H3 variants", "f_time": "(f) Time normalisation",
                 "g_by_ccy": "(g) Values per underlying",
                 "h1_sign": "(h) Sign structure of H1 (review round 1; groups by the sign of the edge choose their "
                            "cells anew in every replication, audit A04)"}
VARIANT_LABEL = {
    ("a_maps", "pm2"): "PM2, PM2 window (equal to test H1)",
    ("a_maps", "sm_all"): "SM, whole period",
    ("a_maps", "pm_all"): "legacy PM, whole period",
    ("a_maps", "sm_pm2_window"): "SM on the fills of the PM2 window",
    ("a_maps", "pm_pm2_window"): "legacy PM on the fills of the PM2 window",
    ("b_mm", "h1_pm2_mm"): "H1 with MM",
    ("b_mm", "h1_sm_all_mm"): "map SM, whole period, with MM",
    ("b_mm", "h2_ratio_mm"): "H2 with MM",
    ("b_mm", "h3_mm"): "H3 with MM",
    ("c_p1_net_edge", "h1_pm2"): "H1 with net edge as in Paper 1",
    ("d_h2", "ratio"): "ratio (equal to test H2)",
    ("d_h2", "ratio_unit"): "next single contract (ratio_unit)",
    ("d_h2", "ratio_tape"): "book from the tape",
    ("d_h2", "ratio_mm"): "MM",
    ("e_h3", "sm_pm2"): "K_SM/K_PM2 (equal to test H3)",
    ("e_h3", "sm_pm2_mm"): "K_SM/K_PM2 with MM",
    ("e_h3", "sm_pm_be"): "K_SM/K_PM, BTC and ETH legs",
    ("e_h3", "pm_pm2_be"): "K_PM/K_PM2, BTC and ETH legs",
    ("e_h3", "sm_pm2_be"): "K_SM/K_PM2, BTC and ETH legs",
    ("e_h3", "sm_pm2_le63"): "days with at most 63 options",
    ("e_h3", "sm_pm2_gt63"): "days with more than 63 options",
    ("f_time", "to_expiry"): "to expiry, annualised",
    ("f_time", "holding"): "empirical holding time",
    ("f_time", "holding_excl_transfer"): "holding time without transfers",
    ("e_h3", "sm_pm2_le63_no_sm"): "days with at most 63 options without SM account",
    ("h1_sign", "within_pos"): "only cells with edge > 0",
    ("h1_sign", "within_nonpos"): "only cells with edge ≤ 0",
    ("h1_sign", "within_sell"): "only maker sells",
    ("h1_sign", "within_buy"): "only maker buys",
    ("h1_sign", "within_pos_sell"): "maker sells with edge > 0",
    ("h1_sign", "within_pos_buy"): "maker buys with edge > 0",
}
GROUP_NAME = {"by_label": "account", "by_ccy": "underlying", "by_regime": "regime",
              "by_account_manager": "manager of the account"}
STATUS_NAME = {"no_options": "without options", "no_snapshot": "without snapshot"}
REGIMES = ("R1", "R2", "R3", "R4")                   # parameter regimes of the figures (FIGURE_SELECTION 6.6)
GROUP_SLOTS = {"by_label": LABELS, "by_ccy": CCYS, "by_regime": REGIMES, "by_account_manager": ("SM", "PM", "PM2")}
VERDICT_FIELDS = ("stat", "lo", "hi", "rejected", "n")

NNBSP = " "   # narrow no-break space as thousands separator (as in the Paper 1 sheet)
MINUS = "−"
MISSING = "n/a"    # a value the data do not give (as in the Paper 1 sheet)
SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")

try:  # the preregistered end of the sample, only used to say whether these are pilot numbers
    sys.path.insert(0, str(REPO))
    from derive_surface.p2events import SAMPLE_END_TS as PREREG_END_TS  # noqa: E402
except Exception:  # pragma: no cover - the sheet still works without the package
    PREREG_END_TS = None


# ---------------------------------------------------------------------------------------------------------------
# formatting
# ---------------------------------------------------------------------------------------------------------------

def _missing(x) -> bool:
    if x is None:
        return True
    try:
        return not math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def num(x, digits: int = 2, sign: bool = False) -> str:
    """Decimal point, narrow no-break space for thousands, typographic minus."""
    if _missing(x):
        return MISSING
    v = round(float(x), digits)
    body = f"{abs(v):,.{digits}f}".replace(",", NNBSP)
    if v < 0:
        return MINUS + body
    return ("+" + body) if (sign and v > 0) else body


def di(x) -> str:
    if _missing(x):
        return MISSING
    return num(int(round(float(x))), 0)


def sig(x, n: int = 2) -> str:
    """n significant digits, e.g. 0.00032617 -> 0.00033."""
    if _missing(x):
        return MISSING
    if float(x) == 0:
        return "0"
    digits = max(0, n - 1 - int(math.floor(math.log10(abs(float(x))))))
    return num(x, digits)


def sci(x, digits: int = 1) -> str:
    """8.7e-10 -> 8.7·10⁻¹⁰."""
    if _missing(x):
        return MISSING
    if float(x) == 0:
        return "0"
    mant, exp = f"{float(x):.{digits}e}".split("e")
    mant = mant.replace("-", MINUS)
    return f"{mant}·10{str(int(exp)).translate(SUPERSCRIPT)}"


def pct(x, digits: int = 1, sign: bool = False) -> str:
    if _missing(x):
        return MISSING
    return num(100 * float(x), digits, sign) + " %"


def fmt_day(x) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return MISSING
    return pd.Timestamp(str(x)).strftime("%Y-%m-%d")


def fmt_ts(x, seconds: bool = True) -> str:
    if x is None:
        return MISSING
    t = pd.Timestamp(x, unit="s", tz="UTC") if isinstance(x, (int, float, np.integer, np.floating)) else pd.Timestamp(x)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    return t.tz_convert("UTC").strftime("%Y-%m-%d %H:%M:%S" if seconds else "%Y-%m-%d %H:%M") + " UTC"


def fmt_month(m) -> str:
    return MISSING if m is None else f"{str(m)[:4]}-{str(m)[5:7]}"


def lvl(level) -> str:
    """0.9 -> 90 % (as in "90 % interval")."""
    return MISSING if _missing(level) else f"{num(100 * float(level), 0)} %"


def cell(name) -> str:
    """Cell names contain '|'; escape them inside markdown tables."""
    return str(name).replace("|", "\\|")


def ci(stat, lo, hi, digits: int) -> str:
    return f"{num(stat, digits)} [{num(lo, digits)}; {num(hi, digits)}]"


def verdict(rejected) -> str:
    if rejected is None:
        return "descriptive"
    return "**rejected**" if bool(rejected) else "not rejected"


def verdict_plain(rejected) -> str:
    if rejected is None:
        return "descriptive"
    return "rejected" if bool(rejected) else "not rejected"


def yes_no(x) -> str:
    return "yes" if bool(x) else "no"


def label_key(label: str) -> Tuple[int, str]:
    digits = "".join(ch for ch in str(label) if ch.isdigit())
    return (int(digits) if digits else 10 ** 9, str(label))


# ---------------------------------------------------------------------------------------------------------------
# flat summary
# ---------------------------------------------------------------------------------------------------------------

def _scalar(v: Any):
    if v is None:
        return None
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        f = float(v)
        return f if math.isfinite(f) else None
    if isinstance(v, str):
        return v
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    raise TypeError(f"summary values must be scalars, got {type(v).__name__}")


def _key(*parts) -> str:
    return "_".join(str(p) for p in parts if p != "").lower().replace("-", "_").replace(" ", "_")


class Summary(dict):
    def put(self, key: str, value: Any) -> None:
        self[_key(key)] = _scalar(value)


class Checks(list):
    def add(self, name: str, ok: bool, detail: str) -> None:
        self.append((name, bool(ok), detail))


def _get(d: Optional[dict], *path, default=None):
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def _bool_col(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().isin(("true", "1", "1.0"))


# ---------------------------------------------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------------------------------------------

def load(results: Path) -> Dict[str, Any]:
    missing = [n for n in REQUIRED if not (results / n).is_file()]
    if missing:
        raise FileNotFoundError(f"missing in {results}: {', '.join(missing)}")
    out: Dict[str, Any] = {}
    for n in REQUIRED:
        p = results / n
        out[n] = json.loads(p.read_text()) if n.endswith(".json") else pd.read_csv(p)
    return out


def _display(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(REPO))
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------------------------------------------

def cutoff(d: Dict[str, Any], s: Summary, checks: Checks, prereg_end_ts: Optional[int]) -> dict:
    h1, h2, h3, h4 = d["h1.json"], d["h2.json"], d["h3.json"], d["h4.json"]
    rb = d["reference_book.csv"]
    days = {"H1": h1.get("last_day"), "H3": h3.get("last_day"),
            "reference book": str(rb["day"].max()) if len(rb) else None}
    sample = h4.get("sample") or [None, None]
    start = pd.Timestamp(sample[0]) if sample[0] else None
    end = pd.Timestamp(sample[1]) if sample[1] else None
    if end is None:  # fall back to the last day any file reports
        last = max(v for v in days.values() if v)
        cut_day = str(last)
    else:
        cut_day = end.tz_convert("UTC").strftime("%Y-%m-%d") if end.tzinfo else end.strftime("%Y-%m-%d")
    is_pilot = None
    if end is not None and prereg_end_ts is not None:
        is_pilot = bool(end.timestamp() < prereg_end_ts - DAY)
    s.put("sample_start_utc", start.isoformat() if start is not None else None)
    s.put("sample_end_utc", end.isoformat() if end is not None else None)
    s.put("cutoff_day", cut_day)
    s.put("sample_prereg_end_utc",
          pd.Timestamp(prereg_end_ts, unit="s", tz="UTC").isoformat() if prereg_end_ts is not None else None)
    s.put("sample_is_pilot", is_pilot)
    bad = {k: v for k, v in days.items() if v != cut_day}
    h2_last = h2.get("last_day")
    ok = not bad and (h2_last is None or str(h2_last) <= cut_day)
    detail = (f"last day of H1, H3 and the reference book equal to the day of the last fill ({fmt_day(cut_day)}), "
              f"H2 ends on {fmt_day(h2_last)}")
    if not ok:
        detail = ("last days differ: " + ", ".join(f"{k} {fmt_day(v)}" for k, v in days.items())
                  + f", H2 {fmt_day(h2_last)}, last fill {fmt_day(cut_day)}")
    checks.add("Cut-off day consistent", ok, detail)
    return {"start": start, "end": end, "day": cut_day, "is_pilot": is_pilot, "prereg_end_ts": prereg_end_ts}


def header(d: Dict[str, Any], s: Summary, cut: dict, results: Path, summary_path: Path,
           now: dt.datetime, checks: Checks) -> List[str]:
    h1 = d["h1.json"]
    b, seed, level = h1.get("b"), h1.get("seed"), h1.get("level")
    s.put("b", b)
    s.put("seed", seed)
    s.put("level", level)
    s.put("summary_schema", SCHEMA)
    # every test and sensitivity file must carry the same B, seed and level
    found = {}
    for name in ("h1.json", "h2.json", "h3.json", "h4.json", "sensitivity.json", "sensitivity_h4.json"):
        found[name] = (d[name].get("b"), d[name].get("seed"), d[name].get("level", level))
    same = len(set(found.values())) == 1
    checks.add("B, seed and level equal in all files", same,
               f"B = {di(b)}, seed {seed}, level {pct(level, 0)}" if same else
               "; ".join(f"{k}: B {v[0]}, seed {v[1]}, level {v[2]}" for k, v in found.items()))
    if cut["end"] is not None:
        stand = f"Sample from {fmt_ts(cut['start'], seconds=False)} to the last fill at {fmt_ts(cut['end'])}"
    else:
        stand = f"Sample up to {fmt_day(cut['day'])} (last day of the result files)"
    if cut["is_pilot"] is True:
        stand += (f". **Pilot state:** the sample ends before the preregistered end "
                  f"({fmt_ts(cut['prereg_end_ts'], seconds=False)}); the numbers of the manuscript come from the "
                  f"final data run.")
    elif cut["is_pilot"] is False:
        stand += f". Final data: the sample reaches the preregistered end ({fmt_ts(cut['prereg_end_ts'], seconds=False)})."
    else:
        stand += "."
    return [
        "# Numbers for Paper 2", "",
        f"Generated {now.astimezone(dt.timezone.utc):%Y-%m-%d %H:%M} UTC from `{_display(results)}` with "
        f"`scripts/p2_numbers.py`. All headline numbers machine-readable in `{_display(summary_path)}` "
        f"(flat, stable keys).", "",
        f"- **Data status:** {stand} Cut-off day {fmt_day(cut['day'])}.",
        f"- **Inference:** B = {di(b)}, seed {seed}, {lvl(level)} percentile intervals from a cluster bootstrap "
        f"over UTC days (H1 to H3, Addendum 3). H4: wild cluster bootstrap with Rademacher weights and "
        f"restricted residuals, cluster UTC day, one-sided p for β > 0, 100 placebo dates.",
        "- **Measurement:** capital under IM (MM as a sensitivity), net edge per contract after Addendum 2: "
        "NE = MO_30min − (fee − rebate)/amount − hedge; edge of a fill = NE·amount. Accounts only as labels "
        "(M1 to M10).", ""]


def sample_section(d: Dict[str, Any], s: Summary, checks: Checks) -> List[str]:
    cap, h1, h2, h3, h4 = (d["capital_check.json"], d["h1.json"], d["h2.json"], d["h3.json"], d["h4.json"])
    ev = d["events.csv"]
    total = cap.get("rows")
    s.put("fills_total", total)
    by_ccy = {c: _get(cap, "managers", c, "sm", "n") for c in CCYS}
    for c in CCYS:
        s.put(f"fills_{c}", by_ccy[c])
    win = {c: _get(cap, "managers", c, "pm2", "n_in_window") for c in CCYS}
    win_total = sum(v for v in win.values() if v is not None)
    s.put("fills_pm2_window", win_total)
    for c in CCYS:
        s.put(f"fills_pm2_window_{c}", win[c])
        s.put(f"pm2_window_start_{c}", _get(h1, "window_start_utc", c))
    kle0 = {}
    for m in MANAGERS:
        kle0[m] = sum(int(_get(cap, "managers", c, m, "sides", side, "k_le_0", default=0) or 0)
                      for c in CCYS for side in ("buy", "sell"))
        s.put(f"k_le_0_{m}", kle0[m])
    checks.add("Fills per underlying add up to the sample",
               total == sum(v for v in by_ccy.values() if v is not None),
               f"{' + '.join(di(by_ccy[c]) for c in CCYS)} = {di(total)}")
    checks.add("PM2 window: capital file and H1 count the same", win_total == h1.get("n_fills_window"),
               f"{di(win_total)} against {di(h1.get('n_fills_window'))}")

    n_events, n_kept = len(ev), int(_bool_col(ev["kept"]).sum())
    with_cells = int((_bool_col(ev["kept"]) & (pd.to_numeric(ev.get("panel_cells", 0), errors="coerce") > 0)).sum())
    ccy_list = lambda m: ", ".join(f"{c} {di(m.get(c))}" for c in CCYS if m.get(c) is not None)  # noqa: E731
    starts = ", ".join(f"{c} {fmt_ts(_get(h1, 'window_start_utc', c), seconds=False)}" for c in CCYS
                       if _get(h1, "window_start_utc", c))
    status = {k: v for k, v in (h3.get("status_counts") or {}).items() if k != "ok"}
    status_txt = ", ".join(f"{di(v)} {STATUS_NAME.get(k, k)}" for k, v in sorted(status.items())) or "none"
    return [
        "## Sample", "",
        f"- Fills of the Paper 1 sample: {di(total)} ({ccy_list(by_ccy)}).",
        f"- PM2 window from {starts}: {di(win_total)} fills ({ccy_list(win)}).",
        f"- Fills with capital per contract ≤ 0 under IM: SM {di(kle0['sm'])}, legacy PM {di(kle0['pm'])}, "
        f"PM2 {di(kle0['pm2'])} (nothing excluded; exclusions only under the rules of H2 and H3).",
        f"- H1: {di(h1.get('n'))} of {di(h1.get('n_cells_any'))} cells populated (at least "
        f"{di(h1.get('min_fills'))} fills; {ccy_list(h1.get('cells_by_ccy') or {})}), {di(h1.get('n_fills'))} fills "
        f"in populated cells, {di(h1.get('n_days'))} UTC days from {fmt_day(h1.get('first_day'))} to "
        f"{fmt_day(h1.get('last_day'))}.",
        f"- H2: sample of {di(h2.get('n_sample'))} fills of the accounts "
        f"{', '.join(sorted(h2.get('accounts') or [], key=label_key))} ({ccy_list(h2.get('fills_by_ccy') or {})}), "
        f"n = {di(h2.get('n'))} after exclusion, {di(h2.get('n_days'))} UTC days from {fmt_day(h2.get('first_day'))} to "
        f"{fmt_day(h2.get('last_day'))}.",
        f"- H3: {di(h3.get('n_rows'))} maker days in the window, of which {di(h3.get('n'))} computed (not computed: "
        f"{status_txt}), {di(h3.get('n_days'))} UTC days from {fmt_day(h3.get('first_day'))} to "
        f"{fmt_day(h3.get('last_day'))}.",
        f"- H4: {di(n_events)} events, {di(n_kept)} kept, of which {di(with_cells)} with panel cells; panel "
        f"{di(h4.get('n'))} rows from {di(h4.get('fills'))} fills, {di(h4.get('cell_events'))} "
        f"cell-event pairs, {di(h4.get('clusters'))} day clusters.", ""]


def validation_section(d: Dict[str, Any], s: Summary, checks: Checks) -> List[str]:
    vs, v = d["validation_summary.json"], d["validation.csv"].copy()
    v["is_initial"] = _bool_col(v["is_initial"])
    ok = v[v["status"].astype(str) == "ok"]
    stats = {}
    for kind in ("single", "book"):
        for mode, is_im in (("", True), ("_mm", False)):
            g = ok[(ok["kind"] == kind) & (ok["is_initial"] == is_im)]
            r = g["rel_err"].abs().to_numpy(float)
            r = r[np.isfinite(r)]
            st = {"n": int(len(g)),
                  "median_rel": float(np.median(r)) if len(r) else None,
                  "p95_rel": float(np.quantile(r, 0.95)) if len(r) else None,
                  "max_rel": float(r.max()) if len(r) else None,
                  "max_abs_usd": float(g["abs_err"].abs().max()) if len(g) else None}
            stats[(kind, mode)] = st
            for k, val in st.items():
                s.put(f"validation_{kind}{mode}_{k}", val)
    books = ok[ok["kind"] == "book"]
    s.put("validation_book_legs_min", int(books["n_legs"].min()) if len(books) else None)
    s.put("validation_book_legs_max", int(books["n_legs"].max()) if len(books) else None)
    bad = v[v["status"].astype(str) != "ok"]
    reverts = int(bad[["ccy", "manager", "kind", "block"]].drop_duplicates().shape[0])
    cells = vs.get("cells") or []
    n_pass = sum(1 for c in cells if c.get("passes"))
    passed = bool(cells) and n_pass == len(cells)
    thr = vs.get("thresholds") or {}
    psc = vs.get("per_scenario_check") or {}
    ts = pd.to_numeric(v["ts"], errors="coerce")
    s.put("validation_cases", vs.get("n_cases"))
    s.put("validation_reverts", reverts)
    s.put("validation_cells", len(cells))
    s.put("validation_cells_passed", n_pass)
    s.put("validation_passed", passed)
    s.put("validation_threshold_median", thr.get("median"))
    s.put("validation_threshold_p95", thr.get("p95"))
    s.put("validation_per_scenario_n", psc.get("n"))
    s.put("validation_per_scenario_equal", psc.get("all_equal"))
    s.put("validation_first_day", ts_day(ts.min()))
    s.put("validation_last_day", ts_day(ts.max()))
    checks.add("Validation: all cells below the threshold", passed, f"{n_pass} of {len(cells)} cells")
    si, bi = stats[("single", "")], stats[("book", "")]
    sm, bm = stats[("single", "_mm")], stats[("book", "_mm")]
    lines = [
        "## Validation of the replica against eth_call", "",
        f"- Threshold of the preregistration per underlying, manager and kind: median |rel| < {pct(thr.get('median'), 1)}, "
        f"95th percentile < {pct(thr.get('p95'), 0)}. Result: {n_pass} of {len(cells)} cells (IM and MM) "
        f"met, {'**passed**' if passed else '**not passed**'}.",
        f"- {di(vs.get('n_cases'))} cases at blocks from {fmt_day(ts_day(ts.min()))} to {fmt_day(ts_day(ts.max()))}; "
        f"{di(reverts)} {'case' if reverts == 1 else 'cases'} without a chain answer (revert), not comparable.",
        f"- Single contracts under IM: n = {di(si['n'])}, median |rel| {sci(si['median_rel'])}, p95 "
        f"{sci(si['p95_rel'])}, maximum {sci(si['max_rel'])}; largest absolute deviation "
        f"{sig(si['max_abs_usd'])} USD.",
        f"- Books under IM: n = {di(bi['n'])} ({di(books['n_legs'].min() if len(books) else None)} to "
        f"{di(books['n_legs'].max() if len(books) else None)} legs), median |rel| {sci(bi['median_rel'])}, p95 "
        f"{sci(bi['p95_rel'])}, maximum {sci(bi['max_rel'])}; largest absolute deviation "
        f"{sig(bi['max_abs_usd'])} USD.",
        f"- MM (sensitivity): single contracts median {sci(sm['median_rel'])}, p95 {sci(sm['p95_rel'])}; books "
        f"median {sci(bm['median_rel'])}, p95 {sci(bm['p95_rel'])}.",
        f"- Scenario path against direct call: {di(psc.get('n'))} books, bit-identical: {yes_no(psc.get('all_equal'))}.",
        "", "| Kind | Underlying | Manager | n | missing | Median \\|rel\\| | p95 \\|rel\\| | Max \\|rel\\| | Threshold |",
        "|---|---|---|---:|---:|---:|---:|---:|---|"]
    order = {"single": 0, "book": 1}
    for c in sorted((c for c in cells if c.get("is_initial")),
                    key=lambda c: (order.get(c.get("kind"), 9), c.get("ccy", ""), MANAGERS.index(c["manager"])
                                   if c.get("manager") in MANAGERS else 9)):
        lines.append(f"| {KIND_NAME.get(c.get('kind'), c.get('kind'))} | {c.get('ccy')} | "
                     f"{MANAGER_NAME.get(c.get('manager'), c.get('manager'))} | {di(c.get('n'))} | "
                     f"{di(c.get('n_missing'))} | {sci(c.get('median_rel'))} | {sci(c.get('p95_rel'))} | "
                     f"{sci(c.get('max_rel'))} | {'met' if c.get('passes') else '**missed**'} |")
    return lines + [""]


def ts_day(x) -> Optional[str]:
    if _missing(x):
        return None
    return pd.Timestamp(int(x), unit="s", tz="UTC").strftime("%Y-%m-%d")


def _pooled(cells: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
    if not len(cells):
        return None, None
    e, i, k = cells["sum_edge"].sum(), cells["sum_index"].sum(), cells["sum_K"].sum()
    return (1e4 * e / i if i else None), (1e4 * e / k if k else None)


def h1_section(d: Dict[str, Any], s: Summary, checks: Checks) -> List[str]:
    h1, cells, sens = d["h1.json"], d["h1_cells.csv"], d["sensitivity.json"]
    occ = cells[_bool_col(cells["occupied"])].copy()
    for k in ("stat", "lo", "hi", "rejected", "threshold", "n", "n_cells_any", "n_fills", "n_fills_window",
              "n_fills_k_le_0", "n_fills_nonfinite", "n_days", "first_day", "last_day", "cells_present_min",
              "n_nan_draws", "min_fills"):
        s.put(f"h1_{'n_cells' if k == 'n' else k}", h1.get(k))
    for c in CCYS:
        s.put(f"h1_n_cells_{c}", _get(h1, "cells_by_ccy", c))
        s.put(f"h1_fills_{c}", _get(h1, "fills_by_ccy", c))
    a, b = _pooled(occ)
    s.put("h1_pooled_edge_bp_notional", a)
    s.put("h1_pooled_edge_bp_capital", b)
    per_ccy = {}
    for c in CCYS:
        sub = occ[occ["ccy"] == c]
        per_ccy[c] = _pooled(sub) if len(sub) else (None, None)
        s.put(f"h1_pooled_{c}_edge_bp_notional", per_ccy[c][0])
        s.put(f"h1_pooled_{c}_edge_bp_capital", per_ccy[c][1])
    shift = occ["rank_shift"].abs()
    s.put("h1_rank_shift_median_abs", float(shift.median()) if len(occ) else None)
    s.put("h1_rank_shift_max_abs", float(shift.max()) if len(occ) else None)
    rho = float(occ["A_bp"].rank().corr(occ["B_bp"].rank())) if len(occ) > 2 else None
    s.put("h1_rho_from_cells", rho)
    checks.add("H1: ρ from h1_cells.csv equal to h1.json", rho is not None and abs(rho - h1["stat"]) < TOL,
               f"{num(rho, 6)} against {num(h1['stat'], 6)}")
    checks.add("H1: populated cells and fills equal to h1.json",
               len(occ) == h1.get("n") and int(occ["fills"].sum()) == h1.get("n_fills"),
               f"{len(occ)} cells, {di(occ['fills'].sum())} fills")
    thr = h1.get("threshold")
    checks.add("H1: verdict follows from the rule (upper bound ≥ threshold)",
               bool(h1["rejected"]) == bool(h1["hi"] >= thr), f"upper bound {num(h1['hi'], 3)}, threshold {num(thr, 1)}")
    lines = [
        "## H1 ranking (preregistered)", "",
        f"- Spearman ρ between edge in bp of notional and edge per PM2 capital over {di(h1.get('n'))} populated "
        f"cells in the PM2 window: **{ci(h1['stat'], h1['lo'], h1['hi'], 3)}** ({lvl(h1.get('level'))} interval).",
        f"- Rule: rejected if the upper bound is ≥ {num(thr, 1)}. Verdict: {verdict(h1['rejected'])}.",
        f"- Pooled over the populated cells: edge {num(a, 2)} bp of notional and {num(b, 1)} bp of PM2 capital.",
        f"- Rank shift (rank by capital minus rank by notional, rank 1 = highest edge): median |Δ| "
        f"{num(shift.median(), 1)}, largest |Δ| {di(shift.max())}.",
        f"- Bootstrap: every replication contains at least {di(h1.get('cells_present_min'))} of the "
        f"{di(h1.get('n'))} cells; {di(h1.get('n_nan_draws'))} replications without ρ.",
        f"- {di(h1.get('n_fills_k_le_0'))} fills with K_PM2 ≤ 0 stay in the sums (Addendum 4); not finite: "
        f"{di(h1.get('n_fills_nonfinite'))}.", "",
        "| Underlying | Cells | Fills | Edge bp notional | Edge bp PM2 capital | ρ per underlying (exploratory) |",
        "|---|---:|---:|---:|---:|---|"]
    for c in CCYS:
        sub = occ[occ["ccy"] == c]
        if not len(sub):
            continue
        g = _get(sens, "g_by_ccy", f"pm2_{c}") or {}
        lines.append(f"| {c} | {di(len(sub))} | {di(sub['fills'].sum())} | {num(per_ccy[c][0], 2)} | "
                     f"{num(per_ccy[c][1], 1)} | {ci(g.get('stat'), g.get('lo'), g.get('hi'), 3) if g else MISSING} |")
    lines += ["", "Largest rank shifts (negative: the cell moves up under capital):", "",
              "| Cell | Fills | Edge bp notional | Rank | Edge bp capital | Rank | Shift |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    ranked = occ.sort_values(["rank_shift", "cell"], kind="mergesort")
    pick = pd.concat([ranked.head(5), ranked.tail(5)]).drop_duplicates("cell")
    for r in pick.itertuples():
        lines.append(f"| {cell(r.cell)} | {di(r.fills)} | {num(r.A_bp, 2)} | {di(r.rank_A)} | {num(r.B_bp, 1)} | "
                     f"{di(r.rank_B)} | {num(r.rank_shift, 0, sign=True)} |")
    return lines + [""]


def h2_section(d: Dict[str, Any], s: Summary, checks: Checks) -> List[str]:
    h2 = d["h2.json"]
    for k in ("stat", "lo", "hi", "rejected", "threshold", "n", "n_sample", "n_excluded", "n_nonfinite", "n_not_ok",
              "n_days", "share_nonpositive", "first_day", "last_day", "check_stored_ratio_max_abs",
              "check_stored_ratio_nan_mismatch"):
        s.put(f"h2_{k}", h2.get(k))
    accounts = sorted(h2.get("accounts") or [], key=label_key)
    s.put("h2_n_accounts", len(accounts))
    s.put("h2_accounts", ",".join(accounts))
    for c in CCYS:
        s.put(f"h2_fills_{c}", _get(h2, "fills_by_ccy", c))
    thr = h2.get("threshold")
    checks.add("H2: verdict follows from the rule (upper bound ≥ threshold)",
               bool(h2["rejected"]) == bool(h2["hi"] >= thr), f"upper bound {num(h2['hi'], 4)}, threshold {num(thr, 1)}")
    chk = h2.get("check_stored_ratio_max_abs")
    if chk is not None:
        checks.add("H2: stored ratio equal to recomputation", float(chk) == 0 and not h2.get(
            "check_stored_ratio_nan_mismatch"), f"largest deviation {sig(chk)}")
    fills = ", ".join(f"{c} {di(_get(h2, 'fills_by_ccy', c))}" for c in CCYS if _get(h2, "fills_by_ccy", c) is not None)
    return [
        "## H2 marginal cost (preregistered)", "",
        f"- Median of ratio = (ΔK/amount)/K_PM2,Einzel over {di(h2.get('n'))} fills: "
        f"**{ci(h2['stat'], h2['lo'], h2['hi'], 4)}** ({lvl(h2.get('level'))} interval).",
        f"- Rule: rejected if the upper bound is ≥ {num(thr, 1)}. Verdict: {verdict(h2['rejected'])}.",
        f"- Share ratio ≤ 0: {pct(h2.get('share_nonpositive'), 1)}. Excluded with K_PM2,Einzel ≤ 0: "
        f"{di(h2.get('n_excluded'))} of {di(h2.get('n_sample'))} drawn fills; not finite "
        f"{di(h2.get('n_nonfinite'))}, status not ok {di(h2.get('n_not_ok'))}.",
        f"- Accounts (book at the start of the day under PM2): {', '.join(accounts)}; fills per underlying: {fills}; "
        f"{di(h2.get('n_days'))} UTC days.",
        f"- Cross-check: stored column ratio against recomputation, largest deviation {sig(chk)}.", ""]


def h3_section(d: Dict[str, Any], s: Summary, checks: Checks) -> List[str]:
    h3 = d["h3.json"]
    for k in ("stat", "lo", "hi", "rejected", "threshold", "n", "n_rows", "n_not_ok", "n_excluded", "n_not_applicable",
              "n_days", "first_day", "last_day", "days_over_63_options", "share_days_over_63_options"):
        s.put(f"h3_{k}", h3.get(k))
    st = h3.get("status_counts") or {}
    s.put("h3_n_no_options", st.get("no_options"))
    s.put("h3_n_no_snapshot", st.get("no_snapshot"))
    acc = h3.get("accounts") or {}
    s.put("h3_n_accounts", len(acc))
    for lab in LABELS:
        s.put(f"h3_days_{lab}", acc.get(lab))
    thr = h3.get("threshold")
    checks.add("H3: verdict follows from the rule (lower bound ≤ threshold)",
               bool(h3["rejected"]) == bool(h3["lo"] <= thr), f"lower bound {num(h3['lo'], 3)}, threshold {num(thr, 1)}")
    notok = ", ".join(f"{di(v)} {STATUS_NAME.get(k, k)}" for k, v in sorted(st.items()) if k != "ok") or "none"
    return [
        "## H3 netting value (preregistered)", "",
        f"- Median of K_SM/K_PM2 over {di(h3.get('n'))} maker days: **{ci(h3['stat'], h3['lo'], h3['hi'], 3)}** "
        f"({lvl(h3.get('level'))} interval).",
        f"- Rule: rejected if the lower bound is ≤ {num(thr, 1)}. Verdict: {verdict(h3['rejected'])}.",
        f"- {di(h3.get('n_rows'))} maker days in the window, not computed: {notok}; excluded with K_PM2 ≤ 0: "
        f"{di(h3.get('n_excluded'))}; {di(h3.get('n_days'))} UTC days from {fmt_day(h3.get('first_day'))} to "
        f"{fmt_day(h3.get('last_day'))}.",
        f"- On {di(h3.get('days_over_63_options'))} days ({pct(h3.get('share_days_over_63_options'), 1)}) the book "
        f"holds more than 63 options; K_SM is counterfactual there (Addendum 4).",
        f"- Maker days per account: {', '.join(f'{k} {di(v)}' for k, v in sorted(acc.items(), key=lambda kv: label_key(kv[0])))}.",
        ""]


def h4_section(d: Dict[str, Any], s: Summary, checks: Checks) -> List[str]:
    h4 = d["h4.json"]
    pl, cr, fe, pc = (h4.get("placebo") or {}), (h4.get("criteria") or {}), (h4.get("fe") or {}), (h4.get("panel_check") or {})
    for k in ("stat", "lo", "hi", "rejected", "se", "t", "p", "n", "fills", "events", "events_kept", "cell_events",
              "day_ccy", "clusters"):
        s.put(f"h4_{k}", h4.get(k))
    for k in ("n", "finite", "p95", "median", "mean", "min", "max", "share_ge_beta", "gap_days"):
        s.put(f"h4_placebo_{k}", pl.get(k))
    for k in ("beta_positive", "p_le_alpha", "beta_gt_placebo_p95"):
        s.put(f"h4_crit_{k}", cr.get(k))
    s.put("h4_fe_iterations", fe.get("iterations"))
    s.put("h4_fe_abs_diff_direct", fe.get("abs_diff_beta_direct_solve"))
    s.put("h4_panel_check_equal", pc.get("equal"))
    beta, p, p95 = h4["stat"], h4.get("p"), pl.get("p95")
    crit = {"beta_positive": beta > 0, "p_le_alpha": p is not None and p <= H4_ALPHA,
            "beta_gt_placebo_p95": p95 is not None and beta > p95}
    rule_rejected = not (crit["beta_positive"] and crit["p_le_alpha"]) or not crit["beta_gt_placebo_p95"]
    checks.add("H4: criteria and verdict follow from β, p and the placebo P95",
               all(bool(cr.get(k)) == v for k, v in crit.items()) and bool(h4["rejected"]) == rule_rejected,
               f"β {num(beta, 2)}, p {num(p, 4)}, P95 {num(p95, 2)}")
    diff = fe.get("abs_diff_beta_direct_solve")
    checks.add("H4: demeaning equal to the direct solution, panel reproduced",
               diff is not None and diff < 1e-8 and bool(pc.get("equal")),
               f"deviation {sci(diff)}, panel rebuilt identical: {yes_no(pc.get('equal'))}")
    ev = d["events.csv"]
    n_kept = int(_bool_col(ev["kept"]).sum())
    checks.add("H4: kept events in events.csv equal to h4.json", n_kept == h4.get("events_kept"),
               f"{n_kept} against {h4.get('events_kept')}")
    return [
        "## H4 price of capital (preregistered)", "",
        f"- β = **{num(beta, 2)}** bp of the index per unit of log dose; {lvl(h4.get('level'))} interval "
        f"[{num(h4.get('lo'), 2)}; {num(h4.get('hi'), 2)}] (wild cluster bootstrap with unrestricted residuals, "
        f"descriptive); cluster SE {num(h4.get('se'), 2)}, t {num(h4.get('t'), 3)}.",
        f"- One-sided wild cluster bootstrap p for β > 0: {num(p, 4)} (B = {di(h4.get('b'))}).",
        f"- Placebo: {di(pl.get('finite'))} of {di(pl.get('n'))} replications finite; 95th percentile "
        f"{num(p95, 2)}, median {num(pl.get('median'), 2)}, mean {num(pl.get('mean'), 2)}, range "
        f"{num(pl.get('min'), 2)} to {num(pl.get('max'), 2)}; share of placebo β ≥ β: {pct(pl.get('share_ge_beta'), 0)}.",
        f"- Criteria: β > 0 {yes_no(cr.get('beta_positive'))}; p ≤ {num(H4_ALPHA, 2)} {yes_no(cr.get('p_le_alpha'))}; "
        f"β above the placebo P95 {yes_no(cr.get('beta_gt_placebo_p95'))}.",
        f"- Rule: rejected if β is not positive with p ≤ {num(H4_ALPHA, 2)} or does not lie above the 95th percentile "
        f"of the placebo β. Verdict: {verdict(h4['rejected'])}.",
        f"- Size: n = {di(h4.get('n'))} rows, {di(h4.get('fills'))} fills, {di(h4.get('events'))} events with "
        f"cells ({di(h4.get('events_kept'))} kept), {di(h4.get('cell_events'))} cell-event pairs, "
        f"{di(h4.get('day_ccy'))} day-underlying groups, {di(h4.get('clusters'))} day clusters.",
        f"- Checks: demeaning in {di(fe.get('iterations'))} iterations, deviation from the direct solution "
        f"{sci(diff)}; panel rebuilt identical: {yes_no(pc.get('equal'))}.", ""]


def _variant_rows(sec_key: str, sec: dict) -> Iterable[Tuple[str, str, dict]]:
    """(summary suffix, label, verdict dict) for every variant of a sensitivity section."""
    for key in sec:
        val = sec[key]
        if not isinstance(val, dict):
            continue
        if "stat" in val:
            yield key, VARIANT_LABEL.get((sec_key, key), key), val
        elif key in GROUP_SLOTS or all(isinstance(v, dict) and "stat" in v for v in val.values()):
            for sub in sorted(val, key=label_key if key == "by_label" else str):
                yield f"{key}_{sub}", f"{GROUP_NAME.get(key, key)} {sub}", val[sub]


def _group_label(sec_key: str, key: str) -> str:
    if sec_key == "g_by_ccy" and "_" in key:
        mp, c = key.rsplit("_", 1)
        where = {"pm2": "PM2 window", "sm_all": "SM, whole period", "pm_all": "legacy PM, whole period"}
        return f"{c}, {where.get(mp, mp)}"
    return key


def sensitivity_section(d: Dict[str, Any], s: Summary, checks: Checks) -> List[str]:
    sens, h1, h2, h3 = d["sensitivity.json"], d["h1.json"], d["h2.json"], d["h3.json"]
    lines = ["## Exploratory sensitivities", "",
             "Not preregistered as a test. \"Verdict by rule\" is the verdict that the preregistered rule of the "
             "respective hypothesis would give for this variant.", ""]
    digits = {"H1": 3, "H2": 4, "H3": 3}
    for sec_key in sorted(k for k, v in sens.items() if isinstance(v, dict)):
        sec = sens[sec_key]
        # fixed slots for grouped variants, so the summary keys do not depend on the data
        for gk, slots in GROUP_SLOTS.items():
            if gk in sec and isinstance(sec[gk], dict):
                for slot in slots:
                    if slot not in sec[gk]:
                        for f in VERDICT_FIELDS:
                            s.put(f"sens_{sec_key}_{gk}_{slot}_{f}", None)
        rows = list(_variant_rows(sec_key, sec))
        if not rows:
            continue
        lines += [f"### {SECTION_TITLE.get(sec_key, sec_key)}", "",
                  f"| Variant | Quantity | Value [{lvl(h1.get('level'))} interval] | n | Verdict by rule |",
                  "|---|---|---|---:|---|"]
        for suffix, label, v in rows:
            for f in VERDICT_FIELDS:
                s.put(f"sens_{sec_key}_{suffix}_{f}", v.get(f))
            rule = str(v.get("rule", ""))
            dg = digits.get(rule, 3)
            if rule == "H1":
                what = "ρ" + (" (edge per capital and year)" if v.get("unit") else "")
            elif v.get("numerator"):
                what = f"Median {v.get('numerator')}/{v.get('denominator')}"
            else:
                what = "Median"
            if label == suffix:
                label = _group_label(sec_key, suffix)
            lines.append(f"| {label} | {what} | {ci(v.get('stat'), v.get('lo'), v.get('hi'), dg)} | "
                         f"{di(v.get('n'))} | {verdict_plain(v.get('rejected'))} |")
        lines.append("")
    same = []
    for (sec_key, key), ref in ((("a_maps", "pm2"), h1), (("d_h2", "ratio"), h2), (("e_h3", "sm_pm2"), h3)):
        v = _get(sens, sec_key, key)
        if v is not None:
            same.append(abs(float(v["stat"]) - float(ref["stat"])) < TOL)
    if same:
        checks.add("Sensitivities: base variant equal to the test", all(same), f"{sum(same)} of {len(same)} equal")
    lines += h4_sensitivity(d, s)
    return lines


def h4_sensitivity(d: Dict[str, Any], s: Summary) -> List[str]:
    sh, h4 = d["sensitivity_h4.json"], d["h4.json"]
    by = sh.get("by_ccy") or {}
    no = sh.get("no_outlier_cells") or {}
    al = sh.get("placebo_all_timelines") or {}
    for c in CCYS:
        v = by.get(c) or {}
        for k in ("beta", "lo", "hi", "p", "se", "n", "clusters", "events", "cell_events"):
            s.put(f"sens_h4_by_ccy_{c}_{k}", v.get(k))
    nh, npl = no.get("h4") or {}, no.get("placebo") or {}
    for k in ("beta", "lo", "hi", "p", "n"):
        s.put(f"sens_h4_no_outlier_{k}", nh.get(k))
    s.put("sens_h4_no_outlier_placebo_p95", npl.get("p95"))
    s.put("sens_h4_no_outlier_placebo_share_ge_beta", npl.get("share_ge_beta"))
    s.put("sens_h4_no_outlier_rejected", no.get("rejected"))
    s.put("sens_h4_no_outlier_max_abs_dose", no.get("max_abs_dose"))
    s.put("sens_h4_no_outlier_rows_dropped", no.get("rows_dropped_real_panel"))
    s.put("sens_h4_no_outlier_cells_above", len(no.get("dose_cells_above") or []))
    apl = al.get("placebo") or {}
    for k in ("p95", "median", "share_ge_beta", "n"):
        s.put(f"sens_h4_all_timelines_placebo_{k}", apl.get(k))
    s.put("sens_h4_all_timelines_rejected", al.get("rejected"))
    mt0 = sh.get("placebo_matched") or {}
    mp0 = mt0.get("placebo") or {}
    for k in ("n", "p95", "median", "share_ge_beta", "t_sd", "t_p05", "t_p95", "share_abs_t_gt_crit"):
        s.put(f"sens_h4_matched_placebo_{k}", mp0.get(k))
    for k in ("min", "median", "max"):
        s.put(f"sens_h4_matched_events_drawn_{k}", (mt0.get("events_drawn") or {}).get(k))
    s.put("sens_h4_matched_rejected", mt0.get("rejected"))
    dr0 = (sh.get("audit") or {}).get("dose_robust") or {}
    for k in ("pairs", "pairs_without_fills", "pairs_with_large_log_ratio", "fills_with_large_log_ratio",
              "pairs_median_differs", "trim_abs_log_ratio", "check_mean_max_abs_diff"):
        s.put(f"sens_h4_dose_{k}", dr0.get(k))
    for name in ("median", "trimmed"):
        v = dr0.get(name) or {}
        for k in ("beta", "se", "t", "p", "lo", "hi", "n", "rows_dropped", "cell_events"):
            s.put(f"sens_h4_dose_{name}_{k}", v.get(k))
    lines = ["### (h) H4 variants", "",
             f"| Variant | β | {lvl(h4.get('level'))} interval | p | n | Placebo P95 | Share placebo β ≥ β | "
             "Verdict by rule |",
             "|---|---:|---|---:|---:|---:|---:|---|"]
    for c in CCYS:
        v = by.get(c)
        if not v:
            continue
        lines.append(f"| only {c} ({di(v.get('events'))} events) | {num(v.get('beta'), 2)} | "
                     f"[{num(v.get('lo'), 2)}; {num(v.get('hi'), 2)}] | {num(v.get('p'), 4)} | {di(v.get('n'))} | "
                     f"{MISSING} | {MISSING} | {MISSING} |")
    if no:
        lines.append(f"| without cells with \\|d\\| > {num(no.get('max_abs_dose'), 0)} | {num(nh.get('beta'), 2)} | "
                     f"[{num(nh.get('lo'), 2)}; {num(nh.get('hi'), 2)}] | {num(nh.get('p'), 4)} | {di(nh.get('n'))} | "
                     f"{num(npl.get('p95'), 2)} | {pct(npl.get('share_ge_beta'), 0)} | {verdict_plain(no.get('rejected'))} |")
    if al:
        lines.append(f"| placebo distance to all timelines | {num(h4.get('stat'), 2)} | [{num(h4.get('lo'), 2)}; "
                     f"{num(h4.get('hi'), 2)}] | {num(h4.get('p'), 4)} | {di(h4.get('n'))} | {num(apl.get('p95'), 2)} | "
                     f"{pct(apl.get('share_ge_beta'), 0)} | {verdict_plain(al.get('rejected'))} |")
    mt = sh.get("placebo_matched") or {}
    mpl = mt.get("placebo") or {}
    if mt:
        lines.append(f"| placebos only for events with cells, windows separate | {num(h4.get('stat'), 2)} | "
                     f"[{num(h4.get('lo'), 2)}; {num(h4.get('hi'), 2)}] | {num(h4.get('p'), 4)} | {di(h4.get('n'))} | "
                     f"{num(mpl.get('p95'), 2)} | {pct(mpl.get('share_ge_beta'), 0)} | "
                     f"{verdict_plain(mt.get('rejected'))} |")
    dr = (sh.get("audit") or {}).get("dose_robust") or {}
    for name, label in (("median", "dose as the median of the log ratios"),
                        ("trimmed", f"dose without fills with \\|log ratio\\| > {num(dr.get('trim_abs_log_ratio'), 0)}")):
        v = dr.get(name)
        if v:
            lines.append(f"| {label} | {num(v.get('beta'), 2)} | [{num(v.get('lo'), 2)}; {num(v.get('hi'), 2)}] | "
                         f"{num(v.get('p'), 4)} | {di(v.get('n'))} | {MISSING} | {MISSING} | {MISSING} |")
    lines.append("")
    above = no.get("dose_cells_above") or []
    if no:
        cells = "; ".join(f"{a.get('event_id')} {a.get('cell')} (d = {num(a.get('dose'), 3)})" for a in above) or "none"
        lines += [f"- Cells with \\|d\\| > {num(no.get('max_abs_dose'), 0)}: {cells}. In the real panel "
                  f"{di(no.get('rows_dropped_real_panel'))} rows drop out; otherwise the variant acts only in the placebo panels."]
    if al:
        lines += ["- Distance to all timelines: placebo dates keep 28 days away from every parameter change of the "
                  "underlying under SM, legacy PM, the PM2 standard lib and the account libs."]
    if mt:
        ed = mt.get("events_drawn") or {}
        lines += [f"- Placebos only for events with cells in the real panel, placebo windows of an underlying without "
                  f"overlap (audit A29): {di(ed.get('min'))} to {di(ed.get('max'))} events per replication "
                  f"(median {num(ed.get('median'), 0)}); sd(t) of the placebos {num(mpl.get('t_sd'), 2)}."]
    return lines + [""]


def _refbook_row_effect(r, m: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    k, kp, f = r[f"K_{m}"], r[f"K_{m}_prev"], r.get("forward", np.nan)
    if _missing(k) or _missing(kp) or kp == 0:
        return None, None, None
    to_bp = (lambda x: 1e4 * x / f) if not _missing(f) and f else (lambda x: None)
    return float(k / kp - 1), to_bp(float(kp)), to_bp(float(k))


def events_section(d: Dict[str, Any], s: Summary, checks: Checks) -> List[str]:
    ev = d["events.csv"].copy()
    rb = d["reference_book.csv"].copy()
    ev["kept"] = _bool_col(ev["kept"])
    ev = ev.sort_values(["event_ts", "ccy"], kind="mergesort").reset_index(drop=True)
    s.put("events_total", len(ev))
    s.put("events_kept", int(ev["kept"].sum()))
    s.put("events_dropped", int((~ev["kept"]).sum()))
    panel_cells = pd.to_numeric(ev["panel_cells"], errors="coerce") if "panel_cells" in ev else pd.Series(np.nan, ev.index)
    s.put("events_with_cells", int((ev["kept"] & (panel_cells > 0)).sum()))
    for c in CCYS:
        s.put(f"events_kept_{c}", int((ev["kept"] & (ev["ccy"] == c)).sum()))
    matched = set()
    lines = ["## Reference book effects of the events", "",
             "Reference book: short straddle ATM (strike = forward) of the expiry near 30 days, 1 contract per leg, "
             "daily at 08:00 UTC; K before computes the same book in the same market state with the parameters of "
             "24 h earlier (pure parameter effect, `results/p2/reference_book.csv`). One row per event from "
             "`results/p2/events.csv`; the reference book day is the first day whose parameter state stems from the "
             "event. K in bp of the forward.", "",
             "| Event | Time | Changed structures | max. \\|dose\\| | kept | Panel cells | "
             "Reference book day | K before | K after | Change |",
             "|---|---|---|---:|---|---:|---|---:|---:|---:|"]
    for i, e in ev.iterrows():
        m = str(e["manager"])
        pts, ptsp = f"{m}_param_ts", f"{m}_param_ts_prev"
        last = e["last_ts"] if "last_ts" in ev and not _missing(e.get("last_ts")) else e["event_ts"]
        hit = pd.DataFrame()
        if pts in rb and ptsp in rb:
            hit = rb[(rb["ccy"] == e["ccy"]) & (rb[pts] >= e["event_ts"]) & (rb[pts] <= last)
                     & (rb[ptsp] < e["event_ts"])].sort_values("day", kind="mergesort")
        change = before = after = None
        rday = None
        if len(hit):
            r = hit.iloc[0]
            matched.add((m, hit.index[0]))
            change, before, after = _refbook_row_effect(r, m)
            rday = str(r["day"])
        eid = str(e["event_id"])
        s.put(f"event_{eid}_kept", bool(e["kept"]))
        s.put(f"event_{eid}_event_utc", str(e.get("event_utc")))
        s.put(f"event_{eid}_max_abs_dose", e.get("max_abs_dose"))
        s.put(f"event_{eid}_panel_cells", None if _missing(panel_cells[i]) else int(panel_cells[i]))
        s.put(f"event_{eid}_refbook_day", rday)
        s.put(f"event_{eid}_refbook_change", change)
        s.put(f"event_{eid}_refbook_log_change", None if change is None else math.log1p(change))
        s.put(f"event_{eid}_refbook_k_before_bp", before)
        s.put(f"event_{eid}_refbook_k_after_bp", after)
        kinds = ", ".join(STRUCT_NAME.get(k, k) for k in str(e.get("kinds", "")).split("+") if k)
        lines.append(f"| {eid} | {fmt_ts(int(e['event_ts']), seconds=False)} | {kinds} | {pct(e.get('max_abs_dose'), 2)} | "
                     f"{yes_no(e['kept'])} | {di(panel_cells[i])} | {fmt_day(rday)} | {num(before, 0)} | "
                     f"{num(after, 0)} | {pct(change, 2, sign=True)} |")
    lines.append("")
    # parameter effects on the reference book that no event row explains
    extra = []
    for m in MANAGERS:
        if f"K_{m}" not in rb:
            continue
        k, kp = rb[f"K_{m}"], rb[f"K_{m}_prev"]
        chg = (k / kp - 1).where(kp.notna() & k.notna() & (kp != 0))
        for idx in rb.index[chg.abs() > 1e-12]:
            if (m, idx) in matched:
                continue
            r = rb.loc[idx]
            extra.append((str(r["day"]), m, str(r["ccy"]), float(chg[idx]), r.get(f"{m}_param_ts")))
    s.put("refbook_changes_without_event", len(extra))
    if extra:
        lines += ["Parameter effects in the reference book without an event row (outside the manager window or not "
                  "in the event list):", ""]
        for day, m, c, chg, pts in sorted(extra):
            since = f", parameter state of {fmt_ts(int(pts), seconds=False)}" if not _missing(pts) else ""
            lines.append(f"- {MANAGER_NAME[m]} {c} {fmt_day(day)}: {pct(chg, 2, sign=True)}{since}.")
        lines.append("")
    # level of the reference book in bp of the forward
    lines += ["Level of the reference book (K in bp of the forward over the days in the manager window):", "",
              "| Underlying | Manager | Days | Minimum | Median | Maximum |", "|---|---|---:|---:|---:|---:|"]
    for c in CCYS:
        sub = rb[rb["ccy"] == c]
        for m in MANAGERS:
            col = f"K_{m}"
            bp = (1e4 * sub[col] / sub["forward"]).dropna() if col in sub and len(sub) else pd.Series(dtype=float)
            vals = {"days": len(bp) if len(bp) else None, "bp_min": bp.min() if len(bp) else None,
                    "bp_median": bp.median() if len(bp) else None, "bp_max": bp.max() if len(bp) else None}
            for k, v in vals.items():
                s.put(f"refbook_{c}_{m}_{k}", v)
            if len(bp):
                lines.append(f"| {c} | {MANAGER_NAME[m]} | {di(len(bp))} | {num(bp.min(), 0)} | {num(bp.median(), 0)} | "
                             f"{num(bp.max(), 0)} |")
    return lines + [""]


def oi_section(d: Dict[str, Any], s: Summary) -> List[str]:
    oi = d["manager_oi_share.csv"].copy()
    oi["month"] = oi["month"].astype(str)
    last_month = str(oi["month"].max()) if len(oi) else None
    s.put("oi_last_month", last_month)
    lines = ["## Manager shares of the options OI", "",
             "Share of `OptionAsset.totalPosition` per manager in the sum over the managers, each on the first day of "
             "the month (`results/p2/manager_oi_share.csv`).", ""]
    for c in CCYS:
        sub = oi[oi["ccy"] == c].sort_values("month")
        last = sub[sub["month"] == last_month].iloc[0] if len(sub) and (sub["month"] == last_month).any() else None
        for m in MANAGERS:
            s.put(f"oi_{c}_{m}_last", None if last is None else last.get(m))
        pos = sub[sub["pm2"] > 0] if len(sub) else sub
        first = str(pos["month"].iloc[0]) if len(pos) else None
        mx = sub.loc[sub["pm2"].idxmax()] if len(sub) and sub["pm2"].notna().any() else None
        below = None
        if len(sub) and sub["pm"].notna().any():
            ok = (sub["pm"] < 0.01).to_numpy()
            # first month from which the legacy PM stays below 1 % until the end
            for j in range(len(ok)):
                if ok[j:].all():
                    below = str(sub["month"].iloc[j])
                    break
        s.put(f"oi_{c}_pm2_first_month", first)
        s.put(f"oi_{c}_pm2_first_share", None if first is None else pos["pm2"].iloc[0])
        s.put(f"oi_{c}_pm2_max", None if mx is None else mx["pm2"])
        s.put(f"oi_{c}_pm2_max_month", None if mx is None else str(mx["month"]))
        s.put(f"oi_{c}_pm_below_1pct_from", below)
        s.put(f"oi_{c}_first_month", str(sub["month"].iloc[0]) if len(sub) else None)
        if not len(sub):
            continue
        parts = [f"data from {fmt_month(sub['month'].iloc[0])}"]
        if first:
            parts.append(f"PM2 first in {fmt_month(first)} ({pct(pos['pm2'].iloc[0], 1)})")
        if mx is not None:
            parts.append(f"at most {pct(mx['pm2'], 1)} ({fmt_month(mx['month'])})")
        if below:
            parts.append(f"legacy PM below 1 % from {fmt_month(below)}")
        if last is not None:
            parts.append(f"last ({fmt_month(last_month)}) SM {pct(last['sm'], 1)}"
                         + (f", legacy PM {pct(last['pm'], 1)}" if not _missing(last.get("pm")) else "")
                         + f", PM2 {pct(last['pm2'], 1)}")
        lines.append(f"- {c}: " + "; ".join(parts) + ".")
    present = [c for c in CCYS if (oi["ccy"] == c).any()]
    cols = [(c, m) for c in present for m in MANAGERS if not (m == "pm" and oi.loc[oi["ccy"] == c, "pm"].isna().all())]
    lines += ["", "| Month | " + " | ".join(f"{c} {MANAGER_NAME[m]}" for c, m in cols) + " |",
              "|---|" + "---:|" * len(cols)]
    for month in sorted(oi["month"].unique()):
        row = []
        for c, m in cols:
            hit = oi[(oi["ccy"] == c) & (oi["month"] == month)]
            row.append(pct(hit[m].iloc[0], 1) if len(hit) else MISSING)
        lines.append(f"| {month} | " + " | ".join(row) + " |")
    return lines + [""]


def _optional_csv(results: Path, name: str) -> Optional[pd.DataFrame]:
    p = Path(results) / name
    return pd.read_csv(p) if p.is_file() else None


def review_section(d: Dict[str, Any], s: Summary, checks: Checks, results: Path) -> List[str]:
    """Numbers of review round 1 (docs/paper2/MANUSCRIPT.md): all exploratory or descriptive."""
    sens, h3, cap = d["sensitivity.json"], d["h3.json"], d["capital_check.json"]
    lines = ["## Review round 1 (exploratory or descriptive)", ""]
    # H1: sign structure
    sign = sens.get("h1_sign") or {}
    fl = sign.get("sign_floor") or {}
    for k in ("mean", "median", "p05", "p95", "draws", "n_pos", "n_nonpos"):
        s.put(f"h1_sign_floor_{k}", fl.get(k))
    top = sign.get("top_overlap") or {}
    s.put("h1_top10_overlap", top.get("top10"))
    s.put("h1_top20_overlap", top.get("top20"))
    s.put("h1_sign_agree", sign.get("sign_agree"))
    wp, wn = sign.get("within_pos") or {}, sign.get("within_nonpos") or {}
    ws, wb, wpb = sign.get("within_sell") or {}, sign.get("within_buy") or {}, sign.get("within_pos_buy") or {}
    lines += [
        f"- H1, sign only: shuffling the ranks within the {di(fl.get('n_pos'))} cells with edge > 0 and within the "
        f"{di(fl.get('n_nonpos'))} others ({di(fl.get('draws'))} draws) gives ρ {num(fl.get('mean'), 3)} on average "
        f"(5th to 95th percentile {num(fl.get('p05'), 3)} to {num(fl.get('p95'), 3)}).",
        f"- H1 within groups: edge > 0 {num(wp.get('stat'), 3)} (n = {di(wp.get('n'))}), edge ≤ 0 "
        f"{num(wn.get('stat'), 3)} (n = {di(wn.get('n'))}), sells {num(ws.get('stat'), 3)}, buys "
        f"{num(wb.get('stat'), 3)}, buys with edge > 0 {num(wpb.get('stat'), 3)} (n = {di(wpb.get('n'))}).",
        f"- Best cells: the ten best per capital and the ten best per notional share {di(top.get('top10'))} cells, "
        f"the best 20 share {di(top.get('top20'))}; same sign in {di(sign.get('sign_agree'))} cells."]
    # H2 population
    pop = (sens.get("d_h2") or {}).get("population") or {}
    s.put("h2_population", pop.get("n"))
    s.put("h2_population_sample_equal", pop.get("sample_equals_marginal"))
    lines.append(f"- H2: population before the draw {di(pop.get('n'))} fills; the preregistered draw gives "
                 f"exactly the fills of marginal.parquet: {yes_no(pop.get('sample_equals_marginal'))}.")
    # H3: accounts above the threshold, days beyond the validated book size
    by_label = (sens.get("e_h3") or {}).get("by_label") or {}
    thr = h3.get("threshold")
    stats = [v.get("stat") for v in by_label.values() if not _missing(v.get("stat"))]
    above = sum(1 for x in stats if thr is not None and x > thr)
    s.put("h3_accounts_median_n", len(stats))
    s.put("h3_accounts_median_above_threshold", above)
    series = _optional_csv(results, "fig_h3_series.csv")
    vcsv = d["validation.csv"]
    legs_max = int(vcsv.loc[vcsv["kind"] == "book", "n_legs"].max()) if (vcsv["kind"] == "book").any() else None
    over = None
    if series is not None and legs_max is not None:
        ok = series[(series["status"].astype(str) == "ok") & np.isfinite(series["ratio_sm_pm2"].to_numpy(float))]
        over = int((ok["n_legs"] > legs_max).sum())
        s.put("h3_legs_max", int(ok["n_legs"].max()))
    s.put("h3_days_over_validated_legs", over)
    fam_counts: Dict[str, int] = {}
    if series is not None:
        ok = series[series["status"].astype(str) == "ok"]
        for lab, mgr in ok[["label", "manager"]].drop_duplicates("label").itertuples(index=False):
            fam = str(mgr).split(":", 1)[0]
            fam_counts[fam] = fam_counts.get(fam, 0) + 1
    for fam in ("SM", "PM", "PM2"):
        s.put(f"h3_accounts_{fam}", fam_counts.get(fam) if series is not None else None)
    lines.append("- H3 accounts by manager: " + ", ".join(f"{k} {v}" for k, v in sorted(fam_counts.items())) + ".")
    e = sens.get("e_h3") or {}
    ns = e.get("sm_pm2_le63_no_sm") or {}
    lines += [
        f"- H3: {above} of {len(stats)} account medians above the threshold {num(thr, 0)}; at most 63 options without "
        f"SM account {ci(ns.get('stat'), ns.get('lo'), ns.get('hi'), 3)} (n = {di(ns.get('n'))}).",
        f"- H3: {di(over)} maker days with more legs than the largest validated book ({di(legs_max)} legs)."]
    # fills outside every manager window
    outside = 0
    for c in CCYS:
        mg = _get(cap, "managers", c) or {}
        n_c = max((v.get("n") or 0) for v in mg.values()) if mg else 0
        in_c = max((v.get("n_in_window") or 0) for v in mg.values()) if mg else 0
        outside += int(n_c - in_c)
    s.put("fills_outside_every_window", outside)
    lines.append(f"- Fills outside every manager window (without capital): {di(outside)}.")
    # validation: blocks drawn per cell of single contracts
    cells = (d["validation_summary.json"].get("cells") or [])
    blocks = [int(c.get("n", 0)) + int(c.get("n_missing", 0)) for c in cells
              if c.get("kind") == "single" and c.get("is_initial")]
    s.put("validation_single_blocks_per_cell", max(blocks) if blocks else None)
    s.put("validation_single_blocks_per_cell_min", min(blocks) if blocks else None)
    # probes of the off-chain discount: expiries of the box-spread measurement quoted in Section 2
    box_path = Path(results) / "semantics" / "box_discount.json"
    box = json.loads(box_path.read_text()) if box_path.is_file() else {}
    first = next((v for k, v in sorted(box.items()) if k.startswith("box_") and isinstance(v, list)), None)
    s.put("semantics_box_expiries", len(first) if first is not None else None)
    # API snapshot (present-day sensitivity, off-chain against chain semantics)
    api = _optional_csv(results, "api_snapshot.csv")
    if api is not None and len(api):
        ok = api[api["status"].astype(str) == "ok"]
        s.put("api_n", len(ok))
        s.put("api_n_cells", len(api))
        ts = pd.to_numeric(ok["ts"], errors="coerce")
        s.put("api_day", pd.Timestamp(int(ts.min()), unit="ms", tz="UTC").strftime("%Y-%m-%d") if len(ts) else None)
        for m in ("sm", "pm2"):
            r = ok[f"rel_diff_{m}"].abs().astype(float)
            s.put(f"api_{m}_median_abs_rel", float(r.median()) if len(r) else None)
            s.put(f"api_{m}_p95_abs_rel", float(r.quantile(0.95)) if len(r) else None)
            s.put(f"api_{m}_max_abs_rel", float(r.max()) if len(r) else None)
        r = ok.assign(ar=ok["rel_diff_pm2"].abs().astype(float))
        s.put("api_pm2_max_tenor_bucket", str(r.loc[r["ar"].idxmax(), "tenor_bucket"]) if len(r) else None)
        med = r.groupby("tenor_bucket")["ar"].median()
        for b, key in ((">90d", "gt90d"), ("<=2d", "le2d")):
            s.put(f"api_pm2_median_abs_rel_{key}", float(med[b]) if b in med else None)
        lines.append(f"- API against chain semantics ({di(len(ok))} single contracts on {fmt_day(s['api_day'])}): PM2 "
                     f"median |rel| {pct(s['api_pm2_median_abs_rel'], 2)}, p95 {pct(s['api_pm2_p95_abs_rel'], 2)}, "
                     f"maximum {pct(s['api_pm2_max_abs_rel'], 2)} (tenor {s['api_pm2_max_tenor_bucket']}); SM "
                     f"median {pct(s['api_sm_median_abs_rel'], 2)}, maximum {pct(s['api_sm_max_abs_rel'], 2)}.")
    # H4 readings and side splits
    rv = (d["sensitivity_h4.json"].get("review") or {})
    rd = rv.get("readings") or {}
    for k in ("y_mean", "y_median", "y_mean_fills", "y_median_fills", "ten_pct_dose", "ten_pct_change_beta",
              "ten_pct_change_lo", "ten_pct_change_hi"):
        s.put(f"h4_review_{k}", rd.get(k))
    for name in ("sells_only", "buys_only", "oi_weighted"):
        v = rv.get(name) or {}
        for k in ("beta", "se", "p", "lo", "hi", "n", "cell_events"):
            s.put(f"h4_review_{name}_{k}", v.get(k))
    ow = rv.get("oi_weighted") or {}
    s.put("h4_review_oi_share_min", ow.get("share_min"))
    s.put("h4_review_oi_share_max", ow.get("share_max"))
    so = rv.get("sells_only") or {}
    lines += [
        f"- H4 level: half spread in the panel {num(rd.get('y_mean'), 2)} bp of the index on average (median "
        f"{num(rd.get('y_median'), 2)}); capital ten per cent cheaper (dose {num(rd.get('ten_pct_dose'), 3)}): "
        f"change of the half spread {num(rd.get('ten_pct_change_beta'), 2, sign=True)} bp, interval "
        f"{num(rd.get('ten_pct_change_lo'), 2, sign=True)} to {num(rd.get('ten_pct_change_hi'), 2, sign=True)} bp.",
        f"- H4 only sell cells: β {num(so.get('beta'), 2)}, p {num(so.get('p'), 4)}; OI-weighted dose "
        f"(share {pct(ow.get('share_min'), 1)} to {pct(ow.get('share_max'), 1)}): β {num(ow.get('beta'), 2)}, "
        f"p {num(ow.get('p'), 4)}.", ""]
    return lines


SIGN_GROUPS = ("within_pos", "within_nonpos", "within_pos_sell", "within_pos_buy")
H1_INTERVAL_KEYS = ("mean_draw", "median_draw", "share_ge_stat", "z0", "basic_lo", "basic_hi", "bc_lo", "bc_hi")
H4_CAL_KEYS = ("n", "t_sd", "t_mad_sd", "t_mean", "t_median", "t_p05", "t_p95", "crit", "share_t_gt_crit",
               "share_abs_t_gt_crit", "beta_sd", "se_median", "p_placebo_t", "lo", "hi", "sd_scaled_lo",
               "sd_scaled_hi", "y_mean", "ten_pct_change_lo", "ten_pct_change_hi", "ten_pct_change_sd_scaled_lo",
               "ten_pct_change_sd_scaled_hi", "ten_pct_narrowing_share", "ten_pct_narrowing_share_sd_scaled",
               "ten_pct_narrowing_share_descriptive")
H4_COMP_KEYS = ("events_kept", "events_with_cells_real", "events_with_cells_placebo_min",
                "events_with_cells_placebo_max", "rows_real", "rows_per_fill_real", "rows_placebo_median",
                "clusters_real", "clusters_placebo_median", "overlap_pairs_real", "overlap_pairs_placebo_mean",
                "same_day_draws_placebo_mean")


def _span(lo, hi) -> str:
    """'8 to 10', or 'always 14' when both ends are equal."""
    return f"always {di(lo)}" if not _missing(lo) and lo == hi else f"{di(lo)} to {di(hi)}"


def audit_section(d: Dict[str, Any], s: Summary) -> List[str]:
    """Numbers of the audit (docs/paper2/AUDIT.md, A04, A05, A28 to A30): all exploratory or descriptive; no
    registered number changes."""
    sens, sh, h1, h4 = d["sensitivity.json"], d["sensitivity_h4.json"], d["h1.json"], d["h4.json"]
    sign = sens.get("h1_sign") or {}
    for g in SIGN_GROUPS:
        v = sign.get(g) or {}
        s.put(f"h1_sign_{g}_switch_share_mean", v.get("switch_share_mean"))
        s.put(f"h1_sign_{g}_n_rep_median", v.get("n_rep_median"))
        s.put(f"h1_sign_{g}_per_replicate", (v.get("selection") == "per replicate") if v else None)
    hi_ = sens.get("h1_interval") or {}
    for k in H1_INTERVAL_KEYS:
        s.put(f"h1_interval_{k}", hi_.get(k))
    au = sh.get("audit") or {}
    cal, comp, dr = au.get("placebo_calibration") or {}, au.get("placebo_composition") or {}, au.get("dose_robust") or {}
    for k in H4_CAL_KEYS:
        s.put(f"h4_cal_{k}", cal.get(k))
    for k in H4_COMP_KEYS:
        s.put(f"h4_comp_{k}", comp.get(k))
    without = comp.get("events_without_cells_real")
    s.put("h4_comp_events_without_cells_real", "; ".join(map(str, without)) if without is not None else None)
    s.put("h4_comp_events_without_cells_real_n", len(without) if without is not None else None)
    lines = ["## Audit (exploratory)", "",
             "Exploratory or descriptive (docs/paper2/AUDIT.md); no registered verdict changes.", ""]
    wp, wn = sign.get("within_pos") or {}, sign.get("within_nonpos") or {}
    wps, wpb = sign.get("within_pos_sell") or {}, sign.get("within_pos_buy") or {}
    if wp:
        lines.append(
            f"- H1 in sign groups (A04, selection anew in each replication: every replication chooses the cells by its "
            f"own edge): edge > 0 {ci(wp.get('stat'), wp.get('lo'), wp.get('hi'), 3)}, edge ≤ 0 "
            f"{ci(wn.get('stat'), wn.get('lo'), wn.get('hi'), 3)}, sells with edge > 0 "
            f"{ci(wps.get('stat'), wps.get('lo'), wps.get('hi'), 3)}, buys with edge > 0 "
            f"{ci(wpb.get('stat'), wpb.get('lo'), wpb.get('hi'), 3)}; on average "
            f"{pct(wp.get('switch_share_mean'), 1)} (edge > 0) and {pct(wn.get('switch_share_mean'), 1)} (edge ≤ 0) "
            f"of the cells leave their group per replication. Groups by side stay fixed.")
    if hi_:
        lines.append(
            f"- H1 interval (A28): {pct(hi_.get('share_ge_stat'), 1)} of the {di(h1.get('b'))} draws lie on or "
            f"above the estimate {num(h1.get('stat'), 4)} (mean {num(hi_.get('mean_draw'), 4)}, median "
            f"{num(hi_.get('median_draw'), 4)}); the percentile interval [{num(h1.get('lo'), 3)}; {num(h1.get('hi'), 3)}] "
            f"is not centred. Reflected [{num(hi_.get('basic_lo'), 3)}; {num(hi_.get('basic_hi'), 3)}], "
            f"bias-corrected [{num(hi_.get('bc_lo'), 3)}; {num(hi_.get('bc_hi'), 3)}].")
    if cal:
        lines += [
            f"- H4, placebo t (A05): sd(t) {num(cal.get('t_sd'), 2)} (MAD sd {num(cal.get('t_mad_sd'), 2)}), 5th/95th "
            f"percentile {num(cal.get('t_p05'), 2)}/{num(cal.get('t_p95'), 2)}; share t > {num(cal.get('crit'), 3)} "
            f"{pct(cal.get('share_t_gt_crit'), 0)}, |t| > {num(cal.get('crit'), 3)} {pct(cal.get('share_abs_t_gt_crit'), 0)}; "
            f"sd of the placebo β {num(cal.get('beta_sd'), 1)} at a median SE of {num(cal.get('se_median'), 1)}.",
            f"- H4, range for β calibrated to the placebo t: [{num(cal.get('lo'), 1)}; {num(cal.get('hi'), 1)}] "
            f"(SE times sd(t): [{num(cal.get('sd_scaled_lo'), 1)}; {num(cal.get('sd_scaled_hi'), 1)}]); p against the "
            f"placebo t {num(cal.get('p_placebo_t'), 2)}. Capital ten per cent cheaper: "
            f"{num(cal.get('ten_pct_change_lo'), 2, sign=True)} to {num(cal.get('ten_pct_change_hi'), 2, sign=True)} bp "
            f"(SE times sd(t): {num(cal.get('ten_pct_change_sd_scaled_lo'), 2, sign=True)} to "
            f"{num(cal.get('ten_pct_change_sd_scaled_hi'), 2, sign=True)} bp); largest narrowing in the range "
            f"{pct(cal.get('ten_pct_narrowing_share'), 0)} of the mean half spread {num(cal.get('y_mean'), 2)} bp "
            f"(descriptive interval: {pct(cal.get('ten_pct_narrowing_share_descriptive'), 0)}; SE times sd(t): "
            f"{pct(cal.get('ten_pct_narrowing_share_sd_scaled'), 0)})."]
    if comp:
        ev_span = _span(comp.get("events_with_cells_placebo_min"), comp.get("events_with_cells_placebo_max"))
        lines.append(
            f"- H4, construction of the placebo panels (A29): {ev_span} events with cells per replication, in the "
            f"real panel {di(comp.get('events_with_cells_real'))} of {di(comp.get('events_kept'))} (without cells: "
            f"{'; '.join(map(str, without or [])) or 'none'}); rows at the median {di(comp.get('rows_placebo_median'))} "
            f"against {di(comp.get('rows_real'))} ({num(comp.get('rows_per_fill_real'), 2)} per fill), day clusters at "
            f"the median {di(comp.get('clusters_placebo_median'))} against {di(comp.get('clusters_real'))}; pairs of "
            f"overlapping windows of one underlying per replication on average "
            f"{num(comp.get('overlap_pairs_placebo_mean'), 1)} against {di(comp.get('overlap_pairs_real'))} in the real "
            f"panel, days drawn twice on average {num(comp.get('same_day_draws_placebo_mean'), 2)}.")
    if dr:
        dm, dt_ = dr.get("median") or {}, dr.get("trimmed") or {}
        lines.append(
            f"- H4, dose (A30): {di(dr.get('pairs_with_large_log_ratio'))} of {di(dr.get('pairs'))} "
            f"cell-event pairs contain fills with |log ratio| > {num(dr.get('trim_abs_log_ratio'), 0)} "
            f"({di(dr.get('fills_with_large_log_ratio'))} fills), in {di(dr.get('pairs_median_differs'))} pairs the "
            f"median departs from the mean by more than {num(dr.get('median_diff', 0.05), 2)}. β with the median dose "
            f"{num(dm.get('beta'), 2)} (p {num(dm.get('p'), 4)}), without these fills {num(dt_.get('beta'), 2)} "
            f"(p {num(dt_.get('p'), 4)}); registered {num(h4.get('stat'), 2)}.")
    return lines + [""]


def checks_section(checks: Checks, s: Summary) -> List[str]:
    failed = sum(1 for _, ok, _ in checks if not ok)
    s.put("checks_n", len(checks))
    s.put("checks_failed", failed)
    s.put("checks_ok", failed == 0)
    lines = ["## Consistency checks", "",
             f"{len(checks) - failed} of {len(checks)} checks met. The checks recompute the verdicts from the numbers "
             f"and rules and reconcile the files with one another.", ""]
    for name, ok, detail in checks:
        lines.append(f"- {name}: {'met' if ok else '**violated**'} ({detail}).")
    return lines + [""]


def limits_section(d: Dict[str, Any], cut: dict) -> List[str]:
    h1, h2, h3, h4 = d["h1.json"], d["h2.json"], d["h3.json"], d["h4.json"]
    cal = (d["sensitivity_h4.json"].get("audit") or {}).get("placebo_calibration") or {}
    lines = ["## Limitations of these numbers", ""]
    if cut["is_pilot"]:
        lines.append(f"- Pilot state: the sample ends at {fmt_ts(cut['end'])}, before the preregistered end "
                     f"({fmt_ts(cut['prereg_end_ts'], seconds=False)}). The numbers of the manuscript come from the "
                     f"final data run.")
    lines += [
        f"- H3: on {pct(h3.get('share_days_over_63_options'), 1)} of the maker days the book holds more options than "
        f"an SM account on v2 can hold; K_SM is counterfactual there.",
        f"- H1: {di(h1.get('n_fills_k_le_0'))} fills with K_PM2 ≤ 0 (RFQ legs priced far from the mark) stay in "
        f"the sums.",
        f"- H2 rests on {len(h2.get('accounts') or [])} accounts under PM2; the distribution per account is under (d).",
        f"- H4: the interval for β is descriptive and conditional on the event dates; the verdict follows from the "
        f"one-sided p and the placebo P95. {di(h4.get('clusters'))} day clusters, {di(h4.get('events'))} "
        f"events with cells." + (f" At placebo dates t scatters with sd {num(cal.get('t_sd'), 2)} instead of 1; the "
                                 f"range calibrated to the placebo t is under Audit." if cal.get("t_sd") else ""),
        "- Capital per fill is the capital of an empty book holding exactly this contract (single contract); "
        "non-USDC collateral stays outside K."]
    return lines + [""]


# ---------------------------------------------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------------------------------------------

def build(results: Path = RESULTS, now: Optional[dt.datetime] = None, prereg_end_ts: Optional[int] = PREREG_END_TS,
          summary_path: Optional[Path] = None) -> Tuple[str, Dict[str, Any]]:
    """Return (markdown, flat summary) for the results directory."""
    results = Path(results)
    d = load(results)
    now = now or dt.datetime.now(dt.timezone.utc)
    summary_path = Path(summary_path) if summary_path is not None else results / SUMMARY_NAME
    s, checks = Summary(), Checks()
    s.put("generated_by", "scripts/p2_numbers.py")
    cut = cutoff(d, s, checks, prereg_end_ts)
    head = header(d, s, cut, results, summary_path, now, checks)
    body = (sample_section(d, s, checks) + validation_section(d, s, checks) + h1_section(d, s, checks)
            + h2_section(d, s, checks) + h3_section(d, s, checks) + h4_section(d, s, checks)
            + sensitivity_section(d, s, checks) + events_section(d, s, checks) + oi_section(d, s)
            + review_section(d, s, checks, results) + audit_section(d, s))
    tail = checks_section(checks, s) + limits_section(d, cut)
    md = "\n".join(head + body + tail).rstrip() + "\n"
    return md, dict(sorted(s.items()))


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 scripts/p2_numbers.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", type=Path, default=RESULTS, help="results directory (default results/p2)")
    ap.add_argument("--out", type=Path, default=OUT, help="markdown output (default docs/paper2/NUMBERS.md)")
    ap.add_argument("--summary", type=Path, default=None, help="summary output (default <results>/summary.json)")
    ap.add_argument("--quiet", action="store_true", help="do not print the sheet")
    args = ap.parse_args(argv)
    summary_path = args.summary or (args.results / SUMMARY_NAME)
    md, summary = build(args.results, summary_path=summary_path)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(md, encoding="utf-8")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
                            encoding="utf-8")
    if not args.quiet:
        print(md)
    print(f"wrote {args.out} and {summary_path} ({len(summary)} keys, checks failed: {summary['checks_failed']})",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
