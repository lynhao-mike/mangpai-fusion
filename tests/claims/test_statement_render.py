"""T-157：断语句子必须由本盘事实装配，不能只返回语料模板。"""

from __future__ import annotations

import re
from types import SimpleNamespace

from engine.claims.domain import render_statement
from engine.claims.rule_loader import RuleEvaluationResult, evaluate_rule, load_claim_rule_registry

GAO_WEALTH_RULE = load_claim_rule_registry().get("GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1")

#: 两张盘各自传入 runner 的聚合事实快照（与 gao_runner 的 context 同构）。
CHART_A_CONTEXT = {
    "evidence_completeness": "full",
    "wealth_exposed": True,
    "pressure_signal_count": 3,
}
CHART_B_CONTEXT = {
    "evidence_completeness": "full",
    "wealth_exposed": True,
    "pressure_signal_count": 5,
}


def _render(rule, context: dict[str, object]) -> str:
    result = evaluate_rule(rule, context)
    assert result.matched is True
    return render_statement(rule, result, context)


def test_two_charts_under_same_rule_render_different_chart_facts() -> None:
    statement_a = _render(GAO_WEALTH_RULE, CHART_A_CONTEXT)
    statement_b = _render(GAO_WEALTH_RULE, CHART_B_CONTEXT)

    assert statement_a != statement_b
    assert "pressure_signal_count=3" in statement_a
    assert "pressure_signal_count=5" in statement_b
    assert "pressure_signal_count=5" not in statement_a
    assert "pressure_signal_count=3" not in statement_b


def test_statement_contains_template_and_at_least_one_fact_value() -> None:
    statement = _render(GAO_WEALTH_RULE, CHART_A_CONTEXT)

    assert statement != GAO_WEALTH_RULE.conclusion_template
    assert statement.startswith(GAO_WEALTH_RULE.conclusion_template)
    assert re.search(r"[a-z_]+=", statement)
    assert "wealth_exposed=True" in statement


def test_render_is_deterministic_and_sorts_facts_by_name() -> None:
    first = _render(GAO_WEALTH_RULE, CHART_A_CONTEXT)
    second = _render(GAO_WEALTH_RULE, CHART_A_CONTEXT)

    assert first == second
    assert first.index("pressure_signal_count=") < first.index("wealth_exposed=")


def test_values_use_repr_style_with_four_decimal_floats() -> None:
    rule = SimpleNamespace(conclusion_template="测试结论。")
    result = RuleEvaluationResult(
        matched=True,
        matched_conditions=(
            SimpleNamespace(fact="label", op="eq", value="full"),
            SimpleNamespace(fact="conflict", op="gte", value=0.35),
            SimpleNamespace(fact="active", op="gte", value=1),
            SimpleNamespace(fact="mixed", op="truthy", value=True),
        ),
        failed_conditions=(),
        matched_exclusions=(),
        matched_counter_conditions=(),
    )
    context = {"label": "full", "conflict": 0.5, "active": 2, "mixed": False}

    statement = render_statement(rule, result, context)

    assert "label='full'" in statement
    assert "conflict=0.5000" in statement
    assert "active=2" in statement
    assert "mixed=False" in statement
    assert statement.index("active=") < statement.index("conflict=") < statement.index("label=")


def test_no_matched_fact_is_marked_not_silent() -> None:
    rule = SimpleNamespace(conclusion_template="测试结论。")
    result = RuleEvaluationResult(
        matched=True,
        matched_conditions=(),
        failed_conditions=(),
        matched_exclusions=(),
        matched_counter_conditions=(),
    )

    statement = render_statement(rule, result, {})

    assert statement.startswith(rule.conclusion_template)
    assert "[no-fact]" in statement
    assert statement != rule.conclusion_template
