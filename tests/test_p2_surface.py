"""Tests for derive_surface.p2surface: chain vol surface, capital grid, reference book, frames and animation.

Everything runs offline on a synthetic feed history (FeedHistory with ``frames=``) and the committed parameter
timelines under results/p2/params.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from derive_surface import margin_pm, margin_pm2, margin_sm, p2surface, pricing
from derive_surface.chainfeeds import svi_vol
from derive_surface.p2chain import block_at_ts, ts_at_block
from derive_surface.p2feeds import FeedHistory
from derive_surface.p2params import Timeline
from derive_surface.p2types import YEAR, Book, OptionLeg

DAY = 86_400
T0 = int(pd.Timestamp("2026-03-10 08:00", tz="UTC").timestamp())
LIVE_DAYS = (1, 7, 14, 28, 35, 91)  # expiries (days after T0) with fresh forward and SVI pushes
SPOT = 70_000.0


def _svi_params(tau: float):
    """A plausible SVI curve for time to expiry ``tau`` (vols roughly 45 to 60 %)."""
    return dict(svi_a=0.2 * tau, svi_b=0.1 * np.sqrt(tau), svi_rho=-0.3, svi_m=0.01, svi_sigma=0.1)


def _history(ccy="BTC", t0=T0, days=1, spot=SPOT, stale=True, fwd_conf=1.0):
    """Synthetic feed history: pushes 60 s before 08:00 UTC of each of ``days`` consecutive days.

    Besides the live expiries it holds an expired expiry, an expiry with a forward but no SVI curve and (``stale``)
    an expiry whose last push is two days old.
    """
    spot_rows, fwd_rows, rate_rows, svi_rows = [], [], [], []
    live = [t0 + d * DAY for d in LIVE_DAYS]
    for i in range(days):
        ts = t0 + i * DAY
        b = block_at_ts(ts - 60)
        bts = ts_at_block(b)
        s = spot * (1 + 0.01 * i)
        spot_rows.append((b, bts, 0, 0, s, 1.0, bts - 1))
        for j, e in enumerate(live + [t0 + 50 * DAY]):  # the last one has a forward but never an SVI curve
            if e <= bts:
                continue  # expired before this push
            tau = (e - bts) / YEAR
            diff = s * (np.exp(0.05 * tau) - 1.0)
            fwd_rows.append((b, bts, 1 + j, e, diff, fwd_conf, bts - 2, 0.0))
            rate_rows.append((b, bts, 20 + j, e, 0.04, 1.0, bts - 3))
            if e != t0 + 50 * DAY:
                row = dict(block=b, block_ts=bts, log_index=40 + j, expiry=e, feed_ts=bts - 4,
                           svi_fwd=(s + diff) * 1.0005, svi_ref_tau=tau, confidence=0.95)
                row.update(_svi_params(tau))
                svi_rows.append(row)
    # an expiry that expired an hour before t0 and one whose feeds stopped two days before t0
    old = block_at_ts(t0 - 2 * DAY)
    for e, lg in ((t0 - 3600, 90), (t0 + 60 * DAY, 91)):
        if e == t0 + 60 * DAY and not stale:
            continue
        bts = ts_at_block(old)
        tau = (e - bts) / YEAR
        fwd_rows.append((old, bts, lg, e, 10.0, 1.0, bts - 2, 0.0))
        row = dict(block=old, block_ts=bts, log_index=lg, expiry=e, feed_ts=bts - 4, svi_fwd=spot,
                   svi_ref_tau=max(tau, 1e-4), confidence=0.95)
        row.update(_svi_params(max(tau, 1e-4)))
        svi_rows.append(row)
    cols = ["block", "block_ts", "log_index", "expiry", "value", "confidence", "feed_ts"]
    b_dep = block_at_ts(t0 - 400 * DAY)
    frames = {
        "spot": pd.DataFrame(spot_rows, columns=cols),
        "forward": pd.DataFrame(fwd_rows, columns=cols + ["fixed"]),
        "rate_pm2": pd.DataFrame(rate_rows, columns=cols),
        "rate_pm": pd.DataFrame([(b_dep, ts_at_block(b_dep), 0, 0, 0.0, 1.0, ts_at_block(b_dep))], columns=cols),
        "perp": pd.DataFrame([(b, bts, 99, 0, 0.0, 1.0, bts - 1)], columns=cols),
        "svi": pd.DataFrame(svi_rows),
    }
    return FeedHistory(ccy, frames=frames)


@pytest.fixture(scope="module")
def hist():
    return _history()


# ------------------------------------------------------------------------------------------------ manager windows

def test_manager_windows_follow_the_preregistration():
    ts = lambda s: int(pd.Timestamp(s, tz="UTC").timestamp())  # noqa: E731
    assert not p2surface.manager_available("BTC", "pm2", ts("2025-06-12 22:59:59"))
    assert p2surface.manager_available("BTC", "pm2", ts("2025-06-12 23:00"))
    assert p2surface.manager_available("ETH", "pm2", ts("2025-06-12 23:00"))
    assert not p2surface.manager_available("HYPE", "pm2", ts("2025-11-10 23:59:59"))
    assert p2surface.manager_available("HYPE", "pm2", ts("2025-11-11 00:00"))
    assert not p2surface.manager_available("HYPE", "sm", ts("2025-11-10 08:00"))
    assert p2surface.manager_available("HYPE", "sm", ts("2025-11-11 08:00"))
    assert not p2surface.manager_available("HYPE", "pm", ts("2026-09-17 08:00"))
    assert p2surface.manager_available("BTC", "pm", ts("2024-01-11 08:00"))
    assert p2surface.manager_available("ETH", "sm", ts("2024-01-11 08:00"))


# ------------------------------------------------------------------------------------------------ chain surface

def test_live_expiries_skip_expired_stale_and_curve_less_expiries(hist):
    got = p2surface.live_expiries(hist, T0)
    assert got == [T0 + d * DAY for d in LIVE_DAYS]


def test_chain_surface_returns_the_vol_feed_value_at_every_strike(hist):
    surf = p2surface.chain_surface("BTC", T0, hist=hist)
    state = hist.state_at(T0, [T0 + d * DAY for d in LIVE_DAYS])
    assert [s.expiry for s in surf.smiles] == [T0 + d * DAY for d in LIVE_DAYS]
    assert surf.spot == pytest.approx(SPOT)
    for sm in surf.smiles:
        es = state.expiries[sm.expiry]
        assert sm.F == es.forward
        assert sm.T == pytest.approx((sm.expiry - T0) / YEAR, rel=1e-15)
        K = sm.F * np.exp(np.linspace(-0.8, 0.8, 41))
        a, b, rho, m, sig, ref_tau = es.svi
        want = svi_vol(K, a, b, rho, m, sig, es.svi_fwd, ref_tau)
        np.testing.assert_allclose(sm(np.log(K / sm.F)), want, rtol=1e-12)
        np.testing.assert_allclose(sm.total_variance(np.log(K / sm.F)), want ** 2 * sm.T, rtol=1e-12)


def test_chain_smile_slope_matches_finite_differences(hist):
    surf = p2surface.chain_surface("BTC", T0, hist=hist)
    for sm in surf.smiles:
        k = np.linspace(-0.4, 0.4, 17)
        h = 1e-6
        fd = (sm.total_variance(k + h) - sm.total_variance(k - h)) / (2 * h)
        np.testing.assert_allclose(sm.dw_dk(k), fd, rtol=1e-5, atol=1e-12)


def test_chain_surface_needs_at_least_one_curve(hist):
    with pytest.raises(ValueError):
        p2surface.chain_surface("BTC", T0 + 500 * DAY, hist=hist)


# ------------------------------------------------------------------------------------------------ capital grid

def _sm_params(ts):
    return Timeline("BTC", "sm").at(ts)


def test_capital_grid_has_one_row_per_node_and_the_plan_columns(hist):
    g = p2surface.capital_grid("BTC", T0, "sm", "short", hist=hist)
    for col in ("delta", "tenor_days", "tau", "forward", "strike", "iv", "is_call", "price", "K", "K_per_forward_bp",
                "net", "mtm"):
        assert col in g.columns, col
    assert len(g) == len(np.unique(g["delta"])) * len(np.unique(g["tau"]))
    assert g["K"].notna().all()
    np.testing.assert_allclose(g["K_per_forward_bp"], 1e4 * g["K"] / g["forward"], rtol=1e-14)
    surf = p2surface.chain_surface("BTC", T0, hist=hist)
    assert g["tau"].min() >= surf.tenors.min() - 1e-15 and g["tau"].max() <= surf.tenors.max() + 1e-15


def test_capital_grid_sm_short_equals_a_times_spot(hist):
    """SM short at the mark: K = min(a S, max-loss branch) with a = max(maxSpotReq - otm, minSpotReq)."""
    g = p2surface.capital_grid("BTC", T0, "sm", "short", hist=hist)
    om = _sm_params(T0)["OptionMarginParams"]
    S = SPOT
    K, F, call = g["strike"].to_numpy(), g["forward"].to_numpy(), g["is_call"].to_numpy()
    otm = np.where(call, np.maximum(K - S, 0.0), np.maximum(S - K, 0.0)) / S
    a = np.where((om["maxSpotReq"] > otm) & (om["maxSpotReq"] - otm > om["minSpotReq"]), om["maxSpotReq"] - otm,
                 om["minSpotReq"])
    c = pricing.price(F, K, g["tau"].to_numpy(), g["iv"].to_numpy(), np.where(call, 1, -1), 1.0)
    np.testing.assert_allclose(g["price"], c, rtol=1e-9, atol=1e-9)
    branch = np.where(call, om["unpairedIMScale"] * F - c, K - c)
    np.testing.assert_allclose(g["K"], np.minimum(a * S, branch), rtol=1e-12)
    assert np.mean(a * S <= branch) > 0.9  # the isolated a*S branch binds almost everywhere


def test_capital_grid_sm_long_is_the_premium(hist):
    g = p2surface.capital_grid("BTC", T0, "sm", "long", hist=hist)
    np.testing.assert_allclose(g["K"], g["price"], rtol=1e-12)
    assert (g["net"] == 0).all()


@pytest.mark.parametrize("mgr, engine", [("pm2", margin_pm2), ("pm", margin_pm), ("sm", margin_sm)])
@pytest.mark.parametrize("side, q", [("short", -1.0), ("long", 1.0)])
def test_capital_grid_equals_the_book_engine_on_listed_expiries(hist, mgr, engine, side, q):
    surf = p2surface.chain_surface("BTC", T0, hist=hist)
    g = p2surface.capital_grid("BTC", T0, mgr, side, hist=hist, tenors=surf.tenors)
    params = Timeline("BTC", mgr).at(T0)
    rng = np.random.default_rng(20260924)
    for i in rng.choice(len(g), 25, replace=False):
        r = g.iloc[i]
        e = int(round(T0 + r["tau"] * YEAR))
        state = hist.state_at(T0, [e])
        book = Book(options=[OptionLeg(e, float(r["strike"]), bool(r["is_call"]), q)])
        net, mtm = engine.net_margin(book, state, params, vols={(e, float(r["strike"])): float(r["iv"])})
        assert r["K"] == pytest.approx(r["price"] * q - net, rel=1e-9, abs=1e-8)
        assert r["mtm"] == pytest.approx(mtm, rel=1e-9, abs=1e-8)


def test_capital_grid_delta_is_self_consistent(hist):
    surf = p2surface.chain_surface("BTC", T0, hist=hist)
    g = p2surface.capital_grid("BTC", T0, "pm2", "short", hist=hist, tenors=surf.tenors)
    d = pricing.delta_of(g["forward"], g["strike"], g["tau"], g["iv"], 1)
    np.testing.assert_allclose(d, g["delta"], atol=1e-10)
    assert (g["is_call"] == (g["strike"] >= g["forward"])).all()
    state = hist.state_at(T0, [s.expiry for s in surf.smiles])
    for sm in surf.smiles:  # on a listed expiry the node vol is the feed vol at the node strike
        rows = g[np.isclose(g["tau"], sm.T, rtol=0, atol=1e-15)]
        es = state.expiries[sm.expiry]
        a, b, rho, m, sig, ref_tau = es.svi
        np.testing.assert_allclose(rows["iv"], svi_vol(rows["strike"], a, b, rho, m, sig, es.svi_fwd, ref_tau),
                                   rtol=1e-8)


def test_capital_grid_drops_tenors_outside_the_listed_range(hist):
    g = p2surface.capital_grid("BTC", T0, "pm2", "short", hist=hist, tenors=np.array([0.1, 7, 30, 900]) / 365)
    assert sorted(np.unique(np.round(g["tenor_days"], 9))) == [7.0, 30.0]


def test_capital_grid_rejects_managers_outside_their_window(hist):
    with pytest.raises(ValueError):
        p2surface.capital_grid("HYPE", T0, "pm", "short", hist=_history("HYPE"))
    early = int(pd.Timestamp("2025-06-12 08:00", tz="UTC").timestamp())
    with pytest.raises(ValueError):
        p2surface.capital_grid("BTC", early, "pm2", "short", hist=_history(t0=early))
    with pytest.raises(ValueError):
        p2surface.capital_grid("BTC", T0, "pm2", "sideways", hist=hist)


# ------------------------------------------------------------------------------------------------ reference book

def _straddle_capital(engine, state, e, K, params, p_call, p_put, **kw):
    book = Book(options=[OptionLeg(e, K, True, -1.0), OptionLeg(e, K, False, -1.0)])
    net, _ = engine.net_margin(book, state, params, **kw)
    return -(p_call + p_put) - net


def test_reference_book_is_the_atm_straddle_nearest_to_30_days(hist):
    rb = p2surface.reference_book_series("BTC", days=["2026-03-10"], hist=hist)
    assert len(rb) == 1
    r = rb.iloc[0]
    e = T0 + 28 * DAY
    assert r["ts"] == T0 and r["day"] == "2026-03-10" and r["expiry"] == e
    assert r["tenor_days"] == pytest.approx(28.0)
    state = hist.state_at(T0, [e])
    es = state.expiries[e]
    assert r["strike"] == es.forward == r["forward"]
    assert r["sigma"] == pytest.approx(es.vol(es.forward), rel=1e-14)
    c = pricing.price(es.forward, es.forward, 28 / 365, es.vol(es.forward), 1, 1.0)
    assert r["price_call"] == pytest.approx(c, rel=1e-9)
    assert r["price_put"] == pytest.approx(c, rel=1e-9)  # D = 1 at K = F
    for mgr, engine in (("sm", margin_sm), ("pm", margin_pm), ("pm2", margin_pm2)):
        params = Timeline("BTC", mgr).at(T0)
        want = _straddle_capital(engine, state, e, es.forward, params, r["price_call"], r["price_put"])
        assert r[f"K_{mgr}"] == pytest.approx(want, rel=1e-12), mgr
        assert r[f"K_{mgr}"] > 0


def test_reference_book_prev_day_uses_yesterdays_parameters(hist):
    base = Timeline("BTC", "sm").at(T0)
    changed = {k: dict(v) for k, v in base.items()}
    changed["OptionMarginParams"]["maxSpotReq"] = 0.25
    changed["OptionMarginParams"]["minSpotReq"] = 0.2
    tl = Timeline("BTC", "sm", entries=[
        {"from_block": 1, "from_ts": T0 - 30 * DAY, "source": "test", "params": base},
        {"from_block": 2, "from_ts": T0 - 3600, "source": "test", "params": changed},
    ])
    h2 = _history(t0=T0 - DAY, days=2)
    rb = p2surface.reference_book_series("BTC", days=["2026-03-09", "2026-03-10"], hist=h2, timelines={"sm": tl})
    first, second = rb.iloc[0], rb.iloc[1]
    assert first["K_sm"] == pytest.approx(first["K_sm_prev"], rel=1e-15)  # no change in the 24 h before
    assert second["K_sm"] > second["K_sm_prev"] * 1.3  # the stricter parameters of today
    assert second["sm_param_ts"] == T0 - 3600 and second["sm_param_ts_prev"] == T0 - 30 * DAY
    state = h2.state_at(T0, [int(second["expiry"])])
    want = _straddle_capital(margin_sm, state, int(second["expiry"]), second["strike"], base, second["price_call"],
                             second["price_put"])
    assert second["K_sm_prev"] == pytest.approx(want, rel=1e-12)


def test_reference_book_is_nan_outside_the_manager_windows():
    rb = p2surface.reference_book_series("HYPE", days=["2026-03-10"], hist=_history("HYPE"))
    assert rb["K_pm"].isna().all() and rb["K_pm_prev"].isna().all()
    assert rb["K_sm"].notna().all() and rb["K_pm2"].notna().all()
    early = int(pd.Timestamp("2025-06-12 08:00", tz="UTC").timestamp())
    rb = p2surface.reference_book_series("BTC", days=["2025-06-12"], hist=_history(t0=early))
    assert rb["K_pm2"].isna().all() and rb["K_sm"].notna().all() and rb["K_pm"].notna().all()


def test_reference_book_skips_days_without_a_live_expiry(hist):
    rb = p2surface.reference_book_series("BTC", days=["2026-03-10", "2027-06-01"], hist=hist)
    assert list(rb["day"]) == ["2026-03-10"]


def test_reference_days_start_per_currency():
    d = p2surface.reference_days("HYPE")
    assert d[0] == "2025-11-11" and d[-1] == "2026-09-17"
    d = p2surface.reference_days("ETH")
    assert d[0] == "2024-01-11" and len(d) == (pd.Timestamp("2026-09-17") - pd.Timestamp("2024-01-11")).days + 1


def test_combine_parts_sorts_by_currency_and_day(tmp_path):
    cols = ["ccy", "day", "K_sm"]
    pd.DataFrame([["ETH", "2024-01-12", 2.0], ["ETH", "2024-01-11", 1.0]], columns=cols).to_csv(
        tmp_path / "ETH_2024Q1.csv", index=False)
    pd.DataFrame([["BTC", "2024-01-11", 3.0]], columns=cols).to_csv(tmp_path / "BTC_2024Q1.csv", index=False)
    out = p2surface.combine_parts(tmp_path, tmp_path / "reference_book.csv")
    got = pd.read_csv(out)
    assert list(zip(got["ccy"], got["day"])) == [("BTC", "2024-01-11"), ("ETH", "2024-01-11"), ("ETH", "2024-01-12")]


# ------------------------------------------------------------------------------------------------ frames, animation

def test_palette_follows_figstyle_and_the_colour_ramp_is_greyscale_safe():
    from derive_surface import figstyle

    assert set(p2surface.MANAGER_COLORS.values()) <= set(figstyle.PALETTE)
    assert len(set(p2surface.MANAGER_COLORS.values())) == 3
    cmap = p2surface.colormap()
    rgb = cmap(np.linspace(0, 1, 64))[:, :3]
    lum = 0.2126 * rgb[:, 0] + 0.7152 * rgb[:, 1] + 0.0722 * rgb[:, 2]
    assert np.all(np.diff(lum) > 0)  # monotone luminance: readable in greyscale


def test_render_frame_returns_an_rgb_image(hist):
    grids = {m: p2surface.capital_grid("BTC", T0, m, "short", hist=hist) for m in ("pm2", "sm")}
    series = pd.DataFrame({"ts": T0 + DAY * np.arange(-5, 3), "pm2": np.linspace(300, 350, 8),
                           "sm": np.linspace(900, 950, 8)})
    rgb = p2surface.render_frame(grids, ccy="BTC", ts=T0, side="short", series=series, events=[T0 - 2 * DAY],
                                 width=640, height=360)
    assert rgb.shape == (360, 640, 3) and rgb.dtype == np.uint8
    assert rgb.std() > 5  # not a blank canvas


def test_series_strip_ignores_events_outside_its_time_range():
    import matplotlib.pyplot as plt

    series = pd.DataFrame({"ts": T0 + DAY * np.arange(0, 10), "pm2": np.linspace(300, 350, 10)})
    fig, ax = plt.subplots()
    p2surface._draw_series(ax, series, T0 + 3 * DAY, [T0 - 400 * DAY, T0 + 5 * DAY, T0 + 900 * DAY], "bp", 8.0)
    lo, hi = ax.get_xlim()
    plt.close(fig)
    t = pd.to_datetime(series["ts"], unit="s")
    import matplotlib.dates as mdates

    assert mdates.num2date(lo).timestamp() >= t.min().timestamp() - 1
    assert mdates.num2date(hi).timestamp() <= t.max().timestamp() + 1


def test_render_frame_draws_panels_outside_the_window_as_empty():
    rgb = p2surface.render_frame({"pm2": None}, ccy="HYPE", ts=T0, width=320, height=200)
    assert rgb.shape == (200, 320, 3)


def test_render_frame_writes_a_png(tmp_path, hist):
    g = {"sm": p2surface.capital_grid("BTC", T0, "sm", "short", hist=hist)}
    path = p2surface.save_frame(g, tmp_path / "x.png", ccy="BTC", ts=T0, side="short", width=480, height=320)
    from PIL import Image

    with Image.open(path) as im:
        assert im.size[0] >= 480 and im.size[1] >= 320


def test_animate_writes_a_gif_with_one_frame_per_day(tmp_path):
    h = _history(days=3)
    days = ["2026-03-10", "2026-03-11", "2026-03-12"]
    path = p2surface.animate("BTC", days, tmp_path, hist=h, managers=("pm2", "sm"), width=480, height=270,
                             hold_last=0)
    from PIL import Image

    assert path.suffix == ".gif" and path.exists()
    with Image.open(path) as im:
        assert im.n_frames == 3
