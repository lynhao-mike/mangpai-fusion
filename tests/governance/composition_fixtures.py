from __future__ import annotations

from engine.governance import (
    ClaimEvidenceGrade,
    ClaimKind,
    ClaimReference,
    ClaimReferenceCategory,
    ClaimStance,
    DigestRef,
    GovernanceClaim,
    GovernanceClaimSpec,
    GovernanceReferenceCatalog,
    ReferenceRegistration,
    TemporalLayer,
    TemporalScope,
    build_governance_claim,
)


def catalog() -> GovernanceReferenceCatalog:
    return GovernanceReferenceCatalog(
        (
            ReferenceRegistration(ClaimReferenceCategory.FACT, "fact", "v1"),
            ReferenceRegistration(ClaimReferenceCategory.FACT, "counter", "v1"),
            ReferenceRegistration(ClaimReferenceCategory.SOURCE_RULE, "rule", "v1"),
        )
    )


def claim(
    school_id: str,
    *,
    stance: ClaimStance = ClaimStance.SUPPORT,
    claim_kind: ClaimKind = ClaimKind.STRUCTURE,
    temporal_scope: TemporalScope | None = None,
    counterevidence: tuple[ClaimReference, ...] = (),
    falsifier: str = "registered contrary structure evidence",
    evidence_grade: ClaimEvidenceGrade = ClaimEvidenceGrade.DIRECT,
) -> GovernanceClaim:
    return build_governance_claim(
        GovernanceClaimSpec(
            school_id=school_id,
            task_id="structure.assessment",
            claim_kind=claim_kind,
            stance=stance,
            conclusion=f"{school_id} structure evidence",
            public_fact_refs=(
                ClaimReference(ClaimReferenceCategory.FACT, "fact", "v1"),
            ),
            certified_fact_refs=(),
            school_reason_refs=(),
            source_rule_refs=(
                ClaimReference(ClaimReferenceCategory.SOURCE_RULE, "rule", "v1"),
            ),
            temporal_scope=temporal_scope or TemporalScope(TemporalLayer.NATAL),
            blockers=(),
            counterevidence=counterevidence,
            falsifier=falsifier,
            confidence=0.7,
            evidence_grade=evidence_grade,
            derivation_chain_digest=DigestRef.from_material(("test", school_id)),
        ),
        catalog(),
    )
