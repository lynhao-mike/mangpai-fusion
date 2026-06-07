"""Build a Top 30 human review package for completed Wenzhen repan samples.

This tool joins structured completed repan records with their raw feedback draft
`input.md` files. It only writes review artifacts and never mutates drafts or
creates formal cases.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DRAFTS_DIR = REPO_ROOT / "cases" / "raw_feedback" / "case_drafts"
PARSED_DIR = REPO_ROOT / "cases" / "raw_feedback" / "parsed"
DEFAULT_JSONL = PARSED_DIR / "wenzhen_repan_completed.jsonl"
DEFAULT_REVIEW_MD = PARSED_DIR / "wenzhen_repan_top30_review.md"
DEFAULT_SUMMARY = PARSED_DIR / "wenzhen_repan_top30_review-summary.json"
TOP_N = 30

YAML_BLOCK_RE = re.compile(r"```yaml\n(?P<body>.*?)\n```", re.S)
RAW_EXCERPT_RE = re.compile(r"## 原始反馈摘录\s*\n\s*```text\n(?P<body>.*?)\n```", re.S)
KNOWN_FACT_RE = re.compile(
    r"^\s*-\s+year:\s*(?P<year>\d{4})\s*\n"
    r"\s+type:\s*(?P<type>[^\n]+)\s*\n"
    r"\s+desc:\s*\"(?P<desc>.*?)\"\s*$",
    re.M | re.S,
)
FIELD_RE = re.compile(r"^\s{2}(?P<key>[^:\n]+):\s*(?P<value>.*)$", re.M)


def build_review_pack(*, dry_run: bool = False, top_n: int = TOP_N) -> dict[str, Any]:
    records = _load_records(DEFAULT_JSONL)[:top_n]
    cases = [_build_case(rank, record) for rank, record in enumerate(records, start=1)]
    summary = _build_summary(cases, dry_run=dry_run)
    if not dry_run:
        PARSED_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULT_REVIEW_MD.write_text(_render_review(cases, summary), encoding="utf-8")
        DEFAULT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _load_records(path: pathlib.Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _build_case(rank: int, record: dict[str, Any]) -> dict[str, Any]:
    raw_id = str(record["raw_id"])
    draft_path = DRAFTS_DIR / raw_id / "input.md"
    draft_text = draft_path.read_text(encoding="utf-8") if draft_path.exists() else ""
    yaml_text = _extract_yaml(draft_text)
    facts = _extract_known_facts(yaml_text)
    raw_excerpt = _extract_raw_excerpt(draft_text)
    return {
        "rank": rank,
        "raw_id": raw_id,
        "draft_path": _rel(draft_path),
        "draft_exists": draft_path.exists(),
        "record": record,
        "birth": _extract_birth_fields(yaml_text),
        "known_facts": facts,
        "known_fact_count": len(facts),
        "raw_excerpt": raw_excerpt,
        "raw_excerpt_chars": len(raw_excerpt),
        "review_flags": _review_flags(record, draft_path.exists(), len(facts), raw_excerpt),
    }


def _extract_yaml(text: str) -> str:
    match = YAML_BLOCK_RE.search(text)
    return match.group("body").strip() if match else ""


def _extract_raw_excerpt(text: str) -> str:
    match = RAW_EXCERPT_RE.search(text)
    return _compact_text(match.group("body")) if match else ""


def _extract_known_facts(yaml_text: str) -> list[dict[str, str]]:
    facts: list[dict[str, str]] = []
    for match in KNOWN_FACT_RE.finditer(yaml_text):
        facts.append(
            {
                "year": match.group("year"),
                "type": match.group("type").strip(),
                "desc": _compact_text(match.group("desc")),
            }
        )
    return facts


def _extract_birth_fields(yaml_text: str) -> dict[str, str]:
    birth = _section(yaml_text, "birth:", "四柱:")
    fields: dict[str, str] = {}
    for match in FIELD_RE.finditer(birth):
        fields[match.group("key").strip()] = match.group("value").strip().strip('"')
    return fields


def _section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        return ""
    start += len(start_marker)
    end = text.find(end_marker, start)
    return text[start : end if end >= 0 else len(text)]


def _review_flags(record: dict[str, Any], draft_exists: bool, fact_count: int, raw_excerpt: str) -> list[str]:
    flags = list(record.get("quality_flags") or [])
    if not draft_exists:
        flags.append("missing_draft_input")
    if fact_count != int(record.get("event_count") or 0):
        flags.append("event_count_mismatch")
    if not raw_excerpt:
        flags.append("missing_raw_excerpt")
    if str(record.get("bazi") or "").find("王") >= 0:
        flags.append("ocr_wang_for_ren")
    if "申西" in json.dumps(record, ensure_ascii=False):
        flags.append("ocr_xi_for_you")
    return sorted(set(flags))


def _build_summary(cases: list[dict[str, Any]], *, dry_run: bool) -> dict[str, Any]:
    flag_counts: dict[str, int] = {}
    missing_drafts: list[str] = []
    mismatched_events: list[str] = []
    for case in cases:
        if not case["draft_exists"]:
            missing_drafts.append(case["raw_id"])
        if "event_count_mismatch" in case["review_flags"]:
            mismatched_events.append(case["raw_id"])
        for flag in case["review_flags"]:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
    return {
        "schema_version": "wenzhen-top30-review/v0.1",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "dry_run": dry_run,
        "source_jsonl": _rel(DEFAULT_JSONL),
        "review_markdown": _rel(DEFAULT_REVIEW_MD),
        "summary_json": _rel(DEFAULT_SUMMARY),
        "case_count": len(cases),
        "missing_draft_count": len(missing_drafts),
        "missing_drafts": missing_drafts,
        "event_count_mismatch_count": len(mismatched_events),
        "event_count_mismatches": mismatched_events,
        "review_flag_distribution": dict(sorted(flag_counts.items())),
        "policy": "Human review package only; do not promote to formal cases until OCR and raw feedback are reviewed.",
    }


def _render_review(cases: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# 问真已补排盘 Top 30 · 人工复核包",
        "",
        f"> 生成时间：{summary['generated_at']}",
        "> 目的：合并已补排盘、原始反馈与 OCR 风险，供人工决定是否转正式 case。",
        "> 约束：本文件不是正式案例库；不得直接作为 pipeline 输入。",
        "",
        "## 汇总",
        "",
        f"- 复核样本数：{summary['case_count']}",
        f"- 缺失草稿数：{summary['missing_draft_count']}",
        f"- 事件数不一致：{summary['event_count_mismatch_count']}",
        f"- 风险标记分布：{summary['review_flag_distribution']}",
        "",
        "## 复核总表",
        "",
        "| 排名 | raw_id | 乾坤 | 四柱 | 事件数 | 草稿事件数 | 评分 | 风险标记 | 草稿 |",
        "|---:|---|---|---|---:|---:|---:|---|---|",
    ]
    for case in cases:
        record = case["record"]
        flags = "、".join(case["review_flags"]) if case["review_flags"] else "-"
        lines.append(
            f"| {case['rank']} | {case['raw_id']} | {record.get('qian_kun', '-')} | {record.get('bazi', '-')} | "
            f"{record.get('event_count', 0)} | {case['known_fact_count']} | {record.get('score', 0)} | {flags} | {case['draft_path']} |"
        )
    lines.extend(["", "## 逐案复核", ""])
    for case in cases:
        lines.extend(_render_case(case))
    return "\n".join(lines).rstrip() + "\n"


def _render_case(case: dict[str, Any]) -> list[str]:
    record = case["record"]
    birth = case["birth"]
    flags = "、".join(case["review_flags"]) if case["review_flags"] else "-"
    lines = [
        f"### {case['rank']}. {case['raw_id']} · {record.get('qian_kun', '-')} · {record.get('bazi', '-')}",
        "",
        "#### 排盘摘要",
        "",
        f"- 来源草稿：`{case['draft_path']}`",
        f"- 原索引：{record.get('original_index', '-')}；来源索引：`{record.get('index_path', '-')}`",
        f"- 公历/太阳时：{record.get('base', {}).get('Solar', '-')} / {record.get('base', {}).get('Sun', '-')}",
        f"- 草稿公历/太阳时：{birth.get('公历', '-')} / {birth.get('太阳时', '-')}",
        f"- 日主/日支/空亡：{record.get('day_master', '-')} / {record.get('day_branch', '-')} / {record.get('void', '-')}",
        f"- 起运：{record.get('start', '-')}",
        f"- 事件数：索引 {record.get('event_count', 0)} / 草稿 {case['known_fact_count']}；评分：{record.get('score', 0)}；质量：{record.get('quality_grade', '-')}",
        f"- 风险标记：{flags}",
        "",
        "#### 四柱明细",
        "",
    ]
    for pillar, label in (("Y", "年"), ("M", "月"), ("D", "日"), ("H", "时")):
        lines.append(f"- {label}柱：{record.get('four', {}).get(pillar, '-')}")
    lines.extend(["", "#### 事件年表", ""])
    for fact in case["known_facts"]:
        lines.append(f"- {fact['year']} · {fact['type']}：{fact['desc']}")
    lines.extend(
        [
            "",
            "#### 原始反馈摘录",
            "",
            "```text",
            case["raw_excerpt"] or "（缺失）",
            "```",
            "",
            "#### 人工复核清单",
            "",
            "- [ ] OCR 干支/空亡/藏干已核正。",
            "- [ ] 出生信息与问真排盘一致。",
            "- [ ] 事件年表可追溯、可用于 statement_index。",
            "- [ ] 可转正式 `cases/C-.../`。",
            "",
        ]
    )
    return lines


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _rel(path: pathlib.Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Only print summary; do not write artifacts.")
    parser.add_argument("--top-n", type=int, default=TOP_N, help="Number of sorted completed records to include.")
    args = parser.parse_args(argv)
    summary = build_review_pack(dry_run=args.dry_run, top_n=args.top_n)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
