from __future__ import annotations

import pytest

from derive_surface import p1cli
from derive_surface.__main__ import main


def test_to_ms_assumes_utc():
    assert p1cli.to_ms("2026-09-17T12:00:00") == 1_789_646_400_000
    assert p1cli.to_ms("2026-09-17T14:00:00+02:00") == 1_789_646_400_000


def test_p1_is_routed_and_help_exits_cleanly(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["p1", "--help"])
    assert exc.value.code == 0
    assert "volfeed" in capsys.readouterr().out


def test_existing_cli_still_parses():
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
