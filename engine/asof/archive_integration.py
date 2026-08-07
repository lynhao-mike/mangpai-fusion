"""将完整 as-of 事业状态链适配为 Unit 5 verified artifact。"""

from __future__ import annotations

import dataclasses as _dataclasses
import datetime as _datetime
import enum as _enum
import hashlib as _hashlib
import json as _json
import math as _math
import os as _os
import tempfile as _tempfile
from pathlib import Path as _Path

import engine.archive as _archive
from engine.asof.career_state_builder import (
    CareerAdjudicationBundle as _CareerAdjudicationBundle,
    CareerStateBuildResult as _CareerStateBuildResult,
)
from engine.asof.consultation_freeze import (
    CareerFreezePackage as _CareerFreezePackage,
    compute_freeze_package_sha256 as _compute_freeze_package_sha256,
)
from engine.asof.future_projection import FutureProjectionFromState as _FutureProjectionFromState
from engine.asof.session_contract import (
    ConsultationState as _ConsultationState,
    SessionEnvelope as _SessionEnvelope,
)


_PAYLOAD_SCHEMA_VERSION = "asof-archive-payload/v1"
_ARTIFACT_SCHEMA_VERSION = "asof-verified-artifact/v1"


def _invalid(message: str, cause: BaseException | None = None) -> _archive.ArchiveInputError:
    error = _archive.ArchiveInputError(message)
    if cause is not None:
        error.__cause__ = cause
    return error


def _same_binding(left: _SessionEnvelope, right: _SessionEnvelope) -> bool:
    return left.identity == right.identity and left.blind_input_sha256 == right.blind_input_sha256


def _validate_chain(
    envelope: _SessionEnvelope,
    freeze_package: _CareerFreezePackage,
    adjudication_bundle: _CareerAdjudicationBundle,
    state_result: _CareerStateBuildResult,
    projection: _FutureProjectionFromState | None,
) -> None:
    try:
        expected = (
            (envelope, _SessionEnvelope, "envelope"),
            (freeze_package, _CareerFreezePackage, "freeze_package"),
            (adjudication_bundle, _CareerAdjudicationBundle, "adjudication_bundle"),
            (state_result, _CareerStateBuildResult, "state_result"),
        )
        for value, model, name in expected:
            if type(value) is not model:
                raise _invalid(f"{name} must have its exact domain type")
        if projection is not None and type(projection) is not _FutureProjectionFromState:
            raise _invalid("projection must be None or exact FutureProjectionFromState")

        if envelope.state is _ConsultationState.STATE_BUILT:
            if projection is not None or envelope != state_result.envelope:
                raise _invalid("STATE_BUILT requires no projection and the state-result envelope")
        elif envelope.state is _ConsultationState.PROJECTED:
            if projection is None or projection.envelope != envelope:
                raise _invalid("PROJECTED requires a projection bound to the final envelope")
            if state_result.envelope.state is not _ConsultationState.STATE_BUILT:
                raise _invalid("PROJECTED must originate from a STATE_BUILT result")
            if not _same_binding(state_result.envelope, envelope):
                raise _invalid("projected and intermediate envelopes have different bindings")
        else:
            raise _invalid("only STATE_BUILT and PROJECTED may be archived")

        if freeze_package.identity != envelope.identity:
            raise _invalid("freeze package identity differs from the envelope")
        if freeze_package.blind_input_sha256 != envelope.blind_input_sha256:
            raise _invalid("freeze package blind digest differs from the envelope")
        if adjudication_bundle.envelope.state is not _ConsultationState.ADJUDICATED:
            raise _invalid("adjudication bundle requires an ADJUDICATED envelope")
        if not _same_binding(adjudication_bundle.envelope, envelope):
            raise _invalid("adjudication envelope binding differs")
        if adjudication_bundle.package != freeze_package:
            raise _invalid("adjudication package differs from the freeze package")
        if adjudication_bundle.freeze_package_sha256 != _compute_freeze_package_sha256(freeze_package):
            raise _invalid("adjudication freeze package digest differs")
        if not _same_binding(state_result.envelope, envelope):
            raise _invalid("state-result envelope binding differs")
    except _archive.ArchiveInputError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise _invalid("invalid as-of domain chain", exc)


def _project(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is float:
        if not _math.isfinite(value):
            raise _invalid("non-finite floats are not canonical JSON values")
        return value
    if isinstance(value, _enum.Enum):
        return _project(value.value)
    if isinstance(value, _datetime.datetime):
        return value.isoformat()
    if isinstance(value, _datetime.date):
        return value.isoformat()
    if _dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {field.name: _project(getattr(value, field.name)) for field in _dataclasses.fields(value)}
    if type(value) in (tuple, list):
        return [_project(item) for item in value]
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise _invalid("canonical JSON objects require string keys")
        return {key: _project(item) for key, item in value.items()}
    raise _invalid(f"unsupported canonical value type: {type(value).__name__}")


def _canonical_bytes(value: object) -> bytes:
    try:
        return _json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise _invalid("value cannot be encoded as canonical UTF-8 JSON", exc)


def serialize_asof_archive_payload(
    envelope: _SessionEnvelope,
    freeze_package: _CareerFreezePackage,
    adjudication_bundle: _CareerAdjudicationBundle,
    state_result: _CareerStateBuildResult,
    projection: _FutureProjectionFromState | None = None,
) -> dict[str, object]:
    """验证完整链并生成纯 JSON as-of archive payload。"""

    _validate_chain(envelope, freeze_package, adjudication_bundle, state_result, projection)
    try:
        payload = {
            "schema_version": _PAYLOAD_SCHEMA_VERSION,
            "envelope": _project(envelope),
            "freeze_package": _project(freeze_package),
            "adjudication_bundle": _project(adjudication_bundle),
            "state_result": _project(state_result),
            "projection": _project(projection),
        }
        _canonical_bytes(payload)
        return payload
    except _archive.ArchiveInputError:
        raise
    except (AttributeError, TypeError, ValueError, UnicodeError) as exc:
        raise _invalid("as-of payload cannot be projected canonically", exc)


def archive_asof_state(
    envelope: _SessionEnvelope,
    freeze_package: _CareerFreezePackage,
    adjudication_bundle: _CareerAdjudicationBundle,
    state_result: _CareerStateBuildResult,
    projection: _FutureProjectionFromState | None,
    *,
    archive_root: _os.PathLike[str] | str,
    artifact_id: str,
    verified_at: str,
    verifier: str,
    verification_basis: tuple[str, ...],
) -> _archive.ArchiveResult:
    """构造临时 verified artifact，并将归档语义完整委托给 Unit 5。"""

    _validate_chain(envelope, freeze_package, adjudication_bundle, state_result, projection)
    payload = serialize_asof_archive_payload(
        envelope, freeze_package, adjudication_bundle, state_result, projection
    )
    payload_bytes = _canonical_bytes(payload)
    digest = _hashlib.sha256(payload_bytes).hexdigest()
    artifact = {
        "schema_version": _ARTIFACT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "source_digest": digest,
        "payload_digest": digest,
        "verified_at": verified_at,
        "verifier": verifier,
        "verification_basis": list(verification_basis),
        "payload": payload,
    }
    artifact_bytes = _canonical_bytes(artifact)

    try:
        temporary = _tempfile.TemporaryDirectory(prefix="asof-archive-")
        source = _Path(temporary.name) / "artifact.json"
        source.write_bytes(artifact_bytes)
        _Path(str(source) + ".source").write_bytes(payload_bytes)
    except OSError as exc:
        try:
            temporary.cleanup()
        except (NameError, OSError):
            pass
        raise _archive.ArchiveIOError("cannot prepare temporary as-of archive input") from exc

    try:
        result = _archive.archive_verified_artifact(source, archive_root)
    except BaseException as backend_error:
        try:
            temporary.cleanup()
        except BaseException:
            pass
        raise backend_error
    try:
        temporary.cleanup()
    except OSError as exc:
        raise _archive.ArchiveIOError("cannot clean temporary as-of archive input") from exc
    return result
