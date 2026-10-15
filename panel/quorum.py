"""The quorum rules from the book, as actual logic.

- At least 4 of 5 personas must approve.
- The security and test personas' approval is mandatory - a quorum that
  excludes them isn't a quorum, however many other approvals there are.
- A dissent can't be silently outvoted: an unresolved dissent blocks
  "approved" status outright. It can only move to "approved, dissent
  resolved" once a human (or a fix) addresses it on the record - this
  prototype surfaces that as a required field, it doesn't fabricate one.
- Concentration-risk check: no single provider vendor should back more
  than `max_seats_per_vendor` of the five seats, and the developer and
  security seats - the two halves of one supposedly independent check -
  must not share a vendor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from .personas import Persona
from .providers.base import ProviderInfo


class Vote(Enum):
    APPROVE = "approve"
    DISSENT = "dissent"


@dataclass(frozen=True)
class SeatVerdict:
    persona: Persona
    provider_info: ProviderInfo
    vote: Vote
    positive_notes: str
    negative_notes: str
    finding: str | None = None  # populated when vote is DISSENT


class QuorumStatus(Enum):
    APPROVED = "approved"
    APPROVED_WITH_OPEN_DISSENT = "approved_with_open_dissent"
    BLOCKED_REQUIRED_PERSONA_DISSENT = "blocked_required_persona_dissent"
    BLOCKED_INSUFFICIENT_APPROVALS = "blocked_insufficient_approvals"


@dataclass
class ConcentrationWarning:
    message: str


@dataclass
class QuorumResult:
    status: QuorumStatus
    approvals: int
    total: int
    dissents: list[SeatVerdict] = field(default_factory=list)
    concentration_warnings: list[ConcentrationWarning] = field(default_factory=list)

    @property
    def quorum_met(self) -> bool:
        return self.status in (
            QuorumStatus.APPROVED,
            QuorumStatus.APPROVED_WITH_OPEN_DISSENT,
        )


def check_concentration(
    verdicts: list[SeatVerdict], max_seats_per_vendor_fraction: float = 0.4
) -> list[ConcentrationWarning]:
    warnings: list[ConcentrationWarning] = []
    total = len(verdicts)
    max_seats = math.floor(total * max_seats_per_vendor_fraction) or 1

    vendor_counts: dict[str, int] = {}
    for v in verdicts:
        vendor_counts[v.provider_info.vendor] = (
            vendor_counts.get(v.provider_info.vendor, 0) + 1
        )
    for vendor, count in vendor_counts.items():
        if count > max_seats:
            warnings.append(
                ConcentrationWarning(
                    f"Provider '{vendor}' backs {count} of {total} seats, "
                    f"above the {max_seats}-seat cap. No single provider "
                    "should carry this much of the panel's review authority."
                )
            )

    by_role = {v.persona.role: v for v in verdicts}
    dev = by_role.get("developer")
    sec = by_role.get("security")
    if dev and sec and dev.provider_info.vendor == sec.provider_info.vendor:
        warnings.append(
            ConcentrationWarning(
                f"Developer and Security seats both run on '{dev.provider_info.vendor}'. "
                "These are supposed to be the two independent halves of one check - "
                "a shared vendor blind spot would appear on both sides of it."
            )
        )
    return warnings


def evaluate(verdicts: list[SeatVerdict]) -> QuorumResult:
    total = len(verdicts)
    approvals = sum(1 for v in verdicts if v.vote is Vote.APPROVE)
    dissents = [v for v in verdicts if v.vote is Vote.DISSENT]
    required_dissents = [v for v in dissents if v.persona.required_for_quorum]
    warnings = check_concentration(verdicts)

    if required_dissents:
        status = QuorumStatus.BLOCKED_REQUIRED_PERSONA_DISSENT
    elif approvals < max(4, total - 1):
        # >=4 of 5 by default; generalizes to "at most one dissent" for
        # other panel sizes.
        status = QuorumStatus.BLOCKED_INSUFFICIENT_APPROVALS
    elif dissents:
        status = QuorumStatus.APPROVED_WITH_OPEN_DISSENT
    else:
        status = QuorumStatus.APPROVED

    return QuorumResult(
        status=status,
        approvals=approvals,
        total=total,
        dissents=dissents,
        concentration_warnings=warnings,
    )
