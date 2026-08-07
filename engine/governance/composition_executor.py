from __future__ import annotations

from typing import Final

from engine.governance.composition_contracts import (
    CompositionExecutionMode,
    CompositionOutcome,
    CompositionResult,
    composition_result_digest,
    reject,
)
from engine.governance.composition_templates import (
    CompositionRegistry,
    CompositionTemplate,
    CompositionTemplateStatus,
)
from engine.governance.fact_values import TemporalScope
from engine.governance.governance_claim import GovernanceClaim
from engine.governance.governance_claim_values import ClaimEvidenceGrade, ClaimKind


_GRADE_ORDER: Final = {
    ClaimEvidenceGrade.INFERENTIAL: 1,
    ClaimEvidenceGrade.CORROBORATED: 2,
    ClaimEvidenceGrade.DIRECT: 3,
}


def _canonical_components(
    components: tuple[GovernanceClaim, ...],
) -> tuple[GovernanceClaim, ...]:
    return tuple(
        sorted(
            components, key=lambda claim: (claim.claim_id, claim.content_digest.value)
        )
    )


def _result(
    template_id: str,
    version: str,
    outcome: CompositionOutcome,
    components: tuple[GovernanceClaim, ...],
    output_kind: ClaimKind | None,
    output_scope: TemporalScope | None,
    evidence_grade: ClaimEvidenceGrade | None,
    issue_code: str | None,
) -> CompositionResult:
    return CompositionResult(
        outcome,
        template_id,
        version,
        composition_result_digest(
            outcome,
            template_id,
            version,
            components,
            output_kind,
            output_scope,
            evidence_grade,
            issue_code,
        ),
        components,
        output_kind,
        output_scope,
        evidence_grade,
        issue_code,
    )


def _cap(
    components: tuple[GovernanceClaim, ...], cap: ClaimEvidenceGrade
) -> ClaimEvidenceGrade:
    strongest = max(
        (claim.evidence_grade for claim in components),
        key=lambda grade: _GRADE_ORDER[grade],
    )
    if _GRADE_ORDER[strongest] <= _GRADE_ORDER[cap]:
        return strongest
    return cap


def _invalid(
    template: CompositionTemplate, components: tuple[GovernanceClaim, ...]
) -> str | None:
    required_count = sum(slot.count for slot in template.required_component_slots)
    if len(components) < required_count:
        return "COMPOSITION.COMPONENTS_REQUIRED"
    variants = {(claim.claim_id, claim.content_digest.value) for claim in components}
    schools = {claim.school_id for claim in components}
    if len(variants) < required_count or len(schools) < required_count:
        return "COMPOSITION.INDEPENDENT_COMPONENTS_REQUIRED"
    if any(
        claim.claim_kind not in template.accepted_claim_kinds for claim in components
    ):
        return "COMPOSITION.CLAIM_KIND_INCOMPATIBLE"
    if any(claim.stance.value not in template.accepted_stances for claim in components):
        return "COMPOSITION.STANCE_INCOMPATIBLE"
    if any(claim.task_id not in template.accepted_task_ids for claim in components):
        return "COMPOSITION.TASK_INCOMPATIBLE"
    if any(
        claim.temporal_scope.layer.value not in template.accepted_temporal_layers
        for claim in components
    ):
        return "COMPOSITION.TEMPORAL_INCOMPATIBLE"
    if len({claim.temporal_scope for claim in components}) != 1:
        return "COMPOSITION.TEMPORAL_INCOMPATIBLE"
    return None


def execute_composition(
    registry: CompositionRegistry,
    *,
    template_id: str,
    version: str,
    components: tuple[GovernanceClaim, ...],
    mode: CompositionExecutionMode,
) -> CompositionResult:
    if type(registry) is not CompositionRegistry:
        reject("COMPOSITION.REGISTRY", "registry", "must be a composition registry")
    if type(template_id) is not str or not template_id:
        reject("COMPOSITION.TEMPLATE_ID", "template_id", "must be nonempty")
    if type(version) is not str or not version:
        reject("COMPOSITION.VERSION", "version", "must be nonempty")
    if type(components) is not tuple or any(
        type(component) is not GovernanceClaim for component in components
    ):
        reject("COMPOSITION.COMPONENTS", "components", "must be immutable claims")
    if type(mode) is not CompositionExecutionMode:
        reject("COMPOSITION.MODE", "mode", "must be explicit execution mode")
    ordered = _canonical_components(components)
    found = registry.lookup(template_id, version)
    if not isinstance(found, CompositionTemplate):
        return _result(
            template_id,
            version,
            CompositionOutcome.UNSUPPORTED,
            ordered,
            None,
            None,
            None,
            found.issue_code,
        )
    if (
        mode is CompositionExecutionMode.PRODUCTION
        and found.status is CompositionTemplateStatus.SYNTHETIC_ONLY
    ):
        return _result(
            template_id,
            version,
            CompositionOutcome.UNSUPPORTED,
            ordered,
            None,
            None,
            None,
            "COMPOSITION.PRODUCTION_FORBIDDEN",
        )
    issue = _invalid(found, ordered)
    if issue in {
        "COMPOSITION.COMPONENTS_REQUIRED",
        "COMPOSITION.INDEPENDENT_COMPONENTS_REQUIRED",
    }:
        return _result(
            template_id,
            version,
            CompositionOutcome.CONDITIONAL,
            ordered,
            None,
            None,
            None,
            issue,
        )
    if issue is not None:
        return _result(
            template_id,
            version,
            CompositionOutcome.CONFLICT,
            ordered,
            None,
            None,
            None,
            issue,
        )
    stances = {claim.stance.value for claim in ordered}
    if (
        "strong_contradiction" in found.human_review_conditions
        and "support" in stances
        and "oppose" in stances
    ):
        return _result(
            template_id,
            version,
            CompositionOutcome.HUMAN_REVIEW,
            ordered,
            None,
            None,
            None,
            "COMPOSITION.STRONG_CONTRADICTION",
        )
    return _result(
        template_id,
        version,
        CompositionOutcome.COMPOSED,
        ordered,
        found.output_kind,
        ordered[0].temporal_scope,
        _cap(ordered, found.evidence_cap),
        None,
    )
