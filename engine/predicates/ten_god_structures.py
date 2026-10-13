from __future__ import annotations

from engine.predicates.cycles import liunian_ganzhi
from engine.predicates.ten_god_profile import (
    SignalSource,
    combine_ten_god_profiles,
    cycle_ten_god_profile,
    natal_ten_god_profile,
)
from engine.predicates.ten_god_structure_core import (
    evaluate_structure,
    layer_assessment,
    phase_for_dayun,
    phase_for_liunian,
    phase_for_natal,
)
from engine.predicates.ten_god_structure_interactions import (
    cycle_damages,
    cycle_evidence,
)
from engine.predicates.ten_god_structure_types import (
    StructureLayerAssessment,
    StructurePhase,
    TenGodStructureAssessment,
    TenGodStructureKind,
)
from engine.predicates.types import ParsedInput

__all__ = [
    "StructureLayerAssessment",
    "StructurePhase",
    "TenGodStructureAssessment",
    "TenGodStructureKind",
    "assess_ten_god_structure",
    "structure_is_effective",
]


def assess_ten_god_structure(
    parsed: ParsedInput,
    kind: TenGodStructureKind,
    *,
    target_year: int | None = None,
) -> TenGodStructureAssessment:
    """Assess all fortunes and only the annual year explicitly supplied by the caller."""
    natal_profile = natal_ten_god_profile(parsed.bazi)
    natal_evaluation = evaluate_structure(kind, natal_profile, (), parsed)
    natal = layer_assessment(
        natal_evaluation,
        phase_for_natal(natal_evaluation.outcome),
    )

    dayun_layers: list[StructureLayerAssessment] = []
    dayun_evaluations = []
    for step in parsed.dayun.排布:
        cycle_profile = cycle_ten_god_profile(
            step.干支,
            parsed.bazi.day_master,
            SignalSource.DAYUN,
        )
        profile = combine_ten_god_profiles(natal_profile, cycle_profile)
        damages = cycle_damages(
            kind,
            natal_profile,
            step.干支,
            SignalSource.DAYUN,
        )
        evaluation = evaluate_structure(kind, profile, damages, parsed)
        dayun_evaluations.append(evaluation)
        phase = phase_for_dayun(
            natal_evaluation.outcome,
            evaluation.outcome,
            kind,
            cycle_profile,
        )
        evidence = evaluation.evidence + cycle_evidence(
            kind,
            natal_profile,
            cycle_profile,
            SignalSource.DAYUN,
        )
        dayun_layers.append(
            layer_assessment(
                evaluation,
                phase,
                ganzhi=step.干支,
                year_range=step.起讫年,
                evidence=evidence,
                interactions=tuple(damage.description for damage in damages),
            )
        )

    liunian = None
    if target_year is not None:
        dayun_index = next(
            (
                index
                for index, step in enumerate(parsed.dayun.排布)
                if step.起讫年[0] <= target_year < step.起讫年[1]
            ),
            None,
        )
        if dayun_index is not None:
            step = parsed.dayun.排布[dayun_index]
            annual_ganzhi = liunian_ganzhi(target_year)
            dayun_profile = cycle_ten_god_profile(
                step.干支,
                parsed.bazi.day_master,
                SignalSource.DAYUN,
            )
            annual_profile = cycle_ten_god_profile(
                annual_ganzhi,
                parsed.bazi.day_master,
                SignalSource.LIUNIAN,
            )
            base_profile = combine_ten_god_profiles(natal_profile, dayun_profile)
            profile = combine_ten_god_profiles(base_profile, annual_profile)
            damages = cycle_damages(
                kind,
                base_profile,
                annual_ganzhi,
                SignalSource.LIUNIAN,
            )
            evaluation = evaluate_structure(kind, profile, damages, parsed)
            phase = phase_for_liunian(
                dayun_evaluations[dayun_index].outcome,
                evaluation.outcome,
                kind,
                annual_profile,
                bool(damages),
            )
            evidence = evaluation.evidence + cycle_evidence(
                kind,
                base_profile,
                annual_profile,
                SignalSource.LIUNIAN,
            )
            liunian = layer_assessment(
                evaluation,
                phase,
                ganzhi=annual_ganzhi,
                year_range=(target_year, target_year + 1),
                evidence=evidence,
                interactions=tuple(damage.description for damage in damages),
            )

    return TenGodStructureAssessment(
        kind=kind,
        natal=natal,
        dayun=tuple(dayun_layers),
        liunian=liunian,
    )


def structure_is_effective(assessment: TenGodStructureAssessment) -> bool:
    effective = {
        StructurePhase.NATAL_ESTABLISHED,
        StructurePhase.DAYUN_COMPLETED,
        StructurePhase.DAYUN_ENHANCED,
        StructurePhase.LIUNIAN_ACTIVATED,
        StructurePhase.STABLE,
    }
    return (
        assessment.natal.phase in effective
        or any(layer.phase in effective for layer in assessment.dayun)
        or (assessment.liunian is not None and assessment.liunian.phase in effective)
    )
