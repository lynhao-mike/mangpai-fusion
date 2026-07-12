"""Prepare reviewed school-capability evaluation data without running inference."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.evaluation.case_audit import audit_cases

_INVENTORY_SCHEMA = "school-capability-case-inventory/v1"
_DECISIONS_SCHEMA = "school-capability-review-decisions/v1"
_LABELS_SCHEMA = "school-capability-labels-unbound/v1"
_CLEAN = {"historical_blind", "prospective"}
_REQUIRED_LABEL_FIELDS = {
    "case_id", "task_id", "label", "source", "observed_at", "confidence_grade",
    "quantifiable", "conflict_state", "reviewer",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _decision_map(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if document.get("schema_version") != _DECISIONS_SCHEMA or not isinstance(document.get("records"), list):
        raise ValueError(f"review decisions must use {_DECISIONS_SCHEMA}")
    result: dict[str, dict[str, Any]] = {}
    for item in document["records"]:
        if not isinstance(item, dict) or not isinstance(item.get("case_id"), str) or item["case_id"] in result:
            raise ValueError("review decisions require unique case_id records")
        result[item["case_id"]] = item
    return result


def build_inventory(cases_dir: Path, reports_dir: Path, review_decisions: dict[str, Any]) -> dict[str, Any]:
    decisions = _decision_map(review_decisions)
    records = []
    for audit in audit_cases(cases_dir, reports_dir):
        decision = decisions.get(audit.case_id, {})
        explicit_contamination = audit.eligibility == "development_only"
        requested = decision.get("classification")
        reviewer = decision.get("reviewed_by")
        human_clean = (
            requested in _CLEAN
            and isinstance(reviewer, str) and bool(reviewer.strip())
            and not reviewer.lower().startswith(("automated", "agent", "ai-"))
            and isinstance(decision.get("reviewed_at"), str) and decision["reviewed_at"].endswith("Z")
            and isinstance(decision.get("provenance_evidence"), list)
            and any(isinstance(item, str) and ":" in item for item in decision["provenance_evidence"])
        )
        evidence = list(audit.contamination_flags)
        if not human_clean:
            evidence.append("human_clean_review_missing")
        if explicit_contamination:
            classification = "development_only"
        elif audit.eligibility == "not_scorable":
            classification = "not_scorable"
        elif human_clean:
            classification = requested
        else:
            classification = "development_only"
        records.append({
            "case_id": audit.case_id,
            "birth_info_complete": audit.has_input and "missing_birth_input" not in audit.contamination_flags,
            "feedback_present": audit.has_feedback,
            "feedback_grade": decision.get("feedback_grade", "unreviewed"),
            "development_contaminated": classification not in _CLEAN,
            "contamination_evidence": sorted(set(evidence)),
            "classification": classification,
            "notes": decision.get("notes", "; ".join(audit.evidence_notes)),
            "reviewed_by": decision.get("reviewed_by", ""),
            "reviewed_at": decision.get("reviewed_at", ""),
        })
    return {"schema_version": _INVENTORY_SCHEMA, "generated_at": _now(), "records": records}


def _task_map(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks = catalog.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("task catalog requires tasks")
    result = {item.get("task_id"): item for item in tasks if isinstance(item, dict)}
    if len(result) != len(tasks) or None in result:
        raise ValueError("task catalog requires unique task_id values")
    return result


def build_unbound_labels(observations: list[dict[str, Any]], task_catalog: dict[str, Any]) -> dict[str, Any]:
    tasks = _task_map(task_catalog)
    labels = []
    seen = set()
    for item in observations:
        if item.get("disposition") == "no_data":
            continue
        missing = _REQUIRED_LABEL_FIELDS - set(item)
        if missing:
            raise ValueError(f"label observation missing field: {sorted(missing)[0]}")
        task = tasks.get(item["task_id"])
        if task is None:
            raise ValueError(f"unknown task_id: {item['task_id']}")
        identity = item["case_id"], item["task_id"]
        if identity in seen:
            raise ValueError("duplicate label identity")
        seen.add(identity)
        for field in ("case_id", "task_id", "source", "observed_at", "confidence_grade", "reviewer"):
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(f"{field} must be a non-empty string")
        if type(item["quantifiable"]) is not bool:
            raise ValueError("quantifiable must be a boolean")
        if item["confidence_grade"] not in {"A", "B", "C"}:
            raise ValueError("confidence_grade must be A, B, or C")
        if item["conflict_state"] not in {"none", "conflicting_sources"}:
            raise ValueError("conflict_state is invalid")
        source = item["source"].replace("\\", "/")
        if not source.startswith(("cases/raw_feedback/source/", "cases/")) or any(marker in source for marker in ("reports/", "analysis.md", "school-claims", "statement_index")) or ":" not in source:
            raise ValueError("source must reference raw feedback or feedback.md with a line number")
        if item["conflict_state"] == "conflicting_sources" and item["quantifiable"]:
            raise ValueError("conflicting_sources label cannot be quantifiable")
        if task.get("high_risk") and (item.get("confidence_grade") != "A" or not item.get("secondary_reviewed_by")):
            raise ValueError("high-risk label requires A grade and secondary_reviewed_by")
        schema = task.get("label_schema", {})
        method = task.get("scoring_method")
        label = item["label"]
        if method == "binary_probability" and label not in {schema.get("positive_label"), schema.get("negative_label")}:
            raise ValueError("binary label does not match task schema")
        if method == "ordinal" and label not in schema.get("labels", []):
            raise ValueError("ordinal label does not match task schema")
        if method == "multiclass_probability" and label not in schema.get("labels", []):
            raise ValueError("categorical label does not match task schema")
        if method == "time_window":
            if not isinstance(label, dict) or type(label.get("occurred")) is not bool:
                raise ValueError("time_window label requires occurred boolean and year")
            year = label.get("year")
            if (label["occurred"] and type(year) is not int) or (not label["occurred"] and year is not None):
                raise ValueError("time_window year is invalid")
        labels.append({field: item[field] for field in _REQUIRED_LABEL_FIELDS})
    return {"schema_version": _LABELS_SCHEMA, "generated_at": _now(), "labels": labels}


def _write(path: Path, payload: dict[str, Any], dry_run: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if dry_run:
        print(text, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _inventory_command(args: argparse.Namespace) -> None:
    payload = build_inventory(Path(args.cases_dir), Path(args.reports_dir), _read_json(Path(args.review_decisions)))
    _write(Path(args.out), payload, args.dry_run)


def _labels_command(args: argparse.Namespace) -> None:
    observations = [json.loads(line) for line in Path(args.observations).read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = build_unbound_labels(observations, _read_json(Path(args.tasks)))
    _write(Path(args.out), payload, args.dry_run)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inventory = commands.add_parser("inventory")
    inventory.add_argument("--cases-dir", required=True)
    inventory.add_argument("--reports-dir", required=True)
    inventory.add_argument("--review-decisions", required=True)
    inventory.add_argument("--out", required=True)
    inventory.add_argument("--dry-run", action="store_true")
    inventory.set_defaults(handler=_inventory_command)
    labels = commands.add_parser("labels")
    labels.add_argument("--observations", required=True)
    labels.add_argument("--tasks", required=True)
    labels.add_argument("--out", required=True)
    labels.add_argument("--dry-run", action="store_true")
    labels.set_defaults(handler=_labels_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    args.handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
