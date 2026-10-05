"""F3 (H2, the next contract in the book): smoke test on synthetic mini results, type size, canvas, tables, checks."""
from __future__ import annotations

import json
import re

import matplotlib

matplotlib.use("Agg")

import matplotlib.text  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from derive_surface.figs_p2 import f3  # noqa: E402

EDGES = np.concatenate([[-np.inf], np.round(np.arange(-1.0, 2.0 + 1e-9, 0.05), 10), [np.inf]])
RULE = ("rejected if the upper bound of the 90% day-cluster bootstrap percentile interval of the median of "
        "(dK / amount) / K_pm2_single is >= 0.5; fills with K_pm2_single <= 0 excluded and counted")


def _dist_rows(label, variant, v):
    rows = [{"label": label, "variant": variant, "kind": "n", "x": np.nan, "x_hi": np.nan, "value": float(len(v))},
            {"label": label, "variant": variant, "kind": "share_le_0", "x": 0.0, "x_hi": np.nan,
             "value": float(np.mean(v <= 0))}]
    for q in (0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99):
        rows.append({"label": label, "variant": variant, "kind": "quantile", "x": q, "x_hi": np.nan,
                     "value": float(np.quantile(v, q))})
    counts, _ = np.histogram(v, bins=EDGES)
    for lo, hi, c in zip(EDGES[:-1], EDGES[1:], counts):
        rows.append({"label": label, "variant": variant, "kind": "hist", "x": lo, "x_hi": hi, "value": float(c)})
    return rows


def _sens(variant, group, stat, n, width=0.02):
    return {"variant": variant, "group": group, "stat": stat, "lo": stat - width, "hi": stat + width,
            "rejected": False, "n": n, "n_days": 30, "n_excluded": 0, "share_nonpositive": 0.4}


def make_results(root, regimes=True, rejected=False, hi=None):
    """Synthetic H2 outputs in the shape of ``inference_p2`` (``h2.json``, ``fig_h2_dist.csv``, ``sens_h2.csv``)."""
    rng = np.random.default_rng(3)
    v = np.concatenate([rng.normal(-0.4, 0.5, 700), rng.uniform(0.0, 1.0, 400), np.ones(60),
                        rng.uniform(1.0, 2.6, 30), [-3.0, 5.0]])
    n = len(v)
    stat = float(np.median(v))
    h2 = {"hypothesis": "H2", "claim": "median < 0.5", "variant": "ratio", "stat": stat, "lo": stat - 0.03,
          "hi": stat + 0.03 if hi is None else hi, "rejected": rejected, "rule": RULE, "threshold": 0.5, "n": n,
          "n_days": 41, "n_sample": n + 1, "n_excluded": 1, "share_nonpositive": float(np.mean(v <= 0)),
          "seed": 20260924, "accounts": ["M10", "M3", "M5"], "fills_by_ccy": {"ETH": n - 300, "HYPE": 300},
          "first_day": "2025-09-04"}
    root.mkdir(parents=True, exist_ok=True)
    (root / "h2.json").write_text(json.dumps(h2))
    rows = _dist_rows("all", "ratio", v) + _dist_rows("all", "ratio_unit", v * 0.9)
    pd.DataFrame(rows).to_csv(root / "fig_h2_dist.csv", index=False)
    sens = [dict(_sens("ratio", "all", stat, n), lo=h2["lo"], hi=h2["hi"]), _sens("ratio_unit", "all", 0.05, n), _sens("ratio_tape", "all", 0.07, n),
            _sens("ratio_mm", "all", 0.04, n - 20), _sens("ratio_mm_std", "all", 0.03, n - 2),
            _sens("ratio", "label=M10", 0.02, 500), _sens("ratio", "label=M3", 0.09, 300),
            _sens("ratio", "label=M5", -0.2, n - 800, width=2.5),
            _sens("ratio", "ccy=ETH", 0.03, n - 300), _sens("ratio", "ccy=HYPE", 0.09, 300)]
    if regimes:
        sens += [_sens("ratio", f"regime=R{k}", 0.02 * k, 200 + k) for k in (1, 2, 3, 4)]
    pd.DataFrame(sens).to_csv(root / "sens_h2.csv", index=False)
    return h2


def _visible_texts(fig):
    fig.canvas.draw()
    return [t for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text().strip()]


def test_build_writes_tables_and_figures(tmp_path):
    res, out = tmp_path / "res", tmp_path / "fig"
    make_results(res)
    paths = f3.build(out_dir=out, results_dir=res)
    for p in (out / "f3.pdf", out / "f3.png", res / "fig_f3_a.csv", res / "fig_f3_b.csv"):
        assert p.exists() and p in paths
    with Image.open(out / "f3.png") as im:
        assert im.size == (round(3.29 * 400), round(4.0 * 400))
    box = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", (out / "f3.pdf").read_bytes())
    assert abs(float(box.group(1)) / 72 - 3.29) <= 0.005 and abs(float(box.group(2)) / 72 - 4.0) <= 0.02


def test_type_size_and_canvas(tmp_path):
    make_results(tmp_path)
    fig, _ = f3.make(tmp_path)
    w, h = fig.get_size_inches()
    assert (round(w, 3), round(h, 3)) == (3.29, 4.0)
    r = fig.canvas.get_renderer()
    box = fig.bbox
    for t in _visible_texts(fig):
        assert t.get_fontsize() >= 7.0 - 1e-9, t.get_text()
        e = t.get_window_extent(r)
        assert e.x0 >= box.x0 - 1 and e.x1 <= box.x1 + 1 and e.y0 >= box.y0 - 1 and e.y1 <= box.y1 + 1, t.get_text()
    for ax in fig.axes:
        e = ax.get_tightbbox(r)
        assert e.x0 >= -1 and e.x1 <= box.x1 + 1 and e.y0 >= -1 and e.y1 <= box.y1 + 1
    matplotlib.pyplot.close(fig)


def test_rows_labels_and_regimes(tmp_path):
    make_results(tmp_path)
    _, tables = f3.make(tmp_path)
    b = tables["b"]
    forest = b[b["kind"].isin(["registered", "sensitivity", "exploratory"])]
    assert forest["label"].tolist() == ["registered", "next contract", "maintenance margin", "tape book",
                                        "M3 (HYPE)", "M5", "M10", "R1 to 23 Jan", "R2 to 24 May", "R3 to 20 Aug",
                                        "R4 since 20 Aug"]
    assert forest["label"].str.len().max() <= 18
    assert forest["kind"].tolist()[:4] == ["registered", "sensitivity", "sensitivity", "sensitivity"]
    # an interval running out of the axis ends in an arrow
    m5 = forest[forest["label"] == "M5"].iloc[0]
    assert m5["arrow_lo"] and m5["arrow_hi"]
    header = b[b["kind"] == "header"]["printed"].tolist()
    assert header[0].startswith("registered: ") and header[0].endswith("→ not rejected")
    assert "3 PM2 subaccounts, ETH and HYPE only" in " ".join(header)
    assert "day clusters" in header[-1]


def test_regime_rows_drop_when_missing(tmp_path):
    make_results(tmp_path, regimes=False)
    _, tables = f3.make(tmp_path)
    assert not tables["b"]["label"].astype(str).str.startswith("R").any()


def test_verdict_must_match_rejected(tmp_path):
    make_results(tmp_path, rejected=True)          # upper bound below 0.5 but flagged rejected
    with pytest.raises(ValueError, match="rejected"):
        f3.make(tmp_path)
    make_results(tmp_path, rejected=True, hi=0.6)  # consistent
    _, tables = f3.make(tmp_path)
    assert tables["b"].iloc[0]["printed"].endswith("→ rejected")


def test_ecdf_bands_and_overflows(tmp_path):
    h2 = make_results(tmp_path)
    _, tables = f3.make(tmp_path)
    a = tables["a"]
    ecdf = a[a["kind"] == "ecdf"]
    assert len(ecdf) == 61 and ecdf["x"].iloc[0] == -1.0 and ecdf["x"].iloc[-1] == 2.0
    assert np.all(np.diff(ecdf["value"]) >= 0)
    at0 = float(ecdf.loc[np.isclose(ecdf["x"], 0.0), "value"].iloc[0])
    assert abs(at0 - h2["share_nonpositive"]) <= 1.0 / h2["n"]
    bands = a[a["kind"] == "band"]
    assert bands["key"].tolist() == ["free", "cheap", "partial", "full"]
    assert abs(bands["value"].sum() - 1.0) < 1e-12
    assert bands["printed"].str.endswith("%").all()
    over = a[a["kind"] == "overflow"].set_index("key")
    dist = pd.read_csv(tmp_path / "fig_h2_dist.csv")
    hist = dist[(dist["label"] == "all") & (dist["variant"] == "ratio") & (dist["kind"] == "hist")]
    assert over.loc["below", "count"] == hist["value"].iloc[0] > 0
    assert over.loc["above", "count"] == hist["value"].iloc[-1] > 0
    assert abs(ecdf["value"].iloc[0] - over.loc["below", "value"]) < 1e-12
    assert abs(ecdf["value"].iloc[-1] - (1 - over.loc["above", "value"])) < 1e-12


def test_checks_pass_on_built_tables(tmp_path):
    res, out = tmp_path / "res", tmp_path / "fig"
    make_results(res)
    f3.build(out_dir=out, results_dir=res)
    results = f3.run_checks(res)
    assert len(results) == len(f3.CHECKS) >= 8
    bad = [r for r in results if not r["ok"]]
    assert not bad, bad


def test_checks_catch_a_wrong_figure_table(tmp_path):
    res, out = tmp_path / "res", tmp_path / "fig"
    make_results(res)
    f3.build(out_dir=out, results_dir=res)
    b = pd.read_csv(res / "fig_f3_b.csv")
    b.loc[b["kind"] == "registered", "stat"] += 0.01
    b.to_csv(res / "fig_f3_b.csv", index=False)
    assert any(not r["ok"] for r in f3.run_checks(res))


def test_caption_is_english_without_dashes():
    assert "—" not in f3.CAPTION and "–" not in f3.CAPTION and " - " not in f3.CAPTION
    assert f3.CAPTION.startswith("\\textbf{A fill in a dominant")


def test_caption_says_the_interval_hides_under_the_circle():
    """A50: the median's interval (about 0.4 pt long) is narrower than the circle; the caption must not promise a
    visible bar."""
    assert "the bar at height one half" not in f3.CAPTION
    assert ("the circle at height one half is the median; its 90~per~cent day-cluster interval is narrower than the "
            "circle and printed at the top") in f3.CAPTION


def test_caption_explains_the_hatched_rejection_region():
    """Audit C3: the hatched stretch of the registered row in panel b is the rejection region of the rule."""
    assert ("The hatched stretch of the registered row, right of the threshold, is the rejection region: the rule "
            "rejects H2 if the interval reaches into it.") in f3.CAPTION
