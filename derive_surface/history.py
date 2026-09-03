"""Historical downloads: every option trade Derive has ever matched, plus the spot feed.

Derive does **not** expose historical orderbook snapshots.  What it does expose
publicly is (a) the complete trade tape — every fill, with the mark price and
index price at fill time — and (b) the spot/index feed at 1-minute granularity.
Every fill is the moment a resting order and an aggressor met, so the tape is
the densest public trace of where the orderbook actually was.

Raw pages are cached under ``data/raw`` (git-ignored, resumable) and condensed
into tidy parquet files under ``data``.
"""
from __future__ import annotations

import gzip
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from .api import DeriveClient, OptionName

log = logging.getLogger(__name__)

PAGE_SIZE = 1000
TRADE_COLUMNS = [
    "trade_id", "timestamp", "instrument_name", "expiry", "strike", "option_type",
    "direction", "trade_price", "trade_amount", "mark_price", "index_price", "liquidity_role", "tx_status",
]


# --------------------------------------------------------------------- trades
def download_trades(
    client: DeriveClient, currency: str, raw_dir: Path, *, to_ts_ms: int | None = None, workers: int = 4
) -> Path:
    """Fetch every option trade for ``currency`` into ``raw_dir/<ccy>/pNNNNN.json.gz`` (resumable)."""
    out = raw_dir / currency
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    # The manifest pins ``to_timestamp`` so pagination is stable; to extend the tape later,
    # delete the manifest (cached pages are kept and re-validated by page number).
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        to_ts_ms = to_ts_ms or int(time.time() * 1000)
        first = client.trade_history(currency, page=1, page_size=PAGE_SIZE, to_ts_ms=to_ts_ms)
        manifest = {"currency": currency, "to_ts_ms": to_ts_ms, **first["pagination"]}
        _write_page(out, 1, first)
        manifest_path.write_text(json.dumps(manifest))
    num_pages = int(manifest["num_pages"])
    todo = [p for p in range(1, num_pages + 1) if not (out / f"p{p:05d}.json.gz").exists()]
    log.info("%s: %d trades, %d pages, %d to fetch", currency, manifest["count"], num_pages, len(todo))

    def fetch(page: int) -> int:
        res = client.trade_history(currency, page=page, page_size=PAGE_SIZE, to_ts_ms=manifest["to_ts_ms"])
        _write_page(out, page, res)
        return page

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for fut in as_completed(pool.submit(fetch, p) for p in todo):
            fut.result()
            done += 1
            if done % 25 == 0 or done == len(todo):
                log.info("%s: %d/%d pages", currency, done, len(todo))
    return out


def _write_page(out: Path, page: int, res: dict) -> None:
    final = out / f"p{page:05d}.json.gz"
    tmp = final.with_suffix(".tmp")
    with gzip.open(tmp, "wt") as fh:
        json.dump(res["trades"], fh)
    tmp.replace(final)  # atomic: a crash never leaves a truncated page that resume would skip


def trades_to_parquet(raw_dir: Path, currency: str, out_path: Path) -> pd.DataFrame:
    """Condense the raw pages into one tidy parquet.

    Each fill appears twice on the tape (maker row + taker row).  We keep the
    taker row — its ``direction`` is the aggressor side, i.e. which side of the
    book was hit — and de-duplicate on ``trade_id``.
    """
    rows: list[dict] = []
    for path in sorted((raw_dir / currency).glob("p*.json.gz")):
        with gzip.open(path, "rt") as fh:
            rows.extend(json.load(fh))
    df = pd.DataFrame(rows)
    df["is_taker"] = df["liquidity_role"].eq("taker")
    df = df.sort_values(["trade_id", "is_taker"], ascending=[True, False]).drop_duplicates("trade_id")
    parsed = df["instrument_name"].map(OptionName.parse)
    df["expiry"] = parsed.map(lambda o: o.expiry_ts).astype("int64")
    df["strike"] = parsed.map(lambda o: o.strike).astype("float64")
    df["option_type"] = parsed.map(lambda o: o.option_type)
    for col in ("trade_price", "trade_amount", "mark_price", "index_price"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["timestamp"] = df["timestamp"].astype("int64")
    df = df[TRADE_COLUMNS].sort_values("timestamp").reset_index(drop=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False, compression="zstd")
    log.info("%s: %d unique trades -> %s", currency, len(df), out_path)
    return df


# ----------------------------------------------------------------------- spot
def download_spot(client: DeriveClient, currency: str, start_s: int, end_s: int, period_s: int) -> pd.DataFrame:
    pts = client.spot_history_full(currency, start_s, end_s, period_s)
    df = pd.DataFrame(pts)
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "price"])
    df["timestamp"] = df["timestamp"].astype("int64")
    df["price"] = pd.to_numeric(df["price"])
    return df[["timestamp", "price"]].sort_values("timestamp").reset_index(drop=True)


def download_all(currencies: list[str], data_dir: Path, *, spot_start_s: int = 1_704_067_200, minute_days: int = 14) -> None:
    """Full historical pull for the given currencies (trades + hourly spot + recent minute spot)."""
    client = DeriveClient()
    raw_dir = data_dir / "raw" / "trades"
    now_s = int(time.time())
    for ccy in currencies:
        hourly = download_spot(client, ccy, spot_start_s, now_s, 3600)
        hourly.to_parquet(data_dir / "spot" / f"{ccy}_1h.parquet", index=False) if _mk(data_dir / "spot") else None
        minute = download_spot(client, ccy, now_s - minute_days * 86400, now_s, 60)
        minute.to_parquet(data_dir / "spot" / f"{ccy}_1m.parquet", index=False)
        log.info("%s: spot %d hourly / %d minute points", ccy, len(hourly), len(minute))
    for ccy in currencies:
        download_trades(client, ccy, raw_dir)
        trades_to_parquet(raw_dir, ccy, data_dir / "trades" / f"{ccy}_option_trades.parquet")


def _mk(p: Path) -> bool:
    p.mkdir(parents=True, exist_ok=True)
    return True


if __name__ == "__main__":  # python -m derive_surface.history BTC ETH HYPE
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    download_all(sys.argv[1:] or ["BTC", "ETH", "HYPE"], Path("data"))
