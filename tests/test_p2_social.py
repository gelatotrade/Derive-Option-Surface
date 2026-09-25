"""Social cards of Paper 2 (``derive_surface.social_p2``): size, type, frame, numbers from ``summary.json``."""
from __future__ import annotations

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

CARDS = ["s1", "s2", "s3"]


def results(root: Path, h1=0.8123, h2=0.0417, h3=3.9876) -> Path:
    rd = root / "results"
    rd.mkdir(parents=True)
    summary = {"h1_stat": h1, "h1_lo": h1 - 0.02, "h1_hi": h1 + 0.01, "h1_n_cells": 12, "h1_first_day": "2025-06-12",
               "h1_last_day": "2026-09-17",
               "h2_stat": h2, "h2_lo": h2 - 0.004, "h2_hi": h2 + 0.005, "h2_share_nonpositive": 0.3871,
               "h2_n": 1999, "h2_n_accounts": 3, "h2_first_day": "2025-09-04", "h2_last_day": "2026-09-17",
               "h3_stat": h3, "h3_lo": h3 - 0.1, "h3_hi": h3 + 0.1, "h3_n": 321, "h3_n_accounts": 5,
               "h3_first_day": "2025-06-13", "h3_last_day": "2026-09-17", "h3_share_days_over_63_options": 0.61}
    (rd / "summary.json").write_text(json.dumps(summary))
    edges = [1, 4, 8, 16, 32, 64, 128, 256, 512]
    rows = [{"kind": "bin", "key": f"[{a}, {b})", "lo": a, "hi": b, "centre": float(np.sqrt(a * b)), "n": 30,
             "median": 0.9 + 0.8 * i, "p25": 0.7 + 0.6 * i, "p75": 1.1 + 1.0 * i, "printed": "30"}
            for i, (a, b) in enumerate(zip(edges[:-1], edges[1:]))]
    pd.DataFrame(rows).to_csv(rd / "fig_f4_a.csv", index=False)
    rng = np.random.default_rng(3)
    a = np.arange(1, 13)
    b = np.argsort(np.argsort(a + rng.normal(0, 2, 12))) + 1
    pd.DataFrame({"cell": [f"c{i}" for i in a], "side": ["sell", "buy"] * 6, "rank_A": a.astype(float),
                  "rank_B": b.astype(float)}).to_csv(rd / "fig_f2_b.csv", index=False)
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
    plt.close(fig)


def test_numbers_come_from_summary_and_stand_in_the_drawing(tmp_path):
    rd = results(tmp_path)
    data = social_p2.load(rd)
    expected = {"s1": "4.2 %", "s2": "4.0", "s3": "0.81"}
    for name, number in expected.items():
        fig, _ = social_p2.CARDS[name](data, tmp_path / "out", keep=True)
        title = fig.texts[0].get_text()                      # the first text of the card is its title
        texts = [t.get_text() for t in _texts(fig) if t is not fig.texts[0]]
        assert number in title, (name, title)
        assert any(number in t for t in texts), (name, texts)
        plt.close(fig)
    s1 = pd.read_csv(rd / "fig_s1.csv").set_index("key")
    assert s1.loc["stat", "printed"] == "4.2 %" and s1.loc["stat", "source"] == "summary.json h2_stat"
    assert pd.read_csv(rd / "fig_s2.csv").set_index("key").loc["stat", "printed"] == "4.0×"
    assert pd.read_csv(rd / "fig_s3.csv").set_index("key").loc["points", "value"] == 12


def test_build_writes_the_three_cards(tmp_path):
    rd = results(tmp_path)
    paths = social_p2.build(rd, tmp_path / "social")
    assert [p.name for p in paths] == ["s1_h2_next_contract.png", "s2_h3_netting.png", "s3_h1_map.png"]
    assert all(p.exists() for p in paths)


def test_titles_have_no_dashes():
    import inspect

    src = inspect.getsource(social_p2)
    assert "—" not in src and "–" not in src
