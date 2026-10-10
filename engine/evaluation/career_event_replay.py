"""事业角色变动历史回放的冻结、揭示与多维评分。

本模块刻意把流程拆成两个阶段：先把仅由命盘生成的预测投影并冻结，之后才允许
用绑定 ``freeze_hash`` 的标签文档揭示现实事件。它不负责读取案例 ``input.md``，
从而避免预测阶段意外获得 known facts、feedback 或 verification。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from engine.asof.career_event_prediction import (
    CAREER_ROLE_CHANGE_MODEL_ID,
    CareerPredictionWindow,
    CareerRoleChangePredictionRun,
)
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import build_chart_feature_vector
from engine.v5.ren_runner import generate_claims as generate_legacy_ren_claims

CAREER_EVENT_REPLAY_SCHEMA = "career-event-replay/v1"
CAREER_EVENT_LABEL_SCHEMA = "career-event-replay-labels/v1"
CAREER_EVENT_SCORE_SCHEMA = "career-event-replay-score/v1"
LEGACY_REN_CAREER_MODEL_ID = "career-role-change-legacy-ren-timing-event-v1"

DatasetClassification = Literal["development_replay_only", "unseen_holdout"]
EventDirection = Literal["positive", "negative", "neutral"]
PredictionStatus = Literal["structure_abstain", "timing_abstain", "predicted"]

_ALLOWED_EVENT_TYPES = frozenset(
    {
        "career.role_change",
        "career.entry",
        "career.job_change",
        "career.transfer",
        "career.promotion",
        "career.demotion",
        "career.exit",
        "career.dismissal",
        "career.unemployment",
        "career.entrepreneurship_start",
        "career.entrepreneurship_failure",
        "career.income_change",
    }
)
_ROLE_CHANGE_CHILDREN = _ALLOWED_EVENT_TYPES - {"career.unemployment"}
_FORBIDDEN_PREDICTION_KEYS = frozenset(
    {
        "known_facts",
        "known_fact_text",
        "feedback",
        "verification",
        "labels",
        "revealed_labels",
        "truth",
        "observed",
        "calibration",
        "event_text",
        "evidence_quote",
    }
)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _require_year(value: object, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    return value


def _require_unit_interval(value: object, field: str) -> float:
    if type(value) not in (int, float):
        raise TypeError(f"{field} must be numeric")
    normalized = float(value)
    if not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{field} must be between 0 and 1")
    return normalized


def _assert_no_forbidden_keys(value: object, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in _FORBIDDEN_PREDICTION_KEYS:
                raise ValueError(f"forbidden revealed field in prediction payload: {path}.{key}")
            _assert_no_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_no_forbidden_keys(child, f"{path}[{index}]")


@dataclass(frozen=True, slots=True)
class CareerEventReplayPrediction:
    """供评分使用的最小盲态预测投影。"""

    case_id: str
    model_id: str
    status: PredictionStatus
    observation_start_year: int
    observation_end_year: int
    predicted_start_year: int | None
    predicted_end_year: int | None
    domain: str | None
    event_type: str | None
    direction: EventDirection | None
    magnitude: float | None

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        _require_text(self.model_id, "model_id")
        if self.status not in {"structure_abstain", "timing_abstain", "predicted"}:
            raise ValueError("invalid career event replay prediction status")
        start = _require_year(self.observation_start_year, "observation_start_year")
        end = _require_year(self.observation_end_year, "observation_end_year")
        if start > end:
            raise ValueError("observation window requires start_year <= end_year")
        predicted_fields = (
            self.predicted_start_year,
            self.predicted_end_year,
            self.domain,
            self.event_type,
            self.direction,
            self.magnitude,
        )
        if self.status != "predicted":
            if any(value is not None for value in predicted_fields):
                raise ValueError("abstained replay prediction cannot contain event fields")
            return
        if any(value is None for value in predicted_fields):
            raise ValueError("predicted replay status requires complete event fields")
        predicted_start = _require_year(self.predicted_start_year, "predicted_start_year")
        predicted_end = _require_year(self.predicted_end_year, "predicted_end_year")
        if predicted_start > predicted_end:
            raise ValueError("predicted window requires start_year <= end_year")
        if predicted_start < start or predicted_end > end:
            raise ValueError("predicted event must remain inside the observation window")
        _require_text(self.domain, "domain")
        if self.event_type not in _ALLOWED_EVENT_TYPES:
            raise ValueError("unsupported career event_type")
        if self.direction not in {"positive", "negative", "neutral"}:
            raise ValueError("invalid career event direction")
        _require_unit_interval(self.magnitude, "magnitude")

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "model_id": self.model_id,
            "status": self.status,
            "observation_start_year": self.observation_start_year,
            "observation_end_year": self.observation_end_year,
            "predicted_start_year": self.predicted_start_year,
            "predicted_end_year": self.predicted_end_year,
            "domain": self.domain,
            "event_type": self.event_type,
            "direction": self.direction,
            "magnitude": self.magnitude,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CareerEventReplayPrediction":
        required = {
            "case_id",
            "model_id",
            "status",
            "observation_start_year",
            "observation_end_year",
            "predicted_start_year",
            "predicted_end_year",
            "domain",
            "event_type",
            "direction",
            "magnitude",
        }
        if set(value) != required:
            raise ValueError("career event replay prediction has invalid schema")
        return cls(**dict(value))


@dataclass(frozen=True, slots=True)
class FrozenCareerEventReplay:
    """标签揭示前冻结的事业事件预测集合。"""

    schema_version: str
    dataset_id: str
    dataset_classification: DatasetClassification
    model_id: str
    predictions: tuple[CareerEventReplayPrediction, ...]
    freeze_hash: str

    def __post_init__(self) -> None:
        if self.schema_version != CAREER_EVENT_REPLAY_SCHEMA:
            raise ValueError("unexpected career event replay schema_version")
        _require_text(self.dataset_id, "dataset_id")
        if self.dataset_classification not in {
            "development_replay_only",
            "unseen_holdout",
        }:
            raise ValueError("invalid dataset_classification")
        _require_text(self.model_id, "model_id")
        predictions = tuple(self.predictions)
        if any(item.model_id != self.model_id for item in predictions):
            raise ValueError("frozen replay predictions must share one model_id")
        identities = [item.case_id for item in predictions]
        if len(set(identities)) != len(identities):
            raise ValueError("duplicate prediction case_id")
        if identities != sorted(identities):
            raise ValueError("frozen predictions must be sorted by case_id")
        object.__setattr__(self, "predictions", predictions)
        if self.freeze_hash and len(self.freeze_hash) != 64:
            raise ValueError("freeze_hash must be a sha256 digest")

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dataset_id": self.dataset_id,
            "dataset_classification": self.dataset_classification,
            "model_id": self.model_id,
            "predictions": [item.to_dict() for item in self.predictions],
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "freeze_hash": self.freeze_hash}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "FrozenCareerEventReplay":
        required = {
            "schema_version",
            "dataset_id",
            "dataset_classification",
            "model_id",
            "predictions",
            "freeze_hash",
        }
        if set(value) != required or not isinstance(value.get("predictions"), list):
            raise ValueError("frozen career event replay has invalid schema")
        return cls(
            schema_version=value["schema_version"],
            dataset_id=value["dataset_id"],
            dataset_classification=value["dataset_classification"],
            model_id=value["model_id"],
            predictions=tuple(
                CareerEventReplayPrediction.from_dict(item)
                for item in value["predictions"]
            ),
            freeze_hash=value["freeze_hash"],
        )


@dataclass(frozen=True, slots=True)
class HistoricalCareerEventLabel:
    """预测冻结后才能揭示的规范化历史事业事件。"""

    label_id: str
    case_id: str
    start_year: int
    end_year: int
    domain: str
    event_type: str
    direction: EventDirection
    magnitude: float
    source_ref: str
    confidence_grade: str
    dataset_classification: DatasetClassification

    def __post_init__(self) -> None:
        _require_text(self.label_id, "label_id")
        _require_text(self.case_id, "case_id")
        start = _require_year(self.start_year, "start_year")
        end = _require_year(self.end_year, "end_year")
        if start > end:
            raise ValueError("historical event window requires start_year <= end_year")
        _require_text(self.domain, "domain")
        if self.event_type not in _ALLOWED_EVENT_TYPES:
            raise ValueError("unsupported historical career event_type")
        if self.direction not in {"positive", "negative", "neutral"}:
            raise ValueError("invalid historical career event direction")
        _require_unit_interval(self.magnitude, "magnitude")
        _require_text(self.source_ref, "source_ref")
        _require_text(self.confidence_grade, "confidence_grade")
        if self.dataset_classification not in {
            "development_replay_only",
            "unseen_holdout",
        }:
            raise ValueError("invalid historical label dataset_classification")

    def to_dict(self) -> dict[str, Any]:
        return {
            "label_id": self.label_id,
            "case_id": self.case_id,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "domain": self.domain,
            "event_type": self.event_type,
            "direction": self.direction,
            "magnitude": self.magnitude,
            "source_ref": self.source_ref,
            "confidence_grade": self.confidence_grade,
            "dataset_classification": self.dataset_classification,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "HistoricalCareerEventLabel":
        required = {
            "label_id",
            "case_id",
            "start_year",
            "end_year",
            "domain",
            "event_type",
            "direction",
            "magnitude",
            "source_ref",
            "confidence_grade",
            "dataset_classification",
        }
        if set(value) != required:
            raise ValueError("historical career event label has invalid schema")
        return cls(**dict(value))


@dataclass(frozen=True, slots=True)
class HistoricalCareerNoEventLabel:
    """显式声明观察窗内没有事业角色变动，避免把缺标签误当负例。"""

    case_id: str
    source_ref: str
    confidence_grade: str
    dataset_classification: DatasetClassification

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        _require_text(self.source_ref, "source_ref")
        _require_text(self.confidence_grade, "confidence_grade")
        if self.dataset_classification not in {
            "development_replay_only",
            "unseen_holdout",
        }:
            raise ValueError("invalid no-event dataset_classification")

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "source_ref": self.source_ref,
            "confidence_grade": self.confidence_grade,
            "dataset_classification": self.dataset_classification,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "HistoricalCareerNoEventLabel":
        required = {
            "case_id",
            "source_ref",
            "confidence_grade",
            "dataset_classification",
        }
        if set(value) != required:
            raise ValueError("historical career no-event label has invalid schema")
        return cls(**dict(value))


@dataclass(frozen=True, slots=True)
class RevealedCareerEventLabels:
    schema_version: str
    freeze_hash: str
    labels: tuple[HistoricalCareerEventLabel, ...]
    no_event_cases: tuple[HistoricalCareerNoEventLabel, ...]

    def __post_init__(self) -> None:
        if self.schema_version != CAREER_EVENT_LABEL_SCHEMA:
            raise ValueError("unexpected career event label schema_version")
        if len(self.freeze_hash) != 64:
            raise ValueError("label freeze_hash must be a sha256 digest")
        labels = tuple(self.labels)
        no_event_cases = tuple(self.no_event_cases)
        identities = [item.label_id for item in labels]
        if len(set(identities)) != len(identities):
            raise ValueError("duplicate historical career label_id")
        negative_cases = [item.case_id for item in no_event_cases]
        if len(set(negative_cases)) != len(negative_cases):
            raise ValueError("duplicate historical career no-event case_id")
        positive_cases = {item.case_id for item in labels}
        if positive_cases.intersection(negative_cases):
            raise ValueError("case cannot have both event and no-event labels")
        object.__setattr__(self, "labels", labels)
        object.__setattr__(self, "no_event_cases", no_event_cases)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "freeze_hash": self.freeze_hash,
            "labels": [item.to_dict() for item in self.labels],
            "no_event_cases": [item.to_dict() for item in self.no_event_cases],
        }


@dataclass(frozen=True, slots=True)
class CareerEventDimensionScore:
    """单案例五维命中及覆盖/错误类型。"""

    case_id: str
    prediction_status: PredictionStatus
    matched_label_id: str | None
    timing_hit: bool
    event_type_hit: bool
    domain_hit: bool
    direction_hit: bool
    magnitude_hit: bool
    predicted: bool
    observed: bool
    false_positive: bool
    false_negative: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "prediction_status": self.prediction_status,
            "matched_label_id": self.matched_label_id,
            "timing_hit": self.timing_hit,
            "event_type_hit": self.event_type_hit,
            "domain_hit": self.domain_hit,
            "direction_hit": self.direction_hit,
            "magnitude_hit": self.magnitude_hit,
            "predicted": self.predicted,
            "observed": self.observed,
            "false_positive": self.false_positive,
            "false_negative": self.false_negative,
        }


@dataclass(frozen=True, slots=True)
class CareerEventReplayScore:
    schema_version: str
    dataset_id: str
    dataset_classification: DatasetClassification
    model_id: str
    freeze_hash: str
    case_scores: tuple[CareerEventDimensionScore, ...]
    metrics: Mapping[str, float | int | str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dataset_id": self.dataset_id,
            "dataset_classification": self.dataset_classification,
            "model_id": self.model_id,
            "freeze_hash": self.freeze_hash,
            "case_scores": [item.to_dict() for item in self.case_scores],
            "metrics": dict(self.metrics),
        }


def project_career_event_prediction(
    run: CareerRoleChangePredictionRun,
) -> CareerEventReplayPrediction:
    """移除结构细节，只保留盲评所需字段。"""

    if not isinstance(run, CareerRoleChangePredictionRun):
        raise TypeError("run must be CareerRoleChangePredictionRun")
    if run.window.mode != "historical":
        raise ValueError("career event replay accepts historical prediction windows only")
    if run.status != "predicted":
        return CareerEventReplayPrediction(
            case_id=run.case_id,
            model_id=run.model_id,
            status=run.status,
            observation_start_year=run.window.start_year,
            observation_end_year=run.window.end_year,
            predicted_start_year=None,
            predicted_end_year=None,
            domain=None,
            event_type=None,
            direction=None,
            magnitude=None,
        )
    if len(run.event_hypotheses) != 1 or len(run.timing_probabilities) != 1:
        raise ValueError("predicted career replay requires exactly one event and timing")
    event = run.event_hypotheses[0]
    timing = run.timing_probabilities[0].time_window
    prediction = CareerEventReplayPrediction(
        case_id=run.case_id,
        model_id=run.model_id,
        status=run.status,
        observation_start_year=run.window.start_year,
        observation_end_year=run.window.end_year,
        predicted_start_year=timing.get("start_year"),
        predicted_end_year=timing.get("end_year"),
        domain=event.domain,
        event_type=event.event_type,
        direction=run.direction,
        magnitude=run.magnitude,
    )
    _assert_no_forbidden_keys(prediction.to_dict())
    return prediction


def _legacy_career_task() -> BlindTask:
    return BlindTask(
        task_id="career.role_change",
        domain="事业",
        claim_type="event",
        scoring_method="binary_event",
        quantifiable=True,
        high_risk=False,
        allowed_time_horizons=["lifetime", "annual"],
        required_input_fields=["four_pillars"],
        label_schema={"type": "boolean"},
        evaluation_note="历史 Ren 岁运关系直接映射职业事件的开发回放适配器。",
    )


def project_legacy_ren_career_event_prediction(
    *,
    case_id: str,
    chart: ChartFactLedger,
    window: CareerPredictionWindow,
) -> CareerEventReplayPrediction:
    """把旧 ``Timing → Event`` Ren 路径投影到同一回放评分契约。"""

    if not isinstance(chart, ChartFactLedger):
        raise TypeError("chart must be ChartFactLedger")
    if not isinstance(window, CareerPredictionWindow):
        raise TypeError("window must be CareerPredictionWindow")
    if window.mode != "historical":
        raise ValueError("legacy career event replay accepts historical windows only")
    scoped_chart = ChartFactLedger(
        sex_marker=chart.sex_marker,
        solar_datetime=chart.solar_datetime,
        four_pillars=dict(chart.four_pillars),
        pillar_details=dict(chart.pillar_details),
        siling=chart.siling,
        void_by_pillar=dict(chart.void_by_pillar),
        start_luck=chart.start_luck,
        dayun_steps=[dict(item) for item in chart.dayun_steps],
        liunian_steps=[
            dict(step)
            for step in chart.liunian_steps
            if type(step.get("year", step.get("年份"))) is not int
            or window.start_year
            <= int(step.get("year", step.get("年份")))
            <= window.end_year
        ],
        missing_fields=list(chart.missing_fields),
        unknown_blocks=list(chart.unknown_blocks),
        raw_source_hash=chart.raw_source_hash,
    )
    claims = generate_legacy_ren_claims(
        scoped_chart,
        build_chart_feature_vector(scoped_chart),
        _legacy_career_task(),
    )
    annual_claims = [
        claim
        for claim in claims
        if claim.time_window is not None
        and claim.time_window.label == "annual"
        and window.start_year <= claim.time_window.start_year <= window.end_year
        and window.start_year <= claim.time_window.end_year <= window.end_year
    ]
    if not annual_claims:
        return CareerEventReplayPrediction(
            case_id=case_id,
            model_id=LEGACY_REN_CAREER_MODEL_ID,
            status="timing_abstain",
            observation_start_year=window.start_year,
            observation_end_year=window.end_year,
            predicted_start_year=None,
            predicted_end_year=None,
            domain=None,
            event_type=None,
            direction=None,
            magnitude=None,
        )
    if len(annual_claims) != 1:
        raise ValueError("legacy Ren replay requires at most one annual claim")
    claim = annual_claims[0]
    prediction = CareerEventReplayPrediction(
        case_id=case_id,
        model_id=LEGACY_REN_CAREER_MODEL_ID,
        status="predicted",
        observation_start_year=window.start_year,
        observation_end_year=window.end_year,
        predicted_start_year=claim.time_window.start_year,
        predicted_end_year=claim.time_window.end_year,
        domain=claim.domain,
        event_type="career.role_change",
        direction=claim.polarity,
        magnitude=claim.magnitude,
    )
    _assert_no_forbidden_keys(prediction.to_dict())
    return prediction


def freeze_career_event_replay_predictions(
    predictions: Sequence[CareerEventReplayPrediction],
    *,
    dataset_id: str,
    dataset_classification: DatasetClassification,
) -> FrozenCareerEventReplay:
    """冻结已投影预测，供 legacy/shared 模型使用同一评分契约。"""

    ordered = tuple(sorted(predictions, key=lambda item: item.case_id))
    if not ordered:
        raise ValueError("career event replay requires at least one prediction")
    model_ids = {item.model_id for item in ordered}
    if len(model_ids) != 1:
        raise ValueError("career event replay cannot mix model_id values")
    frozen = FrozenCareerEventReplay(
        schema_version=CAREER_EVENT_REPLAY_SCHEMA,
        dataset_id=dataset_id,
        dataset_classification=dataset_classification,
        model_id=ordered[0].model_id,
        predictions=ordered,
        freeze_hash="",
    )
    freeze_hash = _digest(frozen.payload())
    return FrozenCareerEventReplay.from_dict({**frozen.payload(), "freeze_hash": freeze_hash})


def freeze_career_event_predictions(
    runs: Sequence[CareerRoleChangePredictionRun],
    *,
    dataset_id: str,
    dataset_classification: DatasetClassification,
) -> FrozenCareerEventReplay:
    """冻结共享预测器输出；API 不接收任何标签或现实事实参数。"""

    return freeze_career_event_replay_predictions(
        tuple(project_career_event_prediction(run) for run in runs),
        dataset_id=dataset_id,
        dataset_classification=dataset_classification,
    )


def verify_frozen_career_event_replay(frozen: FrozenCareerEventReplay) -> None:
    if not isinstance(frozen, FrozenCareerEventReplay):
        raise TypeError("frozen must be FrozenCareerEventReplay")
    _assert_no_forbidden_keys(frozen.payload())
    if _digest(frozen.payload()) != frozen.freeze_hash:
        raise ValueError("career event replay freeze hash mismatch")


def reveal_career_event_labels(
    frozen: FrozenCareerEventReplay,
    labels_document: Mapping[str, Any],
) -> RevealedCareerEventLabels:
    """仅在冻结完整性通过后揭示并验证标签。"""

    verify_frozen_career_event_replay(frozen)
    required = {"schema_version", "freeze_hash", "labels", "no_event_cases"}
    if set(labels_document) != required:
        raise ValueError("career event labels document has invalid schema")
    if labels_document["schema_version"] != CAREER_EVENT_LABEL_SCHEMA:
        raise ValueError("unexpected career event labels schema_version")
    if labels_document["freeze_hash"] != frozen.freeze_hash:
        raise ValueError("career event labels freeze_hash mismatch")
    raw_labels = labels_document["labels"]
    raw_no_event = labels_document["no_event_cases"]
    if not isinstance(raw_labels, list) or not isinstance(raw_no_event, list):
        raise ValueError("career event labels and no_event_cases must be lists")
    labels = tuple(HistoricalCareerEventLabel.from_dict(item) for item in raw_labels)
    no_event_cases = tuple(
        HistoricalCareerNoEventLabel.from_dict(item) for item in raw_no_event
    )
    admitted_cases = {item.case_id for item in frozen.predictions}
    for label in (*labels, *no_event_cases):
        if label.case_id not in admitted_cases:
            raise ValueError("historical label case_id is absent from frozen predictions")
        if label.dataset_classification != frozen.dataset_classification:
            raise ValueError("historical label dataset classification mismatch")
    covered_cases = {item.case_id for item in labels}.union(
        item.case_id for item in no_event_cases
    )
    if covered_cases != admitted_cases:
        raise ValueError("every frozen case requires an explicit event or no-event label")
    return RevealedCareerEventLabels(
        schema_version=CAREER_EVENT_LABEL_SCHEMA,
        freeze_hash=frozen.freeze_hash,
        labels=labels,
        no_event_cases=no_event_cases,
    )


def _windows_overlap(
    left_start: int,
    left_end: int,
    right_start: int,
    right_end: int,
) -> bool:
    return max(left_start, right_start) <= min(left_end, right_end)


def _event_type_hit(predicted: str, observed: str) -> bool:
    if predicted == observed:
        return True
    return predicted == "career.role_change" and observed in _ROLE_CHANGE_CHILDREN


def _score_pair(
    prediction: CareerEventReplayPrediction,
    label: HistoricalCareerEventLabel,
    magnitude_tolerance: float,
) -> tuple[bool, bool, bool, bool, bool]:
    if prediction.status != "predicted":
        return False, False, False, False, False
    return (
        _windows_overlap(
            prediction.predicted_start_year,
            prediction.predicted_end_year,
            label.start_year,
            label.end_year,
        ),
        _event_type_hit(prediction.event_type, label.event_type),
        prediction.domain == label.domain,
        prediction.direction == label.direction,
        abs(prediction.magnitude - label.magnitude) <= magnitude_tolerance,
    )


def _best_label(
    prediction: CareerEventReplayPrediction,
    labels: Sequence[HistoricalCareerEventLabel],
    magnitude_tolerance: float,
) -> tuple[HistoricalCareerEventLabel, tuple[bool, bool, bool, bool, bool]] | None:
    if not labels:
        return None
    scored = [
        (label, _score_pair(prediction, label, magnitude_tolerance))
        for label in labels
    ]
    return max(
        scored,
        key=lambda item: (
            sum(item[1]),
            item[1][0],
            item[1][1],
            item[1][2],
            item[1][3],
            item[1][4],
            -item[0].start_year,
            item[0].label_id,
        ),
    )


def score_career_event_replay(
    frozen: FrozenCareerEventReplay,
    revealed: RevealedCareerEventLabels,
    *,
    magnitude_tolerance: float = 0.25,
) -> CareerEventReplayScore:
    """计算时间、事件类型、领域、方向、重大性与覆盖/错误率。"""

    verify_frozen_career_event_replay(frozen)
    if revealed.freeze_hash != frozen.freeze_hash:
        raise ValueError("revealed labels are not bound to the frozen replay")
    tolerance = _require_unit_interval(magnitude_tolerance, "magnitude_tolerance")
    labels_by_case: dict[str, list[HistoricalCareerEventLabel]] = {}
    for label in revealed.labels:
        labels_by_case.setdefault(label.case_id, []).append(label)
    no_event_cases = {item.case_id for item in revealed.no_event_cases}

    case_scores: list[CareerEventDimensionScore] = []
    for prediction in frozen.predictions:
        labels = labels_by_case.get(prediction.case_id, [])
        if prediction.case_id not in labels_by_case and prediction.case_id not in no_event_cases:
            raise ValueError("revealed labels do not cover every frozen prediction")
        predicted = prediction.status == "predicted"
        observed = bool(labels)
        best = _best_label(prediction, labels, tolerance)
        dimensions = best[1] if best is not None else (False, False, False, False, False)
        case_scores.append(
            CareerEventDimensionScore(
                case_id=prediction.case_id,
                prediction_status=prediction.status,
                matched_label_id=best[0].label_id if best is not None else None,
                timing_hit=dimensions[0],
                event_type_hit=dimensions[1],
                domain_hit=dimensions[2],
                direction_hit=dimensions[3],
                magnitude_hit=dimensions[4],
                predicted=predicted,
                observed=observed,
                false_positive=predicted and not observed,
                false_negative=observed and not predicted,
            )
        )

    total = len(case_scores)
    observed_count = sum(item.observed for item in case_scores)
    predicted_count = sum(item.predicted for item in case_scores)
    false_positive_count = sum(item.false_positive for item in case_scores)
    false_negative_count = sum(item.false_negative for item in case_scores)

    def rate(numerator: int, denominator: int) -> float:
        return round(numerator / denominator, 6) if denominator else 0.0

    metrics: dict[str, float | int | str] = {
        "case_count": total,
        "observed_case_count": observed_count,
        "predicted_case_count": predicted_count,
        "abstain_count": total - predicted_count,
        "coverage": rate(predicted_count, total),
        "timing_hit_rate": rate(sum(item.timing_hit for item in case_scores), observed_count),
        "event_type_hit_rate": rate(sum(item.event_type_hit for item in case_scores), observed_count),
        "domain_hit_rate": rate(sum(item.domain_hit for item in case_scores), observed_count),
        "direction_hit_rate": rate(sum(item.direction_hit for item in case_scores), observed_count),
        "magnitude_hit_rate": rate(sum(item.magnitude_hit for item in case_scores), observed_count),
        "false_positive_count": false_positive_count,
        "false_positive_rate": rate(false_positive_count, total - observed_count),
        "false_negative_count": false_negative_count,
        "false_negative_rate": rate(false_negative_count, observed_count),
        "promotion_eligible": "false" if frozen.dataset_classification == "development_replay_only" else "unadjudicated",
    }
    return CareerEventReplayScore(
        schema_version=CAREER_EVENT_SCORE_SCHEMA,
        dataset_id=frozen.dataset_id,
        dataset_classification=frozen.dataset_classification,
        model_id=frozen.model_id,
        freeze_hash=frozen.freeze_hash,
        case_scores=tuple(case_scores),
        metrics=metrics,
    )
