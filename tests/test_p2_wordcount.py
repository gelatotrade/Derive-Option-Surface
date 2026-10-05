"""Offline tests for scripts/p2_wordcount.py: counting rule of Paper 1, budget as a parameter."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import p2_wordcount as wc  # noqa: E402

TEX = r"""
\begin{document}
\begin{abstract}
One two three four five.
\end{abstract}
% a comment with words that must not count
\maketitle
\section{Introduction}\label{sec:intro}
Alpha beta gamma delta epsilon zeta.
% src summary.json:h1_stat 0.903
\begin{figure*}[t]
  \includegraphics{figures/t1.pdf}
  \caption{\textbf{A title.} A long caption with many words that must not be counted at all.}
  \label{fig:t1}
\end{figure*}
More words here now \citep{ho1981}.
\section{Results}
Only three words.
\subsection{A subsection}
Four more words here.
\section*{Competing interest}
Back matter is counted but has no budget.
\bibliographystyle{cas-model2-names}
\bibliography{refs}
\end{document}
"""


def test_counts_prose_without_figures_captions_comments_or_citations():
    got = wc.sections(TEX)
    assert got["abstract"] == 5
    assert got["Introduction"] == 10          # six plus four; caption, comment and citation excluded
    assert got["Results"] == 3 + 2 + 4        # subsection title and text belong to the section
    assert got["Competing interest"] == 8
    assert "bibliography" not in " ".join(got).lower()


def test_tolerance_stretches_sections_but_not_the_hard_abstract():
    budget = {"abstract": 5, "Introduction": 10, "Results": 10}
    assert not any(r["over"] for r in wc.check(TEX, budget))
    rows = {r["section"]: r for r in wc.check(TEX, {"abstract": 4, "Introduction": 9, "Results": 10})}
    assert rows["abstract"]["over"] and rows["abstract"]["allowed"] == 4        # hard: no tolerance
    assert not rows["Introduction"]["over"] and rows["Introduction"]["allowed"] == 10   # 9 * 1.1 rounds to 10
    rows = {r["section"]: r for r in wc.check(TEX, {"Introduction": 9}, tolerance=0.0, hard=())}
    assert rows["Introduction"]["over"]


def test_default_budget_is_that_of_the_manuscript_plan():
    assert wc.BUDGET["Introduction"] == 600 and wc.BUDGET["Results"] == 1400
    assert wc.BUDGET["Discussion"] == 400 and wc.BUDGET["Conclusion"] == 200 and wc.BUDGET["abstract"] == 200
    assert wc.TOLERANCE == 0.10 and "abstract" in wc.HARD


def test_unbudgeted_sections_are_reported_and_missing_budgeted_ones_flagged():
    rows = {r["section"]: r for r in wc.check(TEX, {"Introduction": 50, "Discussion": 10})}
    assert rows["Results"]["budget"] is None and not rows["Results"]["over"]
    assert rows["Discussion"]["missing"] and rows["Discussion"]["words"] == 0


def test_main_reads_a_budget_file_and_fails_on_overrun(tmp_path, capsys):
    tex = tmp_path / "main.tex"
    tex.write_text(TEX)
    ok = tmp_path / "ok.json"
    ok.write_text(json.dumps({"abstract": 10, "Introduction": 20, "Results": 20}))
    over = tmp_path / "over.json"
    over.write_text(json.dumps({"abstract": 10, "Introduction": 5, "Results": 20}))
    assert wc.main([str(tex), "--budget", str(ok)]) == 0
    assert wc.main([str(tex), "--budget", str(over)]) == 1
    assert "Introduction" in capsys.readouterr().out
