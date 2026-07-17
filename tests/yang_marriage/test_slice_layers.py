from __future__ import annotations

from dataclasses import replace

import pytest

from engine.decision.models import SchoolApplicability
from engine.decision.yang_marriage_slice import apply_yang_marriage_slice
from engine.v5.domain import V5Claim, V5Confidence, V5Evidence, V5Output
from tests.yang_marriage.fixtures import cfv, chart


_TARGET_TASK = "marriage.divorce_or_remarriage"


def _applicability() -> list[SchoolApplicability]:
    return [
        SchoolApplicability(
            school="yang_qingjuan",
            role="lead",
            applicable_domains=["婚姻"],
        ),
        SchoolApplicability(
            school="ziping",
            role="co_lead",
            applicable_domains=["事业"],
        ),
    ]


def _output(case_id: str) -> V5Output:
    return V5Output(
        case_id=case_id,
        claims=[
            V5Claim(
                claim_id="legacy-yang-marriage-target",
                school="yang_qingjuan",
                domain="婚姻",
                claim="旧目标旁路。",
                claim_type="event_claim",
                confidence=V5Confidence(score=0.60),
                evidence=[V5Evidence("old-target", "synthetic", "旧目标证据")],
                metadata={"task_id": _TARGET_TASK},
            ),
            V5Claim(
                claim_id="legacy-nontarget-career",
                school="ziping",
                domain="事业",
                claim="合成非目标事业事件。",
                claim_type="event_claim",
                confidence=V5Confidence(score=0.60),
                evidence=[V5Evidence("career", "synthetic", "非目标证据")],
                metadata={"task_id": "career.role_change"},
            ),
        ],
    )


def _male_counts(*, wealth: int, peers: int) -> dict[str, int]:
    return {
        "正财": wealth,
        "偏财": 0,
        "正官": 0,
        "七杀": 0,
        "比肩": peers,
        "劫财": 0,
        "食神": 0,
        "伤官": 0,
    }


def test_event_replaces_old_target_and_directly_builds_l2_through_l6() -> None:
    case_id = "YM-SYN-M1"
    result, claims, verdicts, events, timings, decisions = apply_yang_marriage_slice(
        _output(case_id),
        chart(case_id),
        cfv(
            case_id,
            chong_pairs=(("子", "午"),),
            ten_god_counts=_male_counts(wealth=1, peers=3),
        ),
        _applicability(),
    )

    target_claims = [claim for claim in claims if claim.metadata.get("task_id") == _TARGET_TASK]
    assert result.state == "event"
    assert len(target_claims) == 1
    assert target_claims[0].claim_id != "legacy-yang-marriage-target"
    assert len(claims) == 2
    assert len(verdicts) == 2
    assert len(events) == 2
    assert len(timings) == 2
    assert len(decisions) == 2


def test_pressure_strips_old_target_and_never_enters_l2_through_l6() -> None:
    case_id = "YM-SYN-P1"
    result, claims, verdicts, events, timings, decisions = apply_yang_marriage_slice(
        _output(case_id),
        chart(case_id),
        cfv(
            case_id,
            chong_pairs=(("子", "午"),),
            ten_god_counts=_male_counts(wealth=2, peers=0),
        ),
        _applicability(),
    )

    assert result.state == "pressure"
    assert [claim.claim_id for claim in claims] == ["legacy-nontarget-career"]
    assert len(verdicts) == len(events) == len(timings) == len(decisions) == 1
    assert all(item.domain != "婚姻" for item in events)
    assert all(item.domain != "婚姻" for item in decisions)


def test_duplicate_yang_applicability_fails_fast() -> None:
    applicability = _applicability()
    duplicate = replace(applicability[0], role="co_lead")

    with pytest.raises(ValueError, match="duplicate yang_qingjuan applicability"):
        apply_yang_marriage_slice(
            _output("YM-SYN-DUP-ROLE"),
            chart("YM-SYN-DUP-ROLE"),
            cfv("YM-SYN-DUP-ROLE"),
            applicability + [duplicate],
        )
