from dataclasses import replace

from engine.asof.daiyun_context import (
    DaiyunStage,
    PathTendencySuggestion,
    adapt_daiyun_segment,
    suggest_daiyun_path_tendencies,
)
from engine.predicates.types import GanZhi, ParsedInput
from engine.yingqi.retrospective import DaiyunSegment
from tests.fixtures.cases import load_case


_FIVE_CLASSES = {"比劫", "食伤", "财", "官杀", "印"}


def test_suggests_structural_path_tendencies_without_mutating_stage() -> None:
    parsed = load_case("C-2026-001")
    assert isinstance(parsed, ParsedInput)
    bazi = replace(parsed.bazi, 日柱=GanZhi.parse("庚午"))
    stage = adapt_daiyun_segment(
        DaiyunSegment(
            seq=1,
            ganzhi="壬子",
            age_range=(8, 17),
            year_range=(1988, 1998),
            feature="",
            typical_domains=[],
        ),
        applicability_conditions=("路径变化仍需人工裁决",),
    )
    stage_before = stage

    suggestion = suggest_daiyun_path_tendencies(GanZhi.parse("壬子"), bazi)

    assert isinstance(suggestion, PathTendencySuggestion)
    assert suggestion.stem_class in _FIVE_CLASSES
    assert suggestion.branch_class in _FIVE_CLASSES
    assert suggestion.note
    assert "启发式" in suggestion.note or "喜忌" in suggestion.note
    assert suggestion.stem_class == "食伤"
    assert "技术输出" in suggestion.open_or_amplify_domains
    assert isinstance(stage, DaiyunStage)
    assert stage == stage_before
    assert stage.opened_paths == ()
    assert stage.closed_paths == ()
    assert stage.amplified_paths == ()
    assert stage.suppressed_paths == ()
    assert stage.repaired_paths == ()
    assert stage.redirected_paths == ()
