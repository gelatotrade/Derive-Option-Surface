"""Validation of the margin replicas against the chain (Paper 2, task B1; gate of the pre-registration).

The replica (``FeedHistory.state_at`` from ``data/p2/feeds`` plus the Paper 1 SVI history, ``Timeline.at`` from
``results/p2/params`` and ``margin_sm`` / ``margin_pm`` / ``margin_pm2.net_margin``) is compared with the deployed
managers at the same block. The chain side builds the portfolio itself from its own feeds: a synthetic account
``SYNTHETIC_ACCOUNT`` is given exactly the book's balances by an ``eth_call`` state override of ``SubAccounts``
(``heldAssets`` and ``balanceAndOrder``), and the manager's own ``getMargin(account, isInitial)`` is called
(``StandardManager``, legacy ``PMRM``, ``PMRM_2``). Nothing of our feed data enters the chain call.

* Capital: ``K = sum p q - net(q; cash = 0)``; ``net`` of the chain is ``getMargin`` minus the perp's
  ``getUnsettledAndUnrealizedCash`` of the synthetic account (so a perp enters at the engine's perp price, as in the
  replica with ``perp_entry = None``). Both managers add that cash linearly to margin and MtM.
* Books too large for the node's ``eth_call`` gas cap (PM2 with some 300 legs needs about 110 M gas, the cap is
  50 M) are evaluated per scenario: ``getMarginAndMarkToMarket(account, isInitial, j)`` runs the lib with scenario
  ``j`` alone; because the requirement is monotone in ``minSPAN = min(basis, pnl_j)`` the net over all scenarios is
  the minimum over ``j`` of these nets (exact, also in fixed point).
* Singles: per currency and manager window (pre-registration) ``N_SINGLE`` random blocks (seed 20260924, one
  ``SeedSequence`` child per cell), one contract per block: a fill of the same UTC day from the Paper 1 tape whose
  expiry is live (forward push at most 1 h old) and has a fresh vol push (signed at most 20 min before the block),
  random side, ``p`` = fill price.
* Books: ``N_BOOK_DAYS`` maker days drawn from the H3 population (dominant maker subaccount, day-start book with at
  least one live option of a currency whose PM2 window is open), per currency under PM2, SM and (BTC, ETH) the legacy
  PM, ``p`` = mark ``M_b`` (Black-76 on the SVI curve, forward ``svi_fwd``, no discount).

Storage layout of ``SubAccounts`` (v2-core ``SubAccounts.sol``, checked with ``eth_getStorageAt``): slot 11
``lastAccountId``, 12 ``lastTradeId``, 13 ``manager``, 14 ``balanceAndOrder``, 15 ``heldAssets``.

Command line (the plan step loads a full FeedHistory with SVI and must run under ``scripts/p2_heavy.py``)::

    python3 scripts/p2_heavy.py --wait-max 500 -- python3 -m derive_surface.p2validate plan --ccy BTC
    python3 -m derive_surface.p2validate chain --max-seconds 500     # repeat until it prints done
    python3 -m derive_surface.p2validate report
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
import time
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from . import books, margin_pm, margin_pm2, margin_sm
from .chainfeeds import RpcError
from .p2chain import Rpc, block_at_ts, ts_at_block
from .p2feeds import FEEDS, FeedExpiryState
from .p2params import PM2_ADDR, PM_ADDR, SRM
from .p2types import YEAR, Book, MarketState, OptionLeg

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "data" / "p2" / "validation"
LOG_PATH = REPO / "data" / "p2" / "logs" / "B1.jsonl"
CSV_PATH = REPO / "results" / "p2" / "validation.csv"
SUMMARY_PATH = REPO / "results" / "p2" / "validation_summary.json"
TAPE_DIR = REPO / "data" / "p1" / "tape"
SNAPSHOTS = REPO / "data" / "p2" / "books" / "snapshots.parquet"

SEED = 20260924
N_SINGLE = 100          # blocks per currency and manager (pre-registration: at least 48)
N_BOOK_DAYS = 20
BOOK_SPAWN_KEY = 100
MAX_VOL_AGE = 1200      # "vol push in the last 20 min" (signing time, the clock of LyraVolFeed's staleness check)
MAX_FWD_AGE = 3600      # FeedHistory.live_expiries default: forward heartbeat
THRESHOLD_MEDIAN = 1e-3
THRESHOLD_P95 = 1e-2
E18 = 10 ** 18


def _utc(text: str) -> int:
    return calendar.timegm(dt.datetime.strptime(text, "%Y-%m-%d %H:%M").timetuple())


SAMPLE_START_TS = _utc("2024-01-11 00:00")
SAMPLE_END_TS = _utc("2026-09-30 08:00")   # registered cut-off (pilot: 2026-09-17 12:00)
PM2_START_TS = {"BTC": _utc("2025-06-12 23:00"), "ETH": _utc("2025-06-12 23:00"), "HYPE": _utc("2025-11-11 00:00")}
HYPE_SM_START_TS = _utc("2025-11-11 00:00")

WINDOWS: Dict[Tuple[str, str], Tuple[int, int]] = {
    ("BTC", "sm"): (SAMPLE_START_TS, SAMPLE_END_TS), ("BTC", "pm"): (SAMPLE_START_TS, SAMPLE_END_TS),
    ("BTC", "pm2"): (PM2_START_TS["BTC"], SAMPLE_END_TS),
    ("ETH", "sm"): (SAMPLE_START_TS, SAMPLE_END_TS), ("ETH", "pm"): (SAMPLE_START_TS, SAMPLE_END_TS),
    ("ETH", "pm2"): (PM2_START_TS["ETH"], SAMPLE_END_TS),
    ("HYPE", "sm"): (HYPE_SM_START_TS, SAMPLE_END_TS), ("HYPE", "pm2"): (PM2_START_TS["HYPE"], SAMPLE_END_TS),
}
CELLS: List[Tuple[str, str]] = [("BTC", "sm"), ("BTC", "pm"), ("BTC", "pm2"), ("ETH", "sm"), ("ETH", "pm"),
                                ("ETH", "pm2"), ("HYPE", "sm"), ("HYPE", "pm2")]

# ---------------------------------------------------------------- addresses (Chain 957)

SUBACCOUNTS = books.SUBACCOUNTS.lower()
MULTICALL3 = books.MULTICALL3
STABLE_FEED = "0x9c61888497d716f5bbd93d5e13d443cc375f1424"   # USDC/USD, stableFeed() of SRM, PMRM and PMRM_2
OPTION_ASSET = {"BTC": "0xd0711b9ebe84b778483709cde62bacfdbae13623",   # addresses_head.json cur[ccy].option
                "ETH": "0x4bb4c3cdc7562f08e9910a0c7d8bb7e108861eb4",
                "HYPE": "0x7344bf2afff9afcd6d024865fc0ca53bf03464d9"}
PERP_ASSET = {ccy: FEEDS[ccy]["perp_asset"].lower() for ccy in ("BTC", "ETH", "HYPE")}
MANAGER = {("sm", ccy): SRM for ccy in ("BTC", "ETH", "HYPE")}
MANAGER.update({("pm", ccy): PM_ADDR[ccy]["manager"] for ccy in PM_ADDR})
MANAGER.update({("pm2", ccy): PM2_ADDR[ccy]["manager"] for ccy in PM2_ADDR})

SLOT_BALANCE_AND_ORDER = 14
SLOT_HELD_ASSETS = 15
SYNTHETIC_ACCOUNT = 2 ** 64 + SEED   # far above SubAccounts.lastAccountId (72 019 on 2026-09-17)
INT240_MIN, INT240_MAX = -(1 << 239), (1 << 239) - 1

# ---------------------------------------------------------------- keccak256 (Ethereum's pre-standard Keccak)

_RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B,
       0x0000000080000001, 0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088,
       0x0000000080008009, 0x000000008000000A, 0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
       0x8000000000008003, 0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
       0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
_ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
_M64 = (1 << 64) - 1


def _rol(x: int, n: int) -> int:
    return ((x << n) | (x >> (64 - n))) & _M64 if n else x


def _keccak_f(a: List[List[int]]) -> List[List[int]]:
    for rc in _RC:
        c = [a[x][0] ^ a[x][1] ^ a[x][2] ^ a[x][3] ^ a[x][4] for x in range(5)]
        d = [c[(x - 1) % 5] ^ _rol(c[(x + 1) % 5], 1) for x in range(5)]
        a = [[a[x][y] ^ d[x] for y in range(5)] for x in range(5)]
        b = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                b[y][(2 * x + 3 * y) % 5] = _rol(a[x][y], _ROT[x][y])
        a = [[b[x][y] ^ ((~b[(x + 1) % 5][y]) & b[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
        a[0][0] ^= rc
    return a


def keccak256(data: bytes) -> bytes:
    """Keccak-256 as used by Ethereum (padding 0x01 ... 0x80, not the NIST SHA3 padding of ``hashlib.sha3_256``)."""
    rate = 136
    msg = bytearray(data)
    msg.append(0x01)
    msg.extend(b"\x00" * ((-len(msg)) % rate))
    msg[-1] |= 0x80
    a = [[0] * 5 for _ in range(5)]
    for off in range(0, len(msg), rate):
        for i in range(rate // 8):
            a[i % 5][i // 5] ^= int.from_bytes(msg[off + 8 * i: off + 8 * i + 8], "little")
        a = _keccak_f(a)
    return b"".join(a[i][0].to_bytes(8, "little") for i in range(4))


def selector(signature: str) -> bytes:
    return keccak256(signature.encode())[:4]


SELECTOR_SIGNATURES = {
    "getMargin(uint256,bool)": "623bb445",
    "getMarginAndMarkToMarket(uint256,bool,uint256)": "6691bc04",
    "getUnsettledAndUnrealizedCash(uint256)": "7a4c2c3a",
    "getScenarios()": "c454b613",
    "getSpot()": "2b37269c",
    "getForwardPrice(uint64)": "b34f2e36",
    "getVol(uint128,uint64)": "96159550",
    "getExpiryMinConfidence(uint64)": "d4435817",
    "getInterestRate(uint64)": "b0487ff6",
    "getPerpPrice()": "90f76b18",
}
SEL = {sig.split("(")[0]: s for sig, s in SELECTOR_SIGNATURES.items()}


def _w(x: int) -> bytes:
    return (int(x) % (1 << 256)).to_bytes(32, "big")


def _calldata(name: str, *args: int) -> bytes:
    return bytes.fromhex(SEL[name]) + b"".join(_w(a) for a in args)


# ---------------------------------------------------------------- SubAccounts storage override

def held_assets_slot(account: int) -> int:
    """Slot of ``heldAssets[account]`` (the array length)."""
    return int.from_bytes(keccak256(_w(account) + _w(SLOT_HELD_ASSETS)), "big")


def held_assets_element_slot(account: int, index: int) -> int:
    """Slot of ``heldAssets[account][index]`` (one packed ``HeldAsset`` per slot)."""
    return int.from_bytes(keccak256(_w(held_assets_slot(account))), "big") + int(index)


def balance_slot(account: int, asset: str, sub_id: int) -> int:
    """Slot of ``balanceAndOrder[account][asset][subId]``."""
    inner = keccak256(_w(account) + _w(SLOT_BALANCE_AND_ORDER))
    mid = keccak256(_w(int(asset, 16)) + inner)
    return int.from_bytes(keccak256(_w(sub_id) + mid), "big")


def unpack_held(word: int) -> Tuple[str, int]:
    """``HeldAsset {address asset; uint96 subId}`` packed low to high."""
    return "0x%040x" % (word & ((1 << 160) - 1)), word >> 160


def unpack_balance(word: int) -> Tuple[int, int]:
    """``BalanceAndOrder {int240 balance; uint16 order}`` packed low to high."""
    bal = word & ((1 << 240) - 1)
    if bal >> 239:
        bal -= 1 << 240
    return bal, word >> 240


def account_state_diff(account: int, balances: Sequence[Tuple[str, int, int]]) -> Dict[str, str]:
    """Storage slots that make ``getAccountBalances(account)`` return exactly ``balances`` (asset, subId, 1e18 int),
    in this order, for an account that holds nothing on chain."""
    seen = set()
    diff = {"0x%064x" % held_assets_slot(account): "0x%064x" % len(balances)}
    for i, (asset, sub_id, bal) in enumerate(balances):
        key = (asset.lower(), int(sub_id))
        if key in seen:
            raise ValueError(f"asset {asset} subId {sub_id} twice")
        seen.add(key)
        bal = int(bal)
        if bal == 0:
            raise ValueError("SubAccounts does not hold zero balances")
        if not INT240_MIN <= bal <= INT240_MAX:
            raise ValueError(f"balance {bal} does not fit int240")
        if not 0 <= int(sub_id) < (1 << 96) or i >= (1 << 16):
            raise ValueError("subId or order out of range")
        diff["0x%064x" % held_assets_element_slot(account, i)] = "0x%064x" % (int(asset, 16) | (int(sub_id) << 160))
        diff["0x%064x" % balance_slot(account, asset, sub_id)] = "0x%064x" % ((bal % (1 << 240)) | (i << 240))
    return diff


def state_override(accounts: Mapping[int, Sequence[Tuple[str, int, int]]]) -> dict:
    diff: Dict[str, str] = {}
    for acc, rows in accounts.items():
        diff.update(account_state_diff(acc, rows))
    return {SUBACCOUNTS: {"stateDiff": diff}}


def wei(x: float) -> int:
    """Exact 1e18 integer of a decimal amount (``repr`` of the float, e.g. 0.3 -> 3e17)."""
    return int((Decimal(repr(float(x))) * E18).to_integral_value())


def book_balances(ccy: str, book: Book) -> List[Tuple[str, int, int]]:
    """Balances of a book in one currency: netted option legs sorted by (expiry, strike, is_call), then the perp."""
    rows = [(OPTION_ASSET[ccy], books.encode_option_subid(leg.expiry, leg.strike, leg.is_call), wei(leg.amount))
            for leg in margin_sm.merged_options(book)]
    rows = [r for r in rows if r[2] != 0]
    if book.perp:
        rows.append((PERP_ASSET[ccy], 0, wei(book.perp)))
    return rows


def snapshot_book(snap: pd.DataFrame, ccy: str, ts: int) -> Tuple[List[Tuple[str, int, int]], Book]:
    """Options (live at ``ts``) and perp of one currency from snapshot rows, as exact balances and as a Book
    (``perp_entry = None``, cash 0; cash and collateral stay outside K)."""
    s = snap[(snap["ccy"] == ccy) & snap["kind"].isin(["option", "perp"])]
    opts, perp_rows = [], []
    for r in s.itertuples(index=False):
        raw = int(str(r.balance_raw))
        if raw == 0:
            continue
        if r.kind == "option":
            e, k, c = books.decode_option_subid(int(str(r.sub_id)))
            if e <= int(ts):
                continue
            opts.append(((e, k, c), raw))
        else:
            perp_rows.append(raw)
    opts.sort(key=lambda t: t[0])
    rows = [(OPTION_ASSET[ccy], books.encode_option_subid(*key), raw) for key, raw in opts]
    legs = [OptionLeg(e, k, c, raw / E18) for (e, k, c), raw in opts]
    perp_raw = sum(perp_rows)
    if perp_raw:
        rows.append((PERP_ASSET[ccy], 0, perp_raw))
    return rows, Book(options=legs, perp=perp_raw / E18, perp_entry=None, cash=0.0)


# ---------------------------------------------------------------- chain calls

def decode_int(data: bytes) -> int:
    v = int.from_bytes(data[:32], "big")
    return v - (1 << 256) if v >> 255 else v


def net_from_scenarios(margins: Sequence[int]) -> float:
    """Net over all scenarios from the per-scenario nets (1e18 ints): their minimum."""
    if not len(margins):
        raise ValueError("no scenario results")
    return min(int(m) for m in margins) / E18


def _call(rpc: Rpc, to: str, data: bytes, block: int, override: dict) -> bytes:
    out = rpc.raw("eth_call", [{"to": to, "data": "0x" + data.hex()}, hex(int(block)), override])
    return bytes.fromhex(out[2:])


def _multicall(rpc: Rpc, calls: Sequence[Tuple[str, bytes]], block: int, override: dict) -> List[Tuple[bool, bytes]]:
    out = rpc.raw("eth_call", [{"to": MULTICALL3, "data": books.encode_aggregate3(calls)}, hex(int(block)), override])
    return books.decode_aggregate3(bytes.fromhex(out[2:]))


def _pair(ok_ret: Tuple[bool, bytes], signed: bool = False) -> Optional[List[float]]:
    ok, ret = ok_ret
    if not ok or len(ret) < 64:
        return None
    a = decode_int(ret) if signed else int.from_bytes(ret[:32], "big")
    return [a / E18, int.from_bytes(ret[32:64], "big") / E18]


def strike_wei(strike: float) -> int:
    """18-decimal strike as encoded in the option subId (1e8 precision)."""
    return int(round(float(strike) * 1e8)) * 10 ** 10


def chain_single(rpc: Rpc, case: dict) -> dict:
    """getMargin (IM, MM) of the synthetic one-leg account under the case's manager, plus the chain feed values."""
    ccy, mgr, block = case["ccy"], case["manager"], int(case["block"])
    e, k = int(case["expiry"]), float(case["strike"])
    acc = SYNTHETIC_ACCOUNT
    rows = [(OPTION_ASSET[ccy], books.encode_option_subid(e, k, bool(case["is_call"])), wei(case["amount"]))]
    ov = state_override({acc: rows})
    f = FEEDS[ccy]
    to = MANAGER[(mgr, ccy)]
    calls = [(to, _calldata("getMargin", acc, 1)), (to, _calldata("getMargin", acc, 0)),
             (f["spot"], _calldata("getSpot")), (f["forward"], _calldata("getForwardPrice", e)),
             (f["vol"], _calldata("getVol", strike_wei(k), e)), (f["vol"], _calldata("getExpiryMinConfidence", e)),
             (STABLE_FEED, _calldata("getSpot"))]
    rate_live = block >= f["deploy"]["rate_pm2"]
    if rate_live:
        calls.append((f["rate_pm2"], _calldata("getInterestRate", e)))
    res = _multicall(rpc, calls, block, ov)
    out = {"id": case["id"], "method": "direct", "status": "ok"}
    for key, r in (("IM", res[0]), ("MM", res[1])):
        out[key] = decode_int(r[1]) / E18 if r[0] else None
    if out["IM"] is None or out["MM"] is None:
        out["status"] = "revert"
    vc = res[5]
    out["diag"] = {"spot": _pair(res[2]), "forward": _pair(res[3]), "vol": _pair(res[4]),
                   "vol_min_conf": int.from_bytes(vc[1][:32], "big") / E18 if vc[0] else None,
                   "stable": _pair(res[6]), "rate_pm2": _pair(res[7], signed=True) if rate_live else None}
    return out


def chain_book(rpc: Rpc, case: dict, per_scenario: bool = False) -> dict:
    """Net (IM, MM) of the synthetic account holding the book, perp at the engine's perp price.

    ``getMargin`` is called directly (the whole 50 M gas cap of ``eth_call``); when it fails under PMRM or PMRM_2
    (out of gas for large books, or a revert) the net is taken over the single-scenario calls. ``per_scenario=True``
    skips the direct call (to check that both routes agree)."""
    ccy, mgr, block = case["ccy"], case["manager"], int(case["block"])
    acc = SYNTHETIC_ACCOUNT + 1
    rows = [(a, int(s), int(b)) for a, s, b in case["balances"]]
    ov = state_override({acc: rows})
    to = MANAGER[(mgr, ccy)]
    has_perp = any(a == PERP_ASSET[ccy] for a, _, _ in rows)
    calls = [(FEEDS[ccy]["spot"], _calldata("getSpot"))]
    if has_perp:
        calls.append((PERP_ASSET[ccy], _calldata("getUnsettledAndUnrealizedCash", acc)))
    if mgr in ("pm", "pm2"):
        calls.append((to, _calldata("getScenarios")))
    res = _multicall(rpc, calls, block, ov)
    out = {"id": case["id"], "method": "direct", "status": "ok", "diag": {"spot": _pair(res[0])}}
    perp_cash = 0
    if has_perp:
        if not res[1][0]:
            return dict(out, status="revert", IM=None, MM=None, note="getUnsettledAndUnrealizedCash reverted")
        perp_cash = decode_int(res[1][1])
    out["perp_cash"] = perp_cash / E18
    notes = []
    if not per_scenario:
        try:
            for key, is_initial in (("IM", 1), ("MM", 0)):
                out[key] = (decode_int(_call(rpc, to, _calldata("getMargin", acc, is_initial), block, ov))
                            - perp_cash) / E18
            return out
        except RpcError as err:
            notes.append(f"getMargin: {str(err)[:120]}")
    if mgr == "sm" or not res[-1][0]:
        return dict(out, status="revert", IM=None, MM=None, note="; ".join(notes))
    ret = res[-1][1]
    n_scen = int.from_bytes(ret[int.from_bytes(ret[:32], "big"):][:32], "big")
    out["method"], out["n_scenarios"] = "per_scenario", n_scen
    for key, is_initial in (("IM", 1), ("MM", 0)):
        margins = []
        for j in range(n_scen):
            try:
                data = _call(rpc, to, _calldata("getMarginAndMarkToMarket", acc, is_initial, j), block, ov)
            except RpcError as err:
                notes.append(f"scenario {j}: {str(err)[:120]}")
                return dict(out, status="revert", IM=None, MM=None, note="; ".join(notes))
            margins.append(decode_int(data) - perp_cash)
        out[key] = net_from_scenarios(margins)
    out["note"] = "; ".join(notes)
    return out


# ---------------------------------------------------------------- replica side

def replica_net(mgr: str, book: Book, state: MarketState, params: Mapping, is_initial: bool) -> float:
    """Replica net margin of ``book`` (cash 0) under ``mgr``; nan where the chain refuses the book (more option
    expiries than ``maxExpiries`` for PMRM / PMRM_2) or a feed value is missing."""
    if mgr not in ("sm", "pm", "pm2"):
        raise ValueError(f"unknown manager {mgr!r}")
    legs = margin_sm.merged_options(book)
    n_exp = len({leg.expiry for leg in legs})
    if mgr in ("pm", "pm2") and params.get("maxExpiries") is not None and n_exp > int(params["maxExpiries"]):
        return float("nan")
    try:
        if mgr == "sm":
            net, _ = margin_sm.net_margin(book, state, params, is_initial)
        elif mgr == "pm":
            fixed = {e: float(getattr(state.expiries[e], "fwd_fixed", 0.0) or 0.0) for e in {leg.expiry for leg in legs}}
            net, _ = margin_pm.net_margin(book, state, params, is_initial, fwd_fixed=fixed)
        else:
            net, _ = margin_pm2.net_margin(book, state, params, is_initial)
    except (ValueError, KeyError):   # an expiry without feed state (no SVI curve, no forward)
        return float("nan")
    return float(net)


def replica_single(mgr: str, row: Mapping, params: Mapping, is_initial: bool) -> float:
    """The same contract through the vectorised path of B2 (``FeedHistory.bulk`` columns + ``margin_*.single``)."""
    arrays = {k: np.asarray([row[k]], dtype=float) for k in
              ("spot", "forward", "sigma", "rate", "vol_conf", "fwd_conf", "spot_conf", "rate_conf", "fwd_fixed",
               "rate_pm", "tau", "strike", "amount")}
    arrays["is_call"] = np.asarray([bool(row["is_call"])])
    mod = {"sm": margin_sm, "pm": margin_pm, "pm2": margin_pm2}[mgr]
    net, _ = mod.single(arrays, params, is_initial)
    return float(net[0])


def mark_premium(book: Book, state: MarketState) -> float:
    """sum q M_b over the options: Black-76 on the SVI curve with forward ``svi_fwd`` and discount 1 (Paper 1 mark)."""
    total = 0.0
    for leg in margin_sm.merged_options(book):
        es = state.expiries[leg.expiry]
        f = es.svi_fwd if es.svi_fwd is not None else es.forward
        call, put = margin_sm.b76_prices(f, leg.strike, es.vol(leg.strike), max(leg.expiry - state.ts, 0))
        total += leg.amount * float(call if leg.is_call else put)
    return total


def capital(premium: float, net: float) -> float:
    return float(premium) - float(net)


def rel_err(k_replica: float, k_chain: float) -> float:
    if not (np.isfinite(k_replica) and np.isfinite(k_chain)) or k_chain == 0:
        return float("nan")
    return abs(k_replica - k_chain) / abs(k_chain)


# ---------------------------------------------------------------- JSON round trip of states and books

def state_to_json(state: MarketState) -> dict:
    exps = {}
    for e, es in state.expiries.items():
        exps[str(int(e))] = {"forward": es.forward, "svi": list(es.svi) if es.svi is not None else None,
                             "svi_fwd": es.svi_fwd, "rate": es.rate, "vol_conf": es.vol_conf, "fwd_conf": es.fwd_conf,
                             "fwd_fixed": float(getattr(es, "fwd_fixed", 0.0)),
                             "rate_conf": float(getattr(es, "rate_conf", 1.0))}
    return {"currency": state.currency, "ts": int(state.ts), "spot": state.spot, "spot_conf": state.spot_conf,
            "perp": state.perp, "perp_conf": state.perp_conf, "stable": state.stable, "expiries": exps}


def state_from_json(d: Mapping) -> MarketState:
    exps = {}
    for e, x in d["expiries"].items():
        exps[int(e)] = FeedExpiryState(expiry=int(e), forward=float(x["forward"]),
                                       svi=tuple(float(v) for v in x["svi"]) if x["svi"] is not None else None,
                                       rate=float(x["rate"]), vol_conf=float(x["vol_conf"]),
                                       fwd_conf=float(x["fwd_conf"]),
                                       svi_fwd=float(x["svi_fwd"]) if x["svi_fwd"] is not None else None,
                                       fwd_fixed=float(x["fwd_fixed"]), rate_conf=float(x["rate_conf"]))
    return MarketState(currency=d["currency"], ts=int(d["ts"]), spot=float(d["spot"]), expiries=exps,
                       perp=None if d.get("perp") is None else float(d["perp"]), stable=float(d.get("stable", 1.0)),
                       spot_conf=float(d["spot_conf"]), perp_conf=float(d["perp_conf"]))


def book_to_json(book: Book) -> dict:
    return {"options": [[int(l.expiry), float(l.strike), bool(l.is_call), float(l.amount)] for l in book.options],
            "perp": float(book.perp)}


def book_from_json(d: Mapping) -> Book:
    return Book(options=[OptionLeg(int(e), float(k), bool(c), float(q)) for e, k, c, q in d["options"]],
                perp=float(d.get("perp", 0.0)), perp_entry=None, cash=0.0)


# ---------------------------------------------------------------- sampling

def cell_rng(key: int) -> np.random.Generator:
    """Independent reproducible stream per cell: SeedSequence(20260924) child ``key``."""
    return np.random.default_rng(np.random.SeedSequence(SEED, spawn_key=(int(key),)))


def draw_block(rng: np.random.Generator, lo_ts: int, hi_ts: int) -> int:
    """Uniform block with timestamp in [lo_ts, hi_ts]."""
    lo = block_at_ts(lo_ts)
    if ts_at_block(lo) < lo_ts:
        lo += 1
    return int(rng.integers(lo, block_at_ts(hi_ts) + 1))


def eligible_expiries(hist, ts: int, max_vol_age: int = MAX_VOL_AGE, max_fwd_age: int = MAX_FWD_AGE) -> List[int]:
    """Live expiries (forward push at most ``max_fwd_age`` s old) with a vol push signed at most ``max_vol_age`` s
    before ``ts``."""
    live = hist.live_expiries(int(ts), max_age=max_fwd_age)
    if not live:
        return []
    n = len(live)
    b = hist.bulk(np.full(n, int(ts)), np.asarray(live, dtype=np.int64), np.ones(n))
    age = b["vol_age"].to_numpy()
    return [int(e) for e, a in zip(live, age) if np.isfinite(a) and a <= max_vol_age]


def day_fills(tape: pd.DataFrame, ts: int) -> pd.DataFrame:
    """Unique fills (one row per trade, the taker row where both exist) of the UTC day of ``ts``."""
    day = int(ts) - int(ts) % 86_400
    pad = 3_600_000  # both rows of a trade lie within minutes of each other (RFQ maker rows up to ~30 min earlier)
    t = tape[(tape["timestamp"] >= day * 1000 - pad) & (tape["timestamp"] < (day + 86_400) * 1000 + pad)]
    if "liquidity_role" in t.columns:
        t = t.assign(_o=(t["liquidity_role"] != "taker").astype(int)).sort_values(["trade_id", "_o"], kind="mergesort")
        t = t.drop(columns="_o")
    t = t.drop_duplicates("trade_id")
    t = t[(t["timestamp"] >= day * 1000) & (t["timestamp"] < (day + 86_400) * 1000)]
    return t.sort_values(["timestamp", "trade_id"], kind="mergesort").reset_index(drop=True)


def pick_contract(rng: np.random.Generator, fills: pd.DataFrame, eligible: Sequence[int]) -> Optional[dict]:
    cand = fills[fills["expiry"].isin([int(e) for e in eligible])]
    if cand.empty:
        return None
    r = cand.iloc[int(rng.integers(len(cand)))]
    side = 1.0 if int(rng.integers(2)) == 1 else -1.0
    return {"trade_id": str(r["trade_id"]), "expiry": int(r["expiry"]), "strike": float(r["strike"]),
            "is_call": str(r["option_type"]) == "C", "price": float(r["trade_price"]), "amount": side}


def maker_day_population(snaps: pd.DataFrame) -> pd.DataFrame:
    """H3 population: (subaccount, day) whose day-start book holds a live option of a currency with open PM2 window.
    Columns subaccount, day, block, ccys (sorted list)."""
    out = []
    for (sub, day), g in snaps.groupby(["subaccount", "day"], sort=True):
        block = int(g["block"].iloc[0])
        ts = ts_at_block(block)
        o = g[g["kind"] == "option"]
        ccys = set()
        for r in o.itertuples(index=False):
            ccy = str(r.ccy)
            win = WINDOWS.get((ccy, "pm2"))
            if win is None or not win[0] <= ts <= win[1]:
                continue
            if r.expiry is not None and not pd.isna(r.expiry) and int(r.expiry) > ts and float(r.amount) != 0.0:
                ccys.add(ccy)
        if ccys:
            out.append({"subaccount": int(sub), "day": pd.Timestamp(day), "block": block, "ccys": sorted(ccys)})
    return pd.DataFrame(out, columns=["subaccount", "day", "block", "ccys"])


def select_maker_days(snaps: pd.DataFrame, n: int = N_BOOK_DAYS) -> pd.DataFrame:
    pop = maker_day_population(snaps)
    rng = cell_rng(BOOK_SPAWN_KEY)
    idx = rng.choice(len(pop), size=min(int(n), len(pop)), replace=False)
    return pop.iloc[np.sort(idx)].reset_index(drop=True)


# ---------------------------------------------------------------- plan (replica values, needs FeedHistory)

def _feed_row(hist, ts: int, expiry: int, strike: float) -> dict:
    b = hist.bulk(np.array([ts]), np.array([expiry], dtype=np.int64), np.array([strike])).iloc[0]
    return {k: float(b[k]) for k in b.index}


def plan_singles(ccy: str, mgr: str, hist, tape: pd.DataFrame, timeline, n: int = N_SINGLE,
                 max_redraw: int = 50) -> Tuple[List[dict], dict]:
    key = CELLS.index((ccy, mgr))
    rng = cell_rng(key)
    lo, hi = WINDOWS[(ccy, mgr)]
    cases, redraws = [], 0
    while len(cases) < n:
        for attempt in range(max_redraw):
            block = draw_block(rng, lo, hi)
            ts = ts_at_block(block)
            c = pick_contract(rng, day_fills(tape, ts), eligible_expiries(hist, ts))
            if c is not None:
                break
            redraws += 1
        else:
            raise RuntimeError(f"{ccy} {mgr}: no eligible fill after {max_redraw} draws")
        e, k = c["expiry"], c["strike"]
        state = hist.state_at(ts, [e])
        params = timeline.at(ts)
        book = Book(options=[OptionLeg(e, k, c["is_call"], c["amount"])])
        row = _feed_row(hist, ts, e, k)
        row.update(tau=max(e - ts, 0) / YEAR, strike=k, amount=c["amount"], is_call=c["is_call"])
        rep = {"IM": replica_net(mgr, book, state, params, True), "MM": replica_net(mgr, book, state, params, False),
               "IM_single": replica_single(mgr, row, params, True), "MM_single": replica_single(mgr, row, params, False)}
        cases.append({"id": f"single-{ccy}-{mgr}-{len(cases):03d}", "kind": "single", "ccy": ccy, "manager": mgr,
                      "block": block, "ts": ts, "expiry": e, "strike": k, "is_call": c["is_call"],
                      "amount": c["amount"], "price": c["price"], "trade_id": c["trade_id"],
                      "premium": c["price"] * c["amount"], "params_from_block": timeline.entry_at(ts)["from_block"],
                      "replica": rep, "feeds": row, "state": state_to_json(state), "book": book_to_json(book)})
    return cases, {"redraws": redraws}


def plan_books(ccy: str, hist, snaps: pd.DataFrame, days: pd.DataFrame, timelines: Mapping[str, object]) -> List[dict]:
    cases = []
    for d in days.itertuples(index=False):
        if ccy not in d.ccys:
            continue
        g = snaps[(snaps["subaccount"] == d.subaccount) & (snaps["day"] == d.day)]
        ts = ts_at_block(int(d.block))
        rows, book = snapshot_book(g, ccy, ts)
        exps = book.expiries()
        state = hist.state_at(ts, exps)
        try:
            premium = mark_premium(book, state)
        except ValueError:
            premium = float("nan")
        for mgr in ("pm2", "sm", "pm"):
            if (ccy, mgr) not in WINDOWS:
                continue
            tl = timelines[mgr]
            params = tl.at(ts)
            rep = {"IM": replica_net(mgr, book, state, params, True), "MM": replica_net(mgr, book, state, params, False)}
            cases.append({"id": f"book-{ccy}-{mgr}-{int(d.subaccount)}-{pd.Timestamp(d.day).date()}", "kind": "book",
                          "ccy": ccy, "manager": mgr, "block": int(d.block), "ts": ts, "subaccount": int(d.subaccount),
                          "day": str(pd.Timestamp(d.day).date()), "n_legs": len(book.options), "n_expiries": len(exps),
                          "perp": book.perp, "premium": premium, "balances": [[a, str(s), str(b)] for a, s, b in rows],
                          "params_from_block": tl.entry_at(ts)["from_block"], "replica": rep,
                          "state": state_to_json(state), "book": book_to_json(book)})
    return cases


def _atomic_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, default=float))
    tmp.replace(path)


def run_plan(ccy: str, n: int = N_SINGLE, out_dir: Path = OUT_DIR) -> dict:
    from .p2feeds import FeedHistory
    from .p2params import Timeline

    t0 = time.monotonic()
    hist = FeedHistory(ccy)
    tape = pd.read_parquet(TAPE_DIR / f"{ccy}_options_full.parquet",
                           columns=["trade_id", "timestamp", "expiry", "strike", "option_type", "trade_price",
                                    "liquidity_role"])
    timelines = {mgr: Timeline(ccy, mgr) for c, mgr in WINDOWS if c == ccy}
    singles, meta = [], {}
    for c, mgr in CELLS:
        if c != ccy:
            continue
        cases, info = plan_singles(ccy, mgr, hist, tape, timelines[mgr], n)
        singles += cases
        meta[mgr] = info
    snaps = pd.read_parquet(SNAPSHOTS)
    days = select_maker_days(snaps)
    book_cases = plan_books(ccy, hist, snaps, days, timelines)
    doc = {"ccy": ccy, "seed": SEED, "n_single": n, "created_utc": dt.datetime.utcnow().isoformat() + "Z",
           "meta": meta, "maker_days": [[int(r.subaccount), str(pd.Timestamp(r.day).date()), int(r.block), list(r.ccys)]
                                        for r in days.itertuples(index=False)],
           "singles": singles, "books": book_cases}
    _atomic_json(Path(out_dir) / f"plan_{ccy}.json", doc)
    return {"ccy": ccy, "singles": len(singles), "books": len(book_cases), "meta": meta,
            "seconds": round(time.monotonic() - t0, 1)}


# ---------------------------------------------------------------- chain step (resumable)

def _load_plans(out_dir: Path) -> List[dict]:
    cases = []
    for ccy in ("BTC", "ETH", "HYPE"):
        p = Path(out_dir) / f"plan_{ccy}.json"
        if p.exists():
            doc = json.loads(p.read_text())
            cases += doc["singles"] + doc["books"]
    return cases


def _load_chain(out_dir: Path) -> Dict[str, dict]:
    p = Path(out_dir) / "chain.jsonl"
    out: Dict[str, dict] = {}
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["id"]] = r
    return out


def run_chain(max_seconds: float = 500.0, out_dir: Path = OUT_DIR, rpc: Optional[Rpc] = None,
              retry_failed: bool = False, only: Optional[str] = None) -> dict:
    """eth_call for every planned case without a result; ``retry_failed`` also redoes cases whose last result is not
    ``ok`` (a new line supersedes the old one), ``only`` restricts to case ids starting with that prefix."""
    rpc = rpc or Rpc(rate=2.0, log_path=LOG_PATH)
    done = _load_chain(out_dir)
    if retry_failed:
        done = {k: v for k, v in done.items() if v.get("status") == "ok"}
    # a result counts only for the block it was computed at: ids repeat across draws (another cut-off moves the blocks)
    todo = [c for c in _load_plans(out_dir)
            if done.get(c["id"], {}).get("block") != c["block"] and (only is None or c["id"].startswith(only))]
    t0 = time.monotonic()
    n = 0
    path = Path(out_dir) / "chain.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    for case in todo:
        if time.monotonic() - t0 > max_seconds:
            break
        try:
            res = chain_single(rpc, case) if case["kind"] == "single" else chain_book(rpc, case)
        except RpcError as err:
            res = {"id": case["id"], "status": "rpc_error", "IM": None, "MM": None, "note": str(err)[:200]}
        res["block"] = int(case["block"])
        with path.open("a") as fh:
            fh.write(json.dumps(res, default=float) + "\n")
        n += 1
    left = len(todo) - n
    return {"processed": n, "remaining": left, "done": left == 0, "seconds": round(time.monotonic() - t0, 1)}


def run_scenario_check(n: int = 6, out_dir: Path = OUT_DIR, rpc: Optional[Rpc] = None) -> dict:
    """Recompute ``n`` PMRM / PMRM_2 books whose direct ``getMargin`` worked via the per-scenario route; both are
    chain values, so they must agree exactly (written to ``per_scenario_check.json``)."""
    rpc = rpc or Rpc(rate=2.0, log_path=LOG_PATH)
    chain = _load_chain(out_dir)
    cases = [c for c in _load_plans(out_dir) if c["kind"] == "book" and c["manager"] in ("pm", "pm2")
             and chain.get(c["id"], {}).get("method") == "direct" and chain[c["id"]].get("status") == "ok"]
    cases = sorted(cases, key=lambda c: -c["n_legs"])[:n]
    rows = []
    for c in cases:
        r = chain_book(rpc, c, per_scenario=True)
        d = chain[c["id"]]
        rows.append({"ccy": c["ccy"], "manager": c["manager"], "n_legs": c["n_legs"], "n_scenarios": r.get("n_scenarios"),
                     "IM_direct": d["IM"], "IM_per_scenario": r.get("IM"), "MM_direct": d["MM"],
                     "MM_per_scenario": r.get("MM"),
                     "equal": r.get("IM") == d["IM"] and r.get("MM") == d["MM"]})
    doc = {"n": len(rows), "all_equal": all(x["equal"] for x in rows), "rows": rows}
    _atomic_json(Path(out_dir) / "per_scenario_check.json", doc)
    return {"n": len(rows), "all_equal": doc["all_equal"]}


# ---------------------------------------------------------------- report

CSV_COLUMNS = ["ccy", "manager", "kind", "block", "ts", "K_replica", "K_chain", "abs_err", "rel_err", "is_initial",
               "status", "method", "expiry", "strike", "is_call", "amount", "premium", "n_legs", "n_expiries", "book",
               "K_replica_single", "vol_rel_dev", "fwd_rel_dev", "spot_rel_dev"]


def _rel_dev(mine: Optional[float], chain: Optional[Sequence[float]]) -> float:
    if chain is None or mine is None or not np.isfinite(mine) or chain[0] == 0:
        return float("nan")
    return abs(mine - chain[0]) / abs(chain[0])


def build_rows(cases: Sequence[dict], chain: Mapping[str, dict], label=None) -> pd.DataFrame:
    rows = []
    for c in cases:
        r = chain.get(c["id"])
        if r is None:
            continue
        if "block" in r and int(r["block"]) != int(c["block"]):
            raise ValueError(f"chain result of {c['id']} is for block {r['block']}, the plan draws {c['block']}")
        diag = r.get("diag") or {}
        feeds = c.get("feeds") or {}
        for key, is_initial in (("IM", True), ("MM", False)):
            net_rep, net_chain = c["replica"].get(key), r.get(key)
            k_rep = capital(c["premium"], net_rep) if net_rep is not None else float("nan")
            k_chain = capital(c["premium"], net_chain) if net_chain is not None else float("nan")
            status = r.get("status", "ok")
            if status == "ok" and not np.isfinite(k_rep):
                status = "replica_nan"
            single = c["replica"].get(f"{key}_single")
            book = ""
            if c["kind"] == "book":
                book = f"{label(c['subaccount']) if label else ''} {c['day']}".strip()
            rows.append({"ccy": c["ccy"], "manager": c["manager"], "kind": c["kind"], "block": int(c["block"]),
                         "ts": int(c["ts"]), "K_replica": k_rep, "K_chain": k_chain,
                         "abs_err": abs(k_rep - k_chain) if np.isfinite(k_rep) and np.isfinite(k_chain) else float("nan"),
                         "rel_err": rel_err(k_rep, k_chain), "is_initial": is_initial, "status": status,
                         "method": r.get("method", ""), "expiry": c.get("expiry"), "strike": c.get("strike"),
                         "is_call": c.get("is_call"), "amount": c.get("amount"), "premium": c["premium"],
                         "n_legs": c.get("n_legs", 1), "n_expiries": c.get("n_expiries", 1), "book": book,
                         "K_replica_single": capital(c["premium"], single) if single is not None else float("nan"),
                         "vol_rel_dev": _rel_dev(feeds.get("sigma"), diag.get("vol")),
                         "fwd_rel_dev": _rel_dev(feeds.get("forward"), diag.get("forward")),
                         "spot_rel_dev": _rel_dev(feeds.get("spot") if feeds else (c.get("state") or {}).get("spot"),
                                                  diag.get("spot"))})
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Median, 95th percentile (linear interpolation) and maximum of |rel| per kind x currency x manager x IM/MM, and
    whether the pre-registered thresholds (median < 0.1 %, p95 < 1 %) hold."""
    out = []
    for (kind, ccy, mgr, im), g in df.groupby(["kind", "ccy", "manager", "is_initial"], sort=True):
        x = g["rel_err"].to_numpy(dtype=float)
        ok = x[np.isfinite(x)]
        med = float(np.median(ok)) if len(ok) else float("nan")
        p95 = float(np.percentile(ok, 95)) if len(ok) else float("nan")
        out.append({"kind": kind, "ccy": ccy, "manager": mgr, "is_initial": bool(im), "n": int(len(ok)),
                    "n_missing": int(len(x) - len(ok)), "median_rel": med, "p95_rel": p95,
                    "max_rel": float(ok.max()) if len(ok) else float("nan"),
                    "passes": bool(len(ok) > 0 and med < THRESHOLD_MEDIAN and p95 < THRESHOLD_P95)})
    return pd.DataFrame(out)


def _labeler():
    try:
        from . import p2ids
        return p2ids.label
    except Exception as err:  # pragma: no cover - labels are optional until B0 is done
        print(f"warning: no account labels ({err}); book column left without label")
        return None


def run_report(out_dir: Path = OUT_DIR, csv_path: Path = CSV_PATH, summary_path: Path = SUMMARY_PATH) -> pd.DataFrame:
    cases = _load_plans(out_dir)
    chain = _load_chain(out_dir)
    df = build_rows(cases, chain, _labeler())
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, float_format="%.10g")
    summ = summarize(df)
    doc = {"thresholds": {"median": THRESHOLD_MEDIAN, "p95": THRESHOLD_P95}, "seed": SEED,
           "n_cases": len(cases), "n_chain": len(chain),
           "status_counts": df.groupby(["kind", "status"]).size().rename("n").reset_index().to_dict("records"),
           "cells": summ.to_dict("records")}
    check = Path(out_dir) / "per_scenario_check.json"
    if check.exists():
        doc["per_scenario_check"] = json.loads(check.read_text())
    _atomic_json(summary_path, doc)
    return summ


# ---------------------------------------------------------------- command line

def main(argv: Optional[Sequence[str]] = None) -> None:
    p = argparse.ArgumentParser(prog="python3 -m derive_surface.p2validate", description="B1: replica against eth_call")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("plan", help="draw cases and compute the replica (heavy: run under scripts/p2_heavy.py)")
    a.add_argument("--ccy", required=True, choices=["BTC", "ETH", "HYPE"])
    a.add_argument("--n", type=int, default=N_SINGLE)
    c = sub.add_parser("chain", help="eth_call with state override for every planned case (resumable)")
    c.add_argument("--max-seconds", type=float, default=500.0)
    c.add_argument("--retry-failed", action="store_true")
    c.add_argument("--only", default=None, help="case id prefix, e.g. book-")
    sub.add_parser("report", help="write results/p2/validation.csv and validation_summary.json")
    k = sub.add_parser("check-scenarios", help="per-scenario route against direct getMargin on books where both work")
    k.add_argument("--n", type=int, default=6)
    args = p.parse_args(argv)
    if args.cmd == "plan":
        print(json.dumps(run_plan(args.ccy, args.n)), flush=True)
    elif args.cmd == "chain":
        print(json.dumps(run_chain(args.max_seconds, retry_failed=args.retry_failed, only=args.only)), flush=True)
    elif args.cmd == "check-scenarios":
        print(json.dumps(run_scenario_check(args.n)), flush=True)
    else:
        with pd.option_context("display.width", 200, "display.max_columns", 20):
            print(run_report().to_string(index=False))


if __name__ == "__main__":
    main()
