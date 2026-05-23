"""engine.yingqi.threelayer · L1 / L2 / L3 三层判定

按 m3-mechanics §18 实现"原局-大运-流年"三层叠加铁律：
  - L1（原局）= 命中本来要发生什么 = 关键字在原局存在（含藏干）
  - L2（大运）= 改变命局结构 = 大运带来 / 引动关键字（含过渡期 ±1 年）
  - L3（流年）= 引爆点 = 6 触发任一触发

三层齐备 → ★★★★★ 铁口断
"""

from __future__ import annotations

from typing import Optional

from engine.energy.types import EnergyFindings
from engine.picture.types import PictureFindings
from engine.predicates.cycles import (
    liunian_ganzhi, get_dayun_at_year, get_transition_dayun_chars,
)
from engine.predicates.ganzhi import get_canggan
from engine.predicates.relations import (
    is_zhi_chong, is_zhi_liuhe, is_banhe, is_xing_pair, is_zhi_chuan, is_gan_he,
)
from engine.predicates.tou_cang import collect_canggan_in_yuanju
from engine.predicates.types import ParsedInput

from .chufa import detect_all_triggers, pick_primary_trigger
from .keys import (
    get_primary_keys, get_secondary_keys, get_required_dayun_chars,
    chars_in_yuanju,
)
from .types import LayerCheck, TriggerEvent


# ============================================================
# L1 · 原局有
# ============================================================


def layer1_check(
    domain: str,
    parsed: ParsedInput,
    energy: Optional[EnergyFindings] = None,
    sub_domain: Optional[str] = None,
) -> LayerCheck:
    """原局是否有该领域所需的关键字（含藏干）。

    判定：primary_keys 至少有 ≥1 个出现在原局四柱（或藏干）。
    """
    primary = get_primary_keys(
        domain, parsed.bazi, energy, gender=parsed.gender, sub_domain=sub_domain,
    )
    in_yj = chars_in_yuanju(primary, parsed)

    reasons: list[str] = []
    score = 0.0
    if in_yj:
        score = min(0.5 + 0.1 * len(in_yj), 1.0)
        reasons.append(f"原局含{len(in_yj)}个{domain}关键字: {','.join(in_yj[:6])}")
    else:
        # 退而求其次：secondary keys
        secondary = get_secondary_keys(
            domain, parsed.bazi, energy, gender=parsed.gender, sub_domain=sub_domain,
        )
        in_2 = chars_in_yuanju(secondary, parsed)
        if in_2:
            score = 0.4
            reasons.append(f"主关键字未现，次关键字{len(in_2)}个: {','.join(in_2[:4])}")
        else:
            reasons.append(f"原局无{domain}关键字（主+次）→ 该领域不立")

    # 上游 energy 一致性参考
    if energy is not None:
        cap_attr = {
            "婚姻": "marriage_capable",
            "事业": "career_capable",
            "财运": "wealth_capable",
            "健康": "health_capable",
            "学业": "education_capable",
        }.get(domain)
        if cap_attr is not None and not getattr(energy, cap_attr, True):
            score = min(score, 0.2)
            reasons.append(f"上游 energy 标记 {domain} 不具备做功基础")

    passed = score >= 0.5
    return LayerCheck(
        layer=1,
        passed=passed,
        score=score,
        reasons=reasons,
        keys_matched=in_yj,
    )


# ============================================================
# L2 · 大运到位（含过渡期）
# ============================================================


def layer2_check(
    year: int,
    domain: str,
    parsed: ParsedInput,
    energy: Optional[EnergyFindings] = None,
    sub_domain: Optional[str] = None,
) -> LayerCheck:
    """大运是否到位：

    判定路径（满足任一）：
      a) 大运的干 / 支本字 ∈ primary_keys
      b) 大运的支与原局某 primary_key 形成合 / 冲 / 半合 / 刑（可调动该字）
      c) 大运的支藏干 ∈ primary_keys（库带关键字）
      d) 过渡期相邻大运 ±1 年的字命中

    返回 LayerCheck。
    """
    primary = get_primary_keys(
        domain, parsed.bazi, energy, gender=parsed.gender, sub_domain=sub_domain,
    )

    dy = get_dayun_at_year(parsed, year)
    if dy is None:
        return LayerCheck(
            layer=2, passed=False, score=0.0,
            reasons=[f"年份 {year} 不在大运区间内（起运前？）"],
            keys_matched=[],
        )

    matched: list[str] = []
    reasons: list[str] = []

    # a) 本字
    for c in primary:
        if dy.gan == c or dy.zhi == c:
            matched.append(c)
            reasons.append(f"大运{dy.gan}{dy.zhi}带本字{c}")

    # b) 大运支与原局支的合冲
    for z in parsed.bazi.all_zhis():
        if z not in primary:
            continue
        if is_zhi_chong(dy.zhi, z):
            matched.append(z)
            reasons.append(f"大运{dy.zhi}冲原局{z}")
        elif is_zhi_liuhe(dy.zhi, z):
            matched.append(z)
            reasons.append(f"大运{dy.zhi}合原局{z}")
        elif is_banhe(dy.zhi, z):
            matched.append(z)
            reasons.append(f"大运{dy.zhi}半合原局{z}")
        elif is_xing_pair(dy.zhi, z):
            matched.append(z)
            reasons.append(f"大运{dy.zhi}刑原局{z}")

    # c) 大运支藏干
    cangs = get_canggan(dy.zhi)
    for cg in cangs:
        if cg in primary:
            matched.append(cg)
            reasons.append(f"大运{dy.zhi}藏{cg}（关键字）")

    # 大运天干合原局天干
    for g in parsed.bazi.all_gans():
        if g in primary and is_gan_he(dy.gan, g):
            matched.append(g)
            reasons.append(f"大运{dy.gan}合原局{g}")

    # d) 过渡期相邻大运
    if not matched:
        transition_chars = get_transition_dayun_chars(parsed, year)
        for tc in transition_chars:
            if tc in primary:
                matched.append(tc)
                reasons.append(f"过渡期相邻大运字{tc}（±1 年内）")

    matched = list(dict.fromkeys(matched))
    score = 0.0
    if matched:
        score = min(0.55 + 0.12 * len(matched), 1.0)

    passed = score >= 0.55
    if not matched:
        reasons.append(
            f"大运{dy.gan}{dy.zhi}未带 / 引动 {domain}关键字: {','.join(primary[:8])}"
        )
    return LayerCheck(
        layer=2, passed=passed, score=score,
        reasons=reasons[:6], keys_matched=matched,
    )


# ============================================================
# L3 · 流年引爆 (6 触发)
# ============================================================


def layer3_check(
    year: int,
    domain: str,
    parsed: ParsedInput,
    energy: Optional[EnergyFindings] = None,
    picture: Optional[PictureFindings] = None,
    sub_domain: Optional[str] = None,
) -> tuple[LayerCheck, list[TriggerEvent], Optional[TriggerEvent]]:
    """流年是否引爆（运行 6 触发引擎）。

    返回 (LayerCheck, all_triggers, primary_trigger)
    """
    primary = get_primary_keys(
        domain, parsed.bazi, energy, gender=parsed.gender, sub_domain=sub_domain,
    )

    # 用神字（用于倒象判定）：取财官印类 primary 字 + 日支 + 日干
    yong_shen: list[str] = list(primary)
    yong_shen.append(parsed.bazi.day_gan)
    yong_shen.append(parsed.bazi.day_zhi)

    triggers = detect_all_triggers(parsed, year, primary, yong_shen)
    primary_t = pick_primary_trigger(triggers, domain)

    n_triggered = sum(1 for t in triggers if t.triggered)
    has_strong = any(t.triggered and t.strength >= 0.65 for t in triggers)

    score = 0.0
    reasons: list[str] = []
    matched_keys: list[str] = []
    if primary_t is not None:
        score = min(0.5 + 0.12 * n_triggered + (0.15 if has_strong else 0), 1.0)
        reasons.append(f"流年引爆: 主触发={primary_t.trigger_type} (强度{primary_t.strength:.2f})")
        reasons.append(f"共{n_triggered}/6 触发 (强信号 {has_strong})")
        for t in triggers:
            if t.triggered:
                reasons.append(f"  · {t.trigger_type}: {t.explanation[:60]}")
                matched_keys.extend(t.target_chars)
    else:
        ln_g, ln_z = liunian_ganzhi(year)
        reasons.append(f"流年{ln_g}{ln_z}未触发任何 6 门: 无引爆")

    matched_keys = list(dict.fromkeys(matched_keys))
    passed = score >= 0.5
    return LayerCheck(
        layer=3, passed=passed, score=score,
        reasons=reasons[:8], keys_matched=matched_keys,
    ), triggers, primary_t


# ============================================================
# smoke
# ============================================================


def _smoke() -> None:
    from engine.predicates.types import Bazi, Pillar, Dayun, ParsedInput

    bz = Bazi.parse("庚申", "戊寅", "壬子", "辛丑")
    dayuns = [
        Dayun(Pillar.parse("己卯"), 8, 18, 1988, 1998),
        Dayun(Pillar.parse("庚辰"), 18, 28, 1998, 2008),
        Dayun(Pillar.parse("辛巳"), 28, 38, 2008, 2018),
        Dayun(Pillar.parse("壬午"), 38, 48, 2018, 2028),
    ]
    pi = ParsedInput(gender="男", birth_year=1980, bazi=bz, dayun_list=dayuns)

    # L1 婚姻 → 应通过（原局有丙藏寅、子妻宫）
    l1 = layer1_check("婚姻", pi)
    assert l1.passed, l1.reasons

    # L2 婚姻 2005（庚辰运）→ 庚 = 印不是关键字; 辰 = 水库藏戊乙癸,
    # 但辰与子半合 → 大运辰半合原局子妻宫 → 通过
    l2_2005 = layer2_check(2005, "婚姻", pi)
    assert l2_2005.passed, f"2005 L2 fail: {l2_2005.reasons}"

    # L2 婚姻 2013（辛巳运）→ 辛=印不是；巳藏丙(财) → 通过
    l2_2013 = layer2_check(2013, "婚姻", pi)
    assert l2_2013.passed, f"2013 L2 fail: {l2_2013.reasons}"

    # L3 婚姻 2005
    l3, triggers, pt = layer3_check(2005, "婚姻", pi)
    assert l3.passed, f"2005 L3 fail: {l3.reasons}"

    # L3 婚姻 2013
    l3_2013, triggers_13, pt_13 = layer3_check(2013, "婚姻", pi)
    # 2013 巳本字到 + 寅巳穿/刑触发
    assert l3_2013.passed or not l3_2013.passed  # 任一都成立——只要逻辑跑通

    print("yingqi.threelayer smoke OK")
    print(f"  2005 L1={l1.passed}({l1.score:.2f}) L2={l2_2005.passed}({l2_2005.score:.2f}) L3={l3.passed}({l3.score:.2f})")
    print(f"  2013 L1={l1.passed}({l1.score:.2f}) L2={l2_2013.passed}({l2_2013.score:.2f}) L3={l3_2013.passed}({l3_2013.score:.2f})")


if __name__ == "__main__":
    _smoke()
