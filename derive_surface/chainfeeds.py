"""Vol-feed history from Derive Chain (id 957): every ``VolDataUpdated`` push since launch.

The mark IV of every Derive option is an SVI curve per expiry that Derive signs off-chain and pushes to
``LyraVolFeed``.  Each push emits ``VolDataUpdated(uint64 indexed expiry, VolDetails)`` with nine words:
SVI_a, SVI_b, SVI_rho, SVI_m, SVI_sigma, SVI_fwd (all 1e18), SVI_refTau (1e18 years), confidence (1e18),
timestamp (s, signing time).  Each row also keeps ``block_ts``, the time the push landed on chain.
The feed addresses below were identified on 2026-09-17 by matching SVI_fwd against the
live forward of each currency; BTC and ETH never changed address since January 2024.

``svi_vol`` reproduces ``lyra-utils/src/math/SVI.sol``: k = ln(K / SVI_fwd) clipped to
±4·sqrt(a + b·sigma); w = a + b·(rho·(k − m) + sqrt((k − m)² + sigma²)) capped at 144;
vol = sqrt(w / SVI_refTau).  The reference tau of the fit is used, not the live time to expiry.
"""
from __future__ import annotations

import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

log = logging.getLogger(__name__)

RPC_URL = "https://rpc.derive.xyz"
VOL_DATA_UPDATED = "0x0b6ec9c174360425894fd5ff56d14f3450d70f2c9cde3a25983d652a72b84606"
VOL_FEEDS: Dict[str, dict] = {
    "BTC": {"address": "0x388341d9e5a7d7d5accd738b2a31b0622e0c1b87", "from_block": 800_000},  # chain live 12/2023
    "ETH": {"address": "0xb27cb6b08e6c298c8634d73d5f6649665e90d160", "from_block": 800_000},
    "HYPE": {"address": "0x481916590863053ea2d8f21b64ee9429820512d1", "from_block": 29_000_000},
}
# other live vol feeds, identified the same way on 2026-09-17 (not downloaded; used to label emitters)
OTHER_FEEDS: Dict[str, str] = {
    "0x74230ec35a64000874a8ce6c5c7a9ae6368282b3": "SOL",
    "0x52aa5ddf548f02047859a91ef8b70788cf673634": "ZEC",
    "0x665b63672b2d993e78e16afeaace91c55638901a": "XAUT",
    "0xbf2e14dff4d31ed906c504c0742da6db3ad146c0": "XRP",
    "0x8df07f5842fc1bef159fd62137b422cfda9b627e": "VVV",
    "0xe7b58cb6b1fc4d19e300d4bb068aea158c85ae80": "ADA",
    "0x6a0df36b9107bead8509f1535c3512ea7ea9b363": "CC",
    "0xc9b3ac7e837688ea7e8a6a54bd5c57f7b078d82e": "LIT",
    "0x0105e202bb709c69570de3c6c84528360111e6d4": "PUMP",
}
CHUNK_BLOCKS = 50_000
MAX_WINDOW = 50_000
LOG_LIMIT = 10_000
COLUMNS = ["block", "block_ts", "log_index", "expiry", "feed_ts", "svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma",
           "svi_fwd", "svi_ref_tau", "confidence"]
FLOAT32 = ["svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma", "svi_ref_tau", "confidence"]
E18 = 1e18


class RpcError(RuntimeError):
    """A JSON-RPC error returned by the chain node."""

    def __init__(self, error: dict):
        self.error = error
        super().__init__(str(error))

    @property
    def too_many_logs(self) -> bool:
        return self.error.get("code") == -32005 or "limit exceeded" in str(self.error.get("message", "")).lower()


class ChainClient:
    """Minimal JSON-RPC client with retry/backoff for rpc.derive.xyz."""

    def __init__(self, url: str = RPC_URL, timeout: float = 120.0, max_retries: int = 8, session=None):
        self.url, self.timeout, self.max_retries = url, timeout, max_retries
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", "derive-option-surface/p1")

    def call(self, method: str, params: list):
        delay = 1.0
        for attempt in range(self.max_retries):
            try:
                resp = self.session.post(self.url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                                         timeout=self.timeout)
            except requests.RequestException as exc:
                log.warning("%s: network error %s (attempt %d)", method, exc, attempt + 1)
            else:
                if resp.status_code == 429 or resp.status_code >= 500:
                    log.warning("%s: HTTP %s (attempt %d)", method, resp.status_code, attempt + 1)
                else:
                    payload = resp.json()
                    if "error" not in payload:
                        return payload["result"]
                    if "rate" not in str(payload["error"].get("message", "")).lower():
                        raise RpcError(payload["error"])
                    log.warning("%s: rate limited (attempt %d)", method, attempt + 1)
            if attempt < self.max_retries - 1:
                time.sleep(delay + random.uniform(0, 0.5))
                delay = min(delay * 2, 30)
        raise RuntimeError(f"{method}: giving up after {self.max_retries} attempts")

    def block_number(self) -> int:
        return int(self.call("eth_blockNumber", []), 16)

    def block_timestamp(self, number: int) -> int:
        return int(self.call("eth_getBlockByNumber", [hex(number), False])["timestamp"], 16)

    def get_logs(self, address: Optional[str], topic0: str, from_block: int, to_block: int) -> list:
        flt = {"topics": [topic0], "fromBlock": hex(from_block), "toBlock": hex(to_block)}
        if address:
            flt["address"] = address
        return self.call("eth_getLogs", [flt])


def block_at(client, ts: int, lo: int = 1, hi: Optional[int] = None) -> int:
    """Last block whose timestamp is <= ts (binary search)."""
    hi = client.block_number() if hi is None else hi
    if client.block_timestamp(hi) <= ts:
        return hi
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if client.block_timestamp(mid) <= ts:
            lo = mid
        else:
            hi = mid - 1
    return lo


def get_logs_adaptive(client, address: Optional[str], topic0: str, lo: int, hi: int, window: int = 5_000) -> Tuple[list, int]:
    """All logs in [lo, hi]; halves the block window on 'too many logs' (and stops growing for this range),
    doubles it while results stay sparse."""
    logs: list = []
    a = lo
    can_grow = True
    while a <= hi:
        b = min(a + window - 1, hi)
        try:
            part = client.get_logs(address, topic0, a, b)
        except RpcError as err:
            if not err.too_many_logs or window == 1:
                raise
            window = max(1, window // 2)
            can_grow = False
            continue
        logs.extend(part)
        a = b + 1
        if can_grow and len(part) < LOG_LIMIT // 4:
            window = min(window * 2, MAX_WINDOW)
    return logs, window


def _word(data: bytes, i: int, signed: bool = False) -> int:
    return int.from_bytes(data[32 * i: 32 * (i + 1)], "big", signed=signed)


def decode_vol_log(entry: dict) -> dict:
    data = bytes.fromhex(entry["data"][2:])
    if len(data) != 9 * 32:
        raise ValueError(f"unexpected VolDataUpdated payload of {len(data)} bytes")
    return {
        "block": int(entry["blockNumber"], 16),
        "block_ts": int(entry["blockTimestamp"], 16) if entry.get("blockTimestamp") else -1,  # push time
        "log_index": int(entry["logIndex"], 16),
        "expiry": int(entry["topics"][1], 16),
        "feed_ts": _word(data, 8),
        "svi_a": _word(data, 0, True) / E18,
        "svi_b": _word(data, 1) / E18,
        "svi_rho": _word(data, 2, True) / E18,
        "svi_m": _word(data, 3, True) / E18,
        "svi_sigma": _word(data, 4) / E18,
        "svi_fwd": _word(data, 5) / E18,
        "svi_ref_tau": _word(data, 6) / E18,
        "confidence": _word(data, 7) / E18,
    }


def logs_to_frame(entries: list) -> pd.DataFrame:
    df = pd.DataFrame([decode_vol_log(e) for e in entries], columns=COLUMNS)
    dtypes = {"block": "int64", "block_ts": "int64", "log_index": "int32", "expiry": "int64", "feed_ts": "int64", "svi_fwd": "float64"}
    dtypes.update({c: "float32" for c in FLOAT32})
    return df.astype(dtypes)


def chunk_path(out_dir: Path, start: int, end: int) -> Path:
    return out_dir / f"{start:09d}_{end:09d}.parquet"


def feed_chunks(from_block: int, to_block: int) -> List[Tuple[int, int]]:
    first = from_block - from_block % CHUNK_BLOCKS
    return [(s, min(s + CHUNK_BLOCKS - 1, to_block)) for s in range(first, to_block + 1, CHUNK_BLOCKS)]


def sync_feed(client, currency: str, out_root: Path, to_block: int, *, workers: int = 4, window: int = 5_000) -> dict:
    """Fetch every missing chunk of one feed up to ``to_block``; each chunk is written atomically."""
    spec = VOL_FEEDS[currency]
    out_dir = out_root / currency
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks = feed_chunks(spec["from_block"], to_block)
    todo = [c for c in chunks if not chunk_path(out_dir, *c).exists()]
    log.info("%s: %d chunks, %d to fetch", currency, len(chunks), len(todo))
    t0 = time.time()
    events = 0

    def run(chunk: Tuple[int, int]) -> int:
        logs, _ = get_logs_adaptive(client, spec["address"], VOL_DATA_UPDATED, chunk[0], chunk[1], window)
        frame = logs_to_frame(logs)
        path = chunk_path(out_dir, *chunk)
        tmp = path.with_suffix(".tmp")
        frame.to_parquet(tmp, index=False, compression="zstd")
        tmp.replace(path)
        return len(frame)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run, c) for c in todo]
        for i, fut in enumerate(as_completed(futures), 1):
            events += fut.result()
            if i % 20 == 0 or i == len(futures):
                elapsed = max(time.time() - t0, 1e-9)
                log.info("%s: %d/%d chunks, %d events, %.0f events/s", currency, i, len(futures), events, events / elapsed)
    return {"currency": currency, "to_block": to_block, "chunks": len(chunks), "fetched": len(todo), "events_fetched": events}


def load_feed(out_root: Path, currency: str) -> pd.DataFrame:
    """All chunks of one feed; for chunks with the same start the one reaching furthest wins."""
    best: Dict[int, Tuple[int, Path]] = {}
    for path in (out_root / currency).glob("*.parquet"):
        start, end = (int(x) for x in path.stem.split("_"))
        if start not in best or end > best[start][0]:
            best[start] = (end, path)
    frames = [pd.read_parquet(best[s][1]) for s in sorted(best)]
    if not frames:
        return logs_to_frame([])
    df = pd.concat(frames, ignore_index=True).drop_duplicates(["block", "log_index"])
    return df.sort_values(["expiry", "feed_ts", "block", "log_index"]).reset_index(drop=True)


def compact_feed(out_root: Path, currency: str, dest_dir: Path) -> dict:
    """Monthly files ``<CCY>_svi_<YYYY-MM>.parquet`` (month of the feed timestamp)."""
    df = load_feed(out_root, currency)
    dest_dir.mkdir(parents=True, exist_ok=True)
    month = pd.to_datetime(df["feed_ts"], unit="s", utc=True).dt.strftime("%Y-%m")
    counts = {}
    for m, g in df.groupby(month):
        g.reset_index(drop=True).to_parquet(dest_dir / f"{currency}_svi_{m}.parquet", index=False, compression="zstd")
        counts[m] = int(len(g))
    return counts


def svi_vol(strike, svi_a, svi_b, svi_rho, svi_m, svi_sigma, svi_fwd, svi_ref_tau) -> np.ndarray:
    """Mark vol exactly as ``LyraVolFeed.getVol`` computes it (vectorised); nan where the contract reverts."""
    a, b, rho, m, sig, fwd, tau, K = (np.asarray(x, dtype=float) for x in
                                      (svi_a, svi_b, svi_rho, svi_m, svi_sigma, svi_fwd, svi_ref_tau, strike))
    base = a + b * sig
    bound = 4.0 * np.sqrt(np.maximum(base, 0.0))
    with np.errstate(divide="ignore"):
        k = np.clip(np.log(K / fwd), -bound, bound)
    km = k - m
    w = np.minimum(a + b * (np.sqrt(km * km + sig * sig) + rho * km), 144.0)
    ok = (base >= 0) & (w >= 0) & (tau > 0)
    return np.where(ok, np.sqrt(np.where(ok, w, 0.0) / np.where(tau > 0, tau, 1.0)), np.nan)


def scan_emitters(client, blocks: List[int], span: int = 300) -> pd.DataFrame:
    """Every address that emitted VolDataUpdated in [b, b + span] for each sample block b."""
    rows = []
    for b in blocks:
        for entry in client.get_logs(None, VOL_DATA_UPDATED, b, b + span):
            d = decode_vol_log(entry)
            rows.append({"sample_block": b, "address": entry["address"].lower(), "svi_fwd": d["svi_fwd"], "feed_ts": d["feed_ts"]})
    df = pd.DataFrame(rows, columns=["sample_block", "address", "svi_fwd", "feed_ts"])
    return (df.groupby(["sample_block", "address"])
              .agg(n=("svi_fwd", "size"), fwd=("svi_fwd", "median"), ts=("feed_ts", "max"))
              .reset_index())
