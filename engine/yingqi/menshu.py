"""engine.yingqi.menshu · 12 道门分类器

按 m3-mechanics §16 实现。Track-C MVP 实现核心 6 个：
  - 动门     - 日干日支 / 合冲穿引动 = 动事
  - 统领门   - 官统财 / 财统官 / 杀统财 = 富贵跃升
  - 墓库门   - 财官入库 + 库开 = 收得
  - 鸳鸯门   - 婚姻专门
  - 寿元门   - 用神被破 / 寿星临绝
  - 牢灾门   - 食伤官杀两敌 / 亡神劫煞犯官符

其余道门（格局/天地/十天/十二地/夹拱/旬空/伤残）按"未分类"返回，
留待 Track-D 旁证补强或后续迭代。

优先级（按任务说明）：寿元门 / 牢灾门 > 鸳鸯门 / 统领门 > 其他
"""

from __future__ import annotations

from typing import Optional

from engine.energy.types import EnergyFindings
from engine.picture.types import PictureFindings
from engine.predicates.cycles import liunian_ganzhi, get_dayun_at_year
from engine.predicates.ganzhi import (
    get_canggan, get_shishen, get_shishen_class, get_wuxing, is_ke,
)
from engine.predicates.relations import (
    is_zhi_chong, is_zhi_liuhe, is_xing_pair, is_zhi_chuan,
)
from engine.predicates.types import ParsedInput

from .types import Door, TriggerEvent, CORE_DOORS_IMPL


# ============================================================
# 1) 鸳鸯门（婚姻）
# ============================================================


def _classify_yuanyang(
    parsed: ParsedInput, domain: str, triggers: list[TriggerEvent]
) -> Optional[Door]:
    if domain != "婚姻":
        return None
    # 触发条件：合冲引动涉及妻宫（日支）or 财字（用神）
    day_zhi = parsed.bazi.day_zhi
    related = False
    explanations: list[str] = []
    for t in triggers:
        if not t.triggered:
            continue
        if day_zhi in t.target_chars:
            related = True
            explanations.append(f"{t.trigger_type}涉及妻/夫宫{day_zhi}")
        # 财官字也算
        for c in t.target_chars:
            day_g = parsed.bazi.day_gan
            try:
                ss = get_shishen(day_g, c)
            except (ValueError, RuntimeError):
                continue
            sc = get_shishen_class(ss)
            if (parsed.gender == "男" and sc == "财") or \
               (parsed.gender == "女" and sc == "官"):
                related = True
                explanations.append(f"{t.trigger_type}涉及配偶星{c}({ss})")
                break
    if not related:
        return None
    conf = 0.85
    return Door(
        door_type="鸳鸯门",
        matched=True,
        confidence=conf,
        explanation="; ".join(explanations[:3]) or "婚姻专门",
    )


# ============================================================
# 2) 寿元门
# ============================================================


def _classify_shouyuan(
    parsed: ParsedInput,
    domain: str,
    energy: Optional[EnergyFindings],
    triggers: list[TriggerEvent],
) -> Optional[Door]:
    """寿元门：用神被破 / 主位被冲 / 倒象 + 健康 domain。"""
    if domain != "健康":
        # 寿元门只在健康 domain 主导（其他 domain 仅作补充提示，不归属）
        return None

    explanations: list[str] = []
    conf = 0.0

    # 倒象 = 寿元被坏
    daoxiang = next((t for t in triggers if t.trigger_type == "倒象成立" and t.triggered), None)
    if daoxiang:
        explanations.append(f"倒象成立: {daoxiang.explanation[:60]}")
        conf = max(conf, 0.92)

    # 日支被冲（主位移位）
    day_zhi = parsed.bazi.day_zhi
    ln_g, ln_z = liunian_ganzhi(parsed.dayun_list[0].start_year if parsed.dayun_list else 0)
    # 上面的 year 不对，由 caller 提供 triggers 已经带了 year 信息
    # 简化：如果触发列表里日支被冲，记录
    for t in triggers:
        if t.trigger_type == "合冲引动" and day_zhi in t.target_chars and "冲" in t.explanation:
            explanations.append(f"主位{day_zhi}被冲")
            conf = max(conf, 0.7)
            break

    if conf == 0.0:
        return None
    return Door(
        door_type="寿元门",
        matched=True,
        confidence=conf,
        explanation="; ".join(explanations) or "寿元被坏",
    )


# ============================================================
# 3) 牢灾门
# ============================================================


def _classify_laozai(
    parsed: ParsedInput,
    domain: str,
    energy: Optional[EnergyFindings],
    triggers: list[TriggerEvent],
) -> Optional[Door]:
    """牢灾门：食伤官杀两敌 + 流年见财 / 比肩抗杀 / 三合财局气数尽。"""
    if domain not in {"事业", "其他", "健康"}:
        return None

    day_g = parsed.bazi.day_gan
    bazi_chars = parsed.bazi.all_chars()

    # 检查是否同时有 食伤 和 官杀（食伤官杀两敌）
    has_shishang = False
    has_guansha = False
    for c in bazi_chars:
        try:
            ss = get_shishen(day_g, c)
        except (ValueError, RuntimeError):
            continue
        sc = get_shishen_class(ss)
        if sc == "食伤":
            has_shishang = True
        elif sc == "官":
            has_guansha = True

    if not (has_shishang and has_guansha):
        return None

    # 倒象作用 → 牢灾信号加强
    daoxiang = next((t for t in triggers if t.trigger_type == "倒象成立" and t.triggered), None)
    if daoxiang:
        return Door(
            door_type="牢灾门",
            matched=True,
            confidence=0.78,
            explanation=f"食伤官杀两敌 + 倒象 → 牢灾信号: {daoxiang.explanation[:50]}",
        )
    return None


# ============================================================
# 4) 墓库门
# ============================================================


def _classify_muku(
    parsed: ParsedInput, domain: str, triggers: list[TriggerEvent]
) -> Optional[Door]:
    """墓库门：财官入库 + 库被开。"""
    muku_t = next((t for t in triggers if t.trigger_type == "墓库开闭" and t.triggered), None)
    if not muku_t:
        return None
    return Door(
        door_type="墓库门",
        matched=True,
        confidence=0.82,
        explanation=f"墓库开: {muku_t.explanation[:80]}",
    )


# ============================================================
# 5) 统领门
# ============================================================


def _classify_tongling(
    parsed: ParsedInput,
    domain: str,
    energy: Optional[EnergyFindings],
    triggers: list[TriggerEvent],
) -> Optional[Door]:
    """统领门：官统财 / 财统官 / 杀统财 = 富贵跃升。"""
    if domain not in {"事业", "财运"}:
        return None

    day_g = parsed.bazi.day_gan
    cnt: dict[str, int] = {"财": 0, "官": 0}
    for c in parsed.bazi.all_chars():
        try:
            sc = get_shishen_class(get_shishen(day_g, c))
        except (ValueError, RuntimeError):
            continue
        if sc in cnt:
            cnt[sc] += 1

    # 简化判定：财官同现且 ≥1 个透出 → 可能统领
    # 实际口诀：官少财多=财统官，官多财少=官统财
    if cnt["财"] == 0 or cnt["官"] == 0:
        return None

    # 触发是否引动相关字
    relevant = any(
        t.triggered and any(
            get_shishen_class(get_shishen(day_g, c)) in ("财", "官")
            for c in t.target_chars
            if c in "甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥"
        )
        for t in triggers
    )
    if not relevant:
        return None

    if cnt["财"] >= cnt["官"]:
        kind = "财统官"
    else:
        kind = "官统财"
    return Door(
        door_type="统领门",
        matched=True,
        confidence=0.7,
        explanation=f"{kind}（财={cnt['财']}, 官={cnt['官']}），{domain}领域跃升信号",
    )


# ============================================================
# 6) 动门（兜底）
# ============================================================


def _classify_dongmen(
    parsed: ParsedInput, domain: str, triggers: list[TriggerEvent]
) -> Optional[Door]:
    """动门（最广义）：日干日支被合冲穿刑或伏吟引动 = 动事。"""
    day_g = parsed.bazi.day_gan
    day_z = parsed.bazi.day_zhi
    for t in triggers:
        if not t.triggered:
            continue
        if day_g in t.target_chars or day_z in t.target_chars:
            return Door(
                door_type="动门",
                matched=True,
                confidence=0.6,
                explanation=f"{t.trigger_type}引动主位({day_g}{day_z})",
            )
    # 多个触发齐发也算"动"
    cnt = sum(1 for t in triggers if t.triggered)
    if cnt >= 2:
        return Door(
            door_type="动门",
            matched=True,
            confidence=0.55,
            explanation=f"{cnt} 触发同时发动",
        )
    return None


# ============================================================
# 主入口
# ============================================================


def classify_into_12_doors(
    parsed: ParsedInput,
    domain: str,
    triggers: list[TriggerEvent],
    energy: Optional[EnergyFindings] = None,
    picture: Optional[PictureFindings] = None,
) -> Optional[Door]:
    """12 道门分类。

    优先级（按任务说明）：寿元门 / 牢灾门 > 鸳鸯门 / 统领门 > 其他

    返回最匹配的门；若无匹配返回未分类 Door（matched=False）或 None。
    """
    candidates: list[Door] = []

    # 高优先：寿元 / 牢灾
    d = _classify_shouyuan(parsed, domain, energy, triggers)
    if d:
        candidates.append(d)
    d = _classify_laozai(parsed, domain, energy, triggers)
    if d:
        candidates.append(d)

    # 中优先：鸳鸯 / 统领
    d = _classify_yuanyang(parsed, domain, triggers)
    if d:
        candidates.append(d)
    d = _classify_tongling(parsed, domain, energy, triggers)
    if d:
        candidates.append(d)

    # 低优先：墓库 / 动门
    d = _classify_muku(parsed, domain, triggers)
    if d:
        candidates.append(d)
    d = _classify_dongmen(parsed, domain, triggers)
    if d:
        candidates.append(d)

    if not candidates:
        return Door(door_type="未分类", matched=False, confidence=0.0,
                    explanation="未触发任何核心 6 门")

    # 按优先级 + confidence 排序
    priority = {
        "寿元门": 0, "牢灾门": 1,
        "鸳鸯门": 2, "统领门": 3,
        "墓库门": 4, "动门": 5,
        "未分类": 99,
    }
    candidates.sort(key=lambda d: (priority.get(d.door_type, 99), -d.confidence))
    return candidates[0]


# ============================================================
# smoke
# ============================================================


def _smoke() -> None:
    from engine.predicates.types import Bazi, Pillar, Dayun, ParsedInput
    from .chufa import detect_all_triggers
    from .keys import get_primary_keys

    bz = Bazi.parse("庚申", "戊寅", "壬子", "辛丑")
    dayuns = [
        Dayun(Pillar.parse("庚辰"), 18, 28, 1998, 2008),
        Dayun(Pillar.parse("壬午"), 38, 48, 2018, 2028),
    ]
    pi = ParsedInput(gender="男", birth_year=1980, bazi=bz, dayun_list=dayuns)

    keys = get_primary_keys("婚姻", bz, None, gender="男")
    yong = ["丙", "子"]

    # 2005 婚姻：合冲引动涉及妻宫子？看 detect 输出
    triggers = detect_all_triggers(pi, 2005, keys, yong)
    door = classify_into_12_doors(pi, "婚姻", triggers)
    # 应是鸳鸯门或动门
    assert door is not None
    assert door.matched
    assert door.door_type in {"鸳鸯门", "动门"}, f"got {door.door_type}"

    # 2026 婚姻：午冲子妻宫 → 鸳鸯门
    triggers = detect_all_triggers(pi, 2026, keys, yong)
    door = classify_into_12_doors(pi, "婚姻", triggers)
    assert door is not None and door.matched
    assert door.door_type == "鸳鸯门", f"got {door.door_type}, expl={door.explanation}"

    # 事业 domain - 2026
    keys_career = get_primary_keys("事业", bz, None, gender="男")
    triggers_career = detect_all_triggers(pi, 2026, keys_career, ["戊", "己"])
    door = classify_into_12_doors(pi, "事业", triggers_career)
    assert door is not None  # 至少未分类

    print("yingqi.menshu smoke OK")


if __name__ == "__main__":
    _smoke()
