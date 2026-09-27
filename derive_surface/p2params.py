"""Parameter timelines of the three Derive margin managers per currency (Paper 2, task A2).

Every timeline is a JSON list ``[{"from_block", "from_ts", "from_utc", "source", "changed", "params", ...}]`` in
ascending order under ``results/p2/params/{CCY}_{mgr}.json`` (``mgr`` in ``sm``, ``pm``, ``pm2``). ``params`` uses the
Solidity struct and field names of v2-core (commit 96796a6) as keys; 1e18-scaled integers are returned as floats
(``int / 10**18``, correctly rounded), ``dteFloor`` stays in seconds (it is not 1e18-scaled on chain), booleans stay
booleans, ``maxExpiries`` and the scenario ``volShock`` enum stay integers.

* PM2 (``PMRM_2`` / ``PMRM_2_1`` + ``PMRMLib_2``): ``VolShockParameters``, ``MarginParameters``,
  ``BasisContingencyParameters``, ``OtherContingencyParameters``, ``SkewShockParameters``, ``CollateralParameters``
  (``{asset: {...}}``, only assets with a non-zero setting), ``scenarios`` (``spotShock``, ``volShock`` 0 None, 1 Up,
  2 Down, 3 Linear, 4 Abs, ``dampeningFactor``) and ``maxExpiries``. Entries carry the lib address in ``lib``.
  Accounts with a lib override (``LibOverrideUpdated``, PMRM_2_1) get their lib's own timeline
  ``{CCY}_pm2_lib_<addr8>.json`` (same schema, scenarios and maxExpiries from the manager); the account to lib map is
  ``{CCY}_pm2_overrides.json`` with accounts only as ``p2ids.label`` (``M1`` .. ``M10`` for the dominant makers,
  else salted HMAC); the raw ids stay in ``data/p2/params/{CCY}_pm2_overrides_raw.json``. The lib of an account
  (``account_lib``, ``pm2_params_for_account``) is resolved only through the raw ids of that file: a label depends on
  the maker ranking, so the labelled file is an export and never a lookup key.
* Legacy PM (``PMRM`` + ``PMRMLib``): ``VolShockParameters``, ``MarginParameters`` (getter
  ``getStaticDiscountParams``), ``BasisContingencyParameters``, ``OtherContingencyParameters``, ``scenarios``
  (``spotShock``, ``volShock`` 0 None, 1 Up, 2 Down) and ``maxExpiries``. The lib emits no events: its state is
  sampled monthly, every change is bisected to its block, and the result is checked with daily samples.
* SM (``StandardManager``, market id BTC 2, ETH 1, HYPE 48): ``OptionMarginParams``, ``PerpMarginRequirements``,
  ``BaseMarginParams``, ``OracleContingencyParams`` and ``DepegParams``, always read from the getters (the event
  ``OptionMarginParamsSet`` emits unpairedMMScale before unpairedIMScale).

The values at an event block are read with a historical ``eth_call`` at that block (state after the block), bundled
through Multicall3 where it exists (from block 1 935 198). Downloads are resumable: every snapshot is cached under
``data/p2/params/``. Run ``python3 -m derive_surface p2 params load --max-seconds 520`` until it prints ``DONE``.
The end block is fixed at the first run (``data/p2/params/meta.json``); a later run with ``--to-block N`` moves it
(e.g. the final data run), refetches the event logs up to N and keeps every cached snapshot.
"""
from __future__ import annotations

import argparse
import bisect
import datetime as dt
import hashlib
import json
import numbers
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from . import p2ids
from .chainfeeds import RpcError
from .p2chain import Rpc, block_at_ts, ts_at_block

REPO = Path(__file__).resolve().parents[1]
PARAMS_DIR = REPO / "results" / "p2" / "params"
DATA_DIR = REPO / "data" / "p2" / "params"
LOG_PATH = REPO / "data" / "p2" / "logs" / "A2.jsonl"
OI_LEGACY = REPO / "data" / "p2" / "kontext" / "margin-historie" / "oi_legacy.json"
EVENTS_KONTEXT = REPO / "data" / "p2" / "kontext" / "margin-historie" / "events.json"
OI_SHARE_CSV = REPO / "results" / "p2" / "manager_oi_share.csv"

CCYS = ("BTC", "ETH", "HYPE")
MANAGERS = ("sm", "pm", "pm2")
ZERO_ADDRESS = "0x" + "0" * 40
DAY_BLOCKS = 43_200  # 86 400 s at exactly 2 s per block
E18 = 10 ** 18

# ---- addresses (data/p2/kontext/margin-historie/deploy.json and addresses_head.json) -------------------------------
SRM = "0x28c9ddf9a3b29c2e6a561c1bc520954e5a33de5d"
SRM_DEPLOY_BLOCK = 843_042
SM_MARKET = {"BTC": 2, "ETH": 1, "HYPE": 48}
PM_ADDR = {
    "BTC": {"manager": "0x45da02b9ccf384d7dbdd7b2b13e705badb43db0d", "lib": "0xfa7f1a242b819a8ec97fd92674c3f0868395b0d3",
            "deploy_block": 843_077},
    "ETH": {"manager": "0xe7cd9370cde6c9b5eabce8f86d01822d3de205a0", "lib": "0x81ed5dc90f708dd908dccffd5128b5c3405f74c5",
            "deploy_block": 843_061},
}
PM2_ADDR = {
    "BTC": {"manager": "0xc7adab7a2b92019098da55ba4c5a8c65ae7e52dc", "lib": "0x1a1b78af94c2a755b911a63345ac1410f65ad61b",
            "deploy_block": 24_712_334},
    "ETH": {"manager": "0xc755dae3fd295a687adf3e192387163f813f0598", "lib": "0x904507c9636cba3e9ffb4ff44567dd6d98031694",
            "deploy_block": 24_712_302},
    "HYPE": {"manager": "0x18b385853a605a9b37e181919d3808c739729347",
             "lib": "0x12e0d427152f9fb46e6f60f708c909a6f978d71f", "deploy_block": 30_294_479},
}
MULTICALL3 = "0xcA11bde05977b3631167028862bE2a173976CA11"
MULTICALL3_BLOCK = 1_935_198  # first block with Multicall3 code on chain 957 (bisected 2026-09-24)
MULTICALL_CHUNK = 250

# ---- selectors: keccak256(signature)[:4], checked in tests/test_p2_params.py -----------------------------------------
SELECTOR_SIGNATURES = {
    "getScenarios()": "0xc454b613",
    "maxExpiries()": "0x7a6640ef",
    "lib()": "0x92801230",
    "getMarginParams()": "0x6ac4a038",
    "getVolShockParams()": "0xe7aa5a01",
    "getBasisContingencyParams()": "0x8097d159",
    "getOtherContingencyParams()": "0xf37b855f",
    "getSkewShockParams()": "0xb01352a5",
    "getCollateralParameters(address)": "0xe8b96662",
    "getStaticDiscountParams()": "0xfc49710b",
    "optionMarginParams(uint256)": "0xbe027d0a",
    "perpMarginRequirements(uint256)": "0xbf270f9d",
    "baseMarginParams(uint256)": "0xcd27955d",
    "oracleContingencyParams(uint256)": "0x0addd056",
    "depegParams()": "0x4deda10f",
    "aggregate3((address,bool,bytes)[])": "0x82ad56cb",
}
SEL = {sig.split("(")[0]: s for sig, s in SELECTOR_SIGNATURES.items()}

# ---- event topics: keccak256(signature) ------------------------------------------------------------------------------
TOPIC_SIGNATURES = {
    "BasisContingencyParamsUpdated": "BasisContingencyParamsUpdated((uint256,uint256,uint256,uint256))",
    "OtherContingencyParamsUpdated":
        "OtherContingencyParamsUpdated((uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256))",
    "MarginParamsUpdated": "MarginParamsUpdated((uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256))",
    "VolShockParamsUpdated": "VolShockParamsUpdated((uint256,uint256,int256,int256,uint256,uint256))",
    "SkewShockParamsUpdated": "SkewShockParamsUpdated((uint256,uint256,int256,int256,int256,int256,int256,int256))",
    "CollateralParametersUpdated": "CollateralParametersUpdated(address,(bool,bool,uint256,uint256))",
    "ScenariosUpdated": "ScenariosUpdated((uint256,uint8,uint256)[])",
    "ScenariosUpdatedLegacy": "ScenariosUpdated((uint256,uint8)[])",
    "MaxExpiriesUpdated": "MaxExpiriesUpdated(uint256)",
    "LibOverrideUpdated": "LibOverrideUpdated(uint256,address)",
    "Upgraded": "Upgraded(address)",
    "Initialized": "Initialized(uint64)",
    "Initialized8": "Initialized(uint8)",
    "OptionMarginParamsSet":
        "OptionMarginParamsSet(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)",
    "PerpMarginRequirementsSet": "PerpMarginRequirementsSet(uint256,uint256,uint256)",
    "BaseMarginParamsSet": "BaseMarginParamsSet(uint256,uint256,uint256)",
    "OracleContingencySet": "OracleContingencySet(uint256,uint256,uint256,uint256)",
    "DepegParametersSet": "DepegParametersSet(uint256,uint256)",
}
TOPICS = {
    "BasisContingencyParamsUpdated": "0x245b48db44e4c35602ea46d52ba878e5119e0d6551ac8a359d06857899c76a07",
    "OtherContingencyParamsUpdated": "0x878d248aabef66910a0db4f344baeb2d4eed1e5671e6185cfefc1e7297b88187",
    "MarginParamsUpdated": "0x7fc48aed126fe9a55b9b95042f6bbbcf7f3aeb0403597a8a66e6b4c236b9cb3f",
    "VolShockParamsUpdated": "0x7a181c4ed98679eb06c72bef2404a0c21c27abafb12ca331d2a12afc45d64420",
    "SkewShockParamsUpdated": "0x1c2f5728dc6a261d78a7b641473e550eeb6ac3af0181fc78121f81ee93d39814",
    "CollateralParametersUpdated": "0xf70803c1931ce412fe6048082652ece6f686e088fb94cf615534f1bea05e572a",
    "ScenariosUpdated": "0x3482100b2761fc927ea0c628603e1861ec49f72f2ed058614a2ceaa2f8c670d6",
    "ScenariosUpdatedLegacy": "0x7f7690a00e29674f73d0b3cc104203d77f221faee6da93a98fdf34951fd3d7d1",
    "MaxExpiriesUpdated": "0x520b49625076bfb12eef67bed24aff3e10e13f167ab1b8f8435bbd2e96ebb793",
    "LibOverrideUpdated": "0x18cf9b0bbe44e80c6e12fdd03dcb2ad256b98ad11e37052fd4d304bd9622b605",
    "Upgraded": "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b",
    "Initialized": "0xc7f505b2f371ae2175ee4913f4499e1f2633a7b5936321eed1cdaeb6115181d2",
    "Initialized8": "0x7f26b83ff96e1f2b6a682f133852f6798a09c465da95921460cefb3847402498",
    "OptionMarginParamsSet": "0x27fa2a745852078008c414643388a6fefaf9faee66bc7f723b7f4c7a35b63f2b",
    "PerpMarginRequirementsSet": "0x7ef63c5e116ba6a9c9d4657818cbb09bbb5a240c20495877a3e207678ec2bfb7",
    "BaseMarginParamsSet": "0xd7ce30aef0d6359722a20b0b2afdb2cdd6bf9c765f7d024608bc7eb257f8cd64",
    "OracleContingencySet": "0x1d062a3f808d5f043e2ea62f5b4f1b9b3f3d0a1d4b352d2a756c1cf875ff3bb1",
    "DepegParametersSet": "0x2867ed6dc95c8ca39e804f743f584442f8061109e1239d1f6c505a81bd7047fc",
}
TOPIC_NAME = {v: k for k, v in TOPICS.items()}
LIB2_EVENTS = ("BasisContingencyParamsUpdated", "OtherContingencyParamsUpdated", "MarginParamsUpdated",
               "VolShockParamsUpdated", "SkewShockParamsUpdated", "CollateralParametersUpdated")
PM2_MANAGER_EVENTS = ("ScenariosUpdated", "MaxExpiriesUpdated", "LibOverrideUpdated", "Upgraded", "Initialized",
                      "Initialized8")
PM_MANAGER_EVENTS = ("ScenariosUpdatedLegacy", "MaxExpiriesUpdated")
SM_EVENTS = ("OptionMarginParamsSet", "PerpMarginRequirementsSet", "BaseMarginParamsSet", "OracleContingencySet",
             "DepegParametersSet")
SM_MARKET_EVENTS = ("OptionMarginParamsSet", "PerpMarginRequirementsSet", "BaseMarginParamsSet")

# ---- struct layouts: (field, kind); u = uint/1e18, i = int/1e18, s = seconds, b = bool -----------------------------
_U8 = lambda names: [(n, "u") for n in names]  # noqa: E731
PM2_STRUCTS = {
    "VolShockParameters": ("getVolShockParams", [("volRangeUp", "u"), ("volRangeDown", "u"), ("shortTermPower", "i"),
                                                 ("longTermPower", "i"), ("dteFloor", "s"), ("minVolUpShock", "u")]),
    "MarginParameters": ("getMarginParams", _U8(["imFactor", "mmFactor", "shortRateMultScale", "longRateMultScale",
                                                 "shortRateAddScale", "longRateAddScale", "shortBaseStaticDiscount",
                                                 "longBaseStaticDiscount"])),
    "BasisContingencyParameters": ("getBasisContingencyParams", _U8(["scenarioSpotUp", "scenarioSpotDown",
                                                                     "basisContAddFactor", "basisContMultFactor"])),
    "OtherContingencyParameters": ("getOtherContingencyParams", _U8(["pegLossThreshold", "pegLossFactor",
                                                                     "confThreshold", "confMargin", "MMPerpPercent",
                                                                     "IMPerpPercent", "MMOptionPercent",
                                                                     "IMOptionPercent"])),
    "SkewShockParameters": ("getSkewShockParams", [("linearBaseCap", "u"), ("absBaseCap", "u"), ("linearCBase", "i"),
                                                   ("absCBase", "i"), ("minKStar", "i"), ("widthScale", "i"),
                                                   ("volParamStatic", "i"), ("volParamScale", "i")]),
}
COLLATERAL_FIELDS = [("isEnabled", "b"), ("isRiskCancelling", "b"), ("MMHaircut", "u"), ("IMHaircut", "u")]
PM_STRUCTS = {
    "VolShockParameters": ("getVolShockParams", [("volRangeUp", "u"), ("volRangeDown", "u"), ("shortTermPower", "i"),
                                                 ("longTermPower", "i"), ("dteFloor", "s")]),
    "MarginParameters": ("getStaticDiscountParams", _U8(["imFactor", "rateMultScale", "rateAddScale",
                                                         "baseStaticDiscount"])),
    "BasisContingencyParameters": ("getBasisContingencyParams", _U8(["scenarioSpotUp", "scenarioSpotDown",
                                                                     "basisContAddFactor", "basisContMultFactor"])),
    "OtherContingencyParameters": ("getOtherContingencyParams", _U8(["pegLossThreshold", "pegLossFactor",
                                                                     "confThreshold", "confMargin", "basePercent",
                                                                     "perpPercent", "optionPercent"])),
}
SM_STRUCTS = {
    "OptionMarginParams": ("optionMarginParams", _U8(["maxSpotReq", "minSpotReq", "mmCallSpotReq", "mmPutSpotReq",
                                                      "MMPutMtMReq", "unpairedIMScale", "unpairedMMScale",
                                                      "mmOffsetScale"])),
    "PerpMarginRequirements": ("perpMarginRequirements", _U8(["mmPerpReq", "imPerpReq"])),
    "BaseMarginParams": ("baseMarginParams", _U8(["marginFactor", "IMScale"])),
    "OracleContingencyParams": ("oracleContingencyParams", _U8(["perpThreshold", "optionThreshold", "baseThreshold",
                                                                "OCFactor"])),
    "DepegParams": ("depegParams", _U8(["threshold", "depegFactor"])),
}


class Deadline(Exception):
    """Raised before a network request once the time budget of a resumable run is used up."""


# =====================================================================================================================
# ABI helpers
# =====================================================================================================================

def words(b: bytes) -> List[int]:
    return [int.from_bytes(b[i:i + 32], "big") for i in range(0, len(b) - len(b) % 32, 32)]


def _signed(x: int) -> int:
    return x - (1 << 256) if x >= (1 << 255) else x


def _enc_uint(x: int) -> str:
    return format(x, "064x")


def _enc_address(a: str) -> str:
    return a.lower().replace("0x", "").rjust(64, "0")


def _address(word: int) -> str:
    return "0x" + format(word, "040x")[-40:]


def decode_struct(b: bytes, fields: Sequence[Tuple[str, str]]) -> dict:
    w = words(b)
    if len(w) < len(fields):
        raise ValueError(f"expected {len(fields)} words, got {len(w)}")
    out = {}
    for (name, kind), x in zip(fields, w):
        if kind == "u":
            out[name] = x / E18
        elif kind == "i":
            out[name] = _signed(x) / E18
        elif kind == "s":
            out[name] = float(x)
        elif kind == "b":
            out[name] = bool(x)
        else:
            raise ValueError(kind)
    return out


def decode_scenarios(b: bytes, width: int) -> List[dict]:
    """``Scenario[]`` of PMRM_2 (width 3: spotShock, volShock, dampeningFactor) or PMRM (width 2)."""
    w = words(b)
    if not w:
        return []
    head = w[0] // 32
    n = w[head]
    out = []
    for i in range(n):
        base = head + 1 + width * i
        s = {"spotShock": w[base] / E18, "volShock": int(w[base + 1])}
        if width == 3:
            s["dampeningFactor"] = w[base + 2] / E18
        out.append(s)
    return out


def encode_aggregate3(calls: Sequence[Tuple[str, str]]) -> str:
    """Calldata of ``Multicall3.aggregate3((address target, bool allowFailure, bytes callData)[])``, allowFailure on."""
    tuples = []
    for to, data in calls:
        payload = bytes.fromhex(data[2:] if data.startswith("0x") else data)
        padded = payload.hex() + "00" * ((32 - len(payload) % 32) % 32)
        tuples.append(_enc_address(to) + _enc_uint(1) + _enc_uint(96) + _enc_uint(len(payload)) + padded)
    offsets, pos = [], 32 * len(tuples)
    for t in tuples:
        offsets.append(pos)
        pos += len(t) // 2
    body = _enc_uint(32) + _enc_uint(len(tuples)) + "".join(_enc_uint(o) for o in offsets) + "".join(tuples)
    return SEL["aggregate3"] + body


def decode_aggregate3(b: bytes) -> List[Tuple[bool, bytes]]:
    """Return value ``(bool success, bytes returnData)[]`` of ``aggregate3``."""
    def word(pos: int) -> int:
        return int.from_bytes(b[pos:pos + 32], "big")

    arr = word(0)
    n = word(arr)
    start = arr + 32
    out = []
    for i in range(n):
        t = start + word(start + 32 * i)
        ok = bool(word(t))
        d = t + word(t + 32)
        size = word(d)
        out.append((ok, bytes(b[d + 32:d + 32 + size])))
    return out


def batch_call(rpc, calls: Sequence[Tuple[str, str]], block: int) -> List[Optional[bytes]]:
    """``eth_call`` of every (to, data) at ``block``: one Multicall3 request per chunk where Multicall3 exists, single
    calls before. A reverted call gives ``None``; a call to an address without code gives ``b""``."""
    if not calls:
        return []
    if block >= MULTICALL3_BLOCK:
        out: List[Optional[bytes]] = []
        for i in range(0, len(calls), MULTICALL_CHUNK):
            chunk = calls[i:i + MULTICALL_CHUNK]
            res = rpc.raw("eth_call", [{"to": MULTICALL3, "data": encode_aggregate3(chunk)}, hex(int(block))])
            dec = decode_aggregate3(bytes.fromhex(res[2:]))
            if len(dec) != len(chunk):
                raise ValueError(f"multicall returned {len(dec)} results for {len(chunk)} calls")
            out.extend(ret if ok else None for ok, ret in dec)
        return out
    out = []
    for to, data in calls:
        try:
            out.append(rpc.eth_call(to, data, block))
        except RpcError:
            out.append(None)
    return out


# =====================================================================================================================
# Assembling the parameter dicts
# =====================================================================================================================

def _uint0(b: Optional[bytes]) -> Optional[int]:
    w = words(b or b"")
    return int(w[0]) if w else None


def assemble_pm2(raw: Dict[str, Optional[bytes]], collaterals: Dict[str, Optional[bytes]]) -> Optional[dict]:
    if any(not raw.get(getter) for getter, _ in PM2_STRUCTS.values()):
        return None
    p = {name: decode_struct(raw[getter], fields) for name, (getter, fields) in PM2_STRUCTS.items()}
    col = {}
    for asset in sorted(collaterals):
        b = collaterals[asset]
        if not b:
            continue
        c = decode_struct(b, COLLATERAL_FIELDS)
        if any(c.values()):
            col[asset.lower()] = c
    p["CollateralParameters"] = col
    p["scenarios"] = decode_scenarios(raw.get("scenarios") or b"", 3)
    p["maxExpiries"] = _uint0(raw.get("maxExpiries")) or 0
    return p


def assemble_pm(raw: Dict[str, Optional[bytes]]) -> Optional[dict]:
    if any(not raw.get(getter) for getter, _ in PM_STRUCTS.values()):
        return None
    p = {name: decode_struct(raw[getter], fields) for name, (getter, fields) in PM_STRUCTS.items()}
    p["scenarios"] = decode_scenarios(raw.get("scenarios") or b"", 2)
    p["maxExpiries"] = _uint0(raw.get("maxExpiries")) or 0
    return p


def assemble_sm(raw: Dict[str, Optional[bytes]]) -> Optional[dict]:
    if any(not raw.get(getter) for getter, _ in SM_STRUCTS.values()):
        return None
    return {name: decode_struct(raw[getter], fields) for name, (getter, fields) in SM_STRUCTS.items()}


@dataclass(frozen=True)
class Target:
    """One parameter set to read: ``(ccy, mgr)`` or a PM2 override lib ``(ccy, "pm2", lib)``."""

    ccy: str
    mgr: str
    lib: Optional[str] = None
    first_block: int = 0
    assets: Tuple[str, ...] = ()

    @property
    def key(self) -> str:
        return f"{self.ccy}/{self.mgr}" + (f"@{self.lib.lower()}" if self.lib else "")

    @property
    def cache_key(self) -> str:
        if not self.assets:
            return self.key
        return self.key + "#" + hashlib.sha1(",".join(self.assets).encode()).hexdigest()[:8]

    @property
    def lib_address(self) -> str:
        if self.mgr == "pm2":
            return (self.lib or PM2_ADDR[self.ccy]["lib"]).lower()
        if self.mgr == "pm":
            return PM_ADDR[self.ccy]["lib"]
        raise ValueError("SM has no lib")

    def calls(self) -> List[Tuple[str, str, str]]:
        if self.mgr == "sm":
            m = _enc_uint(SM_MARKET[self.ccy])
            return [(getter, SRM, SEL[getter] + ("" if getter == "depegParams" else m))
                    for getter, _ in SM_STRUCTS.values()]
        if self.mgr == "pm":
            mgr, lib = PM_ADDR[self.ccy]["manager"], self.lib_address
            return ([("scenarios", mgr, SEL["getScenarios"]), ("maxExpiries", mgr, SEL["maxExpiries"])]
                    + [(getter, lib, SEL[getter]) for getter, _ in PM_STRUCTS.values()])
        mgr, lib = PM2_ADDR[self.ccy]["manager"], self.lib_address
        out = [("scenarios", mgr, SEL["getScenarios"]), ("maxExpiries", mgr, SEL["maxExpiries"]),
               ("lib", mgr, SEL["lib"])]
        out += [(getter, lib, SEL[getter]) for getter, _ in PM2_STRUCTS.values()]
        out += [(f"col:{a}", lib, SEL["getCollateralParameters"] + _enc_address(a)) for a in self.assets]
        return out

    def assemble(self, res: Dict[str, Optional[bytes]]) -> Optional[dict]:
        if self.mgr == "sm":
            return assemble_sm(res)
        if self.mgr == "pm":
            return assemble_pm(res)
        if not self.lib and res.get("lib"):
            live = _address(words(res["lib"])[0])
            if live != self.lib_address:
                raise ValueError(f"{self.key}: manager lib() is {live}, expected {self.lib_address}")
        cols = {k[4:]: v for k, v in res.items() if k.startswith("col:")}
        return assemble_pm2(res, cols)


# =====================================================================================================================
# Resumable snapshot store
# =====================================================================================================================

def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class SnapshotStore:
    """Append-only cache ``(block, target) -> params`` with deduplicated parameter states."""

    def __init__(self, root: Path = DATA_DIR):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "snapshots.jsonl"
        self.states_path = self.root / "states.jsonl"
        self.index: Dict[Tuple[int, str], Optional[str]] = {}
        self.states: Dict[str, dict] = {}
        if self.states_path.exists():
            for line in self.states_path.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.states[row["digest"]] = row["params"]
        if self.index_path.exists():
            for line in self.index_path.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    if row["digest"] is None or row["digest"] in self.states:
                        self.index[(int(row["block"]), row["target"])] = row["digest"]

    def has(self, block: int, target: str) -> bool:
        return (int(block), target) in self.index

    def get(self, block: int, target: str) -> Optional[dict]:
        d = self.index[(int(block), target)]
        return None if d is None else json.loads(_canon(self.states[d]))

    def put(self, block: int, target: str, params: Optional[dict]) -> None:
        digest = None
        if params is not None:
            digest = hashlib.sha1(_canon(params).encode()).hexdigest()
            if digest not in self.states:
                self.states[digest] = json.loads(_canon(params))
                with self.states_path.open("a") as fh:
                    fh.write(json.dumps({"digest": digest, "params": params}) + "\n")
        self.index[(int(block), target)] = digest
        with self.index_path.open("a") as fh:
            fh.write(json.dumps({"block": int(block), "target": target, "digest": digest}) + "\n")


def snapshot(rpc, store: SnapshotStore, block: int, targets: Sequence[Target],
             deadline: Optional[float] = None) -> Dict[str, Optional[dict]]:
    """Parameters of every target at the end of ``block`` (cached); ``None`` before a target's first block."""
    todo = [t for t in targets if block >= t.first_block and not store.has(block, t.cache_key)]
    if todo:
        if deadline is not None and time.monotonic() > deadline:
            raise Deadline()
        calls, spans = [], []
        for t in todo:
            cs = t.calls()
            spans.append((t, len(calls), cs))
            calls.extend(cs)
        results = batch_call(rpc, [(to, data) for _, to, data in calls], block)
        for t, i0, cs in spans:
            res = {name: results[i0 + j] for j, (name, _, _) in enumerate(cs)}
            store.put(block, t.cache_key, t.assemble(res))
    return {t.key: (store.get(block, t.cache_key) if block >= t.first_block else None) for t in targets}


# =====================================================================================================================
# Events
# =====================================================================================================================

LOG_LIMIT = 10_000


def fetch_logs(rpc, addresses: Sequence[str], topics: Sequence[str], lo: int, hi: int,
               min_span: int = 1_000) -> List[dict]:
    """All logs of ``addresses`` with topic0 in ``topics`` in [lo, hi]; the range is halved on node errors."""
    flt = {"address": list(addresses), "topics": [list(topics)], "fromBlock": hex(lo), "toBlock": hex(hi)}
    try:
        part = rpc.raw("eth_getLogs", [flt])
    except RpcError:
        if hi - lo < min_span:
            raise
        part = None
    if part is None or (len(part) >= LOG_LIMIT and hi > lo):
        mid = (lo + hi) // 2
        return (fetch_logs(rpc, addresses, topics, lo, mid, min_span)
                + fetch_logs(rpc, addresses, topics, mid + 1, hi, min_span))
    return list(part)


def decode_event(log: dict) -> dict:
    name = TOPIC_NAME.get(log["topics"][0].lower(), "unknown")
    block = int(log["blockNumber"], 16)
    data = bytes.fromhex(log["data"][2:])
    w = words(data)
    row = {"block": block, "log_index": int(log["logIndex"], 16), "tx": log["transactionHash"],
           "address": log["address"].lower(), "event": name, "ts": ts_at_block(block)}
    if name == "LibOverrideUpdated":
        row["account"] = int(log["topics"][1], 16)
        row["lib"] = _address(w[0])
    elif name == "CollateralParametersUpdated":
        row["asset"] = _address(w[0])
    elif name in SM_MARKET_EVENTS:
        row["market"] = int(w[0])
    elif name == "Upgraded":
        row["implementation"] = _address(int(log["topics"][1], 16))
    elif name == "MaxExpiriesUpdated":
        row["value"] = int(w[0])
    return row


def all_event_filters() -> List[Tuple[str, List[str], List[str]]]:
    """(name, addresses, topics) of every event query of this task (override libs are queried separately)."""
    out = [("srm", [SRM], [TOPICS[e] for e in SM_EVENTS])]
    out.append(("pm", [PM_ADDR[c]["manager"] for c in PM_ADDR] + [PM_ADDR[c]["lib"] for c in PM_ADDR],
                [TOPICS[e] for e in PM_MANAGER_EVENTS]))
    out.append(("pm2", [PM2_ADDR[c]["manager"] for c in PM2_ADDR] + [PM2_ADDR[c]["lib"] for c in PM2_ADDR],
                [TOPICS[e] for e in PM2_MANAGER_EVENTS + LIB2_EVENTS]))
    return out


# =====================================================================================================================
# Timelines
# =====================================================================================================================

def _utc(ts: int) -> str:
    return dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def mark_changes(rows: Iterable[dict]) -> List[dict]:
    """Sort by block, drop rows whose params equal the previous row's, and list the changed top-level keys."""
    out: List[dict] = []
    for r in sorted(rows, key=lambda r: (r["from_block"], r.get("from_ts", 0))):
        if out and _canon(out[-1]["params"]) == _canon(r["params"]):
            continue
        prev = out[-1]["params"] if out else {}
        keys = sorted(set(prev) | set(r["params"]))
        row = dict(r)
        row["changed"] = [k for k in keys if _canon(prev.get(k)) != _canon(r["params"].get(k))]
        out.append(row)
    return out


class Timeline:
    """Parameter timeline of one currency and manager (or one PM2 override lib)."""

    def __init__(self, ccy: str, mgr: str, lib: Optional[str] = None, root: Optional[Path] = None,
                 entries: Optional[List[dict]] = None):
        self.ccy, self.mgr, self.lib = ccy, mgr, (lib.lower() if lib else None)
        self.root = Path(root) if root is not None else PARAMS_DIR
        if entries is None:
            entries = json.loads(self.path(ccy, mgr, lib, self.root).read_text())
        self.entries = sorted(entries, key=lambda e: (e["from_ts"], e["from_block"]))
        self._ts = [int(e["from_ts"]) for e in self.entries]

    @staticmethod
    def path(ccy: str, mgr: str, lib: Optional[str] = None, root: Optional[Path] = None) -> Path:
        root = Path(root) if root is not None else PARAMS_DIR
        name = f"{ccy}_{mgr}" + (f"_lib_{lib.lower()[2:10]}" if lib else "")
        return root / f"{name}.json"

    def entry_at(self, ts: int) -> dict:
        i = bisect.bisect_right(self._ts, int(ts)) - 1
        if i < 0:
            raise KeyError(f"{self.ccy} {self.mgr}: no parameters before ts {ts}")
        return self.entries[i]

    def at(self, ts: int) -> dict:
        return self.entry_at(ts)["params"]

    def changes(self, keys: Optional[Sequence[str]] = None) -> List[int]:
        """``from_ts`` of every entry after the first, optionally only where one of ``keys`` changed."""
        out = []
        for prev, e in zip(self.entries, self.entries[1:]):
            changed = e.get("changed")
            if changed is None:
                changed = [k for k in sorted(set(prev["params"]) | set(e["params"]))
                           if _canon(prev["params"].get(k)) != _canon(e["params"].get(k))]
            if keys is None or any(k in changed for k in keys):
                out.append(int(e["from_ts"]))
        return out

    def save(self, root: Optional[Path] = None) -> Path:
        path = self.path(self.ccy, self.mgr, self.lib, root if root is not None else self.root)
        _write_json(path, self.entries, one_line_items=True)
        return path


def _write_json(path: Path, obj, one_line_items: bool = False) -> None:
    """Atomic JSON write; ``one_line_items`` writes a list with one compact line per item (small, diff friendly)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    if one_line_items and isinstance(obj, list):
        text = "[\n" + ",\n".join(json.dumps(x, ensure_ascii=False) for x in obj) + "\n]\n" if obj else "[]\n"
    else:
        text = json.dumps(obj, indent=1) + "\n"
    tmp.write_text(text)
    tmp.replace(path)


# =====================================================================================================================
# Block grids and change detection (legacy PM has no events)
# =====================================================================================================================

def first_block_at_or_after(ts: int) -> int:
    return block_at_ts(int(ts) - 1) + 1


def day_blocks(lo: int, hi: int) -> List[int]:
    """First block of every UTC day with lo <= block <= hi."""
    t = ts_at_block(lo)
    day = dt.datetime.fromtimestamp(t, dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    out = []
    while True:
        b = first_block_at_or_after(int(day.timestamp()))
        if b > hi:
            return out
        if b >= lo:
            out.append(b)
        day += dt.timedelta(days=1)


def month_blocks(lo: int, hi: int) -> List[int]:
    """First block of every UTC month with lo <= block <= hi."""
    t = dt.datetime.fromtimestamp(ts_at_block(lo), dt.timezone.utc)
    m = dt.datetime(t.year, t.month, 1, tzinfo=dt.timezone.utc)
    out = []
    while True:
        b = first_block_at_or_after(int(m.timestamp()))
        if b > hi:
            return out
        if b >= lo:
            out.append(b)
        m = dt.datetime(m.year + (m.month == 12), m.month % 12 + 1, 1, tzinfo=dt.timezone.utc)


def find_changes(state: Callable[[int], object], samples: Sequence[int]) -> List[int]:
    """Blocks at which ``state`` changes, found by bisection between consecutive samples that differ.

    Every returned block ``c`` satisfies ``state(c - 1) != state(c)``. A change that is reverted before the next sample
    stays invisible; denser samples (daily) reduce that risk.
    """
    blocks = sorted(set(int(b) for b in samples))
    if not blocks:
        return []
    out: List[int] = []
    prev_b, prev_s = blocks[0], state(blocks[0])
    for b in blocks[1:]:
        s_b = state(b)
        lo, s_lo = prev_b, prev_s
        while s_lo != s_b:
            l, h = lo, b
            while l + 1 < h:
                m = (l + h) // 2
                if state(m) == s_lo:
                    l = m
                else:
                    h = m
            out.append(h)
            lo, s_lo = h, state(h)
        prev_b, prev_s = b, s_b
    return sorted(set(out))


# =====================================================================================================================
# Account lib overrides
# =====================================================================================================================

LabelFn = Callable[[int], str]


def _label_fn(label: Optional[LabelFn]) -> LabelFn:
    return label if label is not None else p2ids.label  # looked up at call time (salt and ranking of the repo)


def _norm_lib(lib) -> Optional[str]:
    lib = str(lib).lower() if lib else None
    return None if lib is None or int(lib, 16) == 0 else lib


def overrides_from_raw(raw: Iterable[dict], label: Optional[LabelFn] = None) -> List[dict]:
    """Labelled override list for ``results/`` from the raw rows (``account`` = subaccount id, as in ``data/p2``).

    Accounts appear only as ``p2ids.label`` (``M1`` .. ``M10`` or salted HMAC); ``lib`` is lower case, ``None`` for
    the zero address (override removed, standard lib again).
    """
    lab = _label_fn(label)
    return [{"account": lab(int(r["account"])), "lib": _norm_lib(r["lib"]), "from_block": int(r["from_block"]),
             "from_ts": int(r["from_ts"])} for r in raw]


def overrides_from_events(events: Iterable[dict], label: Optional[LabelFn] = None) -> List[dict]:
    rows = sorted((e for e in events if e["event"] == "LibOverrideUpdated"), key=lambda e: (e["block"], e["log_index"]))
    return overrides_from_raw([{"account": e["account"], "lib": e["lib"], "from_block": e["block"],
                                "from_ts": ts_at_block(e["block"])} for e in rows], label)


def _raw_id(x, what: str) -> int:
    """Raw subaccount id (int or digit string); a label (``M1``, ``X...``) or anything else raises ``ValueError``."""
    if isinstance(x, bool) or x is None:
        raise ValueError(f"{what} {x!r} is not a raw subaccount id")
    if isinstance(x, numbers.Integral) and int(x) >= 0:
        return int(x)
    if isinstance(x, str) and x.strip().isdigit():
        return int(x)
    raise ValueError(f"{what} {x!r} is not a raw subaccount id: overrides are resolved through the raw ids of "
                     f"data/p2/params/{{CCY}}_pm2_overrides_raw.json, never through the rank-dependent labels")


def account_lib(overrides: Sequence[dict], account_id, ts: int) -> Optional[str]:
    """Override lib of an account at ``ts`` (``None`` = standard lib of the manager).

    ``overrides`` are raw rows (``load_overrides``, ``account`` = subaccount id); labelled rows raise ``ValueError``
    because a label names another account once the maker ranking changes. The last row with ``from_ts <= ts`` wins
    (ties in file order); the zero address removes the override.
    """
    acc = _raw_id(account_id, "account id")
    rows = sorted(((int(r["from_ts"]), int(r["from_block"]), i, _raw_id(r["account"], "override account"), r["lib"])
                   for i, r in enumerate(overrides)), key=lambda x: x[:3])
    lib = None
    for from_ts, _, _, a, r_lib in rows:
        if a == acc and from_ts <= int(ts):
            lib = _norm_lib(r_lib)
    return lib


def load_overrides(ccy: str, data_dir: Optional[Path] = None) -> List[dict]:
    """Raw override rows of ``ccy`` from ``{data_dir}/{CCY}_pm2_overrides_raw.json`` (default ``data/p2/params``).

    Rows ``{"account": int, "lib": lower case or None, "from_block", "from_ts"}`` in time order. The labelled
    ``results/p2/params/{CCY}_pm2_overrides.json`` is not read (export only).
    """
    data_dir = Path(data_dir) if data_dir is not None else DATA_DIR
    raw = json.loads((data_dir / f"{ccy}_pm2_overrides_raw.json").read_text())
    rows = [{"account": _raw_id(r["account"], "override account"), "lib": _norm_lib(r["lib"]),
             "from_block": int(r["from_block"]), "from_ts": int(r["from_ts"])} for r in raw]
    return sorted(rows, key=lambda r: (r["from_ts"], r["from_block"]))  # stable: file order within a block


def pm2_params_for_account(ccy: str, account_id, ts: int, root: Optional[Path] = None,
                           data_dir: Optional[Path] = None) -> dict:
    """PM2 parameters that apply to ``account_id`` (raw id) at ``ts``: its override lib if one is set, else the
    standard lib. Timelines from ``root`` (default ``results/p2/params``), overrides from ``data_dir``."""
    lib = account_lib(load_overrides(ccy, data_dir), account_id, ts)
    return Timeline(ccy, "pm2", lib=lib, root=root).at(ts)


def _unsalted_sha10(account_id: int) -> str:
    """Pseudonym of the first A2 run (reversible for small ids); only used to check files before relabelling."""
    return hashlib.sha256(str(int(account_id)).encode()).hexdigest()[:10]


def relabel_overrides(data_dir: Path = DATA_DIR, out_dir: Path = PARAMS_DIR, ccys: Sequence[str] = CCYS,
                      label: Optional[LabelFn] = None) -> Dict[str, int]:
    """Rewrite ``{CCY}_pm2_overrides.json`` from the raw rows in ``data_dir`` with ``p2ids`` labels, without RPC.

    An existing file must describe the same events (same lib, block and time per row, account equal to the old
    unsalted hash or already to the label); otherwise nothing is written and ``ValueError`` is raised.
    """
    lab = _label_fn(label)
    new_by_ccy: Dict[str, List[dict]] = {}
    for ccy in ccys:
        raw = json.loads((Path(data_dir) / f"{ccy}_pm2_overrides_raw.json").read_text())
        new = overrides_from_raw(raw, lab)
        path = Path(out_dir) / f"{ccy}_pm2_overrides.json"
        if path.exists():
            old = json.loads(path.read_text())
            if len(old) != len(new):
                raise ValueError(f"{path}: {len(old)} rows, raw file has {len(new)}")
            for i, (o, n, r) in enumerate(zip(old, new, raw)):
                if (o["lib"], int(o["from_block"]), int(o["from_ts"])) != (n["lib"], n["from_block"], n["from_ts"]):
                    raise ValueError(f"{path}: row {i} differs from the raw file")
                if o["account"] not in (_unsalted_sha10(r["account"]), n["account"]):
                    raise ValueError(f"{path}: row {i} belongs to another account than the raw file")
        new_by_ccy[ccy] = new
    for ccy, new in new_by_ccy.items():
        _write_json(Path(out_dir) / f"{ccy}_pm2_overrides.json", new, one_line_items=True)
    return {ccy: len(new) for ccy, new in new_by_ccy.items()}


# =====================================================================================================================
# Manager share of option OI (from data/p2/kontext/margin-historie/oi_legacy.json)
# =====================================================================================================================

def manager_oi_share(oi: dict) -> pd.DataFrame:
    """Monthly share of ``OptionAsset.totalPosition(manager)`` per currency (sample at 00:00:01 UTC on the 1st)."""
    rows = []
    for ccy in CCYS:
        series = {m: {r["month"]: r.get("oi") for r in oi["oi"].get(f"{ccy}.{m.upper()}", [])} for m in MANAGERS}
        months = sorted({mo for s in series.values() for mo in s if mo != "head"})
        for mo in months:
            vals = {m: (float(series[m].get(mo) or 0.0) if f"{ccy}.{m.upper()}" in oi["oi"] else None)
                    for m in MANAGERS}
            total = sum(v for v in vals.values() if v is not None)
            if total <= 0:
                continue
            rows.append({"month": mo, "ccy": ccy,
                         **{m: (vals[m] / total if vals[m] is not None else float("nan")) for m in MANAGERS}})
    return pd.DataFrame(rows, columns=["month", "ccy", "sm", "pm", "pm2"])


# =====================================================================================================================
# Loader (network)
# =====================================================================================================================

class Loader:
    """Resumable download of all timelines; every method is idempotent thanks to the caches under ``data_dir``."""

    def __init__(self, rpc, data_dir: Path = DATA_DIR, out_dir: Path = PARAMS_DIR, to_block: Optional[int] = None,
                 deadline: Optional[float] = None, log=print):
        """End block: ``to_block`` if given (and stored for later runs), else the stored one, else the chain head.

        A new end block is written to ``meta.json`` only after every log cache records the range it covers, so an
        interrupted run never mistakes an old cache for the new range.
        """
        self.rpc, self.data_dir, self.out_dir, self.deadline, self.log = rpc, Path(data_dir), Path(out_dir), deadline, log
        self.data_dir.mkdir(parents=True, exist_ok=True)
        meta_path = self.data_dir / "meta.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        self._migrate_log_caches(meta.get("to_block"))
        if to_block is not None:
            new = int(to_block)
        elif "to_block" in meta:
            new = int(meta["to_block"])
        else:
            new = int(rpc.raw("eth_blockNumber", []), 16)
        if meta.get("to_block") != new:
            if "to_block" in meta:
                meta.setdefault("previous_to_blocks", []).append(int(meta["to_block"]))
                self.log(f"end block {meta['to_block']} -> {new}")
            meta["to_block"] = new
            _write_json(meta_path, meta)
        self.to_block = new
        self.store = SnapshotStore(self.data_dir)
        self._events: Optional[List[dict]] = None

    # ---- events ------------------------------------------------------------------------------------------------------
    def _migrate_log_caches(self, covered_to: Optional[int]) -> None:
        """Log caches of the first A2 run are plain lists that cover ``[lo, meta.to_block]``; record that range."""
        for path in sorted(self.data_dir.glob("logs_*.json")):
            logs = json.loads(path.read_text())
            if isinstance(logs, list):
                _write_json(path, {"to_block": covered_to, "addresses": None, "topics": None, "from_block": None,
                                   "logs": logs})

    def _logs_cached(self, name: str, addresses: List[str], topics: List[str], lo: int) -> List[dict]:
        """Logs of one filter in ``[lo, self.to_block]``; refetched when the end block or the filter changes."""
        path = self.data_dir / f"logs_{name}.json"
        want = {"addresses": sorted(a.lower() for a in addresses), "topics": sorted(t.lower() for t in topics),
                "from_block": int(lo)}
        cache = json.loads(path.read_text()) if path.exists() else None
        if isinstance(cache, list):  # written before this loader existed and not migrated: range unknown
            cache = None
        if cache is not None:
            same_filter = all(cache.get(k) is None or cache.get(k) == v for k, v in want.items())
            covered = cache.get("to_block")
            if same_filter and covered is not None and covered >= self.to_block:
                addr, top = set(want["addresses"]), set(want["topics"])
                return [L for L in cache["logs"] if lo <= int(L["blockNumber"], 16) <= self.to_block
                        and L["address"].lower() in addr and L["topics"][0].lower() in top]
        self._check_deadline()
        logs = fetch_logs(self.rpc, addresses, topics, lo, self.to_block)
        _write_json(path, {**want, "to_block": self.to_block, "logs": logs})
        self.log(f"logs {name}: {len(logs)} up to block {self.to_block}")
        return logs

    def events(self) -> List[dict]:
        if self._events is not None:
            return self._events
        logs = []
        for name, addrs, topics in all_event_filters():
            logs += self._logs_cached(name, addrs, topics, SRM_DEPLOY_BLOCK)
        rows = [decode_event(L) for L in logs]
        libs = sorted({r["lib"] for r in rows if r["event"] == "LibOverrideUpdated" and int(r["lib"], 16) != 0})
        if libs:
            logs2 = self._logs_cached("override_libs", libs, [TOPICS[e] for e in LIB2_EVENTS],
                                      min(PM2_ADDR[c]["deploy_block"] for c in PM2_ADDR))
            rows += [decode_event(L) for L in logs2]
        self._events = sorted(rows, key=lambda r: (r["block"], r["log_index"]))
        _write_json(self.data_dir / "events_decoded.json", self._events)
        return self._events

    def _check_deadline(self) -> None:
        if self.deadline is not None and time.monotonic() > self.deadline:
            raise Deadline()

    # ---- targets -----------------------------------------------------------------------------------------------------
    def override_libs(self, ccy: str) -> List[str]:
        mgr = PM2_ADDR[ccy]["manager"]
        return sorted({e["lib"] for e in self.events() if e["event"] == "LibOverrideUpdated" and e["address"] == mgr
                       and int(e["lib"], 16) != 0})

    def assets(self, ccy: str) -> Tuple[str, ...]:
        libs = {PM2_ADDR[ccy]["lib"], *self.override_libs(ccy)}
        return tuple(sorted({e["asset"] for e in self.events()
                             if e["event"] == "CollateralParametersUpdated" and e["address"] in libs}))

    def lib_events(self, lib: str) -> List[dict]:
        return [e for e in self.events() if e["address"] == lib.lower() and e["event"] in LIB2_EVENTS]

    def targets(self) -> List[Target]:
        ev = self.events()
        out = []
        for ccy in CCYS:
            m = SM_MARKET[ccy]
            first = min(e["block"] for e in ev if e["event"] in SM_MARKET_EVENTS and e.get("market") == m)
            out.append(Target(ccy, "sm", first_block=first))
        for ccy in PM_ADDR:
            out.append(Target(ccy, "pm", first_block=PM_ADDR[ccy]["deploy_block"]))
        for ccy in CCYS:
            assets = self.assets(ccy)
            out.append(Target(ccy, "pm2", first_block=PM2_ADDR[ccy]["deploy_block"], assets=assets))
            for lib in self.override_libs(ccy):
                first = min(e["block"] for e in self.lib_events(lib))
                out.append(Target(ccy, "pm2", lib=lib, first_block=first, assets=assets))
        return out

    def target_blocks(self, t: Target) -> Dict[int, List[str]]:
        """Event blocks (with event names) at which target ``t`` may change."""
        ev = self.events()
        blocks: Dict[int, List[str]] = {}

        def add(e):
            if t.first_block <= e["block"] <= self.to_block:
                blocks.setdefault(e["block"], []).append(e["event"])

        if t.mgr == "sm":
            m = SM_MARKET[t.ccy]
            for e in ev:
                if e["address"] == SRM and (e.get("market") == m or e["event"] in ("OracleContingencySet",
                                                                                   "DepegParametersSet")):
                    add(e)
        elif t.mgr == "pm":
            for e in ev:
                if e["address"] == PM_ADDR[t.ccy]["manager"] and e["event"] in PM_MANAGER_EVENTS:
                    add(e)
        else:
            mgr = PM2_ADDR[t.ccy]["manager"]
            for e in ev:
                if e["address"] == t.lib_address and e["event"] in LIB2_EVENTS:
                    add(e)
                elif e["address"] == mgr and e["event"] in ("ScenariosUpdated", "MaxExpiriesUpdated", "Upgraded",
                                                            "Initialized", "Initialized8"):
                    add(e)
        blocks.setdefault(t.first_block, []).insert(0, "start")
        return blocks

    # ---- event-based timelines -----------------------------------------------------------------------------------
    def event_timeline(self, t: Target) -> List[dict]:
        rows = []
        for b, names in sorted(self.target_blocks(t).items()):
            p = snapshot(self.rpc, self.store, b, [t], self.deadline)[t.key]
            if p is None:
                continue
            row = {"from_block": b, "from_ts": ts_at_block(b), "from_utc": _utc(ts_at_block(b)),
                   "source": _source(names), "params": p}
            if t.mgr == "pm2":
                row["lib"] = t.lib_address
            rows.append(row)
        return mark_changes(rows)

    # ---- legacy PM ---------------------------------------------------------------------------------------------------
    def legacy_changes(self, t: Target, extra_samples: Sequence[int] = ()) -> Tuple[List[int], List[int], dict]:
        """Monthly samples plus bisection, then daily samples +-14 days around every change until stable.

        Returns ``(samples, changes, stages)``; ``stages`` records the changes after each stage for the documentation.
        """
        def state(b):
            return _canon(snapshot(self.rpc, self.store, b, [t], self.deadline)[t.key])

        start = t.first_block
        monthly = sorted({start, self.to_block, *month_blocks(start, self.to_block)})
        samples = sorted(set(monthly) | set(int(b) for b in extra_samples))
        changes = find_changes(state, samples)
        stages = {"monthly_samples": len(monthly), "extra_samples": len(set(extra_samples)),
                  "changes_after_bisection": list(changes)}
        while True:
            extra = set()
            for c in changes:
                extra |= set(day_blocks(max(start, c - 14 * DAY_BLOCKS), min(self.to_block, c + 14 * DAY_BLOCKS)))
            new_samples = sorted(set(samples) | extra)
            if new_samples == samples:
                stages["samples_total"] = len(samples)
                stages["changes_after_daily_around"] = list(changes)
                return samples, changes, stages
            samples = new_samples
            changes = find_changes(state, samples)

    def change_neighbourhood(self, t: Target, tl: Timeline, changes: Sequence[int], days: int = 14) -> List[dict]:
        """Daily samples +-``days`` around every change compared with the timeline (all must match)."""
        out = []
        for c in changes:
            blocks = day_blocks(max(t.first_block, c - days * DAY_BLOCKS), min(self.to_block, c + days * DAY_BLOCKS))
            ok = 0
            for b in blocks:
                got = snapshot(self.rpc, self.store, b, [t], self.deadline)[t.key]
                ok += _canon(got) == _canon(tl.at(ts_at_block(b)))
            out.append({"block": c, "utc": _utc(ts_at_block(c)), "days": len(blocks), "match": ok})
        return out

    def legacy_timeline(self, t: Target, changes: Sequence[int]) -> List[dict]:
        ev_blocks = self.target_blocks(t)
        rows = []
        for b in sorted({t.first_block, *changes}):
            p = snapshot(self.rpc, self.store, b, [t], self.deadline)[t.key]
            names = [n for n in ev_blocks.get(b, []) if n != "start"]
            src = "start" if b == t.first_block else "bisection"
            if names:
                src += "+" + _source(names)
            rows.append({"from_block": b, "from_ts": ts_at_block(b), "from_utc": _utc(ts_at_block(b)), "source": src,
                         "params": p, "lib": t.lib_address})
        return mark_changes(rows)

    # ---- daily verification ------------------------------------------------------------------------------------------
    def daily_blocks(self) -> List[int]:
        return day_blocks(MULTICALL3_BLOCK, self.to_block)

    def daily_sweep(self, targets: Sequence[Target]) -> int:
        n = 0
        for b in self.daily_blocks():
            if all(self.store.has(b, t.cache_key) or b < t.first_block for t in targets):
                continue
            snapshot(self.rpc, self.store, b, targets, self.deadline)
            n += 1
        return n

    def verify_daily(self, timelines: Dict[str, Timeline], targets: Sequence[Target]) -> dict:
        """Compare every cached daily snapshot with the timeline; ``active`` counts days from the target's start."""
        out = {}
        for t in targets:
            tl = timelines[t.key]
            n = ok = active = 0
            bad = []
            for b in self.daily_blocks():
                if not self.store.has(b, t.cache_key) and b >= t.first_block:
                    continue
                got = self.store.get(b, t.cache_key) if b >= t.first_block else None
                try:
                    want = tl.at(ts_at_block(b))
                except KeyError:
                    want = None
                n += 1
                active += got is not None or want is not None
                if _canon(got) == _canon(want):
                    ok += 1
                else:
                    bad.append({"block": b, "utc": _utc(ts_at_block(b))})
            out[t.key] = {"days": n, "active_days": active, "match": ok, "n_mismatch": len(bad), "mismatch": bad[:50]}
        return out

    # ---- orchestration -------------------------------------------------------------------------------------------
    def run(self) -> dict:
        targets = self.targets()
        timelines: Dict[str, Timeline] = {}
        for t in targets:
            if t.mgr == "pm":
                continue
            timelines[t.key] = Timeline(t.ccy, t.mgr, lib=t.lib, root=self.out_dir, entries=self.event_timeline(t))
            timelines[t.key].save()
            self.log(f"{t.key}: {len(timelines[t.key].entries)} entries")
        for ccy in CCYS:
            mgr = PM2_ADDR[ccy]["manager"]
            ev = [e for e in self.events() if e["address"] == mgr]
            _write_json(self.out_dir / f"{ccy}_pm2_overrides.json", overrides_from_events(ev), one_line_items=True)
            raw = [{"account": e["account"], "lib": e["lib"], "from_block": e["block"], "from_ts": e["ts"]}
                   for e in ev if e["event"] == "LibOverrideUpdated"]
            _write_json(self.data_dir / f"{ccy}_pm2_overrides_raw.json", raw)
        _write_json(Timeline.path("HYPE", "pm", root=self.out_dir), [])  # HYPE has no legacy PM
        legacy = {}
        for t in targets:
            if t.mgr == "pm":
                samples, changes, stages = self.legacy_changes(t)
                legacy[t.key] = stages
                timelines[t.key] = Timeline(t.ccy, "pm", root=self.out_dir, entries=self.legacy_timeline(t, changes))
                timelines[t.key].save()
                self.log(f"{t.key}: changes {[_utc(ts_at_block(c)) for c in changes]}")
        n = self.daily_sweep(targets)
        self.log(f"daily sweep: {n} new days")
        for t in targets:  # final legacy pass with every daily sample
            if t.mgr == "pm":
                samples, changes, stages = self.legacy_changes(t, extra_samples=self.daily_blocks())
                legacy[t.key]["changes_with_all_daily"] = changes
                timelines[t.key] = Timeline(t.ccy, "pm", root=self.out_dir, entries=self.legacy_timeline(t, changes))
                timelines[t.key].save()
                legacy[t.key]["neighbourhood"] = self.change_neighbourhood(t, timelines[t.key], changes)
        check = self.verify_daily(timelines, targets)
        summary = {"to_block": self.to_block, "to_utc": _utc(ts_at_block(self.to_block)), "legacy": legacy,
                   "daily_check": check, "events": _event_counts(self.events())}
        _write_json(self.data_dir / "summary.json", summary)
        return summary


def _source(names: Sequence[str]) -> str:
    uniq = []
    for n in names:
        if n != "start" and n not in uniq:
            uniq.append(n)
    if "start" in names:
        return "start" + ("+event:" + "+".join(uniq) if uniq else "")
    return "event:" + "+".join(uniq)


def _event_counts(events: Sequence[dict]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for e in events:
        k = f"{e['address']}:{e['event']}"
        out[k] = out.get(k, 0) + 1
    return out


# =====================================================================================================================
# Report (markdown table of changes)
# =====================================================================================================================

def _flat(params: dict, prefix: str = "") -> Dict[str, object]:
    out = {}
    for k, v in (params or {}).items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flat(v, key + "."))
        elif isinstance(v, list):
            out[key] = _canon(v)
        else:
            out[key] = v
    return out


def describe_change(prev: Optional[dict], cur: dict, max_items: int = 6) -> str:
    if prev is None:
        return "Start"
    a, b = _flat(prev), _flat(cur)
    parts = []
    for k in sorted(set(a) | set(b)):
        if a.get(k) == b.get(k):
            continue
        if k == "scenarios":
            parts.append(_describe_scenarios(json.loads(a.get(k) or "[]"), json.loads(b.get(k) or "[]")))
        elif k.startswith("CollateralParameters."):
            continue
        else:
            parts.append(f"{k.split('.')[-1]} {_fmt(a.get(k))}→{_fmt(b.get(k))}")
    ncol = sum(1 for k in set(a) | set(b) if k.startswith("CollateralParameters.") and a.get(k) != b.get(k))
    if ncol:
        parts.append(f"Collateral ({ncol} values)")
    if len(parts) > max_items:
        parts = parts[:max_items] + [f"… (+{len(parts) - max_items})"]
    return "; ".join(parts) if parts else "none"


def _grid(sc: Sequence[dict]) -> Tuple[Optional[float], int]:
    """Half width of the regular spot grid (undampened, vol None/Up/Down) and the number of tail scenarios."""
    reg = [s["spotShock"] for s in sc if s.get("dampeningFactor", 1.0) == 1.0 and s["volShock"] <= 2]
    tails = sum(1 for s in sc if s.get("dampeningFactor", 1.0) != 1.0)
    return (round(max(abs(x - 1.0) for x in reg) * 100, 2) if reg else None), tails


def _describe_scenarios(sa: Sequence[dict], sb: Sequence[dict]) -> str:
    (wa, ta), (wb, tb) = _grid(sa), _grid(sb)
    out = []
    if wa != wb:
        out.append(f"grid ±{_fmt(wa)} %→±{_fmt(wb)} %" if wa is not None else f"grid ±{_fmt(wb)} %")
    if ta != tb:
        out.append(f"tails {ta}→{tb}")
    elif ta and [s for s in sa if s.get("dampeningFactor", 1.0) != 1.0] != \
            [s for s in sb if s.get("dampeningFactor", 1.0) != 1.0]:
        out.append("tail dampening changed")
    if len(sa) != len(sb):
        out.append(f"{len(sa)}→{len(sb)} scenarios")
    if not out:
        out.append("scenarios rearranged")
    return "scenarios: " + ", ".join(out)


def _fmt(v) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def _table(tl: Timeline, path: Path, title: str, max_items: int = 14) -> List[str]:
    """Markdown table of one timeline; entries that only change CollateralParameters are counted, not listed."""
    shown = f"`{path.relative_to(REPO)}`" if path.is_absolute() and REPO in path.parents else f"`{path.name}`"
    lines = [f"\n**{title}** ({len(tl.entries)} entries, {shown})\n",
             "| from (UTC) | Block | Source | Change |", "|---|---|---|---|"]
    prev, col_only = None, 0
    for e in tl.entries:
        if prev is not None and e.get("changed") == ["CollateralParameters"]:
            col_only += 1
            prev = e["params"]
            continue
        src = e["source"].replace("+CollateralParametersUpdated", "")
        if len(src) > 60:
            src = src[:57] + "…"
        lines.append(f"| {e['from_utc'][:16]} | {e['from_block']} | {src} | "
                     f"{describe_change(prev, e['params'], max_items)} |")
        prev = e["params"]
    if col_only:
        lines.append(f"\nPlus {col_only} entries that only change `CollateralParameters` (not USDC, outside K).")
    return lines


def report_markdown(root: Path = PARAMS_DIR) -> str:
    root = Path(root)
    lines: List[str] = []
    for ccy in CCYS:
        for mgr in MANAGERS:
            path = Timeline.path(ccy, mgr, root=root)
            if path.exists():
                tl = Timeline(ccy, mgr, root=root)
                if tl.entries:
                    lines += _table(tl, path, f"{ccy} {mgr.upper()}")
        ov_path = root / f"{ccy}_pm2_overrides.json"
        if not ov_path.exists():
            continue
        ov = json.loads(ov_path.read_text())
        for lib in sorted({r["lib"] for r in ov if r["lib"]}):
            path = Timeline.path(ccy, "pm2", lib=lib, root=root)
            tl = Timeline(ccy, "pm2", lib=lib, root=root)
            rows = [r for r in ov if r["lib"] == lib]
            lines += _table(tl, path, f"{ccy} PM2 override lib {lib}")
            days = sorted({_utc(r["from_ts"])[:10] for r in rows})
            lines.append(f"\nAssignments: {len(rows)} events for {len({r['account'] for r in rows})} accounts "
                         f"on {len(days)} days ({days[0]} to {days[-1]}); revocations: "
                         f"{sum(1 for r in ov if r['lib'] is None)}.")
    return "\n".join(lines)


# =====================================================================================================================
# CLI: python3 -m derive_surface p2 params {load, oi-share, report, relabel}
# =====================================================================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m derive_surface p2 params")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ld = sub.add_parser("load", help="download/refresh all parameter timelines (resumable)")
    ld.add_argument("--to-block", type=int, default=None)
    ld.add_argument("--max-seconds", type=float, default=520.0)
    ld.add_argument("--rate", type=float, default=2.0)
    sub.add_parser("oi-share", help="write results/p2/manager_oi_share.csv from oi_legacy.json")
    sub.add_parser("report", help="print the markdown table of parameter changes")
    sub.add_parser("relabel", help="rewrite {CCY}_pm2_overrides.json with p2ids labels from the raw files (no RPC)")
    args = ap.parse_args(argv)
    if args.cmd == "relabel":
        print(json.dumps(relabel_overrides()))
        return 0
    if args.cmd == "oi-share":
        df = manager_oi_share(json.loads(OI_LEGACY.read_text()))
        OI_SHARE_CSV.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(OI_SHARE_CSV, index=False, float_format="%.6f")
        print(f"{OI_SHARE_CSV}: {len(df)} rows")
        return 0
    if args.cmd == "report":
        print(report_markdown())
        return 0
    rpc = Rpc(rate=min(args.rate, 2.0), log_path=LOG_PATH)
    loader = Loader(rpc, to_block=args.to_block, deadline=time.monotonic() + args.max_seconds)
    try:
        summary = loader.run()
    except Deadline:
        print("INCOMPLETE: time budget used up, run again to continue")
        return 3
    print(json.dumps({k: v for k, v in summary.items() if k != "events"}, indent=1)[:6000])
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
