"""子平 / 滴天髓旁路候选规则 YAML 加载器。

加载范围严格限定为 theory/raw/yaml 下的 review_draft / candidate 旁路文件：
- 不读取正式 theory/ziping 或 theory/tiaohou_ditiansui 规则库；
- 不允许 active / confirmed / promoted 状态；
- 不接入默认生产 pipeline，只为旁路裁判与 schema 验证提供只读数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal, Optional

import yaml

from engine.domain.parallel import DomainName, EvidenceItem, ExpertSystem

CandidateExpertSystem = Literal["ziping", "tiaohou_ditiansui"]
ALLOWED_EXPERT_SYSTEMS: tuple[CandidateExpertSystem, ...] = ("ziping", "tiaohou_ditiansui")
ALLOWED_TOP_LEVEL_STATUS = "review_draft"
ALLOWED_SOURCE_SCOPE = "bypass_candidate_rules"
ALLOWED_RULE_STATUS = "candidate"
PROHIBITED_RULE_STATUSES = {"active", "confirmed", "promoted", "deprecated"}
DEFAULT_BYPASS_YAML_DIR = Path("theory/raw/yaml")
DEFAULT_CANDIDATE_FILES: dict[CandidateExpertSystem, Path] = {
    "ziping": DEFAULT_BYPASS_YAML_DIR / "ziping_candidate_rules_2026-06-05.yaml",
    "tiaohou_ditiansui": DEFAULT_BYPASS_YAML_DIR / "tiaohou_ditiansui_candidate_rules_2026-06-05.yaml",
}


class CandidateRuleValidationError(ValueError):
    """旁路候选规则 YAML 不满足审查态安全约束。"""


@dataclass(frozen=True)
class CandidateRuleSource:
    """候选规则来源信息。"""

    path: str
    excerpt: str

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "excerpt": self.excerpt}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CandidateRuleSource":
        return cls(path=str(data.get("path", "")), excerpt=str(data.get("excerpt", "")))


@dataclass(frozen=True)
class CandidateRuleOutput:
    """候选规则可输出模板。"""

    statement: str
    falsifiable: str

    def to_dict(self) -> dict[str, Any]:
        return {"statement": self.statement, "falsifiable": self.falsifiable}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CandidateRuleOutput":
        return cls(
            statement=str(data.get("statement", "")),
            falsifiable=str(data.get("falsifiable", "")),
        )


@dataclass(frozen=True)
class CandidateRuleConditions:
    """候选规则触发、辅助与排除条件。"""

    required: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "required": list(self.required),
            "optional": list(self.optional),
            "exclusions": list(self.exclusions),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CandidateRuleConditions":
        return cls(
            required=[str(x) for x in data.get("required", [])],
            optional=[str(x) for x in data.get("optional", [])],
            exclusions=[str(x) for x in data.get("exclusions", [])],
        )


@dataclass(frozen=True)
class CandidateRule:
    """子平 / 滴天髓旁路候选规则。"""

    id: str
    status: Literal["candidate"]
    expert_system: CandidateExpertSystem
    title: str
    topic: str
    domains: list[DomainName]
    axis_refs: list[str]
    claim: str
    conditions: CandidateRuleConditions
    output: CandidateRuleOutput
    source: CandidateRuleSource
    review_notes: str = ""

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
            "review": {"notes": self.review_notes},
        }

    def to_evidence_item(self) -> EvidenceItem:
        """转换为裁判层 evidence_items 的候选规则证据项。"""

        return EvidenceItem(
            evidence_type="candidate_rule",
            ref=self.id,
            summary=self.claim,
            strength="medium",
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, expected_expert_system: CandidateExpertSystem) -> "CandidateRule":
        status = str(data.get("status", ""))
        expert_system = str(data.get("expert_system", ""))
        if status != ALLOWED_RULE_STATUS:
            raise CandidateRuleValidationError(
                f"候选规则 {data.get('id', '<unknown>')} status 必须为 candidate，实际为 {status!r}。"
            )
        if status in PROHIBITED_RULE_STATUSES:
            raise CandidateRuleValidationError(
                f"候选规则 {data.get('id', '<unknown>')} 禁止使用状态 {status!r}。"
            )
        if expert_system != expected_expert_system:
            raise CandidateRuleValidationError(
                f"候选规则 {data.get('id', '<unknown>')} expert_system 必须为 "
                f"{expected_expert_system!r}，实际为 {expert_system!r}。"
            )
        return cls(
            id=str(data["id"]),
            status="candidate",
            expert_system=expected_expert_system,
            title=str(data["title"]),
            topic=str(data["topic"]),
            domains=[str(x) for x in data.get("domains", [])],
            axis_refs=[str(x) for x in data.get("axis_refs", [])],
            claim=str(data["claim"]),
            conditions=CandidateRuleConditions.from_dict(data.get("conditions", {})),
            output=CandidateRuleOutput.from_dict(data.get("output", {})),
            source=CandidateRuleSource.from_dict(data.get("source", {})),
            review_notes=str(data.get("review", {}).get("notes", "")),
        )


@dataclass(frozen=True)
class CandidateRuleSet:
    """单一专家体系的旁路候选规则集。"""

    schema_version: str
    status: Literal["review_draft"]
    source_scope: Literal["bypass_candidate_rules"]
    expert_system: CandidateExpertSystem
    notes: str
    rules: list[CandidateRule]
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

    def rules_for_domain(self, domain: str) -> list[CandidateRule]:
        """筛选适用于指定功能域的候选规则。"""

        return [rule for rule in self.rules if domain in rule.domains]


@dataclass(frozen=True)
class CandidateRuleLibrary:
    """子平与滴天髓旁路候选规则库。"""

    rule_sets: dict[CandidateExpertSystem, CandidateRuleSet]

    @property
    def rules(self) -> list[CandidateRule]:
        collected: list[CandidateRule] = []
        for expert_system in ALLOWED_EXPERT_SYSTEMS:
            rule_set = self.rule_sets.get(expert_system)
            if rule_set:
                collected.extend(rule_set.rules)
        return collected

    def rules_for_domain(
        self,
        domain: str,
        *,
        expert_system: Optional[CandidateExpertSystem] = None,
    ) -> list[CandidateRule]:
        """按功能域与可选专家体系筛选候选规则。"""

        if expert_system:
            rule_set = self.rule_sets.get(expert_system)
            return rule_set.rules_for_domain(domain) if rule_set else []
        return [rule for rule in self.rules if domain in rule.domains]

    def to_dict(self) -> dict[str, Any]:
        return {key: value.to_dict() for key, value in self.rule_sets.items()}


def load_candidate_rule_set(
    path: str | Path,
    *,
    expected_expert_system: Optional[CandidateExpertSystem] = None,
    workspace_root: str | Path = ".",
) -> CandidateRuleSet:
    """加载并校验单个旁路候选规则 YAML。"""

    resolved_path = _resolve_bypass_path(path, workspace_root=workspace_root)
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise CandidateRuleValidationError(f"{resolved_path} 顶层必须是 YAML mapping。")
    expert_system = _validate_top_level(raw, expected_expert_system=expected_expert_system)
    rules_raw = raw.get("rules", [])
    if not isinstance(rules_raw, list):
        raise CandidateRuleValidationError(f"{resolved_path} rules 必须是 list。")
    rules = [CandidateRule.from_dict(item, expected_expert_system=expert_system) for item in rules_raw]
    return CandidateRuleSet(
        schema_version=str(raw.get("schema_version", "")),
        status="review_draft",
        source_scope="bypass_candidate_rules",
        expert_system=expert_system,
        notes=str(raw.get("notes", "")),
        rules=rules,
        source_path=resolved_path,
    )


def load_default_candidate_library(*, workspace_root: str | Path = ".") -> CandidateRuleLibrary:
    """加载默认子平 / 滴天髓旁路候选规则库。"""

    return CandidateRuleLibrary(
        rule_sets={
            expert_system: load_candidate_rule_set(
                path,
                expected_expert_system=expert_system,
                workspace_root=workspace_root,
            )
            for expert_system, path in DEFAULT_CANDIDATE_FILES.items()
        }
    )


def load_candidate_library(
    paths: Iterable[str | Path],
    *,
    workspace_root: str | Path = ".",
) -> CandidateRuleLibrary:
    """从显式路径集合加载旁路候选规则库。"""

    rule_sets: dict[CandidateExpertSystem, CandidateRuleSet] = {}
    for path in paths:
        rule_set = load_candidate_rule_set(path, workspace_root=workspace_root)
        if rule_set.expert_system in rule_sets:
            raise CandidateRuleValidationError(f"重复加载 expert_system={rule_set.expert_system!r}。")
        rule_sets[rule_set.expert_system] = rule_set
    return CandidateRuleLibrary(rule_sets=rule_sets)


def _validate_top_level(
    raw: dict[str, Any],
    *,
    expected_expert_system: Optional[CandidateExpertSystem],
) -> CandidateExpertSystem:
    status = str(raw.get("status", ""))
    source_scope = str(raw.get("source_scope", ""))
    expert_system = str(raw.get("expert_system", ""))
    if status != ALLOWED_TOP_LEVEL_STATUS:
        raise CandidateRuleValidationError(f"顶层 status 必须为 review_draft，实际为 {status!r}。")
    if source_scope != ALLOWED_SOURCE_SCOPE:
        raise CandidateRuleValidationError(
            f"顶层 source_scope 必须为 bypass_candidate_rules，实际为 {source_scope!r}。"
        )
    if expert_system not in ALLOWED_EXPERT_SYSTEMS:
        raise CandidateRuleValidationError(f"不支持的 expert_system：{expert_system!r}。")
    if expected_expert_system and expert_system != expected_expert_system:
        raise CandidateRuleValidationError(
            f"文件 expert_system 必须为 {expected_expert_system!r}，实际为 {expert_system!r}。"
        )
    return expert_system  # type: ignore[return-value]


def _resolve_bypass_path(path: str | Path, *, workspace_root: str | Path) -> Path:
    root = Path(workspace_root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    bypass_root = (root / DEFAULT_BYPASS_YAML_DIR).resolve()
    try:
        resolved.relative_to(bypass_root)
    except ValueError as exc:
        raise CandidateRuleValidationError(
            f"旁路 YAML 加载器只能读取 {DEFAULT_BYPASS_YAML_DIR.as_posix()} 下的文件：{resolved}"
        ) from exc
    if not resolved.exists():
        raise CandidateRuleValidationError(f"旁路候选规则 YAML 不存在：{resolved}")
    if resolved.suffix.lower() not in {".yaml", ".yml"}:
        raise CandidateRuleValidationError(f"旁路候选规则文件必须是 YAML：{resolved}")
    return resolved
