"""Preflight Wenzhen staging promotion candidates before formal case creation.

This tool validates the staging manifest for naming conflicts, source draft
availability, required fields, and evidence readiness. It writes reports only;
it does not create formal cases.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "cases"
PARSED_DIR = CASES_DIR / "raw_feedback" / "parsed"
DEFAULT_STAGING_JSONL = PARSED_DIR / "wenzhen_repan_top30_staging_manifest.jsonl"
DEFAULT_REPORT_MD = PARSED_DIR / "wenzhen_repan_top30_promotion_preflight.md"
DEFAULT_SUMMARY_JSON = PARSED_DIR / "wenzhen_repan_top30_promotion_preflight-summary.json"
VALID_CASE_ID_RE = re.compile(r"^C-2026-RF\d{6}-[乾坤]-[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥][甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥][甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥][甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]$")
REQUIRED_FIELDS = (
    "raw_id",
    "suggested_case_id",
    "draft_path",
    "bazi",
    "qian_kun",
    "pillars",
    "birth",
    "base",
    "start",
    "event_count",
    "known_fact_count",
)


def run_preflight(*, dry_run: bool = False) -> dict[str, Any]:
    records = _load_staging(DEFAULT_STAGING_JSONL)
    checks = [_check_record(record) for record in records]
    summary = _build_summary(checks, dry_run=dry_run)
    if not dry_run:
        PARSED_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULT_REPORT_MD.write_text(_render_report(checks, summary), encoding="utf-8")
        DEFAULT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _load_staging(path: pathlib.Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _check_record(record: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = [field for field in REQUIRED_FIELDS if field not in record or record.get(field) in (None, "", [])]
    if missing:
        errors.append("missing_required_fields:" + ",".join(missing))

    suggested_case_id = str(record.get("suggested_case_id") or "")
    if not VALID_CASE_ID_RE.match(suggested_case_id):
        errors.append("invalid_suggested_case_id")

    target_dir = CASES_DIR / suggested_case_id
    if target_dir.exists():
        errors.append("formal_case_dir_conflict")

    draft_path = REPO_ROOT / str(record.get("draft_path") or "")
    if not draft_path.exists():
        errors.append("missing_source_draft")

    if record.get("promotion_blocking_flags"):
        errors.append("has_promotion_blocking_flags")

    pillars = record.get("pillars") if isinstance(record.get("pillars"), dict) else {}
    if set(pillars) != {"Y", "M", "D", "H"}:
        errors.append("incomplete_pillars")

    if int(record.get("event_count") or 0) != int(record.get("known_fact_count") or 0):
        errors.append("event_count_mismatch")

    if int(record.get("event_count") or 0) < 10:
        warnings.append("low_event_count")
    if record.get("quality_grade") not in {"A", "B"}:
        warnings.append("low_quality_grade")
    if not record.get("human_review_required"):
        warnings.append("human_review_flag_missing")

    return {
        "raw_id": record.get("raw_id", ""),
        "suggested_case_id": suggested_case_id,
        "draft_path": record.get("draft_path", ""),
        "target_dir": _rel(target_dir),
        "bazi": record.get("bazi", ""),
        "qian_kun": record.get("qian_kun", ""),
        "event_count": record.get("event_count", 0),
        "known_fact_count": record.get("known_fact_count", 0),
        "errors": errors,
        "warnings": warnings,
        "ready_for_manual_promotion": not errors,
    }


def _build_summary(checks: list[dict[str, Any]], *, dry_run: bool) -> dict[str, Any]:
    error_counts: dict[str, int] = {}
    warning_counts: dict[str, int] = {}
    ready = [check for check in checks if check["ready_for_manual_promotion"]]
    blocked = [check for check in checks if not check["ready_for_manual_promotion"]]
    for check in checks:
        for error in check["errors"]:
            key = error.split(":", 1)[0]
            error_counts[key] = error_counts.get(key, 0) + 1
        for warning in check["warnings"]:
            warning_counts[warning] = warning_counts.get(warning, 0) + 1
    return {
        "schema_version": "wenzhen-promotion-preflight/v0.1",
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "dry_run": dry_run,
        "source_staging_jsonl": _rel(DEFAULT_STAGING_JSONL),
        "report_markdown": _rel(DEFAULT_REPORT_MD),
        "summary_json": _rel(DEFAULT_SUMMARY_JSON),
        "candidate_count": len(checks),
        "ready_count": len(ready),
        "blocked_count": len(blocked),
        "ready_raw_ids": [check["raw_id"] for check in ready],
        "blocked_raw_ids": [check["raw_id"] for check in blocked],
        "error_distribution": dict(sorted(error_counts.items())),
        "warning_distribution": dict(sorted(warning_counts.items())),
        "policy": "Preflight report only; manual approval and tools.preflight are still required before formal case creation.",
    }


def _render_report(checks: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# 问真 Top 30 staging · 正式转案预检报告",
        "",
        f"> 生成时间：{summary['generated_at']}",
        "> 用途：检查 staging 候选在创建正式 case 前是否存在命名冲突、证据缺口或字段缺失。",
        "> 约束：本报告不创建正式 case；人工批准后仍需运行 `tools.preflight`。",
        "",
        "## 汇总",
        "",
        f"- 候选数：{summary['candidate_count']}",
        f"- 可进入人工转案：{summary['ready_count']}",
        f"- 阻断数：{summary['blocked_count']}",
        f"- 错误分布：{summary['error_distribution']}",
        f"- 警告分布：{summary['warning_distribution']}",
        "",
        "## 预检表",
        "",
        "| raw_id | 建议 case_id | 四柱 | 事件数 | 目标目录 | 状态 | 错误 | 警告 |",
        "|---|---|---|---:|---|---|---|---|",
    ]
    for check in checks:
        status = "READY" if check["ready_for_manual_promotion"] else "BLOCKED"
        errors = "、".join(check["errors"]) if check["errors"] else "-"
        warnings = "、".join(check["warnings"]) if check["warnings"] else "-"
        lines.append(
            f"| {check['raw_id']} | {check['suggested_case_id']} | {check['bazi']} | {check['event_count']} | "
            f"{check['target_dir']} | {status} | {errors} | {warnings} |"
        )
    lines.extend(["", "## 转案前硬性要求", ""])
    lines.extend(
        [
            "- [ ] 人工确认该候选从 staging 转正式 case。",
            "- [ ] 创建正式目录后补齐 `input.md`、`analysis.md`、`feedback.md`、`statement_index.json`。",
            "- [ ] 正式 `input.md` 运行 `python -m tools.preflight <case>/input.md`。",
            "- [ ] case 与报告/反馈文件互写关联路径。",
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
    parser.add_argument("--dry-run", action="store_true", help="Only print summary; do not write artifacts.")
    args = parser.parse_args(argv)
    summary = run_preflight(dry_run=args.dry_run)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
