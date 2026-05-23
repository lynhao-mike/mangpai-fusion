"""engine.predicates.relations · 干支关系判定

按 m3-mechanics §15 实现：
- 天干五合（合 ≠ 化）
- 地支六合
- 三合 / 半合
- 六冲
- 三刑（寅巳申 / 丑戌未）
- 六穿（六害）
- 暗合（盲派 4 组）
"""

from __future__ import annotations

# ============================================================
# 一、合
# ============================================================

# 天干五合
GAN_HE_PAIRS: list[tuple[str, str]] = [
    ("甲", "己"),
    ("乙", "庚"),
    ("丙", "辛"),
    ("丁", "壬"),
    ("戊", "癸"),
]

GAN_HE_RESULT: dict[frozenset[str], str] = {
    frozenset(["甲", "己"]): "土",
    frozenset(["乙", "庚"]): "金",
    frozenset(["丙", "辛"]): "水",
    frozenset(["丁", "壬"]): "木",
    frozenset(["戊", "癸"]): "火",
}


def is_gan_he(a: str, b: str) -> bool:
    """两个天干是否相合（不论是否化）。"""
    return frozenset([a, b]) in GAN_HE_RESULT


# 地支六合
ZHI_LIU_HE_PAIRS: list[tuple[str, str]] = [
    ("子", "丑"),
    ("寅", "亥"),
    ("卯", "戌"),
    ("辰", "酉"),
    ("巳", "申"),
    ("午", "未"),
]

ZHI_LIU_HE_SET: set[frozenset[str]] = {frozenset(p) for p in ZHI_LIU_HE_PAIRS}


def is_zhi_liuhe(a: str, b: str) -> bool:
    return frozenset([a, b]) in ZHI_LIU_HE_SET


# 三合（仅 4 组，中神最重要）
SAN_HE_GROUPS: list[tuple[str, str, str, str]] = [
    # (字 1, 中神, 字 3, 化局五行)
    ("申", "子", "辰", "水"),
    ("亥", "卯", "未", "木"),
    ("寅", "午", "戌", "火"),
    ("巳", "酉", "丑", "金"),
]


def is_sanhe_full(zhi_set: set[str]) -> tuple[bool, str]:
    """三字是否完整三合，返回 (是否成局, 化局五行 or '')。"""
    for a, b, c, wx in SAN_HE_GROUPS:
        if {a, b, c} <= zhi_set:
            return True, wx
    return False, ""


def is_banhe(a: str, b: str) -> bool:
    """两支半三合（必须包含中神 + 任一字）。"""
    for x, mid, y, _ in SAN_HE_GROUPS:
        if {a, b} == {mid, x} or {a, b} == {mid, y}:
            return True
    return False


# ============================================================
# 二、冲
# ============================================================

ZHI_CHONG_PAIRS: list[tuple[str, str]] = [
    ("子", "午"),
    ("丑", "未"),
    ("寅", "申"),
    ("卯", "酉"),
    ("辰", "戌"),
    ("巳", "亥"),
]

ZHI_CHONG_SET: set[frozenset[str]] = {frozenset(p) for p in ZHI_CHONG_PAIRS}


def is_zhi_chong(a: str, b: str) -> bool:
    return frozenset([a, b]) in ZHI_CHONG_SET


def gan_chong(a: str, b: str) -> bool:
    """天干七冲：甲庚 / 乙辛 / 丙壬 / 丁癸 (戊己土不冲)。"""
    pairs = {frozenset(["甲", "庚"]), frozenset(["乙", "辛"]),
             frozenset(["丙", "壬"]), frozenset(["丁", "癸"])}
    return frozenset([a, b]) in pairs


# ============================================================
# 三、穿（六害）
# ============================================================

ZHI_CHUAN_PAIRS: list[tuple[str, str]] = [
    ("子", "未"),
    ("丑", "午"),
    ("寅", "巳"),
    ("卯", "辰"),
    ("申", "亥"),
    ("酉", "戌"),
]

ZHI_CHUAN_SET: set[frozenset[str]] = {frozenset(p) for p in ZHI_CHUAN_PAIRS}


def is_zhi_chuan(a: str, b: str) -> bool:
    return frozenset([a, b]) in ZHI_CHUAN_SET


# ============================================================
# 四、刑
# ============================================================
# 任派只认两组三刑：寅巳申 / 丑戌未
# 子卯归"破"；辰午酉亥归"自刑"（盲派一般不重视）

SAN_XING_GROUPS: list[set[str]] = [
    {"寅", "巳", "申"},
    {"丑", "戌", "未"},
]


def is_sanxing_full(zhi_set: set[str]) -> bool:
    """三字是否构成完整三刑。"""
    return any(grp <= zhi_set for grp in SAN_XING_GROUPS)


def is_xing_pair(a: str, b: str) -> bool:
    """两支是否互刑（在三刑组合内）。"""
    for grp in SAN_XING_GROUPS:
        if {a, b} <= grp and a != b:
            return True
    # 子卯互刑（按 §15.9 归破，但 §15.11 后段也含 "刑" 含义；为完整起见保留）
    if {a, b} == {"子", "卯"}:
        return True
    return False


def is_zixing(a: str, b: str) -> bool:
    """自刑（同字相见）：辰辰 / 午午 / 酉酉 / 亥亥。"""
    if a != b:
        return False
    return a in {"辰", "午", "酉", "亥"}


# ============================================================
# 五、暗合（盲派 4 组）
# ============================================================
# m3-mechanics §15.5：寅丑 / 午亥 / 卯申 / 子巳

ZHI_AN_HE_PAIRS: set[frozenset[str]] = {
    frozenset(["寅", "丑"]),
    frozenset(["午", "亥"]),
    frozenset(["卯", "申"]),
    frozenset(["子", "巳"]),
}


def is_zhi_anhe(a: str, b: str) -> bool:
    return frozenset([a, b]) in ZHI_AN_HE_PAIRS


# ============================================================
# 六、综合关系判定 (返回所有作用类型)
# ============================================================


def all_zhi_relations(a: str, b: str) -> list[str]:
    """返回两支之间所有作用关系列表（合 / 冲 / 穿 / 刑 / 暗合 / 半合 / 自刑）。"""
    rels: list[str] = []
    if a == b:
        if is_zixing(a, b):
            rels.append("自刑")
        else:
            rels.append("伏吟")
        return rels
    if is_zhi_liuhe(a, b):
        rels.append("六合")
    if is_banhe(a, b):
        rels.append("半合")
    if is_zhi_chong(a, b):
        rels.append("冲")
    if is_zhi_chuan(a, b):
        rels.append("穿")
    if is_xing_pair(a, b):
        rels.append("刑")
    if is_zhi_anhe(a, b):
        rels.append("暗合")
    return rels


def gan_relations(a: str, b: str) -> list[str]:
    """两个天干的关系。"""
    rels: list[str] = []
    if a == b:
        rels.append("伏吟")
        return rels
    if is_gan_he(a, b):
        rels.append("合")
    if gan_chong(a, b):
        rels.append("冲")
    return rels


# ============================================================
# 七、smoke test
# ============================================================


def _smoke() -> None:
    # 天干合
    assert is_gan_he("甲", "己")
    assert is_gan_he("丁", "壬")
    assert not is_gan_he("甲", "庚")

    # 地支合
    assert is_zhi_liuhe("子", "丑")
    assert is_zhi_liuhe("寅", "亥")
    assert not is_zhi_liuhe("子", "午")

    # 冲
    assert is_zhi_chong("子", "午")
    assert is_zhi_chong("寅", "申")
    assert is_zhi_chong("辰", "戌")
    assert not is_zhi_chong("寅", "巳")

    # 穿
    assert is_zhi_chuan("子", "未")
    assert is_zhi_chuan("酉", "戌")
    assert not is_zhi_chuan("子", "丑")

    # 刑
    assert is_xing_pair("寅", "巳")
    assert is_xing_pair("巳", "申")
    assert is_xing_pair("丑", "戌")
    assert is_zixing("辰", "辰")
    assert not is_zixing("子", "子")  # 子非辰午酉亥四自刑

    # 三合 / 半合
    ok, wx = is_sanhe_full({"申", "子", "辰"})
    assert ok and wx == "水"
    assert is_banhe("申", "子")
    assert is_banhe("子", "辰")
    assert not is_banhe("申", "辰")  # 中神不在

    # 暗合
    assert is_zhi_anhe("子", "巳")
    assert is_zhi_anhe("卯", "申")

    # 综合
    rels = all_zhi_relations("辰", "酉")
    assert "六合" in rels

    rels = all_zhi_relations("申", "申")
    assert "伏吟" in rels

    print("predicates.relations smoke OK")


if __name__ == "__main__":
    _smoke()
