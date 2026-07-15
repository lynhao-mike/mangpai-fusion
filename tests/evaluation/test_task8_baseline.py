from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.evaluation.freeze import verify_frozen_run
from engine.evaluation.models import FrozenBlindRun
from tools.school_capability_task8 import (
    APPROVED_SCHOOLS,
    APPROVED_TASK_IDS,
    build_stage_a,
    build_stage_b_inputs,
    canonical_digest,
)


def _source(path: Path) -> Path:
    path.write_text(
        """## P-2026-001 · 乾 · 戊申癸亥戊戌癸亥
- 公历生日：1968-11-24 22:33
- 四柱：戊申 癸亥 戊戌 癸亥
- 大运：5岁起运；甲子→乙丑→丙寅
""",
        encoding="utf-8",
    )
    return path


def test_stage_a_builds_catalog_derived_six_school_ten_task_grid(tmp_path: Path) -> None:
    rules = tmp_path / "claim-rules-v1.yaml"
    rules.write_text("schema_version: claim-executable-rules/v1\nrules: []\n", encoding="utf-8")

    result = build_stage_a(
        source=_source(tmp_path / "input.md"),
        catalog_path=Path("mapping/school-capability-task-catalog-v1.yaml"),
        rules_path=rules,
        frozen_at="2026-07-15T12:00:00Z",
    )

    run = FrozenBlindRun.from_dict(result["historical_batch"]["frozen_run"])
    verify_frozen_run(run)
    assert len(run.outputs) == len(APPROVED_SCHOOLS) * len(APPROVED_TASK_IDS)
    assert {row.school_id for row in run.outputs} == set(APPROVED_SCHOOLS)
    assert {row.task_id for row in run.outputs} == set(APPROVED_TASK_IDS)
    assert result["rule_snapshot"]["rule_snapshot_id"].endswith(hashlib.sha256(rules.read_bytes()).hexdigest())
    assert "@sha256:" in run.task_catalog_version
    assert "@sha256:" in run.rule_snapshot_id


def test_stage_b_rebinds_six_school_routes_without_mutating_labels(tmp_path: Path) -> None:
    rules = tmp_path / "claim-rules-v1.yaml"
    rules.write_text("schema_version: claim-executable-rules/v1\nrules: []\n", encoding="utf-8")
    stage_a = build_stage_a(
        source=_source(tmp_path / "input.md"),
        catalog_path=Path("mapping/school-capability-task-catalog-v1.yaml"),
        rules_path=rules,
        frozen_at="2026-07-15T12:00:00Z",
    )
    case_id = stage_a["historical_batch"]["cases"][0]["case_id"]
    label = {
        "case_id": case_id,
        "task_id": "career.role_change",
        "label": "occurred",
        "source": "cases/fankui-feedback.md:94",
        "observed_at": "2026-07-14",
        "confidence_grade": "B",
        "quantifiable": True,
        "conflict_state": "none",
        "reviewer": "human-reviewer-01",
    }
    labels_doc = {"schema_version": "school-capability-labels/v1", "freeze_hash": "old", "labels": [label]}
    reviewed = {
        "schema_version": "school-capability-case-manifest/v1",
        "generated_at": "2026-07-14T15:21:00Z",
        "reviewed_by": "human-reviewer-01",
        "expected_schools": ["ren", "ziping"],
        "records": [],
    }

    result = build_stage_b_inputs(
        historical_batch=stage_a["historical_batch"],
        cli_tasks=stage_a["cli_tasks"],
        labels_doc=labels_doc,
        reviewed_manifest=reviewed,
        evaluated_at="2026-07-15T12:01:00Z",
    )

    assert result["labels"]["labels"] == [label]
    assert result["labels"]["freeze_hash"] == stage_a["historical_batch"]["frozen_run"]["freeze_hash"]
    assert result["manifest"]["expected_schools"] == list(APPROVED_SCHOOLS)
    routes = result["manifest"]["records"][0]["eligible_routes"]
    assert len(routes) == len(APPROVED_SCHOOLS) * len(APPROVED_TASK_IDS)
    assert {route["school_id"] for route in routes} == set(APPROVED_SCHOOLS)
    assert {route["task_id"] for route in routes} == set(APPROVED_TASK_IDS)
    assert result["failure_counts"]["label_quality"] == 0


def test_high_risk_label_without_a_grade_and_secondary_review_is_held(tmp_path: Path) -> None:
    rules = tmp_path / "claim-rules-v1.yaml"
    rules.write_text("schema_version: claim-executable-rules/v1\nrules: []\n", encoding="utf-8")
    stage_a = build_stage_a(
        source=_source(tmp_path / "input.md"),
        catalog_path=Path("mapping/school-capability-task-catalog-v1.yaml"),
        rules_path=rules,
        frozen_at="2026-07-15T12:00:00Z",
    )
    case_id = stage_a["historical_batch"]["cases"][0]["case_id"]
    label = {
        "case_id": case_id,
        "task_id": "wealth.debt",
        "label": "occurred",
        "source": "cases/fankui-feedback.md:94",
        "observed_at": "2026-07-14",
        "confidence_grade": "B",
        "quantifiable": True,
        "conflict_state": "none",
        "reviewer": "human-reviewer-01",
    }
    result = build_stage_b_inputs(
        historical_batch=stage_a["historical_batch"],
        cli_tasks=stage_a["cli_tasks"],
        labels_doc={"schema_version": "school-capability-labels/v1", "freeze_hash": "old", "labels": [label]},
        reviewed_manifest={"reviewed_by": "human-reviewer-01"},
        evaluated_at="2026-07-15T12:01:00Z",
    )

    assert result["labels"]["labels"] == []
    assert result["manifest"]["records"][0]["eligibility"] == "development_only"
    assert result["failure_counts"]["label_quality"] == len(APPROVED_SCHOOLS)


def test_canonical_digest_is_order_independent() -> None:
    assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})
    assert len(canonical_digest(json.loads('{"a":1}'))) == 64
