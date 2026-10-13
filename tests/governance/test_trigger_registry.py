from __future__ import annotations

import os
from dataclasses import replace

import pytest

from engine.governance.contracts import (
    DigestRef,
    FactLevel,
    SnapshotSpec,
    TemporalLayer,
    TemporalScope,
    build_fact_snapshot,
    build_governance_fact,
)
from engine.governance.fact_values import FactSpec
from engine.governance.trigger_registry import (
    TriggerEvaluationContext,
    TriggerIssueCode,
    TriggerOutcome,
    TriggerRegistrationSpec,
    TriggerRegistryContractError,
    build_trigger_registry,
    evaluate_governance_trigger,
    load_trigger_registry,
)


def _fact(
    fact_kind: str,
    scope: TemporalScope = TemporalScope(TemporalLayer.NATAL),
    payload: tuple[str, str] = ("value", "present"),
):
    return build_governance_fact(
        FactSpec(
            fact_kind=fact_kind,
            fact_level=FactLevel.CANONICAL_OBSERVATION,
            temporal_scope=scope,
            source_positions=(f"input.{fact_kind}",),
            input_refs=("raw-chart",),
            calculator_id="trigger-test",
            calculator_version="1.0.0",
        ),
        payload,
    )


def _snapshot(*facts):
    return build_fact_snapshot(
        SnapshotSpec(
            schema_version="trigger-test-snapshot/v1",
            case_id="C-TRIGGER-001",
            input_digest=DigestRef.from_material(("trigger-test-input",)),
        ),
        tuple(facts),
    )


def _spec(
    trigger_id: str,
    evaluator_id: str = "fact_kind_present",
    required_fact_kinds: tuple[str, ...] = ("chart.natal",),
    allowed_temporal_layers: tuple[str, ...] = ("natal",),
    publication_status: str = "published",
    evaluator_version: str = "1.0.0",
) -> TriggerRegistrationSpec:
    return TriggerRegistrationSpec(
        trigger_id=trigger_id,
        evaluator_id=evaluator_id,
        evaluator_version=evaluator_version,
        required_fact_kinds=required_fact_kinds,
        allowed_temporal_layers=allowed_temporal_layers,
        missing_input_behavior="inactive_with_issue",
        publication_status=publication_status,
    )


def _published_registry():
    return build_trigger_registry(
        (
            _spec("synthetic.natal-present"),
            _spec(
                "synthetic.liunian-target",
                evaluator_id="liunian_target_year_present",
                required_fact_kinds=("chart.liunian",),
                allowed_temporal_layers=("liunian",),
            ),
        )
    )


def test_unknown_trigger_is_inactive_with_issue() -> None:
    # Given: a published registry and a valid snapshot.
    registry = _published_registry()
    snapshot = _snapshot(_fact("chart.natal"))

    # When: an unregistered trigger is evaluated.
    result = evaluate_governance_trigger(
        registry, "synthetic.unknown", snapshot, TriggerEvaluationContext()
    )

    # Then: the new path fails closed.
    assert result == TriggerOutcome(
        active=False,
        issues=(TriggerIssueCode.UNKNOWN_TRIGGER,),
    )


@pytest.mark.parametrize("status", ["candidate", "synthetic_only"])
def test_unpublished_trigger_is_not_executed(status: str) -> None:
    # Given: a trigger that is registered but not published.
    registry = build_trigger_registry(
        (_spec("synthetic.natal-present", publication_status=status),)
    )

    # When: a matching fact snapshot is evaluated.
    result = evaluate_governance_trigger(
        registry,
        "synthetic.natal-present",
        _snapshot(_fact("chart.natal")),
        TriggerEvaluationContext(),
    )

    # Then: the evaluator did not run.
    assert result == TriggerOutcome(
        active=False,
        issues=(TriggerIssueCode.UNPUBLISHED_TRIGGER,),
    )


def test_missing_required_fact_is_inactive() -> None:
    # Given: no fact of the kind declared by the trigger.
    registry = _published_registry()

    # When: the trigger is evaluated.
    result = evaluate_governance_trigger(
        registry,
        "synthetic.natal-present",
        _snapshot(_fact("other.fact")),
        TriggerEvaluationContext(),
    )

    # Then: missing input fails closed.
    assert result == TriggerOutcome(
        active=False,
        issues=(TriggerIssueCode.MISSING_REQUIRED_FACT,),
    )


def test_liunian_trigger_requires_explicit_target_year_fact() -> None:
    # Given: a nonempty natal snapshot but no liunian target-year fact.
    registry = _published_registry()

    # When: a liunian trigger is evaluated.
    result = evaluate_governance_trigger(
        registry,
        "synthetic.liunian-target",
        _snapshot(_fact("chart.natal")),
        TriggerEvaluationContext(parsed_present=True),
    )

    # Then: it remains inactive.
    assert result == TriggerOutcome(
        active=False,
        issues=(TriggerIssueCode.MISSING_REQUIRED_FACT,),
    )


def test_as_of_date_system_clock_and_parsed_object_do_not_substitute_target_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given: context values that must not synthesize liunian.
    monkeypatch.setenv("TZ", "Asia/Shanghai")
    before = os.environ["TZ"]
    registry = _published_registry()
    context = TriggerEvaluationContext(as_of_date="2026-08-04", parsed_present=True)

    # When: no explicit liunian fact exists.
    result = evaluate_governance_trigger(
        registry,
        "synthetic.liunian-target",
        _snapshot(_fact("chart.natal")),
        context,
    )

    # Then: the context did not become target-year evidence.
    assert os.environ["TZ"] == before
    assert result == TriggerOutcome(
        active=False,
        issues=(TriggerIssueCode.MISSING_REQUIRED_FACT,),
    )


def test_liunian_trigger_activates_only_from_explicit_target_year_fact() -> None:
    # Given: an explicit liunian fact with target_year in its TemporalScope.
    registry = _published_registry()
    liunian = _fact(
        "chart.liunian",
        TemporalScope(TemporalLayer.LIUNIAN, target_year=2026),
        ("year", "2026"),
    )

    # When: the liunian trigger is evaluated.
    result = evaluate_governance_trigger(
        registry,
        "synthetic.liunian-target",
        _snapshot(liunian),
        TriggerEvaluationContext(as_of_date="1999-01-01"),
    )

    # Then: only the explicit fact activates it.
    assert result == TriggerOutcome(active=True, issues=())


@pytest.mark.parametrize(
    "evaluator_id",
    ["when wealth looks strong", "chart.liunian.year == 2026", "lambda facts: True"],
)
def test_natural_language_or_expression_is_not_an_evaluator_id(
    evaluator_id: str,
) -> None:
    # Given/When/Then: only closed evaluator IDs parse.
    with pytest.raises(TriggerRegistryContractError) as raised:
        build_trigger_registry((_spec("synthetic.bad", evaluator_id=evaluator_id),))
    assert raised.value.issue_code == "TRIGGER.EVALUATOR_ID"


def test_unknown_evaluator_version_is_rejected() -> None:
    # Given/When/Then: evaluator identity is closed by ID and version.
    with pytest.raises(TriggerRegistryContractError) as raised:
        build_trigger_registry(
            (_spec("synthetic.bad-version", evaluator_version="9.9.9"),)
        )
    assert raised.value.issue_code == "TRIGGER.EVALUATOR_VERSION"


def test_evaluator_can_only_read_declared_fact_kinds() -> None:
    # Given: an undeclared liunian target is present next to the declared natal fact.
    registry = build_trigger_registry(
        (
            _spec(
                "synthetic.natal-present",
                evaluator_id="liunian_target_year_present",
            ),
        )
    )
    liunian = _fact(
        "chart.liunian",
        TemporalScope(TemporalLayer.LIUNIAN, target_year=2026),
    )

    # When: the evaluator would activate if it could read undeclared facts.
    result = evaluate_governance_trigger(
        registry,
        "synthetic.natal-present",
        _snapshot(_fact("chart.natal"), liunian),
        TriggerEvaluationContext(),
    )

    # Then: the visible fact boundary keeps it inactive.
    assert result == TriggerOutcome(active=False, issues=())


def test_same_snapshot_is_deterministic_and_side_effect_free() -> None:
    # Given: the same immutable snapshot is reused.
    registry = _published_registry()
    snapshot = _snapshot(_fact("chart.natal"))

    # When: evaluation is repeated.
    first = evaluate_governance_trigger(
        registry,
        "synthetic.natal-present",
        snapshot,
        TriggerEvaluationContext(parsed_present=True),
    )
    second = evaluate_governance_trigger(
        registry,
        "synthetic.natal-present",
        snapshot,
        TriggerEvaluationContext(parsed_present=False),
    )

    # Then: the result and snapshot are stable.
    assert first == second == TriggerOutcome(active=True, issues=())
    assert snapshot == replace(snapshot)


def test_registry_yaml_accepts_only_the_triggers_top_level_extension() -> None:
    # Given/When: the shared governance YAML is loaded through the trigger surface.
    registry = load_trigger_registry()

    # Then: it exposes only candidate synthetic test triggers, not production triggers.
    assert tuple(item.trigger_id for item in registry.triggers) == (
        "synthetic.natal-present",
        "synthetic.liunian-target",
    )
    assert all(
        item.publication_status.value != "production" for item in registry.triggers
    )
