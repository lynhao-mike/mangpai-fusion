"""engine.yingqi.keys · domain → 关键字映射表

按 m3-foundation §7"用神论命"建模：每个领域的关键字 = 核心十神类对应的字。

供 threelayer.py / chufa.py 使用：
- L1 检查这些关键字是否在原局存在
- L2 检查大运是否带来 / 引动这些字
- L3 检查流年是否引爆这些字
"""

from __future__ import annotations

from typing import Optional

from engine.energy.types import EnergyFindings
from engine.predicates.ganzhi import (
    TIANGAN, DIZHI, GAN_WUXING, ZHI_WUXING, ZHI_CANGGAN,
    get_shishen, get_shishen_class, WUXING_KE, WUXING_SHENG,
)
from engine.predicates.types import Bazi, ParsedInput
from engine.predicates.tou_cang import collect_canggan_in_yuanju


# ============================================================
# 一、domain → 主十神类（一阶映射）
# ============================================================
# 按 m3-foundation §7 多用神原则
#
# 标记：
#   primary  = 核心信号字（必须存在）
#   secondary = 辅助信号字（增强）
#
# 性别敏感的 domain（婚姻/六亲-配偶/六亲-子女）单独分支处理。

# 普适映射（所有 domain 默认包括 日支 = 主位）
DOMAIN_PRIMARY_SHISHEN: dict[str, list[str]] = {
    "事业": ["正官", "七杀", "正印", "偏印"],
    "财运": ["正财", "偏财", "食神", "伤官"],
    "健康": ["正印", "偏印"],   # 日主 / 印 / 禄 单独处理
    "学业": ["正印", "偏印", "食神", "伤官"],
    "其他": [],
}

DOMAIN_SECONDARY_SHISHEN: dict[str, list[str]] = {
    "事业": ["食神", "伤官", "正财", "偏财"],
    "财运": ["正官", "七杀", "比肩", "劫财"],
    "健康": ["食神", "伤官"],   # 食神为寿星
    "学业": ["正官", "七杀", "正财", "偏财"],
    "其他": [],
}


# 婚姻：男命看财（妻），女命看官（夫）
# 六亲-配偶 同理
def _hunyin_primary_shishen(gender: str) -> list[str]:
    if gender == "男":
        return ["正财", "偏财"]
    return ["正官", "七杀"]


def _hunyin_secondary_shishen(gender: str) -> list[str]:
    if gender == "男":
        # 男命无财时，看食伤（财源）；情敌看比劫
        return ["食神", "伤官", "比肩", "劫财"]
    # 女命：财（财生官）+ 印（化官 / 阴干女命特殊）
    return ["正财", "偏财", "正印", "偏印"]


# 六亲细分：父 / 母 / 兄弟 / 子女
LIUQIN_SUB_PRIMARY: dict[str, list[str]] = {
    "父": ["偏财"],
    "母": ["正印"],
    "兄弟": ["比肩", "劫财"],
    "子女": [],  # 男看官杀 / 女看食伤，性别分支
}


def _liuqin_zi_primary(gender: str) -> list[str]:
    return ["正官", "七杀"] if gender == "男" else ["食神", "伤官"]


# ============================================================
# 二、十神类 → 具体字（基于日干）
# ============================================================


def shishen_to_chars(day_gan: str, shishen: str) -> list[str]:
    """该十神对应的所有天干字（不含地支主气推导，仅本干）。

    注：地支字也可触发——通过 get_shishen 反查时，
    但本函数只返回天干字，地支由 _zhi_chars_for_shishen 提供。
    """
    out: list[str] = []
    for g in TIANGAN:
        if get_shishen(day_gan, g) == shishen:
            out.append(g)
    return out


def zhi_chars_for_shishen(day_gan: str, shishen: str) -> list[str]:
    """主气藏干十神对应的地支字。"""
    out: list[str] = []
    for z in DIZHI:
        if get_shishen(day_gan, z) == shishen:  # get_shishen 对地支返回主气十神
            out.append(z)
    return out


# ============================================================
# 三、对外 API
# ============================================================


def get_primary_keys(
    domain: str,
    bazi: Bazi,
    energy: Optional[EnergyFindings] = None,
    gender: str = "男",
    sub_domain: Optional[str] = None,
) -> list[str]:
    """领域的主关键字列表（去重，含天干 + 地支）。

    sub_domain 用于六亲：'父' / '母' / '兄弟' / '子女'
    """
    day_gan = bazi.day_gan
    shishen_list: list[str] = []
    chars: list[str] = []

    # 1) 选十神
    if domain == "婚姻":
        shishen_list = _hunyin_primary_shishen(gender)
        # 主位 = 妻宫 / 夫宫 = 日支
        chars.append(bazi.day_zhi)
    elif domain == "六亲":
        if sub_domain == "子女":
            shishen_list = _liuqin_zi_primary(gender)
            chars.append(bazi.hour.gan)
            chars.append(bazi.hour.zhi)  # 子女宫
        elif sub_domain == "配偶":
            shishen_list = _hunyin_primary_shishen(gender)
            chars.append(bazi.day_zhi)
        elif sub_domain in LIUQIN_SUB_PRIMARY:
            shishen_list = LIUQIN_SUB_PRIMARY[sub_domain]
            # 父=年柱、母=月柱、兄弟=月支
            if sub_domain == "父":
                chars.extend([bazi.year.gan, bazi.year.zhi])
            elif sub_domain == "母":
                chars.extend([bazi.month.gan, bazi.month.zhi])
            elif sub_domain == "兄弟":
                chars.append(bazi.month.zhi)
        else:
            # 通配六亲 = 父 + 母 + 配偶
            shishen_list = LIUQIN_SUB_PRIMARY["父"] + LIUQIN_SUB_PRIMARY["母"] \
                + _hunyin_primary_shishen(gender)
            chars.extend([bazi.year.gan, bazi.year.zhi,
                          bazi.month.gan, bazi.month.zhi,
                          bazi.day_zhi])
    elif domain == "健康":
        # 日主 / 日支 / 印 / 禄
        chars.append(day_gan)
        chars.append(bazi.day_zhi)
        shishen_list = DOMAIN_PRIMARY_SHISHEN.get(domain, [])
    else:
        shishen_list = DOMAIN_PRIMARY_SHISHEN.get(domain, [])

    # 2) 十神 → 具体字
    for ss in shishen_list:
        chars.extend(shishen_to_chars(day_gan, ss))
        chars.extend(zhi_chars_for_shishen(day_gan, ss))

    # 3) energy 提供的领域专属用神字（若有）
    if energy is not None and energy.domain_yong_shen.get(domain):
        chars.extend(energy.domain_yong_shen[domain])

    # 去重保序
    return _dedup(chars)


def get_secondary_keys(
    domain: str,
    bazi: Bazi,
    energy: Optional[EnergyFindings] = None,
    gender: str = "男",
    sub_domain: Optional[str] = None,
) -> list[str]:
    """领域的次关键字列表。"""
    day_gan = bazi.day_gan
    shishen_list: list[str] = []
    chars: list[str] = []

    if domain == "婚姻":
        shishen_list = _hunyin_secondary_shishen(gender)
    elif domain == "六亲":
        # 通用次关键字（父母配偶交叉）
        shishen_list = ["比肩", "劫财", "食神", "伤官"]
    else:
        shishen_list = DOMAIN_SECONDARY_SHISHEN.get(domain, [])

    for ss in shishen_list:
        chars.extend(shishen_to_chars(day_gan, ss))
        chars.extend(zhi_chars_for_shishen(day_gan, ss))

    return _dedup(chars)


def get_required_dayun_chars(
    domain: str,
    energy: Optional[EnergyFindings],
    parsed: ParsedInput,
    gender: Optional[str] = None,
    sub_domain: Optional[str] = None,
) -> list[str]:
    """L2 必需字：大运需要带来 / 引动哪些字才算"到位"。

    规则：
      - L2 至少需要触发 primary_keys 中任一个
      - 触发方式：大运带本字 / 大运合冲原局某 primary_key / 大运带其藏干透出
    """
    g = gender if gender is not None else parsed.gender
    return get_primary_keys(domain, parsed.bazi, energy, gender=g, sub_domain=sub_domain)


# ============================================================
# 四、辅助
# ============================================================


def _dedup(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in seq:
        if x and x not in seen:
            out.append(x)
            seen.add(x)
    return out


def chars_in_yuanju(chars: list[str], parsed: ParsedInput) -> list[str]:
    """这些字在原局（含藏干）中存在的子集。"""
    in_8 = set(parsed.bazi.all_chars())
    cangs = collect_canggan_in_yuanju(parsed)
    out: list[str] = []
    for c in chars:
        if c in in_8 or c in cangs:
            out.append(c)
    return out


# ============================================================
# smoke test
# ============================================================


def _smoke() -> None:
    from engine.predicates.types import Bazi, Pillar, Dayun, ParsedInput
    bz = Bazi.parse("庚申", "戊寅", "壬子", "辛丑")
    pi = ParsedInput(gender="男", birth_year=1980, bazi=bz, dayun_list=[])

    # 婚姻 男命 → 财 + 妻宫
    keys = get_primary_keys("婚姻", bz, None, gender="男")
    # 壬日干，正财=丁，偏财=丙；妻宫=子
    assert "丙" in keys, f"丙 not in {keys}"
    assert "丁" in keys
    assert "子" in keys  # 妻宫
    # 地支主气是财的：午（丁）、巳（丙）
    assert "巳" in keys
    assert "午" in keys

    # 婚姻 女命（戊日干）→ 官 + 夫宫
    bz2 = Bazi.parse("壬戌", "庚戌", "戊辰", "丙辰")
    keys = get_primary_keys("婚姻", bz2, None, gender="女")
    # 戊日干，正官=乙，七杀=甲；夫宫=辰
    assert "甲" in keys
    assert "乙" in keys
    assert "辰" in keys

    # 学业（壬日干）→ 印 + 食伤
    keys = get_primary_keys("学业", bz, None, gender="男")
    # 印 = 庚辛；食伤 = 甲乙
    assert "庚" in keys
    assert "辛" in keys
    assert "甲" in keys

    # 事业 → 官 + 印
    keys = get_primary_keys("事业", bz, None, gender="男")
    assert "戊" in keys  # 七杀
    assert "己" in keys  # 正官
    assert "庚" in keys  # 印

    # chars_in_yuanju
    sub = chars_in_yuanju(["丙", "丁", "庚", "壬", "癸"], pi)
    assert "丙" in sub  # 寅藏丙
    assert "庚" in sub  # 年干
    assert "壬" in sub  # 日干
    assert "癸" in sub  # 子主气 / 丑藏 / 辰藏

    # get_required_dayun_chars
    req = get_required_dayun_chars("婚姻", None, pi)
    assert "丙" in req
    assert "子" in req

    print("yingqi.keys smoke OK")


if __name__ == "__main__":
    _smoke()
