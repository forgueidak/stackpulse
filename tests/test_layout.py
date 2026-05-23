"""Tests for stackpulse.layout."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table

from stackpulse.alert_manager import AlertManager
from stackpulse.alert_rules import Alert, Severity
from stackpulse.history_buffer import ServiceHistory
from stackpulse.layout import (
    _build_alerts_panel,
    _build_services_table,
    build_layout,
    render_to_console,
)
from stackpulse.metrics_formatter import FormattedMetrics


def _make_formatted(name: str = "web") -> FormattedMetrics:
    return FormattedMetrics(
        service_name=name,
        status="[green]running[/green]",
        health="✅",
        cpu_percent="12.3%",
        mem_usage="128 MiB / 512 MiB",
        mem_percent="25.0%",
        net_io="1.2 MiB / 500 KiB",
        block_io="0 B / 0 B",
    )


def _make_alert_manager(with_alert: bool = False) -> AlertManager:
    am = AlertManager()
    if with_alert:
        alert = Alert(
            service_name="web",
            rule_name="high_cpu",
            severity=Severity.WARNING,
            message="CPU above 80%",
            value=85.0,
        )
        am.process([alert])
    return am


class TestBuildServicesTable:
    def test_returns_table(self):
        table = _build_services_table([_make_formatted()], {})
        assert isinstance(table, Table)

    def test_table_has_row_per_service(self):
        metrics = [_make_formatted("web"), _make_formatted("db")]
        table = _build_services_table(metrics, {})
        assert table.row_count == 2

    def test_uses_history_for_sparklines(self):
        history = ServiceHistory(service_name="web", maxlen=60)
        from stackpulse.docker_client import ServiceStats
        for i in range(5):
            history.add(ServiceStats(
                service_name="web", container_id="abc", status="running",
                health="healthy", cpu_percent=float(i * 10),
                mem_usage_bytes=1024 * 1024 * i, mem_limit_bytes=512 * 1024 * 1024,
                net_rx_bytes=0, net_tx_bytes=0, block_read_bytes=0, block_write_bytes=0,
            ))
        table = _build_services_table([_make_formatted("web")], {"web": history})
        assert table.row_count == 1


class TestBuildAlertsPanel:
    def test_no_alerts_shows_green_panel(self):
        am = _make_alert_manager(with_alert=False)
        panel = _build_alerts_panel(am)
        assert isinstance(panel, Panel)
        assert panel.border_style == "green"

    def test_active_alert_shows_red_panel(self):
        am = _make_alert_manager(with_alert=True)
        panel = _build_alerts_panel(am)
        assert panel.border_style == "red"


class TestBuildLayout:
    def test_returns_layout(self):
        am = _make_alert_manager()
        layout = build_layout([_make_formatted()], {}, am)
        assert isinstance(layout, Layout)

    def test_layout_has_services_and_alerts_sections(self):
        am = _make_alert_manager()
        layout = build_layout([_make_formatted()], {}, am)
        names = {child.name for child in layout.children}
        assert "services" in names
        assert "alerts" in names


def test_render_to_console_calls_print():
    console = MagicMock(spec=Console)
    am = _make_alert_manager()
    layout = build_layout([_make_formatted()], {}, am)
    render_to_console(console, layout)
    console.print.assert_called_once_with(layout)
