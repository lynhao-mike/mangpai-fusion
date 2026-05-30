"""领域层 ID / 正则协议。

集中维护 statement_id、feedback 标注与 rule_id 抽取正则，保证报告渲染、反馈摄入、
边界挖掘等工具消费同一套稳定协议。
"""
from __future__ import annotations

import hashlib
import re
from typing import Iterable


RULE_ID_PATTERN = (
    r"\b(?:"
    r"M[123]-[A-Z]-\d+"
    r"|MR-(?:LAYER\d+|[A-Z\d-]+|\d+)"
    r"|XF-\d+"
    r"|G(?:-[A-Z0-9\u4e00-\u9fff]+){1,3}-?\d*"
    r"|GP-[A-Z0-9\u4e00-\u9fff_]+(?:-[A-Z0-9\u4e00-\u9fff_]+)*"
    r")\b"
)
RULE_ID_RE = re.compile(RULE_ID_PATTERN)
RULE_ID_WITH_LAYER_RE = RULE_ID_RE

RULE_ID_RELAX_PATTERN = (
    r"\b(?:"
    r"M[123]-[A-Z]-\d+"
    r"|MR-[A-Z\d-]+"
    r"|G-[A-Z]+(?:-[\u4e00-\u9fff\w]+)?"
    r"|GP-[A-Z0-9\u4e00-\u9fff_]+(?:-[A-Z0-9\u4e00-\u9fff_]+)*"
    r")\b"
)
RULE_ID_RE_RELAX = re.compile(RULE_ID_RELAX_PATTERN)

STATEMENT_ID_PATTERN = r"S-[A-Za-z0-9_]+-[a-f0-9]{6}"
STATEMENT_ID_RE = re.compile(rf"\b{STATEMENT_ID_PATTERN}\b")
FEEDBACK_RE = re.compile(
    rf"\[({STATEMENT_ID_PATTERN})\]\s*\[(y|n|\?|skip)\]",
    re.IGNORECASE,
)
FEEDBACK_SLOT_RE = re.compile(rf"\[{STATEMENT_ID_PATTERN}\]\s*\[\s*\]")


def short_case_id(case_id: str) -> str:
    """提取 statement_id 中使用的短 case 编号。"""
    parts = case_id.split("-") if case_id else []
    if len(parts) >= 3 and parts[2].isdigit():
        return parts[2]
    if case_id:
        return case_id[:6].replace("/", "_").replace("\\", "_")
    return "UNK"


def normalize_rule_ids(rule_ids: Iterable[str] | None) -> list[str]:
    """statement_id hash 前的 rule_id 去空、去重、排序规范化。"""
    normalized: set[str] = set()
    for rid in rule_ids or []:
        s = str(rid).strip()
        if s:
            normalized.add(s)
    return sorted(normalized) or ["NONE"]


def compute_statement_id(case_id: str, rule_ids: Iterable[str] | None) -> str:
    """稳定断语 ID：S-{short_case}-{sha256(short_case|sorted_rule_ids)[:6]}。"""
    short_case = short_case_id(case_id or "")
    payload = f"{short_case}|{','.join(normalize_rule_ids(rule_ids))}"
    trace_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:6]
    return f"S-{short_case}-{trace_hash}"
