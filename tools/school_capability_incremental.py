"""Build an isolated incremental historical-blind capability batch.

The workflow deliberately separates chart-only preparation/Stage A from the
feedback reveal in Stage B.  It never changes runners, production routing, or
weights.  High-risk labels are never emitted by this historical feedback
extractor because this batch has no independent A-grade dual review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from engine.evaluation.freeze import freeze_outputs, verify_frozen_run
from engine.evaluation.manifest_validation import GATE_THRESHOLDS_POLICY
from engine.evaluation.models import BlindSchoolOutput, BlindTask, FrozenBlindRun
from tools.school_capability_batch import (
    ProspectiveCase,
    parse_case_summary_with_audit,
    parse_feedback_labels,
)
from tools.school_capability_task8 import (
    APPROVED_SCHOOLS,
    APPROVED_TASK_IDS,
    build_final_baseline,
    build_stage_a,
    build_stage_b_inputs,
    canonical_digest,
    render_final_markdown,
    score_stage_b,
)

CLASSIFICATION = "historical_blind_candidate"
SCHEMA = "school-capability-increment-audit/v1"
HIGH_RISK_TASK_IDS = {
    "marriage.divorce_or_remarriage",
    "wealth.debt",
    "health.system_risk",
    "health.event_window",
    "wealth.major_loss_window",
}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _subject_from_case_id(case_id: str) -> tuple[str, str]:
    parts = case_id.split("-")
    if len(parts) != 5 or parts[3] not in {"乾", "坤"} or not parts[4]:
        raise ValueError(f"invalid canonical case_id: {case_id}")
    return parts[3], parts[4]


def _isolated_markdown(cases: list[ProspectiveCase]) -> str:
    blocks = []
    for case in cases:
        lines = [
            f"## {case.case_id[:10]} · {case.sex_marker} · {''.join(case.four_pillars)}",
            f"- 公历生日：{case.solar_datetime}",
            f"- 四柱：{' '.join(case.four_pillars)}",
        ]
        if case.dayun_sequence:
            lines.append("- 大运：隔离序列；" + "→".join(case.dayun_sequence))
        blocks.append("\n".join(lines))
    return "# 历史隔离增量输入（仅命盘事实）\n\n" + "\n\n---\n\n".join(blocks) + "\n"


def derive_incremental(source: Path, baseline_path: Path) -> tuple[dict[str, Any], str]:
    baseline = _read_json(baseline_path)
    if baseline.get("schema_version") != "six-month-capability-baseline/v1":
        raise ValueError("baseline schema is invalid")
    if baseline.get("classification") != CLASSIFICATION:
        raise ValueError("baseline classification is not historical_blind_candidate")
    old_ids = sorted({str(row.get("case_id", "")) for row in baseline.get("scores", ())})
    if len(old_ids) != int(baseline.get("case_count", -1)):
        raise ValueError("baseline case IDs do not match case_count")
    old_subjects = {_subject_from_case_id(case_id) for case_id in old_ids}
    parsed = parse_case_summary_with_audit(source)
    incremental = [
        case for case in parsed.cases
        if (case.sex_marker, "".join(case.four_pillars)) not in old_subjects
    ]
    markdown = _isolated_markdown(incremental)
    serialized = markdown.lower()
    forbidden = ("feedback", "known_facts", "report_text", "statement_index", "命主反馈")
    if any(marker in serialized for marker in forbidden):
        raise ValueError("incremental isolated input contains a forbidden revealed marker")
    audit = {
        "schema_version": SCHEMA,
        "classification": CLASSIFICATION,
        "source": source.as_posix(),
        "parent_baseline": baseline_path.as_posix(),
        "parent_freeze_hash": baseline["freeze_hash"],
        "parent_case_count": len(old_ids),
        "current_deduplicated_case_count": len(parsed.cases),
        "duplicate_audit": parsed.duplicates,
        "incremental_case_count": len(incremental),
        "incremental_case_ids": [case.case_id for case in incremental],
        "isolated_input_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
    }
    return audit, markdown


def _prepare(args: argparse.Namespace) -> None:
    audit, markdown = derive_incremental(Path(args.source), Path(args.baseline))
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    if args.dry_run:
        return
    out = Path(args.out_dir)
    if out.exists():
        raise ValueError("prepare output directory must not exist")
    out.mkdir(parents=True)
    _write_json(out / "increment-audit.json", audit)
    (out / "incremental-input.md").write_text(markdown, encoding="utf-8")


def _stage_a(args: argparse.Namespace) -> None:
    result = build_stage_a(
        source=Path(args.input), catalog_path=Path(args.catalog),
        rules_path=Path(args.rules), frozen_at=args.frozen_at,
    )
    batch = result["historical_batch"]
    summary = {
        "classification": batch["classification"],
        "case_count": len(batch["cases"]),
        "output_count": len(batch["frozen_run"]["outputs"]),
        "expected_output_count": len(batch["cases"]) * len(APPROVED_TASK_IDS) * len(APPROVED_SCHOOLS),
        "freeze_hash": batch["frozen_run"]["freeze_hash"],
        "forbidden_marker_count": 0,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.dry_run:
        return
    out = Path(args.out_dir)
    if out.exists():
        raise ValueError("Stage A output directory must not exist")
    out.mkdir(parents=True)
    _write_json(out / "historical-batch.json", batch)
    _write_json(out / "outputs.json", {"schema_version": "school-capability-outputs/v1", "outputs": batch["frozen_run"]["outputs"]})
    _write_json(out / "tasks.json", result["cli_tasks"])
    _write_json(out / "freeze-tasks.json", result["freeze_tasks"])
    _write_json(out / "rule-snapshot.json", result["rule_snapshot"])
    _write_json(out / "frozen-run.json", batch["frozen_run"])


def _task_map(tasks_doc: Mapping[str, Any]) -> dict[str, BlindTask]:
    return {row["task_id"]: BlindTask.from_dict(row) for row in tasks_doc["tasks"]}


def _stage_b(args: argparse.Namespace) -> None:
    root = Path(args.stage_a_dir)
    batch = _read_json(root / "historical-batch.json")
    run = FrozenBlindRun.from_dict(batch["frozen_run"])
    verify_frozen_run(run)  # This must precede opening feedback.
    tasks_doc = _read_json(root / "tasks.json")
    case_ids = {row["case_id"] for row in batch["cases"]}
    raw_labels = parse_feedback_labels(Path(args.feedback), case_ids, reviewer=args.reviewer)
    tasks = _task_map(tasks_doc)
    approved = [row for row in raw_labels if row["task_id"] in tasks and row["task_id"] not in HIGH_RISK_TASK_IDS]
    excluded = [row for row in raw_labels if row not in approved]
    labels_doc = {"schema_version": "school-capability-labels/v1", "freeze_hash": run.freeze_hash, "labels": approved}
    reviewed_stub = {"reviewed_by": args.reviewer}
    inputs = build_stage_b_inputs(
        historical_batch=batch, cli_tasks=tasks_doc, labels_doc=labels_doc,
        reviewed_manifest=reviewed_stub, evaluated_at=args.evaluated_at,
    )
    scores = score_stage_b(
        historical_batch=batch, cli_tasks=tasks_doc,
        stage_b_inputs=inputs, evaluated_at=args.evaluated_at,
    )
    accepted_case_ids = sorted({row["case_id"] for row in inputs["labels"]["labels"]})
    accepted_outputs = [
        row for row in batch["frozen_run"]["outputs"] if row["case_id"] in accepted_case_ids
    ]
    summary = {
        "classification": CLASSIFICATION,
        "parent_freeze_hash": run.freeze_hash,
        "candidate_label_count": len(raw_labels),
        "accepted_approved_task_label_count": len(inputs["labels"]["labels"]),
        "accepted_case_count": len(accepted_case_ids),
        "excluded_outside_catalog_or_high_risk_count": len(excluded),
        "high_risk_assessable_count": 0,
        "accepted_label_identities": [[row["case_id"], row["task_id"]] for row in inputs["labels"]["labels"]],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.dry_run:
        return
    out = Path(args.out_dir)
    if out.exists():
        raise ValueError("Stage B output directory must not exist")
    out.mkdir(parents=True)
    _write_json(out / "candidate-labels.json", {"schema_version": "school-capability-labels/v1", "freeze_hash": run.freeze_hash, "labels": raw_labels})
    _write_json(out / "parent-bound-labels.json", inputs["labels"])
    _write_json(out / "stage-b-inputs.json", inputs)
    _write_json(out / "historical-scores.json", {
        "schema_version": "school-capability-historical-scores/v1",
        "freeze_hash": run.freeze_hash,
        "scores": scores["scores"],
    })
    _write_json(out / "task8-scores.json", scores)
    _write_json(out / "label-audit.json", {**summary, "excluded_labels": excluded})
    _write_json(out / "formal-outputs.json", {"schema_version": "school-capability-outputs/v1", "outputs": accepted_outputs})


def _bind_formal(args: argparse.Namespace) -> None:
    frozen = FrozenBlindRun.from_dict(_read_json(Path(args.frozen_run)))
    verify_frozen_run(frozen)
    stage_a = Path(args.stage_a_dir)
    stage_b = Path(args.stage_b_dir)
    tasks_doc = _read_json(stage_a / "tasks.json")
    task_map = _task_map(tasks_doc)
    parent_inputs = _read_json(stage_b / "stage-b-inputs.json")
    labels = parent_inputs["labels"]["labels"]
    selected_ids = {row["case_id"] for row in labels}
    output_ids = {row.case_id for row in frozen.outputs}
    if output_ids != selected_ids:
        raise ValueError("formal frozen subset does not match labelled cases")
    all_batch = _read_json(stage_a / "historical-batch.json")
    case_map = {row["case_id"]: row for row in all_batch["cases"]}
    outputs_by_case: dict[str, list[Any]] = {case_id: [] for case_id in selected_ids}
    for output in frozen.outputs:
        outputs_by_case[output.case_id].append(output)
    records = []
    metadata: dict[str, dict[str, str]] = {}
    grid: list[list[str]] = []
    for case_id in sorted(selected_ids):
        case = case_map[case_id]
        band = "complete" if case.get("dayun_sequence") and not str(case.get("solar_datetime", "")).startswith(("来源未", "约")) else "partial"
        routes = []
        for output in outputs_by_case[case_id]:
            task = task_map[output.task_id]
            route = {
                "school_id": output.school_id,
                "task_id": output.task_id,
                "chart_prototype_id": "prototype-provisional",
                "claim_type": task.claim_type,
                "time_horizon": task.allowed_time_horizons[0],
                "evidence_completeness_band": band,
            }
            routes.append(route)
            metadata["|".join((case_id, output.task_id, output.school_id))] = {
                key: route[key] for key in ("chart_prototype_id", "time_horizon", "evidence_completeness_band")
            }
        for task_id in APPROVED_TASK_IDS:
            grid.append([case_id, task_id])
        records.append({
            "case_id": case_id, "has_input": True, "has_feedback": True,
            "has_statement_index": False, "has_existing_report": False,
            "feedback_quantifiable": True, "contamination_flags": [],
            "eligibility": CLASSIFICATION,
            "evidence_notes": ["prediction outputs inherited unchanged from parent Stage A freeze; feedback revealed after parent verification"],
            "eligible_routes": routes,
        })
    manifest = {
        "schema_version": "school-capability-case-manifest/v1",
        "generated_at": args.evaluated_at,
        "reviewed_by": args.reviewer,
        "expected_schools": list(APPROVED_SCHOOLS),
        "records": records,
    }
    bound = {"schema_version": "school-capability-labels/v1", "freeze_hash": frozen.freeze_hash, "labels": labels}
    config = {
        "schema_version": "school-capability-evaluation-config/v1",
        "eligible_case_tasks": sorted(grid),
        "baseline_prevalence_by_task": {task_id: 0.5 for task_id in APPROVED_TASK_IDS},
        "case_metadata": dict(sorted(metadata.items())),
        "evidence_grade": "B",
        "evaluated_at": args.evaluated_at,
        "score_weights": {},
        "gate_thresholds": dict(GATE_THRESHOLDS_POLICY),
    }
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "bound-labels.json", bound)
    _write_json(out / "reviewed-manifest.json", manifest)
    _write_json(out / "evaluation-config.json", config)
    print(json.dumps({"formal_freeze_hash": frozen.freeze_hash, "case_count": len(selected_ids), "label_count": len(labels)}, ensure_ascii=False))


def _render_incremental_markdown(payload: Mapping[str, Any], audit: Mapping[str, Any]) -> str:
    text = render_final_markdown(payload)
    text = text.replace("六个月学派能力历史隔离基线（2026-07-15）", "学派能力历史隔离增量基线（2026-07-16）", 1)
    text = text.replace(
        "## 数据来源与历史隔离属性\n",
        "## 增量范围\n"
        f"- 父冻结案例：{audit['parent_case_count']}。\n"
        f"- 当前去重案例：{audit['current_deduplicated_case_count']}。\n"
        f"- 新增案例：{audit['incremental_case_count']}，ID：{', '.join(audit['incremental_case_ids'])}。\n\n"
        "## 数据来源与历史隔离属性\n",
        1,
    )
    return text.replace("2026-07-14 已有人工审核标签", "2026-07-16 已公开历史反馈的保守低歧义标签")


def _finalize(args: argparse.Namespace) -> None:
    stage_a = Path(args.stage_a_dir)
    stage_b = Path(args.stage_b_dir)
    formal_run = FrozenBlindRun.from_dict(_read_json(Path(args.formal_frozen_run)))
    verify_frozen_run(formal_run)
    formal_scores = _read_json(Path(args.formal_scores))
    if formal_scores.get("freeze_hash") != formal_run.freeze_hash:
        raise ValueError("formal scores/frozen run identity mismatch")
    unsigned_scores = dict(formal_scores)
    claimed_scores_digest = unsigned_scores.pop("artifact_digest", None)
    if claimed_scores_digest != f"sha256:{canonical_digest(unsigned_scores)}":
        raise ValueError("formal scores artifact digest mismatch")
    parent_inputs = _read_json(stage_b / "stage-b-inputs.json")
    audit = _read_json(Path(args.increment_audit))
    state_counts = Counter(row["state"] for row in formal_scores["scores"])
    gate = formal_scores.get("computed_gate_evidence", {})
    gate_reasons = [name for name, value in gate.items() if value is False]
    payload = {
        "schema_version": "six-month-capability-baseline/v1",
        "generated_at": args.generated_at,
        "classification": CLASSIFICATION,
        "batch_scope": "incremental_only",
        "task_catalog_identity": formal_run.task_catalog_version,
        "rule_snapshot_identity": formal_run.rule_snapshot_id,
        "freeze_hash": formal_run.freeze_hash,
        "case_count": len({row.case_id for row in formal_run.outputs}),
        "candidate_case_count": audit["incremental_case_count"],
        "labelled_case_count": len({row["case_id"] for row in parent_inputs["labels"]["labels"]}),
        "label_count": len(parent_inputs["labels"]["labels"]),
        "expected_schools": list(APPROVED_SCHOOLS),
        "task_ids": list(APPROVED_TASK_IDS),
        "state_counts": dict(sorted(state_counts.items())),
        "scores": formal_scores["scores"],
        "posteriors": formal_scores["posteriors"],
        "incremental_gains": formal_scores["incremental_gains"],
        "experiment_summary": formal_scores["experiment_summary"],
        "gate_status": "HOLD",
        "gate_reasons": gate_reasons or ["historical incremental evidence does not authorize production routing"],
        "gate_evidence": gate,
        "failure_classification_counts": {
            "high_risk_unassessable": formal_scores["gate_input_summary"].get("high_risk_unassessable_count", 0),
            "calibration_insufficient": sum(
                row.get("status") == "insufficient"
                for row in formal_scores["gate_input_summary"].get("calibration_by_identity", {}).values()
            ),
        },
        "failure_records": [],
        "parent_baseline": audit["parent_baseline"],
        "parent_freeze_hash": audit["parent_freeze_hash"],
        "incremental_case_ids": audit["incremental_case_ids"],
        "provenance": {
            **formal_scores["provenance"],
            "scores_artifact_digest": claimed_scores_digest,
            "historical_input": Path(args.increment_audit).parent.joinpath("incremental-input.md").as_posix(),
            "historical_labels": Path(args.stage_b_dir).joinpath("parent-bound-labels.json").as_posix(),
            "historical_reviewed_manifest": Path(args.formal_scores).parent.joinpath("reviewed-manifest.json").as_posix(),
            "historical_timing_notice": "historical feedback predates this refreeze; this is not a prospective/E3 blind test",
        },
        "prospective_status": {
            "status": "NOT_APPLICABLE_HISTORICAL_INCREMENT",
            "new_case_count": 0,
            "message": "本批为历史增量，不是前瞻样本",
            "bundle_sha256": "not-applicable",
            "rule_snapshot_id": "not-applicable",
            "next_intake_command_template": "use META/prospective-intake-protocol-v1.md",
            "next_bundle_command_template": "use the prospective blind bundle workflow",
        },
    }
    payload["artifact_digest"] = f"sha256:{canonical_digest(payload)}"
    json_out, md_out = Path(args.json_out), Path(args.md_out)
    if json_out.exists() or md_out.exists():
        raise ValueError("final incremental output must not overwrite an existing artifact")
    _write_json(json_out, payload)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.write_text(_render_incremental_markdown(payload, audit), encoding="utf-8")
    print(json.dumps({
        "classification": payload["classification"], "case_count": payload["case_count"],
        "label_count": payload["label_count"], "freeze_hash": payload["freeze_hash"],
        "artifact_digest": payload["artifact_digest"], "gate_status": payload["gate_status"],
    }, ensure_ascii=False, indent=2))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--source", required=True)
    prepare.add_argument("--baseline", required=True)
    prepare.add_argument("--out-dir", required=True)
    prepare.add_argument("--dry-run", action="store_true")
    prepare.set_defaults(handler=_prepare)
    stage_a = commands.add_parser("stage-a")
    stage_a.add_argument("--input", required=True)
    stage_a.add_argument("--catalog", required=True)
    stage_a.add_argument("--rules", required=True)
    stage_a.add_argument("--frozen-at", required=True)
    stage_a.add_argument("--out-dir", required=True)
    stage_a.add_argument("--dry-run", action="store_true")
    stage_a.set_defaults(handler=_stage_a)
    stage_b = commands.add_parser("stage-b")
    stage_b.add_argument("--stage-a-dir", required=True)
    stage_b.add_argument("--feedback", required=True)
    stage_b.add_argument("--reviewer", required=True)
    stage_b.add_argument("--evaluated-at", required=True)
    stage_b.add_argument("--out-dir", required=True)
    stage_b.add_argument("--dry-run", action="store_true")
    stage_b.set_defaults(handler=_stage_b)
    bind = commands.add_parser("bind-formal")
    bind.add_argument("--frozen-run", required=True)
    bind.add_argument("--stage-a-dir", required=True)
    bind.add_argument("--stage-b-dir", required=True)
    bind.add_argument("--reviewer", required=True)
    bind.add_argument("--evaluated-at", required=True)
    bind.add_argument("--out-dir", required=True)
    bind.set_defaults(handler=_bind_formal)
    final = commands.add_parser("finalize")
    final.add_argument("--stage-a-dir", required=True)
    final.add_argument("--stage-b-dir", required=True)
    final.add_argument("--increment-audit", required=True)
    final.add_argument("--formal-frozen-run", required=True)
    final.add_argument("--formal-scores", required=True)
    final.add_argument("--generated-at", required=True)
    final.add_argument("--json-out", required=True)
    final.add_argument("--md-out", required=True)
    final.set_defaults(handler=_finalize)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        args.handler(args)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print(f"INVALID: {error}", file=__import__("sys").stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
