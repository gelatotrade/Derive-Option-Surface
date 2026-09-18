from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import pytest  # noqa: E402

from derive_surface import figures_social  # noqa: E402
from tests.test_p1_figures import inputs  # noqa: E402

SLOTS = ["S1", "S2", "S3", "S4", "S5"]


def test_registry_covers_every_card():
    assert sorted(figures_social.CARDS) == SLOTS


@pytest.mark.parametrize("name", SLOTS)
def test_every_card_is_a_wide_png(tmp_path, name):
    paths = figures_social.CARDS[name](inputs(), tmp_path)
    assert [p.suffix for p in paths] == [".png"]
    png = paths[0]
    assert png.exists() and png.stat().st_size > 20_000
    from PIL import Image
    with Image.open(png) as im:
        assert im.size == (1600, 900), im.size


def test_type_is_large_enough_to_read_on_a_phone():
    assert figures_social.RC["font.size"] >= 15
    assert figures_social.RC["xtick.labelsize"] >= 13


def test_build_writes_every_card(tmp_path, monkeypatch):
    monkeypatch.setattr(figures_social, "load_inputs", lambda root, results_dir: inputs())
    out = figures_social.build("data/p1", "results/p1", tmp_path)
    assert sorted(out) == SLOTS


def test_takeaway_is_wrapped_so_it_cannot_leave_the_image(tmp_path):
    """A one-line takeaway ran off the right edge of every card until it was wrapped."""
    fig = figures_social._card("t", "word " * 60)
    texts = [t.get_text() for t in fig.texts]
    longest = max(len(line) for t in texts for line in t.split("\n"))
    assert longest <= 82
    matplotlib.pyplot.close(fig)


def test_the_print_style_cannot_change_the_card_size(tmp_path):
    """figstyle sets a tight bounding box for print; leaking it here silently resized every card."""
    from derive_surface import figstyle
    figstyle.use_style()
    paths = figures_social.CARDS["S1"](inputs(), tmp_path)
    from PIL import Image
    with Image.open(paths[0]) as im:
        assert im.size == (1600, 900), im.size
