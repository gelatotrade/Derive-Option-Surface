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
    signed = {"theta", "vanna", "charm", "speed", "zomma", "color", "ultima", "rho", "volga"}
    rows = []
    for order, names in ORDERS.items():
        for n in names:
            A, B = ga[n], gb[n]
            if n in signed:  # normalise by the tenor row's largest magnitude: a sign change is not "infinite noise"
                scale = np.broadcast_to(np.nanmax(np.abs(np.where(liquid, A, np.nan)) + np.abs(np.where(liquid, B, np.nan)), axis=1)[:, None] / 2, A.shape)
            else:
                scale = np.maximum(np.abs(A) + np.abs(B), 1e-300) / 2
            a, b = A[liquid], B[liquid]
            rel = np.abs(a - b) / scale[liquid]
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


# ------------------------------------------------------------ regime (SSR)
def skew_stickiness(surfaces: list, tenor_days=(7.0, 30.0, 90.0)) -> pd.DataFrame:
    """Bergomi's skew-stickiness ratio from a time-ordered list of surfaces.

    SSR(T) = (d sigma_ATM / d ln F) / (d sigma / d k)|_ATM, estimated per fixed
    tenor by a through-the-origin regression of ATM-vol changes on log-forward
    changes between consecutive surfaces, divided by the mean ATM skew.
    0 = sticky-delta (smile rides with the forward), 1 = sticky-strike (vol per
    strike frozen), ~2 = short-dated stochastic-vol dynamics (equity indices).
    """
    rows = []
    T_want = np.array(tenor_days) / 365.0
    atm, skw, lnF = [], [], []
    for s in surfaces:
        if len(s.smiles) < 2:
            continue
        T = s.tenors
        a = np.array([sm.atm_iv for sm in s.smiles])
        k = np.array([float(sm.skew(np.zeros(1))[0]) for sm in s.smiles])
        F = np.array([sm.F for sm in s.smiles])
        inside = (T_want >= T.min()) & (T_want <= T.max())
        atm.append(np.where(inside, np.interp(T_want, T, a), np.nan))
        skw.append(np.where(inside, np.interp(T_want, T, k), np.nan))
        lnF.append(np.where(inside, np.log(np.interp(T_want, T, F)), np.nan))
    atm, skw, lnF = (np.array(v) for v in (atm, skw, lnF))
    for j, days in enumerate(tenor_days):
        da, dl = np.diff(atm[:, j]), np.diff(lnF[:, j])
        ok = np.isfinite(da) & np.isfinite(dl) & (np.abs(dl) > 1e-6)
        if ok.sum() < 5:
            rows.append(dict(tenor_days=days, n=int(ok.sum()), slope=np.nan, atm_skew=np.nan, ssr=np.nan, r2=np.nan))
            continue
        slope = float(np.sum(da[ok] * dl[ok]) / np.sum(dl[ok] ** 2))
        resid = da[ok] - slope * dl[ok]
        r2 = 1 - np.sum(resid**2) / np.sum((da[ok] - da[ok].mean()) ** 2) if ok.sum() > 2 else np.nan
        mean_skew = float(np.nanmean(skw[:, j]))
        rows.append(dict(tenor_days=days, n=int(ok.sum()), slope=slope, atm_skew=mean_skew, ssr=slope / mean_skew if mean_skew else np.nan, r2=float(r2)))
    return pd.DataFrame(rows)
