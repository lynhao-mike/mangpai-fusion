import ast
from dataclasses import replace
from pathlib import Path

import pytest

from engine.decision.ziping_career_structure import (
    PublicationState,
    discriminate_ziping_career_structure,
)
from engine.decision.ziping_career_structure_slice import (
    FrozenZipingCareerSlice,
    build_ziping_career_structure_slice,
    freeze_ziping_career_slice,
    to_ziping_career_school_claim,
    to_ziping_career_structural_verdict,
    verify_frozen_ziping_career_slice,
)
from engine.evaluation.freeze import canonical_json


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


def test_supported_slice_freezes_byte_stably(chart, supported_features) -> None:
    kwargs = {
        "case_id": "C-ZIPING-FREEZE",
        "chart": chart,
        "features": supported_features,
        "geju_profile": GEJU_PROFILE,
        "role": "lead",
    }
    first = freeze_ziping_career_slice(build_ziping_career_structure_slice(**kwargs))
    second = freeze_ziping_career_slice(build_ziping_career_structure_slice(**kwargs))

    assert isinstance(first, FrozenZipingCareerSlice)
    verify_frozen_ziping_career_slice(first)
    verify_frozen_ziping_career_slice(second)
    assert first.freeze_hash == second.freeze_hash
    assert canonical_json(first.to_dict()).encode("utf-8") == canonical_json(
        second.to_dict()
    ).encode("utf-8")
    assert first.events == ()
    assert first.timings == ()


def test_feature_and_profile_order_permutation_keeps_freeze_hash(
    chart, supported_features
) -> None:
    left = build_ziping_career_structure_slice(
        "C-ZIPING-PERMUTE",
        chart,
        supported_features,
        {
            "geju_type": "正格",
            "favor_shishen": ["正官", "正印"],
            "avoid_shishen": [],
        },
        role="lead",
    )
    reordered = replace(
        supported_features,
        ten_god_counts=dict(reversed(list(supported_features.ten_god_counts.items()))),
    )
    right = build_ziping_career_structure_slice(
        "C-ZIPING-PERMUTE",
        chart,
        reordered,
        {
            "avoid_shishen": [],
            "favor_shishen": ["正印", "正官"],
            "geju_type": "正格",
        },
        role="lead",
    )

    assert freeze_ziping_career_slice(left).freeze_hash == freeze_ziping_career_slice(
        right
    ).freeze_hash


def test_first_falsifier_freezes_zero_l2_l3_and_zero_timing(
    chart, coarse_trigger_without_output_features
) -> None:
    frozen = freeze_ziping_career_slice(
        build_ziping_career_structure_slice(
            "C-ZIPING-FALSIFIER-FROZEN",
            chart,
            coarse_trigger_without_output_features,
            GEJU_PROFILE,
            role="lead",
        )
    )

    assert frozen.claims == ()
    assert frozen.verdicts == ()
    assert frozen.events == ()
    assert frozen.timings == ()


def test_frozen_slice_rejects_hash_mismatch(chart, supported_features) -> None:
    frozen = freeze_ziping_career_slice(
        build_ziping_career_structure_slice(
            "C-ZIPING-TAMPER",
            chart,
            supported_features,
            GEJU_PROFILE,
            role="lead",
        )
    )

    with pytest.raises(ValueError, match="freeze hash mismatch"):
        verify_frozen_ziping_career_slice(replace(frozen, case_id="C-TAMPERED"))


def test_slice_source_is_statically_truncated_at_l3() -> None:
    source_path = Path("engine/decision/ziping_career_structure_slice.py")
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_modules.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )

    forbidden_modules = {"l4_events", "l5_timing", "ren_career_timing", "render_report"}
    assert not any(
        any(part == forbidden for part in module.split("."))
        for module in imported_modules
        for forbidden in forbidden_modules
    )
    for forbidden_call in (
        "TimeWindow(",
        "TimingProbability(",
        "build_timing_probabilities(",
    ):
        assert forbidden_call not in source
