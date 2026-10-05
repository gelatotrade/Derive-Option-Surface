from __future__ import annotations

import json

from derive_surface.p2chain import Rpc, block_at_ts, ts_at_block


def test_block_clock_is_two_seconds_from_anchor():
    assert block_at_ts(1_704_931_201) == 2_454_793
    assert ts_at_block(2_454_793) == 1_704_931_201
    assert block_at_ts(1_704_931_201 + 3) == 2_454_794  # floor


def test_block_clock_second_anchor():
    # 2026-09-24 00:00:01 UTC is block 45 093 193 (probe of 24.09.2026)
    assert block_at_ts(1_790_208_001) == 45_093_193


class _FakeClient:
    def __init__(self):
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        if method == "eth_call":
            return "0x" + "00" * 31 + "2a"
        return []


def test_rpc_eth_call_encodes_block_and_logs(tmp_path):
    fake = _FakeClient()
    log = tmp_path / "log.jsonl"
    rpc = Rpc(client=fake, rate=1000.0, log_path=log)
    out = rpc.eth_call("0xabc", "0x1234", 100)
    assert out == bytes(31) + b"\x2a"
    method, params = fake.calls[0]
    assert method == "eth_call" and params[0] == {"to": "0xabc", "data": "0x1234"} and params[1] == hex(100)
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert rows[0]["method"] == "eth_call" and "ts" in rows[0]
