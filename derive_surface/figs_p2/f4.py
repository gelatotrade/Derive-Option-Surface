"""F4 · What netting is worth (H3) · 3.29 x 4.0 in (the column width of main.tex), the same frame as F3.

Panel a is K_SM / K_PM2 of the opening book against the number of option legs, as the median per bin with the
interquartile band, read from the maker-day series that the inference wrote (``fig_h3_series.csv``, rows with
``status == ok``).  The bins double in width from [1, 4) to [256, 512), so the SM subaccount limit of 63 legs is a
real position on the axis; right of it K_SM is counterfactual and the region is hatched.  Panel b is the verdict
forest (``f34_frame.ruler``) with the registered median, the sensitivities including the legacy manager on BTC
and ETH legs, and exploratory rows by book size, manager of the subaccount and parameter regime.

No test statistic is computed here; the figure only bins, counts and takes quantiles of a descriptive column.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from matplotlib import transforms
from matplotlib.ticker import NullLocator

from . import f34_frame as fr

SLOT = "f4"
fmt_int = fr.fmt_int
EDGES = [1, 4, 8, 16, 32, 64, 128, 256, 512]
SM_MAX_OPTIONS = 63
LIMIT_X = SM_MAX_OPTIONS + 0.5
XLIM_A = (1.0, 400.0)
XTICKS_A = [1, 4, 16, 64, 256]
MIN_BIN = 20
XLIM_B = (0.5, 32.0)
BAND = "#CCCCCC"
COUNT_STRIP = 0.13                      # share of the axes height kept free for the counts
SENS = [("maintenance margin", "sm_pm2_mm"), ("legacy PM / PM2", "pm_pm2_be")]
EXPLORE = [("SM / PM2 same legs", "sm_pm2_be", "all"), ("≤ 63 legs", "sm_pm2_le63", "all"),
           ("> 63 legs", "sm_pm2_gt63", "all")]
# books by the manager of their subaccount (the text says "subaccount"; "books" keeps the labels short)
MANAGER_ROWS = [("account_manager=PM", "legacy PM books"), ("account_manager=PM2", "PM2 books")]

CAPTION = (
    r"\textbf{What netting is worth (H3).} Panel a is $K_{\mathrm{SM}}/K_{\mathrm{PM2}}$ for the opening books of "
    r"\PH{h3-days} maker-days against the number of option legs, as the median per bin with the interquartile band; "
    r"the grey numbers above the axis are the maker-days per bin. Beyond 63 legs, the most the endpoint accepted "
    r"for a standard-margin subaccount in the probes, $K_{\mathrm{SM}}$ is counterfactual (hatched); "
    r"this is the case on \PH{h3-over63} maker-days. The dashed line is the registered threshold of two. Panel b is "
    r"the registered median with its 90~per~cent interval, the sensitivities including the legacy manager on BTC "
    r"and ETH legs, and, on grey, exploratory rows: SM against PM2 on the same BTC and ETH legs, by book size, by "
    r"the manager of the subaccount and by parameter regime. The hatched stretch of the registered row, left of the "
    r"threshold, is the rejection region: the rule rejects H3 if the interval reaches into it."
)


# ---------------------------------------------------------------------------------------------------------- data

def load(results_dir: Path) -> Tuple[dict, pd.DataFrame, pd.DataFrame]:
    results_dir = Path(results_dir)
    h = json.loads((results_dir / "h3.json").read_text())
    series = pd.read_csv(results_dir / "fig_h3_series.csv", float_precision="round_trip")
    sens = pd.read_csv(results_dir / "sens_h3.csv", float_precision="round_trip")
    return h, series, sens


def ok_days(series: pd.DataFrame) -> pd.DataFrame:
    ok = series[series["status"].astype(str) == "ok"]
    ok = ok[np.isfinite(ok["ratio_sm_pm2"].to_numpy(float))]
    legs = ok["n_legs"].to_numpy(float)
    if len(ok) and (np.nanmin(legs) < EDGES[0] or np.nanmax(legs) >= EDGES[-1] or np.isnan(legs).any()):
        raise ValueError(f"option legs outside [{EDGES[0]}, {EDGES[-1]}) in fig_h3_series.csv")
    return ok


def panel_a_table(h: dict, series: pd.DataFrame) -> pd.DataFrame:
    ok = ok_days(series)
    legs, r = ok["n_legs"].to_numpy(float), ok["ratio_sm_pm2"].to_numpy(float)
    rows: List[Dict[str, object]] = []
    for lo, hi in zip(EDGES[:-1], EDGES[1:]):
        v = r[(legs >= lo) & (legs < hi)]
        q = np.quantile(v, [0.5, 0.25, 0.75]) if len(v) else [np.nan] * 3
        rows.append({"kind": "bin", "key": f"[{lo}, {hi})", "lo": lo, "hi": hi, "centre": float(np.sqrt(lo * hi)),
                     "n": int(len(v)), "median": float(q[0]), "p25": float(q[1]), "p75": float(q[2]),
                     "printed": fmt_int(len(v))})
    over = int((legs > SM_MAX_OPTIONS).sum())
    rows.append({"kind": "annotation", "key": "counterfactual", "lo": LIMIT_X, "hi": np.nan, "centre": np.nan,
                 "n": over, "median": np.nan, "p25": np.nan, "p75": np.nan,
                 "printed": f"SM counterfactual: {fmt_int(over)} of {fmt_int(len(ok))} maker-days"})
    rows.append({"kind": "annotation", "key": "limit", "lo": LIMIT_X, "hi": np.nan, "centre": np.nan,
                 "n": SM_MAX_OPTIONS, "median": np.nan, "p25": np.nan, "p75": np.nan,
                 "printed": f"SM subaccount limit: {SM_MAX_OPTIONS} legs"})
    rows.append({"kind": "annotation", "key": "threshold", "lo": np.nan, "hi": np.nan, "centre": np.nan,
                 "n": len(ok), "median": float(h["threshold"]), "p25": np.nan, "p75": np.nan,
                 "printed": f"{float(h['threshold']):g}: PM2 saves half"})
    return pd.DataFrame(rows)


def forest_rows(h: dict, sens: pd.DataFrame, series: pd.DataFrame) -> List[fr.Row]:
    rows = [fr.Row(label="registered", kind="registered", stat=float(h["stat"]), lo=float(h["lo"]),
                   hi=float(h["hi"]), n=float(h["n"]), source="h3.json", variant="sm_pm2", group="all",
                   n_days=float(h.get("n_days", np.nan)))]
    for label, variant in SENS:
        r = fr.sens_row(sens, label, "sensitivity", variant, "all", "sens_h3.csv")
        if r is not None:
            rows.append(r)
    for label, variant, group in EXPLORE:
        r = fr.sens_row(sens, label, "exploratory", variant, group, "sens_h3.csv")
        if r is not None:
            rows.append(r)
    ok = series[series["status"].astype(str) == "ok"]
    sm_accounts = sorted(set(ok.loc[ok["manager"].astype(str) == "SM", "label"].astype(str)))
    sm_label = f"SM books ({sm_accounts[0]})" if len(sm_accounts) == 1 else "SM books"
    for group, label in [("account_manager=SM", sm_label)] + MANAGER_ROWS:
        r = fr.sens_row(sens, label, "exploratory", "sm_pm2", group, "sens_h3.csv")
        if r is not None:
            rows.append(r)
    rows += fr.regime_rows(sens, "sm_pm2", "sens_h3.csv")
    return rows


def header_lines(h: dict) -> List[str]:
    parts = [f"{len(h['accounts'])} subaccounts", f"{fmt_int(h['n'])} maker-days",
             f"{fmt_int(h['n_days'])} day clusters (UTC days, not subaccounts)"]
    return [fr.verdict_line(h)] + fr.wrap_parts(parts)


def xlim_b(rows: List[fr.Row]) -> Tuple[float, float]:
    """0.5 to 32, doubled outwards while a row would leave the axis (not beyond 1/8 and 256)."""
    vals = np.array([v for r in rows for v in (r.stat, r.lo, r.hi) if np.isfinite(v) and v > 0])
    x0, x1 = XLIM_B
    while vals.size and vals.min() < x0 and x0 > 0.125:
        x0 /= 2.0
    while vals.size and vals.max() > x1 and x1 < 256.0:
        x1 *= 2.0
    return x0, x1


def log2_ticks(x0: float, x1: float, keep: float = 2.0, most: int = 7) -> List[float]:
    """Powers of two on the axis; every second one when there would be more than ``most``, keeping ``keep``."""
    ticks = [2.0 ** k for k in range(int(round(np.log2(x0))), int(round(np.log2(x1))) + 1)]
    if len(ticks) > most:
        k0 = int(round(np.log2(keep)))
        ticks = [t for t in ticks if (int(round(np.log2(t))) - k0) % 2 == 0]
    return ticks


# ---------------------------------------------------------------------------------------------------- drawing

def make(results_dir: Path = Path("results/p2")):
    """Draw F4; returns the figure and the tables {'a': ..., 'b': ...} with every printed number."""
    h, series, sens = load(results_dir)
    a_tab = panel_a_table(h, series)
    header = header_lines(h)
    rows = forest_rows(h, sens, series)
    x0, x1 = xlim_b(rows)
    ticks = log2_ticks(x0, x1, keep=float(h["threshold"]))
    with fr.plt.rc_context(fr.RC):
        fig, ax_a, ax_b = fr.frame(header)
        _panel_a(ax_a, a_tab)
        line, b_tab = fr.ruler(ax_b, rows, h, side="left", xlim=(x0, x1), log=True, ticks=ticks,
                               ticklabels=[f"{t:g}" for t in ticks], xlabel="capital ratio to PM2 (log)")
    if line != header[0]:
        raise ValueError("verdict line of the forest differs from the header")
    b_tab = pd.concat([fr.header_table(header), b_tab], ignore_index=True)
    return fig, {"a": a_tab, "b": b_tab}


def _panel_a(ax, tab: pd.DataFrame) -> None:
    bins = tab[(tab["kind"] == "bin") & (tab["n"] > 0)]
    note = tab[tab["kind"] == "annotation"].set_index("key")
    lo_q, hi_q = float(bins["p25"].min()), float(bins["p75"].max())
    y1 = max(20.0, hi_q * 1.6)
    y0 = min(0.8, lo_q / 2.0)
    # a clean strip at the bottom carries the maker-days per bin; hatch and limit line start above it
    while np.log(lo_q / y0) / np.log(y1 / y0) < COUNT_STRIP + 0.03:
        y0 /= 1.25
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*XLIM_A)
    ax.set_ylim(y0, y1)
    ax.axvspan(LIMIT_X, XLIM_A[1], ymin=COUNT_STRIP, facecolor="none", edgecolor=fr.HATCH, hatch="\\" * 4, lw=0,
               zorder=0)
    ax.axvline(LIMIT_X, ymin=COUNT_STRIP, color=fr.RULE_GREY, lw=0.6, zorder=2)
    thr = float(note.loc["threshold", "median"])
    ax.axhline(thr, color="black", ls="--", lw=0.8, zorder=2)
    ax.fill_between(bins["centre"], bins["p25"], bins["p75"], color=BAND, lw=0, zorder=1)
    ax.plot(bins["centre"], bins["median"], color="black", lw=1.0, zorder=3)
    ax.plot(bins["centre"], bins["median"], "o", ms=2.5, color="black", zorder=4)
    xa = transforms.blended_transform_factory(ax.transData, ax.transAxes)
    for _, b in bins.iterrows():
        ax.text(b["centre"], 0.03, b["printed"], transform=xa, ha="center", va="bottom", fontsize=fr.FS,
                color=fr.GREY)
    ax.text(1.12, thr * 1.06, note.loc["threshold", "printed"], ha="left", va="bottom", fontsize=fr.FS)
    ax.text(LIMIT_X / 1.1, 0.96, note.loc["limit", "printed"].replace(": ", ":\n"), transform=xa, ha="right",
            va="top", fontsize=fr.FS, linespacing=1.15)
    # the counterfactual region is named above the axes, centred on the hatch
    xc = float(np.sqrt(LIMIT_X * XLIM_A[1]))
    ax.text(xc, 1.03, note.loc["counterfactual", "printed"].replace(": ", ":\n"), transform=xa, ha="center",
            va="bottom", fontsize=fr.FS, linespacing=1.15)
    ax.set_xticks(XTICKS_A)
    ax.set_xticklabels([str(t) for t in XTICKS_A])
    ax.xaxis.set_minor_locator(NullLocator())
    yt = ([0.5] if y0 < 0.5 else []) + [1, 2, 4, 8, 16]
    ax.set_yticks(yt)
    ax.set_yticklabels([f"{t:g}" for t in yt])
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_xlabel("option legs in the book (log)")
    ax.set_ylabel("SM / PM2 capital (log)")


def build(out_dir: Path = Path("paper2/figures"), results_dir: Path = Path("results/p2")) -> List[Path]:
    """Write ``fig_f4_a.csv``, ``fig_f4_b.csv`` to ``results_dir`` and ``f4.pdf``/``f4.png`` to ``out_dir``."""
    fig, tables = make(results_dir)
    paths = [fr.write_csv(tables["a"], Path(results_dir) / "fig_f4_a.csv"),
             fr.write_csv(tables["b"], Path(results_dir) / "fig_f4_b.csv")]
    return paths + fr.save(fig, SLOT, out_dir)


# ----------------------------------------------------------------------------------------------------- checks

def _fig(rd: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    return fr.read_csv(rd / "fig_f4_a.csv"), fr.read_csv(rd / "fig_f4_b.csv")


def _chk_verdict(rd: Path):
    h, _, _ = load(rd)
    _, b = _fig(rd)
    printed = b.loc[b["kind"] == "header", "printed"].iloc[0]
    expected = fr.verdict_line(h)                                  # raises if the rule disagrees with rejected
    return printed == expected, f"figure {printed!r}; h3.json gives {expected!r}"


def _chk_sample(rd: Path):
    h, series, _ = load(rd)
    _, b = _fig(rd)
    text = " · ".join(b.loc[b["kind"] == "header", "printed"].iloc[1:])
    want = [f"{len(h['accounts'])} subaccounts", f"{fmt_int(h['n'])} maker-days",
            f"{fmt_int(h['n_days'])} day clusters"]
    missing = [w for w in want if w not in text]
    ok_rows = int((series["status"].astype(str) == "ok").sum())
    acc_sum = sum(h["accounts"].values())
    ok = not missing and acc_sum == h["n"] == ok_rows and h["status_counts"].get("ok") == h["n"]
    return ok, f"missing {missing}; accounts sum {acc_sum}, ok rows {ok_rows}, h3.json n {h['n']}"


def _chk_registered(rd: Path):
    h, _, sens = load(rd)
    _, b = _fig(rd)
    r = b[b["kind"] == "registered"].iloc[0]
    s = sens[(sens["variant"] == "sm_pm2") & (sens["group"] == "all")].iloc[0]
    ok = all(fr.close(r[k], h[k]) for k in ("stat", "lo", "hi", "n")) and \
        all(fr.close(s[k], h[k]) for k in ("stat", "lo", "hi", "n")) and r["printed_n"] == fmt_int(h["n"])
    return ok, f"figure {r['stat']}, [{r['lo']}, {r['hi']}], n {r['n']}; h3.json {h['stat']}, n {h['n']}"


def _chk_rows(rd: Path):
    _, _, sens = load(rd)
    _, b = _fig(rd)
    bad = []
    rows = b[b["source"] == "sens_h3.csv"]
    for _, r in rows.iterrows():
        s = sens[(sens["variant"] == r["variant"]) & (sens["group"] == r["group"])]
        if len(s) != 1 or not all(fr.close(r[k], s.iloc[0][k]) for k in ("stat", "lo", "hi", "n")):
            bad.append(r["label"])
    return not bad and len(rows) > 0, f"{len(rows)} rows against sens_h3.csv; mismatched {bad}"


def _chk_legacy(rd: Path):
    _, _, sens = load(rd)
    _, b = _fig(rd)
    r = b[b["variant"] == "pm_pm2_be"]
    s = sens[(sens["variant"] == "pm_pm2_be") & (sens["group"] == "all")]
    ok = len(r) == 1 and len(s) == 1 and r.iloc[0]["kind"] == "sensitivity" and \
        r.iloc[0]["printed_n"] == fmt_int(s.iloc[0]["n"])
    return ok, f"legacy row n {r.iloc[0]['printed_n'] if len(r) else None}; sens_h3.csv n " \
               f"{s.iloc[0]['n'] if len(s) else None}"


def _chk_bins(rd: Path):
    h, series, _ = load(rd)
    a, _ = _fig(rd)
    ok_ = ok_days(series)
    legs = ok_["n_legs"].to_numpy(float)
    want = np.histogram(legs, bins=EDGES)[0]
    bins = a[a["kind"] == "bin"]
    got = bins["n"].to_numpy(int)
    ok = len(got) == 8 and np.array_equal(got, want) and int(got.sum()) == int(h["n"]) and got.min() >= MIN_BIN
    ok = ok and list(bins["printed"]) == [fmt_int(x) for x in want]
    return ok, f"maker-days per bin {got.tolist()}; series {want.tolist()}; h3.json n {h['n']}"


def _chk_quantiles(rd: Path):
    _, series, _ = load(rd)
    a, _ = _fig(rd)
    ok_ = ok_days(series)
    legs, r = ok_["n_legs"].to_numpy(float), ok_["ratio_sm_pm2"].to_numpy(float)
    bad = []
    for _, b in a[a["kind"] == "bin"].iterrows():
        v = r[(legs >= b["lo"]) & (legs < b["hi"])]
        q = np.quantile(v, [0.5, 0.25, 0.75])
        if not all(fr.close(b[k], x) for k, x in zip(("median", "p25", "p75"), q)):
            bad.append(b["key"])
    return not bad, f"bins off: {bad}"


def _chk_counterfactual(rd: Path):
    h, series, _ = load(rd)
    a, _ = _fig(rd)
    ok_ = ok_days(series)
    legs = ok_["n_legs"].to_numpy(float)
    flag = ok_["over_63_options"].astype(str).str.lower().eq("true").to_numpy()
    cf = a[a["key"] == "counterfactual"].iloc[0]
    n_over = int((legs >= SM_MAX_OPTIONS + 1).sum())
    ok = int(cf["n"]) == n_over == int(flag.sum()) == int(h["days_over_63_options"]) and \
        np.array_equal(flag, legs >= SM_MAX_OPTIONS + 1) and \
        cf["printed"] == f"SM counterfactual: {fmt_int(h['days_over_63_options'])} of {fmt_int(h['n'])} maker-days"
    return ok, f"{cf['printed']}; legs >= 64: {n_over}; flag {int(flag.sum())}; h3.json {h['days_over_63_options']}"


def _chk_threshold(rd: Path):
    h, _, _ = load(rd)
    a, _ = _fig(rd)
    t = a[a["key"] == "threshold"].iloc[0]
    return fr.close(t["median"], h["threshold"]), f"dashed line at {t['median']}; h3.json {h['threshold']}"


CHECKS = [
    fr.Check("verdict line", "fig_f4_b.csv header", "h3.json rule, threshold, lo, hi, rejected", _chk_verdict),
    fr.Check("sample line", "fig_f4_b.csv header", "h3.json accounts, n, n_days, status_counts; fig_h3_series.csv",
             _chk_sample),
    fr.Check("registered row", "fig_f4_b.csv registered", "h3.json and sens_h3.csv sm_pm2/all", _chk_registered),
    fr.Check("other forest rows", "fig_f4_b.csv", "sens_h3.csv", _chk_rows),
    fr.Check("legacy PM row", "fig_f4_b.csv pm_pm2_be", "sens_h3.csv pm_pm2_be/all", _chk_legacy),
    fr.Check("maker-days per bin", "fig_f4_a.csv bin n", "fig_h3_series.csv ok rows, h3.json n", _chk_bins),
    fr.Check("bin quantiles", "fig_f4_a.csv median, p25, p75", "fig_h3_series.csv ratio_sm_pm2", _chk_quantiles),
    fr.Check("counterfactual days", "fig_f4_a.csv counterfactual", "h3.json days_over_63_options; fig_h3_series.csv",
             _chk_counterfactual),
    fr.Check("threshold line", "fig_f4_a.csv threshold", "h3.json threshold", _chk_threshold),
]


def run_checks(results_dir: Path = Path("results/p2")):
    return fr.run(CHECKS, results_dir)
