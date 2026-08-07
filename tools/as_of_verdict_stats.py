"""as-of 盲断闭环 · 三态独立命中统计（不合并为单一命中率）。

背景（根因诊断，见 reports/as-of-life-state-blind-judgment-root-cause-report.md）：
历轮 as-of 报告把 ``engine.asof.reality_translation.LandingVerdict`` 的
``CENTER_HIT``（精确命中中心落点）、``ALTERNATIVE_HIT``（命中同域同向的替代
落点，即方向判断对但强度/主导从属判断偏差）、``MISS``（方向判断本身不对）
三种性质完全不同的结果，在跨轮次汇总表里合并成单一"命中或部分命中"分数
（例如 6/11）。这掩盖了更有信息量的分布：8 个已核验样本复核显示 2 个真
CENTER_HIT、3 个 ALTERNATIVE_HIT（且全部是"预测主导深化，实际从属受限"这一个
方向的系统性偏差，无反向案例）、3 个 MISS（其中 2 个的 root_level 判定本身
就已经系统性偏乐观，见 tools/as_of_root_level_gate.py）。

本模块只做统计汇总，不改变任何既有 verified-result.json、不改变
``engine.asof`` 契约、不重新裁决任何历史案例。输入是调用方已经从磁盘读取好的
逐案 verdict 记录（三元组：case_id、verdict 字符串、可选的强度偏差方向），
输出是三态独立计数与显式的偏差方向分布，供报告引用，替代继续汇报单一分数。
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

__all__ = (
    "VALID_VERDICTS",
    "VALID_BIAS_DIRECTIONS",
    "CaseVerdictRecord",
    "ThreeWaySummary",
    "summarize_verdicts",
)

# 与 engine.asof.reality_translation.LandingVerdict 的字符串值保持一致；
# 本模块不 import 该枚举，避免统计工具与生产契约产生非必要耦合，但字符串值
# 必须手动保持同步（若该枚举新增取值，本模块的校验会拒绝未知字符串，逼迫
# 调用方显式更新 VALID_VERDICTS 而不是静默吞掉新状态）。
VALID_VERDICTS = frozenset({"CENTER_HIT", "ALTERNATIVE_HIT", "MISS", "TAXONOMY_GAP", "ABSTAIN"})

# 仅对 ALTERNATIVE_HIT 有意义：预测的强度/主导-从属方向与实际落地的偏差方向。
VALID_BIAS_DIRECTIONS = frozenset({"OPTIMISTIC", "PESSIMISTIC", "NONE"})


@dataclass(frozen=True, slots=True)
class CaseVerdictRecord:
    """单案的三态归类记录；调用方从已有 verified-result.json 手动整理得到。"""

    case_id: str
    verdict: str
    strength_bias_direction: str = "NONE"

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty")
        if self.verdict not in VALID_VERDICTS:
            raise ValueError(
                f"unknown verdict {self.verdict!r}; update VALID_VERDICTS if this is a real new state"
            )
        if self.strength_bias_direction not in VALID_BIAS_DIRECTIONS:
            raise ValueError(f"unknown bias direction {self.strength_bias_direction!r}")
        if self.verdict != "ALTERNATIVE_HIT" and self.strength_bias_direction != "NONE":
            raise ValueError("strength_bias_direction only applies to ALTERNATIVE_HIT records")


@dataclass(frozen=True, slots=True)
class ThreeWaySummary:
    """三态独立统计结果；不产出单一合并命中率。"""

    total: int
    verdict_counts: dict[str, int]
    alternative_hit_bias_counts: dict[str, int]

    def as_report_lines(self) -> tuple[str, ...]:
        """生成可直接粘贴进报告的行，禁止把三态合并成单一分数。"""

        lines = [f"有效样本总数：{self.total}"]
        for verdict in ("CENTER_HIT", "ALTERNATIVE_HIT", "MISS", "TAXONOMY_GAP", "ABSTAIN"):
            count = self.verdict_counts.get(verdict, 0)
            if count:
                lines.append(f"{verdict}：{count}")
        if self.verdict_counts.get("ALTERNATIVE_HIT", 0):
            for direction in ("OPTIMISTIC", "PESSIMISTIC"):
                count = self.alternative_hit_bias_counts.get(direction, 0)
                if count:
                    lines.append(f"  其中 ALTERNATIVE_HIT 偏差方向={direction}：{count}")
        return tuple(lines)


def summarize_verdicts(records: tuple[CaseVerdictRecord, ...]) -> ThreeWaySummary:
    """按三态独立统计，不产出 (CENTER_HIT+ALTERNATIVE_HIT)/total 这类合并分数。

    调用方若确实需要单一数字用于内部排序等非报告用途，应自行在报告展示层之外
    计算，不应通过本函数获得——本函数的输出契约就是拒绝提供该数字，逼迫报告
    撰写者展示三态分布本身。
    """

    if not records:
        raise ValueError("at least one verdict record is required")
    seen_ids = {record.case_id for record in records}
    if len(seen_ids) != len(records):
        raise ValueError("duplicate case_id in verdict records")

    verdict_counter = Counter(record.verdict for record in records)
    bias_counter = Counter(
        record.strength_bias_direction
        for record in records
        if record.verdict == "ALTERNATIVE_HIT" and record.strength_bias_direction != "NONE"
    )
    return ThreeWaySummary(
        total=len(records),
        verdict_counts=dict(verdict_counter),
        alternative_hit_bias_counts=dict(bias_counter),
    )
