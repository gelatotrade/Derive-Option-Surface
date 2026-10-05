"""Tests for derive_surface.p2events: parameter events, capital doses and the H4 panel (preregistration H4).

All tests are offline. Synthetic timelines are written to a temporary directory; the capital tests use the tracked
PM2 and legacy-PM parameter files under results/p2/params (skipped if missing).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from derive_surface import margin_pm, margin_pm2, p2events
from derive_surface.p2chain import block_at_ts, ts_at_block
from derive_surface.p2types import YEAR

PARAMS = Path(__file__).resolve().parents[1] / "results" / "p2" / "params"
DAY = 86_400


def _utc(s: str) -> int:
    return int(pd.Timestamp(s, tz="UTC").timestamp())


# ------------------------------------------------------------------------------------------------ event list

def _entry(ts: int, params: dict, changed=None) -> dict:
    return {"from_block": block_at_ts(ts), "from_ts": ts, "source": "test", "params": params,
            **({"changed": changed} if changed is not None else {})}


def _pm2_params(im=1.3, vol_up=0.5, coll=0.1, max_exp=12, basis=1.0) -> dict:
    return {"VolShockParameters": {"volRangeUp": vol_up}, "MarginParameters": {"imFactor": im},
            "BasisContingencyParameters": {"basisContAddFactor": basis}, "OtherContingencyParameters": {"x": 1.0},
            "SkewShockParameters": {"y": 1.0}, "CollateralParameters": {"0xabc": {"IMHaircut": coll}},
            "scenarios": [{"spotShock": 1.1, "volShock": 0, "dampeningFactor": 1.0}], "maxExpiries": max_exp}


def _pm_params(basis=1.0, max_exp=11) -> dict:
    return {"VolShockParameters": {"volRangeUp": 0.6}, "MarginParameters": {"imFactor": 1.3},
            "BasisContingencyParameters": {"basisContAddFactor": basis}, "OtherContingencyParameters": {"x": 1.0},
            "scenarios": [{"spotShock": 1.2, "volShock": 0}], "maxExpiries": max_exp}


@pytest.fixture()
def timeline_root(tmp_path: Path) -> Path:
    """BTC timelines: PM2 with changes before the window, collateral/maxExpiries-only changes, two capital changes on
    one UTC day and one on the next day; legacy PM with a pre-sample change, a maxExpiries change and one real change."""
    pm2 = [
        _entry(_utc("2025-06-09 05:18:03"), _pm2_params()),
        _entry(_utc("2025-06-12 22:20:01"), _pm2_params(im=1.25)),               # 40 min before the PM2 window
        _entry(_utc("2025-08-22 02:30:13"), _pm2_params(im=1.25, coll=0.2)),    # collateral only
        _entry(_utc("2025-09-17 21:41:49"), _pm2_params(im=1.25, coll=0.2, max_exp=18)),  # maxExpiries only
        _entry(_utc("2026-05-24 04:05:07"), _pm2_params(im=1.25, coll=0.2, max_exp=18, vol_up=0.6)),
        _entry(_utc("2026-05-24 05:21:47"), _pm2_params(im=1.25, coll=0.2, max_exp=18, vol_up=0.6, basis=2.0)),
        _entry(_utc("2026-05-25 00:00:05"), _pm2_params(im=1.4, coll=0.3, max_exp=18, vol_up=0.6, basis=2.0)),
    ]
    pm = [
        _entry(_utc("2023-12-04 16:36:09"), _pm_params()),
        _entry(_utc("2023-12-11 07:27:35"), _pm_params(basis=1.1)),               # before the sample
        _entry(_utc("2024-06-12 00:01:27"), _pm_params(basis=0.5)),
        _entry(_utc("2024-09-25 04:47:15"), _pm_params(basis=0.5, max_exp=18)),  # maxExpiries only
    ]
    (tmp_path / "BTC_pm2.json").write_text(json.dumps(pm2))
    (tmp_path / "BTC_pm.json").write_text(json.dumps(pm))
    (tmp_path / "HYPE_pm2.json").write_text(json.dumps([_entry(_utc("2025-10-16 10:29:33"), _pm2_params()),
                                                         _entry(_utc("2025-10-17 04:27:21"), _pm2_params(im=2.0)),
                                                         _entry(_utc("2026-01-08 22:50:49"), _pm2_params(im=1.5))]))
    return tmp_path


def test_parameter_changes_drop_collateral_maxexpiries_and_out_of_window(timeline_root):
    ch = p2events.parameter_changes("BTC", "pm2", root=timeline_root)
    assert list(ch["ts"]) == [_utc("2026-05-24 04:05:07"), _utc("2026-05-24 05:21:47"), _utc("2026-05-25 00:00:05")]
    assert list(ch["kinds"]) == ["VolShockParameters", "BasisContingencyParameters", "MarginParameters"]
    legacy = p2events.parameter_changes("BTC", "pm", root=timeline_root)
    assert list(legacy["ts"]) == [_utc("2024-06-12 00:01:27")]
    hype = p2events.parameter_changes("HYPE", "pm2", root=timeline_root)
    assert list(hype["ts"]) == [_utc("2026-01-08 22:50:49")]  # the October change lies before 11.11.2025


def test_same_utc_day_is_merged_per_currency(timeline_root):
    ev = p2events.event_list(("BTC",), root=timeline_root)
    assert list(ev["event_id"]) == ["BTC-pm-20240612", "BTC-pm2-20260524", "BTC-pm2-20260525"]
    may = ev.set_index("event_id").loc["BTC-pm2-20260524"]
    assert may["event_ts"] == _utc("2026-05-24 04:05:07")
    assert may["last_ts"] == _utc("2026-05-24 05:21:47")
    assert may["n_changes"] == 2
    assert may["kinds"] == "BasisContingencyParameters+VolShockParameters"
    assert may["event_day"] == "2026-05-24"


def test_merge_rejects_two_managers_on_one_day():
    ch = pd.DataFrame({"ccy": ["BTC", "BTC"], "manager": ["pm", "pm2"],
                       "ts": [_utc("2025-01-01 01:00"), _utc("2025-01-01 02:00")], "kinds": ["a", "b"]})
    with pytest.raises(ValueError):
        p2events.merge_same_day(ch)


def test_merge_keeps_currencies_apart():
    ch = pd.DataFrame({"ccy": ["BTC", "ETH"], "manager": ["pm2", "pm2"],
                       "ts": [_utc("2025-01-01 01:00"), _utc("2025-01-01 02:00")], "kinds": ["a", "a"]})
    ev = p2events.merge_same_day(ch)
    assert list(ev["event_id"]) == ["BTC-pm2-20250101", "ETH-pm2-20250101"]


def test_event_params_are_immediately_before_first_and_after_last_change(timeline_root):
    ev = p2events.event_list(("BTC",), root=timeline_root).set_index("event_id")
    before, after = p2events.event_params(ev.loc["BTC-pm2-20260524"], root=timeline_root)
    assert before["VolShockParameters"]["volRangeUp"] == 0.5
    assert before["BasisContingencyParameters"]["basisContAddFactor"] == 1.0
    assert after["VolShockParameters"]["volRangeUp"] == 0.6
    assert after["BasisContingencyParameters"]["basisContAddFactor"] == 2.0
    assert after["MarginParameters"]["imFactor"] == 1.25  # the next day's change is a separate event


def test_real_timelines_give_the_preregistered_events():
    if not (PARAMS / "BTC_pm2.json").exists():
        pytest.skip("results/p2/params missing")
    ev = p2events.event_list()
    days = {(r.ccy, r.manager): [] for r in ev.itertuples()}
    for r in ev.itertuples():
        days[(r.ccy, r.manager)].append(r.event_day)
    assert days[("BTC", "pm")] == ["2024-06-12", "2025-02-22"]
    assert days[("ETH", "pm")] == ["2024-06-12", "2025-02-22"]
    assert days[("BTC", "pm2")] == ["2025-10-10", "2026-01-08", "2026-01-23", "2026-05-24", "2026-08-20"]
    assert days[("ETH", "pm2")] == ["2025-10-10", "2026-01-08", "2026-01-23", "2026-05-24", "2026-08-20"]
    assert days[("HYPE", "pm2")] == ["2026-01-08", "2026-05-08", "2026-05-24", "2026-08-20"]
    assert ("HYPE", "pm") not in days


# ------------------------------------------------------------------------------------------------ doses

def test_cell_labels():
    lab = p2events.cell_labels(pd.Series(["BTC", "ETH"]), pd.Series([1, -1]), pd.Series(["00-10", "40-60"]),
                               pd.Series(["<=2d", "7-30d"]))
    assert list(lab) == ["BTC|buy|00-10|<=2d", "ETH|sell|40-60|7-30d"]


def test_dose_is_mean_log_ratio_over_valid_fills():
    cells = np.array(["a", "a", "a", "b", "b"])
    k_before = np.array([100.0, 50.0, -5.0, 10.0, np.nan])
    k_after = np.array([110.0, 40.0, 7.0, 10.0, 12.0])
    d = p2events.cell_doses(cells, k_before, k_after).set_index("cell")
    assert d.loc["a", "dose"] == pytest.approx((math.log(1.1) + math.log(0.8)) / 2, rel=1e-12)
    assert d.loc["a", "n_fills"] == 3 and d.loc["a", "n_valid"] == 2 and d.loc["a", "n_nonpos"] == 1
    assert d.loc["b", "dose"] == 0.0
    assert d.loc["b", "n_valid"] == 1 and d.loc["b", "n_nan"] == 1


def test_dose_window_is_half_open_before_the_event():
    e = _utc("2025-10-10 22:55:31")
    ts = np.array([(e - 14 * DAY) * 1000 - 1, (e - 14 * DAY) * 1000, e * 1000 - 1, e * 1000])
    assert list(p2events.dose_window(ts, e)) == [False, True, True, False]


def _pm2(ccy="BTC"):
    path = PARAMS / f"{ccy}_pm2.json"
    if not path.exists():
        pytest.skip("results/p2/params missing")
    return json.loads(path.read_text())


def _fills_and_state(n=6, t0=_utc("2026-05-20 10:00:00")):
    rng = np.random.default_rng(1)
    ts = (t0 + np.arange(n) * 3_601) * 1000 + 123
    expiry = np.full(n, _utc("2026-06-26 08:00:00"))
    strike = np.array([90_000.0, 100_000.0, 110_000.0, 95_000.0, 105_000.0, 100_000.0])[:n]
    fills = pd.DataFrame({"fill_key": [f"f{i}" for i in range(n)], "ts": ts, "ccy": "BTC", "expiry": expiry,
                          "strike": strike, "is_call": np.array([True, False, True, False, True, True])[:n],
                          "maker_side": np.array([1, -1, -1, 1, -1, 1])[:n],
                          "price": np.array([9_000.0, 3_500.0, 1_200.0, 1_800.0, 2_300.0, 4_000.0])[:n],
                          "cell": ["c1", "c1", "c2", "c2", "c2", "c1"][:n]})
    state = pd.DataFrame({"spot": 100_000.0 + rng.normal(0, 100, n), "forward": 100_500.0, "sigma": 0.5,
                          "rate": 0.04, "rate_pm": 0.0, "vol_conf": 1.0, "fwd_conf": 1.0, "spot_conf": 1.0,
                          "rate_conf": 1.0, "fwd_fixed": 0.0})
    return fills, state


def test_single_capital_pm2_is_premium_minus_net_at_block_time():
    params = _pm2()[-1]["params"]
    fills, state = _fills_and_state()
    k = p2events.single_capital(fills, state, params, "pm2")
    ts_s = fills["ts"].to_numpy() // 1000
    tau = (fills["expiry"].to_numpy() - np.array([ts_at_block(block_at_ts(t)) for t in ts_s])) / YEAR
    arrays = {"spot": state["spot"].to_numpy(), "forward": state["forward"].to_numpy(),
              "sigma": state["sigma"].to_numpy(), "tau": tau, "rate": state["rate"].to_numpy(),
              "strike": fills["strike"].to_numpy(), "is_call": fills["is_call"].to_numpy(),
              "amount": fills["maker_side"].to_numpy(float), "vol_conf": 1.0, "fwd_conf": 1.0, "spot_conf": 1.0,
              "rate_conf": 1.0, "fwd_fixed": 0.0}
    net, _ = margin_pm2.single(arrays, params)
    expected = fills["price"].to_numpy() * fills["maker_side"].to_numpy() - net
    np.testing.assert_allclose(k, expected, rtol=1e-12)
    assert np.all(k[fills["maker_side"].to_numpy() < 0] > 0)  # a short ties up more than it receives


def test_single_capital_pm_uses_the_legacy_rate_not_the_pm2_rate():
    path = PARAMS / "BTC_pm.json"
    if not path.exists():
        pytest.skip("results/p2/params missing")
    params = json.loads(path.read_text())[-1]["params"]
    fills, state = _fills_and_state()
    k0 = p2events.single_capital(fills, state, params, "pm")
    k1 = p2events.single_capital(fills, state.assign(rate=0.9, rate_conf=0.1), params, "pm")
    np.testing.assert_array_equal(k0, k1)
    k2 = p2events.single_capital(fills, state.assign(rate_pm=0.05), params, "pm")
    assert not np.allclose(k0, k2)


def test_single_capital_is_nan_without_market_state():
    params = _pm2()[-1]["params"]
    fills, state = _fills_and_state()
    state.loc[2, "sigma"] = np.nan
    state.loc[4, "forward"] = np.nan
    k = p2events.single_capital(fills, state, params, "pm2")
    assert np.isnan(k[2]) and np.isnan(k[4])
    assert np.isfinite(np.delete(k, [2, 4])).all()


class _FakeHistory:
    def __init__(self, state: pd.DataFrame):
        self.state = state
        self.calls = []

    def bulk(self, ts, expiry, strike):
        self.calls.append(np.asarray(ts).copy())
        return self.state.iloc[: len(ts)].reset_index(drop=True)


def test_event_doses_use_before_and_after_params_on_the_same_fill():
    tl = _pm2()
    before = tl[-1]["params"]
    after = json.loads(json.dumps(before))
    after["MarginParameters"]["imFactor"] = before["MarginParameters"]["imFactor"] * 1.2
    e = _utc("2026-05-24 04:05:07")
    fills, state = _fills_and_state(t0=e - 2 * DAY)
    # one fill after the event and one more than 14 days before it must be ignored
    extra = fills.iloc[:2].copy()
    extra["ts"] = [e * 1000 + 5, (e - 15 * DAY) * 1000]
    extra["fill_key"] = ["late", "early"]
    frame = pd.concat([fills, extra], ignore_index=True)
    hist = _FakeHistory(state)
    per_fill, doses = p2events.event_doses(frame, e, before, after, "pm2", hist)
    assert list(per_fill["fill_key"]) == list(fills["fill_key"])
    np.testing.assert_array_equal(hist.calls[0], fills["ts"].to_numpy() // 1000)
    kb = p2events.single_capital(fills, state, before, "pm2")
    ka = p2events.single_capital(fills, state, after, "pm2")
    np.testing.assert_allclose(per_fill["K_before"], kb)
    np.testing.assert_allclose(per_fill["K_after"], ka)
    d = doses.set_index("cell")["dose"]
    for c in ("c1", "c2"):
        m = (fills["cell"] == c).to_numpy()
        assert d[c] == pytest.approx(float(np.mean(np.log(ka[m] / kb[m]))), rel=1e-12)
    # a collateral-only change leaves every single-contract capital unchanged
    coll = json.loads(json.dumps(before))
    for v in coll["CollateralParameters"].values():
        v["IMHaircut"] = 0.5
    _, zero = p2events.event_doses(frame, e, before, coll, "pm2", _FakeHistory(state))
    assert (zero["dose"] == 0.0).all()


def test_event_doses_without_fills_is_empty():
    per_fill, doses = p2events.event_doses(pd.DataFrame(columns=["fill_key", "ts", "ccy", "expiry", "strike",
                                                                 "is_call", "maker_side", "price", "cell"]),
                                           _utc("2026-05-24 04:05:07"), {}, {}, "pm2", _FakeHistory(pd.DataFrame()))
    assert len(per_fill) == 0 and len(doses) == 0
    assert list(doses.columns) == p2events.DOSE_COLUMNS


def test_events_below_one_percent_are_dropped():
    events = pd.DataFrame({"event_id": ["a", "b", "c", "d"], "ccy": "BTC", "manager": "pm2",
                           "event_ts": [1, 2, 3, 4], "kinds": "x"})
    doses = pd.DataFrame({"event_id": ["a", "a", "b", "b", "c"], "cell": ["x", "y", "x", "y", "x"],
                          "dose": [0.004, -0.0099, 0.002, -0.012, np.nan], "n_fills": 5, "n_valid": 5,
                          "n_nonpos": 0, "n_nan": 0})
    out = p2events.flag_events(events, doses).set_index("event_id")
    assert out.loc["a", "max_abs_dose"] == pytest.approx(0.0099)
    assert not out.loc["a", "kept"]
    assert out.loc["b", "kept"] and out.loc["b", "max_abs_dose"] == pytest.approx(0.012)
    assert not out.loc["c", "kept"] and np.isnan(out.loc["c", "max_abs_dose"])
    assert not out.loc["d", "kept"]  # no fills before the event


# ------------------------------------------------------------------------------------------------ outcome and panel

def test_outcome_is_half_spread_in_bp_of_index():
    mk = pd.DataFrame({"trade_id": ["t1", "t2"], "ts": [_utc("2026-01-01 10:00") * 1000] * 2,
                       "currency": ["BTC", "ETH"], "instrument_name": ["BTC-X", "ETH-X"],
                       "expiry": [_utc("2026-01-30 08:00")] * 2, "strike": [100_000.0, 3_000.0],
                       "option_type": ["C", "P"], "price": [1_000.0, 50.0], "index_price": [95_000.0, 3_100.0],
                       "maker_side": [-1, 1], "delta_bucket": ["25-40", "10-25"], "tenor_bucket": ["7-30d", "7-30d"],
                       "mark_b_t": [980.0, 52.0], "delta_t": [0.3, -0.2], "fwd_t": [95_100.0, 3_101.0],
                       "fee_maker": [0.1, 0.1], "rebate_maker": [0.0, 0.0], "taker_wallet": ["w1", "w2"],
                       "mo_usd_30m": [1.0, 2.0], "mo_dn_30m": [0.0, 0.0], "mo_vol_30m": [0.0, 0.0],
                       "amount": [1.0, 1.0]})  # Paper 1's revised analysis frame reads the amount of each fill
    funding = pd.DataFrame({"instrument_name": ["BTC-PERP", "ETH-PERP"], "timestamp": [0, 0],
                            "funding_rate": [1e-5, 2e-5]})
    f = p2events.outcome_frame(mk, funding)
    assert list(f["fill_key"]) == ["t1", "t2"]
    assert f["y_hs_bp"].tolist() == pytest.approx([1e4 * 20.0 / 95_000.0, 1e4 * 2.0 / 3_100.0])
    assert list(f["cell"]) == ["BTC|sell|25-40|7-30d", "ETH|buy|10-25|7-30d"]
    assert list(f["day"]) == ["2026-01-01", "2026-01-01"]
    assert list(f["is_call"]) == [True, False]


def _panel_frame(e: int) -> pd.DataFrame:
    rows = []

    def add(cell, ts, y=1.0, ccy="BTC"):
        rows.append({"fill_key": f"k{len(rows)}", "ts": int(ts), "ccy": ccy, "cell": cell, "y_hs_bp": y})

    day0 = (e // DAY) * DAY
    for i in range(25):  # cell A: 25 before, 25 after, 5 on the event day, 2 outside the window
        add("A", (day0 - (1 + i % 13) * DAY + 3_600) * 1000)
        add("A", (day0 + (1 + i % 13) * DAY + 3_600) * 1000)
    for i in range(5):
        add("A", (day0 + 60 * i) * 1000)
    add("A", (e - 14 * DAY) * 1000 - 1)
    add("A", (e + 14 * DAY) * 1000 + 1)
    add("A", (e - 14 * DAY) * 1000)       # on the window edges: inside
    add("A", (e + 14 * DAY) * 1000)
    for i in range(19):  # cell B: 19 valid before, 3 nan before, 30 after -> dropped
        add("B", (day0 - 2 * DAY) * 1000)
    for i in range(3):
        add("B", (day0 - 2 * DAY) * 1000, y=np.nan)
    for i in range(30):
        add("B", (day0 + 2 * DAY) * 1000)
    for i in range(25):  # cell C: enough fills but no dose
        add("C", (day0 - 2 * DAY) * 1000)
        add("C", (day0 + 2 * DAY) * 1000)
    for i in range(25):  # another currency
        add("A", (day0 - 2 * DAY) * 1000, ccy="ETH")
        add("A", (day0 + 2 * DAY) * 1000, ccy="ETH")
    f = pd.DataFrame(rows)
    f["day"] = pd.to_datetime(f["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
    return f


def test_panel_window_excludes_event_day_and_thin_cells():
    e = _utc("2025-10-10 22:55:31")
    frame = _panel_frame(e)
    p = p2events.build_panel(frame, "BTC", e, {"A": 0.05, "B": -0.1}, "BTC-pm2-20251010")
    assert list(p.columns) == p2events.PANEL_COLUMNS
    assert set(p["cell"]) == {"A"}
    assert (p["ccy"] == "BTC").all() and (p["event_id"] == "BTC-pm2-20251010").all()
    assert (p["dose"] == 0.05).all()
    assert "2025-10-10" not in set(p["day"])
    assert int((~p["post"]).sum()) == 26 and int(p["post"].sum()) == 26
    assert (p.loc[p["post"], "day"] > "2025-10-10").all()
    assert (p.loc[~p["post"], "day"] < "2025-10-10").all()
    assert p["y_hs_bp"].notna().all()


def test_panel_accepts_any_date_and_dose_vector_for_placebos():
    e = _utc("2025-10-10 22:55:31")
    frame = _panel_frame(e)
    placebo = _utc("2025-10-10 00:00:00")
    p = p2events.build_panel(frame, "BTC", placebo, pd.Series({"A": 0.02, "C": 0.03}), "placebo-1")
    assert set(p["cell"]) == {"A", "C"}
    assert p.set_index("cell")["dose"].groupby(level=0).first().to_dict() == {"A": 0.02, "C": 0.03}
    thin = p2events.build_panel(frame, "BTC", e, {"A": 0.05}, "x", min_fills=27)
    assert len(thin) == 0 and list(thin.columns) == p2events.PANEL_COLUMNS


def test_run_panel_writes_kept_events_only(timeline_root, tmp_path):
    out_dir = tmp_path / "doses"
    out_dir.mkdir()
    doses = {"BTC-pm-20240612": {"A": 0.005}, "BTC-pm2-20260524": {"A": 0.05, "B": np.nan},
             "BTC-pm2-20260525": {"A": -0.02}}
    for eid, vec in doses.items():
        pd.DataFrame({"cell": list(vec), "dose": list(vec.values()), "n_fills": 30, "n_valid": 30, "n_nonpos": 0,
                      "n_nan": 0})[p2events.DOSE_COLUMNS].to_parquet(out_dir / f"{eid}.parquet", index=False)
    e = _utc("2026-05-24 04:05:07")
    frame = _panel_frame(e)
    res = p2events.run_panel(root=timeline_root, out_dir=out_dir, frame=frame, ccys=("BTC",),
                             events_csv=tmp_path / "events.csv", doses_csv=tmp_path / "doses.csv",
                             panel_path=tmp_path / "panel.parquet")
    ev = pd.read_csv(tmp_path / "events.csv")
    assert list(ev.columns) == p2events.EVENTS_CSV_COLUMNS
    assert ev.set_index("event_id")["kept"].to_dict() == {"BTC-pm-20240612": False, "BTC-pm2-20260524": True,
                                                          "BTC-pm2-20260525": True}
    panel = pd.read_parquet(tmp_path / "panel.parquet")
    assert set(panel["event_id"]) <= {"BTC-pm2-20260524", "BTC-pm2-20260525"}
    assert set(panel.loc[panel["event_id"] == "BTC-pm2-20260524", "cell"]) == {"A"}
    assert res["kept"] == 2 and res["panel_rows"] == len(panel)
    (out_dir / "BTC-pm2-20260525.parquet").unlink()
    with pytest.raises(FileNotFoundError):
        p2events.run_panel(root=timeline_root, out_dir=out_dir, frame=frame, ccys=("BTC",),
                           events_csv=tmp_path / "e.csv", doses_csv=tmp_path / "d.csv", panel_path=tmp_path / "p.pq")


def test_dose_vectors_keep_finite_doses_per_event():
    d = pd.DataFrame({"event_id": ["a", "a", "b"], "cell": ["x", "y", "x"], "dose": [0.1, np.nan, -0.2]})
    v = p2events.dose_vectors(d)
    assert v["a"].to_dict() == {"x": 0.1} and v["b"].to_dict() == {"x": -0.2}
