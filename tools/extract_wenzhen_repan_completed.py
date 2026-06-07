"""Extract completed Wenzhen repan entries from split priority indexes.

Outputs a machine-readable completed sample set and a Top 30 review list for
multi-school Bazi analysis calibration. This tool only reads split index files
and writes parsed artifacts; it does not create formal cases.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DRAFTS_DIR = REPO_ROOT / "cases" / "raw_feedback" / "case_drafts"
PARSED_DIR = REPO_ROOT / "cases" / "raw_feedback" / "parsed"
MALE_INDEX = DRAFTS_DIR / "wenzhen-repan-index-male.md"
FEMALE_INDEX = DRAFTS_DIR / "wenzhen-repan-index-female.md"
DEFAULT_JSONL = PARSED_DIR / "wenzhen_repan_completed.jsonl"
DEFAULT_SUMMARY = PARSED_DIR / "wenzhen_repan_completed-summary.json"
DEFAULT_TOP30 = PARSED_DIR / "wenzhen_repan_top30.md"

ENTRY_RE = re.compile(r"(?m)^##\s+(?P<position>\d+)\.\s+(?P<raw_id>RF-\d{4}-\d{6})")
META_RE = re.compile(r"^(?P<key>[^:\n]+):\s*(?P<value>.*)$", re.M)
CODE_BLOCK_RE = re.compile(r"问真排盘：\s*\n\s*```text\n(?P<body>.*?)\n```", re.S)
REQUIRED_REPAN_MARKERS = ("$BASE", "$FOUR", "$DY_LOOP")
FOUR_LINE_RE = re.compile(r"^(?P<pillar>[YMDH]):(?P<body>.+)$", re.M)
BASE_LINE_RE = re.compile(r"^(?P<key>[A-Za-z]+):(?P<value>.*)$", re.M)
DY_HEADER_RE = re.compile(r"^(?:>\s*)?#(?P<year>\d{4}),", re.M)
LIU_YEAR_RE = re.compile(r"^>\s*(?P<year>\d{4}),", re.M)
VALID_BAZI_RE = re.compile(r"^(?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4}$")


@dataclass(frozen=True)
class CompletedRepanRecord:
    raw_id: str
    gender: str
    qian_kun: str
    priority: int
    original_index: int
    status: str
    event_count: int
    quality_grade: str
    score: int
    index_path: str
    index_position: int
    solar_digits: str
    base: dict[str, str]
    four: dict[str, str]
    bazi: str
    day_master: str
    day_branch: str
    void: str
    start: str
    dy_count: int
    liunian_count: int
    repan_complete: bool
    quality_flags: list[str]

    def sort_key(self) -> tuple[int, int, int, int, str]:
        return (-self.event_count, -self.score, _quality_rank(self.quality_grade), self.original_index, self.raw_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_id": self.raw_id,
            "gender": self.gender,
            "qian_kun": self.qian_kun,
            "priority": self.priority,
            "original_index": self.original_index,
            "status": self.status,
            "event_count": self.event_count,
            "quality_grade": self.quality_grade,
            "score": self.score,
            "index_path": self.index_path,
            "index_position": self.index_position,
            "solar_digits": self.solar_digits,
            "base": self.base,
            "four": self.four,
            "bazi": self.bazi,
            "day_master": self.day_master,
            "day_branch": self.day_branch,
            "void": self.void,
            "start": self.start,
            "dy_count": self.dy_count,
            "liunian_count": self.liunian_count,
            "repan_complete": self.repan_complete,
            "quality_flags": self.quality_flags,
        }


def extract_completed() -> list[CompletedRepanRecord]:
    records: list[CompletedRepanRecord] = []
    for path, gender in ((MALE_INDEX, "男"), (FEMALE_INDEX, "女")):
        records.extend(_extract_from_index(path, gender))
    return sorted(records, key=lambda record: record.sort_key())


def write_outputs(*, dry_run: bool = False) -> dict[str, Any]:
    records = extract_completed()
    summary = _build_summary(records, dry_run=dry_run)
    top30 = records[:30]
    if not dry_run:
        PARSED_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULT_JSONL.write_text(
            "\n".join(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) for record in records) + "\n",
            encoding="utf-8",
        )
        DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        DEFAULT_TOP30.write_text(_render_top30(top30, summary), encoding="utf-8")
    return summary


def _extract_from_index(path: pathlib.Path, gender: str) -> list[CompletedRepanRecord]:
    text = path.read_text(encoding="utf-8")
    matches = list(ENTRY_RE.finditer(text))
    records: list[CompletedRepanRecord] = []
    for idx, match in enumerate(matches):
        chunk = text[match.start() : matches[idx + 1].start() if idx + 1 < len(matches) else len(text)]
        record = _parse_entry(path, gender, int(match.group("position")), match.group("raw_id"), chunk)
        if record and record.repan_complete:
            records.append(record)
    return records


def _parse_entry(
    path: pathlib.Path,
    gender: str,
    index_position: int,
    raw_id: str,
    chunk: str,
) -> CompletedRepanRecord | None:
    meta = {match.group("key").strip(): match.group("value").strip() for match in META_RE.finditer(chunk)}
    repan_match = CODE_BLOCK_RE.search(chunk)
    if not repan_match:
        return None
    repan = repan_match.group("body").strip()
    repan_complete = _is_complete_repan(repan)
    if not repan_complete:
        return None

    base = _parse_base(repan)
    four = _parse_four(repan)
    bazi = _build_bazi(four)
    day_master, day_branch = _day_parts(four.get("D", ""))
    flags = _quality_flags(base, four, bazi, repan)
    return CompletedRepanRecord(
        raw_id=raw_id,
        gender=gender,
        qian_kun=base.get("Sex", "乾" if gender == "男" else "坤"),
        priority=_int_value(meta.get("优先级", "0")),
        original_index=_int_value(meta.get("原索引序号", "0")),
        status=meta.get("状态", ""),
        event_count=_int_value(meta.get("事件数", "0")),
        quality_grade=meta.get("质量等级", ""),
        score=_int_value(meta.get("评分", "0")),
        index_path=_rel(path),
        index_position=index_position,
        solar_digits=_solar_digits_from_chunk(chunk),
        base=base,
        four=four,
        bazi=bazi,
        day_master=day_master,
        day_branch=day_branch,
        void=base.get("Void", ""),
        start=base.get("Start", ""),
        dy_count=len(DY_HEADER_RE.findall(repan)),
        liunian_count=len(LIU_YEAR_RE.findall(repan)),
        repan_complete=repan_complete,
        quality_flags=flags,
    )


def _parse_base(repan: str) -> dict[str, str]:
    base_text = _section(repan, "$BASE", "$FOUR")
    return {match.group("key").strip(): match.group("value").strip() for match in BASE_LINE_RE.finditer(base_text)}


def _parse_four(repan: str) -> dict[str, str]:
    four_text = _section(repan, "$FOUR", "$DY_LOOP")
    return {match.group("pillar"): match.group("body").strip() for match in FOUR_LINE_RE.finditer(four_text)}


def _section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        return ""
    start += len(start_marker)
    end = text.find(end_marker, start)
    return text[start:end if end >= 0 else len(text)]


def _build_bazi(four: dict[str, str]) -> str:
    pillars: list[str] = []
    for key in ("Y", "M", "D", "H"):
        parts = [part.strip() for part in four.get(key, "").split(",")]
        if len(parts) >= 3:
            pillars.append(parts[1] + parts[2])
    return "".join(pillars)


def _day_parts(day_line: str) -> tuple[str, str]:
    parts = [part.strip() for part in day_line.split(",")]
    if len(parts) >= 3:
        return parts[1], parts[2]
    return "", ""


def _quality_flags(base: dict[str, str], four: dict[str, str], bazi: str, repan: str) -> list[str]:
    flags: list[str] = []
    if not base.get("Solar"):
        flags.append("missing_solar")
    if not base.get("Sex"):
        flags.append("missing_qian_kun")
    if not base.get("Start"):
        flags.append("missing_dayun_start")
    if len(four) != 4:
        flags.append("missing_four_pillars")
    if len(bazi) != 8:
        flags.append("invalid_bazi_length")
    elif not VALID_BAZI_RE.match(bazi):
        flags.append("invalid_ganzhi_chars")
    if len(DY_HEADER_RE.findall(repan)) < 5:
        flags.append("short_dayun_loop")
    if len(LIU_YEAR_RE.findall(repan)) < 40:
        flags.append("short_liunian_loop")
    return flags


def _is_complete_repan(repan: str) -> bool:
    return bool(repan and repan != "？" and all(marker in repan for marker in REQUIRED_REPAN_MARKERS))


def _solar_digits_from_chunk(chunk: str) -> str:
    lines = chunk.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("太阳时:"):
            for value in lines[idx + 1 : idx + 5]:
                digits = "".join(ch for ch in value if ch.isdigit())
                if len(digits) >= 8:
                    return digits[:12]
    return ""


def _build_summary(records: list[CompletedRepanRecord], *, dry_run: bool) -> dict[str, Any]:
    by_gender = _count_by(records, lambda record: record.gender)
    by_quality = _count_by(records, lambda record: record.quality_grade or "unknown")
    flag_counts: dict[str, int] = {}
    for record in records:
        for flag in record.quality_flags:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
    return {
        "schema_version": "wenzhen-repan-completed/v0.1",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "dry_run": dry_run,
        "source_indexes": [_rel(MALE_INDEX), _rel(FEMALE_INDEX)],
        "record_count": len(records),
        "top30_count": min(30, len(records)),
        "gender_distribution": by_gender,
        "quality_distribution": by_quality,
        "quality_flag_distribution": dict(sorted(flag_counts.items())),
        "selection_policy": "Top 30 sorted by event_count desc, score desc, quality grade, original index.",
        "outputs": {
            "jsonl": _rel(DEFAULT_JSONL),
            "summary": _rel(DEFAULT_SUMMARY),
            "top30": _rel(DEFAULT_TOP30),
        },
    }


def _render_top30(records: list[CompletedRepanRecord], summary: dict[str, Any]) -> str:
    lines = [
        "# 问真已补排盘 Top 30 · 正式 case 候选",
        "",
        f"> 生成时间：{summary['generated_at']}",
        "> 用途：人工复核后分批转入正式 `cases/C-.../`，用于多流派八字分析系统回测与校准。",
        "",
        "## 统计",
        "",
        f"- 已补样本总数：{summary['record_count']}",
        f"- Top 30 候选数：{summary['top30_count']}",
        f"- 性别分布：{summary['gender_distribution']}",
        f"- 质量分布：{summary['quality_distribution']}",
        "",
        "## 候选清单",
        "",
        "| 排名 | raw_id | 乾坤 | 四柱 | 事件数 | 质量 | 评分 | 原索引 | 来源 | 质量标记 |",
        "|---:|---|---|---|---:|---|---:|---:|---|---|",
    ]
    for rank, record in enumerate(records, start=1):
        flags = "、".join(record.quality_flags) if record.quality_flags else "-"
        lines.append(
            "| "
            f"{rank} | {record.raw_id} | {record.qian_kun} | {record.bazi or '-'} | "
            f"{record.event_count} | {record.quality_grade or '-'} | {record.score} | "
            f"{record.original_index} | {record.index_path} | {flags} |"
        )
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "1. 人工复核 Top 30 的原始反馈文本与排盘 OCR 异常。",
            "2. 按 `templates/input-from-wenzhen.md` 转正式 case。",
            "3. 跑 preflight、pipeline、statement_index 与反馈摄入。",
            "",
        ]
    )
    return "\n".join(lines)


def _count_by(records: list[CompletedRepanRecord], key_fn) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(key_fn(record))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _quality_rank(value: str) -> int:
    return {"A": 0, "B": 1, "C": 2, "D": 3}.get(value.strip().upper(), 9)


def _int_value(value: str) -> int:
    match = re.search(r"\d+", value or "")
    return int(match.group(0)) if match else 0


def _rel(path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description="抽取已补问真排盘样本并生成 Top 30 候选")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写输出文件")
    args = parser.parse_args()
    summary = write_outputs(dry_run=args.dry_run)
    print("extract_wenzhen_repan_completed")
    print(f"  dry_run: {args.dry_run}")
    print(f"  records: {summary['record_count']}")
    print(f"  gender_distribution: {summary['gender_distribution']}")
    print(f"  quality_distribution: {summary['quality_distribution']}")
    if summary["quality_flag_distribution"]:
        print(f"  quality_flags: {summary['quality_flag_distribution']}")
    print(f"  top30: {summary['outputs']['top30']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
