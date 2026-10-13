from __future__ import annotations

import json
from pathlib import Path

from engine.evaluation.domain_prospective import build_intake, freeze_snapshot
from engine.v5.domain import V5RunSnapshot
from tools.domain_prospective_cohort import main


def _write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _intake_payload(case_id: str = "DP-2026-001") -> dict[str, object]:
    return {
        "schema_version": "domain-prospective-intake/v1",
        "case_id": case_id,
        "track": "prospective",
        "gender": "坤",
        "birth_datetime": "1992-02-03T04:05:00",
        "as_of_date": "2026-07-31",
        "domains": ["career", "wealth", "marriage"],
    }


def _snapshot(case_id: str = "DP-2026-001") -> V5RunSnapshot:
    snapshot = V5RunSnapshot(
        run_id="run-dp-001",
        case_id=case_id,
        canonical_input={
            "gender_marker": "坤",
            "birth_datetime": "1992-02-03T04:05:00",
            "as_of_date": "2026-07-31",
        },
        metadata={
            "requested_domains": ["career", "wealth", "marriage"],
            "domain_evaluation_claims": [
                {"claim_id": "c1", "domain": "career", "task_id": "career-path", "state": "claim"},
                {"claim_id": "w1", "domain": "wealth", "task_id": "wealth-level", "state": "abstain"},
                {"claim_id": "m1", "domain": "marriage", "task_id": "marriage-state", "state": "claim"},
            ]
        },
    )
    return V5RunSnapshot.from_dict({**snapshot.to_dict(), "output_hash": snapshot.to_output().hash()})


def _labels(freeze_hash: str) -> dict[str, object]:
    return {
        "schema_version": "domain-prospective-labels/v1",
        "freeze_hash": freeze_hash,
        "labels": [
            {"claim_id": "c1", "domain": "career", "task_id": "career-path", "outcome": "hit"},
            {"claim_id": "w1", "domain": "wealth", "task_id": "wealth-level", "outcome": "miss"},
            {"claim_id": "m1", "domain": "marriage", "task_id": "marriage-state", "outcome": "miss"},
        ],
    }


def test_intake_cli_is_create_only_and_rejects_leakage(tmp_path: Path, capsys) -> None:
    source = _write(tmp_path / "source.json", _intake_payload())
    output = tmp_path / "intake.json"

    assert main(["intake", "--input", str(source), "--out", str(output)]) == 0
    assert output.exists()
    assert main(["intake", "--input", str(source), "--out", str(output)]) == 2
    assert "exists" in capsys.readouterr().err

    leaked = _intake_payload("DP-2026-002")
    leaked["known_facts"] = {"career": "known"}
    leaked_source = _write(tmp_path / "leaked.json", leaked)
    assert main(["intake", "--input", str(leaked_source), "--out", str(tmp_path / "bad.json")]) == 2


def test_intake_cli_auto_discovers_duplicate_identity_in_governed_output_directory(tmp_path: Path) -> None:
    first_source = _write(tmp_path / "first.json", _intake_payload())
    first_output = tmp_path / "cohort" / "first-intake.json"
    first_output.parent.mkdir()
    assert main(["intake", "--input", str(first_source), "--out", str(first_output)]) == 0

    duplicate_source = _write(tmp_path / "duplicate.json", _intake_payload("DP-2026-999"))
    duplicate_output = first_output.parent / "duplicate-intake.json"

    assert main(["intake", "--input", str(duplicate_source), "--out", str(duplicate_output)]) == 2
    assert not duplicate_output.exists()


def test_loader_rejects_published_artifact_digest_tampering(tmp_path: Path) -> None:
    source = _write(tmp_path / "source.json", _intake_payload())
    intake_path = tmp_path / "intake.json"
    assert main(["intake", "--input", str(source), "--out", str(intake_path)]) == 0

    document = json.loads(intake_path.read_text(encoding="utf-8"))
    document["case_id"] = "DP-TAMPERED"
    intake_path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

    assert main([
        "freeze", "--intake", str(intake_path), "--snapshot", str(_write(tmp_path / "snapshot.json", _snapshot().to_dict())),
        "--out", str(tmp_path / "freeze.json")
    ]) == 2
    assert not (tmp_path / "freeze.json").exists()


def test_freeze_reveal_score_status_cli_round_trip(tmp_path: Path, capsys) -> None:
    source = _write(tmp_path / "source.json", _intake_payload())
    intake_path = tmp_path / "intake.json"
    snapshot_path = _write(tmp_path / "snapshot.json", _snapshot().to_dict())
    freeze_path = tmp_path / "freeze.json"
    reveal_path = tmp_path / "reveal.json"
    score_path = tmp_path / "score.json"
    status_path = tmp_path / "status.json"

    assert main(["intake", "--input", str(source), "--out", str(intake_path)]) == 0
    assert main(["freeze", "--intake", str(intake_path), "--snapshot", str(snapshot_path), "--out", str(freeze_path)]) == 0
    frozen = json.loads(freeze_path.read_text(encoding="utf-8"))
    labels_path = _write(tmp_path / "labels.json", _labels(frozen["freeze_hash"]))
    assert main(["reveal", "--freeze", str(freeze_path), "--labels", str(labels_path), "--out", str(reveal_path)]) == 0
    assert main(["score", "--freeze", str(freeze_path), "--reveal", str(reveal_path), "--out", str(score_path)]) == 0
    assert main(["status", "--score", str(score_path), "--out", str(status_path)]) == 1

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["status"] == "not_ready"
    assert status["production_ready"] is False
    assert "not_ready" in capsys.readouterr().out


def test_reveal_cli_rejects_missing_freeze_and_hash_tampering(tmp_path: Path) -> None:
    labels_path = _write(tmp_path / "labels.json", _labels("0" * 64))
    assert main(["reveal", "--freeze", str(tmp_path / "missing.json"), "--labels", str(labels_path), "--out", str(tmp_path / "out.json")]) == 2

    intake = build_intake(_intake_payload())
    frozen = freeze_snapshot(intake, _snapshot())
    freeze_payload = frozen.to_dict()
    freeze_payload["claims"][0]["domain"] = "wealth"
    freeze_path = _write(tmp_path / "tampered.json", freeze_payload)
    labels_path = _write(tmp_path / "bound-labels.json", _labels(frozen.freeze_hash))

    assert main(["reveal", "--freeze", str(freeze_path), "--labels", str(labels_path), "--out", str(tmp_path / "reveal.json")]) == 2
    assert not (tmp_path / "reveal.json").exists()
