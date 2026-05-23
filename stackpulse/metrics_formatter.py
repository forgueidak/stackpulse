"""Utilities for formatting raw Docker stats into human-readable metrics."""

from __future__ import annotations

from typing import TypedDict

from stackpulse.docker_client import ServiceStats


class FormattedMetrics(TypedDict):
    name: str
    status: str
    health: str
    cpu: str
    memory: str
    memory_limit: str
    memory_percent: str
    net_io: str
    block_io: str


def _bytes_to_human(num_bytes: float) -> str:
    """Convert a byte count to a human-readable string (e.g. 1.23 MiB)."""
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:6.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PiB"


def _health_icon(health: str) -> str:
    icons = {
        "healthy": "✅",
        "unhealthy": "❌",
        "starting": "⏳",
        "none": "—",
    }
    return icons.get(health.lower(), "❓")


def _status_color_tag(status: str) -> str:
    """Return a simple tag used by the TUI layer to colour-code the status."""
    status_lower = status.lower()
    if status_lower == "running":
        return "green"
    if status_lower in ("exited", "dead"):
        return "red"
    if status_lower in ("paused", "restarting"):
        return "yellow"
    return "white"


def format_service_metrics(stats: ServiceStats) -> FormattedMetrics:
    """Transform a :class:`ServiceStats` dataclass into display-ready strings."""
    cpu_str = f"{stats.cpu_percent:.1f}%" if stats.cpu_percent is not None else "N/A"

    if stats.memory_usage is not None:
        mem_str = _bytes_to_human(stats.memory_usage)
        mem_pct = (
            f"{(stats.memory_usage / stats.memory_limit * 100):.1f}%"
            if stats.memory_limit
            else "N/A"
        )
    else:
        mem_str = "N/A"
        mem_pct = "N/A"

    mem_limit_str = (
        _bytes_to_human(stats.memory_limit) if stats.memory_limit else "N/A"
    )

    net_rx = _bytes_to_human(stats.net_rx or 0)
    net_tx = _bytes_to_human(stats.net_tx or 0)
    net_io_str = f"{net_rx} / {net_tx}"

    blk_r = _bytes_to_human(stats.block_read or 0)
    blk_w = _bytes_to_human(stats.block_write or 0)
    block_io_str = f"{blk_r} / {blk_w}"

    health = stats.health or "none"

    return FormattedMetrics(
        name=stats.name,
        status=f"[{_status_color_tag(stats.status)}]{stats.status}[/]",
        health=f"{_health_icon(health)} {health}",
        cpu=cpu_str,
        memory=mem_str,
        memory_limit=mem_limit_str,
        memory_percent=mem_pct,
        net_io=net_io_str,
        block_io=block_io_str,
    )


def format_all(services: list[ServiceStats]) -> list[FormattedMetrics]:
    """Format a list of service stats, sorted by service name."""
    return [format_service_metrics(s) for s in sorted(services, key=lambda s: s.name)]
