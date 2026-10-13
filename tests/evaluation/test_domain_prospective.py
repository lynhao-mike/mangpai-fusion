from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime

import pytest

from engine.evaluation.domain_prospective import (
    build_intake,
    freeze_snapshot,
    reveal_labels,
    score_revealed,
    summarize_status,
)
from engine.v5.domain import V5RunSnapshot, V5_SCHOOLS
from engine.v5.domain_feedback import claim_hash
from engine.v5.domain_metadata_integrity import seal_capability_metadata
from engine.v5.domain_slices.contract import DomainAnalysisRequest
from engine.v5.domain_slices.orchestrator import run_domain_analysis


def _intake_payload(case_id: str = "DP-2026-001", *, track: str = "prospective") -> dict[str, object]:
    return {
        "schema_version": "domain-prospective-intake/v1",
        "case_id": case_id,
        "track": track,
        "gender": "乾",
        "birth_datetime": "1990-01-01T12:00:00",
        "as_of_date": "2026-07-31",
        "domains": ["career", "wealth", "marriage"],
    }


def _snapshot(case_id: str = "DP-2026-001") -> V5RunSnapshot:
    snapshot = V5RunSnapshot(
        run_id="run-domain-001",
        case_id=case_id,
        canonical_input={
            "gender_marker": "乾",
            "birth_datetime": "1990-01-01T12:00:00",
            "as_of_date": "2026-07-31",
        },
        metadata={
            "requested_domains": ["career", "wealth", "marriage"],
            "domain_evaluation_claims": [
                {"claim_id": "career-claim", "domain": "career", "task_id": "career-path", "state": "claim"},
                {"claim_id": "wealth-abstain", "domain": "wealth", "task_id": "wealth-level", "state": "abstain"},
                {"claim_id": "marriage-claim", "domain": "marriage", "task_id": "marriage-state", "state": "claim"},
            ]
        },
    )
    return V5RunSnapshot.from_dict({**snapshot.to_dict(), "output_hash": snapshot.to_output().hash()})


def _labels(freeze_hash: str) -> dict[str, object]:
    return {
        "schema_version": "domain-prospective-labels/v1",
        "freeze_hash": freeze_hash,
        "labels": [
            {"claim_id": "career-claim", "domain": "career", "task_id": "career-path", "outcome": "hit"},
            {"claim_id": "wealth-abstain", "domain": "wealth", "task_id": "wealth-level", "outcome": "hit"},
            {"claim_id": "marriage-claim", "domain": "marriage", "task_id": "marriage-state", "outcome": "miss"},
        ],
    }


@pytest.mark.parametrize(
    "field",
    ["feedback", "labels", "report", "known_facts", "knownFacts", "model_prediction", "occupation"],
)
def test_intake_rejects_top_level_and_nested_leakage(field: str) -> None:
    payload = _intake_payload()
    payload["extra"] = {field: "forbidden"}

    with pytest.raises(ValueError, match="leakage|whitelist"):
        build_intake(payload)


def test_intake_reuses_domain_request_and_rejects_duplicate_identity() -> None:
    first = build_intake(_intake_payload())

    assert first.request.birth_datetime == datetime(1990, 1, 1, 12, 0)
    assert first.request.as_of_date == date(2026, 7, 31)
    assert first.request.domains == ("career", "wealth", "marriage")

    duplicate = _intake_payload("DP-2026-999")
    with pytest.raises(ValueError, match="identity"):
        build_intake(duplicate, existing=[first])


def _real_snapshot_request(**overrides: object) -> DomainAnalysisRequest:
    values: dict[str, object] = {
        "gender": "乾",
        "birth_datetime": datetime(1990, 1, 1, 12, 0),
        "as_of_date": date(2026, 7, 31),
        "domains": ("career", "wealth", "marriage"),
    }
    values.update(overrides)
    return DomainAnalysisRequest(**values)  # type: ignore[arg-type]


def _real_snapshot() -> V5RunSnapshot:
    return run_domain_analysis(_real_snapshot_request())


def test_real_domain_analysis_snapshot_freezes_conservative_evaluation_manifest() -> None:
    snapshot = _real_snapshot()
    intake = build_intake(_intake_payload(snapshot.case_id))

    frozen = freeze_snapshot(intake, snapshot)
    repeated = run_domain_analysis(_real_snapshot_request())

    assert frozen.claims
    assert frozen.to_dict() == freeze_snapshot(intake, repeated).to_dict()
    assert len({claim.claim_id for claim in frozen.claims}) == len(frozen.claims)
    assert {claim.domain for claim in frozen.claims} <= {"career", "wealth", "marriage"}
    assert {claim.school for claim in frozen.claims} <= set(V5_SCHOOLS)
    assert all(claim.task_id.startswith(claim.domain + ".") for claim in frozen.claims)
    assert all(claim.state == "claim" for claim in frozen.claims)
    assert all(claim.claim_type in {"structure_claim", "event_claim", "timing_claim"} for claim in frozen.claims)
    assert any(claim.claim_type == "timing_claim" for claim in frozen.claims)
    assert all(claim.claim_type != "timing_claim" or claim.task_id.endswith("window") for claim in frozen.claims)

    source_claims = {claim_hash(claim): claim for claim in snapshot.claims}
    abstain_ids = {claim.claim_id for claim in snapshot.claims if claim.stance == "abstain"}
    assert {claim.source_claim_id for claim in frozen.claims}.isdisjoint(abstain_ids)
    assert all(claim.source_claim_hash in source_claims for claim in frozen.claims)
    assert all(source_claims[claim.source_claim_hash].claim_id == claim.source_claim_id for claim in frozen.claims)
    exclusions = snapshot.metadata["domain_evaluation_exclusions"]
    assert len(frozen.claims) + len(exclusions) == len(snapshot.claims)
    assert {item["reason"] for item in exclusions} >= {"missing_task_id", "abstain"}
    assert snapshot.metadata["domain_evaluation_integrity"]["sha256"]
    assert snapshot.canonical_input["gender_marker"] == "乾"
    assert "gender" not in snapshot.canonical_input


@pytest.mark.parametrize("target", ["domain_evaluation_claims", "domain_evaluation_exclusions"])
def test_real_evaluation_metadata_shape_valid_tampering_fails_closed_even_after_resealing(target: str) -> None:
    snapshot = _real_snapshot()
    intake = build_intake(_intake_payload(snapshot.case_id))
    changed = [dict(item) for item in snapshot.metadata[target]]
    if target == "domain_evaluation_claims":
        changed[0]["task_id"] = "career.forged_target"
    else:
        changed[0]["reason"] = "abstain"
    metadata = {**snapshot.metadata, target: changed}
    metadata.pop("capability_integrity")
    tampered = replace(snapshot, metadata=seal_capability_metadata(metadata))

    with pytest.raises(ValueError, match="metadata|integrity|manifest|projection|hash"):
        freeze_snapshot(intake, tampered)


def test_freeze_binds_v5_snapshot_and_is_deterministic() -> None:
    intake = build_intake(_intake_payload())
    snapshot = _snapshot()

    first = freeze_snapshot(intake, snapshot)
    second = freeze_snapshot(intake, snapshot)

    assert first.freeze_hash == second.freeze_hash
    assert first.snapshot_hash == snapshot.hash()
    assert first.snapshot.output_hash_matches()
    assert [claim.state for claim in first.claims] == ["claim", "abstain", "claim"]


def test_freeze_rejects_case_mismatch_and_snapshot_hash_tampering() -> None:
    intake = build_intake(_intake_payload())
    with pytest.raises(ValueError, match="case_id"):
        freeze_snapshot(intake, _snapshot("DP-2026-999"))

    snapshot = _snapshot()
    frozen = freeze_snapshot(intake, snapshot)
    tampered = frozen.to_dict()
    tampered["claims"][0]["task_id"] = "changed"
    with pytest.raises(ValueError, match="hash"):
        reveal_labels(tampered, _labels(frozen.freeze_hash))


@pytest.mark.parametrize(
    ("canonical_patch", "metadata_patch"),
    [
        ({"gender_marker": "坤"}, {}),
        ({"birth_datetime": "1990-01-01T12:00:01"}, {}),
        ({"as_of_date": "2026-08-01"}, {}),
        ({}, {"requested_domains": ["career", "wealth"]}),
        ({"as_of_date": None}, {}),
        ({}, {"requested_domains": None}),
    ],
)
def test_freeze_rejects_snapshot_that_does_not_bind_complete_normalized_request(
    canonical_patch: dict[str, object], metadata_patch: dict[str, object]
) -> None:
    intake = build_intake(_intake_payload())
    snapshot = _snapshot()
    changed_payload = {
        **snapshot.to_dict(),
        "canonical_input": {**snapshot.canonical_input, **canonical_patch},
        "metadata": {**snapshot.metadata, **metadata_patch},
    }
    changed = V5RunSnapshot.from_dict(changed_payload)
    changed = V5RunSnapshot.from_dict({**changed.to_dict(), "output_hash": changed.to_output().hash()})

    with pytest.raises(ValueError, match="request|gender|birth_datetime|as_of_date|domains"):
        freeze_snapshot(intake, changed)


@pytest.mark.parametrize(
    ("canonical_patch", "metadata_patch"),
    [
        ({"gender_marker": "坤"}, {}),
        ({"birth_datetime": "1990-01-01 12:00:01"}, {}),
        ({"as_of_date": "2026-08-01"}, {}),
        ({}, {"requested_domains": ["career", "wealth"]}),
    ],
)
def test_freeze_rejects_real_snapshot_request_mismatch(
    canonical_patch: dict[str, object], metadata_patch: dict[str, object]
) -> None:
    snapshot = _real_snapshot()
    intake = build_intake(_intake_payload(snapshot.case_id))
    changed = replace(
        snapshot,
        canonical_input={**snapshot.canonical_input, **canonical_patch},
        metadata={**snapshot.metadata, **metadata_patch},
    )
    changed = replace(changed, output_hash=changed.to_output().hash())

    with pytest.raises(ValueError, match="request"):
        freeze_snapshot(intake, changed)


def test_reveal_requires_freeze_and_exact_freeze_hash() -> None:
    with pytest.raises(ValueError, match="freeze"):
        reveal_labels(None, _labels("0" * 64))

    frozen = freeze_snapshot(build_intake(_intake_payload()), _snapshot())
    labels = _labels("f" * 64)
    with pytest.raises(ValueError, match="freeze_hash"):
        reveal_labels(frozen, labels)


def test_partial_mature_labels_score_only_hit_or_miss_and_report_label_coverage() -> None:
    frozen = freeze_snapshot(build_intake(_intake_payload()), _snapshot())
    labels = {
        "schema_version": "domain-prospective-labels/v1",
        "freeze_hash": frozen.freeze_hash,
        "labels": [
            {"claim_id": "career-claim", "domain": "career", "task_id": "career-path", "outcome": "hit"},
            {"claim_id": "marriage-claim", "domain": "marriage", "task_id": "marriage-state", "outcome": "pending"},
        ],
    }

    score = score_revealed(frozen, reveal_labels(frozen, labels))

    assert score.metrics["overall"] == {
        "claim_count": 2,
        "labeled_count": 2,
        "scored_count": 1,
        "hit_count": 1,
        "miss_count": 0,
        "pending_count": 1,
        "abstain_count": 1,
        "label_coverage": 1.0,
        "scored_coverage": 0.5,
        "accuracy": 1.0,
    }
    assert score.metrics["by_claim"]["marriage-claim"]["status"] == "pending"
    assert score.metrics["by_claim"]["wealth-abstain"]["status"] == "abstain"


def test_score_is_deterministic_split_by_track_domain_task_claim_and_preserves_abstain() -> None:
    frozen = freeze_snapshot(build_intake(_intake_payload()), _snapshot())
    revealed = reveal_labels(frozen, _labels(frozen.freeze_hash))

    first = score_revealed(frozen, revealed)
    second = score_revealed(frozen, revealed)

    assert first.to_dict() == second.to_dict()
    assert first.track == "prospective"
    assert first.metrics["overall"] == {
        "claim_count": 2,
        "labeled_count": 2,
        "scored_count": 2,
        "hit_count": 1,
        "miss_count": 1,
        "pending_count": 0,
        "abstain_count": 1,
        "label_coverage": 1.0,
        "scored_coverage": 1.0,
        "accuracy": 0.5,
    }
    assert first.metrics["by_domain"]["wealth"]["abstain_count"] == 1
    assert first.metrics["by_domain"]["wealth"]["hit_count"] == 0
    assert first.metrics["by_task"]["wealth-level"]["abstain_count"] == 1
    assert first.metrics["by_claim"]["wealth-abstain"]["status"] == "abstain"


def test_status_keeps_historical_and_prospective_separate_and_not_ready_below_30() -> None:
    prospective = score_revealed(
        freeze_snapshot(build_intake(_intake_payload()), _snapshot()),
        reveal_labels(
            freeze_snapshot(build_intake(_intake_payload()), _snapshot()),
            _labels(freeze_snapshot(build_intake(_intake_payload()), _snapshot()).freeze_hash),
        ),
    )
    historical_intake = build_intake(_intake_payload("DP-H-001", track="historical"))
    historical_frozen = freeze_snapshot(historical_intake, _snapshot("DP-H-001"))
    historical = score_revealed(
        historical_frozen,
        reveal_labels(historical_frozen, _labels(historical_frozen.freeze_hash)),
    )

    status = summarize_status([historical, prospective])

    assert status["status"] == "not_ready"
    assert status["tracks"]["prospective"]["qualified_case_count"] == 0
    assert status["tracks"]["historical"]["qualified_case_count"] == 0
    assert status["production_ready"] is False
    assert status["production_switch_permitted"] is False
    assert "unverified_artifact_chain" in status["failures"]


def test_thirty_isolated_self_signed_scores_cannot_make_status_ready() -> None:
    scores = []
    for index in range(30):
        case_id = f"DP-FORGED-{index:03d}"
        frozen = freeze_snapshot(build_intake(_intake_payload(case_id)), _snapshot(case_id))
        revealed = reveal_labels(frozen, _labels(frozen.freeze_hash))
        scores.append(score_revealed(frozen, revealed))

    status = summarize_status(scores)

    assert status["status"] == "not_ready"
    assert status["tracks"]["prospective"]["score_count"] == 30
    assert status["tracks"]["prospective"]["qualified_case_count"] == 0
    assert status["production_ready"] is False
    assert status["production_switch_permitted"] is False
    assert "unverified_artifact_chain" in status["failures"]
