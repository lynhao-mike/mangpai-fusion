"""tools/as_of_verdict_stats.py 的单元测试。

用真实历史案例（RF000026/057/108/121/125/149/164/179）的三态归类作为测试数据，
确保统计工具能复现 as-of 根因诊断报告中的分布，且不会退化产出单一合并分数。
"""
from __future__ import annotations

import pytest

from tools.as_of_verdict_stats import CaseVerdictRecord, summarize_verdicts


REAL_HISTORICAL_RECORDS = (
    CaseVerdictRecord("RF000026", "ALTERNATIVE_HIT", "OPTIMISTIC"),
    CaseVerdictRecord("RF000057", "MISS"),
    CaseVerdictRecord("RF000108", "ALTERNATIVE_HIT", "OPTIMISTIC"),
    CaseVerdictRecord("RF000121", "CENTER_HIT"),
    CaseVerdictRecord("RF000125", "CENTER_HIT"),
    CaseVerdictRecord("RF000149", "MISS"),
    CaseVerdictRecord("RF000164", "MISS"),
    CaseVerdictRecord("RF000179", "ALTERNATIVE_HIT", "OPTIMISTIC"),
)


def test_case_verdict_record_rejects_unknown_verdict() -> None:
    with pytest.raises(ValueError, match="unknown verdict"):
        CaseVerdictRecord("X", "SUPER_HIT")


def test_case_verdict_record_rejects_bias_direction_on_non_alternative_hit() -> None:
    with pytest.raises(ValueError, match="only applies to ALTERNATIVE_HIT"):
        CaseVerdictRecord("X", "CENTER_HIT", "OPTIMISTIC")


def test_summarize_verdicts_requires_at_least_one_record() -> None:
    with pytest.raises(ValueError, match="at least one"):
        summarize_verdicts(())


def test_summarize_verdicts_rejects_duplicate_case_id() -> None:
    records = (
        CaseVerdictRecord("A", "CENTER_HIT"),
        CaseVerdictRecord("A", "MISS"),
    )
    with pytest.raises(ValueError, match="duplicate case_id"):
        summarize_verdicts(records)


def test_summarize_real_historical_records_reproduces_three_way_split() -> None:
    """复现根因诊断报告的核心结论：2 CENTER_HIT + 3 ALTERNATIVE_HIT(全OPTIMISTIC) + 3 MISS。"""

    summary = summarize_verdicts(REAL_HISTORICAL_RECORDS)

    assert summary.total == 8
    assert summary.verdict_counts == {
        "ALTERNATIVE_HIT": 3,
        "MISS": 3,
        "CENTER_HIT": 2,
    }
    # 关键发现：全部 3 个 ALTERNATIVE_HIT 偏差方向都是 OPTIMISTIC，无一反向。
    assert summary.alternative_hit_bias_counts == {"OPTIMISTIC": 3}
    assert summary.alternative_hit_bias_counts.get("PESSIMISTIC", 0) == 0


def test_as_report_lines_exposes_three_states_not_a_single_merged_score() -> None:
    summary = summarize_verdicts(REAL_HISTORICAL_RECORDS)
    lines = summary.as_report_lines()

    joined = "\n".join(lines)
    assert "CENTER_HIT：2" in joined
    assert "ALTERNATIVE_HIT：3" in joined
    assert "MISS：3" in joined
    assert "OPTIMISTIC：3" in joined
    # 禁止出现类似 "6/8" 或 "命中率" 这类合并单一分数的字样。
    assert "命中率" not in joined
    assert "/8" not in joined


def test_three_way_summary_has_no_single_hit_rate_attribute() -> None:
    """架构约束回归：ThreeWaySummary 不应提供任何单一合并命中率属性/方法。

    该测试故意断言"不存在"，防止未来有人为了方便又悄悄加回单一分数字段，
    重新掩盖 CENTER_HIT/ALTERNATIVE_HIT/MISS 的性质差异。
    """

    summary = summarize_verdicts(REAL_HISTORICAL_RECORDS)
    forbidden_names = ("hit_rate", "score", "accuracy", "merged_rate")
    for name in forbidden_names:
        assert not hasattr(summary, name), f"ThreeWaySummary must not expose {name!r}"
