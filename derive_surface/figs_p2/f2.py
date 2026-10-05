"""F2 of Paper 2: the map in two denominators, H1 (docs/paper2/FIGURE_SELECTION.md, sections 6 and 7,
slot F2).

Panel a takes the full width on top; b and c share the row below it, b on the left, c on the right.

a  Six maps (maker sells above, maker buys below; BTC, ETH, HYPE) of net edge per unit of PM2 capital, ``B_bp`` of
   ``results/p2/h1_cells.csv``, grey by log|B| per row (floor 1 bp), negative cells hatched. The sells print in bp,
   the buys in per cent (``ROW_UNIT``): in bp a buy row reads "-418 -397 -109 -255", four characters with a true
   minus that did not fit the 19.3 pt cells of round 1 side by side.
b  Rank by edge per notional against rank by edge per PM2 capital for the occupied cells (rank 1 top right), the
   diagonal (dashed), the sign lines after the cells with positive edge (dotted) and the rank intervals of the ten
   largest moves (solid, with end ticks).
c  The registered test (``h1.json``) as a forest after section 6.5 (``ruler``) on the range of rho that its rows
   need (``rho_axis``: 0.4 to 1.0 unless an interval reaches lower) with the sensitivities and exploratory
   rows of ``sensitivity.json``; the rows ``edge > 0 only`` / ``edge <= 0 only`` and the band ``sign pattern alone``
   come from ``sensitivity.json["h1_sign"]`` and are left out while that entry is missing (section 10); likewise the
   row ``without RFQ fills`` (``sensitivity.json["i_rfq"]``, audit A12) and the Addendum 6 row ``RFQ fee over legs``
   (``sensitivity.json["c2_rfq_package"]``, the fee of an RFQ package spread over its legs).

The figure layer only counts and sorts; every statistic is read from ``results/p2``.

    python3 -m derive_surface.figs_p2.f2 [--check]
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402

from derive_surface import figstyle  # noqa: E402
from derive_surface.figs_p2._print import print_width, to_print  # noqa: E402
from derive_surface.figs_p2 import f1 as base  # noqa: E402
from derive_surface.markouts import DELTA_LABELS, TENOR_LABELS  # noqa: E402

log = logging.getLogger(__name__)

SLOT = "f2"
WIDTH, HEIGHT = figstyle.DOUBLE, 6.2
FS_MIN = base.FS_MIN
INK, GREY, HEAD = base.INK, base.GREY, base.HEAD
LINE_GREY = "#808080"
BAND_GREY = "#D4D4D4"
EXPLORATORY_BAND = "#F0F0F0"
HATCH_GREY = "#BBBBBB"
MINUS = "\u2212"       # the true minus, as in every other figure
# Unit of the printed number per map row: (label, factor on B_bp). In bp the buy row holds runs such as -418 -397
# -109 -255, four characters of 17.9 pt ink each with the true minus, in the 19.3 pt cells of round 1; in per cent
# they are -4.2 -4.0 -1.1 -2.6 (15.7 pt), and the large buys gain a digit (5k bp prints as 50). The sells keep bp:
# their small cells (0.1 bp) would round away in per cent.
ROW_UNIT = {"sell": ("bp", 1.0), "buy": ("%", 0.01)}
CCYS, SIDES = base.CCYS, base.SIDES
SIDE_TITLE = {"sell": "maker sells (short)",
              "buy": "maker buys (long):\ncapital ≈ premium OTM"}      # OTM: out of the money (caption)
HEADER = ("number = net edge per unit of PM2 capital, per fill: bp for sells, % for buys\n"
          "hatched = negative · × = under 200 fills · pooled over four regimes")
X_RHO = (0.4, 1.0)                       # panel c: the range its rows need (``rho_axis``)
RHO_TICKS = (0.5, 0.75, 1.0)
RHO_MARGIN = 0.02                        # an interval end keeps this much air to the left edge of the axis
N_TOP = 10

# (label, file, key in sensitivity.json, kind); kind: registered, sensitivity (named in the preregistration or an
# addendum), exploratory
FOREST_ROWS = [
    ("registered", "h1", None, "registered"),
    ("maintenance margin", "sens", "b_mm.h1_pm2_mm", "sensitivity"),
    ("companion net edge", "sens", "c_p1_net_edge.h1_pm2", "sensitivity"),
    ("RFQ fee over legs", "sens", "c2_rfq_package.h1_pm2", "sensitivity"),        # Addendum 6
    ("per day to expiry", "sens", "f_time.to_expiry", "exploratory"),
    ("per holding time", "sens", "f_time.holding", "exploratory"),
    ("SM capital", "sens", "a_maps.sm_pm2_window", "exploratory"),
    ("legacy PM capital", "sens", "a_maps.pm_pm2_window", "exploratory"),
    ("BTC only", "sens", "g_by_ccy.pm2_BTC", "exploratory"),
    ("ETH only", "sens", "g_by_ccy.pm2_ETH", "exploratory"),
    ("HYPE only", "sens", "g_by_ccy.pm2_HYPE", "exploratory"),
    ("without RFQ fills", "sens", "i_rfq.h1_pm2_no_rfq", "exploratory"),
    ("edge > 0 only", "sens", "h1_sign.within_pos", "exploratory"),
    ("edge ≤ 0 only", "sens", "h1_sign.within_nonpos", "exploratory"),
]
OPTIONAL_KEYS = {"h1_sign.within_pos", "h1_sign.within_nonpos",   # section 10: rows drop while missing
                 "i_rfq.h1_pm2_no_rfq", "c2_rfq_package.h1_pm2"}
LABEL_MAX = 18                                                     # section 6.5
N_TITLE = "n"                                                      # head of the n column (cells)
BAND_KEY = "h1_sign.sign_floor"
BAND_LABEL = "sign pattern alone"

CAPTION = (
    "The map in two denominators (H1). Panel a is net edge per unit of PM2 capital, per fill, for every cell of "
    "the PM2 window by underlying and maker side, in basis points for maker sells and in per cent for maker buys; "
    "negative cells are hatched and an empty cross marks fewer than 200 fills. For a maker buy the denominator is "
    "about the premium when the option is out of the money and less in the money; the lower row is shaded on its "
    "own scale. The map per notional is Figure~\\PH{p1-map-fig} of the companion paper. Panel b ranks the "
    "\\PH{h1-cells} occupied cells by edge per notional and by edge per PM2 capital; because capital is positive in "
    "every cell, the \\PH{h1-pos} cells with positive edge come first in both rankings, and the dotted lines mark "
    "that boundary. Crosses give the 90~per~cent rank intervals of the ten largest moves. Panel c is the "
    "registered test: Spearman's $\\rho$ with its 90~per~cent day-cluster interval, which is narrower than its "
    "circle and printed above the panel, set against the threshold of 0.5. The hatched stretch of the registered "
    "row, right of the threshold, is the rejection region: the rule rejects H1 if the interval reaches into it. "
    "Sensitivities follow and then, on grey, exploratory rows; n is the number of cells in a row, and in the rows "
    "by the sign of the edge the cells are chosen again in every replicate. The grey band is the $\\rho$ of the "
    "sign pattern alone, with ranks shuffled within each sign group."
)


# =====================================================================================================================
# Formatting, verdict, selection
# =====================================================================================================================

def fmt_edge(v: float) -> str:
    """At most four characters (section 7 F2): one decimal under 10, whole numbers under 1 000, whole thousands;
    negative numbers carry the true minus."""
    if v is None or not np.isfinite(v):
        return ""
    sign = MINUS if v < 0 else ""
    a = abs(float(v))
    if round(a, 1) < 10:
        return f"{sign}{a:.1f}"
    if round(a) < 1000:
        return f"{sign}{round(a):.0f}"
    return f"{sign}{round(a / 1000):.0f}k"


def printed_cell(side: str, b_bp: float) -> str:
    """The number a map cell prints: ``B_bp`` in the unit of its row (``ROW_UNIT``)."""
    return fmt_edge(float(b_bp) * ROW_UNIT[side][1])


def verdict(h: dict, *, side: str) -> bool:
    """Re-apply the registered rule to the interval and require it to match ``h["rejected"]``.

    ``side="upper"``: rejected if the upper bound is at least the threshold (H1, H2); ``"lower"``: rejected if the
    lower bound is at most the threshold (H3). The rule text must name that bound."""
    rule = str(h.get("rule", ""))
    thr = float(h["threshold"])
    if side == "upper":
        if "upper bound" not in rule or ">=" not in rule:
            raise ValueError(f"rule does not reject on the upper bound: {rule!r}")
        rej = float(h["hi"]) >= thr
    elif side == "lower":
        if "lower bound" not in rule or "<=" not in rule:
            raise ValueError(f"rule does not reject on the lower bound: {rule!r}")
        rej = float(h["lo"]) <= thr
    else:
        raise ValueError(f"unknown side {side!r}")
    if bool(rej) != bool(h["rejected"]):
        raise ValueError(f"verdict from rule and bounds ({rej}) differs from rejected = {h['rejected']}")
    return bool(rej)


def header_text(h: dict, rejected: bool) -> str:
    return (f"registered: {float(h['stat']):.2f} [{float(h['lo']):.2f}, {float(h['hi']):.2f}] → "
            f"{'rejected' if rejected else 'not rejected'}")


def rho_axis(c: pd.DataFrame, threshold: float) -> Tuple[Tuple[float, float], List[float]]:
    """x range and ticks of panel c from its rows (``table_c``): ``X_RHO`` with ``RHO_TICKS`` while every interval,
    estimate, the band and the threshold lie at least ``RHO_MARGIN`` right of its left edge; otherwise the left edge
    drops to the next tenth below the lowest of them (not below -1) and the ticks run every 0.5 down from 1.0."""
    keep = c["kind"].isin(["registered", "sensitivity", "exploratory", "band"])
    vals = [float(threshold)] + [float(v) for v in c.loc[keep, ["lo", "stat"]].to_numpy().ravel() if np.isfinite(v)]
    low = min(vals)
    x0, x1 = X_RHO
    if low - RHO_MARGIN >= x0 - 1e-12:
        return (x0, x1), list(RHO_TICKS)
    x0 = max(-1.0, float(np.floor(round((low - RHO_MARGIN) * 10, 9))) / 10)
    return (x0, x1), [t for t in (-1.0, -0.5, 0.0, 0.5, 1.0) if t >= x0 - 1e-12]


def fmt_rho_tick(t: float) -> str:
    """Tick label of the rho axis: the decimals it needs, at least one ("0.5", "0.75", "1.0"), the true minus."""
    s = f"{abs(float(t)):.2f}".rstrip("0")
    s = s + "0" if s.endswith(".") else s
    return (MINUS if t < 0 else "") + s


def top_moves(cells: pd.DataFrame, k: int = N_TOP) -> pd.Series:
    """Cell ids of the ``k`` largest |rank_shift|, ties broken by cell id."""
    c = cells.assign(_abs=cells["rank_shift"].abs())
    c = c.sort_values(["_abs", "cell"], ascending=[False, True], kind="mergesort")
    return c["cell"].head(k).reset_index(drop=True)


def _get(tree: dict, dotted: str):
    node = tree
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


# =====================================================================================================================
# Tables
# =====================================================================================================================

def load_inputs(results_dir: Path) -> dict:
    rd = Path(results_dir)
    return {"cells": pd.read_csv(rd / "h1_cells.csv"), "h1": json.loads((rd / "h1.json").read_text()),
            "sens": json.loads((rd / "sensitivity.json").read_text())}


def table_a(cells: pd.DataFrame) -> pd.DataFrame:
    g = base.full_grid()
    c = cells.drop_duplicates("cell").set_index("cell").reindex(g["cell"])
    a = g.copy()
    a["fills"] = c["fills"].fillna(0).astype(int).to_numpy()
    a["occupied"] = c["occupied"].fillna(False).astype(bool).to_numpy()
    a["A_bp"] = c["A_bp"].to_numpy(float)
    a["B_bp"] = c["B_bp"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        a["kappa_pm2"] = (100 * c["sum_K"] / c["sum_index"]).to_numpy(float)
    a["hatched"] = a["occupied"] & (a["B_bp"] < 0)
    a["shade"] = np.nan
    for side in SIDES:
        m = (a["side"] == side).to_numpy()
        absb = np.maximum(np.abs(a.loc[m, "B_bp"].to_numpy(float)), 1.0)
        sh, _, _ = base.shade_log(absb, a.loc[m, "occupied"].to_numpy(bool), floor=1.0)
        a.loc[m, "shade"] = sh
    a["unit"] = [ROW_UNIT[s][0] for s in a["side"]]
    a["printed"] = [printed_cell(s, v) if o else "×" for s, v, o in zip(a["side"], a["B_bp"], a["occupied"])]
    return a


def table_b(cells: pd.DataFrame) -> pd.DataFrame:
    occ = cells[cells["occupied"].astype(bool)].copy()
    top = set(top_moves(occ[["cell", "rank_shift"]]))
    occ["top10"] = occ["cell"].isin(top)
    n_pos = int((occ["A_bp"] > 0).sum())
    occ["sign_line"] = n_pos + 0.5
    cols = ["cell", "ccy", "side", "delta_bucket", "tenor_bucket", "A_bp", "B_bp", "rank_A", "rank_B", "rank_shift",
            "rank_A_lo", "rank_A_hi", "rank_B_lo", "rank_B_hi", "top10", "sign_line"]
    return occ[cols].sort_values(["rank_A", "cell"]).reset_index(drop=True)


def table_c(h1: dict, sens: dict) -> pd.DataFrame:
    """Forest rows (label, source_key, kind, stat, lo, hi, n, n_days, printed) plus the band, header and sample."""
    rejected = verdict(h1, side="upper")
    rows = []
    for label, src, key, kind in FOREST_ROWS:
        node = h1 if src == "h1" else _get(sens, key)
        if node is None:
            if key in OPTIONAL_KEYS:
                log.warning("sensitivity.json has no %s: row %r left out (section 10)", key, label)
                continue
            raise KeyError(f"sensitivity.json has no {key}")
        rows.append({"label": label, "source_key": "h1.json" if src == "h1" else f"sensitivity.json:{key}",
                     "kind": kind, "stat": float(node["stat"]), "lo": float(node["lo"]), "hi": float(node["hi"]),
                     "n": int(node["n"]), "n_days": int(node["n_days"]), "printed": str(int(node["n"]))})
    band = _get(sens, BAND_KEY)
    if band is not None:
        rows.append({"label": BAND_LABEL, "source_key": f"sensitivity.json:{BAND_KEY}", "kind": "band",
                     "stat": float(band["mean"]), "lo": float(band["p05"]), "hi": float(band["p95"]),
                     "n": int(band.get("draws", 0) or 0), "n_days": np.nan, "printed": BAND_LABEL})
    else:
        log.warning("sensitivity.json has no %s: band left out (section 10)", BAND_KEY)
    rows.append({"label": "header", "source_key": "h1.json", "kind": "header", "stat": float(h1["stat"]),
                 "lo": float(h1["lo"]), "hi": float(h1["hi"]), "n": int(h1["n"]), "n_days": int(h1["n_days"]),
                 "printed": header_text(h1, rejected)})
    for line in sample_lines(h1):
        rows.append({"label": "sample", "source_key": "h1.json", "kind": "sample", "stat": np.nan, "lo": np.nan,
                     "hi": np.nan, "n": int(h1["n"]), "n_days": int(h1["n_days"]), "printed": line})
    return pd.DataFrame(rows)


def sample_lines(h1: dict) -> List[str]:
    thr = float(h1["threshold"])
    return [f"{int(h1['n'])} cells · {int(h1['n_days'])} day clusters",
            f"rejected if upper bound ≥ {thr:g}"]


def table_shift(cells: pd.DataFrame) -> pd.DataFrame:
    """Mean rank shift (rank_B - rank_A, negative = moves up under capital) by tenor and by |delta| per side."""
    occ = cells[cells["occupied"].astype(bool)]
    rows = []
    for side in SIDES:
        s = occ[occ["side"] == side]
        for dim, col, order in (("tenor", "tenor_bucket", TENOR_LABELS), ("delta", "delta_bucket", DELTA_LABELS)):
            for bucket in order:
                g = s[s[col] == bucket]
                if g.empty:
                    continue
                rows.append({"side": side, "dimension": dim, "bucket": bucket, "n_cells": len(g),
                             "mean_rank_shift": float(g["rank_shift"].mean()),
                             "median_rank_shift": float(g["rank_shift"].median()),
                             "mean_rank_A": float(g["rank_A"].mean()), "mean_rank_B": float(g["rank_B"].mean())})
    return pd.DataFrame(rows)


# =====================================================================================================================
# Drawing
# =====================================================================================================================

HEAD_BASE, HEAD_STEP, HEAD_SEP = 3.0, 8.6, 1.5   # points: sample lines above the forest, line pitch, gap


def verdict_offset_pt(n_sample: int) -> float:
    """Height in points of the bottom of the (last) verdict line above the forest, over ``n_sample`` sample lines;
    the panel letter sits there too."""
    return HEAD_BASE + n_sample * HEAD_STEP + HEAD_SEP


def ruler(ax, rows: pd.DataFrame, h: dict, *, side: str, xlim=X_RHO, header_x: float = 0.0,
          sample: Sequence[str] = (), band: Optional[dict] = None, xlabel: str = "",
          letter: Optional[Tuple[str, float]] = None, head_width: Optional[float] = None,
          xticks: Optional[Sequence[float]] = None) -> str:
    """Forest after section 6.5. ``rows`` in drawing order (label, kind, stat, lo, hi, printed); the registered row is
    the first row of kind ``registered``. Draws the bold verdict line and the sample lines above the axes (left edge
    at ``header_x`` in axes coordinates), the dashed threshold, the rejection hatch in the height of the registered
    row, grey bands behind exploratory rows, ``band`` (dict with lo, hi, label) behind all rows and n to the right
    under the head ``N_TITLE``. ``letter`` (text, x as a fraction of the figure width) is the panel letter, on the
    first line of the verdict. A verdict line wider than ``head_width`` inches breaks before its arrow. ``xticks``
    are labelled with ``fmt_rho_tick`` (default: 0, 0.5, 1 on an axis from below zero, else matplotlib's).
    Returns the verdict line; raises ValueError if the rule applied to the bounds disagrees with ``h["rejected"]``."""
    rejected = verdict(h, side=side)
    head = header_text(h, rejected)
    too_long = [str(x) for x in rows["label"] if len(str(x)) > LABEL_MAX]
    if too_long:
        raise ValueError(f"row labels longer than {LABEL_MAX} characters: {too_long}")
    thr = float(h["threshold"])
    x0, x1 = xlim
    n = len(rows)
    extra = 1 if band is not None else 0
    ax.set_xlim(x0, x1)
    ax.set_ylim(n - 0.5 + extra, -0.5)
    trans_n = blended_transform_factory(ax.transAxes, ax.transData)
    for k, r in enumerate(rows.itertuples(index=False)):
        if r.kind == "exploratory":
            ax.add_patch(Rectangle((x0, k - 0.5), x1 - x0, 1.0, facecolor=EXPLORATORY_BAND, edgecolor="none",
                                   zorder=0))
    if band is not None:   # behind every row, plus a row of its own that carries the label
        ax.add_patch(Rectangle((band["lo"], -0.5), band["hi"] - band["lo"], n + extra, facecolor=BAND_GREY,
                               edgecolor="none", zorder=0.5))
    ax.vlines(thr, -0.5, n - 0.5, colors=INK, linestyles="--", lw=0.8, zorder=2)
    reg = [k for k, r in enumerate(rows.itertuples(index=False)) if r.kind == "registered"]
    for k in reg:
        left, width = (thr, x1 - thr) if side == "upper" else (x0, thr - x0)
        ax.add_patch(Rectangle((left, k - 0.42), width, 0.84, fill=False, hatch="////", edgecolor=HATCH_GREY, lw=0.0,
                               zorder=1))
    for k, r in enumerate(rows.itertuples(index=False)):
        col = GREY if r.kind == "exploratory" else INK
        lw = 2.0 if r.kind == "registered" else 1.0
        lo, hi = max(r.lo, x0), min(r.hi, x1)
        ax.plot([lo, hi], [k, k], color=col, lw=lw, solid_capstyle="butt", zorder=3)
        for end, clipped in ((x0, r.lo < x0), (x1, r.hi > x1)):
            if clipped:            # interval runs out of the axis: it ends in an arrow at the axis edge
                start = hi if end == x0 else lo
                ax.annotate("", xy=(end, k), xytext=(start, k), zorder=3,
                            arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, mutation_scale=6.0, shrinkA=0,
                                            shrinkB=0))
        face = INK if r.kind == "registered" else "white"
        ax.plot([r.stat], [k], marker="o", ms=4.0 if r.kind == "registered" else 3.5, mfc=face, mec=col,
                mew=0.8, ls="none", zorder=4)
        ax.text(1.03, k, str(r.printed), transform=trans_n, ha="left", va="center", fontsize=7.0, color=GREY)
    ax.annotate(N_TITLE, xy=(1.03, 1.0), xycoords="axes fraction", xytext=(0, 1), textcoords="offset points",
                ha="left", va="bottom", fontsize=7.0, color=GREY)
    labels = list(rows["label"]) + ([band["label"]] if band is not None else [])
    ax.set_yticks(range(n + extra))
    ax.set_yticklabels(labels, fontsize=7.0)
    for k, t in enumerate(ax.get_yticklabels()):
        if k < n and rows["kind"].iloc[k] == "registered":
            t.set_fontweight("bold")
        if k >= n:
            t.set_color(GREY)
    ax.tick_params(axis="y", length=0, pad=3.0)
    if xticks is not None:
        ax.set_xticks(list(xticks))
        ax.set_xticklabels([fmt_rho_tick(t) for t in xticks], fontsize=7.0)
    else:
        ax.set_xticks([0.0, 0.5, 1.0] if x0 < 0 else ax.get_xticks())
    for name in ("top", "right", "left"):
        ax.spines[name].set_visible(False)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=7.0, labelpad=1.5)
    step = HEAD_STEP
    for i, line in enumerate(reversed(list(sample))):
        ax.annotate(line, xy=(header_x, 1.0), xycoords="axes fraction", xytext=(0, HEAD_BASE + i * step),
                    textcoords="offset points", ha="left", va="bottom", fontsize=7.0, color=HEAD)
    off = verdict_offset_pt(len(sample))
    lines = [head]
    if head_width is not None:
        probe = ax.annotate(head, xy=(header_x, 1.0), xycoords="axes fraction", fontsize=7.0, fontweight="bold")
        fig = ax.figure
        if probe.get_window_extent(fig.canvas.get_renderer()).width / fig.dpi > head_width:
            lines = [head.split(" → ")[0], "→ " + head.split(" → ")[1]]
        probe.remove()
    for i, line in enumerate(reversed(lines)):
        ax.annotate(line, xy=(header_x, 1.0), xycoords="axes fraction", xytext=(0, off + i * step),
                    textcoords="offset points", ha="left", va="bottom", fontsize=7.0, fontweight="bold", color=INK)
    if letter is not None:
        ax.annotate(letter[0], xy=(letter[1], 1.0), xycoords=blended_transform_factory(ax.figure.transFigure,
                                                                                         ax.transAxes),
                    xytext=(0, off + (len(lines) - 1) * step), textcoords="offset points", ha="left",
                    va="bottom", fontsize=8.0, fontweight="bold")
    return head


# Layout in inches (canvas 7.0 x 6.2; saved 6.84 wide, so every x moves in by 2.3 per cent while type keeps its size).
# Panel a spans the full width on top: a map cell is 28.2 pt wide in print (19.3 pt in round 1), so the closest
# neighbours, "−7.3" next to "−126" and "−107" next to "−8.3", keep 10.1 pt between their glyph boxes in the PDF
# (1.2 pt before) and the tenor ticks stand upright. Panels b and c share the row below, each about half the width.
# That row is as high as the forest of c needs (15 rows at 8.0 pt plus the verdict line and two sample lines above
# it); the maps are as high as their cells need (15 pt: the 7 pt number and a strip of hatch above and below it).
L_MAP = 0.79                             # left edge of the first map (row titles and |delta| ticks to its left)
A_RIGHT = 6.97                           # right edge of the last map
MAP_GAP = 0.08                           # between the maps of two underlyings
CELL_PT = 15.0                           # height of a map cell
MAP_H = len(DELTA_LABELS) * CELL_PT / 72.0
ROW_GAP = 0.12                           # between the sell and the buy maps
TOP_MAP = HEIGHT - 0.43                  # letter a, header in two lines and the underlying titles above
BOTTOM_MAP = TOP_MAP - 2 * MAP_H - ROW_GAP
TENOR_Y = 2.45                           # bottom of the tenor title, under the upright tenor ticks
BUY_TITLE_LIFT = 0.10                    # the two-line buy title sits a little high, clear of the tick "90–100"
N_FOREST = 15                            # rows of c with every optional row and the band
FOREST_PT = 8.0                          # row pitch of c (section 6.5, audit F4)
C_BOTTOM = 0.33
C_TOP = C_BOTTOM + N_FOREST * FOREST_PT / 72.0
LETTER_Y = C_TOP + verdict_offset_pt(2) / 72.0   # bottom of the letters b and c, on the verdict line of c
C_LETTER_X = 3.45                        # letter c; the verdict line starts 0.15 in to its right
C_LEFT, C_RIGHT = 4.62, 6.70             # forest axes; the row labels sit to the left, n to the right
B_LETTER_X = 0.02
B_LEGEND_X = 0.20                        # the side legend in one line, right of the letter b
B_BOX = (0.52, C_BOTTOM, 2.60, 1.85)     # left, bottom, width, height of the rank axes
B_YTITLE_X = 0.11                        # centre of the two-line y title of b
SIGN_GREY = "#999999"                    # the sign lines of b: dotted and lighter than the rank intervals
SIGN_DOTS = (0, (1.0, 1.6))
CAP = 2.5                                # end ticks of the rank intervals, points


def _panel_a(fig, a: pd.DataFrame) -> None:
    map_w = (A_RIGHT - L_MAP - 2 * MAP_GAP) / 3
    map_h = MAP_H
    for r, side in enumerate(SIDES):
        top = TOP_MAP - r * (map_h + ROW_GAP)
        for c, ccy in enumerate(CCYS):
            ax = base.add_axes_in(fig, L_MAP + c * (map_w + MAP_GAP), top - map_h, map_w, map_h)
            base.draw_map(ax, base.map_grid(a, "occupied", ccy, side, fill=False), base.map_grid(a, "shade", ccy, side),
                          base.map_grid(a, "printed", ccy, side, fill=""),
                          hatched=base.map_grid(a, "hatched", ccy, side, fill=False),
                          ylabels=(c == 0), xlabels=(r == 1))
            if r == 1:                   # the wide cells leave room for upright tenor ticks
                ax.set_xticklabels(base.TENOR_TICKS, fontsize=7.0, rotation=0, ha="center",
                                   rotation_mode="default")
            if r == 0:
                ax.set_title(ccy, fontsize=8.0, fontweight="bold", pad=3.0)
        lift = BUY_TITLE_LIFT if side == "buy" else 0.0
        fig.text(*base.fig_xy(fig, 0.27, top - map_h / 2 + lift), SIDE_TITLE[side], rotation=90, ha="center",
                 va="center", fontsize=8.0, multialignment="center")
    fig.text(*base.fig_xy(fig, 0.075, (TOP_MAP + BOTTOM_MAP) / 2), base.DELTA_TITLE, rotation=90, ha="center",
             va="center", fontsize=8.0)
    fig.text(*base.fig_xy(fig, L_MAP + 1.5 * map_w + MAP_GAP, TENOR_Y), base.TENOR_TITLE, ha="center", va="bottom",
             fontsize=8.0)
    fig.text(*base.fig_xy(fig, 0.02, HEIGHT - 0.04), "a", ha="left", va="top", fontsize=8.0, fontweight="bold")
    fig.text(*base.fig_xy(fig, L_MAP, HEIGHT - 0.04), HEADER, ha="left", va="top", fontsize=7.0, color=HEAD,
             linespacing=1.25)


def _panel_b(fig, b: pd.DataFrame) -> None:
    ax = base.add_axes_in(fig, *B_BOX)
    n = len(b)
    lim = (n + 5, -4)
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.plot([1, n], [1, n], color=LINE_GREY, ls="--", lw=0.6, zorder=1)
    pos = float(b["sign_line"].iloc[0]) if n else 0.5
    ax.axvline(pos, color=SIGN_GREY, ls=SIGN_DOTS, lw=0.9, zorder=1)
    ax.axhline(pos, color=SIGN_GREY, ls=SIGN_DOTS, lw=0.9, zorder=1)
    # under the sign line at the right, in the block that the sign agreement leaves empty (left, the points crowd)
    ax.text(-2, pos + 3, "↓ edge ≤ 0", ha="right", va="top", fontsize=7.0, color=GREY)
    t = b[b["top10"]]
    for r in t.itertuples(index=False):      # crosses with end ticks: they do not read as the sign lines
        ax.plot([r.rank_A_lo, r.rank_A_hi], [r.rank_B, r.rank_B], color=LINE_GREY, lw=0.6, marker="|", ms=CAP,
                mew=0.6, zorder=2)
        ax.plot([r.rank_A, r.rank_A], [r.rank_B_lo, r.rank_B_hi], color=LINE_GREY, lw=0.6, marker="_", ms=CAP,
                mew=0.6, zorder=2)
    s, u = b[b["side"] == "sell"], b[b["side"] == "buy"]
    ax.plot(s["rank_A"], s["rank_B"], ls="none", marker="v", ms=3.0, mfc=INK, mec=INK, mew=0.4, zorder=3)
    ax.plot(u["rank_A"], u["rank_B"], ls="none", marker="^", ms=3.0, mfc="white", mec=INK, mew=0.6, zorder=3)
    ticks = sorted({t for t in (1, 50, 100, 150) if t <= n - 30} | {1, n})   # section 7: 1, 50, 100, 173
    for setter in (ax.set_xticks, ax.set_yticks):
        setter(ticks)
    ax.set_xticklabels([str(x) for x in ticks], fontsize=7.0)
    ax.set_yticklabels([str(x) for x in ticks], fontsize=7.0)
    ax.set_xlabel("rank by edge per notional (1 = highest edge)", fontsize=7.0, labelpad=1.5)
    left, bottom, _, height = B_BOX       # the y title as figure text: longer than the axes are high
    fig.text(*base.fig_xy(fig, B_YTITLE_X, bottom + height / 2),
             "rank by edge per PM2 capital\n(1 = highest edge)", rotation=90, ha="center", va="center", fontsize=7.0,
             multialignment="center")
    for name in ("top", "right"):
        ax.spines[name].set_visible(False)
    handles = [Line2D([], [], ls="none", marker="v", ms=3.5, mfc=INK, mec=INK, label="maker sells (short)"),
               Line2D([], [], ls="none", marker="^", ms=3.5, mfc="white", mec=INK, mew=0.6,
                      label="maker buys (long)")]
    # above the axes, in one line with the letter: inside, every free block is crossed by the rank intervals
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=base.fig_xy(fig, B_LEGEND_X, LETTER_Y),
              bbox_transform=fig.transFigure, fontsize=7.0, frameon=False, handlelength=0.9, handletextpad=0.35,
              borderpad=0.0, borderaxespad=0.0, ncol=2, columnspacing=1.4)
    fig.text(*base.fig_xy(fig, B_LETTER_X, LETTER_Y), "b", ha="left", va="bottom", fontsize=8.0, fontweight="bold")


def _panel_c(fig, c: pd.DataFrame, h1: dict) -> None:
    ax = base.add_axes_in(fig, C_LEFT, C_BOTTOM, C_RIGHT - C_LEFT, C_TOP - C_BOTTOM)
    rows = c[c["kind"].isin(["registered", "sensitivity", "exploratory"])].reset_index(drop=True)
    b = c[c["kind"] == "band"]
    band = None if b.empty else {"lo": float(b["lo"].iloc[0]), "hi": float(b["hi"].iloc[0]), "label": BAND_LABEL}
    head_left = C_LETTER_X + 0.15                        # right of the letter
    header_x = (head_left - C_LEFT) / (C_RIGHT - C_LEFT)
    printed_w = print_width(WIDTH)                       # the canvas shrinks to this width when saved
    head_width = printed_w - 0.02 - head_left * printed_w / WIDTH
    xlim, xticks = rho_axis(c, float(h1["threshold"]))
    ruler(ax, rows, h1, side="upper", xlim=xlim, xticks=xticks, header_x=header_x,
          sample=list(c.loc[c["kind"] == "sample", "printed"]), band=band, xlabel="Spearman's ρ",
          letter=("c", C_LETTER_X / WIDTH), head_width=head_width)


def make_figure(results_dir: Path = Path("results/p2")):
    """Draw F2 from the files in ``results_dir``; returns (figure, {"a", "b", "c", "shift"} tables)."""
    inputs = load_inputs(results_dir)
    cells, h1, sens = inputs["cells"], inputs["h1"], inputs["sens"]
    tables = {"a": table_a(cells), "b": table_b(cells), "c": table_c(h1, sens), "shift": table_shift(cells)}
    with matplotlib.rc_context(base.rc()):
        fig = plt.figure(figsize=(WIDTH, HEIGHT))
        _panel_a(fig, tables["a"])
        _panel_b(fig, tables["b"])
        _panel_c(fig, tables["c"], h1)
    return fig, tables


def build(out_dir: Path = Path("paper2/figures"), results_dir: Path = Path("results/p2")) -> List[Path]:
    """Write ``fig_f2_{a,b,c,shift}.csv`` to ``results_dir`` and ``f2.pdf`` / ``f2.png`` to ``out_dir``."""
    results_dir = Path(results_dir)
    fig, tables = make_figure(results_dir)
    paths = []
    a_cols = ["cell", "ccy", "side", "delta_bucket", "tenor_bucket", "fills", "occupied", "A_bp", "B_bp", "kappa_pm2",
              "hatched", "shade", "unit", "printed"]
    for key, frame in (("a", tables["a"][a_cols]), ("b", tables["b"]), ("c", tables["c"]),
                       ("shift", tables["shift"])):
        p = results_dir / f"fig_{SLOT}_{key}.csv"
        frame.to_csv(p, index=False)
        paths.append(p)
    with matplotlib.rc_context(base.rc()):
        paths += figstyle.save(to_print(fig), SLOT, Path(out_dir))       # the width main.tex sets the figure at
    return paths


# =====================================================================================================================
# Checks: value in the figure (fig_f2_*.csv) against h1_cells.csv, h1.json and sensitivity.json
# =====================================================================================================================

def _csv(rd, name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(Path(rd) / name, **kw)


def _json(rd, name: str) -> dict:
    return json.loads((Path(rd) / name).read_text())


def _fa(rd) -> pd.DataFrame:
    return _csv(rd, "fig_f2_a.csv", keep_default_na=False, na_values=[""])


def _fc(rd) -> pd.DataFrame:
    return _csv(rd, "fig_f2_c.csv")


def _occ(rd) -> pd.DataFrame:
    h = _csv(rd, "h1_cells.csv")
    return h[h["occupied"]]


def _pos_by_side(frame: pd.DataFrame):
    return {s: (int((g["A_bp"] > 0).sum()), int((g["A_bp"] <= 0).sum()), int(len(g)))
            for s, g in frame.groupby("side")}


def _printed_src(rd):
    h = _csv(rd, "h1_cells.csv").set_index("cell")
    out = {}
    for cell, side in zip(base.full_grid()["cell"], base.full_grid()["side"]):
        occupied = cell in h.index and bool(h.loc[cell, "occupied"])
        out[cell] = printed_cell(side, h.loc[cell, "B_bp"]) if occupied else "×"
    return out


def _forest_fig(rd):
    c = _fc(rd)
    c = c[c["kind"].isin(["registered", "sensitivity", "exploratory", "band"])]
    return {r.source_key: (round(r.stat, 12), round(r.lo, 12), round(r.hi, 12)) for r in c.itertuples()}


def _forest_src(rd):
    sens, h1 = _json(rd, "sensitivity.json"), _json(rd, "h1.json")
    keys = set(_fc(rd)["source_key"])
    out = {}
    for key in keys:
        if key == "h1.json":
            node = h1
            out[key] = (round(node["stat"], 12), round(node["lo"], 12), round(node["hi"], 12))
        elif key.startswith("sensitivity.json:"):
            node = _get(sens, key.split(":", 1)[1])
            if key.endswith(BAND_KEY):
                out[key] = (round(node["mean"], 12), round(node["p05"], 12), round(node["p95"], 12))
            else:
                out[key] = (round(node["stat"], 12), round(node["lo"], 12), round(node["hi"], 12))
    return out


def _header_src(rd):
    h1 = _json(rd, "h1.json")
    rule, thr = str(h1["rule"]), float(h1["threshold"])
    rej = float(h1["hi"]) >= thr if ("upper bound" in rule and ">=" in rule) else None
    if rej is None or rej != bool(h1["rejected"]):
        return "rule and file disagree"
    return header_text(h1, rej)


def _top10_src(rd):
    return sorted(top_moves(_occ(rd)[["cell", "rank_shift"]]))


def _rank_gap(rd):
    b = _csv(rd, "fig_f2_b.csv").set_index("cell")
    h = _occ(rd).set_index("cell").loc[b.index]
    cols = ["rank_A", "rank_B", "rank_A_lo", "rank_A_hi", "rank_B_lo", "rank_B_hi"]
    return float(np.nanmax(np.abs(b[cols].to_numpy(float) - h[cols].to_numpy(float))))


def _kappa_span(frame: pd.DataFrame):
    return round(float(frame["kappa"].min()), 9), round(float(frame["kappa"].max()), 9)


CHECKS: List[dict] = [
    {"name": "points in panel b", "figure": lambda rd: int(len(_csv(rd, "fig_f2_b.csv"))),
     "source": lambda rd: int(_json(rd, "h1.json")["n"]), "pilot": 173},
    {"name": "points in panel b = occupied cells of h1_cells", "figure": lambda rd: int(len(_csv(rd, "fig_f2_b.csv"))),
     "source": lambda rd: int(len(_occ(rd)))},
    {"name": "cells and crosses in panel a", "figure": lambda rd: (int(len(_fa(rd))), int((_fa(rd)["printed"] == "×")
                                                                                          .sum())),
     "source": lambda rd: (base.N_GRID, base.N_GRID - int(len(_occ(rd)))), "pilot": (210, 37)},
    {"name": "sign line after the cells with A_bp > 0", "figure": lambda rd: float(
        _csv(rd, "fig_f2_b.csv")["sign_line"].iloc[0]),
     "source": lambda rd: int((_occ(rd)["A_bp"] > 0).sum()) + 0.5, "pilot": 99.5},
    {"name": "cells with A_bp > 0 / <= 0 / all, by side", "figure": lambda rd: _pos_by_side(_csv(rd, "fig_f2_b.csv")),
     "source": lambda rd: _pos_by_side(_occ(rd)), "pilot": {"buy": (61, 26, 87), "sell": (38, 48, 86)}},
    {"name": "hatched = B_bp < 0 = A_bp <= 0 (sign(A) = sign(B))",
     "figure": lambda rd: sorted(_fa(rd).loc[_fa(rd)["hatched"].astype(str) == "True", "cell"]),
     "source": lambda rd: sorted(_occ(rd).loc[_occ(rd)["A_bp"] <= 0, "cell"])},
    {"name": "printed B_bp (sells in bp, buys in per cent) and crosses",
     "figure": lambda rd: dict(zip(_fa(rd)["cell"], _fa(rd)["printed"].fillna(""))), "source": _printed_src},
    {"name": "every number in a cell at most four characters",
     "figure": lambda rd: bool(_fa(rd)["printed"].fillna("").str.len().max() <= 4), "source": lambda rd: True},
    {"name": "B_bp of panel a = h1_cells", "figure": lambda rd: float(np.nanmax(np.abs(
        _fa(rd).set_index("cell").loc[_occ(rd)["cell"], "B_bp"].to_numpy(float) - _occ(rd)["B_bp"].to_numpy(float)))),
     "source": lambda rd: 0.0, "atol": 1e-9},
    {"name": "ranks and rank intervals of panel b = h1_cells (max abs gap)", "figure": _rank_gap,
     "source": lambda rd: 0.0},
    {"name": "ten largest |rank_shift| (ties by cell id)",
     "figure": lambda rd: sorted(_csv(rd, "fig_f2_b.csv").query("top10")["cell"]), "source": _top10_src},
    {"name": "header line = verdict rebuilt from h1.json rule and bounds",
     "figure": lambda rd: _fc(rd).loc[_fc(rd)["kind"] == "header", "printed"].iloc[0], "source": _header_src},
    {"name": "sample line: cells and day clusters",
     "figure": lambda rd: _fc(rd).loc[_fc(rd)["kind"] == "sample", "printed"].iloc[0],
     "source": lambda rd: f"{int(_json(rd, 'h1.json')['n'])} cells · {int(_json(rd, 'h1.json')['n_days'])} day "
                          f"clusters", "pilot": "173 cells · 463 day clusters"},
    {"name": "forest rows (stat, lo, hi) = h1.json and sensitivity.json", "figure": _forest_fig,
     "source": _forest_src},
    {"name": "fills in occupied cells (panel a) = h1.json n_fills",
     "figure": lambda rd: int(_fa(rd).loc[_fa(rd)["occupied"].astype(str) == "True", "fills"].sum()),
     "source": lambda rd: int(_json(rd, "h1.json")["n_fills"]), "pilot": 331813},
    {"name": "cells present in every replicate", "figure": lambda rd: int(len(_csv(rd, "fig_f2_b.csv"))),
     "source": lambda rd: int(_json(rd, "h1.json").get("cells_present_min", -1)), "pilot": 173},
    {"name": "kappa span of the occupied cells",
     "figure": lambda rd: _kappa_span(_fa(rd).loc[_fa(rd)["occupied"].astype(str) == "True"].rename(
         columns={"kappa_pm2": "kappa"})),
     "source": lambda rd: _kappa_span(_occ(rd).assign(kappa=100 * _occ(rd)["sum_K"] / _occ(rd)["sum_index"])),
     "pilot": (0.074, 38.73)},
]


def run_checks(results_dir: Path = Path("results/p2")) -> pd.DataFrame:
    rows = []
    for c in CHECKS:
        try:
            fv, sv = c["figure"](results_dir), c["source"](results_dir)
            ok = base._same(fv, sv, c.get("rtol", 0.0), c.get("atol", 0.0))
            err = ""
        except Exception as exc:  # noqa: BLE001 - reported, not raised
            fv = sv = None
            ok, err = False, repr(exc)
        rows.append({"slot": SLOT, "check": c["name"], "figure": fv, "source": sv, "ok": bool(ok),
                     "pilot": c.get("pilot"),
                     "pilot_ok": base._pilot_same(fv, c.get("pilot")) if fv is not None else None, "error": err})
    return pd.DataFrame(rows)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", type=Path, default=Path("results/p2"))
    ap.add_argument("--out", type=Path, default=Path("paper2/figures"))
    ap.add_argument("--check", action="store_true", help="print the checks after the build")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    for p in build(args.out, args.results):
        print("wrote", p)
    if args.check:
        res = run_checks(args.results)
        with pd.option_context("display.width", 200, "display.max_colwidth", 80):
            print(res[["check", "ok", "pilot_ok", "error"]].to_string(index=False))
        return 0 if res["ok"].all() else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
