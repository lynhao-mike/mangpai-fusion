"""engine/yingqi/menshu.py · v1.2 D3 任派 · 12 道门分类

按 04-gate-protocol.md § 6.1（任派 §16）实现。

Track-C MVP 实现核心 6 + 简版 5 = 11 道门：
    核心 6（fallback 必交付）：动门 / 统领门 / 墓库门 / 鸳鸯门 / 寿元门 / 牢灾门
    简版 5：格局门 / 天地门 / 夹拱门 / 旬空门 / 伤残门
                （简版 = 触发条件较粗、留待 D4 神煞旁证补强）

主入口：
    classify_into_12_doors(triggers, domain, energy, picture, parsed) -> Optional[DoorType]

优先级（任务说明 § 阶段 2）：
    寿元门 / 牢灾门     (高优先：凶应)
    鸳鸯门 / 统领门     (中优先：领域专门)
    墓库门 / 动门 / 其他 (低优先)

作者：Track-C
"""
from __future__ import annotations

from typing import Any, Optional

from engine.energy.types import EnergyFindings
from engine.picture.types import PictureFindings
from engine.predicates.cycles import liunian_ganzhi
from engine.predicates.palace import get_shishen
from engine.predicates.relations import zhi_chong, zhi_chuan, zhi_xing
from engine.predicates.types import (
    Bazi,
    GAN_LIST,
    ParsedInput,
    ZHI_CANGGAN_TABLE,
    ZHI_LIST,
)

from engine.yingqi.types import DoorType, TriggerEvent


# ============================================================
# 道门候选 dataclass（仅本模块内部使用）
# ============================================================

class _DoorMatch:
    """单个道门匹配候选。"""
    __slots__ = ("door", "priority", "reason")

    def __init__(self, door: DoorType, priority: int, reason: str):
        self.door = door
        self.priority = priority
        self.reason = reason


# 优先级（数字小 = 高优先）
_PRIORITY = {
    "寿元门": 1,
    "牢灾门": 1,
    "鸳鸯门": 2,
    "统领门": 2,
    "格局门": 3,
    "墓库门": 4,
    "天地门": 4,
    "夹拱门": 5,
    "动门": 6,
    "旬空门": 7,
    "伤残门": 7,
}


# ============================================================
# 1. 鸳鸯门（婚姻专门）
# ============================================================

def _classify_yuanyang(
    domain: str,
    triggers: list[TriggerEvent],
    parsed: ParsedInput,
) -> Optional[_DoorMatch]:
    """鸳鸯门：配偶星 / 婚宫被引动。

    04 § 6.1：配偶星与日干形成五合 + 流年引动。
    简化：婚姻 domain + 触发涉及妻/夫宫（日支）或配偶星 → 鸳鸯门。
    """
    if domain != "婚姻":
        return None

    bazi = parsed.bazi
    day_zhi = bazi.日柱.zhi
    day_master = bazi.day_master
    gender = (parsed.birth or {}).get("性别", "M")
    is_male = str(gender).strip().upper() not in ("F", "FEMALE", "女", "坤", "坤造")

    spouse_star_set = {"正官", "七杀"} if not is_male else {"正财", "偏财"}

    notes: list[str] = []
    for t in triggers:
        # 涉及婚宫
        if day_zhi in t.target_chars:
            notes.append(f"{t.type}涉及{('夫' if not is_male else '妻')}宫({day_zhi})")
            continue
        # 涉及配偶星
        for c in t.target_chars:
            if c not in GAN_LIST and c not in ZHI_LIST:
                continue
            try:
                if c in GAN_LIST:
                    ss = get_shishen(c, day_master)
                else:
                    cangs = ZHI_CANGGAN_TABLE.get(c, [])
                    if not cangs:
                        continue
                    ss = get_shishen(cangs[0][0], day_master)
                if ss in spouse_star_set:
                    notes.append(f"{t.type}涉及配偶星{c}({ss})")
                    break
            except (ValueError, RuntimeError):
                continue

    if not notes:
        return None
    return _DoorMatch(
        door="鸳鸯门",
        priority=_PRIORITY["鸳鸯门"],
        reason="; ".join(notes[:3]),
    )


# ============================================================
# 2. 寿元门（健康专门）
# ============================================================

def _classify_shouyuan(
    domain: str,
    triggers: list[TriggerEvent],
    parsed: ParsedInput,
) -> Optional[_DoorMatch]:
    """寿元门：日干被严重克泄 + 流年填实。

    04 § 6.1 触发：日干被严重克泄 + 流年填实
    判定：health domain + (倒象成立 OR 主位被冲)。
    """
    if domain not in ("健康", "六亲"):  # 六亲含寿命相关（如父母去世）
        return None

    notes: list[str] = []
    bazi = parsed.bazi
    day_zhi = bazi.日柱.zhi
    day_gan = bazi.day_master

    # 倒象 = 寿元被坏
    for t in triggers:
        if t.type == "倒象成立":
            # 倒象目标包含日干或主位 → 寿元门
            if day_gan in t.target_chars or day_zhi in t.target_chars:
                notes.append(f"日干/主位倒象: {t.description[:60]}")
            elif domain == "六亲":  # 六亲场景倒象也算寿元
                notes.append(f"用神倒象: {t.description[:60]}")

    # 主位被冲
    for t in triggers:
        if t.type == "合冲引动" and "冲" in t.description:
            if day_zhi in t.target_chars:
                notes.append(f"主位{day_zhi}被冲: {t.description[:60]}")
                break

    if not notes:
        return None
    return _DoorMatch(
        door="寿元门",
        priority=_PRIORITY["寿元门"],
        reason="; ".join(notes[:2]),
    )


# ============================================================
# 3. 牢灾门
# ============================================================

def _classify_laozai(
    domain: str,
    triggers: list[TriggerEvent],
    energy: Optional[EnergyFindings],
    parsed: ParsedInput,
) -> Optional[_DoorMatch]:
    """牢灾门：七杀+羊刃+刑冲在年/月柱。

    简化判定：原局含食伤+官杀（两敌）+ 当年触发倒象 → 牢灾信号。
    """
    if domain not in ("事业", "其他", "健康"):
        return None

    bazi = parsed.bazi
    day_master = bazi.day_master

    has_shishang = False
    has_guansha = False

    # 扫描天干
    for _, gan in bazi.all_gans():
        if gan == day_master:
            continue
        try:
            ss = get_shishen(gan, day_master)
            if ss in ("食神", "伤官"):
                has_shishang = True
            if ss in ("正官", "七杀"):
                has_guansha = True
        except (ValueError, RuntimeError):
            pass

    # 扫描地支主气
    for _, zhi in bazi.all_zhis():
        cangs = ZHI_CANGGAN_TABLE.get(zhi, [])
        if not cangs:
            continue
        try:
            ss = get_shishen(cangs[0][0], day_master)
            if ss in ("食神", "伤官"):
                has_shishang = True
            if ss in ("正官", "七杀"):
                has_guansha = True
        except (ValueError, RuntimeError):
            pass

    if not (has_shishang and has_guansha):
        return None

    # 倒象触发
    daoxiang = next((t for t in triggers if t.type == "倒象成立"), None)
    if daoxiang is None:
        return None

    return _DoorMatch(
        door="牢灾门",
        priority=_PRIORITY["牢灾门"],
        reason=f"食伤官杀两敌 + 倒象凶应: {daoxiang.description[:50]}",
    )


# ============================================================
# 4. 墓库门
# ============================================================

def _classify_muku(
    domain: str,
    triggers: list[TriggerEvent],
) -> Optional[_DoorMatch]:
    """墓库门：触发 = 墓库开闭。

    04 § 6.1 适用 [财运, 六亲, 健康]。
    """
    if domain not in ("财运", "六亲", "健康", "事业"):
        # 事业 domain 在某些场景墓库开也成立（财库被冲 → 财官库开）
        return None

    muku_t = next((t for t in triggers if t.type == "墓库开闭"), None)
    if muku_t is None:
        return None

    return _DoorMatch(
        door="墓库门",
        priority=_PRIORITY["墓库门"],
        reason=f"墓库开: {muku_t.description[:80]}",
    )


# ============================================================
# 5. 统领门
# ============================================================

def _classify_tongling(
    domain: str,
    triggers: list[TriggerEvent],
    energy: Optional[EnergyFindings],
    parsed: ParsedInput,
) -> Optional[_DoorMatch]:
    """统领门：财统官 / 官统财 / 杀统财（事业 / 财运 跃升）。

    简化判定：原局财官同现 + 当年触发涉及财或官字 → 统领门。
    """
    if domain not in ("事业", "财运"):
        return None

    bazi = parsed.bazi
    day_master = bazi.day_master

    cnt_cai = 0
    cnt_guan = 0

    for _, gan in bazi.all_gans():
        if gan == day_master:
            continue
        try:
            ss = get_shishen(gan, day_master)
            if ss in ("正财", "偏财"):
                cnt_cai += 1
            elif ss in ("正官", "七杀"):
                cnt_guan += 1
        except (ValueError, RuntimeError):
            pass

    for _, zhi in bazi.all_zhis():
        cangs = ZHI_CANGGAN_TABLE.get(zhi, [])
        if not cangs:
            continue
        try:
            ss = get_shishen(cangs[0][0], day_master)
            if ss in ("正财", "偏财"):
                cnt_cai += 1
            elif ss in ("正官", "七杀"):
                cnt_guan += 1
        except (ValueError, RuntimeError):
            pass

    if cnt_cai == 0 or cnt_guan == 0:
        return None

    # 当年触发是否涉及财或官
    relevant = False
    for t in triggers:
        for c in t.target_chars:
            try:
                if c in GAN_LIST:
                    ss = get_shishen(c, day_master)
                elif c in ZHI_LIST:
                    cangs = ZHI_CANGGAN_TABLE.get(c, [])
                    if not cangs:
                        continue
                    ss = get_shishen(cangs[0][0], day_master)
                else:
                    continue
                if ss in ("正财", "偏财", "正官", "七杀"):
                    relevant = True
                    break
            except (ValueError, RuntimeError):
                pass
        if relevant:
            break

    if not relevant:
        return None

    kind = "财统官" if cnt_cai >= cnt_guan else "官统财"
    return _DoorMatch(
        door="统领门",
        priority=_PRIORITY["统领门"],
        reason=f"{kind}（财={cnt_cai}, 官={cnt_guan}），{domain}领域跃升",
    )


# ============================================================
# 6. 动门（最广义兜底）
# ============================================================

def _classify_dongmen(
    domain: str,
    triggers: list[TriggerEvent],
    parsed: ParsedInput,
) -> Optional[_DoorMatch]:
    """动门：合冲引动到关键宫位（最广义动事）。

    04 § 6.1 适用 [婚姻, 事业, 财运, 健康]。
    """
    if domain not in ("婚姻", "事业", "财运", "健康"):
        return None

    bazi = parsed.bazi
    day_gan = bazi.day_master
    day_zhi = bazi.日柱.zhi

    # 主位被引动（日柱字在某触发的 target 中）
    for t in triggers:
        if day_gan in t.target_chars or day_zhi in t.target_chars:
            return _DoorMatch(
                door="动门",
                priority=_PRIORITY["动门"],
                reason=f"{t.type}引动主位({day_gan}{day_zhi}): {t.description[:50]}",
            )

    # 两个以上触发齐发也算"动"
    if len(triggers) >= 2:
        return _DoorMatch(
            door="动门",
            priority=_PRIORITY["动门"],
            reason=f"{len(triggers)} 触发同时发动: {[t.type for t in triggers[:3]]}",
        )

    return None


# ============================================================
# 7. 天地门（简版）
# ============================================================

def _classify_tiandi(
    triggers: list[TriggerEvent],
    parsed: ParsedInput,
    year: int,
) -> Optional[_DoorMatch]:
    """天地门：流年天干地支同时引动同一柱。

    判定：流年柱与原局某柱伏吟 OR 流年干合该柱干 + 流年支合/冲该柱支。
    """
    ln = liunian_ganzhi(year)
    bazi = parsed.bazi

    # 伏吟（最强）
    for name, pillar in bazi.all_pillars():
        if pillar.gan == ln.gan and pillar.zhi == ln.zhi:
            return _DoorMatch(
                door="天地门",
                priority=_PRIORITY["天地门"],
                reason=f"流年{ln} 天地伏吟原局{name}",
            )

    # 流年干合 + 流年支合冲（含半三合）同一柱
    from engine.predicates.relations import gan_he as _gh
    from engine.predicates.relations import (
        zhi_liuhe as _zl, zhi_sanhe as _zs,
    )
    for name, pillar in bazi.all_pillars():
        gan_match = _gh(ln.gan, pillar.gan) is not None
        zhi_match = (
            _zl(ln.zhi, pillar.zhi) is not None
            or _zs([ln.zhi, pillar.zhi]) is not None
            or zhi_chong(ln.zhi, pillar.zhi)
        )
        if gan_match and zhi_match:
            return _DoorMatch(
                door="天地门",
                priority=_PRIORITY["天地门"],
                reason=f"流年{ln} 天地双合/合冲原局{name}({pillar})",
            )

    return None


# ============================================================
# 8. 格局门（简版）
# ============================================================

def _classify_geju(
    domain: str,
    triggers: list[TriggerEvent],
    energy: Optional[EnergyFindings],
) -> Optional[_DoorMatch]:
    """格局门：流年破坏或成全原局格局。

    简化判定：energy.zuogong_paths 中有 ≥1 条 layer_count=1 的路径
    + 当年触发涉及该路径的 chain 中字 → 格局门。
    """
    if domain not in ("事业", "财运"):
        return None
    if energy is None or not energy.zuogong_paths:
        return None

    # 取做功路径中的所有字
    geju_chars: set[str] = set()
    for p in energy.zuogong_paths:
        if p.layer_count >= 1:
            geju_chars.update(p.chain)

    if not geju_chars:
        return None

    # 触发是否涉及格局字
    for t in triggers:
        for c in t.target_chars:
            if c in geju_chars:
                # 涉及到了格局字
                return _DoorMatch(
                    door="格局门",
                    priority=_PRIORITY["格局门"],
                    reason=f"流年触发涉及格局字 {c}: {t.description[:50]}",
                )
    return None


# ============================================================
# 9. 旬空门（简版）
# ============================================================

# 60 甲子旬空表（每旬末尾 2 支为旬空）
# 甲子旬：戌亥 / 甲戌旬：申酉 / 甲申旬：午未 / 甲午旬：辰巳 / 甲辰旬：寅卯 / 甲寅旬：子丑
_XUNKONG_TABLE: dict[str, list[str]] = {}


def _build_xunkong_table() -> None:
    """构造每个柱（GanZhi 字符串）对应的旬空。"""
    if _XUNKONG_TABLE:
        return
    # 60 甲子按顺序，每 10 个一旬
    # 索引 0-9: 甲子旬 → 旬空 戌亥
    xunkong_pairs = [("戌", "亥"), ("申", "酉"), ("午", "未"),
                     ("辰", "巳"), ("寅", "卯"), ("子", "丑")]
    # gan idx 0=甲, zhi idx 0=子
    for n in range(60):
        gan = GAN_LIST[n % 10]
        zhi = ZHI_LIST[n % 12]
        xun_idx = n // 10
        _XUNKONG_TABLE[f"{gan}{zhi}"] = list(xunkong_pairs[xun_idx])


_build_xunkong_table()


def _classify_xunkong(
    domain: str,
    parsed: ParsedInput,
) -> Optional[_DoorMatch]:
    """旬空门：关键字落入年柱旬空。

    简化判定：年柱所在旬的旬空字若包含日支 / 时支 → 旬空门。
    """
    if domain not in ("六亲", "财运"):
        return None
    bazi = parsed.bazi
    year_pillar_str = f"{bazi.年柱.gan}{bazi.年柱.zhi}"
    xunkong = _XUNKONG_TABLE.get(year_pillar_str, [])
    if not xunkong:
        return None
    # 检查日支 / 时支是否在旬空
    if bazi.日柱.zhi in xunkong:
        return _DoorMatch(
            door="旬空门",
            priority=_PRIORITY["旬空门"],
            reason=f"日支{bazi.日柱.zhi} 落年柱旬空 ({','.join(xunkong)})",
        )
    if bazi.时柱.zhi in xunkong:
        return _DoorMatch(
            door="旬空门",
            priority=_PRIORITY["旬空门"],
            reason=f"时支{bazi.时柱.zhi} 落年柱旬空 ({','.join(xunkong)})",
        )
    return None


# ============================================================
# 10. 夹拱门 / 11. 伤残门（占位）
# ============================================================

# 这两门需要 D4 神煞旁证才能精准判定，留待后续 Track-D 集成日增强。
# 当前不主动返回（防止误判）。


# ============================================================
# 主入口
# ============================================================

def classify_into_12_doors(
    triggers: list[TriggerEvent],
    domain: str,
    energy: Optional[EnergyFindings],
    picture: Optional[PictureFindings],
    parsed: ParsedInput,
    *,
    year: Optional[int] = None,
) -> Optional[DoorType]:
    """分类到 12 道门之一（按优先级返回最匹配的；无匹配返回 None）。

    优先级（任务说明）：寿元/牢灾 > 鸳鸯/统领 > 格局 > 墓库/天地 > 夹拱 > 动门 > 旬空/伤残。
    """
    if not triggers:
        return None

    candidates: list[_DoorMatch] = []

    # 高优先：寿元 / 牢灾
    m = _classify_shouyuan(domain, triggers, parsed)
    if m:
        candidates.append(m)
    m = _classify_laozai(domain, triggers, energy, parsed)
    if m:
        candidates.append(m)

    # 中优先：鸳鸯 / 统领
    m = _classify_yuanyang(domain, triggers, parsed)
    if m:
        candidates.append(m)
    m = _classify_tongling(domain, triggers, energy, parsed)
    if m:
        candidates.append(m)

    # 中-下：格局门
    m = _classify_geju(domain, triggers, energy)
    if m:
        candidates.append(m)

    # 中-下：墓库 / 天地
    m = _classify_muku(domain, triggers)
    if m:
        candidates.append(m)
    if year is not None:
        m = _classify_tiandi(triggers, parsed, year)
        if m:
            candidates.append(m)

    # 低优先：动门
    m = _classify_dongmen(domain, triggers, parsed)
    if m:
        candidates.append(m)

    # 低优先：旬空门
    m = _classify_xunkong(domain, parsed)
    if m:
        candidates.append(m)

    if not candidates:
        return None

    # 按 priority 升序
    candidates.sort(key=lambda d: d.priority)
    return candidates[0].door


# 调试/可观测：返回所有匹配的门 + reason
def debug_all_door_matches(
    triggers: list[TriggerEvent],
    domain: str,
    energy: Optional[EnergyFindings],
    picture: Optional[PictureFindings],
    parsed: ParsedInput,
    *,
    year: Optional[int] = None,
) -> list[tuple[DoorType, str]]:
    matches: list[_DoorMatch] = []
    for fn, args in [
        (_classify_shouyuan, (domain, triggers, parsed)),
        (_classify_laozai, (domain, triggers, energy, parsed)),
        (_classify_yuanyang, (domain, triggers, parsed)),
        (_classify_tongling, (domain, triggers, energy, parsed)),
        (_classify_geju, (domain, triggers, energy)),
        (_classify_muku, (domain, triggers)),
        (_classify_dongmen, (domain, triggers, parsed)),
        (_classify_xunkong, (domain, parsed)),
    ]:
        m = fn(*args)  # type: ignore[arg-type]
        if m:
            matches.append(m)
    if year is not None:
        m = _classify_tiandi(triggers, parsed, year)
        if m:
            matches.append(m)
    matches.sort(key=lambda d: d.priority)
    return [(m.door, m.reason) for m in matches]


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from tests.fixtures.cases import load_case
    from engine.energy.evaluator import evaluate_energy
    from engine.picture.matcher import match_picture
    from engine.yingqi.chufa import detect_all_triggers
    from engine.yingqi.keys import get_primary_keys

    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    energy = evaluate_energy(parsed)
    picture = match_picture(energy, parsed)

    # 婚姻 2005
    print("\n=== C-2026-001 婚姻 2005 ===")
    keys = get_primary_keys("婚姻", parsed.bazi, energy, gender="M")
    yong = ["丙", "子"]
    trigs = detect_all_triggers(parsed, 2005, keys, yong)
    door = classify_into_12_doors(trigs, "婚姻", energy, picture, parsed, year=2005)
    matches = debug_all_door_matches(trigs, "婚姻", energy, picture, parsed, year=2005)
    print(f"  primary door: {door}")
    print("  all matches:")
    for d, r in matches:
        print(f"    · {d}: {r[:60]}")
    assert door is not None, "2005 婚姻应有道门"

    # 婚姻 2026 → 鸳鸯门（午冲子妻宫）
    print("\n=== C-2026-001 婚姻 2026 ===")
    trigs = detect_all_triggers(parsed, 2026, keys, yong)
    door = classify_into_12_doors(trigs, "婚姻", energy, picture, parsed, year=2026)
    print(f"  door: {door}")

    # 六亲 母 2020 → 寿元门 / 动门
    print("\n=== C-2026-001 六亲(母) 2020 ===")
    keys_mu = get_primary_keys("六亲", parsed.bazi, energy, sub_domain="母")
    trigs = detect_all_triggers(parsed, 2020, keys_mu, ["辛", "庚"])
    door = classify_into_12_doors(trigs, "六亲", energy, picture, parsed, year=2020)
    print(f"  door: {door}")

    # 事业 2020
    print("\n=== C-2026-001 事业 2020 ===")
    keys_career = get_primary_keys("事业", parsed.bazi, energy)
    trigs = detect_all_triggers(parsed, 2020, keys_career, ["戊", "庚"])
    door = classify_into_12_doors(trigs, "事业", energy, picture, parsed, year=2020)
    print(f"  door: {door}")

    # 学业 2024 (C-014)
    print("\n=== C-2026-014 学业 2024 ===")
    parsed014 = load_case("C-2026-014-乾-丙戌庚子乙亥辛巳")
    energy014 = evaluate_energy(parsed014)
    picture014 = match_picture(energy014, parsed014)
    keys_xue = get_primary_keys("学业", parsed014.bazi, energy014)
    trigs = detect_all_triggers(parsed014, 2024, keys_xue, ["壬", "癸"])
    door = classify_into_12_doors(trigs, "学业", energy014, picture014, parsed014, year=2024)
    print(f"  door: {door}")
    matches = debug_all_door_matches(trigs, "学业", energy014, picture014, parsed014, year=2024)
    for d, r in matches:
        print(f"    · {d}: {r[:60]}")

    print("\n[OK] menshu smoke 全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
