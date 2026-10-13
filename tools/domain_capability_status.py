"""六源三领域十八槽位能力覆盖与弃权诊断只读 CLI。

消费一个或多个 ``*.run.json`` 或包含这些文件的目录，输出同源 JSON/Markdown；
``--check`` 只校验并返回退出码，不写规则、权重、路由或快照。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from engine.v5.domain import V5RunSnapshot
from engine.v5.domain_capability_metrics import build_capability_metrics


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="只读扫描六源三领域十八槽位能力与弃权状态")
    parser.add_argument("inputs", nargs="+", help="一个或多个 *.run.json 文件或目录")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--check", action="store_true", help="失败关闭校验全部输入、hash 与十八槽位身份")
    return parser


def _paths(values: Sequence[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        path = Path(value)
        if path.is_dir():
            paths.extend(sorted(path.glob("*.run.json")))
        elif path.name.endswith(".run.json"):
            paths.append(path)
        else:
            raise ValueError(f"input must be a *.run.json file or directory: {path}")
    if not paths:
        raise ValueError("no *.run.json inputs found")
    return paths


def _load(paths: Sequence[Path]) -> list[V5RunSnapshot]:
    snapshots: list[V5RunSnapshot] = []
    for path in paths:
        if not path.is_file():
            raise ValueError(f"run snapshot not found: {path}")
        try:
            snapshots.append(V5RunSnapshot.from_json(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError, KeyError, ValueError) as exc:
            raise ValueError(f"invalid run snapshot {path}: {exc}") from exc
    return snapshots


def render_markdown(metrics: dict[str, Any]) -> str:
    """仅从 JSON 指标对象渲染 Markdown，保证两个格式同源。"""

    lines = [
        "# 六源三领域十八槽位能力覆盖与弃权诊断",
        "",
        f"- 运行快照：{metrics['run_count']}",
        f"- 输入制品：{metrics['input_count']}（重复 run 去重：{metrics['deduplicated_run_count']}）",
        f"- 十八槽位：{metrics['slot_count']}",
        f"- 高风险门禁：{metrics['high_risk_gate']['availability']} — {metrics['high_risk_gate']['note']}",
        "- registration status 与 runtime status 严格分账；前者是当前注册能力，后者是已校验运行观测。",
        "",
        "## 槽位状态",
        "",
        "| school | domain | registration status | runtime status |",
        "|---|---|---|---|",
    ]
    for row in metrics["slots"]:
        runtime = ", ".join(f"{key}={value}" for key, value in row["runtime_status_counts"].items()) or "none"
        lines.append(f"| {row['school']} | {row['domain']} | {row['registration_status']} | {runtime} |")
    lines.extend(
        [
            "",
            "## school/domain/task 指标",
            "",
            "| school | domain | task | registration | runtime | implemented | abstain | unsupported | claims | evidence | conflict | timing | high risk gate |",
            "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in metrics["tasks"]:
        runtime = ", ".join(f"{key}={value}" for key, value in row["runtime_status_counts"].items()) or "none"
        lines.append(
            f"| {row['school']} | {row['domain']} | {row['task']} | {row['registration_status']} | {runtime} | "
            f"{row['implemented_count']} | {row['abstain_count']} | {row['unsupported_count']} | {row['claim_count']} | "
            f"{row['evidence_completeness_rate']:.6f} | {row['conflict_rate']:.6f} | "
            f"{row['timing_coverage_rate']:.6f} | {row['high_risk']['gate_status']} |"
        )
    lines.extend(["", "## 弃权原因 taxonomy", "", "| reason | count |", "|---|---:|"])
    for row in metrics["abstain_reason_taxonomy"]:
        lines.append(f"| {row['reason']} | {row['count']} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    try:
        paths = _paths(args.inputs)
        metrics = build_capability_metrics(_load(paths))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        prefix = "check failed" if args.check else "scan failed"
        print(f"domain capability {prefix}: {exc}", file=sys.stderr)
        return 1
    if args.check:
        print(
            "domain capability check passed: "
            f"runs={metrics['run_count']} slots={metrics['slot_count']} "
            f"deduplicated={metrics['deduplicated_run_count']}"
        )
        return 0
    if args.format == "json":
        print(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_markdown(metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
