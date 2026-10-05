"""F4 (H3, what netting is worth): smoke test on synthetic mini results, type size, canvas, tables, checks."""
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

from derive_surface.figs_p2 import f3, f4  # noqa: E402

RULE = ("rejected if the lower bound of the 90% day-cluster bootstrap percentile interval of the median of "
        "K_sm / K_pm2 over maker days is <= 2; days with K_pm2 <= 0 excluded and counted")
ACCOUNTS = {"M1": "PM:ETH", "M2": "SM", "M3": "PM2:HYPE", "M5": "PM2:ETH", "M6": "PM:BTC"}


def _sens(variant, group, stat, n, width=0.2, rule="H3"):
    return {"variant": variant, "group": group, "stat": stat, "lo": stat - width, "hi": stat + width,
            "rejected": False, "n": n, "n_days": 60, "n_excluded": 0, "n_not_applicable": 0, "rule": rule}


def make_results(root, extra_groups=True, rejected=False):
    """Synthetic H3 outputs in the shape of ``inference_p2`` (``h3.json``, ``fig_h3_series.csv``, ``sens_h3.csv``)."""
    rng = np.random.default_rng(5)
    edges = [1, 4, 8, 16, 32, 64, 128, 256, 512]
    rows = []
    labels = list(ACCOUNTS)
    for k, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        for i in range(22 + 3 * k):
            legs = int(rng.integers(lo, min(hi, 318)))
            lab = labels[(i + k) % len(labels)]
            ratio = float(np.exp(rng.normal(np.log(0.9 + 0.8 * k), 0.4)))
            rows.append({"label": lab, "day": f"2026-01-{1 + i % 28:02d}", "manager": ACCOUNTS[lab], "status": "ok",
                         "n_legs": float(legs), "over_63_options": legs > 63, "ratio_sm_pm2": ratio})
    rows += [{"label": "M1", "day": "2026-02-01", "manager": "PM:ETH", "status": "no_options", "n_legs": 0.0,
              "over_63_options": False, "ratio_sm_pm2": np.nan}]
    series = pd.DataFrame(rows)
    ok = series[series["status"] == "ok"]
    root.mkdir(parents=True, exist_ok=True)
    series.to_csv(root / "fig_h3_series.csv", index=False)
    n = len(ok)
    stat = float(ok["ratio_sm_pm2"].median())
    h3 = {"hypothesis": "H3", "claim": "median > 2.0", "stat": stat, "lo": stat - 0.3, "hi": stat + 0.3,
          "rejected": rejected, "rule": RULE, "threshold": 2.0, "n": n, "n_days": 28, "n_rows": len(series),
          "n_not_ok": 1, "status_counts": {"no_options": 1, "ok": n}, "n_excluded": 0,
          "days_over_63_options": int(ok["over_63_options"].sum()),
          "share_days_over_63_options": float(ok["over_63_options"].mean()),
          "accounts": {k: int((ok["label"] == k).sum()) for k in labels}}
    (root / "h3.json").write_text(json.dumps(h3))
    sens = [dict(_sens("sm_pm2", "all", stat, n), lo=h3["lo"], hi=h3["hi"]), _sens("sm_pm2_mm", "all", stat * 1.2, n),
            _sens("pm_pm2_be", "all", 1.5, n - 40, 0.02, rule="descriptive (no preregistered threshold)"),
            _sens("sm_pm2_be", "all", stat * 1.02, n - 40), _sens("sm_pm2_le63", "all", 1.4, 100),
            dict(_sens("sm_pm2_gt63", "all", 5.0, n - 100), lo=4.8, hi=900.0)]
    sens += [_sens("sm_pm2", f"label={k}", 3.0, int((ok["label"] == k).sum())) for k in labels]
    if extra_groups:
        sens += [_sens("sm_pm2", "account_manager=SM", 1.1, 40), _sens("sm_pm2", "account_manager=PM", 4.0, 80),
                 _sens("sm_pm2", "account_manager=PM2", 5.0, 90)]
        sens += [_sens("sm_pm2", f"regime=R{k}", 3.0 + k, 40 + k) for k in (1, 2, 3, 4)]
    pd.DataFrame(sens).to_csv(root / "sens_h3.csv", index=False)
    return h3, series


def _visible_texts(fig):
    fig.canvas.draw()
    return [t for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text().strip()]


def test_build_writes_tables_and_figures(tmp_path):
    res, out = tmp_path / "res", tmp_path / "fig"
    make_results(res)
    paths = f4.build(out_dir=out, results_dir=res)
    for p in (out / "f4.pdf", out / "f4.png", res / "fig_f4_a.csv", res / "fig_f4_b.csv"):
        assert p.exists() and p in paths
    with Image.open(out / "f4.png") as im:
        assert im.size == (round(3.29 * 400), round(4.0 * 400))
    box = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", (out / "f4.pdf").read_bytes())
    assert abs(float(box.group(1)) / 72 - 3.29) <= 0.005 and abs(float(box.group(2)) / 72 - 4.0) <= 0.02


def test_type_size_and_canvas(tmp_path):
    make_results(tmp_path)
    fig, _ = f4.make(tmp_path)
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


def test_same_frame_as_f3(tmp_path):
    from test_p2_fig_f3 import make_results as make_h2
    make_results(tmp_path)
    make_h2(tmp_path)
    fa, _ = f3.make(tmp_path)
    fb, _ = f4.make(tmp_path)
    assert len(fa.axes) == len(fb.axes) == 2
    for x, y in zip(fa.axes, fb.axes):
        assert np.allclose(x.get_position().bounds, y.get_position().bounds)
    matplotlib.pyplot.close("all")


def test_bins_and_counterfactual(tmp_path):
    h3, series = make_results(tmp_path)
    _, tables = f4.make(tmp_path)
    a = tables["a"]
    bins = a[a["kind"] == "bin"]
    assert bins["lo"].tolist() == [1, 4, 8, 16, 32, 64, 128, 256]
    assert bins["hi"].tolist() == [4, 8, 16, 32, 64, 128, 256, 512]
    assert np.allclose(bins["centre"], np.sqrt(bins["lo"] * bins["hi"]))
    assert int(bins["n"].sum()) == h3["n"]
    ok = series[series["status"] == "ok"]
    first = ok[ok["n_legs"] < 4]["ratio_sm_pm2"]
    row = bins.iloc[0]
    assert np.isclose(row["median"], first.median()) and np.isclose(row["p25"], first.quantile(0.25))
    cf = a[a["key"] == "counterfactual"].iloc[0]
    assert int(cf["n"]) == h3["days_over_63_options"]
    assert cf["printed"] == "SM counterfactual: {} of {} maker-days".format(
        f4.fmt_int(h3["days_over_63_options"]), f4.fmt_int(h3["n"]))


def test_rows_labels_and_optional_groups(tmp_path):
    make_results(tmp_path)
    _, tables = f4.make(tmp_path)
    b = tables["b"]
    forest = b[b["kind"].isin(["registered", "sensitivity", "exploratory"])]
    assert forest["label"].tolist() == ["registered", "maintenance margin", "legacy PM / PM2",
                                        "SM / PM2 same legs", "≤ 63 legs", "> 63 legs", "SM books (M2)",
                                        "legacy PM books", "PM2 books", "R1 to 23 Jan", "R2 to 24 May",
                                        "R3 to 20 Aug", "R4 since 20 Aug"]
    assert forest["label"].str.len().max() <= 18
    assert forest["kind"].tolist()[:3] == ["registered", "sensitivity", "sensitivity"]
    gt = forest[forest["label"] == "> 63 legs"].iloc[0]
    assert gt["arrow_hi"] and not gt["arrow_lo"]
    make_results(tmp_path, extra_groups=False)
    _, tables = f4.make(tmp_path)
    labels = tables["b"]["label"].astype(str).tolist()
    assert "PM2 books" not in labels and "R1 to 23 Jan" not in labels and "SM / PM2 same legs" in labels


def test_verdict_must_match_rejected(tmp_path):
    make_results(tmp_path, rejected=True)          # lower bound above 2 but flagged rejected
    with pytest.raises(ValueError, match="rejected"):
        f4.make(tmp_path)


def test_checks_pass_on_built_tables(tmp_path):
    res, out = tmp_path / "res", tmp_path / "fig"
    make_results(res)
    f4.build(out_dir=out, results_dir=res)
    results = f4.run_checks(res)
    assert len(results) == len(f4.CHECKS) >= 8
    bad = [r for r in results if not r["ok"]]
    assert not bad, bad


def test_checks_catch_a_wrong_figure_table(tmp_path):
    res, out = tmp_path / "res", tmp_path / "fig"
    make_results(res)
    f4.build(out_dir=out, results_dir=res)
    a = pd.read_csv(res / "fig_f4_a.csv")
    a.loc[(a["kind"] == "bin") & (a["lo"] == 64), "median"] *= 1.1
    a.to_csv(res / "fig_f4_a.csv", index=False)
    assert any(not r["ok"] for r in f4.run_checks(res))


def test_caption_is_english_without_dashes():
    assert "—" not in f4.CAPTION and "–" not in f4.CAPTION and " - " not in f4.CAPTION
    assert f4.CAPTION.startswith("\\textbf{What netting is worth")


def test_caption_explains_both_hatches_and_the_grey_counts():
    """Audit C3 and C10: panel a hatches the counterfactual SM range and prints the maker-days per bin in grey; panel
    b hatches the rejection region of the registered row. The caption names all three."""
    assert "the grey numbers above the axis are the maker-days per bin" in f4.CAPTION
    assert "$K_{\\mathrm{SM}}$ is counterfactual (hatched)" in f4.CAPTION
    assert ("The hatched stretch of the registered row, left of the threshold, is the rejection region: the rule "
            "rejects H3 if the interval reaches into it.") in f4.CAPTION
