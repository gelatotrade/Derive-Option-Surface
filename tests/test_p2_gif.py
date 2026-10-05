"""GIF of the BTC PM2 capital surface (``derive_surface.gif_p2``): frame plan, banners, one frame, writer, build."""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.text  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from derive_surface import gif_p2, p2surface  # noqa: E402

DAY = 86_400
EVENTS = [  # event_id, event_utc, kinds, kept
    ("BTC-pm2-20251010", "2025-10-10 22:55:31", "OtherContingencyParameters", False),
    ("BTC-pm2-20260108", "2026-01-08 22:50:49", "MarginParameters", True),
    ("BTC-pm2-20260123", "2026-01-23 04:24:05", "scenarios", True),
    ("BTC-pm2-20260524", "2026-05-24 04:05:07",
     "BasisContingencyParameters+OtherContingencyParameters+VolShockParameters+scenarios", True),
    ("BTC-pm2-20260820", "2026-08-20 22:09:25",
     "BasisContingencyParameters+OtherContingencyParameters+VolShockParameters+scenarios", True),
]
JUMPS = {"BTC-pm2-20260108": 1.60, "BTC-pm2-20260123": -10.49, "BTC-pm2-20260524": -7.84, "BTC-pm2-20260820": -26.05}


def _ts(s: str) -> int:
    return int(pd.Timestamp(s, tz="UTC").timestamp())


def events() -> pd.DataFrame:
    rows = []
    for eid, utc, kinds, kept in EVENTS:
        rows.append({"ccy": "BTC", "manager": "pm2", "event_ts": _ts(utc), "kinds": kinds, "kept": kept,
                     "event_id": eid, "event_utc": utc, "event_day": utc[:10]})
    rows.append({"ccy": "ETH", "manager": "pm2", "event_ts": _ts("2026-01-23 04:24:05"), "kinds": "scenarios",
                 "kept": True, "event_id": "ETH-pm2-20260123", "event_utc": "2026-01-23 04:24:05",
                 "event_day": "2026-01-23"})
    return pd.DataFrame(rows)


def reference_book() -> pd.DataFrame:
    """Daily BTC reference book whose PM2 capital jumps by the log-% of ``JUMPS`` on the first day after an event."""
    days = pd.date_range("2025-06-01", "2026-09-17", freq="D")
    stamp, k, rows = 1_000, 1_450.0, []
    jump_day = {}
    for eid, utc, _, kept in EVENTS:
        if kept:
            t = _ts(utc)
            d = pd.Timestamp(t, unit="s").normalize() + pd.Timedelta(hours=8)
            jump_day[(d if d.timestamp() >= t else d + pd.Timedelta(days=1)).strftime("%Y-%m-%d")] = JUMPS[eid]
    for d in days:
        day = d.strftime("%Y-%m-%d")
        prev_stamp, prev_k = stamp, k
        if day in jump_day:
            stamp, k = stamp + 1, k * np.exp(jump_day[day] / 100.0)
            prev_k = k / np.exp(jump_day[day] / 100.0)
        rows.append({"ccy": "BTC", "day": day, "ts": p2surface._day_ts(day), "forward": 1e4,
                     "K_sm": 2_960.0, "K_sm_prev": 2_960.0, "sm_param_ts": 1, "sm_param_ts_prev": 1,
                     "K_pm": 1_960.0, "K_pm_prev": 1_960.0, "pm_param_ts": 2, "pm_param_ts_prev": 2,
                     "K_pm2": k, "K_pm2_prev": prev_k, "pm2_param_ts": stamp, "pm2_param_ts_prev": prev_stamp})
    return pd.DataFrame(rows)


def grid(ts: int, level: float = 1.0, tenors=None) -> pd.DataFrame:
    deltas = np.round(np.arange(0.05, 0.95 + 1e-9, 0.025), 3)
    tenors = p2surface.ANIM_DAYS if tenors is None else np.asarray(tenors)
    D, T = np.meshgrid(deltas, tenors)
    iv = 0.40 + 0.6 * (D - 0.5) ** 2 + 0.05 / np.sqrt(T)
    kbp = level * (400 + 900 * np.exp(-((D - 0.5) ** 2) / 0.05) * (0.6 + 0.4 * np.log10(T) / np.log10(365)))
    return pd.DataFrame({"manager": "pm2", "side": "short", "ts": ts, "delta": D.ravel(), "tenor_days": T.ravel(),
                         "iv": iv.ravel(), "K_per_forward_bp": kbp.ravel(), "K": kbp.ravel() * 7.6,
                         "forward": 76_000.0})


# ---------------------------------------------------------------------------------------------- plan and banners

def test_weekly_plan_has_the_first_day_wednesdays_events_and_the_t1_block():
    ev = gif_p2.kept_events(events())
    assert list(ev["event_id"]) == list(JUMPS)                     # kept BTC PM2 only, by time
    plan = gif_p2.frame_plan(ev)
    assert plan["ts"].is_monotonic_increasing and plan["ts"].is_unique
    assert plan["ts"].iloc[0] == _ts("2025-06-13 08:00") and plan["kind"].iloc[0] == "first"
    assert plan["ts"].iloc[-1] == 1_789_632_000 and plan["kind"].iloc[-1] == "last"   # the T1 block
    regular = plan[plan["kind"] == "regular"]
    assert len(regular) == 66 and set(pd.to_datetime(regular["day"]).dt.weekday) == {2}
    assert (plan["kind"].isin(["before", "after", "next"])).sum() == 12
    assert len(plan) == 80
    for e in ev.itertuples():
        f = plan[plan["event_id"] == e.event_id].set_index("kind")["ts"]
        assert f["before"] < e.event_ts <= f["after"] and f["next"] == f["after"] + DAY
        assert f["after"] - e.event_ts < DAY
    assert plan.loc[plan["kind"] == "after", "hold"].eq(gif_p2.HOLD).all()
    assert plan["hold"].iloc[-1] == gif_p2.END_HOLD and plan.loc[plan["kind"] == "regular", "hold"].eq(1).all()


def test_daily_plan_has_every_day():
    plan = gif_p2.frame_plan(gif_p2.kept_events(events()), step="daily")
    days = pd.date_range("2025-06-13", "2026-09-17", freq="D")
    assert len(plan) == len(days) and plan["kind"].eq("after").sum() == 4
    with pytest.raises(ValueError):
        gif_p2.frame_plan(gif_p2.kept_events(events()), step="monthly")


def test_steps_in_simple_per_cent():
    assert [gif_p2.fmt_step(gif_p2.step_pct(v)) for v in JUMPS.values()] == ["+1.6 %", "−10 %", "−7.5 %", "−23 %"]
    assert gif_p2.fmt_step(float("nan")) == "n/a"


def test_event_words():
    assert gif_p2.event_words("MarginParameters") == "margin parameters"
    assert gif_p2.event_words("scenarios") == "scenario weights"
    bundle = "BasisContingencyParameters+OtherContingencyParameters+VolShockParameters+scenarios"
    assert gif_p2.event_words(bundle) == "parameter bundle"
    assert gif_p2.event_words(bundle, (0.17, 0.14)) == "parameter bundle incl. spot grid ±17 % → ±14 %"
    assert gif_p2.event_words("VolShockParameters+scenarios") == "vol shocks, scenarios"
    assert gif_p2.banner_lines("20 Aug 2026 · parameter bundle · straddle −23 %") == [
        "20 Aug 2026 · straddle −23 %", "parameter bundle"]


def test_banners_read_the_step_from_the_reference_book():
    ev = gif_p2.kept_events(events())
    b = gif_p2.banners(ev, reference_book(), lambda ts: (0.17, 0.14) if ts == _ts("2026-08-20 22:09:25") else None)
    assert list(b["printed_step"]) == ["+1.6 %", "−10 %", "−7.5 %", "−23 %"]
    np.testing.assert_allclose(b["jump_logpct"], list(JUMPS.values()), atol=1e-9)
    assert b["banner"].iloc[0] == "8 Jan 2026 · margin parameters · straddle +1.6 %"
    assert b["banner"].iloc[1] == "23 Jan 2026 · scenario weights · straddle −10 %"
    assert "spot grid ±17 % → ±14 %" in b["banner"].iloc[3] and b["banner"].iloc[3].endswith("−23 %")


def test_atm_node_and_limits():
    g = grid(1_789_632_000)
    node = g[np.isclose(g["delta"], 0.5)].iloc[(g.loc[np.isclose(g["delta"], 0.5), "tenor_days"] - 30.44).abs()
                                                .argmin()]
    assert gif_p2.atm_pct(g) == pytest.approx(node["K_per_forward_bp"] / 100)
    assert np.isnan(gif_p2.atm_pct(None))
    lim = gif_p2.limits([g, grid(0, 1.2)])
    assert lim["clim"][0] <= 4.0 and lim["clim"][1] >= 12.0
    assert lim["clim"][0] * 2 == int(lim["clim"][0] * 2) and lim["clim"][1] * 2 == int(lim["clim"][1] * 2)


# ---------------------------------------------------------------------------------------------- one frame

def _frame_fig(**kw):
    ev = gif_p2.kept_events(events())
    marks = gif_p2.banners(ev, reference_book())
    series = gif_p2.reference_series(reference_book())
    g = grid(1_789_632_000, tenors=p2surface.ANIM_DAYS[2:18])            # outside tenors: grey floor
    lim = gif_p2.limits([g])
    return gif_p2.render(g, ts=1_789_632_000, lim=lim, series=series, marks=marks, sm_atm=14.08,
                         return_figure=True, **kw)


def test_frame_size_type_and_canvas():
    fig = _frame_fig(banner="20 Aug 2026 · parameter bundle incl. spot grid ±17 % → ±14 % · straddle −23 %",
                     left_out=2)
    assert tuple(np.round(fig.get_size_inches() * fig.dpi)) == (gif_p2.WIDTH, gif_p2.HEIGHT)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    texts = [t for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text().strip()]
    px = {t.get_text(): t.get_fontsize() * fig.dpi / 72 for t in texts}
    assert min(px.values()) >= 22 - 1e-9, sorted(px.items(), key=lambda kv: kv[1])[:3]
    date = [t for t in texts if "UTC" in t.get_text()]
    banner = [t for t in texts if "straddle −23 %" in t.get_text() and "\n" in t.get_text()]
    assert banner and banner[0].get_text() == ("20 Aug 2026 · straddle −23 %\n"
                                               "parameter bundle incl. spot grid ±17 % → ±14 %")
    assert date and banner and all(px[t.get_text()] >= 32 for t in date + banner)
    assert any("2 expiries without fresh feed left out" == t.get_text() for t in texts)
    assert any(t.get_text().startswith("ATM 30 d short: PM2 ") and t.get_text().endswith("SM, same contract, 14.1 %")
               for t in texts)
    from mpl_toolkits.mplot3d.art3d import Text3D

    for t in texts:
        if isinstance(t, Text3D):                  # projected only while drawn; the axes keep them inside
            continue
        e = t.get_window_extent(r)
        assert e.x0 >= -1 and e.y0 >= -1 and e.x1 <= gif_p2.WIDTH + 1 and e.y1 <= gif_p2.HEIGHT + 1, t.get_text()
    plt.close(fig)


def test_render_returns_rgb_of_the_master_size():
    ev = gif_p2.kept_events(events())
    rgb = gif_p2.render(grid(1_789_632_000), ts=1_789_632_000, lim=gif_p2.limits([grid(0)]),
                        series=gif_p2.reference_series(reference_book()), marks=gif_p2.banners(ev, reference_book()))
    assert rgb.shape == (gif_p2.HEIGHT, gif_p2.WIDTH, 3) and rgb.dtype == np.uint8


def test_write_gif_holds_frames_by_duration(tmp_path):
    frames = [np.full((40, 60, 3), v, dtype=np.uint8) for v in (252, 90, 180)]
    path = gif_p2.write_gif(frames, [1, 6, 8], tmp_path / "x.gif")
    with Image.open(path) as im:
        durations = []
        for i in range(im.n_frames):
            im.seek(i)
            durations.append(im.info["duration"])
    assert durations == [250, 1500, 2000]
    with Image.open(path) as im:
        im.seek(0)
        assert im.convert("RGB").getpixel((0, 0)) == (255, 255, 255)    # near white snaps to paper white


# ---------------------------------------------------------------------------------------------- build

def test_build_writes_gif_poster_table_and_meta(tmp_path, monkeypatch):
    rd = tmp_path / "results"
    rd.mkdir()
    events().to_csv(rd / "events.csv", index=False)
    reference_book().to_csv(rd / "reference_book.csv", index=False)
    last = grid(1_789_632_000)
    last.to_csv(rd / "t1_grid.csv", index=False)

    def fake_compute(plan, **kw):
        out = []
        for i, ts in enumerate(plan["ts"]):
            skip = i == 3
            g = None if skip else (last if ts == 1_789_632_000 else grid(int(ts), 1.3 - 0.3 * i / len(plan)))
            out.append({"ts": int(ts), "grid": g, "sm": None if skip else grid(int(ts), 1.4), "n_expiries": 0 if skip
                        else 12, "n_left_out": 1 if i == 5 else 0, "skipped": "no live expiry" if skip else ""})
        return out

    monkeypatch.setattr(gif_p2, "compute", fake_compute)
    monkeypatch.setattr(gif_p2, "grid_widths", lambda ccy, ts: None)
    meta = gif_p2.build(start="2026-08-01", end="2026-09-17", out=tmp_path / "media" / "g.gif", results_dir=rd)
    tab = pd.read_csv(rd / gif_p2.FRAMES_CSV)
    assert meta["frames"] == len(tab) - 1 and meta["skipped"] == 1
    assert (tmp_path / "media" / "g.gif").stat().st_size == meta["bytes"] <= gif_p2.MAX_BYTES
    with Image.open(tmp_path / "media" / "g_end.png") as im:
        assert im.size == (gif_p2.WIDTH, gif_p2.HEIGHT)
    assert tab.loc[tab["kind"] == "after", "banner"].str.contains("straddle −23 %").all()
    assert meta["last_frame_nodes_matched_t1"] == len(last) and meta["last_frame_max_abs_diff_usdc_t1"] < 1e-6
    assert json.loads((rd / gif_p2.META_JSON).read_text())["steps"]["BTC-pm2-20260820"] == "−23 %"


def test_colour_scale_covers_every_frame_so_nothing_is_cut_silently():
    """A23: the fixed scale runs from the smallest to the largest capital of all frames (whole half per cent
    outwards); the 1st to 99th percentile of before painted the cheapest nodes in the colour of 5.5 %."""
    a, b = grid(0), grid(1, 1.3)
    b.loc[0, "K_per_forward_bp"] = 341.0            # a single very cheap node, as on 20 Aug 2026
    lim = gif_p2.limits([a, b])
    k = np.concatenate([a["K_per_forward_bp"], b["K_per_forward_bp"]]) / 100.0
    assert lim["clim"][0] <= k.min() and lim["clim"][1] >= k.max()
    assert lim["clim"] == (3.0, float(np.ceil(k.max() * 2) / 2))
    assert lim["extend"] == "neither"


def test_colour_bar_shows_arrows_when_a_scale_cuts_values():
    """A23: a scale that does not cover the values ends in arrows and says so; a covering scale has none."""
    fig = _frame_fig()
    note = [t.get_text() for t in fig.findobj(matplotlib.text.Text) if t.get_text().startswith("fixed:")]
    cbar = [a for a in fig.axes if getattr(a, "_colorbar", None) is not None]
    assert note == [f"fixed: {gif_p2.limits([grid(1_789_632_000, tenors=p2surface.ANIM_DAYS[2:18])])['clim'][0]:g} "
                    f"to {gif_p2.limits([grid(1_789_632_000, tenors=p2surface.ANIM_DAYS[2:18])])['clim'][1]:g} %"]
    assert cbar and cbar[0]._colorbar.extend == "neither"
    plt.close(fig)
    ev = gif_p2.kept_events(events())
    fig = gif_p2.render(grid(1_789_632_000), ts=1_789_632_000,
                        lim={"clim": (6.0, 10.0), "zlim": (20.0, 80.0), "extend": "both"},
                        series=gif_p2.reference_series(reference_book()), marks=gif_p2.banners(ev, reference_book()),
                        return_figure=True)
    texts = [t.get_text() for t in fig.findobj(matplotlib.text.Text)]
    cbar = [a for a in fig.axes if getattr(a, "_colorbar", None) is not None]
    assert cbar[0]._colorbar.extend == "both"
    assert "fixed: 6 to 10 %, beyond at the ends" in texts
    plt.close(fig)


def test_build_writes_the_mp4_and_records_the_scale(tmp_path, monkeypatch):
    """A23: the MP4 of section 8 is written next to the GIF (``animate.write_mp4``) and the meta records it, the
    scale and the nodes outside the scale (none)."""
    pytest.importorskip("imageio_ffmpeg")
    rd = tmp_path / "results"
    rd.mkdir()
    events().to_csv(rd / "events.csv", index=False)
    reference_book().to_csv(rd / "reference_book.csv", index=False)

    def fake_compute(plan, **kw):
        return [{"ts": int(ts), "grid": grid(int(ts), 1.0 + 0.1 * i), "sm": grid(int(ts), 1.4), "n_expiries": 12,
                 "n_left_out": 0, "skipped": ""} for i, ts in enumerate(plan["ts"])]

    monkeypatch.setattr(gif_p2, "compute", fake_compute)
    monkeypatch.setattr(gif_p2, "grid_widths", lambda ccy, ts: None)
    meta = gif_p2.build(start="2026-09-01", end="2026-09-17", out=tmp_path / "media" / "g.gif", results_dir=rd)
    assert meta["mp4"] == str(tmp_path / "media" / "g.mp4") and (tmp_path / "media" / "g.mp4").stat().st_size > 0
    assert meta["extend"] == "neither" and meta["nodes_outside_scale"] == 0
    tab = pd.read_csv(rd / gif_p2.FRAMES_CSV)
    assert meta["clim_pct"][0] <= tab["K_min_pct"].min() and meta["clim_pct"][1] >= tab["K_max_pct"].max()
