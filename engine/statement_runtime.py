"""Statement runtime builder for production report rendering.

This module builds ``statement_record.v1`` artifacts from the structured report
rendering context. It is intentionally facts-only: it does not update family,
school, canon, or dynamic-confidence weights.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from engine import FINDINGS_SCHEMA_VERSION, __version__

SCHEMA_VERSION = "statement_record.v1"
SOURCE_RULE_VERSION = f"findings-schema:{FINDINGS_SCHEMA_VERSION}"

_REQUIRED_RECORD_FIELDS = (
    "statement_id",
    "case_id",
    "rule_id",
    "family_id",
    "school",
    "canon",
    "rule_type",
    "statement_text",
    "confidence_snapshot",
    "generated_at",
    "source_engine_version",
    "source_rule_version",
)

_RULE_PREFIX_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)*")


@dataclass(frozen=True)
class StatementRuntimeStats:
    """Runtime validation counters for generated statement records."""

    cases_generated: int
    statement_records_generated: int
    missing_field_count: int

    def to_dict(self) -> dict[str, int]:
        return {
            "cases_generated": self.cases_generated,
            "statement_records_generated": self.statement_records_generated,
            "missing_field_count": self.missing_field_count,
        }


def build_statement_records_envelope(
    ctx: Mapping[str, Any],
    case_id: str,
    *,
    generated_at: Optional[str] = None,
) -> dict[str, Any]:
    """Build the per-case ``statement_records.json`` envelope.

    One output statement emits one record in this v1 facts layer. When multiple
    evidence rules support the same visible statement, the first structured
    evidence rule is used as the runtime anchor so ``statement_id`` remains
    unique and directly joinable by feedback.
    """

    ts = generated_at or _utc_now()
    records: list[dict[str, Any]] = []
    seen_statement_ids: set[str] = set()
    for item in _iter_statement_items(ctx):
        statement_id = str(item.get("statement_id") or "").strip()
        if not statement_id:
            continue
        statement_text = _statement_text(item)
        if not statement_text or statement_id in seen_statement_ids:
            continue
        evidence = _evidence_items(item)
        if not evidence and item.get("rule_id"):
            evidence = [{"rule_id": str(item.get("rule_id")), "school": str(item.get("school", ""))}]
        ev = next((entry for entry in evidence if str(entry.get("rule_id") or "").strip()), None)
        if ev is None:
            continue
        rule_id = str(ev.get("rule_id") or "").strip()
        metadata = resolve_rule_metadata(rule_id, ev, item)
        record = {
            "statement_id": statement_id,
            "case_id": case_id,
            "rule_id": rule_id,
            "family_id": metadata["family_id"],
            "school": metadata["school"],
            "canon": metadata["canon"],
            "rule_type": metadata["rule_type"],
            "statement_text": statement_text,
            "confidence_snapshot": _confidence_snapshot(item),
            "generated_at": ts,
            "source_engine_version": __version__,
            "source_rule_version": SOURCE_RULE_VERSION,
        }
        records.append(record)
        seen_statement_ids.add(statement_id)

    stats = validate_statement_records(records)
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "generated_at": ts,
        "statement_records_generated": stats.statement_records_generated,
        "missing_field_count": stats.missing_field_count,
        "records": records,
    }


def write_statement_records(
    ctx: Mapping[str, Any],
    case_id: str,
    case_dir: str | Path,
) -> dict[str, Any]:
    """Build and write ``cases/<case_id>/statement_records.json``."""

    envelope = build_statement_records_envelope(ctx, case_id)
    path = Path(case_dir) / "statement_records.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(envelope, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        try:
            if path.read_text(encoding="utf-8") == text:
                return envelope
        except OSError:
            pass
    path.write_text(text, encoding="utf-8")
    return envelope


def validate_statement_records(records: Iterable[Mapping[str, Any]]) -> StatementRuntimeStats:
    """Count generated records and missing required fields."""

    total = 0
    missing = 0
    for record in records:
        total += 1
        for field in _REQUIRED_RECORD_FIELDS:
            value = record.get(field)
            if value in (None, "", []):
                missing += 1
        snapshot = record.get("confidence_snapshot")
        if not isinstance(snapshot, Mapping):
            missing += 1
        else:
            for field in ("star", "percent", "posterior_mean", "sample_n", "source"):
                if field not in snapshot or snapshot.get(field) in ("", []):
                    missing += 1
    return StatementRuntimeStats(
        cases_generated=1 if total else 0,
        statement_records_generated=total,
        missing_field_count=missing,
    )


def validation_summary(envelopes: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Aggregate generation validation for one or more case envelopes."""

    case_count = 0
    statement_total = 0
    missing_total = 0
    for envelope in envelopes:
        records = envelope.get("records", []) if isinstance(envelope, Mapping) else []
        if isinstance(records, list):
            case_count += 1
            statement_total += len(records)
            missing_total += validate_statement_records(records).missing_field_count
    return {
        "cases_generated": case_count,
        "statement_records_generated": statement_total,
        "missing_field_count": missing_total,
    }


def resolve_rule_metadata(
    rule_id: str,
    evidence: Mapping[str, Any] | None = None,
    statement_item: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Resolve immutable metadata for a generated statement record.

    The resolver uses stable production naming conventions and visible evidence
    metadata only. It does not read or modify any weight table.
    """

    ev = evidence or {}
    item = statement_item or {}
    school = _normalize_school(str(ev.get("school") or item.get("school") or ""), rule_id)
    canon = _canon_for_rule(rule_id, school)
    return {
        "family_id": _family_id_for_rule(rule_id),
        "school": school,
        "canon": canon,
        "rule_type": _rule_type_for_rule(rule_id, item),
    }


def _iter_statement_items(ctx: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    sections = (
        "zuogong_paths",
        "production_rule_conclusions",
        "consensus_conclusions",
        "complementary_conclusions",
        "iron_gates",
        "support_marriage_boosts",
        "support_health",
        "parallel_domain_conclusions",
        "parallel_domain_readings",
        "parallel_domain_consistency_notes",
    )
    for key in sections:
        values = ctx.get(key, []) or []
        if not isinstance(values, list):
            continue
        for item in values:
            if isinstance(item, Mapping):
                yield item


def _evidence_items(item: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw = item.get("evidence") or []
    if isinstance(raw, list):
        return [ev for ev in raw if isinstance(ev, Mapping)]
    return []


def _statement_text(item: Mapping[str, Any]) -> str:
    value = (
        item.get("statement")
        or item.get("description")
        or item.get("candidate_event")
        or item.get("name")
        or item.get("headline")
        or ""
    )
    return str(value).strip()


def _confidence_snapshot(item: Mapping[str, Any]) -> dict[str, Any]:
    star = _int_or_zero(item.get("star"))
    percent = _float_or_zero(item.get("pct", item.get("percent", 0)))
    if percent <= 1.0 and percent > 0:
        percent = round(percent * 100, 2)
    return {
        "star": max(0, min(5, star)),
        "percent": max(0.0, min(100.0, percent)),
        "posterior_mean": None,
        "sample_n": 0,
        "source": "static_rule",
    }


def _family_id_for_rule(rule_id: str) -> str:
    rid = rule_id.strip()
    if not rid:
        return "FAM-UNKNOWN"
    match = _RULE_PREFIX_RE.match(rid)
    if match:
        return f"FAM-{match.group(0)}"
    return f"FAM-{rid}"


def _normalize_school(raw_school: str, rule_id: str) -> str:
    school = raw_school.strip()
    if school and school not in {"?", "—", "source_missing"}:
        return school
    if rule_id.startswith("M1-D"):
        return "段"
    if rule_id.startswith("M2-Y"):
        return "杨"
    if rule_id.startswith(("M3-R", "MR-")):
        return "任"
    if rule_id.startswith("GP-"):
        return "高"
    if rule_id.startswith("ZP-"):
        return "子平"
    if rule_id.startswith("DTS-"):
        return "滴天髓"
    if rule_id.startswith(("PDC", "PDR", "CDC")):
        return "多专家裁判"
    return "runtime_unknown_school"


def _canon_for_rule(rule_id: str, school: str) -> str:
    if rule_id.startswith("M1-D") or school == "段":
        return "duan"
    if rule_id.startswith("M2-Y") or school == "杨":
        return "yang"
    if rule_id.startswith(("M3-R", "MR-")) or school == "任":
        return "ren"
    if rule_id.startswith("GP-") or school == "高":
        return "gao"
    if rule_id.startswith("ZP-") or school == "子平":
        return "ziping"
    if rule_id.startswith("DTS-") or school == "滴天髓":
        return "tiaohou_ditiansui"
    if school == "多专家裁判":
        return "parallel_domain_runtime"
    return "runtime_unknown_canon"


def _rule_type_for_rule(rule_id: str, item: Mapping[str, Any]) -> str:
    section = str(item.get("section") or "")
    if rule_id.startswith(("MR-", "M3-R")):
        return "timing_gate"
    if rule_id.startswith("GP-"):
        return "support_shensha"
    if rule_id.startswith(("ZP-", "DTS-")):
        return "production_rule"
    if section.startswith("parallel") or rule_id.startswith(("PDC", "PDR", "CDC")):
        return "parallel_domain_runtime"
    return "runtime_rule"


def _int_or_zero(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float_or_zero(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
