from __future__ import annotations

from typing import Final, assert_never

from engine.predicates.strength import calc_gan_strength
from engine.predicates.ten_god_profile import SignalSource, TenGodProfile
from engine.predicates.ten_god_structure_types import (
    RoleDamage,
    StructureEvaluation,
    StructureLayerAssessment,
    StructureOutcome,
    StructurePhase,
    TenGodStructureKind,
)
from engine.predicates.types import GanZhi, ParsedInput, Shishen

MIN_ROLE_SCORE: Final = 0.75
_MIN_BODY_SUPPORT: Final = 0.30
_MIN_CONTROL_RATIO: Final = 0.35
_MAX_CONTROL_RATIO: Final = 2.50


def evaluate_structure(
    kind: TenGodStructureKind,
    profile: TenGodProfile,
    damages: tuple[RoleDamage, ...],
    parsed: ParsedInput,
) -> StructureEvaluation:
    controller_roles = controller_roles_for(kind)
    qisha_score = effective_score(profile, damages, "七杀")
    raw_controller_score = profile.total(*controller_roles)
    controller_score = sum(
        effective_score(profile, damages, role) for role in controller_roles
    )
    evidence = (
        f"七杀有效量={qisha_score:.2f}",
        f"{kind.value}用神有效量={controller_score:.2f}",
    )
    if qisha_score < MIN_ROLE_SCORE:
        return StructureEvaluation(
            StructureOutcome.ABSENT,
            evidence,
            ("七杀未成有效结构",),
        )
    controller_damages = tuple(
        damage for damage in damages if damage.role in controller_roles
    )
    if (
        controller_damages
        and raw_controller_score >= MIN_ROLE_SCORE > controller_score
    ):
        return StructureEvaluation(
            StructureOutcome.DISRUPTED,
            evidence,
            tuple(damage.description for damage in controller_damages),
        )
    if controller_score == 0:
        return StructureEvaluation(
            StructureOutcome.ABSENT,
            evidence,
            (f"原局未见{kind.value}用神",),
        )
    if controller_score < MIN_ROLE_SCORE:
        role_name = (
            "食神"
            if kind is TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING
            else kind.value
        )
        return StructureEvaluation(
            StructureOutcome.LATENT,
            evidence,
            (f"{role_name}力量不足，尚未形成有效制杀",),
        )

    blockers = structural_blockers(
        kind,
        profile,
        damages,
        qisha_score,
        controller_score,
    )
    if blockers:
        return StructureEvaluation(StructureOutcome.DISRUPTED, evidence, blockers)
    natal_body_damage = sum(
        damage.score
        for damage in damages
        if damage.target_source is SignalSource.NATAL
        and damage.role in {"比肩", "劫财"}
    )
    body_support = max(
        0.0,
        calc_gan_strength(parsed.bazi.day_master, parsed.bazi)
        - 0.30 * natal_body_damage,
    )
    seal_support = sum(
        effective_score(profile, damages, role) for role in ("正印", "偏印")
    )
    body_support += 0.15 * seal_support
    cycle_body_score = profile.source_total(
        SignalSource.DAYUN, "比肩", "劫财"
    ) + profile.source_total(SignalSource.LIUNIAN, "比肩", "劫财")
    cycle_body_damage = sum(
        damage.score
        for damage in damages
        if damage.target_source is not SignalSource.NATAL
        and damage.role in {"比肩", "劫财"}
    )
    body_support += 0.30 * max(0.0, cycle_body_score - cycle_body_damage)
    if body_support < _MIN_BODY_SUPPORT:
        return StructureEvaluation(
            StructureOutcome.LATENT,
            evidence,
            ("日主无根，暂不能任杀与制化",),
        )
    return StructureEvaluation(StructureOutcome.ESTABLISHED, evidence, ())


def structural_blockers(
    kind: TenGodStructureKind,
    profile: TenGodProfile,
    damages: tuple[RoleDamage, ...],
    qisha_score: float,
    controller_score: float,
) -> tuple[str, ...]:
    match kind:
        case TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING:
            wealth = sum(
                effective_score(profile, damages, role)
                for role in ("正财", "偏财")
            )
            pianyin = effective_score(profile, damages, "偏印")
            if pianyin >= controller_score * 0.8 and wealth < pianyin * 0.8:
                return ("枭神夺食",)
        case TenGodStructureKind.HURTING_OFFICER_CONTROLS_KILLING:
            seal = sum(
                effective_score(profile, damages, role)
                for role in ("正印", "偏印")
            )
            if seal >= controller_score * 0.8:
                return ("印星制伤，伤官不能驾杀",)
        case TenGodStructureKind.KILLING_GENERATES_SEAL:
            wealth = sum(
                effective_score(profile, damages, role)
                for role in ("正财", "偏财")
            )
            if wealth >= controller_score * 0.8:
                return ("财星破印，杀印链受损",)
            food_hurt = sum(
                effective_score(profile, damages, role)
                for role in ("食神", "伤官")
            )
            if food_hurt >= qisha_score * 0.8:
                return ("食伤制杀，截断杀印相生",)
        case unreachable:
            assert_never(unreachable)

    ratio = controller_score / qisha_score
    if ratio < _MIN_CONTROL_RATIO:
        return ("制化力量不足",)
    if (
        kind is not TenGodStructureKind.KILLING_GENERATES_SEAL
        and ratio > _MAX_CONTROL_RATIO
    ):
        return ("制杀太过",)
    return ()


def controller_roles_for(kind: TenGodStructureKind) -> tuple[Shishen, ...]:
    match kind:
        case TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING:
            return ("食神",)
        case TenGodStructureKind.HURTING_OFFICER_CONTROLS_KILLING:
            return ("伤官",)
        case TenGodStructureKind.KILLING_GENERATES_SEAL:
            return ("正印", "偏印")
        case unreachable:
            assert_never(unreachable)


def effective_score(
    profile: TenGodProfile,
    damages: tuple[RoleDamage, ...],
    role: Shishen,
) -> float:
    damaged = sum(damage.score for damage in damages if damage.role == role)
    return max(0.0, profile.total(role) - damaged)


def phase_for_natal(outcome: StructureOutcome) -> StructurePhase:
    match outcome:
        case StructureOutcome.ABSENT:
            return StructurePhase.ABSENT
        case StructureOutcome.LATENT:
            return StructurePhase.LATENT
        case StructureOutcome.ESTABLISHED:
            return StructurePhase.NATAL_ESTABLISHED
        case StructureOutcome.DISRUPTED:
            return StructurePhase.DISRUPTED
        case unreachable:
            assert_never(unreachable)


def phase_for_dayun(
    natal: StructureOutcome,
    current: StructureOutcome,
    kind: TenGodStructureKind,
    cycle: TenGodProfile,
) -> StructurePhase:
    if current is StructureOutcome.ESTABLISHED:
        if natal is not StructureOutcome.ESTABLISHED:
            return StructurePhase.DAYUN_COMPLETED
        if cycle.total(*controller_roles_for(kind), "七杀") >= MIN_ROLE_SCORE:
            return StructurePhase.DAYUN_ENHANCED
        return StructurePhase.STABLE
    return phase_for_natal(current)


def phase_for_liunian(
    dayun: StructureOutcome,
    current: StructureOutcome,
    kind: TenGodStructureKind,
    annual: TenGodProfile,
    has_interaction: bool,
) -> StructurePhase:
    if current is StructureOutcome.ESTABLISHED:
        activates = (
            annual.total(*controller_roles_for(kind), "七杀") >= MIN_ROLE_SCORE
        )
        if dayun is not StructureOutcome.ESTABLISHED or activates or has_interaction:
            return StructurePhase.LIUNIAN_ACTIVATED
        return StructurePhase.STABLE
    return phase_for_natal(current)


def layer_assessment(
    evaluation: StructureEvaluation,
    phase: StructurePhase,
    *,
    ganzhi: GanZhi | None = None,
    year_range: tuple[int, int] | None = None,
    evidence: tuple[str, ...] | None = None,
    interactions: tuple[str, ...] = (),
) -> StructureLayerAssessment:
    return StructureLayerAssessment(
        phase=phase,
        ganzhi=ganzhi,
        year_range=year_range,
        evidence=evaluation.evidence if evidence is None else evidence,
        blockers=evaluation.blockers,
        interactions=interactions,
    )
