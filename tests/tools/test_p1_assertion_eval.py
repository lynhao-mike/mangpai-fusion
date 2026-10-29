"""tests/tools/test_p1_assertion_eval.py · T-186 · P1′ 系统级断言评分器的合成 fixture 测试。

只测尺子，不测命理结论，也**不读真实 fresh-40**（真实答案/输出只由中枢跑）：

1. 六个记账桶：全对 / 全错（写反）/ abstain / missing / routing_claims / mutual；
2. routing 单列：routing 例不进 precision 分母，abstain 不记 ok/wrong；
3. 一等指标：total / precision / coverage / needs_judgment_rate / confident_error 的分子分母；
4. Wilson 95% 区间（参考值 + 边界）；
5. 预注册阈值钉死（改阈值 = 测试红），判定边界 kill / 灰区 / 次级门槛 / pass / not_evaluated；
6. 输入契约：未登记 direction、重复 case、多余 case、routing 非 needs_judgment、分母不对一律报错；
7. CLI：`--json` 退出码 0、缺 routing 文件 / 坏 routing 退出码 2；两次运行逐字节一致。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import p1_assertion_eval as mod

# ── 合成 fixture（手写，非任何真实盘）────────────────────────────────────────

PAIRS = [
    ("巳", "亥"), ("丑", "未"), ("子", "午"), ("卯", "酉"),
    ("辰", "戌"), ("寅", "申"), ("亥", "卯"), ("酉", "戌"),
]
MECHANISMS = ["冲", "合", "穿", "刑", "克", "生", "化", "墓"]
ROUTING_MECHANISMS = ["穿", "合", "刑", "冲", "穿"]


def answer_case(case_id: str, a: str, b: str, *, actor: str | None = None,
                mutual: bool = False, mechanism: str = "冲", kind: str = "制") -> dict:
    relation: dict = {"a": a, "b": b, "kind": kind, "mechanism": mechanism}
    if mutual:
        relation["mutual"] = True
    else:
        relation["actor"] = actor or a
    return {"case_id": case_id, "relation": relation, "source_ref": "sources/duan/fixture.md:L1"}


def routing_case(case_id: str, a: str, b: str, *, mechanism: str = "穿", kind: str = "制",
                 expected: str = mod.NEEDS_JUDGMENT) -> dict:
    return {
        "case_id": case_id, "a": a, "b": b, "kind": kind, "mechanism": mechanism,
        "expected_direction": expected, "source_ref": "sources/duan/fixture.md:L2",
    }


def observation(case_id: str, a: str, b: str, direction: str, *, kind: str = "制") -> dict:
    return {
        "case_id": case_id, "a": a, "b": b, "kind": kind, "direction": direction,
        "edge_id": f"e-{case_id}", "source_ref": "engine-fixture:L1",
    }


def answers_doc(cases: list[dict]) -> dict:
    return {"schema_version": "p1-fresh-40-answers/v1", "case_count": len(cases), "cases": cases}


def routing_doc(cases: list[dict]) -> dict:
    return {"schema_version": "p1-fresh-40-routing/v1", "case_count": len(cases), "cases": cases}


def output_doc(cases: list[dict]) -> dict:
    return {"schema_version": "p1-system-output/v1", "case_count": len(cases), "cases": cases}


def full_answers() -> dict:
    """40 条 main（非真实数据，端点/机制循环生成，只为凑满预注册分母）。"""
    cases = [
        answer_case(f"PF-{i + 1:03d}", *PAIRS[i % len(PAIRS)], mechanism=MECHANISMS[i % len(MECHANISMS)])
        for i in range(40)
    ]
    return answers_doc(cases)


def full_routing() -> dict:
    cases = [
        routing_case(f"PR-{i + 1:02d}", *PAIRS[i], mechanism=ROUTING_MECHANISMS[i])
        for i in range(5)
    ]
    return routing_doc(cases)


def full_output(*, correct_main: int = 40, routing_abstain: bool = True) -> dict:
    """前 `correct_main` 条 main 同向、其余写反；routing 默认全部按预注册 abstain。"""
    cases = []
    for i in range(40):
        a, b = PAIRS[i % len(PAIRS)]
        if i < correct_main:
            cases.append(observation(f"PF-{i + 1:03d}", a, b, mod.DIRECTED))
        else:
            cases.append(observation(f"PF-{i + 1:03d}", b, a, mod.DIRECTED))
    for i in range(5):
        a, b = PAIRS[i]
        direction = mod.NEEDS_JUDGMENT if routing_abstain else mod.DIRECTED
        cases.append(observation(f"PR-{i + 1:02d}", a, b, direction))
    return output_doc(cases)


def write_inputs(tmp_path: Path, *, answers: dict | None = None, routing: dict | None = None,
                 output: dict | None = None) -> tuple[Path, Path, Path]:
    paths = []
    for name, payload in (("answers", answers), ("routing", routing), ("output", output)):
        path = tmp_path / f"{name}.json"
        if payload is not None:
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        paths.append(path)
    return paths[0], paths[1], paths[2]


def run_fixture(tmp_path: Path, *, answers: dict | None = None, routing: dict | None = None,
                output: dict | None = None, **kwargs) -> dict:
    answers_path, routing_path, output_path = write_inputs(
        tmp_path,
        answers=answers if answers is not None else full_answers(),
        routing=routing if routing is not None else full_routing(),
        output=output if output is not None else full_output(),
    )
    return mod.run(answers_path, routing_path, output_path, **kwargs)


def assert_accounting(result: dict) -> None:
    metrics = result["metrics"]
    assert metrics["total"] == sum(metrics[bucket] for bucket in mod.BUCKETS)
    assert result["denominators"]["total"] == metrics["total"]
    assert result["denominators"]["main"] + result["denominators"]["routing"] == metrics["total"]


def case_row(result: dict, case_id: str) -> dict:
    return next(row for row in result["cases"] if row["case_id"] == case_id)


# ── 六桶与一等指标 ──────────────────────────────────────────────────────────

def test_all_correct_full_run_metrics(tmp_path: Path) -> None:
    result = run_fixture(tmp_path, dev20_veto="passed")
    metrics = result["metrics"]

    assert metrics["total"] == 45
    assert (metrics["correct"], metrics["wrong"]) == (40, 0)
    assert (metrics["abstain_expected"], metrics["abstain_unexpected"]) == (5, 0)
    assert (metrics["missing"], metrics["routing_claims"]) == (0, 0)
    assert metrics["precision"]["value"] == 1.0
    assert metrics["precision"]["denominator"] == 40
    # coverage 分母按卡面字面取 total=45：routing 的 5 条正确 abstain 不进分子。
    assert metrics["coverage"]["value"] == pytest.approx(40 / 45)
    assert metrics["coverage"]["denominator"] == 45
    assert metrics["needs_judgment_rate"]["value"] == pytest.approx(5 / 45)
    assert metrics["confident_error"]["value"] == 0.0
    assert result["verdict"]["verdict"] == "pass"
    assert any("coverage" in note for note in result["verdict"]["notes"])
    assert_accounting(result)


def test_all_wrong_is_kill(tmp_path: Path) -> None:
    result = run_fixture(tmp_path, output=full_output(correct_main=0))
    metrics = result["metrics"]

    assert (metrics["correct"], metrics["wrong"]) == (0, 40)
    assert metrics["precision"]["value"] == 0.0
    assert metrics["confident_error"]["value"] == 1.0
    assert metrics["coverage"]["value"] == pytest.approx(40 / 45)
    assert result["verdict"]["verdict"] == "kill"
    assert all(row["reason"] == "reversed" for row in result["cases"] if row["set"] == mod.MAIN_SET)
    assert_accounting(result)


def test_abstain_on_main_is_unexpected_not_ok_or_wrong(tmp_path: Path) -> None:
    answers = answers_doc([
        answer_case("A-1", "巳", "亥"),
        answer_case("A-2", "丑", "未"),
    ])
    routing = routing_doc([routing_case("R-1", "辰", "戌")])
    output = output_doc([
        observation("A-1", "巳", "亥", mod.NEEDS_JUDGMENT),
        observation("A-2", "丑", "未", mod.DIRECTED),
        observation("R-1", "辰", "戌", mod.NEEDS_JUDGMENT),
    ])
    result = run_fixture(tmp_path, answers=answers, routing=routing, output=output)
    metrics = result["metrics"]

    assert case_row(result, "A-1")["status"] == "abstain_unexpected"
    assert case_row(result, "R-1")["status"] == "abstain_expected"
    assert (metrics["correct"], metrics["wrong"]) == (1, 0)
    assert metrics["abstain_unexpected"] == 1
    assert metrics["precision"]["denominator"] == 1  # abstain 不进 direction 分母
    assert metrics["precision"]["value"] == 1.0
    assert metrics["needs_judgment_rate"]["value"] == pytest.approx(2 / 3)
    assert_accounting(result)


def test_missing_is_counted_separately(tmp_path: Path) -> None:
    answers = answers_doc([
        answer_case("A-1", "巳", "亥"),
        answer_case("A-2", "丑", "未"),
    ])
    routing = routing_doc([routing_case("R-1", "辰", "戌")])
    output = output_doc([observation("A-1", "巳", "亥", mod.DIRECTED)])
    result = run_fixture(tmp_path, answers=answers, routing=routing, output=output)
    metrics = result["metrics"]

    assert metrics["missing"] == 2
    assert [row["case_id"] for row in result["cases"] if row["status"] == "missing"] == ["A-2", "R-1"]
    assert case_row(result, "A-2")["reason"] == "not_in_system_output"
    assert metrics["precision"]["denominator"] == 1
    assert metrics["coverage"]["value"] == pytest.approx(1 / 3)
    assert_accounting(result)


def test_reversed_and_endpoint_mismatch_reasons(tmp_path: Path) -> None:
    answers = answers_doc([
        answer_case("A-REV", "巳", "亥"),
        answer_case("A-PAIR", "丑", "未"),
    ])
    output = output_doc([
        observation("A-REV", "亥", "巳", mod.DIRECTED),   # 写反
        observation("A-PAIR", "子", "午", mod.DIRECTED),  # 另一端对
    ])
    result = run_fixture(tmp_path, answers=answers, routing=routing_doc([]), output=output)

    assert case_row(result, "A-REV")["status"] == "wrong"
    assert case_row(result, "A-REV")["reason"] == "reversed"
    assert case_row(result, "A-PAIR")["status"] == "wrong"
    assert case_row(result, "A-PAIR")["reason"] == "endpoint_mismatch"
    assert result["metrics"]["wrong"] == 2


def test_mutual_expected_and_mutual_cross_claims(tmp_path: Path) -> None:
    answers = answers_doc([
        answer_case("A-MUT", "丑", "戌", mutual=True, mechanism="刑", kind="刑"),
        answer_case("A-DIR", "巳", "亥"),
    ])
    output = output_doc([
        observation("A-MUT", "丑", "戌", mod.MUTUAL, kind="刑"),
        observation("A-DIR", "巳", "亥", mod.MUTUAL),
    ])
    result = run_fixture(tmp_path, answers=answers, routing=routing_doc([]), output=output)

    assert case_row(result, "A-MUT")["status"] == "correct"
    assert case_row(result, "A-MUT")["reason"] == "mutual"
    assert case_row(result, "A-DIR")["status"] == "wrong"
    assert case_row(result, "A-DIR")["reason"] == "directed_expected_mutual_observed"
    assert result["metrics"]["correct"] == 1
    assert result["metrics"]["wrong"] == 1


def test_mutual_expected_but_directed_observed(tmp_path: Path) -> None:
    answers = answers_doc([answer_case("A-MUT", "丑", "戌", mutual=True, mechanism="刑")])
    output = output_doc([observation("A-MUT", "丑", "戌", mod.DIRECTED)])
    result = run_fixture(tmp_path, answers=answers, routing=routing_doc([]), output=output)

    row = case_row(result, "A-MUT")
    assert (row["status"], row["reason"]) == ("wrong", "mutual_expected_directed_observed")
    assert row["expected_direction"] == mod.MUTUAL


def test_kind_mismatch_does_not_change_direction_bucket(tmp_path: Path) -> None:
    answers = answers_doc([answer_case("A-1", "巳", "亥", kind="制")])
    output = output_doc([observation("A-1", "巳", "亥", mod.DIRECTED, kind="合")])
    result = run_fixture(tmp_path, answers=answers, routing=routing_doc([]), output=output)

    assert case_row(result, "A-1")["status"] == "correct"
    assert case_row(result, "A-1")["observed_kind"] == "合"
    assert result["metrics"]["correct"] == 1


def test_neutral_half_precision(tmp_path: Path) -> None:
    """无倾向 fixture：2 对 2 错 → precision 50%、confident_error 50%。"""
    cases = [answer_case(f"N-{i}", *PAIRS[i]) for i in range(4)]
    observations = [
        observation("N-0", *PAIRS[0], mod.DIRECTED),
        observation("N-1", *PAIRS[1], mod.DIRECTED),
        observation("N-2", *reversed(PAIRS[2]), mod.DIRECTED),
        observation("N-3", *reversed(PAIRS[3]), mod.DIRECTED),
    ]
    result = run_fixture(tmp_path, answers=answers_doc(cases), routing=routing_doc([]),
                         output=output_doc(observations))
    metrics = result["metrics"]

    assert metrics["precision"]["value"] == 0.5
    assert metrics["confident_error"]["value"] == 0.5
    assert metrics["precision"]["wilson95"]["lower"] < 0.5
    assert metrics["needs_judgment_rate"]["value"] == 0.0
    assert_accounting(result)


def test_routing_claims_do_not_enter_precision(tmp_path: Path) -> None:
    answers = answers_doc([answer_case(f"M-{i}", *PAIRS[i % len(PAIRS)]) for i in range(15)])
    output_claims = output_doc(
        [observation(f"M-{i}", *PAIRS[i % len(PAIRS)], mod.DIRECTED) for i in range(10)]
        + [observation(f"M-{i}", *reversed(PAIRS[i % len(PAIRS)]), mod.DIRECTED) for i in range(10, 15)]
        + [observation(f"R-{i + 1:02d}", *PAIRS[i], mod.DIRECTED) for i in range(3)]
        + [observation(f"R-{i + 1:02d}", *PAIRS[i], mod.NEEDS_JUDGMENT) for i in range(3, 5)]
    )
    routing = routing_doc([routing_case(f"R-{i + 1:02d}", *PAIRS[i], mechanism="穿") for i in range(5)])
    result = run_fixture(tmp_path, answers=answers, routing=routing, output=output_claims)
    metrics = result["metrics"]

    assert (metrics["correct"], metrics["wrong"]) == (10, 5)
    assert metrics["precision"]["denominator"] == 15
    assert metrics["precision"]["value"] == pytest.approx(10 / 15)
    assert metrics["routing_claims"] == 3
    assert result["routing"]["routing_claims"] == 3
    assert result["routing"]["abstain_expected"] == 2
    assert metrics["coverage"]["denominator"] == 20
    assert_accounting(result)


# ── 判定（预注册阈值只读）────────────────────────────────────────────────────

def test_prereg_thresholds_pinned_to_card() -> None:
    thresholds = mod.PREREG_THRESHOLDS
    assert thresholds["main_cases"] == 40
    assert thresholds["routing_cases"] == 5
    assert thresholds["pass_correct_min"] == 32
    assert thresholds["pass_precision_wilson_lower_strictly_greater"] == 0.50
    assert thresholds["pass_coverage_min"] == 0.75
    assert thresholds["pass_confident_error_max"] == 0.10
    assert thresholds["kill_correct_below"] == 24
    assert thresholds["gray_zone_inclusive"] == [24, 31]
    assert thresholds["needs_judgment_rate_routing_only_above"] == 0.50
    assert thresholds["requires_dev20_veto"] is True


@pytest.mark.parametrize("correct,expected", [(23, "kill"), (24, "gray_zone"), (31, "gray_zone"),
                                              (32, "fail_secondary_gate")])
def test_verdict_boundaries(correct: int, expected: str, tmp_path: Path) -> None:
    result = run_fixture(tmp_path, output=full_output(correct_main=correct), dev20_veto="passed")
    assert result["metrics"]["correct"] == correct
    assert result["verdict"]["verdict"] == expected
    assert result["verdict"]["prereg_denominators_met"] is True


def test_pass_requires_dev20_attestation(tmp_path: Path) -> None:
    ok = run_fixture(tmp_path, dev20_veto="passed")
    unknown = run_fixture(tmp_path, dev20_veto="unknown")

    assert ok["verdict"]["verdict"] == "pass"
    assert ok["verdict"]["gates"]["dev20_veto_passed"] is True
    assert unknown["verdict"]["verdict"] == "fail_secondary_gate"
    assert unknown["verdict"]["gates"]["dev20_veto_passed"] is False
    assert any("dev-20" in reason for reason in unknown["verdict"]["reasons"])


def test_routing_engine_only_claim_above_50_percent(tmp_path: Path) -> None:
    """40 条 main 全部 abstain：needs_judgment_rate=40/45>50% → 只准宣称分流引擎。"""
    output = output_doc(
        [observation(f"PF-{i + 1:03d}", *PAIRS[i % len(PAIRS)], mod.NEEDS_JUDGMENT) for i in range(40)]
        + [observation(f"PR-{i + 1:02d}", *PAIRS[i], mod.NEEDS_JUDGMENT) for i in range(5)]
    )
    result = run_fixture(tmp_path, output=output)
    verdict = result["verdict"]

    assert result["metrics"]["abstain_unexpected"] == 40
    # needs_judgment_rate 数的是「系统实际输出 needs_judgment」的条数：main 40 + routing 5。
    assert result["metrics"]["needs_judgment_rate"]["value"] == 1.0
    assert result["metrics"]["needs_judgment_rate"]["numerator"] == 45
    assert verdict["claim"] == "routing_engine_only"
    assert verdict["verdict"] == "kill"
    assert verdict["gates"]["precision_wilson_lower_gt_50"] is False  # 无方向可判


def test_routing_claims_do_not_change_verdict_per_card(tmp_path: Path) -> None:
    """卡 §3 的 pass 门槛不含 routing：routing 硬给方向只进 routing 小表。

    这是卡片字面口径（§4「routing 例单列，不混入 precision 分母」），不是实现的疏忽；
    要把分流正确率设成门槛，必须先改卡。
    """
    result = run_fixture(tmp_path, output=full_output(routing_abstain=False), dev20_veto="passed")

    assert result["metrics"]["routing_claims"] == 5
    assert result["metrics"]["abstain_expected"] == 0
    assert result["metrics"]["precision"]["value"] == 1.0
    assert result["verdict"]["verdict"] == "pass"
    assert any("routing" in note for note in result["verdict"]["notes"])


def test_synthetic_denominators_not_evaluated(tmp_path: Path) -> None:
    answers = answers_doc([answer_case("A-1", "巳", "亥")])
    routing = routing_doc([routing_case("R-1", "辰", "戌")])
    output = output_doc([
        observation("A-1", "巳", "亥", mod.DIRECTED),
        observation("R-1", "辰", "戌", mod.NEEDS_JUDGMENT),
    ])
    result = run_fixture(tmp_path, answers=answers, routing=routing, output=output, dev20_veto="passed")

    assert result["verdict"]["verdict"] == "not_evaluated"
    assert result["verdict"]["prereg_denominators_met"] is False
    assert result["metrics"]["correct"] == 1  # 计数器照常，但不给 pass/kill


# ── Wilson 与分类型小表 ─────────────────────────────────────────────────────

def test_wilson_interval_reference_values() -> None:
    lower, upper = mod.wilson_interval(8, 10)
    assert lower == pytest.approx(0.4902, abs=1e-3)
    assert upper == pytest.approx(0.9433, abs=1e-3)
    assert mod.wilson_interval(0, 0) is None
    lower_zero, _ = mod.wilson_interval(0, 10)
    assert lower_zero == 0.0
    _, upper_full = mod.wilson_interval(10, 10)
    assert upper_full == pytest.approx(1.0)
    assert mod.Z_95 == pytest.approx(1.959963984540054)


def test_wilson_lower_gate_strictly_greater_than_half(tmp_path: Path) -> None:
    """precision 100% 但分母小（Wilson 下界 <50%）时不得判 pass。"""
    answers = answers_doc([answer_case(f"S-{i}", *PAIRS[i]) for i in range(3)])
    output = output_doc([observation(f"S-{i}", *PAIRS[i], mod.DIRECTED) for i in range(3)])
    result = run_fixture(tmp_path, answers=answers, routing=routing_doc([]), output=output,
                         dev20_veto="passed")

    assert result["metrics"]["precision"]["value"] == 1.0
    assert result["metrics"]["precision"]["wilson95"]["lower"] < 0.50
    assert result["verdict"]["gates"]["precision_wilson_lower_gt_50"] is False
    assert result["verdict"]["verdict"] == "not_evaluated"  # 分母也不对


def test_by_kind_table(tmp_path: Path) -> None:
    answers = answers_doc([
        answer_case("K-1", "子", "午", mechanism="冲"),
        answer_case("K-2", "卯", "酉", mechanism="冲"),
        answer_case("K-3", "巳", "申", mechanism="合"),
        answer_case("K-4", "辰", "戌", mechanism="刑"),
    ])
    output = output_doc([
        observation("K-1", "子", "午", mod.DIRECTED),
        observation("K-2", "酉", "卯", mod.DIRECTED),
        observation("K-3", "巳", "申", mod.NEEDS_JUDGMENT),
        # K-4 缺失
    ])
    result = run_fixture(tmp_path, answers=answers, routing=routing_doc([]), output=output)
    table = {row["mechanism"]: row for row in result["by_kind"]}

    assert list(table) == ["冲", "合", "刑"]  # 卡面顺序：冲/合/穿/刑…只保留出现的类
    assert (table["冲"]["total"], table["冲"]["correct"], table["冲"]["wrong"]) == (2, 1, 1)
    assert table["冲"]["precision"]["value"] == 0.5
    assert (table["合"]["correct"], table["合"]["wrong"], table["合"]["abstain_unexpected"]) == (0, 0, 1)
    assert table["合"]["precision"]["value"] is None
    assert (table["刑"]["total"], table["刑"]["missing"]) == (1, 1)


def test_routing_table_is_separate(tmp_path: Path) -> None:
    result = run_fixture(tmp_path)
    routing = result["routing"]

    assert routing["total"] == 5
    assert routing["abstain_expected"] == 5
    assert routing["routing_claims"] == 0
    assert routing["abstain_expected_rate"]["value"] == 1.0
    assert {row["mechanism"] for row in routing["by_mechanism"]} == {"穿", "合", "刑", "冲"}
    assert result["metrics"]["abstain_expected"] == 5


# ── 输入契约 ────────────────────────────────────────────────────────────────

def test_rejects_unknown_direction(tmp_path: Path) -> None:
    answers_path, routing_path, output_path = write_inputs(
        tmp_path, answers=full_answers(), routing=full_routing(),
        output=output_doc([observation("PF-001", "巳", "亥", "ok")]),
    )
    with pytest.raises(ValueError, match="未登记"):
        mod.run(answers_path, routing_path, output_path)


def test_rejects_extra_case_id(tmp_path: Path) -> None:
    answers_path, routing_path, output_path = write_inputs(
        tmp_path, answers=answers_doc([answer_case("A-1", "巳", "亥")]),
        routing=routing_doc([]),
        output=output_doc([
            observation("A-1", "巳", "亥", mod.DIRECTED),
            observation("A-OTHER", "子", "午", mod.DIRECTED),
        ]),
    )
    with pytest.raises(ValueError, match="answers/routing 无"):
        mod.run(answers_path, routing_path, output_path)


def test_rejects_duplicate_case_id_in_output(tmp_path: Path) -> None:
    answers_path, routing_path, output_path = write_inputs(
        tmp_path, answers=answers_doc([answer_case("A-1", "巳", "亥")]),
        routing=routing_doc([]),
        output=output_doc([
            observation("A-1", "巳", "亥", mod.DIRECTED),
            observation("A-1", "亥", "巳", mod.DIRECTED),
        ]),
    )
    with pytest.raises(ValueError, match="重复"):
        mod.run(answers_path, routing_path, output_path)


def test_rejects_routing_expected_direction_not_needs_judgment(tmp_path: Path) -> None:
    answers_path, routing_path, output_path = write_inputs(
        tmp_path, answers=answers_doc([answer_case("A-1", "巳", "亥")]),
        routing=routing_doc([routing_case("R-1", "辰", "戌", expected=mod.DIRECTED)]),
        output=output_doc([observation("A-1", "巳", "亥", mod.DIRECTED)]),
    )
    with pytest.raises(ValueError, match="expected_direction"):
        mod.run(answers_path, routing_path, output_path)


def test_rejects_case_id_overlap_between_answers_and_routing(tmp_path: Path) -> None:
    answers_path, routing_path, output_path = write_inputs(
        tmp_path, answers=answers_doc([answer_case("X-1", "巳", "亥")]),
        routing=routing_doc([routing_case("X-1", "辰", "戌")]),
        output=output_doc([observation("X-1", "巳", "亥", mod.DIRECTED)]),
    )
    with pytest.raises(ValueError, match="重叠"):
        mod.run(answers_path, routing_path, output_path)


def test_rejects_answer_without_actor_or_mutual(tmp_path: Path) -> None:
    answers_path, routing_path, output_path = write_inputs(
        tmp_path, answers=answers_doc([{"case_id": "A-1", "relation": {"a": "巳", "b": "亥"}}]),
        routing=routing_doc([]),
        output=output_doc([observation("A-1", "巳", "亥", mod.DIRECTED)]),
    )
    with pytest.raises(ValueError, match="无法定期望方向"):
        mod.run(answers_path, routing_path, output_path)


def test_rejects_missing_routing_file(tmp_path: Path) -> None:
    answers_path, routing_path, output_path = write_inputs(
        tmp_path, answers=answers_doc([answer_case("A-1", "巳", "亥")]),
        output=output_doc([observation("A-1", "巳", "亥", mod.DIRECTED)]),
    )
    assert not routing_path.exists()
    with pytest.raises(ValueError, match="routing 文件不存在"):
        mod.run(answers_path, routing_path, output_path)


# ── CLI ─────────────────────────────────────────────────────────────────────

def test_cli_json_summary_and_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    answers_path, routing_path, output_path = write_inputs(
        tmp_path, answers=full_answers(), routing=full_routing(), output=full_output(),
    )
    argv = ["--answers", str(answers_path), "--routing", str(routing_path),
            "--system-output", str(output_path)]

    assert mod.main(argv) == 0
    summary = capsys.readouterr().out
    assert "correct=40" in summary
    assert "verdict: fail_secondary_gate" in summary  # 默认 dev20 unknown，不判 pass

    assert mod.main(argv + ["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["metrics"]["correct"] == 40
    assert payload["verdict"]["verdict"] == "fail_secondary_gate"


def test_cli_returns_2_on_bad_input(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    answers_path, routing_path, output_path = write_inputs(
        tmp_path, answers=full_answers(), routing=full_routing(),
        output=output_doc([observation("PF-001", "巳", "亥", "reversed")]),
    )
    code = mod.main(["--answers", str(answers_path), "--routing", str(routing_path),
                     "--system-output", str(output_path)])
    assert code == 2
    assert "输入不合口径" in capsys.readouterr().err

    missing = mod.main(["--answers", str(answers_path), "--routing", str(tmp_path / "nope.json"),
                        "--system-output", str(output_path)])
    assert missing == 2


def test_run_is_deterministic(tmp_path: Path) -> None:
    first = run_fixture(tmp_path)
    second = run_fixture(tmp_path)
    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second, ensure_ascii=False, sort_keys=True
    )
