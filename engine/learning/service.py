"""L9 条件化学习编排与 L1 capability snapshot 回流。"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Iterable, Mapping

import yaml

from engine.evaluation.models import CapabilityPosterior
from engine.learning.governance import decide_learning_tier
from engine.learning.models import (
    ConditionalIdentity,
    ConditionalLearningSignal,
    LearningDecision,
    LearningThresholds,
    ManualReviewItem,
)
from engine.learning.repository import ConditionalLearningRepository


def _load_task_risks(path: str | Path) -> dict[str, bool]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("tasks"), list):
        raise ValueError("task catalog requires tasks array")
    risks: dict[str, bool] = {}
    for index, row in enumerate(raw["tasks"]):
        if not isinstance(row, dict) or not isinstance(row.get("task_id"), str):
            raise ValueError(f"invalid task catalog row {index}")
        task_id = row["task_id"]
        if task_id in risks:
            raise ValueError(f"duplicate task_id in catalog: {task_id}")
        risks[task_id] = bool(row.get("high_risk", False))
    return risks


def _identity_key(row: Mapping[str, object]) -> str:
    return ConditionalIdentity(
        school_id=str(row["school_id"]),
        task_id=str(row["task_id"]),
        chart_prototype_id=str(row["chart_prototype_id"]),
        claim_type=str(row["claim_type"]),
        time_horizon=str(row["time_horizon"]),
        evidence_completeness_band=str(row["evidence_completeness_band"]),
    ).key


def _posterior_rows(repository: ConditionalLearningRepository) -> dict[str, dict[str, object]]:
    active = repository.load_active_snapshot()
    if active is None:
        return {}
    rows: dict[str, dict[str, object]] = {}
    for row in active["posteriors"]:
        key = _identity_key(row)
        if key in rows:
            raise ValueError(f"duplicate posterior identity in active snapshot: {key}")
        rows[key] = dict(row)
    return rows


def _current_posterior(row: Mapping[str, object] | None) -> CapabilityPosterior | None:
    return None if row is None else CapabilityPosterior.from_dict(dict(row))


def _updated_posterior(
    identity: ConditionalIdentity,
    decision: LearningDecision,
    current: CapabilityPosterior | None,
    created_at: str,
) -> dict[str, object]:
    coverage = 0.0 if current is None else current.coverage_rate
    discrimination = 0.0 if current is None else current.discrimination_score
    calibration = None if current is None else current.calibration_error
    gain = 0.0 if current is None else current.incremental_gain
    evidence_grade = "E1" if current is None else current.evidence_grade
    return CapabilityPosterior(
        **identity.to_dict(),
        coverage_rate=coverage,
        discrimination_score=discrimination,
        accuracy_score=decision.proposed_posterior_mean,
        calibration_error=calibration,
        posterior_mean=decision.proposed_posterior_mean,
        credible_interval=decision.proposed_credible_interval,
        n_eff=decision.n_eff_after,
        evidence_grade=evidence_grade,
        last_evaluated_at=created_at,
        incremental_gain=gain,
    ).to_dict()


def _record_reviews(
    repository: ConditionalLearningRepository,
    signal: ConditionalLearningSignal,
    decision: LearningDecision,
) -> None:
    reasons = tuple(decision.audit.get("review_reasons", ()))
    if decision.requires_human_approval and not reasons:
        reasons = ("mature_rule_prior",)
    for reason in reasons:
        repository.record_review(
            ManualReviewItem(
                review_id=f"review-{decision.decision_id.removeprefix('decision-')}-{reason}",
                signal_id=signal.signal_id,
                decision_id=decision.decision_id,
                reason=str(reason),
                target_identity=signal.identity,
                context={
                    "update_tier": decision.update_tier,
                    "n_eff_before": decision.n_eff_before,
                    "n_eff_after": decision.n_eff_after,
                },
            )
        )


def process_learning_signals(
    signals: Iterable[ConditionalLearningSignal],
    *,
    repository: ConditionalLearningRepository,
    thresholds: LearningThresholds,
    task_catalog_path: str | Path,
    approval_decision_ids: set[str] | frozenset[str] = frozenset(),
    created_at: str,
) -> tuple[LearningDecision, ...]:
    """顺序治理信号，仅向独立 L9 repository 写审计与 L1 兼容快照。"""

    task_risks = _load_task_risks(task_catalog_path)
    rows = _posterior_rows(repository)
    decisions: list[LearningDecision] = []
    rule_prior_proposals: list[dict[str, object]] = []

    for signal in signals:
        if signal.identity.task_id not in task_risks:
            raise ValueError(f"task_id not found in task catalog: {signal.identity.task_id}")
        repository.record_signal(signal)
        current_row = rows.get(signal.identity.key)
        current = _current_posterior(current_row)
        proposed = decide_learning_tier(
            signal,
            current,
            thresholds,
            is_high_risk=task_risks[signal.identity.task_id],
        )
        approved = proposed.decision_id in approval_decision_ids
        should_apply = proposed.applied or (proposed.requires_human_approval and approved)

        snapshot_ref: str | None = None
        if should_apply and proposed.update_tier in {"adjust_applicability", "adjust_rule_prior"}:
            rows[signal.identity.key] = _updated_posterior(
                signal.identity, proposed, current, created_at
            )
            if proposed.update_tier == "adjust_rule_prior":
                rule_prior_proposals.append(
                    {
                        "decision_id": proposed.decision_id,
                        "rule_id": signal.rule_id,
                        "identity": signal.identity.to_dict(),
                        "proposed_delta": proposed.proposed_delta,
                        "approved": True,
                    }
                )
            parent = repository.active_snapshot_ref()
            snapshot_ref = repository.freeze_snapshot(
                posteriors=[rows[key] for key in sorted(rows)],
                parent_snapshot_ref=parent,
                decision_ids=[proposed.decision_id],
                created_at=created_at,
                rule_prior_proposals=rule_prior_proposals,
            )
            repository.apply_snapshot(snapshot_ref)

        final = replace(proposed, applied=should_apply, snapshot_ref=snapshot_ref)
        repository.record_decision(final)
        _record_reviews(repository, signal, final)
        decisions.append(final)

    return tuple(decisions)
