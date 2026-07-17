from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from engine.decision.ren_career_timing import discriminate_ren_career_timing


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


def test_task4_discriminator_remains_extraction_only_hold(
    trigger_chart, trigger_features, career_event
) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)

    assert result.local_state.value == "insufficient-trigger"
    assert result.publication_state.value == "hold"
    assert result.selected_family_key == ""
    assert result.failed_gates == ("timing_gate_not_evaluated",)
