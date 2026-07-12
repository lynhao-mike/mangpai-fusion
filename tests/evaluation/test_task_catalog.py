from pathlib import Path

import pytest

from engine.evaluation.task_catalog import load_task_catalog, task_by_id


def _write_task_catalog(tmp_path: Path, **overrides: object) -> Path:
    task = {
        "task_id": "marriage.divorce",
        "domain": "婚姻",
        "claim_type": "binary_event",
        "scoring_method": "binary_probability",
        "quantifiable": True,
        "high_risk": True,
        "allowed_time_horizons": ["lifetime"],
        "required_input_fields": ["four_pillars"],
        "label_schema": {"type": "boolean"},
        "evaluation_note": "test",
        **overrides,
    }
    path = tmp_path / "tasks.yaml"
    import yaml

    path.write_text(
        yaml.safe_dump(
            {"schema_version": "school-capability-tasks/v1", "tasks": [task]},
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


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


@pytest.mark.parametrize("domain", ["", None, 42])
def test_catalog_rejects_empty_null_or_non_string_domain(tmp_path: Path, domain: object) -> None:
    with pytest.raises(ValueError, match="domain must be a non-empty string"):
        load_task_catalog(_write_task_catalog(tmp_path, domain=domain))


def test_catalog_rejects_unsupported_scorer(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported scoring_method: made_up_scorer"):
        load_task_catalog(_write_task_catalog(tmp_path, scoring_method="made_up_scorer"))


def test_catalog_rejects_non_mapping_label_schema(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="label_schema must be a mapping"):
        load_task_catalog(_write_task_catalog(tmp_path, label_schema=["truthy"]))


def test_task_by_id_indexes_tasks() -> None:
    tasks = load_task_catalog(Path("mapping/school-capability-task-catalog-v1.yaml"))
    indexed = task_by_id(tasks)
    assert indexed["marriage.late_marriage"] is tasks[0]


def test_task_by_id_rejects_duplicate_ids() -> None:
    task = load_task_catalog(Path("mapping/school-capability-task-catalog-v1.yaml"))[0]
    with pytest.raises(ValueError, match=f"duplicate task_id: {task.task_id}"):
        task_by_id([task, task])
