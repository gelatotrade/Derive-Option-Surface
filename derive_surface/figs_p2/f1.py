"""F1 of Paper 2: what one contract costs (docs/paper2/FIGURE_SELECTION.md, sections 6 and 7, slot F1).

Left, six maps (maker sells above, maker buys below; BTC, ETH, HYPE): PM2 capital per contract in per cent of
notional, ``kappa = 100 sum_K / sum_index`` of the ``pm2`` map in ``results/p2/fig_edge_maps.csv`` (ratio of sums over
the fills of the PM2 window). Right, one strip per map row: for every occupied cell the capital of the same fills
under standard margin (``sm_pm2win``) and under the legacy manager (``pm_pm2win``) divided by PM2 capital, pooled and,
hollow, for the fills of regime R4 only (``results/p2/fig_f1_regimes.csv``).

The regime table is figure data, not a test statistic: ``cell_capital_by_regime`` sums capital and notional per cell
and parameter regime from ``data/p2/derived/capital.parquet`` joined to the Paper 1 buckets of
``data/p1/derived/markouts.parquet``, and ``check_regimes_against_maps`` requires the regimes to add up to the map.

    python3 -m derive_surface.figs_p2.f1            # regimes (if missing) and the figure
    python3 -m derive_surface.figs_p2.f1 --regimes  # rebuild the regime table first

The map helpers (``draw_map``, ``grey``, ``map_grid``, layout constants) are shared with F2.
"""
from __future__ import annotations

import argparse
import logging
import math
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LogNorm, to_rgb  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from matplotlib.ticker import NullLocator  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402

from derive_surface import figstyle  # noqa: E402
from derive_surface.figs_p2._print import to_print  # noqa: E402
from derive_surface.markouts import DELTA_LABELS, TENOR_LABELS  # noqa: E402

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parents[2]
SLOT = "f1"
WIDTH, HEIGHT = figstyle.DOUBLE, 3.9
FS_MIN = float(getattr(figstyle, "FS_MIN", 7.0))
MANAGER: Dict[str, Tuple[str, str, str]] = dict(getattr(figstyle, "MANAGER", None) or {
    "pm2": ("#0072B2", "-", "o"), "sm": ("#D55E00", "--", "s"), "pm": ("#009E73", ":", "D")})
INK = "#000000"
GREY = "#666666"
HEAD = "#333333"
MIN_FILLS = 200
CCYS = ("BTC", "ETH", "HYPE")
SIDES = ("sell", "buy")
N_GRID = len(CCYS) * len(SIDES) * len(DELTA_LABELS) * len(TENOR_LABELS)
DELTA_TICKS = ["0–10", "10–25", "25–40", "40–60", "60–75", "75–90", "90–100"]
TENOR_TICKS = ["≤2", "2–7", "7–30", "30–90", ">90"]
DELTA_TITLE = "|delta| of the traded option, %"
TENOR_TITLE = "tenor, days"
GREY_LO, GREY_HI = 0.08, 0.72          # section 6.4: Greys between 0.08 and 0.72
WHITE_TEXT_BELOW = 0.45                # luminance under which a cell number is white
HATCH_DARK = "#D0D0D0"                 # hatch on cells with white text: #666666 vanishes on Greys 0.6 to 0.72

# Section 6.6: R1 to 23 Jan 2026 04:24:05, R2 to 24 May 2026 04:05:07, R3 to 20 Aug 2026 22:09:25 UTC, R4 after.
# The bounds are the PM2 events in results/p2/events.csv; a fill at the event second belongs to the later regime.
REGIME_BOUNDS = (1769142245, 1779595507, 1787263765)
REGIMES = ("R1", "R2", "R3", "R4")
REGIME_LABELS = {"R1": "R1 to 23 Jan", "R2": "R2 to 24 May", "R3": "R3 to 20 Aug", "R4": "R4 since 20 Aug"}

SIDE_TITLE = {"sell": "maker sells (short)",
              "buy": "maker buys (long):\ncapital ≈ premium OTM"}      # OTM: out of the money (caption)
HEADER = ("number = PM2 capital per contract, % of notional, ratio of sums over the PM2 window,\n"
          "pooled over four parameter regimes · × = under 200 fills")
STRIP_ROWS = [("sm", "BTC", "pooled", "SM BTC"), ("sm", "BTC", "R4", "R4"),
              ("sm", "ETH", "pooled", "SM ETH"), ("sm", "ETH", "R4", "R4"),
              ("sm", "HYPE", "pooled", "SM HYPE"), ("sm", "HYPE", "R4", "R4"),
              ("pm", "BTC", "pooled", "legacy BTC"), ("pm", "ETH", "pooled", "legacy ETH")]
MAP_OF = {"sm": "sm_pm2win", "pm": "pm_pm2win", "pm2": "pm2"}
X_LIM = (0.6, 5.0)
JITTER = 0.18

CAPTION = (
    "What one contract costs. PM2 capital per contract in per cent of notional over the absolute delta of the "
    "traded option and tenor, for maker sells (upper row) and maker buys (lower row), as a ratio of sums over the "
    "fills of the PM2 window, which the parameter changes of 23 January, 24 May and 20 August 2026 split into four "
    "regimes. Each row is shaded on one logarithmic grey scale, and an empty cross marks a cell with fewer than 200 "
    "fills. The strips on the right give, for every occupied "
    "cell, the capital of the same fills under standard margin (squares) and under the legacy manager (diamonds) "
    "divided by PM2 capital, with the median cell as a bar; hollow squares use only the fills after the parameter "
    "change of 20 August 2026. For a maker buy, standard margin charges the premium, and PM2 about the premium out "
    "of the money (OTM) and less in the money.")


# =====================================================================================================================
# Style and layout helpers (shared with F2)
# =====================================================================================================================

def rc() -> dict:
    """Paper 2 rc: figstyle.RC with the canvas as print size (no tight bbox), black ticks, no grid."""
    out = dict(figstyle.RC)
    out.update({"savefig.bbox": "standard", "savefig.pad_inches": 0.0, "axes.grid": False, "hatch.linewidth": 0.6,
                "xtick.color": INK, "ytick.color": INK, "xtick.labelcolor": INK, "ytick.labelcolor": INK,
                "axes.titlesize": 8.0, "axes.labelsize": 8.0, "font.size": 8.0})
    return out


def add_axes_in(fig, left: float, bottom: float, width: float, height: float, **kw):
    """Axes placed in inches from the lower left corner of the canvas."""
    w, h = fig.get_size_inches()
    return fig.add_axes([left / w, bottom / h, width / w, height / h], **kw)


def fig_xy(fig, x_in: float, y_in: float) -> Tuple[float, float]:
    w, h = fig.get_size_inches()
    return x_in / w, y_in / h


def fmt_sig2(v: float) -> str:
    """Two significant digits, at most two decimals (section 7 F1: 0.07, 0.12, 9.9, 13, 39)."""
    if v is None or not np.isfinite(v):
        return ""
    if v == 0:
        return "0.0"
    r = float(f"{v:.2g}")
    exp = math.floor(math.log10(abs(r)))
    dec = min(2, max(0, 1 - exp))
    return f"{r:.{dec}f}"


def grey(shade: float) -> Tuple[float, float, float]:
    """Greys colormap at ``shade`` (already inside [0.08, 0.72])."""
    return tuple(matplotlib.colormaps["Greys"](float(shade))[:3])


def luminance(rgb) -> float:
    r, g, b = to_rgb(rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def shade_log(values: np.ndarray, mask: np.ndarray, floor: Optional[float] = None) -> Tuple[np.ndarray, float, float]:
    """Position on the grey ramp from a log scale over the masked values (one scale per map row).

    Returns (shade, vmin, vmax); shade is NaN outside the mask. ``floor`` clips small values (F2: 1 bp)."""
    v = np.asarray(values, dtype=float)
    m = np.asarray(mask, dtype=bool) & np.isfinite(v) & (v > 0)
    shade = np.full(v.shape, np.nan)
    if not m.any():
        return shade, float("nan"), float("nan")
    vv = v[m] if floor is None else np.maximum(v[m], floor)
    vmin, vmax = float(vv.min()), float(vv.max())
    if vmax <= vmin:
        vmax = vmin * 1.0001 + 1e-12
    t = LogNorm(vmin, vmax, clip=True)(vv).filled(0.0)
    shade[m] = GREY_LO + (GREY_HI - GREY_LO) * np.asarray(t, dtype=float)
    return shade, vmin, vmax


def map_grid(df: pd.DataFrame, col: str, ccy: str, side: str, fill=np.nan) -> np.ndarray:
    """7 x 5 array (|delta| top to bottom, tenor left to right) of ``col`` for one currency and side."""
    s = df[(df["ccy"] == ccy) & (df["side"] == side)]
    p = s.pivot(index="delta_bucket", columns="tenor_bucket", values=col)
    p = p.reindex(index=DELTA_LABELS, columns=TENOR_LABELS)
    arr = p.to_numpy(dtype=object)
    out = np.empty(arr.shape, dtype=object)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            x = arr[i, j]
            out[i, j] = fill if (x is None or (isinstance(x, float) and np.isnan(x))) else x
    return out


def draw_map(ax, occupied: np.ndarray, shade: np.ndarray, printed: np.ndarray, hatched: Optional[np.ndarray] = None,
             *, ylabels: bool, xlabels: bool) -> None:
    """One map after section 6.4: one number per cell on grey, white text on dark cells, an empty grey cross for
    cells under 200 fills, hatched negative cells (hatch #666666, light grey on the dark cells that carry white
    text, where #666666 would not show)."""
    ax.set_xlim(-0.5, len(TENOR_LABELS) - 0.5)
    ax.set_ylim(len(DELTA_LABELS) - 0.5, -0.5)
    for i in range(len(DELTA_LABELS)):
        for j in range(len(TENOR_LABELS)):
            if not bool(occupied[i, j]):
                ax.text(j, i, "×", ha="center", va="center", fontsize=7.0, color=GREY)
                continue
            col = grey(shade[i, j])
            ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=col, edgecolor="white", lw=0.5, zorder=1))
            dark = luminance(col) < WHITE_TEXT_BELOW
            neg = hatched is not None and bool(hatched[i, j])
            if neg:
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, hatch="////",
                                       edgecolor=HATCH_DARK if dark else GREY, lw=0.0, zorder=2))
            t = ax.text(j, i, str(printed[i, j]), ha="center", va="center", fontsize=7.0,
                        color="white" if dark else INK, zorder=3)
            if neg:   # a plain box in the cell grey behind the number: the hatch stays above and below it, and
                # the minus is no longer crossed by a hatch line (a 1.2 pt halo left "-7.3" reading as "/-7.3")
                t.set_bbox({"boxstyle": "square,pad=0.08", "facecolor": col, "edgecolor": "none", "linewidth": 0})
    ax.set_xticks(range(len(TENOR_LABELS)))
    ax.set_yticks(range(len(DELTA_LABELS)))
    ax.set_xticklabels(TENOR_TICKS if xlabels else [], fontsize=7.0, rotation=40, ha="right",
                       rotation_mode="anchor")
    ax.set_yticklabels(DELTA_TICKS if ylabels else [], fontsize=7.0)
    ax.tick_params(length=0, pad=2.0)
    for s in ax.spines.values():
        s.set_linewidth(0.5)
        s.set_color("#999999")


def golden_jitter(index: int, half: float = JITTER) -> float:
    """Deterministic vertical offset in [-half, half) from the cell index (golden-ratio sequence)."""
    return float(2 * half * ((index * 0.6180339887498949) % 1.0) - half)


def cell_index(delta_bucket: str, tenor_bucket: str) -> int:
    return DELTA_LABELS.index(delta_bucket) * len(TENOR_LABELS) + TENOR_LABELS.index(tenor_bucket)


def full_grid() -> pd.DataFrame:
    rows = [(f"{c}|{s}|{d}|{t}", c, s, d, t) for c in CCYS for s in SIDES for d in DELTA_LABELS for t in TENOR_LABELS]
    return pd.DataFrame(rows, columns=["cell", "ccy", "side", "delta_bucket", "tenor_bucket"])


# =====================================================================================================================
# Regime table (figdata: sums per cell and regime)
# =====================================================================================================================

def regime_of(ts_s) -> np.ndarray:
    """Regime label for UNIX seconds after section 6.6 (a fill at the event second is in the later regime)."""
    k = np.searchsorted(np.asarray(REGIME_BOUNDS, dtype=np.int64), np.asarray(ts_s, dtype=np.int64), side="right")
    return np.asarray(REGIMES, dtype=object)[k]


def cell_capital_by_regime(capital: pd.DataFrame, markouts: pd.DataFrame, min_fills: int = MIN_FILLS) -> pd.DataFrame:
    """Per regime and cell: fills, contracts and the sums of K_sm a, K_pm a, K_pm2 a and index a over the fills with
    finite K_pm2 (the PM2 window). Cells are Paper 1's buckets (markouts), the notional uses the markouts' index and
    amount like the H1 map; ``occupied`` = at least ``min_fills`` fills in the regime."""
    cap = capital[["trade_id", "currency", "ts", "maker_side", "K_sm", "K_pm", "K_pm2"]]
    mk = markouts[["trade_id", "delta_bucket", "tenor_bucket", "index_price", "amount"]]
    f = cap.merge(mk, on="trade_id", how="left", validate="one_to_one")
    f = f[np.isfinite(f["K_pm2"].to_numpy(float))].copy()
    if f["delta_bucket"].isna().any() or f["amount"].isna().any():
        raise ValueError(f"{int(f['delta_bucket'].isna().sum())} PM2 fills without a Paper 1 bucket")
    a = f["amount"].to_numpy(float)
    f["side"] = np.where(f["maker_side"].to_numpy(float) > 0, "buy", "sell")
    f["regime"] = regime_of(f["ts"].to_numpy(np.int64) // 1000)
    f["Ka_sm"] = f["K_sm"].to_numpy(float) * a
    f["Ka_pm"] = f["K_pm"].to_numpy(float) * a
    f["Ka_pm2"] = f["K_pm2"].to_numpy(float) * a
    f["Ia"] = f["index_price"].to_numpy(float) * a
    f["pm_ok"] = np.isfinite(f["Ka_pm"].to_numpy(float))
    f["ccy"] = f["currency"]
    keys = ["regime", "ccy", "side", "delta_bucket", "tenor_bucket"]
    g = f.groupby(keys, sort=True)
    out = g.agg(fills=("trade_id", "size"), contracts=("amount", "sum"), sum_K_sm_a=("Ka_sm", "sum"),
                sum_K_pm_a=("Ka_pm", lambda s: s.sum(min_count=1)), pm_fills=("pm_ok", "sum"),
                sum_K_pm2_a=("Ka_pm2", "sum"), sum_index_a=("Ia", "sum")).reset_index()
    out.insert(1, "cell", out["ccy"] + "|" + out["side"] + "|" + out["delta_bucket"] + "|" + out["tenor_bucket"])
    out["pm_fills"] = out["pm_fills"].astype(int)
    out["occupied"] = out["fills"] >= min_fills
    out["regime_label"] = out["regime"].map(REGIME_LABELS)
    return out


def check_regimes_against_maps(regimes: pd.DataFrame, maps: pd.DataFrame, rtol: float = 1e-9) -> None:
    """The regimes must add up to the maps of the PM2 window: fills and contracts of ``pm2``, sum_index and sum_K of
    ``pm2``, sum_K of ``sm_pm2win`` and ``pm_pm2win`` (relative <= rtol). Raises ValueError otherwise."""
    pooled = regimes.groupby("cell").agg(fills=("fills", "sum"), contracts=("contracts", "sum"),
                                         sum_K_sm_a=("sum_K_sm_a", "sum"),
                                         sum_K_pm_a=("sum_K_pm_a", lambda s: s.sum(min_count=1)),
                                         sum_K_pm2_a=("sum_K_pm2_a", "sum"), sum_index_a=("sum_index_a", "sum"))
    pairs = [("pm2", "fills", "fills"), ("pm2", "contracts", "contracts"), ("pm2", "sum_index", "sum_index_a"),
             ("pm2", "sum_K", "sum_K_pm2_a"), ("sm_pm2win", "sum_K", "sum_K_sm_a"),
             ("pm_pm2win", "sum_K", "sum_K_pm_a")]
    bad = []
    for name, mcol, rcol in pairs:
        m = maps[maps["map"] == name].set_index("cell")[mcol].astype(float)
        m = m[m.abs() > 0] if name != "pm2" else m
        r = pooled[rcol].reindex(m.index).astype(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            rel = np.abs(r.to_numpy() - m.to_numpy()) / np.maximum(np.abs(m.to_numpy()), 1e-300)
        worst = np.nanmax(np.where(np.isfinite(rel), rel, np.inf)) if len(rel) else 0.0
        if not worst <= rtol:
            bad.append(f"{name}.{mcol}: worst relative gap {worst:.3g}")
    extra = set(pooled.index) - set(maps.loc[maps["map"] == "pm2", "cell"])
    if extra:
        bad.append(f"cells in the regimes but not in the pm2 map: {sorted(extra)[:5]}")
    if bad:
        raise ValueError("regimes do not add up to the map: " + "; ".join(bad))


def write_regimes(results_dir: Path = Path("results/p2"), root: Path = REPO) -> Path:
    """Build ``fig_f1_regimes.csv`` from the capital and markouts parquet files and check it against the maps."""
    root, results_dir = Path(root), Path(results_dir)
    cap = pd.read_parquet(root / "data/p2/derived/capital.parquet",
                          columns=["trade_id", "currency", "ts", "maker_side", "K_sm", "K_pm", "K_pm2"])
    mk = pd.read_parquet(root / "data/p1/derived/markouts.parquet",
                         columns=["trade_id", "delta_bucket", "tenor_bucket", "index_price", "amount"])
    reg = cell_capital_by_regime(cap, mk)
    check_regimes_against_maps(reg, pd.read_csv(results_dir / "fig_edge_maps.csv"))
    path = results_dir / "fig_f1_regimes.csv"
    reg.to_csv(path, index=False)
    log.info("wrote %s (%d rows)", path, len(reg))
    return path


# =====================================================================================================================
# Tables behind the figure
# =====================================================================================================================

def _map(maps: pd.DataFrame, name: str) -> pd.DataFrame:
    m = maps[maps["map"] == name].drop_duplicates("cell").set_index("cell")
    return m.reindex(full_grid()["cell"])


def table_a(maps: pd.DataFrame) -> pd.DataFrame:
    """One row per cell of the 210-cell grid: fills, contracts, occupied and kappa under the three managers."""
    g = full_grid()
    pm2, sm, pm = _map(maps, "pm2"), _map(maps, "sm_pm2win"), _map(maps, "pm_pm2win")
    a = g.copy()
    a["fills"] = pm2["fills"].fillna(0).astype(int).to_numpy()
    a["contracts"] = pm2["contracts"].fillna(0.0).to_numpy(float)
    a["occupied"] = pm2["occupied"].fillna(False).astype(bool).to_numpy()
    for other, name in ((sm, "sm_pm2win"), (pm, "pm_pm2win")):
        have = other["fills"].notna().to_numpy()
        if not (np.array_equal(other["fills"].to_numpy()[have], pm2["fills"].to_numpy()[have])
                and np.allclose(other["contracts"].to_numpy(float)[have], pm2["contracts"].to_numpy(float)[have],
                                rtol=1e-12, atol=0.0)):
            raise ValueError(f"{name} does not hold the same fills as pm2")
    with np.errstate(invalid="ignore", divide="ignore"):
        a["kappa_pm2"] = (100 * pm2["sum_K"] / pm2["sum_index"]).to_numpy(float)
        a["kappa_sm"] = (100 * sm["sum_K"] / sm["sum_index"]).to_numpy(float)
        a["kappa_pm"] = (100 * pm["sum_K"] / pm["sum_index"]).to_numpy(float)
        a["q_sm"] = (sm["sum_K"] / pm2["sum_K"]).to_numpy(float)
        a["q_pm"] = (pm["sum_K"] / pm2["sum_K"]).to_numpy(float)
    a["shade"] = np.nan
    for side in SIDES:
        m = (a["side"] == side).to_numpy()
        sh, _, _ = shade_log(a.loc[m, "kappa_pm2"].to_numpy(float), a.loc[m, "occupied"].to_numpy(bool))
        a.loc[m, "shade"] = sh
    a["printed"] = [fmt_sig2(k) if o else "×" for k, o in zip(a["kappa_pm2"], a["occupied"])]
    return a


def table_b(a: pd.DataFrame, regimes: Optional[pd.DataFrame]) -> pd.DataFrame:
    """One row per mark in the strips: pooled SM and legacy ratios of the occupied cells, R4 SM ratios of the cells
    with at least 200 fills in R4. ``row`` counts from the top (0 to 7) within each side's strip."""
    rows = []
    r4 = None
    if regimes is not None:
        r4 = regimes[(regimes["regime"] == "R4") & (regimes["fills"] >= MIN_FILLS)].set_index("cell")
    for side in SIDES:
        for k, (mgr, ccy, regime, label) in enumerate(STRIP_ROWS):
            if regime == "R4" and r4 is None:
                continue
            if regime == "pooled":
                s = a[(a["side"] == side) & (a["ccy"] == ccy) & a["occupied"]]
                ratio = s[f"q_{mgr}"]
                cells = s[["cell", "delta_bucket", "tenor_bucket"]].assign(ratio=ratio.to_numpy(float))
            else:
                s = r4[(r4["side"] == side) & (r4["ccy"] == ccy)]
                with np.errstate(invalid="ignore", divide="ignore"):
                    ratio = (s["sum_K_sm_a"] / s["sum_K_pm2_a"]).to_numpy(float)
                cells = s.reset_index()[["cell", "delta_bucket", "tenor_bucket"]].assign(ratio=ratio)
            cells = cells[np.isfinite(cells["ratio"].to_numpy(float))]
            med = float(np.median(cells["ratio"])) if len(cells) else float("nan")
            for _, c in cells.iterrows():
                rows.append({"ccy": ccy, "side": side, "cell": c["cell"], "manager": mgr, "regime": regime,
                             "ratio": float(c["ratio"]), "row": k, "row_label": label,
                             "jitter": golden_jitter(cell_index(c["delta_bucket"], c["tenor_bucket"])),
                             "row_median": med, "row_n": len(cells), "printed_n": str(len(cells))})
    cols = ["ccy", "side", "cell", "manager", "regime", "ratio", "row", "jitter", "row_label", "row_median", "row_n",
            "printed_n"]
    return pd.DataFrame(rows, columns=cols)


def load_inputs(results_dir: Path) -> Dict[str, Optional[pd.DataFrame]]:
    results_dir = Path(results_dir)
    maps = pd.read_csv(results_dir / "fig_edge_maps.csv")
    reg_path = results_dir / "fig_f1_regimes.csv"
    regimes = pd.read_csv(reg_path) if reg_path.exists() else None
    if regimes is None:
        log.warning("%s missing: F1 is drawn without the R4 rows (section 10 fallback)", reg_path)
    else:
        check_regimes_against_maps(regimes, maps)
    return {"maps": maps, "regimes": regimes}


# =====================================================================================================================
# Figure
# =====================================================================================================================

# Layout in inches (canvas 7.0 x 3.9)
L_MAP = 0.79          # left edge of the first map
MAP_W = 1.25          # width of one map (five tenor columns)
MAP_GAP = 0.07
TOP_MAP = 3.40        # top edge of the upper maps
BOTTOM_MAP = 0.48     # bottom edge of the lower maps
ROW_GAP = 0.13        # between the upper and the lower maps
STRIP_L = 5.40        # left edge of the strips (labels sit to its left)
STRIP_R = 6.74        # right edge of the strips (cell counts sit to its right)


def _strip(ax, b: pd.DataFrame, side: str, top: bool) -> None:
    color_sm, _, mk_sm = MANAGER["sm"]
    color_pm, _, mk_pm = MANAGER["pm"]
    s = b[b["side"] == side]
    ax.set_xscale("log")
    ax.set_xlim(*X_LIM)
    ax.set_ylim(len(STRIP_ROWS) - 0.5, -0.5)
    ax.axvline(1.0, color=INK, ls="--", lw=0.8, zorder=1)
    trans = blended_transform_factory(ax.transAxes, ax.transData)
    labels = []
    for k, (mgr, ccy, regime, label) in enumerate(STRIP_ROWS):
        labels.append(label)
        r = s[s["row"] == k]
        if r.empty:
            continue
        y = k + r["jitter"].to_numpy(float)
        x = r["ratio"].to_numpy(float)
        if mgr == "sm" and regime == "pooled":
            ax.plot(x, y, ls="none", marker=mk_sm, ms=2.5, mfc=color_sm, mec=color_sm, mew=0.3, zorder=3)
        elif mgr == "sm":
            ax.plot(x, y, ls="none", marker=mk_sm, ms=2.5, mfc="none", mec=color_sm, mew=0.5, zorder=3)
        else:
            ax.plot(x, y, ls="none", marker=mk_pm, ms=2.5, mfc=color_pm, mec=color_pm, mew=0.3, zorder=3)
        med = float(r["row_median"].iloc[0])
        ax.plot([med, med], [k - 0.25, k + 0.25], color=INK, lw=1.2 if regime == "pooled" else 0.6,
                solid_capstyle="butt", zorder=4)
        ax.text(1.03, k, str(r["printed_n"].iloc[0]), transform=trans, fontsize=7.0, color=GREY, ha="left",
                va="center")
    ax.set_yticks(range(len(STRIP_ROWS)))
    ax.set_yticklabels(labels, fontsize=7.0)
    ax.tick_params(axis="y", length=0, pad=3.0)
    ax.set_xticks([0.6, 1, 2, 4])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels(["0.6", "1", "2", "4"] if not top else [], fontsize=7.0)
    for name in ("top", "right", "left"):
        ax.spines[name].set_visible(False)
    if top:
        tx = blended_transform_factory(ax.transData, ax.transAxes)
        ax.annotate("← PM2 dearer", xy=(1.0, 1.0), xycoords=tx, xytext=(-3, 5), textcoords="offset points",
                    ha="right", va="bottom", fontsize=7.0, color=INK)
        ax.annotate("PM2 cheaper →", xy=(1.0, 1.0), xycoords=tx, xytext=(3, 5), textcoords="offset points",
                    ha="left", va="bottom", fontsize=7.0, color=INK)
    else:
        ax.set_xlabel("capital ÷ PM2 capital,\nsame fills (log)", fontsize=7.0, labelpad=2.0)


def make_figure(results_dir: Path = Path("results/p2")):
    """Draw F1 from the files in ``results_dir``; returns (figure, {"a": table, "b": table})."""
    inputs = load_inputs(results_dir)
    a = table_a(inputs["maps"])
    b = table_b(a, inputs["regimes"])
    with matplotlib.rc_context(rc()):
        fig = plt.figure(figsize=(WIDTH, HEIGHT))
        map_h = (TOP_MAP - BOTTOM_MAP - ROW_GAP) / 2
        for r, side in enumerate(SIDES):
            top = TOP_MAP - r * (map_h + ROW_GAP)
            for c, ccy in enumerate(CCYS):
                ax = add_axes_in(fig, L_MAP + c * (MAP_W + MAP_GAP), top - map_h, MAP_W, map_h)
                occ = map_grid(a, "occupied", ccy, side, fill=False)
                draw_map(ax, occ, map_grid(a, "shade", ccy, side), map_grid(a, "printed", ccy, side, fill=""),
                         ylabels=(c == 0), xlabels=(r == 1))
                if r == 0:
                    ax.set_title(ccy, fontsize=8.0, fontweight="bold", pad=3.0)
            x, y = fig_xy(fig, 0.27, top - map_h / 2)  # row title between the axis title and the ticks
            fig.text(x, y, SIDE_TITLE[side], rotation=90, ha="center", va="center", fontsize=8.0,
                     multialignment="center")
            sax = add_axes_in(fig, STRIP_L, top - map_h, STRIP_R - STRIP_L, map_h)
            _strip(sax, b, side, top=(r == 0))
        x, y = fig_xy(fig, 0.075, (TOP_MAP + BOTTOM_MAP) / 2)
        fig.text(x, y, DELTA_TITLE, rotation=90, ha="center", va="center", fontsize=8.0)
        x, y = fig_xy(fig, L_MAP + 1.5 * MAP_W + MAP_GAP, 0.04)
        fig.text(x, y, TENOR_TITLE, ha="center", va="bottom", fontsize=8.0)
        x, y = fig_xy(fig, L_MAP, HEIGHT - 0.04)
        fig.text(x, y, HEADER, ha="left", va="top", fontsize=7.0, color=HEAD, linespacing=1.25)
    return fig, {"a": a, "b": b}


def build(out_dir: Path = Path("paper2/figures"), results_dir: Path = Path("results/p2")) -> List[Path]:
    """Write ``fig_f1_a.csv`` and ``fig_f1_b.csv`` to ``results_dir`` and ``f1.pdf`` / ``f1.png`` to ``out_dir``."""
    results_dir = Path(results_dir)
    fig, tables = make_figure(results_dir)
    paths = []
    a_cols = ["ccy", "side", "delta_bucket", "tenor_bucket", "cell", "fills", "contracts", "occupied", "kappa_pm2",
              "kappa_sm", "kappa_pm", "q_sm", "q_pm", "shade", "printed"]
    for key, frame in (("a", tables["a"][a_cols]), ("b", tables["b"])):
        p = results_dir / f"fig_{SLOT}_{key}.csv"
        frame.to_csv(p, index=False)
        paths.append(p)
    with matplotlib.rc_context(rc()):
        paths += figstyle.save(to_print(fig), SLOT, Path(out_dir))       # the width main.tex sets the figure at
    return paths


# =====================================================================================================================
# Checks: value in the figure (fig_f1_*.csv) against the inference files in results/p2
# =====================================================================================================================

def _csv(rd, name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(Path(rd) / name, **kw)


def _a(rd) -> pd.DataFrame:
    return _csv(rd, "fig_f1_a.csv", keep_default_na=False, na_values=[""])


def _pm2(rd) -> pd.DataFrame:
    m = _csv(rd, "fig_edge_maps.csv")
    return m[m["map"] == "pm2"]


def _src_ratio(rd, other: str) -> pd.DataFrame:
    m = _csv(rd, "fig_edge_maps.csv")
    p = m[(m["map"] == "pm2") & m["occupied"]].set_index("cell")
    o = m[m["map"] == other].set_index("cell").reindex(p.index)
    r = (o["sum_K"] / p["sum_K"]).dropna()
    return pd.DataFrame({"ratio": r, "ccy": p.loc[r.index, "ccy"], "side": p.loc[r.index, "side"]})


def _fig_ratio(rd, mgr: str, regime: str = "pooled") -> pd.DataFrame:
    b = _csv(rd, "fig_f1_b.csv")
    return b[(b["manager"] == mgr) & (b["regime"] == regime)]


def _crosses_by_ccy_fig(rd):
    a = _a(rd)
    return {c: int((a.loc[a["ccy"] == c, "printed"] == "×").sum()) for c in CCYS}


def _crosses_by_ccy_src(rd):
    p = _pm2(rd)
    return {c: int(len(DELTA_LABELS) * len(TENOR_LABELS) * len(SIDES) - p[(p["ccy"] == c)]["occupied"].sum())
            for c in CCYS}


def _kappa_span_fig(rd):
    a = _a(rd)
    a = a[a["occupied"].astype(str) == "True"]
    return {f"{c}|{s}": (round(float(g["kappa_pm2"].min()), 9), round(float(g["kappa_pm2"].max()), 9))
            for (c, s), g in a.groupby(["ccy", "side"])}


def _kappa_span_src(rd):
    h = _csv(rd, "h1_cells.csv")
    h = h[h["occupied"]]
    k = 100 * h["sum_K"] / h["sum_index"]
    return {f"{c}|{s}": (round(float(k[g.index].min()), 9), round(float(k[g.index].max()), 9))
            for (c, s), g in h.groupby(["ccy", "side"])}


def _kappa_gap(rd):
    a = _a(rd).set_index("cell")
    h = _csv(rd, "h1_cells.csv").set_index("cell")
    h = h[h["occupied"]]
    k = 100 * h["sum_K"] / h["sum_index"]
    return float(np.max(np.abs(a.loc[k.index, "kappa_pm2"].astype(float) - k)))


def _printed_fig(rd):
    a = _a(rd)
    return dict(zip(a["cell"], a["printed"].fillna("")))


def _printed_src(rd):
    h = _csv(rd, "h1_cells.csv").set_index("cell")
    out = {}
    for cell in full_grid()["cell"]:
        if cell in h.index and bool(h.loc[cell, "occupied"]):
            out[cell] = fmt_sig2(100 * h.loc[cell, "sum_K"] / h.loc[cell, "sum_index"])
        else:
            out[cell] = "×"
    return out


def _range_count(frame: pd.DataFrame):
    r = frame["ratio"].astype(float)
    return round(float(r.min()), 9), round(float(r.max()), 9), int(len(r)), int((r < 1).sum())


def _medians(frame: pd.DataFrame, side: str = "sell"):
    f = frame[frame["side"] == side]
    return {c: round(float(np.median(g["ratio"])), 9) for c, g in f.groupby("ccy")}


def _fills_equal_src(rd):
    m = _csv(rd, "fig_edge_maps.csv")
    p = m[m["map"] == "pm2"].set_index("cell")
    ok = True
    for name in ("sm_pm2win", "pm_pm2win"):
        o = m[m["map"] == name].set_index("cell")
        ok &= bool((o["fills"] == p.loc[o.index, "fills"]).all())
        ok &= bool(np.allclose(o["contracts"], p.loc[o.index, "contracts"], rtol=1e-12, atol=0))
    return ok


def _fills_fig(rd):
    a = _a(rd).set_index("cell")
    return {c: int(v) for c, v in a["fills"].items() if int(v) > 0}


def _fills_src(rd):
    p = _pm2(rd).set_index("cell")
    return {c: int(v) for c, v in p["fills"].items() if int(v) > 0}


def _regimes_add_up(rd):
    try:
        check_regimes_against_maps(_csv(rd, "fig_f1_regimes.csv"), _csv(rd, "fig_edge_maps.csv"))
        return True
    except (ValueError, FileNotFoundError):
        return False


def _r4_src(rd):
    r = _csv(rd, "fig_f1_regimes.csv")
    r = r[(r["regime"] == "R4") & (r["fills"] >= MIN_FILLS) & (r["side"] == "sell")]
    return {c: round(float(np.median(g["sum_K_sm_a"] / g["sum_K_pm2_a"])), 9) for c, g in r.groupby("ccy")}


def _regime_bounds_src(rd):
    """PM2 events of both BTC and ETH whose jump of the PM2 reference book is at least 3 log-% in both (6.6)."""
    e = _csv(rd, "events.csv")
    e = e[e["manager"] == "pm2"]
    r = _csv(rd, "reference_book.csv")
    both = sorted(set(e.loc[e["ccy"] == "BTC", "event_ts"]) & set(e.loc[e["ccy"] == "ETH", "event_ts"]))
    out = []
    for ts in both:
        ok = True
        for c in ("BTC", "ETH"):
            last = e.loc[(e["ccy"] == c) & (e["event_ts"] == ts), "last_ts"].iloc[0]
            j = r[(r["ccy"] == c) & (r["pm2_param_ts"] == last) & (r["pm2_param_ts_prev"] != last)]
            ok &= len(j) > 0 and abs(100 * np.log(j["K_pm2"].iloc[0] / j["K_pm2_prev"].iloc[0])) >= 3.0
        if ok:
            out.append(int(ts))
    return tuple(out)


CHECKS: List[dict] = [
    {"name": "cells in the grid", "figure": lambda rd: int(len(_a(rd))),
     "source": lambda rd: N_GRID, "pilot": 210},
    {"name": "occupied cells", "figure": lambda rd: int((_a(rd)["printed"] != "×").sum()),
     "source": lambda rd: int(_pm2(rd)["occupied"].sum()), "pilot": 173},
    {"name": "crosses (under 200 fills, incl. empty combinations)",
     "figure": lambda rd: int((_a(rd)["printed"] == "×").sum()),
     "source": lambda rd: N_GRID - int(_pm2(rd)["occupied"].sum()), "pilot": 37},
    {"name": "crosses by currency", "figure": _crosses_by_ccy_fig, "source": _crosses_by_ccy_src,
     "pilot": {"BTC": 10, "ETH": 2, "HYPE": 25}},
    {"name": "fills per cell = pm2 map", "figure": _fills_fig, "source": _fills_src},
    {"name": "fills and contracts equal in pm2, sm_pm2win, pm_pm2win", "figure": lambda rd: True,
     "source": _fills_equal_src},
    {"name": "kappa = 100 sum_K / sum_index of h1_cells (max abs gap)", "figure": _kappa_gap,
     "source": lambda rd: 0.0, "atol": 1e-12, "pilot": 0.0},
    {"name": "printed kappa (two significant digits) and crosses", "figure": _printed_fig, "source": _printed_src},
    {"name": "kappa span of occupied cells by currency and side", "figure": _kappa_span_fig,
     "source": _kappa_span_src,
     "pilot": {"BTC|sell": (7.80, 17.69), "BTC|buy": (0.07, 10.86), "ETH|sell": (7.07, 21.36),
               "ETH|buy": (0.08, 14.53), "HYPE|sell": (17.50, 38.73), "HYPE|buy": (0.46, 15.64)}},
    {"name": "q_SM min, max, cells, cells below 1", "figure": lambda rd: _range_count(_fig_ratio(rd, "sm")),
     "source": lambda rd: _range_count(_src_ratio(rd, "sm_pm2win")), "pilot": (0.752, 4.669, 173, 86)},
    {"name": "q_PM min, max, cells, cells below 1", "figure": lambda rd: _range_count(_fig_ratio(rd, "pm")),
     "source": lambda rd: _range_count(_src_ratio(rd, "pm_pm2win")), "pilot": (0.946, 1.736, 128, None)},
    {"name": "median q_SM of the sell cells by currency", "figure": lambda rd: _medians(_fig_ratio(rd, "sm")),
     "source": lambda rd: _medians(_src_ratio(rd, "sm_pm2win")),
     "pilot": {"BTC": 0.943, "ETH": 0.902, "HYPE": 0.875}},
    {"name": "regimes R1 to R4 add up to the maps (relative <= 1e-9)", "figure": lambda rd: True,
     "source": _regimes_add_up},
    {"name": "R4 median q_SM of the sell cells by currency", "figure": lambda rd: _medians(_fig_ratio(rd, "sm", "R4")),
     "source": _r4_src, "pilot": {"BTC": 1.398, "ETH": 1.140, "HYPE": 1.444}},
    {"name": "regime bounds = BTC PM2 events", "figure": lambda rd: REGIME_BOUNDS, "source": _regime_bounds_src},
    {"name": "no strip mark outside the x axis", "figure": lambda rd: int(
        ((_csv(rd, "fig_f1_b.csv")["ratio"] < X_LIM[0]) | (_csv(rd, "fig_f1_b.csv")["ratio"] > X_LIM[1])).sum()),
     "source": lambda rd: 0},
]


def _same(x, y, rtol: float = 0.0, atol: float = 0.0) -> bool:
    if isinstance(x, dict) and isinstance(y, dict):
        return x.keys() == y.keys() and all(_same(x[k], y[k], rtol, atol) for k in x)
    if isinstance(x, (tuple, list)) and isinstance(y, (tuple, list)):
        return len(x) == len(y) and all(_same(a, b, rtol, atol) for a, b in zip(x, y))
    if isinstance(x, (bool, np.bool_)) or isinstance(y, (bool, np.bool_)) or isinstance(x, str) or isinstance(y, str):
        return x == y
    try:
        fx, fy = float(x), float(y)
    except (TypeError, ValueError):
        return x == y
    return bool(np.isclose(fx, fy, rtol=rtol, atol=atol)) or fx == fy


def _pilot_same(x, pilot, digits: int = 3) -> Optional[bool]:
    """Pilot values of the building brief are rounded; compare at their precision (None entries skipped)."""
    if pilot is None:
        return None
    if isinstance(pilot, dict) and isinstance(x, dict):
        return x.keys() == pilot.keys() and all(_pilot_same(x[k], pilot[k], digits) is not False for k in pilot)
    if isinstance(pilot, (tuple, list)) and isinstance(x, (tuple, list)):
        return len(x) == len(pilot) and all(_pilot_same(a, b, digits) is not False for a, b in zip(x, pilot))
    if isinstance(pilot, float):
        dec = max(len(repr(pilot).split(".")[1]) if "." in repr(pilot) else 0, 0)
        return abs(float(x) - pilot) <= 0.5 * 10 ** (-dec) + 1e-12
    return x == pilot


def run_checks(results_dir: Path = Path("results/p2")) -> pd.DataFrame:
    """Evaluate every check; ``ok`` compares figure and source, ``pilot_ok`` the pilot cut of the brief."""
    rows = []
    for c in CHECKS:
        try:
            fv, sv = c["figure"](results_dir), c["source"](results_dir)
            ok = _same(fv, sv, c.get("rtol", 0.0), c.get("atol", 0.0))
            err = ""
        except Exception as exc:  # noqa: BLE001 - reported, not raised
            fv = sv = None
            ok, err = False, repr(exc)
        rows.append({"slot": SLOT, "check": c["name"], "figure": fv, "source": sv, "ok": bool(ok),
                     "pilot": c.get("pilot"), "pilot_ok": _pilot_same(fv, c.get("pilot")) if fv is not None else None,
                     "error": err})
    return pd.DataFrame(rows)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", type=Path, default=Path("results/p2"))
    ap.add_argument("--out", type=Path, default=Path("paper2/figures"))
    ap.add_argument("--regimes", action="store_true", help="rebuild fig_f1_regimes.csv from the parquet files")
    ap.add_argument("--check", action="store_true", help="print the checks after the build")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    log.setLevel(logging.INFO)
    if args.regimes or not (args.results / "fig_f1_regimes.csv").exists():
        write_regimes(args.results)
    for p in build(args.out, args.results):
        print("wrote", p)
    if args.check:
        res = run_checks(args.results)
        with pd.option_context("display.width", 200, "display.max_colwidth", 80):
            print(res[["check", "ok", "pilot_ok", "figure", "error"]].to_string(index=False))
        return 0 if res["ok"].all() else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
