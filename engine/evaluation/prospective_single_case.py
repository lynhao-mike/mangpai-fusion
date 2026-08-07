from __future__ import annotations

import calendar
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Mapping, Sequence, Set
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from engine.application.governance_shadow_types import GovernanceShadowResult
from engine.evaluation.governance_shadow_adapter import (
    GovernanceShadowTaskProjection,
    adapt_governance_shadow_to_blind_outputs,
)
from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    canonical_artifact_sha256,
    publish_new_json,
    single_case_artifact_path,
    validate_parent_ref,
    validate_revision_metadata,
)
from engine.evaluation.freeze import canonical_json, freeze_outputs, verify_frozen_run
from engine.evaluation.models import BlindSchoolOutput, BlindTask, FrozenBlindRun
from engine.governance.school_registry import normalize_school_input


SIX_SCHOOLS: tuple[str, ...] = (
    "ziping",
    "ditiansui",
    "duan",
    "ren",
    "gao",
    "yang",
)

_FUTURE_SCHEMA = "prospective-future-question/v1"
_INTAKE_SCHEMA = "prospective-single-case-intake/v1"
_FORBIDDEN_MARKERS = (
    re.compile(r"(?<![a-z0-9])feedback(?![a-z0-9])"),
    re.compile(r"(?<![a-z0-9])labels?(?![a-z0-9])"),
    re.compile(r"(?<![a-z0-9])reports?(?![a-z0-9])"),
    re.compile(r"(?<![a-z0-9])known[ _-]+facts?(?![a-z0-9])"),
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_REVISION_FIELDS = {"supersedes", "supersedes_sha256", "reason", "approved_by"}
_MIGRATION_FIELDS = {"revision_scope", "superseded_chain_terminal_kind"}
_FORBIDDEN_MIGRATION_KINDS = (
    "frozen-run", "witness", "verification", "feedback", "retrospective",
    "observation", "report", "label", "reveal",
)
_FUTURE_REQUIRED_FIELDS = {
    "schema_version",
    "case_id",
    "subject_id_hash",
    "created_at",
    "artifact_path",
    "future_task_id",
    "question_text_redacted",
    "outcome_type",
    "positive_definition",
    "negative_definition",
    "verification_source_requirements",
    "observation_window",
    "parents",
    "artifact_sha256",
}
_SINGLE_BUNDLE_SCHEMA = "prospective-single-case-blind-bundle/v1"
_SINGLE_INTAKE_REQUIRED_FIELDS = {
    "schema_version",
    "case_id",
    "subject_id_hash",
    "created_at",
    "artifact_path",
    "operator",
    "schools",
    "task_catalog_sha256",
    "records",
    "future_question",
    "parents",
    "artifact_sha256",
}
_INTAKE_RECORD_FIELDS = {"case_id", "input_file", "input_sha256", "subject_id_hash", "task_ids"}
_TASK_BUNDLE_FIELDS = (
    "task_id", "domain", "claim_type", "scoring_method", "quantifiable", "high_risk",
    "allowed_time_horizons", "required_input_fields", "label_schema", "evaluation_note",
)


class ContaminationError(ValueError):
    """A fail-closed STOP caused by leakage or immutable-parent drift."""


def _stop(message: str) -> ContaminationError:
    return ContaminationError(f"STOP: {message}")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _is_linklike(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(is_junction is not None and is_junction())


def _reject_symlink(path: Path, description: str) -> None:
    absolute = Path(path).absolute()
    for candidate in (absolute, *absolute.parents):
        if _is_linklike(candidate):
            raise _stop(f"{description} must not be or traverse a symlink/junction: {path}")


def _parse_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp") from exc
    if parsed.tzinfo != timezone.utc:
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp")
    return parsed


def _add_calendar_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _contains_forbidden_marker(
    value: object, *, allowed_structural_keys: frozenset[str] = frozenset(),
) -> bool:
    if isinstance(value, Mapping):
        return any(
            (
                key not in allowed_structural_keys
                and _contains_forbidden_marker(key)
            )
            or _contains_forbidden_marker(
                item, allowed_structural_keys=allowed_structural_keys,
            )
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(
            _contains_forbidden_marker(
                item, allowed_structural_keys=allowed_structural_keys,
            )
            for item in value
        )
    if isinstance(value, str):
        normalized = value.lower()
        return any(marker.search(normalized) is not None for marker in _FORBIDDEN_MARKERS)
    return False


def _contains_forbidden_value(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_forbidden_value(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_value(item) for item in value)
    if isinstance(value, str):
        normalized = value.lower()
        return any(marker.search(normalized) is not None for marker in _FORBIDDEN_MARKERS)
    return False


def _non_empty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _artifact_version(path: object, kind: str) -> int:
    if not isinstance(path, str):
        raise ValueError("artifact_path must be a non-empty string")
    match = re.search(rf"--{re.escape(kind)}--v(\d{{3}})\.json$", path)
    if match is None:
        raise ValueError(f"artifact_path is not canonical for {kind}")
    return int(match.group(1))


def _revision_payload(value: Mapping[str, Any] | None, version: int) -> dict[str, Any]:
    revision = dict(value or {})
    validate_revision_metadata(revision, version)
    return revision


def _one_question(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) == 1:
        question = value[0]
        if isinstance(question, Mapping):
            return question
    raise ValueError("single-case intake requires exactly one future question")


def validate_future_question_registration(
    document: Mapping[str, Any],
    *,
    freeze_at: str | None = None,
) -> dict[str, Any]:
    """Validate one sealed binary future question without deriving it from chart data."""
    if not isinstance(document, Mapping):
        raise ValueError("future question registration schema is invalid")
    result = dict(document)
    version = _artifact_version(result.get("artifact_path"), "future-question-registration")
    expected_fields = _FUTURE_REQUIRED_FIELDS | (_REVISION_FIELDS if version > 1 else set())
    if set(result) != expected_fields:
        raise ValueError("future question registration schema is invalid")
    validate_revision_metadata(result, version)
    if result.get("schema_version") != _FUTURE_SCHEMA:
        raise ValueError(f"future question must use {_FUTURE_SCHEMA}")
    if _contains_forbidden_marker(result):
        raise ValueError("future question contains forbidden feedback/labels/report/known facts marker")
    _non_empty_string(result.get("case_id"), "case_id")
    subject_hash = result.get("subject_id_hash")
    if not isinstance(subject_hash, str) or _SHA256_PATTERN.fullmatch(subject_hash) is None:
        raise ValueError("subject_id_hash must be a lowercase SHA-256")
    created = _parse_utc(result.get("created_at"), "created_at")
    _non_empty_string(result.get("artifact_path"), "artifact_path")
    _non_empty_string(result.get("future_task_id"), "future_task_id")
    _non_empty_string(result.get("question_text_redacted"), "question_text_redacted")
    if result.get("outcome_type") != "binary":
        raise ValueError("future question outcome_type must be binary")
    _non_empty_string(result.get("positive_definition"), "positive_definition")
    _non_empty_string(result.get("negative_definition"), "negative_definition")
    sources = result.get("verification_source_requirements")
    if (
        not isinstance(sources, list)
        or not sources
        or any(not isinstance(item, str) or not item.strip() for item in sources)
    ):
        raise ValueError("future question source requirements must be non-empty strings")
    window = result.get("observation_window")
    if not isinstance(window, dict) or set(window) != {"start_at", "end_at"}:
        raise ValueError("future question observation_window schema is invalid")
    start = _parse_utc(window.get("start_at"), "observation_window.start_at")
    end = _parse_utc(window.get("end_at"), "observation_window.end_at")
    if start < created:
        raise ValueError("observation_window.start_at must not predate created_at")
    if end <= start:
        raise ValueError("observation_window.end_at must be later than start_at")
    anchor = start
    if freeze_at is not None:
        freeze = _parse_utc(freeze_at, "freeze_at")
        if start != freeze:
            raise ValueError("observation_window.start_at must equal freeze_at")
        anchor = freeze
    if end > _add_calendar_months(anchor, 3):
        raise ValueError("observation_window.end_at exceeds three calendar months")
    if result.get("parents") != []:
        raise ValueError("future question registration must have no parents")
    digest = result.get("artifact_sha256")
    if digest != canonical_artifact_sha256(result):
        raise ValueError("future question artifact_sha256 mismatch")
    return result


def _build_future_question_registration(
    row: Mapping[str, Any],
    draft: Mapping[str, Any],
    *,
    created_at: str,
    artifact_path: Path,
    version: int,
    revision: Mapping[str, Any] | None,
) -> dict[str, Any]:
    allowed = {
        "future_task_id",
        "question_text_redacted",
        "outcome_type",
        "positive_definition",
        "negative_definition",
        "verification_source_requirements",
        "observation_window",
    }
    if set(draft) != allowed:
        raise ValueError("future question draft schema is invalid")
    if _contains_forbidden_marker(draft):
        raise ValueError("future question contains forbidden feedback/labels/report/known facts marker")
    if draft.get("future_task_id") not in row["task_ids"]:
        raise ValueError("future_task_id must match an assigned task")
    payload: dict[str, Any] = {
        "schema_version": _FUTURE_SCHEMA,
        "case_id": row["case_id"],
        "subject_id_hash": row["subject_id_hash"],
        "created_at": created_at,
        "artifact_path": artifact_path.as_posix(),
        **dict(draft),
        "parents": [],
        **_revision_payload(revision, version),
    }
    document = {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}
    return validate_future_question_registration(document)


def build_single_case_intake(
    input_file: Path,
    tasks: dict[str, Any],
    schools: Sequence[str],
    operator: str,
    tasks_by_case: dict[str, list[str]],
    future_question: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    *,
    created_at: str,
    question_created_at: str | None = None,
    existing_subject_hashes: Set[str] = frozenset(),
    case_root: Path,
    version: int = 1,
    question_revision: Mapping[str, Any] | None = None,
    intake_revision: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build one intake and one externally supplied question for immutable publication."""
    intake_created = _parse_utc(created_at, "created_at")
    question_created_at = question_created_at or created_at
    question_created = _parse_utc(question_created_at, "question_created_at")
    if question_created > intake_created:
        raise ValueError("question_created_at must not be later than intake created_at")
    if tuple(schools) != SIX_SCHOOLS:
        raise ValueError("single-case intake requires exactly six schools in canonical order")
    draft = _one_question(future_question)
    if _contains_forbidden_marker(draft):
        raise ValueError("future question contains forbidden feedback/labels/report/known facts marker")

    # Kept local to avoid making the general-purpose dataset CLI an import-time engine dependency.
    from tools.school_capability_dataset import register_prospective_intake

    batch = register_prospective_intake(
        [Path(input_file)],
        tasks,
        list(schools),
        operator,
        tasks_by_case=tasks_by_case,
    )
    if len(batch.get("records", [])) != 1 or tuple(batch.get("schools", [])) != SIX_SCHOOLS:
        raise ValueError("single-case intake requires one record and exactly six schools")
    row = batch["records"][0]
    if row["subject_id_hash"] in existing_subject_hashes:
        raise ValueError("duplicate subject_id_hash across prospective cases")

    question_path = single_case_artifact_path(
        Path(case_root), row["case_id"], "future-question-registration", version
    )
    intake_path = single_case_artifact_path(Path(case_root), row["case_id"], "intake", version)
    question = _build_future_question_registration(
        row,
        draft,
        created_at=question_created_at,
        artifact_path=question_path,
        version=version,
        revision=question_revision,
    )
    question_ref = {
        "artifact_path": question_path.as_posix(),
        "artifact_sha256": question["artifact_sha256"],
    }
    intake_payload: dict[str, Any] = {
        "schema_version": _INTAKE_SCHEMA,
        "case_id": row["case_id"],
        "subject_id_hash": row["subject_id_hash"],
        "created_at": created_at,
        "artifact_path": intake_path.as_posix(),
        "operator": operator,
        "schools": list(SIX_SCHOOLS),
        "task_catalog_sha256": batch["task_catalog_sha256"],
        "records": [row],
        "future_question": question_ref,
        "parents": [question_ref],
        **_revision_payload(intake_revision, version),
    }
    intake = {
        **intake_payload,
        "artifact_sha256": canonical_artifact_sha256(intake_payload),
    }
    return intake, question


def validate_single_case_intake(intake: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return the only immutable intake record."""
    if not isinstance(intake, Mapping):
        raise _stop("single-case intake schema is invalid")
    try:
        version = _artifact_version(intake.get("artifact_path"), "intake")
        validate_revision_metadata(intake, version)
    except ValueError as error:
        raise _stop(f"single-case intake revision is invalid: {error}") from error
    expected_fields = _SINGLE_INTAKE_REQUIRED_FIELDS | (_REVISION_FIELDS if version > 1 else set())
    if set(intake) != expected_fields:
        raise _stop("single-case intake schema is invalid")
    if intake.get("schema_version") != _INTAKE_SCHEMA:
        raise _stop(f"single-case intake must use {_INTAKE_SCHEMA}")
    if intake.get("artifact_sha256") != canonical_artifact_sha256(intake):
        raise _stop("single-case intake hash changed")
    records = intake.get("records")
    if not isinstance(records, list) or len(records) != 1:
        raise _stop("single-case intake requires exactly one record")
    row = records[0]
    if not isinstance(row, dict) or set(row) != _INTAKE_RECORD_FIELDS:
        raise _stop("single-case intake record is invalid")
    case_id = intake.get("case_id")
    subject_hash = intake.get("subject_id_hash")
    if row.get("case_id") != case_id or row.get("subject_id_hash") != subject_hash:
        raise _stop("single-case intake record parent mismatch")
    if tuple(intake.get("schools", ())) != SIX_SCHOOLS:
        raise _stop("single-case intake requires exactly six schools in canonical order")
    if (
        not isinstance(row.get("input_file"), str)
        or not isinstance(row.get("input_sha256"), str)
        or _SHA256_PATTERN.fullmatch(row["input_sha256"]) is None
        or not isinstance(subject_hash, str)
        or _SHA256_PATTERN.fullmatch(subject_hash) is None
        or not isinstance(row.get("task_ids"), list)
        or not row["task_ids"]
        or any(not isinstance(item, str) or not item for item in row["task_ids"])
        or len(row["task_ids"]) != len(set(row["task_ids"]))
    ):
        raise _stop("single-case intake record values are invalid")
    question_ref = intake.get("future_question")
    if (
        not isinstance(question_ref, dict)
        or set(question_ref) != {"artifact_path", "artifact_sha256"}
        or intake.get("parents") != [question_ref]
    ):
        raise _stop("single-case future-question parent mismatch")
    return dict(row)


def _validate_future_question_parent(
    future_question: Mapping[str, Any], intake: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        question = validate_future_question_registration(future_question)
    except ValueError as error:
        raise _stop(f"future-question is invalid: {error}") from error
    expected_ref = {
        "artifact_path": question["artifact_path"],
        "artifact_sha256": question["artifact_sha256"],
    }
    if (
        question.get("case_id") != intake.get("case_id")
        or question.get("subject_id_hash") != intake.get("subject_id_hash")
        or intake.get("future_question") != expected_ref
        or intake.get("parents") != [expected_ref]
    ):
        raise _stop("future-question parent mismatch")
    return question


def _validated_disk_parent(document: Mapping[str, Any], description: str) -> dict[str, Any]:
    try:
        actual = validate_parent_ref(ArtifactRef(
            artifact_path=str(document.get("artifact_path", "")),
            artifact_sha256=str(document.get("artifact_sha256", "")),
        ))
    except (OSError, ValueError, TypeError) as error:
        raise _stop(f"{description} parent is invalid: {error}") from error
    if actual != document:
        raise _stop(f"{description} parent differs from supplied document")
    return actual


def _single_bundle_files(
    intake: Mapping[str, Any],
    future_question: Mapping[str, Any],
    tasks_path: Path,
    rule_snapshot_path: Path,
    *,
    allow_unpublished_parents: bool = False,
) -> tuple[dict[str, bytes], dict[str, Any], dict[str, Any]]:
    validate_single_case_intake(intake)
    _validate_future_question_parent(future_question, intake)
    if allow_unpublished_parents:
        actual_intake = dict(intake)
        actual_question = dict(future_question)
        for document, description in (
            (actual_intake, "single-case intake"),
            (actual_question, "future-question"),
        ):
            if canonical_artifact_sha256(document) != document.get("artifact_sha256"):
                raise _stop(f"unpublished {description} canonical hash mismatch")
    else:
        actual_intake = _validated_disk_parent(intake, "single-case intake")
        actual_question = _validated_disk_parent(future_question, "future-question")
    row = validate_single_case_intake(actual_intake)
    question = _validate_future_question_parent(actual_question, actual_intake)
    intake = actual_intake

    # Reuse the established canonical chart parser and task contract without changing
    # the existing multi-case bundle implementation.
    from tools.school_capability_dataset import parse_canonical_chart

    sources = (Path(tasks_path), Path(rule_snapshot_path))
    for source in sources:
        _reject_symlink(source, "single-case bundle source")
        if not source.is_file():
            raise _stop(f"single-case bundle source must be a regular file: {source}")
    try:
        task_document = json.loads(sources[0].read_text(encoding="utf-8"))
        rule_document = json.loads(sources[1].read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _stop("single-case bundle source must be valid UTF-8 JSON") from error
    if not isinstance(task_document, dict) or not isinstance(task_document.get("tasks"), list):
        raise _stop("task catalog is invalid")
    if _contains_forbidden_value(task_document):
        raise _stop("task catalog contains forbidden content")
    if _contains_forbidden_value(rule_document):
        raise _stop("rule snapshot contains forbidden content")
    try:
        clean_tasks = [
            {field: task[field] for field in _TASK_BUNDLE_FIELDS}
            for task in task_document["tasks"]
        ]
    except (KeyError, TypeError) as error:
        raise _stop("task catalog missing required scoring fields") from error
    bundled_tasks: dict[str, Any] = {
        "schema_version": task_document.get("schema_version"),
        "tasks": clean_tasks,
    }
    if isinstance(task_document.get("task_catalog_version"), str) and task_document["task_catalog_version"]:
        bundled_tasks["task_catalog_version"] = task_document["task_catalog_version"]
    task_bytes = _canonical_json_bytes(bundled_tasks)
    legacy_task_rows = [
        {key: value for key, value in task.items() if key != "evaluation_note"}
        for task in clean_tasks
    ]
    legacy_task_bytes = _canonical_json_bytes({
        "schema_version": task_document.get("schema_version"), "tasks": legacy_task_rows,
    })
    if intake.get("task_catalog_sha256") not in {_sha256(task_bytes), _sha256(legacy_task_bytes)}:
        raise _stop("intake task catalog hash changed")
    known_tasks = {
        task.get("task_id") for task in task_document["tasks"] if isinstance(task, dict)
    }
    if len(known_tasks) != len(task_document["tasks"]) or set(row["task_ids"]) - known_tasks:
        raise _stop("intake contains unknown or duplicate tasks")

    snapshot_id = rule_document.get("rule_snapshot_id") if isinstance(rule_document, dict) else None
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise _stop("rule snapshot requires rule_snapshot_id")
    rule_ref: dict[str, Any] = {
        "rule_snapshot_id": snapshot_id,
        "sha256": _sha256(sources[1].read_bytes()),
    }
    if isinstance(rule_document.get("schools"), list):
        rule_ref["schools"] = rule_document["schools"]
    if isinstance(rule_document.get("runners"), dict):
        rule_ref["runners"] = rule_document["runners"]

    input_path = Path(row["input_file"])
    _reject_symlink(input_path, "single-case input source")
    if not input_path.is_file() or input_path.name != "input.md":
        raise _stop("single-case input source must be a regular input.md")
    if input_path.parent.name != row["case_id"]:
        raise _stop("single-case input parent mismatch")
    input_bytes = input_path.read_bytes()
    if _sha256(input_bytes) != row["input_sha256"]:
        raise _stop("single-case input hash changed")
    try:
        input_text = input_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise _stop("single-case input must be UTF-8") from error
    if _contains_forbidden_marker(input_text):
        raise _stop("single-case input contains forbidden content")
    try:
        chart = parse_canonical_chart(input_text, row["case_id"])
    except ValueError as error:
        raise _stop(f"single-case canonical chart is invalid: {error}") from error
    chart_subject = _sha256(_canonical_json_bytes({
        key: chart[key] for key in ("four_pillars", "sex_marker")
    }))
    if chart_subject != row["subject_id_hash"]:
        raise _stop("single-case subject parent mismatch")

    safe_intake = {
        "schema_version": "school-capability-blind-intake/v1",
        "schools": sorted(SIX_SCHOOLS),
        "records": [{"case_id": row["case_id"], "task_ids": sorted(row["task_ids"])}],
    }
    files = {
        "intake.json": _canonical_json_bytes(safe_intake),
        "tasks.json": task_bytes,
        "rule-snapshot.json": _canonical_json_bytes(rule_ref),
        "future-question.json": _canonical_json_bytes(question),
        f"cases/{row['case_id']}/chart.json": _canonical_json_bytes(chart),
    }
    expected = {
        "intake.json", "tasks.json", "rule-snapshot.json", "future-question.json",
        f"cases/{row['case_id']}/chart.json",
    }
    if set(files) != expected:
        raise _stop("single-case bundle whitelist mismatch")
    return files, row, question


def prepare_single_case_blind_bundle(
    intake: Mapping[str, Any],
    future_question: Mapping[str, Any],
    tasks_path: Path,
    rule_snapshot_path: Path,
    target_dir: Path,
    *,
    dry_run: bool,
    revision: Mapping[str, Any] | None = None,
    created_at: str | None = None,
    _allow_unpublished_parents: bool = False,
) -> dict[str, Any]:
    """Build and create-only publish one whitelist-only blind bundle."""
    target = Path(target_dir)
    _reject_symlink(target, "single-case bundle target")
    if target.exists():
        raise ValueError(f"bundle target must not exist: {target}")
    files, row, question = _single_bundle_files(
        intake, future_question, Path(tasks_path), Path(rule_snapshot_path),
        allow_unpublished_parents=_allow_unpublished_parents,
    )
    version_match = re.search(r"--blind-bundle--v(\d{3})$", target.as_posix())
    if version_match is None:
        if revision:
            raise ValueError("revision metadata requires a versioned blind-bundle target")
        version = 1
    else:
        version = int(version_match.group(1))
    revision_fields = _revision_payload(revision, version)
    hashes = {name: _sha256(content) for name, content in sorted(files.items())}
    parents = [
        {
            "artifact_path": intake["artifact_path"],
            "artifact_sha256": intake["artifact_sha256"],
        },
        {
            "artifact_path": question["artifact_path"],
            "artifact_sha256": question["artifact_sha256"],
        },
    ]
    intake_created = _parse_utc(intake["created_at"], "intake created_at")
    question_created = _parse_utc(question["created_at"], "future-question created_at")
    parent_created = max(intake_created, question_created)
    bundle_created = _parse_utc(created_at, "bundle created_at") if created_at else parent_created
    freeze_at = _parse_utc(
        question["observation_window"]["start_at"], "observation_window.start_at",
    )
    if not parent_created <= bundle_created <= freeze_at:
        raise _stop("single-case bundle time must satisfy parents <= bundle <= planned freeze")
    created_at = bundle_created.isoformat().replace("+00:00", "Z")
    manifest = {
        "schema_version": _SINGLE_BUNDLE_SCHEMA,
        "case_id": row["case_id"],
        "subject_id_hash": intake["subject_id_hash"],
        "created_at": created_at,
        "artifact_path": (target / "bundle-manifest.json").as_posix(),
        "case_count": 1,
        "future_question_count": 1,
        "schools": sorted(SIX_SCHOOLS),
        "parents": parents,
        "files": hashes,
        "bundle_sha256": _sha256(_canonical_json_bytes(hashes)),
        **revision_fields,
    }
    manifest["artifact_sha256"] = canonical_artifact_sha256(manifest)
    if dry_run:
        return manifest

    target.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink(target.parent, "single-case bundle parent")
    temporary = Path(tempfile.mkdtemp(prefix=".b.", dir=target.parent))
    try:
        for name, content in files.items():
            destination = temporary / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        (temporary / "bundle-manifest.json").write_bytes(
            (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        )
        if target.exists() or _is_linklike(target):
            raise ValueError(f"bundle target must not exist: {target}")
        try:
            os.rename(temporary, target)
        except FileExistsError as error:
            raise ValueError(f"bundle target must not exist: {target}") from error
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return manifest


def verify_single_case_bundle(bundle_root: Path) -> dict[str, Any]:
    """Re-read an actual bundle and STOP on any whitelist or digest drift."""
    root = Path(bundle_root)
    _reject_symlink(root, "single-case bundle root")
    if not root.is_dir():
        raise _stop("single-case bundle root must be a directory")
    manifest_path = root / "bundle-manifest.json"
    _reject_symlink(manifest_path, "single-case bundle manifest")
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _stop("single-case bundle manifest is missing or invalid") from error
    expected_manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    if not isinstance(manifest, dict):
        raise _stop("single-case bundle manifest contract mismatch")
    version_match = re.search(r"--blind-bundle--v(\d{3})/bundle-manifest\.json$", str(manifest.get("artifact_path", "")))
    version = int(version_match.group(1)) if version_match is not None else 1
    try:
        validate_revision_metadata(manifest, version)
    except ValueError as error:
        raise _stop(f"single-case bundle revision is invalid: {error}") from error
    expected_manifest_fields = {
        "schema_version", "case_id", "subject_id_hash", "created_at", "artifact_path",
        "case_count", "future_question_count", "schools", "parents", "files",
        "bundle_sha256", "artifact_sha256",
    } | (_REVISION_FIELDS if version > 1 else set())
    if (
        set(manifest) != expected_manifest_fields
        or manifest.get("schema_version") != _SINGLE_BUNDLE_SCHEMA
        or manifest.get("case_count") != 1
        or manifest.get("future_question_count") != 1
        or manifest.get("schools") != sorted(SIX_SCHOOLS)
        or not isinstance(manifest.get("files"), dict)
        or manifest.get("artifact_sha256") != canonical_artifact_sha256(manifest)
    ):
        raise _stop("single-case bundle manifest contract mismatch")
    files = manifest["files"]
    intake_name = "intake.json"
    try:
        intake = json.loads((root / intake_name).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _stop("single-case blind intake is invalid") from error
    records = intake.get("records") if isinstance(intake, dict) else None
    if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
        raise _stop("single-case blind intake requires exactly one record")
    case_id = records[0].get("case_id")
    if not isinstance(case_id, str) or not case_id:
        raise _stop("single-case blind intake case is invalid")
    expected = {
        "intake.json", "tasks.json", "rule-snapshot.json", "future-question.json",
        f"cases/{case_id}/chart.json",
    }
    actual: set[str] = set()
    actual_directories: set[str] = set()
    expected_directories = {"cases", f"cases/{case_id}"}
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in directory_names:
            candidate = base / name
            if _is_linklike(candidate):
                raise _stop(f"single-case bundle contains symlink/junction: {candidate}")
            actual_directories.add(candidate.relative_to(root).as_posix())
        for name in file_names:
            candidate = base / name
            if _is_linklike(candidate) or not candidate.is_file():
                raise _stop(f"single-case bundle contains non-regular file: {candidate}")
            relative = candidate.relative_to(root).as_posix()
            if relative != "bundle-manifest.json":
                actual.add(relative)
    if (
        set(files) != expected
        or actual != expected
        or actual_directories != expected_directories
    ):
        raise _stop("single-case bundle contains extra, missing, or forbidden file")
    if any(not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None for value in files.values()):
        raise _stop("single-case bundle file digest contract mismatch")
    for name, digest in files.items():
        if _sha256((root / name).read_bytes()) != digest:
            raise _stop(f"single-case bundle file hash changed: {name}")
    if manifest.get("bundle_sha256") != _sha256(_canonical_json_bytes(files)):
        raise _stop("single-case bundle hash changed")
    try:
        question = json.loads((root / "future-question.json").read_text(encoding="utf-8"))
        chart = json.loads((root / f"cases/{case_id}/chart.json").read_text(encoding="utf-8"))
        rule_reference = json.loads((root / "rule-snapshot.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _stop("single-case bundle JSON content is invalid") from error
    if any(_contains_forbidden_marker(value) for value in (intake, question, chart, rule_reference)):
        raise _stop("single-case bundle contains forbidden content")
    if question.get("artifact_sha256") != canonical_artifact_sha256(question):
        raise _stop("single-case future-question hash changed")
    if (
        question.get("case_id") != case_id
        or chart.get("case_id") != case_id
        or manifest.get("case_id") != case_id
        or manifest.get("subject_id_hash") != question.get("subject_id_hash")
        or manifest.get("artifact_path") != (root / "bundle-manifest.json").as_posix()
    ):
        raise _stop("single-case bundle parent mismatch")
    try:
        bundle_created = _parse_utc(manifest.get("created_at"), "bundle created_at")
        question_created = _parse_utc(question.get("created_at"), "future-question created_at")
    except ValueError as error:
        raise _stop(f"single-case bundle time contract mismatch: {error}") from error
    if bundle_created < question_created:
        raise _stop("single-case bundle created_at predates future-question")
    parents = manifest.get("parents")
    if (
        not isinstance(parents, list)
        or len(parents) != 2
        or parents[1] != {
            "artifact_path": question.get("artifact_path"),
            "artifact_sha256": question.get("artifact_sha256"),
        }
    ):
        raise _stop("single-case bundle future-question parent mismatch")
    if manifest_bytes != expected_manifest_bytes:
        raise _stop("single-case bundle manifest byte drift detected")
    return {
        "manifest": manifest,
        "manifest_path": manifest_path,
        "chart": chart,
        "future_question": question,
        "parent_refs": parents,
    }


def _single_case_parent_document(reference: Mapping[str, Any], description: str) -> dict[str, Any]:
    if not isinstance(reference, Mapping) or set(reference) != {"artifact_path", "artifact_sha256"}:
        raise _stop(f"{description} parent reference is invalid")
    try:
        return validate_parent_ref(ArtifactRef(
            artifact_path=str(reference["artifact_path"]),
            artifact_sha256=str(reference["artifact_sha256"]),
        ))
    except (OSError, TypeError, ValueError) as error:
        raise _stop(f"{description} parent drift: {error}") from error


def _safe_timing_outputs(
    run: FrozenBlindRun,
    timing_task_ids: set[str],
    chart: Mapping[str, Any],
) -> list[BlindSchoolOutput]:
    """Keep timing claims only when every prediction cites a real annual chart fact."""
    liunian_steps = chart.get("liunian_steps")
    step_count = len(liunian_steps) if isinstance(liunian_steps, list) else 0

    def has_resolved_liunian_ref(prediction: Any) -> bool:
        for ref in prediction.fact_refs:
            match = re.fullmatch(r"liunian_steps\.(\d+)(?:\..+)?", ref)
            if match is not None and int(match.group(1)) < step_count:
                return True
        return False

    outputs: list[BlindSchoolOutput] = []
    for output in run.outputs:
        timing_is_proven = bool(output.predictions) and all(
            has_resolved_liunian_ref(prediction) for prediction in output.predictions
        )
        if output.task_id in timing_task_ids and output.state == "claim" and not timing_is_proven:
            outputs.append(BlindSchoolOutput(
                case_id=output.case_id,
                school_id=output.school_id,
                task_id=output.task_id,
                state="abstain",
                rationale=(
                    "timing claim safely abstained: evidence has no structured fact_ref "
                    "to liunian_steps"
                ),
            ))
        else:
            outputs.append(output)
    return outputs


def _assert_complete_single_case_grid(
    outputs: Sequence[BlindSchoolOutput],
    *,
    case_id: str,
    task_ids: Sequence[str],
) -> None:
    expected = {
        (case_id, school, task_id)
        for school in SIX_SCHOOLS
        for task_id in task_ids
    }
    identities = [(row.case_id, row.school_id, row.task_id) for row in outputs]
    if len(identities) != len(set(identities)):
        raise _stop("single-case frozen run grid contains duplicate identity")
    actual = set(identities)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise _stop(f"single-case frozen run grid mismatch; missing={missing}, extra={extra}")
    if any(row.state not in {"claim", "abstain", "unsupported"} for row in outputs):
        raise _stop("single-case frozen run contains invalid output state")


def _merge_governance_yang_divorce_slot(
    outputs: Sequence[BlindSchoolOutput],
    *,
    generated_run: FrozenBlindRun,
    task_document: Mapping[str, Any],
    case_id: str,
    result: GovernanceShadowResult,
    projections: tuple[GovernanceShadowTaskProjection, ...],
) -> list[BlindSchoolOutput]:
    if len(projections) != 1 or type(projections[0]) is not GovernanceShadowTaskProjection:
        raise TypeError("governance mode requires exactly one exact GovernanceShadowTaskProjection")
    projection = projections[0]
    target_task_id = "marriage.divorce_or_remarriage"
    task_rows = [
        task for task in task_document.get("tasks", [])
        if isinstance(task, dict) and task.get("task_id") == target_task_id
    ]
    if len(task_rows) != 1:
        raise ValueError("governance target task must occur exactly once in the bundled catalog")
    try:
        task = BlindTask(**task_rows[0])
    except (TypeError, ValueError) as error:
        raise ValueError(f"governance target task is invalid: {error}") from error
    if projection.case_id != case_id:
        raise ValueError("governance projection case mismatch")
    if projection.task_catalog_version != generated_run.task_catalog_version:
        raise ValueError("governance projection task catalog mismatch")
    if projection.rule_version != generated_run.rule_snapshot_id:
        raise ValueError("governance projection rule version mismatch")
    if normalize_school_input("yang") != "yang_qingjuan" or projection.school_id != "yang_qingjuan":
        raise ValueError("governance projection does not own the canonical Yang slot")

    adapted = adapt_governance_shadow_to_blind_outputs(result, task, projections)
    if len(adapted) != 1:
        raise ValueError("governance adapter must return exactly one output")
    canonical = adapted[0]
    if (
        canonical.case_id,
        canonical.school_id,
        canonical.task_id,
    ) != (case_id, "yang_qingjuan", target_task_id):
        raise ValueError("governance adapter returned the wrong target identity")
    alias_output = BlindSchoolOutput(
        case_id=canonical.case_id,
        school_id="yang",
        task_id=canonical.task_id,
        state=canonical.state,
        rationale=canonical.rationale,
        predictions=list(canonical.predictions),
        counter_evidence=list(canonical.counter_evidence),
    )
    target = (case_id, "yang", target_task_id)
    matches = sum(
        (output.case_id, output.school_id, output.task_id) == target
        for output in outputs
    )
    if matches != 1:
        raise ValueError("legacy Yang divorce slot must occur exactly once")
    return [
        alias_output
        if (output.case_id, output.school_id, output.task_id) == target
        else output
        for output in outputs
    ]


def build_single_case_staged_frozen_run(
    bundle_root: Path,
    *,
    now_utc: str | None = None,
    freeze_at: str | None = None,
    executed_at: str | None = None,
    revision: Mapping[str, Any] | None = None,
    migration_context: Mapping[str, Any] | None = None,
    governance_shadow_result: GovernanceShadowResult | None = None,
    governance_shadow_projections: tuple[GovernanceShadowTaskProjection, ...] = (),
) -> dict[str, Any]:
    """Re-verify and freeze exactly one complete six-school prospective case."""
    if type(governance_shadow_projections) is not tuple:
        raise TypeError("governance_shadow_projections must be an exact tuple")
    if governance_shadow_result is None:
        if governance_shadow_projections != ():
            raise ValueError("governance inputs must be both absent or both present")
    elif type(governance_shadow_result) is not GovernanceShadowResult:
        raise TypeError("governance_shadow_result must be an exact GovernanceShadowResult")
    elif len(governance_shadow_projections) != 1:
        raise ValueError("governance mode requires exactly one projection")

    root = Path(bundle_root)
    verified = verify_single_case_bundle(root)
    manifest = verified["manifest"]
    parent_refs = verified["parent_refs"]
    intake_parent = _single_case_parent_document(parent_refs[0], "single-case intake")
    question_parent = _single_case_parent_document(parent_refs[1], "future-question")
    row = validate_single_case_intake(intake_parent)
    question = _validate_future_question_parent(question_parent, intake_parent)
    if question != verified["future_question"]:
        raise _stop("future-question bundled content drifted from registered parent")

    # Import locally: the compatibility CLI already owns the established generation path.
    from tools import school_capability_prospective as prospective

    staged = prospective.build_staged_frozen_run(root)
    assignments = staged.get("case_task_assignments")
    expected_assignment = [{"case_id": row["case_id"], "task_ids": sorted(row["task_ids"])}]
    if assignments != expected_assignment:
        raise _stop("single-case frozen run requires exactly one bound case assignment")
    if question.get("future_task_id") not in row["task_ids"]:
        raise _stop("future-question task is not assigned to the single case")

    try:
        task_document = json.loads((root / "tasks.json").read_text(encoding="utf-8"))
        timing_task_ids = {
            task["task_id"]
            for task in task_document["tasks"]
            if task.get("claim_type") == "event_timing"
        }
        generated_run = FrozenBlindRun.from_dict(staged["frozen_run"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise _stop(f"single-case generated frozen run is invalid: {error}") from error
    merged_outputs: Sequence[BlindSchoolOutput] = generated_run.outputs
    if governance_shadow_result is not None:
        merged_outputs = _merge_governance_yang_divorce_slot(
            merged_outputs,
            generated_run=generated_run,
            task_document=task_document,
            case_id=row["case_id"],
            result=governance_shadow_result,
            projections=governance_shadow_projections,
        )
    merged_run = FrozenBlindRun(
        task_catalog_version=generated_run.task_catalog_version,
        rule_snapshot_id=generated_run.rule_snapshot_id,
        frozen_at=generated_run.frozen_at,
        outputs=list(merged_outputs),
        freeze_hash=generated_run.freeze_hash,
    )
    safe_outputs = _safe_timing_outputs(merged_run, timing_task_ids, verified["chart"])
    _assert_complete_single_case_grid(
        safe_outputs, case_id=row["case_id"], task_ids=sorted(row["task_ids"]),
    )
    planned_start = question["observation_window"]["start_at"]
    freeze_at = freeze_at or planned_start
    executed_at = executed_at or now_utc or freeze_at
    try:
        freeze_time = _parse_utc(freeze_at, "freeze_at")
        execution_time = _parse_utc(executed_at, "executed_at")
        planned_time = _parse_utc(planned_start, "observation_window.start_at")
        intake_time = _parse_utc(intake_parent["created_at"], "intake created_at")
        bundle_time = _parse_utc(manifest["created_at"], "bundle created_at")
    except (KeyError, ValueError) as error:
        raise _stop(f"single-case freeze time contract mismatch: {error}") from error
    if freeze_time != planned_time:
        raise _stop("freeze_at must equal observation_window.start_at")
    if not freeze_time <= execution_time <= freeze_time + timedelta(seconds=60):
        raise _stop("executed_at must be within [freeze_at, freeze_at+60s]")
    if not intake_time <= bundle_time <= freeze_time:
        raise _stop("single-case time order must satisfy intake <= bundle <= freeze")
    validate_future_question_registration(question, freeze_at=freeze_at)
    safe_run = freeze_outputs(
        safe_outputs,
        generated_run.task_catalog_version,
        generated_run.rule_snapshot_id,
        frozen_at=freeze_at,
    )
    verify_frozen_run(safe_run)

    version_match = re.search(
        r"--blind-bundle--v(\d{3})/bundle-manifest\.json$",
        str(manifest["artifact_path"]),
    )
    version = int(version_match.group(1)) if version_match is not None else 1
    revision_fields = _revision_payload(revision, version)
    migration_fields: dict[str, Any] = {}
    if migration_context is not None:
        migration_fields = dict(migration_context)
        if migration_fields != {
            "revision_scope": "parent_chain",
            "superseded_chain_terminal_kind": "blind-bundle",
        }:
            raise _stop("approved migration context is invalid")
    if version > 1:
        try:
            predecessor = validate_parent_ref(ArtifactRef(
                revision_fields["supersedes"],
                revision_fields["supersedes_sha256"],
            ))
        except (KeyError, TypeError, ValueError) as error:
            raise _stop(f"frozen run supersedes parent is invalid: {error}") from error
        formal_previous_path = single_case_artifact_path(
            Path(intake_parent["artifact_path"]).parent.parent,
            row["case_id"],
            "frozen-run",
            version - 1,
        )
        if migration_fields:
            if version == 2 and (formal_previous_path.exists() or formal_previous_path.is_symlink()):
                raise _stop("migration cannot bypass the latest formal frozen run")
            try:
                predecessor_version = _artifact_version(
                    predecessor.get("artifact_path", "").replace(
                        "/bundle-manifest.json", ".json"
                    ),
                    "blind-bundle",
                )
            except ValueError:
                bundle_match = re.search(
                    r"--blind-bundle--v(\d{3})/bundle-manifest\.json$",
                    str(predecessor.get("artifact_path", "")),
                )
                predecessor_version = int(bundle_match.group(1)) if bundle_match else -1
            if (
                predecessor_version != version - 1
                or predecessor.get("schema_version") != _SINGLE_BUNDLE_SCHEMA
                or predecessor.get("case_id") != row["case_id"]
                or predecessor.get("subject_id_hash") != intake_parent["subject_id_hash"]
            ):
                raise _stop("migration supersedes parent must be the valid previous blind bundle")
        else:
            try:
                predecessor_version = _artifact_version(
                    predecessor.get("artifact_path"), "frozen-run",
                )
                predecessor_run = FrozenBlindRun.from_dict(predecessor["frozen_run"])
                verify_frozen_run(predecessor_run)
            except (KeyError, TypeError, ValueError) as error:
                raise _stop(f"frozen run supersedes parent is invalid: {error}") from error
            if (
                predecessor_version != version - 1
                or predecessor.get("schema_version") != "school-capability-single-case-staged-run/v1"
                or predecessor.get("case_id") != row["case_id"]
                or predecessor.get("subject_id_hash") != intake_parent["subject_id_hash"]
                or Path(revision_fields["supersedes"]) != formal_previous_path
            ):
                raise _stop("frozen run supersedes parent must be the latest formal previous run")

    task_hash = manifest["files"]["tasks.json"]
    rule_hash = manifest["files"]["rule-snapshot.json"]
    manifest_hash = manifest["artifact_sha256"]
    parents = [
        dict(parent_refs[0]),
        dict(parent_refs[1]),
        {"artifact_path": (root / "tasks.json").as_posix(), "artifact_sha256": task_hash},
        {"artifact_path": (root / "rule-snapshot.json").as_posix(), "artifact_sha256": rule_hash},
        {"artifact_path": (root / "bundle-manifest.json").as_posix(), "artifact_sha256": manifest_hash},
    ]
    artifact_path = single_case_artifact_path(
        Path(intake_parent["artifact_path"]).parent.parent,
        row["case_id"],
        "frozen-run",
        version,
    )
    payload: dict[str, Any] = {
        "schema_version": "school-capability-single-case-staged-run/v1",
        "case_id": row["case_id"],
        "subject_id_hash": intake_parent["subject_id_hash"],
        "created_at": executed_at,
        "freeze_at": freeze_at,
        "executed_at": executed_at,
        "artifact_path": artifact_path.as_posix(),
        "intake_sha256": intake_parent["artifact_sha256"],
        "future_question_registration_sha256": question["artifact_sha256"],
        "task_catalog_sha256": task_hash,
        "rule_snapshot_sha256": rule_hash,
        "bundle_sha256": manifest["bundle_sha256"],
        "bundle_manifest_sha256": manifest_hash,
        "parents": parents,
        "case_task_assignments": expected_assignment,
        "frozen_run": safe_run.to_dict(),
        **revision_fields,
        **migration_fields,
    }
    return {
        **payload,
        "artifact_sha256": _sha256(canonical_json(payload).encode("utf-8")),
    }


def _migration_revision(parent: Mapping[str, Any], reason: str, approved_by: str) -> dict[str, Any]:
    return {
        "supersedes": parent["artifact_path"],
        "supersedes_sha256": parent["artifact_sha256"],
        "reason": reason,
        "approved_by": approved_by,
    }


def _assert_migration_paths_clean(case_dir: Path, *, previous_version: int) -> None:
    for candidate in case_dir.iterdir():
        name = candidate.name.lower()
        frozen_match = re.search(r"--frozen-run--v(\d{3})\.json$", name)
        if frozen_match is not None and 2 <= int(frozen_match.group(1)) <= previous_version:
            continue
        if any(kind in name for kind in _FORBIDDEN_MIGRATION_KINDS):
            raise _stop(f"forbidden migration artifact exists: {candidate}")


def prepare_parent_chain_v002_migration(
    *,
    input_file: Path,
    tasks_path: Path,
    rule_snapshot_path: Path,
    tasks_by_case: dict[str, list[str]],
    future_question_draft: Mapping[str, Any],
    case_root: Path,
    operator: str,
    approved_by: str,
    reason: str,
    transaction_started_at: str,
    freeze_at: str,
    executed_at: str,
    dry_run: bool,
    next_version: int = 2,
) -> dict[str, Any]:
    """Plan or create-only publish an approved whole-parent-chain transaction."""
    input_file = Path(input_file)
    case_id = input_file.parent.name
    case_root = Path(case_root)
    case_dir = case_root / case_id
    if not case_dir.is_dir():
        raise _stop("single-case directory is missing")
    if isinstance(next_version, bool) or not isinstance(next_version, int) or next_version < 2:
        raise ValueError("next_version must be an integer greater than or equal to 2")
    previous_version = next_version - 1
    _assert_migration_paths_clean(case_dir, previous_version=previous_version)

    def sealed(path: Path) -> dict[str, Any]:
        try:
            digest = json.loads(path.read_text(encoding="utf-8"))["artifact_sha256"]
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError) as error:
            raise _stop(f"migration parent is invalid: {path}") from error
        return validate_parent_ref(ArtifactRef(path.as_posix(), digest))

    previous_question = sealed(single_case_artifact_path(
        case_root, case_id, "future-question-registration", previous_version,
    ))
    previous_intake = sealed(single_case_artifact_path(
        case_root, case_id, "intake", previous_version,
    ))
    previous_bundle_root = case_dir / f"{case_id}--blind-bundle--v{previous_version:03d}"
    previous_bundle = verify_single_case_bundle(previous_bundle_root)["manifest"]
    if not (
        previous_question["case_id"]
        == previous_intake["case_id"]
        == previous_bundle["case_id"]
        == case_id
        and previous_question["subject_id_hash"]
        == previous_intake["subject_id_hash"]
        == previous_bundle["subject_id_hash"]
    ):
        raise _stop("previous migration parents do not bind the same case and subject")

    transaction_time = _parse_utc(transaction_started_at, "transaction_started_at")
    question_created = transaction_time
    intake_created = transaction_time + timedelta(microseconds=1)
    bundle_created = transaction_time + timedelta(microseconds=2)
    freeze_time = _parse_utc(freeze_at, "freeze_at")
    execution_time = _parse_utc(executed_at, "executed_at")
    if not bundle_created < freeze_time <= execution_time <= freeze_time + timedelta(seconds=60):
        raise _stop(
            "migration time order must satisfy transaction/question < intake < bundle < freeze "
            "<= executed_at <= freeze_at+60s"
        )
    draft = dict(future_question_draft)
    draft["observation_window"] = {
        "start_at": freeze_at,
        "end_at": _add_calendar_months(freeze_time, 3).isoformat().replace("+00:00", "Z"),
    }
    question_revision = _migration_revision(previous_question, reason, approved_by)
    intake_revision = _migration_revision(previous_intake, reason, approved_by)
    bundle_revision = _migration_revision(previous_bundle, reason, approved_by)
    intake, question = build_single_case_intake(
        input_file,
        json.loads(Path(tasks_path).read_text(encoding="utf-8")),
        SIX_SCHOOLS,
        operator,
        tasks_by_case,
        draft,
        created_at=intake_created.isoformat().replace("+00:00", "Z"),
        question_created_at=question_created.isoformat().replace("+00:00", "Z"),
        case_root=case_root,
        version=next_version,
        question_revision=question_revision,
        intake_revision=intake_revision,
    )
    targets = {
        "future_question": Path(question["artifact_path"]),
        "intake": Path(intake["artifact_path"]),
        "blind_bundle": case_dir / f"{case_id}--blind-bundle--v{next_version:03d}",
        "frozen_run": single_case_artifact_path(
            case_root, case_id, "frozen-run", next_version,
        ),
    }
    existing = [path for path in targets.values() if path.exists() or path.is_symlink()]
    if existing:
        raise ValueError("migration target(s) must not exist: " + ", ".join(map(str, existing)))

    # Build and reverify in a sibling staging tree before any formal write.
    staging = Path(tempfile.mkdtemp(prefix=f".pcv{next_version}.", dir=case_dir.parent))
    try:
        staged_root = staging
        staged_question = {**question, "artifact_path": single_case_artifact_path(
            staged_root, case_id, "future-question-registration", next_version,
        ).as_posix()}
        staged_question["artifact_sha256"] = canonical_artifact_sha256(staged_question)
        staged_intake = {**intake, "artifact_path": single_case_artifact_path(
            staged_root, case_id, "intake", next_version,
        ).as_posix()}
        staged_intake["future_question"] = {
            "artifact_path": staged_question["artifact_path"],
            "artifact_sha256": staged_question["artifact_sha256"],
        }
        staged_intake["parents"] = [staged_intake["future_question"]]
        staged_intake["artifact_sha256"] = canonical_artifact_sha256(staged_intake)
        Path(staged_question["artifact_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(staged_question["artifact_path"]).write_bytes(
            (json.dumps(staged_question, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        )
        Path(staged_intake["artifact_path"]).write_bytes(
            (json.dumps(staged_intake, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        )
        staged_bundle_root = Path(staged_intake["artifact_path"]).with_name(
            f"{case_id}--blind-bundle--v{next_version:03d}"
        )
        staged_manifest = prepare_single_case_blind_bundle(
            staged_intake, staged_question, Path(tasks_path), Path(rule_snapshot_path),
            staged_bundle_root, dry_run=False, revision=bundle_revision,
            created_at=bundle_created.isoformat().replace("+00:00", "Z"),
        )
        staged_run = build_single_case_staged_frozen_run(
            staged_bundle_root,
            freeze_at=freeze_at,
            executed_at=executed_at,
            revision=bundle_revision,
            migration_context={
                "revision_scope": "parent_chain",
                "superseded_chain_terminal_kind": "blind-bundle",
            },
        )
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    question = {**staged_question, "artifact_path": targets["future_question"].as_posix()}
    question["artifact_sha256"] = canonical_artifact_sha256(question)
    intake = {**staged_intake, "artifact_path": targets["intake"].as_posix()}
    intake["future_question"] = {
        "artifact_path": question["artifact_path"], "artifact_sha256": question["artifact_sha256"],
    }
    intake["parents"] = [intake["future_question"]]
    intake["artifact_sha256"] = canonical_artifact_sha256(intake)
    manifest = prepare_single_case_blind_bundle(
        intake, question, Path(tasks_path), Path(rule_snapshot_path),
        targets["blind_bundle"], dry_run=True, revision=bundle_revision,
        created_at=bundle_created.isoformat().replace("+00:00", "Z"),
        _allow_unpublished_parents=True,
    )
    frozen = {
        **staged_run,
        "artifact_path": targets["frozen_run"].as_posix(),
        "intake_sha256": intake["artifact_sha256"],
        "future_question_registration_sha256": question["artifact_sha256"],
        "bundle_sha256": manifest["bundle_sha256"],
        "bundle_manifest_sha256": manifest["artifact_sha256"],
    }
    frozen["parents"] = [
        manifest["parents"][0], manifest["parents"][1],
        {"artifact_path": (targets["blind_bundle"] / "tasks.json").as_posix(), "artifact_sha256": frozen["task_catalog_sha256"]},
        {"artifact_path": (targets["blind_bundle"] / "rule-snapshot.json").as_posix(), "artifact_sha256": frozen["rule_snapshot_sha256"]},
        {"artifact_path": manifest["artifact_path"], "artifact_sha256": manifest["artifact_sha256"]},
    ]
    frozen["artifact_sha256"] = canonical_artifact_sha256(frozen)
    artifacts = {
        "future_question": question,
        "intake": intake,
        "blind_bundle": manifest,
        "frozen_run": frozen,
    }
    plan = {
        "status": "DRY_RUN" if dry_run else "PUBLISHED",
        "publication_order": list(artifacts),
        "freeze_at": freeze_at,
        "artifacts": artifacts,
    }
    if dry_run:
        return plan

    published: list[str] = []
    try:
        publish_new_json(targets["future_question"], question, dry_run=False)
        published.append(targets["future_question"].as_posix())
        publish_new_json(targets["intake"], intake, dry_run=False)
        published.append(targets["intake"].as_posix())
        manifest = prepare_single_case_blind_bundle(
            intake, question, Path(tasks_path), Path(rule_snapshot_path),
            targets["blind_bundle"], dry_run=False, revision=bundle_revision,
            created_at=bundle_created.isoformat().replace("+00:00", "Z"),
        )
        published.append(targets["blind_bundle"].as_posix())
        frozen = build_single_case_staged_frozen_run(
            targets["blind_bundle"],
            freeze_at=freeze_at,
            executed_at=executed_at,
            revision=bundle_revision,
            migration_context={
                "revision_scope": "parent_chain",
                "superseded_chain_terminal_kind": "blind-bundle",
            },
        )
        artifacts["blind_bundle"] = manifest
        artifacts["frozen_run"] = frozen
        publish_new_json(targets["frozen_run"], frozen, dry_run=False)
        published.append(targets["frozen_run"].as_posix())
    except BaseException as error:
        raise ValueError(
            "RECOVERABLE_HOLD: parent-chain v002 publication interrupted; "
            f"published={published}; cause={error}"
        ) from error
    return plan
