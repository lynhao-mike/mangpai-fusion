from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from engine.predicates.ten_god_profile import SignalSource
from engine.predicates.types import GanZhi, Shishen


class TenGodStructureKind(str, Enum):
    FOOD_GOD_CONTROLS_KILLING = "食神制杀"
    HURTING_OFFICER_CONTROLS_KILLING = "伤官驾杀"
    KILLING_GENERATES_SEAL = "杀印相生"


class StructurePhase(str, Enum):
    ABSENT = "未见"
    LATENT = "潜伏"
    NATAL_ESTABLISHED = "原局成立"
    DAYUN_COMPLETED = "大运补全"
    DAYUN_ENHANCED = "大运强化"
    LIUNIAN_ACTIVATED = "流年引动"
    STABLE = "延续"
    DISRUPTED = "破坏"


class StructureOutcome(str, Enum):
    ABSENT = "absent"
    LATENT = "latent"
    ESTABLISHED = "established"
    DISRUPTED = "disrupted"


@dataclass(frozen=True, slots=True)
class StructureLayerAssessment:
    phase: StructurePhase
    ganzhi: GanZhi | None
    year_range: tuple[int, int] | None
    evidence: tuple[str, ...]
    blockers: tuple[str, ...]
    interactions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TenGodStructureAssessment:
    kind: TenGodStructureKind
    natal: StructureLayerAssessment
    dayun: tuple[StructureLayerAssessment, ...]
    liunian: StructureLayerAssessment | None


@dataclass(frozen=True, slots=True)
class StructureEvaluation:
    outcome: StructureOutcome
    evidence: tuple[str, ...]
    blockers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RoleDamage:
    role: Shishen
    score: float
    description: str
    target_source: SignalSource
