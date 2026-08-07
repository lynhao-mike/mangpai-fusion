"""as-of 盲断闭环 · 候选优先级自动排序工具。

基于 §9.4 质量信号和已有脚手架状态，为尚未走完盲断闭环的候选案例排序，
避免每次手动查 §9.4 质量排名报告。

只读，不修改任何案例文件。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from tools.as_of_current_state_scanner import scan_feedback_current_state

__all__ = ("CandidatePriority", "rank_remaining_candidates")

_SECTION_9_4_RE = re.compile(
    r"^###\s+9\.4\b(?P<body>.*?)(?=^###\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
_YEAR_MONTH_RE = re.compile(r"\b\d{4}\s*年\s*(?:1[0-2]|0?[1-9])\s*月")
_ROW_RE = re.compile(r"^\s*\|\s*(?P<label>[^|]+?)\s*\|\s*(?P<value>[^|]*?)\s*\|\s*$", re.MULTILINE)
_SCAFFOLD_FILENAME = "asof-freeze-scaffold-draft.json"
_FREEZE_FILENAME = "asof-blind-freeze.json"
_PENDING_MARKER = "待命主确认"


@dataclass(frozen=True, slots=True)
class CandidatePriority:
    case_id: str
    section_9_4_score: int
    has_scaffold: bool
    already_frozen: bool
    priority_score: float


def _section_9_4_score(feedback_path: Path) -> int:
    content = feedback_path.read_text(encoding="utf-8")
    match = _SECTION_9_4_RE.search(content)
    if match is None:
        return 0

    body = match.group("body")
    score = 2 if _YEAR_MONTH_RE.search(body) else 0
    rows = {
        row.group("label").strip(): row.group("value").strip()
        for row in _ROW_RE.finditer(body)
    }
    before = rows.get("变化前状态", "")
    after = rows.get("变化后状态", "")
    if before and after and _PENDING_MARKER not in before and _PENDING_MARKER not in after:
        score += 2
    return score


def rank_remaining_candidates(cases_root: Path) -> tuple[CandidatePriority, ...]:
    """扫描 cases_root，排除已冻结案例，按优先级降序返回剩余候选。"""

    scan = scan_feedback_current_state(cases_root)
    priorities: list[CandidatePriority] = []
    for signal in scan.likely_has_current_state:
        case_dir = cases_root / signal.case_id
        already_frozen = (case_dir / _FREEZE_FILENAME).is_file()
        if already_frozen:
            continue

        has_scaffold = (case_dir / _SCAFFOLD_FILENAME).is_file()
        section_score = _section_9_4_score(case_dir / "feedback.md")
        priorities.append(
            CandidatePriority(
                case_id=signal.case_id,
                section_9_4_score=section_score,
                has_scaffold=has_scaffold,
                already_frozen=False,
                priority_score=float(section_score * 2 + int(has_scaffold)),
            )
        )

    return tuple(sorted(priorities, key=lambda item: (-item.priority_score, item.case_id)))
