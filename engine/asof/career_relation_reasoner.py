"""职业关系图的双层离散裁决与现实状态单向适配。

本模块只消费职业关系图、带明确日期边界的大运阶段，以及独立的
``RealityTrack``。它不读取 occupation、known facts、职业标签或反馈；不计算
分数、概率或权重，也不以命理信号补写现实状态。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from engine.asof.career_path_state import (
    DayunCareerContext,
    NatalCareerInclination,
    RealityCareerStatus,
)
from engine.asof.career_relation_contract import CandidateStatus, PillarPosition
from engine.asof.career_relation_graph import CareerRelationGraphResult, PillarNode
from engine.asof.reality_track import RealityTrack
from engine.predicates.relations import gan_he, zhi_chong, zhi_chuan, zhi_liuhe, zhi_po, zhi_xing
from engine.predicates.types import GanZhi

_EMPLOYMENT_CAREER = frozenset(("正官", "七杀"))
_EMPLOYMENT_LEFT = frozenset(("正印", "偏印"))
_ENTREPRENEURSHIP_CAREER = frozenset(("正财", "偏财"))
_ENTREPRENEURSHIP_LEFT = frozenset(("食神", "伤官"))
_REALITY_VALUES = frozenset(("employed", "entrepreneurial", "mixed", "transitioning"))


@dataclass(frozen=True, slots=True)
class NatalCareerDecision:
    """原局离散裁决及显式弃权；不包含现实职业答案。"""

    inclination: NatalCareerInclination
    abstain_reason: str | None
    applicability_conditions: tuple[str, ...]
    counter_evidence: tuple[str, ...]
    unresolved_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DayunCareerDecision:
    """唯一可定位大运的离散开放/抑制结果。"""

    context: DayunCareerContext | None
    abstain_reason: str | None
    has_conflict: bool
    stage_sequence: int | None
    stage_start_date: date | None
    stage_end_date: date | None
    evidence_refs: tuple[str, ...]


def _shishens(node: PillarNode) -> frozenset[str]:
    values = {item.shishen for item in node.hidden_stems}
    if node.stem_shishen is not None:
        values.add(node.stem_shishen)
    return frozenset(values)


def _node(graph: CareerRelationGraphResult, pillar: PillarPosition) -> PillarNode:
    return next(item for item in graph.graph.pillars if item.pillar is pillar)


def reason_natal_career_inclination(
    graph: CareerRelationGraphResult,
) -> NatalCareerDecision:
    """仅按职业柱及其左柱的十神组合裁决原局双布尔倾向。

    任职链要求职业柱官杀且左柱印星；经营链要求职业柱财星且左柱食伤。
    财或食伤单独出现均不构成经营链。职业柱未唯一选择时显式弃权。
    """

    inference = graph.inference
    if inference.selected_pillar is None or inference.left_pillar is None:
        reason = (
            "career_relation_conflict"
            if any(item.status is CandidateStatus.CONFLICT for item in inference.candidates)
            else "insufficient_natal_relation_evidence"
        )
        return NatalCareerDecision(
            inclination=NatalCareerInclination(False, False, ()),
            abstain_reason=reason,
            applicability_conditions=("unique_career_pillar_required",),
            counter_evidence=(),
            unresolved_refs=tuple(item.topic.value for item in graph.unresolved),
        )

    left_position = inference.left_pillar.pillar
    if left_position is None:
        return NatalCareerDecision(
            inclination=NatalCareerInclination(False, False, ()),
            abstain_reason="insufficient_natal_relation_evidence",
            applicability_conditions=("career_pillar_left_neighbor_required",),
            counter_evidence=("selected_career_pillar_has_no_left_neighbor",),
            unresolved_refs=tuple(item.topic.value for item in graph.unresolved),
        )

    career_shishens = _shishens(_node(graph, inference.selected_pillar))
    left_shishens = _shishens(_node(graph, left_position))
    employment = bool(career_shishens & _EMPLOYMENT_CAREER) and bool(
        left_shishens & _EMPLOYMENT_LEFT
    )
    entrepreneurship = bool(career_shishens & _ENTREPRENEURSHIP_CAREER) and bool(
        left_shishens & _ENTREPRENEURSHIP_LEFT
    )

    evidence: list[str] = []
    if employment:
        evidence.extend(
            (
                f"natal:career:{inference.selected_pillar.value}:officer_killing",
                f"natal:left:{left_position.value}:seal",
            )
        )
    if entrepreneurship:
        evidence.extend(
            (
                f"natal:career:{inference.selected_pillar.value}:wealth",
                f"natal:left:{left_position.value}:output",
            )
        )

    return NatalCareerDecision(
        inclination=NatalCareerInclination(
            employment_inclined=employment,
            entrepreneurship_inclined=entrepreneurship,
            evidence_refs=tuple(evidence),
        ),
        abstain_reason=None if evidence else "insufficient_natal_relation_evidence",
        applicability_conditions=(
            "employment_requires_officer_killing_plus_left_seal",
            "entrepreneurship_requires_wealth_plus_left_output",
        ),
        counter_evidence=() if evidence else ("no_complete_discrete_chain",),
        unresolved_refs=tuple(item.topic.value for item in graph.unresolved),
    )


def _invalid_or_overlapping(stages: tuple[object, ...]) -> bool:
    intervals: list[tuple[date, date]] = []
    for stage in stages:
        start = getattr(stage, "start_date", None)
        end = getattr(stage, "end_date", None)
        ganzhi = getattr(stage, "ganzhi", None)
        if not isinstance(start, date) or not isinstance(end, date) or start > end:
            return True
        if not isinstance(ganzhi, str):
            return True
        try:
            GanZhi.parse(ganzhi)
        except (TypeError, ValueError):
            return True
        intervals.append((start, end))
    intervals.sort()
    return any(current[0] <= previous[1] for previous, current in zip(intervals, intervals[1:]))


def _dayun_relations(dayun: GanZhi, nodes: Iterable[PillarNode]) -> tuple[bool, bool, tuple[str, ...]]:
    opens = False
    suppresses = False
    evidence: list[str] = []
    for node in nodes:
        if gan_he(dayun.gan, node.gan) is not None or zhi_liuhe(dayun.zhi, node.zhi) is not None:
            opens = True
            evidence.append(f"dayun:{dayun.gan}{dayun.zhi}:opens:{node.pillar.value}:combination")
        destructive: list[str] = []
        if zhi_chong(dayun.zhi, node.zhi):
            destructive.append("clash")
        if zhi_xing(dayun.zhi, node.zhi) is not None:
            destructive.append("punishment")
        if zhi_chuan(dayun.zhi, node.zhi):
            destructive.append("harm")
        if zhi_po(dayun.zhi, node.zhi):
            destructive.append("break")
        if destructive:
            suppresses = True
            evidence.extend(
                f"dayun:{dayun.gan}{dayun.zhi}:suppresses:{node.pillar.value}:{relation}"
                for relation in destructive
            )
    return opens, suppresses, tuple(evidence)


def reason_dayun_career_context(
    *,
    graph: CareerRelationGraphResult,
    natal: NatalCareerInclination,
    as_of_date: date | None,
    stages: Iterable[object],
) -> DayunCareerDecision:
    """仅在截止日落入唯一、合法且互不重叠的大运区间时裁决。"""

    stage_tuple = tuple(stages)
    if as_of_date is None or not stage_tuple or _invalid_or_overlapping(stage_tuple):
        return DayunCareerDecision(None, "insufficient_dayun_information", False, None, None, None, ())

    matches = tuple(
        stage
        for stage in stage_tuple
        if stage.start_date <= as_of_date <= stage.end_date  # type: ignore[attr-defined]
    )
    if len(matches) != 1:
        return DayunCareerDecision(None, "insufficient_dayun_information", False, None, None, None, ())

    stage = matches[0]
    selected = graph.inference.selected_pillar
    left = graph.inference.left_pillar.pillar if graph.inference.left_pillar is not None else None
    if selected is None or left is None:
        return DayunCareerDecision(None, "insufficient_natal_relation_evidence", False, None, None, None, ())

    dayun = GanZhi.parse(stage.ganzhi)  # type: ignore[attr-defined]
    opens, suppresses, evidence = _dayun_relations(dayun, (_node(graph, selected), _node(graph, left)))
    opens_employment = opens and natal.employment_inclined
    opens_entrepreneurship = opens and natal.entrepreneurship_inclined
    suppresses_employment = suppresses and natal.employment_inclined
    suppresses_entrepreneurship = suppresses and natal.entrepreneurship_inclined
    conflict = (opens_employment and suppresses_employment) or (
        opens_entrepreneurship and suppresses_entrepreneurship
    )
    mechanisms = []
    if opens:
        mechanisms.append("大运与职业柱或左柱形成合，开放原局已成立路径")
    if suppresses:
        mechanisms.append("大运与职业柱或左柱形成冲刑害破，抑制原局已成立路径")
    if not mechanisms:
        mechanisms.append("大运未与原局职业链形成契约支持的开放或抑制关系")

    context = DayunCareerContext(
        opens_employment=opens_employment,
        opens_entrepreneurship=opens_entrepreneurship,
        suppresses_employment=suppresses_employment,
        suppresses_entrepreneurship=suppresses_entrepreneurship,
        mechanism="；".join(mechanisms),
    )
    return DayunCareerDecision(
        context=context,
        abstain_reason="mixed_signal" if conflict else None,
        has_conflict=conflict,
        stage_sequence=getattr(stage, "sequence", None),
        stage_start_date=stage.start_date,  # type: ignore[attr-defined]
        stage_end_date=stage.end_date,  # type: ignore[attr-defined]
        evidence_refs=evidence,
    )


def adapt_reality_career_status(track: RealityTrack) -> RealityCareerStatus:
    """把已核验职业现实状态单向适配为职业状态，不接受命理参数。"""

    entries = tuple(
        entry
        for entry in track.active_states
        if entry.domain == "career" and entry.value in _REALITY_VALUES
    )
    values = {entry.value for entry in entries}
    if "transitioning" in values:
        current = "transitioning"
    elif "mixed" in values or {"employed", "entrepreneurial"} <= values:
        current = "mixed"
    elif "entrepreneurial" in values:
        current = "entrepreneurial"
    elif "employed" in values:
        current = "employed"
    else:
        current = "unknown"

    events = tuple(dict.fromkeys(entry.source_event_id for entry in entries))
    history = tuple(
        {
            "state_id": entry.state_id,
            "value": entry.value,
            "event_id": entry.source_event_id,
            "effective_from": entry.effective_from.isoformat(),
        }
        for entry in sorted(entries, key=lambda item: (item.effective_from, item.state_id))
    )
    return RealityCareerStatus(current=current, verified_events=events, transition_history=history)


__all__ = (
    "DayunCareerDecision",
    "NatalCareerDecision",
    "adapt_reality_career_status",
    "reason_dayun_career_context",
    "reason_natal_career_inclination",
)
