"""Tests for derive_surface.inference_p2_h4: H4 of Paper 2 (preregistration H4, Nachtraege 3 and 4).

All tests are offline and use synthetic panels with known solutions: the two-way within estimator against a brute-force
OLS with dummies, the fast wild cluster bootstrap against an explicit refit of every bootstrap sample, the placebo
calendar against hand-counted days, and a small end-to-end run on a synthetic frame.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from derive_surface import inference_p2_h4 as h4
from derive_surface import p2events
from derive_surface.p2chain import block_at_ts

DAY = 86_400


def _utc(s: str) -> int:
    return int(pd.Timestamp(s, tz="UTC").timestamp())


# ------------------------------------------------------------------------------------------------ synthetic panels

def _panel(seed: int = 0, beta: float = 0.0, n_events: int = 4, n_cells: int = 4, half: int = 5, per: int = 3,
           sigma: float = 1.0) -> pd.DataFrame:
    """Events of two currencies with overlapping windows; y = alpha(cell, event) + gamma(day, ccy) + beta post dose + e."""
    rng = np.random.default_rng(seed)
    base = pd.Timestamp("2025-09-01", tz="UTC")
    gamma = {}
    rows = []
    for e in range(n_events):
        ccy = "BTC" if e % 2 == 0 else "ETH"
        ev_day = e * 3 + half
        eid = f"{ccy}-pm2-e{e}"
        for c in range(n_cells):
            cell = f"{ccy}|{'buy' if c % 2 else 'sell'}|c{c}"
            alpha = rng.normal(0, 3)
            dose = rng.uniform(-0.5, 0.2)
            for d in range(ev_day - half, ev_day + half + 1):
                if d == ev_day:
                    continue
                day = (base + pd.Timedelta(days=d)).strftime("%Y-%m-%d")
                g = gamma.setdefault((day, ccy), rng.normal(0, 2))
                post = d > ev_day
                for k in range(per + (c + d) % 2):          # unbalanced
                    y = alpha + g + beta * post * dose + sigma * rng.normal()
                    rows.append({"fill_key": f"{eid}-{c}-{d}-{k}", "ccy": ccy, "cell": cell, "event_id": eid,
                                 "post": post, "dose": dose, "y_hs_bp": y, "day": day})
    return pd.DataFrame(rows, columns=p2events.PANEL_COLUMNS)


def _dummies(codes: np.ndarray) -> np.ndarray:
    m = np.zeros((len(codes), codes.max() + 1))
    m[np.arange(len(codes)), codes] = 1.0
    return m


def _brute(panel: pd.DataFrame, y: np.ndarray = None):
    """OLS of y on [post*dose, dummies alpha(cell,event), dummies gamma(day,ccy)] with pinv; cluster-robust SE by day."""
    d = h4.design(panel)
    yv = d.y if y is None else y
    X = np.column_stack([d.x, _dummies(d.codes_a), _dummies(d.codes_b)])
    with np.errstate(all="ignore"):                            # spurious BLAS flags under numpy 2
        row = np.linalg.pinv(X)[0]
        coef = np.linalg.lstsq(X, yv, rcond=None)[0]
        resid = yv - X @ coef
    beta = float(row @ yv)
    scores = np.bincount(d.clusters, weights=row * resid, minlength=d.n_clusters)
    g = d.n_clusters
    se = float(np.sqrt(g / (g - 1) * (scores ** 2).sum()))
    return beta, se, beta / se


# ------------------------------------------------------------------------------------------------ within estimator

def test_design_groups_are_cell_event_and_day_currency_clustered_by_day():
    p = _panel(seed=1)
    d = h4.design(p)
    assert d.codes_a.max() + 1 == p.groupby(["cell", "event_id"]).ngroups
    assert d.codes_b.max() + 1 == p.groupby(["day", "ccy"]).ngroups
    assert d.n_clusters == p["day"].nunique()
    np.testing.assert_allclose(d.x, p["post"].to_numpy(float) * p["dose"].to_numpy(float))


def test_demean_two_way_equals_residual_on_both_dummy_sets():
    p = _panel(seed=2)
    d = h4.design(p)
    rng = np.random.default_rng(3)
    V = np.column_stack([d.x, d.y, rng.normal(size=len(p))])
    got, iters = h4.demean_two_way(V, d.codes_a, d.codes_b)
    D = np.column_stack([_dummies(d.codes_a), _dummies(d.codes_b)])
    with np.errstate(all="ignore"):
        want = V - D @ np.linalg.lstsq(D, V, rcond=None)[0]
    np.testing.assert_allclose(got, want, atol=1e-9)
    assert iters >= 1
    np.testing.assert_allclose(h4.demean_exact(V, d.codes_a, d.codes_b), want, atol=1e-9)


def test_fit_matches_brute_force_ols_with_dummies_and_day_clusters():
    p = _panel(seed=4, beta=2.0)
    f = h4.fit(p)
    beta, se, t = _brute(p)
    assert f.beta == pytest.approx(beta, rel=1e-9)
    assert f.se == pytest.approx(se, rel=1e-8)
    assert f.t == pytest.approx(t, rel=1e-8)
    assert f.n == len(p) and f.n_clusters == p["day"].nunique()


def test_fit_recovers_beta_exactly_without_noise():
    p = _panel(seed=5, beta=-7.5, sigma=0.0)
    assert h4.fit(p).beta == pytest.approx(-7.5, abs=1e-8)


def test_fit_without_variation_in_post_dose_is_nan():
    p = _panel(seed=6)
    p["dose"] = 0.0
    f = h4.fit(p)
    assert np.isnan(f.beta) and np.isnan(f.t)


# ------------------------------------------------------------------------------------------------ wild cluster bootstrap

def test_restricted_bootstrap_draws_equal_explicit_refits():
    p = _panel(seed=7, beta=1.0)
    f = h4.fit(p)
    prep = h4.wcr_prepare(f)
    rng = np.random.default_rng(8)
    W = rng.choice([-1.0, 1.0], size=(4, f.n_clusters))
    beta_star, t_star = h4.wcr_draws(prep, W)
    u_r = f.yd                                   # restricted residuals under beta = 0: y net of both fixed effects
    fitted_r = f.design.y - u_r
    for b in range(len(W)):
        y_star = fitted_r + W[b][f.design.clusters] * u_r
        bb, _, tb = _brute(p, y_star)
        assert beta_star[b] == pytest.approx(bb, rel=1e-7, abs=1e-10)
        assert t_star[b] == pytest.approx(tb, rel=1e-6)


def test_bootstrap_with_unit_weights_reproduces_the_sample_t():
    p = _panel(seed=9, beta=0.5)
    f = h4.fit(p)
    _, t_star = h4.wcr_draws(h4.wcr_prepare(f), np.ones((1, f.n_clusters)))
    assert t_star[0] == pytest.approx(f.t, rel=1e-8)


def test_unrestricted_interval_draws_are_beta_plus_weighted_scores():
    p = _panel(seed=10, beta=1.0)
    f = h4.fit(p)
    W = np.random.default_rng(11).choice([-1.0, 1.0], size=(3, f.n_clusters))
    got = h4.wcu_draws(f, W)
    for b in range(3):
        y_star = (f.design.y - f.resid) + W[b][f.design.clusters] * f.resid
        assert got[b] == pytest.approx(_brute(p, y_star)[0], rel=1e-7)


def test_wild_bootstrap_one_sided_p_detects_signal_and_ignores_wrong_sign():
    pos = h4.wild_cluster_test(h4.fit(_panel(seed=12, beta=3.0)), b=199, seed=1)
    assert pos["p"] <= 0.05 and pos["lo"] > 0
    neg = h4.wild_cluster_test(h4.fit(_panel(seed=12, beta=-3.0)), b=199, seed=1)
    assert neg["p"] >= 0.9                                    # one-sided for beta > 0
    assert set(pos) >= {"beta", "se", "t", "p", "lo", "hi", "b", "seed", "clusters", "n"}


def test_wild_bootstrap_is_roughly_calibrated_under_the_null():
    ps = [h4.wild_cluster_test(h4.fit(_panel(seed=100 + s, beta=0.0, n_events=4, half=6)), b=199, seed=s)["p"]
          for s in range(30)]
    ps = np.array(ps)
    assert 0.3 < ps.mean() < 0.7
    assert (ps <= 0.05).sum() <= 6


def test_wild_bootstrap_is_reproducible_with_the_seed():
    f = h4.fit(_panel(seed=13, beta=0.3))
    a = h4.wild_cluster_test(f, b=99, seed=20260924)
    b = h4.wild_cluster_test(f, b=99, seed=20260924)
    assert a == b


# ------------------------------------------------------------------------------------------------ placebo calendar

def _entry(ts: int, params: dict) -> dict:
    return {"from_block": block_at_ts(ts), "from_ts": ts, "source": "test", "params": params}


@pytest.fixture()
def params_root(tmp_path: Path) -> Path:
    root = tmp_path / "params"
    root.mkdir()
    pm2 = [_entry(_utc("2025-06-09 05:00"), {"MarginParameters": {"imFactor": 1.3}, "CollateralParameters": {"a": 1}}),
           _entry(_utc("2025-11-10 03:00"), {"MarginParameters": {"imFactor": 1.3}, "CollateralParameters": {"a": 2}}),
           _entry(_utc("2025-12-15 22:00"), {"MarginParameters": {"imFactor": 1.2}, "CollateralParameters": {"a": 2}})]
    pm = [_entry(_utc("2023-12-04 16:00"), {"BasisContingencyParameters": {"x": 1}}),
          _entry(_utc("2025-02-22 19:52"), {"BasisContingencyParameters": {"x": 2}})]
    sm = [_entry(_utc("2023-12-04 16:00"), {"OptionMarginParams": {"a": 1}}),
          _entry(_utc("2025-08-20 00:00"), {"OptionMarginParams": {"a": 2}})]
    lib = [_entry(_utc("2026-02-03 21:00"), {"MarginParameters": {"imFactor": 1.1}})]
    for name, rows in (("BTC_pm2", pm2), ("BTC_pm", pm), ("BTC_sm", sm), ("BTC_pm2_lib_deadbeef", lib)):
        (root / f"{name}.json").write_text(json.dumps(rows))
    return root


def test_change_days_count_every_row_of_the_event_timelines(params_root):
    days = h4.change_days("BTC", root=params_root)
    want = sorted({_utc(s) // DAY for s in ("2025-06-09", "2025-11-10", "2025-12-15", "2023-12-04", "2025-02-22")})
    assert list(days) == want                                   # collateral-only row counts, SM and libs do not
    broad = h4.change_days("BTC", root=params_root, scope="all")
    assert set(broad) == set(want) | {_utc("2025-08-20") // DAY, _utc("2026-02-03") // DAY}


def test_admissible_days_keep_gap_manager_window_and_sample():
    ev = _utc("2026-01-10 22:50")
    changes = np.array([_utc("2025-12-01") // DAY, _utc("2026-01-10") // DAY, _utc("2026-04-01") // DAY])
    window = (_utc("2025-12-20 23:00"), _utc("2026-09-30 08:00"))   # opens inside the gap around 10.01.
    sample = (_utc("2024-01-11"), _utc("2026-03-20 12:00"))
    days = h4.admissible_days(ev, window, changes, sample, gap_days=28, window_days=14)
    first, last = _utc("2026-02-07") // DAY, _utc("2026-03-04") // DAY  # 28 d after 10.01.; 28 d before 01.04.
    # the sample end (t + 14 d <= 20.03. 12:00, i.e. day <= 05.03.) does not bind here
    assert days.min() == first
    assert days.max() == last
    assert len(days) == last - first + 1
    tight = h4.admissible_days(ev, window, changes, (_utc("2024-01-11"), _utc("2026-03-10 12:00")), 28, 14)
    assert tight.max() == _utc("2026-02-23") // DAY             # 24.02. 22:50 + 14 d = 10.03. 22:50 > 12:00
    late_window = h4.admissible_days(ev, (_utc("2026-02-20 23:00"), window[1]), changes, sample, 28, 14)
    assert late_window.min() == _utc("2026-02-21") // DAY       # 20.02. 22:50 is before the window opens


def test_draw_placebos_is_deterministic_and_takes_doses_of_the_same_currency():
    kept = pd.DataFrame({"event_id": ["BTC-a", "BTC-b", "ETH-a"], "ccy": ["BTC", "BTC", "ETH"],
                         "event_ts": [_utc("2025-02-22 19:52:37"), _utc("2026-01-08 22:50:49"),
                                      _utc("2026-01-08 22:50:49")]})
    days = {"BTC-a": np.array([20000, 20001]), "BTC-b": np.array([20100]), "ETH-a": np.array([20200, 20300])}
    d1 = h4.draw_placebos(kept, days, n_rep=50, seed=20260924)
    d2 = h4.draw_placebos(kept, days, n_rep=50, seed=20260924)
    assert d1 == d2 and len(d1) == 50 and all(len(r) == 3 for r in d1)
    for rep in d1:
        for dr, ev in zip(rep, kept.itertuples()):
            assert dr["event_id"] == ev.event_id
            assert dr["placebo_ts"] // DAY in days[ev.event_id]
            assert dr["placebo_ts"] % DAY == ev.event_ts % DAY  # time of day of the real event
            assert dr["source"].split("-")[0] == ev.ccy
    assert {r[0]["source"] for r in d1} == {"BTC-a", "BTC-b"}   # both BTC dose vectors occur
    assert {r[2]["source"] for r in d1} == {"ETH-a"}


def test_draw_placebos_fails_without_admissible_day():
    kept = pd.DataFrame({"event_id": ["BTC-a"], "ccy": ["BTC"], "event_ts": [_utc("2025-02-22")]})
    with pytest.raises(ValueError):
        h4.draw_placebos(kept, {"BTC-a": np.array([], dtype=int)}, n_rep=1, seed=1)


# ------------------------------------------------------------------------------------------------ synthetic frame

def _frame(seed: int = 0, effect_ts=None, effect: float = 0.0, start="2025-06-01", end="2026-03-15",
           per_day: int = 3) -> pd.DataFrame:
    """Fills of BTC in four cells; y shifts by ``effect * dose(cell)`` after ``effect_ts`` (known doses below)."""
    rng = np.random.default_rng(seed)
    days = pd.date_range(start, end, freq="D", tz="UTC")
    rows = []
    for i, d in enumerate(days):
        for c, cell in enumerate(CELLS):
            for k in range(per_day):
                ts = int(d.timestamp()) + 3600 * (1 + 7 * k) + 60 * c
                y = c + 0.5 * rng.normal()
                if effect_ts is not None and ts > effect_ts and d.strftime("%Y-%m-%d") != _day(effect_ts):
                    y += effect * DOSES[cell]
                rows.append({"fill_key": f"f{i}-{c}-{k}", "ts": ts * 1000, "ccy": "BTC", "cell": cell,
                             "day": d.strftime("%Y-%m-%d"), "y_hs_bp": y})
    return pd.DataFrame(rows)


CELLS = ["BTC|buy|00-10|<=2d", "BTC|buy|40-60|7-30d", "BTC|sell|10-25|2-7d", "BTC|sell|40-60|30-90d"]
DOSES = dict(zip(CELLS, [-0.4, -0.1, -0.25, 0.05]))


def _day(ts: int) -> str:
    return pd.Timestamp(ts, unit="s", tz="UTC").strftime("%Y-%m-%d")


def test_placebo_panel_is_p2events_build_panel_on_the_drawn_date():
    fr = _frame(seed=1)
    ts = _utc("2025-10-01 12:00")
    draws = [{"event_id": "BTC-pm2-x", "ccy": "BTC", "placebo_ts": ts, "source": "BTC-pm2-y"}]
    got = h4.placebo_panel(h4.split_frame(fr), draws, {"BTC-pm2-y": pd.Series(DOSES)}, rep=7)
    want = p2events.build_panel(fr, "BTC", ts, pd.Series(DOSES), "P007:BTC-pm2-x")
    pd.testing.assert_frame_equal(got.sort_values("fill_key").reset_index(drop=True),
                                  want.sort_values("fill_key").reset_index(drop=True))


def test_outlier_cells_are_removed_by_absolute_dose():
    p = _panel(seed=14)
    p.loc[p["cell"] == p["cell"].iloc[0], "dose"] = -1.6
    q = h4.drop_outlier_cells(p, max_abs_dose=1.0)
    assert (q["dose"].abs() <= 1.0).all()
    assert len(q) == len(p) - int((p["cell"] == p["cell"].iloc[0]).sum())


# ------------------------------------------------------------------------------------------------ verdict and figure table

@pytest.mark.parametrize("beta,p,p95,rejected", [
    (2.0, 0.01, 1.0, False),
    (2.0, 0.06, 1.0, True),       # p too large
    (-2.0, 0.01, -3.0, True),     # beta not positive
    (2.0, 0.01, 2.0, True),       # not above the 95th percentile
    (2.0, 0.01, float("nan"), True),
])
def test_verdict_follows_the_preregistered_rule(beta, p, p95, rejected):
    v = h4.verdict(beta, p, p95)
    assert v["rejected"] is rejected
    assert set(v["criteria"]) == {"beta_positive", "p_le_alpha", "beta_gt_placebo_p95"}


def test_placebo_percentile_is_numpy_linear_over_finite_betas():
    betas = np.r_[np.arange(100, dtype=float), np.nan]
    s = h4.placebo_summary(betas, beta=96.5)
    assert s["p95"] == pytest.approx(np.quantile(np.arange(100.0), 0.95))
    assert s["finite"] == 100 and s["n"] == 101
    assert s["share_ge_beta"] == pytest.approx(3 / 100)


def test_event_figure_table_terciles_and_means():
    rows = []
    doses = {"c1": -0.3, "c2": -0.2, "c3": -0.1, "c4": 0.0, "c5": 0.1, "c6": 0.2}
    for cell, d in doses.items():
        for post, y in ((False, 1.0), (True, 1.0 + 10 * d)):
            for k in range(2):
                rows.append({"fill_key": f"{cell}{post}{k}", "ccy": "BTC", "cell": cell, "event_id": "E1",
                             "post": post, "dose": d, "y_hs_bp": y + k, "day": "2026-01-01"})
    panel = pd.DataFrame(rows)
    events = pd.DataFrame({"event_id": ["E1", "E2"], "ccy": ["BTC", "BTC"], "manager": ["pm2", "pm2"],
                           "event_day": ["2026-01-08", "2026-02-01"], "event_utc": ["2026-01-08 22:50:49", "x"],
                           "kinds": ["MarginParameters", "scenarios"], "kept": [True, True]})
    t = h4.event_figure_table(panel, events)
    r = t.set_index("event_id").loc["E1"]
    assert r["n_cells"] == 6 and r["median_dose"] == pytest.approx(-0.05)
    assert r["t1_cells"] == 2 and r["t1_dose_lo"] == pytest.approx(-0.3) and r["t1_dose_hi"] == pytest.approx(-0.2)
    assert r["t1_y_pre"] == pytest.approx(1.5) and r["t1_y_post"] == pytest.approx(1.5 - 2.5)
    assert r["t3_y_post"] == pytest.approx(1.5 + 1.5)
    assert t.set_index("event_id").loc["E2", "n_cells"] == 0      # kept event without panel cells stays listed


# ------------------------------------------------------------------------------------------------ end-to-end run

def _setup(tmp_path: Path, params_root: Path, effect: float):
    ev_ts = _utc("2025-12-15 22:00")
    fr = _frame(seed=3, effect_ts=ev_ts, effect=effect)
    events = pd.DataFrame({"event_id": ["BTC-pm2-20251215"], "ccy": ["BTC"], "manager": ["pm2"],
                           "event_ts": [ev_ts], "event_day": ["2025-12-15"], "event_utc": ["2025-12-15 22:00:00"],
                           "kinds": ["MarginParameters"], "kept": [True]})
    doses = pd.DataFrame({"event_id": "BTC-pm2-20251215", "ccy": "BTC", "cell": CELLS,
                          "dose": [DOSES[c] for c in CELLS]})
    panel = p2events.build_panel(fr, "BTC", ev_ts, pd.Series(DOSES), "BTC-pm2-20251215")
    return dict(frame=fr, events=events, doses=doses, panel=panel, params_root=params_root,
                out_dir=tmp_path / "out", parts_dir=tmp_path / "parts")


def test_run_writes_all_outputs_and_resumes(tmp_path, params_root):
    kw = _setup(tmp_path, params_root, effect=20.0)            # capital cheaper (d < 0) -> smaller half spread
    partial = h4.run(b=99, n_placebo=6, max_seconds=0.0, **kw)
    assert partial["status"] == "PARTIAL"
    assert not (kw["out_dir"] / "h4.json").exists()
    res = h4.run(b=99, n_placebo=6, **kw)
    assert res["status"] == "DONE"
    out = json.loads((kw["out_dir"] / "h4.json").read_text())
    for key in ("stat", "lo", "hi", "rejected", "rule", "n", "p", "t", "se", "clusters", "placebo", "criteria"):
        assert key in out
    assert out["stat"] > 0 and out["p"] <= 0.05
    assert out["placebo"]["n"] == 6
    assert out["panel_check"]["equal"] is True
    pl = pd.read_csv(kw["out_dir"] / "h4_placebo.csv")
    assert list(pl["rep"]) == list(range(6))
    assert pl["draws"].str.contains("BTC-pm2-20251215").all()
    fig = pd.read_csv(kw["out_dir"] / "fig_h4_events.csv")
    assert list(fig["event_id"]) == ["BTC-pm2-20251215"]
    sens = json.loads((kw["out_dir"] / "sensitivity_h4.json").read_text())
    assert sens["exploratory"] is True
    assert set(sens["by_ccy"]) == {"BTC"}
    assert {"no_outlier_cells", "placebo_all_timelines"} <= set(sens)
    # a third call recomputes nothing in the placebo stage and gives the same numbers
    again = h4.run(b=99, n_placebo=6, **kw)
    assert again["placebo_new"] == 0
    assert json.loads((kw["out_dir"] / "h4.json").read_text()) == out


def test_run_placebo_dates_keep_the_gap_to_every_change(tmp_path, params_root):
    kw = _setup(tmp_path, params_root, effect=0.0)
    h4.run(b=19, n_placebo=8, **kw)
    pl = pd.read_csv(kw["out_dir"] / "h4_placebo.csv")
    changes = h4.change_days("BTC", root=params_root)
    for s in pl["draws"]:
        for part in s.split(";"):
            _, day, _ = part.split("@")
            dn = pd.Timestamp(day, tz="UTC").value // 10 ** 9 // DAY
            assert np.abs(changes - dn).min() >= 28


def test_run_refuses_stale_placebo_parts(tmp_path, params_root):
    kw = _setup(tmp_path, params_root, effect=0.0)
    h4.run(b=19, n_placebo=3, **kw)
    kw["frame"] = kw["frame"].iloc[:-5]
    with pytest.raises(RuntimeError, match="stale"):
        h4.run(b=19, n_placebo=3, **kw)


def test_main_cli_run(monkeypatch):
    seen = {}

    def fake_run(**kw):
        seen.update(kw)
        return {"status": "DONE"}

    monkeypatch.setattr(h4, "run", fake_run)
    assert h4.main(["run", "--max-seconds", "30", "--b", "99"]) == 0
    assert seen["max_seconds"] == 30.0 and seen["b"] == 99
