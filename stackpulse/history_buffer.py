"""Circular buffer for storing recent metric snapshots per service."""

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List

from stackpulse.docker_client import ServiceStats

DEFAULT_MAX_SAMPLES = 60  # ~1 minute at 1-second poll interval


@dataclass
class MetricPoint:
    """A single timestamped data point for sparkline rendering."""

    timestamp: float
    cpu_percent: float
    mem_percent: float


@dataclass
class ServiceHistory:
    """Holds a fixed-length history of metric points for one service."""

    service_name: str
    max_samples: int = DEFAULT_MAX_SAMPLES
    points: Deque[MetricPoint] = field(default_factory=deque)

    def add(self, point: MetricPoint) -> None:
        """Append a new point, evicting the oldest if at capacity."""
        if len(self.points) >= self.max_samples:
            self.points.popleft()
        self.points.append(point)

    def cpu_series(self) -> List[float]:
        """Return ordered list of CPU percent values."""
        return [p.cpu_percent for p in self.points]

    def mem_series(self) -> List[float]:
        """Return ordered list of memory percent values."""
        return [p.mem_percent for p in self.points]

    def latest(self) -> MetricPoint | None:
        """Return the most recent point, or None if empty."""
        return self.points[-1] if self.points else None


class HistoryBuffer:
    """Manages per-service metric history across poll cycles."""

    def __init__(self, max_samples: int = DEFAULT_MAX_SAMPLES) -> None:
        self._max_samples = max_samples
        self._histories: Dict[str, ServiceHistory] = {}

    def record(self, stats: ServiceStats, timestamp: float) -> None:
        """Record a metric snapshot from a ServiceStats object."""
        name = stats.service_name
        if name not in self._histories:
            self._histories[name] = ServiceHistory(
                service_name=name, max_samples=self._max_samples
            )
        point = MetricPoint(
            timestamp=timestamp,
            cpu_percent=stats.cpu_percent,
            mem_percent=stats.mem_percent,
        )
        self._histories[name].add(point)

    def get(self, service_name: str) -> ServiceHistory | None:
        """Retrieve history for a named service, or None if unseen."""
        return self._histories.get(service_name)

    def all_services(self) -> List[str]:
        """Return names of all tracked services."""
        return list(self._histories.keys())

    def clear(self, service_name: str) -> None:
        """Remove history for a service (e.g. after it is removed)."""
        self._histories.pop(service_name, None)
