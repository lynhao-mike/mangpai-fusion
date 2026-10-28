"""tests/claims/test_claim_contract.py · T-150 度量契约 v1 回归（契约 23 §5.1）。

守五件事（本文件只新建，不改任何既有测试或断言）：

1. 判定表 9 行：`triggered` / `outcome` / `state` 逐行断言（含三值逻辑，未知不得折叠）；
2. 负对照：`preconditions` 含未知原子 → `triggered is None`，且**不是** `False`；
3. 计分器玩具集手算：3 例（含一例多字母预测），断言 scored / correct / accuracy / 两个基线；
4. 预注册缺失或字段缺失 → 退出码 2（fail-closed）；
5. `n_scored == 0` → 抛 `MetricError`，禁止 0/0 静默出分。
"""
from __future__ import annotations

import json

import pytest

from engine.api import analyze_facts, to_jsonable
from engine.claims.condition_ir import build_context, evaluate_claim
from engine.claims.metrics import MetricError, score
from tools.claim_metric import main as claim_metric_main

# 与既有条件测试同盘：庚申 戊寅 壬子 辛丑，日主壬（确定性事实来自 engine.api）
PILLARS = ["庚申", "戊寅", "壬子", "辛丑"]
DAY_MASTER = "壬"
PAIR_ID = "PAIR-1"

TRUE_ATOM = {"atom": "day_master", "args": {"gan": DAY_MASTER}}
FALSE_ATOM = {"atom": "day_master", "args": {"gan": "甲"}}
UNKNOWN_ATOM = {"atom": "needs_judgment", "args": {"reason": "未量化：行运是否走财运"}}
INVALIDATOR_FALSE = {"any": [FALSE_ATOM]}


@pytest.fixture(scope="module")
def ctx() -> dict:
    return build_context(to_jsonable(analyze_facts(pillars=list(PILLARS), gender="乾")))


def _claim(preconditions, *, invalidators=None, framework="standalone",
           frame_atom=None, pair_with=None) -> dict:
    spec = {
        "preconditions": preconditions,
        "invalidators": INVALIDATOR_FALSE if invalidators is None else invalidators,
        "framework_dependency": framework,
    }
    if frame_atom is not None:
        spec["frame_atom"] = frame_atom
    if pair_with is not None:
        spec["pair_with"] = pair_with
    return {"id": "T150-CONTRACT", "conditions_v2": spec}


def _pair_claim() -> dict:
    return _claim(TRUE_ATOM, framework="requires_pair", pair_with=[PAIR_ID])


def _frame_claim(frame_atom=None) -> dict:
    """frame_atom 传 None 即整段缺失（`_claim` 会省略该键）。"""
    return _claim(TRUE_ATOM, framework="requires_school_frame", frame_atom=frame_atom)


# ---------------------------------------------------------------- ① 判定表 9 行

def test_table_row1_preconditions_false(ctx):
    out = evaluate_claim(_claim(FALSE_ATOM), ctx)
    assert (out["triggered"], out["outcome"], out["state"]) == (False, "unknown", "rejected")


def test_table_row2_preconditions_unknown(ctx):
    out = evaluate_claim(_claim({"all": [TRUE_ATOM, UNKNOWN_ATOM]}), ctx)
    assert (out["triggered"], out["outcome"], out["state"]) == (None, "unknown", "needs_fact")


def test_table_row3_pair_false(ctx):
    out = evaluate_claim(_pair_claim(), {**ctx, "cited": {PAIR_ID: False}})
    assert (out["triggered"], out["outcome"], out["state"]) == (False, "unknown", "rejected")


def test_table_row4_pair_unknown_or_missing(ctx):
    # 配对命题为 None 或整条缺失，都是「还没裁决」→ triggered=None，不是 False
    for cited in ({}, {PAIR_ID: None}):
        out = evaluate_claim(_pair_claim(), {**ctx, "cited": cited})
        assert (out["triggered"], out["outcome"], out["state"]) == (None, "unknown", "evidence_only")


def test_table_row5_frame_missing_or_unknown(ctx):
    # frame_atom 缺失、frame_atom 求值为 None：都降为旁证，triggered 未知
    for claim in (_frame_claim(), _frame_claim(frame_atom=UNKNOWN_ATOM)):
        out = evaluate_claim(claim, ctx)
        assert (out["triggered"], out["outcome"], out["state"]) == (None, "unknown", "evidence_only")


def test_table_row6_frame_false(ctx):
    out = evaluate_claim(_frame_claim(frame_atom=FALSE_ATOM), ctx)
    assert (out["triggered"], out["outcome"], out["state"]) == (False, "unknown", "evidence_only")


def test_table_row7_invalidator_true(ctx):
    out = evaluate_claim(_claim(TRUE_ATOM, invalidators={"any": [TRUE_ATOM]}), ctx)
    assert (out["triggered"], out["outcome"], out["state"]) == (True, "fail", "rejected")


def test_table_row8_invalidator_false(ctx):
    out = evaluate_claim(_claim(TRUE_ATOM, invalidators=INVALIDATOR_FALSE), ctx)
    assert (out["triggered"], out["outcome"], out["state"]) == (True, "success", "candidate")


def test_table_row9_invalidator_unknown(ctx):
    out = evaluate_claim(_claim(TRUE_ATOM, invalidators={"any": [UNKNOWN_ATOM]}), ctx)
    assert (out["triggered"], out["outcome"], out["state"]) == (True, "unknown", "candidate")


def test_contract_invariants_hold_for_every_row(ctx):
    """硬规则：triggered 不是 True 时 outcome 必为 unknown；三值集合不得出现第四值。"""
    outputs = [
        evaluate_claim(_claim(FALSE_ATOM), ctx),
        evaluate_claim(_claim({"all": [TRUE_ATOM, UNKNOWN_ATOM]}), ctx),
        evaluate_claim(_pair_claim(), {**ctx, "cited": {PAIR_ID: False}}),
        evaluate_claim(_pair_claim(), {**ctx, "cited": {}}),
        evaluate_claim(_frame_claim(), ctx),
        evaluate_claim(_frame_claim(frame_atom=UNKNOWN_ATOM), ctx),
        evaluate_claim(_frame_claim(frame_atom=FALSE_ATOM), ctx),
        evaluate_claim(_claim(TRUE_ATOM, invalidators={"any": [TRUE_ATOM]}), ctx),
        evaluate_claim(_claim(TRUE_ATOM, invalidators=INVALIDATOR_FALSE), ctx),
        evaluate_claim(_claim(TRUE_ATOM, invalidators={"any": [UNKNOWN_ATOM]}), ctx),
    ]
    for out in outputs:
        assert out["triggered"] in (True, False, None)
        assert out["outcome"] in ("success", "fail", "unknown")
        if out["triggered"] is not True:
            assert out["outcome"] == "unknown", out
        # 旧字段仍在（向后兼容）
        for key in ("state", "value", "reason", "bindings", "failed_atoms",
                    "unknown_facts", "near_miss", "framework"):
            assert key in out


# ---------------------------------------------------------------- ② 负对照

def test_negative_control_unknown_is_none_not_false(ctx):
    out = evaluate_claim(_claim({"all": [TRUE_ATOM, UNKNOWN_ATOM]}), ctx)
    assert out["triggered"] is None
    assert out["triggered"] is not False
    assert out["state"] == "needs_fact"
    assert out["unknown_facts"], "未知必须显性记录，不得静默折叠"


# ---------------------------------------------------------------- ③ 计分器手算

TOY_PROTOCOL = {
    "protocol_id": "toy-v1",
    "claim_id": "TOY-001",
    "frozen_at": "2026-10-28T00:00:00+08:00",
    "commit": "pre-T-151",
    "trigger_definition": "前置条件与框架前置全部成立",
    "direction_rule": "原文方向 -> 标签，不追认答案",
    "label_map": {"one": ["A"], "two": ["A", "B"]},
    "prediction_rule": {"self_controls": "one"},
    "scored_set_rule": "triggered is true 且预测非空且有答案",
    "baseline": "baseline_single",
    "decision_rule": "accuracy 严格高于 baseline_single",
}

# 手算：答案 B / A / A；t1 单字母对、t2 多字母对、t3 单字母错。
TOY_CASES = [
    {"case_id": "t1", "claim_id": "TOY-001", "branch": "self_controls",
     "triggered": True, "outcome": "success", "prediction_letters": ["B"], "answer_letter": "B"},
    {"case_id": "t2", "claim_id": "TOY-001", "branch": "self_controls",
     "triggered": True, "outcome": "fail", "prediction_letters": ["A", "B"], "answer_letter": "A"},
    {"case_id": "t3", "claim_id": "TOY-001", "branch": "self_controls",
     "triggered": True, "outcome": "unknown", "prediction_letters": ["C"], "answer_letter": "A"},
]


def test_scorer_three_case_hand_computed():
    result = score(TOY_CASES, TOY_PROTOCOL)

    assert result["n_total"] == 3
    assert result["n_scored"] == 3
    assert result["n_correct"] == 2
    assert result["n_abstain"] == 0
    assert result["n_not_triggered"] == 0
    assert result["n_missing_answer"] == 0
    assert result["accuracy"] == 0.6667

    # 判定基线：scored 集答案 A/A/B，最多的是 A（2/3）
    assert result["baseline_single"] == {"letter": "A", "hits": 2, "accuracy": 0.6667}
    # 同基数乐观上界：k=1 → {A}（t1 错、t3 对）；k=2 → {A,B}（t2 对）
    assert result["baseline_same_k"]["hits"] == 2
    assert result["baseline_same_k"]["accuracy"] == 0.6667
    assert result["baseline_same_k"]["by_k"]["1"] == {
        "letters": ["A"], "hits": 1, "n": 2, "accuracy": 0.5}
    assert result["baseline_same_k"]["by_k"]["2"] == {
        "letters": ["A", "B"], "hits": 1, "n": 1, "accuracy": 1.0}

    assert result["by_branch"]["self_controls"] == {"n": 3, "correct": 2, "accuracy": 0.6667}
    assert len(result["input_sha256"]) == 64
    # 确定性：同一输入两次逐字节一致
    assert json.dumps(score(TOY_CASES, TOY_PROTOCOL), sort_keys=True) == \
        json.dumps(result, sort_keys=True)


def test_scorer_excludes_unscorable_cases():
    cases = TOY_CASES + [
        {"case_id": "t4", "branch": "self_controls", "triggered": True,
         "outcome": "unknown", "prediction_letters": [], "answer_letter": "A"},
        {"case_id": "t5", "branch": "self_controls", "triggered": False,
         "outcome": "unknown", "prediction_letters": ["A"], "answer_letter": "A"},
        {"case_id": "t6", "branch": "self_controls", "triggered": True,
         "outcome": "success", "prediction_letters": ["A"], "answer_letter": None},
    ]
    result = score(cases, TOY_PROTOCOL)
    assert (result["n_total"], result["n_scored"], result["n_correct"]) == (6, 3, 2)
    assert (result["n_abstain"], result["n_not_triggered"], result["n_missing_answer"]) == (1, 1, 1)


# ---------------------------------------------------------------- ④ 预注册 fail-closed

def _write(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_cli_valid_input_exits_0(tmp_path, capsys):
    protocol = _write(tmp_path, "protocol.json", TOY_PROTOCOL)
    cases = _write(tmp_path, "cases.json", {"cases": TOY_CASES})
    code = claim_metric_main(["--protocol", str(protocol), "--cases", str(cases), "--json"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert out["n_scored"] == 3 and out["accuracy"] == 0.6667


def test_cli_missing_protocol_file_exits_2(tmp_path, capsys):
    cases = _write(tmp_path, "cases.json", TOY_CASES)
    code = claim_metric_main(
        ["--protocol", str(tmp_path / "no-such-protocol.yaml"), "--cases", str(cases)])
    assert code == 2
    assert "拒绝出分" in capsys.readouterr().err


def test_cli_missing_protocol_field_exits_2(tmp_path, capsys):
    broken = {key: value for key, value in TOY_PROTOCOL.items() if key != "decision_rule"}
    protocol = _write(tmp_path, "protocol.json", broken)
    cases = _write(tmp_path, "cases.json", TOY_CASES)
    code = claim_metric_main(["--protocol", str(protocol), "--cases", str(cases)])
    assert code == 2
    err = capsys.readouterr().err
    assert "decision_rule" in err


def test_cli_missing_arguments_exits_2(capsys):
    assert claim_metric_main([]) == 2
    assert "--protocol" in capsys.readouterr().err


def test_validate_protocol_rejects_unknown_label():
    broken = dict(TOY_PROTOCOL, prediction_rule={"self_controls": "不存在的标签"})
    with pytest.raises(MetricError):
        score(TOY_CASES, broken)


# ---------------------------------------------------------------- ⑤ 0 分母

def test_scorer_rejects_empty_scored_set():
    cases = [
        {"case_id": "a", "branch": "self_controls", "triggered": False,
         "outcome": "unknown", "prediction_letters": ["A"], "answer_letter": "A"},
        {"case_id": "b", "branch": "self_controls", "triggered": True,
         "outcome": "unknown", "prediction_letters": [], "answer_letter": "A"},
        {"case_id": "c", "branch": "self_controls", "triggered": True,
         "outcome": "success", "prediction_letters": ["A"], "answer_letter": None},
    ]
    with pytest.raises(MetricError):
        score(cases, TOY_PROTOCOL)


def test_cli_empty_scored_set_exits_2(tmp_path, capsys):
    protocol = _write(tmp_path, "protocol.json", TOY_PROTOCOL)
    cases = _write(tmp_path, "cases.json", [
        {"case_id": "a", "branch": "self_controls", "triggered": False,
         "outcome": "unknown", "prediction_letters": ["A"], "answer_letter": "A"},
    ])
    assert claim_metric_main(["--protocol", str(protocol), "--cases", str(cases)]) == 2
    assert "0/0" in capsys.readouterr().err


def test_scorer_rejects_triggered_false_with_fail():
    """`triggered=False` + `outcome=fail` 是契约明令禁止的组合，必须拒绝。"""
    bad = [{"case_id": "x", "branch": "self_controls", "triggered": False,
            "outcome": "fail", "prediction_letters": ["A"], "answer_letter": "A"}]
    with pytest.raises(MetricError):
        score(bad, TOY_PROTOCOL)


def test_self_check_exits_0(capsys):
    assert claim_metric_main(["--self-check"]) == 0
    assert "PASSED" in capsys.readouterr().out


# ---------------------------------------------------------------- ⑥ §4 映射搬家护栏

def test_instrument_map_lives_in_meta_and_loads():
    from tools import tiekoulu_eval

    assert not hasattr(tiekoulu_eval, "PREDICTION_MAP"), "映射表必须已搬出工具"
    assert not hasattr(tiekoulu_eval, "NO_MAP_REASON")
    data = tiekoulu_eval.load_instrument_map()
    assert tiekoulu_eval.MAP_PATH.name == "claim-instrument-map-v1.yaml"
    assert data["schema"] == "claim-instrument-map/v1"
    assert set(data["prediction_map"]) == {
        "G-SP-165", "G-SP-293", "G-SP-071", "G-SP-130",
        "M1-D-298", "M2-Y-251", "M2-Y-014"}
    assert data["prediction_map"]["G-SP-165"]["predict"] == ["A", "B"]
    assert data["prediction_map"]["G-SP-130"]["predict"] == ["B"]
    assert set(data["no_map_reason"]) == {
        "M1-D-009", "M1-D-013", "M1-D-242", "M3-R-013", "M3-R-166"}
