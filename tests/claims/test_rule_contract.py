"""T-152 · 规则契约 triggered / outcome 判定表与兼容性测试。

只验证新字段语义；``matched`` 仍是旧语义（下一卡另决）。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from engine.claims.rule_loader import (
    ExecutableClaimRule,
    RuleCondition,
    RuleEvaluationError,
    RuleEvaluationResult,
    evaluate_rule,
    load_claim_rule_registry,
)

RULE_PATH = Path("theory/production/claim-rules-v1.yaml")


def _base_rule() -> ExecutableClaimRule:
    return load_claim_rule_registry(RULE_PATH).rules[0]


def _probe_rule(
    *,
    conditions: tuple[RuleCondition, ...],
    exclusions: tuple[RuleCondition, ...] = (),
    counter_conditions: tuple[RuleCondition, ...] = (),
) -> ExecutableClaimRule:
    return replace(
        _base_rule(),
        required_facts=("a", "b", "c"),
        conditions=conditions,
        exclusions=exclusions,
        counter_conditions=counter_conditions,
    )


# ---------------------------------------------------------------------------
# 判定表四行
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("context", "triggered", "outcome", "matched"),
    [
        # conditions 有未满足
        ({"a": 2, "b": True, "c": True}, False, "unknown", False),
        # exclusions 命中
        ({"a": 3, "b": True, "c": True}, False, "unknown", False),
        # conditions 全中、exclusions 未中、counter 命中
        ({"a": 3, "b": False, "c": True}, True, "fail", True),
        # conditions 全中、exclusions 未中、counter 未中
        ({"a": 3, "b": False, "c": False}, True, "success", True),
    ],
)
def test_triggered_outcome_table(
    context: dict[str, object], triggered: bool, outcome: str, matched: bool
) -> None:
    rule = _probe_rule(
        conditions=(RuleCondition("a", "gte", 3),),
        exclusions=(RuleCondition("b", "truthy", True),),
        counter_conditions=(RuleCondition("c", "truthy", True),),
    )
    result = evaluate_rule(rule, context)
    assert result.triggered is triggered
    assert result.outcome == outcome
    assert result.matched is matched


# ---------------------------------------------------------------------------
# 真实生产规则的正反同时命中边界
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("rule_id", "context", "legacy_counter"),
    [
        (
            "DUAN-EVENT-CAREER-PATH-MIXED-V1",
            {
                "evidence_completeness": "full",
                "predicted_label": "mixed",
                "employment_score": 4,
                "entrepreneurship_score": 4,
                "branch_conflict_intensity": 0.35,
                "active_path_count": 1,
            },
            RuleCondition("branch_conflict_intensity", "lte", 0.4),
        ),
        (
            "DUAN-EVENT-WEALTH-DEBT-V1",
            {
                "evidence_completeness": "full",
                "has_wealth": True,
                "wealth_count": 2,
                "peer_pressure": 3,
                "support_drain_imbalance": 3,
                "branch_conflict_intensity": 0.55,
                "active_path_count": 1,
            },
            RuleCondition("support_drain_imbalance", "lte", 3),
        ),
    ],
)
def test_positive_and_counter_overlap_is_triggered_fail_but_still_matched(
    rule_id: str, context: dict[str, object], legacy_counter: RuleCondition
) -> None:
    # T-156：这两条的旧反条件属 A 类（与结论同阈值），已从生产 YAML 删除；
    # 判定表语义改由这里显式钉住的旧反条件验证，测试与生产 YAML 解耦（不是放宽判据）。
    production_rule = load_claim_rule_registry(RULE_PATH).get(rule_id)
    assert production_rule.counter_conditions == ()
    rule = replace(production_rule, counter_conditions=(legacy_counter,))
    result = evaluate_rule(rule, context)

    assert result.failed_conditions == ()
    assert result.matched_exclusions == ()
    assert result.matched_counter_conditions
    assert result.triggered is True
    assert result.outcome == "fail"
    # 本卡硬约束：matched 一个字都不改，仍是旧语义的 True。
    assert result.matched is True


def test_exclusion_hit_keeps_rule_untriggered_and_unknown() -> None:
    rule = load_claim_rule_registry(RULE_PATH).get("DUAN-EVENT-CAREER-PATH-MIXED-V1")
    context = {
        "evidence_completeness": "partial",
        "predicted_label": "mixed",
        "employment_score": 4,
        "entrepreneurship_score": 4,
        "branch_conflict_intensity": 0.35,
        "active_path_count": 1,
    }
    result = evaluate_rule(rule, context)

    assert result.matched_exclusions == rule.exclusions
    assert result.triggered is False
    assert result.outcome == "unknown"
    assert result.matched is False


# ---------------------------------------------------------------------------
# 默认值兼容：旧构造方式不破
# ---------------------------------------------------------------------------

def test_legacy_positional_construction_keeps_defaults() -> None:
    legacy = RuleEvaluationResult(True, (), (), (), ())
    assert (legacy.matched, legacy.triggered, legacy.outcome) == (True, False, "unknown")

    legacy_kw = RuleEvaluationResult(
        matched=False,
        matched_conditions=(),
        failed_conditions=(RuleCondition("a", "gte", 3),),
        matched_exclusions=(),
        matched_counter_conditions=(),
    )
    assert legacy_kw.triggered is False
    assert legacy_kw.outcome == "unknown"
    assert replace(legacy_kw, matched=True).outcome == "unknown"


def test_outcome_is_whitelisted_and_fail_requires_triggered() -> None:
    with pytest.raises(ValueError, match="unknown rule outcome"):
        RuleEvaluationResult(True, (), (), (), (), triggered=True, outcome="partial")
    with pytest.raises(ValueError, match="requires triggered=True"):
        RuleEvaluationResult(True, (), (), (), (), triggered=False, outcome="fail")
    with pytest.raises(ValueError, match="requires triggered=True"):
        RuleEvaluationResult(True, (), (), (), (), triggered=False, outcome="success")


# ---------------------------------------------------------------------------
# 缺失 required_facts 仍抛错，不许当 unknown
# ---------------------------------------------------------------------------

def test_missing_required_fact_raises_and_is_not_silently_unknown() -> None:
    rule = _probe_rule(conditions=(RuleCondition("a", "gte", 3),))
    with pytest.raises(RuleEvaluationError, match="missing context fact"):
        evaluate_rule(rule, {"a": 3})
    with pytest.raises(RuleEvaluationError, match="missing context fact"):
        evaluate_rule(rule, {})
