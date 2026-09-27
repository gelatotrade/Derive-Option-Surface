"""``python3 -m derive_surface p2 <command> ...``: pipeline of paper 2 (capital-adjusted edge on Derive).

Every command hands the remaining arguments unchanged to ``main(argv)`` of its module, for example
``python3 -m derive_surface p2 params load --max-seconds 520`` runs ``derive_surface.p2params.main(["load", ...])``
and ``python3 -m derive_surface p2 feeds --help`` shows the options of the feed module. The exit code is the return
value of that ``main`` (``None`` counts as 0). A command whose code lives outside the package (``p2 numbers`` runs
``scripts/p2_numbers.py``) is imported from its file as a module of its own name and its ``main`` is called the same
way.

Runs that load a FeedHistory with SVI or more than 2 GB go through the machine-wide lock:
``python3 scripts/p2_heavy.py --wait-max 500 -- python3 -m derive_surface p2 <command> ...``.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from collections import OrderedDict
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence

PLAN = "docs/superpowers/plans/2026-09-24-p2-master-plan.md"
REPO = Path(__file__).resolve().parents[1]


class Command(NamedTuple):
    module: str  # module inside the package ``derive_surface`` (or the module name of ``script``)
    task: str  # task of the plan that owns the module
    help: str
    script: Optional[str] = None  # repository-relative file of a script outside the package


COMMANDS = OrderedDict([
    ("feeds", Command("p2feeds", "A1", "feed history: sync, compact, crosscheck")),
    ("params", Command("p2params", "A2", "parameter timelines: load, oi-share, report, relabel")),
    ("books", Command("books", "A5/B3", "maker books: top, load, compact, events, verify-events, compare, ...")),
    ("validate", Command("p2validate", "B1", "replica against eth_call")),
    ("capital", Command("capital", "B2", "capital per fill")),
    ("events", Command("p2events", "B4", "parameter events, doses, H4 panel")),
    ("surface", Command("p2surface", "B5", "chain surface, capital surface, reference book, animation")),
    ("infer", Command("inference_p2", "C1", "H1 to H3 and sensitivities")),
    ("infer-h4", Command("inference_p2_h4", "C1", "H4: regression, wild cluster bootstrap, placebo")),
    ("numbers", Command("p2_numbers", "C1", "number sheet docs/paper2/NUMBERS.md and summary.json",
                        script="scripts/p2_numbers.py")),
    ("api", Command("p2api", "C5b", "explorative API snapshot: get_margin against the replica at the head block")),
    ("figures", Command("figures_p2", "D1", "figures of paper 2")),
    ("ids", Command("p2ids", "B0", "account labels: salt, label")),
])


def _load_script(cmd: str, spec: Command):
    """Import ``spec.script`` as the module ``spec.module`` (once; a module of that name from the same file is
    reused, e.g. when a test imported it already)."""
    path = (REPO / spec.script).resolve()
    if not path.is_file():
        raise SystemExit(f"p2 {cmd}: script {spec.script} is missing (task {spec.task} of {PLAN})")
    mod = sys.modules.get(spec.module)
    if mod is not None and Path(getattr(mod, "__file__", "") or "").resolve() == path:
        return mod
    loader_spec = importlib.util.spec_from_file_location(spec.module, path)
    mod = importlib.util.module_from_spec(loader_spec)
    sys.modules[spec.module] = mod
    try:
        loader_spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop(spec.module, None)
        raise
    return mod


def _module_main(cmd: str):
    spec = COMMANDS[cmd]
    if spec.script:
        module = _load_script(cmd, spec)
        fn = getattr(module, "main", None)
        if not callable(fn):
            raise SystemExit(f"p2 {cmd}: script {spec.script} has no main(argv)")
        return fn
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
        where = spec.script or spec.module
        s = sub.add_parser(cmd, add_help=False, help=f"{spec.help} [{where}, {spec.task}]")
        s.add_argument("args", nargs=argparse.REMAINDER)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv: List[str] = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in COMMANDS:  # forward verbatim, including -h/--help, to the module
        cmd, rest = argv[0], argv[1:]
    else:
        a = _parser().parse_args(argv)  # prints usage and exits for --help, unknown or missing commands
        cmd, rest = a.cmd, a.args
    rc = _module_main(cmd)(rest)
    return 0 if rc is None else int(rc)
