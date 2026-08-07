from __future__ import annotations

from engine.governance.arbitration_contracts import (
    ArbitrationDecision,
    ArbitrationProgress,
    ClaimVariantRef,
    GateName,
    GateRecord,
    variant_key,
)
from engine.governance.arbitration_gates import variant_refs
from engine.governance.arbitration_result import ArbitrationResult
from engine.governance.governance_claim import GovernanceClaim
from engine.governance.governance_claim_values import ClaimKind, ClaimStance


def _variant_claims(
    claims: tuple[GovernanceClaim, ...],
) -> dict[ClaimVariantRef, GovernanceClaim]:
    return {ClaimVariantRef.from_claim(claim): claim for claim in claims}


def _group_stances(progress: ArbitrationProgress) -> tuple[frozenset[ClaimStance], ...]:
    claims = _variant_claims(progress.applicable_claims)
    return tuple(
        frozenset(
            claims[variant].stance for variant in group.variants if variant in claims
        )
        for group in progress.temporal_groups
    )


def _is_high_risk(claims: tuple[GovernanceClaim, ...]) -> bool:
    return any(
        claim.claim_kind in {ClaimKind.EVENT, ClaimKind.TIMING, ClaimKind.RISK}
        for claim in claims
    )


def _decision(progress: ArbitrationProgress) -> ArbitrationDecision:
    if not progress.applicable_claims:
        return ArbitrationDecision.ABSTAIN
    stances = tuple(group for group in _group_stances(progress) if group)
    conflict = any(
        {ClaimStance.SUPPORT, ClaimStance.OPPOSE}.issubset(group) for group in stances
    )
    conditional = any(ClaimStance.CONDITIONAL in group for group in stances)
    if conflict and _is_high_risk(progress.applicable_claims):
        return ArbitrationDecision.HUMAN_REVIEW
    if conflict:
        return ArbitrationDecision.CONFLICT
    if conditional:
        return ArbitrationDecision.CONDITIONAL
    if len(stances) > 1:
        return ArbitrationDecision.COMPLEMENTARY
    return ArbitrationDecision.CONSENSUS


def _minority_variants(
    decision: ArbitrationDecision, claims: tuple[GovernanceClaim, ...]
) -> tuple[ClaimVariantRef, ...]:
    variants = _variant_claims(claims)
    match decision:
        case ArbitrationDecision.CONFLICT | ArbitrationDecision.HUMAN_REVIEW:
            selected = variants
        case ArbitrationDecision.CONDITIONAL:
            selected = {
                ref: claim
                for ref, claim in variants.items()
                if claim.stance in {ClaimStance.CONDITIONAL, ClaimStance.OPPOSE}
            }
        case (
            ArbitrationDecision.CONSENSUS
            | ArbitrationDecision.COMPLEMENTARY
            | ArbitrationDecision.ABSTAIN
        ):
            selected = {}
        case unreachable:
            from typing import assert_never

            assert_never(unreachable)
    return tuple(sorted(selected, key=variant_key))


def decision_gate(progress: ArbitrationProgress) -> ArbitrationResult:
    decision = _decision(progress)
    applicable = variant_refs(progress.applicable_claims)
    return ArbitrationResult.build(
        decision,
        variant_refs(progress.active_claims),
        applicable,
        _minority_variants(decision, progress.applicable_claims),
        progress.preserved_variants,
        progress.temporal_groups,
        progress.evidence_groups,
        progress.counterevidence_traces,
        progress.audits,
        (*progress.gates, GateRecord(GateName.DECISION, applicable, ())),
    )
