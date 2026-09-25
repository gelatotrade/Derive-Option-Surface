"""Write docs/paper2/ZAHLENBLATT.md and results/p2/summary.json from results/p2.

The number sheet is the single source of numbers for the Paper 2 manuscript. Run from anywhere after
`p2 infer` and the H4 run (`inference_p2_h4 run`):

    python3 scripts/p2_zahlenblatt.py [--results results/p2] [--out docs/paper2/ZAHLENBLATT.md]
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
OUT = REPO / "docs" / "paper2" / "ZAHLENBLATT.md"
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

MANAGER_DE = {"sm": "SM", "pm": "Legacy-PM", "pm2": "PM2"}
KIND_DE = {"single": "Einzelkontrakt", "book": "Buch"}
STRUCT_DE = {"BasisContingencyParameters": "Basis", "OtherContingencyParameters": "Kontingenzen",
             "VolShockParameters": "Vol-Schock", "MarginParameters": "Margin", "SkewShockParameters": "Skew",
             "scenarios": "Szenarien", "CollateralParameters": "Collateral", "maxExpiries": "maxExpiries"}
SECTION_DE = {"a_maps": "(a) Karten unter anderen Managern", "b_mm": "(b) MM statt IM",
              "c_p1_net_edge": "(c) Netto-Edge in der Form von Paper 1 (Gebühr und Rabatt ungeteilt)",
              "d_h2": "(d) H2-Varianten", "e_h3": "(e) H3-Varianten", "f_time": "(f) Zeitnormierung",
              "g_by_ccy": "(g) Werte je Basiswert",
              "h1_sign": "(h) Vorzeichenstruktur von H1 (Review-Runde 1)"}
VARIANT_DE = {
    ("a_maps", "pm2"): "PM2, PM2-Fenster (gleich Test H1)",
    ("a_maps", "sm_all"): "SM, ganzer Zeitraum",
    ("a_maps", "pm_all"): "Legacy-PM, ganzer Zeitraum",
    ("a_maps", "sm_pm2_window"): "SM auf den Fills des PM2-Fensters",
    ("a_maps", "pm_pm2_window"): "Legacy-PM auf den Fills des PM2-Fensters",
    ("b_mm", "h1_pm2_mm"): "H1 mit MM",
    ("b_mm", "h1_sm_all_mm"): "Karte SM, ganzer Zeitraum, mit MM",
    ("b_mm", "h2_ratio_mm"): "H2 mit MM",
    ("b_mm", "h3_mm"): "H3 mit MM",
    ("c_p1_net_edge", "h1_pm2"): "H1 mit Netto-Edge wie Paper 1",
    ("d_h2", "ratio"): "ratio (gleich Test H2)",
    ("d_h2", "ratio_unit"): "nächster einzelner Kontrakt (ratio_unit)",
    ("d_h2", "ratio_tape"): "Buch aus dem Tape",
    ("d_h2", "ratio_mm"): "MM",
    ("e_h3", "sm_pm2"): "K_SM/K_PM2 (gleich Test H3)",
    ("e_h3", "sm_pm2_mm"): "K_SM/K_PM2 mit MM",
    ("e_h3", "sm_pm_be"): "K_SM/K_PM, BTC- und ETH-Beine",
    ("e_h3", "pm_pm2_be"): "K_PM/K_PM2, BTC- und ETH-Beine",
    ("e_h3", "sm_pm2_be"): "K_SM/K_PM2, BTC- und ETH-Beine",
    ("e_h3", "sm_pm2_le63"): "Tage mit höchstens 63 Optionen",
    ("e_h3", "sm_pm2_gt63"): "Tage mit mehr als 63 Optionen",
    ("f_time", "to_expiry"): "bis zum Verfall, annualisiert",
    ("f_time", "holding"): "empirische Haltedauer",
    ("f_time", "holding_excl_transfer"): "Haltedauer ohne Transfers",
    ("e_h3", "sm_pm2_le63_no_sm"): "Tage mit höchstens 63 Optionen ohne SM-Konto",
    ("h1_sign", "within_pos"): "nur Zellen mit Edge > 0",
    ("h1_sign", "within_nonpos"): "nur Zellen mit Edge ≤ 0",
    ("h1_sign", "within_sell"): "nur Maker-Verkäufe",
    ("h1_sign", "within_buy"): "nur Maker-Käufe",
    ("h1_sign", "within_pos_sell"): "Maker-Verkäufe mit Edge > 0",
    ("h1_sign", "within_pos_buy"): "Maker-Käufe mit Edge > 0",
}
GROUP_DE = {"by_label": "Konto", "by_ccy": "Basiswert", "by_regime": "Regime",
            "by_account_manager": "Manager des Kontos"}
STATUS_DE = {"no_options": "ohne Optionen", "no_snapshot": "ohne Snapshot"}
REGIMES = ("R1", "R2", "R3", "R4")                   # parameter regimes of the figures (ABBILDUNGSWAHL 6.6)
GROUP_SLOTS = {"by_label": LABELS, "by_ccy": CCYS, "by_regime": REGIMES, "by_account_manager": ("SM", "PM", "PM2")}
VERDICT_FIELDS = ("stat", "lo", "hi", "rejected", "n")

NNBSP = " "   # narrow no-break space as thousands separator (as in the Paper 1 sheet)
MINUS = "−"
SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")

try:  # the preregistered end of the sample, only used to say whether these are pilot numbers
    sys.path.insert(0, str(REPO))
    from derive_surface.p2events import SAMPLE_END_TS as PREREG_END_TS  # noqa: E402
except Exception:  # pragma: no cover - the sheet still works without the package
    PREREG_END_TS = None


# ---------------------------------------------------------------------------------------------------------------
# formatting (German)
# ---------------------------------------------------------------------------------------------------------------

def _missing(x) -> bool:
    if x is None:
        return True
    try:
        return not math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def de(x, digits: int = 2, sign: bool = False) -> str:
    """Decimal comma, narrow no-break space for thousands, typographic minus."""
    if _missing(x):
        return "–"
    v = round(float(x), digits)
    body = f"{abs(v):,.{digits}f}".replace(",", NNBSP).replace(".", ",")
    if v < 0:
        return MINUS + body
    return ("+" + body) if (sign and v > 0) else body


def di(x) -> str:
    if _missing(x):
        return "–"
    return de(int(round(float(x))), 0)


def sig(x, n: int = 2) -> str:
    """n significant digits, e.g. 0.00032617 -> 0,00033."""
    if _missing(x):
        return "–"
    if float(x) == 0:
        return "0"
    digits = max(0, n - 1 - int(math.floor(math.log10(abs(float(x))))))
    return de(x, digits)


def sci(x, digits: int = 1) -> str:
    """8.7e-10 -> 8,7·10⁻¹⁰."""
    if _missing(x):
        return "–"
    if float(x) == 0:
        return "0"
    mant, exp = f"{float(x):.{digits}e}".split("e")
    mant = mant.replace("-", MINUS).replace(".", ",")
    return f"{mant}·10{str(int(exp)).translate(SUPERSCRIPT)}"


def pct(x, digits: int = 1, sign: bool = False) -> str:
    if _missing(x):
        return "–"
    return de(100 * float(x), digits, sign) + " %"


def day_de(x) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "–"
    return pd.Timestamp(str(x)).strftime("%d.%m.%Y")


def ts_de(x, seconds: bool = True) -> str:
    if x is None:
        return "–"
    t = pd.Timestamp(x, unit="s", tz="UTC") if isinstance(x, (int, float, np.integer, np.floating)) else pd.Timestamp(x)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    return t.tz_convert("UTC").strftime("%d.%m.%Y %H:%M:%S" if seconds else "%d.%m.%Y %H:%M") + " UTC"


def month_de(m) -> str:
    return "–" if m is None else f"{str(m)[5:7]}.{str(m)[:4]}"


def lvl(level) -> str:
    """0.9 -> 90-% (as in "90-%-Intervall")."""
    return "–" if _missing(level) else f"{de(100 * float(level), 0)}-%"


def cell(name) -> str:
    """Cell names contain '|'; escape them inside markdown tables."""
    return str(name).replace("|", "\\|")


def ci(stat, lo, hi, digits: int) -> str:
    return f"{de(stat, digits)} [{de(lo, digits)}; {de(hi, digits)}]"


def verdict(rejected) -> str:
    if rejected is None:
        return "beschreibend"
    return "**abgelehnt**" if bool(rejected) else "nicht abgelehnt"


def verdict_plain(rejected) -> str:
    if rejected is None:
        return "beschreibend"
    return "abgelehnt" if bool(rejected) else "nicht abgelehnt"


def yes_no(x) -> str:
    return "ja" if bool(x) else "nein"


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
            "Referenzbuch": str(rb["day"].max()) if len(rb) else None}
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
    detail = (f"letzter Tag von H1, H3 und Referenzbuch gleich dem Tag des letzten Fills ({day_de(cut_day)}), "
              f"H2 endet am {day_de(h2_last)}")
    if not ok:
        detail = ("letzte Tage abweichend: " + ", ".join(f"{k} {day_de(v)}" for k, v in days.items())
                  + f", H2 {day_de(h2_last)}, letzter Fill {day_de(cut_day)}")
    checks.add("Stichtag einheitlich", ok, detail)
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
    checks.add("B, Seed und Niveau in allen Dateien gleich", same,
               f"B = {di(b)}, Seed {seed}, Niveau {pct(level, 0)}" if same else
               "; ".join(f"{k}: B {v[0]}, Seed {v[1]}, Niveau {v[2]}" for k, v in found.items()))
    if cut["end"] is not None:
        stand = f"Stichprobe vom {ts_de(cut['start'], seconds=False)} bis zum letzten Fill am {ts_de(cut['end'])}"
    else:
        stand = f"Stichprobe bis {day_de(cut['day'])} (letzter Tag der Ergebnisdateien)"
    if cut["is_pilot"] is True:
        stand += (f". **Pilotstand:** Die Stichprobe endet vor dem präregistrierten Ende "
                  f"({ts_de(cut['prereg_end_ts'], seconds=False)}); die Zahlen des Manuskripts entstehen mit dem "
                  f"Enddatenlauf.")
    elif cut["is_pilot"] is False:
        stand += f". Enddaten: Die Stichprobe reicht bis zum präregistrierten Ende ({ts_de(cut['prereg_end_ts'], seconds=False)})."
    else:
        stand += "."
    return [
        "# Zahlenblatt Paper 2", "",
        f"Erzeugt {now.astimezone(dt.timezone.utc):%Y-%m-%d %H:%M} UTC aus `{_display(results)}` mit "
        f"`scripts/p2_zahlenblatt.py`. Alle Kopfzahlen maschinenlesbar in `{_display(summary_path)}` "
        f"(flach, Schlüssel stabil).", "",
        f"- **Datenstand:** {stand} Stichtag {day_de(cut['day'])}.",
        f"- **Inferenz:** B = {di(b)}, Seed {seed}, {lvl(level)}-Perzentilintervalle aus einem Cluster-Bootstrap "
        f"über UTC-Tage (H1 bis H3, Nachtrag 3). H4: Wild-Cluster-Bootstrap mit Rademacher-Gewichten und "
        f"restringierten Residuen, Cluster UTC-Tag, einseitiges p für β > 0, 100 Placebo-Termine.",
        "- **Messung:** Kapital unter IM (MM als Sensitivität), Netto-Edge je Kontrakt nach Nachtrag 2: "
        "NE = MO_30min − (Gebühr − Rabatt)/Menge − Hedge; Edge eines Fills = NE·Menge. Konten nur als Labels "
        "(M1 bis M10).", ""]


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
    checks.add("Fills je Basiswert ergeben die Stichprobe",
               total == sum(v for v in by_ccy.values() if v is not None),
               f"{' + '.join(di(by_ccy[c]) for c in CCYS)} = {di(total)}")
    checks.add("PM2-Fenster: Kapitaldatei und H1 zählen gleich", win_total == h1.get("n_fills_window"),
               f"{di(win_total)} gegen {di(h1.get('n_fills_window'))}")

    n_events, n_kept = len(ev), int(_bool_col(ev["kept"]).sum())
    with_cells = int((_bool_col(ev["kept"]) & (pd.to_numeric(ev.get("panel_cells", 0), errors="coerce") > 0)).sum())
    ccy_list = lambda m: ", ".join(f"{c} {di(m.get(c))}" for c in CCYS if m.get(c) is not None)  # noqa: E731
    starts = ", ".join(f"{c} {ts_de(_get(h1, 'window_start_utc', c), seconds=False)}" for c in CCYS
                       if _get(h1, "window_start_utc", c))
    status = {k: v for k, v in (h3.get("status_counts") or {}).items() if k != "ok"}
    status_txt = ", ".join(f"{di(v)} {STATUS_DE.get(k, k)}" for k, v in sorted(status.items())) or "keine"
    return [
        "## Stichprobe", "",
        f"- Fills der Stichprobe von Paper 1: {di(total)} ({ccy_list(by_ccy)}).",
        f"- PM2-Fenster ab {starts}: {di(win_total)} Fills ({ccy_list(win)}).",
        f"- Fills mit Kapital je Kontrakt ≤ 0 unter IM: SM {di(kle0['sm'])}, Legacy-PM {di(kle0['pm'])}, "
        f"PM2 {di(kle0['pm2'])} (nichts ausgeschlossen; Ausschlüsse nur nach den Regeln von H2 und H3).",
        f"- H1: {di(h1.get('n'))} von {di(h1.get('n_cells_any'))} Zellen besetzt (mindestens "
        f"{di(h1.get('min_fills'))} Fills; {ccy_list(h1.get('cells_by_ccy') or {})}), {di(h1.get('n_fills'))} Fills "
        f"in besetzten Zellen, {di(h1.get('n_days'))} UTC-Tage vom {day_de(h1.get('first_day'))} bis "
        f"{day_de(h1.get('last_day'))}.",
        f"- H2: Stichprobe von {di(h2.get('n_sample'))} Fills der Konten "
        f"{', '.join(sorted(h2.get('accounts') or [], key=label_key))} ({ccy_list(h2.get('fills_by_ccy') or {})}), "
        f"n = {di(h2.get('n'))} nach Ausschluss, {di(h2.get('n_days'))} UTC-Tage vom {day_de(h2.get('first_day'))} bis "
        f"{day_de(h2.get('last_day'))}.",
        f"- H3: {di(h3.get('n_rows'))} Maker-Tage im Fenster, davon {di(h3.get('n'))} gerechnet (nicht gerechnet: "
        f"{status_txt}), {di(h3.get('n_days'))} UTC-Tage vom {day_de(h3.get('first_day'))} bis "
        f"{day_de(h3.get('last_day'))}.",
        f"- H4: {di(n_events)} Ereignisse, {di(n_kept)} behalten, davon {di(with_cells)} mit Panel-Zellen; Panel "
        f"{di(h4.get('n'))} Zeilen aus {di(h4.get('fills'))} Fills, {di(h4.get('cell_events'))} "
        f"Zell-Ereignis-Paare, {di(h4.get('clusters'))} Tages-Cluster.", ""]


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
    checks.add("Validierung: alle Zellen unter der Schwelle", passed, f"{n_pass} von {len(cells)} Zellen")
    si, bi = stats[("single", "")], stats[("book", "")]
    sm, bm = stats[("single", "_mm")], stats[("book", "_mm")]
    lines = [
        "## Validierung des Nachbaus gegen eth_call", "",
        f"- Schwelle der Präregistrierung je Basiswert, Manager und Art: Median |rel| < {pct(thr.get('median'), 1)}, "
        f"95. Perzentil < {pct(thr.get('p95'), 0)}. Ergebnis: {n_pass} von {len(cells)} Zellen (IM und MM) "
        f"erfüllt, {'**bestanden**' if passed else '**nicht bestanden**'}.",
        f"- {di(vs.get('n_cases'))} Fälle an Blöcken vom {day_de(ts_day(ts.min()))} bis {day_de(ts_day(ts.max()))}; "
        f"{di(reverts)} Fall ohne Chain-Antwort (Revert), nicht vergleichbar.",
        f"- Einzelkontrakte unter IM: n = {di(si['n'])}, Median |rel| {sci(si['median_rel'])}, p95 "
        f"{sci(si['p95_rel'])}, Maximum {sci(si['max_rel'])}; grösste absolute Abweichung "
        f"{sig(si['max_abs_usd'])} USD.",
        f"- Bücher unter IM: n = {di(bi['n'])} ({di(books['n_legs'].min() if len(books) else None)} bis "
        f"{di(books['n_legs'].max() if len(books) else None)} Beine), Median |rel| {sci(bi['median_rel'])}, p95 "
        f"{sci(bi['p95_rel'])}, Maximum {sci(bi['max_rel'])}; grösste absolute Abweichung "
        f"{sig(bi['max_abs_usd'])} USD.",
        f"- MM (Sensitivität): Einzelkontrakte Median {sci(sm['median_rel'])}, p95 {sci(sm['p95_rel'])}; Bücher "
        f"Median {sci(bm['median_rel'])}, p95 {sci(bm['p95_rel'])}.",
        f"- Szenario-Weg gegen direkten Aufruf: {di(psc.get('n'))} Bücher, bitgleich: {yes_no(psc.get('all_equal'))}.",
        "", "| Art | Basiswert | Manager | n | fehlend | Median \\|rel\\| | p95 \\|rel\\| | Max \\|rel\\| | Schwelle |",
        "|---|---|---|---:|---:|---:|---:|---:|---|"]
    order = {"single": 0, "book": 1}
    for c in sorted((c for c in cells if c.get("is_initial")),
                    key=lambda c: (order.get(c.get("kind"), 9), c.get("ccy", ""), MANAGERS.index(c["manager"])
                                   if c.get("manager") in MANAGERS else 9)):
        lines.append(f"| {KIND_DE.get(c.get('kind'), c.get('kind'))} | {c.get('ccy')} | "
                     f"{MANAGER_DE.get(c.get('manager'), c.get('manager'))} | {di(c.get('n'))} | "
                     f"{di(c.get('n_missing'))} | {sci(c.get('median_rel'))} | {sci(c.get('p95_rel'))} | "
                     f"{sci(c.get('max_rel'))} | {'erfüllt' if c.get('passes') else '**verfehlt**'} |")
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
    checks.add("H1: ρ aus h1_cells.csv gleich h1.json", rho is not None and abs(rho - h1["stat"]) < TOL,
               f"{de(rho, 6)} gegen {de(h1['stat'], 6)}")
    checks.add("H1: besetzte Zellen und Fills gleich h1.json",
               len(occ) == h1.get("n") and int(occ["fills"].sum()) == h1.get("n_fills"),
               f"{len(occ)} Zellen, {di(occ['fills'].sum())} Fills")
    thr = h1.get("threshold")
    checks.add("H1: Urteil folgt aus der Regel (obere Grenze ≥ Schwelle)",
               bool(h1["rejected"]) == bool(h1["hi"] >= thr), f"obere Grenze {de(h1['hi'], 3)}, Schwelle {de(thr, 1)}")
    lines = [
        "## H1 Rangfolge (präregistriert)", "",
        f"- Spearman-ρ zwischen Edge in bp des Nominals und Edge je PM2-Kapital über {di(h1.get('n'))} besetzte "
        f"Zellen im PM2-Fenster: **{ci(h1['stat'], h1['lo'], h1['hi'], 3)}** ({lvl(h1.get('level'))}-Intervall).",
        f"- Regel: abgelehnt, wenn die obere Grenze ≥ {de(thr, 1)} ist. Urteil: {verdict(h1['rejected'])}.",
        f"- Gepoolt über die besetzten Zellen: Edge {de(a, 2)} bp des Nominals und {de(b, 1)} bp des PM2-Kapitals.",
        f"- Rangverschiebung (Rang nach Kapital minus Rang nach Nominal, Rang 1 = höchster Edge): Median |Δ| "
        f"{de(shift.median(), 1)}, grösste |Δ| {di(shift.max())}.",
        f"- Bootstrap: jede Replikation enthält mindestens {di(h1.get('cells_present_min'))} der "
        f"{di(h1.get('n'))} Zellen; {di(h1.get('n_nan_draws'))} Replikationen ohne ρ.",
        f"- {di(h1.get('n_fills_k_le_0'))} Fills mit K_PM2 ≤ 0 bleiben in den Summen (Nachtrag 4); nicht endlich: "
        f"{di(h1.get('n_fills_nonfinite'))}.", "",
        "| Basiswert | Zellen | Fills | Edge bp Nominal | Edge bp PM2-Kapital | ρ je Basiswert (explorativ) |",
        "|---|---:|---:|---:|---:|---|"]
    for c in CCYS:
        sub = occ[occ["ccy"] == c]
        if not len(sub):
            continue
        g = _get(sens, "g_by_ccy", f"pm2_{c}") or {}
        lines.append(f"| {c} | {di(len(sub))} | {di(sub['fills'].sum())} | {de(per_ccy[c][0], 2)} | "
                     f"{de(per_ccy[c][1], 1)} | {ci(g.get('stat'), g.get('lo'), g.get('hi'), 3) if g else '–'} |")
    lines += ["", "Grösste Rangverschiebungen (negativ: die Zelle rückt unter Kapital nach vorn):", "",
              "| Zelle | Fills | Edge bp Nominal | Rang | Edge bp Kapital | Rang | Verschiebung |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    ranked = occ.sort_values(["rank_shift", "cell"], kind="mergesort")
    pick = pd.concat([ranked.head(5), ranked.tail(5)]).drop_duplicates("cell")
    for r in pick.itertuples():
        lines.append(f"| {cell(r.cell)} | {di(r.fills)} | {de(r.A_bp, 2)} | {di(r.rank_A)} | {de(r.B_bp, 1)} | "
                     f"{di(r.rank_B)} | {de(r.rank_shift, 0, sign=True)} |")
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
    checks.add("H2: Urteil folgt aus der Regel (obere Grenze ≥ Schwelle)",
               bool(h2["rejected"]) == bool(h2["hi"] >= thr), f"obere Grenze {de(h2['hi'], 4)}, Schwelle {de(thr, 1)}")
    chk = h2.get("check_stored_ratio_max_abs")
    if chk is not None:
        checks.add("H2: gespeicherte ratio gleich Neuberechnung", float(chk) == 0 and not h2.get(
            "check_stored_ratio_nan_mismatch"), f"grösste Abweichung {sig(chk)}")
    fills = ", ".join(f"{c} {di(_get(h2, 'fills_by_ccy', c))}" for c in CCYS if _get(h2, "fills_by_ccy", c) is not None)
    return [
        "## H2 Grenzkosten (präregistriert)", "",
        f"- Median von ratio = (ΔK/Menge)/K_PM2,Einzel über {di(h2.get('n'))} Fills: "
        f"**{ci(h2['stat'], h2['lo'], h2['hi'], 4)}** ({lvl(h2.get('level'))}-Intervall).",
        f"- Regel: abgelehnt, wenn die obere Grenze ≥ {de(thr, 1)} ist. Urteil: {verdict(h2['rejected'])}.",
        f"- Anteil ratio ≤ 0: {pct(h2.get('share_nonpositive'), 1)}. Ausgeschlossen mit K_PM2,Einzel ≤ 0: "
        f"{di(h2.get('n_excluded'))} von {di(h2.get('n_sample'))} gezogenen Fills; nicht endlich "
        f"{di(h2.get('n_nonfinite'))}, Status nicht ok {di(h2.get('n_not_ok'))}.",
        f"- Konten (Buch zu Tagesbeginn unter PM2): {', '.join(accounts)}; Fills je Basiswert: {fills}; "
        f"{di(h2.get('n_days'))} UTC-Tage.",
        f"- Gegenprobe: gespeicherte Spalte ratio gegen Neuberechnung, grösste Abweichung {sig(chk)}.", ""]


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
    checks.add("H3: Urteil folgt aus der Regel (untere Grenze ≤ Schwelle)",
               bool(h3["rejected"]) == bool(h3["lo"] <= thr), f"untere Grenze {de(h3['lo'], 3)}, Schwelle {de(thr, 1)}")
    notok = ", ".join(f"{di(v)} {STATUS_DE.get(k, k)}" for k, v in sorted(st.items()) if k != "ok") or "keine"
    return [
        "## H3 Netting-Wert (präregistriert)", "",
        f"- Median von K_SM/K_PM2 über {di(h3.get('n'))} Maker-Tage: **{ci(h3['stat'], h3['lo'], h3['hi'], 3)}** "
        f"({lvl(h3.get('level'))}-Intervall).",
        f"- Regel: abgelehnt, wenn die untere Grenze ≤ {de(thr, 1)} ist. Urteil: {verdict(h3['rejected'])}.",
        f"- {di(h3.get('n_rows'))} Maker-Tage im Fenster, nicht gerechnet: {notok}; ausgeschlossen mit K_PM2 ≤ 0: "
        f"{di(h3.get('n_excluded'))}; {di(h3.get('n_days'))} UTC-Tage vom {day_de(h3.get('first_day'))} bis "
        f"{day_de(h3.get('last_day'))}.",
        f"- An {di(h3.get('days_over_63_options'))} Tagen ({pct(h3.get('share_days_over_63_options'), 1)}) hält das "
        f"Buch mehr als 63 Optionen; K_SM ist dort kontrafaktisch (Nachtrag 4).",
        f"- Maker-Tage je Konto: {', '.join(f'{k} {di(v)}' for k, v in sorted(acc.items(), key=lambda kv: label_key(kv[0])))}.",
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
    checks.add("H4: Kriterien und Urteil folgen aus β, p und Placebo-P95",
               all(bool(cr.get(k)) == v for k, v in crit.items()) and bool(h4["rejected"]) == rule_rejected,
               f"β {de(beta, 2)}, p {de(p, 4)}, P95 {de(p95, 2)}")
    diff = fe.get("abs_diff_beta_direct_solve")
    checks.add("H4: Herausmitteln gleich direkter Lösung, Panel reproduziert",
               diff is not None and diff < 1e-8 and bool(pc.get("equal")),
               f"Abweichung {sci(diff)}, Panel neu gebaut identisch: {yes_no(pc.get('equal'))}")
    ev = d["events.csv"]
    n_kept = int(_bool_col(ev["kept"]).sum())
    checks.add("H4: behaltene Ereignisse in events.csv gleich h4.json", n_kept == h4.get("events_kept"),
               f"{n_kept} gegen {h4.get('events_kept')}")
    return [
        "## H4 Preis des Kapitals (präregistriert)", "",
        f"- β = **{de(beta, 2)}** bp des Index je Einheit log-Dosis; {lvl(h4.get('level'))}-Intervall "
        f"[{de(h4.get('lo'), 2)}; {de(h4.get('hi'), 2)}] (Wild-Cluster-Bootstrap mit unrestringierten Residuen, "
        f"beschreibend); Cluster-SE {de(h4.get('se'), 2)}, t {de(h4.get('t'), 3)}.",
        f"- Einseitiges Wild-Cluster-Bootstrap-p für β > 0: {de(p, 4)} (B = {di(h4.get('b'))}).",
        f"- Placebo: {di(pl.get('finite'))} von {di(pl.get('n'))} Replikationen endlich; 95. Perzentil "
        f"{de(p95, 2)}, Median {de(pl.get('median'), 2)}, Mittel {de(pl.get('mean'), 2)}, Spanne "
        f"{de(pl.get('min'), 2)} bis {de(pl.get('max'), 2)}; Anteil der Placebo-β ≥ β: {pct(pl.get('share_ge_beta'), 0)}.",
        f"- Kriterien: β > 0 {yes_no(cr.get('beta_positive'))}; p ≤ {de(H4_ALPHA, 2)} {yes_no(cr.get('p_le_alpha'))}; "
        f"β über dem Placebo-P95 {yes_no(cr.get('beta_gt_placebo_p95'))}.",
        f"- Regel: abgelehnt, wenn β nicht positiv ist mit p ≤ {de(H4_ALPHA, 2)} oder nicht über dem 95. Perzentil "
        f"der Placebo-β liegt. Urteil: {verdict(h4['rejected'])}.",
        f"- Umfang: n = {di(h4.get('n'))} Zeilen, {di(h4.get('fills'))} Fills, {di(h4.get('events'))} Ereignisse mit "
        f"Zellen ({di(h4.get('events_kept'))} behalten), {di(h4.get('cell_events'))} Zell-Ereignis-Paare, "
        f"{di(h4.get('day_ccy'))} Tag-Basiswert-Gruppen, {di(h4.get('clusters'))} Tages-Cluster.",
        f"- Kontrollen: Herausmitteln in {di(fe.get('iterations'))} Iterationen, Abweichung zur direkten Lösung "
        f"{sci(diff)}; Panel neu gebaut identisch: {yes_no(pc.get('equal'))}.", ""]


def _variant_rows(sec_key: str, sec: dict) -> Iterable[Tuple[str, str, dict]]:
    """(summary suffix, German label, verdict dict) for every variant of a sensitivity section."""
    for key in sec:
        val = sec[key]
        if not isinstance(val, dict):
            continue
        if "stat" in val:
            yield key, VARIANT_DE.get((sec_key, key), key), val
        elif key in GROUP_SLOTS or all(isinstance(v, dict) and "stat" in v for v in val.values()):
            for sub in sorted(val, key=label_key if key == "by_label" else str):
                yield f"{key}_{sub}", f"{GROUP_DE.get(key, key)} {sub}", val[sub]


def _group_label(sec_key: str, key: str) -> str:
    if sec_key == "g_by_ccy" and "_" in key:
        mp, c = key.rsplit("_", 1)
        where = {"pm2": "PM2-Fenster", "sm_all": "SM, ganzer Zeitraum", "pm_all": "Legacy-PM, ganzer Zeitraum"}
        return f"{c}, {where.get(mp, mp)}"
    return key


def sensitivity_section(d: Dict[str, Any], s: Summary, checks: Checks) -> List[str]:
    sens, h1, h2, h3 = d["sensitivity.json"], d["h1.json"], d["h2.json"], d["h3.json"]
    lines = ["## Explorative Sensitivitäten", "",
             "Nicht präregistriert als Test. „Urteil nach Regel“ ist das Urteil, das die präregistrierte Regel der "
             "jeweiligen Hypothese auf diese Variante gäbe.", ""]
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
        lines += [f"### {SECTION_DE.get(sec_key, sec_key)}", "",
                  f"| Variante | Grösse | Wert [{lvl(h1.get('level'))}-Intervall] | n | Urteil nach Regel |",
                  "|---|---|---|---:|---|"]
        for suffix, label, v in rows:
            for f in VERDICT_FIELDS:
                s.put(f"sens_{sec_key}_{suffix}_{f}", v.get(f))
            rule = str(v.get("rule", ""))
            dg = digits.get(rule, 3)
            if rule == "H1":
                what = "ρ" + (" (Edge je Kapital und Jahr)" if v.get("unit") else "")
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
        checks.add("Sensitivitäten: Grundvariante gleich dem Test", all(same), f"{sum(same)} von {len(same)} gleich")
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
    lines = ["### (h) H4-Varianten", "",
             f"| Variante | β | {lvl(h4.get('level'))}-Intervall | p | n | Placebo-P95 | Anteil Placebo-β ≥ β | "
             "Urteil nach Regel |",
             "|---|---:|---|---:|---:|---:|---:|---|"]
    for c in CCYS:
        v = by.get(c)
        if not v:
            continue
        lines.append(f"| nur {c} ({di(v.get('events'))} Ereignisse) | {de(v.get('beta'), 2)} | "
                     f"[{de(v.get('lo'), 2)}; {de(v.get('hi'), 2)}] | {de(v.get('p'), 4)} | {di(v.get('n'))} | – | – | – |")
    if no:
        lines.append(f"| ohne Zellen mit \\|d\\| > {de(no.get('max_abs_dose'), 0)} | {de(nh.get('beta'), 2)} | "
                     f"[{de(nh.get('lo'), 2)}; {de(nh.get('hi'), 2)}] | {de(nh.get('p'), 4)} | {di(nh.get('n'))} | "
                     f"{de(npl.get('p95'), 2)} | {pct(npl.get('share_ge_beta'), 0)} | {verdict_plain(no.get('rejected'))} |")
    if al:
        lines.append(f"| Placebo-Abstand zu allen Zeitlinien | {de(h4.get('stat'), 2)} | [{de(h4.get('lo'), 2)}; "
                     f"{de(h4.get('hi'), 2)}] | {de(h4.get('p'), 4)} | {di(h4.get('n'))} | {de(apl.get('p95'), 2)} | "
                     f"{pct(apl.get('share_ge_beta'), 0)} | {verdict_plain(al.get('rejected'))} |")
    lines.append("")
    above = no.get("dose_cells_above") or []
    if no:
        cells = "; ".join(f"{a.get('event_id')} {a.get('cell')} (d = {de(a.get('dose'), 3)})" for a in above) or "keine"
        lines += [f"- Zellen mit \\|d\\| > {de(no.get('max_abs_dose'), 0)}: {cells}. Im echten Panel fallen "
                  f"{di(no.get('rows_dropped_real_panel'))} Zeilen weg; die Variante wirkt sonst nur in den Placebo-Panels."]
    if al:
        lines += ["- Abstand zu allen Zeitlinien: Placebo-Termine halten 28 Tage Abstand zu jeder Parameteränderung "
                  "des Basiswerts unter SM, Legacy-PM, PM2-Standard-Lib und den Konto-Libs."]
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
    lines = ["## Referenzbuch-Effekte der Ereignisse", "",
             "Referenzbuch: Short-Straddle ATM (Strike = Forward) des Verfalls nahe 30 Tagen, 1 Kontrakt je Bein, "
             "täglich 08:00 UTC; K_vorher rechnet dasselbe Buch im selben Marktzustand mit den Parametern von 24 h "
             "früher (reiner Parametereffekt, `results/p2/reference_book.csv`). Zeile je Ereignis aus "
             "`results/p2/events.csv`; der Referenzbuch-Tag ist der erste Tag, dessen Parameterstand aus dem "
             "Ereignis stammt. K in bp des Forwards.", "",
             "| Ereignis | Zeitpunkt | Geänderte Strukturen | max. \\|Dosis\\| | behalten | Panel-Zellen | "
             "Referenzbuch-Tag | K vorher | K nachher | Änderung |",
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
        kinds = ", ".join(STRUCT_DE.get(k, k) for k in str(e.get("kinds", "")).split("+") if k)
        lines.append(f"| {eid} | {ts_de(int(e['event_ts']), seconds=False)} | {kinds} | {pct(e.get('max_abs_dose'), 2)} | "
                     f"{yes_no(e['kept'])} | {di(panel_cells[i])} | {day_de(rday)} | {de(before, 0)} | "
                     f"{de(after, 0)} | {pct(change, 2, sign=True)} |")
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
        lines += ["Parametereffekte im Referenzbuch ohne Ereigniszeile (ausserhalb des Manager-Fensters oder nicht "
                  "in der Ereignisliste):", ""]
        for day, m, c, chg, pts in sorted(extra):
            since = f", Parameterstand vom {ts_de(int(pts), seconds=False)}" if not _missing(pts) else ""
            lines.append(f"- {MANAGER_DE[m]} {c} {day_de(day)}: {pct(chg, 2, sign=True)}{since}.")
        lines.append("")
    # level of the reference book in bp of the forward
    lines += ["Niveau des Referenzbuchs (K in bp des Forwards über die Tage im Manager-Fenster):", "",
              "| Basiswert | Manager | Tage | Minimum | Median | Maximum |", "|---|---|---:|---:|---:|---:|"]
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
                lines.append(f"| {c} | {MANAGER_DE[m]} | {di(len(bp))} | {de(bp.min(), 0)} | {de(bp.median(), 0)} | "
                             f"{de(bp.max(), 0)} |")
    return lines + [""]


def oi_section(d: Dict[str, Any], s: Summary) -> List[str]:
    oi = d["manager_oi_share.csv"].copy()
    oi["month"] = oi["month"].astype(str)
    last_month = str(oi["month"].max()) if len(oi) else None
    s.put("oi_last_month", last_month)
    lines = ["## Manager-Anteile am Options-OI", "",
             "Anteil von `OptionAsset.totalPosition` je Manager an der Summe über die Manager, jeweils am Monatsersten "
             "(`results/p2/manager_oi_share.csv`).", ""]
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
        parts = [f"Daten ab {month_de(sub['month'].iloc[0])}"]
        if first:
            parts.append(f"PM2 erstmals {month_de(first)} ({pct(pos['pm2'].iloc[0], 1)})")
        if mx is not None:
            parts.append(f"höchstens {pct(mx['pm2'], 1)} ({month_de(mx['month'])})")
        if below:
            parts.append(f"Legacy-PM unter 1 % ab {month_de(below)}")
        if last is not None:
            parts.append(f"zuletzt ({month_de(last_month)}) SM {pct(last['sm'], 1)}"
                         + (f", Legacy-PM {pct(last['pm'], 1)}" if not _missing(last.get("pm")) else "")
                         + f", PM2 {pct(last['pm2'], 1)}")
        lines.append(f"- {c}: " + "; ".join(parts) + ".")
    present = [c for c in CCYS if (oi["ccy"] == c).any()]
    cols = [(c, m) for c in present for m in MANAGERS if not (m == "pm" and oi.loc[oi["ccy"] == c, "pm"].isna().all())]
    lines += ["", "| Monat | " + " | ".join(f"{c} {MANAGER_DE[m]}" for c, m in cols) + " |",
              "|---|" + "---:|" * len(cols)]
    for month in sorted(oi["month"].unique()):
        row = []
        for c, m in cols:
            hit = oi[(oi["ccy"] == c) & (oi["month"] == month)]
            row.append(pct(hit[m].iloc[0], 1) if len(hit) else "–")
        lines.append(f"| {month} | " + " | ".join(row) + " |")
    return lines + [""]


def _optional_csv(results: Path, name: str) -> Optional[pd.DataFrame]:
    p = Path(results) / name
    return pd.read_csv(p) if p.is_file() else None


def review_section(d: Dict[str, Any], s: Summary, checks: Checks, results: Path) -> List[str]:
    """Numbers of review round 1 (docs/paper2/MANUSKRIPT.md): all exploratory or descriptive."""
    sens, h3, cap = d["sensitivity.json"], d["h3.json"], d["capital_check.json"]
    lines = ["## Review-Runde 1 (explorativ oder beschreibend)", ""]
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
        f"- H1, nur Vorzeichen: Mischt man die Ränge innerhalb der {di(fl.get('n_pos'))} Zellen mit Edge > 0 und der "
        f"{di(fl.get('n_nonpos'))} übrigen ({di(fl.get('draws'))} Ziehungen), ist ρ im Mittel {de(fl.get('mean'), 3)} "
        f"(5. bis 95. Perzentil {de(fl.get('p05'), 3)} bis {de(fl.get('p95'), 3)}).",
        f"- H1 innerhalb von Gruppen: Edge > 0 {de(wp.get('stat'), 3)} (n = {di(wp.get('n'))}), Edge ≤ 0 "
        f"{de(wn.get('stat'), 3)} (n = {di(wn.get('n'))}), Verkäufe {de(ws.get('stat'), 3)}, Käufe "
        f"{de(wb.get('stat'), 3)}, Käufe mit Edge > 0 {de(wpb.get('stat'), 3)} (n = {di(wpb.get('n'))}).",
        f"- Beste Zellen: von den zehn besten je Kapital {di(top.get('top10'))} unter den zehn besten je Nominal, von "
        f"den besten 20 {di(top.get('top20'))}; gleiches Vorzeichen in {di(sign.get('sign_agree'))} Zellen."]
    # H2 population
    pop = (sens.get("d_h2") or {}).get("population") or {}
    s.put("h2_population", pop.get("n"))
    s.put("h2_population_sample_equal", pop.get("sample_equals_marginal"))
    lines.append(f"- H2: Population vor der Ziehung {di(pop.get('n'))} Fills; die präregistrierte Ziehung ergibt "
                 f"genau die Fills von marginal.parquet: {yes_no(pop.get('sample_equals_marginal'))}.")
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
    lines.append("- H3-Konten nach Manager: " + ", ".join(f"{k} {v}" for k, v in sorted(fam_counts.items())) + ".")
    e = sens.get("e_h3") or {}
    ns = e.get("sm_pm2_le63_no_sm") or {}
    lines += [
        f"- H3: {above} von {len(stats)} Kontomedianen über der Schwelle {de(thr, 0)}; höchstens 63 Optionen ohne "
        f"SM-Konto {ci(ns.get('stat'), ns.get('lo'), ns.get('hi'), 3)} (n = {di(ns.get('n'))}).",
        f"- H3: {di(over)} Maker-Tage mit mehr Beinen als das grösste validierte Buch ({di(legs_max)} Beine)."]
    # fills outside every manager window
    outside = 0
    for c in CCYS:
        mg = _get(cap, "managers", c) or {}
        n_c = max((v.get("n") or 0) for v in mg.values()) if mg else 0
        in_c = max((v.get("n_in_window") or 0) for v in mg.values()) if mg else 0
        outside += int(n_c - in_c)
    s.put("fills_outside_every_window", outside)
    lines.append(f"- Fills ausserhalb jedes Manager-Fensters (ohne Kapital): {di(outside)}.")
    # validation: blocks drawn per cell of single contracts
    cells = (d["validation_summary.json"].get("cells") or [])
    blocks = [int(c.get("n", 0)) + int(c.get("n_missing", 0)) for c in cells
              if c.get("kind") == "single" and c.get("is_initial")]
    s.put("validation_single_blocks_per_cell", max(blocks) if blocks else None)
    s.put("validation_single_blocks_per_cell_min", min(blocks) if blocks else None)
    # probes of the off-chain discount: expiries of the box-spread measurement quoted in Section 2
    box_path = Path(results) / "semantik" / "box_diskont.json"
    box = json.loads(box_path.read_text()) if box_path.is_file() else {}
    first = next((v for k, v in sorted(box.items()) if k.startswith("box_") and isinstance(v, list)), None)
    s.put("semantik_box_expiries", len(first) if first is not None else None)
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
        lines.append(f"- API gegen Chain-Semantik ({di(len(ok))} Einzelkontrakte am {day_de(s['api_day'])}): PM2 "
                     f"Median |rel| {pct(s['api_pm2_median_abs_rel'], 2)}, p95 {pct(s['api_pm2_p95_abs_rel'], 2)}, "
                     f"Maximum {pct(s['api_pm2_max_abs_rel'], 2)} (Laufzeit {s['api_pm2_max_tenor_bucket']}); SM "
                     f"Median {pct(s['api_sm_median_abs_rel'], 2)}, Maximum {pct(s['api_sm_max_abs_rel'], 2)}.")
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
        f"- H4 Niveau: Halbspread im Panel im Mittel {de(rd.get('y_mean'), 2)} bp des Index (Median "
        f"{de(rd.get('y_median'), 2)}); Kapital zehn Prozent billiger (Dosis {de(rd.get('ten_pct_dose'), 3)}): "
        f"Änderung des Halbspreads {de(rd.get('ten_pct_change_beta'), 2, sign=True)} bp, Intervall "
        f"{de(rd.get('ten_pct_change_lo'), 2, sign=True)} bis {de(rd.get('ten_pct_change_hi'), 2, sign=True)} bp.",
        f"- H4 nur Verkaufszellen: β {de(so.get('beta'), 2)}, p {de(so.get('p'), 4)}; OI-gewichtete Dosis "
        f"(Anteil {pct(ow.get('share_min'), 1)} bis {pct(ow.get('share_max'), 1)}): β {de(ow.get('beta'), 2)}, "
        f"p {de(ow.get('p'), 4)}.", ""]
    return lines


def checks_section(checks: Checks, s: Summary) -> List[str]:
    failed = sum(1 for _, ok, _ in checks if not ok)
    s.put("checks_n", len(checks))
    s.put("checks_failed", failed)
    s.put("checks_ok", failed == 0)
    lines = ["## Konsistenzprüfungen", "",
             f"{len(checks) - failed} von {len(checks)} Prüfungen erfüllt. Die Prüfungen rechnen die Urteile aus den "
             f"Zahlen und Regeln nach und gleichen die Dateien untereinander ab.", ""]
    for name, ok, detail in checks:
        lines.append(f"- {name}: {'erfüllt' if ok else '**verletzt**'} ({detail}).")
    return lines + [""]


def limits_section(d: Dict[str, Any], cut: dict) -> List[str]:
    h1, h2, h3, h4 = d["h1.json"], d["h2.json"], d["h3.json"], d["h4.json"]
    lines = ["## Einschränkungen dieser Zahlen", ""]
    if cut["is_pilot"]:
        lines.append(f"- Pilotstand: Die Stichprobe endet am {ts_de(cut['end'])}, vor dem präregistrierten Ende "
                     f"({ts_de(cut['prereg_end_ts'], seconds=False)}). Die Zahlen des Manuskripts entstehen mit dem "
                     f"Enddatenlauf.")
    lines += [
        f"- H3: An {pct(h3.get('share_days_over_63_options'), 1)} der Maker-Tage hält das Buch mehr Optionen, als ein "
        f"SM-Konto auf v2 halten kann; K_SM ist dort kontrafaktisch.",
        f"- H1: {di(h1.get('n_fills_k_le_0'))} Fills mit K_PM2 ≤ 0 (weit vom Mark bepreiste RFQ-Beine) bleiben in "
        f"den Summen.",
        f"- H2 beruht auf {len(h2.get('accounts') or [])} Konten unter PM2; die Verteilung je Konto steht unter (d).",
        f"- H4: Das Intervall für β ist beschreibend; das Urteil folgt aus dem einseitigen p und dem Placebo-P95. "
        f"{di(h4.get('clusters'))} Tages-Cluster, {di(h4.get('events'))} Ereignisse mit Zellen.",
        "- Kapital je Fill ist das Kapital eines leeren Buchs mit genau diesem Kontrakt (Einzelkontrakt); "
        "Nicht-USDC-Collateral bleibt ausserhalb von K."]
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
    s.put("generated_by", "scripts/p2_zahlenblatt.py")
    cut = cutoff(d, s, checks, prereg_end_ts)
    head = header(d, s, cut, results, summary_path, now, checks)
    body = (sample_section(d, s, checks) + validation_section(d, s, checks) + h1_section(d, s, checks)
            + h2_section(d, s, checks) + h3_section(d, s, checks) + h4_section(d, s, checks)
            + sensitivity_section(d, s, checks) + events_section(d, s, checks) + oi_section(d, s)
            + review_section(d, s, checks, results))
    tail = checks_section(checks, s) + limits_section(d, cut)
    md = "\n".join(head + body + tail).rstrip() + "\n"
    return md, dict(sorted(s.items()))


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 scripts/p2_zahlenblatt.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", type=Path, default=RESULTS, help="results directory (default results/p2)")
    ap.add_argument("--out", type=Path, default=OUT, help="markdown output (default docs/paper2/ZAHLENBLATT.md)")
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
