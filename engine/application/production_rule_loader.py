from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

from engine.application.production_rule_models import (
    ALLOWED_PRODUCTION_EXPERT_SYSTEMS,
    ALLOWED_RULE_STATUS,
    ALLOWED_SOURCE_SCOPE,
    ALLOWED_TOP_LEVEL_STATUS,
    EXPERT_DISPLAY_NAMES,
    ProductionExpertSystem,
    ProductionRule,
    ProductionRuleConditions,
    ProductionRuleOutput,
    ProductionRuleSet,
    ProductionRuleSource,
    ProductionRuleValidationError,
)
from engine.application.production_rule_triggers import (
    _has_guansha_mixed as _has_guansha_mixed,
    _has_hour_qisha as _has_hour_qisha,
    _has_qisha_structure as _has_qisha_structure,
    _has_qisha_with_control as _has_qisha_with_control,
    rule_triggered,
)
from engine.application.production_rule_validation import (
    DEFAULT_PRODUCTION_FILES,
    load_production_rule_set,
)
from engine.energy.types import EnergyFindings
from engine.picture.types import PictureFindings
from engine.predicates.types import ParsedInput

_DEFAULT_LIBRARY_CACHE: ProductionRuleLibrary | None = None
_LOGGER = logging.getLogger(__name__)
_rule_triggered = rule_triggered

__all__ = [
    "ALLOWED_PRODUCTION_EXPERT_SYSTEMS",
    "ALLOWED_RULE_STATUS",
    "ALLOWED_SOURCE_SCOPE",
    "ALLOWED_TOP_LEVEL_STATUS",
    "DEFAULT_PRODUCTION_FILES",
    "EXPERT_DISPLAY_NAMES",
    "ProductionExpertSystem",
    "ProductionRule",
    "ProductionRuleConditions",
    "ProductionRuleLibrary",
    "ProductionRuleOutput",
    "ProductionRuleSet",
    "ProductionRuleSource",
    "ProductionRuleValidationError",
    "load_default_production_library",
    "load_production_library",
    "load_production_rule_set",
]


@dataclass(frozen=True, slots=True)
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
        parsed: ParsedInput | None,
        energy: EnergyFindings,
        picture: PictureFindings,
    ) -> list[ProductionRule]:
        return [
            rule
            for rule in self.rules
            if rule_triggered(rule, parsed=parsed, energy=energy, picture=picture)
        ]

    def to_dict(self) -> dict[str, Any]:
        return {key: value.to_dict() for key, value in self.rule_sets.items()}


def load_default_production_library(
    *,
    workspace_root: str | Path = ".",
) -> ProductionRuleLibrary:
    global _DEFAULT_LIBRARY_CACHE
    if _DEFAULT_LIBRARY_CACHE is not None and str(workspace_root) == ".":
        return _DEFAULT_LIBRARY_CACHE

    rule_sets: dict[ProductionExpertSystem, ProductionRuleSet] = {}
    for expert_system, path in DEFAULT_PRODUCTION_FILES.items():
        try:
            rule_sets[expert_system] = load_production_rule_set(
                path,
                expected_expert_system=expert_system,
                workspace_root=workspace_root,
            )
        except (
            KeyError,
            OSError,
            TypeError,
            ProductionRuleValidationError,
            yaml.YAMLError,
        ) as error:
            _LOGGER.warning("生产规则集 %s 加载跳过：%s", expert_system, error)

    library = ProductionRuleLibrary(rule_sets=rule_sets)
    if str(workspace_root) == ".":
        _DEFAULT_LIBRARY_CACHE = library
    return library


def load_production_library(
    paths: Iterable[str | Path],
    *,
    workspace_root: str | Path = ".",
) -> ProductionRuleLibrary:
    rule_sets: dict[ProductionExpertSystem, ProductionRuleSet] = {}
    for path in paths:
        rule_set = load_production_rule_set(path, workspace_root=workspace_root)
        if rule_set.expert_system in rule_sets:
            raise ProductionRuleValidationError(
                f"重复加载 expert_system={rule_set.expert_system!r}。"
            )
        rule_sets[rule_set.expert_system] = rule_set
    return ProductionRuleLibrary(rule_sets=rule_sets)
