from panel import Seat, run_panel
from panel.personas import DEVELOPER, OPS, REQUIREMENTS, SECURITY, TEST
from panel.providers import MockProvider
from panel.providers.base import Provider, ProviderError, ProviderInfo
from panel.quorum import QuorumStatus


def _seats():
    return [
        Seat(REQUIREMENTS, MockProvider("vendor-alpha", bias="requirements")),
        Seat(DEVELOPER, MockProvider("vendor-beta", bias="developer")),
        Seat(SECURITY, MockProvider("vendor-gamma", bias="security")),
        Seat(TEST, MockProvider("vendor-delta", bias="test")),
        Seat(OPS, MockProvider("vendor-epsilon", bias="ops")),
    ]


CLEAN_TASK = (
    "Implement fallback-carrier selection: when a regional carrier API "
    "times out, apply the existing eligibility rules to select a "
    "replacement carrier rather than queue the shipment. Eligibility is "
    "checked against each carrier's certification status, read live for "
    "this one decision point rather than from a background store. This "
    "path has a runbook entry and an alert for the capacity it touches, "
    "and it ships with a failure-path test that verifies the fallback "
    "fires when the primary carrier's API times out."
)

CACHE_GAP_TASK = CLEAN_TASK.replace(
    "read live for this one decision point rather than from a background "
    "store",
    "read from a cache that refreshes every six hours",
)


def test_clean_task_reaches_full_quorum():
    run = run_panel("fallback carrier", CLEAN_TASK, _seats(), owner="Dana")
    assert run.quorum_result.status is QuorumStatus.APPROVED
    assert run.quorum_result.approvals == 5
    assert "No findings were raised." in run.audit_trail.render_markdown()


def test_cache_gap_task_blocks_on_security():
    run = run_panel("fallback carrier", CACHE_GAP_TASK, _seats(), owner="Dana")
    assert run.quorum_result.status is QuorumStatus.BLOCKED_REQUIRED_PERSONA_DISSENT
    security_dissents = [
        v for v in run.quorum_result.dissents if v.persona.role == "security"
    ]
    assert len(security_dissents) == 1
    assert "cach" in security_dissents[0].finding.lower()


class _AlwaysFailsProvider(Provider):
    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(vendor="flaky", model="flaky-1")

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        raise ProviderError("simulated outage")


def test_unreachable_provider_fails_closed_as_a_dissent():
    seats = _seats()
    seats[2] = Seat(SECURITY, _AlwaysFailsProvider())  # security seat goes dark
    run = run_panel("fallback carrier", CLEAN_TASK, seats, owner="Dana")
    security_verdict = next(v for v in run.verdicts if v.persona.role == "security")
    assert security_verdict.vote.value == "dissent"
    assert run.quorum_result.status is QuorumStatus.BLOCKED_REQUIRED_PERSONA_DISSENT
