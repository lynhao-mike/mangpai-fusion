from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from engine.application.production_rule_models import (
    ALLOWED_SOURCE_SCOPE,
    ALLOWED_TOP_LEVEL_STATUS,
    ProductionExpertSystem,
    ProductionRule,
    ProductionRuleSet,
    ProductionRuleValidationError,
)

DEFAULT_PRODUCTION_FILES: dict[ProductionExpertSystem, Path] = {
    "ziping": Path("theory/ziping/index.yaml"),
    "tiaohou_ditiansui": Path("theory/tiaohou_ditiansui/index.yaml"),
}
_EXPERT_SYSTEM_BY_RAW: dict[str, ProductionExpertSystem] = {
    "ziping": "ziping",
    "tiaohou_ditiansui": "tiaohou_ditiansui",
}


def load_production_rule_set(
    path: str | Path,
    *,
    expected_expert_system: ProductionExpertSystem | None = None,
    workspace_root: str | Path = ".",
) -> ProductionRuleSet:
    resolved_path = _resolve_production_path(path, workspace_root=workspace_root)
    raw = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ProductionRuleValidationError(f"{resolved_path} 顶层必须是 YAML mapping。")
    expert_system = _validate_top_level(
        raw,
        expected_expert_system=expected_expert_system,
    )
    rules_raw = raw.get("rules", [])
    if not isinstance(rules_raw, list):
        raise ProductionRuleValidationError(f"{resolved_path} rules 必须是 list。")
    rules = [
        ProductionRule.from_dict(item, expected_expert_system=expert_system)
        for item in rules_raw
    ]
    return ProductionRuleSet(
        schema_version=str(raw.get("schema_version", "")),
        status="active",
        source_scope="production_rules",
        expert_system=expert_system,
        notes=str(raw.get("notes", "")),
        rules=rules,
        source_path=resolved_path,
    )


def _validate_top_level(
    raw: dict[str, Any],
    *,
    expected_expert_system: ProductionExpertSystem | None,
) -> ProductionExpertSystem:
    status = str(raw.get("status", ""))
    source_scope = str(raw.get("source_scope", ""))
    expert_system = str(raw.get("expert_system", ""))
    if status != ALLOWED_TOP_LEVEL_STATUS:
        raise ProductionRuleValidationError(
            f"顶层 status 必须为 active，实际为 {status!r}。"
        )
    if source_scope != ALLOWED_SOURCE_SCOPE:
        raise ProductionRuleValidationError(
            "顶层 source_scope 必须为 production_rules，"
            f"实际为 {source_scope!r}。"
        )
    validated_system = _EXPERT_SYSTEM_BY_RAW.get(expert_system)
    if validated_system is None:
        raise ProductionRuleValidationError(
            f"不支持的 expert_system：{expert_system!r}。"
        )
    if expected_expert_system and validated_system != expected_expert_system:
        raise ProductionRuleValidationError(
            f"文件 expert_system 必须为 {expected_expert_system!r}，"
            f"实际为 {validated_system!r}。"
        )
    return validated_system


def _resolve_production_path(
    path: str | Path,
    *,
    workspace_root: str | Path,
) -> Path:
    root = Path(workspace_root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    allowed_roots = [
        (root / "theory" / name).resolve() for name in DEFAULT_PRODUCTION_FILES
    ]
    if not any(_is_relative_to(resolved, allowed_root) for allowed_root in allowed_roots):
        raise ProductionRuleValidationError(
            "生产规则加载器只能读取 theory/ziping 或 "
            f"theory/tiaohou_ditiansui 下的 YAML 文件：{resolved}"
        )
    if not resolved.exists():
        raise ProductionRuleValidationError(f"正式生产规则 YAML 不存在：{resolved}")
    if resolved.suffix.lower() not in {".yaml", ".yml"}:
        raise ProductionRuleValidationError(f"正式生产规则文件必须是 YAML：{resolved}")
    return resolved


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
