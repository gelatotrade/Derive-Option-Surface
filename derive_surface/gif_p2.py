"""GIF of the BTC PM2 capital surface over the PM2 window (``docs/paper2/ABBILDUNGSWAHL.md``, section 8).

One frame per week (Wednesday 08:00 UTC, plus the first PM2 day and the T1 block 17 Sep 2026 08:00 UTC as the last
frame) or per day; for every kept BTC PM2 event three extra day frames: the last 08:00 block before the event, the
first after it (held 1.5 s under a banner) and the day after. Each frame shows

* the chain surface of the day in 3D as in Figure T1 a (height = implied vol, colour = PM2 capital of one short
  contract in % of the forward on one fixed scale for all frames that covers every node, iso-capital lines
  at 8 and 12 %);
* in the corner the SM capital of the same ATM 30 d short from the SM grid of the same frame;
* a time strip with the BTC reference straddle per manager (colour and line style as F5 c), a cursor, and the kept
  BTC PM2 events as vertical lines with the step of the straddle in simple per cent.

Honesty: expiries without a fresh feed (older than ``p2surface.LIVE_MAX_AGE``) are left out and counted on a plaque,
tenors outside the live expiries are drawn as a grey floor instead of being extrapolated, a week without a live expiry
is skipped and recorded, every frame shows date, time and block.

Heavy (feed history with SVI, loaded per quarter): run through ``scripts/p2_heavy.py``::

    python3 scripts/p2_heavy.py --wait-max 500 -- python3 -m derive_surface p2 figures gif [--step daily]

Writes ``docs/media/p2_btc_capital_surface.gif`` (at most 8 MB), ``..._end.png`` (the last frame, poster),
``docs/media/p2_btc_capital_surface.mp4`` (``animate.write_mp4``, needs ``imageio-ffmpeg`` of requirements.txt),
``results/p2/gif_frames.csv`` and ``results/p2/gif_meta.json``. The file names differ from section 8
(``BTC_p2_capital_pm2.*``): every Paper 2 medium in ``docs/media`` starts with ``p2_``.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import textwrap
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import patheffects  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402

from . import p2surface  # noqa: E402
from .p2chain import block_at_ts  # noqa: E402

log = logging.getLogger(__name__)

CCY = "BTC"
MANAGER = "pm2"
START, END = "2025-06-13", "2026-09-17"
HOUR = p2surface.REF_HOUR
DAY = 86_400
WEEKDAY = 2                               # Wednesday
OUT = Path("docs/media/p2_btc_capital_surface.gif")
RESULTS = Path("results/p2")
FRAMES_CSV = "gif_frames.csv"
META_JSON = "gif_meta.json"
MAX_BYTES = 8 * 1024 * 1024

WIDTH, HEIGHT, DPI = 1200, 675, 100
FPS = 4.0
HOLD = 6                                   # frames the first frame after an event is held (1.5 s at 4 fps)
END_HOLD = 8
ISO = (8.0, 12.0)
YTOP = 34.0                                # top of the time strip, % of forward
ATM_DELTA, ATM_DAYS = 0.5, 30.44

# type in points at 100 dpi: 16 pt = 22 px (axes and ticks), 24 pt = 33 px (banner and date)
FS_TICK, FS_LABEL, FS_TITLE, FS_DATE, FS_BANNER = 16.0, 16.0, 20.0, 24.0, 24.0
INK = "#111111"
GREY = "#666666"
MANAGER_STYLE = {"pm2": ("#0072B2", "-"), "sm": ("#D55E00", "--"), "pm": ("#009E73", ":")}
MANAGER_NAME = {"pm2": "PM2", "sm": "SM", "pm": "legacy PM"}
MINUS = "−"
STROKE = [patheffects.withStroke(linewidth=3.0, foreground="white")]
KIND_WORDS = {"MarginParameters": "margin parameters", "VolShockParameters": "vol shocks",
              "BasisContingencyParameters": "contingencies", "OtherContingencyParameters": "contingencies",
              "SkewShockParameters": "skew shocks", "scenarios": "scenarios", "CollateralParameters": "collateral"}


# ---------------------------------------------------------------------------------------------------- plan

def _day(ts: int) -> str:
    return dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).strftime("%Y-%m-%d")


def kept_events(events: pd.DataFrame, ccy: str = CCY, manager: str = MANAGER) -> pd.DataFrame:
    """Kept events of ``ccy``/``manager`` from ``events.csv``, by time."""
    e = events[(events["ccy"] == ccy) & (events["manager"] == manager)]
    e = e[e["kept"].astype(str).str.lower().isin(["true", "1"])]
    return e.sort_values("event_ts", kind="mergesort").reset_index(drop=True)


def frame_plan(events: pd.DataFrame, start: str = START, end: str = END, step: str = "weekly",
               hour: int = HOUR) -> pd.DataFrame:
    """Frames in time order: ``ts, day, kind, event_id, hold``.

    ``kind`` is ``first``, ``regular``, ``last`` or ``before``/``after``/``next`` around a kept event; ``hold`` is the
    number of frame slots a frame stays on screen (``HOLD`` for the frame after an event, ``END_HOLD`` for the last).
    """
    t0, t1 = p2surface._day_ts(start, hour), p2surface._day_ts(end, hour)
    rows = [{"ts": t0, "kind": "first", "event_id": ""}]
    days = pd.date_range(pd.Timestamp(start) + pd.Timedelta(days=1), pd.Timestamp(end) - pd.Timedelta(days=1),
                         freq="D")
    for d in days:
        if step == "daily" or (step == "weekly" and d.weekday() == WEEKDAY):
            rows.append({"ts": p2surface._day_ts(d, hour), "kind": "regular", "event_id": ""})
    if step not in ("daily", "weekly"):
        raise ValueError(f"step must be weekly or daily, not {step!r}")
    rows.append({"ts": t1, "kind": "last", "event_id": ""})
    for ev in events.itertuples():
        e_ts = int(ev.event_ts)
        if not t0 < e_ts < t1:
            continue
        same = p2surface._day_ts(_day(e_ts), hour)
        before = same if same < e_ts else same - DAY
        after = before + DAY
        for ts, kind in ((before, "before"), (after, "after"), (after + DAY, "next")):
            if t0 <= ts <= t1:
                rows.append({"ts": ts, "kind": kind, "event_id": str(ev.event_id)})
    plan = pd.DataFrame(rows)
    rank = {"after": 0, "before": 1, "next": 2, "last": 3, "first": 4, "regular": 5}
    plan["_r"] = plan["kind"].map(rank)
    plan = plan.sort_values(["ts", "_r"], kind="mergesort").drop_duplicates("ts", keep="first")
    plan = plan.drop(columns="_r").reset_index(drop=True)
    plan["day"] = [_day(t) for t in plan["ts"]]
    plan["hold"] = np.where(plan["kind"] == "after", HOLD, np.where(plan["kind"] == "last", END_HOLD, 1))
    return plan[["ts", "day", "kind", "event_id", "hold"]]


# ---------------------------------------------------------------------------------------------------- banner

def step_pct(logpct: float) -> float:
    """Simple per cent of a change given in log-% (100 ln K1/K0)."""
    return 100.0 * (np.exp(float(logpct) / 100.0) - 1.0)


def fmt_step(pct: float) -> str:
    """Two significant digits with sign and a true minus: +1.6 %, −10 %, −7.5 %, −23 %."""
    if not np.isfinite(pct):
        return "n/a"
    a = abs(pct)
    s = f"{a:.0f}" if a >= 9.95 else f"{a:.1f}"
    return f"{'+' if pct >= 0 else MINUS}{s} %"


def event_words(kinds: str, widths: Optional[Tuple[float, float]] = None) -> str:
    """What changed, in words, from the ``kinds`` of ``events.csv``; ``widths`` = half width of the core spot grid
    before and after (fractions) when it changed. A change of the scenarios alone that keeps the grid reads "scenario
    weights"; three or more kinds read "parameter bundle"."""
    parts = [k for k in str(kinds).split("+") if k]
    words: List[str] = []
    for k in parts:
        w = KIND_WORDS.get(k, k)
        if w not in words:
            words.append(w)
    if parts == ["scenarios"] and widths is None:
        words = ["scenario weights"]
    text = "parameter bundle" if len(words) >= 3 else ", ".join(words)
    if widths is not None:
        a, b = (int(round(100 * x)) for x in widths)
        text += f"{' incl.' if len(words) >= 3 else ','} spot grid ±{a} % → ±{b} %"
    return text


def grid_widths(ccy: str, event_ts: int, manager: str = MANAGER) -> Optional[Tuple[float, float]]:
    """Half width of the PM2 core spot grid just before and after ``event_ts`` when it changed, else None."""
    from . import margin_pm2
    from .figs_p2 import t1
    from .p2params import Timeline

    tl = Timeline(ccy, manager)
    try:
        a = t1.grid_width(margin_pm2._Params(tl.at(int(event_ts) - 1)))[0]
        b = t1.grid_width(margin_pm2._Params(tl.at(int(event_ts) + 1)))[0]
    except Exception:  # noqa: BLE001 - no timeline: no grid words
        return None
    return None if abs(a - b) < 1e-9 else (a, b)


def banners(events: pd.DataFrame, rb: pd.DataFrame, widths: Callable[[int], Optional[tuple]] = lambda ts: None,
            ccy: str = CCY, manager: str = MANAGER) -> pd.DataFrame:
    """Per kept event: ``event_id, event_ts, jump_logpct, step_pct, printed_step, banner``.

    The step is the change the parameters alone make to the reference straddle (``reference_book.csv``, first day
    whose parameter stamp differs from the day before, at most one day after the event; as in F5 b)."""
    from .figs_p2.f5 import pure_jump

    rows = []
    for ev in events.itertuples():
        jump, _ = pure_jump(rb, ccy, manager, int(ev.event_ts), str(ev.event_day))
        pct = step_pct(jump) if np.isfinite(jump) else np.nan
        date = pd.Timestamp(int(ev.event_ts), unit="s").strftime("%-d %b %Y")
        text = f"{date} · {event_words(ev.kinds, widths(int(ev.event_ts)))} · straddle {fmt_step(pct)}"
        rows.append({"event_id": ev.event_id, "event_ts": int(ev.event_ts), "jump_logpct": jump, "step_pct": pct,
                     "printed_step": fmt_step(pct), "banner": text})
    return pd.DataFrame(rows, columns=["event_id", "event_ts", "jump_logpct", "step_pct", "printed_step", "banner"])


def reference_series(rb: pd.DataFrame, ccy: str = CCY, start: str = START, end: str = END,
                     pad_days: int = 10) -> pd.DataFrame:
    """Reference straddle per manager in % of the forward, ``ts`` plus one column per manager."""
    r = rb[rb["ccy"] == ccy].sort_values("ts", kind="mergesort")
    lo = p2surface._day_ts(start) - pad_days * DAY
    hi = p2surface._day_ts(end) + pad_days * DAY
    r = r[(r["ts"] >= lo) & (r["ts"] <= hi)]
    out = pd.DataFrame({"ts": r["ts"].to_numpy(int)})
    for m in ("sm", "pm", "pm2"):
        out[m] = (100.0 * r[f"K_{m}"] / r["forward"]).to_numpy(float)
    return out


# ---------------------------------------------------------------------------------------------------- one frame

def _pivot(grid: pd.DataFrame, value: str):
    p = grid.pivot(index="tenor_days", columns="delta", values=value).sort_index()
    return p.columns.to_numpy(float), p.index.to_numpy(float), p.to_numpy(float)


def atm_pct(grid: Optional[pd.DataFrame]) -> float:
    """Capital of the ATM 30 d short node (delta 0.5, tenor nearest 30.44 days) in % of the forward."""
    if grid is None or len(grid) == 0:
        return np.nan
    t = grid["tenor_days"].to_numpy(float)
    tn = t[np.argmin(np.abs(t - ATM_DAYS))]
    if abs(tn - ATM_DAYS) > 5.0:
        return np.nan
    sel = grid[np.isclose(grid["delta"], ATM_DELTA) & np.isclose(grid["tenor_days"], tn)]
    return float(sel["K_per_forward_bp"].iloc[0]) / 100.0 if len(sel) else np.nan


def limits(grids: Iterable[Optional[pd.DataFrame]]) -> dict:
    """Colour and height limits shared by every frame. Colour: the full range of the capital over all frames in % of
    the forward, widened to whole half per cent, so that no node is cut (a percentile scale painted the cheapest
    nodes of August 2026 in the colour of its lower end); ``extend`` is therefore "neither". Height: the full range
    of the implied vol over all frames, to whole 5 vol points (no surface leaves the box)."""
    grids = [g for g in grids if g is not None and len(g)]
    if grids:
        k = np.concatenate([g["K_per_forward_bp"].to_numpy(float) for g in grids]) / 100.0
        lo, hi = float(np.nanmin(k)), float(np.nanmax(k))
        iv = np.concatenate([g["iv"].to_numpy(float) for g in grids]) * 100.0
        z0, z1 = float(np.nanmin(iv)), float(np.nanmax(iv))
    else:
        lo, hi = (v / 100.0 for v in p2surface.fit_limits([])["clim"])
        z0, z1 = 20.0, 80.0
    lo, hi = np.floor(lo * 2) / 2, np.ceil(hi * 2) / 2
    return {"clim": (float(lo), float(hi)), "zlim": (float(np.floor(z0 / 5) * 5), float(np.ceil(z1 / 5) * 5)),
            "extend": "neither"}


def outside_scale(k_pct: np.ndarray, clim: Sequence[float]) -> int:
    """Nodes whose capital (% of forward) lies outside the colour scale."""
    k = np.asarray(k_pct, dtype=float)
    k = k[np.isfinite(k)]
    return int(((k < clim[0]) | (k > clim[1])).sum())


def _iso(ax, x, ly, Z, C, zlim) -> None:
    import contourpy
    from scipy.interpolate import RegularGridInterpolator

    if len(x) < 2 or len(ly) < 2:
        return
    gen = contourpy.contour_generator(x, ly, np.ma.masked_invalid(C), line_type="Separate")
    interp = RegularGridInterpolator((ly, x), Z, bounds_error=False, fill_value=None)
    lift = 0.006 * (zlim[1] - zlim[0])
    for lev in ISO:
        segs = [s for s in gen.lines(lev) if len(s) >= 2]
        for s in segs:
            ax.plot(s[:, 0], s[:, 1], interp(np.column_stack([s[:, 1], s[:, 0]])) + lift, color=INK, lw=1.3,
                    zorder=3)
        if segs:
            s = max(segs, key=len)
            k = len(s) // 2
            z = float(interp([[s[k, 1], s[k, 0]]])[0]) + lift
            ax.text(s[k, 0], s[k, 1], z, f"{lev:g} %", fontsize=FS_TICK, color=INK, ha="center", va="bottom",
                    zorder=4, path_effects=STROKE)


def _surface(ax, grid: pd.DataFrame, norm, zlim) -> None:
    x, days, Z = _pivot(grid, "iv")
    Z = Z * 100.0
    C = _pivot(grid, "K_per_forward_bp")[2] / 100.0
    ly = np.log10(days)
    X, Y = np.meshgrid(x, ly)
    colors = matplotlib.colormaps[p2surface.CMAP_NAME](norm(np.nan_to_num(C, nan=norm.vmin)))
    colors[~np.isfinite(C)] = p2surface.NA_COLOR
    ax.computed_zorder = False
    ax.plot_surface(X, Y, Z, facecolors=colors, rstride=1, cstride=1, linewidth=0.25, edgecolor=(0, 0, 0, 0.12),
                    shade=False, antialiased=True, zorder=1)
    y_all = np.log10(p2surface.ANIM_DAYS)
    for lo, hi in ((y_all[0], ly.min()), (ly.max(), y_all[-1])):     # tenors without a live expiry: grey floor
        if hi - lo > 1e-9:
            fx, fy = np.meshgrid([x.min(), x.max()], [lo, hi])
            ax.plot_surface(fx, fy, np.full(fx.shape, zlim[0]), color=p2surface.NA_COLOR, shade=False, zorder=0,
                            linewidth=0)
    _iso(ax, x, ly, Z, C, zlim)


def _axes3d(ax, zlim) -> None:
    ax.set_facecolor("white")
    for a_ in (ax.xaxis, ax.yaxis, ax.zaxis):
        a_.set_pane_color((1, 1, 1, 0))
        a_._axinfo["grid"]["color"] = (0.86, 0.86, 0.86, 1.0)
    ax.view_init(elev=24, azim=-128)
    ax.set_xlim(0.05, 0.95)
    y_all = np.log10(p2surface.ANIM_DAYS)
    ax.set_ylim(y_all[0], y_all[-1])
    ax.set_zlim(*zlim)
    ax.set_xticks([0.1, 0.5, 0.9])
    ax.set_xticklabels(["0.1", "0.5", "0.9"])
    ticks = np.array([1, 7, 30, 90, 365])
    ax.set_yticks(np.log10(ticks))
    ax.set_yticklabels([str(t) for t in ticks])
    zt = np.arange(np.ceil(zlim[0] / 20) * 20, zlim[1] + 1e-9, 20)
    ax.set_zticks(zt)
    ax.set_zticklabels([f"{v:.0f}" for v in zt])
    ax.tick_params(labelsize=FS_TICK, colors=INK, pad=1)
    ax.set_xlabel("call delta", fontsize=FS_LABEL, labelpad=10)
    ax.set_ylabel("days to expiry", fontsize=FS_LABEL, labelpad=12)
    ax.set_zlabel("implied vol, %", fontsize=FS_LABEL, labelpad=8)


def _strip(ax, series: pd.DataFrame, ts: int, marks: pd.DataFrame, start: str, end: str) -> None:
    t = pd.to_datetime(series["ts"], unit="s")
    for m in ("sm", "pm", "pm2"):
        if m in series and np.isfinite(series[m]).any():
            color, ls = MANAGER_STYLE[m]
            ax.plot(t, series[m], color=color, ls=ls, lw=2.2)
    lo, hi = pd.Timestamp(start) - pd.Timedelta(days=6), pd.Timestamp(end) + pd.Timedelta(days=6)
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, YTOP)
    ax.set_yticks([0, 10, 20, 30])
    ev_t = [pd.to_datetime(int(v), unit="s") for v in marks["event_ts"]]
    for i, (et, label) in enumerate(zip(ev_t, marks["printed_step"])):
        ax.axvline(et, color=GREY, lw=1.0, zorder=1)
        left = not (i > 0 and (et - ev_t[i - 1]).days < 45)     # left of the line unless the previous is close
        dx = pd.Timedelta(days=-3 if left else 3)
        ax.text(et + dx, 1.03, label, fontsize=FS_TICK, color=INK, ha="right" if left else "left", va="bottom",
                transform=ax.get_xaxis_transform(), zorder=4)
    ax.axvline(pd.to_datetime(int(ts), unit="s"), color=INK, lw=2.0, zorder=5)
    ax.tick_params(labelsize=FS_TICK, colors=INK, length=4)
    ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=(1, 4, 7, 10)))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %Y"))
    ax.grid(True, axis="y", alpha=0.3, lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_ylabel("straddle,\n% of fwd", fontsize=FS_LABEL, labelpad=4)


def banner_lines(banner: str) -> List[str]:
    """Two lines of a banner ``date · what changed · straddle step``: date and step first, then what changed."""
    parts = [p.strip() for p in banner.split(" · ") if p.strip()]
    if len(parts) >= 3:
        return [f"{parts[0]} · {parts[-1]}", " · ".join(parts[1:-1])]
    return textwrap.wrap(banner, 46)[:2]


def render(grid: Optional[pd.DataFrame], *, ts: int, lim: dict, series: pd.DataFrame, marks: pd.DataFrame,
           sm_atm: float = np.nan, banner: str = "", left_out: int = 0, start: str = START, end: str = END,
           return_figure: bool = False):
    """One frame, ``HEIGHT`` x ``WIDTH`` RGB (or the figure with ``return_figure``)."""
    with plt.rc_context({"font.size": FS_TICK, "savefig.bbox": None, "figure.dpi": DPI, "axes.linewidth": 1.0,
                         "font.family": "DejaVu Sans"}):
        fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI, facecolor="white")
        norm = Normalize(*lim["clim"])
        ax = fig.add_axes([-0.04, 0.29, 0.82, 0.60], projection="3d")
        ax.set_box_aspect((1.35, 1.0, 0.75), zoom=1.2)
        _axes3d(ax, lim["zlim"])
        if grid is not None and len(grid):
            _surface(ax, grid, norm, lim["zlim"])
        cax = fig.add_axes([0.805, 0.37, 0.017, 0.37])
        extend = lim.get("extend", "neither")
        cb = fig.colorbar(ScalarMappable(norm=norm, cmap=matplotlib.colormaps[p2surface.CMAP_NAME]), cax=cax,
                          extend=extend, extendfrac=0.06)
        span = lim["clim"][1] - lim["clim"][0]
        step = 2 if span <= 12 else 4
        ticks = np.arange(np.ceil(lim["clim"][0] / step) * step, lim["clim"][1] + 1e-9, step)
        cb.set_ticks(ticks)
        cb.set_ticklabels([f"{v:g}" for v in ticks])
        cb.ax.tick_params(labelsize=FS_TICK, colors=INK)
        for lev in ISO:
            cb.ax.axhline(lev, color=INK, lw=1.6)
        cb.set_label("capital, % of forward", fontsize=FS_LABEL, labelpad=6)
        note = f"fixed: {lim['clim'][0]:g} to {lim['clim'][1]:g} %"
        if extend != "neither":            # arrows: values beyond the scale take the colour of its ends
            note += ", beyond at the ends"
        fig.text(0.785, 0.345, note, fontsize=FS_TICK, color=GREY, va="top")
        when = dt.datetime.fromtimestamp(int(ts), dt.timezone.utc)
        fig.text(0.012, 0.975, "BTC · PM2 capital of one short contract", fontsize=FS_TITLE, fontweight="bold",
                 color=INK, va="top")
        fig.text(0.988, 0.975, f"{when:%d %b %Y}, {when:%H:%M} UTC", fontsize=FS_DATE, color=INK, ha="right",
                 va="top")
        fig.text(0.988, 0.905, f"block {block_at_ts(int(ts)):,}".replace(",", " "), fontsize=FS_TICK, color=GREY,
                 ha="right", va="top")
        sm_txt = f"{sm_atm:.1f} %" if np.isfinite(sm_atm) else "n/a"
        pm2_txt = f"{atm_pct(grid):.1f} %" if grid is not None and np.isfinite(atm_pct(grid)) else "n/a"
        fig.text(0.012, 0.905, f"ATM 30 d short: PM2 {pm2_txt} · SM, same contract, {sm_txt}", fontsize=FS_LABEL,
                 color=INK, va="top")
        if left_out > 0:
            fig.text(0.988, 0.245, f"{left_out} expir{'y' if left_out == 1 else 'ies'} without fresh feed left out",
                     fontsize=FS_TICK, color=INK, va="bottom", ha="right",
                     bbox=dict(boxstyle="round,pad=0.25", fc="#F2F2F2", ec=GREY, lw=0.8))
        if banner:
            fig.text(0.012, 0.845, "\n".join(banner_lines(banner)), fontsize=FS_BANNER, fontweight="bold",
                     color="white", ha="left", va="top", linespacing=1.12,
                     bbox=dict(boxstyle="square,pad=0.3", fc=INK, ec=INK), zorder=10)
        sx = fig.add_axes([0.105, 0.065, 0.64, 0.14])
        _strip(sx, series, ts, marks, start, end)
        last = series.dropna(subset=["pm2"]).iloc[-1] if series["pm2"].notna().any() else None
        if last is not None:
            y_used: List[float] = []
            for m in ("sm", "pm", "pm2"):
                v = float(last[m]) if m in last else np.nan
                if not np.isfinite(v):
                    continue
                y = v
                for u in y_used:
                    if abs(y - u) < 7.0:
                        y = u - 7.0
                y_used.append(y)
                color, _ = MANAGER_STYLE[m]
                sx.annotate(f"{MANAGER_NAME[m]} {v:.0f} %", xy=(1.0, y), xycoords=("axes fraction", "data"),
                            xytext=(8, 0), textcoords="offset points", fontsize=FS_TICK, color=color, va="center",
                            ha="left", annotation_clip=False)
        if return_figure:
            return fig
        fig.canvas.draw()
        rgb = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
        plt.close(fig)
        return rgb


# ---------------------------------------------------------------------------------------------------- writing

def write_gif(frames: Sequence[np.ndarray], holds: Sequence[int], path: Path, fps: float = FPS) -> Path:
    """GIF with one global 256-colour palette (from a sample of the frames); a held frame is written once with a
    longer duration."""
    from PIL import Image

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    idx = np.unique(np.linspace(0, len(frames) - 1, min(len(frames), 12)).astype(int))
    sample = Image.fromarray(np.concatenate([frames[i][::2, ::2] for i in idx], axis=0))
    pal = sample.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    colours = np.asarray(pal.getpalette()[:768], dtype=float).reshape(-1, 3)
    for target in ((255, 255, 255), (17, 17, 17)):           # paper white and ink stay exact
        k = int(np.argmin(((colours - np.asarray(target)) ** 2).sum(axis=1)))
        if np.abs(colours[k] - np.asarray(target)).max() <= 8:
            colours[k] = target
    pal.putpalette([int(v) for v in colours.ravel()])
    imgs = [_indexed(f, colours, pal) for f in frames]
    base = int(round(1000 / fps))
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=[base * int(h) for h in holds], loop=0,
                 optimize=False, disposal=1)
    return path


def _indexed(frame: np.ndarray, colours: np.ndarray, pal) -> "Image.Image":
    """Frame mapped to the nearest colour of the global palette (exact nearest neighbour over the frame's distinct
    colours; Pillow's own mapping works on a reduced colour cube and turns paper white into light grey)."""
    from PIL import Image

    flat = frame.reshape(-1, 3).astype(np.int64)
    key = (flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]
    uniq, inv = np.unique(key, return_inverse=True)
    rgb = np.stack([(uniq >> 16) & 255, (uniq >> 8) & 255, uniq & 255], axis=1).astype(float)
    best = np.empty(len(uniq), dtype=np.uint8)
    for i in range(0, len(uniq), 4096):
        d = ((rgb[i:i + 4096, None, :] - colours[None, :, :]) ** 2).sum(axis=2)
        best[i:i + 4096] = np.argmin(d, axis=1)
    h, w = frame.shape[:2]
    img = Image.frombytes("P", (w, h), np.ascontiguousarray(best[inv].reshape(h, w)).tobytes())
    img.putpalette(pal.getpalette())
    return img


def compute(plan: pd.DataFrame, *, ccy: str = CCY, loader: Optional[Callable[[int, int], object]] = None
            ) -> List[dict]:
    """Capital grids of PM2 and SM for every frame of ``plan`` (heavy: feed history per quarter)."""
    loader = loader or (lambda lo, hi: p2surface.load_history(ccy, lo, hi))
    tenors = p2surface.ANIM_DAYS / 365.0
    out: List[dict] = []
    q = [f"{pd.Timestamp(int(t), unit='s').year}Q{(pd.Timestamp(int(t), unit='s').month - 1) // 3 + 1}"
         for t in plan["ts"]]
    for key in dict.fromkeys(q):
        rows = plan[[k == key for k in q]]
        hist = loader(int(rows["ts"].min()) - 2 * DAY, int(rows["ts"].max()))
        for r in rows.itertuples():
            ts = int(r.ts)
            rec = {"ts": ts, "grid": None, "sm": None, "n_expiries": 0, "n_left_out": 0, "skipped": ""}
            exps = p2surface.live_expiries(hist, ts)
            rec["n_expiries"] = len(exps)
            rec["n_left_out"] = _stale(hist, ts)
            if not exps:
                rec["skipped"] = "no live expiry"
                out.append(rec)
                continue
            state = hist.state_at(ts, exps)
            try:
                rec["grid"] = p2surface.capital_grid(ccy, ts, MANAGER, "short", hist=hist, state=state,
                                                     tenors=tenors)
                rec["sm"] = p2surface.capital_grid(ccy, ts, "sm", "short", hist=hist, state=state, tenors=tenors)
            except ValueError as exc:
                rec["skipped"] = str(exc)[:120]
            out.append(rec)
            log.info("%s %s: %d expiries, %d stale", ccy, _day(ts), rec["n_expiries"], rec["n_left_out"])
        del hist
    return out


def _stale(hist, ts: int) -> int:
    """Expiries after ``ts`` with a vol or forward push before ``ts`` that is older than ``LIVE_MAX_AGE``."""
    e = np.asarray(hist.svi.expiries, dtype=np.int64)
    e = e[e > int(ts) + p2surface.MIN_DAYS * DAY]
    if len(e) == 0:
        return 0
    b = hist.bulk(np.full(len(e), int(ts)), e, np.full(len(e), np.nan))
    va, fa = b["vol_age"].to_numpy(float), b["fwd_age"].to_numpy(float)
    known = np.isfinite(va) & np.isfinite(fa)
    stale = known & ((va > p2surface.LIVE_MAX_AGE) | (fa > p2surface.LIVE_MAX_AGE))
    return int(stale.sum())


def build(step: str = "weekly", start: str = START, end: str = END, out: Path = OUT,
          results_dir: Path = RESULTS, loader: Optional[Callable[[int, int], object]] = None,
          t1_grid: Optional[Path] = None) -> dict:
    """Plan, compute, render and write the GIF, its poster, the MP4 and the frame table."""
    rd = Path(results_dir)
    events = kept_events(pd.read_csv(rd / "events.csv"))
    rb = pd.read_csv(rd / "reference_book.csv")
    plan = frame_plan(events, start, end, step)
    marks = banners(events, rb, lambda ts: grid_widths(CCY, ts))
    series = reference_series(rb, CCY, start, end)
    recs = compute(plan, loader=loader)
    grids = [r["grid"] for r in recs if r["grid"] is not None]
    lim = limits(grids)
    frames, holds, table = [], [], []
    banner_of = dict(zip(marks["event_id"], marks["banner"]))
    for (i, p), r in zip(plan.iterrows(), recs):
        g = r["grid"]
        row = {"frame": len(frames), "day": p["day"], "ts": int(p["ts"]), "block": block_at_ts(int(p["ts"])),
               "kind": p["kind"], "event_id": p["event_id"], "hold": int(p["hold"]),
               "duration_ms": int(round(1000 / FPS)) * int(p["hold"]), "n_expiries": r["n_expiries"],
               "n_left_out": r["n_left_out"], "skipped": r["skipped"], "banner": ""}
        if g is None:
            row["frame"] = -1
            table.append(row)
            continue
        banner = banner_of.get(p["event_id"], "") if p["kind"] == "after" else ""
        k = g["K_per_forward_bp"].to_numpy(float) / 100.0
        row.update(banner=banner, K_min_pct=float(np.nanmin(k)), K_median_pct=float(np.nanmedian(k)),
                   K_max_pct=float(np.nanmax(k)), pm2_atm_pct=atm_pct(g), sm_atm_pct=atm_pct(r["sm"]),
                   n_nodes=int(len(g)))
        frames.append(render(g, ts=int(p["ts"]), lim=lim, series=series, marks=marks, sm_atm=row["sm_atm_pct"],
                             banner=banner, left_out=r["n_left_out"], start=start, end=end))
        holds.append(int(p["hold"]))
        table.append(row)
    out = Path(out)
    gif = write_gif(frames, holds, out)
    from PIL import Image

    poster = out.with_name(out.stem + "_end.png")
    Image.fromarray(frames[-1]).save(poster, optimize=True)
    from .animate import write_mp4

    mp4 = write_mp4([f for f, h in zip(frames, holds) for _ in range(h)], out.with_suffix(".mp4"), FPS)
    tab = pd.DataFrame(table)
    tab.to_csv(rd / FRAMES_CSV, index=False)
    outside = sum(outside_scale(g["K_per_forward_bp"].to_numpy(float) / 100.0, lim["clim"]) for g in grids)
    meta = {"gif": str(gif), "bytes": gif.stat().st_size, "max_bytes": MAX_BYTES, "frames": len(frames),
            "skipped": int((tab["frame"] < 0).sum()), "step": step, "start": start, "end": end,
            "clim_pct": list(lim["clim"]), "extend": lim.get("extend", "neither"), "nodes_outside_scale": outside,
            "zlim": list(lim["zlim"]), "poster": str(poster),
            "mp4": str(mp4) if mp4 else None, "steps": dict(zip(marks["event_id"], marks["printed_step"]))}
    last = recs[-1]["grid"] if recs and recs[-1]["grid"] is not None else None
    t1_path = Path(t1_grid) if t1_grid is not None else rd / "t1_grid.csv"
    if last is not None and t1_path.exists() and int(plan["ts"].iloc[-1]) == int(pd.read_csv(t1_path)["ts"].iloc[0]):
        t1g = pd.read_csv(t1_path)
        t1g = t1g[t1g["manager"] == MANAGER]
        key = ["d", "t"]
        a = last.assign(d=last["delta"].round(9), t=last["tenor_days"].round(6))[key + ["K"]]
        b = t1g.assign(d=t1g["delta"].round(9), t=t1g["tenor_days"].round(6))[key + ["K"]]
        both = a.merge(b, on=key, suffixes=("", "_t1"))
        meta["last_frame_nodes_matched_t1"] = int(len(both))
        meta["last_frame_max_abs_diff_usdc_t1"] = float(np.abs(both["K"] - both["K_t1"]).max())
    (rd / META_JSON).write_text(json.dumps(meta, indent=1))
    if meta["bytes"] > MAX_BYTES:
        raise RuntimeError(f"{gif} has {meta['bytes'] / 2**20:.1f} MB, more than 8 MB")
    return meta
