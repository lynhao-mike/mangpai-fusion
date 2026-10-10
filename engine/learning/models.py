"""L9 条件化学习的不可变数据契约。"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, fields
from types import MappingProxyType
from typing import Any, ClassVar, Mapping, TypeVar

_T = TypeVar("_T", bound="FrozenContract")


def _require(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _probability(value: float, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set | frozenset):
        return frozenset(_freeze(item) for item in value)
    return deepcopy(value)


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple | frozenset):
        return [_thaw(item) for item in value]
    return deepcopy(value)


class FrozenContract:
    """为 frozen dataclass 提供 JSON 友好序列化。"""

    _tuple_fields: ClassVar[frozenset[str]] = frozenset()

    def to_dict(self) -> dict[str, Any]:
        return {field.name: _thaw(getattr(self, field.name)) for field in fields(self)}

    @classmethod
    def from_dict(cls: type[_T], data: Mapping[str, Any]) -> _T:
        copied = deepcopy(dict(data))
        for name in cls._tuple_fields:
            if copied.get(name) is not None:
                copied[name] = tuple(copied[name])
        return cls(**copied)


@dataclass(frozen=True)
class ConditionalIdentity(FrozenContract):
    school_id: str
    task_id: str
    chart_prototype_id: str
    claim_type: str
    time_horizon: str
    evidence_completeness_band: str

    def __post_init__(self) -> None:
        for declared_field in fields(self):
            _require(getattr(self, declared_field.name), declared_field.name)

    @property
    def key(self) -> str:
        return "|".join(
            (
                self.school_id,
                self.task_id,
                self.chart_prototype_id,
                self.claim_type,
                self.time_horizon,
                self.evidence_completeness_band,
            )
        )


@dataclass(frozen=True)
class ConditionalLearningSignal(FrozenContract):
    signal_id: str
    feedback_observation_id: str
    claim_id: str
    rule_id: str
    identity: ConditionalIdentity
    verdict: str
    feedback_quality: float
    attributable: bool
    time_error: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        for name in ("signal_id", "feedback_observation_id", "claim_id", "rule_id"):
            _require(getattr(self, name), name)
        if not isinstance(self.identity, ConditionalIdentity):
            raise TypeError("identity must be ConditionalIdentity")
        if self.verdict not in {"hit", "miss", "partial", "no_data"}:
            raise ValueError("verdict must be hit, miss, partial, or no_data")
        if not self.attributable and self.verdict != "no_data":
            raise ValueError("unattributable signal verdict must be no_data")
        _probability(self.feedback_quality, "feedback_quality")
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    @property
    def effective_weight(self) -> float:
        return 0.0 if not self.attributable or self.verdict == "no_data" else self.feedback_quality

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["identity"] = self.identity.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConditionalLearningSignal":
        copied = deepcopy(dict(data))
        copied["identity"] = ConditionalIdentity.from_dict(copied["identity"])
        return cls(**copied)


@dataclass(frozen=True)
class LearningThresholds(FrozenContract):
    medium_n_eff: float
    mature_n_eff: float
    partial_weight: float
    max_posterior_delta: float
    large_change_delta: float

    def __post_init__(self) -> None:
        if self.medium_n_eff < 0:
            raise ValueError("medium_n_eff must be non-negative")
        if self.mature_n_eff < self.medium_n_eff:
            raise ValueError("mature_n_eff must be at least medium_n_eff")
        _probability(self.partial_weight, "partial_weight")
        if not 0.0 < self.max_posterior_delta <= 1.0:
            raise ValueError("max_posterior_delta must be between 0 exclusive and 1")
        if not 0.0 < self.large_change_delta <= 1.0:
            raise ValueError("large_change_delta must be between 0 exclusive and 1")


@dataclass(frozen=True)
class LearningDecision(FrozenContract):
    decision_id: str
    signal_id: str
    target_identity: ConditionalIdentity
    update_tier: str
    proposed_delta: float
    proposed_posterior_mean: float
    proposed_credible_interval: tuple[float, float]
    n_eff_before: float
    n_eff_after: float
    applied: bool
    requires_human_approval: bool
    snapshot_ref: str | None
    rationale: str
    audit: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    _tuple_fields: ClassVar[frozenset[str]] = frozenset({"proposed_credible_interval"})

    def __post_init__(self) -> None:
        for name in ("decision_id", "signal_id", "rationale"):
            _require(getattr(self, name), name)
        if self.update_tier not in {
            "record_only",
            "adjust_applicability",
            "adjust_rule_prior",
            "manual_review",
        }:
            raise ValueError("invalid update_tier")
        _probability(self.proposed_posterior_mean, "proposed_posterior_mean")
        low, high = self.proposed_credible_interval
        if not 0.0 <= low <= high <= 1.0:
            raise ValueError("proposed_credible_interval must satisfy 0 <= low <= high <= 1")
        if self.n_eff_before < 0 or self.n_eff_after < 0:
            raise ValueError("n_eff must be non-negative")
        object.__setattr__(self, "audit", _freeze(self.audit))

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["target_identity"] = self.target_identity.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LearningDecision":
        copied = deepcopy(dict(data))
        copied["target_identity"] = ConditionalIdentity.from_dict(copied["target_identity"])
        copied["proposed_credible_interval"] = tuple(copied["proposed_credible_interval"])
        return cls(**copied)


@dataclass(frozen=True)
class ManualReviewItem(FrozenContract):
    review_id: str
    signal_id: str
    decision_id: str | None
    reason: str
    target_identity: ConditionalIdentity
    context: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        for name in ("review_id", "signal_id", "reason"):
            _require(getattr(self, name), name)
        object.__setattr__(self, "context", _freeze(self.context))

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["target_identity"] = self.target_identity.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ManualReviewItem":
        copied = deepcopy(dict(data))
        copied["target_identity"] = ConditionalIdentity.from_dict(copied["target_identity"])
        return cls(**copied)
