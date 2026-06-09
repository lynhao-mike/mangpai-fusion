"""多流派并行功能域 canonical runner。

所有并行功能域输出必须经由本 runner：
- 以 DomainAnalyzerRegistry 作为唯一专家接线机制；
- 对 parsed / base_context / 每个 analyzer context 做 deep copy；
- 默认顺序执行，可选 bounded thread executor；
- 每个 analyzer 独立 exception / timeout envelope，并 fallback abstain；
- 在 reading.notes 中记录 execution audit，保持领域模型向后兼容。
"""

from __future__ import annotations

import copy
import time
from concurrent.futures import TimeoutError
from dataclasses import dataclass
from typing import Any, Callable, Literal, Sequence, overload

from engine.application.adjudication import adjudicate_domain, build_domain_consensus
from engine.application.conflict_detection import conflict_penalties_from_conflicts, detect_cross_expert_conflicts
from engine.application.cross_domain_consistency import evaluate_cross_domain_consistency
from engine.application.domain_analyzers import (
    DEFAULT_DOMAINS,
    DEFAULT_EXPERT_ORDER,
    EXPERT_LABELS,
    AbstainDomainAnalyzer,
    DomainAnalysisContext,
    DomainAnalyzer,
    DomainAnalyzerRegistry,
    build_empty_parallel_registry,
)
from engine.application.parallel_audit import AnalyzerExecutionAudit
from engine.application.parallel_execution import ParallelExecutionConfig, execute_callables
from engine.domain.parallel import DomainAnalysis, DomainName, EvidenceItem, ExpertReading, ExpertSystem, ParallelAnalysisOutput


@dataclass(frozen=True)
class AnalyzerExecutionResult:
    """单个 analyzer 的 reading + 审计 envelope。"""

    reading: ExpertReading
    audit: AnalyzerExecutionAudit


@dataclass(frozen=True)
class ParallelDomainRunResult:
    """runner 领域输出与执行审计。"""

    output: ParallelAnalysisOutput
    execution_audit: list[AnalyzerExecutionAudit]

    def audit_dicts(self) -> list[dict[str, Any]]:
        return [audit.to_dict() for audit in self.execution_audit]


@overload
def run_parallel_domain_analysis(
    parsed: Any,
    *,
    case_id: str | None = None,
    domains: Sequence[DomainName] | None = None,
    expert_order: Sequence[ExpertSystem] = DEFAULT_EXPERT_ORDER,
    registry: DomainAnalyzerRegistry | None = None,
    base_context: dict[str, Any] | None = None,
    execution_config: ParallelExecutionConfig | None = None,
    timeout_seconds: float | None = None,
    include_audit: Literal[False] = False,
) -> ParallelAnalysisOutput: ...


@overload
def run_parallel_domain_analysis(
    parsed: Any,
    *,
    case_id: str | None = None,
    domains: Sequence[DomainName] | None = None,
    expert_order: Sequence[ExpertSystem] = DEFAULT_EXPERT_ORDER,
    registry: DomainAnalyzerRegistry | None = None,
    base_context: dict[str, Any] | None = None,
    execution_config: ParallelExecutionConfig | None = None,
    timeout_seconds: float | None = None,
    include_audit: Literal[True],
) -> ParallelDomainRunResult: ...


def run_parallel_domain_analysis(
    parsed: Any,
    *,
    case_id: str | None = None,
    domains: Sequence[DomainName] | None = None,
    expert_order: Sequence[ExpertSystem] = DEFAULT_EXPERT_ORDER,
    registry: DomainAnalyzerRegistry | None = None,
    base_context: dict[str, Any] | None = None,
    execution_config: ParallelExecutionConfig | None = None,
    timeout_seconds: float | None = None,
    include_audit: bool = False,
) -> ParallelAnalysisOutput | ParallelDomainRunResult:
    """运行多专家功能域分析。

    默认返回 ParallelAnalysisOutput 以保持既有调用兼容；当 include_audit=True 时，
    返回 ParallelDomainRunResult，额外携带 expert × domain 执行审计。
    """

    parsed_snapshot = copy.deepcopy(parsed)
    base_context_snapshot = copy.deepcopy(base_context or {})
    resolved_case_id = case_id or _case_id_from_parsed(parsed_snapshot)
    selected_domains = list(domains or DEFAULT_DOMAINS)
    active_registry = registry or build_empty_parallel_registry()
    active_execution_config = execution_config or ParallelExecutionConfig(timeout_seconds=timeout_seconds)

    analyses: list[DomainAnalysis] = []
    execution_audit: list[AnalyzerExecutionAudit] = []
    for domain in selected_domains:
        tasks = [
            _build_analyzer_task(
                parsed=parsed_snapshot,
                domain=domain,
                case_id=resolved_case_id,
                expert_system=expert_system,
                analyzer=active_registry.get(domain, expert_system),
                base_context=base_context_snapshot,
                timeout_seconds=active_execution_config.timeout_seconds,
            )
            for expert_system in expert_order
        ]
        raw_results = execute_callables(tasks, config=active_execution_config)
        analyzer_results = [
            _coerce_execution_result(
                raw_result=raw_result,
                parsed=parsed_snapshot,
                domain=domain,
                case_id=resolved_case_id,
                expert_system=expert_system,
                base_context=base_context_snapshot,
            )
            for raw_result, expert_system in zip(raw_results, expert_order)
        ]
        readings = [result.reading for result in analyzer_results]
        execution_audit.extend(result.audit for result in analyzer_results)
        initial_conflicts = detect_cross_expert_conflicts(
            case_id=resolved_case_id,
            domain=domain,
            readings=readings,
        )
        conflict_penalties = conflict_penalties_from_conflicts(initial_conflicts)
        adjudication = adjudicate_domain(
            case_id=resolved_case_id,
            domain=domain,
            readings=readings,
            conflict_penalties=conflict_penalties,
        )
        conflicts = detect_cross_expert_conflicts(
            case_id=resolved_case_id,
            domain=domain,
            readings=readings,
            adjudication_result=adjudication,
        )
        consensus = build_domain_consensus(
            case_id=resolved_case_id,
            domain=domain,
            readings=readings,
            adjudication=adjudication,
        )
        analyses.append(
            DomainAnalysis(
                domain=domain,
                readings=readings,
                adjudication_result=adjudication,
                consensus=consensus,
                conflicts=conflicts,
            )
        )

    consistency_notes = evaluate_cross_domain_consistency(analyses, case_id=resolved_case_id)
    output = ParallelAnalysisOutput(
        case_id=resolved_case_id,
        domain_analyses=analyses,
        consistency_notes=[note.to_dict() for note in consistency_notes],
    )
    if include_audit:
        return ParallelDomainRunResult(output=output, execution_audit=execution_audit)
    return output


def _build_analyzer_task(
    *,
    parsed: Any,
    domain: DomainName,
    case_id: str,
    expert_system: ExpertSystem,
    analyzer: DomainAnalyzer,
    base_context: dict[str, Any],
    timeout_seconds: float | None,
) -> Callable[[], AnalyzerExecutionResult]:
    def task() -> AnalyzerExecutionResult:
        return _run_one_analyzer(
            parsed=parsed,
            domain=domain,
            case_id=case_id,
            expert_system=expert_system,
            analyzer=analyzer,
            base_context=base_context,
            timeout_seconds=timeout_seconds,
        )

    return task


def _run_one_analyzer(
    *,
    parsed: Any,
    domain: DomainName,
    case_id: str,
    expert_system: ExpertSystem,
    analyzer: DomainAnalyzer,
    base_context: dict[str, Any],
    timeout_seconds: float | None,
) -> AnalyzerExecutionResult:
    start = time.perf_counter()
    context = DomainAnalysisContext(
        case_id=case_id,
        base_context=copy.deepcopy(base_context),
    )
    parsed_for_analyzer = copy.deepcopy(parsed)
    try:
        reading = analyzer.analyze(parsed_for_analyzer, domain, context)
        duration_ms = (time.perf_counter() - start) * 1000
        if timeout_seconds is not None and duration_ms > timeout_seconds * 1000:
            return _timeout_result(
                parsed=parsed,
                domain=domain,
                case_id=case_id,
                expert_system=expert_system,
                base_context=base_context,
                duration_ms=duration_ms,
            )
        status = "abstain" if reading.stance == "abstain" else "success"
        audit = AnalyzerExecutionAudit(
            case_id=case_id,
            domain=domain,
            expert_system=expert_system,
            status=status,
            duration_ms=duration_ms,
            source_engine=reading.source_engine,
            message=reading.claim if status == "abstain" else "",
        )
        return AnalyzerExecutionResult(reading=_attach_audit(reading, audit), audit=audit)
    except Exception as exc:  # noqa: BLE001
        duration_ms = (time.perf_counter() - start) * 1000
        return _exception_result(
            parsed=parsed,
            domain=domain,
            case_id=case_id,
            expert_system=expert_system,
            base_context=base_context,
            duration_ms=duration_ms,
            exc=exc,
        )


def _coerce_execution_result(
    *,
    raw_result: AnalyzerExecutionResult | BaseException,
    parsed: Any,
    domain: DomainName,
    case_id: str,
    expert_system: ExpertSystem,
    base_context: dict[str, Any],
) -> AnalyzerExecutionResult:
    if isinstance(raw_result, AnalyzerExecutionResult):
        return raw_result
    if isinstance(raw_result, TimeoutError):
        return _timeout_result(
            parsed=parsed,
            domain=domain,
            case_id=case_id,
            expert_system=expert_system,
            base_context=base_context,
            duration_ms=0.0,
        )
    return _exception_result(
        parsed=parsed,
        domain=domain,
        case_id=case_id,
        expert_system=expert_system,
        base_context=base_context,
        duration_ms=0.0,
        exc=raw_result,
    )


def _exception_result(
    *,
    parsed: Any,
    domain: DomainName,
    case_id: str,
    expert_system: ExpertSystem,
    base_context: dict[str, Any],
    duration_ms: float,
    exc: BaseException,
) -> AnalyzerExecutionResult:
    exception_class = type(exc).__name__
    message = f"分析器异常，按隔离原则弃权：{exception_class}: {exc}"
    reading = _attach_diagnostic_evidence(
        _fallback_abstain(
            parsed=parsed,
            domain=domain,
            case_id=case_id,
            expert_system=expert_system,
            base_context=base_context,
            reason=message,
            source_engine="parallel_domain_runner.exception_envelope",
        ),
        error_type=exception_class,
        message=str(exc),
        duration_ms=duration_ms,
        source_engine="parallel_domain_runner.exception_envelope",
    )
    audit = AnalyzerExecutionAudit(
        case_id=case_id,
        domain=domain,
        expert_system=expert_system,
        status="exception",
        duration_ms=duration_ms,
        source_engine=reading.source_engine,
        error_type=exception_class,
        message=str(exc),
    )
    return AnalyzerExecutionResult(reading=_attach_audit(reading, audit), audit=audit)


def _timeout_result(
    *,
    parsed: Any,
    domain: DomainName,
    case_id: str,
    expert_system: ExpertSystem,
    base_context: dict[str, Any],
    duration_ms: float,
) -> AnalyzerExecutionResult:
    message = "分析器超时，按隔离原则弃权。"
    reading = _attach_diagnostic_evidence(
        _fallback_abstain(
            parsed=parsed,
            domain=domain,
            case_id=case_id,
            expert_system=expert_system,
            base_context=base_context,
            reason=message,
            source_engine="parallel_domain_runner.timeout_envelope",
        ),
        error_type="TimeoutError",
        message=message,
        duration_ms=duration_ms,
        source_engine="parallel_domain_runner.timeout_envelope",
    )
    audit = AnalyzerExecutionAudit(
        case_id=case_id,
        domain=domain,
        expert_system=expert_system,
        status="timeout",
        duration_ms=duration_ms,
        source_engine=reading.source_engine,
        error_type="TimeoutError",
        message=message,
    )
    return AnalyzerExecutionResult(reading=_attach_audit(reading, audit), audit=audit)


def _fallback_abstain(
    *,
    parsed: Any,
    domain: DomainName,
    case_id: str,
    expert_system: ExpertSystem,
    base_context: dict[str, Any],
    reason: str,
    source_engine: str,
) -> ExpertReading:
    context = DomainAnalysisContext(
        case_id=case_id,
        base_context=copy.deepcopy(base_context),
    )
    return AbstainDomainAnalyzer(
        expert_system=expert_system,
        expert_name=EXPERT_LABELS[expert_system],
        reason=reason,
        source_engine=source_engine,
    ).analyze(copy.deepcopy(parsed), domain, context)


def _attach_diagnostic_evidence(
    reading: ExpertReading,
    *,
    error_type: str,
    message: str,
    duration_ms: float,
    source_engine: str,
) -> ExpertReading:
    data = reading.to_dict()
    data["evidence_items"] = list(data.get("evidence_items", []))
    data["evidence_items"].append(
        EvidenceItem(
            evidence_type="runtime_finding",
            ref=f"{source_engine}:{error_type}",
            summary=(
                f"exception_class={error_type}; exception_message={message}; "
                f"source_engine={source_engine}; duration_ms={duration_ms:.3f}"
            ),
            strength="low",
        ).to_dict()
    )
    return ExpertReading.from_dict(data)


def _attach_audit(reading: ExpertReading, audit: AnalyzerExecutionAudit) -> ExpertReading:
    data = reading.to_dict()
    marker = f"execution_audit={audit.to_dict()}"
    data["notes"] = f"{data.get('notes', '')}；{marker}" if data.get("notes") else marker
    return ExpertReading.from_dict(data)


def _case_id_from_parsed(parsed: Any) -> str:
    case_id = getattr(parsed, "case_id", None)
    if case_id:
        return str(case_id)
    meta = getattr(parsed, "meta", None)
    if isinstance(meta, dict) and meta.get("case_id"):
        return str(meta["case_id"])
    return "C-UNKNOWN"
