"""Export a point-in-time snapshot of service metrics to JSON or CSV."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Iterable, Literal

from stackpulse.metrics_formatter import FormattedMetrics

ExportFormat = Literal["json", "csv"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def export_snapshot(
    metrics: Iterable[FormattedMetrics],
    fmt: ExportFormat = "json",
) -> str:
    """Serialise *metrics* to a string in the requested *fmt*.

    Parameters
    ----------
    metrics:
        Iterable of :class:`FormattedMetrics` instances to export.
    fmt:
        ``"json"`` (default) or ``"csv"``.

    Returns
    -------
    str
        The serialised snapshot.
    """
    rows = list(metrics)
    timestamp = _utc_now_iso()

    if fmt == "json":
        return _to_json(rows, timestamp)
    if fmt == "csv":
        return _to_csv(rows, timestamp)
    raise ValueError(f"Unsupported export format: {fmt!r}")


def _to_json(rows: list[FormattedMetrics], timestamp: str) -> str:
    payload = {
        "exported_at": timestamp,
        "services": [
            {
                "service": r.service,
                "status": r.status,
                "health": r.health,
                "cpu_pct": r.cpu_pct,
                "mem_usage": r.mem_usage,
                "mem_limit": r.mem_limit,
                "mem_pct": r.mem_pct,
                "net_rx": r.net_rx,
                "net_tx": r.net_tx,
                "pids": r.pids,
            }
            for r in rows
        ],
    }
    return json.dumps(payload, indent=2)


def _to_csv(rows: list[FormattedMetrics], timestamp: str) -> str:
    fieldnames = [
        "exported_at",
        "service",
        "status",
        "health",
        "cpu_pct",
        "mem_usage",
        "mem_limit",
        "mem_pct",
        "net_rx",
        "net_tx",
        "pids",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(
            {
                "exported_at": timestamp,
                "service": r.service,
                "status": r.status,
                "health": r.health,
                "cpu_pct": r.cpu_pct,
                "mem_usage": r.mem_usage,
                "mem_limit": r.mem_limit,
                "mem_pct": r.mem_pct,
                "net_rx": r.net_rx,
                "net_tx": r.net_tx,
                "pids": r.pids,
            }
        )
    return buf.getvalue()
