"""Thin client for the public Derive (ex-Lyra) JSON-RPC API.

Only public endpoints are used; no wallet, no session key.  Endpoint semantics
were verified live against ``api.lyra.finance`` (the host still used by
derive.xyz); see ``docs/derive_api_notes.md`` for the empirical findings.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable

import requests

REST_URL = "https://api.lyra.finance"
WS_URL = "wss://api.lyra.finance/ws"

log = logging.getLogger(__name__)


class DeriveError(RuntimeError):
    """A JSON-RPC level error returned by Derive."""

    def __init__(self, method: str, error: dict):
        self.method = method
        self.error = error
        super().__init__(f"{method}: {error}")


@dataclass(frozen=True)
class OptionName:
    """Parsed option instrument name, e.g. ``BTC-20260904-110000-C``."""

    currency: str
    expiry_date: str  # YYYYMMDD (UTC)
    strike: float
    option_type: str  # "C" | "P"

    @classmethod
    def parse(cls, name: str) -> "OptionName":
        ccy, date, strike, kind = name.split("-")
        return cls(ccy, date, float(strike), kind)

    @property
    def expiry_ts(self) -> int:
        """Expiry as unix seconds; Derive options expire 08:00 UTC."""
        d = dt.datetime.strptime(self.expiry_date, "%Y%m%d").replace(tzinfo=dt.timezone.utc)
        return int((d + dt.timedelta(hours=8)).timestamp())


def expiry_date_str(expiry_ts: int) -> str:
    """Unix expiry seconds -> ``YYYYMMDD`` as expected by ``get_tickers``."""
    return dt.datetime.fromtimestamp(expiry_ts, dt.timezone.utc).strftime("%Y%m%d")


class DeriveClient:
    """Synchronous REST client with retry/backoff plus an async WebSocket helper."""

    def __init__(
        self,
        base_url: str = REST_URL,
        ws_url: str = WS_URL,
        timeout: float = 60.0,
        max_retries: int = 8,
        session: requests.Session | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.ws_url = ws_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = session or requests.Session()

    # ------------------------------------------------------------------ REST
    def call(self, method: str, **params: Any) -> Any:
        """POST ``/public/<method>`` and return the ``result`` payload."""
        url = f"{self.base_url}/public/{method}"
        delay = 1.0
        for attempt in range(self.max_retries):
            try:
                resp = self.session.post(url, json=params, timeout=self.timeout)
            except requests.RequestException as exc:  # network hiccup -> retry
                log.warning("%s: network error %s (attempt %d)", method, exc, attempt + 1)
            else:
                if resp.status_code == 429 or resp.status_code >= 500:
                    log.warning("%s: HTTP %s (attempt %d)", method, resp.status_code, attempt + 1)
                else:
                    payload = resp.json()
                    if "error" in payload:
                        err = payload["error"]
                        if _is_rate_limit(err):
                            log.warning("%s: rate limited %s (attempt %d)", method, err, attempt + 1)
                        else:
                            raise DeriveError(method, err)
                    else:
                        return payload["result"]
            time.sleep(delay + random.uniform(0, 0.5))
            delay = min(delay * 2, 30)
        raise RuntimeError(f"{method}: giving up after {self.max_retries} attempts")

    # typed helpers --------------------------------------------------------
    def currencies(self) -> list[dict]:
        return self.call("get_all_currencies")

    def instruments(self, currency: str, instrument_type: str = "option", expired: bool = False) -> list[dict]:
        return self.call("get_instruments", currency=currency, instrument_type=instrument_type, expired=expired)

    def option_expiries(self, currency: str) -> list[int]:
        """Sorted unique expiry timestamps (unix s) of live options."""
        return sorted({i["option_details"]["expiry"] for i in self.instruments(currency)})

    def ticker(self, instrument_name: str) -> dict:
        return self.call("get_ticker", instrument_name=instrument_name)

    def tickers(self, currency: str, expiry_date: str, instrument_type: str = "option") -> dict[str, dict]:
        """Slim tickers for every instrument of one expiry (``expiry_date`` = YYYYMMDD)."""
        return self.call("get_tickers", currency=currency, instrument_type=instrument_type, expiry_date=expiry_date)["tickers"]

    def trade_history(
        self,
        currency: str,
        *,
        instrument_type: str = "option",
        page: int = 1,
        page_size: int = 1000,
        from_ts_ms: int = 0,
        to_ts_ms: int | None = None,
    ) -> dict:
        params: dict[str, Any] = dict(
            currency=currency, instrument_type=instrument_type, page=page, page_size=page_size, from_timestamp=from_ts_ms
        )
        if to_ts_ms is not None:
            params["to_timestamp"] = to_ts_ms
        return self.call("get_trade_history", **params)

    def spot_history(self, currency: str, start_s: int, end_s: int, period_s: int = 3600) -> list[dict]:
        """Spot feed points (max 500 per call — page over time windows for more)."""
        return self.call("get_spot_feed_history", currency=currency, start_timestamp=start_s, end_timestamp=end_s, period=period_s)[
            "spot_feed_history"
        ]

    def spot_history_full(self, currency: str, start_s: int, end_s: int, period_s: int = 3600) -> list[dict]:
        """Walk ``spot_history`` in 500-point windows and return the deduplicated union."""
        window = 500 * period_s
        points: dict[int, dict] = {}
        t = start_s
        while t < end_s:
            for p in self.spot_history(currency, t, min(t + window, end_s), period_s):
                points[int(p["timestamp"])] = p
            t += window
        return [points[k] for k in sorted(points)]

    # ------------------------------------------------------------------ WS
    async def stream(
        self,
        channels: Iterable[str],
        on_message: Callable[[str, dict], Awaitable[None] | None],
        duration_s: float | None = None,
        batch_size: int = 100,
    ) -> None:
        """Subscribe to ``channels`` and dispatch every notification to ``on_message``.

        ``on_message(channel, data)`` may be sync or async.  Subscriptions are
        sent in batches so that very large channel lists do not trip the server.
        """
        import websockets  # imported lazily: only needed for live recording

        channels = list(channels)
        deadline = time.monotonic() + duration_s if duration_s else None
        async with websockets.connect(self.ws_url, max_size=None, ping_interval=20) as ws:
            for i in range(0, len(channels), batch_size):
                batch = channels[i : i + batch_size]
                await ws.send(json.dumps({"id": f"sub-{i}", "method": "subscribe", "params": {"channels": batch}}))
            while deadline is None or time.monotonic() < deadline:
                timeout = None if deadline is None else max(0.1, deadline - time.monotonic())
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                except asyncio.TimeoutError:
                    break
                msg = json.loads(raw)
                if msg.get("method") != "subscription":
                    if "error" in msg:
                        log.warning("ws error: %s", msg["error"])
                    continue
                params = msg["params"]
                res = on_message(params["channel"], params["data"])
                if asyncio.iscoroutine(res):
                    await res


def _is_rate_limit(err: dict) -> bool:
    msg = json.dumps(err).lower()
    return "rate" in msg and "limit" in msg


def slim_ticker_row(name: str, t: dict) -> dict:
    """Flatten a slim ticker (as returned by ``get_tickers``) into one tidy row."""
    op = t.get("option_pricing") or {}
    o = OptionName.parse(name)
    f = _f
    return {
        "ts": int(t["t"]),
        "instrument_name": name,
        "expiry": o.expiry_ts,
        "strike": o.strike,
        "option_type": o.option_type,
        "bid": f(t.get("b")),
        "ask": f(t.get("a")),
        "bid_amount": f(t.get("B")),
        "ask_amount": f(t.get("A")),
        "mark": f(t.get("M")),
        "index": f(t.get("I")),
        "forward": f(op.get("f")),
        "iv": f(op.get("i")),
        "bid_iv": f(op.get("bi")),
        "ask_iv": f(op.get("ai")),
        "delta": f(op.get("d")),
        "gamma": f(op.get("g")),
        "vega": f(op.get("v")),
        "theta": f(op.get("t")),
        "rho": f(op.get("r")),
        "discount_factor": f(op.get("df")),
        "open_interest": f((t.get("stats") or {}).get("oi")),
    }


def _f(x: Any) -> float | None:
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None
