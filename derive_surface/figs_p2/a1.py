"""A1 · Does the replica match the chain? (FIGURE_SELECTION.md section 7, A1, appendix), 7.0 x 2.5 in.

Absolute relative deviation of initial-margin capital between the offline replicas and ``eth_call`` on the deployed
managers, from ``results/p2/validation.csv`` (``status == "ok"``, ``is_initial``; maintenance margin only in the
tables) and the registered bounds of ``validation_summary.json``.

* a: single contracts, one row per underlying and manager (``kind == "single"``), points jittered by row, median as a
  thick tick, 95th percentile as a thin tick, n on the right.
* b: the opening books of the maker-days (``kind == "book"``) against their number of legs.

x (a) and y (b) are logarithmic from 1e-13 to 1e-1. Exact zeros are drawn in a separate grey strip (left of a, below
b); deviations above zero but below 1e-13 (floating-point residue, down to about 1e-16) are drawn on the axis edge,
labelled "≤1e−13". The caption sentence on feed ages is checked against ``data/p2/derived/capital.parquet``: every
fill in the PM2 window must use a vol feed no older than ``p2validate.MAX_VOL_AGE`` and a forward no older than
``p2validate.MAX_FWD_AGE`` (the limits of the validation blocks); otherwise the sentence is left out. The spot feed
has no such limit in the validation; the sentence counts the fills whose spot price is older than the heartbeat of the
spot feed (``p2feeds.HEARTBEAT["spot"]``), which stay in the sample as registered.

Command line: ``python3 -m derive_surface.figs_p2.a1`` (writes ``paper2/figures/a1.{pdf,png}`` and
``results/p2/fig_a1_{a,b,meta}.csv``, prints the checks).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.transforms as mtransforms  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FixedLocator, NullFormatter  # noqa: E402

from .. import p2feeds, p2validate  # noqa: E402
from . import _kit_t2a1 as kit  # noqa: E402

SLOT = "a1"
WIDTH, HEIGHT = 7.0, 2.5
VALIDATION = Path("validation.csv")
SUMMARY = Path("validation_summary.json")
CAPITAL = Path("data/p2/derived/capital.parquet")
ROWS = [("BTC", "sm"), ("BTC", "pm"), ("BTC", "pm2"), ("ETH", "sm"), ("ETH", "pm"), ("ETH", "pm2"),
        ("HYPE", "sm"), ("HYPE", "pm2")]
X_LO, X_HI = 1e-13, 1e-1
MAJOR = [1e-13, 1e-11, 1e-9, 1e-7, 1e-5, 1e-3, 1e-1]
JITTER = 0.2
STRIP_SPREAD = 0.6          # horizontal spread of exact zeros inside the strip (strip x runs from -1 to 1)
SEED = 20260924
STRIP_BG = "#E6E6E6"
MS_SINGLE, MS_BOOK = 2.0, 3.0

FEED_SENTENCE = "In the PM2 window no fill uses a vol or forward feed older than the limits of the validation blocks"
SPOT_CLAUSE = ("; {n} fills use a spot price older than the heartbeat of the spot feed ({hb} seconds) and stay in the "
               "sample.")
SPOT_NONE = (", and none uses a spot price older than the heartbeat of the spot feed ({hb} seconds).")
_CAPTION_HEAD = (
    r"\textbf{Does the replica match the chain?} Absolute relative deviation of initial-margin capital between each "
    r"offline replica and \texttt{eth\_call} on the deployed contracts, for single contracts per underlying and "
    r"manager (panel a) and for the opening books of 20 maker-days against their number of legs (panel b). Exact "
    r"matches sit in the strip on the left of panel a and at the bottom of panel b; deviations below $10^{-13}$ sit "
    r"on the edge of the axis. Thick ticks mark the median of a row, thin ticks its 95th percentile. The lines are "
    r"the registered bounds for the median (0.1 per cent) and the 95th percentile (1 per cent). One single HYPE "
    r"contract under PM2 hit a reverting call and is left out."
)
_CAPTION_TAIL = r"The replica follows the contracts on chain; the venue's off-chain engine discounts PM2 at a flat two " \
                r"per cent."
# the spot clause with placeholders, as a literal: scripts/p2_build.py reads CAPTION without importing the module
_SPOT_CLAUSE_PH = (r"; \PH{a1-spot-stale} fills use a spot price older than the heartbeat of the spot feed "
                   r"(\PH{a1-spot-heartbeat} seconds) and stay in the sample.")
CAPTION = " ".join([_CAPTION_HEAD, FEED_SENTENCE + _SPOT_CLAUSE_PH, _CAPTION_TAIL])


def feed_sentence(fa: dict) -> str:
    """The feed-age sentence of the caption: vol and forward within the validation limits, and the count of fills
    with a spot price older than the spot heartbeat; empty unless ``capital.parquet`` confirms the first part."""
    if fa["holds"] is not True:
        return ""
    n, hb = int(fa["spot_stale_fills"]), f"{fa['spot_limit_s']:g}"
    return FEED_SENTENCE + (SPOT_CLAUSE.format(n=n, hb=hb) if n > 0 else SPOT_NONE.format(hb=hb))


def caption(data: dict) -> str:
    """The caption; the feed-age sentence only when ``capital.parquet`` confirms it."""
    sentence = feed_sentence(data["feed_age"])
    return " ".join([_CAPTION_HEAD] + ([sentence] if sentence else []) + [_CAPTION_TAIL])


# ---------------------------------------------------------------------------------------------------- data

def _bool(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().isin(["true", "1"])


def points(validation: pd.DataFrame) -> pd.DataFrame:
    """Every ``ok`` row (IM and MM) with its drawing position: ``strip`` (exact zero), ``at_edge`` (0 < |rel| <
    1e-13, drawn on the edge), ``x_plot`` (|rel| clipped at 1e-13; NaN in the strip), ``row`` and ``jitter`` for the
    singles, ``drawn`` = initial margin."""
    v = validation.copy()
    v["is_initial"] = _bool(v["is_initial"])
    v = v[v["status"] == "ok"].copy()
    rel = v["rel_err"].astype(float).abs()
    v["abs_rel"] = rel
    v["strip"] = rel == 0.0
    v["at_edge"] = (rel > 0.0) & (rel < X_LO)
    v["x_plot"] = np.where(v["strip"], np.nan, np.maximum(rel, X_LO))
    row = {k: i for i, k in enumerate(ROWS)}
    v["row"] = [row.get((c, m), -1) if k == "single" else -1 for c, m, k in zip(v["ccy"], v["manager"], v["kind"])]
    v = v.sort_values(["kind", "row", "ccy", "manager", "is_initial", "block", "book"], kind="mergesort")
    rng = np.random.default_rng(SEED)
    v["jitter"] = np.where(v["kind"] == "single", rng.uniform(-JITTER, JITTER, len(v)), 0.0)
    # exact zeros of the singles are spread across the width of the strip, so that their number shows
    v["strip_x"] = np.where(v["strip"] & (v["kind"] == "single"), rng.uniform(-STRIP_SPREAD, STRIP_SPREAD, len(v)),
                            np.where(v["strip"], 0.0, np.nan))
    v["drawn"] = v["is_initial"]
    return v.reset_index(drop=True)


def row_stats(pts: pd.DataFrame) -> pd.DataFrame:
    """n, median, 95th percentile (linear), maximum and exact zeros of |rel| per single row, IM and MM."""
    out = []
    for im in (True, False):
        for i, (ccy, mgr) in enumerate(ROWS):
            g = pts[(pts["kind"] == "single") & (pts["ccy"] == ccy) & (pts["manager"] == mgr)
                    & (pts["is_initial"] == im)]["abs_rel"].to_numpy(dtype=float)
            out.append({"row": i, "ccy": ccy, "manager": mgr, "is_initial": im, "n": int(len(g)),
                        "median": float(np.median(g)) if len(g) else np.nan,
                        "p95": float(np.percentile(g, 95)) if len(g) else np.nan,
                        "max": float(g.max()) if len(g) else np.nan, "exact_zeros": int((g == 0).sum())})
    return pd.DataFrame(out)


def feed_age(capital_path: Optional[Path]) -> dict:
    """Largest vol and forward feed age over the fills of the PM2 window, against the validation limits, and the
    fills of the window whose spot price is older than the spot heartbeat."""
    lim = {"vol_limit_s": float(p2validate.MAX_VOL_AGE), "fwd_limit_s": float(p2validate.MAX_FWD_AGE),
           "spot_limit_s": float(p2feeds.HEARTBEAT["spot"])}
    if capital_path is None or not Path(capital_path).exists():
        return dict(lim, vol_age_max_s=np.nan, fwd_age_max_s=np.nan, spot_age_max_s=np.nan, spot_stale_fills=0,
                    fills=0, holds=None, capital_path="")
    c = pd.read_parquet(capital_path, columns=["currency", "ts", "vol_age", "fwd_age", "spot_age"])
    ts = c["ts"].astype("int64")
    ts = ts // 1000 if len(ts) and ts.max() > 10 ** 11 else ts      # capital.parquet keeps the tape's milliseconds
    start = c["currency"].map(p2validate.PM2_START_TS)
    w = c[start.notna() & (ts >= start)]
    vmax, fmax = float(w["vol_age"].max()), float(w["fwd_age"].max())
    holds = bool(len(w) > 0 and w["vol_age"].notna().all() and w["fwd_age"].notna().all()
                 and vmax <= lim["vol_limit_s"] and fmax <= lim["fwd_limit_s"])
    return dict(lim, vol_age_max_s=vmax, fwd_age_max_s=fmax, spot_age_max_s=float(w["spot_age"].max()),
                spot_stale_fills=int((w["spot_age"] > lim["spot_limit_s"]).sum()), fills=int(len(w)), holds=holds,
                capital_path=str(capital_path))


def load(results_dir: Path = Path("results/p2"), capital_path: Optional[Path] = CAPITAL) -> dict:
    rd = Path(results_dir)
    raw = pd.read_csv(rd / VALIDATION)
    summary = json.loads((rd / SUMMARY).read_text())
    pts = points(raw)
    rev = raw[raw["status"] == "revert"]
    books = pts[(pts["kind"] == "book") & pts["is_initial"]]
    per_ccy = books[["book", "ccy"]].drop_duplicates().groupby("ccy").size().to_dict()
    return {"points": pts, "stats": row_stats(pts), "thresholds": dict(summary["thresholds"]),
            "revert_rows": int(len(rev)),
            "revert_cases": int(len(rev[["ccy", "manager", "kind", "block", "expiry", "strike", "is_call", "amount"]]
                                    .astype(str).drop_duplicates())),
            "books": int(len(books[["book", "ccy"]].drop_duplicates())), "maker_days": int(books["book"].nunique()),
            "books_per_ccy": {k: int(per_ccy.get(k, 0)) for k in ("BTC", "ETH", "HYPE")},
            "largest_miss": float(books["abs_err"].abs().max()), "K_max": float(books["K_chain"].abs().max()),
            "feed_age": feed_age(capital_path)}


# ---------------------------------------------------------------------------------------------------- printed text

def _bound(kind: str, value: float) -> str:
    return f"{'median' if kind == 'median' else 'p95'} bound {100 * value:g}{kit.THIN}%"


def book_texts(data: dict) -> Dict[str, str]:
    c = data["books_per_ccy"]
    return {"books": f"{data['books']} books from {data['maker_days']} maker-days\n"
                     f"(BTC {c['BTC']}, ETH {c['ETH']}, HYPE {c['HYPE']})",
            "miss": f"largest miss {data['largest_miss']:.2f} USDC\non K up to {data['K_max'] / 1e6:.1f} M USDC"}


def _tick_labels() -> List[str]:
    return [("≤" + kit.sci(x)) if x == X_LO else kit.sci(x) for x in MAJOR]


# ---------------------------------------------------------------------------------------------------- tables

def tables(data: dict) -> Dict[str, pd.DataFrame]:
    pts = data["points"]
    cols = ["item", "kind", "ccy", "manager", "row", "is_initial", "drawn", "block", "ts", "book", "n_legs", "K_chain",
            "K_replica", "abs_err", "rel_err", "strip", "at_edge", "x_plot", "jitter", "strip_x", "value",
            "printed"]
    th = data["thresholds"]
    thr = [{"item": "threshold", "manager": k, "value": float(th[k]), "printed": _bound(k, float(th[k])),
            "drawn": True} for k in ("median", "p95")]
    single = pts[pts["kind"] == "single"].assign(item="point", value=np.nan, printed="")
    st = []
    for _, r in data["stats"].iterrows():
        base = {"kind": "single", "ccy": r["ccy"], "manager": r["manager"], "row": int(r["row"]),
                "is_initial": bool(r["is_initial"]), "drawn": bool(r["is_initial"])}
        st += [dict(base, item="n", value=float(r["n"]), printed=f"n {int(r['n'])}"),
               dict(base, item="median", value=r["median"], printed=""),
               dict(base, item="p95", value=r["p95"], printed=""),
               dict(base, item="max", value=r["max"], printed="", drawn=False),
               dict(base, item="exact_zeros", value=float(r["exact_zeros"]), printed="", drawn=False)]
    a = pd.concat([single, pd.DataFrame(st), pd.DataFrame(thr),
                   pd.DataFrame([{"item": "revert_cases", "kind": "single", "value": float(data["revert_cases"]),
                                  "drawn": False, "printed": ""},
                                 {"item": "revert_rows", "kind": "single", "value": float(data["revert_rows"]),
                                  "drawn": False, "printed": ""}])], ignore_index=True)
    bk = pts[pts["kind"] == "book"].assign(item="point", value=np.nan, printed="")
    txt = book_texts(data)
    extra = [{"item": "books", "value": float(data["books"]), "printed": txt["books"]},
             {"item": "maker_days", "value": float(data["maker_days"]), "printed": txt["books"]}]
    extra += [{"item": f"books_{k}", "value": float(v), "printed": txt["books"]}
              for k, v in data["books_per_ccy"].items()]
    extra += [{"item": "largest_miss_usdc", "value": data["largest_miss"], "printed": txt["miss"]},
              {"item": "K_chain_max_usdc", "value": data["K_max"], "printed": txt["miss"]}]
    b = pd.concat([bk, pd.DataFrame([dict(e, kind="book", drawn=True) for e in extra]), pd.DataFrame(thr)],
                  ignore_index=True)
    fa = data["feed_age"]
    meta = pd.DataFrame([{"key": k, "value": v} for k, v in (
        ("x_lo", X_LO), ("x_hi", X_HI), ("revert_cases", data["revert_cases"]), ("revert_rows", data["revert_rows"]),
        ("vol_age_max_s", fa["vol_age_max_s"]), ("fwd_age_max_s", fa["fwd_age_max_s"]),
        ("vol_limit_s", fa["vol_limit_s"]), ("fwd_limit_s", fa["fwd_limit_s"]), ("pm2_window_fills", fa["fills"]),
        ("spot_age_max_s", fa["spot_age_max_s"]), ("spot_limit_s", fa["spot_limit_s"]),
        ("spot_stale_fills", fa["spot_stale_fills"]),
        ("feed_sentence_holds", fa["holds"]), ("capital_path", fa["capital_path"]))])
    meta["printed"] = np.where(meta["key"] == "feed_sentence_holds", feed_sentence(fa), "")
    return {"fig_a1_a.csv": a[cols], "fig_a1_b.csv": b[cols], "fig_a1_meta.csv": meta}


# ---------------------------------------------------------------------------------------------------- figure

def draw(data: dict):
    fig = kit.new_figure(WIDTH, HEIGHT)
    _panel_a(fig, data)
    _panel_b(fig, data)
    return fig


def _log_axis(axis) -> None:
    axis.set_major_locator(FixedLocator(MAJOR))
    axis.set_minor_locator(FixedLocator([10.0 ** e for e in range(-13, 0)]))
    axis.set_minor_formatter(NullFormatter())


def _mgr_style(mgr: str) -> dict:
    color, _ls, marker = kit.MANAGER[mgr]
    return {"marker": marker, "mfc": "none", "mec": color, "ls": "none"}


def _panel_a(fig, data: dict) -> None:
    top, height = 0.42, 1.68
    kit.letter(fig, 0.02, 0.04, "a")
    kit.fig_text(fig, 0.17, 0.04, "single contracts", fontsize=8.0)
    strip = kit.axes_at(fig, 0.87, top, 0.20, height)
    ax = kit.axes_at(fig, 1.13, top, 2.65, height, sharey=strip)
    strip.set_facecolor(STRIP_BG)
    for s in ("left", "bottom"):
        strip.spines[s].set_visible(False)
    strip.set_xlim(-1, 1)
    strip.set_xticks([])
    pts = data["points"]
    single = pts[(pts["kind"] == "single") & pts["drawn"]]
    for (ccy, mgr), g in single.groupby(["ccy", "manager"], sort=False):
        st = _mgr_style(mgr)
        y = g["row"] + g["jitter"]
        z = g["strip"].to_numpy()
        ax.plot(g["x_plot"][~z], y[~z], ms=MS_SINGLE, mew=0.45, clip_on=False, zorder=3, **st)
        strip.plot(g["strip_x"][z], y[z], ms=MS_SINGLE, mew=0.45, zorder=3, **st)
    stats = data["stats"][data["stats"]["is_initial"]]
    for _, r in stats.iterrows():
        y = float(r["row"])
        for key, lw in (("median", 1.2), ("p95", 0.6)):
            val = float(r[key])
            if not np.isfinite(val):
                continue
            target, x = (strip, 0.0) if val == 0.0 else (ax, max(val, X_LO))
            target.plot([x, x], [y - 0.3, y + 0.3], color="black", lw=lw, solid_capstyle="butt", zorder=4)
        ax.annotate(f"n {int(r['n'])}", xy=(1.0, y), xycoords=mtransforms.blended_transform_factory(
            ax.transAxes, ax.transData), xytext=(4, 0), textcoords="offset points", ha="left", va="center",
                    fontsize=kit.FS_MIN, color=kit.GREY)
    th = data["thresholds"]
    ax.axvline(th["median"], color="black", lw=0.8, ls="--", zorder=1)
    ax.axvline(th["p95"], color="black", lw=0.8, ls="-.", zorder=1)
    tr = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
    ax.annotate(_bound("median", th["median"]), xy=(th["median"], 1.0), xycoords=tr, xytext=(-2, 2),
                textcoords="offset points", ha="right", va="bottom", fontsize=kit.FS_MIN)
    lift = 0.155 / height                                  # the p95 label sits one line higher
    ax.plot([th["p95"], th["p95"]], [1.0, 1.0 + lift], transform=tr, color="black", lw=0.8, ls="-.", clip_on=False)
    ax.annotate(_bound("p95", th["p95"]), xy=(th["p95"], 1.0 + lift), xycoords=tr, xytext=(-2, 0),
                textcoords="offset points", ha="right", va="bottom", fontsize=kit.FS_MIN)
    strip.annotate("exact", xy=(0.5, 1.0), xycoords="axes fraction", xytext=(0, 2), textcoords="offset points",
                   ha="center", va="bottom", fontsize=kit.FS_MIN)
    ax.set_xscale("log")
    ax.set_xlim(X_LO, X_HI)
    _log_axis(ax.xaxis)
    ax.set_xticklabels(_tick_labels())
    ax.set_xlabel("|relative deviation of K|, replica vs eth_call")
    strip.set_ylim(len(ROWS) - 0.5, -0.5)
    strip.set_yticks(range(len(ROWS)))
    strip.set_yticklabels([f"{c} {kit.MANAGER_LABEL[m]}" for c, m in ROWS])
    strip.tick_params(axis="y", length=0, pad=3)
    ax.tick_params(axis="y", which="both", left=False, labelleft=False)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", which="major", color="#DDDDDD", lw=0.4, zorder=0)
    key = [Line2D([], [], ls="none", marker="|", ms=7, mew=1.2, color="black", label="median"),
           Line2D([], [], ls="none", marker="|", ms=7, mew=0.6, color="black", label="p95")]
    ax.legend(handles=key, loc="lower right", bbox_to_anchor=(0.80, 0.0), frameon=False, handlelength=0.8,
              handletextpad=0.4, borderaxespad=0.2, labelspacing=0.2)


def _panel_b(fig, data: dict) -> None:
    top, h_main, gap, h_strip = 0.42, 1.49, 0.05, 0.14
    left, width = 4.98, 1.97
    kit.letter(fig, 4.42, 0.04, "b")
    kit.fig_text(fig, 4.57, 0.04, "opening books", fontsize=8.0)
    ax = kit.axes_at(fig, left, top, width, h_main)
    strip = kit.axes_at(fig, left, top + h_main + gap, width, h_strip, sharex=ax)
    strip.set_facecolor(STRIP_BG)
    strip.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    pts = data["points"]
    books = pts[(pts["kind"] == "book") & pts["drawn"]]
    handles = []
    for mgr in ("sm", "pm", "pm2"):
        g = books[books["manager"] == mgr]
        if g.empty:
            continue
        st = _mgr_style(mgr)
        z = g["strip"].to_numpy()
        ax.plot(g["n_legs"][~z], g["x_plot"][~z], ms=MS_BOOK, mew=0.6, clip_on=False, zorder=3, **st)
        strip.plot(g["n_legs"][z], np.zeros(int(z.sum())), ms=MS_BOOK, mew=0.6, clip_on=False, zorder=3, **st)
        handles.append(Line2D([], [], ms=MS_BOOK + 0.6, mew=0.7, label=kit.MANAGER_LABEL[mgr], **st))
    th = data["thresholds"]
    ax.axhline(th["median"], color="black", lw=0.8, ls="--", zorder=1)
    ax.axhline(th["p95"], color="black", lw=0.8, ls="-.", zorder=1)
    tr = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    for k in ("median", "p95"):
        ax.annotate(_bound(k, th[k]), xy=(1.0, th[k]), xycoords=tr, xytext=(0, 1.5), textcoords="offset points",
                    ha="right", va="bottom", fontsize=kit.FS_MIN)
    txt = book_texts(data)
    ax.annotate(txt["books"] + "\n" + txt["miss"], xy=(0.0, th["median"]), xycoords=tr, xytext=(3, -3),
                textcoords="offset points", ha="left", va="top", fontsize=kit.FS_MIN, linespacing=1.15)
    ax.set_yscale("log")
    ax.set_ylim(X_LO, X_HI)
    _log_axis(ax.yaxis)
    ax.set_yticklabels(_tick_labels())
    ax.set_ylabel("|relative deviation of K|")
    ax.grid(axis="y", which="major", color="#DDDDDD", lw=0.4, zorder=0)
    ax.set_xscale("log")
    ax.set_xlim(2, 300)
    ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
    strip.set_ylim(-1, 1)
    strip.set_yticks([0])
    strip.set_yticklabels(["exact"])
    strip.tick_params(axis="y", length=0, pad=6)
    ticks = [2, 5, 10, 20, 50, 100, 200]
    strip.xaxis.set_major_locator(FixedLocator(ticks))
    strip.xaxis.set_minor_locator(FixedLocator([3, 4, 6, 7, 8, 9, 30, 40, 60, 70, 80, 90, 300]))
    strip.xaxis.set_minor_formatter(NullFormatter())
    strip.set_xticklabels([str(t) for t in ticks])
    strip.set_xlabel("legs in the book")
    W, H = fig.get_size_inches()
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(left / W, 1.0 - (top - 0.03) / H), ncol=3,
               handletextpad=0.2, columnspacing=1.0, borderaxespad=0.0, borderpad=0.0, frameon=False,
               handlelength=1.0)


# ---------------------------------------------------------------------------------------------------- build

def build(out_dir: Path = Path("paper2/figures"), results_dir: Path = Path("results/p2"),
          capital_path: Optional[Path] = CAPITAL) -> List[Path]:
    """Write ``fig_a1_{a,b,meta}.csv`` to ``results_dir`` and ``a1.pdf``/``a1.png`` (400 dpi) to ``out_dir``."""
    data = load(results_dir, capital_path=capital_path)
    paths = [kit.write_csv(df, results_dir, name) for name, df in tables(data).items()]
    return paths + kit.save(draw(data), SLOT, out_dir)


# ---------------------------------------------------------------------------------------------------- checks

def _fa(rd: Path) -> pd.DataFrame:
    return pd.read_csv(rd / "fig_a1_a.csv")


def _fb(rd: Path) -> pd.DataFrame:
    return pd.read_csv(rd / "fig_a1_b.csv")


def _fmeta(rd: Path) -> pd.Series:
    m = pd.read_csv(rd / "fig_a1_meta.csv", keep_default_na=False)
    return m.set_index("key")["value"]


def _src_v(rd: Path) -> pd.DataFrame:
    v = pd.read_csv(rd / VALIDATION)
    v["is_initial"] = _bool(v["is_initial"])
    return v


def _src_ok(rd: Path, kind: str) -> pd.DataFrame:
    v = _src_v(rd)
    return v[(v["status"] == "ok") & v["is_initial"] & (v["kind"] == kind)]


def _src_cell(rd: Path, kind: str, ccy: str, mgr: str, key: str) -> float:
    s = json.loads((rd / SUMMARY).read_text())
    hit = [c for c in s["cells"] if c["kind"] == kind and c["ccy"] == ccy and c["manager"] == mgr
           and bool(c["is_initial"])]
    return float(hit[0][key]) if len(hit) == 1 else float("nan")


def _fig_stat(ccy: str, mgr: str, item: str):
    def f(rd):
        a = _fa(rd)
        sel = a[(a["item"] == item) & (a["ccy"] == ccy) & (a["manager"] == mgr) & _bool(a["is_initial"])]
        return float(sel["value"].iloc[0]) if len(sel) == 1 else float("nan")
    return f


def _fig_zeros(ccy: Optional[str], mgr: Optional[str]):
    def f(rd):
        a = _fa(rd)
        sel = a[(a["item"] == "point") & _bool(a["drawn"]) & _bool(a["strip"])]
        if ccy is not None:
            sel = sel[(sel["ccy"] == ccy) & (sel["manager"] == mgr)]
        return float(len(sel))
    return f


def _src_zeros(ccy: Optional[str], mgr: Optional[str]):
    def f(rd):
        v = _src_ok(rd, "single")
        if ccy is not None:
            v = v[(v["ccy"] == ccy) & (v["manager"] == mgr)]
        return float((v["rel_err"].astype(float) == 0).sum())
    return f


def _fig_points(rd: Path, panel: str) -> pd.DataFrame:
    d = _fa(rd) if panel == "a" else _fb(rd)
    return d[(d["item"] == "point") & _bool(d["drawn"])]


def _fig_b_item(item: str):
    def f(rd):
        b = _fb(rd)
        return float(b.loc[b["item"] == item, "value"].iloc[0])
    return f


def _fig_threshold(k: str):
    def f(rd):
        a = _fa(rd)
        return float(a.loc[(a["item"] == "threshold") & (a["manager"] == k), "value"].iloc[0])
    return f


def _src_feed(rd: Path) -> float:
    path = str(_fmeta(rd)["capital_path"])
    fa = feed_age(Path(path) if path else None)
    return float(fa["holds"] is True)


def _src_spot_stale(rd: Path) -> float:
    path = str(_fmeta(rd)["capital_path"])
    return float(feed_age(Path(path) if path else None)["spot_stale_fills"])


def _largest_single_mgr(rd: Path) -> str:
    p = _fig_points(rd, "a")
    r = p.loc[p["rel_err"].astype(float).abs().idxmax()]
    return f"{r['ccy']} {r['manager']}"


def _src_largest_single_mgr(rd: Path) -> str:
    v = _src_ok(rd, "single")
    r = v.loc[v["rel_err"].astype(float).abs().idxmax()]
    return f"{r['ccy']} {r['manager']}"


N_EXPECTED = {cell: 100 for cell in ROWS}
N_EXPECTED[("HYPE", "pm2")] = 99
ZEROS_EXPECTED = {("BTC", "pm2"): 19, ("BTC", "sm"): 45, ("ETH", "pm2"): 15, ("ETH", "sm"): 53, ("HYPE", "sm"): 49,
                  ("BTC", "pm"): 0, ("ETH", "pm"): 0, ("HYPE", "pm2"): 0}

CHECKS: List[dict] = (
    [kit.check(f"a_n_{c}_{m}", f"a: n printed for {c} {kit.MANAGER_LABEL[m]}", _fig_stat(c, m, "n"),
               (lambda c=c, m=m: lambda rd: _src_cell(rd, "single", c, m, "n"))(), expected=N_EXPECTED[(c, m)])
     for c, m in ROWS]
    + [kit.check(f"a_zeros_{c}_{m}", f"a: exact zeros in the strip, {c} {kit.MANAGER_LABEL[m]}", _fig_zeros(c, m),
                 _src_zeros(c, m), expected=ZEROS_EXPECTED[(c, m)]) for c, m in ROWS]
    + [kit.check("a_zeros_total", "a: exact zeros in the strip, all rows", _fig_zeros(None, None),
                 _src_zeros(None, None), expected=181)]
    + [kit.check(f"a_{k}_{c}_{m}", f"a: {k} tick, {c} {kit.MANAGER_LABEL[m]}", _fig_stat(c, m, k),
                 (lambda c=c, m=m, key=key: lambda rd: _src_cell(rd, "single", c, m, key))(), rel=1e-9, abs_=1e-20)
       for c, m in ROWS for k, key in (("median", "median_rel"), ("p95", "p95_rel"))]
    + [kit.check("a_largest_median", "a: largest median over the rows (ETH legacy PM)",
                 lambda rd: float(_fa(rd).query("item == 'median'").loc[lambda d: _bool(d["is_initial"]), "value"].max()),
                 lambda rd: max(_src_cell(rd, "single", c, m, "median_rel") for c, m in ROWS),
                 expected=3.18e-9, expected_tol=0.005e-9),
       kit.check("a_largest_single", "a: largest single IM deviation drawn",
                 lambda rd: float(_fig_points(rd, "a")["rel_err"].astype(float).abs().max()),
                 lambda rd: float(_src_ok(rd, "single")["rel_err"].astype(float).abs().max()),
                 expected=8.88e-8, expected_tol=0.005e-8),
       kit.check("a_largest_single_cell", "a: the largest single IM deviation is ETH PM2", _largest_single_mgr,
                 _src_largest_single_mgr, expected="ETH pm2"),
       kit.check("a_threshold_median", "median bound (registered)", _fig_threshold("median"),
                 lambda rd: float(json.loads((rd / SUMMARY).read_text())["thresholds"]["median"]), expected=0.001),
       kit.check("a_threshold_p95", "p95 bound (registered)", _fig_threshold("p95"),
                 lambda rd: float(json.loads((rd / SUMMARY).read_text())["thresholds"]["p95"]), expected=0.01),
       kit.check("a_revert_cases", "reverting cases left out (caption)", lambda rd: float(_fmeta(rd)["revert_cases"]),
                 lambda rd: float(len(_src_v(rd).query("status == 'revert'")[["ccy", "manager", "kind", "block",
                                                                              "expiry", "strike", "is_call",
                                                                              "amount"]].astype(str)
                                      .drop_duplicates())), expected=1),
       kit.check("a_revert_rows", "reverting rows (IM and MM)", lambda rd: float(_fmeta(rd)["revert_rows"]),
                 lambda rd: float((_src_v(rd)["status"] == "revert").sum()), expected=2),
       kit.check("b_points", "b: IM book points drawn", lambda rd: float(len(_fig_points(rd, "b"))),
                 lambda rd: float(len(_src_ok(rd, "book"))), expected=77),
       kit.check("b_legs_min", "b: fewest legs", lambda rd: float(_fig_points(rd, "b")["n_legs"].min()),
                 lambda rd: float(_src_ok(rd, "book")["n_legs"].min()), expected=2),
       kit.check("b_legs_max", "b: most legs", lambda rd: float(_fig_points(rd, "b")["n_legs"].max()),
                 lambda rd: float(_src_ok(rd, "book")["n_legs"].max()), expected=245),
       kit.check("b_largest", "b: largest book IM deviation (ETH legacy PM)",
                 lambda rd: float(_fig_points(rd, "b")["rel_err"].astype(float).abs().max()),
                 lambda rd: max(_src_cell(rd, "book", c, m, "max_rel") for c, m in ROWS
                                if np.isfinite(_src_cell(rd, "book", c, m, "max_rel"))),
                 expected=3.45e-8, expected_tol=0.005e-8),
       kit.check("b_largest_miss", "b: largest miss, USDC (printed 0.05)", _fig_b_item("largest_miss_usdc"),
                 lambda rd: float(_src_ok(rd, "book")["abs_err"].abs().max()), expected=0.0503, expected_tol=5e-5),
       kit.check("b_K_max", "b: K up to, USDC (printed 19.5 M)", _fig_b_item("K_chain_max_usdc"),
                 lambda rd: float(_src_ok(rd, "book")["K_chain"].abs().max()), expected=19_494_690, expected_tol=0.5),
       kit.check("b_books", "b: books (book x underlying)", _fig_b_item("books"),
                 lambda rd: float(len(_src_ok(rd, "book")[["book", "ccy"]].drop_duplicates())), expected=26),
       kit.check("b_maker_days", "b: maker-days", _fig_b_item("maker_days"),
                 lambda rd: float(_src_ok(rd, "book")["book"].nunique()), expected=20)]
    + [kit.check(f"b_books_{c}", f"b: books of {c}", _fig_b_item(f"books_{c}"),
                 (lambda c=c: lambda rd: float(_src_ok(rd, "book").loc[lambda d: d["ccy"] == c, "book"].nunique()))(),
                 expected=e) for c, e in (("BTC", 7), ("ETH", 18), ("HYPE", 1))]
    + [kit.check("feed_age", "caption: no PM2-window fill uses a feed older than the validation limits",
                 lambda rd: float(str(_fmeta(rd)["feed_sentence_holds"]) == "True"), _src_feed, expected=1.0),
       kit.check("spot_stale", "caption: PM2-window fills with a spot price older than the spot heartbeat",
                 lambda rd: float(_fmeta(rd)["spot_stale_fills"]), _src_spot_stale)]
)


def run_checks(results_dir: Path = Path("results/p2"), with_expected: bool = True) -> pd.DataFrame:
    """Every check of :data:`CHECKS` (figure table against source file, and against the build instruction)."""
    return kit.run_checks(CHECKS, results_dir, with_expected=with_expected)


def main() -> None:  # pragma: no cover - command line
    paths = build()
    for p in paths:
        print("wrote", p)
    out = run_checks()
    print(out[["id", "figure", "source", "agrees", "expected", "matches_instruction", "error"]].to_string())


if __name__ == "__main__":  # pragma: no cover
    main()
