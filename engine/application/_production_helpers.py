"""Private pure and filesystem-bound helpers for the production service."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Union

from engine.application.artifact_inventory import collect_analysis_artifacts
from engine.application.cache_key import DEFAULT_TEMPLATE_NAME, compute_cache_key
from engine.infrastructure.analysis_store import AnalysisArtifactRecord


def resolve_under_workspace(path: Union[str, Path], workspace_root: Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(workspace_root)
    except ValueError as exc:
        raise ValueError(f"path must stay under workspace: {path}") from exc
    return resolved


def normalize_request(request: Any, workspace_root: Path) -> Any:
    input_path = resolve_under_workspace(request.input_path, workspace_root)
    if not input_path.exists():
        raise FileNotFoundError(f"input_path does not exist: {request.input_path}")
    if input_path.name != "input.md":
        raise ValueError(f"input_path must point to input.md: {request.input_path}")

    cases_dir = (
        resolve_under_workspace(request.cases_dir, workspace_root)
        if request.cases_dir is not None
        else workspace_root / "cases"
    )
    reports_dir = (
        resolve_under_workspace(request.reports_dir, workspace_root)
        if request.reports_dir is not None
        else workspace_root / "reports"
    )
    cases_index_path = (
        resolve_under_workspace(request.cases_index_path, workspace_root)
        if request.cases_index_path is not None
        else None
    )
    return replace(
        request,
        input_path=input_path,
        render=bool(request.render),
        force=bool(request.force),
        template_name=DEFAULT_TEMPLATE_NAME,
        render_v6_preprod=bool(request.render_v6_preprod),
        cases_dir=cases_dir,
        reports_dir=reports_dir,
        cases_index_path=cases_index_path,
    )


def prepare_request(
    request: Any,
    workspace_root: Path,
    cache_key_for: Callable[..., str] = compute_cache_key,
) -> tuple[Any, str, str]:
    normalized = normalize_request(request, workspace_root)
    input_sha256 = hashlib.sha256(normalized.input_path.read_bytes()).hexdigest()
    cache_key = cache_key_for(
        input_sha256=input_sha256,
        render=normalized.render,
        template_name=normalized.template_name,
        render_v6_preprod=normalized.render_v6_preprod,
    )
    return normalized, input_sha256, cache_key


def collect_production_artifacts(
    *,
    case_id: str,
    output: Any,
    request: Any,
    workspace_root: Path,
    completed_at: str,
    append_if_exists: Callable[..., None],
) -> list[AnalysisArtifactRecord]:
    artifacts = collect_analysis_artifacts(
        case_id=case_id,
        output=output,
        render=request.render,
        cases_dir=request.cases_dir or workspace_root / "cases",
        reports_dir=request.reports_dir or workspace_root / "reports",
        workspace_root=workspace_root,
        created_at=completed_at,
    )
    if request.render_v6_preprod:
        reports_dir = request.reports_dir or workspace_root / "reports"
        for kind, filename in (
            ("v6_preprod_report", f"{case_id}-v6-preprod-content-report.md"),
            ("v5_prediction_ledger", f"{case_id}-v6-preprod-content-report.v5.json"),
            ("decision_run_ledger", f"{case_id}-v6-preprod-content-report.decision-run.json"),
        ):
            append_if_exists(
                artifacts,
                kind=kind,
                path=reports_dir / filename,
                created_at=completed_at,
            )
    return artifacts


def build_summary(output: Any, timing: Any) -> dict[str, Any]:
    confidence = getattr(output, "overall_confidence", None)
    summary: dict[str, Any] = {
        "case_id": getattr(output, "case_id", ""),
        "analysis_date": getattr(output, "analysis_date", ""),
        "final_conclusions_count": len(getattr(output, "final_conclusions", []) or []),
        "conflicts_count": len(getattr(output, "conflicts", []) or []),
        "gate_results_count": len(getattr(output, "gate_results", []) or []),
        "hash_chain_valid": bool(getattr(output, "hash_chain_valid", True)),
        "pipeline_total_seconds": getattr(timing, "total_seconds", None),
    }
    if confidence is not None:
        summary["overall_confidence"] = {
            "star": getattr(confidence, "star", None),
            "percent": getattr(confidence, "percent", None),
            "label": getattr(confidence, "label", ""),
        }
    return summary
