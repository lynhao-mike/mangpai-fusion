from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "report-v1.3.md"
EVENT_ARCHIVE = ROOT / "tools" / "event_archive.py"


REQUIRED_025_HEADINGS = [
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

REQUIRED_PARALLEL_TRACE_TOKENS = [
    "### 多专家功能域裁判（v1.5 旁路）",
    "reading_ids",
    "adjudication_id",
    "expert_systems",
    "domain",
    "consensus_layer",
    "supporting_experts",
    "dissenting_experts",
    "abstained_experts",
    "feedback_state",
    "冲突解释",
]


def _template_text() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def test_report_v13_keeps_025_standard_headings_and_internal_marker() -> None:
    """防止 V2 单报告模板再次漂移掉 025/H2 稳定章节契约。"""

    text = _template_text()

    for heading in REQUIRED_025_HEADINGS:
        assert heading in text, heading
    assert "命理师内部版" in text
    assert "product_version | v1.3.0" in text
    assert "pipeline_version | v1.4.0" in text


def test_report_v13_keeps_input_context_compatibility_rows() -> None:
    """render_from_output 必须能被静态模板保障输出四柱和大运上下文。"""

    text = _template_text()

    assert "| 四柱 | {{ bazi_str }} |" in text
    assert "| 大运 | {{ dayun_str }} |" in text
    assert "<!-- # 八字分析报告 · {{ case_id }} · {{ qian_kun }} -->" in text


def test_report_v13_keeps_key_yingqi_year_first_column() -> None:
    """关键应期表首列必须保留年份，供 smoke 与后续解析器稳定抽取。"""

    text = _template_text()

    assert "## 六、关键应期" in text
    assert "| 年份 | 事项 | 时间窗口 | 触发条件 | 置信度 |" in text
    assert "| {{ g.year }} | {{ g.domain }} |" in text


def test_report_v13_keeps_production_rule_participation_block() -> None:
    """子平 / 滴天髓生产规则参与块是生产规则证据链的报告出口。"""

    text = _template_text()

    assert "### 子平 / 滴天髓生产规则参与" in text
    assert "子平规则参与" in text
    assert "滴天髓规则参与" in text
    assert "{{ c.evidence_str }}" in text


def test_report_v13_keeps_parallel_domain_e14_trace_fields() -> None:
    """模板必须保留 output_linter E14 所需的并行域裁判追踪字段。"""

    text = _template_text()

    for token in REQUIRED_PARALLEL_TRACE_TOKENS:
        assert token in text, token
    assert "{% if parallel_domain_conclusions %}" in text
    assert "{% for c in parallel_domain_conclusions %}" in text


def test_event_archive_header_keeps_content_and_legacy_report_links() -> None:
    """事件归档头部必须同时保留正式内容报告和历史 analyst-report 兼容引用。"""

    source = EVENT_ARCHIVE.read_text(encoding="utf-8")

    assert "{case_id}-content-report.md" in source
    assert "{case_id}-analyst-report.md" in source
    assert "历史报告兼容引用" in source
