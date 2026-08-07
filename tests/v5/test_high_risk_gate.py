"""高风险领域命题独立安全门禁测试。"""

from __future__ import annotations

from engine.v5.domain import V5Claim, V5Confidence, V5Evidence
from engine.v5.high_risk_gate import HIGH_RISK_TASKS, apply_high_risk_gate


def _claim(
    school: str,
    task_id: str,
    *,
    claim_id: str | None = None,
    claim_type: str = "event_claim",
    stance: str = "support",
    source: str | None = None,
    text: str = "可追溯的结构或事件证据。",
    falsifiable: str = "若现实核验未出现对应事件，则本命题失验。",
    score: float = 0.72,
) -> V5Claim:
    evidence = V5Evidence(
        evidence_id=f"ev-{claim_id or school}-{task_id}",
        source=source if source is not None else school,
        text=text,
        node_refs=["chart:root"],
        rule_ids=[f"RULE-{school}"],
    )
    return V5Claim(
        claim_id=claim_id or f"cl-{school}-{task_id}",
        school=school,  # type: ignore[arg-type]
        domain="财富" if task_id.startswith("wealth.") else "婚姻",
        claim=f"{task_id} 判断",
        claim_type=claim_type,  # type: ignore[arg-type]
        stance=stance,  # type: ignore[arg-type]
        confidence=V5Confidence(tier="★★★★", score=score, note="门禁前证据强度"),
        evidence=[evidence],
        falsifiable=falsifiable,
        metadata={"task_id": task_id, "high_risk": task_id in HIGH_RISK_TASKS},
    )


def test_registry_explicitly_covers_required_high_risk_tasks() -> None:
    assert HIGH_RISK_TASKS == {
        "wealth.debt",
        "wealth.major_loss_window",
        "marriage.divorce_or_remarriage",
    }


def test_single_source_high_risk_signal_fails_closed_to_abstain_without_confidence_gain() -> None:
    original = _claim("duan_jianye", "wealth.debt")

    gated, audit = apply_high_risk_gate([original])

    claim = gated[0]
    assert claim.stance == "abstain"
    assert claim.stance != "oppose"
    assert claim.confidence == original.confidence
    assert claim.metadata["high_risk_gate"]["status"] == "failed"
    assert claim.metadata["high_risk_gate"]["reason"] == "insufficient_independent_non_timing_sources"
    assert claim.metadata["high_risk_gate"]["independent_source_count"] == 1
    assert audit["status_counts"] == {"failed": 1}


def test_two_independent_complete_non_timing_sources_pass_without_confidence_gain() -> None:
    originals = [
        _claim("gao_dechen", "wealth.debt"),
        _claim("duan_jianye", "wealth.debt"),
    ]

    gated, audit = apply_high_risk_gate(originals)

    assert [claim.stance for claim in gated] == ["support", "support"]
    assert [claim.confidence for claim in gated] == [claim.confidence for claim in originals]
    assert {claim.metadata["high_risk_gate"]["status"] for claim in gated} == {"passed"}
    assert all(claim.metadata["high_risk_gate"]["independent_source_count"] == 2 for claim in gated)
    assert audit["status_counts"] == {"passed": 2}


def test_ren_fuhong_timing_only_never_counts_as_independent_structure_support() -> None:
    originals = [
        _claim("duan_jianye", "wealth.major_loss_window", claim_type="event_claim"),
        _claim("ren_fuhong", "wealth.major_loss_window", claim_type="timing_claim"),
    ]

    gated, _ = apply_high_risk_gate(originals)

    assert all(claim.stance == "abstain" for claim in gated)
    assert all(claim.metadata["high_risk_gate"]["independent_source_count"] == 1 for claim in gated)
    ren = next(claim for claim in gated if claim.school == "ren_fuhong")
    assert ren.confidence == originals[1].confidence
    assert ren.metadata["high_risk_gate"]["timing_only_excluded"] is True


def test_non_timing_evidence_claim_does_not_count_as_structure_or_event_support() -> None:
    originals = [
        _claim("duan_jianye", "wealth.debt", claim_type="event_claim"),
        _claim("gao_dechen", "wealth.debt", claim_type="evidence_claim"),
    ]

    gated, _ = apply_high_risk_gate(originals)

    assert all(claim.stance == "abstain" for claim in gated)
    assert all(claim.metadata["high_risk_gate"]["independent_source_count"] == 1 for claim in gated)


def test_missing_falsifier_or_incomplete_evidence_fails_closed() -> None:
    claims = [
        _claim("gao_dechen", "marriage.divorce_or_remarriage", falsifiable=""),
        _claim("duan_jianye", "marriage.divorce_or_remarriage", text=""),
    ]

    gated, _ = apply_high_risk_gate(claims)

    reasons = {claim.metadata["high_risk_gate"]["reason"] for claim in gated}
    assert reasons == {"missing_falsifier", "incomplete_evidence"}
    assert all(claim.stance == "abstain" for claim in gated)


def test_ordinary_tasks_are_unchanged_and_output_is_deterministic() -> None:
    ordinary = _claim("duan_jianye", "career.role_change")
    high_risk = [
        _claim("gao_dechen", "wealth.debt"),
        _claim("duan_jianye", "wealth.debt"),
    ]

    left, left_audit = apply_high_risk_gate([ordinary, *high_risk])
    right, right_audit = apply_high_risk_gate([ordinary, *high_risk])

    assert left[0] is ordinary
    assert left == right
    assert left_audit == right_audit
