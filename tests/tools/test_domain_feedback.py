"""命题级结构化反馈 CLI 测试。"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from engine.v5.domain import V5Claim, V5Confidence, V5Output, V5RunSnapshot
from tools.domain_feedback import main


def _write_snapshot(path: Path, *, high_risk: bool = True) -> V5RunSnapshot:
    claim = V5Claim(
        claim_id="claim-cli-001",
        school="ziping",
        domain="财富",
        claim="存在债务压力风险。",
        claim_type="event_claim",
        stance="support",
        confidence=V5Confidence(),
        falsifiable="若无债务压力则不成立。",
        metadata={"task_id": "wealth.debt", "high_risk": high_risk},
    )
    snapshot = V5RunSnapshot.from_output(
        V5Output(case_id="C-TEST-DOMAIN-FEEDBACK-CLI", chart={"pillars": []}, claims=[claim])
    )
    path.write_text(snapshot.to_json(), encoding="utf-8")
    return snapshot


def _filled_draft(draft_path: Path, *, reviewer: str = "human-reviewer-01", status: str = "accepted") -> None:
    payload = json.loads(draft_path.read_text(encoding="utf-8"))
    payload.update(
        {
            "reviewer": reviewer,
            "status": status,
            "observed_at": "2026-08-01T00:00:00Z",
            "note": "人工核验。",
        }
    )
    draft_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_prepare_ingest_status_and_candidates_happy_path(tmp_path: Path, capsys) -> None:
    snapshot_path = tmp_path / "case.run.json"
    _write_snapshot(snapshot_path)
    draft_path = tmp_path / "draft.json"
    store = tmp_path / "feedback-store"

    assert main(["prepare", "--snapshot", str(snapshot_path), "--claim-id", "claim-cli-001", "--out", str(draft_path)]) == 0
    capsys.readouterr()
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    assert draft["claim_id"] == "claim-cli-001"
    assert draft["status"] == "unknown"

    _filled_draft(draft_path)
    assert main(["ingest", "--snapshot", str(snapshot_path), "--feedback", str(draft_path), "--store", str(store)]) == 0
    receipt = json.loads(capsys.readouterr().out)
    artifact = Path(receipt["artifact_path"])
    assert artifact.is_file()

    assert main(["status", "--store", str(store), "--snapshot", str(snapshot_path)]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["valid_feedback_count"] == 1
    assert status["status_counts"] == {"accepted": 1}

    assert main(["candidates", "--store", str(store), "--snapshot", str(snapshot_path)]) == 0
    candidates = json.loads(capsys.readouterr().out)
    assert candidates["read_only"] is True
    assert candidates["candidates"][0]["requires_human_review"] is True


def test_prepare_and_ingest_are_create_only(tmp_path: Path, capsys) -> None:
    snapshot_path = tmp_path / "case.run.json"
    _write_snapshot(snapshot_path)
    draft_path = tmp_path / "draft.json"
    store = tmp_path / "feedback-store"

    assert main(["prepare", "--snapshot", str(snapshot_path), "--claim-id", "claim-cli-001", "--out", str(draft_path)]) == 0
    assert main(["prepare", "--snapshot", str(snapshot_path), "--claim-id", "claim-cli-001", "--out", str(draft_path)]) == 2
    assert "already exists" in capsys.readouterr().err

    _filled_draft(draft_path)
    assert main(["ingest", "--snapshot", str(snapshot_path), "--feedback", str(draft_path), "--store", str(store)]) == 0
    assert main(["ingest", "--snapshot", str(snapshot_path), "--feedback", str(draft_path), "--store", str(store)]) == 2
    assert "duplicate" in capsys.readouterr().err


def test_ingest_rejects_duplicate_reviewer_for_same_claim(tmp_path: Path, capsys) -> None:
    snapshot_path = tmp_path / "case.run.json"
    _write_snapshot(snapshot_path)
    store = tmp_path / "feedback-store"
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    assert main(["prepare", "--snapshot", str(snapshot_path), "--claim-id", "claim-cli-001", "--out", str(first)]) == 0
    _filled_draft(first)
    assert main(["ingest", "--snapshot", str(snapshot_path), "--feedback", str(first), "--store", str(store)]) == 0

    payload = json.loads(first.read_text(encoding="utf-8"))
    payload["feedback_id"] = "feedback-distinct-id"
    second.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    assert main(["ingest", "--snapshot", str(snapshot_path), "--feedback", str(second), "--store", str(store)]) == 2
    assert "duplicate reviewer" in capsys.readouterr().err


def test_all_file_boundaries_reject_symlinks(tmp_path: Path, capsys) -> None:
    if not hasattr(os, "symlink"):
        pytest.skip("symlink unsupported")
    snapshot_path = tmp_path / "case.run.json"
    _write_snapshot(snapshot_path)
    snapshot_link = tmp_path / "snapshot-link.run.json"
    try:
        snapshot_link.symlink_to(snapshot_path)
    except OSError:
        pytest.skip("symlink creation not permitted")

    assert main(["prepare", "--snapshot", str(snapshot_link), "--claim-id", "claim-cli-001", "--out", str(tmp_path / "draft.json")]) == 2
    assert "symlink" in capsys.readouterr().err


def test_ingest_rejects_snapshot_tampering_and_orphan_claim(tmp_path: Path, capsys) -> None:
    snapshot_path = tmp_path / "case.run.json"
    _write_snapshot(snapshot_path)
    draft = tmp_path / "draft.json"
    assert main(["prepare", "--snapshot", str(snapshot_path), "--claim-id", "claim-cli-001", "--out", str(draft)]) == 0
    _filled_draft(draft)

    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    payload["claims"][0]["claim"] = "篡改"
    snapshot_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    assert main(["ingest", "--snapshot", str(snapshot_path), "--feedback", str(draft), "--store", str(tmp_path / "store")]) == 2
    assert "snapshot output hash mismatch" in capsys.readouterr().err

    clean_path = tmp_path / "clean.run.json"
    _write_snapshot(clean_path)
    orphan = json.loads(draft.read_text(encoding="utf-8"))
    orphan["claim_id"] = "missing-claim"
    draft.write_text(json.dumps(orphan, ensure_ascii=False), encoding="utf-8")
    assert main(["ingest", "--snapshot", str(clean_path), "--feedback", str(draft), "--store", str(tmp_path / "store-2")]) == 2
    assert "claim_id not found" in capsys.readouterr().err


def test_candidates_are_stdout_only_and_do_not_mutate_production_files(tmp_path: Path, capsys) -> None:
    snapshot_path = tmp_path / "case.run.json"
    _write_snapshot(snapshot_path, high_risk=False)
    store = tmp_path / "feedback-store"
    draft = tmp_path / "draft.json"
    assert main(["prepare", "--snapshot", str(snapshot_path), "--claim-id", "claim-cli-001", "--out", str(draft)]) == 0
    _filled_draft(draft, status="unknown")
    assert main(["ingest", "--snapshot", str(snapshot_path), "--feedback", str(draft), "--store", str(store)]) == 0
    capsys.readouterr()

    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert main(["candidates", "--store", str(store), "--snapshot", str(snapshot_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert payload["automatic_promotion"] is False
    assert payload["candidates"][0]["scored_outcome_count"] == 0
