"""F5 of Paper 2: the engine over time (FIGURE_SELECTION section 7, F5; 7.0 x 5.15 in).

a  share of option open interest per manager at the start of each month (``manager_oi_share.csv`` samples
   00:00:01 UTC on the 1st), one strip per underlying (PM2 at the bottom).
b  five rails (BTC legacy PM, BTC PM2, ETH legacy PM, ETH PM2, HYPE PM2): every row of the parameter timeline as a
   grey tick, the registered H4 events in the status grammar of section 6.2 (filled = in the H4 panel, left half =
   kept without a panel cell, hollow = dropped by the dose rule), the effect of the parameters alone on the reference
   straddle in log-%, the +-14 day windows of the kept events and the admissible placebo days. Each rail has three
   lanes: the numbers stand above their symbols (numbers of close events pushed apart, ``label_offsets``; a leader
   line once a number no longer overhangs its symbol), the symbols, ticks and window bars sit on the rail, the placebo
   dashes 0.3 rows below it. A key in two rows under the title of b explains the marks (4.3 in tall before the
   revision of 29 September 2026, when the numbers stood beside the symbols and ran into each other).
c  capital of the BTC reference straddle per manager in per cent of the forward; the legacy line is thin in months
   where the legacy manager holds less than ``LEGACY_THICK_SHARE`` of BTC open interest (``legacy_thin_below``).

Inputs in ``results_dir``: ``manager_oi_share.csv``, ``params/{CCY}_{pm,pm2}.json``, ``events.csv``,
``reference_book.csv``, ``h4.json`` and, when the inference delivered it, ``h4_placebo_days.csv``. Tables:
``fig_f5_a.csv``, ``fig_f5_b.csv``, ``fig_f5_c.csv``.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from matplotlib import patheffects
from matplotlib.patches import Patch

from .. import p2events
from . import _kit_f5f6 as kit

NAME = "f5"
WIDTH, HEIGHT = 7.0, 5.15
DAY = 86_400
T0, T1 = pd.Timestamp("2024-01-01"), pd.Timestamp("2026-09-30")
RAILS: List[Tuple[str, str]] = [("BTC", "pm"), ("BTC", "pm2"), ("ETH", "pm"), ("ETH", "pm2"), ("HYPE", "pm2")]
CCYS = ("BTC", "ETH", "HYPE")
WINDOW_DAYS = p2events.WINDOW_DAYS
PM2_START_TS = p2events.PM2_START_TS
LEGACY_THICK_SHARE = 0.05     # legacy line thin (0.5 pt) in months where the legacy manager holds less of BTC OI
PANEL_A_TITLE = "share of option open interest at the start of each month"
PANEL_B_TITLE = "parameter changes · number = effect of the parameters alone on the reference straddle, log-%"
MAX_JUMP_LAG_DAYS = 1
REF_DAY = "2026-09-17"

# panel b: three lanes per rail, numbers above the rail, symbols on it, placebo days below it
PLACEBO_OFFSET = 0.30         # rows below the rail (instruction: 0.3 rows)
PLACEBO_LW = 1.5              # pt
LABEL_LIFT = 4.5              # pt from the rail to the lower edge of an event number
LABEL_GAP = 3.0               # pt at least between two numbers on one rail; closer numbers move apart
SHIFT_MIN = 0.5               # pt: a number moved less than this stands centred "above" its symbol
WINDOW_HALF = 0.17            # rows: half height of the grey +-14 day bars
TICK_HALF = 0.04              # in: half height of a grey timeline tick (0.08 in tall)
BRACKET_UP, BRACKET_DOWN = 0.40, 0.22   # rows above / below the rail of the "PM2 window" bracket
BRACKET_DAYS = 12             # length of the bracket's serifs
MARKER_PT = {"o": 4.6, "D": 4.0}

HALO = [patheffects.withStroke(linewidth=2.0, foreground="white")]   # numbers stay legible over grey ticks

# layout in inches
L, R = 0.95, 5.88
A_TOP, A_H, A_GAP = 0.25, 0.42, 0.05
B_TITLE, B_LEGEND = 1.68, 1.84       # top of the title and of the symbol legend of b
B_TOP, B_H = 2.15, 1.58
B_YLIM = (-0.62, 4.5)               # rows, top and bottom (rails at 0 .. 4)
C_TOP, C_H = B_TOP + B_H + 0.24, 0.90

CAPTION = (
    r"\textbf{The engine over time.} Panel a is the share of option open interest per manager and underlying at "
    r"the start of each month. Panel b marks every parameter change of the legacy manager and of PM2 as a grey "
    r"tick and the registered H4 events as symbols: filled when they enter the panel, half filled when kept without a cell of 20 "
    r"fills on each side, and hollow when dropped by the one per cent dose rule. The number is the change that the "
    r"parameters alone make to the capital of the reference straddle of the underlying, in log per cent. Grey bars "
    r"are the windows of 14 days on either side of each kept event; the windows of January and of May 2026 overlap, so "
    r"\PH{h4-dup-fills} fills enter two events. Black dashes below each line are the days from which placebo dates "
    r"may be drawn. Panel c is the capital of the BTC reference book, a short straddle struck at the forward on the "
    r"listed expiry nearest to 30 days, one contract per leg, in per cent of the forward; the small saw teeth come "
    r"from rolling between expiries of 21 and 36 days, and the legacy line is thin in months in which the legacy "
    r"manager held less than \PH{f5-legacy-thin} per cent of BTC open interest. Parameter changes of standard margin "
    r"left the reference book unchanged."
)


def rail_label(ccy: str, manager: str) -> str:
    return f"{ccy} {kit.MANAGER_LABEL[manager]}" if manager == "pm2" else f"{ccy} legacy PM"


def _x(ts) -> np.ndarray:
    """Matplotlib date numbers of unix seconds."""
    return mdates.date2num(pd.to_datetime(np.asarray(ts, dtype="int64"), unit="s"))


def _day_ts(day) -> np.ndarray:
    return (pd.to_datetime(pd.Series(day)).astype("int64") // 10 ** 9).to_numpy()


# =====================================================================================================================
# Tables
# =====================================================================================================================

def table_a(results_dir: Path) -> pd.DataFrame:
    oi = pd.read_csv(Path(results_dir) / "manager_oi_share.csv")
    out = oi[["month", "ccy", "sm", "pm", "pm2"]].copy()
    out[["sm", "pm", "pm2"]] = out[["sm", "pm", "pm2"]].astype(float).fillna(0.0)
    return out.sort_values(["ccy", "month"], kind="mergesort").reset_index(drop=True)


def pure_jump(rb: pd.DataFrame, ccy: str, manager: str, event_ts: int, event_day: str) -> Tuple[float, str]:
    """100 ln(K_m / K_m_prev) on the first reference day at or after the event whose parameter stamp differs from the
    day before (at most one day later); NaN when there is none."""
    sub = rb[(rb["ccy"] == ccy) & (rb["ts"] >= int(event_ts))].sort_values("ts", kind="mergesort")
    a, b = sub[f"{manager}_param_ts"], sub[f"{manager}_param_ts_prev"]
    sub = sub[a.notna() & b.notna() & (a != b)]
    if len(sub) == 0:
        return np.nan, ""
    r = sub.iloc[0]
    if (pd.Timestamp(r["day"]) - pd.Timestamp(event_day)).days > MAX_JUMP_LAG_DAYS:
        return np.nan, ""
    return float(100.0 * np.log(float(r[f"K_{manager}"]) / float(r[f"K_{manager}_prev"]))), str(r["day"])


def status(ev) -> str:
    if not bool(ev.kept):
        return "dropped"
    return "panel" if int(ev.panel_cells) > 0 else "kept_no_cell"


@lru_cache(maxsize=None)
def _text_width_pt(text: str) -> float:
    """Advance width of ``text`` at ``kit.FS_MIN`` in points (the layout width matplotlib gives the drawn text)."""
    if not text:
        return 0.0
    from matplotlib.backends.backend_agg import RendererAgg
    from matplotlib.font_manager import FontProperties

    w, _, _ = RendererAgg(72, 72, 72).get_text_width_height_descent(text, FontProperties(size=kit.FS_MIN), False)
    return float(w)


def _points_per_day() -> float:
    """Points per calendar day on the printed canvas (the canvas shrinks to the print width, the type does not)."""
    from ._print import print_width

    days = mdates.date2num(T1) - mdates.date2num(T0)
    return (R - L) * print_width(WIDTH) / WIDTH * 72.0 / days


def label_offsets(x_days, texts, gap: float = LABEL_GAP) -> np.ndarray:
    """Horizontal offsets in points of the event numbers of one rail (sorted by time), which stand centred above their
    symbols: numbers that would come closer than ``gap`` are pushed apart symmetrically, in time order, until none
    does (the earlier one of two close events to the left, the later one to the right)."""
    x = np.asarray(x_days, dtype=float) * _points_per_day()
    w = np.array([_text_width_pt(t) for t in texts], dtype=float)
    c = x.copy()
    for _ in range(500):
        moved = False
        for k in range(len(c) - 1):
            need = (w[k] + w[k + 1]) / 2.0 + gap - (c[k + 1] - c[k])
            if need > 1e-6:
                c[k] -= need / 2.0
                c[k + 1] += need / 2.0
                moved = True
        if not moved:
            break
    return c - x


def _label_sides(ev: pd.DataFrame) -> Dict[str, str]:
    """Where each event number (event rows of table b) stands: "above" its symbol, or above and moved "left" /
    "right" of it (with a leader line once it no longer overhangs the symbol)."""
    out = {}
    for _, g in ev.groupby(["ccy", "manager"], sort=False):
        g = g.sort_values("row_ts", kind="mergesort")
        dx = label_offsets(_x(g["row_ts"]), list(g["printed"].astype(str)))
        for eid, d in zip(g["event_id"], dx):
            out[eid] = "above" if abs(d) <= SHIFT_MIN else ("left" if d < 0 else "right")
    return out


def _placebo_days(results_dir: Path, h4: dict, events: pd.DataFrame) -> Tuple[Dict[Tuple[str, str], np.ndarray],
                                                                             Dict[Tuple[str, str], str]]:
    """Admissible placebo days per rail (union over its kept events) and the printed count per rail."""
    kept = events[events["kept"].astype(bool)]
    per_event = {k: int(v["days"]) for k, v in h4["placebo"]["admissible_days"].items()}
    path = Path(results_dir) / "h4_placebo_days.csv"
    table = pd.read_csv(path) if path.exists() else None
    days, printed = {}, {}
    for ccy, m in RAILS:
        ids = list(kept.loc[(kept["ccy"] == ccy) & (kept["manager"] == m), "event_id"])
        counts = sorted({per_event[e] for e in ids if e in per_event})
        if table is not None:
            t = table[table["timeline"].isin(ids) & table["admissible"].astype(bool)]
            days[(ccy, m)] = np.array(sorted(set(t["day"])), dtype=object)
        if counts:
            printed[(ccy, m)] = str(counts[0]) if len(counts) == 1 else f"{counts[0]} to {counts[-1]}"
    return days, printed


def table_b(results_dir: Path) -> pd.DataFrame:
    rd = Path(results_dir)
    events = pd.read_csv(rd / "events.csv")
    rb = pd.read_csv(rd / "reference_book.csv")
    h4 = json.loads((rd / "h4.json").read_text())
    pl_days, pl_printed = _placebo_days(rd, h4, events)
    rows = []
    for ccy, m in RAILS:
        rail = rail_label(ccy, m)
        n_pl = pl_printed.get((ccy, m), "")
        rows.append({"mark": "rail", "ccy": ccy, "manager": m, "rail": rail,
                     "placebo_days": pd.to_numeric(n_pl, errors="coerce"),
                     "printed": f"placebo days: {n_pl}" if n_pl else ""})
        evs = events[(events["ccy"] == ccy) & (events["manager"] == m)]
        tl = json.loads((rd / "params" / f"{ccy}_{m}.json").read_text())
        for r in tl:
            t = int(r["from_ts"])
            hit = evs[(evs["event_ts"] <= t) & (evs["last_ts"] >= t)]
            rows.append({"mark": "timeline_row", "ccy": ccy, "manager": m, "rail": rail, "row_ts": t,
                         "kinds": "+".join(r.get("changed") or []),
                         "event_id": hit["event_id"].iloc[0] if len(hit) else ""})
        for e in evs.itertuples():
            st = status(e)
            jump, jday = pure_jump(rb, ccy, m, int(e.event_ts), str(e.event_day))
            kept = st != "dropped"
            rows.append({"mark": "event", "ccy": ccy, "manager": m, "rail": rail, "row_ts": int(e.event_ts),
                         "kinds": e.kinds, "event_id": e.event_id, "status": st, "panel_cells": int(e.panel_cells),
                         "jump_logpct": jump, "jump_day": jday,
                         "window_lo": int(e.event_ts) - WINDOW_DAYS * DAY if kept else np.nan,
                         "window_hi": int(e.event_ts) + WINDOW_DAYS * DAY if kept else np.nan,
                         "label_side": "", "printed": kit.signed_int(jump)})
        for d in pl_days.get((ccy, m), []):
            rows.append({"mark": "placebo_day", "ccy": ccy, "manager": m, "rail": rail,
                         "row_ts": int(_day_ts([d])[0]), "placebo_days": pd.to_numeric(n_pl, errors="coerce")})
        if m == "pm2":
            rows.append({"mark": "window_start", "ccy": ccy, "manager": m, "rail": rail,
                         "row_ts": int(PM2_START_TS[ccy]), "printed": "PM2 window"})
    cols = ["mark", "ccy", "manager", "rail", "row_ts", "kinds", "event_id", "status", "panel_cells", "jump_logpct",
            "jump_day", "window_lo", "window_hi", "placebo_days", "label_side", "printed"]
    out = pd.DataFrame(rows, columns=cols)
    is_ev = out["mark"] == "event"
    out.loc[is_ev, "label_side"] = out.loc[is_ev, "event_id"].map(_label_sides(out[is_ev]))
    return out


def table_c(results_dir: Path) -> pd.DataFrame:
    rd = Path(results_dir)
    rb = pd.read_csv(rd / "reference_book.csv")
    oi = table_a(rd)
    out = rb[["ccy", "day", "ts", "tenor_days"]].copy()
    for m in ("sm", "pm", "pm2"):
        out[f"K_{m}_pct"] = 100.0 * rb[f"K_{m}"].astype(float) / rb["forward"].astype(float)
    start = {c: pd.Timestamp(int(PM2_START_TS[c]), unit="s").normalize() + pd.Timedelta(days=1) for c in CCYS}
    too_early = pd.to_datetime(out["day"]) < out["ccy"].map(start)
    out.loc[too_early, "K_pm2_pct"] = np.nan
    share = oi.set_index(["ccy", "month"])["pm"]
    month = pd.to_datetime(out["day"]).dt.strftime("%Y-%m")
    s = pd.Series([share.get((c, mo), np.nan) for c, mo in zip(out["ccy"], month)], index=out.index)
    out["legacy_thin"] = ~(s >= LEGACY_THICK_SHARE)
    out["legacy_thin_below"] = LEGACY_THICK_SHARE
    out["drawn"] = out["ccy"] == "BTC"
    out["printed"] = ""
    out = out.sort_values(["ccy", "day"], kind="mergesort").reset_index(drop=True)
    btc = out.index[out["ccy"] == "BTC"]
    if len(btc):
        last = out.loc[btc[-1]]
        out.loc[btc[-1], "printed"] = "; ".join(_end_labels(last))
    return out


def _end_labels(last) -> List[str]:
    return [f"{kit.MANAGER_LABEL[m]} {kit.pct(float(last[f'K_{m}_pct']))}" for m in ("sm", "pm", "pm2")
            if np.isfinite(float(last[f"K_{m}_pct"]))]


# =====================================================================================================================
# Figure
# =====================================================================================================================

def _calendar(ax, labels: bool) -> None:
    ax.set_xlim(mdates.date2num(T0), mdates.date2num(T1))
    ticks = pd.date_range(T0, T1, freq="QS")
    ax.set_xticks(mdates.date2num(ticks))
    ax.set_xticklabels([t.strftime("%Y-%m") for t in ticks] if labels else [])
    ax.tick_params(axis="x", length=2.5)


def _panel_a(fig, a: pd.DataFrame) -> None:
    kit.letter(fig, 0.02, 0.03, "a")
    kit.fig_text(fig, L, 0.04, PANEL_A_TITLE, ha="left")
    sty = {"pm2": dict(facecolor=kit.MANAGER["pm2"][0], edgecolor="none"),
           "pm": dict(facecolor=kit.MANAGER["pm"][0], alpha=0.35, edgecolor="none"),
           "sm": dict(facecolor="white", edgecolor=kit.MANAGER["sm"][0], hatch="////", linewidth=0.4)}
    axes = []
    for i, ccy in enumerate(CCYS):
        ax = kit.axes_at(fig, L, A_TOP + i * (A_H + A_GAP), R - L, A_H)
        axes.append(ax)
        s = a[a["ccy"] == ccy].sort_values("month")
        if len(s):
            starts = pd.to_datetime(s["month"])
            edges = mdates.date2num(list(starts) + [starts.iloc[-1] + pd.offsets.MonthBegin(1)])
            pm2, pm, sm = (s[c].to_numpy(float) for c in ("pm2", "pm", "sm"))
            ax.stairs(pm2, edges, baseline=0.0, fill=True, **sty["pm2"])
            ax.stairs(pm2 + pm, edges, baseline=pm2, fill=True, **sty["pm"])
            ax.stairs(pm2 + pm + sm, edges, baseline=pm2 + pm, fill=True, **sty["sm"])
        _calendar(ax, labels=False)
        ax.set_ylim(0, 1)
        ax.set_yticks([0, 1])
        lo, hi = ax.set_yticklabels(["0", "1"])
        lo.set_va("bottom")                             # keep both labels inside the strip: no clash between strips
        hi.set_va("top")
        kit.fig_text(fig, L - 0.36, A_TOP + i * (A_H + A_GAP) + A_H / 2, ccy, fontsize=kit.FS_LETTER,
                     fontweight="bold", ha="right", va="center")
    axes[1].set_ylabel("share of option OI", labelpad=3)
    handles = [Patch(label="PM2", **sty["pm2"]), Patch(label="legacy PM", **sty["pm"]),
               Patch(label="SM", **sty["sm"])]
    axes[0].legend(handles=handles, loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3, frameon=False,
                   handlelength=1.6, handleheight=0.8, columnspacing=1.2, borderaxespad=0.1, borderpad=0.1)


def _marker_kw(manager: str, st: str) -> dict:
    """Event symbol in the status grammar of section 6.2: shape and colour = manager, fill = status."""
    color, _, marker = kit.MANAGER[manager]
    fill = {"panel": "full", "kept_no_cell": "left", "dropped": "none"}[st]
    return dict(linestyle="none", marker=marker, markersize=MARKER_PT[marker], markeredgecolor=color,
                markerfacecolor=color if fill != "none" else "white", markerfacecoloralt="white",
                fillstyle=fill if fill != "none" else "full", markeredgewidth=0.9)


def _legend_b(fig) -> None:
    """Key of the marks of b in two rows under its title: the three fills of the event symbols (each shown for the
    legacy PM diamond and the PM2 circle), then tick, window bar and placebo dash."""
    from matplotlib.legend_handler import HandlerTuple
    from matplotlib.lines import Line2D

    def pair(st):
        return tuple(Line2D([], [], **_marker_kw(m, st)) for m in ("pm", "pm2"))

    handles = [pair("panel"), pair("kept_no_cell"), pair("dropped"),
               Line2D([], [], linestyle="none", marker="|", markersize=2 * TICK_HALF * 72, markeredgewidth=0.6,
                      color="#999999"),
               Patch(facecolor="black", alpha=0.12, edgecolor="none"),
               Line2D([], [], color="black", linewidth=PLACEBO_LW, solid_capstyle="butt")]
    labels = ["in the H4 panel", "kept, no cell", "dropped (dose rule)", "parameter change", "±14 day window",
              "placebo days"]
    order = [0, 3, 1, 4, 2, 5]                      # filled by column: symbols in the first row, marks in the second
    W, H = fig.get_size_inches()
    fig.legend([handles[k] for k in order], [labels[k] for k in order], loc="upper left",
               bbox_to_anchor=(L / W, 1.0 - B_LEGEND / H), ncol=3, frameon=False,
               handler_map={tuple: HandlerTuple(ndivide=None, pad=0.15)}, handlelength=1.5, handleheight=0.8,
               handletextpad=0.4, columnspacing=1.6, labelspacing=0.35, borderaxespad=0.0, borderpad=0.0)


def _panel_b(fig, b: pd.DataFrame) -> None:
    kit.letter(fig, 0.02, B_TITLE - 0.01, "b")
    kit.fig_text(fig, L, B_TITLE, PANEL_B_TITLE, ha="left")
    _legend_b(fig)
    ax = kit.axes_at(fig, L, B_TOP, R - L, B_H)
    ax.spines["left"].set_visible(False)
    n = len(RAILS)
    row_in = B_H / (B_YLIM[1] - B_YLIM[0])
    tick_half = TICK_HALF / row_in
    for i, (ccy, m) in enumerate(RAILS):
        rail = rail_label(ccy, m)
        rb = b[b["rail"] == rail]
        ev = rb[rb["mark"] == "event"].sort_values("row_ts", kind="mergesort")
        for e in ev[ev["status"] != "dropped"].itertuples():
            ax.fill_between(_x([e.window_lo, e.window_hi]), i - WINDOW_HALF, i + WINDOW_HALF, color="black",
                            alpha=0.12, linewidth=0, zorder=1)
        tl = rb[rb["mark"] == "timeline_row"]
        ax.vlines(_x(tl["row_ts"]), i - tick_half, i + tick_half, color="#999999", linewidth=0.6, zorder=2)
        pl = rb[rb["mark"] == "placebo_day"]
        if len(pl):
            x0 = _x(pl["row_ts"])
            ax.hlines(np.full(len(x0), i + PLACEBO_OFFSET), x0, x0 + 1.0, color="black", linewidth=PLACEBO_LW,
                      capstyle="butt", zorder=2)
        xs = _x(ev["row_ts"])
        dx = label_offsets(xs, list(ev["printed"].astype(str))) if len(ev) else []
        for e, x, d in zip(ev.itertuples(), xs, dx):
            ax.plot([x], [i], zorder=4, **_marker_kw(m, e.status))
            _, _, marker = kit.MANAGER[m]
            if abs(d) > _text_width_pt(str(e.printed)) / 2.0 + MARKER_PT[marker] / 2.0:   # no longer over it
                # leader line as an annotation without text, so that the number's box stays the text alone
                ax.annotate("", (x, i), xytext=(d, LABEL_LIFT), textcoords="offset points", zorder=4.5,
                            arrowprops=dict(arrowstyle="-", color="black", linewidth=0.5, shrinkA=0.8,
                                            shrinkB=MARKER_PT[marker] / 2 + 0.6))
            ax.annotate(e.printed, (x, i), xytext=(d, LABEL_LIFT), textcoords="offset points", ha="center",
                        va="bottom", fontsize=kit.FS_MIN, zorder=5, path_effects=HALO)
        for w in rb[rb["mark"] == "window_start"].itertuples():
            x = _x([w.row_ts])[0]
            top, bot = i - BRACKET_UP, i + BRACKET_DOWN
            ax.plot([x + BRACKET_DAYS, x, x, x + BRACKET_DAYS], [top, top, bot, bot], color="black", linewidth=0.8,
                    zorder=3, solid_joinstyle="miter")
            ax.annotate(w.printed, (x, top), xytext=(-2.5, 0), textcoords="offset points", ha="right", va="center",
                        fontsize=kit.FS_MIN, path_effects=HALO, zorder=5)
        head = rb[rb["mark"] == "rail"]
        if len(head) and head["printed"].iloc[0]:
            ax.annotate(head["printed"].iloc[0], (1.0, i), xycoords=("axes fraction", "data"),
                        xytext=(12, 0), textcoords="offset points", ha="left", va="center", fontsize=kit.FS_MIN)
    ax.set_ylim(B_YLIM[1], B_YLIM[0])
    ax.set_yticks(range(n))
    ax.set_yticklabels([rail_label(c, m) for c, m in RAILS])
    ax.tick_params(axis="y", length=0, pad=4)
    _calendar(ax, labels=False)


def _panel_c(fig, c: pd.DataFrame, b: pd.DataFrame) -> None:
    kit.letter(fig, 0.02, C_TOP - 0.21, "c")
    kit.fig_text(fig, L, C_TOP - 0.20, "BTC reference book: short straddle at the forward, listed expiry nearest "
                 "30 days, one contract per leg", ha="left")
    ax = kit.axes_at(fig, L, C_TOP, R - L, C_H)
    s = c[c["drawn"]].sort_values("day")
    x = mdates.date2num(pd.to_datetime(s["day"]) + pd.Timedelta(hours=8))
    ev = b[(b["mark"] == "event") & (b["ccy"] == "BTC") & (b["status"] != "dropped")]
    for t in _x(ev["row_ts"]):
        ax.axvline(t, color="#999999", linewidth=0.4, zorder=1)
    for m in ("sm", "pm2"):
        color, ls, _ = kit.MANAGER[m]
        ax.plot(x, s[f"K_{m}_pct"], color=color, linestyle=ls, linewidth=1.2, zorder=3)
    color, ls, _ = kit.MANAGER["pm"]
    y = s["K_pm_pct"].to_numpy(float)
    thin = s["legacy_thin"].to_numpy(bool)
    thick_y = np.where(~thin, y, np.nan)
    thin_y = np.where(thin, y, np.nan)
    # join the runs: the first point of each run also ends the previous one
    change = np.flatnonzero(thin[1:] != thin[:-1]) + 1
    for k in change:
        thick_y[k] = y[k] if thin[k] else thick_y[k]
        thin_y[k - 1] = y[k - 1] if not thin[k - 1] else thin_y[k - 1]
    ax.plot(x, thick_y, color=color, linestyle=ls, linewidth=1.2, zorder=2)
    ax.plot(x, thin_y, color=color, linestyle=ls, linewidth=0.5, zorder=2)
    ax.set_ylim(0, 32)
    ax.set_yticks([0, 10, 20, 30])
    ax.grid(axis="y", color="#CCCCCC", linewidth=0.4)
    ax.set_axisbelow(True)
    ax.set_ylabel("% of forward")
    _calendar(ax, labels=True)
    last = s.iloc[-1]
    for m, text in zip(("sm", "pm", "pm2"), _end_labels(last)):
        ax.annotate(text, (1.0, float(last[f"K_{m}_pct"])), xycoords=("axes fraction", "data"), xytext=(6, 0),
                    textcoords="offset points", ha="left", va="center", fontsize=kit.FS_MIN,
                    color=kit.MANAGER[m][0])


def figure(results_dir: Path = Path("results/p2")):
    """The figure (not saved) from the inputs in ``results_dir``."""
    rd = Path(results_dir)
    a, b, c = table_a(rd), table_b(rd), table_c(rd)
    fig = kit.new_figure(WIDTH, HEIGHT)
    _panel_a(fig, a)
    _panel_b(fig, b)
    _panel_c(fig, c, b)
    return fig


def build(out_dir: Path = Path("paper2/figures"), results_dir: Path = Path("results/p2")) -> List[Path]:
    """Write ``fig_f5_{a,b,c}.csv`` to ``results_dir`` and ``f5.pdf``/``f5.png`` to ``out_dir``."""
    rd = Path(results_dir)
    paths = [kit.write_csv(table_a(rd), rd, "fig_f5_a.csv"), kit.write_csv(table_b(rd), rd, "fig_f5_b.csv"),
             kit.write_csv(table_c(rd), rd, "fig_f5_c.csv")]
    fig = figure(rd)
    return paths + kit.save(fig, NAME, Path(out_dir))


# =====================================================================================================================
# Checks: what the figure prints (fig_f5_*.csv) against the sources in results_dir
# =====================================================================================================================

def _fb(rd: Path) -> pd.DataFrame:
    return pd.read_csv(rd / "fig_f5_b.csv")


def _fig_events(rd: Path) -> pd.DataFrame:
    b = _fb(rd)
    return b[b["mark"] == "event"].set_index("event_id")


def _src_events(rd: Path) -> pd.DataFrame:
    return pd.read_csv(rd / "events.csv").set_index("event_id")


def _src_status(rd: Path) -> Dict[str, str]:
    ev = _src_events(rd)
    return {k: ("dropped" if not bool(r["kept"]) else ("panel" if int(r["panel_cells"]) > 0 else "kept_no_cell"))
            for k, r in ev.iterrows()}


def _src_jumps(rd: Path) -> Dict[str, float]:
    """Independent reading of reference_book.csv: the reference day on or up to one day after the event day at 08:00
    UTC on which the manager's parameter stamp changed."""
    rb = pd.read_csv(rd / "reference_book.csv")
    out = {}
    for eid, e in _src_events(rd).iterrows():
        m = e["manager"]
        s = rb[(rb["ccy"] == e["ccy"]) & (rb["day"] >= e["event_day"])].sort_values("day").head(2)
        s = s[(s["ts"] >= e["event_ts"]) & (s[f"{m}_param_ts"] != s[f"{m}_param_ts_prev"])
              & s[f"{m}_param_ts"].notna()]
        out[eid] = float(100 * np.log(s[f"K_{m}"].iloc[0] / s[f"K_{m}_prev"].iloc[0])) if len(s) else np.nan
    return out


def _src_ref(rd: Path, ccy: str) -> List[float]:
    rb = pd.read_csv(rd / "reference_book.csv")
    r = rb[(rb["ccy"] == ccy)].sort_values("day").iloc[-1]
    return [100 * float(r[f"K_{m}"]) / float(r["forward"]) for m in ("sm", "pm", "pm2")]


def _fig_ref(rd: Path, ccy: str) -> List[float]:
    c = pd.read_csv(rd / "fig_f5_c.csv")
    r = c[c["ccy"] == ccy].sort_values("day").iloc[-1]
    return [float(r[f"K_{m}_pct"]) for m in ("sm", "pm", "pm2")]


def _src_rail_days(rd: Path) -> Dict[str, int]:
    h4 = json.loads((rd / "h4.json").read_text())["placebo"]["admissible_days"]
    ev = _src_events(rd)
    out = {}
    for ccy, m in RAILS:
        ids = [k for k, r in ev.iterrows() if r["ccy"] == ccy and r["manager"] == m and bool(r["kept"])]
        vals = {int(h4[k]["days"]) for k in ids if k in h4}
        if len(vals) == 1:
            out[rail_label(ccy, m)] = vals.pop()
    return out


def _fig_rail_days(rd: Path) -> Dict[str, int]:
    b = _fb(rd)
    r = b[(b["mark"] == "rail") & b["placebo_days"].notna()]
    return {k: int(v) for k, v in zip(r["rail"], r["placebo_days"])}


def _src_last_month_pm2(rd: Path) -> Dict[str, float]:
    oi = pd.read_csv(rd / "manager_oi_share.csv")
    last = oi.sort_values("month").groupby("ccy").tail(1)
    return {c: float(v) for c, v in zip(last["ccy"], last["pm2"])}


def _fig_last_month_pm2(rd: Path) -> Dict[str, float]:
    a = pd.read_csv(rd / "fig_f5_a.csv")
    last = a.sort_values("month").groupby("ccy").tail(1)
    return {c: float(v) for c, v in zip(last["ccy"], last["pm2"])}


EXPECTED_JUMPS = {
    "BTC-pm-20240612": 0.0, "ETH-pm-20240612": 0.0, "BTC-pm2-20251010": 0.0, "ETH-pm2-20251010": 0.0,
    "BTC-pm-20250222": -18.56, "ETH-pm-20250222": -18.89,
    "BTC-pm2-20260108": 1.60, "BTC-pm2-20260123": -10.49, "BTC-pm2-20260524": -7.84, "BTC-pm2-20260820": -26.05,
    "ETH-pm2-20260108": 1.61, "ETH-pm2-20260123": -4.88, "ETH-pm2-20260524": -3.36, "ETH-pm2-20260820": -18.28,
    "HYPE-pm2-20260108": 1.54, "HYPE-pm2-20260508": -7.43, "HYPE-pm2-20260524": -37.43, "HYPE-pm2-20260820": -20.33,
}

CHECKS = [
    kit.check("f5.b.events", "event symbols in b = rows of events.csv",
              lambda rd: len(_fig_events(rd)), lambda rd: len(_src_events(rd)), expected=18),
    kit.check("f5.b.status_counts", "filled / half filled / hollow symbols",
              lambda rd: _fig_events(rd)["status"].value_counts().to_dict(),
              lambda rd: pd.Series(_src_status(rd)).value_counts().to_dict(),
              expected={"panel": 13, "kept_no_cell": 1, "dropped": 4}),
    kit.check("f5.b.status_ids", "filled symbols are exactly kept & panel_cells > 0 (events.csv)",
              lambda rd: _fig_events(rd)["status"].sort_index().to_dict(),
              lambda rd: dict(sorted(_src_status(rd).items()))),
    kit.check("f5.b.panel_cells", "panel cells of the filled events = h4.json cell_events",
              lambda rd: int(_fig_events(rd).query("status == 'panel'")["panel_cells"].sum()),
              lambda rd: int(json.loads((rd / "h4.json").read_text())["cell_events"]), expected=475),
    kit.check("f5.b.jumps", "effect of the parameters alone, log-% (reference_book.csv)",
              lambda rd: _fig_events(rd)["jump_logpct"].to_dict(), _src_jumps, rel=1e-9, abs_=1e-9,
              expected=EXPECTED_JUMPS, expected_tol=0.005),
    kit.check("f5.b.printed_jumps", "printed numbers = signed whole log-% of reference_book.csv",
              lambda rd: _fig_events(rd)["printed"].astype(str).to_dict(),
              lambda rd: {k: kit.signed_int(v) for k, v in _src_jumps(rd).items()}),
    kit.check("f5.b.windows", "+-14 day windows of the kept events (events.csv)",
              lambda rd: {k: [r["window_lo"], r["window_hi"]] for k, r in _fig_events(rd).iterrows()
                          if r["status"] != "dropped"},
              lambda rd: {k: [r["event_ts"] - WINDOW_DAYS * DAY, r["event_ts"] + WINDOW_DAYS * DAY]
                          for k, r in _src_events(rd).iterrows() if bool(r["kept"])}),
    kit.check("f5.b.timeline_rows", "grey ticks per rail = rows of params/{CCY}_{m}.json",
              lambda rd: _fb(rd).query("mark == 'timeline_row'").groupby("rail").size().to_dict(),
              lambda rd: {rail_label(c, m): len(json.loads((rd / "params" / f"{c}_{m}.json").read_text()))
                          for c, m in RAILS}),
    kit.check("f5.b.placebo_days", "placebo days per rail (h4.json placebo.admissible_days)",
              _fig_rail_days, _src_rail_days,
              expected={"BTC legacy PM": 363, "BTC PM2": 54, "ETH legacy PM": 319, "ETH PM2": 10, "HYPE PM2": 67}),
    kit.check("f5.a.shares", "stacked shares = manager_oi_share.csv after fillna(0)",
              lambda rd: pd.read_csv(rd / "fig_f5_a.csv").sort_values(["ccy", "month"])[["sm", "pm", "pm2"]]
              .to_numpy().ravel().tolist(),
              lambda rd: pd.read_csv(rd / "manager_oi_share.csv").sort_values(["ccy", "month"])[["sm", "pm", "pm2"]]
              .fillna(0.0).to_numpy().ravel().tolist()),
    kit.check("f5.a.pm2_last_month", "PM2 share of option OI in the last month (September 2026)",
              _fig_last_month_pm2, _src_last_month_pm2,
              expected={"BTC": 0.9096, "ETH": 0.7189, "HYPE": 0.8792}, expected_tol=5e-5),
    kit.check("f5.c.btc_last", "BTC reference straddle on the last day, % of forward (SM, legacy PM, PM2)",
              lambda rd: _fig_ref(rd, "BTC"), lambda rd: _src_ref(rd, "BTC"), expected=[29.61, 19.68, 10.03],
              expected_tol=0.005),
    kit.check("f5.c.eth_last", "ETH reference straddle on the last day (CSV only)",
              lambda rd: _fig_ref(rd, "ETH"), lambda rd: _src_ref(rd, "ETH"), expected=[29.71, 19.41, 10.94],
              expected_tol=0.005),
    kit.check("f5.c.hype_last", "HYPE reference straddle on the last day (CSV only)",
              lambda rd: _fig_ref(rd, "HYPE"), lambda rd: _src_ref(rd, "HYPE"),
              expected=[59.36, float("nan"), 20.19], expected_tol=0.005),
    kit.check("f5.c.last_day", "direct labels are the values of 17 Sep 2026",
              lambda rd: pd.read_csv(rd / "fig_f5_c.csv").query("ccy == 'BTC'")["day"].max(),
              lambda rd: pd.read_csv(rd / "reference_book.csv").query("ccy == 'BTC'")["day"].max(), expected=REF_DAY),
    kit.check("f5.c.printed", "printed direct labels",
              lambda rd: pd.read_csv(rd / "fig_f5_c.csv", keep_default_na=False).query("printed != ''")["printed"]
              .tolist(),
              lambda rd: ["; ".join(f"{kit.MANAGER_LABEL[m]} {kit.pct(v)}" for m, v in
                                    zip(("sm", "pm", "pm2"), _src_ref(rd, "BTC")) if np.isfinite(v))]),
]
