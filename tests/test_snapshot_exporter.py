"""Tests for stackpulse.snapshot_exporter."""

from __future__ import annotations

import csv
import io
import json

import pytest

from stackpulse.metrics_formatter import FormattedMetrics
from stackpulse.snapshot_exporter import export_snapshot


def _make_formatted(
    service: str = "web",
    status: str = "running",
    health: str = "healthy",
    cpu_pct: str = "12.3%",
    mem_usage: str = "128 MiB",
    mem_limit: str = "512 MiB",
    mem_pct: str = "25.0%",
    net_rx: str = "1.2 MiB",
    net_tx: str = "0.5 MiB",
    pids: int = 4,
) -> FormattedMetrics:
    return FormattedMetrics(
        service=service,
        status=status,
        health=health,
        cpu_pct=cpu_pct,
        mem_usage=mem_usage,
        mem_limit=mem_limit,
        mem_pct=mem_pct,
        net_rx=net_rx,
        net_tx=net_tx,
        pids=pids,
    )


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

class TestJsonExport:
    def test_returns_valid_json(self):
        result = export_snapshot([_make_formatted()], fmt="json")
        parsed = json.loads(result)  # must not raise
        assert isinstance(parsed, dict)

    def test_contains_exported_at(self):
        parsed = json.loads(export_snapshot([_make_formatted()], fmt="json"))
        assert "exported_at" in parsed

    def test_service_count_matches(self):
        metrics = [_make_formatted("web"), _make_formatted("db")]
        parsed = json.loads(export_snapshot(metrics, fmt="json"))
        assert len(parsed["services"]) == 2

    def test_service_fields_present(self):
        parsed = json.loads(export_snapshot([_make_formatted()], fmt="json"))
        svc = parsed["services"][0]
        for key in ("service", "status", "health", "cpu_pct", "mem_usage",
                    "mem_limit", "mem_pct", "net_rx", "net_tx", "pids"):
            assert key in svc

    def test_service_name_value(self):
        parsed = json.loads(export_snapshot([_make_formatted("redis")], fmt="json"))
        assert parsed["services"][0]["service"] == "redis"

    def test_empty_metrics_gives_empty_list(self):
        parsed = json.loads(export_snapshot([], fmt="json"))
        assert parsed["services"] == []


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

class TestCsvExport:
    def test_returns_valid_csv(self):
        result = export_snapshot([_make_formatted()], fmt="csv")
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 1

    def test_csv_has_header(self):
        result = export_snapshot([_make_formatted()], fmt="csv")
        assert result.startswith("exported_at")

    def test_csv_service_name(self):
        result = export_snapshot([_make_formatted("nginx")], fmt="csv")
        reader = csv.DictReader(io.StringIO(result))
        row = next(reader)
        assert row["service"] == "nginx"

    def test_csv_row_count(self):
        metrics = [_make_formatted("a"), _make_formatted("b"), _make_formatted("c")]
        result = export_snapshot(metrics, fmt="csv")
        reader = csv.DictReader(io.StringIO(result))
        assert len(list(reader)) == 3

    def test_csv_empty_metrics(self):
        result = export_snapshot([], fmt="csv")
        reader = csv.DictReader(io.StringIO(result))
        assert list(reader) == []


# ---------------------------------------------------------------------------
# Invalid format
# ---------------------------------------------------------------------------

def test_invalid_format_raises():
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_snapshot([_make_formatted()], fmt="xml")  # type: ignore[arg-type]
