"""Offline tests for scripts/p2_build.py: log, source and caption checks, and the build with a fake tectonic."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import p2_build as pb  # noqa: E402

LOG_CLEAN = """This is XeTeX
LaTeX Warning: Some harmless warning.
Underfull \\hbox (badness 5832) in paragraph at lines 59--68
Package hyperref Warning: Ignoring empty anchor on input line 92.
"""
LOG_BAD = LOG_CLEAN + """Overfull \\hbox (12.3pt too wide) in paragraph at lines 10--12
LaTeX Warning: Reference `fig:f9' on page 3 undefined on input line 40.
LaTeX Warning: Citation `nobody2020' on page 1 undefined on input line 12.
! Undefined control sequence.
LaTeX Warning: File `figures/x.pdf' not found on input line 7.
"""

TEX = r"""\documentclass{article}
\begin{document}
\begin{abstract}
Short abstract.
\end{abstract}
\maketitle
\section{Introduction}
We cite \citep{ho1981} and show Figure~\ref{fig:f1}.
\begin{figure}[t]
  \includegraphics[width=\linewidth]{figures/f1.pdf}
  \caption{\textbf{What one contract costs.} Capital over 200 fills.}
  \label{fig:f1}
\end{figure}
\section{Conclusion}
Done.
\bibliographystyle{plain}
\bibliography{refs}
\end{document}
"""
BIB = "@article{ho1981,\n title={x}}\n@article{other2000,\n title={y}}\n"
LITERATUR = "| ho1981 | Ho and Stoll |\n| other2000 | Other |\n"
BUDGET = {"abstract": 50, "Introduction": 50, "Conclusion": 50}


def test_log_problems_finds_what_must_stop_a_build():
    clean = pb.log_problems(LOG_CLEAN)
    assert not any(clean.values())                       # underfull boxes and hyperref notes are allowed
    bad = pb.log_problems(LOG_BAD, console="error: something failed")
    assert len(bad["overfull"]) == 1
    assert bad["undefined references"] and bad["undefined citations"]
    assert len(bad["errors"]) == 2                       # "! ..." in the log and "error:" on the console
    assert bad["missing files"]


def test_dashes_in_prose_but_not_in_math_urls_or_comments():
    assert pb.dashes(TEX) == []
    ok = TEX.replace("Done.", r"Done $C - \mathrm{net}$ at \url{https://a--b.org} % an -- aside" "\n")
    assert pb.dashes(ok) == []
    for bad in ["Done -- twice.", "Done — twice.", "Done – twice.", "Done - twice."]:
        assert pb.dashes(TEX.replace("Done.", bad)), bad
    assert pb.dashes(TEX.replace("Done.", "A moneyness-by-tenor map, maker-days.")) == []


def test_placeholders_outside_comments():
    assert pb.placeholders(TEX) == []
    assert pb.placeholders(TEX.replace("Done.", r"Done \PH{h1-rho}.")) == [r"\PH{h1-rho}"]
    assert pb.placeholders(TEX.replace("Done.", r"Done. % \PH{old}")) == []


def test_citations_must_be_in_the_bib_and_in_the_literature_file():
    assert not any(pb.citation_problems(TEX, BIB, LITERATUR).values())
    tex = TEX.replace(r"\citep{ho1981}", r"\citep{ho1981,missing2001}")
    got = pb.citation_problems(tex, BIB, LITERATUR)
    assert got["citations not in refs.bib"] == ["missing2001"]
    got = pb.citation_problems(TEX, BIB, "| other2000 |")
    assert got["citations not in LITERATUR.md"] == ["ho1981"]


def test_figure_problems(tmp_path):
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "f1.pdf").write_bytes(b"%PDF")
    assert not any(pb.figure_problems(TEX, tmp_path, ["f1"]).values())
    got = pb.figure_problems(TEX, tmp_path, ["f1", "f2"])
    assert got["figure slots missing"] == ["f2"]
    got = pb.figure_problems(TEX.replace(r"Figure~\ref{fig:f1}", "a figure"), tmp_path, ["f1"])
    assert got["figures never referenced"] == ["fig:f1"]
    (tmp_path / "figures" / "f1.pdf").unlink()
    assert pb.figure_problems(TEX, tmp_path, ["f1"])["figure files missing"] == ["figures/f1.pdf"]


def test_module_caption_is_read_without_import(tmp_path):
    mod = tmp_path / "a1.py"
    mod.write_text('import matplotlib\nHEAD = (r"\\textbf{Title.} "\n        "first part.")\n'
                   'TAIL = "Last part."\nCAPTION = " ".join([HEAD, "middle.", TAIL])\n')
    assert pb.module_caption(mod) == r"\textbf{Title.} first part. middle. Last part."
    (tmp_path / "f1.py").write_text("CAPTION = compute()\n")
    assert pb.module_caption(tmp_path / "f1.py") is None


def test_caption_drift_with_placeholders_and_exceptions(tmp_path):
    (tmp_path / "f1.py").write_text('CAPTION = "What one contract costs. Capital over \\\\PH{n} fills."\n')
    assert pb.caption_drift(TEX, tmp_path, exceptions=[]) == []           # \PH stands for "200"
    (tmp_path / "f1.py").write_text('CAPTION = "What one contract costs. Capital over all fills."\n')
    assert pb.caption_drift(TEX, tmp_path, exceptions=[]) == ["f1"]
    ex = [("f1", "over all fills.", "over 200 fills.", "reason")]
    assert pb.caption_drift(TEX, tmp_path, exceptions=ex) == []


def _paper(tmp_path: Path, tex: str = TEX) -> Path:
    paper = tmp_path / "paper2"
    (paper / "figures").mkdir(parents=True)
    (paper / "figures" / "f1.pdf").write_bytes(b"%PDF")
    (paper / "main.tex").write_text(tex)
    (paper / "refs.bib").write_text(BIB)
    (tmp_path / "LITERATUR.md").write_text(LITERATUR)
    return paper


def fake_tectonic(log: str, returncode: int = 0, pdf: bool = True):
    def run(cmd, cwd=None, capture_output=True, text=True):
        out = Path(cmd[cmd.index("--outdir") + 1])
        (out / "main.log").write_text(log)
        if pdf:
            (out / "main.pdf").write_bytes(b"%PDF-1.5 fake")
        return subprocess.CompletedProcess(cmd, returncode, "note: done", "")
    return run


def _build(tmp_path, paper, runner, text="Introduction Conclusion References"):
    return pb.build(paper, runner=runner, numbers=False, read_pdf=lambda p: (3, text),
                    literatur_path=tmp_path / "LITERATUR.md", figs=tmp_path / "nofigs", budget=BUDGET,
                    slots=["f1"], must=["Introduction", "Conclusion", "References"])


def test_clean_build(tmp_path):
    paper = _paper(tmp_path)
    rep = _build(tmp_path, paper, fake_tectonic(LOG_CLEAN))
    assert rep.failed() == [] and rep.pages == 3
    assert (paper / "main.pdf").read_bytes().startswith(b"%PDF")


def test_build_fails_on_log_pdf_and_source_problems(tmp_path):
    paper = _paper(tmp_path)
    assert "overfull" in _build(tmp_path, paper, fake_tectonic(LOG_BAD)).failed()
    assert "errors" in _build(tmp_path, paper, fake_tectonic(LOG_CLEAN, returncode=1)).failed()
    assert "missing parts" in _build(tmp_path, paper, fake_tectonic(LOG_CLEAN), text="Introduction").failed()
    assert "unresolved ?? in PDF" in _build(tmp_path, paper, fake_tectonic(LOG_CLEAN),
                                            text="Introduction Conclusion References Figure ??").failed()
    rep = _build(tmp_path, paper, fake_tectonic(LOG_CLEAN, pdf=False))
    assert rep.problems["missing parts"] == ["no PDF written"]
    paper = _paper(tmp_path / "b", TEX.replace("Done.", r"Done -- \PH{x}."))
    failed = _build(tmp_path / "b", paper, fake_tectonic(LOG_CLEAN)).failed()
    assert "placeholders" in failed and "dashes in prose" in failed


def test_build_fails_over_budget(tmp_path):
    paper = _paper(tmp_path, TEX.replace("Done.", "word " * 80))
    assert "over word budget" in _build(tmp_path, paper, fake_tectonic(LOG_CLEAN)).failed()


def test_every_slot_of_the_manuscript_is_listed():
    assert pb.SLOTS == ["t1", "t2", "f1", "f2", "f3", "f4", "f5", "f6", "a1"]
    assert {"Competing interest", "Data, code and pre-registration", "References", "G13"} <= set(pb.MUST_CONTAIN)
