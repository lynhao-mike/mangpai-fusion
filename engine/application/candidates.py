"""应用层候选事件提取：把已知事实映射为应期候选。"""

from __future__ import annotations

from engine.predicates.types import ParsedInput

def _extract_candidates(
    parsed: ParsedInput,
) -> list[tuple[int, str, str]]:
    """从 ParsedInput.known_facts + questions 提取候选事件。

    返回 [(year, candidate_event, domain), ...]

    domain 映射表（preflight type → engine domain）：
        职业 → 事业
        学历 → 学业
        子女/父母/亲属 → 六亲
        其余 保持不变
    """
    # preflight type → engine domain 映射；输出必须符合 D3 gate 支持的 Domain。
    _TYPE_TO_DOMAIN: dict[str, str] = {
        "职业": "事业",
        "学历": "学业",
        "子女": "六亲",
        "父母": "六亲",
        "亲属": "六亲",
        "兄弟": "六亲",
        "姐妹": "六亲",
        "兄弟姐妹": "六亲",
    }

    candidates: list[tuple[int, str, str]] = []

    # 从 known_facts 提取
    for fact in (parsed.known_facts or []):
        raw_type = fact.type or "其他"
        domain = _TYPE_TO_DOMAIN.get(raw_type, raw_type)
        if fact.year and fact.event:
            candidates.append((fact.year, fact.event, domain))
        elif fact.year and fact.content:
            candidates.append((fact.year, fact.content, domain))

    return candidates
