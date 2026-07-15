from pathlib import Path

import yaml

from engine.evaluation.task_catalog import load_task_catalog, task_by_id


TASK_CATALOG_PATH = Path("mapping/school-capability-task-catalog-v1.yaml")
COVERAGE_PATH = Path("mapping/school-capability-runner-coverage-v1.yaml")

APPROVED_COVERAGE = {
    "structure.overview": {
        "claim_type": "structure_claim",
        "primary_schools": ["ziping"],
        "supporting_schools": ["ditiansui"],
    },
    "career.role_change": {
        "claim_type": "binary_event",
        "primary_schools": ["ziping"],
        "supporting_schools": ["duan"],
    },
    "marriage.divorce_or_remarriage": {
        "claim_type": "binary_event",
        "primary_schools": ["yang"],
        "supporting_schools": ["duan"],
    },
    "wealth.debt": {
        "claim_type": "binary_event",
        "primary_schools": ["duan"],
        "supporting_schools": ["gao"],
    },
    "career.path_type": {
        "claim_type": "categorical_state",
        "primary_schools": ["duan"],
        "supporting_schools": ["ziping"],
    },
    "health.system_risk": {
        "claim_type": "categorical_state",
        "primary_schools": ["gao"],
        "supporting_schools": ["ren"],
    },
    "career.change_window": {
        "claim_type": "event_timing",
        "primary_schools": ["ren", "duan"],
        "supporting_schools": ["gao"],
    },
    "marriage.event_window": {
        "claim_type": "event_timing",
        "primary_schools": ["ren", "duan"],
        "supporting_schools": ["gao"],
    },
    "health.event_window": {
        "claim_type": "event_timing",
        "primary_schools": ["ren", "duan"],
        "supporting_schools": ["gao"],
    },
    "wealth.major_loss_window": {
        "claim_type": "event_timing",
        "primary_schools": ["ren", "duan"],
        "supporting_schools": ["gao"],
    },
}

HIGH_RISK_TASK_IDS = {
    "marriage.divorce_or_remarriage",
    "wealth.debt",
    "health.system_risk",
    "health.event_window",
    "wealth.major_loss_window",
}
TIMING_TASK_IDS = {
    "career.change_window",
    "marriage.event_window",
    "health.event_window",
    "wealth.major_loss_window",
}
REQUIRED_COVERAGE_FIELDS = {
    "task_id",
    "claim_type",
    "primary_schools",
    "supporting_schools",
    "delivery_batch",
    "high_risk",
}


def _load_coverage() -> list[dict[str, object]]:
    raw = yaml.safe_load(COVERAGE_PATH.read_text(encoding="utf-8"))
    assert raw["schema_version"] == "school-capability-runner-coverage/v1"
    assert isinstance(raw["coverage"], list)
    return raw["coverage"]


def test_approved_six_month_tasks_exist_once_and_keep_high_risk_flags() -> None:
    tasks = load_task_catalog(TASK_CATALOG_PATH)
    indexed = task_by_id(tasks)

    assert set(APPROVED_COVERAGE) <= set(indexed)
    assert len([task.task_id for task in tasks if task.task_id in APPROVED_COVERAGE]) == 10
    assert {task_id for task_id in APPROVED_COVERAGE if indexed[task_id].high_risk} == HIGH_RISK_TASK_IDS


def test_runner_coverage_contains_only_the_approved_matrix() -> None:
    coverage = _load_coverage()
    coverage_ids = [item["task_id"] for item in coverage]

    assert len(coverage_ids) == len(set(coverage_ids)) == 10
    assert set(coverage_ids) == set(APPROVED_COVERAGE)
    for item in coverage:
        assert set(item) == REQUIRED_COVERAGE_FIELDS
        task_id = item["task_id"]
        expected = APPROVED_COVERAGE[task_id]
        assert item["claim_type"] == expected["claim_type"]
        assert item["primary_schools"] == expected["primary_schools"]
        assert item["supporting_schools"] == expected["supporting_schools"]
        assert item["high_risk"] is (task_id in HIGH_RISK_TASK_IDS)


def test_timing_tasks_keep_ren_and_duan_in_batch_1_and_gao_in_batch_2() -> None:
    coverage = {item["task_id"]: item for item in _load_coverage()}

    for task_id in TIMING_TASK_IDS:
        item = coverage[task_id]
        assert item["primary_schools"] == ["ren", "duan"]
        assert item["delivery_batch"] == {
            "ren": "batch_1",
            "duan": "batch_1",
            "gao": "batch_2",
        }
