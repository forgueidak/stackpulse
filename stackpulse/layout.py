"""Terminal layout builder for the StackPulse dashboard.

Builds a Rich-based layout that displays service health, resource usage,
sparklines, and active alerts in a structured terminal UI.
"""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from stackpulse.alert_manager import AlertManager
from stackpulse.history_buffer import ServiceHistory
from stackpulse.metrics_formatter import FormattedMetrics, format_service_metrics
from stackpulse.sparkline import render_percentage_sparkline

_SPARKLINE_WIDTH = 20


def _build_services_table(metrics_list: List[FormattedMetrics], histories: dict[str, ServiceHistory]) -> Table:
    table = Table(
        title="Services",
        expand=True,
        show_lines=False,
        header_style="bold cyan",
    )
    table.add_column("Service", min_width=18)
    table.add_column("Status", justify="center", min_width=10)
    table.add_column("Health", justify="center", min_width=8)
    table.add_column("CPU %", justify="right", min_width=8)
    table.add_column("CPU Trend", min_width=_SPARKLINE_WIDTH + 2)
    table.add_column("Mem Usage", justify="right", min_width=12)
    table.add_column("Mem Trend", min_width=_SPARKLINE_WIDTH + 2)
    table.add_column("Net I/O", justify="right", min_width=14)
    table.add_column("Block I/O", justify="right", min_width=14)

    for m in metrics_list:
        history = histories.get(m.service_name)
        cpu_spark = (
            render_percentage_sparkline(history.cpu_series(), width=_SPARKLINE_WIDTH)
            if history else ""
        )
        mem_spark = (
            render_percentage_sparkline(history.mem_series(), width=_SPARKLINE_WIDTH)
            if history else ""
        )

        table.add_row(
            m.service_name,
            Text.from_markup(m.status),
            m.health,
            m.cpu_percent,
            cpu_spark,
            m.mem_usage,
            mem_spark,
            m.net_io,
            m.block_io,
        )

    return table


def _build_alerts_panel(alert_manager: AlertManager) -> Panel:
    alerts = alert_manager.active_alerts()
    if not alerts:
        body = Text("No active alerts", style="dim green")
    else:
        body = Text()
        for alert in alerts:
            style = "bold red" if alert.severity.value == "critical" else "bold yellow"
            body.append(f"[{alert.severity.value.upper()}] ", style=style)
            body.append(f"{alert.service_name}: {alert.message}\n")
    return Panel(body, title="Alerts", border_style="red" if alerts else "green")


def build_layout(
    metrics_list: List[FormattedMetrics],
    histories: dict[str, ServiceHistory],
    alert_manager: AlertManager,
) -> Layout:
    """Compose the full dashboard layout."""
    root = Layout(name="root")
    root.split_column(
        Layout(name="services", ratio=4),
        Layout(name="alerts", ratio=1),
    )
    root["services"].update(
        Panel(_build_services_table(metrics_list, histories), title="StackPulse", border_style="cyan")
    )
    root["alerts"].update(_build_alerts_panel(alert_manager))
    return root


def render_to_console(console: Console, layout: Layout) -> None:
    """Render a layout to the given console."""
    console.print(layout)
