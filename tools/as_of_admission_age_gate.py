"""as-of 盲断闭环 · admission 阶段命主年龄×as_of_date 窗口匹配预筛选。

背景（根因诊断，见 reports/as-of-life-state-blind-judgment-root-cause-report.md）：
``reports/as-of-life-state-blind-judgment-n50-extension-report-r2.md`` §7 第2条
自行记录：该轮 6 个新增候选中 3 个（50%）因窗口内证据不足被记为无效样本，
高于 N5 轮的 1/5（20%），且该报告已经诊断出原因——命主在候选 as_of_date 时
仍处于学生阶段或刚入职，尚未产生可评分的事业事件；报告本身提出"应在
ADMISSION 阶段增加命主年龄与 as_of_date 窗口匹配度的预筛选"，但未落地。

本模块提供最小可行的预筛选函数：给定出生日期与候选 as_of_date，返回该案例
在候选 as_of_date 时的命主年龄，以及是否落在"可能已有可评分事业事件"的
合理年龄区间。这只是启发式预筛选，不是准入门槛的充分条件：年龄落在区间内
不保证反馈里一定有可评分事件（命主可能读研、深造、失业空窗等），年龄落在
区间外也不是绝对排除依据（不常见的早熟或超龄案例仍可能有效）。本模块的
目的是把"候选 as_of_date 选在命主明显还是学生的年龄"这类可预先避免的无效
样本，尽量筛在阅读 feedback.md 之前，从而降低判读工时的浪费——不是提高
判断准确率本身。

本模块不读取任何案例文件、不导入 engine.asof、不构成 as-of 两阶段协议
（截断→冻结→揭示→核验）的任何一步，只是该协议开始前的一个独立预筛选步骤。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

__all__ = (
    "DEFAULT_MIN_CAREER_AGE",
    "DEFAULT_MAX_CAREER_AGE",
    "AgeWindowFinding",
    "compute_age_at",
    "check_age_window_fit",
)

# 依据 n50-extension-report-r2.md §7 第2条的观察：3 个因窗口不足被记为无效
# 样本的案例，命主在候选 as_of_date 时"仍在学生阶段或刚入职"。国内典型全日制
# 教育路径下，多数人 22 岁左右本科毕业进入职场，因此把默认下界设为 23（给
# 应届入职留出至少半年到一年的时间产生可评分事件），上界设为 65（法定退休
# 年龄附近，超过后职业事件密度通常显著下降）。这两个默认值都是启发式估计，
# 不是精确心理学或劳动统计学结论，调用方可按具体案例覆盖。
DEFAULT_MIN_CAREER_AGE = 23
DEFAULT_MAX_CAREER_AGE = 65


@dataclass(frozen=True, slots=True)
class AgeWindowFinding:
    """单案的年龄×窗口匹配度预筛选结果。"""

    age_at_as_of_date: int
    fits_career_window: bool
    note: str


def compute_age_at(birth_date: date, as_of_date: date) -> int:
    """按周岁计算命主在 ``as_of_date`` 时的年龄。"""

    if as_of_date < birth_date:
        raise ValueError("as_of_date must not precede birth_date")
    age = as_of_date.year - birth_date.year
    if (as_of_date.month, as_of_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def check_age_window_fit(
    birth_date: date,
    as_of_date: date,
    *,
    min_career_age: int = DEFAULT_MIN_CAREER_AGE,
    max_career_age: int = DEFAULT_MAX_CAREER_AGE,
) -> AgeWindowFinding:
    """预筛选候选 as_of_date 是否落在命主可能已有可评分事业事件的年龄区间。

    这是 admission 阶段的启发式预筛选，不是准入的充分或必要条件：命中
    ``fits_career_window=False`` 只提示"这个候选窗口选择更容易产出无效样本，
    建议换一个 as_of_date 或换一个候选案例"，不构成自动拒绝；调用方仍应
    结合具体案例背景做最终判断。
    """

    if min_career_age < 0 or max_career_age < min_career_age:
        raise ValueError("invalid career age bounds")

    age = compute_age_at(birth_date, as_of_date)
    fits = min_career_age <= age <= max_career_age

    if fits:
        note = f"命主在候选 as_of_date 时年龄为 {age} 岁，落在职业活跃期区间内。"
    elif age < min_career_age:
        note = (
            f"命主在候选 as_of_date 时年龄仅 {age} 岁，低于职业活跃期下界"
            f"{min_career_age} 岁，很可能仍处于学生阶段或刚入职，建议改选更晚的"
            "as_of_date 或更换候选案例，以降低窗口内无可评分事业事件的概率。"
        )
    else:
        note = (
            f"命主在候选 as_of_date 时年龄已达 {age} 岁，超过职业活跃期上界"
            f"{max_career_age} 岁，事业事件密度可能显著下降，建议核实该窗口是否"
            "仍适合作为事业候选事件的核验窗口。"
        )

    return AgeWindowFinding(age_at_as_of_date=age, fits_career_window=fits, note=note)
