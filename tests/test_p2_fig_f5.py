"""F5 of Paper 2 (the engine over time): smoke test on synthetic mini data in a temporary results directory.

Checks the canvas (7.0 x 4.3 in, PDF at print size), the type size (nothing under 7 pt), that every text stays on the
canvas, the status grammar of the event symbols, the pure parameter jumps and the check list against the sources.
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

from derive_surface.figs_p2 import _kit_f5f6 as kit  # noqa: E402
from derive_surface.figs_p2 import f5  # noqa: E402

DAY = 86_400


def _ts(s: str) -> int:
    return int(pd.Timestamp(s, tz="UTC").timestamp())


EVENTS = [  # ccy, manager, event_utc, kept, panel_cells, jump (log-%)
    ("BTC", "pm", "2024-06-12 00:01:27", False, 0, 0.0),
    ("BTC", "pm", "2025-02-22 19:52:37", True, 25, -18.56),
    ("BTC", "pm2", "2026-01-08 22:50:49", True, 25, 1.60),
    ("BTC", "pm2", "2026-01-23 04:24:05", True, 27, -10.49),
    ("ETH", "pm2", "2025-10-10 22:55:31", False, 0, 0.0),
    ("ETH", "pm2", "2026-05-24 04:05:07", True, 54, -3.36),
    ("HYPE", "pm2", "2026-01-08 22:50:49", True, 0, 1.54),
    ("HYPE", "pm2", "2026-05-08 12:24:23", True, 29, -7.43),
]


def _events() -> pd.DataFrame:
    rows = []
    for ccy, m, utc, kept, cells, _ in EVENTS:
        ts = _ts(utc)
        day = utc[:10]
        rows.append({"ccy": ccy, "manager": m, "event_ts": ts, "kinds": "MarginParameters", "max_abs_dose": 0.1,
                     "kept": kept, "event_id": f"{ccy}-{m}-{day.replace('-', '')}", "event_utc": utc,
                     "event_day": day, "last_ts": ts, "n_changes": 1, "n_dose_fills": 10, "n_valid": 10,
                     "n_nonpos": 0, "n_nan": 0, "n_cells": 30, "panel_cells": cells, "panel_fills_pre": 0,
                     "panel_fills_post": 0})
    return pd.DataFrame(rows)


def _params(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    starts = {"pm": "2023-12-04 16:00", "pm2": "2025-06-09 05:18"}
    for ccy, managers in (("BTC", ("pm", "pm2")), ("ETH", ("pm", "pm2")), ("HYPE", ("pm2",))):
        for m in managers:
            if ccy == "HYPE":
                start = "2025-10-16 10:00"
            else:
                start = starts[m]
            ts = [_ts(start), _ts(start) + 5 * DAY]
            ts += [_ts(u) for c, mm, u, *_ in EVENTS if c == ccy and mm == m]
            ts += [_ts("2025-09-01 12:00")] if m == "pm2" else []
            rows = [{"from_block": i, "from_ts": t, "from_utc": "", "source": "test", "params": {}, "lib": "0x",
                     "changed": ["MarginParameters"]} for i, t in enumerate(sorted(set(ts)))]
            (root / f"{ccy}_{m}.json").write_text(json.dumps(rows))
    (root / "HYPE_pm.json").write_text("[]")


def _reference_book() -> pd.DataFrame:
    rows = []
    for ccy, start in (("BTC", "2024-01-11"), ("ETH", "2024-01-11"), ("HYPE", "2025-11-11")):
        k = {"sm": 30.0, "pm": 24.0, "pm2": 14.4}
        pts = {"sm": 1.0, "pm": 1.0, "pm2": 1.0}
        evs = [(pd.Timestamp(u[:10]) + pd.Timedelta(days=0 if int(u[11:13]) < 8 else 1), m, j, _ts(u))
               for c, m, u, _, _, j in EVENTS if c == ccy]
        for i, d in enumerate(pd.date_range(start, "2026-09-17", freq="D")):
            ts = int(d.tz_localize("UTC").timestamp()) + 8 * 3600
            fwd = 50_000.0 * (1 + 0.1 * np.sin(i / 40))
            row = {"ccy": ccy, "day": d.strftime("%Y-%m-%d"), "ts": ts, "tenor_days": 21 + i % 15, "forward": fwd}
            for m in ("sm", "pm", "pm2"):
                prev_k, prev_pts = k[m], pts[m]
                for day, mm, j, ets in evs:
                    if mm == m and day == d:
                        k[m] = k[m] * np.exp(j / 100)
                        pts[m] = float(ets)
                live = not (m == "pm2" and d < pd.Timestamp("2025-06-13")) and not (m == "pm" and ccy == "HYPE")
                row[f"K_{m}"] = k[m] * fwd / 100 if live else np.nan
                row[f"K_{m}_prev"] = prev_k * fwd / 100 if live else np.nan
                row[f"{m}_param_ts"] = pts[m] if live else np.nan
                row[f"{m}_param_ts_prev"] = prev_pts if live else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def _oi() -> pd.DataFrame:
    rows = []
    for ccy, first in (("BTC", "2024-01"), ("ETH", "2024-02"), ("HYPE", "2025-12")):
        for i, mth in enumerate(pd.period_range(first, "2026-09", freq="M")):
            pm2 = 0.0 if str(mth) < "2025-06" else min(0.9, 0.1 + 0.05 * i)
            pm = np.nan if ccy == "HYPE" else (0.0 if str(mth) >= "2026-02" else 0.5 * (1 - pm2))
            sm = 1 - pm2 - (0 if np.isnan(pm) else pm)
            rows.append({"month": str(mth), "ccy": ccy, "sm": sm, "pm": pm, "pm2": pm2})
    return pd.DataFrame(rows)


def _h4(events: pd.DataFrame) -> dict:
    kept = events[events["kept"]]
    return {"hypothesis": "H4", "n": 900, "fills": 850, "cell_events": int(kept["panel_cells"].sum()),
            "placebo": {"admissible_days": {e: {"days": 3, "first": "2025-07-16", "last": "2025-07-18"}
                                            for e in kept["event_id"]}}}


def _placebo_days(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for e in events[events["kept"]].itertuples():
        for k, day in enumerate(["2025-07-15", "2025-07-16", "2025-07-17", "2025-07-18"]):
            rows.append({"timeline": e.event_id, "ccy": e.ccy, "manager": e.manager, "day": day,
                         "admissible": k > 0, "drawn_count": 1 if k == 2 else 0})
    return pd.DataFrame(rows)


@pytest.fixture()
def results(tmp_path: Path) -> Path:
    rd = tmp_path / "results"
    rd.mkdir()
    ev = _events()
    ev.to_csv(rd / "events.csv", index=False)
    _params(rd / "params")
    _reference_book().to_csv(rd / "reference_book.csv", index=False)
    _oi().to_csv(rd / "manager_oi_share.csv", index=False)
    (rd / "h4.json").write_text(json.dumps(_h4(ev)))
    _placebo_days(ev).to_csv(rd / "h4_placebo_days.csv", index=False)
    return rd


def _pdf_width_in(path: Path) -> float:
    m = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", path.read_bytes())
    return float(m.group(1)) / 72.0


def test_figure_size_type_size_and_canvas(results):
    fig = f5.figure(results)
    assert tuple(np.round(fig.get_size_inches(), 3)) == (7.0, 4.3)
    assert kit.small_texts(fig) == []
    assert kit.texts_off_canvas(fig) == []
    assert kit.overlapping_texts(fig) == []


def test_build_writes_pdf_png_and_tables(results, tmp_path):
    out = tmp_path / "fig"
    paths = f5.build(out_dir=out, results_dir=results)
    assert {p.name for p in paths} >= {"f5.pdf", "f5.png"}
    assert _pdf_width_in(out / "f5.pdf") == pytest.approx(7.0, abs=0.02)
    from PIL import Image
    with Image.open(out / "f5.png") as im:
        assert im.size == (2800, 1720)
    for name in ("fig_f5_a.csv", "fig_f5_b.csv", "fig_f5_c.csv"):
        assert (results / name).exists()


def test_status_grammar_jumps_and_windows(results):
    f5.build(out_dir=results.parent / "fig", results_dir=results)
    b = pd.read_csv(results / "fig_f5_b.csv")
    ev = b[b["mark"] == "event"].set_index("event_id")
    assert len(ev) == len(EVENTS)
    assert set(ev.index[ev["status"] == "panel"]) == {"BTC-pm-20250222", "BTC-pm2-20260108", "BTC-pm2-20260123",
                                                      "ETH-pm2-20260524", "HYPE-pm2-20260508"}
    assert list(ev.index[ev["status"] == "kept_no_cell"]) == ["HYPE-pm2-20260108"]
    assert set(ev.index[ev["status"] == "dropped"]) == {"BTC-pm-20240612", "ETH-pm2-20251010"}
    for ccy, m, utc, _, _, j in EVENTS:
        eid = f"{ccy}-{m}-{utc[:10].replace('-', '')}"
        assert ev.loc[eid, "jump_logpct"] == pytest.approx(j, abs=1e-9)
    assert ev.loc["BTC-pm2-20260123", "printed"] == "−10"
    assert ev.loc["BTC-pm-20240612", "printed"] == "0"
    assert ev.loc["BTC-pm2-20260108", "printed"] == "+2"
    # the earlier of two events less than 30 days apart carries its number on the left
    assert ev.loc["BTC-pm2-20260108", "label_side"] == "left"
    assert ev.loc["BTC-pm2-20260123", "label_side"] == "right"
    kept = ev[ev["status"] != "dropped"]
    assert (kept["window_hi"] - kept["window_lo"] == 28 * DAY).all()
    assert ev.loc[ev["status"] == "dropped", "window_lo"].isna().all()
    rows = b[b["mark"] == "timeline_row"]
    for rail, n in rows.groupby("rail").size().items():
        ccy, m = rail.split()[0], "pm2" if rail.endswith("PM2") else "pm"
        assert n == len(json.loads((results / "params" / f"{ccy}_{m}.json").read_text()))
    pl = b[b["mark"] == "placebo_day"]
    assert set(pl.groupby("rail").size()) == {3}


def test_panel_a_fills_missing_legacy_share_and_panel_c_values(results):
    f5.build(out_dir=results.parent / "fig", results_dir=results)
    a = pd.read_csv(results / "fig_f5_a.csv")
    assert a["pm"].notna().all()
    assert np.allclose(a[["sm", "pm", "pm2"]].sum(axis=1), 1.0)
    c = pd.read_csv(results / "fig_f5_c.csv")
    btc = c[(c["ccy"] == "BTC")].sort_values("day")
    assert btc["drawn"].all() and not c.loc[c["ccy"] != "BTC", "drawn"].any()
    assert btc.loc[btc["day"] < "2025-06-13", "K_pm2_pct"].isna().all()
    last = btc.iloc[-1]
    rb = pd.read_csv(results / "reference_book.csv")
    r = rb[(rb["ccy"] == "BTC") & (rb["day"] == "2026-09-17")].iloc[0]
    assert last["K_sm_pct"] == pytest.approx(100 * r["K_sm"] / r["forward"])
    assert isinstance(last["printed"], str) and last["printed"].startswith("SM ")
    thin = btc.set_index("day")["legacy_thin"]
    assert not thin["2024-06-01"] and thin["2026-03-01"]


def test_without_placebo_day_table_only_the_count_is_printed(results):
    (results / "h4_placebo_days.csv").unlink()
    fig = f5.figure(results)
    assert kit.small_texts(fig) == [] and kit.texts_off_canvas(fig) == []
    f5.build(out_dir=results.parent / "fig", results_dir=results)
    b = pd.read_csv(results / "fig_f5_b.csv")
    assert (b["mark"] == "placebo_day").sum() == 0
    assert (b.loc[b["mark"] == "rail", "placebo_days"] == 3).sum() == 4      # ETH legacy PM has no kept event here


def test_checks_agree_on_synthetic_results(results):
    f5.build(out_dir=results.parent / "fig", results_dir=results)
    res = kit.run_checks(f5.CHECKS, results, with_expected=False)
    assert res["error"].eq("").all(), res.loc[res["error"] != "", ["id", "error"]]
    assert res["agrees"].all(), res.loc[~res["agrees"], ["id", "figure", "source"]]


def test_caption_has_no_dashes():
    assert "—" not in f5.CAPTION and "–" not in f5.CAPTION and " - " not in f5.CAPTION
    assert f5.CAPTION.startswith("\\textbf{The engine over time.}")
