"""Read-only school capability baseline CLI.

JSON contracts used by this phase:
- freeze --outputs: {"schema_version":"school-capability-outputs/v1","outputs":[BlindSchoolOutput...]}
- freeze --tasks: {"task_catalog_version":"..."}
- freeze --rule-snapshot: {"rule_snapshot_id":"..."}
- score --tasks: {"schema_version":"school-capability-cli-tasks/v1","tasks":[BlindTask...]}
- score --evaluation-config: explicit eligible grid, development baseline prevalence, six-dimensional
  case/output metadata, evidence grade, evaluation time, and 0/0.5/1 score weights.
- score output: computed individual scores, four-group rows/summary, gains, and posteriors.
- report --scores requires computed posteriors (an explicitly computed empty list is valid).

This tool audits and evaluates fixtures/artifacts. It never calibrates production rules or weights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.evaluation.capability import build_capability_posteriors
from engine.evaluation.case_audit import audit_cases
from engine.evaluation.experiments import run_four_group_experiment
from engine.evaluation.freeze import freeze_outputs, reveal_labels, verify_frozen_run
from engine.evaluation.models import BlindSchoolOutput, BlindTask, CapabilityPosterior, FrozenBlindRun
from engine.evaluation.report import render_capability_report
from engine.evaluation.scoring import score_output

_ROOT = Path(__file__).resolve().parents[1]
_FORBIDDEN_DIRS = tuple((_ROOT / name).resolve() for name in ("cases", "theory", "META"))
_FORBIDDEN_FILES = tuple((_ROOT / name).resolve() for name in ("engine/expert-weights.yaml", "engine/domain-weights.yaml"))


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _safe_output(path: Path) -> Path:
    if path.is_symlink():
        raise ValueError(f"output target must not be a symlink: {path}")
    resolved = path.resolve()
    if resolved in _FORBIDDEN_FILES or any(resolved == directory or directory in resolved.parents for directory in _FORBIDDEN_DIRS):
        raise ValueError(f"forbidden output path: {resolved}")
    return resolved


def _atomic_write(target: Path, content: str) -> None:
    if not target.is_absolute():
        raise ValueError("atomic writer requires a validated absolute path")
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if target.is_symlink() or target.parent.resolve() != target.parent:
            raise ValueError("output path changed or became a symlink before replace")
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _write_json(path: Path, payload: object) -> None:
    _atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _require_schema(document: dict[str, Any], expected: str) -> None:
    if document.get("schema_version") != expected:
        raise ValueError(f"schema_version must be {expected}")


def _audit(args: argparse.Namespace) -> None:
    target = _safe_output(Path(args.out))
    cases_dir = Path(args.cases_dir)
    reports_dir = Path(args.reports_dir)
    if not cases_dir.is_dir() or not reports_dir.is_dir():
        raise ValueError("cases-dir and reports-dir must be existing directories")
    records = audit_cases(cases_dir, reports_dir)
    _write_json(target, {
        "schema_version": "school-capability-case-manifest/v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "records": [record.to_dict() for record in records],
    })


def _freeze(args: argparse.Namespace) -> None:
    target = _safe_output(Path(args.out))
    outputs_doc = _read_json(Path(args.outputs))
    _require_schema(outputs_doc, "school-capability-outputs/v1")
    raw_outputs = outputs_doc.get("outputs")
    if not isinstance(raw_outputs, list):
        raise ValueError("outputs must be a list")
    tasks_doc = _read_json(Path(args.tasks))
    snapshot_doc = _read_json(Path(args.rule_snapshot))
    task_version = tasks_doc.get("task_catalog_version")
    snapshot_id = snapshot_doc.get("rule_snapshot_id")
    if not isinstance(task_version, str) or not task_version or not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("task_catalog_version and rule_snapshot_id must be non-empty strings")
    canonical = lambda document: json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    task_identity = f"{task_version}@sha256:{hashlib.sha256(canonical(tasks_doc)).hexdigest()}"
    snapshot_identity = f"{snapshot_id}@sha256:{hashlib.sha256(canonical(snapshot_doc)).hexdigest()}"
    run = freeze_outputs([BlindSchoolOutput.from_dict(item) for item in raw_outputs], task_identity, snapshot_identity)
    _write_json(target, run.to_dict())


def _parse_key(key: str) -> tuple[str, str, str]:
    parts = key.split("|")
    if len(parts) != 3 or any(not part for part in parts):
        raise ValueError("score_weights keys must be case_id|task_id|school_id")
    return parts[0], parts[1], parts[2]


def _score(args: argparse.Namespace) -> None:
    target = _safe_output(Path(args.out))
    manifest = _read_json(Path(args.manifest))
    if set(manifest) != {"schema_version", "generated_at", "expected_schools", "records"} or manifest.get("schema_version") != "school-capability-case-manifest/v1":
        raise ValueError("manifest top-level schema is invalid")
    records = manifest["records"]
    expected_schools = manifest["expected_schools"]
    record_fields = {"case_id", "has_input", "has_feedback", "has_statement_index", "has_existing_report", "feedback_quantifiable", "contamination_flags", "eligibility", "evidence_notes"}
    if not isinstance(records, list) or any(not isinstance(record, dict) or set(record) != record_fields for record in records):
        raise ValueError("manifest records have invalid schema")
    if not isinstance(expected_schools, list) or not expected_schools or any(not isinstance(school, str) or not school for school in expected_schools) or len(set(expected_schools)) != len(expected_schools):
        raise ValueError("expected_schools must be a unique non-empty string list")
    eligible_cases = {record["case_id"] for record in records if record["eligibility"] in {"blind_candidate", "historical_blind_candidate"}}
    manifest_digest = hashlib.sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    run = FrozenBlindRun.from_dict(_read_json(Path(args.frozen_run)))
    verify_frozen_run(run)  # Identity/freeze gate must precede any labels file access.
    labels = reveal_labels(run, Path(args.labels))
    tasks_doc = _read_json(Path(args.tasks))
    _require_schema(tasks_doc, "school-capability-cli-tasks/v1")
    config = _read_json(Path(args.evaluation_config))
    _require_schema(config, "school-capability-evaluation-config/v1")
    raw_tasks = tasks_doc.get("tasks")
    raw_grid = config.get("eligible_case_tasks")
    raw_weights = config.get("score_weights")
    if not isinstance(raw_tasks, list) or not isinstance(raw_grid, list) or not isinstance(raw_weights, dict):
        raise ValueError("tasks, eligible_case_tasks, and score_weights are required")
    tasks = [BlindTask.from_dict(item) for item in raw_tasks]
    task_map = {task.task_id: task for task in tasks}
    if len(task_map) != len(tasks):
        raise ValueError("duplicate task_id")
    grid: list[tuple[str, str]] = []
    for item in raw_grid:
        if not isinstance(item, list) or len(item) != 2 or any(not isinstance(value, str) or not value for value in item):
            raise ValueError("eligible_case_tasks entries must be [case_id, task_id]")
        grid.append((item[0], item[1]))
    if len(set(grid)) != len(grid):
        raise ValueError("duplicate eligible case-task identity")
    if any(case_id not in eligible_cases for case_id, _ in grid):
        raise ValueError("eligible grid contains a case not eligible in manifest")
    weights = {_parse_key(key): value for key, value in raw_weights.items()}
    if any(value not in (0, 0.5, 1) for value in weights.values()):
        raise ValueError("score weight must be one of 0, 0.5, or 1")
    label_map = {(label.case_id, label.task_id): label for label in labels}
    if len(label_map) != len(labels):
        raise ValueError("duplicate label identity")
    grid_set = set(grid)
    unknown_grid_tasks = {task_id for _, task_id in grid if task_id not in task_map}
    if unknown_grid_tasks:
        raise ValueError(f"unknown task in eligible grid: {sorted(unknown_grid_tasks)[0]}")
    if any((label.case_id, label.task_id) not in grid_set for label in labels):
        raise ValueError("label is outside eligible grid")
    output_keys = {(output.case_id, output.task_id, output.school_id) for output in run.outputs}
    if len(output_keys) != len(run.outputs):
        raise ValueError("duplicate output identity")
    if any((case_id, task_id) not in grid_set or task_id not in task_map for case_id, task_id, _ in weights):
        raise ValueError("score weight references grid outside or unknown task")
    if any(key not in output_keys for key in weights):
        raise ValueError("score weight references nonexistent output")
    metadata = config.get("case_metadata")
    baseline = config.get("baseline_prevalence_by_task")
    evidence_grade, evaluated_at = config.get("evidence_grade"), config.get("evaluated_at")
    if not isinstance(metadata, dict) or not isinstance(baseline, dict) or not isinstance(evidence_grade, str) or not evidence_grade or not isinstance(evaluated_at, str) or not evaluated_at:
        raise ValueError("case_metadata, baseline_prevalence_by_task, evidence_grade, and evaluated_at are required")
    metadata_keys = {_parse_key(key) for key in metadata}
    if metadata_keys != output_keys:
        raise ValueError("case_metadata must exactly cover frozen outputs")
    if set(baseline) != {task_id for _, task_id in grid}:
        raise ValueError("baseline_prevalence_by_task must exactly cover eligible tasks")
    scores = []
    score_objects = []
    probabilities: dict[str, float] = {}
    for output in run.outputs:
        identity = (output.case_id, output.task_id)
        if identity not in grid_set:
            raise ValueError(f"output is outside eligible grid: {identity}")
        if output.task_id not in task_map:
            raise ValueError(f"unknown task: {output.task_id}")
        key = (output.case_id, output.task_id, output.school_id)
        raw_metadata = metadata.get("|".join(key))
        if not isinstance(raw_metadata, dict) or any(not isinstance(raw_metadata.get(name), str) or not raw_metadata[name] for name in ("chart_prototype_id", "time_horizon", "evidence_completeness_band")):
            raise ValueError(f"missing six-dimensional metadata for {key}")
        score = replace(score_output(output, task_map[output.task_id], label_map.get(identity)), **raw_metadata)
        score_objects.append(score)
        scores.append(score.to_dict())
        if output.state == "claim" and task_map[output.task_id].scoring_method == "binary_probability":
            probabilities["|".join((output.case_id, output.task_id, output.school_id))] = output.predictions[0].probability
    schools = expected_schools
    expected_outputs = {(case_id, task_id, school) for case_id, task_id in grid for school in schools}
    if output_keys != expected_outputs:
        raise ValueError("each eligible case-task and expected school requires exactly one output")
    experiment = run_four_group_experiment(run.outputs, labels, tasks, schools, eligible_case_tasks=grid, baseline_prevalence=baseline)
    gains_by_school_task = experiment.capability_incremental_gain_by_school_task()
    eligible_by_identity: dict[tuple[str, str, str, str, str, str], set[str]] = defaultdict(set)
    gains_by_identity = {}
    for score in score_objects:
        identity6 = (score.school_id, score.task_id, score.chart_prototype_id, score.claim_type, score.time_horizon, score.evidence_completeness_band)
        eligible_by_identity[identity6].update(case_id for case_id, task_id in grid if task_id == score.task_id)
        gains_by_identity[identity6] = gains_by_school_task.get((score.school_id, score.task_id), 0.0)
    probability_map = {_parse_key(key): value for key, value in probabilities.items()}
    probability_scores = [score for score in score_objects if task_map[score.task_id].scoring_method == "binary_probability"]
    probability_identities = {identity: cases for identity, cases in eligible_by_identity.items() if task_map[identity[1]].scoring_method == "binary_probability"}
    posteriors = build_capability_posteriors(probability_scores, evidence_grade, evaluated_at, claim_probabilities=probability_map, eligible_case_ids=probability_identities, score_weights=weights, incremental_gains=gains_by_identity)
    rows = [row.__dict__ for row in experiment.rows]
    serialized_gains = {"|".join(identity): value for identity, value in sorted(gains_by_identity.items())}
    _write_json(target, {
        "schema_version": "school-capability-scores/v1", "freeze_hash": run.freeze_hash,
        "provenance": {"manifest_digest": f"sha256:{manifest_digest}", "task_catalog": run.task_catalog_version, "rule_snapshot": run.rule_snapshot_id, "freeze_hash": run.freeze_hash},
        "eligible_case_tasks": [list(item) for item in sorted(grid)], "scores": scores,
        "claim_probabilities": dict(sorted(probabilities.items())),
        "score_weights": {"|".join(key): value for key, value in sorted(weights.items())},
        "experiment_rows": rows, "experiment_summary": dict(experiment.mean_utility_by_group),
        "incremental_gains": serialized_gains, "posteriors_computed": True,
        "posteriors": [posterior.to_dict() for posterior in posteriors],
    })


def _report(args: argparse.Namespace) -> None:
    target = _safe_output(Path(args.out))
    scores_doc = _read_json(Path(args.scores))
    _require_schema(scores_doc, "school-capability-scores/v1")
    manifest_doc = _read_json(Path(args.manifest))
    _require_schema(manifest_doc, "school-capability-case-manifest/v1")
    records = manifest_doc.get("records")
    if not isinstance(records, list):
        raise ValueError("manifest records must be a list")
    summary = Counter(record.get("eligibility", "unknown") for record in records if isinstance(record, dict))
    if "posteriors" not in scores_doc or not isinstance(scores_doc["posteriors"], list):
        raise ValueError("posteriors must be present and be a list")
    raw_posteriors = scores_doc["posteriors"]
    if not raw_posteriors and scores_doc.get("posteriors_computed") is not True:
        raise ValueError("empty posteriors require posteriors_computed: true")
    posteriors = [CapabilityPosterior.from_dict(item) for item in raw_posteriors]
    experiment_summary = scores_doc.get("experiment_summary", {})
    if not isinstance(experiment_summary, dict):
        raise ValueError("experiment_summary must be an object")
    gate_evidence = scores_doc.get("gate_evidence")
    if gate_evidence is not None and not isinstance(gate_evidence, dict):
        raise ValueError("gate_evidence must be an object")
    text = render_capability_report(summary, experiment_summary, posteriors, gate_evidence=gate_evidence)
    _atomic_write(target, text)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only blind school capability baseline evaluation")
    commands = parser.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("audit")
    audit.add_argument("--cases-dir", required=True)
    audit.add_argument("--reports-dir", required=True)
    audit.add_argument("--out", required=True)
    audit.set_defaults(handler=_audit)
    freeze = commands.add_parser("freeze")
    freeze.add_argument("--outputs", required=True)
    freeze.add_argument("--tasks", required=True)
    freeze.add_argument("--rule-snapshot", required=True)
    freeze.add_argument("--out", required=True)
    freeze.set_defaults(handler=_freeze)
    score = commands.add_parser("score")
    score.add_argument("--frozen-run", required=True)
    score.add_argument("--manifest", required=True)
    score.add_argument("--labels", required=True)
    score.add_argument("--tasks", required=True)
    score.add_argument("--evaluation-config", required=True)
    score.add_argument("--out", required=True)
    score.set_defaults(handler=_score)
    report = commands.add_parser("report")
    report.add_argument("--scores", required=True)
    report.add_argument("--manifest", required=True)
    report.add_argument("--out", required=True)
    report.set_defaults(handler=_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
