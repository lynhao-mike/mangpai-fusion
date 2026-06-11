"""Generate content reports for repaired Wenzhen invalid-ganzhi cases.

This tool processes only the 7 repaired cases recorded in
wenzhen_fixed_cases_preflight-summary.json. It runs:
- tools.preflight.parse
- engine.pipeline.run_pipeline
- tools.render_report.render_from_output

It intentionally does not call feedback_ingest or batch_review.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import traceback
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SUMMARY_JSON = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_fixed_cases_preflight-summary.json"
OUTPUT_JSON = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_fixed_cases_report-generation-summary.json"
OUTPUT_MD = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_fixed_cases_report-generation-summary.md"
REPORTS_DIR = REPO_ROOT / "reports"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate content reports for repaired Wenzhen cases.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and planned targets without writing reports.")
    args = parser.parse_args(argv)

    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    rows = [_process_case(row, dry_run=args.dry_run) for row in summary.get("results", [])]
    payload = {
        "dry_run": args.dry_run,
        "total": len(rows),
        "generated": sum(1 for row in rows if row["status"] == "generated"),
        "planned": sum(1 for row in rows if row["status"] == "planned"),
        "skipped_existing": sum(1 for row in rows if row["status"] == "skipped_existing"),
        "errors": [row for row in rows if row["status"] == "error"],
        "results": rows,
        "policy": "只生成统一 content-report；不运行 feedback_ingest / batch_review。",
    }
    if not args.dry_run:
        OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        OUTPUT_MD.write_text(_render_markdown(payload), encoding="utf-8")
    _safe_print_json(payload)
    return 0 if not payload["errors"] else 1


def _process_case(row: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    case_id = row["case_id"]
    input_path = REPO_ROOT / row["input"]
    report_path = REPORTS_DIR / f"{case_id}-content-report.md"
    base = {
        "raw_id": row.get("raw_id", ""),
        "case_id": case_id,
        "input": _rel(input_path),
        "report": _rel(report_path),
    }
    if report_path.exists():
        return {**base, "status": "skipped_existing"}
    if dry_run:
        return {**base, "status": "planned"}

    try:
        from tools.preflight import parse as preflight_parse
        from engine.pipeline import run_pipeline
        from engine.predicates.types import adapt_parsed
        from tools.render_report import render_from_output

        parsed = adapt_parsed(preflight_parse(input_path))
        output = run_pipeline(parsed)
        report_md = render_from_output(output, variant="standard", lint_before=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_md, encoding="utf-8")
        return {**base, "status": "generated"}
    except Exception as exc:  # noqa: BLE001
        return {
            **base,
            "status": "error",
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 问真修复 case 统一报告生成结果",
        "",
        "## 汇总",
        "",
        f"- 总数：{payload['total']}",
        f"- 已生成：{payload['generated']}",
        f"- 已存在跳过：{payload['skipped_existing']}",
        f"- 错误：{len(payload['errors'])}",
        f"- 策略：{payload['policy']}",
        "",
        "## 明细",
        "",
        "| raw_id | case_id | report | 状态 |",
        "|---|---|---|---|",
    ]
    for row in payload["results"]:
        lines.append(f"| {row['raw_id']} | {row['case_id']} | {row['report']} | {row['status']} |")
    if payload["errors"]:
        lines.extend(["", "## 错误", ""])
        for row in payload["errors"]:
            lines.append(f"- {row['case_id']}：{row.get('error', '')}")
    lines.append("")
    return "\n".join(lines)


def _safe_print_json(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace") + b"\n")


def _rel(path: pathlib.Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
