"""tools/case_feedback_repan_index.py · 问真排盘补录索引生成器

用途：
    扫描 cases/raw_feedback/case_drafts/RF-.../input.md，生成一份人工补问真排盘索引。

输出：
    cases/raw_feedback/case_drafts/wenzhen-repan-index.md

边界：
    - 只读取 case draft。
    - 不改写单个 RF 草稿。
    - 不创建正式 C-... case。
    - 不运行 preflight / pipeline。
"""

from __future__ import annotations

import argparse
import pathlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DRAFTS_DIR = REPO_ROOT / "cases" / "raw_feedback" / "case_drafts"
DEFAULT_OUTPUT = DRAFTS_DIR / "wenzhen-repan-index.md"

BIRTH_BLOCK_RE = re.compile(r"\nbirth:\n(?P<body>.*?)(?=\n\n四柱:)", re.S)
SIZHU_BLOCK_RE = re.compile(r"\n四柱:\n(?P<body>.*?)(?=\n\n藏干:)", re.S)
EVENT_RE = re.compile(r"^\s*- year:\s*(?P<year>\S+)", re.M)


@dataclass(frozen=True)
class RepanEntry:
    raw_id: str
    input_path: pathlib.Path
    birth_block: str
    sizhu_block: str
    event_count: int
    needs_repan: bool


def collect_entries(drafts_dir: pathlib.Path = DRAFTS_DIR) -> list[RepanEntry]:
    entries: list[RepanEntry] = []
    for input_path in sorted(drafts_dir.glob("RF-*/input.md")):
        raw_id = input_path.parent.name
        text = input_path.read_text(encoding="utf-8")
        birth_block = _extract_block(BIRTH_BLOCK_RE, text)
        sizhu_block = _extract_block(SIZHU_BLOCK_RE, text)
        needs_repan = "待补" in sizhu_block or "待补" in birth_block
        event_count = len(EVENT_RE.findall(text))
        entries.append(
            RepanEntry(
                raw_id=raw_id,
                input_path=input_path,
                birth_block=birth_block,
                sizhu_block=sizhu_block,
                event_count=event_count,
                needs_repan=needs_repan,
            )
        )
    return entries


def render_index(entries: list[RepanEntry], *, only_needs_repan: bool = True) -> str:
    selected = [e for e in entries if e.needs_repan or not only_needs_repan]
    selected.sort(key=lambda e: (-e.event_count, e.raw_id))
    lines: list[str] = [
        "# 问真排盘补录索引 · 真实反馈 case drafts",
        "",
        f"> 生成时间：{datetime.now(timezone.utc).isoformat()}",
        f"> 来源目录：`{_rel(DRAFTS_DIR)}`",
        "",
        "## 使用方法",
        "",
        "1. 每条标题后先看 `太阳时: “性别”`，下一行是纯数字太阳时。",
        "2. 将纯数字太阳时复制到问真八字 APP 排盘。",
        "3. 将问真排盘原文粘贴到 `问真排盘：` 下方的占位区，替换 `？`。",
        "4. 其他字段不用手填；后续按 RF 编号回到原草稿自动/半自动补齐。",
        "",
        "## 统计",
        "",
        f"- draft 总数：{len(entries)}",
        f"- 本索引待补排盘数：{len(selected)}",
        "- 排序：事件数多的样本优先，便于理论验证。",
        "",
        "---",
        "",
    ]
    for idx, entry in enumerate(selected, start=1):
        lines.extend(_render_entry(idx, entry))
    return "\n".join(lines).rstrip() + "\n"


def write_index(
    *,
    output: pathlib.Path = DEFAULT_OUTPUT,
    only_needs_repan: bool = True,
    dry_run: bool = False,
) -> tuple[pathlib.Path, int, int]:
    entries = collect_entries()
    selected_count = len([e for e in entries if e.needs_repan or not only_needs_repan])
    content = render_index(entries, only_needs_repan=only_needs_repan)
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    return output, len(entries), selected_count


def _render_entry(index: int, entry: RepanEntry) -> list[str]:
    return [
        f"## {index:03d}. {entry.raw_id}",
        f"太阳时: “{_display_gender(entry.birth_block)}”",
        "",
        _compact_solar_time(entry.birth_block),
        "",
        "问真排盘：",
        "",
        "```text",
        "？",
        "```",
        "",
        "---",
        "",
    ]


def _extract_block(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    if not match:
        return "  待补: true"
    return match.group("body").rstrip()


def _compact_solar_time(birth_block: str) -> str:
    value = _birth_value(birth_block, "太阳时") or _birth_value(birth_block, "公历")
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits[:12] if len(digits) >= 12 else digits or "待补"
def _birth_value(birth_block: str, key: str) -> str:
    for line in birth_block.splitlines():
        stripped = line.strip()
        if not stripped.startswith(f"{key}:"):
            continue
        return stripped.split(":", 1)[1].strip().strip('"')
    return ""


def _display_gender(birth_block: str) -> str:
    value = _birth_value(birth_block, "性别").upper()
    if value == "M" or value == "男":
        return "男"
    if value == "F" or value == "女":
        return "女"
    return value or "待补"




def _rel(path: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="生成真实反馈问真排盘补录索引")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="输出 Markdown 路径")
    parser.add_argument("--include-complete", action="store_true", help="也包含已补完整四柱的样本")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写文件")
    args = parser.parse_args(argv)

    output, total, selected = write_index(
        output=pathlib.Path(args.output),
        only_needs_repan=not args.include_complete,
        dry_run=args.dry_run,
    )
    print("case_feedback_repan_index")
    print(f"  dry_run: {args.dry_run}")
    print(f"  drafts: {total}")
    print(f"  indexed: {selected}")
    print(f"  output: {_rel(output)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
