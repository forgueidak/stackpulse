"""Tests for stackpulse.pin_manager."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from stackpulse.pin_manager import PinManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _manager() -> PinManager:
    """Return a PinManager with no persistence."""
    return PinManager()


# ---------------------------------------------------------------------------
# Basic pin / unpin
# ---------------------------------------------------------------------------

def test_pin_adds_service():
    pm = _manager()
    pm.pin("web")
    assert pm.is_pinned("web")


def test_unpin_removes_service():
    pm = _manager()
    pm.pin("web")
    pm.unpin("web")
    assert not pm.is_pinned("web")


def test_unpin_nonexistent_is_noop():
    pm = _manager()
    pm.unpin("ghost")  # must not raise
    assert not pm.is_pinned("ghost")


def test_toggle_pins_unpinned_service():
    pm = _manager()
    result = pm.toggle("db")
    assert result is True
    assert pm.is_pinned("db")


def test_toggle_unpins_pinned_service():
    pm = _manager()
    pm.pin("db")
    result = pm.toggle("db")
    assert result is False
    assert not pm.is_pinned("db")


def test_clear_removes_all():
    pm = _manager()
    pm.pin("a")
    pm.pin("b")
    pm.clear()
    assert pm.pinned == frozenset()


def test_pinned_returns_frozenset():
    pm = _manager()
    pm.pin("x")
    assert isinstance(pm.pinned, frozenset)


# ---------------------------------------------------------------------------
# sort_pinned_first
# ---------------------------------------------------------------------------

def test_sort_pinned_first_puts_pinned_at_top():
    pm = _manager()
    pm.pin("redis")
    result = pm.sort_pinned_first(["web", "redis", "db"])
    assert result[0] == "redis"


def test_sort_pinned_first_stable_alpha_within_groups():
    pm = _manager()
    pm.pin("redis")
    pm.pin("api")
    result = pm.sort_pinned_first(["web", "redis", "db", "api"])
    assert result[:2] == ["api", "redis"]
    assert result[2:] == ["db", "web"]


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path: Path):
    pin_file = tmp_path / "pinned.json"
    pm = PinManager(_persist_path=pin_file)
    pm.pin("svc-a")
    pm.pin("svc-b")

    loaded = PinManager.load(pin_file)
    assert loaded.is_pinned("svc-a")
    assert loaded.is_pinned("svc-b")


def test_load_missing_file_returns_empty(tmp_path: Path):
    pm = PinManager.load(tmp_path / "nonexistent.json")
    assert pm.pinned == frozenset()


def test_load_corrupt_file_returns_empty(tmp_path: Path):
    pin_file = tmp_path / "pinned.json"
    pin_file.write_text("not json{{")
    pm = PinManager.load(pin_file)
    assert pm.pinned == frozenset()


def test_save_creates_parent_dirs(tmp_path: Path):
    pin_file = tmp_path / "deep" / "nested" / "pinned.json"
    pm = PinManager(_persist_path=pin_file)
    pm.pin("worker")
    assert pin_file.exists()
    data = json.loads(pin_file.read_text())
    assert "worker" in data["pinned"]
