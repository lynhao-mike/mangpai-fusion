"""Synchronize Wenzhen repan split index status and statistics.

This utility preserves pasted repan blocks in the male/female priority indexes,
then refreshes each entry status, per-file statistics, numbering, and the
navigation page statistics.
"""

from __future__ import annotations

import argparse
import pathlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DRAFTS_DIR = REPO_ROOT / "cases" / "raw_feedback" / "case_drafts"
NAV_PATH = DRAFTS_DIR / "wenzhen-repan-index.md"
MALE_PATH = DRAFTS_DIR / "wenzhen-repan-index-male.md"
FEMALE_PATH = DRAFTS_DIR / "wenzhen-repan-index-female.md"

ENTRY_RE = re.compile(r"(?m)^##\s+\d+\.\s+(RF-\d{4}-\d{6})")
META_RE = re.compile(r"^(?P<key>[^:\n]+):\s*(?P<value>.*)$", re.M)
CODE_BLOCK_RE = re.compile(r"问真排盘：\s*\n\s*```text\n(?P<body>.*?)\n```", re.S)
REQUIRED_REPAN_MARKERS = ("$BASE", "$FOUR", "$DY_LOOP")


@dataclass
class Entry:
    raw_id: str
    body: str
    original_position: int
    complete: bool
    event_count: int
    quality: str
    score: int
    original_index: int

    @property
    def status(self) -> str:
        return "已补" if self.complete else "待补"


def sync_indexes(*, dry_run: bool = False) -> dict[str, tuple[int, int, int]]:
    now = datetime.now(timezone.utc).isoformat()
    male_entries = _read_entries(MALE_PATH)
    female_entries = _read_entries(FEMALE_PATH)

    stats: dict[str, tuple[int, int, int]] = {}
    for path, gender, entries in (
        (MALE_PATH, "男", male_entries),
        (FEMALE_PATH, "女", female_entries),
    ):
        ordered = _ordered_entries(entries)
        complete_count = sum(1 for entry in ordered if entry.complete)
        pending_count = len(ordered) - complete_count
        stats[gender] = (len(ordered), pending_count, complete_count)
        content = _render_gender_index(gender, now, ordered, pending_count, complete_count)
        if not dry_run:
            path.write_text(content, encoding="utf-8")

    total = len(male_entries) + len(female_entries)
    male_total, male_pending, male_complete = stats["男"]
    female_total, female_pending, female_complete = stats["女"]
    nav_content = _render_nav(
        now=now,
        total=total,
        male_total=male_total,
        male_pending=male_pending,
        male_complete=male_complete,
        female_total=female_total,
        female_pending=female_pending,
        female_complete=female_complete,
    )
    if not dry_run:
        NAV_PATH.write_text(nav_content, encoding="utf-8")
    return stats


def _read_entries(path: pathlib.Path) -> list[Entry]:
    text = path.read_text(encoding="utf-8")
    matches = list(ENTRY_RE.finditer(text))
    entries: list[Entry] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        entries.append(_parse_entry(match.group(1), chunk, index))
    return entries


def _parse_entry(raw_id: str, chunk: str, original_position: int) -> Entry:
    meta = {match.group("key").strip(): match.group("value").strip() for match in META_RE.finditer(chunk)}
    repan_body = _repan_body(chunk)
    complete = _is_complete_repan(repan_body)
    updated = _replace_meta(chunk, "状态", "已补" if complete else "待补")
    return Entry(
        raw_id=raw_id,
        body=updated,
        original_position=original_position,
        complete=complete,
        event_count=_int_value(meta.get("事件数", "0")),
        quality=meta.get("质量等级", ""),
        score=_int_value(meta.get("评分", "0")),
        original_index=_int_value(meta.get("原索引序号", "0")),
    )


def _repan_body(chunk: str) -> str:
    match = CODE_BLOCK_RE.search(chunk)
    return match.group("body").strip() if match else ""


def _is_complete_repan(body: str) -> bool:
    if not body or body == "？":
        return False
    return all(marker in body for marker in REQUIRED_REPAN_MARKERS)


def _replace_meta(chunk: str, key: str, value: str) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(key)}:\s*.*$")
    replacement = f"{key}: {value}"
    if pattern.search(chunk):
        return pattern.sub(replacement, chunk, count=1)
    lines = chunk.splitlines()
    insert_at = 2 if len(lines) >= 2 else len(lines)
    lines.insert(insert_at, replacement)
    return "\n".join(lines)


def _ordered_entries(entries: list[Entry]) -> list[Entry]:
    return sorted(
        entries,
        key=lambda entry: (
            entry.complete,
            -entry.score,
            _quality_rank(entry.quality),
            -entry.event_count,
            entry.original_index or 999999,
            entry.raw_id,
        ),
    )


def _quality_rank(value: str) -> int:
    order = {"A": 0, "B": 1, "C": 2, "D": 3}
    return order.get(value.strip().upper(), 9)


def _render_gender_index(
    gender: str,
    now: str,
    entries: list[Entry],
    pending_count: int,
    complete_count: int,
) -> str:
    lines = [
        f"# 问真排盘补录索引 · {'男命' if gender == '男' else '女命'}优先级",
        "",
        f"> 生成时间：{now}",
        "> 来源：`cases/raw_feedback/case_drafts/wenzhen-repan-index.md`",
        f"> 性别筛选：{gender}",
        "",
        "## 统计",
        "",
        f"- 本性别条目数：{len(entries)}",
        f"- 待补排盘数：{pending_count}",
        f"- 已补排盘数：{complete_count}",
        "- 排序：待补优先；同为待补时按评分、质量等级、事件数、原索引序号排序；已补条目保留在文末。",
        "",
        "## 使用方法",
        "",
        "1. 优先补 `问真排盘：` 下仍为 `？` 的条目。",
        "2. 每条标题后先看 `太阳时: “性别”`，下一行是纯数字太阳时。",
        "3. 将纯数字太阳时复制到问真八字 APP 排盘。",
        "4. 将问真排盘原文粘贴到 `问真排盘：` 下方代码块，替换 `？`。",
        "5. 同步脚本以代码块内同时包含 `$BASE`、`$FOUR`、`$DY_LOOP` 判定为已补。",
        "6. 已补条目保留在文末，便于核验与后续回填草稿。",
        "",
        "---",
        "",
    ]
    for position, entry in enumerate(entries, start=1):
        body = re.sub(r"^##\s+\d+\.\s+", f"## {position:03d}. ", entry.body, count=1)
        body = _replace_meta(body, "优先级", str(position))
        body = re.sub(r"(?:\n---\s*)+$", "", body.rstrip())
        lines.append(body.rstrip())
        lines.extend(["", "---", ""])
    return "\n".join(lines).rstrip() + "\n"


def _render_nav(
    *,
    now: str,
    total: int,
    male_total: int,
    male_pending: int,
    male_complete: int,
    female_total: int,
    female_pending: int,
    female_complete: int,
) -> str:
    return (
        "# 问真排盘补录索引 · 按性别拆分入口\n\n"
        f"> 更新时间：{now}\n"
        "> 原完整索引已按性别拆分为两个优先级文档；已补排盘内容保留在对应性别文档中。\n\n"
        "## 文档入口\n\n"
        "- 男命优先索引：`cases/raw_feedback/case_drafts/wenzhen-repan-index-male.md`\n"
        "- 女命优先索引：`cases/raw_feedback/case_drafts/wenzhen-repan-index-female.md`\n\n"
        "## 统计\n\n"
        f"- 总条目数：{total}\n"
        f"- 男命条目数：{male_total}；待补：{male_pending}；已补：{male_complete}\n"
        f"- 女命条目数：{female_total}；待补：{female_pending}；已补：{female_complete}\n"
        "- 未识别性别条目数：0\n\n"
        "## 排序规则\n\n"
        "1. `状态: 待补` 排在 `状态: 已补` 前。\n"
        "2. 状态由排盘代码块自动判定：同时包含 `$BASE`、`$FOUR`、`$DY_LOOP` 为已补，否则为待补。\n"
        "3. 待补内部按评分、质量等级、事件数、原索引序号排序。\n"
        "4. 已补条目保留在文末，便于核验和后续回填正式草稿。\n"
    )


def _int_value(value: str) -> int:
    match = re.search(r"\d+", value or "")
    return int(match.group(0)) if match else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="同步问真排盘男/女拆分索引状态和统计")
    parser.add_argument("--dry-run", action="store_true", help="只计算统计，不写文件")
    args = parser.parse_args()
    stats = sync_indexes(dry_run=args.dry_run)
    print("sync_wenzhen_repan_index_status")
    print(f"  dry_run: {args.dry_run}")
    for gender in ("男", "女"):
        total, pending, complete = stats[gender]
        print(f"  {gender}: total={total} pending={pending} complete={complete}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
