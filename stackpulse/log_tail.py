"""Tail recent log lines from Docker Compose service containers."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LogEntry:
    service: str
    line: str


@dataclass
class ServiceLogs:
    service: str
    entries: List[LogEntry] = field(default_factory=list)

    @property
    def lines(self) -> List[str]:
        return [e.line for e in self.entries]


def tail_service_logs(
    service: str,
    tail: int = 20,
    project_name: Optional[str] = None,
    runner: Optional[callable] = None,
) -> ServiceLogs:
    """Return the last *tail* log lines for *service*.

    Parameters
    ----------
    service:
        The Compose service name.
    tail:
        Number of lines to retrieve.
    project_name:
        Optional ``--project-name`` passed to ``docker compose``.
    runner:
        Callable used to execute the command (defaults to
        ``subprocess.run``).  Injected for testing.
    """
    if runner is None:
        runner = subprocess.run

    cmd: List[str] = ["docker", "compose"]
    if project_name:
        cmd += ["--project-name", project_name]
    cmd += ["logs", "--no-color", f"--tail={tail}", service]

    try:
        result = runner(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        raw = result.stdout or ""
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        raw = ""

    entries = [
        LogEntry(service=service, line=line)
        for line in raw.splitlines()
        if line.strip()
    ]
    return ServiceLogs(service=service, entries=entries)


def tail_all_services(
    services: List[str],
    tail: int = 10,
    project_name: Optional[str] = None,
    runner: Optional[callable] = None,
) -> List[ServiceLogs]:
    """Collect logs for every service in *services*."""
    return [
        tail_service_logs(svc, tail=tail, project_name=project_name, runner=runner)
        for svc in services
    ]
