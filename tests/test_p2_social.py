"""Social cards of Paper 2 (``derive_surface.social_p2``, FIGURE_SELECTION section 9): size, type, frame, the title
rule of card 2, a verdict card whose title and layout do not depend on the outcome, and numbers read from
``results/p2`` that ``scripts/p2_figure_check.py`` finds again in their sources."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.text  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from derive_surface import social_p2  # noqa: E402
from tests import test_p2_gif as G  # noqa: E402

CARDS = ["s1", "s2", "s3"]
REPO = Path(__file__).resolve().parents[1]
RULE_UP = "rejected if the upper bound of the 90% day-cluster bootstrap percentile interval is >= {t}"
RULE_LO = "rejected if the lower bound of the 90% day-cluster bootstrap percentile interval is <= {t}"


def _h(stat, lo, hi, thr, rejected, rule):
    return {"stat": stat, "lo": lo, "hi": hi, "threshold": thr, "rejected": rejected, "rule": rule.format(t=thr)}


def _h4(beta=-4.6, p=0.6224, p95=23.4):
    c1, c2 = beta > 0 and p <= 0.05, beta > p95
    return {"stat": beta, "p": p, "placebo": {"p95": p95}, "rejected": not (c1 and c2),
            "criteria": {"beta_positive": beta > 0, "p_le_alpha": p <= 0.05, "beta_gt_placebo_p95": c2}}


def results(root: Path, *, h1=(0.8123, 0.79, 0.82), h2=(0.0417, 0.037, 0.046), h3=(3.9876, 3.9, 4.1),
            straddle=(10.03, 12.02, 29.61, 14.66)) -> Path:
    rd = root / "results"
    rd.mkdir(parents=True)
    hs = {"h1": _h(*h1, 0.5, h1[2] >= 0.5, RULE_UP), "h2": _h(*h2, 0.5, h2[2] >= 0.5, RULE_UP),
          "h3": _h(*h3, 2.0, h3[1] <= 2.0, RULE_LO), "h4": _h4()}
    for k, v in hs.items():
        (rd / f"{k}.json").write_text(json.dumps(v))
    days = pd.date_range("2024-01-11", "2026-09-17", freq="D")
    n = len(days)
    pm2 = np.where(days >= pd.Timestamp("2025-06-13"), 14.5, np.nan)
    pd.DataFrame({"ccy": "BTC", "day": days.strftime("%Y-%m-%d"), "ts": 0, "tenor_days": 22.0,
                  "K_sm_pct": np.full(n, 29.61), "K_pm_pct": np.linspace(23.5, 19.68, n), "K_pm2_pct": pm2,
                  "legacy_thin": False, "drawn": True, "printed": ""}).to_csv(rd / "fig_f5_c.csv", index=False)
    G.events().to_csv(rd / "events.csv", index=False)
    G.reference_book().to_csv(rd / "reference_book.csv", index=False)
    book, call, sm, sm_call = straddle
    rows = [{"kind": "capital", "item": i, "value_pct_forward": v, "value_usdc": v * 765.0}
            for i, v in (("K_pm2_book", book), ("K_pm2_call", call), ("K_sm", sm), ("K_sm_call", sm_call))]
    rows += [{"kind": "meta", "item": "ts", "value_usdc": 1_789_632_000.0},
             {"kind": "meta", "item": "tenor_days", "value_usdc": 22.0}]
    pd.DataFrame(rows).to_csv(rd / "fig_t2_c.csv", index=False)
    return rd


def _texts(fig):
    fig.canvas.draw()
    return [t for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text().strip()]


@pytest.mark.parametrize("name", CARDS)
def test_card_is_1600_by_900_with_large_type_inside_the_frame(tmp_path, name):
    rd = results(tmp_path)
    fig, path = social_p2.CARDS[name](social_p2.load(rd), tmp_path / "out", keep=True)
    with Image.open(path) as im:
        assert im.size == (1600, 900)
    r = fig.canvas.get_renderer()
    for t in _texts(fig):
        assert t.get_fontsize() / social_p2.PT >= social_p2.MIN_PX - 1e-9, (t.get_text(), t.get_fontsize())
        e = t.get_window_extent(r)
        assert e.x0 >= 0 and e.y0 >= 0 and e.x1 <= 1600 and e.y1 <= 900, t.get_text()
    assert any(t.get_text() == social_p2.FOOTER for t in _texts(fig))
    assert path.name == social_p2.NAMES[name] + ".png"
    plt.close(fig)


def test_texts_of_a_card_do_not_overlap(tmp_path):
    rd = results(tmp_path)
    data = social_p2.load(rd)
    for name in CARDS:
        fig, _ = social_p2.CARDS[name](data, tmp_path / "out", keep=True)
        r = fig.canvas.get_renderer()
        boxes = [(t.get_text(), t.get_window_extent(r)) for t in _texts(fig)]
        clash = [(a, b) for i, (a, ea) in enumerate(boxes) for b, eb in boxes[i + 1:] if ea.overlaps(eb)]
        assert clash == [], (name, clash)
        plt.close(fig)


def test_verdict_card_keeps_title_and_layout_whatever_the_outcome(tmp_path):
    """A22: the verdict card is the same card for any outcome; only the verdict words follow the rules."""
    shapes, verdicts = [], []
    for k, kw in enumerate(({}, {"h1": (0.41, 0.35, 0.47), "h2": (0.61, 0.55, 0.66), "h3": (1.8, 1.7, 1.9)})):
        rd = results(tmp_path / str(k), **kw)
        fig, _ = social_p2.card_verdicts(social_p2.load(rd), tmp_path / str(k) / "out", keep=True)
        texts = _texts(fig)
        shapes.append((fig.texts[0].get_text(), len(fig.axes), len(fig.texts)))
        verdicts.append([t.get_text() for t in fig.texts if t.get_text() in ("rejected", "not rejected")])
        plt.close(fig)
        assert any("H4" == t.get_text() for t in texts)
    assert shapes[0] == shapes[1] and shapes[0][0] == "Four pre-registered tests. Four verdicts."
    assert verdicts == [["rejected", "not rejected", "not rejected", "rejected"],
                        ["not rejected", "rejected", "rejected", "rejected"]]


def test_verdict_card_refuses_a_verdict_that_breaks_its_rule(tmp_path):
    rd = results(tmp_path)
    h = json.loads((rd / "h2.json").read_text())
    h["rejected"] = True
    (rd / "h2.json").write_text(json.dumps(h))
    with pytest.raises(ValueError):
        social_p2.card_verdicts(social_p2.load(rd), tmp_path / "out")


def test_verdict_card_shows_no_interval_for_h4_and_no_exploratory_number(tmp_path):
    """A22: nothing exploratory on the cards; H4 shows the estimate, the one-sided p and the placebo P95."""
    rd = results(tmp_path)
    fig, _ = social_p2.card_verdicts(social_p2.load(rd), tmp_path / "out", keep=True)
    texts = [t.get_text() for t in _texts(fig)]
    assert "β = −4.6, one-sided p = 0.62, P95 23.4" in texts
    assert not any("[" in t for t in texts if t.startswith("β"))
    assert not any("0.63" in t or "profitable" in t for t in texts)
    plt.close(fig)


def test_straddle_card_follows_the_title_rule(tmp_path):
    assert social_p2.straddle_title(10.0, 12.0) == social_p2.TITLE_LESS
    assert social_p2.straddle_title(13.0, 12.0) == social_p2.TITLE_LITTLE
    assert social_p2.straddle_title(15.5, 12.0) is None
    rd = results(tmp_path, straddle=(15.5, 12.0, 29.6, 14.7))
    paths = social_p2.build(rd, tmp_path / "social")
    assert [p.name for p in paths] == ["s1_three_engines.png", "s3_verdicts.png"]


def test_straddle_series_card_prints_the_steps_in_whole_simple_per_cent(tmp_path):
    rd = results(tmp_path)
    social_p2.card_straddle_series(social_p2.load(rd), tmp_path / "out")
    s1 = pd.read_csv(rd / "fig_s1.csv").set_index("key")
    steps = s1.loc[s1.index.str.startswith("step_"), "printed"].to_dict()
    assert steps == {"step_BTC-pm2-20260108": "+2 %", "step_BTC-pm2-20260123": "−10 %",
                     "step_BTC-pm2-20260524": "−8 %", "step_BTC-pm2-20260820": "−23 %"}
    assert s1.loc["last_sm", "printed"] == "30 %" and s1.loc["last_pm2", "source"].startswith("fig_f5_c.csv:K_pm2_pct@")


def test_build_writes_the_three_cards_and_the_check_finds_every_number(tmp_path):
    rd = results(tmp_path)
    paths = social_p2.build(rd, tmp_path / "social")
    assert [p.name for p in paths] == ["s1_three_engines.png", "s2_straddle_vs_call.png", "s3_verdicts.png"]
    spec = importlib.util.spec_from_file_location("p2_figure_check", REPO / "scripts" / "p2_figure_check.py")
    fc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fc)
    res = fc.media_checks(rd)
    cards = res[res["slot"].isin(CARDS)]
    n_rows = sum(len(pd.read_csv(rd / f"fig_{c}.csv")) for c in CARDS)
    assert len(cards) == n_rows and cards["ok"].all(), cards.loc[~cards["ok"]].to_string()
    s3 = pd.read_csv(rd / "fig_s3.csv")
    s3.loc[s3["key"] == "h3_stat", "value"] += 0.01
    s3.to_csv(rd / "fig_s3.csv", index=False)
    res = fc.media_checks(rd)
    assert not res.loc[res["check"].str.contains("h3_stat"), "ok"].any()


def test_titles_have_no_dashes():
    import inspect

    src = inspect.getsource(social_p2)
    assert "—" not in src and "–" not in src
