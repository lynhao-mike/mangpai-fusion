from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from engine.energy.types import Confidence, Evidence, School

ProductionExpertSystem = Literal["ziping", "tiaohou_ditiansui"]
ALLOWED_PRODUCTION_EXPERT_SYSTEMS: tuple[ProductionExpertSystem, ...] = (
    "ziping",
    "tiaohou_ditiansui",
)
ALLOWED_TOP_LEVEL_STATUS = "active"
ALLOWED_SOURCE_SCOPE = "production_rules"
ALLOWED_RULE_STATUS = "active"
EXPERT_DISPLAY_NAMES: dict[ProductionExpertSystem, School] = {
    "ziping": "子平",
    "tiaohou_ditiansui": "滴天髓",
}


class ProductionRuleValidationError(ValueError):
    """生产规则 YAML 不满足正式规则库约束。"""


@dataclass(frozen=True, slots=True)
class ProductionRuleSource:
    """生产规则来源。"""

    path: str
    excerpt: str

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "excerpt": self.excerpt}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProductionRuleSource:
        return cls(path=str(data.get("path", "")), excerpt=str(data.get("excerpt", "")))


@dataclass(frozen=True, slots=True)
class ProductionRuleOutput:
    """生产规则输出模板。"""

    statement: str
    falsifiable: str

    def to_dict(self) -> dict[str, Any]:
        return {"statement": self.statement, "falsifiable": self.falsifiable}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProductionRuleOutput:
        return cls(
            statement=str(data.get("statement", "")),
            falsifiable=str(data.get("falsifiable", "")),
        )


@dataclass(frozen=True, slots=True)
class ProductionRuleConditions:
    """生产规则触发条件。"""

    required: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    trigger: str = "always"

    def to_dict(self) -> dict[str, Any]:
        return {
            "required": list(self.required),
            "optional": list(self.optional),
            "exclusions": list(self.exclusions),
            "trigger": self.trigger,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProductionRuleConditions:
        return cls(
            required=[str(value) for value in data.get("required", [])],
            optional=[str(value) for value in data.get("optional", [])],
            exclusions=[str(value) for value in data.get("exclusions", [])],
            trigger=str(data.get("trigger", "always")),
        )


@dataclass(frozen=True, slots=True)
class ProductionRule:
    """正式生产规则。"""

    id: str
    status: Literal["active"]
    expert_system: ProductionExpertSystem
    title: str
    topic: str
    domains: list[str]
    axis_refs: list[str]
    claim: str
    conditions: ProductionRuleConditions
    output: ProductionRuleOutput
    source: ProductionRuleSource
    confidence: Confidence
    layer: str = "互补"
    rule_type: str = "GENERAL_PRINCIPLE"
    quantifiable: bool = False
    review_notes: str = ""

    @property
    def display_school(self) -> School:
        return EXPERT_DISPLAY_NAMES[self.expert_system]

    def to_evidence(self) -> Evidence:
        return Evidence(
            rule_id=self.id,
            school=self.display_school,
            description=f"{self.title}：{self.claim}",
            weight=round(self.confidence.posterior, 3),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "expert_system": self.expert_system,
            "title": self.title,
            "topic": self.topic,
            "domains": list(self.domains),
            "axis_refs": list(self.axis_refs),
            "claim": self.claim,
            "conditions": self.conditions.to_dict(),
            "output": self.output.to_dict(),
            "source": self.source.to_dict(),
            "confidence": self.confidence.to_dict(),
            "layer": self.layer,
            "rule_type": self.rule_type,
            "quantifiable": self.quantifiable,
            "review": {"notes": self.review_notes},
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        expected_expert_system: ProductionExpertSystem,
    ) -> ProductionRule:
        status = str(data.get("status", ""))
        expert_system = str(data.get("expert_system", ""))
        if status != ALLOWED_RULE_STATUS:
            raise ProductionRuleValidationError(
                f"生产规则 {data.get('id', '<unknown>')} status 必须为 active，"
                f"实际为 {status!r}。"
            )
        if expert_system != expected_expert_system:
            raise ProductionRuleValidationError(
                f"生产规则 {data.get('id', '<unknown>')} expert_system 必须为 "
                f"{expected_expert_system!r}，实际为 {expert_system!r}。"
            )
        confidence = data.get("confidence", {}) or {}
        return cls(
            id=str(data["id"]),
            status="active",
            expert_system=expected_expert_system,
            title=str(data["title"]),
            topic=str(data["topic"]),
            domains=[str(value) for value in data.get("domains", [])],
            axis_refs=[str(value) for value in data.get("axis_refs", [])],
            claim=str(data["claim"]),
            conditions=ProductionRuleConditions.from_dict(data.get("conditions", {})),
            output=ProductionRuleOutput.from_dict(data.get("output", {})),
            source=ProductionRuleSource.from_dict(data.get("source", {})),
            confidence=Confidence(
                star=int(confidence.get("star", 4)),
                percent=float(confidence.get("percent", 0.78)),
                posterior=float(
                    confidence.get("posterior", confidence.get("percent", 0.78))
                ),
                variance=float(confidence.get("variance", 0.04)),
                sample_n=int(confidence.get("sample_n", 1)),
            ),
            layer=str(data.get("layer", "互补")),
            rule_type=str(data.get("rule_type", "GENERAL_PRINCIPLE")),
            quantifiable=bool(data.get("quantifiable", False)),
            review_notes=str(data.get("review", {}).get("notes", "")),
        )


@dataclass(frozen=True, slots=True)
class ProductionRuleSet:
    """单一专家体系的正式生产规则集。"""

    schema_version: str
    status: Literal["active"]
    source_scope: Literal["production_rules"]
    expert_system: ProductionExpertSystem
    notes: str
    rules: list[ProductionRule]
    source_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "source_scope": self.source_scope,
            "expert_system": self.expert_system,
            "notes": self.notes,
            "rules": [rule.to_dict() for rule in self.rules],
            "source_path": self.source_path.as_posix(),
        }

    def rules_for_domain(self, domain: str) -> list[ProductionRule]:
        return [rule for rule in self.rules if domain in rule.domains]
