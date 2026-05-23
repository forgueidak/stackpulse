"""Tests for stackpulse.log_tail."""

from __future__ import annotations

from types import SimpleNamespace
from typing import List

import pytest

from stackpulse.log_tail import (
    LogEntry,
    ServiceLogs,
    tail_all_services,
    tail_service_logs,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_runner(stdout: str = "", returncode: int = 0):
    """Return a fake subprocess.run that yields a fixed stdout."""
    calls: List[list] = []

    def runner(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(stdout=stdout, stderr="", returncode=returncode)

    runner.calls = calls  # type: ignore[attr-defined]
    return runner


# ---------------------------------------------------------------------------
# LogEntry / ServiceLogs
# ---------------------------------------------------------------------------

def test_service_logs_lines_property():
    logs = ServiceLogs(
        service="web",
        entries=[LogEntry(service="web", line="hello"), LogEntry(service="web", line="world")],
    )
    assert logs.lines == ["hello", "world"]


def test_service_logs_empty_entries():
    logs = ServiceLogs(service="db")
    assert logs.lines == []


# ---------------------------------------------------------------------------
# tail_service_logs
# ---------------------------------------------------------------------------

def test_tail_service_logs_parses_lines():
    runner = _make_runner(stdout="line one\nline two\nline three\n")
    result = tail_service_logs("web", tail=5, runner=runner)

    assert result.service == "web"
    assert len(result.entries) == 3
    assert result.entries[0].line == "line one"
    assert result.entries[2].line == "line three"


def test_tail_service_logs_skips_blank_lines():
    runner = _make_runner(stdout="\nvalid line\n   \nanother\n")
    result = tail_service_logs("api", runner=runner)
    assert len(result.entries) == 2


def test_tail_service_logs_command_includes_tail_flag():
    runner = _make_runner()
    tail_service_logs("svc", tail=42, runner=runner)
    cmd = runner.calls[0]
    assert "--tail=42" in cmd
    assert "svc" in cmd


def test_tail_service_logs_includes_project_name():
    runner = _make_runner()
    tail_service_logs("svc", project_name="myproject", runner=runner)
    cmd = runner.calls[0]
    assert "--project-name" in cmd
    assert "myproject" in cmd


def test_tail_service_logs_omits_project_name_when_none():
    runner = _make_runner()
    tail_service_logs("svc", project_name=None, runner=runner)
    cmd = runner.calls[0]
    assert "--project-name" not in cmd


def test_tail_service_logs_returns_empty_on_file_not_found():
    def bad_runner(cmd, **kwargs):
        raise FileNotFoundError("docker not found")

    result = tail_service_logs("svc", runner=bad_runner)
    assert result.entries == []


def test_tail_service_logs_returns_empty_on_timeout():
    import subprocess

    def bad_runner(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, 10)

    result = tail_service_logs("svc", runner=bad_runner)
    assert result.entries == []


# ---------------------------------------------------------------------------
# tail_all_services
# ---------------------------------------------------------------------------

def test_tail_all_services_returns_one_per_service():
    runner = _make_runner(stdout="log line\n")
    results = tail_all_services(["web", "db", "cache"], tail=5, runner=runner)
    assert len(results) == 3
    assert {r.service for r in results} == {"web", "db", "cache"}


def test_tail_all_services_empty_list():
    runner = _make_runner()
    results = tail_all_services([], runner=runner)
    assert results == []
