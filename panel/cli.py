"""Command-line entry point.

    python -m panel.cli review --task "task text here" [--summary ...] [--why ...] [--owner ...]
    python -m panel.cli demo         # runs the Fenwick Freight example

This ships with MockProvider seats by default so it runs with no API keys.
Wire in real providers in your own script using the `panel` package
directly - see examples/fenwick_fallback_carrier.py for the pattern.
"""

from __future__ import annotations

import argparse
import sys

from .orchestrator import run_panel
from .personas import DEVELOPER, OPS, REQUIREMENTS, SECURITY, TEST, Seat
from .providers import MockProvider


def _default_seats() -> list[Seat]:
    return [
        Seat(REQUIREMENTS, MockProvider("vendor-alpha", bias="requirements")),
        Seat(DEVELOPER, MockProvider("vendor-beta", bias="developer")),
        Seat(SECURITY, MockProvider("vendor-gamma", bias="security")),
        Seat(TEST, MockProvider("vendor-delta", bias="test")),
        Seat(OPS, MockProvider("vendor-epsilon", bias="ops")),
    ]


def cmd_review(args: argparse.Namespace) -> int:
    run = run_panel(
        task_summary=args.summary or args.task[:60],
        task_text=args.task,
        seats=_default_seats(),
        why=args.why or "",
        owner=args.owner or "unassigned",
    )
    print(run.audit_trail.render_markdown())
    print()
    print(f"quorum_met={run.quorum_result.quorum_met} status={run.quorum_result.status.value}")
    return 0 if run.quorum_result.quorum_met else 1


def cmd_demo(_args: argparse.Namespace) -> int:
    from .demos.fenwick_fallback_carrier import main as demo_main

    demo_main()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="panel", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    review = sub.add_parser("review", help="Run the panel against a task description")
    review.add_argument("--task", required=True, help="The task text to review")
    review.add_argument("--summary", help="Short summary for the TL;DR")
    review.add_argument("--why", help="Why this change, for the TL;DR")
    review.add_argument("--owner", help="Named owner, for the TL;DR")
    review.set_defaults(func=cmd_review)

    demo = sub.add_parser("demo", help="Run the Fenwick Freight example end to end")
    demo.set_defaults(func=cmd_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
