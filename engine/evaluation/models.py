from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, TypeVar

OutputState = Literal["claim", "abstain", "unsupported"]
_T = TypeVar("_T", bound="PersistedContract")


class PersistedContract:
    def to_dict(self) -> dict[str, Any]:
        return deepcopy(asdict(self))

    @classmethod
    def from_dict(cls: type[_T], data: dict[str, Any]) -> _T:
        return cls(**deepcopy(data))


def _require(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} is required")


def _rate(value: float | None, name: str) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class BlindTask(PersistedContract):
    task_id: str
    domain: str
    claim_type: str
    scoring_method: str
    quantifiable: bool
    high_risk: bool
    allowed_time_horizons: list[str]
    required_input_fields: list[str]
    label_schema: dict[str, Any]
    evaluation_note: str

    def __post_init__(self) -> None:
        _require(self.task_id, "task_id")
        _require(self.domain, "domain")
        _require(self.scoring_method, "scoring_method")
        if self.quantifiable and not self.label_schema:
            raise ValueError("quantifiable task requires non-empty label_schema")


@dataclass(frozen=True)
class CaseAuditRecord(PersistedContract):
    case_id: str
    has_input: bool
    has_feedback: bool
    has_statement_index: bool
    has_existing_report: bool
    feedback_quantifiable: bool
    contamination_flags: list[str]
    eligibility: str
    evidence_notes: list[str]

    def __post_init__(self) -> None:
        _require(self.case_id, "case_id")


@dataclass(frozen=True)
class BlindPrediction(PersistedContract):
    prediction_id: str
    event_label: str
    probability: float
    time_window: dict[str, int | str]
    evidence_refs: list[str]
    falsifier: str

    def __post_init__(self) -> None:
        _rate(self.probability, "probability")
        _require(self.event_label, "event_label")
        _require(self.falsifier, "falsifier")


@dataclass(frozen=True)
class BlindSchoolOutput(PersistedContract):
    case_id: str
    school_id: str
    task_id: str
    state: OutputState
    rationale: str
    predictions: list[BlindPrediction] = field(default_factory=list)
    counter_evidence: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require(self.case_id, "case_id")
        _require(self.school_id, "school_id")
        _require(self.task_id, "task_id")
        if self.state not in ("claim", "abstain", "unsupported"):
            raise ValueError("state must be claim, abstain, or unsupported")
        if self.state == "claim" and not self.predictions:
            raise ValueError("claim requires at least one prediction")
        if self.state != "claim" and self.predictions:
            raise ValueError(f"{self.state} cannot contain predictions")
        _require(self.rationale, "rationale")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BlindSchoolOutput:
        copied = deepcopy(data)
        copied["predictions"] = [BlindPrediction.from_dict(item) for item in copied.get("predictions", [])]
        return cls(**copied)


@dataclass(frozen=True)
class FrozenBlindRun(PersistedContract):
    task_catalog_version: str
    rule_snapshot_id: str
    frozen_at: str
    outputs: list[BlindSchoolOutput]
    freeze_hash: str
    schema_version: str = "school-capability-frozen-run/v1"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FrozenBlindRun:
        copied = deepcopy(data)
        copied["outputs"] = [BlindSchoolOutput.from_dict(item) for item in copied["outputs"]]
        return cls(**copied)


@dataclass(frozen=True)
class RevealedLabel(PersistedContract):
    case_id: str
    task_id: str
    label: Any
    observed_at: str
    source: str
    confidence_grade: str
    quantifiable: bool
    conflict_state: str

    def __post_init__(self) -> None:
        _require(self.case_id, "case_id")
        _require(self.task_id, "task_id")


@dataclass(frozen=True)
class ScoreRecord(PersistedContract):
    case_id: str
    school_id: str
    task_id: str
    claim_type: str
    state: OutputState
    abstained: bool
    knowledge_coverage: bool
    chart_prototype_id: str = "unclassified"
    time_horizon: str = "unspecified"
    evidence_completeness_band: str = "unknown"
    probability_score: float | None = None
    timing_score: float | None = None
    ordinal_score: float | None = None
    portrait_agreement: float | None = None
    utility: float | None = None
    observed_positive: bool | None = None

    def __post_init__(self) -> None:
        _require(self.case_id, "case_id")
        _require(self.school_id, "school_id")
        _require(self.task_id, "task_id")
        if self.state not in ("claim", "abstain", "unsupported"):
            raise ValueError("state must be claim, abstain, or unsupported")
        for name in ("probability_score", "timing_score", "ordinal_score", "portrait_agreement"):
            _rate(getattr(self, name), name)


@dataclass(frozen=True)
class CapabilityPosterior(PersistedContract):
    school_id: str
    task_id: str
    chart_prototype_id: str
    claim_type: str
    time_horizon: str
    evidence_completeness_band: str
    coverage_rate: float
    discrimination_score: float
    accuracy_score: float
    calibration_error: float | None
    posterior_mean: float
    credible_interval: tuple[float, float]
    n_eff: float
    evidence_grade: str
    last_evaluated_at: str
    incremental_gain: float = 0.0

    def __post_init__(self) -> None:
        _require(self.school_id, "school_id")
        _require(self.task_id, "task_id")
        for name in ("coverage_rate", "discrimination_score", "accuracy_score", "calibration_error", "posterior_mean"):
            _rate(getattr(self, name), name)
        low, high = self.credible_interval
        if not 0.0 <= low <= high <= 1.0:
            raise ValueError("credible_interval must satisfy 0 <= low <= high <= 1")
        if self.n_eff < 0:
            raise ValueError("n_eff must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["credible_interval"] = list(self.credible_interval)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityPosterior:
        copied = deepcopy(data)
        copied["credible_interval"] = tuple(copied["credible_interval"])
        return cls(**copied)
