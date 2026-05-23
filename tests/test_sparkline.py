"""Tests for stackpulse.sparkline."""

import pytest

from stackpulse.sparkline import (
    render_sparkline,
    render_percentage_sparkline,
    _BLOCKS,
    _NUM_LEVELS,
)


def test_empty_series_returns_empty_string():
    assert render_sparkline([]) == ""


def test_output_length_equals_width():
    series = [10.0, 20.0, 30.0, 40.0, 50.0]
    result = render_sparkline(series, width=10)
    assert len(result) == 10


def test_output_length_when_series_longer_than_width():
    series = list(range(50))
    result = render_sparkline(series, width=20)
    assert len(result) == 20


def test_only_last_n_samples_used():
    """The rightmost character should reflect the last value in the series."""
    series = [0.0] * 10 + [100.0]
    result = render_sparkline(series, width=5, min_val=0.0, max_val=100.0)
    # Last char must be the highest block.
    assert result[-1] == _BLOCKS[_NUM_LEVELS]


def test_flat_line_uses_mid_level_block():
    series = [42.0, 42.0, 42.0]
    result = render_sparkline(series, width=3)
    expected_char = _BLOCKS[_NUM_LEVELS // 2]
    assert all(c == expected_char for c in result.strip())


def test_padding_added_for_short_series():
    series = [1.0, 2.0]
    result = render_sparkline(series, width=5)
    assert len(result) == 5
    assert result.startswith("   ")  # 3 spaces of padding


def test_min_value_maps_to_lowest_block():
    series = [0.0, 50.0, 100.0]
    result = render_sparkline(series, width=3, min_val=0.0, max_val=100.0)
    assert result[0] == _BLOCKS[0]


def test_max_value_maps_to_highest_block():
    series = [0.0, 50.0, 100.0]
    result = render_sparkline(series, width=3, min_val=0.0, max_val=100.0)
    assert result[-1] == _BLOCKS[_NUM_LEVELS]


def test_render_percentage_sparkline_length():
    series = [10.0, 20.0, 80.0, 95.0]
    result = render_percentage_sparkline(series, width=15)
    assert len(result) == 15


def test_render_percentage_sparkline_max_clamp():
    """Values at 100 % should render as the highest block."""
    series = [100.0]
    result = render_percentage_sparkline(series, width=1)
    assert result == _BLOCKS[_NUM_LEVELS]


def test_render_percentage_sparkline_min_clamp():
    """Values at 0 % should render as the lowest (space) block."""
    series = [0.0]
    result = render_percentage_sparkline(series, width=1)
    assert result == _BLOCKS[0]
