"""engine.predicates.ganzhi · 干支基础

提供：
- 10 天干 / 12 地支常量
- 五行映射
- 阴阳判定
- 地支藏干（人元三元）
- 十神判定
- 公历年份 ↔ 干支换算（公元 4 年 = 甲子）

注：本文件是 Track-C bootstrap 的基础（任务原本声称 Track-A 应已交付）。
"""

from __future__ import annotations

from typing import Optional


# ============================================================
# 一、常量
# ============================================================

TIANGAN = "甲乙丙丁戊己庚辛壬癸"
DIZHI = "子丑寅卯辰巳午未申酉戌亥"

# 五行
WUXING = ("木", "火", "土", "金", "水")

# 天干 → 五行
GAN_WUXING: dict[str, str] = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 地支 → 五行
ZHI_WUXING: dict[str, str] = {
    "子": "水", "亥": "水",
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
}

# 天干阴阳（甲丙戊庚壬 = 阳）
GAN_YINYANG: dict[str, str] = {
    "甲": "阳", "乙": "阴",
    "丙": "阳", "丁": "阴",
    "戊": "阳", "己": "阴",
    "庚": "阳", "辛": "阴",
    "壬": "阳", "癸": "阴",
}

# 地支阴阳（子寅辰午申戌 = 阳）
ZHI_YINYANG: dict[str, str] = {
    "子": "阳", "丑": "阴",
    "寅": "阳", "卯": "阴",
    "辰": "阳", "巳": "阴",
    "午": "阳", "未": "阴",
    "申": "阳", "酉": "阴",
    "戌": "阳", "亥": "阴",
}

# 地支藏干（人元）—— 主气在前
# 参见 m3-foundation §11 三元论命
ZHI_CANGGAN: dict[str, list[str]] = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# 五行生克
WUXING_SHENG: dict[str, str] = {  # A 生 B
    "木": "火", "火": "土", "土": "金", "金": "水", "水": "木",
}
WUXING_KE: dict[str, str] = {  # A 克 B
    "木": "土", "土": "水", "水": "火", "火": "金", "金": "木",
}


# ============================================================
# 二、基础工具
# ============================================================


def is_gan(ch: str) -> bool:
    return ch in TIANGAN


def is_zhi(ch: str) -> bool:
    return ch in DIZHI


def get_wuxing(ch: str) -> str:
    """取一个干或支的五行。"""
    if ch in GAN_WUXING:
        return GAN_WUXING[ch]
    if ch in ZHI_WUXING:
        return ZHI_WUXING[ch]
    raise ValueError(f"未知干支字符: {ch!r}")


def get_yinyang(ch: str) -> str:
    if ch in GAN_YINYANG:
        return GAN_YINYANG[ch]
    if ch in ZHI_YINYANG:
        return ZHI_YINYANG[ch]
    raise ValueError(f"未知干支字符: {ch!r}")


def get_canggan(zhi: str) -> list[str]:
    """取地支的人元藏干（主气在前）。"""
    if zhi not in ZHI_CANGGAN:
        raise ValueError(f"未知地支: {zhi!r}")
    return list(ZHI_CANGGAN[zhi])


def is_yang(ch: str) -> bool:
    return get_yinyang(ch) == "阳"


def is_yin(ch: str) -> bool:
    return get_yinyang(ch) == "阴"


# ============================================================
# 三、五行生克查询
# ============================================================


def is_sheng(a: str, b: str) -> bool:
    """五行 a 是否生 b（a/b 可以是干或支或五行字符）。"""
    wa = get_wuxing(a) if a in GAN_WUXING or a in ZHI_WUXING else a
    wb = get_wuxing(b) if b in GAN_WUXING or b in ZHI_WUXING else b
    return WUXING_SHENG.get(wa) == wb


def is_ke(a: str, b: str) -> bool:
    """五行 a 是否克 b。"""
    wa = get_wuxing(a) if a in GAN_WUXING or a in ZHI_WUXING else a
    wb = get_wuxing(b) if b in GAN_WUXING or b in ZHI_WUXING else b
    return WUXING_KE.get(wa) == wb


def is_same_wuxing(a: str, b: str) -> bool:
    return get_wuxing(a) == get_wuxing(b)


# ============================================================
# 四、十神判定（以日干为我）
# ============================================================

# 十神 = (我五行/对方五行 关系) × (我阴阳/对方阴阳 同/异)
# 同我同阴阳 = 比肩；同我异阴阳 = 劫财
# 我生同阴阳 = 食神；我生异阴阳 = 伤官
# 我克同阴阳 = 偏财；我克异阴阳 = 正财
# 克我同阴阳 = 七杀；克我异阴阳 = 正官
# 生我同阴阳 = 偏印；生我异阴阳 = 正印
SHISHEN_NAMES = (
    "比肩", "劫财", "食神", "伤官", "偏财", "正财",
    "七杀", "正官", "偏印", "正印",
)


def get_shishen(day_gan: str, target: str) -> str:
    """取 target（干或支藏干主气）相对日干的十神。

    若 target 是地支 → 用其主气藏干判十神。
    """
    if target in GAN_WUXING:
        # 直接是天干
        target_gan = target
    elif target in ZHI_CANGGAN:
        # 地支 → 取主气
        target_gan = ZHI_CANGGAN[target][0]
    else:
        raise ValueError(f"未知 target: {target!r}")

    me_wx = GAN_WUXING[day_gan]
    me_yy = GAN_YINYANG[day_gan]
    t_wx = GAN_WUXING[target_gan]
    t_yy = GAN_YINYANG[target_gan]
    same_yy = (me_yy == t_yy)

    if me_wx == t_wx:
        return "比肩" if same_yy else "劫财"
    if WUXING_SHENG[me_wx] == t_wx:  # 我生
        return "食神" if same_yy else "伤官"
    if WUXING_KE[me_wx] == t_wx:  # 我克
        return "偏财" if same_yy else "正财"
    if WUXING_KE[t_wx] == me_wx:  # 克我
        return "七杀" if same_yy else "正官"
    if WUXING_SHENG[t_wx] == me_wx:  # 生我
        return "偏印" if same_yy else "正印"
    raise RuntimeError(f"无法判定十神: day={day_gan} target={target}")


def get_shishen_class(shishen: str) -> str:
    """十神 → 类别（财/官/印/食/比 五大类）。"""
    if shishen in {"正财", "偏财"}:
        return "财"
    if shishen in {"正官", "七杀"}:
        return "官"
    if shishen in {"正印", "偏印"}:
        return "印"
    if shishen in {"食神", "伤官"}:
        return "食伤"
    if shishen in {"比肩", "劫财"}:
        return "比劫"
    raise ValueError(f"未知十神: {shishen!r}")


# ============================================================
# 五、年份 ↔ 干支换算
# ============================================================
# 任务规定：公元 4 年 = 甲子年（与现代万年历一致：1984=甲子，1984-4=1980 整 60 倍数）。


def year_to_ganzhi(year: int) -> tuple[str, str]:
    """公历年份 → (天干, 地支)。

    >>> year_to_ganzhi(1980)
    ('庚', '申')
    >>> year_to_ganzhi(2005)
    ('乙', '酉')
    >>> year_to_ganzhi(2024)
    ('甲', '辰')
    """
    offset = year - 4  # 公元 4 年 = 甲子
    gan = TIANGAN[offset % 10]
    zhi = DIZHI[offset % 12]
    return gan, zhi


def year_to_pillar_str(year: int) -> str:
    g, z = year_to_ganzhi(year)
    return f"{g}{z}"


# ============================================================
# 六、smoke test
# ============================================================


def _smoke() -> None:
    # 五行
    assert get_wuxing("壬") == "水"
    assert get_wuxing("子") == "水"
    assert get_wuxing("辰") == "土"

    # 阴阳
    assert is_yang("甲")
    assert is_yin("乙")
    assert is_yang("子")  # 子为阳支
    assert is_yin("丑")

    # 藏干
    assert get_canggan("寅") == ["甲", "丙", "戊"]
    assert get_canggan("子") == ["癸"]
    assert get_canggan("辰") == ["戊", "乙", "癸"]

    # 十神（壬日干）
    assert get_shishen("壬", "丙") == "偏财"  # 壬克丙 同阳
    assert get_shishen("壬", "丁") == "正财"  # 壬克丁 异
    assert get_shishen("壬", "戊") == "七杀"  # 戊克壬 同阳
    assert get_shishen("壬", "己") == "正官"
    assert get_shishen("壬", "庚") == "偏印"  # 庚生壬 同阳
    assert get_shishen("壬", "辛") == "正印"
    assert get_shishen("壬", "甲") == "食神"  # 壬生甲 同阳
    assert get_shishen("壬", "癸") == "劫财"  # 同水异阴阳

    # 地支十神（取主气藏干）
    assert get_shishen("壬", "寅") == "食神"  # 寅主气甲
    assert get_shishen("壬", "子") == "劫财"  # 子主气癸

    # 五行生克
    assert is_sheng("水", "木")
    assert is_ke("水", "火")
    assert is_ke("壬", "丙")  # 水克火

    # 年份换算（任务里关键的几个）
    assert year_to_ganzhi(1980) == ("庚", "申"), year_to_ganzhi(1980)
    assert year_to_ganzhi(1982) == ("壬", "戌")
    assert year_to_ganzhi(2005) == ("乙", "酉")
    assert year_to_ganzhi(2006) == ("丙", "戌")
    assert year_to_ganzhi(2013) == ("癸", "巳")
    assert year_to_ganzhi(2020) == ("庚", "子")
    assert year_to_ganzhi(2024) == ("甲", "辰")
    assert year_to_ganzhi(2026) == ("丙", "午")

    # 十神类别
    assert get_shishen_class("偏财") == "财"
    assert get_shishen_class("正官") == "官"
    assert get_shishen_class("食神") == "食伤"

    print("predicates.ganzhi smoke OK")


if __name__ == "__main__":
    _smoke()
