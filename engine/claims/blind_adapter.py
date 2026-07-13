"""把引擎 Claim 显式绑定到盲测输出，不从报告文本反推。"""

from __future__ import annotations

from engine.claims.domain import Claim
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, BlindTask


def claim_to_blind_output(claim: Claim, *, case_id: str, task: BlindTask) -> BlindSchoolOutput:
    if claim.task_id != task.task_id:
        raise ValueError("claim and task task_id must match")

    evidence_refs = [evidence.evidence_id for evidence in claim.evidence]
    window = claim.time_window.to_dict() if claim.time_window else {}
    event_label = str(task.label_schema.get("event") or task.label_schema.get("positive_label") or claim.statement)
    probability = 0.65 if claim.claim_type in {"event_claim", "timing_claim"} else 0.5
    prediction = BlindPrediction(
        prediction_id="prediction-" + claim.claim_id.removeprefix("claim-"),
        event_label=event_label,
        probability=probability,
        time_window=window,
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
