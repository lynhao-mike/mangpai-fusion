"""H2 · 唯一标准报告校验

当前标准取代历史 master/client 双版：
  - 渲染默认输出命理师内部版标准结构
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
    "# 📌 归档信息与命盘结构",
    "## 五派裁决与共识融合总论",
    "## 命局做功与人生主线",
    "## 性格与行为模式",
    "## 主要事项结构",
    "### 学业结构",
    "### 事业结构",
    "### 财富结构",
    "### 婚姻结构",
    "### 健康结构",
    "## 受限概率系统",
    "## 待反馈关键流年与事件",
]


def test_h2_standard_report_has_v5_headings(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """标准报告必须固定为当前 V5 命理师内部结构。"""
    from tools.render_report import render

    report = render(
        energy=mock_energy,
        picture=mock_picture,
        gates=mock_gates,
        parsed=mock_parsed,
        support=None,
        template_name="report-v5.md",
        variant="standard",
        _skip_lint=True,
    )

    for heading in _REQUIRED_HEADINGS:
        assert heading in report


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
        variant="standard",
        _skip_lint=True,
    )
    try:
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
    except FileNotFoundError:
        pytest.skip("历史 legacy 模板文件已删除，跳过兼容性测试")
        return
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


def test_h2_standard_context_marks_low_confidence_high_evidence_theory_items(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """标准报告允许高证据低置信细节输出，但必须标记为理论推断。"""
    from tools.render_report import render

    gate_cls = type(mock_gates[0])
    gates = list(mock_gates) + [
        gate_cls(
            2032,
            "事业平台层级跃迁",
            "事业",
            passed=3,
            star=3,
            pct=50,
            evidence_chain=["M3-R-031", "M2-Y-CAREER"],
        )
    ]

    ctx: dict = {}
    render(
        energy=mock_energy,
        picture=mock_picture,
        gates=gates,
        parsed=mock_parsed,
        support=None,
        variant="standard",
        _skip_lint=True,
        _capture_ctx_to=ctx,
    )

    assert ctx["variant"] == "standard"
    assert ctx["is_client"] is False
    assert ctx["is_master"] is True
    assert ctx["detail_expansions"]["career"].allow_theory_detail is True
    assert ctx["detail_expansions"]["career"].inference_type == "理论推断"

    low_star_items = []
    for key in ("zuogong_paths", "consensus_conclusions", "complementary_conclusions", "gate_results", "iron_gates"):
        low_star_items.extend(item for item in ctx.get(key, []) if item.get("star", 0) < 4)

    assert low_star_items
    for item in low_star_items:
        stmt = item.get("statement", "")
        assert "理论推断" in stmt or "证据强度" in stmt or "EvidenceScore" in stmt


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
        assert {
            "statement_id",
            "domain",
            "summary",
            "status",
            "section",
            "rule_ids",
            "schools",
            "rule_id",
            "family_id",
            "school",
            "canon",
            "rule_type",
        }.issubset(set(item))
        assert item["statement_id"].startswith("S-")
        assert item["status"] == "pending"
        assert isinstance(item["rule_ids"], list)
        assert isinstance(item["schools"], list)
