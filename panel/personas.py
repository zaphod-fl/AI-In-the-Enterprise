"""The five personas, each running a positive approach and a negative approach.

Positive approach: try to make the case true that this task, as built, does
what it's supposed to do.
Negative approach: try to prove it false. A negative pass must produce a
specific finding or an explicit "checked and clear" - never a vague
"looks fine" (see the book's "three things that make a negative approach
real" passage in Chapter 3).
"""

from __future__ import annotations

from dataclasses import dataclass

from .providers.base import Provider


@dataclass(frozen=True)
class Persona:
    name: str
    role: str  # short id: "requirements", "developer", "security", "test", "ops"
    positive_charge: str
    negative_charge: str
    required_for_quorum: bool = False

    def positive_system_prompt(self) -> str:
        return (
            f"You are the {self.name} on an independent review panel. "
            f"POSITIVE APPROACH. {self.positive_charge} "
            "Respond with what you found, specifically. If you found nothing "
            "worth flagging, say so plainly rather than padding your answer."
        )

    def negative_system_prompt(self) -> str:
        return (
            f"You are the {self.name} on an independent review panel. "
            f"NEGATIVE APPROACH. {self.negative_charge} "
            "You must either produce a specific finding with a concrete "
            "mechanism and scenario, or state explicitly 'checked and clear' "
            "- never a vague 'looks fine'."
        )


@dataclass(frozen=True)
class Seat:
    """A persona bound to a specific provider - one seat on the panel."""

    persona: Persona
    provider: Provider


REQUIREMENTS = Persona(
    name="Requirements analyst",
    role="requirements",
    positive_charge=(
        "Confirm that the implementation matches the stated intent: every "
        "constraint named in the task is actually addressed."
    ),
    negative_charge=(
        "Look for gaps between what was stated and what was built: an "
        "unstated assumption filled in by the agent, a constraint quietly "
        "dropped, or an edge case the task never considered."
    ),
)

DEVELOPER = Persona(
    name="Developer",
    role="developer",
    positive_charge=(
        "Confirm the implementation is correct, idiomatic, and does what "
        "the task describes."
    ),
    negative_charge=(
        "Look for correctness bugs, unhandled error paths, or places the "
        "implementation silently diverges from the stated task."
    ),
)

SECURITY = Persona(
    name="Security engineer",
    role="security",
    positive_charge=(
        "Confirm there is no security-relevant gap in this change - auth, "
        "data handling, credential management, trust boundaries."
    ),
    negative_charge=(
        "Try to find a security-relevant gap: a cached or stale check used "
        "where a live one matters, a credential handled unsafely, a trust "
        "boundary crossed implicitly."
    ),
    required_for_quorum=True,
)

TEST = Persona(
    name="Test engineer",
    role="test",
    positive_charge=(
        "Confirm there is adequate test or validation evidence for this "
        "change, including the failure path, not just the happy path."
    ),
    negative_charge=(
        "Try to find what isn't actually tested: a fallback path, an edge "
        "case, a claim of 'it works' with no evidence behind it."
    ),
    required_for_quorum=True,
)

OPS = Persona(
    name="Operations/SRE",
    role="ops",
    positive_charge=(
        "Confirm this change is operationally ready: it has a runbook "
        "entry, an alert, or a documented rollback if something goes wrong."
    ),
    negative_charge=(
        "Try to find what would page someone at 2 a.m. without warning: "
        "missing monitoring, an undocumented capacity assumption, no "
        "rollback path."
    ),
)

ALL_PERSONAS: tuple[Persona, ...] = (REQUIREMENTS, DEVELOPER, SECURITY, TEST, OPS)
