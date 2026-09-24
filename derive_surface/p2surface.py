"""The engine's view of the vol surface: chain SVI curves as a :class:`~derive_surface.surface.Surface`, the capital
of one contract on the call-delta x tenor grid, a fixed reference book over time, frames and animations.

* :func:`chain_surface` turns the SVI curves of the Lyra vol feed at one time into a ``Surface`` (adapter
  :class:`ChainSmile`, like ``StickyStrikeSmile`` in ``shock.py``): the vol at strike ``K`` is exactly
  ``LyraVolFeed.getVol`` (``chainfeeds.svi_vol`` with the curve's own ``SVI_fwd`` and ``SVI_refTau``), the smile's
  forward ``F`` is the forward feed of the expiry (the forward every engine prices with), and the total variance
  uses the true time to expiry.
* :func:`capital_grid` prices one contract (short or long) at every node of the call-delta x tenor grid of
  ``surface.py`` (total variance linear in tenor at fixed delta, OTM option per node: call where ``K >= F``) and
  runs the vectorised engine replica (``margin_sm``, ``margin_pm`` or ``margin_pm2``) with the parameters in force.
  The trade price ``p`` is the Black-76 mark on the node's forward with discount 1 (the SM and legacy-PM valuation,
  so that an SM short costs exactly ``a * S``); the capital is ``K = p q - net_IM(q; cash = 0)`` per contract and
  ``K_per_forward_bp = 1e4 K / F``. Between listed expiries the forward and the PM2 rate are interpolated linearly
  in tenor and a node takes the smaller confidence of its two neighbouring expiries.
* :func:`reference_book_series` computes, every day at 08:00 UTC, the capital of a fixed reference book: a short
  ATM straddle (strike = forward of the expiry whose time to expiry is closest to 30 days, one contract per leg,
  both legs at the Black-76 mark with D = 1) under SM, legacy PM and PM2 in their preregistered windows, and the
  same book and market with the parameters of the day before (pure parameter effect).
* :func:`render_frame` / :func:`animate` draw the surface in 3D (height = implied vol, colour = capital) in the
  figure style of the paper (Okabe-Ito for the managers, the greyscale-safe ``cividis`` ramp for capital) and write
  GIF (and MP4 when ``imageio`` is installed) like ``docs/media``.

Memory: a feed history with SVI curves needs a few GB for a full currency. Runs from the command line load one
currency at a time in quarterly windows and must go through ``scripts/p2_heavy.py``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import time
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402

from . import figstyle, margin_pm, margin_pm2, margin_sm  # noqa: E402
from .chainfeeds import svi_vol  # noqa: E402
from .p2feeds import FeedHistory  # noqa: E402
from .p2params import Timeline  # noqa: E402
from .p2types import YEAR, Book, MarketState, OptionLeg  # noqa: E402
from .surface import DELTA_AXIS, Smile, Surface  # noqa: E402

log = logging.getLogger(__name__)

DAY = 86_400
MANAGERS = ("sm", "pm", "pm2")
ENGINES = {"sm": margin_sm, "pm": margin_pm, "pm2": margin_pm2}
SIDES = {"short": -1.0, "sell": -1.0, "long": 1.0, "buy": 1.0}
REF_HOUR = 8            # daily construction time of the reference book (UTC)
REF_TARGET_DAYS = 30.0  # the reference straddle uses the expiry closest to 30 days
END_DAY = "2026-09-17"  # pilot cut 17.09.2026 12:00 UTC (the 08:00 book of that day is inside)
REF_START = {"BTC": "2024-01-11", "ETH": "2024-01-11", "HYPE": "2025-11-11"}
SURFACE_DIR = Path("data/p2/surface")
PARTS_DIR = SURFACE_DIR / "refbook"
REF_CSV = Path("results/p2/reference_book.csv")
LIVE_MAX_AGE = DAY      # an expiry is live when its forward and SVI pushes are at most one day old
MIN_DAYS = 0.5          # expiries closer than half a day are left out of the surface
ANIM_DAYS = np.geomspace(1.0, 365.0, 20)  # fixed tenor axis of animations (days)


def _ts(s: str) -> int:
    return int(pd.Timestamp(s, tz="UTC").timestamp())


# Manager windows of the preregistration (start, inclusive); SM and legacy PM over the whole sample (HYPE SM from
# 11.11.2025), PM2 for BTC/ETH from 12.06.2025 23:00 UTC and for HYPE from 11.11.2025; no legacy PM for HYPE.
WINDOW_START: Dict[tuple, Optional[int]] = {
    ("BTC", "sm"): _ts("2024-01-11"), ("ETH", "sm"): _ts("2024-01-11"), ("HYPE", "sm"): _ts("2025-11-11"),
    ("BTC", "pm"): _ts("2024-01-11"), ("ETH", "pm"): _ts("2024-01-11"), ("HYPE", "pm"): None,
    ("BTC", "pm2"): _ts("2025-06-12 23:00"), ("ETH", "pm2"): _ts("2025-06-12 23:00"),
    ("HYPE", "pm2"): _ts("2025-11-11"),
}

# figure style: managers in fixed Okabe-Ito slots, line styles as a second channel for greyscale print
MANAGER_COLORS = {"pm2": figstyle.PALETTE[0], "sm": figstyle.PALETTE[1], "pm": figstyle.PALETTE[2]}
MANAGER_STYLES = {"pm2": "-", "sm": "--", "pm": ":"}
MANAGER_LABELS = {"sm": "SM (standard margin)", "pm": "Legacy PM", "pm2": "PM2 (portfolio margin 2)"}
INK = "#1a1a1a"
NA_COLOR = (0.85, 0.85, 0.85, 1.0)
CMAP_NAME = "cividis"


def manager_available(ccy: str, mgr: str, ts: int) -> bool:
    """True when ``mgr`` is inside its preregistered window for ``ccy`` at ``ts``."""
    start = WINDOW_START.get((ccy, mgr))
    return start is not None and int(ts) >= start


def colormap():
    """The sequential colour ramp for capital (``cividis``: monotone luminance, readable in greyscale)."""
    return matplotlib.colormaps[CMAP_NAME]


# ---------------------------------------------------------------------------------------------------- chain smile

class ChainSmile(Smile):
    """One on-chain SVI curve as a :class:`Smile`: vol exactly ``LyraVolFeed.getVol``, total variance on the true T.

    ``forward`` is the forward feed of the expiry (log-moneyness ``k`` is relative to it); ``svi`` is
    ``(a, b, rho, m, sigma, ref_tau)`` and ``svi_fwd`` the forward the curve was fitted on (the feed's own
    moneyness reference). ``k``/``iv`` hold a probe of the curve on |k| <= 0.6 for ``wing_pad``/``k_range``.
    """

    def __init__(self, expiry: int, T: float, forward: float, svi: Sequence[float], svi_fwd: Optional[float] = None):
        a, b, rho, m, sig, ref_tau = (float(x) for x in svi)
        self.svi = (a, b, rho, m, sig, ref_tau)
        self.svi_fwd = float(svi_fwd) if svi_fwd is not None and np.isfinite(svi_fwd) else float(forward)
        F = float(forward)
        kk = np.linspace(-0.6, 0.6, 61)
        iv = self._feed_vol(F * np.exp(kk))
        super().__init__(int(expiry), float(T), F, 1.0, kk, iv, np.ones_like(kk), "chain", np.zeros(1))

    def _feed_vol(self, strike) -> np.ndarray:
        a, b, rho, m, sig, ref_tau = self.svi
        return svi_vol(np.asarray(strike, dtype=float), a, b, rho, m, sig, self.svi_fwd, ref_tau)

    def total_variance(self, k: np.ndarray) -> np.ndarray:
        k = np.asarray(k, dtype=float)
        return self._feed_vol(self.F * np.exp(k)) ** 2 * self.T

    def dw_dk(self, k: np.ndarray) -> np.ndarray:
        """Slope of the total variance; 0 where the feed clips moneyness or caps w (the curve is flat there)."""
        a, b, rho, m, sig, ref_tau = self.svi
        k = np.asarray(k, dtype=float)
        kf = k + np.log(self.F / self.svi_fwd)  # moneyness against SVI_fwd
        bound = 4.0 * np.sqrt(max(a + b * sig, 0.0))
        km = np.clip(kf, -bound, bound) - m
        root = np.sqrt(km * km + sig * sig)
        w = a + b * (root + rho * km)
        slope = b * (rho + km / root)
        active = (np.abs(kf) < bound) & (w < 144.0)
        return np.where(active, slope * self.T / ref_tau, 0.0)


def surface_from_state(state: MarketState, *, min_days: float = MIN_DAYS) -> Surface:
    """``Surface`` of every expiry of ``state`` with an SVI curve and a forward, at least ``min_days`` out."""
    smiles = []
    for e, es in state.expiries.items():
        T = (int(e) - state.ts) / YEAR
        if T * 365.0 < min_days or es.svi is None or not np.isfinite(es.forward):
            continue
        smiles.append(ChainSmile(int(e), T, float(es.forward), es.svi, es.svi_fwd))
    if not smiles:
        raise ValueError(f"{state.currency} {state.ts}: no SVI curve at least {min_days} days out")
    smiles.sort(key=lambda s: s.T)
    return Surface(int(state.ts) * 1000, state.currency, float(state.spot), smiles)


def live_expiries(hist: FeedHistory, ts: int, *, max_age: int = LIVE_MAX_AGE, min_days: float = MIN_DAYS) -> List[int]:
    """Expiries more than ``min_days`` after ``ts`` whose forward and SVI curve were signed at most ``max_age`` ago."""
    e = np.asarray(hist.svi.expiries, dtype=np.int64)
    e = e[e > int(ts) + min_days * DAY]
    if len(e) == 0:
        return []
    b = hist.bulk(np.full(len(e), int(ts)), e, np.full(len(e), np.nan))
    ok = (b["vol_age"].to_numpy() <= max_age) & (b["fwd_age"].to_numpy() <= max_age) & np.isfinite(b["forward"])
    return [int(x) for x in e[ok]]


def load_history(ccy: str, start_ts: int, end_ts: int) -> FeedHistory:
    """Feed history of ``ccy`` restricted to [start_ts, end_ts] (exact state inside; heavy: use p2_heavy.py)."""
    return FeedHistory(ccy, start_ts=int(start_ts), end_ts=int(end_ts))


def _state_and_surface(ccy: str, ts: int, hist: Optional[FeedHistory], state: Optional[MarketState],
                       min_days: float = MIN_DAYS):
    if state is None:
        hist = hist if hist is not None else load_history(ccy, int(ts) - DAY, int(ts))
        state = hist.state_at(int(ts), live_expiries(hist, int(ts), min_days=min_days))
    return state, surface_from_state(state, min_days=min_days)


def chain_surface(ccy: str, ts: int, hist: Optional[FeedHistory] = None, *, state: Optional[MarketState] = None,
                  min_days: float = MIN_DAYS) -> Surface:
    """The vol surface of the chain at ``ts``: one :class:`ChainSmile` per live expiry (see :func:`live_expiries`)."""
    return _state_and_surface(ccy, ts, hist, state, min_days)[1]


# ---------------------------------------------------------------------------------------------------- capital grid

def _bracket_min(t: np.ndarray, T: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Per tenor ``t`` the smaller value of the two neighbouring expiries (the expiry's own value on a node)."""
    j = np.clip(np.searchsorted(T, t, side="left"), 0, len(T) - 1)
    i = np.clip(j - 1, 0, len(T) - 1)
    exact = np.isclose(T[j], t, rtol=0.0, atol=1e-15)
    return np.where(exact, v[j], np.minimum(v[i], v[j]))


def grid_nodes(surface: Surface, state: MarketState, x: Optional[np.ndarray] = None,
               tenors: Optional[np.ndarray] = None, n_tenors: int = 24, option: str = "otm") -> pd.DataFrame:
    """Engine inputs at every node of the call-delta x tenor grid (tenors outside the listed range are dropped)."""
    T_exp = surface.tenors
    if tenors is not None:
        tenors = np.asarray(tenors, dtype=float)
        tenors = tenors[(tenors >= T_exp.min() - 1e-15) & (tenors <= T_exp.max() + 1e-15)]
        if len(tenors) == 0:
            raise ValueError("no tenor inside the listed expiry range")
    g = surface.greeks_grid("delta", x if x is None else np.asarray(x, dtype=float), tenors, n_tenors)
    x, tn, iv, K = g["x"], g["tenors"], g["iv"], g["strike"]
    exps = [s.expiry for s in surface.smiles]
    ess = [state.expiries[e] for e in exps]

    def per_tenor(vals, how="interp"):
        vals = np.asarray(vals, dtype=float)
        return np.interp(tn, T_exp, vals) if how == "interp" else _bracket_min(tn, T_exp, vals)

    F = per_tenor([s.F for s in surface.smiles])
    cols = {
        "rate": per_tenor([es.rate for es in ess]),
        "rate_conf": per_tenor([getattr(es, "rate_conf", 1.0) for es in ess], "min"),
        "vol_conf": per_tenor([es.vol_conf for es in ess], "min"),
        "fwd_conf": per_tenor([es.fwd_conf for es in ess], "min"),
    }
    n_t, n_x = iv.shape
    tt = np.repeat(tn, n_x)
    out = pd.DataFrame({"delta": np.tile(x, n_t), "tau": tt, "tenor_days": tt * 365.0,
                        "forward": np.repeat(F, n_x), "strike": K.ravel(), "iv": iv.ravel(),
                        "k": g["k"].ravel()})
    for c, v in cols.items():
        out[c] = np.repeat(v, n_x)
    if option == "otm":
        out["is_call"] = out["strike"] >= out["forward"]
    elif option in ("call", "put"):
        out["is_call"] = option == "call"
    else:
        raise ValueError(f"option must be otm, call or put, not {option!r}")
    out["spot"] = float(state.spot)
    out["spot_conf"] = float(state.spot_conf)
    return out


def _engine_arrays(nodes: pd.DataFrame, mgr: str, q: float, rate_pm: float) -> dict:
    a = {k: nodes[k].to_numpy() for k in ("spot", "forward", "tau", "strike", "vol_conf", "fwd_conf", "spot_conf",
                                          "rate")}
    a.update(sigma=nodes["iv"].to_numpy(), is_call=nodes["is_call"].to_numpy(dtype=bool),
             amount=np.full(len(nodes), float(q)), fwd_fixed=np.zeros(len(nodes)))
    # PM2 reads its own rate feed; the legacy PM its static feed (rate 0 at confidence 1); SM ignores rates
    a["rate_conf"] = nodes["rate_conf"].to_numpy() if mgr == "pm2" else np.ones(len(nodes))
    a["rate_pm"] = np.full(len(nodes), float(rate_pm))
    return a


def side_amount(side) -> float:
    if isinstance(side, str) and side.lower() in SIDES:
        return SIDES[side.lower()]
    if side in (-1, 1):
        return float(side)
    raise ValueError(f"side must be short/sell or long/buy, not {side!r}")


def capital_grid(ccy: str, ts: int, manager: str, side, *, hist: Optional[FeedHistory] = None,
                 state: Optional[MarketState] = None, params: Optional[Mapping] = None,
                 x: Optional[np.ndarray] = None, tenors: Optional[np.ndarray] = None, n_tenors: int = 24,
                 option: str = "otm", is_initial: bool = True, rate_pm: Optional[float] = None) -> pd.DataFrame:
    """Capital of one contract per node of the call-delta x tenor grid under ``manager`` at ``ts``.

    Columns: ``delta`` (call delta; a put node has put delta ``delta - 1``), ``tau`` (years), ``tenor_days``,
    ``forward``, ``strike``, ``iv``, ``is_call``, ``price`` (Black-76 mark, D = 1), ``net``, ``mtm`` (engine),
    ``K = price * q - net`` (USD per contract) and ``K_per_forward_bp``. ``params`` defaults to the timeline of
    ``results/p2/params`` at ``ts``. Raises ``ValueError`` outside the manager's preregistered window.
    """
    mgr = manager.lower()
    if mgr not in ENGINES:
        raise ValueError(f"manager must be one of {MANAGERS}, not {manager!r}")
    q = side_amount(side)
    if not manager_available(ccy, mgr, ts):
        raise ValueError(f"{mgr} is not available for {ccy} at {ts} (preregistered window)")
    if hist is None and state is None:
        hist = load_history(ccy, int(ts) - DAY, int(ts))
    state, surf = _state_and_surface(ccy, ts, hist, state)
    if params is None:
        params = Timeline(ccy, mgr).at(int(ts))
    if rate_pm is None:
        rate_pm = float(hist.bulk([int(ts)], [0], [np.nan])["rate_pm"].iloc[0]) if hist is not None else 0.0
    nodes = grid_nodes(surf, state, x, tenors, n_tenors, option)
    net, mtm = ENGINES[mgr].single(_engine_arrays(nodes, mgr, q, rate_pm), params, is_initial)
    call, put = margin_sm.b76_prices(nodes["forward"].to_numpy(), nodes["strike"].to_numpy(), nodes["iv"].to_numpy(),
                                     nodes["tau"].to_numpy() * YEAR)
    nodes["price"] = np.where(nodes["is_call"].to_numpy(dtype=bool), call, put)
    nodes["net"] = net
    nodes["mtm"] = mtm
    nodes["K"] = nodes["price"] * q - net
    nodes["K_per_forward_bp"] = 1e4 * nodes["K"] / nodes["forward"]
    nodes.insert(0, "manager", mgr)
    nodes.insert(1, "side", "short" if q < 0 else "long")
    nodes.insert(2, "ts", int(ts))
    return nodes


# ---------------------------------------------------------------------------------------------------- reference book

def reference_days(ccy: str, start: Optional[str] = None, end: str = END_DAY) -> List[str]:
    """UTC days of the reference series of ``ccy`` (from its start in the sample to the pilot cut)."""
    lo = pd.Timestamp(start or REF_START[ccy])
    return [d.strftime("%Y-%m-%d") for d in pd.date_range(lo, pd.Timestamp(end), freq="D")]


def _day_ts(day, hour: int = REF_HOUR) -> int:
    d = pd.Timestamp(day)
    d = d.tz_localize("UTC") if d.tzinfo is None else d.tz_convert("UTC")
    return int((d.normalize() + pd.Timedelta(hours=hour)).timestamp())


def _straddle(e: int, K: float) -> Book:
    return Book(options=[OptionLeg(int(e), float(K), True, -1.0), OptionLeg(int(e), float(K), False, -1.0)])


def _book_capital(mgr: str, book: Book, state: MarketState, params: Mapping, premium: float, rate_pm: float) -> float:
    kw = {"rates": {e: rate_pm for e in book.expiries()}} if mgr == "pm" else {}
    net, _ = ENGINES[mgr].net_margin(book, state, params, True, **kw)
    return float(premium - net)


def _reference_row(ccy: str, day: str, ts: int, hist: FeedHistory, timelines: Mapping[str, Timeline]) -> Optional[dict]:
    exps = live_expiries(hist, ts)
    if not exps:
        return None
    days = np.array([(e - ts) / DAY for e in exps])
    e = int(exps[int(np.argmin(np.abs(days - REF_TARGET_DAYS)))])  # ties: the earlier expiry
    state = hist.state_at(ts, [e])
    es = state.expiries[e]
    K = float(es.forward)
    sigma = float(es.vol(K))
    b = hist.bulk([ts], [e], [K]).iloc[0]
    c, p = (float(v) for v in margin_sm.b76_prices(K, K, sigma, e - ts))
    rate_pm = float(b["rate_pm"])
    book = _straddle(e, K)
    premium = -(c + p)  # sum p q with q = -1 per leg
    row = {"ccy": ccy, "day": day, "ts": int(ts), "expiry": e, "tenor_days": (e - ts) / DAY, "spot": float(state.spot),
           "forward": K, "strike": K, "sigma": sigma, "rate": float(es.rate), "rate_pm": rate_pm,
           "price_call": c, "price_put": p, "spot_age": float(b["spot_age"]), "fwd_age": float(b["fwd_age"]),
           "vol_age": float(b["vol_age"])}
    for mgr in MANAGERS:
        vals = {"K": np.nan, "K_prev": np.nan, "ts": np.nan, "ts_prev": np.nan}
        tl = timelines.get(mgr)
        if tl is not None and manager_available(ccy, mgr, ts):
            for tag, t in (("", ts), ("_prev", ts - DAY)):
                try:
                    entry = tl.entry_at(t)
                except KeyError:
                    continue
                vals["K" + tag] = _book_capital(mgr, book, state, entry["params"], premium, rate_pm)
                vals["ts" + tag] = int(entry["from_ts"])
        row[f"K_{mgr}"] = vals["K"]
        row[f"K_{mgr}_prev"] = vals["K_prev"]
        row[f"{mgr}_param_ts"] = vals["ts"]
        row[f"{mgr}_param_ts_prev"] = vals["ts_prev"]
    return row


def _timelines(ccy: str, timelines: Optional[Mapping[str, Timeline]] = None) -> Dict[str, Timeline]:
    out = {}
    for mgr in MANAGERS:
        if timelines is not None and mgr in timelines:
            out[mgr] = timelines[mgr]
        elif Timeline.path(ccy, mgr).exists():
            out[mgr] = Timeline(ccy, mgr)
    return out


def reference_book_series(ccy: str, days: Optional[Iterable] = None, *, hist: Optional[FeedHistory] = None,
                          timelines: Optional[Mapping[str, Timeline]] = None, hour: int = REF_HOUR) -> pd.DataFrame:
    """Capital of the reference short ATM straddle per day (see module doc) under SM, legacy PM and PM2.

    Columns: ``ccy, day, ts, expiry, tenor_days, spot, forward, strike, sigma, rate, rate_pm, price_call, price_put,
    spot_age, fwd_age, vol_age`` and per manager ``K_<m>`` (today's parameters), ``K_<m>_prev`` (parameters in force
    24 h earlier, same book and market), ``<m>_param_ts`` / ``<m>_param_ts_prev`` (``from_ts`` of the parameter
    entries used). Capital is NaN outside the manager windows; days without a live expiry are left out.
    ``hist`` must cover the days; without it the history is loaded per quarter (heavy).
    """
    days = [pd.Timestamp(d).strftime("%Y-%m-%d") for d in (days if days is not None else reference_days(ccy))]
    tls = _timelines(ccy, timelines)
    rows = []
    if hist is None:
        for chunk in _quarters(days).values():
            h = load_history(ccy, _day_ts(chunk[0], hour), _day_ts(chunk[-1], hour))
            rows += [r for d in chunk for r in [_reference_row(ccy, d, _day_ts(d, hour), h, tls)] if r is not None]
            del h
    else:
        rows = [r for d in days for r in [_reference_row(ccy, d, _day_ts(d, hour), hist, tls)] if r is not None]
    return pd.DataFrame(rows)


def _quarters(days: Sequence[str]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for d in days:
        t = pd.Timestamp(d)
        out.setdefault(f"{t.year}Q{(t.month - 1) // 3 + 1}", []).append(d)
    return out


def combine_parts(parts_dir: Path = PARTS_DIR, out: Path = REF_CSV) -> Path:
    """Concatenate the quarterly part files into one CSV sorted by currency and day."""
    parts = [pd.read_csv(p) for p in sorted(Path(parts_dir).glob("*_*Q*.csv"))]
    df = pd.concat(parts, ignore_index=True).sort_values(["ccy", "day"], kind="mergesort")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(out)
    return out


def run_reference_book(ccy: str, *, parts_dir: Path = PARTS_DIR, max_seconds: float = 480.0) -> dict:
    """Resumable run: one part file per quarter under ``parts_dir``; stops after ``max_seconds``."""
    t0 = time.monotonic()
    parts_dir = Path(parts_dir)
    parts_dir.mkdir(parents=True, exist_ok=True)
    chunks = _quarters(reference_days(ccy))
    done = 0
    for tag, chunk in chunks.items():
        path = parts_dir / f"{ccy}_{tag}.csv"
        if path.exists():
            done += 1
            continue
        if time.monotonic() - t0 > max_seconds:
            break
        t1 = time.monotonic()
        df = reference_book_series(ccy, chunk)
        tmp = path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        tmp.replace(path)
        done += 1
        log.info("%s %s: %d of %d days in %.0f s", ccy, tag, len(df), len(chunk), time.monotonic() - t1)
    return {"ccy": ccy, "done": done, "total": len(chunks), "remaining": len(chunks) - done}


# ---------------------------------------------------------------------------------------------------- frames

def param_events(ccy: str, managers: Sequence[str] = ("pm2", "pm"), keys: Optional[Mapping[str, Sequence[str]]] = None
                 ) -> pd.DataFrame:
    """Capital-relevant parameter changes (``Timeline.changes(keys=...)``) inside the manager windows."""
    default = {"pm2": ["VolShockParameters", "MarginParameters", "BasisContingencyParameters",
                       "OtherContingencyParameters", "SkewShockParameters", "scenarios"],
               "pm": ["VolShockParameters", "MarginParameters", "BasisContingencyParameters",
                      "OtherContingencyParameters", "scenarios"],
               "sm": ["OptionMarginParams"]}
    rows = []
    for mgr in managers:
        if WINDOW_START.get((ccy, mgr)) is None or not Timeline.path(ccy, mgr).exists():
            continue
        for t in Timeline(ccy, mgr).changes(keys=(keys or default)[mgr]):
            if manager_available(ccy, mgr, t):
                rows.append({"ts": int(t), "manager": mgr})
    return pd.DataFrame(rows, columns=["ts", "manager"])


def _pivot(grid: pd.DataFrame, value: str):
    iv = grid.pivot(index="tau", columns="delta", values="iv")
    c = grid.pivot(index="tau", columns="delta", values=value).reindex_like(iv)
    return iv.columns.to_numpy(float), iv.index.to_numpy(float), iv.to_numpy(float) * 100.0, c.to_numpy(float)


def fit_limits(frames: Sequence[Mapping[str, Optional[pd.DataFrame]]], value: str = "K_per_forward_bp") -> dict:
    """Colour, height and tenor limits shared by all frames (1st to 99th percentile)."""
    zs, cs, ds = [], [], []
    for grids in frames:
        for g in grids.values():
            if g is None or len(g) == 0:
                continue
            zs.append(g["iv"].to_numpy() * 100)
            cs.append(g[value].to_numpy())
            ds.append(g["tenor_days"].to_numpy())
    if not zs:  # every panel outside its manager window
        return {"zlim": None, "clim": (0.0, 1.0), "ylim_days": None}
    z, c, d = (np.concatenate(v) for v in (zs, cs, ds))
    zlo, zhi = np.nanpercentile(z, [1, 99])
    pad = 0.06 * (zhi - zlo)
    clo, chi = np.nanpercentile(c, [1, 99])
    return {"zlim": (zlo - pad, zhi + pad), "clim": (clo, chi), "ylim_days": (float(np.nanmin(d)), float(np.nanmax(d)))}


def _draw_panel(ax, grid: Optional[pd.DataFrame], mgr: str, *, value: str, norm, zlim, ylim_days, fs: float) -> None:
    ax.set_facecolor("white")
    for axis_ in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis_.set_pane_color((1, 1, 1, 0))
        axis_._axinfo["grid"]["color"] = (0.85, 0.85, 0.85, 1.0)
    ax.set_title(MANAGER_LABELS.get(mgr, mgr), fontsize=fs + 1, color=INK, pad=0)
    if grid is None or len(grid) == 0:
        ax.text2D(0.5, 0.5, "outside the manager window", transform=ax.transAxes, ha="center", fontsize=fs,
                  color=figstyle.GREY)
        ax.set_axis_off()
        return
    x, tau, Z, C = _pivot(grid, value)
    days = tau * 365.0
    X, Y = np.meshgrid(x, np.log10(days))
    colors = colormap()(norm(np.nan_to_num(C, nan=norm.vmin)))
    colors[~np.isfinite(C)] = NA_COLOR
    ax.plot_surface(X, Y, Z, facecolors=colors, rstride=1, cstride=1, linewidth=0.2, edgecolor=(0, 0, 0, 0.10),
                    shade=False, antialiased=True)
    ax.view_init(elev=24, azim=-128)
    ax.tick_params(colors=figstyle.GREY, labelsize=fs - 1, pad=0)
    ax.set_xlabel("Call delta (put = Δ − 1)", fontsize=fs, color=INK, labelpad=2)
    ax.set_xticks([0.1, 0.25, 0.5, 0.75, 0.9])
    y0, y1 = ylim_days or (days.min(), days.max())
    ticks = np.array([1, 2, 7, 14, 30, 90, 180, 365])
    ticks = ticks[(ticks >= y0 * 0.95) & (ticks <= y1 * 1.05)]
    ax.set_yticks(np.log10(ticks))
    ax.set_yticklabels([f"{t:d}d" for t in ticks])
    ax.set_ylim(np.log10(y0), np.log10(y1))
    ax.set_ylabel("Days to expiry", fontsize=fs, color=INK, labelpad=2)
    ax.set_zlabel("Implied vol (%)", fontsize=fs, color=INK, labelpad=0)
    if zlim:
        ax.set_zlim(*zlim)
    ax.set_xlim(x.min(), x.max())


def _draw_series(ax, series: pd.DataFrame, ts: int, events: Iterable[int], label: str, fs: float) -> None:
    t = pd.to_datetime(series["ts"], unit="s")
    for mgr in ("pm2", "sm", "pm"):
        if mgr in series.columns and series[mgr].notna().any():
            ax.plot(t, series[mgr], color=MANAGER_COLORS[mgr], linestyle=MANAGER_STYLES[mgr], linewidth=1.1,
                    label=MANAGER_LABELS[mgr].split(" (")[0])
    lo, hi = int(series["ts"].min()), int(series["ts"].max())
    for ev in events or []:
        if lo <= int(ev) <= hi:  # events outside the strip would widen its time axis
            ax.axvline(pd.to_datetime(int(ev), unit="s"), color=figstyle.GREY, linewidth=0.5, linestyle=(0, (1, 2)))
    if lo <= int(ts) <= hi:
        ax.axvline(pd.to_datetime(int(ts), unit="s"), color=INK, linewidth=0.9)
    ax.set_xlim(t.min(), t.max())
    ax.set_title(label, fontsize=fs, color=INK, loc="left", pad=2)
    ax.tick_params(labelsize=fs - 1, colors=figstyle.GREY)
    ax.grid(True, alpha=0.25, linewidth=0.4)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper right", fontsize=fs - 1, frameon=False, ncol=3, bbox_to_anchor=(1.0, 1.25))


def render_frame(grids: Mapping[str, Optional[pd.DataFrame]], *, ccy: str, ts: int, side: str = "short",
                 value: str = "K_per_forward_bp", clim=None, zlim=None, ylim_days=None,
                 series: Optional[pd.DataFrame] = None, events: Optional[Iterable[int]] = None,
                 series_label: str = "Reference short ATM straddle, about 30 days: capital (bp of forward)",
                 width: int = 960, height: int = 540, dpi: int = 100, title: Optional[str] = None) -> np.ndarray:
    """One frame: a 3D panel per manager (height IV, colour capital on a shared scale), optionally a time strip.

    ``grids`` maps manager -> :func:`capital_grid` frame (None = outside the window). ``series`` has a ``ts``
    column (seconds) and one column per manager; ``events`` are parameter-change times drawn on the strip.
    Returns an RGB array of ``height`` x ``width`` pixels.
    """
    figstyle.use_style()
    fs = 8.0
    lim = fit_limits([grids], value) if (clim is None or zlim is None) else {}
    clim = clim or lim["clim"]
    zlim = zlim or lim["zlim"]
    ylim_days = ylim_days or lim.get("ylim_days")
    norm = Normalize(*clim)
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor="white")
    rows = [3.2, 1.0] if series is not None else [1.0]
    n = len(grids)
    gs = GridSpec(len(rows), n + 1, figure=fig, height_ratios=rows, width_ratios=[1.0] * n + [0.035],
                  left=0.04, right=0.93, top=0.86, bottom=0.10 if series is not None else 0.04, wspace=0.05,
                  hspace=0.25)
    for i, (mgr, g) in enumerate(grids.items()):
        ax = fig.add_subplot(gs[0, i], projection="3d")
        _draw_panel(ax, g, mgr, value=value, norm=norm, zlim=zlim, ylim_days=ylim_days, fs=fs)
    cax = fig.add_subplot(gs[0, n])
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=colormap()), cax=cax)
    unit = "bp of forward" if value == "K_per_forward_bp" else value
    cb.set_label(f"Capital per {side} contract ({unit})", fontsize=fs, color=INK)
    cb.ax.tick_params(labelsize=fs - 1, colors=figstyle.GREY)
    if series is not None:
        ax_s = fig.add_subplot(gs[1, :n])
        _draw_series(ax_s, series, ts, events or [], series_label, fs)
    when = dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fig.text(0.04, 0.955, title or f"{ccy} · the engine's view of the vol surface", fontsize=fs + 3, color=INK,
             weight="bold")
    fig.text(0.96, 0.955, when, fontsize=fs + 1, color=figstyle.GREY, ha="right")
    fig.text(0.04, 0.905, "Height: implied vol of the on-chain SVI feed · colour: initial-margin capital "
             "K = p·q − net per contract at the Black-76 mark (chain parameters and feeds)",
             fontsize=fs, color=figstyle.GREY)
    fig.canvas.draw()
    rgb = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    plt.close(fig)
    return rgb


def save_frame(grids: Mapping[str, Optional[pd.DataFrame]], path: Path, **kw) -> Path:
    """:func:`render_frame` written as PNG."""
    from PIL import Image

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(render_frame(grids, **kw)).save(path, optimize=True)
    return path


# ---------------------------------------------------------------------------------------------------- animation

def _frame_grids(ccy: str, ts: int, hist: FeedHistory, managers: Sequence[str], side: str,
                 tenors: np.ndarray) -> Dict[str, Optional[pd.DataFrame]]:
    state = hist.state_at(ts, live_expiries(hist, ts))
    out: Dict[str, Optional[pd.DataFrame]] = {}
    for mgr in managers:
        out[mgr] = capital_grid(ccy, ts, mgr, side, hist=hist, state=state, tenors=tenors) \
            if manager_available(ccy, mgr, ts) else None
    return out


def animate(ccy: str, days: Iterable, out, *, hist: Optional[FeedHistory] = None,
            managers: Sequence[str] = ("pm2", "sm"), side: str = "short", hour: int = REF_HOUR, fps: float = 4,
            width: int = 960, height: int = 540, series: Optional[pd.DataFrame] = None,
            events: Optional[Iterable[int]] = None, hold_last: int = 6, name: Optional[str] = None) -> Path:
    """GIF (and MP4 when ``imageio`` is installed) of the capital surface, one frame per day at ``hour`` UTC.

    ``out`` is a directory; the file is ``{ccy}_capital_{side}_{first}_{last}.gif`` unless ``name`` is given.
    Without ``hist`` the feed history is loaded per quarter (heavy: run through ``scripts/p2_heavy.py``).
    """
    from .animate import write_gif, write_mp4

    days = [pd.Timestamp(d).strftime("%Y-%m-%d") for d in days]
    tenors = ANIM_DAYS / 365.0
    frames = []
    chunks = _quarters(days).values() if hist is None else [days]
    for chunk in chunks:
        h = hist if hist is not None else load_history(ccy, _day_ts(chunk[0], hour), _day_ts(chunk[-1], hour))
        for d in chunk:
            ts = _day_ts(d, hour)
            try:
                frames.append((ts, _frame_grids(ccy, ts, h, managers, side, tenors)))
            except ValueError as exc:  # no live expiry that day
                log.warning("%s %s skipped: %s", ccy, d, exc)
    if not frames:
        raise ValueError("no frame")
    lim = fit_limits([g for _, g in frames])
    rgb = [render_frame(g, ccy=ccy, ts=ts, side=side, series=series, events=events, width=width, height=height,
                        **lim) for ts, g in frames]
    out = Path(out)
    tag = name or f"{ccy}_capital_{side}_{days[0]}_{days[-1]}"
    write_mp4(rgb, out / f"{tag}.mp4", fps)
    return write_gif(rgb, out / f"{tag}.gif", fps, hold_last=hold_last)


def reference_series_bp(ccy: str, path: Path = REF_CSV) -> Optional[pd.DataFrame]:
    """Reference-book capital in bp of the forward per manager (``ts`` plus one column per manager)."""
    path = Path(path)
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df = df[df["ccy"] == ccy]
    out = pd.DataFrame({"ts": df["ts"].to_numpy()})
    for mgr in MANAGERS:
        out[mgr] = (1e4 * df[f"K_{mgr}"] / df["forward"]).to_numpy()
    return out


# ---------------------------------------------------------------------------------------------------- probe and CLI

def probe(ccy: str = "BTC", day: str = END_DAY, managers: Sequence[str] = ("pm2", "sm"), side: str = "short",
          out_dir: Path = SURFACE_DIR, hour: int = REF_HOUR) -> dict:
    """Stills of one day (one PNG per manager and one side by side) plus the grid values as CSV."""
    ts = _day_ts(day, hour)
    hist = load_history(ccy, ts - DAY, ts)
    grids = _frame_grids(ccy, ts, hist, managers, side, ANIM_DAYS / 365.0)
    lim = fit_limits([grids])
    out_dir = Path(out_dir)
    stem = f"probe_{ccy}_{day}"
    paths = [save_frame(grids, out_dir / f"{stem}_{'_'.join(managers)}.png", ccy=ccy, ts=ts, side=side,
                        width=1600, height=800, dpi=160, **lim)]
    for mgr in managers:
        paths.append(save_frame({mgr: grids[mgr]}, out_dir / f"{stem}_{mgr}.png", ccy=ccy, ts=ts, side=side,
                                width=1000, height=800, dpi=160, **lim))
    table = pd.concat([g for g in grids.values() if g is not None], ignore_index=True)
    table.to_csv(out_dir / f"{stem}_grid.csv", index=False)
    summary = {"ts": ts, "paths": [str(p) for p in paths], "n_expiries": len(live_expiries(hist, ts)),
               "limits": {k: list(map(float, v)) for k, v in lim.items()}}
    for mgr, g in grids.items():
        if g is not None:
            summary[mgr] = {"K_bp_min": float(g["K_per_forward_bp"].min()),
                            "K_bp_median": float(g["K_per_forward_bp"].median()),
                            "K_bp_max": float(g["K_per_forward_bp"].max())}
    (out_dir / f"{stem}_summary.json").write_text(json.dumps(summary, indent=1))
    return summary


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser(prog="python3 -m derive_surface.p2surface")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe")
    p.add_argument("--ccy", default="BTC")
    p.add_argument("--day", default=END_DAY)
    p.add_argument("--managers", default="pm2,sm")
    p.add_argument("--side", default="short")
    p.add_argument("--out", default=str(SURFACE_DIR))
    r = sub.add_parser("refbook")
    r.add_argument("--ccy", required=True)
    r.add_argument("--max-seconds", type=float, default=480.0)
    r.add_argument("--parts", default=str(PARTS_DIR))
    c = sub.add_parser("refbook-combine")
    c.add_argument("--parts", default=str(PARTS_DIR))
    c.add_argument("--out", default=str(REF_CSV))
    a = sub.add_parser("animate")
    a.add_argument("--ccy", default="BTC")
    a.add_argument("--start", required=True)
    a.add_argument("--end", required=True)
    a.add_argument("--managers", default="pm2,sm")
    a.add_argument("--side", default="short")
    a.add_argument("--out", default=str(SURFACE_DIR))
    a.add_argument("--series", default=str(REF_CSV))
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.cmd == "probe":
        print(json.dumps(probe(args.ccy, args.day, tuple(args.managers.split(",")), args.side, Path(args.out)),
                         indent=1))
    elif args.cmd == "refbook":
        print(json.dumps(run_reference_book(args.ccy, parts_dir=Path(args.parts), max_seconds=args.max_seconds)))
    elif args.cmd == "refbook-combine":
        print(combine_parts(Path(args.parts), Path(args.out)))
    elif args.cmd == "animate":
        days = reference_days(args.ccy, args.start, args.end)
        managers = tuple(args.managers.split(","))
        ev = param_events(args.ccy, [m for m in managers if m != "sm"])
        series = reference_series_bp(args.ccy, Path(args.series))
        if series is not None:  # the strip shows the animated window plus 45 days on each side
            lo, hi = _day_ts(days[0]) - 45 * DAY, _day_ts(days[-1]) + 45 * DAY
            series = series[(series["ts"] >= lo) & (series["ts"] <= hi)]
        print(animate(args.ccy, days, Path(args.out), managers=managers, side=args.side, series=series,
                      events=list(ev["ts"])))


if __name__ == "__main__":
    main()
