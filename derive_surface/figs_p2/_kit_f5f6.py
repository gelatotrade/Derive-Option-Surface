"""Shared helpers of the Paper 2 figures F5 and F6 (ABBILDUNGSWAHL section 6).

Canvas = print size (no ``bbox tight``), no text under ``FS_MIN``, manager colours and line styles from section 6.2,
axes placed in inches from the top left corner, and a small runner for the check lists (``CHECKS``) of the slots.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, List, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.text  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .. import figstyle  # noqa: E402

FS_MIN = 7.0
FS_LETTER = 8.0
GREY = "#666666"
LIGHT = "#F0F0F0"
MINUS = "−"
THIN = " "
MANAGER = {"pm2": ("#0072B2", "-", "o"), "sm": ("#D55E00", "--", "s"), "pm": ("#009E73", ":", "D")}
MANAGER_LABEL = {"pm2": "PM2", "sm": "SM", "pm": "legacy PM"}

RC = dict(figstyle.RC)
RC.update({"font.size": FS_MIN, "axes.titlesize": FS_MIN, "axes.labelsize": FS_MIN, "xtick.labelsize": FS_MIN,
           "ytick.labelsize": FS_MIN, "legend.fontsize": FS_MIN, "axes.grid": False, "savefig.bbox": None,
           "savefig.pad_inches": 0.0, "savefig.dpi": 400, "xtick.color": "black", "ytick.color": "black",
           "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.major.pad": 2.0, "ytick.major.pad": 2.0,
           "axes.labelpad": 2.0, "hatch.linewidth": 0.5})


def new_figure(width: float, height: float):
    """Empty figure at print size in the P2 style."""
    matplotlib.rcParams.update(RC)
    return plt.figure(figsize=(width, height))


def axes_at(fig, left: float, top: float, width: float, height: float, **kw):
    """Axes placed in inches, ``top`` measured from the upper edge of the canvas; top and right spines off."""
    W, H = fig.get_size_inches()
    ax = fig.add_axes([left / W, 1.0 - (top + height) / H, width / W, height / H], **kw)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return ax


def fig_text(fig, x: float, y: float, text: str, **kw):
    """Text at (x, y) inches from the upper left corner."""
    W, H = fig.get_size_inches()
    kw.setdefault("fontsize", FS_MIN)
    kw.setdefault("va", "top")
    return fig.text(x / W, 1.0 - y / H, text, **kw)


def letter(fig, x: float, y: float, s: str):
    """Panel letter, 8 pt bold, top left at (x, y) inches."""
    return fig_text(fig, x, y, s, fontsize=FS_LETTER, fontweight="bold", ha="left")


def save(fig, name: str, out_dir: Path) -> List[Path]:
    """``name.pdf`` and ``name.png`` (400 dpi) at print size (``_print.to_print``: the width main.tex sets)."""
    from ._print import to_print

    to_print(fig)
    with matplotlib.rc_context({"savefig.bbox": None, "savefig.pad_inches": 0.0, "savefig.dpi": 400}):
        return figstyle.save(fig, name, Path(out_dir))


def write_csv(frame: pd.DataFrame, results_dir: Path, name: str) -> Path:
    path = Path(results_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


# ------------------------------------------------------------------------------------------------ number formats

def signed_int(x: float, zero_below: float = 0.5) -> str:
    """Whole number with sign and a true minus; ``|x| < zero_below`` prints as ``0``."""
    if not np.isfinite(x):
        return ""
    if abs(x) < zero_below:
        return "0"
    v = int(round(x))
    return f"+{v}" if v > 0 else f"{MINUS}{abs(v)}"


def num(x: float, digits: int = 2) -> str:
    """Fixed decimals with a true minus sign."""
    s = f"{x:.{digits}f}"
    return s.replace("-", MINUS)


def thousands(n: float) -> str:
    """Integer with a thin space as thousands separator (91 446)."""
    return f"{int(round(n)):,}".replace(",", THIN)


def pct(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}{THIN}%"


# ------------------------------------------------------------------------------------------------ layout checks

def texts(fig) -> List[matplotlib.text.Text]:
    """Non-empty text artists that are actually drawn (recorded during a draw, so tick labels outside the view
    limits and annotations whose anchor is clipped are left out)."""
    drawn: List[matplotlib.text.Text] = []
    original = matplotlib.text.Text.draw

    def record(self, renderer):
        if self.get_visible() and self.get_text().strip() and self not in drawn:
            drawn.append(self)
        return original(self, renderer)

    matplotlib.text.Text.draw = record
    try:
        fig.canvas.draw()
    finally:
        matplotlib.text.Text.draw = original
    r = fig.canvas.get_renderer()
    return [t for t in drawn if t.get_window_extent(r).width > 0]


def small_texts(fig, fs_min: float = FS_MIN) -> List[str]:
    return [f"{t.get_text()!r} {t.get_fontsize():.2f}" for t in texts(fig) if t.get_fontsize() < fs_min - 1e-9]


def texts_off_canvas(fig, tol_px: float = 0.5) -> List[str]:
    r = fig.canvas.get_renderer()
    bb = fig.bbox
    out = []
    for t in texts(fig):
        e = t.get_window_extent(r)
        if e.x0 < bb.x0 - tol_px or e.y0 < bb.y0 - tol_px or e.x1 > bb.x1 + tol_px or e.y1 > bb.y1 + tol_px:
            out.append(t.get_text())
    return out


def overlapping_texts(fig, pad_px: float = 0.0) -> List[tuple]:
    """Pairs of text artists whose drawn boxes intersect (tick labels of one axis with each other included)."""
    r = fig.canvas.get_renderer()
    ts = texts(fig)
    boxes = [t.get_window_extent(r) for t in ts]
    out = []
    for i in range(len(ts)):
        for j in range(i + 1, len(ts)):
            a, b = boxes[i], boxes[j]
            if (a.x0 < b.x1 - pad_px and b.x0 < a.x1 - pad_px and a.y0 < b.y1 - pad_px and b.y0 < a.y1 - pad_px):
                out.append((ts[i].get_text(), ts[j].get_text()))
    return out


# ------------------------------------------------------------------------------------------------ checks

def _close(a, b, rel: float, abs_: float) -> bool:
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        return set(a) == set(b) and all(_close(a[k], b[k], rel, abs_) for k in a)
    if isinstance(a, (list, tuple, np.ndarray, pd.Series)) and isinstance(b, (list, tuple, np.ndarray, pd.Series)):
        a, b = list(a), list(b)
        return len(a) == len(b) and all(_close(x, y, rel, abs_) for x, y in zip(a, b))
    if isinstance(a, (bool, np.bool_)) or isinstance(b, (bool, np.bool_)):
        return bool(a) == bool(b)
    if isinstance(a, str) or isinstance(b, str):
        return str(a) == str(b)
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return a == b
    if math.isnan(fa) or math.isnan(fb):
        return math.isnan(fa) and math.isnan(fb)
    return abs(fa - fb) <= max(abs_, rel * max(abs(fa), abs(fb)))


def check(id: str, what: str, figure: Callable[[Path], object], source: Callable[[Path], object],
          expected=None, rel: float = 1e-9, abs_: float = 0.0, expected_tol: float = 0.0) -> dict:
    """One check: ``figure(results_dir)`` reads what the figure prints (its ``fig_*.csv``), ``source(results_dir)``
    reads the registered or input file. ``expected`` is the number of the build instruction (real data only), compared
    with the figure value within ``expected_tol`` (absolute)."""
    return {"id": id, "what": what, "figure": figure, "source": source, "expected": expected, "rel": rel,
            "abs": abs_, "expected_tol": expected_tol}


def run_checks(checks: Sequence[Mapping], results_dir: Path, with_expected: bool = True) -> pd.DataFrame:
    """Evaluate a check list; ``agrees`` is figure == source, ``matches_instruction`` figure == expected."""
    rows = []
    for c in checks:
        try:
            got = c["figure"](Path(results_dir))
            src = c["source"](Path(results_dir))
            ok = _close(got, src, c["rel"], c["abs"])
            err = ""
        except Exception as exc:  # noqa: BLE001
            got = src = None
            ok = False
            err = repr(exc)[:200]
        exp = c.get("expected")
        if with_expected and exp is not None and got is not None:
            match = _close(got, exp, 0.0, c.get("expected_tol", 0.0))
        else:
            match = None
        rows.append({"id": c["id"], "what": c["what"], "figure": got, "source": src, "agrees": ok,
                     "expected": exp, "matches_instruction": match, "error": err})
    return pd.DataFrame(rows)
