from __future__ import annotations

from engine.predicates.relations import gan_he, zhi_chong, zhi_chuan, zhi_xing
from engine.predicates.ten_god_profile import SignalSource, TenGodProfile
from engine.predicates.ten_god_structure_core import MIN_ROLE_SCORE, controller_roles_for
from engine.predicates.ten_god_structure_types import RoleDamage, TenGodStructureKind
from engine.predicates.types import GanZhi, Shishen, Zhi

_DAMAGEABLE_ROLES: tuple[Shishen, ...] = (
    "比肩",
    "劫财",
    "食神",
    "伤官",
    "正财",
    "偏财",
    "正官",
    "七杀",
    "正印",
    "偏印",
)


def cycle_damages(
    kind: TenGodStructureKind,
    base_profile: TenGodProfile,
    cycle_ganzhi: GanZhi,
    source: SignalSource,
) -> tuple[RoleDamage, ...]:
    damages: list[RoleDamage] = []
    for role in _DAMAGEABLE_ROLES:
        for signal in base_profile.signals_for(role):
            branch = signal.branch
            if branch is not None and _branch_attacked(cycle_ganzhi, branch):
                target = (
                    f"原局{signal.location}"
                    if signal.source is SignalSource.NATAL
                    else signal.location
                )
                relation = (
                    "冲"
                    if zhi_chong(cycle_ganzhi.zhi, branch)
                    else "刑穿"
                )
                damages.append(
                    RoleDamage(
                        role=role,
                        score=signal.score,
                        description=(
                            f"{source.value}{cycle_ganzhi.zhi}{relation}"
                            f"{target}{branch}，{role}受损"
                        ),
                        target_source=signal.source,
                    )
                )
            if signal.visible and gan_he(cycle_ganzhi.gan, signal.gan) is not None:
                damages.append(
                    RoleDamage(
                        role=role,
                        score=signal.score,
                        description=(
                            f"{source.value}{cycle_ganzhi.gan}合绊"
                            f"{signal.location}{signal.gan}，{role}受损"
                        ),
                        target_source=signal.source,
                    )
                )
    return tuple(damages)


def cycle_evidence(
    kind: TenGodStructureKind,
    base: TenGodProfile,
    cycle: TenGodProfile,
    source: SignalSource,
) -> tuple[str, ...]:
    evidence: list[str] = []
    for role in controller_roles_for(kind):
        if (
            base.total(role) < MIN_ROLE_SCORE
            <= base.total(role) + cycle.total(role)
        ):
            evidence.append(f"{source.value}补入{role}")
        elif cycle.total(role) >= MIN_ROLE_SCORE:
            evidence.append(f"{source.value}强化{role}")
    if (
        base.total("七杀") < MIN_ROLE_SCORE
        <= base.total("七杀") + cycle.total("七杀")
    ):
        evidence.append(f"{source.value}补入七杀")
    return tuple(evidence)


def _branch_attacked(cycle_ganzhi: GanZhi, target_branch: Zhi) -> bool:
    return bool(
        zhi_chong(cycle_ganzhi.zhi, target_branch)
        or zhi_chuan(cycle_ganzhi.zhi, target_branch)
        or zhi_xing(cycle_ganzhi.zhi, target_branch)
    )
