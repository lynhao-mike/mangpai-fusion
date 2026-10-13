from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from engine.f09.canonical_json import JcsValue, bounded_jcs_sha256, canonicalize_bounded_jcs
from engine.f09.errors import F09WriteError


_SCHEMA_VERSION = "f09.operator-phase-observation-log.v1"
_LOCATOR_SCHEMA_VERSION = "f09.operator-phase-observation-locator.v1"
_ERROR_CODE = "APPLICATION.OBSERVATION_PERSISTENCE_FAILED"
_ERROR_PATH = "/artifact_root/operator-diagnostics"
_TERMINAL_STATUSES = ("FAILED", "REJECTED")


def _fail(diagnostic: str) -> F09WriteError:
    return F09WriteError(_ERROR_CODE, _ERROR_PATH, diagnostic)


def _locator_material(request: object) -> dict[str, JcsValue]:
    return {
        "schema_version": _LOCATOR_SCHEMA_VERSION,
        "case_id": request.case_id,
        "request_id": request.request_id,
        "attempt_id": request.attempt_id,
        "mode": request.mode,
    }


def _observation_material(observation: object) -> dict[str, JcsValue]:
    return {
        "event": observation.event,
        "case_id": observation.case_id,
        "mode": observation.mode,
        "phase": observation.phase,
        "status": observation.status,
        "issue_codes": observation.issue_codes,
        "artifact_set_state": observation.artifact_set_state,
    }


def _log_material(
    request: object,
    observations: tuple[object, ...],
    stopped_at: str | None,
) -> dict[str, JcsValue]:
    terminal = tuple(item for item in observations if item.status in _TERMINAL_STATUSES)
    if stopped_at is None:
        if terminal:
            raise _fail("completed run contains a terminal observation")
    elif (
        len(terminal) != 1
        or observations[-1] is not terminal[0]
        or terminal[0].phase != stopped_at
        or not terminal[0].issue_codes
        or any(type(code) is not str or not code for code in terminal[0].issue_codes)
    ):
        raise _fail("terminal observation is not closed")
    if any(
        item.case_id != request.case_id
        or item.mode != request.mode
        or item.event != "F09_SLICE_PHASE"
        for item in observations
    ):
        raise _fail("observation identity mismatch")
    return {
        "schema_version": _SCHEMA_VERSION,
        "case_id": request.case_id,
        "request_id": request.request_id,
        "attempt_id": request.attempt_id,
        "mode": request.mode,
        "completed": stopped_at is None,
        "stopped_at": stopped_at,
        "observations": tuple(_observation_material(item) for item in observations),
    }


def persist_phase_observation_log(
    request: object,
    observations: tuple[object, ...],
    stopped_at: str | None,
) -> Path:
    root = request.artifact_root
    if not isinstance(root, Path):
        raise _fail("artifact root must be a Path")

    temp: Path | None = None
    committed = False
    try:
        payload = canonicalize_bounded_jcs(_log_material(request, observations, stopped_at))
        locator = bounded_jcs_sha256(_locator_material(request)).value
        directory = root / "operator-diagnostics"
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"{locator}.json"
        temp = directory / f".{locator}.{uuid4().hex}.tmp"
        with temp.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
        committed = True
        if target.read_bytes() != payload:
            raise OSError("diagnostic readback mismatch")
        return target
    except F09WriteError:
        raise
    except Exception as error:
        raise _fail(f"diagnostic persistence failed: {type(error).__name__}") from error
    finally:
        if not committed and temp is not None:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
