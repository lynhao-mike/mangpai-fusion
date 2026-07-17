from __future__ import annotations

from dataclasses import replace
import json

import pytest

from engine.decision import v5_adapter
from engine.decision.l3_structure import build_structural_verdicts
from engine.decision.l4_events import build_event_hypotheses
from engine.decision.l5_timing import build_timing_probabilities
from engine.decision.l6_arbitration import build_arbitration_decisions
from engine.decision.models import SchoolApplicability
from engine.decision.yang_marriage_slice import (
    apply_yang_marriage_slice,
    build_yang_marriage_slice_decision_run,
)
from engine.v5.domain import V5Claim, V5Confidence, V5Evidence, V5Output
from tests.yang_marriage.fixtures import cfv, chart, slice_output, synthetic_cases


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


def _nontarget_event(claim_id: str, domain: str, task_id: str) -> V5Claim:
    return V5Claim(
        claim_id=claim_id,
        school="ziping",
        domain=domain,
        claim=f"合成非目标{domain}事件。",
        claim_type="event_claim",
        confidence=V5Confidence(score=0.60),
        evidence=[V5Evidence(claim_id, "synthetic", f"非目标{domain}证据")],
        metadata={"task_id": task_id},
    )


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


def test_event_preserves_legacy_l2_l5_and_arbitrates_complete_domains_once() -> None:
    case_id = "YM-SYN-MULTI-EVENT"
    applicability = _applicability()
    original = _output(case_id)
    output = replace(
        original,
        claims=[
            original.claims[0],
            _nontarget_event("legacy-nontarget-marriage", "婚姻", "marriage.other"),
            original.claims[1],
            _nontarget_event("legacy-nontarget-health", "健康", "health.check"),
            _nontarget_event("legacy-nontarget-wealth", "财富", "wealth.change"),
        ],
    )
    legacy_output = replace(
        output,
        claims=[claim for claim in output.claims if claim.metadata.get("task_id") != _TARGET_TASK],
    )
    baseline_claims = v5_adapter._claims(legacy_output, applicability)
    baseline_verdicts = build_structural_verdicts(case_id, baseline_claims)
    baseline_events = build_event_hypotheses(case_id, baseline_verdicts, baseline_claims)
    baseline_timings = build_timing_probabilities(case_id, baseline_events)
    baseline_decisions = build_arbitration_decisions(case_id, baseline_events, applicability)

    result, claims, verdicts, events, timings, decisions = apply_yang_marriage_slice(
        output,
        chart(case_id),
        cfv(
            case_id,
            chong_pairs=(("子", "午"),),
            ten_god_counts=_male_counts(wealth=1, peers=3),
        ),
        applicability,
    )

    baseline_ids = {
        "claims": {item.claim_id for item in baseline_claims},
        "verdicts": {item.verdict_id for item in baseline_verdicts},
        "events": {item.event_id for item in baseline_events},
        "timings": {item.prediction_id for item in baseline_timings},
    }
    actual_legacy = [
        [item for item in claims if item.claim_id in baseline_ids["claims"]],
        [item for item in verdicts if item.verdict_id in baseline_ids["verdicts"]],
        [item for item in events if item.event_id in baseline_ids["events"]],
        [item for item in timings if item.prediction_id in baseline_ids["timings"]],
    ]
    for actual, baseline in zip(
        actual_legacy,
        [baseline_claims, baseline_verdicts, baseline_events, baseline_timings],
        strict=True,
    ):
        assert [item.to_dict() for item in actual] == [item.to_dict() for item in baseline]

    assert result.state == "event"
    target_claims = [claim for claim in claims if claim.metadata.get("task_id") == _TARGET_TASK]
    assert len(target_claims) == 1
    target_verdicts = [verdict for verdict in verdicts if verdict.claim_id == target_claims[0].claim_id]
    assert len(target_verdicts) == 1
    target_events = [event for event in events if target_verdicts[0].verdict_id in event.source_verdict_ids]
    assert len(target_events) == 1
    target_timings = [timing for timing in timings if timing.event_id == target_events[0].event_id]
    assert len(target_timings) == 1
    assert len({item.claim_id for item in claims}) == len(claims)
    assert len({item.verdict_id for item in verdicts}) == len(verdicts)
    assert len({item.event_id for item in events}) == len(events)
    assert len({item.prediction_id for item in timings}) == len(timings)

    assert len({decision.domain for decision in decisions}) == len(decisions)
    marriage_decisions = [decision for decision in decisions if decision.domain == "婚姻"]
    assert len(marriage_decisions) == 1
    legacy_marriage_event_ids = {
        event.event_id for event in baseline_events if event.domain == "婚姻"
    }
    assert legacy_marriage_event_ids
    assert set(marriage_decisions[0].competing_event_ids) == (
        legacy_marriage_event_ids | {target_events[0].event_id}
    )
    expected_decisions = build_arbitration_decisions(case_id, events, applicability)
    assert [item.to_dict() for item in decisions] == [
        item.to_dict() for item in expected_decisions
    ]
    assert [item.to_dict() for item in decisions] != [
        item.to_dict() for item in baseline_decisions
    ]


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


def target_counts(run) -> tuple[int, int, int, int, int]:
    claim_ids = {
        claim.claim_id for claim in run.school_claims
        if claim.metadata.get("task_id") == _TARGET_TASK
    }
    verdict_ids = {
        verdict.verdict_id for verdict in run.structural_verdicts
        if verdict.claim_id in claim_ids
    }
    event_ids = {
        event.event_id for event in run.event_hypotheses
        if set(event.source_verdict_ids) & verdict_ids
    }
    return (
        len(claim_ids),
        len(verdict_ids),
        len(event_ids),
        sum(timing.event_id in event_ids for timing in run.timing_probabilities),
        sum(
            bool(set(decision.competing_event_ids) & event_ids)
            for decision in run.arbitration_decisions
        ),
    )


def _target_serialization(run) -> str:
    target_claim_ids = {
        claim.claim_id for claim in run.school_claims
        if claim.metadata.get("task_id") == _TARGET_TASK
    }
    target_verdict_ids = {
        verdict.verdict_id for verdict in run.structural_verdicts
        if verdict.claim_id in target_claim_ids
    }
    target_event_ids = {
        event.event_id for event in run.event_hypotheses
        if set(event.source_verdict_ids) & target_verdict_ids
    }
    objects = [
        *[item.to_dict() for item in run.school_claims if item.claim_id in target_claim_ids],
        *[item.to_dict() for item in run.structural_verdicts if item.verdict_id in target_verdict_ids],
        *[item.to_dict() for item in run.event_hypotheses if item.event_id in target_event_ids],
        *[item.to_dict() for item in run.timing_probabilities if item.event_id in target_event_ids],
        *[item.to_dict() for item in run.arbitration_decisions
          if set(item.competing_event_ids) & target_event_ids],
    ]
    return json.dumps(objects, ensure_ascii=False, sort_keys=True)


@pytest.mark.parametrize("case_id", ["YM-SYN-M1", "YM-SYN-F1", "YM-SYN-F2"])
def test_event_has_exact_complete_l2_l6_trace(case_id: str) -> None:
    sample = next(item for item in synthetic_cases() if item.case_id == case_id)
    result, run = build_yang_marriage_slice_decision_run(
        slice_output(case_id), sample.chart, sample.features
    )

    assert result.state == "event"
    assert target_counts(run) == (1, 1, 1, 1, 1)
    assert run.validate_trace() == []
    assert run.report_items == []
    assert run.feedback_signals == []
    assert run.feedback_attributions == []
    assert run.calibration_actions == []


@pytest.mark.parametrize(
    "sample",
    [item for item in synthetic_cases() if item.expected_state != "event"],
    ids=lambda item: item.case_id,
)
def test_pressure_and_abstain_have_zero_target_objects_in_every_layer(sample) -> None:
    result, run = build_yang_marriage_slice_decision_run(
        slice_output(sample.case_id), sample.chart, sample.features
    )

    assert result.state in {"pressure", "abstain"}
    assert target_counts(run) == (0, 0, 0, 0, 0)
    assert all(claim.claim_id != "legacy-yang-marriage-target" for claim in run.school_claims)
    public_text = json.dumps(run.to_dict(), ensure_ascii=False)
    assert "存在关系压力不等于离婚或再婚事件成立" not in public_text


def test_decision_run_is_deterministic_for_repeat_and_pair_permutation() -> None:
    sample = next(item for item in synthetic_cases() if item.case_id == "YM-SYN-R1")
    first_result, first_run = build_yang_marriage_slice_decision_run(
        slice_output(sample.case_id), sample.chart, sample.features
    )
    repeated_result, repeated_run = build_yang_marriage_slice_decision_run(
        slice_output(sample.case_id), sample.chart, sample.features
    )
    reversed_features = replace(
        sample.features,
        chong_pairs=tuple(
            tuple(reversed(pair)) for pair in reversed(sample.features.chong_pairs)
        ),
        xing_hai_pairs=tuple(
            tuple(reversed(pair)) for pair in reversed(sample.features.xing_hai_pairs)
        ),
    )
    permuted_result, permuted_run = build_yang_marriage_slice_decision_run(
        slice_output(sample.case_id), sample.chart, reversed_features
    )

    assert first_result.to_dict() == repeated_result.to_dict() == permuted_result.to_dict()
    assert first_run.to_dict() == repeated_run.to_dict() == permuted_run.to_dict()
    assert _target_serialization(first_run) == _target_serialization(permuted_run)


def test_old_target_presence_does_not_change_slice_run() -> None:
    sample = next(item for item in synthetic_cases() if item.case_id == "YM-SYN-M1")
    _, with_old = build_yang_marriage_slice_decision_run(
        slice_output(sample.case_id), sample.chart, sample.features
    )
    _, without_old = build_yang_marriage_slice_decision_run(
        slice_output(sample.case_id, include_old_target=False), sample.chart, sample.features
    )

    assert with_old.to_dict() == without_old.to_dict()
    assert "legacy-yang-marriage-target" not in json.dumps(
        with_old.to_dict(), ensure_ascii=False
    )


def test_decision_run_preserves_non_target_legacy_objects_field_for_field() -> None:
    sample = next(item for item in synthetic_cases() if item.case_id == "YM-SYN-M1")
    output = slice_output(sample.case_id, include_old_target=False)
    _, run = build_yang_marriage_slice_decision_run(output, sample.chart, sample.features)
    baseline_claims = v5_adapter._claims(output, run.school_applicability)
    baseline_verdicts = build_structural_verdicts(sample.case_id, baseline_claims)
    baseline_events = build_event_hypotheses(
        sample.case_id, baseline_verdicts, baseline_claims
    )
    baseline_timings = build_timing_probabilities(sample.case_id, baseline_events)
    baseline_decisions = build_arbitration_decisions(
        sample.case_id, baseline_events, run.school_applicability
    )
    baseline_layers = (
        baseline_claims, baseline_verdicts, baseline_events, baseline_timings,
        baseline_decisions,
    )
    run_layers = (
        run.school_claims, run.structural_verdicts, run.event_hypotheses,
        run.timing_probabilities, run.arbitration_decisions,
    )
    id_fields = ("claim_id", "verdict_id", "event_id", "prediction_id", "decision_id")
    for layer, expected, field in zip(run_layers, baseline_layers, id_fields, strict=True):
        expected_ids = {getattr(item, field) for item in expected}
        actual = [item for item in layer if getattr(item, field) in expected_ids]
        assert [item.to_dict() for item in actual] == [item.to_dict() for item in expected]


def test_decision_run_duplicate_non_target_claim_fails_before_l3() -> None:
    sample = next(item for item in synthetic_cases() if item.case_id == "YM-SYN-P1")
    output = slice_output(sample.case_id, include_old_target=False)
    duplicated = replace(output, claims=[*output.claims, output.claims[0]])

    with pytest.raises(ValueError, match="duplicate L2 claim_id"):
        build_yang_marriage_slice_decision_run(
            duplicated, sample.chart, sample.features
        )


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
