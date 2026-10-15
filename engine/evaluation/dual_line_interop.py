from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FieldDifference:
    statement_key: str
    field_path: str
    compatibility_value: object
    v5_value: object
    classification: str = "human_adjudication_blocker"


@dataclass(frozen=True)
class DualLineDiffReport:
    case_id: str
    input_sha256: str
    differences: list[FieldDifference] = field(default_factory=list)
    adjudication_blockers: list[FieldDifference] = field(default_factory=list)


def build_diff_report(
    *,
    case_id: str,
    input_sha256: str,
    differences: list[FieldDifference],
) -> DualLineDiffReport:
    """Keep all observed field differences; no similarity-based reconciliation."""
    blockers = [difference for difference in differences]
    return DualLineDiffReport(
        case_id=case_id,
        input_sha256=input_sha256,
        differences=list(differences),
        adjudication_blockers=blockers,
    )


def archive_diff_report(report: DualLineDiffReport, destination: str | Path) -> Path:
    """Create one JSON diff artifact without overwriting an existing archive."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    differences = [
        {
            "statement_key": item.statement_key,
            "field_path": item.field_path,
            "compatibility_value": item.compatibility_value,
            "v5_value": item.v5_value,
            "classification": item.classification,
        }
        for item in report.differences
    ]
    payload = {
        "case_id": report.case_id,
        "input_sha256": report.input_sha256,
        "differences": differences,
        "adjudication_blockers": [
            {
                "statement_key": item.statement_key,
                "field_path": item.field_path,
                "compatibility_value": item.compatibility_value,
                "v5_value": item.v5_value,
                "classification": item.classification,
            }
            for item in report.adjudication_blockers
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(encoded)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def _value(item: Any, name: str, default: Any = None) -> Any:
    return item.get(name, default) if isinstance(item, dict) else getattr(item, name, default)


def _rule_ids(item: Any, *, compatibility: bool) -> set[str]:
    evidence = _value(item, "evidence", []) or []
    identities: set[str] = set()
    for record in evidence:
        values = [_value(record, "rule_id", "")] if compatibility else (_value(record, "rule_ids", []) or [])
        identities.update(str(value).strip() for value in values if str(value).strip())
    return identities


def _claim_rows(output: Any, *, compatibility: bool) -> list[Any]:
    rows = _value(output, "final_conclusions" if compatibility else "claims", []) or []
    return list(rows)


def _raw_claim_value(item: Any, field_name: str, *, compatibility: bool) -> Any:
    if field_name == "statement":
        return _value(item, "statement" if compatibility else "claim")
    return _value(item, field_name)


def compare_dual_line_outputs(
    *,
    case_id: str,
    input_sha256: str,
    compatibility_output: Any,
    v5_output: Any,
) -> DualLineDiffReport:
    """Compare claims only when a rule identity uniquely links both outputs."""
    compatibility = _claim_rows(compatibility_output, compatibility=True)
    v5 = _claim_rows(v5_output, compatibility=False)
    compatibility_ids = [_rule_ids(row, compatibility=True) for row in compatibility]
    v5_ids = [_rule_ids(row, compatibility=False) for row in v5]

    candidates: dict[tuple[int, int], set[str]] = {}
    for left_index, left_ids in enumerate(compatibility_ids):
        for right_index, right_ids in enumerate(v5_ids):
            shared = left_ids & right_ids
            if shared:
                candidates[(left_index, right_index)] = shared

    left_matches: dict[int, list[int]] = {}
    right_matches: dict[int, list[int]] = {}
    for left_index, right_index in candidates:
        left_matches.setdefault(left_index, []).append(right_index)
        right_matches.setdefault(right_index, []).append(left_index)
    matched = {
        pair
        for pair in candidates
        if len(left_matches[pair[0]]) == 1 and len(right_matches[pair[1]]) == 1
    }

    differences: list[FieldDifference] = []
    matched_left = {left for left, _ in matched}
    matched_right = {right for _, right in matched}
    comparable_fields = ("statement", "domain", "direction", "rule_direction", "polarity")
    for left_index, right_index in sorted(matched):
        left, right = compatibility[left_index], v5[right_index]
        identities = sorted(candidates[(left_index, right_index)])
        statement_key = "rule:" + ",".join(identities)
        for field_name in comparable_fields:
            left_value = _raw_claim_value(left, field_name, compatibility=True)
            right_value = _raw_claim_value(right, field_name, compatibility=False)
            if left_value is not None and right_value is not None and left_value != right_value:
                differences.append(FieldDifference(
                    statement_key=statement_key,
                    field_path=field_name,
                    compatibility_value=left_value,
                    v5_value=right_value,
                ))

    for left_index, row in enumerate(compatibility):
        if left_index not in matched_left:
            key = str(_value(row, "conclusion_id", f"compatibility:{left_index}"))
            differences.append(FieldDifference(
                statement_key=f"compatibility:{key}",
                field_path="statement",
                compatibility_value=_raw_claim_value(row, "statement", compatibility=True),
                v5_value=None,
            ))
    for right_index, row in enumerate(v5):
        if right_index not in matched_right:
            key = str(_value(row, "claim_id", f"v5:{right_index}"))
            differences.append(FieldDifference(
                statement_key=f"v5:{key}",
                field_path="statement",
                compatibility_value=None,
                v5_value=_raw_claim_value(row, "statement", compatibility=False),
            ))

    return build_diff_report(
        case_id=case_id,
        input_sha256=input_sha256,
        differences=differences,
    )


def blind_compatibility_input(parsed: Any) -> Any:
    """Clone parsed input and remove retrospective facts/questions from blind context."""
    blind = deepcopy(parsed)
    blind.known_facts = []
    blind.questions = []
    metadata = getattr(blind, "case_meta", None)
    if not isinstance(metadata, dict):
        raise ValueError("case_meta must be a dict for blind compatibility execution")
    blind.case_meta = {
        key: value
        for key, value in metadata.items()
        if str(key).strip().casefold() not in {"feedback", "known_facts", "known facts", "核验", "反馈", "已知事实"}
    }
    return blind


def blind_input_sha256(value: object) -> str:
    """Hash a canonical blind input mapping; key order does not affect identity."""
    try:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("blind input must be finite, JSON-serializable data") from error
    return hashlib.sha256(payload).hexdigest()


def admit_v004_bundle(bundle_root: str | Path, *, expected_case_id: str) -> Path:
    """Accept only the explicitly named v004 blind-bundle directory."""
    root = Path(bundle_root)
    if not expected_case_id or not root.name.startswith(f"{expected_case_id}--"):
        raise ValueError("bundle case identifier is not approved")
    expected_name = f"{expected_case_id}--blind-bundle--v004"
    if root.name != expected_name:
        raise ValueError("only the exact v004 blind-bundle root is admitted")
    if not root.is_dir():
        raise ValueError("v004 blind-bundle root must be an existing directory")
    return root


@dataclass(frozen=True)
class DualLineRun:
    case_id: str
    input_sha256: str
    compatibility_output: Any
    v5_snapshot: Any
    decision_run: Any
    diff_report: DualLineDiffReport
    trace_issues: list[str] = field(default_factory=list)
    differences: list[FieldDifference] = field(default_factory=list)
    adjudication_blockers: list[FieldDifference] = field(default_factory=list)


def _chart_from_parsed(parsed: Any, *, case_id: str) -> dict[str, Any]:
    bazi = getattr(parsed, "bazi", None)
    if bazi is None or not callable(getattr(bazi, "all_pillars", None)):
        raise ValueError("parsed input must provide a structured Bazi chart")
    pillars = {name: f"{pillar.gan}{pillar.zhi}" for name, pillar in bazi.all_pillars()}
    english_names = {"年": "year", "月": "month", "日": "day", "时": "hour"}
    if set(pillars) != set(english_names):
        raise ValueError("parsed input must provide all four pillars")
    return {
        "case_id": case_id,
        "pillars": {english_names[name]: pillars[name] for name in english_names},
    }


def _blind_v5_chart(chart: dict[str, Any], *, case_id: str) -> dict[str, Any]:
    blind_chart = deepcopy(chart)
    for key in ("known_facts", "known facts", "questions", "feedback", "outcomes"):
        blind_chart.pop(key, None)
    blind_chart["case_id"] = case_id
    return blind_chart


def run_dual_line(
    *,
    case_id: str,
    parsed_input: Any,
    chart: dict[str, Any] | None = None,
    approved_case_ids: frozenset[str],
    workspace_root: str | Path = ".",
) -> DualLineRun:
    """Run both cores on isolated blind inputs without invoking production e2e side effects."""
    if not case_id or case_id not in approved_case_ids:
        raise ValueError(f"case_id {case_id!r} is not in the dual-line allowlist")
    if str(getattr(parsed_input, "case_id", "")) != case_id:
        raise ValueError("parsed input case identifier does not match the approved case")

    if chart is not None and not isinstance(chart, dict):
        raise ValueError("V5 chart must be a mapping")
    if chart is not None and str(chart.get("case_id", case_id)) != case_id:
        raise ValueError("V5 chart case identifier does not match the approved case")
    v5_chart = _blind_v5_chart(
        chart if chart is not None else _chart_from_parsed(parsed_input, case_id=case_id),
        case_id=case_id,
    )
    input_hash = blind_input_sha256(v5_chart)

    compatibility_input = blind_compatibility_input(parsed_input)
    from engine.application.pipeline_runner import run_pipeline
    compatibility_output = run_pipeline(
        compatibility_input,
        cases_dir=Path(workspace_root) / "cases",
        write_findings=False,
    )

    from engine.v5.runner import run_v5
    from engine.v5.domain import V5RunSnapshot
    from engine.decision.v5_adapter import decision_run_from_snapshot

    v5_output = run_v5(v5_chart, case_id=case_id, workspace_root=str(workspace_root))
    snapshot = V5RunSnapshot.from_output(v5_output)
    decision_run = decision_run_from_snapshot(snapshot)
    if decision_run.case_id != case_id or decision_run.run_id != snapshot.run_id:
        raise ValueError("DecisionRun case_id or run_id does not match the V5 snapshot")
    validate_dual_line_trace(decision_run)
    diff_report = compare_dual_line_outputs(
        case_id=case_id,
        input_sha256=input_hash,
        compatibility_output=compatibility_output,
        v5_output=v5_output,
    )
    return DualLineRun(
        case_id=case_id,
        input_sha256=input_hash,
        compatibility_output=compatibility_output,
        v5_snapshot=snapshot,
        decision_run=decision_run,
        diff_report=diff_report,
        differences=diff_report.differences,
        adjudication_blockers=diff_report.adjudication_blockers,
    )


def validate_dual_line_trace(decision_run: Any) -> None:
    """Require a complete DecisionRun trace before exposing an interop result."""
    validate = getattr(decision_run, "validate_trace", None)
    if not callable(validate):
        raise ValueError("DecisionRun trace validator is required")
    issues = validate()
    if issues:
        raise ValueError("DecisionRun trace validation failed: " + "; ".join(map(str, issues)))


def statement_records_v2_for_conclusions(
    output: Any,
    *,
    case_id: str,
    run_id: str,
) -> dict[str, Any]:
    """Build strict v2 records, requiring identity absent from legacy conclusions."""
    from engine.statement_runtime import build_statement_records_v2_envelope

    rows: list[dict[str, Any]] = []
    for conclusion in getattr(output, "final_conclusions", []):
        evidence = []
        for item in getattr(conclusion, "evidence", []) or []:
            rule_id = str(getattr(item, "rule_id", "") or "").strip()
            school = str(getattr(item, "school", "") or "").strip()
            if rule_id and school:
                evidence.append({"rule_id": rule_id, "school": school})
        rows.append({
            "statement": getattr(conclusion, "statement", ""),
            "matter_category": getattr(conclusion, "matter_category", ""),
            "rule_direction": getattr(conclusion, "rule_direction", ""),
            "section": getattr(conclusion, "section", ""),
            "evidence": evidence,
            "star": getattr(getattr(conclusion, "confidence", None), "star", 0),
            "percent": getattr(getattr(conclusion, "confidence", None), "percent", 0.0),
        })
    return build_statement_records_v2_envelope(
        {"production_rule_conclusions": rows}, case_id, run_id=run_id
    )


