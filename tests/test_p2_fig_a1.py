"""A1: does the replica match the chain? (FIGURE_SELECTION section 7, A1)."""
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
    fa = _load(res)["feed_age"]
    assert a1.feed_sentence(fa).startswith(a1.feed_prefix(fa))
    _capital(vol_max=p2validate.MAX_VOL_AGE + 1).to_parquet(res.parent / "capital.parquet")
    data = _load(res)
    assert data["feed_age"]["holds"] is False
    assert a1.feed_sentence(data["feed_age"]) == ""
    (res.parent / "capital.parquet").unlink()
    assert a1.feed_sentence(_load(res)["feed_age"]) == ""


def test_caption_has_no_dashes():
    assert "—" not in a1.CAPTION and "–" not in a1.CAPTION


@pytest.mark.skipif(not (REAL / "validation.csv").exists() or not REAL_CAPITAL.exists(),
                    reason="real results not present")
def test_real_data_figure_agrees_with_the_results(tmp_path):
    """On the real data every value the figure prints equals its source.  The expectations of the build
    instruction are the numbers of the pilot cut (17 September 2026); on the registered sample they differ by
    design, so ``p2_figure_check.py`` reports them in its column "Build instruction" instead of failing on them."""
    rd = tmp_path / "results"
    rd.mkdir()
    for name in ("validation.csv", "validation_summary.json"):
        shutil.copy(REAL / name, rd / name)
    a1.build(out_dir=tmp_path / "figures", results_dir=rd, capital_path=REAL_CAPITAL)
    out = a1.run_checks(rd)
    fixed = {"a_threshold_median", "a_threshold_p95", "feed_age"}   # registered bounds and the appendix sentence
    bad = out[~out["agrees"] | (out["id"].isin(fixed) & (out["matches_instruction"] == False))]  # noqa: E712
    assert bad.empty, bad.to_string()


def test_spot_feed_age_is_counted_and_named_in_the_appendix_sentence(res, tmp_path):
    """A47: the vol and forward limits say nothing about the spot feed; fills of the PM2 window with a spot price
    older than the spot heartbeat are counted, named in the sentence of Appendix A and kept (the first row lies
    before the window and does not count)."""
    hb = int(p2feeds.HEARTBEAT["spot"])
    data = _load(res)
    assert data["feed_age"]["spot_stale_fills"] == 0 and data["feed_age"]["spot_limit_s"] == hb
    sentence = a1.feed_sentence(data["feed_age"])
    assert sentence.startswith(a1.feed_prefix(data["feed_age"]))
    assert f"none uses a spot price older than the heartbeat of the spot feed ({hb} seconds)" in sentence
    _capital(spot=(5000.0, hb + 6.0, 20.0, 1161.0)).to_parquet(res.parent / "capital.parquet")
    data = _load(res)
    fa = data["feed_age"]
    assert fa["spot_stale_fills"] == 2 and fa["spot_age_max_s"] == 1161.0 and fa["holds"] is True
    assert (f"; 2 fills use a spot price older than the heartbeat of the spot feed ({hb} seconds) and stay in the "
            "sample.") in a1.feed_sentence(fa)
    a1.build(out_dir=tmp_path / "figures", results_dir=res, capital_path=res.parent / "capital.parquet")
    meta = pd.read_csv(res / "fig_a1_meta.csv").set_index("key")["value"]
    assert float(meta["spot_stale_fills"]) == 2 and float(meta["spot_limit_s"]) == hb
    out = a1.run_checks(res, with_expected=False)
    assert out["agrees"].all(), out.loc[~out["agrees"], ["id", "figure", "source", "error"]].to_string()


def test_caption_says_what_is_drawn_and_the_feed_ages_go_to_appendix_a():
    """C11: the caption says what is drawn and how to read it (FIGURE_SELECTION 6.8). The feed ages describe nothing
    drawn and stand in the text of Appendix A; the off-chain discount is said in Figure 1 and Section 2."""
    assert "feed older" not in a1.CAPTION and "heartbeat" not in a1.CAPTION
    assert "off-chain" not in a1.CAPTION and "discount" not in a1.CAPTION
    assert "\\PH" not in a1.CAPTION


def test_appendix_sentence_names_vol_and_forward_and_the_spot_count():
    """The limits are printed as numbers (reader audit, round 2: "the limits of the validation blocks" said none)."""
    assert a1.APPENDIX_SENTENCE.startswith(
        "In the PM2 window no fill uses a volatility feed older than \\PH{a1-vol-limit}~seconds or a forward feed "
        "older than \\PH{a1-fwd-limit}~seconds, the feed ages the validation allows")
    assert a1.APPENDIX_SENTENCE.endswith(a1.SPOT_CLAUSE.format(n="\\PH{a1-spot-stale}", hb="\\PH{a1-spot-heartbeat}"))
    fa = {"vol_limit_s": float(p2validate.MAX_VOL_AGE), "fwd_limit_s": float(p2validate.MAX_FWD_AGE)}
    assert a1.feed_prefix(fa) == ("In the PM2 window no fill uses a volatility feed older than 1\\,200~seconds or a "
                                  "forward feed older than 3\\,600~seconds, the feed ages the validation allows")


def _panel_b_bounds(fig):
    """The main axes of panel b and its two bound labels, keyed "median" and "p95" as the thresholds."""
    ax = next(a for a in fig.axes if a.get_ylabel() == "|relative deviation of K|")
    labels = {t.get_text().split()[0].lower(): t for t in ax.texts if "bound" in t.get_text()}
    return ax, labels


def _panel_a(fig):
    """The main axes of panel a (the log axis right of the strip of exact zeros)."""
    return next(a for a in fig.axes if a.get_xlabel().startswith("|relative deviation of K|, replica"))


def test_bound_labels_and_key_write_p95_as_figure_8_does(res):
    """F9 against F8: the 95th percentile is "P95" in the bound labels of both panels and in the key of panel a."""
    data = _load(res)
    fig = a1.draw(data)
    try:
        txt = [t.get_text() for t in kit.texts(fig)]
        assert txt.count(f"P95 bound 1{kit.THIN}%") == 2 and txt.count(f"median bound 0.1{kit.THIN}%") == 2
        assert not [t for t in txt if "p95" in t]
        key = _panel_a(fig).get_legend()
        assert [t.get_text() for t in key.get_texts()] == ["median", "P95"]
    finally:
        matplotlib.pyplot.close(fig)
    tab = a1.tables(data)
    for name in ("fig_a1_a.csv", "fig_a1_b.csv"):
        thr = tab[name][tab[name]["item"] == "threshold"]
        assert set(thr["printed"]) == {f"P95 bound 1{kit.THIN}%", f"median bound 0.1{kit.THIN}%"}
    assert "thin ticks its 95th percentile (P95)" in a1.CAPTION and "p95" not in a1.CAPTION


def test_count_column_is_headed_once_by_a_grey_n(res):
    """F9 as F3 to F6: one grey "n" heads the counts, which print bare and right-aligned, one per row."""
    data = _load(res)
    fig = a1.draw(data)
    try:
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        ax = _panel_a(fig)
        stats = data["stats"][data["stats"]["is_initial"]].sort_values("row")
        # the counts are the grey numbers right of the axis (the tick labels of the log axis are texts, too)
        x_axis = ax.get_window_extent(r).x1
        counts = [t for t in ax.texts if t.get_text().isdigit() and t.get_window_extent(r).x0 > x_axis]
        assert [t.get_text() for t in sorted(counts, key=lambda t: -t.get_window_extent(r).y0)] == \
            [str(int(n)) for n in stats["n"]]
        assert not [t.get_text() for t in kit.texts(fig) if t.get_text().startswith("n ")]
        head = [t for t in ax.texts if t.get_text() == "n"]
        assert len(head) == 1 and head[0].get_color() == kit.GREY and all(t.get_color() == kit.GREY for t in counts)
        rights = {round(t.get_window_extent(r).x1, 1) for t in counts + head}
        assert max(rights) - min(rights) < 0.5                                  # one right edge for the column
        assert head[0].get_window_extent(r).y0 > max(t.get_window_extent(r).y1 for t in counts)   # above the rows
        assert head[0].get_window_extent(r).x0 > x_axis                          # right of the axis
        assert kit.overlapping_texts(fig) == []
    finally:
        matplotlib.pyplot.close(fig)
    a = a1.tables(data)["fig_a1_a.csv"]
    n = a[a["item"] == "n"]
    assert (n["printed"] == n["value"].astype(int).astype(str)).all()


def test_bound_labels_of_panel_b_sit_on_their_own_lines(res):
    """F9: the two bounds are one decade apart; each label sits on its own line (centred on it, breaking it) and
    reaches neither the other line nor the text block below."""
    data = _load(res)
    fig = a1.draw(data)
    try:
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        ax, labels = _panel_b_bounds(fig)
        assert set(labels) == {"median", "p95"}
        y = {k: ax.transData.transform((1.0, data["thresholds"][k]))[1] for k in labels}
        for k, t in labels.items():
            e = t.get_window_extent(r)
            other = y["p95" if k == "median" else "median"]
            assert e.y0 < y[k] < e.y1, k
            assert not e.y0 <= other <= e.y1, k
            assert t.get_bbox_patch() is not None and t.get_bbox_patch().get_facecolor()[:3] == (1.0, 1.0, 1.0)
    finally:
        matplotlib.pyplot.close(fig)


def test_log_axes_are_labelled_as_powers_of_ten_with_no_type_under_7pt(res):
    """F8/T8: both log axes read 10^e as the caption and the appendix do, not '1e-11'; base and exponent are
    separate texts of 7 pt (mathtext would set the exponent at 4.9 pt)."""
    fig = a1.draw(_load(res))
    try:
        txt = [t.get_text() for t in kit.texts(fig)]
        assert not [s for s in txt if "1e" in s or "$" in s]
        assert txt.count("≤10") == 2 and txt.count(f"{kit.MINUS}13") == 2
        for e in (1, 3, 5, 7, 9, 11):
            assert txt.count(f"{kit.MINUS}{e}") == 2, e
        assert kit.small_texts(fig) == []
    finally:
        matplotlib.pyplot.close(fig)


def test_power_ticks_raise_the_exponent_and_keep_the_axis_label_clear():
    fig = kit.new_figure(3.0, 2.0)
    try:
        ax = kit.axes_at(fig, 0.6, 0.2, 2.2, 1.3)
        ax.set_xscale("log")
        ax.set_xlim(1e-9, 1e-1)
        ax.set_xticks([1e-9, 1e-5, 1e-1])
        ax.set_xlabel("x")
        out = kit.power_ticks(ax, "x", [1e-9, 1e-5, 1e-1], prefix={1e-9: "≤"})
        assert [t.get_text() for t in out] == ["≤10", f"{kit.MINUS}9", "10", f"{kit.MINUS}5", "10", f"{kit.MINUS}1"]
        assert kit.power_parts(1e3) == ("10", "3")
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        assert not any(t.get_visible() and t.get_text() for t in ax.get_xticklabels())
        for base, exp in zip(out[::2], out[1::2]):
            b, e = base.get_window_extent(r), exp.get_window_extent(r)
            assert e.x0 >= b.x1 - 0.5 and e.y0 > b.y0 + 0.3 * kit.FS_MIN * fig.dpi / 72.0
            assert base.get_fontsize() == exp.get_fontsize() == kit.FS_MIN
        label = ax.xaxis.label.get_window_extent(r)
        assert label.y1 < min(t.get_window_extent(r).y0 for t in out)
        assert kit.overlapping_texts(fig) == []
    finally:
        matplotlib.pyplot.close(fig)
