"""Social cards of Paper 2: three core findings at 1600 x 900, drawn to be read on a phone.

Pattern ``figures_social.py`` (fixed size, no tight bounding box, one idea per card, the takeaway in the picture).
Every number is read from ``results/p2/summary.json`` (and the figure tables of F2 and F4 for the drawings), never
typed; each number of a title stands in the drawing as well. Type at least 28 px, colour only for PM2 and always
together with a second cue, simple per cent. Cards:

* ``s1_h2_next_contract.png`` (H2): the next contract in a big PM2 book costs a few per cent of its stand-alone
  capital;
* ``s2_h3_netting.png`` (H3): PM2 needs a multiple less capital than standard margin for the same maker books;
* ``s3_h1_map.png`` (H1): per unit of capital, the map of where makers earn stays the same (Spearman's rho).

The numbers of every card go to ``results/p2/fig_s{1,2,3}.csv`` (``key, value, printed, source``).
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

WIDTH, HEIGHT, DPI = 10.0, 5.625, 160          # 1600 x 900 px
MIN_PX = 28.0
PT = 72.0 / DPI                                 # points per pixel
INK = "#111111"
MUTED = "#555555"
PM2 = "#0072B2"
FOOTER = "Derive, chain 957 · replica of the deployed margin contracts · pre-registration commit c4fcb59"
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
    "figure.autolayout": False, "axes.unicode_minus": True, "font.family": "DejaVu Sans",
}


def pct(x: float, digits: int = 1) -> str:
    return f"{100 * float(x):.{digits}f} %"


def thousands(n) -> str:
    return f"{int(round(float(n))):,}".replace(",", " ")


def month(day: str) -> str:
    return pd.Timestamp(day).strftime("%b %Y")


def load(results_dir: Path = RESULTS) -> dict:
    rd = Path(results_dir)
    return {"summary": json.loads((rd / "summary.json").read_text()), "f4a": pd.read_csv(rd / "fig_f4_a.csv"),
            "f2b": pd.read_csv(rd / "fig_f2_b.csv"), "rd": rd}


TAKE_CHARS = 84                                 # 14 pt at 160 dpi: a line of the takeaway fits the card


def _card(title: str, takeaway: Sequence[str]):
    """Card with a two-line title, a takeaway of at most two lines and the footer."""
    lines = [ln for part in takeaway for ln in textwrap.wrap(part, TAKE_CHARS)]
    if len(lines) > 2:
        raise ValueError(f"takeaway longer than two lines: {lines}")
    matplotlib.rcParams.update(RC)
    fig = plt.figure(figsize=(WIDTH, HEIGHT))
    fig.text(0.035, 0.955, title, fontsize=24, fontweight="bold", va="top", linespacing=1.1)
    fig.text(0.035, 0.195, "\n".join(lines), fontsize=14, color=MUTED, va="top", linespacing=1.25)
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


# ---------------------------------------------------------------------------------------------------- cards

def card_h2(data: dict, out_dir: Path, *, keep: bool = False):
    """H2: the next contract in a big PM2 book against the same contract on its own."""
    s = data["summary"]
    stat, lo, hi, share0 = (float(s[k]) for k in ("h2_stat", "h2_lo", "h2_hi", "h2_share_nonpositive"))
    p_stat, p0 = pct(stat), pct(share0, 0)
    title = f"In a big PM2 book, the next contract costs\n{p_stat} of its stand-alone capital"
    take = [f"Median of {thousands(s['h2_n'])} fills, {s['h2_n_accounts']} PM2 maker accounts (ETH, HYPE), "
            f"{month(s['h2_first_day'])} to {month(s['h2_last_day'])};",
            f"90 % interval {pct(lo)} to {pct(hi)}. {p0} of the fills add no capital at all."]
    fig = _card(title, take)
    ax = _axes(fig, [0.30, 0.34, 0.64, 0.36])
    ax.barh([1], [100.0], height=0.55, color="white", edgecolor=PM2, linewidth=3.0, hatch="//")
    ax.barh([0], [100 * stat], height=0.55, color=PM2, edgecolor=PM2, linewidth=3.0)
    ax.errorbar([100 * stat], [0], xerr=[[100 * (stat - lo)], [100 * (hi - stat)]], fmt="none", ecolor=INK,
                elinewidth=2.5, capsize=8)
    ax.text(100.0 - 2, 1, "100 %", ha="right", va="center", fontsize=18, fontweight="bold",
            bbox=dict(fc="white", ec="none", pad=1))
    ax.text(100 * hi + 2.0, 0, p_stat, ha="left", va="center", fontsize=22, fontweight="bold", color=INK)
    ax.set_yticks([1, 0])
    ax.set_yticklabels(["the contract\non its own", "the same contract\nadded to the book"], fontsize=15)
    ax.set_xlim(0, 105)
    ax.set_ylim(-0.6, 1.6)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0 %", "25 %", "50 %", "75 %", "100 %"])
    ax.set_xlabel("PM2 capital of one more contract, % of its stand-alone capital")
    ax.text(0.5, 1.02, f"{p0} of fills: free (book capital does not rise)", transform=ax.transAxes, ha="center",
            va="bottom", fontsize=15, color=INK)
    rows = [("stat", stat, p_stat, "summary.json h2_stat"), ("lo", lo, pct(lo), "summary.json h2_lo"),
            ("hi", hi, pct(hi), "summary.json h2_hi"),
            ("share_nonpositive", share0, p0, "summary.json h2_share_nonpositive"),
            ("n", s["h2_n"], thousands(s["h2_n"]), "summary.json h2_n")]
    return _finish(fig, "s1_h2_next_contract", out_dir, rows, data["rd"], "fig_s1.csv", keep)


def card_h3(data: dict, out_dir: Path, *, keep: bool = False):
    """H3: standard margin over PM2 capital of the maker books, by book size."""
    s = data["summary"]
    stat, lo, hi = (float(s[k]) for k in ("h3_stat", "h3_lo", "h3_hi"))
    f = f"{stat:.1f}"
    title = f"PM2 cuts the capital of real maker books\nby a factor of {f} against standard margin"
    take = [f"Median of SM ÷ PM2 capital over {thousands(s['h3_n'])} maker-days, {s['h3_n_accounts']} accounts, "
            f"{month(s['h3_first_day'])} to {month(s['h3_last_day'])};",
            f"90 % interval {lo:.2f} to {hi:.2f}; above 63 options "
            f"({pct(s['h3_share_days_over_63_options'], 0)} of days) SM is counterfactual."]
    fig = _card(title, take)
    ax = _axes(fig, [0.12, 0.33, 0.83, 0.40])
    b = data["f4a"][data["f4a"]["kind"] == "bin"]
    ax.fill_between(b["centre"], b["p25"], b["p75"], color="#CCCCCC", lw=0, label="middle half of the days")
    ax.plot(b["centre"], b["median"], color=INK, marker="o", ms=9, lw=3.0, label="median per book size")
    ax.axhline(stat, color=PM2, ls="--", lw=3.0)
    ax.text(1.15, stat / 1.1, f"all {thousands(s['h3_n'])} maker-days: {f}×", color=PM2, fontsize=18,
            fontweight="bold", va="top", ha="left")
    ax.axvline(63.5, color=MUTED, lw=1.5)
    ax.text(70, 0.5, "SM account\nlimit: 63 options", color=MUTED, fontsize=14, va="bottom", ha="left")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, 520)
    ax.set_ylim(0.4, 16)
    ax.set_xticks([1, 4, 16, 64, 256])
    ax.set_xticklabels(["1", "4", "16", "64", "256"])
    ax.set_yticks([0.5, 1, 2, 4, 8, 16])
    ax.set_yticklabels(["0.5×", "1×", "2×", "4×", "8×", "16×"])
    ax.minorticks_off()
    ax.set_xlabel("option legs in the maker's book (log)")
    ax.set_ylabel("SM ÷ PM2 capital")
    ax.legend(loc="upper left", fontsize=14, handlelength=1.6)
    rows = [("stat", stat, f"{f}×", "summary.json h3_stat"), ("lo", lo, f"{lo:.2f}", "summary.json h3_lo"),
            ("hi", hi, f"{hi:.2f}", "summary.json h3_hi"), ("n", s["h3_n"], thousands(s["h3_n"]), "summary.json h3_n"),
            ("share_over_63", s["h3_share_days_over_63_options"], pct(s["h3_share_days_over_63_options"], 0),
             "summary.json h3_share_days_over_63_options")]
    return _finish(fig, "s2_h3_netting", out_dir, rows, data["rd"], "fig_s2.csv", keep)


def card_h1(data: dict, out_dir: Path, *, keep: bool = False):
    """H1: rank of the cells by edge per notional against rank by edge per unit of PM2 capital."""
    s = data["summary"]
    stat, lo, hi = (float(s[k]) for k in ("h1_stat", "h1_lo", "h1_hi"))
    r = f"{stat:.2f}"
    title = f"Measured per unit of capital, the map of\nwhere makers earn stays the same: ρ = {r}"
    take = [f"Spearman's ρ, {s['h1_n_cells']} delta × tenor cells (BTC, ETH, HYPE), edge per notional against",
            f"edge per PM2 capital, {month(s['h1_first_day'])} to {month(s['h1_last_day'])}; "
            f"90 % interval {lo:.2f} to {hi:.2f}."]
    fig = _card(title, take)
    ax = _axes(fig, [0.22, 0.32, 0.27, 0.47])
    b = data["f2b"]
    n = int(len(b))
    sell, buy = b[b["side"] == "sell"], b[b["side"] == "buy"]
    ax.plot([1, n], [1, n], color=MUTED, ls="--", lw=1.5)
    ax.plot(sell["rank_A"], sell["rank_B"], ls="none", marker="v", ms=7, color=INK, label="maker sells")
    ax.plot(buy["rank_A"], buy["rank_B"], ls="none", marker="^", ms=7, mfc="white", mec=INK, mew=1.3,
            label="maker buys")
    ax.set_xlim(n + 5, -4)
    ax.set_ylim(n + 5, -4)
    ax.set_xticks([1, 50, 100, 150])
    ax.set_yticks([1, 50, 100, 150])
    ax.set_xlabel("rank by edge per notional")
    ax.set_ylabel("rank by edge per capital")
    fig.legend(*ax.get_legend_handles_labels(), loc="upper left", bbox_to_anchor=(0.56, 0.47), fontsize=15,
               handletextpad=0.3, frameon=False)
    fig.text(0.565, 0.66, f"ρ = {r}", fontsize=30, fontweight="bold", va="center")
    fig.text(0.565, 0.555, f"{s['h1_n_cells']} cells, 1 = highest edge;\ndashed: same rank in both", fontsize=15,
             va="center", color=MUTED)
    rows = [("stat", stat, r, "summary.json h1_stat"), ("lo", lo, f"{lo:.2f}", "summary.json h1_lo"),
            ("hi", hi, f"{hi:.2f}", "summary.json h1_hi"),
            ("n_cells", s["h1_n_cells"], str(s["h1_n_cells"]), "summary.json h1_n_cells"),
            ("points", n, str(n), "fig_f2_b.csv rows")]
    return _finish(fig, "s3_h1_map", out_dir, rows, data["rd"], "fig_s3.csv", keep)


def _finish(fig, name: str, out_dir: Path, rows, results_dir: Path, table: str, keep: bool):
    _table(rows, results_dir, table)
    path = _save(fig, name, out_dir)
    if keep:
        return fig, path
    plt.close(fig)
    return path


CARDS: Dict[str, Callable] = {"s1": card_h2, "s2": card_h3, "s3": card_h1}


def build(results_dir: Path = RESULTS, out_dir: Path = OUT, only: Optional[Sequence[str]] = None) -> List[Path]:
    data = load(results_dir)
    names = list(CARDS) if only is None else list(only)
    return [CARDS[n](data, Path(out_dir)) for n in names]
