"""engine/energy/evaluator.py · v1.2 D1 段派 · 能量评估主入口

主入口：``evaluate_energy(parsed) -> EnergyFindings``

编排子模块：tiyong → shidang → zuogong → zeishen → 富贵层级折算
计算 layer_count、wealth_ceiling、has_guoheqiaoqiao、muxing_qufa 等核心字段。

依赖：
- engine.predicates.* (types/ganzhi/wuxing/relations/strength)
- engine.energy.types (EnergyFindings 等)
- engine.energy.tiyong
- engine.energy.shidang
- engine.energy.zuogong
- engine.energy.zeishen
"""
from __future__ import annotations

from typing import Any, Optional, Union

from engine.energy.shidang import evaluate_shidang
from engine.energy.tiyong import (
    determine_muxing_qufa,
    evaluate_tiyong,
)
from engine.energy.types import (
    Confidence,
    EnergyFindings,
    Evidence,
    Magnitude,
    MuxingQufa,
    OrdinalLevel,
    School,
    ShiDang,
    TiyongStructure,
    WealthCeiling,
    ZeishenBushen,
    ZuogongPath,
)
from engine.energy.zeishen import evaluate_zeishen
from engine.energy.zuogong import (
    calc_layer_count,
    detect_guoheqiaoqiao,
    evaluate_zuogong,
)
from engine.predicates.types import (
    Bazi,
    Dayun,
    Gan,
    GanZhi,
    ParsedInput,
    Wuxing,
    adapt_bazi,
    adapt_dayun,
    adapt_parsed,
)
from engine.predicates.strength import calc_gan_strength, calc_wuxing_strength
from engine.predicates.wuxing import wuxing_relation


# ============================================================
# 富贵层级折算（M1-D-173 + §7 L0-L5）
# ============================================================

# 15 档 wealth_ceiling 顺序（巨富→贫困）
_WEALTH_LADDER: list[WealthCeiling] = [
    "巨富级·上", "巨富级·中", "巨富级·下",
    "大富级·上", "大富级·中", "大富级·下",
    "中富级·上", "中富级·中", "中富级·下",
    "小富级·上", "小富级·中", "小富级·下",
    "贫困级·上", "贫困级·中", "贫困级·下",
]


def _derive_wealth_ceiling(
    layer_count: int,
    body_strength: float,
    has_guoheqiaoqiao: bool,
    has_strong_yong: bool,
    has_food_money_chain: bool = False,
) -> WealthCeiling:
    """段派富贵层级折算。

    M1-D-173 基线对照表：
        layer 0 = 平庸（贫困级）
        layer 1 = 百万级（小富级）→ 但若身强+食生财稳定，可达 中富级·下
        layer 2 = 千万级（中富级）
        layer 3 = 亿级（大富级）
        layer 4 = 百亿级（巨富级）

    层级内分 上/中/下 三档，调整因素：
        - 体强弱：体强 → 上档；体中 → 中档；体弱 → 下档
        - 用神是否旺：旺用 +0.5 档；弱用 -0.5 档
        - 过河拆桥结构：+1 档
        - layer=1 + 身强 + 食生财 = 上调到中富级·下（M1-D-049 经理命）
    """
    # 起点：layer → 5 个 band
    base_band_idx = {
        0: 4,  # 贫困级
        1: 3,  # 小富级
        2: 2,  # 中富级
        3: 1,  # 大富级
        4: 0,  # 巨富级
    }[layer_count]

    # M1-D-049 内食神格 + 财生官 = 企业经理：身强 + 食生财稳定 = 中富候选
    if layer_count == 1 and body_strength >= 0.85 and has_food_money_chain:
        base_band_idx = 2  # 中富级
        sub = 2  # 下
    else:
        # 三档内位置：0=上 / 1=中 / 2=下
        if body_strength >= 0.85:
            sub = 0  # 上
        elif body_strength >= 0.55:
            sub = 1  # 中
        else:
            sub = 2  # 下

    # 用神旺 → 提一档
    if has_strong_yong:
        if sub > 0:
            sub -= 1
        elif base_band_idx > 0:
            base_band_idx -= 1
            sub = 2

    # 过河拆桥 +1 档
    if has_guoheqiaoqiao:
        if sub > 0:
            sub -= 1
        elif base_band_idx > 0:
            base_band_idx -= 1
            sub = 2

    idx = base_band_idx * 3 + sub
    idx = max(0, min(idx, len(_WEALTH_LADDER) - 1))
    return _WEALTH_LADDER[idx]


# ============================================================
# energy_level（5 级序数 + 浮点）
# ============================================================

def _derive_energy_level(layer_count: int, body_strength: float) -> Magnitude:
    """整体能量级别（5 级）。"""
    # 0-4 层映射到 0/0.25/0.50/0.75/1.0 base
    base = layer_count / 4.0
    # 体强弱微调（±0.10）
    body_adj = (body_strength - 0.5) * 0.20
    score = max(0.0, min(1.0, base + body_adj))
    if score >= 0.85:
        ord_label: OrdinalLevel = "极强"
    elif score >= 0.65:
        ord_label = "强"
    elif score >= 0.45:
        ord_label = "中"
    elif score >= 0.25:
        ord_label = "弱"
    else:
        ord_label = "无"
    return Magnitude(ordinal=ord_label, score=round(score, 3))


# ============================================================
# Confidence 聚合（06-confidence § 三 简化版）
# ============================================================

# 06-confidence: posterior → ★ 区间
def _posterior_to_star(p: float) -> int:
    if p < 0.40:
        return 1
    if p < 0.55:
        return 2
    if p < 0.70:
        return 3
    if p < 0.85:
        return 4
    return 5


def _aggregate_confidence(evidences: list[Evidence]) -> Confidence:
    """简化版多规律联立聚合（06 § 三）。"""
    if not evidences:
        return Confidence(star=2, percent=0.50, posterior=0.50,
                          variance=0.083, sample_n=0)

    # 取最强为 base
    sorted_ev = sorted(evidences, key=lambda e: -e.weight)
    base = sorted_ev[0].weight
    margin = sum(max(0, e.weight - 0.5) * 0.15 for e in sorted_ev[1:])

    posterior = min(0.95, base + margin)
    return Confidence(
        star=_posterior_to_star(posterior),
        percent=round(posterior, 3),
        posterior=round(posterior, 3),
        variance=0.05,
        sample_n=len(evidences),
    )


# ============================================================
# 主入口
# ============================================================

def evaluate_energy(parsed: Union[ParsedInput, Any]) -> EnergyFindings:
    """段派 D1 能量评估主入口。

    输入：ParsedInput（本地或 preflight 适配后）
    输出：EnergyFindings
    """
    # 适配
    if not isinstance(parsed, ParsedInput):
        parsed = adapt_parsed(parsed)

    bazi = parsed.bazi
    dayun = parsed.dayun

    # 1. 体用判别
    tiyong = evaluate_tiyong(bazi)
    muxing_qufa: MuxingQufa = determine_muxing_qufa(bazi)  # type: ignore[assignment]

    # 2. 势 + 党
    shidang = evaluate_shidang(bazi, tiyong)

    # 3. 做功扫描
    zuogong_paths = evaluate_zuogong(bazi, tiyong)

    # 4. 贼神捕神
    zeishen = evaluate_zeishen(bazi, dayun)

    # 5. 计算 layer_count + 富贵层级
    layer_count = calc_layer_count(zuogong_paths, bazi)
    has_guohe = detect_guoheqiaoqiao(zuogong_paths)

    # 体强弱 = 日干强度 + 比劫/印总势力
    day_master = bazi.day_master
    body_strength = calc_gan_strength(day_master, bazi)

    # 用神是否旺：5 行中 财/官杀 任一 ≥ 0.30
    shi = calc_wuxing_strength(bazi)
    from engine.predicates.ganzhi import gan_to_wuxing
    day_wx = gan_to_wuxing(day_master)
    has_strong_yong = False
    for wx, val in shi.items():
        if val >= 0.30:
            rel = wuxing_relation(day_wx, wx)
            if rel in ("克我", "我克"):
                has_strong_yong = True
                break

    wealth_ceiling = _derive_wealth_ceiling(
        layer_count=layer_count,
        body_strength=body_strength,
        has_guoheqiaoqiao=has_guohe,
        has_strong_yong=has_strong_yong,
        has_food_money_chain=any(
            p.type == "生泄" and "[食伤生财]" in p.description
            for p in zuogong_paths if p.layer_count >= 1
        ),
    )

    # 6. 整体能量级别
    energy_level = _derive_energy_level(layer_count, body_strength)

    # 7. 收集 evidence + 计算 confidence
    evidence: list[Evidence] = []
    # 体用证据
    evidence.append(Evidence(
        rule_id="M1-D-005..008",
        school="段",
        description=f"体用判定：体 {len(tiyong.body)} 字，用 {len(tiyong.purpose)} 字",
        weight=0.75,
    ))
    # 势/党证据
    if shidang.dang:
        evidence.append(Evidence(
            rule_id="M1-D-122",
            school="段",
            description=f"势/党：{shidang.dang[0][1]}",
            weight=0.70,
        ))
    # 做功证据：每条独立 path 一条
    for p in zuogong_paths[:5]:  # 最多 5 条
        if p.layer_count >= 1:
            evidence.append(Evidence(
                rule_id={
                    "制": "M1-D-009", "化": "M1-D-010", "生泄": "M1-D-011",
                    "合": "M1-D-012", "墓": "M1-D-013", "复合": "M1-D-014",
                }.get(p.type, "M1-D-009"),
                school="段",
                description=f"{p.type}：{p.description}",
                weight=p.strength.score,
            ))
    # 贼神证据
    if zeishen.zei_shen:
        evidence.append(Evidence(
            rule_id="M1-D-015",
            school="段",
            description=f"贼神：{','.join(zeishen.zei_shen)}",
            weight=0.65,
        ))
    # 母星证据
    evidence.append(Evidence(
        rule_id="M1-D-199",
        school="段",
        description=f"母星取法（段派独门）：{muxing_qufa}（决策 J）",
        weight=0.80,
    ))
    # 过河拆桥
    if has_guohe:
        evidence.append(Evidence(
            rule_id="M1-D-171",
            school="段",
            description="过河拆桥结构候选 = 食生财 + 财生官 三连环",
            weight=0.75,
        ))

    confidence = _aggregate_confidence(evidence)

    # 8. 组装 EnergyFindings
    findings = EnergyFindings(
        energy_level=energy_level,
        layer_count=layer_count,
        zuogong_paths=zuogong_paths,
        tiyong=tiyong,
        shidang=shidang,
        zeishen=zeishen,
        wealth_ceiling=wealth_ceiling,
        has_guoheqiaoqiao=has_guohe,
        muxing_qufa=muxing_qufa,
        confidence=confidence,
        evidence=evidence,
        case_id=parsed.case_id,
        debug_info={
            "body_strength": round(body_strength, 3),
            "has_strong_yong": has_strong_yong,
            "shidang_summary": shidang.description,
        },
    )
    return findings


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from engine.predicates.types import (
        Bazi, Dayun, DayunStep, GanZhi, _default_canggan_for,
    )

    cases = {
        "C-2026-001": ("庚", "申", "戊", "寅", "壬", "子", "辛", "丑"),
        "C-2026-002": ("壬", "戌", "庚", "戌", "戊", "辰", "丙", "辰"),
        "C-2026-014": ("丙", "戌", "庚", "子", "乙", "亥", "辛", "巳"),
        "C-2026-011": ("乙", "丑", "乙", "酉", "丁", "丑", "癸", "卯"),
        "C-2026-012": ("壬", "戌", "癸", "丑", "丙", "申", "壬", "辰"),
    }
    for cid, parts in cases.items():
        b = Bazi(
            年柱=GanZhi(parts[0], parts[1]),
            月柱=GanZhi(parts[2], parts[3]),
            日柱=GanZhi(parts[4], parts[5]),
            时柱=GanZhi(parts[6], parts[7]),
        )
        b.藏干 = _default_canggan_for(b)
        # 简化大运（仅 8 步占位）
        dy = Dayun(起运岁=5, 起运年=1990, 顺逆="顺", 排布=[
            DayunStep(序号=i + 1, 干支=GanZhi("甲", "子"), 起岁=5 + i * 10,
                      止岁=14 + i * 10, 起讫年=(1990 + i * 10, 2000 + i * 10))
            for i in range(8)
        ])
        parsed = ParsedInput(case_id=cid, bazi=b, dayun=dy)
        ef = evaluate_energy(parsed)
        print(f"\n=== {cid} ===")
        print(f"  layer_count = {ef.layer_count}")
        print(f"  wealth_ceiling = {ef.wealth_ceiling}")
        print(f"  energy_level = {ef.energy_level.ordinal} ({ef.energy_level.score})")
        print(f"  muxing_qufa = {ef.muxing_qufa}")
        print(f"  has_guoheqiaoqiao = {ef.has_guoheqiaoqiao}")
        print(f"  body_strength = {ef.debug_info['body_strength']}")
        print(f"  ★{ef.confidence.star} ({ef.confidence.percent:.0%})")
        print(f"  evidence chain ({len(ef.evidence)}):")
        for e in ef.evidence[:5]:
            print(f"    - [{e.school}] {e.rule_id}: {e.description[:60]}")

    print("\n[OK] evaluate_energy smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
