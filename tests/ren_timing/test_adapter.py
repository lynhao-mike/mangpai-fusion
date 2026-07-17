from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from engine.decision.ren_career_timing import discriminate_ren_career_timing
from engine.decision.ren_career_timing_slice import to_ren_timing_probability
from engine.features import build_chart_feature_vector


def _selected_family(result):
    return next(
        family
        for family in result.evidence_families
        if family.family_key == result.selected_family_key
    )


def _selected_atom(result):
    return min(
        _selected_family(result).atoms,
        key=lambda atom: (atom.priority, atom.year, atom.atom_id),
    )


def _resolve_fact_ref(chart: Any, ref: str) -> Any:
    current: Any = chart
    for part in ref.split("."):
        if part.isdigit():
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            current = getattr(current, part)
    return current


def _resolve_source_ref(ref: str) -> dict[str, Any]:
    path_text, anchor = ref.rsplit("#", 1)
    path = Path(path_text)
    assert path.is_file()
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    return next(rule for rule in document["rules"] if rule.get("id") == anchor)


def test_emit_result_builds_real_annual_window_with_rule_controlled_probability(
    trigger_chart, trigger_features, career_event
) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)
    atom = _selected_atom(result)

    timing = to_ren_timing_probability("C-REN-TIMING-001", result)

    assert timing.event_id == career_event.event_id
    assert timing.time_window == {
        "start_year": atom.year,
        "end_year": atom.year,
        "label": "annual",
    }
    assert "MVP 默认时间窗" not in str(timing.to_dict())
    assert timing.confidence == atom.confidence
    assert timing.probability_range == (
        max(0.0, atom.confidence - 0.1),
        min(1.0, atom.confidence + 0.1),
    )
    assert 0.0 <= timing.probability_range[0] <= timing.probability_range[1] <= 1.0


def test_emit_result_uses_stably_sorted_selected_atom_refs(
    trigger_chart, trigger_features, career_event
) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)
    atom = _selected_atom(result)

    timing = to_ren_timing_probability("C-REN-TIMING-001", result)

    assert timing.trigger_conditions == sorted(
        {atom.liunian_ref, atom.target_ref, atom.source_ref}
    )


def test_emitted_evidence_refs_resolve_to_real_chart_facts_and_rule_source(
    trigger_chart, trigger_features, career_event
) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)
    atom = _selected_atom(result)
    timing = to_ren_timing_probability("C-REN-TIMING-001", result)

    fact_refs = [atom.liunian_ref, atom.target_ref]
    resolved_facts = [_resolve_fact_ref(trigger_chart, ref) for ref in fact_refs]
    source_rule = _resolve_source_ref(atom.source_ref)

    assert all(value is not None for value in resolved_facts)
    assert atom.source_ref in timing.trigger_conditions
    assert source_rule["id"]
    assert source_rule["id"] in Path(atom.source_ref.split("#", 1)[0]).read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize("fixture_name", ["no_trigger_chart", "partial_chart"])
def test_non_emit_result_fails_closed(
    request, fixture_name, career_event
) -> None:
    chart = request.getfixturevalue(fixture_name)
    result = discriminate_ren_career_timing(
        chart,
        build_chart_feature_vector(chart),
        career_event,
    )

    with pytest.raises(ValueError, match="emit publication state required"):
        to_ren_timing_probability("C-REN-TIMING-001", result)


def test_emit_without_selected_family_fails_closed(
    trigger_chart, trigger_features, career_event
) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)
    missing = replace(result, selected_family_key="missing-family")

    with pytest.raises(ValueError, match="selected evidence family is required"):
        to_ren_timing_probability("C-REN-TIMING-001", missing)


@pytest.mark.parametrize("year", [1899, 2101])
def test_selected_atom_with_illegal_year_fails_closed(
    trigger_chart, trigger_features, career_event, year
) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)
    selected = _selected_family(result)
    invalid_atom = replace(_selected_atom(result), year=year)
    invalid_family = replace(selected, atoms=(invalid_atom,))
    invalid_result = replace(
        result,
        evidence_families=tuple(
            invalid_family if family.family_key == selected.family_key else family
            for family in result.evidence_families
        ),
    )

    with pytest.raises(ValueError, match="year outside supported staged range"):
        to_ren_timing_probability("C-REN-TIMING-001", invalid_result)
