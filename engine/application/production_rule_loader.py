"""子平 / 滴天髓生产规则加载与最小触发评估。

本模块只读取正式生产规则库 ``theory/ziping`` 与
``theory/tiaohou_ditiansui``，与旁路候选规则加载器隔离：
- 顶层 ``status`` 必须为 ``active``；
- 单条规则 ``status`` 必须为 ``active``；
- 不读取 ``theory/raw/yaml`` 旁路候选文件；
- 输出转换为现有 ``FinalConclusion`` 可消费的 evidence 链。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal, Optional

import yaml

from engine.energy.types import Confidence, EnergyFindings, Evidence
from engine.picture.types import PictureFindings
from engine.predicates.relations import zhi_chong
from engine.predicates.types import GAN_TO_WUXING, ZHI_TO_WUXING, ParsedInput

ProductionExpertSystem = Literal["ziping", "tiaohou_ditiansui"]
ALLOWED_PRODUCTION_EXPERT_SYSTEMS: tuple[ProductionExpertSystem, ...] = (
    "ziping",
    "tiaohou_ditiansui",
)
ALLOWED_TOP_LEVEL_STATUS = "active"
ALLOWED_SOURCE_SCOPE = "production_rules"
ALLOWED_RULE_STATUS = "active"
DEFAULT_PRODUCTION_FILES: dict[ProductionExpertSystem, Path] = {
    "ziping": Path("theory/ziping/index.yaml"),
    "tiaohou_ditiansui": Path("theory/tiaohou_ditiansui/index.yaml"),
}
EXPERT_DISPLAY_NAMES: dict[ProductionExpertSystem, str] = {
    "ziping": "子平",
    "tiaohou_ditiansui": "滴天髓",
}


class ProductionRuleValidationError(ValueError):
    """生产规则 YAML 不满足正式规则库约束。"""


@dataclass(frozen=True)
class ProductionRuleSource:
    """生产规则来源。"""

    path: str
    excerpt: str

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "excerpt": self.excerpt}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProductionRuleSource":
        return cls(path=str(data.get("path", "")), excerpt=str(data.get("excerpt", "")))


@dataclass(frozen=True)
class ProductionRuleOutput:
    """生产规则输出模板。"""

    statement: str
    falsifiable: str

    def to_dict(self) -> dict[str, Any]:
        return {"statement": self.statement, "falsifiable": self.falsifiable}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProductionRuleOutput":
        return cls(
            statement=str(data.get("statement", "")),
            falsifiable=str(data.get("falsifiable", "")),
        )


@dataclass(frozen=True)
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
    def from_dict(cls, data: dict[str, Any]) -> "ProductionRuleConditions":
        return cls(
            required=[str(x) for x in data.get("required", [])],
            optional=[str(x) for x in data.get("optional", [])],
            exclusions=[str(x) for x in data.get("exclusions", [])],
            trigger=str(data.get("trigger", "always")),
        )


@dataclass(frozen=True)
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
    review_notes: str = ""

    @property
    def display_school(self) -> str:
        return EXPERT_DISPLAY_NAMES[self.expert_system]

    def to_evidence(self) -> Evidence:
        return Evidence(
            rule_id=self.id,
            school=self.display_school,  # type: ignore[arg-type]
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
            "review": {"notes": self.review_notes},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, expected_expert_system: ProductionExpertSystem) -> "ProductionRule":
        status = str(data.get("status", ""))
        expert_system = str(data.get("expert_system", ""))
        if status != ALLOWED_RULE_STATUS:
            raise ProductionRuleValidationError(
                f"生产规则 {data.get('id', '<unknown>')} status 必须为 active，实际为 {status!r}。"
            )
        if expert_system != expected_expert_system:
            raise ProductionRuleValidationError(
                f"生产规则 {data.get('id', '<unknown>')} expert_system 必须为 "
                f"{expected_expert_system!r}，实际为 {expert_system!r}。"
            )
        conf = data.get("confidence", {}) or {}
        return cls(
            id=str(data["id"]),
            status="active",
            expert_system=expected_expert_system,
            title=str(data["title"]),
            topic=str(data["topic"]),
            domains=[str(x) for x in data.get("domains", [])],
            axis_refs=[str(x) for x in data.get("axis_refs", [])],
            claim=str(data["claim"]),
            conditions=ProductionRuleConditions.from_dict(data.get("conditions", {})),
            output=ProductionRuleOutput.from_dict(data.get("output", {})),
            source=ProductionRuleSource.from_dict(data.get("source", {})),
            confidence=Confidence(
                star=int(conf.get("star", 4)),
                percent=float(conf.get("percent", 0.78)),
                posterior=float(conf.get("posterior", conf.get("percent", 0.78))),
                variance=float(conf.get("variance", 0.04)),
                sample_n=int(conf.get("sample_n", 1)),
            ),
            layer=str(data.get("layer", "互补")),
            review_notes=str(data.get("review", {}).get("notes", "")),
        )


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class ProductionRuleLibrary:
    """子平与滴天髓正式生产规则库。"""

    rule_sets: dict[ProductionExpertSystem, ProductionRuleSet]

    @property
    def rules(self) -> list[ProductionRule]:
        collected: list[ProductionRule] = []
        for expert_system in ALLOWED_PRODUCTION_EXPERT_SYSTEMS:
            rule_set = self.rule_sets.get(expert_system)
            if rule_set:
                collected.extend(rule_set.rules)
        return collected

    def triggered_rules(
        self,
        *,
        parsed: Optional[ParsedInput],
        energy: EnergyFindings,
        picture: PictureFindings,
    ) -> list[ProductionRule]:
        return [
            rule
            for rule in self.rules
            if _rule_triggered(rule, parsed=parsed, energy=energy, picture=picture)
        ]

    def to_dict(self) -> dict[str, Any]:
        return {key: value.to_dict() for key, value in self.rule_sets.items()}


def load_production_rule_set(
    path: str | Path,
    *,
    expected_expert_system: Optional[ProductionExpertSystem] = None,
    workspace_root: str | Path = ".",
) -> ProductionRuleSet:
    """加载并校验单个正式生产规则 YAML。"""

    resolved_path = _resolve_production_path(path, workspace_root=workspace_root)
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ProductionRuleValidationError(f"{resolved_path} 顶层必须是 YAML mapping。")
    expert_system = _validate_top_level(raw, expected_expert_system=expected_expert_system)
    rules_raw = raw.get("rules", [])
    if not isinstance(rules_raw, list):
        raise ProductionRuleValidationError(f"{resolved_path} rules 必须是 list。")
    rules = [ProductionRule.from_dict(item, expected_expert_system=expert_system) for item in rules_raw]
    return ProductionRuleSet(
        schema_version=str(raw.get("schema_version", "")),
        status="active",
        source_scope="production_rules",
        expert_system=expert_system,
        notes=str(raw.get("notes", "")),
        rules=rules,
        source_path=resolved_path,
    )


def load_default_production_library(*, workspace_root: str | Path = ".") -> ProductionRuleLibrary:
    """加载默认子平 / 滴天髓正式生产规则库。"""

    return ProductionRuleLibrary(
        rule_sets={
            expert_system: load_production_rule_set(
                path,
                expected_expert_system=expert_system,
                workspace_root=workspace_root,
            )
            for expert_system, path in DEFAULT_PRODUCTION_FILES.items()
        }
    )


def load_production_library(
    paths: Iterable[str | Path],
    *,
    workspace_root: str | Path = ".",
) -> ProductionRuleLibrary:
    """从显式路径集合加载正式生产规则库。"""

    rule_sets: dict[ProductionExpertSystem, ProductionRuleSet] = {}
    for path in paths:
        rule_set = load_production_rule_set(path, workspace_root=workspace_root)
        if rule_set.expert_system in rule_sets:
            raise ProductionRuleValidationError(f"重复加载 expert_system={rule_set.expert_system!r}。")
        rule_sets[rule_set.expert_system] = rule_set
    return ProductionRuleLibrary(rule_sets=rule_sets)


def _validate_top_level(
    raw: dict[str, Any],
    *,
    expected_expert_system: Optional[ProductionExpertSystem],
) -> ProductionExpertSystem:
    status = str(raw.get("status", ""))
    source_scope = str(raw.get("source_scope", ""))
    expert_system = str(raw.get("expert_system", ""))
    if status != ALLOWED_TOP_LEVEL_STATUS:
        raise ProductionRuleValidationError(f"顶层 status 必须为 active，实际为 {status!r}。")
    if source_scope != ALLOWED_SOURCE_SCOPE:
        raise ProductionRuleValidationError(
            f"顶层 source_scope 必须为 production_rules，实际为 {source_scope!r}。"
        )
    if expert_system not in ALLOWED_PRODUCTION_EXPERT_SYSTEMS:
        raise ProductionRuleValidationError(f"不支持的 expert_system：{expert_system!r}。")
    if expected_expert_system and expert_system != expected_expert_system:
        raise ProductionRuleValidationError(
            f"文件 expert_system 必须为 {expected_expert_system!r}，实际为 {expert_system!r}。"
        )
    return expert_system  # type: ignore[return-value]


def _resolve_production_path(path: str | Path, *, workspace_root: str | Path) -> Path:
    root = Path(workspace_root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    allowed_roots = [(root / "theory" / name).resolve() for name in DEFAULT_PRODUCTION_FILES]
    if not any(_is_relative_to(resolved, allowed_root) for allowed_root in allowed_roots):
        raise ProductionRuleValidationError(
            "生产规则加载器只能读取 theory/ziping 或 theory/tiaohou_ditiansui 下的 YAML 文件："
            f"{resolved}"
        )
    if not resolved.exists():
        raise ProductionRuleValidationError(f"正式生产规则 YAML 不存在：{resolved}")
    if resolved.suffix.lower() not in {".yaml", ".yml"}:
        raise ProductionRuleValidationError(f"正式生产规则文件必须是 YAML：{resolved}")
    return resolved


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _rule_triggered(
    rule: ProductionRule,
    *,
    parsed: Optional[ParsedInput],
    energy: EnergyFindings,
    picture: PictureFindings,
) -> bool:
    trigger = rule.conditions.trigger
    if trigger == "always":
        return parsed is not None
    if trigger == "has_wealth_picture":
        return bool(getattr(picture, "caifu", None) or getattr(picture, "wealth_level", None))
    if trigger == "has_official_picture":
        return bool(getattr(picture, "guanming", None))
    if trigger == "has_marriage_picture":
        return bool(getattr(picture, "marriage_picture", None))
    if trigger == "has_tiaohou_advice":
        return bool(getattr(picture, "tiaohou_advice", None))
    if trigger == "wuxing_imbalanced":
        return _is_wuxing_imbalanced(parsed)
    if trigger == "has_zhi_chong":
        return _has_zhi_chong(parsed)
    if trigger == "has_energy_structure":
        return bool(getattr(energy, "tiyong", None) and getattr(energy, "layer_count", 0) >= 0)
    return False


def _is_wuxing_imbalanced(parsed: Optional[ParsedInput]) -> bool:
    if parsed is None or not getattr(parsed, "bazi", None):
        return False
    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for _, gan in parsed.bazi.all_gans():
        counts[GAN_TO_WUXING[gan]] += 1
    for _, zhi in parsed.bazi.all_zhis():
        counts[ZHI_TO_WUXING[zhi]] += 1
    values = list(counts.values())
    return max(values) - min(values) >= 2 or any(value == 0 for value in values)


def _has_zhi_chong(parsed: Optional[ParsedInput]) -> bool:
    if parsed is None or not getattr(parsed, "bazi", None):
        return False
    zhis = [zhi for _, zhi in parsed.bazi.all_zhis()]
    for idx, left in enumerate(zhis):
        for right in zhis[idx + 1:]:
            if zhi_chong(left, right):
                return True
    return False
