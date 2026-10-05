from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

from derive_surface import p2ids
from derive_surface import p2params as pp

FIX = Path(__file__).parent / "fixtures" / "p2"


def _chain_fixture() -> dict:
    return json.loads((FIX / "params_chain_44810450.json").read_text())


def _raw(name: str) -> bytes:
    return bytes.fromhex(_chain_fixture()["single"][name][2:])


# --------------------------------------------------------------------------------------------
# Timeline
# --------------------------------------------------------------------------------------------

def _entries():
    return [
        {"from_block": 100, "from_ts": 1_000, "source": "event:A", "params": {"MarginParameters": {"imFactor": 1.0}}},
        {"from_block": 200, "from_ts": 1_200, "source": "event:B", "params": {"MarginParameters": {"imFactor": 1.5}}},
        {"from_block": 300, "from_ts": 1_400, "source": "bisection",
         "params": {"MarginParameters": {"imFactor": 1.5}, "scenarios": [{"spotShock": 1.1, "volShock": 1}]}},
    ]


def test_timeline_at_picks_last_entry_not_after_ts():
    tl = pp.Timeline("BTC", "pm", entries=_entries())
    assert tl.at(1_000)["MarginParameters"]["imFactor"] == 1.0
    assert tl.at(1_199)["MarginParameters"]["imFactor"] == 1.0
    assert tl.at(1_200)["MarginParameters"]["imFactor"] == 1.5
    assert tl.at(1_399)["MarginParameters"]["imFactor"] == 1.5 and "scenarios" not in tl.at(1_399)
    assert tl.at(10**10)["scenarios"][0]["volShock"] == 1
    assert tl.entry_at(1_250)["from_block"] == 200


def test_timeline_before_first_entry_raises_keyerror():
    tl = pp.Timeline("BTC", "pm", entries=_entries())
    with pytest.raises(KeyError):
        tl.at(999)
    with pytest.raises(KeyError):
        pp.Timeline("HYPE", "pm", entries=[]).at(2_000_000_000)


def test_timeline_unsorted_input_is_sorted():
    tl = pp.Timeline("BTC", "pm", entries=list(reversed(_entries())))
    assert [e["from_block"] for e in tl.entries] == [100, 200, 300]


def test_timeline_changes_and_key_filter():
    tl = pp.Timeline("BTC", "pm", entries=pp.mark_changes(_entries()))
    assert tl.changes() == [1_200, 1_400]
    assert tl.changes(keys=["scenarios"]) == [1_400]
    assert tl.changes(keys=["MarginParameters"]) == [1_200]


def test_timeline_json_roundtrip_keeps_all_keys(tmp_path):
    ent = pp.mark_changes(_entries())
    ent[0]["lib"] = "0x1a1b78af94c2a755b911a63345ac1410f65ad61b"
    ent[0]["params"]["CollateralParameters"] = {"0xabc": {"isEnabled": True, "isRiskCancelling": False,
                                                          "MMHaircut": 0.126, "IMHaircut": 0.014}}
    path = pp.Timeline("BTC", "pm2", entries=ent).save(root=tmp_path)
    assert path.name == "BTC_pm2.json"
    back = pp.Timeline("BTC", "pm2", root=tmp_path)
    assert back.entries == ent
    assert json.loads(path.read_text()) == ent


def test_timeline_path_for_override_lib(tmp_path):
    lib = "0x4E8EA8AFEB1F7583C3D1E27176D864FA652546C8"
    assert pp.Timeline.path("BTC", "pm2", lib=lib, root=tmp_path).name == "BTC_pm2_lib_4e8ea8af.json"


def test_mark_changes_merges_identical_consecutive_states():
    rows = [
        {"from_block": 1, "from_ts": 10, "source": "event:X", "params": {"a": {"x": 1.0}, "b": {"y": 2.0}}},
        {"from_block": 2, "from_ts": 12, "source": "event:Y", "params": {"a": {"x": 1.0}, "b": {"y": 2.0}}},
        {"from_block": 3, "from_ts": 14, "source": "event:Z", "params": {"a": {"x": 1.0}, "b": {"y": 3.0}}},
    ]
    out = pp.mark_changes(rows)
    assert [r["from_block"] for r in out] == [1, 3]
    assert out[0]["changed"] == ["a", "b"] and out[1]["changed"] == ["b"]
    assert out[0]["source"] == "event:X"  # later identical states do not create entries


# --------------------------------------------------------------------------------------------
# ABI decoding on real chain responses (block 44 810 450, 2026-09-17 10:55 UTC)
# --------------------------------------------------------------------------------------------

def test_decode_pm2_standard_lib_real_chain():
    raw = {
        "scenarios": _raw("pm2.getScenarios"), "maxExpiries": _raw("pm2.maxExpiries"),
        "getMarginParams": _raw("lib2.getMarginParams"), "getVolShockParams": _raw("lib2.getVolShockParams"),
        "getBasisContingencyParams": _raw("lib2.getBasisContingencyParams"),
        "getOtherContingencyParams": _raw("lib2.getOtherContingencyParams"),
        "getSkewShockParams": _raw("lib2.getSkewShockParams"),
    }
    p = pp.assemble_pm2(raw, {"0x7da2d398ddddfc946efd2c758c4688d21887790d": _raw("lib2.getCollateralParameters"),
                              "0x000000000000000000000000000000000000dead": b""})
    assert set(p) == {"VolShockParameters", "MarginParameters", "BasisContingencyParameters",
                      "OtherContingencyParameters", "SkewShockParameters", "CollateralParameters", "scenarios",
                      "maxExpiries"}
    assert p["MarginParameters"] == {"imFactor": 1.0, "mmFactor": 0.8, "shortRateMultScale": 0.0,
                                     "longRateMultScale": 0.0, "shortRateAddScale": 0.1, "longRateAddScale": 0.1,
                                     "shortBaseStaticDiscount": 1.02, "longBaseStaticDiscount": 0.98}
    assert p["VolShockParameters"] == {"volRangeUp": 0.4, "volRangeDown": 0.25, "shortTermPower": 0.3,
                                       "longTermPower": 0.13, "dteFloor": 86400.0, "minVolUpShock": 0.5}
    assert p["BasisContingencyParameters"] == {"scenarioSpotUp": 1.035, "scenarioSpotDown": 0.965,
                                               "basisContAddFactor": 0.5, "basisContMultFactor": 2.0}
    assert p["OtherContingencyParameters"]["confMargin"] == 0.4
    assert p["OtherContingencyParameters"]["IMOptionPercent"] == 0.001
    assert p["SkewShockParameters"]["linearCBase"] == -0.1 and p["SkewShockParameters"]["widthScale"] == 4.0
    assert p["maxExpiries"] == 16
    sc = p["scenarios"]
    assert len(sc) == 33 and sc[0] == {"spotShock": 1.14, "volShock": 1, "dampeningFactor": 1.0}
    grid = sorted({s["spotShock"] for s in sc if s["dampeningFactor"] == 1.0 and s["volShock"] < 3})
    assert grid[0] == 0.86 and grid[-1] == 1.14 and len(grid) == 9  # grid +-14 % since 20.08.2026
    tails = [s for s in sc if s["dampeningFactor"] < 1.0]
    assert len(tails) == 8 and max(s["spotShock"] for s in tails) == 6.0
    assert sorted(s["volShock"] for s in sc if s["volShock"] >= 3) == [3, 4]  # one Linear, one Abs
    assert p["CollateralParameters"] == {"0x7da2d398ddddfc946efd2c758c4688d21887790d": {
        "isEnabled": True, "isRiskCancelling": True, "MMHaircut": 0.126, "IMHaircut": 0.014}}


def test_decode_override_lib_mm_factor():
    m = pp.decode_struct(_raw("ovr.getMarginParams"), pp.PM2_STRUCTS["MarginParameters"][1])
    assert m["mmFactor"] == 0.35 and m["imFactor"] == 1.0


def test_decode_legacy_pm_real_chain():
    raw = {
        "scenarios": _raw("pm1.getScenarios"), "maxExpiries": _raw("pm1.maxExpiries"),
        "getStaticDiscountParams": _raw("lib1.getStaticDiscountParams"),
        "getVolShockParams": _raw("lib1.getVolShockParams"),
        "getBasisContingencyParams": _raw("lib1.getBasisContingencyParams"),
        "getOtherContingencyParams": _raw("lib1.getOtherContingencyParams"),
    }
    p = pp.assemble_pm(raw)
    assert set(p) == {"VolShockParameters", "MarginParameters", "BasisContingencyParameters",
                      "OtherContingencyParameters", "scenarios", "maxExpiries"}
    assert p["MarginParameters"] == {"imFactor": 1.25, "rateMultScale": 1.0, "rateAddScale": 0.12,
                                     "baseStaticDiscount": 0.95}
    assert p["VolShockParameters"] == {"volRangeUp": 0.5, "volRangeDown": 0.275, "shortTermPower": 0.3,
                                       "longTermPower": 0.13, "dteFloor": 86400.0}
    assert p["OtherContingencyParameters"] == {"pegLossThreshold": 0.99, "pegLossFactor": 4.0, "confThreshold": 0.55,
                                               "confMargin": 1.0, "basePercent": 0.03, "perpPercent": 0.03,
                                               "optionPercent": 0.015}
    assert p["maxExpiries"] == 18
    assert len(p["scenarios"]) == 23 and p["scenarios"][0] == {"spotShock": 1.18, "volShock": 1}
    grid = sorted({s["spotShock"] for s in p["scenarios"]})
    assert grid[0] == 0.82 and grid[-1] == 1.18 and len(grid) == 9


def test_decode_sm_real_chain_uses_getter_order():
    raw = {"optionMarginParams": _raw("srm.optionMarginParams"),
           "perpMarginRequirements": _raw("srm.perpMarginRequirements"),
           "baseMarginParams": _raw("srm.baseMarginParams"),
           "oracleContingencyParams": _raw("srm.oracleContingencyParams"), "depegParams": _raw("srm.depegParams")}
    p = pp.assemble_sm(raw)
    assert set(p) == {"OptionMarginParams", "PerpMarginRequirements", "BaseMarginParams", "OracleContingencyParams",
                      "DepegParams"}
    # getter order (IM before MM); the event OptionMarginParamsSet emits unpairedMM before unpairedIM
    assert p["OptionMarginParams"] == {"maxSpotReq": 0.15, "minSpotReq": 0.13, "mmCallSpotReq": 0.09,
                                       "mmPutSpotReq": 0.09, "MMPutMtMReq": 0.09, "unpairedIMScale": 1.2,
                                       "unpairedMMScale": 1.1, "mmOffsetScale": 1.05}
    assert p["PerpMarginRequirements"] == {"mmPerpReq": 0.05, "imPerpReq": 0.066}
    assert p["BaseMarginParams"] == {"marginFactor": 0.75, "IMScale": 0.93}
    assert p["OracleContingencyParams"] == {"perpThreshold": 0.55, "optionThreshold": 0.55, "baseThreshold": 0.55,
                                            "OCFactor": 1.0}
    assert p["DepegParams"] == {"threshold": 0.99, "depegFactor": 2.0}


def test_assemble_returns_none_without_code():
    empty = {k: b"" for k in ("optionMarginParams", "perpMarginRequirements", "baseMarginParams",
                              "oracleContingencyParams", "depegParams")}
    assert pp.assemble_sm(empty) is None


# --------------------------------------------------------------------------------------------
# Multicall3
# --------------------------------------------------------------------------------------------

def test_multicall_encoding_matches_abi_reference():
    fx = _chain_fixture()
    calls = [(c["to"], c["data"]) for c in fx["calls"]]
    assert pp.encode_aggregate3(calls) == fx["multicall_data"]
    dec = pp.decode_aggregate3(bytes.fromhex(fx["multicall_result"][2:]))
    assert [[ok, "0x" + ret.hex()] for ok, ret in dec] == fx["multicall_decoded"]
    assert [("0x" + ret.hex()) for _, ret in dec] == [fx["single"][c["name"]] for c in fx["calls"]]


class _FakeRpc:
    def __init__(self, fx):
        self.fx = fx
        self.calls = []

    def raw(self, method, params):
        self.calls.append((method, params))
        assert method == "eth_call" and params[0]["to"].lower() == pp.MULTICALL3.lower()
        return self.fx["multicall_result"]

    def eth_call(self, to, data, block, gas=None):
        self.calls.append(("single", to, data, block))
        for c in self.fx["calls"]:
            if c["to"] == to and c["data"] == data:
                return bytes.fromhex(self.fx["single"][c["name"]][2:])
        raise AssertionError("unexpected call")


def test_batch_call_multicall_after_deploy_single_before():
    fx = _chain_fixture()
    calls = [(c["to"], c["data"]) for c in fx["calls"]]
    rpc = _FakeRpc(fx)
    out = pp.batch_call(rpc, calls, fx["block"])
    assert len(rpc.calls) == 1 and out[-1] == b"" and out[0] == bytes.fromhex(fx["single"]["pm2.getScenarios"][2:])
    rpc2 = _FakeRpc(fx)
    out2 = pp.batch_call(rpc2, calls[:3], pp.MULTICALL3_BLOCK - 1)
    assert len(rpc2.calls) == 3 and all(c[0] == "single" for c in rpc2.calls)
    assert out2 == out[:3]


# --------------------------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------------------------

def _logs():
    return json.loads((FIX / "params_logs.json").read_text())


def test_decode_event_logs_real_chain():
    rows = {(x["key"], x["event"]): pp.decode_event(x["log"]) for x in _logs()}
    lo = rows[("BTC.PM2", "LibOverrideUpdated")]
    assert lo["event"] == "LibOverrideUpdated" and lo["account"] == 0x16a2e
    assert lo["lib"] == "0x4e8ea8afeb1f7583c3d1e27176d864fa652546c8" and lo["block"] == 44_968_136
    col = rows[("BTC.PM2", "CollateralParametersUpdated")]
    assert col["asset"] == "0xb0431da0c2293df9f0d96c3af9a5b8d547014608"
    assert rows[("BTC.PM2", "MarginParamsUpdated")]["event"] == "MarginParamsUpdated"
    assert rows[("BTC.PM2", "ScenariosUpdated")]["event"] == "ScenariosUpdated"
    assert rows[("BTC.PM", "ScenariosUpdated")]["event"] == "ScenariosUpdatedLegacy"
    om = rows[("SRM", "OptionMarginParamsSet")]
    assert om["event"] == "OptionMarginParamsSet" and om["market"] == 2 and om["block"] == 843_078
    oc = rows[("SRM", "OracleContingencySet")]
    assert oc["event"] == "OracleContingencySet" and oc.get("market") is None


class _LogRpc:
    """eth_getLogs fake that refuses ranges wider than ``max_span`` like a node with a range limit."""

    def __init__(self, logs, max_span):
        self.logs, self.max_span, self.requests = logs, max_span, 0

    def raw(self, method, params):
        from derive_surface.chainfeeds import RpcError

        self.requests += 1
        flt = params[0]
        lo, hi = int(flt["fromBlock"], 16), int(flt["toBlock"], 16)
        if hi - lo > self.max_span:
            raise RpcError({"code": -32005, "message": "query returned more than 10000 results"})
        return [L for L in self.logs if lo <= int(L["blockNumber"], 16) <= hi]


def test_fetch_logs_splits_on_error_and_keeps_order():
    logs = [x["log"] for x in _logs()]
    rpc = _LogRpc(logs, max_span=20_000_000)
    got = pp.fetch_logs(rpc, ["0x1"], [pp.TOPICS["MarginParamsUpdated"]], 0, 45_000_000)
    assert sorted(int(L["blockNumber"], 16) for L in got) == sorted(int(L["blockNumber"], 16) for L in logs)
    assert rpc.requests > 1


# --------------------------------------------------------------------------------------------
# Change detection for the legacy PM (no events): samples + bisection
# --------------------------------------------------------------------------------------------

def test_find_changes_bisects_every_visible_change():
    def state(b):
        return "A" if b < 137 else "B" if b < 500 else "C" if b < 501 else "D"

    calls = []

    def fn(b):
        calls.append(b)
        return state(b)

    assert pp.find_changes(fn, [0, 1_000]) == [137, 500, 501]
    assert pp.find_changes(fn, [0, 137, 1_000]) == [137, 500, 501]
    assert pp.find_changes(fn, [0, 100]) == []


def test_find_changes_misses_revert_between_samples_but_denser_samples_catch_it():
    def state(b):
        return "B" if 300 <= b < 400 else "A"

    assert pp.find_changes(state, [0, 1_000]) == []
    assert pp.find_changes(state, [0, 350, 1_000]) == [300, 400]


def test_day_blocks_are_first_block_of_utc_day():
    days = pp.day_blocks(pp.block_at_ts(1_704_931_201), pp.block_at_ts(1_704_931_201 + 2 * 86_400))
    assert days[0] == 2_454_793 and days[1] - days[0] == 43_200 and len(days) == 3


def test_month_blocks():
    mb = pp.month_blocks(2_454_793, pp.block_at_ts(1_709_251_201 + 10))  # 2024-01-11 .. 2024-03-01
    assert [pp.ts_at_block(b) for b in mb] == [1_706_745_601, 1_709_251_201]  # 2024-02-01, 2024-03-01 00:00:01


# --------------------------------------------------------------------------------------------
# Account lib overrides (accounts only as p2ids label in results/)
# --------------------------------------------------------------------------------------------

LAB = p2ids.Labeler([5, 7], bytes(range(32)))  # 5 -> M1, 7 -> M2, everything else X + HMAC


def test_overrides_are_labelled_and_resolved_by_time():
    events = [
        {"event": "LibOverrideUpdated", "block": 1_000, "log_index": 0, "account": 92718, "lib": "0xAbC"},
        {"event": "LibOverrideUpdated", "block": 2_000, "log_index": 1, "account": 92718,
         "lib": "0x0000000000000000000000000000000000000000"},
        {"event": "LibOverrideUpdated", "block": 1_500, "log_index": 0, "account": 5, "lib": "0xdef"},
    ]
    rows = pp.overrides_from_events(events, label=LAB.label)
    assert rows[0] == {"account": LAB.label(92718), "lib": "0xabc", "from_block": 1_000,
                       "from_ts": pp.ts_at_block(1_000)}
    assert rows[0]["account"].startswith("X") and rows[1]["account"] == "M1"
    assert hashlib.sha256(b"92718").hexdigest()[:10] not in json.dumps(rows)
    assert rows[-1]["lib"] is None and rows[-1]["from_block"] == 2_000


def test_overrides_default_to_the_p2ids_label(monkeypatch):
    monkeypatch.setattr(p2ids, "label", LAB.label)
    ev = [{"event": "LibOverrideUpdated", "block": 1_000, "log_index": 0, "account": 7, "lib": "0xabc"}]
    rows = pp.overrides_from_events(ev)
    assert rows[0]["account"] == "M2"


def _raw_overrides():
    return [{"account": 92718, "lib": "0xAbC", "from_block": 1_000, "from_ts": pp.ts_at_block(1_000)},
            {"account": 5, "lib": "0xdef", "from_block": 1_500, "from_ts": pp.ts_at_block(1_500)},
            {"account": 92718, "lib": pp.ZERO_ADDRESS, "from_block": 2_000, "from_ts": pp.ts_at_block(2_000)}]


def test_account_lib_resolves_raw_ids_by_time():
    raw = list(reversed(_raw_overrides()))  # input order does not matter, rows are ordered by time
    t = pp.ts_at_block
    assert pp.account_lib(raw, 92718, t(999)) is None
    assert pp.account_lib(raw, 92718, t(1_000)) == "0xabc"  # lower case
    assert pp.account_lib(raw, 92718, t(1_999)) == "0xabc"
    assert pp.account_lib(raw, 92718, t(2_000)) is None  # zero address: standard lib again
    assert pp.account_lib(raw, 5, t(1_600)) == "0xdef"
    assert pp.account_lib(raw, "5", t(1_600)) == "0xdef"  # a raw id as digit string (as in some frames)
    assert pp.account_lib(raw, 6, t(1_600)) is None


def test_account_lib_does_not_call_the_labeler(monkeypatch):
    def boom(_):
        raise AssertionError("account_lib must not depend on p2ids.label")

    monkeypatch.setattr(p2ids, "label", boom)
    assert pp.account_lib(_raw_overrides(), 5, pp.ts_at_block(1_600)) == "0xdef"


def test_account_lib_refuses_labelled_rows():
    """Labelled rows (results/ export) are no key: the label of an id changes with the maker ranking."""
    rows = pp.overrides_from_raw(_raw_overrides(), label=LAB.label)
    with pytest.raises(ValueError, match="raw"):
        pp.account_lib(rows, 5, pp.ts_at_block(1_600))
    with pytest.raises(ValueError):
        pp.account_lib(rows, 6, pp.ts_at_block(1_600))  # also when no row would match
    with pytest.raises(ValueError):
        pp.account_lib(_raw_overrides(), "M1", pp.ts_at_block(1_600))  # a label as account id


def test_load_overrides_reads_the_raw_file(tmp_path):
    raw = list(reversed(_raw_overrides()))
    (tmp_path / "BTC_pm2_overrides_raw.json").write_text(json.dumps(raw))
    rows = pp.load_overrides("BTC", data_dir=tmp_path)
    assert [(r["account"], r["lib"], r["from_block"]) for r in rows] == [
        (92718, "0xabc", 1_000), (5, "0xdef", 1_500), (92718, None, 2_000)]
    assert all(type(r["account"]) is int for r in rows)
    with pytest.raises(FileNotFoundError):  # no silent fallback to the labelled export
        pp.load_overrides("ETH", data_dir=tmp_path)


def test_overrides_from_raw_match_overrides_from_events():
    raw = _raw_overrides()
    ev = [{"event": "LibOverrideUpdated", "block": r["from_block"], "log_index": 0, "account": r["account"],
           "lib": r["lib"]} for r in raw]
    assert pp.overrides_from_raw(raw, label=LAB.label) == pp.overrides_from_events(ev, label=LAB.label)


def test_relabel_rewrites_hashed_overrides_without_rpc(tmp_path):
    data, out = tmp_path / "data", tmp_path / "out"
    data.mkdir()
    out.mkdir()
    raw = _raw_overrides()
    (data / "BTC_pm2_overrides_raw.json").write_text(json.dumps(raw))
    old = [{"account": hashlib.sha256(str(r["account"]).encode()).hexdigest()[:10],
            "lib": None if r["lib"] == pp.ZERO_ADDRESS else r["lib"].lower(),
            "from_block": r["from_block"], "from_ts": r["from_ts"]} for r in raw]
    (out / "BTC_pm2_overrides.json").write_text(json.dumps(old))
    res = pp.relabel_overrides(data_dir=data, out_dir=out, ccys=("BTC",), label=LAB.label)
    new = json.loads((out / "BTC_pm2_overrides.json").read_text())
    assert [r["account"] for r in new] == [LAB.label(92718), "M1", LAB.label(92718)]
    assert [(r["lib"], r["from_block"], r["from_ts"]) for r in new] == [(r["lib"], r["from_block"], r["from_ts"])
                                                                         for r in old]
    assert res == {"BTC": 3}
    # a file that does not describe the same events is not overwritten
    (out / "BTC_pm2_overrides.json").write_text(json.dumps(old[:2]))
    with pytest.raises(ValueError):
        pp.relabel_overrides(data_dir=data, out_dir=out, ccys=("BTC",), label=LAB.label)
    assert json.loads((out / "BTC_pm2_overrides.json").read_text()) == old[:2]
    # an unsalted hash that does not belong to the raw account is refused as well
    bad = [dict(r) for r in old]
    bad[1]["account"] = hashlib.sha256(b"6").hexdigest()[:10]
    (out / "BTC_pm2_overrides.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        pp.relabel_overrides(data_dir=data, out_dir=out, ccys=("BTC",), label=LAB.label)


# --------------------------------------------------------------------------------------------
# Loader: end block (--to-block) and log caches, offline with a fake RPC
# --------------------------------------------------------------------------------------------

class FakeRpc:
    def __init__(self, head: int = 999, logs=()):
        self.head, self.logs, self.calls = head, list(logs), []

    def raw(self, method, params):
        self.calls.append(method)
        if method == "eth_blockNumber":
            return hex(self.head)
        if method == "eth_getLogs":
            f = params[0]
            lo, hi = int(f["fromBlock"], 16), int(f["toBlock"], 16)
            addrs = {a.lower() for a in f["address"]}
            topics = {t.lower() for t in f["topics"][0]}
            return [L for L in self.logs if lo <= int(L["blockNumber"], 16) <= hi
                    and L["address"].lower() in addrs and L["topics"][0].lower() in topics]
        raise AssertionError(method)


def _log(block: int, address: str = pp.SRM, event: str = "OptionMarginParamsSet") -> dict:
    return {"blockNumber": hex(block), "address": address, "topics": [pp.TOPICS[event]], "data": "0x",
            "logIndex": "0x0", "transactionHash": "0x" + f"{block:064x}"}


def _meta(d: Path) -> dict:
    return json.loads((d / "meta.json").read_text())


def test_loader_to_block_overrides_the_stored_end_block(tmp_path):
    (tmp_path / "meta.json").write_text(json.dumps({"to_block": 100}))
    rpc = FakeRpc()
    ld = pp.Loader(rpc, data_dir=tmp_path, out_dir=tmp_path / "out", to_block=200)
    assert ld.to_block == 200 and _meta(tmp_path)["to_block"] == 200
    assert pp.Loader(rpc, data_dir=tmp_path, out_dir=tmp_path / "out").to_block == 200  # resumed run
    assert rpc.calls == []


def test_loader_without_meta_or_to_block_uses_the_chain_head(tmp_path):
    rpc = FakeRpc(head=999)
    assert pp.Loader(rpc, data_dir=tmp_path, out_dir=tmp_path / "out").to_block == 999
    assert rpc.calls == ["eth_blockNumber"] and _meta(tmp_path)["to_block"] == 999


def test_log_caches_follow_a_new_end_block(tmp_path):
    topics = [pp.TOPICS["OptionMarginParamsSet"]]
    logs = [_log(150), _log(250)]
    rpc = FakeRpc(logs=logs)
    # state after the first A2 run: plain list cache that covers blocks up to meta.to_block = 200
    (tmp_path / "meta.json").write_text(json.dumps({"to_block": 200}))
    (tmp_path / "logs_srm.json").write_text(json.dumps([logs[0]]))
    ld = pp.Loader(rpc, data_dir=tmp_path, out_dir=tmp_path / "out")
    assert ld._logs_cached("srm", [pp.SRM], topics, 100) == [logs[0]] and rpc.calls == []
    ld = pp.Loader(rpc, data_dir=tmp_path, out_dir=tmp_path / "out", to_block=300)
    got = ld._logs_cached("srm", [pp.SRM], topics, 100)
    assert [int(L["blockNumber"], 16) for L in got] == [150, 250] and "eth_getLogs" in rpc.calls
    n = len(rpc.calls)
    again = pp.Loader(rpc, data_dir=tmp_path, out_dir=tmp_path / "out")
    assert again.to_block == 300 and again._logs_cached("srm", [pp.SRM], topics, 100) == got
    assert len(rpc.calls) == n


def test_interrupted_run_does_not_take_an_old_cache_for_the_new_end_block(tmp_path):
    topics = [pp.TOPICS["OptionMarginParamsSet"]]
    logs = [_log(150), _log(250)]
    rpc = FakeRpc(logs=logs)
    (tmp_path / "meta.json").write_text(json.dumps({"to_block": 200}))
    (tmp_path / "logs_srm.json").write_text(json.dumps([logs[0]]))
    pp.Loader(rpc, data_dir=tmp_path, out_dir=tmp_path / "out", to_block=300)  # stops before any download
    ld = pp.Loader(rpc, data_dir=tmp_path, out_dir=tmp_path / "out")  # next call without --to-block
    assert ld.to_block == 300
    assert [int(L["blockNumber"], 16) for L in ld._logs_cached("srm", [pp.SRM], topics, 100)] == [150, 250]


def test_log_cache_is_refetched_when_the_filter_changes(tmp_path):
    lib_a, lib_b = "0x" + "a" * 40, "0x" + "b" * 40
    topics = [pp.TOPICS["MarginParamsUpdated"]]
    logs = [_log(150, lib_a, "MarginParamsUpdated"), _log(160, lib_b, "MarginParamsUpdated")]
    rpc = FakeRpc(logs=logs)
    ld = pp.Loader(rpc, data_dir=tmp_path, out_dir=tmp_path / "out", to_block=300)
    assert ld._logs_cached("override_libs", [lib_a], topics, 100) == [logs[0]]
    n = len(rpc.calls)
    assert ld._logs_cached("override_libs", [lib_a], topics, 100) == [logs[0]] and len(rpc.calls) == n
    assert ld._logs_cached("override_libs", [lib_a, lib_b], topics, 100) == logs and len(rpc.calls) > n


def test_cli_load_passes_to_block_and_relabel_needs_no_rpc(monkeypatch, capsys):
    seen = {}

    class FakeLoader:
        def __init__(self, rpc, to_block=None, deadline=None, **kw):
            seen["to_block"] = to_block

        def run(self):
            return {"to_block": seen["to_block"]}

    monkeypatch.setattr(pp, "Loader", FakeLoader)
    monkeypatch.setattr(pp, "Rpc", lambda **kw: object())
    assert pp.main(["load", "--to-block", "45500000", "--max-seconds", "5"]) == 0
    assert seen["to_block"] == 45_500_000 and "DONE" in capsys.readouterr().out
    monkeypatch.setattr(pp, "relabel_overrides", lambda: {"BTC": 15})
    monkeypatch.setattr(pp, "Rpc", lambda **kw: pytest.fail("relabel must not open an RPC client"))
    assert pp.main(["relabel"]) == 0
    assert '"BTC": 15' in capsys.readouterr().out


def test_lower_end_block_cuts_cached_logs(tmp_path):
    topics = [pp.TOPICS["OptionMarginParamsSet"]]
    rpc = FakeRpc(logs=[_log(150), _log(250)])
    pp.Loader(rpc, data_dir=tmp_path, out_dir=tmp_path / "out", to_block=300)._logs_cached("srm", [pp.SRM], topics, 1)
    ld = pp.Loader(rpc, data_dir=tmp_path, out_dir=tmp_path / "out", to_block=200)
    assert [int(L["blockNumber"], 16) for L in ld._logs_cached("srm", [pp.SRM], topics, 1)] == [150]


# --------------------------------------------------------------------------------------------
# Snapshot store (resumable downloads)
# --------------------------------------------------------------------------------------------

def test_snapshot_store_roundtrip(tmp_path):
    st = pp.SnapshotStore(tmp_path)
    st.put(123, "BTC/pm", {"a": {"x": 1.0}})
    st.put(124, "BTC/pm", None)
    st2 = pp.SnapshotStore(tmp_path)
    assert st2.has(123, "BTC/pm") and st2.get(123, "BTC/pm") == {"a": {"x": 1.0}}
    assert st2.has(124, "BTC/pm") and st2.get(124, "BTC/pm") is None
    assert not st2.has(125, "BTC/pm")


# --------------------------------------------------------------------------------------------
# Manager share of option OI
# --------------------------------------------------------------------------------------------

def test_manager_oi_share():
    oi = {"oi": {
        "BTC.SM": [{"month": "2024-01", "oi": 30.0}, {"month": "2024-02", "oi": 0.0}, {"month": "head", "oi": 5.0}],
        "BTC.PM": [{"month": "2024-01", "oi": 10.0}, {"month": "2024-02", "oi": 0.0}, {"month": "head", "oi": 5.0}],
        "BTC.PM2": [{"month": "2024-01", "oi": 0.0}, {"month": "2024-02", "oi": 0.0}, {"month": "head", "oi": 0.0}],
        "HYPE.SM": [{"month": "2024-01", "oi": None}, {"month": "2024-02", "oi": 1.0}],
        "HYPE.PM2": [{"month": "2024-01", "oi": None}, {"month": "2024-02", "oi": 3.0}],
    }}
    df = pp.manager_oi_share(oi)
    assert list(df.columns) == ["month", "ccy", "sm", "pm", "pm2"]
    btc = df[df.ccy == "BTC"].set_index("month")
    assert list(btc.index) == ["2024-01"]  # months without OI and the head row are dropped
    assert btc.loc["2024-01", "sm"] == 0.75 and btc.loc["2024-01", "pm"] == 0.25 and btc.loc["2024-01", "pm2"] == 0.0
    hype = df[df.ccy == "HYPE"].set_index("month")
    assert list(hype.index) == ["2024-02"] and math.isnan(hype.loc["2024-02", "pm"])
    assert hype.loc["2024-02", "pm2"] == 0.75


# --------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------

def test_selectors_and_topics_match_keccak():
    keccak = pytest.importorskip("eth_hash.auto").keccak
    for sig, sel in pp.SELECTOR_SIGNATURES.items():
        assert sel == "0x" + keccak(sig.encode()).hex()[:8], sig
    for name, sig in pp.TOPIC_SIGNATURES.items():
        assert pp.TOPICS[name] == "0x" + keccak(sig.encode()).hex(), sig


# --------------------------------------------------------------------------------------------
# Account view and change description
# --------------------------------------------------------------------------------------------

def test_pm2_params_for_account_uses_override_lib(tmp_path):
    std = [{"from_block": 10, "from_ts": 100, "source": "start", "lib": "0xstd",
            "params": {"MarginParameters": {"mmFactor": 0.8}}}]
    ovr = [{"from_block": 20, "from_ts": 200, "source": "start", "lib": "0x4e8ea8afeb",
            "params": {"MarginParameters": {"mmFactor": 0.35}}}]
    pp.Timeline("BTC", "pm2", entries=std).save(root=tmp_path)
    pp.Timeline("BTC", "pm2", lib="0x4e8ea8afeb", entries=ovr).save(root=tmp_path)
    raw = [{"account": 7, "lib": "0x4E8EA8AFEB", "from_block": 30, "from_ts": 300}]
    (tmp_path / "BTC_pm2_overrides_raw.json").write_text(json.dumps(raw))
    at = lambda acc, ts: pp.pm2_params_for_account("BTC", acc, ts, root=tmp_path, data_dir=tmp_path)  # noqa: E731
    assert at(7, 250)["MarginParameters"]["mmFactor"] == 0.8
    assert at(7, 300)["MarginParameters"]["mmFactor"] == 0.35
    assert at(8, 300)["MarginParameters"]["mmFactor"] == 0.8


LIB_A, LIB_B = "0xaaaaaaaa11", "0xbbbbbbbb22"


def _two_lib_world(tmp_path):
    """Standard lib (mmFactor 0.8), lib A (0.35) for account 5 and lib B (0.5) for account 7, both from ts 300."""
    data, out = tmp_path / "data", tmp_path / "out"
    data.mkdir()
    out.mkdir()
    for lib, mm in ((None, 0.8), (LIB_A, 0.35), (LIB_B, 0.5)):
        pp.Timeline("BTC", "pm2", lib=lib, entries=[{"from_block": 10, "from_ts": 100, "source": "start",
                                                     "params": {"MarginParameters": {"mmFactor": mm}}}]).save(root=out)
    raw = [{"account": 5, "lib": LIB_A, "from_block": 30, "from_ts": 300},
           {"account": 7, "lib": LIB_B, "from_block": 30, "from_ts": 300}]
    (data / "BTC_pm2_overrides_raw.json").write_text(json.dumps(raw))
    return data, out, raw


def test_changed_ranking_does_not_silently_switch_the_lib(tmp_path, monkeypatch):
    """Review of B0: the lib of an account must not follow its rank-dependent label.

    The export in ``out`` was labelled under the ranking [5, 7] (5 = M1, 7 = M2). Under the new ranking [7, 5],
    account 7 is M1, and a lookup through the label would return lib A of the old M1. The resolution goes through
    the raw ids and keeps 5 -> A, 7 -> B under both rankings (and with a stale or missing export).
    """
    data, out, raw = _two_lib_world(tmp_path)
    old_rank = p2ids.Labeler([5, 7], bytes(range(32)))
    new_rank = p2ids.Labeler([7, 5], bytes(range(32)))
    stale = pp.overrides_from_raw(raw, label=old_rank.label)
    (out / "BTC_pm2_overrides.json").write_text(json.dumps(stale))
    # the scenario is a real trap: under the new ranking the label of 7 points at the row of lib A
    assert new_rank.label(7) == "M1" and [r["lib"] for r in stale if r["account"] == "M1"] == [LIB_A]

    for lab in (old_rank, new_rank):
        monkeypatch.setattr(p2ids, "label", lab.label)
        mm = {acc: pp.pm2_params_for_account("BTC", acc, 300, root=out, data_dir=data)["MarginParameters"]["mmFactor"]
              for acc in (5, 7, 8)}
        assert mm == {5: 0.35, 7: 0.5, 8: 0.8}
        rows = pp.load_overrides("BTC", data_dir=data)
        assert pp.account_lib(rows, 5, 300) == LIB_A and pp.account_lib(rows, 7, 300) == LIB_B
    (out / "BTC_pm2_overrides.json").unlink()  # the export is not read at all
    assert pp.pm2_params_for_account("BTC", 7, 300, root=out, data_dir=data)["MarginParameters"]["mmFactor"] == 0.5


def test_books_pm2_params_resolves_through_raw_ids(tmp_path, monkeypatch):
    """``books._Pm2Params`` (B3/B4) calls ``load_overrides(ccy, root)`` and ``account_lib`` with the raw id."""
    books = pytest.importorskip("derive_surface.books")
    data, out, raw = _two_lib_world(tmp_path)
    monkeypatch.setattr(pp, "DATA_DIR", data)
    monkeypatch.setattr(pp, "PARAMS_DIR", out)
    monkeypatch.setattr(p2ids, "label", p2ids.Labeler([7, 5], bytes(range(32))).label)
    prm = books._Pm2Params()
    assert prm.lib("BTC", 5, 300) == LIB_A and prm.lib("BTC", 7, 300) == LIB_B and prm.lib("BTC", 7, 299) is None
    params, lib = prm.account("BTC", 7, 300)
    assert lib == LIB_B and params["MarginParameters"]["mmFactor"] == 0.5


def _sc(grid, tail_damp):
    out = [{"spotShock": s, "volShock": v, "dampeningFactor": 1.0} for s in grid for v in (0, 1, 2)]
    out += [{"spotShock": 3.0, "volShock": 1, "dampeningFactor": tail_damp}]
    return out


def test_describe_change_names_grid_and_tail_changes():
    a = {"scenarios": _sc([0.83, 1.0, 1.17], 0.02), "maxExpiries": 14}
    b = {"scenarios": _sc([0.86, 1.0, 1.14], 0.02), "maxExpiries": 16}
    c = {"scenarios": _sc([0.86, 1.0, 1.14], 0.01), "maxExpiries": 16}
    assert pp.describe_change(None, a) == "Start"
    d = pp.describe_change(a, b)
    assert "±17 %→±14 %" in d and "maxExpiries 14→16" in d
    assert "tail dampening" in pp.describe_change(b, c)
