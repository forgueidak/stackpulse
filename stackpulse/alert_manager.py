"""Stateful alert manager: deduplicates and tracks active/resolved alerts."""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from stackpulse.alert_rules import Alert, AlertRule, DEFAULT_RULES, evaluate_rules
from stackpulse.docker_client import ServiceStats


class AlertManager:
    """Tracks firing alerts across polling cycles to avoid duplicate noise."""

    def __init__(self, rules: Optional[List[AlertRule]] = None) -> None:
        self._rules = rules if rules is not None else DEFAULT_RULES
        # key: (service_name, rule_name) -> Alert
        self._active: Dict[Tuple[str, str], Alert] = {}

    @property
    def active_alerts(self) -> List[Alert]:
        """Return all currently firing alerts sorted by severity then service."""
        return sorted(
            self._active.values(),
            key=lambda a: (a.severity.value, a.service_name),
        )

    def process(self, stats_list: List[ServiceStats]) -> Tuple[List[Alert], List[Alert]]:
        """Process a fresh batch of service stats.

        Returns:
            new_alerts:      alerts that fired this cycle for the first time.
            resolved_alerts: alerts that were active but are no longer firing.
        """
        current_keys: Dict[Tuple[str, str], Alert] = {}

        for stats in stats_list:
            for alert in evaluate_rules(stats, self._rules):
                key = (alert.service_name, alert.rule_name)
                current_keys[key] = alert

        new_alerts: List[Alert] = []
        for key, alert in current_keys.items():
            if key not in self._active:
                new_alerts.append(alert)

        resolved_alerts: List[Alert] = []
        for key, alert in list(self._active.items()):
            if key not in current_keys:
                resolved_alerts.append(alert)

        self._active = current_keys
        return new_alerts, resolved_alerts

    def clear(self) -> None:
        """Reset all tracked state."""
        self._active.clear()
