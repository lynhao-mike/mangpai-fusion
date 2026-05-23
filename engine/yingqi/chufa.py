"""engine.yingqi.chufa · 6 触发引擎

按 m3-mechanics §17 实现 6 大触发：
  1. 本字到
  2. 伏吟引动
  3. 合冲引动
  4. 墓库开闭
  5. 藏干透出
  6. 倒象成立  ← 任派核心铁律：必凶

每个 detect_* 函数返回 TriggerEvent。
"""

from __future__ import annotations

from typing import Optional

from engine.predicates.cycles import (
    liunian_ganzhi, get_dayun_at_year, is_liunian_yingdong_bazi_zi,
)
from engine.predicates.ganzhi import (
    get_canggan, get_wuxing, is_ke, is_sheng,
)
from engine.predicates.relations import (
    is_gan_he, is_zhi_liuhe, is_zhi_chong, is_banhe,
    is_zhi_chuan, is_xing_pair, is_zhi_anhe, is_zixing,
    SAN_HE_GROUPS, all_zhi_relations,
)
from engine.predicates.tou_cang import is_tou_at, collect_canggan_in_yuanju
from engine.predicates.types import ParsedInput

from .types import TriggerEvent, TRIGGER_TYPES


# ============================================================
# 1) 本字到
# ============================================================


def detect_benzi_dao(
    parsed: ParsedInput, year: int, key_chars: list[str]
) -> TriggerEvent:
    """流年/大运 是否带来关键字本字。"""
    ln_g, ln_z = liunian_ganzhi(year)
    dy = get_dayun_at_year(parsed, year)
    matched: list[str] = []
    via: list[str] = []
    for c in key_chars:
        if ln_g == c or ln_z == c:
            matched.append(c)
            via.append(f"流年{c}")
        if dy is not None and (dy.gan == c or dy.zhi == c):
            matched.append(c)
            via.append(f"大运{c}")
    matched = list(dict.fromkeys(matched))
    via = list(dict.fromkeys(via))
    triggered = bool(matched)
    return TriggerEvent(
        trigger_type="本字到",
        triggered=triggered,
        strength=min(0.4 + 0.2 * len(matched), 1.0) if triggered else 0.0,
        target_chars=matched,
        explanation="; ".join(via) if via else "无本字到",
    )


# ============================================================
# 2) 伏吟引动
# ============================================================


def detect_fuyin(parsed: ParsedInput, year: int) -> TriggerEvent:
    """流年柱伏吟原局任一柱（干 + 支同字）。"""
    ln_g, ln_z = liunian_ganzhi(year)
    pillar_names = ["年柱", "月柱", "日柱", "时柱"]
    pillars = [parsed.bazi.year, parsed.bazi.month, parsed.bazi.day, parsed.bazi.hour]
    matched_pillars: list[str] = []
    matched_chars: list[str] = []
    for name, p in zip(pillar_names, pillars):
        if p.gan == ln_g and p.zhi == ln_z:
            matched_pillars.append(f"{name}({p.gan}{p.zhi})")
            matched_chars.extend([p.gan, p.zhi])
    # 也考虑大运伏吟
    dy = get_dayun_at_year(parsed, year)
    if dy is not None:
        for name, p in zip(pillar_names, pillars):
            if p.gan == dy.gan and p.zhi == dy.zhi:
                matched_pillars.append(f"大运伏吟{name}({p.gan}{p.zhi})")
                matched_chars.extend([p.gan, p.zhi])
    matched_chars = list(dict.fromkeys(matched_chars))
    triggered = bool(matched_pillars)
    return TriggerEvent(
        trigger_type="伏吟引动",
        triggered=triggered,
        strength=0.7 if triggered else 0.0,
        target_chars=matched_chars,
        explanation="; ".join(matched_pillars) if matched_pillars else "无伏吟",
    )


# ============================================================
# 3) 合冲引动
# ============================================================


def detect_hechong(
    parsed: ParsedInput, year: int, key_chars: list[str]
) -> TriggerEvent:
    """合冲引动：流年/大运 与原局之间，对关键字的 合 / 冲 / 解合 / 解冲。

    任派 §15.8 / §17：
      - 命中有合，流年逢冲 = 应（解合）
      - 命中有冲，流年逢合 = 应（解冲）
      - 命中既不冲也不合，流年单独形成合或冲 = 应
    """
    ln_g, ln_z = liunian_ganzhi(year)
    dy = get_dayun_at_year(parsed, year)
    matched_chars: list[str] = []
    explanations: list[str] = []

    bazi_zhis = parsed.bazi.all_zhis()
    bazi_gans = parsed.bazi.all_gans()
    pillar_names = ["年", "月", "日", "时"]

    # 3.1 流年支 vs 原局
    for name, z in zip(pillar_names, bazi_zhis):
        rels = all_zhi_relations(ln_z, z)
        if not rels:
            continue
        # 关键字过滤：z 是关键字，或 z 的合冲伴侣是关键字
        if z in key_chars or any(r in {"六合", "冲", "半合"} for r in rels):
            matched_chars.append(z)
            explanations.append(f"流年{ln_z}-{name}支{z}: {','.join(rels)}")
    # 流年支 vs 大运支
    if dy is not None:
        rels = all_zhi_relations(ln_z, dy.zhi)
        if rels:
            explanations.append(f"流年{ln_z}-大运{dy.zhi}: {','.join(rels)}")
            if any(r in {"六合", "冲", "半合"} for r in rels):
                matched_chars.append(dy.zhi)

    # 3.1.5 大运支 vs 原局支（核心：大运直接动到关键字 / 主位）
    if dy is not None:
        for name, z in zip(pillar_names, bazi_zhis):
            rels = all_zhi_relations(dy.zhi, z)
            if not rels:
                continue
            if z in key_chars or any(r in {"六合", "冲", "半合", "穿", "刑"} for r in rels):
                matched_chars.append(z)
                explanations.append(f"大运{dy.zhi}-{name}支{z}: {','.join(rels)}")

    # 3.2 流年干 vs 原局天干
    for name, g in zip(pillar_names, bazi_gans):
        if is_gan_he(ln_g, g):
            matched_chars.append(g)
            explanations.append(f"流年干{ln_g}-{name}干{g}: 合")
        # 七冲（参 relations.gan_chong）暂不强调，留 explanation
    # 流年干 vs 大运干
    if dy is not None and is_gan_he(ln_g, dy.gan):
        matched_chars.append(dy.gan)
        explanations.append(f"流年干{ln_g}-大运干{dy.gan}: 合")

    # 3.3 解合 / 解冲（命中有合，流年冲；命中有冲，流年合）
    # 简化版：检测原局支两两是否相合 / 相冲，流年是否带来对应解合 / 解冲字
    for i in range(len(bazi_zhis)):
        for j in range(i + 1, len(bazi_zhis)):
            zi, zj = bazi_zhis[i], bazi_zhis[j]
            if is_zhi_liuhe(zi, zj):
                # 命中有合，流年是否冲其中一字 → 解合
                if is_zhi_chong(ln_z, zi) or is_zhi_chong(ln_z, zj):
                    explanations.append(f"解合: 原局{zi}{zj}合, 流年{ln_z}冲")
                    matched_chars.extend([zi, zj])
            elif is_zhi_chong(zi, zj):
                # 命中有冲，流年是否合其中一字 → 解冲
                if is_zhi_liuhe(ln_z, zi) or is_zhi_liuhe(ln_z, zj):
                    explanations.append(f"解冲: 原局{zi}{zj}冲, 流年{ln_z}合")
                    matched_chars.extend([zi, zj])

    # 仅保留与关键字相关的（限定到 domain）
    # 但若没有 key_chars 命中，仍保留 matched_chars（让 menshu 能看到合冲发生）
    if key_chars:
        related = [c for c in matched_chars if c in key_chars]
        # 关键字相关 OR 原局字（让 menshu/动门兜底分类）
        if not related:
            # 退而求其次：把所有原局相关的合冲字保留下来
            bazi_all = set(parsed.bazi.all_chars())
            related = [c for c in matched_chars if c in bazi_all]
        matched_chars = list(dict.fromkeys(related))
    else:
        matched_chars = list(dict.fromkeys(matched_chars))

    triggered = bool(matched_chars or explanations)
    # 强度：命中越多越强
    strength = 0.0
    if triggered:
        n = len(matched_chars)
        strength = min(0.5 + 0.15 * n, 1.0)
    return TriggerEvent(
        trigger_type="合冲引动",
        triggered=triggered,
        strength=strength,
        target_chars=matched_chars,
        explanation="; ".join(explanations) if explanations else "无合冲引动",
    )


# ============================================================
# 4) 墓库开闭
# ============================================================
# 寅申巳亥 入各自墓库（寅入未、申入丑、巳入戌、亥入辰）
# 子午卯酉 一般不入墓
# 财官入墓不发，逢冲刑开库即应

KU_MAP = {
    "未": "木",   # 寅 / 卯 入未
    "丑": "金",   # 申 / 酉 入丑
    "戌": "火",   # 巳 / 午 入戌
    "辰": "水",   # 亥 / 子 入辰
}


def detect_muku(
    parsed: ParsedInput, year: int, key_chars: list[str]
) -> TriggerEvent:
    """墓库开闭：原局有库 + 流年/大运冲刑该库 → 开库应。"""
    ln_g, ln_z = liunian_ganzhi(year)
    dy = get_dayun_at_year(parsed, year)
    bazi_zhis = parsed.bazi.all_zhis()

    explanations: list[str] = []
    matched: list[str] = []

    # 找原局含库的地支
    for z in bazi_zhis:
        if z not in KU_MAP:
            continue
        # 该库藏五行 = KU_MAP[z]
        ku_wx = KU_MAP[z]

        # 库里藏的关键字
        cangs_in_ku = get_canggan(z)
        key_in_ku = [c for c in cangs_in_ku if c in key_chars]
        if not key_in_ku:
            # 库里没装关键字 → 该库开闭无关
            continue

        # 是否被流年/大运冲、刑（开库）
        opened_by: list[str] = []
        if is_zhi_chong(ln_z, z):
            opened_by.append(f"流年{ln_z}冲")
        if is_xing_pair(ln_z, z):
            opened_by.append(f"流年{ln_z}刑")
        if dy is not None:
            if is_zhi_chong(dy.zhi, z):
                opened_by.append(f"大运{dy.zhi}冲")
            if is_xing_pair(dy.zhi, z):
                opened_by.append(f"大运{dy.zhi}刑")

        if opened_by:
            explanations.append(
                f"库{z}({ku_wx},藏{','.join(cangs_in_ku)})被开: {','.join(opened_by)}"
                f"; 库内关键字: {','.join(key_in_ku)}"
            )
            matched.append(z)
            matched.extend(key_in_ku)

        # 库被合住（合而不化）= 闭库 = 不应
        elif is_zhi_liuhe(ln_z, z) or (dy is not None and is_zhi_liuhe(dy.zhi, z)):
            explanations.append(f"库{z}被合（闭库）: 不应")

    matched = list(dict.fromkeys(matched))
    triggered = bool(matched)
    strength = 0.0
    if triggered:
        strength = min(0.6 + 0.15 * len(matched), 1.0)
    return TriggerEvent(
        trigger_type="墓库开闭",
        triggered=triggered,
        strength=strength,
        target_chars=matched,
        explanation="; ".join(explanations) if explanations else "无墓库开闭",
    )


# ============================================================
# 5) 藏干透出
# ============================================================


def detect_canggan_tou(
    parsed: ParsedInput, year: int, key_chars: list[str]
) -> TriggerEvent:
    """流年 / 大运 把原局藏干透出。"""
    ln_g, ln_z = liunian_ganzhi(year)
    dy = get_dayun_at_year(parsed, year)

    cangs_in_yj = collect_canggan_in_yuanju(parsed)
    explanations: list[str] = []
    matched: list[str] = []

    for cg, positions in cangs_in_yj.items():
        if cg not in key_chars:
            continue
        if cg in parsed.bazi.all_gans():
            continue  # 已经在天干里，不算"新透出"
        # 流年透出
        if ln_g == cg:
            matched.append(cg)
            explanations.append(f"藏干{cg}（{','.join(positions)}）→ 流年透出")
        # 大运透出
        if dy is not None and dy.gan == cg:
            matched.append(cg)
            explanations.append(f"藏干{cg}（{','.join(positions)}）→ 大运透出")

    matched = list(dict.fromkeys(matched))
    triggered = bool(matched)
    return TriggerEvent(
        trigger_type="藏干透出",
        triggered=triggered,
        strength=min(0.55 + 0.15 * len(matched), 1.0) if triggered else 0.0,
        target_chars=matched,
        explanation="; ".join(explanations) if explanations else "无藏干新透出",
    )


# ============================================================
# 6) 倒象成立（任派核心铁律）
# ============================================================
# §10：又制又生又合又冲成矛盾 = 倒象 → 必凶
#
# 简化判定：用神被 ≥ 3 种关系作用（合/冲/刑/穿/克）即倒象
# 完整判定：同时存在 制 + 生 = 矛盾


def detect_daoxiang(
    parsed: ParsedInput, year: int, yong_shen_chars: list[str]
) -> TriggerEvent:
    """倒象判定：用神被多重作用。

    简化版（按任务 fallback）：用神被 ≥3 种关系作用 → 倒象
    完整版（保留设计）：用神同时被 制 + 生 = 矛盾 = 倒象
    """
    ln_g, ln_z = liunian_ganzhi(year)
    dy = get_dayun_at_year(parsed, year)

    bazi_chars = parsed.bazi.all_chars()
    bazi_zhis = parsed.bazi.all_zhis()
    bazi_gans = parsed.bazi.all_gans()

    explanations: list[str] = []
    is_xiong = False

    # 收集 baseline (仅原局) 和 active (原局 + 大运 + 流年) 的字
    base_zhis = list(bazi_zhis)
    base_gans = list(bazi_gans)
    active_zhis = list(bazi_zhis)
    active_gans = list(bazi_gans)
    if dy is not None:
        active_gans.append(dy.gan)
        active_zhis.append(dy.zhi)
    active_gans.append(ln_g)
    active_zhis.append(ln_z)

    matched: list[str] = []

    def _count_rels(ys: str, gans: list[str], zhis: list[str]) -> dict[str, int]:
        rc: dict[str, int] = {}
        if ys in zhis or ys in "子丑寅卯辰巳午未申酉戌亥":
            for z in zhis:
                if z == ys:
                    continue
                rs = all_zhi_relations(z, ys)
                for r in rs:
                    rc[r] = rc.get(r, 0) + 1
            ys_wx = get_wuxing(ys)
            for g in gans:
                g_wx = get_wuxing(g)
                if is_ke(g_wx, ys_wx):
                    rc["天干克"] = rc.get("天干克", 0) + 1
                if is_sheng(g_wx, ys_wx):
                    rc["天干生"] = rc.get("天干生", 0) + 1
        if ys in gans or ys in "甲乙丙丁戊己庚辛壬癸":
            for g in gans:
                if g == ys:
                    continue
                if is_gan_he(g, ys):
                    rc["合"] = rc.get("合", 0) + 1
            ys_wx = get_wuxing(ys)
            for z in zhis:
                z_wx = get_wuxing(z)
                if is_ke(z_wx, ys_wx):
                    rc["地支克"] = rc.get("地支克", 0) + 1
                if is_sheng(z_wx, ys_wx):
                    rc["地支生"] = rc.get("地支生", 0) + 1
        return rc

    for ys in yong_shen_chars:
        if ys not in bazi_chars:
            continue

        baseline = _count_rels(ys, base_gans, base_zhis)
        active = _count_rels(ys, active_gans, active_zhis)

        # 增量：active 多出来的关系类型数 + 同类型多出来的次数
        delta_types = set(active.keys()) - set(baseline.keys())
        delta_count = 0
        for k, v in active.items():
            delta_count += max(0, v - baseline.get(k, 0))

        # 当前关系类型分类
        n_distinct = len([r for r in active if active[r] >= 1])
        has_real_sheng = any(r in active for r in ("天干生", "地支生"))
        has_real_ke = any(r in active for r in ("天干克", "地支克", "冲", "穿", "刑"))
        has_he = any(r in active for r in ("六合", "半合", "合"))

        # 倒象 = 多种条件之一：
        # 条件 A：增量 ≥ 2 种新关系类型 + 生克合三态齐 + 累计 ≥ 4 种（重大矛盾）
        # 条件 B：增量包含凶煞类型 (冲/穿/刑/克) + 累计 ≥ 4 种 (凶煞引动)
        # 条件 C：增量次数 ≥ 4 (兜底——多重打击)
        delta_has_xiong = bool(
            delta_types & {"冲", "穿", "刑", "天干克", "地支克"}
        )
        cond_A = (
            len(delta_types) >= 2
            and has_real_sheng and has_real_ke and has_he
            and n_distinct >= 4
        )
        cond_B = delta_has_xiong and n_distinct >= 4
        cond_C = delta_count >= 4

        is_dao = cond_A or cond_B or cond_C

        if is_dao:
            reason_tag = "A.三态矛盾" if cond_A else ("B.凶煞引动" if cond_B else "C.多重打击")
            explanations.append(
                f"用神{ys}: 大运/流年新增{len(delta_types)}种新类型({','.join(sorted(delta_types)) or '无'})"
                f", 累计{n_distinct}种, 增量次数{delta_count} → 倒象凶应 [{reason_tag}]"
            )
            is_xiong = True
            matched.append(ys)

    triggered = bool(matched)
    return TriggerEvent(
        trigger_type="倒象成立",
        triggered=triggered,
        strength=0.95 if triggered else 0.0,
        target_chars=list(dict.fromkeys(matched)),
        explanation="; ".join(explanations) if explanations else "无倒象",
        is_xiong=is_xiong,
    )


# ============================================================
# 主入口：6 触发并行检测
# ============================================================


def detect_all_triggers(
    parsed: ParsedInput,
    year: int,
    primary_keys: list[str],
    yong_shen_chars: Optional[list[str]] = None,
) -> list[TriggerEvent]:
    """运行 6 大触发，返回 list[TriggerEvent]（含未触发的）。"""
    if yong_shen_chars is None:
        yong_shen_chars = primary_keys
    return [
        detect_benzi_dao(parsed, year, primary_keys),
        detect_fuyin(parsed, year),
        detect_hechong(parsed, year, primary_keys),
        detect_muku(parsed, year, primary_keys),
        detect_canggan_tou(parsed, year, primary_keys),
        detect_daoxiang(parsed, year, yong_shen_chars),
    ]


# ============================================================
# 主触发挑选（按 04 § 5.2 优先级）
# ============================================================
#
# 优先级（强信号优先）：
#   1. 倒象成立 (is_xiong)        ★ 最高（凶应必报）
#   2. 墓库开闭                    ★★（财官库开 = 大事）
#   3. 合冲引动 + 涉及主位          ★（妻宫被合 / 冲）
#   4. 藏干透出                    ★
#   5. 本字到                      ★
#   6. 伏吟引动                    ★

PRIMARY_PRIORITY = (
    "倒象成立",
    "墓库开闭",
    "合冲引动",
    "藏干透出",
    "本字到",
    "伏吟引动",
)


def pick_primary_trigger(
    triggers: list[TriggerEvent], domain: str = ""
) -> Optional[TriggerEvent]:
    """从触发列表中挑出主触发（按 PRIMARY_PRIORITY 优先级）。"""
    triggered = [t for t in triggers if t.triggered]
    if not triggered:
        return None
    # 按优先级 + 强度排序
    rank = {name: i for i, name in enumerate(PRIMARY_PRIORITY)}
    triggered.sort(key=lambda t: (rank.get(t.trigger_type, 99), -t.strength))
    return triggered[0]


# ============================================================
# smoke
# ============================================================


def _smoke() -> None:
    from engine.predicates.types import Bazi, Pillar, Dayun, ParsedInput
    bz = Bazi.parse("庚申", "戊寅", "壬子", "辛丑")
    dayuns = [
        Dayun(Pillar.parse("庚辰"), 18, 28, 1998, 2008),
        Dayun(Pillar.parse("辛巳"), 28, 38, 2008, 2018),
        Dayun(Pillar.parse("壬午"), 38, 48, 2018, 2028),
    ]
    pi = ParsedInput(gender="男", birth_year=1980, bazi=bz, dayun_list=dayuns)

    # 婚姻关键字（粗判）：丙丁巳午 + 子（妻宫）
    keys = ["丙", "丁", "巳", "午", "子"]
    yong = ["丙", "子"]

    # 2005 乙酉
    triggers = detect_all_triggers(pi, 2005, keys, yong)
    by_type = {t.trigger_type: t for t in triggers}

    # 合冲引动应触发（乙合庚、辰酉合大运、酉与申隔位）
    assert by_type["合冲引动"].triggered, by_type["合冲引动"].explanation

    # 2026 丙午
    triggers = detect_all_triggers(pi, 2026, keys, yong)
    by_type = {t.trigger_type: t for t in triggers}
    # 本字到（午）
    assert by_type["本字到"].triggered
    assert "午" in by_type["本字到"].target_chars
    # 合冲引动（午冲子）
    assert by_type["合冲引动"].triggered

    # 倒象（用神子被多重打击：壬午运 + 丙午年）
    # 子 受冲（午）多次，但需要 ≥3 种不同关系
    # 实际原局：申子半合（生），子丑合（合），大运午冲，流年午冲
    # 关系类型 = {半合, 六合, 冲} ≥ 3 → 倒象成立
    assert by_type["倒象成立"].triggered, by_type["倒象成立"].explanation

    # 主触发：倒象优先
    primary = pick_primary_trigger(triggers, "婚姻")
    assert primary is not None
    assert primary.trigger_type == "倒象成立"

    # 2013 癸巳
    triggers = detect_all_triggers(pi, 2013, keys, yong)
    by_type = {t.trigger_type: t for t in triggers}
    # 本字到（巳）
    assert by_type["本字到"].triggered
    # 大运辛巳 + 流年癸巳 → 大运伏吟流年（不是原局柱伏吟）
    # 流年柱 != 原局任一柱 → 伏吟不触发
    # 本字到 + 合冲引动可能触发（巳与申合制）

    print("yingqi.chufa smoke OK")


if __name__ == "__main__":
    _smoke()
