"""Utilities for rendering ASCII sparklines from metric time-series data."""

from __future__ import annotations

from typing import Sequence

# Block characters ordered from lowest to highest fill
_BLOCKS = " ▁▂▃▄▅▆▇█"
_NUM_LEVELS = len(_BLOCKS) - 1  # exclude the space (empty)


def render_sparkline(
    series: Sequence[float],
    width: int = 20,
    min_val: float | None = None,
    max_val: float | None = None,
) -> str:
    """Return a unicode sparkline string for *series*.

    Args:
        series: Sequence of numeric values (oldest → newest).
        width:  Number of characters in the output string.
        min_val: Override the minimum for scaling (defaults to series min).
        max_val: Override the maximum for scaling (defaults to series max).

    Returns:
        A string of *width* block characters representing the data trend.
        An empty string is returned when *series* is empty.
    """
    if not series:
        return ""

    # Take the last *width* samples so the line always scrolls right.
    samples = list(series[-width:])

    lo = min_val if min_val is not None else min(samples)
    hi = max_val if max_val is not None else max(samples)

    # Pad with spaces on the left if we have fewer points than width.
    padding = width - len(samples)

    if hi == lo:
        # Flat line — render at mid-level.
        bar = _BLOCKS[_NUM_LEVELS // 2] * len(samples)
        return " " * padding + bar

    span = hi - lo
    chars: list[str] = []
    for v in samples:
        normalised = (v - lo) / span  # 0.0 – 1.0
        index = round(normalised * _NUM_LEVELS)
        index = max(0, min(_NUM_LEVELS, index))
        chars.append(_BLOCKS[index])

    return " " * padding + "".join(chars)


def render_percentage_sparkline(series: Sequence[float], width: int = 20) -> str:
    """Convenience wrapper that fixes the scale to 0-100 % for CPU/memory."""
    return render_sparkline(series, width=width, min_val=0.0, max_val=100.0)
