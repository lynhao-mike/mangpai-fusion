"""Production-facing application service for mangpai-fusion analyses.

The service wraps the existing preflight/pipeline/render workflow with
production concerns: idempotent-ish job IDs, cache keys, SQLite metadata,
artifact inventory, and stable response envelopes.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

from engine import FINDINGS_SCHEMA_VERSION, PIPELINE_SCHEMA_VERSION, __version__
from engine.application.artifact_inventory import (
    append_artifact_if_exists,
    collect_analysis_artifacts,
    display_path,
    file_sha256,
    write_report_artifact,
)
from engine.application.cache_key import compute_cache_key as _compute_cache_key
from engine.application.pipeline_runner import run_pipeline_e2e
from engine.infrastructure.analysis_store import (
    AnalysisArtifactRecord,
    AnalysisJobRecord,
    SQLiteAnalysisStore,
)


DEFAULT_TEMPLATE_NAME = "report-v1.3.md"
STANDARD_REPORT_VARIANT = "standard"
SERVICE_NAME = "mangpai-fusion-production-api"


@dataclass(frozen=True)
class SubmitAnalysisRequest:
    """Validated production analysis request."""

    input_path: Path
    render: bool = True
    force: bool = False
    template_name: str = DEFAULT_TEMPLATE_NAME
    cases_dir: Optional[Path] = None
    reports_dir: Optional[Path] = None
    cases_index_path: Optional[Path] = None


class ProductionAnalysisService:
    """Synchronous production MVP service around the existing analysis pipeline."""

    def __init__(
        self,
        *,
        store: SQLiteAnalysisStore,
        workspace_root: Optional[Union[str, Path]] = None,
    ) -> None:
        self.store = store
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()

    def health(self) -> dict[str, Any]:
        return {
            "service": SERVICE_NAME,
            "status": "ok",
            "engine_version": __version__,
            "findings_schema_version": FINDINGS_SCHEMA_VERSION,
            "pipeline_schema_version": PIPELINE_SCHEMA_VERSION,
            "database": str(self.store.db_path),
            "workspace_root": str(self.workspace_root),
        }

    def submit(self, request: SubmitAnalysisRequest) -> dict[str, Any]:
        """Run or reuse one analysis and return a stable response envelope."""
        normalized, input_sha256, cache_key = self._prepare_request(request)

        if not normalized.force:
            cached = self.store.get_cached_job(cache_key)
            if cached is not None and cached.status == "completed":
                cached_response = self._record_cached_response(
                    cached=cached,
                    input_path=normalized.input_path,
                    input_sha256=input_sha256,
                    cache_key=cache_key,
                    request=normalized,
                )
                return cached_response.to_dict()

        now = _utc_now()
        analysis_id = self.new_analysis_id(now)
        self.store.create_job(
            analysis_id=analysis_id,
            input_path=self._display_path(normalized.input_path),
            input_sha256=input_sha256,
            cache_key=cache_key,
            engine_version=__version__,
            render=normalized.render,
            template_name=normalized.template_name,
            created_at=now,
            started_at=now,
        )
        return self._run_existing_job(analysis_id, normalized, input_sha256, cache_key).to_dict()

    def enqueue(self, request: SubmitAnalysisRequest) -> AnalysisJobRecord:
        """Create a queued job without running the pipeline."""
        normalized, input_sha256, cache_key = self._prepare_request(request)
        if not normalized.force:
            cached = self.store.get_cached_job(cache_key)
            if cached is not None and cached.status == "completed":
                return self._record_cached_response(
                    cached=cached,
                    input_path=normalized.input_path,
                    input_sha256=input_sha256,
                    cache_key=cache_key,
                    request=normalized,
                )
        now = _utc_now()
        analysis_id = self.new_analysis_id(now)
        return self.store.create_job(
            analysis_id=analysis_id,
            input_path=self._display_path(normalized.input_path),
            input_sha256=input_sha256,
            cache_key=cache_key,
            engine_version=__version__,
            render=normalized.render,
            template_name=normalized.template_name,
            created_at=now,
            status="queued",
        )

    def run_queued(self, analysis_id: str, request: SubmitAnalysisRequest) -> AnalysisJobRecord:
        """Run a previously queued job in a worker."""
        normalized, input_sha256, cache_key = self._prepare_request(request)
        self.store.mark_job_running(analysis_id=analysis_id, started_at=_utc_now())
        return self._run_existing_job(analysis_id, normalized, input_sha256, cache_key)

    def _run_existing_job(
        self,
        analysis_id: str,
        normalized: SubmitAnalysisRequest,
        input_sha256: str,
        cache_key: str,
    ) -> AnalysisJobRecord:
        try:
            output, timing = run_pipeline_e2e(
                normalized.input_path,
                cases_dir=normalized.cases_dir,
                cases_index_path=normalized.cases_index_path,
                do_render=normalized.render,
                do_self_iter=False,
                template_name=DEFAULT_TEMPLATE_NAME,
                report_variant=STANDARD_REPORT_VARIANT,
            )
            case_id = str(output.case_id or "")
            summary = self._build_summary(output, timing)
            artifacts = self._collect_artifacts(
                case_id=case_id,
                output=output,
                timing=timing,
                request=normalized,
                completed_at=_utc_now(),
            )
            completed_at = _utc_now()
            job = self.store.complete_job(
                analysis_id=analysis_id,
                case_id=case_id,
                summary=summary,
                completed_at=completed_at,
                artifacts=artifacts,
            )
            self.store.save_cache(
                cache_key=cache_key,
                analysis_id=analysis_id,
                case_id=case_id,
                input_sha256=input_sha256,
                engine_version=__version__,
                summary=summary,
                created_at=completed_at,
            )
            return job
        except Exception as exc:  # noqa: BLE001 - preserve production job state
            failed = self.store.fail_job(
                analysis_id=analysis_id,
                error=f"{type(exc).__name__}: {exc}",
                completed_at=_utc_now(),
            )
            return failed

    def get(self, analysis_id: str) -> Optional[dict[str, Any]]:
        job = self.store.get_job(analysis_id)
        return job.to_dict() if job is not None else None

    def list(
        self,
        *,
        status: Optional[str] = None,
        case_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List recent production jobs for dashboards and polling clients."""
        return [
            job.to_dict()
            for job in self.store.list_jobs(
                status=status,
                case_id=case_id,
                limit=limit,
                offset=offset,
            )
        ]

    def _prepare_request(self, request: SubmitAnalysisRequest) -> tuple[SubmitAnalysisRequest, str, str]:
        normalized = self._normalize_request(request)
        input_bytes = normalized.input_path.read_bytes()
        input_sha256 = hashlib.sha256(input_bytes).hexdigest()
        cache_key = self.compute_cache_key(
            input_sha256=input_sha256,
            render=normalized.render,
            template_name=normalized.template_name,
        )
        return normalized, input_sha256, cache_key

    def compute_cache_key(
        self,
        *,
        input_sha256: str,
        render: bool,
        template_name: str,
    ) -> str:
        return _compute_cache_key(
            input_sha256=input_sha256,
            render=render,
            template_name=template_name,
        )

    def new_analysis_id(self, now: Optional[str] = None) -> str:
        stamp = (now or _utc_now()).replace("-", "").replace(":", "")
        stamp = stamp.replace("T", "-").replace("Z", "").split(".")[0]
        return f"AN-{stamp}-{uuid.uuid4().hex[:12]}"

    def _record_cached_response(
        self,
        *,
        cached: AnalysisJobRecord,
        input_path: Path,
        input_sha256: str,
        cache_key: str,
        request: SubmitAnalysisRequest,
    ) -> AnalysisJobRecord:
        now = _utc_now()
        analysis_id = self.new_analysis_id(now)
        self.store.create_job(
            analysis_id=analysis_id,
            input_path=self._display_path(input_path),
            input_sha256=input_sha256,
            cache_key=cache_key,
            engine_version=__version__,
            render=request.render,
            template_name=request.template_name,
            created_at=now,
            status="completed",
            case_id=cached.case_id,
            cache_hit=True,
            started_at=now,
        )
        return self.store.complete_job(
            analysis_id=analysis_id,
            case_id=cached.case_id,
            summary=cached.summary,
            completed_at=now,
            artifacts=cached.artifacts,
            cache_hit=True,
        )

    def _normalize_request(self, request: SubmitAnalysisRequest) -> SubmitAnalysisRequest:
        input_path = self._resolve_under_workspace(request.input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"input_path does not exist: {request.input_path}")
        if input_path.name != "input.md":
            raise ValueError(f"input_path must point to input.md: {request.input_path}")
        cases_dir = (
            self._resolve_under_workspace(request.cases_dir)
            if request.cases_dir is not None
            else self.workspace_root / "cases"
        )
        reports_dir = (
            self._resolve_under_workspace(request.reports_dir)
            if request.reports_dir is not None
            else self.workspace_root / "reports"
        )
        cases_index_path = (
            self._resolve_under_workspace(request.cases_index_path)
            if request.cases_index_path is not None
            else None
        )
        return SubmitAnalysisRequest(
            input_path=input_path,
            render=bool(request.render),
            force=bool(request.force),
            template_name=DEFAULT_TEMPLATE_NAME,
            cases_dir=cases_dir,
            reports_dir=reports_dir,
            cases_index_path=cases_index_path,
        )

    def _resolve_under_workspace(self, path: Union[str, Path]) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.workspace_root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise ValueError(f"path must stay under workspace: {path}") from exc
        return resolved

    def _collect_artifacts(
        self,
        *,
        case_id: str,
        output: Any,
        timing: Any,
        request: SubmitAnalysisRequest,
        completed_at: str,
    ) -> list[AnalysisArtifactRecord]:
        return collect_analysis_artifacts(
            case_id=case_id,
            output=output,
            render=request.render,
            cases_dir=request.cases_dir or self.workspace_root / "cases",
            reports_dir=request.reports_dir or self.workspace_root / "reports",
            workspace_root=self.workspace_root,
            created_at=completed_at,
        )

    def _write_report_artifact(self, *, case_id: str, report_md: str, reports_dir: Path) -> Path:
        return write_report_artifact(case_id=case_id, report_md=report_md, reports_dir=reports_dir)

    def _append_artifact_if_exists(
        self,
        artifacts: list[AnalysisArtifactRecord],
        *,
        kind: str,
        path: Path,
        created_at: str,
    ) -> None:
        append_artifact_if_exists(
            artifacts,
            kind=kind,
            path=path,
            workspace_root=self.workspace_root,
            created_at=created_at,
        )

    def _build_summary(self, output: Any, timing: Any) -> dict[str, Any]:
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

    def _display_path(self, path: Union[str, Path]) -> str:
        return display_path(path, workspace_root=self.workspace_root)


def request_from_dict(payload: dict[str, Any]) -> SubmitAnalysisRequest:
    """Build a request DTO from API JSON payload."""
    input_path = payload.get("input_path")
    if not isinstance(input_path, str) or not input_path.strip():
        raise ValueError("input_path is required")
    return SubmitAnalysisRequest(
        input_path=Path(input_path),
        render=bool(payload.get("render", True)),
        force=bool(payload.get("force", False)),
        template_name=DEFAULT_TEMPLATE_NAME,
        cases_dir=Path(str(payload["cases_dir"])) if payload.get("cases_dir") else None,
        reports_dir=Path(str(payload["reports_dir"])) if payload.get("reports_dir") else None,
        cases_index_path=(
            Path(str(payload["cases_index_path"]))
            if payload.get("cases_index_path")
            else None
        ),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _file_sha256(path: Path) -> str:
    return file_sha256(path)
