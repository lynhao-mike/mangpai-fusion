"""L2 任务型命题默认编排：Chart → cfv-v1 → school Claim → BlindSchoolOutput。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from engine.claims.blind_adapter import claim_to_blind_output
from engine.claims.domain import TaskUnsupported
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY, RunnerRegistry
from engine.decision.models import ChartFactLedger
from engine.evaluation.freeze import freeze_outputs
from engine.evaluation.models import BlindSchoolOutput, BlindTask, FrozenBlindRun
from engine.features import build_chart_feature_vector


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


def _missing_required_fields(chart: ChartFactLedger, task: BlindTask) -> tuple[str, ...]:
    missing: list[str] = []
    for field in task.required_input_fields:
        if field == "four_pillars":
            values = tuple(chart.four_pillars.values())
            present = bool(values) and all(str(value).strip() not in {"", "_"} for value in values)
        else:
            value = getattr(chart, field, None)
            present = bool(str(value).strip()) if isinstance(value, str) else value is not None
        if not present:
            missing.append(field)
    return tuple(missing)


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
    registry: RunnerRegistry = DEFAULT_RUNNER_REGISTRY,
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
        for task in sorted(tasks, key=lambda item: item.task_id):
            generator = registry.resolve(school, task.task_id)
            if generator is None:
                rows.append(_state_output(
                    case_id=case_id, school=school, task=task, state="unsupported",
                    rationale="no independent L2 claim generator is registered for this school",
                ))
                continue
            missing_required = _missing_required_fields(ledger, task)
            if missing_required:
                rows.append(_state_output(
                    case_id=case_id, school=school, task=task, state="abstain",
                    rationale=f"missing required chart facts: {', '.join(missing_required)}",
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
    registry: RunnerRegistry = DEFAULT_RUNNER_REGISTRY,
    frozen_at: str | None = None,
) -> FrozenBlindRun:
    """从命盘事实直接生成并冻结盲测输出，形成 03 可消费的标准制品。"""
    outputs = generate_blind_outputs(
        chart,
        tasks,
        case_id=case_id,
        schools=schools,
        registry=registry,
    )
    return freeze_outputs(
        outputs,
        task_catalog_version,
        rule_snapshot_id,
        frozen_at=frozen_at,
    )
