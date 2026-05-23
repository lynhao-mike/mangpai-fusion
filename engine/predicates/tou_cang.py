"""engine.predicates.tou_cang · 透藏谓词

按契约 02 § 4.6 实现 5 个函数。透藏是 6 触发"藏干透出"的判定基础。

定义：
- 藏 = 某天干隐藏在某地支的人元三元中
- 透 = 该天干显式出现在四柱天干 / 大运天干 / 流年天干
"""

from __future__ import annotations

from typing import Optional

from .ganzhi import get_canggan
from .types import Bazi, ParsedInput
from .cycles import liunian_ganzhi, get_dayun_at_year


# ============================================================
# 1) is_canggan
# ============================================================


def is_canggan(gan: str, zhi: str) -> bool:
    """gan 是否藏在 zhi 的人元中。

    >>> is_canggan('丙', '寅')
    True
    >>> is_canggan('癸', '子')
    True
    >>> is_canggan('甲', '酉')
    False
    """
    return gan in get_canggan(zhi)


# ============================================================
# 2) is_tou
# ============================================================


def is_tou(gan: str, parsed: ParsedInput) -> bool:
    """某天干是否透在原局四柱天干。

    >>> # 庚申戊寅壬子辛丑 → 庚 / 戊 / 壬 / 辛 透
    """
    return gan in parsed.bazi.all_gans()


# ============================================================
# 3) tou_chu
# ============================================================


def tou_chu(canggan: str, parsed: ParsedInput, year: Optional[int] = None) -> dict:
    """藏干 canggan 是否"透出"。

    透出范围（按 m3-mechanics §17 第 5 条 "藏干透出"）：
      - 透在原局四柱天干 (always)
      - 透在大运天干 (year 给出时)
      - 透在流年天干 (year 给出时)

    返回 dict:
        {
            "tou_chu": True / False,
            "in_yuanju": [位置..., ...],
            "in_dayun": True / False,
            "in_liunian": True / False,
        }
    """
    in_yuanju: list[str] = []
    pillar_names = ["年干", "月干", "日干", "时干"]
    for name, g in zip(pillar_names, parsed.bazi.all_gans()):
        if g == canggan:
            in_yuanju.append(name)

    in_dayun = False
    in_liunian = False
    if year is not None:
        dy = get_dayun_at_year(parsed, year)
        if dy is not None and dy.gan == canggan:
            in_dayun = True
        ln_g, _ = liunian_ganzhi(year)
        if ln_g == canggan:
            in_liunian = True

    return {
        "tou_chu": bool(in_yuanju) or in_dayun or in_liunian,
        "in_yuanju": in_yuanju,
        "in_dayun": in_dayun,
        "in_liunian": in_liunian,
    }


# ============================================================
# 4) get_all_tou_chars
# ============================================================


def get_all_tou_chars(parsed: ParsedInput, year: Optional[int] = None) -> list[str]:
    """取此 (parsed, year) 配置下所有透出的天干（去重）。"""
    chars: set[str] = set(parsed.bazi.all_gans())
    if year is not None:
        dy = get_dayun_at_year(parsed, year)
        if dy is not None:
            chars.add(dy.gan)
        ln_g, _ = liunian_ganzhi(year)
        chars.add(ln_g)
    return sorted(chars)


# ============================================================
# 5) is_tou_at
# ============================================================


def is_tou_at(canggan: str, parsed: ParsedInput, year: int) -> dict:
    """藏干在指定年份"刚好新透出来"——即只在大运 or 流年透出，原局未透。

    用途：6 触发"藏干透出"的精确判定（关键应期信号）。
    """
    detail = tou_chu(canggan, parsed, year)
    new_at_dayun = detail["in_dayun"] and not detail["in_yuanju"]
    new_at_liunian = detail["in_liunian"] and not detail["in_yuanju"]
    return {
        "is_new_tou": new_at_dayun or new_at_liunian,
        "via_dayun": new_at_dayun,
        "via_liunian": new_at_liunian,
        "already_in_yuanju": bool(detail["in_yuanju"]),
    }


# ============================================================
# 辅助：原局藏干清单
# ============================================================


def collect_canggan_in_yuanju(parsed: ParsedInput) -> dict[str, list[str]]:
    """原局四柱地支的所有藏干，去重并标位置。

    返回 {藏干字: [位置1, 位置2, ...]}
    位置如 '年支:庚' / '月支:丙' 表示该藏干来自哪一柱。
    """
    pillar_names = ["年支", "月支", "日支", "时支"]
    out: dict[str, list[str]] = {}
    for name, z in zip(pillar_names, parsed.bazi.all_zhis()):
        for cg in get_canggan(z):
            out.setdefault(cg, []).append(f"{name}({z})")
    return out


# ============================================================
# smoke test
# ============================================================


def _smoke() -> None:
    from .types import Bazi, Pillar, Dayun, ParsedInput

    bz = Bazi.parse("庚申", "戊寅", "壬子", "辛丑")
    dayuns = [
        Dayun(Pillar.parse("庚辰"), 18, 28, 1998, 2008),
        Dayun(Pillar.parse("辛巳"), 28, 38, 2008, 2018),
        Dayun(Pillar.parse("壬午"), 38, 48, 2018, 2028),
    ]
    pi = ParsedInput(gender="男", birth_year=1980, bazi=bz, dayun_list=dayuns)

    # is_canggan
    assert is_canggan("丙", "寅")  # 寅藏甲丙戊
    assert is_canggan("辛", "丑")  # 丑藏己癸辛
    assert not is_canggan("甲", "酉")  # 酉只藏辛

    # is_tou
    assert is_tou("庚", pi)  # 庚透在年干
    assert is_tou("壬", pi)  # 壬日干
    assert not is_tou("乙", pi)  # 乙不透原局

    # tou_chu - 2005 乙酉 (大运庚辰)
    # 乙：藏在原局辰？不藏。藏在大运辰里 → in_dayun?  Wait, 大运是庚辰，gan=庚 不是乙。
    # 流年是乙酉，gan=乙 → in_liunian=True
    info = tou_chu("乙", pi, 2005)
    assert info["in_liunian"] is True
    assert info["in_yuanju"] == []
    assert info["in_dayun"] is False
    assert info["tou_chu"] is True

    # 庚 在原局年干 + 大运庚辰 → 双透
    info = tou_chu("庚", pi, 2005)
    assert info["in_yuanju"] == ["年干"]
    assert info["in_dayun"] is True

    # 丙：原局月支寅藏丙，丙未透在 2005 → tou_chu=False
    info = tou_chu("丙", pi, 2005)
    assert info["tou_chu"] is False
    info = tou_chu("丙", pi, 2026)  # 2026 丙午，丙透在流年
    assert info["in_liunian"] is True
    assert info["tou_chu"] is True

    # get_all_tou_chars
    chars_2005 = get_all_tou_chars(pi, 2005)
    assert "庚" in chars_2005 and "戊" in chars_2005 and "壬" in chars_2005 and "辛" in chars_2005
    assert "乙" in chars_2005  # 流年
    # 2005 大运庚辰 gan=庚（已在原局集合）
    chars_no_year = get_all_tou_chars(pi)
    assert "乙" not in chars_no_year

    # is_tou_at - 关键应期信号
    info = is_tou_at("乙", pi, 2005)
    assert info["is_new_tou"] is True
    assert info["via_liunian"] is True
    assert info["already_in_yuanju"] is False

    # 庚在原局已透 → not new
    info = is_tou_at("庚", pi, 2005)
    assert info["is_new_tou"] is False
    assert info["already_in_yuanju"] is True

    # 收集原局藏干
    cangs = collect_canggan_in_yuanju(pi)
    assert "丙" in cangs  # 寅藏丙
    assert "癸" in cangs  # 子主气 + 丑藏 + 应该有
    assert "戊" in cangs  # 寅 / 申中藏戊

    print("predicates.tou_cang smoke OK")


if __name__ == "__main__":
    _smoke()
