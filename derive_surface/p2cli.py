"""``python3 -m derive_surface p2 <command> ...``: pipeline of paper 2 (capital-adjusted edge on Derive).

Every command hands the remaining arguments unchanged to ``main(argv)`` of its module, for example
``python3 -m derive_surface p2 params load --max-seconds 520`` runs ``derive_surface.p2params.main(["load", ...])``
and ``python3 -m derive_surface p2 feeds --help`` shows the options of the feed module. The exit code is the return
value of that ``main`` (``None`` counts as 0).

Runs that load a FeedHistory with SVI or more than 2 GB go through the machine-wide lock:
``python3 scripts/p2_heavy.py --wait-max 500 -- python3 -m derive_surface p2 <command> ...``.
"""
from __future__ import annotations

import argparse
import importlib
from collections import OrderedDict
from typing import List, NamedTuple, Optional, Sequence

PLAN = "docs/superpowers/plans/2026-09-24-p2-gesamtplan.md"


class Command(NamedTuple):
    module: str  # module inside the package ``derive_surface``
    task: str  # task of the plan that owns the module
    help: str


COMMANDS = OrderedDict([
    ("feeds", Command("p2feeds", "A1", "feed history: sync, compact, crosscheck")),
    ("params", Command("p2params", "A2", "parameter timelines: load, oi-share, report, relabel")),
    ("books", Command("books", "A5/B3", "maker books: top, load, compact, events, verify-events, compare, ...")),
    ("validate", Command("p2validate", "B1", "replica against eth_call")),
    ("capital", Command("capital", "B2", "capital per fill")),
    ("events", Command("p2events", "B4", "parameter events, doses, H4 panel")),
    ("surface", Command("p2surface", "B5", "chain surface, capital surface, reference book, animation")),
    ("infer", Command("inference_p2", "C1", "H1 to H4 and sensitivities")),
    ("figures", Command("figures_p2", "D1", "figures of paper 2")),
    ("ids", Command("p2ids", "B0", "account labels: salt, label")),
])


def _module_main(cmd: str):
    spec = COMMANDS[cmd]
    name = f"{__package__ or 'derive_surface'}.{spec.module}"
    try:
        module = importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name != name:  # the module exists but one of its imports is missing: do not hide that
            raise
        raise SystemExit(f"p2 {cmd}: module {name} is not implemented yet (task {spec.task} of {PLAN})") from None
    fn = getattr(module, "main", None)
    if not callable(fn):
        raise SystemExit(f"p2 {cmd}: module {name} has no main(argv)")
    return fn


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="derive_surface p2", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", metavar="command", required=True)
    for cmd, spec in COMMANDS.items():
        s = sub.add_parser(cmd, add_help=False, help=f"{spec.help} [{spec.module}, {spec.task}]")
        s.add_argument("args", nargs=argparse.REMAINDER)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    import sys

    argv: List[str] = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in COMMANDS:  # forward verbatim, including -h/--help, to the module
        cmd, rest = argv[0], argv[1:]
    else:
        a = _parser().parse_args(argv)  # prints usage and exits for --help, unknown or missing commands
        cmd, rest = a.cmd, a.args
    rc = _module_main(cmd)(rest)
    return 0 if rc is None else int(rc)
