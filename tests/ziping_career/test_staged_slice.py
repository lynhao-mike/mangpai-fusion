from dataclasses import replace

import pytest

from engine.decision.ziping_career_structure import (
    PublicationState,
    discriminate_ziping_career_structure,
)
from engine.decision.ziping_career_structure_slice import (
    build_ziping_career_structure_slice,
    to_ziping_career_school_claim,
    to_ziping_career_structural_verdict,
)


GEJU_PROFILE = {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []}


def _emit_result(chart, supported_features):
    return discriminate_ziping_career_structure(chart, supported_features, GEJU_PROFILE)


def test_emit_builds_one_structure_claim_and_one_l3_pass(
    chart, supported_features
) -> None:
    run = build_ziping_career_structure_slice(
        "C-ZIPING-CAREER-001",
        chart,
        supported_features,
        GEJU_PROFILE,
        role="lead",
    )

    assert run.result.publication_state is PublicationState.EMIT
    assert len(run.claims) == 1
    assert len(run.verdicts) == 1
    assert run.claims[0].claim_type == "structure_claim"
    assert run.verdicts[0].verdict == "pass"
    assert "time_window" not in run.claims[0].metadata
    assert run.events == ()
    assert run.timings == ()


def test_first_falsifier_produces_zero_l2_and_zero_l3(
    chart, coarse_trigger_without_output_features
) -> None:
    run = build_ziping_career_structure_slice(
        "C-ZIPING-CAREER-FALSIFIER",
        chart,
        coarse_trigger_without_output_features,
        GEJU_PROFILE,
        role="lead",
    )

    assert run.result.coarse_trigger_observed is True
    assert run.result.publication_state is PublicationState.HOLD
    assert run.claims == ()
    assert run.verdicts == ()
    assert run.events == ()
    assert run.timings == ()


@pytest.mark.parametrize(
    "fixture_name", ["coarse_trigger_without_output_features", "protected_features"]
)
def test_non_emit_fails_closed_in_l2_adapter(
    request, chart, fixture_name: str
) -> None:
    features = request.getfixturevalue(fixture_name)
    result = discriminate_ziping_career_structure(
        chart,
        features,
        {
            "geju_type": "正格",
            "favor_shishen": ["正官", "正印"],
            "avoid_shishen": ["伤官"],
        },
    )

    with pytest.raises(ValueError, match="emit publication state required"):
        to_ziping_career_school_claim(result, "lead", features.chart_id)


def test_l2_rejects_abstain_role(chart, supported_features) -> None:
    result = _emit_result(chart, supported_features)

    with pytest.raises(ValueError, match="non-abstain L1 role required"):
        to_ziping_career_school_claim(result, "abstain", supported_features.chart_id)


def test_l3_rejects_wrong_task_rule_identity(chart, supported_features) -> None:
    result = _emit_result(chart, supported_features)
    claim = to_ziping_career_school_claim(result, "lead", supported_features.chart_id)

    with pytest.raises(ValueError, match="task rule identity"):
        to_ziping_career_structural_verdict(
            "C-ZIPING-CAREER-001",
            result,
            replace(claim, metadata={**claim.metadata, "task_rule_id": "WRONG"}),
        )


def test_l3_rejects_tampered_mapping_digest(chart, supported_features) -> None:
    result = _emit_result(chart, supported_features)
    claim = to_ziping_career_school_claim(result, "lead", supported_features.chart_id)

    with pytest.raises(ValueError, match="mapping digest"):
        to_ziping_career_structural_verdict(
            "C-ZIPING-CAREER-001",
            result,
            replace(claim, metadata={**claim.metadata, "mapping_digest": "tampered"}),
        )


def test_l3_rejects_missing_required_family(chart, supported_features) -> None:
    result = _emit_result(chart, supported_features)
    claim = to_ziping_career_school_claim(result, "lead", supported_features.chart_id)
    family_keys = [
        key for key in claim.metadata["family_keys"] if key != "geju_direction"
    ]

    with pytest.raises(ValueError, match="required evidence families"):
        to_ziping_career_structural_verdict(
            "C-ZIPING-CAREER-001",
            result,
            replace(claim, metadata={**claim.metadata, "family_keys": family_keys}),
        )


def test_l3_rejects_duplicate_evidence_ref(chart, supported_features) -> None:
    result = _emit_result(chart, supported_features)
    claim = to_ziping_career_school_claim(result, "lead", supported_features.chart_id)

    with pytest.raises(ValueError, match="duplicate evidence ref"):
        to_ziping_career_structural_verdict(
            "C-ZIPING-CAREER-001",
            result,
            replace(claim, evidence_refs=[*claim.evidence_refs, claim.evidence_refs[0]]),
        )


def test_supported_rerun_has_stable_claim_and_verdict_ids(
    chart, supported_features
) -> None:
    first = build_ziping_career_structure_slice(
        "C-ZIPING-CAREER-STABLE",
        chart,
        supported_features,
        GEJU_PROFILE,
        role="lead",
    )
    second = build_ziping_career_structure_slice(
        "C-ZIPING-CAREER-STABLE",
        chart,
        supported_features,
        GEJU_PROFILE,
        role="lead",
    )

    assert first.claims[0].claim_id == second.claims[0].claim_id
    assert first.verdicts[0].verdict_id == second.verdicts[0].verdict_id
