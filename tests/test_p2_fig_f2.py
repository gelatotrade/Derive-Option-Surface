"""F2 (the map in two denominators, H1): smoke test on synthetic mini data, type size, canvas size, verdict rule,
tables and checks."""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.text  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from derive_surface.figs_p2 import f2  # noqa: E402
from derive_surface.markouts import DELTA_LABELS, TENOR_LABELS  # noqa: E402

CCYS = ("BTC", "ETH", "HYPE")
SIDES = ("sell", "buy")
RULE = ("rejected if the upper bound of the 90% day-cluster bootstrap percentile interval of Spearman's rho "
        "between edge in bp of notional and edge per PM2 capital over the occupied cells is >= 0.5")


def row(stat, lo, hi, n, n_days=40):
    return {"stat": stat, "lo": lo, "hi": hi, "rejected": bool(hi >= 0.5), "n": n, "n_days": n_days,
            "rule": "H1", "exploratory": True}


def synth(results_dir: Path, seed: int = 1, sign: bool = True, rejected=None, rfq: bool = True,
          package: bool = True, h1_stat=(0.83, 0.78, 0.87)) -> None:
    """h1_cells.csv, h1.json and sensitivity.json with the keys F2 reads."""
    rng = np.random.default_rng(seed)
    rows = []
    for ccy in CCYS:
        for side in SIDES:
            for i, d in enumerate(DELTA_LABELS):
                for j, t in enumerate(TENOR_LABELS):
                    fills = int(rng.choice([12, 150, 400, 2000], p=[0.1, 0.1, 0.4, 0.4]))
                    idx = fills * 1e5
                    kappa = (8 + 2 * i) if side == "sell" else 0.07 * 1.8 ** (i + 0.6 * j)
                    a_bp = rng.normal(1.0, 4.0)
                    rows.append({"cell": f"{ccy}|{side}|{d}|{t}", "ccy": ccy, "side": side, "delta_bucket": d,
                                 "tenor_bucket": t, "fills": fills, "contracts": fills * 2.0, "fills_k_le_0": 0,
                                 "sum_edge": a_bp * idx / 1e4, "sum_index": idx, "sum_K": kappa / 100 * idx})
    h = pd.DataFrame(rows)
    h["sum_den"] = h["sum_K"]
    h["scale"] = 1.0
    h["occupied"] = h["fills"] >= 200
    h["A_bp"] = 1e4 * h["sum_edge"] / h["sum_index"]
    h["B_bp"] = 1e4 * h["sum_edge"] / h["sum_K"]
    occ = h["occupied"]
    h["rank_A"] = h["A_bp"].where(occ).rank(ascending=False)
    h["rank_B"] = h["B_bp"].where(occ).rank(ascending=False)
    h["rank_shift"] = h["rank_B"] - h["rank_A"]
    for c in ("A", "B"):
        h[f"{c}_lo"] = h[f"{c}_bp"] - 1
        h[f"{c}_hi"] = h[f"{c}_bp"] + 1
        h[f"rank_{c}_lo"] = (h[f"rank_{c}"] - 6).clip(lower=1)
        h[f"rank_{c}_hi"] = (h[f"rank_{c}"] + 6).clip(upper=int(occ.sum()))
    h["window"] = "pm2"
    h["capital"] = "K_pm2"
    results_dir.mkdir(parents=True, exist_ok=True)
    h.to_csv(results_dir / "h1_cells.csv", index=False)
    n = int(occ.sum())
    stat, lo, hi = h1_stat
    h1 = {"hypothesis": "H1", "stat": stat, "lo": lo, "hi": hi, "rejected": bool(hi >= 0.5) if rejected is None
          else rejected, "rule": RULE, "threshold": 0.5, "n": n, "n_days": 40,
          "n_fills": int(h.loc[occ, "fills"].sum()), "n_fills_window": int(h["fills"].sum()),
          "n_fills_k_le_0": 0, "n_cells_any": len(h), "cells_present_min": n}
    (results_dir / "h1.json").write_text(json.dumps(h1))
    sens = {"a_maps": {"sm_pm2_window": row(0.82, 0.77, 0.86, n), "pm_pm2_window": row(0.84, 0.8, 0.88, 80)},
            "b_mm": {"h1_pm2_mm": row(0.83, 0.78, 0.87, n)},
            "c_p1_net_edge": {"h1_pm2": row(0.85, 0.8, 0.89, n)},
            "f_time": {"to_expiry": row(0.7, 0.6, 0.76, n), "holding": row(0.72, 0.65, 0.8, n)},
            "g_by_ccy": {f"pm2_{c}": row(0.8, 0.7, 0.9, 30) for c in CCYS}}
    if rfq:
        sens["i_rfq"] = {"h1_pm2_no_rfq": row(0.8, 0.75, 0.85, n - 5)}
    if package:
        sens["c2_rfq_package"] = {"h1_pm2": row(0.84, 0.79, 0.88, n)}
    if sign:
        npos = int((h.loc[occ, "A_bp"] > 0).sum())
        sens["h1_sign"] = {"within_pos": row(0.6, 0.45, 0.7, npos), "within_nonpos": row(-0.3, -0.45, 0.1, n - npos),
                           "sign_floor": {"mean": 0.7, "p05": 0.66, "p95": 0.74, "draws": 4000,
                                          "seed": 20260924}}
    (results_dir / "sensitivity.json").write_text(json.dumps(sens))


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


def test_fmt_edge_at_most_four_characters_with_the_true_minus():
    vals = (3.44, -0.84, 240.2, -35.4, 3120.0, -12345.0, 9.96, 999.6, -999.6, 0.04, -725.3)
    got = [f2.fmt_edge(v) for v in vals]
    assert got == ["3.4", "−0.8", "240", "−35", "3k", "−12k", "10", "1k", "−1k", "0.0", "−725"]
    assert all(len(s) <= 4 for s in got)
    assert not any("-" in s for s in got)                  # U+2212, as in every other figure (audit T9)


def test_cells_print_sells_in_bp_and_buys_in_per_cent():
    """F1/T9: in bp a buy row reads -418 -397 -109 -255; in per cent it is -4.2 -4.0 -1.1 -2.6, and 5k bp is 50."""
    assert [f2.printed_cell("sell", v) for v in (-725.3, -7.3, 0.1, 164.0)] == ["−725", "−7.3", "0.1", "164"]
    assert [f2.printed_cell("buy", v) for v in (-418.0, -397.0, 4980.0, -2049.0, 8.8, -6.3)] == [
        "−4.2", "−4.0", "50", "−20", "0.1", "−0.1"]
    assert "bp for sells, % for buys" in f2.HEADER


def _print_canvas(fig):
    from derive_surface.figs_p2._print import to_print

    to_print(fig)
    fig.canvas.draw()
    return fig.canvas.get_renderer()


def test_neighbouring_cell_numbers_keep_a_gap_at_print_size(rd):
    """F1/T9: the widest pairs that the formats allow, side by side in two cells of a map, keep at least 2.3 pt of
    white between their ink, with the true minus at 7 pt: sells "−8.8" next to "−888", buys "−8.8" next to
    "−8.8"."""
    fig, _ = f2.make_figure(rd)
    r = _print_canvas(fig)
    maps = [ax for ax in fig.axes if len(ax.get_xticks()) == len(TENOR_LABELS) and ax.get_ylim()[0] > 6]
    assert len(maps) == 6
    cell_pt = maps[0].get_window_extent(r).width / len(TENOR_LABELS) * 72.0 / fig.dpi

    def ink_pt(s):                                          # width of the glyph outlines, not of the advance
        return TextPath((0, 0), s, size=7.0, prop=FontProperties(family="DejaVu Sans")).get_extents().width

    assert cell_pt - (ink_pt("−8.8") + ink_pt("−888")) / 2 >= 2.3
    assert cell_pt - ink_pt("−8.8") >= 3.4
    assert cell_pt - ink_pt("−888") >= 1.0                  # alone, the widest number stays inside its cell
    plt.close(fig)


def test_hatched_cells_leave_the_number_free_and_keep_the_grid_line(rd):
    """F1: a box behind the number wider than its cell covered the white grid line, so "-418-397" ran together."""
    fig, _ = f2.make_figure(rd)
    maps = [ax for ax in fig.axes if len(ax.get_xticks()) == len(TENOR_LABELS) and ax.get_ylim()[0] > 6]
    for ax in maps:
        assert not any(t.get_bbox_patch() is not None for t in ax.texts)
        for patch in ax.patches:
            x, w = patch.get_x(), patch.get_width()
            assert w <= 1.0 + 1e-9 and abs((x + 0.5) - round(x + 0.5)) < 1e-9   # every patch inside one cell
    plt.close(fig)


def test_verdict_is_rebuilt_from_rule_and_bounds():
    h = {"stat": 0.8, "lo": 0.7, "hi": 0.9, "rejected": True, "rule": RULE, "threshold": 0.5}
    assert f2.verdict(h, side="upper") is True
    with pytest.raises(ValueError):
        f2.verdict({**h, "rejected": False}, side="upper")
    with pytest.raises(ValueError):
        f2.verdict({**h, "hi": 0.4}, side="upper")          # rule says not rejected, file says rejected
    assert f2.verdict({**h, "hi": 0.4, "lo": 0.1, "rejected": False}, side="upper") is False
    with pytest.raises(ValueError):
        f2.verdict(h, side="lower")                         # rule text names the upper bound


def test_build_aborts_when_the_verdict_disagrees(tmp_path):
    d = tmp_path / "bad"
    synth(d, rejected=False)
    with pytest.raises(ValueError):
        f2.make_figure(d)


def test_top10_breaks_ties_by_cell_id():
    cells = pd.DataFrame({"cell": [f"c{i:02d}" for i in range(14)],
                          "rank_shift": [5, -30, 30, 12, -12, 12, 1, 2, 3, 40, -40, 7, 7, 7]})
    top = f2.top_moves(cells, 10)
    assert list(top) == ["c09", "c10", "c01", "c02", "c03", "c04", "c05", "c11", "c12", "c13"]


def test_smoke_build_writes_figures_and_tables(rd, tmp_path):
    out = tmp_path / "fig"
    paths = f2.build(out_dir=out, results_dir=rd)
    names = {p.name for p in paths}
    assert {"f2.pdf", "f2.png", "fig_f2_a.csv", "fig_f2_b.csv", "fig_f2_c.csv", "fig_f2_shift.csv"} <= names
    w, h = pdf_size_in(out / "f2.pdf")
    assert w == pytest.approx(6.84, abs=0.005) and h == pytest.approx(4.4, abs=0.02)
    cells = pd.read_csv(rd / "h1_cells.csv")
    b = pd.read_csv(rd / "fig_f2_b.csv")
    assert len(b) == int(cells["occupied"].sum()) and int(b["top10"].sum()) == 10
    a = pd.read_csv(rd / "fig_f2_a.csv", keep_default_na=False)
    assert len(a) == 210 and (a["printed"] == "×").sum() == 210 - int(cells["occupied"].sum())
    c = pd.read_csv(rd / "fig_f2_c.csv")
    assert c.loc[c["kind"] == "header", "printed"].iloc[0] == "registered: 0.83 [0.78, 0.87] → rejected"


def test_sign_rows_and_band_follow_the_data_contract(tmp_path):
    with_sign, without = tmp_path / "s", tmp_path / "n"
    synth(with_sign, sign=True)
    synth(without, sign=False)
    fig, t = f2.make_figure(with_sign)
    c = t["c"]
    assert {"edge > 0 only", "edge ≤ 0 only"} <= set(c["label"]) and (c["kind"] == "band").sum() == 1
    plt.close(fig)
    fig, t = f2.make_figure(without)
    c = t["c"]
    assert not ({"edge > 0 only", "edge ≤ 0 only"} & set(c["label"])) and (c["kind"] == "band").sum() == 0
    assert (c["kind"].isin(["registered", "sensitivity", "exploratory"])).sum() == 12
    plt.close(fig)


def test_row_without_rfq_fills_follows_the_data_contract(tmp_path):
    """Audit A12: an exploratory row without RFQ fills, left out while sensitivity.json has no i_rfq entry."""
    with_rfq, without = tmp_path / "r", tmp_path / "n"
    synth(with_rfq)
    synth(without, rfq=False)
    fig, t = f2.make_figure(with_rfq)
    row = t["c"].set_index("label").loc["without RFQ fills"]
    assert row["kind"] == "exploratory" and row["source_key"] == "sensitivity.json:i_rfq.h1_pm2_no_rfq"
    plt.close(fig)
    fig, t = f2.make_figure(without)
    assert "without RFQ fills" not in set(t["c"]["label"])
    plt.close(fig)


def test_row_rfq_fee_over_legs_follows_the_data_contract(tmp_path):
    """C4: Addendum 6 adds H1 with the fee of an RFQ package spread over its legs; a registered sensitivity row,
    left out while sensitivity.json has no c2_rfq_package entry."""
    with_pkg, without = tmp_path / "p", tmp_path / "n"
    synth(with_pkg)
    synth(without, package=False)
    fig, t = f2.make_figure(with_pkg)
    c = t["c"].reset_index(drop=True)
    row = c.set_index("label").loc["RFQ fee over legs"]
    assert row["kind"] == "sensitivity" and row["source_key"] == "sensitivity.json:c2_rfq_package.h1_pm2"
    assert list(c["label"][:4]) == ["registered", "maintenance margin", "companion net edge", "RFQ fee over legs"]
    plt.close(fig)
    fig, t = f2.make_figure(without)
    assert "RFQ fee over legs" not in set(t["c"]["label"])
    plt.close(fig)


def test_forest_labels_short_and_n_column_headed(rd):
    """Section 6.5: row labels at most 18 characters; C10/F11: the count column is headed n."""
    assert all(len(label) <= f2.LABEL_MAX for label, *_ in f2.FOREST_ROWS)
    fig, _ = f2.make_figure(rd)
    assert "n" in [t.get_text() for t in texts(fig)]
    plt.close(fig)


def test_forest_rows_are_set_with_leading(rd):
    """F4: rows of 7 pt type were set solid at 7.0 pt; every row of the forest now gets at least 7.9 pt."""
    fig, t = f2.make_figure(rd)
    ax = [a for a in fig.axes if a.get_xlabel() == "Spearman's ρ"][0]
    rows = len(ax.get_yticks())
    assert rows == (t["c"]["kind"].isin(["registered", "sensitivity", "exploratory", "band"])).sum()
    assert ax.get_window_extent().height * 72.0 / fig.dpi / rows >= 7.9
    plt.close(fig)


@pytest.mark.parametrize("h1_stat", [(0.83, 0.78, 0.87), (0.3, 0.2, 0.45)])
def test_no_text_runs_into_another_at_print_size(tmp_path, h1_stat):
    """F12/C7 (header against the letter b), F6/T13 (row title against the tick 90-100), the verdict of c against
    the axis title of b, also when the verdict reads "not rejected" (a longer line)."""
    d = tmp_path / "r"
    synth(d, h1_stat=h1_stat, rejected=bool(h1_stat[2] >= 0.5))
    fig, _ = f2.make_figure(d)
    r = _print_canvas(fig)
    W, H = fig.bbox.width, fig.bbox.height
    boxes = []
    for t in texts(fig):
        if t.get_rotation() not in (0.0, 90.0) or t.get_text() == "×":     # tenor ticks (40 degrees), crosses
            continue
        e = t.get_window_extent(r)
        assert e.x0 >= -0.5 and e.x1 <= W + 0.5 and e.y0 >= -0.5 and e.y1 <= H + 0.5, t.get_text()
        boxes.append((t.get_text(), e))
    for i, (ta, a) in enumerate(boxes):
        for tb, b in boxes[i + 1:]:
            assert not (a.x0 < b.x1 and b.x0 < a.x1 and a.y0 < b.y1 and b.y0 < a.y1), (ta, tb)
    plt.close(fig)


def test_type_size_canvas_and_extent(rd):
    fig, _ = f2.make_figure(rd)
    assert tuple(fig.get_size_inches()) == pytest.approx((7.0, 4.4))
    r = fig.canvas.get_renderer()
    canvas = fig.bbox
    for t in texts(fig):
        assert t.get_fontsize() >= f2.FS_MIN - 1e-9, t.get_text()
        e = t.get_window_extent(r)
        assert e.x0 >= canvas.x0 - 1 and e.x1 <= canvas.x1 + 1, t.get_text()
        assert e.y0 >= canvas.y0 - 1 and e.y1 <= canvas.y1 + 1, t.get_text()
    for ax in fig.axes:
        e = ax.get_tightbbox(r)
        assert e.x0 >= canvas.x0 - 1 and e.x1 <= canvas.x1 + 1
        assert e.y0 >= canvas.y0 - 1 and e.y1 <= canvas.y1 + 1
    assert not any(t.get_text() in ("▲", "▼") for t in texts(fig))
    plt.close(fig)


def test_checks_pass_on_consistent_data(rd, tmp_path):
    f2.build(out_dir=tmp_path / "fig", results_dir=rd)
    res = f2.run_checks(rd)
    assert len(res) == len(f2.CHECKS) >= 8
    assert res["ok"].all(), res[~res["ok"]].to_string()


def test_caption_is_english_without_dashes_and_uses_placeholders():
    assert "—" not in f2.CAPTION and "–" not in f2.CAPTION
    for key in ("p1-map-fig", "h1-cells", "h1-pos"):
        assert "\\PH{" + key + "}" in f2.CAPTION


def test_buy_row_is_not_called_edge_per_premium_without_the_money_qualifier():
    """A13: the denominator is about the premium only for buys out of the money. T1: OTM is defined in Figure 1 and
    glossed once more in Figure 3, so this caption does not gloss it again."""
    assert "OTM" in f2.SIDE_TITLE["buy"]
    assert "lower row is edge per unit of premium" not in f2.CAPTION
    assert "about the premium when the option is out of the money and less in the money" in f2.CAPTION
    assert "(OTM)" not in f2.CAPTION


def test_caption_says_what_the_hatch_the_dotted_lines_the_units_and_n_are():
    """C3: the hatched stretch of the registered row is the rejection region, in the words of Figures 5 and 6;
    F3: the sign lines are dotted; F1: the two units of panel a; C10/F11: n."""
    assert ("The hatched stretch of the registered row, right of the threshold, is the rejection region: the rule "
            "rejects H1 if the interval reaches into it.") in f2.CAPTION
    assert "the dotted lines mark that boundary" in f2.CAPTION
    assert "in basis points for maker sells and in per cent for maker buys" in f2.CAPTION
    assert "n is the number of cells in a row" in f2.CAPTION


def test_sign_lines_are_dotted_and_the_rank_intervals_carry_end_ticks(rd):
    """F3: boundary lines and interval crosses were drawn alike (grey, 0.6 pt, solid)."""
    fig, t = f2.make_figure(rd)
    ax = [a for a in fig.axes if a.get_xlabel().startswith("rank by edge per notional")][0]
    sign = [ln for ln in ax.get_lines() if ln.get_color() == f2.SIGN_GREY]
    assert len(sign) == 2 and all(ln.get_linestyle() not in ("-", "solid") for ln in sign)
    crosses = [ln for ln in ax.get_lines() if ln.get_marker() in ("|", "_")]
    assert len(crosses) == 2 * int(t["b"]["top10"].sum())
    assert all(ln.get_linestyle() == "-" for ln in crosses)
    plt.close(fig)


def test_caption_names_the_selection_per_replicate_and_the_hidden_interval():
    """A04: the sign rows choose their cells again in every replicate; A50: the registered interval is narrower
    than its circle and printed above the panel."""
    assert "the cells are chosen again in every replicate" in f2.CAPTION
    assert "narrower than its circle" in f2.CAPTION
