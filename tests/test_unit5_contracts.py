from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


PUBLIC_CASES = (
    ("A01", "engine.archive.archive_verified_artifact"),
    ("A02", ("source", "archive_root")),
    ("A03", ("ArchiveInputError", "ArchiveConflictError", "ArchiveIOError")),
    ("A04", "ArchiveResult"),
)

CLI_ACCEPT_CASES = (
    ("A05", "success"),
    ("A06", "help"),
    ("A07", "version"),
    ("A08", "public-error"),
)

CLI_REJECT_CASES = (
    ("A09", ()),
    ("A10", ("--archive-root", "archive", "source.json")),
    ("A11", ("source.json", "--archive-root", "a", "--archive-root", "b")),
    ("A12", ("--help", "source.json", "--archive-root", "archive")),
)

IDEMPOTENCY_CASES = (
    ("B01", "create"),
    ("B02", "repeat"),
    ("B03", "canonical-repeat"),
    ("B04", "no-cache"),
)

CONFLICT_CASES = (
    ("B05", "payload"),
    ("B06", "metadata"),
    ("B07", "digest"),
    ("B08", "existing-bytes"),
)

ARTIFACT_CASES = (
    ("C01", "valid"),
    ("C02", "sidecar-missing"),
    ("C03", "sidecar-unreadable"),
    ("C04", "source-digest-mismatch"),
)

FIXED_REPORT_CASES = (
    ("D01", 33),
    ("D02", "labels"),
    ("D03", "lexemes"),
    ("D04", "encoding"),
    ("D05", 52),
)

EVENT_REPORT_CASES = (
    ("D06", 0),
    ("D07", 1),
    ("D08", 19),
    ("D09", "chronological"),
    ("D10", "reject-overflow"),
)

WINDOWS_PUBLISH_CASES = (
    ("E01", "same-parent"),
    ("E02", "exclusive-stage"),
    ("E03", "flush-close-rename"),
    ("E04", "no-replace"),
    ("E05", "readback"),
)

WINDOWS_FAILURE_CASES = (
    ("E06", "source-reparse"),
    ("E07", "root-reparse"),
    ("E08", "parent-reparse"),
    ("E09", "readback-mismatch"),
    ("E10", "safe-cleanup"),
)


def _module():
    return importlib.import_module("engine.archive")


def _artifact(*, artifact_id: str = "artifact-001", payload: dict | None = None) -> dict:
    payload = {"answer": 42} if payload is None else payload
    payload_bytes = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "schema_version": "verified-artifact/v1",
        "artifact_id": artifact_id,
        "source_digest": hashlib.sha256(b"source").hexdigest(),
        "payload_digest": hashlib.sha256(payload_bytes).hexdigest(),
        "verified_at": "2026-07-28T00:00:00+00:00",
        "verifier": "unit-test",
        "verification_basis": ["contract-fixture"],
        "payload": payload,
    }


def _write_artifact(
    path: Path,
    value: dict | None = None,
    *,
    formatted: bool = False,
    source_bytes: bytes = b"source",
) -> Path:
    value = _artifact() if value is None else value
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2 if formatted else None),
        encoding="utf-8",
    )
    path.with_name(path.name + ".source").write_bytes(source_bytes)
    return path


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tools.archive_verified_artifact", *args],
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize(("instance_id", "expected"), PUBLIC_CASES, ids=lambda value: value if isinstance(value, str) and value.startswith("A") else None)
def test_public_api_contract(instance_id: str, expected, tmp_path: Path) -> None:
    module = _module()
    if instance_id == "A01":
        assert module.archive_verified_artifact.__module__ + "." + module.archive_verified_artifact.__name__ == expected
    elif instance_id == "A02":
        signature = inspect.signature(module.archive_verified_artifact)
        assert tuple(signature.parameters) == expected
        assert all(parameter.annotation is not inspect.Parameter.empty for parameter in signature.parameters.values())
        assert signature.return_annotation in {module.ArchiveResult, "ArchiveResult"}
    elif instance_id == "A03":
        assert tuple(error.__name__ for error in module.PUBLIC_EXCEPTIONS) == expected
    else:
        source = _write_artifact(tmp_path / "source.json")
        assert type(module.archive_verified_artifact(source, tmp_path / "archive")).__name__ == expected


@pytest.mark.parametrize(("instance_id", "scenario"), CLI_ACCEPT_CASES, ids=lambda value: value if isinstance(value, str) and value.startswith("A") else None)
def test_cli_grammar_acceptance(instance_id: str, scenario: str, tmp_path: Path) -> None:
    if scenario == "help":
        completed = _run_cli("--help")
        assert completed.returncode == 0 and "usage:" in completed.stdout.lower() and completed.stderr == ""
        return
    if scenario == "version":
        completed = _run_cli("--version")
        assert completed.returncode == 0 and completed.stdout.strip() and completed.stderr == ""
        return
    source = _write_artifact(tmp_path / "source.json")
    if scenario == "public-error":
        bad = _artifact()
        bad["verifier"] = "invalid|report-text"
        _write_artifact(source, bad)
        archive = tmp_path / "archive"
        completed = _run_cli(str(source), "--archive-root", str(archive))
        assert completed.returncode == 1 and completed.stdout == "" and completed.stderr.strip()
        assert not archive.exists()
        return
    completed = _run_cli(str(source), "--archive-root", str(tmp_path / "archive"))
    assert completed.returncode == 0 and completed.stdout.strip() and completed.stderr == ""


@pytest.mark.parametrize(("instance_id", "argv"), CLI_REJECT_CASES, ids=lambda value: value if isinstance(value, str) and value.startswith("A") else None)
def test_cli_grammar_rejection(instance_id: str, argv: tuple[str, ...], tmp_path: Path) -> None:
    completed = _run_cli(*argv)
    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr.strip()
    assert not (tmp_path / "archive").exists()


@pytest.mark.parametrize(("instance_id", "scenario"), IDEMPOTENCY_CASES, ids=lambda value: value if isinstance(value, str) and value.startswith("B") else None)
def test_archive_idempotency(instance_id: str, scenario: str, tmp_path: Path) -> None:
    module = _module()
    source = _write_artifact(tmp_path / "source.json", formatted=scenario == "canonical-repeat")
    archive = tmp_path / "archive"
    first = module.archive_verified_artifact(source, archive)
    before = first.target.read_bytes()
    if scenario == "create":
        assert first.status == "CREATED" and first.target.exists()
        return
    if scenario == "no-cache":
        source.unlink()
        source.with_name(source.name + ".source").unlink()
        with pytest.raises(module.ArchiveInputError):
            module.archive_verified_artifact(source, archive)
        return
    if scenario == "canonical-repeat":
        _write_artifact(source, formatted=False)
    second = module.archive_verified_artifact(source, archive)
    assert second.status == "UNCHANGED"
    assert second.target.read_bytes() == before


@pytest.mark.parametrize(("instance_id", "mutation"), CONFLICT_CASES, ids=lambda value: value if isinstance(value, str) and value.startswith("B") else None)
def test_archive_conflict(instance_id: str, mutation: str, tmp_path: Path) -> None:
    module = _module()
    source = _write_artifact(tmp_path / "source.json")
    archive = tmp_path / "archive"
    created = module.archive_verified_artifact(source, archive)
    before = created.target.read_bytes()
    changed = _artifact()
    if mutation == "payload":
        changed = _artifact(payload={"answer": 43})
    elif mutation == "metadata":
        changed["verifier"] = "other"
    elif mutation == "digest":
        changed["source_digest"] = hashlib.sha256(b"other").hexdigest()
    else:
        created.target.write_bytes(before + b" ")
        before = created.target.read_bytes()
    _write_artifact(source, changed, source_bytes=b"other" if mutation == "digest" else b"source")
    with pytest.raises(module.ArchiveConflictError):
        module.archive_verified_artifact(source, archive)
    assert created.target.read_bytes() == before


@pytest.mark.parametrize(("instance_id", "scenario"), ARTIFACT_CASES, ids=lambda value: value if isinstance(value, str) and value.startswith("C") else None)
def test_verified_artifact_boundary(instance_id: str, scenario: str, tmp_path: Path) -> None:
    module = _module()
    value = _artifact()
    source = _write_artifact(tmp_path / "source.json", value)
    sidecar = source.with_name(source.name + ".source")
    if scenario == "sidecar-missing":
        sidecar.unlink()
    elif scenario == "sidecar-unreadable":
        sidecar.unlink()
        sidecar.mkdir()
    elif scenario == "source-digest-mismatch":
        sidecar.write_bytes(b"digest-mismatch")
    if scenario == "valid":
        result = module.archive_verified_artifact(source, tmp_path / "archive")
        assert result.payload_digest == value["payload_digest"]
    else:
        with pytest.raises(module.ArchiveInputError):
            module.archive_verified_artifact(source, tmp_path / "archive")

    if scenario == "source-digest-mismatch":
        sidecar.write_bytes(b"source")
        value["verifier"] = "\ud800"
        source.write_text(json.dumps(value, ensure_ascii=True), encoding="utf-8")
        with pytest.raises(module.ArchiveInputError):
            module.archive_verified_artifact(source, tmp_path / "archive")


@pytest.mark.parametrize(("instance_id", "oracle"), FIXED_REPORT_CASES, ids=lambda value: value if isinstance(value, str) and value.startswith("D") else None)
def test_report_fixed_region(instance_id: str, oracle, tmp_path: Path) -> None:
    module = _module()
    result = module.archive_verified_artifact(_write_artifact(tmp_path / "source.json"), tmp_path / "archive")
    encoded = result.report.encode("utf-8")
    lines = result.report.removesuffix("\n").split("\n")
    if instance_id == "D01":
        assert lines[32] == "EVENTS: BEGIN" and len(lines[:33]) == oracle
    elif instance_id == "D02":
        labels = [line.split(":", 1)[0] for line in lines[1:32]]
        assert labels[:4] == ["report-schema", "artifact-id", "artifact-schema", "source-digest"]
        assert labels[-7:] == [f"reserved-0{i}" for i in range(1, 8)]
    elif instance_id == "D03":
        assert lines[19:25] == [
            "digest-algorithm: sha256", "text-encoding: utf-8", "line-ending: lf",
            "fixed-line-count: 33", "event-line-count: 19", "total-line-count: 52",
        ]
    elif instance_id == "D04":
        assert not encoded.startswith(b"\xef\xbb\xbf") and b"\r" not in encoded
        assert all(not line.endswith(" ") for line in lines)
    else:
        assert len(lines) == oracle and result.report.endswith("\n") and not result.report.endswith("\n\n")


@pytest.mark.parametrize(("instance_id", "oracle"), EVENT_REPORT_CASES, ids=lambda value: value if isinstance(value, str) and value.startswith("D") else None)
def test_report_event_region(instance_id: str, oracle, tmp_path: Path) -> None:
    module = _module()
    count = oracle if isinstance(oracle, int) else 2
    events = [
        {"time": f"2026-07-28T00:00:{index:02d}+00:00", "kind": "STEP", "detail": f"event-{index}"}
        for index in range(count)
    ]
    if oracle == "chronological":
        events.reverse()
    if oracle == "reject-overflow":
        events = events * 10
        with pytest.raises(module.ArchiveInputError):
            module._render_report(_artifact(), "CREATED", Path("target.json"), events)
        return
    report = module._render_report(_artifact(), "CREATED", Path("target.json"), events)
    lines = report.removesuffix("\n").split("\n")
    event_lines = lines[33:]
    used = [line for line in event_lines if ": USED|" in line]
    assert len(event_lines) == 19 and len(used) == count
    assert all(line == f"event-{index:02d}: EMPTY|-|-|-" for index, line in enumerate(event_lines[count:], count + 1))
    if oracle == "chronological":
        times = [line.split("|")[1] for line in used]
        assert times == sorted(times)


@pytest.mark.parametrize(("instance_id", "scenario"), WINDOWS_PUBLISH_CASES, ids=lambda value: value if isinstance(value, str) and value.startswith("E") else None)
def test_windows_publish_flow(instance_id: str, scenario: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    calls: list[tuple] = []
    real_open = module._open_stage
    real_rename = module._rename_no_replace
    real_readback = module._readback
    real_identity = module._identity_snapshot
    real_fsync = module.os.fsync

    class ObservedHandle:
        def __init__(self, handle):
            self.handle = handle

        def write(self, value):
            calls.append(("write",))
            return self.handle.write(value)

        def flush(self):
            calls.append(("flush",))
            return self.handle.flush()

        def fileno(self):
            return self.handle.fileno()

        def close(self):
            calls.append(("close",))
            return self.handle.close()

    def open_stage(parent, *args, **kwargs):
        calls.append(("stage", Path(parent)))
        handle, path = real_open(parent, *args, **kwargs)
        return ObservedHandle(handle), path

    def fsync(descriptor):
        calls.append(("fsync",))
        return real_fsync(descriptor)

    def rename(source, target):
        calls.append(("rename", Path(source), Path(target), Path(source).parent == Path(target).parent))
        if scenario == "no-replace":
            Path(target).write_bytes(b"competitor")
        return real_rename(source, target)

    def readback(target):
        calls.append(("readback", Path(target)))
        return real_readback(target)

    def identity(path):
        snapshot = real_identity(path)
        calls.append(("identity", Path(path), snapshot))
        return snapshot

    monkeypatch.setattr(module, "_open_stage", open_stage)
    monkeypatch.setattr(module, "_rename_no_replace", rename)
    monkeypatch.setattr(module, "_readback", readback)
    monkeypatch.setattr(module, "_identity_snapshot", identity)
    monkeypatch.setattr(module.os, "fsync", fsync)
    source = _write_artifact(tmp_path / "source.json")
    if scenario == "no-replace":
        with pytest.raises(module.ArchiveConflictError):
            module.archive_verified_artifact(source, tmp_path / "archive")
        target = tmp_path / "archive" / "artifact-001.json"
        assert target.read_bytes() == b"competitor"
        return
    result = module.archive_verified_artifact(source, tmp_path / "archive")
    names = [call[0] for call in calls]
    if scenario == "same-parent":
        assert calls[0][1] == result.target.parent
    elif scenario == "exclusive-stage":
        assert names.count("stage") == 1 and not any(result.target.parent.glob("*.staging"))
    elif scenario == "flush-close-rename":
        archive_identities = [call for call in calls if call[0] == "identity" and call[1] == result.target.parent]
        assert names.index("write") < names.index("flush") < names.index("fsync") < names.index("close") < names.index("rename")
        assert len(archive_identities) >= 2 and archive_identities[0][2] == archive_identities[-1][2]
    else:
        assert names.index("rename") < names.index("readback")
        assert result.target.read_bytes() == module._canonical_json(_artifact())


@pytest.mark.parametrize(("instance_id", "scenario"), WINDOWS_FAILURE_CASES, ids=lambda value: value if isinstance(value, str) and value.startswith("E") else None)
def test_windows_reparse_and_failure_flow(instance_id: str, scenario: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    source = _write_artifact(tmp_path / "source.json")
    archive = tmp_path / "archive"
    if "reparse" in scenario:
        if scenario == "parent-reparse":
            real_identity = module._identity_snapshot
            observations = {"count": 0}

            def changed_identity(path):
                snapshot = real_identity(path)
                if Path(path) == archive:
                    observations["count"] += 1
                    if observations["count"] > 1:
                        return (*snapshot[:-1], snapshot[-1] + "-changed")
                return snapshot

            monkeypatch.setattr(module, "_identity_snapshot", changed_identity)
            with pytest.raises(module.ArchiveIOError, match="identity"):
                module.archive_verified_artifact(source, archive)
            assert not list(archive.rglob("*.staging")) if archive.exists() else True
            return
        real_check = module._reject_reparse

        def reject(path):
            path = Path(path)
            if (scenario == "source-reparse" and path == source) or (
                scenario == "root-reparse" and path == archive
            ):
                raise module.ArchiveInputError("reparse point")
            return real_check(path)

        monkeypatch.setattr(module, "_reject_reparse", reject)
        with pytest.raises(module.ArchiveInputError):
            module.archive_verified_artifact(source, archive)
        assert not archive.exists()
    elif scenario == "readback-mismatch":
        real_readback = module._readback
        monkeypatch.setattr(module, "_readback", lambda _path: b"mismatch")
        with pytest.raises(module.ArchiveIOError, match="readback mismatch"):
            module.archive_verified_artifact(source, archive)

        monkeypatch.setattr(module, "_readback", real_readback)
        stable_archive = tmp_path / "stable-archive"
        module.archive_verified_artifact(source, stable_archive)
        real_identity = module._identity_snapshot
        observations = {"target": 0}

        def replaced_existing_target(path):
            snapshot = real_identity(path)
            if Path(path).name == "artifact-001.json":
                observations["target"] += 1
                if observations["target"] > 1:
                    return (*snapshot[:-1], snapshot[-1] + "-replaced")
            return snapshot

        monkeypatch.setattr(module, "_identity_snapshot", replaced_existing_target)
        with pytest.raises(module.ArchiveIOError, match="identity"):
            module.archive_verified_artifact(source, stable_archive)
    else:
        class BrokenHandle:
            def write(self, _value):
                raise OSError("write failed")

            def close(self):
                return None

        real_open = module._open_stage

        def broken_open(parent):
            handle, stage = real_open(parent)
            handle.close()
            return BrokenHandle(), stage

        monkeypatch.setattr(module, "_open_stage", broken_open)
        with pytest.raises(module.ArchiveIOError):
            module.archive_verified_artifact(source, archive)
        assert not list(archive.rglob("*.staging")) if archive.exists() else True
