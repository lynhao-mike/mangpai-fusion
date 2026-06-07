"""V2 分析输出契约。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from engine.v2 import V2_SCHEMA_VERSION
from engine.v2.domain.agents import DomainReasoningResult
from engine.v2.domain.evidence import DomainEvidence, SchoolEvidence
from engine.v2.domain.events import EventCandidate
from engine.v2.domain.similarity import SimilarCase


@dataclass(frozen=True)
class V2AnalysisOutput:
    """V2 实战推理旁路输出。

    M0/M1 阶段承载 Evidence Adapter 与 Evidence Builder 的结果；
    M2 起承载领域 Agent 推理结果，后续继续扩展 event_candidates、similar_cases、arbitration_results。
    """

    case_id: str
    school_evidences: list[SchoolEvidence] = field(default_factory=list)
    domain_evidences: list[DomainEvidence] = field(default_factory=list)
    domain_results: list[DomainReasoningResult] = field(default_factory=list)
    event_candidates: list[EventCandidate] = field(default_factory=list)
    similar_cases: list[SimilarCase] = field(default_factory=list)
    arbitration_results: list[dict[str, Any]] = field(default_factory=list)
    final_conclusions: list[str] = field(default_factory=list)
    report_sections: dict[str, Any] = field(default_factory=dict)
    schema_version: str = V2_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "school_evidences": [item.to_dict() for item in self.school_evidences],
            "domain_evidences": [item.to_dict() for item in self.domain_evidences],
            "domain_results": [item.to_dict() for item in self.domain_results],
            "event_candidates": [item.to_dict() for item in self.event_candidates],
            "similar_cases": [item.to_dict() for item in self.similar_cases],
            "arbitration_results": list(self.arbitration_results),
            "final_conclusions": list(self.final_conclusions),
            "report_sections": dict(self.report_sections),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "V2AnalysisOutput":
        return cls(
            case_id=str(data.get("case_id", "")),
            school_evidences=[SchoolEvidence.from_dict(x) for x in data.get("school_evidences", [])],
            domain_evidences=[DomainEvidence.from_dict(x) for x in data.get("domain_evidences", [])],
            domain_results=[DomainReasoningResult.from_dict(x) for x in data.get("domain_results", [])],
            event_candidates=[EventCandidate.from_dict(x) for x in data.get("event_candidates", [])],
            similar_cases=[SimilarCase.from_dict(x) for x in data.get("similar_cases", [])],
            arbitration_results=[dict(x) for x in data.get("arbitration_results", [])],
            final_conclusions=[str(x) for x in data.get("final_conclusions", [])],
            report_sections=dict(data.get("report_sections", {})),
            schema_version=str(data.get("schema_version", V2_SCHEMA_VERSION)),
        )

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, value: str) -> "V2AnalysisOutput":
        return cls.from_dict(json.loads(value))

    def hash(self) -> str:
        canonical = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
