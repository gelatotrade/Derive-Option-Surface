"""Full-field option trade tape: both rows of every fill, fetched in single-page time windows.

Measured against api.lyra.finance on 2026-09-17:

* ``get_trade_history`` returns the rows of a page in no stable chronological order, so walking the
  pages of a large range can skip or repeat rows.  We split every day until each window fits into
  one page and fetch that window exactly once.
* ``from_timestamp`` and ``to_timestamp`` are both inclusive (count[a, m-1] + count[m, b] == count[a, b]).
* Every fill has a maker row and a taker row with the same ``trade_id``; each row carries wallet,
  subaccount_id, rfq_id, fees, rebate and realised PnL.

Window files ``<from>_<to>.json.gz`` are written atomically, so an interrupted download resumes where
it stopped.  The manifest lists the leaf windows of one run; ``condense`` reads exactly those, so
windows of an earlier run with a different end time can never be counted twice.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple

import pandas as pd

from .api import OptionName

log = logging.getLogger(__name__)

PAGE_SIZE = 1000
DAY_MS = 86_400_000
FIELDS = [
    "trade_id", "timestamp", "instrument_name", "direction", "liquidity_role", "trade_price", "trade_amount",
    "mark_price", "index_price", "wallet", "subaccount_id", "rfq_id", "quote_id", "trade_fee", "expected_rebate",
    "extra_fee", "realized_pnl", "realized_pnl_excl_fees", "tx_hash", "tx_status",
]
NUMERIC = [
    "trade_price", "trade_amount", "mark_price", "index_price", "trade_fee", "expected_rebate", "extra_fee",
    "realized_pnl", "realized_pnl_excl_fees",
]
ROW_KEY = ["trade_id", "liquidity_role", "subaccount_id"]
Window = Tuple[int, int, int]  # (from_ms, to_ms, rows); both bounds inclusive


def _query(client, lo_ms: int, hi_ms: int, page: int, instrument_type: str) -> dict:
    return client.call(
        "get_trade_history", instrument_type=instrument_type, page=page, page_size=PAGE_SIZE,
        from_timestamp=lo_ms, to_timestamp=hi_ms,
    )


def window_path(out_dir: Path, lo_ms: int, hi_ms: int) -> Path:
    return out_dir / f"{lo_ms}_{hi_ms}.json.gz"


def _write_window(path: Path, lo_ms: int, hi_ms: int, count: int, trades: list) -> None:
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt") as fh:
        json.dump({"from_ms": lo_ms, "to_ms": hi_ms, "count": count, "fetched_ms": int(time.time() * 1000), "trades": trades}, fh)
    tmp.replace(path)


def _read_window(path: Path) -> dict:
    with gzip.open(path, "rt") as fh:
        return json.load(fh)


def fetch_range(client, lo_ms: int, hi_ms: int, out_dir: Path, instrument_type: str = "option") -> List[Window]:
    """Fetch every row in [lo_ms, hi_ms] into single-page window files and return the leaf windows."""
    leaves: List[Window] = []
    stack = [(lo_ms, hi_ms)]
    while stack:
        a, b = stack.pop()
        path = window_path(out_dir, a, b)
        if path.exists():
            leaves.append((a, b, int(_read_window(path)["count"])))
            continue
        res = _query(client, a, b, 1, instrument_type)
        n = int(res["pagination"]["count"])
        if n > PAGE_SIZE and a < b:
            m = (a + b) // 2
            stack.append((m + 1, b))
            stack.append((a, m))
            continue
        trades = list(res["trades"])
        if n > PAGE_SIZE:  # one millisecond holding more than a page: walk its pages and de-duplicate
            for page in range(2, int(res["pagination"]["num_pages"]) + 1):
                trades.extend(_query(client, a, b, page, instrument_type)["trades"])
            trades = list({(t["trade_id"], t["liquidity_role"], t["subaccount_id"]): t for t in trades}.values())
            if len(trades) != n:
                log.warning("window %d: %d unique rows after paging, API count %d", a, len(trades), n)
        _write_window(path, a, b, n, trades)
        leaves.append((a, b, n))
    return leaves


def download_tape(
    client, out_dir: Path, start_ms: int, end_ms: int, *, instrument_type: str = "option", workers: int = 6
) -> dict:
    """Fetch [start_ms, end_ms] day by day (parallel) and write a manifest listing the leaf windows."""
    out_dir.mkdir(parents=True, exist_ok=True)
    days = [(d, min(d + DAY_MS - 1, end_ms)) for d in range(start_ms, end_ms + 1, DAY_MS)]
    leaves: List[Window] = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetch_range, client, a, b, out_dir, instrument_type) for a, b in days]
        for i, fut in enumerate(as_completed(futures), 1):
            leaves.extend(fut.result())
            if i % 50 == 0 or i == len(futures):
                log.info("tape %s: %d/%d days, %d rows, %.0f s", instrument_type, i, len(futures),
                         sum(w[2] for w in leaves), time.time() - t0)
    leaves.sort()
    api_count = int(_query(client, start_ms, end_ms, 1, instrument_type)["pagination"]["count"])
    manifest = {
        "instrument_type": instrument_type, "from_ms": start_ms, "to_ms": end_ms,
        "rows_in_windows": sum(w[2] for w in leaves), "api_count": api_count, "windows": len(leaves),
        "leaves": [list(w) for w in leaves], "finished_ms": int(time.time() * 1000),
    }
    (out_dir / f"manifest_{start_ms}_{end_ms}.json").write_text(json.dumps(manifest))
    if manifest["rows_in_windows"] != api_count:
        log.warning("row count mismatch: windows %d vs API %d", manifest["rows_in_windows"], api_count)
    return manifest


def condense(out_dir: Path, manifest: dict) -> pd.DataFrame:
    """All rows of the manifest's windows as one typed frame (both rows of every fill)."""
    frames, bad = [], []
    for a, b, n in manifest["leaves"]:
        trades = _read_window(window_path(out_dir, a, b))["trades"]
        if len(trades) != n:
            bad.append((a, b, n, len(trades)))
        if trades:
            frames.append(pd.DataFrame(trades).reindex(columns=FIELDS))
    if bad:
        raise ValueError(f"{len(bad)} windows whose row count differs from the API count, e.g. {bad[:3]}")
    if not frames:
        return pd.DataFrame(columns=FIELDS + ["currency", "expiry", "strike", "option_type"])
    df = pd.concat(frames, ignore_index=True)
    before = len(df)
    df = df.drop_duplicates(ROW_KEY)
    if len(df) != before:
        log.warning("dropped %d duplicate rows", before - len(df))
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
    df["timestamp"] = df["timestamp"].astype("int64")
    df["subaccount_id"] = pd.to_numeric(df["subaccount_id"]).astype("int64")
    df["wallet"] = df["wallet"].str.lower()
    parsed = {name: OptionName.parse(name) for name in df["instrument_name"].unique()}
    df["currency"] = df["instrument_name"].map(lambda n: parsed[n].currency)
    df["expiry"] = df["instrument_name"].map(lambda n: parsed[n].expiry_ts).astype("int64")
    df["strike"] = df["instrument_name"].map(lambda n: parsed[n].strike).astype("float64")
    df["option_type"] = df["instrument_name"].map(lambda n: parsed[n].option_type)
    return df.sort_values(["timestamp", "trade_id", "liquidity_role"]).reset_index(drop=True)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_tape(df: pd.DataFrame, tape_dir: Path) -> dict:
    """One parquet per underlying plus MANIFEST.json (rows, sha256)."""
    tape_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for ccy, g in df.groupby("currency"):
        path = tape_dir / f"{ccy}_options_full.parquet"
        g.reset_index(drop=True).to_parquet(path, index=False, compression="zstd")
        files[path.name] = {"rows": int(len(g)), "sha256": _sha256(path)}
    (tape_dir / "MANIFEST.json").write_text(json.dumps(files, indent=1, sort_keys=True))
    return files
