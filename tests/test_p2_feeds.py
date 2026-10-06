from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from derive_surface import p2feeds as pf
from derive_surface.chainfeeds import RpcError
from derive_surface.p2chain import ts_at_block

FIX = Path(__file__).parent / "fixtures" / "p2"
SETTLE = json.loads((FIX / "feeds_btc_settlement.json").read_text())
MC = json.loads((FIX / "feeds_multicall_btc.json").read_text())


def words(hexdata: str):
    h = hexdata[2:]
    return [int(h[i:i + 64], 16) for i in range(0, len(h), 64)]


def signed(x: int) -> int:
    return x - (1 << 256) if x >= (1 << 255) else x


# ---------------------------------------------------------------- topics and addresses

def test_topics_are_keccak_of_event_signatures():
    # keccak256 of the signatures, computed once with eth_hash and checked against real logs (fixtures)
    assert pf.SPOT_PRICE_UPDATED == SETTLE["spot"][0]["topics"][0]
    assert pf.FORWARD_DATA_UPDATED == SETTLE["forward"][0]["topics"][0]
    assert pf.RATE_UPDATED == SETTLE["rate_pm2"][0]["topics"][0]
    assert pf.SPOT_DIFF_UPDATED == SETTLE["perp"][0]["topics"][0]
    assert pf.STATIC_RATE_UPDATED == SETTLE["rate_pm"][0]["topics"][0]
    assert set(pf.TOPICS) == {"spot", "forward", "rate_pm2", "rate_pm", "perp"}


def test_feed_addresses():
    btc = pf.FEEDS["BTC"]
    for kind in ("spot", "forward", "rate_pm2", "rate_pm", "perp"):
        assert btc[kind] == SETTLE["addresses"][kind].lower()
    assert btc["vol"] == "0x388341d9e5a7d7d5accd738b2a31b0622e0c1b87"
    assert pf.FEEDS["HYPE"]["rate_pm"] is None
    assert pf.FEEDS["HYPE"]["perp"] == "0x947eb7b730eaf6a76dd7374eb443e6c5fc51503b"
    for ccy in ("BTC", "ETH", "HYPE"):
        for kind in ("spot", "forward", "rate_pm2", "perp"):
            assert pf.FEEDS[ccy]["deploy"][kind] > 800_000
    # the load reaches the end of the Paper 1 load, cut-off 30.09.2026 08:00 UTC + 25 h (block 45 411 792)
    from derive_surface import markouts, p2chain
    assert pf.TO_BLOCK >= p2chain.block_at_ts((markouts.FINAL_CUTOFF_MS + markouts.LOAD_BUFFER_MS) // 1000)


# ---------------------------------------------------------------- decoding real logs

def test_decode_spot_log():
    entry = SETTLE["spot"][-1]
    row = pf.decode_log("spot", entry)
    w = words(entry["data"])
    assert row["block"] == int(entry["blockNumber"], 16)
    assert row["block_ts"] == int(entry["blockTimestamp"], 16) == ts_at_block(row["block"])
    assert row["log_index"] == int(entry["logIndex"], 16)
    assert row["expiry"] == 0
    assert row["value"] == w[0] / 10**18
    assert row["confidence"] == w[1] / 10**18
    assert row["feed_ts"] == w[2]


def test_decode_forward_settlement_log():
    entry = SETTLE["forward"][-1]
    row = pf.decode_log("forward", entry)
    w = words(entry["data"])
    assert row["expiry"] == SETTLE["expiry"]
    assert row["value"] == signed(w[0]) / 10**18
    assert row["value"] < 0
    assert row["confidence"] == w[1] / 10**18
    assert row["feed_ts"] == w[2]
    assert SETTLE["expiry"] - row["feed_ts"] < 1800  # inside the TWAP window
    assert row["fixed"] == ((w[4] - w[3]) // 1800) / 10**18
    assert row["fixed"] > 0


def test_decode_forward_far_log_has_no_fixed_portion():
    row = pf.decode_log("forward", SETTLE["forward_far"][-1])
    assert row["expiry"] == SETTLE["expiry_far"] and row["fixed"] == 0.0


def test_decode_rate_perp_and_static_rate():
    rate = pf.decode_log("rate_pm2", SETTLE["rate_pm2"][-1])
    w = words(SETTLE["rate_pm2"][-1]["data"])
    assert rate["expiry"] == SETTLE["expiry"] and rate["value"] == signed(w[0]) / 10**18 and rate["feed_ts"] == w[2]
    perp = pf.decode_log("perp", SETTLE["perp"][-1])
    w = words(SETTLE["perp"][-1]["data"])
    assert perp["expiry"] == 0 and perp["value"] == signed(w[0]) / 10**18 and perp["value"] < 0
    static = pf.decode_log("rate_pm", SETTLE["rate_pm"][0])
    assert static["value"] == 0.0 and static["confidence"] == 1.0 and static["expiry"] == 0
    assert static["feed_ts"] == static["block_ts"]


def test_logs_to_frame_columns():
    df = pf.logs_to_frame("forward", SETTLE["forward"] + SETTLE["forward_far"])
    assert list(df.columns) == ["block", "block_ts", "log_index", "expiry", "value", "confidence", "feed_ts", "fixed"]
    assert len(df) == len(SETTLE["forward"]) + len(SETTLE["forward_far"])
    spot = pf.logs_to_frame("spot", SETTLE["spot"])
    assert list(spot.columns) == ["block", "block_ts", "log_index", "expiry", "value", "confidence", "feed_ts"]
    assert pf.logs_to_frame("rate_pm2", []).empty


# ---------------------------------------------------------------- forward exactly as LyraForwardFeed

def _last(entries):
    return max(entries, key=lambda e: (int(e["blockNumber"], 16), int(e["logIndex"], 16)))


def test_forward_portions_int_match_eth_call_in_settlement_window():
    spot_int = words(SETTLE["eth_call"]["getSpot"])[0]
    fwd = words(_last(SETTLE["forward"])["data"])
    fixed, variable = pf.forward_portions_int(spot_int, signed(fwd[0]), fwd[2], SETTLE["expiry"], fwd[3], fwd[4])
    want = words(SETTLE["eth_call"]["getForwardPricePortions"])
    assert (fixed, variable) == (want[0], want[1])
    assert fixed + variable == words(SETTLE["eth_call"]["getForwardPrice"])[0]


def test_forward_portions_int_far_expiry():
    spot_int = words(SETTLE["eth_call"]["getSpot"])[0]
    fwd = words(_last(SETTLE["forward_far"])["data"])
    fixed, variable = pf.forward_portions_int(spot_int, signed(fwd[0]), fwd[2], SETTLE["expiry_far"], fwd[3], fwd[4])
    want = words(SETTLE["eth_call"]["getForwardPricePortions_far"])
    assert (fixed, variable) == (want[0], want[1]) and fixed == 0


def test_forward_price_float_vectorised():
    spot = np.array([100.0, 100.0, 100.0])
    diff = np.array([2.0, 2.0, 2.0])
    expiry = np.array([10_000, 10_000, 10_000])
    feed_ts = np.array([10_000 - 3600, 10_000 - 900, 10_000])
    fixed = np.array([0.0, 50.0, 101.5])
    got = pf.forward_price(spot, diff, feed_ts, expiry, fixed)
    assert got[0] == 102.0
    assert got[1] == pytest.approx(50.0 + 102.0 * 900 / 1800)
    assert got[2] == 101.5


def test_perp_price_caps_the_difference():
    got = pf.perp_price(np.array([100.0, 100.0, 100.0]), np.array([1.0, 10.0, -10.0]))
    np.testing.assert_allclose(got, [101.0, 106.0, 94.0])


# ---------------------------------------------------------------- FeedHistory on real fixtures

def _fixture_history():
    frames = {
        "spot": pf.logs_to_frame("spot", SETTLE["spot"]),
        "forward": pf.logs_to_frame("forward", SETTLE["forward"] + SETTLE["forward_far"]),
        "rate_pm2": pf.logs_to_frame("rate_pm2", SETTLE["rate_pm2"] + SETTLE["rate_far"]),
        "perp": pf.logs_to_frame("perp", SETTLE["perp"]),
    }
    return pf.FeedHistory("BTC", frames=frames)


def test_state_at_matches_eth_call_fixture():
    hist = _fixture_history()
    ts = SETTLE["block_ts"]
    st = hist.state_at(ts, [SETTLE["expiry"], SETTLE["expiry_far"]])
    ec = {k: words(v) for k, v in SETTLE["eth_call"].items()}
    assert st.spot == ec["getSpot"][0] / 10**18
    assert st.spot_conf == ec["getSpot"][1] / 10**18
    near, far = st.expiries[SETTLE["expiry"]], st.expiries[SETTLE["expiry_far"]]
    assert near.forward == pytest.approx(ec["getForwardPrice"][0] / 10**18, rel=1e-14)
    assert near.fwd_conf == ec["getForwardPrice"][1] / 10**18
    assert far.forward == pytest.approx(ec["getForwardPricePortions_far"][1] / 10**18, rel=1e-14)
    assert near.rate == signed(ec["getInterestRate"][0]) / 10**18
    assert far.rate == signed(ec["getInterestRate_far"][0]) / 10**18
    assert st.perp == pytest.approx(ec["getPerpPrice"][0] / 10**18, rel=1e-14)
    assert st.perp_conf == ec["getPerpPrice"][1] / 10**18
    assert near.svi is None  # no vol frame given


# ---------------------------------------------------------------- FeedHistory on a synthetic mini history

E1, E2 = 2_000_000_000, 2_000_086_400


def _frame(rows, cols=("block", "log_index", "expiry", "value", "confidence", "feed_ts")):
    df = pd.DataFrame(rows, columns=list(cols))
    df.insert(1, "block_ts", [ts_at_block(b) for b in df["block"]])
    return df


def _mini_frames():
    b0 = 40_000_000
    spot = _frame([(b0, 0, 0, 100.0, 1.0, ts_at_block(b0) - 1),
                   (b0 + 10, 0, 0, 101.0, 0.9, ts_at_block(b0 + 10) - 1),
                   (b0 + 20, 3, 0, 102.0, 1.0, ts_at_block(b0 + 20) - 1)])
    fwd = _frame([(b0 + 5, 1, E1, 5.0, 0.8, ts_at_block(b0 + 5) - 2),
                  (b0 + 15, 1, E1, 7.0, 1.0, ts_at_block(b0 + 15) - 2),
                  (b0 + 15, 2, E2, -3.0, 1.0, ts_at_block(b0 + 15) - 2)])
    fwd["fixed"] = 0.0
    rate = _frame([(b0 + 12, 0, E1, 0.05, 1.0, ts_at_block(b0 + 12) - 1)])
    perp = _frame([(b0 + 1, 0, 0, 0.5, 1.0, ts_at_block(b0 + 1) - 1)])
    svi = pd.DataFrame({"block": [b0 + 8], "block_ts": [ts_at_block(b0 + 8)], "log_index": [0], "expiry": [E1],
                        "feed_ts": [ts_at_block(b0 + 8) - 3], "svi_a": np.float32([0.001]), "svi_b": np.float32([0.02]),
                        "svi_rho": np.float32([-0.3]), "svi_m": np.float32([0.01]), "svi_sigma": np.float32([0.05]),
                        "svi_fwd": [103.0], "svi_ref_tau": np.float32([0.05]), "confidence": np.float32([0.95])})
    return b0, {"spot": spot, "forward": fwd, "rate_pm2": rate, "perp": perp, "svi": svi}


def _mini_history():
    b0, frames = _mini_frames()
    return b0, pf.FeedHistory("BTC", frames=frames)


def test_state_at_takes_last_value_at_or_before_ts():
    b0, hist = _mini_history()
    st = hist.state_at(ts_at_block(b0 + 15), [E1, E2])
    assert st.spot == 101.0 and st.spot_conf == 0.9
    assert st.expiries[E1].forward == 101.0 + 7.0
    assert st.expiries[E2].forward == 101.0 - 3.0
    assert st.expiries[E1].rate == 0.05 and st.expiries[E2].rate == 0.0
    assert st.expiries[E1].fwd_conf == min(1.0, 0.9)
    assert st.perp == 101.5
    e1 = st.expiries[E1]
    assert e1.svi is not None and e1.svi_fwd == 103.0 and e1.vol_conf == pytest.approx(0.95)
    assert st.expiries[E2].svi is None
    # one second before block b0 + 15 the second forward push is not yet visible
    st = hist.state_at(ts_at_block(b0 + 15) - 1, [E1, E2])
    assert st.expiries[E1].forward == 101.0 + 5.0 and np.isnan(st.expiries[E2].forward)
    # before any spot
    st = hist.state_at(ts_at_block(b0) - 1, [E1])
    assert np.isnan(st.spot) and np.isnan(st.expiries[E1].forward)
    assert st.ts == ts_at_block(b0) - 1 and st.currency == "BTC"


def test_bulk_matches_state_at_row_by_row():
    b0, hist = _mini_history()
    rng = np.random.default_rng(1)
    n = 200
    ts = rng.integers(ts_at_block(b0) - 5, ts_at_block(b0 + 25), n)
    expiry = rng.choice([E1, E2, 1_999_000_000], n)
    strike = rng.choice([90.0, 100.0, 110.0], n)
    out = hist.bulk(ts, expiry, strike)
    assert list(out.columns[:11]) == ["spot", "forward", "sigma", "rate", "svi_fwd", "vol_conf", "fwd_conf",
                                      "spot_age", "fwd_age", "vol_age", "rate_age"]
    assert len(out) == n
    for i in range(n):
        st = hist.state_at(int(ts[i]), [int(expiry[i])])
        es = st.expiries[int(expiry[i])]
        row = out.iloc[i]
        np.testing.assert_equal(row["spot"], st.spot)
        np.testing.assert_equal(row["forward"], es.forward)
        np.testing.assert_equal(row["rate"], es.rate)
        np.testing.assert_equal(row["fwd_fixed"], es.fwd_fixed)
        np.testing.assert_equal(row["rate_conf"], es.rate_conf)
        np.testing.assert_equal(row["fwd_conf"], es.fwd_conf)
        assert isinstance(es, pf.ExpiryState)
        np.testing.assert_equal(row["perp"], st.perp if st.perp is not None else np.nan)
        if es.svi is None:
            assert np.isnan(row["sigma"]) and np.isnan(row["svi_fwd"])
        else:
            assert row["sigma"] == es.vol(float(strike[i]))
            assert row["svi_fwd"] == es.svi_fwd and row["vol_conf"] == es.vol_conf
    # ages are ts - feed_ts of the value used
    i = int(np.argmax(ts))
    assert out["spot_age"].iloc[i] == ts[i] - (ts_at_block(b0 + 20) - 1)


def test_bulk_speed_600k_rows():
    rng = np.random.default_rng(2)
    b0 = 30_000_000
    expiries = np.arange(200) * 86_400 + 1_800_000_000
    n_f = 400_000
    fblock = np.sort(rng.integers(b0, b0 + 2_000_000, n_f))
    fwd = pd.DataFrame({"block": fblock, "log_index": np.zeros(n_f, dtype=np.int32), "expiry": rng.choice(expiries, n_f),
                        "value": rng.normal(0, 10, n_f), "confidence": np.ones(n_f), "feed_ts": ts_at_block(0) + 2 * fblock - 1,
                        "fixed": np.zeros(n_f)})
    fwd.insert(1, "block_ts", ts_at_block(0) + 2 * fwd["block"].to_numpy())
    sblock = np.arange(b0, b0 + 2_000_000, 30)
    spot = pd.DataFrame({"block": sblock, "block_ts": ts_at_block(0) + 2 * sblock, "log_index": 0, "expiry": 0,
                         "value": 100.0 + rng.normal(0, 1, len(sblock)), "confidence": 1.0,
                         "feed_ts": ts_at_block(0) + 2 * sblock - 1})
    svi = pd.DataFrame({"block": fblock, "block_ts": fwd["block_ts"], "log_index": 1, "expiry": fwd["expiry"],
                        "feed_ts": fwd["feed_ts"], "svi_a": np.float32(0.001), "svi_b": np.float32(0.02),
                        "svi_rho": np.float32(-0.3), "svi_m": np.float32(0.0), "svi_sigma": np.float32(0.05),
                        "svi_fwd": 100.0, "svi_ref_tau": np.float32(0.05), "confidence": np.float32(1.0)})
    hist = pf.FeedHistory("BTC", frames={"spot": spot, "forward": fwd, "rate_pm2": fwd.drop(columns="fixed"), "perp": spot,
                                         "svi": svi})
    n = 600_000
    ts = rng.integers(ts_at_block(b0), ts_at_block(b0 + 2_000_000), n)
    t0 = time.perf_counter()
    out = hist.bulk(ts, rng.choice(expiries, n), rng.uniform(80, 120, n))
    assert time.perf_counter() - t0 < 60
    assert len(out) == n and out["forward"].notna().mean() > 0.9


# ---------------------------------------------------------------- download and compaction

class FakeRpc:
    """eth_getLogs over a synthetic spot feed: one log every 7 blocks; refuses more than `limit` logs."""

    def __init__(self, limit=50):
        self.limit, self.calls = limit, []

    def raw(self, method, params):
        assert method == "eth_getLogs"
        flt = params[0]
        lo, hi = int(flt["fromBlock"], 16), int(flt["toBlock"], 16)
        self.calls.append((lo, hi))
        blocks = [b for b in range(lo, hi + 1) if b % 7 == 0]
        if len(blocks) > self.limit:
            raise RpcError({"code": -32005, "message": "logs count limit exceeded (10000)"})
        out = []
        for b in blocks:
            data = "0x" + (b * 10 ** 18).to_bytes(32, "big").hex() + (10 ** 18).to_bytes(32, "big").hex() + \
                   ts_at_block(b).to_bytes(32, "big").hex()
            out.append({"address": flt["address"], "topics": [flt["topics"][0]], "data": data, "blockNumber": hex(b),
                        "logIndex": "0x0", "blockTimestamp": hex(ts_at_block(b))})
        return out


def test_fetch_logs_adapts_window():
    rpc = FakeRpc(limit=50)
    logs, window = pf.fetch_logs(rpc, "0xfeed", pf.SPOT_PRICE_UPDATED, 1_000, 5_000, window=10_000, target=40)
    assert [int(e["blockNumber"], 16) for e in logs] == [b for b in range(1_000, 5_001) if b % 7 == 0]
    assert 0 < window < 10_000


def test_sync_is_resumable_and_compact_writes_one_file(tmp_path, monkeypatch):
    monkeypatch.setattr(pf, "CHUNK_BLOCKS", 1_000)
    raw, out = tmp_path / "raw", tmp_path / "feeds"
    rpc = FakeRpc(limit=100)
    lo = pf.FEEDS["BTC"]["deploy"]["spot"]
    to_block = lo + 3_500
    first = pf.sync("BTC", "spot", to_block, rpc=rpc, raw_dir=raw, max_seconds=0)
    assert first["fetched"] == 1 and not first["done"]
    while not pf.sync("BTC", "spot", to_block, rpc=rpc, raw_dir=raw, max_seconds=0)["done"]:
        pass
    n_calls = len(rpc.calls)
    again = pf.sync("BTC", "spot", to_block, rpc=rpc, raw_dir=raw)
    assert again["done"] and again["fetched"] == 0 and len(rpc.calls) == n_calls
    info = pf.compact("BTC", "spot", raw_dir=raw, out_dir=out)
    df = pd.read_parquet(out / "BTC_spot.parquet")
    want = [b for b in range(lo, to_block + 1) if b % 7 == 0]
    assert df["block"].tolist() == want and info["rows"] == len(want)
    assert info["block_ts_mismatch"] == 0
    assert (df["value"] == df["block"].astype(float)).all()


# ---------------------------------------------------------------- multicall

def test_aggregate3_encoding_matches_eth_abi():
    calls = [(c["target"], c["allow_failure"], c["data"]) for c in MC["calls"]]
    assert pf.encode_aggregate3(calls) == MC["calldata"]


def test_aggregate3_decoding_matches_eth_abi():
    got = pf.decode_aggregate3(MC["response"])
    assert [(ok, "0x" + data.hex()) for ok, data in got] == [(d["success"], d["data"]) for d in MC["decoded"]]


def test_sync_parts_split_the_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr(pf, "CHUNK_BLOCKS", 1_000)
    raw = tmp_path / "raw"
    lo = pf.FEEDS["BTC"]["deploy"]["perp"]
    to_block = lo + 5_500  # six chunks of 1 000 blocks
    a = pf.sync("BTC", "perp", to_block, rpc=FakeRpc(limit=200), raw_dir=raw, part=(0, 2))
    assert a["fetched"] == 3 and not a["done"]
    b = pf.sync("BTC", "perp", to_block, rpc=FakeRpc(limit=200), raw_dir=raw, part=(1, 2))
    assert b["fetched"] == 3 and b["done"]


def test_state_carries_fixed_forward_portion_and_rate_confidence():
    hist = _fixture_history()
    st = hist.state_at(SETTLE["block_ts"], [SETTLE["expiry"], SETTLE["expiry_far"]])
    portions = words(SETTLE["eth_call"]["getForwardPricePortions"])
    near, far = st.expiries[SETTLE["expiry"]], st.expiries[SETTLE["expiry_far"]]
    assert near.fwd_fixed == pytest.approx(portions[0] / 10**18, rel=1e-15)
    assert near.forward - near.fwd_fixed == pytest.approx(portions[1] / 10**18, rel=1e-12)
    assert far.fwd_fixed == 0.0
    assert near.rate_conf == words(SETTLE["eth_call"]["getInterestRate"])[1] / 10**18
    out = hist.bulk(np.array([SETTLE["block_ts"]] * 2), np.array([SETTLE["expiry"], SETTLE["expiry_far"]]),
                    np.array([100_000.0, 100_000.0]))
    assert out["fwd_fixed"].tolist() == [near.fwd_fixed, 0.0]
    assert out["rate_conf"].tolist() == [near.rate_conf, far.rate_conf]
    assert out["rate_pm"].tolist() == [0.0, 0.0]  # no legacy frame given: static rate 0


def test_history_without_svi_and_legacy_rate_frame():
    b0, mini = _mini_frames()
    static = pd.DataFrame({"block": [843_076], "block_ts": [ts_at_block(843_076)], "log_index": [29], "expiry": [0],
                           "value": [0.01], "confidence": [1.0], "feed_ts": [ts_at_block(843_076)]})
    frames = {"spot": mini["spot"], "svi": mini["svi"], "rate_pm": static}
    hist = pf.FeedHistory("BTC", frames=frames, with_svi=False)
    out = hist.bulk(np.array([ts_at_block(b0 + 20)]), np.array([E1]), np.array([100.0]))
    assert out["rate_pm"].iloc[0] == 0.01 and np.isnan(out["sigma"].iloc[0]) and out["spot"].iloc[0] == 102.0


class FakeMulticallRpc:
    """Answers Multicall3.aggregate3 at the fixture block with the recorded eth_call results."""

    def __init__(self):
        ec = SETTLE["eth_call"]
        e, e2 = SETTLE["expiry"], SETTLE["expiry_far"]
        far = words(ec["getForwardPricePortions_far"])
        a = SETTLE["addresses"]
        self.answers = {
            (a["spot"].lower(), "2b37269c"): ec["getSpot"][2:],
            (a["perp_asset"].lower(), "90f76b18"): ec["getPerpPrice"][2:],
            (a["forward"].lower(), "b34f2e36" + e.to_bytes(32, "big").hex()): ec["getForwardPrice"][2:],
            (a["forward"].lower(), "b34f2e36" + e2.to_bytes(32, "big").hex()):
                (far[0] + far[1]).to_bytes(32, "big").hex() + far[2].to_bytes(32, "big").hex(),
            (a["rate_pm2"].lower(), "b0487ff6" + e.to_bytes(32, "big").hex()): ec["getInterestRate"][2:],
            (a["rate_pm2"].lower(), "b0487ff6" + e2.to_bytes(32, "big").hex()): ec["getInterestRate_far"][2:],
        }
        self.blocks = []

    def raw(self, method, params):
        assert method == "eth_call" and params[0]["to"] == pf.MULTICALL3
        self.blocks.append(int(params[1], 16))
        raw = bytes.fromhex(params[0]["data"][10:])
        w = lambda pos: int.from_bytes(raw[pos:pos + 32], "big")  # noqa: E731
        n, head, results = w(32), 64, []
        for k in range(n):
            el = head + w(head + 32 * k)
            target = "0x" + raw[el + 12:el + 32].hex()
            size = w(el + 96)
            results.append(self.answers[(target, raw[el + 128:el + 128 + size].hex())])
        elems = []
        for r in results:
            data = bytes.fromhex(r)
            elems.append((1).to_bytes(32, "big") + (64).to_bytes(32, "big") + len(data).to_bytes(32, "big") + data)
        offs, pos = b"", 32 * len(elems)
        for e in elems:
            offs += pos.to_bytes(32, "big")
            pos += len(e)
        return "0x" + ((32).to_bytes(32, "big") + len(elems).to_bytes(32, "big") + offs + b"".join(elems)).hex()


def test_crosscheck_against_recorded_eth_calls():
    rpc = FakeMulticallRpc()
    b = SETTLE["block"]
    res = pf.crosscheck("BTC", n=1, rpc=rpc, hist=_fixture_history(), lo_block=b, hi_block=b + 1)
    assert res["blocks"] == [b] and rpc.blocks == [b]
    assert res["reverted"] == 0 and res["calls"] == 6
    assert res["spot"]["max_abs_dev"] == 0 and res["rate"]["max_abs_dev"] == 0
    assert res["forward"]["n"] == 2 and res["forward"]["max_rel_dev"] < 1e-14
    assert res["perp"]["max_rel_dev"] < 1e-14
    assert res["spot"]["conf_equal"] == 1 and res["forward"]["conf_equal"] == 2 and res["rate"]["conf_equal"] == 2


@pytest.mark.parametrize("key,kind", [("spot", "spot"), ("forward", "forward"), ("forward_far", "forward"),
                                      ("rate_pm2", "rate_pm2"), ("rate_far", "rate_pm2"), ("perp", "perp"),
                                      ("rate_pm", "rate_pm")])
def test_every_fixture_log_decodes(key, kind):
    for entry in SETTLE[key]:
        row = pf.decode_log(kind, entry)
        w = words(entry["data"])
        assert row["block"] == int(entry["blockNumber"], 16) and row["block_ts"] == ts_at_block(row["block"])
        assert row["value"] == (signed(w[0]) if kind != "spot" else w[0]) / 10**18
        assert row["confidence"] == w[1] / 10**18 <= 1.0
        if kind != "rate_pm":
            assert row["feed_ts"] == w[2] <= row["block_ts"]
        if kind in ("forward", "rate_pm2"):
            assert row["expiry"] == int(entry["topics"][1], 16)


def test_crosscheck_at_given_blocks():
    b = SETTLE["block"]
    res = pf.crosscheck("BTC", rpc=FakeMulticallRpc(), hist=_fixture_history(), blocks=[b])
    assert res["blocks"] == [b] and res["forward"]["exact"] + res["forward"]["n"] >= 2
