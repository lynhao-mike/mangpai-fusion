from __future__ import annotations

from engine.governance import (
    ClaimEvidenceGrade,
    ClaimIssue,
    ClaimIssueCode,
    ClaimKind,
    ClaimReference,
    ClaimReferenceCategory,
    ClaimStance,
    DigestRef,
    GovernanceClaimSpec,
    GovernanceReferenceCatalog,
    ReferenceRegistration,
    TemporalLayer,
    TemporalScope,
    build_governance_claim,
)
from engine.governance.registries import (
    CapabilityIdentity,
    CapabilityRegistration,
    CapabilityRole,
    FactCertificationRegistry,
    LegacyCompatibilitySource,
    PeerSchool,
    PublicationStatus,
    SchoolRegistry,
)
from engine.governance.arbitration import (
    ArbitrationArena,
    ArbitrationContext,
    ArbitrationDecision,
    GateName,
    arbitrate,
)


_TEST_DERIVATION_DIGEST = DigestRef.from_material(("task7", "derivation"))


def _catalog() -> GovernanceReferenceCatalog:
    return GovernanceReferenceCatalog(
        (
            ReferenceRegistration(ClaimReferenceCategory.FACT, "fact", "v1"),
            ReferenceRegistration(ClaimReferenceCategory.SOURCE_RULE, "rule", "v1"),
            ReferenceRegistration(ClaimReferenceCategory.SOURCE_RULE, "rule-alt", "v1"),
        )
    )


def _registry(
    role: CapabilityRole = CapabilityRole.LEAD,
    kind: ClaimKind = ClaimKind.STRUCTURE,
    publication_status: PublicationStatus = PublicationStatus.PUBLISHED,
) -> SchoolRegistry:
    identity = CapabilityIdentity(
        "ziping", "task", kind, ClaimEvidenceGrade.DIRECT, "v1"
    )
    return SchoolRegistry(
        tuple(
            PeerSchool(value)
            for value in (
                "ziping",
                "gao_dechen",
                "duan_jianye",
                "yang_qingjuan",
                "ren_fuhong",
            )
        ),
        (LegacyCompatibilitySource("ditiansui"),),
        (CapabilityRegistration(identity, role, publication_status),),
    )


def _claim(
    *,
    stance: ClaimStance = ClaimStance.SUPPORT,
    scope: TemporalScope | None = None,
    school: str = "ziping",
    kind: ClaimKind = ClaimKind.STRUCTURE,
    blockers: tuple[ClaimIssue, ...] = (),
    source_rule_refs: tuple[ClaimReference, ...] | None = None,
    counterevidence: tuple[ClaimReference, ...] = (),
    confidence: float = 0.7,
    derivation_chain_digest: DigestRef = _TEST_DERIVATION_DIGEST,
):
    return build_governance_claim(
        GovernanceClaimSpec(
            school_id=school,
            task_id="task",
            claim_kind=kind,
            stance=stance,
            conclusion=f"{school}-{stance.value}",
            public_fact_refs=(
                ClaimReference(ClaimReferenceCategory.FACT, "fact", "v1"),
            ),
            certified_fact_refs=(),
            school_reason_refs=(),
            source_rule_refs=source_rule_refs
            or (ClaimReference(ClaimReferenceCategory.SOURCE_RULE, "rule", "v1"),),
            temporal_scope=scope or TemporalScope(TemporalLayer.NATAL),
            blockers=blockers,
            counterevidence=counterevidence,
            falsifier=(
                "registered contrary evidence"
                if kind in {ClaimKind.EVENT, ClaimKind.TIMING, ClaimKind.RISK}
                else ""
            ),
            confidence=confidence,
            evidence_grade=ClaimEvidenceGrade.DIRECT,
            derivation_chain_digest=derivation_chain_digest,
        ),
        _catalog(),
    )


def _arena(
    *claims,
    role: CapabilityRole = CapabilityRole.LEAD,
    kind: ClaimKind = ClaimKind.STRUCTURE,
    publication_status: PublicationStatus = PublicationStatus.PUBLISHED,
) -> ArbitrationArena:
    return ArbitrationArena(
        tuple(claims),
        ArbitrationContext((), FactCertificationRegistry(())),
        _catalog(),
        _registry(role, kind, publication_status),
        "v1",
    )


def test_arbitration_records_all_seven_gates_in_fixed_order() -> None:
    # Given: a qualified claim in a fully typed arena.
    arena = _arena(_claim())

    # When: the arena passes through the central arbitrator.
    result = arbitrate(arena)

    # Then: audit records prove the mandated seven-gate order.
    assert tuple(record.gate for record in result.gates) == tuple(GateName)
    assert result.decision is ArbitrationDecision.CONSENSUS


def test_temporally_incompatible_claims_are_not_compared() -> None:
    # Given: opposite positions scoped to natal and a distinct explicit year.
    natal = _claim(stance=ClaimStance.SUPPORT)
    liunian = _claim(
        stance=ClaimStance.OPPOSE,
        scope=TemporalScope(TemporalLayer.LIUNIAN, target_year=2026),
    )

    # When: the incompatible inputs are arbitrated.
    result = arbitrate(_arena(natal, liunian))

    # Then: the result retains separate scopes without declaring a conflict.
    assert result.decision is ArbitrationDecision.COMPLEMENTARY
    assert len(result.temporal_groups) == 2


def test_unpublished_or_evidence_only_capability_cannot_be_winner() -> None:
    # Given: an otherwise valid claim restricted to evidence-only use.
    arena = _arena(_claim(), role=CapabilityRole.EVIDENCE_ONLY)

    # When: capability applicability is evaluated exactly.
    result = arbitrate(arena)

    # Then: it remains audited but cannot create a winner state.
    assert result.decision is ArbitrationDecision.ABSTAIN
    assert result.applicable_claim_ids == ()


def test_unregistered_capability_stops_at_applicability_gate() -> None:
    # Given: a peer-school claim absent from the exact five-dimensional registry.
    claim = _claim(school="gao_dechen")

    # When: its otherwise valid evidence reaches the final qualification boundary.
    result = arbitrate(_arena(claim))

    # Then: it is retained for audit but produces a typed applicability abstention.
    assert result.decision is ArbitrationDecision.ABSTAIN
    assert result.audits[-1].gate is GateName.APPLICABILITY


def test_candidate_capability_stops_at_applicability_gate() -> None:
    # Given: an exact capability that has not been explicitly published.
    result = arbitrate(_arena(_claim(), publication_status=PublicationStatus.CANDIDATE))

    # When / Then: proposal status cannot silently grant a decision role.
    assert result.decision is ArbitrationDecision.ABSTAIN
    assert result.audits[-1].gate is GateName.APPLICABILITY


def test_typed_blocker_stops_claim_at_evidence_gate() -> None:
    # Given: a qualified claim with an explicit unresolved blocker.
    issue = ClaimIssue(ClaimIssueCode.INSUFFICIENT_EVIDENCE, "required input absent")
    claim = _claim(blockers=(issue,))

    # When: the evidence gate checks the closed blocker value.
    result = arbitrate(_arena(claim))

    # Then: it never reaches capability qualification.
    assert result.decision is ArbitrationDecision.ABSTAIN
    assert all(audit.gate is not GateName.APPLICABILITY for audit in result.audits)


def test_conditional_claim_uses_the_closed_conditional_decision_state() -> None:
    # Given: a qualified claim whose stance carries an explicit condition.
    result = arbitrate(_arena(_claim(stance=ClaimStance.CONDITIONAL)))

    # When / Then: decision output uses one of the approved closed states.
    assert result.decision is ArbitrationDecision.CONDITIONAL


def test_timing_scopes_remain_distinct_without_intersection_or_average() -> None:
    # Given: direct timing claims for two distinct explicit target years.
    early = _claim(
        kind=ClaimKind.TIMING,
        scope=TemporalScope(TemporalLayer.LIUNIAN, target_year=2025),
    )
    later = _claim(
        kind=ClaimKind.TIMING,
        scope=TemporalScope(TemporalLayer.LIUNIAN, target_year=2027),
    )

    # When: scoped timing evidence is arbitrated under one exact capability.
    result = arbitrate(_arena(early, later, kind=ClaimKind.TIMING))

    # Then: both declared windows survive as separate typed records.
    assert tuple(group.scope.target_year for group in result.temporal_groups) == (
        2025,
        2027,
    )


def test_high_risk_direct_conflict_preserves_both_claims_for_human_review() -> None:
    # Given: opposing direct event evidence in one compatible high-risk arena.
    support = _claim(stance=ClaimStance.SUPPORT, kind=ClaimKind.EVENT)
    oppose = _claim(stance=ClaimStance.OPPOSE, kind=ClaimKind.EVENT)

    # When: the typed conflict is arbitrated.
    arena = ArbitrationArena(
        (support, oppose),
        ArbitrationContext((), FactCertificationRegistry(())),
        _catalog(),
        _registry(kind=ClaimKind.EVENT),
        "v1",
    )
    result = arbitrate(arena)

    # Then: no claim is discarded from the audit record.
    assert set(result.retained_claim_ids) == {support.claim_id, oppose.claim_id}
    assert result.decision is ArbitrationDecision.HUMAN_REVIEW
