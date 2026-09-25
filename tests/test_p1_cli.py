from __future__ import annotations

import pytest

from derive_surface import p1cli
from derive_surface.__main__ import main


def test_to_ms_assumes_utc():
    assert p1cli.to_ms("2026-09-17T12:00:00") == 1_789_646_400_000
    assert p1cli.to_ms("2026-09-17T14:00:00+02:00") == 1_789_646_400_000
    assert p1cli.to_ms("2026-09-17T12:00:00Z") == 1_789_646_400_000


def test_p1_is_routed_and_help_exits_cleanly(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["p1", "--help"])
    assert exc.value.code == 0
    assert "volfeed" in capsys.readouterr().out


def test_markouts_command_is_listed(capsys):
    with pytest.raises(SystemExit):
        main(["p1", "--help"])
    assert "markouts" in capsys.readouterr().out


def test_inference_command_is_listed(capsys):
    with pytest.raises(SystemExit):
        main(["p1", "--help"])
    assert "inference" in capsys.readouterr().out


def test_existing_cli_still_parses():
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_every_subcommand_reaches_its_own_handler(monkeypatch, tmp_path, capsys):
    """A mis-nested branch once let `inference` import its module and then do nothing, silently and with exit 0."""
    from derive_surface import p1cli

    calls = []
    monkeypatch.setattr("derive_surface.inference_p1.run_all",
                        lambda *a, **k: calls.append("inference") or {"ok": True})
    monkeypatch.setattr("derive_surface.figures_p1.build",
                        lambda *a, **k: calls.append("figures") or {"T1": [tmp_path / "t1.pdf"]})
    p1cli.main(["--root", str(tmp_path), "inference", "--results", str(tmp_path)])
    p1cli.main(["--root", str(tmp_path), "figures", "--results", str(tmp_path), "--out", str(tmp_path)])
    assert calls == ["inference", "figures"]


def test_cards_command_draws_the_social_cards(monkeypatch, tmp_path):
    from derive_surface import p1cli

    calls = []
    monkeypatch.setattr("derive_surface.figures_social.build",
                        lambda *a, **k: calls.append((a, k)) or {"S1": [tmp_path / "s1.png"]})
    p1cli.main(["--root", str(tmp_path), "cards", "--results", str(tmp_path), "--out", str(tmp_path),
                "--only", "S1,S5"])
    assert len(calls) == 1 and calls[0][1]["only"] == ["S1", "S5"]
