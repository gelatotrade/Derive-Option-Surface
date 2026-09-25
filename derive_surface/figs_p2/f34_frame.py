"""The frame that F3 (H2) and F4 (H3) share: one column, 3.4 x 4.0 in, and the verdict forest.

Both figures stand side by side at the top of a page, so they have the same canvas, the same header block, the
same axes boxes and the same forest grammatics (ABBILDUNGSWAHL.md, 6.5): the bold verdict line is rebuilt from the
registered rule and bounds and must agree with ``rejected`` in the result file, otherwise the build stops.

Layout from the top: three header lines (verdict, then the sample in two lines), a zone of two text lines above
panel a, panel a, its axis labels, panel b (the forest) and its axis labels.  The axes of a and b have the same
left and right edges, so F3 can put both panels on one x-axis.  Nothing is saved with a tight box: the canvas is
the printed size.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import transforms  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from matplotlib.textpath import TextToPath  # noqa: E402
from PIL import Image  # noqa: E402

from .. import figstyle  # noqa: E402

FS_MIN = float(getattr(figstyle, "FS_MIN", 7.0))
FS = 7.0                     # every text in these two figures except axis titles and panel letters
FS_LABEL = 8.0
W, H = figstyle.SINGLE, 4.0
DPI = 400
GREY = "#666666"             # n column, exploratory rows, counts
LIGHT = "#F0F0F0"            # band behind exploratory rows
HATCH = "#BBBBBB"            # registered rejection region
RULE_GREY = "#808080"
ARROW = 4.0                  # arrow head of an interval that leaves the axis, points

RC = dict(figstyle.RC)
RC.update({"savefig.bbox": None, "savefig.pad_inches": 0.0, "savefig.dpi": DPI, "axes.grid": False,
           "font.size": FS_LABEL, "axes.labelsize": FS_LABEL, "xtick.labelsize": FS, "ytick.labelsize": FS,
           "xtick.color": "black", "ytick.color": "black", "hatch.linewidth": 0.5, "axes.unicode_minus": True,
           "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.major.pad": 2.0, "ytick.major.pad": 2.0,
           "axes.labelpad": 2.5})

# ---------------------------------------------------------------------------------------------- layout, inches
PAD = 0.03
AX_LEFT, AX_RIGHT = 1.075, 2.99         # common left and right edge: widest row label, widest n (19 999)
N_RIGHT = W - PAD                        # right edge of the n column
HEADER_TOP = H - 0.04
LINE = 0.125                             # pitch of 7 pt lines
HEADER_LINES = 3
ZONE = 0.27                              # two 7 pt lines above panel a (band shares in F3, labels in F4)
A_TOP = HEADER_TOP - HEADER_LINES * LINE - 0.02 - ZONE
A_H = 1.12
B_TOP = A_TOP - A_H - 0.36
B_H = 1.45
TEXT_MAX = W - 2 * PAD                   # widest header line

REGIMES = [("regime=R1", "R1 to 23 Jan"), ("regime=R2", "R2 to 24 May"), ("regime=R3", "R3 to 20 Aug"),
           ("regime=R4", "R4 since 20 Aug")]
LABEL_MAX = 18

_T2P = TextToPath()


# -------------------------------------------------------------------------------------------------- formatting

def fmt_int(n) -> str:
    """19 999, the thin grouping of the paper, with a plain space."""
    return f"{int(round(float(n))):,}".replace(",", " ")


def decimals(stat: float) -> int:
    """At least two decimals and at least two significant digits: 4.75, 0.035."""
    a = abs(float(stat))
    if not np.isfinite(a) or a == 0:
        return 2
    return max(2, 1 - int(math.floor(math.log10(a))))


def fmt_triplet(stat: float, lo: float, hi: float) -> str:
    d = decimals(stat)
    return f"{stat:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]"


def pct(share: float, digits: int = 0) -> str:
    return f"{100.0 * share:.{digits}f} %"


def text_width_in(s: str, size: float = FS, weight: str = "normal") -> float:
    """Printed width of one line of text in inches (same font as the figure)."""
    fp = FontProperties(size=size, weight=weight)
    w, _, _ = _T2P.get_text_width_height_descent(s, fp, ismath=False)
    return w / 72.0


def wrap_parts(parts: Sequence[str], max_in: float = TEXT_MAX, sep: str = " · ") -> List[str]:
    """Join the parts with a middle dot on one line if it fits, else on two lines of balanced width."""
    parts = list(parts)
    one = sep.join(parts)
    if text_width_in(one) <= max_in:
        return [one]
    best = None
    for k in range(1, len(parts)):
        lines = [sep.join(parts[:k]), sep.join(parts[k:])]
        widest = max(text_width_in(x) for x in lines)
        if widest <= max_in and (best is None or widest < best[0]):
            best = (widest, lines)
    if best is None:
        raise ValueError(f"header does not fit the column in two lines: {parts!r}")
    return best[1]


def list_words(words: Sequence[str]) -> str:
    words = list(words)
    if len(words) <= 1:
        return "".join(words)
    return ", ".join(words[:-1]) + " and " + words[-1]


# ------------------------------------------------------------------------------------------------------ verdict

_RULE = re.compile(r"rejected if the (upper|lower) bound\b.*?\bis (>=|<=)\s*([-+]?[0-9]*\.?[0-9]+)")


def verdict(h: dict) -> Tuple[bool, str]:
    """Apply the registered rule to the bounds again; stop if it disagrees with ``h['rejected']``.

    Returns (rejected, side), side = 'right' when the rejection region lies above the threshold (H1, H2) and
    'left' when it lies below (H3)."""
    m = _RULE.search(str(h.get("rule", "")))
    if not m:
        raise ValueError(f"cannot read the registered rule: {h.get('rule')!r}")
    bound, op, num = m.groups()
    thr = float(h["threshold"])
    if not math.isclose(float(num), thr, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError(f"rule threshold {num} differs from threshold {thr}")
    x = float(h["hi"] if bound == "upper" else h["lo"])
    rejected = x >= thr if op == ">=" else x <= thr
    if bool(rejected) != bool(h["rejected"]):
        raise ValueError(f"the rule gives {'rejected' if rejected else 'not rejected'} on the {bound} bound "
                         f"{x!r} against {thr!r}, but the result file says rejected={h['rejected']!r}")
    return bool(rejected), ("right" if op == ">=" else "left")


def verdict_line(h: dict) -> str:
    rejected, _ = verdict(h)
    word = "rejected" if rejected else "not rejected"
    return f"registered: {fmt_triplet(h['stat'], h['lo'], h['hi'])} → {word}"


# ------------------------------------------------------------------------------------------------------- rows

@dataclass
class Row:
    label: str
    kind: str                    # registered | sensitivity | exploratory
    stat: float
    lo: float
    hi: float
    n: float
    source: str
    variant: str = ""
    group: str = ""
    n_days: float = float("nan")


def sens_row(sens: pd.DataFrame, label: str, kind: str, variant: str, group: str, source: str) -> Optional[Row]:
    """One row of a ``sens_*.csv`` table, or None when the inference has not written it."""
    m = sens[(sens["variant"].astype(str) == variant) & (sens["group"].astype(str) == group)]
    if m.empty:
        return None
    if len(m) > 1:
        raise ValueError(f"{source}: {len(m)} rows for {variant}/{group}")
    r = m.iloc[0]
    return Row(label=label, kind=kind, stat=float(r["stat"]), lo=float(r["lo"]), hi=float(r["hi"]),
               n=float(r["n"]), source=source, variant=variant, group=group,
               n_days=float(r["n_days"]) if "n_days" in r else float("nan"))


def regime_rows(sens: pd.DataFrame, variant: str, source: str) -> List[Row]:
    rows = [sens_row(sens, lab, "exploratory", variant, grp, source) for grp, lab in REGIMES]
    return [r for r in rows if r is not None]


# ------------------------------------------------------------------------------------------------------- frame

def _rect(left: float, bottom: float, width: float, height: float) -> List[float]:
    return [left / W, bottom / H, width / W, height / H]


def frame(header: Sequence[str]) -> Tuple[plt.Figure, plt.Axes, plt.Axes]:
    """Canvas, header block, the two axes boxes and the panel letters."""
    if not 1 <= len(header) <= HEADER_LINES:
        raise ValueError(f"header has {len(header)} lines, room for {HEADER_LINES}")
    fig = plt.figure(figsize=(W, H))
    ax_a = fig.add_axes(_rect(AX_LEFT, A_TOP - A_H, AX_RIGHT - AX_LEFT, A_H))
    ax_b = fig.add_axes(_rect(AX_LEFT, B_TOP - B_H, AX_RIGHT - AX_LEFT, B_H))
    for i, line in enumerate(header):
        if text_width_in(line, weight="bold" if i == 0 else "normal") > TEXT_MAX:
            raise ValueError(f"header line too wide for the column: {line!r}")
        fig.text(PAD / W, (HEADER_TOP - i * LINE) / H, line, ha="left", va="top", fontsize=FS,
                 fontweight="bold" if i == 0 else "normal")
    fig.text(PAD / W, (A_TOP + ZONE) / H, "a", ha="left", va="top", fontsize=8.0, fontweight="bold")
    fig.text(PAD / W, (B_TOP + 0.02) / H, "b", ha="left", va="bottom", fontsize=8.0, fontweight="bold")
    for ax in (ax_a, ax_b):
        ax.tick_params(labelsize=FS, colors="black")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    return fig, ax_a, ax_b


def ruler(ax, rows: Sequence[Row], h: dict, *, side: str, xlim: Tuple[float, float], log: bool = False,
          ticks: Optional[Sequence[float]] = None, ticklabels: Optional[Sequence[str]] = None,
          xlabel: str = "", n_title: str = "n") -> Tuple[str, pd.DataFrame]:
    """The verdict forest: registered row first, then sensitivities, then exploratory rows on grey.

    Returns the bold verdict line (rebuilt from the rule) and one table row per drawn row."""
    _, rule_side = verdict(h)
    if side != rule_side:
        raise ValueError(f"side={side!r} but the registered rule rejects on the {rule_side}")
    if not rows or rows[0].kind != "registered":
        raise ValueError("the first row must be the registered one")
    for r in rows:
        if len(r.label) > LABEL_MAX:
            raise ValueError(f"row label longer than {LABEL_MAX} characters: {r.label!r}")
    fig = ax.figure
    thr = float(h["threshold"])
    x0, x1 = xlim
    if log:
        ax.set_xscale("log")
    ax.set_xlim(x0, x1)
    n = len(rows)
    ys = -np.arange(n, dtype=float)
    ax.set_ylim(-n + 0.5, 0.5)
    for y, r in zip(ys, rows):
        if r.kind == "exploratory":
            ax.axhspan(y - 0.5, y + 0.5, color=LIGHT, lw=0, zorder=0)
    hx0, hx1 = (thr, x1) if side == "right" else (x0, thr)
    ax.add_patch(Rectangle((hx0, ys[0] - 0.5), hx1 - hx0, 1.0, facecolor="none", edgecolor=HATCH, hatch="////",
                           lw=0, zorder=0.5))
    ax.axvline(thr, color="black", ls="--", lw=0.8, zorder=1)
    n_tf = transforms.blended_transform_factory(fig.transFigure, ax.transData)
    out = []
    for y, r in zip(ys, rows):
        reg = r.kind == "registered"
        col = GREY if r.kind == "exploratory" else "black"
        lw = 2.0 if reg else 1.0
        lo, hi = r.lo, r.hi
        arrow_lo = bool(np.isfinite(lo) and (lo < x0 or (log and lo <= 0)))
        arrow_hi = bool(np.isfinite(hi) and hi > x1)
        if np.isfinite(lo) and np.isfinite(hi):
            a, b = (x0 if arrow_lo else lo), (x1 if arrow_hi else hi)
            ax.plot([a, b], [y, y], color=col, lw=lw, solid_capstyle="butt", zorder=3, clip_on=False)
            # arrow heads sit inside the axis, their tips on its edge
            if arrow_lo:
                ax.plot([x0], [y], marker="<", ms=ARROW, color=col, mew=0, zorder=3, clip_on=False,
                        transform=transforms.offset_copy(ax.transData, fig, x=ARROW / 2, units="points"))
            if arrow_hi:
                ax.plot([x1], [y], marker=">", ms=ARROW, color=col, mew=0, zorder=3, clip_on=False,
                        transform=transforms.offset_copy(ax.transData, fig, x=-ARROW / 2, units="points"))
        inside = np.isfinite(r.stat) and x0 <= r.stat <= x1
        if inside:
            if reg:
                ax.plot([r.stat], [y], "o", ms=4.5, mfc="black", mec="black", mew=0.8, zorder=4)
            else:
                ax.plot([r.stat], [y], "o", ms=4.0, mfc="white", mec=col, mew=0.8, zorder=4)
        printed_n = fmt_int(r.n)
        ax.text(N_RIGHT / W, y, printed_n, transform=n_tf, ha="right", va="center", fontsize=FS, color=GREY)
        out.append({"row": len(out), "label": r.label, "kind": r.kind, "source": r.source, "variant": r.variant,
                    "group": r.group, "stat": r.stat, "lo": r.lo, "hi": r.hi, "n": r.n, "n_days": r.n_days,
                    "y": y, "arrow_lo": arrow_lo, "arrow_hi": arrow_hi, "stat_drawn": bool(inside),
                    "printed_n": printed_n, "printed": r.label})
    ax.text(N_RIGHT / W, 1.0, n_title, transform=transforms.blended_transform_factory(fig.transFigure, ax.transAxes),
            ha="right", va="bottom", fontsize=FS, color=GREY)
    ax.set_yticks(ys)
    ax.set_yticklabels([r.label for r in rows])
    for t, r in zip(ax.get_yticklabels(), rows):
        t.set_fontweight("bold" if r.kind == "registered" else "normal")
        t.set_color("black")
    ax.tick_params(axis="y", length=0, pad=2)
    ax.spines["left"].set_visible(False)
    if ticks is not None:
        ax.set_xticks(list(ticks))
        ax.set_xticklabels(list(ticklabels) if ticklabels is not None else [f"{t:g}" for t in ticks])
        ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel(xlabel)
    table = pd.DataFrame(out)
    return verdict_line(h), table


def header_table(lines: Sequence[str]) -> pd.DataFrame:
    return pd.DataFrame({"row": [-len(lines) + i for i in range(len(lines))], "label": "", "kind": "header",
                         "printed": list(lines)})


# -------------------------------------------------------------------------------------------------------- save

def save(fig: plt.Figure, name: str, out_dir: Path) -> List[Path]:
    """PDF and PNG (400 dpi) at the printed size, plus a luminance copy under ``gray/`` for the grey check."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf, png = out_dir / f"{name}.pdf", out_dir / f"{name}.png"
    with plt.rc_context(RC):
        fig.savefig(pdf)
        fig.savefig(png, dpi=DPI)
    plt.close(fig)
    gray_dir = out_dir / "gray"
    gray_dir.mkdir(parents=True, exist_ok=True)
    gray = gray_dir / f"{name}.png"
    with Image.open(png) as im:
        im.convert("L").save(gray)
    return [pdf, png, gray]


def read_csv(path: Path) -> pd.DataFrame:
    """A figure table as written: floats exactly, printed text as text."""
    df = pd.read_csv(path, float_precision="round_trip", dtype={"printed": str, "printed_n": str})
    for c in ("printed", "printed_n"):
        if c in df:
            df[c] = df[c].fillna("")
    return df


def write_csv(df: pd.DataFrame, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


# ------------------------------------------------------------------------------------------------------ checks

@dataclass(frozen=True)
class Check:
    """One test number: a value as it stands in the figure table against the result file it comes from."""
    name: str
    figure: str
    source: str
    fn: Callable[[Path], Tuple[bool, str]]


def run(checks: Sequence[Check], results_dir: Path) -> List[Dict[str, object]]:
    out = []
    for c in checks:
        try:
            ok, detail = c.fn(Path(results_dir))
        except Exception as exc:  # noqa: BLE001 - a check that cannot run is a failed check
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        out.append({"name": c.name, "figure": c.figure, "source": c.source, "ok": bool(ok), "detail": detail})
    return out


def close(a: float, b: float, rel: float = 1e-12, abs_: float = 1e-12) -> bool:
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_)
