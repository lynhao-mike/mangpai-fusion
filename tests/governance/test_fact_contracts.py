from __future__ import annotations

import operator
from collections.abc import Callable
from dataclasses import FrozenInstanceError, replace
from enum import StrEnum

import pytest

from engine.governance import (
    CanonicalValue,
    ConflictingFactIdError,
    DigestRef,
    DuplicateFactIdError,
    FactContractError,
    FactLevel,
    FactSnapshot,
    FactSpec,
    GovernanceFact,
    SnapshotSpec,
    TemporalLayer,
    TemporalScope,
    build_fact_snapshot,
    build_governance_fact,
)


def _spec() -> FactSpec:
    return FactSpec(
        fact_kind="chart.hidden_stems",
        fact_level=FactLevel.CANONICAL_OBSERVATION,
        temporal_scope=TemporalScope(layer=TemporalLayer.NATAL),
        source_positions=("month.branch", "day.branch"),
        input_refs=("input.four_pillars",),
        calculator_id="hidden-stems",
        calculator_version="1.0.0",
    )


def _fact(payload: CanonicalValue, spec: FactSpec | None = None) -> GovernanceFact:
    return build_governance_fact(spec or _spec(), payload)


def _snapshot_spec(material: CanonicalValue = "input-v1") -> SnapshotSpec:
    return SnapshotSpec(
        schema_version="governance.fact-snapshot.v1",
        case_id="C-FACT-001",
        input_digest=DigestRef.from_material(material),
    )


def test_fact_domains_are_closed_string_enums() -> None:
    # Given / When
    levels = tuple(level.value for level in FactLevel)
    layers = tuple(layer.value for layer in TemporalLayer)

    # Then
    assert issubclass(FactLevel, StrEnum)
    assert levels == (
        "canonical_observation",
        "candidate_derived",
        "certified_technical",
        "certified_cross_school",
    )
    assert layers == ("natal", "dayun", "liunian")
    with pytest.raises(ValueError, match="school_conclusion"):
        FactLevel("school_conclusion")


def test_fact_payload_is_deeply_copied_and_frozen() -> None:
    # Given
    original = {"stems": ["甲", {"branch": "子"}]}

    # When
    fact = _fact(original)
    original["stems"][1]["branch"] = "午"
    original["stems"].append("乙")

    # Then
    assert fact.payload == {"stems": ("甲", {"branch": "子"})}
    with pytest.raises(TypeError):
        operator.setitem(fact.payload, "extra", "value")
    with pytest.raises(FrozenInstanceError):
        fact.fact_kind = "changed"


def test_fact_identity_is_separate_from_content_and_version_binding() -> None:
    # Given
    first = _fact({"value": "甲", "school": "ziping", "display_text": "old"})
    changed_spec = replace(_spec(), calculator_version="2.0.0")

    # When
    payload_changed = _fact(
        {"value": "乙", "school": "gao_dechen", "display_text": "new"},
    )
    version_changed = _fact(first.payload, changed_spec)

    # Then
    assert first.fact_id == payload_changed.fact_id == version_changed.fact_id
    assert first.content_digest != payload_changed.content_digest
    assert first.content_digest != version_changed.content_digest


def test_unordered_references_are_normalized_without_changing_identity() -> None:
    # Given
    reordered = replace(
        _spec(),
        source_positions=("day.branch", "month.branch"),
        input_refs=("input.sex", "input.four_pillars"),
    )
    sorted_refs = replace(
        reordered,
        source_positions=("month.branch", "day.branch"),
        input_refs=("input.four_pillars", "input.sex"),
    )

    # When
    first = _fact({"value": "甲"}, reordered)
    second = _fact({"value": "甲"}, sorted_refs)

    # Then
    assert first.source_positions == ("day.branch", "month.branch")
    assert first.input_refs == ("input.four_pillars", "input.sex")
    assert first == second


@pytest.mark.parametrize(
    "invalid_spec",
    (
        lambda: replace(_spec(), fact_kind=""),
        lambda: replace(_spec(), calculator_id=" "),
        lambda: replace(_spec(), calculator_version=""),
        lambda: replace(_spec(), source_positions=()),
        lambda: replace(_spec(), source_positions=("month.branch", "")),
        lambda: replace(_spec(), input_refs=()),
        lambda: replace(_spec(), input_refs=("input.chart", "input.chart")),
    ),
)
def test_fact_spec_rejects_empty_or_ambiguous_identity_material(
    invalid_spec: Callable[[], FactSpec],
) -> None:
    # Given / When
    with pytest.raises(FactContractError):
        invalid_spec()


@pytest.mark.parametrize("year", (True, False, 0, -1, 10_000))
def test_temporal_scope_rejects_bool_and_out_of_range_years(year: int | bool) -> None:
    # Given / When
    with pytest.raises(FactContractError):
        TemporalScope(layer=TemporalLayer.LIUNIAN, target_year=year)


def test_temporal_layers_enforce_separate_fail_closed_fields() -> None:
    # Given / When
    natal = TemporalScope(layer=TemporalLayer.NATAL)
    dayun = TemporalScope(
        layer=TemporalLayer.DAYUN,
        dayun_start_year=2018,
        dayun_end_year=2027,
    )
    liunian = TemporalScope(
        layer=TemporalLayer.LIUNIAN,
        target_year=2026,
        dayun_start_year=2018,
        dayun_end_year=2027,
    )

    # Then
    assert natal.layer is TemporalLayer.NATAL
    assert dayun.dayun_start_year == 2018
    assert liunian.target_year == 2026
    invalid = (
        lambda: TemporalScope(layer=TemporalLayer.NATAL, target_year=2026),
        lambda: TemporalScope(layer=TemporalLayer.DAYUN),
        lambda: TemporalScope(
            layer=TemporalLayer.DAYUN,
            dayun_start_year=2027,
            dayun_end_year=2018,
        ),
        lambda: TemporalScope(layer=TemporalLayer.DAYUN, target_year=2026),
        lambda: TemporalScope(layer=TemporalLayer.LIUNIAN),
        lambda: TemporalScope(
            layer=TemporalLayer.LIUNIAN,
            target_year=2026,
            dayun_start_year=2027,
            dayun_end_year=2036,
        ),
    )
    for invalid_scope in invalid:
        with pytest.raises(FactContractError):
            invalid_scope()


def test_fact_payload_rejects_non_string_keys() -> None:
    # Given / When
    with pytest.raises(FactContractError):
        _fact({1: "non-string key"})


def test_fact_payload_rejects_unsupported_values() -> None:
    # Given / When
    with pytest.raises(FactContractError):
        _fact({"unsupported": frozenset({"value"})})


def test_fact_payload_rejects_cycles() -> None:
    # Given
    cyclic = []
    cyclic.append(cyclic)

    # When / Then
    with pytest.raises(FactContractError):
        _fact(cyclic)


def test_snapshot_sorts_facts_and_is_order_independent() -> None:
    # Given
    first = _fact({"value": "甲"})
    second = _fact(
        {"value": "乙"},
        replace(_spec(), fact_kind="chart.visible_stems"),
    )

    # When
    forward = build_fact_snapshot(_snapshot_spec(), (first, second))
    reversed_order = build_fact_snapshot(_snapshot_spec(), (second, first))

    # Then
    assert forward == reversed_order
    assert forward.facts == tuple(
        sorted((first, second), key=lambda fact: fact.fact_id)
    )


def test_snapshot_rejects_identical_duplicate_fact_ids() -> None:
    # Given
    fact = _fact({"value": "甲"})

    # When / Then
    with pytest.raises(DuplicateFactIdError) as caught:
        build_fact_snapshot(_snapshot_spec(), (fact, fact))
    assert caught.value.fact_id == fact.fact_id


def test_snapshot_rejects_conflicting_content_as_integrity_error() -> None:
    # Given
    first = _fact({"value": "甲"})
    conflicting = _fact({"value": "乙"})

    # When / Then
    with pytest.raises(ConflictingFactIdError) as caught:
        build_fact_snapshot(_snapshot_spec(), (first, conflicting))
    assert caught.value.fact_id == first.fact_id
    assert caught.value.first_digest != caught.value.conflicting_digest


def test_snapshot_digest_binds_input_fact_payload_and_calculator_version() -> None:
    # Given
    first = _fact({"value": "甲"})
    payload_changed = _fact({"value": "乙"})
    version_changed = _fact(
        {"value": "甲"},
        replace(_spec(), calculator_version="2.0.0"),
    )

    # When
    baseline = build_fact_snapshot(_snapshot_spec(), (first,))
    changed_payload = build_fact_snapshot(_snapshot_spec(), (payload_changed,))
    changed_version = build_fact_snapshot(_snapshot_spec(), (version_changed,))
    changed_input = build_fact_snapshot(_snapshot_spec("input-v2"), (first,))

    # Then
    assert (
        baseline.snapshot_id
        == changed_payload.snapshot_id
        == changed_version.snapshot_id
    )
    assert (
        len(
            {
                baseline.content_digest,
                changed_payload.content_digest,
                changed_version.content_digest,
                changed_input.content_digest,
            },
        )
        == 4
    )
    assert baseline.snapshot_id != changed_input.snapshot_id
    assert isinstance(baseline, FactSnapshot)
