"""Pin manager — allows users to pin/unpin services for persistent highlighting."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Set
import json

_DEFAULT_PIN_FILE = Path.home() / ".stackpulse" / "pinned.json"


@dataclass
class PinManager:
    """Tracks which service names are currently pinned."""

    _pinned: Set[str] = field(default_factory=set)
    _persist_path: Path | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def pinned(self) -> frozenset[str]:
        """Return an immutable snapshot of pinned service names."""
        return frozenset(self._pinned)

    def pin(self, service: str) -> None:
        """Pin *service*."""
        self._pinned.add(service)
        self._save()

    def unpin(self, service: str) -> None:
        """Unpin *service* (no-op if not pinned)."""
        self._pinned.discard(service)
        self._save()

    def toggle(self, service: str) -> bool:
        """Toggle pin state.  Returns *True* if the service is now pinned."""
        if service in self._pinned:
            self.unpin(service)
            return False
        self.pin(service)
        return True

    def is_pinned(self, service: str) -> bool:
        return service in self._pinned

    def clear(self) -> None:
        """Unpin all services."""
        self._pinned.clear()
        self._save()

    def sort_pinned_first(self, services: Iterable[str]) -> list[str]:
        """Return *services* sorted so pinned names come first."""
        lst = list(services)
        return sorted(lst, key=lambda s: (0 if s in self._pinned else 1, s))

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: Path = _DEFAULT_PIN_FILE) -> "PinManager":
        """Load pins from *path*, creating an empty manager if absent."""
        if path.exists():
            try:
                data = json.loads(path.read_text())
                pinned = set(data.get("pinned", []))
            except (json.JSONDecodeError, KeyError):
                pinned = set()
        else:
            pinned = set()
        return cls(_pinned=pinned, _persist_path=path)

    def _save(self) -> None:
        if self._persist_path is None:
            return
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._persist_path.write_text(
            json.dumps({"pinned": sorted(self._pinned)}, indent=2)
        )
