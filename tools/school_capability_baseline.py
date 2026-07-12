"""Read-only school capability baseline CLI.

JSON contracts used by this phase:
- freeze --outputs: {"schema_version":"school-capability-outputs/v1","outputs":[BlindSchoolOutput...]}
- freeze --tasks: {"task_catalog_version":"..."}
- freeze --rule-snapshot: {"rule_snapshot_id":"..."}
- score --tasks: {"schema_version":"school-capability-cli-tasks/v1","tasks":[BlindTask...],
  "eligible_case_tasks":[[case_id,task_id]...],"score_weights":{"case|task|school":0|0.5|1}}
- score output: binary_probability tasks only, with explicit eligible grid, claim probabilities and weights.
- report --scores accepts the score output plus optional experiment_summary and posteriors.

This tool audits and evaluates fixtures/artifacts. It never calibrates production rules or weights.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from engine.evaluation.case_audit import audit_cases
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
    resolved = path.resolve()
    if resolved in _FORBIDDEN_FILES or any(resolved == directory or directory in resolved.parents for directory in _FORBIDDEN_DIRS):
        raise ValueError(f"forbidden output path: {resolved}")
    return resolved


def _atomic_write(path: Path, content: str) -> None:
    target = _safe_output(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
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
    cases_dir = Path(args.cases_dir)
    reports_dir = Path(args.reports_dir)
    if not cases_dir.is_dir() or not reports_dir.is_dir():
        raise ValueError("cases-dir and reports-dir must be existing directories")
    records = audit_cases(cases_dir, reports_dir)
    _write_json(Path(args.out), {
        "schema_version": "school-capability-case-manifest/v1",
        "records": [record.to_dict() for record in records],
    })


def _freeze(args: argparse.Namespace) -> None:
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
    run = freeze_outputs([BlindSchoolOutput.from_dict(item) for item in raw_outputs], task_version, snapshot_id)
    _write_json(Path(args.out), run.to_dict())


def _parse_key(key: str) -> tuple[str, str, str]:
    parts = key.split("|")
    if len(parts) != 3 or any(not part for part in parts):
        raise ValueError("score_weights keys must be case_id|task_id|school_id")
    return parts[0], parts[1], parts[2]


def _score(args: argparse.Namespace) -> None:
    run = FrozenBlindRun.from_dict(_read_json(Path(args.frozen_run)))
    verify_frozen_run(run)  # Identity/freeze gate must precede any labels file access.
    labels = reveal_labels(run, Path(args.labels))
    tasks_doc = _read_json(Path(args.tasks))
    _require_schema(tasks_doc, "school-capability-cli-tasks/v1")
    raw_tasks = tasks_doc.get("tasks")
    raw_grid = tasks_doc.get("eligible_case_tasks")
    raw_weights = tasks_doc.get("score_weights")
    if not isinstance(raw_tasks, list) or not isinstance(raw_grid, list) or not isinstance(raw_weights, dict):
        raise ValueError("tasks, eligible_case_tasks, and score_weights are required")
    tasks = [BlindTask.from_dict(item) for item in raw_tasks]
    unsupported = sorted({task.scoring_method for task in tasks if task.scoring_method != "binary_probability"})
    if unsupported:
        raise ValueError(f"this CLI phase supports only binary_probability tasks; received: {', '.join(unsupported)}")
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
    weights = {_parse_key(key): value for key, value in raw_weights.items()}
    if any(value not in (0, 0.5, 1) for value in weights.values()):
        raise ValueError("score weight must be one of 0, 0.5, or 1")
    label_map = {(label.case_id, label.task_id): label for label in labels}
    if len(label_map) != len(labels):
        raise ValueError("duplicate label identity")
    grid_set = set(grid)
    scores = []
    probabilities: dict[str, float] = {}
    for output in run.outputs:
        identity = (output.case_id, output.task_id)
        if identity not in grid_set:
            raise ValueError(f"output is outside eligible grid: {identity}")
        if output.task_id not in task_map:
            raise ValueError(f"unknown task: {output.task_id}")
        score = score_output(output, task_map[output.task_id], label_map.get(identity))
        scores.append(score.to_dict())
        if output.state == "claim":
            if len(output.predictions) != 1:
                raise ValueError("binary score input requires exactly one prediction")
            probabilities["|".join((output.case_id, output.task_id, output.school_id))] = output.predictions[0].probability
    _write_json(Path(args.out), {
        "schema_version": "school-capability-scores/v1",
        "freeze_hash": run.freeze_hash,
        "eligible_case_tasks": [list(item) for item in sorted(grid)],
        "scores": scores,
        "claim_probabilities": dict(sorted(probabilities.items())),
        "score_weights": {"|".join(key): value for key, value in sorted(weights.items())},
        "incremental_gains": {},
        "experiment_summary": {},
        "posteriors": [],
    })


def _report(args: argparse.Namespace) -> None:
    scores_doc = _read_json(Path(args.scores))
    _require_schema(scores_doc, "school-capability-scores/v1")
    manifest_doc = _read_json(Path(args.manifest))
    _require_schema(manifest_doc, "school-capability-case-manifest/v1")
    records = manifest_doc.get("records")
    if not isinstance(records, list):
        raise ValueError("manifest records must be a list")
    summary = Counter(record.get("eligibility", "unknown") for record in records if isinstance(record, dict))
    raw_posteriors = scores_doc.get("posteriors", [])
    if not isinstance(raw_posteriors, list):
        raise ValueError("posteriors must be a list")
    posteriors = [CapabilityPosterior.from_dict(item) for item in raw_posteriors]
    experiment_summary = scores_doc.get("experiment_summary", {})
    if not isinstance(experiment_summary, dict):
        raise ValueError("experiment_summary must be an object")
    text = render_capability_report(summary, experiment_summary, posteriors)
    _atomic_write(Path(args.out), text)


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
    score.add_argument("--labels", required=True)
    score.add_argument("--tasks", required=True)
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
