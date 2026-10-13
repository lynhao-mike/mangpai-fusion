"""十八槽位能力覆盖与弃权诊断核心测试。"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime

import pytest

from engine.v5.domain import V5Claim, V5Confidence, V5Evidence
from engine.v5.domain_capability_metrics import build_capability_metrics
from engine.v5.domain_slices.contract import DomainAnalysisRequest
from engine.v5.domain_slices.orchestrator import run_domain_analysis


def _snapshot(*, domains=("career", "wealth", "marriage")):
    return run_domain_analysis(
        DomainAnalysisRequest(
            gender="乾",
            birth_datetime=datetime(1990, 1, 1, 12, 0),
            as_of_date=date(2026, 7, 31),
            domains=domains,
        )
    )


def test_metrics_preserve_eighteen_slot_identity_and_registration_runtime_ledger() -> None:
    snapshot = _snapshot(domains=("career",))

    metrics = build_capability_metrics([snapshot])

    assert metrics["run_count"] == 1
    assert metrics["slot_count"] == 18
    assert len(metrics["slots"]) == 18
    yang_wealth = next(
        row for row in metrics["slots"]
        if row["school"] == "yang_qingjuan" and row["domain"] == "wealth"
    )
    assert yang_wealth["registration_status"] == "unsupported"
    assert yang_wealth["runtime_status_counts"] == {"not_requested": 1}
    assert "unsupported" not in yang_wealth["runtime_status_counts"]


def test_metrics_group_claims_by_school_domain_task_and_use_stable_zero_denominators() -> None:
    snapshot = _snapshot(domains=("wealth",))

    metrics = build_capability_metrics([snapshot])
    rows = metrics["tasks"]

    assert rows == sorted(rows, key=lambda row: (row["school"], row["domain"], row["task"]))
    assert all(0.0 <= row["evidence_completeness_rate"] <= 1.0 for row in rows)
    assert all(0.0 <= row["conflict_rate"] <= 1.0 for row in rows)
    assert all(0.0 <= row["timing_coverage_rate"] <= 1.0 for row in rows)
    placeholder = next(row for row in rows if row["task"] == "__slot__")
    assert placeholder["substantive_claim_count"] == 0
    assert placeholder["evidence_completeness_rate"] == 0.0
    assert placeholder["timing_coverage_rate"] == 0.0


def test_duplicate_identical_run_is_deduplicated_but_conflicting_duplicate_fails_closed() -> None:
    snapshot = _snapshot(domains=("career",))

    assert build_capability_metrics([snapshot, snapshot])["run_count"] == 1

    conflicting = replace(snapshot, metadata={**snapshot.metadata, "marker": "different"})
    with pytest.raises(ValueError, match="duplicate run_id"):
        build_capability_metrics([snapshot, conflicting])


def test_shape_valid_coverage_tampering_and_legacy_unsealed_metadata_fail_closed() -> None:
    snapshot = _snapshot(domains=("career",))
    coverage = [dict(item) for item in snapshot.metadata["slice_coverage"]]
    coverage[0] = {**coverage[0], "reason": "shape-valid tampering"}
    tampered = replace(snapshot, metadata={**snapshot.metadata, "slice_coverage": coverage})

    with pytest.raises(ValueError, match="metadata|capability|integrity|hash"):
        build_capability_metrics([tampered])

    legacy_metadata = dict(snapshot.metadata)
    legacy_metadata.pop("capability_integrity", None)
    legacy = replace(snapshot, metadata=legacy_metadata)
    with pytest.raises(ValueError, match="unavailable|metadata|capability|integrity"):
        build_capability_metrics([legacy])


def test_tampered_output_hash_and_broken_slot_identity_fail_closed() -> None:
    snapshot = _snapshot(domains=("career",))
    tampered_claim = replace(snapshot.claims[0], claim="被篡改")
    tampered = replace(snapshot, claims=[tampered_claim, *snapshot.claims[1:]])

    with pytest.raises(ValueError, match="output hash mismatch"):
        build_capability_metrics([tampered])

    coverage = [dict(item) for item in snapshot.metadata["slice_coverage"]]
    coverage[0] = {**coverage[0], "school": "fake_school"}
    broken_slots = replace(snapshot, metadata={**snapshot.metadata, "slice_coverage": coverage})
    with pytest.raises(ValueError, match="eighteen-slot identity"):
        build_capability_metrics([broken_slots])


def test_metrics_aggregate_evidence_conflict_timing_high_risk_and_abstain_taxonomy() -> None:
    base = _snapshot(domains=("wealth",))
    evidence = V5Evidence(
        evidence_id="ev-metric",
        source="test",
        text="完整证据",
        node_refs=["chart:root"],
    )
    claims = [
        V5Claim(
            claim_id="cl-support",
            school="ziping",
            domain="财富",
            claim="支持",
            claim_type="event_claim",
            stance="support",
            confidence=V5Confidence(),
            evidence=[evidence],
            timing_hints=[{"start_year": 2026}],
            metadata={"task_id": "wealth.debt", "high_risk": True},
        ),
        V5Claim(
            claim_id="cl-oppose",
            school="ziping",
            domain="财富",
            claim="反对",
            claim_type="counter_claim",
            stance="oppose",
            confidence=V5Confidence(),
            evidence=[evidence],
            metadata={"task_id": "wealth.debt", "high_risk": True},
        ),
    ]
    snapshot = replace(base, claims=claims, output_hash="")
    snapshot = replace(snapshot, output_hash=snapshot.to_output().hash())

    metrics = build_capability_metrics([snapshot])
    debt = next(row for row in metrics["tasks"] if row["task"] == "wealth.debt")

    assert debt["claim_count"] == 2
    assert debt["evidence_completeness_rate"] == 1.0
    assert debt["conflict_rate"] == 1.0
    assert debt["timing_coverage_rate"] == 0.5
    assert debt["high_risk"]["metadata_present"] is True
    assert debt["high_risk"]["gate_status"] == "unavailable"
    assert metrics["high_risk_gate"]["availability"] == "unavailable"
    assert metrics["abstain_reason_taxonomy"]


def test_real_gate_metadata_makes_capability_gate_available_with_observed_statistics() -> None:
    snapshot = _snapshot(domains=("wealth", "marriage"))

    metrics = build_capability_metrics([snapshot])

    assert metrics["high_risk_gate"]["availability"] == "available"
    assert metrics["high_risk_gate"]["status_counts"]
    high_risk_rows = [row for row in metrics["tasks"] if row["high_risk"]["metadata_present"]]
    assert high_risk_rows
    assert all(row["high_risk"]["gate_status"] != "unavailable" for row in high_risk_rows)
