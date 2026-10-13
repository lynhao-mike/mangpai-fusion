"""截止态反馈准入预扫描器测试。"""
from __future__ import annotations

from pathlib import Path

from tools.as_of_current_state_scanner import (
    analyze_feedback_current_state,
    scan_feedback_current_state,
)


def test_real_cases_scan_partitions_every_feedback_file() -> None:
    result = scan_feedback_current_state(Path("cases"))

    assert result.total_scanned > 0
    assert (
        len(result.likely_has_current_state)
        + len(result.likely_historical_only)
        + len(result.no_year_table)
        == result.total_scanned
    )
    assert "启发式" in result.note


def test_rf000900_is_likely_to_have_current_state() -> None:
    result = scan_feedback_current_state(Path("cases"))

    signal = next(
        item
        for item in result.likely_has_current_state
        if "RF000900" in item.case_id
    )
    assert signal.max_year_in_table == 2024
    assert signal.has_recent_year is True
    assert signal.has_state_word is True


def test_recent_unemployed_row_has_current_state_signal() -> None:
    signal = analyze_feedback_current_state(
        "| 年份 | 类型 | 事实摘录 |\n|---:|---|---|\n| 2025 | 职业 | 目前无业 |",
        case_id="C-TEST-RECENT",
        feedback_path="cases/C-TEST-RECENT/feedback.md",
    )

    assert signal.has_state_word is True
    assert signal.has_recent_year is True
    assert signal.likely_has_current_state is True


def test_old_exam_row_is_not_recent() -> None:
    signal = analyze_feedback_current_state(
        "| 年份 | 类型 | 事实摘录 |\n|---:|---|---|\n| 2015 | 教育 | 高考 |",
        case_id="C-TEST-OLD",
        feedback_path="cases/C-TEST-OLD/feedback.md",
    )

    assert signal.max_year_in_table == 2015
    assert signal.has_recent_year is False
    assert signal.likely_has_current_state is False
