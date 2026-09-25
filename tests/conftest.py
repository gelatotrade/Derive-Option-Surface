from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _private_salt(tmp_path, monkeypatch):
    """Tests never create or read the real wallet salt under data/p1."""
    from derive_surface import inference_p1
    monkeypatch.setattr(inference_p1, "SALT_PATH", tmp_path / "secret_salt.txt")
