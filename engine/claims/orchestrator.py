"""L2 任务型命题默认编排：Chart → cfv-v1 → school Claim → BlindSchoolOutput。"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from engine.claims.blind_adapter import claim_to_blind_output
from engine.claims.domain import Claim, TaskUnsupported
from engine.decision.models import ChartFactLedger
from engine.evaluation.freeze import freeze_outputs
from engine.evaluation.models import BlindSchoolOutput, BlindTask, FrozenBlindRun
from engine.features import ChartFeatureVector, build_chart_feature_vector
from engine.v5.ren_runner import generate_claims as generate_ren_claims
from engine.v5.ziping_runner import generate_claims as generate_ziping_claims

ClaimGenerator = Callable[[ChartFactLedger, ChartFeatureVector, BlindTask], list[Claim]]
_ENGINE_RUNNERS: dict[str, ClaimGenerator] = {
    "ziping": generate_ziping_claims,
    "ren": generate_ren_claims,
}


def chart_ledger_from_mapping(chart: dict[str, Any]) -> ChartFactLedger:
    """把 v5 chart DTO 确定性规范为 L0 事实账本。"""
    pillars_raw = chart.get("pillars") or chart.get("four_pillars") or {}
    if isinstance(pillars_raw, (list, tuple)):
        pillars = {key: str(value) for key, value in zip(("year", "month", "day", "hour"), pillars_raw)}
    elif isinstance(pillars_raw, dict):
        pillars = {str(key): str(value) for key, value in pillars_raw.items()}
    else:
        pillars = {}
    dayun_raw = chart.get("dayun_steps") or []
    liunian_raw = chart.get("liunian_steps") or []
    return ChartFactLedger(
        sex_marker=str(chart.get("gender_marker") or chart.get("sex_marker") or chart.get("sex") or ""),
        solar_datetime=str(chart.get("solar_datetime") or ""),
        four_pillars=pillars,
        start_luck=str(chart.get("start_luck") or ""),
        dayun_steps=[dict(item) for item in dayun_raw if isinstance(item, dict)] if isinstance(dayun_raw, (list, tuple)) else [],
        liunian_steps=[dict(item) for item in liunian_raw if isinstance(item, dict)] if isinstance(liunian_raw, (list, tuple)) else [],
        missing_fields=[str(item) for item in chart.get("missing_fields", [])] if isinstance(chart.get("missing_fields", []), (list, tuple)) else [],
    )


def _state_output(
    *,
    case_id: str,
    school: str,
    task: BlindTask,
    state: str,
    rationale: str,
) -> BlindSchoolOutput:
    return BlindSchoolOutput(
        case_id=case_id,
        school_id=school,
        task_id=task.task_id,
        state=state,  # type: ignore[arg-type]
        rationale=rationale,
    )


def generate_blind_outputs(
    chart: ChartFactLedger | dict[str, Any],
    tasks: Sequence[BlindTask],
    *,
    case_id: str,
    schools: Sequence[str] = ("ziping", "ren"),
) -> list[BlindSchoolOutput]:
    """运行任务型 L2 引擎；不消费反馈、报告或人工 school-claims JSON。"""
    ledger = chart if isinstance(chart, ChartFactLedger) else chart_ledger_from_mapping(chart)
    try:
        features = build_chart_feature_vector(ledger)
    except (TypeError, ValueError) as exc:
        features = None
        feature_error = str(exc)
    else:
        feature_error = ""

    rows: list[BlindSchoolOutput] = []
    for school in sorted(set(schools)):
        generator = _ENGINE_RUNNERS.get(school)
        for task in sorted(tasks, key=lambda item: item.task_id):
            if generator is None:
                rows.append(_state_output(
                    case_id=case_id, school=school, task=task, state="unsupported",
                    rationale="no independent L2 claim generator is registered for this school",
                ))
                continue
            if features is None:
                rows.append(_state_output(
                    case_id=case_id, school=school, task=task, state="abstain",
                    rationale=f"chart facts are insufficient to build cfv-v1: {feature_error}",
                ))
                continue
            try:
                claims = generator(ledger, features, task)
            except TaskUnsupported as exc:
                rows.append(_state_output(
                    case_id=case_id, school=school, task=task, state="unsupported", rationale=str(exc),
                ))
                continue
            if not claims:
                rows.append(_state_output(
                    case_id=case_id, school=school, task=task, state="abstain",
                    rationale="runner covers this task but chart facts do not satisfy a production trigger",
                ))
                continue
            selected = min(claims, key=lambda claim: claim.claim_id)
            rows.append(claim_to_blind_output(selected, case_id=case_id, task=task))
    return rows


def generate_frozen_claim_run(
    chart: ChartFactLedger | dict[str, Any],
    tasks: Sequence[BlindTask],
    *,
    case_id: str,
    task_catalog_version: str,
    rule_snapshot_id: str,
    schools: Sequence[str] = ("ziping", "ren"),
    frozen_at: str | None = None,
) -> FrozenBlindRun:
    """从命盘事实直接生成并冻结盲测输出，形成 03 可消费的标准制品。"""
    outputs = generate_blind_outputs(chart, tasks, case_id=case_id, schools=schools)
    return freeze_outputs(
        outputs,
        task_catalog_version,
        rule_snapshot_id,
        frozen_at=frozen_at,
    )
