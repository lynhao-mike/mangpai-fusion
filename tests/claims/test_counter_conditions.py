"""T-156 · 反条件语义审计：A 类删除后的边界行为、B 类保留、正条件逐字快照。

分类与原文引证见 ``META/counter-condition-audit-v1.md``：

* **A 类（7 条）**：反条件与正条件同 fact、同阈值，在阈值点上正反同时成立，与结论/依据自相矛盾
  → ``counter_conditions`` 置空（不是放宽判据，是删掉与结论打架的那一条）。
* **B 类（3 条）**：反条件用的是正条件里没有的 fact，且结论/依据有独立语义
  （「冲动信号同向」「信号接近时不输出」「无有效做功路径」）→ 反条件原文保留。
* **C 类（0 条）**：本次没有「不同 fact 又找不到语义依据」的规则需要留待人类裁决。

``matched`` 在本卡一个字没改：下面的断言都显式钉住它。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from engine.claims.rule_loader import (
    RuleCondition,
    evaluate_rule,
    load_claim_rule_registry,
)

RULE_PATH = Path(__file__).resolve().parents[2] / "theory" / "production" / "claim-rules-v1.yaml"

A_CLASS = frozenset(
    {
        "DUAN-EVENT-CAREER-PATH-MIXED-V1",
        "DUAN-EVENT-WEALTH-DEBT-V1",
        "DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1",
        "GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1",
        "GAO-HEALTH-SYSTEM-RISK-MODERATE-V1",
        "GAO-HEALTH-SYSTEM-RISK-HIGH-V1",
        "YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1",
    }
)

B_CLASS = frozenset(
    {
        "DUAN-EVENT-CAREER-ROLE-CHANGE-V1",
        "DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1",
        "DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1",
    }
)

# 本卡没有 C 类；写成显式常量，防止以后有人把 C 类当 A 类删掉。
C_CLASS: frozenset[str] = frozenset()

# T-156 之前的逐字快照（由当时的 YAML 备份机械生成，SHA256 6396883D…BEBEF）。
# 只用来证明「正条件 / 排除条件 / 结论 / 依据」一个字没变；counter_conditions 是修前原文，
# 供 A 类重建旧行为、B 类核对保留。
OLD_SNAPSHOT: dict[str, dict[str, object]] = {
    "DUAN-EVENT-CAREER-ROLE-CHANGE-V1": {
        "required_facts": (
            "evidence_completeness", "has_official", "has_output", "output_count",
            "official_count", "movement_structure", "active_path_count", "branch_conflict_intensity",
        ),
        "conditions": (
            ("has_official", "truthy", True),
            ("has_output", "truthy", True),
            ("output_count", "gte", 2),
            ("official_count", "gte", 1),
            ("movement_structure", "truthy", True),
            ("active_path_count", "gte", 1),
        ),
        "exclusions": (("evidence_completeness", "ne", "full"),),
        "counter_conditions": (("branch_conflict_intensity", "lte", 0.34),),
        "conclusion_template": (
            "段派原局的财官事业结构与做功、冲动信号同向，支持一生中出现显著岗位、职责或职业角色变化。"
        ),
        "confidence_basis": "官杀与食伤事业结构、段派体用做功路径及官杀混杂或地支冲动共同成立。",
    },
    "DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1": {
        "required_facts": (
            "evidence_completeness", "predicted_label", "employment_score",
            "entrepreneurship_score", "employment_advantage", "active_path_count",
        ),
        "conditions": (
            ("predicted_label", "eq", "employment"),
            ("employment_score", "gte", 4),
            ("employment_advantage", "gte", 3),
        ),
        "exclusions": (("evidence_completeness", "ne", "full"),),
        "counter_conditions": (("active_path_count", "lte", 0),),
        "conclusion_template": "段派原局结构支持主要职业路径归为受雇任职。",
        "confidence_basis": "官印任职信号明显高于食伤财经营信号；信号接近时不输出。",
    },
    "DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1": {
        "required_facts": (
            "evidence_completeness", "predicted_label", "employment_score",
            "entrepreneurship_score", "entrepreneurship_advantage", "active_path_count",
        ),
        "conditions": (
            ("predicted_label", "eq", "entrepreneurship"),
            ("entrepreneurship_score", "gte", 4),
            ("entrepreneurship_advantage", "gte", 3),
            ("active_path_count", "gte", 1),
        ),
        "exclusions": (("evidence_completeness", "ne", "full"),),
        "counter_conditions": (("employment_score", "gte", 2),),
        "conclusion_template": "段派原局结构支持主要职业路径归为创业经营。",
        "confidence_basis": (
            "食伤财经营信号明显高于官印任职信号，并存在有效做功路径；信号接近时不输出。"
        ),
    },
    "DUAN-EVENT-CAREER-PATH-MIXED-V1": {
        "required_facts": (
            "evidence_completeness", "predicted_label", "employment_score",
            "entrepreneurship_score", "branch_conflict_intensity", "active_path_count",
        ),
        "conditions": (
            ("predicted_label", "eq", "mixed"),
            ("employment_score", "gte", 4),
            ("entrepreneurship_score", "gte", 4),
            ("branch_conflict_intensity", "gte", 0.35),
            ("active_path_count", "gte", 1),
        ),
        "exclusions": (("evidence_completeness", "ne", "full"),),
        "counter_conditions": (("branch_conflict_intensity", "lte", 0.4),),
        "conclusion_template": "段派原局结构支持主要职业路径归为任职与经营混合。",
        "confidence_basis": (
            "官印任职与食伤财经营信号均达到门槛，并有冲动及有效做功路径；单侧信号不足时不输出。"
        ),
    },
    "DUAN-EVENT-WEALTH-DEBT-V1": {
        "required_facts": (
            "evidence_completeness", "has_wealth", "wealth_count", "peer_pressure",
            "support_drain_imbalance", "branch_conflict_intensity", "active_path_count",
        ),
        "conditions": (
            ("has_wealth", "truthy", True),
            ("wealth_count", "gte", 2),
            ("peer_pressure", "gte", 3),
            ("support_drain_imbalance", "gte", 3),
            ("branch_conflict_intensity", "gte", 0.55),
            ("active_path_count", "gte", 1),
        ),
        "exclusions": (("evidence_completeness", "ne", "full"),),
        "counter_conditions": (("support_drain_imbalance", "lte", 3),),
        "conclusion_template": (
            "段派原局显示财富承压、比劫竞争与做功失衡同向，存在形成显著债务或长期负债的风险。"
        ),
        "confidence_basis": (
            "财星存在且同时受到比劫竞争、克泄耗失衡、强冲动及做功路径约束；高风险任务采用保守置信上限。"
        ),
    },
    "DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1": {
        "required_facts": ("evidence_completeness", "independent_signal_count", "active_path_count"),
        "conditions": (
            ("independent_signal_count", "gte", 2),
            ("active_path_count", "gte", 1),
        ),
        "exclusions": (("evidence_completeness", "ne", "full"),),
        "counter_conditions": (("independent_signal_count", "lte", 2),),
        "conclusion_template": (
            "段派原局至少两组独立婚姻事件信号同向，支持一生中存在离婚或再婚事件风险，但不作必然判断。"
        ),
        "confidence_basis": (
            "日支受冲刑害、官杀混杂、冲与刑害并见中至少两项独立成立，并有段派做功路径；"
            "高风险任务采用保守置信上限。"
        ),
    },
    "GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1": {
        "required_facts": ("evidence_completeness", "wealth_exposed", "pressure_signal_count"),
        "conditions": (
            ("wealth_exposed", "truthy", True),
            ("pressure_signal_count", "gte", 2),
        ),
        "exclusions": (("evidence_completeness", "ne", "full"),),
        "counter_conditions": (("pressure_signal_count", "lte", 2),),
        "conclusion_template": "高派结构性旁证显示债务风险与财富承压信号复合出现，但不作必然判断。",
        "confidence_basis": (
            "财星达到最低门槛，并至少有两项比劫竞争、克泄耗失衡、支冲突或五行偏枯代理同向；"
            "未使用神煞或应期输入。"
        ),
    },
    "GAO-HEALTH-SYSTEM-RISK-MODERATE-V1": {
        "required_facts": ("evidence_completeness", "predicted_label", "risk_signal_count"),
        "conditions": (
            ("predicted_label", "eq", "moderate"),
            ("risk_signal_count", "gte", 2),
            ("risk_signal_count", "lte", 2),
        ),
        "exclusions": (("evidence_completeness", "ne", "full"),),
        "counter_conditions": (("risk_signal_count", "gte", 2),),
        "conclusion_template": (
            "高派结构风险分层为 moderate：多项原局结构代理同向，仅表示系统性健康风险旁证，不替代专业评估。"
        ),
        "confidence_basis": (
            "只按生扶与克泄耗失衡、气候极端、五行集中偏枯及支冲突的复合程度分层；不使用疾病或神煞诊断。"
        ),
    },
    "GAO-HEALTH-SYSTEM-RISK-HIGH-V1": {
        "required_facts": ("evidence_completeness", "predicted_label", "risk_signal_count"),
        "conditions": (
            ("predicted_label", "eq", "high"),
            ("risk_signal_count", "gte", 3),
        ),
        "exclusions": (("evidence_completeness", "ne", "full"),),
        "counter_conditions": (("risk_signal_count", "lte", 3),),
        "conclusion_template": (
            "高派结构风险分层为 high：多项原局结构代理同向，仅表示较高的系统性健康风险旁证，"
            "不替代专业评估。"
        ),
        "confidence_basis": (
            "只按生扶与克泄耗失衡、气候极端、五行集中偏枯及支冲突的复合程度分层；不使用疾病或神煞诊断。"
        ),
    },
    "YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1": {
        "required_facts": (
            "evidence_completeness", "sex", "spouse_star_basis", "independent_signal_count",
        ),
        "conditions": (
            ("sex", "truthy", True),
            ("spouse_star_basis", "in", ("wealth", "official")),
            ("independent_signal_count", "gte", 2),
        ),
        "exclusions": (("evidence_completeness", "ne", "full"), ("sex", "falsy", True)),
        "counter_conditions": (("independent_signal_count", "lte", 2),),
        "conclusion_template": (
            "杨派原局至少两类独立婚姻事件信号同向，存在离婚或再婚事件风险，但不作必然判断。"
        ),
        "confidence_basis": (
            "按性别选取配偶星，并要求夫妻宫、配偶星、比劫、食伤冲突或女命官杀混杂中"
            "至少两类独立信号同向；高风险任务保守封顶。"
        ),
    },
}

# 边界上下文：正条件全部成立，且（修前的）反条件也恰好成立。
# A 类取在旧反条件的阈值点上；B 类取在仍保留的反条件阈值上。
BOUNDARY_CONTEXTS: dict[str, dict[str, object]] = {
    # --- A 类：修后在阈值点上必须 success ---
    "DUAN-EVENT-CAREER-PATH-MIXED-V1": {
        "evidence_completeness": "full",
        "predicted_label": "mixed",
        "employment_score": 4,
        "entrepreneurship_score": 4,
        "branch_conflict_intensity": 0.4,  # 正条件 >= 0.35 与旧反条件 <= 0.4 的重叠点
        "active_path_count": 1,
    },
    "DUAN-EVENT-WEALTH-DEBT-V1": {
        "evidence_completeness": "full",
        "has_wealth": True,
        "wealth_count": 2,
        "peer_pressure": 3,
        "support_drain_imbalance": 3,  # 正条件 >= 3 与旧反条件 <= 3 的同一点
        "branch_conflict_intensity": 0.55,
        "active_path_count": 1,
    },
    "DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1": {
        "evidence_completeness": "full",
        "independent_signal_count": 2,  # 「至少两组」的阈值点，旧反条件 <= 2 也成立
        "active_path_count": 1,
    },
    "GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1": {
        "evidence_completeness": "full",
        "wealth_exposed": True,
        "pressure_signal_count": 2,  # 「至少有两项」的阈值点，旧反条件 <= 2 也成立
    },
    "GAO-HEALTH-SYSTEM-RISK-MODERATE-V1": {
        "evidence_completeness": "full",
        "predicted_label": "moderate",
        "risk_signal_count": 2,  # 正条件已是 >= 2 且 <= 2，旧反条件 >= 2 被逻辑蕴含
    },
    "GAO-HEALTH-SYSTEM-RISK-HIGH-V1": {
        "evidence_completeness": "full",
        "predicted_label": "high",
        "risk_signal_count": 3,  # 正条件 >= 3 与旧反条件 <= 3 的同一点
    },
    "YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1": {
        "evidence_completeness": "full",
        "sex": "male",  # 「性别已知」；本卡未碰杨派 sex 条件
        "spouse_star_basis": "wealth",
        "independent_signal_count": 2,  # 「至少两类」的阈值点，旧反条件 <= 2 也成立
    },
    # --- B 类：反条件仍保留，命中也必须 fail ---
    "DUAN-EVENT-CAREER-ROLE-CHANGE-V1": {
        "evidence_completeness": "full",
        "has_official": True,
        "has_output": True,
        "output_count": 2,
        "official_count": 1,
        "movement_structure": True,
        "active_path_count": 1,
        "branch_conflict_intensity": 0.34,  # 保留的反条件 <= 0.34 命中
    },
    "DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1": {
        "evidence_completeness": "full",
        "predicted_label": "employment",
        "employment_score": 4,
        "entrepreneurship_score": 1,
        "employment_advantage": 3,
        "active_path_count": 0,  # 保留的反条件 <= 0 命中（无有效做功路径）
    },
    "DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1": {
        "evidence_completeness": "full",
        "predicted_label": "entrepreneurship",
        "employment_score": 2,  # 保留的反条件 >= 2 命中（任职信号接近）
        "entrepreneurship_score": 5,
        "entrepreneurship_advantage": 3,
        "active_path_count": 1,
    },
}


def _registry():
    return load_claim_rule_registry(RULE_PATH)


def _triples(conditions) -> tuple[tuple[str, str, object], ...]:
    return tuple((condition.fact, condition.op, condition.value) for condition in conditions)


def _as_rule_conditions(raw: object) -> tuple[RuleCondition, ...]:
    return tuple(RuleCondition(fact, op, value) for fact, op, value in raw)  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 静态：分类完整 + A 类清空 + B 类原文保留
# ---------------------------------------------------------------------------

def test_every_rule_is_classified_exactly_once() -> None:
    registry = _registry()
    ids = set(registry.rule_ids)
    assert len(registry) == 10
    assert ids == set(A_CLASS) | set(B_CLASS)
    assert set(A_CLASS).isdisjoint(B_CLASS)
    assert set(OLD_SNAPSHOT) == ids
    assert set(BOUNDARY_CONTEXTS) == ids
    # 本卡 C 类 0 条：审计表 §3 记录「不同 fact 但找不到语义依据」的规则不存在。
    assert C_CLASS == frozenset()


@pytest.mark.parametrize("rule_id", sorted(A_CLASS))
def test_a_class_counter_conditions_are_empty(rule_id: str) -> None:
    rule = _registry().get(rule_id)
    assert rule.counter_conditions == ()
    # 修前原文非空，证明本卡确实删掉了东西（而不是本来就没有）。
    assert OLD_SNAPSHOT[rule_id]["counter_conditions"]


@pytest.mark.parametrize("rule_id", sorted(B_CLASS))
def test_b_class_counter_conditions_are_kept_verbatim(rule_id: str) -> None:
    rule = _registry().get(rule_id)
    assert _triples(rule.counter_conditions) == OLD_SNAPSHOT[rule_id]["counter_conditions"]
    assert rule.counter_conditions


# ---------------------------------------------------------------------------
# A 类：边界上下文修后 success，且旧行为确实只是被反条件压掉
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rule_id", sorted(A_CLASS))
def test_a_class_boundary_is_triggered_success_and_matched(rule_id: str) -> None:
    rule = _registry().get(rule_id)
    context = BOUNDARY_CONTEXTS[rule_id]
    result = evaluate_rule(rule, context)

    assert result.failed_conditions == ()
    assert result.matched_exclusions == ()
    assert result.matched_counter_conditions == ()
    assert result.triggered is True
    assert result.outcome == "success"
    assert result.matched is True


@pytest.mark.parametrize("rule_id", sorted(A_CLASS))
def test_a_class_legacy_counter_was_the_only_failure_cause(rule_id: str) -> None:
    """用修前反条件重建旧行为：同一上下文曾 outcome="fail"，但 matched 一直是 True。"""
    rule = _registry().get(rule_id)
    legacy_counter = _as_rule_conditions(OLD_SNAPSHOT[rule_id]["counter_conditions"])
    legacy_rule = replace(rule, counter_conditions=legacy_counter)
    context = BOUNDARY_CONTEXTS[rule_id]

    before = evaluate_rule(legacy_rule, context)
    after = evaluate_rule(rule, context)

    assert before.matched_counter_conditions == legacy_counter
    assert before.failed_conditions == ()
    assert before.triggered is True
    assert before.outcome == "fail"
    assert before.matched is True  # T-156 硬约束：matched 一个字不改

    assert after.matched_counter_conditions == ()
    assert after.triggered is True
    assert after.outcome == "success"
    assert after.matched is True


# ---------------------------------------------------------------------------
# B 类：反条件成立 → 仍 fail
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rule_id", sorted(B_CLASS))
def test_b_class_counter_hit_still_fails(rule_id: str) -> None:
    rule = _registry().get(rule_id)
    context = BOUNDARY_CONTEXTS[rule_id]
    result = evaluate_rule(rule, context)

    assert result.failed_conditions == ()
    assert result.matched_exclusions == ()
    assert result.matched_counter_conditions == rule.counter_conditions
    assert result.triggered is True
    assert result.outcome == "fail"
    assert result.matched is True


# ---------------------------------------------------------------------------
# 快照：正条件 / 排除条件 / 结论 / 依据 逐字未变
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rule_id", sorted(OLD_SNAPSHOT))
def test_positive_conditions_and_texts_match_t156_snapshot(rule_id: str) -> None:
    rule = _registry().get(rule_id)
    snapshot = OLD_SNAPSHOT[rule_id]

    assert rule.required_facts == snapshot["required_facts"]
    assert _triples(rule.conditions) == snapshot["conditions"]
    assert _triples(rule.exclusions) == snapshot["exclusions"]
    assert rule.conclusion_template == snapshot["conclusion_template"]
    assert rule.confidence_basis == snapshot["confidence_basis"]
