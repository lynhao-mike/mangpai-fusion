from __future__ import annotations

import importlib
from dataclasses import replace
from pathlib import Path

import pytest

from engine.features import ChartFeatureVector


def _module():
    try:
        return importlib.import_module("engine.decision.chart_prototype")
    except ModuleNotFoundError as exc:
        pytest.fail(f"learnable prototype module is missing: {exc}")


def _vector(**changes: object) -> ChartFeatureVector:
    base = ChartFeatureVector(
        schema_version="cfv-v1",
        chart_id="chart-prototype-test",
        element_counts={"木": 2, "火": 2, "土": 2, "金": 1, "水": 1},
        element_energy={"木": 0.2, "火": 0.2, "土": 0.2, "金": 0.2, "水": 0.2},
        dominant_element="木",
        missing_elements=(),
        element_concentration=0.25,
        day_master="甲",
        day_master_element="木",
        month_branch="辰",
        month_lord="戊",
        rooted_count=1,
        supporting_count=4,
        draining_count=4,
        monthly_command_favorable=False,
        ten_god_counts={
            "比肩": 1,
            "劫财": 1,
            "食神": 0,
            "伤官": 0,
            "正财": 0,
            "偏财": 0,
            "正官": 0,
            "七杀": 0,
            "正印": 0,
            "偏印": 0,
        },
        has_official=False,
        has_wealth=False,
        has_output=False,
        has_resource=False,
        mixed_official_kill=False,
        chong_pairs=(),
        he_pairs=(),
        xing_hai_pairs=(),
        branch_conflict_intensity=0.1,
        cold_warm_axis=0.0,
        dry_wet_axis=0.0,
        climate_extreme=False,
        has_hour_pillar=True,
        evidence_completeness="full",
    )
    return replace(base, **changes)


@pytest.mark.parametrize(
    ("expected", "changes"),
    [
        ("prototype-climate-cold", {"cold_warm_axis": -0.8, "climate_extreme": True}),
        ("prototype-climate-hot", {"cold_warm_axis": 0.8, "climate_extreme": True}),
        ("prototype-climate-dry", {"dry_wet_axis": 0.8, "climate_extreme": True}),
        ("prototype-climate-wet", {"dry_wet_axis": -0.8, "climate_extreme": True}),
        ("prototype-element-concentrated", {"element_concentration": 0.625, "missing_elements": ("金", "水")}),
        ("prototype-branch-conflict-high", {"branch_conflict_intensity": 0.7, "chong_pairs": (("子", "午"),)}),
        ("prototype-official-kill-mixed", {"mixed_official_kill": True, "has_official": True}),
        ("prototype-wealth-official-combo", {"has_wealth": True, "has_official": True}),
        ("prototype-output-resource-combo", {"has_output": True, "has_resource": True}),
        ("prototype-day-master-supported", {"supporting_count": 7, "draining_count": 1, "rooted_count": 3}),
        ("prototype-day-master-drained", {"supporting_count": 1, "draining_count": 7, "rooted_count": 0}),
        ("prototype-relation-harmony", {"he_pairs": (("子", "丑"), ("寅", "亥"))}),
        ("prototype-balanced", {}),
    ],
)
def test_each_registered_prototype_has_a_positive_and_negative_example(
    expected: str,
    changes: dict[str, object],
) -> None:
    module = _module()

    positive = module.classify_prototype(_vector(**changes))
    negative = module.classify_prototype(_vector(**({} if changes else {"evidence_completeness": "partial"})))

    assert positive.prototype_id == expected
    assert positive.matched_conditions
    if changes:
        assert negative.prototype_id != expected


def test_registry_contains_between_ten_and_twenty_data_defined_prototypes() -> None:
    module = _module()

    definitions = module.load_prototype_registry(Path("mapping/chart-prototype-registry-v1.yaml"))

    assert 10 <= len(definitions) <= 20
    assert all(item.required_features for item in definitions)
    assert all(item.prototype_id.startswith("prototype-") for item in definitions)


def test_boundary_assignment_exposes_alternative_and_is_deterministic() -> None:
    module = _module()
    vector = _vector(
        branch_conflict_intensity=0.7,
        chong_pairs=(("子", "午"),),
        mixed_official_kill=True,
        has_official=True,
    )

    first = module.classify_prototype(vector)
    second = module.classify_prototype(vector)

    assert first == second
    assert first.prototype_id == "prototype-official-kill-mixed"
    assert "prototype-branch-conflict-high" in first.alternative_ids
    assert 0.0 < first.confidence < 1.0


def test_partial_unmatched_vector_is_not_forced_into_nearest_prototype() -> None:
    module = _module()

    assignment = module.classify_prototype(_vector(evidence_completeness="partial"))

    assert assignment.prototype_id == "prototype-unclassified"
    assert assignment.confidence == 0.0
    assert assignment.matched_conditions == ()
