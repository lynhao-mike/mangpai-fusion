from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from engine.evaluation.models import BlindSchoolOutput, FrozenBlindRun, RevealedLabel


def canonical_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_freeze_hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _sorted_outputs(outputs: Iterable[BlindSchoolOutput]) -> list[BlindSchoolOutput]:
    normalized = []
    for output in outputs:
        data = output.to_dict()
        data["predictions"] = sorted(data["predictions"], key=lambda item: item["prediction_id"])
        normalized.append(BlindSchoolOutput.from_dict(data))
    return sorted(normalized, key=lambda item: (item.case_id, item.task_id, item.school_id))


def _payload(run: FrozenBlindRun) -> dict[str, object]:
    payload = run.to_dict()
    payload.pop("freeze_hash")
    return payload


def freeze_outputs(
    outputs: Sequence[BlindSchoolOutput] | Iterable[BlindSchoolOutput],
    task_catalog_version: str,
    rule_snapshot_id: str,
    *,
    frozen_at: str | None = None,
) -> FrozenBlindRun:
    normalized_outputs = _sorted_outputs(outputs)
    timestamp = frozen_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # Protect frozen_at while keeping identical freezes stable: absent an injected
    # timestamp, derive its value from the canonical content rather than wall-clock time.
    if frozen_at is None:
        seed = {
            "task_catalog_version": task_catalog_version,
            "rule_snapshot_id": rule_snapshot_id,
            "outputs": [item.to_dict() for item in normalized_outputs],
        }
        timestamp = f"content:{compute_freeze_hash(seed)}"
    run = FrozenBlindRun(
        task_catalog_version=task_catalog_version,
        rule_snapshot_id=rule_snapshot_id,
        frozen_at=timestamp,
        outputs=normalized_outputs,
        freeze_hash="",
    )
    return FrozenBlindRun.from_dict({**run.to_dict(), "freeze_hash": compute_freeze_hash(_payload(run))})


def verify_frozen_run(run: FrozenBlindRun) -> None:
    if compute_freeze_hash(_payload(run)) != run.freeze_hash:
        raise ValueError("freeze hash mismatch")


def reveal_labels(run: FrozenBlindRun, labels_path: Path) -> list[RevealedLabel]:
    verify_frozen_run(run)
    document = json.loads(labels_path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or set(document) != {"schema_version", "freeze_hash", "labels"}:
        raise ValueError("labels document must contain exactly schema_version, freeze_hash, and labels")
    if document["schema_version"] != "school-capability-labels/v1":
        raise ValueError("labels schema_version must be school-capability-labels/v1")
    if document["freeze_hash"] != run.freeze_hash:
        raise ValueError("labels freeze_hash does not match frozen run")
    raw_labels = document["labels"]
    if not isinstance(raw_labels, list):
        raise ValueError("labels must be a list")
    required = {"case_id", "task_id", "label", "observed_at", "source", "confidence_grade", "quantifiable", "conflict_state", "reviewer"}
    labels = []
    seen = set()
    for item in raw_labels:
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError("label record has invalid schema")
        identity = item["case_id"], item["task_id"]
        if identity in seen:
            raise ValueError("duplicate label identity")
        seen.add(identity)
        labels.append(RevealedLabel.from_dict(item))
    return labels
