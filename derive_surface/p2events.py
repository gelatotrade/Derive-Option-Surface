"""Parameter events, capital doses and the H4 panel for Paper 2 (preregistration H4, docs/paper2/PRAEREGISTRIERUNG.md).

* **Events:** every capital-relevant on-chain parameter change of PM2 (standard lib) per currency inside its PM2
  window, plus the legacy-PM changes of BTC and ETH inside the sample (2024-06-12 and 2025-02-22). Changes of
  ``CollateralParameters`` and ``maxExpiries`` do not change the capital of a single contract and are left out.
  Changes of one currency on the same UTC day are merged into one event; its time ``event_ts`` is the first change.
* **Dose:** ``d_{c,e}`` = mean over the fills of cell ``c`` with taker time in ``[e - 14 d, e)`` of
  ``log(K_after / K_before)``: the same fill (maker side, fill price, one contract) in the same market state at the fill,
  priced under the changed manager once with the parameters immediately before the first change of the day and once
  with those after its last change. ``K = p q - net_IM(q; cash = 0)`` exactly as the single-contract capital of B2.
  Fills whose K is not positive under either parameter set have no log ratio; they are counted (``n_nonpos``).
* **Events kept:** those whose largest absolute dose over all cells with a dose is at least 1 %.
* **Panel:** fills of the currency with taker time in ``[e - 14 d, e + 14 d]`` except the UTC day of ``e``;
  ``post`` = after the event day; cells with a dose and at least 20 fills before and 20 after.
  ``y_hs_bp = 1e4 * hs / index_price`` with ``hs`` from :func:`derive_surface.inference_p1.analysis_frame`.
  :func:`build_panel` takes any date and any dose vector (placebo dates are drawn in stage C). No regression here.

Heavy step (FeedHistory with SVI, run under ``scripts/p2_heavy.py``)::

    python3 scripts/p2_heavy.py --wait-max 500 -- python3 -m derive_surface.p2events doses --ccy BTC --max-seconds 500
    python3 -m derive_surface.p2events panel
"""
from __future__ import annotations

import argparse
import copy
import gc
import json
import time
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from . import margin_pm, margin_pm2
from .p2chain import ANCHOR_TS, BLOCK_SECONDS
from .p2params import Timeline
from .p2types import YEAR

REPO = Path(__file__).resolve().parents[1]
DERIVED_DIR = REPO / "data" / "p2" / "derived"
DOSE_DIR = DERIVED_DIR / "h4_doses"                 # one file per event (resumable)
PANEL_PATH = DERIVED_DIR / "h4_panel.parquet"
EVENTS_CSV = REPO / "results" / "p2" / "events.csv"
DOSES_CSV = REPO / "results" / "p2" / "h4_doses.csv"
MARKOUTS = REPO / "data" / "p1" / "derived" / "markouts.parquet"
FUNDING = REPO / "data" / "p1" / "ref" / "funding_history.parquet"

DAY = 86_400
WINDOW_DAYS = 14
MIN_ABS_DOSE = 0.01          # events whose largest |dose| over all cells is below 1 % are dropped
MIN_SIDE_FILLS = 20          # fills per cell before and after the event
EXCLUDED_KEYS = ("CollateralParameters", "maxExpiries")
CCYS = ("BTC", "ETH", "HYPE")
SAMPLE_START_TS = 1_704_931_200                     # 2024-01-11 00:00 UTC
SAMPLE_END_TS = 1_790_755_200                       # 2026-09-30 08:00 UTC
PM2_START_TS = {"BTC": 1_749_769_200, "ETH": 1_749_769_200, "HYPE": 1_762_819_200}  # 2025-06-12 23:00, 2025-11-11
EVENT_MANAGERS = {"BTC": ("pm", "pm2"), "ETH": ("pm", "pm2"), "HYPE": ("pm2",)}

CHANGE_COLUMNS = ["ccy", "manager", "ts", "kinds"]
EVENT_BASE_COLUMNS = ["event_id", "ccy", "manager", "event_ts", "event_utc", "event_day", "last_ts", "n_changes",
                      "change_ts", "kinds"]
DOSE_COLUMNS = ["cell", "dose", "n_fills", "n_valid", "n_nonpos", "n_nan"]
FILL_DOSE_COLUMNS = ["fill_key", "cell", "K_before", "K_after", "log_ratio"]
PANEL_COLUMNS = ["fill_key", "ccy", "cell", "event_id", "post", "dose", "y_hs_bp", "day"]
EVENTS_CSV_COLUMNS = ["ccy", "manager", "event_ts", "kinds", "max_abs_dose", "kept", "event_id", "event_utc",
                      "event_day", "last_ts", "n_changes", "n_dose_fills", "n_valid", "n_nonpos", "n_nan", "n_cells",
                      "panel_cells", "panel_fills_pre", "panel_fills_post"]
MARKOUT_COLUMNS = ["trade_id", "ts", "currency", "instrument_name", "expiry", "strike", "option_type", "price",
                   "index_price", "maker_side", "delta_bucket", "tenor_bucket", "mark_b_t", "delta_t", "fwd_t",
                   "fee_maker", "rebate_maker", "taker_wallet", "mo_usd_30m", "mo_dn_30m", "mo_vol_30m"]
ENGINES = {"pm2": margin_pm2.single, "pm": margin_pm.single}


# =====================================================================================================================
# Events
# =====================================================================================================================

def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _utc_day(ts) -> np.ndarray:
    return pd.to_datetime(np.asarray(ts, dtype=np.int64), unit="s", utc=True).strftime("%Y-%m-%d").to_numpy()


def manager_window(ccy: str, manager: str) -> Tuple[int, int]:
    """Preregistered window of a manager: PM2 from its start per currency, legacy PM over the whole sample."""
    if manager == "pm2":
        return PM2_START_TS[ccy], SAMPLE_END_TS
    if manager == "pm":
        return SAMPLE_START_TS, SAMPLE_END_TS
    raise ValueError(f"no events for manager {manager!r}")


def capital_keys(tl: Timeline) -> List[str]:
    """Parameter structs that can change the capital of a single contract (all but collateral and maxExpiries)."""
    keys = set()
    for e in tl.entries:
        keys.update(e["params"])
    return sorted(k for k in keys if k not in EXCLUDED_KEYS)


def parameter_changes(ccy: str, manager: str, root: Optional[Path] = None) -> pd.DataFrame:
    """Capital-relevant changes of one timeline inside the manager window: ``ccy, manager, ts, kinds``."""
    tl = Timeline(ccy, manager, root=root)
    keys = capital_keys(tl)
    lo, hi = manager_window(ccy, manager)
    wanted = {t for t in tl.changes(keys=keys) if lo <= t <= hi}
    rows = []
    for prev, e in zip(tl.entries, tl.entries[1:]):
        t = int(e["from_ts"])
        if t not in wanted:
            continue
        kinds = [k for k in keys if _canon(prev["params"].get(k)) != _canon(e["params"].get(k))]
        rows.append({"ccy": ccy, "manager": manager, "ts": t, "kinds": "+".join(kinds)})
    return pd.DataFrame(rows, columns=CHANGE_COLUMNS)


def merge_same_day(changes: pd.DataFrame) -> pd.DataFrame:
    """One event per currency and UTC day; ``event_ts`` is the first change, ``last_ts`` the last."""
    if len(changes) == 0:
        return pd.DataFrame(columns=EVENT_BASE_COLUMNS)
    ch = changes.assign(event_day=_utc_day(changes["ts"]))
    rows = []
    for (ccy, day), g in ch.groupby(["ccy", "event_day"], sort=True):
        managers = sorted(set(g["manager"]))
        if len(managers) > 1:
            raise ValueError(f"{ccy} {day}: changes of several managers {managers} on one day")
        ts = sorted(int(t) for t in g["ts"])
        kinds = sorted({k for s in g["kinds"] for k in str(s).split("+") if k})
        rows.append({"event_id": f"{ccy}-{managers[0]}-{day.replace('-', '')}", "ccy": ccy, "manager": managers[0],
                     "event_ts": ts[0],
                     "event_utc": pd.Timestamp(ts[0], unit="s", tz="UTC").strftime("%Y-%m-%d %H:%M:%S"),
                     "event_day": day, "last_ts": ts[-1], "n_changes": len(ts),
                     "change_ts": ";".join(str(t) for t in ts), "kinds": "+".join(kinds)})
    return (pd.DataFrame(rows, columns=EVENT_BASE_COLUMNS).sort_values(["ccy", "event_ts"], kind="mergesort")
            .reset_index(drop=True))


def event_list(ccys: Sequence[str] = CCYS, root: Optional[Path] = None) -> pd.DataFrame:
    """All preregistered H4 events (PM2 per currency, legacy PM for BTC and ETH), same-day changes merged."""
    parts = [parameter_changes(c, m, root=root) for c in ccys for m in EVENT_MANAGERS[c]]
    parts = [p for p in parts if len(p)]
    return merge_same_day(pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=CHANGE_COLUMNS))


def event_params(event: Mapping, root: Optional[Path] = None) -> Tuple[dict, dict]:
    """(parameters immediately before the first change, parameters after the last change) of a merged event."""
    tl = Timeline(event["ccy"], event["manager"], root=root)
    return copy.deepcopy(tl.at(int(event["event_ts"]) - 1)), copy.deepcopy(tl.at(int(event["last_ts"])))


# =====================================================================================================================
# Capital of a single contract and doses
# =====================================================================================================================

def cell_labels(ccy, maker_side, delta_bucket, tenor_bucket) -> np.ndarray:
    """Cell = currency x maker side (buy/sell) x |delta| bucket x tenor bucket of Paper 1, e.g. ``BTC|sell|10-25|7-30d``."""
    side = np.where(np.asarray(maker_side, dtype=float) > 0, "buy", "sell")
    parts = [np.asarray(ccy, dtype=object), side.astype(object), np.asarray(delta_bucket, dtype=object),
             np.asarray(tenor_bucket, dtype=object)]
    return np.array(["|".join(map(str, t)) for t in zip(*parts)], dtype=object)


def block_time(ts_s) -> np.ndarray:
    """Timestamp of the block that contains time ``ts_s`` (exactly 2 s per block), as ``ts_at_block(block_at_ts(t))``."""
    t = np.asarray(ts_s, dtype=np.int64)
    return ANCHOR_TS + ((t - ANCHOR_TS) // BLOCK_SECONDS) * BLOCK_SECONDS


def engine_arrays(fills: pd.DataFrame, state: pd.DataFrame, manager: str) -> Dict[str, np.ndarray]:
    """Inputs of ``margin_*.single`` for one-contract books: maker side as amount, market state from
    ``FeedHistory.bulk`` at the fill, time to expiry from the block time (``secToExpiry`` on chain). PM2 reads the PM2
    rate feed; the legacy PM its own rate feed (``rate_pm``, constant 0 with confidence 1 since deploy)."""
    n = len(fills)
    ts_s = fills["ts"].to_numpy(np.int64) // 1000
    tau = (fills["expiry"].to_numpy(np.int64) - block_time(ts_s)) / YEAR
    st = lambda k: state[k].to_numpy(float) if n else np.zeros(0)  # noqa: E731
    arrays = {"spot": st("spot"), "forward": st("forward"), "sigma": st("sigma"), "tau": tau,
              "strike": fills["strike"].to_numpy(float), "is_call": fills["is_call"].to_numpy(bool),
              "amount": fills["maker_side"].to_numpy(float), "vol_conf": st("vol_conf"), "fwd_conf": st("fwd_conf"),
              "spot_conf": st("spot_conf"), "fwd_fixed": st("fwd_fixed"), "stable": np.ones(n)}
    if manager == "pm2":
        arrays.update(rate=st("rate"), rate_conf=st("rate_conf"))
    elif manager == "pm":
        arrays.update(rate_pm=st("rate_pm"), rate_conf=np.ones(n))
    else:
        raise ValueError(f"unknown manager {manager!r}")
    return arrays


def single_capital(fills: pd.DataFrame, state: pd.DataFrame, params: Mapping, manager: str,
                   is_initial: bool = True) -> np.ndarray:
    """``K = p q - net(q; cash = 0)`` per fill for ``q`` = maker side (one contract); NaN where the state is missing."""
    fills = fills.reset_index(drop=True)
    state = state.reset_index(drop=True)
    arrays = engine_arrays(fills, state, manager)
    need = ("spot", "forward", "sigma", "tau", "vol_conf", "fwd_conf", "spot_conf", "fwd_fixed", "rate_conf")
    ok = np.ones(len(fills), dtype=bool)
    for k in need:
        ok &= np.isfinite(arrays[k])
    ok &= arrays["tau"] > 0
    k_out = np.full(len(fills), np.nan)
    if ok.any():
        net, _ = ENGINES[manager]({k: v[ok] for k, v in arrays.items()}, params, is_initial)
        k_out[ok] = fills["price"].to_numpy(float)[ok] * arrays["amount"][ok] - net
    return k_out


def log_ratios(k_before, k_after) -> np.ndarray:
    """log(K_after / K_before) where both are finite and positive, else NaN."""
    kb = np.asarray(k_before, dtype=float)
    ka = np.asarray(k_after, dtype=float)
    ok = np.isfinite(kb) & np.isfinite(ka) & (kb > 0) & (ka > 0)
    out = np.full(len(kb), np.nan)
    out[ok] = np.log(ka[ok] / kb[ok])
    return out


def cell_doses(cells, k_before, k_after) -> pd.DataFrame:
    """Dose per cell: mean log ratio over the fills with positive K before and after; counts of all, valid,
    non-positive and missing capitals."""
    kb = np.asarray(k_before, dtype=float)
    ka = np.asarray(k_after, dtype=float)
    fin = np.isfinite(kb) & np.isfinite(ka)
    df = pd.DataFrame({"cell": np.asarray(cells, dtype=object), "lr": log_ratios(kb, ka),
                       "nonpos": fin & ((kb <= 0) | (ka <= 0)), "nan": ~fin})
    if len(df) == 0:
        return pd.DataFrame(columns=DOSE_COLUMNS)
    g = df.groupby("cell", sort=True)
    out = pd.DataFrame({"dose": g["lr"].mean(), "n_fills": g.size(), "n_valid": g["lr"].count(),
                        "n_nonpos": g["nonpos"].sum(), "n_nan": g["nan"].sum()}).reset_index()
    for c in ("n_fills", "n_valid", "n_nonpos", "n_nan"):
        out[c] = out[c].astype(int)
    return out[DOSE_COLUMNS]


def dose_window(ts_ms, event_ts: int, window_days: int = WINDOW_DAYS) -> np.ndarray:
    """Fills (taker time in ms) in ``[e - window, e)``."""
    ts = np.asarray(ts_ms, dtype=np.int64)
    return (ts >= (int(event_ts) - window_days * DAY) * 1000) & (ts < int(event_ts) * 1000)


def event_doses(frame: pd.DataFrame, event_ts: int, before: Mapping, after: Mapping, manager: str, hist,
                window_days: int = WINDOW_DAYS, is_initial: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Per-fill capitals and cell doses of one event. ``frame`` holds the fills of the event's currency with the
    columns ``fill_key, ts (ms), expiry, strike, is_call, maker_side, price, cell``; ``hist`` is a ``FeedHistory``
    (only ``.bulk`` is used). Returns ``(per_fill[FILL_DOSE_COLUMNS], doses[DOSE_COLUMNS])``."""
    f = frame[dose_window(frame["ts"].to_numpy(np.int64), event_ts, window_days)].reset_index(drop=True)
    if len(f) == 0:
        return pd.DataFrame(columns=FILL_DOSE_COLUMNS), pd.DataFrame(columns=DOSE_COLUMNS)
    state = hist.bulk(f["ts"].to_numpy(np.int64) // 1000, f["expiry"].to_numpy(np.int64),
                      f["strike"].to_numpy(float))
    kb = single_capital(f, state, before, manager, is_initial)
    ka = single_capital(f, state, after, manager, is_initial)
    per_fill = pd.DataFrame({"fill_key": f["fill_key"].to_numpy(), "cell": f["cell"].to_numpy(), "K_before": kb,
                             "K_after": ka, "log_ratio": log_ratios(kb, ka)})
    return per_fill, cell_doses(f["cell"].to_numpy(), kb, ka)


def flag_events(events: pd.DataFrame, doses: pd.DataFrame, min_abs_dose: float = MIN_ABS_DOSE) -> pd.DataFrame:
    """Add ``max_abs_dose`` (over all cells with a dose), fill counts and ``kept`` (max |dose| >= 1 %)."""
    ev = events.copy()
    d = doses.assign(abs_dose=doses["dose"].astype(float).abs())
    g = d.groupby("event_id")
    stats = pd.DataFrame({"max_abs_dose": g["abs_dose"].max(), "n_dose_fills": g["n_fills"].sum(),
                          "n_valid": g["n_valid"].sum(), "n_nonpos": g["n_nonpos"].sum(), "n_nan": g["n_nan"].sum(),
                          "n_cells": g["dose"].count()})
    ev = ev.drop(columns=[c for c in stats.columns if c in ev.columns]).merge(
        stats, left_on="event_id", right_index=True, how="left")
    for c in ("n_dose_fills", "n_valid", "n_nonpos", "n_nan", "n_cells"):
        ev[c] = ev[c].fillna(0).astype(int)
    ev["max_abs_dose"] = ev["max_abs_dose"].astype(float)
    ev["kept"] = (ev["max_abs_dose"] >= min_abs_dose).fillna(False).astype(bool)
    return ev


# =====================================================================================================================
# Outcome and panel
# =====================================================================================================================

def outcome_frame(markouts: pd.DataFrame, funding: pd.DataFrame) -> pd.DataFrame:
    """Per fill: key, taker time, cell, UTC day, ``y_hs_bp = 1e4 hs / index`` (hs from Paper 1's analysis frame) and
    the contract fields needed for the capital."""
    from .inference_p1 import analysis_frame

    a = analysis_frame(markouts, funding)
    return pd.DataFrame({
        "fill_key": a["trade_id"].to_numpy(), "ts": a["ts"].to_numpy(np.int64), "ccy": a["currency"].to_numpy(),
        "cell": cell_labels(a["currency"], a["maker_side"], a["delta_bucket"], a["tenor_bucket"]),
        "day": a["day"].to_numpy(), "hs": a["hs"].to_numpy(float), "index_price": a["index_price"].to_numpy(float),
        "y_hs_bp": 1e4 * a["hs"].to_numpy(float) / a["index_price"].to_numpy(float),
        "price": a["price"].to_numpy(float), "maker_side": a["maker_side"].to_numpy(np.int64),
        "expiry": a["expiry"].to_numpy(np.int64), "strike": a["strike"].to_numpy(float),
        "is_call": (a["option_type"] == "C").to_numpy(bool)})


def load_frame(markouts_path: Path = MARKOUTS, funding_path: Path = FUNDING) -> pd.DataFrame:
    """:func:`outcome_frame` of all Paper 1 fills (only the needed markout columns are read)."""
    return outcome_frame(pd.read_parquet(markouts_path, columns=MARKOUT_COLUMNS), pd.read_parquet(funding_path))


def build_panel(frame: pd.DataFrame, ccy: str, event_ts: int, doses, event_id: str,
                window_days: int = WINDOW_DAYS, min_fills: int = MIN_SIDE_FILLS) -> pd.DataFrame:
    """H4 panel of one (real or placebo) event date and dose vector.

    ``frame`` needs ``fill_key, ts (ms), ccy, cell, y_hs_bp, day``; ``doses`` maps cell -> dose (dict or Series).
    Fills of ``ccy`` with taker time in ``[e - window, e + window]``, without the UTC day of ``e`` and with a finite
    ``y_hs_bp``; ``post`` = day after the event day; only cells with a finite dose and at least ``min_fills`` fills
    before and after. Returns ``PANEL_COLUMNS``."""
    d = pd.Series(doses, dtype=float) if not isinstance(doses, pd.Series) else doses.astype(float)
    d = d[np.isfinite(d.to_numpy())]
    e = int(event_ts)
    ev_day = _utc_day([e])[0]
    ts = frame["ts"].to_numpy(np.int64)
    y = frame["y_hs_bp"].to_numpy(float)
    m = ((frame["ccy"].to_numpy() == ccy) & (ts >= (e - window_days * DAY) * 1000)
         & (ts <= (e + window_days * DAY) * 1000) & (frame["day"].to_numpy() != ev_day) & np.isfinite(y)
         & frame["cell"].isin(d.index).to_numpy())
    sub = frame.loc[m, ["fill_key", "cell", "y_hs_bp", "day"]]
    post = sub["day"].to_numpy() > ev_day
    counts = pd.DataFrame({"cell": sub["cell"].to_numpy(), "post": post}).groupby("cell")["post"].agg(["sum", "size"])
    ok = counts.index[(counts["sum"] >= min_fills) & (counts["size"] - counts["sum"] >= min_fills)]
    keep = sub["cell"].isin(ok).to_numpy()
    sub = sub[keep]
    out = pd.DataFrame({"fill_key": sub["fill_key"].to_numpy(), "ccy": ccy, "cell": sub["cell"].to_numpy(),
                        "event_id": event_id, "post": post[keep].astype(bool),
                        "dose": sub["cell"].map(d).to_numpy(float), "y_hs_bp": sub["y_hs_bp"].to_numpy(float),
                        "day": sub["day"].to_numpy()}, columns=PANEL_COLUMNS)
    return out.reset_index(drop=True)


# =====================================================================================================================
# Runs (resumable) and CLI
# =====================================================================================================================

def _dose_paths(event_id: str, out_dir: Path) -> Tuple[Path, Path]:
    return out_dir / f"{event_id}.parquet", out_dir / f"{event_id}_fills.parquet"


def run_doses(ccys: Sequence[str] = CCYS, max_seconds: Optional[float] = None, out_dir: Path = DOSE_DIR,
              root: Optional[Path] = None, frame: Optional[pd.DataFrame] = None) -> dict:
    """Doses of every event of ``ccys`` not yet on disk (one FeedHistory window with SVI per event; heavy)."""
    from .p2feeds import FeedHistory

    t0 = time.monotonic()
    out_dir.mkdir(parents=True, exist_ok=True)
    events = event_list(ccys, root=root)
    todo = [ev for ev in events.to_dict("records") if not _dose_paths(ev["event_id"], out_dir)[0].exists()]
    done = []
    if todo and frame is None:
        frame = load_frame()
    for ev in todo:
        if max_seconds is not None and done and time.monotonic() - t0 > max_seconds:
            break
        e = int(ev["event_ts"])
        before, after = event_params(ev, root=root)
        fills = frame[frame["ccy"] == ev["ccy"]]
        hist = FeedHistory(ev["ccy"], start_ts=e - WINDOW_DAYS * DAY, end_ts=e)
        per_fill, doses = event_doses(fills, e, before, after, ev["manager"], hist)
        del hist
        gc.collect()
        dose_path, fill_path = _dose_paths(ev["event_id"], out_dir)
        per_fill.to_parquet(fill_path, index=False)
        doses.to_parquet(dose_path, index=False)  # written last: marks the event as done
        done.append(ev["event_id"])
        print(f"{ev['event_id']}: {len(per_fill)} fills, {len(doses)} cells, max |dose| "
              f"{np.nanmax(np.abs(doses['dose'])) if len(doses) and doses['dose'].notna().any() else float('nan'):.4f}"
              f" ({time.monotonic() - t0:.0f} s)", flush=True)
    remaining = len(todo) - len(done)
    return {"done": done, "remaining": remaining, "status": "DONE" if remaining == 0 else "PARTIAL"}


def load_doses(events: pd.DataFrame, out_dir: Path = DOSE_DIR) -> pd.DataFrame:
    """Cell doses of all events (``event_id, ccy`` + ``DOSE_COLUMNS``); every event must have been run."""
    parts = []
    missing = []
    for ev in events.itertuples():
        path = _dose_paths(ev.event_id, out_dir)[0]
        if not path.exists():
            missing.append(ev.event_id)
            continue
        d = pd.read_parquet(path)
        d.insert(0, "ccy", ev.ccy)
        d.insert(0, "event_id", ev.event_id)
        parts.append(d)
    if missing:
        raise FileNotFoundError(f"doses missing for {missing}; run `p2events doses` first")
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["event_id", "ccy"] + DOSE_COLUMNS)


def dose_vectors(doses: pd.DataFrame) -> Dict[str, pd.Series]:
    """event_id -> Series cell -> dose (finite doses only), e.g. for placebo panels in stage C."""
    d = doses[np.isfinite(doses["dose"].astype(float))]
    return {eid: g.set_index("cell")["dose"].astype(float) for eid, g in d.groupby("event_id", sort=True)}


def run_panel(root: Optional[Path] = None, out_dir: Path = DOSE_DIR, frame: Optional[pd.DataFrame] = None,
              events_csv: Path = EVENTS_CSV, doses_csv: Path = DOSES_CSV, panel_path: Path = PANEL_PATH,
              ccys: Sequence[str] = CCYS) -> dict:
    """events.csv, h4_doses.csv and the panel of all kept events."""
    events = event_list(ccys, root=root)
    doses = load_doses(events, out_dir)
    events = flag_events(events, doses)
    if frame is None:
        frame = load_frame()
    vectors = dose_vectors(doses)
    panels = []
    stats = {}
    for ev in events[events["kept"]].itertuples():
        p = build_panel(frame, ev.ccy, int(ev.event_ts), vectors.get(ev.event_id, {}), ev.event_id)
        panels.append(p)
        stats[ev.event_id] = (p["cell"].nunique(), int((~p["post"]).sum()), int(p["post"].sum()))
    panel = pd.concat(panels, ignore_index=True) if panels else pd.DataFrame(columns=PANEL_COLUMNS)
    for i, c in enumerate(("panel_cells", "panel_fills_pre", "panel_fills_post")):
        events[c] = events["event_id"].map({k: v[i] for k, v in stats.items()}).fillna(0).astype(int)
    events_csv.parent.mkdir(parents=True, exist_ok=True)
    events[EVENTS_CSV_COLUMNS].to_csv(events_csv, index=False)
    doses.to_csv(doses_csv, index=False)
    panel_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(panel_path, index=False)
    return {"events": int(len(events)), "kept": int(events["kept"].sum()), "panel_rows": int(len(panel)),
            "panel_cells": int(panel.groupby("event_id")["cell"].nunique().sum()) if len(panel) else 0}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m derive_surface.p2events")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("events", help="list the H4 events")
    s = sub.add_parser("doses", help="cell doses per event (FeedHistory with SVI: run under scripts/p2_heavy.py)")
    s.add_argument("--ccy", action="append", choices=CCYS)
    s.add_argument("--max-seconds", type=float, default=None)
    sub.add_parser("panel", help="events.csv, h4_doses.csv and h4_panel.parquet")
    a = ap.parse_args(argv)
    if a.cmd == "events":
        print(event_list().to_string(index=False))
    elif a.cmd == "doses":
        res = run_doses(tuple(a.ccy) if a.ccy else CCYS, max_seconds=a.max_seconds)
        print(res["status"], f"remaining={res['remaining']}", flush=True)
    else:
        print(json.dumps(run_panel()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
