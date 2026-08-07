"""应用层候选事件提取：把已知事实映射为应期候选。"""

from __future__ import annotations

from typing import Final

from engine.predicates.types import ParsedInput
from engine.yingqi.types import Domain


_FACT_TYPE_TO_DOMAIN: Final[dict[str, Domain]] = {
    "婚姻": "婚姻",
    "事业": "事业",
    "财运": "财运",
    "健康": "健康",
    "学业": "学业",
    "六亲": "六亲",
    "其他": "其他",
    "职业": "事业",
    "学历": "学业",
    "子女": "六亲",
    "父母": "六亲",
    "亲属": "六亲",
    "兄弟": "六亲",
    "姐妹": "六亲",
    "兄弟姐妹": "六亲",
    "灾厄": "健康",
    "牢狱": "其他",
    "出国": "其他",
}


def _normalize_fact_domain(raw_type: str | None) -> Domain:
    fact_type = (raw_type or "其他").strip()
    return _FACT_TYPE_TO_DOMAIN.get(fact_type, "其他")


def _extract_candidates(
    parsed: ParsedInput,
) -> list[tuple[int, str, Domain]]:
    candidates: list[tuple[int, str, Domain]] = []

    for fact in (parsed.known_facts or []):
        domain = _normalize_fact_domain(fact.type)
        if fact.year and fact.event:
            candidates.append((fact.year, fact.event, domain))
        elif fact.year and fact.content:
            candidates.append((fact.year, fact.content, domain))

    return candidates
