from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

_INITIAL_REVIEW_N_EFF = 5.0


def compute_gate_evidence(
    *,
    posteriors: Sequence[Mapping[str, Any] | object],
    incremental_gains: Mapping[str, Any],
    experiment_summary: Mapping[str, Any],
    high_risk_audit_summary: Mapping[str, Any],
    coverage_summary: Mapping[str, Any],
    gate_thresholds: Mapping[str, Any],
    provenance: Mapping[str, Any],
) -> dict[str, bool]:
    """Recompute derived gate evidence solely from persisted base facts."""
    required = {"coverage_complete", "calibration_min_samples", "calibration_max_error", "high_risk_min_utility"}
    if set(gate_thresholds) != required:
        return {}
    rows = [item if isinstance(item, Mapping) else item.to_dict() for item in posteriors]
    coverage = coverage_summary.get("coverage_by_identity", {})
    calibration_counts = coverage_summary.get("calibration_sample_count_by_identity", {})
    high_risk_tasks = high_risk_audit_summary.get("high_risk_task_ids", [])
    high_risk_utilities = high_risk_audit_summary.get("high_risk_utilities", [])
    provenance_valid = (
        all(isinstance(provenance.get(key), str) and provenance[key] for key in ("manifest_digest", "task_catalog", "rule_snapshot", "freeze_hash"))
        and str(provenance["manifest_digest"]).startswith("sha256:")
        and "@sha256:" in str(provenance["task_catalog"])
        and "@sha256:" in str(provenance["rule_snapshot"])
        and len(str(provenance["freeze_hash"])) == 64
    )
    return {
        "coverage_complete": bool(coverage) and all(float(value) >= float(gate_thresholds["coverage_complete"]) for value in coverage.values()),
        "calibration_acceptable": bool(calibration_counts) and all(int(count) >= int(gate_thresholds["calibration_min_samples"]) for count in calibration_counts.values()) and all(item.get("calibration_error") is not None and float(item["calibration_error"]) <= float(gate_thresholds["calibration_max_error"]) for item in rows),
        "incremental_non_negative": bool(incremental_gains) and all(float(value) >= 0.0 for value in incremental_gains.values()),
        "high_risk_safe": bool(high_risk_tasks) and int(high_risk_audit_summary.get("high_risk_unassessable_count", 0)) == 0 and bool(high_risk_utilities) and all(float(value) >= float(gate_thresholds["high_risk_min_utility"]) for value in high_risk_utilities),
        "provenance_valid": provenance_valid,
    }


def _number(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_capability_report(
    manifest_summary: Mapping[str, int],
    experiment_summary: Mapping[str, Any],
    posteriors: Sequence[Mapping[str, Any] | object],
    *,
    gate_evidence: Mapping[str, bool] | None = None,
) -> str:
    """Render a cautious baseline view; it never promotes production expertise."""
    posterior_rows = [item if isinstance(item, Mapping) else item.to_dict() for item in posteriors]
    all_below_threshold = all(float(item.get("n_eff", 0.0)) < _INITIAL_REVIEW_N_EFF for item in posterior_rows)
    required_gate_keys = {"coverage_complete", "calibration_acceptable", "incremental_non_negative", "high_risk_safe", "provenance_valid"}
    complete_gate = gate_evidence is not None and set(gate_evidence) == required_gate_keys and all(type(value) is bool for value in gate_evidence.values())
    if complete_gate and gate_evidence["incremental_non_negative"] is False and all(gate_evidence[key] for key in required_gate_keys - {"incremental_non_negative"}):
        recommendation = "STOP"
    elif not all_below_threshold and complete_gate and all(gate_evidence.values()):
        recommendation = "READY_FOR_MANUAL_REVIEW"
    else:
        recommendation = "HOLD"
    manifest_lines = [f"- {name}: {count}" for name, count in sorted(manifest_summary.items())] or ["- 无案例记录"]
    experiment_lines: list[str] = []
    for group, summary in sorted(experiment_summary.items()):
        if isinstance(summary, Mapping):
            rendered = ", ".join(f"{key}={_number(value)}" for key, value in sorted(summary.items()))
        else:
            rendered = _number(summary)
        experiment_lines.append(f"- {group}: {rendered}")
    if not experiment_lines:
        experiment_lines.append("- 尚无可发布的实验结果")
    posterior_lines = [
        "- {school}/{task}: coverage={coverage}, discrimination={discrimination}, "
        "accuracy={accuracy}, calibration={calibration}, incremental_gain={gain}, "
        "posterior={mean}, interval=[{low}, {high}], N_eff={n_eff}, evidence={grade}".format(
            school=item.get("school_id", "unknown"), task=item.get("task_id", "unknown"),
            coverage=_number(item.get("coverage_rate", "n/a")),
            discrimination=_number(item.get("discrimination_score", "n/a")),
            accuracy=_number(item.get("accuracy_score", "n/a")),
            calibration=_number(item.get("calibration_error", "n/a")),
            gain=_number(item.get("incremental_gain", "n/a")),
            mean=_number(item.get("posterior_mean", "n/a")),
            low=_number(item.get("credible_interval", ["n/a", "n/a"])[0]),
            high=_number(item.get("credible_interval", ["n/a", "n/a"])[1]),
            n_eff=_number(item.get("n_eff", 0.0)), grade=item.get("evidence_grade", "unknown"),
        ) for item in posterior_rows
    ] or ["- 尚无条件化后验"]
    return "\n".join([
        "# 学派能力暂定能力基线",
        "",
        "## 1. 评估范围与证据等级",
        "本报告区分弱先验、历史盲评证据与未来前瞻证据；当前结果仅是可复核基线。",
        "",
        "## 2. 案例可用性与污染盘点",
        *manifest_lines,
        "",
        "## 3. 任务覆盖与三态输出",
        "输出状态为 claim / abstain / unsupported；缺失输出不得视为错误预测。",
        "",
        "## 4. 六维条件切片下的五维能力基线",
        "在 school / task / chart prototype / claim type / time horizon / evidence completeness 六维条件切片下，按覆盖、区分度、准确度、校准与增量收益五个能力指标观察，不合成为生产权重。",
        "详细后验仅在下一节展示，避免重复发布。",
        "",
        "## 5. 四组增量实验",
        *experiment_lines,
        "",
        "## 6. 条件化能力后验",
        *posterior_lines,
        "",
        "## 7. 校准与高风险误差",
        "高风险误报需单独审查；低样本校准值不得外推。",
        "",
        "## 8. 样本与证据限制",
        "历史报告、已知反馈与规则开发材料可能造成标签泄漏；污染案例不得作为盲评证据。",
        "初始样本不能证明稳定专长，结论必须由独立前瞻样本证伪或复现。",
        "",
        "## 9. 评估门禁建议",
        f"**{recommendation}**",
        "缺少完整、显式、可复核的 gate evidence 时一律 HOLD；正式出口仅允许人工复核、停止或保持。",
        "",
    ])
