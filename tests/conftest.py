from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def sandbox(monkeypatch, tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("HAS_CONFIG", str(tmp_path / "cfg" / "config.json"))
    monkeypatch.setenv("LOCALAPPDATA", str(home / "AppData" / "Local"))
    return home


@pytest.fixture
def write_json():
    def _write(path: Path, data: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    return _write
