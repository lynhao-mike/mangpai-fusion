"""Build a dry-run promotion plan for the first Wenzhen staging candidates.

This tool prepares a human approval package for formal case creation. It does
not create case directories or write formal case files.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PARSED_DIR = REPO_ROOT / "cases" / "raw_feedback" / "parsed"
DEFAULT_STAGING_JSONL = PARSED_DIR / "wenzhen_repan_top30_staging_manifest.jsonl"
DEFAULT_PLAN_MD = PARSED_DIR / "wenzhen_repan_first5_promotion_plan.md"
DEFAULT_PLAN_JSON = PARSED_DIR / "wenzhen_repan_first5_promotion_plan.json"
BATCH_SIZE = 5
REQUIRED_CASE_FILES = ("input.md", "analysis.md", "feedback.md", "statement_index.json")


def build_plan(*, batch_size: int = BATCH_SIZE, dry_run: bool = False) -> dict[str, Any]:
    staging = _load_staging(DEFAULT_STAGING_JSONL)
    selected = staging[:batch_size]
    plan = [_plan_record(record) for record in selected]
    summary = _build_summary(plan, dry_run=dry_run)
    if not dry_run:
        PARSED_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULT_PLAN_JSON.write_text(json.dumps({"summary": summary, "plans": plan}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        DEFAULT_PLAN_MD.write_text(_render_plan(plan, summary), encoding="utf-8")
    return summary


def _load_staging(path: pathlib.Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _plan_record(record: dict[str, Any]) -> dict[str, Any]:
    case_id = record["suggested_case_id"]
    case_dir = pathlib.Path("cases") / case_id
    files = {name: (case_dir / name).as_posix() for name in REQUIRED_CASE_FILES}
    return {
        "rank": record["rank"],
        "raw_id": record["raw_id"],
        "case_id": case_id,
        "case_dir": case_dir.as_posix(),
        "qian_kun": record["qian_kun"],
        "bazi": record["bazi"],
        "draft_path": record["draft_path"],
        "source_index_path": record["source_index_path"],
        "event_count": record["event_count"],
        "known_fact_count": record["known_fact_count"],
        "target_files": files,
        "planned_actions": [
            f"创建目录 {case_dir.as_posix()}",
            f"生成 {files['input.md']}：从 staging 排盘与草稿 birth/known_facts 合并",
            f"生成 {files['analysis.md']}：记录来源、转案说明与待分析占位",
            f"生成 {files['feedback.md']}：迁移原 known_facts 并保留 raw_id 追踪",
            f"生成 {files['statement_index.json']}：初始化 statement 追踪骨架",
            f"运行 python -m tools.preflight {files['input.md']}",
        ],
        "manual_approval_required": True,
    }


def _build_summary(plan: list[dict[str, Any]], *, dry_run: bool) -> dict[str, Any]:
    return {
        "schema_version": "wenzhen-first5-promotion-plan/v0.1",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "dry_run": dry_run,
        "source_staging_jsonl": _rel(DEFAULT_STAGING_JSONL),
        "plan_markdown": _rel(DEFAULT_PLAN_MD),
        "plan_json": _rel(DEFAULT_PLAN_JSON),
        "batch_size": len(plan),
        "raw_ids": [item["raw_id"] for item in plan],
        "case_ids": [item["case_id"] for item in plan],
        "required_files_per_case": list(REQUIRED_CASE_FILES),
        "policy": "Dry-run promotion plan only; no formal case directories are created.",
    }


def _render_plan(plan: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# 问真 staging · 首批 5 个正式转案 dry-run 方案",
        "",
        f"> 生成时间：{summary['generated_at']}",
        "> 用途：供人工批准首批正式 case 创建；本方案不创建任何正式目录。",
        "",
        "## 汇总",
        "",
        f"- 首批数量：{summary['batch_size']}",
        f"- 来源 staging：`{summary['source_staging_jsonl']}`",
        f"- 必备文件：{', '.join(summary['required_files_per_case'])}",
        "",
        "## 首批清单",
        "",
        "| 顺位 | raw_id | 建议 case_id | 乾坤 | 四柱 | 事件数 | 源草稿 |",
        "|---:|---|---|---|---|---:|---|",
    ]
    for item in plan:
        lines.append(
            f"| {item['rank']} | {item['raw_id']} | {item['case_id']} | {item['qian_kun']} | {item['bazi']} | {item['event_count']} | {item['draft_path']} |"
        )
    lines.extend(["", "## 逐案操作预案", ""])
    for item in plan:
        lines.extend(
            [
                f"### {item['rank']}. {item['raw_id']} → {item['case_id']}",
                "",
                f"- 目标目录：`{item['case_dir']}`",
                f"- 来源草稿：`{item['draft_path']}`",
                f"- 来源索引：`{item['source_index_path']}`",
                f"- 事件数：{item['event_count']} / 草稿事实数：{item['known_fact_count']}",
                "- 目标文件：",
            ]
        )
        for file_path in item["target_files"].values():
            lines.append(f"  - `{file_path}`")
        lines.extend(["- 操作步骤："])
        for action in item["planned_actions"]:
            lines.append(f"  - [ ] {action}")
        lines.extend(["", ""])
    lines.extend(
        [
            "## 人工批准清单",
            "",
            "- [ ] 确认首批 5 个 raw_id 均允许转正式 case。",
            "- [ ] 确认目标目录命名策略 `C-2026-RFxxxxxx-乾/坤-四柱`。",
            "- [ ] 确认转案时保留 raw_id、源草稿、源索引、复核包路径。",
            "- [ ] 批准后再执行真实创建脚本或手工创建。",
            "",
        ]
    )
    return "\n".join(lines)


def _rel(path: pathlib.Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Number of staging candidates to include.")
    parser.add_argument("--dry-run", action="store_true", help="Only print summary; do not write plan artifacts.")
    args = parser.parse_args(argv)
    summary = build_plan(batch_size=args.batch_size, dry_run=args.dry_run)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
