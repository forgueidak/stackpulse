"""Tests for stackpulse.filter_engine."""
from __future__ import annotations

import pytest

from stackpulse.filter_engine import FilterCriteria, apply_filter
from stackpulse.metrics_formatter import FormattedMetrics


def _make_metric(
    name: str = "svc",
    status: str = "running",
    health: str = "healthy",
    cpu: str = "10.0%",
) -> FormattedMetrics:
    return FormattedMetrics(
        service_name=name,
        status=status,
        health=health,
        cpu_percent=cpu,
        mem_usage="50 MiB",
        mem_limit="512 MiB",
        mem_percent="9.8%",
        net_io="1 KiB / 2 KiB",
        block_io="0 B / 0 B",
        sparkline="▄▄▄",
    )


SERVICES = [
    _make_metric("web", "running", "healthy", "5.0%"),
    _make_metric("db", "running", "unhealthy", "75.0%"),
    _make_metric("cache", "exited", "none", "0.0%"),
    _make_metric("worker", "running", "healthy", "45.0%"),
]


def test_empty_criteria_returns_all():
    result = apply_filter(SERVICES, FilterCriteria())
    assert len(result) == len(SERVICES)


def test_name_pattern_substring():
    result = apply_filter(SERVICES, FilterCriteria(name_pattern="web"))
    assert [m.service_name for m in result] == ["web"]


def test_name_pattern_regex():
    result = apply_filter(SERVICES, FilterCriteria(name_pattern="^(web|db)$"))
    assert {m.service_name for m in result} == {"web", "db"}


def test_name_pattern_case_insensitive():
    result = apply_filter(SERVICES, FilterCriteria(name_pattern="WEB"))
    assert result[0].service_name == "web"


def test_name_pattern_bad_regex_falls_back_to_substring():
    # "[unclosed" is an invalid regex; should not raise
    result = apply_filter(SERVICES, FilterCriteria(name_pattern="[unclosed"))
    assert result == []


def test_filter_by_status():
    result = apply_filter(SERVICES, FilterCriteria(statuses=["exited"]))
    assert [m.service_name for m in result] == ["cache"]


def test_filter_by_multiple_statuses():
    result = apply_filter(SERVICES, FilterCriteria(statuses=["running", "exited"]))
    assert len(result) == 4


def test_filter_by_health():
    result = apply_filter(SERVICES, FilterCriteria(health_states=["unhealthy"]))
    assert [m.service_name for m in result] == ["db"]


def test_filter_by_min_cpu():
    result = apply_filter(SERVICES, FilterCriteria(min_cpu=40.0))
    assert {m.service_name for m in result} == {"db", "worker"}


def test_filter_by_max_cpu():
    result = apply_filter(SERVICES, FilterCriteria(max_cpu=10.0))
    assert {m.service_name for m in result} == {"web", "cache"}


def test_filter_by_cpu_range():
    result = apply_filter(SERVICES, FilterCriteria(min_cpu=5.0, max_cpu=50.0))
    assert {m.service_name for m in result} == {"web", "worker"}


def test_combined_criteria():
    result = apply_filter(
        SERVICES,
        FilterCriteria(statuses=["running"], health_states=["healthy"], max_cpu=20.0),
    )
    assert [m.service_name for m in result] == ["web"]


def test_is_empty_true_for_default():
    assert FilterCriteria().is_empty is True


def test_is_empty_false_when_any_field_set():
    assert FilterCriteria(name_pattern="x").is_empty is False
    assert FilterCriteria(statuses=["running"]).is_empty is False
    assert FilterCriteria(min_cpu=1.0).is_empty is False
