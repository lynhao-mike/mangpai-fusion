"""严格、只读、版本化的 production Claim 可执行规则加载与求值。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml


CLAIM_RULE_SCHEMA_VERSION = "claim-executable-rules/v1"
DEFAULT_CLAIM_RULE_PATH = Path(__file__).resolve().parents[2] / "theory" / "production" / "claim-rules-v1.yaml"
_ALLOWED_OPERATORS = frozenset({"eq", "ne", "gte", "lte", "in", "not_in", "truthy", "falsy"})
_ALLOWED_OUTCOMES = frozenset({"success", "fail", "unknown"})
_ALLOWED_SCHOOLS = frozenset({"duan", "gao", "yang"})
_ALLOWED_LIFECYCLE_STATES = frozenset({"staged", "production-candidate"})
_TOP_LEVEL_FIELDS = frozenset({"schema_version", "rules"})
_REQUIRED_RULE_FIELDS = frozenset(
    {
        "rule_id", "school_id", "task_scope", "claim_type", "required_facts", "conditions",
        "exclusions", "counter_conditions", "conclusion_template", "confidence_basis", "falsifier",
        "source_refs", "lifecycle_state",
    }
)
_OPTIONAL_RULE_FIELDS = frozenset(
    {"predicted_label", "base_confidence", "high_risk_confidence_cap", "polarity"}
)
_CONDITION_FIELDS = frozenset({"fact", "op", "value"})
_SOURCE_REF_FIELDS = frozenset({"path", "locator", "supports"})
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class RuleSchemaError(ValueError):
    """规则文件不满足 claim-executable-rules/v1 严格 schema。"""


class RuleEvaluationError(ValueError):
    """规则上下文缺失或条件比较类型不合法。"""


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_value(item) for key, item in value.items()})
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(_freeze_value(item) for item in value)
    return value


@dataclass(frozen=True)
class RuleCondition:
    fact: str
    op: str
    value: Any

    def __post_init__(self) -> None:
        if not isinstance(self.fact, str) or not self.fact.strip():
            raise RuleSchemaError("condition fact must be non-empty")
        if self.op not in _ALLOWED_OPERATORS:
            raise RuleSchemaError(f"unknown condition operator: {self.op}")
        object.__setattr__(self, "value", _freeze_value(self.value))


@dataclass(frozen=True)
class SourceRef:
    path: str
    locator: str
    supports: str

    def __post_init__(self) -> None:
        for name in ("path", "locator", "supports"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise RuleSchemaError(f"source_refs.{name} must be non-empty")


@dataclass(frozen=True)
class ExecutableClaimRule:
    rule_id: str
    school_id: str
    task_scope: tuple[str, ...]
    claim_type: str
    required_facts: tuple[str, ...]
    conditions: tuple[RuleCondition, ...]
    exclusions: tuple[RuleCondition, ...]
    counter_conditions: tuple[RuleCondition, ...]
    conclusion_template: str
    confidence_basis: str
    falsifier: str
    source_refs: tuple[SourceRef, ...]
    lifecycle_state: str
    predicted_label: str | None = None
    base_confidence: float = 0.5
    high_risk_confidence_cap: float | None = None
    polarity: str = "neutral"


@dataclass(frozen=True)
class RuleEvaluationResult:
    matched: bool
    matched_conditions: tuple[RuleCondition, ...]
    failed_conditions: tuple[RuleCondition, ...]
    matched_exclusions: tuple[RuleCondition, ...]
    matched_counter_conditions: tuple[RuleCondition, ...]
    triggered: bool = False
    outcome: str = "unknown"

    def __post_init__(self) -> None:
        if self.outcome not in _ALLOWED_OUTCOMES:
            raise ValueError(f"unknown rule outcome: {self.outcome}")
        if not self.triggered and self.outcome != "unknown":
            raise ValueError(f"outcome={self.outcome!r} requires triggered=True")


@dataclass(frozen=True)
class ClaimRuleRegistry:
    schema_version: str
    rules: tuple[ExecutableClaimRule, ...]
    by_id: Mapping[str, ExecutableClaimRule]

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))
        object.__setattr__(self, "by_id", MappingProxyType(dict(self.by_id)))

    def __len__(self) -> int:
        return len(self.rules)

    @property
    def rule_ids(self) -> tuple[str, ...]:
        return tuple(rule.rule_id for rule in self.rules)

    def get(self, rule_id: str) -> ExecutableClaimRule:
        try:
            return self.by_id[rule_id]
        except KeyError as exc:
            raise KeyError(f"unknown claim rule: {rule_id}") from exc

    def find(self, *, school_id: str, task_id: str) -> tuple[ExecutableClaimRule, ...]:
        return tuple(rule for rule in self.rules if rule.school_id == school_id and task_id in rule.task_scope)


def _require_mapping(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuleSchemaError(f"{location} must be a mapping")
    return value


def _non_empty_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuleSchemaError(f"{location} must be non-empty")
    return value


def _string_tuple(value: Any, location: str, *, non_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise RuleSchemaError(f"{location} must be a list")
    result = tuple(_non_empty_string(item, location) for item in value)
    if non_empty and not result:
        raise RuleSchemaError(f"{location} must be non-empty")
    return result


def _parse_conditions(value: Any, location: str, *, non_empty: bool = False) -> tuple[RuleCondition, ...]:
    if not isinstance(value, list):
        raise RuleSchemaError(f"{location} must be a list")
    if non_empty and not value:
        raise RuleSchemaError(f"{location} must be non-empty")
    conditions: list[RuleCondition] = []
    for index, raw in enumerate(value):
        condition = _require_mapping(raw, f"{location}[{index}]")
        unknown = set(condition) - _CONDITION_FIELDS
        missing = _CONDITION_FIELDS - set(condition)
        if unknown:
            raise RuleSchemaError(f"{location}[{index}] unknown fields: {sorted(unknown)}")
        if missing:
            raise RuleSchemaError(f"{location}[{index}] missing fields: {sorted(missing)}")
        conditions.append(RuleCondition(str(condition["fact"]), str(condition["op"]), condition["value"]))
    return tuple(conditions)


def _parse_sources(value: Any, rule_id: str) -> tuple[SourceRef, ...]:
    if not isinstance(value, list) or not value:
        raise RuleSchemaError(f"{rule_id}.source_refs must be non-empty")
    result: list[SourceRef] = []
    for index, raw in enumerate(value):
        item = _require_mapping(raw, f"{rule_id}.source_refs[{index}]")
        unknown = set(item) - _SOURCE_REF_FIELDS
        missing = _SOURCE_REF_FIELDS - set(item)
        if unknown or missing:
            raise RuleSchemaError(
                f"{rule_id}.source_refs[{index}] invalid fields; unknown={sorted(unknown)}, missing={sorted(missing)}"
            )
        source = SourceRef(str(item["path"]), str(item["locator"]), str(item["supports"]))
        source_path = (_REPOSITORY_ROOT / Path(source.path)).resolve()
        try:
            source_path.relative_to(_REPOSITORY_ROOT.resolve())
        except ValueError as exc:
            raise RuleSchemaError(f"source path escapes repository: {source.path}") from exc
        if not source_path.is_file():
            raise RuleSchemaError(f"source path does not exist: {source.path}")
        result.append(source)
    return tuple(result)


def _confidence(value: Any, location: str, *, optional: bool = False) -> float | None:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuleSchemaError(f"{location} must be numeric")
    result = float(value)
    if not 0.0 <= result <= 1.0:
        raise RuleSchemaError(f"{location} must be between 0 and 1")
    return result


def _parse_rule(raw: Any, index: int) -> ExecutableClaimRule:
    data = _require_mapping(raw, f"rules[{index}]")
    unknown = set(data) - (_REQUIRED_RULE_FIELDS | _OPTIONAL_RULE_FIELDS)
    missing = _REQUIRED_RULE_FIELDS - set(data)
    if unknown:
        raise RuleSchemaError(f"rules[{index}] unknown rule fields: {sorted(unknown)}")
    if missing:
        raise RuleSchemaError(f"rules[{index}] missing required fields: {sorted(missing)}")

    rule_id = _non_empty_string(data["rule_id"], f"rules[{index}].rule_id")
    school_id = _non_empty_string(data["school_id"], f"{rule_id}.school_id")
    if school_id not in _ALLOWED_SCHOOLS:
        raise RuleSchemaError(f"{rule_id}.school_id must be duan, gao, or yang")
    if data["claim_type"] != "event_claim":
        raise RuleSchemaError(f"{rule_id}.claim_type must be event_claim")
    lifecycle_state = _non_empty_string(data["lifecycle_state"], f"{rule_id}.lifecycle_state")
    if lifecycle_state not in _ALLOWED_LIFECYCLE_STATES:
        raise RuleSchemaError(f"{rule_id}.lifecycle_state is invalid")
    polarity = str(data.get("polarity", "neutral"))
    if polarity not in {"positive", "negative", "neutral"}:
        raise RuleSchemaError(f"{rule_id}.polarity is invalid")

    required_facts = _string_tuple(data["required_facts"], f"{rule_id}.required_facts", non_empty=True)
    conditions = _parse_conditions(data["conditions"], f"{rule_id}.conditions", non_empty=True)
    exclusions = _parse_conditions(data["exclusions"], f"{rule_id}.exclusions")
    counter_conditions = _parse_conditions(data["counter_conditions"], f"{rule_id}.counter_conditions")
    referenced = {condition.fact for condition in (*conditions, *exclusions, *counter_conditions)}
    undeclared = referenced - set(required_facts)
    if undeclared:
        raise RuleSchemaError(f"{rule_id} conditions use undeclared required_facts: {sorted(undeclared)}")

    return ExecutableClaimRule(
        rule_id=rule_id,
        school_id=school_id,
        task_scope=_string_tuple(data["task_scope"], f"{rule_id}.task_scope", non_empty=True),
        claim_type="event_claim",
        required_facts=required_facts,
        conditions=conditions,
        exclusions=exclusions,
        counter_conditions=counter_conditions,
        conclusion_template=_non_empty_string(data["conclusion_template"], f"{rule_id}.conclusion_template"),
        confidence_basis=_non_empty_string(data["confidence_basis"], f"{rule_id}.confidence_basis"),
        falsifier=_non_empty_string(data["falsifier"], f"{rule_id}.falsifier"),
        source_refs=_parse_sources(data["source_refs"], rule_id),
        lifecycle_state=lifecycle_state,
        predicted_label=(
            _non_empty_string(data["predicted_label"], f"{rule_id}.predicted_label")
            if "predicted_label" in data else None
        ),
        base_confidence=float(_confidence(data.get("base_confidence", 0.5), f"{rule_id}.base_confidence")),
        high_risk_confidence_cap=_confidence(
            data.get("high_risk_confidence_cap"), f"{rule_id}.high_risk_confidence_cap", optional=True
        ),
        polarity=polarity,
    )


def load_claim_rule_registry(path: str | Path = DEFAULT_CLAIM_RULE_PATH) -> ClaimRuleRegistry:
    """从显式、固定文件加载规则；严格拒绝 schema 漂移。"""
    rule_path = Path(path)
    try:
        document = yaml.safe_load(rule_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RuleSchemaError(f"cannot load claim rule file: {rule_path}") from exc
    top = _require_mapping(document, "document")
    unknown = set(top) - _TOP_LEVEL_FIELDS
    missing = _TOP_LEVEL_FIELDS - set(top)
    if unknown:
        raise RuleSchemaError(f"unknown top-level fields: {sorted(unknown)}")
    if missing:
        raise RuleSchemaError(f"missing top-level fields: {sorted(missing)}")
    if top["schema_version"] != CLAIM_RULE_SCHEMA_VERSION:
        raise RuleSchemaError(f"unsupported schema_version: {top['schema_version']}")
    if not isinstance(top["rules"], list):
        raise RuleSchemaError("rules must be a list")

    rules = tuple(_parse_rule(raw, index) for index, raw in enumerate(top["rules"]))
    indexed: dict[str, ExecutableClaimRule] = {}
    for rule in rules:
        if rule.rule_id in indexed:
            raise RuleSchemaError(f"duplicate rule_id: {rule.rule_id}")
        indexed[rule.rule_id] = rule
    return ClaimRuleRegistry(CLAIM_RULE_SCHEMA_VERSION, rules, indexed)


def _resolve_fact(context: Mapping[str, Any], fact: str) -> Any:
    current: Any = context
    for part in fact.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise RuleEvaluationError(f"missing context fact: {fact}")
        current = current[part]
    return current


def _same_scalar_type(actual: Any, expected: Any) -> bool:
    if actual is None or expected is None:
        return actual is None and expected is None
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected)
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return True
    return type(actual) is type(expected)


def _condition_matches(condition: RuleCondition, context: Mapping[str, Any]) -> bool:
    actual = _resolve_fact(context, condition.fact)
    expected = condition.value
    op = condition.op
    if op == "truthy":
        return bool(actual)
    if op == "falsy":
        return not bool(actual)
    if op in {"eq", "ne"}:
        if not _same_scalar_type(actual, expected):
            raise RuleEvaluationError(
                f"incompatible types for {condition.fact}: {type(actual).__name__} {op} {type(expected).__name__}"
            )
        result = actual == expected
        return result if op == "eq" else not result
    if op in {"gte", "lte"}:
        if (
            isinstance(actual, bool) or isinstance(expected, bool)
            or not isinstance(actual, (int, float)) or not isinstance(expected, (int, float))
        ):
            raise RuleEvaluationError(f"incompatible numeric comparison for {condition.fact}")
        return actual >= expected if op == "gte" else actual <= expected
    if op in {"in", "not_in"}:
        if not isinstance(expected, tuple):
            raise RuleEvaluationError(f"in/not_in value must be a sequence for {condition.fact}")
        if expected and not all(_same_scalar_type(actual, item) for item in expected):
            raise RuleEvaluationError(f"incompatible membership comparison for {condition.fact}")
        result = actual in expected
        return result if op == "in" else not result
    raise RuleEvaluationError(f"unknown operator at evaluation: {op}")


def evaluate_rule(rule: ExecutableClaimRule, context: Mapping[str, Any]) -> RuleEvaluationResult:
    """严格求值正向条件、排除条件与可审计反证条件。"""
    for fact in rule.required_facts:
        _resolve_fact(context, fact)
    matched_conditions = tuple(item for item in rule.conditions if _condition_matches(item, context))
    failed_conditions = tuple(item for item in rule.conditions if item not in matched_conditions)
    matched_exclusions = tuple(item for item in rule.exclusions if _condition_matches(item, context))
    matched_counters = tuple(item for item in rule.counter_conditions if _condition_matches(item, context))
    triggered = not failed_conditions and not matched_exclusions
    # 本卡只新增 triggered / outcome；matched 仍是旧语义，是否翻转另案裁决。
    if not triggered:
        outcome = "unknown"
    elif matched_counters:
        outcome = "fail"
    else:
        outcome = "success"
    return RuleEvaluationResult(
        matched=not failed_conditions and not matched_exclusions,
        matched_conditions=matched_conditions,
        failed_conditions=failed_conditions,
        matched_exclusions=matched_exclusions,
        matched_counter_conditions=matched_counters,
        triggered=triggered,
        outcome=outcome,
    )
