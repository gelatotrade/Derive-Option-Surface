"""F3 · A fill in the book (H2) · 3.29 x 4.0 in (the column width of main.tex).

Panel a is the cumulative distribution of dK per contract over the stand-alone PM2 capital, read from the binned
distribution that the inference wrote (``fig_h2_dist.csv``, label ``all``, variant ``ratio``): the value at every
right bin edge is the cumulative count over n, from the left overflow at x = -1 to one minus the right overflow at
x = 2.  Bands behind the curve split the fills into free (<= 0), cheap (0 to 1/2), partial (1/2 to 1) and full
(>= 1, the whole stand-alone capital); the share <= 0 comes from ``share_le_0``, the others from the bins.  The
median with its day-cluster interval sits at height one half (the interval is narrower than the circle; its bounds
are in the header).  Panel b is the verdict forest (``f34_frame.ruler``) on the same x-axis.

No test statistic is computed here; the figure only sums bins and sorts rows.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from matplotlib import transforms

from . import f34_frame as fr

SLOT = "f3"
XLIM = (-1.0, 2.0)
TICKS = [-1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]
TICKLABELS = ["−1", "−0.5", "0", "0.5", "1", "1.5", "2"]
XLABEL = "ΔK per contract / stand-alone PM2 capital"
LABEL_NUDGE = {"cheap": -0.05, "partial": 0.05}     # x offset of the two inner band labels
BANDS = [("free", -np.inf, 0.0, "#BDBDBD"), ("cheap", 0.0, 0.5, "#D9D9D9"), ("partial", 0.5, 1.0, "#EFEFEF"),
         ("full", 1.0, np.inf, "white")]
SENS = [("next contract", "ratio_unit"), ("maintenance margin", "ratio_mm"), ("tape book", "ratio_tape")]
N_BINS = 62

CAPTION = (
    r"\textbf{A fill in a dominant maker's book (H2).} Panel a is the cumulative distribution of the "
    r"marginal capital of a fill per contract over its stand-alone PM2 capital, $\Delta K / K_{\text{single}}$, "
    r"for the \PH{h2-n} tested fills of the four PM2 subaccounts, which trade ETH and HYPE only; the numbers above "
    r"the bands are the shares of fills in each band, and the shares beyond the axis are given at both ends. The "
    r"dashed line is the registered threshold of one half, and the circle at height one half is the median; its 90 per "
    r"cent day-cluster interval is narrower than the circle and printed at the top. Panel b repeats the registered "
    r"row above the sensitivities and, on grey, "
    r"exploratory rows per account and per parameter regime. A maker who starts from an empty book pays the "
    r"stand-alone capital of Figure~\ref{fig:f1}."
)


# ---------------------------------------------------------------------------------------------------------- data

def load(results_dir: Path) -> Tuple[dict, pd.DataFrame, pd.DataFrame]:
    results_dir = Path(results_dir)
    h = json.loads((results_dir / "h2.json").read_text())
    dist = pd.read_csv(results_dir / "fig_h2_dist.csv", float_precision="round_trip")
    sens = pd.read_csv(results_dir / "sens_h2.csv", float_precision="round_trip")
    return h, dist, sens


def registered_dist(dist: pd.DataFrame) -> Tuple[pd.DataFrame, float, float]:
    """The 62 bins of the registered variant over all fills, n and the share <= 0."""
    d = dist[(dist["label"].astype(str) == "all") & (dist["variant"].astype(str) == "ratio")]
    hist = d[d["kind"] == "hist"].sort_values("x", kind="mergesort").reset_index(drop=True)
    if len(hist) != N_BINS or not (np.isneginf(hist["x"].iloc[0]) and np.isposinf(hist["x_hi"].iloc[-1])):
        raise ValueError(f"fig_h2_dist.csv: expected {N_BINS} bins with two open ends, got {len(hist)}")
    inner_lo = hist["x"].to_numpy(float)[1:]
    if not (np.isclose(inner_lo[0], XLIM[0]) and np.isclose(hist["x_hi"].to_numpy(float)[-2], XLIM[1])):
        raise ValueError("fig_h2_dist.csv: inner bins do not span [-1, 2]")
    n = float(d.loc[d["kind"] == "n", "value"].iloc[0])
    share0 = float(d.loc[d["kind"] == "share_le_0", "value"].iloc[0])
    if not np.isclose(hist["value"].sum(), n, rtol=0, atol=1e-9):
        raise ValueError(f"fig_h2_dist.csv: bins sum to {hist['value'].sum()}, n = {n}")
    return hist, n, share0


def panel_a_table(hist: pd.DataFrame, n: float, share0: float, h: dict) -> pd.DataFrame:
    counts = hist["value"].to_numpy(float)
    right = hist["x_hi"].to_numpy(float)
    cum = np.cumsum(counts)
    rows: List[Dict[str, object]] = []
    for x, c in zip(right[:-1], cum[:-1]):                 # right edges -1, -0.95, ..., 2
        rows.append({"kind": "ecdf", "key": "", "x": float(x), "x_hi": np.nan, "count": float(c),
                     "value": float(c / n), "printed": ""})

    def f_at(x):
        k = int(np.flatnonzero(np.isclose(right, x))[0])
        return float(cum[k] / n), float(cum[k])

    f_half, c_half = f_at(0.5)
    f_one, c_one = f_at(1.0)
    shares = {"free": share0, "cheap": f_half - share0, "partial": f_one - f_half, "full": 1.0 - f_one}
    band_counts = {"free": share0 * n, "cheap": c_half - share0 * n, "partial": c_one - c_half, "full": n - c_one}
    for key, lo, hi, _ in BANDS:
        rows.append({"kind": "band", "key": key, "x": lo, "x_hi": hi, "count": float(band_counts[key]),
                     "value": float(shares[key]), "printed": fr.pct(shares[key])})
    below, above = float(counts[0]), float(counts[-1])
    rows.append({"kind": "overflow", "key": "below", "x": XLIM[0], "x_hi": np.nan, "count": below,
                 "value": below / n, "printed": f"{fr.pct(below / n, 1)} below −1"})
    rows.append({"kind": "overflow", "key": "above", "x": XLIM[1], "x_hi": np.nan, "count": above,
                 "value": above / n, "printed": f"{fr.pct(above / n, 1)} above 2"})
    rows.append({"kind": "median", "key": "registered", "x": float(h["lo"]), "x_hi": float(h["hi"]), "count": n,
                 "value": float(h["stat"]), "printed": ""})
    rows.append({"kind": "n", "key": "all", "x": np.nan, "x_hi": np.nan, "count": n, "value": n, "printed": ""})
    return pd.DataFrame(rows)


def _account_key(group: str) -> Tuple[int, str]:
    lab = group.split("=", 1)[1]
    m = re.search(r"(\d+)$", lab)
    return (int(m.group(1)) if m else 10 ** 9, lab)


def forest_rows(h: dict, sens: pd.DataFrame) -> List[fr.Row]:
    rows = [fr.Row(label="registered", kind="registered", stat=float(h["stat"]), lo=float(h["lo"]),
                   hi=float(h["hi"]), n=float(h["n"]), source="h2.json", variant=str(h.get("variant", "ratio")),
                   group="all", n_days=float(h.get("n_days", np.nan)))]
    for label, variant in SENS:
        r = fr.sens_row(sens, label, "sensitivity", variant, "all", "sens_h2.csv")
        if r is not None:
            rows.append(r)
    base = sens[sens["variant"].astype(str) == "ratio"]
    ccy = base[base["group"].astype(str).str.startswith("ccy=")]
    groups = sorted((g for g in base["group"].astype(str) if g.startswith("label=")), key=_account_key)
    for g in groups:
        r = fr.sens_row(sens, g.split("=", 1)[1], "exploratory", "ratio", g, "sens_h2.csv")
        # an account that is the only one of its underlying says so (M3 is all of HYPE)
        same = ccy[np.isclose(ccy["n"].astype(float), r.n) & np.isclose(ccy["stat"].astype(float), r.stat)]
        if len(same) == 1:
            r.label = f"{r.label} ({same['group'].iloc[0].split('=', 1)[1]})"
        rows.append(r)
    rows += fr.regime_rows(sens, "ratio", "sens_h2.csv")
    return rows


def header_lines(h: dict) -> List[str]:
    ccys = sorted(h.get("fills_by_ccy", {}))
    parts = [f"{len(h['accounts'])} PM2 accounts, {fr.list_words(ccys)} only",
             f"{fr.fmt_int(h['n'])} of {fr.fmt_int(h['n_sample'])} sampled fills",
             f"{fr.fmt_int(h['n_days'])} day clusters"]
    return [fr.verdict_line(h)] + fr.wrap_parts(parts)


# ---------------------------------------------------------------------------------------------------- drawing

def make(results_dir: Path = Path("results/p2")):
    """Draw F3; returns the figure and the tables {'a': ..., 'b': ...} with every printed number."""
    h, dist, sens = load(results_dir)
    hist, n, share0 = registered_dist(dist)
    if not np.isclose(n, float(h["n"])):
        raise ValueError(f"fig_h2_dist.csv n = {n} but h2.json n = {h['n']}")
    a_tab = panel_a_table(hist, n, share0, h)
    header = header_lines(h)
    with fr.plt.rc_context(fr.RC):
        fig, ax_a, ax_b = fr.frame(header)
        _panel_a(ax_a, a_tab, h)
        rows = forest_rows(h, sens)
        line, b_tab = fr.ruler(ax_b, rows, h, side="right", xlim=XLIM, ticks=TICKS, ticklabels=TICKLABELS,
                               xlabel=XLABEL)
    if line != header[0]:
        raise ValueError("verdict line of the forest differs from the header")
    b_tab = pd.concat([fr.header_table(header), b_tab], ignore_index=True)
    return fig, {"a": a_tab, "b": b_tab}


def _panel_a(ax, tab: pd.DataFrame, h: dict) -> None:
    ax.set_xlim(*XLIM)
    ax.set_ylim(0.0, 1.0)
    bands = tab[tab["kind"] == "band"].set_index("key")
    for key, lo, hi, colour in BANDS:
        if colour != "white":
            ax.axvspan(max(lo, XLIM[0]), min(hi, XLIM[1]), color=colour, lw=0, zorder=0)
    top = transforms.blended_transform_factory(ax.transData, ax.transAxes)
    for key, lo, hi, _ in BANDS:
        # "cheap" and "partial" sit over bands of 0.5 each and would read as one phrase; nudge them apart
        xc = (max(lo, XLIM[0]) + min(hi, XLIM[1])) / 2.0 + LABEL_NUDGE.get(key, 0.0)
        ax.text(xc, 1.03, f"{key}\n{bands.loc[key, 'printed']}", transform=top, ha="center", va="bottom",
                fontsize=fr.FS, linespacing=1.15)
    ax.axvline(0.5, color="black", ls="--", lw=0.8, zorder=2)
    ax.axvline(1.0, color=fr.RULE_GREY, lw=0.5, zorder=2)
    e = tab[tab["kind"] == "ecdf"]
    ax.plot(e["x"], e["value"], drawstyle="steps-post", color="black", lw=1.0, zorder=3)
    ax.plot([h["lo"], h["hi"]], [0.5, 0.5], color="black", lw=2.0, solid_capstyle="butt", zorder=4)
    ax.plot([h["stat"]], [0.5], "o", ms=4.5, mfc="white", mec="black", mew=0.9, zorder=5)
    over = tab[tab["kind"] == "overflow"].set_index("key")
    # overflow shares in the two corners an ECDF never reaches, one line for the share and one for the edge
    ax.text(0.02, 0.96, over.loc["below", "printed"].replace(" below", "\nbelow"), transform=ax.transAxes,
            ha="left", va="top", fontsize=fr.FS, linespacing=1.15)
    ax.text(0.98, 0.04, over.loc["above", "printed"].replace(" above", "\nabove"), transform=ax.transAxes,
            ha="right", va="bottom", fontsize=fr.FS, linespacing=1.15)
    ax.set_xticks(TICKS)
    ax.set_xticklabels(TICKLABELS)
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0", "0.25", "0.5", "0.75", "1"])
    ax.set_ylabel("share of fills")


def build(out_dir: Path = Path("paper2/figures"), results_dir: Path = Path("results/p2")) -> List[Path]:
    """Write ``fig_f3_a.csv``, ``fig_f3_b.csv`` to ``results_dir`` and ``f3.pdf``/``f3.png`` to ``out_dir``."""
    fig, tables = make(results_dir)
    paths = [fr.write_csv(tables["a"], Path(results_dir) / "fig_f3_a.csv"),
             fr.write_csv(tables["b"], Path(results_dir) / "fig_f3_b.csv")]
    return paths + fr.save(fig, SLOT, out_dir)


# ----------------------------------------------------------------------------------------------------- checks

def _fig(rd: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    return fr.read_csv(rd / "fig_f3_a.csv"), fr.read_csv(rd / "fig_f3_b.csv")


def _chk_verdict(rd: Path):
    h, _, _ = load(rd)
    _, b = _fig(rd)
    printed = b.loc[b["kind"] == "header", "printed"].iloc[0]
    expected = fr.verdict_line(h)                                  # raises if the rule disagrees with rejected
    return printed == expected, f"figure {printed!r}; h2.json gives {expected!r}"


def _chk_sample(rd: Path):
    h, _, _ = load(rd)
    _, b = _fig(rd)
    text = " · ".join(b.loc[b["kind"] == "header", "printed"].iloc[1:])
    want = [f"{len(h['accounts'])} PM2 accounts", fr.list_words(sorted(h["fills_by_ccy"])) + " only",
            f"{fr.fmt_int(h['n'])} of {fr.fmt_int(h['n_sample'])} sampled fills",
            f"{fr.fmt_int(h['n_days'])} day clusters"]
    missing = [w for w in want if w not in text]
    ccy_sum = sum(h["fills_by_ccy"].values())
    ok = not missing and ccy_sum == h["n"] and h["n_sample"] - h["n_excluded"] == h["n"]
    return ok, f"missing {missing}; fills by ccy sum {ccy_sum}, n {h['n']}, n_sample {h['n_sample']}"


def _chk_registered(rd: Path):
    h, _, sens = load(rd)
    _, b = _fig(rd)
    r = b[b["kind"] == "registered"].iloc[0]
    s = sens[(sens["variant"] == "ratio") & (sens["group"] == "all")].iloc[0]
    ok = all(fr.close(r[k], h[k]) for k in ("stat", "lo", "hi", "n")) and \
        all(fr.close(s[k], h[k]) for k in ("stat", "lo", "hi", "n")) and r["printed_n"] == fr.fmt_int(h["n"])
    return ok, f"figure {r['stat']}, [{r['lo']}, {r['hi']}], n {r['n']}; h2.json {h['stat']}, n {h['n']}"


def _chk_rows(rd: Path):
    _, _, sens = load(rd)
    _, b = _fig(rd)
    bad = []
    rows = b[b["source"] == "sens_h2.csv"]
    for _, r in rows.iterrows():
        s = sens[(sens["variant"] == r["variant"]) & (sens["group"] == r["group"])]
        if len(s) != 1 or not all(fr.close(r[k], s.iloc[0][k]) for k in ("stat", "lo", "hi", "n")):
            bad.append(r["label"])
    return not bad and len(rows) > 0, f"{len(rows)} rows against sens_h2.csv; mismatched {bad}"


def _chk_accounts(rd: Path):
    h, _, _ = load(rd)
    _, b = _fig(rd)
    acc = b[b["group"].astype(str).str.startswith("label=")]
    labels = sorted(g.split("=", 1)[1] for g in acc["group"])
    ok = labels == sorted(h["accounts"]) and int(acc["n"].sum()) == int(h["n"])
    return ok, f"figure accounts {labels} with {int(acc['n'].sum())} fills; h2.json {sorted(h['accounts'])}, n {h['n']}"


def _chk_bins(rd: Path):
    h, dist, _ = load(rd)
    hist, n, _ = registered_dist(dist)                             # raises unless 62 bins, two open, sum = n
    return int(n) == int(h["n"]), f"{len(hist)} bins sum to {n}; h2.json n {h['n']}"


def _chk_ecdf(rd: Path):
    _, dist, _ = load(rd)
    a, _ = _fig(rd)
    hist, n, _ = registered_dist(dist)
    want = np.cumsum(hist["value"].to_numpy(float))[:-1] / n
    got = a.loc[a["kind"] == "ecdf", "value"].to_numpy(float)
    ok = len(got) == len(want) and np.allclose(got, want, rtol=0, atol=1e-12)
    return ok, f"{len(got)} steps against the cumulative bins"


def _chk_ecdf_zero(rd: Path):
    h, dist, _ = load(rd)
    a, _ = _fig(rd)
    _, n, share0 = registered_dist(dist)
    e = a[a["kind"] == "ecdf"]
    at0 = float(e.loc[np.isclose(e["x"], 0.0), "value"].iloc[0])
    ok = abs(at0 - h["share_nonpositive"]) <= 1.0 / n and fr.close(share0, h["share_nonpositive"])
    return ok, f"ECDF(0) {at0}; share_le_0 {share0}; h2.json share_nonpositive {h['share_nonpositive']}"


def _chk_bands(rd: Path):
    _, dist, _ = load(rd)
    a, _ = _fig(rd)
    hist, n, share0 = registered_dist(dist)
    right, cum = hist["x_hi"].to_numpy(float), np.cumsum(hist["value"].to_numpy(float))
    f = {x: cum[int(np.flatnonzero(np.isclose(right, x))[0])] / n for x in (0.5, 1.0)}
    want = {"free": share0, "cheap": f[0.5] - share0, "partial": f[1.0] - f[0.5], "full": 1 - f[1.0]}
    bands = a[a["kind"] == "band"].set_index("key")
    ok = all(fr.close(bands.loc[k, "value"], v) and bands.loc[k, "printed"] == fr.pct(v) for k, v in want.items())
    ok = ok and abs(bands["value"].sum() - 1.0) < 1e-12
    return ok, "; ".join(f"{k} {bands.loc[k, 'printed']}" for k in want)


def _chk_overflow(rd: Path):
    _, dist, _ = load(rd)
    a, _ = _fig(rd)
    hist, n, _ = registered_dist(dist)
    over = a[a["kind"] == "overflow"].set_index("key")
    e = a.loc[a["kind"] == "ecdf", "value"].to_numpy(float)
    lo, hi = hist["value"].iloc[0] / n, hist["value"].iloc[-1] / n
    ok = fr.close(over.loc["below", "value"], lo) and fr.close(over.loc["above", "value"], hi) and \
        fr.close(e[0], lo) and fr.close(e[-1], 1 - hi)
    return ok, f"{over.loc['below', 'printed']}; {over.loc['above', 'printed']}"


def _chk_median(rd: Path):
    h, _, _ = load(rd)
    a, _ = _fig(rd)
    m = a[a["kind"] == "median"].iloc[0]
    ok = fr.close(m["value"], h["stat"]) and fr.close(m["x"], h["lo"]) and fr.close(m["x_hi"], h["hi"])
    return ok, f"bar {m['x']} to {m['x_hi']}, circle {m['value']}"


CHECKS = [
    fr.Check("verdict line", "fig_f3_b.csv header", "h2.json rule, threshold, lo, hi, rejected", _chk_verdict),
    fr.Check("sample line", "fig_f3_b.csv header", "h2.json accounts, fills_by_ccy, n, n_sample, n_days",
             _chk_sample),
    fr.Check("registered row", "fig_f3_b.csv registered", "h2.json and sens_h2.csv ratio/all", _chk_registered),
    fr.Check("other forest rows", "fig_f3_b.csv", "sens_h2.csv", _chk_rows),
    fr.Check("account rows", "fig_f3_b.csv label=*", "h2.json accounts and n", _chk_accounts),
    fr.Check("62 bins, two open, sum n", "fig_h2_dist.csv all/ratio", "h2.json n", _chk_bins),
    fr.Check("ECDF steps", "fig_f3_a.csv ecdf", "fig_h2_dist.csv hist", _chk_ecdf),
    fr.Check("ECDF at 0", "fig_f3_a.csv ecdf x=0", "h2.json share_nonpositive, fig_h2_dist.csv share_le_0",
             _chk_ecdf_zero),
    fr.Check("band shares", "fig_f3_a.csv band", "fig_h2_dist.csv hist and share_le_0", _chk_bands),
    fr.Check("overflows", "fig_f3_a.csv overflow and ECDF ends", "fig_h2_dist.csv open bins", _chk_overflow),
    fr.Check("median bar", "fig_f3_a.csv median", "h2.json stat, lo, hi", _chk_median),
]


def run_checks(results_dir: Path = Path("results/p2")):
    return fr.run(CHECKS, results_dir)
