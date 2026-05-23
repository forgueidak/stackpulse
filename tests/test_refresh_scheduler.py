"""Tests for stackpulse.refresh_scheduler."""

from __future__ import annotations

import pytest

from stackpulse.refresh_scheduler import (
    RefreshScheduler,
    _MIN_INTERVAL,
    _MAX_INTERVAL,
    _DEFAULT_INTERVAL,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeClock:
    """Controllable monotonic clock for deterministic tests."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _scheduler(interval: float = 2.0, start: float = 0.0) -> tuple[RefreshScheduler, FakeClock]:
    clock = FakeClock(start)
    sched = RefreshScheduler(interval=interval)
    sched._inject_clock(clock)
    return sched, clock


# ---------------------------------------------------------------------------
# Interval clamping
# ---------------------------------------------------------------------------

def test_default_interval():
    sched = RefreshScheduler()
    assert sched.interval == _DEFAULT_INTERVAL


def test_interval_clamped_to_minimum():
    sched = RefreshScheduler(interval=0.1)
    assert sched.interval == _MIN_INTERVAL


def test_interval_clamped_to_maximum():
    sched = RefreshScheduler(interval=999.0)
    assert sched.interval == _MAX_INTERVAL


def test_set_interval_updates_value():
    sched, _ = _scheduler(interval=2.0)
    sched.set_interval(5.0)
    assert sched.interval == 5.0


def test_set_interval_clamps_below_minimum():
    sched, _ = _scheduler()
    sched.set_interval(0.0)
    assert sched.interval == _MIN_INTERVAL


# ---------------------------------------------------------------------------
# is_due / acknowledge
# ---------------------------------------------------------------------------

def test_not_due_before_interval_elapsed():
    sched, clock = _scheduler(interval=2.0)
    clock.advance(1.9)
    assert sched.is_due() is False


def test_due_when_interval_elapsed():
    sched, clock = _scheduler(interval=2.0)
    clock.advance(2.0)
    assert sched.is_due() is True


def test_not_due_immediately_after_acknowledge():
    sched, clock = _scheduler(interval=2.0)
    clock.advance(3.0)
    assert sched.is_due() is True
    sched.acknowledge()
    assert sched.is_due() is False


def test_tick_count_increments_on_acknowledge():
    sched, clock = _scheduler()
    assert sched.tick_count == 0
    clock.advance(5.0)
    sched.acknowledge()
    sched.acknowledge()
    assert sched.tick_count == 2


# ---------------------------------------------------------------------------
# seconds_until_next
# ---------------------------------------------------------------------------

def test_seconds_until_next_positive_before_due():
    sched, clock = _scheduler(interval=4.0)
    clock.advance(1.0)
    remaining = sched.seconds_until_next()
    assert abs(remaining - 3.0) < 1e-9


def test_seconds_until_next_zero_when_overdue():
    sched, clock = _scheduler(interval=2.0)
    clock.advance(10.0)
    assert sched.seconds_until_next() == 0.0
