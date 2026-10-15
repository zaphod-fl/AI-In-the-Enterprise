"""Audit trail generation: the TL;DR, the issue & risk log, and the dissent log.

These are the three artifacts the book's Chapter 5 describes as the actual
documentation an AI-built system needs - not a design doc that trails the
code, but a record generated from the review that just happened.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .quorum import QuorumResult, QuorumStatus, SeatVerdict, Vote


@dataclass
class AuditTrail:
    tldr: str
    issue_log_rows: list[dict[str, str]]
    dissent_log_rows: list[dict[str, str]]

    def render_markdown(self) -> str:
        lines = ["# TL;DR", "", self.tldr, "", "# Issue & Risk Log", ""]
        if self.issue_log_rows:
            cols = ["Finding", "Raised by", "Severity", "Status", "Notes"]
            lines.append("| " + " | ".join(cols) + " |")
            lines.append("|" + "---|" * len(cols))
            for row in self.issue_log_rows:
                lines.append("| " + " | ".join(row.get(c, "") for c in cols) + " |")
        else:
            lines.append("No findings were raised.")
        lines += ["", "# Dissent Log", ""]
        if self.dissent_log_rows:
            cols = ["Persona", "Provider", "Finding", "Status", "Resolution"]
            lines.append("| " + " | ".join(cols) + " |")
            lines.append("|" + "---|" * len(cols))
            for row in self.dissent_log_rows:
                lines.append("| " + " | ".join(row.get(c, "") for c in cols) + " |")
        else:
            lines.append("No dissents were raised.")
        return "\n".join(lines)


def build_audit_trail(
    task_summary: str,
    why: str,
    owner: str,
    verdicts: list[SeatVerdict],
    quorum_result: QuorumResult,
) -> AuditTrail:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    panel_line = (
        f"{quorum_result.approvals}/{quorum_result.total} approved "
        f"({quorum_result.status.value})"
    )
    risk_accepted = (
        "none recorded"
        if quorum_result.status == QuorumStatus.APPROVED
        else "see dissent log - requires a named owner and an expiration "
        "condition before this can be treated as resolved"
    )

    tldr = (
        f"**Change:** {task_summary}\n"
        f"**Why:** {why}\n"
        f"**Panel:** {panel_line}\n"
        f"**Risk accepted:** {risk_accepted}\n"
        f"**Owner:** {owner}\n"
        f"**Generated:** {timestamp}"
    )

    issue_rows = []
    for v in verdicts:
        if v.vote is Vote.DISSENT:
            issue_rows.append(
                {
                    "Finding": (v.finding or "").replace("\n", " ")[:200],
                    "Raised by": v.persona.name,
                    "Severity": "high" if v.persona.required_for_quorum else "medium",
                    "Status": "open",
                    "Notes": f"provider: {v.provider_info.vendor}",
                }
            )
    for w in quorum_result.concentration_warnings:
        issue_rows.append(
            {
                "Finding": w.message,
                "Raised by": "quorum engine (concentration check)",
                "Severity": "medium",
                "Status": "open",
                "Notes": "",
            }
        )

    dissent_rows = []
    for v in quorum_result.dissents:
        dissent_rows.append(
            {
                "Persona": v.persona.name,
                "Provider": f"{v.provider_info.vendor} ({v.provider_info.model})",
                "Finding": (v.finding or "").replace("\n", " ")[:200],
                "Status": "overridden" if quorum_result.quorum_met else "blocking",
                "Resolution": "NEEDS HUMAN ENTRY: fix applied, or rebuttal with "
                "evidence, before this can be marked resolved",
            }
        )

    return AuditTrail(
        tldr=tldr, issue_log_rows=issue_rows, dissent_log_rows=dissent_rows
    )
