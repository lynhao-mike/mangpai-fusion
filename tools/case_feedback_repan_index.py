"""tools/case_feedback_repan_index.py · 问真排盘补录索引生成器

用途：
    扫描 cases/raw_feedback/case_drafts/RF-.../input.md，生成一份人工补问真排盘索引。

输出：
    cases/raw_feedback/case_drafts/wenzhen-repan-index.md

边界：
    - 只读取 case draft。
    - 不改写单个 RF 草稿。
    - 不创建正式 C-... case。
    - 不运行 preflight / pipeline。
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "cases"
DRAFTS_DIR = CASES_DIR / "raw_feedback" / "case_drafts"
PARSED_CASES = CASES_DIR / "raw_feedback" / "parsed" / "real_cases_990.jsonl"
DEFAULT_OUTPUT = DRAFTS_DIR / "wenzhen-repan-index.md"
MALE_OUTPUT = DRAFTS_DIR / "wenzhen-repan-index-male.md"
FEMALE_OUTPUT = DRAFTS_DIR / "wenzhen-repan-index-female.md"

BIRTH_BLOCK_RE = re.compile(r"\nbirth:\n(?P<body>.*?)(?=\n\n四柱:)", re.S)
SIZHU_BLOCK_RE = re.compile(r"\n四柱:\n(?P<body>.*?)(?=\n\n藏干:)", re.S)
EVENT_RE = re.compile(r"^\s*- year:\s*(?P<year>\S+)", re.M)
RAW_ID_RE = re.compile(r"RF-\d{4}-\d{6}")
QUALITY_RANK = {"A": 0, "B": 1, "C": 2, "D": 3}


@dataclass(frozen=True)
class QualityMeta:
    quality_grade: str = ""
    score: int = 0
    event_count: int = 0


@dataclass(frozen=True)
class RepanEntry:
    raw_id: str
    input_path: pathlib.Path
    birth_block: str
    sizhu_block: str
    event_count: int
    needs_repan: bool
    quality_grade: str
    score: int
    promoted: bool


def collect_entries(drafts_dir: pathlib.Path = DRAFTS_DIR) -> list[RepanEntry]:
    quality_by_raw_id = _load_quality_meta()
    promoted_raw_ids = _collect_promoted_raw_ids()
    entries: list[RepanEntry] = []
    for input_path in sorted(drafts_dir.glob("RF-*/input.md")):
        raw_id = input_path.parent.name
        text = input_path.read_text(encoding="utf-8")
        birth_block = _extract_block(BIRTH_BLOCK_RE, text)
        sizhu_block = _extract_block(SIZHU_BLOCK_RE, text)
        needs_repan = "待补" in sizhu_block or "待补" in birth_block
        event_count = len(EVENT_RE.findall(text))
        quality_meta = quality_by_raw_id.get(raw_id, QualityMeta(event_count=event_count))
        entries.append(
            RepanEntry(
                raw_id=raw_id,
                input_path=input_path,
                birth_block=birth_block,
                sizhu_block=sizhu_block,
                event_count=max(event_count, quality_meta.event_count),
                needs_repan=needs_repan,
                quality_grade=quality_meta.quality_grade,
                score=quality_meta.score,
                promoted=raw_id in promoted_raw_ids,
            )
        )
    return entries


def render_index(
    entries: list[RepanEntry],
    *,
    only_needs_repan: bool = True,
    gender: str | None = None,
) -> str:
    selected = _select_entries(entries, only_needs_repan=only_needs_repan, gender=gender)
    title_suffix = f" · {gender}" if gender else ""
    lines: list[str] = [
        f"# 问真排盘补录索引{title_suffix} · 真实反馈 case drafts",
        "",
        f"> 生成时间：{datetime.now(timezone.utc).isoformat()}",
        f"> 来源目录：`{_rel(DRAFTS_DIR)}`",
        "",
        "## 使用方法",
        "",
        "1. 每条标题后先看 `太阳时: “性别”`，下一行是纯数字太阳时。",
        "2. 将纯数字太阳时复制到问真八字 APP 排盘。",
        "3. 将问真排盘原文粘贴到 `问真排盘：` 下方的占位区，替换 `？`。",
        "4. 其他字段不用手填；后续按 RF 编号回到原草稿自动/半自动补齐。",
        "",
        "## 统计",
        "",
        f"- draft 总数：{len(entries)}",
        f"- 已生成正式案例排除数：{sum(1 for entry in entries if entry.promoted)}",
        f"- 本索引待补排盘数：{len(selected)}",
        "- 排序：反馈质量等级优先，其次评分、事件数与 RF 编号。",
        "",
        "---",
        "",
    ]
    for idx, entry in enumerate(selected, start=1):
        lines.extend(_render_entry(idx, entry))
    return "\n".join(lines).rstrip() + "\n"



def _select_entries(
    entries: list[RepanEntry],
    *,
    only_needs_repan: bool = True,
    gender: str | None = None,
) -> list[RepanEntry]:
    selected = [e for e in entries if (e.needs_repan or not only_needs_repan) and not e.promoted]
    if gender:
        selected = [e for e in selected if _display_gender(e.birth_block) == gender]
    selected.sort(key=_quality_sort_key)
    return selected


def write_index(
    *,
    output: pathlib.Path = DEFAULT_OUTPUT,
    only_needs_repan: bool = True,
    gender: str | None = None,
    dry_run: bool = False,
) -> tuple[pathlib.Path, int, int]:
    entries = collect_entries()
    selected_count = len(
        _select_entries(entries, only_needs_repan=only_needs_repan, gender=gender)
    )
    content = render_index(entries, only_needs_repan=only_needs_repan, gender=gender)
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    return output, len(entries), selected_count



def write_split_indexes(
    *,
    only_needs_repan: bool = True,
    dry_run: bool = False,
) -> list[tuple[pathlib.Path, int, int]]:
    return [
        write_index(
            output=MALE_OUTPUT,
            only_needs_repan=only_needs_repan,
            gender="男",
            dry_run=dry_run,
        ),
        write_index(
            output=FEMALE_OUTPUT,
            only_needs_repan=only_needs_repan,
            gender="女",
            dry_run=dry_run,
        ),
    ]


def _render_entry(index: int, entry: RepanEntry) -> list[str]:
    quality = entry.quality_grade or "待补"
    return [
        f"## {index:03d}. {entry.raw_id} · 质量 {quality} · 评分 {entry.score} · 事件 {entry.event_count}",
        f"太阳时: “{_display_gender(entry.birth_block)}”",
        "",
        _compact_solar_time(entry.birth_block),
        "",
        "问真排盘：",
        "",
        "```text",
        "？",
        "```",
        "",
        "---",
        "",
    ]


def _extract_block(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    if not match:
        return "  待补: true"
    return match.group("body").rstrip()


def _compact_solar_time(birth_block: str) -> str:
    value = _birth_value(birth_block, "太阳时") or _birth_value(birth_block, "公历")
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits[:12] if len(digits) >= 12 else digits or "待补"
def _birth_value(birth_block: str, key: str) -> str:
    for line in birth_block.splitlines():
        stripped = line.strip()
        if not stripped.startswith(f"{key}:"):
            continue
        return stripped.split(":", 1)[1].strip().strip('"')
    return ""


def _display_gender(birth_block: str) -> str:
    value = _birth_value(birth_block, "性别").upper()
    if value == "M" or value == "男":
        return "男"
    if value == "F" or value == "女":
        return "女"
    return value or "待补"




def _quality_sort_key(entry: RepanEntry) -> tuple[int, int, int, str]:
    return (
        QUALITY_RANK.get(entry.quality_grade.strip().upper(), 9),
        -entry.score,
        -entry.event_count,
        entry.raw_id,
    )


def _load_quality_meta(path: pathlib.Path = PARSED_CASES) -> dict[str, QualityMeta]:
    if not path.exists():
        return {}
    result: dict[str, QualityMeta] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        raw_id = str(record.get("raw_id", "")).strip()
        if not raw_id:
            continue
        events = record.get("events", [])
        event_count = len(events) if isinstance(events, list) else 0
        score = int(record.get("score", 0) or 0) or event_count * 10 + _quality_bonus(record)
        result[raw_id] = QualityMeta(
            quality_grade=str(record.get("quality_grade", "")).strip().upper(),
            score=score,
            event_count=event_count,
        )
    return result


def _quality_bonus(record: dict[str, object]) -> int:
    bonus = 0
    if record.get("birth_place_sanitized"):
        bonus += 1
    if record.get("true_solar_time_raw"):
        bonus += 1
    questions = record.get("questions", [])
    if isinstance(questions, list) and questions:
        bonus += 1
    quality_flags = record.get("quality_flags", [])
    if isinstance(quality_flags, list) and not quality_flags:
        bonus += 2
    return bonus


def _collect_promoted_raw_ids(cases_dir: pathlib.Path = CASES_DIR) -> set[str]:
    result: set[str] = set()
    for input_path in cases_dir.glob("C-*/input.md"):
        text = input_path.read_text(encoding="utf-8")
        result.update(RAW_ID_RE.findall(text))
    return result


def _rel(path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="生成真实反馈问真排盘补录索引")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="输出 Markdown 路径")
    parser.add_argument("--include-complete", action="store_true", help="也包含已补完整四柱的样本")
    parser.add_argument("--split-gender", action="store_true", help="按男/女分别输出两份 Markdown")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写文件")
    args = parser.parse_args(argv)

    print("case_feedback_repan_index")
    print(f"  dry_run: {args.dry_run}")
    if args.split_gender:
        for output, total, selected in write_split_indexes(
            only_needs_repan=not args.include_complete,
            dry_run=args.dry_run,
        ):
            print(f"  drafts: {total}")
            print(f"  indexed: {selected}")
            print(f"  output: {_rel(output)}")
    else:
        output, total, selected = write_index(
            output=pathlib.Path(args.output),
            only_needs_repan=not args.include_complete,
            dry_run=args.dry_run,
        )
        print(f"  drafts: {total}")
        print(f"  indexed: {selected}")
        print(f"  output: {_rel(output)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
