"""Build a machine-readable staging manifest for Wenzhen Top 30 promotion candidates.

The manifest records promotion-ready candidates after the review gate, but does
not create formal cases. Human review is still required before promotion.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from typing import Any

from tools.build_wenzhen_top30_review_gate import BLOCKING_FLAGS
from tools.build_wenzhen_top30_review_pack import (
    DEFAULT_JSONL,
    PARSED_DIR,
    TOP_N,
    _build_case,
    _load_records,
    _rel,
)

DEFAULT_STAGING_JSONL = PARSED_DIR / "wenzhen_repan_top30_staging_manifest.jsonl"
DEFAULT_STAGING_SUMMARY = PARSED_DIR / "wenzhen_repan_top30_staging_manifest-summary.json"
DEFAULT_STAGING_INDEX = PARSED_DIR / "wenzhen_repan_top30_staging_manifest.md"


def build_staging_manifest(*, dry_run: bool = False, top_n: int = TOP_N) -> dict[str, Any]:
    cases = [_build_case(rank, record) for rank, record in enumerate(_load_records(DEFAULT_JSONL)[:top_n], start=1)]
    records = [_to_staging_record(case) for case in cases if not _blocking_flags(case)]
    summary = _build_summary(records, cases, dry_run=dry_run)
    if not dry_run:
        PARSED_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULT_STAGING_JSONL.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n",
            encoding="utf-8",
        )
        DEFAULT_STAGING_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        DEFAULT_STAGING_INDEX.write_text(_render_index(records, summary), encoding="utf-8")
    return summary


def _to_staging_record(case: dict[str, Any]) -> dict[str, Any]:
    record = case["record"]
    bazi = str(record.get("bazi") or "")
    qian_kun = str(record.get("qian_kun") or "")
    suggested_case_id = f"C-2026-RF{case['raw_id'].split('-')[-1]}-{qian_kun}-{bazi}"
    return {
        "schema_version": "wenzhen-top30-staging/v0.1",
        "rank": case["rank"],
        "raw_id": case["raw_id"],
        "suggested_case_id": suggested_case_id,
        "status": "staged_pending_human_review",
        "draft_path": case["draft_path"],
        "source_index_path": record.get("index_path", ""),
        "source_index_position": record.get("index_position", 0),
        "original_index": record.get("original_index", 0),
        "qian_kun": qian_kun,
        "gender": record.get("gender", ""),
        "bazi": bazi,
        "pillars": record.get("four", {}),
        "birth": case.get("birth", {}),
        "base": record.get("base", {}),
        "day_master": record.get("day_master", ""),
        "day_branch": record.get("day_branch", ""),
        "void": record.get("void", ""),
        "start": record.get("start", ""),
        "dy_count": record.get("dy_count", 0),
        "liunian_count": record.get("liunian_count", 0),
        "event_count": record.get("event_count", 0),
        "known_fact_count": case.get("known_fact_count", 0),
        "quality_grade": record.get("quality_grade", ""),
        "score": record.get("score", 0),
        "review_flags": case.get("review_flags", []),
        "promotion_blocking_flags": _blocking_flags(case),
        "human_review_required": True,
        "required_manual_checks": [
            "核对出生信息与脱敏粒度",
            "核对问真排盘四柱/藏干/起运",
            "将事件年表映射到 feedback.md 与 statement_index.json",
            "运行 preflight 后再进入正式 case 库",
        ],
    }


def _blocking_flags(case: dict[str, Any]) -> list[str]:
    return [flag for flag in case.get("review_flags", []) if flag in BLOCKING_FLAGS]


def _build_summary(records: list[dict[str, Any]], all_cases: list[dict[str, Any]], *, dry_run: bool) -> dict[str, Any]:
    blocked = [case for case in all_cases if _blocking_flags(case)]
    return {
        "schema_version": "wenzhen-top30-staging-manifest/v0.1",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "dry_run": dry_run,
        "source_jsonl": _rel(DEFAULT_JSONL),
        "staging_jsonl": _rel(DEFAULT_STAGING_JSONL),
        "staging_summary": _rel(DEFAULT_STAGING_SUMMARY),
        "staging_index": _rel(DEFAULT_STAGING_INDEX),
        "top_n": len(all_cases),
        "staged_count": len(records),
        "blocked_count": len(blocked),
        "staged_raw_ids": [record["raw_id"] for record in records],
        "blocked_raw_ids": [case["raw_id"] for case in blocked],
        "policy": "Staging manifest is a transfer queue only; formal cases require human review and preflight.",
    }


def _render_index(records: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# 问真 Top 30 · 转案 staging manifest 索引",
        "",
        f"> 生成时间：{summary['generated_at']}",
        "> 用途：机器可读转案候选队列；不是正式 case。",
        "",
        "## 汇总",
        "",
        f"- Top N：{summary['top_n']}",
        f"- staging 候选：{summary['staged_count']}",
        f"- 阻断未入队：{summary['blocked_count']}",
        f"- JSONL：`{summary['staging_jsonl']}`",
        "",
        "## 候选表",
        "",
        "| 排名 | raw_id | 建议 case_id | 乾坤 | 四柱 | 事件数 | 草稿 | 状态 |",
        "|---:|---|---|---|---|---:|---|---|",
    ]
    for record in records:
        lines.append(
            f"| {record['rank']} | {record['raw_id']} | {record['suggested_case_id']} | {record['qian_kun']} | "
            f"{record['bazi']} | {record['event_count']} | {record['draft_path']} | {record['status']} |"
        )
    lines.extend(
        [
            "",
            "## 使用约束",
            "",
            "- [ ] 人工确认后才允许创建正式 `cases/C-.../` 目录。",
            "- [ ] 正式 `input.md` 必须通过 `python -m tools.preflight <case>/input.md`。",
            "- [ ] `feedback.md` 与 `statement_index.json` 必须保留原始反馈追踪路径。",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Only print summary; do not write artifacts.")
    parser.add_argument("--top-n", type=int, default=TOP_N, help="Number of sorted completed records to include.")
    args = parser.parse_args(argv)
    summary = build_staging_manifest(dry_run=args.dry_run, top_n=args.top_n)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
