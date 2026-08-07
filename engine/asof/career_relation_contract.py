"""职业柱五步法的无权重关系数据契约。

本模块只表达职业柱候选、柱间关系、离散优先级、冲突与弃权；
不读取职业答案，不计算十神，也不提供浮点评分或经验权重。
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from enum import Enum
import json
from typing import Any, Iterable


SCHEMA_VERSION = "career-relation-inference/v1"


class FrozenStringEnum(str, Enum):
    """可稳定序列化为字符串的领域枚举基类。"""


class PillarPosition(FrozenStringEnum):
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"


PILLAR_ORDER = (
    PillarPosition.YEAR,
    PillarPosition.MONTH,
    PillarPosition.DAY,
    PillarPosition.HOUR,
)
_PILLAR_INDEX = {pillar: index for index, pillar in enumerate(PILLAR_ORDER)}


class CareerPalace(FrozenStringEnum):
    SELF = "self_palace"
    OTHER = "other_palace"


class SelectionStage(FrozenStringEnum):
    SELF_OFFICER_KILLING = "step_1_self_officer_killing"
    SELF_OFFICER_KILLING_TOMB = "step_2_self_officer_killing_tomb"
    OTHER_OFFICER_KILLING_LINKED_TO_HOUR = (
        "step_3_other_officer_killing_linked_to_hour"
    )
    WEALTH_OR_WEALTH_TOMB = "step_4_wealth_or_wealth_tomb"
    FORMATION_STAR_LINKED_TO_SELF = "step_5_formation_star_linked_to_self"


STAGE_ORDER = (
    SelectionStage.SELF_OFFICER_KILLING,
    SelectionStage.SELF_OFFICER_KILLING_TOMB,
    SelectionStage.OTHER_OFFICER_KILLING_LINKED_TO_HOUR,
    SelectionStage.WEALTH_OR_WEALTH_TOMB,
    SelectionStage.FORMATION_STAR_LINKED_TO_SELF,
)
_STAGE_INDEX = {stage: index for index, stage in enumerate(STAGE_ORDER)}


class RelationType(FrozenStringEnum):
    COMBINATION = "combination"
    CLASH = "clash"
    PUNISHMENT = "punishment"
    HARM = "harm"
    HIDDEN_REVEALED = "hidden_revealed"
    ADJACENT = "adjacent"
    ROOTED = "rooted"
    ENTERS_TOMB = "enters_tomb"


class CandidateStatus(FrozenStringEnum):
    PROPOSED = "proposed"
    REJECTED = "rejected"
    SELECTED = "selected"
    CONFLICT = "conflict"


class RejectionReason(FrozenStringEnum):
    PALACE_STAGE_MISMATCH = "palace_stage_mismatch"
    MISSING_HOUR_LINK = "missing_hour_link"
    MISSING_SELF_PALACE_LINK = "missing_self_palace_link"
    LOWER_PRIORITY_STAGE = "lower_priority_stage"


class AbstentionReason(FrozenStringEnum):
    NO_CANDIDATE = "no_candidate"
    NO_ELIGIBLE_CANDIDATE = "no_eligible_candidate"
    MULTIPLE_TOP_PRIORITY_CANDIDATES = "multiple_top_priority_candidates"


def palace_for_pillar(pillar: PillarPosition) -> CareerPalace:
    """按日、时为我宫，年、月为他宫返回职业语义宫位。"""

    if pillar in (PillarPosition.DAY, PillarPosition.HOUR):
        return CareerPalace.SELF
    return CareerPalace.OTHER


def left_neighbor(pillar: PillarPosition) -> PillarPosition | None:
    """按年→月→日→时返回紧邻左柱；年柱显式返回 ``None``。"""

    index = _PILLAR_INDEX[pillar]
    return None if index == 0 else PILLAR_ORDER[index - 1]


@dataclass(frozen=True, slots=True)
class CareerRelation:
    source: PillarPosition
    target: PillarPosition
    relation_type: RelationType
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise ValueError("relation endpoints must be different pillars")
        if self.relation_type is RelationType.ADJACENT:
            distance = abs(_PILLAR_INDEX[self.source] - _PILLAR_INDEX[self.target])
            if distance != 1:
                raise ValueError("adjacent relation requires neighboring pillars")
        if not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs):
            raise ValueError("relation evidence_refs must contain non-empty references")
        object.__setattr__(self, "evidence_refs", tuple(sorted(set(self.evidence_refs))))


@dataclass(frozen=True, slots=True)
class CareerPillarCandidate:
    pillar: PillarPosition
    palace: CareerPalace
    stage: SelectionStage
    relations: tuple[CareerRelation, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    status: CandidateStatus = CandidateStatus.PROPOSED
    rejection_reason: RejectionReason | None = None

    def __post_init__(self) -> None:
        if not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs):
            raise ValueError("candidate evidence_refs must contain non-empty references")
        if any(
            relation.source != self.pillar and relation.target != self.pillar
            for relation in self.relations
        ):
            raise ValueError("every candidate relation must involve the candidate pillar")
        if self.status is CandidateStatus.REJECTED and self.rejection_reason is None:
            raise ValueError("rejected candidate requires rejection_reason")
        if self.status is not CandidateStatus.REJECTED and self.rejection_reason is not None:
            raise ValueError("only rejected candidate may carry rejection_reason")

        relations = tuple(sorted(set(self.relations), key=_relation_sort_key))
        object.__setattr__(self, "relations", relations)
        object.__setattr__(self, "evidence_refs", tuple(sorted(set(self.evidence_refs))))


@dataclass(frozen=True, slots=True)
class LeftPillar:
    career_pillar: PillarPosition
    pillar: PillarPosition | None

    def __post_init__(self) -> None:
        expected = left_neighbor(self.career_pillar)
        if self.pillar != expected:
            raise ValueError(
                f"left pillar for {self.career_pillar.value} must be "
                f"{expected.value if expected else None}"
            )


@dataclass(frozen=True, slots=True)
class CareerRelationInference:
    candidates: tuple[CareerPillarCandidate, ...]
    selected_pillar: PillarPosition | None
    left_pillar: LeftPillar | None
    abstention_reason: AbstentionReason | None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        if self.selected_pillar is None:
            if self.left_pillar is not None:
                raise ValueError("left_pillar requires selected_pillar")
            if self.abstention_reason is None:
                raise ValueError("inference without selection requires abstention_reason")
        else:
            if self.abstention_reason is not None:
                raise ValueError("selected inference cannot carry abstention_reason")
            if self.left_pillar is None:
                raise ValueError("selected inference requires explicit left_pillar")
            if self.left_pillar.career_pillar is not self.selected_pillar:
                raise ValueError("left_pillar must describe selected_pillar")

        object.__setattr__(self, "candidates", tuple(sorted(self.candidates, key=_candidate_sort_key)))

    def to_canonical_dict(self) -> dict[str, Any]:
        """返回只含 JSON 基础类型、键和值顺序稳定的结构。"""

        return _canonical_value(self)

    def to_canonical_json(self) -> str:
        """返回确定性的紧凑 UTF-8 JSON 文本。"""

        return json.dumps(
            self.to_canonical_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


def infer_career_pillar(
    candidates: Iterable[CareerPillarCandidate],
) -> CareerRelationInference:
    """按五步法离散优先级选择职业柱，平级多候选时显式弃权。"""

    proposed = tuple(candidates)
    if not proposed:
        return CareerRelationInference(
            candidates=(),
            selected_pillar=None,
            left_pillar=None,
            abstention_reason=AbstentionReason.NO_CANDIDATE,
        )
    if any(candidate.status is not CandidateStatus.PROPOSED for candidate in proposed):
        raise ValueError("inference input candidates must have proposed status")

    evaluated: list[CareerPillarCandidate] = []
    eligible: list[CareerPillarCandidate] = []
    for candidate in proposed:
        rejection = _eligibility_rejection(candidate)
        if rejection is None:
            eligible.append(candidate)
            evaluated.append(candidate)
        else:
            evaluated.append(
                replace(
                    candidate,
                    status=CandidateStatus.REJECTED,
                    rejection_reason=rejection,
                )
            )

    if not eligible:
        return CareerRelationInference(
            candidates=tuple(evaluated),
            selected_pillar=None,
            left_pillar=None,
            abstention_reason=AbstentionReason.NO_ELIGIBLE_CANDIDATE,
        )

    winning_stage = min(eligible, key=lambda item: _STAGE_INDEX[item.stage]).stage
    winners = [candidate for candidate in eligible if candidate.stage is winning_stage]
    output: list[CareerPillarCandidate] = []
    winner_status = (
        CandidateStatus.SELECTED if len(winners) == 1 else CandidateStatus.CONFLICT
    )
    winner_pillars = {candidate.pillar for candidate in winners}

    for candidate in evaluated:
        if candidate.status is CandidateStatus.REJECTED:
            output.append(candidate)
        elif candidate.stage is winning_stage and candidate.pillar in winner_pillars:
            output.append(replace(candidate, status=winner_status))
        else:
            output.append(
                replace(
                    candidate,
                    status=CandidateStatus.REJECTED,
                    rejection_reason=RejectionReason.LOWER_PRIORITY_STAGE,
                )
            )

    if len(winners) > 1:
        return CareerRelationInference(
            candidates=tuple(output),
            selected_pillar=None,
            left_pillar=None,
            abstention_reason=AbstentionReason.MULTIPLE_TOP_PRIORITY_CANDIDATES,
        )

    selected = winners[0].pillar
    return CareerRelationInference(
        candidates=tuple(output),
        selected_pillar=selected,
        left_pillar=LeftPillar(selected, left_neighbor(selected)),
        abstention_reason=None,
    )


def _eligibility_rejection(
    candidate: CareerPillarCandidate,
) -> RejectionReason | None:
    if candidate.palace is not palace_for_pillar(candidate.pillar):
        return RejectionReason.PALACE_STAGE_MISMATCH

    if candidate.stage in (
        SelectionStage.SELF_OFFICER_KILLING,
        SelectionStage.SELF_OFFICER_KILLING_TOMB,
    ) and candidate.palace is not CareerPalace.SELF:
        return RejectionReason.PALACE_STAGE_MISMATCH

    if candidate.stage is SelectionStage.OTHER_OFFICER_KILLING_LINKED_TO_HOUR:
        if candidate.palace is not CareerPalace.OTHER:
            return RejectionReason.PALACE_STAGE_MISMATCH
        if not _has_link_to_pillar(candidate.relations, PillarPosition.HOUR):
            return RejectionReason.MISSING_HOUR_LINK

    if candidate.stage is SelectionStage.FORMATION_STAR_LINKED_TO_SELF:
        if not any(
            palace_for_pillar(_other_endpoint(relation, candidate.pillar))
            is CareerPalace.SELF
            for relation in candidate.relations
        ):
            return RejectionReason.MISSING_SELF_PALACE_LINK

    return None


def _has_link_to_pillar(
    relations: tuple[CareerRelation, ...], target: PillarPosition
) -> bool:
    return any(relation.source is target or relation.target is target for relation in relations)


def _other_endpoint(
    relation: CareerRelation, candidate_pillar: PillarPosition
) -> PillarPosition:
    return relation.target if relation.source is candidate_pillar else relation.source


def _relation_sort_key(relation: CareerRelation) -> tuple[int, int, str, tuple[str, ...]]:
    return (
        _PILLAR_INDEX[relation.source],
        _PILLAR_INDEX[relation.target],
        relation.relation_type.value,
        relation.evidence_refs,
    )


def _candidate_sort_key(candidate: CareerPillarCandidate) -> tuple[int, int, str]:
    return (
        _STAGE_INDEX[candidate.stage],
        _PILLAR_INDEX[candidate.pillar],
        candidate.status.value,
    )


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _canonical_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_canonical_value(item) for item in value]
    return value
