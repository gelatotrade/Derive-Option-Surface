"""Social cards of Paper 2 at 1600 x 900, drawn to be read on a phone
(``docs/paper2/FIGURE_SELECTION.md``, section 9).

Pattern ``figures_social.py`` (fixed size, no tight bounding box, one idea per card). Every number is read from
``results/p2``, never typed, and each number of a title stands in the drawing as well. Type at least 28 px, colour
only for the managers and always together with a line style or hatch, simple per cent. Cards:

* ``s1_three_engines.png``: one short BTC straddle under the three margin managers over time (the series of F5 c),
  the steps of the parameter changes kept for H4 and the three values of the last day;
* ``s2_straddle_vs_call.png``: one short call against the short straddle under PM2 and SM, from the same reference
  row as T2 c; the title follows the rule of section 9 (the card is left out when neither title holds);
* ``s3_verdicts.png``: the four registered tests with estimate, interval, threshold and rejection side, H4 with
  the placebo 95th percentile and the one-sided p; the verdicts are rebuilt with the rules of the verdict ruler
  (``figs_p2.f2.verdict``, ``figs_p2.f6.checklist``). Title and layout do not depend on the outcome.

Departures from section 9, and why: the first card says "margin managers", not "margin engines", because the paper
keeps "engine" for the two implementations (off-chain and on chain) of the managers; the footer names the commit of
the pre-registration (``c9e9162``, ``cc0a29f`` before the rewrite of 5 October 2026), not that of Addendum 4; H4 shows no interval, since its interval is descriptive
and too narrow for the spread between placebo dates (audit A05); the statement of H2 names the whole fill, which is
what the registered statistic covers.

The numbers of every card go to ``results/p2/fig_s{1,2,3}.csv`` (``key, value, printed, source``). A source reads
``<file>:<column>@<col>=<value>,...`` (one row of a CSV), ``<file>.json:<dotted key>`` or ``step <event_id>`` (the
step the parameters alone make to the reference straddle, as in F5 b and the GIF); ``scripts/p2_figure_check.py``
compares every value with its source.
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates  # noqa: E402
import matplotlib.lines  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.transforms  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

WIDTH, HEIGHT, DPI = 10.0, 5.625, 160          # 1600 x 900 px
MIN_PX = 28.0
PT = 72.0 / DPI                                 # points per pixel
INK = "#111111"
MUTED = "#555555"
HATCH_GREY = "#999999"
MANAGER = {"pm2": ("#0072B2", "-", "PM2"), "pm": ("#009E73", ":", "legacy PM"), "sm": ("#D55E00", "--", "SM")}
FOOTER = "Derive, chain 957 · replica of the deployed margin contracts · pre-registration c9e9162"
RESULTS = Path("results/p2")
OUT = Path("paper2/social")
MINUS = "−"
RC = {
    "font.size": 16.0, "axes.titlesize": 16.0, "axes.labelsize": 15.0, "xtick.labelsize": 14.0,
    "ytick.labelsize": 14.0, "legend.fontsize": 14.0, "legend.frameon": False, "axes.grid": False,
    "axes.linewidth": 1.2, "axes.edgecolor": INK, "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK,
    "ytick.color": INK, "xtick.major.width": 1.2, "ytick.major.width": 1.2, "xtick.major.size": 6,
    "ytick.major.size": 6, "lines.linewidth": 3.0, "figure.dpi": DPI, "savefig.dpi": DPI,
    "savefig.facecolor": "white", "figure.facecolor": "white", "savefig.bbox": None, "savefig.pad_inches": 0.0,
    "figure.autolayout": False, "axes.unicode_minus": True, "font.family": "DejaVu Sans", "hatch.linewidth": 1.2,
}
TAKE_CHARS = 84                                 # 14 pt at 160 dpi: a line of the takeaway fits the card
TITLE_CHARS = 46                                # 24 pt bold: a longer title breaks into two lines
LINE_PX = 4.0                                   # section 9: lines of 4 px


def pct(x: float, digits: int = 1) -> str:
    return f"{float(x):.{digits}f} %".replace("-", MINUS)


def whole_step(simple_pct: float) -> str:
    """A step in simple per cent with sign and a true minus, whole per cent: +2 %, −10 %, −8 %, −23 %."""
    return f"{'+' if simple_pct >= 0 else MINUS}{abs(simple_pct):.0f} %"


def day_text(day: str) -> str:
    return pd.Timestamp(day).strftime("%-d %b %Y")


def load(results_dir: Path = RESULTS) -> dict:
    rd = Path(results_dir)
    h = {k: json.loads((rd / f"{k}.json").read_text()) for k in ("h1", "h2", "h3", "h4")}
    return {"rd": rd, "f5c": pd.read_csv(rd / "fig_f5_c.csv"), "t2c": pd.read_csv(rd / "fig_t2_c.csv"),
            "events": pd.read_csv(rd / "events.csv"), "rb": pd.read_csv(rd / "reference_book.csv"), **h}


def _card(title: str, takeaway: Sequence[str]):
    """Card with a one- or two-line title, a takeaway of at most two lines and the footer."""
    lines = [ln for part in takeaway for ln in textwrap.wrap(part, TAKE_CHARS)]
    if len(lines) > 2:
        raise ValueError(f"takeaway longer than two lines: {lines}")
    matplotlib.rcParams.update(RC)
    fig = plt.figure(figsize=(WIDTH, HEIGHT))
    fig.text(0.035, 0.955, "\n".join(textwrap.wrap(title, TITLE_CHARS)), fontsize=24, fontweight="bold", va="top",
             linespacing=1.1)
    fig.text(0.035, 0.175, "\n".join(lines), fontsize=14, color=MUTED, va="top", linespacing=1.25)
    fig.text(0.035, 0.03, FOOTER, fontsize=13, color=MUTED, va="bottom")
    return fig


def _axes(fig, rect):
    ax = fig.add_axes(rect)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return ax


def _table(rows: Sequence[tuple], results_dir: Path, name: str) -> Path:
    path = Path(results_dir) / name
    pd.DataFrame(rows, columns=["key", "value", "printed", "source"]).to_csv(path, index=False)
    return path


def _save(fig, name: str, out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.png"
    fig.savefig(path)
    return path


def _finish(fig, name: str, out_dir: Path, rows, results_dir: Path, table: str, keep: bool):
    _table(rows, results_dir, table)
    path = _save(fig, name, out_dir)
    if keep:
        return fig, path
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------------------------------- card 1

def steps(data: dict, ccy: str = "BTC") -> pd.DataFrame:
    """Kept events of ``ccy`` (every manager) with the step the parameters alone make to the reference straddle, in
    simple per cent (``gif_p2.banners``, the rule of F5 b)."""
    from . import gif_p2

    out = []
    for m in ("pm", "pm2"):
        ev = gif_p2.kept_events(data["events"], ccy, m)
        b = gif_p2.banners(ev, data["rb"], ccy=ccy, manager=m)
        if len(b):
            out.append(b.assign(manager=m))
    if not out:
        return pd.DataFrame(columns=["event_id", "event_ts", "step_pct", "manager", "printed"])
    s = pd.concat(out, ignore_index=True).sort_values("event_ts", kind="mergesort").reset_index(drop=True)
    s["printed"] = [whole_step(p) for p in s["step_pct"]]
    return s


STEP_SLOTS = [("left", 0), ("right", 0), ("left", 1), ("right", 1)]   # side of the line, tier above the axes
STEP_GAP_PX = 14.0                              # least white space between two step labels


def _place_step(fig, ax, text: str, x, color: str, placed: list):
    """The step label at the top of its event line, left or right of it and on the first of two tiers above the
    axes that keeps it inside the card and clear of the labels already placed (lines 14 days apart cannot carry
    a label each between them)."""
    r = fig.canvas.get_renderer()
    for side, tier in STEP_SLOTS:
        t = ax.annotate(text, xy=(x, 1.0), xycoords=("data", "axes fraction"), xytext=(-5 if side == "left" else 5,
                        4 + 34 * tier), textcoords="offset points", ha="right" if side == "left" else "left",
                        va="bottom", fontsize=13, color=color, fontweight="bold")
        e = t.get_window_extent(r)
        inside = e.x0 >= 0 and e.x1 <= fig.bbox.width and e.y1 <= fig.bbox.height
        if inside and not any(e.padded(STEP_GAP_PX).overlaps(p.get_window_extent(r)) for p in placed):
            if tier:                                  # the event line reaches up to its label
                top = (e.y0 + 0.5 * e.height - ax.get_window_extent(r).y0) / ax.get_window_extent(r).height
                ax.plot([x, x], [1.0, top], color="#999999", lw=1.5, clip_on=False,
                        transform=matplotlib.transforms.blended_transform_factory(ax.transData, ax.transAxes))
            return t
        t.remove()
    raise ValueError(f"no free place for the step label {text!r}")


def card_straddle_series(data: dict, out_dir: Path, *, keep: bool = False):
    """Card 1: the BTC reference straddle per manager over time, the steps of the kept events and the last values."""
    c = data["f5c"]
    c = c[c["ccy"] == "BTC"].sort_values("day", kind="mergesort")
    last = c.iloc[-1]
    st = steps(data)
    title = "One short BTC straddle. Three margin managers."
    take = [f"At the forward, listed expiry nearest 30 days ({last['tenor_days']:.0f} d on {day_text(last['day'])}), "
            "% of forward.", "Capital for a hypothetical book, not a balance."]
    fig = _card(title, take)
    fig.text(0.735, 0.80, f"on {day_text(last['day'])}", fontsize=14, color=MUTED, va="center")
    ax = _axes(fig, [0.075, 0.30, 0.60, 0.44])
    t = pd.to_datetime(c["day"])
    lw = LINE_PX * PT
    for m in ("sm", "pm", "pm2"):
        color, ls, _ = MANAGER[m]
        ax.plot(t, c[f"K_{m}_pct"], color=color, ls=ls, lw=lw, solid_capstyle="butt")
    ax.set_ylim(0, 35)
    ax.set_yticks([0, 10, 20, 30])
    ax.set_yticklabels(["0", "10", "20", "30"])
    ax.set_ylabel("% of forward")
    lo, hi = t.min() - pd.Timedelta(days=10), t.max() + pd.Timedelta(days=10)
    ax.set_xlim(lo, hi)
    ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=(1, 7)))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %Y"))
    ax.grid(True, axis="y", color="#DDDDDD", lw=0.8)
    ax.text(0.01, 0.03, "grey lines: parameter changes kept for H4,\nwith the step they make to the straddle",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=13, color=MUTED, linespacing=1.1)
    placed: list = list(fig.texts)                   # the title and the notes are obstacles as well
    for r in st.itertuples():
        et = pd.to_datetime(int(r.event_ts), unit="s")
        ax.axvline(et, color="#999999", lw=1.5, zorder=0, clip_on=False, ymax=1.03)
        placed.append(_place_step(fig, ax, r.printed, et, MANAGER[r.manager][0], placed))
    # the three values of the last day, large, with the line style and the name
    for k, m in enumerate(("sm", "pm", "pm2")):
        color, ls, name = MANAGER[m]
        y = 0.73 - k * 0.19
        fig.text(0.735, y, f"{float(last[f'K_{m}_pct']):.0f} %", fontsize=30, fontweight="bold", color=color,
                 va="center")
        fig.add_artist(matplotlib.lines.Line2D([0.735, 0.80], [y - 0.075, y - 0.075], color=color, ls=ls, lw=lw,
                                               transform=fig.transFigure))
        fig.text(0.815, y - 0.075, name, fontsize=15, color=INK, va="center")
    day = str(last["day"])
    rows = [(f"last_{m}", float(last[f"K_{m}_pct"]), f"{float(last[f'K_{m}_pct']):.0f} %",
             f"fig_f5_c.csv:K_{m}_pct@ccy=BTC,day={day}") for m in ("sm", "pm", "pm2")]
    rows.append(("tenor_days", float(last["tenor_days"]), f"{last['tenor_days']:.0f} d",
                 f"fig_f5_c.csv:tenor_days@ccy=BTC,day={day}"))
    rows += [(f"step_{r.event_id}", float(r.step_pct), r.printed, f"step {r.event_id}") for r in st.itertuples()]
    return _finish(fig, "s1_three_engines", out_dir, rows, data["rd"], "fig_s1.csv", keep)


# ---------------------------------------------------------------------------------------------------- card 2

TITLE_LESS = "Under PM2 a short straddle needs less capital than one short call."
TITLE_LITTLE = "Under PM2 the second leg of a straddle adds little capital."


def straddle_title(k_straddle: float, k_call: float) -> Optional[str]:
    """Section 9: the first title only if the straddle needs less than one call under PM2, the second if the second
    leg adds less than a quarter of the call; otherwise no card."""
    if k_straddle < k_call:
        return TITLE_LESS
    if k_straddle - k_call < 0.25 * k_call:
        return TITLE_LITTLE
    return None


def card_straddle_vs_call(data: dict, out_dir: Path, *, keep: bool = False):
    """Card 2: one short call and the short straddle, PM2 and SM, from the reference row of T2 c."""
    c = data["t2c"]
    cap = c[c["kind"] == "capital"].set_index("item")["value_pct_forward"].astype(float)
    meta = c[c["kind"] == "meta"].set_index("item")["value_usdc"]
    vals = {"pm2": (cap["K_pm2_call"], cap["K_pm2_book"]), "sm": (cap["K_sm_call"], cap["K_sm"])}
    title = straddle_title(vals["pm2"][1], vals["pm2"][0])
    if title is None:
        return None
    when = pd.Timestamp(int(float(meta["ts"])), unit="s")
    take = [f"BTC, {when:%-d %b %Y}, {when:%H:%M} UTC, strike at the forward, {float(meta['tenor_days']):.0f} days, "
            "% of forward.", "Capital, not risk."]
    fig = _card(title, take)
    ax = _axes(fig, [0.10, 0.31, 0.84, 0.46])
    width, top = 0.36, max(v for pair in vals.values() for v in pair)
    rows = []
    for g, m in enumerate(("pm2", "sm")):
        color, _, name = MANAGER[m]
        for k, (label, v) in enumerate((("one short call", vals[m][0]), ("short straddle", vals[m][1]))):
            x = g + (k - 0.5) * (width + 0.04)
            filled = label == "short straddle"
            if filled and m == "sm":                  # hatch in white on the fill, as SM is hatched in F5 a
                ax.bar(x, v, width=width, color=color, edgecolor="white", lw=0.0, hatch="//")
            else:
                ax.bar(x, v, width=width, color=color if filled else "white", lw=0.0)
            ax.bar(x, v, width=width, fill=False, edgecolor=color, lw=3.0)
            ax.text(x, v + 0.02 * top, pct(v), ha="center", va="bottom", fontsize=17, fontweight="bold")
            ax.text(x, -0.04 * top, label, ha="center", va="top", fontsize=14)
            item = {("pm2", 0): "K_pm2_call", ("pm2", 1): "K_pm2_book", ("sm", 0): "K_sm_call", ("sm", 1): "K_sm"}
            key = item[(m, k)]
            rows.append((key, float(v), pct(v), f"fig_t2_c.csv:value_pct_forward@item={key}"))
        ax.text(g, -0.17 * top, name, ha="center", va="top", fontsize=18, fontweight="bold", color=color)
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylim(0, 1.18 * top)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(True)
    ax.set_ylabel("% of forward")
    ax.set_yticks([0, 10, 20, 30])
    rows.append(("tenor_days", float(meta["tenor_days"]), f"{float(meta['tenor_days']):.0f} days",
                 "fig_t2_c.csv:value_usdc@item=tenor_days"))
    return _finish(fig, "s2_straddle_vs_call", out_dir, rows, data["rd"], "fig_s2.csv", keep)


# ---------------------------------------------------------------------------------------------------- card 3

STATEMENTS = [
    ("H1", "The capital denominator reorders the map"),
    ("H2", "A fill in a dominant maker's PM2 book binds under half its stand-alone capital"),
    ("H3", "PM2 needs less than half the capital of standard margin for the same books"),
    ("H4", "Cheaper capital, tighter spreads"),
]
ROW_Y = (0.775, 0.61, 0.445, 0.28)              # centre of each test row, figure fraction
STATEMENT_CHARS = 41
RULER_X, RULER_W = 0.53, 0.25                   # the verdict bar of each row, figure fraction


def verdicts(data: dict) -> Dict[str, dict]:
    """Estimate, bounds, threshold, rule text and verdict per test, the verdicts rebuilt with the rules of the ruler
    (a mismatch with ``rejected`` of the result file raises)."""
    from .figs_p2 import f2, f6

    out = {}
    for key, side in (("h1", "upper"), ("h2", "upper"), ("h3", "lower")):
        h = data[key]
        rej = f2.verdict(h, side=side)
        thr = float(h["threshold"])
        out[key] = {"stat": float(h["stat"]), "lo": float(h["lo"]), "hi": float(h["hi"]), "threshold": thr,
                    "side": side, "rejected": rej,
                    "rule": f"rejected if the {'upper' if side == 'upper' else 'lower'} bound "
                            f"{'≥' if side == 'upper' else '≤'} {thr:g}"}
    h4 = data["h4"]
    lines = f6.checklist(h4)
    out["h4"] = {"stat": float(h4["stat"]), "p": float(h4["p"]), "p95": float(h4["placebo"]["p95"]),
                 "threshold": 0.0, "side": "beta", "rejected": bool(lines[2][1]),
                 "rule": f"rejected unless β > 0, p ≤ {f6.ALPHA:g}, β > P95"}
    return out


def _num(x: float, digits: int) -> str:
    return f"{x:.{digits}f}".replace("-", MINUS)


def _number_line(v: dict, key: str) -> str:
    """Estimate and 90 % interval in brackets (H4: estimate and one-sided p), as in the headers of the forests."""
    d = {"h1": 2, "h2": 3, "h3": 2}.get(key)
    if d is None:
        return f"β = {_num(v['stat'], 1)}, one-sided p = {_num(v['p'], 2)}, P95 {_num(v['p95'], 1)}"
    name = "ρ" if key == "h1" else "median"
    return f"{name} {_num(v['stat'], d)} [{_num(v['lo'], d)}, {_num(v['hi'], d)}]"


def _ruler(ax, v: dict, key: str) -> None:
    """One verdict bar: hatched rejection side, dashed threshold, interval and estimate (H4: estimate and the
    placebo 95th percentile)."""
    if key == "h3":
        ax.set_xscale("log")
        x0, x1 = min(1.0, v["lo"] / 1.2), max(8.0, v["hi"] * 1.2)
        ticks = [t for t in (1, 2, 4, 8, 16) if x0 <= t <= x1]
        labels = [f"{t:g}×" for t in ticks]
    elif key == "h4":
        x0 = min(-50.0, v["stat"] - 10.0)
        x1 = max(50.0, v["p95"] + 10.0, v["stat"] + 10.0)
        ticks = [t for t in (-50, -25, 0, 25, 50) if x0 <= t <= x1]
        labels = [f"{t:g}".replace("-", MINUS) for t in ticks]
    else:
        x0, x1 = min(0.0, v["lo"] - 0.05), max(1.0, v["hi"] + 0.05)
        ticks = [0.0, 0.5, 1.0]
        labels = ["0", "0.5", "1"]
    ax.set_xlim(x0, x1)
    ax.set_ylim(-1, 1)
    thr = v["threshold"]
    if v["side"] == "upper":
        left, right = thr, x1
    elif v["side"] == "beta":                   # H4 rejects every β ≤ max(0, placebo P95) (audit B3)
        left, right = x0, max(thr, v["p95"])
    else:
        left, right = x0, thr
    ax.add_patch(Rectangle((left, -0.8), right - left, 1.6, fill=False, hatch="//", edgecolor=HATCH_GREY, lw=0.0,
                           zorder=0))
    ax.axvline(thr, color=INK, ls="--", lw=2.0, zorder=1)
    if key == "h4":
        ax.plot([v["p95"], v["p95"]], [-0.8, 0.8], color=MUTED, lw=3.0, zorder=2)
        ax.annotate("placebo P95", xy=(v["p95"], 0.8), xytext=(4, 0), textcoords="offset points", ha="left",
                    va="top", fontsize=13, color=MUTED)
    else:
        ax.plot([v["lo"], v["hi"]], [0, 0], color=INK, lw=6.0, solid_capstyle="butt", zorder=3)
    ax.plot([v["stat"]], [0], "o", ms=13, mfc=INK, mec="white", mew=1.5, zorder=4)
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)
    ax.minorticks_off()
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="x", labelsize=13, pad=2)


def card_verdicts(data: dict, out_dir: Path, *, keep: bool = False):
    """Card 3: the four registered tests and their verdicts; title and layout independent of the outcome."""
    v = verdicts(data)
    title = "Four pre-registered tests. Four verdicts."
    take = ["Registered before the capital figures of the analysis; numbers from a pilot cut.",
            "[ ]: 90 % interval. Hatched: an interval (H4: the estimate) reaching it rejects."]
    fig = _card(title, take)
    rows = []
    for (label, statement), y in zip(STATEMENTS, ROW_Y):
        key = label.lower()
        r = v[key]
        fig.text(0.035, y + 0.03, label, fontsize=18, fontweight="bold", va="center")
        fig.text(0.085, y + 0.03, "\n".join(textwrap.wrap(statement, STATEMENT_CHARS)), fontsize=14, va="center",
                 linespacing=1.1)
        fig.text(0.085, y - 0.05, r["rule"], fontsize=13, color=MUTED, va="center")
        ax = _axes(fig, [RULER_X, y - 0.05, RULER_W, 0.045])
        _ruler(ax, r, key)
        fig.text(RULER_X, y + 0.005, _number_line(r, key), fontsize=13, va="bottom")
        fig.text(0.965, y - 0.03, "rejected" if r["rejected"] else "not rejected", fontsize=17, fontweight="bold",
                 ha="right", va="center")
        src, line = f"{key}.json", _number_line(r, key)
        fields = (("stat", "p", "p95") if key == "h4" else ("stat", "lo", "hi", "threshold"))
        rows += [(f"{key}_{f}", r[f], line, f"{src}:{'placebo.p95' if f == 'p95' else f}") for f in fields]
        rows.append((f"{key}_rejected", float(r["rejected"]), "rejected" if r["rejected"] else "not rejected",
                     f"{src}:rejected"))
    return _finish(fig, "s3_verdicts", out_dir, rows, data["rd"], "fig_s3.csv", keep)


CARDS: Dict[str, Callable] = {"s1": card_straddle_series, "s2": card_straddle_vs_call, "s3": card_verdicts}
NAMES = {"s1": "s1_three_engines", "s2": "s2_straddle_vs_call", "s3": "s3_verdicts"}


def build(results_dir: Path = RESULTS, out_dir: Path = OUT, only: Optional[Sequence[str]] = None) -> List[Path]:
    """Write the cards (all three unless ``only``); a card whose title rule fails is left out and not listed."""
    data = load(results_dir)
    names = list(CARDS) if only is None else list(only)
    paths = [CARDS[n](data, Path(out_dir)) for n in names]
    return [p for p in paths if p is not None]
