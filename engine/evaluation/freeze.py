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
    if document.get("freeze_hash") != run.freeze_hash:
        raise ValueError("labels freeze_hash does not match frozen run")
    return [RevealedLabel.from_dict(item) for item in document.get("labels", [])]
