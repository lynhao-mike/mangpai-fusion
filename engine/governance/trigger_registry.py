from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Never, assert_never

from engine.governance.contracts import FactSnapshot, GovernanceFact
from engine.governance.fact_values import TemporalLayer


@dataclass(frozen=True, slots=True)
class TriggerRegistryContractError(Exception):
    issue_code: str
    field_path: str
    diagnostic: str

    def __str__(self) -> str:
        return self.diagnostic


def _reject(issue_code: str, field_path: str, diagnostic: str) -> Never:
    raise TriggerRegistryContractError(issue_code, field_path, diagnostic)


@unique
class TriggerIssueCode(StrEnum):
    UNKNOWN_TRIGGER = "unknown_trigger"
    UNPUBLISHED_TRIGGER = "unpublished_trigger"
    MISSING_REQUIRED_FACT = "missing_required_fact"


@unique
class TriggerEvaluatorId(StrEnum):
    FACT_KIND_PRESENT = "fact_kind_present"
    LIUNIAN_TARGET_YEAR_PRESENT = "liunian_target_year_present"


@unique
class TriggerPublicationStatus(StrEnum):
    CANDIDATE = "candidate"
    SYNTHETIC_ONLY = "synthetic_only"
    PUBLISHED = "published"


@unique
class MissingInputBehavior(StrEnum):
    INACTIVE_WITH_ISSUE = "inactive_with_issue"


@dataclass(frozen=True, slots=True)
class TriggerEvaluationContext:
    as_of_date: str | None = None
    parsed_present: bool = False

    def __post_init__(self) -> None:
        if self.as_of_date is not None and (
            type(self.as_of_date) is not str or not self.as_of_date.strip()
        ):
            _reject("TRIGGER.CONTEXT_AS_OF_DATE", "as_of_date", "invalid as-of date")
        if type(self.parsed_present) is not bool:
            _reject("TRIGGER.CONTEXT_PARSED", "parsed_present", "invalid parsed flag")


@dataclass(frozen=True, slots=True)
class TriggerOutcome:
    active: bool
    issues: tuple[TriggerIssueCode, ...]

    def __post_init__(self) -> None:
        if type(self.active) is not bool:
            _reject("TRIGGER.OUTCOME", "active", "active must be boolean")
        if type(self.issues) is not tuple or any(
            type(issue) is not TriggerIssueCode for issue in self.issues
        ):
            _reject("TRIGGER.ISSUES", "issues", "issues must be trigger issue codes")


@dataclass(frozen=True, slots=True)
class TriggerRegistrationSpec:
    trigger_id: str
    evaluator_id: str
    evaluator_version: str
    required_fact_kinds: tuple[str, ...]
    allowed_temporal_layers: tuple[str, ...]
    missing_input_behavior: str
    publication_status: str


@dataclass(frozen=True, slots=True)
class TriggerRegistration:
    trigger_id: str
    evaluator_id: TriggerEvaluatorId
    evaluator_version: str
    required_fact_kinds: tuple[str, ...]
    allowed_temporal_layers: tuple[TemporalLayer, ...]
    missing_input_behavior: MissingInputBehavior
    publication_status: TriggerPublicationStatus

    def __post_init__(self) -> None:
        _text("trigger_id", self.trigger_id)
        _text("evaluator_version", self.evaluator_version)
        if type(self.evaluator_id) is not TriggerEvaluatorId:
            _reject("TRIGGER.EVALUATOR_ID", "evaluator_id", "unsupported evaluator")
        if type(self.missing_input_behavior) is not MissingInputBehavior:
            _reject(
                "TRIGGER.MISSING_INPUT",
                "missing_input_behavior",
                "unsupported missing input behavior",
            )
        if type(self.publication_status) is not TriggerPublicationStatus:
            _reject("TRIGGER.STATUS", "publication_status", "unsupported status")
        object.__setattr__(
            self,
            "required_fact_kinds",
            _strings("required_fact_kinds", self.required_fact_kinds),
        )
        layers = self.allowed_temporal_layers
        if type(layers) is not tuple or not layers:
            _reject("TRIGGER.TEMPORAL_LAYERS", "allowed_temporal_layers", "required")
        if any(type(layer) is not TemporalLayer for layer in layers):
            _reject(
                "TRIGGER.TEMPORAL_LAYERS",
                "allowed_temporal_layers",
                "unsupported temporal layer",
            )
        if len(layers) != len(set(layers)):
            _reject(
                "TRIGGER.TEMPORAL_LAYERS",
                "allowed_temporal_layers",
                "duplicate temporal layer",
            )


@dataclass(frozen=True, slots=True)
class TriggerRegistry:
    triggers: tuple[TriggerRegistration, ...]

    def __post_init__(self) -> None:
        if type(self.triggers) is not tuple or any(
            type(item) is not TriggerRegistration for item in self.triggers
        ):
            _reject("TRIGGER.REGISTRY", "triggers", "invalid trigger registry")
        identities = tuple(item.trigger_id for item in self.triggers)
        if len(identities) != len(set(identities)):
            _reject("TRIGGER.DUPLICATE", "trigger_id", "duplicate trigger ID")

    def lookup(self, trigger_id: str) -> TriggerRegistration | None:
        _text("trigger_id", trigger_id)
        for trigger in self.triggers:
            if trigger.trigger_id == trigger_id:
                return trigger
        return None


def _text(field_path: str, value: str) -> str:
    if type(value) is not str or not value.strip():
        _reject("TRIGGER.TEXT", field_path, f"{field_path} must be nonempty")
    return value


def _strings(field_path: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        _reject("TRIGGER.STRINGS", field_path, f"{field_path} must be nonempty")
    normalized = tuple(sorted(_text(field_path, value) for value in values))
    if len(normalized) != len(set(normalized)):
        _reject("TRIGGER.STRINGS", field_path, f"{field_path} contains duplicates")
    return normalized


def _evaluator(value: str) -> TriggerEvaluatorId:
    for evaluator in TriggerEvaluatorId:
        if value == evaluator.value:
            return evaluator
    _reject("TRIGGER.EVALUATOR_ID", "evaluator_id", "unsupported evaluator")


def _layer(value: str) -> TemporalLayer:
    for layer in TemporalLayer:
        if value == layer.value:
            return layer
    _reject(
        "TRIGGER.TEMPORAL_LAYER",
        "allowed_temporal_layers",
        "unsupported temporal layer",
    )


def _missing_behavior(value: str) -> MissingInputBehavior:
    for behavior in MissingInputBehavior:
        if value == behavior.value:
            return behavior
    _reject(
        "TRIGGER.MISSING_INPUT",
        "missing_input_behavior",
        "unsupported missing input behavior",
    )


def _status(value: str) -> TriggerPublicationStatus:
    for status in TriggerPublicationStatus:
        if value == status.value:
            return status
    _reject("TRIGGER.STATUS", "publication_status", "unsupported status")


def _registration(spec: TriggerRegistrationSpec) -> TriggerRegistration:
    if type(spec) is not TriggerRegistrationSpec:
        _reject("TRIGGER.SPEC", "trigger", "invalid trigger spec")
    version = _text("evaluator_version", spec.evaluator_version)
    if version != "1.0.0":
        _reject(
            "TRIGGER.EVALUATOR_VERSION",
            "evaluator_version",
            "unsupported evaluator version",
        )
    return TriggerRegistration(
        trigger_id=_text("trigger_id", spec.trigger_id),
        evaluator_id=_evaluator(spec.evaluator_id),
        evaluator_version=version,
        required_fact_kinds=_strings("required_fact_kinds", spec.required_fact_kinds),
        allowed_temporal_layers=tuple(
            _layer(value) for value in spec.allowed_temporal_layers
        ),
        missing_input_behavior=_missing_behavior(spec.missing_input_behavior),
        publication_status=_status(spec.publication_status),
    )


def build_trigger_registry(
    entries: tuple[TriggerRegistrationSpec, ...],
) -> TriggerRegistry:
    if type(entries) is not tuple:
        _reject("TRIGGER.REGISTRY", "triggers", "trigger entries must be a tuple")
    return TriggerRegistry(tuple(_registration(entry) for entry in entries))


def _declared_facts(
    trigger: TriggerRegistration, snapshot: FactSnapshot
) -> tuple[GovernanceFact, ...]:
    required = set(trigger.required_fact_kinds)
    visible = tuple(fact for fact in snapshot.facts if fact.fact_kind in required)
    found = {fact.fact_kind for fact in visible}
    if required - found:
        return ()
    return tuple(
        fact
        for fact in visible
        if fact.temporal_scope.layer in trigger.allowed_temporal_layers
    )


def _evaluate(
    evaluator_id: TriggerEvaluatorId,
    facts: tuple[GovernanceFact, ...],
) -> bool:
    match evaluator_id:
        case TriggerEvaluatorId.FACT_KIND_PRESENT:
            return bool(facts)
        case TriggerEvaluatorId.LIUNIAN_TARGET_YEAR_PRESENT:
            return any(
                fact.temporal_scope.layer is TemporalLayer.LIUNIAN
                and fact.temporal_scope.target_year is not None
                for fact in facts
            )
        case unreachable:
            assert_never(unreachable)


def evaluate_governance_trigger(
    registry: TriggerRegistry,
    trigger_id: str,
    snapshot: FactSnapshot,
    context: TriggerEvaluationContext,
) -> TriggerOutcome:
    if type(registry) is not TriggerRegistry:
        _reject("TRIGGER.REGISTRY", "registry", "invalid registry")
    if type(snapshot) is not FactSnapshot:
        _reject("TRIGGER.SNAPSHOT", "snapshot", "invalid fact snapshot")
    if type(context) is not TriggerEvaluationContext:
        _reject("TRIGGER.CONTEXT", "context", "invalid evaluation context")
    trigger = registry.lookup(trigger_id)
    if trigger is None:
        return TriggerOutcome(False, (TriggerIssueCode.UNKNOWN_TRIGGER,))
    if trigger.publication_status is not TriggerPublicationStatus.PUBLISHED:
        return TriggerOutcome(False, (TriggerIssueCode.UNPUBLISHED_TRIGGER,))
    facts = _declared_facts(trigger, snapshot)
    if not facts:
        return TriggerOutcome(False, (TriggerIssueCode.MISSING_REQUIRED_FACT,))
    return TriggerOutcome(_evaluate(trigger.evaluator_id, facts), ())


def load_trigger_registry() -> TriggerRegistry:
    from engine.governance.trigger_loader import load_trigger_registry as load

    return load()
