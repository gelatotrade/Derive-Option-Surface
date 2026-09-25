#!/usr/bin/env python3
"""Build the manuscript and refuse to call a halted run a success.

tectonic keeps going after a recoverable LaTeX error and still writes a PDF, so a missing section can hide
behind a clean-looking log.  This checks the log for errors, then checks that the parts that must be in the
finished paper are actually in it, and only then reports the page count and the word budget.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p1_wordcount as wc  # noqa: E402

PAPER = Path("paper")
MUST_CONTAIN = ["Competing interest", "Data, code and pre-registration", "Use of generative tools",
                "References", "Conclusion", "G13"]


def main() -> int:
    run = subprocess.run(["tectonic", "main.tex"], cwd=PAPER, capture_output=True, text=True)
    log = run.stdout + run.stderr
    errors = [line for line in log.splitlines() if line.lower().startswith("error")]
    overfull = [line for line in log.splitlines() if "overfull" in line.lower()]
    if run.returncode != 0 or errors:
        print("BUILD FAILED")
        print("\n".join(errors[:10]) or log[-2000:])
        return 1

    import pypdf
    reader = pypdf.PdfReader(PAPER / "main.pdf")
    text = " ".join((page.extract_text() or "") for page in reader.pages)
    missing = [needle for needle in MUST_CONTAIN if needle not in text]
    rows = wc.check((PAPER / "main.tex").read_text())
    over = [r for r in rows if r["over"]]

    print("pages           {}".format(len(reader.pages)))
    print("words           {}".format(sum(r["words"] for r in rows)))
    print("overfull boxes  {}".format(len(overfull)))
    print("missing parts   {}".format(", ".join(missing) if missing else "none"))
    print("over budget     {}".format(", ".join(r["section"] for r in over) if over else "none"))
    if missing:
        print("\nA part of the paper did not make it into the PDF. A recoverable LaTeX error stops output "
              "without stopping the build; read the log before trusting the page count.")
    return 1 if (missing or over) else 0


if __name__ == "__main__":
    raise SystemExit(main())
