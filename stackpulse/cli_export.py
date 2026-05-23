"""CLI entry-point for exporting a one-shot metrics snapshot.

Usage
-----
    python -m stackpulse.cli_export [--format json|csv] [--output FILE]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from stackpulse.docker_client import collect_service_stats
from stackpulse.metrics_formatter import format_service_metrics
from stackpulse.snapshot_exporter import ExportFormat, export_snapshot


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stackpulse-export",
        description="Export a one-shot snapshot of Docker Compose service metrics.",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "--output",
        dest="output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        stats_list = collect_service_stats()
    except Exception as exc:  # noqa: BLE001
        print(f"[stackpulse] Failed to collect stats: {exc}", file=sys.stderr)
        return 1

    if not stats_list:
        print("[stackpulse] No running Compose services found.", file=sys.stderr)
        return 0

    formatted = [format_service_metrics(s) for s in stats_list]
    output = export_snapshot(formatted, fmt=args.fmt)  # type: ignore[arg-type]

    if args.output:
        path = Path(args.output)
        path.write_text(output, encoding="utf-8")
        print(f"[stackpulse] Snapshot written to {path}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
