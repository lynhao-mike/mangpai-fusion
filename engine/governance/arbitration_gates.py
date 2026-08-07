from __future__ import annotations

from typing import assert_never

from engine.governance.arbitration_contracts import (
    ArbitrationArena,
    ArbitrationIssueCode,
    ArbitrationProgress,
    ClaimAudit,
    ClaimVariantRef,
    CounterevidenceTrace,
    EvidenceGroup,
    GateName,
    GateRecord,
    TemporalGroup,
    variant_key,
)
from engine.governance.fact_values import TemporalScope
from engine.governance.governance_claim import GovernanceClaim
from engine.governance.governance_claim_integrity import validate_claim_integrity
from engine.governance.school_registry import (
    CapabilityAbstention,
    CapabilityIdentity,
    CapabilityQualification,
    CapabilityRole,
    LegacyCompatibilitySource,
    PeerSchool,
    UnknownSchool,
)


def variant_refs(claims: tuple[GovernanceClaim, ...]) -> tuple[ClaimVariantRef, ...]:
    return tuple(
        sorted((ClaimVariantRef.from_claim(claim) for claim in claims), key=variant_key)
    )


def initial_progress(arena: ArbitrationArena) -> ArbitrationProgress:
    unique = {
        (claim.claim_id, claim.content_digest.value): claim for claim in arena.claims
    }
    return ArbitrationProgress(
        tuple(
            sorted(
                unique.values(),
                key=lambda claim: (claim.claim_id, claim.content_digest.value),
            )
        ),
        (),
        (),
        variant_refs(tuple(unique.values())),
    )


def record(
    progress: ArbitrationProgress,
    gate: GateName,
    active: tuple[GovernanceClaim, ...],
    audits: tuple[ClaimAudit, ...],
) -> ArbitrationProgress:
    rejected = tuple(audit.owner for audit in audits if audit.gate is gate)
    return ArbitrationProgress(
        active,
        audits,
        (*progress.gates, GateRecord(gate, variant_refs(active), rejected)),
        progress.preserved_variants,
        progress.temporal_groups,
        progress.evidence_groups,
        progress.counterevidence_traces,
        progress.applicable_claims,
    )


def eligibility_gate(
    arena: ArbitrationArena, progress: ArbitrationProgress
) -> ArbitrationProgress:
    kept: list[GovernanceClaim] = []
    audits = progress.audits
    for claim in progress.active_claims:
        school = arena.school_registry.lookup_school(claim.school_id)
        match school:
            case PeerSchool():
                kept.append(claim)
            case LegacyCompatibilitySource() | UnknownSchool():
                audits = (
                    *audits,
                    ClaimAudit(
                        ClaimVariantRef.from_claim(claim),
                        GateName.ELIGIBILITY,
                        ArbitrationIssueCode.ELIGIBILITY_UNKNOWN_SCHOOL,
                    ),
                )
            case unreachable:
                assert_never(unreachable)
    return record(progress, GateName.ELIGIBILITY, tuple(kept), audits)


def _scope_key(scope: TemporalScope) -> tuple[str, int | None, int | None, int | None]:
    return (
        scope.layer.value,
        scope.dayun_start_year,
        scope.dayun_end_year,
        scope.target_year,
    )


def temporal_gate(progress: ArbitrationProgress) -> ArbitrationProgress:
    grouped: dict[TemporalScope, list[GovernanceClaim]] = {}
    for claim in progress.active_claims:
        grouped.setdefault(claim.temporal_scope, []).append(claim)
    groups = tuple(
        TemporalGroup(scope, variant_refs(tuple(claims)))
        for scope, claims in sorted(
            grouped.items(), key=lambda item: _scope_key(item[0])
        )
    )
    updated = ArbitrationProgress(
        progress.active_claims,
        progress.audits,
        progress.gates,
        progress.preserved_variants,
        groups,
        progress.evidence_groups,
        progress.counterevidence_traces,
        progress.applicable_claims,
    )
    return record(updated, GateName.TEMPORAL, updated.active_claims, updated.audits)


def evidence_gate(
    arena: ArbitrationArena, progress: ArbitrationProgress
) -> ArbitrationProgress:
    kept: list[GovernanceClaim] = []
    audits = progress.audits
    for claim in progress.active_claims:
        validate_claim_integrity(claim, arena.reference_catalog)
        if claim.blockers:
            audits = (
                *audits,
                ClaimAudit(
                    ClaimVariantRef.from_claim(claim),
                    GateName.EVIDENCE,
                    ArbitrationIssueCode.EVIDENCE_BLOCKED,
                ),
            )
        else:
            kept.append(claim)
    return record(progress, GateName.EVIDENCE, tuple(kept), audits)


def _source_identity(claim: GovernanceClaim) -> tuple[str, ...]:
    references = (
        *claim.public_fact_refs,
        *claim.certified_fact_refs,
        *claim.school_reason_refs,
        *claim.source_rule_refs,
    )
    return tuple(
        sorted(
            (
                *(
                    f"{reference.category.value}:{reference.reference_id}:{reference.version}"
                    for reference in references
                ),
                f"derivation:{claim.derivation_chain_digest.value}",
            )
        )
    )


def independence_gate(progress: ArbitrationProgress) -> ArbitrationProgress:
    grouped: dict[tuple[str, ...], list[GovernanceClaim]] = {}
    for claim in progress.active_claims:
        identity = _source_identity(claim)
        grouped.setdefault(identity, []).append(claim)
    evidence_groups = tuple(
        sorted(
            (
                EvidenceGroup(
                    identity,
                    variant_refs(tuple(members)),
                )
                for identity, members in grouped.items()
            ),
            key=lambda group: tuple(variant_key(variant) for variant in group.variants),
        )
    )
    updated = ArbitrationProgress(
        progress.active_claims,
        progress.audits,
        progress.gates,
        progress.preserved_variants,
        progress.temporal_groups,
        evidence_groups,
        progress.counterevidence_traces,
        progress.applicable_claims,
    )
    return record(updated, GateName.INDEPENDENCE, updated.active_claims, updated.audits)


def counterevidence_gate(progress: ArbitrationProgress) -> ArbitrationProgress:
    traces = tuple(
        CounterevidenceTrace(ClaimVariantRef.from_claim(claim), claim.counterevidence)
        for claim in progress.active_claims
        if claim.counterevidence
    )
    updated = ArbitrationProgress(
        progress.active_claims,
        progress.audits,
        progress.gates,
        progress.preserved_variants,
        progress.temporal_groups,
        progress.evidence_groups,
        tuple(sorted(traces, key=lambda trace: variant_key(trace.owner))),
        progress.applicable_claims,
    )
    return record(
        updated, GateName.COUNTEREVIDENCE, updated.active_claims, updated.audits
    )


def applicability_gate(
    arena: ArbitrationArena, progress: ArbitrationProgress
) -> ArbitrationProgress:
    applicable: list[GovernanceClaim] = []
    audits = progress.audits
    for claim in progress.active_claims:
        identity = CapabilityIdentity(
            claim.school_id,
            claim.task_id,
            claim.claim_kind,
            claim.evidence_grade,
            arena.capability_version,
        )
        result = arena.school_registry.lookup_capability(identity)
        match result:
            case CapabilityQualification(
                role=CapabilityRole.LEAD | CapabilityRole.CO_LEAD
            ):
                applicable.append(claim)
            case (
                CapabilityQualification(
                    role=CapabilityRole.EVIDENCE_ONLY | CapabilityRole.ABSTAIN
                )
                | CapabilityAbstention()
            ):
                audits = (
                    *audits,
                    ClaimAudit(
                        ClaimVariantRef.from_claim(claim),
                        GateName.APPLICABILITY,
                        ArbitrationIssueCode.CAPABILITY_ABSTAIN,
                    ),
                )
            case unreachable:
                assert_never(unreachable)
    updated = ArbitrationProgress(
        progress.active_claims,
        audits,
        progress.gates,
        progress.preserved_variants,
        progress.temporal_groups,
        progress.evidence_groups,
        progress.counterevidence_traces,
        tuple(applicable),
    )
    return record(
        updated, GateName.APPLICABILITY, updated.applicable_claims, updated.audits
    )
