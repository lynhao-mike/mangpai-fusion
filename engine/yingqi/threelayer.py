"""engine/yingqi/threelayer.py · v1.2 D3 任派 · L1/L2/L3 三层判定

严格按 04-gate-protocol.md § 三/四/五 实现。

3 层判定的本质：
    L1 原局有       —— 命中本来要发生什么（关键字在原局含藏干存在）
    L2 大运到位     —— 当前年份所在大运（含过渡期 ±1 年）提供必需触发字
    L3 流年引爆     —— 流年对原局/大运的关键字构成 6 触发之一

L3 的 6 触发引擎在 chufa.py 实现。本模块只做"是否引爆"判定。

API（与 04 契约一致）:
    layer1_check(domain, parsed, energy) -> LayerCheck
    layer2_check(year, domain, energy, parsed) -> LayerCheck
    layer3_check(year, domain, energy, picture, parsed)
        -> tuple[LayerCheck, list[TriggerEvent], Optional[TriggerEvent]]

作者：Track-C
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import EnergyFindings
from engine.picture.types import PictureFindings
from engine.predicates.cycles import (
    get_adjacent_dayun,
    get_dayun_at_year,
    is_in_dayun_transition,
    liunian_ganzhi,
)
from engine.predicates.relations import (
    zhi_chong,
    zhi_chuan,
    zhi_liuhe,
    zhi_sanhe,
    zhi_sanhui,
    zhi_xing,
)
from engine.predicates.tou_cang import is_canggan
from engine.predicates.types import (
    Bazi,
    Dayun,
    DayunStep,
    GanZhi,
    ParsedInput,
)

from engine.yingqi.keys import (
    chars_in_yuanju,
    get_primary_keys,
    get_required_dayun_chars,
    get_secondary_keys,
    infer_sub_domain,
)
from engine.yingqi.types import LayerCheck, TriggerEvent


# ============================================================
# L1 · 原局有
# ============================================================

def layer1_check(
    domain: str,
    parsed: ParsedInput,
    energy: Optional[EnergyFindings] = None,
    *,
    sub_domain: Optional[str] = None,
) -> LayerCheck:
    """L1 原局有：domain 关键字是否在原局四柱（含藏干）存在。

    判定路径：
        1. primary_keys 命中 → passed=True
        2. 退而求其次 secondary_keys 命中 → passed=True 但标 used_secondary_keys
        3. 否则 passed=False
        特殊豁免（04 § 9.1 婚姻无星借宫）：婚姻 domain 配偶星完全不见原局，
        仍 passed=True（rationale 标"无星借宫"，依赖 D2 marriage_picture）。
    """
    bazi = parsed.bazi
    gender = (parsed.birth or {}).get("性别")

    primary = get_primary_keys(
        domain, bazi, energy, gender=gender, sub_domain=sub_domain,
    )
    found_primary = chars_in_yuanju(primary, bazi)

    if found_primary:
        return LayerCheck(
            layer="L1_原局有",
            passed=True,
            evidence_chars=found_primary[:6],  # 最多展示 6 个
            rationale=(
                f"原局存在 {domain}{'-' + sub_domain if sub_domain else ''} "
                f"关键字: {','.join(found_primary[:6])}"
            ),
        )

    # secondary
    secondary = get_secondary_keys(
        domain, bazi, energy, gender=gender, sub_domain=sub_domain,
    )
    found_secondary = chars_in_yuanju(secondary, bazi)
    if found_secondary:
        return LayerCheck(
            layer="L1_原局有",
            passed=True,
            evidence_chars=found_secondary[:4],
            rationale=(
                f"原局主关键字未现，但次关键字 {','.join(found_secondary[:4])} "
                f"提供间接背景"
            ),
            used_secondary_keys=True,
        )

    # 婚姻"无星借宫"豁免（04 § 9.1）
    if domain == "婚姻":
        return LayerCheck(
            layer="L1_原局有",
            passed=True,
            evidence_chars=[bazi.日柱.zhi],
            rationale=(
                "婚姻无星借宫：配偶星不见原局，依赖 D2 marriage_picture "
                "提供配偶画像（杨派『无官借伤、无财借食』）"
            ),
            used_secondary_keys=True,
        )

    return LayerCheck(
        layer="L1_原局有",
        passed=False,
        evidence_chars=[],
        rationale=f"原局未见 {domain} 关键字（主+次）",
    )


# ============================================================
# L2 · 大运到位
# ============================================================

def layer2_check(
    year: int,
    domain: str,
    energy: Optional[EnergyFindings],
    parsed: ParsedInput,
    *,
    sub_domain: Optional[str] = None,
) -> LayerCheck:
    """L2 大运到位：当前年份所在大运（含过渡期）提供 domain 必需字。

    判定路径（04 § 4.2）：
        a) 大运的干 / 支本字 ∈ required_chars
        b) 大运的支与原局某 required_char 形成合 / 冲 / 半合 / 刑
        c) 大运的支藏干 ∈ required_chars
        d) 过渡期 ±1 年内相邻大运的字命中（标 used_transition）
    """
    bazi = parsed.bazi
    birth_year = int((parsed.birth or {}).get("公历年") or
                     parsed.dayun.起运年 - int(parsed.dayun.起运岁))

    try:
        cur_step = get_dayun_at_year(parsed.dayun, birth_year, year)
    except ValueError as e:
        return LayerCheck(
            layer="L2_大运到位",
            passed=False,
            evidence_chars=[],
            rationale=f"年份 {year} 在大运起运前: {e}",
        )

    needed = get_required_dayun_chars(
        domain, energy, parsed, sub_domain=sub_domain,
    )

    found: list[str] = []
    notes: list[str] = []

    # a) 本字
    cur_gz = cur_step.干支
    if cur_gz.gan in needed:
        found.append(cur_gz.gan)
        notes.append(f"大运{cur_gz}的天干{cur_gz.gan}∈ 必需字")
    if cur_gz.zhi in needed:
        found.append(cur_gz.zhi)
        notes.append(f"大运{cur_gz}的地支{cur_gz.zhi}∈ 必需字")

    # b) 大运支与原局支的合冲
    for name, zhi in bazi.all_zhis():
        if zhi not in needed:
            continue
        if zhi_chong(cur_gz.zhi, zhi):
            found.append(zhi)
            notes.append(f"大运{cur_gz.zhi}冲原局{name}{zhi}")
        elif zhi_liuhe(cur_gz.zhi, zhi) is not None:
            found.append(zhi)
            notes.append(f"大运{cur_gz.zhi}六合原局{name}{zhi}")
        elif zhi_sanhe([cur_gz.zhi, zhi]) is not None:
            found.append(zhi)
            notes.append(f"大运{cur_gz.zhi}与原局{name}{zhi}半三合")
        elif zhi_xing(cur_gz.zhi, zhi) is not None:
            found.append(zhi)
            notes.append(f"大运{cur_gz.zhi}刑原局{name}{zhi}")

    # c) 大运支藏干
    from engine.predicates.types import ZHI_CANGGAN_TABLE
    cangs_in_dy = [g for g, _, _ in ZHI_CANGGAN_TABLE.get(cur_gz.zhi, [])]
    for cg in cangs_in_dy:
        if cg in needed and cg not in found:
            found.append(cg)
            notes.append(f"大运{cur_gz.zhi}藏 {cg} ∈ 必需字")

    # d) 过渡期相邻大运
    used_transition = False
    if not found and is_in_dayun_transition(year, cur_step, threshold_years=1):
        adj = get_adjacent_dayun(parsed.dayun, cur_step)
        if adj is not None:
            adj_gz = adj.干支
            if adj_gz.gan in needed:
                found.append(adj_gz.gan)
                used_transition = True
                notes.append(
                    f"过渡期：相邻大运{adj_gz}的天干{adj_gz.gan}∈ 必需字"
                )
            if adj_gz.zhi in needed:
                found.append(adj_gz.zhi)
                used_transition = True
                notes.append(
                    f"过渡期：相邻大运{adj_gz}的地支{adj_gz.zhi}∈ 必需字"
                )

    if found:
        # 去重保序
        seen: set[str] = set()
        deduped: list[str] = []
        for c in found:
            if c not in seen:
                seen.add(c)
                deduped.append(c)
        return LayerCheck(
            layer="L2_大运到位",
            passed=True,
            evidence_chars=deduped[:6],
            rationale=(
                f"大运{cur_gz}{'(过渡期)' if used_transition else ''}: "
                + "; ".join(notes[:4])
            ),
            used_transition=used_transition,
        )

    return LayerCheck(
        layer="L2_大运到位",
        passed=False,
        evidence_chars=[],
        rationale=(
            f"大运{cur_gz}未提供 {domain} 必需字（含过渡期 ±1 年）。"
            f"必需字（前 8 个）: {','.join(needed[:8])}"
        ),
    )


# ============================================================
# L3 · 流年引爆
# ============================================================

def layer3_check(
    year: int,
    domain: str,
    energy: Optional[EnergyFindings],
    picture: Optional[PictureFindings],
    parsed: ParsedInput,
    *,
    sub_domain: Optional[str] = None,
) -> tuple[LayerCheck, list[TriggerEvent], Optional[TriggerEvent]]:
    """L3 流年引爆：调用 chufa.py 的 6 触发引擎。

    返回 (LayerCheck, all_triggers, primary_trigger)。
    主触发挑选按 04 § 5.2 优先级。
    """
    # 延迟 import 避免循环
    from engine.yingqi.chufa import detect_all_triggers, pick_primary_trigger

    bazi = parsed.bazi
    gender = (parsed.birth or {}).get("性别")

    primary_keys = get_primary_keys(
        domain, bazi, energy, gender=gender, sub_domain=sub_domain,
    )
    secondary_keys = get_secondary_keys(
        domain, bazi, energy, gender=gender, sub_domain=sub_domain,
    )
    target_keys = list(dict.fromkeys(primary_keys + secondary_keys))

    # 用神字（用于倒象判定）：用 EnergyFindings.tiyong.purpose 的字
    yong_shen_chars: list[str] = []
    if energy is not None:
        for item in energy.tiyong.purpose:
            yong_shen_chars.append(item.char)
    if not yong_shen_chars:
        # fallback：用 primary_keys 前几个 + 日干
        yong_shen_chars = list(primary_keys[:4]) + [bazi.day_master]

    triggers = detect_all_triggers(parsed, year, target_keys, yong_shen_chars)
    primary = pick_primary_trigger(triggers)

    n_triggered = len(triggers)
    ln = liunian_ganzhi(year)

    if n_triggered > 0:
        evidence_chars: list[str] = []
        seen: set[str] = set()
        for t in triggers:
            for c in t.target_chars:
                if c not in seen:
                    seen.add(c)
                    evidence_chars.append(c)

        rationale_parts = [
            f"流年{ln} 触发 {n_triggered} 个: {[t.type for t in triggers]}"
        ]
        if primary is not None:
            rationale_parts.append(f"主触发={primary.type}: {primary.description[:50]}")

        return (
            LayerCheck(
                layer="L3_流年引爆",
                passed=True,
                evidence_chars=evidence_chars[:8],
                rationale=" | ".join(rationale_parts),
            ),
            triggers,
            primary,
        )

    return (
        LayerCheck(
            layer="L3_流年引爆",
            passed=False,
            evidence_chars=[],
            rationale=f"流年{ln} 未触发任何 6 门",
        ),
        triggers,
        primary,
    )


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from tests.fixtures.cases import load_case
    from engine.energy.evaluator import evaluate_energy
    from engine.picture.matcher import match_picture

    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    energy = evaluate_energy(parsed)
    picture = match_picture(energy, parsed)

    # 1) C-2026-001 婚姻 2005 → L1/L2 应通过
    print("\n=== C-2026-001 婚姻 2005 ===")
    l1 = layer1_check("婚姻", parsed, energy)
    l2 = layer2_check(2005, "婚姻", energy, parsed)
    l3, trigs, primary = layer3_check(2005, "婚姻", energy, picture, parsed)
    print(f"  L1: passed={l1.passed} | {l1.rationale}")
    print(f"  L2: passed={l2.passed} | {l2.rationale}")
    print(f"  L3: passed={l3.passed} | n_triggers={len(trigs)} | primary={primary.type if primary else None}")
    print(f"     L3 rationale: {l3.rationale}")
    assert l1.passed, f"L1 应通过：{l1.rationale}"
    assert l2.passed, f"L2 应通过：{l2.rationale}"
    assert l3.passed, f"L3 应通过：{l3.rationale}"
    print("  → 三层全过 ✓")

    # 2) C-2026-001 婚姻 2013 → L1/L2/L3 应通过（picture 钳制在 gate.py 处理）
    print("\n=== C-2026-001 婚姻 2013（v1.0 错婚期）===")
    l1 = layer1_check("婚姻", parsed, energy)
    l2 = layer2_check(2013, "婚姻", energy, parsed)
    l3, trigs, primary = layer3_check(2013, "婚姻", energy, picture, parsed)
    print(f"  L1: passed={l1.passed}")
    print(f"  L2: passed={l2.passed} | {l2.rationale}")
    print(f"  L3: passed={l3.passed} | n_triggers={len(trigs)}")
    # 2013 三层会过（这是 v1.0 误判的根源）—— 需要 D2 marriage_picture 在 gate.py 把 passed 钳到 ≤1

    # 3) C-2026-001 六亲 母 2020
    print("\n=== C-2026-001 六亲(母) 2020 ===")
    sub = "母"
    l1 = layer1_check("六亲", parsed, energy, sub_domain=sub)
    l2 = layer2_check(2020, "六亲", energy, parsed, sub_domain=sub)
    l3, trigs, primary = layer3_check(2020, "六亲", energy, picture, parsed, sub_domain=sub)
    print(f"  L1: passed={l1.passed} | {l1.rationale}")
    print(f"  L2: passed={l2.passed} | {l2.rationale}")
    print(f"  L3: passed={l3.passed} | primary={primary.type if primary else None}")

    # 4) C-2026-014 学业 2024
    parsed014 = load_case("C-2026-014-乾-丙戌庚子乙亥辛巳")
    energy014 = evaluate_energy(parsed014)
    picture014 = match_picture(energy014, parsed014)
    print("\n=== C-2026-014 学业 2024 ===")
    l1 = layer1_check("学业", parsed014, energy014)
    l2 = layer2_check(2024, "学业", energy014, parsed014)
    l3, trigs, primary = layer3_check(2024, "学业", energy014, picture014, parsed014)
    print(f"  L1: passed={l1.passed} | {l1.rationale}")
    print(f"  L2: passed={l2.passed} | {l2.rationale}")
    print(f"  L3: passed={l3.passed} | n_triggers={len(trigs)}")

    print("\n[OK] threelayer smoke 全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
