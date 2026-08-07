"""现实落点冻结、受约束转译、核验与条件分支裁剪。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LandingVerdict(str, Enum):
    CENTER_HIT = "CENTER_HIT"
    ALTERNATIVE_HIT = "ALTERNATIVE_HIT"
    MISS = "MISS"
    TAXONOMY_GAP = "TAXONOMY_GAP"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True, slots=True)
class LandingPoint:
    name: str
    domain: str
    direction: str

    def __post_init__(self) -> None:
        if not all((self.name.strip(), self.domain.strip(), self.direction.strip())):
            raise ValueError("landing point requires name, domain and direction")


@dataclass(frozen=True, slots=True)
class FrozenLandingSet:
    """结果揭晓前冻结的有限落点集合；核验不得回写。"""

    function_candidate: str
    center: LandingPoint
    alternatives: tuple[LandingPoint, ...]
    weak_hit_boundary: str
    falsifiers: tuple[str, ...]
    exclusions: tuple[str, ...]
    frozen_version: str

    def __post_init__(self) -> None:
        if not self.function_candidate.strip() or not self.frozen_version.strip():
            raise ValueError("frozen landing set requires function and version")
        if len(self.alternatives) > 2:
            raise ValueError("at most two alternative landing points may be frozen")
        if not self.weak_hit_boundary.strip() or not self.falsifiers or not self.exclusions:
            raise ValueError("freeze requires weak boundary, falsifiers and exclusions")
        if any(
            point.domain != self.center.domain or point.direction != self.center.direction
            for point in self.alternatives
        ):
            raise ValueError("alternatives must preserve center domain and direction")
        names = (self.center.name,) + tuple(point.name for point in self.alternatives)
        if len(set(names)) != len(names):
            raise ValueError("frozen landing names must be unique")


@dataclass(frozen=True, slots=True)
class RealityConstraint:
    state_id: str
    description: str
    closed_landing_names: tuple[str, ...]
    reachable_landing_names: tuple[str, ...]
    verified: bool


@dataclass(frozen=True, slots=True)
class TranslationDecision:
    original_function_candidate: str
    closed_original_landing: str | None
    triggering_constraint_id: str | None
    selected_landing: LandingPoint | None
    falsifiers: tuple[str, ...]
    reason_code: str


@dataclass(frozen=True, slots=True)
class LandingVerification:
    verdict: LandingVerdict
    frozen_landing_name: str | None
    actual_landing: LandingPoint
    reason_code: str
    taxonomy_evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConditionalBranch:
    branch_id: str
    evidence_tier: int
    impact_tier: int
    minimum_question: str

    def __post_init__(self) -> None:
        if self.evidence_tier not in {1, 2, 3} or self.impact_tier not in {1, 2, 3, 4}:
            raise ValueError("branch tiers must use frozen ordinal categories")
        if not self.minimum_question.strip():
            raise ValueError("branch requires a minimum disambiguation question")


def translate_landing(
    frozen: FrozenLandingSet,
    *,
    constraint: RealityConstraint | None = None,
) -> TranslationDecision:
    """按截止日事实约束选择冻结落点；不创造新落点。"""

    if constraint is None or frozen.center.name not in constraint.closed_landing_names:
        return TranslationDecision(
            frozen.function_candidate,
            None,
            None,
            frozen.center,
            frozen.falsifiers,
            "CENTER_REACHABLE",
        )
    if not constraint.verified:
        return TranslationDecision(
            frozen.function_candidate,
            frozen.center.name,
            constraint.state_id,
            None,
            frozen.falsifiers,
            "UNVERIFIED_CONSTRAINT_CANNOT_TRANSLATE",
        )

    alternatives = tuple(
        point for point in frozen.alternatives if point.name in constraint.reachable_landing_names
    )
    if not alternatives:
        return TranslationDecision(
            frozen.function_candidate,
            frozen.center.name,
            constraint.state_id,
            None,
            frozen.falsifiers,
            "NO_LEGAL_FROZEN_ALTERNATIVE",
        )
    return TranslationDecision(
        frozen.function_candidate,
        frozen.center.name,
        constraint.state_id,
        alternatives[0],
        frozen.falsifiers,
        "FROZEN_ALTERNATIVE_SELECTED",
    )


def verify_landing(
    frozen: FrozenLandingSet,
    *,
    actual: LandingPoint,
    explicit_constraint: RealityConstraint | None = None,
    taxonomy_evidence: tuple[str, ...] = (),
) -> LandingVerification:
    """只按冻结集合核验；同域同方向的词典外结果登记缺口而非命中。"""

    if actual.name == frozen.center.name:
        return LandingVerification(LandingVerdict.CENTER_HIT, frozen.center.name, actual, "CENTER_MATCHED", ())
    alternative_names = {point.name for point in frozen.alternatives}
    if actual.name in alternative_names:
        return LandingVerification(
            LandingVerdict.ALTERNATIVE_HIT,
            actual.name,
            actual,
            "FROZEN_ALTERNATIVE_MATCHED",
            (),
        )
    same_function = actual.domain == frozen.center.domain and actual.direction == frozen.center.direction
    constrained = explicit_constraint is not None and explicit_constraint.verified
    if same_function and constrained and taxonomy_evidence:
        return LandingVerification(
            LandingVerdict.TAXONOMY_GAP,
            None,
            actual,
            "UNFROZEN_SAME_DOMAIN_DIRECTION_GAP",
            taxonomy_evidence,
        )
    return LandingVerification(LandingVerdict.MISS, None, actual, "OUTSIDE_FROZEN_LANDINGS", ())


def select_output_branches(branches: tuple[ConditionalBranch, ...]) -> tuple[ConditionalBranch, ...]:
    """内部候选可完整保留；输出按证据、影响、可消歧性稳定裁剪至两个。"""

    ordered = sorted(
        branches,
        key=lambda branch: (-branch.evidence_tier, -branch.impact_tier, branch.branch_id),
    )
    return tuple(ordered[:2])
