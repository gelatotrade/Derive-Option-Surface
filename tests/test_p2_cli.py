from __future__ import annotations

import sys
import types

import pytest

from derive_surface import p2cli
from derive_surface.__main__ import main

COMMANDS = ["feeds", "params", "validate", "capital", "books", "events", "infer", "infer-h4", "numbers", "api",
            "figures", "surface"]


def _fake_modules(monkeypatch, calls, rc=0):
    for cmd, spec in p2cli.COMMANDS.items():
        name = spec.module if spec.script else f"derive_surface.{spec.module}"
        fake = types.ModuleType(name)
        fake.main = lambda argv, cmd=cmd: calls.append((cmd, list(argv))) or rc
        if spec.script:
            fake.__file__ = str(p2cli.REPO / spec.script)
        monkeypatch.setitem(sys.modules, name, fake)


def test_p2_is_routed_and_help_lists_every_command(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["p2", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for cmd in COMMANDS:
        assert cmd in out


def test_commands_map_to_the_modules_of_the_plan():
    assert {c: s.module for c, s in p2cli.COMMANDS.items()} == {
        "feeds": "p2feeds", "params": "p2params", "validate": "p2validate", "capital": "capital", "books": "books",
        "events": "p2events", "infer": "inference_p2", "infer-h4": "inference_p2_h4", "numbers": "p2_numbers",
        "api": "p2api", "figures": "figures_p2", "surface": "p2surface", "ids": "p2ids"}


def test_only_the_number_sheet_is_a_script_and_it_exists():
    scripts = {c: s.script for c, s in p2cli.COMMANDS.items() if s.script}
    assert scripts == {"numbers": "scripts/p2_numbers.py"}
    assert (p2cli.REPO / scripts["numbers"]).is_file()


def test_every_command_reaches_the_main_of_its_module(monkeypatch):
    calls = []
    _fake_modules(monkeypatch, calls)
    for cmd in p2cli.COMMANDS:
        assert p2cli.main([cmd, "run", "--flag", "1"]) == 0
    assert calls == [(cmd, ["run", "--flag", "1"]) for cmd in p2cli.COMMANDS]


def test_options_after_the_command_belong_to_the_module(monkeypatch):
    calls = []
    _fake_modules(monkeypatch, calls)
    p2cli.main(["params", "--help"])
    p2cli.main(["books", "-h", "--accounts", "all"])
    assert calls == [("params", ["--help"]), ("books", ["-h", "--accounts", "all"])]


def test_exit_code_of_the_module_reaches_python_m(monkeypatch):
    calls = []
    _fake_modules(monkeypatch, calls, rc=3)
    with pytest.raises(SystemExit) as exc:
        main(["p2", "params", "load"])
    assert exc.value.code == 3 and calls == [("params", ["load"])]


def test_none_from_a_module_main_is_success(monkeypatch):
    calls = []
    _fake_modules(monkeypatch, calls, rc=None)
    assert p2cli.main(["books", "top"]) == 0
    assert main(["p2", "books", "top"]) is None


def test_real_module_help_is_forwarded(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["p2", "params", "--help"])
    assert exc.value.code == 0
    assert "oi-share" in capsys.readouterr().out


@pytest.mark.parametrize("cmd,needle", [("infer", "sensitivity"), ("infer-h4", "run"), ("api", "report"),
                                        ("numbers", "NUMBERS.md")])
def test_new_commands_reach_the_real_modules(cmd, needle, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["p2", cmd, "--help"])
    assert exc.value.code == 0
    assert needle in capsys.readouterr().out


def test_script_is_loaded_as_a_module_once(monkeypatch):
    monkeypatch.delitem(sys.modules, "p2_numbers", raising=False)
    fn = p2cli._module_main("numbers")
    mod = sys.modules["p2_numbers"]
    assert fn is mod.main and mod.__file__ == str(p2cli.REPO / "scripts" / "p2_numbers.py")
    assert p2cli._module_main("numbers") is fn


def test_missing_script_gives_a_clear_error(monkeypatch):
    monkeypatch.setitem(p2cli.COMMANDS, "numbers",
                        p2cli.Command("_p2_no_such_script", "C1", "x", script="scripts/_p2_no_such_script.py"))
    with pytest.raises(SystemExit) as exc:
        p2cli.main(["numbers"])
    msg = str(exc.value.code)
    assert "scripts/_p2_no_such_script.py" in msg and "C1" in msg


def test_missing_module_gives_a_clear_error(monkeypatch):
    monkeypatch.setitem(p2cli.COMMANDS, "validate", p2cli.Command("_p2_no_such_module", "B1", "replica vs eth_call"))
    with pytest.raises(SystemExit) as exc:
        p2cli.main(["validate", "run"])
    msg = str(exc.value.code)
    assert "derive_surface._p2_no_such_module" in msg and "B1" in msg and "not implemented yet" in msg


def test_import_errors_inside_an_existing_module_are_not_masked(monkeypatch, tmp_path):
    import derive_surface

    (tmp_path / "_p2_broken_mod.py").write_text("import _p2_no_such_dependency_xyz\n\ndef main(argv):\n    return 0\n")
    monkeypatch.setattr(derive_surface, "__path__", list(derive_surface.__path__) + [str(tmp_path)])
    monkeypatch.setitem(p2cli.COMMANDS, "validate", p2cli.Command("_p2_broken_mod", "B1", "x"))
    with pytest.raises(ModuleNotFoundError) as exc:
        p2cli.main(["validate"])
    assert exc.value.name == "_p2_no_such_dependency_xyz"


def test_module_without_main_is_an_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "derive_surface._p2_no_main", types.ModuleType("derive_surface._p2_no_main"))
    monkeypatch.setitem(p2cli.COMMANDS, "validate", p2cli.Command("_p2_no_main", "B1", "x"))
    with pytest.raises(SystemExit) as exc:
        p2cli.main(["validate"])
    assert "main" in str(exc.value.code)


def test_unknown_or_missing_command_exits_with_usage(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["p2", "nope"])
    assert exc.value.code == 2
    with pytest.raises(SystemExit) as exc:
        main(["p2"])
    assert exc.value.code == 2


def test_p1_and_legacy_cli_still_parse():
    with pytest.raises(SystemExit) as exc:
        main(["p1", "--help"])
    assert exc.value.code == 0
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
