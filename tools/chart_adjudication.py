"""chart-only 命局结构裁决入口。

该入口只接受命盘事实，调用现有 ChartAdjudication，不读取 cases、reports、
feedback、known_facts 或现实 outcome。它输出的是原局结构层主断；现实映射
仍由独立注册表和 Measurement Spec 门禁管理。

示例：
    py -3 -m tools.chart_adjudication --input chart.json --case-id synthetic --format markdown
    py -3 -m tools.chart_adjudication --input chart.json --case-id synthetic --format json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from engine.claims.orchestrator import ChartAdjudication, generate_chart_adjudication
from engine.evaluation.models import BlindTask


FORBIDDEN_KEY_FRAGMENTS = {
    "feedback",
    "known_facts",
    "outcome",
    "reality",
    "label",
    "report",
    "observation",
}


class ChartAdjudicationInputError(ValueError):
    """Raised when chart-only input contains an out-of-scope field."""


def _read_chart(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ChartAdjudicationInputError(f"missing chart input: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ChartAdjudicationInputError(f"invalid chart JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ChartAdjudicationInputError("chart input must be a JSON object")
    _assert_chart_only(value)
    if not (value.get("pillars") or value.get("four_pillars")):
        raise ChartAdjudicationInputError("chart input requires pillars or four_pillars")
    return value


def _assert_chart_only(value: object, path: str = "chart") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS):
                raise ChartAdjudicationInputError(
                    f"chart-only input contains forbidden field at {path}.{key}"
                )
            _assert_chart_only(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_chart_only(child, f"{path}[{index}]")


def structure_task() -> BlindTask:
    return BlindTask(
        task_id="structure.overview",
        domain="总体",
        claim_type="structure",
        scoring_method="chart_structure_adjudication",
        quantifiable=False,
        high_risk=False,
        allowed_time_horizons=[],
        required_input_fields=["four_pillars"],
        label_schema={},
        evaluation_note="Chart-only structure adjudication; no reality outcome input.",
    )


def _public_state(state: str) -> str:
    return {
        "primary": "已形成结构层主断",
        "partial": "部分结构目标已形成主断，仍有目标竞争未解决",
        "unresolved": "结构目标竞争未解决",
        "abstain": "结构层弃权",
        "unsupported": "结构任务不支持",
    }.get(state, state)


def render_chart_adjudication(result: ChartAdjudication) -> str:
    lines = [
        "# 命局结构层裁决（chart-only）",
        "",
        f"- 裁决状态：**{_public_state(result.state)}**",
        f"- 四柱：{'｜'.join(result.chart.four_pillars.get(key, '') for key in ('year', 'month', 'day', 'hour'))}",
        f"- 裁决说明：{result.rationale}",
        "",
        "## 主断",
        "",
    ]
    if result.primary_claims:
        for index, claim in enumerate(result.primary_claims, start=1):
            evidence = "；".join(item.text for item in claim.evidence) or "当前无独立证据文字。"
            falsifier = claim.falsifier or "当前未登记明确反证条件。"
            lines.extend([
                f"### {index}",
                "",
                f"- 判断：{claim.statement}",
                f"- 证据：{evidence}",
                f"- 反证条件：{falsifier}",
                "- 现实映射：未进入现实 outcome 测量层。",
                "",
            ])
    else:
        lines.extend(["当前没有形成可输出的唯一结构主断。", ""])

    unresolved = [unit for unit in result.units if unit.status == "UNRESOLVED"]
    if unresolved:
        lines.extend(["## 未决竞争", ""])
        for unit in unresolved:
            lines.append(f"- 当前保留 {len(unit.candidate_claim_ids)} 个竞争候选；不人工选择 winner。")
        lines.append("")

    lines.extend([
        "## 边界",
        "",
        "- 本结果只表示原局结构层裁决，不等于学历、职业、财富、婚姻或其他现实 outcome。",
        "- 当前没有批准的 CHART_L2→现实测量映射；现实结果不得回写本次 chart-only 裁决。",
        "",
    ])
    return "\n".join(lines)


def run(chart: dict[str, Any], *, case_id: str, schools: tuple[str, ...]) -> ChartAdjudication:
    return generate_chart_adjudication(
        chart,
        structure_task(),
        case_id=case_id,
        schools=schools,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="只用命盘事实执行原局结构层裁决。")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--school", action="append", dest="schools")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)
    try:
        chart = _read_chart(args.input)
        schools = tuple(args.schools or ("ziping", "ditiansui"))
        result = run(chart, case_id=args.case_id, schools=schools)
    except (ChartAdjudicationInputError, ValueError, OSError) as exc:
        print(f"chart adjudication failed closed: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_chart_adjudication(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
