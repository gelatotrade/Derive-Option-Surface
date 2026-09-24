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
import json
import os
import time
from collections import defaultdict
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


if __name__ == "__main__":
    main()
