"""H2 · 唯一标准报告校验

025 标准取代历史 master/client 双版：
  - 渲染只输出命主可读版标准结构
  - 历史 variant 入参不得改变输出结构
  - 标准报告不包含 MASTER/CLIENT 标记与反馈空槽
  - statement_index 使用 statements 列表结构
"""
from __future__ import annotations

import re

import pytest


pytestmark = pytest.mark.v1_3_acceptance


_FEEDBACK_SLOT_RE = re.compile(r"\[S-[\w-]+\]\s*\[\s*\]")
_REQUIRED_HEADINGS = [
    "## 0. 基本盘面",
    "## 一、命局核心结论",
    "## 二、体用、病药与人生主线",
    "## 三、五维定位",
    "## 四、婚恋与家庭",
    "## 五、事业与财富",
    "## 六、关键应期",
    "## 七、健康与生活风险",
    "## 八、行动建议",
    "## 九、总评",
    "## 归档信息",
]


def test_h2_standard_report_has_025_headings(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """标准报告必须固定为 C-2026-025 的命主可读结构。"""
    from tools.render_report import render

    report = render(
        energy=mock_energy,
        picture=mock_picture,
        gates=mock_gates,
        parsed=mock_parsed,
        support=None,
        template_name="report-v1.3.md",
        variant="standard",
        _skip_lint=True,
    )

    for heading in _REQUIRED_HEADINGS:
        assert heading in report
    assert "命主可读版" in report
    assert "product_version | v1.3.0" in report
    assert "pipeline_version | v1.4.0" in report


def test_h2_legacy_variants_are_ignored(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """历史 master/client 入参仅兼容调用，不得再生成不同结构。"""
    from tools.render_report import render

    standard = render(
        energy=mock_energy,
        picture=mock_picture,
        gates=mock_gates,
        parsed=mock_parsed,
        support=None,
        template_name="report-v1.3.md",
        variant="standard",
        _skip_lint=True,
    )
    master_arg = render(
        energy=mock_energy,
        picture=mock_picture,
        gates=mock_gates,
        parsed=mock_parsed,
        support=None,
        template_name="legacy-ignored.md",
        variant="legacy-master",
        _skip_lint=True,
    )
    client_arg = render(
        energy=mock_energy,
        picture=mock_picture,
        gates=mock_gates,
        parsed=mock_parsed,
        support=None,
        template_name="another-legacy-ignored.md",
        variant="legacy-client",
        _skip_lint=True,
    )

    assert master_arg == standard
    assert client_arg == standard


def test_h2_standard_report_has_no_dual_variant_markers(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """唯一标准报告不再包含 MASTER/CLIENT 标记或反馈空槽。"""
    from tools.render_report import render

    report = render(
        energy=mock_energy,
        picture=mock_picture,
        gates=mock_gates,
        parsed=mock_parsed,
        support=None,
        variant="standard",
        _skip_lint=True,
    )

    assert "MASTER 版" not in report
    assert "CLIENT 版" not in report
    assert "master/client" not in report
    assert _FEEDBACK_SLOT_RE.search(report) is None


def test_h2_standard_context_filters_low_star_items(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """标准命主可读版只保留 ★4+ 主线。"""
    from tools.render_report import render

    ctx: dict = {}
    render(
        energy=mock_energy,
        picture=mock_picture,
        gates=mock_gates,
        parsed=mock_parsed,
        support=None,
        variant="standard",
        _skip_lint=True,
        _capture_ctx_to=ctx,
    )

    assert ctx["variant"] == "standard"
    assert ctx["is_client"] is True
    assert ctx["is_master"] is False
    for key in ("zuogong_paths", "consensus_conclusions", "complementary_conclusions", "gate_results", "iron_gates"):
        for item in ctx.get(key, []):
            assert item.get("star", 0) >= 4


def test_h2_statement_index_uses_025_list_schema(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """对象映射结构必须与 025 一致：顶层 statements 为列表。"""
    from tools.render_report import _build_statement_index, render

    ctx: dict = {}
    render(
        energy=mock_energy,
        picture=mock_picture,
        gates=mock_gates,
        parsed=mock_parsed,
        support=None,
        variant="standard",
        _skip_lint=True,
        _capture_ctx_to=ctx,
    )
    index = _build_statement_index(ctx, mock_parsed.case_id)

    assert set(index) == {"case_id", "generated_at", "statements"}
    assert index["case_id"] == mock_parsed.case_id
    assert isinstance(index["statements"], list)
    assert index["statements"]
    for item in index["statements"]:
        assert set(item) == {
            "statement_id",
            "domain",
            "summary",
            "status",
            "section",
            "rule_ids",
            "schools",
        }
        assert item["statement_id"].startswith("S-")
        assert item["status"] == "pending"
        assert isinstance(item["rule_ids"], list)
        assert isinstance(item["schools"], list)
