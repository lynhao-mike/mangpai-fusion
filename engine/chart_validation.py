"""engine/chart_validation.py · 八字排盘验证模块

在进入八字分析前，验证排盘数据的正确性：
- 四柱（年、月、日、时）
- 节气换月
- 大运方向（顺/逆）与干支排布
- 起运岁数

## 使用规则

1. 若来源明确为问真八字 APP → 跳过验证，直接返回 valid（`source="问真八字"`）
2. 若提供公历日期 + 时支 → 精确重排 + 逐柱比对
3. 若仅提供四柱 → 走"内部一致性"校验（月干-年干五虎遁、时干-日干五鼠遁、60甲子合法性）

## 依赖

- ``sxtwl``：寿星天文历，用于节气与四柱的精确计算
- ``engine.predicates.types``：共享的 GanZhi/Bazi 类型

作者：排盘验证模块
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import re
from typing import Literal, Optional

import sxtwl

from engine.predicates.types import (
    GAN_LIST,
    GAN_YINYANG,
    ZHI_LIST,
    GanZhi,
)


Gender = Literal["M", "F", "男", "女", "乾", "坤"]


# ============================================================
# 一、类型定义
# ============================================================

@dataclass(frozen=True)
class DayunResult:
    """大运计算结果。"""

    direction: Literal["顺", "逆"]
    """大运走向（顺行 / 逆行）。"""

    sequence: tuple[GanZhi, ...]
    """从起运开始的连续 10 步大运干支。"""

    qiyun_age: float
    """起运虚岁（浮点，含小数）。"""


class ChartValidationError(ValueError):
    """排盘未通过验证，禁止进入分析流程。"""


@dataclass
class ValidationResult:
    """排盘验证结果。"""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    corrected_pillars: Optional[dict[str, str]] = None
    """若声称的四柱有误且我们能精确重排，此处返回正确的四柱。"""
    skipped: bool = False
    """来源为可信数据源（问真八字）时标记为 True。"""
    reverse_candidates: Optional[list[str]] = None
    """仅四柱反推得到的候选公历日期。"""


# ============================================================
# 二、来源可信白名单
# ============================================================

TRUSTED_SOURCES = frozenset({
    "问真八字",
    "问真八字APP",
    "问真八字 APP",
    "wenzhen",
    "Wenzhen",
})


def _is_trusted_source(source: Optional[str]) -> bool:
    if not source:
        return False
    normalized = "".join(source.split()).lower()
    return "问真八字" in normalized or "wenzhen" in normalized


# ============================================================
# 三、性别归一化
# ============================================================

def _normalize_gender(g: Gender) -> Literal["M", "F"]:
    if g in ("M", "男", "乾"):
        return "M"
    if g in ("F", "女", "坤"):
        return "F"
    raise ValueError(f"未知性别: {g!r}")


# ============================================================
# 四、四柱计算（sxtwl 驱动）
# ============================================================

def _parse_solar_datetime(solar_date: str) -> tuple[datetime, bool]:
    """解析公历日期或日期时间，返回时刻及是否显式提供时间。"""
    match = re.match(
        r"^\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})"
        r"(?:[ T](\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?",
        str(solar_date),
    )
    if not match:
        raise ValueError(
            f"日期格式错误，应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM: {solar_date!r}"
        )
    year, month, day = map(int, match.group(1, 2, 3))
    has_time = match.group(4) is not None
    hour = int(match.group(4) or 0)
    minute = int(match.group(5) or 0)
    second = int(match.group(6) or 0)
    return datetime(year, month, day, hour, minute, second), has_time


def _parse_solar_date(solar_date: str) -> tuple[int, int, int]:
    """解析公历日期部分。"""
    value, _ = _parse_solar_datetime(solar_date)
    return value.year, value.month, value.day


def lunar_to_solar(lunar_date: str, *, is_leap_month: bool = False) -> str:
    """农历日期转公历日期。

    ``lunar_date`` 使用 ``YYYY-MM-DD``；闰月必须显式设置
    ``is_leap_month=True``，不根据文本猜测。
    """
    y, m, d = _parse_solar_date(lunar_date)
    solar = sxtwl.fromLunar(y, m, d, is_leap_month)
    return (
        f"{solar.getSolarYear():04d}-"
        f"{solar.getSolarMonth():02d}-"
        f"{solar.getSolarDay():02d}"
    )


def _sxtwl_day(solar_date: str):
    y, m, d = _parse_solar_date(solar_date)
    return sxtwl.fromSolar(y, m, d)


def _jieqi_datetime(day: object) -> datetime:
    value = sxtwl.JD2DD(day.getJieQiJD())
    second = int(value.s)
    microsecond = int(round((float(value.s) - second) * 1_000_000))
    return datetime(
        int(value.Y), int(value.M), int(value.D),
        int(value.h), int(value.m), second, microsecond,
    )


def _previous_ganzhi(gz: object) -> GanZhi:
    return GanZhi(
        gan=GAN_LIST[(int(gz.tg) - 1) % 10],
        zhi=ZHI_LIST[(int(gz.dz) - 1) % 12],
    )


def compute_year_pillar(solar_date: str) -> GanZhi:
    """计算年柱；显式提供时刻时按立春精确分钟分界。"""
    birth_dt, has_time = _parse_solar_datetime(solar_date)
    day = _sxtwl_day(solar_date)
    yz = day.getYearGZ()
    if (
        has_time
        and day.hasJieQi()
        and day.getJieQi() == _JIEQI_NAMES.index("立春")
        and birth_dt < _jieqi_datetime(day)
    ):
        return _previous_ganzhi(yz)
    return GanZhi(gan=GAN_LIST[yz.tg], zhi=ZHI_LIST[yz.dz])


def compute_month_pillar(solar_date: str) -> GanZhi:
    """计算月柱；显式提供时刻时按换月节气精确分钟分界。"""
    birth_dt, has_time = _parse_solar_datetime(solar_date)
    day = _sxtwl_day(solar_date)
    mz = day.getMonthGZ()
    if (
        has_time
        and day.hasJieQi()
        and day.getJieQi() in _MONTH_JIE_INDICES
        and birth_dt < _jieqi_datetime(day)
    ):
        return _previous_ganzhi(mz)
    return GanZhi(gan=GAN_LIST[mz.tg], zhi=ZHI_LIST[mz.dz])


def compute_day_pillar(solar_date: str) -> GanZhi:
    """计算日柱（甲子循环 + 万年历基准）。"""
    day = _sxtwl_day(solar_date)
    dz = day.getDayGZ()
    return GanZhi(gan=GAN_LIST[dz.tg], zhi=ZHI_LIST[dz.dz])


def reverse_pillar_dates(
    claimed_pillars: dict[str, str],
    *,
    start_year: int,
    end_year: int,
) -> list[str]:
    """从完整四柱反推指定年份区间内的候选公历日期。

    四柱本身无法唯一确定出生年份（六十年循环），因此必须显式给出有限
    年份区间。时柱只校验日干与时支的五鼠遁关系，候选粒度为日期。
    """
    if end_year < start_year:
        raise ValueError("end_year 不能小于 start_year")
    if end_year - start_year > 200:
        raise ValueError("反推年份区间不能超过 200 年")

    internal_errors = _check_internal_consistency(claimed_pillars)
    if internal_errors:
        return []

    target_year = claimed_pillars["年柱"]
    target_month = claimed_pillars["月柱"]
    target_day = claimed_pillars["日柱"]
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    current = start
    candidates: list[str] = []
    while current <= end:
        solar = current.isoformat()
        if (
            str(compute_year_pillar(solar)) == target_year
            and str(compute_month_pillar(solar)) == target_month
            and str(compute_day_pillar(solar)) == target_day
        ):
            candidates.append(solar)
        current += timedelta(days=1)
    return candidates


def compute_hour_pillar(day_gan: str, hour_zhi: str) -> GanZhi:
    """五鼠遁时：日干 + 时支 → 时柱。

    子时起干规则：
        甲己日起甲子时  (day_gan_idx % 5 == 0)
        乙庚日起丙子时  (day_gan_idx % 5 == 1)
        丙辛日起戊子时  (day_gan_idx % 5 == 2)
        丁壬日起庚子时  (day_gan_idx % 5 == 3)
        戊癸日起壬子时  (day_gan_idx % 5 == 4)

    公式：子时干 index = (day_gan_idx % 5) * 2
    """
    if day_gan not in GAN_LIST:
        raise ValueError(f"非法日干: {day_gan!r}")
    if hour_zhi not in ZHI_LIST:
        raise ValueError(f"非法时支: {hour_zhi!r}")

    day_gan_idx = GAN_LIST.index(day_gan)
    hour_zhi_idx = ZHI_LIST.index(hour_zhi)
    zi_hour_gan_idx = (day_gan_idx % 5) * 2
    hour_gan_idx = (zi_hour_gan_idx + hour_zhi_idx) % 10
    return GanZhi(gan=GAN_LIST[hour_gan_idx], zhi=hour_zhi)


def compute_hour_pillar_at(solar_datetime: str) -> GanZhi:
    """按问真晚子时口径计算时柱：23点时干使用次日日干。"""
    birth_dt, has_time = _parse_solar_datetime(solar_datetime)
    if not has_time:
        raise ValueError("计算时柱必须提供 HH:MM")
    hour_zhi = ZHI_LIST[((birth_dt.hour + 1) // 2) % 12]
    day_for_hour = birth_dt + timedelta(days=1) if birth_dt.hour == 23 else birth_dt
    day_gan = compute_day_pillar(day_for_hour.strftime("%Y-%m-%d")).gan
    return compute_hour_pillar(day_gan, hour_zhi)


# ============================================================
# 五、大运计算
# ============================================================

_JIEQI_NAMES = (
    "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
    "春分", "清明", "谷雨", "立夏", "小满", "芒种",
    "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
    "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
)
_MONTH_JIE_INDICES = frozenset(
    _JIEQI_NAMES.index(name)
    for name in (
        "立春", "惊蛰", "清明", "立夏", "芒种", "小暑",
        "立秋", "白露", "寒露", "立冬", "大雪", "小寒",
    )
)


def dayun_direction(gender: Gender, year_gan: str) -> Literal["顺", "逆"]:
    """按年干阴阳与性别计算大运方向。

    阳年男、阴年女顺排；阴年男、阳年女逆排。
    """
    norm_gender = _normalize_gender(gender)
    if year_gan not in GAN_LIST:
        raise ValueError(f"非法年干: {year_gan!r}")
    is_yang_year = GAN_YINYANG[year_gan] == "阳"
    forward = is_yang_year if norm_gender == "M" else not is_yang_year
    return "顺" if forward else "逆"


def _is_forward(gender: Literal["M", "F"], year_gan: str) -> bool:
    """内部布尔适配；公共调用应使用 ``dayun_direction``。"""
    return dayun_direction(gender, year_gan) == "顺"


def compute_dayun(
    month_pillar: GanZhi,
    gender: Gender,
    year_gan: str,
    solar_date: Optional[str] = None,
    steps: int = 10,
) -> DayunResult:
    """计算大运序列。

    - direction：由性别 + 年干阴阳决定
    - sequence：从月柱起，顺行取下一甲子，逆行取上一甲子
    - qiyun_age：若给出 solar_date，则通过与最近节气的距离精算；否则返回 0
    """
    norm_g = _normalize_gender(gender)
    if year_gan not in GAN_LIST:
        raise ValueError(f"非法年干: {year_gan!r}")

    forward = _is_forward(norm_g, year_gan)
    direction: Literal["顺", "逆"] = "顺" if forward else "逆"

    # 从月柱推序列
    mg_idx = GAN_LIST.index(month_pillar.gan)
    mz_idx = ZHI_LIST.index(month_pillar.zhi)
    delta = 1 if forward else -1

    seq: list[GanZhi] = []
    for i in range(1, steps + 1):
        g = GAN_LIST[(mg_idx + delta * i) % 10]
        z = ZHI_LIST[(mz_idx + delta * i) % 12]
        seq.append(GanZhi(gan=g, zhi=z))

    qiyun_age = 0.0
    if solar_date is not None:
        qiyun_age = _compute_qiyun_age(solar_date, forward)

    return DayunResult(
        direction=direction,
        sequence=tuple(seq),
        qiyun_age=qiyun_age,
    )


def _compute_qiyun_age(solar_date: str, forward: bool) -> float:
    """通过与最近节气的距离计算起运岁。

    - 顺行（阳男阴女）：找出生日之后的下一个"节"，日差 / 3 = 起运岁
    - 逆行（阴男阳女）：找出生日之前的上一个"节"

    "节"指 12 个月柱的分界：立春、惊蛰、清明、立夏、芒种、小暑、
    立秋、白露、寒露、立冬、大雪、小寒（不含中气）。

    3 天 = 1 岁（业界通用换算）。
    """
    birth_dt, has_time = _parse_solar_datetime(solar_date)
    if not has_time:
        birth_dt = birth_dt.replace(hour=0, minute=0, second=0)
    birth_day = birth_dt.date()

    if forward:
        # 顺排：取出生后的下一个节（含出生当天节气时刻在出生后的情况）
        for offset in range(0, 91):
            candidate_date = birth_day + timedelta(days=offset)
            day = sxtwl.fromSolar(
                candidate_date.year, candidate_date.month, candidate_date.day
            )
            if not day.hasJieQi() or day.getJieQi() not in _MONTH_JIE_INDICES:
                continue
            jieqi_dt = _jieqi_datetime(day)
            # 节气时刻必须严格晚于出生时刻
            if (jieqi_dt - birth_dt).total_seconds() > 0:
                return (jieqi_dt - birth_dt).total_seconds() / 86400.0 / 3.0
    else:
        # 逆排：取出生前的上一个节（含出生当天节气时刻在出生前的情况）
        for offset in range(0, 91):
            candidate_date = birth_day - timedelta(days=offset)
            day = sxtwl.fromSolar(
                candidate_date.year, candidate_date.month, candidate_date.day
            )
            if not day.hasJieQi() or day.getJieQi() not in _MONTH_JIE_INDICES:
                continue
            jieqi_dt = _jieqi_datetime(day)
            # 节气时刻必须严格早于出生时刻
            if (birth_dt - jieqi_dt).total_seconds() > 0:
                return (birth_dt - jieqi_dt).total_seconds() / 86400.0 / 3.0

    return 0.0


# ---- 以下代码删除（原双向搜索残片） ----
    best_secs: Optional[float] = None

    # 双向各搜 45 天（最长节气间距约 33 天，45 天已足够覆盖）
    for sign, end in ((1, 46), (-1, 46)):
        for offset in range(0, end):
            candidate_date = birth_day + timedelta(days=sign * offset)
            day = sxtwl.fromSolar(
                candidate_date.year, candidate_date.month, candidate_date.day
            )
            if not day.hasJieQi() or day.getJieQi() not in _MONTH_JIE_INDICES:
                continue
            jieqi_dt = _jieqi_datetime(day)
            diff = abs((jieqi_dt - birth_dt).total_seconds())
            if best_secs is None or diff < best_secs:
                best_secs = diff

    if best_secs is None:
        return 0.0
    return best_secs / 86400.0 / 3.0


# ============================================================
# 六、内部一致性校验
# ============================================================

def _wuhu_expected_month_gan(year_gan: str, month_zhi: str) -> str:
    """五虎遁月：年干 + 月支 → 月柱天干。

    寅月干 index = (年干 index * 2 + 2) % 10
    月干 index = (寅月干 index + (月支 index - 寅索引) mod 12) mod 10
    """
    year_gan_idx = GAN_LIST.index(year_gan)
    yin_gan_idx = (year_gan_idx * 2 + 2) % 10
    zhi_offset = (ZHI_LIST.index(month_zhi) - ZHI_LIST.index("寅")) % 12
    return GAN_LIST[(yin_gan_idx + zhi_offset) % 10]


def _wushu_expected_hour_gan(day_gan: str, hour_zhi: str) -> str:
    """五鼠遁时：日干 + 时支 → 时柱天干。"""
    return compute_hour_pillar(day_gan, hour_zhi).gan


def _check_internal_consistency(pillars: dict[str, str]) -> list[str]:
    """在无日期情况下检查四柱之间的内部约束。

    返回错误列表；空列表表示通过。
    """
    errors: list[str] = []

    for name in ("年柱", "月柱", "日柱", "时柱"):
        if name not in pillars:
            errors.append(f"缺少{name}")
            continue
        gz_str = pillars[name]
        if len(gz_str) != 2 or gz_str[0] not in GAN_LIST or gz_str[1] not in ZHI_LIST:
            errors.append(f"{name}格式非法: {gz_str!r}")
            continue
        gan, zhi = gz_str[0], gz_str[1]
        if GAN_YINYANG[gan] != {"子": "阳", "丑": "阴", "寅": "阳", "卯": "阴",
                                 "辰": "阳", "巳": "阴", "午": "阳", "未": "阴",
                                 "申": "阳", "酉": "阴", "戌": "阳", "亥": "阴"}[zhi]:
            errors.append(f"{name} {gz_str} 非 60 甲子（阴阳不配）")

    if errors:
        return errors

    # 五虎遁月：月干必须与年干推出的月干一致
    year_gan = pillars["年柱"][0]
    month_zhi = pillars["月柱"][1]
    month_gan_actual = pillars["月柱"][0]
    month_gan_expected = _wuhu_expected_month_gan(year_gan, month_zhi)
    if month_gan_actual != month_gan_expected:
        errors.append(
            f"月柱天干与年干不符五虎遁月规则：{year_gan}年{month_zhi}月应为 "
            f"{month_gan_expected}{month_zhi}，实际 {pillars['月柱']}"
        )

    # 五鼠遁时：时干必须与日干推出的时干一致
    day_gan = pillars["日柱"][0]
    hour_zhi = pillars["时柱"][1]
    hour_gan_actual = pillars["时柱"][0]
    hour_gan_expected = _wushu_expected_hour_gan(day_gan, hour_zhi)
    if hour_gan_actual != hour_gan_expected:
        errors.append(
            f"时柱天干与日干不符五鼠遁时规则：{day_gan}日{hour_zhi}时应为 "
            f"{hour_gan_expected}{hour_zhi}，实际 {pillars['时柱']}"
        )

    return errors


# ============================================================
# 七、验证主入口
# ============================================================

def validate_chart(
    claimed_pillars: dict[str, str],
    gender: Optional[Gender] = None,
    solar_date: Optional[str] = None,
    lunar_date: Optional[str] = None,
    lunar_is_leap_month: bool = False,
    hour_zhi: Optional[str] = None,
    source: Optional[str] = None,
    claimed_dayun: Optional[dict] = None,
    reverse_start_year: Optional[int] = None,
    reverse_end_year: Optional[int] = None,
) -> ValidationResult:
    """验证排盘数据准确性。

    参数:
        claimed_pillars: 用户/APP 声称的四柱，如 {"年柱":"庚申","月柱":"戊寅",...}
        gender: 性别（用于大运方向验证）
        solar_date: 公历日期 'YYYY-MM-DD'（可选）
        hour_zhi: 时支（可选，配合 solar_date 用来精算时柱）
        source: 数据来源。若为可信来源（问真八字）则跳过验证
        claimed_dayun: 大运声称，形如
            ``{"顺逆": "顺", "排布": ["己卯", "庚辰", ...], "起运岁": 8}``
            任一字段缺失即跳过该字段检查。

    返回:
        ValidationResult，其中 corrected_pillars 在能精算时提供正确排盘
    """
    result = ValidationResult(is_valid=True)

    # 可信来源 → 跳过
    if _is_trusted_source(source):
        result.skipped = True
        return result

    if solar_date and lunar_date:
        result.is_valid = False
        result.errors.append("公历日期和农历日期不能同时提供")
        return result

    if lunar_date:
        try:
            solar_date = lunar_to_solar(
                lunar_date,
                is_leap_month=lunar_is_leap_month,
            )
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"农历日期解析失败: {e}")
            return result

    # 有日期 → 精算并逐柱对比
    if solar_date:
        try:
            expected: dict[str, str] = {
                "年柱": str(compute_year_pillar(solar_date)),
                "月柱": str(compute_month_pillar(solar_date)),
                "日柱": str(compute_day_pillar(solar_date)),
            }
            if hour_zhi:
                _, has_time = _parse_solar_datetime(solar_date)
                if has_time:
                    expected["时柱"] = str(compute_hour_pillar_at(solar_date))
                else:
                    day_gan = expected["日柱"][0]
                    expected["时柱"] = str(compute_hour_pillar(day_gan, hour_zhi))
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"日期解析失败: {e}")
            return result

        # 逐柱比对
        pillar_ok = True
        for name in ("年柱", "月柱", "日柱", "时柱"):
            if name not in expected:
                continue
            if name not in claimed_pillars:
                result.errors.append(f"声称的四柱缺少 {name}")
                pillar_ok = False
                continue
            if claimed_pillars[name] != expected[name]:
                result.errors.append(
                    f"{name}错误：声称 {claimed_pillars[name]}，"
                    f"根据 {solar_date} 精算为 {expected[name]}"
                )
                pillar_ok = False

        if not pillar_ok:
            result.is_valid = False
            result.corrected_pillars = expected
    else:
        # 无日期 → 内部一致性
        errs = _check_internal_consistency(claimed_pillars)
        if errs:
            result.is_valid = False
            result.errors.extend(errs)
        elif reverse_start_year is not None or reverse_end_year is not None:
            if reverse_start_year is None or reverse_end_year is None:
                result.is_valid = False
                result.errors.append("四柱反推必须同时提供起止年份")
            else:
                result.reverse_candidates = reverse_pillar_dates(
                    claimed_pillars,
                    start_year=reverse_start_year,
                    end_year=reverse_end_year,
                )
                if not result.reverse_candidates:
                    result.is_valid = False
                    result.errors.append("指定年份区间内未找到与四柱匹配的日期")

    # 大运验证（需要性别 + 年干 + 月柱）
    if (
        claimed_dayun
        and gender
        and "年柱" in claimed_pillars
        and "月柱" in claimed_pillars
    ):
        _validate_dayun(
            claimed_dayun=claimed_dayun,
            year_gan=claimed_pillars["年柱"][0],
            month_pillar_str=claimed_pillars["月柱"],
            gender=gender,
            solar_date=solar_date,
            result=result,
        )

    return result


def _validate_dayun(
    claimed_dayun: dict,
    year_gan: str,
    month_pillar_str: str,
    gender: Gender,
    solar_date: Optional[str],
    result: ValidationResult,
) -> None:
    """内部：把大运声称与精算结果对比，把错误挂到 result 上。"""
    try:
        month_pillar = GanZhi.parse(month_pillar_str)
    except Exception as e:
        result.errors.append(f"月柱解析失败: {e}")
        result.is_valid = False
        return

    steps = max(len(claimed_dayun.get("排布", [])), 10)
    computed = compute_dayun(
        month_pillar=month_pillar,
        gender=gender,
        year_gan=year_gan,
        solar_date=solar_date,
        steps=steps,
    )

    # 方向
    claimed_dir = claimed_dayun.get("顺逆")
    if claimed_dir and claimed_dir != computed.direction:
        result.errors.append(
            f"大运方向错误：声称 {claimed_dir}，"
            f"根据 {gender}性 + {year_gan}({GAN_YINYANG[year_gan]}) "
            f"应为 {computed.direction}"
        )
        result.is_valid = False

    # 序列
    claimed_seq = claimed_dayun.get("排布") or []
    computed_seq = [str(s) for s in computed.sequence]
    for i, claimed in enumerate(claimed_seq):
        if i >= len(computed_seq):
            break
        if claimed != computed_seq[i]:
            result.errors.append(
                f"第{i+1}步大运错误：声称 {claimed}，精算为 {computed_seq[i]}"
            )
            result.is_valid = False

    # 起运岁（仅在有日期时精算）
    if solar_date and "起运岁" in claimed_dayun:
        claimed_age = float(claimed_dayun["起运岁"])
        diff = abs(computed.qiyun_age - claimed_age)
        if diff >= 1.5:
            result.warnings.append(
                f"起运岁差距较大：声称 {claimed_age}，精算 {computed.qiyun_age:.2f}"
            )


# ============================================================
# 八、便捷入口：ChartValidator（面向对象）
# ============================================================

def _pillar_text(bazi: object, name: str) -> str:
    """兼容 dict 四柱与属性式 Bazi，返回指定柱文本。"""
    if isinstance(bazi, dict):
        value = bazi[name]
    else:
        value = getattr(bazi, name)
    return str(value)


def ensure_parsed_chart_validated(parsed: object) -> None:
    """确保程序化 ``ParsedInput`` 已验证，未通过则阻断分析。

    已由 preflight 标记的输入幂等放行；未标记输入现场验证并写回状态。
    """
    case_meta = getattr(parsed, "case_meta", None)
    if not isinstance(case_meta, dict):
        raise ChartValidationError("缺少 case_meta，无法记录排盘验证状态")

    current = case_meta.get("排盘验证状态")
    if current in {"validated", "skipped_trusted_wenzhen"}:
        return

    birth = getattr(parsed, "birth", None)
    bazi = getattr(parsed, "bazi", None)
    dayun = getattr(parsed, "dayun", None)
    if not isinstance(birth, dict) or bazi is None or dayun is None:
        raise ChartValidationError("缺少 birth/bazi/dayun，无法验证排盘")

    source = birth.get("来源") or case_meta.get("来源")
    solar_raw = birth.get("公历")
    if isinstance(solar_raw, datetime):
        solar_date = solar_raw.strftime("%Y-%m-%d %H:%M:%S")
    elif solar_raw:
        value, has_time = _parse_solar_datetime(str(solar_raw))
        solar_date = value.strftime(
            "%Y-%m-%d %H:%M:%S" if has_time else "%Y-%m-%d"
        )
    else:
        solar_date = None

    claimed_pillars = {
        name: _pillar_text(bazi, name)
        for name in ("年柱", "月柱", "日柱", "时柱")
    }
    steps = getattr(dayun, "排布", []) or []
    claimed_dayun = {
        "顺逆": getattr(dayun, "顺逆", None),
        "起运岁": getattr(dayun, "起运岁", None),
        "排布": [str(getattr(step, "干支")) for step in steps],
    }
    result = validate_chart(
        claimed_pillars=claimed_pillars,
        gender=str(birth.get("性别", "")),
        solar_date=solar_date,
        hour_zhi=claimed_pillars["时柱"][1],
        source=str(source) if source is not None else None,
        claimed_dayun=claimed_dayun,
    )
    if not result.is_valid:
        correction = (
            f"；后续唯一依据应修正为 {result.corrected_pillars}"
            if result.corrected_pillars else ""
        )
        raise ChartValidationError("；".join(result.errors) + correction)

    case_meta["排盘验证状态"] = (
        "skipped_trusted_wenzhen" if result.skipped else "validated"
    )
    if result.warnings:
        case_meta["排盘验证警告"] = list(result.warnings)


@dataclass
class ChartValidator:
    """面向对象封装，用于命理师工作流。

    示例::

        v = ChartValidator(source="用户直贴")
        r = v.validate(
            claimed_pillars={"年柱": "庚申", ...},
            solar_date="1980-02-09",
            hour_zhi="丑",
            gender="M",
        )
        if not r.is_valid:
            print(r.errors)
            print("正确排盘：", r.corrected_pillars)
    """

    source: Optional[str] = None

    def validate(
        self,
        claimed_pillars: dict[str, str],
        gender: Optional[Gender] = None,
        solar_date: Optional[str] = None,
        lunar_date: Optional[str] = None,
        lunar_is_leap_month: bool = False,
        hour_zhi: Optional[str] = None,
        claimed_dayun: Optional[dict] = None,
    ) -> ValidationResult:
        return validate_chart(
            claimed_pillars=claimed_pillars,
            gender=gender,
            solar_date=solar_date,
            lunar_date=lunar_date,
            lunar_is_leap_month=lunar_is_leap_month,
            hour_zhi=hour_zhi,
            source=self.source,
            claimed_dayun=claimed_dayun,
        )


__all__ = [
    "ChartValidationError",
    "ChartValidator",
    "DayunResult",
    "ValidationResult",
    "compute_day_pillar",
    "compute_dayun",
    "dayun_direction",
    "compute_hour_pillar",
    "compute_hour_pillar_at",
    "compute_month_pillar",
    "compute_year_pillar",
    "ensure_parsed_chart_validated",
    "lunar_to_solar",
    "reverse_pillar_dates",
    "validate_chart",
]
