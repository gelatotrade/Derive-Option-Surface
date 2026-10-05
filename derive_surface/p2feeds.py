"""Feed history for Paper 2: spot, forward, PM2 rate and perp pushes on Derive Chain 957, and the market state the
margin engines see at any point in time.

Every Lyra feed stores the last accepted signed update and emits one event per accepted update (updates with an older
or equal signing time are ignored without an event), so the storage of a feed after block B is fully described by its
last event up to B. The events (v2-core ``src/interfaces``, topics checked against real logs, see tests/fixtures/p2):

* ``SpotPriceUpdated(uint96 spot, uint96 confidence, uint64 timestamp)`` (``LyraSpotFeed``)
* ``ForwardDataUpdated(uint64 indexed expiry, (int96 fwdSpotDifference, uint64 confidence, uint64 timestamp),
  (uint256 settlementStartAggregate, uint256 currentSpotAggregate))`` (``LyraForwardFeed``)
* ``RateUpdated(uint64 indexed expiry, int96 rate, uint96 confidence, uint64 timestamp)`` (``LyraRateFeed``, PM2)
* ``SpotDiffUpdated(int96 spotDiff, uint96 confidence, uint64 timestamp)`` (``LyraSpotDiffFeed``, the perp price feed
  behind ``PerpAsset.perpFeed()``)
* ``RateUpdated(int64 rate, uint64 confidence)`` (legacy-PM rate feed; a static feed that was set once to 0)

Values in the compacted files (``data/p2/feeds/{CCY}_{kind}.parquet``) are floats in USD (rates as decimals):
spot = price, forward = ``fwdSpotDifference`` plus ``fixed`` (settlement portion, see below), rate_pm2 = rate per
expiry, perp = ``spotDiff``, rate_pm = static rate. ``feed_ts`` is the signing time the contracts check staleness on.

Forward exactly as ``LyraForwardFeed.getForwardPricePortions``: variable = spot + fwdSpotDifference with the *current*
spot; if the forward push was signed less than 30 min (``SETTLEMENT_TWAP_DURATION``) before expiry, the fixed portion is
(currentSpotAggregate - settlementStartAggregate) / 1800 and the variable portion is scaled by (expiry - ts) / 1800.
Perp exactly as ``LyraSpotDiffFeed.getResult``: spot + spotDiff clipped to ±spotDiffCap·spot (cap 0.06 on all three
feeds since deploy, the only ``SpotDiffCapUpdated`` events are the ones at deploy).
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .chainfeeds import RpcError, svi_vol
from .p2chain import ANCHOR_BLOCK, Rpc, block_at_ts, ts_at_block
from .p2types import ExpiryState, MarketState

log = logging.getLogger(__name__)

FEEDS_DIR = Path("data/p2/feeds")
RAW_DIR = FEEDS_DIR / "raw"
VOLFEED_DIR = Path("data/p1/volfeed")
LOG_PATH = Path("data/p2/logs/A1.jsonl")

# 2026-09-17 12:00:00 UTC (pilot cut of Paper 1) is block 44 812 392; the load runs to 13:26:55 UTC as a buffer.
TO_BLOCK = 44_815_000
FILL_START_BLOCK = ANCHOR_BLOCK  # 2024-01-11 00:00:01 UTC, first day of the Paper 1 sample

# keccak256 of the event signatures (computed once with eth_hash, confirmed on real logs in tests/fixtures/p2)
SPOT_PRICE_UPDATED = "0xbd86cbf2ccd8e501428ca22429126186e6ed6c5287f2be73152c58bae94f4183"  # SpotPriceUpdated(uint96,uint96,uint64)
FORWARD_DATA_UPDATED = "0x9f896aba44d86664403ab1344cde140b477c830d6ceda60ae36c1e7132fd2686"  # ForwardDataUpdated(uint64,(int96,uint64,uint64),(uint256,uint256))
RATE_UPDATED = "0xf00d73eebf231f5bfbe60b1882b53b782160a5c8c38e1f1cb26470fdde355768"  # RateUpdated(uint64,int96,uint96,uint64)
SPOT_DIFF_UPDATED = "0x248fe0fb2a38847211f28b18cd0417aa0a9b2259a16e92e793ba97887eb5d951"  # SpotDiffUpdated(int96,uint96,uint64)
STATIC_RATE_UPDATED = "0x203d3e59e9d6dd4310ba6d0a2b518dea62d541573ba6f674aec647220186c946"  # RateUpdated(int64,uint64)
TOPICS = {"spot": SPOT_PRICE_UPDATED, "forward": FORWARD_DATA_UPDATED, "rate_pm2": RATE_UPDATED,
          "perp": SPOT_DIFF_UPDATED, "rate_pm": STATIC_RATE_UPDATED}
KINDS = ("spot", "forward", "rate_pm2", "perp", "rate_pm")

# function selectors (first 4 bytes of keccak256 of the signature)
SEL_GET_SPOT = "0x2b37269c"             # getSpot()
SEL_GET_FORWARD_PRICE = "0xb34f2e36"    # getForwardPrice(uint64)
SEL_GET_INTEREST_RATE = "0xb0487ff6"    # getInterestRate(uint64)
SEL_GET_PERP_PRICE = "0x90f76b18"       # getPerpPrice()
SEL_AGGREGATE3 = "0x82ad56cb"           # aggregate3((address,bool,bytes)[])
MULTICALL3 = "0xcA11bde05977b3631167028862bE2a173976CA11"  # code on Chain 957 from about block 2 000 000

SETTLEMENT_TWAP = 1800   # LyraForwardFeed.SETTLEMENT_TWAP_DURATION
PERP_DIFF_CAP = 0.06     # LyraSpotDiffFeed.spotDiffCap of the BTC, ETH and HYPE perp feeds (SpotDiffCapUpdated at deploy)
HEARTBEAT = {"spot": 180, "forward": 3600, "vol": 1200, "rate_pm2": 43200, "perp": 1200}  # heartbeat() at block 44 812 000

# Addresses: SRM oracles (OraclesSet, unchanged since deploy), PM/PM2 interestRateFeed(), PerpAsset.perpFeed()
# (PerpFeedUpdated only at deploy). Sources: data/p2/kontext/margin-historie/{deploy,addresses_head}.json and eth_call
# on 2026-09-24. Deploy blocks from eth_getCode bisection (deploy.json) or the constructor event of the feed.
FEEDS: Dict[str, dict] = {
    "BTC": {
        "spot": "0x5eb59391e7870807ad2c8792e8c5e75838e0fdb0",
        "forward": "0x958c54bfacc0e2dee586564b31bf3f171f256279",
        "vol": "0x388341d9e5a7d7d5accd738b2a31b0622e0c1b87",
        "rate_pm2": "0x37d299d9d83186b6043e68c00d58b1f59c965461",
        "rate_pm": "0x6fef1bb8ade9a836663d4c15afd5985fb545004f",
        "perp": "0x34bc7fe1965b4e9f4071b69f2e60b8dc88f34475",
        "perp_asset": "0xdba83c0c654db1cd914fa2710ba743e925b53086",
        "deploy": {"spot": 843_075, "forward": 843_075, "vol": 843_076, "rate_pm2": 24_712_333, "rate_pm": 843_076,
                   "perp": 843_076},
    },
    "ETH": {
        "spot": "0x727ad65db6ae99db5dbee8f202846dd6009bf6d5",
        "forward": "0x791a570f5785fbdb02ea5c7a794c43111ae2f948",
        "vol": "0xb27cb6b08e6c298c8634d73d5f6649665e90d160",
        "rate_pm2": "0x14062edef4e2b7bd5399929e014a271a22df77e3",
        "rate_pm": "0x30a6e6a3851c18aa67429acc8a1dfafe20a29feb",
        "perp": "0x33e18f4f508d7ad3e958aa2dcf4b3ecaec38d7c6",
        "perp_asset": "0xaf65752c4643e25c02f693f9d4fe19cf23a095e3",
        "deploy": {"spot": 843_059, "forward": 843_059, "vol": 843_059, "rate_pm2": 24_712_300, "rate_pm": 843_059,
                   "perp": 843_059},
    },
    "HYPE": {
        "spot": "0x4fdec4f8cfa5bddedbc60338516f3cb6ba03b143",
        "forward": "0x0f79fa7bd5c098b99743a9714bcd11f219c9b695",
        "vol": "0x481916590863053ea2d8f21b64ee9429820512d1",
        "rate_pm2": "0x18522e5d09f3a6964fc094c230bfcb1ab27e0f17",
        "rate_pm": None,  # HYPE never had a legacy portfolio manager
        "perp": "0x947eb7b730eaf6a76dd7374eb443e6c5fc51503b",
        "perp_asset": "0x4890cd16569a961814d277b07f3a4517dc08bcd2",
        "deploy": {"spot": 30_293_595, "forward": 30_294_426, "vol": 30_294_429, "rate_pm2": 30_294_452,
                   "perp": 30_294_378},
    },
}

CHUNK_BLOCKS = 250_000
MAX_WINDOW = 2_000_000
TARGET_LOGS = 8_000        # the node refuses more than 10 000 logs per request
E18 = 10 ** 18
BASE_COLUMNS = ["block", "block_ts", "log_index", "expiry", "value", "confidence", "feed_ts"]
SVI_COLUMNS = ["block", "block_ts", "log_index", "expiry", "feed_ts", "svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma",
               "svi_fwd", "svi_ref_tau", "confidence"]


def columns(kind: str) -> List[str]:
    return BASE_COLUMNS + (["fixed"] if kind == "forward" else [])


# ---------------------------------------------------------------- decoding

def _words(data_hex: str) -> List[int]:
    h = data_hex[2:] if data_hex.startswith("0x") else data_hex
    return [int(h[i:i + 64], 16) for i in range(0, len(h), 64)]


def _signed(x: int) -> int:
    return x - (1 << 256) if x >= (1 << 255) else x


_N_WORDS = {"spot": 3, "forward": 5, "rate_pm2": 3, "perp": 3, "rate_pm": 2}


def decode_log(kind: str, entry: dict) -> dict:
    """One feed event as a row: block, block_ts, log_index, expiry, value, confidence, feed_ts (+ fixed for forward)."""
    w = _words(entry["data"])
    if len(w) != _N_WORDS[kind]:
        raise ValueError(f"{kind}: unexpected payload of {len(w)} words")
    block = int(entry["blockNumber"], 16)
    block_ts = int(entry["blockTimestamp"], 16) if entry.get("blockTimestamp") else ts_at_block(block)
    row = {"block": block, "block_ts": block_ts, "log_index": int(entry["logIndex"], 16), "expiry": 0}
    if kind == "spot":
        row.update(value=w[0] / E18, confidence=w[1] / E18, feed_ts=w[2])
    elif kind == "perp":
        row.update(value=_signed(w[0]) / E18, confidence=w[1] / E18, feed_ts=w[2])
    elif kind == "rate_pm2":
        row.update(expiry=int(entry["topics"][1], 16), value=_signed(w[0]) / E18, confidence=w[1] / E18, feed_ts=w[2])
    elif kind == "forward":
        # settlement aggregates are only non-zero for pushes signed inside the last 30 min before expiry
        fixed = max(w[4] - w[3], 0) // SETTLEMENT_TWAP
        row.update(expiry=int(entry["topics"][1], 16), value=_signed(w[0]) / E18, confidence=w[1] / E18, feed_ts=w[2],
                   fixed=fixed / E18)
    elif kind == "rate_pm":
        row.update(value=_signed(w[0]) / E18, confidence=w[1] / E18, feed_ts=block_ts)
    else:
        raise ValueError(kind)
    return row


def _typed(df: pd.DataFrame, kind: str) -> pd.DataFrame:
    dtypes = {"block": "int64", "block_ts": "int64", "log_index": "int32", "expiry": "int64", "value": "float64",
              "confidence": "float64", "feed_ts": "int64"}
    if kind == "forward":
        dtypes["fixed"] = "float64"
    return df.astype(dtypes)


def logs_to_frame(kind: str, entries: Sequence[dict]) -> pd.DataFrame:
    return _typed(pd.DataFrame([decode_log(kind, e) for e in entries], columns=columns(kind)), kind)


# ---------------------------------------------------------------- contract arithmetic

def forward_portions_int(spot: int, diff: int, feed_ts: int, expiry: int, start_agg: int, cur_agg: int) -> Tuple[int, int]:
    """``LyraForwardFeed._getSettlementPricePortions`` in exact 1e18 integer arithmetic: (fixed, variable)."""
    variable = spot + diff
    if variable < 0:
        raise ValueError("SafeCast: negative forward")
    if expiry - feed_ts >= SETTLEMENT_TWAP:
        return 0, variable
    fixed = (cur_agg - start_agg) // SETTLEMENT_TWAP
    return fixed, variable * (expiry - feed_ts) // SETTLEMENT_TWAP


def forward_price(spot, diff, feed_ts, expiry, fixed):
    """Vectorised forward = fixed + variable in USD; nan where spot or forward data is missing."""
    spot, diff, feed_ts, expiry, fixed = (np.asarray(x, dtype=float) for x in (spot, diff, feed_ts, expiry, fixed))
    variable = spot + diff
    remaining = expiry - feed_ts
    with np.errstate(invalid="ignore"):
        settling = remaining < SETTLEMENT_TWAP
    return np.where(settling, fixed + variable * remaining / SETTLEMENT_TWAP, variable)


def perp_price(spot, diff, cap: float = PERP_DIFF_CAP):
    """``LyraSpotDiffFeed.getResult``: spot + spotDiff, the difference capped at ±cap·spot."""
    spot, diff = np.asarray(spot, dtype=float), np.asarray(diff, dtype=float)
    bound = spot * cap
    return spot + np.minimum(np.maximum(diff, -bound), bound)


# ---------------------------------------------------------------- download

def fetch_logs(rpc, address: str, topic0: str, lo: int, hi: int, window: int = 20_000,
               target: int = TARGET_LOGS) -> Tuple[list, int]:
    """All logs of one topic in [lo, hi]. The block window follows the observed log density towards ``target`` logs per
    request and is halved when the node refuses a range (more than 10 000 logs)."""
    out: list = []
    a = lo
    while a <= hi:
        b = min(a + window - 1, hi)
        flt = {"address": address, "topics": [topic0], "fromBlock": hex(a), "toBlock": hex(b)}
        try:
            part = rpc.raw("eth_getLogs", [flt])
        except RpcError as err:
            if not err.too_many_logs or b == a:
                raise
            window = max(1, (b - a + 1) // 2)
            continue
        out.extend(part)
        span = b - a + 1
        a = b + 1
        window = int(min(max(span * target / len(part), 1), MAX_WINDOW)) if part else min(span * 4, MAX_WINDOW)
    return out, window


def raw_path(raw_dir: Path, ccy: str, kind: str, start: int, end: int) -> Path:
    return Path(raw_dir) / ccy / kind / f"{start:09d}_{end:09d}.parquet"


def chunks(ccy: str, kind: str, to_block: int) -> List[Tuple[int, int, int]]:
    """(first block to fetch, grid start, grid end) of every chunk from the feed's deploy block to ``to_block``."""
    lo = FEEDS[ccy]["deploy"][kind]
    first = lo - lo % CHUNK_BLOCKS
    return [(max(s, lo), s, min(s + CHUNK_BLOCKS - 1, to_block)) for s in range(first, to_block + 1, CHUNK_BLOCKS)]


def sync(ccy: str, kind: str, to_block: int = TO_BLOCK, *, rpc=None, raw_dir: Path = RAW_DIR,
         max_seconds: Optional[float] = None, target: int = TARGET_LOGS, part: Tuple[int, int] = (0, 1)) -> dict:
    """Fetch every missing chunk of one feed up to ``to_block``; each chunk is written atomically, so the download can
    be interrupted and resumed. Stops after the chunk that crosses ``max_seconds`` (always fetches at least one).
    ``part=(k, n)`` takes only every n-th chunk starting at k, so n processes can share one feed."""
    address = FEEDS[ccy].get(kind)
    info = {"ccy": ccy, "kind": kind, "to_block": to_block, "fetched": 0, "events": 0}
    if address is None:
        return dict(info, chunks=0, remaining=0, done=True)
    rpc = rpc or Rpc(rate=2.0, log_path=LOG_PATH)
    k, n = part
    todo = [c for i, c in enumerate(chunks(ccy, kind, to_block))
            if i % n == k and not raw_path(raw_dir, ccy, kind, c[1], c[2]).exists()]
    t0 = time.monotonic()
    window = 20_000
    for lo, start, end in todo:
        entries, window = fetch_logs(rpc, address, TOPICS[kind], lo, end, window, target)
        frame = logs_to_frame(kind, entries)
        path = raw_path(raw_dir, ccy, kind, start, end)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        frame.to_parquet(tmp, index=False, compression="zstd")
        tmp.replace(path)
        info["fetched"] += 1
        info["events"] += len(frame)
        log.info("%s %s: %d-%d %d events (%.0f s)", ccy, kind, lo, end, len(frame), time.monotonic() - t0)
        if max_seconds is not None and time.monotonic() - t0 >= max_seconds:
            break
    all_chunks = chunks(ccy, kind, to_block)
    remaining = sum(not raw_path(raw_dir, ccy, kind, c[1], c[2]).exists() for c in all_chunks)
    return dict(info, chunks=len(all_chunks), remaining=remaining, done=remaining == 0,
                seconds=round(time.monotonic() - t0, 1))


def load_raw(ccy: str, kind: str, raw_dir: Path = RAW_DIR) -> Tuple[pd.DataFrame, List[Tuple[int, int]]]:
    """All raw chunks of one feed (for chunks with the same start the one reaching furthest wins) and their ranges."""
    best: Dict[int, Tuple[int, Path]] = {}
    for path in (Path(raw_dir) / ccy / kind).glob("*.parquet"):
        start, end = (int(x) for x in path.stem.split("_"))
        if start not in best or end > best[start][0]:
            best[start] = (end, path)
    ranges = [(s, best[s][0]) for s in sorted(best)]
    frames = [pd.read_parquet(best[s][1]) for s in sorted(best)]
    frames = [f for f in frames if len(f)]
    if not frames:
        return _typed(pd.DataFrame(columns=columns(kind)), kind), ranges
    df = pd.concat(frames, ignore_index=True).drop_duplicates(["block", "log_index"])
    return df.sort_values(["expiry", "block", "log_index"], kind="mergesort").reset_index(drop=True), ranges


def compact(ccy: str, kind: str, *, raw_dir: Path = RAW_DIR, out_dir: Path = FEEDS_DIR) -> dict:
    """One file ``{CCY}_{kind}.parquet`` per feed, sorted by (expiry, block, log_index), with a coverage report."""
    df, ranges = load_raw(ccy, kind, raw_dir)
    gaps = [(a[1] + 1, b[0] - 1) for a, b in zip(ranges, ranges[1:]) if b[0] != a[1] + 1]
    expected_ts = ts_at_block(0) + 2 * df["block"].to_numpy(dtype=np.int64)
    out = Path(out_dir) / f"{ccy}_{kind}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    df.to_parquet(tmp, index=False, compression="zstd", row_group_size=1_000_000)
    tmp.replace(out)
    return {"ccy": ccy, "kind": kind, "rows": int(len(df)), "path": str(out),
            "first_block": int(df["block"].min()) if len(df) else None,
            "last_block": int(df["block"].max()) if len(df) else None,
            "covered": [max(ranges[0][0], FEEDS[ccy]["deploy"][kind]), ranges[-1][1]] if ranges else None, "gaps": gaps,
            "expiries": int(df["expiry"].nunique()), "block_ts_mismatch": int((df["block_ts"].to_numpy() != expected_ts).sum()),
            "feed_ts_after_block": int((df["feed_ts"] > df["block_ts"]).sum())}


# ---------------------------------------------------------------- history lookups

@dataclass(frozen=True)
class FeedExpiryState(ExpiryState):
    """:class:`ExpiryState` plus the two feed fields the PM engines read when present: the fixed forward portion of the
    30-min settlement window (``getForwardPricePortions``, USD, 0 outside the window) and the rate feed confidence."""

    fwd_fixed: float = 0.0
    rate_conf: float = 1.0


def _window(df: pd.DataFrame, start_ts: Optional[int], end_ts: Optional[int]) -> pd.DataFrame:
    """Rows with block_ts in [start_ts, end_ts] plus, per expiry, the last row before start_ts (exact state at start)."""
    if end_ts is not None:
        df = df[df["block_ts"] <= end_ts]
    if start_ts is not None:
        before = df["block_ts"] < start_ts
        last = df[before].sort_values(["expiry", "block", "log_index"], kind="mergesort").groupby("expiry").tail(1)
        df = pd.concat([last, df[~before]], ignore_index=True)
    return df


def _is_sorted(df: pd.DataFrame) -> bool:
    """True if rows are strictly increasing in (expiry, block, log_index) (compacted files are)."""
    e = df["expiry"].to_numpy(dtype=np.int64)
    b = (df["block"].to_numpy(dtype=np.int64) << 20) | df["log_index"].to_numpy(dtype=np.int64)
    return bool(np.all((e[1:] > e[:-1]) | ((e[1:] == e[:-1]) & (b[1:] > b[:-1]))))


class _Feed:
    """Pushes of one feed sorted by (expiry, block, log_index) with a (expiry code, block_ts) search key."""

    def __init__(self, df: Optional[pd.DataFrame], cols: Sequence[str]):
        if df is None or len(df) == 0:
            self.expiries = np.zeros(0, dtype=np.int64)
            self.key = np.zeros(0, dtype=np.int64)
            self.cols = {c: np.zeros(0) for c in cols}
            return
        if not _is_sorted(df):
            df = df.sort_values(["expiry", "block", "log_index"], kind="mergesort")
        expiry = df["expiry"].to_numpy(dtype=np.int64)
        self.expiries = np.unique(expiry)
        code = np.searchsorted(self.expiries, expiry).astype(np.int64)
        self.key = (code << 32) | df["block_ts"].to_numpy(dtype=np.int64)
        self.cols = {c: df[c].to_numpy() for c in cols}

    def locate(self, expiry: np.ndarray, ts: np.ndarray) -> np.ndarray:
        """Row of the last push with block_ts <= ts for each (expiry, ts); -1 where there is none."""
        expiry = np.asarray(expiry, dtype=np.int64)
        ts = np.asarray(ts, dtype=np.int64)
        if len(self.expiries) == 0:
            return np.full(len(ts), -1, dtype=np.int64)
        code = np.minimum(np.searchsorted(self.expiries, expiry), len(self.expiries) - 1).astype(np.int64)
        known = self.expiries[code] == expiry
        idx = np.searchsorted(self.key, (code << 32) | ts, side="right") - 1
        ok = known & (idx >= 0)
        ok[ok] &= (self.key[idx[ok]] >> 32) == code[ok]
        return np.where(ok, idx, -1)

    def take(self, col: str, idx: np.ndarray, fill: float = np.nan) -> np.ndarray:
        vals = self.cols[col]
        out = np.full(len(idx), fill, dtype=float)
        hit = idx >= 0
        out[hit] = vals[idx[hit]]
        return out


def _read_feed(path: Path, kind: str, start_ts: Optional[int], end_ts: Optional[int]) -> pd.DataFrame:
    if not path.exists():
        return _typed(pd.DataFrame(columns=columns(kind)), kind)
    filters = [("block_ts", "<=", int(end_ts))] if end_ts is not None else None
    return _window(pd.read_parquet(path, filters=filters), start_ts, None)


def _read_svi(volfeed_dir: Path, ccy: str, start_ts: Optional[int], end_ts: Optional[int]) -> pd.DataFrame:
    """SVI pushes of Paper 1 (monthly files by feed_ts month; feed_ts <= block_ts, so later months can be skipped)."""
    parts = []
    for path in sorted(Path(volfeed_dir).glob(f"{ccy}_svi_*.parquet")):
        month_start = pd.Timestamp(path.stem.split("_")[-1] + "-01", tz="UTC").timestamp()
        if end_ts is not None and month_start > end_ts:
            continue
        parts.append(_window(pd.read_parquet(path, columns=SVI_COLUMNS), start_ts, end_ts))
    if not parts:
        return pd.DataFrame(columns=SVI_COLUMNS)
    return _window(pd.concat(parts, ignore_index=True).drop_duplicates(["block", "log_index"]), start_ts, end_ts)


class FeedHistory:
    """Market state of one currency at any time: for every feed the last push with block_ts <= ts.

    ``frames`` (keys spot, forward, rate_pm2, perp, rate_pm, svi) replaces the files, e.g. in tests. ``start_ts`` and
    ``end_ts`` restrict loading to a window without changing any state inside it (memory: a full BTC history with SVI
    needs a few GB, a monthly window a few hundred MB). ``with_svi=False`` skips the vol feed.
    """

    def __init__(self, ccy: str, *, feeds_dir: Path = FEEDS_DIR, volfeed_dir: Path = VOLFEED_DIR,
                 frames: Optional[Dict[str, pd.DataFrame]] = None, start_ts: Optional[int] = None,
                 end_ts: Optional[int] = None, perp_cap: float = PERP_DIFF_CAP, with_svi: bool = True):
        self.ccy, self.perp_cap = ccy, perp_cap
        if frames is None:
            frames = {k: _read_feed(Path(feeds_dir) / f"{ccy}_{k}.parquet", k, start_ts, end_ts)
                      for k in ("spot", "forward", "rate_pm2", "perp", "rate_pm")}
            if with_svi:
                frames["svi"] = _read_svi(volfeed_dir, ccy, start_ts, end_ts)
        else:
            frames = {k: _window(v, start_ts, end_ts) for k, v in frames.items() if with_svi or k != "svi"}
        self.spot = _Feed(frames.pop("spot", None), ["value", "confidence", "feed_ts"])
        self.forward = _Feed(frames.pop("forward", None), ["value", "confidence", "feed_ts", "fixed"])
        self.rate = _Feed(frames.pop("rate_pm2", None), ["value", "confidence", "feed_ts"])
        self.perp = _Feed(frames.pop("perp", None), ["value", "confidence", "feed_ts"])
        self.rate_pm = _Feed(frames.pop("rate_pm", None), ["value"])
        self.svi = _Feed(frames.pop("svi", None), ["svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma", "svi_fwd",
                                                   "svi_ref_tau", "confidence", "feed_ts"])

    def _core(self, ts: np.ndarray, expiry: np.ndarray) -> Dict[str, np.ndarray]:
        ts = np.asarray(ts, dtype=np.int64)
        expiry = np.asarray(expiry, dtype=np.int64)
        tsf = ts.astype(float)
        out: Dict[str, np.ndarray] = {}
        i = self.spot.locate(np.zeros_like(expiry), ts)
        spot, spot_conf = self.spot.take("value", i), self.spot.take("confidence", i)
        out.update(spot=spot, spot_conf=spot_conf, spot_age=tsf - self.spot.take("feed_ts", i))
        i = self.forward.locate(expiry, ts)
        fwd_ts = self.forward.take("feed_ts", i)
        fixed = self.forward.take("fixed", i, 0.0)
        out["forward"] = forward_price(spot, self.forward.take("value", i), fwd_ts, expiry, fixed)
        with np.errstate(invalid="ignore"):
            out["fwd_fixed"] = np.where(expiry - fwd_ts < SETTLEMENT_TWAP, fixed, 0.0)
        out["fwd_conf"] = np.minimum(self.forward.take("confidence", i), spot_conf)
        out["fwd_age"] = tsf - fwd_ts
        i = self.rate.locate(expiry, ts)
        out["rate"] = self.rate.take("value", i, 0.0)
        out["rate_conf"] = self.rate.take("confidence", i, 1.0)
        out["rate_age"] = tsf - self.rate.take("feed_ts", i)
        out["rate_pm"] = self.rate_pm.take("value", self.rate_pm.locate(np.zeros_like(expiry), ts), 0.0)
        i = self.svi.locate(expiry, ts)
        for c in ("svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma", "svi_fwd", "svi_ref_tau"):
            out[c] = self.svi.take(c, i)
        out["vol_conf"] = self.svi.take("confidence", i)
        out["vol_age"] = tsf - self.svi.take("feed_ts", i)
        i = self.perp.locate(np.zeros_like(expiry), ts)
        out["perp"] = perp_price(spot, self.perp.take("value", i), self.perp_cap)
        out["perp_conf"] = np.minimum(self.perp.take("confidence", i), spot_conf)
        return out

    def bulk(self, ts, expiry, strike) -> pd.DataFrame:
        """Feed state for many (ts, expiry, strike) rows at once (ts in whole seconds: for fills ``ts_ms // 1000``, which
        selects exactly the pushes with ``block_ts * 1000 <= ts_ms``). sigma exactly as ``LyraVolFeed.getVol``; ages are
        ``ts - feed_ts`` of the value used (signing time, the clock of the contracts' staleness checks; Paper 1's
        ``svi_age_s_t`` counts from the push instead); nan where a feed has no value yet, rate 0 and rate_conf 1 then.
        Extra columns: perp, spot_conf, perp_conf, fwd_fixed, rate_conf and rate_pm (legacy-PM static rate)."""
        c = self._core(ts, expiry)
        with np.errstate(invalid="ignore", divide="ignore"):
            sigma = svi_vol(np.asarray(strike, dtype=float), c["svi_a"], c["svi_b"], c["svi_rho"], c["svi_m"],
                            c["svi_sigma"], c["svi_fwd"], c["svi_ref_tau"])
        return pd.DataFrame({"spot": c["spot"], "forward": c["forward"], "sigma": sigma, "rate": c["rate"],
                             "svi_fwd": c["svi_fwd"], "vol_conf": c["vol_conf"], "fwd_conf": c["fwd_conf"],
                             "spot_age": c["spot_age"], "fwd_age": c["fwd_age"], "vol_age": c["vol_age"],
                             "rate_age": c["rate_age"], "perp": c["perp"], "spot_conf": c["spot_conf"],
                             "perp_conf": c["perp_conf"], "fwd_fixed": c["fwd_fixed"], "rate_conf": c["rate_conf"],
                             "rate_pm": c["rate_pm"]})

    def state_at(self, ts: int, expiries: Iterable[int]) -> MarketState:
        exps = [int(e) for e in expiries]
        probe = exps or [0]
        c = self._core(np.full(len(probe), int(ts)), np.array(probe, dtype=np.int64))
        states = {}
        for j, e in enumerate(exps):
            has_svi = not np.isnan(c["svi_a"][j])
            svi = tuple(float(c[k][j]) for k in ("svi_a", "svi_b", "svi_rho", "svi_m", "svi_sigma", "svi_ref_tau")) \
                if has_svi else None
            states[e] = FeedExpiryState(expiry=e, forward=float(c["forward"][j]), svi=svi, rate=float(c["rate"][j]),
                                        vol_conf=float(c["vol_conf"][j]), fwd_conf=float(c["fwd_conf"][j]),
                                        svi_fwd=float(c["svi_fwd"][j]) if has_svi else None,
                                        fwd_fixed=float(c["fwd_fixed"][j]), rate_conf=float(c["rate_conf"][j]))
        perp = float(c["perp"][0])
        return MarketState(currency=self.ccy, ts=int(ts), spot=float(c["spot"][0]), expiries=states,
                           perp=None if np.isnan(perp) else perp, spot_conf=float(c["spot_conf"][0]),
                           perp_conf=float(c["perp_conf"][0]))

    def live_expiries(self, ts: int, max_age: int = HEARTBEAT["forward"]) -> List[int]:
        """Expiries after ts whose last forward push is at most ``max_age`` s old (getForwardPrice does not revert)."""
        e = self.forward.expiries[self.forward.expiries > ts]
        if len(e) == 0:
            return []
        i = self.forward.locate(e, np.full(len(e), ts))
        age = ts - self.forward.take("feed_ts", i)
        return [int(x) for x in e[(i >= 0) & (age <= max_age)]]


# ---------------------------------------------------------------- multicall and cross-check against eth_call

def _u256(x: int) -> str:
    return int(x).to_bytes(32, "big").hex()


def encode_aggregate3(calls: Sequence[Tuple[str, bool, str]]) -> str:
    """Calldata of Multicall3.aggregate3((address target, bool allowFailure, bytes callData)[])."""
    elems = []
    for target, allow_failure, data in calls:
        payload = bytes.fromhex(data[2:] if data.startswith("0x") else data)
        padded = payload + b"\x00" * (-len(payload) % 32)
        elems.append(_u256(int(target, 16)) + _u256(1 if allow_failure else 0) + _u256(96) + _u256(len(payload))
                     + padded.hex())
    offsets, pos = [], 32 * len(elems)
    for e in elems:
        offsets.append(_u256(pos))
        pos += len(e) // 2
    return SEL_AGGREGATE3 + _u256(32) + _u256(len(elems)) + "".join(offsets) + "".join(elems)


def decode_aggregate3(result: str) -> List[Tuple[bool, bytes]]:
    """Return value of aggregate3: (bool success, bytes returnData)[]."""
    raw = bytes.fromhex(result[2:] if result.startswith("0x") else result)

    def word(pos: int) -> int:
        return int.from_bytes(raw[pos:pos + 32], "big")

    base = word(0)
    n = word(base)
    head = base + 32
    out = []
    for k in range(n):
        el = head + word(head + 32 * k)
        boff = el + word(el + 32)
        size = word(boff)
        out.append((word(el) != 0, raw[boff + 32: boff + 32 + size]))
    return out


def multicall(rpc, calls: Sequence[Tuple[str, str]], block: int, batch: int = 80) -> List[Tuple[bool, bytes]]:
    """eth_calls bundled through Multicall3 at one block (failures allowed, e.g. stale feeds)."""
    out: List[Tuple[bool, bytes]] = []
    for k in range(0, len(calls), batch):
        part = [(to, True, data) for to, data in calls[k:k + batch]]
        res = rpc.raw("eth_call", [{"to": MULTICALL3, "data": encode_aggregate3(part)}, hex(int(block))])
        out.extend(decode_aggregate3(res))
    return out


def _pair(data: bytes, signed_first: bool = False) -> Tuple[int, int]:
    a, b = int.from_bytes(data[:32], "big"), int.from_bytes(data[32:64], "big")
    return (_signed(a) if signed_first else a), b


def crosscheck(ccy: str, n: int = 10, seed: int = 20260924, *, rpc=None, hist: Optional[FeedHistory] = None,
               lo_block: Optional[int] = None, hi_block: int = TO_BLOCK, blocks: Optional[Sequence[int]] = None) -> dict:
    """getSpot, getForwardPrice (all live expiries), getInterestRate (PM2 feed) and getPerpPrice per eth_call at n
    random blocks (or at the given ``blocks``) against ``state_at``."""
    rpc = rpc or Rpc(rate=2.0, log_path=LOG_PATH)
    hist = hist or FeedHistory(ccy, with_svi=False)
    f = FEEDS[ccy]
    lo = lo_block or max(FILL_START_BLOCK, f["deploy"]["forward"] + 43_200)
    if blocks is None:
        blocks = np.random.default_rng(seed).integers(lo, hi_block, n)
    blocks = sorted(int(b) for b in blocks)
    rows = []
    for block in blocks:
        ts = ts_at_block(block)
        exps = hist.live_expiries(ts)
        rate_live = block >= f["deploy"]["rate_pm2"]
        calls = [(f["spot"], SEL_GET_SPOT), (f["perp_asset"], SEL_GET_PERP_PRICE)]
        calls += [(f["forward"], SEL_GET_FORWARD_PRICE + _u256(e)) for e in exps]
        if rate_live:
            calls += [(f["rate_pm2"], SEL_GET_INTEREST_RATE + _u256(e)) for e in exps]
        res = multicall(rpc, calls, block)
        st = hist.state_at(ts, exps)

        def check(name, expiry, ok, data, mine, mine_conf, signed_first=False):
            row = {"block": block, "ts": ts, "what": name, "expiry": expiry, "ok": ok, "chain": None,
                   "replica": mine, "abs_dev": None, "rel_dev": None, "conf_equal": None}
            if ok:
                val, conf = _pair(data, signed_first)
                chain = val / E18
                row.update(chain=chain, abs_dev=abs(mine - chain), rel_dev=abs(mine - chain) / max(abs(chain), 1e-300),
                           conf_equal=bool(conf / E18 == mine_conf))
            rows.append(row)

        check("spot", 0, res[0][0], res[0][1], st.spot, st.spot_conf)
        check("perp", 0, res[1][0], res[1][1], st.perp if st.perp is not None else float("nan"), st.perp_conf)
        for k, e in enumerate(exps):
            ok, data = res[2 + k]
            check("forward", e, ok, data, st.expiries[e].forward, st.expiries[e].fwd_conf)
            if rate_live:
                ok, data = res[2 + len(exps) + k]
                check("rate", e, ok, data, st.expiries[e].rate, st.expiries[e].rate_conf, signed_first=True)
    df = pd.DataFrame(rows)
    summary = {"ccy": ccy, "blocks": blocks, "calls": int(len(df)), "reverted": int((~df["ok"]).sum())}
    for what, g in df[df["ok"]].groupby("what"):
        summary[what] = {"n": int(len(g)), "max_abs_dev": float(g["abs_dev"].max()), "max_rel_dev": float(g["rel_dev"].max()),
                         "exact": int((g["abs_dev"] == 0).sum()), "conf_equal": int(g["conf_equal"].sum())}
    summary["rows"] = rows
    return summary


# ---------------------------------------------------------------- command line

def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(prog="python3 -m derive_surface.p2feeds", description="Paper 2 feed history")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync", help="download feed events (resumable)")
    s.add_argument("--ccy", nargs="+", default=["BTC", "ETH", "HYPE"])
    s.add_argument("--kind", nargs="+", default=list(KINDS))
    s.add_argument("--to-block", type=int, default=TO_BLOCK)
    s.add_argument("--max-seconds", type=float, default=480.0)
    s.add_argument("--part", default="0/1", help="k/n: every n-th chunk starting at k")
    c = sub.add_parser("compact", help="write data/p2/feeds/{CCY}_{kind}.parquet")
    c.add_argument("--ccy", nargs="+", default=["BTC", "ETH", "HYPE"])
    c.add_argument("--kind", nargs="+", default=list(KINDS))
    x = sub.add_parser("crosscheck", help="state_at against eth_call at random blocks")
    x.add_argument("--ccy", nargs="+", default=["BTC", "ETH", "HYPE"])
    x.add_argument("--n", type=int, default=10)
    x.add_argument("--seed", type=int, default=20260924)
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if args.cmd == "sync":
        t0 = time.monotonic()
        rpc = Rpc(rate=2.0, log_path=LOG_PATH)
        for ccy in args.ccy:
            for kind in args.kind:
                left = args.max_seconds - (time.monotonic() - t0)
                if left <= 0:
                    print(json.dumps({"ccy": ccy, "kind": kind, "done": False, "note": "time budget used"}))
                    continue
                part = tuple(int(x) for x in args.part.split("/"))
                print(json.dumps(sync(ccy, kind, args.to_block, rpc=rpc, max_seconds=left, part=part)), flush=True)
    elif args.cmd == "compact":
        for ccy in args.ccy:
            for kind in args.kind:
                if FEEDS[ccy].get(kind) is None:
                    continue
                print(json.dumps(compact(ccy, kind)), flush=True)
    elif args.cmd == "crosscheck":
        for ccy in args.ccy:
            res = crosscheck(ccy, args.n, args.seed)
            out = FEEDS_DIR / f"crosscheck_{ccy}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(res, indent=1, default=float))
            print(json.dumps({k: v for k, v in res.items() if k != "rows"}, default=float), flush=True)


if __name__ == "__main__":
    main()
