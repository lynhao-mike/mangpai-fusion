"""engine/predicates/relations.py · v1.2 合冲刑穿破谓词（11 函数）

实现 02-predicate-library.md § 4.3 全部 11 个函数。

相对力度排序（M1-D-021..024 + 178 + relation_strength）：
    冲 1.0 > 穿 0.9 > 克 0.8 > 刑 0.7 > 合 0.6 > 破 0.4

合分 3 态：化成 / 合绊 / 搅局（M1-D-139, 181）

作者：Track-A
"""
from __future__ import annotations

from typing import Literal, Optional

from engine.predicates.types import (
    Canggan,
    Gan,
    GanZhi,
    Wuxing,
    Zhi,
    ZHI_LIST,
    ZHI_CANGGAN_TABLE,
)
from engine.predicates.ganzhi import gan_to_wuxing, zhi_to_wuxing


# ============================================================
# 数据表
# ============================================================

# 天干五合（化神 + 默认状态）
# 段派：合是否化成由是否得令、有无搅局判定，详见 gan_he 文档
_GAN_HE_TABLE: dict[frozenset[Gan], Wuxing] = {
    frozenset(("甲", "己")): "土",
    frozenset(("乙", "庚")): "金",
    frozenset(("丙", "辛")): "水",
    frozenset(("丁", "壬")): "木",
    frozenset(("戊", "癸")): "火",
}

# 地支六合
_ZHI_LIUHE_TABLE: dict[frozenset[Zhi], Optional[Wuxing]] = {
    frozenset(("子", "丑")): "土",
    frozenset(("寅", "亥")): "木",
    frozenset(("卯", "戌")): "火",
    frozenset(("辰", "酉")): "金",
    frozenset(("巳", "申")): "水",
    frozenset(("午", "未")): None,  # 午未合而不化（多说合化"日月之精"无固定五行）
}

# 三合局：(三合三字, 化神)
_SANHE_TABLE: list[tuple[frozenset[Zhi], Wuxing]] = [
    (frozenset(("申", "子", "辰")), "水"),
    (frozenset(("寅", "午", "戌")), "火"),
    (frozenset(("巳", "酉", "丑")), "金"),
    (frozenset(("亥", "卯", "未")), "木"),
]

# 三合局的中支（半合的关键支）
_SANHE_CENTER: dict[frozenset[Zhi], Zhi] = {
    frozenset(("申", "子", "辰")): "子",
    frozenset(("寅", "午", "戌")): "午",
    frozenset(("巳", "酉", "丑")): "酉",
    frozenset(("亥", "卯", "未")): "卯",
}

# 三会方：(三会三字, 五行)
_SANHUI_TABLE: list[tuple[frozenset[Zhi], Wuxing]] = [
    (frozenset(("寅", "卯", "辰")), "木"),
    (frozenset(("巳", "午", "未")), "火"),
    (frozenset(("申", "酉", "戌")), "金"),
    (frozenset(("亥", "子", "丑")), "水"),
]

# 地支六冲
_ZHI_CHONG_PAIRS: set[frozenset[Zhi]] = {
    frozenset(("子", "午")),
    frozenset(("丑", "未")),
    frozenset(("寅", "申")),
    frozenset(("卯", "酉")),
    frozenset(("辰", "戌")),
    frozenset(("巳", "亥")),
}

# 地支三刑（互刑式）
_SAN_XING_GROUPS: list[frozenset[Zhi]] = [
    frozenset(("寅", "巳", "申")),
    frozenset(("丑", "戌", "未")),
]
# 子卯互刑
_HU_XING: set[frozenset[Zhi]] = {frozenset(("子", "卯"))}
# 自刑
_ZI_XING: set[Zhi] = {"辰", "午", "酉", "亥"}

# 地支六穿（任派核心，段派也用）
# 子未 / 丑午 / 寅巳 / 卯辰 / 申亥 / 酉戌
_ZHI_CHUAN_PAIRS: set[frozenset[Zhi]] = {
    frozenset(("子", "未")),
    frozenset(("丑", "午")),
    frozenset(("寅", "巳")),
    frozenset(("卯", "辰")),
    frozenset(("申", "亥")),
    frozenset(("酉", "戌")),
}

# 地支六破
# 子酉 / 寅亥 / 卯午 / 辰丑 / 巳申 / 戌未
_ZHI_PO_PAIRS: set[frozenset[Zhi]] = {
    frozenset(("子", "酉")),
    frozenset(("寅", "亥")),
    frozenset(("卯", "午")),
    frozenset(("辰", "丑")),
    frozenset(("巳", "申")),
    frozenset(("戌", "未")),
}

# 干支暗合表（段派 + 杨派 + 任派 都引用）
# 来源：M1-D-136 暗合 7 子类
# 干支暗合（一柱内或跨柱）= 天干与地支藏干合
# 这里只列经典对（非穷举）：
_GAN_ZHI_ANHE_PAIRS: set[tuple[Gan, Zhi]] = {
    ("甲", "丑"),  # 甲己合：丑藏己
    ("戊", "子"),  # 戊癸合：子藏癸
    ("丙", "申"),  # 丙辛合：申藏壬?? 申主气庚 + 中气壬，无辛 → 故此对存争议；保守不收
    ("丁", "亥"),  # 丁壬合：亥主气壬 → 真合
    ("辛", "午"),  # 丙辛合：午主气丁，丁壬非丙辛 → 不收
}
# 重整：用规范定义"天干与地支藏干形成五合"
_GAN_ZHI_ANHE_PAIRS = set()
for gan in ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"):
    for zhi in ZHI_LIST:
        # 找 zhi 的所有藏干
        for cg, _, _ in ZHI_CANGGAN_TABLE.get(zhi, []):
            if frozenset((gan, cg)) in _GAN_HE_TABLE:
                _GAN_ZHI_ANHE_PAIRS.add((gan, zhi))


# ============================================================
# 1. 天干五合
# ============================================================

def gan_he(
    a: Gan,
    b: Gan,
    *,
    has_geju_support: Optional[bool] = None,
    has_jiaolu: Optional[bool] = None,
    is_dejin: Optional[bool] = None,
) -> Optional[tuple[Wuxing, Literal["化成", "合绊", "搅局"]]]:
    """天干五合判定。

    返回 (化神, 状态) 或 None。

    五合表：
    - 甲己合化土 / 乙庚合化金 / 丙辛合化水 / 丁壬合化木 / 戊癸合化火

    状态判定（M1-D-181 / D-139）：
    - 化成：得令 + 有格局支撑 + 无搅局 → 真化（"如夫妻一心"）
    - 合绊：合而不化（无得令支撑）→ 二干都被绊住失去原性
    - 搅局：有第三方搅局（如另一干来争合）

    若不传 has_geju_support / has_jiaolu / is_dejin，则默认状态为 "合绊"
    （保守判断，符合段派"合不化的多过化的"实际比例）。
    """
    if a == b:
        return None
    pair = frozenset((a, b))
    if pair not in _GAN_HE_TABLE:
        return None

    huashen = _GAN_HE_TABLE[pair]

    # 默认状态：合绊
    state: Literal["化成", "合绊", "搅局"] = "合绊"
    if has_jiaolu is True:
        state = "搅局"
    elif is_dejin is True and has_geju_support is True:
        state = "化成"
    elif is_dejin is False:
        state = "合绊"

    return huashen, state


# ============================================================
# 2. 地支六合
# ============================================================

def zhi_liuhe(a: Zhi, b: Zhi) -> Optional[Wuxing]:
    """地支六合，返回化神（或 None 若不合 / 午未合无固定）。"""
    if a == b:
        return None
    pair = frozenset((a, b))
    if pair in _ZHI_LIUHE_TABLE:
        return _ZHI_LIUHE_TABLE[pair]
    return None


# ============================================================
# 3. 三合局
# ============================================================

def zhi_sanhe(zhis: list[Zhi]) -> Optional[Wuxing]:
    """地支三合局：申子辰水 / 寅午戌火 / 巳酉丑金 / 亥卯未木。

    支持半合：3 字齐全成全局 / 含中支 + 任一其他支 = 半合。
    """
    if not zhis:
        return None
    s = set(zhis)
    for group, hua in _SANHE_TABLE:
        if group <= s:
            return hua
        # 半合：必须含中支 + 至少另 1 个
        center = _SANHE_CENTER[group]
        if center in s:
            others = group - {center}
            if any(o in s for o in others):
                return hua
    return None


# ============================================================
# 4. 三会方
# ============================================================

def zhi_sanhui(zhis: list[Zhi]) -> Optional[Wuxing]:
    """地支三会方：寅卯辰木 / 巳午未火 / 申酉戌金 / 亥子丑水。

    必须 3 支全到才成会（与三合不同，三会不允许半会）。
    """
    if not zhis:
        return None
    s = set(zhis)
    for group, hua in _SANHUI_TABLE:
        if group <= s:
            return hua
    return None


# ============================================================
# 5. 地支六冲
# ============================================================

def zhi_chong(a: Zhi, b: Zhi) -> bool:
    """地支六冲：子午 / 丑未 / 寅申 / 卯酉 / 辰戌 / 巳亥。"""
    if a == b:
        return False
    return frozenset((a, b)) in _ZHI_CHONG_PAIRS


# ============================================================
# 6. 地支刑
# ============================================================

def zhi_xing(a: Zhi, b: Zhi) -> Optional[Literal["三刑", "自刑", "互刑"]]:
    """地支刑判定。

    - 三刑：寅巳申、丑戌未（任意 2 字即可触发"半刑"，按段派统计为三刑）
    - 自刑：辰辰、午午、酉酉、亥亥
    - 互刑：子卯
    """
    if a == b:
        if a in _ZI_XING:
            return "自刑"
        return None
    pair = frozenset((a, b))
    if pair in _HU_XING:
        return "互刑"
    for grp in _SAN_XING_GROUPS:
        if pair <= grp:
            return "三刑"
    return None


# ============================================================
# 7. 地支六穿
# ============================================================

def zhi_chuan(a: Zhi, b: Zhi) -> bool:
    """地支六穿（六害）。

    任派核心概念："穿不可调和"。
    """
    if a == b:
        return False
    return frozenset((a, b)) in _ZHI_CHUAN_PAIRS


# ============================================================
# 8. 地支六破
# ============================================================

def zhi_po(a: Zhi, b: Zhi) -> bool:
    """地支六破。"""
    if a == b:
        return False
    return frozenset((a, b)) in _ZHI_PO_PAIRS


# ============================================================
# 9. 地支自合（藏干自合）
# ============================================================

def zhi_zihe(z: Zhi) -> Optional[GanZhi]:
    """地支自合（藏干内部存在五合）。

    例：辰中藏戊乙癸 → 戊癸合（自合，化火）
        戌中藏戊辛丁 → 丙辛合？戌无丙 → 无自合
        但实际段派认可的"自合"较少，主要是辰戌（含癸）和未（含乙己）。

    返回构造的"虚拟干支"表达自合的两干（任意，仅供下游判读）；
    无自合返回 None。
    """
    cangs = ZHI_CANGGAN_TABLE.get(z, [])
    gans_in = [c[0] for c in cangs]
    for i in range(len(gans_in)):
        for j in range(i + 1, len(gans_in)):
            if frozenset((gans_in[i], gans_in[j])) in _GAN_HE_TABLE:
                return GanZhi(gan=gans_in[i], zhi=z)  # type: ignore[arg-type]
    return None


# ============================================================
# 10. 干支暗合
# ============================================================

def gan_zhi_anhe(g: Gan, z: Zhi) -> bool:
    """干支暗合：天干与地支某个藏干形成五合。

    例：甲与丑（丑藏己 → 甲己合）
        戊与子（子藏癸 → 戊癸合）
        丁与亥（亥藏壬 → 丁壬合）
    """
    return (g, z) in _GAN_ZHI_ANHE_PAIRS


# ============================================================
# 11. 关系力度
# ============================================================

_REL_STRENGTH_TABLE: dict[str, float] = {
    "合": 0.6,
    "六合": 0.6,
    "三合": 0.7,  # 三合化局力度更大
    "冲": 1.0,
    "刑": 0.7,
    "克": 0.8,
    "穿": 0.9,
    "害": 0.9,  # 害=穿
    "破": 0.4,
}


def relation_strength(rel: str) -> float:
    """5 大制法力度排序（M1-D 标准 + relation_strength 契约）。

    合 0.6 / 冲 1.0 / 刑 0.7 / 克 0.8 / 穿 0.9 / 破 0.4
    """
    if rel in _REL_STRENGTH_TABLE:
        return _REL_STRENGTH_TABLE[rel]
    raise ValueError(f"未知关系: {rel!r}")


# ============================================================
# smoke test
# ============================================================

def _smoke() -> None:
    # 天干五合
    h = gan_he("甲", "己")
    assert h is not None and h[0] == "土"
    assert gan_he("丙", "辛")[0] == "水"  # type: ignore[index]
    assert gan_he("甲", "甲") is None
    assert gan_he("甲", "乙") is None  # 不构成合

    # 状态判定
    assert gan_he("甲", "己")[1] == "合绊"  # type: ignore[index]
    assert gan_he("甲", "己", is_dejin=True, has_geju_support=True)[1] == "化成"  # type: ignore[index]
    assert gan_he("甲", "己", has_jiaolu=True)[1] == "搅局"  # type: ignore[index]

    # 六合
    assert zhi_liuhe("子", "丑") == "土"
    assert zhi_liuhe("寅", "亥") == "木"
    assert zhi_liuhe("午", "未") is None  # 不化
    assert zhi_liuhe("子", "卯") is None

    # 三合
    assert zhi_sanhe(["申", "子", "辰"]) == "水"
    assert zhi_sanhe(["申", "子"]) == "水"  # 半合（含中支子）
    assert zhi_sanhe(["申", "辰"]) is None  # 不含中支
    assert zhi_sanhe(["寅", "午", "戌"]) == "火"

    # 三会
    assert zhi_sanhui(["寅", "卯", "辰"]) == "木"
    assert zhi_sanhui(["寅", "卯"]) is None  # 不允许半会

    # 冲
    assert zhi_chong("子", "午")
    assert zhi_chong("寅", "申")
    assert not zhi_chong("子", "丑")

    # 刑
    assert zhi_xing("寅", "巳") == "三刑"
    assert zhi_xing("丑", "戌") == "三刑"
    assert zhi_xing("子", "卯") == "互刑"
    assert zhi_xing("辰", "辰") == "自刑"
    assert zhi_xing("子", "丑") is None  # 子丑合不刑

    # 穿
    assert zhi_chuan("子", "未")
    assert zhi_chuan("寅", "巳")
    assert not zhi_chuan("子", "午")  # 是冲不是穿

    # 破
    assert zhi_po("子", "酉")
    assert zhi_po("巳", "申")
    assert not zhi_po("子", "丑")

    # 自合
    assert zhi_zihe("辰") is not None  # 戊癸合
    assert zhi_zihe("子") is None  # 子只藏癸

    # 干支暗合
    assert gan_zhi_anhe("甲", "丑")  # 丑藏己 → 甲己合
    assert gan_zhi_anhe("戊", "子")  # 子藏癸 → 戊癸合
    assert gan_zhi_anhe("丁", "亥")  # 亥藏壬 → 丁壬合
    assert not gan_zhi_anhe("甲", "子")  # 子无己

    # 关系力度
    assert relation_strength("冲") == 1.0
    assert relation_strength("穿") == 0.9
    assert relation_strength("克") == 0.8
    assert relation_strength("刑") == 0.7
    assert relation_strength("合") == 0.6
    assert relation_strength("破") == 0.4
    try:
        relation_strength("XX")
        raise AssertionError
    except ValueError:
        pass

    print("[OK] relations smoke：11 函数全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
