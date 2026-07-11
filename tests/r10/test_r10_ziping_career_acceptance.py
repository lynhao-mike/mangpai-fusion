from __future__ import annotations

import json
import re
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from engine.decision import v5_adapter
from engine.decision.l1_school_router import route_schools
from engine.decision.l4_events import build_event_hypotheses
from engine.decision.models import (
    ChartFactLedger,
    ContextFactLedger,
    SchoolApplicability,
    SchoolClaim,
)
from engine.decision.r10_ziping_career import (
    apply_ziping_career_slice,
    build_ziping_career_decision_run,
)
from engine.v5.domain import V5Claim, V5Confidence, V5Output
from engine.v5.runner import run_v5

BASELINE_PATH = Path("tests/r10/fixtures/r6_ziping_career_baseline.json")
TARGET_DOMAINS = {"总体", "事业"}
CHART = {
    "case_id": "C-R10-ZIPING",
    "pillars": {"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
    "current_dayun": "壬午",
    "current_year": "丙午（2026 年）",
}


def load_r6_baseline() -> dict[str, object]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _run_formal_case():
    from engine.v5.preprod import build_chart_from_input

    input_path = Path("cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md")
    chart = build_chart_from_input(input_path)
    output = run_v5(chart, case_id=str(chart["case_id"]), workspace_root=".")
    return output, build_ziping_career_decision_run(
        output,
        raw_text=input_path.read_text(encoding="utf-8"),
    )


def test_r6_baseline_is_frozen_and_nonempty() -> None:
    baseline = load_r6_baseline()
    assert baseline["case_id"] == "C-2026-035-乾-戊辰癸亥甲戌庚午"
    assert int(baseline["career_claim_count"]) == 270
    assert int(baseline["career_school_count"]) == 5
    assert int(baseline["career_evidence_count"]) == 270
    assert int(baseline["career_fifteen_layer_count"]) == 15
    assert baseline["required_text_sentinels"] == ["事业", "依据", "置信度", "应期"]


def test_r6_frozen_gate_rejects_degraded_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    degraded_path = tmp_path / "r6_ziping_career_baseline.json"
    degraded_path.write_text(
        json.dumps(
            {
                "case_id": "C-2026-035-乾-戊辰癸亥甲戌庚午",
                "career_claim_count": 1,
                "career_school_count": 1,
                "career_evidence_count": 1,
                "career_fifteen_layer_count": 15,
                "required_text_sentinels": ["x"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(sys.modules[__name__], "BASELINE_PATH", degraded_path)

    with pytest.raises(AssertionError):
        test_r6_baseline_is_frozen_and_nonempty()


def test_falsifier_l2_keeps_real_runner_wangshuai_yongshen_and_source_metadata() -> None:
    output, run = _run_formal_case()
    source_claims = [
        item
        for item in output.claims
        if item.school == "ziping" and item.domain in TARGET_DOMAINS
    ]
    ziping_claims = [
        item
        for item in run.school_claims
        if item.school == "ziping" and item.domain in TARGET_DOMAINS
    ]

    independent_claims = [
        item
        for item in ziping_claims
        if item.metadata.get("source_scope") == "ziping_independent_runner"
    ]
    assert independent_claims
    assert any("旺衰" in item.statement for item in independent_claims)
    assert any("用神=" in item.statement for item in independent_claims)
    assert any(item.metadata.get("geju_type") for item in ziping_claims)
    assert any("yao_favor_shishen" in item.metadata for item in ziping_claims)
    by_source_id = {item.claim_id: item for item in source_claims}
    for item in ziping_claims:
        source = by_source_id[item.claim_id]
        assert item.evidence_refs == [evidence.evidence_id for evidence in source.evidence]
        assert item.confidence == source.confidence.score
        assert item.falsifier == source.falsifiable
        assert {
            key: value for key, value in item.metadata.items() if key != "v5_payload"
        } == source.metadata
        assert item.metadata["v5_payload"] == {
            "stance": source.stance,
            "polarity": source.polarity,
            "counter_evidence": [value.to_dict() for value in source.counter_evidence],
            "timing_hints": source.timing_hints,
            "probabilistic": source.probabilistic,
        }


def test_falsifier_career_information_is_not_thinner_than_r6() -> None:
    baseline = load_r6_baseline()
    _, run = _run_formal_case()
    claims = [item for item in run.school_claims if item.domain in TARGET_DOMAINS]
    assert len(claims) >= int(baseline["career_claim_count"])
    assert len({item.school for item in claims}) >= int(baseline["career_school_count"])
    assert sum(len(item.evidence_refs) for item in claims) >= int(
        baseline["career_evidence_count"]
    )


def test_falsifier_report_keeps_all_fifteen_judgment_layers(tmp_path: Path) -> None:
    from engine.v5.preprod import render_v6_preprod_case

    baseline = load_r6_baseline()
    report_path, _ = render_v6_preprod_case(
        "cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md",
        reports_dir=tmp_path,
        workspace_root=".",
    )
    report_text = Path(report_path).read_text(encoding="utf-8")
    template_text = Path("templates/report-v6.md").read_text(encoding="utf-8")
    row_pattern = re.compile(r"^\|\s*(\d{1,2})\s*\|", re.MULTILINE)
    template_layers = [int(value) for value in row_pattern.findall(template_text)]
    report_layers = [int(value) for value in row_pattern.findall(report_text)]

    assert template_layers == list(range(1, 16))
    assert report_layers == template_layers
    assert len(report_layers) == int(baseline["career_fifteen_layer_count"])
    for sentinel in baseline["required_text_sentinels"]:
        assert str(sentinel) in report_text


def test_ziping_career_decision_run_has_complete_trace() -> None:
    output = run_v5(CHART, case_id="C-R10-ZIPING")
    run = build_ziping_career_decision_run(output)

    assert run.validate_trace() == []
    assert any(item.domain == "事业" for item in run.school_claims)
    decision_by_id = {item.decision_id: item for item in run.arbitration_decisions}
    assert any(decision_by_id[item.decision_id].domain == "事业" for item in run.report_items)


def test_career_l7_text_is_serialized_verbatim() -> None:
    output = run_v5(CHART, case_id="C-R10-ZIPING")
    run = build_ziping_career_decision_run(output)
    serialized = run.to_dict()
    decision_by_id = {item.decision_id: item.domain for item in run.arbitration_decisions}
    career_items = [
        item for item in run.report_items
        if decision_by_id[item.decision_id] == "事业"
    ]
    serialized_items = {
        item["report_item_id"]: item["display_text"]
        for item in serialized["report_items"]
    }

    assert career_items
    for item in career_items:
        assert serialized_items[item.report_item_id] == item.display_text


def test_preprod_builds_r10_run_from_exact_input_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from engine.v5 import preprod

    input_path = Path("cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md")
    input_text = input_path.read_text(encoding="utf-8")
    calls: list[str] = []
    real_builder = build_ziping_career_decision_run

    def recording_builder(output: V5Output, raw_text: str = ""):
        calls.append(raw_text)
        return real_builder(output, raw_text=raw_text)

    monkeypatch.setattr(preprod, "build_ziping_career_decision_run", recording_builder)
    preprod.render_v6_preprod_case(input_path, reports_dir=tmp_path, workspace_root=".")

    assert calls == [input_text]


def test_ziping_career_slice_never_sends_target_claims_to_adapter() -> None:
    output = run_v5(CHART, case_id="C-R10-ZIPING")
    ledger = ChartFactLedger(
        four_pillars=CHART["pillars"],
        dayun_steps=[{"ganzhi": "壬午"}],
    )
    applicability = route_schools(
        ledger,
        ContextFactLedger(analysis_focus_text="事业"),
    )

    with (
        patch("engine.decision.v5_adapter._claims", wraps=v5_adapter._claims) as legacy_claims,
        patch(
            "engine.decision.v5_adapter._verdicts",
            side_effect=AssertionError("slice must call L3 directly"),
        ),
        patch(
            "engine.decision.v5_adapter._events",
            side_effect=AssertionError("slice must call L4 directly"),
        ),
    ):
        claims, verdicts, events = apply_ziping_career_slice(output, applicability)

    legacy_claims.assert_called_once()
    legacy_output = legacy_claims.call_args.args[0]
    assert not any(
        claim.school == "ziping" and claim.domain in TARGET_DOMAINS
        for claim in legacy_output.claims
    )

    role = next(item.role for item in applicability if item.school == "ziping")
    native_ids = {
        claim.claim_id
        for claim in output.claims
        if claim.school == "ziping" and claim.domain in TARGET_DOMAINS
    }
    native_l2 = [claim for claim in claims if claim.claim_id in native_ids]
    assert native_l2
    assert {claim.claim_id for claim in native_l2} == native_ids
    assert {claim.role_granted_by_l1 for claim in native_l2} == {role}

    non_target_ids = {
        claim.claim_id
        for claim in output.claims
        if not (claim.school == "ziping" and claim.domain in TARGET_DOMAINS)
        and claim.claim_id
        and claim.school
        and claim.domain
        and next(
            (item.role for item in applicability if item.school == claim.school),
            "co_lead",
        )
        != "abstain"
    }
    assert non_target_ids <= {claim.claim_id for claim in claims}
    assert {verdict.claim_id for verdict in verdicts} == {
        claim.claim_id for claim in claims
    }

    eligible_event_claim_ids = {
        claim.claim_id
        for claim in claims
        if claim.claim_type in {"event", "event_claim"}
        and claim.role_granted_by_l1 != "evidence_only"
        and next(
            verdict.verdict
            for verdict in verdicts
            if verdict.claim_id == claim.claim_id
        )
        in {"pass", "weaken"}
    }
    event_claim_ids = {
        verdict.claim_id
        for event in events
        for verdict in verdicts
        if verdict.verdict_id in event.source_verdict_ids
    }
    assert event_claim_ids <= eligible_event_claim_ids
    assert events == build_event_hypotheses(output.case_id, verdicts, claims)
    assert {claim.domain for claim in claims} >= {
        claim.domain
        for claim in output.claims
        if claim.claim_id in non_target_ids
    }


def _v5_claim(
    claim_id: str,
    school: str,
    domain: str,
    statement: str,
) -> V5Claim:
    return V5Claim(
        claim_id=claim_id,
        school=school,  # type: ignore[arg-type]
        domain=domain,
        claim=statement,
        claim_type="event_claim",
        confidence=V5Confidence(score=0.7),
    )


def _applicability(school: str, role: str = "co_lead") -> SchoolApplicability:
    return SchoolApplicability(school=school, role=role)  # type: ignore[arg-type]


def _legacy_claim(claim_id: str, school: str, domain: str) -> SchoolClaim:
    return SchoolClaim(
        claim_id=claim_id,
        school=school,
        role_granted_by_l1="co_lead",
        domain=domain,
        claim_type="event_claim",
        statement=f"legacy:{claim_id}",
    )


@pytest.mark.parametrize(
    "applicability",
    [
        [_applicability("ziping", "lead"), _applicability("ziping", "co_lead")],
        [_applicability("ziping", "co_lead"), _applicability("ziping", "lead")],
    ],
)
def test_slice_rejects_duplicate_ziping_applicability_in_any_order(
    applicability: list[SchoolApplicability],
) -> None:
    output = V5Output(
        case_id="duplicate-applicability",
        claims=[
            _v5_claim("other", "ditiansui", "事业", "非目标"),
            _v5_claim("target", "ziping", "事业", "目标"),
        ],
    )

    with pytest.raises(ValueError, match="duplicate ziping applicability"):
        apply_ziping_career_slice(output, applicability)


@pytest.mark.parametrize("ziping_role", [None, "abstain"])
def test_missing_or_abstain_ziping_only_suppresses_targets(
    ziping_role: str | None,
) -> None:
    target = _v5_claim("target", "ziping", "事业", "目标")
    other = _v5_claim("other", "ditiansui", "事业", "非目标")
    output = V5Output(case_id="suppression", claims=[target, other])
    applicability = [_applicability("ditiansui")]
    if ziping_role is not None:
        applicability.append(_applicability("ziping", ziping_role))
    preserved = _legacy_claim("other", "ditiansui", "事业")

    with patch("engine.decision.v5_adapter._claims", return_value=[preserved]) as adapter:
        claims, verdicts, _ = apply_ziping_career_slice(output, applicability)

    assert claims == [preserved]
    assert [verdict.claim_id for verdict in verdicts] == ["other"]
    assert adapter.call_args.args[0].claims == [other]
    assert adapter.call_args.args[1] is applicability


@pytest.mark.parametrize(
    "claims",
    [
        [
            _v5_claim("same-id", "ditiansui", "事业", "非目标"),
            _v5_claim("same-id", "ziping", "事业", "目标"),
        ],
        [
            _v5_claim("same-id", "ziping", "事业", "完全重复"),
            _v5_claim("same-id", "ziping", "事业", "完全重复"),
        ],
        [
            _v5_claim("same-id", "ziping", "总体", "内容甲"),
            _v5_claim("same-id", "ziping", "事业", "内容乙"),
        ],
    ],
)
def test_slice_rejects_duplicate_merged_l2_claim_ids_with_id_in_error(
    claims: list[V5Claim],
) -> None:
    output = V5Output(case_id="duplicate-l2", claims=claims)
    applicability = [_applicability("ziping", "lead"), _applicability("ditiansui")]

    with pytest.raises(ValueError, match="same-id"):
        apply_ziping_career_slice(output, applicability)


def test_slice_filters_legacy_by_position_and_preserves_adapter_contract_and_results() -> None:
    other_school = _v5_claim("other-school", "ditiansui", "事业", "其他派")
    target_a = _v5_claim("target-a", "ziping", "事业", "目标甲")
    ziping_wealth = _v5_claim("ziping-wealth", "ziping", "财富", "子平财富")
    target_b = _v5_claim("target-b", "ziping", "总体", "目标乙")
    output = V5Output(
        case_id="isolation",
        chart={"marker": object()},
        claims=[other_school, target_a, ziping_wealth, target_b],
        structure_graph=V5Output(case_id="graph-sentinel").structure_graph,
        arbitration_results=[],
        prediction_ledger=V5Output(case_id="ledger-sentinel").prediction_ledger,
        learning_signals=[],
        schema_version="test-schema",
    )
    applicability = [_applicability("ziping", "lead"), _applicability("ditiansui")]
    legacy_a = _legacy_claim("other-school", "ditiansui", "事业")
    legacy_b = _legacy_claim("ziping-wealth", "ziping", "财富")
    adapter_result = [legacy_a, legacy_b]

    with patch("engine.decision.v5_adapter._claims", return_value=adapter_result) as adapter:
        claims, verdicts, events = apply_ziping_career_slice(output, applicability)

    adapter.assert_called_once()
    adapted_output, adapted_applicability = adapter.call_args.args
    assert adapted_output.claims == [other_school, ziping_wealth]
    assert adapted_applicability is applicability
    assert replace(adapted_output, claims=output.claims) == output
    assert claims[:2] == adapter_result
    assert claims[0] is legacy_a
    assert claims[1] is legacy_b
    assert [claim.claim_id for claim in claims] == [
        "other-school",
        "ziping-wealth",
        "target-a",
        "target-b",
    ]
    assert len(claims) == len(verdicts)
    assert len({claim.claim_id for claim in claims}) == len(claims)
    assert len({verdict.verdict_id for verdict in verdicts}) == len(verdicts)
    assert [verdict.claim_id for verdict in verdicts] == [claim.claim_id for claim in claims]
    assert events == build_event_hypotheses(output.case_id, verdicts, claims)


def test_equal_but_distinct_target_objects_are_not_removed_by_equality_side_effects() -> None:
    target = _v5_claim("duplicate-target", "ziping", "事业", "相同目标")
    equal_distinct_target = replace(target)
    assert equal_distinct_target == target
    assert equal_distinct_target is not target
    output = V5Output(case_id="equal-distinct", claims=[target, equal_distinct_target])

    with pytest.raises(ValueError, match="duplicate-target"):
        apply_ziping_career_slice(output, [_applicability("ziping", "lead")])


def test_same_id_with_different_content_is_rejected_before_l3() -> None:
    output = V5Output(
        case_id="same-id-different-content",
        claims=[
            _v5_claim("collision", "ziping", "事业", "目标内容"),
            _v5_claim("collision", "ditiansui", "财富", "不同内容"),
        ],
    )

    with pytest.raises(ValueError, match="collision"):
        apply_ziping_career_slice(
            output,
            [_applicability("ziping", "lead"), _applicability("ditiansui")],
        )
