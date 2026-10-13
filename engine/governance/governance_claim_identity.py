from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from engine.governance.canonical import CanonicalValue
from engine.governance.fact_values import DigestRef, TemporalScope
from engine.governance.governance_claim_values import (
    AdapterProvenance,
    ClaimIssue,
    ClaimReference,
)

if TYPE_CHECKING:
    from engine.governance.governance_claim import (
        GovernanceClaim,
        GovernanceClaimSpec,
    )


CLAIM_SCHEMA: Final = "governance.claim.v1"


def _scope_material(scope: TemporalScope) -> CanonicalValue:
    return (
        scope.layer.value,
        scope.dayun_start_year,
        scope.dayun_end_year,
        scope.target_year,
    )


def _reference_material(references: tuple[ClaimReference, ...]) -> CanonicalValue:
    return tuple(
        (item.category.value, item.reference_id, item.version) for item in references
    )


def identity_material(spec: GovernanceClaimSpec) -> CanonicalValue:
    return (
        CLAIM_SCHEMA,
        spec.school_id,
        spec.task_id,
        spec.claim_kind.value,
        spec.stance.value,
        spec.conclusion,
        _scope_material(spec.temporal_scope),
    )


@dataclass(frozen=True, slots=True)
class ClaimContent:
    claim_id: str
    specification: GovernanceClaimSpec
    public_fact_refs: tuple[ClaimReference, ...]
    certified_fact_refs: tuple[ClaimReference, ...]
    school_reason_refs: tuple[ClaimReference, ...]
    source_rule_refs: tuple[ClaimReference, ...]
    blockers: tuple[ClaimIssue, ...]
    counterevidence: tuple[ClaimReference, ...]
    falsifier: str
    confidence: float
    evidence_grade: str
    derivation_chain_digest: DigestRef
    adapter_provenance: AdapterProvenance | None


def content_material(content: ClaimContent) -> CanonicalValue:
    provenance = content.adapter_provenance
    provenance_material: CanonicalValue = (
        None
        if provenance is None
        else (
            provenance.adapter_id,
            provenance.adapter_version,
            provenance.source_claim_ref,
        )
    )
    return (
        CLAIM_SCHEMA,
        content.claim_id,
        identity_material(content.specification),
        _reference_material(content.public_fact_refs),
        _reference_material(content.certified_fact_refs),
        _reference_material(content.school_reason_refs),
        _reference_material(content.source_rule_refs),
        tuple((issue.code.value, issue.detail) for issue in content.blockers),
        _reference_material(content.counterevidence),
        content.falsifier,
        content.confidence,
        content.evidence_grade,
        content.derivation_chain_digest.value,
        provenance_material,
    )


def content_from_claim(claim: GovernanceClaim) -> ClaimContent:
    return ClaimContent(
        claim_id=claim.claim_id,
        specification=claim.specification,
        public_fact_refs=claim.public_fact_refs,
        certified_fact_refs=claim.certified_fact_refs,
        school_reason_refs=claim.school_reason_refs,
        source_rule_refs=claim.source_rule_refs,
        blockers=claim.blockers,
        counterevidence=claim.counterevidence,
        falsifier=claim.falsifier,
        confidence=claim.confidence,
        evidence_grade=claim.evidence_grade.value,
        derivation_chain_digest=claim.derivation_chain_digest,
        adapter_provenance=claim.adapter_provenance,
    )
