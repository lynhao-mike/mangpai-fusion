"""engine.predicates.types · 共用数据类型

按契约 01-input-schema 的核心字段建模。

注：v1.2 完整契约 01 / 03 尚未交付，本文件提供 Track-C 所需最小集。
后续 Track-A/B/D/E 可在此基础上扩展（不破坏向后兼容）。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


# ============================================================
# 一、四柱 / 大运 / 输入解析
# ============================================================


@dataclass(frozen=True)
class Pillar:
    """单柱（年/月/日/时）。"""

    gan: str   # 天干 (1 字)
    zhi: str   # 地支 (1 字)

    def __post_init__(self) -> None:
        if len(self.gan) != 1 or len(self.zhi) != 1:
            raise ValueError(f"Pillar 干支各必须为 1 字: gan={self.gan!r}, zhi={self.zhi!r}")

    def to_str(self) -> str:
        return f"{self.gan}{self.zhi}"

    @classmethod
    def parse(cls, s: str) -> "Pillar":
        """从 '甲子' 这样的 2 字字符串解析。"""
        s = s.strip()
        if len(s) != 2:
            raise ValueError(f"Pillar.parse 需要 2 字串: {s!r}")
        return cls(gan=s[0], zhi=s[1])


@dataclass(frozen=True)
class Bazi:
    """八字四柱（年-月-日-时）。"""

    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar

    @property
    def day_gan(self) -> str:
        return self.day.gan

    @property
    def day_zhi(self) -> str:
        return self.day.zhi

    def all_gans(self) -> list[str]:
        return [self.year.gan, self.month.gan, self.day.gan, self.hour.gan]

    def all_zhis(self) -> list[str]:
        return [self.year.zhi, self.month.zhi, self.day.zhi, self.hour.zhi]

    def all_chars(self) -> list[str]:
        """8 个字（含重复）。"""
        return self.all_gans() + self.all_zhis()

    @classmethod
    def parse(cls, year: str, month: str, day: str, hour: str) -> "Bazi":
        return cls(
            year=Pillar.parse(year),
            month=Pillar.parse(month),
            day=Pillar.parse(day),
            hour=Pillar.parse(hour),
        )


@dataclass(frozen=True)
class Dayun:
    """单步大运。"""

    pillar: Pillar          # 大运干支
    start_age: int          # 起运年龄（虚岁）
    end_age: int            # 此运结束年龄（不含）
    start_year: int         # 公历起运年（含）
    end_year: int           # 公历此运结束年（不含）

    @property
    def gan(self) -> str:
        return self.pillar.gan

    @property
    def zhi(self) -> str:
        return self.pillar.zhi

    def covers_year(self, year: int) -> bool:
        return self.start_year <= year < self.end_year

    def covers_age(self, age: int) -> bool:
        return self.start_age <= age < self.end_age


@dataclass(frozen=True)
class ParsedInput:
    """命主输入解析后的统一结构。

    最小必需字段（Track-C 使用）：
    - 性别（'男' / '女'）
    - 公历出生年（用于推 age = year - birth_year）
    - 八字四柱
    - 大运排布（按起运年龄递增排列）
    """

    gender: str
    birth_year: int
    bazi: Bazi
    dayun_list: list[Dayun] = field(default_factory=list)

    # 可选：旬空、命宫等（Track-C 暂不使用，留口子）
    xun_kong: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.gender not in {"男", "女"}:
            raise ValueError(f"gender 必须是 男/女: {self.gender!r}")

    def age_at_year(self, year: int) -> int:
        """命主在 year 年的虚岁（出生那年算 1 岁；这里简化用周岁差）。"""
        return year - self.birth_year


# ============================================================
# 二、序列化辅助
# ============================================================


def pillar_to_dict(p: Pillar) -> dict:
    return {"gan": p.gan, "zhi": p.zhi}


def parsed_input_to_dict(pi: ParsedInput) -> dict:
    return {
        "gender": pi.gender,
        "birth_year": pi.birth_year,
        "bazi": {
            "year": pillar_to_dict(pi.bazi.year),
            "month": pillar_to_dict(pi.bazi.month),
            "day": pillar_to_dict(pi.bazi.day),
            "hour": pillar_to_dict(pi.bazi.hour),
        },
        "dayun_list": [
            {
                "pillar": pillar_to_dict(d.pillar),
                "start_age": d.start_age,
                "end_age": d.end_age,
                "start_year": d.start_year,
                "end_year": d.end_year,
            }
            for d in pi.dayun_list
        ],
        "xun_kong": list(pi.xun_kong),
    }


# ============================================================
# 三、smoke test
# ============================================================


def _smoke() -> None:
    bz = Bazi.parse("庚申", "戊寅", "壬子", "辛丑")
    assert bz.day_gan == "壬"
    assert bz.day_zhi == "子"
    assert bz.all_chars() == ["庚", "戊", "壬", "辛", "申", "寅", "子", "丑"]

    dy = Dayun(pillar=Pillar.parse("庚辰"), start_age=18, end_age=28,
               start_year=1998, end_year=2008)
    assert dy.covers_year(2005)
    assert not dy.covers_year(2008)

    pi = ParsedInput(gender="男", birth_year=1980, bazi=bz, dayun_list=[dy])
    assert pi.age_at_year(2005) == 25

    d = parsed_input_to_dict(pi)
    assert d["bazi"]["day"]["gan"] == "壬"
    print("predicates.types smoke OK")


if __name__ == "__main__":
    _smoke()
