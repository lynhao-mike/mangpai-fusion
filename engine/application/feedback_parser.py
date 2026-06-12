from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from engine.domain.ids import FEEDBACK_RE

FeedbackVerdict = Literal["hit", "miss", "no_data"]

ANNOTATION_TO_VERDICT: dict[str, FeedbackVerdict] = {
    "y": "hit",
    "n": "miss",
    "?": "no_data",
    "skip": "no_data",
}


@dataclass
class StatementFeedback:
    """一条断语级反馈。"""

    statement_id: str
    annotation: str
    verdict: FeedbackVerdict
    raw_line: str = ""


def parse_statement_feedback(text: str) -> list[StatementFeedback]:
    """从填好的 feedback.md 文本里抽出所有 `[S-...] [y/n/?/skip]` 标注。

    去重策略：同一 statement_id 出现多次 → 取最后一次有效标注。
    本模块不依赖 tools 层，供 application 与 CLI/tool 边界共同复用。
    """
    matches: dict[str, StatementFeedback] = {}
    for line in text.splitlines():
        for m in FEEDBACK_RE.finditer(line):
            sid = m.group(1)
            ann = m.group(2).lower()
            verdict = ANNOTATION_TO_VERDICT.get(ann, "no_data")
            matches[sid] = StatementFeedback(
                statement_id=sid,
                annotation=ann,
                verdict=verdict,
                raw_line=line.strip(),
            )
    return list(matches.values())
