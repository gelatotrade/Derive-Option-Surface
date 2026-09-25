from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import p1_wordcount as wc  # noqa: E402

TEX = r"""
\begin{abstract}
One two three four five.
\end{abstract}
\maketitle
\section{Introduction}
Alpha beta gamma delta epsilon zeta.
\begin{figure*}[t]
  \includegraphics{figures/t1.pdf}
  \caption{\textbf{A title.} A long caption with many words that must not be counted at all.}
  \label{fig:t1}
\end{figure*}
More words here now.
\section{Results}
Only three words.
\bibliographystyle{cas-model2-names}
\bibliography{refs}
"""


def test_counts_words_per_section_without_figures_or_captions():
    got = wc.sections(TEX)
    assert got["Introduction"] == 10         # six plus four, the caption is excluded
    assert got["Results"] == 3
    assert got["abstract"] == 5


def test_bibliography_is_not_a_section():
    assert "bibliography" not in " ".join(wc.sections(TEX)).lower()


def test_check_reports_only_the_sections_over_budget():
    out = wc.check(TEX, {"Introduction": 5, "Results": 50, "abstract": 150})
    over = [row for row in out if row["over"]]
    assert [row["section"] for row in over] == ["Introduction"]
    assert over[0]["words"] == 10 and over[0]["budget"] == 5


def test_check_tolerates_ten_percent():
    assert not any(r["over"] for r in wc.check(TEX, {"Introduction": 10, "Results": 3, "abstract": 5}))
    assert not any(r["over"] for r in wc.check(TEX, {"Introduction": 10, "Results": 3, "abstract": 5},
                                               tolerance=0.0))
    assert any(r["over"] for r in wc.check(TEX, {"Introduction": 9}, tolerance=0.0))
    assert not any(r["over"] for r in wc.check(TEX, {"Introduction": 10}, tolerance=0.10))


def test_unbudgeted_section_is_reported_but_not_over():
    rows = wc.check(TEX, {"Introduction": 20})
    results = [r for r in rows if r["section"] == "Results"][0]
    assert results["budget"] is None and results["over"] is False
