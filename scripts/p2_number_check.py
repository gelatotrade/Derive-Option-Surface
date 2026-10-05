#!/usr/bin/env python3
"""Check every number in the text of the Paper 2 manuscript against the one source declared for it.

Rule of the manuscript: every number, date and clock time in the checked text is bound, occurrence by occurrence,
to exactly one source by a declaration in the same unit: a value in a file under ``results/p2`` (including
``results/p2/semantics``), a named constant of the pre-registration (``CONSTANTS`` below, with the place where it is
registered), the date of a commit, a count over the verdicts, or, for a small count that the sentence itself makes
evident, a text label.  Nothing is searched.  A number without a declaration, a declaration without its number and
a value that no longer prints as the text says are all errors, and each fails ``p2_build.py``.

Units.  The abstract, the prose of every section and every subsection (subsection titles included) and every
figure caption.  Not checked: title, keywords, labels, references, citations, URLs, display formulas (notation)
and the bibliography.  Identifiers that carry digits (PM2, H1, M3, R4, UTC+2, Addendum 2) are not numbers.  Commit
hashes in ``\\texttt`` must exist in the repository.

Declarations.  A comment line

    % src <source> <printed> [<printed> ...]

binds printed numbers to one source.  It belongs to the unit it stands in: inside the abstract environment to the
abstract, inside a figure environment to that figure's caption, elsewhere to the prose of its section or
subsection; a declaration anywhere else (before the first section, outside the abstract) is an error.  Within a
unit the printed numbers of all declarations, read line by line and left to right, bind the occurrences of the
text in the same order: the declarations of a unit list its numbers in the order in which they are printed, one
entry per occurrence.  One declaration yields one value; several printed numbers on one line are repeated
occurrences of that value ("% src ident:ln_0_9 -0.105 -0.105").  "four" and "4" are different printed forms.

Sources:

    file.json:path                 an exact dotted path (list items by index), e.g. summary.json:h1_stat
    file.json:path1,path2,...      several paths; one value only through an aggregate or ~all
    file.json:pat*tern             a glob over the paths; likewise
    file.csv:col@filter            the column in the rows the filter selects.  filter: col=value[,col op value...]
                                   with op one of = != < <= > >= (numeric where both sides are numbers); a filter
                                   that is not of that form names the value of the first column; without @filter
                                   every row (a .jsonl file is read as file.jsonl:line.path)
    derived:name                   counts no single file states: n_rejected, n_not_rejected, n_hypotheses (over
                                   h1.json to h4.json) and h1_cells_pos (occupied cells of h1_cells.csv with A_bp > 0)
    const:name                     a constant of the pre-registration (CONSTANTS), matched exactly
    ident:name                     an arithmetic identity used as a reading aid (IDENTITIES)
    git:sha                        date and clock time of a commit (author date in its own time zone)
    text:label                     a whole number evident from the sentence itself; no data, listed in the report

Operations, appended with ``~`` and applied from left to right:

    ~pct  times 100     ~bp  times 10^4     ~neg  sign changed     ~abs  magnitude
    ~min ~max ~median ~mean ~sum ~count     reduce the selection to one value
    ~distinct                               the number of distinct values in the selection
    ~all                                    every selected value must match the printed number
    ~up ~down                               the direction the sentence gives the change (no effect on the value)

Without an aggregate or ``~all`` the selection must hold exactly one distinct value (rows that repeat one value, as
the row medians of a figure table, count as one).

Matching.  A number printed with d decimals matches a value v if |v - x| <= 0.5 * 10**-d (plus a relative 1e-9);
scientific notation (``8.7\\times10^{-10}``) works on the mantissa.  A scale, a magnitude or a change of sign only
comes from the operations: "fell by 22.9 per cent" is ``~neg~pct`` of a negative change, so a rise no longer
matches.  A printed number may carry a relation in the declaration (``>0.5``, ``<=2``): then every value must satisfy
it.  Dates ("17 September 2026", "September 2026", "17 September") and clock times ("08:00") match the one date or
time in the value: an ISO or compact date in a string, a day and month in the dotted form (17.09. or 17.09.2026),
or a Unix time.  Spelled numbers
from "two" upwards count as numbers ("one" is too ambiguous and is skipped).

Directions (audit B2).  A number that a direction word governs through "by" ("fell by 22.9", "made the book
cheaper, by between 3.4 and 37.4", "a narrowing by up to 39") must declare the direction of the word, ``~down`` or
``~up``, and a declared direction needs such a word; the phrase after "by" ends at a comma, a semicolon, a colon or
the end of the sentence.  Where the operations drop the sign (``~neg``, ``~abs``), the sign of the selected values
must agree with the direction as well: a negative change cannot rise.  In "falls from 11.86 to 10.76" and "rise from
rank 76 to 4" the printed numbers must move as the word says (a smaller rank is a rise).  So a changed verb fails
although every number still matches.

    python3 scripts/p2_number_check.py [--tex paper2/main.tex] [--results results/p2]
                                       [--report docs/paper2/NUMBER_CHECK.md] [--no-report] [--template]

``--template`` prints, unit by unit, every number in the order of the text with its present binding and, where it
has none, candidate sources to check by hand.  Exit status 1 if any error is found.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import json
import math
import re
import statistics
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

REPO = Path(__file__).resolve().parents[1]
TEX = Path("paper2/main.tex")
RESULTS = Path("results/p2")
REPORT = Path("docs/paper2/NUMBER_CHECK.md")
PREREG = "docs/paper2/PRAEREGISTRIERUNG.md"
PREREG_P1 = "docs/paper1/PRAEREGISTRIERUNG.md"

# ---------------------------------------------------------------------------------------------------------------
# Constants of the pre-registration (commit c9e9162; cc0a29f until 5 October 2026, 1d13227 until 27 September 2026)
# and its dated addenda:
# name -> (value, meaning, file, section).
# A value that means two things has two names.  Dates and clock times are ISO strings.  The section is named as in
# the English translations (docs/paper2/PREREGISTRATION.md, docs/paper1/PREREGISTRATION.md); SECTION_ORIGINAL gives
# the heading of the same section in the binding German original, verbatim.
# ---------------------------------------------------------------------------------------------------------------
CONSTANTS: Dict[str, Tuple[object, str, str, str]] = {
    "prereg_day": ("2026-09-24", "pre-registration fixed on 24 September 2026", PREREG, "Header"),
    "sample_start": ("2024-01-11 00:00", "start of the sample 11 January 2024 00:00 UTC", PREREG, "Sample"),
    "sample_end": ("2026-09-30 08:00", "preregistered end of the sample 30 September 2026 08:00 UTC", PREREG,
                   "Sample"),
    "pilot_cut": ("2026-09-17 12:00", "pilot cut 17 September 2026 12:00 UTC", PREREG, "Sample"),
    "pm2_window_btc_eth": ("2025-06-12 23:00", "PM2 window for BTC and ETH from 12 June 2025 23:00 UTC", PREREG,
                           "Sample"),
    "window_hype": ("2025-11-11 00:00", "SM and PM2 for HYPE from 11 November 2025 00:00 UTC", PREREG, "Sample"),
    "managers": (3, "three managers: SM, legacy PM, PM2", PREREG, "Sample"),
    "cash_zero": (0, "cash = 0 in K_p(q) = Σ p·q − net_IM(q; cash = 0)", PREREG,
                  "Semantics and capital"),
    "q_buy": (1, "q = +1 for a maker buy", PREREG, "Semantics and capital"),
    "q_sell": (-1, "q = −1 for a maker sell", PREREG, "Semantics and capital"),
    "markout_minutes": (30, "net edge after 30 minutes", PREREG, "Semantics and capital"),
    "cell_min_fills": (200, "cell populated from 200 fills", PREREG, "Semantics and capital"),
    "bp_factor": (10_000, "10⁴ in the cell quantities (basis points)", PREREG, "Semantics and capital"),
    "dominant_makers": (10, "the ten dominant maker subaccounts", PREREG, "Maker books"),
    "hypotheses": (4, "four hypotheses H1 to H4", PREREG, "Hypotheses and rejection rules"),
    "h1_threshold": (0.5, "H1 rejected if the upper bound is ≥ 0.5", PREREG, "Hypotheses and rejection rules"),
    "h2_threshold": (0.5, "H2: median of ΔK / K_PM2,Einzel smaller than 0.5", PREREG,
                     "Hypotheses and rejection rules"),
    "h3_threshold": (2, "H3: median of K_SM / K_PM2 greater than 2", PREREG, "Hypotheses and rejection rules"),
    "interval_pct": (90, "90 % interval", PREREG, "Hypotheses and rejection rules"),
    "h2_sample": (20_000, "simple random sample of 20 000 fills (H2)", PREREG,
                  "Hypotheses and rejection rules"),
    "seed": (20_260_924, "seed 20260924", PREREG, "Hypotheses and rejection rules"),
    "legacy_event_2024": ("2024-06-12", "legacy PM event 12 June 2024", PREREG, "Hypotheses and rejection rules"),
    "legacy_event_2025": ("2025-02-22", "legacy PM event 22 February 2025", PREREG, "Hypotheses and rejection rules"),
    "dose_filter_pct": (1, "events whose largest absolute dose is below 1 % are dropped", PREREG,
                        "Hypotheses and rejection rules"),
    "dose_window_days": (14, "dose window [e − 14 days, e)", PREREG, "Hypotheses and rejection rules"),
    "regression_window_days": (14, "regression window [e − 14 days, e + 14 days]", PREREG,
                               "Hypotheses and rejection rules"),
    "h4_min_fills_side": (20, "cells need at least 20 fills before and 20 after the event", PREREG,
                          "Hypotheses and rejection rules"),
    "h4_alpha": (0.05, "one-sided p ≤ 0.05", PREREG, "Hypotheses and rejection rules"),
    "placebo_dates": (100, "100 placebo dates", PREREG, "Hypotheses and rejection rules"),
    "placebo_percentile": (95, "β above the 95th percentile of the placebo β", PREREG,
                           "Hypotheses and rejection rules"),
    "placebo_gap_days": (28, "placebo dates at least 28 days from every event", PREREG,
                         "Hypotheses and rejection rules"),
    "bootstrap_draws": (9_999, "B = 9 999 bootstrap draws", PREREG, "Inference"),
    "api_discount_pct": (2, "API semantics with 2 % (exploratory)", PREREG, "Inference"),
    "validation_min_blocks": (48, "at least 48 random blocks per underlying and manager", PREREG,
                              "Validation before measurement"),
    "validation_min_maker_days": (20, "maker books on at least 20 maker days", PREREG,
                                  "Validation before measurement"),
    "validation_median_pct": (0.1, "median of the absolute relative deviation below 0.1 %", PREREG,
                              "Validation before measurement"),
    "validation_percentile": (95, "95th percentile of the absolute relative deviation", PREREG,
                              "Validation before measurement"),
    "validation_p95_pct": (1, "95th percentile below 1 %", PREREG, "Validation before measurement"),
    "addenda_day": ("2026-09-25", "Addenda 1 to 4, dated 25 September 2026", PREREG, "Addendum 1"),
    "interval_lower_percentile": (5, "interval from the 5th percentile of the replications", PREREG, "Addendum 3"),
    "interval_upper_percentile": (95, "to the 95th percentile of the replications", PREREG, "Addendum 3"),
    "addenda": (4, "four dated addenda", PREREG, "Addendum 4"),
    "addenda_total": (7, "seven dated addenda: 1 to 4 of 25 September, 5 of 27 September, 6 of 30 September and 7 "
                         "of 5 October 2026", PREREG, "Addendum 7"),
    "addendum5_day": ("2026-09-27", "Addendum 5, dated 27 September 2026 (history rewrite, after all results)",
                      PREREG, "Addendum 5"),
    "sm_max_options": (63, "63 options that an SM account on v2 can hold", PREREG, "Addendum 4"),
    "delta_edge_10": (10, "|Δ| bucket edge 10 %", PREREG_P1, "Cells and classes"),
    "delta_edge_25": (25, "|Δ| bucket edge 25 %", PREREG_P1, "Cells and classes"),
    "delta_edge_40": (40, "|Δ| bucket edge 40 %", PREREG_P1, "Cells and classes"),
    "delta_edge_60": (60, "|Δ| bucket edge 60 %", PREREG_P1, "Cells and classes"),
    "delta_edge_60_delta": (0.6, "|Δ| bucket edge 60 % as delta 0.6", PREREG_P1, "Cells and classes"),
    "delta_edge_75": (75, "|Δ| bucket edge 75 %", PREREG_P1, "Cells and classes"),
    "delta_edge_90": (90, "|Δ| bucket edge 90 %", PREREG_P1, "Cells and classes"),
    "tenor_edge_2d": (2, "tenor bucket edge 2 days", PREREG_P1, "Cells and classes"),
    "tenor_edge_7d": (7, "tenor bucket edge 7 days", PREREG_P1, "Cells and classes"),
    "tenor_edge_30d": (30, "tenor bucket edge 30 days", PREREG_P1, "Cells and classes"),
    "tenor_edge_90d": (90, "tenor bucket edge 90 days", PREREG_P1, "Cells and classes"),
}
# The heading of each section in the binding German original, quoted verbatim ("Header" is the text before the
# first section and has no heading).
SECTION_ORIGINAL: Dict[str, str] = {
    "Sample": "Stichprobe", "Semantics and capital": "Semantik und Kapital", "Maker books": "Maker-Bücher",
    "Hypotheses and rejection rules": "Hypothesen und Ablehnungsregeln", "Inference": "Inferenz",
    "Validation before measurement": "Validierung vor der Messung", "Addendum 1": "Nachtrag 1",
    "Addendum 3": "Nachtrag 3", "Addendum 4": "Nachtrag 4", "Addendum 5": "Nachtrag 5", "Addendum 6": "Nachtrag 6", "Addendum 7": "Nachtrag 7",
    "Cells and classes": "Zellen und Klassen"}
# Arithmetic identities used to read a result; they are not results.
IDENTITIES: Dict[str, Tuple[float, str]] = {
    "ln_0_9": (math.log(0.9), "ln 0.9: the dose when capital becomes ten per cent cheaper (reading aid for β, "
                              "Figure F6)"),
}

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]
MONTH_ABBR = {m[:3]: i + 1 for i, m in enumerate(MONTHS)}
WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
         "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
         "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100}
UNITS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}

ELEMENTWISE: Dict[str, Callable[[float], float]] = {"pct": lambda v: v * 100.0, "bp": lambda v: v * 1e4,
                                                    "neg": lambda v: -v, "abs": abs}
AGGREGATES: Dict[str, Callable[[List[float]], float]] = {
    "min": min, "max": max, "median": statistics.median, "mean": statistics.fmean, "sum": math.fsum, "count": len}
DIRECTIONS = ("up", "down")
DIRECTION_WORDS: Dict[str, str] = {w: "down" for w in (
    "fell", "fall", "falls", "falling", "cut", "cuts", "lower", "lowered", "lowers", "cheaper", "narrowed", "narrows",
    "narrowing", "decrease", "decreased", "decreases", "drop", "dropped", "drops", "reduce", "reduced", "reduces",
    "shrank", "shrinks")}
DIRECTION_WORDS.update({w: "up" for w in (
    "rose", "rise", "rises", "rising", "raise", "raised", "raises", "higher", "dearer", "widened", "widens",
    "widening", "increase", "increased", "increases", "grew", "grows")})


# ---------------------------------------------------------------------------------------------------------------
# Dates and clock times inside a value
# ---------------------------------------------------------------------------------------------------------------
ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?")
COMPACT = re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)")
DOTTED = re.compile(r"(?<![\d.])(\d{1,2})\.(\d{1,2})\.(\d{4})?")
WORDDATE = re.compile(r"(?<!\d)(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?\s+(\d{4})")
CLOCK = re.compile(r"(?<![\d:])(\d{2}):(\d{2})(?::\d{2})?")


def _valid(y: int, m: int, d: int) -> bool:
    try:
        dt.date(y, m, d)
    except ValueError:
        return False
    return 2000 <= y <= 2100


def moments(value) -> Tuple[Set[str], Set[str]]:
    """Dates ('YYYY-MM-DD', or '--MM-DD' for a day without year) and clock times ('HH:MM') in one value."""
    dates: Set[str] = set()
    times: Set[str] = set()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        v = float(value)
        for scale in (1.0, 1e3):
            if 1.4e9 <= v / scale <= 2.2e9:
                t = dt.datetime.fromtimestamp(v / scale, tz=dt.timezone.utc)
                dates.add(t.strftime("%Y-%m-%d"))
                times.add(t.strftime("%H:%M"))
        return dates, times
    if not isinstance(value, str):
        return dates, times
    text = value
    for m in ISO.finditer(text):
        if _valid(int(m.group(1)), int(m.group(2)), int(m.group(3))):
            dates.add("{}-{}-{}".format(m.group(1), m.group(2), m.group(3)))
            if m.group(4):
                times.add("{}:{}".format(m.group(4), m.group(5)))
    text = ISO.sub(" ", text)
    for m in COMPACT.finditer(text):
        if _valid(int(m.group(1)), int(m.group(2)), int(m.group(3))):
            dates.add("{}-{}-{}".format(m.group(1), m.group(2), m.group(3)))
    for m in WORDDATE.finditer(text):
        mo = MONTH_ABBR.get(m.group(2).lower())
        if mo and _valid(int(m.group(3)), mo, int(m.group(1))):
            dates.add("{:04d}-{:02d}-{:02d}".format(int(m.group(3)), mo, int(m.group(1))))
    for m in DOTTED.finditer(text):
        d, mo = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            y = int(m.group(3)) if m.group(3) else None
            dates.add("{:04d}-{:02d}-{:02d}".format(y, mo, d) if y and _valid(y, mo, d) else
                      "--{:02d}-{:02d}".format(mo, d))
    for m in CLOCK.finditer(text):
        if int(m.group(1)) < 24 and int(m.group(2)) < 60:
            times.add("{}:{}".format(m.group(1), m.group(2)))
    return dates, times


def _at_granularity(dates: Set[str], kind: str) -> Set[str]:
    """The dates of a value at the granularity of a printed date: full, month or day of a month."""
    if kind == "date":
        return {d for d in dates if not d.startswith("--")}
    if kind == "month":
        return {d[:7] for d in dates if not d.startswith("--")}
    return {"--" + d[-5:] for d in dates}


# ---------------------------------------------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------------------------------------------
def default_git_date(repo: Path = REPO) -> Callable[[str], Optional[str]]:
    def when(sha: str) -> Optional[str]:
        run = subprocess.run(["git", "-C", str(repo), "show", "-s", "--format=%ai", sha],
                             capture_output=True, text=True)
        return (run.stdout.strip() or None) if run.returncode == 0 else None
    return when


def default_commit_resolver(repo: Path = REPO) -> Callable[[str], bool]:
    def resolve(sha: str) -> bool:
        run = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", sha + "^{commit}"],
                             capture_output=True, text=True)
        return run.returncode == 0
    return resolve


def _number(x) -> Optional[float]:
    if isinstance(x, bool) or x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x) if math.isfinite(float(x)) else None
    try:
        v = float(str(x))
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def _flatten(obj, path: str, out: Dict[str, object]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            _flatten(v, "{}.{}".format(path, k) if path else str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _flatten(v, "{}.{}".format(path, i) if path else str(i), out)
    else:
        out[path] = obj


FILTER_TERM = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(!=|<=|>=|=|<|>)(.*)$")


def _compare(cell: str, op: str, want: str) -> bool:
    a, b = _number(cell), _number(want)
    if op in ("=", "!="):
        same = (a == b) if a is not None and b is not None else cell == want
        return same if op == "=" else not same
    if a is None or b is None:
        return False
    return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]


@dataclass
class Spec:
    raw: str
    file: str
    key: str
    ops: List[str]


def parse_spec(raw: str) -> Tuple[Optional[Spec], str]:
    head, *ops = raw.split("~")
    file, sep, key = head.partition(":")
    if not sep or not file or not key:
        return None, "source without file:key"
    unknown = [o for o in ops if o not in ELEMENTWISE and o not in AGGREGATES and o not in ("all", "distinct")
               and o not in DIRECTIONS]
    if unknown:
        return None, "unknown operation ~" + ", ~".join(unknown)
    if sum(o in DIRECTIONS for o in ops) > 1:
        return None, "one direction, ~up or ~down"
    if ops.count("all") > 1 or ("all" in ops and ops[-1] != "all"):
        return None, "~all stands once and at the end"
    return Spec(raw, file, key, ops), ""


class Sources:
    """The files under a results directory, read when a declaration names them."""

    def __init__(self, results: Path, git_date: Optional[Callable[[str], Optional[str]]] = None):
        self.results = Path(results)
        self.git_date = git_date or default_git_date()
        self._json: Dict[str, Dict[str, object]] = {}
        self._csv: Dict[str, Tuple[List[str], List[List[str]]]] = {}
        self._derived: Optional[Dict[str, float]] = None

    def flat(self, rel: str) -> Dict[str, object]:
        if rel not in self._json:
            path = self.results / rel
            out: Dict[str, object] = {}
            if rel.endswith(".jsonl"):
                for n, line in enumerate(path.read_text().splitlines(), 1):
                    if line.strip():
                        _flatten(json.loads(line), str(n), out)
            else:
                _flatten(json.loads(path.read_text()), "", out)
            self._json[rel] = out
        return self._json[rel]

    def table(self, rel: str) -> Tuple[List[str], List[List[str]]]:
        if rel not in self._csv:
            with (self.results / rel).open(newline="") as fh:
                reader = csv.reader(fh)
                header = next(reader, [])
                self._csv[rel] = (header, [row for row in reader])
        return self._csv[rel]

    def derived(self) -> Dict[str, float]:
        if self._derived is None:
            out: Dict[str, float] = {}
            flags = []
            for name in ("h1.json", "h2.json", "h3.json", "h4.json"):
                path = self.results / name
                if path.is_file():
                    flags.append(json.loads(path.read_text()).get("rejected"))
            if flags and all(isinstance(f, bool) for f in flags):
                out["n_rejected"] = float(sum(flags))
                out["n_not_rejected"] = float(len(flags) - sum(flags))
                out["n_hypotheses"] = float(len(flags))
            cells = self.results / "h1_cells.csv"
            if cells.is_file():
                with cells.open(newline="") as fh:
                    rows = list(csv.DictReader(fh))
                out["h1_cells_pos"] = float(sum(1 for r in rows if r.get("occupied") == "True"
                                                and (_number(r.get("A_bp")) or 0.0) > 0))
            self._derived = out
        return self._derived

    def select(self, spec: Spec) -> Tuple[List[object], str]:
        """The raw values a source names, before the operations; an error text instead if it names none."""
        f, key = spec.file, spec.key
        if f == "derived":
            d = self.derived()
            return ([d[key]], "") if key in d else ([], "derived:{} unknown".format(key))
        if f == "const":
            if key not in CONSTANTS:
                return [], "constant {} not in the list".format(key)
            return [CONSTANTS[key][0]], ""
        if f == "ident":
            return ([IDENTITIES[key][0]], "") if key in IDENTITIES else ([], "identity {} unknown".format(key))
        if f == "git":
            stamp = self.git_date(key)
            return ([stamp], "") if stamp else ([], "commit {} unknown".format(key))
        if f == "text":
            return [], "text: binds no value"
        path = self.results / f
        if not path.is_file():
            return [], "file {} missing".format(f)
        if f.endswith(".csv"):
            return self._select_csv(f, key)
        if not f.endswith((".json", ".jsonl")):
            return [], "only JSON and CSV files"
        flat = self.flat(f)
        if "," in key:
            missing = [k for k in key.split(",") if k not in flat]
            if missing:
                return [], "key missing: " + ", ".join(missing)
            return [flat[k] for k in key.split(",")], ""
        if any(c in key for c in "*?["):
            hits = [v for k, v in flat.items() if fnmatch.fnmatchcase(k, key)]
            return (hits, "") if hits else ([], "pattern {} matches no key".format(key))
        return ([flat[key]], "") if key in flat else ([], "key {} missing".format(key))

    def _select_csv(self, f: str, key: str) -> Tuple[List[object], str]:
        header, rows = self.table(f)
        col, at, filt = key.partition("@")
        if col not in header:
            return [], "column {} missing in {}".format(col, f)
        terms = [FILTER_TERM.match(t) for t in filt.split(",")] if at else []
        if at and all(m and m.group(1) in header for m in terms):
            conds = [(header.index(m.group(1)), m.group(2), m.group(3)) for m in terms]
            chosen = [r for r in rows if all(i < len(r) and _compare(r[i], op, want) for i, op, want in conds)]
        elif at:
            chosen = [r for r in rows if r and r[0] == filt]
        else:
            chosen = rows
        i = header.index(col)
        values = [r[i] for r in chosen if i < len(r) and r[i] != ""]
        if not values:
            return [], "filter {} matches no row with a value".format(filt or "(none)")
        return [(_number(v) if _number(v) is not None else v) for v in values], ""

    def resolve(self, raw: str) -> Tuple[List[object], bool, str]:
        """(values after the operations, every value must match, error)."""
        spec, err = parse_spec(raw)
        if spec is None:
            return [], False, err
        if spec.file == "text":
            return [], False, ""
        values, err = self.select(spec)
        if err:
            return [], False, err
        every = False
        for op in spec.ops:
            if op == "all":
                every = True
                continue
            if op in DIRECTIONS:                # binds the verb of the sentence, not the value
                continue
            if op == "count":                   # counts rows or keys, whatever they hold
                values = [float(len(values))]
                continue
            if op == "distinct":                # counts the distinct values of the selection
                values = [float(len({(_number(v) if _number(v) is not None else v) for v in values}))]
                continue
            nums = [_number(v) for v in values]
            if any(n is None for n in nums):
                return [], False, "~{} on a value that is not a number".format(op)
            if op in ELEMENTWISE:
                values = [ELEMENTWISE[op](n) for n in nums]
            else:
                values = [float(AGGREGATES[op](nums))]
        if not every:
            distinct = {(_number(v) if _number(v) is not None else v) for v in values}
            if len(distinct) != 1:
                return [], False, "selection not unique ({} distinct values); add a filter, an aggregate or " \
                                  "~all".format(len(distinct))
            values = values[:1]
        return values, every, ""


# ---------------------------------------------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------------------------------------------
FIGURE = re.compile(r"\\begin\{(figure\*?)\}(.*?)\\end\{\1\}", re.S)
DISPLAY = re.compile(r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}.*?\\end\{\1\}|\\\[.*?\\\]", re.S)
DECLARATION = re.compile(r"^[ \t]*%+[ \t]*src[ \t]+(\S+)[ \t]+(.+?)[ \t]*$", re.M)
HEADING = re.compile(r"\\(section|subsection)\*?\s*\{")
BODY_END = re.compile(r"\\bibliographystyle|\\bibliography\{|\\end\{document\}")


def _balanced(text: str, start: int) -> Tuple[str, int]:
    """Content of the brace group opening at ``text[start] == '{'`` and the index after it."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
    return text[start + 1:], len(text)


def captions(block: str) -> List[str]:
    out = []
    for m in re.finditer(r"\\caption\s*(\[[^\]]*\])?\s*\{", block):
        content, _ = _balanced(block, m.end() - 1)
        out.append(content)
    return out


def mask_comments(tex: str) -> str:
    """The text with every comment blanked out, so that offsets stay those of the original."""
    return re.sub(r"(?<!\\)%.*", lambda m: " " * len(m.group(0)), tex)


@dataclass
class Token:
    kind: str                 # number, date, month, dayonly, time, commit
    raw: str
    value: float = float("nan")
    decimals: int = 0
    exponent: int = 0
    signed: bool = False
    iso: str = ""
    spelled: bool = False
    pos: int = -1
    rel: str = ""             # relation of a printed number in a declaration: > >= < <=

    def key(self) -> tuple:
        """What binds a printed number to a declaration: its printed form ("four" and "Four" alike)."""
        if self.kind == "number":
            return ("number", round(self.value, 12), self.decimals, self.exponent, self.spelled, self.signed)
        return (self.kind, self.iso if self.kind != "commit" else self.raw)


@dataclass
class Decl:
    line: int
    spec: str
    printed: str
    tokens: List[Token]


@dataclass
class Unit:
    where: str
    text: str
    decls: List[Decl] = field(default_factory=list)


REMOVE_ARG = re.compile(r"\\(label|ref|eqref|pageref|cite[a-z]*|includegraphics|url|bibliography[a-z]*|input|"
                        r"href)\s*(\[[^\]]*\])?\{[^}]*\}")
TEXTTT = re.compile(r"\\texttt\{([^{}]*)\}")
SCI = re.compile(r"(\d+(?:\.\d+)?)\s*\\times\s*10\^\{?\s*([-+]?\d+)\s*\}?")
POW10 = re.compile(r"(?<![\d.])10\^\{?\s*([-+]?\d+)\s*\}?")
THOUSANDS = re.compile(r"(?<=\d)\\,(?=\d{3}(?!\d))")
IDENT = re.compile(r"(?<![A-Za-z0-9])(?:UTC[+-]\d+|Addend(?:um|a)\s+\d+(?:\s*(?:,|and|to)\s*\d+)*|"
                   r"[A-Za-z]+\d+[A-Za-z0-9]*)")
MONTH_RE = "|".join(m.capitalize() for m in MONTHS)
DATE_FULL = re.compile(r"(?<![\d.])(\d{1,2})\s+(" + MONTH_RE + r")\s+(\d{4})(?!\d)")
DATE_DM = re.compile(r"(?<![\d.])(\d{1,2})\s+(" + MONTH_RE + r")(?![A-Za-z])")
DATE_MY = re.compile(r"(?<![A-Za-z])(" + MONTH_RE + r")\s+(\d{4})(?!\d)")
TIME = re.compile(r"(?<![\d.:])(\d{1,2}):(\d{2})(?![\d:])")
NUM = re.compile(r"(?<![A-Za-z0-9_.])(?P<sign>[-+]?)(?P<num>\d+(?:\.\d+)?)(?:e(?P<exp>[-+]?\d+))?"
                 r"(?P<ord>st|nd|rd|th)?(?![A-Za-z0-9_])")
WORD_RE = re.compile(r"(?<![A-Za-z-])(" + "|".join(sorted(WORDS, key=len, reverse=True)) + r")(?:-(" +
                     "|".join(UNITS) + r"))?(?![A-Za-z])", re.I)
RELATION = re.compile(r"(>=|<=|>|<)\s*$")
_DIR_WORDS = "|".join(sorted(DIRECTION_WORDS, key=len, reverse=True))
DIRECTION_WORD = re.compile(r"(?<![A-Za-z-])(" + _DIR_WORDS + r")(?![A-Za-z-])", re.I)
BY = re.compile(r"(?<![A-Za-z])by(?![A-Za-z])")
PHRASE_END = re.compile(r"[,;:]|\.(?=\s|$)")
FROM_TO = re.compile(r"(?<![A-Za-z-])(" + _DIR_WORDS + r")\s+from\s+(rank\s+)?([-+]?\d+(?:\.\d+)?)\s+to\s+"
                     r"(?:rank\s+)?([-+]?\d+(?:\.\d+)?)(?![\d.]\d)", re.I)


def clean(text: str) -> Tuple[str, List[Token]]:
    """Plain text with LaTeX removed, plus the commit hashes found in ``\\texttt``."""
    commits: List[Token] = []
    text = REMOVE_ARG.sub(" ", text)
    for m in TEXTTT.finditer(text):
        for word in re.split(r"[\s,;]+", m.group(1)):
            if re.fullmatch(r"[0-9a-f]{7,40}", word):
                commits.append(Token("commit", word))
    text = TEXTTT.sub(" ", text)
    text = THOUSANDS.sub("", text)
    text = SCI.sub(lambda m: "{}e{}".format(m.group(1), m.group(2)), text)
    text = POW10.sub(lambda m: "1e{}".format(m.group(1)), text)
    text = text.replace("~", " ").replace("\\,", " ").replace("\\ ", " ")
    text = text.replace("\\%", " per cent ").replace("%", " per cent ").replace("$", " ")
    text = re.sub(r"\\[A-Za-z]+\*?", " ", text)
    text = re.sub(r"[{}]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return IDENT.sub(" ", text), commits


def scan(text: str, relations: bool = False) -> Tuple[str, List[Token]]:
    """The plain text and its numbers, dates, clock times (in the order of the text) and commit hashes.

    With ``relations`` (the printed part of a declaration) a ``>``, ``>=``, ``<`` or ``<=`` just before a number
    becomes its relation.
    """
    text, commits = clean(text)
    plain = text
    found: List[Token] = []

    def take(pattern, make):
        nonlocal text
        for m in pattern.finditer(text):
            tok = make(m)
            tok.pos = m.start()
            found.append(tok)
        text = pattern.sub(lambda m: ";" * len(m.group(0)), text)

    take(DATE_FULL, lambda m: Token("date", m.group(0), iso="{:04d}-{:02d}-{:02d}".format(
        int(m.group(3)), MONTHS.index(m.group(2).lower()) + 1, int(m.group(1)))))
    take(DATE_MY, lambda m: Token("month", m.group(0), iso="{:04d}-{:02d}".format(
        int(m.group(2)), MONTHS.index(m.group(1).lower()) + 1)))
    take(DATE_DM, lambda m: Token("dayonly", m.group(0), iso="--{:02d}-{:02d}".format(
        MONTHS.index(m.group(2).lower()) + 1, int(m.group(1)))))
    take(TIME, lambda m: Token("time", m.group(0), iso="{:02d}:{}".format(int(m.group(1)), m.group(2))))
    for m in NUM.finditer(text):
        num = m.group("num")
        decimals = len(num.split(".")[1]) if "." in num else 0
        exp = int(m.group("exp")) if m.group("exp") else 0
        value = float(num) * 10 ** exp
        if m.group("sign") == "-":
            value = -value
        found.append(Token("number", m.group(0).strip(), value=value, decimals=decimals, exponent=exp,
                           signed=bool(m.group("sign")), pos=m.start()))
    for m in WORD_RE.finditer(text):
        value = WORDS[m.group(1).lower()] + (UNITS[m.group(2).lower()] if m.group(2) else 0)
        found.append(Token("number", m.group(0), value=float(value), spelled=True, pos=m.start()))
    found.sort(key=lambda t: t.pos)
    for tok in found if relations else []:
        rel = RELATION.search(plain[:tok.pos])
        tok.rel = rel.group(1) if rel else ""
    return plain, found + commits


def tokens(text: str) -> List[Token]:
    """Numbers, dates and clock times of one piece of LaTeX prose in the order of the text, then commit hashes."""
    return scan(text)[1]


def _line_of(tex: str, offset: int) -> int:
    return tex.count("\n", 0, offset) + 1


def structure(tex: str) -> Tuple[List[Unit], List[Decl]]:
    """The checked units with their declarations, and the declarations that stand in no unit."""
    masked = mask_comments(tex)
    begin = masked.find("\\begin{document}")
    end_m = BODY_END.search(masked, max(begin, 0))
    body_end = end_m.start() if end_m else len(masked)
    spans: List[Tuple[int, int, Unit]] = []      # (start, end, unit) for declarations
    out: List[Unit] = []
    ab = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", masked, re.S)
    if ab:
        unit = Unit("abstract", ab.group(1))
        out.append(unit)
        spans.append((ab.start(1), ab.end(1), unit))
    heads = []
    for m in HEADING.finditer(masked, 0, body_end):
        if m.start() < max(begin, 0):
            continue
        title, after = _balanced(masked, m.end() - 1)
        heads.append((m.start(), after, m.group(1), title))
    section = ""
    for n, (start, after, level, title) in enumerate(heads):
        stop = heads[n + 1][0] if n + 1 < len(heads) else body_end
        if level == "section":
            section, where, prefix = title, title, ""
        else:
            where, prefix = "{} / {}".format(section, title), title + "\n"
        content = masked[after:stop]
        for fig in FIGURE.finditer(content):
            label = re.search(r"\\label\{([^}]*)\}", fig.group(2))
            caps = captions(fig.group(2))
            name = "caption " + (label.group(1) if label else "?")
            for k, cap in enumerate(caps):
                unit = Unit(name, cap)
                out.append(unit)
                if k == 0:
                    spans.append((after + fig.start(), after + fig.end(), unit))
        prose = DISPLAY.sub(" ", FIGURE.sub(lambda f: " " * len(f.group(0)), content))
        unit = Unit(where, prefix + prose)
        out.append(unit)
        spans.append((after, stop, unit))
    stray: List[Decl] = []
    for m in DECLARATION.finditer(tex):
        _, toks = scan(m.group(2), relations=True)
        decl = Decl(_line_of(tex, m.start()), m.group(1), m.group(2), [t for t in toks if t.kind != "commit"])
        # the innermost span holds it: a figure inside a section comes after the section in ``spans``
        owners = [u for s, e, u in spans if s <= m.start() < e]
        figure_owner = [u for u in owners if u.where.startswith("caption ")]
        owner = figure_owner[0] if figure_owner else (owners[0] if owners else None)
        if owner is None:
            stray.append(decl)
        else:
            owner.decls.append(decl)
    return out, stray


def units(tex: str) -> List[Unit]:
    return structure(tex)[0]


# ---------------------------------------------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------------------------------------------
@dataclass
class Verdict:
    unit: str
    token: Token
    ok: bool
    how: str          # result, constant, identity, git, text, commit | none, mismatch, decl (errors)
    source: str
    detail: str = ""
    line: int = 0     # line of the declaration in the manuscript
    context: str = ""


HOW_OF = {"const": "constant", "ident": "identity", "git": "git", "text": "text"}


def _tolerance(tok: Token) -> float:
    return 0.5 * 10.0 ** (tok.exponent - tok.decimals)


def _fits_number(tok: Token, v: float) -> bool:
    x = tok.value
    if tok.rel:
        return {">": v > x, ">=": v >= x, "<": v < x, "<=": v <= x}[tok.rel]
    return abs(v - x) <= _tolerance(tok) + 1e-9 * max(1.0, abs(x))


def _fits_moment(tok: Token, value) -> Tuple[bool, str]:
    dates, times = moments(value)
    if tok.kind == "time":
        if len(times) != 1:
            return False, "value holds {} clock times".format(len(times))
        return tok.iso in times, next(iter(times))
    found = _at_granularity(dates, tok.kind)
    if len(found) != 1:
        return False, "value holds {} dates".format(len(found))
    return tok.iso in found, next(iter(found))


def evaluate(printed: Token, spec: str, sources: Sources) -> Tuple[bool, str, str]:
    """(ok, how, detail) of one printed number against its declared source."""
    file = spec.split(":", 1)[0]
    how = HOW_OF.get(file, "result")
    if file == "text":
        label = spec.partition(":")[2]
        whole = printed.kind == "number" and printed.decimals == 0 and printed.exponent == 0 and not printed.rel
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", label) or "~" in spec:
            return False, "mismatch", "text: needs a label of letters, digits and _"
        if not whole or printed.value < 0:
            return False, "mismatch", "text: only for whole, non-negative numbers"
        return True, how, "count word from the sentence"
    if file == "const" and "~" not in spec and spec.split(":", 1)[1] in CONSTANTS:
        value, what, path, section = CONSTANTS[spec.split(":", 1)[1]]
        if printed.kind == "number" and not isinstance(value, str) and not printed.rel:
            ok = abs(float(value) - printed.value) <= 1e-9 * max(1.0, abs(printed.value))
            return ok, "constant" if ok else "mismatch", "{} ({}, {})".format(what, path, section)
    values, every, err = sources.resolve(spec)
    if err:
        return False, "mismatch", err
    shown = []
    for value in values:
        if printed.kind == "number":
            v = _number(value)
            if v is None:
                return False, "mismatch", "value {!r} is not a number".format(value)
            if not _fits_number(printed, v):
                return False, "mismatch", "value {:.6g} does not match {}{}".format(v, printed.rel, printed.raw)
            shown.append("{:.6g}".format(v))
        else:
            ok, got = _fits_moment(printed, value)
            if not ok:
                return False, "mismatch", "date or clock time {} does not match {}".format(got, printed.raw)
            shown.append(got)
    if file == "const":
        key = spec.split(":", 1)[1].split("~")[0]
        return True, how, "{} ({}, {})".format(CONSTANTS[key][1], CONSTANTS[key][2], CONSTANTS[key][3])
    if file == "ident":
        key = spec.split(":", 1)[1].split("~")[0]
        return True, how, "{:.6g}: {}".format(IDENTITIES[key][0], IDENTITIES[key][1])
    detail = ("all: " if every else "= ") + ", ".join(shown[:4]) + (" …" if len(shown) > 4 else "")
    return True, how, detail


def _align(a: Sequence[tuple], b: Sequence[tuple]) -> List[Tuple[int, int]]:
    """Index pairs of a longest common subsequence of ``a`` (declared) and ``b`` (printed), earliest first."""
    n, m = len(a), len(b)
    table = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            table[i][j] = table[i + 1][j + 1] + 1 if a[i] == b[j] else max(table[i + 1][j], table[i][j + 1])
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        if a[i] == b[j]:
            pairs.append((i, j))
            i, j = i + 1, j + 1
        elif table[i + 1][j] >= table[i][j + 1]:
            i += 1
        else:
            j += 1
    return pairs


def _context(plain: str, tok: Token, width: int = 38) -> str:
    if tok.pos < 0:
        return ""
    return plain[max(0, tok.pos - width):tok.pos + len(tok.raw) + width].strip()


def governing_direction(plain: str, pos: int, reach: int = 100) -> Tuple[str, str]:
    """(direction, word) of the direction word that governs the number at ``pos`` through "by", else ("", "")."""
    head = plain[:pos]
    by = None
    for by in BY.finditer(head):
        pass
    if by is None:
        return "", ""
    mid = head[by.end():]
    if len(mid) > reach or PHRASE_END.search(mid) or DIRECTION_WORD.search(mid):
        return "", ""
    before = head[max(0, by.start() - reach):by.start()]
    ends = [m.end() for m in re.finditer(r"[;:]|\.(?=\s)", before)]
    before = before[ends[-1]:] if ends else before
    words = list(DIRECTION_WORD.finditer(before))
    if not words:
        return "", ""
    word = words[-1].group(1)
    return DIRECTION_WORDS[word.lower()], word


def direction_error(plain: str, tok: Token, spec: str, sources: Sources) -> str:
    """Why the direction word of the sentence and the declaration of the number disagree ("" if they agree)."""
    ops = spec.split("~")[1:]
    declared = next((o for o in ops if o in DIRECTIONS), "")
    direction, word = governing_direction(plain, tok.pos)
    if direction and not declared:
        return "'{}' governs this number through 'by': declare ~{}".format(word, direction)
    if declared and not direction:
        return "declared ~{}, but no direction word governs this number through 'by'".format(declared)
    if declared != direction:
        return "'{}' says {}, the declaration ~{}".format(word, direction, declared)
    if direction and ("neg" in ops or "abs" in ops):
        parsed, _ = parse_spec(spec)
        raw, err = sources.select(parsed) if parsed else ([], "")
        nums = [_number(v) for v in raw] if not err else []
        signs = {n > 0 for n in nums if n is not None and n != 0}
        if len(signs) == 1 and ("up" if signs.pop() else "down") != direction:
            return "'{}' says {}, but the selected change is {}".format(
                word, direction, "negative" if direction == "up" else "positive")
    return ""


def from_to_errors(plain: str) -> Dict[int, str]:
    """Position of the second number -> error, for every "<word> from X to Y" whose numbers move against the word
    (with "rank" a smaller number is a rise)."""
    out: Dict[int, str] = {}
    for m in FROM_TO.finditer(plain):
        direction = DIRECTION_WORDS[m.group(1).lower()]
        x, y = float(m.group(3)), float(m.group(4))
        up = y < x if m.group(2) else y > x
        if x != y and up != (direction == "up"):
            out[m.start(4)] = "'{}' says {}, but the text goes from {}{} to {}".format(
                m.group(1), direction, "rank " if m.group(2) else "", m.group(3), m.group(4))
    return out


def check_unit(unit: Unit, sources: Sources, resolve_commit: Callable[[str], bool]) -> List[Verdict]:
    plain, toks = scan(unit.text)
    printed = [t for t in toks if t.kind != "commit"]
    commits = [t for t in toks if t.kind == "commit"]
    flat = [(d, p) for d in unit.decls for p in d.tokens]
    pairs = dict((j, i) for i, j in _align([p.key() for _, p in flat], [t.key() for t in printed]))
    moves = from_to_errors(plain)
    out: List[Verdict] = []
    for j, tok in enumerate(printed):
        ctx = _context(plain, tok)
        if j not in pairs:
            out.append(Verdict(unit.where, tok, False, "none", "", "not declared", 0, ctx))
            continue
        decl, p = flat[pairs[j]]
        ok, how, detail = evaluate(p, decl.spec, sources)
        if ok and tok.kind == "number" and not decl.spec.startswith("text:"):
            err = direction_error(plain, tok, decl.spec, sources) or moves.get(tok.pos, "")
            if err:
                ok, how, detail = False, "mismatch", err
        out.append(Verdict(unit.where, tok, ok, how, decl.spec, detail, decl.line, ctx))
    used = set(pairs.values())
    for i, (decl, p) in enumerate(flat):
        if i not in used:
            out.append(Verdict(unit.where, p, False, "decl", decl.spec,
                               "declaration binds no occurrence: number not (or no longer) in the text or not in "
                               "the order of the text", decl.line))
    for d in unit.decls:
        if not d.tokens:
            out.append(Verdict(unit.where, Token("number", d.printed), False, "decl", d.spec,
                               "declaration without a printed number", d.line))
    for tok in commits:
        ok = resolve_commit(tok.raw)
        out.append(Verdict(unit.where, tok, ok, "commit" if ok else "none", "git: commit present" if ok else "",
                           "" if ok else "commit unknown"))
    return out


def check(tex: str, results: Path = RESULTS, resolve_commit: Optional[Callable[[str], bool]] = None,
          git_date: Optional[Callable[[str], Optional[str]]] = None,
          sources: Optional[Sources] = None) -> List[Verdict]:
    """All verdicts for a manuscript, unit by unit, then the declarations that stand in no unit."""
    resolve_commit = resolve_commit or default_commit_resolver()
    sources = sources or Sources(Path(results), git_date)
    us, stray = structure(tex)
    out: List[Verdict] = []
    for u in us:
        out += check_unit(u, sources, resolve_commit)
    for d in stray:
        for p in d.tokens or [Token("number", d.printed)]:
            out.append(Verdict("front matter", p, False, "decl", d.spec,
                               "declaration outside a checked unit (abstract, section, figure)",
                               d.line))
    return out


def unused_declarations(verdicts: Sequence[Verdict]) -> List[Tuple[str, str]]:
    """(source, printed number) of every declaration that binds no occurrence or stands in no unit."""
    return [(v.source, v.token.raw) for v in verdicts if v.how == "decl"]


# ---------------------------------------------------------------------------------------------------------------
# Template: every number in order, with its binding or candidates to check by hand
# ---------------------------------------------------------------------------------------------------------------
TRIALS = [[], ["pct"], ["neg"], ["neg", "pct"], ["bp"]]


def candidates(tok: Token, sources: Sources, limit: int = 4) -> List[str]:
    """Sources in summary.json and CONSTANTS that would print as ``tok``; a hint, never a binding."""
    out: List[str] = []
    if tok.kind == "number":
        for name, (value, _, _, _) in CONSTANTS.items():
            if not isinstance(value, str) and abs(float(value) - tok.value) <= 1e-9 * max(1.0, abs(tok.value)):
                out.append("const:" + name)
    else:
        for name, (value, _, _, _) in CONSTANTS.items():
            if isinstance(value, str) and _fits_moment(tok, value)[0]:
                out.append("const:" + name)
    try:
        flat = sources.flat("summary.json")
    except (OSError, ValueError):
        flat = {}
    for key, value in flat.items():
        if len(out) >= limit + 3:
            break
        if tok.kind == "number":
            v = _number(value)
            if v is None:
                continue
            for ops in TRIALS:
                w = v
                for op in ops:
                    w = ELEMENTWISE[op](w)
                if _fits_number(tok, w):
                    out.append("summary.json:" + key + "".join("~" + o for o in ops))
                    break
        elif isinstance(value, str) and _fits_moment(tok, value)[0]:
            out.append("summary.json:" + key)
    return out[:limit + 3]


def template(tex: str, results: Path = RESULTS, resolve_commit: Optional[Callable[[str], bool]] = None,
             git_date: Optional[Callable[[str], Optional[str]]] = None) -> str:
    resolve_commit = resolve_commit or default_commit_resolver()
    sources = Sources(Path(results), git_date)
    us, stray = structure(tex)
    old: Dict[tuple, List[str]] = {}
    for d in [d for u in us for d in u.decls] + stray:
        for p in d.tokens:
            old.setdefault(p.key(), [])
            if d.spec not in old[p.key()]:
                old[p.key()].append(d.spec)
    lines = ["Template of the declarations: per unit every number in the order of the text. Lines with ??? are "
             "open; the suggestions are equalities of value and must be checked for meaning.", ""]
    for u in us:
        vs = [v for v in check_unit(u, sources, resolve_commit) if v.token.kind != "commit"]
        if not vs:
            continue
        open_n = sum(1 for v in vs if not v.ok)
        lines.append("## {}  ({} numbers, {} open)".format(u.where, sum(1 for v in vs if v.how != "decl"), open_n))
        for v in vs:
            printed = (v.token.rel or "") + v.token.raw
            if v.how == "decl":
                lines.append("%   remove: % src {} {}   [{}]".format(v.source, printed, v.detail))
            elif v.ok:
                lines.append("% src {} {}".format(v.source, printed))
            else:
                hint = [s for s in old.get(v.token.key(), []) if s != v.source]
                cands = candidates(v.token, sources)
                note = "so far: {}; ".format(", ".join(hint)) if hint else ""
                note += ("candidates: " + ", ".join(cands)) if cands else "no candidates"
                if v.how == "mismatch":
                    note = "{}: {}; {}".format(v.source, v.detail, note)
                lines.append("% src ??? {}   | {} | {}".format(printed, v.context, note))
        lines.append("")
    if stray:
        lines.append("## Declarations outside every unit (remove or move into their unit)")
        lines += ["%   line {}: % src {} {}".format(d.line, d.spec, d.printed) for d in stray]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------------------------------------------
HOW = {"result": "Result", "constant": "Constant", "identity": "Identity", "git": "Commit date",
       "text": "Text count", "commit": "Commit", "none": "**NOT DECLARED**", "mismatch": "**SOURCE DOES NOT MATCH**",
       "decl": "**DECLARATION WITHOUT OCCURRENCE**"}
ORDER = ["result", "constant", "identity", "git", "text", "commit", "none", "mismatch", "decl"]


def _md(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def render(verdicts: Sequence[Verdict], tex_path: str, results_path: str,
           now: Optional[dt.datetime] = None) -> str:
    now = now or dt.datetime.now(dt.timezone.utc)
    errors = [v for v in verdicts if not v.ok]
    counts: Dict[str, int] = {}
    for v in verdicts:
        counts[v.how] = counts.get(v.how, 0) + 1
    lines = [
        "# Number check Paper 2",
        "",
        "Generated {} with `scripts/p2_number_check.py` from `{}` against `{}` and the list of constants of the "
        "pre-registration. Rules in the header of the script.".format(now.strftime("%Y-%m-%d %H:%M UTC"), tex_path,
                                                                     results_path),
        "",
        "Checked are the abstract, the prose of all sections and subsections including their titles, and all "
        "figure captions; not checked are the title, keywords, cross-references, citations, URLs, display formulas "
        "and the bibliography. Every number, date and clock time is bound by `% src source printed` in its unit to "
        "exactly one source, in the order of the text; nothing is searched. \"Text count\": a count word that the "
        "sentence itself makes evident (`text:`), without a data source.",
        "",
        "## Result",
        "",
        "- Numbers, dates and commits in the text: {}".format(sum(1 for v in verdicts if v.how != "decl")),
    ]
    for how in ORDER:
        if counts.get(how):
            lines.append("- {}: {}".format(HOW[how].strip("*"), counts[how]))
    lines += ["", "**Errors: {}**".format(len(errors)) + ("" if errors else " (none)"), ""]
    if errors:
        lines += ["| Place | Text | Kind | Line | Note |", "|---|---|---|---|---|"]
        lines += ["| {} | `{}` | {} | {} | {} |".format(_md(v.unit), _md(v.token.rel + v.token.raw), HOW[v.how],
                                                       v.line or "", _md(" ".join(s for s in [v.source, v.detail,
                                                                                          v.context] if s)))
                  for v in errors]
        lines.append("")
    texts = [v for v in verdicts if v.how == "text"]
    if texts:
        lines += ["Text counts (without a data source, for review):", ""]
        lines += ["- {}: `{}` ({}) … {} …".format(_md(v.unit), v.token.raw, v.source, _md(v.context)) for v in texts]
        lines.append("")
    lines += ["## All numbers", "", "| Place | Text | Evidence | Source | Value |", "|---|---|---|---|---|"]
    for v in verdicts:
        lines.append("| {} | `{}` | {} | {} | {} |".format(_md(v.unit), _md((v.token.rel + v.token.raw).strip()),
                                                         HOW[v.how], _md(v.source), _md(v.detail)))
    lines += ["", "## Constants of the pre-registration", "",
              "Source: `{}` (commit `c9e9162`) with Addenda 1 to 4 of 25 September 2026, Addendum 5 of 27 September, "
              "Addendum 6 of 30 September and Addendum 7 of 5 October 2026; the bucket edges from "
              "`{}`. In the manuscript as `const:name`. Sections are named as in the English translations, with the "
              "heading of the binding German original in quotation marks.".format(PREREG, PREREG_P1), "",
              "| Name | Value | Meaning | Section |", "|---|---|---|---|"]
    for name, (v, w, path, s) in CONSTANTS.items():
        shown = v if isinstance(v, str) else ("{:,}".format(int(v)).replace(",", " ") if float(v).is_integer()
                                              else v)
        section = s + (' ("{}")'.format(SECTION_ORIGINAL[s]) if s in SECTION_ORIGINAL else "")
        lines.append("| `{}` | {} | {} | {}{} |".format(name, shown, _md(w), section,
                                                       "" if path == PREREG else " (Paper 1)"))
    lines += ["", "Arithmetic identities (no results, only reading aids; in the manuscript as `ident:name`):", ""]
    lines += ["- `{}` = {:.4f}: {}".format(k, v, w) for k, (v, w) in IDENTITIES.items()]
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tex", default=str(TEX))
    ap.add_argument("--results", default=str(RESULTS))
    ap.add_argument("--report", default=str(REPORT))
    ap.add_argument("--no-report", action="store_true", help="print only, do not write the report")
    ap.add_argument("--template", action="store_true",
                    help="print every number in the order of the text with its binding or candidates")
    args = ap.parse_args(argv)
    tex = Path(args.tex).read_text()
    if args.template:
        print(template(tex, Path(args.results)), end="")
        return 0
    verdicts = check(tex, Path(args.results))
    errors = [v for v in verdicts if not v.ok]
    if not args.no_report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(render(verdicts, args.tex, args.results))
    print("numbers checked  {}".format(sum(1 for v in verdicts if v.how != "decl")))
    print("text counts      {}".format(sum(1 for v in verdicts if v.how == "text")))
    print("errors           {}".format(len(errors)))
    for v in errors:
        print("  {:<34} {!r:<22} {:<9} {}{}".format(v.unit[:34], v.token.rel + v.token.raw, v.how,
                                                    "line {} ".format(v.line) if v.line else "",
                                                    " ".join(s for s in [v.source, v.detail] if s)))
    if not args.no_report:
        print("report           {}".format(args.report))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
