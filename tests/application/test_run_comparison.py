from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from engine.application.run_comparison import StructuredRunItem, compare_runs, run_and_compare
from engine.application.staged_parallel_runner import ParallelRun
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, FrozenBlindRun


@dataclass(frozen=True)
class LegacyFixture:
    structured_run_items: tuple[StructuredRunItem, ...]


def _item(
    task_id: str,
    school_id: str,
    *,
    state: str = "claim",
    event_label: str | None = "occurred",
    polarity: str | None = "neutral",
    time_window: dict[str, object] | None = None,
    risk_flag: bool | None = False,
    evidence_completeness: str | None = "full",
) -> StructuredRunItem:
    return StructuredRunItem(
        task_id=task_id,
        school_id=school_id,
        domain="事业",
        claim_state=state,
        event_label=event_label,
        polarity=polarity,
        time_window=time_window,
        risk_flag=risk_flag,
        evidence_completeness=evidence_completeness,
    )


def _claim_run(items: tuple[StructuredRunItem, ...]) -> FrozenBlindRun:
    outputs = []
    for index, item in enumerate(items):
        predictions = []
        if item.claim_state == "claim":
            predictions.append(
                BlindPrediction(
                    prediction_id=f"p-{index}",
                    event_label=item.event_label or "occurred",
                    probability=0.7,
                    time_window=item.time_window or {},
                    evidence_refs=[f"e-{index}"] if item.evidence_completeness != "partial" else [],
                    falsifier="not observed",
                )
            )
        outputs.append(
            BlindSchoolOutput(
                case_id="C-TASK10",
                school_id=item.school_id,
                task_id=item.task_id,
                state=item.claim_state,
                rationale="structured fixture",
                predictions=predictions,
            )
        )
    run = FrozenBlindRun(
        task_catalog_version="tasks/v1",
        rule_snapshot_id="rules/v1",
        frozen_at="content:fixed",
        outputs=outputs,
        freeze_hash="hash-fixed",
    )
    object.__setattr__(run, "comparison_metadata", {
        (item.task_id, item.school_id): {
            "domain": item.domain,
            "polarity": item.polarity,
            "risk_flag": item.risk_flag,
            "evidence_completeness": item.evidence_completeness,
        }
        for item in items
    })
    return run


def test_compare_runs_returns_all_five_statuses_across_seven_dimensions() -> None:
    legacy_items = (
        _item("t.same", "s", event_label="occurred"),
        _item("t.differ", "s", event_label="employment", polarity="positive"),
        _item("t.only_legacy", "s", state="abstain", event_label=None, polarity=None, time_window=None, risk_flag=None, evidence_completeness=None),
        _item("t.both_missing", "s", state="abstain", event_label=None, polarity=None, time_window=None, risk_flag=None, evidence_completeness=None),
    )
    claim_items = (
        _item("t.same", "s", event_label="occurred"),
        _item("t.differ", "s", event_label="entrepreneurship", polarity="negative"),
        _item("t.only_claim", "s", event_label="moderate"),
        _item("t.both_missing", "s", state="abstain", event_label=None, polarity=None, time_window=None, risk_flag=None, evidence_completeness=None),
    )
    parallel = ParallelRun(
        case_id="C-TASK10",
        legacy_snapshot=LegacyFixture(legacy_items),
        claim_snapshot=_claim_run(claim_items),
    )

    comparison = compare_runs(parallel)
    by_key = {(row.task_id, row.school_id): row for row in comparison.items}

    assert by_key[("t.same", "s")].task_coverage.status == "same"
    assert by_key[("t.differ", "s")].event_label.status == "differ"
    assert by_key[("t.differ", "s")].polarity.status == "differ"
    assert by_key[("t.only_legacy", "s")].task_coverage.status == "only_legacy"
    assert by_key[("t.only_claim", "s")].task_coverage.status == "only_claim"
    assert by_key[("t.both_missing", "s")].event_label.status == "both_missing"

    expected_dimensions = {
        "task_coverage",
        "claim_state",
        "event_label",
        "polarity",
        "time_window",
        "risk_flag",
        "evidence_completeness",
    }
    assert set(comparison.items[0].to_dict()) == {"task_id", "school_id", "domain", *expected_dimensions}


@pytest.mark.parametrize(
    ("field", "legacy_value", "claim_value"),
    (
        ("claim_state", "claim", "abstain"),
        ("event_label", "occurred", "entrepreneurship"),
        ("polarity", "positive", "negative"),
        (
            "time_window",
            {"start_year": 2024, "end_year": 2025, "label": "annual"},
            {"start_year": 2025, "end_year": 2025, "label": "annual"},
        ),
        ("risk_flag", False, True),
        ("evidence_completeness", "full", "no_hour"),
    ),
)
def test_each_structured_value_dimension_detects_difference(field, legacy_value, claim_value) -> None:
    kwargs = {
        "state": "claim",
        "event_label": "occurred",
        "polarity": "neutral",
        "time_window": {"start_year": 2024, "end_year": 2024, "label": "annual"},
        "risk_flag": False,
        "evidence_completeness": "full",
    }
    legacy_kwargs = dict(kwargs)
    claim_kwargs = dict(kwargs)
    key = "state" if field == "claim_state" else field
    legacy_kwargs[key] = legacy_value
    claim_kwargs[key] = claim_value
    if field == "claim_state" and claim_value != "claim":
        claim_kwargs.update(event_label=None, time_window=None)

    comparison = compare_runs(ParallelRun(
        case_id="C-TASK10",
        legacy_snapshot=LegacyFixture((_item("task", "school", **legacy_kwargs),)),
        claim_snapshot=_claim_run((_item("task", "school", **claim_kwargs),)),
    ))

    assert getattr(comparison.items[0], field).status == "differ"


def test_comparison_is_sorted_deterministic_and_contains_no_forbidden_fields(monkeypatch) -> None:
    items = (
        _item("z-task", "b-school", event_label="occurred"),
        _item("a-task", "z-school", event_label="moderate"),
        _item("a-task", "a-school", event_label="entrepreneurship"),
    )
    parallel = ParallelRun(
        case_id="C-TASK10",
        legacy_snapshot=LegacyFixture(tuple(reversed(items))),
        claim_snapshot=_claim_run(items),
    )
    monkeypatch.setattr("engine.application.run_comparison.run_parallel", lambda *args, **kwargs: parallel)

    first = run_and_compare(object(), (), case_id="C-TASK10", schools=()).to_dict()
    second = run_and_compare(object(), (), case_id="C-TASK10", schools=()).to_dict()
    first_bytes = json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    second_bytes = json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    assert first_bytes == second_bytes
    assert [(row["task_id"], row["school_id"]) for row in first["items"]] == [
        ("a-task", "a-school"),
        ("a-task", "z-school"),
        ("z-task", "b-school"),
    ]
    serialized = first_bytes.decode("utf-8").lower()
    for forbidden in ("feedback", "revealed_labels", "known_facts", "report_text", "school_claims"):
        assert forbidden not in serialized


def test_compare_runs_preserves_independent_branch_errors() -> None:
    comparison = compare_runs(ParallelRun(
        case_id="C-TASK10",
        legacy_snapshot=None,
        claim_snapshot=None,
        legacy_error="RuntimeError: legacy boom",
        claim_error="RuntimeError: claim boom",
    ))

    assert comparison.legacy_error == "RuntimeError: legacy boom"
    assert comparison.claim_error == "RuntimeError: claim boom"
    assert comparison.items == ()
