"""命题级结构化反馈与只读校准候选核心测试。"""

from __future__ import annotations

from dataclasses import replace

import pytest

from engine.v5.domain import (
    V5Claim,
    V5Confidence,
    V5Evidence,
    V5Output,
    V5RunSnapshot,
)
from engine.v5.domain_feedback import (
    DomainClaimFeedback,
    aggregate_calibration_candidates,
    build_feedback_draft,
    claim_hash,
    validate_feedback,
)


def _claim(
    claim_id: str = "claim-wealth-debt",
    *,
    school: str = "ziping",
    task_id: str = "wealth.debt",
    claim_type: str = "event_claim",
    high_risk: bool = True,
) -> V5Claim:
    return V5Claim(
        claim_id=claim_id,
        school=school,
        domain="财富",
        claim="存在债务压力风险。",
        claim_type=claim_type,
        stance="support",
        confidence=V5Confidence(tier="★★★", score=0.62),
        evidence=[
            V5Evidence(
                evidence_id=f"ev-{claim_id}",
                source="test",
                text="财星受制且结构证据完整。",
                node_refs=["chart:root"],
            )
        ],
        falsifiable="若核验期无债务压力则不成立。",
        metadata={"task_id": task_id, "high_risk": high_risk},
    )


def _snapshot(*claims: V5Claim) -> V5RunSnapshot:
    output = V5Output(
        case_id="C-TEST-DOMAIN-FEEDBACK",
        chart={"pillars": ["甲子", "乙丑", "丙寅", "丁卯"]},
        claims=list(claims or (_claim(),)),
    )
    return V5RunSnapshot.from_output(output)


def _feedback(
    snapshot: V5RunSnapshot,
    *,
    status: str = "accepted",
    reviewer: str = "human-reviewer-01",
    claim: V5Claim | None = None,
) -> DomainClaimFeedback:
    target = claim or snapshot.claims[0]
    return DomainClaimFeedback(
        feedback_id=f"feedback-{reviewer}-{status}",
        case_id=snapshot.case_id,
        run_id=snapshot.run_id,
        snapshot_output_hash=snapshot.output_hash,
        claim_id=target.claim_id,
        claim_hash=claim_hash(target),
        reviewer=reviewer,
        status=status,
        observed_at="2026-08-01T00:00:00Z",
        note="人工核验。",
    )


def test_claim_hash_is_stable_and_draft_binds_run_output_and_claim() -> None:
    snapshot = _snapshot()
    claim = snapshot.claims[0]

    assert claim_hash(claim) == claim_hash(V5Claim.from_dict(claim.to_dict()))
    draft = build_feedback_draft(snapshot, claim.claim_id)

    assert draft.run_id == snapshot.run_id
    assert draft.snapshot_output_hash == snapshot.output_hash
    assert draft.claim_id == claim.claim_id
    assert draft.claim_hash == claim_hash(claim)
    assert draft.status == "unknown"


@pytest.mark.parametrize(
    "status",
    ["accepted", "rejected", "partial", "unknown", "timing_deviation"],
)
def test_feedback_status_taxonomy_is_closed(status: str) -> None:
    snapshot = _snapshot()
    validate_feedback(_feedback(snapshot, status=status), snapshot)


def test_feedback_rejects_unknown_status_or_orphan_claim() -> None:
    snapshot = _snapshot()
    with pytest.raises(ValueError, match="feedback status"):
        validate_feedback(_feedback(snapshot, status="hit"), snapshot)

    orphan = replace(_feedback(snapshot), claim_id="missing-claim")
    with pytest.raises(ValueError, match="claim_id not found"):
        validate_feedback(orphan, snapshot)


def test_feedback_rejects_wrong_run_output_hash_and_tampered_claim() -> None:
    snapshot = _snapshot()
    with pytest.raises(ValueError, match="run_id mismatch"):
        validate_feedback(replace(_feedback(snapshot), run_id="run-wrong"), snapshot)
    with pytest.raises(ValueError, match="snapshot output hash mismatch"):
        validate_feedback(
            replace(_feedback(snapshot), snapshot_output_hash="deadbeef"),
            snapshot,
        )

    tampered_claim = replace(snapshot.claims[0], claim="已被篡改")
    tampered = replace(snapshot, claims=[tampered_claim])
    with pytest.raises(ValueError, match="snapshot output hash mismatch"):
        validate_feedback(_feedback(snapshot), tampered)

    forged_snapshot = replace(tampered, output_hash=tampered.to_output().hash())
    forged_feedback = replace(
        _feedback(snapshot),
        snapshot_output_hash=forged_snapshot.output_hash,
    )
    with pytest.raises(ValueError, match="claim hash mismatch"):
        validate_feedback(forged_feedback, forged_snapshot)


def test_duplicate_reviewer_and_duplicate_feedback_are_rejected() -> None:
    snapshot = _snapshot()
    existing = _feedback(snapshot)

    with pytest.raises(ValueError, match="duplicate feedback_id"):
        validate_feedback(existing, snapshot, existing_feedback=[existing])

    second = replace(existing, feedback_id="feedback-second")
    with pytest.raises(ValueError, match="duplicate reviewer"):
        validate_feedback(second, snapshot, existing_feedback=[existing])


def test_candidates_keep_unknown_partial_and_timing_deviation_in_separate_ledgers() -> None:
    claim = _claim(high_risk=False)
    snapshot = _snapshot(claim)
    feedback = [
        _feedback(snapshot, status="accepted", reviewer="human-01"),
        _feedback(snapshot, status="rejected", reviewer="human-02"),
        _feedback(snapshot, status="partial", reviewer="human-03"),
        _feedback(snapshot, status="unknown", reviewer="human-04"),
        _feedback(snapshot, status="timing_deviation", reviewer="human-05"),
    ]

    payload = aggregate_calibration_candidates(feedback, [snapshot])
    candidate = payload["candidates"][0]

    assert candidate["identity"] == {
        "school": "ziping",
        "domain": "财富",
        "task": "wealth.debt",
        "claim_type": "event_claim",
    }
    assert candidate["evidence_count"] == 5
    assert candidate["support_count"] == 1
    assert candidate["oppose_count"] == 1
    assert candidate["partial_count"] == 1
    assert candidate["unknown_count"] == 1
    assert candidate["timing_deviation_count"] == 1
    assert candidate["scored_outcome_count"] == 2
    assert candidate["hit_rate"] == 0.5
    assert payload["read_only"] is True
    assert payload["automatic_promotion"] is False


def test_high_risk_candidate_always_requires_human_review() -> None:
    snapshot = _snapshot(_claim(high_risk=True))

    candidate = aggregate_calibration_candidates([_feedback(snapshot)], [snapshot])["candidates"][0]

    assert candidate["risk_level"] == "high"
    assert candidate["requires_human_review"] is True
    assert candidate["promotion_allowed"] is False
