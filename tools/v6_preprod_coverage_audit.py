"""tools.v6_preprod_coverage_audit · v6 preprod 批量覆盖审计。

只读扫描 v6 preprod 报告与配套 artifact，判断是否达到统一报告切默认入口的最低证据门槛。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"
META_DIR = REPO_ROOT / "META"

REQUIRED_SECTIONS = [
    "# 📌 归档信息与命盘结构",
    "## 五派裁决与共识融合总论",
    "## 命局做功与人生主线",
    "## 十五层判断摘要",
    "## 性格与行为模式",
    "## 主要事项结构",
    "### 学业结构",
    "### 事业结构",
    "### 财富结构",
    "### 婚姻结构",
    "### 健康结构",
    "## 受限概率系统",
    "## 主要事件预测账本（prediction-first）",
    "## 待反馈关键流年与事件",
    "### 待反馈（已发生验证项）",
    "### 待反馈（预测验证项）",
    "## 系统级约束",
]

REQUIRED_DOMAIN_MARKERS = {
    "学业": ["学历层次", "学校层级", "学业表现", "学科倾向"],
    "事业": ["职业层级", "单位层级", "权力层级", "成就等级"],
    "财富": ["收入层级", "资产层级", "财富状态"],
    "婚姻": ["感情状态", "婚姻质量", "配偶学历", "配偶事业", "配偶财富", "配偶外貌", "配偶气质"],
    "健康": ["体质", "疾病风险", "健康状态", "寿元倾向"],
}

REQUIRED_ARTIFACTS = {
    "v5_json": ".v5.json",
    "run_json": ".run.json",
    "decision_run_json": ".decision-run.json",
    "feedback_attachment": ".feedback-attachment.json",
}


def _case_id_from_report(path: Path) -> str:
    return path.name.removesuffix("-v6-preprod-content-report.md")


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _audit_one(report_path: Path) -> dict[str, Any]:
    text = report_path.read_text(encoding="utf-8")
    missing: list[str] = []
    warnings: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            missing.append(f"section:{section.split(' ', 1)[-1].lstrip('#').strip()}")

    for domain, markers in REQUIRED_DOMAIN_MARKERS.items():
        for marker in markers:
            if marker not in text:
                missing.append(f"domain_marker:{domain}:{marker}")

    layer_rows = 0
    for line in text.splitlines():
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if parts and parts[0].isdigit():
            layer = int(parts[0])
            if 1 <= layer <= 15:
                layer_rows += 1
    if layer_rows < 15:
        missing.append("fifteen_layers:rows<15")

    if "[打开报告文件](" not in text or "[打开案例目录](" not in text or "[打开反馈文件](" not in text:
        missing.append("archive_links:clickable_paths")

    prediction_domains = {domain for domain in REQUIRED_DOMAIN_MARKERS if f"| {domain} |" in text}
    if len(prediction_domains) < 5:
        missing.append("prediction_ledger:domain_coverage<5")

    artifact_status: dict[str, bool] = {}
    artifact_schema: dict[str, str] = {}
    for key, suffix in REQUIRED_ARTIFACTS.items():
        artifact = report_path.with_suffix(suffix)
        exists = artifact.exists()
        artifact_status[key] = exists
        if not exists:
            missing.append(f"artifact:{key}")
            continue
        payload = _read_json(artifact)
        if payload is None:
            missing.append(f"artifact_json:{key}")
            continue
        artifact_schema[key] = str(
            payload.get("schema_version")
            or payload.get("snapshot_schema_version")
            or payload.get("attachment_schema_version")
            or ""
        )

    passed = not missing
    return {
        "case_id": _case_id_from_report(report_path),
        "report_path": report_path.as_posix(),
        "passed": passed,
        "missing": missing,
        "warnings": warnings,
        "artifact_status": artifact_status,
        "artifact_schema": artifact_schema,
        "layer_rows": layer_rows,
        "prediction_domain_count": len(prediction_domains),
    }


def audit_v6_preprod_reports(report_paths: list[str | Path]) -> dict[str, Any]:
    paths = [Path(path) for path in report_paths]
    cases = [_audit_one(path) for path in paths]
    pass_count = sum(1 for item in cases if item["passed"])
    return {
        "case_count": len(cases),
        "pass_count": pass_count,
        "fail_count": len(cases) - pass_count,
        "cases": cases,
    }


def _default_reports() -> list[Path]:
    return sorted(REPORTS_DIR.glob("*-v6-preprod-content-report.md"))


def _markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# v6 preprod coverage audit",
        "",
        f"- case_count: {result['case_count']}",
        f"- pass_count: {result['pass_count']}",
        f"- fail_count: {result['fail_count']}",
        "",
        "| case_id | passed | missing | prediction_domains | layer_rows |",
        "|---|---:|---|---:|---:|",
    ]
    for item in result["cases"]:
        missing = "; ".join(item["missing"]) if item["missing"] else ""
        lines.append(
            f"| {item['case_id']} | {str(item['passed']).lower()} | {missing} | {item['prediction_domain_count']} | {item['layer_rows']} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="审计 v6 preprod 报告是否覆盖统一报告最低要求")
    parser.add_argument("reports", nargs="*", help="报告路径；不传则扫描 reports/*-v6-preprod-content-report.md")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--write-md", default="", help="写入 Markdown 审计报告路径")
    args = parser.parse_args(argv)

    paths = [Path(item) for item in args.reports] if args.reports else _default_reports()
    result = audit_v6_preprod_reports(paths)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_markdown_report(result), end="")
    if args.write_md:
        output = Path(args.write_md)
        if not output.is_absolute():
            output = REPO_ROOT / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(_markdown_report(result), encoding="utf-8")
    return 0 if result["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
