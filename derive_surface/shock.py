"""What-if movie: move the underlying, hold the surface's *shape*, watch the book re-price.

The live recording shows what the market did in a couple of hours.  This module
shows the mechanics in isolation: take the latest orderbook surface, sweep the
forward through ``±amplitude`` and re-price every strike under a chosen regime:

* ``sticky_delta`` — implied vol is a function of moneyness ``k = ln(K/F)``:
  the smile travels with the forward (the crypto market's default behaviour).
  In *delta* coordinates the surface is invariant by construction; in *strike*
  coordinates it slides.
* ``sticky_strike`` — implied vol per strike is frozen; the forward moves
  underneath it, so in moneyness coordinates the smile shifts the other way.

The strike ladder is re-priced with Black-76 at each frame so the second-order
effects (vanna: the skew re-pricing the delta; gamma: the convexity of the
ladder) are visible as motion, not as numbers.
"""
from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from . import pricing
from .animate import Frame, Renderer, frame_from_snapshot, load_live_tickers, write_gif, write_mp4
from .surface import Smile, Surface

log = logging.getLogger(__name__)


class StickyStrikeSmile(Smile):
    """A smile frozen per strike: evaluating at forward F' reads the base smile at the same strike."""

    def __init__(self, base: Smile, new_F: float):
        super().__init__(base.expiry, base.T, new_F, base.df, base.k, base.iv, base.weight, base.model, base.params)
        self._base, self._shift = base, np.log(new_F / base.F)

    def total_variance(self, k: np.ndarray) -> np.ndarray:  # k relative to F' -> same strike relative to F
        return self._base.total_variance(np.asarray(k, float) + self._shift)


def shocked_surface(base: Surface, eps: float, regime: str) -> Surface:
    smiles = []
    for sm in base.smiles:
        F_new = sm.F * (1 + eps)
        smiles.append(replace(sm, F=F_new) if regime == "sticky_delta" else StickyStrikeSmile(sm, F_new))
    return Surface(base.ts_ms, base.currency, base.spot * (1 + eps), smiles)


def repriced_ladder(base: Frame, shocked: Surface) -> tuple[pd.DataFrame, float]:
    """Re-price the front ladder from the shocked smile; keep each quote's original bid/ask width."""
    sm = next(s for s in shocked.smiles if s.expiry == base.ladder_expiry)
    lad = base.ladder.copy()
    K = lad["strike"].values
    iv = sm(np.log(K / sm.F))
    for side, kind in (("call", 1), ("put", -1)):
        quoted = (base.ladder[f"{side}_bid"].gt(0) & base.ladder[f"{side}_ask"].gt(0)).values  # only strikes the live book prices two-sided
        mid = np.where(quoted, pricing.price(sm.F, K, sm.T, iv, kind, sm.df), np.nan)
        half = 0.5 * (lad[f"{side}_ask"] - lad[f"{side}_bid"]).fillna(0).values
        lad[f"{side}_mid"] = mid
        lad[f"{side}_bid"], lad[f"{side}_ask"] = np.maximum(mid - half, 0), mid + half
    return lad, sm.F


def animate_shock(
    data_dir: Path, currency: str, out_dir: Path, *, amplitude: float = 0.06, n_frames: int = 72, regime: str = "sticky_delta",
    axis: str = "strike", color_by: str = "mvdelta", fps: float = 10, width: int = 880, height: int = 496, suffix: str = ""
) -> Path:
    tk = load_live_tickers(data_dir, currency)
    last = int(tk["cycle_ts"].max())
    base = frame_from_snapshot(tk[tk["cycle_ts"] == last], currency, last)
    base.surface.smiles = [s for s in base.surface.smiles if s.T * 365 >= 1.0]  # the sub-day expiry only adds noise here
    eps = amplitude * np.sin(2 * np.pi * np.arange(n_frames) / n_frames)
    F0 = base.forward
    x_grid = F0 * np.exp(np.linspace(-0.16, 0.16, 41)) if axis == "strike" else None
    frames = []
    for i, e in enumerate(eps):
        s = shocked_surface(base.surface, float(e), regime)
        lad, F = repriced_ladder(base, s)
        cap = f"Scenario: forward {F0:,.0f} → {F:,.0f} ({e:+.1%}) · {regime.replace('_', '-')} · smile shape from the live orderbook, ladder re-priced with Black-76"
        frames.append(Frame(base.ts_ms, s, lad, base.ladder_expiry, F, caption=cap, cursor_x=float(i)))
    r = Renderer(currency, axis=axis, color_by=color_by, width=width, height=height,
                 title=f"{currency} · Derive options · spot shock ({regime.replace('_', '-')})")
    r.x_grid = x_grid
    r.time_axis = False
    r.mask_wings = axis in ("strike", "logm")
    r.fit_limits(frames)
    spot_t = np.arange(n_frames, dtype=float)
    spot_p = base.surface.spot * (1 + eps)
    ladder_hi = max(f.ladder[["call_ask", "put_ask"]].max().max() for f in frames)
    rgb = [r.render(f, spot_t, spot_p, (0, n_frames - 1), (spot_p.min() * 0.995, spot_p.max() * 1.005), (0, ladder_hi * 1.08)) for f in frames]
    tag = f"{currency}_shock_{regime}{suffix}"
    write_mp4(rgb, out_dir / f"{tag}.mp4", fps)
    return write_gif(rgb, out_dir / f"{tag}.gif", fps)


if __name__ == "__main__":  # python -m derive_surface.shock BTC [sticky_delta|sticky_strike] [color_by]
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ccy = sys.argv[1]
    regime = sys.argv[2] if len(sys.argv) > 2 else "sticky_delta"
    color_by = sys.argv[3] if len(sys.argv) > 3 else "mvdelta"
    animate_shock(Path("data"), ccy, Path("docs/media"), regime=regime, color_by=color_by, suffix="" if color_by == "mvdelta" else f"_{color_by}")
