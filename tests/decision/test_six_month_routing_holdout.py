from __future__ import annotations

import hashlib
import json

import pytest

from tools.l1_routing_holdout_audit import (
    adapt_six_month_baseline,
    build_audit_artifact,
    render_audit_report,
)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _baseline() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for case_id, observed in (
        ("P-001-乾-甲子乙丑丙寅丁卯", True),
        ("P-002-坤-戊辰己巳庚午辛未", False),
        ("P-003-乾-壬申癸酉甲戌乙亥", True),
        ("P-004-坤-丙子丁丑戊寅己卯", False),
    ):
        for school, utility in (("ziping", 0.6), ("duan", 0.4)):
            rows.append({
                "case_id": case_id,
                "school_id": school,
                "task_id": "career.role_change",
                "claim_type": "binary_event",
                "state": "claim",
                "abstained": False,
                "knowledge_coverage": True,
                "chart_prototype_id": "prototype-provisional",
                "time_horizon": "ten_year",
                "evidence_completeness_band": "complete",
                "probability_score": 0.7 if observed else 0.3,
                "timing_score": None,
                "ordinal_score": None,
                "portrait_agreement": None,
                "utility": utility,
                "observed_positive": observed,
            })
    payload: dict[str, object] = {
        "schema_version": "six-month-capability-baseline/v1",
        "generated_at": "2026-07-15T12:43:00Z",
        "classification": "historical_blind_candidate",
        "freeze_hash": "freeze-task8",
        "task_ids": ["career.role_change"],
        "scores": rows,
        "provenance": {"freeze_hash": "freeze-task8"},
    }
    payload["artifact_digest"] = f"sha256:{_digest(payload)}"
    return payload


def _cases() -> list[dict[str, object]]:
    return [
        {"case_id": "P-001-乾-甲子乙丑丙寅丁卯", "sex_marker": "乾", "four_pillars": ["甲子", "乙丑", "丙寅", "丁卯"]},
        {"case_id": "P-002-坤-戊辰己巳庚午辛未", "sex_marker": "坤", "four_pillars": ["戊辰", "己巳", "庚午", "辛未"]},
        {"case_id": "P-003-乾-壬申癸酉甲戌乙亥", "sex_marker": "乾", "four_pillars": ["壬申", "癸酉", "甲戌", "乙亥"]},
        {"case_id": "P-004-坤-丙子丁丑戊寅己卯", "sex_marker": "坤", "four_pillars": ["丙子", "丁丑", "戊寅", "己卯"]},
    ]


def test_task8_baseline_is_safely_adapted_without_changing_schema_identity() -> None:
    batch, scores = adapt_six_month_baseline(_baseline(), _cases())

    assert batch["schema_version"] == "school-capability-historical-batch/v1"
    assert scores["schema_version"] == "school-capability-historical-scores/v1"
    assert batch["frozen_run"]["freeze_hash"] == "freeze-task8"
    assert scores["freeze_hash"] == "freeze-task8"
    assert [row["case_id"] for row in batch["cases"]] == [row["case_id"] for row in _cases()]
    assert all(row["sex_marker"] and len(row["four_pillars"]) == 4 for row in batch["cases"])


def test_task8_adapter_rejects_untrusted_or_incomplete_case_facts() -> None:
    baseline = _baseline()
    baseline["artifact_digest"] = "sha256:tampered"
    with pytest.raises(ValueError, match="artifact digest"):
        adapt_six_month_baseline(baseline, _cases())

    with pytest.raises(ValueError, match="路由审计输入不完整"):
        adapt_six_month_baseline(_baseline(), _cases()[:-1])


def test_task9_artifact_has_dynamic_baseline_governance_fields_and_holds_single_class() -> None:
    batch, scores = adapt_six_month_baseline(_baseline(), _cases())
    artifact = build_audit_artifact(
        batch,
        scores,
        holdout_fraction=0.25,
        salt="six-month-l1-routing-v1",
        minimum_competitive_cases=1,
        static_school_by_task={"career.role_change": "ziping"},
        static_baseline_source="mapping/school-capability-runner-coverage-v1.yaml",
        source_baseline="META/six-month-capability-baseline-2026-07-15.json",
        source_artifact_digest=str(_baseline()["artifact_digest"]),
        classification="historical_blind_candidate",
        generated_at="2026-07-15T13:00:00Z",
        high_risk_task_ids={"wealth.debt"},
    )

    required = {
        "source_baseline", "source_artifact_digest", "classification",
        "static_school_by_task", "training_capability_snapshot_id",
        "calibration_audit", "high_risk_audit", "label_distribution_by_task",
        "prototype_incremental_evidence", "gate_reasons", "generated_at", "artifact_digest",
    }
    assert required <= artifact.keys()
    assert artifact["split"]["salt"] == "six-month-l1-routing-v1"
    assert set(artifact["split"]["training_case_ids"]).isdisjoint(artifact["split"]["holdout_case_ids"])
    assert artifact["competitive_coverage"]["competitive_by_task"]
    assert artifact["competitive_coverage"]["competitive_identities"][0]["schools"] == ["duan", "ziping"]
    assert artifact["route_comparison"]["selection_changes"] == 0
    assert artifact["calibration_audit"]["status"] == "insufficient"
    assert artifact["high_risk_audit"]["assessable_record_count"] == 0
    assert artifact["gate_status"] == "HOLD"
    assert any("单一" in reason or "正负" in reason for reason in artifact["gate_reasons"])

    report = render_audit_report(artifact)
    assert "static baseline 来源与映射" in report
    assert "historical blind candidate" in report
    assert "一个任务、两个流派" not in report
