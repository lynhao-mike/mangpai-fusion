"""tools/cross_domain_consistency_check.py · 跨域一致性扫描工具

用途：
    1. 批量扫描 reports/*.md，复用 output_linter 的 W9 cross-domain coupling 检查；
    2. 对 parallel analysis JSON 执行 application service 级跨域一致性检查。

示例：
    python tools/cross_domain_consistency_check.py --backfill
    python tools/cross_domain_consistency_check.py --parallel-json findings/parallel.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.application.cross_domain_consistency import evaluate_cross_domain_consistency
from engine.domain.parallel import ParallelAnalysisOutput
from tools.output_linter import lint

REPORTS_DIR = ROOT / "reports"
DEFAULT_OUTPUT = ROOT / "META" / "cross-domain-backfill.md"


@dataclass(frozen=True)
class BackfillHit:
    path: pathlib.Path
    warnings: list[str]


def scan_reports(reports_dir: pathlib.Path = REPORTS_DIR) -> list[BackfillHit]:
    """扫描 reports/*.md 中的 W9 跨维度耦合告警。"""
    hits: list[BackfillHit] = []
    for path in sorted(reports_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        result = lint(text)
        w9 = [i.message for i in result.warnings if i.code == "W9"]
        if w9:
            hits.append(BackfillHit(path=path, warnings=w9))
    return hits


def scan_parallel_json(path: pathlib.Path) -> list[dict]:
    """读取 ParallelAnalysisOutput JSON 并返回跨域一致性 note dict。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    output = ParallelAnalysisOutput.from_dict(data)
    return [
        note.to_dict()
        for note in evaluate_cross_domain_consistency(output.domain_analyses, case_id=output.case_id)
    ]


def render_markdown(hits: list[BackfillHit]) -> str:
    """渲染回溯扫描结果。"""
    lines = [
        "# cross-domain consistency backfill",
        "",
        "> 来源：`tools/cross_domain_consistency_check.py --backfill`；检查 `tools/output_linter.py` 的 W9。",
        "",
        f"- W9 触发报告数：{len(hits)}",
        "",
    ]
    if not hits:
        lines.append("未发现历史报告触发 W9。")
        lines.append("")
        return "\n".join(lines)

    lines.extend([
        "| 报告 | W9 告警 |",
        "|---|---|",
    ])
    for hit in hits:
        rel = hit.path.relative_to(ROOT).as_posix()
        msg = "<br>".join(m.replace("|", "\\|") for m in hit.warnings)
        lines.append(f"| `{rel}` | {msg} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="跨维度输出一致性扫描")
    parser.add_argument("--backfill", action="store_true", help="扫描 reports/*.md")
    parser.add_argument("--parallel-json", help="扫描 ParallelAnalysisOutput JSON")
    parser.add_argument("--write", nargs="?", const=str(DEFAULT_OUTPUT), help="把 --backfill 结果写入指定 markdown 文件；不带路径时写 META/cross-domain-backfill.md")
    args = parser.parse_args(argv)

    if args.parallel_json:
        path = pathlib.Path(args.parallel_json)
        if not path.is_absolute():
            path = ROOT / path
        print(json.dumps(scan_parallel_json(path), ensure_ascii=False, indent=2))
        return 0

    if not args.backfill:
        parser.error("必须指定 --backfill 或 --parallel-json")

    hits = scan_reports()
    md = render_markdown(hits)
    print(md)

    if args.write:
        out = pathlib.Path(args.write)
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT).as_posix()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
