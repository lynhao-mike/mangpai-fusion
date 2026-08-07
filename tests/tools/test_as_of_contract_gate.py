"""tools/as_of_contract_gate.py 的偏离A/B/D回归测试。

宽泛职业文本逐字摘自 RF000894 历史冻结记录；其余对照样本专门锚定窗口边界与
现实兑现保护语义，区分“应该触发人工提醒”和“不应该触发提醒”的情况。
"""
from __future__ import annotations

import pytest

from tools.as_of_contract_gate import (
    MAX_WINDOW_MONTHS,
    check_center_statement_breadth,
    check_completion_realization_guard,
    check_event_window,
    check_theory_evidence,
    run_contract_gate,
)

# 摘自 RF000894 冻结文本中的职业中心 statement；审计认定其覆盖面过宽。
RF000894_CENTER_STATEMENT = (
    "数据/信息处理、分析判断、技术方法、研究策划、流程质量或复杂问题解决之一"
)


def test_rf000894_center_statement_is_flagged_as_too_broad() -> None:
    finding = check_center_statement_breadth(RF000894_CENTER_STATEMENT)
    assert finding.or_count >= 3
    assert finding.likely_too_broad is True


def test_narrow_center_statement_with_one_or_is_not_flagged() -> None:
    finding = check_center_statement_breadth("数据分析或流程质量管理")
    assert finding.or_count == 1
    assert finding.likely_too_broad is False


@pytest.mark.parametrize(
    ("window_start", "window_end", "expected_exceeds"),
    (
        ("2018-01-01", "2020-12-31", True),
        ("2024-01-01", "2024-12-31", False),
        ("2024-01-01", "2025-02-28", False),
    ),
)
def test_event_window_boundaries(
    window_start: str,
    window_end: str,
    expected_exceeds: bool,
) -> None:
    finding = check_event_window("EVENT-1", window_start, window_end, "岗位职责显著变化")
    assert finding.exceeds_limit is expected_exceeds
    assert finding.exceeds_limit is (finding.window_months > MAX_WINDOW_MONTHS)


def test_event_description_counts_multiple_or_connectors() -> None:
    finding = check_event_window(
        "EVENT-2",
        "2024-01-01",
        "2024-12-31",
        "换单位或换岗位或职责重组",
    )
    assert finding.or_count_in_event >= 2


def test_activate_existing_without_alternative_is_missing_guard() -> None:
    finding = check_completion_realization_guard("ACTIVATE_EXISTING", ())
    assert finding.has_activate_existing_center is True
    assert finding.missing_realization_guard is True


def test_activate_existing_with_unstable_income_alternative_has_guard() -> None:
    finding = check_completion_realization_guard(
        "ACTIVATE_EXISTING",
        ("能力存在，但当前收入不稳，仍处于项目化兑现阶段",),
    )
    assert finding.has_incomplete_realization_alt is True
    assert finding.missing_realization_guard is False


def test_non_activate_existing_mode_does_not_require_guard() -> None:
    finding = check_completion_realization_guard("COMPLETE_LATENT", ())
    assert finding.has_activate_existing_center is False
    assert finding.missing_realization_guard is False


def test_contract_gate_reports_no_issue_when_all_checks_pass() -> None:
    result = run_contract_gate(
        center_statement="数据分析或流程质量管理",
        center_completion_mode="ACTIVATE_EXISTING",
        alternative_statements=("能力已有，但现实兑现不稳",),
        event_candidates=(("EVENT-OK", "2024-01-01", "2024-12-31", "岗位调整"),),
        theory_evidence=("[ziping:ZP-001] 食神生财，喜身旺有根 (来源: theory/ziping/index.yaml)",),
    )
    assert result.any_issue_found is False
    assert result.passes_gate is True
    assert result.blocking_reasons == ()


def test_none_root_level_justification_does_not_change_existing_behavior() -> None:
    result = run_contract_gate(
        center_statement="数据分析或流程质量管理",
        center_completion_mode="ACTIVATE_EXISTING",
        alternative_statements=("能力已有，但现实兑现不稳",),
        event_candidates=(("EVENT-OK", "2024-01-01", "2024-12-31", "岗位调整"),),
        theory_evidence=("[ziping:ZP-001] 食神生财，喜身旺有根 (来源: theory/ziping/index.yaml)",),
        root_level="STRONG_ROOT",
        root_level_justification=None,
    )
    assert result.root_level_finding is None
    assert result.any_issue_found is False
    assert result.passes_gate is True


def test_strong_root_shortcut_is_advisory_and_does_not_block_gate() -> None:
    result = run_contract_gate(
        center_statement="数据分析或流程质量管理",
        center_completion_mode="ACTIVATE_EXISTING",
        alternative_statements=("能力已有，但现实兑现不稳",),
        event_candidates=(("EVENT-OK", "2024-01-01", "2024-12-31", "岗位调整"),),
        theory_evidence=("[ziping:ZP-001] 食神生财，喜身旺有根 (来源: theory/ziping/index.yaml)",),
        root_level="STRONG_ROOT",
        root_level_justification="日支临官、时支帝旺，根气结构性极强。",
    )
    assert result.root_level_finding is not None
    assert result.root_level_finding.likely_shortcut is True
    assert result.any_issue_found is True
    assert result.passes_gate is True
    assert result.blocking_reasons == ()
    assert "root_level" in result.summary


def test_strong_root_with_domain_location_does_not_add_advisory_issue() -> None:
    result = run_contract_gate(
        center_statement="数据分析或流程质量管理",
        center_completion_mode="ACTIVATE_EXISTING",
        alternative_statements=("能力已有，但现实兑现不稳",),
        event_candidates=(("EVENT-OK", "2024-01-01", "2024-12-31", "岗位调整"),),
        theory_evidence=("[ziping:ZP-001] 食神生财，喜身旺有根 (来源: theory/ziping/index.yaml)",),
        root_level="STRONG_ROOT",
        root_level_justification="日支临官，食神透出并对应候选职业领域，且有财星承载路径。",
    )
    assert result.root_level_finding is not None
    assert result.root_level_finding.likely_shortcut is False
    assert result.any_issue_found is False
    assert result.passes_gate is True


def test_contract_gate_reports_issue_when_any_advisory_check_fails() -> None:
    result = run_contract_gate(
        center_statement=RF000894_CENTER_STATEMENT,
        center_completion_mode="COMPLETE_LATENT",
        alternative_statements=(),
        event_candidates=(("EVENT-OK", "2024-01-01", "2024-12-31", "岗位调整"),),
        theory_evidence=("[yang:Y-001] 正官用印化 (来源: theory/yang/index.yaml)",),
    )
    assert result.any_issue_found is True
    assert result.passes_gate is True


def test_missing_theory_evidence_blocks_contract_gate_with_specific_reason() -> None:
    result = run_contract_gate(
        center_statement="数据分析",
        center_completion_mode="COMPLETE_LATENT",
        alternative_statements=(),
        event_candidates=(("EVENT-OK", "2024-01-01", "2024-12-31", "岗位调整"),),
    )
    assert result.passes_gate is False
    assert "缺少 theory_evidence" in result.blocking_reasons[0]


def test_empty_theory_evidence_blocks_contract_gate_with_specific_reason() -> None:
    result = run_contract_gate(
        center_statement="数据分析",
        center_completion_mode="COMPLETE_LATENT",
        alternative_statements=(),
        event_candidates=(("EVENT-OK", "2024-01-01", "2024-12-31", "岗位调整"),),
        theory_evidence=(),
    )
    assert result.passes_gate is False
    assert result.theory_evidence_finding.blocks_freeze is True
    assert result.blocking_reasons
    assert "缺少 theory_evidence" in result.blocking_reasons[0]


def test_structured_theory_citation_passes_theory_evidence_gate() -> None:
    finding = check_theory_evidence(
        ({"school": "yang", "rule_id": "M2-Y-003", "summary": "正官用印化"},)
    )
    assert finding.blocks_freeze is False
    assert finding.evidence_count == 1


def test_no_hit_audit_record_passes_theory_evidence_gate() -> None:
    result = run_contract_gate(
        center_statement="数据分析",
        center_completion_mode="COMPLETE_LATENT",
        alternative_statements=(),
        event_candidates=(("EVENT-OK", "2024-01-01", "2024-12-31", "岗位调整"),),
        theory_evidence=("已检索关键词正官/印化，无命中",),
    )
    assert result.passes_gate is True
    assert result.theory_evidence_finding.blocks_freeze is False


@pytest.mark.parametrize("placeholder", ("TODO", "待补充", "暂无"))
def test_placeholder_only_theory_evidence_blocks_gate(placeholder: str) -> None:
    finding = check_theory_evidence((placeholder,))
    assert finding.placeholder_only is True
    assert finding.blocks_freeze is True
