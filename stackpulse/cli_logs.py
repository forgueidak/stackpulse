"""CLI entry-point: stream recent logs for one or all Compose services."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from stackpulse.log_tail import tail_all_services, tail_service_logs


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stackpulse-logs",
        description="Tail logs from Docker Compose services.",
    )
    parser.add_argument(
        "services",
        nargs="*",
        metavar="SERVICE",
        help="Service name(s) to tail. Omit to tail all provided via --all.",
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=20,
        metavar="N",
        help="Number of log lines per service (default: 20).",
    )
    parser.add_argument(
        "--project-name",
        default=None,
        metavar="NAME",
        help="Docker Compose project name.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    services: List[str] = args.services
    if not services:
        parser.error("Provide at least one SERVICE name.")
        return 1

    results = tail_all_services(
        services,
        tail=args.tail,
        project_name=args.project_name,
    )

    for svc_logs in results:
        header = f"=== {svc_logs.service} ==="
        print(header)
        if svc_logs.entries:
            for entry in svc_logs.entries:
                print(entry.line)
        else:
            print("(no log output)")
        print()

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
