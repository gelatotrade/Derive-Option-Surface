"""F1 (what one contract costs): smoke test on synthetic mini data, type size, canvas size, tables and checks."""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.text  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from derive_surface.figs_p2 import f1  # noqa: E402
from derive_surface.markouts import DELTA_LABELS, TENOR_LABELS  # noqa: E402

CCYS = ("BTC", "ETH", "HYPE")
SIDES = ("sell", "buy")
PRICE = {"BTC": 80_000.0, "ETH": 3_000.0, "HYPE": 40.0}
REGIMES = ("R1", "R2", "R3", "R4")


def synth(results_dir: Path, seed: int = 0, regimes: bool = True) -> None:
    """fig_edge_maps.csv (pm2, sm_pm2win, pm_pm2win), h1_cells.csv and fig_f1_regimes.csv that agree with each other."""
    rng = np.random.default_rng(seed)
    reg_rows = []
    for ccy in CCYS:
        for side in SIDES:
            for i, d in enumerate(DELTA_LABELS):
                for j, t in enumerate(TENOR_LABELS):
                    fills = int(rng.choice([8, 60, 150, 260, 900, 3000], p=[0.05, 0.05, 0.1, 0.2, 0.3, 0.3]))
                    split = rng.multinomial(fills, [0.3, 0.3, 0.25, 0.15])
                    kappa = (8 + 2 * i + 12 * (ccy == "HYPE")) if side == "sell" else 0.07 * 1.8 ** (i + 0.6 * j)
                    for k, r in enumerate(REGIMES):
                        n = int(split[k])
                        contracts = n * rng.uniform(0.5, 3.0)
                        idx = contracts * PRICE[ccy]
                        k_pm2 = kappa / 100 * idx
                        q_sm = (rng.lognormal(-0.05, 0.12) if side == "sell" else rng.uniform(1.0, 1.2)) * (
                            1.35 if r == "R4" else 1.0)
                        reg_rows.append({"regime": r, "ccy": ccy, "side": side, "delta_bucket": d, "tenor_bucket": t,
                                         "cell": f"{ccy}|{side}|{d}|{t}", "fills": n, "contracts": contracts,
                                         "sum_K_sm_a": k_pm2 * q_sm,
                                         "sum_K_pm_a": k_pm2 * rng.uniform(1.2, 1.5) if ccy != "HYPE" else np.nan,
                                         "pm_fills": n if ccy != "HYPE" else 0,
                                         "sum_K_pm2_a": k_pm2, "sum_index_a": idx,
                                         "edge": rng.normal(0.5, 3.0) * 1e-4 * idx})
    reg = pd.DataFrame(reg_rows)
    reg["occupied"] = reg["fills"] >= 200
    keys = ["cell", "ccy", "side", "delta_bucket", "tenor_bucket"]
    pooled = reg.groupby(keys, sort=False).agg(
        fills=("fills", "sum"), contracts=("contracts", "sum"), sum_K_sm_a=("sum_K_sm_a", "sum"),
        sum_K_pm_a=("sum_K_pm_a", lambda s: s.sum(min_count=1)), sum_K_pm2_a=("sum_K_pm2_a", "sum"),
        sum_index_a=("sum_index_a", "sum"), edge=("edge", "sum")).reset_index()
    maps = []
    for name, col in (("pm2", "sum_K_pm2_a"), ("sm_pm2win", "sum_K_sm_a"), ("pm_pm2win", "sum_K_pm_a")):
        m = pooled.copy()
        if name == "pm_pm2win":
            m = m[m["ccy"] != "HYPE"].copy()
        m.insert(0, "map", name)
        m["fills_k_le_0"] = 0
        m["sum_edge"] = m["edge"]
        m["sum_index"] = m["sum_index_a"]
        m["sum_K"] = m[col]
        m["sum_den"] = m[col]
        m["scale"] = 1.0
        m["occupied"] = m["fills"] >= 200
        m["A_bp"] = 1e4 * m["sum_edge"] / m["sum_index"]
        m["B_bp"] = 1e4 * m["sum_edge"] / m["sum_K"]
        occ = m["occupied"]
        m["rank_A"] = m["A_bp"].where(occ).rank(ascending=False)
        m["rank_B"] = m["B_bp"].where(occ).rank(ascending=False)
        m["rank_shift"] = m["rank_B"] - m["rank_A"]
        for c in ("A", "B"):
            m[f"{c}_lo"] = m[f"{c}_bp"] - 1
            m[f"{c}_hi"] = m[f"{c}_bp"] + 1
            m[f"rank_{c}_lo"] = (m[f"rank_{c}"] - 5).clip(lower=1)
            m[f"rank_{c}_hi"] = m[f"rank_{c}"] + 5
        maps.append(m.drop(columns=["sum_K_sm_a", "sum_K_pm_a", "sum_K_pm2_a", "sum_index_a", "edge"]))
    maps = pd.concat(maps, ignore_index=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    maps.to_csv(results_dir / "fig_edge_maps.csv", index=False)
    h1 = maps[maps["map"] == "pm2"].drop(columns=["map"]).assign(window="pm2", capital="K_pm2")
    h1.to_csv(results_dir / "h1_cells.csv", index=False)
    if regimes:
        reg.drop(columns=["edge"]).to_csv(results_dir / "fig_f1_regimes.csv", index=False)
    # the three PM2 events that bound the regimes, and a smaller one that does not (under 3 log-% in the book)
    ev = [(1767912649, 1767912649), *[(b, b) for b in f1.REGIME_BOUNDS]]
    pd.DataFrame([{"ccy": c, "manager": "pm2", "event_ts": ts, "last_ts": last} for c in ("BTC", "ETH")
                  for ts, last in ev]).to_csv(results_dir / "events.csv", index=False)
    book = []
    for c in ("BTC", "ETH"):
        prev, k = 1749467000, 1000.0
        for ts, jump in zip([e[0] for e in ev], (1.6, -10.5, -7.8, -26.0)):
            book.append({"ccy": c, "pm2_param_ts": ts, "pm2_param_ts_prev": prev, "K_pm2": k * np.exp(jump / 100),
                         "K_pm2_prev": k})
            prev, k = ts, k * np.exp(jump / 100)
    pd.DataFrame(book).to_csv(results_dir / "reference_book.csv", index=False)


def texts(fig):
    fig.canvas.draw()
    return [t for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text().strip()]


def pdf_size_in(path: Path):
    m = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", path.read_bytes())
    return float(m.group(1)) / 72.0, float(m.group(2)) / 72.0


@pytest.fixture()
def rd(tmp_path):
    d = tmp_path / "results"
    synth(d)
    return d


def test_fmt_two_significant_digits():
    assert [f1.fmt_sig2(v) for v in (0.0744, 0.123, 9.94, 9.96, 13.2, 38.73, 1.0, 0.46)] == [
        "0.07", "0.12", "9.9", "10", "13", "39", "1.0", "0.46"]


def test_regimes_from_fills_split_at_the_event_second():
    b1, b2, b3 = f1.REGIME_BOUNDS
    ts = np.array([b1 - 1, b1, b2 - 1, b2, b3 - 1, b3, b3 + 10]) * 1000
    cap = pd.DataFrame({"trade_id": [f"t{i}" for i in range(7)], "currency": "BTC", "ts": ts,
                        "maker_side": [-1, -1, 1, 1, -1, -1, -1], "amount": 2.0, "index_price": 100.0,
                        "K_sm": 3.0, "K_pm": [4.0, np.nan, 4.0, 4.0, 4.0, 4.0, 4.0], "K_pm2": 2.0})
    cap.loc[6, "K_pm2"] = np.nan                       # outside the PM2 window: dropped
    mk = pd.DataFrame({"trade_id": cap["trade_id"], "delta_bucket": "40-60", "tenor_bucket": "7-30d",
                       "index_price": 100.0, "amount": 2.0})
    reg = f1.cell_capital_by_regime(cap, mk)
    got = reg.groupby("regime")["fills"].sum().to_dict()
    assert got == {"R1": 1, "R2": 2, "R3": 2, "R4": 1}
    assert reg["sum_K_pm2_a"].sum() == pytest.approx(6 * 4.0)
    assert reg["sum_index_a"].sum() == pytest.approx(6 * 200.0)
    r2 = reg[(reg["regime"] == "R2")]
    assert set(r2["side"]) == {"sell", "buy"}
    assert reg.loc[reg["regime"] == "R1", "sum_K_pm_a"].iloc[0] == pytest.approx(8.0)
    assert np.isnan(reg.loc[(reg["regime"] == "R2") & (reg["side"] == "sell"), "sum_K_pm_a"].iloc[0])


def test_regime_sums_must_match_the_map(rd):
    reg = pd.read_csv(rd / "fig_f1_regimes.csv")
    maps = pd.read_csv(rd / "fig_edge_maps.csv")
    f1.check_regimes_against_maps(reg, maps)                  # consistent: no error
    bad = reg.copy()
    bad.loc[0, "sum_K_pm2_a"] *= 1.001
    with pytest.raises(ValueError):
        f1.check_regimes_against_maps(bad, maps)


def test_smoke_build_writes_figures_and_tables(rd, tmp_path):
    out = tmp_path / "fig"
    paths = f1.build(out_dir=out, results_dir=rd)
    names = sorted(p.name for p in paths)
    assert {"f1.pdf", "f1.png", "fig_f1_a.csv", "fig_f1_b.csv"} <= set(names)
    w, h = pdf_size_in(out / "f1.pdf")
    assert w == pytest.approx(7.0, abs=0.02) and h == pytest.approx(3.9, abs=0.02)
    a = pd.read_csv(rd / "fig_f1_a.csv", keep_default_na=False)
    assert len(a) == 210
    assert (a.loc[a["occupied"].astype(str) == "False", "printed"] == "×").all()
    b = pd.read_csv(rd / "fig_f1_b.csv")
    assert set(b["regime"]) == {"pooled", "R4"}
    assert (b["jitter"].abs() <= 0.18 + 1e-12).all()
    maps = pd.read_csv(rd / "fig_edge_maps.csv")
    occ = maps[(maps["map"] == "pm2") & maps["occupied"]]
    assert ((b["manager"] == "sm") & (b["regime"] == "pooled")).sum() == len(occ)
    assert (b["manager"] == "pm").sum() == int((occ["ccy"] != "HYPE").sum())


def test_type_size_canvas_and_extent(rd):
    fig, _ = f1.make_figure(rd)
    w, h = fig.get_size_inches()
    assert (w, h) == pytest.approx((7.0, 3.9))
    r = fig.canvas.get_renderer()
    canvas = fig.bbox
    for t in texts(fig):
        assert t.get_fontsize() >= f1.FS_MIN - 1e-9, t.get_text()
        e = t.get_window_extent(r)
        assert e.x0 >= canvas.x0 - 1 and e.x1 <= canvas.x1 + 1, t.get_text()
        assert e.y0 >= canvas.y0 - 1 and e.y1 <= canvas.y1 + 1, t.get_text()
    for ax in fig.axes:
        e = ax.get_tightbbox(r)
        assert e.x0 >= canvas.x0 - 1 and e.x1 <= canvas.x1 + 1
        assert e.y0 >= canvas.y0 - 1 and e.y1 <= canvas.y1 + 1
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_without_regimes_the_hollow_rows_drop(tmp_path):
    d = tmp_path / "r"
    synth(d, regimes=False)
    fig, tables = f1.make_figure(d)
    assert set(tables["b"]["regime"]) == {"pooled"}
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_checks_pass_on_consistent_data(rd, tmp_path):
    f1.build(out_dir=tmp_path / "fig", results_dir=rd)
    res = f1.run_checks(rd)
    assert len(res) == len(f1.CHECKS) >= 8
    assert res["ok"].all(), res[~res["ok"]].to_string()


def test_caption_is_english_without_dashes():
    assert "—" not in f1.CAPTION and "–" not in f1.CAPTION
    assert f1.CAPTION.startswith("What one contract costs.")
