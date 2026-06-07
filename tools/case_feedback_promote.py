"""tools/case_feedback_promote.py · 真实反馈样本转案草稿工具

用途：
    从 cases/raw_feedback/parsed/real_cases_990.jsonl 中筛选 A/B 级样本，
    生成可人工补问真排盘的 case draft。

边界：
    - 不创建正式 cases/C-... 目录。
    - 不写 cases/cases-index.md。
    - 不运行 preflight / pipeline / report。
    - 不把真实案例反馈写入 theory/。

输出：
    cases/raw_feedback/case_drafts/RF-.../input.md
    cases/raw_feedback/case_drafts/RF-.../feedback.md
    cases/raw_feedback/case_drafts/RF-.../statement_index.json
    cases/raw_feedback/case_drafts/promote-summary.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_FEEDBACK_DIR = REPO_ROOT / "cases" / "raw_feedback"
PARSED_JSONL = RAW_FEEDBACK_DIR / "parsed" / "real_cases_990.jsonl"
DRAFTS_DIR = RAW_FEEDBACK_DIR / "case_drafts"
SUMMARY_PATH = DRAFTS_DIR / "promote-summary.json"
SCHEMA_VERSION = "case-feedback-promote/v0.1"

DEFAULT_GRADES = ("A", "B")
DEFAULT_MIN_EVENTS = 1
SKIP_FLAGS = {"abnormal_birth_date", "very_long_possible_concatenation"}


@dataclass
class PromoteDecision:
    raw_id: str
    selected: bool
    reasons: list[str] = field(default_factory=list)
    draft_dir: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_id": self.raw_id,
            "selected": self.selected,
            "reasons": self.reasons,
            "draft_dir": self.draft_dir,
        }


@dataclass
class PromoteResult:
    dry_run: bool
    source_jsonl: pathlib.Path
    output_dir: pathlib.Path
    decisions: list[PromoteDecision] = field(default_factory=list)
    selected_records: list[dict[str, Any]] = field(default_factory=list)
    started_at: str = ""
    generated_at: str = ""
    grades: tuple[str, ...] = DEFAULT_GRADES
    limit: Optional[int] = None
    min_events: int = DEFAULT_MIN_EVENTS
    require_bazi: bool = False
    include_duplicates: bool = False

    def summary(self) -> dict[str, Any]:
        grade_distribution: dict[str, int] = {}
        quality_flag_distribution: dict[str, int] = {}
        directly_formalizable = 0
        needs_wenzhen_repan = 0
        for record in self.selected_records:
            grade = str(record.get("quality_grade", ""))
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
            for flag in record.get("quality_flags", []):
                quality_flag_distribution[flag] = quality_flag_distribution.get(flag, 0) + 1
            if _has_complete_bazi(record):
                directly_formalizable += 1
            else:
                needs_wenzhen_repan += 1

        return {
            "schema_version": SCHEMA_VERSION,
            "dry_run": self.dry_run,
            "generated_at": self.generated_at,
            "source_jsonl": _rel(self.source_jsonl),
            "output_dir": _rel(self.output_dir),
            "summary_path": _rel(SUMMARY_PATH),
            "grades": list(self.grades),
            "limit": self.limit,
            "min_events": self.min_events,
            "require_bazi": self.require_bazi,
            "include_duplicates": self.include_duplicates,
            "evaluated_count": len(self.decisions),
            "selected_count": len(self.selected_records),
            "skipped_count": len([d for d in self.decisions if not d.selected]),
            "directly_formalizable_count": directly_formalizable,
            "needs_wenzhen_repan_count": needs_wenzhen_repan,
            "grade_distribution": grade_distribution,
            "quality_flag_distribution": quality_flag_distribution,
            "decisions": [d.to_dict() for d in self.decisions],
        }


def load_records(path: pathlib.Path = PARSED_JSONL) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"parsed JSONL not found: {_rel(path)}")
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_no}: {exc}") from exc
        if isinstance(item, dict):
            records.append(item)
    return records


def promote(
    *,
    source_jsonl: pathlib.Path = PARSED_JSONL,
    grades: Iterable[str] = DEFAULT_GRADES,
    limit: Optional[int] = None,
    min_events: int = DEFAULT_MIN_EVENTS,
    require_bazi: bool = False,
    include_duplicates: bool = False,
    dry_run: bool = False,
) -> PromoteResult:
    grade_tuple = tuple(str(g).upper() for g in grades)
    result = PromoteResult(
        dry_run=dry_run,
        source_jsonl=source_jsonl,
        output_dir=DRAFTS_DIR,
        started_at=datetime.now(timezone.utc).isoformat(),
        grades=grade_tuple,
        limit=limit,
        min_events=min_events,
        require_bazi=require_bazi,
        include_duplicates=include_duplicates,
    )

    selected_count = 0
    for record in load_records(source_jsonl):
        decision = _decide(
            record,
            grades=grade_tuple,
            min_events=min_events,
            require_bazi=require_bazi,
            include_duplicates=include_duplicates,
        )
        result.decisions.append(decision)
        if not decision.selected:
            continue
        if limit is not None and selected_count >= limit:
            decision.selected = False
            decision.reasons.append("over_limit")
            continue

        selected_count += 1
        raw_id = str(record.get("raw_id", f"RF-UNKNOWN-{selected_count:06d}"))
        draft_dir = DRAFTS_DIR / raw_id
        decision.draft_dir = _rel(draft_dir)
        result.selected_records.append(record)
        if not dry_run:
            _write_draft(record, draft_dir)

    result.generated_at = datetime.now(timezone.utc).isoformat()
    if not dry_run:
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        SUMMARY_PATH.write_text(
            json.dumps(result.summary(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return result


def _decide(
    record: dict[str, Any],
    *,
    grades: tuple[str, ...],
    min_events: int,
    require_bazi: bool,
    include_duplicates: bool,
) -> PromoteDecision:
    raw_id = str(record.get("raw_id", ""))
    reasons: list[str] = []
    grade = str(record.get("quality_grade", "")).upper()
    quality_flags = set(str(x) for x in record.get("quality_flags", []))
    events = record.get("events", []) if isinstance(record.get("events", []), list) else []

    if grade not in grades:
        reasons.append("grade_not_selected")
    if not record.get("qian_kun"):
        reasons.append("missing_qian_kun")
    if not (record.get("birth_datetime_raw") or record.get("true_solar_time_raw") or record.get("bazi_raw")):
        reasons.append("missing_birth_datetime_and_bazi")
    if len(events) < min_events:
        reasons.append("insufficient_events")
    if quality_flags & SKIP_FLAGS:
        reasons.append("unsafe_quality_flag")
    if not include_duplicates and "possible_duplicate" in quality_flags:
        reasons.append("possible_duplicate")
    if require_bazi and not _has_complete_bazi(record):
        reasons.append("missing_complete_bazi")

    return PromoteDecision(raw_id=raw_id, selected=not reasons, reasons=reasons)


def _write_draft(record: dict[str, Any], draft_dir: pathlib.Path) -> None:
    draft_dir.mkdir(parents=True, exist_ok=True)
    (draft_dir / "input.md").write_text(_render_input(record), encoding="utf-8")
    (draft_dir / "feedback.md").write_text(_render_feedback(record), encoding="utf-8")
    (draft_dir / "statement_index.json").write_text(
        json.dumps(_statement_index(record), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _render_input(record: dict[str, Any]) -> str:
    raw_id = str(record.get("raw_id", "RF-UNKNOWN"))
    qian_kun = str(record.get("qian_kun", "")) or "待补"
    gender = str(record.get("gender", "")) or "待补"
    sex = "F" if qian_kun == "坤" or gender.startswith("女") else "M" if qian_kun == "乾" or gender.startswith("男") else "待补"
    birth_time = str(record.get("birth_datetime_raw", "")) or "待补"
    true_solar_time = str(record.get("true_solar_time_raw", "")) or birth_time
    place = str(record.get("birth_place_raw", "")) or "待补"
    sanitized_place = str(record.get("birth_place_sanitized", "")) or place
    bazi = _split_bazi(str(record.get("bazi_raw", "")))
    events = _known_facts_yaml(record)

    return f"""# {raw_id} · 真实反馈候选草稿（待补问真排盘）

> 来源：`cases/raw_feedback/parsed/real_cases_990.jsonl` 中 `{raw_id}`。
> 状态：候选 case draft，仅用于人工补排盘与理论验证准备；未通过 `tools.preflight`，不得直接运行 pipeline。

```yaml
schema_version: 1.2.0
case_meta:
  case_id: {raw_id}
  立案日期: {datetime.now(timezone.utc).date().isoformat()}
  命主代号: {raw_id}
  策略: DRAFT
  来源: 真实案例反馈990个案例
  原始反馈ID: {raw_id}
  转案状态: 待补问真排盘

birth:
  性别: {sex}
  乾坤: {qian_kun}
  公历: "{birth_time}"
  农历: "待补"
  出生地: "{place}"
  出生地脱敏: "{sanitized_place}"
  真太阳时校正: true
  太阳时: "{true_solar_time}"

四柱:
  年柱: "{bazi[0]}"
  月柱: "{bazi[1]}"
  日柱: "{bazi[2]}"
  时柱: "{bazi[3]}"

藏干:
  年支: []
  月支: []
  日支: []
  时支: []

大运:
  起运岁数: 待补
  排布: []

神煞: {{}}
十二长生: {{}}
三宫元: {{}}

known_facts:
{events}

提问:
  - "用于理论验证：依据真实反馈事件回测命局结构、应期与功能域规则。"
```

## 待补清单

- [ ] 用问真八字 APP 按出生信息重新排盘。
- [ ] 补齐四柱、藏干、大运、神煞、十二长生。
- [ ] 复核出生地和真太阳时，删除过细个人地点。
- [ ] 通过 `python -m tools.preflight <input.md>` 后再转入正式 `cases/C-.../`。

## 原始反馈摘录

```text
{str(record.get("raw_text", "")).strip()}
```
"""


def _render_feedback(record: dict[str, Any]) -> str:
    raw_id = str(record.get("raw_id", "RF-UNKNOWN"))
    events = record.get("events", []) if isinstance(record.get("events", []), list) else []
    event_lines = "\n".join(
        f"- {event.get('year', '未知年')}：{event.get('text', '')}"
        for event in events
    ) or "- 待补"
    flags = ", ".join(str(x) for x in record.get("quality_flags", [])) or "无"
    privacy = ", ".join(str(x) for x in record.get("privacy_flags", [])) or "无"
    return f"""# {raw_id} · 反馈草稿

## 反馈来源

- 原始反馈ID：{raw_id}
- 源文件：{record.get('source_file', '')}
- 原文行号：{record.get('line_start', '')}-{record.get('line_end', '')}
- 质量等级：{record.get('quality_grade', '')}
- 质量标记：{flags}
- 隐私标记：{privacy}

## 已抽取事件

{event_lines}

## 反馈摄入状态

- 当前状态：待补排盘，未进入正式反馈校准。
- 后续动作：补齐正式 `input.md` 并生成 analyst report 后，再按 `templates/feedback.md` 改写为可摄入反馈。
"""


def _statement_index(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "statement-index/draft-v0.1",
        "case_id": record.get("raw_id", ""),
        "status": "draft_pending_wenzhen_repan",
        "source": {
            "raw_id": record.get("raw_id", ""),
            "source_file": record.get("source_file", ""),
            "line_start": record.get("line_start", ""),
            "line_end": record.get("line_end", ""),
        },
        "statements": [],
        "notes": [
            "真实反馈候选草稿；未生成规则断语，不进入 feedback_ingest。",
            "补齐问真排盘并转正式 case 后重建 statement_index.json。",
        ],
    }


def _known_facts_yaml(record: dict[str, Any]) -> str:
    events = record.get("events", []) if isinstance(record.get("events", []), list) else []
    if not events:
        return "  []"
    lines: list[str] = []
    for event in events:
        year = event.get("year", "待补")
        text = str(event.get("text", "")).replace('"', "'").strip()
        domains = event.get("domains", []) if isinstance(event.get("domains", []), list) else []
        event_type = domains[0] if domains else "other"
        lines.extend(
            [
                f"  - year: {year}",
                f"    type: {event_type}",
                f"    desc: \"{text}\"",
            ]
        )
    return "\n".join(lines)


def _split_bazi(value: str) -> tuple[str, str, str, str]:
    compact = "".join(value.split())
    if len(compact) == 8:
        return compact[0:2], compact[2:4], compact[4:6], compact[6:8]
    return "待补", "待补", "待补", "待补"


def _has_complete_bazi(record: dict[str, Any]) -> bool:
    compact = "".join(str(record.get("bazi_raw", "")).split())
    return len(compact) == 8


def _rel(path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _print_human(result: PromoteResult) -> None:
    summary = result.summary()
    print("case_feedback_promote")
    print(f"  dry_run: {summary['dry_run']}")
    print(f"  source: {summary['source_jsonl']}")
    print(f"  output_dir: {summary['output_dir']}")
    print(f"  evaluated: {summary['evaluated_count']}")
    print(f"  selected: {summary['selected_count']}")
    print(f"  directly_formalizable: {summary['directly_formalizable_count']}")
    print(f"  needs_wenzhen_repan: {summary['needs_wenzhen_repan_count']}")
    print(f"  grades: {summary['grade_distribution']}")


def _smoke() -> int:
    result = promote(dry_run=True, limit=3, min_events=1)
    if result.summary()["selected_count"] < 1:
        raise AssertionError("smoke expected at least one selected record")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="真实反馈 A/B 级样本转 case draft 工具")
    parser.add_argument("--source-jsonl", default=str(PARSED_JSONL), help="结构化真实反馈 JSONL")
    parser.add_argument("--grades", nargs="+", default=list(DEFAULT_GRADES), help="选择质量等级，默认 A B")
    parser.add_argument("--limit", type=int, default=None, help="最多生成多少个草稿")
    parser.add_argument("--min-events", type=int, default=DEFAULT_MIN_EVENTS, help="最少事件数，默认 1")
    parser.add_argument("--require-bazi", action="store_true", help="只选择已有完整四柱的记录")
    parser.add_argument("--include-duplicates", action="store_true", help="允许 possible_duplicate 样本入选")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写文件")
    parser.add_argument("--smoke", action="store_true", help="运行内置自检")
    args = parser.parse_args(argv)

    if args.smoke:
        return _smoke()

    result = promote(
        source_jsonl=pathlib.Path(args.source_jsonl),
        grades=args.grades,
        limit=args.limit,
        min_events=args.min_events,
        require_bazi=args.require_bazi,
        include_duplicates=args.include_duplicates,
        dry_run=args.dry_run,
    )
    _print_human(result)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
