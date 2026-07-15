"""L9 append-only 审计与内容寻址不可变快照仓储。"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from engine.learning.models import ConditionalLearningSignal, LearningDecision, ManualReviewItem

_SCHEMA_VERSION = "conditional-capability-snapshot/v1"


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


class ConditionalLearningRepository:
    """写入范围严格限制在构造时给定的独立 L9 root。"""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.snapshots_dir = self.root / "snapshots"
        self.signals_path = self.root / "signals.jsonl"
        self.decisions_path = self.root / "decisions.jsonl"
        self.reviews_path = self.root / "reviews.jsonl"
        self.active_path = self.root / "active.json"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _normalize_ref(snapshot_ref: str) -> str:
        digest = snapshot_ref.removeprefix("sha256:")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("snapshot_ref must be sha256:<64 lowercase hex characters>")
        return digest

    def snapshot_path(self, snapshot_ref: str) -> Path:
        return self.snapshots_dir / f"{self._normalize_ref(snapshot_ref)}.json"

    def _append_jsonl(self, path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as handle:
            handle.write(_canonical_bytes(payload) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())

    def record_signal(self, signal: ConditionalLearningSignal) -> None:
        self._append_jsonl(self.signals_path, signal.to_dict())

    def record_decision(self, decision: LearningDecision) -> None:
        self._append_jsonl(self.decisions_path, decision.to_dict())

    def record_review(self, item: ManualReviewItem) -> None:
        self._append_jsonl(self.reviews_path, item.to_dict())

    def freeze_snapshot(
        self,
        posteriors: Iterable[Mapping[str, Any]],
        parent_snapshot_ref: str | None,
        decision_ids: Iterable[str],
        created_at: str,
        *,
        rule_prior_proposals: Iterable[Mapping[str, Any]] = (),
    ) -> str:
        if parent_snapshot_ref is not None:
            self._normalize_ref(parent_snapshot_ref)
        hash_payload = {
            "schema_version": _SCHEMA_VERSION,
            "posteriors": list(posteriors),
            "parent_snapshot_ref": parent_snapshot_ref,
            "decision_ids": list(decision_ids),
            "created_at": created_at,
            "rule_prior_proposals": list(rule_prior_proposals),
        }
        digest = hashlib.sha256(_canonical_bytes(hash_payload)).hexdigest()
        snapshot_ref = f"sha256:{digest}"
        payload = {**hash_payload, "content_hash": snapshot_ref}
        content = _canonical_bytes(payload)
        destination = self.snapshot_path(snapshot_ref)
        if destination.exists():
            if destination.read_bytes() != content:
                raise RuntimeError("content-addressed snapshot collision")
            return snapshot_ref
        self._atomic_write(destination, content, overwrite=False)
        return snapshot_ref

    @staticmethod
    def _atomic_write(destination: Path, content: bytes, *, overwrite: bool) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f"{destination.name}.", suffix=".tmp", dir=destination.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            if destination.exists() and not overwrite:
                raise FileExistsError(destination)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)

    def load_snapshot(self, snapshot_ref: str) -> dict[str, Any]:
        path = self.snapshot_path(snapshot_ref)
        if not path.exists():
            raise FileNotFoundError(f"snapshot does not exist: {snapshot_ref}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("content_hash") != snapshot_ref:
            raise ValueError("snapshot content_hash does not match reference")
        return payload

    def apply_snapshot(self, snapshot_ref: str) -> None:
        self.load_snapshot(snapshot_ref)
        pointer = _canonical_bytes({"snapshot_ref": snapshot_ref})
        self._atomic_write(self.active_path, pointer, overwrite=True)

    def load_active_snapshot(self) -> dict[str, Any] | None:
        if not self.active_path.exists():
            return None
        pointer = json.loads(self.active_path.read_text(encoding="utf-8"))
        return self.load_snapshot(pointer["snapshot_ref"])

    def active_snapshot_ref(self) -> str | None:
        if not self.active_path.exists():
            return None
        return str(json.loads(self.active_path.read_text(encoding="utf-8"))["snapshot_ref"])

    def rollback(self, snapshot_ref: str) -> str:
        snapshot = self.load_snapshot(snapshot_ref)
        parent = snapshot.get("parent_snapshot_ref")
        if not parent:
            raise ValueError("snapshot has no parent to rollback to")
        self.apply_snapshot(parent)
        return str(parent)
