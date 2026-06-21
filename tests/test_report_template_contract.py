from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_V5 = ROOT / "templates" / "report-v5.md"
TEMPLATE_V6 = ROOT / "templates" / "report-v6.md"
EVENT_ARCHIVE = ROOT / "tools" / "event_archive.py"


REQUIRED_UNIFIED_HEADINGS = [
    "# 命理师内容报告（统一版）",
    "## 基本盘面",
    "## 五派总论",
    "## 性格与行为模式",
    "## 主要事项结果分类判断表",
    "### 学业",
    "### 事业",
    "### 财富",
    "### 婚姻",
    "### 健康",
    "## 多派共识与互补结论",
    "# 📌 待反馈关键流年与事件（重点校准区）",
    "## 报告边界与风险提示",
    "## 归档与反馈入口",
]

REQUIRED_OUTCOME_CN_FIELDS = [
    "学历层次",
    "学校层次",
    "成绩水平",
    "专业/方向类型",
    "职业层级",
    "单位层级",
    "权力层级",
    "成就层级",
    "年收入",
    "资产等级",
    "财富稳定性",
    "感情状态",
    "婚姻质量",
    "配偶教育",
    "配偶事业",
    "配偶财富",
    "配偶外貌",
    "配偶气质",
    "家庭结构",
    "体质",
    "疾病风险",
    "心理健康",
    "寿元风险/长寿倾向",
]

FORBIDDEN_REPORT_MACHINE_FIELDS = [
    "degree_level",
    "institution_level",
    "academic_performance",
    "occupation_level",
    "organization_level",
    "authority_level",
    "achievement_level",
    "income_level",
    "asset_level",
    "wealth_stability",
    "relationship_status",
    "marriage_quality",
    "spouse_quality",
    "physical_condition",
    "major_disease_risk",
    "mental_health",
    "longevity_risk",
]


def _template_text(path: Path = TEMPLATE_V5) -> str:
    return path.read_text(encoding="utf-8")


def test_report_templates_keep_unified_headings() -> None:
    """防止统一报告模板漂移掉标准章节契约。"""

    for template in (TEMPLATE_V5, TEMPLATE_V6):
        text = _template_text(template)
        for heading in REQUIRED_UNIFIED_HEADINGS:
            if heading == "## 五派总论":
                assert "## 命局核心结论" in text or "## v6.2 五派裁决总论" in text
                continue
            assert heading in text, f"{template.name}: {heading}"
        assert "命理师内容报告（统一版）" in text


def test_report_v5_keeps_input_context_compatibility_rows() -> None:
    """render_from_output 必须能被静态模板保障输出四柱和大运上下文。"""

    text = _template_text(TEMPLATE_V5)

    assert "| 案例编号 | {{ case_id }} |" in text
    assert "| 命式 | {{ qian_kun }}造 |" in text
    assert "| 大运 | {{ dayun_str }} |" in text
    assert "# 命理师内容报告（统一版）· {{ case_id }} · {{ qian_kun }}" in text


def test_report_v5_keeps_key_year_table() -> None:
    """关键年份表必须保留年份首列，供 smoke 与后续解析器稳定抽取。"""

    text = _template_text(TEMPLATE_V5)

    assert "# 📌 待反馈关键流年与事件（重点校准区）" in text
    assert "| 优先级 | 反馈主题 | 时间窗口 | 需要确认的事实 | 校准用途 |" in text
    assert "{{ probability_event_1_domain }}" in text


def test_report_templates_keep_outcome_taxonomy_cn_fields() -> None:
    """模板必须按中文二级指标展示 outcome taxonomy。"""

    for template in (TEMPLATE_V5, TEMPLATE_V6):
        text = _template_text(template)
        for token in REQUIRED_OUTCOME_CN_FIELDS:
            assert token in text, f"{template.name}: {token}"
        assert "报告只展示中文字段" in text
        assert "机器标签仅保留在契约、映射与内部结构中" in text


def test_report_templates_do_not_show_machine_field_names() -> None:
    """报告模板展示文本不得出现裸机器字段名。"""

    import re

    for template in (TEMPLATE_V5, TEMPLATE_V6):
        text = _template_text(template)
        visible_text = re.sub(r"{{[^}]+}}", "", text)
        for token in FORBIDDEN_REPORT_MACHINE_FIELDS:
            assert token not in visible_text, f"{template.name}: {token}"


def test_event_archive_header_keeps_content_and_legacy_report_links() -> None:
    """事件归档头部必须同时保留正式内容报告和历史 analyst-report 兼容引用。"""

    source = EVENT_ARCHIVE.read_text(encoding="utf-8")

    assert "{case_id}-content-report.md" in source
    assert "{case_id}-analyst-report.md" in source
    assert "历史报告兼容引用" in source
