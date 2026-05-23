"""Tests for stackpulse.history_buffer."""

import time
from unittest.mock import MagicMock

import pytest

from stackpulse.docker_client import ServiceStats
from stackpulse.history_buffer import HistoryBuffer, MetricPoint, ServiceHistory


def _make_stats(name: str, cpu: float = 10.0, mem: float = 20.0) -> ServiceStats:
    s = MagicMock(spec=ServiceStats)
    s.service_name = name
    s.cpu_percent = cpu
    s.mem_percent = mem
    return s


class TestServiceHistory:
    def test_add_single_point(self):
        h = ServiceHistory(service_name="web", max_samples=5)
        h.add(MetricPoint(timestamp=1.0, cpu_percent=5.0, mem_percent=10.0))
        assert len(h.points) == 1

    def test_evicts_oldest_when_full(self):
        h = ServiceHistory(service_name="web", max_samples=3)
        for i in range(4):
            h.add(MetricPoint(timestamp=float(i), cpu_percent=float(i), mem_percent=0.0))
        assert len(h.points) == 3
        assert h.points[0].cpu_percent == 1.0  # oldest evicted

    def test_cpu_series_order(self):
        h = ServiceHistory(service_name="web", max_samples=10)
        values = [1.0, 2.0, 3.0]
        for v in values:
            h.add(MetricPoint(timestamp=v, cpu_percent=v, mem_percent=0.0))
        assert h.cpu_series() == values

    def test_mem_series_order(self):
        h = ServiceHistory(service_name="web", max_samples=10)
        for v in [10.0, 20.0, 30.0]:
            h.add(MetricPoint(timestamp=v, cpu_percent=0.0, mem_percent=v))
        assert h.mem_series() == [10.0, 20.0, 30.0]

    def test_latest_returns_most_recent(self):
        h = ServiceHistory(service_name="web", max_samples=5)
        h.add(MetricPoint(timestamp=1.0, cpu_percent=1.0, mem_percent=1.0))
        h.add(MetricPoint(timestamp=2.0, cpu_percent=9.0, mem_percent=9.0))
        assert h.latest().cpu_percent == 9.0

    def test_latest_returns_none_when_empty(self):
        h = ServiceHistory(service_name="web")
        assert h.latest() is None


class TestHistoryBuffer:
    def test_record_creates_history_entry(self):
        buf = HistoryBuffer()
        buf.record(_make_stats("api", cpu=5.0, mem=15.0), timestamp=1.0)
        assert "api" in buf.all_services()

    def test_record_multiple_services(self):
        buf = HistoryBuffer()
        buf.record(_make_stats("api"), timestamp=1.0)
        buf.record(_make_stats("db"), timestamp=1.0)
        assert set(buf.all_services()) == {"api", "db"}

    def test_get_returns_service_history(self):
        buf = HistoryBuffer()
        buf.record(_make_stats("web", cpu=42.0), timestamp=1.0)
        history = buf.get("web")
        assert history is not None
        assert history.latest().cpu_percent == 42.0

    def test_get_returns_none_for_unknown_service(self):
        buf = HistoryBuffer()
        assert buf.get("unknown") is None

    def test_record_respects_max_samples(self):
        buf = HistoryBuffer(max_samples=3)
        for i in range(5):
            buf.record(_make_stats("svc", cpu=float(i)), timestamp=float(i))
        assert len(buf.get("svc").points) == 3

    def test_clear_removes_service(self):
        buf = HistoryBuffer()
        buf.record(_make_stats("tmp"), timestamp=1.0)
        buf.clear("tmp")
        assert buf.get("tmp") is None

    def test_clear_nonexistent_service_is_safe(self):
        buf = HistoryBuffer()
        buf.clear("ghost")  # should not raise
