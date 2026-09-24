"""Capital per fill for Paper 2 (task B2): the one-contract capital of every fill under SM, legacy PM and PM2.

Preregistration (``docs/paper2/PRAEREGISTRIERUNG.md``, Semantik und Kapital, with Nachtrag 1):

* ``K_p(q) = p q - net_IM(q; cash = 0)`` for the book that holds only the filled contract, ``q = maker_side``
  (+1 maker buy, -1 maker sell), ``p`` = fill price, per contract; MM (``K_*_mm``) is the sensitivity.
* Chain semantics at the block of the taker timestamp (``markouts.ts``, ms): every feed at its last push with
  ``block_ts <= ts // 1000`` (``FeedHistory.bulk``), time to expiry from the block timestamp (the ``block.timestamp`` an
  ``eth_call`` at that block sees; 2 s blocks, so at most 1 s before the taker second), parameters of the standard lib
  in force at that block (``Timeline.at``). No exclusion for feed age; the ages are carried along.
* Rates: PM2 reads the PM2 rate feed (``rate``, ``rate_conf``), the legacy PM its own static feed (``rate_pm`` = 0 at
  confidence 1 over the whole history), SM does not discount (Nachtrag 1, item 2). The stable-coin feed is not loaded;
  ``stable`` = 1.
* Manager windows: SM over the whole sample (HYPE from 11.11.2025 00:00 UTC), legacy PM for BTC and ETH over the whole
  sample and never for HYPE, PM2 for BTC and ETH from 12.06.2025 23:00 UTC and for HYPE from 11.11.2025 00:00 UTC.
  Outside its window a manager's columns are NaN; they are also NaN where a required feed (spot, forward, vol at the
  strike) has no value, which is where the chain call would revert.

Output ``data/p2/derived/capital.parquet`` (one row per fill of ``data/p1/derived/markouts.parquet``) with the columns
of :data:`OUT_COLUMNS`: ``K_*`` capital, ``V_*`` the engine's mark-to-market of the contract (so ``R = V - net`` and
``K = p q - V + R``), ``reg_*`` the ``from_ts`` of the parameter entry used (-1 = none), the feed state and ages.
The run writes monthly parts per currency and resumes where it stopped (``python3 -m derive_surface.capital run``).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from . import margin_pm, margin_pm2, margin_sm
from .p2chain import ANCHOR_BLOCK, ANCHOR_TS, BLOCK_SECONDS
from .p2feeds import FeedHistory
from .p2params import Timeline
from .p2types import YEAR

MARKOUTS = Path("data/p1/derived/markouts.parquet")
DERIVED_DIR = Path("data/p2/derived")
PART_VERSION = 1
PARTS_DIR = DERIVED_DIR / "capital_parts" / f"v{PART_VERSION}"
OUT_PATH = DERIVED_DIR / "capital.parquet"
CHECK_PATH = Path("results/p2/capital_check.json")

MANAGERS = ("sm", "pm", "pm2")
ENGINES = {"sm": margin_sm.single, "pm": margin_pm.single, "pm2": margin_pm2.single}

SAMPLE_START = 1_704_931_200      # 11.01.2024 00:00 UTC, first taker second of the Paper 1 sample
PM2_START_BTC_ETH = 1_749_769_200  # 12.06.2025 23:00 UTC
HYPE_START = 1_762_819_200         # 11.11.2025 00:00 UTC
# first taker second of each manager window; a missing currency means the manager is never available
WINDOW_START: Dict[str, Dict[str, int]] = {
    "sm": {"BTC": SAMPLE_START, "ETH": SAMPLE_START, "HYPE": HYPE_START},
    "pm": {"BTC": SAMPLE_START, "ETH": SAMPLE_START},
    "pm2": {"BTC": PM2_START_BTC_ETH, "ETH": PM2_START_BTC_ETH, "HYPE": HYPE_START},
}

MARKOUT_COLUMNS = ["trade_id", "ts", "currency", "expiry", "strike", "option_type", "price", "amount", "maker_side",
                   "index_price"]
FEED_COLUMNS = ["spot", "forward", "sigma", "rate", "rate_pm", "svi_fwd", "spot_conf", "fwd_conf", "vol_conf",
                "rate_conf", "fwd_fixed", "spot_age", "fwd_age", "vol_age", "rate_age"]
K_COLUMNS = [f"K_{m}" for m in MANAGERS] + [f"K_{m}_mm" for m in MANAGERS]
OUT_COLUMNS = (["trade_id", "currency", "ts", "block", "sec", "maker_side", "option_type", "expiry", "strike", "price",
                "amount", "index_price"] + K_COLUMNS + [f"V_{m}" for m in MANAGERS] + [f"reg_{m}" for m in MANAGERS]
               + FEED_COLUMNS)


# ---------------------------------------------------------------- windows and clock

def in_window(ccy: str, mgr: str, ts_s) -> np.ndarray:
    """True where the manager's preregistered window is open at taker second ``ts_s``."""
    ts_s = np.asarray(ts_s, dtype=np.int64)
    start = WINDOW_START[mgr].get(ccy)
    if start is None:
        return np.zeros(ts_s.shape, dtype=bool)
    return ts_s >= start


def fill_clock(ts_ms, expiry) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(taker second, block of that second, seconds to expiry at the block timestamp) per fill."""
    ts_s = np.asarray(ts_ms, dtype=np.int64) // 1000
    block = ANCHOR_BLOCK + (ts_s - ANCHOR_TS) // BLOCK_SECONDS
    block_ts = ANCHOR_TS + (block - ANCHOR_BLOCK) * BLOCK_SECONDS
    return ts_s, block, np.asarray(expiry, dtype=np.int64) - block_ts


# ---------------------------------------------------------------- engine inputs and capital

def engine_arrays(fills: pd.DataFrame, feed: pd.DataFrame) -> Dict[str, np.ndarray]:
    """Inputs of ``margin_*.single`` for the one-contract books of ``fills`` (row-aligned with ``feed``)."""
    _, _, sec = fill_clock(fills["ts"].to_numpy(), fills["expiry"].to_numpy())
    n = len(fills)
    f = {c: feed[c].to_numpy(dtype=float) for c in ("spot", "forward", "sigma", "rate", "rate_pm", "vol_conf",
                                                   "fwd_conf", "spot_conf", "rate_conf", "fwd_fixed")}
    return {"spot": f["spot"], "forward": f["forward"], "sigma": f["sigma"],
            "tau": np.maximum(sec, 0).astype(float) / YEAR, "rate": f["rate"],
            "strike": fills["strike"].to_numpy(dtype=float),
            "is_call": (fills["option_type"].to_numpy() == "C"),
            "amount": fills["maker_side"].to_numpy(dtype=float),
            "vol_conf": f["vol_conf"], "fwd_conf": f["fwd_conf"], "spot_conf": f["spot_conf"],
            "rate_conf": f["rate_conf"], "fwd_fixed": f["fwd_fixed"], "rate_pm": f["rate_pm"],
            "stable": np.ones(n)}


def manager_arrays(mgr: str, arrays: Mapping[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Per-manager view of :func:`engine_arrays`: the legacy PM reads its own static rate feed (``rate_pm``, confidence
    1 by its single ``RateUpdated`` at deploy), never the PM2 feed's ``rate`` and ``rate_conf``."""
    a = dict(arrays)
    if mgr == "pm":
        a["rate_conf"] = np.ones(np.shape(a["spot"]))
    return a


def capital_single(mgr: str, arrays: Mapping[str, np.ndarray], params: Mapping, price,
                   is_initial: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """(K, V) of one-contract books: ``K = p q - net`` with ``q = arrays['amount']``, ``V`` the engine mtm."""
    net, mtm = ENGINES[mgr](manager_arrays(mgr, arrays), params, is_initial)
    q = np.asarray(arrays["amount"], dtype=float)
    return np.asarray(price, dtype=float) * q - net, mtm


def load_timelines(ccy: str, root: Optional[Path] = None) -> Dict[str, Timeline]:
    """Standard-lib parameter timelines of the three managers (``results/p2/params``)."""
    return {m: Timeline(ccy, m, root=root) for m in MANAGERS if Timeline.path(ccy, m, root=root).exists()}


def fill_capital(fills: pd.DataFrame, feed: pd.DataFrame, timelines: Mapping[str, Timeline], ccy: str) -> pd.DataFrame:
    """Capital of every fill of one currency under every manager (see the module docstring); rows as ``fills``."""
    fills = fills.reset_index(drop=True)
    feed = feed.reset_index(drop=True)
    n = len(fills)
    ts_s, block, sec = fill_clock(fills["ts"].to_numpy(), fills["expiry"].to_numpy())
    base = engine_arrays(fills, feed)
    valid = np.isfinite(base["spot"]) & np.isfinite(base["forward"]) & np.isfinite(base["sigma"])
    price = fills["price"].to_numpy(dtype=float)
    out = {"trade_id": fills["trade_id"].to_numpy(), "currency": np.full(n, ccy, dtype=object),
           "ts": fills["ts"].to_numpy(dtype=np.int64), "block": block, "sec": sec,
           "maker_side": fills["maker_side"].to_numpy(dtype=np.int64),
           "option_type": fills["option_type"].to_numpy(), "expiry": fills["expiry"].to_numpy(dtype=np.int64),
           "strike": fills["strike"].to_numpy(dtype=float), "price": price,
           "amount": fills["amount"].to_numpy(dtype=float), "index_price": fills["index_price"].to_numpy(dtype=float)}
    for mgr in MANAGERS:
        k_im, k_mm, v = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
        reg = np.full(n, -1, dtype=np.int64)
        tl = timelines.get(mgr)
        if tl is not None and tl.entries:
            froms = np.array([int(e["from_ts"]) for e in tl.entries], dtype=np.int64)
            idx = np.searchsorted(froms, ts_s, side="right") - 1
            use = in_window(ccy, mgr, ts_s) & (idx >= 0)
            reg[use] = froms[idx[use]]
            calc = use & valid
            for r in np.unique(idx[calc]):
                sel = np.flatnonzero(calc & (idx == r))
                params = tl.at(int(ts_s[sel[0]]))  # the regime in force for every fill of the group
                sub = {k: val[sel] for k, val in base.items()}
                k_im[sel], v[sel] = capital_single(mgr, sub, params, price[sel], True)
                k_mm[sel], _ = capital_single(mgr, sub, params, price[sel], False)
        out[f"K_{mgr}"], out[f"K_{mgr}_mm"], out[f"V_{mgr}"], out[f"reg_{mgr}"] = k_im, k_mm, v, reg
    for c in FEED_COLUMNS:
        out[c] = feed[c].to_numpy(dtype=float)
    return pd.DataFrame(out)[OUT_COLUMNS]


def capital_for(fills: pd.DataFrame, hist: FeedHistory, timelines: Mapping[str, Timeline], ccy: str) -> pd.DataFrame:
    """:func:`fill_capital` with the feed state from ``hist.bulk`` at the taker second."""
    fills = fills.reset_index(drop=True)
    ts_s = fills["ts"].to_numpy(dtype=np.int64) // 1000
    feed = hist.bulk(ts_s, fills["expiry"].to_numpy(dtype=np.int64), fills["strike"].to_numpy(dtype=float))
    return fill_capital(fills, feed, timelines, ccy)


# ---------------------------------------------------------------- resumable run

def _part_path(parts_dir: Path, ccy: str, month: str) -> Path:
    return Path(parts_dir) / f"{ccy}_{month}.parquet"


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    df.to_parquet(tmp, index=False)
    tmp.replace(path)


def _months(ts_ms: pd.Series) -> np.ndarray:
    return pd.to_datetime(ts_ms.to_numpy(dtype=np.int64), unit="ms").strftime("%Y-%m").to_numpy()


def _default_history(ccy: str, start_ts: int, end_ts: int) -> FeedHistory:
    return FeedHistory(ccy, start_ts=start_ts, end_ts=end_ts)


def run(ccys: Sequence[str] = ("BTC", "ETH", "HYPE"), *, markouts: Path = MARKOUTS, parts_dir: Path = PARTS_DIR,
        history_factory: Callable[[str, int, int], FeedHistory] = _default_history,
        timelines: Optional[Mapping[str, Mapping[str, Timeline]]] = None, max_seconds: Optional[float] = None,
        months_per_window: int = 3, log: Callable[[str], None] = lambda s: None) -> dict:
    """Compute the missing monthly parts ``{parts_dir}/{CCY}_{YYYY-MM}.parquet``, one feed window per
    ``months_per_window`` missing months (``FeedHistory(start_ts, end_ts)`` spans exactly the window's fills).
    Stops before a new window once ``max_seconds`` have passed (at least one window per call); call again to resume.
    """
    t0 = time.monotonic()
    fills_all = pd.read_parquet(markouts, columns=MARKOUT_COLUMNS)
    written, first, stopped = 0, True, False
    for ccy in ccys:
        f = fills_all[fills_all["currency"] == ccy]
        if f.empty:
            continue
        month = _months(f["ts"])
        todo = [m for m in sorted(set(month)) if not _part_path(parts_dir, ccy, m).exists()]
        if not todo:
            continue
        tls = (timelines or {}).get(ccy) or load_timelines(ccy)
        for w in range(0, len(todo), months_per_window):
            if not first and max_seconds is not None and time.monotonic() - t0 > max_seconds:
                stopped = True
                break
            first = False
            window = todo[w:w + months_per_window]
            in_w = np.isin(month, window)
            sub, sub_month = f[in_w], month[in_w]
            ts_s = sub["ts"].to_numpy(dtype=np.int64) // 1000
            t1 = time.monotonic()
            hist = history_factory(ccy, int(ts_s.min()), int(ts_s.max()))
            t_load = time.monotonic() - t1
            for m in window:
                out = capital_for(sub[sub_month == m], hist, tls, ccy)
                _write_parquet(out, _part_path(parts_dir, ccy, m))
                written += 1
            del hist
            log(f"{ccy} {window[0]}..{window[-1]}: {len(sub)} fills, feed load {t_load:.1f} s, "
                f"total {time.monotonic() - t0:.0f} s")
        if stopped:
            break
    remaining = 0
    for ccy in ccys:
        f = fills_all[fills_all["currency"] == ccy]
        remaining += sum(not _part_path(parts_dir, ccy, m).exists() for m in set(_months(f["ts"])))
    return {"done": remaining == 0, "written": written, "remaining": remaining,
            "seconds": round(time.monotonic() - t0, 1)}


def combine(*, parts_dir: Path = PARTS_DIR, out: Path = OUT_PATH, markouts: Path = MARKOUTS) -> pd.DataFrame:
    """Concatenate the parts into ``out``; every fill of ``markouts`` must appear exactly once."""
    parts = sorted(Path(parts_dir).glob("*.parquet"))
    if not parts:
        raise ValueError(f"no parts under {parts_dir}")
    df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    ids = pd.read_parquet(markouts, columns=["trade_id"])["trade_id"]
    missing = int((~ids.isin(df["trade_id"])).sum())
    if missing:
        raise ValueError(f"{missing} fills of {markouts} missing from the parts; run first")
    unknown = int((~df["trade_id"].isin(ids)).sum())
    dup = int(df["trade_id"].duplicated().sum())
    if unknown or dup:
        raise ValueError(f"parts hold {unknown} unknown and {dup} duplicate fills")
    df = df.sort_values(["ts", "trade_id"], kind="mergesort").reset_index(drop=True)[OUT_COLUMNS]
    _write_parquet(df, Path(out))
    return df


# ---------------------------------------------------------------- plausibility (descriptive, no inference)

QUANTILES = {"p01": 0.01, "p05": 0.05, "p25": 0.25, "p50": 0.5, "p75": 0.75, "p95": 0.95, "p99": 0.99}


def _num(x) -> Optional[float]:
    x = float(x)
    return None if not np.isfinite(x) else x


def _dist(x: np.ndarray) -> dict:
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {k: None for k in list(QUANTILES) + ["min", "max", "mean"]}
    q = np.quantile(x, list(QUANTILES.values()))
    d = {k: _num(v) for k, v in zip(QUANTILES, q)}
    d.update(min=_num(x.min()), max=_num(x.max()), mean=_num(x.mean()))
    return d


def _side(k: np.ndarray, index: np.ndarray) -> dict:
    fin = np.isfinite(k)
    le0 = int((k[fin] <= 0).sum())
    return {"n": int(len(k)), "n_finite": int(fin.sum()), "k_le_0": le0,
            "share_k_le_0": _num(le0 / fin.sum()) if fin.any() else None,
            "k_over_index": _dist(k / index)}


def plausibility(df: pd.DataFrame) -> dict:
    """NaN shares per manager and window, distribution of K / index per manager and maker side, count of K <= 0,
    the exactness check K_sm = p for maker buys, and feed ages. Descriptive only (no cells, no hypotheses)."""
    out: dict = {"rows": int(len(df)), "managers": {}, "ages": {}}
    for ccy in sorted(df["currency"].unique()):
        d = df[df["currency"] == ccy]
        ts_s = d["ts"].to_numpy(dtype=np.int64) // 1000
        side = d["maker_side"].to_numpy()
        index = d["index_price"].to_numpy(dtype=float)
        out["managers"][ccy] = {}
        for mgr in MANAGERS:
            win = in_window(ccy, mgr, ts_s)
            e: dict = {"n": int(len(d)), "n_in_window": int(win.sum())}
            for suffix, key in (("", "sides"), ("_mm", "sides_mm")):
                k = d[f"K_{mgr}{suffix}"].to_numpy(dtype=float)
                nan = ~np.isfinite(k)
                if suffix == "":
                    e.update(nan_in_window=int(nan[win].sum()), share_nan=_num(nan.mean()),
                             share_nan_in_window=_num(nan[win].mean()) if win.any() else None,
                             finite_outside_window=int((~nan[~win]).sum()))
                e[key] = {name: _side(k[win & (side == s)], index[win & (side == s)])
                          for name, s in (("buy", 1), ("sell", -1))}
            out["managers"][ccy][mgr] = e
        win2 = in_window(ccy, "pm2", ts_s)
        out["ages"][ccy] = {c: _dist(d[c].to_numpy(dtype=float)[win2 if c == "rate_age" else slice(None)])
                            for c in ("spot_age", "fwd_age", "vol_age", "rate_age")}
    buy = (df["maker_side"].to_numpy() == 1) & np.isfinite(df["K_sm"].to_numpy(dtype=float))
    out["sm_long_exact"] = {"n": int(buy.sum()),
                            "mismatch": int((df["K_sm"].to_numpy()[buy] != df["price"].to_numpy()[buy]).sum())}
    out["regimes"] = {}
    for ccy, d in df.groupby("currency"):
        out["regimes"][ccy] = {}
        for mgr in MANAGERS:
            reg = d[f"reg_{mgr}"].to_numpy(dtype=np.int64)
            vc = pd.Series(reg[reg >= 0]).value_counts().sort_index()
            out["regimes"][ccy][mgr] = {pd.to_datetime(int(k), unit="s").strftime("%Y-%m-%d %H:%M:%S"): int(v)
                                        for k, v in vc.items()}
    out["sec_min"] = {ccy: int(v) for ccy, v in df.groupby("currency")["sec"].min().items()}
    return out


def crosscheck_p1(df: pd.DataFrame, marks: pd.DataFrame) -> dict:
    """Comparison with Paper 1 (``markouts``: ``trade_id, iv_mark_t, mark_b_t, is_rfq``): vol at the strike equal to
    ``iv_mark_t`` (relative 1e-6), the SM mark-to-market per contract against ``mark_b_t`` (Black-76 on the SVI curve
    with ``SVI_fwd``, D = 1) in bp of the index, and the fills with K <= 0 per manager (RFQ count, price / mark)."""
    d = df.merge(marks[["trade_id", "iv_mark_t", "mark_b_t", "is_rfq"]], on="trade_id", how="left", validate="1:1")
    sig, iv = d["sigma"].to_numpy(dtype=float), d["iv_mark_t"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        equal = np.abs(sig - iv) <= 1e-6 * np.abs(iv)
    side = d["maker_side"].to_numpy(dtype=float)
    mark = d["mark_b_t"].to_numpy(dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):  # mark 0 for far OTM options -> inf, dropped by _dist
        bp = 1e4 * (d["V_sm"].to_numpy(dtype=float) / side - mark) / d["index_price"].to_numpy(dtype=float)
        ratio = d["price"].to_numpy(dtype=float) / mark
    out = {"n": int(len(d)), "sigma_equal": int(equal.sum()), "v_sm_minus_mark_bp": _dist(bp), "k_le_0": {}}
    rfq = d["is_rfq"].to_numpy(dtype=bool)
    for mgr in MANAGERS:
        k = d[f"K_{mgr}"].to_numpy(dtype=float)
        le0 = np.isfinite(k) & (k <= 0)
        pom = {}
        for name, s in (("buy", 1), ("sell", -1)):
            r = ratio[le0 & (side == s)]
            pom[name] = {"n": int(len(r)), "min": _num(r.min()) if len(r) else None,
                         "max": _num(r.max()) if len(r) else None}
        out["k_le_0"][mgr] = {"n": int(le0.sum()), "n_rfq": int((le0 & rfq).sum()), "price_over_mark": pom}
    return out


# ---------------------------------------------------------------- CLI

def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser(prog="python3 -m derive_surface.capital")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="compute missing monthly parts (resumable)")
    r.add_argument("--ccy", nargs="+", default=["BTC", "ETH", "HYPE"])
    r.add_argument("--max-seconds", type=float, default=480.0)
    r.add_argument("--months-per-window", type=int, default=3)
    sub.add_parser("combine", help=f"write {OUT_PATH}")
    c = sub.add_parser("check", help=f"plausibility summary to {CHECK_PATH}")
    c.add_argument("--out", type=Path, default=CHECK_PATH)
    args = ap.parse_args(argv)
    if args.cmd == "run":
        res = run(args.ccy, max_seconds=args.max_seconds, months_per_window=args.months_per_window,
                  log=lambda s: print(s, flush=True))
        print(json.dumps(res))
        if not res["done"]:
            sys.exit(3)
    elif args.cmd == "combine":
        df = combine()
        print(json.dumps({"rows": len(df), "out": str(OUT_PATH)}))
    else:
        df = pd.read_parquet(OUT_PATH)
        chk = plausibility(df)
        chk["p1"] = crosscheck_p1(df, pd.read_parquet(MARKOUTS, columns=["trade_id", "iv_mark_t", "mark_b_t", "is_rfq"]))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(chk, indent=1) + "\n")
        print(json.dumps({"out": str(args.out), "rows": chk["rows"], "sm_long_exact": chk["sm_long_exact"]}))


if __name__ == "__main__":
    main()


__all__ = ["WINDOW_START", "OUT_COLUMNS", "in_window", "fill_clock", "engine_arrays", "manager_arrays",
           "capital_single", "load_timelines", "fill_capital", "capital_for", "run", "combine", "plausibility",
           "crosscheck_p1", "main"]
