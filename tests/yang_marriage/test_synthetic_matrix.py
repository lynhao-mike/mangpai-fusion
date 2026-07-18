from __future__ import annotations

import json

import pytest

from engine.decision.yang_marriage import discriminate_yang_marriage
from engine.features.types import ChartFeatureVector
from tests.yang_marriage.fixtures import SyntheticMarriageCase, synthetic_cases


_CASE_IDS = (
    "YM-SYN-M1",
    "YM-SYN-F1",
    "YM-SYN-F2",
    "YM-SYN-S1",
    "YM-SYN-S2",
    "YM-SYN-P1",
    "YM-SYN-P2",
    "YM-SYN-P3",
    "YM-SYN-G1",
    "YM-SYN-G2",
    "YM-SYN-G3",
    "YM-SYN-I1",
    "YM-SYN-I2",
    "YM-SYN-I3",
    "YM-SYN-D1",
    "YM-SYN-D2",
    "YM-SYN-D3",
    "YM-SYN-D4",
    "YM-SYN-X1",
    "YM-SYN-R1",
)


def _sample(case_id: str) -> SyntheticMarriageCase:
    return next(item for item in synthetic_cases() if item.case_id == case_id)


def _family_keys(result: object) -> tuple[str, ...]:
    return tuple(item.family_key for item in result.families)  # type: ignore[attr-defined]


def _semantic_input(sample: SyntheticMarriageCase) -> str:
    chart_payload = sample.chart.to_dict()
    chart_payload.pop("raw_source_hash")
    feature_payload = sample.features.to_dict()
    feature_payload.pop("chart_id")
    return json.dumps(
        {"chart": chart_payload, "features": feature_payload},
        ensure_ascii=False,
        sort_keys=True,
    )


@pytest.mark.parametrize("sample", synthetic_cases(), ids=lambda item: item.case_id)
def test_synthetic_matrix_has_exact_state_and_families(
    sample: SyntheticMarriageCase,
) -> None:
    result = discriminate_yang_marriage(sample.case_id, sample.chart, sample.features)
    keys = _family_keys(result)

    assert result.state == sample.expected_state
    assert keys == sample.expected_families
    assert len(keys) == len(set(keys))
    assert (result.state == "event") is (
        result.event_anchor_passed
        and result.independent_spouse_interaction_passed
        and not result.blocking_reason_codes
    )


def test_matrix_has_exactly_twenty_unique_case_ids_and_independent_inputs() -> None:
    samples = synthetic_cases()

    assert tuple(item.case_id for item in samples) == _CASE_IDS
    assert len(samples) == len({item.case_id for item in samples}) == 20
    assert len({_semantic_input(item) for item in samples}) == 20
    assert len({id(item.chart) for item in samples}) == 20
    assert len({id(item.features) for item in samples}) == 20

    mutable_ids: list[int] = []
    for item in samples:
        mutable_ids.extend((id(item.chart.four_pillars), id(item.features.element_counts),
                            id(item.features.element_energy), id(item.features.ten_god_counts)))
    assert len(mutable_ids) == len(set(mutable_ids))


@pytest.mark.parametrize(
    ("case_id", "blocker"),
    (
        ("YM-SYN-I1", "missing_or_unknown_sex"),
        ("YM-SYN-I2", "missing_or_invalid_day_pillar"),
        ("YM-SYN-I3", "incomplete_evidence"),
    ),
)
def test_incomplete_inputs_have_exact_hard_blocker(case_id: str, blocker: str) -> None:
    sample = _sample(case_id)
    result = discriminate_yang_marriage(sample.case_id, sample.chart, sample.features)

    assert result.state == "abstain"
    assert result.blocking_reason_codes == (blocker,)
    assert result.event_anchor_passed is False
    assert result.independent_spouse_interaction_passed is False


@pytest.mark.parametrize(
    ("case_id", "expected_pairs", "expected_state"),
    (
        ("YM-SYN-D1", (("寅", "申"),), "pressure"),
        ("YM-SYN-D2", (("午", "子"), ("卯", "子")), "pressure"),
        ("YM-SYN-D3", (), "pressure"),
        ("YM-SYN-D4", (("午", "子"),), "event"),
    ),
)
def test_dedup_cases_have_exact_canonical_pairs_and_one_relevant_family(
    case_id: str,
    expected_pairs: tuple[tuple[str, str], ...],
    expected_state: str,
) -> None:
    sample = _sample(case_id)
    result = discriminate_yang_marriage(sample.case_id, sample.chart, sample.features)
    anchors = [
        item for item in result.families
        if item.family_key == "spouse_palace_event_anchor"
    ]
    configurations = [
        item for item in result.families
        if item.family_key == "spouse_star_configuration"
    ]

    assert result.state == expected_state
    assert len(anchors) == (1 if expected_pairs else 0)
    if anchors:
        assert anchors[0].canonical_pairs == expected_pairs
    if case_id in {"YM-SYN-D3", "YM-SYN-D4"}:
        assert len(configurations) == 1
    assert "invalid_relationship_pair" not in result.blocking_reason_codes


def test_r1_repeats_identical_input_and_survives_pair_permutation() -> None:
    sample = _sample("YM-SYN-R1")
    first = discriminate_yang_marriage(sample.case_id, sample.chart, sample.features)
    repeated = discriminate_yang_marriage(sample.case_id, sample.chart, sample.features)
    permuted_payload = sample.features.to_dict()
    permuted_payload["chong_pairs"] = [
        list(reversed(pair)) for pair in reversed(sample.features.chong_pairs)
    ]
    permuted_payload["xing_hai_pairs"] = [
        list(reversed(pair)) for pair in reversed(sample.features.xing_hai_pairs)
    ]
    permuted_features = ChartFeatureVector.from_dict(permuted_payload)
    permuted = discriminate_yang_marriage(
        sample.case_id, sample.chart, permuted_features
    )

    assert first.to_dict() == repeated.to_dict() == permuted.to_dict()
