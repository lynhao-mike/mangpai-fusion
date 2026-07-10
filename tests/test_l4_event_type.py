from __future__ import annotations

from engine.decision.v5_adapter import classify_event_type


ALLOWED_EVENT_TYPES = {
    "车祸",
    "手术",
    "疾病",
    "婚变",
    "结婚",
    "发财",
    "破财",
    "升迁",
    "换岗",
    "创业",
    "学历",
    "事业变动",
    "财务变动",
    "婚恋变动",
    "健康风险",
    "学习节点",
    "待具体化事件",
}


def test_classifies_specific_events_from_label():
    assert classify_event_type("天干戊土透出+地支有冲=车祸最明显标志组合", "婚姻") == "车祸"
    assert classify_event_type("库有开关之分→冲开=发财", "财富") == "发财"
    assert classify_event_type("晚婚或多婚成定律", "婚姻") == "婚变"
    assert classify_event_type("考试、证照、培训、学历或技能升级出现可反馈节点", "学业") == "学历"


def test_falls_back_to_domain_generic_when_no_keyword():
    assert classify_event_type("段建业规则参与：体的分类 — 工具", "事业") == "事业变动"
    assert classify_event_type("", "财富") == "财务变动"
    assert classify_event_type("无匹配文本", "婚姻") == "婚恋变动"
    assert classify_event_type("无匹配文本", "健康") == "健康风险"


def test_unknown_domain_falls_back_to_placeholder():
    assert classify_event_type("无匹配", "总体") == "待具体化事件"


def test_events_no_longer_use_placeholder_event_type():
    from engine.decision import decision_run_from_v5
    from engine.v5 import run_v5

    output = run_v5({"case_id": "C-TEST-R8", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    run = decision_run_from_v5(output)

    event_types = {event.event_type for event in run.event_hypotheses}
    assert "v5_prediction" not in event_types
    assert event_types
    assert event_types <= ALLOWED_EVENT_TYPES
    assert run.validate_trace() == []
