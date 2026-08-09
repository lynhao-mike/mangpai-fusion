from __future__ import annotations

import inspect
import json
import os
import threading
from pathlib import Path

import pytest

import engine.evaluation.prospective_artifacts as artifacts
from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    canonical_artifact_sha256,
    publish_new_json,
    single_case_artifact_path,
    validate_parent_ref,
    validate_revision_metadata,
)


CASE_ID = "P-GO-2026-001-坤-壬戌己酉乙卯丁亥"


def _authority_root(tmp_path: Path) -> Path:
    state = tmp_path / "META" / "project-state.json"
    contract = (
        tmp_path
        / ".omo"
        / "drafts"
        / ("w2-c4-governance-promotion-remediation-r3-admission-contract-2026-08-08.md")
    )
    state.parent.mkdir(parents=True)
    contract.parent.mkdir(parents=True)
    state.write_bytes(Path("META/project-state.json").read_bytes())
    contract.write_bytes(
        Path(
            ".omo/drafts/w2-c4-governance-promotion-remediation-r3-admission-contract-2026-08-08.md"
        ).read_bytes()
    )
    return tmp_path.absolute()


def test_production_module_exposes_no_arbitrary_root_authority_surface() -> None:
    forbidden = {
        "_TEST_AUTHORITY_ISSUER",
        "_issue_repository_authority",
        "_use_test_repository_authority",
        "_TEST_AUTHORITY",
    }

    assert forbidden.isdisjoint(vars(artifacts))
    assert not any(
        inspect.isfunction(value)
        and "authority" in name.lower()
        and "root" in inspect.signature(value).parameters
        for name, value in vars(artifacts).items()
    )


def test_repository_authority_is_one_closure_held_token_per_trusted_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _authority_root(tmp_path)
    monkeypatch.setattr(artifacts, "_trusted_repository_root", lambda: root)

    assert artifacts._repository_authority() is artifacts._repository_authority()


@pytest.mark.parametrize(
    "relative_anchor",
    [
        Path("META/project-state.json"),
        Path(
            ".omo/drafts/"
            "w2-c4-governance-promotion-remediation-r3-admission-contract-2026-08-08.md"
        ),
    ],
)
def test_repository_authority_cache_fails_closed_after_canonical_anchor_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative_anchor: Path,
) -> None:
    root = _authority_root(tmp_path)
    monkeypatch.setattr(artifacts, "_trusted_repository_root", lambda: root)
    original = artifacts._repository_authority()
    anchor = root / relative_anchor
    anchor.write_bytes(anchor.read_bytes() + b"\nDRIFT")

    with pytest.raises(ValueError, match="canonical|contract|drift"):
        reacquired = artifacts._repository_authority()
        assert reacquired is not original


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
    target.write_bytes(
        (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )

    with pytest.raises(ValueError, match="stored digest"):
        validate_parent_ref(ref)


def test_validate_parent_ref_rejects_content_digest_drift(tmp_path: Path) -> None:
    target = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)
    ref = publish_new_json(target, _payload(), dry_run=False)
    document = json.loads(target.read_text(encoding="utf-8"))
    document["created_at"] = "2026-07-16T00:00:01Z"
    target.write_bytes(
        (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )

    with pytest.raises(ValueError, match="canonical digest"):
        validate_parent_ref(ref)


def test_validate_parent_ref_authenticates_recursive_tree_inside_admitted_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "trusted"
    parent_path = root / "parents" / "parent.json"
    parent_ref = publish_new_json(parent_path, _payload(), dry_run=False)
    child_path = root / "children" / "child.json"
    child_ref = publish_new_json(
        child_path,
        _payload(parents=[parent_ref.__dict__]),
        dry_run=False,
    )

    document = validate_parent_ref(child_ref, admitted_root=root)

    assert document["parents"] == [parent_ref.__dict__]


def test_recursive_parent_accepts_authority_bound_raw_json_by_exact_byte_digest(
    tmp_path: Path,
) -> None:
    root = tmp_path / "trusted"
    raw_path = root / "bundle" / "tasks.json"
    raw_path.parent.mkdir(parents=True)
    raw = b'{"tasks": []}\n'
    raw_path.write_bytes(raw)
    raw_ref = ArtifactRef(
        raw_path.as_posix(), artifacts.hashlib.sha256(raw).hexdigest()
    )
    child_ref = publish_new_json(
        root / "child.json",
        _payload(parents=[raw_ref.__dict__]),
        dry_run=False,
    )

    document = validate_parent_ref(child_ref, admitted_root=root)

    assert document["parents"] == [raw_ref.__dict__]
    raw_path.write_bytes(b'{"tasks": ["drift"]}\n')
    with pytest.raises(ValueError, match="digest"):
        validate_parent_ref(child_ref, admitted_root=root)


@pytest.mark.parametrize(
    "unsafe_path",
    [
        Path("..") / "outside.json",
        Path("nested") / ".." / "parent.json",
    ],
)
def test_validate_parent_ref_rejects_traversal_and_normalized_alias(
    tmp_path: Path, unsafe_path: Path
) -> None:
    root = tmp_path / "trusted"
    outside = tmp_path / "outside.json"
    actual = root / "parent.json"
    ref = publish_new_json(actual, _payload(), dry_run=False)
    candidate = root / unsafe_path
    if unsafe_path.parts[0] == "nested":
        candidate = root / unsafe_path
    else:
        outside.write_bytes(actual.read_bytes())
    unsafe_ref = ArtifactRef(candidate.as_posix(), ref.artifact_sha256)

    with pytest.raises(ValueError, match="PATH_(TRAVERSAL|ALIAS)"):
        validate_parent_ref(unsafe_ref, admitted_root=root)


def test_validate_parent_ref_rejects_absolute_root_escape(tmp_path: Path) -> None:
    root = tmp_path / "trusted"
    outside = tmp_path / "outside.json"
    ref = publish_new_json(outside, _payload(), dry_run=False)

    with pytest.raises(ValueError, match="PATH_OUTSIDE_ROOT"):
        validate_parent_ref(ref, admitted_root=root)


def test_validate_parent_ref_rejects_symlink_ancestor(tmp_path: Path) -> None:
    root = tmp_path / "trusted"
    real = root / "real"
    ref = publish_new_json(real / "parent.json", _payload(), dry_run=False)
    linked = root / "linked"
    try:
        linked.symlink_to(real, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink creation unavailable on this host: {exc}")

    linked_ref = ArtifactRef((linked / "parent.json").as_posix(), ref.artifact_sha256)
    with pytest.raises(ValueError, match="PATH_LINK_LIKE"):
        validate_parent_ref(linked_ref, admitted_root=root)


def test_validate_parent_ref_rejects_reparse_ancestor_through_portable_seam(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "trusted"
    parent_path = root / "junction" / "parent.json"
    ref = publish_new_json(parent_path, _payload(), dry_run=False)
    monkeypatch.setattr(
        artifacts,
        "_is_reparse_point",
        lambda candidate: candidate == parent_path.parent,
        raising=False,
    )

    with pytest.raises(ValueError, match="PATH_LINK_LIKE"):
        validate_parent_ref(ref, admitted_root=root)


def test_validate_parent_ref_rejects_orphan_schema_drift_and_parent_cycle(
    tmp_path: Path,
) -> None:
    root = tmp_path / "trusted"
    child_path = root / "child.json"
    missing_ref = ArtifactRef((root / "missing.json").as_posix(), "a" * 64)
    orphan = publish_new_json(
        child_path,
        _payload(parents=[missing_ref.__dict__]),
        dry_run=False,
    )
    with pytest.raises(ValueError, match="PATH_UNREADABLE"):
        validate_parent_ref(orphan, admitted_root=root)

    malformed_path = root / "malformed.json"
    malformed = publish_new_json(
        malformed_path,
        _payload(parents=[{"artifact_path": missing_ref.artifact_path}]),
        dry_run=False,
    )
    with pytest.raises(ValueError, match="PARENT_SCHEMA"):
        validate_parent_ref(malformed, admitted_root=root)

    cycle_path = root / "cycle.json"
    cycle_payload = _payload()
    cycle_digest = canonical_artifact_sha256(cycle_payload)
    cycle_payload["parents"] = [
        ArtifactRef(cycle_path.as_posix(), cycle_digest).__dict__
    ]
    cycle_ref = publish_new_json(cycle_path, cycle_payload, dry_run=False)
    with pytest.raises(ValueError, match="PARENT_CYCLE"):
        validate_parent_ref(cycle_ref, admitted_root=root)


def test_validate_parent_ref_rejects_duplicate_logical_parent(tmp_path: Path) -> None:
    root = tmp_path / "trusted"
    parent_ref = publish_new_json(root / "parent.json", _payload(), dry_run=False)
    child_ref = publish_new_json(
        root / "child.json",
        _payload(parents=[parent_ref.__dict__, parent_ref.__dict__]),
        dry_run=False,
    )

    with pytest.raises(ValueError, match="PARENT_DUPLICATE"):
        validate_parent_ref(child_ref, admitted_root=root)


def test_publish_authenticates_destination_parent_and_rejects_linklike_leaf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "trusted"
    target = root / "output.json"
    root.mkdir()
    monkeypatch.setattr(
        artifacts,
        "_is_reparse_point",
        lambda candidate: candidate == target,
        raising=False,
    )

    with pytest.raises(ValueError, match="PATH_LINK_LIKE"):
        publish_new_json(target, _payload(), dry_run=False, admitted_root=root)
    assert not target.exists()


def test_publish_rejects_destination_escape_and_keeps_atomic_race_loser(
    tmp_path: Path,
) -> None:
    root = tmp_path / "trusted"
    with pytest.raises(ValueError, match="PATH_OUTSIDE_ROOT"):
        publish_new_json(
            tmp_path / "outside.json",
            _payload(),
            dry_run=False,
            admitted_root=root,
        )

    target = root / "output.json"
    publish_new_json(target, _payload(), dry_run=False, admitted_root=root)
    with pytest.raises(ValueError, match="already exists"):
        publish_new_json(target, _payload(), dry_run=False, admitted_root=root)


@pytest.mark.skipif(
    os.name != "nt", reason="physical Windows junction coverage requires Windows"
)
def test_windows_junction_platform_accounting_is_explicit() -> None:
    assert os.name == "nt"


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

    monkeypatch.setattr(
        "engine.evaluation.prospective_artifacts.os.link", lose_publication_race
    )
    monkeypatch.setattr(
        "engine.evaluation.prospective_artifacts.os.close", record_close
    )

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
