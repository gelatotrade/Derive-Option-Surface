"""T1 (the engine's view of the surface): smoke test on synthetic mini data, binding rules, layout rules."""
from __future__ import annotations

import json
import re

import matplotlib

matplotlib.use("Agg")

import matplotlib.text  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from scipy.stats import norm  # noqa: E402

from derive_surface import margin_pm2, margin_sm, p2surface  # noqa: E402
from derive_surface.figs_p2 import t1  # noqa: E402
from derive_surface.p2types import YEAR  # noqa: E402

TS = t1.TS
DAY = 86_400


# ---------------------------------------------------------------------------------------------- synthetic inputs

def pm2_params(width: float = 0.14) -> dict:
    """PM2 parameters in the A2 schema with a core grid of +-width, dampened tails and two skew scenarios."""
    step = width / 4.0
    core = []
    for s in np.round(1.0 + step * np.arange(4, -5, -1), 6):
        dirs = [1] if abs(abs(s - 1.0) - width) < 1e-9 else [1, 0, 2]
        core += [{"spotShock": float(s), "volShock": d, "dampeningFactor": 1.0} for d in dirs]
    tails = [(0.34, 0.12), (0.67, 0.245), (1.5, 0.16), (2.0, 0.08), (3.0, 0.02)]
    return {
        "BasisContingencyParameters": {"basisContAddFactor": 0.5, "basisContMultFactor": 2.0,
                                       "scenarioSpotDown": 0.965, "scenarioSpotUp": 1.035},
        "MarginParameters": {"imFactor": 1.0, "longBaseStaticDiscount": 0.98, "longRateAddScale": 0.1,
                             "longRateMultScale": 0.0, "mmFactor": 0.8, "shortBaseStaticDiscount": 1.02,
                             "shortRateAddScale": 0.1, "shortRateMultScale": 0.0},
        "OtherContingencyParameters": {"IMOptionPercent": 0.001, "IMPerpPercent": 0.0075, "MMOptionPercent": 0.0015,
                                       "MMPerpPercent": 0.0075, "confMargin": 0.4, "confThreshold": 0.55,
                                       "pegLossFactor": 4.0, "pegLossThreshold": 0.99},
        "SkewShockParameters": {"absBaseCap": 0.25, "absCBase": -0.1, "linearBaseCap": 0.25, "linearCBase": -0.1,
                                "minKStar": 0.01, "volParamScale": 0.0, "volParamStatic": 0.6, "widthScale": 4.0},
        "VolShockParameters": {"dteFloor": 86400.0, "longTermPower": 0.13, "minVolUpShock": 0.5,
                               "shortTermPower": 0.3, "volRangeDown": 0.25, "volRangeUp": 0.4},
        "scenarios": core + [{"spotShock": s, "volShock": 1, "dampeningFactor": d} for s, d in tails]
        + [{"spotShock": 1.0, "volShock": 3, "dampeningFactor": 1.0},
           {"spotShock": 1.0, "volShock": 4, "dampeningFactor": 1.0}],
        "maxExpiries": 16,
    }


def sm_params(**option) -> dict:
    om = {"MMPutMtMReq": 0.09, "maxSpotReq": 0.15, "minSpotReq": 0.13, "mmCallSpotReq": 0.09,
          "mmOffsetScale": 1.05, "mmPutSpotReq": 0.09, "unpairedIMScale": 1.2, "unpairedMMScale": 1.1}
    om.update(option)
    return {"BaseMarginParams": {"IMScale": 0.93, "marginFactor": 0.75},
            "DepegParams": {"depegFactor": 2.0, "threshold": 0.99},
            "OptionMarginParams": om,
            "OracleContingencyParams": {"OCFactor": 1.0, "baseThreshold": 0.55, "optionThreshold": 0.55,
                                        "perpThreshold": 0.55},
            "PerpMarginRequirements": {"imPerpReq": 0.066, "mmPerpReq": 0.05}}


def _entry(ts: int, params: dict, changed) -> dict:
    return {"from_block": 1000 + ts // 2, "from_ts": int(ts), "from_utc": "", "source": "synthetic",
            "changed": changed, "params": params}


def nodes(deltas=None, days=None) -> pd.DataFrame:
    """Engine inputs on a small call-delta x tenor grid (OTM option per node, strike from the call delta)."""
    deltas = np.linspace(0.05, 0.95, 7) if deltas is None else np.asarray(deltas, float)
    days = np.array([1.0, 7.0, 30.439163, 90.0, 365.0]) if days is None else np.asarray(days, float)
    F, S = 76_000.0, 76_050.0
    rows = []
    for d in days:
        tau = d / 365.0
        for x in deltas:
            iv = 0.30 + 0.25 * (x - 0.5) ** 2 + 0.08 / np.sqrt(d)
            K = F * np.exp(-iv * np.sqrt(tau) * norm.ppf(x) + 0.5 * iv * iv * tau)
            rows.append({"delta": x, "tau": tau, "tenor_days": d, "forward": F, "strike": K, "iv": iv,
                         "k": np.log(K / F), "rate": 0.036, "rate_conf": 1.0, "vol_conf": 0.95, "fwd_conf": 1.0,
                         "is_call": K >= F, "spot": S, "spot_conf": 1.0})
    return pd.DataFrame(rows)


def grid_for(mgr: str, params: dict, base: pd.DataFrame) -> pd.DataFrame:
    """What ``p2surface.capital_grid`` returns for one short contract per node (same engine call)."""
    g = base.copy()
    q = -1.0
    net, mtm = p2surface.ENGINES[mgr].single(p2surface._engine_arrays(g, mgr, q, 0.0), params, True)
    call, put = margin_sm.b76_prices(g["forward"].to_numpy(), g["strike"].to_numpy(), g["iv"].to_numpy(),
                                     g["tau"].to_numpy() * YEAR)
    g["price"] = np.where(g["is_call"].to_numpy(bool), call, put)
    g["net"], g["mtm"] = net, mtm
    g["K"] = g["price"] * q - net
    g["K_per_forward_bp"] = 1e4 * g["K"] / g["forward"]
    g.insert(0, "manager", mgr)
    g.insert(1, "side", "short")
    g.insert(2, "ts", TS)
    return g


@pytest.fixture()
def results_dir(tmp_path):
    rd = tmp_path / "results"
    (rd / "params").mkdir(parents=True)
    pm2_old, pm2_new, sm = pm2_params(0.17), pm2_params(0.14), sm_params()
    (rd / "params" / "BTC_pm2.json").write_text(json.dumps([
        _entry(TS - 90 * DAY, pm2_old, None), _entry(TS - 28 * DAY, pm2_new, ["scenarios"]),
        _entry(TS - 10 * DAY, pm2_new, ["CollateralParameters"])]))
    (rd / "params" / "BTC_sm.json").write_text(json.dumps([_entry(TS - 400 * DAY, sm, None)]))
    base = nodes()
    grid = pd.concat([grid_for("pm2", pm2_new, base), grid_for("sm", sm, base)], ignore_index=True)
    grid.to_csv(rd / t1.GRID_FILE, index=False)
    expiries = [TS + int(d * DAY) for d in (1.0, 3.0, 8.0, 15.0, 22.0, 50.0, 99.0, 190.0)]
    (rd / t1.META_FILE).write_text(json.dumps({"ccy": "BTC", "ts": TS, "block": 45_000_000, "expiries": expiries}))
    return rd


# ---------------------------------------------------------------------------------------------- binding rules

@pytest.mark.parametrize("mgr", ["pm2", "sm"])
def test_decomposition_adds_up_to_the_grid_capital_at_every_node(results_dir, mgr):
    grid = pd.read_csv(results_dir / t1.GRID_FILE)
    g = grid[grid["manager"] == mgr].reset_index(drop=True)
    params = (pm2_params(0.14) if mgr == "pm2" else sm_params())
    r = t1.binding_rule(g, "BTC", TS, mgr, params=params)
    assert len(r) == len(g)
    parts = r[[c for c in r.columns if c.startswith("c_")]].sum(axis=1)
    rel = np.abs(parts - g["K"]) / np.abs(g["K"])
    assert rel.max() <= 1e-9
    assert r["rule"].notna().all() and (r["rule"] != "").all()
    assert set(r["rule_key"]) <= set(t1.CLASS_STYLE[mgr])


def test_binding_rule_refuses_a_grid_that_the_engine_does_not_reproduce(results_dir):
    grid = pd.read_csv(results_dir / t1.GRID_FILE)
    g = grid[grid["manager"] == "pm2"].reset_index(drop=True)
    g.loc[3, "K"] *= 1.001
    with pytest.raises(ValueError, match="decomposition"):
        t1.binding_rule(g, "BTC", TS, "pm2", params=pm2_params(0.14))


def test_pm2_classes_cover_every_class():
    P = margin_pm2._Params(pm2_params(0.14))
    shock, dirs, damp = P.shock, P.dirs, P.damp
    idx = {
        "up": int(np.flatnonzero(np.isclose(shock, 1.14) & (dirs == 1))[0]),
        "down": int(np.flatnonzero(np.isclose(shock, 0.86) & (dirs == 1))[0]),
        "core": int(np.flatnonzero(np.isclose(shock, 1.035) & (dirs == 2))[0]),
        "tail_up": int(np.flatnonzero(np.isclose(shock, 2.0))[0]),
        "tail_down": int(np.flatnonzero(np.isclose(shock, 0.34))[0]),
        "other": int(np.flatnonzero(dirs == 3)[0]),
    }
    j = np.array(list(idx.values()) + [0])
    scenario_binds = np.array([True] * len(idx) + [False])     # last one: the basis contingency binds
    keys = t1.pm2_class_keys(P, j, scenario_binds)
    assert list(keys) == list(idx) + ["other"]
    labels = t1.class_labels("pm2", P, j, keys)
    assert labels["up"] == "spot +14 %, vol up" and labels["down"] == "spot −14 %, vol up"
    assert labels["tail_up"] == "spot ×2 (dampened)" and labels["tail_down"] == "spot ×0.34 (dampened)"
    assert labels["core"] == "core, other vol" and labels["other"] == "basis/skew/other"


def test_pm2_grid_width_is_read_from_the_parameters():
    P = margin_pm2._Params(pm2_params(0.17))
    j = np.array([int(np.flatnonzero(np.isclose(P.shock, 1.17))[0])])
    keys = t1.pm2_class_keys(P, j, np.array([True]))
    assert keys[0] == "up" and t1.class_labels("pm2", P, j, keys)["up"] == "spot +17 %, vol up"


def test_sm_branches_cover_every_class():
    base = nodes(deltas=[0.05, 0.45, 0.95], days=[30.0])
    g = grid_for("sm", sm_params(), base)
    r = t1.binding_rule(g.reset_index(drop=True), "BTC", TS, "sm", params=sm_params())
    assert list(r["rule_key"]) == ["floor", "otm", "floor"]
    assert r.loc[1, "rule"] == "15 % − OTM" and r.loc[0, "rule"] == "13 % floor"
    strict = sm_params(mmPutSpotReq=0.2)     # the MM put branch binds once its spot charge exceeds the IM charge
    g2 = grid_for("sm", strict, base)
    r2 = t1.binding_rule(g2.reset_index(drop=True), "BTC", TS, "sm", params=strict)
    assert r2.loc[2, "rule_key"] == "mm_put" and r2.loc[2, "rule"] == "put: 1.05 × MM"


# ---------------------------------------------------------------------------------------------- build

def test_build_writes_tables_and_figures(tmp_path, results_dir):
    out = tmp_path / "figures"
    paths = t1.build(out_dir=out, results_dir=results_dir)
    names = {p.name for p in paths}
    assert {"t1.pdf", "t1.png", "fig_t1_ab.csv", "fig_t1_cd.csv", "fig_t1_meta.csv"} <= names
    assert all(p.exists() and p.stat().st_size > 0 for p in paths)
    ab = pd.read_csv(results_dir / "fig_t1_ab.csv")
    cd = pd.read_csv(results_dir / "fig_t1_cd.csv")
    for col in ("manager", "delta", "tenor_days", "iv", "strike", "forward", "K_usdc", "K_pct_forward", "printed"):
        assert col in ab.columns
    for col in ("manager", "delta", "tenor_days", "rule", "spot_shock", "vol_shock", "dampening", "K_pct_forward",
                "printed"):
        assert col in cd.columns
    assert len(ab) == len(cd) == 2 * 35
    meta = pd.read_csv(results_dir / "fig_t1_meta.csv")
    assert {"key", "manager", "value", "printed"} <= set(meta.columns)
    n_exp = meta.loc[meta["key"] == "n_expiries", "value"].iloc[0]
    assert n_exp == 8
    head = meta.loc[meta["key"] == "header", "printed"].iloc[0]
    assert head == ("BTC · 17 Sep 2026, 08:00 UTC · 8 live expiries · PM2 spot grid ±14 % since "
                    "20 Aug 2026 · chain semantics")
    classes = meta[meta["key"] == "n_class"]
    for mgr in ("pm2", "sm"):
        assert classes.loc[classes["manager"] == mgr, "value"].sum() == 35


def test_pdf_and_png_have_the_print_size(tmp_path, results_dir):
    out = tmp_path / "figures"
    t1.build(out_dir=out, results_dir=results_dir)
    pdf = (out / "t1.pdf").read_bytes()
    box = [float(v) for v in re.search(rb"/MediaBox\s*\[\s*([\d.\s]+)\]", pdf).group(1).split()]
    assert abs(box[2] / 72 - 6.84) <= 0.005 and abs(box[3] / 72 - 4.2) <= 0.02
    from PIL import Image

    with Image.open(out / "t1.png") as im:
        assert im.size == (2736, 1680)


def _extent(t, r):
    """Window extent of a text; a 3D text is measured where it is drawn (its projected position)."""
    from mpl_toolkits.mplot3d import art3d, proj3d

    if not isinstance(t, art3d.Text3D):
        return t.get_window_extent(r)
    x, y, _ = proj3d.proj_transform(t._x, t._y, t._z, t.axes.M)
    old = (t._x, t._y)
    t._x, t._y = x, y
    try:
        return matplotlib.text.Text.get_window_extent(t, r)
    finally:
        t._x, t._y = old


def test_figure_size_fonts_and_canvas(results_dir):
    data = t1.load(results_dir)
    tables = t1.tables(data)
    fig = t1.draw(data, tables)
    try:
        assert tuple(np.round(fig.get_size_inches(), 3)) == (7.0, 4.2)
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        W, H = fig.bbox.width, fig.bbox.height
        texts = [t for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text().strip()]
        assert texts
        small = [(t.get_text(), t.get_fontsize()) for t in texts if t.get_fontsize() < t1.FS_MIN - 1e-9]
        assert not small
        for t in texts:
            e = _extent(t, r)
            if e.width <= 0:
                continue
            assert e.x0 >= -0.5 and e.y0 >= -0.5 and e.x1 <= W + 0.5 and e.y1 <= H + 0.5, t.get_text()
        for ax in fig.axes:
            e = ax.get_window_extent(r)
            assert e.x0 >= -0.5 and e.y0 >= -0.5 and e.x1 <= W + 0.5 and e.y1 <= H + 0.5, ax
        n3d = sum(getattr(ax, "name", "") == "3d" for ax in fig.axes)
        assert n3d == 2
    finally:
        matplotlib.pyplot.close(fig)


def test_checks_agree_with_the_sources(results_dir, tmp_path):
    t1.build(out_dir=tmp_path / "figures", results_dir=results_dir)
    res = t1.run_checks(results_dir)
    assert len(res) == len(t1.CHECKS)
    assert res["agrees_source"].all(), res.loc[~res["agrees_source"]].to_dict("records")


def test_caption_and_checks_follow_the_rules():
    assert "—" not in t1.CAPTION and "–" not in t1.CAPTION
    assert t1.CAPTION.startswith("The surface as the engine sees it.")
    ids = [c["id"] for c in t1.CHECKS]
    assert len(ids) == len(set(ids))
    for c in t1.CHECKS:
        assert {"id", "what", "figure", "source", "expected", "tol"} <= set(c)
        assert c["figure"][0].startswith("fig_t1")
        assert not str(c["source"][0]).startswith("fig_t1")      # never the figure's own table
    expected = {c["id"]: c["expected"] for c in t1.CHECKS}
    assert expected["n_nodes_pm2"] == 740 and expected["n_expiries"] == 15
    assert expected["atm_pm2"] == pytest.approx(11.826) and expected["atm_sm"] == pytest.approx(14.080)


def test_a_short_iso_line_that_clabel_skips_gets_its_label_inside_the_panel():
    """A54: in panel c the 4 % line is a short piece at the upper right edge that ``clabel`` leaves out; it gets a
    label of its own, inside the axes."""
    import matplotlib.pyplot as plt

    x = np.linspace(0.05, 0.95, 19)
    days = np.geomspace(1.0, 365.0, 24)
    X, D = np.meshgrid(x, days)
    C = 10.0 - 7.0 * ((X > 0.88) & (D > 120.0))            # 3 % in the corner: a short 4 % piece, 8 % around it
    fig, ax = plt.subplots(figsize=(2.8, 0.84))
    try:
        ax.set_yscale("log")
        ax.set_xlim(0.05, 0.95)
        ax.set_ylim(1.0, 365.0)
        added = t1.label_missing_levels(ax, x, days, C, labelled={"8 %"})
        assert [t.get_text() for t in added] == ["4 %"]
        fig.canvas.draw()
        box, e = ax.get_window_extent(), added[0].get_window_extent()
        assert box.x0 - 0.5 <= e.x0 and e.x1 <= box.x1 + 0.5 and box.y0 - 0.5 <= e.y0 and e.y1 <= box.y1 + 0.5
        assert t1.label_missing_levels(ax, x, days, C, labelled={"4 %", "8 %"}) == []
    finally:
        plt.close(fig)


def test_expiry_ticks_sit_outside_the_rule_panels(results_dir):
    """A54: the ticks of the listed expiries point outwards, so no iso-line hides among them."""
    data = t1.load(results_dir)
    fig = t1.draw(data, t1.tables(data))
    try:
        fig.canvas.draw()
        for ax in fig.axes:
            if getattr(ax, "name", "") == "3d" or not ax.get_title(loc="left"):
                continue
            box = ax.get_window_extent()
            ticks = [ln for ln in ax.lines if not ln.get_clip_on() and ln.get_linewidth() == pytest.approx(0.7)]
            assert ticks
            for ln in ticks:
                e = ln.get_window_extent()
                assert e.x0 >= box.x1 - 0.5, ax.get_title(loc="left")
    finally:
        matplotlib.pyplot.close(fig)
