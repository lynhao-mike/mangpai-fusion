"""命题级结构化反馈契约与只读校准候选聚合。

该模块只绑定不可变 ``V5RunSnapshot`` 与原始 claim；不修改理论、规则、
权重、生产路由或历史快照，也不提供 promotion 能力。
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Literal, Sequence

from engine.v5.domain import V5Claim, V5RunSnapshot
from engine.v5.high_risk_gate import HIGH_RISK_TASKS

DOMAIN_FEEDBACK_SCHEMA_VERSION = "domain-claim-feedback-v1"
CALIBRATION_CANDIDATES_SCHEMA_VERSION = "domain-calibration-candidates-v1"
DomainFeedbackStatus = Literal[
    "accepted",
    "rejected",
    "partial",
    "unknown",
    "timing_deviation",
]
DOMAIN_FEEDBACK_STATUSES = frozenset(
    {"accepted", "rejected", "partial", "unknown", "timing_deviation"}
)


def _canonical_hash(payload: object) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def claim_hash(claim: V5Claim) -> str:
    """返回覆盖完整原始命题内容的稳定 SHA-256。"""

    return _canonical_hash(claim.to_dict())


@dataclass(frozen=True)
class DomainClaimFeedback:
    """一名 reviewer 对一个冻结命题的一条 create-only 反馈。"""

    feedback_id: str
    case_id: str
    run_id: str
    snapshot_output_hash: str
    claim_id: str
    claim_hash: str
    reviewer: str = ""
    status: DomainFeedbackStatus = "unknown"
    observed_at: str = ""
    note: str = ""
    schema_version: str = DOMAIN_FEEDBACK_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "feedback_id": self.feedback_id,
            "case_id": self.case_id,
            "run_id": self.run_id,
            "snapshot_output_hash": self.snapshot_output_hash,
            "claim_id": self.claim_id,
            "claim_hash": self.claim_hash,
            "reviewer": self.reviewer,
            "status": self.status,
            "observed_at": self.observed_at,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainClaimFeedback":
        if not isinstance(data, dict):
            raise TypeError("feedback artifact must be a JSON object")
        return cls(
            feedback_id=str(data.get("feedback_id", "")),
            case_id=str(data.get("case_id", "")),
            run_id=str(data.get("run_id", "")),
            snapshot_output_hash=str(data.get("snapshot_output_hash", "")),
            claim_id=str(data.get("claim_id", "")),
            claim_hash=str(data.get("claim_hash", "")),
            reviewer=str(data.get("reviewer", "")),
            status=data.get("status", "unknown"),
            observed_at=str(data.get("observed_at", "")),
            note=str(data.get("note", "")),
            schema_version=str(data.get("schema_version", "")),
        )

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, value: str) -> "DomainClaimFeedback":
        return cls.from_dict(json.loads(value))


def _find_claim(snapshot: V5RunSnapshot, claim_id: str) -> V5Claim:
    matches = [claim for claim in snapshot.claims if claim.claim_id == claim_id]
    if not matches:
        raise ValueError(f"claim_id not found in run snapshot: {claim_id}")
    if len(matches) > 1:
        raise ValueError(f"duplicate claim_id in run snapshot: {claim_id}")
    return matches[0]


def validate_snapshot(snapshot: V5RunSnapshot) -> None:
    if not snapshot.output_hash_matches():
        raise ValueError(f"snapshot output hash mismatch for run_id: {snapshot.run_id}")
    claim_ids = [claim.claim_id for claim in snapshot.claims]
    duplicates = sorted(claim_id for claim_id, count in Counter(claim_ids).items() if count > 1)
    if duplicates:
        raise ValueError("duplicate claim_id in run snapshot: " + ", ".join(duplicates))


def build_feedback_draft(snapshot: V5RunSnapshot, claim_id: str) -> DomainClaimFeedback:
    """构造仍待人工填写的确定性反馈草稿。"""

    validate_snapshot(snapshot)
    claim = _find_claim(snapshot, claim_id)
    stable_claim_hash = claim_hash(claim)
    raw_id = f"{snapshot.run_id}|{claim_id}|{stable_claim_hash}"
    return DomainClaimFeedback(
        feedback_id="feedback-" + hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:16],
        case_id=snapshot.case_id,
        run_id=snapshot.run_id,
        snapshot_output_hash=snapshot.output_hash,
        claim_id=claim_id,
        claim_hash=stable_claim_hash,
    )


def validate_feedback(
    feedback: DomainClaimFeedback,
    snapshot: V5RunSnapshot,
    *,
    existing_feedback: Iterable[DomainClaimFeedback] = (),
) -> V5Claim:
    """失败关闭校验反馈绑定、taxonomy 和同命题 reviewer 唯一性。"""

    validate_snapshot(snapshot)
    if feedback.schema_version != DOMAIN_FEEDBACK_SCHEMA_VERSION:
        raise ValueError(f"unsupported feedback schema_version: {feedback.schema_version!r}")
    if feedback.status not in DOMAIN_FEEDBACK_STATUSES:
        raise ValueError(f"unsupported feedback status: {feedback.status!r}")
    if feedback.run_id != snapshot.run_id:
        raise ValueError(f"run_id mismatch: feedback={feedback.run_id!r} snapshot={snapshot.run_id!r}")
    if feedback.case_id != snapshot.case_id:
        raise ValueError(f"case_id mismatch: feedback={feedback.case_id!r} snapshot={snapshot.case_id!r}")
    if feedback.snapshot_output_hash != snapshot.output_hash:
        raise ValueError("snapshot output hash mismatch")
    claim = _find_claim(snapshot, feedback.claim_id)
    if feedback.claim_hash != claim_hash(claim):
        raise ValueError(f"claim hash mismatch for claim_id: {feedback.claim_id}")
    if not feedback.feedback_id.strip():
        raise ValueError("feedback_id is required")
    if not feedback.reviewer.strip():
        raise ValueError("reviewer is required")
    if not feedback.observed_at.strip():
        raise ValueError("observed_at is required")

    for existing in existing_feedback:
        if existing.feedback_id == feedback.feedback_id:
            raise ValueError(f"duplicate feedback_id: {feedback.feedback_id}")
        if (
            existing.run_id == feedback.run_id
            and existing.claim_id == feedback.claim_id
            and existing.reviewer == feedback.reviewer
        ):
            raise ValueError(
                "duplicate reviewer feedback for run/claim: "
                f"{feedback.reviewer} / {feedback.run_id} / {feedback.claim_id}"
            )
    return claim


def _snapshot_index(snapshots: Sequence[V5RunSnapshot]) -> dict[str, V5RunSnapshot]:
    index: dict[str, V5RunSnapshot] = {}
    for snapshot in snapshots:
        validate_snapshot(snapshot)
        previous = index.get(snapshot.run_id)
        if previous is not None and previous.hash() != snapshot.hash():
            raise ValueError(f"duplicate run_id has conflicting snapshots: {snapshot.run_id}")
        index[snapshot.run_id] = snapshot
    return index


def aggregate_calibration_candidates(
    feedback_rows: Sequence[DomainClaimFeedback],
    snapshots: Sequence[V5RunSnapshot],
) -> dict[str, Any]:
    """按 school/domain/task/claim_type 聚合只读候选，不执行 promotion。"""

    snapshots_by_run = _snapshot_index(snapshots)
    validated: list[tuple[DomainClaimFeedback, V5Claim]] = []
    seen: list[DomainClaimFeedback] = []
    for feedback in feedback_rows:
        snapshot = snapshots_by_run.get(feedback.run_id)
        if snapshot is None:
            raise ValueError(f"run snapshot not found for feedback run_id: {feedback.run_id}")
        claim = validate_feedback(feedback, snapshot, existing_feedback=seen)
        seen.append(feedback)
        validated.append((feedback, claim))

    groups: dict[tuple[str, str, str, str], list[tuple[DomainClaimFeedback, V5Claim]]] = defaultdict(list)
    for feedback, claim in validated:
        task = str(claim.metadata.get("task_id", "")).strip()
        identity = (claim.school, claim.domain, task, claim.claim_type)
        groups[identity].append((feedback, claim))

    candidates: list[dict[str, Any]] = []
    for identity, rows in sorted(groups.items()):
        school, domain, task, claim_type = identity
        counts = Counter(feedback.status for feedback, _ in rows)
        high_risk = task in HIGH_RISK_TASKS or any(bool(claim.metadata.get("high_risk")) for _, claim in rows)
        support_count = counts["accepted"]
        oppose_count = counts["rejected"]
        scored_count = support_count + oppose_count
        candidates.append(
            {
                "identity": {
                    "school": school,
                    "domain": domain,
                    "task": task,
                    "claim_type": claim_type,
                },
                "evidence_count": len(rows),
                "support_count": support_count,
                "oppose_count": oppose_count,
                "partial_count": counts["partial"],
                "unknown_count": counts["unknown"],
                "timing_deviation_count": counts["timing_deviation"],
                "scored_outcome_count": scored_count,
                "hit_rate": support_count / scored_count if scored_count else None,
                "risk_level": "high" if high_risk else "normal",
                "requires_human_review": high_risk,
                "promotion_allowed": False,
            }
        )
    return {
        "schema_version": CALIBRATION_CANDIDATES_SCHEMA_VERSION,
        "read_only": True,
        "automatic_promotion": False,
        "feedback_count": len(validated),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
