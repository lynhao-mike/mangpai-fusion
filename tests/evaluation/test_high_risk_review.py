from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from engine.evaluation.high_risk_review import (
    HIGH_RISK_TASK_IDS,
    finalize_reviews,
    prepare_review_packets,
    validate_review,
)


ROOT = Path(__file__).resolve().parents[2]
MODULE = "tools.school_capability_review"
OBSERVATION_SHA256 = "a" * 64


def _review(
    reviewer: str,
    decision: object = "occurred",
    *,
    task_id: str = "wealth.debt",
    observation_sha256: str = OBSERVATION_SHA256,
) -> dict[str, Any]:
    return {
        "schema_version": "school-capability-high-risk-review/v1",
        "case_id": "P-GO-2026-001",
        "task_id": task_id,
        "observation_sha256": observation_sha256,
        "reviewer": reviewer,
        "decision": decision,
        "source_refs": ["custody://record-001"],
        "rationale": "独立核对观察资料后作出判断。",
        "signed_at": "2026-10-01T00:00:00Z",
    }


def _adjudication(adjudicator: str, decision: object = "occurred") -> dict[str, Any]:
    return {
        "schema_version": "school-capability-high-risk-adjudication/v1",
        "case_id": "P-GO-2026-001",
        "task_id": "wealth.debt",
        "observation_sha256": OBSERVATION_SHA256,
        "adjudicator": adjudicator,
        "decision": decision,
        "source_refs": ["custody://record-001"],
        "rationale": "审阅相同观察及两份冲突理由后裁决。",
        "signed_at": "2026-10-02T00:00:00Z",
    }


def _observation() -> dict[str, Any]:
    return {
        "schema_version": "prospective-observation/v1",
        "case_id": "P-GO-2026-001",
        "task_id": "wealth.debt",
        "label": "occurred",
        "observed_at": "2026-09-30T00:00:00Z",
        "observation_window": {
            "started_at": "2026-07-01T00:00:00Z",
            "ended_at": "2026-09-30T00:00:00Z",
        },
        "source_refs": ["custody://record-001"],
        "quantifiable": True,
        "conflict_state": "none",
        "custodian": "human-custodian-01",
    }


def _run(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", MODULE, *(str(arg) for arg in args)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_same_reviewer_cannot_produce_a_grade_label() -> None:
    review = _review("human-reviewer-a")

    with pytest.raises(ValueError, match="different independent reviewers"):
        finalize_reviews("P-GO-2026-001", "wealth.debt", review, review)


def test_reviewer_cannot_match_intake_runner_or_outcome_operator() -> None:
    review = _review("human-intake-01")

    with pytest.raises(ValueError, match="role separation"):
        validate_review(
            review,
            disallowed_reviewers={"human-intake-01", "human-runner-01", "human-custodian-01"},
        )


def test_reviews_must_reference_the_same_observation_hash() -> None:
    with pytest.raises(ValueError, match="observation hash"):
        finalize_reviews(
            "P-GO-2026-001",
            "wealth.debt",
            _review("human-reviewer-a"),
            _review("human-reviewer-b", observation_sha256="b" * 64),
        )


def test_consistent_independent_reviews_produce_standard_a_grade_label() -> None:
    final = finalize_reviews(
        "P-GO-2026-001",
        "wealth.debt",
        _review("human-reviewer-a"),
        _review("human-reviewer-b"),
    )

    assert final["status"] == "GO"
    assert final["label"] == {
        "case_id": "P-GO-2026-001",
        "task_id": "wealth.debt",
        "label": "occurred",
        "observed_at": "2026-10-01T00:00:00Z",
        "source": final["label"]["source"],
        "confidence_grade": "A",
        "quantifiable": True,
        "conflict_state": "none",
        "reviewer": "human-reviewer-a+human-reviewer-b",
    }
    assert final["label"]["source"].startswith("high-risk-review://sha256:")
    assert final["reviewers"] == ["human-reviewer-a", "human-reviewer-b"]


def test_conflicting_reviews_hold_without_adjudication() -> None:
    final = finalize_reviews(
        "P-GO-2026-001",
        "wealth.debt",
        _review("human-reviewer-a", "occurred"),
        _review("human-reviewer-b", "not_observed"),
    )

    assert final["status"] == "HOLD"
    assert final["label"] is None
    assert final["reason"] == "adjudication_required"


def test_adjudicator_must_be_a_third_independent_human() -> None:
    with pytest.raises(ValueError, match="adjudicator must differ"):
        finalize_reviews(
            "P-GO-2026-001",
            "wealth.debt",
            _review("human-reviewer-a", "occurred"),
            _review("human-reviewer-b", "not_observed"),
            _adjudication("human-reviewer-a"),
        )


def test_third_party_adjudication_preserves_both_reviews_and_reason() -> None:
    review_a = _review("human-reviewer-a", "occurred")
    review_b = _review("human-reviewer-b", "not_observed")
    adjudication = _adjudication("human-adjudicator-c", "occurred")

    final = finalize_reviews(
        "P-GO-2026-001", "wealth.debt", review_a, review_b, adjudication
    )

    assert final["status"] == "GO"
    assert final["label"]["confidence_grade"] == "A"
    assert final["label"]["label"] == "occurred"
    assert final["label"]["conflict_state"] == "resolved_by_adjudication"
    assert final["reviews"] == [review_a, review_b]
    assert final["adjudication"] == adjudication
    assert final["adjudication"]["rationale"]


def test_non_high_risk_task_cannot_use_review_gate() -> None:
    assert HIGH_RISK_TASK_IDS == {
        "wealth.debt",
        "marriage.divorce_or_remarriage",
        "health.system_risk",
    }
    with pytest.raises(ValueError, match="not a supported high-risk task"):
        finalize_reviews(
            "P-GO-2026-001",
            "career.role_change",
            _review("human-reviewer-a", task_id="career.role_change"),
            _review("human-reviewer-b", task_id="career.role_change"),
        )


@pytest.mark.parametrize("leaked_key", ["probability", "runner_output", "report_text", "school_output"])
def test_review_leakage_scan_rejects_prediction_fields(leaked_key: str) -> None:
    review = _review("human-reviewer-a")
    review[leaked_key] = "forbidden"

    with pytest.raises(ValueError, match="leakage"):
        validate_review(review)


def test_decisions_follow_task_label_schema() -> None:
    validate_review(_review("human-a", "not_observed"))
    validate_review(_review("human-a", "high", task_id="health.system_risk"))

    with pytest.raises(ValueError, match="decision"):
        validate_review(_review("human-a", "relationship_pressure"))
    with pytest.raises(ValueError, match="decision"):
        validate_review(_review("human-a", "diagnosis", task_id="health.system_risk"))


def test_prepare_packets_are_separate_and_contain_no_prediction(tmp_path: Path) -> None:
    observation = _observation()
    packets = prepare_review_packets(
        observation,
        reviewer_a="human-reviewer-a",
        reviewer_b="human-reviewer-b",
        disallowed_reviewers={"human-intake-01", "human-runner-01", "human-custodian-01"},
    )

    assert set(packets) == {"reviewer_a", "reviewer_b"}
    assert packets["reviewer_a"]["reviewer"] == "human-reviewer-a"
    assert packets["reviewer_b"]["reviewer"] == "human-reviewer-b"
    assert packets["reviewer_a"]["observation_sha256"] == packets["reviewer_b"]["observation_sha256"]
    assert packets["reviewer_a"]["observation_sha256"] == hashlib.sha256(
        json.dumps(observation, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    serialized = json.dumps(packets, ensure_ascii=False).lower()
    assert "probability" not in serialized
    assert "runner_output" not in serialized
    assert "report_text" not in serialized


def test_cli_prepare_dry_run_writes_nothing_and_existing_target_is_rejected(tmp_path: Path) -> None:
    observation = tmp_path / "observation.json"
    observation.write_text(json.dumps(_observation(), ensure_ascii=False), encoding="utf-8")
    target = tmp_path / "packets"

    dry_run = _run(
        "prepare",
        "--observation", observation,
        "--reviewer-a", "human-reviewer-a",
        "--reviewer-b", "human-reviewer-b",
        "--intake-operator", "human-intake-01",
        "--runner-operator", "human-runner-01",
        "--outcome-custodian", "human-custodian-01",
        "--out-dir", target,
        "--dry-run",
    )

    assert dry_run.returncode == 0, dry_run.stderr
    assert not target.exists()
    preview = json.loads(dry_run.stdout)
    assert preview["dry_run"] is True

    target.mkdir()
    result = _run(
        "prepare",
        "--observation", observation,
        "--reviewer-a", "human-reviewer-a",
        "--reviewer-b", "human-reviewer-b",
        "--intake-operator", "human-intake-01",
        "--runner-operator", "human-runner-01",
        "--outcome-custodian", "human-custodian-01",
        "--out-dir", target,
    )
    assert result.returncode != 0
    assert "must not exist" in result.stderr


def test_cli_finalize_dry_run_emits_unbound_label_without_writing(tmp_path: Path) -> None:
    review_a = tmp_path / "review-a.json"
    review_b = tmp_path / "review-b.json"
    review_a.write_text(json.dumps(_review("human-reviewer-a"), ensure_ascii=False), encoding="utf-8")
    review_b.write_text(json.dumps(_review("human-reviewer-b"), ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "label.json"

    result = _run(
        "finalize",
        "--review-a", review_a,
        "--review-b", review_b,
        "--out", output,
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert not output.exists()
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert payload["result"]["label"]["confidence_grade"] == "A"
