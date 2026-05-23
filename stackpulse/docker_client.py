"""Docker Compose service health and resource usage data collector."""

import subprocess
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ServiceStats:
    name: str
    container_id: str
    status: str
    cpu_percent: float
    mem_usage: str
    mem_percent: float
    net_io: str
    block_io: str
    health: Optional[str] = None


def get_compose_services() -> list[dict]:
    """Return list of containers managed by Docker Compose in current directory."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().splitlines()
        return [json.loads(line) for line in lines if line.strip()]
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return []


def get_container_stats(container_ids: list[str]) -> list[ServiceStats]:
    """Fetch live resource stats for given container IDs."""
    if not container_ids:
        return []

    try:
        result = subprocess.run(
            [
                "docker", "stats", "--no-stream", "--format",
                "{{.Name}}\t{{.ID}}\t{{.CPUPerc}}\t{{.MemUsage}}\t"
                "{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}",
            ] + container_ids,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return []

    stats: list[ServiceStats] = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) != 7:
            continue
        name, cid, cpu, mem_usage, mem_perc, net_io, block_io = parts
        stats.append(
            ServiceStats(
                name=name,
                container_id=cid,
                status="running",
                cpu_percent=float(cpu.strip("%") or 0),
                mem_usage=mem_usage,
                mem_percent=float(mem_perc.strip("%") or 0),
                net_io=net_io,
                block_io=block_io,
            )
        )
    return stats


def collect_service_stats() -> list[ServiceStats]:
    """High-level call: fetch Compose services and enrich with live stats."""
    services = get_compose_services()
    id_to_service = {s["ID"]: s for s in services if "ID" in s}

    stats = get_container_stats(list(id_to_service.keys()))

    for stat in stats:
        svc = id_to_service.get(stat.container_id, {})
        stat.status = svc.get("State", stat.status)
        stat.health = svc.get("Health") or None

    return stats
