from __future__ import annotations

import json
import re
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from .models import CaseAuditRecord

_EXPLICIT_CONTAMINATION = ("反馈校准", "既有反馈", "已验")
_UNCERTAIN_CONTAMINATION = ("过往情况", "已知情况", "事实参考", "反馈内容")
_KNOWN_FACT_MARKERS = ("命主反馈", "实际情况", "已发生", "已验证")
_RULE_DEVELOPMENT_MARKERS = ("规则开发", "规则校准", "开发样本", "训练样本")
_BIRTH_INPUT_PATTERN = re.compile(r"(?:四柱|八字)\s*[：:]\s*\S+")
_QUANTIFIABLE_FEEDBACK_PATTERNS = (
    re.compile(r"\b(?:19|20)\d{2}\b"),
    re.compile(r"(?:通过|未通过|录取|未录取|结婚|离婚|入职|离职|确诊|发生|结果)"),
)


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _matching_reports(case_id: str, reports_dir: Path) -> list[Path]:
    if not reports_dir.is_dir():
        return []
    return sorted(path for path in reports_dir.glob(f"{case_id}*.md") if path.is_file())


def audit_case(case_dir: Path, reports_dir: Path) -> CaseAuditRecord:
    case_id = case_dir.name
    input_path = case_dir / "input.md"
    feedback_path = case_dir / "feedback.md"
    analysis_path = case_dir / "analysis.md"
    statement_index_path = case_dir / "statement_index.json"

    has_input = input_path.is_file()
    has_feedback = feedback_path.is_file()
    has_statement_index = statement_index_path.is_file()
    report_paths = _matching_reports(case_id, reports_dir)
    has_existing_report = bool(report_paths)

    input_text = _read_text(input_path)
    feedback_text = _read_text(feedback_path)
    inspected_outputs = [(analysis_path, _read_text(analysis_path))]
    inspected_outputs.extend((path, _read_text(path)) for path in report_paths)

    feedback_quantifiable = has_feedback and all(
        pattern.search(feedback_text) for pattern in _QUANTIFIABLE_FEEDBACK_PATTERNS
    )
    flags: list[str] = []
    notes: list[str] = []
    uncertain = False

    if not has_input or not _BIRTH_INPUT_PATTERN.search(input_text):
        flags.append("missing_birth_input")
        notes.append("input.md is absent or has no recognizable 四柱/八字 field")
    if not has_feedback:
        flags.append("missing_feedback")
        notes.append("feedback.md is absent")
    elif not feedback_quantifiable:
        flags.append("unstructured_feedback")
        notes.append("feedback exists but lacks both a year and a recognizable outcome")

    if any(marker in input_text for marker in _KNOWN_FACT_MARKERS):
        flags.append("known_facts_embedded_in_input")
        notes.append("input contains an explicit known-fact marker")
    if any(marker in input_text for marker in _RULE_DEVELOPMENT_MARKERS):
        flags.append("rule_development_reference")
        notes.append("input identifies the case as rule-development material")

    for path, text in inspected_outputs:
        explicit = sorted(marker for marker in _EXPLICIT_CONTAMINATION if marker in text)
        if explicit:
            if "feedback_calibrated_report" not in flags:
                flags.append("feedback_calibrated_report")
            notes.append(f"{path.name} contains explicit contamination marker(s): {', '.join(explicit)}")
        uncertain_markers = sorted(marker for marker in _UNCERTAIN_CONTAMINATION if marker in text)
        if uncertain_markers:
            uncertain = True
            notes.append(f"{path.name} contains uncertain contamination marker(s): {', '.join(uncertain_markers)}")

    if "feedback_calibrated_report" in flags or "known_facts_embedded_in_input" in flags or "rule_development_reference" in flags:
        eligibility = "development_only"
    elif "missing_birth_input" in flags or "missing_feedback" in flags or "unstructured_feedback" in flags:
        eligibility = "not_scorable"
    elif uncertain:
        eligibility = "manual_review"
    else:
        eligibility = "manual_review"
        notes.append("no explicit contamination found; provenance requires human confirmation")

    return CaseAuditRecord(
        case_id=case_id,
        has_input=has_input,
        has_feedback=has_feedback,
        has_statement_index=has_statement_index,
        has_existing_report=has_existing_report,
        feedback_quantifiable=feedback_quantifiable,
        contamination_flags=flags,
        eligibility=eligibility,
        evidence_notes=notes,
    )


def audit_cases(cases_dir: Path, reports_dir: Path) -> list[CaseAuditRecord]:
    if not cases_dir.is_dir():
        return []
    return [
        audit_case(case_dir, reports_dir)
        for case_dir in sorted(path for path in cases_dir.iterdir() if path.is_dir())
    ]


def write_case_manifest(records: Sequence[CaseAuditRecord], path: Path) -> None:
    payload = {
        "schema_version": "school-capability-case-manifest/v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "records": [record.to_dict() for record in records],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
