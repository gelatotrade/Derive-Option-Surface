"""Small, reproducible analyses quoted in the README.

``greek_noise_table`` answers "which order of greeks can an orderbook support?"
empirically: build the surface once from every quote's *bid* IV and once from
its *ask* IV, evaluate each greek on the same (delta, tenor) grid, and report
the median relative gap.  The gap is the part of each greek that is spread,
not signal.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .surface import Smile, Surface, quotes_from_snapshot

ORDERS = {
    1: ["delta", "vega", "theta"],
    2: ["gamma", "vanna", "volga", "charm"],
    3: ["speed", "zomma", "color", "ultima"],
}


def surface_from_side(df: pd.DataFrame, currency: str, side: str, ts_ms: int | None = None) -> Surface:
    """Surface fitted to ``iv_bid`` or ``iv_ask`` instead of the mid."""
    ts_ms = ts_ms or int(df["ts"].max())
    q = quotes_from_snapshot(df, ts_ms).dropna(subset=[f"iv_{side}"])
    smiles = [
        Smile.fit(int(e), g["T"].iloc[0], g["F"].iloc[0], g["df"].iloc[0], g["k"].values, g[f"iv_{side}"].values, g["weight"].values)
        for e, g in q.groupby("expiry")
        if len(g) >= 3
    ]
    return Surface(ts_ms, currency, float(df["index"].median()), sorted(smiles, key=lambda s: s.T))


def greek_noise_table(df: pd.DataFrame, currency: str, axis: str = "logm", delta_band: tuple[float, float] = (0.10, 0.90)) -> pd.DataFrame:
    """Relative bid-vs-ask gap per greek on a fixed-strike (``logm``) grid, restricted to the liquid 10-90 delta region.

    (On a *delta* grid the first-order greeks are pinned by the coordinates themselves, which would flatter them.)
    """
    bid, ask = (surface_from_side(df, currency, s) for s in ("bid", "ask"))
    tenors = np.geomspace(max(bid.tenors.min(), ask.tenors.min()), min(bid.tenors.max(), ask.tenors.max()), 16)
    x = np.linspace(-0.25, 0.25, 41) if axis == "logm" else None
    gb, ga = bid.greeks_grid(axis, x, tenors=tenors), ask.greeks_grid(axis, x, tenors=tenors)
    d = 0.5 * (ga["delta"] + gb["delta"])
    call_delta = np.where(d < 0, d + 1, d)  # OTM puts carry delta - 1
    liquid = (call_delta >= delta_band[0]) & (call_delta <= delta_band[1])
    rows = []
    for order, names in ORDERS.items():
        for n in names:
            a, b = ga[n][liquid], gb[n][liquid]
            scale = np.maximum(np.abs(a) + np.abs(b), 1e-300) / 2
            rel = np.abs(a - b) / scale
            rows.append(dict(order=order, greek=n, median_rel_gap=float(np.nanmedian(rel)), p75_rel_gap=float(np.nanpercentile(rel, 75))))
    q = quotes_from_snapshot(df)
    spread = (q["iv_ask"] - q["iv_bid"]).dropna()
    out = pd.DataFrame(rows)
    out.attrs["median_spread_volpts"] = float(spread.median() * 100)
    out.attrs["iv_rel_gap"] = float(np.nanmedian(np.abs(ga["iv"] - gb["iv"]) / ((ga["iv"] + gb["iv"]) / 2)))
    return out


if __name__ == "__main__":
    import sys

    df = pd.read_parquet(sys.argv[1])
    t = greek_noise_table(df, sys.argv[2] if len(sys.argv) > 2 else "BTC", sys.argv[3] if len(sys.argv) > 3 else "logm")
    print(f"median bid/ask spread: {t.attrs['median_spread_volpts']:.2f} vol points; iv rel gap {t.attrs['iv_rel_gap']:.3f}")
    print(t.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
