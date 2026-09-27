"""Offline tests for scripts/p2_zahlenblatt.py on a synthetic results directory with known answers."""
from __future__ import annotations

import copy
import datetime as dt
import json
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import p2_zahlenblatt as zb  # noqa: E402

NOW = dt.datetime(2026, 9, 25, 12, 0, tzinfo=dt.timezone.utc)
B, SEED = 99, 7
PREREG_END = 1_790_755_200  # 2026-09-30 08:00 UTC

# event and parameter timestamps
P0 = 1_760_000_000            # parameter state before the events
E1 = 1_767_912_649            # 2026-01-08 22:50:49 UTC, kept, capital falls by 20 %
E2 = 1_769_142_245            # 2026-01-23 04:24:05 UTC, dropped, no effect on the reference book
P3 = 1_779_000_000            # parameter change without an event row
DAY = 86_400


def _verdict(stat, lo, hi, rejected, n, rule, **kw):
    d = {"stat": stat, "lo": lo, "hi": hi, "rejected": rejected, "n": n, "rule": rule, "b": B, "seed": SEED,
         "level": 0.9, "exploratory": True}
    d.update(kw)
    return d


def base_inputs() -> dict:
    """All inputs as python objects; write_results turns them into files."""
    h1 = {"hypothesis": "H1", "stat": 0.5, "lo": 0.2, "hi": 0.8, "rejected": True, "rule": "rho rule",
          "threshold": 0.5, "b": B, "seed": SEED, "level": 0.9, "min_fills": 200, "n": 3, "n_fills": 900,
          "n_fills_k_le_0": 2, "n_fills_nonfinite": 0, "n_cells_any": 4, "n_days": 10, "n_nan_draws": 0,
          "cells_present_min": 3, "cells_present_median": 3.0, "first_day": "2025-06-12", "last_day": "2026-09-17",
          "n_fills_window": 1000, "window_start_utc": {"BTC": "2025-06-12T23:00:00+00:00",
                                                       "ETH": "2025-06-12T23:00:00+00:00",
                                                       "HYPE": "2025-11-11T00:00:00+00:00"},
          "fills_by_ccy": {"BTC": 600, "HYPE": 300}, "cells_by_ccy": {"BTC": 2, "HYPE": 1}}
    # A_bp = 10, 20, 30 (index 1e4 each); B_bp = 100, 400, 200 -> Spearman rho = 0.5
    # pooled: A = 1e4 * 60 / 3e4 = 20 bp, B = 1e4 * 60 / 3000 = 200 bp
    cells = pd.DataFrame({
        "cell": ["BTC|buy|00-10|<=2d", "BTC|sell|00-10|<=2d", "HYPE|buy|00-10|<=2d", "HYPE|sell|00-10|<=2d"],
        "ccy": ["BTC", "BTC", "HYPE", "HYPE"], "side": ["buy", "sell", "buy", "sell"],
        "delta_bucket": ["00-10"] * 4, "tenor_bucket": ["<=2d"] * 4,
        "fills": [300, 300, 300, 100], "contracts": [1.0] * 4, "fills_k_le_0": [2, 0, 0, 0],
        "sum_edge": [10.0, 20.0, 30.0, 1.0], "sum_index": [1e4, 1e4, 1e4, 1e4],
        "sum_K": [1000.0, 500.0, 1500.0, 10.0], "sum_den": [1000.0, 500.0, 1500.0, 10.0], "scale": [1.0] * 4,
        "occupied": [True, True, True, False],
        "A_bp": [10.0, 20.0, 30.0, 1.0], "B_bp": [100.0, 400.0, 200.0, 1000.0],
        "rank_A": [3.0, 2.0, 1.0, None], "rank_B": [3.0, 1.0, 2.0, None], "rank_shift": [0.0, -1.0, 1.0, None],
        "window": ["pm2"] * 4, "capital": ["K_pm2"] * 4})
    h2 = {"hypothesis": "H2", "stat": 0.0345, "lo": 0.0307, "hi": 0.0386, "rejected": False, "rule": "h2 rule",
          "threshold": 0.5, "n": 199, "n_days": 37, "n_sample": 200, "n_not_ok": 0, "n_excluded": 1,
          "n_nonfinite": 0, "share_nonpositive": 0.42, "b": B, "seed": SEED, "level": 0.9,
          "accounts": ["M3", "M5"], "fills_by_ccy": {"ETH": 150, "HYPE": 49}, "first_day": "2025-09-04",
          "last_day": "2026-09-17", "check_stored_ratio_max_abs": 0.0, "check_stored_ratio_nan_mismatch": 0}
    h3 = {"hypothesis": "H3", "stat": 4.75, "lo": 4.66, "hi": 4.82, "rejected": False, "rule": "h3 rule",
          "threshold": 2.0, "n": 50, "n_days": 20, "n_rows": 53, "n_not_ok": 3,
          "status_counts": {"no_options": 2, "no_snapshot": 1, "ok": 50}, "n_not_applicable": 0, "n_excluded": 0,
          "b": B, "seed": SEED, "level": 0.9, "share_days_over_63_options": 0.7, "days_over_63_options": 35,
          "accounts": {"M1": 20, "M2": 30}, "first_day": "2025-06-13", "last_day": "2026-09-17"}
    h4 = {"hypothesis": "H4", "stat": -4.6, "lo": -26.0, "hi": 16.6, "rejected": True, "rule": "h4 rule",
          "n": 900, "se": 13.1, "t": -0.35, "p": 0.6224, "p_sided": "one-sided, beta > 0", "b": B, "seed": SEED,
          "level": 0.9, "interval": "descriptive", "clusters": 14, "fills": 800, "events": 1, "events_kept": 1,
          "cell_events": 5, "day_ccy": 30,
          "criteria": {"beta_positive": False, "p_le_alpha": False, "beta_gt_placebo_p95": False},
          "placebo": {"n": 100, "finite": 100, "p95": 23.4, "share_ge_beta": 0.64, "median": 1.15, "mean": -7.6,
                      "min": -101.3, "max": 42.4, "gap_days": 28, "seed": SEED, "admissible_days": {}},
          "fe": {"method": "alternating projections", "iterations": 53, "abs_diff_beta_direct_solve": 1e-13},
          "panel_check": {"equal": True, "rows_stored": 900, "rows_rebuilt": 900},
          "sample": ["2024-01-11T00:00:00+00:00", "2026-09-17T11:51:53+00:00"]}
    sens = {"exploratory": True, "b": B, "seed": SEED, "level": 0.9,
            "a_maps": {"pm2": _verdict(0.5, 0.2, 0.8, True, 3, "H1"),
                       "sm_all": _verdict(0.6, 0.3, 0.9, True, 4, "H1")},
            "b_mm": {"h2_ratio_mm": _verdict(0.019, 0.016, 0.022, False, 190, "H2")},
            "d_h2": {"ratio": _verdict(0.0345, 0.0307, 0.0386, False, 199, "H2"),
                     "by_label": {"M3": _verdict(0.023, 0.013, 0.036, False, 100, "H2")},
                     "by_ccy": {"ETH": _verdict(0.038, 0.034, 0.042, False, 150, "H2")}},
            "e_h3": {"sm_pm2": _verdict(4.75, 4.66, 4.82, False, 50, "H3"),
                     "pm_pm2_be": _verdict(1.545, 1.535, 1.554, None, 40, "descriptive (no preregistered threshold)"),
                     "by_label": {"M2": _verdict(1.08, 1.05, 1.11, True, 30, "H3")},
                     "share_days_over_63_options": 0.7, "days_over_63_options": 35, "days_ok": 50},
            "g_by_ccy": {"pm2_BTC": _verdict(0.4, 0.1, 0.7, True, 2, "H1")}}
    sens_h4 = {"exploratory": True, "hypothesis": "H4", "b": B, "seed": SEED,
               "by_ccy": {"BTC": {"beta": -3.4, "se": 4.3, "t": -0.79, "p": 0.75, "lo": -10.5, "hi": 3.6, "n": 500,
                                  "clusters": 12, "events": 1, "cell_events": 3}},
               "no_outlier_cells": {"max_abs_dose": 1.0, "rows_dropped_real_panel": 0,
                                    "dose_cells_above": [{"event_id": "BTC-pm2-20260108", "cell": "c", "dose": -1.6}],
                                    "h4": {"beta": -4.6, "p": 0.6224, "lo": -26.0, "hi": 16.6, "n": 900},
                                    "placebo": {"n": 100, "p95": 23.4, "share_ge_beta": 0.65},
                                    "rejected": True, "criteria": {}},
               "placebo_all_timelines": {"placebo": {"n": 100, "p95": 21.6, "share_ge_beta": 0.88},
                                         "rejected": True, "criteria": {}}}

    def mgr(n, in_window, k_buy, k_sell):
        return {"n": n, "n_in_window": in_window, "sides": {"buy": {"k_le_0": k_buy}, "sell": {"k_le_0": k_sell}}}
    capital = {"rows": 1500, "managers": {
        "BTC": {"sm": mgr(1000, 1000, 0, 3), "pm": mgr(1000, 1000, 1, 2), "pm2": mgr(1000, 700, 1, 1)},
        "ETH": {"sm": mgr(0, 0, 0, 0), "pm": mgr(0, 0, 0, 0), "pm2": mgr(0, 0, 0, 0)},
        "HYPE": {"sm": mgr(500, 300, 0, 0), "pm": mgr(500, 0, 0, 0), "pm2": mgr(500, 300, 0, 0)}}}
    vsum = {"thresholds": {"median": 0.001, "p95": 0.01}, "seed": 20260924, "n_cases": 5, "n_chain": 5,
            "cells": [{"kind": "single", "ccy": "BTC", "manager": "pm2", "is_initial": True, "n": 3, "n_missing": 0,
                       "median_rel": 2e-9, "p95_rel": 2.9e-9, "max_rel": 3e-9, "passes": True},
                      {"kind": "book", "ccy": "BTC", "manager": "pm2", "is_initial": True, "n": 1, "n_missing": 0,
                       "median_rel": 4e-9, "p95_rel": 4e-9, "max_rel": 4e-9, "passes": True}],
            "per_scenario_check": {"n": 2, "all_equal": True}}
    val_rows = []
    for rel, kind, legs in [(1e-9, "single", 1), (2e-9, "single", 1), (3e-9, "single", 1), (4e-9, "book", 7)]:
        for ii in (True, False):
            val_rows.append({"ccy": "BTC", "manager": "pm2", "kind": kind, "block": 1, "ts": 1_750_000_000,
                             "K_chain": 100.0, "abs_err": rel * 100, "rel_err": rel, "is_initial": ii,
                             "status": "ok", "n_legs": legs})
    for ii in (True, False):
        val_rows.append({"ccy": "HYPE", "manager": "pm2", "kind": "single", "block": 2, "ts": 1_772_000_000,
                         "K_chain": float("nan"), "abs_err": float("nan"), "rel_err": float("nan"), "is_initial": ii,
                         "status": "revert", "n_legs": 1})
    validation = pd.DataFrame(val_rows)
    events = pd.DataFrame([
        {"ccy": "BTC", "manager": "pm2", "event_ts": E1, "kinds": "MarginParameters", "max_abs_dose": 0.25,
         "kept": True, "event_id": "BTC-pm2-20260108", "event_utc": "2026-01-08 22:50:49", "event_day": "2026-01-08",
         "last_ts": E1, "n_changes": 1, "panel_cells": 5, "panel_fills_pre": 400, "panel_fills_post": 500},
        {"ccy": "BTC", "manager": "pm2", "event_ts": E2, "kinds": "OtherContingencyParameters", "max_abs_dose": 0.0,
         "kept": False, "event_id": "BTC-pm2-20260123", "event_utc": "2026-01-23 04:24:05", "event_day": "2026-01-23",
         "last_ts": E2, "n_changes": 1, "panel_cells": 0, "panel_fills_pre": 0, "panel_fills_post": 0}])

    def rb(day, ts, k, kp, pts, ptsp):
        return {"ccy": "BTC", "day": day, "ts": ts, "forward": 10_000.0, "K_sm": 300.0, "K_sm_prev": 300.0,
                "sm_param_ts": 1, "sm_param_ts_prev": 1, "K_pm": 200.0, "K_pm_prev": 200.0, "pm_param_ts": 1.0,
                "pm_param_ts_prev": 1.0, "K_pm2": k, "K_pm2_prev": kp, "pm2_param_ts": pts, "pm2_param_ts_prev": ptsp}
    refbook = pd.DataFrame([
        rb("2026-01-08", E1 - 20_000, 100.0, 100.0, P0, P0),
        rb("2026-01-09", E1 + 33_000, 80.0, 100.0, E1, P0),         # -20 % at E1
        rb("2026-01-23", E2 + 13_000, 80.0, 80.0, E2, E1),          # E2: new entry, 0 %
        rb("2026-05-17", P3 + 10_000, 90.0, 80.0, P3, E2),          # change without an event row: +12.5 %
        rb("2026-09-17", PREREG_END - 13 * DAY, 90.0, 90.0, P3, P3)])
    oi = pd.DataFrame([
        {"month": "2025-05", "ccy": "BTC", "sm": 0.5, "pm": 0.5, "pm2": 0.0},
        {"month": "2025-07", "ccy": "BTC", "sm": 0.4, "pm": 0.4, "pm2": 0.2},
        {"month": "2026-03", "ccy": "BTC", "sm": 0.3, "pm": 0.005, "pm2": 0.695},
        {"month": "2026-09", "ccy": "BTC", "sm": 0.3, "pm": 0.0, "pm2": 0.7},
        {"month": "2026-09", "ccy": "HYPE", "sm": 0.12, "pm": float("nan"), "pm2": 0.88}])
    return {"h1.json": h1, "h1_cells.csv": cells, "h2.json": h2, "h3.json": h3, "h4.json": h4,
            "sensitivity.json": sens, "sensitivity_h4.json": sens_h4, "capital_check.json": capital,
            "validation_summary.json": vsum, "validation.csv": validation, "events.csv": events,
            "reference_book.csv": refbook, "manager_oi_share.csv": oi}


def write_results(path: Path, inputs: dict) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    for name, obj in inputs.items():
        if name.endswith(".json"):
            (path / name).write_text(json.dumps(obj))
        else:
            obj.to_csv(path / name, index=False)
    return path


@pytest.fixture()
def results(tmp_path) -> Path:
    return write_results(tmp_path / "results", base_inputs())


def run(path: Path):
    return zb.build(path, now=NOW, prereg_end_ts=PREREG_END)


# --------------------------------------------------------------------------------------------------------------


def test_summary_is_flat_and_json_strict(results):
    _, s = run(results)
    assert s, "summary must not be empty"
    for k, v in s.items():
        assert isinstance(k, str) and k == k.lower() and "-" not in k and " " not in k, k
        assert v is None or isinstance(v, (bool, int, float, str)), (k, type(v))
    json.dumps(s, allow_nan=False)  # no NaN or inf


def test_headline_values_are_passed_through(results):
    _, s = run(results)
    assert s["h1_stat"] == 0.5 and s["h1_lo"] == 0.2 and s["h1_hi"] == 0.8 and s["h1_rejected"] is True
    assert s["h1_n_cells"] == 3 and s["h1_n_cells_btc"] == 2 and s["h1_n_cells_eth"] is None
    assert s["h2_stat"] == 0.0345 and s["h2_rejected"] is False and s["h2_n_excluded"] == 1
    assert s["h3_stat"] == 4.75 and s["h3_n_no_options"] == 2 and s["h3_n_no_snapshot"] == 1
    assert s["h4_stat"] == -4.6 and s["h4_p"] == 0.6224 and s["h4_placebo_p95"] == 23.4
    assert s["h4_crit_beta_positive"] is False
    assert s["b"] == B and s["seed"] == SEED and s["level"] == 0.9


def test_pooled_cell_values_and_rank_shift(results):
    _, s = run(results)
    assert s["h1_pooled_edge_bp_notional"] == pytest.approx(20.0)
    assert s["h1_pooled_edge_bp_capital"] == pytest.approx(200.0)
    assert s["h1_rank_shift_max_abs"] == 1.0
    assert s["h1_rho_from_cells"] == pytest.approx(0.5)


def test_sample_counts_and_cutoff_from_data(results):
    _, s = run(results)
    assert s["fills_total"] == 1500 and s["fills_btc"] == 1000 and s["fills_eth"] == 0 and s["fills_hype"] == 500
    assert s["fills_pm2_window"] == 1000 and s["fills_pm2_window_btc"] == 700
    assert s["k_le_0_sm"] == 3 and s["k_le_0_pm"] == 3 and s["k_le_0_pm2"] == 2
    assert s["sample_end_utc"] == "2026-09-17T11:51:53+00:00"
    assert s["cutoff_day"] == "2026-09-17"
    assert s["sample_is_pilot"] is True


def test_cutoff_is_not_hard_coded(tmp_path):
    inp = base_inputs()
    inp["h4.json"]["sample"][1] = "2026-09-30T07:58:00+00:00"
    for k in ("h1.json", "h3.json"):
        inp[k]["last_day"] = "2026-09-30"
    inp["h2.json"]["last_day"] = "2026-09-29"
    rb = inp["reference_book.csv"]
    rb.loc[rb.index[-1], "day"] = "2026-09-30"
    md, s = zb.build(write_results(tmp_path / "r", inp), now=NOW, prereg_end_ts=PREREG_END)
    assert s["cutoff_day"] == "2026-09-30" and s["sample_is_pilot"] is False
    assert "30.09.2026" in md and "17.09.2026" not in md
    assert s["checks_failed"] == 0


def test_validation_numbers(results):
    _, s = run(results)
    assert s["validation_single_n"] == 3
    assert s["validation_single_median_rel"] == pytest.approx(2e-9)
    assert s["validation_single_max_rel"] == pytest.approx(3e-9)
    assert s["validation_single_p95_rel"] == pytest.approx(2.9e-9)
    assert s["validation_book_n"] == 1 and s["validation_book_median_rel"] == pytest.approx(4e-9)
    assert s["validation_reverts"] == 1
    assert s["validation_passed"] is True and s["validation_cells"] == 2


def test_reference_book_effects_are_matched_to_events(results):
    md, s = run(results)
    assert s["event_btc_pm2_20260108_refbook_change"] == pytest.approx(-0.2)
    assert s["event_btc_pm2_20260108_refbook_day"] == "2026-01-09"
    assert s["event_btc_pm2_20260123_refbook_change"] == pytest.approx(0.0)
    assert s["event_btc_pm2_20260108_kept"] is True and s["event_btc_pm2_20260123_kept"] is False
    assert s["events_total"] == 2 and s["events_kept"] == 1 and s["events_dropped"] == 1
    assert s["refbook_changes_without_event"] == 1
    assert "−20,00 %" in md and "+12,50 %" in md
    # reference book level in bp of the forward (K / forward * 1e4): PM2 100, 80, 80, 90, 90 -> median 90 bp
    assert s["refbook_btc_pm2_bp_median"] == pytest.approx(90.0)
    assert s["refbook_hype_pm_bp_median"] is None


def test_manager_shares(results):
    _, s = run(results)
    assert s["oi_last_month"] == "2026-09"
    assert s["oi_btc_pm2_last"] == 0.7 and s["oi_hype_pm_last"] is None and s["oi_hype_pm2_last"] == 0.88
    assert s["oi_btc_pm2_first_month"] == "2025-07"
    assert s["oi_btc_pm2_max"] == 0.7 and s["oi_btc_pm2_max_month"] == "2026-09"
    assert s["oi_btc_pm_below_1pct_from"] == "2026-03"
    assert s["oi_eth_pm2_last"] is None


def test_sensitivities_flat_with_fixed_label_slots(results):
    _, s = run(results)
    assert s["sens_a_maps_sm_all_stat"] == 0.6 and s["sens_a_maps_sm_all_rejected"] is True
    assert s["sens_d_h2_by_label_m3_stat"] == 0.023
    for i in range(1, 11):  # all ten dominant account labels exist as keys
        assert f"sens_d_h2_by_label_m{i}_stat" in s and f"sens_e_h3_by_label_m{i}_stat" in s
    assert s["sens_d_h2_by_label_m1_stat"] is None
    assert s["sens_e_h3_pm_pm2_be_rejected"] is None
    assert s["sens_h4_by_ccy_btc_beta"] == -3.4 and s["sens_h4_by_ccy_eth_beta"] is None
    assert s["sens_h4_all_timelines_placebo_p95"] == 21.6


def test_keys_are_stable_across_data(tmp_path):
    a = base_inputs()
    b = copy.deepcopy(a)
    b["sensitivity.json"]["d_h2"]["by_label"] = {"M5": _verdict(0.05, 0.04, 0.07, False, 90, "H2")}
    b["h1.json"]["cells_by_ccy"] = {"ETH": 3}
    b["h2.json"]["fills_by_ccy"] = {"BTC": 199}
    _, sa = zb.build(write_results(tmp_path / "a", a), now=NOW, prereg_end_ts=PREREG_END)
    _, sb = zb.build(write_results(tmp_path / "b", b), now=NOW, prereg_end_ts=PREREG_END)
    core = lambda s: {k for k in s if not k.startswith("event_")}  # noqa: E731
    assert core(sa) == core(sb)


def test_markdown_verdicts_numbers_and_sections(results):
    md, _ = run(results)
    for head in ("## Stichprobe", "## Validierung", "## H1", "## H2", "## H3", "## H4", "## Explorative",
                 "## Referenzbuch", "## Manager-Anteile", "## Konsistenzprüfungen"):
        assert head in md, head
    assert "**abgelehnt**" in md and "nicht abgelehnt" in md
    assert "0,500 [0,200; 0,800]" in md          # H1 with interval
    assert "0,0345 [0,0307; 0,0386]" in md       # H2
    assert "17.09.2026 11:51:53 UTC" in md       # last fill from the data
    assert "1\u202f500" in md                   # thousands separator as in the Paper 1 sheet


def _table_rows(md: str):
    """Yield (header columns, row columns, line) for every markdown table row; escaped pipes do not count."""
    header = None
    for line in md.splitlines():
        if not line.startswith("|"):
            header = None
            continue
        n = len(re.findall(r"(?<!\\)\|", line))
        if header is None:
            header = n
        yield header, n, line


def test_markdown_tables_have_consistent_columns(results):
    md, _ = run(results)
    rows = list(_table_rows(md))
    assert len(rows) > 20
    bad = [line for header, n, line in rows if n != header]
    assert not bad, bad
    assert "BTC\\|buy\\|00-10\\|<=2d" in md  # cell names are escaped inside tables


def test_verdicts_are_recomputed_from_the_rules(tmp_path):
    inp = base_inputs()
    inp["h2.json"]["rejected"] = True  # hi 0.0386 < 0.5: the rule says not rejected
    _, s = zb.build(write_results(tmp_path / "r", inp), now=NOW, prereg_end_ts=PREREG_END)
    assert s["checks_failed"] >= 1 and s["checks_ok"] is False


def test_h4_verdict_is_recomputed_from_beta_p_and_placebo(tmp_path):
    # criteria flags consistent with beta, p and P95, but the verdict contradicts the rule
    inp = base_inputs()
    inp["h4.json"]["rejected"] = False
    _, s = zb.build(write_results(tmp_path / "a", inp), now=NOW, prereg_end_ts=PREREG_END)
    assert s["checks_failed"] == 1
    # a positive, significant beta above the placebo P95 must not be rejected
    inp = base_inputs()
    inp["h4.json"].update(stat=30.0, p=0.01, rejected=False,
                          criteria={"beta_positive": True, "p_le_alpha": True, "beta_gt_placebo_p95": True})
    _, s = zb.build(write_results(tmp_path / "b", inp), now=NOW, prereg_end_ts=PREREG_END)
    assert s["checks_failed"] == 0 and s["h4_rejected"] is False


def test_consistency_checks_pass_on_consistent_data_and_flag_seed(results, tmp_path):
    _, s = run(results)
    assert s["checks_failed"] == 0 and s["checks_ok"] is True
    inp = base_inputs()
    inp["h3.json"]["seed"] = SEED + 1
    md, s2 = zb.build(write_results(tmp_path / "r", inp), now=NOW, prereg_end_ts=PREREG_END)
    assert s2["checks_failed"] >= 1 and "**verletzt**" in md


def test_missing_input_raises(tmp_path):
    inp = base_inputs()
    del inp["h3.json"]
    with pytest.raises(FileNotFoundError, match="h3.json"):
        zb.build(write_results(tmp_path / "r", inp), now=NOW, prereg_end_ts=PREREG_END)


def test_main_writes_markdown_and_sorted_summary(results, tmp_path):
    out, summ = tmp_path / "Z.md", tmp_path / "summary.json"
    assert zb.main(["--results", str(results), "--out", str(out), "--summary", str(summ), "--quiet"]) == 0
    text = summ.read_text()
    s = json.loads(text)
    assert list(s) == sorted(s)
    assert out.read_text().startswith("# Zahlenblatt Paper 2")
    # deterministic summary: a second run gives the same bytes
    zb.main(["--results", str(results), "--out", str(out), "--summary", str(summ), "--quiet"])
    assert summ.read_text() == text


# ------------------------------------------------------------------------------------------------ audit (A04, A05, A28-A30)

AUDIT_KEYS = ("h1_interval_share_ge_stat", "h1_interval_bc_lo", "h1_interval_basic_hi",
              "h1_sign_within_pos_switch_share_mean", "h1_sign_within_nonpos_per_replicate",
              "h4_cal_t_sd", "h4_cal_lo", "h4_cal_hi", "h4_cal_ten_pct_change_lo", "h4_cal_ten_pct_narrowing_share",
              "h4_cal_ten_pct_narrowing_share_descriptive", "h4_cal_p_placebo_t", "h4_cal_sd_scaled_lo",
              "h4_comp_events_without_cells_real", "h4_comp_events_without_cells_real_n", "h4_comp_overlap_pairs_real",
              "sens_h4_matched_placebo_p95", "sens_h4_matched_placebo_t_sd", "sens_h4_matched_rejected",
              "sens_h4_dose_median_beta", "sens_h4_dose_trimmed_p", "sens_h4_dose_pairs_with_large_log_ratio")


def _audit_inputs() -> dict:
    inp = base_inputs()
    sens, sh = inp["sensitivity.json"], inp["sensitivity_h4.json"]
    sens["h1_sign"] = {"within_pos": _verdict(0.634, 0.572, 0.702, True, 99, "H1", selection="per replicate",
                                              switch_share_mean=0.21, n_rep_median=97.0),
                       "within_nonpos": _verdict(0.636, 0.460, 0.684, True, 74, "H1", selection="per replicate",
                                                 switch_share_mean=0.19, n_rep_median=76.0),
                       "within_sell": _verdict(0.990, 0.985, 0.992, True, 86, "H1", selection="fixed")}
    sens["h1_interval"] = {"stat": 0.5, "lo": 0.2, "hi": 0.8, "mean_draw": 0.48, "median_draw": 0.49,
                           "share_ge_stat": 0.152, "z0": 1.03, "basic_lo": 0.2, "basic_hi": 0.8, "bc_lo": 0.45,
                           "bc_hi": 0.85, "exploratory": True, "b": B, "seed": SEED, "level": 0.9}
    sh["audit"] = {"exploratory": True, "b": B, "seed": SEED,
                   "placebo_calibration": {"n": 100, "t_sd": 1.82, "t_mad_sd": 2.13, "t_p05": -2.62, "t_p95": 2.83,
                                           "crit": 1.645, "share_t_gt_crit": 0.21, "share_abs_t_gt_crit": 0.43,
                                           "beta_sd": 28.7, "se_median": 8.8, "p_placebo_t": 0.62, "lo": -41.6,
                                           "hi": 29.7, "sd_scaled_lo": -43.7, "sd_scaled_hi": 34.5, "y_mean": 7.93,
                                           "ten_pct_change_lo": -3.13, "ten_pct_change_hi": 4.39,
                                           "ten_pct_change_sd_scaled_lo": -3.64, "ten_pct_change_sd_scaled_hi": 4.61,
                                           "ten_pct_narrowing_share": 0.395, "ten_pct_narrowing_share_sd_scaled": 0.46,
                                           "ten_pct_narrowing_share_descriptive": 0.22},
                   "placebo_composition": {"events_kept": 14, "events_with_cells_real": 13,
                                           "events_without_cells_real": ["HYPE-pm2-20260108"],
                                           "events_with_cells_placebo_min": 14, "events_with_cells_placebo_max": 14,
                                           "rows_real": 900, "rows_per_fill_real": 1.08, "rows_placebo_median": 980.0,
                                           "clusters_real": 14, "clusters_placebo_median": 19.0,
                                           "overlap_pairs_real": 3, "overlap_pairs_placebo_mean": 9.4,
                                           "same_day_draws_placebo_mean": 0.7},
                   "dose_robust": {"pairs": 5, "pairs_with_large_log_ratio": 1, "fills_with_large_log_ratio": 2,
                                   "pairs_median_differs": 1, "pairs_without_fills": 0, "trim_abs_log_ratio": 1.0,
                                   "check_mean_max_abs_diff": 0.0,
                                   "median": {"beta": -5.1, "se": 13.0, "t": -0.39, "p": 0.64, "lo": -27.0,
                                              "hi": 16.0, "n": 900, "rows_dropped": 0, "cell_events": 5},
                                   "trimmed": {"beta": -4.9, "se": 13.0, "t": -0.38, "p": 0.63, "lo": -26.5,
                                               "hi": 16.2, "n": 900, "rows_dropped": 0, "cell_events": 5}}}
    sh["placebo_matched"] = {"placebo": {"n": 100, "p95": 30.1, "median": 0.5, "share_ge_beta": 0.6, "t_sd": 1.7,
                                         "t_p05": -2.5, "t_p95": 2.6, "share_abs_t_gt_crit": 0.4},
                             "events_drawn": {"min": 6, "median": 7.0, "max": 9}, "rejected": True, "criteria": {}}
    return inp


def test_audit_numbers_pass_through_and_keys_exist_without_them(tmp_path):
    md, s = zb.build(write_results(tmp_path / "a", _audit_inputs()), now=NOW, prereg_end_ts=PREREG_END)
    assert s["h1_interval_share_ge_stat"] == 0.152 and s["h1_interval_bc_lo"] == 0.45
    assert s["h1_sign_within_pos_switch_share_mean"] == 0.21 and s["h1_sign_within_nonpos_per_replicate"] is True
    assert s["sens_h1_sign_within_pos_lo"] == 0.572 and s["sens_h1_sign_within_nonpos_hi"] == 0.684
    assert s["h4_cal_t_sd"] == 1.82 and (s["h4_cal_lo"], s["h4_cal_hi"]) == (-41.6, 29.7)
    assert s["h4_cal_ten_pct_narrowing_share"] == 0.395 and s["h4_cal_ten_pct_narrowing_share_descriptive"] == 0.22
    assert s["h4_comp_events_without_cells_real"] == "HYPE-pm2-20260108"
    assert s["h4_comp_events_without_cells_real_n"] == 1 and s["h4_comp_overlap_pairs_real"] == 3
    assert s["sens_h4_matched_placebo_p95"] == 30.1 and s["sens_h4_matched_rejected"] is True
    assert s["sens_h4_dose_median_beta"] == -5.1 and s["sens_h4_dose_trimmed_p"] == 0.63
    assert s["sens_h4_dose_pairs_with_large_log_ratio"] == 1
    assert "## Audit (explorativ)" in md
    assert "Auswahl je Replikation neu" in md and "1,82" in md and "−41,6" in md
    assert "Placebos nur Ereignisse mit Zellen" in md and "Dosis als Median" in md
    assert s["checks_failed"] == 0
    rows = list(_table_rows(md))
    assert not [line for header, n, line in rows if n != header]
    _, s0 = run(write_results(tmp_path / "b", base_inputs()))
    for k in AUDIT_KEYS:
        assert k in s0 and k in s, k
        assert s0[k] is None, k
