"""Tests for stackpulse.theme_manager."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from stackpulse.theme_manager import Theme, ThemeManager, _BUILTIN_THEMES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _manager(tmp_path: Path) -> ThemeManager:
    """Return a ThemeManager backed by a temp directory."""
    return ThemeManager(config_path=tmp_path / "theme.json")


# ---------------------------------------------------------------------------
# Builtin themes
# ---------------------------------------------------------------------------


def test_default_active_theme(tmp_path):
    mgr = _manager(tmp_path)
    assert mgr.active.name == "default"


def test_available_includes_builtins(tmp_path):
    mgr = _manager(tmp_path)
    for name in _BUILTIN_THEMES:
        assert name in mgr.available


def test_available_is_sorted(tmp_path):
    mgr = _manager(tmp_path)
    assert mgr.available == sorted(mgr.available)


# ---------------------------------------------------------------------------
# set_theme
# ---------------------------------------------------------------------------


def test_set_theme_changes_active(tmp_path):
    mgr = _manager(tmp_path)
    mgr.set_theme("dark")
    assert mgr.active.name == "dark"
    assert mgr.active.border_style == "grey42"


def test_set_unknown_theme_raises(tmp_path):
    mgr = _manager(tmp_path)
    with pytest.raises(ValueError, match="Unknown theme"):
        mgr.set_theme("nonexistent_theme")


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------


def test_register_custom_theme(tmp_path):
    mgr = _manager(tmp_path)
    custom = Theme(name="solarized", healthy_color="#859900")
    mgr.register(custom)
    assert "solarized" in mgr.available
    mgr.set_theme("solarized")
    assert mgr.active.healthy_color == "#859900"


def test_register_overwrites_existing(tmp_path):
    mgr = _manager(tmp_path)
    replacement = Theme(name="dark", healthy_color="#00ff00")
    mgr.register(replacement)
    mgr.set_theme("dark")
    assert mgr.active.healthy_color == "#00ff00"


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def test_active_theme_persisted_across_instances(tmp_path):
    cfg = tmp_path / "theme.json"
    mgr1 = ThemeManager(config_path=cfg)
    mgr1.set_theme("light")

    mgr2 = ThemeManager(config_path=cfg)
    assert mgr2.active.name == "light"


def test_custom_theme_persisted_across_instances(tmp_path):
    cfg = tmp_path / "theme.json"
    mgr1 = ThemeManager(config_path=cfg)
    custom = Theme(name="my_theme", sparkline_color="purple")
    mgr1.register(custom)
    mgr1.set_theme("my_theme")

    mgr2 = ThemeManager(config_path=cfg)
    assert "my_theme" in mgr2.available
    assert mgr2.active.name == "my_theme"
    assert mgr2.active.sparkline_color == "purple"


def test_corrupt_config_falls_back_to_default(tmp_path):
    cfg = tmp_path / "theme.json"
    cfg.write_text("{invalid json")
    mgr = ThemeManager(config_path=cfg)
    assert mgr.active.name == "default"


def test_missing_config_uses_default(tmp_path):
    cfg = tmp_path / "no_such_file.json"
    mgr = ThemeManager(config_path=cfg)
    assert mgr.active.name == "default"


def test_save_creates_parent_directories(tmp_path):
    cfg = tmp_path / "nested" / "dir" / "theme.json"
    mgr = ThemeManager(config_path=cfg)
    mgr.set_theme("dark")
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert data["active_theme"] == "dark"
