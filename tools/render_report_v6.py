"""tools.render_report_v6 · v5/v6 预生产报告渲染入口。

最小闭环：case input.md → chart DTO → run_v5 → report-v6 ViewModel → Markdown。
该入口不替换 tools.render_report.py，不改旧生产主流程。
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from engine.v5.report_view import render_report_v6_from_output
from engine.v5.runner import run_v5

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = REPO_ROOT / "templates" / "report-v6.md"

PILLAR_RE = re.compile(r"\| \*\*(年柱|月柱|日柱|时柱)\*\* \|[^|]*\|\s*([^|\s]+)\s*\|\s*([^|\s]+)\s*\|")
FIELD_ROW_RE = re.compile(r"\| \*\*(?P<key>[^*]+)\*\* \| (?P<value>[^|]+) \|")
DAYUN_RE = re.compile(r"\|\s*\d+\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*\*\*([^*]+)\*\*")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_case_id(input_path: Path, text: str) -> str:
    match = re.search(r"#\s+([^\s]+)\s+·\s+输入信息", text)
    if match:
        return match.group(1)
    return input_path.parent.name


def _parse_gender_marker(case_id: str, text: str) -> str:
    if "-乾-" in case_id or "乾造" in text or "男（乾造）" in text:
        return "乾"
    if "-坤-" in case_id or "坤造" in text or "女（坤造）" in text:
        return "坤"
    return "乾/坤"


def _parse_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for match in FIELD_ROW_RE.finditer(text):
        fields[match.group("key").strip()] = match.group("value").strip()
    return fields


def _parse_pillars(text: str) -> dict[str, str]:
    pillars: dict[str, str] = {}
    key_map = {
        "年柱": ("year_stem", "year_branch"),
        "月柱": ("month_stem", "month_branch"),
        "日柱": ("day_stem", "day_branch"),
        "时柱": ("hour_stem", "hour_branch"),
    }
    for match in PILLAR_RE.finditer(text):
        stem_key, branch_key = key_map[match.group(1)]
        pillars[stem_key] = match.group(2).strip()
        pillars[branch_key] = match.group(3).strip()
    return pillars


def _parse_dayun_summary(text: str) -> str:
    items: list[str] = []
    for match in DAYUN_RE.finditer(text):
        age_range = match.group(1).strip()
        year_range = match.group(2).strip()
        ganzhi = match.group(3).strip()
        items.append(f"{ganzhi}运：{year_range}（{age_range}）")
    return "；".join(items[:10]) or "见案例输入"


def _parse_current_dayun(text: str) -> str:
    """解析当前大运，避免跨行误捕大运表格。"""

    for line in text.splitlines():
        if "⚠️ 当前运" in line:
            match = re.search(r"\*\*([^*]+)\*\*", line)
            if match:
                return match.group(1).strip()
        if "当前大运" in line:
            match = re.search(r"当前大运[:：】\s]*([^，。\n|]+)", line)
            if match:
                value = match.group(1).strip()
                if value:
                    return value
        if "当前位置" in line and "大运" in line:
            match = re.search(r"：\s*([^（，。\n]+大运)", line)
            if match:
                return match.group(1).strip()
    return "待补充"


def _parse_current_year(text: str) -> str:
    match = re.search(r"流年([^（\n]+（\d{4}\s*年）|\d{4}\s*年)", text)
    if match:
        return match.group(0).replace("流年", "").strip()
    match = re.search(r"当前位置（\d{4}-\d{2}-\d{2}）", text)
    if match:
        return match.group(0)[5:9]
    return "当前流年"


def build_chart_from_input(input_path: str | Path) -> dict[str, Any]:
    """从 case input.md 构造 v5 MVP chart DTO。"""

    path = Path(input_path)
    text = _read_text(path)
    fields = _parse_fields(text)
    chart: dict[str, Any] = {
        "case_id": _parse_case_id(path, text),
        "gender_marker": _parse_gender_marker(path.parent.name, text),
        "current_dayun": _parse_current_dayun(text),
        "current_year": _parse_current_year(text),
        "start_luck": fields.get("起运/交运", "待补充"),
        "dayun_summary": _parse_dayun_summary(text),
        "source_input": str(path.as_posix()),
    }
    chart.update(_parse_pillars(text))
    chart["pillars"] = {
        "year": chart.get("year_stem", "") + chart.get("year_branch", ""),
        "month": chart.get("month_stem", "") + chart.get("month_branch", ""),
        "day": chart.get("day_stem", "") + chart.get("day_branch", ""),
        "hour": chart.get("hour_stem", "") + chart.get("hour_branch", ""),
    }
    return chart


def _display_path(path: Path) -> str:
    """优先返回仓库相对路径；仓库外路径保留绝对路径。"""

    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def render_case(input_path: str | Path, *, output_path: str | Path | None = None, template_path: str | Path = DEFAULT_TEMPLATE) -> tuple[Path, Path]:
    """渲染一个 case，返回 (report_path, json_path)。"""

    input_file = Path(input_path)
    if not input_file.is_absolute():
        input_file = REPO_ROOT / input_file
    chart = build_chart_from_input(input_file)
    case_id = chart["case_id"]
    report_file = Path(output_path) if output_path else REPO_ROOT / "reports" / f"{case_id}-v6-preprod-content-report.md"
    if not report_file.is_absolute():
        report_file = REPO_ROOT / report_file
    json_file = report_file.with_suffix(".v5.json")
    case_dir = input_file.parent
    feedback_path = case_dir / "feedback.md"

    output = run_v5(chart, case_id=case_id, workspace_root=str(REPO_ROOT))
    report_md = render_report_v6_from_output(
        output,
        template_path=template_path,
        report_path=_display_path(report_file),
        case_dir=_display_path(case_dir),
        feedback_path=_display_path(feedback_path),
    )

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report_md, encoding="utf-8")
    json_file.write_text(output.to_json(), encoding="utf-8")
    return report_file, json_file


def _default_output_for_input(input_path: str | Path, output_dir: str | Path) -> Path:
    """按 case_id 在指定目录下生成默认 v6 报告路径。"""

    input_file = Path(input_path)
    if not input_file.is_absolute():
        input_file = REPO_ROOT / input_file
    chart = build_chart_from_input(input_file)
    return Path(output_dir) / f"{chart['case_id']}-v6-preprod-content-report.md"


def render_cases(
    input_paths: list[str | Path],
    *,
    output_dir: str | Path | None = None,
    template_path: str | Path = DEFAULT_TEMPLATE,
) -> list[tuple[Path, Path]]:
    """批量渲染多个 case，返回每个 case 的 (report_path, json_path)。"""

    target_dir = Path(output_dir) if output_dir is not None else REPO_ROOT / "reports"
    if not target_dir.is_absolute():
        target_dir = REPO_ROOT / target_dir
    outputs: list[tuple[Path, Path]] = []
    for input_path in input_paths:
        report_path = _default_output_for_input(input_path, target_dir)
        outputs.append(render_case(input_path, output_path=report_path, template_path=template_path))
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="渲染 v6 预生产五派并行裁判报告")
    parser.add_argument("input", nargs="+", help="一个或多个 case input.md 路径")
    parser.add_argument("--output", "-o", help="单案报告输出路径；仅允许配合一个 input 使用", default=None)
    parser.add_argument("--output-dir", help="批量输出目录；默认 reports/", default=None)
    parser.add_argument("--template", help="模板路径", default=str(DEFAULT_TEMPLATE))
    args = parser.parse_args(argv)

    if args.output and len(args.input) != 1:
        parser.error("--output 只能在单个 input 时使用；批量请使用 --output-dir。")

    if len(args.input) == 1:
        report_path, json_path = render_case(args.input[0], output_path=args.output, template_path=args.template)
        print(f"[OK] report: {_display_path(report_path)}")
        print(f"[OK] v5 json: {_display_path(json_path)}")
        return 0

    rendered = render_cases(args.input, output_dir=args.output_dir, template_path=args.template)
    for report_path, json_path in rendered:
        print(f"[OK] report: {_display_path(report_path)}")
        print(f"[OK] v5 json: {_display_path(json_path)}")
    print(f"[OK] rendered {len(rendered)} reports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
