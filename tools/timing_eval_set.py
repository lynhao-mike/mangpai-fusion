"""T-148 · 婚姻应期评测集构建器（只造尺子，不建模）。

从 ``cases/raw_feedback/parsed/real_cases_990.jsonl`` 解析真实反馈案例，产出：

* ``META/timing-eval-set-v1.json``   评测集（性别 / 出生 / 婚姻事件 / 是否可评测）
* ``META/timing-baseline-v1.json``   冻结基线（先于任何模型生成，含「不得修改」声明）
* ``META/timing-eval-set-v1.md``     人读报告（解析成功率、失败分类、基线表）

本模块**不输出任何应期预测、概率或评分**；``marriage_events[].age`` 是
``事件年份 - 出生年份`` 的确定性盘面事实，不是模型输出。

用法::

    python -m tools.timing_eval_set

退出码：0 通过；2 基线数字与任务卡不复现（打印差异分类，不落盘）；
3 已冻结基线被改动（拒绝覆盖）；4 数据源不可读；5 缺少 lunar-python。

数据口径（与任务卡 §2 实测一致，见 §7.1）：

* 去重：``duplicate_key`` 全等去重，保留文件中首次出现者。
* 出生时刻：``true_solar_time_raw``（ADR-005 优先）→ 否则 ``clock_beijing``。
* 历法：``birth_datetime_raw`` 对 ``solar`` / ``solar_unspecified`` 直接使用；
  ``lunar`` 且原文含「排盘所用公历」者已是公历（287/288 与农历换算互证），
  其余 ``lunar`` 记录按农历换算为公历，绝不把农历当公历直接用。
* 年龄：``event.year - birth.year``（整年差，无月日修正）。
* 合理婚龄窗口：15–50 岁（窗口外事件视为数据噪声，不参与基线；窗口内事件才算可评测）。
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "cases" / "raw_feedback" / "parsed" / "real_cases_990.jsonl"
EVAL_PATH = ROOT / "META" / "timing-eval-set-v1.json"
BASELINE_PATH = ROOT / "META" / "timing-baseline-v1.json"
REPORT_PATH = ROOT / "META" / "timing-eval-set-v1.md"

SCHEMA_EVAL = "timing-eval-set/v1"
SCHEMA_BASELINE = "timing-baseline/v1"

GENDERS = ("男", "女")
AGE_MIN = 15
AGE_MAX = 50

# 任务卡 §2 冻结基线（必须现场复现，禁止调带对齐）。
CARD_BASELINE = {
    "sample_size": 392,
    "bands": {
        "age_26": {"range": [26, 26], "hits": 44, "rate_pct": 11.2},
        "age_24_30": {"range": [24, 30], "hits": 177, "rate_pct": 45.2},
        "age_22_28": {"range": [22, 28], "hits": 191, "rate_pct": 48.7},
        "age_20_30": {"range": [20, 30], "hits": 245, "rate_pct": 62.5},
    },
}
BAND_ORDER = ("age_26", "age_24_30", "age_22_28", "age_20_30")

PREDICTION_KEY_DENYLIST = (
    "predict",
    "prediction",
    "forecast",
    "expected_age",
    "probability",
    "probability_pct",
    "score",
    "应期预测",
)

# ---------------------------------------------------------------------------
# 文本与日期解析
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"(\d{4})\s*[年.\-/]\s*(\d{1,2})\s*[月.\-/]\s*(\d{1,2})\s*[日号]?")
_TIME_RE = re.compile(r"(\d{1,2})\s*[:时点]\s*(\d{1,2})?")
_PERIOD_RE = re.compile(r"(凌晨|早上|早晨|清晨|上午|中午|下午|晚上|夜里|晚)")
_PM_PERIODS = ("下午", "晚上", "夜里", "晚")
_TST_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$")

_LUNAR_MONTHS = {
    "正": 1, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
    "七": 7, "八": 8, "九": 9, "十": 10, "冬": 11, "腊": 12,
    "十一": 11, "十二": 12,
}
_LUNAR_DAYS = {
    "初一": 1, "初二": 2, "初三": 3, "初四": 4, "初五": 5, "初六": 6,
    "初七": 7, "初八": 8, "初九": 9, "初十": 10, "十一": 11, "十二": 12,
    "十三": 13, "十四": 14, "十五": 15, "十六": 16, "十七": 17, "十八": 18,
    "十九": 19, "二十": 20, "廿一": 21, "廿二": 22, "廿三": 23, "廿四": 24,
    "廿五": 25, "廿六": 26, "廿七": 27, "廿八": 28, "廿九": 29, "三十": 30,
}
_LUNAR_TEXT_RE = re.compile(
    r"农\(阴\)历[:：]\s*(\d{4})\s*年\s*(闰?)"
    r"(十一|十二|正|一|二|三|四|五|六|七|八|九|十|冬|腊)月\s*"
    r"(初[一二三四五六七八九十]|十[一二三四五六七八九]|二十|廿[一二三四五六七八九]|三十)"
)


def _norm_text(value: str | None) -> str:
    return unicodedata.normalize("NFKC", value or "").strip()


def parse_clock_datetime(raw: str | None) -> dict[str, Any]:
    """解析 ``birth_datetime_raw``。返回 ok / dt / has_time / reason。

    reason 取值：empty / no_date / bad_date / bad_time / None（成功）。
    """
    text = _norm_text(raw)
    if not text:
        return {"ok": False, "dt": None, "has_time": False, "reason": "empty"}
    match = _DATE_RE.search(text)
    if not match:
        return {"ok": False, "dt": None, "has_time": False, "reason": "no_date"}
    year, month, day = (int(part) for part in match.groups())
    rest = text[match.end():]
    time_match = _TIME_RE.search(rest)
    if not time_match:
        try:
            return {"ok": True, "dt": datetime(year, month, day), "has_time": False, "reason": None}
        except ValueError:
            return {"ok": False, "dt": None, "has_time": False, "reason": "bad_date"}
    hour = int(time_match.group(1))
    minute = int(time_match.group(2) or 0)
    period = _PERIOD_RE.search(rest[: time_match.start() + 5])
    if period and period.group(1) in _PM_PERIODS and hour < 12:
        hour += 12
    if hour > 23 or minute > 59:
        return {"ok": False, "dt": None, "has_time": False, "reason": "bad_time"}
    try:
        return {
            "ok": True,
            "dt": datetime(year, month, day, hour, minute),
            "has_time": True,
            "reason": None,
        }
    except ValueError:
        return {"ok": False, "dt": None, "has_time": False, "reason": "bad_date"}


def parse_true_solar_time(raw: str | None) -> datetime | None:
    match = _TST_RE.match(_norm_text(raw))
    if not match:
        return None
    try:
        return datetime(*(int(part) for part in match.groups()))
    except ValueError:
        return None


def extract_lunar_text_date(raw_text: str | None) -> tuple[int, int, int] | None:
    """从 ``raw_text`` 中提取「农(阴)历:1992 年十月廿四」式农历日期。"""
    match = _LUNAR_TEXT_RE.search(raw_text or "")
    if not match:
        return None
    year = int(match.group(1))
    month = _LUNAR_MONTHS[match.group(3)]
    day = _LUNAR_DAYS[match.group(4)]
    if match.group(2):
        month = -month
    return year, month, day


def _lunar_to_solar(year: int, month: int, day: int) -> datetime:
    """农历→公历；失败时抛出 ValueError（调用方必须分类记录，不得静默）。"""
    try:
        from lunar_python import Lunar
    except ImportError as exc:  # pragma: no cover - 环境缺失时 fail closed
        raise RuntimeError("缺少 lunar-python，无法换算农历（requirements.txt 已声明）") from exc
    solar = Lunar.fromYmd(year, month, day).getSolar()
    return datetime(solar.getYear(), solar.getMonth(), solar.getDay())


def resolve_birth(record: dict[str, Any]) -> dict[str, Any]:
    """把案例原始出生字段解析为可用于评测的公历出生时刻。"""
    parsed = parse_clock_datetime(record["birth_datetime_raw"])
    if not parsed["ok"]:
        return {
            "ok": False,
            "dt": None,
            "has_time": False,
            "time_basis": None,
            "birth_source": None,
            "reason": f"birth_{parsed['reason']}",
        }

    birth_dt: datetime = parsed["dt"]
    calendar = record["calendar_type"]
    has_paipan_solar = "排盘所用公历" in (record.get("raw_text") or "")
    if calendar == "lunar" and not has_paipan_solar:
        try:
            birth_dt = _lunar_to_solar(birth_dt.year, birth_dt.month, birth_dt.day).replace(
                hour=birth_dt.hour, minute=birth_dt.minute
            )
        except ValueError as exc:
            return {
                "ok": False,
                "dt": None,
                "has_time": parsed["has_time"],
                "time_basis": None,
                "birth_source": "lunar_converted",
                "reason": f"lunar_convert_failed: {exc}",
            }
        birth_source = "lunar_converted"
    elif calendar == "lunar":
        birth_source = "solar_from_paipan"
    elif calendar in ("solar", "solar_unspecified"):
        birth_source = "solar_asis"
    else:
        birth_source = "unknown_calendar_as_solar"

    has_time = parsed["has_time"]
    time_basis = "clock_beijing"
    solar_time_raw = _norm_text(record["true_solar_time_raw"])
    if solar_time_raw:
        solar_time = parse_true_solar_time(solar_time_raw)
        if solar_time is None:
            return {
                "ok": False,
                "dt": None,
                "has_time": has_time,
                "time_basis": None,
                "birth_source": birth_source,
                "reason": "birth_true_solar_time_unparseable",
            }
        birth_dt = solar_time
        has_time = True
        time_basis = "true_solar"

    return {
        "ok": True,
        "dt": birth_dt,
        "has_time": has_time,
        "time_basis": time_basis,
        "birth_source": birth_source,
        "reason": None,
    }


# ---------------------------------------------------------------------------
# 事件、去重、漏斗
# ---------------------------------------------------------------------------


def marriage_events(record: dict[str, Any]) -> list[dict[str, Any]]:
    """婚姻域事件（``domains`` 含 marriage）且年份为整数。"""
    events = []
    for event in record.get("events") or []:
        domains = event.get("domains") or []
        year = event.get("year")
        if "marriage" in domains and isinstance(year, int):
            events.append(event)
    return events


def dedupe_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """按 ``duplicate_key`` 去重，保留首次出现者，并统计重复组。"""
    seen: dict[str, str] = {}
    unique: list[dict[str, Any]] = []
    groups: dict[str, list[str]] = {}
    removed: list[dict[str, Any]] = []
    for record in records:
        key = record["duplicate_key"]
        groups.setdefault(key, []).append(record["raw_id"])
        if key in seen:
            removed.append(
                {
                    "case_id": record["raw_id"],
                    "duplicate_key": key,
                    "kept_case_id": seen[key],
                    "reason": "duplicate",
                }
            )
            continue
        seen[key] = record["raw_id"]
        unique.append(record)
    duplicated = {key: ids for key, ids in groups.items() if len(ids) > 1}
    stats = {
        "groups": len(duplicated),
        "extra_records": sum(len(ids) - 1 for ids in duplicated.values()),
        "group_sizes": {
            str(size): sum(1 for ids in duplicated.values() if len(ids) == size)
            for size in sorted({len(ids) for ids in duplicated.values()})
        },
        "keys": [
            {"duplicate_key": key, "case_ids": ids}
            for key, ids in sorted(duplicated.items(), key=lambda item: item[1][0])
        ],
        "removed": removed,
    }
    return unique, stats


def build_cases(
    unique: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """产出评测案例、无法成为候选的剔除清单、候选但不可评测的清单。"""
    cases: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    unusable: list[dict[str, Any]] = []
    for record in unique:
        reasons: list[str] = []
        if record["gender"] not in GENDERS:
            reasons.append("missing_gender")
        birth = resolve_birth(record)
        if not birth["ok"]:
            reasons.append(birth["reason"])
        events = marriage_events(record)
        if not events:
            reasons.append("no_marriage_event_with_year")

        if not (birth["ok"] and events and record["gender"] in GENDERS):
            excluded.append(
                {
                    "case_id": record["raw_id"],
                    "reasons": reasons,
                    "birth_datetime_raw": record["birth_datetime_raw"],
                    "calendar_type": record["calendar_type"],
                }
            )
            continue

        birth_year = birth["dt"].year
        payload_events = []
        for event in events:
            age = event["year"] - birth_year
            payload_events.append(
                {
                    "year": event["year"],
                    "age": age,
                    "age_plausible": AGE_MIN <= age <= AGE_MAX,
                    "polarity": event.get("polarity"),
                    "text": event.get("text") or "",
                }
            )
        usable = birth["has_time"] and any(item["age_plausible"] for item in payload_events)
        cases.append(
            {
                "case_id": record["raw_id"],
                "gender": record["gender"],
                "birth_datetime_raw": record["birth_datetime_raw"],
                "birth_dt": birth["dt"].isoformat(sep=" "),
                "birth_year": birth_year,
                "birth_has_time": birth["has_time"],
                "time_basis": birth["time_basis"],
                "birth_source": birth["birth_source"],
                "calendar_type_raw": record["calendar_type"],
                "marriage_events": payload_events,
                "usable_for_timing": usable,
                "quality_grade": record["quality_grade"],
                "quality_flags": record["quality_flags"],
                "duplicate_key": record["duplicate_key"],
            }
        )
        if not usable:
            if not birth["has_time"]:
                unusable.append({"case_id": record["raw_id"], "reasons": ["birth_date_only"]})
            else:
                unusable.append(
                    {
                        "case_id": record["raw_id"],
                        "reasons": [f"no_marriage_event_in_age_window_{AGE_MIN}_{AGE_MAX}"],
                    }
                )

    cases.sort(key=lambda item: item["case_id"])
    excluded.sort(key=lambda item: item["case_id"])
    unusable.sort(key=lambda item: item["case_id"])
    stats = {
        "with_gender": sum(1 for record in unique if record["gender"] in GENDERS),
        "birth_date_ok": sum(1 for record in unique if resolve_birth(record)["ok"]),
        "birth_time_ok": sum(
            1 for record in unique if resolve_birth(record)["ok"] and resolve_birth(record)["has_time"]
        ),
        "marriage_cases": sum(1 for record in unique if marriage_events(record)),
        "marriage_events": sum(len(marriage_events(record)) for record in unique),
        "timing_candidates": len(cases),
        "candidates_with_time": sum(1 for case in cases if case["birth_has_time"]),
        "usable_for_timing": sum(1 for case in cases if case["usable_for_timing"]),
        "usable_marriage_events": sum(
            1
            for case in cases
            if case["usable_for_timing"]
            for event in case["marriage_events"]
            if event["age_plausible"]
        ),
        "excluded_records": len(excluded),
        "unusable_candidates": len(unusable),
    }
    return cases, excluded, unusable, stats


# ---------------------------------------------------------------------------
# 基线
# ---------------------------------------------------------------------------


def _band_key(lo: int, hi: int) -> str:
    return f"age_{lo}" if lo == hi else f"age_{lo}_{hi}"


def compute_band_hits(rows: list[tuple[int, list[int]]]) -> dict[str, dict[str, Any]]:
    """rows = [(birth_year, [event_year, ...]), ...]。"""
    result: dict[str, dict[str, Any]] = {}
    for key in BAND_ORDER:
        lo, hi = CARD_BASELINE["bands"][key]["range"]
        hits = sum(1 for birth_year, years in rows if any(lo <= year - birth_year <= hi for year in years))
        result[key] = {
            "range": [lo, hi],
            "hits": hits,
            "rate_pct": round(100.0 * hits / len(rows), 1) if rows else 0.0,
        }
    return result


def card_reproduction_baseline(records: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """复现任务卡 §2 的实测口径：未去重、出生字段按原值（不二次换算农历）。"""
    rows: list[tuple[int, list[int]]] = []
    for record in records:
        if record["gender"] not in GENDERS:
            continue
        parsed = parse_clock_datetime(record["birth_datetime_raw"])
        if not parsed["ok"]:
            continue
        birth_year = parsed["dt"].year
        years = [
            event["year"]
            for event in marriage_events(record)
            if AGE_MIN <= event["year"] - birth_year <= AGE_MAX
        ]
        if years:
            rows.append((birth_year, years))
    return compute_band_hits(rows), rows


def cleaned_reference_baseline(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """清洗口径参考：去重 + 农历换算 + 出生时刻齐备 + 合理婚龄窗口。"""
    usable = [case for case in cases if case["usable_for_timing"]]
    rows: list[tuple[int, list[int]]] = [
        (
            case["birth_year"],
            [event["year"] for event in case["marriage_events"] if event["age_plausible"]],
        )
        for case in usable
    ]
    bands = compute_band_hits(rows)
    return {"sample_size": len(usable), "bands": bands}


def diff_classification(
    records: list[dict[str, Any]],
    unique: list[dict[str, Any]],
    card_rows: list[tuple[int, list[int]]],
    cleaned: dict[str, Any],
) -> dict[str, Any]:
    """把「卡上数字 vs 清洗口径」的差异按五类归因，供中枢裁决。"""
    date_pool = [
        record
        for record in records
        if record["gender"] in GENDERS and parse_clock_datetime(record["birth_datetime_raw"])["ok"]
    ]
    date_pool_marriage = [record for record in date_pool if marriage_events(record)]
    unique_pool = [
        record
        for record in unique
        if record["gender"] in GENDERS and resolve_birth(record)["ok"] and marriage_events(record)
    ]
    noisy = 0
    for record in date_pool_marriage:
        birth_year = parse_clock_datetime(record["birth_datetime_raw"])["dt"].year
        if not any(event["year"] - birth_year >= AGE_MIN for event in marriage_events(record)):
            noisy += 1
    lunar_records = [record for record in records if record["calendar_type"] == "lunar"]
    lunar_no_paipan = [
        record for record in lunar_records if "排盘所用公历" not in (record.get("raw_text") or "")
    ]
    lunar_converted = 0
    lunar_failed = 0
    year_shift = 0
    for record in lunar_no_paipan:
        parsed = parse_clock_datetime(record["birth_datetime_raw"])
        if not parsed["ok"]:
            continue
        try:
            solar = _lunar_to_solar(parsed["dt"].year, parsed["dt"].month, parsed["dt"].day)
        except ValueError:
            lunar_failed += 1
            continue
        lunar_converted += 1
        if solar.year != parsed["dt"].year:
            year_shift += 1
    return {
        "missing": {
            "note": "缺性别 / 缺出生 / 缺时刻 / 无婚姻事件导致剔除的案例，逐条见 excluded_records",
            "raw_without_gender": sum(1 for record in records if record["gender"] not in GENDERS),
            "raw_without_birth_time": sum(
                1
                for record in records
                if not parse_clock_datetime(record["birth_datetime_raw"])["ok"]
                or not parse_clock_datetime(record["birth_datetime_raw"])["has_time"]
            ),
            "raw_marriage_cases": sum(1 for record in records if marriage_events(record)),
            "raw_marriage_events": sum(len(marriage_events(record)) for record in records),
            "implausible_age_events_dropped_cases": noisy,
        },
        "duplicates": {
            "note": "按 duplicate_key 去重；卡上 392 为未去重口径",
            "raw_date_pool": len(date_pool_marriage),
            "deduped_candidates": len(unique_pool),
            "sample_delta": len(unique_pool) - len(date_pool_marriage),
        },
        "lunar": {
            "note": "birth_datetime_raw 对含「排盘所用公历」的农历记录已是公历；无该标记的按农历换算",
            "lunar_records": len(lunar_records),
            "lunar_with_paipan_solar": len(lunar_records) - len(lunar_no_paipan),
            "lunar_no_paipan": len(lunar_no_paipan),
            "lunar_converted": lunar_converted,
            "lunar_convert_failed": lunar_failed,
            "lunar_year_shift_after_conversion": year_shift,
        },
        "age_field": {
            "note": "年龄 = event.year - birth.year（整年差）",
            "card_sample": len(card_rows),
            "cleaned_sample": cleaned["sample_size"],
        },
        "event_type": {
            "note": "婚姻事件 = events[].domains 含 'marriage' 且 year 为整数",
            "raw_marriage_events": sum(len(marriage_events(record)) for record in records),
        },
    }


# ---------------------------------------------------------------------------
# 农历交叉验证
# ---------------------------------------------------------------------------


def lunar_verification(records: list[dict[str, Any]]) -> dict[str, Any]:
    """验证「birth_datetime_raw 是否已是公历」。

    对含中文农历日期的记录做 农历→公历 换算并与 birth_datetime_raw 比对：
    match = 已换算；late_zi_minus1d = 排盘日与出生钟表日相差一日（23 时晚子时）；
    mismatch_other = 无法解释的差异；no_pattern = 无中文农历日期可抽取。
    """
    stats = {
        "lunar_records": 0,
        "match": 0,
        "late_zi_minus1d": 0,
        "mismatch_other": 0,
        "convert_error": 0,
        "no_pattern": 0,
        "no_birth": 0,
    }
    buckets: dict[str, list[dict[str, Any]]] = {"match": [], "late_zi_minus1d": [], "mismatch_other": []}
    for record in records:
        if record["calendar_type"] != "lunar":
            continue
        stats["lunar_records"] += 1
        parsed = parse_clock_datetime(record["birth_datetime_raw"])
        text_date = extract_lunar_text_date(record.get("raw_text"))
        if text_date is None:
            stats["no_pattern"] += 1
            continue
        if not parsed["ok"]:
            stats["no_birth"] += 1
            continue
        try:
            solar = _lunar_to_solar(*text_date)
        except ValueError:
            stats["convert_error"] += 1
            continue
        delta_days = (parsed["dt"].date() - solar.date()).days
        if delta_days == 0:
            stats["match"] += 1
            verdict = "match"
        elif delta_days == -1 and parsed["dt"].hour == 23:
            stats["late_zi_minus1d"] += 1
            verdict = "late_zi_minus1d"
        else:
            stats["mismatch_other"] += 1
            verdict = "mismatch_other"
        if len(buckets[verdict]) < 3:
            buckets[verdict].append(
                {
                    "case_id": record["raw_id"],
                    "lunar_text": _LUNAR_TEXT_RE.search(record.get("raw_text") or "").group(0),
                    "lunar_to_solar": solar.date().isoformat(),
                    "birth_datetime_raw": record["birth_datetime_raw"],
                    "verdict": verdict,
                }
            )

    converted_samples: list[dict[str, Any]] = []
    for record in records:
        if record["calendar_type"] != "lunar" or "排盘所用公历" in (record.get("raw_text") or ""):
            continue
        parsed = parse_clock_datetime(record["birth_datetime_raw"])
        if not parsed["ok"]:
            continue
        try:
            solar = _lunar_to_solar(parsed["dt"].year, parsed["dt"].month, parsed["dt"].day)
        except ValueError:
            # 换算失败已在上一循环计入 stats["convert_error"]，此处只影响抽样展示。
            continue
        entry = {
            "case_id": record["raw_id"],
            "birth_datetime_raw": record["birth_datetime_raw"],
            "lunar_to_solar": solar.date().isoformat(),
            "year_shift": solar.year - parsed["dt"].year,
        }
        if entry["year_shift"] and sum(1 for item in converted_samples if item["year_shift"]) < 2:
            converted_samples.append(entry)
        elif len(converted_samples) < 4:
            converted_samples.append(entry)

    samples = buckets["match"][:3] + buckets["late_zi_minus1d"][:2] + buckets["mismatch_other"][:1]
    return {
        "stats": stats,
        "samples": samples,
        "converted_samples": converted_samples[:4],
    }


# ---------------------------------------------------------------------------
# 落盘
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _payload_sha256(payload: dict[str, Any], volatile: tuple[str, ...]) -> str:
    core = {key: value for key, value in payload.items() if key not in volatile}
    material = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _git_head() -> tuple[str, str | None]:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return "unavailable", f"git 调用失败：{exc}"
    if completed.returncode != 0:
        return "unavailable", f"git 退出码 {completed.returncode}：{completed.stderr.strip()}"
    return completed.stdout.strip(), None


def _write_json(path: Path, payload: dict[str, Any], volatile: tuple[str, ...]) -> bool:
    """内容稳定时不重写（保证复跑幂等）。返回是否写入。"""
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{path} 不是合法 JSON：{exc}") from exc
        if _payload_sha256(existing, volatile) == _payload_sha256(payload, volatile):
            return False
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def _assert_no_prediction_fields(payload: Any, path: str = "$") -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).lower()
            if any(token in lowered for token in PREDICTION_KEY_DENYLIST):
                raise RuntimeError(f"评测集出现预测字段：{path}.{key}")
            _assert_no_prediction_fields(value, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _assert_no_prediction_fields(value, f"{path}[{index}]")


def _render_report(
    *,
    generated_at: str,
    git_head: str,
    source_sha: str,
    total: int,
    unique_count: int,
    duplicate_stats: dict[str, Any],
    funnel: dict[str, Any],
    excluded: list[dict[str, Any]],
    card_bands: dict[str, dict[str, Any]],
    cleaned: dict[str, Any],
    lunar: dict[str, Any],
    diff: dict[str, Any],
    unusable: list[dict[str, Any]],
) -> str:
    lines: list[str] = []
    add = lines.append
    add("# T-148 · 婚姻应期评测集 v1（人读报告）")
    add("")
    add(f"- 生成脚本：`tools/timing_eval_set.py`")
    add(f"- 数据源：`cases/raw_feedback/parsed/real_cases_990.jsonl`（sha256 `{source_sha}`）")
    add(f"- 生成时间：`{generated_at}`")
    add(f"- 生成时 HEAD：`{git_head}`")
    add("- 性质：**只造尺子，不建模**。本报告与配套 JSON 不含任何应期预测字段。")
    add("")
    add("## 1. 解析漏斗")
    add("")
    add("| 环节（去重后） | 数量 |")
    add("|---|---:|")
    add(f"| 原始记录 | {total} |")
    add(f"| `duplicate_key` 去重后 | {unique_count}（重复组 {duplicate_stats['groups']}，多余记录 {duplicate_stats['extra_records']}） |")
    add(f"| 有性别（男/女） | {funnel['with_gender']} |")
    add(f"| 出生日期可解析 | {funnel['birth_date_ok']} |")
    add(f"| 出生时刻可解析 | {funnel['birth_time_ok']} |")
    add(f"| 有婚姻事件且带年份 | {funnel['marriage_cases']}（事件 {funnel['marriage_events']} 条） |")
    add(f"| 性别 + 出生 + 婚姻事件（候选） | {funnel['timing_candidates']}（有出生时刻 {funnel['candidates_with_time']}） |")
    add(f"| **可用于应期评测（`usable_for_timing`）** | **{funnel['usable_for_timing']}**（其中合理婚龄窗口内事件 {funnel['usable_marriage_events']} 条） |")
    add("")
    add("`usable_for_timing` = 有性别 + 有出生时刻（可排盘）+ 至少一条 15–50 岁的婚姻域事件。")
    add("")
    add("## 2. 解析失败分类（逐条见 `timing-eval-set-v1.json.excluded_records`）")
    add("")
    counter: dict[str, list[str]] = {}
    for item in excluded:
        primary = item["reasons"][0] if item["reasons"] else "unknown"
        counter.setdefault(primary, []).append(item["case_id"])
    add("| 原因 | 案例数 | 案例（去重后） |")
    add("|---|---:|---|")
    for reason, ids in sorted(counter.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        sample = "、".join(ids[:8]) + ("…" if len(ids) > 8 else "")
        add(f"| `{reason}` | {len(ids)} | {sample} |")
    add(f"| `duplicate`（重复被剔除） | {duplicate_stats['extra_records']} | 见 JSON `duplicates.removed` |")
    add("")
    add("候选案例中不可评测（`usable_for_timing = false`）的逐条原因见 JSON `unusable_cases`：")
    add("")
    other: dict[str, list[str]] = {}
    for item in unusable:
        primary = item["reasons"][0] if item["reasons"] else "unknown"
        other.setdefault(primary, []).append(item["case_id"])
    add("| 原因 | 案例数 | 案例 |")
    add("|---|---:|---|")
    for reason, ids in sorted(other.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        sample = "、".join(ids[:8]) + ("…" if len(ids) > 8 else "")
        add(f"| `{reason}` | {len(ids)} | {sample} |")
    add("")
    add("分类口径：`missing_gender` 缺性别；`birth_empty` 出生字段为空；`birth_no_date` 无日期；")
    add("`birth_bad_date` / `birth_bad_time` 非法日期或时刻；`birth_date_only` 只有日期无时刻；")
    add("`lunar_convert_failed` 农历换算失败；`no_marriage_event_with_year` 无婚姻域事件。")
    add("")
    add("## 3. 冻结基线（任务卡 §2 口径，现场复现）")
    add("")
    add("口径：未去重、`birth_datetime_raw` 按原值、`age = event.year - birth.year`、")
    add(f"保留 {AGE_MIN}–{AGE_MAX} 岁婚姻事件、案例至少 1 条保留事件。")
    add(f"（上限 {AGE_MAX} 为非约束：本数据婚姻事件年龄最大 50。）")
    add("")
    add(f"> **口径说明**：{AGE_MIN} 岁下限是复现任务卡 §2「n=392」所需的推断条件（任务卡未写明该过滤）；")
    add("> 加上它才能同时得到 392 与 44/177/191/245。不加上它则样本为 419，卡上数字无法复现。")
    add("")
    add("| 猜测 | 命中 | 样本量 | 命中率 | 任务卡 |")
    add("|---|---:|---:|---:|---:|")
    for key in BAND_ORDER:
        band = card_bands[key]
        expected = CARD_BASELINE["bands"][key]
        add(f"| {key}（{band['range'][0]}–{band['range'][1]} 岁） | {band['hits']} | {CARD_BASELINE['sample_size']} | **{band['rate_pct']:.1f}%** | {expected['rate_pct']:.1f}% |")
    add("")
    add("## 4. 清洗口径参考（去重 + 农历换算 + 出生时刻齐备）")
    add("")
    add("| 猜测 | 命中 | 样本量 | 命中率 |")
    add("|---|---:|---:|---:|")
    for key in BAND_ORDER:
        band = cleaned["bands"][key]
        add(f"| {key}（{band['range'][0]}–{band['range'][1]} 岁） | {band['hits']} | {cleaned['sample_size']} | {band['rate_pct']:.1f}% |")
    add("")
    add("> 清洗口径与任务卡口径的差异分类见第 5 节；**验收基线仍以第 3 节为准**，")
    add("> 清洗口径仅作下游对照，不得用来替换冻结数字。")
    add("")
    add("## 5. 差异分类（卡上 392 vs 清洗口径）")
    add("")
    dup = diff["duplicates"]
    lun = diff["lunar"]
    miss = diff["missing"]
    add("| 类别 | 事实 | 影响 |")
    add("|---|---|---|")
    add(f"| 重复 | `duplicate_key` 重复组 {duplicate_stats['groups']} 个 / 多余记录 {duplicate_stats['extra_records']} 条 | 卡上 392 为**未去重**口径；去重后候选 {dup['deduped_candidates']}（未去重 {dup['raw_date_pool']}） |")
    add(f"| 农历 | 农历记录 {lun['lunar_records']}，其中含「排盘所用公历」{lun['lunar_with_paipan_solar']}；其余 {lun['lunar_no_paipan']} 条中 {lun['lunar_converted']} 条按农历换算（失败 {lun['lunar_convert_failed']}），其余为出生字段缺失 | 换算后跨公历年 {lun['lunar_year_shift_after_conversion']} 例，影响 26 岁带个别命中 |")
    add(f"| 缺失 | 缺性别 {miss['raw_without_gender']}、缺出生时刻 {miss['raw_without_birth_time']}、无婚姻事件案例由漏斗剔除 | 见第 1、2 节 |")
    add(f"| 年龄字段 | 整年差 `event.year - birth.year` | 无月日修正；年龄带按任务卡原文 |")
    add(f"| 事件类型 | 仅 `domains` 含 `marriage` 且 `year` 为整数 | 原始婚姻域事件 {miss['raw_marriage_events']} 条 |")
    add("")
    add("## 6. 农历换算抽样验证")
    add("")
    add("方法：从 `raw_text` 抽取「农(阴)历:YYYY 年X月X日」，用 `lunar-python` 换算为公历，")
    add("与 `birth_datetime_raw` 的日期比对。若大量 `match`，说明该字段对含排盘标记的记录**已是公历**，")
    add("不得二次换算。")
    add("")
    add("| 判定 | 数量 | 含义 |")
    add("|---|---:|---|")
    add(f"| `match` | {lunar['stats']['match']} | 已换算为公历，日期一致 |")
    add(f"| `late_zi_minus1d` | {lunar['stats']['late_zi_minus1d']} | 记录的是出生钟表日（23 时晚子时，排盘日 +1） |")
    add(f"| `mismatch_other` | {lunar['stats']['mismatch_other']} | 无法解释的差异（需人工复核） |")
    add(f"| `convert_error` | {lunar['stats']['convert_error']} | 该农历日期不存在 |")
    add(f"| `no_pattern` | {lunar['stats']['no_pattern']} | 原文无中文农历日期（多为数字农历，另行换算） |")
    add("")
    add("抽样：")
    add("")
    add("| case_id | 农历原文 | 换算公历 | `birth_datetime_raw` | 判定 |")
    add("|---|---|---|---|---|")
    for sample in lunar["samples"]:
        add(f"| {sample['case_id']} | {sample['lunar_text']} | {sample['lunar_to_solar']} | {sample['birth_datetime_raw']} | `{sample['verdict']}` |")
    add("")
    add("数字农历（`no_pattern`，原文无中文农历日期）按农历换算为公历的抽样：")
    add("")
    add("| case_id | `birth_datetime_raw`（农历） | 换算公历 | 年份位移 |")
    add("|---|---|---|---:|")
    for sample in lunar.get("converted_samples", []):
        add(
            f"| {sample['case_id']} | {sample['birth_datetime_raw']} | "
            f"{sample['lunar_to_solar']} | {sample['year_shift']:+d} |"
        )
    add("")
    add("## 7. 使用须知")
    add("")
    add("- 评测时只用 `usable_for_timing = true` 的案例；预测必须在读取 `marriage_events` 之前冻结。")
    add("- 任何应期模型的命中率必须同时胜过第 3 节（4 个年龄带）与人口学常识基线。")
    add("- 本评测集不含预测字段；如需扩展，另建 v2，不得改写 v1 基线。")
    add("")
    return "\n".join(lines) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    if not SOURCE_PATH.exists():
        print(f"[T-148] 数据源不存在：{SOURCE_PATH}", file=sys.stderr)
        return 4

    try:
        import lunar_python  # noqa: F401  # 仅探测依赖，避免静默降级
    except ImportError as exc:
        print(f"[T-148] 缺少 lunar-python，无法验证/换算农历：{exc}", file=sys.stderr)
        return 5

    records: list[dict[str, Any]] = []
    read_errors: list[dict[str, Any]] = []
    with SOURCE_PATH.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                read_errors.append({"line": line_no, "reason": "json_decode", "detail": str(exc)})

    unique, duplicate_stats = dedupe_records(records)
    cases, excluded, unusable, funnel = build_cases(unique)
    card_bands, card_rows = card_reproduction_baseline(records)
    cleaned = cleaned_reference_baseline(cases)
    lunar = lunar_verification(records)
    diff = diff_classification(records, unique, card_rows, cleaned)

    # ---- 复现校验（Amendment 1）：任一数字不符即停，不落盘、不调参 ----
    mismatches: list[str] = []
    if len(card_rows) != CARD_BASELINE["sample_size"]:
        mismatches.append(f"样本量 {len(card_rows)} != {CARD_BASELINE['sample_size']}")
    for key in BAND_ORDER:
        expected = CARD_BASELINE["bands"][key]
        got = card_bands[key]
        if got["hits"] != expected["hits"] or got["rate_pct"] != expected["rate_pct"]:
            mismatches.append(
                f"{key}: hits {got['hits']}/{len(card_rows)}={got['rate_pct']:.1f}% "
                f"!= card {expected['hits']}/{CARD_BASELINE['sample_size']}={expected['rate_pct']:.1f}%"
            )

    print("[T-148] 婚姻应期评测集")
    print(f"  source   : {SOURCE_PATH.relative_to(ROOT).as_posix()}（{len(records)} 条，读取失败 {len(read_errors)}）")
    print(
        f"  dedupe   : {len(records)} -> {len(unique)}"
        f"（重复组 {duplicate_stats['groups']}，多余 {duplicate_stats['extra_records']}）"
    )
    print(
        "  funnel   : "
        f"gender={funnel['with_gender']} birth_date={funnel['birth_date_ok']} "
        f"birth_time={funnel['birth_time_ok']} marriage_cases={funnel['marriage_cases']} "
        f"candidates={funnel['timing_candidates']} usable={funnel['usable_for_timing']}"
    )
    print(f"  baseline : n={len(card_rows)}（任务卡口径：未去重 + 出生字段原值 + 合理婚龄窗口）")
    for key in BAND_ORDER:
        band = card_bands[key]
        print(
            f"    {key:<10} {band['hits']:>3}/{len(card_rows)} = {band['rate_pct']:>5.1f}%"
            f"  (card {CARD_BASELINE['bands'][key]['rate_pct']:.1f}%)"
        )
    print(
        f"  cleaned  : n={cleaned['sample_size']}"
        + "  "
        + "  ".join(f"{key}={cleaned['bands'][key]['rate_pct']:.1f}%" for key in BAND_ORDER)
    )
    print(
        "  lunar    : "
        f"records={lunar['stats']['lunar_records']} match={lunar['stats']['match']} "
        f"late_zi={lunar['stats']['late_zi_minus1d']} other={lunar['stats']['mismatch_other']} "
        f"no_pattern={lunar['stats']['no_pattern']}"
    )

    if mismatches:
        print("\n[DIFF] 任务卡 §2 基线未能现场复现，已停止落盘（禁止调参对齐）：", file=sys.stderr)
        for item in mismatches:
            print(f"  - {item}", file=sys.stderr)
        print("\n差异分类（供中枢裁决）：", file=sys.stderr)
        print(json.dumps(diff, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    if read_errors:
        print("\n[DIFF] 数据源存在无法解析的 JSON 行：", file=sys.stderr)
        print(json.dumps(read_errors, ensure_ascii=False, indent=2), file=sys.stderr)
        return 4

    frozen_at = None
    frozen_head = None
    if BASELINE_PATH.exists():
        try:
            existing_baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[T-148] 冻结基线不是合法 JSON：{exc}", file=sys.stderr)
            return 3
        frozen_at = existing_baseline.get("frozen_at")
        frozen_head = existing_baseline.get("git_head")
    generated_at = frozen_at or datetime.now().astimezone().isoformat(timespec="seconds")
    if frozen_head:
        git_head, git_error = frozen_head, None
    else:
        git_head, git_error = _git_head()
    if git_error:
        print(f"  git      : {git_head}（{git_error}）")
    source_sha = _sha256_file(SOURCE_PATH)

    eval_payload: dict[str, Any] = {
        "schema": SCHEMA_EVAL,
        "task": "T-148",
        "purpose": "婚姻应期评测集：只造尺子，不建模；不含任何应期预测字段。",
        "generated_at": generated_at,
        "script": "tools/timing_eval_set.py",
        "source": {
            "path": SOURCE_PATH.relative_to(ROOT).as_posix(),
            "records": len(records),
            "sha256": source_sha,
            "read_errors": read_errors,
        },
        "definition": {
            "gender": "gender in {男,女}",
            "birth": "true_solar_time_raw 优先（ADR-005），否则 birth_datetime_raw；"
            "农历记录仅在原文无『排盘所用公历』时换算",
            "age": "event.year - birth.year（整年差）",
            "marriage_event": "events[].domains 含 'marriage' 且 year 为整数",
            "usable_for_timing": f"有性别 + 有出生时刻 + 至少一条 {AGE_MIN}-{AGE_MAX} 岁婚姻事件",
            "dedupe": "duplicate_key 全等去重，保留首次出现",
        },
        "counts": {
            "raw_records": len(records),
            "unique_records": len(unique),
            "duplicate_groups": duplicate_stats["groups"],
            "duplicate_extra_records": duplicate_stats["extra_records"],
            **funnel,
        },
        "duplicates": {
            "groups": duplicate_stats["groups"],
            "extra_records": duplicate_stats["extra_records"],
            "group_sizes": duplicate_stats["group_sizes"],
            "keys": duplicate_stats["keys"],
            "removed": duplicate_stats["removed"],
        },
        "lunar_verification": lunar,
        "diff_classification": diff,
        "excluded_records": excluded,
        "unusable_cases": unusable,
        "cases": cases,
    }
    _assert_no_prediction_fields(eval_payload)

    baseline_payload: dict[str, Any] = {
        "schema": SCHEMA_BASELINE,
        "task": "T-148",
        "status": "frozen",
        "immutable": True,
        "notice": "此文件一经生成不得修改（T-148 §3.3 / §7.1）。如需变更，另建 v2 并由中枢裁决；本脚本拒绝覆盖不一致的冻结基线。",
        "frozen_at": generated_at,
        "git_head": git_head,
        "script": "tools/timing_eval_set.py",
        "source": {
            "path": SOURCE_PATH.relative_to(ROOT).as_posix(),
            "records": len(records),
            "sha256": source_sha,
        },
        "definition": {
            "population": "原始 992 条记录（未去重；复现任务卡 §2 中枢实测口径）",
            "filters": [
                "gender in {男,女}",
                "birth_datetime_raw 可按原值解析出日期（不二次换算农历）",
                "events[].domains 含 'marriage' 且 year 为整数",
                f"age = event.year - birth.year，保留 {AGE_MIN} <= age <= {AGE_MAX}（上限非约束：本数据最大 50）",
                "案例至少保留 1 条婚姻事件",
            ],
            "age_definition": "event.year - birth.year（整年差，无月日修正）",
            "dedupe": "none",
            "lunar": "birth_datetime_raw 按原值使用",
            "bands": {key: CARD_BASELINE["bands"][key]["range"] for key in BAND_ORDER},
        },
        "sample_size": len(card_rows),
        "bands": {key: {"range": card_bands[key]["range"], "hits": card_bands[key]["hits"], "rate_pct": card_bands[key]["rate_pct"]} for key in BAND_ORDER},
        "card_expectation": CARD_BASELINE,
        "card_match": True,
        "cleaned_reference": {
            "notice": "参考对照，不是验收基线：去重 + 农历换算 + 出生时刻齐备 + 合理婚龄窗口",
            "sample_size": cleaned["sample_size"],
            "bands": cleaned["bands"],
        },
        "difference_classification": diff,
    }
    baseline_payload["payload_sha256"] = _payload_sha256(
        baseline_payload, ("frozen_at", "payload_sha256", "git_head")
    )

    report = _render_report(
        generated_at=generated_at,
        git_head=git_head,
        source_sha=source_sha,
        total=len(records),
        unique_count=len(unique),
        duplicate_stats=duplicate_stats,
        funnel=funnel,
        excluded=excluded,
        card_bands=card_bands,
        cleaned=cleaned,
        lunar=lunar,
        diff=diff,
        unusable=unusable,
    )

    if BASELINE_PATH.exists():
        try:
            existing = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[T-148] 冻结基线不是合法 JSON：{exc}", file=sys.stderr)
            return 3
        if existing.get("payload_sha256") != baseline_payload["payload_sha256"]:
            print("[T-148] 冻结基线指纹不一致，拒绝覆盖（§3.3 不得修改）：", file=sys.stderr)
            print(
                f"  existing={existing.get('payload_sha256')}\n  computed={baseline_payload['payload_sha256']}",
                file=sys.stderr,
            )
            print("  如确需变更，请由中枢裁决并另建 v2。", file=sys.stderr)
            return 3
        print(f"  baseline : 已冻结，指纹一致（{baseline_payload['payload_sha256'][:12]}…），未改写")
    else:
        BASELINE_PATH.write_text(
            json.dumps(baseline_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"  baseline : 已冻结 -> {BASELINE_PATH.relative_to(ROOT).as_posix()}")

    eval_written = _write_json(EVAL_PATH, eval_payload, ("generated_at",))
    report_written = False
    if not REPORT_PATH.exists() or REPORT_PATH.read_text(encoding="utf-8") != report:
        REPORT_PATH.write_text(report, encoding="utf-8")
        report_written = True

    print(
        f"  wrote    : eval={'yes' if eval_written else 'unchanged'} "
        f"report={'yes' if report_written else 'unchanged'} "
        f"cases={len(cases)}"
    )
    print("  status   : OK（任务卡 §2 四个年龄带与 n=392 现场复现）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
