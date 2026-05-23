"""Unit tests for stackpulse.docker_client module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from stackpulse.docker_client import (
    ServiceStats,
    collect_service_stats,
    get_compose_services,
    get_container_stats,
)


SAMPLE_COMPOSE_OUTPUT = json.dumps(
    {"ID": "abc123", "Name": "web", "State": "running", "Health": "healthy"}
)

SAMPLE_STATS_OUTPUT = (
    "web\tabc123\t12.5%\t128MiB / 1GiB\t12.5%\t1MB / 500kB\t10MB / 5MB"
)


@patch("stackpulse.docker_client.subprocess.run")
def test_get_compose_services_success(mock_run):
    mock_run.return_value = MagicMock(stdout=SAMPLE_COMPOSE_OUTPUT, returncode=0)
    services = get_compose_services()
    assert len(services) == 1
    assert services[0]["Name"] == "web"
    assert services[0]["ID"] == "abc123"


@patch("stackpulse.docker_client.subprocess.run")
def test_get_compose_services_failure(mock_run):
    import subprocess
    mock_run.side_effect = subprocess.CalledProcessError(1, "docker")
    services = get_compose_services()
    assert services == []


@patch("stackpulse.docker_client.subprocess.run")
def test_get_container_stats_success(mock_run):
    mock_run.return_value = MagicMock(stdout=SAMPLE_STATS_OUTPUT, returncode=0)
    stats = get_container_stats(["abc123"])
    assert len(stats) == 1
    s = stats[0]
    assert s.name == "web"
    assert s.cpu_percent == 12.5
    assert s.mem_percent == 12.5
    assert s.net_io == "1MB / 500kB"


def test_get_container_stats_empty_ids():
    stats = get_container_stats([])
    assert stats == []


@patch("stackpulse.docker_client.get_container_stats")
@patch("stackpulse.docker_client.get_compose_services")
def test_collect_service_stats_enriches_health(mock_services, mock_stats):
    mock_services.return_value = [
        {"ID": "abc123", "Name": "web", "State": "running", "Health": "healthy"}
    ]
    mock_stats.return_value = [
        ServiceStats(
            name="web",
            container_id="abc123",
            status="running",
            cpu_percent=5.0,
            mem_usage="64MiB / 512MiB",
            mem_percent=12.5,
            net_io="100kB / 50kB",
            block_io="1MB / 0B",
        )
    ]
    result = collect_service_stats()
    assert len(result) == 1
    assert result[0].health == "healthy"
    assert result[0].status == "running"
