"""Ties providers + personas + quorum + audit trail together.

run_panel() is the one function most callers need: give it a task
description and a list of seats (persona bound to provider), and it runs
every seat's positive and negative pass, computes quorum, and returns both
the quorum result and a ready-to-render audit trail.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .audit import AuditTrail, build_audit_trail
from .personas import Seat
from .providers.base import ProviderError
from .quorum import QuorumResult, SeatVerdict, Vote, evaluate

_VERDICT_RE = re.compile(r"VERDICT:\s*(APPROVE|DISSENT)", re.I)


@dataclass
class PanelRun:
    task_summary: str
    verdicts: list[SeatVerdict]
    quorum_result: QuorumResult
    audit_trail: AuditTrail


def _run_seat(seat: Seat, task_text: str) -> SeatVerdict:
    persona = seat.persona
    provider = seat.provider

    try:
        positive_notes = provider.complete(
            persona.positive_system_prompt(), task_text
        )
    except ProviderError as exc:
        positive_notes = f"[provider error during positive pass: {exc}]"

    try:
        negative_notes = provider.complete(
            persona.negative_system_prompt(), task_text
        )
    except ProviderError as exc:
        # A provider that can't be reached can't silently count as an
        # approval - that would defeat the whole point of an independent
        # check. Treat an unreachable negative pass as a dissent so a
        # degraded provider blocks rather than passes by default
        # (fail-closed, per the book's degraded-provider discussion).
        negative_notes = f"[provider error during negative pass: {exc}]"
        return SeatVerdict(
            persona=persona,
            provider_info=provider.info,
            vote=Vote.DISSENT,
            positive_notes=positive_notes,
            negative_notes=negative_notes,
            finding=f"Provider unreachable - treated as a dissent (fail-closed): {exc}",
        )

    match = _VERDICT_RE.search(negative_notes)
    if match and match.group(1).upper() == "APPROVE":
        vote = Vote.APPROVE
        finding = None
    else:
        # No parseable verdict at all is treated the same as a dissent: a
        # negative pass that didn't clearly say "checked and clear" hasn't
        # earned an approval.
        vote = Vote.DISSENT
        finding = _VERDICT_RE.sub("", negative_notes).strip()

    return SeatVerdict(
        persona=persona,
        provider_info=provider.info,
        vote=vote,
        positive_notes=positive_notes,
        negative_notes=negative_notes,
        finding=finding,
    )


def run_panel(
    task_summary: str,
    task_text: str,
    seats: list[Seat],
    why: str = "",
    owner: str = "unassigned",
) -> PanelRun:
    verdicts = [_run_seat(seat, task_text) for seat in seats]
    quorum_result = evaluate(verdicts)
    audit_trail = build_audit_trail(
        task_summary=task_summary,
        why=why or task_summary,
        owner=owner,
        verdicts=verdicts,
        quorum_result=quorum_result,
    )
    return PanelRun(
        task_summary=task_summary,
        verdicts=verdicts,
        quorum_result=quorum_result,
        audit_trail=audit_trail,
    )
