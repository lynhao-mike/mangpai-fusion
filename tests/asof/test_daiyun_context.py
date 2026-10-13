from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from engine.asof.daiyun_context import (
    DaiyunStage,
    NatalRelation,
    PathChange,
    adapt_daiyun_segment,
)
from engine.asof.natal_capacity import EvidenceRef
from engine.yingqi.retrospective import DaiyunSegment


def _evidence(locator: str, excerpt: str) -> EvidenceRef:
    return EvidenceRef(
        source="cases/C-2026-028-乾-壬戌癸卯壬子乙巳/input.md",
        locator=locator,
        excerpt=excerpt,
    )


def _segment() -> DaiyunSegment:
    return DaiyunSegment(
        seq=4,
        ganzhi="丙寅",
        age_range=(33, 42),
        year_range=(2014, 2024),
        feature="丙财 + 寅支气",
        typical_domains=["财富", "婚姻"],
    )


def test_adapter_is_deterministic_and_preserves_half_open_time_semantics() -> None:
    kwargs = {"applicability_conditions": ("事业结构证据独立通过",)}
    first = adapt_daiyun_segment(_segment(), **kwargs)
    second = adapt_daiyun_segment(_segment(), **kwargs)
    assert first == second
    assert first.start_date == date(2014, 1, 1)
    assert first.end_date == date(2023, 12, 31)
    assert first.sequence == 4
    assert first.ganzhi == "丙寅"
    with pytest.raises(FrozenInstanceError):
        first.domain_tendency = "open"  # type: ignore[misc]


def test_free_text_is_retained_as_unresolved_and_never_maps_paths() -> None:
    stage = adapt_daiyun_segment(
        _segment(),
        applicability_conditions=("尚无结构化路径裁决",),
    )
    assert stage.opened_paths == ()
    assert stage.closed_paths == ()
    assert stage.amplified_paths == ()
    assert stage.suppressed_paths == ()
    assert stage.repaired_paths == ()
    assert stage.redirected_paths == ()
    assert stage.domain_tendency == "undetermined"
    assert {ref.locator.rsplit(".", 1)[-1] for ref in stage.unresolved_signal_refs} == {
        "feature",
        "typical_domains",
    }


def test_structured_path_changes_require_explicit_traceable_input() -> None:
    relation_evidence = _evidence("大运.排布[4]", "丙寅 2014-2024")
    change = PathChange("organization-responsibility", "阶段放大组织权责路径", (relation_evidence,))
    relation = NatalRelation("career-authority", "大运信号作用于原局权责节点", (relation_evidence,))
    stage = adapt_daiyun_segment(
        _segment(),
        amplified_paths=(change,),
        natal_relations=(relation,),
        domain_tendency="open",
        applicability_conditions=("原局权责节点存在", "阶段信号独立成立"),
        counter_evidence=(_evidence("四柱.时柱", "乙巳/伤官"),),
    )
    assert stage.amplified_paths == (change,)
    assert stage.natal_relations == (relation,)
    assert stage.applicability_conditions
    assert stage.counter_evidence
    assert stage.signal_refs[0].locator == "segment[4].year_range"


def test_asof_stage_is_not_the_existing_retrospective_container() -> None:
    assert DaiyunStage is not DaiyunSegment
    assert not issubclass(DaiyunStage, DaiyunSegment)
    assert "flow_years" not in DaiyunStage.__dataclass_fields__
    assert "feature" not in DaiyunStage.__dataclass_fields__
    assert "typical_domains" not in DaiyunStage.__dataclass_fields__
