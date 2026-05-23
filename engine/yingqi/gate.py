"""engine.yingqi.gate · gate_yingqi 主入口

按任务说明 §阶段 3 实现。修复 G2（C-2026-001 婚期偏差 8 年）的关键：
check_against_picture 函数会用 picture.marriage_picture.best_window 拒绝
不在最佳窗口内的婚姻应期，把 passed_layers 钳到 ≤ 1。

主流程：
  1. 跑 L1/L2/L3 三层判定 + 6 触发
  2. 上游一致性检查（energy_consistent + picture_consistent）
  3. picture_consistent=False 时强制 passed_layers = min(passed_layers, 1)
  4. 12 道门分类
  5. 计算 confidence + star
"""

from __future__ import annotations

from typing import Optional

from engine.energy.types import EnergyFindings
from engine.picture.types import PictureFindings
from engine.predicates.cycles import liunian_ganzhi
from engine.predicates.types import ParsedInput

from .menshu import classify_into_12_doors
from .threelayer import layer1_check, layer2_check, layer3_check
from .types import GateResult, LayerCheck, TriggerEvent, Door


# ============================================================
# 上游一致性检查
# ============================================================


def check_against_energy(
    domain: str,
    energy: Optional[EnergyFindings],
    candidate_event: str,
) -> tuple[bool, list[str]]:
    """检查事件与 energy 一致。

    若 energy 标记 domain 不具备做功基础（如 marriage_capable=False），
    则结婚 / 升迁 等"成立性事件"不一致。

    凶应（婚变 / 失业 / 重病）则不要求 capable=True。
    """
    if energy is None:
        return True, ["energy 未提供，跳过一致性检查"]

    cap_attr = {
        "婚姻": "marriage_capable",
        "事业": "career_capable",
        "财运": "wealth_capable",
        "健康": "health_capable",
        "学业": "education_capable",
    }.get(domain)

    if cap_attr is None:
        return True, [f"domain={domain} 无能力字段映射"]

    cap = getattr(energy, cap_attr, True)

    # 简化：成立性事件（结婚 / 升迁 / 高考通过 等）需要 capable=True
    # 凶事件（婚变 / 重病 / 牢灾）不需要
    success_keywords = ("结婚", "升迁", "升职", "上学", "高考", "考上", "录取",
                        "得财", "怀孕", "生子", "晋升", "提拔", "成立")
    is_success = any(k in candidate_event for k in success_keywords)
    if is_success and not cap:
        return False, [f"energy 标记 {domain} 无做功能力 → 成立性事件不一致"]
    return True, [f"energy 与事件 '{candidate_event}' 一致 (cap={cap})"]


def check_against_picture(
    domain: str,
    picture: Optional[PictureFindings],
    parsed: ParsedInput,
    year: int,
    candidate_event: str,
) -> tuple[bool, list[str]]:
    """检查事件年份与 picture 给出的画面窗口一致。

    本函数是修复 G2 的关键：
    - 婚姻：picture.marriage_picture.best_window = (lo, hi)，
            若 candidate_event 是结婚类且 age 不在 [lo, hi] 内 → 不一致
    - 学业：picture.education_picture.key_year_window
    - 事业：rising_windows 任一不命中算"次佳"，但仍可一致
    """
    if picture is None:
        return True, ["picture 未提供，跳过一致性检查"]

    age = parsed.age_at_year(year)

    # 婚姻
    if domain == "婚姻":
        marry_keywords = ("结婚", "成婚", "嫁", "娶", "领证", "成家", "初婚")
        is_marry = any(k in candidate_event for k in marry_keywords)
        if is_marry:
            mp = picture.marriage_picture
            lo, hi = mp.best_window
            sec = mp.secondary_window
            if lo <= age <= hi:
                return True, [f"年龄 {age} ∈ 最佳婚窗 [{lo},{hi}]"]
            if sec is not None and sec[0] <= age <= sec[1]:
                return True, [f"年龄 {age} ∈ 次佳窗口 {sec}"]
            # 不在任何窗口
            return False, [
                f"年龄 {age} 不在最佳婚窗 [{lo},{hi}]"
                + (f" 也不在次佳 {sec}" if sec else "")
                + " → 婚姻 picture 不一致"
            ]
        return True, [f"事件 '{candidate_event}' 非结婚类，跳过 picture 检查"]

    # 学业（高考类）
    if domain == "学业":
        edu_keywords = ("高考", "上学", "考上", "录取", "考研", "毕业")
        is_edu = any(k in candidate_event for k in edu_keywords)
        if is_edu:
            ep = picture.education_picture
            if ep.key_year_window is None:
                return True, ["education_picture 无窗口，跳过"]
            lo, hi = ep.key_year_window
            if lo <= age <= hi:
                return True, [f"年龄 {age} ∈ 学业关键窗口 [{lo},{hi}]"]
            return False, [
                f"年龄 {age} 不在学业关键窗口 [{lo},{hi}] → 学业 picture 不一致"
            ]

    # 事业（rising_windows）
    if domain == "事业":
        rises = picture.career_picture.rising_windows
        if not rises:
            return True, ["career_picture 无 rising_windows，跳过"]
        for lo, hi in rises:
            if lo <= age <= hi:
                return True, [f"年龄 {age} ∈ 事业上升窗口 [{lo},{hi}]"]
        return True, [f"年龄 {age} 不在任何事业上升窗口（次佳）"]  # 事业不强制

    return True, [f"domain={domain} 无 picture 强约束"]


# ============================================================
# 置信度 + 星级
# ============================================================
# 按 06 § 四 应期 GateResult 专用置信度公式（契约未交付，本实现即作为参考）


def compute_yingqi_confidence(
    passed_layers: int,
    triggers: list[TriggerEvent],
    primary_trigger: Optional[TriggerEvent],
    is_xiong: bool,
    energy_consistent: bool,
    picture_consistent: bool,
) -> tuple[float, int]:
    """应期专用置信度。

    基础分：passed_layers × 0.25 (3 层 = 0.75)
    + 主触发强度 × 0.20
    + 上游一致性 (各 0.05)
    + 倒象凶应保底 + 0.10（必应）

    返回 (confidence ∈ [0,1], star ∈ [1,5])
    """
    base = passed_layers * 0.25
    bonus_trigger = 0.0
    if primary_trigger is not None:
        bonus_trigger = primary_trigger.strength * 0.20
    bonus_consistent = 0.0
    if energy_consistent:
        bonus_consistent += 0.05
    if picture_consistent:
        bonus_consistent += 0.05
    bonus_xiong = 0.10 if is_xiong else 0.0
    # 三层未齐 → 上限 0.85（不可铁断）
    cap = 0.85 if passed_layers < 3 else 1.0
    conf = min(base + bonus_trigger + bonus_consistent + bonus_xiong, cap)
    conf = max(conf, 0.0)

    # 星级映射（按 confidence.yaml）
    pct = conf * 100.0
    if pct >= 90:
        star = 5
    elif pct >= 80:
        star = 4
    elif pct >= 65:
        star = 3
    elif pct >= 50:
        star = 2
    else:
        star = 1

    # 强约束：passed_layers < 3 时，星级最高 4
    if passed_layers < 3:
        star = min(star, 4)
    if passed_layers <= 1:
        star = min(star, 3)
    if passed_layers == 0:
        star = min(star, 2)

    return conf, star


# ============================================================
# 主入口
# ============================================================


def gate_yingqi(
    year: int,
    candidate_event: str,
    domain: str,
    energy: Optional[EnergyFindings],
    picture: Optional[PictureFindings],
    parsed: ParsedInput,
    sub_domain: Optional[str] = None,
) -> GateResult:
    """应期三层门主入口。

    Args:
        year: 公历年
        candidate_event: 候选事件描述（如 '结婚' / '升正科' / '高考考上'）
        domain: 领域 ('婚姻' / '事业' / '财运' / '健康' / '学业' / '六亲' / '其他')
        energy: D1 段派输出（可为 None，表示上游未跑）
        picture: D2 杨派输出（可为 None）
        parsed: 命主解析输入
        sub_domain: 六亲细分（'父' / '母' / '兄弟' / '子女' / '配偶'）

    Returns:
        GateResult 含 passed_layers / triggers / door / confidence / star。
    """
    # 1) 三层判定
    l1 = layer1_check(domain, parsed, energy, sub_domain)
    l2 = layer2_check(year, domain, parsed, energy, sub_domain)
    l3, triggers, primary_t = layer3_check(
        year, domain, parsed, energy, picture, sub_domain
    )
    passed = sum([1 if x.passed else 0 for x in (l1, l2, l3)])

    # 2) 上游一致性
    e_ok, e_reasons = check_against_energy(domain, energy, candidate_event)
    p_ok, p_reasons = check_against_picture(
        domain, picture, parsed, year, candidate_event
    )

    consistency_reasons: list[str] = []
    consistency_reasons.extend([f"[energy] {r}" for r in e_reasons])
    consistency_reasons.extend([f"[picture] {r}" for r in p_reasons])

    # 3) 上游硬约束（修复 G2 的关键！）
    # picture 不一致 → 钳到 ≤ 1（保留 L1，但 L2/L3 视为不可信）
    if not p_ok:
        passed = min(passed, 1)
        consistency_reasons.insert(0, "[硬约束] picture_consistent=False → passed_layers ≤ 1")
    # energy 不一致 → 钳到 ≤ 2
    if not e_ok:
        passed = min(passed, 2)
        consistency_reasons.insert(0, "[硬约束] energy_consistent=False → passed_layers ≤ 2")

    # 4) 12 道门
    door = classify_into_12_doors(parsed, domain, triggers, energy, picture)

    # 5) 倒象 / 凶应
    is_xiong = bool(primary_t and primary_t.is_xiong)

    # 6) 置信度 + 星级
    conf, star = compute_yingqi_confidence(
        passed_layers=passed,
        triggers=triggers,
        primary_trigger=primary_t,
        is_xiong=is_xiong,
        energy_consistent=e_ok,
        picture_consistent=p_ok,
    )

    # 7) 摘要
    ln_g, ln_z = liunian_ganzhi(year)
    age = parsed.age_at_year(year)
    summary_parts = [
        f"{year}年({ln_g}{ln_z}, {age}岁) · {domain} · '{candidate_event}'",
        f"三层: L1={'✓' if l1.passed else '✗'} L2={'✓' if l2.passed else '✗'} L3={'✓' if l3.passed else '✗'} (passed={passed}/3)",
        f"主触发: {primary_t.trigger_type if primary_t else '无'}"
        + (f"({primary_t.strength:.2f})" if primary_t else ""),
        f"道门: {door.door_type if door else '无'}",
        f"上游: energy={'✓' if e_ok else '✗'} picture={'✓' if p_ok else '✗'}",
        f"置信度: {conf:.2%} ★{star}",
    ]
    if is_xiong:
        summary_parts.append("⚠️ 倒象凶应（必凶）")
    summary = " | ".join(summary_parts)

    # 8) 上游 hash（追溯）
    e_hash = energy.upstream_hash if energy is not None else ""
    p_hash = picture.upstream_hash if picture is not None else ""

    return GateResult(
        year=year,
        candidate_event=candidate_event,
        domain=domain,
        layer1=l1, layer2=l2, layer3=l3,
        passed_layers=passed,
        triggers=triggers,
        primary_trigger=primary_t,
        door=door,
        energy_consistent=e_ok,
        picture_consistent=p_ok,
        consistency_reasons=consistency_reasons,
        confidence=conf,
        star=star,
        is_xiong=is_xiong,
        upstream_energy_hash=e_hash,
        upstream_picture_hash=p_hash,
        rule_ids=[
            "M3-R-003",  # 三层叠加
            "M3-R-031",  # 6 触发应期
            "M3-R-022",  # 禄刃不可坏
            "M3-R-052",  # 倒象
            "M3-R-119",  # 大运流年应期三层法
        ],
        summary=summary,
    )


# ============================================================
# smoke
# ============================================================


def _smoke() -> None:
    from engine.predicates.types import Bazi, Pillar, Dayun, ParsedInput
    from engine.picture.types import PictureFindings, MarriagePicture

    bz = Bazi.parse("庚申", "戊寅", "壬子", "辛丑")
    dayuns = [
        Dayun(Pillar.parse("己卯"), 8, 18, 1988, 1998),
        Dayun(Pillar.parse("庚辰"), 18, 28, 1998, 2008),
        Dayun(Pillar.parse("辛巳"), 28, 38, 2008, 2018),
        Dayun(Pillar.parse("壬午"), 38, 48, 2018, 2028),
    ]
    pi = ParsedInput(gender="男", birth_year=1980, bazi=bz, dayun_list=dayuns)

    # 杨派 picture：最佳婚窗 [23, 27]
    mp = MarriagePicture(best_window=(23, 27), expected_status="稳定")
    pic = PictureFindings(bazi_str="庚申戊寅壬子辛丑", marriage_picture=mp)

    # G2 圣杯测试
    r2005 = gate_yingqi(2005, "结婚", "婚姻", None, pic, pi)
    print(f"\n[2005] {r2005.summary}")
    assert r2005.passed_layers == 3
    assert r2005.star >= 4

    r2013 = gate_yingqi(2013, "结婚", "婚姻", None, pic, pi)
    print(f"[2013] {r2013.summary}")
    assert r2013.passed_layers <= 1, f"2013 passed={r2013.passed_layers} (期望 ≤1)"
    assert r2013.star <= 3

    print("\nyingqi.gate smoke OK")


if __name__ == "__main__":
    _smoke()
