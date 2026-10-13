from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from engine.application.governance_fact_builder import (
    FactBuilderError,
    build_governance_fact_snapshot,
)
from engine.application.governance_shadow_school_views import adapt_school_views
from engine.application.governance_shadow_types import (
    CompositionRequest,
    CompositionTrace,
    GovernanceShadowDependencies,
    GovernanceShadowRequest,
    GovernanceShadowResult,
    SchoolViewFailure as SchoolViewFailure,
    SchoolViewOutcome as SchoolViewOutcome,
    ShadowArbitrationTrace,
    ShadowClaimTrace,
    ShadowIssue,
    TriggerRequest as TriggerRequest,
    TriggerTrace,
    UnavailableSchool,
    shadow_result_digest,
)
from engine.governance.arbitration import arbitrate
from engine.governance.arbitration_contracts import (
    ArbitrationArena,
    ArbitrationContext,
    ArbitrationIntegrityError,
)
from engine.governance.composition_contracts import CompositionExecutionMode
from engine.governance.composition_executor import execute_composition
from engine.governance.contracts import FactSnapshot, build_fact_snapshot
from engine.governance.fact_values import DigestRef, SnapshotSpec
from engine.governance.governance_claim import GovernanceClaim
from engine.governance.trigger_registry import evaluate_governance_trigger


_SCHEMA_VERSION = "governance.shadow-result.v1"
_RUNNER_VERSION = "governance-shadow-runner/v1"


@dataclass(frozen=True, slots=True)
class _RunContext:
    unavailable: tuple[UnavailableSchool, ...] = ()
    excluded_claim_refs: tuple[str, ...] = ()
    triggers: tuple[TriggerTrace, ...] = ()
    compositions: tuple[CompositionTrace, ...] = ()
    arbitration: ShadowArbitrationTrace | None = None
    issues: tuple[ShadowIssue, ...] = ()


def _result(
    status: Literal["ok", "fail_closed"],
    snapshot: FactSnapshot,
    claims: tuple[GovernanceClaim, ...],
    context: _RunContext,
) -> GovernanceShadowResult:
    trace = GovernanceShadowResult(
        _SCHEMA_VERSION,
        _RUNNER_VERSION,
        status,
        str(snapshot.snapshot_id),
        snapshot.content_digest.value,
        snapshot.input_digest.value,
        tuple(sorted({fact.fact_kind for fact in snapshot.facts})),
        tuple(ShadowClaimTrace.from_claim(claim) for claim in claims),
        tuple(sorted(context.unavailable, key=lambda item: item.school_id)),
        tuple(sorted(context.excluded_claim_refs)),
        tuple(sorted(context.triggers, key=lambda item: item.trigger_id)),
        tuple(
            sorted(
                context.compositions,
                key=lambda item: (item.template_id, item.version, item.content_digest),
            )
        ),
        context.arbitration,
        tuple(sorted(context.issues, key=lambda item: item.to_canonical())),
        "",
    )
    return GovernanceShadowResult(
        trace.schema_version,
        trace.runner_version,
        trace.status,
        trace.fact_snapshot_id,
        trace.fact_snapshot_digest,
        trace.input_digest,
        trace.fact_kinds,
        trace.claims,
        trace.unavailable_schools,
        trace.excluded_claim_refs,
        trace.trigger_results,
        trace.composition_results,
        trace.arbitration,
        trace.issues,
        shadow_result_digest(trace),
    )


def _fact_failure(error: FactBuilderError) -> GovernanceShadowResult:
    snapshot = build_fact_snapshot(
        SnapshotSpec(
            "governance.fact-snapshot.v1",
            "fact-build-failed",
            DigestRef.from_material(("fact-build-failed",)),
        ),
        (),
    )
    context = _RunContext(
        issues=(ShadowIssue(error.issue_code, error.field_path, error.diagnostic),)
    )
    return _result("fail_closed", snapshot, (), context)


def _triggers(
    snapshot: FactSnapshot, dependencies: GovernanceShadowDependencies
) -> tuple[TriggerTrace, ...]:
    if dependencies.trigger_registry is None:
        return ()
    traces: list[TriggerTrace] = []
    for request in dependencies.trigger_requests:
        outcome = evaluate_governance_trigger(
            dependencies.trigger_registry,
            request.trigger_id,
            snapshot,
            request.context,
        )
        traces.append(
            TriggerTrace(
                request.trigger_id,
                outcome.active,
                tuple(issue.value for issue in outcome.issues),
            )
        )
    return tuple(traces)


def _compositions(
    claims: tuple[GovernanceClaim, ...], dependencies: GovernanceShadowDependencies
) -> tuple[CompositionTrace, ...]:
    if dependencies.composition_registry is None:
        return ()
    by_id = {claim.claim_id: claim for claim in claims}
    traces: list[CompositionTrace] = []
    for request in dependencies.composition_requests:
        traces.append(_composition_trace(request, by_id, dependencies))
    return tuple(traces)


def _composition_trace(
    request: CompositionRequest,
    claims: dict[str, GovernanceClaim],
    dependencies: GovernanceShadowDependencies,
) -> CompositionTrace:
    registry = dependencies.composition_registry
    if registry is None:
        raise AssertionError("composition registry checked before trace execution")
    result = execute_composition(
        registry,
        template_id=request.template_id,
        version=request.version,
        components=tuple(
            claims[claim_id]
            for claim_id in request.component_claim_ids
            if claim_id in claims
        ),
        mode=CompositionExecutionMode.SHADOW,
    )
    return CompositionTrace(
        result.template_id,
        result.template_version,
        result.outcome.value,
        result.content_digest.value,
        result.issue_code,
    )


def _merge(
    context: _RunContext,
    triggers: tuple[TriggerTrace, ...],
    compositions: tuple[CompositionTrace, ...],
    arbitration: ShadowArbitrationTrace | None = None,
    issues: tuple[ShadowIssue, ...] = (),
) -> _RunContext:
    return _RunContext(
        context.unavailable,
        context.excluded_claim_refs,
        triggers,
        compositions,
        arbitration,
        (*context.issues, *issues),
    )


def _arbitration_result(
    request: GovernanceShadowRequest,
    dependencies: GovernanceShadowDependencies,
    snapshot: FactSnapshot,
    claims: tuple[GovernanceClaim, ...],
) -> ShadowArbitrationTrace:
    arena = ArbitrationArena(
        claims,
        ArbitrationContext(snapshot.facts, dependencies.certification_registry),
        dependencies.reference_catalog,
        dependencies.school_registry,
        dependencies.capability_version,
        request.fact_conflicts,
    )
    return ShadowArbitrationTrace.from_result(arbitrate(arena))


def run_governance_shadow(
    request: GovernanceShadowRequest,
    dependencies: GovernanceShadowDependencies,
) -> GovernanceShadowResult:
    try:
        snapshot = build_governance_fact_snapshot(
            case_id=request.case_id,
            raw_payload=request.raw_payload,
            chart=request.chart,
            target_year=request.target_year,
            calculator_version=request.calculator_version,
            feature_vector=request.feature_vector,
        )
    except FactBuilderError as error:
        return _fact_failure(error)
    adapted = adapt_school_views(request.school_views, dependencies.reference_catalog)
    context = _RunContext(
        adapted.unavailable,
        adapted.excluded_claim_refs,
        issues=adapted.issues,
    )
    claims = adapted.claims
    triggers = _triggers(snapshot, dependencies)
    compositions = _compositions(claims, dependencies)
    if request.fact_conflicts:
        issues = tuple(
            ShadowIssue("ARBITRATION.FACT_CONFLICT", item.fact_id, "fact conflict")
            for item in request.fact_conflicts
        )
        return _result(
            "fail_closed",
            snapshot,
            claims,
            _merge(context, triggers, compositions, issues=issues),
        )
    try:
        arbitration = _arbitration_result(request, dependencies, snapshot, claims)
    except ArbitrationIntegrityError as error:
        issue = ShadowIssue(error.code.value, error.fact_id, str(error))
        return _result(
            "fail_closed",
            snapshot,
            claims,
            _merge(context, triggers, compositions, issues=(issue,)),
        )
    return _result(
        "ok",
        snapshot,
        claims,
        _merge(context, triggers, compositions, arbitration=arbitration),
    )
