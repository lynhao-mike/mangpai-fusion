"""legacy 与 Claim run 的确定性结构化差异。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from engine.application.staged_parallel_runner import ParallelRun, run_parallel
from engine.evaluation.models import BlindSchoolOutput, BlindTask

ComparisonStatus = Literal["same", "differ", "only_legacy", "only_claim", "both_missing"]


@dataclass(frozen=True)
class StructuredRunItem:
    task_id: str
    school_id: str
    domain: str
    claim_state: str | None
    event_label: str | None = None
    polarity: str | None = None
    time_window: Mapping[str, object] | None = None
    risk_flag: bool | None = None
    evidence_completeness: str | None = None


@dataclass(frozen=True)
class DimensionDifference:
    status: ComparisonStatus
    legacy: object | None
    claim: object | None

    def to_dict(self) -> dict[str, object | None]:
        return {"status": self.status, "legacy": self.legacy, "claim": self.claim}


@dataclass(frozen=True)
class RunComparisonItem:
    task_id: str
    school_id: str
    domain: str
    task_coverage: DimensionDifference
    claim_state: DimensionDifference
    event_label: DimensionDifference
    polarity: DimensionDifference
    time_window: DimensionDifference
    risk_flag: DimensionDifference
    evidence_completeness: DimensionDifference

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "school_id": self.school_id,
            "domain": self.domain,
            "task_coverage": self.task_coverage.to_dict(),
            "claim_state": self.claim_state.to_dict(),
            "event_label": self.event_label.to_dict(),
            "polarity": self.polarity.to_dict(),
            "time_window": self.time_window.to_dict(),
            "risk_flag": self.risk_flag.to_dict(),
            "evidence_completeness": self.evidence_completeness.to_dict(),
        }


@dataclass(frozen=True)
class RunComparison:
    case_id: str
    items: tuple[RunComparisonItem, ...]
    legacy_error: str | None = None
    claim_error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "legacy_error": self.legacy_error,
            "claim_error": self.claim_error,
            "items": [item.to_dict() for item in sorted(self.items, key=lambda row: (row.task_id, row.school_id))],
        }


def _canonical_window(value: Mapping[str, object] | None) -> dict[str, object] | None:
    if not value:
        return None
    return {
        "start_year": value.get("start_year"),
        "end_year": value.get("end_year"),
        "label": value.get("label"),
    }


def _difference(legacy: object | None, claim: object | None) -> DimensionDifference:
    if legacy is None and claim is None:
        status: ComparisonStatus = "both_missing"
    elif legacy is None:
        status = "only_claim"
    elif claim is None:
        status = "only_legacy"
    elif legacy == claim:
        status = "same"
    else:
        status = "differ"
    return DimensionDifference(status, legacy, claim)


def _legacy_items(snapshot: Any | None) -> tuple[StructuredRunItem, ...]:
    if snapshot is None:
        return ()
    explicit = getattr(snapshot, "structured_run_items", None)
    if explicit is not None:
        return tuple(explicit)

    rows: list[StructuredRunItem] = []
    for conclusion in getattr(snapshot, "final_conclusions", ()):
        year = getattr(conclusion, "yingqi_year", None)
        rows.append(StructuredRunItem(
            task_id=str(getattr(conclusion, "task_id", "") or getattr(conclusion, "domain", "")),
            school_id=str(getattr(conclusion, "school_id", "legacy")),
            domain=str(getattr(conclusion, "domain", "")),
            claim_state="claim",
            event_label=getattr(conclusion, "event_label", None),
            polarity=getattr(conclusion, "polarity", None),
            time_window={"start_year": year, "end_year": year, "label": "annual"} if year is not None else None,
            risk_flag=getattr(conclusion, "high_risk", None),
            evidence_completeness=getattr(conclusion, "evidence_completeness", None),
        ))
    return tuple(rows)


def _claim_item(
    output: BlindSchoolOutput,
    metadata: Mapping[str, object],
    fallback_completeness: str | None,
) -> StructuredRunItem:
    prediction = output.predictions[0] if output.predictions else None
    return StructuredRunItem(
        task_id=output.task_id,
        school_id=output.school_id,
        domain=str(metadata.get("domain", "")),
        claim_state=output.state,
        event_label=prediction.event_label if prediction else None,
        polarity=metadata.get("polarity") if isinstance(metadata.get("polarity"), str) else None,
        time_window=_canonical_window(prediction.time_window) if prediction else None,
        risk_flag=metadata.get("risk_flag") if isinstance(metadata.get("risk_flag"), bool) else None,
        evidence_completeness=(
            str(metadata["evidence_completeness"])
            if metadata.get("evidence_completeness") is not None
            else fallback_completeness
        ),
    )


def _claim_items(parallel_run: ParallelRun) -> tuple[StructuredRunItem, ...]:
    if parallel_run.claim_snapshot is None:
        return ()
    task_metadata = {task_id: (domain, high_risk) for task_id, domain, high_risk in parallel_run.task_metadata}
    extra = getattr(parallel_run.claim_snapshot, "comparison_metadata", {})
    rows = []
    for output in parallel_run.claim_snapshot.outputs:
        domain, high_risk = task_metadata.get(output.task_id, ("", False))
        metadata = dict(extra.get((output.task_id, output.school_id), {}))
        metadata.setdefault("domain", domain)
        metadata.setdefault("risk_flag", high_risk)
        rows.append(_claim_item(output, metadata, parallel_run.evidence_completeness))
    return tuple(rows)


def compare_runs(parallel_run: ParallelRun) -> RunComparison:
    """按 (task_id, school_id) 对齐并比较七个结构化维度。"""
    legacy = {(item.task_id, item.school_id): item for item in _legacy_items(parallel_run.legacy_snapshot)}
    claim = {(item.task_id, item.school_id): item for item in _claim_items(parallel_run)}
    items = []
    for key in sorted(set(legacy) | set(claim)):
        left = legacy.get(key)
        right = claim.get(key)
        items.append(RunComparisonItem(
            task_id=key[0],
            school_id=key[1],
            domain=(left.domain if left else right.domain if right else ""),
            task_coverage=_difference(left is not None if left else None, right is not None if right else None),
            claim_state=_difference(left.claim_state if left else None, right.claim_state if right else None),
            event_label=_difference(left.event_label if left else None, right.event_label if right else None),
            polarity=_difference(left.polarity if left else None, right.polarity if right else None),
            time_window=_difference(
                _canonical_window(left.time_window) if left else None,
                _canonical_window(right.time_window) if right else None,
            ),
            risk_flag=_difference(left.risk_flag if left else None, right.risk_flag if right else None),
            evidence_completeness=_difference(
                left.evidence_completeness if left else None,
                right.evidence_completeness if right else None,
            ),
        ))
    return RunComparison(
        case_id=parallel_run.case_id,
        items=tuple(items),
        legacy_error=parallel_run.legacy_error,
        claim_error=parallel_run.claim_error,
    )


def run_and_compare(
    chart: object,
    tasks: Sequence[BlindTask],
    *,
    case_id: str,
    schools: Sequence[str],
    registry: object = None,
) -> RunComparison:
    """显式组合并跑与比较，不改变任何默认入口。"""
    kwargs: dict[str, object] = {"case_id": case_id, "schools": schools}
    if registry is not None:
        kwargs["registry"] = registry
    return compare_runs(run_parallel(chart, tasks, **kwargs))  # type: ignore[arg-type]
