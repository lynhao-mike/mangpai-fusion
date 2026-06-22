"""领域层 social-clock 与体制路径关键词协议。

这些规则同时被 D3 应期 gate 与报告级 output_linter 消费。集中维护后，新增或调整
关键词时不会出现 gate 通过但 lint 仍按旧口径告警的漂移。
"""
from __future__ import annotations


SocialClockRule = tuple[tuple[str, ...], tuple[int, int], str]
EducationStageRule = tuple[str, tuple[int, int], str]

# 事件关键词 → (lo, hi, label) 年龄窗口。按长关键词优先排序。
SOCIAL_CLOCK_RULES: tuple[SocialClockRule, ...] = (
    (("研究生毕业", "硕士毕业"), (24, 29), "研究生毕业"),
    (("博士毕业", "PhD毕业", "PhD 毕业"), (27, 35), "博士毕业"),
    (("研究生入学", "硕士入学", "读研"), (21, 26), "研究生入学"),
    (("博士入学",), (24, 32), "博士入学"),
    (("本科毕业", "大学毕业"), (21, 24), "本科毕业（4 年制）"),
    (("高考",), (17, 19), "高考"),
    (("考研",), (21, 25), "考研"),
    (("入学", "上学", "录取"), (17, 23), "升学/入学"),
    (("初婚", "成家"), (20, 40), "初婚"),
    (("结婚", "成婚", "嫁", "娶", "领证"), (20, 50), "结婚（含再婚）"),
    (("入职", "第一份工作", "首份工作"), (21, 28), "首次入职"),
    (("升迁", "升职", "提拔", "晋升"), (25, 65), "升职"),
    (("退休",), (55, 70), "退休"),
    (("生子", "生女", "怀孕", "得子", "得女"), (20, 45), "生育"),
)

# 偏差容忍度（单位：年）。农历/虚岁换算可能有 ±1 年误差。
SOCIAL_CLOCK_TOLERANCE: int = 1

# 教育阶段窗口：用于报告层强制拆分学业时间轴，避免把初中/高中/大学合并为笼统区间。
EDUCATION_STAGE_RULES: tuple[EducationStageRule, ...] = (
    ("小学阶段", (6, 12), "基础学习、家庭教育、启蒙稳定度"),
    ("初中阶段", (12, 15), "排名、偏科、学习习惯、人际分心"),
    ("高中阶段", (15, 18), "高考能力、考试稳定性、升学压力"),
    ("大学阶段", (18, 22), "录取批次、学校层级、专业、复读/转学/毕业"),
    ("毕业或证照兑现", (22, 24), "毕业年份、最高学历、证照或中断"),
)


def build_education_timeline(birth_year: int) -> list[dict[str, object]]:
    """按出生年生成标准教育阶段时间轴。

    该函数只生成社会学制窗口，不直接给学历结论；学历结论必须另接考试、录取、学校、毕业和反馈锚点。
    """
    return [
        {
            "stage": stage,
            "age_range": age_range,
            "year_range": (birth_year + age_range[0], birth_year + age_range[1]),
            "required_checks": checks,
        }
        for stage, age_range, checks in EDUCATION_STAGE_RULES
    ]

# 体制路径关键词。保留 output_linter 的完整关键词与 gate 的核心子集。
INSTITUTIONAL_KEYWORDS: tuple[str, ...] = (
    "体制内",
    "公门",
    "国企",
    "体制",
    "事业单位",
    "选调",
    "公务员",
    "党政",
    "行政机关",
    "行政",
    "省厅",
    "正厅",
    "副厅",
    "正处",
    "副处",
    "厅局级",
    "厅局",
    "省部级",
    "省部",
)

INSTITUTIONAL_HINTS: tuple[str, ...] = INSTITUTIONAL_KEYWORDS
