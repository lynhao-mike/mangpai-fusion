from __future__ import annotations

from collections.abc import Callable

import pytest

from engine.claims.domain import Claim
from engine.claims.orchestrator import generate_blind_outputs, generate_frozen_claim_run
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY, RunnerRegistry
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector
from engine.v5.duan_runner import generate_claims as generate_duan_claims
from engine.v5.ren_runner import generate_claims as generate_ren_claims
from engine.v5.ziping_runner import generate_claims as generate_ziping_claims


def _task(task_id: str, *, required_input_fields: tuple[str, ...] = ("four_pillars",)) -> BlindTask:
    return BlindTask(
        task_id=task_id,
        domain="事业",
        claim_type="structure",
        scoring_method="portrait_agreement",
        quantifiable=False,
        high_risk=False,
        allowed_time_horizons=["annual"],
        required_input_fields=required_input_fields,
        label_schema={},
        evaluation_note="runner-registry fixture",
    )


def _chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "庚申", "month": "庚申", "day": "甲午", "hour": "辛酉"},
    )


def test_default_registry_resolves_only_currently_implemented_school_tasks() -> None:
    ziping_tasks = {
        "structure.overview",
        "marriage.late_marriage",
        "career.role_change",
    }
    ren_tasks = {
        "career.change_window",
        "career.role_change",
        "marriage.event_window",
        "wealth.major_loss_window",
        "health.event_window",
    }
    duan_tasks = {
        "career.role_change",
        "career.path_type",
        "wealth.debt",
        "marriage.divorce_or_remarriage",
    }

    for task_id in ziping_tasks:
        assert DEFAULT_RUNNER_REGISTRY.resolve("ziping", task_id) is generate_ziping_claims
    for task_id in ren_tasks:
        assert DEFAULT_RUNNER_REGISTRY.resolve("ren", task_id) is generate_ren_claims
    for task_id in duan_tasks:
        assert DEFAULT_RUNNER_REGISTRY.resolve("duan", task_id) is generate_duan_claims

    assert DEFAULT_RUNNER_REGISTRY.resolve("ziping", "career.change_window") is None
    assert DEFAULT_RUNNER_REGISTRY.resolve("ren", "structure.overview") is None
    assert DEFAULT_RUNNER_REGISTRY.resolve("unknown-school", "structure.overview") is None
    assert DEFAULT_RUNNER_REGISTRY.resolve("duan", "career.change_window") is None


def test_registry_rejects_duplicate_school_task_registration() -> None:
    def generator(
        chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask,
    ) -> list[Claim]:
        return []

    with pytest.raises(ValueError, match="duplicate"):
        RunnerRegistry(
            [
                ("ziping", "structure.overview", generator),
                ("ziping", "structure.overview", generator),
            ]
        )


def test_registry_copies_external_mapping_and_exposes_no_mutable_registry() -> None:
    def first(
        chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask,
    ) -> list[Claim]:
        return []

    def replacement(
        chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask,
    ) -> list[Claim]:
        raise AssertionError("external mutation leaked into registry")

    registrations: dict[tuple[str, str], Callable[[ChartFactLedger, ChartFeatureVector, BlindTask], list[Claim]]] = {
        ("custom", "structure.overview"): first,
    }
    registry = RunnerRegistry(registrations)
    registrations[("custom", "structure.overview")] = replacement

    assert registry.resolve("custom", "structure.overview") is first
    assert not hasattr(registry, "registrations")
    assert not hasattr(registry, "runners")
    with pytest.raises((AttributeError, TypeError)):
        registry._runners[("custom", "other")] = replacement  # type: ignore[attr-defined]


def test_injected_registry_dispatches_exact_task_and_short_circuits_unregistered_task() -> None:
    calls: list[str] = []

    def generator(
        chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask,
    ) -> list[Claim]:
        calls.append(task.task_id)
        return []

    registry = RunnerRegistry([("custom", "registered.task", generator)])
    rows = generate_blind_outputs(
        _chart(),
        [
            _task("unregistered.task", required_input_fields=("four_pillars", "solar_datetime")),
            _task("registered.task"),
        ],
        case_id="C-RUNNER-REGISTRY",
        schools=["custom"],
        registry=registry,
    )

    assert calls == ["registered.task"]
    assert [(row.task_id, row.state) for row in rows] == [
        ("registered.task", "abstain"),
        ("unregistered.task", "unsupported"),
    ]


def test_injected_registry_preserves_deterministic_school_and_task_order() -> None:
    def generator(
        chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask,
    ) -> list[Claim]:
        return []

    registry = RunnerRegistry(
        [
            (school, task_id, generator)
            for school in ("alpha", "beta")
            for task_id in ("task.a", "task.z")
        ]
    )
    rows = generate_blind_outputs(
        _chart(),
        [_task("task.z"), _task("task.a")],
        case_id="C-RUNNER-ORDER",
        schools=["beta", "alpha", "beta"],
        registry=registry,
    )

    assert [(row.school_id, row.task_id) for row in rows] == [
        ("alpha", "task.a"),
        ("alpha", "task.z"),
        ("beta", "task.a"),
        ("beta", "task.z"),
    ]


def test_default_registry_preserves_claim_abstain_and_unsupported_states() -> None:
    rows = generate_blind_outputs(
        _chart(),
        [_task("structure.overview"), _task("career.change_window")],
        case_id="C-RUNNER-DEFAULT",
        schools=["ziping", "ren"],
    )
    indexed = {(row.school_id, row.task_id): row.state for row in rows}

    assert indexed[("ziping", "structure.overview")] == "claim"
    assert indexed[("ziping", "career.change_window")] == "unsupported"
    assert indexed[("ren", "structure.overview")] == "unsupported"
    assert indexed[("ren", "career.change_window")] == "abstain"


def test_frozen_entry_passes_injected_registry_to_blind_generation() -> None:
    calls: list[str] = []

    def generator(
        chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask,
    ) -> list[Claim]:
        calls.append(task.task_id)
        return []

    registry = RunnerRegistry([("custom", "registered.task", generator)])
    frozen = generate_frozen_claim_run(
        _chart(),
        [_task("registered.task"), _task("unregistered.task")],
        case_id="C-RUNNER-FROZEN",
        task_catalog_version="tasks/v1",
        rule_snapshot_id="rules/v1",
        schools=["custom"],
        registry=registry,
        frozen_at="2026-07-15T00:00:00Z",
    )

    assert calls == ["registered.task"]
    assert [(row.task_id, row.state) for row in frozen.outputs] == [
        ("registered.task", "abstain"),
        ("unregistered.task", "unsupported"),
    ]
