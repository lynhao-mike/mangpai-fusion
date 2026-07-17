from __future__ import annotations

import hashlib

from engine.decision.models import TimingProbability
from engine.decision.ren_career_timing import PublicationState, RenTimingResult


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
