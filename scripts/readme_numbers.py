"""Print the figures quoted in README.md so they can be refreshed from the data on disk."""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from derive_surface.analysis import greek_noise_table  # noqa: E402

DATA = Path("data")


def d(ms: float) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def main() -> None:
    total = 0
    for c in ("BTC", "ETH", "HYPE"):
        t = pd.read_parquet(DATA / "trades" / f"{c}_option_trades.parquet")
        total += len(t)
        print(f"{c}_TRADES={len(t):,}  {c}_FROM={d(t.timestamp.min())}  {c}_TO={d(t.timestamp.max())}")
    print(f"TRADES_TOTAL={total:,}")
    live = DATA / "live"
    if live.exists():
        n_instr, t0, t1, cycles = 0, None, None, 0
        for c in ("BTC", "ETH", "HYPE"):
            f = live / f"{c}_tickers.parquet"
            if f.exists():
                tk = pd.read_parquet(f)
                n_instr += tk["instrument_name"].nunique()
                cycles = max(cycles, tk["cycle_ts"].nunique())
                t0 = min(t0 or tk.cycle_ts.min(), tk.cycle_ts.min())
                t1 = max(t1 or tk.cycle_ts.max(), tk.cycle_ts.max())
        if t0:
            print(f"LIVE_INSTR={n_instr}  LIVE_CYCLES={cycles}  LIVE_FROM={dt.datetime.fromtimestamp(t0/1000, dt.timezone.utc):%H:%M}  "
                  f"LIVE_TO={dt.datetime.fromtimestamp(t1/1000, dt.timezone.utc):%H:%M} UTC  LIVE_DURATION={(t1-t0)/3.6e6:.1f} h")
        for name in ("depth.parquet", "depth_snapshot.parquet"):
            f = live / name
            if f.exists():
                dp = pd.read_parquet(f)
                print(f"{name}: {dp.instrument_name.nunique()} instruments, {len(dp):,} levels, "
                      f"ts={dt.datetime.fromtimestamp(dp.book_ts.max()/1000, dt.timezone.utc):%Y-%m-%d %H:%M} UTC")
        for c in ("BTC", "ETH", "HYPE"):
            f = live / f"{c}_tickers.parquet"
            if f.exists():
                tk = pd.read_parquet(f)
                snap = tk[tk.cycle_ts == tk.cycle_ts.max()]
                tab = greek_noise_table(snap, c)
                print(f"--- {c} greek noise @ {dt.datetime.fromtimestamp(int(snap.cycle_ts.max())/1000, dt.timezone.utc):%Y-%m-%d %H:%M} UTC, "
                      f"median spread {tab.attrs['median_spread_volpts']:.2f} vol pts")
                print(tab.to_string(index=False, float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
