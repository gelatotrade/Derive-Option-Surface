"""Print width of the Paper 2 figures: the canvas is the width at which ``paper2/main.tex`` sets it.

cas-dc sets ``figure*`` at the text width, 494.50888 pt, and ``figure`` at the column width, 238.25444 pt (TeX points,
72.27 to the inch): 6.8425 and 3.2967 in. The slots are laid out on canvases of 7.0 and 3.4 in (ABBILDUNGSWAHL 6.1);
set with ``width=\\linewidth`` they shrank by 2.3 and 3.0 per cent, and every text of 7 pt printed at 6.8 pt (audit
A48). :func:`to_print` sets the canvas to 6.84 or 3.29 in just before a figure is saved, a hair under the set width
so that the scale in the paper is at least one: every position, which the slots give as a fraction of the canvas,
moves closer by that factor, while the type keeps its size in points.
"""
from __future__ import annotations

TEXTWIDTH_IN = 494.50888 / 72.27            # \textwidth of cas-dc (figure*)
COLUMNWIDTH_IN = 238.25444 / 72.27          # \columnwidth of cas-dc (figure)
PRINT_WIDTH = {7.0: 6.84, 3.4: 3.29}        # layout width -> width of the saved canvas
TOL = 1e-6


def print_width(width: float) -> float:
    """Saved width for a canvas laid out at ``width`` (a canvas already at print width stays)."""
    for layout, printed in PRINT_WIDTH.items():
        if abs(width - layout) < TOL or abs(width - printed) < TOL:
            return printed
    raise ValueError(f"no print width for a canvas {width!r} in wide")


def to_print(fig):
    """Set ``fig`` to its print width, keeping the height; returns ``fig``."""
    w, h = fig.get_size_inches()
    fig.set_size_inches(print_width(float(w)), float(h), forward=False)
    return fig
