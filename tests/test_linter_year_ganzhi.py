"""测试 output_linter 对公历年—干支不一致的检测。"""
from __future__ import annotations

from tools.output_linter import lint


def test_lint_catches_wrong_year_ganzhi() -> None:
    """报告中出现「2029 己亥」应被 linter 判定 ERROR（2029=己酉，不是己亥）。"""
    bad_md = "| 2029 | 己亥·正财 | 亥=偏印（家到） | 首选婚期 |"
    res = lint(bad_md)
    assert not res.passed
    error_codes = [e.code for e in res.errors]
    assert "E13" in error_codes, f"期望 E13 错误，实际: {error_codes}"


def test_lint_accepts_correct_year_ganzhi() -> None:
    """正确的「2029 己酉」不应产生 E13 错误。"""
    good_md = "| 2029 | 己酉·正财 | 首选婚期 |"
    res = lint(good_md)
    assert "E13" not in [e.code for e in res.errors]


def test_lint_catches_2031_wrong() -> None:
    """2031=辛亥，「2031 甲子」应被拒绝。"""
    bad_md = "婚期：2031 甲子年（首选婚期）"
    res = lint(bad_md)
    assert "E13" in [e.code for e in res.errors]


def test_lint_accepts_2031_correct() -> None:
    """「2031 辛亥」正确，不报 E13。"""
    good_md = "婚期：2031 辛亥年（首选婚期）"
    res = lint(good_md)
    assert "E13" not in [e.code for e in res.errors]
