"""Tests for stackpulse.sort_engine and stackpulse.cli_sort."""

from __future__ import annotations

import argparse
from typing import List

import pytest

from stackpulse.metrics_formatter import FormattedMetrics
from stackpulse.sort_engine import (
    SortCriteria,
    SortField,
    SortOrder,
    sort_metrics,
)
from stackpulse.cli_sort import attach_sort_args, criteria_from_args


def _make_metric(
    name: str,
    cpu: str = "10.0%",
    mem: str = "20.0%",
    status: str = "running",
    health: str = "healthy",
) -> FormattedMetrics:
    return FormattedMetrics(
        service_name=name,
        status=status,
        health=health,
        cpu_percent=cpu,
        mem_usage="128 MiB",
        mem_limit="512 MiB",
        mem_percent=mem,
        net_io="1 KiB / 2 KiB",
        block_io="0 B / 0 B",
        sparkline="▄▄▄",
    )


SAMPLE: List[FormattedMetrics] = [
    _make_metric("web", cpu="50.0%", mem="30.0%", health="unhealthy"),
    _make_metric("db", cpu="5.0%", mem="80.0%", health="healthy"),
    _make_metric("cache", cpu="20.0%", mem="10.0%", health="starting"),
]


def test_default_sort_by_name_asc():
    result = sort_metrics(SAMPLE)
    assert [m.service_name for m in result] == ["cache", "db", "web"]


def test_sort_by_name_desc():
    criteria = SortCriteria(field=SortField.NAME, order=SortOrder.DESC)
    result = sort_metrics(SAMPLE, criteria)
    assert [m.service_name for m in result] == ["web", "db", "cache"]


def test_sort_by_cpu_asc():
    criteria = SortCriteria(field=SortField.CPU, order=SortOrder.ASC)
    result = sort_metrics(SAMPLE, criteria)
    assert result[0].service_name == "db"   # 5 %
    assert result[-1].service_name == "web"  # 50 %


def test_sort_by_cpu_desc():
    criteria = SortCriteria(field=SortField.CPU, order=SortOrder.DESC)
    result = sort_metrics(SAMPLE, criteria)
    assert result[0].service_name == "web"


def test_sort_by_memory_asc():
    criteria = SortCriteria(field=SortField.MEMORY, order=SortOrder.ASC)
    result = sort_metrics(SAMPLE, criteria)
    assert result[0].service_name == "cache"  # 10 %
    assert result[-1].service_name == "db"    # 80 %


def test_sort_by_health():
    criteria = SortCriteria(field=SortField.HEALTH, order=SortOrder.ASC)
    result = sort_metrics(SAMPLE, criteria)
    assert result[0].service_name == "db"    # healthy -> rank 0
    assert result[-1].service_name == "web"  # unhealthy -> rank 2


def test_sort_by_status():
    mixed = [
        _make_metric("a", status="exited"),
        _make_metric("b", status="running"),
        _make_metric("c", status="paused"),
    ]
    criteria = SortCriteria(field=SortField.STATUS, order=SortOrder.ASC)
    result = sort_metrics(mixed, criteria)
    assert [m.service_name for m in result] == ["b", "c", "a"]


def test_sort_empty_list():
    assert sort_metrics([]) == []


def test_sort_does_not_mutate_original():
    original = list(SAMPLE)
    sort_metrics(SAMPLE, SortCriteria(field=SortField.CPU))
    assert SAMPLE == original


def test_is_default_true():
    assert SortCriteria().is_default() is True


def test_is_default_false():
    assert SortCriteria(field=SortField.CPU).is_default() is False


# --- cli_sort tests ---

def _parse(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    attach_sort_args(parser)
    return parser.parse_args(args)


def test_criteria_from_args_defaults_returns_none():
    ns = _parse([])
    assert criteria_from_args(ns) is None


def test_criteria_from_args_custom_field():
    ns = _parse(["--sort-by", "cpu"])
    criteria = criteria_from_args(ns)
    assert criteria is not None
    assert criteria.field == SortField.CPU
    assert criteria.order == SortOrder.ASC


def test_criteria_from_args_custom_order():
    ns = _parse(["--sort-by", "memory", "--sort-order", "desc"])
    criteria = criteria_from_args(ns)
    assert criteria is not None
    assert criteria.field == SortField.MEMORY
    assert criteria.order == SortOrder.DESC
