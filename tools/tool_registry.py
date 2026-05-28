"""tools/tool_registry.py · 工具注册表生成 / 校验器

用途：
    1. 扫描 tools/*.py，提取每个工具的首行 docstring 摘要。
    2. 按 tools/README.md 中的 active/deprecated/historical/missing 章节生成注册表。
    3. 输出 JSON 或 Markdown，作为人工索引之外的可执行真相源。

只读工具：不会修改仓库文件。

示例：
    python tools/tool_registry.py --format markdown
    python tools/tool_registry.py --format json
    python tools/tool_registry.py --check
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import sys
import warnings
from dataclasses import asdict, dataclass
from typing import Literal

ToolStatus = Literal["active", "internal", "deprecated", "historical", "missing", "unindexed"]

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"
README_PATH = TOOLS_DIR / "README.md"

STATUS_HEADINGS: dict[str, ToolStatus] = {
    "active": "active",
    "internal": "internal",
    "deprecated": "deprecated",
    "historical": "historical",
    "missing": "missing",
}

TOOL_LINK_RE = re.compile(r"\[`([^`]+\.py)`\]|\|\s*`([^`]+\.py)`\s*\|")


@dataclass(frozen=True)
class ToolEntry:
    name: str
    status: ToolStatus
    path: str | None
    summary: str
    exists: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _rel(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _first_docline(path: pathlib.Path) -> str:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return f"<syntax-error: {exc.msg}>"
    doc = ast.get_docstring(tree) or ""
    if not doc.strip():
        return ""
    return doc.strip().splitlines()[0].strip()


def _scan_python_tools() -> dict[str, pathlib.Path]:
    return {
        path.name: path
        for path in sorted(TOOLS_DIR.glob("*.py"))
        if path.name != "__init__.py"
    }


def _read_readme_statuses() -> dict[str, ToolStatus]:
    if not README_PATH.exists():
        return {}

    statuses: dict[str, ToolStatus] = {}
    current: ToolStatus | None = None
    for line in README_PATH.read_text(encoding="utf-8").splitlines():
        heading = line.strip().lower()
        for key, status in STATUS_HEADINGS.items():
            if heading.startswith(f"## {key}"):
                current = status
                break
        else:
            # no heading change
            pass

        if current is None:
            continue
        if line.lstrip().startswith("|"):
            for match in TOOL_LINK_RE.finditer(line):
                name = match.group(1) or match.group(2)
                statuses[name] = current
    return statuses


def build_registry() -> list[ToolEntry]:
    tools = _scan_python_tools()
    readme_statuses = _read_readme_statuses()
    entries: list[ToolEntry] = []

    for name, path in tools.items():
        status = readme_statuses.get(name, "unindexed")
        entries.append(ToolEntry(
            name=name,
            status=status,
            path=_rel(path),
            summary=_first_docline(path),
            exists=True,
        ))

    for name, status in readme_statuses.items():
        if name in tools:
            continue
        if status == "missing":
            entries.append(ToolEntry(
                name=name,
                status="missing",
                path=None,
                summary="README declares this historical name as missing.",
                exists=False,
            ))
        else:
            entries.append(ToolEntry(
                name=name,
                status=status,
                path=None,
                summary="README references this tool but no matching file exists.",
                exists=False,
            ))

    order = {"active": 0, "internal": 1, "deprecated": 2, "historical": 3, "unindexed": 4, "missing": 5}
    entries.sort(key=lambda e: (order[e.status], e.name))
    return entries


def registry_to_markdown(entries: list[ToolEntry]) -> str:
    lines = [
        "# tools registry",
        "",
        "| status | tool | exists | path | summary |",
        "|---|---|---:|---|---|",
    ]
    for e in entries:
        path = e.path or ""
        lines.append(
            f"| {e.status} | `{e.name}` | {str(e.exists).lower()} | {path} | {e.summary} |"
        )
    lines.append("")
    return "\n".join(lines)


def registry_to_json(entries: list[ToolEntry]) -> str:
    return json.dumps([e.to_dict() for e in entries], ensure_ascii=False, indent=2)


def check_registry(entries: list[ToolEntry]) -> list[str]:
    problems: list[str] = []
    for e in entries:
        if e.status == "unindexed":
            problems.append(f"UNINDEXED tool exists but is absent from tools/README.md: {e.name}")
        if e.status != "missing" and not e.exists:
            problems.append(f"BROKEN README reference: {e.name} is marked {e.status} but file is missing")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan tools/*.py and build an executable tool registry.")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--check", action="store_true", help="exit non-zero when registry/README drift is detected")
    args = parser.parse_args(argv)

    entries = build_registry()
    if args.check:
        problems = check_registry(entries)
        if problems:
            print("tool registry check failed:", file=sys.stderr)
            for p in problems:
                print(f"- {p}", file=sys.stderr)
            return 1
        print("tool registry check passed")
        return 0

    if args.format == "json":
        print(registry_to_json(entries))
    else:
        print(registry_to_markdown(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
