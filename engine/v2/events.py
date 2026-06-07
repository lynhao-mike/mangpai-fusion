"""V2 事件映射器。"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from engine.v2.domain.agents import DomainReasoningResult
from engine.v2.domain.events import EventCandidate

DEFAULT_EVENT_MAPPING_PATH = Path(__file__).resolve().parent / "mapping" / "event_mapping.yaml"


def build_event_candidates(
    domain_results: list[DomainReasoningResult],
    *,
    mapping_path: str | Path | None = None,
) -> list[EventCandidate]:
    """把领域 Agent 输出映射为结构化事件候选。"""
    mapping = load_event_mapping(mapping_path)
    candidates: list[EventCandidate] = []
    for result in domain_results:
        domain_mapping = mapping.get(result.domain, {})
        candidates.extend(_claims_to_candidates(result, "main", result.main_claims, domain_mapping.get("main", {})))
        candidates.extend(_claims_to_candidates(result, "risk", result.risk_claims, domain_mapping.get("risk", {})))
        candidates.extend(
            _claims_to_candidates(result, "opportunity", result.opportunity_claims, domain_mapping.get("opportunity", {}))
        )
    return candidates


def load_event_mapping(mapping_path: str | Path | None = None) -> dict[str, dict[str, dict[str, Any]]]:
    path = Path(mapping_path) if mapping_path is not None else DEFAULT_EVENT_MAPPING_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = data.get("mappings", {})
    return {str(domain): dict(config) for domain, config in raw.items()}


def _claims_to_candidates(
    result: DomainReasoningResult,
    claim_kind: str,
    claims: list[str],
    config: dict[str, Any],
) -> list[EventCandidate]:
    candidates: list[EventCandidate] = []
    for index, claim in enumerate(claims, start=1):
        event_type = str(config.get("event_type", f"{result.domain}_{claim_kind}"))
        title = str(config.get("title", event_type))
        polarity = str(config.get("polarity", _default_polarity(claim_kind)))
        tags = [str(x) for x in config.get("tags", [result.domain, claim_kind])]
        candidates.append(
            EventCandidate(
                event_id=_event_id(result.case_id, result.domain, claim_kind, index, claim),
                case_id=result.case_id,
                domain=result.domain,
                event_type=event_type,
                title=title,
                description=claim,
                source_claim=claim,
                evidence_ids=list(result.evidence_ids),
                confidence=result.confidence,
                polarity=polarity,
                tags=tags,
                metadata={"claim_kind": claim_kind, "claim_index": index},
            )
        )
    return candidates


def _default_polarity(claim_kind: str) -> str:
    if claim_kind == "risk":
        return "negative"
    if claim_kind == "opportunity":
        return "positive"
    return "neutral"


def _event_id(case_id: str, domain: str, claim_kind: str, index: int, claim: str) -> str:
    raw = "|".join([case_id, domain, claim_kind, str(index), claim])
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"v2evt-{digest}"
