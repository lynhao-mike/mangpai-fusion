"""V2 事件映射测试。"""

from __future__ import annotations

from engine.v2.domain.agents import DomainReasoningResult
from engine.v2.domain.events import EventCandidate
from engine.v2.events import build_event_candidates, load_event_mapping


def _result() -> DomainReasoningResult:
    return DomainReasoningResult(
        case_id="C-test",
        domain="wealth",
        main_claims=["财运结构清晰"],
        risk_claims=["财务波动风险"],
        opportunity_claims=["适合把握资产机会"],
        evidence_ids=["ev-a", "ev-b"],
        confidence=0.73,
    )


def test_event_candidate_round_trip():
    event = EventCandidate(
        event_id="evt-1",
        case_id="C-test",
        domain="career",
        event_type="career_direction",
        title="事业主线候选",
        description="事业方向明确",
        source_claim="事业方向明确",
        evidence_ids=["ev-1"],
        confidence=0.8,
        polarity="positive",
        tags=["career"],
    )
    assert EventCandidate.from_dict(event.to_dict()) == event


def test_load_event_mapping_contains_default_domains():
    mapping = load_event_mapping()
    assert "career" in mapping
    assert "wealth" in mapping
    assert mapping["wealth"]["risk"]["event_type"] == "wealth_risk"


def test_build_event_candidates_maps_claim_types():
    events = build_event_candidates([_result()])
    assert len(events) == 3
    assert {event.event_type for event in events} == {"wealth_pattern", "wealth_risk", "wealth_opportunity"}
    assert {event.polarity for event in events} == {"positive", "negative"}


def test_build_event_candidates_preserves_evidence_ids_and_confidence():
    events = build_event_candidates([_result()])
    assert all(event.evidence_ids == ["ev-a", "ev-b"] for event in events)
    assert all(event.confidence == 0.73 for event in events)


def test_build_event_candidates_uses_fallback_for_unknown_domain():
    result = DomainReasoningResult(case_id="C-test", domain="unknown", main_claims=["未知领域命题"])
    events = build_event_candidates([result])
    assert len(events) == 1
    assert events[0].event_type == "unknown_main"
    assert events[0].polarity == "neutral"
