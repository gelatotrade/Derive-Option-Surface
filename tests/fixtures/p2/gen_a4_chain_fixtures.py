"""Generate the Task A4 chain fixtures (not collected by pytest).

    python3 tests/fixtures/p2/gen_a4_chain_fixtures.py {sm,pm,accounts,pm_accounts} [--max-seconds 520]

* ``sm_chain_cases.json``: ``StandardManager.getIsolatedMargin`` at historical blocks (BTC, ETH, HYPE) together with
  every input the replica needs (SM market feeds and parameters read at the same block).
* ``pm_chain_cases.json``: the deployed legacy ``PMRMLib`` (``addPrecomputes`` then ``getMarginAndMarkToMarket``)
  on portfolios built exactly like ``PMRM._arrangePortfolio`` from the legacy manager's feeds, IM and MM.
* ``sm_chain_accounts.json``: whole SM accounts (``SubAccounts.getAccountBalances``) against
  ``StandardManager.getMarginAndMarkToMarket`` with all feed values of the account's markets.
* ``pm_chain_accounts.json``: whole legacy-PM maker accounts against ``PMRM.getMargin(account, isInitial)`` (and the
  MtM of ``getMarginAndMarkToMarket(account, true, 0)``) with every feed value; accounts are chosen from
  ``data/p2/books/snapshots.parquet`` (Task A5) by fixed criteria.

The two account fixtures identify real accounts (whole balances at a block, ``sha256(str(id))[:10]`` is reversible by
enumeration), so they are written to ``data/p2/fixtures_private`` (not tracked, Addendum 1.4, audit A01); the tests
skip without them. The case fixtures ``sm_chain_cases.json`` and ``pm_chain_cases.json`` hold synthetic portfolios
and stay in tests/fixtures/p2.

Needs network access to https://rpc.lyra.finance through ``derive_surface.p2chain.Rpc`` (<= 2 requests/s, every
request logged to ``data/p2/logs/A4.jsonl``), view calls bundled through Multicall3 (deployed on Chain 957 before
block 2 454 793), the Paper 1 SVI history under ``data/p1/volfeed/``, ``data/p1/derived/markouts.parquet`` and the
packages ``eth_abi`` / ``eth_hash`` (present on the author's system, not a dependency of ``derive_surface``).
Resumable: finished blocks stay in the output file; rerun until it prints ``done``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

import pandas as pd
from eth_abi import decode, encode
from eth_hash.auto import keccak

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from derive_surface.p2chain import Rpc, block_at_ts, ts_at_block  # noqa: E402

OUT = Path(__file__).resolve().parent
PRIVATE = ROOT / "data" / "p2" / "fixtures_private"  # account-identifying outputs, not tracked
LOG = ROOT / "data" / "p2" / "logs" / "A4.jsonl"
MC3 = "0xcA11bde05977b3631167028862bE2a173976CA11"
SRM = "0x28c9ddF9A3B29c2E6a561c1BC520954e5A33de5D"
SUBACCOUNTS = "0xE7603DF191D699d8BD9891b821347dbAb889E5a5"
CASH = "0x57B03E14d409ADC7fAb6CFc44b5886CAD2D5f02b"
PM = {"BTC": "0x45DA02B9cCF384d7DbDD7b2b13e705BADB43Db0D", "ETH": "0xe7cD9370CdE6C9b5eAbCe8f86d01822d3de205A0"}
MARKET = {"ETH": 1, "BTC": 2, "HYPE": 48}
STEP = {"BTC": 1000.0, "ETH": 50.0, "HYPE": 1.0}
E18 = 10 ** 18

SM_BLOCKS = [("BTC", "2024-02-15"), ("BTC", "2024-09-10"), ("BTC", "2025-03-05"), ("BTC", "2025-11-20"),
             ("BTC", "2026-09-10"), ("ETH", "2024-04-20"), ("ETH", "2025-01-15"), ("ETH", "2025-08-01"),
             ("ETH", "2026-06-01"), ("HYPE", "2025-12-01"), ("HYPE", "2026-04-15"), ("HYPE", "2026-09-10")]
PM_BLOCKS = [("BTC", "2024-03-01"), ("BTC", "2024-10-01"), ("BTC", "2025-06-01"), ("BTC", "2026-01-15"),
             ("ETH", "2024-05-01"), ("ETH", "2024-12-01"), ("ETH", "2025-04-01"), ("ETH", "2026-03-01")]
ACCOUNT_DAYS = ["2024-03-20", "2024-11-05", "2025-05-12", "2025-10-01", "2026-02-10", "2026-08-20"]
# legacy-PM account targets: one per parameter regime and currency (basis 1.0/1.2 until 12.06.2024, then 0.5/2.0;
# volRangeUp, optionPercent and scenarios change on 22.02.2025)
PM_ACCOUNT_TARGETS = [("ETH", "2024-03-15"), ("BTC", "2024-09-15"), ("ETH", "2024-12-15"), ("BTC", "2025-06-15"),
                      ("ETH", "2025-12-15")]

SH = "(uint256,uint256,int256,bool,bool)"
EH = f"(uint256,uint256,{SH}[],uint256,uint256,uint256,uint256,uint256,int256,int256,int256,uint256,uint256,uint256)"
PF = f"(uint256,uint256,uint256,int256,{EH}[],int256,uint256,uint256,int256,int256,uint256,uint256,uint256,int256)"
SC = "(uint256,uint8)"


def sel(sig: str) -> bytes:
    return keccak(sig.encode())[:4]


def cd(sig: str, types=(), args=()) -> bytes:
    return sel(sig) + (encode(list(types), list(args)) if types else b"")


def ts_of(day: str, hour: int = 12) -> int:
    return int(dt.datetime.strptime(day, "%Y-%m-%d").replace(hour=hour, tzinfo=dt.timezone.utc).timestamp())


class Chain:
    def __init__(self):
        self.rpc = Rpc(rate=2.0, log_path=LOG)

    def block_ts(self, block: int) -> int:
        ts = int(self.rpc.raw("eth_getBlockByNumber", [hex(block), False])["timestamp"], 16)
        assert ts == ts_at_block(block), (block, ts)
        return ts

    def multicall(self, calls, block: int, chunk: int = 40):
        """calls: list of (to, calldata bytes) -> list of (ok, return bytes)."""
        out = []
        for i in range(0, len(calls), chunk):
            part = calls[i:i + chunk]
            data = cd("aggregate3((address,bool,bytes)[])", ["(address,bool,bytes)[]"],
                      [[(to, True, c) for to, c in part]])
            raw = self.rpc.eth_call(MC3, "0x" + data.hex(), block)
            out.extend(decode(["(bool,bytes)[]"], raw)[0])
        return out

    def call(self, to: str, data: bytes, block: int) -> bytes:
        return self.rpc.eth_call(to, "0x" + data.hex(), block)


def addr(word: bytes) -> str:
    return "0x" + word[12:32].hex()


def dec(types, ok_ret):
    ok, ret = ok_ret
    if not ok:
        return None
    return decode(list(types), ret)


def active_expiries(ccy: str, ts: int, targets=(7, 60)):
    months = {dt.datetime.utcfromtimestamp(ts - d * 86400).strftime("%Y-%m") for d in (0, 1)}
    frames = [pd.read_parquet(ROOT / "data" / "p1" / "volfeed" / f"{ccy}_svi_{m}.parquet") for m in sorted(months)
              if (ROOT / "data" / "p1" / "volfeed" / f"{ccy}_svi_{m}.parquet").exists()]
    df = pd.concat(frames)
    df = df[(df.block_ts <= ts) & (df.block_ts >= ts - 3600) & (df.expiry > ts + 2 * 86400)]
    exps = sorted(int(e) for e in df.expiry.unique())
    chosen = []
    for d in targets:
        e = min(exps, key=lambda x: abs(x - ts - d * 86400))
        if e not in chosen:
            chosen.append(e)
    return chosen


def load(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {"source": "", "cases": []}


def save(path: Path, doc: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=1))
    tmp.replace(path)


def f18(x: int) -> float:
    return int(x) / E18


# ------------------------------------------------------------------------------------------------ SM params

SM_OPT = ["maxSpotReq", "minSpotReq", "mmCallSpotReq", "mmPutSpotReq", "MMPutMtMReq", "unpairedIMScale",
          "unpairedMMScale", "mmOffsetScale"]


def sm_param_calls(mid: int):
    return [(SRM, cd("getMarketFeeds(uint256)", ["uint256"], [mid])),
            (SRM, cd("optionMarginParams(uint256)", ["uint256"], [mid])),
            (SRM, cd("perpMarginRequirements(uint256)", ["uint256"], [mid])),
            (SRM, cd("baseMarginParams(uint256)", ["uint256"], [mid])),
            (SRM, cd("oracleContingencyParams(uint256)", ["uint256"], [mid])),
            (SRM, cd("depegParams()")), (SRM, cd("stableFeed()"))]


def sm_params_decode(res):
    feeds = [addr(res[0][1][i * 32:(i + 1) * 32]) for i in range(3)]
    o = dec(["uint256"] * 8, res[1])
    p = dec(["uint256"] * 2, res[2])
    b = dec(["uint256"] * 2, res[3])
    oc = dec(["uint256"] * 4, res[4])
    dp = dec(["uint256"] * 2, res[5])
    params = {"OptionMarginParams": dict(zip(SM_OPT, map(f18, o))),
              "PerpMarginRequirements": dict(zip(["mmPerpReq", "imPerpReq"], map(f18, p))),
              "BaseMarginParams": dict(zip(["marginFactor", "IMScale"], map(f18, b))),
              "OracleContingencyParams": dict(zip(["perpThreshold", "optionThreshold", "baseThreshold", "OCFactor"],
                                                  map(f18, oc))),
              "DepegParams": dict(zip(["threshold", "depegFactor"], map(f18, dp)))}
    return feeds, params, addr(res[6][1])


# ------------------------------------------------------------------------------------------------ SM isolated

def sm_case(chain: Chain, ccy: str, day: str) -> dict:
    ts0 = ts_of(day)
    block = block_at_ts(ts0)
    bts = chain.block_ts(block)
    mid = MARKET[ccy]
    (spot_f, fwd_f, vol_f), params, stable_f = sm_params_decode(chain.multicall(sm_param_calls(mid), block))
    exps = active_expiries(ccy, bts)
    calls = [(spot_f, cd("getSpot()")), (stable_f, cd("getSpot()"))]
    for e in exps:
        calls += [(fwd_f, cd("getForwardPrice(uint64)", ["uint64"], [e])),
                  (vol_f, cd("getExpiryMinConfidence(uint64)", ["uint64"], [e]))]
    res = chain.multicall(calls, block)
    spot, spot_conf = dec(["uint256", "uint256"], res[0])
    stable, _ = dec(["uint256", "uint256"], res[1])
    expiries = {}
    for i, e in enumerate(exps):
        fwd = dec(["uint256", "uint256"], res[2 + 2 * i])
        vc = dec(["uint256"], res[3 + 2 * i])
        if fwd is None or vc is None:
            continue
        expiries[e] = {"forward": f18(fwd[0]), "fwd_conf": f18(fwd[1]), "vol_conf": f18(vc[0]), "vols": {}}
    grid = []
    for e, d in expiries.items():
        for m in (0.7, 0.9, 1.0, 1.1, 1.4):
            k = max(STEP[ccy], round(d["forward"] * m / STEP[ccy]) * STEP[ccy])
            grid.append((e, k))
    res = chain.multicall([(vol_f, cd("getVol(uint128,uint64)", ["uint128", "uint64"], [int(k * E18), e]))
                           for e, k in grid], block)
    for (e, k), r in zip(grid, res):
        v = dec(["uint256", "uint256"], r)
        if v is not None:
            expiries[e]["vols"][repr(k)] = [f18(v[0]), f18(v[1])]
    rows_in = [(e, k, c, q, im) for e, k in grid if repr(k) in expiries[e]["vols"]
               for c in (True, False) for q in (-1.0, 1.0, -2.5) for im in (True, False)]
    res = chain.multicall([(SRM, cd("getIsolatedMargin(uint256,uint256,uint256,bool,int256,bool)",
                                    ["uint256", "uint256", "uint256", "bool", "int256", "bool"],
                                    [mid, int(k * E18), e, c, int(q * E18), im])) for e, k, c, q, im in rows_in],
                           block)
    rows = []
    for (e, k, c, q, im), r in zip(rows_in, res):
        out = dec(["int256", "int256"], r)
        if out is None:
            continue
        rows.append({"expiry": e, "strike": k, "is_call": c, "amount": q, "is_initial": im,
                     "margin": f18(out[0]), "mtm": f18(out[1])})
    return {"ccy": ccy, "day": day, "block": block, "ts": bts, "market_id": mid, "params": params,
            "spot": f18(spot), "spot_conf": f18(spot_conf), "stable": f18(stable),
            "expiries": {str(e): d for e, d in expiries.items()}, "rows": rows}


# ------------------------------------------------------------------------------------------------ legacy PM

def pm_case(chain: Chain, ccy: str, day: str) -> dict:
    ts0 = ts_of(day)
    block = block_at_ts(ts0)
    bts = chain.block_ts(block)
    pm = PM[ccy]
    names = ["spotFeed()", "stableFeed()", "forwardFeed()", "interestRateFeed()", "volFeed()", "lib()", "perp()"]
    res = chain.multicall([(pm, cd(n)) for n in names] + [(pm, cd("getScenarios()")), (pm, cd("maxExpiries()"))],
                          block)
    f = {n: addr(r[1]) for n, r in zip(names, res)}
    scen = decode([f"{SC}[]"], res[7][1])[0]
    max_exp = decode(["uint256"], res[8][1])[0]
    lib = f["lib()"]
    res = chain.multicall([(lib, cd("getBasisContingencyParams()")), (lib, cd("getVolShockParams()")),
                           (lib, cd("getStaticDiscountParams()")), (lib, cd("getOtherContingencyParams()")),
                           (f["spotFeed()"], cd("getSpot()")), (f["stableFeed()"], cd("getSpot()")),
                           (f["perp()"], cd("getPerpPrice()"))], block)
    bc = decode(["uint256"] * 4, res[0][1])
    vs = decode(["uint256", "uint256", "int256", "int256", "uint256"], res[1][1])
    mp = decode(["uint256"] * 4, res[2][1])
    oc = decode(["uint256"] * 7, res[3][1])
    spot, spot_conf = decode(["uint256", "uint256"], res[4][1])
    stable, _ = decode(["uint256", "uint256"], res[5][1])
    perp_price, perp_conf = decode(["uint256", "uint256"], res[6][1])
    params = {
        "BasisContingencyParameters": dict(zip(["scenarioSpotUp", "scenarioSpotDown", "basisContAddFactor",
                                                "basisContMultFactor"], map(f18, bc))),
        "VolShockParameters": {"volRangeUp": f18(vs[0]), "volRangeDown": f18(vs[1]), "shortTermPower": f18(vs[2]),
                               "longTermPower": f18(vs[3]), "dteFloor": float(vs[4])},
        "MarginParameters": dict(zip(["imFactor", "rateMultScale", "rateAddScale", "baseStaticDiscount"],
                                     map(f18, mp))),
        "OtherContingencyParameters": dict(zip(["pegLossThreshold", "pegLossFactor", "confThreshold", "confMargin",
                                                "basePercent", "perpPercent", "optionPercent"], map(f18, oc))),
        "scenarios": [{"spotShock": f18(s), "volShock": int(v)} for s, v in scen],
        "maxExpiries": int(max_exp),
    }
    exps = active_expiries(ccy, bts)
    calls = []
    for e in exps:
        calls += [(f["forwardFeed()"], cd("getForwardPricePortions(uint64)", ["uint64"], [e])),
                  (f["interestRateFeed()"], cd("getInterestRate(uint64)", ["uint64"], [e]))]
    res = chain.multicall(calls, block)
    expiries = {}
    for i, e in enumerate(exps):
        fp = dec(["uint256"] * 3, res[2 * i])
        rt = dec(["int256", "uint256"], res[2 * i + 1])
        if fp is None or rt is None:
            raise RuntimeError(f"feed missing for expiry {e} at block {block}")
        expiries[e] = {"fixed_wei": fp[0], "var_wei": fp[1], "fwd_conf_wei": fp[2], "rate_wei": rt[0],
                       "rate_conf_wei": rt[1], "vols": {}}
    e0, e1 = exps[0], exps[-1]
    F0 = (expiries[e0]["fixed_wei"] + expiries[e0]["var_wei"]) / E18
    F1 = (expiries[e1]["fixed_wei"] + expiries[e1]["var_wei"]) / E18

    def k(F, m):
        return max(STEP[ccy], round(F * m / STEP[ccy]) * STEP[ccy])

    books = {
        "short_otm_call": ([(e0, k(F0, 1.05), True, -1.0)], 0.0, 0.0),
        "long_puts": ([(e1, k(F1, 0.95), False, 2.0)], 0.0, 0.0),
        "short_deep_otm_put": ([(e0, k(F0, 0.8), False, -1.0)], 0.0, 0.0),
        "mixed_with_perp": ([(e0, k(F0, 1.0), True, -1.0), (e0, k(F0, 1.05), True, 1.0), (e0, k(F0, 0.95), False, -1.0),
                             (e0, k(F0, 0.8), False, 2.0), (e1, k(F1, 1.0), True, 1.0), (e1, k(F1, 1.0), False, -1.5),
                             (e1, k(F1, 1.25), True, -0.7)], -0.3, 0.0),
        "mixed_perp_base": ([(e0, k(F0, 1.0), True, -1.0), (e0, k(F0, 1.0), False, -1.0), (e1, k(F1, 1.1), True, -2.0),
                             (e1, k(F1, 0.9), False, 1.0)], 0.5, 0.25),
    }
    keys = sorted({(e, kk) for legs, _, _ in books.values() for e, kk, _, _ in legs})
    res = chain.multicall([(f["volFeed()"], cd("getVol(uint128,uint64)", ["uint128", "uint64"], [int(kk * E18), e]))
                           for e, kk in keys], block)
    for (e, kk), r in zip(keys, res):
        v = decode(["uint256", "uint256"], r[1])
        expiries[e]["vols"][repr(kk)] = [int(v[0]), int(v[1])]
    pfs = []
    for name, (legs, perp, base) in books.items():
        by = {}
        for e, kk, c, q in legs:
            by.setdefault(e, []).append((kk, c, q))
        min_conf = spot_conf if perp == 0 else min(spot_conf, perp_conf)
        exs = []
        for e, opts in by.items():
            d = expiries[e]
            mc = min(d["fwd_conf_wei"], d["rate_conf_wei"])
            net = 0
            sh = []
            for kk, c, q in opts:
                vol, vc = d["vols"][repr(kk)]
                mc = min(mc, vc)
                net += abs(int(q * E18))
                sh.append((int(kk * E18), vol, int(q * E18), c, False))
            exs.append((e, max(e - bts, 0), sh, d["fixed_wei"], d["var_wei"], max(d["rate_wei"], 0), mc, net,
                        0, 0, 0, 0, 0, 0))
        pfs.append((spot, perp_price if perp != 0 else 0, stable, 0, exs, int(perp * E18), int(base * E18), 0, 0, 0,
                    0, 0, min_conf, 0))
    res = chain.multicall([(lib, cd(f"addPrecomputes({PF})", [PF], [pf])) for pf in pfs], block, chunk=10)
    pf2s = [decode([PF], r[1])[0] for r in res]
    calls = [(lib, cd(f"getMarginAndMarkToMarket({PF},bool,{SC}[])", [PF, "bool", f"{SC}[]"], [pf2, im, scen]))
             for pf2 in pf2s for im in (True, False)]
    res = chain.multicall(calls, block, chunk=10)
    out_books = []
    for j, (name, (legs, perp, base)) in enumerate(books.items()):
        rec = {"name": name, "legs": [[e, kk, c, q] for e, kk, c, q in legs], "perp": perp, "base": base}
        for i, key in enumerate(("IM", "MM")):
            ok, ret = res[2 * j + i]
            if not ok:
                raise RuntimeError(f"getMarginAndMarkToMarket reverted for {name} at {block}")
            mg, mtm, worst = decode(["int256", "int256", "uint256"], ret)
            rec[key] = {"net": f18(mg), "mtm": f18(mtm), "worst": int(worst)}
        rec["staticContingency"] = f18(pf2s[j][10])
        rec["basisContingency"] = f18(pf2s[j][9])
        rec["confidenceContingency"] = f18(pf2s[j][11])
        out_books.append(rec)
    exp_out = {}
    for e, d in expiries.items():
        exp_out[str(e)] = {"fixed": f18(d["fixed_wei"]), "var": f18(d["var_wei"]), "fwd_conf": f18(d["fwd_conf_wei"]),
                           "rate": f18(d["rate_wei"]), "rate_conf": f18(d["rate_conf_wei"]),
                           "vols": {kk: [f18(v), f18(c)] for kk, (v, c) in d["vols"].items()}}
    return {"ccy": ccy, "day": day, "block": block, "ts": bts, "manager": pm, "lib": lib, "params": params,
            "spot": f18(spot), "spot_conf": f18(spot_conf), "stable": f18(stable), "perp_price": f18(perp_price),
            "perp_conf": f18(perp_conf), "expiries": exp_out, "books": out_books}


# ------------------------------------------------------------------------------------------------ SM accounts

def decode_subid(sub_id: int):
    return sub_id & 0xFFFFFFFF, ((sub_id >> 32) & 0x7FFFFFFFFFFFFFFF) * 10 ** 10 / E18, (sub_id >> 95) > 0


def account_case(chain: Chain, day: str, acc: int, block: int, bts: int, balances) -> dict:
    assets = sorted({a for a, _, _ in balances if a.lower() != CASH.lower()})
    res = chain.multicall([(SRM, cd("assetDetails(address)", ["address"], [a])) for a in assets], block)
    details = {a: decode(["bool", "uint8", "uint256"], r[1]) for a, r in zip(assets, res)}
    markets = sorted({int(d[2]) for d in details.values()})
    calls = []
    for mid in markets:
        calls += sm_param_calls(mid)
    res = chain.multicall(calls, block)
    mk = {}
    stable_f = None
    for i, mid in enumerate(markets):
        feeds, params, stable_f = sm_params_decode(res[7 * i:7 * i + 7])
        mk[mid] = {"feeds": feeds, "params": params, "options": [], "perp": None, "base": 0.0}
    cash = 0.0
    for a, sub, bal in balances:
        if a.lower() == CASH.lower():
            cash = f18(bal)
            continue
        ok, typ, mid = details[a]
        m = mk[int(mid)]
        if typ == 1:
            e, k, c = decode_subid(sub)
            m["options"].append([e, k, c, f18(bal)])
        elif typ == 2:
            m["perp"] = {"asset": a, "amount": f18(bal)}
        elif typ == 3:
            m["base"] = f18(bal)
        else:
            raise RuntimeError(f"unknown asset type {typ} for {a}")
    calls = [(stable_f, cd("getSpot()"))]
    idx = []
    for mid, m in mk.items():
        spot_f, fwd_f, vol_f = m["feeds"]
        calls.append((spot_f, cd("getSpot()")))
        idx.append(("spot", mid, None))
        for e in sorted({o[0] for o in m["options"]}):
            calls += [(fwd_f, cd("getForwardPrice(uint64)", ["uint64"], [e])),
                      (vol_f, cd("getExpiryMinConfidence(uint64)", ["uint64"], [e]))]
            idx += [("fwd", mid, e), ("vconf", mid, e)]
        for e, k, c, q in m["options"]:
            calls.append((vol_f, cd("getVol(uint128,uint64)", ["uint128", "uint64"], [int(round(k * E18)), e])))
            idx.append(("vol", mid, (e, k)))
        if m["perp"] is not None:
            p = m["perp"]["asset"]
            calls += [(p, cd("getPerpPrice()")), (p, cd("getUnsettledAndUnrealizedCash(uint256)", ["uint256"], [acc]))]
            idx += [("perp", mid, None), ("upnl", mid, None)]
    calls += [(SRM, cd("getMarginAndMarkToMarket(uint256,bool,uint256)", ["uint256", "bool", "uint256"], [acc, im, 0]))
              for im in (True, False)]
    res = chain.multicall(calls, block)
    stable = f18(decode(["uint256", "uint256"], res[0][1])[0])
    for (kind, mid, key), (ok, ret) in zip(idx, res[1:]):
        if not ok:
            raise RuntimeError(f"{kind} reverted for market {mid} {key}")
        m = mk[mid]
        if kind == "spot":
            s, sc = decode(["uint256", "uint256"], ret)
            m["spot"], m["spot_conf"] = f18(s), f18(sc)
        elif kind == "fwd":
            fw, fc = decode(["uint256", "uint256"], ret)
            m.setdefault("expiries", {}).setdefault(str(key), {})
            m["expiries"][str(key)].update({"forward": f18(fw), "fwd_conf": f18(fc)})
        elif kind == "vconf":
            m.setdefault("expiries", {}).setdefault(str(key), {})["vol_conf"] = f18(decode(["uint256"], ret)[0])
        elif kind == "vol":
            v, _ = decode(["uint256", "uint256"], ret)
            m.setdefault("vols", {})[f"{key[0]}|{key[1]!r}"] = f18(v)
        elif kind == "perp":
            pp, pc = decode(["uint256", "uint256"], ret)
            m["perp"].update({"price": f18(pp), "conf": f18(pc)})
        elif kind == "upnl":
            m["perp"]["upnl"] = f18(decode(["int256"], ret)[0])
    expect = {}
    for key, (ok, ret) in zip(("IM", "MM"), res[-2:]):
        if not ok:
            raise RuntimeError("getMarginAndMarkToMarket reverted")
        mg, mtm = decode(["int256", "int256"], ret)
        expect[key] = {"net": f18(mg), "mtm": f18(mtm)}
    for m in mk.values():
        m.pop("feeds")
    return {"day": day, "block": block, "ts": bts, "account_hash": hashlib.sha256(str(acc).encode()).hexdigest()[:10],
            "cash": cash, "stable": stable,
            "markets": {str(mid): m for mid, m in mk.items()}, **expect}


def find_accounts(chain: Chain, day: str, want: int = 2):
    ts0 = ts_of(day, 0)
    block = block_at_ts(ts0)
    bts = chain.block_ts(block)
    m = pd.read_parquet(ROOT / "data" / "p1" / "derived" / "markouts.parquet", columns=["ts", "taker_sub", "maker_sub"])
    w = m[(m.ts >= (ts0 - 3 * 86400) * 1000) & (m.ts < ts0 * 1000)]
    ids = pd.concat([w.taker_sub, w.maker_sub]).value_counts().index.astype(int).tolist()[:120]
    res = chain.multicall([(SUBACCOUNTS, cd("manager(uint256)", ["uint256"], [i])) for i in ids], block, chunk=60)
    sm_ids = [i for i, r in zip(ids, res) if r[0] and addr(r[1]).lower() == SRM.lower()]
    res = chain.multicall([(SUBACCOUNTS, cd("getAccountBalances(uint256)", ["uint256"], [i])) for i in sm_ids[:40]],
                          block, chunk=20)
    picked = []
    for i, r in zip(sm_ids[:40], res):
        if not r[0]:
            continue
        bals = decode(["(address,uint256,int256)[]"], r[1])[0]
        n_opt = sum(1 for a, s, b in bals if s != 0)
        if 2 <= n_opt <= 30:
            picked.append((n_opt, i, bals))
    picked.sort(key=lambda x: -x[0])
    return block, bts, picked[:want]


# ------------------------------------------------------------------------------------------------ legacy-PM accounts

def pick_pm_accounts():
    """(ccy, day, subaccount, block) per target: a snapshot with options and a perp under the legacy PM, 3 to 11
    expiries and 10 to 60 options, closest to the target day (ties: more expiries, then more options)."""
    df = pd.read_parquet(ROOT / "data" / "p2" / "books" / "snapshots.parquet",
                         columns=["subaccount", "day", "block", "manager", "kind", "expiry"])
    out = []
    for ccy, day in PM_ACCOUNT_TARGETS:
        d = df[df.manager.str.lower() == PM[ccy].lower()]
        g = d.groupby(["subaccount", "day", "block"]).agg(
            n=("kind", lambda k: int((k == "option").sum())), perp=("kind", lambda k: bool((k == "perp").any())),
            ne=("expiry", "nunique")).reset_index()
        g = g[g["perp"] & g["n"].between(10, 60) & g["ne"].between(3, 11)].copy()
        if g.empty:
            continue
        g["dist"] = (g.day - pd.Timestamp(day)).abs()
        g = g.sort_values(["dist", "ne", "n"], ascending=[True, False, False])
        r = g.iloc[0]
        out.append((ccy, r.day.strftime("%Y-%m-%d"), int(r.subaccount), int(r.block)))
    return out


def pm_account_case(chain: Chain, ccy: str, day: str, acc: int, block: int) -> dict:
    bts = chain.block_ts(block)
    pm = PM[ccy]
    names = ["spotFeed()", "stableFeed()", "forwardFeed()", "interestRateFeed()", "volFeed()", "lib()", "perp()",
             "option()", "baseAsset()"]
    res = chain.multicall([(pm, cd(n)) for n in names] + [(pm, cd("getScenarios()")), (pm, cd("maxExpiries()")),
                                                          (SUBACCOUNTS, cd("manager(uint256)", ["uint256"], [acc])),
                                                          (SUBACCOUNTS, cd("getAccountBalances(uint256)", ["uint256"],
                                                                           [acc]))], block)
    f = {n: addr(r[1]) for n, r in zip(names, res)}
    scen = decode([f"{SC}[]"], res[9][1])[0]
    max_exp = decode(["uint256"], res[10][1])[0]
    if addr(res[11][1]).lower() != pm.lower():
        raise RuntimeError("account not under the legacy PM at this block")
    balances = decode(["(address,uint256,int256)[]"], res[12][1])[0]
    lib = f["lib()"]
    res = chain.multicall([(lib, cd("getBasisContingencyParams()")), (lib, cd("getVolShockParams()")),
                           (lib, cd("getStaticDiscountParams()")), (lib, cd("getOtherContingencyParams()")),
                           (f["spotFeed()"], cd("getSpot()")), (f["stableFeed()"], cd("getSpot()")),
                           (f["perp()"], cd("getPerpPrice()")),
                           (f["perp()"], cd("getUnsettledAndUnrealizedCash(uint256)", ["uint256"], [acc]))], block)
    bc = decode(["uint256"] * 4, res[0][1])
    vs = decode(["uint256", "uint256", "int256", "int256", "uint256"], res[1][1])
    mp = decode(["uint256"] * 4, res[2][1])
    oc = decode(["uint256"] * 7, res[3][1])
    spot, spot_conf = decode(["uint256", "uint256"], res[4][1])
    stable, _ = decode(["uint256", "uint256"], res[5][1])
    perp_price, perp_conf = decode(["uint256", "uint256"], res[6][1])
    upnl = decode(["int256"], res[7][1])[0]
    params = {
        "BasisContingencyParameters": dict(zip(["scenarioSpotUp", "scenarioSpotDown", "basisContAddFactor",
                                                "basisContMultFactor"], map(f18, bc))),
        "VolShockParameters": {"volRangeUp": f18(vs[0]), "volRangeDown": f18(vs[1]), "shortTermPower": f18(vs[2]),
                               "longTermPower": f18(vs[3]), "dteFloor": float(vs[4])},
        "MarginParameters": dict(zip(["imFactor", "rateMultScale", "rateAddScale", "baseStaticDiscount"],
                                     map(f18, mp))),
        "OtherContingencyParameters": dict(zip(["pegLossThreshold", "pegLossFactor", "confThreshold", "confMargin",
                                                "basePercent", "perpPercent", "optionPercent"], map(f18, oc))),
        "scenarios": [{"spotShock": f18(s), "volShock": int(v)} for s, v in scen],
        "maxExpiries": int(max_exp),
    }
    options, cash, base, perp_q = [], 0.0, 0.0, 0.0
    for a, sub, bal in balances:
        a = a.lower()
        if a == CASH.lower():
            cash = f18(bal)
        elif a == f["option()"].lower():
            sub = int(sub)
            options.append((sub & 0xFFFFFFFF, ((sub >> 32) & 0x7FFFFFFFFFFFFFFF) * 10 ** 10, (sub >> 95) > 0,
                            int(bal)))
        elif a == f["perp()"].lower():
            perp_q = f18(bal)
        elif a == f["baseAsset()"].lower():
            base = f18(bal)
        else:
            raise RuntimeError(f"asset {a} not handled by the legacy PM")
    exps = sorted({o[0] for o in options})
    calls = []
    for e in exps:
        calls += [(f["forwardFeed()"], cd("getForwardPricePortions(uint64)", ["uint64"], [e])),
                  (f["interestRateFeed()"], cd("getInterestRate(uint64)", ["uint64"], [e]))]
    calls += [(f["volFeed()"], cd("getVol(uint128,uint64)", ["uint128", "uint64"], [k, e])) for e, k, _, _ in options]
    res = chain.multicall(calls, block)
    expiries = {}
    for i, e in enumerate(exps):
        fp = dec(["uint256"] * 3, res[2 * i])
        rt = dec(["int256", "uint256"], res[2 * i + 1])
        if fp is None or rt is None:
            raise RuntimeError(f"feed reverted for expiry {e}")
        expiries[str(e)] = {"fixed": f18(fp[0]), "var": f18(fp[1]), "fwd_conf": f18(fp[2]), "rate": f18(rt[0]),
                            "rate_conf": f18(rt[1])}
    vols = {}
    for (e, k, _, _), r in zip(options, res[2 * len(exps):]):
        v = dec(["uint256", "uint256"], r)
        if v is None:
            raise RuntimeError(f"getVol reverted for {e} {k}")
        vols[f"{e}|{k / E18!r}"] = [f18(v[0]), f18(v[1])]
    expect = {}
    for key, im in (("IM", True), ("MM", False)):
        ret = chain.call(pm, cd("getMargin(uint256,bool)", ["uint256", "bool"], [acc, im]), block)
        expect[key] = f18(decode(["int256"], ret)[0])
    ret = chain.call(pm, cd("getMarginAndMarkToMarket(uint256,bool,uint256)", ["uint256", "bool", "uint256"],
                            [acc, True, 0]), block)
    expect["mtm"] = f18(decode(["int256", "int256"], ret)[1])
    return {"ccy": ccy, "day": day, "block": block, "ts": bts, "manager": pm, "lib": lib,
            "account_hash": hashlib.sha256(str(acc).encode()).hexdigest()[:10], "params": params,
            "spot": f18(spot), "spot_conf": f18(spot_conf), "stable": f18(stable), "cash": cash, "base": base,
            "perp": ({"amount": perp_q, "price": f18(perp_price), "conf": f18(perp_conf), "upnl": f18(upnl)}
                     if perp_q != 0 else None),
            "options": [[e, k / E18, c, f18(q)] for e, k, c, q in options], "expiries": expiries, "vols": vols,
            **expect}


# ------------------------------------------------------------------------------------------------ driver

def run(kind: str, max_seconds: float) -> None:
    chain = Chain()
    t0 = time.time()
    if kind == "sm":
        path = OUT / "sm_chain_cases.json"
        doc = load(path)
        doc["source"] = ("StandardManager.getIsolatedMargin (SRM 0x28c9...5de5D) per eth_call at the block, inputs "
                         "from the SM market feeds (getMarketFeeds) and parameter getters at the same block")
        done = {(c["ccy"], c["day"]) for c in doc["cases"]}
        for ccy, day in SM_BLOCKS:
            if (ccy, day) in done:
                continue
            if time.time() - t0 > max_seconds:
                print("time budget reached")
                return
            doc["cases"].append(sm_case(chain, ccy, day))
            save(path, doc)
            print(ccy, day, len(doc["cases"][-1]["rows"]), "rows", flush=True)
    elif kind == "pm":
        path = OUT / "pm_chain_cases.json"
        doc = load(path)
        doc["source"] = ("legacy PMRMLib.addPrecomputes + getMarginAndMarkToMarket per eth_call at the block on "
                         "portfolios arranged like PMRM._arrangePortfolio from the legacy manager's feeds")
        done = {(c["ccy"], c["day"]) for c in doc["cases"]}
        for ccy, day in PM_BLOCKS:
            if (ccy, day) in done:
                continue
            if time.time() - t0 > max_seconds:
                print("time budget reached")
                return
            doc["cases"].append(pm_case(chain, ccy, day))
            save(path, doc)
            print(ccy, day, "ok", flush=True)
    elif kind == "accounts":
        PRIVATE.mkdir(parents=True, exist_ok=True)
        path = PRIVATE / "sm_chain_accounts.json"
        doc = load(path)
        doc["source"] = ("StandardManager.getMarginAndMarkToMarket(account, isInitial, 0) per eth_call for SM "
                         "accounts active in Paper 1 (SubAccounts.getAccountBalances), with every feed input; "
                         "account ids "
                         "stored only as sha256(str(id))[:10]")
        done = {c["day"] for c in doc["cases"]}
        for day in ACCOUNT_DAYS:
            if day in done:
                continue
            if time.time() - t0 > max_seconds:
                print("time budget reached")
                return
            block, bts, picked = find_accounts(chain, day)
            for n_opt, acc, bals in picked:
                try:
                    doc["cases"].append(account_case(chain, day, acc, block, bts,
                                                     [(a, int(s), int(b)) for a, s, b in bals]))
                    print(day, n_opt, "legs", flush=True)
                except RuntimeError as exc:
                    print(day, "account skipped:", exc, flush=True)
            if not picked:
                doc["cases"].append({"day": day, "skipped": "no SM account with 2 to 30 options"})
            save(path, doc)
    elif kind == "pm_accounts":
        PRIVATE.mkdir(parents=True, exist_ok=True)
        path = PRIVATE / "pm_chain_accounts.json"
        doc = load(path)
        doc["source"] = ("legacy PMRM.getMargin(account, isInitial) and getMarginAndMarkToMarket(account, true, 0) per "
                         "eth_call for legacy-PM maker accounts (chosen from data/p2/books/snapshots.parquet), with "
                         "every feed value and parameter at the same block; account ids stored only as "
                         "sha256(str(id))[:10]")
        done = {(c["ccy"], c["day"]) for c in doc["cases"]}
        for ccy, day, acc, block in pick_pm_accounts():
            if (ccy, day) in done:
                continue
            if time.time() - t0 > max_seconds:
                print("time budget reached")
                return
            try:
                doc["cases"].append(pm_account_case(chain, ccy, day, acc, block))
                print(ccy, day, len(doc["cases"][-1]["options"]), "options", flush=True)
            except RuntimeError as exc:
                doc["cases"].append({"ccy": ccy, "day": day, "skipped": str(exc)})
                print(ccy, day, "skipped:", exc, flush=True)
            save(path, doc)
    print("done")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["sm", "pm", "accounts", "pm_accounts"])
    ap.add_argument("--max-seconds", type=float, default=520.0)
    args = ap.parse_args()
    run(args.kind, args.max_seconds)
