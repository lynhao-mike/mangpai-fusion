from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from tools.school_capability_dataset import register_prospective_intake


YAML_TASK_CATALOG = Path("mapping/school-capability-task-catalog-v1.yaml")
LEGACY_PROSPECTIVE_TASK_CATALOG = Path("META/school-capability-prospective-tasks-v1.json")
GO_TASK_CATALOG = Path("META/prospective-go-task-catalog-v1.json")
PROTOCOL = Path("META/prospective-intake-protocol-v1.md")
OBSERVATION_TEMPLATE = Path("templates/prospective-observation-v1.json")
TASKS_BY_CASE = Path("META/prospective-go/prospective-go-b01-tasks-by-case.json")

APPROVED_TASK_IDS = (
    "structure.overview",
    "career.role_change",
    "marriage.divorce_or_remarriage",
    "wealth.debt",
    "career.path_type",
    "health.system_risk",
    "career.change_window",
    "marriage.event_window",
    "health.event_window",
    "wealth.major_loss_window",
)
BINARY_TASK_IDS = {
    "career.role_change",
    "marriage.divorce_or_remarriage",
}
TIMING_TASK_IDS = {
    "career.change_window",
    "marriage.event_window",
    "health.event_window",
    "wealth.major_loss_window",
}
HIGH_RISK_REVIEW_TASK_IDS = {
    "marriage.divorce_or_remarriage",
    "wealth.debt",
    "health.system_risk",
}
COPIED_TASK_FIELDS = {
    "task_id",
    "claim_type",
    "scoring_method",
    "quantifiable",
    "high_risk",
    "allowed_time_horizons",
    "required_input_fields",
    "label_schema",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _yaml_tasks() -> dict[str, dict[str, Any]]:
    document = yaml.safe_load(YAML_TASK_CATALOG.read_text(encoding="utf-8"))
    return {task["task_id"]: task for task in document["tasks"]}


def _gate_status(
    *,
    subject_hashes: list[str],
    binary_labels: dict[str, list[str]],
    timing_assignments: dict[str, list[dict[str, Any]]],
    high_risk_labels: list[dict[str, Any]],
) -> str:
    """Test-side statement of the frozen Task 1 intake gate."""
    if len(subject_hashes) < 30 or len(set(subject_hashes)) < 30:
        return "HOLD"
    if not any(
        len(labels) >= 20 and {"occurred", "not_observed"} <= set(labels)
        for task_id, labels in binary_labels.items()
        if task_id in BINARY_TASK_IDS
    ):
        return "HOLD"
    if any(not steps for steps in timing_assignments.values()):
        return "HOLD"
    for label in high_risk_labels:
        if label.get("task_id") not in HIGH_RISK_REVIEW_TASK_IDS:
            continue
        reviewers = label.get("reviewers", [])
        if len(reviewers) != 2 or len(set(reviewers)) != 2:
            return "HOLD"
    return "GO"


def _go_inputs() -> dict[str, Any]:
    return {
        "subject_hashes": [f"subject-{index:02d}" for index in range(30)],
        "binary_labels": {
            "career.role_change": ["occurred"] * 10 + ["not_observed"] * 10,
        },
        "timing_assignments": {
            task_id: [{"year": 2026, "ganzhi": "丙午"}]
            for task_id in TIMING_TASK_IDS
        },
        "high_risk_labels": [
            {"task_id": task_id, "reviewers": ["human-reviewer-a", "human-reviewer-b"]}
            for task_id in HIGH_RISK_REVIEW_TASK_IDS
        ],
    }


def test_go_catalog_freezes_exactly_ten_approved_tasks_without_field_drift() -> None:
    document = _read_json(GO_TASK_CATALOG)

    assert document["schema_version"] == "school-capability-cli-tasks/v1"
    assert document["task_catalog_version"] == "prospective-go-tasks-v1"
    tasks = document["tasks"]
    assert [task["task_id"] for task in tasks] == list(APPROVED_TASK_IDS)

    source = _yaml_tasks()
    for task in tasks:
        expected = source[task["task_id"]]
        assert {field: task[field] for field in COPIED_TASK_FIELDS} == {
            field: expected[field] for field in COPIED_TASK_FIELDS
        }


def test_legacy_five_task_catalog_cannot_satisfy_binary_and_high_risk_collection() -> None:
    legacy_ids = {task["task_id"] for task in _read_json(LEGACY_PROSPECTIVE_TASK_CATALOG)["tasks"]}

    assert len(legacy_ids) == 5
    assert "career.role_change" not in legacy_ids
    assert not HIGH_RISK_REVIEW_TASK_IDS <= legacy_ids
    assert set(APPROVED_TASK_IDS) != legacy_ids


@pytest.mark.parametrize(
    "mutation",
    [
        "too_few_subjects",
        "duplicate_subject",
        "too_few_binary",
        "positive_only_binary",
        "negative_only_binary",
        "missing_liunian",
        "single_reviewer",
        "duplicate_reviewer",
    ],
)
def test_prospective_gate_holds_when_a_hard_collection_requirement_is_missing(mutation: str) -> None:
    inputs = _go_inputs()
    if mutation == "too_few_subjects":
        inputs["subject_hashes"] = inputs["subject_hashes"][:29]
    elif mutation == "duplicate_subject":
        inputs["subject_hashes"][-1] = inputs["subject_hashes"][0]
    elif mutation == "too_few_binary":
        inputs["binary_labels"]["career.role_change"] = ["occurred"] * 10 + ["not_observed"] * 9
    elif mutation == "positive_only_binary":
        inputs["binary_labels"]["career.role_change"] = ["occurred"] * 20
    elif mutation == "negative_only_binary":
        inputs["binary_labels"]["career.role_change"] = ["not_observed"] * 20
    elif mutation == "missing_liunian":
        inputs["timing_assignments"]["career.change_window"] = []
    elif mutation == "single_reviewer":
        inputs["high_risk_labels"][0]["reviewers"] = ["human-reviewer-a"]
    elif mutation == "duplicate_reviewer":
        inputs["high_risk_labels"][0]["reviewers"] = ["human-reviewer-a", "human-reviewer-a"]

    assert _gate_status(**inputs) == "HOLD"


def test_prospective_gate_reference_fixture_reaches_go_without_lowering_thresholds() -> None:
    assert _gate_status(**_go_inputs()) == "GO"


def test_protocol_and_observation_template_freeze_prediction_first_semantics() -> None:
    protocol = PROTOCOL.read_text(encoding="utf-8")
    template = _read_json(OBSERVATION_TEMPLATE)

    for required_text in (
        "freeze",
        "not_observed",
        "no_data",
        "liunian_steps",
        "sex_marker + four_pillars",
        "outcome custodian",
        "intake operator",
        "runner operator",
        "两名独立人类 reviewer",
        "第三方 adjudicator",
        "整批 STOP",
    ):
        assert required_text in protocol

    assert template["schema_version"] == "prospective-observation/v1"
    assert template["prediction_fields_forbidden"] is True
    record = template["record_template"]
    assert set(record) == {
        "case_id",
        "task_id",
        "label",
        "observed_at",
        "observation_window",
        "source_refs",
        "quantifiable",
        "conflict_state",
        "custodian",
    }
    serialized = json.dumps(template, ensure_ascii=False).lower()
    assert "probability" not in serialized
    assert "runner_output" not in serialized
    assert "report_text" not in serialized


def test_first_batch_assigns_career_binary_timing_and_rotating_high_risk_tasks() -> None:
    assignments = _read_json(TASKS_BY_CASE)
    expected_case_ids = {f"P-GO-2026-{index:03d}" for index in range(1, 11)}

    assert set(assignments) == expected_case_ids
    assigned_high_risk: set[str] = set()
    for case_id, task_ids in assignments.items():
        assert len(task_ids) == len(set(task_ids))
        assert set(task_ids) <= set(APPROVED_TASK_IDS)
        assert "career.role_change" in task_ids
        assert TIMING_TASK_IDS & set(task_ids)
        assigned_high_risk.update(HIGH_RISK_REVIEW_TASK_IDS & set(task_ids))
    assert assigned_high_risk == HIGH_RISK_REVIEW_TASK_IDS


def test_timing_assignment_requires_real_canonical_liunian_steps(tmp_path: Path) -> None:
    case_id = "P-GO-2026-001"
    input_path = tmp_path / case_id / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n", encoding="utf-8")
    tasks = _read_json(GO_TASK_CATALOG)

    intake = register_prospective_intake(
        [input_path],
        tasks,
        ["ren", "duan"],
        "human-intake-01",
        tasks_by_case={case_id: ["career.role_change", "career.change_window"]},
    )

    assert intake["records"][0]["task_ids"] == ["career.change_window", "career.role_change"]
    # Task 1 freezes the protocol: assigning timing is not evidence that annual facts exist.
    # The real batch remains HOLD until canonical chart parsing yields non-empty liunian_steps.
    assert _gate_status(
        subject_hashes=[f"subject-{index:02d}" for index in range(30)],
        binary_labels={"career.role_change": ["occurred"] * 10 + ["not_observed"] * 10},
        timing_assignments={"career.change_window": []},
        high_risk_labels=[],
    ) == "HOLD"
