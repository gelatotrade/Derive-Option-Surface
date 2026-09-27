"""Read-only access to Derive Chain 957 for Paper 2: block clock, throttled eth_call and logs, request log."""
from __future__ import annotations

import datetime as dt
import json
import threading
import time
from pathlib import Path
from typing import Optional

from .chainfeeds import ChainClient, get_logs_adaptive

RPC_URL = "https://rpc.lyra.finance"
ANCHOR_BLOCK = 2_454_793          # 2024-01-11 00:00:01 UTC
ANCHOR_TS = 1_704_931_201
BLOCK_SECONDS = 2                 # exactly 2 s per block since genesis (checked on 2026-09-24)


def block_at_ts(ts: int) -> int:
    """Last block with timestamp <= ts."""
    return ANCHOR_BLOCK + (int(ts) - ANCHOR_TS) // BLOCK_SECONDS


def ts_at_block(block: int) -> int:
    return ANCHOR_TS + (int(block) - ANCHOR_BLOCK) * BLOCK_SECONDS


class Rpc:
    """Throttled wrapper around :class:`ChainClient` that appends every request to a JSONL log."""

    def __init__(self, client=None, url: str = RPC_URL, rate: float = 2.0, log_path: Optional[Path] = None):
        self.client = client or ChainClient(url=url)
        self.min_gap = 1.0 / rate
        self.log_path = Path(log_path) if log_path else None
        self._last = 0.0
        self._lock = threading.Lock()

    def _throttle(self) -> None:
        with self._lock:
            wait = self._last + self.min_gap - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()

    def _log(self, method: str, params, result) -> None:
        if self.log_path is None:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(), "method": method, "params": params,
               "result": result if isinstance(result, (str, int, float)) or result is None else f"<{type(result).__name__}>"}
        with self.log_path.open("a") as fh:
            fh.write(json.dumps(row) + "\n")

    def raw(self, method: str, params: list):
        self._throttle()
        out = self.client.call(method, params)
        self._log(method, params, out)
        return out

    def eth_call(self, to: str, data: str, block: int, gas: Optional[int] = None) -> bytes:
        tx = {"to": to, "data": data}
        if gas is not None:
            tx["gas"] = hex(gas)
        out = self.raw("eth_call", [tx, hex(int(block))])
        return bytes.fromhex(out[2:])

    def logs(self, address: Optional[str], topic0: str, lo: int, hi: int, window: int = 5_000) -> list:
        """All logs in [lo, hi] with adaptive windows; each underlying request is throttled."""
        throttled = _ThrottledLogs(self)
        entries, _ = get_logs_adaptive(throttled, address, topic0, lo, hi, window=window)
        return entries


class _ThrottledLogs:
    def __init__(self, rpc: Rpc):
        self.rpc = rpc

    def get_logs(self, address, topic0, from_block, to_block):
        flt = {"topics": [topic0], "fromBlock": hex(from_block), "toBlock": hex(to_block)}
        if address:
            flt["address"] = address
        return self.rpc.raw("eth_getLogs", [flt])
