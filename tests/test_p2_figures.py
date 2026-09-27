"""Registry of the Paper 2 figures (``derive_surface.figures_p2``): nine slots, type size, print size, greyscale.

Every slot is built from the synthetic results of its own test module (``tests/test_p2_fig_<slot>.py``), through the
registry, in a temporary results directory. The figures are caught at ``savefig`` so that every text artist can be
measured before the file is written.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import NamedTuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.figure  # noqa: E402
import matplotlib.text  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from matplotlib.colors import to_rgba  # noqa: E402

from derive_surface import figures_p2, p2cli  # noqa: E402
from derive_surface.p2params import Timeline  # noqa: E402

from tests import test_p2_fig_a1 as A1  # noqa: E402
from tests import test_p2_fig_f1 as F1  # noqa: E402
from tests import test_p2_fig_f2 as F2  # noqa: E402
from tests import test_p2_fig_f3 as F3  # noqa: E402
from tests import test_p2_fig_f4 as F4  # noqa: E402
from tests import test_p2_fig_f5 as F5  # noqa: E402
from tests import test_p2_fig_f6 as F6  # noqa: E402
from tests import test_p2_fig_t1 as T1  # noqa: E402
from tests import test_p2_fig_t2 as T2  # noqa: E402

SLOTS = ["t1", "t2", "f1", "f2", "f3", "f4", "f5", "f6", "a1"]
REPO = Path(__file__).resolve().parents[1]
REAL = REPO / "results" / "p2"
LUMINANCE_GAP = 0.15


# ---------------------------------------------------------------------------------------------- synthetic results

def _t1(rd: Path) -> dict:
    (rd / "params").mkdir(parents=True)
    pm2_old, pm2_new, sm = T1.pm2_params(0.17), T1.pm2_params(0.14), T1.sm_params()
    ts, day = T1.TS, T1.DAY
    (rd / "params" / "BTC_pm2.json").write_text(json.dumps([
        T1._entry(ts - 90 * day, pm2_old, None), T1._entry(ts - 28 * day, pm2_new, ["scenarios"]),
        T1._entry(ts - 10 * day, pm2_new, ["CollateralParameters"])]))
    (rd / "params" / "BTC_sm.json").write_text(json.dumps([T1._entry(ts - 400 * day, sm, None)]))
    base = T1.nodes()
    grid = pd.concat([T1.grid_for("pm2", pm2_new, base), T1.grid_for("sm", sm, base)], ignore_index=True)
    grid.to_csv(rd / T1.t1.GRID_FILE, index=False)
    expiries = [ts + int(d * day) for d in (1.0, 3.0, 8.0, 15.0, 22.0, 50.0, 99.0, 190.0)]
    (rd / T1.t1.META_FILE).write_text(json.dumps({"ccy": "BTC", "ts": ts, "block": 45_000_000,
                                                  "expiries": expiries}))
    return {}


def _t2(rd: Path) -> dict:
    (rd / "semantics").mkdir(parents=True)
    (rd / "params").mkdir()
    T2._factors().to_csv(rd / "semantics" / "factors.csv", index=False)
    params = {m: Timeline("BTC", m, root=REAL / "params").entry_at(T2.t2.REF_TS) for m in ("pm2", "sm")}
    for m, entry in params.items():
        (rd / "params" / f"BTC_{m}.json").write_text(json.dumps([entry]))
    row = T2._reference_row(params["pm2"]["params"], params["sm"]["params"])
    early = dict(row, day="2026-09-16", ts=row["ts"] - 86_400)
    pd.DataFrame([early, row]).to_csv(rd / "reference_book.csv", index=False)
    return {}


def _a1(rd: Path) -> dict:
    rd.mkdir(parents=True)
    v = A1._validation()
    v.to_csv(rd / "validation.csv", index=False)
    (rd / "validation_summary.json").write_text(json.dumps(A1._summary(v)))
    cap = rd.parent / "capital.parquet"
    A1._capital().to_parquet(cap)
    return {"capital_path": cap}


def _f5(rd: Path) -> dict:
    rd.mkdir(parents=True)
    ev = F5._events()
    ev.to_csv(rd / "events.csv", index=False)
    F5._params(rd / "params")
    F5._reference_book().to_csv(rd / "reference_book.csv", index=False)
    F5._oi().to_csv(rd / "manager_oi_share.csv", index=False)
    (rd / "h4.json").write_text(json.dumps(F5._h4(ev)))
    F5._placebo_days(ev).to_csv(rd / "h4_placebo_days.csv", index=False)
    return {}


def _f6(rd: Path) -> dict:
    panel, doses = F6._panel()
    F6._write(rd, panel, doses)
    pp = rd.parent / "h4_panel.parquet"
    panel.to_parquet(pp)
    return {"panel_path": pp}


def _no_extra(make):
    def run(rd: Path) -> dict:
        make(rd)
        return {}
    return run


SYNTH = {"t1": _t1, "t2": _t2, "a1": _a1, "f5": _f5, "f6": _f6, "f1": _no_extra(F1.synth),
         "f2": _no_extra(F2.synth), "f3": _no_extra(F3.make_results), "f4": _no_extra(F4.make_results)}


def synthetic(slot: str, tmp: Path) -> tuple:
    rd = tmp / f"results_{slot}"
    return rd, SYNTH[slot](rd)


def _text_3d(t) -> bool:
    from mpl_toolkits.mplot3d.art3d import Text3D

    return isinstance(t, Text3D)


def _outside(t, r, W: float, H: float) -> bool:
    e = t.get_window_extent(r)
    return e.width > 0 and (e.x0 < -0.5 or e.y0 < -0.5 or e.x1 > W + 0.5 or e.y1 > H + 0.5)


class Caught:
    """Figures passed to ``Figure.savefig`` during a build, measured before they are written."""

    def __init__(self):
        self.figures = []

    def texts(self, fig):
        fig.canvas.draw()
        out = []
        for t in fig.findobj(matplotlib.text.Text):
            if t.get_visible() and t.get_text().strip():
                out.append(t)
        return out


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """Every slot built once through the registry from synthetic results (figures caught at savefig)."""
    tmp = tmp_path_factory.mktemp("p2figs")
    mp = pytest.MonkeyPatch()
    caught = Caught()
    original = matplotlib.figure.Figure.savefig

    def savefig(self, *args, **kwargs):
        if all(f is not self for f in caught.figures):
            caught.figures.append(self)
            self._p2_small = [f"{t.get_text()!r} {t.get_fontsize():.2f}" for t in caught.texts(self)
                              if t.get_fontsize() < figures_p2.FS_MIN - 1e-9]
            self._p2_artists = _encodings(self)
            from derive_surface.figs_p2 import _kit_f5f6

            r = self.canvas.get_renderer()
            W, H = self.bbox.width, self.bbox.height
            self._p2_off = [t.get_text() for t in _kit_f5f6.texts(self)          # texts actually drawn
                            if not _text_3d(t) and _outside(t, r, W, H)]
        return original(self, *args, **kwargs)

    mp.setattr(matplotlib.figure.Figure, "savefig", savefig)
    out = {}
    try:
        for slot in SLOTS:
            n0 = len(caught.figures)
            rd, extra = synthetic(slot, tmp)
            paths = figures_p2.build([slot], tmp / "figures", rd, extra={slot: extra})[slot]
            out[slot] = {"paths": paths, "figures": caught.figures[n0:], "results": rd}
    finally:
        mp.undo()
    return out


# ---------------------------------------------------------------------------------------------- greyscale encodings

def _luminance(rgba) -> float:
    """Luminance of a colour composited on white (Rec. 709 weights on sRGB values, as the grey copies are made)."""
    r, g, b, a = rgba
    r, g, b = (a * c + (1.0 - a) for c in (r, g, b))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _chromatic(rgba) -> bool:
    r, g, b, a = rgba
    return a > 0 and max(r, g, b) - min(r, g, b) > 0.08


class Mark(NamedTuple):
    """One categorical colour on the canvas: the colour, what else tells the category apart in greyscale (``key``:
    kind of mark, dash pattern, marker, fill style, hatch), where it sits (``group``: its legend or its axes) and its
    drawn extent in pixels."""
    rgba: tuple
    key: tuple
    group: str
    legend: bool
    extent: tuple


def _dashes(line) -> str:
    offset, seq = line._unscaled_dash_pattern
    return "solid" if not seq else ",".join(f"{x:g}" for x in seq)


def _legend_members(fig) -> dict:
    """id of every artist inside a legend -> that legend's group name."""
    from matplotlib.legend import Legend

    out = {}
    for leg in fig.findobj(Legend):
        for x in leg.findobj():
            out[id(x)] = f"legend {id(leg)}"
    return out


def _extent(a, renderer) -> tuple:
    try:
        e = a.get_window_extent(renderer)
        return (float(e.x0), float(e.y0), float(e.x1), float(e.y1))
    except Exception:  # noqa: BLE001 - no extent: treated as everywhere
        return (-np.inf, -np.inf, np.inf, np.inf)


def _encodings(fig) -> list:
    """Categorical colour marks of a figure (see :class:`Mark`).

    A category is told apart by its colour and by everything the greyscale print keeps: the kind of mark, its dash
    pattern, marker and fill style, and the hatch of an area. Continuous colour maps (surfaces, meshes, colour-mapped
    collections) are no categories and are left out."""
    from matplotlib.collections import Collection, PathCollection, PolyCollection, QuadMesh
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    in_legend = _legend_members(fig)
    out = []
    for a in fig.findobj():
        if not getattr(a, "get_visible", lambda: False)() or a is fig.patch:
            continue
        found = []
        if isinstance(a, Line2D):
            mk = a.get_marker()
            n = len(a.get_xdata())
            ls_drawn = str(a.get_linestyle()) not in ("None", "none", " ", "") and a.get_linewidth() > 0
            mk_drawn = mk not in (None, "None", "none", "", " ") and n > 0
            if ls_drawn and n > 1:
                found.append((to_rgba(a.get_color(), a.get_alpha()), ("line", _dashes(a), str(mk) if mk_drawn
                                                                         else "")))
            if mk_drawn:
                face = to_rgba(a.get_markerfacecolor(), a.get_alpha())
                hollow = face[3] == 0 or _luminance(face) > 0.99
                colour = to_rgba(a.get_markeredgecolor(), a.get_alpha()) if hollow else face
                found.append((colour, ("marker", str(mk), a.get_fillstyle(), "hollow" if hollow else "filled",
                                       _dashes(a) if ls_drawn else "")))
        elif isinstance(a, Patch):
            fc = a.get_facecolor()
            if fc[3] > 0 or a.get_hatch():
                found.append((tuple(fc), ("area", a.get_hatch() or "")))
        elif isinstance(a, QuadMesh):
            continue
        elif isinstance(a, (PolyCollection, PathCollection)) and isinstance(a, Collection):
            fcs = np.atleast_2d(a.get_facecolor())
            if a.get_array() is None and len({tuple(np.round(c, 3)) for c in fcs}) <= 3:
                kind = "points" if isinstance(a, PathCollection) else "area"
                found += [(tuple(c), (kind, a.get_hatch() or "")) for c in {tuple(c) for c in fcs} if c[3] > 0]
        if found:
            legend = id(a) in in_legend
            ax = getattr(a, "axes", None)
            group = in_legend[id(a)] if legend else (f"axes {id(ax)}" if ax is not None else "figure")
            ext = _extent(a, r)
            out += [Mark(tuple(float(x) for x in rgba), key, group, legend, ext) for rgba, key in found]
    return out


def _overlap(a: tuple, b: tuple) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def colour_only_pairs(marks: list) -> list:
    """Pairs of different chromatic colours that nothing but the colour tells apart (same kind of mark, dash
    pattern, marker, fill style and hatch), that share a place (the same legend, or overlapping marks in the same
    axes), and that are less than 15 % apart in luminance."""
    marks = [m for m in marks if _chromatic(m.rgba)]
    bad = set()
    for i in range(len(marks)):
        for j in range(i + 1, len(marks)):
            a, b = marks[i], marks[j]
            if a.key != b.key or a.group != b.group:
                continue
            ca, cb = (tuple(round(x, 3) for x in m.rgba) for m in (a, b))
            if ca == cb or not (a.legend or _overlap(a.extent, b.extent)):
                continue
            gap = abs(_luminance(ca) - _luminance(cb))
            if gap < LUMINANCE_GAP:
                bad.add((a.key, min(ca, cb), max(ca, cb), round(gap, 3)))
    return sorted(bad)


# ---------------------------------------------------------------------------------------------- registry

def test_registry_has_the_nine_slots_in_the_order_of_the_paper():
    assert list(figures_p2.FIGURES) == SLOTS
    assert list(figures_p2.CAPTIONS) == SLOTS
    for slot, mod in figures_p2.FIGURES.items():
        assert mod.__name__ == f"derive_surface.figs_p2.{slot}"
        assert callable(mod.build) and mod.CHECKS, slot
        assert figures_p2.CAPTIONS[slot] == mod.CAPTION


def test_captions_are_english_without_dashes():
    for slot, cap in figures_p2.CAPTIONS.items():
        assert "—" not in cap and "–" not in cap, slot
        assert cap.isascii() or set(cap) - set(map(chr, range(128))) <= {"β", "ρ"}, slot


def test_unknown_slot_is_refused():
    with pytest.raises(KeyError):
        figures_p2.build(["t9"])


def test_cli_points_at_the_registry(capsys):
    assert p2cli.COMMANDS["figures"].module == "figures_p2"
    with pytest.raises(SystemExit):
        p2cli.main(["figures", "--help"])
    assert "build" in capsys.readouterr().out


# ---------------------------------------------------------------------------------------------- built figures

def test_every_slot_writes_pdf_png_and_its_tables(built):
    for slot in SLOTS:
        names = {Path(p).name for p in built[slot]["paths"]}
        assert {f"{slot}.pdf", f"{slot}.png"} <= names, slot
        assert any(Path(p).parent.name == "gray" and Path(p).name == f"{slot}.png" for p in built[slot]["paths"])
        assert any(re.fullmatch(rf"fig_{slot}(_[a-z0-9]+)?\.csv", n) for n in names), slot


def test_print_size_of_every_slot(built):
    for slot in SLOTS:
        w, h = figures_p2.SIZES[slot]
        pdf = next(Path(p) for p in built[slot]["paths"] if Path(p).name == f"{slot}.pdf")
        box = re.search(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", pdf.read_bytes())
        x0, y0, x1, y1 = (float(v) for v in box.groups())
        assert abs((x1 - x0) / 72 - w) <= 0.02 and abs((y1 - y0) / 72 - h) <= 0.02, (slot, (x1 - x0) / 72,
                                                                                       (y1 - y0) / 72)
        figs = built[slot]["figures"]
        assert figs and tuple(np.round(figs[0].get_size_inches(), 3)) == (w, h), slot


def test_no_type_under_seven_points_in_any_slot(built):
    small = {slot: f._p2_small for slot in SLOTS for f in built[slot]["figures"] if f._p2_small}
    assert small == {}


def test_exactly_one_slot_is_three_dimensional(built):
    three_d = [slot for slot in SLOTS if any(ax.name == "3d" for f in built[slot]["figures"] for ax in f.axes)]
    assert three_d == ["t1"]


def test_manager_colours_are_told_apart_in_greyscale_by_more_than_colour():
    """PM2, SM and legacy PM share hue families that fall within 15 % luminance of each other (Okabe-Ito blue,
    vermillion, green); section 6.2 double-codes them, so every pair differs in line style and marker."""
    from derive_surface.figs_p2 import _kit_f5f6, _kit_t2a1

    for manager in (_kit_f5f6.MANAGER, _kit_t2a1.MANAGER):
        items = list(manager.items())
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                (_, (_, ls_i, mk_i)), (_, (_, ls_j, mk_j)) = items[i], items[j]
                assert ls_i != ls_j and mk_i != mk_j


def test_category_colours_that_only_colour_tells_apart_differ_by_15_percent_luminance(built):
    """Greyscale test: within a figure, two categorical colours on marks of the same kind, line style, marker, fill
    style and hatch must be at least 15 % apart in luminance (composited on white)."""
    bad = {}
    for slot in SLOTS:
        for f in built[slot]["figures"]:
            pairs = colour_only_pairs(f._p2_artists)
            if pairs:
                bad[slot] = pairs
    assert bad == {}


def test_colour_only_pairs_catches_a_greyscale_clash():
    blue, vermillion, light = to_rgba("#0072B2"), to_rgba("#D55E00"), to_rgba("#009E73", 0.35)
    box, apart = (0, 0, 10, 10), (0, 20, 10, 30)

    def mark(rgba, key=("area", ""), group="axes 1", legend=False, extent=box):
        return Mark(rgba, key, group, legend, extent)

    assert colour_only_pairs([mark(blue), mark(vermillion)])                          # same place, colour only
    assert colour_only_pairs([mark(blue), mark(vermillion, key=("area", "////"))]) == []   # hatch tells apart
    assert colour_only_pairs([mark(blue), mark(light)]) == []                         # 35 % green is light enough
    assert colour_only_pairs([mark(blue), mark(vermillion, extent=apart)]) == []      # separate labelled rows
    assert colour_only_pairs([mark(blue, group="legend 1", legend=True, extent=box),
                              mark(vermillion, group="legend 1", legend=True, extent=apart)])  # one legend


# ---------------------------------------------------------------------------------------------- checks

def test_checks_of_every_slot_agree_on_synthetic_results(built):
    from derive_surface.figs_p2 import f6

    for slot in SLOTS:
        rd = built[slot]["results"]
        checks = f6.checks(rd.parent / "h4_panel.parquet") if slot == "f6" else None
        res = figures_p2.run_checks(slot, rd, checks=checks)
        assert len(res) == len(figures_p2.FIGURES[slot].CHECKS), slot
        failed = res.loc[~res["ok"], ["check", "error"]]
        assert failed.empty, (slot, failed.to_dict("records"))
        assert list(res.columns) == ["slot", "check", "figure", "source", "ok", "instruction", "error"]


# ---------------------------------------------------------------------------------------------- check script

def _check_script():
    import importlib.util

    spec = importlib.util.spec_from_file_location("p2_figure_check", REPO / "scripts" / "p2_figure_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_check_script_reports_caption_drift_without_changing_the_tex():
    chk = _check_script()
    caps = {"t1": r"\textbf{The surface.} Panel a has \PH{n} nodes.", "f3": "The next contract.",
            "a1": "Does it match?"}
    tex = (r"\begin{figure*}[t]\includegraphics[width=\linewidth]{figures/t1.pdf}"
           "\n  \\caption{\\textbf{The surface.} Panel a has\n  740 nodes.}\\label{fig:t1}\\end{figure*}\n"
           r"\begin{figure}[t]\includegraphics{figures/f3.pdf}\caption{The next {contract} — changed.}\end{figure}"
           "\n% \\begin{figure}\\includegraphics{figures/a1.pdf}\\caption{Does it match?}\\end{figure}\n")
    assert chk.tex_captions(tex)["t1"].startswith(r"\textbf{The surface.}")
    res = chk.compare_captions(tex, caps).set_index("slot")
    assert res.loc["t1", "status"] == "equal"                       # \PH{n} stands for 740
    assert res.loc["f3", "status"] == "differs" and "dash in main.tex" in res.loc["f3", "note"]
    assert res.loc["a1", "status"] == "missing"                       # commented out
    ex = [("f3", "The next contract.", r"The next {contract} — changed.", "reason")]
    assert chk.compare_captions(tex, caps, ex).set_index("slot").loc["f3", "status"] == "equal with exception"


def test_check_script_media_checks_compare_cards_with_their_sources(tmp_path):
    """Every number of a card is compared with its source (JSON key, one CSV row or summary.json); a source that
    does not resolve fails."""
    chk = _check_script()
    rd = tmp_path / "results"
    rd.mkdir()
    (rd / "summary.json").write_text(json.dumps({"h2_stat": 0.0345}))
    (rd / "h1.json").write_text(json.dumps({"stat": 0.9, "placebo": {"p95": 23.4}}))
    pd.DataFrame({"item": ["a", "b"], "value": [1.5, 2.5]}).to_csv(rd / "fig_x.csv", index=False)
    rows = [("stat", 0.0345, "3.5 %", "summary.json h2_stat"), ("b", 2.5, "2.5", "fig_x.csv:value@item=b"),
            ("p95", 23.4, "23.4", "h1.json:placebo.p95"), ("n", 12, "12", "fig_f2_b.csv rows")]
    pd.DataFrame(rows, columns=["key", "value", "printed", "source"]).to_csv(rd / "fig_s1.csv", index=False)
    pd.DataFrame([("stat", 0.91, "0.91", "h1.json:stat")],
                 columns=["key", "value", "printed", "source"]).to_csv(rd / "fig_s3.csv", index=False)
    res = chk.media_checks(rd)
    assert list(res["slot"]) == ["s1"] * 4 + ["s3"] and list(res["ok"]) == [True, True, True, False, False]


def test_caption_elements_must_be_drawn(tmp_path):
    chk = _check_script()
    rd = tmp_path / "results"
    rd.mkdir()
    pd.DataFrame({"kind": ["registered", "exploratory"]}).to_csv(rd / "fig_f2_c.csv", index=False)
    pd.DataFrame({"variant": ["ratio", "ratio"], "group": ["all", "label=M3"]}).to_csv(rd / "fig_f3_b.csv", index=False)
    tex = (r"\begin{figure}\includegraphics{figures/f2.pdf}\caption{Rows on grey; the grey band is the floor.}"
           r"\end{figure}" "\n"
           r"\begin{figure}\includegraphics{figures/f3.pdf}\caption{Rows per account and per parameter regime.}"
           r"\end{figure}")
    res = chk.element_checks(tex, rd)
    got = {r.check.split(":")[0]: r.ok for r in res.itertuples()}
    assert got == {'caption "grey band"': False, 'caption "per account"': True, 'caption "per parameter regime"': False}
    pd.DataFrame({"kind": ["registered", "band"]}).to_csv(rd / "fig_f2_c.csv", index=False)
    assert chk.element_checks(tex, rd).set_index("check").loc[
        'caption "grey band": a row of kind band (h1_sign.sign_floor)', "ok"]


def test_check_sheet_is_the_same_whatever_the_order_of_sets_and_mappings():
    """The F2 forest source was a mapping filled from a set, so FIGURE_CHECKS.md changed with the hash seed of the
    run; the sheet prints every set and every mapping sorted, nested ones included."""
    chk = _check_script()
    keys = ["sensitivity.json:b_mm", "h1.json", 10, "sensitivity.json:a_maps", 2.5]

    def sheet(order):
        checks = pd.DataFrame([
            chk._row("f2", "forest rows", {k: (1, 2) for k in order}, set(order), True),
            chk._row("f5", "ids", frozenset(order), {k: {"b": 1, "a": {3, 1, 2}} for k in order}, True)])
        shapes = pd.DataFrame(columns=["what", "figure", "target", "ok"])
        captions = pd.DataFrame(columns=["slot", "status", "note"])
        text = chk.sheet(checks, shapes, captions, Path("results/p2"))
        return "\n".join(line for line in text.splitlines() if not line.startswith("Generated "))

    first = sheet(keys)
    assert all(sheet(order) == first for order in (keys[::-1], keys[2:] + keys[:2], sorted(keys, key=str)))
    assert chk._cell({"b": 1, 10: 2, "a": 3, 2.5: 4}) == "{2.5: 4, 10: 2, a: 3, b: 1}"  # numbers first, then text
    assert chk._cell({"x", "b", "a"}) == "[a, b, x]"
    assert chk._cell({"k": [{"z": 1, "y": 2}, frozenset({3, 1})]}) == "{k: [{y: 2, z: 1}, [1, 3]]}"
    assert chk._cell([3, 1, 2]) == "[3, 1, 2]"  # a list keeps its order


# ---------------------------------------------------------------------------------------------- set in the paper

def test_print_width_is_the_width_main_tex_sets_the_figure_at():
    """A48: cas-dc sets figure* at the text width (494.50888 pt) and figure at the column width (238.25444 pt, TeX
    points); with width=\\linewidth a 7.0 or 3.4 in canvas shrank by 2.3 or 3.0 per cent, and 7 pt type printed at
    6.8 pt. The canvases are the widths a hair under the set width, so the scale in the paper is at least one."""
    from derive_surface.figs_p2 import _print

    assert _print.TEXTWIDTH_IN == pytest.approx(6.8425, abs=1e-4)
    assert _print.COLUMNWIDTH_IN == pytest.approx(3.2967, abs=1e-4)
    for slot, (w, _) in figures_p2.SIZES.items():
        placed = _print.COLUMNWIDTH_IN if slot in ("f3", "f4") else _print.TEXTWIDTH_IN
        assert 1.0 <= placed / w <= 1.003, slot


def test_to_print_sets_the_canvas_once():
    from derive_surface.figs_p2 import _print

    fig = matplotlib.figure.Figure(figsize=(7.0, 4.2))
    _print.to_print(fig)
    assert tuple(np.round(fig.get_size_inches(), 3)) == (6.84, 4.2)
    _print.to_print(fig)
    assert tuple(np.round(fig.get_size_inches(), 3)) == (6.84, 4.2)
    with pytest.raises(ValueError):
        _print.to_print(matplotlib.figure.Figure(figsize=(5.0, 2.0)))


def test_saved_figures_keep_every_text_on_the_canvas(built):
    """After the canvas is set to the print width, nothing leaves it."""
    off = {slot: f._p2_off for slot in SLOTS for f in built[slot]["figures"] if f._p2_off}
    assert off == {}


def test_check_script_measures_the_type_as_main_tex_sets_it(tmp_path):
    """A48: the check reads the width main.tex gives each figure and the smallest type in its PDF; 7 pt on a 7.0 in
    canvas set at the text width prints at 6.84 pt and fails, on a 6.84 in canvas it passes."""
    pytest.importorskip("fitz")
    import matplotlib.pyplot as plt

    chk = _check_script()
    figs = tmp_path / "figures"
    figs.mkdir()
    for name, w in (("wide", 7.0), ("fit", 6.84), ("col", 3.29)):
        fig = plt.figure(figsize=(w, 1.0))
        fig.text(0.1, 0.5, "seven points", fontsize=7.0)
        fig.savefig(figs / f"{name}.pdf")
        plt.close(fig)
    tex = "\n".join(rf"\begin{{{env}}}\includegraphics[width=\linewidth]{{figures/{n}.pdf}}\caption{{x}}\end{{{env}}}"
                    for env, n in (("figure*", "wide"), ("figure*", "fit"), ("figure", "col")))
    res = chk.placement_checks(tex, figs).set_index("what")
    assert not res.loc["wide.pdf set in main.tex", "ok"]
    assert res.loc["fit.pdf set in main.tex", "ok"] and res.loc["col.pdf set in main.tex", "ok"]


def test_build_script_can_read_every_module_caption():
    """``scripts/p2_build.py`` compares main.tex with the CAPTION of each slot module, read without importing it; a
    caption it cannot evaluate would drop out of that comparison unnoticed."""
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("p2_build_for_captions", REPO / "scripts" / "p2_build.py")
    build = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = build                       # dataclasses of the script look their module up
    try:
        spec.loader.exec_module(build)
    finally:
        sys.modules.pop(spec.name, None)
    for slot in SLOTS:
        cap = build.module_caption(REPO / "derive_surface" / "figs_p2" / f"{slot}.py")
        assert cap is not None and build._norm(cap) == build._norm(figures_p2.CAPTIONS[slot]), slot
