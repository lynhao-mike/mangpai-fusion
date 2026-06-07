"""D1-D4 runtime findings 到 V2 Evidence 的适配。"""

from __future__ import annotations

from typing import Any

from engine.v2.domain.evidence import SchoolEvidence
from engine.v2.evidence.base import confidence_from_obj, normalize_domain, stable_evidence_id, text_from_evidence_item


def energy_to_evidence(energy: Any) -> list[SchoolEvidence]:
    case_id = str(getattr(energy, "case_id", ""))
    confidence = confidence_from_obj(getattr(energy, "confidence", None), 0.65)
    evidences: list[SchoolEvidence] = []

    for idx, item in enumerate(getattr(energy, "evidence", []) or []):
        ref = str(getattr(item, "rule_id", "") or f"energy-{idx}")
        evidences.append(
            SchoolEvidence(
                evidence_id=stable_evidence_id(case_id, "duan", ref, idx),
                case_id=case_id,
                source_school="duan",
                domain="general",
                claim="段派能量与做功结构提供基础证据。",
                evidence=text_from_evidence_item(item),
                confidence=confidence,
                source_rule_id=ref,
                trace_ids=[ref],
                metadata={"adapter": "energy_to_evidence", "layer_count": getattr(energy, "layer_count", 0)},
            )
        )

    if not evidences:
        evidences.append(
            SchoolEvidence(
                evidence_id=stable_evidence_id(case_id, "duan", "summary"),
                case_id=case_id,
                source_school="duan",
                domain="general",
                claim="段派能量层提供命局结构基础证据。",
                evidence=f"做功层数={getattr(energy, 'layer_count', 0)}。",
                confidence=confidence,
                metadata={"adapter": "energy_to_evidence", "fallback": True},
            )
        )
    return evidences


def picture_to_evidence(picture: Any) -> list[SchoolEvidence]:
    case_id = str(getattr(picture, "case_id", ""))
    confidence = confidence_from_obj(getattr(picture, "confidence", None), 0.62)
    evidences: list[SchoolEvidence] = []

    for idx, item in enumerate(getattr(picture, "evidence", []) or []):
        ref = str(getattr(item, "rule_id", "") or f"picture-{idx}")
        evidences.append(
            SchoolEvidence(
                evidence_id=stable_evidence_id(case_id, "yang", ref, idx),
                case_id=case_id,
                source_school="yang",
                domain="general",
                claim="杨派画面层提供现实画像证据。",
                evidence=text_from_evidence_item(item),
                confidence=confidence,
                source_rule_id=ref,
                trace_ids=[ref],
                metadata={"adapter": "picture_to_evidence"},
            )
        )

    domain_hints = [
        ("wealth", getattr(picture, "caifu", None), "杨派财富画像提供财运证据。"),
        ("career", getattr(picture, "guanming", None), "杨派官命取法提供事业证据。"),
        ("marriage", getattr(picture, "marriage_picture", None), "杨派婚姻画像提供婚姻证据。"),
        ("general", getattr(picture, "tiaohou_advice", None), "杨派调候建议提供环境与取象证据。"),
    ]
    for domain, payload, claim in domain_hints:
        if payload:
            evidences.append(
                SchoolEvidence(
                    evidence_id=stable_evidence_id(case_id, "yang", domain, "payload"),
                    case_id=case_id,
                    source_school="yang",
                    domain=domain,
                    claim=claim,
                    evidence=str(payload),
                    confidence=confidence,
                    trace_ids=[f"yang-{domain}"],
                    metadata={"adapter": "picture_to_evidence", "payload_type": type(payload).__name__},
                )
            )
    return evidences


def gate_results_to_evidence(gate_results: list[Any], *, case_id: str = "") -> list[SchoolEvidence]:
    evidences: list[SchoolEvidence] = []
    for idx, gate in enumerate(gate_results or []):
        gate_case_id = str(getattr(gate, "case_id", "") or case_id)
        confidence = confidence_from_obj(getattr(gate, "confidence", None), 0.6)
        event_types = list(getattr(gate, "event_type_hypotheses", []) or [])
        domain = _domain_from_event_types(event_types)
        ref = str(getattr(gate, "trace_id", "") or getattr(gate, "candidate_id", "") or f"gate-{idx}")
        evidences.append(
            SchoolEvidence(
                evidence_id=stable_evidence_id(gate_case_id, "ren", ref, idx),
                case_id=gate_case_id,
                source_school="ren",
                domain=domain,
                claim="任派应期层提供时间触发证据。",
                evidence=f"应期候选={getattr(gate, 'candidate_id', ref)}；事件类型={event_types or ['未分类']}。",
                confidence=confidence,
                source_rule_id=ref,
                trace_ids=[ref],
                time_scope=_time_scope_from_gate(gate),
                metadata={"adapter": "gate_results_to_evidence", "event_type_hypotheses": event_types},
            )
        )
    return evidences


def support_to_evidence(support: Any) -> list[SchoolEvidence]:
    if support is None:
        return []
    case_id = str(getattr(support, "case_id", ""))
    confidence = confidence_from_obj(getattr(support, "confidence", None), 0.58)
    evidences: list[SchoolEvidence] = []

    for idx, item in enumerate(getattr(support, "evidence", []) or []):
        ref = str(getattr(item, "rule_id", "") or f"support-{idx}")
        evidences.append(
            SchoolEvidence(
                evidence_id=stable_evidence_id(case_id, "gao", ref, idx),
                case_id=case_id,
                source_school="gao",
                domain="general",
                claim="高派旁证层提供神煞与横向补强证据。",
                evidence=text_from_evidence_item(item),
                confidence=confidence,
                source_rule_id=ref,
                trace_ids=[ref],
                metadata={"adapter": "support_to_evidence"},
            )
        )

    supports = getattr(support, "shensha_supports", {}) or {}
    if isinstance(supports, dict):
        for raw_domain, rows in supports.items():
            for idx, row in enumerate(rows or []):
                name = getattr(row, "name", "") or getattr(row, "shensha", "") or str(row)
                evidences.append(
                    SchoolEvidence(
                        evidence_id=stable_evidence_id(case_id, "gao", raw_domain, name, idx),
                        case_id=case_id,
                        source_school="gao",
                        domain=normalize_domain(str(raw_domain)),
                        claim="高派神煞旁证提供领域补强证据。",
                        evidence=str(row),
                        confidence=confidence,
                        trace_ids=[f"gao-{raw_domain}-{idx}"],
                        metadata={"adapter": "support_to_evidence", "raw_domain": raw_domain},
                    )
                )
    return evidences


def _domain_from_event_types(event_types: list[str]) -> str:
    joined = " ".join(str(x) for x in event_types)
    if any(key in joined for key in ("婚", "感情", "配偶")):
        return "marriage"
    if any(key in joined for key in ("财", "钱", "资产")):
        return "wealth"
    if any(key in joined for key in ("官", "事业", "工作", "职")):
        return "career"
    if any(key in joined for key in ("病", "灾", "健康")):
        return "health"
    if any(key in joined for key in ("学", "考试", "证")):
        return "education"
    return "general"


def _time_scope_from_gate(gate: Any) -> dict[str, Any] | None:
    year = getattr(gate, "year", None)
    if year is None:
        return None
    try:
        year_int = int(year)
    except (TypeError, ValueError):
        return None
    return {"type": "liunian", "label": str(year_int), "start_year": year_int, "end_year": year_int}
