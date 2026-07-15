"""生成 L1 learned/static 严格无泄漏留出审计制品。

兼容旧 historical batch/scores 双文件，也可只读适配 Task 8 的
``six-month-capability-baseline/v1``。适配不会重跑预测、读取反馈或重新评分。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable, Mapping

import yaml

from engine.decision.real_routing_evaluator import build_training_capability_snapshot
from engine.decision.routing_holdout_artifacts import (
    audit_competitive_coverage,
    build_deterministic_case_split,
    compare_static_learned_routes,
    rewrite_score_prototypes,
)
from tools.school_capability_batch import parse_case_summary_with_audit

OLD_BATCH_SCHEMA = "school-capability-historical-batch/v1"
OLD_SCORES_SCHEMA = "school-capability-historical-scores/v1"
TASK8_SCHEMA = "six-month-capability-baseline/v1"
AUDIT_SCHEMA = "l1-routing-holdout-audit/v2"
DEFAULT_STATIC_COVERAGE = Path("mapping/school-capability-runner-coverage-v1.yaml")


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _verify_content_digest(document: Mapping[str, Any]) -> str:
    unsigned = dict(document)
    claimed = unsigned.pop("artifact_digest", None)
    actual = f"sha256:{_canonical_digest(unsigned)}"
    if claimed != actual:
        raise ValueError("Task 8 artifact digest mismatch")
    return actual


def _normalize_case_facts(cases: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in cases:
        case_id = str(raw.get("case_id", ""))
        pillars = raw.get("four_pillars")
        sex = str(raw.get("sex_marker", ""))
        if not case_id or case_id in seen or sex not in {"乾", "坤"}:
            raise ValueError("Task 8 路由审计输入不完整：case identity 不可信")
        if not isinstance(pillars, (list, tuple)) or len(pillars) != 4 or not all(str(item) for item in pillars):
            raise ValueError(f"Task 8 路由审计输入不完整：{case_id} 缺少 sex_marker + four_pillars")
        seen.add(case_id)
        normalized.append({
            "case_id": case_id,
            "sex_marker": sex,
            "four_pillars": [str(item) for item in pillars],
            "solar_datetime": str(raw.get("solar_datetime", "")),
            "dayun_sequence": [
                str(item.get("ganzhi", "")) if isinstance(item, Mapping) else str(item)
                for item in raw.get("dayun_sequence", raw.get("dayun_steps", ()))
                if (item.get("ganzhi") if isinstance(item, Mapping) else item)
            ],
        })
    return normalized


def adapt_six_month_baseline(
    baseline: Mapping[str, Any],
    frozen_cases: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """把 Task 8 最终制品安全适配为旧审计接口，不伪造原 schema 身份。"""
    if baseline.get("schema_version") != TASK8_SCHEMA:
        raise ValueError("invalid six-month baseline schema")
    _verify_content_digest(baseline)
    if baseline.get("classification") != "historical_blind_candidate":
        raise ValueError("Task 8 baseline classification is not historical_blind_candidate")
    freeze_hash = str(baseline.get("freeze_hash", ""))
    provenance = baseline.get("provenance")
    if not freeze_hash or not isinstance(provenance, Mapping) or provenance.get("freeze_hash") != freeze_hash:
        raise ValueError("Task 8 freeze identity mismatch")
    score_rows = baseline.get("scores")
    if not isinstance(score_rows, list):
        raise ValueError("Task 8 baseline scores are missing")

    cases = _normalize_case_facts(frozen_cases)
    case_map = {row["case_id"]: row for row in cases}
    score_case_ids = {str(row.get("case_id", "")) for row in score_rows if isinstance(row, Mapping)}
    missing = sorted(score_case_ids - set(case_map))
    if missing:
        raise ValueError(f"Task 8 路由审计输入不完整：缺少冻结 case facts：{missing[0]}")
    selected_cases = [case_map[case_id] for case_id in sorted(score_case_ids)]
    if not selected_cases:
        raise ValueError("Task 8 路由审计输入不完整：没有评分案例")

    # adapter_origin 明确记录这是内存接口适配，不篡改 Task 8 原 schema_version。
    batch = {
        "schema_version": OLD_BATCH_SCHEMA,
        "classification": "historical_blind_candidate",
        "adapter_origin": TASK8_SCHEMA,
        "cases": selected_cases,
        "frozen_run": {"freeze_hash": freeze_hash},
    }
    scores = {
        "schema_version": OLD_SCORES_SCHEMA,
        "adapter_origin": TASK8_SCHEMA,
        "freeze_hash": freeze_hash,
        "scores": [dict(row) for row in score_rows],
    }
    return batch, scores


def load_static_school_by_task(path: Path, task_ids: Iterable[str]) -> dict[str, str]:
    """从 Task 1 冻结 expert-authored coverage 的主力顺序读取静态基线。"""
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping) or document.get("schema_version") != "school-capability-runner-coverage/v1":
        raise ValueError("invalid static coverage schema")
    wanted = set(task_ids)
    result: dict[str, str] = {}
    for row in document.get("coverage", ()):
        if not isinstance(row, Mapping):
            continue
        task_id = str(row.get("task_id", ""))
        primary = row.get("primary_schools")
        if task_id in wanted and isinstance(primary, list) and primary:
            result[task_id] = str(primary[0])
    return dict(sorted(result.items()))


def _competitive_details(
    rows: Iterable[Mapping[str, Any]], holdout_ids: set[str],
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        case_id = str(row.get("case_id", ""))
        if case_id in holdout_ids and row.get("utility") is not None:
            grouped[(case_id, str(row.get("task_id", "")))].add(str(row.get("school_id", "")))
    identities = [
        {"case_id": case_id, "task_id": task_id, "schools": sorted(schools)}
        for (case_id, task_id), schools in sorted(grouped.items()) if len(schools) >= 2
    ]
    by_task = Counter(row["task_id"] for row in identities)
    return dict(sorted(by_task.items())), identities


def _label_distribution(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        if row.get("utility") is None:
            continue
        value = row.get("observed_positive")
        label = "positive" if value is True else "negative" if value is False else "other"
        counters[str(row.get("task_id", ""))][label] += 1
    return {
        task: {"positive": counts["positive"], "negative": counts["negative"], "other": counts["other"]}
        for task, counts in sorted(counters.items())
    }


def _calibration_audit(records: Iterable[Any], lookup: Mapping[tuple[str, str, str], Mapping[str, Any]]) -> dict[str, Any]:
    static_errors: list[float] = []
    learned_errors: list[float] = []
    labels: set[bool] = set()
    for record in records:
        static = lookup[(record.case_id, record.task_id, record.static_school)]
        learned = lookup[(record.case_id, record.task_id, record.learned_school)]
        observed = static.get("observed_positive")
        if observed not in {True, False} or static.get("probability_score") is None or learned.get("probability_score") is None:
            continue
        target = 1.0 if observed else 0.0
        labels.add(bool(observed))
        static_errors.append((float(static["probability_score"]) - target) ** 2)
        learned_errors.append((float(learned["probability_score"]) - target) ** 2)
    sufficient = len(static_errors) >= 5 and len(labels) >= 2
    static_error = fmean(static_errors) if static_errors else None
    learned_error = fmean(learned_errors) if learned_errors else None
    return {
        "status": "sufficient" if sufficient else "insufficient",
        "sample_count": len(static_errors),
        "static_brier": static_error,
        "learned_brier": learned_error,
        "worsened": bool(sufficient and learned_error is not None and static_error is not None and learned_error > static_error),
    }


def _high_risk_audit(records: Iterable[Any], high_risk_task_ids: set[str]) -> dict[str, Any]:
    selected = [row for row in records if row.task_id in high_risk_task_ids]
    static_fp = sum(row.static_utility < 0 for row in selected)
    learned_fp = sum(row.learned_utility < 0 for row in selected)
    return {
        "task_ids": sorted(high_risk_task_ids),
        "assessable_record_count": len(selected),
        "static_false_positive_count": static_fp,
        "learned_false_positive_count": learned_fp,
        "false_positives_increased": learned_fp > static_fp,
        "status": "sufficient" if selected else "insufficient",
    }


def _prototype_evidence(records: Iterable[Any], prototype_by_case: Mapping[str, str]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for row in records:
        grouped[(row.task_id, prototype_by_case[row.case_id])].append(row)
    evidence: list[dict[str, Any]] = []
    for (task, prototype), values in sorted(grouped.items()):
        changed = [row for row in values if row.static_school != row.learned_school]
        labels = len(values)
        if len(changed) >= 2:
            evidence.append({
                "task_id": task,
                "chart_prototype_id": prototype,
                "record_count": labels,
                "selection_change_count": len(changed),
                "static_mean_utility": fmean(row.static_utility for row in values),
                "learned_mean_utility": fmean(row.learned_utility for row in values),
            })
    return evidence


def build_audit_artifact(
    batch: dict[str, Any],
    scores: dict[str, Any],
    *,
    holdout_fraction: float,
    salt: str,
    minimum_competitive_cases: int,
    static_school_by_task: Mapping[str, str] | None = None,
    static_baseline_source: str = "legacy explicit static mapping",
    source_baseline: str = "legacy historical batch/scores",
    source_artifact_digest: str | None = None,
    classification: str | None = None,
    generated_at: str | None = None,
    high_risk_task_ids: set[str] | None = None,
) -> dict[str, Any]:
    if batch.get("schema_version") != OLD_BATCH_SCHEMA:
        raise ValueError("invalid historical batch schema")
    if scores.get("schema_version") != OLD_SCORES_SCHEMA:
        raise ValueError("invalid historical scores schema")
    if batch["frozen_run"]["freeze_hash"] != scores.get("freeze_hash"):
        raise ValueError("batch/scores freeze_hash mismatch")

    rows = scores.get("scores", [])
    labelled_ids = {str(row["case_id"]) for row in rows if row.get("utility") is not None}
    eligible_cases = [row for row in batch["cases"] if row["case_id"] in labelled_ids]
    split = build_deterministic_case_split(eligible_cases, holdout_fraction=holdout_fraction, salt=salt)
    training_ids = set(split.training_case_ids)
    holdout_ids = set(split.holdout_case_ids)
    if training_ids & holdout_ids:
        raise ValueError("training/holdout leakage detected")

    rewritten = rewrite_score_prototypes(rows, batch["cases"])
    static_map = dict(sorted((static_school_by_task or {"career.role_change": "ziping"}).items()))
    # 没有任何真实可评分行的任务不可进入比较。
    scored_school_tasks = {(str(row["task_id"]), str(row["school_id"])) for row in rewritten if row.get("utility") is not None}
    static_map = {task: school for task, school in static_map.items() if (task, school) in scored_school_tasks}

    coverage = audit_competitive_coverage(
        rewritten, holdout_case_ids=holdout_ids, minimum_competitive_cases=minimum_competitive_cases,
    )
    competitive_by_task, competitive_identities = _competitive_details(rewritten, holdout_ids)
    comparison = compare_static_learned_routes(
        rewritten,
        training_case_ids=training_ids,
        holdout_case_ids=holdout_ids,
        static_school_by_task=static_map,
        minimum_holdout_cases=minimum_competitive_cases,
    )
    prototype_by_case = {
        row["case_id"]: row["chart_prototype_id"] for row in rewritten if row["case_id"] in labelled_ids
    }
    snapshot = build_training_capability_snapshot(
        batch=batch,
        score_rows=rewritten,
        training_case_ids=training_ids,
        evaluated_at=generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    lookup = {
        (str(row["case_id"]), str(row["task_id"]), str(row["school_id"])): row
        for row in rewritten if row.get("utility") is not None
    }
    calibration = _calibration_audit(comparison.records, lookup)
    high_risk = _high_risk_audit(comparison.records, high_risk_task_ids or set())
    labels = _label_distribution(row for row in rewritten if row["case_id"] in holdout_ids)
    prototype_evidence = _prototype_evidence(comparison.records, prototype_by_case)
    selection_changes = sum(row.static_school != row.learned_school for row in comparison.records)
    route_records = [row.__dict__ for row in comparison.records]

    reasons = [*coverage.reasons, *comparison.reasons]
    single_class_tasks = [task for task, counts in labels.items() if not counts["positive"] or not counts["negative"]]
    stop_reasons: list[str] = []
    hold_reasons: list[str] = []
    if comparison.status == "STOP":
        stop_reasons.extend(comparison.reasons)
    if calibration["worsened"]:
        stop_reasons.append("校准误差在留出集显著恶化。")
    if high_risk["false_positives_increased"]:
        stop_reasons.append("高风险假阳性增加。")
    if coverage.status != "READY":
        hold_reasons.extend(coverage.reasons)
    if selection_changes == 0:
        hold_reasons.append("learned 与 static 选择完全相同。")
    if single_class_tasks:
        hold_reasons.append(f"留出标签缺少正负例或为单一类别：{', '.join(single_class_tasks)}。")
    if calibration["status"] == "insufficient":
        hold_reasons.append("校准样本不足，calibration_status=insufficient。")
    if high_risk["status"] == "insufficient":
        hold_reasons.append("高风险任务不可评估。")
    if not prototype_evidence:
        hold_reasons.append("没有 task × prototype 稳定增量证据。")
    if classification != "historical_blind_candidate":
        hold_reasons.append("证据属性未确认为 historical_blind_candidate。")

    gate_status = "STOP" if stop_reasons else "HOLD" if hold_reasons else "GO"
    gate_reasons = list(dict.fromkeys([*stop_reasons, *hold_reasons, *reasons]))
    payload: dict[str, Any] = {
        "schema_version": AUDIT_SCHEMA,
        "source_baseline": source_baseline,
        "source_freeze_hash": scores["freeze_hash"],
        "source_artifact_digest": source_artifact_digest,
        "classification": classification or batch.get("classification", "historical_blind_candidate"),
        "split": {
            "salt": split.salt,
            "holdout_fraction": split.holdout_fraction,
            "subject_identity": "sex_marker + four_pillars",
            "training_case_ids": list(split.training_case_ids),
            "holdout_case_ids": list(split.holdout_case_ids),
        },
        "static_baseline_source": static_baseline_source,
        "static_school_by_task": static_map,
        "training_capability_snapshot_id": snapshot["snapshot_id"],
        "training_capability_snapshot": {**snapshot, "source_freeze_hash": scores["freeze_hash"]},
        "prototype_by_case": dict(sorted(prototype_by_case.items())),
        "competitive_coverage": {
            "status": coverage.status,
            "holdout_subject_count": len(split.holdout_case_ids),
            "holdout_case_count": coverage.holdout_case_count,
            "scored_case_task_count": coverage.scored_case_task_count,
            "competitive_case_task_count": coverage.competitive_case_task_count,
            "competitive_by_task": competitive_by_task,
            "competitive_identities": competitive_identities,
            "reasons": list(coverage.reasons),
        },
        "route_comparison": {
            "status": comparison.status,
            "record_count": len(comparison.records),
            "selection_changes": selection_changes,
            "records": route_records,
            "static_mean_utility": comparison.static_mean_utility,
            "learned_mean_utility": comparison.learned_mean_utility,
            "reasons": list(comparison.reasons),
        },
        "calibration_audit": calibration,
        "high_risk_audit": high_risk,
        "label_distribution_by_task": labels,
        "single_class_tasks": single_class_tasks,
        "prototype_incremental_evidence": prototype_evidence,
        "gate_status": gate_status,
        "gate_reasons": gate_reasons,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    payload["artifact_digest"] = f"sha256:{_canonical_digest(payload)}"
    return payload


def render_audit_report(artifact: Mapping[str, Any]) -> str:
    split = artifact["split"]
    coverage = artifact["competitive_coverage"]
    comparison = artifact["route_comparison"]
    calibration = artifact["calibration_audit"]
    high_risk = artifact["high_risk_audit"]
    static_lines = [f"| {task} | {school} |" for task, school in artifact["static_school_by_task"].items()]
    coverage_lines = [f"| {task} | {count} |" for task, count in coverage["competitive_by_task"].items()]
    route_lines = [
        f"| {row['case_id']} | {row['task_id']} | {row['static_school']} | {row['learned_school']} | {row['static_utility']:.4f} | {row['learned_utility']:.4f} |"
        for row in comparison["records"]
    ]
    label_lines = [
        f"| {task} | {counts['positive']} | {counts['negative']} | {counts['other']} |"
        for task, counts in artifact["label_distribution_by_task"].items()
    ]
    return "\n".join([
        "# L1 可学习路由留出集对照",
        "",
        f"**门禁结论：{artifact['gate_status']}**",
        "",
        "## 来源与证据等级",
        f"- Task 8 制品：`{artifact['source_baseline']}`",
        f"- freeze hash：`{artifact['source_freeze_hash']}`",
        f"- artifact digest：`{artifact['source_artifact_digest']}`",
        "- 数据证据等级：historical blind candidate；不是 prospective/E3。",
        f"- 本审计摘要：`{artifact['artifact_digest']}`",
        "",
        "## 无泄漏 subject 切分",
        f"- subject identity：`{split['subject_identity']}`",
        f"- 训练案例：{len(split['training_case_ids'])}",
        f"- 留出案例：{len(split['holdout_case_ids'])}",
        f"- holdout fraction：{split['holdout_fraction']}",
        f"- 固定切分盐：`{split['salt']}`",
        f"- 训练能力快照：`{artifact['training_capability_snapshot_id']}`，仅由训练 case IDs 构造并绑定 Task 8 freeze hash。",
        "",
        "## static baseline 来源与映射",
        f"来源：`{artifact['static_baseline_source']}`。映射不是 learned 训练结果反写。",
        "",
        "| 任务 | static school |", "|---|---|", *(static_lines or ["| — | — |"]),
        "",
        "## 按任务竞争覆盖",
        f"- 留出可评分 case/task：{coverage['scored_case_task_count']}",
        f"- 多派竞争 case/task：{coverage['competitive_case_task_count']}（最低门槛 5）",
        "- claim 与有标签、按协议产生 utility 的 abstain 可参与；unsupported / utility=None 不参与。",
        "",
        "| 任务 | 多派竞争数 |", "|---|---:|", *(coverage_lines or ["| — | 0 |"]),
        "",
        "## learned/static 选择与留出效用",
        f"- 可比较记录：{comparison['record_count']}",
        f"- 选择变化：{comparison['selection_changes']}",
        f"- static 平均效用：{comparison['static_mean_utility']:.4f}",
        f"- learned 平均效用：{comparison['learned_mean_utility']:.4f}",
        "",
        "| case | task | static | learned | static utility | learned utility |", "|---|---|---|---|---:|---:|", *(route_lines or ["| — | — | — | — | — | — |"]),
        "",
        "## 标签分布",
        "| 任务 | 正例 | 负例 | 其他类别 |", "|---|---:|---:|---:|", *(label_lines or ["| — | 0 | 0 | 0 |"]),
        "",
        "## 校准与高风险检查",
        f"- calibration status：`{calibration['status']}`；样本数 {calibration['sample_count']}；static/learned Brier：{calibration['static_brier']} / {calibration['learned_brier']}。",
        f"- 高风险 status：`{high_risk['status']}`；可评估记录 {high_risk['assessable_record_count']}；static/learned 假阳性 {high_risk['static_false_positive_count']} / {high_risk['learned_false_positive_count']}。",
        f"- task × prototype 稳定增量切片：{len(artifact['prototype_incremental_evidence'])}。",
        "",
        "## 门禁依据",
        *(f"- {reason}" for reason in artifact["gate_reasons"]),
        "",
        "## 治理结论",
        f"结论为 **{artifact['gate_status']}**。本审计不修改 `routing_mode`、默认路由、生产权重、runner、规则或评分算法。",
        "",
    ])


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


def _cases_from_source(path: Path) -> list[dict[str, Any]]:
    audit = parse_case_summary_with_audit(path)
    return [
        {"case_id": row.case_id, "sex_marker": row.sex_marker, "four_pillars": list(row.four_pillars),
         "solar_datetime": row.solar_datetime, "dayun_sequence": list(row.dayun_sequence)}
        for row in audit.cases
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--baseline", type=Path)
    source.add_argument("--batch", type=Path)
    parser.add_argument("--scores", type=Path)
    parser.add_argument("--frozen-input", type=Path)
    parser.add_argument("--static-coverage", type=Path, default=DEFAULT_STATIC_COVERAGE)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--holdout-fraction", type=float, default=0.25)
    parser.add_argument("--salt", default="six-month-l1-routing-v1")
    parser.add_argument("--minimum-competitive-cases", type=int, default=5)
    parser.add_argument("--generated-at")
    args = parser.parse_args()

    source_digest: str | None = None
    classification = "historical_blind_candidate"
    if args.baseline:
        baseline = _read_json(args.baseline)
        provenance = baseline.get("provenance", {})
        frozen_path = args.frozen_input or Path(str(provenance.get("historical_input", "")))
        if not frozen_path.is_file():
            raise ValueError("Task 8 路由审计输入不完整：找不到 provenance 冻结历史输入")
        batch, scores = adapt_six_month_baseline(baseline, _cases_from_source(frozen_path))
        source_baseline = args.baseline.as_posix()
        source_digest = str(baseline.get("artifact_digest"))
        task_ids = baseline.get("task_ids", ())
    else:
        if args.scores is None:
            parser.error("--scores is required with --batch")
        batch, scores = _read_json(args.batch), _read_json(args.scores)
        source_baseline = f"{args.batch.as_posix()} + {args.scores.as_posix()}"
        task_ids = {row.get("task_id") for row in scores.get("scores", ())}
        classification = str(batch.get("classification", classification))

    coverage_doc = yaml.safe_load(args.static_coverage.read_text(encoding="utf-8"))
    high_risk_tasks = {
        str(row["task_id"]) for row in coverage_doc.get("coverage", ())
        if isinstance(row, Mapping) and row.get("high_risk")
    }
    static_map = load_static_school_by_task(args.static_coverage, task_ids)
    artifact = build_audit_artifact(
        batch, scores,
        holdout_fraction=args.holdout_fraction,
        salt=args.salt,
        minimum_competitive_cases=args.minimum_competitive_cases,
        static_school_by_task=static_map,
        static_baseline_source=args.static_coverage.as_posix(),
        source_baseline=source_baseline,
        source_artifact_digest=source_digest,
        classification=classification,
        generated_at=args.generated_at,
        high_risk_task_ids=high_risk_tasks,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(render_audit_report(artifact), encoding="utf-8")
    print(json.dumps({"status": artifact["gate_status"], "out": str(args.out), "report": str(args.report)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
