from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from derive_surface import figstyle  # noqa: E402


def test_column_widths_match_the_cas_layout():
    assert figstyle.SINGLE == pytest.approx(3.4)
    assert figstyle.DOUBLE == pytest.approx(7.0)


def test_palette_is_okabe_ito_and_long_enough_for_every_class():
    assert len(figstyle.PALETTE) >= 8
    assert all(c.startswith("#") and len(c) == 7 for c in figstyle.PALETTE)
    assert len(set(figstyle.PALETTE)) == len(figstyle.PALETTE)
    assert set(figstyle.CLASS_COLORS) == {"vault", "rfq", "dominant_maker", "mm_programme", "large", "other"}
    assert len(set(figstyle.CLASS_COLORS.values())) == 6
    assert set(figstyle.CLASS_LABELS) == set(figstyle.CLASS_COLORS)


def test_figure_applies_the_style_and_size():
    fig, ax = figstyle.figure(figstyle.SINGLE, 2.0)
    assert fig.get_size_inches() == pytest.approx([3.4, 2.0])
    assert matplotlib.rcParams["font.size"] == pytest.approx(8.0)
    assert not ax.spines["top"].get_visible() and not ax.spines["right"].get_visible()
    matplotlib.pyplot.close(fig)


def test_save_writes_pdf_and_png(tmp_path):
    fig, ax = figstyle.figure(figstyle.SINGLE, 2.0)
    ax.plot([0, 1], [0, 1])
    paths = figstyle.save(fig, "test_fig", tmp_path)
    assert sorted(p.suffix for p in paths) == [".pdf", ".png"]
    assert all(p.exists() and p.stat().st_size > 1000 for p in paths)
    assert (tmp_path / "test_fig.pdf").exists()


def test_robust_limits_ignores_the_tails():
    values = np.concatenate([np.random.default_rng(0).normal(0, 1, 10_000), [1e6, -1e6]])
    lo, hi = figstyle.robust_limits(values, q=0.99, pad=0.0)
    assert -6 < lo < -1 and 1 < hi < 6


def test_robust_limits_handles_nan_and_constant_input():
    lo, hi = figstyle.robust_limits(np.array([np.nan, 5.0, 5.0]))
    assert lo < 5.0 < hi
    assert figstyle.robust_limits(np.array([np.nan, np.nan])) == (0.0, 1.0)


def test_money_and_vol_formatters():
    assert figstyle.money(1234.5) == "1,234" or figstyle.money(1234.5) == "1,235"
    assert figstyle.money(-0.4) == "-0.40"
    assert figstyle.vol(2.5) == "2.5"
