"""事业角色变动的共享命局结构→事件→应期预测链。

该模块只消费 ``ChartFactLedger`` 与显式观察窗口，不读取 known facts、
feedback、verification 或 calibration 数据。历史回放与未来预测使用同一入口；
两者只通过 ``CareerPredictionWindow.mode`` 和流年窗口区分，不改变规则。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Any, Literal

from engine.claims.domain import Claim
from engine.decision.models import (
    ChartFactLedger,
    EventHypothesis,
    StructuralVerdict,
    TimingProbability,
)
from engine.decision.ren_career_timing import RenTimingResult
from engine.decision.ren_career_timing_slice import build_ren_career_timing_slice
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector, build_chart_feature_vector
from engine.v5.duan_runner import generate_claims as generate_duan_claims

CAREER_ROLE_CHANGE_MODEL_ID = "career-role-change-shared-predictor-v1"
CAREER_ROLE_CHANGE_TASK_ID = "career.role_change"

PredictionMode = Literal["historical", "future"]
PredictionStatus = Literal["structure_abstain", "timing_abstain", "predicted"]


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


@dataclass(frozen=True, slots=True)
class CareerPredictionWindow:
    """同一预测器的历史或未来流年观察窗。"""

    start_year: int
    end_year: int
    mode: PredictionMode

    def __post_init__(self) -> None:
        if type(self.start_year) is not int or type(self.end_year) is not int:
            raise TypeError("career prediction window years must be integers")
        if self.start_year > self.end_year:
            raise ValueError("career prediction window requires start_year <= end_year")
        if self.mode not in {"historical", "future"}:
            raise ValueError("career prediction window mode must be historical or future")

    def to_dict(self) -> dict[str, int | str]:
        return {
            "start_year": self.start_year,
            "end_year": self.end_year,
            "mode": self.mode,
        }


@dataclass(frozen=True, slots=True)
class CareerRoleChangePredictionRun:
    """一次可审计的共享事业事件预测结果。"""

    schema_version: str
    model_id: str
    case_id: str
    window: CareerPredictionWindow
    status: PredictionStatus
    features: ChartFeatureVector
    structure_claims: tuple[Claim, ...]
    structural_verdicts: tuple[StructuralVerdict, ...]
    event_hypotheses: tuple[EventHypothesis, ...]
    timing_result: RenTimingResult
    timing_probabilities: tuple[TimingProbability, ...]
    direction: str
    magnitude: float | None

    def __post_init__(self) -> None:
        if not self.schema_version.strip():
            raise ValueError("schema_version is required")
        if self.model_id != CAREER_ROLE_CHANGE_MODEL_ID:
            raise ValueError("unexpected career role change model_id")
        if not self.case_id.strip():
            raise ValueError("case_id is required")
        if self.status not in {"structure_abstain", "timing_abstain", "predicted"}:
            raise ValueError("invalid career role change prediction status")
        if len(self.structure_claims) > 1:
            raise ValueError("career role change predictor allows at most one structure claim")
        if len(self.structural_verdicts) > 1 or len(self.event_hypotheses) > 1:
            raise ValueError("career role change predictor allows at most one qualified event")
        if self.status == "structure_abstain" and (
            self.structure_claims
            or self.structural_verdicts
            or self.event_hypotheses
            or self.timing_probabilities
        ):
            raise ValueError("structure abstain cannot contain qualified event outputs")
        if self.status == "predicted" and (
            not self.structure_claims
            or not self.structural_verdicts
            or not self.event_hypotheses
            or not self.timing_probabilities
        ):
            raise ValueError("predicted status requires the complete structure-event-timing chain")
        if self.status != "predicted" and self.timing_probabilities:
            raise ValueError("only predicted status may contain timing probabilities")
        object.__setattr__(self, "structure_claims", tuple(self.structure_claims))
        object.__setattr__(self, "structural_verdicts", tuple(self.structural_verdicts))
        object.__setattr__(self, "event_hypotheses", tuple(self.event_hypotheses))
        object.__setattr__(self, "timing_probabilities", tuple(self.timing_probabilities))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "model_id": self.model_id,
            "case_id": self.case_id,
            "window": self.window.to_dict(),
            "status": self.status,
            "features": self.features.to_dict(),
            "structure_claims": [claim.to_dict() for claim in self.structure_claims],
            "structural_verdicts": [verdict.to_dict() for verdict in self.structural_verdicts],
            "event_hypotheses": [event.to_dict() for event in self.event_hypotheses],
            "timing_result": self.timing_result.to_dict(),
            "timing_probabilities": [item.to_dict() for item in self.timing_probabilities],
            "direction": self.direction,
            "magnitude": self.magnitude,
        }


def _career_role_change_task() -> BlindTask:
    return BlindTask(
        task_id=CAREER_ROLE_CHANGE_TASK_ID,
        domain="事业",
        claim_type="event",
        scoring_method="binary_event",
        quantifiable=True,
        high_risk=False,
        allowed_time_horizons=["lifetime", "annual"],
        required_input_fields=["four_pillars"],
        label_schema={
            "type": "boolean",
            "positive_label": "occurred",
            "negative_label": "not_observed",
        },
        evaluation_note=(
            "共享事业角色变动预测器：段派结构资格先行，任派真实年度触发后置。"
        ),
    )


def _windowed_chart(
    chart: ChartFactLedger,
    window: CareerPredictionWindow,
) -> ChartFactLedger:
    """只裁剪流年观察窗；无年份流年保留并由 timing gate 失败关闭。"""

    liunian_steps = [
        dict(step)
        for step in chart.liunian_steps
        if type(step.get("year", step.get("年份"))) is not int
        or window.start_year <= int(step.get("year", step.get("年份"))) <= window.end_year
    ]
    return replace(chart, liunian_steps=liunian_steps)


def _qualify_event(
    *,
    features: ChartFeatureVector,
    claim: Claim,
) -> tuple[StructuralVerdict, EventHypothesis]:
    verdict_id = _stable_id(
        "career-structure-verdict",
        CAREER_ROLE_CHANGE_MODEL_ID,
        features.chart_id,
        claim.claim_id,
    )
    verdict = StructuralVerdict(
        verdict_id=verdict_id,
        claim_id=claim.claim_id,
        verdict="pass",
        structural_reason=claim.confidence_basis,
        required_support=[evidence.evidence_id for evidence in claim.evidence],
        confidence=claim.confidence,
    )
    event = EventHypothesis(
        event_id=_stable_id(
            "career-event",
            CAREER_ROLE_CHANGE_MODEL_ID,
            features.chart_id,
            verdict_id,
        ),
        source_verdict_ids=[verdict_id],
        domain=claim.domain,
        event_type=CAREER_ROLE_CHANGE_TASK_ID,
        subject="命主",
        concrete_event=claim.statement,
        landing_path="岗位、职责或职业角色发生可核验变化",
        confidence=claim.confidence,
    )
    return verdict, event


def predict_career_role_change(
    *,
    case_id: str,
    chart: ChartFactLedger,
    window: CareerPredictionWindow,
) -> CareerRoleChangePredictionRun:
    """从命局结构生成事业事件资格，再以同一观察窗寻找真实年度应期。

    API 故意不接收现实标签、反馈、核验结果或校准参数。历史回放与未来预测
    均调用本函数，因此不会出现一套规则解释历史、另一套规则预测未来。
    """

    if not isinstance(chart, ChartFactLedger):
        raise TypeError("chart must be ChartFactLedger")
    if not isinstance(window, CareerPredictionWindow):
        raise TypeError("window must be CareerPredictionWindow")
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("case_id is required")

    scoped_chart = _windowed_chart(chart, window)
    features = build_chart_feature_vector(scoped_chart)
    task = _career_role_change_task()
    claims = tuple(generate_duan_claims(scoped_chart, features, task))
    if len(claims) > 1:
        raise ValueError("Duan career role change gate returned more than one claim")

    if not claims:
        timing_result, timings = build_ren_career_timing_slice(
            case_id,
            scoped_chart,
            features,
            None,
            task_id=CAREER_ROLE_CHANGE_TASK_ID,
        )
        return CareerRoleChangePredictionRun(
            schema_version="career-role-change-prediction-run/v1",
            model_id=CAREER_ROLE_CHANGE_MODEL_ID,
            case_id=case_id,
            window=window,
            status="structure_abstain",
            features=features,
            structure_claims=(),
            structural_verdicts=(),
            event_hypotheses=(),
            timing_result=timing_result,
            timing_probabilities=timings,
            direction="neutral",
            magnitude=None,
        )

    claim = claims[0]
    verdict, event = _qualify_event(features=features, claim=claim)
    timing_result, timings = build_ren_career_timing_slice(
        case_id,
        scoped_chart,
        features,
        event,
        task_id=CAREER_ROLE_CHANGE_TASK_ID,
    )
    return CareerRoleChangePredictionRun(
        schema_version="career-role-change-prediction-run/v1",
        model_id=CAREER_ROLE_CHANGE_MODEL_ID,
        case_id=case_id,
        window=window,
        status="predicted" if timings else "timing_abstain",
        features=features,
        structure_claims=(claim,),
        structural_verdicts=(verdict,),
        event_hypotheses=(event,),
        timing_result=timing_result,
        timing_probabilities=timings,
        direction=claim.polarity,
        magnitude=claim.magnitude,
    )
