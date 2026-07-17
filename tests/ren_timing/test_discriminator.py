from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from engine.decision.ren_career_timing import discriminate_ren_career_timing
from engine.features import build_chart_feature_vector
from engine.predicates.relations import zhi_chong, zhi_chuan, zhi_liuhe, zhi_xing


def _atoms(result):
    return tuple(atom for family in result.evidence_families for atom in family.atoms)


def test_extracts_auditable_relation_atoms(trigger_chart, trigger_features, career_event) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)
    atoms = _atoms(result)

    assert atoms
    assert {atom.relation for atom in atoms} >= {"冲", "穿", "伏吟"}
    assert all(atom.year >= 1900 for atom in atoms)
    assert all(atom.liunian_ref.startswith("liunian_steps.") for atom in atoms)
    assert all(atom.target_ref and atom.rule_id and atom.source_ref for atom in atoms)
    assert len({atom.atom_id for atom in atoms}) == len(atoms)


def test_trigger_atoms_are_immutable_slots_dtos(trigger_chart, trigger_features, career_event) -> None:
    atom = _atoms(discriminate_ren_career_timing(trigger_chart, trigger_features, career_event))[0]

    assert not hasattr(atom, "__dict__")
    with pytest.raises(FrozenInstanceError):
        atom.year = 2099  # type: ignore[misc]


def test_relation_atoms_are_family_deduplicated(trigger_chart, trigger_features, career_event) -> None:
    duplicate_relation_chart = replace(
        trigger_chart,
        four_pillars={**trigger_chart.four_pillars, "hour": "辛子"},
    )
    result = discriminate_ren_career_timing(
        duplicate_relation_chart,
        trigger_features,
        career_event,
    )
    keys = [family.family_key for family in result.evidence_families]

    assert len(keys) == len(set(keys))
    assert all(family.atoms for family in result.evidence_families)
    assert any(len(family.atoms) > 1 for family in result.evidence_families)


def test_chart_and_feature_input_order_does_not_change_serialized_result(
    trigger_chart, trigger_features, career_event
) -> None:
    reordered_chart = replace(
        trigger_chart,
        four_pillars=dict(reversed(tuple(trigger_chart.four_pillars.items()))),
        dayun_steps=list(reversed(trigger_chart.dayun_steps)),
        liunian_steps=list(reversed(trigger_chart.liunian_steps)),
    )
    reordered_features = replace(
        trigger_features,
        element_counts=dict(reversed(tuple(trigger_features.element_counts.items()))),
        element_energy=dict(reversed(tuple(trigger_features.element_energy.items()))),
        ten_god_counts=dict(reversed(tuple(trigger_features.ten_god_counts.items()))),
        chong_pairs=tuple(reversed(trigger_features.chong_pairs)),
        he_pairs=tuple(reversed(trigger_features.he_pairs)),
        xing_hai_pairs=tuple(reversed(trigger_features.xing_hai_pairs)),
    )

    original = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)
    reordered = discriminate_ren_career_timing(reordered_chart, reordered_features, career_event)

    assert original.to_dict() == reordered.to_dict()
    assert {atom.atom_id for atom in _atoms(original)} == {atom.atom_id for atom in _atoms(reordered)}


def test_valid_trigger_emits_one_selected_family(
    trigger_chart, trigger_features, career_event
) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)

    assert result.local_state.value == "timing-ready"
    assert result.publication_state.value == "emit"
    assert result.selected_family_key
    assert result.failed_gates == ()
    selected = next(
        family for family in result.evidence_families
        if family.family_key == result.selected_family_key
    )
    expected = min(
        result.evidence_families,
        key=lambda family: (
            min(atom.priority for atom in family.atoms),
            min(atom.year for atom in family.atoms),
            family.family_key,
        ),
    )
    assert selected == expected


def test_first_falsifier_has_no_l5_eligible_result(no_trigger_chart, career_event) -> None:
    annual_branch = no_trigger_chart.liunian_steps[0]["ganzhi"][1]
    target_branches = [
        value[1] for value in no_trigger_chart.four_pillars.values()
    ] + [no_trigger_chart.liunian_steps[0]["dayun"][1]]
    assert all(
        not zhi_chong(annual_branch, target)
        and zhi_xing(annual_branch, target) is None
        and not zhi_chuan(annual_branch, target)
        and annual_branch != target
        and zhi_liuhe(annual_branch, target) is None
        and frozenset((annual_branch, target)) != frozenset(("午", "未"))
        for target in target_branches
    )

    features = build_chart_feature_vector(no_trigger_chart)
    result = discriminate_ren_career_timing(no_trigger_chart, features, career_event)

    assert result.local_state.value == "abstain"
    assert result.publication_state.value != "emit"
    assert result.selected_family_key == ""
    assert "relation_trigger_required" in result.failed_gates


def test_missing_context_abstains(partial_chart, career_event) -> None:
    features = build_chart_feature_vector(partial_chart)
    result = discriminate_ren_career_timing(partial_chart, features, career_event)

    assert result.local_state.value == "abstain"
    assert result.publication_state.value == "abstain"
    assert set(result.input_blockers) == {"dayun_required", "liunian_required"}


def test_related_but_unusable_year_is_hold(
    trigger_chart, trigger_features, career_event
) -> None:
    incomplete = replace(
        trigger_chart,
        liunian_steps=[{"ganzhi": "丙午", "dayun": "甲午"}],
    )
    result = discriminate_ren_career_timing(incomplete, trigger_features, career_event)

    assert result.local_state.value == "insufficient-trigger"
    assert result.publication_state.value == "hold"
    assert result.selected_family_key == ""
    assert result.failed_gates == ("trigger_year_required",)


def test_step_without_any_relation_abstains(no_trigger_chart, career_event) -> None:
    features = build_chart_feature_vector(no_trigger_chart)
    result = discriminate_ren_career_timing(no_trigger_chart, features, career_event)

    assert result.local_state.value == "abstain"
    assert result.publication_state.value == "abstain"
    assert result.failed_gates == ("relation_trigger_required",)


@pytest.mark.parametrize("event", [None, "not-an-event"])
def test_missing_or_wrong_type_upstream_event_is_routing_abstain(
    trigger_chart, trigger_features, event
) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, event)

    assert result.local_state.value == "abstain"
    assert result.publication_state.value == "abstain"
    assert result.routing_blockers == ("qualified_career_event_required",)


def test_wrong_event_type_is_routing_abstain(
    trigger_chart, trigger_features, career_event
) -> None:
    wrong_event = replace(career_event, event_type="wealth.gain")
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, wrong_event)

    assert result.local_state.value == "abstain"
    assert result.publication_state.value == "abstain"
    assert result.routing_blockers == ("qualified_career_event_required",)


def test_unsupported_task_is_unsupported(
    trigger_chart, trigger_features, career_event
) -> None:
    result = discriminate_ren_career_timing(
        trigger_chart,
        trigger_features,
        career_event,
        task_id="marriage.event",
    )

    assert result.local_state.value == "unsupported"
    assert result.publication_state.value == "unsupported"
