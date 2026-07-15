"""把引擎 Claim 显式绑定到盲测输出，不从报告文本反推。"""

from __future__ import annotations

import hashlib
from collections.abc import Collection

from engine.claims.domain import Claim
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, BlindTask


_COMPATIBLE_TASK_TYPES: dict[str, frozenset[str]] = {
    "structure_claim": frozenset({"structure", "structure_claim", "portrait"}),
    "event_claim": frozenset({
        "event", "binary", "binary_event", "categorical", "categorical_state", "ordinal", "ordinal_state",
    }),
    "timing_claim": frozenset({"event_timing", "time_window", "timing"}),
    "portrait_claim": frozenset({"portrait"}),
}
_CLASSIFICATION_TASK_TYPES = frozenset({"categorical", "categorical_state", "ordinal", "ordinal_state"})
_BINARY_TASK_TYPES = frozenset({"event", "binary", "binary_event"})
_TIMING_HORIZONS = frozenset({"annual", "ten_year", "ten-year"})


def _validate_compatibility(claim: Claim, task: BlindTask) -> None:
    compatible = _COMPATIBLE_TASK_TYPES[claim.claim_type]
    if task.claim_type not in compatible:
        raise ValueError(
            f"incompatible claim/task types: {claim.claim_type} cannot map to {task.claim_type}"
        )


def _validated_label(claim: Claim, task: BlindTask) -> str:
    if task.claim_type in _BINARY_TASK_TYPES:
        label = task.label_schema.get("positive_label")
        return str(label or claim.statement)
    if task.claim_type in _CLASSIFICATION_TASK_TYPES:
        label = claim.applicability_snapshot.get("predicted_label")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"{task.claim_type} claim requires applicability_snapshot predicted_label")
        allowed = task.label_schema.get("labels")
        if isinstance(allowed, Collection) and not isinstance(allowed, (str, bytes)) and label not in allowed:
            raise ValueError(f"predicted_label {label!r} is not in allowed labels for {task.task_id}")
        return label
    if claim.claim_type == "timing_claim":
        # 当前目录均声明 event；task_id 仅兼容早期已冻结测试夹具。
        return str(task.label_schema.get("event") or task.task_id)
    return claim.statement


def _validated_window(claim: Claim, task: BlindTask) -> dict[str, int | str]:
    if claim.claim_type in {"structure_claim", "portrait_claim"}:
        return {}
    if claim.time_window is None:
        raise ValueError(f"{claim.claim_type} requires an explicit time window")
    horizon = claim.time_window.label
    if claim.claim_type == "timing_claim" and horizon not in _TIMING_HORIZONS:
        raise ValueError(f"timing_claim requires annual or ten-year time window, got {horizon!r}")
    if horizon not in task.allowed_time_horizons:
        raise ValueError(f"time window {horizon!r} is not allowed for task {task.task_id}")
    return claim.time_window.to_dict()


def claim_to_blind_output(claim: Claim, *, case_id: str, task: BlindTask) -> BlindSchoolOutput:
    if claim.task_id != task.task_id:
        raise ValueError("claim and task task_id must match")
    if not claim.school_id.strip():
        raise ValueError("claim school_id is required")
    _validate_compatibility(claim, task)

    evidence_refs = [evidence.evidence_id for evidence in claim.evidence]
    prediction_digest = hashlib.sha256(claim.claim_id.encode("utf-8")).hexdigest()[:24]
    prediction = BlindPrediction(
        prediction_id=f"prediction-{prediction_digest}",
        event_label=_validated_label(claim, task),
        probability=claim.confidence,
        time_window=_validated_window(claim, task),
        evidence_refs=evidence_refs,
        falsifier=claim.falsifier,
    )
    return BlindSchoolOutput(
        case_id=case_id,
        school_id=claim.school_id,
        task_id=claim.task_id,
        state="claim",
        rationale=claim.confidence_basis,
        predictions=[prediction],
    )
