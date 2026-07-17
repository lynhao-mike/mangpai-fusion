import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from types import MappingProxyType

import pytest

from engine.decision.ziping_career_structure import (
    LocalStructureState,
    PublicationState,
    discriminate_ziping_career_structure,
)


GEJU = {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []}


def test_supported_requires_named_official_output_and_structure_gates(
    chart, supported_features
) -> None:
    result = discriminate_ziping_career_structure(chart, supported_features, GEJU)
    assert result.local_state is LocalStructureState.SUPPORTED
    assert result.publication_state is PublicationState.EMIT
    assert result.gates == {
        "complete_fact_closure": True,
        "official_path_anchor": True,
        "output_interference_present": True,
        "structure_qualification": True,
    }
    assert {item.family_key for item in result.families if item.matched} >= {
        "official_path_anchor",
        "output_interference",
        "geju_direction",
    }


def test_first_falsifier_coarse_official_trigger_without_output_is_hold(
    chart, coarse_trigger_without_output_features
) -> None:
    result = discriminate_ziping_career_structure(
        chart, coarse_trigger_without_output_features, GEJU
    )
    assert result.coarse_trigger_observed is True
    assert result.gates["official_path_anchor"] is True
    assert result.gates["output_interference_present"] is False
    assert result.local_state is LocalStructureState.WEAKENED
    assert result.publication_state is PublicationState.HOLD


def test_financial_and_seal_protection_can_contradict_disruption(
    chart, protected_features
) -> None:
    result = discriminate_ziping_career_structure(
        chart,
        protected_features,
        {
            "geju_type": "正格",
            "favor_shishen": ["正官", "正印"],
            "avoid_shishen": ["伤官"],
        },
    )
    assert result.local_state is LocalStructureState.CONTRADICTED
    assert result.publication_state is PublicationState.HOLD
    assert "official_path_protection" in result.matched_counter_families


def test_branch_conflict_cannot_replace_official_or_output_gates(
    chart, supported_features
) -> None:
    features = replace(
        supported_features,
        ten_god_counts={key: 0 for key in supported_features.ten_god_counts},
        has_official=False,
        has_output=False,
        branch_conflict_intensity=1.0,
    )
    result = discriminate_ziping_career_structure(chart, features, GEJU)
    assert result.publication_state is not PublicationState.EMIT
    assert result.gates["official_path_anchor"] is False
    assert result.gates["output_interference_present"] is False


def test_partial_input_abstains(chart, supported_features) -> None:
    result = discriminate_ziping_career_structure(
        chart,
        replace(supported_features, evidence_completeness="partial"),
        GEJU,
    )
    assert result.local_state is LocalStructureState.ABSTAIN
    assert result.publication_state is PublicationState.ABSTAIN
    assert "complete_fact_closure" in result.failed_gates


def test_missing_geju_type_abstains(chart, supported_features) -> None:
    result = discriminate_ziping_career_structure(
        chart, supported_features, {"favor_shishen": [], "avoid_shishen": []}
    )
    assert result.local_state is LocalStructureState.ABSTAIN
    assert result.publication_state is PublicationState.ABSTAIN


def test_unknown_task_is_unsupported(chart, supported_features) -> None:
    result = discriminate_ziping_career_structure(
        chart,
        supported_features,
        GEJU,
        task_id="career.change_window",
    )
    assert result.publication_state is PublicationState.UNSUPPORTED


def test_discrimination_and_nested_families_are_immutable(
    chart, supported_features
) -> None:
    result = discriminate_ziping_career_structure(chart, supported_features, GEJU)
    assert isinstance(result.gates, MappingProxyType)
    assert isinstance(result.families, tuple)
    assert all(isinstance(item.fact_refs, tuple) for item in result.families)
    with pytest.raises(FrozenInstanceError):
        result.local_state = LocalStructureState.ABSTAIN  # type: ignore[misc]
    with pytest.raises(TypeError):
        result.gates["official_path_anchor"] = False  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        result.families[0].matched = False  # type: ignore[misc]


def test_discriminator_has_no_forbidden_imports() -> None:
    source_path = Path("engine/decision/ziping_career_structure.py")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    forbidden = ("feedback", "labels", "reports", "ren_career_timing", "l5_timing", "pipeline")
    assert not [name for name in imported if any(token in name for token in forbidden)]
