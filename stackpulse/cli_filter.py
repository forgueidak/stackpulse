"""CLI helpers for parsing --filter flags into a FilterCriteria.

Usage (from the main CLI or interactive prompt)::

    parser = argparse.ArgumentParser()
    attach_filter_args(parser)
    args = parser.parse_args()
    criteria = criteria_from_args(args)
"""
from __future__ import annotations

import argparse
from typing import List, Optional

from stackpulse.filter_engine import FilterCriteria


def attach_filter_args(parser: argparse.ArgumentParser) -> None:
    """Add filter-related arguments to *parser* in-place."""
    grp = parser.add_argument_group("filtering")
    grp.add_argument(
        "--name",
        metavar="PATTERN",
        default=None,
        help="Show only services whose name matches PATTERN (substring or regex).",
    )
    grp.add_argument(
        "--status",
        metavar="STATUS",
        action="append",
        dest="statuses",
        default=[],
        help="Keep services with this status (repeatable). E.g. running, exited.",
    )
    grp.add_argument(
        "--health",
        metavar="STATE",
        action="append",
        dest="health_states",
        default=[],
        help="Keep services with this health state (repeatable). E.g. healthy.",
    )
    grp.add_argument(
        "--min-cpu",
        type=float,
        default=None,
        metavar="PCT",
        help="Lower CPU %% bound (inclusive).",
    )
    grp.add_argument(
        "--max-cpu",
        type=float,
        default=None,
        metavar="PCT",
        help="Upper CPU %% bound (inclusive).",
    )


def criteria_from_args(args: argparse.Namespace) -> FilterCriteria:
    """Build a :class:`FilterCriteria` from parsed *args*."""
    return FilterCriteria(
        name_pattern=args.name,
        statuses=list(args.statuses),
        health_states=list(args.health_states),
        min_cpu=args.min_cpu,
        max_cpu=args.max_cpu,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stackpulse-filter",
        description="Print active filter criteria (for debugging).",
    )
    attach_filter_args(parser)
    return parser


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)
    criteria = criteria_from_args(args)
    if criteria.is_empty:
        print("No filters active — all services will be shown.")
    else:
        print("Active filters:")
        if criteria.name_pattern:
            print(f"  name pattern : {criteria.name_pattern}")
        if criteria.statuses:
            print(f"  statuses     : {', '.join(criteria.statuses)}")
        if criteria.health_states:
            print(f"  health states: {', '.join(criteria.health_states)}")
        if criteria.min_cpu is not None:
            print(f"  min CPU      : {criteria.min_cpu}%")
        if criteria.max_cpu is not None:
            print(f"  max CPU      : {criteria.max_cpu}%")


if __name__ == "__main__":  # pragma: no cover
    main()
