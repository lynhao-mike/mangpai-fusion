"""H9 · GateResult.event_type_hypotheses round-trip + 注入逻辑

落地：plans/architecture-v1.4.md § 六 H9（决策 V4，已实现）
契约：engine/contracts/03-findings-schema.md § 七（GateResult schema）
代码：engine/yingqi/types.py + engine/yingqi/gate._infer_event_type_hypotheses

要求：
    1. 默认 event_type_hypotheses=[]（向后兼容）
    2. to_dict / from_dict / to_json / from_json 完整 round-trip
    3. 旧 JSON（无字段）反序列化 → 默认空列表
    4. 注入逻辑：体制内 + 财源 → ["职级升迁", "财源/置业"]
    5. 已是升迁事件 / 非体制 / 婚姻域 / 空 industry_pointers → 不注入
"""
from __future__ import annotations

import json

import pytest


pytestmark = [pytest.mark.v1_3_acceptance, pytest.mark.v1_4_acceptance]


def _make_gate_result(**overrides):
    from engine.yingqi.types import GateResult, LayerCheck
    base = dict(
        year=2010, candidate_event="财源", domain="财运",
        layer1=LayerCheck(layer="L1_原局有", passed=True),
        layer2=LayerCheck(layer="L2_大运到位", passed=True),
        layer3=LayerCheck(layer="L3_流年引爆", passed=True),
        passed_layers=3,
    )
    base.update(overrides)
    return GateResult(**base)


def _make_picture(pointers):
    from engine.picture.types import PictureFindings
    return PictureFindings(industry_pointers=pointers)


# ============================================================
# round-trip
# ============================================================

def test_h9_default_empty_list():
    gr = _make_gate_result()
    assert gr.event_type_hypotheses == [], \
        f"默认应为空 list，得到 {gr.event_type_hypotheses}"


def test_h9_round_trip_via_json():
    """填值 → to_json → from_json → 一致。"""
    from engine.yingqi.types import GateResult

    gr = _make_gate_result(event_type_hypotheses=["职级升迁", "财源/置业"])
    back = GateResult.from_json(gr.to_json())
    assert back.event_type_hypotheses == ["职级升迁", "财源/置业"]
    assert gr.to_dict() == back.to_dict()


def test_h9_round_trip_preserves_hash():
    """同字段 round-trip 后 hash 一致（保证 statement_id 稳定性 / D1 锚点）。"""
    gr = _make_gate_result(event_type_hypotheses=["职级升迁", "财源/置业"])
    from engine.yingqi.types import GateResult
    back = GateResult.from_json(gr.to_json())
    assert gr.hash() == back.hash(), "round-trip 后 hash 应一致"


def test_h9_legacy_json_default_empty():
    """旧 JSON（无 event_type_hypotheses 字段）反序列化 → 空 list（向后兼容）。"""
    from engine.yingqi.types import GateResult

    legacy_json = {
        "year": 2005, "candidate_event": "结婚", "domain": "婚姻",
        "layer1": {"layer": "L1_原局有", "passed": True,
                   "evidence_chars": [], "rationale": "",
                   "used_transition": False, "used_secondary_keys": False},
        "layer2": {"layer": "L2_大运到位", "passed": True,
                   "evidence_chars": [], "rationale": "",
                   "used_transition": False, "used_secondary_keys": False},
        "layer3": {"layer": "L3_流年引爆", "passed": True,
                   "evidence_chars": [], "rationale": "",
                   "used_transition": False, "used_secondary_keys": False},
        "passed_layers": 3, "triggers": [], "primary_trigger": None, "door": None,
        "confidence": None,
        # 故意省略 event_type_hypotheses
    }
    gr = GateResult.from_json(json.dumps(legacy_json))
    assert gr.event_type_hypotheses == [], \
        f"旧 JSON 反序列化应得空 list，得到 {gr.event_type_hypotheses}"


def test_h9_filling_then_dict_serializes_field():
    """填值后 to_dict 一定包含此键（哪怕空）。"""
    gr_empty = _make_gate_result()
    gr_full = _make_gate_result(event_type_hypotheses=["A", "B"])
    assert "event_type_hypotheses" in gr_empty.to_dict()
    assert gr_full.to_dict()["event_type_hypotheses"] == ["A", "B"]


# ============================================================
# 注入逻辑（_infer_event_type_hypotheses）
# ============================================================

def test_h9_inject_institutional_财源():
    """体制内 + 财源事件 → 注入双解。"""
    from engine.yingqi.gate import _infer_event_type_hypotheses
    r = _infer_event_type_hypotheses("财运", "财源/置业",
                                      _make_picture(["公门"]))
    assert r == ["职级升迁", "财源/置业"]


def test_h9_no_inject_for_already_promotion_event():
    """已是"升迁"类事件 → 不重复注入。"""
    from engine.yingqi.gate import _infer_event_type_hypotheses
    r = _infer_event_type_hypotheses("事业", "升迁副处",
                                      _make_picture(["公门"]))
    assert r == []


def test_h9_no_inject_for_non_institutional():
    """非体制行业（技术/制造）→ 不注入。"""
    from engine.yingqi.gate import _infer_event_type_hypotheses
    r = _infer_event_type_hypotheses("财运", "财源/置业",
                                      _make_picture(["技术/制造"]))
    assert r == []


def test_h9_no_inject_for_marriage_domain():
    """婚姻域 → 不注入（V4 仅适用 财运/事业）。"""
    from engine.yingqi.gate import _infer_event_type_hypotheses
    r = _infer_event_type_hypotheses("婚姻", "结婚",
                                      _make_picture(["公门"]))
    assert r == []


def test_h9_no_inject_for_empty_pointers():
    """空 industry_pointers → 不注入。"""
    from engine.yingqi.gate import _infer_event_type_hypotheses
    r = _infer_event_type_hypotheses("财运", "财源",
                                      _make_picture([]))
    assert r == []


@pytest.mark.parametrize("pointer", ["公门", "国企", "体制", "事业单位",
                                      "选调", "公务员", "正处", "副厅"])
def test_h9_inject_for_all_institutional_keywords(pointer):
    """所有体制内关键词都应触发注入。"""
    from engine.yingqi.gate import _infer_event_type_hypotheses
    r = _infer_event_type_hypotheses("财运", "财动婚动",
                                      _make_picture([pointer]))
    assert r == ["职级升迁", "财源/置业"], f"关键词 {pointer!r} 未触发注入"
