"""八字同参 → 紫微 v4.0 数据集键的确定性映射。

只做映射，不做命理推断。口径差异一律写入 alignment_warnings，
不静默换算（对应 AGENTS.md §4「保留 variants / boundary_warnings」）。

    --birth "2001-12-31 06:00" --gender 坤
        -> hour_index = floor(((6 + 1) % 24) / 2) = 3 （卯）
        -> key = "2001-12-31-3-female"

时辰序号换算式与 ziwei-doushu 的 app/api/chart/route.ts 中
clockHourToBranch 完全一致。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")

_GENDER_MAP = {
    "坤": "female", "女": "female", "female": "female", "f": "female",
    "乾": "male", "男": "male", "male": "male", "m": "male",
}

_BIRTH_RE = re.compile(
    r"^\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})"
    r"[ T](\d{1,2}):(\d{2})(?::(\d{2}))?\s*$"
)

# 两套体系恒常存在的口径差异，任何时候都要带在信封里
BASE_WARNINGS = (
    "bazi_jieqi_vs_ziwei_solar_date",
    "dataset_content_version_fixed_vs_engine_live",
    "ziwei_brightness_default_changed_after_v4",
)


def parse_birth(value: str) -> datetime:
    """解析 engine.cli 同款出生时间字符串。"""
    m = _BIRTH_RE.match(value or "")
    if not m:
        raise ValueError(f"无法解析 --birth：{value!r}；需要 'YYYY-MM-DD HH:MM'")
    y, mo, d, h, mi, sec = m.groups()
    return datetime(int(y), int(mo), int(d), int(h), int(mi), int(sec or 0))


def hour_index(clock_hour: int) -> int:
    """钟表小时 → 时辰序号 0..11（子=0 … 亥=11）。"""
    return ((clock_hour + 1) % 24) // 2


def normalize_gender(value: str) -> str:
    key = (value or "").strip().lower()
    for k, v in _GENDER_MAP.items():
        if key == k.lower():
            return v
    raise ValueError(f"无法解析 --gender：{value!r}；可用 坤/乾/女/男/female/male")


@dataclass(frozen=True)
class CaseKey:
    birth_iso: str
    gender: str
    gender_ziwei: str
    clock_hour: int
    hour_index: int
    branch: str
    ziwei_key: str
    year: int
    calendar_policy: dict = field(default_factory=dict)
    tz_policy: str = "no_correction"
    schema_version: str = "case-key/v1"
    alignment_warnings: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "birth_iso": self.birth_iso,
            "gender": self.gender,
            "hour_index": self.hour_index,
            "calendar_policy": dict(self.calendar_policy),
            "tz_policy": self.tz_policy,
            "schema_version": self.schema_version,
            "ziwei_key": self.ziwei_key,
            "alignment_warnings": list(self.alignment_warnings),
        }


def build_case_key(birth: str, gender: str, *, tz_policy: str = "no_correction") -> CaseKey:
    dt = parse_birth(birth)
    hidx = hour_index(dt.hour)
    g = normalize_gender(gender)
    dstr = dt.strftime("%Y-%m-%d")
    key = f"{dstr}-{hidx}-{g}"

    warnings = list(BASE_WARNINGS)
    if dt.hour == 23:
        # 数据集按公历日期建键，晚子时换日口径未经核实，绝不自动改成次日
        warnings.append("late_zi_hour_date_policy_unverified")
    if tz_policy != "no_correction":
        # 一旦传入出生地经度，八字与紫微的真太阳时处理会分叉
        warnings.append("true_solar_time_divergence_risk")

    return CaseKey(
        birth_iso=f"{dstr} {dt.strftime('%H:%M')}",
        gender=(gender or "").strip(),
        gender_ziwei=g,
        clock_hour=dt.hour,
        hour_index=hidx,
        branch=BRANCHES[hidx],
        ziwei_key=key,
        year=dt.year,
        calendar_policy={"bazi": "jieqi", "ziwei": "solar_date"},
        tz_policy=tz_policy,
        alignment_warnings=tuple(warnings),
    )
