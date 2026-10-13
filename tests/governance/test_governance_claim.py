from __future__ import annotations

from dataclasses import FrozenInstanceError
from math import nan

import pytest

from engine.governance import (
    ClaimEvidenceGrade,
    ClaimIssue,
    ClaimIssueCode,
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


_TEST_DERIVATION_DIGEST = DigestRef.from_material(("test", "governance-claim"))


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


def _ref(category: ClaimReferenceCategory, ref_id: str, version: str) -> ClaimReference:
    return ClaimReference(category=category, reference_id=ref_id, version=version)


def _spec(
    *,
    claim_kind: ClaimKind = ClaimKind.STRUCTURE,
    stance: ClaimStance = ClaimStance.SUPPORT,
    public_fact_refs: tuple[ClaimReference, ...] | None = None,
    blockers: tuple[ClaimIssue, ...] = (),
    counterevidence: tuple[ClaimReference, ...] = (),
    falsifier: str = "A registered contrary structure result.",
    confidence: float = 0.62,
) -> GovernanceClaimSpec:
    return GovernanceClaimSpec(
        school_id="ziping",
        task_id="structure.assessment",
        claim_kind=claim_kind,
        stance=stance,
        conclusion="The registered structure condition holds.",
        public_fact_refs=(
            (_ref(ClaimReferenceCategory.FACT, "fact-a", "facts-1"),)
            if public_fact_refs is None
            else public_fact_refs
        ),
        certified_fact_refs=(
            _ref(ClaimReferenceCategory.CERTIFIED_FACT, "fact-certified", "cert-2"),
        ),
        school_reason_refs=(
            _ref(ClaimReferenceCategory.SCHOOL_REASON, "reason-a", "school-3"),
        ),
        source_rule_refs=(
            _ref(ClaimReferenceCategory.SOURCE_RULE, "rule-a", "rules-4"),
        ),
        temporal_scope=TemporalScope(layer=TemporalLayer.NATAL),
        blockers=blockers,
        counterevidence=counterevidence,
        falsifier=falsifier,
        confidence=confidence,
        evidence_grade=ClaimEvidenceGrade.CORROBORATED,
        derivation_chain_digest=_TEST_DERIVATION_DIGEST,
    )


def test_governance_claim_is_frozen_deep_immutable_and_normalizes_refs() -> None:
    # Given: a valid claim specification with repeated and permuted references.
    fact = _ref(ClaimReferenceCategory.FACT, "fact-a", "facts-1")
    spec = _spec(public_fact_refs=(fact, fact))

    # When: the governance claim is built through its readonly catalog boundary.
    claim = build_governance_claim(spec, _catalog())

    # Then: its public fields are immutable and evidence references are canonical.
    assert claim.public_fact_refs == (fact,)
    with pytest.raises(FrozenInstanceError):
        claim.__setattr__("confidence", 0.1)


def test_governance_claim_rejects_abstention_without_typed_reason_issue() -> None:
    # Given: an abstention whose blockers are empty.
    spec = _spec(stance=ClaimStance.ABSTAIN, blockers=())

    # When / Then: construction fails closed.
    with pytest.raises(GovernanceClaimContractError, match="ABSTAIN_REASON"):
        build_governance_claim(spec, _catalog())


def test_governance_claim_requires_counterevidence_or_falsifier_for_high_risk_kind() -> (
    None
):
    # Given: a high-risk event claim without either required safeguard.
    spec = _spec(
        claim_kind=ClaimKind.EVENT,
        falsifier="",
        counterevidence=(),
    )

    # When / Then: construction rejects the unsupported claim.
    with pytest.raises(GovernanceClaimContractError, match="HIGH_RISK"):
        build_governance_claim(spec, _catalog())


def test_governance_claim_rejects_unknown_and_wrong_version_references() -> None:
    # Given: one missing reference and one known ID at a wrong version.
    missing = _spec(
        public_fact_refs=(_ref(ClaimReferenceCategory.FACT, "fact-missing", "facts-1"),)
    )
    wrong_version = _spec(
        public_fact_refs=(_ref(ClaimReferenceCategory.FACT, "fact-a", "facts-unknown"),)
    )

    # When / Then: neither can be silently admitted by the catalog.
    with pytest.raises(GovernanceClaimContractError, match="REFERENCE_UNKNOWN"):
        build_governance_claim(missing, _catalog())
    with pytest.raises(GovernanceClaimContractError, match="REFERENCE_VERSION"):
        build_governance_claim(wrong_version, _catalog())


def test_governance_claim_separates_stable_identity_from_content_digest() -> None:
    # Given: semantically identical claims with refs in a different order and content variance.
    baseline = build_governance_claim(_spec(), _catalog())
    reordered = build_governance_claim(
        _spec(
            public_fact_refs=(_ref(ClaimReferenceCategory.FACT, "fact-a", "facts-1"),),
        ),
        _catalog(),
    )
    changed_confidence = build_governance_claim(_spec(confidence=0.31), _catalog())

    # When / Then: ordering is irrelevant, while content changes retain assertion identity.
    assert baseline == reordered
    assert baseline.claim_id == changed_confidence.claim_id
    assert baseline.content_digest != changed_confidence.content_digest


def test_governance_claim_normalizes_its_public_specification_before_digesting() -> (
    None
):
    # Given: equivalent specs with duplicate and differently ordered collections.
    fact = _ref(ClaimReferenceCategory.FACT, "fact-a", "facts-1")
    issue = ClaimIssue(ClaimIssueCode.INSUFFICIENT_EVIDENCE, "missing input")
    duplicate = _spec(public_fact_refs=(fact, fact), blockers=(issue, issue))
    canonical = _spec(public_fact_refs=(fact,), blockers=(issue,))

    # When: both values cross the canonical claim boundary.
    first = build_governance_claim(duplicate, _catalog())
    second = build_governance_claim(canonical, _catalog())

    # Then: equal digests correspond to equal complete public envelopes.
    assert first == second
    assert first.specification == second.specification
    assert first.content_digest == second.content_digest


def test_direct_governance_claim_rejects_forged_public_content_and_identity() -> None:
    # Given: a canonical claim and a valid reference catalog.
    baseline = build_governance_claim(_spec(), _catalog())
    fact = _ref(ClaimReferenceCategory.FACT, "fact-a", "facts-1")

    # When / Then: direct construction diverges from the canonical specification.
    with pytest.raises(GovernanceClaimContractError, match="CLAIM.INTEGRITY"):
        GovernanceClaim(
            claim_id=baseline.claim_id,
            content_digest=baseline.content_digest,
            specification=baseline.specification,
            public_fact_refs=(fact, fact),
            certified_fact_refs=baseline.certified_fact_refs,
            school_reason_refs=baseline.school_reason_refs,
            source_rule_refs=baseline.source_rule_refs,
            blockers=baseline.blockers,
            counterevidence=baseline.counterevidence,
            falsifier=baseline.falsifier,
            confidence=baseline.confidence,
            evidence_grade=baseline.evidence_grade,
            derivation_chain_digest=baseline.derivation_chain_digest,
            adapter_provenance=baseline.adapter_provenance,
            reference_catalog=_catalog(),
        )
    with pytest.raises(GovernanceClaimContractError, match="CLAIM.INTEGRITY"):
        GovernanceClaim(
            claim_id="governance_claim:forged",
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
            derivation_chain_digest=baseline.derivation_chain_digest,
            adapter_provenance=baseline.adapter_provenance,
            reference_catalog=_catalog(),
        )
    with pytest.raises(GovernanceClaimContractError, match="CLAIM.INTEGRITY"):
        GovernanceClaim(
            claim_id=baseline.claim_id,
            content_digest=baseline.content_digest.from_material(("forged",)),
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
            derivation_chain_digest=baseline.derivation_chain_digest,
            adapter_provenance=baseline.adapter_provenance,
            reference_catalog=_catalog(),
        )


@pytest.mark.parametrize("confidence", (-0.01, 1.01, nan))
def test_governance_claim_rejects_confidence_outside_closed_range(
    confidence: float,
) -> None:
    # Given: a numeric value outside the permitted closed interval.
    spec = _spec(confidence=confidence)

    # When / Then: evidence grade does not relax confidence validation.
    with pytest.raises(GovernanceClaimContractError, match="CONFIDENCE"):
        build_governance_claim(spec, _catalog())


def test_governance_claim_abstention_accepts_typed_reason_issue() -> None:
    # Given: an abstention with a typed, auditable reason.
    issue = ClaimIssue(ClaimIssueCode.INSUFFICIENT_EVIDENCE, "missing required input")
    spec = _spec(stance=ClaimStance.ABSTAIN, blockers=(issue,))

    # When: it is projected into the public envelope.
    claim = build_governance_claim(spec, _catalog())

    # Then: the exact typed issue is preserved.
    assert claim.blockers == (issue,)
