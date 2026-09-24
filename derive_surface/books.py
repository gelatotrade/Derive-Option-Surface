"""On-chain books of the dominant maker subaccounts (Paper 2, task A5).

* ``top_maker_subaccounts``: the ten subaccounts with the most maker fills in the Paper 1 sample.
* ``decode_option_subid``: exact port of ``lyra-utils/encoding/OptionEncoding.fromSubId``.
* ``snapshot`` / ``snapshot_many``: ``SubAccounts.getAccountBalances`` and ``SubAccounts.manager`` per account at one
  block, bundled through Multicall3 ``aggregate3`` (one ``eth_call`` for many accounts).
* ``load_snapshots`` / ``compact``: resumable download of the day-start books (first block of every UTC day) into
  ``data/p2/books/raw/*.json`` and ``data/p2/books/snapshots.parquet``.
* ``book_at`` / ``book_before_fill``: preregistered book before a fill = day-start snapshot + the subaccount's tape
  fills of the day with an earlier timestamp than its own row of the fill (options only; perps stay at day start).
* ``reconcile_day``: day-start book + fills of the day against the next day-start book.
* ``decode_balance_adjusted`` / ``fetch_balance_events`` / ``load_events`` / ``compact_events``: ``BalanceAdjusted``
  events of ``SubAccounts`` per (subaccount, day), i.e. every balance change between two day-start snapshots.
* ``replay_balances`` / ``onchain_book_before`` / ``OnchainBooks``: exact on-chain book just before the fill's
  transaction = day-start snapshot + ``BalanceAdjusted`` events up to that transaction (options and perps).
* ``perp_drift`` / ``compare_books``: diagnostics of the tape-based book against the chain.

Raw subaccount ids stay under ``data/p2`` (git-ignored); anything written elsewhere uses ``sha10``.
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import hashlib
import heapq
import json
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .chainfeeds import LOG_LIMIT, RpcError
from .p2chain import Rpc, block_at_ts, ts_at_block
from .p2types import Book, OptionLeg

MARKOUTS = Path("data/p1/derived/markouts.parquet")
TAPE_DIR = Path("data/p1/tape")
KONTEXT = Path("data/p2/kontext/margin-historie")
BOOKS_DIR = Path("data/p2/books")
LOG_PATH = Path("data/p2/logs/A5.jsonl")
EVENTS_DIR = BOOKS_DIR / "events"

START_DAY = "2024-01-11"
END_DAY = "2026-09-17"
SAMPLE_CCYS = ("BTC", "ETH", "HYPE")

SUBACCOUNTS = "0xE7603DF191D699d8BD9891b821347dbAb889E5a5"  # SubAccounts (ERC721), = manager.subAccounts()
MULTICALL3 = "0xcA11bde05977b3631167028862bE2a173976CA11"   # code present on chain 957 from before block 2 454 793
ZERO_ADDRESS = "0x" + "00" * 20

# function selectors = keccak256(signature)[:4]
SEL_GET_ACCOUNT_BALANCES = "c7569701"  # getAccountBalances(uint256) -> (address asset, uint256 subId, int256 balance)[]
SEL_MANAGER = "52981457"               # manager(uint256) -> address
SEL_AGGREGATE3 = "82ad56cb"            # aggregate3((address target, bool allowFailure, bytes callData)[])
SEL_CASH_ASSET = "5cd93cf3"            # cashAsset() -> address (BaseManager)
# keccak256("BalanceAdjusted(uint256,address,bytes32,int256,int256,int256,uint256)"), ISubAccounts.sol
T_BALANCE_ADJUSTED = "0x503ec09c1b4597d114eca849f7013c8c457988802d1dc5da49a0c461b5f88658"

UINT32_MAX = 0xFFFFFFFF
UINT63_MAX = 0x7FFFFFFFFFFFFFFF
UINT96_MASK = (1 << 96) - 1
INT64_MAX = (1 << 63) - 1
AMOUNT_EPS = 1e-9        # contracts; below this a netted leg counts as closed
DAY_MS = 86_400_000

SNAPSHOT_COLUMNS = ["subaccount", "day", "block", "manager", "asset", "sub_id", "kind", "ccy", "expiry", "strike",
                    "is_call", "amount", "balance_raw", "manager_label"]
EVENT_COLUMNS = ["subaccount", "day", "block", "tx_index", "log_index", "tx_hash", "manager", "asset", "sub_id",
                 "amount_raw", "pre_raw", "post_raw", "trade_id", "amount"]


def sha10(x) -> str:
    return hashlib.sha256(str(x).encode()).hexdigest()[:10]


# ---------------------------------------------------------------- option sub ids (OptionEncoding.sol)

def decode_option_subid(sub_id: int) -> Tuple[int, float, bool]:
    """(expiry, strike, is_call) exactly as ``OptionEncoding.fromSubId(subId.toUint96())``.

    Layout ``[1 bit isCall][63 bits strike in 1e8][32 bits expiry]``; the 18-decimal strike ``s * 1e10`` is returned
    as the float ``s / 1e8``. Sub ids above uint96 revert on chain (SafeCast) and raise ``ValueError`` here.
    """
    sub = int(sub_id)
    if sub < 0 or sub >> 96:
        raise ValueError(f"sub id {sub} does not fit uint96")
    expiry = sub & UINT32_MAX
    strike_e8 = (sub >> 32) & UINT63_MAX
    return expiry, strike_e8 / 1e8, (sub >> 95) > 0


def encode_option_subid(expiry: int, strike: float, is_call: bool) -> int:
    """Inverse of :func:`decode_option_subid` (``OptionEncoding.toSubId`` with the strike in USD)."""
    strike_e8 = int(round(float(strike) * 1e8))
    if not 0 < int(expiry) <= UINT32_MAX or not 0 <= strike_e8 <= UINT63_MAX:
        raise ValueError("expiry or strike out of range")
    return int(expiry) | (strike_e8 << 32) | ((1 if is_call else 0) << 95)


def _strike_text(strike: float) -> str:
    s = ("%.8f" % float(strike)).rstrip("0").rstrip(".")
    return s.replace(".", "_")


def instrument_name(ccy: str, expiry: int, strike: float, is_call: bool) -> str:
    """Derive instrument name, e.g. ``HYPE-20251121-38_75-P`` (decimal point written as ``_``)."""
    day = dt.datetime.fromtimestamp(int(expiry), tz=dt.timezone.utc).strftime("%Y%m%d")
    return f"{ccy}-{day}-{_strike_text(strike)}-{'C' if is_call else 'P'}"


def parse_instrument_name(name: str) -> Tuple[str, int, float, bool]:
    """(ccy, expiry, strike, is_call); the expiry is 08:00 UTC of the named day, as for every Derive option."""
    ccy, day, strike, cp = name.split("-")
    d = dt.datetime.strptime(day, "%Y%m%d").replace(hour=8, tzinfo=dt.timezone.utc)
    return ccy, int(d.timestamp()), float(strike.replace("_", ".")), cp == "C"


def first_block_of_day(day_ts: int) -> int:
    """First block with timestamp >= ``day_ts`` (00:00:01 UTC with the 2 s clock)."""
    b = block_at_ts(day_ts)
    return b + 1 if ts_at_block(b) < day_ts else b


def _day_ts(day) -> int:
    d = pd.Timestamp(day)
    return calendar.timegm(d.date().timetuple())


# ---------------------------------------------------------------- minimal ABI

def _word(x: int) -> bytes:
    return int(x).to_bytes(32, "big")


def _int_word(x: int) -> bytes:
    return (int(x) % (1 << 256)).to_bytes(32, "big")


def _addr_word(addr: str) -> bytes:
    raw = bytes.fromhex(addr[2:] if addr.startswith("0x") else addr)
    if len(raw) != 20:
        raise ValueError(f"bad address {addr}")
    return bytes(12) + raw


def _read(data: bytes, off: int) -> int:
    return int.from_bytes(data[off:off + 32], "big")


def _read_signed(data: bytes, off: int) -> int:
    v = _read(data, off)
    return v - (1 << 256) if v >> 255 else v


def decode_address(data: bytes) -> str:
    return "0x" + bytes(data[12:32]).hex()


def account_calls(acc: int) -> List[Tuple[str, bytes]]:
    """``getAccountBalances(acc)`` and ``manager(acc)`` on SubAccounts as (target, calldata)."""
    return [(SUBACCOUNTS, bytes.fromhex(SEL_GET_ACCOUNT_BALANCES) + _word(acc)),
            (SUBACCOUNTS, bytes.fromhex(SEL_MANAGER) + _word(acc))]


def _pad(b: bytes) -> bytes:
    return b + bytes((-len(b)) % 32)


def _encode_dynamic_array(elems: List[bytes]) -> bytes:
    offs, off = [], 32 * len(elems)
    for e in elems:
        offs.append(off)
        off += len(e)
    return _word(len(elems)) + b"".join(_word(o) for o in offs) + b"".join(elems)


def encode_aggregate3(calls: Sequence[Tuple[str, bytes]], allow_failure: bool = True) -> str:
    """Calldata of ``Multicall3.aggregate3(Call3[])`` with ``Call3 = (address, bool, bytes)``."""
    elems = [_addr_word(t) + _word(1 if allow_failure else 0) + _word(0x60) + _word(len(cd)) + _pad(cd)
             for t, cd in calls]
    return "0x" + SEL_AGGREGATE3 + (_word(0x20) + _encode_dynamic_array(elems)).hex()


def decode_aggregate3(data: bytes) -> List[Tuple[bool, bytes]]:
    """Return value ``(bool success, bytes returnData)[]`` of ``aggregate3``."""
    base = _read(data, 0)
    n = _read(data, base)
    start = base + 32
    out = []
    for i in range(n):
        eo = start + _read(data, start + 32 * i)
        ok = _read(data, eo) != 0
        bo = eo + _read(data, eo + 32)
        ln = _read(data, bo)
        out.append((ok, bytes(data[bo + 32:bo + 32 + ln])))
    return out


def _encode_bool_bytes_array(entries: Sequence[Tuple[bool, bytes]]) -> bytes:
    elems = [_word(1 if ok else 0) + _word(0x40) + _word(len(b)) + _pad(b) for ok, b in entries]
    return _word(0x20) + _encode_dynamic_array(elems)


def decode_balances(data: bytes) -> List[Tuple[str, int, int]]:
    """``AssetBalance[]`` = (asset, subId, balance) with the balance as signed 1e18 integer."""
    base = _read(data, 0)
    n = _read(data, base)
    p = base + 32
    out = []
    for _ in range(n):
        out.append(("0x" + bytes(data[p + 12:p + 32]).hex(), _read(data, p + 32), _read_signed(data, p + 64)))
        p += 96
    return out


def _encode_balances(rows: Sequence[Tuple[str, int, int]]) -> bytes:
    body = b"".join(_addr_word(a) + _word(s) + _int_word(b) for a, s, b in rows)
    return _word(0x20) + _word(len(rows)) + body


# ---------------------------------------------------------------- asset registry

class AssetRegistry:
    """Maps asset addresses to (kind, ccy) and managers to labels; cash asset read from ``manager.cashAsset()``."""

    def __init__(self, assets: Optional[Dict[str, Tuple[str, str]]] = None, managers: Optional[Dict[str, str]] = None,
                 cash_by_manager: Optional[Dict[str, str]] = None):
        self.assets = {k.lower(): v for k, v in (assets or {}).items()}
        self.managers = {k.lower(): v for k, v in (managers or {}).items()}
        self.cash_by_manager = {k.lower(): v.lower() for k, v in (cash_by_manager or {}).items()}

    @classmethod
    def from_dicts(cls, head_cur: Dict[str, dict], currencies: Iterable[dict], managers: Iterable[dict] = ()) -> "AssetRegistry":
        """``head_cur`` = ``addresses_head.json['cur']`` (primary for BTC, ETH, HYPE); ``currencies`` =
        ``all_currencies.json['result']`` (every other currency); ``managers`` = its ``managers`` entries."""
        assets: Dict[str, Tuple[str, str]] = {}
        for r in currencies:
            pa = r.get("protocol_asset_addresses") or {}
            for key, kind in (("option", "option"), ("perp", "perp"), ("spot", "base")):
                if pa.get(key):
                    assets[pa[key].lower()] = (kind, r["currency"])
        for ccy, d in head_cur.items():
            for key, kind in (("option", "option"), ("perp", "perp"), ("spot_asset", "base")):
                if d.get(key):
                    assets[d[key].lower()] = (kind, ccy)
        mgrs = {}
        for m in managers:
            mgrs[m["address"].lower()] = m["margin_type"] + (f":{m['currency']}" if m.get("currency") else "")
        return cls(assets, mgrs)

    @classmethod
    def from_kontext(cls, kontext: Path = KONTEXT) -> "AssetRegistry":
        head = json.loads((Path(kontext) / "addresses_head.json").read_text())["cur"]
        cur = json.loads((Path(kontext) / "all_currencies.json").read_text())["result"]
        managers, seen = [], set()
        for r in cur:
            for m in r.get("managers") or []:
                if m["address"].lower() not in seen:
                    seen.add(m["address"].lower())
                    managers.append(m)
        return cls.from_dicts(head, cur, managers)

    @property
    def cash_assets(self) -> set:
        return set(self.cash_by_manager.values())

    def classify(self, asset: str) -> Tuple[str, Optional[str]]:
        a = asset.lower()
        if a in self.cash_assets:
            return "cash", "USDC"
        return self.assets.get(a, ("other", None))

    def ensure_cash(self, rpc: Rpc, manager: str, block: int) -> None:
        m = manager.lower()
        if m == ZERO_ADDRESS or m in self.cash_by_manager:
            return
        self.cash_by_manager[m] = decode_address(rpc.eth_call(manager, "0x" + SEL_CASH_ASSET, block))

    def manager_label(self, manager: Optional[str]) -> str:
        if not manager or manager.lower() == ZERO_ADDRESS:
            return "none"
        return self.managers.get(manager.lower(), "unknown")

    def load_cash(self, path: Path) -> None:
        if Path(path).exists():
            for k, v in json.loads(Path(path).read_text()).items():
                self.cash_by_manager.setdefault(k.lower(), v.lower())

    def save_cash(self, path: Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.cash_by_manager, indent=1, sort_keys=True))


_DEFAULT_REGISTRY: Optional[AssetRegistry] = None


def default_registry() -> AssetRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = AssetRegistry.from_kontext()
        _DEFAULT_REGISTRY.load_cash(BOOKS_DIR / "cash_assets.json")
    return _DEFAULT_REGISTRY


# ---------------------------------------------------------------- snapshots

def fetch_raw(rpc: Rpc, subaccounts: Sequence[int], block: int) -> Dict[int, Optional[Tuple[str, List[Tuple[str, int, int]]]]]:
    """{acc: (manager, balances)} at ``block``; ``None`` for accounts that do not exist yet (manager = 0).

    One Multicall3 ``eth_call`` for all accounts; on an error returned by the node (e.g. gas cap) the batch is split
    in halves. Network failures (the client already retries them) propagate unchanged.
    """
    subaccounts = [int(a) for a in subaccounts]
    calls = [c for acc in subaccounts for c in account_calls(acc)]
    try:
        res = decode_aggregate3(rpc.eth_call(MULTICALL3, encode_aggregate3(calls), block))
    except RpcError:
        if len(subaccounts) == 1:
            raise
        half = len(subaccounts) // 2
        out = fetch_raw(rpc, subaccounts[:half], block)
        out.update(fetch_raw(rpc, subaccounts[half:], block))
        return out
    out: Dict[int, Optional[Tuple[str, List[Tuple[str, int, int]]]]] = {}
    for i, acc in enumerate(subaccounts):
        (ok_b, b), (ok_m, m) = res[2 * i], res[2 * i + 1]
        if not ok_m:
            raise RuntimeError(f"manager() failed at block {block}")
        mgr = decode_address(m)
        if mgr == ZERO_ADDRESS:
            out[acc] = None
            continue
        if not ok_b:  # sub-call ran out of gas inside the batch: ask directly
            b = rpc.eth_call(SUBACCOUNTS, "0x" + account_calls(acc)[0][1].hex(), block)
        out[acc] = (mgr, decode_balances(b))
    return out


def rows_from_balances(manager: str, balances: Sequence[Tuple[str, int, int]], registry: AssetRegistry) -> List[dict]:
    rows = []
    for asset, sub, bal in balances:
        kind, ccy = registry.classify(asset)
        expiry = strike = is_call = None
        if kind == "option":
            expiry, strike, is_call = decode_option_subid(sub)
        rows.append({"asset": asset, "sub_id": int(sub), "balance": int(bal), "amount": int(bal) / 1e18, "kind": kind,
                     "ccy": ccy, "expiry": expiry, "strike": strike, "is_call": is_call, "manager": manager})
    if not rows:
        rows.append({"asset": None, "sub_id": None, "balance": 0, "amount": 0.0, "kind": "none", "ccy": None,
                     "expiry": None, "strike": None, "is_call": None, "manager": manager})
    return rows


def snapshot_many(rpc: Rpc, subaccounts: Sequence[int], block: int,
                  registry: Optional[AssetRegistry] = None) -> Dict[int, List[dict]]:
    """Decoded balances of many subaccounts at ``block``; accounts that do not exist yet are left out."""
    reg = registry or default_registry()
    out = {}
    for acc, v in fetch_raw(rpc, subaccounts, block).items():
        if v is None:
            continue
        reg.ensure_cash(rpc, v[0], block)
        out[acc] = rows_from_balances(v[0], v[1], reg)
    return out


def snapshot(rpc: Rpc, subaccount: int, block: int, registry: Optional[AssetRegistry] = None) -> List[dict]:
    """Rows ``asset, sub_id, balance, amount, kind, ccy, expiry, strike, is_call, manager`` of one subaccount.

    ``kind`` is ``option``, ``perp``, ``cash``, ``base`` (spot/collateral asset) or ``other`` (unknown address); an
    existing account without balances yields one ``kind = "none"`` row with its manager; a missing account ``[]``.
    """
    return snapshot_many(rpc, [subaccount], block, registry).get(int(subaccount), [])


def snapshot_frame(subaccount: int, day, block: int, manager: str, balances: Sequence[Sequence],
                   registry: AssetRegistry) -> pd.DataFrame:
    """Rows of one (subaccount, day) as in ``snapshots.parquet`` from raw ``(asset, sub_id, balance)`` triples
    (ints or decimal strings, as stored in ``data/p2/books/raw``)."""
    bals = [(str(a), int(sid), int(b)) for a, sid, b in balances]
    label = registry.manager_label(manager)
    rows = []
    for r in rows_from_balances(manager, bals, registry):
        rows.append({"subaccount": int(subaccount), "day": pd.Timestamp(day), "block": int(block),
                     "manager": r["manager"], "asset": r["asset"],
                     "sub_id": None if r["sub_id"] is None else str(r["sub_id"]), "kind": r["kind"], "ccy": r["ccy"],
                     "expiry": r["expiry"], "strike": r["strike"], "is_call": r["is_call"], "amount": r["amount"],
                     "balance_raw": str(r["balance"]), "manager_label": label})
    return _typed_snapshots(pd.DataFrame(rows, columns=SNAPSHOT_COLUMNS))


def _typed_snapshots(df: pd.DataFrame) -> pd.DataFrame:
    df = df.astype({"subaccount": "int64", "block": "int64", "expiry": "Int64", "strike": "float64",
                    "is_call": "boolean", "amount": "float64"})
    df["day"] = pd.to_datetime(df["day"])
    return df


# ---------------------------------------------------------------- top makers

def top_maker_subaccounts(n: int = 10, markouts: Optional[pd.DataFrame] = None, path: Path = MARKOUTS) -> List[int]:
    """Subaccounts with the most maker fills in the Paper 1 sample (ties by id)."""
    if markouts is None:
        markouts = pd.read_parquet(path, columns=["maker_sub"])
    vc = markouts["maker_sub"].value_counts()
    df = pd.DataFrame({"sub": vc.index.astype("int64"), "n": vc.values}).sort_values(["n", "sub"], ascending=[False, True])
    return [int(x) for x in df["sub"].head(n)]


# ---------------------------------------------------------------- books from snapshot + tape

LegKey = Tuple[str, int, float, bool]


def _as_frame(rows) -> pd.DataFrame:
    return rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(list(rows))


def _single(snap: pd.DataFrame, col: str):
    if col not in snap.columns or snap.empty:
        return None
    vals = snap[col].dropna().unique()
    if len(vals) > 1:
        raise ValueError(f"snapshot rows span several values of {col!r}: {list(vals)[:5]}")
    return vals[0] if len(vals) else None


def _snapshot_positions(snap: pd.DataFrame) -> Tuple[Dict[LegKey, float], Dict[str, float]]:
    legs: Dict[LegKey, float] = defaultdict(float)
    perps: Dict[str, float] = defaultdict(float)
    if snap.empty:
        return legs, perps
    for r in snap.itertuples(index=False):
        if r.kind == "option":
            legs[(str(r.ccy), int(r.expiry), round(float(r.strike), 8), bool(r.is_call))] += float(r.amount)
        elif r.kind == "perp":
            perps[str(r.ccy)] += float(r.amount)
    return legs, perps


def _tape_deltas(tape: pd.DataFrame, sub, lo_ms: int, hi_ms: int,
                 exclude_trade_ids: Optional[Iterable[str]] = None) -> Dict[LegKey, float]:
    """Signed option fills of subaccount ``sub`` with ``lo_ms <= timestamp < hi_ms`` (maker and taker rows),
    without the rows of ``exclude_trade_ids``."""
    if tape is None or len(tape) == 0:
        return {}
    t = tape
    if sub is not None and "subaccount_id" in t.columns:
        t = t[t["subaccount_id"] == int(sub)]
    t = t[(t["timestamp"] >= lo_ms) & (t["timestamp"] < hi_ms)]
    if exclude_trade_ids is not None:
        if "trade_id" not in t.columns:
            raise ValueError("exclude_trade_ids needs a trade_id column in the tape")
        t = t[~t["trade_id"].isin(list(exclude_trade_ids))]
    if t.empty:
        return {}
    direction = t["direction"].astype(str)
    if not direction.isin(["buy", "sell"]).all():
        raise ValueError("tape direction must be buy or sell")
    sign = np.where(direction == "buy", 1.0, -1.0)
    if {"currency", "expiry", "strike", "option_type"} <= set(t.columns):
        ccy, exp, k, cp = t["currency"].astype(str), t["expiry"].astype("int64"), t["strike"].astype(float), t["option_type"]
        is_call = cp.astype(str).eq("C")
    else:
        parsed = [parse_instrument_name(n) for n in t["instrument_name"]]
        ccy = pd.Series([p[0] for p in parsed], index=t.index)
        exp = pd.Series([p[1] for p in parsed], index=t.index)
        k = pd.Series([p[2] for p in parsed], index=t.index)
        is_call = pd.Series([p[3] for p in parsed], index=t.index)
    g = pd.DataFrame({"ccy": ccy.values, "expiry": exp.values, "strike": k.round(8).values, "is_call": is_call.values,
                      "q": sign * t["trade_amount"].astype(float).values})
    s = g.groupby(["ccy", "expiry", "strike", "is_call"], sort=False)["q"].sum()
    return {(str(c), int(e), float(kk), bool(ic)): float(q) for (c, e, kk, ic), q in s.items()}


def _merge(legs: Dict[LegKey, float], deltas: Dict[LegKey, float]) -> Dict[LegKey, float]:
    out: Dict[LegKey, float] = defaultdict(float, legs)
    for k, v in deltas.items():
        out[k] += v
    return out


def _day_start_ms(snap: pd.DataFrame, ts_ms: int) -> int:
    day = _single(snap, "day")
    if day is None:
        return int(ts_ms) - int(ts_ms) % DAY_MS
    return _day_ts(day) * 1000


def fill_day(ts_ms: int) -> pd.Timestamp:
    """UTC day (naive midnight, as ``snapshots.parquet['day']``) of a tape row; for a maker fill pass the maker row's
    timestamp (``markouts.ts_maker``), which can fall on the day before the taker row."""
    ts_ms = int(ts_ms)
    return pd.Timestamp(ts_ms - ts_ms % DAY_MS, unit="ms")


def _books_from_positions(legs: Dict[LegKey, float], perps: Dict[str, float], ts_ms: int) -> Dict[str, Book]:
    by_ccy: Dict[str, List[OptionLeg]] = defaultdict(list)
    for (ccy, e, k, c), q in legs.items():
        if e * 1000 <= int(ts_ms) or abs(q) < AMOUNT_EPS:
            continue
        by_ccy[ccy].append(OptionLeg(expiry=e, strike=k, is_call=c, amount=round(q, 10)))
    out = {}
    for ccy in sorted(set(by_ccy) | {c for c, p in perps.items() if abs(p) >= AMOUNT_EPS}):
        opts = sorted(by_ccy.get(ccy, []), key=lambda leg: leg.key)
        out[ccy] = Book(options=opts, perp=float(perps.get(ccy, 0.0)), perp_entry=None, cash=0.0)
    return out


def book_at(snapshot_rows, tape_rows, ts: int, subaccount: Optional[int] = None,
            exclude_trade_ids: Optional[Iterable[str]] = None) -> Dict[str, Book]:
    """Preregistered book of one subaccount just before ``ts``: day-start snapshot + all of its tape fills (maker and
    taker rows) of that UTC day with ``timestamp < ts`` and not in ``exclude_trade_ids``; options with
    ``expiry * 1000 <= ts`` are removed; ``cash = 0`` (capital is measured at zero cash). One :class:`Book` per
    currency with options or a perp.

    ``ts`` (Unix milliseconds) must be the timestamp of **this subaccount's own tape row** of the fill. For a maker
    fill that is ``markouts.ts_maker``, not ``markouts.ts``: ``ts`` is the taker row, and for RFQ fills the maker row
    is older (median 4 s, up to 28 min), so ``ts`` would put the fill itself into the book before it. Prefer
    :func:`book_before_fill`, which cuts at the own row and always drops the fill's ``trade_id``. Fills with exactly
    the same millisecond (other legs of a multi-leg RFQ, batched matches) are left out, as preregistered ("früherer
    Zeitstempel"). The snapshot day must contain ``ts`` (``ValueError`` otherwise); select it with :func:`fill_day`.

    Limitations: the tape holds option fills only, so perps stay at their day-start value (``perp_entry = None``),
    and trade-module transfers between subaccounts of one operator are not in the tape. The exact book at the fill's
    transaction is :func:`onchain_book_before`.

    ``snapshot_rows`` are the rows of one (subaccount, day) of ``snapshots.parquet``; on the creation day of an
    account there is none (it did not exist at 00:00 UTC): pass empty rows and ``subaccount``.
    """
    if int(ts) < 10 ** 11:
        raise ValueError("ts must be Unix milliseconds")
    snap = _as_frame(snapshot_rows)
    sub = subaccount if subaccount is not None else _single(snap, "subaccount")
    tape = _as_frame(tape_rows) if tape_rows is not None else None
    if sub is None and tape is not None and "subaccount_id" in tape.columns and tape["subaccount_id"].nunique() > 1:
        raise ValueError("subaccount unknown: pass subaccount= or snapshot rows with a subaccount column")
    lo = _day_start_ms(snap, ts)
    if not lo <= int(ts) < lo + DAY_MS:
        raise ValueError(f"ts {int(ts)} is not in the UTC day of the snapshot rows (starting {lo})")
    legs, perps = _snapshot_positions(snap)
    legs = _merge(legs, _tape_deltas(tape, sub, lo, int(ts), exclude_trade_ids))
    return _books_from_positions(legs, perps, int(ts))


def book_before_fill(snapshot_rows, tape_rows, trade_id: str, subaccount: Optional[int] = None) -> Dict[str, Book]:
    """:func:`book_at` cut at this subaccount's own tape row of ``trade_id`` (its earliest row, if several), with
    that trade excluded. ``KeyError`` if the subaccount has no tape row of ``trade_id``."""
    snap = _as_frame(snapshot_rows)
    tape = _as_frame(tape_rows)
    sub = subaccount if subaccount is not None else _single(snap, "subaccount")
    if sub is None:
        raise ValueError("subaccount unknown: pass subaccount= or snapshot rows with a subaccount column")
    own = tape[(tape["trade_id"] == trade_id) & (tape["subaccount_id"] == int(sub))]
    if own.empty:
        raise KeyError(f"no tape row of trade {trade_id!r} for this subaccount")
    return book_at(snap, tape, int(own["timestamp"].min()), subaccount=int(sub), exclude_trade_ids=[trade_id])


def reconcile_day(snap_day, snap_next, tape, lag_ms: int = 0, ccys: Optional[Sequence[str]] = None) -> dict:
    """Day-start book + all fills of the day against the next day-start book (option legs only).

    Legs expiring at or before the next day start are ignored on both sides (settlement). ``lag_ms`` shifts the
    fill window to ``[day - lag, next day - lag)`` as a diagnostic for fills matched before and settled after
    midnight. A leg matches if the absolute difference is at most ``AMOUNT_EPS`` contracts.
    """
    s0, s1 = _as_frame(snap_day), _as_frame(snap_next)
    sub = _single(s0, "subaccount")
    lo = _day_start_ms(s0, 0)
    hi = lo + DAY_MS
    exp_legs, _ = _snapshot_positions(s0)
    exp_legs = _merge(exp_legs, _tape_deltas(_as_frame(tape) if tape is not None else None, sub, lo - lag_ms, hi - lag_ms))
    act_legs, _ = _snapshot_positions(s1)

    def keep(k):
        return k[1] * 1000 > hi and (ccys is None or k[0] in ccys)

    keys = {k for k, v in exp_legs.items() if keep(k) and abs(v) >= AMOUNT_EPS}
    keys |= {k for k, v in act_legs.items() if keep(k) and abs(v) >= AMOUNT_EPS}
    diffs = [abs(exp_legs.get(k, 0.0) - act_legs.get(k, 0.0)) for k in keys]
    n_match = sum(d <= AMOUNT_EPS for d in diffs)
    return {"n_legs": len(keys), "n_match": int(n_match), "day_match": bool(n_match == len(keys)),
            "max_abs_diff": float(max(diffs)) if diffs else 0.0, "sum_abs_diff": float(sum(diffs))}


# ---------------------------------------------------------------- resumable loader

def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def load_snapshots(rpc: Rpc, subaccounts: Sequence[int], start_day: str = START_DAY, end_day: str = END_DAY,
                   out_dir: Path = BOOKS_DIR, registry: Optional[AssetRegistry] = None,
                   max_seconds: Optional[float] = None, max_days: Optional[int] = None) -> dict:
    """Day-start balances and managers of ``subaccounts`` for every UTC day in [start_day, end_day].

    One Multicall3 call per day at the first block of the day, one JSON file per day under ``out_dir/raw``
    (written atomically, existing days are skipped). Accounts that do not exist yet on a day are not stored.
    """
    out_dir = Path(out_dir)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    reg = registry or default_registry()
    reg.load_cash(out_dir / "cash_assets.json")
    days = [d.strftime("%Y-%m-%d") for d in pd.date_range(start_day, end_day, freq="D")]
    todo = [d for d in days if not (raw_dir / f"{d}.json").exists()]
    t0, done = time.monotonic(), 0
    try:
        for day in todo:
            if max_days is not None and done >= max_days:
                break
            if max_seconds is not None and time.monotonic() - t0 > max_seconds:
                break
            blk = first_block_of_day(_day_ts(day))
            raw = fetch_raw(rpc, subaccounts, blk)
            accounts = {}
            for acc, v in raw.items():
                if v is None:
                    continue
                reg.ensure_cash(rpc, v[0], blk)
                accounts[str(acc)] = {"manager": v[0], "balances": [[a, str(s), str(b)] for a, s, b in v[1]]}
            payload = {"day": day, "block": blk, "block_ts": ts_at_block(blk), "accounts": accounts}
            _atomic_write(raw_dir / f"{day}.json", json.dumps(payload, separators=(",", ":")))
            done += 1
    finally:
        reg.save_cash(out_dir / "cash_assets.json")
    return {"done": done, "remaining": len(todo) - done, "total": len(days)}


def compact(out_dir: Path = BOOKS_DIR, registry: Optional[AssetRegistry] = None) -> pd.DataFrame:
    """All day files into ``out_dir/snapshots.parquet`` (columns :data:`SNAPSHOT_COLUMNS`)."""
    out_dir = Path(out_dir)
    reg = registry or default_registry()
    reg.load_cash(out_dir / "cash_assets.json")
    frames = []
    for f in sorted((out_dir / "raw").glob("*.json")):
        p = json.loads(f.read_text())
        for acc, v in sorted(p["accounts"].items(), key=lambda kv: int(kv[0])):
            frames.append(snapshot_frame(int(acc), p["day"], int(p["block"]), v["manager"], v["balances"], reg))
    df = _typed_snapshots(pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=SNAPSHOT_COLUMNS))
    df = df.sort_values(["subaccount", "day"], kind="stable").reset_index(drop=True)
    df.to_parquet(out_dir / "snapshots.parquet", index=False)
    return df


# ---------------------------------------------------------------- BalanceAdjusted events (exact on-chain books)

def decode_balance_adjusted(log: dict) -> dict:
    """One ``BalanceAdjusted(uint indexed accountId, address indexed manager, bytes32 indexed assetAndSubId,
    int amount, int preBalance, int postBalance, uint tradeId)`` log of ``SubAccounts``.

    ``assetAndSubId = uint160(asset) << 96 | subId``; ``amount`` is the applied delta (``post - pre``, v2-core
    ``_adjustBalance``); balances are signed 1e18 integers. ``trade_id`` is the ``SubAccounts.lastTradeId`` counter,
    not the ``trade_id`` of the tape.
    """
    topics = log["topics"]
    if topics[0].lower() != T_BALANCE_ADJUSTED:
        raise ValueError("not a BalanceAdjusted log")
    data = bytes.fromhex(log["data"][2:])
    if len(data) != 128:
        raise ValueError(f"unexpected BalanceAdjusted payload of {len(data)} bytes")
    key = int(topics[3], 16)
    return {"subaccount": int(topics[1], 16), "manager": "0x" + topics[2][-40:].lower(),
            "block": int(log["blockNumber"], 16), "tx_index": int(log["transactionIndex"], 16),
            "log_index": int(log["logIndex"], 16), "tx_hash": log["transactionHash"].lower(),
            "asset": "0x%040x" % (key >> 96), "sub_id": key & UINT96_MASK, "amount": _read_signed(data, 0),
            "pre": _read_signed(data, 32), "post": _read_signed(data, 64), "trade_id": _read(data, 96)}


def _splittable(err: RpcError) -> bool:
    msg = str(err.error.get("message", "")).lower()
    return err.too_many_logs or "more than" in msg or "too many" in msg or "response size" in msg


def fetch_balance_events_windowed(rpc: Rpc, subaccount: int, lo: int, hi: int, window: Optional[int] = None,
                                  grow_below: int = LOG_LIMIT // 4) -> Tuple[List[dict], int]:
    """Decoded ``BalanceAdjusted`` events of ``subaccount`` in blocks [lo, hi], sorted by (block, log_index), and the
    block window that worked last.

    ``eth_getLogs`` filtered on ``accountId`` in windows of ``window`` blocks (default: the whole range); when the node
    refuses a window for too many results it is halved; after a window with fewer than ``grow_below`` results it
    is doubled again. Other node errors and network failures propagate.
    """
    topic1 = "0x" + int(subaccount).to_bytes(32, "big").hex()
    lo, hi = int(lo), int(hi)
    w = max(1, int(window)) if window else hi - lo + 1
    rows: List[dict] = []
    a = lo
    while a <= hi:
        b = min(a + w - 1, hi)
        flt = {"address": SUBACCOUNTS, "topics": [T_BALANCE_ADJUSTED, topic1], "fromBlock": hex(a), "toBlock": hex(b)}
        try:
            logs = rpc.raw("eth_getLogs", [flt])
        except RpcError as err:
            if b == a or not _splittable(err):
                raise
            w = max(1, (b - a + 1) // 2)
            continue
        rows.extend(decode_balance_adjusted(lg) for lg in logs if not lg.get("removed"))
        a = b + 1
        if len(logs) < grow_below:
            w = min(2 * w, hi - lo + 1)
    return sorted(rows, key=lambda r: (r["block"], r["log_index"])), w


def fetch_balance_events(rpc: Rpc, subaccount: int, lo: int, hi: int) -> List[dict]:
    """:func:`fetch_balance_events_windowed` without the window hint."""
    return fetch_balance_events_windowed(rpc, subaccount, lo, hi)[0]


def events_frame(rows: Sequence[dict], day=None) -> pd.DataFrame:
    """Decoded events as a frame with :data:`EVENT_COLUMNS` (balances as exact decimal text, ``amount`` in contracts)."""
    recs = []
    for r in rows:
        if int(r["trade_id"]) > INT64_MAX:
            raise ValueError("trade id does not fit int64")
        recs.append({"subaccount": int(r["subaccount"]), "day": pd.Timestamp(day) if day is not None else pd.NaT,
                     "block": int(r["block"]), "tx_index": int(r["tx_index"]), "log_index": int(r["log_index"]),
                     "tx_hash": str(r["tx_hash"]).lower(), "manager": str(r["manager"]).lower(),
                     "asset": str(r["asset"]).lower(), "sub_id": str(int(r["sub_id"])),
                     "amount_raw": str(int(r["amount"])), "pre_raw": str(int(r["pre"])), "post_raw": str(int(r["post"])),
                     "trade_id": int(r["trade_id"]), "amount": int(r["amount"]) / 1e18})
    df = pd.DataFrame(recs, columns=EVENT_COLUMNS)
    df = df.astype({"subaccount": "int64", "block": "int64", "tx_index": "int64", "log_index": "int64",
                    "trade_id": "int64", "amount": "float64"})
    df["day"] = pd.to_datetime(df["day"])
    return df


def _event_file(out_dir: Path, subaccount: int, day: str) -> Path:
    return Path(out_dir) / f"{int(subaccount)}_{day}.parquet"


def load_events(rpc: Rpc, account_days: Iterable[Tuple[int, object]], out_dir: Path = EVENTS_DIR,
                max_seconds: Optional[float] = None, max_items: Optional[int] = None) -> dict:
    """``BalanceAdjusted`` events of each (subaccount, UTC day) for blocks (first block of the day, first block of the
    next day], i.e. exactly the changes between two day-start snapshots. One parquet file per item (written
    atomically, existing items are skipped), resumable under a time budget."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    items = sorted({(int(a), pd.Timestamp(d).strftime("%Y-%m-%d")) for a, d in account_days})
    todo = [(a, d) for a, d in items if not _event_file(out_dir, a, d).exists()]
    t0, done = time.monotonic(), 0
    hint: Dict[int, int] = {}  # per account: the window the previous day ended with
    for acc, day in todo:
        if max_items is not None and done >= max_items:
            break
        if max_seconds is not None and time.monotonic() - t0 > max_seconds:
            break
        b0 = first_block_of_day(_day_ts(day))
        b1 = first_block_of_day(_day_ts(day) + 86_400)
        rows, w = fetch_balance_events_windowed(rpc, acc, b0 + 1, b1, hint.get(acc))
        hint[acc] = w
        df = events_frame(rows, day=day)
        path = _event_file(out_dir, acc, day)
        tmp = path.with_suffix(".tmp")
        df.to_parquet(tmp, index=False)
        os.replace(tmp, path)
        done += 1
    return {"done": done, "remaining": len(todo) - done, "total": len(items)}


def compact_events(out_dir: Path = EVENTS_DIR, path: Path = BOOKS_DIR / "events.parquet",
                   registry: Optional[AssetRegistry] = None) -> pd.DataFrame:
    """All event files into one parquet with :data:`EVENT_COLUMNS` plus ``kind`` and ``ccy`` of the asset."""
    reg = registry or default_registry()
    files = sorted(Path(out_dir).glob("*.parquet"))
    frames = [pd.read_parquet(f) for f in files]
    frames = [f for f in frames if len(f)]
    df = pd.concat(frames, ignore_index=True) if frames else events_frame([])
    cls = {a: reg.classify(a) for a in df["asset"].unique()}
    df["kind"] = df["asset"].map({a: v[0] for a, v in cls.items()})
    df["ccy"] = df["asset"].map({a: v[1] for a, v in cls.items()})
    df = df.sort_values(["subaccount", "block", "log_index"], kind="stable").reset_index(drop=True)
    df.to_parquet(path, index=False)
    return df


BalanceKey = Tuple[str, int]


def _snapshot_balances(snap: pd.DataFrame) -> Dict[BalanceKey, int]:
    bal: Dict[BalanceKey, int] = {}
    if snap.empty:
        return bal
    has_raw = "balance_raw" in snap.columns
    for r in snap.itertuples(index=False):
        if r.asset is None or (isinstance(r.asset, float) and np.isnan(r.asset)):
            continue
        raw = int(r.balance_raw) if has_raw and r.balance_raw is not None else int(round(float(r.amount) * 1e18))
        key = (str(r.asset).lower(), int(r.sub_id))
        bal[key] = bal.get(key, 0) + raw
    return bal


def _event_tuples(events) -> List[Tuple[int, int, str, BalanceKey, int, int]]:
    """(block, log_index, tx_hash, key, pre, post) in chain order from a frame or decoded dicts."""
    if isinstance(events, pd.DataFrame):
        ev = events
        out = list(zip(ev["block"].astype("int64"), ev["log_index"].astype("int64"), ev["tx_hash"].str.lower(),
                       zip(ev["asset"].str.lower(), ev["sub_id"].map(int)), ev["pre_raw"].map(int),
                       ev["post_raw"].map(int)))
    else:
        out = [(int(r["block"]), int(r["log_index"]), str(r["tx_hash"]).lower(),
                (str(r["asset"]).lower(), int(r["sub_id"])), int(r["pre"]), int(r["post"])) for r in events]
    out = [(int(b), int(li), tx, (a, int(sid)), int(pre), int(post)) for b, li, tx, (a, sid), pre, post in out]
    return sorted(out, key=lambda e: (e[0], e[1]))


def _check_same_account(snap: pd.DataFrame, events) -> None:
    if not isinstance(events, pd.DataFrame) or events.empty:
        return
    accs = set(events["subaccount"].astype("int64").unique())
    if len(accs) > 1:
        raise ValueError("events span several subaccounts")
    sub = _single(snap, "subaccount")
    if sub is not None and int(sub) not in accs:
        raise ValueError("events and snapshot belong to different subaccounts")
    if "day" in events.columns and events["day"].notna().any():
        days = set(pd.to_datetime(events["day"]).dropna().unique())
        sday = _single(snap, "day")
        if len(days) > 1 or (sday is not None and pd.Timestamp(sday) not in {pd.Timestamp(d) for d in days}):
            raise ValueError("events and snapshot belong to different days")


def replay_balances_many(snapshot_rows, events, tx_hashes: Sequence[str],
                         include_tx: bool = False) -> Dict[str, Dict[BalanceKey, int]]:
    """Exact raw balances ``{(asset, sub_id): int}`` of one subaccount just before (``include_tx``: just after) each
    transaction in ``tx_hashes``, in one pass over the day's events.

    Start is the day-start snapshot (``balance_raw``), then the ``BalanceAdjusted`` events of the same (subaccount,
    day) in chain order (block, log_index). Every event's ``pre`` balance must equal the running balance, which
    catches missing events, a wrong snapshot or foreign events (``ValueError``). ``KeyError`` for a transaction
    without an event of this subaccount. Zero balances are dropped.
    """
    snap = _as_frame(snapshot_rows)
    _check_same_account(snap, events)
    ev = _event_tuples(events)
    first: Dict[str, int] = {}
    last: Dict[str, int] = {}
    for i, e in enumerate(ev):
        first.setdefault(e[2], i)
        last[e[2]] = i
    cuts: Dict[int, List[str]] = defaultdict(list)
    for tx in tx_hashes:
        t = str(tx).lower()
        if t not in first:
            raise KeyError(f"transaction {tx} has no BalanceAdjusted event of this subaccount on this day")
        cuts[last[t] + 1 if include_tx else first[t]].append(str(tx))
    bal = _snapshot_balances(snap)
    out: Dict[str, Dict[BalanceKey, int]] = {}
    stop = max(cuts) if cuts else len(ev)
    for i in range(stop + 1):
        for tx in cuts.get(i, ()):
            out[tx] = {k: v for k, v in bal.items() if v != 0}
        if i == len(ev) or i == stop:
            break
        blk, li, _tx, key, pre, post = ev[i]
        if bal.get(key, 0) != pre:
            raise ValueError(f"event chain broken at block {blk} log {li}: pre {pre} != running {bal.get(key, 0)}")
        bal[key] = post
    return out


def replay_balances(snapshot_rows, events, tx_hash: Optional[str] = None, include_tx: bool = False) -> Dict[BalanceKey, int]:
    """:func:`replay_balances_many` for one transaction; without ``tx_hash`` all events of the day are applied (the
    result then equals the next day-start snapshot)."""
    if tx_hash is not None:
        return replay_balances_many(snapshot_rows, events, [tx_hash], include_tx)[str(tx_hash)]
    snap = _as_frame(snapshot_rows)
    _check_same_account(snap, events)
    bal = _snapshot_balances(snap)
    for blk, li, _tx, key, pre, post in _event_tuples(events):
        if bal.get(key, 0) != pre:
            raise ValueError(f"event chain broken at block {blk} log {li}: pre {pre} != running {bal.get(key, 0)}")
        bal[key] = post
    return {k: v for k, v in bal.items() if v != 0}


def books_from_balances(bal: Dict[BalanceKey, int], ts_ms: int, registry: Optional[AssetRegistry] = None) -> Dict[str, Book]:
    """Books per currency (options not expired at ``ts_ms`` and perps; cash and collateral left out) from raw balances."""
    reg = registry or default_registry()
    legs: Dict[LegKey, float] = defaultdict(float)
    perps: Dict[str, float] = defaultdict(float)
    for (asset, sid), b in bal.items():
        kind, ccy = reg.classify(asset)
        if kind == "option":
            e, k, c = decode_option_subid(sid)
            legs[(str(ccy), int(e), round(float(k), 8), bool(c))] += b / 1e18
        elif kind == "perp":
            perps[str(ccy)] += b / 1e18
    return _books_from_positions(legs, perps, int(ts_ms))


def _tx_block(events, tx_hash: str) -> int:
    t = str(tx_hash).lower()
    if isinstance(events, pd.DataFrame):
        blocks = events.loc[events["tx_hash"].str.lower() == t, "block"]
        if blocks.empty:
            raise KeyError(f"transaction {tx_hash} has no BalanceAdjusted event of this subaccount on this day")
        return int(blocks.min())
    blocks = [int(r["block"]) for r in events if str(r["tx_hash"]).lower() == t]
    if not blocks:
        raise KeyError(f"transaction {tx_hash} has no BalanceAdjusted event of this subaccount on this day")
    return min(blocks)


def onchain_book_before(snapshot_rows, events, tx_hash: str, registry: Optional[AssetRegistry] = None,
                        ts: Optional[int] = None, include_tx: bool = False) -> Dict[str, Book]:
    """Exact on-chain book of one subaccount just before the fill's transaction ``tx_hash`` (``tx_hash`` of its tape
    row): day-start snapshot + ``BalanceAdjusted`` events of that (subaccount, day) up to the transaction.

    Unlike :func:`book_at` this includes perp trades and trade-module transfers between subaccounts. Options with
    ``expiry * 1000 <= ts`` are removed, ``ts`` defaults to the timestamp of the transaction's block (ms); perps
    with ``perp_entry = None``, ``cash = 0``. The events must be those of the snapshot's day (the day whose event
    file holds ``tx_hash``, see :class:`OnchainBooks`).
    """
    bal = replay_balances(snapshot_rows, events, tx_hash, include_tx)
    ts_ms = int(ts) if ts is not None else ts_at_block(_tx_block(events, tx_hash)) * 1000
    return books_from_balances(bal, ts_ms, registry)


class OnchainBooks:
    """Exact books before fills from ``snapshots.parquet`` and ``events.parquet``.

    The (subaccount, day) of a fill is the day whose event file contains its transaction; this is the UTC day of the
    block, which can differ from the tape day when settlement crosses midnight.
    """

    def __init__(self, snapshots: pd.DataFrame, events: pd.DataFrame, registry: Optional[AssetRegistry] = None):
        self.registry = registry or default_registry()
        self.snaps = {(int(s), pd.Timestamp(d)): g for (s, d), g in snapshots.groupby(["subaccount", "day"])}
        self.events = {(int(s), pd.Timestamp(d)): g for (s, d), g in events.groupby(["subaccount", "day"])}
        self.tx_day: Dict[Tuple[int, str], pd.Timestamp] = {}
        for (s, d), g in self.events.items():
            for tx in g["tx_hash"].str.lower().unique():
                self.tx_day.setdefault((s, tx), d)
        self._empty = pd.DataFrame(columns=SNAPSHOT_COLUMNS)

    def locate(self, subaccount: int, tx_hash: str) -> pd.Timestamp:
        key = (int(subaccount), str(tx_hash).lower())
        if key not in self.tx_day:
            raise KeyError(f"no BalanceAdjusted event of transaction {tx_hash} for this subaccount in the loaded days")
        return self.tx_day[key]

    def _snap(self, subaccount: int, day: pd.Timestamp) -> pd.DataFrame:
        return self.snaps.get((int(subaccount), day), self._empty)

    def before(self, subaccount: int, tx_hash: str, ts: Optional[int] = None, include_tx: bool = False) -> Dict[str, Book]:
        day = self.locate(subaccount, tx_hash)
        return onchain_book_before(self._snap(subaccount, day), self.events[(int(subaccount), day)], tx_hash,
                                   self.registry, ts, include_tx)

    def before_many(self, subaccount: int, tx_hashes: Sequence[str], include_tx: bool = False) -> Dict[str, Dict[str, Book]]:
        """Books before many transactions of one subaccount, one replay per day (expiry cut at each block's time)."""
        by_day: Dict[pd.Timestamp, List[str]] = defaultdict(list)
        for tx in tx_hashes:
            by_day[self.locate(subaccount, tx)].append(str(tx))
        out: Dict[str, Dict[str, Book]] = {}
        for day, txs in by_day.items():
            ev = self.events[(int(subaccount), day)]
            bals = replay_balances_many(self._snap(subaccount, day), ev, txs, include_tx)
            blocks = ev.groupby(ev["tx_hash"].str.lower())["block"].min()
            for tx in txs:
                out[tx] = books_from_balances(bals[tx], ts_at_block(int(blocks[tx.lower()])) * 1000, self.registry)
        return out


def compare_books(tape_book: Optional[Book], chain_book: Optional[Book]) -> dict:
    """Leg-by-leg comparison of two books of one currency (tolerance ``AMOUNT_EPS`` contracts)."""
    a = {leg.key: leg.amount for leg in (tape_book.options if tape_book else [])}
    b = {leg.key: leg.amount for leg in (chain_book.options if chain_book else [])}
    keys = set(a) | set(b)
    diffs = {k: abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys}
    n_diff = sum(d > AMOUNT_EPS for d in diffs.values())
    pa = tape_book.perp if tape_book else 0.0
    pb = chain_book.perp if chain_book else 0.0
    return {"n_legs": len(keys), "n_diff": int(n_diff), "options_equal": bool(n_diff == 0),
            "gross_abs_diff": float(sum(diffs.values())), "gross_chain": float(sum(abs(v) for v in b.values())),
            "perp_tape": float(pa), "perp_chain": float(pb), "perp_equal": bool(abs(pa - pb) <= AMOUNT_EPS)}


def perp_drift(snaps: pd.DataFrame, ccys: Optional[Sequence[str]] = None) -> pd.DataFrame:
    """Per subaccount: consecutive day-start pairs (both snapshots present) and how often the perp position changed.

    The change of a pair is the sum over currencies of |perp(next) - perp(day)|; a day without a perp row counts as
    zero. ``median_abs_change`` and ``max_abs_change`` are over the changed pairs (contracts).
    """
    s = snaps
    perp = s[s["kind"] == "perp"]
    if ccys is not None:
        perp = perp[perp["ccy"].isin(list(ccys))]
    pos = perp.groupby(["subaccount", "day", "ccy"])["amount"].sum()
    rows = []
    for acc, g in s.groupby("subaccount"):
        days = sorted(pd.Timestamp(d) for d in g["day"].unique())
        have = set(days)
        p = pos.loc[acc] if acc in pos.index.get_level_values(0) else pd.Series(dtype=float)
        by_day: Dict[pd.Timestamp, Dict[str, float]] = defaultdict(dict)
        for (d, c), v in p.items():
            by_day[pd.Timestamp(d)][c] = float(v)
        changes = []
        n_pairs = 0
        for d in days:
            nd = d + pd.Timedelta(days=1)
            if nd not in have:
                continue
            n_pairs += 1
            a, b = by_day.get(d, {}), by_day.get(nd, {})
            ch = sum(abs(b.get(c, 0.0) - a.get(c, 0.0)) for c in set(a) | set(b))
            if ch > AMOUNT_EPS:
                changes.append(ch)
        rows.append({"subaccount": int(acc), "day_pairs": n_pairs, "days_changed": len(changes),
                     "share_changed": len(changes) / n_pairs if n_pairs else float("nan"),
                     "median_abs_change": float(np.median(changes)) if changes else 0.0,
                     "max_abs_change": float(max(changes)) if changes else 0.0})
    return pd.DataFrame(rows)


def verify_event_days(snaps: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Per loaded (subaccount, day) with a snapshot on the next day: does day-start snapshot + the day's events give
    the next day-start snapshot exactly (all assets, raw 1e18 balances)? ``chain_ok`` is False when a ``pre`` balance
    does not match the running balance; ``n_diff`` counts differing assets otherwise."""
    snap_g = {(int(s_), pd.Timestamp(d)): g for (s_, d), g in snaps.groupby(["subaccount", "day"])}
    empty = pd.DataFrame(columns=SNAPSHOT_COLUMNS)
    rows = []
    for (s_, d), g in events.groupby(["subaccount", "day"]):
        s_, d = int(s_), pd.Timestamp(d)
        nxt = snap_g.get((s_, d + pd.Timedelta(days=1)))
        if nxt is None:
            continue
        rec = {"subaccount": s_, "day": d, "n_events": int(len(g)), "chain_ok": True, "n_keys": 0, "n_diff": 0}
        try:
            got = replay_balances(snap_g.get((s_, d), empty), g)
        except ValueError:
            rec.update(chain_ok=False, exact=False)
            rows.append(rec)
            continue
        exp = {k: v for k, v in _snapshot_balances(nxt).items() if v != 0}
        keys = set(got) | set(exp)
        rec["n_keys"] = len(keys)
        rec["n_diff"] = sum(got.get(k, 0) != exp.get(k, 0) for k in keys)
        rec["exact"] = rec["n_diff"] == 0
        rows.append(rec)
    return pd.DataFrame(rows, columns=["subaccount", "day", "n_events", "chain_ok", "n_keys", "n_diff", "exact"])


def event_days_for_fills(rows: pd.DataFrame) -> set:
    """(subaccount, 'YYYY-MM-DD') of the UTC day of each tape row (``subaccount_id``, ``timestamp``)."""
    return {(int(a), fill_day(t).strftime("%Y-%m-%d")) for a, t in zip(rows["subaccount_id"], rows["timestamp"])}


def missing_fill_days(rows: pd.DataFrame, events: pd.DataFrame, loaded: set, max_lag_days: int = 2) -> set:
    """Next (subaccount, day) to load for tape rows whose transaction is not yet among ``events``: the first day
    after the row's day (up to ``max_lag_days``) that is not loaded yet; settlement can cross midnight."""
    found = set(zip(events["subaccount"].astype("int64"), events["tx_hash"].str.lower()))
    out = set()
    for a, t, tx in zip(rows["subaccount_id"], rows["timestamp"], rows["tx_hash"].astype(str).str.lower()):
        if (int(a), tx) in found:
            continue
        d0 = fill_day(t)
        for k in range(1, max_lag_days + 1):
            item = (int(a), (d0 + pd.Timedelta(days=k)).strftime("%Y-%m-%d"))
            if item not in loaded:
                out.add(item)
                break
    return out


# ================================================================ Part 2 (task B3): marginal capital, netting value, holding time
#
# Preregistration (docs/paper2/PRAEREGISTRIERUNG.md incl. Nachtrag 1):
# * H2 population: maker fills of the ten dominant subaccounts in the PM2 window of the fill's currency whose account is
#   under PM2 at the start of the UTC day; a seeded simple random sample of 20 000 (numpy default_rng(20260924)).
# * book before a fill = day-start snapshot + BalanceAdjusted events up to the fill's transaction (Nachtrag 1);
#   dK = K(after) - K(before) = p q_new + net(before) - net(after) at zero cash under PM2 with the account's lib.
# * netting value of a maker day: K of the day-start book (marks M_b of Paper 1) under SM, legacy PM (BTC/ETH legs only)
#   and PM2, each currency its own portfolio under PM2 and the legacy PM; only currencies whose PM2 window is open.
# * holding time (sensitivity): FIFO per subaccount and instrument over the tape fills, reconciled to the day-start
#   snapshots (transfers), median per Paper-1 cell on the maker side.

PM2_WINDOW_START = {"BTC": 1_749_769_200, "ETH": 1_749_769_200, "HYPE": 1_762_819_200}  # 12.06.2025 23:00, 11.11.2025
LEGACY_PM_CCYS = ("BTC", "ETH")
H2_N = 20_000
H2_SEED = 20260924
PILOT_END_MS = 1_789_646_400_000  # 17.09.2026 12:00 UTC (pilot cut of Paper 1)
DERIVED_DIR = Path("data/p2/derived")


def pm2_window_open(ccy: str, ts: int) -> bool:
    """True if the PM2 window of ``ccy`` is open at ``ts`` (Unix seconds)."""
    start = PM2_WINDOW_START.get(str(ccy))
    return start is not None and int(ts) >= start


def filter_pm2_window(books_by_ccy: Dict[str, Book], ts: int) -> Dict[str, Book]:
    """Only the books of currencies whose PM2 window is open at ``ts`` (seconds); other currencies drop out."""
    return {c: b for c, b in books_by_ccy.items() if pm2_window_open(c, ts)}


def _zero_cash(book: Optional[Book]) -> Book:
    if book is None:
        return Book()
    return Book(options=list(book.options), perp=float(book.perp), perp_entry=None, cash=0.0)


def add_leg(book: Optional[Book], expiry: int, strike: float, is_call: bool, q: float) -> Book:
    """``book`` at zero cash plus one option leg (the engines net legs of the same instrument)."""
    b = _zero_cash(book)
    b.options.append(OptionLeg(int(expiry), float(strike), bool(is_call), float(q)))
    return b


def leg_vols(state, legs: Sequence[OptionLeg]) -> Dict[Tuple[int, float], float]:
    """Vol-feed value at every (expiry, strike) of ``legs`` (``LyraVolFeed.getVol`` on the expiry's SVI curve,
    vectorised); nan where the expiry has no state or no SVI curve."""
    from .chainfeeds import svi_vol

    by_e: Dict[int, List[float]] = defaultdict(list)
    for leg in legs:
        by_e[int(leg.expiry)].append(float(leg.strike))
    out: Dict[Tuple[int, float], float] = {}
    for e, ks in by_e.items():
        es = state.expiries.get(e)
        if es is None or es.svi is None:
            out.update({(e, k): float("nan") for k in ks})
            continue
        a, b, rho, m, sig, ref = es.svi
        f = es.svi_fwd if es.svi_fwd is not None else es.forward
        with np.errstate(invalid="ignore", divide="ignore"):
            v = svi_vol(np.asarray(ks, dtype=float), a, b, rho, m, sig, f, ref)
        out.update({(e, k): float(x) for k, x in zip(ks, np.atleast_1d(v))})
    return out


def mark_b(state, legs: Sequence[OptionLeg], vols: Optional[Dict[Tuple[int, float], float]] = None) -> np.ndarray:
    """Paper-1 mark M_b per leg: Black-76 on the last pushed SVI curve, forward ``SVI_fwd``, discount 1
    (``markpath.mark_from_svi``); nan without a curve or at/after expiry."""
    from . import pricing

    if not len(legs):
        return np.zeros(0)
    vols = vols if vols is not None else leg_vols(state, legs)
    F, K, T, V, kind = [], [], [], [], []
    for leg in legs:
        es = state.expiries.get(int(leg.expiry))
        f = float("nan") if es is None or es.svi is None else (es.svi_fwd if es.svi_fwd is not None else es.forward)
        F.append(f)
        K.append(float(leg.strike))
        T.append((float(leg.expiry) - float(state.ts)) / pricing.YEAR)
        V.append(vols.get((int(leg.expiry), float(leg.strike)), float("nan")))
        kind.append(1 if leg.is_call else -1)
    F, K, T, V, kind = (np.asarray(x, dtype=float) for x in (F, K, T, V, kind))
    with np.errstate(invalid="ignore"):
        price = pricing.price(F, K, T, V, kind, 1.0)
    return np.where((T > 0) & np.isfinite(V) & np.isfinite(F), price, np.nan)


def marginal_capital(book: Optional[Book], state, params, expiry: int, strike: float, is_call: bool, q: float,
                     price: float, *, is_initial: bool = True, vols: Optional[Dict[Tuple[int, float], float]] = None,
                     net_fn=None, net_before: Optional[float] = None) -> dict:
    """Marginal capital of adding ``q`` contracts of (expiry, strike, is_call) at ``price`` to ``book``:
    ``dK = K(after) - K(before) = price * q + net(before) - net(after)`` with zero cash (the marks of the existing legs
    cancel). ``net_fn`` defaults to ``margin_pm2.net_margin``; perps enter with entry at the engine's perp price."""
    from . import margin_pm2

    fn = net_fn or margin_pm2.net_margin
    before = _zero_cash(book)
    after = add_leg(before, expiry, strike, is_call, q)
    if vols is None:
        vols = leg_vols(state, after.options)
    if net_before is None:
        empty = not before.options and before.perp == 0.0
        net_before = 0.0 if empty else float(fn(before, state, params, is_initial, vols=vols)[0])
    net_after = float(fn(after, state, params, is_initial, vols=vols)[0])
    return {"dK": float(price) * float(q) + float(net_before) - net_after, "net_before": float(net_before),
            "net_after": net_after}


def _state_ok(state, legs: Sequence[OptionLeg], vols: Dict[Tuple[int, float], float], perp: float) -> bool:
    if state is None or not np.isfinite(state.spot):
        return False
    if perp != 0.0 and not np.isfinite(state.perp_price):
        return False
    for leg in legs:
        es = state.expiries.get(int(leg.expiry))
        if es is None or not np.isfinite(es.forward):
            return False
        if not np.isfinite(vols.get((int(leg.expiry), float(leg.strike)), float("nan"))):
            return False
    return True


def _engines():
    from . import margin_pm, margin_pm2, margin_sm
    return {"sm": margin_sm.net_margin, "pm": margin_pm.net_margin, "pm2": margin_pm2.net_margin}


def maker_day_capital(books_by_ccy: Dict[str, Book], states: Dict[str, object], params: Dict[str, Dict[str, dict]], *,
                      vols: Optional[Dict[str, Dict[Tuple[int, float], float]]] = None) -> dict:
    """Capital K = sum M_b q - net(q; cash = 0) of one day-start book under SM, legacy PM and PM2, IM and MM.

    ``books_by_ccy`` are the (window-filtered) books per currency, ``states[ccy]`` the market states at the day start,
    ``params[mgr][ccy]`` the parameters (``mgr`` in sm, pm, pm2; a missing entry gives nan). Every currency is its own
    portfolio (PM2 and legacy PM do not net across currencies; SM margins markets separately and adds them), so
    ``K_mgr = sum over ccy of K_mgr_ccy``. The legacy PM only exists for BTC and ETH: its K covers these legs only (nan
    without them) and is nan when a book holds more expiries than ``maxExpiries`` (PMRM reverts). Columns: ``K_sm,
    K_pm, K_pm2`` and ``*_mm``, the same per currency (``K_pm2_ETH``), ``premium[_ccy]``, ``n_legs, n_legs_pm,
    gross_contracts, perp_gross, n_expiries_max, ccys, status`` (``ok`` / ``no_state``), ``pm_too_many_expiries``,
    ``pm2_over_max_expiries``.
    """
    from . import margin_pm
    from .margin_sm import merged_options

    engines = _engines()
    ccys = sorted(c for c, b in books_by_ccy.items() if b.options or b.perp != 0.0)
    out: dict = {"ccys": ",".join(ccys), "n_legs": 0, "n_legs_pm": 0, "gross_contracts": 0.0, "perp_gross": 0.0,
                 "n_expiries_max": 0, "status": "ok", "pm_too_many_expiries": False, "pm2_over_max_expiries": False}
    prem: Dict[str, float] = {}
    vmaps: Dict[str, Dict[Tuple[int, float], float]] = {}
    books0: Dict[str, Book] = {}
    ok = True
    for c in ccys:
        bk = _zero_cash(books_by_ccy[c])
        legs = merged_options(bk)
        bk = Book(options=legs, perp=bk.perp, perp_entry=None, cash=0.0)
        books0[c] = bk
        n_exp = len({leg.expiry for leg in legs})
        out["n_legs"] += len(legs)
        out["n_legs_pm"] += len(legs) if c in LEGACY_PM_CCYS else 0
        out["gross_contracts"] += float(sum(abs(leg.amount) for leg in legs))
        out["perp_gross"] += abs(float(bk.perp))
        out["n_expiries_max"] = max(out["n_expiries_max"], n_exp)
        p2 = params.get("pm2", {}).get(c)
        if p2 is not None and p2.get("maxExpiries") is not None and n_exp > int(p2["maxExpiries"]):
            out["pm2_over_max_expiries"] = True
        st = states.get(c)
        if st is None:
            ok = False
            continue
        vm = (vols or {}).get(c) or leg_vols(st, legs)
        vmaps[c] = vm
        marks = mark_b(st, legs, vm)
        prem[c] = float(np.dot(marks, [leg.amount for leg in legs])) if legs else 0.0
        out[f"premium_{c}"] = prem[c]
        if not _state_ok(st, legs, vm, float(bk.perp)) or not np.isfinite(prem[c]):
            ok = False
    if not ok:
        out["status"] = "no_state"
    nan = float("nan")
    out["premium"] = float(sum(prem.values())) if ok else nan
    for mgr in ("sm", "pm", "pm2"):
        for im in (True, False):
            col = f"K_{mgr}" + ("" if im else "_mm")
            vals = []
            for c in ccys:
                if mgr == "pm" and c not in LEGACY_PM_CCYS:
                    continue
                p = params.get(mgr, {}).get(c)
                v = nan
                if ok and p is not None:
                    kw = {"strict_expiries": True} if mgr == "pm" else {}
                    try:
                        net = engines[mgr](books0[c], states[c], p, im, vols=vmaps[c], **kw)[0]
                        v = prem[c] - float(net)
                    except margin_pm.TooManyExpiries:
                        out["pm_too_many_expiries"] = True
                out[f"{col}_{c}"] = v
                vals.append(v)
            out[col] = float(sum(vals)) if vals else nan
    return out


# ---------------------------------------------------------------- H2 population and sample

def _fill_days(ts_ms) -> pd.Series:
    t = pd.Series(np.asarray(ts_ms, dtype="int64"))
    return pd.to_datetime(t - t % DAY_MS, unit="ms")


def h2_population(markouts: pd.DataFrame, snaps: pd.DataFrame, top: Sequence[int]) -> pd.DataFrame:
    """Maker fills (``maker_sub``) of the dominant subaccounts ``top`` in the PM2 window of their currency (at the
    fill time ``ts``) whose account is under a PM2 manager in the day-start snapshot of the UTC day of its own row
    (``ts_maker``); sorted by (ts, trade_id). Adds ``day_manager`` (manager label at the day start)."""
    m = markouts[markouts["maker_sub"].isin([int(x) for x in top])].copy()
    start = m["currency"].map(PM2_WINDOW_START)
    m = m[start.notna() & (m["ts"] // 1000 >= start.fillna(0))]
    lab = snaps.groupby(["subaccount", "day"])["manager_label"].first()
    key = pd.MultiIndex.from_arrays([m["maker_sub"].astype("int64").to_numpy(), _fill_days(m["ts_maker"]).to_numpy()])
    m["day_manager"] = lab.reindex(key).to_numpy()
    m = m[m["day_manager"].astype(str).str.startswith("PM2")]
    return m.sort_values(["ts", "trade_id"], kind="mergesort").reset_index(drop=True)


def h2_sample(pop: pd.DataFrame, n: int = H2_N, seed: int = H2_SEED) -> pd.DataFrame:
    """Simple random sample of ``n`` rows without replacement (``np.random.default_rng(seed).choice``, rows kept in
    the population order); the whole population when it has at most ``n`` rows."""
    if len(pop) <= n:
        return pop.reset_index(drop=True).copy()
    idx = np.sort(np.random.default_rng(seed).choice(len(pop), size=n, replace=False))
    return pop.iloc[idx].reset_index(drop=True)


# ---------------------------------------------------------------- FIFO holding time

class FifoInventory:
    """FIFO lots per instrument ``(ccy, expiry, strike, is_call)``; closing quantities are recorded as pieces
    ``(key, open_ms, close_ms, qty, how)`` for lots with a key (a maker fill), ``how`` in fill, transfer, expiry,
    censored. Lots without a key (taker fills, positions of unknown origin) are tracked but not recorded."""

    def __init__(self):
        self.lots: Dict[LegKey, deque] = {}
        self.pieces: List[Tuple[Optional[str], int, int, float, str]] = []
        self._heap: List[Tuple[int, LegKey]] = []

    def position(self, inst: LegKey) -> float:
        return float(sum(lot[1] for lot in self.lots.get(inst, ())))

    def _move(self, inst: LegKey, ts: int, q: float, key: Optional[str], how: str) -> float:
        lots = self.lots.get(inst)
        if lots is None:
            lots = self.lots[inst] = deque()
            heapq.heappush(self._heap, (int(inst[1]), inst))
        rem = float(q)
        while abs(rem) > AMOUNT_EPS and lots and (lots[0][1] > 0) != (rem > 0):
            lot = lots[0]
            c = min(abs(rem), abs(lot[1]))
            if lot[2] is not None:
                self.pieces.append((lot[2], lot[0], int(ts), c, how))
            lot[1] -= c if lot[1] > 0 else -c
            rem -= c if rem > 0 else -c
            if abs(lot[1]) <= AMOUNT_EPS:
                lots.popleft()
        if abs(rem) > AMOUNT_EPS:
            lots.append([int(ts), rem, key])
            return abs(rem)
        return 0.0

    def trade(self, inst: LegKey, ts: int, q: float, key: Optional[str] = None) -> float:
        """Apply a fill of ``q`` contracts (signed); returns the quantity that opened a new lot."""
        return self._move(inst, ts, q, key, "fill")

    def set_position(self, inst: LegKey, ts: int, target: float, how: str = "transfer") -> None:
        """Move the position to ``target`` (reconciliation with a day-start snapshot): a reduction closes the oldest
        lots with ``how``, an increase opens a lot of unknown origin."""
        delta = float(target) - self.position(inst)
        if abs(delta) > AMOUNT_EPS:
            self._move(inst, ts, delta, None, how)

    def expire(self, ts: int) -> None:
        """Close every lot of instruments with ``expiry * 1000 <= ts`` at their expiry (settlement)."""
        while self._heap and self._heap[0][0] * 1000 <= int(ts):
            e, inst = heapq.heappop(self._heap)
            for lot in self.lots.pop(inst, ()):
                if lot[2] is not None:
                    self.pieces.append((lot[2], lot[0], int(e) * 1000, abs(lot[1]), "expiry"))

    def close_all(self, ts: int, how: str = "censored") -> None:
        for inst, lots in self.lots.items():
            for lot in lots:
                if lot[2] is not None:
                    self.pieces.append((lot[2], lot[0], int(ts), abs(lot[1]), how))
        self.lots.clear()
        self._heap.clear()


PIECE_COLUMNS = ["key", "open_ms", "close_ms", "qty", "how"]


def _inst_positions(rows: pd.DataFrame, ccys: Sequence[str]) -> Dict[LegKey, float]:
    pos: Dict[LegKey, float] = defaultdict(float)
    r = rows[(rows["kind"] == "option") & rows["ccy"].isin(list(ccys))]
    for c, e, k, ic, a in zip(r["ccy"], r["expiry"], r["strike"], r["is_call"], r["amount"]):
        pos[(str(c), int(e), round(float(k), 8), bool(ic))] += float(a)
    return pos


def fifo_account(tape: pd.DataFrame, snaps: Optional[pd.DataFrame], end_ms: int, start_ms: Optional[int] = None,
                 ccys: Sequence[str] = SAMPLE_CCYS, reconcile: bool = True) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """FIFO over the tape fills of one subaccount (maker and taker rows, currencies ``ccys``) in time order, with the
    option positions reset to every day-start snapshot (00:00:01 UTC) before that day's fills: differences are
    transfers (trade module, liquidation) and close the oldest lots (``how = transfer``) or open lots of unknown
    origin. Lots are closed by later fills, at expiry, by transfers, or censored at ``end_ms``. Maker rows open lots
    keyed by ``trade_id``. Returns the pieces (:data:`PIECE_COLUMNS`) and the quantity each maker fill opened."""
    start_ms = int(start_ms) if start_ms is not None else _day_ts(START_DAY) * 1000
    events: List[Tuple[int, int, int, object]] = []
    if reconcile and snaps is not None and len(snaps):
        for i, (day, g) in enumerate(snaps.groupby("day", sort=True)):
            events.append(((_day_ts(day) + 1) * 1000, 0, i, _inst_positions(g, ccys)))
    t = tape[tape["currency"].isin(list(ccys)) & (tape["timestamp"] >= start_ms) & (tape["timestamp"] <= int(end_ms))]
    t = t.sort_values(["timestamp", "trade_id"], kind="mergesort")
    sign = np.where(t["direction"].astype(str).to_numpy() == "buy", 1.0, -1.0)
    for j, (ts, tid, role, c, e, k, cp, a, sg) in enumerate(zip(
            t["timestamp"], t["trade_id"], t["liquidity_role"], t["currency"], t["expiry"], t["strike"],
            t["option_type"], t["trade_amount"], sign)):
        inst = (str(c), int(e), round(float(k), 8), str(cp) == "C")
        events.append((int(ts), 1, j, (inst, float(a) * float(sg), str(tid) if role == "maker" else None)))
    events.sort(key=lambda x: (x[0], x[1], x[2]))
    inv = FifoInventory()
    opened: Dict[str, float] = {}
    for ts, kind, _, payload in events:
        if ts > int(end_ms):
            break
        inv.expire(ts)
        if kind == 0:
            pos = payload
            for inst in set(pos) | set(inv.lots):
                if inst[1] * 1000 > ts:
                    inv.set_position(inst, ts, pos.get(inst, 0.0))
        else:
            inst, q, key = payload
            got = inv.trade(inst, ts, q, key)
            if key is not None:
                opened[key] = opened.get(key, 0.0) + got
    inv.expire(int(end_ms))
    inv.close_all(int(end_ms))
    return pd.DataFrame(inv.pieces, columns=PIECE_COLUMNS), opened


def fill_holding_times(pieces: pd.DataFrame, opened: Dict[str, float]) -> pd.DataFrame:
    """Per maker fill that opened contracts: ``q_open``, the contract-weighted mean holding time in days over its
    closed pieces (``ht_days``; fill, expiry and transfer) and without transfers (``ht_days_excl_transfer``), and the
    contracts closed by each route (``c_fill, c_expiry, c_transfer, c_censored``)."""
    keys = [k for k, v in opened.items() if v > AMOUNT_EPS]
    out = pd.DataFrame({"trade_id": keys, "q_open": [float(opened[k]) for k in keys]})
    p = pieces.copy()
    p["days"] = (p["close_ms"].astype(float) - p["open_ms"].astype(float)) / DAY_MS
    p["w"] = p["qty"] * p["days"]

    def mean_days(sel: pd.DataFrame) -> pd.Series:
        g = sel.groupby("key")[["w", "qty"]].sum()
        return g["w"] / g["qty"]

    out["ht_days"] = out["trade_id"].map(mean_days(p[p["how"] != "censored"]))
    out["ht_days_excl_transfer"] = out["trade_id"].map(mean_days(p[p["how"].isin(["fill", "expiry"])]))
    by_how = p.groupby(["key", "how"])["qty"].sum()
    for how in ("fill", "expiry", "transfer", "censored"):
        s = by_how.xs(how, level="how") if how in by_how.index.get_level_values("how") else pd.Series(dtype=float)
        out[f"c_{how}"] = out["trade_id"].map(s).fillna(0.0)
    return out


def weighted_median(values, weights) -> float:
    """Lower weighted median: the smallest value whose cumulative weight reaches half the total."""
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    ok = np.isfinite(v) & np.isfinite(w) & (w > 0)
    v, w = v[ok], w[ok]
    if not len(v):
        return float("nan")
    o = np.argsort(v, kind="mergesort")
    v, w = v[o], w[o]
    c = np.cumsum(w)
    return float(v[min(int(np.searchsorted(c, 0.5 * c[-1])), len(v) - 1)])


CELL_KEYS = ["ccy", "side", "delta_bucket", "tenor_bucket"]


def holding_cells(fills: pd.DataFrame, ht: pd.DataFrame, pieces: pd.DataFrame) -> pd.DataFrame:
    """Holding time per Paper-1 cell (currency x maker side x |delta| bucket x tenor bucket) for ``window`` all and pm2
    (fills in the PM2 window of their currency). ``fills``: maker fills (``trade_id, currency, maker_side,
    delta_bucket, tenor_bucket, ts``); ``ht`` from :func:`fill_holding_times`; ``pieces`` with ``key, qty, days, how``.
    ``median_days`` is over opening fills, ``median_days_w`` the contract-weighted median over closed pieces; the
    shares split the opened contracts by how they were closed."""
    f = fills.copy()
    f["ccy"] = f["currency"].astype(str)
    f["side"] = np.where(f["maker_side"].to_numpy() > 0, "buy", "sell")
    start = f["ccy"].map(PM2_WINDOW_START)
    f["in_pm2"] = start.notna() & (f["ts"] // 1000 >= start.fillna(0))
    f = f.merge(ht, on="trade_id", how="left")
    closed = pieces[pieces["how"] != "censored"][["key", "qty", "days"]]
    rows = []
    for window, sub in (("all", f), ("pm2", f[f["in_pm2"]])):
        for cell, g in sub.groupby(CELL_KEYS, sort=True):
            op = g[g["q_open"].fillna(0.0) > AMOUNT_EPS]
            pc = closed[closed["key"].isin(set(op["trade_id"]))]
            qsum = float(op["q_open"].sum())
            rec = dict(zip(CELL_KEYS, cell))
            rec.update(window=window, n_fills=int(len(g)), n_opening=int(len(op)), q_open=qsum,
                       median_days=float(op["ht_days"].median()) if op["ht_days"].notna().any() else float("nan"),
                       median_days_w=weighted_median(pc["days"], pc["qty"]),
                       median_days_excl_transfer=float(op["ht_days_excl_transfer"].median())
                       if op["ht_days_excl_transfer"].notna().any() else float("nan"))
            for how in ("fill", "expiry", "transfer", "censored"):
                rec[f"share_{how}"] = float(op[f"c_{how}"].sum()) / qsum if qsum > 0 else float("nan")
            rows.append(rec)
    cols = ["window"] + CELL_KEYS + ["n_fills", "n_opening", "q_open", "median_days", "median_days_w",
                                     "median_days_excl_transfer", "share_fill", "share_expiry", "share_transfer",
                                     "share_censored"]
    return pd.DataFrame(rows, columns=cols)


# ---------------------------------------------------------------- B3: one fill, maker days, resumable runs

def fill_marginal(chain_book: Optional[Book], tape_book: Optional[Book], state, params, params_std, expiry: int,
                  strike: float, is_call: bool, q: float, price: float) -> dict:
    """All marginal-capital numbers of one maker fill under PM2 (``q`` signed contracts at ``price``).

    ``chain_book``: exact on-chain book before the fill's transaction in the fill's currency (``None`` = no position);
    ``tape_book``: the day-start + tape book (``None`` = not available). ``params`` are the account's PM2 parameters,
    ``params_std`` those of the standard lib (the single-contract capital of B2). Returns ``dK`` (IM, whole fill),
    ``dK_mm``, ``dK_unit`` (one contract in the fill's direction), ``dK_tape``, ``K_single_book(_mm)`` (per contract,
    standard lib, empty book), ``net_before/net_after``, book sizes and ``status`` (``ok`` / ``no_state``).
    """
    nan = float("nan")
    chain = _zero_cash(chain_book)
    new = OptionLeg(int(expiry), float(strike), bool(is_call), float(q))
    legs = list(chain.options) + [new] + (list(tape_book.options) if tape_book is not None else [])
    out = {"n_legs_before": len(chain.options), "n_expiries_before": len({leg.expiry for leg in chain.options}),
           "gross_before": float(sum(abs(leg.amount) for leg in chain.options)), "perp_before": float(chain.perp),
           "n_legs_tape": len(tape_book.options) if tape_book is not None else -1,
           "perp_tape": float(tape_book.perp) if tape_book is not None else nan, "tape_ok": tape_book is not None}
    keys = ("dK", "dK_mm", "dK_unit", "dK_tape", "K_single_book", "K_single_book_mm", "net_before", "net_after")
    vols = leg_vols(state, legs)
    perp = max(abs(chain.perp), abs(tape_book.perp) if tape_book is not None else 0.0)
    if not _state_ok(state, legs, vols, perp):
        out.update({k: nan for k in keys}, status="no_state")
        return out
    sgn = 1.0 if q > 0 else -1.0
    leg = (int(expiry), float(strike), bool(is_call))
    im = marginal_capital(chain, state, params, *leg, q, price, vols=vols)
    out.update(status="ok", dK=im["dK"], net_before=im["net_before"], net_after=im["net_after"])
    out["dK_unit"] = marginal_capital(chain, state, params, *leg, sgn, price, vols=vols,
                                      net_before=im["net_before"])["dK"]
    out["dK_mm"] = marginal_capital(chain, state, params, *leg, q, price, is_initial=False, vols=vols)["dK"]
    out["K_single_book"] = marginal_capital(None, state, params_std, *leg, sgn, price, vols=vols)["dK"]
    out["K_single_book_mm"] = marginal_capital(None, state, params_std, *leg, sgn, price, is_initial=False,
                                               vols=vols)["dK"]
    out["dK_tape"] = marginal_capital(tape_book, state, params, *leg, q, price, vols=vols)["dK"] \
        if tape_book is not None else nan
    return out


def maker_day_list(markouts: pd.DataFrame, top: Sequence[int], end_day: str = END_DAY) -> pd.DataFrame:
    """(subaccount, day) of every UTC day with at least one maker fill (day of the maker's own row ``ts_maker``) of
    the accounts ``top`` whose day start (00:00:01) lies in the PM2 window of BTC and ETH, up to ``end_day``."""
    m = markouts[markouts["maker_sub"].isin([int(x) for x in top])]
    df = pd.DataFrame({"subaccount": m["maker_sub"].astype("int64").to_numpy(), "day": _fill_days(m["ts_maker"]).to_numpy()})
    first = pd.Timestamp(min(PM2_WINDOW_START.values()) - 1, unit="s").ceil("D")
    df = df[(df["day"] >= first) & (df["day"] <= pd.Timestamp(end_day))]
    return df.drop_duplicates().sort_values(["subaccount", "day"], kind="mergesort").reset_index(drop=True)


class _Pm2Params:
    """PM2 parameters of the standard lib and of an account's lib (``p2params``), with cached timelines."""

    def __init__(self, root: Optional[Path] = None):
        self.root = root
        self._tl: Dict[Tuple[str, Optional[str]], object] = {}
        self._ov: Dict[str, list] = {}

    def timeline(self, ccy: str, lib: Optional[str] = None):
        from .p2params import Timeline

        key = (ccy, lib)
        if key not in self._tl:
            self._tl[key] = Timeline(ccy, "pm2", lib=lib, root=self.root)
        return self._tl[key]

    def lib(self, ccy: str, sub: int, ts: int) -> Optional[str]:
        from .p2params import account_lib, load_overrides

        if ccy not in self._ov:
            self._ov[ccy] = load_overrides(ccy, self.root)
        return account_lib(self._ov[ccy], int(sub), int(ts))

    def account(self, ccy: str, sub: int, ts: int) -> Tuple[dict, Optional[str]]:
        lib = self.lib(ccy, sub, ts)
        return self.timeline(ccy, lib).at(int(ts)), lib

    def standard(self, ccy: str, ts: int) -> dict:
        return self.timeline(ccy, None).at(int(ts))


def _labels(subs: Iterable[int]) -> Dict[int, str]:
    from . import p2ids

    subs = sorted({int(s) for s in subs})
    return dict(zip(subs, p2ids.labels(subs)))


def _block_ts(ts_s: int) -> int:
    """Timestamp of the block of second ``ts_s`` (the ``block.timestamp`` an eth_call at that block sees; B2)."""
    return ts_at_block(block_at_ts(int(ts_s)))


def _month_bounds(month: str) -> Tuple[int, int]:
    m0 = pd.Timestamp(month + "-01")
    m1 = m0 + pd.offsets.MonthBegin(1)
    return _day_ts(m0), _day_ts(m1)


MARKOUT_B3_COLUMNS = ["trade_id", "ts", "ts_maker", "currency", "maker_sub", "tx_hash", "amount", "price",
                      "maker_side", "expiry", "strike", "option_type"]
MARGINAL_PARTS = DERIVED_DIR / "marginal_parts" / "v1"
MAKER_DAY_PARTS = DERIVED_DIR / "maker_day_parts" / "v1"
CAPITAL_PATH = DERIVED_DIR / "capital.parquet"


def _atomic_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)


def _h2_inputs() -> Tuple[List[int], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    top = json.loads((BOOKS_DIR / "top_makers.json").read_text())["subaccounts"]
    snaps = pd.read_parquet(BOOKS_DIR / "snapshots.parquet")
    m = pd.read_parquet(MARKOUTS, columns=MARKOUT_B3_COLUMNS)
    m = m[m["maker_sub"].isin(top)].reset_index(drop=True)
    pop = h2_population(m, snaps, top)
    return top, snaps, pop, h2_sample(pop)


def _chunk_marginal(fills: pd.DataFrame, hist, ob: "OnchainBooks", snap_g: dict, tape_g: dict, prm: _Pm2Params,
                    registry: AssetRegistry) -> pd.DataFrame:
    empty = pd.DataFrame(columns=SNAPSHOT_COLUMNS)
    rows = []
    for sub, g in fills.groupby("maker_sub", sort=True):
        sub = int(sub)
        day_of: Dict[str, pd.Timestamp] = {}
        for tx in g["tx_hash"].astype(str).str.lower().unique():
            try:
                day_of[tx] = ob.locate(sub, tx)
            except KeyError:
                pass
        by_day: Dict[pd.Timestamp, List[str]] = defaultdict(list)
        for tx, d in day_of.items():
            by_day[d].append(tx)
        bals: Dict[str, Dict[BalanceKey, int]] = {}
        for d, txs in by_day.items():
            bals.update(replay_balances_many(ob._snap(sub, d), ob.events[(sub, d)], txs))
        for f in g.itertuples(index=False):
            ccy, tx = str(f.currency), str(f.tx_hash).lower()
            ts_s = int(f.ts) // 1000
            blk_ts = _block_ts(ts_s)
            q = float(f.maker_side) * float(f.amount)
            rec = {"fill_key": f.trade_id, "subaccount": sub, "ts": int(f.ts), "ts_maker": int(f.ts_maker),
                   "ccy": ccy, "manager": f.day_manager, "expiry": int(f.expiry), "strike": float(f.strike),
                   "is_call": str(f.option_type) == "C", "maker_side": int(f.maker_side), "amount": float(f.amount),
                   "q": q, "price": float(f.price), "block_ts": blk_ts}
            if tx not in day_of:
                rec["status"] = "no_tx"
                rows.append(rec)
                continue
            rec["chain_day"] = day_of[tx]
            chain = books_from_balances(bals[tx], blk_ts * 1000, registry).get(ccy)
            fday = fill_day(int(f.ts_maker))
            try:
                tb = book_before_fill(snap_g.get((sub, fday), empty), tape_g.get((sub, fday)), f.trade_id,
                                      subaccount=sub)
                tape_book = tb.get(ccy, Book())
            except (KeyError, ValueError):
                tape_book = None
            exps = {int(f.expiry)} | {leg.expiry for leg in (chain.options if chain else [])} \
                | {leg.expiry for leg in (tape_book.options if tape_book is not None else [])}
            state = hist.state_at(blk_ts, sorted(exps))
            params, lib = prm.account(ccy, sub, ts_s)
            rec["lib"] = lib or "std"
            rec.update(fill_marginal(chain, tape_book, state, params, prm.standard(ccy, ts_s), int(f.expiry),
                                     float(f.strike), str(f.option_type) == "C", q, float(f.price)))
            rows.append(rec)
    return pd.DataFrame(rows)


def run_marginal(max_seconds: float = 480.0, parts_dir: Path = MARGINAL_PARTS, log=print) -> dict:
    """Resumable H2 run: one part per (currency, month) of the sampled fills; FeedHistory is loaded per month."""
    import gc

    from .p2feeds import FeedHistory

    t0 = time.monotonic()
    top, snaps, pop, sample = _h2_inputs()
    sample = sample.assign(month=pd.to_datetime(sample["ts"], unit="ms").dt.strftime("%Y-%m"))
    chunks = sorted(sample.groupby(["currency", "month"]).groups)
    todo = [(c, m) for c, m in chunks if not (Path(parts_dir) / f"{c}_{m}.parquet").exists()]
    log(f"population {len(pop)}, sample {len(sample)}, chunks {len(chunks)}, todo {len(todo)}")
    if todo:
        accs = sorted(int(x) for x in sample["maker_sub"].unique())
        tape = load_tape(accs)
        tape = tape.assign(_day=_fill_days(tape["timestamp"]).to_numpy())
        tape_g = {(int(a), pd.Timestamp(d)): g for (a, d), g in tape.groupby(["subaccount_id", "_day"])}
        snaps_a = snaps[snaps["subaccount"].isin(accs)]
        snap_g = {(int(a), pd.Timestamp(d)): g for (a, d), g in snaps_a.groupby(["subaccount", "day"])}
        prm, reg = _Pm2Params(), default_registry()
    done = 0
    for ccy, month in todo:
        if time.monotonic() - t0 > max_seconds:
            break
        fills = sample[(sample["currency"] == ccy) & (sample["month"] == month)]
        lo, hi = _month_bounds(month)
        d_lo, d_hi = pd.Timestamp(lo - 86400, unit="s"), pd.Timestamp(hi + 2 * 86400, unit="s")
        subs = sorted(int(x) for x in fills["maker_sub"].unique())
        ev = pd.read_parquet(BOOKS_DIR / "events.parquet",
                             filters=[("subaccount", "in", subs), ("day", ">=", d_lo), ("day", "<=", d_hi)])
        sn = snaps_a[snaps_a["subaccount"].isin(subs) & (snaps_a["day"] >= d_lo) & (snaps_a["day"] <= d_hi)]
        ob = OnchainBooks(sn, ev, reg)
        hist = FeedHistory(ccy, start_ts=lo - 3600, end_ts=hi + 3600)
        t1 = time.monotonic()
        df = _chunk_marginal(fills, hist, ob, snap_g, tape_g, prm, reg)
        _atomic_parquet(df, Path(parts_dir) / f"{ccy}_{month}.parquet")
        done += 1
        log(f"{ccy} {month}: {len(df)} fills, status {df['status'].value_counts().to_dict()}, "
            f"{time.monotonic() - t1:.0f}s compute, {time.monotonic() - t0:.0f}s total")
        del hist, ob, ev
        gc.collect()
    remaining = len(todo) - done
    return {"chunks": len(chunks), "done": done, "remaining": remaining, "population": int(len(pop)),
            "sample": int(len(sample))}


def combine_marginal(parts_dir: Path = MARGINAL_PARTS, out: Path = DERIVED_DIR / "marginal.parquet",
                     capital: Path = CAPITAL_PATH) -> Tuple[pd.DataFrame, dict]:
    """All parts into ``marginal.parquet`` with ``K_single_pm2(_mm)`` from B2 and the ratios; consistency check of
    the book engine on the one-contract book against B2 (``K_single_book`` vs ``K_single_pm2``)."""
    df = pd.concat([pd.read_parquet(f) for f in sorted(Path(parts_dir).glob("*.parquet"))], ignore_index=True)
    cap = pd.read_parquet(capital, columns=["trade_id", "K_pm2", "K_pm2_mm"]).rename(
        columns={"trade_id": "fill_key", "K_pm2": "K_single_pm2", "K_pm2_mm": "K_single_pm2_mm"})
    df = df.merge(cap, on="fill_key", how="left")
    df["day"] = _fill_days(df["ts"]).to_numpy()
    df["label"] = df["subaccount"].map(_labels(df["subaccount"]))
    a = df["amount"].to_numpy(dtype=float)
    for src, dst in (("dK", "dK_per_contract"), ("dK_mm", "dK_mm_per_contract"), ("dK_tape", "dK_tape_per_contract")):
        df[dst] = df[src] / a
    ks, ksm = df["K_single_pm2"], df["K_single_pm2_mm"]
    df["ratio"] = (df["dK_per_contract"] / ks).where(ks > 0)
    df["ratio_unit"] = (df["dK_unit"] / ks).where(ks > 0)
    df["ratio_tape"] = (df["dK_tape_per_contract"] / ks).where(ks > 0)
    df["ratio_mm"] = (df["dK_mm_per_contract"] / ksm).where(ksm > 0)
    ok = df["status"] == "ok"
    d = (df.loc[ok, "K_single_book"] - df.loc[ok, "K_single_pm2"]).abs()
    rel = d / df.loc[ok, "K_single_pm2"].abs().clip(lower=1e-12)
    dm = (df.loc[ok, "K_single_book_mm"] - df.loc[ok, "K_single_pm2_mm"]).abs()
    lead = ["fill_key", "subaccount", "label", "day", "ts", "ts_maker", "block_ts", "ccy", "manager", "lib"]
    df = df[lead + [c for c in df.columns if c not in lead]]
    df = df.sort_values(["ts", "fill_key"], kind="mergesort").reset_index(drop=True)
    _atomic_parquet(df, Path(out))
    check = {"rows": int(len(df)), "status": {str(k): int(v) for k, v in df["status"].value_counts().items()},
             "tape_ok": int(df["tape_ok"].fillna(False).astype(bool).sum()),
             "k_single_missing": int(df["K_single_pm2"].isna().sum()),
             "k_single_le_0": int((df["K_single_pm2"] <= 0).sum()),
             "single_vs_b2_max_abs": float(d.max()) if len(d) else float("nan"),
             "single_vs_b2_max_rel": float(rel.max()) if len(rel) else float("nan"),
             "single_mm_vs_b2_max_abs": float(dm.max()) if len(dm) else float("nan"),
             "empty_book_fills": int((df.loc[ok, "n_legs_before"] == 0).sum()),
             "empty_book_dK_vs_single_max_abs": float(
                 ((df.loc[ok & (df["n_legs_before"] == 0) & (df["perp_before"] == 0), "dK_per_contract"]
                   - df.loc[ok & (df["n_legs_before"] == 0) & (df["perp_before"] == 0), "K_single_book"]).abs().max())
                 if (ok & (df["n_legs_before"] == 0) & (df["perp_before"] == 0)).any() else float("nan"))}
    return df, check


MAKER_DAY_LEAD = ["subaccount", "label", "day", "ts", "manager", "status", "ccys", "n_legs", "n_legs_pm",
                  "gross_contracts", "perp_gross", "n_expiries_max", "premium", "K_sm", "K_pm", "K_pm2", "K_sm_mm",
                  "K_pm_mm", "K_pm2_mm", "pm_too_many_expiries", "pm2_over_max_expiries"]


def _maker_day_books(snap: pd.DataFrame, day) -> Dict[str, Book]:
    ts = _day_ts(day) + 1
    legs, perps = _snapshot_positions(snap)
    return filter_pm2_window(_books_from_positions(legs, perps, ts * 1000), ts)


def _chunk_maker_days(days: pd.DataFrame, snap_g: dict, month: str, prm: _Pm2Params, history_factory) -> pd.DataFrame:
    import gc

    from .p2params import Timeline

    items = []
    need: Dict[str, Dict[Tuple[int, pd.Timestamp], List[int]]] = defaultdict(dict)
    for r in days.itertuples(index=False):
        sub, day = int(r.subaccount), pd.Timestamp(r.day)
        snap = snap_g.get((sub, day))
        rec = {"subaccount": sub, "day": day, "ts": _day_ts(day) + 1}
        if snap is None:
            rec["status"] = "no_snapshot"
            items.append((rec, None))
            continue
        rec["manager"] = _single(snap, "manager_label")
        bks = _maker_day_books(snap, day)
        if not any(b.options for b in bks.values()):
            rec["status"] = "no_options"
            items.append((rec, None))
            continue
        for c, b in bks.items():
            need[c][(sub, day)] = sorted({leg.expiry for leg in b.options})
        items.append((rec, bks))
    lo, hi = _month_bounds(month)
    states: Dict[Tuple[int, pd.Timestamp], Dict[str, object]] = defaultdict(dict)
    for c in sorted(need):
        hist = history_factory(c, lo - 3600, hi + 3600)
        for (sub, day), exps in need[c].items():
            states[(sub, day)][c] = hist.state_at(_day_ts(day) + 1, exps)
        del hist
        gc.collect()
    tls: Dict[Tuple[str, str], Optional[Timeline]] = {}

    def at(c: str, mgr: str, ts: int) -> Optional[dict]:
        """Standard-lib parameters in force at ``ts``; None outside the manager's timeline (e.g. HYPE legacy PM)."""
        if (c, mgr) not in tls:
            try:
                tls[(c, mgr)] = Timeline(c, mgr)
            except FileNotFoundError:
                tls[(c, mgr)] = None
        tl = tls[(c, mgr)]
        try:
            return tl.at(ts) if tl is not None else None
        except KeyError:
            return None

    rows = []
    for rec, bks in items:
        if bks is None:
            rows.append(rec)
            continue
        sub, day, ts = rec["subaccount"], rec["day"], rec["ts"]
        params = {"sm": {}, "pm": {}, "pm2": {}}
        for c in bks:
            for mgr in ("sm", "pm"):
                p = at(c, mgr, ts) if (mgr == "sm" or c in LEGACY_PM_CCYS) else None
                if p is not None:
                    params[mgr][c] = p
            params["pm2"][c] = prm.account(c, sub, ts)[0]
        rec.update(maker_day_capital(bks, states[(sub, day)], params))
        rows.append(rec)
    return pd.DataFrame(rows)


def _default_history(ccy: str, start_ts: int, end_ts: int):
    from .p2feeds import FeedHistory

    return FeedHistory(ccy, start_ts=start_ts, end_ts=end_ts)


def run_maker_days(max_seconds: float = 480.0, parts_dir: Path = MAKER_DAY_PARTS, log=print,
                   history_factory=_default_history) -> dict:
    """Resumable netting-value run: one part per month of maker days, one FeedHistory window per currency."""
    t0 = time.monotonic()
    top = json.loads((BOOKS_DIR / "top_makers.json").read_text())["subaccounts"]
    m = pd.read_parquet(MARKOUTS, columns=["maker_sub", "ts_maker"])
    days = maker_day_list(m, top)
    days = days.assign(month=days["day"].dt.strftime("%Y-%m"))
    months = sorted(days["month"].unique())
    todo = [mo for mo in months if not (Path(parts_dir) / f"{mo}.parquet").exists()]
    log(f"maker days {len(days)}, months {len(months)}, todo {len(todo)}")
    if todo:
        snaps = pd.read_parquet(BOOKS_DIR / "snapshots.parquet")
        snaps = snaps[snaps["subaccount"].isin(top) & (snaps["day"] >= days["day"].min())]
        snap_g = {(int(a), pd.Timestamp(d)): g for (a, d), g in snaps.groupby(["subaccount", "day"])}
        prm = _Pm2Params()
    done = 0
    for mo in todo:
        if time.monotonic() - t0 > max_seconds:
            break
        t1 = time.monotonic()
        df = _chunk_maker_days(days[days["month"] == mo], snap_g, mo, prm, history_factory)
        _atomic_parquet(df, Path(parts_dir) / f"{mo}.parquet")
        done += 1
        log(f"{mo}: {len(df)} maker days, status {df['status'].value_counts().to_dict()}, "
            f"{time.monotonic() - t1:.0f}s, {time.monotonic() - t0:.0f}s total")
    return {"months": len(months), "done": done, "remaining": len(todo) - done, "maker_days": int(len(days))}


def combine_maker_days(parts_dir: Path = MAKER_DAY_PARTS, out: Path = DERIVED_DIR / "maker_days.parquet") -> Tuple[pd.DataFrame, dict]:
    df = pd.concat([pd.read_parquet(f) for f in sorted(Path(parts_dir).glob("*.parquet"))], ignore_index=True)
    df["label"] = df["subaccount"].map(_labels(df["subaccount"]))
    for mgr in ("sm", "pm", "pm2"):
        for ccy in (("BTC", "ETH") if mgr == "pm" else SAMPLE_CCYS):
            for sfx in ("", "_mm"):
                col = f"K_{mgr}{sfx}_{ccy}"
                if col not in df.columns:
                    df[col] = np.nan
    for ccy in SAMPLE_CCYS:
        if f"premium_{ccy}" not in df.columns:
            df[f"premium_{ccy}"] = np.nan
    for col in MAKER_DAY_LEAD:
        if col not in df.columns:
            df[col] = np.nan
    df = df[MAKER_DAY_LEAD + sorted(c for c in df.columns if c not in MAKER_DAY_LEAD)]
    df = df.sort_values(["subaccount", "day"], kind="mergesort").reset_index(drop=True)
    _atomic_parquet(df, Path(out))
    ok = df["status"] == "ok"
    check = {"rows": int(len(df)), "status": {str(k): int(v) for k, v in df["status"].value_counts().items()},
             "by_label": {str(k): int(v) for k, v in df.loc[ok, "label"].value_counts().sort_index().items()},
             "nan_ok": {c: int(df.loc[ok, c].isna().sum()) for c in ("K_sm", "K_pm", "K_pm2", "K_sm_mm", "K_pm_mm",
                                                                      "K_pm2_mm")},
             "pm_too_many_expiries": int(df.loc[ok, "pm_too_many_expiries"].fillna(False).astype(bool).sum()),
             "pm2_over_max_expiries": int(df.loc[ok, "pm2_over_max_expiries"].fillna(False).astype(bool).sum()),
             "no_btc_eth_legs": int((df.loc[ok, "n_legs_pm"] == 0).sum())}
    return df, check


def run_holding(out_csv: Path = Path("results/p2/holding_time.csv"),
                out_fills: Path = DERIVED_DIR / "holding_fills.parquet", end_ms: int = PILOT_END_MS) -> dict:
    """FIFO holding time of the maker fills of the ten dominant subaccounts, median per Paper-1 cell."""
    top = json.loads((BOOKS_DIR / "top_makers.json").read_text())["subaccounts"]
    snaps = pd.read_parquet(BOOKS_DIR / "snapshots.parquet",
                            columns=["subaccount", "day", "kind", "ccy", "expiry", "strike", "is_call", "amount"])
    snaps = snaps[snaps["subaccount"].isin(top)]
    tape = load_tape(top)
    all_pieces, opened = [], {}
    for sub in top:
        pc, op = fifo_account(tape[tape["subaccount_id"] == int(sub)], snaps[snaps["subaccount"] == int(sub)], end_ms)
        all_pieces.append(pc.assign(subaccount=int(sub)))
        opened.update(op)
    pieces = pd.concat(all_pieces, ignore_index=True)
    pieces["days"] = (pieces["close_ms"].astype(float) - pieces["open_ms"].astype(float)) / DAY_MS
    ht = fill_holding_times(pieces, opened)
    fills = pd.read_parquet(MARKOUTS, columns=["trade_id", "ts", "currency", "maker_sub", "maker_side", "delta_bucket",
                                               "tenor_bucket"])
    fills = fills[fills["maker_sub"].isin(top)].reset_index(drop=True)
    cells = holding_cells(fills, ht, pieces)
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    cells.to_csv(out_csv, index=False, float_format="%.6g")
    f2 = fills.merge(ht, on="trade_id", how="left")
    f2["label"] = f2["maker_sub"].map(_labels(f2["maker_sub"]))
    _atomic_parquet(f2, Path(out_fills))
    in_tape = set(tape.loc[tape["liquidity_role"] == "maker", "trade_id"].astype(str))
    q = pieces.groupby("how")["qty"].sum()
    return {"maker_fills": int(len(fills)), "maker_fills_in_tape": int(fills["trade_id"].astype(str).isin(in_tape).sum()),
            "opening_fills": int(len(ht)), "contracts_opened": float(ht["q_open"].sum()),
            "contracts_by_how": {str(k): float(v) for k, v in q.items()}, "cells": int(len(cells)),
            "cells_all": int((cells["window"] == "all").sum()), "cells_pm2": int((cells["window"] == "pm2").sum())}


# ---------------------------------------------------------------- CLI helpers

def load_tape(subaccounts: Sequence[int], ccys: Sequence[str] = SAMPLE_CCYS, tape_dir: Path = TAPE_DIR) -> pd.DataFrame:
    cols = ["trade_id", "timestamp", "instrument_name", "direction", "liquidity_role", "trade_amount", "subaccount_id",
            "currency", "expiry", "strike", "option_type", "tx_hash"]
    frames = []
    for c in ccys:
        t = pd.read_parquet(Path(tape_dir) / f"{c}_options_full.parquet", columns=cols)
        frames.append(t[t["subaccount_id"].isin([int(s) for s in subaccounts])])
    return pd.concat(frames, ignore_index=True)


def reconcile_all(snaps: pd.DataFrame, tape: pd.DataFrame, n_sample: int = 20, seed: int = 20260924,
                  lags_ms: Sequence[int] = (0, 10_000, 60_000, 300_000)) -> dict:
    """Reconcile every maker day (>= 1 maker fill, next day-start snapshot present) and a random sample of them."""
    tape = tape.copy()
    tape["day"] = pd.to_datetime(tape["timestamp"], unit="ms").dt.floor("D")
    maker_days = tape[tape["liquidity_role"] == "maker"].groupby(["subaccount_id", "day"]).size().index
    snap_groups = {k: g for k, g in snaps.groupby(["subaccount", "day"])}
    tape_groups = {k: g for k, g in tape.groupby(["subaccount_id", "day"])}
    cand = [(int(s), d) for s, d in maker_days if (s, d) in snap_groups and (s, d + pd.Timedelta(days=1)) in snap_groups]
    rows = []
    for s, d in cand:
        t = pd.concat([g for g in (tape_groups.get((s, d - pd.Timedelta(days=1))), tape_groups.get((s, d))) if g is not None])
        row = {"subaccount": s, "day": d.strftime("%Y-%m-%d")}
        for lag in lags_ms:
            r = reconcile_day(snap_groups[(s, d)], snap_groups[(s, d + pd.Timedelta(days=1))], t, lag_ms=lag, ccys=SAMPLE_CCYS)
            row.update({f"{k}_lag{lag // 1000}s": v for k, v in r.items()})
        rows.append(row)
    res = pd.DataFrame(rows)
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(len(res), size=min(n_sample, len(res)), replace=False)) if len(res) else []
    sample = res.iloc[idx]

    def quote(df: pd.DataFrame, lag: int) -> dict:
        s = f"_lag{lag // 1000}s"
        return {"maker_days": int(len(df)), "days_full_match": int(df["day_match" + s].sum()),
                "legs": int(df["n_legs" + s].sum()), "legs_match": int(df["n_match" + s].sum()),
                "median_max_abs_diff": float(df["max_abs_diff" + s].median()) if len(df) else 0.0}

    return {"sample": {str(lag // 1000) + "s": quote(sample, lag) for lag in lags_ms},
            "all": {str(lag // 1000) + "s": quote(res, lag) for lag in lags_ms},
            "sample_rows": sample.to_dict("records"),
            "per_account": {str(s): {"maker_days": int(len(g)), "days_full_match": int(g["day_match_lag0s"].sum())}
                            for s, g in res.groupby("subaccount")}}


def pm2_accounts(snaps: pd.DataFrame) -> List[int]:
    """Subaccounts whose manager is a PM2 manager on any day-start snapshot."""
    lab = snaps.groupby("subaccount")["manager_label"].agg(lambda x: set(x))
    return sorted(int(a) for a, v in lab.items() if any(str(x).startswith("PM2") for x in v))


def _loaded_event_items(out_dir: Path = EVENTS_DIR) -> set:
    out = set()
    for f in Path(out_dir).glob("*.parquet"):
        acc, day = f.stem.split("_")
        out.add((int(acc), day))
    return out


def compare_tape_vs_chain(snaps: pd.DataFrame, events: pd.DataFrame, tape: pd.DataFrame, fills: pd.DataFrame,
                          registry: Optional[AssetRegistry] = None) -> pd.DataFrame:
    """For maker fills (``maker_sub, trade_id, ts_maker, currency, tx_hash``): preregistered tape book
    (:func:`book_before_fill`) against the exact on-chain book (:class:`OnchainBooks`), both with the expiry cut at
    ``ts_maker``, in the fill's currency."""
    ob = OnchainBooks(snaps, events, registry)
    snap_g = {(int(s), pd.Timestamp(d)): g for (s, d), g in snaps.groupby(["subaccount", "day"])}
    tape = tape.assign(_day=[fill_day(t) for t in tape["timestamp"]])
    tape_g = {(int(s), pd.Timestamp(d)): g for (s, d), g in tape.groupby(["subaccount_id", "_day"])}
    empty = pd.DataFrame(columns=SNAPSHOT_COLUMNS)
    rows = []
    for f in fills.itertuples(index=False):
        sub, day = int(f.maker_sub), fill_day(f.ts_maker)
        rec = {"subaccount": sub, "trade_id": f.trade_id, "ccy": f.currency, "day": day,
               "rfq_lag_ms": int(f.ts) - int(f.ts_maker)}
        tb = book_before_fill(snap_g.get((sub, day), empty), tape_g.get((sub, day)), f.trade_id, subaccount=sub)
        try:
            cb = ob.before(sub, f.tx_hash, ts=int(f.ts_maker))
        except KeyError:
            rec["chain_found"] = False
            rows.append(rec)
            continue
        rec["chain_found"] = True
        rec["chain_day_differs"] = bool(ob.locate(sub, f.tx_hash) != day)
        rec.update(compare_books(tb.get(f.currency), cb.get(f.currency)))
        rows.append(rec)
    return pd.DataFrame(rows)


def _compare_summary(df: pd.DataFrame) -> dict:
    ok = df[df["chain_found"]]
    rel = (ok["gross_abs_diff"] / ok["gross_chain"].where(ok["gross_chain"] > 0)).dropna()
    both = ok["options_equal"] & ok["perp_equal"]
    return {"fills": int(len(df)), "chain_found": int(len(ok)),
            "options_equal": int(ok["options_equal"].sum()), "perp_equal": int(ok["perp_equal"].sum()),
            "both_equal": int(both.sum()),
            "share_options_equal": float(ok["options_equal"].mean()) if len(ok) else float("nan"),
            "share_perp_equal": float(ok["perp_equal"].mean()) if len(ok) else float("nan"),
            "share_both_equal": float(both.mean()) if len(ok) else float("nan"),
            "median_rel_gross_diff": float(rel.median()) if len(rel) else float("nan"),
            "p90_rel_gross_diff": float(rel.quantile(0.9)) if len(rel) else float("nan"),
            "median_abs_perp_diff": float((ok["perp_tape"] - ok["perp_chain"]).abs().median()) if len(ok) else float("nan"),
            "median_rel_perp_diff": float(((ok["perp_tape"] - ok["perp_chain"]).abs()
                                           / ok["perp_chain"].abs().where(ok["perp_chain"].abs() > AMOUNT_EPS)).median())
            if len(ok) else float("nan"),
            "chain_day_differs": int(ok["chain_day_differs"].sum()) if len(ok) else 0}


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(prog="python3 -m derive_surface.books", description="Maker books (Paper 2, A5)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("top", help="top-10 maker subaccounts -> data/p2/books/top_makers.json")
    ld = sub.add_parser("load", help="resumable day-start snapshots")
    ld.add_argument("--max-seconds", type=float, default=520.0)
    ld.add_argument("--start", default=START_DAY)
    ld.add_argument("--end", default=END_DAY)
    sub.add_parser("compact", help="raw day files -> snapshots.parquet")
    rc = sub.add_parser("reconcile", help="day-start + fills vs next day-start")
    rc.add_argument("--n", type=int, default=20)
    rc.add_argument("--seed", type=int, default=20260924)
    ev = sub.add_parser("events", help="BalanceAdjusted events of the maker days (resumable, fills gaps)")
    ev.add_argument("--accounts", choices=["pm2", "all"], default="pm2")
    ev.add_argument("--max-seconds", type=float, default=520.0)
    sub.add_parser("perp-drift", help="day-to-day perp changes per account -> perp_drift.json")
    sub.add_parser("verify-events", help="snapshot + events == next snapshot per loaded day -> events_verify.json")
    cp = sub.add_parser("compare", help="tape book vs exact on-chain book at sampled maker fills")
    cp.add_argument("--accounts", choices=["pm2", "all"], default="pm2")
    cp.add_argument("--n", type=int, default=3000)
    cp.add_argument("--seed", type=int, default=20260924)
    mg = sub.add_parser("marginal", help="B3: marginal capital of the H2 sample (resumable) -> derived/marginal.parquet")
    mg.add_argument("--max-seconds", type=float, default=480.0)
    md = sub.add_parser("maker-days", help="B3: netting value of the maker days (resumable) -> derived/maker_days.parquet")
    md.add_argument("--max-seconds", type=float, default=480.0)
    sub.add_parser("holding", help="B3: FIFO holding time per cell -> results/p2/holding_time.csv")
    a = ap.parse_args(argv)
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    top_path = BOOKS_DIR / "top_makers.json"
    if a.cmd == "top":
        m = pd.read_parquet(MARKOUTS, columns=["maker_sub"])
        top = top_maker_subaccounts(10, m)
        counts = m["maker_sub"].value_counts()
        top_path.write_text(json.dumps({"subaccounts": top, "maker_fills": {str(s): int(counts[s]) for s in top},
                                        "total_fills": int(len(m))}, indent=1))
        print(json.dumps([{"sha10": sha10(s), "maker_fills": int(counts[s])} for s in top], indent=1))
    elif a.cmd == "load":
        top = json.loads(top_path.read_text())["subaccounts"]
        rpc = Rpc(rate=2.0, log_path=LOG_PATH)
        st = load_snapshots(rpc, top, a.start, a.end, max_seconds=a.max_seconds)
        print(json.dumps(st))
    elif a.cmd == "compact":
        df = compact()
        print(len(df), "rows;", df.groupby("kind").size().to_dict())
    elif a.cmd == "reconcile":
        top = json.loads(top_path.read_text())["subaccounts"]
        snaps = pd.read_parquet(BOOKS_DIR / "snapshots.parquet")
        out = reconcile_all(snaps, load_tape(top), n_sample=a.n, seed=a.seed)
        (BOOKS_DIR / "reconcile.json").write_text(json.dumps(out, indent=1, default=str))
        print(json.dumps({"sample": out["sample"], "all": out["all"]}, indent=1))
    elif a.cmd == "events":
        top = json.loads(top_path.read_text())["subaccounts"]
        snaps = pd.read_parquet(BOOKS_DIR / "snapshots.parquet")
        accs = pm2_accounts(snaps) if a.accounts == "pm2" else top
        tape = load_tape(accs)
        maker = tape[tape["liquidity_role"] == "maker"]
        extra_path = BOOKS_DIR / "events_extra.json"
        extra = {(int(x), str(d)) for x, d in json.loads(extra_path.read_text())} if extra_path.exists() else set()
        items = event_days_for_fills(maker) | extra
        rpc = Rpc(rate=2.0, log_path=LOG_PATH)
        st = load_events(rpc, items, max_seconds=a.max_seconds)
        print(json.dumps(st))
        if st["remaining"] == 0:
            df = compact_events()
            new = missing_fill_days(maker, df, _loaded_event_items())
            if new:
                extra_path.write_text(json.dumps(sorted(extra | new)))
                print(json.dumps({"gap_days_added": len(new), "rerun": True}))
            else:
                found = set(zip(df["subaccount"], df["tx_hash"]))
                miss = [(int(s_), tx) for s_, tx in zip(maker["subaccount_id"], maker["tx_hash"].str.lower())
                        if (int(s_), tx) not in found]
                cov = {"maker_rows": int(len(maker)), "tx_found": int(len(maker) - len(miss)), "missing": len(miss),
                       "account_days": len(_loaded_event_items()), "events": int(len(df)),
                       "events_by_kind": {str(k): int(v) for k, v in df["kind"].value_counts().items()}}
                (BOOKS_DIR / "events_coverage.json").write_text(json.dumps(cov, indent=1))
                print(json.dumps(cov, indent=1))
    elif a.cmd == "verify-events":
        snaps = pd.read_parquet(BOOKS_DIR / "snapshots.parquet")
        events = pd.read_parquet(BOOKS_DIR / "events.parquet")
        v = verify_event_days(snaps[snaps["subaccount"].isin(events["subaccount"].unique())], events)
        out = {"account_days": int(len(v)), "chain_ok": int(v["chain_ok"].sum()), "exact": int(v["exact"].sum()),
               "events": int(v["n_events"].sum()),
               "per_account": {sha10(s_): {"days": int(len(g)), "exact": int(g["exact"].sum())}
                               for s_, g in v.groupby("subaccount")},
               "not_exact": [{"sha10": sha10(r.subaccount), "day": r.day.strftime("%Y-%m-%d"), "chain_ok": bool(r.chain_ok),
                              "n_diff": int(r.n_diff)} for r in v[~v["exact"].astype(bool)].itertuples()]}
        (BOOKS_DIR / "events_verify.json").write_text(json.dumps(out, indent=1))
        print(json.dumps(out, indent=1))
    elif a.cmd == "perp-drift":
        snaps = pd.read_parquet(BOOKS_DIR / "snapshots.parquet")
        res = {}
        for name, cc in (("all", None), ("sample_ccys", SAMPLE_CCYS)):
            d = perp_drift(snaps, cc)
            d["sha10"] = d["subaccount"].map(sha10)
            d["manager_label"] = d["subaccount"].map(snaps.groupby("subaccount")["manager_label"].first())
            res[name] = d.drop(columns="subaccount").to_dict("records")
        (BOOKS_DIR / "perp_drift.json").write_text(json.dumps(res, indent=1))
        print(json.dumps(res["sample_ccys"], indent=1))
    elif a.cmd == "compare":
        top = json.loads(top_path.read_text())["subaccounts"]
        snaps = pd.read_parquet(BOOKS_DIR / "snapshots.parquet")
        accs = pm2_accounts(snaps) if a.accounts == "pm2" else top
        events = pd.read_parquet(BOOKS_DIR / "events.parquet")
        events = events[events["subaccount"].isin(accs)]
        m = pd.read_parquet(MARKOUTS, columns=["trade_id", "ts", "ts_maker", "currency", "tx_hash", "maker_sub"])
        m = m[m["maker_sub"].isin(accs)].reset_index(drop=True)
        rng = np.random.default_rng(a.seed)
        fills = m.iloc[np.sort(rng.choice(len(m), size=min(a.n, len(m)), replace=False))]
        df = compare_tape_vs_chain(snaps[snaps["subaccount"].isin(accs)], events, load_tape(accs), fills)
        out = {"n": int(len(fills)), "population": int(len(m)), "seed": a.seed, "all": _compare_summary(df),
               "rfq_lagged": _compare_summary(df[df["rfq_lag_ms"] > 0]),
               "per_account": {sha10(s_): _compare_summary(g) for s_, g in df.groupby("subaccount")}}
        (BOOKS_DIR / "compare_books.json").write_text(json.dumps(out, indent=1, default=str))
        print(json.dumps(out, indent=1, default=str))
    elif a.cmd == "marginal":
        st = run_marginal(a.max_seconds)
        if st["remaining"] == 0:
            _, check = combine_marginal()
            st["check"] = check
            (DERIVED_DIR / "marginal_check.json").write_text(json.dumps(check, indent=1))
        print(json.dumps(st, indent=1, default=str))
        print("DONE" if st["remaining"] == 0 else "RERUN")
    elif a.cmd == "maker-days":
        st = run_maker_days(a.max_seconds)
        if st["remaining"] == 0:
            _, check = combine_maker_days()
            st["check"] = check
            (DERIVED_DIR / "maker_days_check.json").write_text(json.dumps(check, indent=1))
        print(json.dumps(st, indent=1, default=str))
        print("DONE" if st["remaining"] == 0 else "RERUN")
    elif a.cmd == "holding":
        st = run_holding()
        (DERIVED_DIR / "holding_check.json").write_text(json.dumps(st, indent=1))
        print(json.dumps(st, indent=1))


if __name__ == "__main__":
    main()
