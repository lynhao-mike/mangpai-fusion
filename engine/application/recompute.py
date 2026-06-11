from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from tools.feedback_ingest import parse_statement_feedback

from engine.application.confidence_delta import build_confidence_delta
from engine.application.conclusion_diff import build_conclusion_diff
from engine.application.pipeline_runner import run_pipeline_e2e
from engine.application.school_verdict import build_school_verdict_matrix


class RecomputeHardGateError(RuntimeError):
    """Raised when a Wenzhen recompute run does not produce required artifacts."""


@dataclass(frozen=True)
class RecomputeRequest:
    input_path: Path
    cases_dir: Path = Path("cases")
    reports_dir: Path = Path("reports")
    cases_index_path: Path | None = None
    template_name: str = "report-v1.3.md"
    report_variant: str = "standard"
    require_statement_index: bool = True


@dataclass(frozen=True)
class RecomputeResult:
    case_id: str
    case_dir: Path
    artifacts: dict[str, Path]
    manifest: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_dir": str(self.case_dir),
            "artifacts": {key: str(path) for key, path in self.artifacts.items()},
            "manifest": self.manifest,
        }


PipelineRunner = Callable[..., tuple[Any, Any]]


def recompute_wenzhen_case(
    request: RecomputeRequest,
    *,
    pipeline_runner: PipelineRunner = run_pipeline_e2e,
) -> RecomputeResult:
    input_path = Path(request.input_path)
    cases_dir = Path(request.cases_dir)
    reports_dir = Path(request.reports_dir)
    case_dir = input_path.parent
    case_id = case_dir.name

    before_output = _read_json(case_dir / "findings" / "analysis_output.json")
    before_hash = _sha256_if_exists(input_path)

    output, timing = pipeline_runner(
        input_path,
        cases_dir=cases_dir,
        cases_index_path=request.cases_index_path,
        do_render=True,
        do_self_iter=False,
        template_name=request.template_name,
        report_variant=request.report_variant,
        error_policy="strict",
    )
    output_dict = output.to_dict() if hasattr(output, "to_dict") else dict(output)
    case_id = str(output_dict.get("case_id") or case_id)
    case_dir = cases_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    statement_index_path = case_dir / "statement_index.json"
    statement_index = _load_statement_index(statement_index_path)
    if request.require_statement_index:
        _assert_statement_index_ready(statement_index_path, statement_index)

    after_hash = _sha256_if_exists(input_path)
    school_matrix = build_school_verdict_matrix(output_dict).to_dict()
    conclusion_diff = build_conclusion_diff(
        case_id=case_id,
        before_output=before_output,
        after_output=output_dict,
    ).to_dict()
    confidence_delta = build_confidence_delta(
        case_id=case_id,
        before_output=before_output,
        after_output=output_dict,
    ).to_dict()
    feedback_binding = _build_feedback_binding_check(case_dir, statement_index)

    report_path = reports_dir / f"{case_id}-content-report.md"
    artifacts = {
        "findings_before": case_dir / "findings.before.json",
        "findings_after": case_dir / "findings.after.json",
        "school_verdict_matrix": case_dir / "school_verdict_matrix.json",
        "conclusion_diff": case_dir / "conclusion_diff.json",
        "confidence_delta": case_dir / "confidence_delta.json",
        "feedback_binding_check": case_dir / "feedback_binding_check.json",
        "recompute_manifest": case_dir / "recompute_manifest.json",
    }

    _write_json(artifacts["findings_before"], before_output or {})
    _write_json(artifacts["findings_after"], output_dict)
    _write_json(artifacts["school_verdict_matrix"], school_matrix)
    _write_json(artifacts["conclusion_diff"], conclusion_diff)
    _write_json(artifacts["confidence_delta"], confidence_delta)
    _write_json(artifacts["feedback_binding_check"], feedback_binding)

    manifest = {
        "case_id": case_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_path": str(input_path),
        "input_sha256_before": before_hash,
        "input_sha256_after": after_hash,
        "pipeline_schema_version": output_dict.get("pipeline_version"),
        "findings_schema_version": output_dict.get("schema_version"),
        "timing_total_seconds": getattr(timing, "total_seconds", None),
        "hard_gates": {
            "statement_index_required": request.require_statement_index,
            "statement_index_statement_count": len(statement_index.get("statements") or []),
            "feedback_binding_ready": feedback_binding["ready"],
            "structured_feedback_count": feedback_binding["structured_feedback_count"],
        },
        "artifacts": {
            **{key: str(path) for key, path in artifacts.items() if key != "recompute_manifest"},
            "statement_index": str(statement_index_path),
            "content_report": str(report_path),
        },
    }
    _write_json(artifacts["recompute_manifest"], manifest)

    return RecomputeResult(
        case_id=case_id,
        case_dir=case_dir,
        artifacts=artifacts,
        manifest=manifest,
    )


def _load_statement_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = _read_json(path)
    return data if isinstance(data, dict) else {}


def _assert_statement_index_ready(path: Path, index: dict[str, Any]) -> None:
    statements = index.get("statements")
    if not isinstance(statements, list) or not statements:
        raise RecomputeHardGateError(
            f"statement_index is required and must contain statements: {path}"
        )


def _build_feedback_binding_check(case_dir: Path, statement_index: dict[str, Any]) -> dict[str, Any]:
    statement_ids = {
        str(item.get("statement_id"))
        for item in statement_index.get("statements") or []
        if isinstance(item, dict) and item.get("statement_id")
    }
    feedback_path = case_dir / "feedback.md"
    feedback_text = feedback_path.read_text(encoding="utf-8") if feedback_path.exists() else ""
    structured_feedback = parse_statement_feedback(feedback_text) if feedback_text else []
    structured_ids = sorted({item.statement_id for item in structured_feedback})
    referenced = sorted(statement_id for statement_id in statement_ids if statement_id in feedback_text)
    unknown_structured_ids = sorted(set(structured_ids) - statement_ids)
    return {
        "feedback_path": str(feedback_path),
        "statement_count": len(statement_ids),
        "referenced_statement_count": len(referenced),
        "referenced_statement_ids": referenced,
        "structured_feedback_count": len(structured_feedback),
        "structured_feedback_statement_ids": structured_ids,
        "unknown_structured_statement_ids": unknown_structured_ids,
        "ready": bool(statement_ids),
        "structured_feedback_ready": bool(structured_feedback) and not unknown_structured_ids,
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_if_exists(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
