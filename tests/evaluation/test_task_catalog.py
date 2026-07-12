from pathlib import Path

import pytest

from engine.evaluation.task_catalog import load_task_catalog, task_by_id


def test_catalog_has_unique_ids_and_supported_scorers() -> None:
    tasks = load_task_catalog(Path("mapping/school-capability-task-catalog-v1.yaml"))
    assert 15 <= len(tasks) <= 25
    assert len({task.task_id for task in tasks}) == len(tasks)
    assert {task.domain for task in tasks} >= {"婚姻", "财富", "事业", "学业", "健康", "性格"}
    assert {task.scoring_method for task in tasks} <= {
        "binary_probability",
        "multiclass_probability",
        "ordinal",
        "time_window",
        "portrait_agreement",
    }


def test_catalog_rejects_probability_task_without_label_schema(tmp_path: Path) -> None:
    path = tmp_path / "tasks.yaml"
    path.write_text(
        "schema_version: school-capability-tasks/v1\ntasks:\n"
        "  - task_id: marriage.divorce\n"
        "    domain: 婚姻\n"
        "    claim_type: binary_event\n"
        "    scoring_method: binary_probability\n"
        "    quantifiable: true\n"
        "    high_risk: true\n"
        "    allowed_time_horizons: [lifetime]\n"
        "    required_input_fields: [four_pillars]\n"
        "    label_schema: {}\n"
        "    evaluation_note: test\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="label_schema"):
        load_task_catalog(path)


def test_catalog_rejects_duplicate_task_ids(tmp_path: Path) -> None:
    path = tmp_path / "tasks.yaml"
    task = (
        "  - task_id: duplicate.task\n"
        "    domain: 婚姻\n"
        "    claim_type: portrait\n"
        "    scoring_method: portrait_agreement\n"
        "    quantifiable: false\n"
        "    high_risk: false\n"
        "    allowed_time_horizons: [lifetime]\n"
        "    required_input_fields: [four_pillars]\n"
        "    label_schema: {}\n"
        "    evaluation_note: test\n"
    )
    path.write_text(
        "schema_version: school-capability-tasks/v1\ntasks:\n" + task + task,
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate task_id"):
        load_task_catalog(path)


def test_task_by_id_indexes_tasks() -> None:
    tasks = load_task_catalog(Path("mapping/school-capability-task-catalog-v1.yaml"))
    indexed = task_by_id(tasks)
    assert indexed["marriage.late_marriage"] is tasks[0]
