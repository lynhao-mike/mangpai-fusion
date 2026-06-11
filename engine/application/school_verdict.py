from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SchoolVerdictMatrix:
    case_id: str
    schools: list[dict[str, Any]]
    parallel_domains: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "schools": self.schools,
            "parallel_domains": self.parallel_domains,
            "conflicts": self.conflicts,
        }


def build_school_verdict_matrix(output: dict[str, Any]) -> SchoolVerdictMatrix:
    case_id = str(output.get("case_id") or "UNKNOWN")
    schools = _extract_school_rows(output)
    parallel_domains = _extract_parallel_domains(output)
    conflicts = _extract_conflicts(output)
    return SchoolVerdictMatrix(
        case_id=case_id,
        schools=schools,
        parallel_domains=parallel_domains,
        conflicts=conflicts,
    )


def _extract_school_rows(output: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, label in (
        ("theory_findings", "theory"),
        ("blind_findings", "blind"),
        ("fusion_findings", "fusion"),
    ):
        data = output.get(key)
        if not isinstance(data, dict):
            rows.append(_missing_row(label, key))
            continue
        rows.append(
            {
                "school": label,
                "source": key,
                "available": True,
                "summary": _summary_from_findings(data),
                "confidence": _confidence_from_findings(data),
                "evidence_rule_ids": _rule_ids_from_findings(data),
            }
        )
    return rows


def _missing_row(label: str, key: str) -> dict[str, Any]:
    return {
        "school": label,
        "source": key,
        "available": False,
        "summary": "missing",
        "confidence": None,
        "evidence_rule_ids": [],
    }


def _summary_from_findings(data: dict[str, Any]) -> Any:
    for key in ("summary", "conclusions", "final_conclusion", "dominant_patterns"):
        value = data.get(key)
        if value:
            return value
    return "available_without_summary"


def _confidence_from_findings(data: dict[str, Any]) -> Any:
    for key in ("confidence_summary", "fusion_confidence", "confidence", "overall_confidence"):
        value = data.get(key)
        if value:
            return value
    return None


def _rule_ids_from_findings(data: dict[str, Any]) -> list[str]:
    rule_ids: list[str] = []
    for key in ("evidence_rule_ids", "rule_ids", "participating_rule_ids"):
        value = data.get(key)
        if isinstance(value, list):
            rule_ids.extend(str(v) for v in value)
    for item in data.get("conclusions") or []:
        if isinstance(item, dict):
            evidence = item.get("evidence_rule_ids") or item.get("rule_ids") or []
            if isinstance(evidence, list):
                rule_ids.extend(str(v) for v in evidence)
    return sorted(set(rule_ids))


def _extract_parallel_domains(output: dict[str, Any]) -> list[dict[str, Any]]:
    parallel = output.get("parallel_analysis")
    if not isinstance(parallel, dict):
        return []
    domains = parallel.get("domains") or parallel.get("domain_analyses") or []
    rows: list[dict[str, Any]] = []
    if isinstance(domains, dict):
        domain_iter = domains.values()
    elif isinstance(domains, list):
        domain_iter = domains
    else:
        domain_iter = []
    for item in domain_iter:
        if not isinstance(item, dict):
            continue
        consensus = item.get("consensus") if isinstance(item.get("consensus"), dict) else {}
        rows.append(
            {
                "domain": item.get("domain") or consensus.get("domain"),
                "consensus": consensus or item.get("adjudication") or {},
                "readings": item.get("readings") or [],
            }
        )
    return rows


def _extract_conflicts(output: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts = output.get("conflicts") or []
    if not isinstance(conflicts, list):
        return []
    return [dict(item) for item in conflicts if isinstance(item, dict)]
