"""Refresh scheduler — controls the polling interval for live dashboard updates."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


_DEFAULT_INTERVAL: float = 2.0
_MIN_INTERVAL: float = 0.5
_MAX_INTERVAL: float = 60.0


@dataclass
class RefreshScheduler:
    """Tracks elapsed time and decides when the next data refresh is due."""

    interval: float = _DEFAULT_INTERVAL
    _last_tick: float = field(default_factory=time.monotonic, init=False, repr=False)
    _tick_count: int = field(default=0, init=False, repr=False)
    _clock: Callable[[], float] = field(default=time.monotonic, init=False, repr=False)

    def __post_init__(self) -> None:
        self.interval = _clamp(self.interval, _MIN_INTERVAL, _MAX_INTERVAL)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_due(self) -> bool:
        """Return True when at least *interval* seconds have elapsed since the
        last acknowledged tick."""
        return (self._clock() - self._last_tick) >= self.interval

    def acknowledge(self) -> None:
        """Mark the current moment as the start of the next interval."""
        self._last_tick = self._clock()
        self._tick_count += 1

    def set_interval(self, seconds: float) -> None:
        """Update the polling interval, clamped to allowed bounds."""
        self.interval = _clamp(seconds, _MIN_INTERVAL, _MAX_INTERVAL)

    @property
    def tick_count(self) -> int:
        """Total number of acknowledged ticks since creation."""
        return self._tick_count

    def seconds_until_next(self) -> float:
        """Seconds remaining until the next refresh is due (>= 0)."""
        elapsed = self._clock() - self._last_tick
        remaining = self.interval - elapsed
        return max(remaining, 0.0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _inject_clock(self, clock: Callable[[], float]) -> None:  # test helper
        """Replace the monotonic clock with a controllable callable (tests only)."""
        self._clock = clock
        self._last_tick = clock()


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
