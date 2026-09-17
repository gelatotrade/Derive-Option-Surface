from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from derive_surface import chainfeeds as cf

FIXTURE = Path(__file__).parent / "fixtures" / "vol_log_btc_44814062.json"


def word(x: int) -> str:
    return (x % (1 << 256)).to_bytes(32, "big").hex()


def make_log(block, idx, expiry, fwd=50_000.0, ts=1_700_000_000, a=0.0001, b=0.01, rho=-0.2, m=-0.005, sig=0.01, tau=0.002):
    vals = [a, b, rho, m, sig, fwd, tau, 0.95]
    data = "0x" + "".join(word(int(round(v * 1e18))) for v in vals) + word(ts)
    return {"address": "0xfeed", "topics": [cf.VOL_DATA_UPDATED, "0x" + word(expiry)], "data": data,
            "blockNumber": hex(block), "logIndex": hex(idx)}


class FakeChain:
    """One log every 10 blocks; refuses ranges longer than max_span blocks with the real -32005 error."""

    def __init__(self, max_span=1000, head=100_000):
        self.max_span, self.head, self.calls = max_span, head, 0

    def get_logs(self, address, topic0, from_block, to_block):
        self.calls += 1
        if to_block - from_block + 1 > self.max_span:
            raise cf.RpcError({"code": -32005, "message": "logs count limit exceeded (10000)"})
        return [make_log(b, 0, 1_800_000_000) for b in range(from_block, to_block + 1) if b % 10 == 0]

    def block_number(self):
        return self.head

    def block_timestamp(self, n):
        return 1_000 + 2 * n


def test_decode_real_log():
    d = cf.decode_vol_log(json.loads(FIXTURE.read_text()))
    assert d["block"] == 44_814_062 and d["expiry"] == 1_789_718_400 and d["feed_ts"] == 1_789_649_694
    assert d["svi_fwd"] == pytest.approx(76735.40114792966, rel=1e-12)
    assert d["svi_rho"] == pytest.approx(-0.21917865955083932, rel=1e-9)
    assert d["svi_a"] == pytest.approx(9.7272545053122e-05, rel=1e-9)
    assert d["svi_ref_tau"] == pytest.approx(0.0021803652968, rel=1e-9)
    assert d["confidence"] == pytest.approx(0.95)


def test_decode_rejects_wrong_payload():
    bad = make_log(1, 0, 1)
    bad["data"] = bad["data"][:-64]
    with pytest.raises(ValueError):
        cf.decode_vol_log(bad)


def test_svi_vol_real_params_atm_is_plausible():
    d = cf.decode_vol_log(json.loads(FIXTURE.read_text()))
    vol = cf.svi_vol(d["svi_fwd"], d["svi_a"], d["svi_b"], d["svi_rho"], d["svi_m"], d["svi_sigma"], d["svi_fwd"], d["svi_ref_tau"])
    assert 0.28 < float(vol) < 0.30


def test_svi_vol_formula_bound_and_cap():
    a, b, rho, m, sig, fwd, tau = 0.01, 0.1, -0.3, 0.02, 0.1, 100.0, 0.5
    K = 110.0
    k = math.log(K / fwd)
    w = a + b * (rho * (k - m) + math.sqrt((k - m) ** 2 + sig ** 2))
    assert float(cf.svi_vol(K, a, b, rho, m, sig, fwd, tau)) == pytest.approx(math.sqrt(w / tau), rel=1e-12)
    bound = 4 * math.sqrt(a + b * sig)
    far = float(cf.svi_vol(fwd * math.exp(10), a, b, rho, m, sig, fwd, tau))
    at_bound = float(cf.svi_vol(fwd * math.exp(bound), a, b, rho, m, sig, fwd, tau))
    assert far == pytest.approx(at_bound, rel=1e-12)
    assert float(cf.svi_vol(fwd, 500.0, 0.0, 0.0, 0.0, 0.1, fwd, 1.0)) == pytest.approx(12.0)  # w capped at 144
    assert np.isnan(cf.svi_vol(fwd, -1.0, 0.0, 0.0, 0.0, 0.1, fwd, 1.0))


def test_adaptive_window_halves_and_returns_each_log_once():
    chain = FakeChain(max_span=1000)
    logs, window = cf.get_logs_adaptive(chain, "0xfeed", cf.VOL_DATA_UPDATED, 0, 9_999, window=5_000)
    blocks = [int(x["blockNumber"], 16) for x in logs]
    assert blocks == list(range(0, 10_000, 10))
    assert window <= 1000


def test_adaptive_window_reraises_other_errors():
    class Broken(FakeChain):
        def get_logs(self, *a):
            raise cf.RpcError({"code": -32000, "message": "header not found"})

    with pytest.raises(cf.RpcError):
        cf.get_logs_adaptive(Broken(), "0xfeed", cf.VOL_DATA_UPDATED, 0, 100)


def test_block_at_binary_search():
    chain = FakeChain(head=50_000)
    assert cf.block_at(chain, 1_000 + 2 * 12_345) == 12_345
    assert cf.block_at(chain, 1_000 + 2 * 12_345 + 1) == 12_345
    assert cf.block_at(chain, 10 ** 12) == 50_000


def test_sync_feed_writes_chunks_and_resumes(tmp_path, monkeypatch):
    monkeypatch.setattr(cf, "CHUNK_BLOCKS", 2_000)
    monkeypatch.setitem(cf.VOL_FEEDS, "TST", {"address": "0xfeed", "from_block": 1_000})
    chain = FakeChain(max_span=1000)
    res = cf.sync_feed(chain, "TST", tmp_path, 6_499, workers=2, window=4_000)
    assert res["chunks"] == 4 and res["fetched"] == 4 and res["events_fetched"] == 650  # chunk 0 starts at block 0
    files = sorted(p.name for p in (tmp_path / "TST").glob("*.parquet"))
    assert files[0] == "000000000_000001999.parquet" and files[-1] == "000006000_000006499.parquet"
    again = cf.sync_feed(chain, "TST", tmp_path, 6_499, workers=2)
    assert again["fetched"] == 0
    df = cf.load_feed(tmp_path, "TST")
    assert len(df) == 650 and df["svi_a"].dtype == "float32" and df["svi_fwd"].dtype == "float64"


def test_load_feed_prefers_longest_chunk(tmp_path):
    d = tmp_path / "TST"
    d.mkdir()
    short = cf.logs_to_frame([make_log(10, 0, 1)])
    long = cf.logs_to_frame([make_log(10, 0, 1), make_log(20, 0, 1)])
    short.to_parquet(cf.chunk_path(d, 0, 15))
    long.to_parquet(cf.chunk_path(d, 0, 49_999))
    assert len(cf.load_feed(tmp_path, "TST")) == 2


def test_compact_feed_by_month(tmp_path):
    d = tmp_path / "TST"
    d.mkdir()
    frame = cf.logs_to_frame([make_log(10, 0, 1, ts=1_704_067_200), make_log(20, 0, 1, ts=1_706_745_600)])
    frame.to_parquet(cf.chunk_path(d, 0, 49_999))
    counts = cf.compact_feed(tmp_path, "TST", tmp_path / "out")
    assert counts == {"2024-01": 1, "2024-02": 1}
    assert (tmp_path / "out" / "TST_svi_2024-02.parquet").exists()


def test_scan_emitters_groups_by_address():
    class Multi(FakeChain):
        def get_logs(self, address, topic0, a, b):
            assert address is None
            x = make_log(a, 0, 1, fwd=100.0)
            y = make_log(a, 1, 1, fwd=50_000.0)
            y["address"] = "0xABC"
            return [x, y, y]

    out = cf.scan_emitters(Multi(), [100, 200], span=10)
    assert set(out["address"]) == {"0xfeed", "0xabc"}
    row = out[(out.sample_block == 100) & (out.address == "0xabc")].iloc[0]
    assert row.n == 2 and row.fwd == pytest.approx(50_000.0)
