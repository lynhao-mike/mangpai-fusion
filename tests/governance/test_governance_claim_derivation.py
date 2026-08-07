from __future__ import annotations

import pytest

from engine.governance import (
    ClaimEvidenceGrade,
    ClaimKind,
    ClaimReference,
    ClaimReferenceCategory,
    ClaimStance,
    DigestRef,
    GovernanceClaim,
    GovernanceClaimContractError,
    GovernanceClaimSpec,
    GovernanceReferenceCatalog,
    ReferenceRegistration,
    TemporalLayer,
    TemporalScope,
    build_governance_claim,
)


def _catalog() -> GovernanceReferenceCatalog:
    return GovernanceReferenceCatalog(
        registrations=(
            ReferenceRegistration(ClaimReferenceCategory.FACT, "fact-a", "facts-1"),
            ReferenceRegistration(
                ClaimReferenceCategory.CERTIFIED_FACT, "fact-certified", "cert-2"
            ),
            ReferenceRegistration(
                ClaimReferenceCategory.SCHOOL_REASON, "reason-a", "school-3"
            ),
            ReferenceRegistration(
                ClaimReferenceCategory.SOURCE_RULE, "rule-a", "rules-4"
            ),
        )
    )


def _spec(derivation_chain_digest: DigestRef) -> GovernanceClaimSpec:
    return GovernanceClaimSpec(
        school_id="ziping",
        task_id="structure.assessment",
        claim_kind=ClaimKind.STRUCTURE,
        stance=ClaimStance.SUPPORT,
        conclusion="The registered structure condition holds.",
        public_fact_refs=(
            ClaimReference(ClaimReferenceCategory.FACT, "fact-a", "facts-1"),
        ),
        certified_fact_refs=(
            ClaimReference(
                ClaimReferenceCategory.CERTIFIED_FACT, "fact-certified", "cert-2"
            ),
        ),
        school_reason_refs=(
            ClaimReference(
                ClaimReferenceCategory.SCHOOL_REASON, "reason-a", "school-3"
            ),
        ),
        source_rule_refs=(
            ClaimReference(ClaimReferenceCategory.SOURCE_RULE, "rule-a", "rules-4"),
        ),
        temporal_scope=TemporalScope(layer=TemporalLayer.NATAL),
        blockers=(),
        counterevidence=(),
        falsifier="A registered contrary structure result.",
        confidence=0.62,
        evidence_grade=ClaimEvidenceGrade.CORROBORATED,
        derivation_chain_digest=derivation_chain_digest,
    )


def test_governance_claim_spec_requires_explicit_derivation_digest() -> None:
    # Given: every native claim field except the derivation chain digest.
    # When / Then: construction fails before an unauditable claim can exist.
    with pytest.raises(TypeError, match="derivation_chain_digest"):
        GovernanceClaimSpec(
            school_id="ziping",
            task_id="structure.assessment",
            claim_kind=ClaimKind.STRUCTURE,
            stance=ClaimStance.SUPPORT,
            conclusion="The registered structure condition holds.",
            public_fact_refs=(
                ClaimReference(ClaimReferenceCategory.FACT, "fact-a", "facts-1"),
            ),
            certified_fact_refs=(
                ClaimReference(
                    ClaimReferenceCategory.CERTIFIED_FACT,
                    "fact-certified",
                    "cert-2",
                ),
            ),
            school_reason_refs=(
                ClaimReference(
                    ClaimReferenceCategory.SCHOOL_REASON, "reason-a", "school-3"
                ),
            ),
            source_rule_refs=(
                ClaimReference(ClaimReferenceCategory.SOURCE_RULE, "rule-a", "rules-4"),
            ),
            temporal_scope=TemporalScope(layer=TemporalLayer.NATAL),
            blockers=(),
            counterevidence=(),
            falsifier="A registered contrary structure result.",
            confidence=0.62,
            evidence_grade=ClaimEvidenceGrade.CORROBORATED,
        )


def test_governance_claim_rejects_non_digest_derivation_value() -> None:
    # Given: a specification with ordinary text where an exact digest is required.
    specification = _spec("not-a-digest")

    # When / Then: the canonical claim boundary rejects the wrong runtime type.
    with pytest.raises(GovernanceClaimContractError, match="DERIVATION_DIGEST"):
        build_governance_claim(specification, _catalog())


def test_direct_governance_claim_rejects_forged_derivation_digest() -> None:
    # Given: a valid built claim and a different valid digest value.
    baseline = build_governance_claim(
        _spec(DigestRef.from_material(("source", "legacy-a"))), _catalog()
    )
    forged = DigestRef.from_material(("source", "legacy-b"))

    # When / Then: direct construction cannot diverge from the public specification.
    with pytest.raises(GovernanceClaimContractError, match="CLAIM.INTEGRITY"):
        GovernanceClaim(
            claim_id=baseline.claim_id,
            content_digest=baseline.content_digest,
            specification=baseline.specification,
            public_fact_refs=baseline.public_fact_refs,
            certified_fact_refs=baseline.certified_fact_refs,
            school_reason_refs=baseline.school_reason_refs,
            source_rule_refs=baseline.source_rule_refs,
            blockers=baseline.blockers,
            counterevidence=baseline.counterevidence,
            falsifier=baseline.falsifier,
            confidence=baseline.confidence,
            evidence_grade=baseline.evidence_grade,
            derivation_chain_digest=forged,
            adapter_provenance=baseline.adapter_provenance,
            reference_catalog=_catalog(),
        )


def test_derivation_chain_changes_content_digest_without_changing_claim_identity() -> (
    None
):
    # Given: equivalent claim semantics from two independently identified derivations.
    first = build_governance_claim(
        _spec(DigestRef.from_material(("source", "legacy-a"))), _catalog()
    )
    second = build_governance_claim(
        _spec(DigestRef.from_material(("source", "legacy-b"))), _catalog()
    )

    # When / Then: derivation changes content integrity but not semantic identity.
    assert first.claim_id == second.claim_id
    assert first.content_digest != second.content_digest
    assert first.derivation_chain_digest != second.derivation_chain_digest
