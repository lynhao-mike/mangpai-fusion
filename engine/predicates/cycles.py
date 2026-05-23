"""engine.predicates.cycles · 大运流年谓词

按契约 02 § 4.5 实现 9 个函数。所有应期判定的基础。

注：契约 02 文档尚未交付（仅 00/09 已写）；本实现按任务说明 §阶段 1 与
m3-mechanics §17/§18 的语义建模，命名与签名向 02 契约靠齐。
"""

from __future__ import annotations

from typing import Optional

from .ganzhi import year_to_ganzhi, get_canggan
from .relations import (
    is_gan_he,
    is_zhi_liuhe,
    is_zhi_chong,
    is_banhe,
    gan_relations,
    all_zhi_relations,
)
from .types import Bazi, Dayun, ParsedInput


# ============================================================
# 1) get_dayun_at_age / get_dayun_at_year
# ============================================================


def get_dayun_at_age(parsed: ParsedInput, age: int) -> Optional[Dayun]:
    """命主 age 岁时所在的大运。无（含起运前）则返回 None。"""
    for dy in parsed.dayun_list:
        if dy.covers_age(age):
            return dy
    return None


def get_dayun_at_year(parsed: ParsedInput, year: int) -> Optional[Dayun]:
    """命主在 year 公历年所在的大运。"""
    for dy in parsed.dayun_list:
        if dy.covers_year(year):
            return dy
    return None


# ============================================================
# 2) liunian_ganzhi
# ============================================================


def liunian_ganzhi(year: int) -> tuple[str, str]:
    """公历年份 → 流年干支。

    >>> liunian_ganzhi(2005)
    ('乙', '酉')
    >>> liunian_ganzhi(2013)
    ('癸', '巳')
    >>> liunian_ganzhi(2024)
    ('甲', '辰')
    """
    return year_to_ganzhi(year)


# ============================================================
# 3) is_dayun_zhi_chong_bazi
# ============================================================


def is_dayun_zhi_chong_bazi(parsed: ParsedInput, year: int) -> dict:
    """大运地支与原局四柱地支的冲关系列表。

    返回 dict:
        {
            "is_chong": True/False,
            "chong_with": ["申"...],     # 大运地支与原局哪些字相冲
            "dayun_zhi": "辰",
        }
    """
    dy = get_dayun_at_year(parsed, year)
    if dy is None:
        return {"is_chong": False, "chong_with": [], "dayun_zhi": ""}
    dyz = dy.zhi
    chong_targets: list[str] = []
    for z in parsed.bazi.all_zhis():
        if is_zhi_chong(dyz, z):
            chong_targets.append(z)
    return {
        "is_chong": bool(chong_targets),
        "chong_with": chong_targets,
        "dayun_zhi": dyz,
    }


# ============================================================
# 4) is_liunian_with_dayun_he
# ============================================================


def is_liunian_with_dayun_he(parsed: ParsedInput, year: int) -> dict:
    """流年与大运的合关系（天干合 / 地支合 / 半合）。"""
    dy = get_dayun_at_year(parsed, year)
    if dy is None:
        return {"gan_he": False, "zhi_liuhe": False, "zhi_banhe": False}
    ln_g, ln_z = liunian_ganzhi(year)
    return {
        "gan_he": is_gan_he(dy.gan, ln_g),
        "zhi_liuhe": is_zhi_liuhe(dy.zhi, ln_z),
        "zhi_banhe": is_banhe(dy.zhi, ln_z),
    }


# ============================================================
# 5) is_liunian_with_bazi_he
# ============================================================


def is_liunian_with_bazi_he(parsed: ParsedInput, year: int) -> dict:
    """流年与原局四柱的合关系。

    返回所有合点（天干合或地支合）。
    """
    ln_g, ln_z = liunian_ganzhi(year)
    gan_he_with: list[str] = []
    zhi_he_with: list[str] = []
    for g in parsed.bazi.all_gans():
        if is_gan_he(ln_g, g):
            gan_he_with.append(g)
    for z in parsed.bazi.all_zhis():
        if is_zhi_liuhe(ln_z, z):
            zhi_he_with.append(z)
    return {
        "any_he": bool(gan_he_with or zhi_he_with),
        "gan_he_with": gan_he_with,
        "zhi_he_with": zhi_he_with,
    }


# ============================================================
# 6) is_liunian_chong_bazi
# ============================================================


def is_liunian_chong_bazi(parsed: ParsedInput, year: int) -> dict:
    """流年地支冲原局四柱地支。"""
    _, ln_z = liunian_ganzhi(year)
    chong_with: list[str] = []
    for z in parsed.bazi.all_zhis():
        if is_zhi_chong(ln_z, z):
            chong_with.append(z)
    return {
        "is_chong": bool(chong_with),
        "chong_with": chong_with,
        "liunian_zhi": ln_z,
    }


# ============================================================
# 7) is_liunian_yingdong_bazi_zi
# ============================================================
# 引动 = 原局某字（含天干/地支/藏干）以本字、合、冲、刑、穿、伏吟之一被流年触发
# 这是判断"原局之事是否被流年点亮"的兜底函数


def is_liunian_yingdong_bazi_zi(parsed: ParsedInput, year: int, target_char: str) -> dict:
    """流年是否引动原局的某个字 target_char。

    引动方式：
      A) 流年带来 target_char 本字（liunian.gan == target 或 liunian.zhi == target）
      B) 流年与 target_char 形成合 / 冲 / 刑 / 穿 / 暗合 / 半合
      C) target_char 是某地支的藏干，且流年带出该地支或天干透出 target

    返回 {"yingdong": bool, "ways": [...], "explain": str}
    """
    if target_char not in parsed.bazi.all_chars():
        # 也许 target 是某地支的藏干，先检查
        is_canggan = False
        for z in parsed.bazi.all_zhis():
            if target_char in get_canggan(z):
                is_canggan = True
                break
        if not is_canggan:
            return {"yingdong": False, "ways": [], "explain": "target 不在原局"}

    ln_g, ln_z = liunian_ganzhi(year)
    ways: list[str] = []

    # A) 本字到
    if ln_g == target_char or ln_z == target_char:
        ways.append("本字到")

    # B) 形成关系
    # 流年干 vs target（若 target 是天干）
    if target_char in "甲乙丙丁戊己庚辛壬癸":
        rels = gan_relations(ln_g, target_char)
        for r in rels:
            ways.append(f"天干{r}")
    # 流年支 vs target（若 target 是地支）
    if target_char in "子丑寅卯辰巳午未申酉戌亥":
        rels = all_zhi_relations(ln_z, target_char)
        for r in rels:
            ways.append(f"地支{r}")

    return {
        "yingdong": bool(ways),
        "ways": ways,
        "explain": "; ".join(ways) if ways else "未引动",
    }


# ============================================================
# 8) find_year_when_zhi_appears
# ============================================================


def find_year_when_zhi_appears(start: int, end: int, target_zhi: str) -> list[int]:
    """在 [start, end] 闭区间内，找流年地支为 target_zhi 的所有年份。"""
    result: list[int] = []
    for y in range(start, end + 1):
        _, z = liunian_ganzhi(y)
        if z == target_zhi:
            result.append(y)
    return result


def find_year_when_gan_appears(start: int, end: int, target_gan: str) -> list[int]:
    """同上，按天干。"""
    result: list[int] = []
    for y in range(start, end + 1):
        g, _ = liunian_ganzhi(y)
        if g == target_gan:
            result.append(y)
    return result


# ============================================================
# 9) is_dayun_in_transition
# ============================================================
# 任务说明 §阶段 2 §threelayer：L2 必须含过渡期判定 ——
# 当前年距大运起讫 ±1 年内，相邻大运字也算


def get_transition_dayun_chars(parsed: ParsedInput, year: int) -> list[str]:
    """取 year 所在大运 + 过渡期内的相邻大运的所有字。

    过渡期 = 与当前大运起讫 ±1 年距离内。
    """
    chars: list[str] = []
    cur = get_dayun_at_year(parsed, year)
    if cur is None:
        return chars
    chars.extend([cur.gan, cur.zhi])

    # 找前一个 / 后一个大运
    idx = None
    for i, dy in enumerate(parsed.dayun_list):
        if dy is cur:
            idx = i
            break
    if idx is None:
        return chars

    # 过渡期：year 距 cur.start_year 或 cur.end_year - 1 都 ≤ 1
    if year - cur.start_year <= 1 and idx > 0:
        prev = parsed.dayun_list[idx - 1]
        chars.extend([prev.gan, prev.zhi])
    if cur.end_year - 1 - year <= 1 and idx < len(parsed.dayun_list) - 1:
        nxt = parsed.dayun_list[idx + 1]
        chars.extend([nxt.gan, nxt.zhi])
    return chars


# ============================================================
# smoke test
# ============================================================


def _smoke() -> None:
    from .types import Bazi, Pillar, Dayun, ParsedInput

    # C-2026-001 命主 1：庚申戊寅壬子辛丑，1980 生
    bz = Bazi.parse("庚申", "戊寅", "壬子", "辛丑")
    dayuns = [
        Dayun(Pillar.parse("己卯"), 8, 18, 1988, 1998),
        Dayun(Pillar.parse("庚辰"), 18, 28, 1998, 2008),
        Dayun(Pillar.parse("辛巳"), 28, 38, 2008, 2018),
        Dayun(Pillar.parse("壬午"), 38, 48, 2018, 2028),
    ]
    pi = ParsedInput(gender="男", birth_year=1980, bazi=bz, dayun_list=dayuns)

    # 流年干支
    assert liunian_ganzhi(2005) == ("乙", "酉")
    assert liunian_ganzhi(2013) == ("癸", "巳")

    # 大运定位
    dy_2005 = get_dayun_at_year(pi, 2005)
    assert dy_2005 is not None and dy_2005.gan == "庚" and dy_2005.zhi == "辰"
    dy_2013 = get_dayun_at_year(pi, 2013)
    assert dy_2013 is not None and dy_2013.gan == "辛" and dy_2013.zhi == "巳"

    # 大运冲原局
    chk = is_dayun_zhi_chong_bazi(pi, 2018)  # 壬午冲子
    assert chk["is_chong"] is True
    assert "子" in chk["chong_with"]

    # 流年合大运
    chk = is_liunian_with_dayun_he(pi, 2005)  # 乙酉 vs 庚辰：乙庚合 + 辰酉合
    assert chk["gan_he"] is True
    assert chk["zhi_liuhe"] is True

    # 流年合原局
    chk = is_liunian_with_bazi_he(pi, 2005)  # 乙酉
    # 乙合庚（年干）→ True
    assert "庚" in chk["gan_he_with"]

    # 流年冲原局
    chk = is_liunian_chong_bazi(pi, 2026)  # 丙午 → 午冲子
    assert chk["is_chong"] is True
    assert "子" in chk["chong_with"]

    # 引动：流年 2026 是否引动原局的"子"
    chk = is_liunian_yingdong_bazi_zi(pi, 2026, "子")
    assert chk["yingdong"] is True
    assert any("冲" in w for w in chk["ways"])

    # 找流年
    years = find_year_when_zhi_appears(2000, 2030, "辰")
    assert 2024 in years  # 甲辰年
    assert 2012 in years  # 壬辰年

    # 过渡期
    # 2017 在辛巳运（2008-2018）末年 → 应含 壬午（下一运）
    chars = get_transition_dayun_chars(pi, 2017)
    assert "辛" in chars and "巳" in chars
    assert "壬" in chars and "午" in chars  # 进入过渡

    print("predicates.cycles smoke OK")


if __name__ == "__main__":
    _smoke()
