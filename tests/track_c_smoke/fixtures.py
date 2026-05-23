"""Track-C smoke test fixtures.

为 C-2026-001 / C-2026-002 / C-2026-014 三个回归案例提供
ParsedInput + EnergyFindings + PictureFindings 的固定构造。

数据来源：
- cases/C-2026-001/input.md   (1980-02-09 男 庚申戊寅壬子辛丑)
- cases/C-2026-002/input.md   (1982-10-12 女 壬戌庚戌戊辰丙辰)
- cases/C-2026-014/input.md   (2006-12-12 男 丙戌庚子乙亥辛巳)

注：上游 Track-A/B 尚未交付，本 fixtures 中的 EnergyFindings / PictureFindings
是按 case feedback.md 的 ground truth 反向构造的"oracle 上游"。
Track-A/B 完整实现后，应替换这些 fixture 为真实 evaluator/matcher 的输出。
"""

from __future__ import annotations

from engine.energy.types import EnergyFindings
from engine.picture.types import (
    PictureFindings, MarriagePicture, CareerPicture, EducationPicture,
)
from engine.predicates.types import Bazi, Pillar, Dayun, ParsedInput


# ============================================================
# C-2026-001 · 男 1980-02-09 02:00 · 庚申戊寅壬子辛丑
# 真实婚年 = 2005，子 = 2006，提副科 = 2020
# ============================================================


def parsed_C001() -> ParsedInput:
    bz = Bazi.parse("庚申", "戊寅", "壬子", "辛丑")
    dayuns = [
        Dayun(Pillar.parse("己卯"),  8, 18, 1988, 1998),
        Dayun(Pillar.parse("庚辰"), 18, 28, 1998, 2008),
        Dayun(Pillar.parse("辛巳"), 28, 38, 2008, 2018),
        Dayun(Pillar.parse("壬午"), 38, 48, 2018, 2028),
        Dayun(Pillar.parse("癸未"), 48, 58, 2028, 2038),
        Dayun(Pillar.parse("甲申"), 58, 68, 2038, 2048),
    ]
    return ParsedInput(gender="男", birth_year=1980, bazi=bz, dayun_list=dayuns)


def energy_C001() -> EnergyFindings:
    """模拟 Track-A 段派 D1 输出。

    C-001 是杀印相生格，财弱（丙藏寅被冲），层级 L2-L3。
    """
    return EnergyFindings(
        bazi_str="庚申戊寅壬子辛丑",
        marriage_capable=True,    # 有妻宫子 + 财根（藏丙）
        career_capable=True,      # 杀印相生
        wealth_capable=True,      # 财弱但能成
        health_capable=True,
        education_capable=True,
        energy_level=2,
        domain_yong_shen={
            "婚姻": ["丙", "丁", "子"],   # 财 + 妻宫
            "事业": ["戊", "己", "庚", "辛"],  # 官 + 印
            "六亲": ["庚", "辛"],          # 印=母
            "学业": ["庚", "辛", "甲"],    # 印 + 食神
        },
        upstream_hash="C001-energy-stub",
    )


def picture_C001() -> PictureFindings:
    """模拟 Track-B 杨派 D2 输出。

    根据 feedback ground truth：婚姻 2005 年（25 岁）→ 最佳窗口 [23, 28]。
    """
    mp = MarriagePicture(
        best_window=(23, 28),         # 25 岁结婚 → 中靶
        secondary_window=(20, 22),    # 容差
        expected_status="稳定",
        spouse_keywords=["公职", "强势", "家境优越"],
        confidence=0.78,
    )
    cp = CareerPicture(
        rising_windows=[(38, 48)],   # 壬午运 = 事业上升
        domain_keywords=["公门", "国企", "正科级"],
        confidence=0.72,
    )
    ep = EducationPicture(
        expected_level="高级·下等",  # 二本
        key_year_window=(17, 19),
        confidence=0.7,
    )
    return PictureFindings(
        bazi_str="庚申戊寅壬子辛丑",
        marriage_picture=mp,
        career_picture=cp,
        education_picture=ep,
        upstream_hash="C001-picture-stub",
    )


# ============================================================
# C-2026-002 · 女 1982-10-12 07:20 · 壬戌庚戌戊辰丙辰
# ============================================================


def parsed_C002() -> ParsedInput:
    bz = Bazi.parse("壬戌", "庚戌", "戊辰", "丙辰")
    dayuns = [
        Dayun(Pillar.parse("己酉"),  2, 12, 1983, 1993),
        Dayun(Pillar.parse("戊申"), 12, 22, 1993, 2003),
        Dayun(Pillar.parse("丁未"), 22, 32, 2003, 2013),
        Dayun(Pillar.parse("丙午"), 32, 42, 2013, 2023),
        Dayun(Pillar.parse("乙巳"), 42, 52, 2023, 2033),
    ]
    return ParsedInput(gender="女", birth_year=1982, bazi=bz, dayun_list=dayuns)


def energy_C002() -> EnergyFindings:
    return EnergyFindings(
        bazi_str="壬戌庚戌戊辰丙辰",
        marriage_capable=True,
        career_capable=True,
        wealth_capable=True,
        health_capable=True,
        education_capable=True,
        energy_level=2,
        domain_yong_shen={
            "婚姻": ["甲", "乙", "辰"],   # 戊日干，官=甲乙；夫宫=辰
            "事业": ["甲", "乙", "丙", "丁"],
        },
        upstream_hash="C002-energy-stub",
    )


def picture_C002() -> PictureFindings:
    """C-002 婚姻 2005 年（23 岁）→ 最佳窗口 [21, 26]。"""
    mp = MarriagePicture(
        best_window=(21, 26),
        secondary_window=(27, 30),
        expected_status="稳定",
        spouse_keywords=["体制内", "靠妻方提拔"],
        confidence=0.72,
    )
    return PictureFindings(
        bazi_str="壬戌庚戌戊辰丙辰",
        marriage_picture=mp,
        upstream_hash="C002-picture-stub",
    )


# ============================================================
# C-2026-014 · 男 2006-12-12 09:45 · 丙戌庚子乙亥辛巳
# 高考 2024 年（17 岁）
# ============================================================


def parsed_C014() -> ParsedInput:
    bz = Bazi.parse("丙戌", "庚子", "乙亥", "辛巳")
    dayuns = [
        Dayun(Pillar.parse("辛丑"), 15, 25, 2021, 2031),
        Dayun(Pillar.parse("壬寅"), 25, 35, 2031, 2041),
        Dayun(Pillar.parse("癸卯"), 35, 45, 2041, 2051),
        Dayun(Pillar.parse("甲辰"), 45, 55, 2051, 2061),
    ]
    return ParsedInput(gender="男", birth_year=2006, bazi=bz, dayun_list=dayuns)


def energy_C014() -> EnergyFindings:
    """C-014 是正官格官印相生 + 印独生身。"""
    return EnergyFindings(
        bazi_str="丙戌庚子乙亥辛巳",
        marriage_capable=True,
        career_capable=True,
        wealth_capable=True,
        health_capable=True,
        education_capable=True,
        energy_level=3,
        domain_yong_shen={
            "学业": ["壬", "癸", "丙", "丁"],   # 乙日干 印=壬癸 食伤=丙丁
            "事业": ["庚", "辛", "壬", "癸"],   # 官 + 印
        },
        upstream_hash="C014-energy-stub",
    )


def picture_C014() -> PictureFindings:
    """C-014 高考 2024 年 17 岁 → key_year_window [17, 19]。"""
    mp = MarriagePicture(
        best_window=(25, 32),
        expected_status="未知",
        confidence=0.55,
    )
    cp = CareerPicture(
        rising_windows=[(25, 35)],
        domain_keywords=["审计", "财经", "执业"],
        confidence=0.65,
    )
    ep = EducationPicture(
        expected_level="高级·上等",
        key_year_window=(17, 19),  # 17 岁高考命中
        confidence=0.78,
    )
    return PictureFindings(
        bazi_str="丙戌庚子乙亥辛巳",
        marriage_picture=mp,
        career_picture=cp,
        education_picture=ep,
        upstream_hash="C014-picture-stub",
    )
