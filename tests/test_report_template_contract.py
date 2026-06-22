from __future__ import annotations

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_V5 = ROOT / "templates" / "report-v5.md"
TEMPLATE_V6 = ROOT / "templates" / "report-v6.md"

_EXISTING_TEMPLATES = [t for t in (TEMPLATE_V5, TEMPLATE_V6) if t.exists()]
EVENT_ARCHIVE = ROOT / "tools" / "event_archive.py"


REQUIRED_UNIFIED_HEADINGS = [
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
    "### 待反馈（已发生验证项）",
    "### 待反馈（预测验证项）",
    "## 系统级约束",
]

REQUIRED_OUTCOME_CN_FIELDS = [
    "学历层次",
    "学校层级",
    "学业表现",
    "学科倾向",
    "职业层级",
    "单位层级",
    "权力层级",
    "成就等级",
    "收入层级",
    "资产层级",
    "财富状态",
    "感情状态",
    "婚姻质量",
    "配偶学历",
    "配偶事业",
    "配偶财富",
    "配偶外貌",
    "配偶气质",
    "体质",
    "疾病风险",
    "健康状态",
    "寿元倾向",
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


def _template_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("template", _EXISTING_TEMPLATES, ids=lambda p: p.name)
def test_report_templates_keep_unified_headings(template: Path) -> None:
    """防止统一报告模板漂移掉 v7.7 标准章节契约。"""

    text = _template_text(template)
    for heading in REQUIRED_UNIFIED_HEADINGS:
        assert heading in text, f"{template.name}: {heading}"
    assert "时间标准：公历（YYYY–YYYY年）+ 年龄（XX–XX岁）" in text


def test_report_v5_keeps_input_context_compatibility_rows() -> None:
    """静态模板必须保障输出四柱、大运与归档上下文。"""

    if not TEMPLATE_V5.exists():
        pytest.skip("report-v5.md 已删除，跳过兼容性测试")
    text = _template_text(TEMPLATE_V5)

    assert "- 案例编号：{{ 案例编号 }}" in text
    assert "- 命式：{{ 命式 }}造" in text
    assert "- 当前大运：{{ 当前大运 }}" in text
    assert "## 相关引用文档" in text
    assert "[打开报告文件]({{ 报告路径 }})" in text
    assert "[打开案例目录]({{ 案例目录 }})" in text
    assert "[打开反馈文件]({{ 反馈入口 }})" in text
    assert "| 柱位 | 天干 | 地支 | 十神主轴 | 藏干 | 长生 | 神煞 |" in text
    assert "| 年柱 | {{ 年干 }} | {{ 年支 }} | {{ 年柱十神主轴 }} | {{ 年柱藏干 }} | {{ 年柱长生 }} | {{ 年柱神煞 }} |" in text


def test_report_v5_keeps_key_year_table() -> None:
    """关键反馈表必须保留时间窗口，供后续解析器稳定抽取。"""

    if not TEMPLATE_V5.exists():
        pytest.skip("report-v5.md 已删除，跳过兼容性测试")
    text = _template_text(TEMPLATE_V5)

    assert "## 待反馈关键流年与事件" in text
    assert "### 待反馈（已发生验证项）" in text
    assert "### 待反馈（预测验证项）" in text
    assert "| 优先级 | 领域 | 时间窗口 | 具体应事 | 回访要点 |" in text
    assert "{{ 已发生反馈一优先级 }}" in text
    assert "{{ 预测反馈一优先级 }}" in text


@pytest.mark.parametrize("template", _EXISTING_TEMPLATES, ids=lambda p: p.name)
def test_report_templates_keep_outcome_taxonomy_cn_fields(template: Path) -> None:
    """模板必须按中文二级指标展示可训练事项分类。"""

    text = _template_text(template)
    for token in REQUIRED_OUTCOME_CN_FIELDS:
        assert token in text, f"{template.name}: {token}"
    assert "全部展示字段必须中文化" in text
    assert "反馈必须能回写系统" in text
    assert "| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |" in text
    assert "| 指标 | 稳定枚举 | 判断结果 |" not in text
    assert "置信状态（星级）" in text
    assert "中（★★★☆☆）" in text


@pytest.mark.parametrize("template", _EXISTING_TEMPLATES, ids=lambda p: p.name)
def test_report_templates_keep_v77_time_standard(template: Path) -> None:
    """模板必须固定 v7.7 数字时间标准，禁止回退到中文数字年份。"""

    forbidden_time_terms = [
        "二零二五年",
        "二零三五年",
        "二至十一岁",
        "十二至二十一岁",
        "二十二至三十一岁",
    ]
    text = _template_text(template)
    assert "YYYY" in text
    assert "XX" in text
    assert "{{ 运.年份范围 }}" in text
    assert "所有时间窗口必须使用" in text
    for token in forbidden_time_terms:
        assert token not in text, f"{template.name}: {token}"


@pytest.mark.parametrize("template", _EXISTING_TEMPLATES, ids=lambda p: p.name)
def test_report_templates_do_not_show_machine_field_names(template: Path) -> None:
    """报告模板展示文本不得出现裸机器字段名。"""

    import re

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
