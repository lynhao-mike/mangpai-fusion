"""V2 Evidence Builder。

负责将多流派 SchoolEvidence 归一化为 DomainEvidence。
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from engine.v2.domain.evidence import DomainEvidence, SchoolEvidence


def build_domain_evidences(evidences: Iterable[SchoolEvidence]) -> list[DomainEvidence]:
    """将 SchoolEvidence 按领域归并为 DomainEvidence。"""

    deduped = _dedupe_evidences(evidences)
    grouped: dict[str, list[SchoolEvidence]] = defaultdict(list)
    case_id = ""
    for item in deduped:
        case_id = case_id or item.case_id
        grouped[item.domain or "general"].append(item)

    results: list[DomainEvidence] = []
    for domain in sorted(grouped):
        rows = grouped[domain]
        coverage: dict[str, int] = defaultdict(int)
        support_score = 0.0
        conflict_score = 0.0
        for item in rows:
            coverage[item.source_school] += 1
            if item.polarity == "negative":
                conflict_score += item.confidence
            else:
                support_score += item.confidence
        total = max(1, len(rows))
        normalized = round((support_score / total) * min(1.0, 0.5 + len(coverage) / 10), 4)
        results.append(
            DomainEvidence(
                case_id=case_id,
                domain=domain,
                evidences=rows,
                support_score=round(support_score, 4),
                conflict_score=round(conflict_score, 4),
                coverage=dict(sorted(coverage.items())),
                normalized_confidence=normalized,
            )
        )
    return results


def _dedupe_evidences(evidences: Iterable[SchoolEvidence]) -> list[SchoolEvidence]:
    seen: set[str] = set()
    output: list[SchoolEvidence] = []
    for item in evidences:
        key = item.evidence_id
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output
