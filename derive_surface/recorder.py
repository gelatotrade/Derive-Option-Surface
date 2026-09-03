"""Live orderbook recorder.

Two independent recorders, both append parquet *parts* that ``merge_parts``
later concatenates:

* ``record_tickers`` — every ``interval_s`` seconds pull the slim ticker of
  **every** live option (one ``get_tickers`` call per expiry).  A slim ticker
  carries best bid/ask with sizes, the exchange mark and IV, bid/ask IV and the
  first-order greeks — i.e. the top of every book plus the index and forward.
* ``record_depth`` — subscribe over WebSocket to the price-level book
  (``orderbook.<name>.1.10``) of the instruments near the money and flush the
  latest book of each instrument every ``flush_s`` seconds.
"""
from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from .api import DeriveClient, expiry_date_str, slim_ticker_row

log = logging.getLogger(__name__)


# ------------------------------------------------------------------- tickers
def snapshot_tickers(client: DeriveClient, currency: str, expiries: list[int], workers: int = 6) -> pd.DataFrame:
    """One full top-of-book snapshot of all options of ``currency``."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        books = pool.map(lambda e: client.tickers(currency, expiry_date_str(e)), expiries)
    rows = [slim_ticker_row(name, t) for book in books for name, t in book.items()]
    df = pd.DataFrame(rows)
    df.insert(0, "currency", currency)
    return df


def record_tickers(
    currencies: list[str], out_dir: Path, *, interval_s: float = 20, duration_s: float = 3600, flush_every: int = 12
) -> None:
    client = DeriveClient()
    out_dir.mkdir(parents=True, exist_ok=True)
    expiries = {c: client.option_expiries(c) for c in currencies}
    refreshed = time.time()
    buffers: dict[str, list[pd.DataFrame]] = {c: [] for c in currencies}
    t_end = time.time() + duration_s
    cycle = 0
    while time.time() < t_end:
        t0 = time.time()
        if t0 - refreshed > 900:  # expiries roll daily at 08:00 UTC
            expiries = {c: client.option_expiries(c) for c in currencies}
            refreshed = t0
        for c in currencies:
            live = [e for e in expiries[c] if e > t0]
            try:
                df = snapshot_tickers(client, c, live)
                df.insert(0, "cycle_ts", int(t0 * 1000))
                buffers[c].append(df)
            except Exception as exc:  # keep recording no matter what
                log.warning("%s snapshot failed: %s", c, exc)
        cycle += 1
        if cycle % flush_every == 0:
            _flush(buffers, out_dir, "tickers")
        log.info("cycle %d done in %.1fs", cycle, time.time() - t0)
        time.sleep(max(0.0, interval_s - (time.time() - t0)))
    _flush(buffers, out_dir, "tickers")


# --------------------------------------------------------------------- depth
def pick_depth_instruments(client: DeriveClient, currency: str, *, band: float = 0.08, max_per_ccy: int = 40) -> list[str]:
    """Options near the money on the two nearest expiries (>= 20h out) plus the nearest monthly."""
    now = time.time()
    expiries = [e for e in client.option_expiries(currency) if e - now > 20 * 3600]
    chosen = expiries[:2] + [e for e in expiries if e - now > 20 * 86400][:1]
    names: list[str] = []
    for e in dict.fromkeys(chosen):
        tk = client.tickers(currency, expiry_date_str(e))
        rows = [slim_ticker_row(n, t) for n, t in tk.items()]
        idx = next((r["index"] for r in rows if r["index"]), None)
        if not idx:
            continue
        near = sorted((r for r in rows if abs(r["strike"] / idx - 1) <= band), key=lambda r: abs(r["strike"] - idx))
        names += [r["instrument_name"] for r in near]
    return names[:max_per_ccy]


def record_depth(currencies: list[str], out_dir: Path, *, duration_s: float = 3600, flush_s: float = 10, depth: int = 10) -> None:
    client = DeriveClient()
    out_dir.mkdir(parents=True, exist_ok=True)
    names = {c: pick_depth_instruments(client, c) for c in currencies}
    channels = [f"orderbook.{n}.1.{depth}" for ns in names.values() for n in ns]
    log.info("subscribing to %d depth channels", len(channels))
    latest: dict[str, dict] = {}
    buffer: list[dict] = []
    parts = 0
    last_flush = time.time()

    def on_message(channel: str, data: dict) -> None:
        nonlocal buffer, parts, last_flush
        latest[data["instrument_name"]] = data
        now = time.time()
        if now - last_flush >= flush_s:
            flush_ts = int(now * 1000)
            for name, book in latest.items():
                for side in ("bids", "asks"):
                    for level, (price, amount) in enumerate(book[side]):
                        buffer.append(
                            dict(flush_ts=flush_ts, book_ts=book["timestamp"], instrument_name=name, side=side[:-1],
                                 level=level, price=float(price), amount=float(amount))
                        )
            last_flush = now
            if len(buffer) > 200_000:
                _write_part(pd.DataFrame(buffer), out_dir, "depth", parts)
                parts += 1
                buffer = []

    asyncio.run(client.stream(channels, on_message, duration_s=duration_s))
    if buffer:
        _write_part(pd.DataFrame(buffer), out_dir, "depth", parts)


# ------------------------------------------------------------------- storage
def _flush(buffers: dict[str, list[pd.DataFrame]], out_dir: Path, kind: str) -> None:
    for c, dfs in buffers.items():
        if dfs:
            n = len(list(out_dir.glob(f"{kind}_{c}_part*.parquet")))
            _write_part(pd.concat(dfs, ignore_index=True), out_dir, f"{kind}_{c}", n)
            dfs.clear()


def _write_part(df: pd.DataFrame, out_dir: Path, prefix: str, n: int) -> None:
    path = out_dir / f"{prefix}_part{n:04d}.parquet"
    df.to_parquet(path, index=False, compression="zstd")
    log.info("wrote %s (%d rows)", path.name, len(df))


def merge_parts(out_dir: Path, prefix: str, target: Path) -> pd.DataFrame:
    parts = sorted(out_dir.glob(f"{prefix}_part*.parquet"))
    df = pd.concat((pd.read_parquet(p) for p in parts), ignore_index=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(target, index=False, compression="zstd")
    return df


if __name__ == "__main__":  # python -m derive_surface.recorder tickers|depth DURATION_S
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    kind, duration = sys.argv[1], float(sys.argv[2])
    ccys = sys.argv[3:] or ["BTC", "ETH", "HYPE"]
    out = Path("data/raw/live")
    record_tickers(ccys, out, duration_s=duration) if kind == "tickers" else record_depth(ccys, out, duration_s=duration)


# ------------------------------------------------------- full depth snapshot
def depth_snapshot(currencies: list[str], out_path: Path, *, depth: int = 20, batch: int = 150, settle_s: float = 6.0) -> pd.DataFrame:
    """One complete picture of the resting orders: price levels of *every* live option.

    Subscribes in batches (the server accepts large subscription lists but
    publishes each book once on subscribe), keeps the first full book per
    instrument, and writes one tidy parquet: instrument, side, level, price, amount.
    """
    client = DeriveClient()
    names = [i["instrument_name"] for c in currencies for i in client.instruments(c)]
    books: dict[str, dict] = {}

    def on_message(channel: str, data: dict) -> None:
        books.setdefault(data["instrument_name"], data)

    for i in range(0, len(names), batch):
        chans = [f"orderbook.{n}.1.{depth}" for n in names[i : i + batch]]
        asyncio.run(client.stream(chans, on_message, duration_s=settle_s))
        log.info("depth snapshot: %d/%d books", len(books), len(names))
    rows = [
        dict(instrument_name=n, book_ts=b["timestamp"], side=side[:-1], level=lvl, price=float(p), amount=float(a))
        for n, b in books.items()
        for side in ("bids", "asks")
        for lvl, (p, a) in enumerate(b[side])
    ]
    df = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False, compression="zstd")
    log.info("wrote %s: %d resting levels across %d instruments", out_path, len(df), df["instrument_name"].nunique())
    return df
