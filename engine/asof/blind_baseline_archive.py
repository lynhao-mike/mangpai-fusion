"""将无反馈 BLIND_BASELINE 绑定到 prospective lineage 并只创建归档。"""
from __future__ import annotations

import dataclasses as _dataclasses
import hashlib as _hashlib
import json as _json
from pathlib import Path as _Path
from typing import Mapping as _Mapping

from engine.asof.blind_baseline import (
    QUESTION_SNAPSHOT_SCHEMA_VERSION,
    RUNTIME_SNAPSHOT_SCHEMA_VERSION,
    ArtifactKind,
    ArtifactReference,
    BaselineQuestionSnapshot,
    BaselineRuntimeSnapshot,
    BlindBaselineRunResult,
    blind_baseline_payload_sha256,
    serialize_blind_baseline_payload,
)
from engine.evaluation.prospective_artifacts import (
    ArtifactRef as _ProspectiveArtifactRef,
    canonical_artifact_sha256 as _canonical_artifact_sha256,
    publish_new_json as _publish_new_json,
    validate_parent_ref as _validate_parent_ref,
)


BLIND_BASELINE_ARTIFACT_SCHEMA_VERSION = "asof-blind-baseline-artifact/v1"


class BlindBaselineArchiveError(ValueError):
    CODES = frozenset(
        {
            "INVALID_TYPE",
            "INVALID_VALUE",
            "IDENTITY_MISMATCH",
            "LINEAGE_MISMATCH",
            "HASH_MISMATCH",
            "PUBLICATION_ERROR",
            "READBACK_ERROR",
        }
    )

    def __init__(self, code: str, message: str) -> None:
        if code not in self.CODES:
            raise ValueError("unknown blind baseline archive error code")
        self.code = code
        super().__init__(f"{code}: {message}")


def _error(code: str, message: str) -> BlindBaselineArchiveError:
    return BlindBaselineArchiveError(code, message)


def _text(value: object, field: str) -> str:
    if type(value) is not str:
        raise _error("INVALID_TYPE", f"{field} must be str")
    if not value.strip():
        raise _error("INVALID_VALUE", f"{field} must not be empty")
    return value


def _mapping(value: object, field: str) -> _Mapping[str, object]:
    if not isinstance(value, _Mapping):
        raise _error("INVALID_TYPE", f"{field} must be a mapping")
    return value


def _digest(value: object, field: str) -> str:
    text = _text(value, field)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise _error("INVALID_VALUE", f"{field} must be lowercase SHA-256")
    return text


def _raw_file_sha256(path: _Path) -> str:
    try:
        return _hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise _error("LINEAGE_MISMATCH", f"cannot read lineage file: {path}") from exc


def _verify_asof_bundle(bundle_root: _Path) -> dict[str, object]:
    """延迟加载 prospective verifier，避免归档基础能力被可选模块阻塞。"""

    from engine.evaluation.prospective_asof import verify_asof_blind_bundle

    return verify_asof_blind_bundle(bundle_root=bundle_root)


def _verify_single_bundle(bundle_root: _Path) -> dict[str, object]:
    """延迟加载 single-case verifier，并保持其事实源验证语义。"""

    from engine.evaluation.prospective_single_case import verify_single_case_bundle

    return verify_single_case_bundle(bundle_root)


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindBaselineLineageContext:
    blind_input: object
    identity: object
    blind_input_sha256: str
    question_snapshot: BaselineQuestionSnapshot
    runtime_snapshot: BaselineRuntimeSnapshot
    parent: ArtifactReference

    def __post_init__(self) -> None:
        _digest(self.blind_input_sha256, "blind_input_sha256")
        if type(self.question_snapshot) is not BaselineQuestionSnapshot:
            raise _error(
                "INVALID_TYPE",
                "question_snapshot must be BaselineQuestionSnapshot",
            )
        if type(self.runtime_snapshot) is not BaselineRuntimeSnapshot:
            raise _error(
                "INVALID_TYPE",
                "runtime_snapshot must be BaselineRuntimeSnapshot",
            )
        if type(self.parent) is not ArtifactReference:
            raise _error("INVALID_TYPE", "parent must be ArtifactReference")


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindBaselineArchiveResult:
    artifact_path: str
    artifact_sha256: str
    document: dict[str, object]
    readback_verified: bool


def load_blind_baseline_lineage_context(
    *,
    asof_bundle_root: _Path,
    code_version: str,
    model_id: str,
) -> BlindBaselineLineageContext:
    """重验 as-of/单案 bundle，并从其唯一事实源构造 baseline 上下文。"""

    if not isinstance(asof_bundle_root, _Path):
        raise _error("INVALID_TYPE", "asof_bundle_root must be pathlib.Path")
    code_version = _text(code_version, "code_version")
    model_id = _text(model_id, "model_id")
    try:
        asof = _verify_asof_bundle(asof_bundle_root)
    except (OSError, TypeError, ValueError) as exc:
        raise _error("LINEAGE_MISMATCH", "as-of blind bundle verification failed") from exc

    manifest = _mapping(asof.get("manifest"), "asof manifest")
    parents = manifest.get("parents")
    if type(parents) is not list or len(parents) != 2:
        raise _error("LINEAGE_MISMATCH", "as-of bundle parent set is invalid")
    single_bundle_ref = _mapping(parents[0], "single-case bundle parent")
    parent_manifest_path = _Path(
        _text(single_bundle_ref.get("artifact_path"), "single-case bundle path")
    )
    try:
        single = _verify_single_bundle(parent_manifest_path.parent)
    except (OSError, TypeError, ValueError) as exc:
        raise _error("LINEAGE_MISMATCH", "single-case blind bundle verification failed") from exc

    single_manifest = _mapping(single.get("manifest"), "single-case manifest")
    if (
        single_manifest.get("artifact_path") != single_bundle_ref.get("artifact_path")
        or single_manifest.get("artifact_sha256")
        != single_bundle_ref.get("artifact_sha256")
    ):
        raise _error("LINEAGE_MISMATCH", "single-case bundle reference differs")

    question = _mapping(single.get("future_question"), "future question")
    task_id = _text(question.get("future_task_id"), "future_task_id")
    question_path = _text(question.get("artifact_path"), "future question path")
    question_sha256 = _digest(
        question.get("artifact_sha256"),
        "future question artifact_sha256",
    )
    window = _mapping(question.get("observation_window"), "observation_window")
    question_snapshot = BaselineQuestionSnapshot(
        QUESTION_SNAPSHOT_SCHEMA_VERSION,
        f"{task_id}@sha256:{question_sha256}",
        task_id,
        _text(question.get("question_text_redacted"), "question_text_redacted"),
        _text(question.get("outcome_type"), "outcome_type"),
        _text(question.get("positive_definition"), "positive_definition"),
        _text(question.get("negative_definition"), "negative_definition"),
        _text(window.get("start_at"), "observation_window.start_at"),
        _text(window.get("end_at"), "observation_window.end_at"),
        ArtifactReference(question_path, question_sha256),
    )

    single_root = parent_manifest_path.parent
    rule_path = single_root / "rule-snapshot.json"
    try:
        rule_reference = _json.loads(rule_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, _json.JSONDecodeError) as exc:
        raise _error("LINEAGE_MISMATCH", "rule snapshot reference is unreadable") from exc
    if type(rule_reference) is not dict or set(rule_reference) != {
        "rule_snapshot_id",
        "sha256",
    }:
        raise _error("LINEAGE_MISMATCH", "rule snapshot reference schema is invalid")
    manifest_files = _mapping(single_manifest.get("files"), "single-case files")
    if _raw_file_sha256(rule_path) != manifest_files.get("rule-snapshot.json"):
        raise _error("HASH_MISMATCH", "bundled rule snapshot file digest differs")
    runtime_snapshot = BaselineRuntimeSnapshot(
        RUNTIME_SNAPSHOT_SCHEMA_VERSION,
        _text(rule_reference.get("rule_snapshot_id"), "rule_snapshot_id"),
        _digest(rule_reference.get("sha256"), "rule snapshot sha256"),
        code_version,
        model_id,
    )

    identity = asof.get("identity")
    initial_envelope = asof.get("initial_envelope")
    blind_input_sha256 = getattr(initial_envelope, "blind_input_sha256", None)
    parent_path = _text(manifest.get("artifact_path"), "as-of manifest path")
    parent_sha256 = _digest(
        manifest.get("artifact_sha256"),
        "as-of manifest artifact_sha256",
    )
    return BlindBaselineLineageContext(
        asof.get("blind_input"),
        identity,
        _digest(blind_input_sha256, "blind_input_sha256"),
        question_snapshot,
        runtime_snapshot,
        ArtifactReference(parent_path, parent_sha256),
    )


def _archive_document(
    *,
    result: BlindBaselineRunResult,
    context: BlindBaselineLineageContext,
    artifact_path: _Path,
) -> dict[str, object]:
    if type(result) is not BlindBaselineRunResult:
        raise _error("INVALID_TYPE", "result must be BlindBaselineRunResult")
    if type(context) is not BlindBaselineLineageContext:
        raise _error("INVALID_TYPE", "context must be BlindBaselineLineageContext")
    if not isinstance(artifact_path, _Path) or not artifact_path.is_absolute():
        raise _error("INVALID_VALUE", "artifact_path must be an absolute pathlib.Path")
    if result.artifact_kind is not ArtifactKind.BLIND_BASELINE:
        raise _error("INVALID_VALUE", "only BLIND_BASELINE can use this archive adapter")
    identity = result.final_envelope.identity
    if identity != context.identity:
        raise _error("IDENTITY_MISMATCH", "baseline identity differs from lineage")
    if result.final_envelope.blind_input_sha256 != context.blind_input_sha256:
        raise _error("HASH_MISMATCH", "blind input digest differs from lineage")
    if result.question_snapshot != context.question_snapshot:
        raise _error("LINEAGE_MISMATCH", "question snapshot differs from lineage")
    if result.runtime_snapshot != context.runtime_snapshot:
        raise _error("LINEAGE_MISMATCH", "runtime snapshot differs from lineage")

    baseline = serialize_blind_baseline_payload(result)
    baseline_sha256 = blind_baseline_payload_sha256(baseline)
    return {
        "schema_version": BLIND_BASELINE_ARTIFACT_SCHEMA_VERSION,
        "artifact_kind": ArtifactKind.BLIND_BASELINE.value,
        "case_id": identity.case_id,
        "as_of_date": identity.as_of_date.isoformat(),
        "session_id": identity.session_id,
        "artifact_path": artifact_path.as_posix(),
        "parents": [
            {
                "artifact_path": context.parent.artifact_path,
                "artifact_sha256": context.parent.artifact_sha256,
            }
        ],
        "baseline_payload_sha256": baseline_sha256,
        "baseline": baseline,
    }


def publish_blind_baseline(
    *,
    result: BlindBaselineRunResult,
    context: BlindBaselineLineageContext,
    artifact_path: _Path,
    admitted_root: _Path,
    dry_run: bool = False,
) -> BlindBaselineArchiveResult:
    """以 create-only 方式发布 baseline，并在正式写入后立即读回验证。"""

    if not isinstance(admitted_root, _Path) or not admitted_root.is_absolute():
        raise _error("INVALID_VALUE", "admitted_root must be an absolute pathlib.Path")
    if type(dry_run) is not bool:
        raise _error("INVALID_TYPE", "dry_run must be exact bool")
    document = _archive_document(
        result=result,
        context=context,
        artifact_path=artifact_path,
    )
    parent_ref = _ProspectiveArtifactRef(
        context.parent.artifact_path,
        context.parent.artifact_sha256,
    )
    try:
        _validate_parent_ref(parent_ref, admitted_root=admitted_root)
        published = _publish_new_json(
            artifact_path,
            document,
            dry_run=dry_run,
            admitted_root=admitted_root,
        )
    except (OSError, TypeError, ValueError) as exc:
        raise _error("PUBLICATION_ERROR", "blind baseline publication failed") from exc

    if dry_run:
        return BlindBaselineArchiveResult(
            published.artifact_path,
            published.artifact_sha256,
            document,
            False,
        )

    try:
        readback = _validate_parent_ref(
            _ProspectiveArtifactRef(
                published.artifact_path,
                published.artifact_sha256,
            ),
            admitted_root=admitted_root,
        )
    except (OSError, TypeError, ValueError) as exc:
        raise _error("READBACK_ERROR", "published blind baseline failed readback") from exc
    if readback.get("artifact_sha256") != published.artifact_sha256:
        raise _error("HASH_MISMATCH", "published artifact digest differs on readback")
    unsigned = {
        key: value for key, value in readback.items() if key != "artifact_sha256"
    }
    if unsigned != document:
        raise _error("READBACK_ERROR", "published blind baseline content differs")
    if _canonical_artifact_sha256(readback) != published.artifact_sha256:
        raise _error("HASH_MISMATCH", "published artifact canonical digest differs")
    baseline = _mapping(readback.get("baseline"), "readback baseline")
    if (
        readback.get("baseline_payload_sha256")
        != blind_baseline_payload_sha256(dict(baseline))
    ):
        raise _error("HASH_MISMATCH", "baseline payload digest differs on readback")
    return BlindBaselineArchiveResult(
        published.artifact_path,
        published.artifact_sha256,
        readback,
        True,
    )


__all__ = (
    "BLIND_BASELINE_ARTIFACT_SCHEMA_VERSION",
    "BlindBaselineArchiveError",
    "BlindBaselineArchiveResult",
    "BlindBaselineLineageContext",
    "load_blind_baseline_lineage_context",
    "publish_blind_baseline",
)
