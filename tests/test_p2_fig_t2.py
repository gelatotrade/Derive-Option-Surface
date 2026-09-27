"""T2: what get_margin returns, and how PM2 prices a book (FIGURE_SELECTION section 7, T2)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from derive_surface import margin_pm2, margin_sm  # noqa: E402
from derive_surface.figs_p2 import _kit_t2a1 as kit  # noqa: E402
from derive_surface.figs_p2 import t2  # noqa: E402
from derive_surface.p2params import Timeline  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
REAL = REPO / "results" / "p2"


def _faktoren() -> pd.DataFrame:
    rows = []
    hist17 = "historisch 17.09. 10:45:13Z Blk 44810149"
    hist24 = "historisch 24.09. 09:24:59Z Blk 45110142 (H1_liste)"
    for messung, buch, fall, sm_r, pm2_r, v_sm, v_pm2 in [
            (hist17, "b17_exakt", "A", 500_000.0, 150_000.0, -100_000.0, -99_000.0),
            (hist17, "b17_exakt", "B", 190_000.0, 18_000.0, 1_800.0, 1_700.0),
            (hist17, "b17_exakt", "C", 250_000.0, 80_000.0, -50_000.0, -49_000.0),
            (hist24, "b24", "A", 640_000.0, 180_000.0, -830_000.0, -829_000.0),
            (hist24, "b24", "B", 210_000.0, 100_000.0, -500_000.0, -499_500.0),
            ("historisch 24.09. 09:24:59Z Blk 45110142 (H0_heutige_Liste)", "b24", "B", 1.0, 1.0, -1.0, -1.0),
            ("live live_result.json Blk 45114232", "b17_heute", "A", 1.0, 1.0, -1.0, -1.0)]:
        sm_c, pm2_c = sm_r - v_sm, pm2_r - v_pm2
        rows.append({"messung": messung, "buch": buch, "fall": fall, "SM_Cnet": sm_c, "PM2_Cnet": pm2_c,
                     "F_Cnet": round(sm_c / pm2_c, 2), "SM_R_ticker": np.nan, "PM2_R_ticker": np.nan,
                     "F_R_ticker": np.nan, "SM_R_engine": sm_r, "PM2_R_engine": pm2_r,
                     "F_R_engine": round(sm_r / pm2_r, 2), "V_und_SM": v_sm, "V_PM2": v_pm2})
    return pd.DataFrame(rows)


def _reference_row(params_pm2, params_sm, ts=t2.REF_TS) -> dict:
    """A synthetic reference straddle whose K_pm2 and K_sm come from the engines (as p2surface writes them)."""
    spot, fwd, sigma, rate = 100_000.0, 100_400.0, 0.45, 0.03
    expiry = ts + 22 * 86_400
    c, p = (float(v) for v in margin_sm.b76_prices(fwd, fwd, sigma, expiry - ts))
    row = {"ccy": "BTC", "day": "2026-09-17", "ts": ts, "expiry": expiry, "tenor_days": 22.0, "spot": spot,
           "forward": fwd, "strike": fwd, "sigma": sigma, "rate": rate, "rate_pm": 0.0, "price_call": c,
           "price_put": p, "spot_age": 30.0, "fwd_age": 60.0, "vol_age": 60.0}
    book, state, vols = t2.straddle_inputs(pd.Series(row))
    for mgr, eng, prm in (("pm2", margin_pm2, params_pm2), ("sm", margin_sm, params_sm)):
        net, _ = eng.net_margin(book, state, prm, True, vols=vols)
        row[f"K_{mgr}"] = -(c + p) - net
    row["K_pm"] = np.nan
    return row


@pytest.fixture(scope="module")
def real_params():
    return {m: Timeline("BTC", m, root=REAL / "params").entry_at(t2.REF_TS) for m in ("pm2", "sm")}


@pytest.fixture
def res(tmp_path, real_params):
    rd = tmp_path / "results"
    (rd / "semantics").mkdir(parents=True)
    (rd / "params").mkdir()
    _faktoren().to_csv(rd / "semantics" / "faktoren.csv", index=False)
    for m, entry in real_params.items():
        (rd / "params" / f"BTC_{m}.json").write_text(json.dumps([entry]))
    row = _reference_row(real_params["pm2"]["params"], real_params["sm"]["params"])
    early = dict(row, day="2026-09-16", ts=row["ts"] - 86_400)
    pd.DataFrame([early, row]).to_csv(rd / "reference_book.csv", index=False)
    return rd


def test_probe_rows_are_the_four_historical_books_in_drawing_order():
    rows = t2.probe_rows(_faktoren())
    assert list(rows["label"]) == ["17 Sep, mixed", "24 Sep, mixed", "17 Sep, short", "24 Sep, short"]
    assert list(rows["block"]) == [44810149, 45110142, 44810149, 45110142]


def test_probe_rows_refuse_anything_but_four_rows():
    f = _faktoren()
    extra = f.iloc[[4]].assign(messung="historisch 24.09. 09:24:59Z Blk 45110142 (second list)")
    with pytest.raises(ValueError, match="four"):
        t2.probe_rows(pd.concat([f, extra]))


def test_scenarios_reproduce_the_engine(res, real_params):
    row = pd.read_csv(res / "reference_book.csv").iloc[-1]
    book, state, vols = t2.straddle_inputs(row)
    sc = t2.pm2_scenarios(book, state, real_params["pm2"]["params"], vols=vols)
    d = margin_pm2.margin_details(book, state, real_params["pm2"]["params"], True, vols=vols)
    assert np.allclose(sc["pnl_usdc"].to_numpy(), d["scenario_pnl"])
    assert int(sc.loc[sc["binding"], "scenario"].iloc[0]) == int(np.argmin(d["scenario_pnl"]))
    assert sc["binding"].sum() == 1
    core = sc[(sc["dampening"] == 1.0) & ~sc["is_skew"]]
    assert np.isclose(core["spot_shock"].max() - 1.0, 0.14) and np.isclose(1.0 - core["spot_shock"].min(), 0.14)
    assert sc.loc[~sc["is_skew"], "spot_shock"].nunique() == 17


def test_load_refuses_a_reference_row_the_engine_does_not_reproduce(res):
    rb = pd.read_csv(res / "reference_book.csv")
    rb.loc[rb.index[-1], "K_pm2"] *= 1.001
    rb.to_csv(res / "reference_book.csv", index=False)
    with pytest.raises(ValueError, match="reproduce"):
        t2.load(res)


def test_legs_come_from_the_reference_book_when_it_carries_them(res):
    base = t2.load(res)
    rb = pd.read_csv(res / "reference_book.csv")
    rb["K_pm2_call"] = base["K_pm2_call"]
    rb["K_pm2_put"] = base["K_pm2_put"]
    rb.to_csv(res / "reference_book.csv", index=False)
    data = t2.load(res)
    assert data["legs_source"] == "reference_book.csv"
    assert np.isclose(data["K_pm2_legs"], base["K_pm2_call"] + base["K_pm2_put"])
    assert base["legs_source"] == "recomputed on the reference row"


def test_build_writes_figure_and_tables(res, tmp_path):
    out = tmp_path / "figures"
    paths = t2.build(out_dir=out, results_dir=res)
    names = {p.name for p in paths}
    assert {"t2.pdf", "t2.png", "fig_t2_a.csv", "fig_t2_b.csv", "fig_t2_c.csv"} <= names
    w, h = kit.pdf_size_inches(out / "t2.pdf")
    assert abs(w - 6.84) <= 0.005 and abs(h - 2.6) <= 0.02
    c = pd.read_csv(res / "fig_t2_c.csv")
    scen = c[c["kind"] == "scenario"]
    assert scen["binding"].sum() == 1
    assert not scen.loc[scen["is_skew"], "drawn"].any()
    assert set(c.loc[c["kind"] == "capital", "item"]) >= {"K_pm2_book", "K_pm2_legs", "K_sm"}
    a = pd.read_csv(res / "fig_t2_a.csv")
    assert {"R 210", "R 100", "710", "600"} <= set(a["printed"].dropna())
    b = pd.read_csv(res / "fig_t2_b.csv")
    assert len(b) == 4 and list(b["label"]) == ["17 Sep, mixed", "24 Sep, mixed", "17 Sep, short", "24 Sep, short"]


def test_figure_type_size_and_canvas(res):
    fig = t2.draw(t2.load(res))
    assert tuple(np.round(fig.get_size_inches(), 3)) == (7.0, 2.6)
    assert kit.small_texts(fig) == []
    assert kit.texts_off_canvas(fig) == []
    assert kit.overlapping_texts(fig) == []


def test_checks_agree_on_synthetic_data(res, tmp_path):
    t2.build(out_dir=tmp_path / "figures", results_dir=res)
    out = t2.run_checks(res, with_expected=False)
    assert len(out) == len(t2.CHECKS)
    assert out["agrees"].all(), out.loc[~out["agrees"], ["id", "figure", "source", "error"]].to_string()


def test_caption_has_no_dashes():
    assert "—" not in t2.CAPTION and "–" not in t2.CAPTION


@pytest.mark.skipif(not (REAL / "semantics" / "faktoren.csv").exists() or not (REAL / "reference_book.csv").exists(),
                    reason="real results not present")
def test_real_data_meets_the_build_instruction(tmp_path):
    rd = tmp_path / "results"
    (rd / "semantics").mkdir(parents=True)
    shutil.copy(REAL / "semantics" / "faktoren.csv", rd / "semantics" / "faktoren.csv")
    shutil.copy(REAL / "reference_book.csv", rd / "reference_book.csv")
    shutil.copytree(REAL / "params", rd / "params")
    t2.build(out_dir=tmp_path / "figures", results_dir=rd)
    out = t2.run_checks(rd)
    bad = out[~out["agrees"] | (out["matches_instruction"] == False)]  # noqa: E712
    assert bad.empty, bad.to_string()


def test_panel_c_says_the_shock_axis_is_not_to_scale():
    """A53: the 17 spot shocks sit at equal steps (0.34, 0.67, 0.86, then 0.035 apart, then up to 6); axis and
    caption say so."""
    assert "not to scale" in t2.XLABEL_C and t2.XLABEL_C.startswith("spot shock")
    assert "spot shocks in order, not to scale" in t2.CAPTION


def test_single_legs_under_sm_are_in_the_table_for_card_2(res, tmp_path, real_params):
    """Section 10: card 2 sets one short call against the short straddle under PM2 and SM, from the same reference
    row; T2 computes the SM legs with the same engine and state (not drawn in T2)."""
    t2.build(out_dir=tmp_path / "figures", results_dir=res)
    c = pd.read_csv(res / "fig_t2_c.csv").set_index("item")
    for item in ("K_sm_call", "K_sm_put", "K_pm2_call", "K_pm2_put"):
        assert c.loc[item, "kind"] == "capital" and not bool(c.loc[item, "drawn"])
        assert np.isfinite(c.loc[item, "value_usdc"]) and c.loc[item, "value_usdc"] > 0
    row = pd.read_csv(res / "reference_book.csv").iloc[-1]
    book, state, vols = t2.straddle_inputs(row)
    call = [leg for leg in book.options if leg.is_call][0]
    net, _ = margin_sm.net_margin(t2.Book(options=[call]), state, real_params["sm"]["params"], True, vols=vols)
    assert c.loc["K_sm_call", "value_usdc"] == pytest.approx(-float(row["price_call"]) - net, rel=1e-12)
