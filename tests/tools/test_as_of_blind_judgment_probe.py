"""as_of_blind_judgment_probe 的截断与表格内嵌注释检测测试。

夹具全部为合成文本，不引用任何真实案例内容；候选10污染模式的复现仅取自
reports/as-of-life-state-blind-judgment-batch-report.md §2.2 已如实记录的
结构描述（表格行 + 年龄区间 + 中文括号注释），不重新读取候选10原始 input.md。
"""
from __future__ import annotations

from tools.as_of_blind_judgment_probe import (
    detect_table_embedded_annotation,
    truncate_blind_section,
)


def test_truncate_blind_section_heading_boundary_unchanged() -> None:
    """既有 heading 边界行为不因新函数引入而改变。"""

    text = "# 排盘\n四柱信息\n\n## 三、命主已知信息\n反馈内容\n"
    truncated, cut_line, boundary_type = truncate_blind_section(text)
    assert truncated == "# 排盘\n四柱信息\n\n"
    assert cut_line == 4
    assert boundary_type == "heading"


def test_truncate_blind_section_yaml_key_boundary_unchanged() -> None:
    """既有 yaml_key 边界行为不因新函数引入而改变。"""

    text = "schema_version: 1.2.0\n四柱: 甲子\nknown_facts:\n  反馈: 内容\n"
    truncated, cut_line, boundary_type = truncate_blind_section(text)
    assert truncated == "schema_version: 1.2.0\n四柱: 甲子\n"
    assert cut_line == 3
    assert boundary_type == "yaml_key"


def test_truncate_blind_section_no_boundary_returns_none_unchanged() -> None:
    """无边界标记时既有行为（返回全文、None、None）不变。"""

    text = "# 排盘\n四柱信息\n无任何边界标记\n"
    truncated, cut_line, boundary_type = truncate_blind_section(text)
    assert truncated == text
    assert cut_line is None
    assert boundary_type is None


def test_detect_table_embedded_annotation_matches_candidate10_pattern() -> None:
    """合成夹具复现候选10已记录的污染结构：表格行+年龄区间+中文括号注释。"""

    text = (
        "## 三、大运排布\n"
        "\n"
        "| 起讫 | 大运 | 十神 |\n"
        "|---|---|---|\n"
        "| 22-32 | 癸未 | 比/劫 |\n"
        "| 32-42 | 癸亥 | 比/劫（深圳外贸） |\n"
        "| **42-52（当前）** | **壬午** | **劫/官（管资金）** |\n"
        "| 52-62 | 辛酉 | 印/枭 |\n"
    )
    hits = detect_table_embedded_annotation(text)
    assert hits == (6, 7)


def test_detect_table_embedded_annotation_no_hit_on_clean_table() -> None:
    """不含括号注释的正常排盘表格不应命中。"""

    text = (
        "| 起讫 | 大运 | 十神 |\n"
        "|---|---|---|\n"
        "| 22-32 | 癸未 | 比/劫 |\n"
        "| 32-42 | 癸亥 | 比/劫 |\n"
    )
    hits = detect_table_embedded_annotation(text)
    assert hits == ()


def test_detect_table_embedded_annotation_no_hit_without_age_range() -> None:
    """含括号但无年龄区间/当前标记的表格行不应命中。"""

    text = "| 干支 | 藏干 | 神煞 |\n|---|---|---|\n| 甲子 | 癸 | 华盖（贵人） |\n"
    hits = detect_table_embedded_annotation(text)
    assert hits == ()


def test_detect_table_embedded_annotation_no_hit_with_english_bracket_content() -> None:
    """括号内容为非中文字符（如英文/数字）时不应命中，属已知局限。"""

    text = "| 22-32 | 癸未 | 比/劫 (Shenzhen) |\n"
    hits = detect_table_embedded_annotation(text)
    assert hits == ()


def test_detect_table_embedded_annotation_empty_text_returns_empty_tuple() -> None:
    hits = detect_table_embedded_annotation("")
    assert hits == ()
