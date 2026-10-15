"""The book's own running example, run through this prototype.

From Chapter 3: Fenwick's fallback-carrier task - apply the existing
eligibility rules to select a replacement carrier during a regional
outage - reaches the panel. The security engineer's negative-approach
pass flags that the eligibility check queries a carrier's certification
status from a cache that refreshes every six hours, which is exactly the
kind of gap this demo's MockProvider is tuned to catch.

Run: panel demo
(or, from a repo checkout without installing: python -m examples.fenwick_fallback_carrier)
"""

from __future__ import annotations

from panel import Seat, run_panel
from panel.personas import DEVELOPER, OPS, REQUIREMENTS, SECURITY, TEST
from panel.providers import MockProvider

TASK_SUMMARY = "Fallback-carrier selection during a regional outage"

TASK_TEXT = (
    "Implement fallback-carrier selection: when a regional carrier API "
    "times out, apply the existing eligibility rules to select a "
    "replacement carrier rather than queue the shipment. Eligibility is "
    "checked against each carrier's certification status, which is read "
    "from a cache that refreshes every six hours. This path has a runbook "
    "entry and an alert for the capacity it touches, and it ships with a "
    "failure-path test that verifies the fallback fires when the primary "
    "carrier's API times out."
)


def build_seats() -> list[Seat]:
    # Five different "vendors" (mocked), each biased toward the kind of
    # thing that persona is actually supposed to catch - deliberately
    # diverse, the way the book's Chapter 3 describes. Note developer and
    # security are NOT on the same vendor, satisfying the concentration
    # check in panel/quorum.py. The task text above is written so that,
    # like the book's own version of this story, only Security finds
    # anything: the six-hour certification cache is the real gap, and the
    # other four personas have nothing to add.
    return [
        Seat(REQUIREMENTS, MockProvider("vendor-alpha", bias="requirements")),
        Seat(DEVELOPER, MockProvider("vendor-beta", bias="developer")),
        Seat(SECURITY, MockProvider("vendor-gamma", bias="security")),
        Seat(TEST, MockProvider("vendor-delta", bias="test")),
        Seat(OPS, MockProvider("vendor-epsilon", bias="ops")),
    ]


# The fixed version: certification is checked live instead of from the
# six-hour cache, for this one decision point - exactly the fix the book
# describes the developer agent making in response to the dissent.
FIXED_TASK_TEXT = (
    "Implement fallback-carrier selection: when a regional carrier API "
    "times out, apply the existing eligibility rules to select a "
    "replacement carrier rather than queue the shipment. Eligibility is "
    "checked against each carrier's certification status, read live for "
    "this one decision point rather than from a background store, since "
    "the cost of a stale read is highest at exactly the moment this task "
    "runs. This path has a runbook entry and an alert for the capacity "
    "it touches, and it ships with a failure-path test that verifies the "
    "fallback fires when the primary carrier's API times out."
)


def _print_run(run) -> None:
    for v in run.verdicts:
        print(f"\n[{v.persona.name}] ({v.provider_info.vendor}) -> {v.vote.value.upper()}")
        if v.finding:
            print(f"  finding: {v.finding}")
    print("\n" + "-" * 70)
    print(
        f"Quorum: {run.quorum_result.status.value} "
        f"({run.quorum_result.approvals}/{run.quorum_result.total} approved)"
    )
    for w in run.quorum_result.concentration_warnings:
        print(f"  concentration warning: {w.message}")


def main() -> None:
    print("=" * 70)
    print("ROUND 1:", TASK_SUMMARY)
    print("=" * 70)
    run1 = run_panel(
        task_summary=TASK_SUMMARY,
        task_text=TASK_TEXT,
        seats=build_seats(),
        why="Keep dispatch routing holding up when a regional carrier goes down.",
        owner="Dana (Fenwick Freight)",
    )
    _print_run(run1)

    print("\n" + "=" * 70)
    print("ROUND 1 AUDIT TRAIL")
    print("=" * 70)
    print(run1.audit_trail.render_markdown())

    if run1.quorum_result.quorum_met:
        return

    print("\n\n" + "#" * 70)
    print("# Security's dissent can't be silently outvoted. The developer")
    print("# agent fixes it: certification is now checked live, not cached,")
    print("# for this decision point. The panel re-votes.")
    print("#" * 70 + "\n")

    print("=" * 70)
    print("ROUND 2 (after fix):", TASK_SUMMARY)
    print("=" * 70)
    run2 = run_panel(
        task_summary=TASK_SUMMARY,
        task_text=FIXED_TASK_TEXT,
        seats=build_seats(),
        why="Keep dispatch routing holding up when a regional carrier goes down.",
        owner="Dana (Fenwick Freight)",
    )
    _print_run(run2)

    print("\n" + "=" * 70)
    print("ROUND 2 AUDIT TRAIL")
    print("=" * 70)
    print(run2.audit_trail.render_markdown())


if __name__ == "__main__":
    main()
