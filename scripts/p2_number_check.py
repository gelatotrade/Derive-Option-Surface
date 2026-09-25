#!/usr/bin/env python3
"""Check every number in the text of the Paper 2 manuscript against ``results/p2`` and the pre-registration.

Rule of the manuscript: a number in the text is either a result, and then it stands in a file under
``results/p2`` (including ``results/p2/semantik``), or it is a constant of the pre-registration, and then it is
on the explicit list ``CONSTANTS`` below with the place where it is registered.  Nothing else may appear.

What is checked: the abstract, the prose of every section (subsection titles included) and every figure
caption.  Not checked: title, keywords, labels, references, citations, URLs, display formulas (notation) and
the bibliography.  Identifiers that carry digits (PM2, H1, M3, R4, UTC+2, Addendum 2) are not numbers.

Declared sources.  A comment line in the manuscript

    % src summary.json:h1_stat 0.903
    % src fig_f1_b.csv:row_median 0.943 0.902 0.875

ties printed numbers to one source: a JSON key (dotted path, ``*`` allowed) or a CSV column (``col`` for any
row, ``col@rowkey`` for rows whose first field is ``rowkey``).  Dates and clock times can be declared as well
("% src summary.json:api_day 25 September 2026"): the declared file must contain that date or time (anywhere in
it), ``const:`` binds it to the constants of the pre-registration and ``git:<sha>`` to the author date of a
commit in its own time zone.  The pseudo file ``derived`` holds counts over
``h1.json`` to ``h4.json`` (``n_rejected``, ``n_not_rejected``, ``n_hypotheses``) and the number of occupied
cells with positive edge in ``h1_cells.csv`` (``h1_cells_pos``), because no single file states them.  A declaration before the first section holds for
the whole text, except inside the abstract environment, where it holds for the abstract only; one inside a section
holds for that section and the captions of its floats.  Every occurrence of
a declared number in its scope must then be covered by the declared sources and by nothing else; a declared
number the source no longer covers, for instance after the final data run, is reported as not covered.  Numbers
without a declaration are matched generically.

How a number is matched:

* A number printed with ``d`` decimals is covered by a value ``v`` if ``|v * s - x| <= 0.5 * 10**-d`` (plus a
  relative 1e-9), so ``0.903`` is covered by ``0.90294``; scientific notation (``8.7\\times10^{-10}``) works on
  the mantissa.  The scale ``s`` is 1, and for a number followed by "per cent" (also at the end of a range,
  "from 3.64 to 3.82 per cent") also 100 (share to per cent) and 0.01 (basis points to per cent); "basis
  points" also allows 1e4.  A number printed without a sign may be covered by the magnitude of a negative
  value ("fell by 22.9 per cent"), and the report says so; a printed minus needs a negative value.  A printed
  integer is covered by a rounded value only if it has at least three significant digits.
* Generic sources come in three tiers: (0) ``summary.json``; (1) ``h1.json`` to ``h4.json``,
  ``sensitivity*.json``, ``validation_summary.json``, ``events.csv`` and the probe results
  ``semantik/faktoren.csv``, ``semantik/box_diskont.json``, ``semantik/v_konvention.json``; (2) every other
  JSON or CSV file.  Raw draws (numeric lists longer than 25 entries) are not sources, and inside strings only
  integers of five digits or more count (block numbers), plus dates and clock times.
* Generic order: a constant of the pre-registration; else an exact value in tier 0 or 1; else a rounded value in
  tier 0 or 1; else an arithmetic identity; else a value in tier 2, which must be exact or printed with at least
  three significant digits, because a large table covers almost any short number by chance.
* Dates ("17 September 2026", "September 2026", "17 September"), clock times ("08:00") and commit hashes in
  ``\\texttt`` are matched against the dates and times in the result files, the constants and the git history.
  Spelled numbers from "two" upwards count as numbers ("one" is too ambiguous and is skipped).

The report names the source found first and up to two more that fit equally well.

    python3 scripts/p2_number_check.py [--tex paper2/main.tex] [--results results/p2]
                                       [--report docs/paper2/ZAHLENPRUEFUNG.md] [--no-report]

Exit status 1 if any number is not covered.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import fnmatch
import json
import math
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[1]
TEX = Path("paper2/main.tex")
RESULTS = Path("results/p2")
REPORT = Path("docs/paper2/ZAHLENPRUEFUNG.md")
PREREG = "docs/paper2/PRAEREGISTRIERUNG.md"

# ---------------------------------------------------------------------------------------------------------------
# Constants of the pre-registration (commit 1d13227) and its dated addenda: value, meaning, section.
# ---------------------------------------------------------------------------------------------------------------
CONSTANTS: List[Tuple[float, str, str]] = [
    (0, "cash = 0 in K_p(q) = Σ p·q − net_IM(q; cash = 0)", "Semantik und Kapital"),
    (1, "q = +1 bei Maker-Kauf; Dosisfilter 1 %; Schwelle 95. Perzentil 1 %",
     "Semantik und Kapital; Hypothesen, H4; Validierung vor der Messung"),
    (-1, "q = −1 bei Maker-Verkauf", "Semantik und Kapital"),
    (30, "Netto-Edge nach 30 Minuten; Laufzeit-Bucketgrenze 30 Tage (Paper 1); Referenzbuch nahe 30 Tagen",
     "Semantik und Kapital"),
    (200, "Zelle besetzt ab 200 Fills", "Semantik und Kapital"),
    (10_000, "10⁴ in den Zellgrössen (Basispunkte)", "Semantik und Kapital"),
    (10, "die zehn dominanten Maker-Subaccounts; |Δ|-Bucketgrenze 10 % (Paper 1)", "Maker-Bücher; Semantik"),
    (3, "drei Manager: SM, Legacy-PM, PM2", "Stichprobe (Manager-Fenster)"),
    (4, "vier Hypothesen H1 bis H4", "Hypothesen und Ablehnungsregeln"),
    (0.5, "Schwelle H1 (obere Grenze ≥ 0,5) und H2 (Median < 0,5)", "Hypothesen und Ablehnungsregeln"),
    (2, "Schwelle H3 (Median > 2); Chain- und API-Semantik; API-Diskont 2 %; Laufzeit-Bucketgrenze 2 Tage",
     "Hypothesen und Ablehnungsregeln; Inferenz; Semantik"),
    (90, "90-%-Intervall", "Hypothesen und Ablehnungsregeln"),
    (20_000, "einfache Zufallsstichprobe von 20 000 Fills (H2)", "Hypothesen, H2"),
    (20_260_924, "Seed 20260924", "Hypothesen, H2; Inferenz"),
    (14, "Dosisfenster [e − 14 Tage, e) und Regressionsfenster ± 14 Tage", "Hypothesen, H4"),
    (20, "mindestens 20 Fills vor und nach dem Ereignis; mindestens 20 Maker-Tage (Validierung)",
     "Hypothesen, H4; Validierung vor der Messung"),
    (5, "einseitiges p ≤ 0,05 (fünf Prozent)", "Hypothesen, H4"),
    (0.05, "einseitiges p ≤ 0,05", "Hypothesen, H4"),
    (95, "95. Perzentil (Placebo-β, Validierung)", "Hypothesen, H4; Validierung vor der Messung"),
    (100, "100 Placebo-Termine", "Hypothesen, H4"),
    (28, "Placebo-Termine mindestens 28 Tage von jedem Ereignis", "Hypothesen, H4"),
    (9_999, "B = 9 999 Bootstrap-Ziehungen", "Inferenz"),
    (48, "mindestens 48 Zufallsblöcke je Basiswert und Manager", "Validierung vor der Messung"),
    (0.1, "Schwelle Median der absoluten relativen Abweichung 0,1 %", "Validierung vor der Messung"),
    (63, "63 Optionen, die ein SM-Konto auf v2 halten kann", "Nachtrag 4, Ziffer 2"),
    (25, "|Δ|-Bucketgrenze 25 %", "Semantik und Kapital (Buckets aus Paper 1)"),
    (40, "|Δ|-Bucketgrenze 40 %", "Semantik und Kapital (Buckets aus Paper 1)"),
    (60, "|Δ|-Bucketgrenze 60 %", "Semantik und Kapital (Buckets aus Paper 1)"),
    (0.6, "|Δ|-Bucketgrenze 60 % als Delta 0,6", "Semantik und Kapital (Buckets aus Paper 1)"),
    (75, "|Δ|-Bucketgrenze 75 %", "Semantik und Kapital (Buckets aus Paper 1)"),
    (7, "Laufzeit-Bucketgrenze 7 Tage", "Semantik und Kapital (Buckets aus Paper 1)"),
]
CONSTANT_DATES: List[Tuple[str, str, str]] = [
    ("2024-01-11", "Stichprobenbeginn 11.01.2024 00:00 UTC", "Stichprobe"),
    ("2026-09-30", "präregistriertes Stichprobenende 30.09.2026 08:00 UTC", "Stichprobe"),
    ("2026-09-17", "Pilotschnitt 17.09.2026 12:00 UTC", "Stichprobe"),
    ("2025-06-12", "PM2-Fenster BTC und ETH ab 12.06.2025 23:00 UTC", "Stichprobe (Manager-Fenster)"),
    ("2025-11-11", "SM und PM2 für HYPE ab 11.11.2025", "Stichprobe (Manager-Fenster)"),
    ("2024-06-12", "Legacy-PM-Ereignis 12.06.2024", "Hypothesen, H4"),
    ("2025-02-22", "Legacy-PM-Ereignis 22.02.2025", "Hypothesen, H4"),
    ("2026-09-24", "Präregistrierung, Commit 1d13227 (git log)", "Kopf der Präregistrierung"),
    ("2026-09-25", "Nachträge 1 bis 4, datiert 25.09.2026", "Nachträge 1 bis 4"),
]
CONSTANT_TIMES: List[Tuple[str, str, str]] = [
    ("00:00", "Stichprobenbeginn und HYPE-Fenster 00:00 UTC", "Stichprobe"),
    ("08:00", "Stichprobenende 08:00 UTC", "Stichprobe"),
    ("12:00", "Pilotschnitt 12:00 UTC", "Stichprobe"),
    ("23:00", "PM2-Fenster ab 23:00 UTC", "Stichprobe (Manager-Fenster)"),
    ("22:33", "Commit 1d13227 um 22:33 UTC+2 (git log)", "Kopf der Präregistrierung"),
]
# Arithmetic identities used to read a result; they are not results.
IDENTITIES: List[Tuple[float, str]] = [
    (math.log(0.9), "ln 0,9: Dosis, wenn Kapital zehn Prozent billiger wird (Lesehilfe zu β, Abbildung F6)"),
]

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]
MONTH_ABBR = {m[:3]: i + 1 for i, m in enumerate(MONTHS)}
WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
         "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
         "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100}
UNITS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}

TIERS = 3
TIER1 = {"h1.json", "h2.json", "h3.json", "h4.json", "sensitivity.json", "sensitivity_h4.json",
         "validation_summary.json", "events.csv", "semantik/faktoren.csv", "semantik/box_diskont.json",
         "semantik/v_konvention.json"}
MAX_LIST = 25              # longer numeric lists are raw draws, not reported numbers
MIN_SIG = 3                # significant digits a rounded match needs in tier 2, and a rounded integer anywhere


# ---------------------------------------------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------------------------------------------
@dataclass
class Pool:
    """Every number, date and clock time under a results directory: sorted per tier, and per file for lookups."""
    values: List[List[float]] = field(default_factory=lambda: [[] for _ in range(TIERS)])
    keys: List[List[str]] = field(default_factory=lambda: [[] for _ in range(TIERS)])
    by_file: Dict[str, List[Tuple[str, str, float]]] = field(default_factory=dict)  # file -> (row, key, value)
    dates: Dict[str, Tuple[int, str]] = field(default_factory=dict)   # 'YYYY-MM-DD' -> (tier, source)
    times: Dict[str, Tuple[int, str]] = field(default_factory=dict)   # 'HH:MM' -> (tier, source)
    dates_by_file: Dict[str, set] = field(default_factory=dict)       # file -> dates found in it
    times_by_file: Dict[str, set] = field(default_factory=dict)       # file -> clock times found in it
    files: int = 0

    def add(self, tier: int, value, label: str, file: str = "", row: str = "", key: str = "") -> None:
        if isinstance(value, bool) or value is None:
            return
        v = float(value)
        if not math.isfinite(v):
            return
        self.values[tier].append(v)
        self.keys[tier].append(label)
        if file:
            self.by_file.setdefault(file, []).append((row, key, v))

    def add_date(self, iso: str, tier: int, label: str) -> None:
        if iso not in self.dates or tier < self.dates[iso][0]:
            self.dates[iso] = (tier, label)
        self.dates_by_file.setdefault(_label_file(label), set()).add(iso)

    def add_time(self, hhmm: str, tier: int, label: str) -> None:
        if hhmm not in self.times or tier < self.times[hhmm][0]:
            self.times[hhmm] = (tier, label)
        self.times_by_file.setdefault(_label_file(label), set()).add(hhmm)

    def finish(self) -> "Pool":
        for t in range(TIERS):
            order = sorted(range(len(self.values[t])), key=self.values[t].__getitem__)
            self.values[t] = [self.values[t][i] for i in order]
            self.keys[t] = [self.keys[t][i] for i in order]
        return self

    def size(self) -> int:
        return sum(len(v) for v in self.values)

    def find(self, tier: int, lo: float, hi: float) -> List[Tuple[float, str]]:
        """Every value of one tier in [lo, hi]."""
        vals = self.values[tier]
        i = bisect.bisect_left(vals, lo)
        j = bisect.bisect_right(vals, hi)
        return [(vals[n], self.keys[tier][n]) for n in range(i, j)]

    def declared(self, spec: str) -> List[Tuple[float, str]]:
        """Values of a declared source ``file:key`` (JSON, glob allowed) or ``file:col[@rowkey]`` (CSV)."""
        file, _, key = spec.partition(":")
        rows = self.by_file.get(file, [])
        if file.endswith(".csv"):
            col, _, rowkey = key.partition("@")
            return [(v, "{}[{}].{}".format(file, r, k)) for r, k, v in rows
                    if k == col and (not rowkey or r == rowkey)]
        return [(v, "{}:{}".format(file, k)) for _, k, v in rows if fnmatch.fnmatchcase(k, key)]


def _label_file(label: str) -> str:
    """The file of a source label ``file:path``, ``file[row].col`` or ``file (header)``."""
    return re.split(r"[:\[ ]", label, maxsplit=1)[0]


ISO = re.compile(r"(?<!\d)(\d{4})-(\d{2})(?:-(\d{2}))?(?:[T ](\d{2}):(\d{2}))?")
COMPACT = re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)")
DOTTED = re.compile(r"(?<![\d.])(\d{1,2})\.(\d{1,2})\.(\d{4})?")
WORDDATE = re.compile(r"(?<!\d)(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?\s+(\d{4})")
CLOCK = re.compile(r"(?<!\d)(\d{2}):(\d{2})(?::\d{2})?")
LONGINT = re.compile(r"(?<![\d.\-])\d{5,}(?![\d.])")


def _valid(y: int, m: int, d: Optional[int] = None) -> bool:
    try:
        dt.date(y, m, d or 1)
    except ValueError:
        return False
    return 2000 <= y <= 2100


def _harvest_string(pool: Pool, tier: int, text: str, label: str, file: str = "", row: str = "",
                    key: str = "", numbers: bool = True) -> None:
    for m in ISO.finditer(text):
        y, mo = int(m.group(1)), int(m.group(2))
        d = int(m.group(3)) if m.group(3) else None
        if _valid(y, mo, d):
            iso = "{:04d}-{:02d}".format(y, mo) + ("-{:02d}".format(d) if d else "")
            pool.add_date(iso, tier, label)
            if d:
                pool.add_date(iso[:7], tier, label)
        if m.group(4):
            pool.add_time("{}:{}".format(m.group(4), m.group(5)), tier, label)
    for m in COMPACT.finditer(text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid(y, mo, d):
            iso = "{:04d}-{:02d}-{:02d}".format(y, mo, d)
            pool.add_date(iso, tier, label)
            pool.add_date(iso[:7], tier, label)
    for m in DOTTED.finditer(text):
        d, mo = int(m.group(1)), int(m.group(2))
        y = int(m.group(3)) if m.group(3) else None
        if 1 <= mo <= 12 and 1 <= d <= 31:
            pool.add_date("--{:02d}-{:02d}".format(mo, d), tier, label)
            if y and _valid(y, mo, d):
                pool.add_date("{:04d}-{:02d}-{:02d}".format(y, mo, d), tier, label)
    for m in WORDDATE.finditer(text):
        mo = MONTH_ABBR.get(m.group(2).lower())
        if mo and _valid(int(m.group(3)), mo, int(m.group(1))):
            iso = "{:04d}-{:02d}-{:02d}".format(int(m.group(3)), mo, int(m.group(1)))
            pool.add_date(iso, tier, label)
            pool.add_date(iso[:7], tier, label)
    for m in CLOCK.finditer(text):
        if int(m.group(1)) < 24 and int(m.group(2)) < 60:
            pool.add_time("{}:{}".format(m.group(1), m.group(2)), tier, label)
    if numbers:
        # only long integers (block numbers); short numbers inside strings belong to dates, ids and rule texts
        for m in LONGINT.finditer(text):
            pool.add(tier, float(m.group(0)), label + " (text)", file, row, key)


def _harvest_epoch(pool: Pool, tier: int, name: str, value: float, label: str) -> None:
    """Unix times in columns or keys named like a timestamp become dates and clock times."""
    low = name.lower()
    if not (low == "ts" or low.endswith("_ts") or low.startswith("ts_") or "_ts_" in low):
        return
    if 1.4e9 <= value <= 2.2e9:
        t = dt.datetime.fromtimestamp(value, tz=dt.timezone.utc)
        iso = t.strftime("%Y-%m-%d")
        pool.add_date(iso, tier, label)
        pool.add_date(iso[:7], tier, label)
        pool.add_time(t.strftime("%H:%M"), tier, label)


def _walk_json(pool: Pool, tier: int, obj, file: str, path: str = "", name: str = "") -> None:
    label = "{}:{}".format(file, path)
    if isinstance(obj, dict):
        for k, v in obj.items():
            _harvest_string(pool, tier, str(k), label, numbers=False)
            _walk_json(pool, tier, v, file, (path + "." if path else "") + str(k), str(k))
    elif isinstance(obj, list):
        if len(obj) > MAX_LIST and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in obj):
            return
        for i, v in enumerate(obj):
            _walk_json(pool, tier, v, file, "{}.{}".format(path, i) if path else str(i), name)
    elif isinstance(obj, bool) or obj is None:
        return
    elif isinstance(obj, (int, float)):
        pool.add(tier, obj, label, file, "", path)
        _harvest_epoch(pool, tier, name, float(obj), label)
    elif isinstance(obj, str):
        _harvest_string(pool, tier, obj, label, file, "", path)


def tier_of(rel: str) -> int:
    if rel == "summary.json":
        return 0
    if rel in TIER1:
        return 1
    return 2


def load_pool(results: Path) -> Pool:
    """Every number, date and clock time in the JSON, JSONL and CSV files under ``results``."""
    pool = Pool()
    for path in sorted(results.rglob("*")):
        if not path.is_file() or path.suffix not in (".json", ".jsonl", ".csv"):
            continue
        rel = path.relative_to(results).as_posix()
        tier = tier_of(rel)
        pool.files += 1
        if path.suffix == ".json":
            try:
                _walk_json(pool, tier, json.loads(path.read_text()), rel)
            except json.JSONDecodeError:
                _harvest_string(pool, tier, path.read_text(), rel, rel)
        elif path.suffix == ".jsonl":
            for n, line in enumerate(path.read_text().splitlines(), 1):
                if line.strip():
                    try:
                        _walk_json(pool, tier, json.loads(line), rel, str(n))
                    except json.JSONDecodeError:
                        _harvest_string(pool, tier, line, "{}:{}".format(rel, n), rel, str(n))
        else:
            with path.open(newline="") as fh:
                reader = csv.reader(fh)
                header = next(reader, [])
                for col in header:
                    _harvest_string(pool, tier, col, rel + " (header)", numbers=False)
                for n, row in enumerate(reader, 1):
                    rowkey = row[0] if row else str(n)
                    shown = rowkey if len(rowkey) <= 40 else str(n)
                    for col, cell in zip(header, row):
                        if cell == "":
                            continue
                        label = "{}[{}].{}".format(rel, shown, col)
                        try:
                            v = float(cell)
                        except ValueError:
                            _harvest_string(pool, tier, cell, label, rel, rowkey, col)
                            continue
                        pool.add(tier, v, label, rel, rowkey, col)
                        _harvest_epoch(pool, tier, col, v, label)
    _add_derived(pool, results)
    return pool.finish()


def _add_derived(pool: Pool, results: Path) -> None:
    """Counts over the registered verdicts, which no single file states: file ``derived`` in declarations."""
    flags = []
    for name in ("h1.json", "h2.json", "h3.json", "h4.json"):
        path = results / name
        if path.is_file():
            try:
                flags.append(json.loads(path.read_text()).get("rejected"))
            except json.JSONDecodeError:
                continue
    cells = results / "h1_cells.csv"
    if cells.is_file():
        with cells.open(newline="") as fh:
            rows = list(csv.DictReader(fh))
        try:
            pos = sum(1 for r in rows if r.get("occupied") == "True" and float(r.get("A_bp") or "nan") > 0)
            pool.add(0, pos, "derived:h1_cells_pos (h1_cells.csv, occupied und A_bp > 0)", "derived", "",
                     "h1_cells_pos")
        except ValueError:
            pass
    if flags and all(isinstance(f, bool) for f in flags):
        pool.add(0, sum(flags), "derived:n_rejected (h1.json bis h4.json, rejected)", "derived", "", "n_rejected")
        pool.add(0, len(flags) - sum(flags), "derived:n_not_rejected (h1.json bis h4.json, rejected)", "derived",
                 "", "n_not_rejected")
        pool.add(0, len(flags), "derived:n_hypotheses (h1.json bis h4.json)", "derived", "", "n_hypotheses")


# ---------------------------------------------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------------------------------------------
COMMENT = re.compile(r"(?<!\\)%.*")
FIGURE = re.compile(r"\\begin\{(figure\*?)\}(.*?)\\end\{\1\}", re.S)
DISPLAY = re.compile(r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}.*?\\end\{\1\}|\\\[.*?\\\]", re.S)
DECLARATION = re.compile(r"^\s*%+\s*src\s+(\S+:\S+)\s+(.+?)\s*$", re.M)


@dataclass
class Unit:
    where: str
    text: str
    scope: str = "global"      # the section whose declarations apply, besides the global ones


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


def _sections(tex: str) -> Tuple[str, List[Tuple[str, str]]]:
    """Front matter up to the first section, and (name, content) per section, comments kept."""
    body = re.split(r"\\bibliographystyle|\\bibliography\{|\\end\{document\}", tex)[0]
    parts = re.split(r"\\section\*?\{([^}]*)\}", body)
    return parts[0], list(zip(parts[1::2], parts[2::2]))


def units(tex: str) -> List[Unit]:
    """Abstract, section prose and figure captions, in the order of the manuscript.

    The ``scope`` of a unit is the section it stands in; a caption belongs to the section of its float.
    """
    front, secs = _sections(tex)
    out: List[Unit] = []
    ab = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", COMMENT.sub("", front), re.S)
    if ab:
        out.append(Unit("abstract", ab.group(1), "abstract"))
    for name, content in secs:
        content = COMMENT.sub("", content)
        for fig in FIGURE.finditer(content):
            label = re.search(r"\\label\{([^}]*)\}", fig.group(2))
            for cap in captions(fig.group(2)):
                out.append(Unit("caption " + (label.group(1) if label else "?"), cap, name))
        prose = DISPLAY.sub(" ", FIGURE.sub(" ", content))
        out.append(Unit(name, prose, name))
    return out


@dataclass
class Token:
    kind: str                 # number, date, month, dayonly, time, commit
    raw: str
    value: float = float("nan")
    decimals: int = 0
    exponent: int = 0
    signed: bool = False
    unit: str = ""            # percent, bp
    iso: str = ""
    spelled: bool = False

    def ident(self) -> Tuple[float, int, int, bool]:
        """What a declaration binds: value and printed precision; "four" and "4" are different numbers."""
        return round(self.value, 12), self.decimals, self.exponent, self.spelled


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
UNIT_WORD = r"(?:per\s+cent\b|percent\b|log\s+per\s+cent\b|basis\s+points?\b|bp\b)"
UNIT_AFTER = re.compile(r"\s*" + UNIT_WORD, re.I)
RANGE_UNIT = re.compile(r"\s*(?:to|and|or)\s+[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?\s*" + UNIT_WORD, re.I)
WORD_RE = re.compile(r"(?<![A-Za-z-])(" + "|".join(sorted(WORDS, key=len, reverse=True)) + r")(?:-(" +
                     "|".join(UNITS) + r"))?(?![A-Za-z])", re.I)


def _unit(after: str) -> str:
    m = UNIT_AFTER.match(after) or RANGE_UNIT.match(after)
    if not m:
        return ""
    word = m.group(0).lower()
    if "cent" in word:
        return "percent"
    return "bp"


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


def tokens(text: str) -> List[Token]:
    """Numbers, dates, clock times and commit hashes of one piece of LaTeX prose."""
    text, out = clean(text)

    def take(pattern, make):
        nonlocal text

        def repl(m):
            out.append(make(m))
            return " ; "
        text = pattern.sub(repl, text)

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
        out.append(Token("number", m.group(0).strip(), value=value, decimals=decimals, exponent=exp,
                         signed=bool(m.group("sign")), unit=_unit(text[m.end():m.end() + 40])))
    for m in WORD_RE.finditer(text):
        value = WORDS[m.group(1).lower()] + (UNITS[m.group(2).lower()] if m.group(2) else 0)
        out.append(Token("number", m.group(0), value=float(value), spelled=True,
                         unit=_unit(text[m.end():m.end() + 40])))
    return out


def declarations(tex: str) -> List[Tuple[str, str, Token]]:
    """(scope, source spec, printed number) for every ``% src file:key numbers`` line of the manuscript.

    A declaration before the first section is global, except one inside the abstract environment, which applies
    to the abstract only; one inside a section applies to that section's prose and to the captions of the floats
    placed in it.
    """
    out = []
    front, secs = _sections(tex)
    ab = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", front, re.S)
    parts = [("global", front)]
    if ab:   # declarations inside the abstract environment hold for the abstract only
        parts = [("abstract", ab.group(1)), ("global", front[:ab.start()] + front[ab.end():])]
    for scope, text in parts + list(secs):
        for m in DECLARATION.finditer(text):
            for tok in tokens(m.group(2)):
                if tok.kind != "commit":
                    out.append((scope, m.group(1), tok))
    return out


def decl_key(tok: Token):
    """What a declaration binds: a number with its printed precision, or a date or clock time."""
    if tok.kind == "number":
        return tok.ident()
    return ("time" if tok.kind == "time" else "date", tok.iso)


def _date_in(iso: str, dates) -> bool:
    """A printed date (full, month or day of a month) among ISO dates."""
    if iso.startswith("--"):
        return any(d.endswith(iso[1:]) for d in dates)
    return iso in dates or any(d.startswith(iso) for d in dates)


def default_git_date(repo: Path = REPO) -> Callable[[str], Optional[str]]:
    def when(sha: str) -> Optional[str]:
        run = subprocess.run(["git", "-C", str(repo), "show", "-s", "--format=%ai", sha],
                             capture_output=True, text=True)
        return run.stdout.strip() or None if run.returncode == 0 else None
    return when


def match_declared_date(tok: Token, specs: Sequence[str], pool: "Pool",
                        git_date: Optional[Callable[[str], Optional[str]]] = None) -> Tuple[bool, str, str]:
    """(covered, source, detail) of a date or clock time bound by declarations."""
    git_date = git_date or default_git_date()
    for spec in specs:
        file, _, key = spec.partition(":")
        if file == "const":
            pool_d = [d for d, _, _ in CONSTANT_DATES] if tok.kind != "time" else [x for x, _, _ in CONSTANT_TIMES]
            ok = _date_in(tok.iso, pool_d) if tok.kind != "time" else tok.iso in pool_d
        elif file == "git":
            stamp = git_date(key)
            ok = bool(stamp) and (tok.iso == stamp[11:16] if tok.kind == "time" else _date_in(tok.iso, [stamp[:10]]))
        elif tok.kind == "time":
            ok = tok.iso in pool.times_by_file.get(file, set())
        else:
            ok = _date_in(tok.iso, pool.dates_by_file.get(file, set()))
        if ok:
            return True, spec, tok.iso
    return False, ", ".join(specs), "erklärte Quelle deckt das Datum nicht"


# ---------------------------------------------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------------------------------------------
@dataclass
class Verdict:
    unit: str
    token: Token
    ok: bool
    how: str          # declared, result, constant, identity, date, time, commit, none
    source: str
    detail: str = ""


def _scales(unit: str) -> List[Tuple[float, str]]:
    if unit == "percent":
        return [(1.0, ""), (100.0, "×100"), (0.01, "bp→%")]
    if unit == "bp":
        return [(1.0, ""), (1e4, "×10⁴")]
    return [(1.0, "")]


def _tolerance(tok: Token) -> float:
    return 0.5 * 10.0 ** (tok.exponent - tok.decimals)


def significant(tok: Token) -> int:
    """Significant digits as printed: 0.0345 has 3, 7.80 has 3, 42 has 2."""
    if tok.spelled:
        return len(str(int(abs(tok.value))))
    mantissa = tok.raw.lower().split("e")[0]
    digits = re.sub(r"[^0-9]", "", mantissa).lstrip("0")
    return len(digits) or 1


def _fits(tok: Token, candidates: List[Tuple[float, str]], exact: bool) -> List[Tuple[float, str, str]]:
    """Candidates that print as the token, best first, as (value, source, flags)."""
    x = tok.value
    tol = 1e-9 * max(1.0, abs(x)) if exact else _tolerance(tok) + 1e-9 * max(1.0, abs(x))
    signs = [1.0] if tok.signed else [1.0, -1.0]
    hits = []
    for value, source in candidates:
        for sign in signs:
            for scale, label in _scales(tok.unit):
                err = abs(value * scale - sign * x)
                if err <= tol:
                    flags = " ".join(f for f in [label, "Betrag" if sign < 0 else ""] if f)
                    hits.append((err, value, source, flags))
    hits.sort(key=lambda h: h[0])
    seen, out = set(), []
    for _, v, s, f in hits:
        if s not in seen:
            seen.add(s)
            out.append((v, s, f))
    return out


def _search(tok: Token, pool: Pool, tier: int, exact: bool) -> List[Tuple[float, str, str]]:
    x = tok.value
    tol = 1e-9 * max(1.0, abs(x)) if exact else _tolerance(tok) + 1e-9 * max(1.0, abs(x))
    signs = [1.0] if tok.signed else [1.0, -1.0]
    cands: List[Tuple[float, str]] = []
    for sign in signs:
        for scale, _ in _scales(tok.unit):
            lo, hi = sorted(((sign * x - tol) / scale, (sign * x + tol) / scale))
            cands.extend(pool.find(tier, lo, hi))
    return _fits(tok, cands, exact)


def _describe(hits: List[Tuple[float, str, str]], exact: bool) -> Tuple[str, str]:
    value, source, flags = hits[0]
    others = [s for _, s, _ in hits[1:3]]
    label = source + ("; auch " + "; ".join(others) if others else "")
    return label, ("{} {:.6g} {}".format("=" if exact else "≈", value, flags)).strip()


def _constant(tok: Token) -> Optional[Tuple[str, str]]:
    """A constant is registered as a value, not as a rounding: only an exact match counts."""
    x = tok.value
    tol = 1e-9 * max(1.0, abs(x))
    for value, what, where in CONSTANTS:
        same_sign = not tok.signed or value == 0 or math.copysign(1, x) == math.copysign(1, value)
        if abs(abs(x) - abs(value)) <= tol and same_sign:
            return "{} ({})".format(PREREG, where), what
    return None


def match_number(tok: Token, pool: Pool,
                 declared: Optional[Dict[Tuple[float, int, int, bool], List[str]]] = None) -> Tuple[bool, str, str, str]:
    """(covered, how, source, detail) for one number, in the order of the module docstring."""
    specs = (declared or {}).get(tok.ident())
    if specs:
        cands = [c for spec in specs for c in pool.declared(spec)]
        exact = _fits(tok, cands, exact=True)
        rounded_ok = tok.decimals > 0 or tok.exponent != 0 or significant(tok) >= MIN_SIG
        hits = exact or (_fits(tok, cands, exact=False) if rounded_ok else [])
        if hits:
            source, detail = _describe(hits, bool(exact))
            return True, "declared", source, detail
        return False, "none", ", ".join(specs), "erklärte Quelle deckt die Zahl nicht"
    rounded_ok = tok.decimals > 0 or tok.exponent != 0 or significant(tok) >= MIN_SIG
    const = _constant(tok)
    if const:
        return True, "constant", const[0], const[1]
    for tier in (0, 1):
        hits = _search(tok, pool, tier, exact=True)
        if hits:
            source, detail = _describe(hits, True)
            return True, "result", source, detail
    if rounded_ok:
        for tier in (0, 1):
            hits = _search(tok, pool, tier, exact=False)
            if hits:
                source, detail = _describe(hits, False)
                return True, "result", source, detail
    for value, what in IDENTITIES:
        tol = _tolerance(tok) + 1e-9
        if abs(tok.value - value) <= tol or (not tok.signed and abs(abs(tok.value) - abs(value)) <= tol):
            return True, "identity", "Rechenidentität", what
    hits = _search(tok, pool, 2, exact=True)
    if hits:
        source, detail = _describe(hits, True)
        return True, "result", source, detail
    if significant(tok) >= MIN_SIG and rounded_ok:
        hits = _search(tok, pool, 2, exact=False)
        if hits:
            source, detail = _describe(hits, False)
            return True, "result", source, detail
        return False, "none", "", "kein Wert in results/p2 und keine Konstante"
    return False, "none", "", ("zu wenige Stellen für einen gerundeten Treffer ausserhalb von summary.json "
                               "und den Testdateien")


def default_commit_resolver(repo: Path = REPO) -> Callable[[str], bool]:
    def resolve(sha: str) -> bool:
        run = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", sha + "^{commit}"],
                             capture_output=True, text=True)
        return run.returncode == 0
    return resolve


def check_units(us: Sequence[Unit], pool: Pool, resolve_commit: Optional[Callable[[str], bool]] = None,
                declared: Optional[Sequence[Tuple[str, str, Token]]] = None,
                git_date: Optional[Callable[[str], Optional[str]]] = None) -> List[Verdict]:
    resolve_commit = resolve_commit or default_commit_resolver()
    tables: Dict[str, Dict[tuple, List[str]]] = {}
    for scope, spec, tok in declared or []:
        specs = tables.setdefault(scope, {}).setdefault(decl_key(tok), [])
        if spec not in specs:
            specs.append(spec)
    const_dates = {d: (what, where) for d, what, where in CONSTANT_DATES}
    const_times = {t: (what, where) for t, what, where in CONSTANT_TIMES}
    out: List[Verdict] = []
    for u in us:
        table = {k: list(v) for k, v in tables.get("global", {}).items()}
        if u.scope != "global":
            for k, v in tables.get(u.scope, {}).items():
                table[k] = table.get(k, []) + [x for x in v if x not in table.get(k, [])]
        for tok in tokens(u.text):
            if tok.kind == "number":
                ok, how, src, detail = match_number(tok, pool, table)
                out.append(Verdict(u.where, tok, ok, how, src, detail))
            elif tok.kind != "commit" and decl_key(tok) in table:
                ok, src, detail = match_declared_date(tok, table[decl_key(tok)], pool, git_date)
                out.append(Verdict(u.where, tok, ok, "declared" if ok else "none", src, detail))
            elif tok.kind in ("date", "month", "dayonly"):
                if tok.kind == "dayonly":
                    found = [k for k in pool.dates if k.endswith(tok.iso[1:])]
                    hit = min(found, key=lambda k: (pool.dates[k][0], k)) if found else None
                    const = next((d for d in const_dates if d.endswith(tok.iso[1:])), None)
                else:
                    hit = tok.iso if tok.iso in pool.dates else None
                    const = next((d for d in const_dates if d.startswith(tok.iso)), None)
                if hit:
                    out.append(Verdict(u.where, tok, True, "date", pool.dates[hit][1], hit))
                elif const:
                    what, where = const_dates[const]
                    out.append(Verdict(u.where, tok, True, "constant", "{} ({})".format(PREREG, where), what))
                else:
                    out.append(Verdict(u.where, tok, False, "none", "", "Datum weder in results/p2 noch Konstante"))
            elif tok.kind == "time":
                if tok.iso in const_times:
                    what, where = const_times[tok.iso]
                    out.append(Verdict(u.where, tok, True, "constant", "{} ({})".format(PREREG, where), what))
                elif tok.iso in pool.times:
                    out.append(Verdict(u.where, tok, True, "time", pool.times[tok.iso][1]))
                else:
                    out.append(Verdict(u.where, tok, False, "none", "", "Uhrzeit weder in results/p2 noch Konstante"))
            elif tok.kind == "commit":
                ok = resolve_commit(tok.raw)
                out.append(Verdict(u.where, tok, ok, "commit" if ok else "none",
                                   "git: Commit vorhanden" if ok else "", "" if ok else "Commit unbekannt"))
    return out


def check(tex: str, results: Path = RESULTS, pool: Optional[Pool] = None,
          resolve_commit: Optional[Callable[[str], bool]] = None,
          git_date: Optional[Callable[[str], Optional[str]]] = None) -> List[Verdict]:
    """All verdicts for a manuscript; ``pool`` may be passed to avoid reading the results twice."""
    pool = pool if pool is not None else load_pool(results)
    return check_units(units(tex), pool, resolve_commit, declarations(tex), git_date)


def unused_declarations(tex: str, verdicts: Sequence[Verdict]) -> List[Tuple[str, str]]:
    """Declared numbers that no longer occur in their scope."""
    scope_of = {u.where: u.scope for u in units(tex)}
    used = {(scope_of.get(v.unit, "global"), decl_key(v.token)) for v in verdicts if v.token.kind != "commit"}
    used_any = {ident for _, ident in used}
    out = []
    for scope, spec, tok in declarations(tex):
        hit = decl_key(tok) in used_any if scope == "global" else (scope, decl_key(tok)) in used
        if not hit:
            out.append((spec, tok.raw))
    return out


# ---------------------------------------------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------------------------------------------
HOW = {"declared": "Ergebnis (erklärt)", "result": "Ergebnis", "constant": "Konstante", "identity": "Identität",
       "date": "Datum", "time": "Uhrzeit", "commit": "Commit", "none": "**UNBELEGT**"}


def _md(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def render(verdicts: Sequence[Verdict], pool: Pool, tex_path: str, results_path: str, tex: str = "",
           now: Optional[dt.datetime] = None) -> str:
    now = now or dt.datetime.now(dt.timezone.utc)
    bad = [v for v in verdicts if not v.ok]
    counts: Dict[str, int] = {}
    for v in verdicts:
        counts[v.how] = counts.get(v.how, 0) + 1
    unused = unused_declarations(tex, verdicts) if tex else []
    lines = [
        "# Zahlenprüfung Paper 2",
        "",
        "Erzeugt {} mit `scripts/p2_number_check.py` aus `{}` gegen `{}` ({} Dateien, {} Zahlen) und die "
        "Konstantenliste der Präregistrierung. Regeln im Kopf des Skripts.".format(
            now.strftime("%Y-%m-%d %H:%M UTC"), tex_path, results_path, pool.files, pool.size()),
        "",
        "Geprüft sind Abstract, Fliesstext aller Abschnitte samt Zwischentiteln und alle Bildunterschriften; nicht "
        "geprüft Titel, Schlüsselwörter, Verweise, Zitate, URLs, abgesetzte Formeln und Literatur. Kennungen mit "
        "Ziffern (PM2, H1, M3, UTC+2, Addendum 2) sind keine Zahlen. „Ergebnis (erklärt)“: die Zahl ist im "
        "Manuskript per `% src datei:schlüssel` an eine Quelle gebunden und nur gegen sie geprüft. „Ergebnis“: "
        "generischer Treffer, zuerst `summary.json`, dann Hypothesen-, Sensitivitäts- und Probedateien, dann "
        "alle übrigen Tabellen (dort nur exakt oder mit mindestens drei signifikanten Stellen). Bei kleinen "
        "ganzen Zahlen ist die genannte Fundstelle eine von mehreren.",
        "",
        "## Ergebnis",
        "",
        "- Zahlen, Daten und Commits im Text: {}".format(len(verdicts)),
    ]
    for how in ["declared", "result", "constant", "identity", "date", "time", "commit", "none"]:
        if counts.get(how):
            lines.append("- {}: {}".format(HOW[how].strip("*"), counts[how]))
    lines += ["", "**Unbelegte Zahlen: {}**".format(len(bad)) + ("" if bad else " (keine)"), ""]
    if bad:
        lines += ["| Stelle | Text | Art | Hinweis |", "|---|---|---|---|"]
        lines += ["| {} | `{}` | {} | {} |".format(_md(v.unit), _md(v.token.raw), v.token.kind,
                                                 _md(" ".join(s for s in [v.source, v.detail] if s)))
                  for v in bad]
        lines.append("")
    if unused:
        lines += ["Erklärte Zahlen, die im Text nicht mehr vorkommen (Hinweis, kein Fehler):", ""]
        lines += ["- `{}` aus `{}`".format(raw, spec) for spec, raw in unused]
        lines.append("")
    lines += ["## Alle Zahlen", "", "| Stelle | Text | Beleg | Quelle | Wert |", "|---|---|---|---|---|"]
    for v in verdicts:
        lines.append("| {} | `{}` | {} | {} | {} |".format(_md(v.unit), _md(v.token.raw.strip()), HOW[v.how],
                                                         _md(v.source), _md(v.detail)))
    lines += ["", "## Konstanten der Präregistrierung", "",
              "Quelle: `{}` (Commit `1d13227`) mit den Nachträgen 1 bis 4 vom 25.09.2026.".format(PREREG), "",
              "| Wert | Bedeutung | Abschnitt |", "|---|---|---|"]
    lines += ["| {} | {} | {} |".format("{:,}".format(v).replace(",", " ") if float(v).is_integer() else v,
                                        _md(w), _md(s)) for v, w, s in CONSTANTS]
    lines += ["| {} | {} | {} |".format(d, _md(w), _md(s)) for d, w, s in CONSTANT_DATES]
    lines += ["| {} | {} | {} |".format(t, _md(w), _md(s)) for t, w, s in CONSTANT_TIMES]
    lines += ["", "Rechenidentitäten (keine Ergebnisse, nur Lesehilfen):", ""]
    lines += ["- {:.4f}: {}".format(v, w) for v, w in IDENTITIES]
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tex", default=str(TEX))
    ap.add_argument("--results", default=str(RESULTS))
    ap.add_argument("--report", default=str(REPORT))
    ap.add_argument("--no-report", action="store_true", help="print only, do not write the report")
    args = ap.parse_args(argv)
    tex = Path(args.tex).read_text()
    pool = load_pool(Path(args.results))
    verdicts = check(tex, pool=pool)
    bad = [v for v in verdicts if not v.ok]
    if not args.no_report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(render(verdicts, pool, args.tex, args.results, tex))
    print("numbers checked  {}".format(len(verdicts)))
    print("declared         {}".format(sum(v.how == "declared" for v in verdicts)))
    print("unsourced        {}".format(len(bad)))
    for v in bad:
        print("  {:<30} {!r:<14} {}".format(v.unit[:30], v.token.raw, v.detail))
    for spec, raw in unused_declarations(tex, verdicts):
        print("  declared but not in the text: {} ({})".format(raw, spec))
    if not args.no_report:
        print("report           {}".format(args.report))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
