from __future__ import annotations

from dataclasses import dataclass
from typing import assert_never

from engine.claims.domain import Claim
from engine.decision.models import SchoolClaim
from engine.application.governance_claim_adapter_values import (
    DOMAIN_KINDS,
    SCHOOL_METADATA_KEYS,
    SCHOOL_ROLE_VALUES,
    AdaptationResult,
    catalog_loss,
    loss,
    metadata_text,
    school_id,
    school_kind,
    school_references,
    school_scope,
    school_stance,
)
from engine.governance import (
    AdapterProvenance,
    ClaimEvidenceGrade,
    ClaimIssueCode,
    ClaimKind,
    ClaimReference,
    ClaimReferenceCategory,
    ClaimStance,
    DigestRef,
    GovernanceClaimContractError,
    GovernanceClaimSpec,
    GovernanceReferenceCatalog,
    TemporalScope,
    build_governance_claim,
)
from engine.governance.governance_claim_derivation import derivation_chain_digest


_ADAPTER_VERSION = "1"


@dataclass(frozen=True, slots=True)
class _AdaptationInput:
    school_id: str
    task_id: str
    claim_kind: ClaimKind
    stance: ClaimStance
    conclusion: str
    temporal_scope: TemporalScope
    confidence: float
    falsifier: str
    references: tuple[ClaimReference, ...]
    provenance: AdapterProvenance
    derivation_chain_digest: DigestRef


def _spec(input: _AdaptationInput) -> GovernanceClaimSpec:
    reasons = tuple(
        reference
        for reference in input.references
        if reference.category is ClaimReferenceCategory.SCHOOL_REASON
    )
    rules = tuple(
        reference
        for reference in input.references
        if reference.category is ClaimReferenceCategory.SOURCE_RULE
    )
    return GovernanceClaimSpec(
        school_id=input.school_id,
        task_id=input.task_id,
        claim_kind=input.claim_kind,
        stance=input.stance,
        conclusion=input.conclusion,
        public_fact_refs=(),
        certified_fact_refs=(),
        school_reason_refs=reasons,
        source_rule_refs=rules,
        temporal_scope=input.temporal_scope,
        blockers=(),
        counterevidence=(),
        falsifier=input.falsifier,
        confidence=input.confidence,
        evidence_grade=ClaimEvidenceGrade.INFERENTIAL,
        derivation_chain_digest=input.derivation_chain_digest,
        adapter_provenance=input.provenance,
    )


def adapt_decision_school_claim(
    claim: SchoolClaim, catalog: GovernanceReferenceCatalog
) -> AdaptationResult:
    if type(claim) is not SchoolClaim:
        return loss(ClaimIssueCode.ADAPTER_INPUT_INVALID, "expected SchoolClaim")
    if claim.role_granted_by_l1 not in SCHOOL_ROLE_VALUES:
        return loss(ClaimIssueCode.LEGACY_METADATA_INVALID, "legacy role is invalid")
    if claim.role_granted_by_l1 == "abstain":
        return loss(ClaimIssueCode.LEGACY_ROLE_ABSTAIN, "abstaining role cannot speak")
    if set(claim.metadata) - SCHOOL_METADATA_KEYS:
        return loss(
            ClaimIssueCode.LEGACY_METADATA_UNAPPROVED,
            "metadata contains an unapproved key",
        )
    canonical_school = school_id(claim.school)
    if canonical_school is None:
        return loss(ClaimIssueCode.UNSUPPORTED_LEGACY_CLAIM, "unknown legacy school")
    claim_kind = school_kind(claim)
    if claim_kind is None:
        return loss(
            ClaimIssueCode.UNSUPPORTED_LEGACY_CLAIM, "legacy claim kind is unsupported"
        )
    stance = school_stance(claim)
    if stance is None:
        return loss(
            ClaimIssueCode.LEGACY_METADATA_INVALID, "stance is not explicitly mapped"
        )
    temporal_scope = school_scope(claim)
    if temporal_scope is None:
        return loss(
            ClaimIssueCode.TEMPORAL_SCOPE_MISSING, "scope is not explicitly mapped"
        )
    task_id = metadata_text(claim, "task_id")
    version = metadata_text(claim, "reference_version")
    if task_id is None or version is None:
        return loss(
            ClaimIssueCode.LEGACY_METADATA_INVALID, "task or version is missing"
        )
    references = school_references(claim, version)
    if references is None:
        return loss(
            ClaimIssueCode.LEGACY_REFERENCE_INVALID, "legacy references are invalid"
        )
    provenance = AdapterProvenance(
        "decision-school-claim-adapter", _ADAPTER_VERSION, claim.claim_id
    )
    try:
        adapted = build_governance_claim(
            _spec(
                _AdaptationInput(
                    canonical_school,
                    task_id,
                    claim_kind,
                    stance,
                    claim.statement,
                    temporal_scope,
                    claim.confidence,
                    claim.falsifier,
                    references,
                    provenance,
                    derivation_chain_digest(
                        (provenance.source_claim_ref,),
                        provenance,
                        (
                            ("task_id", task_id),
                            ("stance", stance.value),
                            ("temporal_scope", temporal_scope.layer.value),
                            ("reference_version", version),
                        ),
                    ),
                )
            ),
            catalog,
        )
    except GovernanceClaimContractError as error:
        return catalog_loss(error)
    return AdaptationResult(adapted, ())


def adapt_domain_claim(
    claim: Claim,
    catalog: GovernanceReferenceCatalog,
    temporal_scope: TemporalScope,
    requested_stance: ClaimStance | None = None,
) -> AdaptationResult:
    if type(claim) is not Claim:
        return loss(ClaimIssueCode.ADAPTER_INPUT_INVALID, "expected Claim")
    if claim.applicability_snapshot:
        return loss(
            ClaimIssueCode.LEGACY_CONTEXT_UNAPPROVED,
            "applicability context is not an approved adapter input",
        )
    match requested_stance:
        case ClaimStance.CONDITIONAL:
            return loss(
                ClaimIssueCode.LEGACY_CONDITIONAL_LOSS,
                "legacy Claim lacks conditional stance",
            )
        case ClaimStance.ABSTAIN:
            return loss(
                ClaimIssueCode.LEGACY_ABSTENTION_LOSS,
                "legacy Claim lacks abstain stance",
            )
        case ClaimStance.SUPPORT | ClaimStance.OPPOSE | None:
            pass
        case unreachable:
            assert_never(unreachable)
    canonical_school = school_id(claim.school_id)
    claim_kind = DOMAIN_KINDS.get(claim.claim_type)
    if claim_kind is None:
        return loss(
            ClaimIssueCode.UNSUPPORTED_LEGACY_CLAIM,
            "legacy claim kind is unsupported",
        )
    if canonical_school is None:
        return loss(ClaimIssueCode.UNSUPPORTED_LEGACY_CLAIM, "unknown legacy school")
    version = "legacy-v1"
    references = tuple(
        ClaimReference(ClaimReferenceCategory.SCHOOL_REASON, item.evidence_id, version)
        for item in claim.evidence
    ) + tuple(
        ClaimReference(ClaimReferenceCategory.SOURCE_RULE, item.rule_id, version)
        for item in claim.evidence
    )
    stance = requested_stance or ClaimStance(claim.stance)
    provenance = AdapterProvenance(
        "domain-claim-adapter", _ADAPTER_VERSION, claim.claim_id
    )
    try:
        adapted = build_governance_claim(
            _spec(
                _AdaptationInput(
                    canonical_school,
                    claim.task_id,
                    claim_kind,
                    stance,
                    claim.statement,
                    temporal_scope,
                    claim.confidence,
                    claim.falsifier,
                    references,
                    provenance,
                    derivation_chain_digest(
                        (provenance.source_claim_ref,),
                        provenance,
                        (
                            ("school_id", canonical_school),
                            ("task_id", claim.task_id),
                            ("claim_kind", claim_kind.value),
                            ("stance", stance.value),
                            ("temporal_scope", temporal_scope.layer.value),
                            ("reference_version", version),
                        ),
                    ),
                )
            ),
            catalog,
        )
    except GovernanceClaimContractError as error:
        return catalog_loss(error)
    return AdaptationResult(adapted, ())
