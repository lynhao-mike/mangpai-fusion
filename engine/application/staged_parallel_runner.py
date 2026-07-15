"""显式并跑 legacy 与 Claim 冻结链；两分支失败互不影响。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from engine.application.pipeline_runner import run_pipeline
from engine.claims.orchestrator import generate_frozen_claim_run
from engine.claims.domain import Claim
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY, RunnerRegistry
from engine.decision.l6_staged_arbitration import (
    ConflictRuleSet,
    StagedArbitrationResult,
    arbitrate_staged,
)
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask, FrozenBlindRun
from engine.features import build_chart_feature_vector
from engine.predicates.types import Bazi, Dayun, DayunStep, GanZhi, ParsedInput, _default_canggan_for

_TASK_CATALOG_VERSION = "school-capability-tasks/v1-task10-staged"
_RULE_SNAPSHOT_ID = "task10-structured-parallel-v1"
_DEFAULT_CONFLICT_RULES = Path(__file__).parents[1] / "decision" / "conflict-rules.yaml"


@dataclass(frozen=True)
class ParallelRun:
    """同一命盘上两条相互隔离路径的不可变结果。"""

    case_id: str
    legacy_snapshot: Any | None
    claim_snapshot: FrozenBlindRun | None
    legacy_error: str | None = None
    claim_error: str | None = None
    task_metadata: tuple[tuple[str, str, bool], ...] = ()
    evidence_completeness: str | None = None


def _error_text(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def _pillar(chart: ChartFactLedger, name: str) -> GanZhi:
    aliases = {
        "year": ("year", "年柱"),
        "month": ("month", "月柱"),
        "day": ("day", "日柱"),
        "hour": ("hour", "时柱"),
    }
    value = next((chart.four_pillars[key] for key in aliases[name] if key in chart.four_pillars), "")
    return GanZhi.parse(str(value))


def _year(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def chart_to_parsed_input(chart: ChartFactLedger, *, case_id: str) -> ParsedInput:
    """仅从 ChartFactLedger 构造 legacy ParsedInput，不注入上下文事实。"""
    bazi = Bazi(
        年柱=_pillar(chart, "year"),
        月柱=_pillar(chart, "month"),
        日柱=_pillar(chart, "day"),
        时柱=_pillar(chart, "hour"),
    )
    bazi.藏干 = _default_canggan_for(bazi)

    steps: list[DayunStep] = []
    for index, raw in enumerate(chart.dayun_steps, start=1):
        ganzhi = raw.get("ganzhi") or raw.get("干支")
        if not ganzhi:
            continue
        start_year = _year(raw.get("start_year") or raw.get("起年"))
        end_year = _year(raw.get("end_year") or raw.get("止年"), start_year + 9)
        start_age = _year(raw.get("start_age") or raw.get("起岁"), (index - 1) * 10)
        end_age = _year(raw.get("end_age") or raw.get("止岁"), start_age + 9)
        steps.append(DayunStep(index, GanZhi.parse(str(ganzhi)), start_age, end_age, (start_year, end_year + 1)))

    birth_year = _year(chart.solar_datetime[:4]) if chart.solar_datetime else 0
    start_luck_year = _year(chart.start_luck, birth_year)
    dayun = Dayun(
        起运岁=float(max(0, start_luck_year - birth_year)) if birth_year else 0.0,
        起运年=start_luck_year,
        顺逆="顺",
        排布=steps,
    )
    return ParsedInput(
        case_id=case_id,
        bazi=bazi,
        dayun=dayun,
        birth={"性别": chart.sex_marker, "公历": chart.solar_datetime},
        case_meta={"case_id": case_id, "来源": "问真八字"},
    )


def _capturing_registry(
    registry: RunnerRegistry,
    tasks: Sequence[BlindTask],
    schools: Sequence[str],
    captured: list[Claim],
) -> RunnerRegistry:
    """装饰现有 runner 以保留本次生成的原始 Claim，不改变各派执行逻辑。"""
    registrations = []
    for school_id in sorted(set(schools)):
        for task in sorted(tasks, key=lambda item: item.task_id):
            generator = registry.resolve(school_id, task.task_id)
            if generator is None:
                continue

            def capture(chart, features, blind_task, *, _generator=generator):
                claims = _generator(chart, features, blind_task)
                captured.extend(claims)
                return claims

            registrations.append((school_id, task.task_id, capture))
    return RunnerRegistry(registrations)


def run_parallel(
    chart: ChartFactLedger,
    tasks: Sequence[BlindTask],
    *,
    case_id: str,
    schools: Sequence[str],
    registry: RunnerRegistry = DEFAULT_RUNNER_REGISTRY,
) -> ParallelRun:
    """显式运行两条路径；不落盘，且每条路径拥有独立异常边界。"""
    task_metadata = tuple(sorted((task.task_id, task.domain, task.high_risk) for task in tasks))
    try:
        completeness = build_chart_feature_vector(chart).evidence_completeness
    except (TypeError, ValueError):
        completeness = "partial"

    legacy_snapshot: Any | None = None
    legacy_error: str | None = None
    try:
        parsed = chart_to_parsed_input(chart, case_id=case_id)
        legacy_snapshot = run_pipeline(parsed, write_findings=False)
    except Exception as exc:  # noqa: BLE001 - branch isolation boundary
        legacy_error = _error_text(exc)

    claim_snapshot: FrozenBlindRun | None = None
    claim_error: str | None = None
    captured_claims: list[Claim] = []
    try:
        claim_snapshot = generate_frozen_claim_run(
            chart,
            tasks,
            case_id=case_id,
            task_catalog_version=_TASK_CATALOG_VERSION,
            rule_snapshot_id=_RULE_SNAPSHOT_ID,
            schools=schools,
            registry=_capturing_registry(registry, tasks, schools, captured_claims),
        )
        object.__setattr__(claim_snapshot, "staged_claims", tuple(captured_claims))
    except Exception as exc:  # noqa: BLE001 - branch isolation boundary
        claim_error = _error_text(exc)

    return ParallelRun(
        case_id=case_id,
        legacy_snapshot=legacy_snapshot,
        claim_snapshot=claim_snapshot,
        legacy_error=legacy_error,
        claim_error=claim_error,
        task_metadata=task_metadata,
        evidence_completeness=completeness,
    )


def _claims_from_snapshot(snapshot: FrozenBlindRun | None) -> tuple[Claim, ...]:
    """读取冻结 run 上随运行产生的 Claim 旁车；不从展示字段反推命题。"""
    if snapshot is None:
        return ()
    claims = getattr(snapshot, "staged_claims", ())
    if not isinstance(claims, tuple | list) or not all(isinstance(item, Claim) for item in claims):
        return ()
    return tuple(claims)


def run_parallel_with_arbitration(
    parallel_run: ParallelRun,
    route_plan: Mapping[str, str] | None = None,
    *,
    conflict_rules: ConflictRuleSet | None = None,
) -> StagedArbitrationResult:
    """把显式并跑产物送入 staged L6；缺少 Claim 时返回三段空裁决。"""
    claims = _claims_from_snapshot(parallel_run.claim_snapshot)
    rules = conflict_rules or ConflictRuleSet.from_yaml(_DEFAULT_CONFLICT_RULES)
    return arbitrate_staged(
        parallel_run.case_id,
        claims,
        route_plan,
        conflict_rules=rules,
    )
