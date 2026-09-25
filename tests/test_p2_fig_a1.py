"""A1: does the replica match the chain? (ABBILDUNGSWAHL section 7, A1)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from derive_surface import p2feeds, p2validate  # noqa: E402
from derive_surface.figs_p2 import _kit_t2a1 as kit  # noqa: E402
from derive_surface.figs_p2 import a1  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
REAL = REPO / "results" / "p2"
REAL_CAPITAL = REPO / "data" / "p2" / "derived" / "capital.parquet"
TS = 1_780_000_000


def _validation() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    rows = []

    def add(ccy, mgr, kind, rel, n_legs=1, book="", status="ok", K=10_000.0):
        for im in (True, False):
            rows.append({"ccy": ccy, "manager": mgr, "kind": kind, "block": 1, "ts": TS, "K_replica": K,
                         "K_chain": K if status == "ok" else np.nan, "abs_err": rel * K if status == "ok" else np.nan,
                         "rel_err": rel if status == "ok" else np.nan, "is_initial": im, "status": status,
                         "method": "direct", "expiry": TS + 86_400, "strike": 100.0, "is_call": True,
                         "amount": -1.0, "premium": 1.0, "n_legs": n_legs, "n_expiries": 1, "book": book,
                         "K_replica_single": K, "vol_rel_dev": 0.0, "fwd_rel_dev": 0.0, "spot_rel_dev": 0.0})

    for ccy, mgr in a1.ROWS:
        for i in range(12):
            rel = 0.0 if (mgr != "pm" and i < 3) else float(10 ** rng.uniform(-11, -7))
            if mgr == "pm2" and i == 3:
                rel = 2e-16                                  # below the axis: drawn on its edge
            add(ccy, mgr, "single", rel)
    add("HYPE", "pm2", "single", np.nan, status="revert")
    for ccy, mgrs, days in (("BTC", ("sm", "pm", "pm2"), ("M2 2025-07-03", "M4 2025-08-02")),
                            ("ETH", ("sm", "pm", "pm2"), ("M2 2025-07-03", "M5 2025-11-06", "M8 2026-07-01")),
                            ("HYPE", ("sm", "pm2"), ("M3 2026-05-30",))):
        for j, day in enumerate(days):
            for mgr in mgrs:
                rel = 0.0 if (mgr == "sm" and j == 0) else float(10 ** rng.uniform(-10, -8))
                add(ccy, mgr, "book", rel, n_legs=int(3 + 40 * j), book=day, K=2e6 * (j + 1))
    return pd.DataFrame(rows)


def _summary(v: pd.DataFrame) -> dict:
    ok = v[v["status"] == "ok"]
    return {"thresholds": {"median": 0.001, "p95": 0.01},
            "status_counts": v.groupby(["kind", "status"]).size().rename("n").reset_index().to_dict("records"),
            "cells": p2validate.summarize(ok).to_dict("records")}


def _capital(vol_max=1100.0, fwd_max=1000.0, spot=(900.0, 20.0, 30.0, 40.0)) -> pd.DataFrame:
    ts = np.array([p2validate.PM2_START_TS["BTC"] - 10, p2validate.PM2_START_TS["BTC"] + 10,
                   p2validate.PM2_START_TS["ETH"] + 20, p2validate.PM2_START_TS["HYPE"] + 30])
    return pd.DataFrame({"currency": ["BTC", "BTC", "ETH", "HYPE"], "ts": ts,
                         "vol_age": [5000.0, 60.0, vol_max, 30.0], "fwd_age": [9000.0, 40.0, 50.0, fwd_max],
                         "spot_age": list(spot)})


@pytest.fixture
def res(tmp_path):
    rd = tmp_path / "results"
    rd.mkdir()
    v = _validation()
    v.to_csv(rd / "validation.csv", index=False)
    (rd / "validation_summary.json").write_text(json.dumps(_summary(v)))
    _capital().to_parquet(tmp_path / "capital.parquet")
    return rd


def _load(res):
    return a1.load(res, capital_path=res.parent / "capital.parquet")


def test_points_are_ok_rows_and_mm_stays_in_the_table(res):
    data = _load(res)
    pts = data["points"]
    assert (pts["status"] == "ok").all()
    assert pts.loc[pts["drawn"], "is_initial"].all()
    assert (~pts.loc[~pts["is_initial"], "drawn"]).all()
    single_im = pts[(pts["kind"] == "single") & pts["is_initial"]]
    assert len(single_im) == 12 * 8
    assert data["revert_cases"] == 1 and data["revert_rows"] == 2


def test_exact_zeros_go_to_the_strip_and_tiny_values_to_the_axis_edge(res):
    pts = _load(res)["points"]
    zero = pts["rel_err"] == 0
    assert pts.loc[zero, "strip"].all() and not pts.loc[~zero, "strip"].any()
    tiny = (pts["rel_err"] > 0) & (pts["rel_err"] < a1.X_LO)
    assert tiny.any()
    assert pts.loc[tiny, "at_edge"].all()
    assert np.allclose(pts.loc[tiny, "x_plot"], a1.X_LO)


def test_build_writes_figure_and_tables(res, tmp_path):
    out = tmp_path / "figures"
    paths = a1.build(out_dir=out, results_dir=res, capital_path=res.parent / "capital.parquet")
    names = {p.name for p in paths}
    assert {"a1.pdf", "a1.png", "fig_a1_a.csv", "fig_a1_b.csv", "fig_a1_meta.csv"} <= names
    w, h = kit.pdf_size_inches(out / "a1.pdf")
    assert abs(w - 6.84) <= 0.005 and abs(h - 2.5) <= 0.02
    b = pd.read_csv(res / "fig_a1_b.csv")
    pts = b[b["item"] == "point"]
    mm = pts[~pts["is_initial"].astype(str).str.lower().eq("true")]
    assert len(mm) > 0 and not mm["drawn"].astype(str).str.lower().eq("true").any()


def test_figure_type_size_and_canvas(res):
    fig = a1.draw(_load(res))
    assert tuple(np.round(fig.get_size_inches(), 3)) == (7.0, 2.5)
    assert kit.small_texts(fig) == []
    assert kit.texts_off_canvas(fig) == []
    assert kit.overlapping_texts(fig) == []


def test_checks_agree_on_synthetic_data(res, tmp_path):
    a1.build(out_dir=tmp_path / "figures", results_dir=res, capital_path=res.parent / "capital.parquet")
    out = a1.run_checks(res, with_expected=False)
    assert len(out) == len(a1.CHECKS)
    assert out["agrees"].all(), out.loc[~out["agrees"], ["id", "figure", "source", "error"]].to_string()


def test_feed_age_sentence_only_when_it_holds(res, tmp_path):
    assert a1.FEED_SENTENCE in a1.caption(_load(res))
    _capital(vol_max=p2validate.MAX_VOL_AGE + 1).to_parquet(res.parent / "capital.parquet")
    data = _load(res)
    assert data["feed_age"]["holds"] is False
    assert a1.FEED_SENTENCE not in a1.caption(data)
    (res.parent / "capital.parquet").unlink()
    assert a1.FEED_SENTENCE not in a1.caption(_load(res))


def test_caption_has_no_dashes():
    assert "—" not in a1.CAPTION and "–" not in a1.CAPTION


@pytest.mark.skipif(not (REAL / "validation.csv").exists() or not REAL_CAPITAL.exists(),
                    reason="real results not present")
def test_real_data_meets_the_build_instruction(tmp_path):
    rd = tmp_path / "results"
    rd.mkdir()
    for name in ("validation.csv", "validation_summary.json"):
        shutil.copy(REAL / name, rd / name)
    a1.build(out_dir=tmp_path / "figures", results_dir=rd, capital_path=REAL_CAPITAL)
    out = a1.run_checks(rd)
    bad = out[~out["agrees"] | (out["matches_instruction"] == False)]  # noqa: E712
    assert bad.empty, bad.to_string()


def test_spot_feed_age_is_counted_and_named_in_the_caption(res, tmp_path):
    """A47: the vol and forward limits say nothing about the spot feed; fills of the PM2 window with a spot price
    older than the spot heartbeat are counted, named in the caption and kept (the first row lies before the
    window and does not count)."""
    hb = int(p2feeds.HEARTBEAT["spot"])
    data = _load(res)
    assert data["feed_age"]["spot_stale_fills"] == 0 and data["feed_age"]["spot_limit_s"] == hb
    assert a1.FEED_SENTENCE in a1.caption(data)
    assert f"none uses a spot price older than the heartbeat of the spot feed ({hb} seconds)" in a1.caption(data)
    _capital(spot=(5000.0, hb + 6.0, 20.0, 1161.0)).to_parquet(res.parent / "capital.parquet")
    data = _load(res)
    fa = data["feed_age"]
    assert fa["spot_stale_fills"] == 2 and fa["spot_age_max_s"] == 1161.0 and fa["holds"] is True
    assert (f"; 2 fills use a spot price older than the heartbeat of the spot feed ({hb} seconds) and stay in the "
            "sample.") in a1.caption(data)
    a1.build(out_dir=tmp_path / "figures", results_dir=res, capital_path=res.parent / "capital.parquet")
    meta = pd.read_csv(res / "fig_a1_meta.csv").set_index("key")["value"]
    assert float(meta["spot_stale_fills"]) == 2 and float(meta["spot_limit_s"]) == hb
    out = a1.run_checks(res, with_expected=False)
    assert out["agrees"].all(), out.loc[~out["agrees"], ["id", "figure", "source", "error"]].to_string()


def test_module_caption_names_vol_and_forward_and_the_spot_count():
    assert "no fill uses a vol or forward feed older than the limits of the validation blocks" in a1.CAPTION
    assert "\\PH{a1-spot-stale} fills use a spot price older than the heartbeat of the spot feed" in a1.CAPTION


def test_placeholder_clause_is_the_spot_clause():
    assert a1._SPOT_CLAUSE_PH == a1.SPOT_CLAUSE.format(n="\\PH{a1-spot-stale}", hb="\\PH{a1-spot-heartbeat}")
