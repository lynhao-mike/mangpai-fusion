from __future__ import annotations

import json
from pathlib import Path

from tools.v6_preprod_coverage_audit import audit_v6_preprod_reports


def test_audit_v6_preprod_reports_detects_required_coverage(tmp_path: Path) -> None:
    report = tmp_path / "C-TEST-001-乾-甲子乙丑丙寅丁卯-v6-preprod-content-report.md"
    base = """# 📌 归档信息与命盘结构
- 案例编号：C-TEST-001-乾-甲子乙丑丙寅丁卯
- 命式：乾造
- 报告路径：[打开报告文件](reports/C-TEST-001-乾-甲子乙丑丙寅丁卯-v6-preprod-content-report.md)
- 案例目录：[打开案例目录](cases/C-TEST-001-乾-甲子乙丑丙寅丁卯)
- 反馈入口：[打开反馈文件](cases/C-TEST-001-乾-甲子乙丑丙寅丁卯/feedback.md)

## 五派裁决与共识融合总论
## 命局做功与人生主线
## 十五层判断摘要
| 层 | 判断对象 | 本案摘要 | 反馈口径 |
|---|---|---|---|
"""
    layers = "\n".join(f"| {i} | 层{i} | 摘要 | 反馈 |" for i in range(1, 16))
    domains = """
## 性格与行为模式
| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|:---:|---|---|
| 行为模式 | 稳定 | 证据 | ★★★（60%） | 长期 | 反馈 |

## 主要事项结构
### 学业结构
| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |
|---|---|---|:---:|---|---|---|
| 学历层次 | 普通本科 | 证据 | ★★★（60%） | 2020–2024年 | 反馈 | 普通本科 |
| 学校层级 | 普通院校 | 证据 | ★★★（60%） | 2020–2024年 | 反馈 | 普通院校 |
| 学业表现 | 平均 | 证据 | ★★★（60%） | 2020–2024年 | 反馈 | 平均 |
| 学科倾向 | 理科 | 证据 | ★★★（60%） | 2020–2024年 | 反馈 | 理科 |
### 事业结构
| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |
|---|---|---|:---:|---|---|---|
| 职业层级 | 普通员工 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 普通员工 |
| 单位层级 | 小型民企 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 小型民企 |
| 权力层级 | 无权力 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 无权力 |
| 成就等级 | 一般 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 一般 |
### 财富结构
| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |
|---|---|---|:---:|---|---|---|
| 收入层级 | 十万到二十万 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 十万到二十万 |
| 资产层级 | 零到五十万 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 零到五十万 |
| 财富状态 | 稳定 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 稳定 |
### 婚姻结构
| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |
|---|---|---|:---:|---|---|---|
| 感情状态 | 晚婚 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 晚婚 |
| 婚姻质量 | 一般 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 一般 |
| 配偶学历 | 普通本科 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 普通本科 |
| 配偶事业 | 普通员工 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 普通员工 |
| 配偶财富 | 十万以下 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 十万以下 |
| 配偶外貌 | 普通 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 普通 |
| 配偶气质 | 稳重 | 证据 | ★★★（60%） | 2024–2028年 | 反馈 | 稳重 |
### 健康结构
| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |
|---|---|---|:---:|---|---|---|
| 体质 | 一般 | 证据 | ★★★（60%） | 长期 | 反馈 | 一般 |
| 疾病风险 | 消化系统 | 证据 | ★★★（60%） | 长期 | 反馈 | 消化系统 |
| 健康状态 | 低风险 | 证据 | ★★★（60%） | 长期 | 反馈 | 低风险 |
| 寿元倾向 | 长寿倾向 | 证据 | ★★★（60%） | 长期 | 反馈 | 长寿倾向 |

## 受限概率系统
## 主要事件预测账本（prediction-first）
| 事件领域 | 具体应事 | 时间窗口 | 触发条件 | 概率区间 | 置信状态 | 星级 | 证伪口径 | 反馈状态 |
|---|---|---|---|---:|:---:|:---:|---|---|
| 学业 | 升学 | 2024–2028年 | 条件 | 45%–65% | 中 | ★★★☆☆ | 无 | pending |
| 事业 | 岗位变化 | 2024–2028年 | 条件 | 45%–65% | 中 | ★★★☆☆ | 无 | pending |
| 财富 | 收入变化 | 2024–2028年 | 条件 | 45%–65% | 中 | ★★★☆☆ | 无 | pending |
| 婚姻 | 关系变化 | 2024–2028年 | 条件 | 45%–65% | 中 | ★★★☆☆ | 无 | pending |
| 健康 | 健康波动 | 2024–2028年 | 条件 | 45%–65% | 中 | ★★★☆☆ | 无 | pending |
## 待反馈关键流年与事件
### 待反馈（已发生验证项）
### 待反馈（预测验证项）
## 系统级约束
"""
    report.write_text(base + "\n" + layers + "\n" + domains, encoding="utf-8")
    report.with_suffix(".v5.json").write_text(json.dumps({"schema_version": "5.0.0-five-school-mvp"}), encoding="utf-8")
    report.with_suffix(".run.json").write_text(json.dumps({"snapshot_schema_version": "run-snapshot-v1"}), encoding="utf-8")
    report.with_suffix(".decision-run.json").write_text(json.dumps({"schema_version": "decision-run-v1"}), encoding="utf-8")
    report.with_suffix(".feedback-attachment.json").write_text(json.dumps({"attachment_schema_version": "feedback-attachment-v1"}), encoding="utf-8")

    result = audit_v6_preprod_reports([report])

    assert result["case_count"] == 1
    assert result["pass_count"] == 1
    assert result["fail_count"] == 0
    assert result["cases"][0]["missing"] == []


def test_audit_v6_preprod_reports_flags_missing_domain_section(tmp_path: Path) -> None:
    report = tmp_path / "C-TEST-002-坤-甲子乙丑丙寅丁卯-v6-preprod-content-report.md"
    report.write_text("# 📌 归档信息与命盘结构\n## 十五层判断摘要\n## 主要事项结构\n### 学业结构\n", encoding="utf-8")

    result = audit_v6_preprod_reports([report])

    assert result["pass_count"] == 0
    missing = result["cases"][0]["missing"]
    assert "section:事业结构" in missing
    assert "section:健康结构" in missing
    assert "artifact:v5_json" in missing
