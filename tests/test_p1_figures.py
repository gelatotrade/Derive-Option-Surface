from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from derive_surface import figures_p1  # noqa: E402

T0 = 1_735_689_600_000          # 2025-01-01 UTC
MONTH = 30 * 86_400_000
SLOTS = ["A1", "F1", "F2", "F3", "F4", "F5", "F6", "T1", "T2"]


def frame(n=900, seed=0):
    """An analysis frame with every column the figures read."""
    rng = np.random.default_rng(seed)
    classes = np.array(["other", "rfq", "dominant_maker", "mm_programme", "large", "vault"])
    ccy = rng.choice(["BTC", "ETH", "HYPE"], n)
    index = np.where(ccy == "BTC", 84_000.0, np.where(ccy == "ETH", 2_900.0, 52.0))
    f = pd.DataFrame({
        "trade_id": ["t{}".format(i) for i in range(n)],
        "ts": T0 + rng.integers(0, 20 * MONTH, n),
        "currency": ccy,
        "index_price": index,
        "instrument_name": ["{}-20250131-100000-C".format(c) for c in ccy],
        "expiry": (T0 + 30 * 86_400_000) // 1000,
        "strike": 100_000.0,
        "option_type": rng.choice(["C", "P"], n),
        "taker_class": rng.choice(classes, n),
        "taker_wallet": rng.choice(["0x{}".format(i) for i in range(30)], n),
        "cluster": rng.choice(["0x{}".format(i) for i in range(30)], n),
        "delta_bucket": rng.choice(["00-10", "25-40", "40-60", "90-100"], n),
        "tenor_bucket": rng.choice(["<=2d", "7-30d", ">90d"], n),
        "abs_delta_pct": rng.uniform(1, 99, n),
        "tenor_days": rng.uniform(0.5, 120, n),
        "amount": np.abs(rng.lognormal(0, 0.8, n)),
        "notional": np.abs(rng.lognormal(9, 1.2, n)),
        "price": np.abs(rng.lognormal(4, 1, n)),
        "mark_b_t": np.abs(rng.lognormal(4, 1, n)),
        "maker_side": rng.choice([-1, 1], n),
        "hs": rng.normal(2.0, 3.0, n),
        "as_usd": rng.normal(-0.5, 2.0, n),
        "net_edge": rng.normal(1.0, 3.0, n),
        "fee_maker": np.abs(rng.normal(0.4, 0.2, n)) * (rng.random(n) > 0.6),
        "fee_taker": np.abs(rng.normal(1.2, 0.5, n)),
        "rebate_maker": np.abs(rng.normal(0.1, 0.05, n)),
        "hedge": np.abs(rng.normal(0.5, 0.2, n)),
        "svi_age_s_t": np.abs(rng.normal(30, 25, n)),
        "is_sweep": rng.random(n) < 0.1,
        "size_above_p90": rng.random(n) < 0.1,
        "delta_t": rng.uniform(-1, 1, n),
        "fwd_t": index * 1.001,
        "iv_fill": np.abs(rng.normal(0.6, 0.1, n)),
        "iv_mark_t": np.abs(rng.normal(0.6, 0.1, n)),
        "mo_set": rng.normal(1.0, 8.0, n),
        "mo_set_vrp": rng.normal(0.0, 8.0, n),
    })
    for h in ("1m", "5m", "30m", "4h", "24h"):
        f["mo_usd_{}".format(h)] = rng.normal(1.5, 6.0, n)
        f["mo_dn_{}".format(h)] = f["mo_usd_{}".format(h)] - rng.normal(0, 0.5, n)
        f["mo_vol_{}".format(h)] = rng.normal(2.0, 4.0, n)
        f["mo_usd_a_{}".format(h)] = f["mo_usd_{}".format(h)] + rng.normal(0, 1.0, n)
        f["lag_a_{}_s".format(h)] = np.abs(rng.normal(900, 400, n))
        f["mark_b_{}".format(h)] = f["mark_b_t"] + rng.normal(0, 1, n)
        f["iv_b_{}".format(h)] = np.abs(rng.normal(0.6, 0.1, n))
        f["fwd_b_{}".format(h)] = f["fwd_t"] + rng.normal(0, 50, n)
    f["y_usd"] = f["mo_usd_30m"]
    f["y_dn"] = f["mo_dn_30m"]
    f["y_vol"] = f["mo_vol_30m"]
    f["day"] = pd.to_datetime(f["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
    f["month"] = pd.to_datetime(f["ts"], unit="ms", utc=True).dt.strftime("%Y-%m")
    return f


def results():
    cells = []
    for c in ("BTC", "ETH", "HYPE"):
        for d in ("00-10", "25-40", "40-60", "90-100"):
            for t in ("<=2d", "7-30d", ">90d"):
                mean = {"BTC": 20.0, "ETH": 1.0, "HYPE": 0.2}[c] * (1 if d != "00-10" else -1)
                cells.append({"currency": c, "delta_bucket": d, "tenor_bucket": t, "fills": 900,
                              "mean": mean, "lo": mean - 2, "hi": mean + 2, "p": 0.01,
                              "positive": mean - 2 > 0, "negative": mean + 2 < 0})
    return {
        "summary": {"fills": 900, "horizon": "30m", "half_spread_bp": 1.0, "missing_vol_unit": 12, "seed": 1, "b": 99,
                    "H1": {"top10_share": {"share": 0.905, "lo": 0.698, "hi": 0.943, "loss_total": -3_240_781,
                                           "wallets": 30, "top": 10},
                           "size_coefficient": {"beta": -0.765, "se": 1.04, "t": -0.74, "p": 0.476},
                           "sweep_coefficient": {"beta": -0.357, "se": 3.46, "t": -0.10, "p": 0.944}, "rejected": True},
                    "H2": {"markout_30m": {"mean": 4.22, "lo": 1.55, "hi": 8.53, "p": 0.0075, "n": 1994, "clusters": 8},
                           "settlement_vrp": {"mean": -6.37, "lo": -17.79, "hi": 5.14}, "rejected": False},
                    "H3": {"did": {"beta": -1.046, "se": 0.85, "t": -1.23, "p": 0.2419, "n": 147_240, "clusters": 3879,
                                   "placebos": 100, "placebo_share_more_extreme": 0.46, "window_days": 90,
                                   "event_ms": 1_782_205_200_000, "treated": "HYPE", "y": "y_vol"}, "rejected": True},
                    "H4": {"cells": 36, "share_positive": 0.5, "atm_short": [], "rejected": True}},
        "cells": pd.DataFrame(cells),
        "classes": pd.DataFrame({
            "class": ["other", "rfq", "vault", "large", "mm_programme", "dominant_maker"],
            "fills": [329_432, 121_064, 1_994, 52_200, 42_976, 56_274],
            "clusters": [10_749, 4_512, 8, 104, 33, 17],
            "mean": [24.73, 15.21, 4.22, 3.89, -20.67, -25.41],
            "lo": [21.95, 12.18, 1.55, -8.90, -24.37, -28.12],
            "hi": [28.10, 18.96, 8.53, 19.07, -1.90, -19.87],
            "p": [0.0005, 0.0005, 0.0075, 0.6625, 0.094, 0.1065],
            "mean_hs": [25.6, 16.0, 5.0, 4.0, -16.0, -16.6],
            "mean_as": [-0.87, -0.8, -0.8, -0.1, -4.7, -8.81],
            "mean_fee": [1.24, 1.3, 34.21, 1.2, 1.2, 1.23],
            "mean_rebate": [0.57, 0.5, 0.1, 0.2, 0.3, 0.08],
            "mean_hedge": [2.87, 3.0, 3.0, 3.5, 3.5, 3.93],
            "mean_ne": [21.19, 11.4, 0.5, -0.7, -25.0, -30.49],
            "mean_dn": [25.3, 15.0, 4.0, 3.5, -16.0, -16.0],
            "mean_vol": [3.6, 1.5, 1.7, 1.6, -0.6, -1.3],
            "share_negative": [0.27, 0.3, 0.3, 0.4, 0.62, 0.676],
            "mean_notional": [8_000.0, 9_000.0, 240_405.0, 50_000.0, 20_000.0, 8_858.0]}),
        "lorenz": pd.DataFrame({"wallet": ["0x{}".format(i) for i in range(50)],
                                "loss": -np.sort(np.abs(np.random.default_rng(2).lognormal(9, 2, 50)))[::-1],
                                "wallet_share": np.linspace(0.02, 1.0, 50),
                                "loss_share": np.clip(np.linspace(0.39, 1.0, 50), 0, 1)}),
        "horizons": pd.DataFrame({"horizon": ["1m", "5m", "30m", "4h", "24h"], "n": [900] * 5,
                                  "mean": [15.22, 13.32, 13.05, 13.06, 13.02],
                                  "lo": [9.25, 8.0, 8.0, 8.0, 8.0], "hi": [21.9, 19.0, 19.0, 19.0, 19.0],
                                  "p": [0.0005] * 5,
                                  "mean_dn": [15.71, 15.6, 15.5, 15.4, 16.0],
                                  "mean_vol": [2.59, 2.58, 2.56, 2.54, 1.89],
                                  "mean_path_a": [12.96, 12.8, 12.5, 12.6, 13.2]}),
        "sensitivity": pd.DataFrame({"half_spread_bp": [0.0, 1.0, 3.0], "cells": [97, 97, 97],
                                     "share_positive": [0.5773, 0.4948, 0.3814]}),
        "paths": pd.DataFrame({"group": ["all", "lag_a <= 300 s", "lag_a <= 3600 s", "svi_age <= 60 s",
                                         "svi_age > 60 s"],
                               "fills": [540_531, 26_885, 135_971, 501_384, 39_147],
                               "correlation": [0.390, 0.896, 0.939, 0.397, 0.240],
                               "sign_agreement": [0.691, 0.913, 0.835, 0.688, 0.719],
                               "median_gap": [0.022, -0.005, 0.007, 0.023, 0.017],
                               "median_lag_a_s": [15_026.3, 117.6, 1_144.8, 15_047.3, 14_726.9]}),
    }


def inputs():
    return {"frame": frame(), "results": results(), "svi": pd.DataFrame()}


def test_registry_covers_every_planned_slot():
    assert sorted(figures_p1.FIGURES) == SLOTS


@pytest.mark.parametrize("name", SLOTS)
def test_every_figure_writes_a_pdf_and_a_png(tmp_path, name):
    paths = figures_p1.FIGURES[name](inputs(), tmp_path)
    assert [p.suffix for p in paths] == [".pdf", ".png"]
    assert all(p.exists() and p.stat().st_size > 1500 for p in paths)
    assert all(p.stem == name.lower() for p in paths)


def test_build_runs_only_the_requested_subset(tmp_path, monkeypatch):
    monkeypatch.setattr(figures_p1, "load_inputs", lambda root, results_dir: inputs())
    out = figures_p1.build("data/p1", "results/p1", tmp_path, only=["T2", "F4"])
    assert sorted(out) == ["F4", "T2"] and all(len(v) == 2 for v in out.values())


def test_build_rejects_an_unknown_slot(tmp_path, monkeypatch):
    monkeypatch.setattr(figures_p1, "load_inputs", lambda root, results_dir: inputs())
    with pytest.raises(KeyError):
        figures_p1.build("data/p1", "results/p1", tmp_path, only=["F9"])
