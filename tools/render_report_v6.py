"""tools.render_report_v6 · v5/v6 预生产报告渲染 CLI。

最小闭环：case input.md → chart DTO → run_v5 → report-v6 ViewModel → Markdown。
该入口不替换 tools.render_report.py，不改旧生产主流程。

实际渲染逻辑位于 engine.v5.preprod，避免 application 层反向依赖 tools.*。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from engine.v5.preprod import (
    build_chart_from_input,
    render_v6_preprod_case,
    render_v6_preprod_cases,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = REPO_ROOT / "templates" / "report-v6.md"


def _display_path(path: Path) -> str:
    """优先返回仓库相对路径；仓库外路径保留绝对路径。"""

    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def render_case(input_path: str | Path, *, output_path: str | Path | None = None, template_path: str | Path = DEFAULT_TEMPLATE) -> tuple[Path, Path]:
    """渲染一个 case，返回 (report_path, json_path)。"""

    return render_v6_preprod_case(
        input_path,
        output_path=output_path,
        template_path=template_path,
        workspace_root=REPO_ROOT,
    )


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

    return render_v6_preprod_cases(
        input_paths,
        output_dir=output_dir or REPO_ROOT / "reports",
        template_path=template_path,
        workspace_root=REPO_ROOT,
    )


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
