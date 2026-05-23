"""Alert rules engine for threshold-based service health notifications."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from stackpulse.docker_client import ServiceStats


class Severity(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    name: str
    metric: str  # "cpu_percent", "mem_percent", "status"
    threshold: float
    severity: Severity
    message_template: str = "{service}: {metric} is {value}"


@dataclass
class Alert:
    rule_name: str
    service_name: str
    severity: Severity
    message: str
    value: float


DEFAULT_RULES: List[AlertRule] = [
    AlertRule(
        name="high_cpu",
        metric="cpu_percent",
        threshold=80.0,
        severity=Severity.WARNING,
        message_template="{service}: CPU usage at {value:.1f}%",
    ),
    AlertRule(
        name="critical_cpu",
        metric="cpu_percent",
        threshold=95.0,
        severity=Severity.CRITICAL,
        message_template="{service}: CPU critical at {value:.1f}%",
    ),
    AlertRule(
        name="high_memory",
        metric="mem_percent",
        threshold=75.0,
        severity=Severity.WARNING,
        message_template="{service}: Memory usage at {value:.1f}%",
    ),
    AlertRule(
        name="critical_memory",
        metric="mem_percent",
        threshold=90.0,
        severity=Severity.CRITICAL,
        message_template="{service}: Memory critical at {value:.1f}%",
    ),
]


def evaluate_rules(
    stats: ServiceStats,
    rules: Optional[List[AlertRule]] = None,
) -> List[Alert]:
    """Evaluate alert rules against a ServiceStats snapshot.

    Returns a list of triggered Alert objects (may be empty).
    """
    if rules is None:
        rules = DEFAULT_RULES

    alerts: List[Alert] = []

    metric_map = {
        "cpu_percent": stats.cpu_percent,
        "mem_percent": stats.mem_percent,
    }

    for rule in rules:
        value = metric_map.get(rule.metric)
        if value is None:
            continue
        if value >= rule.threshold:
            message = rule.message_template.format(
                service=stats.name, metric=rule.metric, value=value
            )
            alerts.append(
                Alert(
                    rule_name=rule.name,
                    service_name=stats.name,
                    severity=rule.severity,
                    message=message,
                    value=value,
                )
            )

    return alerts
