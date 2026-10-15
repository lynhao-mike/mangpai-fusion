from __future__ import annotations

import pytest

from engine.statement_runtime import (
    build_statement_records_envelope,
    build_statement_records_v2_envelope,
)


def test_v1_statement_record_keeps_legacy_schema_without_v2_fields() -> None:
    envelope = build_statement_records_envelope(
        {
            "production_rule_conclusions": [
                {
                    "statement_id": "stmt-career-001",
                    "statement": "事业有阶段性提升。",
                    "rule_id": "ZP-CAREER-001",
                    "school": "子平",
                    "section": "事业",
                    "matter_category": "事业",
                    "rule_direction": "support",
                }
            ]
        },
        "C-TEST-STATEMENT-RUNTIME",
        generated_at="2026-10-14T00:00:00Z",
    )

    assert envelope["schema_version"] == "statement_record.v1"
    assert envelope["statement_records_generated"] == 1
    record = envelope["records"][0]
    assert {"section", "matter_category", "rule_direction", "run_id"}.isdisjoint(record)


def test_v1_statement_record_ignores_v2_identity_fields() -> None:
    envelope = build_statement_records_envelope(
        {
            "production_rule_conclusions": [
                {
                    "statement_id": "stmt-legacy-001",
                    "statement": "旧记录断语。",
                    "rule_id": "LEGACY-001",
                }
            ]
        },
        "C-TEST-STATEMENT-LEGACY",
        generated_at="2026-10-14T00:00:00Z",
    )

    record = envelope["records"][0]
    assert envelope["schema_version"] == "statement_record.v1"
    assert {"section", "matter_category", "rule_direction", "run_id"}.isdisjoint(record)


def test_v2_statement_records_split_rules_and_bind_run_identity() -> None:
    envelope = build_statement_records_v2_envelope(
        {
            "production_rule_conclusions": [
                {
                    "statement_id": "visible-statement-id",
                    "statement": "职业方向明确。",
                    "section": "事业",
                    "matter_category": "career",
                    "rule_direction": "positive",
                    "evidence": [
                        {"rule_id": "ZP-PROD-CAREER-001", "school": "子平"},
                        {"rule_id": "DTS-PROD-CAREER-002", "school": "滴天髓"},
                    ],
                }
            ]
        },
        "C-TEST-STATEMENT-V2",
        run_id="run-test-001",
        generated_at="2026-10-14T00:00:00Z",
    )

    assert envelope["schema_version"] == "statement_record.v2"
    assert {record["rule_id"] for record in envelope["records"]} == {
        "ZP-PROD-CAREER-001",
        "DTS-PROD-CAREER-002",
    }
    assert len({record["statement_id"] for record in envelope["records"]}) == 2
    assert all(record["run_id"] == "run-test-001" for record in envelope["records"])
    assert all(record["matter_category"] == "career" for record in envelope["records"])


def test_v2_statement_records_reject_missing_structured_learning_identity() -> None:
    with pytest.raises(ValueError, match="matter_category"):
        build_statement_records_v2_envelope(
            {
                "production_rule_conclusions": [
                    {
                        "statement_id": "not-an-identity-source",
                        "statement": "文本不能代替结构化字段。",
                        "section": "career",
                        "evidence": [{"rule_id": "ZP-PROD-CAREER-001"}],
                    }
                ]
            },
            "C-TEST-STATEMENT-V2-MISSING",
            run_id="run-test-002",
            generated_at="2026-10-14T00:00:00Z",
        )


def test_v2_statement_records_reject_conflicting_directions_for_same_rule() -> None:
    with pytest.raises(ValueError, match="conflicting rule_direction"):
        build_statement_records_v2_envelope(
            {
                "production_rule_conclusions": [
                    {
                        "statement": "同一规则不能在同一事项被重复计为相反方向。",
                        "section": "事业",
                        "matter_category": "career",
                        "rule_direction": "positive",
                        "evidence": [
                            {
                                "rule_id": "ZP-PROD-CAREER-003",
                                "school": "子平",
                                "rule_direction": "positive",
                            },
                            {
                                "rule_id": "ZP-PROD-CAREER-003",
                                "school": "子平",
                                "rule_direction": "negative",
                            },
                        ],
                    }
                ]
            },
            "C-TEST-STATEMENT-V2-CONFLICT",
            run_id="run-test-003",
            generated_at="2026-10-14T00:00:00Z",
        )
