from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY
from tools.school_capability_dataset import prepare_blind_bundle, register_prospective_intake


YAML_TASK_CATALOG = Path("mapping/school-capability-task-catalog-v1.yaml")
LEGACY_PROSPECTIVE_TASK_CATALOG = Path("META/school-capability-prospective-tasks-v1.json")
GO_TASK_CATALOG = Path("META/prospective-go-task-catalog-v1.json")
GO_RULE_SNAPSHOT = Path("META/prospective-go-rule-snapshot-v1.json")
PROTOCOL = Path("META/prospective-intake-protocol-v1.md")
ACTION_PLAN = Path("plans/upgrade-guides/post-gate-action-plan-2026-07-15.md")
TOOLS_README = Path("tools/README.md")
HANDOFF = Path("handoff.md")
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


def test_go_rule_snapshot_freezes_six_real_runners_and_ten_task_catalog() -> None:
    snapshot = _read_json(GO_RULE_SNAPSHOT)
    catalog_bytes = GO_TASK_CATALOG.read_bytes()

    assert snapshot["schema_version"] == "prospective-go-rule-snapshot/v1"
    assert snapshot["rule_snapshot_id"] == "prospective-go-six-source-ten-task-rules-v1"
    assert snapshot["schools"] == ["ziping", "ditiansui", "duan", "ren", "gao", "yang"]
    assert set(snapshot["runners"]) == set(snapshot["schools"])
    assert snapshot["feature_schema"] == "cfv-v1"
    assert snapshot["task_catalog"] == GO_TASK_CATALOG.as_posix()
    assert snapshot["task_catalog_summary"] == {
        "schema_version": "school-capability-cli-tasks/v1",
        "task_catalog_version": "prospective-go-tasks-v1",
        "task_ids": list(APPROVED_TASK_IDS),
        "sha256": hashlib.sha256(catalog_bytes).hexdigest(),
    }

    tasks = _read_json(GO_TASK_CATALOG)["tasks"]
    for school, dotted_path in snapshot["runners"].items():
        module_name, function_name = dotted_path.rsplit(".", 1)
        runner = getattr(importlib.import_module(module_name), function_name)
        registered = [
            task["task_id"]
            for task in tasks
            if DEFAULT_RUNNER_REGISTRY.resolve(school, task["task_id"]) is runner
        ]
        assert registered, f"{school} snapshot runner has no registered GO task"


def test_prepare_blind_consumes_go_rule_snapshot_id(tmp_path: Path) -> None:
    case_id = "P-GO-2026-001-乾-甲子乙丑丙寅丁卯"
    input_path = tmp_path / case_id / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n", encoding="utf-8")
    schools = ["ziping", "ditiansui", "duan", "ren", "gao", "yang"]
    intake = register_prospective_intake(
        [input_path], _read_json(GO_TASK_CATALOG), schools, "human-intake-01"
    )
    bundle_dir = tmp_path / "bundle"

    prepare_blind_bundle(intake, GO_TASK_CATALOG, GO_RULE_SNAPSHOT, bundle_dir)

    rule_reference = _read_json(bundle_dir / "rule-snapshot.json")
    assert rule_reference["rule_snapshot_id"] == "prospective-go-six-source-ten-task-rules-v1"
    assert rule_reference["sha256"] == hashlib.sha256(GO_RULE_SNAPSHOT.read_bytes()).hexdigest()


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


def test_protocol_documents_single_case_order_ledgers_and_three_isolated_gates() -> None:
    protocol = PROTOCOL.read_text(encoding="utf-8")

    for required_text in (
        "每案 dry-run 后当天正式 single-case intake",
        "不等待 10 案",
        "恰好 1 个",
        "三个月内",
        "每案独立 bundle / freeze / witness / verification",
        "VERIFIED 前禁止反馈释放",
        "prediction_first_immediate_retrospective",
        "future_observation",
        "完成数完全分账",
        "每 10 案只聚合父引用",
        "prediction_capability_candidate_gate_v1",
        "future_empirical_gate_v1",
        "historical_platform_baseline_2026_07_15",
        "只读独立 HOLD",
        "独立人类见证人",
        "人工硬停点",
        "不得自动切换生产入口",
    ):
        assert required_text in protocol


def test_action_plan_replaces_batch_blocking_with_single_case_and_split_gate_rhythm() -> None:
    plan = ACTION_PLAN.read_text(encoding="utf-8")
    task3 = plan.split("## Task 3:", 1)[1].split("## Task 4:", 1)[0]
    task4 = plan.split("## Task 4:", 1)[1].split("## Task 5:", 1)[0]
    task5 = plan.split("## Task 5:", 1)[1].split("## Task 6:", 1)[0]
    tasks7_to_10 = plan.split("## Task 7:", 1)[1].split("## Task 11:", 1)[0]
    task11 = plan.split("## Task 11:", 1)[1]

    assert "每案 dry-run 后当天正式 single-case intake" in task3
    assert "满 10 案后正式写 intake" not in task3
    assert "每案独立 bundle / freeze / witness / verification" in task4
    assert "恰好 1 个" in task5 and "三个月内" in task5
    assert "prediction_capability_candidate_gate_v1" in tasks7_to_10
    assert "future_empirical_gate_v1" in tasks7_to_10
    assert "prediction_first_immediate_retrospective" in tasks7_to_10
    assert "future_observation" in tasks7_to_10
    assert "historical_platform_baseline_2026_07_15" in task11
    assert "只读" in task11
    assert "20 immediate + 10 future" in task11
    assert "production_switch=false" in task11


def test_tools_index_registers_real_single_case_and_cohort_cli_as_offline_only() -> None:
    text = TOOLS_README.read_text(encoding="utf-8")

    assert "[`school_capability_cohort.py`](school_capability_cohort.py:1)" in text
    for command in (
        "single-case-intake",
        "prepare-single-case-blind",
        "stage-single-case-frozen-run",
        "witness-freeze-chain",
        "witness-verify-single-case",
        "issue-feedback-release",
        "release-immediate-retrospective-template",
        "collect-immediate-retrospective",
        "collect-future-observation",
        "build-case-completion",
        "tools.school_capability_cohort build",
        "tools.school_capability_cohort gate",
        "tools.school_capability_cohort future-gate",
        "tools.school_capability_cohort report",
    ):
        assert command in text
    assert "所有写操作先 dry-run，人工确认后才正式执行" in text
    assert "仅离线评估" in text
    assert "production_switch=false" in text
    assert 'set "SCHOOL_CAPABILITY_WITNESS_KEY="' in text
    assert "NOT SET" in text


def test_handoff_names_first_legal_case_action_and_all_independent_holds() -> None:
    handoff = HANDOFF.read_text(encoding="utf-8")

    assert "首案" in handoff
    assert "当天正式 single-case intake" in handoff
    assert "不等待 10 案" in handoff
    assert "人工硬停点" in handoff
    assert "verification=VERIFIED 前禁止反馈释放" in handoff
    assert "prediction_capability_candidate_gate_v1 = HOLD" in handoff
    assert "future_empirical_gate_v1 = HOLD" in handoff
    assert "historical_platform_baseline_2026_07_15 = HOLD" in handoff
    assert "只读" in handoff
    assert "static" in handoff
    assert "production_switch=false" in handoff
    assert "离线 GO 不代表平台 GO 或生产 GO" in handoff


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


def test_short_prospective_slot_assigns_tasks_to_unique_full_case_id(tmp_path: Path) -> None:
    slot_id = "P-GO-2026-001"
    case_id = f"{slot_id}-乾-甲子乙丑丙寅丁卯"
    input_path = tmp_path / case_id / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n", encoding="utf-8")

    intake = register_prospective_intake(
        [input_path],
        _read_json(GO_TASK_CATALOG),
        ["ren", "duan"],
        "human-intake-01",
        tasks_by_case={slot_id: ["career.role_change", "career.change_window"]},
    )

    assert intake["records"][0]["case_id"] == case_id
    assert intake["records"][0]["task_ids"] == ["career.change_window", "career.role_change"]


@pytest.mark.parametrize("arrived_count", [1, 5])
def test_frozen_ten_slot_table_allows_not_yet_arrived_same_batch_slots(
    tmp_path: Path, arrived_count: int,
) -> None:
    assignments = _read_json(TASKS_BY_CASE)
    charts = (
        ("乾", "甲子 乙丑 丙寅 丁卯"),
        ("坤", "戊辰 己巳 庚午 辛未"),
        ("乾", "壬申 癸酉 甲戌 乙亥"),
        ("坤", "丙子 丁丑 戊寅 己卯"),
        ("乾", "庚辰 辛巳 壬午 癸未"),
    )
    input_paths = []
    expected_tasks: dict[str, list[str]] = {}
    for index, (sex_marker, pillars) in enumerate(charts[:arrived_count], start=1):
        slot_id = f"P-GO-2026-{index:03d}"
        compact_pillars = pillars.replace(" ", "")
        case_id = f"{slot_id}-{sex_marker}-{compact_pillars}"
        input_path = tmp_path / case_id / "input.md"
        input_path.parent.mkdir(parents=True)
        input_path.write_text(f"四柱：{pillars}\n性别：{sex_marker}\n", encoding="utf-8")
        input_paths.append(input_path)
        expected_tasks[case_id] = sorted(assignments[slot_id])

    intake = register_prospective_intake(
        input_paths,
        _read_json(GO_TASK_CATALOG),
        ["ziping", "ditiansui", "duan", "ren", "gao", "yang"],
        "human-intake-01",
        tasks_by_case=assignments,
    )

    assert len(intake["records"]) == arrived_count
    assert {row["case_id"]: row["task_ids"] for row in intake["records"]} == expected_tasks


def test_full_prospective_case_key_still_assigns_tasks(tmp_path: Path) -> None:
    case_id = "P-GO-2026-001-乾-甲子乙丑丙寅丁卯"
    input_path = tmp_path / case_id / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n", encoding="utf-8")

    intake = register_prospective_intake(
        [input_path],
        _read_json(GO_TASK_CATALOG),
        ["ren", "duan"],
        "human-intake-01",
        tasks_by_case={case_id: ["career.role_change"]},
    )

    assert intake["records"][0]["task_ids"] == ["career.role_change"]


def test_short_prospective_slot_rejects_ambiguous_full_case_ids(tmp_path: Path) -> None:
    slot_id = "P-GO-2026-001"
    input_paths = []
    for suffix, chart in (
        ("乾-甲子乙丑丙寅丁卯", "四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n"),
        ("坤-戊辰己巳庚午辛未", "四柱：戊辰 己巳 庚午 辛未\n性别：坤\n"),
    ):
        input_path = tmp_path / f"{slot_id}-{suffix}" / "input.md"
        input_path.parent.mkdir(parents=True)
        input_path.write_text(chart, encoding="utf-8")
        input_paths.append(input_path)

    with pytest.raises(ValueError, match="ambiguous tasks_by_case slot"):
        register_prospective_intake(
            input_paths,
            _read_json(GO_TASK_CATALOG),
            ["ren", "duan"],
            "human-intake-01",
            tasks_by_case={slot_id: ["career.role_change"]},
        )


def test_short_prospective_slot_rejects_unknown_slot(tmp_path: Path) -> None:
    case_id = "P-GO-2026-001-乾-甲子乙丑丙寅丁卯"
    input_path = tmp_path / case_id / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n", encoding="utf-8")

    with pytest.raises(ValueError, match="tasks_by_case references unknown case: P-GO-2026-999"):
        register_prospective_intake(
            [input_path],
            _read_json(GO_TASK_CATALOG),
            ["ren", "duan"],
            "human-intake-01",
            tasks_by_case={"P-GO-2026-999": ["career.role_change"]},
        )


@pytest.mark.parametrize(
    ("assignments", "expected_error"),
    [
        ({"P-GO-2026-01": ["career.role_change"]}, "tasks_by_case references unknown case"),
        (
            {
                "P-GO-2026-001": ["career.role_change"],
                "P-GO-2026-003": ["career.change_window"],
            },
            "tasks_by_case references unknown case: P-GO-2026-003",
        ),
        (
            {
                "P-GO-2027-001": ["career.role_change"],
                "P-GO-2027-002": ["career.change_window"],
            },
            "tasks_by_case references unknown case: P-GO-2027-001",
        ),
        (
            {"P-GO-2026-999-乾-甲子乙丑丙寅丁卯": ["career.role_change"]},
            "tasks_by_case references unknown case",
        ),
    ],
)
def test_not_yet_arrived_exception_rejects_malformed_gapped_cross_batch_and_full_keys(
    tmp_path: Path, assignments: dict[str, list[str]], expected_error: str,
) -> None:
    case_id = "P-GO-2026-001-乾-甲子乙丑丙寅丁卯"
    input_path = tmp_path / case_id / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n", encoding="utf-8")

    with pytest.raises(ValueError, match=expected_error):
        register_prospective_intake(
            [input_path],
            _read_json(GO_TASK_CATALOG),
            ["ren", "duan"],
            "human-intake-01",
            tasks_by_case=assignments,
        )


def test_tasks_by_case_rejects_short_and_full_keys_resolving_same_case(tmp_path: Path) -> None:
    slot_id = "P-GO-2026-001"
    case_id = f"{slot_id}-乾-甲子乙丑丙寅丁卯"
    input_path = tmp_path / case_id / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate tasks_by_case resolution"):
        register_prospective_intake(
            [input_path],
            _read_json(GO_TASK_CATALOG),
            ["ren", "duan"],
            "human-intake-01",
            tasks_by_case={
                slot_id: ["career.change_window"],
                case_id: ["career.role_change"],
            },
        )
