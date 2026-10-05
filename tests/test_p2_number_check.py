"""Offline tests for scripts/p2_number_check.py on a synthetic results directory with known answers.

The expectations are written by hand from the fixture values below, not computed with the module under test.
The mutation test and the swap cases (audit A19 to A21 and A33; data/p2/audit/zahlen/swap_check.py) run on a
manuscript whose sentences are copied from paper2/main.tex and declared in the format of the module docstring;
the mutants are generated with a regular expression of their own, not with the tokenizer of the module.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import p2_number_check as nc  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
KNOWN_COMMITS = {"cc0a29f", "e492ba1"}
GIT_DATES = {"cc0a29f": "2026-09-24 22:33:10 +0200", "e492ba1": "2026-09-25 01:29:58 +0200"}


def resolve(sha: str) -> bool:
    return sha in KNOWN_COMMITS


def git_date(sha: str):
    return GIT_DATES.get(sha)


SUMMARY = {
    "fills_total": 603940, "h1_stat": 0.9029439, "h1_lo": 0.8805637, "h1_hi": 0.9074329,
    "sens_b_mm_h1_pm2_mm_stat": 0.90255, "h1_rank_shift_median_abs": 14.0, "h1_n_fills_k_le_0": 20,
    "h2_stat": 0.0345401, "h2_share_nonpositive": 0.4196209, "h2_n_accounts": 4,
    "cutoff_day": "2026-09-17", "api_day": "2026-09-25", "sample_start_utc": "2024-01-11T00:00:00+00:00",
    "h4_stat": -4.599234, "h4_p": 0.6224, "events_kept": 14, "validation_single_blocks_per_cell": 100,
    "validation_single_median_rel": 8.667e-10,
    "event_btc_pm2_20260820_refbook_change": -0.2293, "event_btc_pm2_20260820_refbook_log_change": -0.26046,
    "event_btc_pm2_20260820_refbook_day": "2026-08-20", "event_btc_pm2_20260524_refbook_day": "2026-05-24",
    "event_eth_pm2_20260524_refbook_log_change": -0.0336, "event_hype_pm2_20260524_refbook_log_change": -0.3743,
    "event_btc_pm2_20260108_refbook_log_change": 0.0160, "event_btc_pm2_20260108_refbook_day": "2026-01-08",
    "sens_h4_by_ccy_btc_beta": -3.4180514, "sens_h4_by_ccy_eth_beta": -1.8989519,
    "sens_h4_by_ccy_hype_beta": -10.1235642, "sens_h4_by_ccy_btc_p": 0.7497, "sens_h4_by_ccy_eth_p": 0.669,
    "sens_h4_by_ccy_hype_p": 0.5778, "h4_review_sells_only_beta": -3.8096927, "h4_review_sells_only_p": 0.5766,
    "h4_review_oi_weighted_beta": -5.1293638, "h4_review_oi_weighted_p": 0.5926,
    "long_draws": list(range(100, 200)),
}


@pytest.fixture()
def results(tmp_path: Path) -> Path:
    r = tmp_path / "results"
    (r / "semantics").mkdir(parents=True)
    (r / "summary.json").write_text(json.dumps(SUMMARY))
    (r / "h1.json").write_text(json.dumps({"stat": 0.9029439, "rejected": True}))
    (r / "h2.json").write_text(json.dumps({"stat": 0.0345, "rejected": False}))
    (r / "h3.json").write_text(json.dumps({"stat": 4.7467, "rejected": False}))
    (r / "h4.json").write_text(json.dumps({"stat": -4.6, "rejected": True, "placebo": {"admissible_days": {
        "ETH-pm2-20260108": {"days": 10, "first": "2025-07-16", "last": "2025-07-25"},
        "BTC-pm2-20260108": {"days": 54, "first": "2025-07-16", "last": "2026-03-21"}}}}))
    (r / "semantics" / "box_discount.json").write_text(json.dumps({"box_2026-09-24T11:27Z": [
        {"r_chain": 0.0364, "r_api": 0.02}, {"r_chain": 0.0382, "r_api": 0.02}, {"r_chain": 0.0371, "r_api": 0.02}]}))
    (r / "semantics" / "factors.csv").write_text(
        "measurement,book,case,block,F_Cnet\n"
        "historical 2026-09-17T10:45:13Z block 44810149,b17,A,44810149,2.33\n"
        "historical 2026-09-17T10:45:13Z block 44810149,b17,B,44810149,11.86\n")
    (r / "fig_f1_a.csv").write_text(
        "ccy,side,cell,occupied,kappa_pm2\n"
        "BTC,sell,BTC|sell|00-10|<=2d,True,13.136\nBTC,sell,BTC|sell|10-25|2-7d,True,7.798\n"
        "BTC,sell,BTC|sell|25-40|>90d,True,17.690\nBTC,sell,BTC|sell|90-100|>90d,False,30.0\n"
        "ETH,sell,ETH|sell|00-10|<=2d,True,7.12\nETH,sell,ETH|sell|25-40|>90d,True,21.38\n"
        "HYPE,sell,HYPE|sell|00-10|<=2d,True,17.52\nHYPE,sell,HYPE|sell|25-40|>90d,True,38.66\n"
        "BTC,buy,BTC|buy|00-10|<=2d,True,0.612\n")
    (r / "fig_f1_b.csv").write_text(
        "ccy,side,manager,regime,row_median\n"
        "BTC,sell,sm,pooled,0.9433035\nBTC,sell,sm,pooled,0.9433035\nETH,sell,sm,pooled,0.9021\n"
        "HYPE,sell,sm,pooled,0.8752\nBTC,sell,sm,r4,1.3977\nETH,sell,sm,r4,1.1402\n"
        "BTC,sell,pm,pooled,1.3818\nETH,sell,pm,pooled,1.3551\n")
    (r / "fig_h2_dist.csv").write_text(
        "label,variant,kind,x,value\nall,ratio,quantile,0.25,-0.27636\nall,ratio,quantile,0.75,0.63058\n"
        "all,ratio_tape,quantile,0.25,-0.27956\nall,ratio,n,,19999\n")
    (r / "h1_cells.csv").write_text(
        "cell,occupied,A_bp,rank_A,rank_B\nBTC|buy|00-10|2-7d,True,1.5,76,4\nBTC|buy|00-10|<=2d,True,-0.3,121,173\n"
        "c,False,2.0,,\nd,True,0.2,50,60\n")
    return r


def tex(body: str, abstract: str = "Abstract text.", front: str = "") -> str:
    return ("\\begin{document}\n\\begin{abstract}\n" + abstract + "\n\\end{abstract}\n" + front +
            "\n\\maketitle\n" + body + "\n\\bibliographystyle{x}\n\\bibliography{refs}\n\\end{document}\n")


def check(results: Path, body: str, abstract: str = "Abstract text.", front: str = "", dates=git_date):
    return nc.check(tex(body, abstract, front), results, resolve_commit=resolve, git_date=dates)


def fill(template: str, *values: str) -> str:
    """The template with each ``<>`` replaced by the next value (LaTeX braces rule out str.format)."""
    for v in values:
        template = template.replace("<>", v, 1)
    return template


def bad(vs):
    return [(v.token.raw, v.how) for v in vs if not v.ok]


# ---------------------------------------------------------------------------------------------------------------
# Text: what counts as a number, and the units
# ---------------------------------------------------------------------------------------------------------------
def test_identifiers_comments_formulas_and_citations_are_not_numbers(results):
    vs = check(results, r"""\section{Results}
PM2 and H1 under UTC+2 in Addendum 2, see Figure~\ref{fig:f1} and \citet{albiez2026}.
% 12345 in a comment
\begin{equation}
  e = 10^4 \frac{a}{b} + 7.77
\end{equation}
""")
    assert vs == []


def test_every_number_must_be_declared_nothing_is_searched(results):
    vs = check(results, "\\section{Results}\nThe correlation is 0.903 over 603\\,940 fills.\n")
    assert [(v.token.raw, v.how, v.ok) for v in vs] == [("0.903", "none", False), ("603940", "none", False)]


def test_constants_need_an_explicit_binding_by_name(results):
    body = "\\section{Data}\nCells hold 200 fills and the threshold is 0.5.\n"
    assert bad(check(results, body)) == [("200", "none"), ("0.5", "none")]
    vs = check(results, body + "% src const:cell_min_fills 200\n% src const:h1_threshold 0.5\n")
    assert [(v.how, v.ok) for v in vs] == [("constant", True), ("constant", True)]
    wrong = body + "% src const:placebo_dates 200\n% src const:h1_threshold 0.5\n"
    assert bad(check(results, wrong)) == [("200", "mismatch")]          # 100 placebo dates, not 200
    unknown = body + "% src const:no_such_constant 200\n% src const:h1_threshold 0.5\n"
    assert bad(check(results, unknown)) == [("200", "mismatch")]


def test_captions_and_subsections_are_units_of_their_own(results):
    body = r"""\section{Results}
\subsection{First}
Value 0.903.
% src summary.json:h1_stat 0.903
\begin{figure}[t]
  \includegraphics{figures/f1.pdf}
  \caption{\textbf{Title.} Also 0.903.}
  \label{fig:f1}
\end{figure}
\subsection{Second}
Value 0.903.
"""
    vs = check(results, body)
    assert [(v.unit, v.ok) for v in vs] == [("caption fig:f1", False), ("Results / First", True),
                                           ("Results / Second", False)]
    inside = body.replace("  \\label{fig:f1}\n", "  \\label{fig:f1}\n% src summary.json:h1_stat 0.903\n")
    vs = check(results, inside)
    assert [(v.unit, v.ok) for v in vs] == [("caption fig:f1", True), ("Results / First", True),
                                           ("Results / Second", False)]


def test_declaration_outside_every_unit_is_an_error(results):
    vs = check(results, "\\section{R}\nValue 0.903.\n% src summary.json:h1_stat 0.903\n",
               front="% src summary.json:h1_stat 0.903\n")
    assert [(v.unit, v.how, v.ok) for v in vs] == [("R", "result", True), ("front matter", "decl", False)]


def test_abstract_declarations_hold_for_the_abstract_only(results):
    vs = check(results, "\\section{A}\nValue 0.903.\n",
               abstract="The correlation is 0.903.\n% src summary.json:h1_stat 0.903")
    assert [(v.unit, v.ok) for v in vs] == [("abstract", True), ("A", False)]


# ---------------------------------------------------------------------------------------------------------------
# One source per occurrence, in the order of the text (A19)
# ---------------------------------------------------------------------------------------------------------------
def test_a_declaration_binds_one_occurrence_in_text_order(results):
    body = ("\\section{R}\nThe test gives 0.903, and under maintenance margin it is 0.903 as well.\n"
            "% src summary.json:h1_stat 0.903\n% src summary.json:sens_b_mm_h1_pm2_mm_stat 0.903\n")
    vs = check(results, body)
    assert [v.source for v in vs] == ["summary.json:h1_stat", "summary.json:sens_b_mm_h1_pm2_mm_stat"]
    assert all(v.ok for v in vs)
    once = body.replace("% src summary.json:sens_b_mm_h1_pm2_mm_stat 0.903\n", "")
    assert bad(check(results, once)) == [("0.903", "none")]            # the second occurrence is not declared


def test_a_value_printed_twice_is_declared_twice(results):
    body = "\\section{R}\nA dose of $-0.105$ predicts $-0.105\\,\\beta$.\n"
    assert not bad(check(results, body + "% src ident:ln_0_9 -0.105 -0.105\n"))
    assert bad(check(results, body + "% src ident:ln_0_9 -0.105\n")) == [("-0.105", "none")]


def test_a_declared_number_that_is_not_printed_is_an_error(results):
    vs = check(results, "\\section{R}\nNothing.\n% src summary.json:h1_stat 0.903\n")
    assert [(v.unit, v.token.raw, v.how, v.ok) for v in vs] == [("R", "0.903", "decl", False)]
    assert nc.unused_declarations(vs) == [("summary.json:h1_stat", "0.903")]


def test_declarations_out_of_text_order_fail(results):
    body = ("\\section{R}\nThe ratio is 0.943 in BTC, 0.902 in ETH and 0.875 in HYPE.\n"
            "% src fig_f1_b.csv:row_median@ccy=BTC,manager=sm,regime=pooled 0.943\n"
            "% src fig_f1_b.csv:row_median@ccy=ETH,manager=sm,regime=pooled 0.902\n"
            "% src fig_f1_b.csv:row_median@ccy=HYPE,manager=sm,regime=pooled 0.875\n")
    assert not bad(check(results, body))
    swapped = body.replace("0.943 in BTC, 0.902 in ETH and 0.875 in HYPE",
                           "0.875 in BTC, 0.943 in ETH and 0.902 in HYPE")
    assert sorted(bad(check(results, swapped))) == [("0.875", "decl"), ("0.875", "none")]


def test_a_stale_value_fails_at_its_own_occurrence(results):
    body = ("\\section{R}\nThe test gives 0.903; under maintenance margin 0.903. 14 events pass, and the median "
            "cell moves by 14 ranks; the four makers.\n"
            "% src summary.json:h1_stat 0.903\n% src summary.json:sens_b_mm_h1_pm2_mm_stat 0.903\n"
            "% src summary.json:events_kept 14\n% src summary.json:h1_rank_shift_median_abs 14\n"
            "% src summary.json:h2_n_accounts four\n")
    assert not bad(check(results, body))
    (results / "summary.json").write_text(json.dumps(dict(SUMMARY, h1_stat=0.911, events_kept=15, h2_n_accounts=5)))
    vs = check(results, body)
    assert [(v.source, v.ok) for v in vs] == [
        ("summary.json:h1_stat", False), ("summary.json:sens_b_mm_h1_pm2_mm_stat", True),
        ("summary.json:events_kept", False), ("summary.json:h1_rank_shift_median_abs", True),
        ("summary.json:h2_n_accounts", False)]


# ---------------------------------------------------------------------------------------------------------------
# Sources: exact keys, rows, aggregates (A21)
# ---------------------------------------------------------------------------------------------------------------
def test_csv_needs_a_row_filter_that_fixes_one_value(results):
    body = "\\section{R}\nKappa is 7.8.\n% src fig_f1_a.csv:kappa_pm2<> 7.8\n"
    assert bad(check(results, fill(body, ""))) == [("7.8", "mismatch")]              # every row: not one value
    assert bad(check(results, fill(body, "@ccy=BTC,side=sell"))) == [("7.8", "mismatch")]
    assert not bad(check(results, fill(body, "@cell=BTC|sell|10-25|2-7d")))
    assert not bad(check(results, fill(body, "@ccy=BTC,side=sell,occupied=True~min")))
    assert bad(check(results, fill(body, "@ccy=BTC,side=sell~min"))) == []          # the unoccupied cell is 30.0
    assert bad(check(results, fill(body, "@ccy=XRP~min"))) == [("7.8", "mismatch")]  # no row


def test_rows_repeating_one_value_count_as_one(results):
    vs = check(results, "\\section{R}\nIt is 0.943.\n"
                        "% src fig_f1_b.csv:row_median@ccy=BTC,regime=pooled,manager=sm 0.943\n")
    assert vs[0].ok


def test_first_column_shorthand_and_numeric_filters(results):
    vs = check(results, "\\section{R}\nFrom rank 121 to rank 173; 2 cells are positive; 0.63 at the third "
                        "quartile.\n"
                        "% src h1_cells.csv:rank_A@BTC|buy|00-10|<=2d 121\n"
                        "% src h1_cells.csv:rank_B@BTC|buy|00-10|<=2d 173\n"
                        "% src h1_cells.csv:cell@occupied=True,A_bp>0~count 2\n"
                        "% src fig_h2_dist.csv:value@label=all,variant=ratio,x=0.75 0.63\n")
    assert all(v.ok for v in vs) and len(vs) == 4


def test_count_and_distinct_count_rows(results):
    vs = check(results, "\\section{R}\nThe table has 8 rows of 5 groups under 2 managers.\n"
                        "% src fig_f1_b.csv:ccy~count 8\n"
                        "% src fig_f1_b.csv:row_median~distinct 7\n"
                        "% src fig_f1_b.csv:manager~distinct 2\n")
    assert bad(vs) == [("5", "none"), ("7", "decl")]                 # 7 distinct medians, 5 is not declared
    vs = check(results, "\\section{R}\nThe table has 8 rows of 7 medians under 2 managers.\n"
                        "% src fig_f1_b.csv:ccy~count 8\n"
                        "% src fig_f1_b.csv:row_median~distinct 7\n"
                        "% src fig_f1_b.csv:manager~distinct 2\n")
    assert not bad(vs)


def test_glob_needs_one_value_or_an_aggregate(results):
    body = "\\section{E}\nThe feed ranged from 3.64 to 3.82 per cent; the endpoint uses 2.0000 per cent.\n"
    good = body + ("% src semantics/box_discount.json:box_*.r_chain~min~pct 3.64\n"
                   "% src semantics/box_discount.json:box_*.r_chain~max~pct 3.82\n"
                   "% src semantics/box_discount.json:box_*.r_api~pct 2.0000\n")
    assert not bad(check(results, good))
    glob_any = body + ("% src semantics/box_discount.json:box_*.r_chain~pct 3.64\n"
                       "% src semantics/box_discount.json:box_*.r_chain~pct 3.82\n"
                       "% src semantics/box_discount.json:box_*.r_api~pct 2.0000\n")
    assert bad(check(results, glob_any)) == [("3.64", "mismatch"), ("3.82", "mismatch")]


def test_key_lists_aggregates_and_relations(results):
    body = ("\\section{R}\nEach with a one-sided $p$ above 0.5.\n"
            "% src summary.json:sens_h4_by_ccy_btc_p,sens_h4_by_ccy_eth_p,sens_h4_by_ccy_hype_p<> <>0.5\n")
    assert not bad(check(results, fill(body, "~min", ">")))
    assert not bad(check(results, fill(body, "~all", ">")))
    assert bad(check(results, fill(body, "", ">"))) == [("0.5", "mismatch")]        # three values, no aggregate
    assert bad(check(results, fill(body, "~max", "<"))) == [("0.5", "mismatch")]
    assert bad(check(results, fill(body, "~min", ""))) == [("0.5", "mismatch")]     # 0.5778 is not 0.5


def test_missing_keys_files_and_operations_fail(results):
    for spec in ["summary.json:no_such_key", "nofile.json:h1_stat", "fig_f1_a.csv:no_col@ccy=BTC~min",
                 "summary.json", "summary.json:h1_stat~wrongop", "text:0.903"]:
        vs = check(results, fill("\\section{R}\nValue 0.903.\n% src <> 0.903\n", spec))
        assert bad(vs) == [("0.903", "mismatch")], spec


def test_long_numeric_lists_can_be_named_but_are_never_searched(results):
    assert bad(check(results, "\\section{R}\nA draw of 150.\n")) == [("150", "none")]
    assert not bad(check(results, "\\section{R}\nA draw of 150.\n% src summary.json:long_draws.50 150\n"))


def test_derived_counts(results):
    vs = check(results, "\\section{R}\nTwo of four are rejected; 2 cells are positive.\n"
                        "% src derived:n_rejected Two\n% src derived:n_hypotheses four\n"
                        "% src derived:h1_cells_pos 2\n")
    assert [(v.how, v.ok) for v in vs] == [("result", True)] * 3


def test_text_counts_are_integers_with_a_label(results):
    body = "\\section{R}\nThe two rankings differ.\n% src text:<> two\n"
    vs = check(results, fill(body, "two_rankings"))
    assert [(v.how, v.ok) for v in vs] == [("text", True)]
    assert bad(check(results, "\\section{R}\nA share of 0.28.\n% src text:share 0.28\n")) == [("0.28", "mismatch")]


# ---------------------------------------------------------------------------------------------------------------
# Rounding, scales and signs only as declared (A20, A21)
# ---------------------------------------------------------------------------------------------------------------
def test_rounding_to_the_printed_precision(results):
    body = "\\section{R}\nThe correlation is <>.\n% src summary.json:h1_stat <>\n"
    for printed in ["0.903", "0.90", "0.9029"]:
        assert not bad(check(results, fill(body, printed, printed))), printed
    for printed in ["0.904", "0.902", "0.9030"]:
        assert bad(check(results, fill(body, printed, printed))) == [(printed, "mismatch")], printed


def test_per_cent_scale_only_as_declared(results):
    body = "\\section{R}\nThe median is 3.5 per cent.\n% src summary.json:h2_stat<> 3.5\n"
    assert bad(check(results, fill(body, ""))) == [("3.5", "mismatch")]
    assert not bad(check(results, fill(body, "~pct")))
    assert bad(check(results, fill(body, "~bp"))) == [("3.5", "mismatch")]


def test_sign_and_magnitude_only_as_declared(results):
    fell = ("\\section{R}\nThe capital fell by 22.9 per cent.\n"
            "% src summary.json:event_btc_pm2_20260820_refbook_change<> 22.9\n")
    assert bad(check(results, fill(fell, "~pct~down"))) == [("22.9", "mismatch")]
    assert not bad(check(results, fill(fell, "~neg~pct~down")))
    assert not bad(check(results, fill(fell, "~abs~pct~down")))
    rose = ("\\section{R}\nOnly one change raised it, by about 1.6 log per cent.\n"
            "% src summary.json:event_btc_pm2_20260108_refbook_log_change<> 1.6\n")
    assert not bad(check(results, fill(rose, "~pct~up")))
    assert bad(check(results, fill(rose, "~neg~pct~up"))) == [("1.6", "mismatch")]
    minus = "\\section{R}\nA value of $-0.903$.\n% src summary.json:h1_stat -0.903\n"
    assert bad(check(results, minus)) == [("-0.903", "mismatch")]


# ---------------------------------------------------------------------------------------------------------------
# Direction words (audit B2): the verb of a change is bound as well as its number
# ---------------------------------------------------------------------------------------------------------------
FELL = "\\section{R}\nThe capital <> by 22.9 per cent.\n% src summary.json:event_btc_pm2_20260820_refbook_change<> 22.9\n"


def test_a_number_after_a_direction_word_and_by_needs_its_declared_direction(results):
    assert bad(check(results, fill(FELL, "fell", "~neg~pct"))) == [("22.9", "mismatch")]
    assert not bad(check(results, fill(FELL, "fell", "~neg~pct~down")))
    assert not bad(check(results, fill(FELL, "was cut", "~neg~pct~down")))


def test_a_changed_verb_fails_although_the_number_still_matches(results):
    vs = check(results, fill(FELL, "rose", "~neg~pct~down"))
    assert bad(vs) == [("22.9", "mismatch")] and "rose" in [v for v in vs if not v.ok][0].detail
    # the verb and the declaration changed alike: ~neg binds a negative change, which cannot rise
    assert bad(check(results, fill(FELL, "rose", "~neg~pct~up"))) == [("22.9", "mismatch")]


def test_a_declared_direction_needs_a_direction_word(results):
    assert bad(check(results, fill(FELL, "changed", "~neg~pct~down"))) == [("22.9", "mismatch")]
    assert not bad(check(results, fill(FELL, "changed", "~neg~pct")))


def test_the_direction_reaches_across_a_comma_before_by_and_over_a_range(results):
    body = ("\\section{R}\nThe events made the book <>, by between 3.4 and 37.4 log per cent.\n"
            "% src summary.json:event_eth_pm2_20260524_refbook_log_change~neg~pct~down 3.4\n"
            "% src summary.json:event_hype_pm2_20260524_refbook_log_change~neg~pct~down 37.4\n")
    assert not bad(check(results, fill(body, "cheaper")))
    assert bad(check(results, fill(body, "dearer"))) == [("3.4", "mismatch"), ("37.4", "mismatch")]


def test_the_direction_stops_at_the_end_of_the_by_phrase(results):
    body = ("\\section{R}\nThe capital fell by 22.9 per cent, and 14 events passed.\n"
            "% src summary.json:event_btc_pm2_20260820_refbook_change~neg~pct~down 22.9\n"
            "% src summary.json:events_kept 14\n")
    assert not bad(check(results, body))


def test_a_magnitude_may_carry_a_down_word(results):
    body = ("\\section{R}\nA narrowing by up to 42.0 per cent is not excluded.\n"
            "% src summary.json:h2_share_nonpositive~pct<> 42.0\n")
    assert not bad(check(results, fill(body, "~down")))
    assert bad(check(results, fill(body, "~up"))) == [("42.0", "mismatch")]


def test_from_to_follows_the_verb(results):
    body = ("\\section{R}\nThe count <> from 14 to 4.\n"
            "% src summary.json:events_kept 14\n% src summary.json:h2_n_accounts 4\n")
    assert not bad(check(results, fill(body, "fell")))
    assert bad(check(results, fill(body, "rose"))) == [("4", "mismatch")]


def test_from_to_on_ranks_reads_a_smaller_rank_as_a_rise(results):
    body = ("\\section{R}\nThe cell <> from rank 76 to 4.\n"
            "% src h1_cells.csv:rank_A@BTC|buy|00-10|2-7d 76\n% src h1_cells.csv:rank_B@BTC|buy|00-10|2-7d 4\n")
    assert not bad(check(results, fill(body, "rises")))
    assert bad(check(results, fill(body, "falls"))) == [("4", "mismatch")]


def test_direction_is_one_operation_and_changes_no_value(results):
    body = "\\section{R}\nThe median is 3.5 per cent.\n% src summary.json:h2_stat~pct<> 3.5\n"
    assert bad(check(results, fill(body, "~down~up"))) == [("3.5", "mismatch")]
    spec, err = nc.parse_spec("summary.json:h2_stat~pct~down")
    assert spec is not None and not err


def test_scientific_notation_and_long_integers(results):
    vs = check(results, "\\section{Data}\nThe median is $8.7\\times10^{-10}$ at block 44\\,810\\,149.\n"
                        "% src summary.json:validation_single_median_rel 8.7\\times10^{-10}\n"
                        "% src semantics/factors.csv:block@case=B 44\\,810\\,149\n")
    assert [v.ok for v in vs] == [True, True]


def test_spelled_and_digit_forms_are_different_printed_numbers(results):
    vs = check(results, "\\section{R}\nThe four makers, one day.\n% src summary.json:h2_n_accounts 4\n")
    assert sorted(bad(vs)) == [("4", "decl"), ("four", "none")]


# ---------------------------------------------------------------------------------------------------------------
# Dates, clock times and commits (A33)
# ---------------------------------------------------------------------------------------------------------------
def test_dates_bind_to_their_key_not_to_the_file(results):
    body = "\\section{R}\nCut on 17 September 2026.\n% src summary.json:<> 17 September 2026\n"
    assert not bad(check(results, fill(body, "cutoff_day")))
    assert bad(check(results, fill(body, "api_day"))) == [("17 September 2026", "mismatch")]


def test_partial_dates_clock_times_and_constants(results):
    vs = check(results, "\\section{R}\nIn September 2026, from 16 July to 25 July 2025, at 10:45 and since "
                        "11 January 2024 00:00.\n"
                        "% src summary.json:api_day September 2026\n"
                        "% src h4.json:placebo.admissible_days.ETH-pm2-20260108.first 16 July\n"
                        "% src h4.json:placebo.admissible_days.ETH-pm2-20260108.last 25 July 2025\n"
                        "% src semantics/factors.csv:measurement@case=B 10:45\n"
                        "% src const:sample_start 11 January 2024 00:00\n")
    assert [(v.token.raw, v.ok) for v in vs] == [("September 2026", True), ("16 July", True),
                                                ("25 July 2025", True), ("10:45", True),
                                                ("11 January 2024", True), ("00:00", True)]
    wrong = tex("\\section{R}\nSince 11 January 2024.\n% src const:pilot_cut 11 January 2024\n")
    assert bad(nc.check(wrong, results, resolve_commit=resolve, git_date=git_date)) == [("11 January 2024", "mismatch")]


def test_commit_dates_in_their_own_time_zone(results):
    body = ("\\section{R}\nRegistered on 24 September 2026 at 22:33 in \\texttt{cc0a29f}, the addenda of "
            "25 September 2026 in \\texttt{e492ba1}, not in \\texttt{abcdef1}.\n"
            "% src git:cc0a29f 24 September 2026 22:33\n% src git:e492ba1 25 September 2026\n")
    vs = check(results, body)
    assert [(v.token.raw, v.how, v.ok) for v in vs] == [
        ("24 September 2026", "git", True), ("22:33", "git", True), ("25 September 2026", "git", True),
        ("cc0a29f", "commit", True), ("e492ba1", "commit", True), ("abcdef1", "none", False)]
    utc = check(results, body, dates=lambda sha: {"cc0a29f": "2026-09-24 20:33:10 +0000",
                                                  "e492ba1": "2026-09-24 23:29:58 +0000"}[sha])
    assert bad(utc) == [("22:33", "mismatch"), ("25 September 2026", "mismatch"), ("abcdef1", "none")]


# ---------------------------------------------------------------------------------------------------------------
# The constants are those of the pre-registration (independent check of the list)
# ---------------------------------------------------------------------------------------------------------------
def _renderings(value) -> list:
    """How the pre-registration writes a value: German numbers, dates as dd.mm.yyyy or ISO, clock times."""
    if isinstance(value, str):
        date, _, clock = value.partition(" ")
        y, m, d = date.split("-")
        return [("{}.{}.{}".format(d, m, y), date)] + ([(clock,)] if clock else [])
    if float(value).is_integer():
        return [("{:,}".format(int(abs(value))).replace(",", " "),)]
    return [(str(value).replace(".", ","),)]


def _section(text: str, heading: str) -> str:
    """The section of the binding German original that carries the English section name ``heading``."""
    if heading == "Header":
        return text[:text.index("\n## ")]
    original = nc.SECTION_ORIGINAL[heading]
    m = re.search(r"^## " + re.escape(original) + r"\b.*?(?=^## |\Z)", text, re.S | re.M)
    return m.group(0) if m else ""


# How the binding German original words a constant where the value alone does not identify it; verbatim quotes.
ALIASES = {"bp_factor": ["10⁴"], "q_sell": ["−1"], "q_buy": ["+1"], "managers": ["SM", "Legacy-PM", "PM2"],
           "hypotheses": ["H1", "H2", "H3", "H4"], "addenda": ["## Nachtrag 4"], "addenda_total": ["## Nachtrag 6"],
           "cash_zero": ["cash = 0"], "dominant_makers": ["zehn"], "seed": ["20260924"],
           "interval_lower_percentile": ["5. und"],
           "interval_upper_percentile": ["95. Perzentil"], "api_discount_pct": ["mit 2 %"],
           "dose_filter_pct": ["unter 1 %"], "validation_p95_pct": ["unter 1 %"], "h3_threshold": ["grösser als 2"],
           "delta_edge_10": ["[0,10)"], "delta_edge_25": ["[10,25)"], "delta_edge_40": ["[25,40)"],
           "delta_edge_60": ["[40,60)"], "delta_edge_60_delta": ["[40,60)"], "delta_edge_75": ["[60,75)"],
           "delta_edge_90": ["[75,90)"], "tenor_edge_2d": ["≤2 d"], "tenor_edge_7d": ["(2,7]"],
           "tenor_edge_30d": ["(7,30]"], "tenor_edge_90d": ["(30,90]"]}


def test_every_constant_stands_in_its_section_of_the_pre_registration():
    assert len(nc.CONSTANTS) >= 40
    for name, (value, meaning, path, heading) in nc.CONSTANTS.items():
        part = _section((REPO / path).read_text(), heading)
        assert part, (name, heading)
        if heading != "Header":   # the section name is that of the English translation next to the original
            translation = (REPO / path).with_name("PREREGISTRATION.md").read_text()
            assert re.search(r"^## " + re.escape(heading) + r"\b", translation, re.M), (name, heading)
        if name in ALIASES:
            for piece in ALIASES[name]:
                assert piece in part, (name, piece, heading)
            continue
        for options in _renderings(value):
            assert any(o in part for o in options), (name, options, heading)


# ---------------------------------------------------------------------------------------------------------------
# Report, exit status, template
# ---------------------------------------------------------------------------------------------------------------
def test_report_and_exit_status(results, tmp_path, monkeypatch):
    monkeypatch.setattr(nc, "default_commit_resolver", lambda repo=None: resolve)
    report = tmp_path / "NUMBER_CHECK.md"
    cases = {"good": ("The correlation is 0.903.", "% src summary.json:h1_stat 0.903", 0),
             "undeclared": ("The correlation is 0.777.", "", 1),
             "unused": ("The correlation is high.", "% src summary.json:h1_stat 0.903", 1),
             "stale": ("The correlation is 0.904.", "% src summary.json:h1_stat 0.904", 1)}
    for name, (sentence, decl, status) in cases.items():
        path = tmp_path / (name + ".tex")
        path.write_text(tex("\\section{R}\n" + sentence + "\n" + decl + "\n"))
        assert nc.main(["--tex", str(path), "--results", str(results), "--report", str(report)]) == status, name
        text = report.read_text()
        assert ("**Errors: 0** (none)" in text) == (status == 0)
        assert "## Constants of the pre-registration" in text and "cell_min_fills" in text


def test_template_lists_every_number_in_order_with_suggestions(results):
    t = tex("\\section{R}\nThe correlation is 0.903 and the share 42.0 per cent over 200 fills.\n"
            "% src summary.json:h1_stat 0.903\n")
    out = nc.template(t, results, resolve_commit=resolve, git_date=git_date)
    lines = [l for l in out.splitlines() if l.startswith("% src")]
    assert lines[0].startswith("% src summary.json:h1_stat 0.903")
    assert lines[1].startswith("% src ??? 42.0") and "summary.json:h2_share_nonpositive~pct" in lines[1]
    assert lines[2].startswith("% src ??? 200") and "const:cell_min_fills" in lines[2]


# ---------------------------------------------------------------------------------------------------------------
# Mutations and swaps on sentences of paper2/main.tex (audit A19 to A21, A33)
# ---------------------------------------------------------------------------------------------------------------
MANUSCRIPT = r"""\begin{document}
\begin{abstract}
Capital does not reorder the moneyness-by-tenor map of the edge in the registered sense (rank correlation 0.903;
H1 rejected), but much of that correlation is the sign of the edge; among profitable cells the two rankings
differ markedly. In the books of the four makers under the newer portfolio manager (ETH and HYPE only), a fill
binds a median 3.5 per cent of its stand-alone capital per contract. Four hypotheses were registered before any
capital figure of the registered analysis was computed; two are rejected.
% src summary.json:h1_stat 0.903
% src text:two_rankings two
% src summary.json:h2_n_accounts four
% src summary.json:h2_stat~pct 3.5
% src derived:n_hypotheses Four
% src derived:n_rejected two
\end{abstract}
\maketitle
\section{The engine and what it returns}\label{sec:engine}
The off-chain engine discounts PM2 at an undocumented flat rate, which a box spread puts at 2.0000 per cent.
The on-chain engine discounts with the rate feed, which ranged from 3.64 to 3.82
per cent across the same expiries. In the probes that preceded this paper it gave a ratio of standard to PM2
margin of 11.86 at block 44\,810\,149 on 17 September at 10:45.
% src semantics/box_discount.json:box_*.r_api~pct 2.0000
% src semantics/box_discount.json:box_*.r_chain~min~pct 3.64
% src semantics/box_discount.json:box_*.r_chain~max~pct 3.82
% src semantics/factors.csv:F_Cnet@book=b17,case=B 11.86
% src semantics/factors.csv:block@case=B 44\,810\,149
% src semantics/factors.csv:measurement@case=B 17 September 10:45

\section{Data and measurement}\label{sec:data}
The fills are every BTC, ETH and HYPE option fill from 11 January 2024 to the pilot cut of 17 September 2026,
603\,940 in all, each with the net edge thirty minutes after the fill. Intervals are 90 per cent percentile
intervals of a cluster bootstrap over UTC days with 9\,999 draws, and H4 uses 100 placebo dates at least 28
days from any parameter change. Before any capital entered a test, the offline replicas were validated
against \texttt{eth\_call} on 100 random blocks per underlying and manager (registered: at least 48).
% src summary.json:sample_start_utc 11 January 2024
% src summary.json:cutoff_day 17 September 2026
% src summary.json:fills_total 603\,940
% src const:markout_minutes thirty
% src const:interval_pct 90
% src const:bootstrap_draws 9\,999
% src const:placebo_dates 100
% src const:placebo_gap_days 28
% src summary.json:validation_single_blocks_per_cell 100
% src const:validation_min_blocks 48

\section{Results}\label{sec:results}

\subsection{The capital denominator and the map (H1)}
Under PM2 a single maker sell binds between 7.8 and 17.7 per cent of notional in BTC,
between 7.1 and 21.4 in ETH and between 17.5 and 38.7 in HYPE. The ratio of standard margin to PM2 capital in
the median sell cell is 0.943 in BTC, 0.902 in ETH and 0.875 in HYPE. After the parameter change of 20 August
2026 it is 1.398 and 1.140 for BTC and ETH. The legacy manager needs more, with medians of 1.382 and
1.355 for BTC and ETH sells.
% src fig_f1_a.csv:kappa_pm2@ccy=BTC,side=sell,occupied=True~min 7.8
% src fig_f1_a.csv:kappa_pm2@ccy=BTC,side=sell,occupied=True~max 17.7
% src fig_f1_a.csv:kappa_pm2@ccy=ETH,side=sell,occupied=True~min 7.1
% src fig_f1_a.csv:kappa_pm2@ccy=ETH,side=sell,occupied=True~max 21.4
% src fig_f1_a.csv:kappa_pm2@ccy=HYPE,side=sell,occupied=True~min 17.5
% src fig_f1_a.csv:kappa_pm2@ccy=HYPE,side=sell,occupied=True~max 38.7
% src fig_f1_b.csv:row_median@ccy=BTC,side=sell,manager=sm,regime=pooled 0.943
% src fig_f1_b.csv:row_median@ccy=ETH,side=sell,manager=sm,regime=pooled 0.902
% src fig_f1_b.csv:row_median@ccy=HYPE,side=sell,manager=sm,regime=pooled 0.875
% src summary.json:event_btc_pm2_20260820_refbook_day 20 August 2026
% src fig_f1_b.csv:row_median@ccy=BTC,side=sell,manager=sm,regime=r4 1.398
% src fig_f1_b.csv:row_median@ccy=ETH,side=sell,manager=sm,regime=r4 1.140
% src fig_f1_b.csv:row_median@ccy=BTC,side=sell,manager=pm,regime=pooled 1.382
% src fig_f1_b.csv:row_median@ccy=ETH,side=sell,manager=pm,regime=pooled 1.355

Across the cells the rank correlation is 0.903, with a 90 per cent interval from 0.881 to 0.907. Since the
upper bound exceeds 0.5, the registered rule rejects H1. The median cell moves by 14 ranks; BTC buys with two to
seven days to expiry rise from rank 76 to 4. The 20 fills with a PM2 capital that is not positive stay in the
sums.
% src summary.json:h1_stat 0.903
% src const:interval_pct 90
% src summary.json:h1_lo 0.881
% src summary.json:h1_hi 0.907
% src const:h1_threshold 0.5
% src summary.json:h1_rank_shift_median_abs 14
% src const:tenor_edge_2d two
% src const:tenor_edge_7d seven
% src h1_cells.csv:rank_A@BTC|buy|00-10|2-7d 76
% src h1_cells.csv:rank_B@BTC|buy|00-10|2-7d 4
% src summary.json:h1_n_fills_k_le_0 20

\subsection{A fill in a maker's book (H2)}
Its median is 0.0345, and 42.0 per cent of the fills leave the capital of the book unchanged or reduce it. H2
is not rejected: in these books the median fill costs 3.5 per cent of what it would cost alone.
About a quarter of the fills free more than 0.28 of their stand-alone capital, a quarter bind more than 0.63
of it.
% src summary.json:h2_stat 0.0345
% src summary.json:h2_share_nonpositive~pct 42.0
% src summary.json:h2_stat~pct 3.5
% src fig_h2_dist.csv:value@label=all,variant=ratio,kind=quantile,x=0.25~neg 0.28
% src fig_h2_dist.csv:value@label=all,variant=ratio,kind=quantile,x=0.75 0.63

\subsection{The price of capital (H4)}
The registered set holds its events once changes of the same day are merged; 14 pass the dose filter. Almost
every kept event made the reference book cheaper, by between 3.4 and 37.4
log per cent; for BTC the largest step came on 20 August 2026, when the PM2 capital of the straddle fell by
22.9 per cent (26.0 log per cent). Only the events of 8 January 2026 raised it, by about 1.6 log per cent.
The estimate of $\beta$ is $-4.60$ basis points of the index per unit of log capital, with a one-sided wild
cluster bootstrap $p$ of 0.6224. Per underlying the estimate is $-3.42$ for BTC, $-1.90$ for ETH and
$-10.12$ for HYPE, on sell cells alone $-3.81$, and with the dose weighted by the open-interest share $-5.13$,
each with a one-sided $p$ above 0.5; the placebo dates of ETH under
PM2 can be drawn from 10 days only, between 16 July and 25 July 2025.
% src summary.json:events_kept 14
% src summary.json:event_eth_pm2_20260524_refbook_log_change~neg~pct~down 3.4
% src summary.json:event_hype_pm2_20260524_refbook_log_change~neg~pct~down 37.4
% src summary.json:event_btc_pm2_20260820_refbook_day 20 August 2026
% src summary.json:event_btc_pm2_20260820_refbook_change~neg~pct~down 22.9
% src summary.json:event_btc_pm2_20260820_refbook_log_change~neg~pct~down 26.0
% src summary.json:event_btc_pm2_20260108_refbook_day 8 January 2026
% src summary.json:event_btc_pm2_20260108_refbook_log_change~pct~up 1.6
% src summary.json:h4_stat -4.60
% src summary.json:h4_p 0.6224
% src summary.json:sens_h4_by_ccy_btc_beta -3.42
% src summary.json:sens_h4_by_ccy_eth_beta -1.90
% src summary.json:sens_h4_by_ccy_hype_beta -10.12
% src summary.json:h4_review_sells_only_beta -3.81
% src summary.json:h4_review_oi_weighted_beta -5.13
% src summary.json:sens_h4_by_ccy_btc_p,sens_h4_by_ccy_eth_p,sens_h4_by_ccy_hype_p,h4_review_sells_only_p,h4_review_oi_weighted_p~min >0.5
% src h4.json:placebo.admissible_days.ETH-pm2-20260108.days 10
% src h4.json:placebo.admissible_days.ETH-pm2-20260108.first 16 July
% src h4.json:placebo.admissible_days.ETH-pm2-20260108.last 25 July 2025

\begin{figure}[t]
  \centering
  \includegraphics[width=\linewidth]{figures/f5.pdf}
  \caption{\textbf{The engine over time.} Grey bars are the windows of 14 days on either side of each kept
  event; the windows of January and of May 2026 overlap.}
  \label{fig:f5}
% src const:regression_window_days 14
% src summary.json:event_btc_pm2_20260524_refbook_day May 2026
\end{figure}

\subsection{Sensitivities}
Under maintenance margin $\rho$ is 0.903.
% src summary.json:sens_b_mm_h1_pm2_mm_stat 0.903

\section*{Data, code and pre-registration}
The four hypotheses were committed on 24 September 2026 at 22:33 UTC+2, in commit \texttt{cc0a29f}. Four
dated addenda of 25 September 2026 follow.
% src const:hypotheses four
% src git:cc0a29f 24 September 2026 22:33
% src const:addenda Four
% src git:e492ba1 25 September 2026

\bibliographystyle{x}
\bibliography{refs}
\end{document}
"""

# the twelve swaps of data/p2/audit/zahlen/swap_check.py, verbatim
SWAPS = [("$-3.42$ for BTC, $-1.90$ for ETH", "$-1.90$ for BTC, $-3.42$ for ETH"),
         ("0.943 in BTC, 0.902 in ETH and 0.875 in HYPE", "0.875 in BTC, 0.943 in ETH and 0.902 in HYPE"),
         ("it is 1.398 and 1.140 for BTC and ETH", "it is 1.382 and 1.355 for BTC and ETH"),
         ("between 7.8 and 17.7 per cent of notional in BTC", "between 7.1 and 21.4 per cent of notional in BTC"),
         ("by between 3.4 and 37.4\nlog per cent", "by between 1.6 and 26.0\nlog per cent"),
         ("raised it, by about 1.6 log per cent", "raised it, by about 3.4 log per cent"),
         ("free more than 0.28 of their", "free more than 0.63 of their"),
         ("from 3.64 to 3.82\nper cent", "from 3.64 to 3.64\nper cent"),
         ("each with a one-sided $p$ above 0.5;", "each with a one-sided $p$ above 0.6;"),
         ("on 100 random blocks per underlying", "on 200 random blocks per underlying"),
         ("between 16 July and 25 July 2025", "between 16 July and 25 August 2025"),
         ("can be drawn from 10 days only", "can be drawn from 54 days only")]

MUT_NUM = re.compile(r"(?<![A-Za-z0-9_.{\\])(\d+(?:\\,\d{3})*(?:\.\d+)?)(?![A-Za-z0-9_}])")
NEXT_WORD = {"two": "three", "four": "five", "Four": "Five", "seven": "eight", "thirty": "forty"}
PREV_WORD = {"two": "three", "four": "three", "Four": "Three", "seven": "six", "thirty": "twenty"}


def _all_ok(results: Path, t: str) -> bool:
    return all(v.ok for v in nc.check(t, results, resolve_commit=resolve, git_date=git_date))


def test_the_manuscript_fixture_passes(results):
    vs = nc.check(MANUSCRIPT, results, resolve_commit=resolve, git_date=git_date)
    assert [(v.unit, v.token.raw, v.how, v.detail) for v in vs if not v.ok] == []
    assert len(vs) > 75 and {v.how for v in vs} >= {"result", "constant", "text", "git", "commit"}


def _text_mutants(t: str):
    """Every printed number of the prose with its last digit one up and one down, and spelled numbers."""
    lines = t.split("\n")
    for i, line in enumerate(lines):
        if line.lstrip().startswith("%") or "\\label" in line or "\\includegraphics" in line:
            continue
        for m in MUT_NUM.finditer(line):
            if line[:m.start()].endswith("UTC+") or re.search(r"\\texttt\{[^}]*$", line[:m.start()]):
                continue
            digit = int(m.group(1)[-1])
            for new in (digit + 1, digit - 1):
                if 0 <= new <= 9:
                    mutated = line[:m.end() - 1] + str(new) + line[m.end():]
                    yield "{}: {} -> {}".format(i + 1, m.group(1), m.group(1)[:-1] + str(new)), \
                        "\n".join(lines[:i] + [mutated] + lines[i + 1:])
        for m in re.finditer(r"\b(" + "|".join(NEXT_WORD) + r")\b", line):
            for table in (NEXT_WORD, PREV_WORD):
                mutated = line[:m.start()] + table[m.group(1)] + line[m.end():]
                yield "{}: {} -> {}".format(i + 1, m.group(1), table[m.group(1)]), \
                    "\n".join(lines[:i] + [mutated] + lines[i + 1:])


def test_every_digit_changed_in_the_text_fails(results):
    t = MANUSCRIPT
    assert _all_ok(results, t)
    mutants = list(_text_mutants(t))
    assert len(mutants) > 150
    survived = [label for label, m in mutants if _all_ok(results, m)]
    assert survived == []


def test_a_number_changed_in_text_and_declaration_alike_fails_on_its_value(results):
    """The author edits the text and its declaration but not the data: the value check must catch it."""
    t = MANUSCRIPT
    decl = re.compile(r"^(% src (\S+) )(.*)$", re.M)
    literals = set()
    for m in decl.finditer(t):
        if not m.group(2).startswith("text:") and not m.group(3).startswith((">", "<")):
            literals |= {s for s in MUT_NUM.findall(m.group(3))}
    assert len(literals) > 50
    survived = []
    for lit in sorted(literals):
        digit = int(lit[-1])
        for new in (digit + 1, digit - 1):
            if not 0 <= new <= 9:
                continue
            repl = lit[:-1] + str(new)
            pat = re.compile(r"(?<![\d.A-Za-z\\])" + re.escape(lit) + r"(?!\.?\d)")

            def sub_line(line: str) -> str:
                if line.startswith("% src "):
                    head, _, printed = line.partition(" ")[2].partition(" ")
                    return "% src " + head + " " + pat.sub(repl, printed)
                return line if line.lstrip().startswith("%") else pat.sub(repl, line)
            mutated = "\n".join(sub_line(l) for l in t.split("\n"))
            vs = nc.check(mutated, results, resolve_commit=resolve, git_date=git_date)
            if not any(v.how == "mismatch" for v in vs):
                survived.append("{} -> {}".format(lit, repl))
    assert survived == []


@pytest.mark.parametrize("old,new", SWAPS)
def test_the_swaps_of_the_audit_fail(results, old, new):
    t = MANUSCRIPT
    assert old in t
    assert _all_ok(results, t)
    assert not _all_ok(results, t.replace(old, new, 1))
