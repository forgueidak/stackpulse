"""Tests for stackpulse.cli_pin."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from stackpulse.cli_pin import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(tmp_path: Path, *args: str) -> tuple[int, str]:
    pin_file = tmp_path / "pinned.json"
    argv = ["--pin-file", str(pin_file), *args]
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(argv)
    return rc, buf.getvalue()


# ---------------------------------------------------------------------------
# pin sub-command
# ---------------------------------------------------------------------------

def test_pin_command_exits_zero(tmp_path):
    rc, _ = _run(tmp_path, "pin", "web")
    assert rc == 0


def test_pin_command_persists(tmp_path):
    _run(tmp_path, "pin", "web", "db")
    data = json.loads((tmp_path / "pinned.json").read_text())
    assert "web" in data["pinned"]
    assert "db" in data["pinned"]


def test_pin_command_output_mentions_service(tmp_path):
    _, out = _run(tmp_path, "pin", "redis")
    assert "redis" in out


# ---------------------------------------------------------------------------
# unpin sub-command
# ---------------------------------------------------------------------------

def test_unpin_removes_pinned_service(tmp_path):
    _run(tmp_path, "pin", "web")
    _run(tmp_path, "unpin", "web")
    data = json.loads((tmp_path / "pinned.json").read_text())
    assert "web" not in data["pinned"]


# ---------------------------------------------------------------------------
# toggle sub-command
# ---------------------------------------------------------------------------

def test_toggle_pins_service(tmp_path):
    _, out = _run(tmp_path, "toggle", "api")
    assert "pinned" in out


def test_toggle_unpins_already_pinned(tmp_path):
    _run(tmp_path, "pin", "api")
    _, out = _run(tmp_path, "toggle", "api")
    assert "unpinned" in out


# ---------------------------------------------------------------------------
# list sub-command
# ---------------------------------------------------------------------------

def test_list_shows_pinned_services(tmp_path):
    _run(tmp_path, "pin", "svc-a", "svc-b")
    _, out = _run(tmp_path, "list")
    assert "svc-a" in out
    assert "svc-b" in out


def test_list_empty_shows_message(tmp_path):
    _, out = _run(tmp_path, "list")
    assert "no pinned" in out


# ---------------------------------------------------------------------------
# clear sub-command
# ---------------------------------------------------------------------------

def test_clear_removes_all(tmp_path):
    _run(tmp_path, "pin", "x", "y")
    rc, out = _run(tmp_path, "clear")
    assert rc == 0
    assert "cleared" in out
    data = json.loads((tmp_path / "pinned.json").read_text())
    assert data["pinned"] == []
