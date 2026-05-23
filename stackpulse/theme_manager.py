"""Theme manager for stackpulse terminal dashboard.

Provides named colour/style themes that can be applied to the layout
and metrics display.  Each theme is a simple dataclass so it can be
serialised to / from JSON for persistence.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Optional

_DEFAULT_THEME_NAME = "default"


@dataclass
class Theme:
    name: str
    # Rich markup colour names / hex strings
    healthy_color: str = "green"
    warning_color: str = "yellow"
    critical_color: str = "red"
    unknown_color: str = "dim white"
    header_color: str = "bold cyan"
    border_style: str = "blue"
    sparkline_color: str = "cyan"
    pinned_color: str = "bold magenta"


_BUILTIN_THEMES: Dict[str, Theme] = {
    "default": Theme(name="default"),
    "dark": Theme(
        name="dark",
        healthy_color="bright_green",
        warning_color="dark_orange",
        critical_color="bright_red",
        unknown_color="grey50",
        header_color="bold bright_cyan",
        border_style="grey42",
        sparkline_color="bright_cyan",
        pinned_color="bold bright_magenta",
    ),
    "light": Theme(
        name="light",
        healthy_color="dark_green",
        warning_color="orange3",
        critical_color="dark_red",
        unknown_color="grey46",
        header_color="bold blue",
        border_style="black",
        sparkline_color="blue",
        pinned_color="bold purple",
    ),
}


class ThemeManager:
    """Loads, stores and switches between named themes."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._themes: Dict[str, Theme] = dict(_BUILTIN_THEMES)
        self._active_name: str = _DEFAULT_THEME_NAME
        self._config_path = config_path or _default_config_path()
        self._load_from_disk()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def active(self) -> Theme:
        return self._themes[self._active_name]

    @property
    def available(self) -> list[str]:
        return sorted(self._themes.keys())

    def set_theme(self, name: str) -> None:
        if name not in self._themes:
            raise ValueError(f"Unknown theme {name!r}. Available: {self.available}")
        self._active_name = name
        self._save_to_disk()

    def register(self, theme: Theme) -> None:
        """Register a custom theme (overwrites built-ins with same name)."""
        self._themes[theme.name] = theme

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_from_disk(self) -> None:
        if not self._config_path.exists():
            return
        try:
            data = json.loads(self._config_path.read_text())
            self._active_name = data.get("active_theme", _DEFAULT_THEME_NAME)
            for raw in data.get("custom_themes", []):
                self._themes[raw["name"]] = Theme(**raw)
        except Exception:
            pass  # corrupt config — silently fall back to defaults

    def _save_to_disk(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        custom = [
            asdict(t)
            for t in self._themes.values()
            if t.name not in _BUILTIN_THEMES
        ]
        payload = {"active_theme": self._active_name, "custom_themes": custom}
        self._config_path.write_text(json.dumps(payload, indent=2))


def _default_config_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "stackpulse" / "theme.json"
