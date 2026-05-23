"""Tests for alert_rules and AlertManager."""

import pytest

from stackpulse.docker_client import ServiceStats
from stackpulse.alert_rules import (
    Alert,
    AlertRule,
    Severity,
    evaluate_rules,
    DEFAULT_RULES,
)
from stackpulse.alert_manager import AlertManager


def _make_stats(
    name="web",
    cpu_percent=0.0,
    mem_percent=0.0,
    status="running",
    health="healthy",
) -> ServiceStats:
    return ServiceStats(
        name=name,
        container_id="abc123",
        status=status,
        health=health,
        cpu_percent=cpu_percent,
        mem_usage=0,
        mem_limit=1024 ** 3,
        mem_percent=mem_percent,
        net_rx=0,
        net_tx=0,
    )


# ---------------------------------------------------------------------------
# evaluate_rules
# ---------------------------------------------------------------------------

def test_no_alerts_when_below_thresholds():
    stats = _make_stats(cpu_percent=10.0, mem_percent=20.0)
    alerts = evaluate_rules(stats)
    assert alerts == []


def test_warning_cpu_fires_above_threshold():
    stats = _make_stats(cpu_percent=85.0)
    alerts = evaluate_rules(stats)
    names = [a.rule_name for a in alerts]
    assert "high_cpu" in names


def test_critical_cpu_fires_at_threshold():
    stats = _make_stats(cpu_percent=95.0)
    alerts = evaluate_rules(stats)
    names = [a.rule_name for a in alerts]
    assert "critical_cpu" in names
    severities = {a.rule_name: a.severity for a in alerts}
    assert severities["critical_cpu"] == Severity.CRITICAL


def test_warning_memory_fires():
    stats = _make_stats(mem_percent=80.0)
    alerts = evaluate_rules(stats)
    names = [a.rule_name for a in alerts]
    assert "high_memory" in names


def test_custom_rules_override_defaults():
    custom = [AlertRule("low_cpu", "cpu_percent", 5.0, Severity.WARNING, "{service} {value}")]
    stats = _make_stats(cpu_percent=10.0)
    alerts = evaluate_rules(stats, rules=custom)
    assert len(alerts) == 1
    assert alerts[0].rule_name == "low_cpu"


def test_alert_message_contains_service_name():
    stats = _make_stats(name="redis", cpu_percent=90.0)
    alerts = evaluate_rules(stats)
    cpu_alerts = [a for a in alerts if "cpu" in a.rule_name]
    assert all("redis" in a.message for a in cpu_alerts)


# ---------------------------------------------------------------------------
# AlertManager
# ---------------------------------------------------------------------------

def test_manager_detects_new_alert():
    manager = AlertManager()
    new, resolved = manager.process([_make_stats(cpu_percent=85.0)])
    assert any(a.rule_name == "high_cpu" for a in new)
    assert resolved == []


def test_manager_no_duplicate_on_second_cycle():
    manager = AlertManager()
    manager.process([_make_stats(cpu_percent=85.0)])
    new, resolved = manager.process([_make_stats(cpu_percent=85.0)])
    assert new == []
    assert resolved == []


def test_manager_resolves_alert_when_metric_drops():
    manager = AlertManager()
    manager.process([_make_stats(cpu_percent=85.0)])
    new, resolved = manager.process([_make_stats(cpu_percent=10.0)])
    assert new == []
    assert any(a.rule_name == "high_cpu" for a in resolved)


def test_manager_active_alerts_property():
    manager = AlertManager()
    manager.process([_make_stats(cpu_percent=85.0)])
    assert len(manager.active_alerts) >= 1


def test_manager_clear_resets_state():
    manager = AlertManager()
    manager.process([_make_stats(cpu_percent=85.0)])
    manager.clear()
    assert manager.active_alerts == []
