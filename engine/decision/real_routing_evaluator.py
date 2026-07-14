"""真实 L1 评估辅助：仅从训练集重建正式原型能力后验。"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping

from engine.decision.routing_holdout_artifacts import rewrite_score_prototypes
from engine.evaluation.capability import build_capability_posteriors
from engine.evaluation.models import ScoreRecord


def build_training_capability_snapshot(
    *,
    batch: Mapping[str, Any],
    score_rows: Iterable[Mapping[str, Any]],
    training_case_ids: set[str] | frozenset[str],
    evaluated_at: str,
) -> dict[str, Any]:
    """排除留出案后，以 cfv-v1 正式原型重建六维 CapabilityPosterior。"""
    rewritten = rewrite_score_prototypes(score_rows, batch["cases"])
    training_rows = [row for row in rewritten if row["case_id"] in training_case_ids]
    probability_rows = [
        ScoreRecord.from_dict(row)
        for row in training_rows
        if row.get("probability_score") is not None
    ]
    eligible: dict[tuple[str, str, str, str, str, str], set[str]] = {}
    probability_map: dict[tuple[str, str, str], float] = {}
    for row in probability_rows:
        identity = (
            row.school_id, row.task_id, row.chart_prototype_id,
            row.claim_type, row.time_horizon, row.evidence_completeness_band,
        )
        eligible.setdefault(identity, set()).add(row.case_id)
        probability_map[(row.case_id, row.task_id, row.school_id)] = 0.65
    posteriors = build_capability_posteriors(
        probability_rows,
        "B",
        evaluated_at,
        claim_probabilities=probability_map,
        eligible_case_ids=eligible,
    ) if probability_rows else []
    ids = sorted(training_case_ids)
    digest = hashlib.sha256(json.dumps(ids, ensure_ascii=False).encode("utf-8")).hexdigest()[:20]
    return {
        "schema_version": "l1-training-capability-snapshot/v1",
        "snapshot_id": f"cap-train-{digest}",
        "training_case_ids": ids,
        "evaluated_at": evaluated_at,
        "posteriors": [row.to_dict() for row in posteriors],
    }
