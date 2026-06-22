from __future__ import annotations

from engine.domain.social_clock import build_education_timeline
from tools.output_linter import lint


def test_build_education_timeline_for_case_034_birth_year() -> None:
    timeline = build_education_timeline(1984)

    assert timeline[0]["stage"] == "小学阶段"
    assert timeline[0]["year_range"] == (1990, 1996)
    assert timeline[1]["stage"] == "初中阶段"
    assert timeline[1]["year_range"] == (1996, 1999)
    assert timeline[2]["stage"] == "高中阶段"
    assert timeline[2]["year_range"] == (1999, 2002)
    assert timeline[3]["stage"] == "大学阶段"
    assert timeline[3]["year_range"] == (2002, 2006)
    assert timeline[4]["stage"] == "毕业或证照兑现"
    assert timeline[4]["year_range"] == (2006, 2008)


def _minimal_v77_report(education_section: str) -> str:
    return f"""# 📌 归档信息与命盘结构

- 分析版本：v7.7
- 时间标准：公历（YYYY–YYYY年）+ 年龄（XX–XX岁）
- 报告路径：[x](reports/x.md)

## 四柱结构

四柱竖排：

| 项目 | 年柱 | 月柱 | 日柱 | 时柱 |
|---|---|---|---|---|
| 天干 | 甲 | 甲 | 癸 | 壬 |

## 大运速览

## 五派裁决与共识融合总论

## 命局做功与人生主线

## 主要事项结构

| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |

### 学业结构

| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |
|---|---|---|---|---|---|---|
{education_section}

### 事业结构

| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |

### 财富结构

| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |

### 婚姻结构

| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |

### 健康结构

| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈回写 | 稳定枚举 |

## 受限概率系统

置信状态（星级）：中（★★★☆☆）

| 事件领域 | 具体应事 | 时间窗口 | 概率 | 置信状态 | 星级 |
|---|---|---|---|---|---|
| 学业 | 测试 | 2025–2030年 | 76% | 中 | ★★★☆☆ |

## 待反馈关键流年与事件

### 待反馈（已发生验证项）

| 优先级 | 领域 | 时间窗口 | 具体应事 | 回访要点 |

### 待反馈（预测验证项）

| 优先级 | 领域 | 时间窗口 | 具体应事 | 回访要点 |

## 系统级约束

全部展示字段必须中文化。
"""


def test_v77_linter_blocks_education_without_university_stage() -> None:
    md = _minimal_v77_report(
        "| 学历层次 | 待反馈候选 | 能力强 | 中（★★★☆☆） | 1996–2004年 | 反馈 | 枚举 |"
    )

    result = lint(md)
    codes = {issue.code for issue in result.errors}

    assert "E-V77-EDU-STAGE-MISSING" in codes
    assert "E-V77-EDU-TIMELINE-MISSING" in codes
    assert "E-V77-EDU-BLANKET-WINDOW" in codes


def test_v77_linter_accepts_education_timeline_and_causal_chain() -> None:
    edu = """| 学历层次 | 待反馈候选：不能由学习能力直接推出学历 | 学习能力需接考试表现 | 中（★★★☆☆） | 分段 | 反馈 | 枚举 |

#### 教育阶段时间轴

| 阶段 | 年份窗口 | 年龄窗口 | 大运切片 | 必须校验 |
|---|---|---|---|---|
| 小学阶段 | 1990–1996年 | 6–12岁 | 乙亥运 | 基础学习 |
| 初中阶段 | 1996–1999年 | 12–15岁 | 丙子运 | 排名 |
| 高中阶段 | 1999–2002年 | 15–18岁 | 丙子运 | 高考 |
| 大学阶段 | 2002–2006年 | 18–22岁 | 丙子运→丁丑运 | 高考、录取、学校层级、毕业 |
| 毕业或证照兑现 | 2006–2008年 | 22–24岁 | 丁丑运 | 毕业 |

> 学业因果链约束：不能由学习能力直接推出学历；必须按“学习能力 → 考试表现 → 高考/录取 → 学校层级 → 学历或毕业兑现”逐层校验。现实锚点不足时只输出待反馈候选。
"""
    result = lint(_minimal_v77_report(edu))

    edu_errors = [issue for issue in result.errors if issue.code.startswith("E-V77-EDU")]
    assert edu_errors == []
