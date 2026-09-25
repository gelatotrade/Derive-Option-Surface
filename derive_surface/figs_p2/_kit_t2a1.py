"""Shared helpers of the Paper 2 figures T2 and A1 (ABBILDUNGSWAHL section 6).

Canvas = print size (no ``bbox tight``, no padding), no text under ``FS_MIN``, manager colours, line styles and
markers from section 6.2 (read from ``figstyle`` once it carries them), axes placed in inches from the top left corner,
a grey copy for the greyscale test, and the runner for the check lists (``CHECKS``) of the two slots.
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

FS_MIN = float(getattr(figstyle, "FS_MIN", 7.0))
FS_LETTER = 8.0
GREY = "#666666"
MINUS = "−"
THIN = " "
MANAGER = dict(getattr(figstyle, "MANAGER", {"pm2": ("#0072B2", "-", "o"), "sm": ("#D55E00", "--", "s"),
                                              "pm": ("#009E73", ":", "D")}))
MANAGER_LABEL = {"pm2": "PM2", "sm": "SM", "pm": "legacy PM"}
DASHDOT_PM2_LEGS = (0, (3, 1, 1, 1))   # reserved for "PM2, legs one by one" (T2 c)

RC = dict(figstyle.RC)
RC.update({"font.size": FS_MIN, "axes.titlesize": 8.0, "axes.labelsize": FS_MIN, "xtick.labelsize": FS_MIN,
           "ytick.labelsize": FS_MIN, "legend.fontsize": FS_MIN, "axes.grid": False, "savefig.bbox": None,
           "savefig.pad_inches": 0.0, "savefig.dpi": 400, "xtick.color": "black", "ytick.color": "black",
           "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
           "xtick.major.pad": 2.0, "ytick.major.pad": 2.0, "axes.labelpad": 2.0, "hatch.linewidth": 0.5,
           "hatch.color": GREY, "axes.unicode_minus": True})


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
    """``name.pdf`` and ``name.png`` (400 dpi) at print size, plus the luminance copy ``gray/name.png``."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    with matplotlib.rc_context({"savefig.bbox": None, "savefig.pad_inches": 0.0, "savefig.dpi": 400}):
        for suffix in (".pdf", ".png"):
            path = out_dir / f"{name}{suffix}"
            fig.savefig(path)
            paths.append(path)
    plt.close(fig)
    gray = out_dir / "gray" / f"{name}.png"
    gray.parent.mkdir(parents=True, exist_ok=True)
    img = plt.imread(paths[1])
    lum = 0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]
    plt.imsave(gray, lum, cmap="gray", vmin=0.0, vmax=1.0)
    paths.append(gray)
    return paths


def write_csv(frame: pd.DataFrame, results_dir: Path, name: str) -> Path:
    path = Path(results_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format="%.12g")
    return path


def sci(x: float) -> str:
    """Tick label of a power of ten with a true minus: 1e-11 -> '1e−11'."""
    e = int(round(math.log10(x)))
    return f"1e{MINUS}{abs(e)}" if e < 0 else f"1e{e}"


# ------------------------------------------------------------------------------------------------ layout checks

def texts(fig) -> List[matplotlib.text.Text]:
    """Visible, non-empty text artists that are drawn on the canvas."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    out = []
    for t in fig.findobj(matplotlib.text.Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        try:
            e = t.get_window_extent(r)
        except Exception:  # noqa: BLE001
            continue
        if e.width > 0 and e.height > 0:
            out.append(t)
    return out


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
    """Pairs of text artists whose drawn boxes intersect."""
    r = fig.canvas.get_renderer()
    ts = texts(fig)
    boxes = [t.get_window_extent(r) for t in ts]
    out = []
    for i in range(len(ts)):
        for j in range(i + 1, len(ts)):
            a, b = boxes[i], boxes[j]
            if a.x0 < b.x1 - pad_px and b.x0 < a.x1 - pad_px and a.y0 < b.y1 - pad_px and b.y0 < a.y1 - pad_px:
                out.append((ts[i].get_text(), ts[j].get_text()))
    return out


def pdf_size_inches(path: Path) -> tuple:
    """Width and height of the first MediaBox of a PDF, in inches."""
    import re

    raw = Path(path).read_bytes()
    m = re.search(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", raw)
    if m is None:
        raise ValueError(f"no MediaBox in {path}")
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    return (x1 - x0) / 72.0, (y1 - y0) / 72.0


# ------------------------------------------------------------------------------------------------ checks

def _close(a, b, rel: float, abs_: float) -> bool:
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
    reads the input file in ``results/p2`` (never the figure table). ``expected`` is the number of the build
    instruction (real data only), compared with the figure value within ``expected_tol`` (absolute)."""
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
        match = _close(got, exp, 0.0, c.get("expected_tol", 0.0)) if with_expected and exp is not None \
            and got is not None else None
        rows.append({"id": c["id"], "what": c["what"], "figure": got, "source": src, "agrees": ok,
                     "expected": exp, "matches_instruction": match, "error": err})
    return pd.DataFrame(rows)
