"""CLI entry-point for managing pinned services from the command line."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from stackpulse.pin_manager import PinManager, _DEFAULT_PIN_FILE


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stackpulse-pin",
        description="Manage pinned services for StackPulse dashboard.",
    )
    parser.add_argument(
        "--pin-file",
        metavar="PATH",
        default=str(_DEFAULT_PIN_FILE),
        help="Path to the pinned-services JSON file (default: %(default)s).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # pin
    p_pin = sub.add_parser("pin", help="Pin one or more services.")
    p_pin.add_argument("services", nargs="+", metavar="SERVICE")

    # unpin
    p_unpin = sub.add_parser("unpin", help="Unpin one or more services.")
    p_unpin.add_argument("services", nargs="+", metavar="SERVICE")

    # toggle
    p_toggle = sub.add_parser("toggle", help="Toggle pin state of a service.")
    p_toggle.add_argument("service", metavar="SERVICE")

    # list
    sub.add_parser("list", help="List currently pinned services.")

    # clear
    sub.add_parser("clear", help="Unpin all services.")

    return parser


def main(argv: list[str] | None = None) -> int:  # noqa: D401
    """Entry-point; returns exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    pm = PinManager.load(Path(args.pin_file))

    if args.command == "pin":
        for svc in args.services:
            pm.pin(svc)
            print(f"Pinned: {svc}")

    elif args.command == "unpin":
        for svc in args.services:
            pm.unpin(svc)
            print(f"Unpinned: {svc}")

    elif args.command == "toggle":
        now_pinned = pm.toggle(args.service)
        state = "pinned" if now_pinned else "unpinned"
        print(f"{args.service}: {state}")

    elif args.command == "list":
        pins = sorted(pm.pinned)
        if pins:
            for name in pins:
                print(name)
        else:
            print("(no pinned services)")

    elif args.command == "clear":
        pm.clear()
        print("All pins cleared.")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
