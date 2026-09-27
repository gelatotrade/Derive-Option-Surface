"""Explorative API snapshot (Paper 2, task C5b): ``public/get_margin`` against the replica at the head block.

Preregistration (``docs/paper2/PRAEREGISTRIERUNG.md``, section Inference): "API semantics with 2 %" is exploratory. The v2 API
(``api.lyra.finance``) computes margin off chain with a flat PM2 discount of 2 % and ticker prices; its history cannot
be rebuilt (``docs/paper2/get_margin_semantics.md``), so it is measured once, today, next to the chain semantics.

Cells: currency x maker side (buy, sell) x the 7 |delta| buckets x 5 tenor buckets of Paper 1 (``markouts``). Each
cell gets one listed, active instrument:

* expiry: among the active expiries with at least 30 min left, the one whose time to expiry lies in the tenor bucket
  and is nearest to its mid (1, 4.5, 18.5, 60 days; for the open bucket > 90 d the mid between 90 d and the longest
  listed expiry); ties: the earlier expiry.
* type: call or put, whichever is more frequent among the Paper 1 fills of the same cell (currency, maker side,
  |delta| bucket, tenor bucket) in the PM2 window; ties and empty cells: call.
* strike: the instrument of that type and expiry with a ticker whose |delta| (ticker forward delta, the Paper 1
  convention) is nearest to the bucket mid (5, 17.5, 32.5, 50, 67.5, 82.5, 95 %) and inside the bucket; ties: the
  smaller strike.

Measurement, in one go per instrument: the tickers of an expiry are read right before its instruments (``p`` = ticker
mark ``M``); then ``get_margin`` under SM and under PM2 (``market`` = currency for both), each a single request with
``simulated_positions`` +1, ``simulated_position_changes`` -2 and no collateral, so that ``pre`` is net_IM(+1; C = 0) and
``post`` is net_IM(-1; C = 0) at the same price state; then one ``eth_call`` at the head block through Multicall3 that
returns block number and time, the chain feeds (``getSpot``, ``getForwardPricePortions``, ``getVol`` at the strike, the
PM2 rate, the stable feed) and, for two synthetic accounts holding +1 and -1 contract (state override of ``SubAccounts``
as in ``p2validate``), ``getMargin(account, true)`` of the StandardManager and of PMRM_2.

* ``K_api = p q - net_IM`` from the API.
* ``K_chain = p q - net_IM`` from the replica (``capital.capital_single``, i.e. ``margin_sm`` / ``margin_pm2.single`` as
  in B2) on the chain feeds of that block, parameters of the standard lib from ``results/p2/params``.
* ``K_oracle``: the same with the managers' own ``getMargin`` (checks feeds, parameters and replica together).
* ``K_rep_api``: the replica in API semantics (index as spot, ticker forward, mark IV, PM2 rate 2 %, confidences 1).
* ``rel_diff_* = K_api / K_chain - 1``, ``rel_oracle_* = K_chain / K_oracle - 1``,
  ``rel_rep_api_* = K_api / K_rep_api - 1``.

No accounts: every book is simulated. At most 2 requests per second over API and chain together; every request with
its raw answer (including the instrument lists and tickers) goes to ``data/p2/logs/C5b.jsonl``.

    python3 -m derive_surface p2 api run [--ccy BTC ETH HYPE]
    python3 -m derive_surface p2 api report     # re-render docs/paper2/status/C5b.md from the CSV and the meta file
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from . import books, capital, p2validate
from .api import expiry_date_str
from .chainfeeds import ChainClient, RpcError
from .markouts import DELTA_EDGES, DELTA_LABELS, TENOR_EDGES_D, TENOR_LABELS
from .p2chain import RPC_URL, Rpc
from .p2feeds import FEEDS
from .p2params import PM2_ADDR, SRM, Timeline
from .p2types import YEAR

REPO = Path(__file__).resolve().parents[1]
LOG_PATH = REPO / "data" / "p2" / "logs" / "C5b.jsonl"
CSV_PATH = REPO / "results" / "p2" / "api_snapshot.csv"
META_PATH = REPO / "data" / "p2" / "api_snapshot" / "meta.json"
DOC_PATH = REPO / "docs" / "paper2" / "status" / "C5b.md"
MARKOUTS = REPO / "data" / "p1" / "derived" / "markouts.parquet"

API_URL = "https://api.lyra.finance"
USER_AGENT = "derive-option-surface/p2-C5b (research, public endpoints only)"
RATE = 2.0                 # requests per second over API and chain together
API_RATE = 0.02            # flat PM2 discount rate of the v2 API (get_margin_semantics.md, section 3)
CCYS = ("BTC", "ETH", "HYPE")
SIDES = (("buy", 1.0), ("sell", -1.0))
MANAGERS = ("sm", "pm2")
MARGIN_TYPE = {"sm": "SM", "pm2": "PM2"}
DAY = 86_400
MIN_LEFT_S = 1_800         # Paper 1 drops fills in the last 30 min before expiry (settlement TWAP window)
E18 = 10 ** 18
ACC_BUY = 2 ** 64 + 2_026_092_501   # synthetic accounts, far above SubAccounts.lastAccountId
ACC_SELL = ACC_BUY + 1

KEY_COLUMNS = ["ccy", "side", "delta_bucket", "tenor_bucket", "instrument"]
CSV_COLUMNS = KEY_COLUMNS + [
    "K_api_sm", "K_chain_sm", "K_api_pm2", "K_chain_pm2", "rel_diff_sm", "rel_diff_pm2", "ts",
    "status", "option_type", "type_share", "type_n", "strike", "tenor_days", "delta", "mark", "index", "forward_api",
    "iv_api", "K_oracle_sm", "K_oracle_pm2", "rel_oracle_sm", "rel_oracle_pm2", "K_rep_api_sm", "K_rep_api_pm2",
    "rel_rep_api_sm", "rel_rep_api_pm2", "spot_chain", "forward_chain", "sigma_chain", "rate_chain", "ticker_ts",
    "block", "params_sm", "params_pm2", "error"]
INT_COLUMNS = ("ts", "ticker_ts", "block", "type_n")
NAN = float("nan")


# ================================================================================================ buckets (Paper 1)

def delta_bucket(abs_delta_pct) -> Optional[str]:
    """Paper 1 |delta| bucket of ``abs_delta_pct`` (percent), left-closed as ``pd.cut(..., right=False)``."""
    x = float(abs_delta_pct)
    if not math.isfinite(x):
        return None
    for i, lab in enumerate(DELTA_LABELS):
        if DELTA_EDGES[i] <= x < DELTA_EDGES[i + 1]:
            return lab
    return None


def tenor_bucket(days) -> Optional[str]:
    """Paper 1 tenor bucket of ``days``, right-closed and the first bucket including 0."""
    x = float(days)
    if not (x >= 0):
        return None
    for i, lab in enumerate(TENOR_LABELS):
        if (TENOR_EDGES_D[i] < x or (i == 0 and x == TENOR_EDGES_D[0])) and x <= TENOR_EDGES_D[i + 1]:
            return lab
    return None


def delta_mid(label: str) -> float:
    i = DELTA_LABELS.index(label)
    return (DELTA_EDGES[i] + min(DELTA_EDGES[i + 1], 100.0)) / 2.0


def tenor_mid(label: str, max_days: float) -> float:
    """Bucket mid in days; the open bucket (> 90 d) ends at the longest listed expiry."""
    i = TENOR_LABELS.index(label)
    hi = TENOR_EDGES_D[i + 1]
    return (TENOR_EDGES_D[i] + (float(max_days) if math.isinf(hi) else hi)) / 2.0


def choose_expiry(tenors: Mapping[int, float], label: str, min_left_days: float = MIN_LEFT_S / DAY) -> Optional[int]:
    """The expiry (key of ``tenors``: expiry -> days left) in tenor bucket ``label`` nearest to its mid; ties: the
    earlier expiry. Expiries with less than 30 min left are not eligible."""
    ok = {int(e): float(d) for e, d in tenors.items() if float(d) >= min_left_days}
    if not ok:
        return None
    target = tenor_mid(label, max(ok.values()))
    inside = [(abs(d - target), e) for e, d in ok.items() if tenor_bucket(d) == label]
    return min(inside)[1] if inside else None


# ================================================================================================ tickers and choice

def _f(x) -> float:
    if x is None or x == "":
        return NAN
    try:
        return float(x)
    except (TypeError, ValueError):
        return NAN


def ticker_fields(t: Mapping) -> dict:
    """Mark, index, forward delta, forward and mark IV of a slim ticker (``get_tickers``)."""
    op = t.get("option_pricing") or {}
    ts = t.get("t")
    return {"mark": _f(t.get("M")), "index": _f(t.get("I")), "delta": _f(op.get("d")), "forward": _f(op.get("f")),
            "iv": _f(op.get("i")), "ticker_ts": int(ts) if ts is not None else None}


CAND_COLUMNS = ["instrument", "expiry", "strike", "is_call", "delta", "mark", "index", "forward", "iv", "ticker_ts"]


def candidates(instruments: Sequence[Mapping], tickers: Mapping[str, Mapping]) -> pd.DataFrame:
    """Active listed options (``get_instruments``) that also have a ticker, in the order of the list."""
    rows = []
    for inst in instruments:
        name = inst.get("instrument_name")
        if not inst.get("is_active") or inst.get("instrument_type", "option") != "option" or name not in tickers:
            continue
        od = inst["option_details"]
        tf = ticker_fields(tickers[name])
        rows.append({"instrument": name, "expiry": int(od["expiry"]), "strike": float(od["strike"]),
                     "is_call": od["option_type"] == "C", **{k: tf[k] for k in CAND_COLUMNS[4:]}})
    return pd.DataFrame(rows, columns=CAND_COLUMNS)


def choose_instrument(cands: pd.DataFrame, label: str, is_call: bool) -> Optional[dict]:
    """The candidate of the type whose |delta| is nearest to the bucket mid and inside the bucket; ties: the smaller
    strike (distances rounded to 1e-9 percentage points against float noise)."""
    if cands.empty:
        return None
    c = cands[(cands["is_call"].astype(bool) == bool(is_call)) & np.isfinite(cands["delta"].astype(float))
              & np.isfinite(cands["mark"].astype(float))]
    if c.empty:
        return None
    absd = 100.0 * np.abs(c["delta"].to_numpy(dtype=float))
    inside = np.array([delta_bucket(x) == label for x in absd], dtype=bool)
    if not inside.any():
        return None
    c = c[inside].assign(_dist=np.round(np.abs(absd[inside] - delta_mid(label)), 9))
    return c.sort_values(["_dist", "strike"], kind="mergesort").iloc[0].drop("_dist").to_dict()


def cell_types(frame: pd.DataFrame) -> Dict[Tuple[str, str, str, str], Tuple[str, float, int]]:
    """Majority option type of the Paper 1 fills per cell (currency, maker side, |delta| bucket, tenor bucket) in the
    PM2 window: ``{cell: (type, share of that type, fills)}``; ties give the call."""
    out = {}
    for ccy, start in capital.WINDOW_START["pm2"].items():
        f = frame[(frame["currency"] == ccy) & (frame["ts"].to_numpy() >= int(start) * 1000)]
        if f.empty:
            continue
        g = f.groupby(["maker_side", "delta_bucket", "tenor_bucket", "option_type"]).size().unstack(fill_value=0)
        for (side, d, ten), r in g.iterrows():
            n_c, n_p = int(r.get("C", 0)), int(r.get("P", 0))
            n = n_c + n_p
            if n == 0:
                continue
            typ = "C" if n_c >= n_p else "P"
            out[(ccy, "buy" if side > 0 else "sell", str(d), str(ten))] = (typ, max(n_c, n_p) / n, n)
    return out


def cell_type(types: Mapping, ccy: str, side: str, d: str, ten: str) -> Tuple[str, float, int]:
    return types.get((ccy, side, d, ten), ("C", NAN, 0))


def load_cell_types(path: Path = MARKOUTS) -> Dict[Tuple[str, str, str, str], Tuple[str, float, int]]:
    cols = ["currency", "maker_side", "option_type", "delta_bucket", "tenor_bucket", "ts"]
    return cell_types(pd.read_parquet(path, columns=cols))


# ================================================================================================ API side

def margin_request(margin_type: str, ccy: str, name: str) -> dict:
    """One ``get_margin`` for both sides: pre = net(+1), post = net(+1 - 2) = net(-1), no collateral."""
    return {"margin_type": margin_type, "market": ccy,
            "simulated_positions": [{"instrument_name": name, "amount": "1"}],
            "simulated_collaterals": [],
            "simulated_position_changes": [{"instrument_name": name, "amount": "-2"}]}


def api_nets(result: Mapping) -> Tuple[float, float]:
    """(net_IM(+1), net_IM(-1)) from ``pre_initial_margin`` and ``post_initial_margin``."""
    return float(result["pre_initial_margin"]), float(result["post_initial_margin"])


def capital_pair(mark: float, net_buy: float, net_sell: float) -> Tuple[float, float]:
    """(K(+1), K(-1)) with K = p q - net(q; C = 0)."""
    return float(mark) - float(net_buy), -float(mark) - float(net_sell)


class Throttle:
    """At most ``rate`` request starts per second, shared by every client that calls :meth:`wait`.

    Consecutive starts are at least ``(1 + margin) / rate`` apart on the clock read *after* sleeping, so a late
    wake-up never shortens the next gap (three starts never fall into one second)."""

    def __init__(self, rate: float = RATE, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep, margin: float = 0.01):
        self.gap = (1.0 + float(margin)) / float(rate)
        self.clock, self.sleep = clock, sleep
        self._next = -math.inf
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = self.clock()
            while now < self._next:
                self.sleep(self._next - now)
                now = self.clock()
            self._next = now + self.gap


class ApiError(RuntimeError):
    """A JSON-RPC error of the Derive API."""

    def __init__(self, method: str, error):
        self.method, self.error = method, error
        super().__init__(f"{method}: {error}")


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def _append(path: Optional[Path], row: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


class ApiClient:
    """Public REST client for ``api.lyra.finance`` with User-Agent, shared throttle, retries on 429/5xx and a JSONL log
    of every attempt with the raw answer."""

    def __init__(self, base_url: str = API_URL, session=None, throttle: Optional[Throttle] = None,
                 log_path: Optional[Path] = LOG_PATH, sleep: Callable[[float], None] = time.sleep,
                 max_retries: int = 6, timeout: float = 60.0, user_agent: str = USER_AGENT):
        if session is None:
            import requests

            session = requests.Session()
        self.session = session
        self.session.headers["User-Agent"] = user_agent
        self.base_url = base_url.rstrip("/")
        self.throttle = throttle or Throttle()
        self.log_path = Path(log_path) if log_path else None
        self.sleep, self.max_retries, self.timeout = sleep, max_retries, timeout
        self.n_requests = 0

    def call(self, method: str, **params):
        delay = 1.0
        for _ in range(self.max_retries):
            self.throttle.wait()
            ts = _utc_now()
            try:
                resp = self.session.post(f"{self.base_url}/public/{method}", json=params, timeout=self.timeout)
                status, text = int(resp.status_code), resp.text
            except Exception as exc:  # network error: retry
                status, text = -1, repr(exc)
            self.n_requests += 1
            _append(self.log_path, {"ts": ts, "host": self.base_url, "method": f"public/{method}", "params": params,
                                    "http_status": status, "raw": text})
            payload = None
            if status == 200:
                try:
                    payload = json.loads(text)
                except ValueError:
                    payload = None
            if payload is not None:
                if "error" not in payload:
                    return payload["result"]
                msg = json.dumps(payload["error"]).lower()
                if not ("rate" in msg and "limit" in msg):
                    raise ApiError(method, payload["error"])
            elif 0 < status < 500 and status not in (200, 429):
                raise ApiError(method, {"http_status": status, "body": text[:500]})
            self.sleep(delay)
            delay = min(2 * delay, 30.0)
        raise RuntimeError(f"{method}: giving up after {self.max_retries} attempts")


class SharedRpc(Rpc):
    """:class:`p2chain.Rpc` that waits on a shared :class:`Throttle` and counts its requests."""

    def __init__(self, throttle: Throttle, client=None, url: str = RPC_URL, log_path: Optional[Path] = LOG_PATH):
        if client is None:
            client = ChainClient(url=url)
            client.session.headers["User-Agent"] = USER_AGENT
        super().__init__(client=client, url=url, rate=1e9, log_path=log_path)
        self.url = url
        self.shared = throttle
        self.n_requests = 0
        self._start: Optional[str] = None

    def _throttle(self) -> None:
        self.shared.wait()
        self._start = _utc_now()   # the log carries the start of the request, as ApiClient does

    def _log(self, method: str, params, result) -> None:
        _append(self.log_path, {"ts": self._start, "host": self.url, "method": method, "params": params,
                                "result": result if isinstance(result, (str, int, float)) or result is None
                                else f"<{type(result).__name__}>"})

    def raw(self, method: str, params: list):
        self.n_requests += 1
        return super().raw(method, params)


# ================================================================================================ chain side

SIGNATURES = {
    "getBlockNumber": "getBlockNumber()",                      # Multicall3
    "getCurrentBlockTimestamp": "getCurrentBlockTimestamp()",  # Multicall3
    "getSpot": "getSpot()",
    "getForwardPricePortions": "getForwardPricePortions(uint64)",
    "getVol": "getVol(uint128,uint64)",
    "getInterestRate": "getInterestRate(uint64)",
    "getMargin": "getMargin(uint256,bool)",
}
SEL = {name: p2validate.selector(sig).hex() for name, sig in SIGNATURES.items()}
CALL_NAMES = ["getBlockNumber", "getCurrentBlockTimestamp", "getSpot", "getForwardPricePortions", "getVol",
              "getInterestRate", "getSpot:stable", "getMargin:sm_buy", "getMargin:sm_sell", "getMargin:pm2_buy",
              "getMargin:pm2_sell"]


def _w(x: int) -> bytes:
    return (int(x) % (1 << 256)).to_bytes(32, "big")


def _cd(name: str, *args: int) -> bytes:
    return bytes.fromhex(SEL[name]) + b"".join(_w(a) for a in args)


def chain_calls(ccy: str, expiry: int, strike: float, is_call: bool) -> Tuple[List[Tuple[str, bytes]], dict]:
    """Multicall3 calls (order :data:`CALL_NAMES`) and the ``SubAccounts`` state override for one instrument."""
    f = FEEDS[ccy]
    e = int(expiry)
    sub = books.encode_option_subid(e, strike, is_call)
    asset = p2validate.OPTION_ASSET[ccy]
    override = p2validate.state_override({ACC_BUY: [(asset, sub, E18)], ACC_SELL: [(asset, sub, -E18)]})
    pm2 = PM2_ADDR[ccy]["manager"]
    calls = [(books.MULTICALL3, _cd("getBlockNumber")), (books.MULTICALL3, _cd("getCurrentBlockTimestamp")),
             (f["spot"], _cd("getSpot")), (f["forward"], _cd("getForwardPricePortions", e)),
             (f["vol"], _cd("getVol", p2validate.strike_wei(strike), e)), (f["rate_pm2"], _cd("getInterestRate", e)),
             (p2validate.STABLE_FEED, _cd("getSpot")),
             (SRM, _cd("getMargin", ACC_BUY, 1)), (SRM, _cd("getMargin", ACC_SELL, 1)),
             (pm2, _cd("getMargin", ACC_BUY, 1)), (pm2, _cd("getMargin", ACC_SELL, 1))]
    return calls, override


def _word(data: bytes, i: int, signed: bool = False) -> int:
    v = int.from_bytes(data[32 * i:32 * i + 32], "big")
    return v - (1 << 256) if signed and v >> 255 else v


def decode_chain(res: Sequence[Tuple[bool, bytes]]) -> dict:
    """Values of :func:`chain_calls` (floats in USD, rates as decimals); ``None`` where a call reverted."""
    if len(res) != len(CALL_NAMES):
        raise ValueError(f"expected {len(CALL_NAMES)} results, got {len(res)}")
    ok = [bool(r[0]) and len(r[1]) >= 32 for r in res]
    out = {"failed": [n for n, good in zip(CALL_NAMES, ok) if not good]}

    def get(i, fn):
        return fn(res[i][1]) if ok[i] else None

    out["block"] = get(0, lambda b: _word(b, 0))
    out["block_ts"] = get(1, lambda b: _word(b, 0))
    out["spot"] = get(2, lambda b: _word(b, 0) / E18)
    out["spot_conf"] = get(2, lambda b: _word(b, 1) / E18)
    out["forward"] = get(3, lambda b: (_word(b, 0) + _word(b, 1)) / E18)
    out["fwd_fixed"] = get(3, lambda b: _word(b, 0) / E18)
    out["fwd_conf"] = get(3, lambda b: _word(b, 2) / E18)
    out["sigma"] = get(4, lambda b: _word(b, 0) / E18)
    out["vol_conf"] = get(4, lambda b: _word(b, 1) / E18)
    out["rate"] = get(5, lambda b: _word(b, 0, signed=True) / E18)
    out["rate_conf"] = get(5, lambda b: _word(b, 1) / E18)
    out["stable"] = get(6, lambda b: _word(b, 0) / E18)
    for i, key in zip(range(7, 11), ("net_sm_buy", "net_sm_sell", "net_pm2_buy", "net_pm2_sell")):
        out[key] = get(i, lambda b: _word(b, 0, signed=True) / E18)
    return out


def chain_snapshot(rpc, ccy: str, expiry: int, strike: float, is_call: bool) -> dict:
    """One ``eth_call`` at the head block with the calls of :func:`chain_calls`."""
    calls, override = chain_calls(ccy, expiry, strike, is_call)
    raw = rpc.raw("eth_call", [{"to": books.MULTICALL3, "data": books.encode_aggregate3(calls)}, "latest", override])
    return decode_chain(books.decode_aggregate3(bytes.fromhex(raw[2:])))


def _pair_arrays(spot, forward, sigma, tau, rate, strike, is_call, vol_conf, fwd_conf, spot_conf, rate_conf,
                 fwd_fixed, stable) -> Dict[str, np.ndarray]:
    two = np.ones(2)
    return {"spot": spot * two, "forward": forward * two, "sigma": sigma * two, "tau": max(tau, 0.0) * two,
            "rate": rate * two, "strike": float(strike) * two, "is_call": np.array([bool(is_call)] * 2),
            "amount": np.array([1.0, -1.0]), "vol_conf": vol_conf * two, "fwd_conf": fwd_conf * two,
            "spot_conf": spot_conf * two, "rate_conf": rate_conf * two, "fwd_fixed": fwd_fixed * two,
            "rate_pm": 0.0 * two, "stable": stable * two}


def _capital(mgr: str, arrays: Mapping, params: Mapping, mark: float) -> Tuple[float, float]:
    k, _ = capital.capital_single(mgr, arrays, params, np.array([float(mark)] * 2), True)
    return float(k[0]), float(k[1])


def replica_capital(ch: Mapping, expiry: int, strike: float, is_call: bool, mark: float,
                    params: Mapping[str, Mapping]) -> Dict[str, Tuple[float, float]]:
    """(K(+1), K(-1)) of the replica per manager on the chain feeds ``ch`` (:func:`decode_chain`); NaN where a feed
    the manager needs reverted. SM does not discount; PM2 uses the PM2 rate feed (Addendum 1, item 2)."""
    need = ("block_ts", "spot", "spot_conf", "forward", "fwd_fixed", "fwd_conf", "sigma", "vol_conf", "stable")
    out = {m: (NAN, NAN) for m in MANAGERS}
    if any(ch.get(k) is None for k in need) or not math.isfinite(float(mark)):
        return out
    tau = (int(expiry) - int(ch["block_ts"])) / YEAR
    for mgr in MANAGERS:
        rate, rate_conf = ch.get("rate"), ch.get("rate_conf")
        if mgr == "pm2" and (rate is None or rate_conf is None):
            continue
        a = _pair_arrays(ch["spot"], ch["forward"], ch["sigma"], tau, rate or 0.0, strike, is_call, ch["vol_conf"],
                         ch["fwd_conf"], ch["spot_conf"], rate_conf if rate_conf is not None else 1.0,
                         ch["fwd_fixed"], ch["stable"])
        out[mgr] = _capital(mgr, a, params[mgr], mark)
    return out


def replica_api_semantics(tick: Mapping, ts: float, expiry: int, strike: float, is_call: bool, mark: float,
                          params: Mapping[str, Mapping]) -> Dict[str, Tuple[float, float]]:
    """The replica in API semantics: index as spot, ticker forward, mark IV, PM2 rate :data:`API_RATE`, all
    confidences 1, time to expiry from ``ts`` (seconds)."""
    vals = [float(tick.get(k, NAN)) for k in ("index", "forward", "iv")] + [float(mark)]
    if not all(math.isfinite(v) for v in vals):
        return {m: (NAN, NAN) for m in MANAGERS}
    spot, fwd, iv, _ = vals
    a = _pair_arrays(spot, fwd, iv, (int(expiry) - float(ts)) / YEAR, API_RATE, strike, is_call, 1.0, 1.0, 1.0, 1.0,
                     0.0, 1.0)
    return {mgr: _capital(mgr, a, params[mgr], mark) for mgr in MANAGERS}


def rel_diff(a, b) -> float:
    """a / b - 1; NaN if either is not finite or b is 0."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return NAN
    if not (math.isfinite(a) and math.isfinite(b)) or b == 0:
        return NAN
    return a / b - 1.0


# ================================================================================================ the snapshot

class TimelineParams:
    """``(params, from_utc)`` of the standard lib in force at ``ts`` from ``results/p2/params`` (cached)."""

    def __init__(self, root: Optional[Path] = None):
        self.root = root
        self._tl: Dict[Tuple[str, str], Timeline] = {}

    def __call__(self, ccy: str, mgr: str, ts: int) -> Tuple[Mapping, str]:
        key = (ccy, mgr)
        if key not in self._tl:
            self._tl[key] = Timeline(ccy, mgr, root=self.root)
        e = self._tl[key].entry_at(int(ts))
        return e["params"], e["from_utc"]


def measure_instrument(api, rpc, ccy: str, cand: Mapping, params_at: Callable, clock: Callable[[], float]) -> dict:
    """API (SM, PM2) and chain for one instrument, both sides; see the module docstring."""
    name, e, k, is_call = cand["instrument"], int(cand["expiry"]), float(cand["strike"]), bool(cand["is_call"])
    mark = float(cand["mark"])
    t_api = float(clock())
    out = {"ts": int(round(t_api * 1000)), "errors": []}
    for mgr in MANAGERS:
        try:
            nets = api_nets(api.call("get_margin", **margin_request(MARGIN_TYPE[mgr], ccy, name)))
            out[f"K_api_{mgr}"] = capital_pair(mark, *nets)
        except ApiError as exc:
            out[f"K_api_{mgr}"] = (NAN, NAN)
            out["errors"].append(f"api {MARGIN_TYPE[mgr]}: {json.dumps(exc.error)[:160]}")
    ch = None
    try:
        ch = chain_snapshot(rpc, ccy, e, k, is_call)
    except (RpcError, ValueError) as exc:
        out["errors"].append(f"chain: {str(exc)[:160]}")
    out["chain"] = ch
    ts_params = int(ch["block_ts"]) if ch and ch.get("block_ts") is not None else int(t_api)
    params, out["params_from"] = {}, {}
    for mgr in MANAGERS:
        params[mgr], out["params_from"][mgr] = params_at(ccy, mgr, ts_params)
    if ch is not None:
        if ch["failed"]:
            out["errors"].append("chain revert: " + ", ".join(ch["failed"]))
        out["K_chain"] = replica_capital(ch, e, k, is_call, mark, params)
        out["K_oracle"] = {mgr: tuple(mark * q - ch[f"net_{mgr}_{s}"] if ch[f"net_{mgr}_{s}"] is not None else NAN
                                      for s, q in SIDES) for mgr in MANAGERS}
    else:
        out["K_chain"] = {m: (NAN, NAN) for m in MANAGERS}
        out["K_oracle"] = {m: (NAN, NAN) for m in MANAGERS}
    out["K_rep_api"] = replica_api_semantics(cand, t_api, e, k, is_call, mark, params)
    return out


def _status(m: Optional[dict]) -> str:
    if any(err.startswith("api") for err in m["errors"]):
        return "api_error"
    if m["chain"] is None:
        return "chain_error"
    if m["chain"]["failed"]:
        return "chain_revert"
    vals = [m[f"K_{w}_{mgr}"] if w == "api" else m[f"K_{w}"][mgr] for w in ("api", "chain") for mgr in MANAGERS]
    return "ok" if all(math.isfinite(x) for pair in vals for x in pair) else "nan"


def _row(ccy, side, d, ten, status, typ, share, n) -> dict:
    row = {c: NAN for c in CSV_COLUMNS}
    row.update({"ccy": ccy, "side": side, "delta_bucket": d, "tenor_bucket": ten, "instrument": None,
                "status": status, "option_type": typ, "type_share": share, "type_n": n, "ts": None,
                "ticker_ts": None, "block": None, "params_sm": None, "params_pm2": None, "error": None})
    return row


def _full_row(ccy, side, q, d, ten, typ, share, n, cand, m, t0) -> dict:
    i = 0 if q > 0 else 1
    row = _row(ccy, side, d, ten, _status(m), typ, share, n)
    ch = m["chain"] or {}
    row.update({"instrument": cand["instrument"], "strike": float(cand["strike"]),
                "tenor_days": (int(cand["expiry"]) - float(t0)) / DAY, "delta": float(cand["delta"]),
                "mark": float(cand["mark"]), "index": float(cand["index"]), "forward_api": float(cand["forward"]),
                "iv_api": float(cand["iv"]), "ts": m["ts"], "ticker_ts": cand["ticker_ts"], "block": ch.get("block"),
                "spot_chain": ch.get("spot"), "forward_chain": ch.get("forward"), "sigma_chain": ch.get("sigma"),
                "rate_chain": ch.get("rate"), "params_sm": m["params_from"]["sm"],
                "params_pm2": m["params_from"]["pm2"], "error": "; ".join(m["errors"]) or None})
    for mgr in MANAGERS:
        row[f"K_api_{mgr}"] = m[f"K_api_{mgr}"][i]
        row[f"K_chain_{mgr}"] = m["K_chain"][mgr][i]
        row[f"K_oracle_{mgr}"] = m["K_oracle"][mgr][i]
        row[f"K_rep_api_{mgr}"] = m["K_rep_api"][mgr][i]
        row[f"rel_diff_{mgr}"] = rel_diff(row[f"K_api_{mgr}"], row[f"K_chain_{mgr}"])
        row[f"rel_oracle_{mgr}"] = rel_diff(row[f"K_chain_{mgr}"], row[f"K_oracle_{mgr}"])
        row[f"rel_rep_api_{mgr}"] = rel_diff(row[f"K_api_{mgr}"], row[f"K_rep_api_{mgr}"])
    return row


def snapshot_ccy(ccy: str, api, rpc, types: Mapping, params_at: Callable, clock: Callable[[], float] = time.time
                 ) -> List[dict]:
    """All 70 cells of one currency (rows also for cells without an instrument, with their status)."""
    insts = [i for i in api.call("get_instruments", currency=ccy, instrument_type="option", expired=False)
             if i.get("is_active") and i.get("instrument_type", "option") == "option"]
    t0 = float(clock())
    tenors = {int(i["option_details"]["expiry"]): (int(i["option_details"]["expiry"]) - t0) / DAY for i in insts}
    rows: List[dict] = []
    for ten in TENOR_LABELS:
        e = choose_expiry(tenors, ten)
        if e is None:
            for side, _ in SIDES:
                for d in DELTA_LABELS:
                    rows.append(_row(ccy, side, d, ten, "no_expiry", *cell_type(types, ccy, side, d, ten)))
            continue
        tick = api.call("get_tickers", currency=ccy, instrument_type="option", expiry_date=expiry_date_str(e))
        cands = candidates([i for i in insts if int(i["option_details"]["expiry"]) == e], tick["tickers"])
        measured: Dict[str, dict] = {}
        for side, q in SIDES:
            for d in DELTA_LABELS:
                typ, share, n = cell_type(types, ccy, side, d, ten)
                cand = choose_instrument(cands, d, typ == "C")
                if cand is None:
                    rows.append(_row(ccy, side, d, ten, "no_strike", typ, share, n))
                    continue
                name = cand["instrument"]
                if name not in measured:
                    measured[name] = measure_instrument(api, rpc, ccy, cand, params_at, clock)
                rows.append(_full_row(ccy, side, q, d, ten, typ, share, n, cand, measured[name], t0))
    return rows


def to_frame(rows: Sequence[dict]) -> pd.DataFrame:
    df = pd.DataFrame(list(rows), columns=CSV_COLUMNS)
    order = {"ccy": list(CCYS), "side": [s for s, _ in SIDES], "delta_bucket": DELTA_LABELS,
             "tenor_bucket": TENOR_LABELS}
    keys = [df[c].map({v: i for i, v in enumerate(vals)}).fillna(len(vals)) for c, vals in order.items()]
    df = df.iloc[np.lexsort(tuple(reversed([k.to_numpy() for k in keys])))].reset_index(drop=True)
    for c in INT_COLUMNS:
        df[c] = pd.to_numeric(df[c], errors="coerce").round().astype("Int64")
    return df


# ================================================================================================ document text

THOUSANDS = ","
MINUS = "−"
MISSING = "n/a"
SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _finite(x) -> bool:
    try:
        return math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def fmt_num(x, digits: int = 2, sign: bool = False) -> str:
    """Decimal point, comma for thousands, typographic minus."""
    if not _finite(x):
        return MISSING
    v = round(float(x), digits)
    body = f"{abs(v):,.{digits}f}".replace(",", THOUSANDS)
    if v < 0:
        return MINUS + body
    return ("+" + body) if (sign and v > 0) else body


def fmt_pct(x, digits: int = 2, sign: bool = True) -> str:
    return MISSING if not _finite(x) else fmt_num(100.0 * float(x), digits, sign) + " %"


def fmt_sci(x, n: int = 2) -> str:
    """n significant digits; very small or large numbers as m·10ⁿ."""
    if not _finite(x):
        return MISSING
    v = float(x)
    if v == 0:
        return "0"
    ex = int(math.floor(math.log10(abs(v))))
    if -3 <= ex <= 5:
        return fmt_num(v, max(0, n - 1 - ex))
    m = v / 10 ** ex
    if round(abs(m), n - 1) >= 10:
        m, ex = m / 10, ex + 1
    return fmt_num(m, n - 1) + "·10" + str(ex).translate(SUPERSCRIPT)


def _q(s: pd.Series, p: float) -> float:
    s = pd.to_numeric(s, errors="coerce").dropna()
    return float(s.quantile(p)) if len(s) else NAN


def _med(s: pd.Series) -> float:
    return _q(s, 0.5)


SIDE_NAME = {"buy": "buy", "sell": "sell"}
MGR_NAME = {"sm": "SM", "pm2": "PM2"}
N_TOP = 8
STATUS_TEXT = {"ok": "measured", "no_expiry": "no listed expiry in the tenor bucket",
               "no_strike": "no strike of the type in the |Δ| bucket", "api_error": "error of the API",
               "chain_error": "eth_call failed", "chain_revert": "chain feed reverted",
               "nan": "value not finite"}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December")  # not strftime("%B"), which follows the locale (de_DE on the author's machine)


def _repo_rel(p: Path) -> str:
    """``p`` relative to the repository as the code names it (no symlink resolved), else as given."""
    try:
        return Path(p).relative_to(REPO).as_posix()
    except ValueError:
        return str(p)


TYPES_SOURCES = ("markouts", "given")  # values of the meta field types_source: keys, never document text


def types_source_key(value) -> Optional[str]:
    """Key of the meta field ``types_source``. A meta file written before the keys held the document text itself
    (the run of 25 September 2026: the path of the Paper 1 markouts and a German description); it is read by the
    path."""
    text = "" if value is None else str(value).strip()
    if text in TYPES_SOURCES:
        return text
    return "markouts" if "markouts.parquet" in text else None


def types_source_text(value) -> str:
    """The English text of ``types_source`` in the document, whatever run wrote the meta file."""
    key = types_source_key(value)
    if key == "markouts":
        return f"`{_repo_rel(MARKOUTS)}` (maker side, |Δ| and tenor bucket, PM2 window)"
    if key == "given":
        return "given by the caller of `run`"
    return MISSING


def _utc(iso: Optional[str]) -> Optional[dt.datetime]:
    if not iso:
        return None
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def _utc_day(iso: Optional[str]) -> str:
    """'25 September 2026'."""
    t = _utc(iso)
    return MISSING if t is None else f"{t.day} {MONTHS[t.month - 1]} {t.year}"


def _utc_text(iso: Optional[str]) -> str:
    """'25 September 2026 00:44:17'."""
    t = _utc(iso)
    return MISSING if t is None else f"{_utc_day(iso)} {t:%H:%M:%S}"


def _table(header: Sequence[str], rows: Sequence[Sequence[str]], align: Sequence[str]) -> List[str]:
    def line(cells):
        return "| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |"
    out = [line(header), "|" + "|".join("---:" if a == "r" else "---" for a in align) + "|"]
    return out + [line(r) for r in rows]


def render_doc(df: pd.DataFrame, meta: Mapping) -> str:
    """The section ``docs/paper2/status/C5b.md``, only from the CSV and the meta file."""
    ok = df[df["status"] == "ok"]
    n_cells, n_ok = len(df), len(ok)
    blocks = pd.to_numeric(df["block"], errors="coerce").dropna()
    day = _utc_day(meta.get("start_utc"))
    L: List[str] = []
    L.append("## C5b API snapshot: `public/get_margin` against the replica at the current block")
    L.append("")
    L.append(f"Status as of {day}. **Exploratory:** the pre-registration lists \"API semantics with 2 %\" among the "
             "exploratory quantities. The v2 API computes off-chain with ticker prices and a flat PM2 discount of 2 % "
             "(`docs/paper2/get_margin_semantics.md`, section 3); its history cannot be reconstructed, so only today "
             "is measured. No accounts: all books are simulated (API: `simulated_positions`; chain: two synthetic "
             "accounts via state override). No inference, no input to H1 to H4. Tests: `tests/test_p2_api.py` "
             "(offline, API and chain as mocks, replica on `results/p2/params`).")
    L.append("")
    L.append("### Run")
    L.append("")
    req = meta.get("requests", {})
    L.append(f"- Time: {_utc_text(meta.get('start_utc'))} to {_utc_text(meta.get('end_utc'))} UTC; blocks "
             f"{fmt_num(blocks.min(), 0) if len(blocks) else MISSING} to "
             f"{fmt_num(blocks.max(), 0) if len(blocks) else MISSING}.")
    L.append(f"- Requests: {fmt_num(req.get('api'), 0)} to `{meta.get('api_host', API_URL)}` and "
             f"{fmt_num(req.get('rpc'), 0)} `eth_call` to `{meta.get('rpc_url', RPC_URL)}`, together at most "
             f"{fmt_num(meta.get('rate_per_s', RATE), 0)} per second (measured in the log: at most "
             f"{fmt_num(meta.get('max_requests_in_1s'), 0)} starts in a window of 1 s), "
             f"user agent `{meta.get('user_agent', USER_AGENT)}`. "
             f"Log with all responses, instrument lists and tickers included: "
             f"`{meta.get('log', 'data/p2/logs/C5b.jsonl')}`.")
    params = meta.get("params", {})
    if params:
        parts = [f"{c} SM from {v.get('sm', MISSING)}, PM2 from {v.get('pm2', MISSING)}" for c, v in params.items()]
        L.append("- Parameters (standard lib, `results/p2/params`, valid entry): " + "; ".join(parts) + " UTC.")
    L.append(f"- Type choice from: {types_source_text(meta.get('types_source'))}.")
    L.append(f"- Result: `results/p2/api_snapshot.csv` ({n_cells} rows, one per cell), metadata "
             f"`{meta.get('meta', 'data/p2/api_snapshot/meta.json')}`.")
    L.append("")
    L.append("### Decisions")
    L.append("")
    L.append("1. **Cells:** underlying × maker side (buy, sell) × 7 |Δ| buckets × 5 tenor buckets of "
             "the Paper 1 map, that is 70 cells per underlying.")
    L.append("2. **Expiry:** among the listed, active expiries with at least 30 min to expiry, the one whose time to "
             "expiry lies in the bucket and is closest to the bucket midpoint (1, 4.5, 18.5, 60 days; for > 90 days "
             "the midpoint between 90 days and the longest listed expiry). Tie: the earlier one.")
    L.append("3. **Type:** call or put, whichever type is more frequent among the Paper 1 fills of the same cell in "
             "the PM2 window (tie or no fills: call). The pre-registration fixes no type; this way the instrument is "
             "representative of the cell of the map.")
    L.append("4. **Strike:** the active instrument of this type and expiry with a ticker whose |Δ| (ticker delta, "
             "forward delta as in Paper 1) is closest to the bucket midpoint (5, 17.5, 32.5, 50, 67.5, 82.5, 95 %) "
             "and lies in the bucket. Tie: the smaller strike.")
    L.append("5. **Price:** p = ticker mark from `get_tickers` of the expiry, read directly before the measurements "
             "of its instruments.")
    L.append("6. **K_api** = p·q − net_IM(q; C = 0) from `get_margin` with `market` = underlying under SM and "
             "under PM2, one request per instrument and manager: `simulated_positions` q = +1, "
             "`simulated_position_changes` −2, no collateral. `pre` is net(+1), `post` net(−1), both at the "
             "same prices.")
    L.append("7. **K_chain** = p·q − net_IM(q; C = 0) from the replica (`margin_sm`, `margin_pm2`, path of "
             "B2) with the on-chain feeds at the current block: one `eth_call` via Multicall3 returns block, block "
             "time, `getSpot`, `getForwardPricePortions`, `getVol` at the strike, the PM2 rate and the stable feed. "
             "PM2 with the rate feed, SM without discounting. The same price p as for K_api; time to expiry from the "
             "block time.")
    L.append("8. **Cross-check K_oracle:** the same multicall calls `getMargin(account, true)` of StandardManager and "
             "PMRM_2 for two synthetic accounts with +1 and −1 contract (state override of `SubAccounts` as in "
             "B1).")
    L.append("9. **Replica in API semantics K_rep_api:** replica with the index as spot, ticker forward, mark IV, "
             "PM2 rate 2 % and confidences 1, time to expiry from the time of the API request.")
    L.append("10. **Deviation:** rel = K_api / K_chain − 1 (sign: positive means the API binds more capital). "
             "The price p cancels out of K_api − K_chain; it acts only through the denominator.")
    L.append("")
    L.append("### Coverage")
    L.append("")
    counts = df["status"].value_counts()
    L.append(f"- {n_ok} of {n_cells} cells measured, {ok['instrument'].nunique()} distinct instruments.")
    for st in ("no_expiry", "no_strike", "api_error", "chain_error", "chain_revert", "nan"):
        if counts.get(st, 0):
            n_st = int(counts[st])
            L.append(f"- {STATUS_TEXT[st]}: {n_st} {'cell' if n_st == 1 else 'cells'}.")
    if len(ok):
        miss = df[df["status"] == "no_expiry"].groupby("ccy")["tenor_bucket"].unique()
        for ccy, tens in miss.items():
            L.append(f"- {ccy} without an expiry in: {', '.join(sorted(set(tens), key=TENOR_LABELS.index))}.")
    L.append("")
    L.append("### K_api against K_chain")
    L.append("")
    rows = []
    for ccy in CCYS:
        for side, _ in SIDES:
            for mgr in MANAGERS:
                s = ok[(ok["ccy"] == ccy) & (ok["side"] == side)][f"rel_diff_{mgr}"]
                if not len(s):
                    continue
                rows.append([ccy, SIDE_NAME[side], MGR_NAME[mgr], str(len(s)), fmt_pct(_med(s), 3),
                             fmt_pct(s.min(), 3), fmt_pct(s.max(), 3), fmt_pct(_med(s.abs()), 3, sign=False)])
    L += _table(["Underlying", "Side", "Manager", "Cells", "Median rel", "Minimum", "Maximum", "Median |rel|"],
                rows, ["l", "l", "l", "r", "r", "r", "r", "r"])
    L.append("")
    buy = ok[ok["side"] == "buy"]
    if len(buy):
        exact = ((buy["K_api_sm"] == buy["mark"]) & (buy["K_chain_sm"] == buy["mark"])).sum()
        L.append(f"SM, buy: in {int(exact)} of {len(buy)} cells K_api = K_chain = p exactly; SM gives a long option "
                 "no credit, and the capital is the premium.")
        L.append("")
    L.append("Median of rel per tenor bucket over all underlyings and |Δ| buckets:")
    L.append("")
    rows = []
    for ten in TENOR_LABELS:
        for side, _ in SIDES:
            s = ok[(ok["tenor_bucket"] == ten) & (ok["side"] == side)]
            if not len(s):
                continue
            rows.append([ten, SIDE_NAME[side], str(len(s)), fmt_pct(_med(s["rel_diff_sm"]), 3),
                         fmt_pct(_med(s["rel_diff_pm2"]), 3)])
    L += _table(["Tenor", "Side", "Cells", "SM", "PM2"], rows, ["l", "l", "r", "r", "r"])
    L.append("")
    if len(ok):
        top = ok.assign(_a=ok[["rel_diff_sm", "rel_diff_pm2"]].abs().max(axis=1))
        top = top.sort_values(["_a", "ccy", "instrument", "side"], ascending=[False, True, True, True]).head(N_TOP)
        L.append(f"Largest deviations ({len(top)} cells with the largest |rel| over both managers):")
        L.append("")
        rows = []
        for r in top.itertuples():
            mgr = "sm" if abs(r.rel_diff_sm) >= abs(r.rel_diff_pm2) else "pm2"
            rows.append([f"{r.ccy}, {SIDE_NAME[r.side]}, {r.delta_bucket}, {r.tenor_bucket}", f"`{r.instrument}`",
                         MGR_NAME[mgr], fmt_num(r.mark, 2), fmt_num(getattr(r, f"K_api_{mgr}"), 2),
                         fmt_num(getattr(r, f"K_chain_{mgr}"), 2), fmt_pct(getattr(r, f"rel_diff_{mgr}"), 3),
                         fmt_pct(getattr(r, f"rel_rep_api_{mgr}"), 3)])
        L += _table(["Cell", "Instrument", "Manager", "p", "K_api", "K_chain", "rel", "K_api/K_rep_api − 1"], rows,
                    ["l", "l", "l", "r", "r", "r", "r", "r"])
        L.append("")
    L.append("### Cross-checks")
    L.append("")
    rows = []
    for mgr in MANAGERS:
        o = ok[f"rel_oracle_{mgr}"].abs()
        r = ok[f"rel_rep_api_{mgr}"]
        rows.append([MGR_NAME[mgr], str(int(o.notna().sum())), fmt_sci(_med(o)), fmt_sci(o.max()),
                     fmt_pct(_med(r), 3), fmt_pct(_med(r.abs()), 3, sign=False), fmt_pct(r.abs().max(), 3, sign=False)])
    L += _table(["Manager", "Cells", "Median |K_chain/K_oracle − 1|", "Max", "Median K_api/K_rep_api − 1",
                 "Median |…|", "Max |…|"], rows, ["l", "r", "r", "r", "r", "r", "r"])
    L.append("")
    L.append("Feeds per underlying (median over the measured instruments): ticker against chain at the same "
             "instrument.")
    L.append("")
    rows = []
    inst = ok.drop_duplicates(["ccy", "instrument"])
    for ccy in CCYS:
        s = inst[inst["ccy"] == ccy]
        if not len(s):
            continue
        spot = 1e4 * (s["index"] / s["spot_chain"] - 1)
        fwd = 1e4 * (s["forward_api"] / s["forward_chain"] - 1)
        vol = 100 * (s["iv_api"] - s["sigma_chain"])
        rows.append([ccy, str(len(s)), fmt_num(_med(spot), 1, True), fmt_num(_med(fwd), 1, True),
                     fmt_num(_med(vol), 2, True), fmt_pct(_med(s["rate_chain"]), 2, sign=False)])
    L += _table(["Underlying", "Instruments", "Index/spot − 1 (bp)", "Forward ticker/chain − 1 (bp)",
                 "Mark IV − chain vol (vol points)", "PM2 rate feed"], rows, ["l", "r", "r", "r", "r", "r"])
    L.append("")
    L.append("### Limitations")
    L.append("")
    L.append("- A snapshot of one point in time with one instrument per cell; no statement about the sample of "
             "Paper 2 and no inference.")
    L.append("- K_api − K_chain mixes three causes: the API's flat 2 % discount against the rate feed, ticker "
             "prices against the lagging on-chain feeds, and any differences of the off-chain engine. K_rep_api "
             "separates the first and second part from the third.")
    L.append("- API and chain are read per instrument in three requests shortly after one another (gap ≥ 0.5 s); "
             "price moves in between enter rel.")
    L.append("- The parameters come from `results/p2/params` (state of the last load run); K_oracle shows whether "
             "they still apply at the current block.")
    L.append("")
    L.append("### Interfaces")
    L.append("")
    L.append("- `derive_surface/p2api.py`: `run(ccys, ...)`, `snapshot_ccy`, `measure_instrument`, `chain_calls`, "
             "`decode_chain`, `replica_capital`, `replica_api_semantics`, `choose_expiry`, `choose_instrument`, "
             "`cell_types`, `render_doc`; `ApiClient` and `SharedRpc` share a `Throttle` (2 per second).")
    L.append("- CLI: `python3 -m derive_surface p2 api run [--ccy BTC ETH HYPE]` and `p2 api report` (document "
             "rebuilt from the CSV and the metadata). Not a heavy run (reads only 6 columns from "
             "`markouts.parquet`).")
    L.append("- New in `p2cli`: `p2 infer` (H1 to H3 as before), `p2 infer-h4` (`inference_p2_h4.main`), "
             "`p2 numbers` (`scripts/p2_numbers.py`, imported as a module), `p2 api` (`p2api.main`).")
    return "\n".join(L) + "\n"


# ================================================================================================ run and report

def _rel(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(REPO))
    except ValueError:
        return str(p)


def _iso(t: float) -> str:
    return dt.datetime.fromtimestamp(float(t), dt.timezone.utc).isoformat(timespec="seconds")


def max_starts_per_second(log_path: Path, start_utc: str, end_utc: str) -> Optional[int]:
    """Largest number of logged request starts in any window [t, t + 1 s) between ``start_utc`` and ``end_utc``."""
    path = Path(log_path)
    if not path.exists():
        return None
    lo = dt.datetime.fromisoformat(start_utc).timestamp()
    hi = dt.datetime.fromisoformat(end_utc).timestamp()
    ts = []
    for line in path.read_text().splitlines():
        try:
            t = dt.datetime.fromisoformat(json.loads(line)["ts"]).timestamp()
        except (ValueError, KeyError, TypeError):
            continue
        if lo <= t <= hi:
            ts.append(t)
    ts.sort()
    best, j = 0, 0
    for i, t in enumerate(ts):
        while ts[j] <= t - 1.0:
            j += 1
        best = max(best, i - j + 1)
    return best


def report(csv_path: Path = CSV_PATH, meta_path: Path = META_PATH, doc_path: Path = DOC_PATH) -> str:
    df = pd.read_csv(csv_path)
    meta = json.loads(Path(meta_path).read_text())
    text = render_doc(df, meta)
    Path(doc_path).parent.mkdir(parents=True, exist_ok=True)
    Path(doc_path).write_text(text, encoding="utf-8")
    return text


def run(ccys: Sequence[str] = CCYS, csv_path: Path = CSV_PATH, meta_path: Path = META_PATH,
        doc_path: Path = DOC_PATH, api=None, rpc=None, types: Optional[Mapping] = None,
        params_at: Optional[Callable] = None, clock: Callable[[], float] = time.time,
        log_path: Path = LOG_PATH) -> pd.DataFrame:
    throttle = Throttle(RATE)
    api = api if api is not None else ApiClient(throttle=throttle, log_path=log_path)
    rpc = rpc if rpc is not None else SharedRpc(throttle, log_path=log_path)
    types_source = "given"  # a key of TYPES_SOURCES; the document text comes from types_source_text
    if types is None:
        types = load_cell_types()
        types_source = "markouts"
    params_at = params_at or TimelineParams()
    start = float(clock())
    wall_start = _utc_now()
    rows: List[dict] = []
    for ccy in ccys:
        rows += snapshot_ccy(ccy, api, rpc, types, params_at, clock)
    end = float(clock())
    wall_end = _utc_now()
    df = to_frame(rows)
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, float_format="%.10g")
    params = {}
    for ccy in ccys:
        sub = df[(df["ccy"] == ccy) & df["params_sm"].notna()]
        if len(sub):
            params[ccy] = {m: str(sub[f"params_{m}"].iloc[0]) for m in MANAGERS}
    meta = {"task": "C5b", "start_utc": _iso(start), "end_utc": _iso(end), "api_host": API_URL, "rpc_url": RPC_URL,
            "user_agent": USER_AGENT, "rate_per_s": RATE,
            "requests": {"api": int(getattr(api, "n_requests", 0)), "rpc": int(getattr(rpc, "n_requests", 0))},
            "max_requests_in_1s": max_starts_per_second(log_path, wall_start, wall_end),
            "params": params, "types_source": types_source, "log": _rel(log_path), "csv": _rel(csv_path),
            "meta": _rel(meta_path), "cells": int(len(df)), "ok": int((df["status"] == "ok").sum())}
    Path(meta_path).parent.mkdir(parents=True, exist_ok=True)
    Path(meta_path).write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n")
    report(csv_path, meta_path, doc_path)
    return df


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="derive_surface p2 api", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="measure now: get_margin (SM, PM2) and the replica at the head block")
    r.add_argument("--ccy", nargs="+", default=list(CCYS), choices=list(CCYS))
    r.add_argument("--csv", type=Path, default=CSV_PATH)
    r.add_argument("--meta", type=Path, default=META_PATH)
    r.add_argument("--doc", type=Path, default=DOC_PATH)
    p = sub.add_parser("report", help="re-render the document from the CSV and the meta file")
    p.add_argument("--csv", type=Path, default=CSV_PATH)
    p.add_argument("--meta", type=Path, default=META_PATH)
    p.add_argument("--doc", type=Path, default=DOC_PATH)
    a = ap.parse_args(list(argv) if argv is not None else None)
    if a.cmd == "run":
        df = run(a.ccy, a.csv, a.meta, a.doc)
        print(json.dumps({"cells": int(len(df)), "status": df["status"].value_counts().to_dict()}), flush=True)
    else:
        report(a.csv, a.meta, a.doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
