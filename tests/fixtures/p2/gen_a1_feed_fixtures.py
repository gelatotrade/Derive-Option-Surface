"""Regenerate the A1 feed fixtures (not collected by pytest; needs network, eth_abi from the system for the multicall
reference encoding, no package dependency). Run from the repo root:

    python3 tests/fixtures/p2/gen_a1_feed_fixtures.py

feeds_btc_settlement.json: real BTC feed logs in the 200 blocks up to block B = 10 min before the 2026-09-11 08:00 UTC
expiry (inside the 30-min settlement window) plus the eth_call results of getSpot, getForwardPrice(Portions),
getInterestRate (PM2 rate feed) and getPerpPrice at B, and the one event of the static legacy-PM rate feed.
feeds_multicall_btc.json: a Multicall3.aggregate3 call at B (calldata encoded with eth_abi) and its raw response.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from derive_surface.p2chain import Rpc, block_at_ts, ts_at_block  # noqa: E402

OUT = Path("tests/fixtures/p2")
rpc = Rpc(rate=2.0, log_path="data/p2/logs/A1.jsonl")
T_SPOT = "0xbd86cbf2ccd8e501428ca22429126186e6ed6c5287f2be73152c58bae94f4183"
T_FWD = "0x9f896aba44d86664403ab1344cde140b477c830d6ceda60ae36c1e7132fd2686"
T_RATE = "0xf00d73eebf231f5bfbe60b1882b53b782160a5c8c38e1f1cb26470fdde355768"
T_DIFF = "0x248fe0fb2a38847211f28b18cd0417aa0a9b2259a16e92e793ba97887eb5d951"
T_STATIC = "0x203d3e59e9d6dd4310ba6d0a2b518dea62d541573ba6f674aec647220186c946"
BTC = dict(spot="0x5eb59391e7870807ad2c8792e8c5e75838e0fdb0", forward="0x958c54bfacc0e2dee586564b31bf3f171f256279",
           rate_pm2="0x37d299d9d83186b6043e68c00d58b1f59c965461", rate_pm="0x6fef1bb8ade9a836663d4c15afd5985fb545004f",
           perp="0x34bc7fe1965b4e9f4071b69f2e60b8dc88f34475", perp_asset="0xDBa83C0C654DB1cd914FA2710bA743e925B53086")
E = 1789113600   # 2026-09-11 08:00 UTC
E2 = 1790928000  # 2026-10-02 08:00 UTC
B = block_at_ts(E - 600)
LO = B - 200


def word(x: int) -> str:
    return x.to_bytes(32, "big").hex()


def logs(addr, topics, lo=LO, hi=B):
    return rpc.raw("eth_getLogs", [{"address": addr, "topics": topics, "fromBlock": hex(lo), "toBlock": hex(hi)}])


def call(to, data):
    try:
        return rpc.raw("eth_call", [{"to": to, "data": data}, hex(B)])
    except Exception as exc:  # recorded as text, the tests expect successful calls
        return "ERR " + str(exc)


def settlement_fixture() -> dict:
    out = {"block": B, "block_ts": ts_at_block(B), "expiry": E, "expiry_far": E2, "addresses": BTC,
           "spot": logs(BTC["spot"], [T_SPOT]),
           "forward": logs(BTC["forward"], [T_FWD, "0x" + word(E)]),
           "rate_pm2": logs(BTC["rate_pm2"], [T_RATE, "0x" + word(E)]),
           "perp": logs(BTC["perp"], [T_DIFF]),
           "forward_far": logs(BTC["forward"], [T_FWD, "0x" + word(E2)]),
           "rate_far": logs(BTC["rate_pm2"], [T_RATE, "0x" + word(E2)]),
           "rate_pm": logs(BTC["rate_pm"], [T_STATIC], 843_000, 844_000)}
    out["eth_call"] = {
        "getSpot": call(BTC["spot"], "0x2b37269c"),
        "getForwardPricePortions": call(BTC["forward"], "0x80f1d266" + word(E)),
        "getForwardPrice": call(BTC["forward"], "0xb34f2e36" + word(E)),
        "getInterestRate": call(BTC["rate_pm2"], "0xb0487ff6" + word(E)),
        "getPerpPrice": call(BTC["perp_asset"], "0x90f76b18"),
        "getForwardPricePortions_far": call(BTC["forward"], "0x80f1d266" + word(E2)),
        "getInterestRate_far": call(BTC["rate_pm2"], "0xb0487ff6" + word(E2)),
    }
    return out


def multicall_fixture() -> dict:
    from eth_abi import decode, encode

    mc = "0xcA11bde05977b3631167028862bE2a173976CA11"
    calls = [(BTC["spot"], True, bytes.fromhex("2b37269c")),
             (BTC["forward"], True, bytes.fromhex("b34f2e36" + word(E))),
             (BTC["forward"], True, bytes.fromhex("b34f2e36" + word(1234567890))),  # missing expiry: reverts
             (BTC["rate_pm2"], True, bytes.fromhex("b0487ff6" + word(E2))),
             (BTC["perp_asset"], True, bytes.fromhex("90f76b18"))]
    data = "0x82ad56cb" + encode(["(address,bool,bytes)[]"], [calls]).hex()
    res = rpc.raw("eth_call", [{"to": mc, "data": data}, hex(B)])
    (dec,) = decode(["(bool,bytes)[]"], bytes.fromhex(res[2:]))
    return {"block": B, "multicall": mc,
            "calls": [{"target": t, "allow_failure": f, "data": "0x" + c.hex()} for t, f, c in calls],
            "calldata": data, "response": res, "decoded": [{"success": s, "data": "0x" + r.hex()} for s, r in dec]}


if __name__ == "__main__":
    (OUT / "feeds_btc_settlement.json").write_text(json.dumps(settlement_fixture(), indent=1))
    (OUT / "feeds_multicall_btc.json").write_text(json.dumps(multicall_fixture(), indent=1))
