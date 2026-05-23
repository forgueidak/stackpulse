"""CLI helpers for parsing sort arguments used by the dashboard and export commands."""

from __future__ import annotations

import argparse
from typing import Optional

from stackpulse.sort_engine import SortCriteria, SortField, SortOrder


def attach_sort_args(parser: argparse.ArgumentParser) -> None:
    """Add --sort-by and --sort-order arguments to *parser*."""
    parser.add_argument(
        "--sort-by",
        dest="sort_field",
        choices=[f.value for f in SortField],
        default=SortField.NAME.value,
        help="Field to sort services by (default: name).",
    )
    parser.add_argument(
        "--sort-order",
        dest="sort_order",
        choices=[o.value for o in SortOrder],
        default=SortOrder.ASC.value,
        help="Sort direction: asc or desc (default: asc).",
    )


def criteria_from_args(args: argparse.Namespace) -> Optional[SortCriteria]:
    """Build a :class:`SortCriteria` from parsed CLI *args*.

    Returns ``None`` when the user did not specify either flag so callers can
    fall back to a sensible default without inspecting the object.
    """
    field = SortField(getattr(args, "sort_field", SortField.NAME.value))
    order = SortOrder(getattr(args, "sort_order", SortOrder.ASC.value))
    criteria = SortCriteria(field=field, order=order)
    return None if criteria.is_default() else criteria


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stackpulse-sort",
        description="Print services sorted by a chosen metric (demo).",
    )
    attach_sort_args(parser)
    return parser


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)
    criteria = criteria_from_args(args) or SortCriteria()
    print(f"Sorting by '{criteria.field.value}' ({criteria.order.value})")
