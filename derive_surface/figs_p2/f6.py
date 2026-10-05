"""F6 of Paper 2: the price of capital, H4 (FIGURE_SELECTION section 7, F6; 7.0 x 4.2 in).

a  dose strip: one row per event in the H4 panel (labelled "22 Feb 2025 BTC legacy", the date style of the text),
   one symbol per cell and event pair at 100 x dose (log-%), sells above and buys below the line, median as a bar,
   the band |dose| < 1 log-% with its share of pairs.
b  binned residuals (Frisch-Waugh-Lovell): half spread against post x dose after both fixed effects, 20 equal-count
   bins, line through the origin with slope beta / 100 per log-%, histogram of the residualised regressor below
   (labelled "rows"). Without ``fig_h4_fwl_bins.csv`` the within-event contrasts of the dose terciles, without a line.
c  beta among the placebo betas, with the two registered criteria rebuilt from ``criteria`` (the build refuses when
   they do not give ``rejected``).
d  beta per underlying (exploratory) next to the registered beta; intervals descriptive. The registered row is
   hatched up to max(0, placebo P95), the values of beta at which the rule rejects H4 whatever the p-value (as card
   S3, audit B3); a dashed mark "P95" ends the hatching.

Inputs: ``h4_panel.parquet`` (pairs event x cell), ``results_dir``: ``h4_doses.csv``, ``fig_h4_events.csv``,
``h4.json``, ``h4_placebo.csv``, ``sensitivity_h4.json``, ``fig_h4_fwl_bins.csv`` (optional). Tables:
``fig_f6_a.csv`` ... ``fig_f6_d.csv`` and ``fig_f6_head.csv`` (header line).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from matplotlib import patheffects
from matplotlib.patches import Rectangle
from matplotlib.ticker import MaxNLocator

from . import _kit_f5f6 as kit

NAME = "f6"
WIDTH, HEIGHT = 7.0, 4.2
PANEL = Path("data/p2/derived/h4_panel.parquet")
ALPHA = 0.05
BAND = 1.0                    # |dose| < 1 log-%
N_BINS = 20
X_A = (-46.0, 4.0)
HALO = [patheffects.withStroke(linewidth=2.0, foreground="white")]
BAR_GREY = "#BBBBBB"
BAND_GREY = "#E3E3E3"

# layout in inches
AL, AR = 1.30, 2.98           # a and d (AL: room for the longest row label, "22 Feb 2025 BTC legacy", at print size)
A_TOP, A_H = 0.52, 1.83
D_TOP, D_H = 3.10, 0.70
BL, BR = 4.12, 6.90           # b and c
B_TOP, B_H = 0.44, 1.10
S_GAP, S_H = 0.03, 0.15
C_TOP, C_H = 2.56, 1.02

CAPTION = (
    r"\textbf{The price of capital (H4).} Panel a shows the dose, the change in log capital that a parameter change "
    r"makes to a cell, for each of the \PH{h4-pairs} cell-event pairs of the \PH{h4-events} events in the H4 panel, "
    r"sells above and buys below each line, with the median as a bar. Panel b is the half spread against the "
    r"post-event dose after removing the cell by event and the day by underlying effects, in 20 bins of equal size, "
    r"above a grey histogram of that dose over all observations of the H4 panel; the line shows the estimate "
    r"$\beta$, whose interval is descriptive because the registered $p$ comes from restricted residuals. Panel c "
    r"places $\beta$ among the estimates at 100 placebo dates and lists both registered criteria. Panel d gives "
    r"$\beta$ per underlying, for exploration; in the registered row, hatching marks the values of $\beta$ at which "
    r"the rule rejects H4 whatever its $p$, up to the 95th placebo percentile (P95) or zero, whichever is larger. "
    r"Most doses are close to zero or negative, so $\beta$ is identified from parameter changes that made capital "
    r"cheaper. Doses on the axes are in log per cent, 100 times the change in log capital, so the line in panel b "
    r"has the slope $\beta/100$ per log per cent. To read the slope: capital ten~per~cent cheaper is a dose of "
    r"$-0.105$, or $-10.5$~log per~cent, which predicts a change in the half spread of $-0.105\,\beta$ basis points "
    r"of the index."
)


def event_label(event_id: str, ccy: str, manager: str, day: str) -> str:
    """Row label of panel a, "22 Feb 2025 BTC legacy": the day in the order of the text, month abbreviated."""
    t = pd.Timestamp(day)
    return f"{t.day} {t:%b %Y} {ccy} {'legacy' if manager == 'pm' else 'PM2'}"


def reject_upto(h4: dict) -> float:
    """Upper end of the hatching in the registered row of panel d: H4 is rejected whatever the p-value for every
    beta up to the larger of zero and the placebo 95th percentile (``placebo.p95``), as on card S3 (audit B3)."""
    return max(0.0, float(h4["placebo"]["p95"]))


def _load(rd: Path, name: str):
    return json.loads((Path(rd) / name).read_text())


# =====================================================================================================================
# Tables
# =====================================================================================================================

def pairs(results_dir: Path, panel_path: Path = PANEL) -> pd.DataFrame:
    """Cell and event pairs of the H4 panel with their dose (``h4_doses.csv``) and fills before and after."""
    panel = pd.read_parquet(panel_path, columns=["event_id", "cell", "post"])
    cnt = (panel.assign(post=panel["post"].astype(bool))
           .groupby(["event_id", "cell"])["post"].agg(n_post="sum", n=lambda s: len(s)).reset_index())
    cnt["n_pre"] = cnt["n"] - cnt["n_post"]
    doses = pd.read_csv(Path(results_dir) / "h4_doses.csv")[["event_id", "cell", "dose"]]
    out = cnt.merge(doses, on=["event_id", "cell"], how="left", validate="one_to_one")
    if out["dose"].isna().any():
        raise ValueError("panel pairs without a dose in h4_doses.csv")
    return out[["event_id", "cell", "dose", "n_pre", "n_post"]]


def _event_rows(results_dir: Path) -> pd.DataFrame:
    ev = pd.read_csv(Path(results_dir) / "fig_h4_events.csv")
    ev = ev[ev["n_cells"] > 0].copy()
    ev["event_ts"] = pd.to_datetime(ev["event_utc"]).astype("int64")
    ev["ccy_rank"] = ev["ccy"].map({"BTC": 0, "ETH": 1, "HYPE": 2})
    ev = ev.sort_values(["event_ts", "ccy_rank"], kind="mergesort").reset_index(drop=True)
    ev["row"] = np.arange(len(ev))
    ev["label"] = [event_label(e, c, m, d) for e, c, m, d in zip(ev["event_id"], ev["ccy"], ev["manager"],
                                                                 ev["event_day"])]
    return ev


def table_a(results_dir: Path, panel_path: Path = PANEL) -> pd.DataFrame:
    ev = _event_rows(results_dir)
    p = pairs(results_dir, panel_path).merge(ev[["event_id", "ccy", "manager", "row", "label"]], on="event_id",
                                             how="inner")
    p["side"] = p["cell"].str.split("|").str[1]
    p["dose_logpct"] = 100.0 * p["dose"]
    p["y"] = p["row"] + np.where(p["side"] == "sell", -0.15, 0.15)
    p["mark"] = "pair"
    p["printed"] = ""
    rows = [p]
    med = p.groupby(["event_id", "row", "label"], as_index=False).agg(dose_logpct=("dose_logpct", "median"),
                                                                     value=("dose_logpct", "size"))
    med["mark"] = "median"
    med["y"] = med["row"]
    med["printed"] = med["value"].astype(int).astype(str)          # n pairs at the right
    rows.append(med)
    share = float(np.mean(np.abs(p["dose_logpct"]) < BAND)) if len(p) else np.nan
    rows.append(pd.DataFrame([{"mark": "band", "value": share, "dose_logpct": BAND,
                               "printed": f"|dose| < 1 log-%: {kit.pct(100 * share)} of pairs"}]))
    cols = ["mark", "event_id", "ccy", "manager", "label", "cell", "side", "dose_logpct", "n_pre", "n_post", "row",
            "y", "value", "printed"]
    out = pd.concat(rows, ignore_index=True)
    return out.reindex(columns=cols).sort_values(["mark", "row", "event_id", "cell"], kind="mergesort",
                                                 na_position="last").reset_index(drop=True)


def table_b(results_dir: Path) -> pd.DataFrame:
    rd = Path(results_dir)
    h4 = _load(rd, "h4.json")
    path = rd / "fig_h4_fwl_bins.csv"
    cols = ["mode", "kind", "bin", "event_id", "tercile", "x_mean", "y_mean", "n_rows", "n_fills", "x", "x_hi",
            "count", "y", "fwl_slope", "slope_per_logpct", "printed"]
    if path.exists():
        b = pd.read_csv(path)
        b["mode"] = "bins"
        line = {"mode": "bins", "kind": "line", "slope_per_logpct": float(h4["stat"]) / 100.0,
                "fwl_slope": float(b["fwl_slope"].iloc[0]),
                "printed": f"β = {kit.num(h4['stat'])} bp per log unit\n90{kit.THIN}% interval "
                           f"[{kit.num(h4['lo'], 1)}, {kit.num(h4['hi'], 1)}], descriptive"}
        b = pd.concat([b, pd.DataFrame([line])], ignore_index=True)
        return b.reindex(columns=cols)
    ev = _event_rows(rd)
    rows = []
    for e in ev.itertuples():
        med = np.array([getattr(e, f"t{k}_median_dose") for k in (1, 2, 3)], dtype=float)
        dy = np.array([getattr(e, f"t{k}_y_post") - getattr(e, f"t{k}_y_pre") for k in (1, 2, 3)], dtype=float)
        for k in range(3):
            rows.append({"mode": "contrast", "kind": "contrast", "event_id": e.event_id, "tercile": k + 1,
                         "x": 100.0 * (med[k] - np.nanmean(med)), "y": dy[k] - np.nanmean(dy)})
    rows.append({"mode": "contrast", "kind": "note", "printed": "no fitted line: binned residuals not available"})
    return pd.DataFrame(rows).reindex(columns=cols)


def _group_days(adm: Dict[str, dict], ids: List[str]) -> str:
    vals = sorted({int(adm[i]["days"]) for i in ids if i in adm})
    if not vals:
        return ""
    return str(vals[0]) if len(vals) == 1 else f"{vals[0]} to {vals[-1]}"


def placebo_days_text(h4: dict) -> str:
    adm = h4["placebo"]["admissible_days"]
    parts = []
    for ccy in ("BTC", "ETH", "HYPE"):
        s = _group_days(adm, [k for k in adm if k.startswith(f"{ccy}-pm2-")])
        if s:
            parts.append(f"{ccy} {s}")
    leg = [_group_days(adm, [k for k in adm if k.startswith(f"{c}-pm-")]) for c in ("BTC", "ETH")]
    leg = [s for s in leg if s]
    if leg:
        parts.append("legacy " + " / ".join(leg))
    return "placebo days: " + " · ".join(parts)


def checklist(h4: dict) -> List[Tuple[str, bool]]:
    """The two registered criteria and the verdict, rebuilt from ``criteria`` and checked against beta, p, the
    placebo 95th percentile and ``rejected``; ``ValueError`` when anything disagrees."""
    crit = h4["criteria"]
    beta, p, p95 = float(h4["stat"]), float(h4["p"]), float(h4["placebo"]["p95"])
    c1 = bool(crit["beta_positive"]) and bool(crit["p_le_alpha"])
    c2 = bool(crit["beta_gt_placebo_p95"])
    if c1 != (beta > 0 and p <= ALPHA) or c2 != (beta > p95):
        raise ValueError("H4 criteria in h4.json disagree with beta, p and the placebo 95th percentile")
    rejected = not (c1 and c2)
    if rejected != bool(h4["rejected"]):
        raise ValueError(f"H4 check list gives rejected={rejected}, h4.json says rejected={h4['rejected']}")
    met = {True: "met", False: "not met"}
    return [(f"β > 0 and one-sided wild p ≤ 0.05 (p = {p:.3f}): {met[c1]}", c1),
            (f"β above placebo P95 ({kit.num(p95, 1)}): {met[c2]}", c2),
            ("H4: rejected" if rejected else "H4: not rejected", rejected)]


def table_c(results_dir: Path) -> pd.DataFrame:
    rd = Path(results_dir)
    h4 = _load(rd, "h4.json")
    pl = pd.read_csv(rd / "h4_placebo.csv")
    rows = [{"kind": "placebo", "rep": int(r), "beta": float(b)} for r, b in zip(pl["rep"], pl["beta"])]
    lines = checklist(h4)
    rows += [{"kind": "estimate", "beta": float(h4["stat"]), "printed": "estimate"},
             {"kind": "p95", "beta": float(h4["placebo"]["p95"]), "printed": "placebo P95"},
             {"kind": "p", "beta": float(h4["p"])},
             {"kind": "criterion_1", "value": lines[0][1], "printed": lines[0][0]},
             {"kind": "criterion_2", "value": lines[1][1], "printed": lines[1][0]},
             {"kind": "verdict", "value": lines[2][1], "printed": lines[2][0]},
             {"kind": "placebo_days", "printed": placebo_days_text(h4)}]
    return pd.DataFrame(rows).reindex(columns=["kind", "rep", "beta", "value", "printed"])


def table_d(results_dir: Path) -> pd.DataFrame:
    rd = Path(results_dir)
    h4 = _load(rd, "h4.json")
    sens = _load(rd, "sensitivity_h4.json")
    rows = [{"label": "registered", "source_key": "h4.json", "kind": "registered", "stat": h4["stat"],
             "lo": h4["lo"], "hi": h4["hi"], "n": h4["clusters"], "reject_upto": reject_upto(h4)}]
    for ccy in ("BTC", "ETH", "HYPE"):
        s = sens.get("by_ccy", {}).get(ccy)
        if s is None:
            continue
        rows.append({"label": f"{ccy} only", "source_key": f"sensitivity_h4.json by_ccy.{ccy}",
                     "kind": "exploratory", "stat": s["beta"], "lo": s["lo"], "hi": s["hi"], "n": s["clusters"]})
    out = pd.DataFrame(rows)
    out["printed"] = [f"{kit.num(s)} [{kit.num(lo, 1)}, {kit.num(hi, 1)}]" for s, lo, hi in
                      zip(out["stat"], out["lo"], out["hi"])]
    return out


def table_head(results_dir: Path) -> pd.DataFrame:
    h4 = _load(Path(results_dir), "h4.json")
    vals = {"events": h4["events"], "pairs": h4["cell_events"], "rows": h4["n"], "fills": h4["fills"],
            "fills_in_two_windows": int(h4["n"]) - int(h4["fills"]), "day_clusters": h4["clusters"],
            "day_ccy_effects": h4["day_ccy"]}
    t = kit.thousands
    line1 = (f"{t(vals['events'])} events · {t(vals['pairs'])} cell-event pairs · {t(vals['rows'])} rows "
             f"from {t(vals['fills'])} fills ({t(vals['fills_in_two_windows'])} in two windows)")
    line2 = f"{t(vals['day_clusters'])} day clusters · {t(vals['day_ccy_effects'])} day × underlying effects"
    out = pd.DataFrame({"key": list(vals), "value": list(vals.values())})
    out["printed"] = ""
    return pd.concat([out, pd.DataFrame([{"key": "line1", "printed": line1}, {"key": "line2", "printed": line2}])],
                     ignore_index=True)


# =====================================================================================================================
# Figure
# =====================================================================================================================

def _panel_a(fig, a: pd.DataFrame) -> None:
    kit.letter(fig, 0.02, 0.33, "a")
    ax = kit.axes_at(fig, AL, A_TOP, AR - AL, A_H)
    pr = a[a["mark"] == "pair"]
    med = a[a["mark"] == "median"].sort_values("row")
    n = len(med)
    lo = min(X_A[0], float(np.floor(pr["dose_logpct"].min())) - 2 if len(pr) else X_A[0])
    hi = max(X_A[1], float(np.ceil(pr["dose_logpct"].max())) + 2 if len(pr) else X_A[1])
    ax.axvspan(-BAND, BAND, color=BAND_GREY, linewidth=0, zorder=0)
    for m in ("pm", "pm2"):
        color = kit.MANAGER[m][0]
        s = pr[(pr["manager"] == m) & (pr["side"] == "sell")]
        ax.plot(s["dose_logpct"], s["y"], linestyle="none", marker="v", markersize=2.5, markerfacecolor=color,
                markeredgecolor=color, markeredgewidth=0.4, zorder=3)
        s = pr[(pr["manager"] == m) & (pr["side"] == "buy")]
        ax.plot(s["dose_logpct"], s["y"], linestyle="none", marker="^", markersize=2.5, markerfacecolor="white",
                markeredgecolor=color, markeredgewidth=0.5, zorder=3)
    ax.vlines(med["dose_logpct"], med["row"] - 0.36, med["row"] + 0.36, color="black", linewidth=1.3, zorder=4)
    for r in med.itertuples():
        ax.annotate(r.printed, (1.0, r.row), xycoords=("axes fraction", "data"), xytext=(4, 0),
                    textcoords="offset points", ha="left", va="center", fontsize=kit.FS_MIN, color=kit.GREY)
    ax.annotate("pairs", (1.0, -0.62), xycoords=("axes fraction", "data"), xytext=(4, 0), textcoords="offset points",
                ha="left", va="bottom", fontsize=kit.FS_MIN, color=kit.GREY)
    band = a[a["mark"] == "band"].iloc[0]
    ax.annotate(band["printed"], (BAND, -0.62), xycoords="data", xytext=(0, 0), textcoords="offset points",
                ha="right", va="bottom", fontsize=kit.FS_MIN, annotation_clip=False)
    ax.set_xlim(lo, hi)
    ax.set_ylim(n - 0.5, -0.5)
    ax.set_yticks(med["row"])
    ax.set_yticklabels(med["label"])
    ax.tick_params(axis="y", length=0, pad=3)
    ax.spines["left"].set_visible(False)
    ax.set_xticks([t for t in (-40, -30, -20, -10, 0) if lo <= t <= hi])
    ax.set_xlabel("dose: change in log capital of the cell, log-%\n(< 0: capital got cheaper)", linespacing=1.1)


def _panel_b(fig, b: pd.DataFrame) -> None:
    kit.letter(fig, 3.50, 0.33, "b")
    ax = kit.axes_at(fig, BL, B_TOP, BR - BL, B_H)
    mode = str(b["mode"].iloc[0])
    ax.axhline(0, color="#999999", linewidth=0.4, zorder=0)
    ax.axvline(0, color="#999999", linewidth=0.4, zorder=0)
    if mode == "bins":
        bins = b[b["kind"] == "bin"]
        hist = b[b["kind"] == "hist"]
        line = b[b["kind"] == "line"].iloc[0]
        x0, x1 = float(hist["x"].min()), float(hist["x_hi"].max())
        pad = 0.03 * (x1 - x0)
        xlim = (x0 - pad, x1 + pad)
        size = 14.0 * bins["n_fills"].astype(float) / float(bins["n_fills"].max())
        ax.scatter(bins["x_mean"], bins["y_mean"], s=size, color="black", linewidths=0, zorder=3)
        xs = np.array(xlim)
        ax.plot(xs, float(line["slope_per_logpct"]) * xs, color="black", linewidth=1.0, zorder=2)
        y = np.concatenate([bins["y_mean"].to_numpy(float), float(line["slope_per_logpct"]) * xs])
        note = str(line["printed"])
        ax.set_ylabel("half spread,\nresidualised,\nbp of index", linespacing=1.1)
        ax.tick_params(axis="x", labelbottom=False)
        strip = kit.axes_at(fig, BL, B_TOP + B_H + S_GAP, BR - BL, S_H)
        strip.bar(hist["x"], hist["count"], width=hist["x_hi"] - hist["x"], align="edge", color=BAR_GREY,
                  linewidth=0)
        strip.set_xlim(*xlim)
        strip.set_yticks([])
        strip.spines["left"].set_visible(False)
        strip.text(0.0, 0.5, "rows", transform=strip.transAxes, ha="right", va="center", fontsize=kit.FS_MIN,
                   color=kit.GREY)                          # the strip is the histogram of the rows (caption)
        strip.set_xlabel("post × dose, residualised, log-%")
        ax.set_xlim(*xlim)
    else:
        c = b[b["kind"] == "contrast"]
        ax.scatter(c["x"], c["y"], s=10, facecolors="none", edgecolors=kit.GREY, linewidths=0.6, zorder=3)
        y = c["y"].to_numpy(float)
        note = str(b.loc[b["kind"] == "note", "printed"].iloc[0])
        ax.set_ylabel("within-event\ncontrast, bp of index\n(no day effects)", linespacing=1.1)
        ax.set_xlabel("dose relative to the event mean, log-%")
    y = y[np.isfinite(y)]
    lo, hi = (float(y.min()), float(y.max())) if len(y) else (-1.0, 1.0)
    span = max(hi - lo, 1e-9)
    ax.set_ylim(lo - 0.08 * span, hi + 0.62 * span)
    ax.text(0.02, 0.97, note, transform=ax.transAxes, ha="left", va="top", fontsize=kit.FS_MIN, linespacing=1.15,
            path_effects=HALO, zorder=5)


def _panel_c(fig, c: pd.DataFrame) -> None:
    kit.letter(fig, 3.50, C_TOP - 0.45, "c")
    lines = c[c["kind"].isin(["criterion_1", "criterion_2", "verdict"])]
    for k, r in enumerate(lines.itertuples()):
        kit.fig_text(fig, BL - 0.25, C_TOP - 0.44 + 0.125 * k, r.printed, ha="left",
                     fontweight="bold" if r.kind == "verdict" else "normal")
    ax = kit.axes_at(fig, BL, C_TOP, BR - BL, C_H)
    pl = c.loc[c["kind"] == "placebo", "beta"].to_numpy(float)
    pl = pl[np.isfinite(pl)]
    beta = float(c.loc[c["kind"] == "estimate", "beta"].iloc[0])
    p95 = float(c.loc[c["kind"] == "p95", "beta"].iloc[0])
    edges = np.linspace(min(pl.min(), beta), max(pl.max(), beta), 21)
    counts, _ = np.histogram(pl, bins=edges)
    ax.bar(edges[:-1], counts, width=np.diff(edges), align="edge", color=BAR_GREY, linewidth=0, zorder=1)
    top = max(int(counts.max()), 1)
    ax.set_ylim(0, top * 1.52)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=4))
    ax.axvline(p95, color="black", linestyle="--", linewidth=0.8, zorder=3)
    ax.axvline(beta, color="black", linestyle="-", linewidth=1.5, zorder=3)
    pad = 0.04 * (edges[-1] - edges[0])
    ax.set_xlim(edges[0] - pad, edges[-1] + pad)
    x0, x1 = ax.get_xlim()
    per_in = (x1 - x0) / (BR - BL)                                   # data units per inch
    per_in_y = top * 1.52 / C_H                                       # counts per inch
    line_h = kit.FS_MIN / 72 * 1.2 * per_in_y                         # one text line, in counts
    spans, ys = {}, {}
    for x, other, text, yy in ((beta, p95, "estimate", 1.40), (p95, beta, "placebo\nP95", 1.10)):
        w, pad_x = _text_width_in(text) * per_in, 3 / 72 * per_in
        right = _label_side(x, other, w, pad_x, x0, x1) == "right"
        spans[text] = (x + pad_x, x + pad_x + w) if right else (x - pad_x - w, x - pad_x)
        y = top * yy
        if text != "estimate":
            # lift the P95 label clear of the bars under it, unless that would run into the estimate label
            lo, hi = spans[text]
            under = counts[(edges[1:] > lo) & (edges[:-1] < hi)]
            lifted = max(y, (float(under.max()) if under.size else 0.0) + line_h * 1.1)
            e_lo, e_hi = spans["estimate"]
            clash = lo < e_hi and e_lo < hi and lifted + line_h > ys["estimate"] - line_h / 2
            y = y if clash else lifted
        ys[text] = y
        ax.annotate(text, (x, y), xytext=(3 if right else -3, 0), textcoords="offset points",
                    ha="left" if right else "right", va="center", fontsize=kit.FS_MIN, linespacing=1.0,
                    path_effects=HALO, zorder=4)
    ax.set_ylabel("placebo dates")
    ax.set_xlabel("β at 100 placebo dates, bp of index per log unit")
    days = c.loc[c["kind"] == "placebo_days", "printed"].iloc[0]
    kit.fig_text(fig, BL - 0.25, C_TOP + C_H + 0.30, days, ha="left", color=kit.GREY)


def _text_width_in(text: str, size: float = kit.FS_MIN) -> float:
    """Rough width of the longest line (DejaVu Sans, 0.6 em per character)."""
    return max(len(line) for line in text.split("\n")) * 0.6 * size / 72.0


def _label_side(x: float, other: float, width: float, pad: float, x0: float, x1: float) -> str:
    """Right of the line if the label fits inside the axes there and does not cross the other line, else left."""
    fits_right = x + pad + width <= x1 and not (x < other < x + pad + width)
    fits_left = x - pad - width >= x0 and not (x - pad - width < other < x)
    return "right" if fits_right or not fits_left else "left"


def _panel_d(fig, d: pd.DataFrame) -> None:
    kit.letter(fig, 0.02, D_TOP - 0.27, "d")
    kit.fig_text(fig, AL, D_TOP - 0.26, "β per underlying · 90 % intervals, descriptive", ha="left")
    ax = kit.axes_at(fig, AL, D_TOP, AR - AL, D_H)
    n = len(d)
    reg = d[d["kind"] == "registered"].iloc[0]
    edge = float(reg["reject_upto"])                            # max(0, placebo P95)
    top = max(float(reg["hi"]), 0.0, edge)
    span = top - min(float(reg["lo"]), 0.0)
    lo = min(float(reg["lo"]), 0.0) - 0.25 * span
    hi = top + 0.25 * span
    for i, r in enumerate(d.itertuples()):
        explo = r.kind == "exploratory"
        if explo:
            ax.axhspan(i - 0.5, i + 0.5, color=kit.LIGHT, linewidth=0, zorder=0)
        else:
            ax.add_patch(Rectangle((lo, i - 0.4), edge - lo, 0.8, facecolor="none", edgecolor=BAR_GREY, hatch="////",
                                   linewidth=0, zorder=0.5))
            if edge > 0.0:                                      # the hatching ends at the placebo P95
                ax.plot([edge, edge], [i - 0.4, i + 0.4], color="black", linestyle="--", linewidth=0.8, zorder=1)
                ax.annotate("P95", (edge, i), xytext=(3, 0), textcoords="offset points", ha="left", va="center",
                            fontsize=kit.FS_MIN, path_effects=HALO, zorder=4)
        color = kit.GREY if explo else "black"
        lw = 1.0 if explo else 2.0
        a, b = max(float(r.lo), lo), min(float(r.hi), hi)
        ax.plot([a, b], [i, i], color=color, linewidth=lw, solid_capstyle="butt", zorder=2)
        if float(r.lo) < lo:
            ax.plot([lo], [i], marker="<", markersize=3.5, color=color, zorder=2, clip_on=False)
        if float(r.hi) > hi:
            ax.plot([hi], [i], marker=">", markersize=3.5, color=color, zorder=2, clip_on=False)
        ax.plot([r.stat], [i], marker="o", markersize=3.6 if explo else 4.0, markerfacecolor="white" if explo
                else "black", markeredgecolor=color, markeredgewidth=0.8, zorder=3)
        ax.annotate(str(int(r.n)), (1.0, i), xycoords=("axes fraction", "data"), xytext=(6, 0),
                    textcoords="offset points", ha="left", va="center", fontsize=kit.FS_MIN, color=kit.GREY)
    ax.annotate("clusters", (1.0, -0.55), xycoords=("axes fraction", "data"), xytext=(6, 0),
                textcoords="offset points", ha="left", va="bottom", fontsize=kit.FS_MIN, color=kit.GREY)
    ax.axvline(0.0, color="black", linestyle="--", linewidth=0.8, zorder=1)
    ax.set_xlim(lo, hi)
    ax.set_ylim(n - 0.5, -0.5)
    ax.set_yticks(range(n))
    labels = ax.set_yticklabels(d["label"])
    for t, k in zip(labels, d["kind"]):
        t.set_fontweight("bold" if k == "registered" else "normal")
        t.set_color("black" if k == "registered" else kit.GREY)
    ax.tick_params(axis="y", length=0, pad=6)                   # room for the arrow heads at the axis ends
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("β, bp of index per log unit of capital")


def figure(results_dir: Path = Path("results/p2"), panel_path: Path = PANEL):
    """The figure (not saved); raises ``ValueError`` when the H4 check list disagrees with ``h4.json``."""
    rd = Path(results_dir)
    a, b, c, d, head = (table_a(rd, panel_path), table_b(rd), table_c(rd), table_d(rd), table_head(rd))
    fig = kit.new_figure(WIDTH, HEIGHT)
    hl = head.set_index("key")["printed"]
    kit.fig_text(fig, 0.02, 0.03, hl["line1"], ha="left")
    kit.fig_text(fig, 0.02, 0.15, hl["line2"], ha="left")
    kit.fig_text(fig, BR, 0.15, "panel a: \u25bc maker sells (short) \u00b7 \u25b3 maker buys (long) \u00b7 "
                 "colour = manager", ha="right")
    _panel_a(fig, a)
    _panel_b(fig, b)
    _panel_c(fig, c)
    _panel_d(fig, d)
    return fig


def build(out_dir: Path = Path("paper2/figures"), results_dir: Path = Path("results/p2"),
          panel_path: Path = PANEL) -> List[Path]:
    """Write ``fig_f6_{a,b,c,d,head}.csv`` to ``results_dir`` and ``f6.pdf``/``f6.png`` to ``out_dir``."""
    rd = Path(results_dir)
    fig = figure(rd, panel_path)                              # refuses before anything is written
    paths = [kit.write_csv(table_a(rd, panel_path), rd, "fig_f6_a.csv"), kit.write_csv(table_b(rd), rd, "fig_f6_b.csv"),
             kit.write_csv(table_c(rd), rd, "fig_f6_c.csv"), kit.write_csv(table_d(rd), rd, "fig_f6_d.csv"),
             kit.write_csv(table_head(rd), rd, "fig_f6_head.csv")]
    return paths + kit.save(fig, NAME, Path(out_dir))


# =====================================================================================================================
# Checks: what the figure prints (fig_f6_*.csv) against the sources
# =====================================================================================================================

def _fa(rd: Path) -> pd.DataFrame:
    return pd.read_csv(rd / "fig_f6_a.csv", keep_default_na=False, na_values=[""])


def _fig_pairs(rd: Path) -> pd.DataFrame:
    a = _fa(rd)
    return a[a["mark"] == "pair"]


def _src_pairs(rd: Path, panel_path: Path) -> pd.DataFrame:
    """Independent join: distinct (event_id, cell) of the panel with the dose of h4_doses.csv."""
    panel = pd.read_parquet(panel_path, columns=["event_id", "cell"]).drop_duplicates()
    doses = pd.read_csv(rd / "h4_doses.csv").set_index(["event_id", "cell"])["dose"]
    panel["dose_logpct"] = [100.0 * doses[(e, c)] for e, c in zip(panel["event_id"], panel["cell"])]
    return panel


def _dose_stats(x: pd.Series) -> List[float]:
    x = x.to_numpy(float)
    return [float(np.median(x)), float(x.min()), float(x.max()), 100 * float(np.mean(x > 0)),
            100 * float(np.mean(x < -1.0)), 100 * float(np.mean(np.abs(x) < 1.0))]


def _src_head(rd: Path, panel_path: Path) -> Dict[str, int]:
    p = pd.read_parquet(panel_path, columns=["fill_key", "event_id", "cell", "day", "ccy"])
    return {"events": int(p["event_id"].nunique()), "pairs": int(p.groupby(["event_id", "cell"]).ngroups),
            "rows": int(len(p)), "fills": int(p["fill_key"].nunique()),
            "fills_in_two_windows": int(len(p) - p["fill_key"].nunique()), "day_clusters": int(p["day"].nunique()),
            "day_ccy_effects": int(p.groupby(["day", "ccy"]).ngroups)}


def _fig_head(rd: Path) -> Dict[str, int]:
    h = pd.read_csv(rd / "fig_f6_head.csv")
    h = h[h["value"].notna()]
    return {k: int(v) for k, v in zip(h["key"], h["value"])}


def _fc(rd: Path) -> pd.DataFrame:
    return pd.read_csv(rd / "fig_f6_c.csv", keep_default_na=False, na_values=[""])


def _fd(rd: Path) -> Dict[str, list]:
    d = pd.read_csv(rd / "fig_f6_d.csv")
    return {r.label: [r.stat, r.lo, r.hi, int(r.n)] for r in d.itertuples()}


def _src_d(rd: Path) -> Dict[str, list]:
    h4, sens = _load(rd, "h4.json"), _load(rd, "sensitivity_h4.json")
    out = {"registered": [h4["stat"], h4["lo"], h4["hi"], int(h4["clusters"])]}
    for ccy, s in sens.get("by_ccy", {}).items():
        out[f"{ccy} only"] = [s["beta"], s["lo"], s["hi"], int(s["clusters"])]
    return out


EXPECTED_PAIRS = {
    "BTC-pm-20250222": 25, "BTC-pm2-20260108": 25, "BTC-pm2-20260123": 27, "BTC-pm2-20260524": 38,
    "BTC-pm2-20260820": 43, "ETH-pm-20250222": 50, "ETH-pm2-20260108": 37, "ETH-pm2-20260123": 40,
    "ETH-pm2-20260524": 54, "ETH-pm2-20260820": 52, "HYPE-pm2-20260508": 29, "HYPE-pm2-20260524": 35,
    "HYPE-pm2-20260820": 20,
}


def checks(panel_path: Path = PANEL) -> list:
    """Check list of F6; the panel path is a parameter so that the tests can point it at synthetic data."""
    pp = Path(panel_path)
    return [
        kit.check("f6.a.rows", "rows of a = events with panel cells (fig_h4_events.csv n_cells > 0)",
                  lambda rd: int(_fig_pairs(rd)["event_id"].nunique()),
                  lambda rd: int((pd.read_csv(rd / "fig_h4_events.csv")["n_cells"] > 0).sum()), expected=13),
        kit.check("f6.a.pairs_per_event", "symbols per row = n_cells of fig_h4_events.csv",
                  lambda rd: _fig_pairs(rd).groupby("event_id").size().to_dict(),
                  lambda rd: pd.read_csv(rd / "fig_h4_events.csv").query("n_cells > 0").set_index("event_id")
                  ["n_cells"].to_dict(), expected=EXPECTED_PAIRS),
        kit.check("f6.a.pairs_total", "symbols in a = h4.json cell_events",
                  lambda rd: int(len(_fig_pairs(rd))), lambda rd: int(_load(rd, "h4.json")["cell_events"]),
                  expected=475),
        kit.check("f6.a.doses", "dose of every symbol = h4_doses.csv on the panel pairs, log-%",
                  lambda rd: _fig_pairs(rd).set_index(["event_id", "cell"])["dose_logpct"].sort_index().tolist(),
                  lambda rd: _src_pairs(rd, pp).set_index(["event_id", "cell"])["dose_logpct"].sort_index().tolist(),
                  rel=1e-12),
        kit.check("f6.a.dose_stats", "median, min, max (log-%); % positive, % below -1, % with |dose| < 1",
                  lambda rd: _dose_stats(_fig_pairs(rd)["dose_logpct"]),
                  lambda rd: _dose_stats(_src_pairs(rd, pp)["dose_logpct"]),
                  expected=[-0.634, -44.21, 2.20, 11.2, 48.6, 44.4], expected_tol=0.051),
        kit.check("f6.a.band", "printed share of pairs with |dose| < 1 log-%",
                  lambda rd: _fa(rd).query("mark == 'band'")["printed"].iloc[0],
                  lambda rd: f"|dose| < 1 log-%: {kit.pct(_dose_stats(_src_pairs(rd, pp)['dose_logpct'])[5])} of pairs"),
        kit.check("f6.a.medians", "median bar per row = median dose of the event's pairs",
                  lambda rd: _fa(rd).query("mark == 'median'").set_index("event_id")["dose_logpct"].sort_index()
                  .tolist(),
                  lambda rd: _src_pairs(rd, pp).groupby("event_id")["dose_logpct"].median().sort_index().tolist()),
        kit.check("f6.head.panel", "header numbers = h4_panel.parquet",
                  _fig_head, lambda rd: _src_head(rd, pp),
                  expected={"events": 13, "pairs": 475, "rows": 91446, "fills": 84919, "fills_in_two_windows": 6527,
                            "day_clusters": 141, "day_ccy_effects": 322}),
        kit.check("f6.head.h4", "header numbers = h4.json",
                  _fig_head, lambda rd: (lambda h: {"events": h["events"], "pairs": h["cell_events"], "rows": h["n"],
                                                    "fills": h["fills"], "fills_in_two_windows": h["n"] - h["fills"],
                                                    "day_clusters": h["clusters"], "day_ccy_effects": h["day_ccy"]})(
                      _load(rd, "h4.json"))),
        kit.check("f6.b.line", "slope of the line x 100 = h4.json stat (beta)",
                  lambda rd: 100 * float(pd.read_csv(rd / "fig_f6_b.csv").query("kind == 'line'")
                                         ["slope_per_logpct"].iloc[0]),
                  lambda rd: float(_load(rd, "h4.json")["stat"]), rel=1e-8),
        kit.check("f6.b.fwl_slope", "fwl_slope of fig_h4_fwl_bins.csv = h4.json stat",
                  lambda rd: float(pd.read_csv(rd / "fig_f6_b.csv").query("kind == 'line'")["fwl_slope"].iloc[0]),
                  lambda rd: float(_load(rd, "h4.json")["stat"]), rel=1e-8),
        kit.check("f6.b.bins", "20 bins covering all panel rows (h4.json n)",
                  lambda rd: [int((pd.read_csv(rd / "fig_f6_b.csv")["kind"] == "bin").sum()),
                              int(pd.read_csv(rd / "fig_f6_b.csv").query("kind == 'bin'")["n_rows"].sum())],
                  lambda rd: [N_BINS, int(_load(rd, "h4.json")["n"])]),
        kit.check("f6.b.printed", "printed beta and interval = h4.json",
                  lambda rd: pd.read_csv(rd / "fig_f6_b.csv").query("kind == 'line'")["printed"].iloc[0],
                  lambda rd: (lambda h: f"β = {kit.num(h['stat'])} bp per log unit\n90{kit.THIN}% interval "
                                        f"[{kit.num(h['lo'], 1)}, {kit.num(h['hi'], 1)}], descriptive")(
                      _load(rd, "h4.json"))),
        kit.check("f6.c.placebo", "placebo betas in the histogram = h4_placebo.csv",
                  lambda rd: sorted(_fc(rd).query("kind == 'placebo'")["beta"].tolist()),
                  lambda rd: sorted(pd.read_csv(rd / "h4_placebo.csv")["beta"].tolist())),
        kit.check("f6.c.n_placebo", "finite placebo betas in the histogram = finite betas of h4_placebo.csv",
                  lambda rd: int(np.isfinite(_fc(rd).query("kind == 'placebo'")["beta"]).sum()),
                  lambda rd: int(np.isfinite(pd.read_csv(rd / "h4_placebo.csv")["beta"]).sum()), expected=100),
        kit.check("f6.c.p95", "P95 line = numpy quantile of h4_placebo.csv = h4.json placebo.p95",
                  lambda rd: [float(_fc(rd).query("kind == 'p95'")["beta"].iloc[0])] * 2,
                  lambda rd: [float(_load(rd, "h4.json")["placebo"]["p95"]),
                              float(np.quantile(pd.read_csv(rd / "h4_placebo.csv")["beta"].dropna(), 0.95))]),
        kit.check("f6.c.estimate", "estimate line = h4.json stat",
                  lambda rd: float(_fc(rd).query("kind == 'estimate'")["beta"].iloc[0]),
                  lambda rd: float(_load(rd, "h4.json")["stat"])),
        kit.check("f6.c.criteria", "check list = h4.json criteria (p, beta > 0, beta > P95)",
                  lambda rd: [bool(_fc(rd).query("kind == 'criterion_1'")["value"].iloc[0] in (True, "True")),
                              bool(_fc(rd).query("kind == 'criterion_2'")["value"].iloc[0] in (True, "True")),
                              float(_fc(rd).query("kind == 'p'")["beta"].iloc[0])],
                  lambda rd: (lambda h: [bool(h["criteria"]["beta_positive"] and h["criteria"]["p_le_alpha"]),
                                         bool(h["criteria"]["beta_gt_placebo_p95"]), float(h["p"])])(
                      _load(rd, "h4.json"))),
        kit.check("f6.c.verdict", "printed verdict = h4.json rejected",
                  lambda rd: _fc(rd).query("kind == 'verdict'")["printed"].iloc[0],
                  lambda rd: "H4: rejected" if _load(rd, "h4.json")["rejected"] else "H4: not rejected"),
        kit.check("f6.c.placebo_days", "placebo days per timeline = h4.json placebo.admissible_days",
                  lambda rd: _fc(rd).query("kind == 'placebo_days'")["printed"].iloc[0],
                  lambda rd: placebo_days_text(_load(rd, "h4.json")),
                  expected="placebo days: BTC 54 · ETH 10 · HYPE 67 · legacy 363 / 319"),
        kit.check("f6.d.rows", "forest rows = h4.json and sensitivity_h4.json by_ccy (stat, lo, hi, clusters)",
                  _fd, _src_d),
        kit.check("f6.d.hatch", "hatching of the registered row ends at max(0, h4.json placebo.p95)",
                  lambda rd: float(pd.read_csv(rd / "fig_f6_d.csv").query("kind == 'registered'")["reject_upto"]
                                   .iloc[0]),
                  lambda rd: max(0.0, float(_load(rd, "h4.json")["placebo"]["p95"]))),
    ]


CHECKS = checks()
