from __future__ import annotations

import calendar
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Mapping, Sequence, Set
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    canonical_artifact_sha256,
    single_case_artifact_path,
    validate_parent_ref,
)
from engine.evaluation.freeze import canonical_json, freeze_outputs, verify_frozen_run
from engine.evaluation.models import BlindSchoolOutput, FrozenBlindRun


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
    "allowed_time_horizons", "required_input_fields", "label_schema",
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
    if not isinstance(document, Mapping) or set(document) != _FUTURE_REQUIRED_FIELDS:
        raise ValueError("future question registration schema is invalid")
    result = dict(document)
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
    existing_subject_hashes: Set[str] = frozenset(),
    case_root: Path,
    version: int = 1,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build one intake and one externally supplied question for immutable publication."""
    _parse_utc(created_at, "created_at")
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
        created_at=created_at,
        artifact_path=question_path,
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
    }
    intake = {
        **intake_payload,
        "artifact_sha256": canonical_artifact_sha256(intake_payload),
    }
    return intake, question


def validate_single_case_intake(intake: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return the only immutable intake record."""
    if not isinstance(intake, Mapping) or set(intake) != _SINGLE_INTAKE_REQUIRED_FIELDS:
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
) -> tuple[dict[str, bytes], dict[str, Any], dict[str, Any]]:
    validate_single_case_intake(intake)
    _validate_future_question_parent(future_question, intake)
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
    legacy_task_bytes = _canonical_json_bytes({
        "schema_version": task_document.get("schema_version"), "tasks": clean_tasks,
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
) -> dict[str, Any]:
    """Build and create-only publish one whitelist-only blind bundle."""
    target = Path(target_dir)
    _reject_symlink(target, "single-case bundle target")
    if target.exists():
        raise ValueError(f"bundle target must not exist: {target}")
    files, row, question = _single_bundle_files(
        intake, future_question, Path(tasks_path), Path(rule_snapshot_path),
    )
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
    bundle_created = max(intake_created, question_created)
    freeze_at = _parse_utc(
        question["observation_window"]["start_at"], "observation_window.start_at",
    )
    if bundle_created > freeze_at:
        raise _stop("single-case bundle cannot be generated after planned freeze")
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
    }
    manifest["artifact_sha256"] = canonical_artifact_sha256(manifest)
    if dry_run:
        return manifest

    target.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink(target.parent, "single-case bundle parent")
    temporary = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
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
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {
            "schema_version", "case_id", "subject_id_hash", "created_at", "artifact_path",
            "case_count", "future_question_count", "schools", "parents", "files",
            "bundle_sha256", "artifact_sha256",
        }
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


def build_single_case_staged_frozen_run(bundle_root: Path) -> dict[str, Any]:
    """Re-verify and freeze exactly one complete six-school prospective case."""
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
    safe_outputs = _safe_timing_outputs(generated_run, timing_task_ids, verified["chart"])
    _assert_complete_single_case_grid(
        safe_outputs, case_id=row["case_id"], task_ids=sorted(row["task_ids"]),
    )
    frozen_at = question["observation_window"]["start_at"]
    try:
        freeze_time = _parse_utc(frozen_at, "freeze_at")
        intake_time = _parse_utc(intake_parent["created_at"], "intake created_at")
        bundle_time = _parse_utc(manifest["created_at"], "bundle created_at")
    except (KeyError, ValueError) as error:
        raise _stop(f"single-case freeze time contract mismatch: {error}") from error
    if not intake_time <= bundle_time <= freeze_time:
        raise _stop("single-case time order must satisfy intake <= bundle <= freeze")
    validate_future_question_registration(question, freeze_at=frozen_at)
    safe_run = freeze_outputs(
        safe_outputs,
        generated_run.task_catalog_version,
        generated_run.rule_snapshot_id,
        frozen_at=frozen_at,
    )
    verify_frozen_run(safe_run)

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
    artifact_path = Path(intake_parent["artifact_path"]).with_name(
        f"{row['case_id']}--frozen-run--v001.json"
    )
    payload: dict[str, Any] = {
        "schema_version": "school-capability-single-case-staged-run/v1",
        "case_id": row["case_id"],
        "subject_id_hash": intake_parent["subject_id_hash"],
        "created_at": frozen_at,
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
    }
    return {
        **payload,
        "artifact_sha256": _sha256(canonical_json(payload).encode("utf-8")),
    }
