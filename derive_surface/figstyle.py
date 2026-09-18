"""Figure style for the paper: Elsevier CAS two-column layout, print-safe colours, PDF plus PNG.

Widths are the CAS text widths (3.4 in for one column, 7.0 in for the full width) so that figures go into
the manuscript at scale 1 and keep their 8 pt type.  Colours are the Okabe-Ito palette, which stays
distinguishable for the common colour vision deficiencies and separates in grayscale; the counterparty
classes get fixed colours so that every figure of the paper uses the same one for the same class.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SINGLE = 3.4
DOUBLE = 7.0
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442", "#000000"]
GREY = "#666666"
CLASS_COLORS = {
    "other": "#0072B2",
    "rfq": "#009E73",
    "vault": "#E69F00",
    "large": "#56B4E9",
    "mm_programme": "#CC79A7",
    "dominant_maker": "#D55E00",
}
CLASS_LABELS = {
    "other": "other takers",
    "rfq": "RFQ",
    "vault": "vault",
    "large": "large wallet",
    "mm_programme": "MM programme",
    "dominant_maker": "dominant maker",
}
CLASS_ORDER = ["other", "rfq", "vault", "large", "mm_programme", "dominant_maker"]

RC = {
    "font.size": 8.0,
    "axes.titlesize": 8.0,
    "axes.labelsize": 8.0,
    "xtick.labelsize": 7.0,
    "ytick.labelsize": 7.0,
    "legend.fontsize": 7.0,
    "legend.frameon": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.4,
    "axes.axisbelow": True,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "lines.linewidth": 1.2,
    "figure.dpi": 150,
    "savefig.dpi": 400,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}


def use_style() -> None:
    matplotlib.rcParams.update(RC)


def figure(width: float = SINGLE, height: float = 2.4, **kwargs):
    """A styled figure with one axis (or a grid when ``nrows``/``ncols`` are given)."""
    use_style()
    fig, axes = plt.subplots(figsize=(width, height), **kwargs)
    for ax in np.atleast_1d(np.asarray(axes)).ravel():
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    return fig, axes


def save(fig, name: str, out_dir: Path) -> List[Path]:
    """Write ``name.pdf`` (for the manuscript) and ``name.png`` (for quick looks)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for suffix in (".pdf", ".png"):
        path = out_dir / f"{name}{suffix}"
        fig.savefig(path)
        paths.append(path)
    plt.close(fig)
    return paths


def robust_limits(values: Iterable[float], q: float = 0.99, pad: float = 0.05) -> Tuple[float, float]:
    """Axis limits from the central quantile range, so that a few huge fills do not flatten the picture."""
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return 0.0, 1.0
    lo, hi = float(np.quantile(arr, 1 - q)), float(np.quantile(arr, q))
    if hi <= lo:
        lo, hi = lo - 1.0, hi + 1.0
    span = hi - lo
    return lo - pad * span, hi + pad * span


def money(x: float, _pos: int = 0) -> str:
    """USDC label: thousands separator for large numbers, two decimals below ten."""
    if not np.isfinite(x):
        return ""
    if abs(x) >= 10:
        return f"{x:,.0f}"
    return f"{x:.2f}"


def vol(x: float, _pos: int = 0) -> str:
    """Vol-point label."""
    return "" if not np.isfinite(x) else f"{x:.1f}"


def class_bars(ax, classes: Sequence[str], values: Sequence[float], horizontal: bool = True, **kwargs):
    """Bars in the fixed class colours and the fixed order."""
    colors = [CLASS_COLORS.get(c, GREY) for c in classes]
    labels = [CLASS_LABELS.get(c, c) for c in classes]
    if horizontal:
        bars = ax.barh(range(len(values)), values, color=colors, **kwargs)
        ax.set_yticks(range(len(values)))
        ax.set_yticklabels(labels)
    else:
        bars = ax.bar(range(len(values)), values, color=colors, **kwargs)
        ax.set_xticks(range(len(values)))
        ax.set_xticklabels(labels, rotation=30, ha="right")
    return bars
