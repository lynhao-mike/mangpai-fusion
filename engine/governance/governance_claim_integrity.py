from __future__ import annotations

import math
from typing import TYPE_CHECKING, assert_never

from engine.governance.canonical import stable_object_id
from engine.governance.fact_values import DigestRef, TemporalScope
from engine.governance.governance_claim_identity import (
    ClaimContent,
    content_material,
    identity_material,
)
from engine.governance.governance_claim_values import (
    AdapterProvenance,
    ClaimEvidenceGrade,
    ClaimKind,
    ClaimReferenceCategory,
    ClaimStance,
    GovernanceReferenceCatalog,
    normalize_issues,
    normalize_references,
    reject as _reject,
    require_text as _text,
)

if TYPE_CHECKING:
    from engine.governance.governance_claim import GovernanceClaim, GovernanceClaimSpec


_CANONICAL_SCHOOLS = frozenset(
    {"ziping", "gao_dechen", "duan_jianye", "yang_qingjuan", "ren_fuhong"}
)


def canonical_specification(spec: GovernanceClaimSpec) -> GovernanceClaimSpec:
    from engine.governance.governance_claim import GovernanceClaimSpec

    if type(spec) is not GovernanceClaimSpec:
        _reject("CLAIM.SPECIFICATION", "specification", "invalid claim specification")
    _text("school_id", spec.school_id)
    _text("task_id", spec.task_id)
    _text("conclusion", spec.conclusion)
    if spec.school_id not in _CANONICAL_SCHOOLS:
        _reject("CLAIM.SCHOOL_ID", "school_id", "school ID must be canonical")
    if type(spec.claim_kind) is not ClaimKind or type(spec.stance) is not ClaimStance:
        _reject(
            "CLAIM.ENUM", "claim_kind", "claim kind and stance must be closed enums"
        )
    if type(spec.evidence_grade) is not ClaimEvidenceGrade:
        _reject(
            "CLAIM.EVIDENCE_GRADE", "evidence_grade", "evidence grade must be closed"
        )
    if type(spec.derivation_chain_digest) is not DigestRef:
        _reject(
            "CLAIM.DERIVATION_DIGEST",
            "derivation_chain_digest",
            "derivation chain digest must be an exact DigestRef",
        )
    if (
        spec.adapter_provenance is not None
        and type(spec.adapter_provenance) is not AdapterProvenance
    ):
        _reject("CLAIM.PROVENANCE", "adapter_provenance", "invalid adapter provenance")
    if type(spec.temporal_scope) is not TemporalScope:
        _reject("CLAIM.TEMPORAL_SCOPE", "temporal_scope", "scope is required")
    if (
        type(spec.confidence) is not float
        or not math.isfinite(spec.confidence)
        or not 0 <= spec.confidence <= 1
    ):
        _reject(
            "CLAIM.CONFIDENCE",
            "confidence",
            "confidence must be finite from zero through one",
        )
    facts = normalize_references(
        "public_fact_refs", spec.public_fact_refs, ClaimReferenceCategory.FACT
    )
    certified = normalize_references(
        "certified_fact_refs",
        spec.certified_fact_refs,
        ClaimReferenceCategory.CERTIFIED_FACT,
    )
    reasons = normalize_references(
        "school_reason_refs",
        spec.school_reason_refs,
        ClaimReferenceCategory.SCHOOL_REASON,
    )
    rules = normalize_references(
        "source_rule_refs", spec.source_rule_refs, ClaimReferenceCategory.SOURCE_RULE
    )
    blockers = normalize_issues(spec.blockers)
    counterevidence = normalize_references("counterevidence", spec.counterevidence)
    _text("falsifier", spec.falsifier) if spec.falsifier else None
    match spec.stance:
        case ClaimStance.ABSTAIN:
            if not blockers:
                _reject(
                    "CLAIM.ABSTAIN_REASON",
                    "blockers",
                    "abstain requires a typed reason issue",
                )
        case ClaimStance.SUPPORT | ClaimStance.OPPOSE | ClaimStance.CONDITIONAL:
            pass
        case unreachable:
            assert_never(unreachable)
    match spec.claim_kind:
        case ClaimKind.EVENT | ClaimKind.TIMING | ClaimKind.RISK:
            if not counterevidence and not spec.falsifier:
                _reject(
                    "CLAIM.HIGH_RISK",
                    "falsifier",
                    "high-risk kinds require a safeguard",
                )
        case ClaimKind.STRUCTURE | ClaimKind.SUPPORT:
            pass
        case unreachable:
            assert_never(unreachable)
    return GovernanceClaimSpec(
        school_id=spec.school_id,
        task_id=spec.task_id,
        claim_kind=spec.claim_kind,
        stance=spec.stance,
        conclusion=spec.conclusion,
        public_fact_refs=facts,
        certified_fact_refs=certified,
        school_reason_refs=reasons,
        source_rule_refs=rules,
        temporal_scope=spec.temporal_scope,
        blockers=blockers,
        counterevidence=counterevidence,
        falsifier=spec.falsifier,
        confidence=spec.confidence,
        evidence_grade=spec.evidence_grade,
        derivation_chain_digest=spec.derivation_chain_digest,
        adapter_provenance=spec.adapter_provenance,
    )


def claim_content(spec: GovernanceClaimSpec, claim_id: str) -> ClaimContent:
    return ClaimContent(
        claim_id=claim_id,
        specification=spec,
        public_fact_refs=spec.public_fact_refs,
        certified_fact_refs=spec.certified_fact_refs,
        school_reason_refs=spec.school_reason_refs,
        source_rule_refs=spec.source_rule_refs,
        blockers=spec.blockers,
        counterevidence=spec.counterevidence,
        falsifier=spec.falsifier,
        confidence=spec.confidence,
        evidence_grade=spec.evidence_grade.value,
        derivation_chain_digest=spec.derivation_chain_digest,
        adapter_provenance=spec.adapter_provenance,
    )


def validate_claim_integrity(
    claim: GovernanceClaim, catalog: GovernanceReferenceCatalog
) -> None:
    if type(catalog) is not GovernanceReferenceCatalog:
        _reject("CLAIM.CATALOG", "reference_catalog", "catalog is required")
    canonical_spec = canonical_specification(claim.specification)
    expected_id = str(
        stable_object_id("governance_claim", identity_material(canonical_spec))
    )
    expected_digest = DigestRef.from_material(
        content_material(claim_content(canonical_spec, expected_id))
    )
    expected_fields = (
        canonical_spec == claim.specification,
        expected_id == claim.claim_id,
        type(claim.content_digest) is DigestRef,
        expected_digest == claim.content_digest,
        canonical_spec.public_fact_refs == claim.public_fact_refs,
        canonical_spec.certified_fact_refs == claim.certified_fact_refs,
        canonical_spec.school_reason_refs == claim.school_reason_refs,
        canonical_spec.source_rule_refs == claim.source_rule_refs,
        canonical_spec.blockers == claim.blockers,
        canonical_spec.counterevidence == claim.counterevidence,
        canonical_spec.falsifier == claim.falsifier,
        canonical_spec.confidence == claim.confidence,
        canonical_spec.evidence_grade == claim.evidence_grade,
        canonical_spec.derivation_chain_digest == claim.derivation_chain_digest,
        canonical_spec.adapter_provenance == claim.adapter_provenance,
    )
    if not all(expected_fields):
        _reject(
            "CLAIM.INTEGRITY",
            "governance_claim",
            "claim envelope must equal its canonical specification, ID, and digest",
        )
    for references in (
        canonical_spec.public_fact_refs,
        canonical_spec.certified_fact_refs,
        canonical_spec.school_reason_refs,
        canonical_spec.source_rule_refs,
        canonical_spec.counterevidence,
    ):
        for reference in references:
            catalog.validate(reference)
