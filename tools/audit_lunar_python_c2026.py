"""只读审计 C-2026 案例中的 lunar-python 四柱与大运结果。"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from lunar_python import Solar

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPORTS = ROOT / "reports"
CASES = ROOT / "cases"
GANZHI_60 = tuple(
    f"{gan}{zhi}"
    for index in range(60)
    for gan, zhi in [("甲乙丙丁戊己庚辛壬癸"[index % 10], "子丑寅卯辰巳午未申酉戌亥"[index % 12])]
)
LIUNIAN_ANCHORS = {
    1980: "庚申",
    1984: "甲子",
    2005: "乙酉",
    2013: "癸巳",
    2020: "庚子",
    2024: "甲辰",
    2026: "丙午",
}
OUT_OF_SCOPE_QIYUN_ANCHORS = (
    ("RF000449", (1997, 4, 2, 1, 57, 0), 1, (0, 10, 24, 9)),
    ("RF000957", (2002, 10, 11, 20, 30, 0), 1, (0, 9, 7, 7)),
)
RAW_FILES = (
    CASES / "raw_feedback/parsed/wenzhen_pending_analysis_samples.jsonl",
    CASES / "raw_feedback/parsed/wenzhen_repan_completed.jsonl",
)
CASE_ID_RE = re.compile(r"^(C-2026-(?:RF\d{6}|\d{3}))-")
START_RE = re.compile(r"出生后(\d+)年(\d+)月(\d+)天(\d+)小时")
GAN_YINYANG = {
    "甲": "阳", "乙": "阴", "丙": "阳", "丁": "阴", "戊": "阳",
    "己": "阴", "庚": "阳", "辛": "阴", "壬": "阳", "癸": "阴",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def raw_id(record: dict[str, Any]) -> str:
    value = str(record.get("raw_id") or record.get("id") or "")
    match = re.search(r"(\d{6})$", value)
    return f"RF{match.group(1)}" if match else ""


def load_raw_index() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    structures: dict[str, Any] = {}
    for path in RAW_FILES:
        rows = load_jsonl(path)
        structures[str(path.relative_to(ROOT))] = {
            "count": len(rows),
            "top_keys": Counter(tuple(sorted(row)) for row in rows).most_common(5),
            "base_keys": Counter(tuple(sorted((row.get("base") or {}))) for row in rows).most_common(5),
            "value_types": {key: type(value).__name__ for key, value in rows[0].items()} if rows else {},
            "four_keys": Counter(tuple(sorted((row.get("four") or {}))) for row in rows).most_common(5),
        }
        for row in rows:
            rid = raw_id(row)
            if rid:
                index.setdefault(rid, row)
    return index, structures


def report_case_ids() -> list[str]:
    ids: set[str] = set()
    for path in REPORTS.glob("C-2026*.md"):
        match = CASE_ID_RE.match(path.name)
        if match:
            ids.add(match.group(1))
    return sorted(ids)


def case_path(case_id: str) -> Path | None:
    matches = sorted(CASES.glob(f"{case_id}-*/input.md"))
    return matches[0] if len(matches) == 1 else None


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```yaml\s*\n(.*?)\n```", text, re.DOTALL)
    if not match:
        return {}
    value = yaml.safe_load(match.group(1))
    return value if isinstance(value, dict) else {}


def gender_code(value: Any, case_id: str) -> int:
    text = str(value or "")
    return 1 if text.startswith("男") or "-乾-" in case_id else 0


def expected_forward(year_gan: str, gender: int) -> bool:
    yang = GAN_YINYANG[year_gan] == "阳"
    return yang if gender == 1 else not yang


def adjacent_ganzhi(value: str, forward: bool) -> str | None:
    if value not in GANZHI_60:
        return None
    index = GANZHI_60.index(value)
    return GANZHI_60[(index + (1 if forward else -1)) % 60]


def claimed_sequence_direction(month_pillar: str, sequence: list[str]) -> str | None:
    if not sequence:
        return None
    if sequence[0] == adjacent_ganzhi(month_pillar, True):
        return "forward"
    if sequence[0] == adjacent_ganzhi(month_pillar, False):
        return "backward"
    return "non_adjacent"


def solar_datetime(value: Any) -> datetime:
    return datetime(
        value.getYear(), value.getMonth(), value.getDay(),
        value.getHour(), value.getMinute(), value.getSecond(),
    )


def nearest_jie(birth: datetime, lunar: Any) -> dict[str, Any]:
    candidates = (lunar.getPrevJie(), lunar.getNextJie())
    values = [
        (item.getName(), solar_datetime(item.getSolar()))
        for item in candidates
    ]
    name, moment = min(values, key=lambda item: abs((birth - item[1]).total_seconds()))
    return {
        "name": name,
        "datetime": moment.isoformat(sep=" "),
        "signed_hours": round((birth - moment).total_seconds() / 3600, 3),
        "absolute_hours": round(abs((birth - moment).total_seconds()) / 3600, 3),
    }


def liunian_anchor_audit() -> dict[str, Any]:
    # 独立历法锚点，不由 lunar-python 或案例字段生成。
    from engine.predicates.cycles import liunian_ganzhi

    rows = []
    for year, expected in LIUNIAN_ANCHORS.items():
        actual = str(liunian_ganzhi(year))
        rows.append({"year": year, "expected": expected, "actual": actual, "match": expected == actual})
    return {
        "evidence": "A_independent_calendar_anchors",
        "matched": sum(row["match"] for row in rows),
        "total": len(rows),
        "records": rows,
    }


def qiyun_hours(value: tuple[int, int, int, int] | list[int]) -> int:
    # 仅用于差异分层；按 lunar-python 的 1 年=12 月、1 月=30 天口径折算。
    year, month, day, hour = value
    return (((year * 12 + month) * 30 + day) * 24 + hour)


def out_of_scope_qiyun_anchor_audit() -> dict[str, Any]:
    rows = []
    for raw_case_id, birth, gender, expected in OUT_OF_SCOPE_QIYUN_ANCHORS:
        ec = Solar.fromYmdHms(*birth).getLunar().getEightChar()
        ec.setSect(2)
        sect_results = {}
        for sect in (1, 2):
            yun = ec.getYun(gender, sect)
            actual = (yun.getStartYear(), yun.getStartMonth(), yun.getStartDay(), yun.getStartHour())
            sect_results[str(sect)] = {
                "actual": actual,
                "absolute_delta_days": round(abs(qiyun_hours(actual) - qiyun_hours(expected)) / 24, 3),
                "start_solar": str(yun.getStartSolar()),
            }
        rows.append({
            "raw_case_id": raw_case_id,
            "expected": expected,
            "evidence": "A_raw_wenzhen",
            "in_report_case_scope": False,
            "sect_results": sect_results,
        })
    return {"total": len(rows), "records": rows}


def parse_birth(data: dict[str, Any]) -> tuple[datetime | None, str]:
    birth = data.get("birth") or data.get("出生") or {}
    for key in ("太阳时", "公历", "出生时间"):
        raw = birth.get(key) if isinstance(birth, dict) else None
        if raw:
            text = str(raw).strip()
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    return datetime.strptime(text, fmt), key
                except ValueError:
                    pass
    return None, ""


def claimed_pillars(data: dict[str, Any], case_id: str) -> tuple[str, str, str, str] | None:
    pillars = data.get("四柱") or {}
    if isinstance(pillars, dict):
        values = tuple(str(pillars.get(key, "")) for key in ("年柱", "月柱", "日柱", "时柱"))
        if all(values):
            return values  # type: ignore[return-value]
    tail = case_id.split("-")[-1]
    if len(tail) == 8:
        return tuple(tail[i:i + 2] for i in range(0, 8, 2))  # type: ignore[return-value]
    return None


def claimed_dayun(data: dict[str, Any]) -> dict[str, Any]:
    value = data.get("大运") or {}
    return value if isinstance(value, dict) else {}


def raw_start(record: dict[str, Any] | None) -> tuple[int, int, int, int] | None:
    base = (record or {}).get("base") or {}
    match = START_RE.search(str(base.get("Start") or ""))
    return tuple(map(int, match.groups())) if match else None  # type: ignore[return-value]


def raw_bazi(record: dict[str, Any] | None) -> tuple[str, str, str, str] | None:
    text = str((record or {}).get("bazi") or "")
    return tuple(text[i:i + 2] for i in range(0, 8, 2)) if len(text) == 8 else None  # type: ignore[return-value]


def audit_case(case_id: str, raw_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    input_path = case_path(case_id)
    result: dict[str, Any] = {"case_id": case_id, "input": str(input_path.relative_to(ROOT)) if input_path else None}
    if input_path is None:
        result["status"] = "missing_or_ambiguous_input"
        return result
    data = parse_frontmatter(input_path)
    birth, birth_source = parse_birth(data)
    result["birth_source"] = birth_source or None
    if birth is None:
        result["status"] = "missing_precise_birth"
        return result
    rid_match = re.search(r"RF\d{6}", case_id)
    rid = rid_match.group(0) if rid_match else ""
    raw = raw_index.get(rid)
    claimed = claimed_pillars(data, case_id)
    independent_pillars = raw_bazi(raw) or claimed
    independence = "A_raw_wenzhen" if raw_bazi(raw) else "B_case_input"
    birth_data = data.get("birth") or data.get("出生") or {}
    gender = gender_code(
        birth_data.get("性别") if isinstance(birth_data, dict) else None,
        input_path.parent.name,
    )
    lunar = Solar.fromYmdHms(birth.year, birth.month, birth.day, birth.hour, birth.minute, birth.second).getLunar()
    ec = lunar.getEightChar()
    ec.setSect(2)
    actual_pillars = (ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime())
    yun = ec.getYun(gender, 1)
    actual_dayun = [(item.getGanZhi(), item.getStartYear()) for item in yun.getDaYun(11) if item.getGanZhi()]
    dy = claimed_dayun(data)
    rows = dy.get("排布") if isinstance(dy.get("排布"), list) else []
    expected_sequence = [str(row.get("干支")) for row in rows if isinstance(row, dict) and row.get("干支")]
    expected_start_years: list[int] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        span = row.get("起讫") or row.get("起讫年")
        match = re.match(r"(\d{4})", str(span or ""))
        if match:
            expected_start_years.append(int(match.group(1)))
    start_ref = raw_start(raw)
    actual_start = (yun.getStartYear(), yun.getStartMonth(), yun.getStartDay(), yun.getStartHour())
    late_zi = birth.hour == 23
    sequence_actual = [item[0] for item in actual_dayun]
    direction_expected = expected_forward(actual_pillars[0][0], gender)
    case_sequence_direction = claimed_sequence_direction(actual_pillars[1], expected_sequence)
    expected_direction_name = "forward" if direction_expected else "backward"
    result.update({
        "status": "audited",
        "birth": birth.isoformat(sep=" "),
        "birth_gender": "M" if gender == 1 else "F",
        "year_gan_yinyang": GAN_YINYANG[actual_pillars[0][0]],
        "late_zi_excluded": late_zi,
        "nearest_jie": nearest_jie(birth, lunar),
        "evidence": independence,
        "metric_evidence": {
            "pillars": independence,
            "direction": "R_gender_year_gan_rule",
            "first_dayun": "B_migrated_case_input",
            "sequence": "B_migrated_case_input",
            "qiyun_exact": "A_raw_wenzhen" if start_ref else None,
            "dayun_start_years": "B_migrated_case_input",
        },
        "pillars_expected": independent_pillars,
        "pillars_actual": actual_pillars,
        "pillars_match": independent_pillars == actual_pillars if independent_pillars else None,
        "direction_expected": direction_expected,
        "direction_actual": bool(yun.isForward()),
        "direction_match": direction_expected == bool(yun.isForward()),
        "case_sequence_direction": case_sequence_direction,
        "case_sequence_direction_matches_rule": case_sequence_direction == expected_direction_name if case_sequence_direction in {"forward", "backward"} else None,
        "first_dayun_expected": expected_sequence[0] if expected_sequence else None,
        "first_dayun_actual": sequence_actual[0] if sequence_actual else None,
        "first_dayun_match": expected_sequence[0] == sequence_actual[0] if expected_sequence and sequence_actual else None,
        "sequence_expected": expected_sequence,
        "sequence_actual": sequence_actual,
        "sequence_match": sequence_actual[:len(expected_sequence)] == expected_sequence if expected_sequence else None,
        "qiyun_expected": start_ref,
        "qiyun_actual": actual_start,
        "qiyun_match": start_ref == actual_start if start_ref else None,
        "start_years_expected": expected_start_years,
        "start_years_actual": [item[1] for item in actual_dayun],
        "start_years_match": [item[1] for item in actual_dayun[:len(expected_start_years)]] == expected_start_years if expected_start_years else None,
        "start_solar_actual": str(yun.getStartSolar()),
        "raw_has_dy": bool((raw or {}).get("dy") or (raw or {}).get("four", {}).get("dy")),
        "raw_has_ln": bool((raw or {}).get("ln") or (raw or {}).get("four", {}).get("ln")),
    })
    return result


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    audited = [row for row in records if row.get("status") == "audited"]
    formal = [row for row in audited if not row.get("late_zi_excluded")]
    def metric(name: str) -> dict[str, int]:
        comparable = [row for row in formal if row.get(name) is not None]
        return {"matched": sum(row[name] is True for row in comparable), "total": len(comparable)}
    sequence_direction_rows = [
        row for row in formal if row.get("case_sequence_direction_matches_rule") is not None
    ]
    near_jie = [row for row in formal if row["nearest_jie"]["absolute_hours"] <= 48]
    qiyun_rows = [row for row in formal if row.get("qiyun_expected")]
    for row in qiyun_rows:
        row["qiyun_absolute_delta_days"] = round(
            abs(qiyun_hours(row["qiyun_actual"]) - qiyun_hours(row["qiyun_expected"])) / 24,
            3,
        )
    a_pillar_rows = [row for row in formal if row.get("evidence") == "A_raw_wenzhen"]
    return {
        "report_case_ids": len(records),
        "audited": len(audited),
        "formal_non_late_zi": len(formal),
        "late_zi_excluded": sum(bool(row.get("late_zi_excluded")) for row in audited),
        "late_zi_case_ids": [row["case_id"] for row in audited if row.get("late_zi_excluded")],
        "near_jie_within_48h": {
            "total": len(near_jie),
            "case_ids": [row["case_id"] for row in near_jie],
        },
        "coverage": {
            "gender": Counter(row.get("birth_gender") for row in formal),
            "year_gan_yinyang": Counter(row.get("year_gan_yinyang") for row in formal),
            "direction": Counter("forward" if row.get("direction_expected") else "backward" for row in formal),
        },
        "evidence": Counter(row.get("evidence") for row in audited),
        "metric_evidence": {
            "pillars": f"A_raw_wenzhen for {len(a_pillar_rows)} formal RF rows; B_case_input otherwise",
            "direction": "R_gender_year_gan_rule",
            "first_dayun": "B_migrated_case_input",
            "sequence": "B_migrated_case_input",
            "qiyun_exact": "A_raw_wenzhen",
            "dayun_start_years": "B_migrated_case_input",
            "liunian": "A_independent_calendar_anchors",
            "dayun_at_year": "insufficient_no_independent_dayun_intervals",
        },
        "pillars": metric("pillars_match"),
        "direction": metric("direction_match"),
        "first_dayun": metric("first_dayun_match"),
        "sequence": metric("sequence_match"),
        "qiyun_exact": metric("qiyun_match"),
        "dayun_start_years": metric("start_years_match"),
        "case_sequence_direction_vs_rule": {
            "matched": sum(row["case_sequence_direction_matches_rule"] is True for row in sequence_direction_rows),
            "total": len(sequence_direction_rows),
            "mismatch_case_ids": [row["case_id"] for row in sequence_direction_rows if row["case_sequence_direction_matches_rule"] is False],
        },
        "qiyun_tolerance": {
            "exact": sum(row["qiyun_absolute_delta_days"] == 0 for row in qiyun_rows),
            "within_1_day": sum(row["qiyun_absolute_delta_days"] <= 1 for row in qiyun_rows),
            "within_10_days": sum(row["qiyun_absolute_delta_days"] <= 10 for row in qiyun_rows),
            "within_31_days": sum(row["qiyun_absolute_delta_days"] <= 31 for row in qiyun_rows),
            "over_31_days_case_ids": [row["case_id"] for row in qiyun_rows if row["qiyun_absolute_delta_days"] > 31],
            "total": len(qiyun_rows),
        },
        "qiyun_mismatch_case_ids": [row["case_id"] for row in formal if row.get("qiyun_match") is False],
        "raw_dy_available": sum(bool(row.get("raw_has_dy")) for row in formal),
        "raw_ln_available": sum(bool(row.get("raw_has_ln")) for row in formal),
        "status": Counter(row.get("status") for row in records),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raw_index, structures = load_raw_index()
    records = [audit_case(case_id, raw_index) for case_id in report_case_ids()]
    payload = {
        "summary": summarize(records),
        "liunian_anchor_audit": liunian_anchor_audit(),
        "out_of_scope_qiyun_anchor_audit": out_of_scope_qiyun_anchor_audit(),
        "raw_structures": structures,
        "records": records,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=list)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
