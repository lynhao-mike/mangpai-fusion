"""把治理 shadow 结果显式绑定为盲测输出，不从聚合 trace 猜测语义。"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Literal, Sequence

from engine.application.governance_shadow_types import (
    GovernanceShadowResult,
    shadow_result_digest,
)
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, BlindTask
from engine.governance.canonical import stable_object_id
from engine.governance.governance_claim import GovernanceClaim
from engine.governance.governance_claim_values import ClaimKind, ClaimStance

_PROJECTION_SCHEMA = "governance-shadow-task-projection/v1"
_SHADOW_SCHEMA = "governance.shadow-result.v1"
_SHADOW_RUNNER = "governance-shadow-runner/v1"
_TASK_ID = "marriage.divorce_or_remarriage"
_EVENT_CONCLUSION_ID = "yang.divorce_or_remarriage_event_risk/v1"
_EVENT_CONCLUSION = (
    "杨派原局夫妻宫事件锚与独立配偶结构交互同向，"
    "支持存在离婚或再婚事件风险，但不作必然判断。"
)
_EVIDENCE_REF = re.compile(r"^[^#\s]+#[^#\s]+$")
_FACT_REF = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_\u4e00-\u9fff]+)*$"
)


@dataclass(frozen=True, slots=True)
class ShadowPredictionBinding:
    source_claim: GovernanceClaim
    event_conclusion_id: Literal["yang.divorce_or_remarriage_event_risk/v1"]
    probability: float
    horizon: Literal["lifetime", "ten_year"]
    start_year: int | None
    end_year: int | None
    evidence_refs: tuple[str, ...]
    fact_refs: tuple[str, ...]
    falsifier: str


@dataclass(frozen=True, slots=True)
class GovernanceShadowTaskProjection:
    schema_version: str
    case_id: str
    school_id: str
    task_id: str
    task_catalog_version: str
    rule_version: str
    calculator_version: str
    expected_result_digest: str
    expected_fact_snapshot_id: str
    expected_fact_snapshot_digest: str
    expected_input_digest: str
    source_execution_state: Literal["executed", "unavailable"]
    capability_state: Literal["certified", "uncertified"]
    rationale: str
    prediction: ShadowPredictionBinding | None = None


def _exact_text(value: object, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty exact trimmed text")
    return value


def _validate_task(task: BlindTask) -> None:
    if (
        task.task_id != _TASK_ID
        or task.domain != "婚姻"
        or task.claim_type != "binary_event"
        or task.scoring_method != "binary_probability"
        or task.quantifiable is not True
        or task.high_risk is not True
        or tuple(task.allowed_time_horizons) != ("lifetime", "ten_year")
        or tuple(task.required_input_fields) != ("four_pillars", "sex_marker")
        or dict(task.label_schema)
        != {
            "type": "boolean",
            "positive_label": "occurred",
            "negative_label": "not_observed",
        }
        or task.evaluation_note != "只评价是否发生，不把关系压力自动等同离婚"
    ):
        raise ValueError("task does not match the exact admitted predicate")


def _validated_refs(
    values: tuple[str, ...], pattern: re.Pattern[str], field: str
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field} must be a non-empty tuple")
    checked: list[str] = []
    for value in values:
        text = _exact_text(value, field)
        if pattern.fullmatch(text) is None:
            raise ValueError(f"invalid {field} grammar")
        checked.append(text)
    if len(set(checked)) != len(checked):
        raise ValueError(f"duplicate {field}")
    return tuple(sorted(checked))


def _validated_window(binding: ShadowPredictionBinding) -> dict[str, int | str]:
    if binding.horizon == "lifetime":
        if binding.start_year is not None or binding.end_year is not None:
            raise ValueError("lifetime cannot contain years")
        return {"label": "lifetime"}
    if binding.horizon != "ten_year":
        raise ValueError("unsupported horizon")
    if (
        type(binding.start_year) is not int
        or type(binding.end_year) is not int
        or binding.start_year > binding.end_year
    ):
        raise ValueError("ten_year requires ordered integer years")
    return {
        "label": "ten_year",
        "start_year": binding.start_year,
        "end_year": binding.end_year,
    }


def _validated_prediction(
    projection: GovernanceShadowTaskProjection,
    result: GovernanceShadowResult,
) -> BlindPrediction:
    binding = projection.prediction
    if type(binding) is not ShadowPredictionBinding:
        raise ValueError("claim requires an exact prediction binding")
    claim = binding.source_claim
    if type(claim) is not GovernanceClaim:
        raise ValueError("prediction requires an exact GovernanceClaim")

    traces = tuple(item for item in result.claims if item.claim_id == claim.claim_id)
    if len(traces) != 1:
        raise ValueError("source claim must match exactly one shadow trace")
    trace = traces[0]
    provenance = claim.adapter_provenance
    if (
        claim.school_id != projection.school_id
        or trace.school_id != projection.school_id
        or claim.content_digest.value != trace.content_digest
        or provenance is None
        or provenance.source_claim_ref != trace.source_claim_ref
    ):
        raise ValueError("source claim ownership does not match shadow trace")
    if (
        claim.task_id != _TASK_ID
        or claim.claim_kind is not ClaimKind.EVENT
        or claim.stance is not ClaimStance.SUPPORT
        or claim.blockers
        or not claim.falsifier
    ):
        raise ValueError("source claim does not satisfy event support semantics")
    conclusion = claim.specification.conclusion
    if (
        binding.event_conclusion_id != _EVENT_CONCLUSION_ID
        or conclusion != conclusion.strip()
        or conclusion != _EVENT_CONCLUSION
    ):
        raise ValueError("source claim does not satisfy the exact event conclusion")
    if (
        result.arbitration is None
        or claim.claim_id not in result.arbitration.retained_claim_ids
        or claim.claim_id in result.excluded_claim_refs
        or trace.source_claim_ref in result.excluded_claim_refs
    ):
        raise ValueError("source claim is not an eligible retained claim")

    probability = binding.probability
    if (
        type(probability) not in (int, float)
        or isinstance(probability, bool)
        or not math.isfinite(probability)
        or not 0.0 <= probability <= 1.0
    ):
        raise ValueError("probability must be finite and between zero and one")
    falsifier = _exact_text(binding.falsifier, "falsifier")
    if falsifier != claim.falsifier:
        raise ValueError("binding falsifier must equal source claim falsifier")
    evidence_refs = _validated_refs(
        binding.evidence_refs, _EVIDENCE_REF, "evidence_refs"
    )
    fact_refs = _validated_refs(binding.fact_refs, _FACT_REF, "fact_refs")
    window = _validated_window(binding)
    prediction_id = str(
        stable_object_id(
            "governance_shadow_prediction",
            (
                _PROJECTION_SCHEMA,
                projection.case_id,
                projection.school_id,
                projection.task_id,
                claim.claim_id,
                claim.content_digest.value,
                binding.event_conclusion_id,
                conclusion,
                projection.task_catalog_version,
                projection.rule_version,
                projection.calculator_version,
                binding.horizon,
                binding.start_year,
                binding.end_year,
                float(probability),
                evidence_refs,
                fact_refs,
                falsifier,
            ),
        )
    )
    return BlindPrediction(
        prediction_id=prediction_id,
        event_label="occurred",
        probability=float(probability),
        time_window=window,
        evidence_refs=list(evidence_refs),
        fact_refs=list(fact_refs),
        falsifier=falsifier,
    )


def adapt_governance_shadow_to_blind_outputs(
    result: GovernanceShadowResult,
    task: BlindTask,
    projections: Sequence[GovernanceShadowTaskProjection],
) -> tuple[BlindSchoolOutput, ...]:
    """Validate explicit attestations and convert them without semantic inference."""
    if type(result) is not GovernanceShadowResult or type(task) is not BlindTask:
        raise TypeError("exact GovernanceShadowResult and BlindTask are required")
    if result.schema_version != _SHADOW_SCHEMA or result.runner_version != _SHADOW_RUNNER:
        raise ValueError("unsupported shadow schema or runner")
    if shadow_result_digest(result) != result.result_digest:
        raise ValueError("shadow result digest mismatch")
    if result.status != "ok":
        raise ValueError("fail-closed shadow result cannot be adapted")
    _validate_task(task)
    if isinstance(projections, (str, bytes)):
        raise TypeError("projections must be a non-empty sequence")
    items = tuple(projections)
    if not items:
        raise ValueError("projections must be non-empty")

    shared: tuple[str, ...] | None = None
    identities: set[tuple[str, str, str]] = set()
    used_claims: set[str] = set()
    outputs: list[BlindSchoolOutput] = []
    for projection in items:
        if type(projection) is not GovernanceShadowTaskProjection:
            raise TypeError("exact GovernanceShadowTaskProjection is required")
        if projection.schema_version != _PROJECTION_SCHEMA:
            raise ValueError("unsupported projection schema")
        for field in (
            "case_id",
            "school_id",
            "task_id",
            "task_catalog_version",
            "rule_version",
            "calculator_version",
            "expected_result_digest",
            "expected_fact_snapshot_id",
            "expected_fact_snapshot_digest",
            "expected_input_digest",
            "rationale",
        ):
            _exact_text(getattr(projection, field), field)
        if projection.task_id != task.task_id:
            raise ValueError("projection task mismatch")
        if (
            projection.expected_result_digest != result.result_digest
            or projection.expected_fact_snapshot_id != result.fact_snapshot_id
            or projection.expected_fact_snapshot_digest != result.fact_snapshot_digest
            or projection.expected_input_digest != result.input_digest
        ):
            raise ValueError("projection shadow identity mismatch")
        current_shared = (
            projection.case_id,
            projection.task_catalog_version,
            projection.rule_version,
            projection.calculator_version,
            projection.expected_result_digest,
            projection.expected_fact_snapshot_id,
            projection.expected_fact_snapshot_digest,
            projection.expected_input_digest,
        )
        if shared is None:
            shared = current_shared
        elif current_shared != shared:
            raise ValueError("projections do not share one attested source context")
        identity = (projection.case_id, projection.school_id, projection.task_id)
        if identity in identities:
            raise ValueError("duplicate output identity")
        identities.add(identity)

        unavailable = tuple(
            item
            for item in result.unavailable_schools
            if item.school_id == projection.school_id
        )
        if projection.source_execution_state == "unavailable":
            if len(unavailable) != 1:
                raise ValueError("unavailable projection requires exactly one trace")
        elif projection.source_execution_state == "executed":
            if unavailable:
                raise ValueError("executed projection conflicts with unavailable trace")
        else:
            raise ValueError("invalid source execution state")
        if projection.capability_state not in ("certified", "uncertified"):
            raise ValueError("invalid capability state")

        unsupported = (
            projection.source_execution_state == "unavailable"
            or projection.capability_state == "uncertified"
        )
        if unsupported:
            if projection.prediction is not None:
                raise ValueError("unsupported output cannot carry a prediction")
            state: Literal["claim", "abstain", "unsupported"] = "unsupported"
            predictions: list[BlindPrediction] = []
        elif projection.prediction is None:
            state = "abstain"
            predictions = []
        else:
            prediction = _validated_prediction(projection, result)
            claim_id = projection.prediction.source_claim.claim_id
            if claim_id in used_claims:
                raise ValueError("source claim cannot back multiple outputs")
            used_claims.add(claim_id)
            state = "claim"
            predictions = [prediction]
        outputs.append(
            BlindSchoolOutput(
                case_id=projection.case_id,
                school_id=projection.school_id,
                task_id=projection.task_id,
                state=state,
                rationale=projection.rationale,
                predictions=predictions,
                counter_evidence=[],
            )
        )
    return tuple(sorted(outputs, key=lambda item: (item.case_id, item.task_id, item.school_id)))
