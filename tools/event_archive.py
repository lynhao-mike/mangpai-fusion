"""tools/event_archive.py · 交互事件增量归档工具。

用途
----
把一次临时问答 / 专项分析 / 处理结果追加归档到：
- cases/C-YYYY-NNN-*/events.md：能定位到案例时；
- META/session-events.md：无法定位到具体案例时。

本工具只做增量 append，不改写 analysis.md / feedback.md / statement_index.json，
避免把临时专项问答混入铁断报告或反馈校准通道。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "cases"
META_DIR = REPO_ROOT / "META"
CASE_ID_RE = re.compile(r"^C-\d{4}-\d{3}-")


@dataclass(frozen=True)
class ArchiveRecord:
    """一次交互归档记录。"""

    record_id: str
    target_path: Path
    case_id: Optional[str]
    created_at: str
    event_type: str
    question: str
    analysis: str
    result: str

    def to_markdown(self) -> str:
        case_line = self.case_id or "—"
        return "\n".join(
            [
                f"## {self.created_at} · {self.event_type} · {self.record_id}",
                "",
                f"- case_id：{case_line}",
                "",
                "### 询问",
                "",
                self.question.strip() or "—",
                "",
                "### 分析摘要",
                "",
                self.analysis.strip() or "—",
                "",
                "### 处理结果",
                "",
                self.result.strip() or "—",
                "",
                "---",
                "",
            ]
        )


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _record_id(created_at: str, case_id: Optional[str], question: str, result: str) -> str:
    raw = "\n".join([created_at, case_id or "META", question, result])
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
    return f"EVT-{created_at[:10].replace('-', '')}-{digest}"


def resolve_case_dir(case_id: str) -> Path:
    """按完整 case_id 或前缀定位案例目录。"""
    direct = CASES_DIR / case_id
    if direct.exists() and direct.is_dir():
        return direct
    if not CASES_DIR.exists():
        raise FileNotFoundError(f"cases 目录不存在: {CASES_DIR}")
    matches = [p for p in CASES_DIR.iterdir() if p.is_dir() and p.name.startswith(case_id)]
    if not matches:
        raise FileNotFoundError(f"case 目录不存在: {case_id}")
    if len(matches) > 1:
        names = ", ".join(p.name for p in matches[:5])
        raise ValueError(f"case_id 前缀不唯一: {case_id} -> {names}")
    return matches[0]


def _target_for(case_id: Optional[str]) -> tuple[Path, Optional[str]]:
    if case_id:
        case_dir = resolve_case_dir(case_id)
        return case_dir / "events.md", case_dir.name
    return META_DIR / "session-events.md", None


def _ensure_header(path: Path, case_id: Optional[str]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if case_id:
        title = f"# events · {case_id}\n\n> 本文件记录临时问答、专项分析与处理结果。由 tools/event_archive.py 增量维护；不作为反馈计分事实源。\n\n"
    else:
        title = "# session-events · 未绑定案例交互记录\n\n> 本文件记录无法归入具体 case 的临时问答、架构分析与处理结果。由 tools/event_archive.py 增量维护。\n\n"
    path.write_text(title, encoding="utf-8")


def archive_interaction(
    *,
    question: str,
    analysis: str,
    result: str,
    case_id: Optional[str] = None,
    event_type: str = "专项问答",
    created_at: Optional[str] = None,
    dry_run: bool = False,
) -> ArchiveRecord:
    """增量归档一次交互。

    Args:
        question: 用户本次询问原文或摘要。
        analysis: 分析过程摘要；建议记录依据、路径和关键判断。
        result: 最终交付结果摘要。
        case_id: 完整案例 ID 或唯一前缀；为空则写 META/session-events.md。
        event_type: 事件类型，如“财运专项”“架构评审”“反馈处理”。
        created_at: ISO UTC 时间；测试可注入。
        dry_run: True 时只返回记录，不写盘。
    """
    created = created_at or _utc_now()
    target_path, full_case_id = _target_for(case_id)
    rid = _record_id(created, full_case_id, question, result)
    record = ArchiveRecord(
        record_id=rid,
        target_path=target_path,
        case_id=full_case_id,
        created_at=created,
        event_type=event_type,
        question=question,
        analysis=analysis,
        result=result,
    )
    if dry_run:
        return record

    _ensure_header(target_path, full_case_id)
    with target_path.open("a", encoding="utf-8") as f:
        f.write(record.to_markdown())
    return record


def _read_arg(value: str) -> str:
    """支持 @path 从文件读取长文本。"""
    if value.startswith("@"):
        return Path(value[1:]).read_text(encoding="utf-8")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="增量归档一次问答 / 专项分析 / 处理结果")
    parser.add_argument("--case-id", default=None, help="完整 case_id 或唯一前缀；为空写 META/session-events.md")
    parser.add_argument("--event-type", default="专项问答", help="事件类型")
    parser.add_argument("--question", required=True, help="询问文本；支持 @file")
    parser.add_argument("--analysis", required=True, help="分析摘要；支持 @file")
    parser.add_argument("--result", required=True, help="处理结果；支持 @file")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写盘")
    args = parser.parse_args()

    record = archive_interaction(
        case_id=args.case_id,
        event_type=args.event_type,
        question=_read_arg(args.question),
        analysis=_read_arg(args.analysis),
        result=_read_arg(args.result),
        dry_run=args.dry_run,
    )
    print(f"[event_archive] record_id={record.record_id}")
    print(f"  target={record.target_path.relative_to(REPO_ROOT)}")
    if args.dry_run:
        print("  dry_run=true")


if __name__ == "__main__":
    main()
