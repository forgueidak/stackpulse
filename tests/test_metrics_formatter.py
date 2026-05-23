"""Tests for stackpulse.metrics_formatter."""

from __future__ import annotations

import pytest

from stackpulse.docker_client import ServiceStats
from stackpulse.metrics_formatter import (
    _bytes_to_human,
    _health_icon,
    format_all,
    format_service_metrics,
)


def _make_stats(**overrides) -> ServiceStats:
    defaults = dict(
        name="web",
        container_id="abc123",
        status="running",
        health="healthy",
        cpu_percent=12.5,
        memory_usage=52_428_800,   # 50 MiB
        memory_limit=536_870_912,  # 512 MiB
        net_rx=1_048_576,          # 1 MiB
        net_tx=2_097_152,          # 2 MiB
        block_read=4_194_304,      # 4 MiB
        block_write=8_388_608,     # 8 MiB
    )
    defaults.update(overrides)
    return ServiceStats(**defaults)


class TestBytesToHuman:
    def test_bytes(self):
        assert "B" in _bytes_to_human(512)

    def test_kibibytes(self):
        assert "KiB" in _bytes_to_human(2048)

    def test_mebibytes(self):
        result = _bytes_to_human(52_428_800)
        assert "MiB" in result
        assert "50.00" in result

    def test_gibibytes(self):
        assert "GiB" in _bytes_to_human(2 * 1024 ** 3)


class TestHealthIcon:
    @pytest.mark.parametrize("health,icon", [
        ("healthy", "✅"),
        ("unhealthy", "❌"),
        ("starting", "⏳"),
        ("none", "—"),
    ])
    def test_known_states(self, health, icon):
        assert _health_icon(health) == icon

    def test_unknown_state(self):
        assert _health_icon("weird") == "❓"


class TestFormatServiceMetrics:
    def test_cpu_formatted(self):
        result = format_service_metrics(_make_stats(cpu_percent=7.3))
        assert result["cpu"] == "7.3%"

    def test_cpu_none(self):
        result = format_service_metrics(_make_stats(cpu_percent=None))
        assert result["cpu"] == "N/A"

    def test_memory_percent_calculated(self):
        stats = _make_stats(memory_usage=268_435_456, memory_limit=536_870_912)
        result = format_service_metrics(stats)
        assert result["memory_percent"] == "50.0%"

    def test_memory_none(self):
        result = format_service_metrics(_make_stats(memory_usage=None, memory_limit=None))
        assert result["memory"] == "N/A"
        assert result["memory_percent"] == "N/A"

    def test_net_io_format(self):
        result = format_service_metrics(_make_stats())
        assert "/" in result["net_io"]

    def test_health_icon_in_output(self):
        result = format_service_metrics(_make_stats(health="healthy"))
        assert "✅" in result["health"]

    def test_running_status_tag(self):
        result = format_service_metrics(_make_stats(status="running"))
        assert "green" in result["status"]

    def test_exited_status_tag(self):
        result = format_service_metrics(_make_stats(status="exited"))
        assert "red" in result["status"]


class TestFormatAll:
    def test_sorted_by_name(self):
        services = [
            _make_stats(name="zebra"),
            _make_stats(name="alpha"),
            _make_stats(name="middle"),
        ]
        result = format_all(services)
        assert [r["name"] for r in result] == ["alpha", "middle", "zebra"]

    def test_returns_all_entries(self):
        services = [_make_stats(name=f"svc{i}") for i in range(5)]
        assert len(format_all(services)) == 5
