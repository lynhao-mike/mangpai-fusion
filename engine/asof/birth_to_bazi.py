"""从已校正的公历出生时间排出八字四柱与大运。

依赖：6tail/lunar-python (MIT)。
边界：本模块只做历法排盘，不做出生地、经度、时区或真太阳时换算；
调用方必须传入已经完成所需校正的无时区 ``datetime``。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from lunar_python import Solar


@dataclass(frozen=True, slots=True)
class BaziResult:
    """lunar-python 排盘结果。"""

    pillars: tuple[str, str, str, str]
    dayun: tuple[dict[str, int | str], ...]
    gender: str
    birth_datetime: str
    calculator: str = "lunar-python"
    dayun_method: str = "default_3day_1year"


def calc_bazi(birth_dt: datetime, gender: str) -> BaziResult:
    """从公历出生时间排出四柱和十步大运。

    ``birth_dt`` 按调用方提供的本地真太阳时直接使用。日柱采用午夜换日；
    大运采用 lunar-python 的 ``sect=1`` 默认算法（三天折一年）。
    """
    normalized_gender = gender.strip().upper()
    if normalized_gender not in {"M", "F"}:
        raise ValueError("gender must be 'M' or 'F'")
    if birth_dt.tzinfo is not None:
        raise ValueError("birth_dt must be a naive datetime already corrected by caller")

    solar = Solar.fromYmdHms(
        birth_dt.year,
        birth_dt.month,
        birth_dt.day,
        birth_dt.hour,
        birth_dt.minute,
        birth_dt.second,
    )
    eight_char = solar.getLunar().getEightChar()
    eight_char.setSect(2)  # 午夜换日：23:00-23:59 仍使用当日日柱。
    pillars = (
        eight_char.getYear(),
        eight_char.getMonth(),
        eight_char.getDay(),
        eight_char.getTime(),
    )

    yun = eight_char.getYun(1 if normalized_gender == "M" else 0, 1)
    dayun = tuple(
        {"ganzhi": item.getGanZhi(), "start_year": item.getStartYear()}
        for item in yun.getDaYun(11)
        if item.getGanZhi()
    )

    return BaziResult(
        pillars=pillars,
        dayun=dayun,
        gender=normalized_gender,
        birth_datetime=birth_dt.isoformat(sep=" ", timespec="seconds"),
    )
