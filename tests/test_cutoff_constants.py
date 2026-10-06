"""The registered cut-off of both papers is written in several modules; they must agree (final data run)."""
from __future__ import annotations

import datetime as dt

from derive_surface import books, gif_p2, inference_p1, markouts, p1cli, p2chain, p2events, p2feeds, p2surface, \
    p2validate
from derive_surface.figs_p2 import f5, t1, t2

CUT_S = 1_790_755_200                      # 2026-09-30 08:00 UTC, Paper 1 pre-registration, sample
CUT_DAY = "2026-09-30"
PROBE_S = 1_789_632_000                    # 2026-09-17 08:00 UTC, day of the API probes (illustrative snapshots)


def test_sample_end_is_the_registered_cut_off_everywhere():
    assert markouts.FINAL_CUTOFF_MS == CUT_S * 1000
    assert books.SAMPLE_END_MS == CUT_S * 1000 and books.END_DAY == CUT_DAY
    assert p2events.SAMPLE_END_TS == CUT_S and p2validate.SAMPLE_END_TS == CUT_S
    assert p2surface.END_DAY == CUT_DAY and f5.REF_DAY == CUT_DAY
    assert inference_p1.FUNDING_END_MS == CUT_S * 1000
    assert p1cli.to_ms("2026-09-30T08:00:00Z") == CUT_S * 1000


def test_load_end_is_cut_off_plus_25_hours():
    end_s = (markouts.FINAL_CUTOFF_MS + markouts.LOAD_BUFFER_MS) // 1000
    assert dt.datetime.fromtimestamp(end_s, dt.timezone.utc) == dt.datetime(2026, 10, 1, 9, tzinfo=dt.timezone.utc)
    assert p2feeds.TO_BLOCK == p2chain.block_at_ts(end_s)


def test_snapshots_stay_on_the_probe_day():
    assert t1.TS == PROBE_S and t2.REF_TS == PROBE_S and gif_p2.END == "2026-09-17"
