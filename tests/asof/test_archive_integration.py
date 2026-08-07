from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
import os
from dataclasses import fields, replace
from datetime import date, datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, get_type_hints

import pytest

import engine.archive as archive_backend
from engine.asof.career_state_builder import CareerAdjudicationBundle, CareerStateBuildResult
from engine.asof.consultation_freeze import (
    FREEZE_PACKAGE_SCHEMA_VERSION,
    CareerFreezePackage,
    FrozenCareerFundamental,
    compute_freeze_package_sha256,
)
from engine.asof.future_projection import (
    FutureProjectionFromState,
    UnsupportedDomainProjection,
    UnsupportedDomainStatus,
)
from engine.asof.reality_track import RealityTrack
from engine.asof.session_contract import (
    SESSION_SCHEMA_VERSION,
    ConsultationState,
    SessionEnvelope,
    SessionIdentity,
)
from engine.asof.state_ledger import DecisionAction, VerifiedState


MODULE_NAME = "engine.asof.archive_integration"
TARGET = Path("tests/asof/test_archive_integration.py")
CASE_ID = "C-2026-001-乾-庚申戊寅壬子辛丑"
AS_OF = date(2020, 1, 1)
VERIFIED_AT = "2026-07-28T00:00:00+00:00"
PAYLOAD_FIELDS = {
    "schema_version",
    "envelope",
    "freeze_package",
    "adjudication_bundle",
    "state_result",
    "projection",
}
ARTIFACT_FIELDS = {
    "schema_version",
    "artifact_id",
    "source_digest",
    "payload_digest",
    "verified_at",
    "verifier",
    "verification_basis",
    "payload",
}


def _api() -> ModuleType:
    """仅在测试执行期导入 wished-for Unit 6 API。"""

    return importlib.import_module(MODULE_NAME)


def _identity(**changes: Any) -> SessionIdentity:
    values = {
        "schema_version": SESSION_SCHEMA_VERSION,
        "case_id": CASE_ID,
        "as_of_date": AS_OF,
        "session_id": "S-20260727T120000Z-0123abcd",
    }
    values.update(changes)
    return SessionIdentity(**values)


def _envelope(state: ConsultationState, **changes: Any) -> SessionEnvelope:
    values = {"identity": _identity(), "blind_input_sha256": "1" * 64, "state": state}
    values.update(changes)
    return SessionEnvelope(**values)


def _fundamental() -> FrozenCareerFundamental:
    return FrozenCareerFundamental(
        fundamental_id="career-baseline",
        window_start=date(2019, 1, 1),
        window_end=AS_OF,
        window_center=date(2019, 7, 2),
        center="mid-level professional",
        reasonable_range=("specialist", "team lead"),
        strongest_alternative="independent specialist",
        falsifiers=("no sustained professional responsibility",),
    )


def _objects(*, projected: bool = False) -> tuple[
    SessionEnvelope,
    CareerFreezePackage,
    CareerAdjudicationBundle,
    CareerStateBuildResult,
    FutureProjectionFromState | None,
]:
    identity = _identity()
    freeze_package = CareerFreezePackage(
        FREEZE_PACKAGE_SCHEMA_VERSION,
        identity,
        "1" * 64,
        (_fundamental(),),
        (),
    )
    digest = compute_freeze_package_sha256(freeze_package)
    adjudication_bundle = CareerAdjudicationBundle(
        _envelope(ConsultationState.ADJUDICATED),
        digest,
        freeze_package,
        (),
        (),
        freeze_package.fundamentals[0],
    )
    track = RealityTrack(CASE_ID, AS_OF, (), (), ())
    verified_state = VerifiedState(
        CASE_ID,
        AS_OF,
        track,
        "mid-level professional",
        ("specialist", "team lead"),
        (),
        (),
        DecisionAction.OUTPUT,
    )
    state_result = CareerStateBuildResult(
        _envelope(ConsultationState.STATE_BUILT),
        (),
        verified_state,
        (),
    )
    projection = None
    envelope = state_result.envelope
    if projected:
        projection = FutureProjectionFromState(
            _envelope(ConsultationState.PROJECTED),
            (),
            (),
            (),
            (),
            (
                UnsupportedDomainProjection(
                    "health",
                    UnsupportedDomainStatus.NOT_IMPLEMENTED,
                    DecisionAction.ABSTAIN,
                ),
            ),
        )
        envelope = projection.envelope
    return envelope, freeze_package, adjudication_bundle, state_result, projection


def _serialize(api: ModuleType, *, projected: bool = False, values: tuple[Any, ...] | None = None) -> dict[str, object]:
    arguments = _objects(projected=projected) if values is None else values
    return api.serialize_asof_archive_payload(*arguments)


def _archive(api: ModuleType, tmp_path: Path, *, projected: bool = False, artifact_id: str = "asof-unit6-001", values: tuple[Any, ...] | None = None):
    arguments = _objects(projected=projected) if values is None else values
    return api.archive_asof_state(
        *arguments,
        archive_root=tmp_path / "archive",
        artifact_id=artifact_id,
        verified_at=VERIFIED_AT,
        verifier="unit6-test",
        verification_basis=("unit5-contract", "unit6-integration"),
    )


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _assert_archive_input(api: ModuleType, operation: Callable[[], Any]) -> None:
    with pytest.raises(archive_backend.ArchiveInputError) as caught:
        operation()
    assert caught.type is archive_backend.ArchiveInputError


def test_public_surface_is_exactly_two_module_owned_callables_and_has_no_cli() -> None:
    api = _api()
    public_callables = {
        name
        for name, value in vars(api).items()
        if not name.startswith("_")
        and callable(value)
        and getattr(value, "__module__", None) == MODULE_NAME
    }
    assert public_callables == {"serialize_asof_archive_payload", "archive_asof_state"}

    serializer = inspect.signature(api.serialize_asof_archive_payload)
    archive = inspect.signature(api.archive_asof_state)
    assert tuple(serializer.parameters) == (
        "envelope",
        "freeze_package",
        "adjudication_bundle",
        "state_result",
        "projection",
    )
    assert tuple(archive.parameters) == (
        "envelope",
        "freeze_package",
        "adjudication_bundle",
        "state_result",
        "projection",
        "archive_root",
        "artifact_id",
        "verified_at",
        "verifier",
        "verification_basis",
    )

    shared_annotations = {
        "envelope": SessionEnvelope,
        "freeze_package": CareerFreezePackage,
        "adjudication_bundle": CareerAdjudicationBundle,
        "state_result": CareerStateBuildResult,
        "projection": FutureProjectionFromState | None,
    }
    assert get_type_hints(api.serialize_asof_archive_payload) == {
        **shared_annotations,
        "return": dict[str, object],
    }
    assert get_type_hints(api.archive_asof_state) == {
        **shared_annotations,
        "archive_root": os.PathLike[str] | str,
        "artifact_id": str,
        "verified_at": str,
        "verifier": str,
        "verification_basis": tuple[str, ...],
        "return": archive_backend.ArchiveResult,
    }
    positional = inspect.Parameter.POSITIONAL_OR_KEYWORD
    keyword_only = inspect.Parameter.KEYWORD_ONLY
    assert all(parameter.kind is positional for parameter in serializer.parameters.values())
    assert all(parameter.kind is positional for parameter in tuple(archive.parameters.values())[:5])
    assert all(parameter.kind is keyword_only for parameter in tuple(archive.parameters.values())[5:])
    assert serializer.parameters["projection"].default is None
    assert archive.parameters["projection"].default is inspect.Parameter.empty
    assert all(
        parameter.default is inspect.Parameter.empty
        for name, parameter in serializer.parameters.items()
        if name != "projection"
    )
    assert all(parameter.default is inspect.Parameter.empty for parameter in archive.parameters.values())

    source = Path(api.__file__)
    tree = ast.parse(source.read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and any(isinstance(item, ast.Constant) and item.value == "__main__" for item in ast.walk(node.test))
        for node in ast.walk(tree)
    )
    assert not hasattr(api, "main")


@pytest.mark.parametrize("projected", (False, True), ids=("state-built", "projected"))
def test_serializer_accepts_both_legal_state_projection_combinations_and_is_deterministic(projected: bool) -> None:
    api = _api()
    left = _serialize(api, projected=projected)
    right = _serialize(api, projected=projected)
    assert left == right and left is not right
    assert set(left) == PAYLOAD_FIELDS
    assert left["projection"] is (None if not projected else left["projection"])
    assert left["envelope"]["state"] == ("PROJECTED" if projected else "STATE_BUILT")
    assert left["envelope"]["identity"]["as_of_date"] == "2020-01-01"
    assert left["freeze_package"]["fundamentals"][0]["reasonable_range"] == ["specialist", "team lead"]
    if projected:
        unsupported = left["projection"]["unsupported_domains"][0]
        assert unsupported == {
            "decision_action": "ABSTAIN",
            "domain": "health",
            "status": "NOT_IMPLEMENTED",
        }
    assert json.loads(_canonical(left)) == left


@pytest.mark.parametrize(
    "slot",
    ("envelope", "freeze_package", "adjudication_bundle", "state_result", "projection"),
)
def test_serializer_rejects_every_inexact_top_level_type(slot: str) -> None:
    api = _api()
    values = list(_objects(projected=True))
    values[("envelope", "freeze_package", "adjudication_bundle", "state_result", "projection").index(slot)] = object()
    _assert_archive_input(api, lambda: _serialize(api, values=tuple(values)))


@pytest.mark.parametrize(
    "case",
    ("wrong_state_without_projection", "projection_missing", "projection_with_state_built", "projection_source_chain"),
)
def test_serializer_rejects_invalid_state_and_projection_combinations(case: str) -> None:
    api = _api()
    values = list(_objects(projected=case != "wrong_state_without_projection"))
    if case == "wrong_state_without_projection":
        values[0] = _envelope(ConsultationState.PROJECTED)
    elif case == "projection_missing":
        values[4] = None
    elif case == "projection_with_state_built":
        values[0] = values[3].envelope
    else:
        values[4] = replace(values[4], envelope=_envelope(ConsultationState.PROJECTED, blind_input_sha256="2" * 64))
    _assert_archive_input(api, lambda: _serialize(api, values=tuple(values)))


@pytest.mark.parametrize("case", ("identity", "blind_hash", "freeze_hash", "state_identity"))
def test_serializer_rejects_identity_and_hash_chain_mismatches(case: str) -> None:
    api = _api()
    values = list(_objects())
    if case == "identity":
        values[0] = _envelope(
            ConsultationState.STATE_BUILT,
            identity=_identity(session_id="S-20260727T120000Z-deadbeef"),
        )
    elif case == "blind_hash":
        values[0] = _envelope(ConsultationState.STATE_BUILT, blind_input_sha256="2" * 64)
    elif case == "freeze_hash":
        values[2] = replace(values[2], freeze_package_sha256="0" * 64)
    else:
        values[3] = replace(
            values[3],
            envelope=_envelope(
                ConsultationState.STATE_BUILT,
                identity=_identity(session_id="S-20260727T120000Z-deadbeef"),
            ),
        )
    _assert_archive_input(api, lambda: _serialize(api, values=tuple(values)))


@pytest.mark.parametrize(
    "case",
    (
        "freeze_identity",
        "freeze_blind_hash",
        "adjudication_identity",
        "adjudication_blind_hash",
        "adjudication_package",
    ),
)
def test_serializer_rejects_each_independent_cross_object_chain_mismatch(case: str) -> None:
    api = _api()
    values = list(_objects())
    if case == "freeze_identity":
        values[1] = replace(
            values[1],
            identity=_identity(session_id="S-20260727T120000Z-deadbeef"),
        )
    elif case == "freeze_blind_hash":
        values[1] = replace(values[1], blind_input_sha256="2" * 64)
    elif case == "adjudication_identity":
        values[2] = replace(
            values[2],
            envelope=_envelope(
                ConsultationState.ADJUDICATED,
                identity=_identity(session_id="S-20260727T120000Z-deadbeef"),
            ),
        )
    elif case == "adjudication_blind_hash":
        values[2] = replace(
            values[2],
            envelope=_envelope(ConsultationState.ADJUDICATED, blind_input_sha256="2" * 64),
        )
    else:
        different_fundamental = replace(values[1].fundamentals[0], center="senior professional")
        different_package = replace(values[1], fundamentals=(different_fundamental,))
        values[2] = replace(values[2], package=different_package)
    _assert_archive_input(api, lambda: _serialize(api, values=tuple(values)))


@pytest.mark.parametrize("operation_name", ("serialize", "archive"))
def test_rejects_non_adjudicated_bundle_envelope_before_backend_delegation(
    operation_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _api()
    values = list(_objects())
    values[2] = replace(
        values[2],
        envelope=_envelope(ConsultationState.STATE_BUILT),
    )
    calls: list[tuple[Any, ...]] = []
    monkeypatch.setattr(archive_backend, "archive_verified_artifact", lambda *args: calls.append(args))
    if operation_name == "serialize":
        operation = lambda: _serialize(api, values=tuple(values))
    else:
        operation = lambda: _archive(api, tmp_path, values=tuple(values))
    _assert_archive_input(api, operation)
    assert calls == []


def test_archive_api_rejects_invalid_cross_object_binding_before_delegation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api()
    values = list(_objects())
    values[0] = _envelope(ConsultationState.PROJECTED)
    calls: list[tuple[Any, ...]] = []
    monkeypatch.setattr(archive_backend, "archive_verified_artifact", lambda *args: calls.append(args))
    _assert_archive_input(api, lambda: _archive(api, tmp_path, values=tuple(values)))
    assert calls == []


@pytest.mark.parametrize(
    "invalid_value",
    (object(), {1: "non-string-key"}),
    ids=("unknown-type", "non-string-dict-key"),
)
def test_recursive_projection_rejects_unknown_type_and_non_string_dict_key(invalid_value: object) -> None:
    api = _api()
    values = list(_objects())
    state_result = values[3]
    object.__setattr__(state_result.verified_state, "current_center", invalid_value)
    _assert_archive_input(api, lambda: _serialize(api, values=tuple(values)))


@pytest.mark.parametrize("non_finite", (float("nan"), float("inf"), float("-inf")), ids=("nan", "positive-infinity", "negative-infinity"))
def test_recursive_projection_rejects_non_finite_float(non_finite: float) -> None:
    api = _api()
    values = list(_objects())
    state_result = values[3]
    object.__setattr__(state_result.verified_state, "current_center", non_finite)
    _assert_archive_input(api, lambda: _serialize(api, values=tuple(values)))


def test_archive_builds_exact_eight_field_artifact_with_equal_digests_and_exact_sidecar_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api()
    observed: dict[str, Any] = {}
    sentinel = archive_backend.ArchiveResult("CREATED", tmp_path / "sentinel.json", "asof-unit6-001", "0" * 64, "unit5 report\n")

    def fake(source: Path, archive_root: Path):
        observed["source"] = Path(source)
        observed["archive_root"] = Path(archive_root)
        observed["artifact_bytes"] = Path(source).read_bytes()
        observed["sidecar_bytes"] = Path(str(source) + ".source").read_bytes()
        return sentinel

    monkeypatch.setattr(archive_backend, "archive_verified_artifact", fake)
    result = _archive(api, tmp_path)
    assert result is sentinel
    assert observed["archive_root"] == tmp_path / "archive"
    artifact = json.loads(observed["artifact_bytes"].decode("utf-8"))
    payload_bytes = _canonical(artifact["payload"])
    digest = hashlib.sha256(payload_bytes).hexdigest()
    assert set(artifact) == ARTIFACT_FIELDS
    assert artifact["artifact_id"] == "asof-unit6-001"
    assert artifact["verified_at"] == VERIFIED_AT
    assert artifact["verifier"] == "unit6-test"
    assert artifact["verification_basis"] == ["unit5-contract", "unit6-integration"]
    assert artifact["source_digest"] == artifact["payload_digest"] == digest
    assert observed["sidecar_bytes"] == payload_bytes
    assert observed["artifact_bytes"] == _canonical(artifact)


def test_archive_dynamically_delegates_exactly_once_with_correct_parameters_and_return_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api()
    calls: list[tuple[Path, Path]] = []
    sentinel = archive_backend.ArchiveResult("UNCHANGED", tmp_path / "target.json", "asof-unit6-001", "f" * 64, "unit5 report\n")

    def fake(source: Path, archive_root: Path):
        calls.append((Path(source), Path(archive_root)))
        assert Path(source).is_file()
        assert Path(str(source) + ".source").is_file()
        return sentinel

    monkeypatch.setattr(archive_backend, "archive_verified_artifact", fake)
    assert _archive(api, tmp_path) is sentinel
    assert len(calls) == 1
    assert calls[0][1] == tmp_path / "archive"


@pytest.mark.parametrize(
    "error_type",
    (archive_backend.ArchiveInputError, archive_backend.ArchiveConflictError, archive_backend.ArchiveIOError),
    ids=("input", "conflict", "io"),
)
def test_archive_preserves_all_public_backend_exception_instances(error_type: type[Exception], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    api = _api()
    sentinel = error_type("sentinel")
    calls = 0

    def fail(_source: Path, _archive_root: Path):
        nonlocal calls
        calls += 1
        raise sentinel

    monkeypatch.setattr(archive_backend, "archive_verified_artifact", fail)
    with pytest.raises(error_type) as caught:
        _archive(api, tmp_path)
    assert caught.value is sentinel
    assert calls == 1


def test_archive_preserves_backend_exception_when_cleanup_raises_runtime_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _api()
    sentinel = RuntimeError("backend sentinel")
    calls = 0

    class CleanupFails:
        def __init__(self, *, prefix: str):
            self.name = str(tmp_path / prefix)
            Path(self.name).mkdir()

        def cleanup(self) -> None:
            raise RuntimeError("cleanup sentinel")

    def fail(_source: Path, _archive_root: Path):
        nonlocal calls
        calls += 1
        raise sentinel

    monkeypatch.setattr(api._tempfile, "TemporaryDirectory", CleanupFails)
    monkeypatch.setattr(archive_backend, "archive_verified_artifact", fail)
    with pytest.raises(RuntimeError) as caught:
        _archive(api, tmp_path)
    assert caught.value is sentinel
    assert calls == 1


def test_real_archive_covers_created_unchanged_and_unit5_report(tmp_path: Path) -> None:
    api = _api()
    first = _archive(api, tmp_path)
    second = _archive(api, tmp_path)
    assert first.status == "CREATED"
    assert second.status == "UNCHANGED"
    assert first.target == second.target
    assert first.target.is_file()
    assert first.report and second.report
    report_path = tmp_path / "unit5-report.txt"
    report_path.write_text(first.report, encoding="utf-8", newline="\n")
    assert report_path.is_file()


def test_real_archive_detects_same_artifact_id_conflict(tmp_path: Path) -> None:
    api = _api()
    _archive(api, tmp_path, artifact_id="asof-unit6-conflict")
    values = list(_objects())
    values[3] = replace(
        values[3],
        verified_state=replace(values[3].verified_state, current_center="executive"),
    )
    with pytest.raises(archive_backend.ArchiveConflictError):
        _archive(api, tmp_path, artifact_id="asof-unit6-conflict", values=tuple(values))


def test_collection_contract_has_no_top_level_target_import_and_keeps_helpers_local() -> None:
    _api()
    tree = ast.parse(TARGET.read_text(encoding="utf-8"))
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert MODULE_NAME not in imports
    assert not any(name.startswith("tests.") for name in imports)
    tests = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]
    assert len(tests) >= 10
