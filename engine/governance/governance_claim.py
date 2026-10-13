from __future__ import annotations

from dataclasses import InitVar, dataclass

from engine.governance.canonical import stable_object_id
from engine.governance.fact_values import DigestRef, TemporalScope
from engine.governance.governance_claim_identity import (
    content_material,
    identity_material,
)
from engine.governance.governance_claim_integrity import (
    canonical_specification,
    claim_content,
    validate_claim_integrity,
)
from engine.governance.governance_claim_values import (
    AdapterProvenance,
    ClaimEvidenceGrade,
    ClaimIssue,
    ClaimKind,
    ClaimReference,
    ClaimStance,
    GovernanceReferenceCatalog,
    reject as _reject,
)


@dataclass(frozen=True, slots=True)
class GovernanceClaimSpec:
    school_id: str
    task_id: str
    claim_kind: ClaimKind
    stance: ClaimStance
    conclusion: str
    public_fact_refs: tuple[ClaimReference, ...]
    certified_fact_refs: tuple[ClaimReference, ...]
    school_reason_refs: tuple[ClaimReference, ...]
    source_rule_refs: tuple[ClaimReference, ...]
    temporal_scope: TemporalScope
    blockers: tuple[ClaimIssue, ...]
    counterevidence: tuple[ClaimReference, ...]
    falsifier: str
    confidence: float
    evidence_grade: ClaimEvidenceGrade
    derivation_chain_digest: DigestRef
    adapter_provenance: AdapterProvenance | None = None


@dataclass(frozen=True, slots=True)
class GovernanceClaim:
    claim_id: str
    content_digest: DigestRef
    specification: GovernanceClaimSpec
    public_fact_refs: tuple[ClaimReference, ...]
    certified_fact_refs: tuple[ClaimReference, ...]
    school_reason_refs: tuple[ClaimReference, ...]
    source_rule_refs: tuple[ClaimReference, ...]
    blockers: tuple[ClaimIssue, ...]
    counterevidence: tuple[ClaimReference, ...]
    falsifier: str
    confidence: float
    evidence_grade: ClaimEvidenceGrade
    derivation_chain_digest: DigestRef
    adapter_provenance: AdapterProvenance | None
    reference_catalog: InitVar[GovernanceReferenceCatalog]

    def __post_init__(self, reference_catalog: GovernanceReferenceCatalog) -> None:
        validate_claim_integrity(self, reference_catalog)

    @property
    def school_id(self) -> str:
        return self.specification.school_id

    @property
    def task_id(self) -> str:
        return self.specification.task_id

    @property
    def claim_kind(self) -> ClaimKind:
        return self.specification.claim_kind

    @property
    def stance(self) -> ClaimStance:
        return self.specification.stance

    @property
    def temporal_scope(self) -> TemporalScope:
        return self.specification.temporal_scope


def build_governance_claim(
    spec: GovernanceClaimSpec, catalog: GovernanceReferenceCatalog
) -> GovernanceClaim:
    if (
        type(spec) is not GovernanceClaimSpec
        or type(catalog) is not GovernanceReferenceCatalog
    ):
        _reject(
            "CLAIM.BOUNDARY", "spec", "typed specification and catalog are required"
        )
    canonical_spec = canonical_specification(spec)
    claim_id = str(
        stable_object_id("governance_claim", identity_material(canonical_spec))
    )
    digest = DigestRef.from_material(
        content_material(claim_content(canonical_spec, claim_id))
    )
    return GovernanceClaim(
        claim_id=claim_id,
        content_digest=digest,
        specification=canonical_spec,
        public_fact_refs=canonical_spec.public_fact_refs,
        certified_fact_refs=canonical_spec.certified_fact_refs,
        school_reason_refs=canonical_spec.school_reason_refs,
        source_rule_refs=canonical_spec.source_rule_refs,
        blockers=canonical_spec.blockers,
        counterevidence=canonical_spec.counterevidence,
        falsifier=canonical_spec.falsifier,
        confidence=canonical_spec.confidence,
        evidence_grade=canonical_spec.evidence_grade,
        derivation_chain_digest=canonical_spec.derivation_chain_digest,
        adapter_provenance=canonical_spec.adapter_provenance,
        reference_catalog=catalog,
    )
