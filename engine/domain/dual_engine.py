"""双引擎适配层领域模型。

本模块只定义可序列化的数据外壳：理论派 findings、盲派 findings、融合 findings。
具体推理仍由既有 D1-D4、生产规则与多专家裁判模块负责。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional


DUAL_ENGINE_SCHEMA_VERSION = "dual-engine-findings-2026-06-07"


@dataclass(frozen=True)
class TheoryFindings:
    """理论派聚合输出。"""

    case_id: str
    triggered_rules: list[dict[str, Any]] = field(default_factory=list)
    rule_count_by_system: dict[str, int] = field(default_factory=dict)
    strength_profile: dict[str, float] = field(default_factory=dict)
    day_master_strength: float = 0.0
    main_yongshen: list[str] = field(default_factory=list)
    assistant_yongshen: list[str] = field(default_factory=list)
    evidence_rule_ids: list[str] = field(default_factory=list)
    confidence_summary: dict[str, Any] = field(default_factory=dict)
    schema_version: str = DUAL_ENGINE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "triggered_rules": [dict(rule) for rule in self.triggered_rules],
            "rule_count_by_system": dict(self.rule_count_by_system),
            "strength_profile": dict(self.strength_profile),
            "day_master_strength": self.day_master_strength,
            "main_yongshen": list(self.main_yongshen),
            "assistant_yongshen": list(self.assistant_yongshen),
            "evidence_rule_ids": list(self.evidence_rule_ids),
            "confidence_summary": dict(self.confidence_summary),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TheoryFindings":
        return cls(
            case_id=str(data.get("case_id", "")),
            triggered_rules=[dict(rule) for rule in data.get("triggered_rules", [])],
            rule_count_by_system={
                str(k): int(v) for k, v in data.get("rule_count_by_system", {}).items()
            },
            strength_profile={
                str(k): float(v) for k, v in data.get("strength_profile", {}).items()
            },
            day_master_strength=float(data.get("day_master_strength", 0.0)),
            main_yongshen=[str(x) for x in data.get("main_yongshen", [])],
            assistant_yongshen=[str(x) for x in data.get("assistant_yongshen", [])],
            evidence_rule_ids=[str(x) for x in data.get("evidence_rule_ids", [])],
            confidence_summary=dict(data.get("confidence_summary", {})),
            schema_version=str(data.get("schema_version", DUAL_ENGINE_SCHEMA_VERSION)),
        )

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, text: str) -> "TheoryFindings":
        return cls.from_dict(json.loads(text))


@dataclass(frozen=True)
class BlindFindings:
    """盲派 D1-D4 聚合输出。"""

    case_id: str
    energy_summary: dict[str, Any] = field(default_factory=dict)
    picture_summary: dict[str, Any] = field(default_factory=dict)
    timing_summary: dict[str, Any] = field(default_factory=dict)
    support_summary: dict[str, Any] = field(default_factory=dict)
    evidence_rule_ids: list[str] = field(default_factory=list)
    upstream_hashes: dict[str, str] = field(default_factory=dict)
    schema_version: str = DUAL_ENGINE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "energy_summary": dict(self.energy_summary),
            "picture_summary": dict(self.picture_summary),
            "timing_summary": dict(self.timing_summary),
            "support_summary": dict(self.support_summary),
            "evidence_rule_ids": list(self.evidence_rule_ids),
            "upstream_hashes": dict(self.upstream_hashes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlindFindings":
        return cls(
            case_id=str(data.get("case_id", "")),
            energy_summary=dict(data.get("energy_summary", {})),
            picture_summary=dict(data.get("picture_summary", {})),
            timing_summary=dict(data.get("timing_summary", {})),
            support_summary=dict(data.get("support_summary", {})),
            evidence_rule_ids=[str(x) for x in data.get("evidence_rule_ids", [])],
            upstream_hashes={str(k): str(v) for k, v in data.get("upstream_hashes", {}).items()},
            schema_version=str(data.get("schema_version", DUAL_ENGINE_SCHEMA_VERSION)),
        )

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, text: str) -> "BlindFindings":
        return cls.from_dict(json.loads(text))


@dataclass(frozen=True)
class FusionFindings:
    """理论派与盲派融合输出。"""

    case_id: str
    conclusions: list[dict[str, Any]] = field(default_factory=list)
    theory_support: list[str] = field(default_factory=list)
    blind_support: list[str] = field(default_factory=list)
    confidence_summary: dict[str, Any] = field(default_factory=dict)
    parallel_analysis: Optional[Any] = None
    schema_version: str = DUAL_ENGINE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "conclusions": [dict(item) for item in self.conclusions],
            "theory_support": list(self.theory_support),
            "blind_support": list(self.blind_support),
            "confidence_summary": dict(self.confidence_summary),
            "parallel_analysis": (
                self.parallel_analysis.to_dict()
                if self.parallel_analysis is not None
                and hasattr(self.parallel_analysis, "to_dict")
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FusionFindings":
        return cls(
            case_id=str(data.get("case_id", "")),
            conclusions=[dict(item) for item in data.get("conclusions", [])],
            theory_support=[str(x) for x in data.get("theory_support", [])],
            blind_support=[str(x) for x in data.get("blind_support", [])],
            confidence_summary=dict(data.get("confidence_summary", {})),
            parallel_analysis=_load_parallel_analysis(data.get("parallel_analysis")),
            schema_version=str(data.get("schema_version", DUAL_ENGINE_SCHEMA_VERSION)),
        )

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, text: str) -> "FusionFindings":
        return cls.from_dict(json.loads(text))


def _load_parallel_analysis(data: Any) -> Optional[Any]:
    if not data:
        return None
    try:
        from engine.domain.parallel import ParallelAnalysisOutput
        return ParallelAnalysisOutput.from_dict(data)
    except Exception:  # noqa: BLE001
        return None
