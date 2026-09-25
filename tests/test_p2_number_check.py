"""Offline tests for scripts/p2_number_check.py on a synthetic results directory with known answers."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import p2_number_check as nc  # noqa: E402

KNOWN_COMMITS = {"1d13227"}


def resolve(sha: str) -> bool:
    return sha in KNOWN_COMMITS


@pytest.fixture()
def results(tmp_path: Path) -> Path:
    r = tmp_path / "results"
    (r / "semantik").mkdir(parents=True)
    (r / "summary.json").write_text(json.dumps({
        "fills_total": 603940, "h1_stat": 0.9029439, "h1_lo": 0.8805637, "h2_stat": 0.0345401,
        "h2_share_nonpositive": 0.4196209, "cutoff_day": "2026-09-17", "h4_stat": -4.599234,
        "validation_single_median_rel": 8.667e-10, "event_x_refbook_change": -0.2293,
        "long_draws": list(range(100, 200)),
    }))
    (r / "h1.json").write_text(json.dumps({"stat": 0.9029439, "rejected": True}))
    (r / "h2.json").write_text(json.dumps({"stat": 0.0345, "rejected": False}))
    (r / "h3.json").write_text(json.dumps({"stat": 4.7467, "rejected": False}))
    (r / "h4.json").write_text(json.dumps({"stat": -4.6, "rejected": True}))
    (r / "semantik" / "box_diskont.json").write_text(json.dumps({"box_1": [{"r_chain": 0.0364},
                                                                          {"r_chain": 0.0382}]}))
    (r / "semantik" / "faktoren.csv").write_text(
        "messung,F_Cnet\nhistorisch 17.09. 10:45:13Z Blk 44810149,11.86\n")
    (r / "table.csv").write_text("cell,kappa,rank\nBTC|sell,7.798,76\nETH|sell,17.690,4\nBTC|buy,0.612,121\n")
    (r / "h1_cells.csv").write_text("cell,occupied,A_bp\na,True,1.5\nb,True,-0.3\nc,False,2.0\nd,True,0.2\n")
    return r


def tex(body: str, front: str = "") -> str:
    return ("\\begin{document}\n\\begin{abstract}\nAbstract text.\n\\end{abstract}\n" + front +
            "\n\\maketitle\n" + body + "\n\\bibliographystyle{x}\n\\bibliography{refs}\n\\end{document}\n")


def verdicts(results: Path, body: str, front: str = ""):
    return nc.check(tex(body, front), results, resolve_commit=resolve)


def by_raw(vs):
    return {v.token.raw: v for v in vs}


def test_rounding_scales_and_signs(results):
    vs = by_raw(verdicts(results, r"""\section{Results}
The correlation is 0.903, not 0.905. The share is 42.0 per cent and the median 3.5 per cent.
The estimate is $-4.60$ and the book fell by 22.9 per cent. There were 603\,940 fills.
"""))
    assert vs["0.903"].ok and "summary.json:h1_stat" in vs["0.903"].source
    assert not vs["0.905"].ok
    assert vs["42.0"].ok and "×100" in vs["42.0"].detail
    assert vs["3.5"].ok
    assert vs["-4.60"].ok
    assert vs["22.9"].ok and "Betrag" in vs["22.9"].detail      # magnitude of a negative change
    assert vs["603940"].ok and vs["603940"].detail.startswith("=")


def test_printed_minus_needs_a_negative_value(results):
    vs = by_raw(verdicts(results, "\\section{Results}\nA value of $-0.903$.\n"))
    assert not vs["-0.903"].ok


def test_range_passes_its_unit_to_the_first_number(results):
    vs = by_raw(verdicts(results, "\\section{Engine}\nThe rate ranged from 3.64 to 3.82 per cent.\n"))
    assert vs["3.64"].ok and vs["3.82"].ok
    assert vs["3.64"].token.unit == "percent"


def test_scientific_notation_and_block_numbers_in_strings(results):
    vs = by_raw(verdicts(results, "\\section{Data}\nThe median is $8.7\\times10^{-10}$ at block 44\\,810\\,149.\n"))
    assert vs["8.7e-10"].ok
    assert vs["44810149"].ok and "faktoren.csv" in vs["44810149"].source


def test_identifiers_comments_formulas_and_citations_are_not_numbers(results):
    vs = verdicts(results, r"""\section{Results}
PM2 and H1 under UTC+2 in Addendum 2, see Figure~\ref{fig:f1} and \citet{albiez2026}.
% 12345 in a comment
\begin{equation}
  e = 10^4 \frac{a}{b} + 7.77
\end{equation}
""")
    assert vs == []


def test_constants_and_spelled_numbers(results):
    vs = verdicts(results, "\\section{Data}\nThe threshold is 0.5, books above 63 options, ten makers, one day.\n")
    got = {v.token.raw: v for v in vs}
    assert got["0.5"].how == "constant" and got["63"].how == "constant"
    assert got["ten"].ok and got["ten"].token.spelled
    assert "one" not in got


def test_small_numbers_need_a_headline_source_or_three_digits(results):
    vs = by_raw(verdicts(results, "\\section{Results}\nKappa runs from 7.80 to 17.7, and 0.61 or 0.612.\n"))
    assert vs["7.80"].ok and "table.csv" in vs["7.80"].source      # three significant digits
    assert vs["17.7"].ok
    assert not vs["0.61"].ok                                        # two digits, rounded, only in a large table
    assert vs["0.612"].ok                                           # exact


def test_exact_integers_in_tables_count(results):
    vs = by_raw(verdicts(results, "\\section{Results}\nFrom rank 121 to rank 76.\n"))
    assert vs["121"].ok and vs["76"].ok


def test_dates_times_and_commits(results):
    vs = by_raw(verdicts(results, r"""\section{Back}
Cut on 17 September 2026 at 12:00, registered on 24 September 2026 in \texttt{1d13227}, not
\texttt{abcdef1}; nothing happened on 3 March 2021 or at 13:37.
"""))
    assert vs["17 September 2026"].ok and vs["17 September 2026"].how == "date"
    assert vs["12:00"].how == "constant"
    assert vs["24 September 2026"].how == "constant"
    assert vs["1d13227"].ok and vs["1d13227"].how == "commit"
    assert not vs["abcdef1"].ok
    assert not vs["3 March 2021"].ok
    assert not vs["13:37"].ok


def test_captions_are_checked_as_their_own_unit(results):
    vs = verdicts(results, r"""\section{Results}
Text.
\begin{figure}[t]
  \includegraphics{figures/f1.pdf}
  \caption{\textbf{Title.} A caption with 0.904 in it.}
  \label{fig:f1}
\end{figure}
""")
    bad = [v for v in vs if not v.ok]
    assert [(v.unit, v.token.raw) for v in bad] == [("caption fig:f1", "0.904")]


def test_declared_source_is_the_only_one_that_counts(results):
    body = r"""\section{Results}
The correlation is 0.903.
% src summary.json:h2_stat 0.903
"""
    vs = verdicts(results, body)
    assert not vs[0].ok and vs[0].detail == "erklärte Quelle deckt die Zahl nicht"
    vs = verdicts(results, body.replace("h2_stat", "h1_*"))
    assert vs[0].ok and vs[0].how == "declared"


def test_declarations_hold_for_their_section_and_globally_from_the_front(results):
    body = r"""\section{A}
Value 0.903.
% src summary.json:h2_stat 0.903
\section{B}
Value 0.903.
"""
    vs = verdicts(results, body)
    assert [v.ok for v in vs] == [False, True]                      # B falls back to the generic match
    vs = verdicts(results, "\\section{A}\nValue 0.903.\n\\section{B}\nValue 0.903.\n",
                  front="% src summary.json:h2_stat 0.903\n")
    assert [v.ok for v in vs] == [False, False]


def test_declarations_inside_the_abstract_hold_for_the_abstract_only(results):
    t = ("\\begin{document}\n\\begin{abstract}\nThe correlation is 0.903.\n% src summary.json:h2_stat 0.903\n"
         "\\end{abstract}\n\\maketitle\n\\section{A}\nValue 0.903.\n\\bibliographystyle{x}\n\\end{document}\n")
    vs = nc.check(t, results, resolve_commit=resolve)
    assert [(v.unit, v.ok) for v in vs] == [("abstract", False), ("A", True)]   # A falls back to the generic match
    ok = t.replace("h2_stat", "h1_stat")
    vs = nc.check(ok, results, resolve_commit=resolve)
    assert vs[0].how == "declared" and vs[1].how == "result"
    assert nc.unused_declarations(ok, vs) == []


def test_declared_dates_and_times_bind_to_their_source(results):
    body = ("\\section{R}\nThe cut of 17 September 2026 at 10:45 and the addenda of 25 September 2026.\n"
            "% src summary.json:cutoff_day 17 September 2026\n% src git:c4fcb59 25 September 2026\n"
            "% src semantik/faktoren.csv:messung 10:45\n")
    t = tex(body)
    vs = nc.check(t, results, resolve_commit=resolve, git_date=lambda sha: "2026-09-25 01:29:58 +0200")
    got = {v.token.raw: v for v in vs}
    assert got["17 September 2026"].how == "declared" and got["17 September 2026"].source == "summary.json:cutoff_day"
    assert got["25 September 2026"].how == "declared" and got["25 September 2026"].source == "git:c4fcb59"
    assert got["10:45"].how == "declared"
    vs = nc.check(t, results, resolve_commit=resolve, git_date=lambda sha: "2026-09-24 23:29:58 +0000")
    assert not {v.token.raw: v for v in vs}["25 September 2026"].ok       # the commit is of another day
    wrong = tex("\\section{R}\nOn 17 September 2026.\n% src semantik/faktoren.csv:messung 17 September 2026\n")
    assert not nc.check(wrong, results, resolve_commit=resolve)[0].ok     # the declared file has no such date
    const = tex("\\section{R}\nFrom 11 January 2024.\n% src const:sample 11 January 2024\n")
    v = nc.check(const, results, resolve_commit=resolve)[0]
    assert v.ok and v.how == "declared" and nc.unused_declarations(const, [v]) == []


def test_declared_csv_column_and_row(results):
    vs = verdicts(results, "\\section{R}\nKappa 7.8 and rank 4.\n% src table.csv:kappa 7.8\n"
                           "% src table.csv:rank@ETH|sell 4\n")
    assert all(v.ok and v.how == "declared" for v in vs)
    vs = verdicts(results, "\\section{R}\nRank 4.\n% src table.csv:rank@BTC|sell 4\n")
    assert not vs[0].ok


def test_derived_counts(results):
    vs = verdicts(results, "\\section{R}\nTwo of four are rejected; 2 cells are positive.\n"
                           "% src derived:n_rejected Two\n% src derived:h1_cells_pos 2\n")
    got = {v.token.raw: v for v in vs}
    assert got["Two"].how == "declared" and got["2"].how == "declared"


def test_long_numeric_lists_are_not_sources(results):
    vs = verdicts(results, "\\section{R}\nA draw of 150.\n")
    assert not vs[0].ok


def test_unused_declarations_are_listed(results):
    t = tex("\\section{R}\nNothing.\n% src summary.json:h1_stat 0.903\n")
    vs = nc.check(t, results, resolve_commit=resolve)
    assert nc.unused_declarations(t, vs) == [("summary.json:h1_stat", "0.903")]


def test_report_and_exit_status(results, tmp_path, monkeypatch):
    monkeypatch.setattr(nc, "default_commit_resolver", lambda repo=None: resolve)
    good = tmp_path / "good.tex"
    good.write_text(tex("\\section{R}\nThe correlation is 0.903 over 603\\,940 fills.\n"))
    bad = tmp_path / "bad.tex"
    bad.write_text(tex("\\section{R}\nThe correlation is 0.777.\n"))
    report = tmp_path / "ZAHLENPRUEFUNG.md"
    assert nc.main(["--tex", str(good), "--results", str(results), "--report", str(report)]) == 0
    text = report.read_text()
    assert "**Unbelegte Zahlen: 0** (keine)" in text and "## Konstanten der Präregistrierung" in text
    assert nc.main(["--tex", str(bad), "--results", str(results), "--report", str(report)]) == 1
    assert "0.777" in report.read_text()
