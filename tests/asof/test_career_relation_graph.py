import json
from typing import Any

import pytest

from engine.asof.career_relation_contract import (
    AbstentionReason,
    CandidateStatus,
    PillarPosition,
    RelationType,
    SelectionStage,
)
from engine.asof.career_relation_graph import (
    UnresolvedTopic,
    build_career_relation_graph,
)
from engine.predicates.types import Bazi, GanZhi


def _bazi(year: str, month: str, day: str, hour: str) -> Bazi:
    return Bazi(
        年柱=GanZhi.parse(year),
        月柱=GanZhi.parse(month),
        日柱=GanZhi.parse(day),
        时柱=GanZhi.parse(hour),
    )


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False


def test_builds_four_pillar_nodes_with_hidden_stems_ten_gods_and_palaces() -> None:
    result = build_career_relation_graph(_bazi("庚申", "戊寅", "壬子", "辛丑"))

    assert [node.pillar for node in result.graph.pillars] == [
        PillarPosition.YEAR,
        PillarPosition.MONTH,
        PillarPosition.DAY,
        PillarPosition.HOUR,
    ]
    assert [node.palace.value for node in result.graph.pillars] == [
        "other_palace",
        "other_palace",
        "self_palace",
        "self_palace",
    ]
    hour = result.graph.pillars[-1]
    assert (hour.gan, hour.zhi, hour.stem_shishen) == ("辛", "丑", "正印")
    assert {item.gan: item.shishen for item in hour.hidden_stems} == {
        "己": "正官",
        "癸": "劫财",
        "辛": "正印",
    }


def test_trace_always_covers_frozen_five_steps_and_marks_unsupported_steps() -> None:
    result = build_career_relation_graph(_bazi("甲子", "乙卯", "壬子", "癸亥"))

    assert tuple(item.stage for item in result.stage_trace) == tuple(SelectionStage)
    assert result.stage_trace[1].found_pillars == ()
    assert "unresolved" in result.stage_trace[1].note
    assert result.stage_trace[4].found_pillars == ()
    assert "unresolved" in result.stage_trace[4].note
    assert {item.topic for item in result.unresolved} == {
        UnresolvedTopic.ROOTING_STRENGTH,
        UnresolvedTopic.FOUR_STATE_POWER,
        UnresolvedTopic.TOMB_RELATION,
        UnresolvedTopic.FORMATION_STAR,
    }


def test_step_one_selects_unique_self_palace_officer_and_characterizes_left_pillar() -> None:
    result = build_career_relation_graph(_bazi("庚申", "戊寅", "壬子", "辛丑"))

    assert result.inference.selected_pillar is PillarPosition.HOUR
    assert result.inference.left_pillar is not None
    assert result.inference.left_pillar.pillar is PillarPosition.DAY
    assert result.left_pillar_characterization.career_pillar is PillarPosition.HOUR
    assert result.left_pillar_characterization.pillar is PillarPosition.DAY
    assert result.left_pillar_characterization.gan == "壬"
    assert result.left_pillar_characterization.zhi == "子"


def test_step_three_requires_a_proven_relation_to_hour() -> None:
    linked = build_career_relation_graph(_bazi("戊寅", "乙卯", "壬子", "丁亥"))
    unlinked = build_career_relation_graph(_bazi("己卯", "甲午", "壬子", "庚申"))

    assert linked.inference.selected_pillar is PillarPosition.YEAR
    selected = next(
        item for item in linked.inference.candidates if item.status is CandidateStatus.SELECTED
    )
    assert selected.stage is SelectionStage.OTHER_OFFICER_KILLING_LINKED_TO_HOUR
    assert any(
        relation.source is PillarPosition.HOUR or relation.target is PillarPosition.HOUR
        for relation in selected.relations
    )
    assert unlinked.stage_trace[2].found_pillars == ()
    assert all(
        item.stage is not SelectionStage.OTHER_OFFICER_KILLING_LINKED_TO_HOUR
        for item in unlinked.inference.candidates
    )


def test_step_four_prefers_self_palace_and_only_falls_back_to_other_palace() -> None:
    self_result = build_career_relation_graph(_bazi("甲子", "乙卯", "壬子", "丁亥"))
    other_result = build_career_relation_graph(_bazi("丁卯", "甲子", "壬子", "癸亥"))

    assert self_result.inference.selected_pillar is PillarPosition.HOUR
    assert self_result.stage_trace[3].found_pillars == (PillarPosition.HOUR,)
    assert "other_palace not scanned" in self_result.stage_trace[3].note
    assert other_result.inference.selected_pillar is PillarPosition.YEAR
    assert other_result.stage_trace[3].found_pillars == (PillarPosition.YEAR,)


def test_left_pillar_boundary_for_selected_year_is_explicit_and_characterization_is_empty() -> None:
    result = build_career_relation_graph(_bazi("丁卯", "甲子", "壬子", "癸亥"))

    assert result.inference.selected_pillar is PillarPosition.YEAR
    assert result.inference.left_pillar is not None
    assert result.inference.left_pillar.pillar is None
    assert result.left_pillar_characterization.career_pillar is PillarPosition.YEAR
    assert result.left_pillar_characterization.pillar is None
    assert result.left_pillar_characterization.gan is None
    assert result.left_pillar_characterization.zhi is None
    assert result.left_pillar_characterization.hidden_shishen == ()


def test_multiple_top_priority_candidates_remain_an_explicit_conflict() -> None:
    result = build_career_relation_graph(_bazi("甲子", "乙丑", "壬戌", "己未"))

    assert result.inference.selected_pillar is None
    assert result.inference.left_pillar is None
    assert result.left_pillar_characterization is None
    assert (
        result.inference.abstention_reason
        is AbstentionReason.MULTIPLE_TOP_PRIORITY_CANDIDATES
    )
    winners = [
        item
        for item in result.inference.candidates
        if item.stage is SelectionStage.SELF_OFFICER_KILLING
    ]
    assert {item.pillar for item in winners} == {
        PillarPosition.DAY,
        PillarPosition.HOUR,
    }
    assert {item.status for item in winners} == {CandidateStatus.CONFLICT}


def test_graph_emits_only_cross_pillar_exact_hidden_stem_roots() -> None:
    result = build_career_relation_graph(_bazi("甲子", "己丑", "丙寅", "辛巳"))
    rooted = {
        (relation.source, relation.target, relation.evidence_refs)
        for relation in result.graph.relations
        if relation.relation_type is RelationType.ROOTED
    }

    assert rooted == {
        (PillarPosition.YEAR, PillarPosition.DAY, ("root_exists:甲:寅:year-day",)),
        (PillarPosition.DAY, PillarPosition.HOUR, ("root_exists:丙:巳:day-hour",)),
        (PillarPosition.HOUR, PillarPosition.MONTH, ("root_exists:辛:丑:hour-month",)),
    }
    assert all(source is not target for source, target, _ in rooted)
    assert UnresolvedTopic.ROOTING_STRENGTH in {
        signal.topic for signal in result.unresolved
    }


def test_graph_contains_only_repository_supported_deterministic_relation_types() -> None:
    first = build_career_relation_graph(_bazi("甲子", "己丑", "丙寅", "辛巳"))
    second = build_career_relation_graph(_bazi("甲子", "乙丑", "丙寅", "庚午"))
    relation_types = {
        relation.relation_type
        for result in (first, second)
        for relation in result.graph.relations
    }

    assert {
        RelationType.ADJACENT,
        RelationType.COMBINATION,
        RelationType.CLASH,
        RelationType.PUNISHMENT,
        RelationType.HARM,
        RelationType.HIDDEN_REVEALED,
        RelationType.ROOTED,
    } <= relation_types
    assert RelationType.ENTERS_TOMB not in relation_types


def test_canonical_output_is_deterministic_has_no_float_or_answer_leakage() -> None:
    chart = _bazi("戊寅", "乙卯", "壬子", "丁亥")

    outputs = [build_career_relation_graph(chart).to_canonical_json() for _ in range(3)]

    assert outputs[0] == outputs[1] == outputs[2]
    payload = json.loads(outputs[0])
    assert not _contains_float(payload)
    lowered = outputs[0].lower()
    for forbidden in ("occupation", "known_facts", "feedback", "entrepreneurship"):
        assert forbidden not in lowered


@pytest.mark.parametrize(
    "chart,error_type,match",
    [
        (object(), TypeError, "bazi must be"),
        (
            Bazi(
                年柱=GanZhi("X", "子"),
                月柱=GanZhi.parse("乙丑"),
                日柱=GanZhi.parse("丙寅"),
                时柱=GanZhi.parse("丁卯"),
            ),
            ValueError,
            "invalid gan for year",
        ),
        (
            Bazi(
                年柱=GanZhi("甲", "X"),
                月柱=GanZhi.parse("乙丑"),
                日柱=GanZhi.parse("丙寅"),
                时柱=GanZhi.parse("丁卯"),
            ),
            ValueError,
            "invalid zhi for year",
        ),
        (
            Bazi(
                年柱=GanZhi("甲", "丑"),
                月柱=GanZhi.parse("乙丑"),
                日柱=GanZhi.parse("丙寅"),
                时柱=GanZhi.parse("丁卯"),
            ),
            ValueError,
            "invalid jiazi for year",
        ),
    ],
)
def test_rejects_non_bazi_invalid_symbols_and_invalid_jiazi(
    chart: object, error_type: type[Exception], match: str
) -> None:
    with pytest.raises(error_type, match=match):
        build_career_relation_graph(chart)  # type: ignore[arg-type]
