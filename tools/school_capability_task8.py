"""Reproducible Task 8 historical-isolation baseline orchestration.

Stage A accepts chart inputs, the approved task catalog, and the executable-rule
snapshot only.  Stage B is a separate command which verifies Stage A before it
opens the reviewed labels and prior reviewed manifest.  This module never
changes runners, rules, scoring policy, production weights, or routing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from engine.evaluation.capability import build_capability_posteriors
from engine.evaluation.experiments import run_four_group_experiment
from engine.claims.orchestrator import generate_blind_outputs
from engine.evaluation.freeze import freeze_outputs, verify_frozen_run
from engine.evaluation.manifest_validation import GATE_THRESHOLDS_POLICY, validate_reviewed_manifest
from engine.evaluation.models import BlindSchoolOutput, BlindTask, FrozenBlindRun, RevealedLabel
from engine.evaluation.report import compute_gate_evidence
from engine.evaluation.scoring import score_output
from engine.evaluation.task_catalog import load_task_catalog
from tools.school_capability_batch import ProspectiveCase, parse_case_summary_with_audit

APPROVED_SCHOOLS = ("ziping", "ditiansui", "duan", "ren", "gao", "yang")
APPROVED_TASK_IDS = (
    "structure.overview",
    "career.role_change",
    "marriage.divorce_or_remarriage",
    "wealth.debt",
    "career.path_type",
    "health.system_risk",
    "career.change_window",
    "marriage.event_window",
    "health.event_window",
    "wealth.major_loss_window",
)
SCHEMA_VERSION = "six-month-capability-baseline/v1"


def canonical_digest(value: object) -> str:
    content = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with __import__("os").fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            __import__("os").fsync(stream.fileno())
        __import__("os").replace(temporary, path)
    except BaseException:
        try:
            __import__("os").unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _approved_tasks(catalog_path: Path) -> list[BlindTask]:
    indexed = {task.task_id: task for task in load_task_catalog(catalog_path)}
    missing = set(APPROVED_TASK_IDS) - set(indexed)
    if missing:
        raise ValueError(f"approved task missing from catalog: {sorted(missing)[0]}")
    return [indexed[task_id] for task_id in APPROVED_TASK_IDS]


def _task_documents(tasks: Sequence[BlindTask], catalog_path: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    selected = [task.to_dict() for task in tasks]
    source_sha = hashlib.sha256(catalog_path.read_bytes()).hexdigest()
    version = f"school-capability-task-catalog-v1-ten-approved@source-sha256:{source_sha}"
    freeze_doc = {"task_catalog_version": version, "tasks": selected}
    cli_doc = {"schema_version": "school-capability-cli-tasks/v1", "task_catalog_version": version, "tasks": selected}
    identity = f"{version}@sha256:{canonical_digest(cli_doc)}"
    return freeze_doc, cli_doc, identity


def _rule_snapshot(rules_path: Path) -> dict[str, Any]:
    content_sha = hashlib.sha256(rules_path.read_bytes()).hexdigest()
    return {
        "rule_snapshot_id": f"claim-rules-v1-{content_sha}",
        "source": rules_path.as_posix(),
        "content_sha256": content_sha,
    }


def _assert_complete_grid(run: FrozenBlindRun, case_ids: Iterable[str]) -> None:
    expected = {
        (case_id, task_id, school_id)
        for case_id in case_ids
        for task_id in APPROVED_TASK_IDS
        for school_id in APPROVED_SCHOOLS
    }
    actual = {(row.case_id, row.task_id, row.school_id) for row in run.outputs}
    if len(actual) != len(run.outputs) or actual != expected:
        raise ValueError("frozen output grid is not a unique six-school by ten-task matrix")


def _chart_mapping(case: ProspectiveCase) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "sex_marker": case.sex_marker,
        "solar_datetime": case.solar_datetime,
        "four_pillars": list(case.four_pillars),
        "dayun_steps": [{"ganzhi": ganzhi} for ganzhi in case.dayun_sequence],
        "liunian_steps": [],
    }


def _scoring_contract_error(output: BlindSchoolOutput, task: BlindTask) -> str | None:
    if output.state != "claim":
        return None
    if task.scoring_method == "multiclass_probability":
        expected = tuple(task.label_schema.get("labels", ()))
        actual = tuple(prediction.event_label for prediction in output.predictions)
        if len(actual) != len(expected) or set(actual) != set(expected):
            return "multiclass claim does not provide the full catalog probability distribution"
        if abs(sum(prediction.probability for prediction in output.predictions) - 1.0) > 1e-9:
            return "multiclass claim probabilities do not sum to one"
    return None


def _stage_a_outputs(cases: Sequence[ProspectiveCase], tasks: Sequence[BlindTask]) -> list[BlindSchoolOutput]:
    """Keep the matrix total when a runner claim violates a frozen evaluation contract."""
    outputs: list[BlindSchoolOutput] = []
    for case in cases:
        for school in APPROVED_SCHOOLS:
            for task in tasks:
                try:
                    output = generate_blind_outputs(
                        _chart_mapping(case), [task], case_id=case.case_id, schools=[school],
                    )[0]
                    contract_error = _scoring_contract_error(output, task)
                    if contract_error:
                        output = BlindSchoolOutput(
                            case_id=case.case_id,
                            school_id=school,
                            task_id=task.task_id,
                            state="abstain",
                            rationale=f"runner claim rejected by frozen scoring contract: {contract_error}",
                        )
                except ValueError as error:
                    if "is not allowed for task" not in str(error):
                        raise
                    output = BlindSchoolOutput(
                        case_id=case.case_id,
                        school_id=school,
                        task_id=task.task_id,
                        state="abstain",
                        rationale=f"runner claim rejected by frozen task contract: {error}",
                    )
                outputs.append(output)
    return outputs


def build_stage_a(
    *, source: Path, catalog_path: Path, rules_path: Path, frozen_at: str,
) -> dict[str, Any]:
    """Build Stage A without accepting or reading any revealed-data path."""
    tasks = _approved_tasks(catalog_path)
    freeze_tasks, cli_tasks, task_identity = _task_documents(tasks, catalog_path)
    snapshot = _rule_snapshot(rules_path)
    snapshot_identity = f"{snapshot['rule_snapshot_id']}@sha256:{canonical_digest(snapshot)}"
    audit = parse_case_summary_with_audit(source)
    frozen = freeze_outputs(
        _stage_a_outputs(audit.cases, tasks),
        task_identity,
        snapshot_identity,
        frozen_at=frozen_at,
    )
    batch = {
        "schema_version": "school-capability-historical-batch/v1",
        "classification": "historical_blind_candidate",
        "cases": [
            {
                "case_id": case.case_id,
                "sex_marker": case.sex_marker,
                "four_pillars": list(case.four_pillars),
                "solar_datetime": case.solar_datetime,
                "dayun_sequence": list(case.dayun_sequence),
                "liunian_sequence": [],
            }
            for case in audit.cases
        ],
        "duplicate_audit": audit.duplicates,
        "frozen_run": frozen.to_dict(),
    }
    run = FrozenBlindRun.from_dict(batch["frozen_run"])
    verify_frozen_run(run)
    _assert_complete_grid(run, (row["case_id"] for row in batch["cases"]))
    serialized = json.dumps(batch, ensure_ascii=False).lower()
    forbidden = ('"labels"', '"feedback"', '"known_facts"', '"report_text"', '"scores"')
    if any(marker in serialized for marker in forbidden):
        raise ValueError("Stage A artifact contains revealed-data fields")
    return {
        "historical_batch": batch,
        "freeze_tasks": freeze_tasks,
        "cli_tasks": cli_tasks,
        "rule_snapshot": snapshot,
    }


def _label_schema_valid(label: Mapping[str, Any], task: BlindTask) -> bool:
    if not label.get("quantifiable") or label.get("conflict_state") != "none":
        return False
    value = label.get("label")
    schema = task.label_schema
    if task.scoring_method == "binary_probability":
        return value in {schema.get("positive_label"), schema.get("negative_label")}
    if task.scoring_method == "multiclass_probability":
        return value in schema.get("labels", ())
    if task.scoring_method == "time_window":
        return (
            isinstance(value, dict)
            and type(value.get("occurred")) is bool
            and ((value["occurred"] and type(value.get("year")) is int) or (not value["occurred"] and value.get("year") is None))
        )
    return True


def _evidence_band(case: Mapping[str, Any]) -> str:
    solar = str(case.get("solar_datetime", ""))
    return "complete" if case.get("dayun_sequence") and not solar.startswith(("来源未", "约")) else "partial"


def build_stage_b_inputs(
    *,
    historical_batch: dict[str, Any],
    cli_tasks: dict[str, Any],
    labels_doc: dict[str, Any],
    reviewed_manifest: dict[str, Any],
    evaluated_at: str,
) -> dict[str, Any]:
    """Verify the frozen run first, then bind unchanged eligible human labels."""
    run = FrozenBlindRun.from_dict(historical_batch["frozen_run"])
    verify_frozen_run(run)
    _assert_complete_grid(run, (row["case_id"] for row in historical_batch["cases"]))
    tasks = [BlindTask.from_dict(row) for row in cli_tasks["tasks"]]
    task_map = {task.task_id: task for task in tasks}
    case_map = {row["case_id"]: row for row in historical_batch["cases"]}
    reviewer = reviewed_manifest.get("reviewed_by")
    if not isinstance(reviewer, str) or not reviewer or reviewer.lower().startswith(("agent", "ai-", "automated")):
        raise ValueError("existing reviewed manifest must identify a human reviewer")
    raw_labels = labels_doc.get("labels")
    if labels_doc.get("schema_version") != "school-capability-labels/v1" or not isinstance(raw_labels, list):
        raise ValueError("historical labels schema is invalid")

    accepted: list[dict[str, Any]] = []
    label_quality_holds: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw in raw_labels:
        if not isinstance(raw, dict):
            raise ValueError("label record must be an object")
        identity = raw.get("case_id"), raw.get("task_id")
        if identity[0] not in case_map or identity[1] not in task_map:
            continue
        if identity in seen:
            raise ValueError("duplicate label identity")
        seen.add(identity)  # type: ignore[arg-type]
        task = task_map[str(identity[1])]
        high_risk_ok = not task.high_risk or (
            raw.get("confidence_grade") == "A" and bool(raw.get("secondary_reviewed_by"))
        )
        if not high_risk_ok or not _label_schema_valid(raw, task):
            label_quality_holds.extend(
                {"case_id": str(identity[0]), "task_id": str(identity[1]), "school_id": school}
                for school in APPROVED_SCHOOLS
            )
            continue
        accepted.append(dict(raw))

    accepted.sort(key=lambda row: (row["case_id"], row["task_id"]))
    labelled_cases = {row["case_id"] for row in accepted}
    outputs_by_case: dict[str, list[Any]] = defaultdict(list)
    for output in run.outputs:
        outputs_by_case[output.case_id].append(output)
    records = []
    for case_id, case in sorted(case_map.items()):
        eligible = case_id in labelled_cases
        routes = []
        if eligible:
            for output in outputs_by_case[case_id]:
                task = task_map[output.task_id]
                routes.append({
                    "school_id": output.school_id,
                    "task_id": output.task_id,
                    "chart_prototype_id": "prototype-provisional",
                    "claim_type": task.claim_type,
                    "time_horizon": task.allowed_time_horizons[0],
                    "evidence_completeness_band": _evidence_band(case),
                })
        records.append({
            "case_id": case_id,
            "has_input": True,
            "has_feedback": eligible,
            "has_statement_index": False,
            "has_existing_report": False,
            "feedback_quantifiable": eligible,
            "contamination_flags": [],
            "eligibility": "historical_blind_candidate" if eligible else "development_only",
            "evidence_notes": ["historical feedback predates current runner refreeze; labels revealed only after Stage A verification"] if eligible else ["no eligible existing reviewed label for approved Task 8 grid"],
            "eligible_routes": routes,
        })
    manifest = {
        "schema_version": "school-capability-case-manifest/v1",
        "generated_at": evaluated_at,
        "reviewed_by": reviewer,
        "expected_schools": list(APPROVED_SCHOOLS),
        "records": records,
    }
    validate_reviewed_manifest(manifest)
    return {
        "manifest": manifest,
        "labels": {"schema_version": "school-capability-labels/v1", "freeze_hash": run.freeze_hash, "labels": accepted},
        "failure_counts": {"label_quality": len(label_quality_holds)},
        "label_quality_holds": label_quality_holds,
    }


def _baseline_prevalence(labels: Sequence[RevealedLabel], tasks: Sequence[BlindTask]) -> dict[str, float]:
    labels_by_task: dict[str, list[RevealedLabel]] = defaultdict(list)
    for label in labels:
        labels_by_task[label.task_id].append(label)
    result: dict[str, float] = {}
    for task in tasks:
        rows = labels_by_task.get(task.task_id, [])
        if task.scoring_method == "binary_probability" and rows:
            positive = task.label_schema["positive_label"]
            result[task.task_id] = sum(row.label == positive for row in rows) / len(rows)
        else:
            result[task.task_id] = 0.5
    return result


def score_stage_b(
    *, historical_batch: dict[str, Any], cli_tasks: dict[str, Any], stage_b_inputs: dict[str, Any], evaluated_at: str,
) -> dict[str, Any]:
    run = FrozenBlindRun.from_dict(historical_batch["frozen_run"])
    verify_frozen_run(run)
    tasks = [BlindTask.from_dict(row) for row in cli_tasks["tasks"]]
    task_map = {task.task_id: task for task in tasks}
    labels = [RevealedLabel.from_dict(row) for row in stage_b_inputs["labels"]["labels"]]
    label_map = {(row.case_id, row.task_id): row for row in labels}
    case_map = {row["case_id"]: row for row in historical_batch["cases"]}

    scores = []
    output_map = {(row.case_id, row.task_id, row.school_id): row for row in run.outputs}
    for output in run.outputs:
        task = task_map[output.task_id]
        score = replace(
            score_output(output, task, label_map.get((output.case_id, output.task_id))),
            chart_prototype_id="prototype-provisional",
            time_horizon=task.allowed_time_horizons[0],
            evidence_completeness_band=_evidence_band(case_map[output.case_id]),
        )
        scores.append(score)

    grid = [(case_id, task_id) for case_id in sorted(case_map) for task_id in APPROVED_TASK_IDS]
    experiment = run_four_group_experiment(
        run.outputs,
        labels,
        tasks,
        APPROVED_SCHOOLS,
        eligible_case_tasks=grid,
        baseline_prevalence=_baseline_prevalence(labels, tasks),
    )
    all_utility = {(row.case_id, row.task_id): row.utility for row in experiment.rows if row.group_id == "all_schools"}
    gains: dict[tuple[str, str, str, str, str, str], list[float]] = defaultdict(list)
    for row in experiment.rows:
        if not row.group_id.startswith("leave_one_school_out:") or row.utility is None:
            continue
        base = all_utility.get((row.case_id, row.task_id))
        if base is None:
            continue
        school = row.group_id.removeprefix("leave_one_school_out:")
        score = next(item for item in scores if (item.case_id, item.task_id, item.school_id) == (row.case_id, row.task_id, school))
        identity = (score.school_id, score.task_id, score.chart_prototype_id, score.claim_type, score.time_horizon, score.evidence_completeness_band)
        gains[identity].append(base - row.utility)
    gains_by_identity = {key: sum(values) / len(values) for key, values in gains.items()}

    probability_scores = [row for row in scores if task_map[row.task_id].scoring_method == "binary_probability"]
    probability_map = {
        key: output_map[key].predictions[0].probability
        for key in output_map
        if output_map[key].state == "claim" and task_map[key[1]].scoring_method == "binary_probability"
    }
    eligible: dict[tuple[str, str, str, str, str, str], set[str]] = defaultdict(set)
    for score in probability_scores:
        identity = (score.school_id, score.task_id, score.chart_prototype_id, score.claim_type, score.time_horizon, score.evidence_completeness_band)
        eligible[identity].add(score.case_id)
    posteriors = build_capability_posteriors(
        probability_scores,
        "B",
        evaluated_at,
        claim_probabilities=probability_map,
        eligible_case_ids=eligible,
        incremental_gains=gains_by_identity,
    )

    failures = Counter(stage_b_inputs["failure_counts"])
    failure_records: list[dict[str, str]] = list(stage_b_inputs["label_quality_holds"])
    for score in scores:
        reason: str | None = None
        task = task_map[score.task_id]
        case = case_map[score.case_id]
        if score.state == "unsupported":
            reason = "coverage"
        elif score.state == "abstain":
            reason = "input_completeness" if task.scoring_method == "time_window" and not case.get("liunian_sequence") else "trigger_boundary"
        elif (score.case_id, score.task_id) not in label_map:
            reason = "label_quality"
        elif task.high_risk and score.observed_positive is False and score.utility is not None and score.utility < 0:
            reason = "high_risk_false_positive"
        if reason:
            failures[reason] += 1
            failure_records.append({"case_id": score.case_id, "task_id": score.task_id, "school_id": score.school_id, "classification": reason})
    for posterior in posteriors:
        if posterior.calibration_error is None or posterior.n_eff < GATE_THRESHOLDS_POLICY["calibration_min_samples"]:
            failures["calibration"] += 1

    state_counts = Counter(row.state for row in run.outputs)
    calibration_counts: dict[str, int] = {}
    coverage: dict[str, float] = {}
    for identity, cases in eligible.items():
        key = "|".join(identity)
        rows = [score for score in probability_scores if (score.school_id, score.task_id, score.chart_prototype_id, score.claim_type, score.time_horizon, score.evidence_completeness_band) == identity]
        calibration_counts[key] = sum(row.state == "claim" and row.probability_score is not None for row in rows)
        coverage[key] = sum(row.knowledge_coverage for row in rows) / len(cases) if cases else 0.0
    high_risk_tasks = {task.task_id for task in tasks if task.high_risk}
    high_risk_scores = [row for row in scores if row.task_id in high_risk_tasks]
    high_risk_assessable = [row for row in high_risk_scores if row.utility is not None]
    summary = {
        "coverage_by_identity": coverage,
        "calibration_sample_count_by_identity": calibration_counts,
        "high_risk_task_ids": sorted(high_risk_tasks),
        "high_risk_unassessable_count": sum(row.utility is None for row in high_risk_scores),
        "high_risk_utilities": [row.utility for row in high_risk_assessable],
    }
    provenance = {
        "manifest_digest": f"sha256:{canonical_digest(stage_b_inputs['manifest'])}",
        "task_catalog": run.task_catalog_version,
        "rule_snapshot": run.rule_snapshot_id,
        "freeze_hash": run.freeze_hash,
    }
    serialized_gains = {"|".join(key): value for key, value in sorted(gains_by_identity.items())}
    gate = compute_gate_evidence(
        posteriors=[row.to_dict() for row in posteriors],
        incremental_gains=serialized_gains,
        experiment_summary=experiment.mean_utility_by_group,
        high_risk_audit_summary=summary,
        coverage_summary=summary,
        gate_thresholds=GATE_THRESHOLDS_POLICY,
        provenance=provenance,
    )
    payload = {
        "schema_version": "school-capability-scores/v1",
        "freeze_hash": run.freeze_hash,
        "provenance": provenance,
        "scores": [row.to_dict() for row in scores],
        "experiment_rows": [row.__dict__ for row in experiment.rows],
        "experiment_summary": dict(experiment.mean_utility_by_group),
        "incremental_gains": serialized_gains,
        "posteriors_computed": True,
        "posteriors": [row.to_dict() for row in posteriors],
        "gate_input_summary": {**summary, "gate_thresholds": dict(GATE_THRESHOLDS_POLICY)},
        "computed_gate_evidence": gate,
        "state_counts": dict(state_counts),
        "failure_classification_counts": dict(sorted(failures.items())),
        "failure_records": failure_records,
    }
    payload["artifact_digest"] = f"sha256:{canonical_digest(payload)}"
    return payload


def audit_prospective(*, intake_path: Path, bundle_dir: Path, snapshot_path: Path) -> dict[str, Any]:
    intake = _read_json(intake_path)
    manifest = _read_json(bundle_dir / "bundle-manifest.json")
    snapshot = _read_json(snapshot_path)
    if intake.get("schema_version") != "school-capability-prospective-intake/v1" or not isinstance(intake.get("records"), list):
        raise ValueError("prospective intake schema is invalid")
    files = manifest.get("files")
    if manifest.get("schema_version") != "school-capability-blind-bundle/v1" or not isinstance(files, dict):
        raise ValueError("blind bundle manifest schema is invalid")
    actual = {path.relative_to(bundle_dir).as_posix() for path in bundle_dir.rglob("*") if path.is_file() and path.name != "bundle-manifest.json"}
    if actual != set(files):
        raise ValueError("blind bundle whitelist differs from manifest")
    for relative, expected in files.items():
        path = bundle_dir / relative
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"blind bundle file hash mismatch: {relative}")
        normalized = path.read_text(encoding="utf-8").lower().replace("_", " ").replace("-", " ")
        if any(marker in normalized for marker in ("feedback", "labels", "report", "known facts")):
            raise ValueError(f"forbidden revealed content in blind bundle: {relative}")
    bundle_hash = hashlib.sha256(
        json.dumps(dict(sorted(files.items())), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if manifest.get("bundle_sha256") != bundle_hash:
        raise ValueError("blind bundle hash mismatch")
    rule_file = _read_json(bundle_dir / "rule-snapshot.json")
    if rule_file.get("rule_snapshot_id") != snapshot.get("rule_snapshot_id"):
        raise ValueError("prospective rule snapshot identity mismatch")
    return {
        "status": "VALID_READ_ONLY",
        "new_case_count": 0,
        "message": "本轮无新增前瞻样本",
        "bundle_sha256": manifest["bundle_sha256"],
        "rule_snapshot_id": snapshot["rule_snapshot_id"],
        "rule_snapshot_policy": "旧版本身份已保留；Task 7 新规则须使用新 intake、新 snapshot 和新目标目录",
        "next_intake_command_template": "python -m tools.school_capability_dataset prospective-intake --input <new-case>/input.md --tasks <new-task-catalog.json> --school <school> --operator <human> --out <new-intake.json>",
        "next_bundle_command_template": "python -m tools.school_capability_dataset prepare-blind --intake <new-intake.json> --tasks <new-task-catalog.json> --rule-snapshot <new-rule-snapshot.json> --target-dir <new-nonexistent-bundle-dir>",
    }


def _gate_status(scores: Mapping[str, Any]) -> tuple[str, list[str]]:
    gate = scores.get("computed_gate_evidence", {})
    reasons = [name for name, value in gate.items() if value is False]
    if not gate.get("provenance_valid", False):
        return "STOP", ["artifact provenance or digest invalid", *reasons]
    return "HOLD", reasons or ["historical evidence does not authorize production routing"]


def build_final_baseline(
    *, historical_batch: dict[str, Any], stage_b_inputs: dict[str, Any], scores: dict[str, Any], prospective: dict[str, Any], generated_at: str,
) -> dict[str, Any]:
    run = FrozenBlindRun.from_dict(historical_batch["frozen_run"])
    verify_frozen_run(run)
    unsigned_scores = dict(scores)
    score_digest = unsigned_scores.pop("artifact_digest", None)
    if score_digest != f"sha256:{canonical_digest(unsigned_scores)}":
        raise ValueError("scores artifact digest mismatch")
    gate_status, gate_reasons = _gate_status(scores)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "classification": "historical_blind_candidate",
        "task_catalog_identity": run.task_catalog_version,
        "rule_snapshot_identity": run.rule_snapshot_id,
        "freeze_hash": run.freeze_hash,
        "case_count": len(historical_batch["cases"]),
        "labelled_case_count": len({row["case_id"] for row in stage_b_inputs["labels"]["labels"]}),
        "label_count": len(stage_b_inputs["labels"]["labels"]),
        "expected_schools": list(APPROVED_SCHOOLS),
        "task_ids": list(APPROVED_TASK_IDS),
        "state_counts": scores["state_counts"],
        "scores": scores["scores"],
        "posteriors": scores["posteriors"],
        "incremental_gains": scores["incremental_gains"],
        "experiment_summary": scores["experiment_summary"],
        "gate_status": gate_status,
        "gate_reasons": gate_reasons,
        "gate_evidence": scores["computed_gate_evidence"],
        "failure_classification_counts": scores["failure_classification_counts"],
        "failure_records": scores["failure_records"],
        "provenance": {
            **scores["provenance"],
            "scores_artifact_digest": scores["artifact_digest"],
            "historical_input": "cases/shuru-input.md",
            "historical_labels": "META/school-capability-historical-labels-2026-07-14.json",
            "historical_reviewed_manifest": "META/school-capability-reviewed-manifest-2026-07-14.json",
            "historical_timing_notice": "historical feedback predates the current six-runner refreeze; this is not a true prospective blind test",
        },
        "prospective_status": prospective,
    }
    payload["artifact_digest"] = f"sha256:{canonical_digest(payload)}"
    return payload


def render_final_markdown(payload: Mapping[str, Any]) -> str:
    posteriors = payload["posteriors"]
    posterior_lines = [
        f"| {row['school_id']} | {row['task_id']} | {row['evidence_completeness_band']} | {row['n_eff']:.3f} | {row['posterior_mean']:.3f} | [{row['credible_interval'][0]:.3f}, {row['credible_interval'][1]:.3f}] |"
        for row in posteriors
    ] or ["| — | — | — | 0 | — | — |"]
    state_by_school_task = Counter((row["school_id"], row["task_id"], row["state"]) for row in payload["scores"])
    coverage_lines = []
    for school in APPROVED_SCHOOLS:
        for task in APPROVED_TASK_IDS:
            coverage_lines.append(
                f"| {school} | {task} | {state_by_school_task[(school, task, 'claim')]} | {state_by_school_task[(school, task, 'abstain')]} | {state_by_school_task[(school, task, 'unsupported')]} |"
            )
    experiment_lines = [f"- `{name}`：{value:.6f}" for name, value in sorted(payload["experiment_summary"].items())] or ["- 无可评分实验效用。"]
    failure_lines = [f"- `{name}`：{count}" for name, count in sorted(payload["failure_classification_counts"].items())]
    gate_reasons = [f"- {reason}" for reason in payload["gate_reasons"]]
    prospective = payload["prospective_status"]
    return "\n".join([
        "# 六个月学派能力历史隔离基线（2026-07-15）",
        "",
        "## 判定摘要",
        "- **artifact validity**：GO；阶段 A 冻结哈希、阶段 B 标签绑定、评分摘要与制品摘要均已校验。本处 GO 只表示本轮历史隔离基线链有效。",
        f"- **capability evidence**：形成 {len(posteriors)} 个非空后验切片；宽区间、低样本或单类标签仍须按 HOLD 理解。",
        f"- **routing readiness**：**{payload['gate_status']}**；本任务不运行 learned/static 门禁，也不切换默认路由。",
        "- **prospective evidence**：本批仍为 historical_blind_candidate，重冻不会升级为 prospective 或 E3。",
        *gate_reasons,
        "",
        "## 数据来源与历史隔离属性",
        "- 命盘输入来自既有历史汇总并保持原去重结果；预测阶段只消费 case identity、性别、四柱、出生时间、大运、任务目录和规则快照。",
        "- 标签只来自 2026-07-14 已有人工审核标签，未新增标签、负例或 prospective 身份。",
        "- **历史反馈早于当前六来源 runner 预测**；本次只是用新 runner 重冻历史输入，不是真实前瞻盲测。",
        f"- freeze hash：`{payload['freeze_hash']}`",
        f"- artifact digest：`{payload['artifact_digest']}`",
        "",
        "## 六来源 × 十任务三态覆盖",
        "| 学派 | 任务 | claim | abstain | unsupported |",
        "|---|---|---:|---:|---:|",
        *coverage_lines,
        "",
        "覆盖增加、Claim 数量或规则数量不等于准确率提升。",
        "",
        "## 非空后验及可信区间",
        "| 学派 | 任务 | 证据完整度 | N_eff | 后验均值 | 95% CI |",
        "|---|---|---|---:|---:|---|",
        *posterior_lines,
        "",
        "## 四组增量实验摘要",
        *experiment_lines,
        "",
        "增量只表示同一历史标签集上的评估差异；runner 增加不会自动构成能力提升。",
        "",
        "## 高风险假阳性与不可评估项",
        f"- 高风险假阳性分类数：{payload['failure_classification_counts'].get('high_risk_false_positive', 0)}。",
        "- 未达到 A 级与双审要求的高风险标签保持不可评分；没有把门槛降级。",
        "- 无标签、只有正例、缺逐年流年或校准样本不足的切片保持 HOLD。",
        "",
        "## 失败分类",
        *failure_lines,
        "- `leakage` 一旦非零应整批 STOP；本轮最终制品要求其为零。",
        "",
        "## 与 2026-07-14 基线的可比变化",
        "- 旧基线只冻结 ziping/ren 与更广的 19 任务矩阵；本轮按唯一目录筛选十任务并扩展为六来源。",
        "- 本轮新增 runner 的三态覆盖只说明可执行范围变化，不自动说明准确率、校准或生产效用提升。",
        "- 标签仍主要覆盖既有职业与婚恋事件任务；Tasks 3—5 新增高风险任务缺少合格人工标签，不能进行能力升级声明。",
        "",
        "## 标签与输入限制",
        "- 不补造负例，因此部分任务只有正例，缺少判别力。",
        "- 历史输入没有逐年流年序列；任/段 timing runner 的 abstain 属于正确克制，但使应期任务不可评估。",
        "- 出生时间或大运缺失的案例保留在矩阵中并进入 input_completeness/partial 记录，没有删除异常样本改善分数。",
        "",
        "## Prospective 状态",
        f"- {prospective['status']}；{prospective['message']}。",
        f"- 旧 bundle hash：`{prospective['bundle_sha256']}`；旧规则身份：`{prospective['rule_snapshot_id']}`，未静默改写。",
        f"- 下一批 intake 模板：`{prospective['next_intake_command_template']}`",
        f"- 下一批 bundle 模板：`{prospective['next_bundle_command_template']}`",
        "",
        "## 下一不可逆决策",
        "**不能由 Task 8 直接进入生产路由或宣称 Task 9 已 GO。** 当前 routing readiness 为 HOLD；只有后续获得真实竞争覆盖、负例判别力、可评估高风险任务和足够校准样本后，才可单独执行 Task 9 learned/static 留出竞争。",
        "",
    ])


def _stage_a_command(args: argparse.Namespace) -> None:
    root = Path(args.out_dir)
    if root.exists():
        raise ValueError("Stage A output directory must not exist")
    result = build_stage_a(source=Path(args.source), catalog_path=Path(args.catalog), rules_path=Path(args.rules), frozen_at=args.frozen_at)
    root.mkdir(parents=True)
    _atomic_json(root / "historical-batch.json", result["historical_batch"])
    _atomic_json(root / "outputs.json", {"schema_version": "school-capability-outputs/v1", "outputs": result["historical_batch"]["frozen_run"]["outputs"]})
    _atomic_json(root / "tasks.json", result["cli_tasks"])
    _atomic_json(root / "freeze-tasks.json", result["freeze_tasks"])
    _atomic_json(root / "rule-snapshot.json", result["rule_snapshot"])
    _atomic_json(root / "frozen-run.json", result["historical_batch"]["frozen_run"])
    print(result["historical_batch"]["frozen_run"]["freeze_hash"])


def _stage_b_command(args: argparse.Namespace) -> None:
    root = Path(args.stage_a_dir)
    batch = _read_json(root / "historical-batch.json")
    run = FrozenBlindRun.from_dict(batch["frozen_run"])
    verify_frozen_run(run)  # Must happen before the next two reads.
    labels = _read_json(Path(args.labels))
    reviewed = _read_json(Path(args.reviewed_manifest))
    inputs = build_stage_b_inputs(historical_batch=batch, cli_tasks=_read_json(root / "tasks.json"), labels_doc=labels, reviewed_manifest=reviewed, evaluated_at=args.evaluated_at)
    scores = score_stage_b(historical_batch=batch, cli_tasks=_read_json(root / "tasks.json"), stage_b_inputs=inputs, evaluated_at=args.evaluated_at)
    out = Path(args.out_dir)
    if out.exists():
        raise ValueError("Stage B output directory must not exist")
    out.mkdir(parents=True)
    _atomic_json(out / "reviewed-manifest.json", inputs["manifest"])
    _atomic_json(out / "bound-labels.json", inputs["labels"])
    _atomic_json(out / "stage-b-inputs.json", inputs)
    _atomic_json(out / "scores.json", scores)
    print(scores["artifact_digest"])


def _finalize_command(args: argparse.Namespace) -> None:
    stage_a = Path(args.stage_a_dir)
    stage_b = Path(args.stage_b_dir)
    prospective = audit_prospective(intake_path=Path(args.prospective_intake), bundle_dir=Path(args.prospective_bundle), snapshot_path=Path(args.prospective_snapshot))
    payload = build_final_baseline(
        historical_batch=_read_json(stage_a / "historical-batch.json"),
        stage_b_inputs=_read_json(stage_b / "stage-b-inputs.json"),
        scores=_read_json(stage_b / "scores.json"),
        prospective=prospective,
        generated_at=args.generated_at,
    )
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    if json_path.exists() or md_path.exists():
        raise ValueError("final output must not overwrite an existing artifact")
    _atomic_json(json_path, payload)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_final_markdown(payload), encoding="utf-8")
    print(payload["artifact_digest"])


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    stage_a = commands.add_parser("stage-a")
    stage_a.add_argument("--source", required=True)
    stage_a.add_argument("--catalog", required=True)
    stage_a.add_argument("--rules", required=True)
    stage_a.add_argument("--frozen-at", required=True)
    stage_a.add_argument("--out-dir", required=True)
    stage_a.set_defaults(handler=_stage_a_command)
    stage_b = commands.add_parser("stage-b")
    stage_b.add_argument("--stage-a-dir", required=True)
    stage_b.add_argument("--labels", required=True)
    stage_b.add_argument("--reviewed-manifest", required=True)
    stage_b.add_argument("--evaluated-at", required=True)
    stage_b.add_argument("--out-dir", required=True)
    stage_b.set_defaults(handler=_stage_b_command)
    final = commands.add_parser("finalize")
    final.add_argument("--stage-a-dir", required=True)
    final.add_argument("--stage-b-dir", required=True)
    final.add_argument("--prospective-intake", required=True)
    final.add_argument("--prospective-bundle", required=True)
    final.add_argument("--prospective-snapshot", required=True)
    final.add_argument("--generated-at", required=True)
    final.add_argument("--json-out", required=True)
    final.add_argument("--md-out", required=True)
    final.set_defaults(handler=_finalize_command)
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
