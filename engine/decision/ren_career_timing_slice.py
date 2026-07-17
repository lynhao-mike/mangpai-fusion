from __future__ import annotations

import hashlib
from dataclasses import replace

from engine.decision.models import ChartFactLedger, EventHypothesis, TimingProbability
from engine.decision.ren_career_timing import (
    EvidenceFamily,
    PublicationState,
    RenTimingResult,
    discriminate_ren_career_timing,
)
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput
from engine.features import ChartFeatureVector


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def to_ren_timing_probability(
    case_id: str,
    result: RenTimingResult,
) -> TimingProbability:
    if result.publication_state is not PublicationState.EMIT:
        raise ValueError("emit publication state required for Ren L5 adapter")

    selected = next(
        (
            family
            for family in result.evidence_families
            if family.family_key == result.selected_family_key
        ),
        None,
    )
    if selected is None or not selected.atoms:
        raise ValueError("selected evidence family is required")

    atom = min(
        selected.atoms,
        key=lambda item: (item.priority, item.year, item.atom_id),
    )
    if atom.year < 1900 or atom.year > 2100:
        raise ValueError("Ren timing year outside supported staged range")

    refs = sorted({atom.liunian_ref, atom.target_ref, atom.source_ref})
    return TimingProbability(
        prediction_id=_stable_id(
            "ren-timing",
            case_id,
            result.event_id,
            atom.year,
            atom.rule_id,
        ),
        event_id=result.event_id,
        time_window={
            "start_year": atom.year,
            "end_year": atom.year,
            "label": "annual",
        },
        trigger_conditions=refs,
        probability_range=(
            max(0.0, atom.confidence - 0.1),
            min(1.0, atom.confidence + 0.1),
        ),
        confidence=atom.confidence,
        falsifier=(
            f"若 {atom.year} 年未发生可核验的显著职业角色或岗位变化，"
            "则该任派应期命题证伪。"
        ),
    )


def _normalize_fact_refs(result: RenTimingResult) -> RenTimingResult:
    families = tuple(
        EvidenceFamily(
            family_key=family.family_key,
            atoms=tuple(
                replace(
                    atom,
                    liunian_ref=atom.to_dict()["liunian_ref"],
                    target_ref=atom.to_dict()["target_ref"],
                )
                for atom in family.atoms
            ),
        )
        for family in result.evidence_families
    )
    return replace(result, evidence_families=families)


def build_ren_career_timing_slice(
    case_id: str,
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    event: EventHypothesis | None,
    *,
    task_id: str = "career.role_change",
) -> tuple[RenTimingResult, tuple[TimingProbability, ...]]:
    result = discriminate_ren_career_timing(chart, features, event, task_id=task_id)
    if result.publication_state is not PublicationState.EMIT:
        return result, ()
    result = _normalize_fact_refs(result)
    return result, (to_ren_timing_probability(case_id, result),)


def to_blind_output(
    case_id: str,
    result: RenTimingResult,
    timings: tuple[TimingProbability, ...],
) -> BlindSchoolOutput:
    state = (
        "claim"
        if timings
        else (
            "unsupported"
            if result.publication_state is PublicationState.UNSUPPORTED
            else "abstain"
        )
    )
    predictions = [
        BlindPrediction(
            prediction_id=item.prediction_id,
            event_label="career.role_change",
            probability=item.confidence,
            time_window=dict(item.time_window),
            evidence_refs=[ref for ref in item.trigger_conditions if "#" in ref],
            falsifier=item.falsifier,
            fact_refs=[ref for ref in item.trigger_conditions if "#" not in ref],
        )
        for item in timings
    ]
    reasons = (*result.input_blockers, *result.failed_gates, *result.routing_blockers)
    rationale = (
        "任派真实岁运触发形成职业角色变化应期窗口。"
        if predictions
        else "; ".join(reasons) or "任派切片未形成可发布应期。"
    )
    return BlindSchoolOutput(
        case_id=case_id,
        school_id="ren",
        task_id=result.task_id,
        state=state,
        rationale=rationale,
        predictions=predictions,
        counter_evidence=list(result.failed_gates),
    )
