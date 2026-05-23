"""Filter engine for narrowing displayed services by name, status, or health."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from stackpulse.metrics_formatter import FormattedMetrics


@dataclass
class FilterCriteria:
    """Criteria used to filter services shown in the dashboard."""

    name_pattern: Optional[str] = None          # substring or regex
    statuses: List[str] = field(default_factory=list)   # e.g. ["running", "exited"]
    health_states: List[str] = field(default_factory=list)  # e.g. ["healthy", "unhealthy"]
    min_cpu: Optional[float] = None             # inclusive lower bound (%)
    max_cpu: Optional[float] = None             # inclusive upper bound (%)

    @property
    def is_empty(self) -> bool:
        """Return True when no criteria are set (everything passes)."""
        return (
            self.name_pattern is None
            and not self.statuses
            and not self.health_states
            and self.min_cpu is None
            and self.max_cpu is None
        )


def _matches_name(metric: FormattedMetrics, pattern: Optional[str]) -> bool:
    if pattern is None:
        return True
    try:
        return bool(re.search(pattern, metric.service_name, re.IGNORECASE))
    except re.error:
        # Fall back to plain substring match on bad regex
        return pattern.lower() in metric.service_name.lower()


def _matches_status(metric: FormattedMetrics, statuses: List[str]) -> bool:
    if not statuses:
        return True
    return metric.status.lower() in [s.lower() for s in statuses]


def _matches_health(metric: FormattedMetrics, health_states: List[str]) -> bool:
    if not health_states:
        return True
    return metric.health.lower() in [h.lower() for h in health_states]


def _matches_cpu_range(
    metric: FormattedMetrics,
    min_cpu: Optional[float],
    max_cpu: Optional[float],
) -> bool:
    try:
        cpu = float(metric.cpu_percent.rstrip("%"))
    except (ValueError, AttributeError):
        return True
    if min_cpu is not None and cpu < min_cpu:
        return False
    if max_cpu is not None and cpu > max_cpu:
        return False
    return True


def apply_filter(
    metrics: Iterable[FormattedMetrics],
    criteria: FilterCriteria,
) -> List[FormattedMetrics]:
    """Return only those *metrics* that satisfy every criterion in *criteria*."""
    if criteria.is_empty:
        return list(metrics)

    result: List[FormattedMetrics] = []
    for m in metrics:
        if (
            _matches_name(m, criteria.name_pattern)
            and _matches_status(m, criteria.statuses)
            and _matches_health(m, criteria.health_states)
            and _matches_cpu_range(m, criteria.min_cpu, criteria.max_cpu)
        ):
            result.append(m)
    return result
