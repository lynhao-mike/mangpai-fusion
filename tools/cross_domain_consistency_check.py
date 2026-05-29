"""tools/cross_domain_consistency_check.py · v1.4 V8 历史报告耦合回溯扫描

用途：
    批量扫描 reports/*.md，复用 output_linter 的 W9 cross-domain coupling
    检查，输出历史报告中“高置信体制内信号 + 市场财富分级 + 无耦合标注”的清单。

示例：
    python tools/cross_domain_consistency_check.py --backfill
    python tools/cross_domain_consistency_check.py --backfill --write META/cross-domain-backfill.md
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
    parser = argparse.ArgumentParser(description="历史报告跨维度输出耦合 W9 回溯扫描")
    parser.add_argument("--backfill", action="store_true", help="扫描 reports/*.md")
    parser.add_argument("--write", nargs="?", const=str(DEFAULT_OUTPUT), help="把结果写入指定 markdown 文件；不带路径时写 META/cross-domain-backfill.md")
    args = parser.parse_args(argv)

    if not args.backfill:
        parser.error("必须指定 --backfill")

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
