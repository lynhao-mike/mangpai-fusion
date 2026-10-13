"""将高质量阳历原始反馈批量转换为已自动排盘的 as-of 候选 case。

默认 dry-run；只有显式传入 ``--write`` 才会在 cases/ 下创建全新的
``C-2026-RF*`` 目录。本工具不运行 preflight/pipeline，不更新 cases-index.md。
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from engine.asof.birth_to_bazi import BaziResult, calc_bazi

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "cases" / "raw_feedback" / "parsed" / "real_cases_990.jsonl"
DEFAULT_CASES_ROOT = ROOT / "cases"
UNSAFE_FLAGS = {"abnormal_birth_date", "very_long_possible_concatenation"}


LATE_ZI_HOUR_SKIP_REASON = "23:00-23:59边界排除"


def is_late_zi_hour_boundary(dt: datetime) -> bool:
    """判断出生时刻是否落在23:00:00-23:59:59（晚子时日柱换日歧义区间）。"""
    return dt.hour == 23


@dataclass(frozen=True, slots=True)
class CaseResult:
    raw_id: str
    success: bool
    case_id: str = ""
    case_dir: str = ""
    error: str = ""
    datetime_source: str = ""
    bazi_raw: str = ""
    bazi_match: bool | None = None


@dataclass(slots=True)
class BatchResult:
    dry_run: bool
    requested: int
    eligible: int
    selected: int
    cases: list[CaseResult] = field(default_factory=list)
    skipped_late_zi_hour: list[str] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        compared = [item for item in self.cases if item.bazi_match is not None]
        matched = sum(item.bazi_match is True for item in compared)
        successful = sum(item.success for item in self.cases)
        return {
            "dry_run": self.dry_run,
            "requested": self.requested,
            "eligible": self.eligible,
            "selected": self.selected,
            "paipan_success": successful,
            "paipan_success_rate": round(successful / self.selected, 4) if self.selected else 0.0,
            "bazi_compared": len(compared),
            "bazi_matched": matched,
            "bazi_match_rate": round(matched / len(compared), 4) if compared else None,
            "skipped_late_zi_hour_count": len(self.skipped_late_zi_hour),
            "skipped_late_zi_hour_raw_ids": list(self.skipped_late_zi_hour),
            "skipped_late_zi_hour_reason": LATE_ZI_HOUR_SKIP_REASON if self.skipped_late_zi_hour else "",
            "cases": [asdict(item) for item in self.cases],
        }


def load_records(path: Path = DEFAULT_SOURCE) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"JSONL line {line_number} is not an object")
        records.append(value)
    return records


def normalize_birth_datetime(raw: str) -> datetime:
    """解析数据集中已观察到的公历日期时间格式；缺时辰时拒绝猜测。"""
    text = str(raw or "").strip()
    if not text:
        raise ValueError("出生日期时间为空")
    text = text.translate(str.maketrans({"：": ":", "，": " ", "。": " "}))
    text = re.sub(r"\s+", " ", text)
    date_match = re.search(r"(?P<y>\d{4})\s*(?:年|[-./])\s*(?P<m>\d{1,2})\s*(?:月|[-./])\s*(?P<d>\d{1,2})\s*日?", text)
    if not date_match:
        raise ValueError(f"无法解析出生日期: {raw}")
    time_text = text[date_match.end() :].strip()
    time_match = re.search(r"(?P<h>\d{1,2})\s*(?::|点|时)\s*(?P<minute>\d{1,2})(?:\s*(?::|分)\s*(?P<second>\d{1,2}))?", time_text)
    if not time_match:
        raise ValueError(f"缺少可确认的出生时辰: {raw}")

    year, month, day = (int(date_match.group(name)) for name in ("y", "m", "d"))
    hour = int(time_match.group("h"))
    minute = int(time_match.group("minute"))
    second = int(time_match.group("second") or 0)
    if hour == 24:
        if minute or second:
            raise ValueError("24时仅允许24:00:00")
        return datetime(year, month, day) + timedelta(days=1)
    if hour > 23 or minute > 59 or second > 59:
        raise ValueError(f"出生时间超出范围: {raw}")
    return datetime(year, month, day, hour, minute, second)


def choose_birth_datetime(record: dict[str, Any]) -> tuple[datetime, str]:
    for field_name in ("true_solar_time_raw", "birth_datetime_raw"):
        value = str(record.get(field_name, "") or "").strip()
        if value:
            return normalize_birth_datetime(value), field_name
    raise ValueError("true_solar_time_raw 与 birth_datetime_raw 均为空")


def _gender(record: dict[str, Any]) -> tuple[str, str]:
    qian_kun = str(record.get("qian_kun", "") or "").strip()
    gender = str(record.get("gender", "") or "").strip()
    if qian_kun == "乾" or gender.startswith("男"):
        return "M", "乾"
    if qian_kun == "坤" or gender.startswith("女"):
        return "F", "坤"
    raise ValueError("缺少明确性别/乾坤")


def _is_eligible(record: dict[str, Any]) -> bool:
    flags = {str(item) for item in (record.get("quality_flags") or [])}
    events = record.get("events")
    return bool(
        str(record.get("quality_grade", "")).upper() in {"A", "B"}
        and record.get("calendar_type") == "solar"
        and (record.get("true_solar_time_raw") or record.get("birth_datetime_raw"))
        and isinstance(events, list)
        and events
        and not flags.intersection(UNSAFE_FLAGS)
    )


def _processable(record: dict[str, Any]) -> bool:
    try:
        choose_birth_datetime(record)
        _gender(record)
    except ValueError:
        return False
    return True


def _is_late_zi_hour_record(record: dict[str, Any]) -> bool:
    """判断记录解析出的出生时刻是否落在23:00-23:59边界（解析失败时视为非边界）。"""
    try:
        birth_dt, _source = choose_birth_datetime(record)
    except ValueError:
        return False
    return is_late_zi_hour_boundary(birth_dt)


def select_records(
    records: Iterable[dict[str, Any]],
    *,
    limit: int = 20,
    excluded_raw_ids: set[str] | None = None,
    exclude_late_zi_hour: bool = True,
    skipped_late_zi_hour: list[str] | None = None,
) -> list[dict[str, Any]]:
    """按 duplicate_key 去重，并优先保留可排盘且有 bazi_raw 的对照样本。

    ``exclude_late_zi_hour``（默认 True）会跳过出生时刻落在23:00:00-23:59:59的
    候选记录，因为该区间日柱换日口径存在 sect=1 与 sect=2 歧义（已在
    C-2026-RF000132 上验证过至少1例不一致）。传入 ``exclude_late_zi_hour=False``
    表示调用方已明确知情并接受该歧义风险，可强制纳入这类候选。
    """
    unique: list[tuple[int, dict[str, Any]]] = []
    seen: set[str] = set()
    excluded = excluded_raw_ids or set()
    for index, record in enumerate(records):
        raw_id = str(record.get("raw_id", ""))
        if not _is_eligible(record) or raw_id in excluded:
            continue
        if exclude_late_zi_hour and _is_late_zi_hour_record(record):
            if skipped_late_zi_hour is not None:
                skipped_late_zi_hour.append(raw_id)
            continue
        key = str(record.get("duplicate_key") or record.get("raw_id") or index)
        if key in seen:
            continue
        seen.add(key)
        unique.append((index, record))
    unique.sort(
        key=lambda item: (
            0 if item[1].get("bazi_raw") and _processable(item[1]) else 1,
            0 if _processable(item[1]) else 1,
            item[0],
        )
    )
    return [record for _, record in unique[:limit]]


def _yaml_quote(value: object) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)


def _compact_bazi(value: object) -> str:
    return "".join(str(value or "").split())


def _case_id(record: dict[str, Any], qian_kun: str, bazi: BaziResult) -> str:
    raw_digits = re.sub(r"\D", "", str(record.get("raw_id", "")))
    serial = raw_digits[-6:] if raw_digits else "UNKNOWN"
    return f"C-2026-RF{serial}-{qian_kun}-{''.join(bazi.pillars)}"


def render_input(
    record: dict[str, Any],
    case_id: str,
    birth_dt: datetime,
    datetime_source: str,
    bazi: BaziResult,
) -> str:
    gender, qian_kun = _gender(record)
    place = str(record.get("birth_place_sanitized", "") or "未提供")
    dayun_lines = "\n".join(
        f"    - 干支: {_yaml_quote(item['ganzhi'])}\n      起始年: {item['start_year']}"
        for item in bazi.dayun
    )
    return f"""# {case_id} · 自动排盘输入

> 来源：`cases/raw_feedback/parsed/real_cases_990.jsonl` 的 `{record.get('raw_id', '')}`。
> 本文件由 lunar-python 自动排盘生成；未运行 preflight/pipeline。

```yaml
schema_version: 1.2.0
case_meta:
  case_id: {_yaml_quote(case_id)}
  立案日期: {datetime.now(timezone.utc).date().isoformat()}
  命主代号: {_yaml_quote(record.get('raw_id', ''))}
  策略: AS_OF_RAW_FEEDBACK_CANDIDATE
  来源: 真实案例反馈990个案例

birth:
  性别: {gender}
  乾坤: {qian_kun}
  公历: {_yaml_quote(birth_dt.isoformat(sep=' ', timespec='seconds'))}
  出生地脱敏: {_yaml_quote(place)}
  时间来源: {datetime_source}
  真太阳时字段优先: {str(datetime_source == 'true_solar_time_raw').lower()}
  经度校正: false
  经度校正说明: "本模块未做地点、经度、时区或真太阳时换算；直接采用来源字段时间。"

四柱:
  年柱: {_yaml_quote(bazi.pillars[0])}
  月柱: {_yaml_quote(bazi.pillars[1])}
  日柱: {_yaml_quote(bazi.pillars[2])}
  时柱: {_yaml_quote(bazi.pillars[3])}

大运:
  算法: default_3day_1year
  日柱换日: midnight
  排布:
{dayun_lines}

known_facts: []
提问:
  - "仅作为 as-of 盲断候选；已知事件见 feedback.md。"
```

## 排盘口径

- 日柱：午夜换日，23:00–23:59 仍算当日，00:00 换至次日。
- 大运：lunar-python `getYun(gender, sect=1)`，三天折一年。
- 地点：仅保留脱敏出生地；本工具未做经度校正。
"""


def _escape_table(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def render_feedback(record: dict[str, Any], case_id: str) -> str:
    events = record.get("events") if isinstance(record.get("events"), list) else []
    rows = []
    for event in events:
        if not isinstance(event, dict):
            continue
        year = event.get("year", "未知")
        domains = ", ".join(str(item) for item in (event.get("domains") or []))
        rows.append(f"| {_escape_table(year)} | {_escape_table(event.get('text'))} | {_escape_table(domains)} |")
    event_rows = "\n".join(rows) or "| 未知 | 无可用事件 | |"
    return f"""# {case_id} · 原始反馈年表

> 来源：`cases/raw_feedback/parsed/real_cases_990.jsonl` 的 `{record.get('raw_id', '')}`。
> 这些是盲断后的核验材料；生成排盘时未把事件写入 input.md。

## 事件年表

| 年份 | 已知事实 | 功能域 |
|---:|---|---|
{event_rows}

## 数据审计

- 质量等级：{_escape_table(record.get('quality_grade'))}
- 质量标记：{_escape_table(', '.join(str(x) for x in (record.get('quality_flags') or [])) or '无')}
- 原始八字对照：{_escape_table(record.get('bazi_raw') or '无')}
"""


def run_batch(
    *,
    source: Path = DEFAULT_SOURCE,
    cases_root: Path = DEFAULT_CASES_ROOT,
    limit: int = 20,
    dry_run: bool = True,
    exclude_late_zi_hour: bool = True,
) -> BatchResult:
    """批量将真实反馈候选转换为 as-of case 目录。

    ``exclude_late_zi_hour``（默认 True）跳过23:00:00-23:59:59出生的候选，
    因为该时段日柱换日口径存在 sect=1/sect=2 歧义。传入 False 表示调用方
    已明确知情并接受该歧义、需要强制纳入这类候选。
    """
    records = load_records(source)
    eligible_count = len(
        select_records(records, limit=len(records), exclude_late_zi_hour=exclude_late_zi_hour)
    )
    existing_raw_ids = {
        f"RF-2026-{match.group(1)}"
        for path in cases_root.glob("C-2026-RF*-*")
        if (match := re.match(r"C-2026-RF(\d{6})-", path.name))
    }
    skipped_late_zi_hour: list[str] = []
    selected = select_records(
        records,
        limit=limit,
        excluded_raw_ids=existing_raw_ids,
        exclude_late_zi_hour=exclude_late_zi_hour,
        skipped_late_zi_hour=skipped_late_zi_hour,
    )
    result = BatchResult(
        dry_run=dry_run,
        requested=limit,
        eligible=eligible_count,
        selected=len(selected),
        skipped_late_zi_hour=skipped_late_zi_hour,
    )

    for record in selected:
        raw_id = str(record.get("raw_id", ""))
        try:
            birth_dt, datetime_source = choose_birth_datetime(record)
            gender, qian_kun = _gender(record)
            bazi = calc_bazi(birth_dt, gender)
            case_id = _case_id(record, qian_kun, bazi)
            case_dir = cases_root / case_id
            if case_dir.exists():
                raise FileExistsError(f"拒绝覆盖已存在目录: {case_dir}")
            raw_bazi = _compact_bazi(record.get("bazi_raw"))
            bazi_match = raw_bazi == "".join(bazi.pillars) if raw_bazi else None
            if not dry_run:
                case_dir.mkdir(parents=True, exist_ok=False)
                (case_dir / "input.md").write_text(
                    render_input(record, case_id, birth_dt, datetime_source, bazi), encoding="utf-8"
                )
                (case_dir / "feedback.md").write_text(render_feedback(record, case_id), encoding="utf-8")
            result.cases.append(
                CaseResult(
                    raw_id=raw_id,
                    success=True,
                    case_id=case_id,
                    case_dir=str(case_dir.relative_to(ROOT) if case_dir.is_relative_to(ROOT) else case_dir),
                    datetime_source=datetime_source,
                    bazi_raw=raw_bazi,
                    bazi_match=bazi_match,
                )
            )
        except (ValueError, TypeError, OSError) as exc:
            result.cases.append(CaseResult(raw_id=raw_id, success=False, error=str(exc)))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--cases-root", type=Path, default=DEFAULT_CASES_ROOT)
    parser.add_argument("--limit", type=int, default=20)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="仅预览（默认）")
    mode.add_argument("--write", action="store_true", help="创建全新的 C-2026-RF* case 目录")
    parser.add_argument(
        "--allow-late-zi-hour-boundary",
        action="store_true",
        help=(
            "明确知情后强制处理23:00:00-23:59:59出生的候选（默认排除，"
            "因该时段日柱换日口径存在 sect=1/sect=2 歧义）"
        ),
    )
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit 必须大于0")
    result = run_batch(
        source=args.source,
        cases_root=args.cases_root,
        limit=args.limit,
        dry_run=not args.write,
        exclude_late_zi_hour=not args.allow_late_zi_hour_boundary,
    )
    print(json.dumps(result.summary(), ensure_ascii=False, indent=2))
    return 0 if all(item.success for item in result.cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
