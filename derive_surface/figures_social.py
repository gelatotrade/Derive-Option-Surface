"""Cards for social media: the same numbers as the paper, drawn to be read on a phone.

The manuscript figures are built for a 3.4 inch print column at 8 pt and are unreadable on a screen the
size of a hand.  These are the same results at 1600 by 900 with type three times the size, one idea per
card, and the takeaway written into the picture because a post has no caption underneath it.
"""
from __future__ import annotations

from pathlib import Path
import textwrap
from typing import Dict, List, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from . import figdata, figstyle  # noqa: E402
from .figures_p1 import load_inputs, minus  # noqa: E402
from .markouts import DELTA_LABELS, TENOR_LABELS  # noqa: E402

WIDTH, HEIGHT, DPI = 10.0, 5.625, 160          # 1600 x 900
INK = "#111111"
MUTED = "#6b6b6b"
RC = {
    "font.size": 16.0,
    "axes.titlesize": 21.0,
    "axes.labelsize": 16.0,
    "xtick.labelsize": 14.0,
    "ytick.labelsize": 14.0,
    "legend.fontsize": 14.0,
    "legend.frameon": False,
    "axes.grid": True,
    "grid.alpha": 0.18,
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
    "axes.linewidth": 1.0,
    "axes.edgecolor": INK,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "lines.linewidth": 2.4,
    "figure.dpi": DPI,
    "savefig.dpi": DPI,
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
    # the print style sets a tight bounding box; a card must keep its exact 1600 x 900 frame, so every
    # setting that can change the output size is pinned here rather than inherited
    "savefig.bbox": None,
    "savefig.pad_inches": 0.0,
    "figure.autolayout": False,
}


def _card(title: str, takeaway: str):
    """A card with room for a two-line takeaway; the line is wrapped so it can never leave the image."""
    matplotlib.rcParams.update(RC)
    fig = plt.figure(figsize=(WIDTH, HEIGHT))
    fig.text(0.035, 0.955, title, fontsize=25, fontweight="bold", va="top")
    fig.text(0.035, 0.115, "\n".join(textwrap.wrap(takeaway, 82)[:3]), fontsize=14, color=MUTED, va="top")
    return fig


def _axes(fig, rect=(0.125, 0.29, 0.845, 0.545)):
    ax = fig.add_axes(rect)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return ax


def _save(fig, name: str, out_dir: Path) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "{}.png".format(name)
    fig.savefig(path)
    plt.close(fig)
    return [path]


def card_s1(inputs: dict, out_dir: Path) -> List[Path]:
    """Where the maker's edge goes."""
    frame = inputs["frame"]
    steps = figdata.waterfall_components(frame)
    values = dict(zip(steps["step"], steps["value"]))
    order = ["half spread", "adverse selection", "maker fee", "maker rebate", "hedge cost", "net edge"]
    labels = ["half\nspread", "adverse\nselection", "maker\nfee", "maker\nrebate", "hedge\ncost", "NET\nEDGE"]

    fig = _card("Where an options maker's edge goes",
                "Mean per contract, 603,940 Derive fills, BTC / ETH / HYPE, Jan 2024 to Sep 2026.")
    ax = _axes(fig)
    running = 0.0
    for i, (key, label) in enumerate(zip(order, labels)):
        v = float(values[key])
        total = key == "net edge"
        bottom = 0.0 if total else running
        color = INK if total else (figstyle.PALETTE[0] if v >= 0 else figstyle.PALETTE[1])
        ax.bar(i, v, bottom=bottom, color=color, width=0.66)
        top = bottom + v
        ax.text(i, max(top, bottom) + 0.6, minus("{:+.2f}".format(v)), ha="center", fontsize=16, fontweight="bold")
        if not total:
            running += v
    ax.axhline(0, color=INK, lw=1.2)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_ylabel("USDC per contract")
    ax.set_ylim(0, max(values.values()) * 1.22)
    return _save(fig, "s1_decomposition", out_dir)


def card_s2(inputs: dict, out_dir: Path) -> List[Path]:
    """The counterparty decides the sign."""
    classes = inputs["results"]["classes"].copy()
    classes = classes.sort_values("mean")
    names = {"other": "everyone else", "rfq": "RFQ flow", "vault": "vaults", "large": "large wallets",
             "mm_programme": "MM programme", "dominant_maker": "dominant makers"}

    fig = _card("Same options. Opposite outcome.",
                "Mean 30-minute markout per contract, by who took the other side. "
                "Wallet counts in brackets.")
    ax = _axes(fig, (0.27, 0.29, 0.70, 0.545))
    pos = np.arange(len(classes))
    colors = [figstyle.PALETTE[1] if v < 0 else figstyle.PALETTE[0] for v in classes["mean"]]
    ax.barh(pos, classes["mean"], color=colors, height=0.62)
    ax.set_yticks(pos)
    ax.set_yticklabels(["{}  ({})".format(names.get(c, c), int(g))
                        for c, g in zip(classes["class"], classes["clusters"])])
    for i, v in enumerate(classes["mean"]):
        ax.text(v + (1.2 if v >= 0 else -1.2), i, minus("{:+.1f}".format(v)), va="center",
                ha="left" if v >= 0 else "right", fontsize=16, fontweight="bold")
    ax.axvline(0, color=INK, lw=1.2)
    ax.set_xlabel("USDC per contract")
    span = float(classes["mean"].abs().max())
    ax.set_xlim(-span * 1.35, span * 1.35)
    return _save(fig, "s2_counterparty", out_dir)


def card_s3(inputs: dict, out_dir: Path) -> List[Path]:
    """Concentration."""
    lorenz = inputs["results"]["lorenz"]
    h1 = inputs["results"]["summary"]["H1"]["top10_share"]
    share, loss = lorenz["wallet_share"].to_numpy(float), lorenz["loss_share"].to_numpy(float)

    fig = _card("Ten wallets take 90% of it",
                "Cumulative share of the maker's aggregate loss, by loss-making taker wallet. "
                "One address alone carries 39%.")
    ax = _axes(fig)
    ax.plot(share, loss, color=figstyle.PALETTE[0])
    ax.set_xscale("log")
    top_x = 10.0 / max(len(lorenz), 1)
    ax.plot([top_x], [float(h1["share"])], "o", color=figstyle.PALETTE[1], ms=14)
    ax.annotate("top 10 wallets\n{:.1f}% of the loss".format(100 * float(h1["share"])),
                xy=(top_x, float(h1["share"])), xytext=(0.30, 0.34), textcoords="axes fraction",
                fontsize=17, fontweight="bold",
                arrowprops=dict(arrowstyle="->", lw=1.6, color=INK))
    ax.set_ylim(0, 1.04)
    ax.set_xlim(max(top_x / 25, 1e-4), 1.0)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("share of loss-making taker wallets, log scale")
    ax.set_ylabel("share of the loss")
    return _save(fig, "s3_concentration", out_dir)


def card_s4(inputs: dict, out_dir: Path) -> List[Path]:
    """The proxies fail."""
    frame, h1 = inputs["frame"], inputs["results"]["summary"]["H1"]
    raw_size = float(frame.loc[frame["size_above_p90"], "y_dn"].mean()
                     - frame.loc[~frame["size_above_p90"], "y_dn"].mean())
    raw_sweep = float(frame.loc[frame["is_sweep"], "y_dn"].mean() - frame.loc[~frame["is_sweep"], "y_dn"].mean())
    rows = [("big trades", raw_size, float(h1["size_coefficient"]["beta"]), float(h1["size_coefficient"]["t"])),
            ("sweeps", raw_sweep, float(h1["sweep_coefficient"]["beta"]), float(h1["sweep_coefficient"]["t"]))]

    fig = _card("Big orders aren't the problem",
                "Difference in the maker's result. Hollow: raw comparison. Solid: same instrument, same day. "
                "Neither coefficient is distinguishable from zero.")
    ax = _axes(fig, (0.19, 0.31, 0.78, 0.50))
    for i, (name, raw, ctrl, t) in enumerate(rows):
        ax.plot([raw, ctrl], [i, i], color=MUTED, lw=2.0)
        ax.plot([raw], [i], "o", mfc="white", mec=figstyle.PALETTE[1], mew=2.6, ms=15)
        ax.plot([ctrl], [i], "o", color=figstyle.PALETTE[0], ms=15)
        ax.annotate(minus("t = {:.2f}".format(t)), xy=(ctrl, i), xytext=(0, 16), textcoords="offset points",
                    ha="center", fontsize=15, fontweight="bold", zorder=4,
                    bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"))     # over the zero line
    ax.axvline(0, color=INK, lw=1.2)
    span = max(abs(r[1]) for r in rows)
    ax.set_xlim(-span * 1.12, span * 0.16)          # room to the right of zero for the t labels
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_ylim(-0.6, len(rows) - 0.25)
    ax.set_xlabel("difference in markout, USDC per contract")
    ax.legend(handles=[Line2D([], [], marker="o", mfc="white", mec=figstyle.PALETTE[1], mew=2.6, ls="none",
                              label="raw"),
                       Line2D([], [], marker="o", color=figstyle.PALETTE[0], ls="none",
                              label="controlled")], loc="upper left")
    return _save(fig, "s4_proxies", out_dir)


def s5_takeaway(grids: Dict[str, pd.DataFrame]) -> str:
    """The sentence under the S5 title, with the median over the occupied cells of each panel.

    The first card stated a ranking in words; that ranking came from a unit error (net edge per contract
    over the notional of the whole fill), so the takeaway now carries the numbers of the map it sits on.
    """
    medians = []
    for ccy, values in grids.items():
        finite = values.to_numpy(float)
        finite = finite[np.isfinite(finite)]
        if finite.size:
            medians.append("{} {:.1f}".format(ccy, float(np.median(finite))))
    return ("Median net edge in basis points of notional, one shared colour scale. Rows are the absolute "
            "delta, columns the tenor. Median over the cells: {} bp.".format(", ".join(medians)))


def card_s5(inputs: dict, out_dir: Path) -> List[Path]:
    """Where a maker is actually paid."""
    frame = inputs["frame"]
    bp = frame.assign(bp=figdata.edge_bp(frame))               # edge of the fill over its notional
    currencies = [c for c in ("BTC", "ETH", "HYPE") if (bp["currency"] == c).any()]

    grids = {}
    for ccy in currencies:
        values, _ = figdata.cell_matrix(bp[bp["currency"] == ccy], "bp", stat="median")
        grids[ccy] = values
    fig = _card("Where a maker actually gets paid", s5_takeaway(grids))
    everything = np.concatenate([g.to_numpy(float).ravel() for g in grids.values()])
    everything = everything[np.isfinite(everything)]
    # one scale for all three panels: a per-panel scale would make the cheapest underlying look the hottest
    vmin, vmax = 0.0, float(np.nanpercentile(everything, 97)) if everything.size else 1.0
    for k, ccy in enumerate(currencies):
        values = grids[ccy]
        grid = values.to_numpy(float).T
        span = 0.88 / max(len(currencies), 1)
        left = 0.085 + k * span
        ax = fig.add_axes([left, 0.30, span - 0.05, 0.48])
        ax.imshow(grid, cmap="Blues", aspect="auto", vmin=vmin, vmax=vmax)
        cut = vmin + 0.55 * (vmax - vmin)
        for i in range(grid.shape[0]):
            for j in range(grid.shape[1]):
                v = grid[i, j]
                if np.isfinite(v):
                    ax.text(j, i, minus("{:.0f}".format(v) if abs(v) >= 10 else "{:.1f}".format(v)),
                            ha="center", va="center", fontsize=12,
                            color="white" if v > cut else INK)
        ax.set_xticks(range(grid.shape[1]))
        ax.set_xticklabels(values.index, rotation=45, ha="right", fontsize=11)
        ax.set_yticks(range(grid.shape[0]))
        ax.set_yticklabels(values.columns if k == 0 else [], fontsize=11)
        ax.set_title(ccy, fontsize=19, fontweight="bold")
        ax.grid(False)
    return _save(fig, "s5_map", out_dir)


CARDS = {"S1": card_s1, "S2": card_s2, "S3": card_s3, "S4": card_s4, "S5": card_s5}


def build(root, results_dir, out_dir, only: Sequence[str] = None) -> Dict[str, List[Path]]:
    names = list(CARDS) if only is None else [n.strip() for n in only]
    unknown = [n for n in names if n not in CARDS]
    if unknown:
        raise KeyError("unknown card(s): {}".format(", ".join(unknown)))
    data = load_inputs(root, results_dir)
    return {name: CARDS[name](data, Path(out_dir)) for name in names}
