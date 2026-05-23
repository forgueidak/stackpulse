"""Sort engine for ordering service metrics by various criteria."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from stackpulse.metrics_formatter import FormattedMetrics


class SortField(str, Enum):
    NAME = "name"
    CPU = "cpu"
    MEMORY = "memory"
    STATUS = "status"
    HEALTH = "health"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class SortCriteria:
    field: SortField = SortField.NAME
    order: SortOrder = SortOrder.ASC

    def is_default(self) -> bool:
        return self.field == SortField.NAME and self.order == SortOrder.ASC


_HEALTH_RANK = {"healthy": 0, "starting": 1, "unhealthy": 2, "none": 3}
_STATUS_RANK = {"running": 0, "paused": 1, "exited": 2, "dead": 3}


def _cpu_key(m: FormattedMetrics) -> float:
    try:
        return float(m.cpu_percent.rstrip("%"))
    except ValueError:
        return 0.0


def _mem_key(m: FormattedMetrics) -> float:
    try:
        return float(m.mem_percent.rstrip("%"))
    except ValueError:
        return 0.0


def _health_key(m: FormattedMetrics) -> int:
    raw = m.health.lower().strip()
    for key in _HEALTH_RANK:
        if key in raw:
            return _HEALTH_RANK[key]
    return 3


def _status_key(m: FormattedMetrics) -> int:
    raw = m.status.lower().strip()
    for key in _STATUS_RANK:
        if key in raw:
            return _STATUS_RANK[key]
    return 4


_KEY_FUNCS = {
    SortField.NAME: lambda m: m.service_name.lower(),
    SortField.CPU: _cpu_key,
    SortField.MEMORY: _mem_key,
    SortField.STATUS: _status_key,
    SortField.HEALTH: _health_key,
}


def sort_metrics(
    metrics: List[FormattedMetrics],
    criteria: Optional[SortCriteria] = None,
) -> List[FormattedMetrics]:
    """Return a sorted copy of *metrics* according to *criteria*."""
    if criteria is None:
        criteria = SortCriteria()

    key_fn = _KEY_FUNCS[criteria.field]
    reverse = criteria.order == SortOrder.DESC
    return sorted(metrics, key=key_fn, reverse=reverse)
