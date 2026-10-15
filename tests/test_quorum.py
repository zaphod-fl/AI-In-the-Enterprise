from panel.personas import DEVELOPER, OPS, REQUIREMENTS, SECURITY, TEST
from panel.providers.base import ProviderInfo
from panel.quorum import QuorumStatus, SeatVerdict, Vote, check_concentration, evaluate


def _verdict(persona, vendor, vote, finding=None):
    return SeatVerdict(
        persona=persona,
        provider_info=ProviderInfo(vendor=vendor, model=f"{vendor}-m"),
        vote=vote,
        positive_notes="",
        negative_notes="",
        finding=finding,
    )


def _all_approve():
    return [
        _verdict(REQUIREMENTS, "v1", Vote.APPROVE),
        _verdict(DEVELOPER, "v2", Vote.APPROVE),
        _verdict(SECURITY, "v3", Vote.APPROVE),
        _verdict(TEST, "v4", Vote.APPROVE),
        _verdict(OPS, "v5", Vote.APPROVE),
    ]


def test_unanimous_approval():
    result = evaluate(_all_approve())
    assert result.status is QuorumStatus.APPROVED
    assert result.quorum_met
    assert result.approvals == 5


def test_non_required_dissent_still_reaches_quorum():
    verdicts = _all_approve()
    verdicts[1] = _verdict(DEVELOPER, "v2", Vote.DISSENT, finding="minor style nit")
    result = evaluate(verdicts)
    assert result.status is QuorumStatus.APPROVED_WITH_OPEN_DISSENT
    assert result.quorum_met
    assert len(result.dissents) == 1


def test_security_dissent_blocks_even_with_four_approvals():
    verdicts = _all_approve()
    verdicts[2] = _verdict(SECURITY, "v3", Vote.DISSENT, finding="cache staleness gap")
    result = evaluate(verdicts)
    assert result.status is QuorumStatus.BLOCKED_REQUIRED_PERSONA_DISSENT
    assert not result.quorum_met


def test_test_engineer_dissent_blocks_too():
    verdicts = _all_approve()
    verdicts[3] = _verdict(TEST, "v4", Vote.DISSENT, finding="no failure-path test")
    result = evaluate(verdicts)
    assert result.status is QuorumStatus.BLOCKED_REQUIRED_PERSONA_DISSENT
    assert not result.quorum_met


def test_two_non_required_dissents_block_on_count():
    verdicts = _all_approve()
    verdicts[0] = _verdict(REQUIREMENTS, "v1", Vote.DISSENT, finding="vague")
    verdicts[1] = _verdict(DEVELOPER, "v2", Vote.DISSENT, finding="nit")
    result = evaluate(verdicts)
    assert result.status is QuorumStatus.BLOCKED_INSUFFICIENT_APPROVALS
    assert not result.quorum_met


def test_concentration_warning_when_one_vendor_backs_too_many_seats():
    verdicts = [
        _verdict(REQUIREMENTS, "shared-vendor", Vote.APPROVE),
        _verdict(DEVELOPER, "shared-vendor", Vote.APPROVE),
        _verdict(SECURITY, "shared-vendor", Vote.APPROVE),
        _verdict(TEST, "v4", Vote.APPROVE),
        _verdict(OPS, "v5", Vote.APPROVE),
    ]
    warnings = check_concentration(verdicts)
    assert any("shared-vendor" in w.message for w in warnings)


def test_concentration_warning_when_dev_and_security_share_a_vendor():
    verdicts = _all_approve()
    verdicts[1] = _verdict(DEVELOPER, "same-vendor", Vote.APPROVE)
    verdicts[2] = _verdict(SECURITY, "same-vendor", Vote.APPROVE)
    warnings = check_concentration(verdicts)
    assert any("independent" in w.message.lower() for w in warnings)
