"""F6 of Paper 2 (the price of capital, H4): smoke test on synthetic mini data in a temporary results directory.

Checks the canvas (7.0 x 4.2 in, PDF at print size), the type size (nothing under 7 pt), that every text stays on the
canvas, the dose strip, the binned residuals with the slope beta, the check list of H4 rebuilt from ``criteria``
(and the refusal when it disagrees with ``rejected``), the fallback without binned residuals, and the check list of
the slot against the synthetic sources.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from derive_surface import inference_p2_h4 as h4mod  # noqa: E402
from derive_surface.figs_p2 import _kit_f5f6 as kit  # noqa: E402
from derive_surface.figs_p2 import f6  # noqa: E402

EVENTS = [  # event_id, ccy, manager, event_utc, cells
    ("BTC-pm-20250222", "BTC", "pm", "2025-02-22 19:52:37", 6),
    ("BTC-pm2-20260123", "BTC", "pm2", "2026-01-23 04:24:05", 5),
    ("ETH-pm2-20260123", "ETH", "pm2", "2026-01-23 04:24:05", 7),
    ("HYPE-pm2-20260108", "HYPE", "pm2", "2026-01-08 22:50:49", 0),
]


def _panel(seed: int = 1) -> tuple:
    rng = np.random.default_rng(seed)
    rows, doses = [], []
    for eid, ccy, m, utc, n_cells in EVENTS:
        day0 = pd.Timestamp(utc[:10])
        for c in range(n_cells + 2):                         # two cells without panel fills
            side = "sell" if c % 2 == 0 else "buy"
            cell = f"{ccy}|{side}|{10 * c:02d}-{10 * c + 10}|7-30d"
            dose = float(rng.uniform(-0.40, 0.02)) if c % 3 else float(rng.uniform(-0.005, 0.005))
            doses.append({"event_id": eid, "ccy": ccy, "cell": cell, "dose": dose, "n_fills": 30, "n_valid": 30,
                          "n_nonpos": 0, "n_nan": 0})
            if c >= n_cells:
                continue
            for d in range(-5, 6):
                if d == 0:
                    continue
                for k in range(2 + (c + d) % 3):
                    rows.append({"fill_key": f"{ccy}-{c}-{d}-{k}-{eid[-4:]}", "ccy": ccy, "cell": cell,
                                 "event_id": eid, "post": d > 0, "dose": dose,
                                 "y_hs_bp": float(3 + c + rng.normal() + (d > 0) * 2.0 * dose),
                                 "day": (day0 + pd.Timedelta(days=d)).strftime("%Y-%m-%d")})
    panel = pd.DataFrame(rows)
    # the two BTC-pm2 and ETH-pm2 windows share days; one fill key in two windows
    panel.loc[panel.index[-1], "fill_key"] = panel["fill_key"].iloc[0]
    return panel, pd.DataFrame(doses)


def _write(rd: Path, panel: pd.DataFrame, doses: pd.DataFrame, flip_verdict: bool = False,
           with_bins: bool = True) -> None:
    rd.mkdir(parents=True, exist_ok=True)
    doses.to_csv(rd / "h4_doses.csv", index=False)
    ev = pd.DataFrame([{"event_id": e, "ccy": c, "manager": m, "event_ts": int(pd.Timestamp(u, tz="UTC").timestamp()),
                        "event_day": u[:10], "event_utc": u, "kinds": "scenarios", "kept": True}
                       for e, c, m, u, _ in EVENTS])
    h4mod.event_figure_table(panel, ev).to_csv(rd / "fig_h4_events.csv", index=False)
    f = h4mod.fit(panel)
    betas = np.linspace(-30, 20, 40) + np.random.default_rng(3).normal(0, 1, 40)
    pd.DataFrame({"rep": range(40), "beta": betas}).to_csv(rd / "h4_placebo.csv", index=False)
    p = 0.31
    ps = h4mod.placebo_summary(betas, f.beta)
    v = h4mod.verdict(f.beta, p, ps["p95"])
    adm = {e: {"days": {"BTC": 54, "ETH": 10, "HYPE": 67}[c] if m == "pm2" else {"BTC": 363, "ETH": 319}[c]}
           for e, c, m, _, _ in EVENTS}
    res = {"hypothesis": "H4", "stat": f.beta, "lo": f.beta - 7.0, "hi": f.beta + 5.0,
           "rejected": (not v["rejected"]) if flip_verdict else v["rejected"], "rule": h4mod.RULE, "n": f.n,
           "p": p, "clusters": f.n_clusters, "fills": int(panel["fill_key"].nunique()),
           "events": int(panel["event_id"].nunique()), "events_kept": len(EVENTS),
           "cell_events": int(panel.groupby(["cell", "event_id"]).ngroups),
           "day_ccy": int(panel.groupby(["day", "ccy"]).ngroups), "criteria": v["criteria"],
           "placebo": {**ps, "admissible_days": adm}}
    (rd / "h4.json").write_text(json.dumps(res))
    by_ccy = {}
    for ccy in ("BTC", "ETH"):
        g = h4mod.fit(panel[panel["ccy"] == ccy].reset_index(drop=True))
        by_ccy[ccy] = {"beta": g.beta, "lo": g.beta - 3.0, "hi": g.beta + 90.0, "clusters": g.n_clusters,
                       "n": g.n}
    (rd / "sensitivity_h4.json").write_text(json.dumps({"exploratory": True, "by_ccy": by_ccy}))
    if with_bins:
        h4mod.fwl_bins(panel, f=f).to_csv(rd / "fig_h4_fwl_bins.csv", index=False)


@pytest.fixture()
def setup(tmp_path: Path):
    panel, doses = _panel()
    rd = tmp_path / "results"
    _write(rd, panel, doses)
    pp = tmp_path / "h4_panel.parquet"
    panel.to_parquet(pp)
    return rd, pp


def _pdf_width_in(path: Path) -> float:
    m = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", path.read_bytes())
    return float(m.group(1)) / 72.0


def test_figure_size_type_size_and_canvas(setup):
    rd, pp = setup
    fig = f6.figure(rd, panel_path=pp)
    assert tuple(np.round(fig.get_size_inches(), 3)) == (7.0, 4.2)
    assert kit.small_texts(fig) == []
    assert kit.texts_off_canvas(fig) == []
    assert kit.overlapping_texts(fig) == []


def test_build_writes_pdf_png_and_tables(setup, tmp_path):
    rd, pp = setup
    out = tmp_path / "fig"
    paths = f6.build(out_dir=out, results_dir=rd, panel_path=pp)
    assert {p.name for p in paths} >= {"f6.pdf", "f6.png"}
    assert _pdf_width_in(out / "f6.pdf") == pytest.approx(7.0, abs=0.02)
    from PIL import Image
    with Image.open(out / "f6.png") as im:
        assert im.size == (2800, 1680)
    for name in ("fig_f6_a.csv", "fig_f6_b.csv", "fig_f6_c.csv", "fig_f6_d.csv", "fig_f6_head.csv"):
        assert (rd / name).exists()


def test_dose_strip_rows_pairs_and_sides(setup, tmp_path):
    rd, pp = setup
    f6.build(out_dir=tmp_path / "fig", results_dir=rd, panel_path=pp)
    a = pd.read_csv(rd / "fig_f6_a.csv")
    pairs = a[a["mark"] == "pair"]
    assert len(pairs) == 18                                   # 6 + 5 + 7; HYPE event without panel cells has no row
    assert pairs.groupby("event_id").size().to_dict() == {"BTC-pm-20250222": 6, "BTC-pm2-20260123": 5,
                                                          "ETH-pm2-20260123": 7}
    rows = pairs.drop_duplicates("event_id").sort_values("row")
    assert list(rows["event_id"]) == ["BTC-pm-20250222", "BTC-pm2-20260123", "ETH-pm2-20260123"]
    off = pairs["y"] - pairs["row"]
    assert np.allclose(off[pairs["side"] == "sell"], -0.15) and np.allclose(off[pairs["side"] == "buy"], 0.15)
    doses = pd.read_csv(rd / "h4_doses.csv").set_index(["event_id", "cell"])["dose"]
    for r in pairs.itertuples():
        assert r.dose_logpct == pytest.approx(100 * doses[(r.event_id, r.cell)])
    band = a[a["mark"] == "band"].iloc[0]
    share = float(np.mean(np.abs(pairs["dose_logpct"]) < 1.0))
    assert band["value"] == pytest.approx(share)
    assert band["printed"].startswith("|dose| < 1 log-%: ")


def test_binned_residuals_line_has_the_slope_beta(setup, tmp_path):
    rd, pp = setup
    f6.build(out_dir=tmp_path / "fig", results_dir=rd, panel_path=pp)
    b = pd.read_csv(rd / "fig_f6_b.csv")
    assert set(b["mode"]) == {"bins"}
    res = json.loads((rd / "h4.json").read_text())
    line = b[b["kind"] == "line"].iloc[0]
    assert 100 * line["slope_per_logpct"] == pytest.approx(res["stat"], rel=1e-10)
    assert (b["kind"] == "bin").sum() == 20


def test_fallback_without_binned_residuals_draws_no_line(setup, tmp_path):
    rd, pp = setup
    (rd / "fig_h4_fwl_bins.csv").unlink()
    fig = f6.figure(rd, panel_path=pp)
    assert kit.small_texts(fig) == [] and kit.texts_off_canvas(fig) == [] and kit.overlapping_texts(fig) == []
    f6.build(out_dir=tmp_path / "fig", results_dir=rd, panel_path=pp)
    b = pd.read_csv(rd / "fig_f6_b.csv")
    assert set(b["mode"]) == {"contrast"}
    assert (b["kind"] == "line").sum() == 0
    assert (b["kind"] == "contrast").sum() == 3 * 3
    ev = pd.read_csv(rd / "fig_h4_events.csv").set_index("event_id")
    e = ev.loc["ETH-pm2-20260123"]
    c = b[(b["kind"] == "contrast") & (b["event_id"] == "ETH-pm2-20260123")].sort_values("tercile")
    med = [e[f"t{k}_median_dose"] for k in (1, 2, 3)]
    dy = [e[f"t{k}_y_post"] - e[f"t{k}_y_pre"] for k in (1, 2, 3)]
    assert c["x"].tolist() == pytest.approx([100 * (m - np.mean(med)) for m in med])
    assert c["y"].tolist() == pytest.approx([d - np.mean(dy) for d in dy])


def test_checklist_follows_criteria_and_refuses_a_mismatch(setup, tmp_path):
    rd, pp = setup
    f6.build(out_dir=tmp_path / "fig", results_dir=rd, panel_path=pp)
    c = pd.read_csv(rd / "fig_f6_c.csv", keep_default_na=False)
    res = json.loads((rd / "h4.json").read_text())
    verdict = c.loc[c["kind"] == "verdict", "printed"].iloc[0]
    assert verdict == ("H4: rejected" if res["rejected"] else "H4: not rejected")
    assert (c["kind"] == "placebo").sum() == 40
    panel, doses = _panel()
    _write(rd, panel, doses, flip_verdict=True)
    with pytest.raises(ValueError, match="rejected"):
        f6.figure(rd, panel_path=pp)


def test_checks_agree_on_synthetic_results(setup, tmp_path):
    rd, pp = setup
    f6.build(out_dir=tmp_path / "fig", results_dir=rd, panel_path=pp)
    checks = f6.checks(panel_path=pp)
    res = kit.run_checks(checks, rd, with_expected=False)
    assert res["error"].eq("").all(), res.loc[res["error"] != "", ["id", "error"]].to_string()
    assert res["agrees"].all(), res.loc[~res["agrees"], ["id", "figure", "source"]].to_string()
    assert len(f6.CHECKS) == len(checks)


def test_caption_has_no_dashes():
    assert "—" not in f6.CAPTION and "–" not in f6.CAPTION and " - " not in f6.CAPTION
    assert f6.CAPTION.startswith("\\textbf{The price of capital (H4).}")
