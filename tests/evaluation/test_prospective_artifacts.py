from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    canonical_artifact_sha256,
    publish_new_json,
    single_case_artifact_path,
    validate_parent_ref,
    validate_revision_metadata,
)


CASE_ID = "P-GO-2026-001-坤-壬戌己酉乙卯丁亥"


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "prospective-artifact/v1",
        "case_id": CASE_ID,
        "subject_id_hash": "a" * 64,
        "created_at": "2026-07-16T00:00:00Z",
        "parents": [],
    }
    payload.update(overrides)
    return payload


def test_single_case_name_and_hash_exclude_self_digest(tmp_path: Path) -> None:
    path = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)

    assert path.name == f"{CASE_ID}--intake--v001.json"
    payload = {
        "schema_version": "x/v1",
        "case_id": CASE_ID,
        "artifact_sha256": "0" * 64,
    }
    assert canonical_artifact_sha256(payload) == canonical_artifact_sha256(
        {**payload, "artifact_sha256": "f" * 64}
    )


@pytest.mark.parametrize(
    ("case_id", "artifact_kind", "version"),
    [
        ("P-GO-2026-1-坤-壬戌己酉乙卯丁亥", "intake", 1),
        (CASE_ID, "Intake", 1),
        (CASE_ID, "intake_json", 1),
        (CASE_ID, "intake", 0),
    ],
)
def test_single_case_path_rejects_invalid_identity(
    tmp_path: Path, case_id: str, artifact_kind: str, version: int
) -> None:
    with pytest.raises(ValueError, match="invalid"):
        single_case_artifact_path(tmp_path, case_id, artifact_kind, version)


def test_publish_dry_run_returns_ref_without_writing(tmp_path: Path) -> None:
    target = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)

    ref = publish_new_json(target, _payload(), dry_run=True)

    assert ref == ArtifactRef(target.as_posix(), canonical_artifact_sha256(_payload()))
    assert not target.exists()
    assert not target.parent.exists()


def test_publish_is_create_only_and_parent_hash_is_recomputed(tmp_path: Path) -> None:
    target = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)
    payload = _payload()

    ref = publish_new_json(target, payload, dry_run=False)

    assert ref.artifact_path == target.as_posix()
    with pytest.raises(ValueError, match="already exists"):
        publish_new_json(target, payload, dry_run=False)
    assert validate_parent_ref(ref) == json.loads(target.read_text(encoding="utf-8"))


def test_publish_rejects_dangling_symlink(tmp_path: Path) -> None:
    target = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)
    target.parent.mkdir(parents=True)
    try:
        target.symlink_to(target.parent / "missing.json")
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable on this Windows host: {exc}")

    with pytest.raises(ValueError, match="already exists"):
        publish_new_json(target, _payload(), dry_run=False)


def test_validate_parent_ref_rejects_byte_drift(tmp_path: Path) -> None:
    target = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)
    ref = publish_new_json(target, _payload(), dry_run=False)
    target.write_bytes(target.read_bytes() + b" ")

    with pytest.raises(ValueError, match="byte drift"):
        validate_parent_ref(ref)


def test_validate_parent_ref_rejects_stored_digest_drift(tmp_path: Path) -> None:
    target = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)
    ref = publish_new_json(target, _payload(), dry_run=False)
    document = json.loads(target.read_text(encoding="utf-8"))
    document["artifact_sha256"] = "f" * 64
    target.write_bytes((json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    with pytest.raises(ValueError, match="stored digest"):
        validate_parent_ref(ref)


def test_validate_parent_ref_rejects_content_digest_drift(tmp_path: Path) -> None:
    target = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)
    ref = publish_new_json(target, _payload(), dry_run=False)
    document = json.loads(target.read_text(encoding="utf-8"))
    document["created_at"] = "2026-07-16T00:00:01Z"
    target.write_bytes((json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    with pytest.raises(ValueError, match="canonical digest"):
        validate_parent_ref(ref)


def test_v002_requires_complete_named_human_revision_metadata() -> None:
    valid = _payload(
        supersedes="previous.json",
        supersedes_sha256="b" * 64,
        reason="Correct operator transcription",
        approved_by="human-reviewer-01",
    )
    validate_revision_metadata(valid, 2)

    for field in ("supersedes", "supersedes_sha256", "reason", "approved_by"):
        invalid = dict(valid)
        invalid.pop(field)
        with pytest.raises(ValueError, match=field):
            validate_revision_metadata(invalid, 2)

    with pytest.raises(ValueError, match="approved_by"):
        validate_revision_metadata({**valid, "approved_by": "  "}, 2)


@pytest.mark.parametrize(
    "field",
    ["supersedes", "supersedes_sha256", "reason", "approved_by"],
)
def test_v001_rejects_revision_metadata(field: str) -> None:
    with pytest.raises(ValueError, match="v001"):
        validate_revision_metadata(_payload(**{field: "unexpected"}), 1)


def test_publishing_v002_preserves_v001_bytes(tmp_path: Path) -> None:
    v001 = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)
    first_ref = publish_new_json(v001, _payload(), dry_run=False)
    original_bytes = v001.read_bytes()
    v002 = single_case_artifact_path(tmp_path, CASE_ID, "intake", 2)
    revised = _payload(
        created_at="2026-07-16T01:00:00Z",
        supersedes=first_ref.artifact_path,
        supersedes_sha256=first_ref.artifact_sha256,
        reason="Correct operator transcription",
        approved_by="human-reviewer-01",
    )
    validate_revision_metadata(revised, 2)

    publish_new_json(v002, revised, dry_run=False)

    assert v001.read_bytes() == original_bytes
    assert v002.exists()


def test_publish_race_loser_does_not_close_an_already_owned_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)
    closed_descriptors: list[int] = []
    real_close = __import__("os").close

    def lose_publication_race(source: Path, destination: Path) -> None:
        raise FileExistsError(destination)

    def record_close(descriptor: int) -> None:
        closed_descriptors.append(descriptor)
        real_close(descriptor)

    monkeypatch.setattr("engine.evaluation.prospective_artifacts.os.link", lose_publication_race)
    monkeypatch.setattr("engine.evaluation.prospective_artifacts.os.close", record_close)

    with pytest.raises(ValueError, match="already exists"):
        publish_new_json(target, _payload(), dry_run=False)

    assert closed_descriptors == []
    assert not list(target.parent.glob("*.tmp"))


def test_publish_is_atomic_create_only_under_race(tmp_path: Path) -> None:
    target = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def publish(created_at: str) -> None:
        barrier.wait()
        try:
            publish_new_json(target, _payload(created_at=created_at), dry_run=False)
        except ValueError as exc:
            outcomes.append(str(exc))
        else:
            outcomes.append("published")

    threads = [
        threading.Thread(target=publish, args=("2026-07-16T00:00:00Z",)),
        threading.Thread(target=publish, args=("2026-07-16T00:00:01Z",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert outcomes.count("published") == 1
    assert sum("already exists" in outcome for outcome in outcomes) == 1
    document = json.loads(target.read_text(encoding="utf-8"))
    assert document["artifact_sha256"] == canonical_artifact_sha256(document)
    assert not list(target.parent.glob("*.tmp"))
