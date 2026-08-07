"""基于语料库规则的起运年龄计算器。

支持两套口径：
1. 盲派粗略法：生日与最近十二节之差÷3，余二进一、余一舍去，
   最小 1 岁、最大 10 岁，按虚岁表达。
2. 港台精确法：3 日=1 岁，1 日=120 天，1 时辰=10 天，精确到时刻。

关键规则：
- 只使用十二节（立春/惊蛰/清明/立夏/芒种/小暑/立秋/白露/寒露/
  立冬/大雪/小寒），不使用雨水/春分/谷雨等“气”。
- 顺排：从出生时刻顺推至下一个十二节。
- 逆排：从出生时刻逆推至上一个十二节。
- 阳年男、阴年女顺排；阴年男、阳年女逆排。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final

from lunar_python import Solar

JIE_NAMES: Final[frozenset[str]] = frozenset(
    {
        "立春",
        "惊蛰",
        "清明",
        "立夏",
        "芒种",
        "小暑",
        "立秋",
        "白露",
        "寒露",
        "立冬",
        "大雪",
        "小寒",
    }
)

# lunar-python 在节气表边缘会使用拼音常量名，表内主体使用中文名。
_JIE_ALIASES: Final[dict[str, str]] = {
    "LI_CHUN": "立春",
    "JING_ZHE": "惊蛰",
    "QING_MING": "清明",
    "LI_XIA": "立夏",
    "MANG_ZHONG": "芒种",
    "XIAO_SHU": "小暑",
    "LI_QIU": "立秋",
    "BAI_LU": "白露",
    "HAN_LU": "寒露",
    "LI_DONG": "立冬",
    "DA_XUE": "大雪",
    "XIAO_HAN": "小寒",
}
_YANG_STEMS: Final[frozenset[str]] = frozenset("甲丙戊庚壬")
_YIN_STEMS: Final[frozenset[str]] = frozenset("乙丁己辛癸")
_MALE_GENDERS: Final[frozenset[str]] = frozenset({"M", "MALE", "男", "乾"})
_FEMALE_GENDERS: Final[frozenset[str]] = frozenset({"F", "FEMALE", "女", "坤"})


@dataclass(frozen=True, slots=True)
class QiyunResult:
    birth_datetime: str
    gender: str
    year_stem: str
    is_shunpai: bool
    ref_jie_datetime: str
    ref_jie_name: str
    diff_days: float
    diff_hours: float
    mang_pai_start_age: int
    mang_pai_method: str
    hk_tw_start_years: float
    hk_tw_start_datetime: str
    wenzhen_reference: str


def _normalize_gender(gender: str) -> str | None:
    value = str(gender).strip().upper()
    if value in _MALE_GENDERS:
        return "M"
    if value in _FEMALE_GENDERS:
        return "F"
    return None


def _direction(gender: str, year_stem: str) -> bool | None:
    """返回是否顺排；输入无法识别时返回 ``None``。"""
    normalized_gender = _normalize_gender(gender)
    stem = str(year_stem).strip()[:1]
    if normalized_gender is None or stem not in _YANG_STEMS | _YIN_STEMS:
        return None
    is_yang_year = stem in _YANG_STEMS
    return is_yang_year == (normalized_gender == "M")


def _solar_to_datetime(solar: object) -> datetime:
    return datetime(
        solar.getYear(),
        solar.getMonth(),
        solar.getDay(),
        solar.getHour(),
        solar.getMinute(),
        solar.getSecond(),
    )


def _twelve_jie_near(birth_dt: datetime) -> tuple[tuple[datetime, str], ...]:
    """读取出生年前后节气表，并严格过滤为十二节。"""
    found: dict[tuple[datetime, str], None] = {}
    for year in range(birth_dt.year - 1, birth_dt.year + 2):
        probe = Solar.fromYmdHms(year, 6, 15, 12, 0, 0)
        for raw_name, solar in probe.getLunar().getJieQiTable().items():
            name = _JIE_ALIASES.get(raw_name, raw_name)
            if name not in JIE_NAMES:
                continue
            found[(_solar_to_datetime(solar), name)] = None
    return tuple(sorted(found, key=lambda item: item[0]))


def _rough_start_age(diff_days: float) -> int:
    """按整日“余二进一、余一舍去”换算，并限制到 1—10 岁。"""
    whole_days = max(0, int(diff_days))
    years, remainder = divmod(whole_days, 3)
    if remainder == 2:
        years += 1
    return min(10, max(1, years))


def _error_result(
    birth_dt: object,
    gender: str,
    year_stem: str,
    wenzhen_reference: str,
    message: str,
) -> QiyunResult:
    birth_text = (
        birth_dt.isoformat(sep=" ", timespec="seconds")
        if isinstance(birth_dt, datetime)
        else str(birth_dt)
    )
    return QiyunResult(
        birth_datetime=birth_text,
        gender=str(gender),
        year_stem=str(year_stem),
        is_shunpai=False,
        ref_jie_datetime="",
        ref_jie_name="",
        diff_days=0.0,
        diff_hours=0.0,
        mang_pai_start_age=1,
        mang_pai_method=f"无法计算：{message}",
        hk_tw_start_years=0.0,
        hk_tw_start_datetime="",
        wenzhen_reference=wenzhen_reference,
    )


def calc_qiyun(
    birth_dt: datetime,
    gender: str,
    year_stem: str,
    *,
    wenzhen_reference: str = "",
) -> QiyunResult:
    """按顺逆方向定位十二节，返回粗略法与精确法起运结果。

    ``birth_dt`` 应为调用方已校正（优先真太阳时）的公历时间。无法识别的输入
    或 lunar-python 历法边界不会向外抛异常，而会在 ``mang_pai_method`` 中说明。
    """
    if not isinstance(birth_dt, datetime):
        return _error_result(birth_dt, gender, year_stem, wenzhen_reference, "birth_dt 不是 datetime")

    direction = _direction(gender, year_stem)
    if direction is None:
        return _error_result(birth_dt, gender, year_stem, wenzhen_reference, "性别或年干无法识别")

    normalized_birth = birth_dt.replace(tzinfo=None) if birth_dt.tzinfo else birth_dt
    try:
        jie_entries = _twelve_jie_near(normalized_birth)
        candidates = [
            item
            for item in jie_entries
            if (item[0] >= normalized_birth if direction else item[0] <= normalized_birth)
        ]
        if not candidates:
            return _error_result(
                normalized_birth,
                gender,
                year_stem,
                wenzhen_reference,
                "lunar-python 节气表中没有可用的方向性十二节",
            )
        ref_dt, ref_name = (candidates[0] if direction else candidates[-1])
    except Exception as exc:  # lunar-python 支持年份边界由其版本决定。
        return _error_result(
            normalized_birth,
            gender,
            year_stem,
            wenzhen_reference,
            f"lunar-python 历法计算失败：{exc}",
        )

    delta = ref_dt - normalized_birth if direction else normalized_birth - ref_dt
    diff_hours = max(0.0, delta.total_seconds() / 3600.0)
    diff_days = diff_hours / 24.0
    hk_tw_years = diff_hours / 72.0

    # 每 1 个出生—节令间隔小时折 5 个交运日：24 小时=120 天，
    # 2 小时（一个时辰）=10 天，故 72 小时=360 天=1 起运年。
    hk_tw_start = normalized_birth + timedelta(days=diff_hours * 5.0)
    method = (
        "十二节方向法；生日与方向性节令差按整日÷3，余二进一、余一舍去，"
        "最小1岁、最大10岁（虚岁）"
    )
    if birth_dt.tzinfo is not None:
        method += "；输入含时区，按原墙上时间去除时区后计算"

    return QiyunResult(
        birth_datetime=normalized_birth.isoformat(sep=" ", timespec="seconds"),
        gender=_normalize_gender(gender) or str(gender),
        year_stem=str(year_stem).strip()[:1],
        is_shunpai=direction,
        ref_jie_datetime=ref_dt.isoformat(sep=" ", timespec="seconds"),
        ref_jie_name=ref_name,
        diff_days=round(diff_days, 9),
        diff_hours=round(diff_hours, 6),
        mang_pai_start_age=_rough_start_age(diff_days),
        mang_pai_method=method,
        hk_tw_start_years=round(hk_tw_years, 9),
        hk_tw_start_datetime=hk_tw_start.isoformat(sep=" ", timespec="seconds"),
        wenzhen_reference=wenzhen_reference,
    )


__all__ = ("JIE_NAMES", "QiyunResult", "calc_qiyun")
