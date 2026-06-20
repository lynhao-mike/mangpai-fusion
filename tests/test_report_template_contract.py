from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "report-v5.md"
EVENT_ARCHIVE = ROOT / "tools" / "event_archive.py"


REQUIRED_V5_HEADINGS = [
    "# 报告模板 v5 · 五派命理推理操作系统统一版",
    "## 二、统一报告骨架",
    "## 基本盘面",
    "## v5 五派裁决总论",
    "## 三段式仲裁摘要",
    "## 受限概率提示",
    "## 性格与行为模式",
    "## 主要事项 outcome taxonomy 判断表",
    "## 学业与学习能力",
    "## 事业与职业路径",
    "## 财富与资产",
    "## 婚姻与家庭",
    "## 健康与风险",
    "## 关键年份提示",
    "## 风险提示与校准清单",
    "## 总评",
    "## 归档信息",
]

REQUIRED_V5_TAXONOMY_TOKENS = [
    "engine/contracts/11-outcome-taxonomy-v1.md",
    "mapping/outcome-taxonomy-v1.yaml",
    "education_domain_level",
    "career_domain_level",
    "wealth_domain_level",
    "marriage_domain_level",
    "health_domain_level",
]


def _template_text() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def test_report_v5_keeps_unified_template_headings_and_internal_marker() -> None:
    """防止 V5 五派统一版模板漂移掉标准章节契约。"""

    text = _template_text()

    for heading in REQUIRED_V5_HEADINGS:
        assert heading in text, heading
    assert "命理师内部版 · 五派命理推理操作系统 v5 分析" in text
    assert "《命理师内容报告（统一版）》" in text


def test_report_v5_keeps_input_context_compatibility_rows() -> None:
    """render_from_output 必须能被静态模板保障输出四柱和大运上下文。"""

    text = _template_text()

    assert "| 案例编号 | {{ case_id }} |" in text
    assert "| 命式 | {{ qian_kun }}造 |" in text
    assert "| 大运 | {{ luck_sequence }} |" in text
    assert "# 命理师内容报告（统一版）· {{ case_id }} · {{ qian_kun }}" in text


def test_report_v5_keeps_key_year_table() -> None:
    """关键年份表必须保留年份首列，供 smoke 与后续解析器稳定抽取。"""

    text = _template_text()

    assert "## 关键年份提示" in text
    assert "| 年份 | 主题 | 判断 |" in text
    assert "| {{ key_year_1 }} | {{ key_year_1_theme }} | {{ key_year_1_judgment }} |" in text


def test_report_v5_keeps_outcome_taxonomy_contract_tokens() -> None:
    """V5 模板必须保留主要事项 outcome taxonomy 展示出口。"""

    text = _template_text()

    for token in REQUIRED_V5_TAXONOMY_TOKENS:
        assert token in text, token


def test_report_v5_keeps_detail_expansion_dual_score_block() -> None:
    """模板必须显式展示首轮细断的证据分、置信分与不确定性口径。"""

    text = _template_text()

    for token in (
        "### DetailExpansion 展开策略",
        "EvidenceScore",
        "ConfidenceScore",
        "{{ r.evidence_score_value }}",
        "{{ r.confidence_score_value }}",
        "{{ r.inference_type }}",
        "{{ r.theory_sources }}",
        "{{ r.uncertainty }}",
        "理论推断",
    ):
        assert token in text, token


def test_event_archive_header_keeps_content_and_legacy_report_links() -> None:
    """事件归档头部必须同时保留正式内容报告和历史 analyst-report 兼容引用。"""

    source = EVENT_ARCHIVE.read_text(encoding="utf-8")

    assert "{case_id}-content-report.md" in source
    assert "{case_id}-analyst-report.md" in source
    assert "历史报告兼容引用" in source
