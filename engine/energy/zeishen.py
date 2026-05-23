"""engine/energy/zeishen.py · v1.2 D1 段派 · 贼神捕神

段派"贼神捕神"（M1-D-015..016, 115）：

正向（应吉）：
    强体 + 弱用 + 大运到位（捕神）= 应吉
    捕神 = 大运/流年到位的"激发字"

反向（应凶）：
    强用 + 弱体 = 应凶
    贼神 = 强体的克星 + 弱用 = 引爆点

段派应用：解释"为什么 X 大运反而出问题"。

启发式实现（08 § 失败兜底允许简化）：
- 贼神 = 体强方的克星（=用神字）
- 捕神 = 贼神在原局已存在 + 大运字的引爆字
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import ZeishenBushen
from engine.predicates.types import (
    Bazi,
    Dayun,
    Gan,
    Wuxing,
    Zhi,
)
from engine.predicates.ganzhi import gan_to_wuxing, zhi_to_wuxing
from engine.predicates.strength import calc_wuxing_strength
from engine.predicates.wuxing import wuxing_relation


def evaluate_zeishen(
    bazi: Bazi,
    dayun: Optional[Dayun] = None,
) -> ZeishenBushen:
    """贼神/捕神识别。

    简化逻辑：
    1. 计算 5 行势力，识别"强势五行"（势力 ≥ 0.30）
    2. 贼神 = 强势五行的克者（按 day_master 视角属于"用神"或反生）
    3. 捕神 = 大运中字面与贼神字符同行的字
    """
    day_master = bazi.day_master
    day_wx = gan_to_wuxing(day_master)
    shi = calc_wuxing_strength(bazi)

    # 找强势五行（除日干本五行外）
    strong_wxs = [(wx, v) for wx, v in shi.items() if v >= 0.30]
    strong_wxs.sort(key=lambda x: -x[1])

    zei_shen: list[str] = []  # 贼神字（克我者 / 制我者）
    bu_shen: list[str] = []   # 捕神字
    triggered_steps: list[int] = []
    rationale_parts: list[str] = []

    for wx, val in strong_wxs:
        rel = wuxing_relation(day_wx, wx)
        if rel == "克我":
            # 强官杀 → 是贼神
            zei_shen.append(wx)
            rationale_parts.append(f"{wx}势 {val:.0%} 极旺且为'克我'（官杀） → 贼神")

    # 捕神 = 大运字与贼神同五行
    if dayun and zei_shen:
        for step in dayun.排布:
            sgan_wx = gan_to_wuxing(step.干支.gan)
            szhi_wx = zhi_to_wuxing(step.干支.zhi)
            for zwx in zei_shen:
                if sgan_wx == zwx or szhi_wx == zwx:
                    bu_shen.append(str(step.干支))
                    triggered_steps.append(step.序号)
                    break

    rationale = "段派贼神捕神（M1-D-015..016）：" + ("; ".join(rationale_parts)
                                                    if rationale_parts else "无极旺克我者，贼神不显")

    return ZeishenBushen(
        zei_shen=zei_shen,
        bu_shen=bu_shen,
        triggered_by_dayun=triggered_steps,
        rationale=rationale,
    )


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from engine.predicates.types import GanZhi, _default_canggan_for, DayunStep, Dayun

    bazi = Bazi(
        年柱=GanZhi("庚", "申"),
        月柱=GanZhi("戊", "寅"),
        日柱=GanZhi("壬", "子"),
        时柱=GanZhi("辛", "丑"),
    )
    bazi.藏干 = _default_canggan_for(bazi)

    # 大运（精简）
    dy = Dayun(
        起运岁=8.5,
        起运年=1988,
        顺逆="顺",
        排布=[
            DayunStep(序号=1, 干支=GanZhi("己", "卯"), 起岁=8, 止岁=17, 起讫年=(1988, 1998)),
            DayunStep(序号=2, 干支=GanZhi("庚", "辰"), 起岁=18, 止岁=27, 起讫年=(1998, 2008)),
            DayunStep(序号=3, 干支=GanZhi("辛", "巳"), 起岁=28, 止岁=37, 起讫年=(2008, 2018)),
            DayunStep(序号=4, 干支=GanZhi("壬", "午"), 起岁=38, 止岁=47, 起讫年=(2018, 2028)),
        ],
    )
    z = evaluate_zeishen(bazi, dy)
    print(f"贼神: {z.zei_shen}, 捕神: {z.bu_shen}, 引爆步: {z.triggered_by_dayun}")
    print(f"rationale: {z.rationale}")
    print("[OK] zeishen smoke")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
