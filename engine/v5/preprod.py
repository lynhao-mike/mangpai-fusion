"""engine.v5.preprod · v6 预生产渲染应用内服务。

提供 application 层可调用的 v5/v6 预生产闭环：
case input.md → chart DTO → run_v5 → report-v6 Markdown + v5 JSON。

本模块不依赖 tools.*，避免 application 层反向依赖。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from engine.v5.report_view import render_report_v6_from_output
from engine.v5.runner import run_v5

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


def _extract_yaml_front_matter(text: str) -> dict[str, Any] | None:
    """提取 ```yaml ... ``` 段；这是最懒且最稳的 input 解析入口。"""

    match = re.search(r"```yaml\s*(.*?)\s*```", text, flags=re.DOTALL)
    if not match:
        return None
    payload = yaml.safe_load(match.group(1))
    return payload if isinstance(payload, dict) else None


def build_chart_from_input(input_path: str | Path) -> dict[str, Any]:
    """从 case input.md 构造 v5 chart DTO。

    ponytail: 先吃 YAML front matter，失败再回退旧正则表格解析。
    """

    path = Path(input_path)
    text = _read_text(path)
    payload = _extract_yaml_front_matter(text)
    if payload:
        birth = payload.get("birth", {}) or {}
        sizhu = payload.get("四柱", {}) or {}
        dayun = payload.get("大运", {}) or {}
        paida = dayun.get("排布", []) or []
        current_dayun = paida[0].get("干支", "待补充") if paida else "待补充"
        if paida:
            for item in paida:
                try:
                    start_year = int(str(item.get("起讫", "")).split("-")[0])
                except Exception:
                    continue
                if start_year <= 2026:
                    current_dayun = str(item.get("干支", current_dayun))
        chart = {
            "case_id": str(payload.get("case_meta", {}).get("case_id") or _parse_case_id(path, text)),
            "gender_marker": _parse_gender_marker(path.parent.name, text),
            "current_dayun": current_dayun,
            "current_year": _parse_current_year(text),
            "start_luck": f"出生后 {dayun.get('起运岁', '待补充')} 年起运" if dayun.get("起运岁") is not None else "待补充",
            "dayun_summary": "；".join(
                f"{item.get('干支', '')}运：{item.get('起讫', '')}（{item.get('起岁', '')}-{item.get('止岁', '')} 岁）"
                for item in paida[:10]
            ) or "见案例输入",
            "source_input": str(path.as_posix()),
            "year_stem": str(sizhu.get("年柱", "")[:1]),
            "year_branch": str(sizhu.get("年柱", "")[1:]),
            "month_stem": str(sizhu.get("月柱", "")[:1]),
            "month_branch": str(sizhu.get("月柱", "")[1:]),
            "day_stem": str(sizhu.get("日柱", "")[:1]),
            "day_branch": str(sizhu.get("日柱", "")[1:]),
            "hour_stem": str(sizhu.get("时柱", "")[:1]),
            "hour_branch": str(sizhu.get("时柱", "")[1:]),
        }
        chart["pillars"] = {
            "year": str(sizhu.get("年柱", "")),
            "month": str(sizhu.get("月柱", "")),
            "day": str(sizhu.get("日柱", "")),
            "hour": str(sizhu.get("时柱", "")),
        }
        return chart

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


def _display_path(path: Path, *, workspace_root: Path) -> str:
    try:
        return path.relative_to(workspace_root).as_posix()
    except ValueError:
        return path.as_posix()


def default_v6_report_path(input_path: str | Path, *, reports_dir: str | Path) -> Path:
    """按 case_id 生成默认 v6 预生产报告路径。"""

    chart = build_chart_from_input(input_path)
    return Path(reports_dir) / f"{chart['case_id']}-v6-preprod-content-report.md"


def render_v6_preprod_case(
    input_path: str | Path,
    *,
    output_path: str | Path | None = None,
    reports_dir: str | Path | None = None,
    template_path: str | Path = "templates/report-v6.md",
    workspace_root: str | Path = ".",
) -> tuple[Path, Path]:
    """渲染一个 v6 预生产 case，返回 (report_path, json_path)。"""

    root = Path(workspace_root).resolve()
    input_file = Path(input_path)
    if not input_file.is_absolute():
        input_file = root / input_file
    input_file = input_file.resolve()
    template_file = Path(template_path)
    if not template_file.is_absolute():
        template_file = root / template_file
    if output_path is None:
        target_dir = Path(reports_dir) if reports_dir is not None else root / "reports"
        if not target_dir.is_absolute():
            target_dir = root / target_dir
        report_file = default_v6_report_path(input_file, reports_dir=target_dir)
    else:
        report_file = Path(output_path)
        if not report_file.is_absolute():
            report_file = root / report_file
    report_file = report_file.resolve()
    json_file = report_file.with_suffix(".v5.json")

    chart = build_chart_from_input(input_file)
    case_id = str(chart["case_id"])
    case_dir = input_file.parent
    feedback_path = case_dir / "feedback.md"
    output = run_v5(chart, case_id=case_id, workspace_root=str(root))
    report_md = render_report_v6_from_output(
        output,
        template_path=template_file,
        report_path=_display_path(report_file, workspace_root=root),
        case_dir=_display_path(case_dir, workspace_root=root),
        feedback_path=_display_path(feedback_path, workspace_root=root),
    )
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report_md, encoding="utf-8")
    json_file.write_text(output.to_json(), encoding="utf-8")
    return report_file, json_file


def render_v6_preprod_cases(
    input_paths: list[str | Path],
    *,
    output_dir: str | Path | None = None,
    template_path: str | Path = "templates/report-v6.md",
    workspace_root: str | Path = ".",
) -> list[tuple[Path, Path]]:
    """批量渲染多个 v6 预生产 case。"""

    root = Path(workspace_root).resolve()
    target_dir = Path(output_dir) if output_dir is not None else root / "reports"
    if not target_dir.is_absolute():
        target_dir = root / target_dir
    outputs: list[tuple[Path, Path]] = []
    for input_path in input_paths:
        outputs.append(
            render_v6_preprod_case(
                input_path,
                reports_dir=target_dir,
                template_path=template_path,
                workspace_root=root,
            )
        )
    return outputs
