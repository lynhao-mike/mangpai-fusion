"""生产分析 artifact 清单应用服务。

把 [`ProductionAnalysisService`](engine/application/production_service.py) 中的 artifact
发现、报告 artifact 写入、路径展示与 sha256 计算抽离到独立模块，降低生产服务
的职责密度。该模块只处理文件系统 artifact 编目，不触碰 job store、cache 或
pipeline 编排。
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any, Union

from engine.infrastructure.analysis_store import AnalysisArtifactRecord


FINDINGS_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("energy", "energy.json"),
    ("picture", "picture.json"),
    ("gate_results", "gate_results.json"),
    ("support", "support.json"),
    ("analysis_output", "analysis_output.json"),
    ("timing", "timing.json"),
)


def collect_analysis_artifacts(
    *,
    case_id: str,
    output: Any,
    render: bool,
    cases_dir: Path,
    reports_dir: Path,
    workspace_root: Path,
    created_at: str,
) -> list[AnalysisArtifactRecord]:
    """收集一次分析运行产生的 artifact 记录。

    保持历史生产服务行为：先记录 findings 内固定 JSON 文件，再记录
    statement_index.json；若本次开启 render 且 output 带 report_md，则写入
    reports/{case_id}-content-report.md 并记录 report artifact。
    """
    artifacts: list[AnalysisArtifactRecord] = []
    findings_dir = cases_dir / case_id / "findings"
    for kind, filename in FINDINGS_ARTIFACTS:
        append_artifact_if_exists(
            artifacts,
            kind=kind,
            path=findings_dir / filename,
            workspace_root=workspace_root,
            created_at=created_at,
        )

    statement_index = cases_dir / case_id / "statement_index.json"
    append_artifact_if_exists(
        artifacts,
        kind="statement_index",
        path=statement_index,
        workspace_root=workspace_root,
        created_at=created_at,
    )

    if render and hasattr(output, "report_md"):
        report_path = write_report_artifact(
            case_id=case_id,
            report_md=str(getattr(output, "report_md")),
            reports_dir=reports_dir,
        )
        append_artifact_if_exists(
            artifacts,
            kind="report",
            path=report_path,
            workspace_root=workspace_root,
            created_at=created_at,
        )
    return artifacts


def write_report_artifact(*, case_id: str, report_md: str, reports_dir: Path) -> Path:
    """以历史文件名与临时文件 move 语义写入统一内容报告 artifact。"""
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{case_id}-content-report.md"
    tmp_path = reports_dir / f".{case_id}-content-report.tmp"
    tmp_path.write_text(report_md, encoding="utf-8")
    shutil.move(str(tmp_path), str(report_path))
    return report_path


def append_artifact_if_exists(
    artifacts: list[AnalysisArtifactRecord],
    *,
    kind: str,
    path: Path,
    workspace_root: Path,
    created_at: str,
) -> None:
    """若 artifact 文件存在，则追加带展示路径与 sha256 的记录。"""
    if not path.exists():
        return
    artifacts.append(
        AnalysisArtifactRecord(
            kind=kind,
            path=display_path(path, workspace_root=workspace_root),
            sha256=file_sha256(path),
            created_at=created_at,
        )
    )


def display_path(path: Union[str, Path], *, workspace_root: Path) -> str:
    """返回相对 workspace 的展示路径；若不在 workspace 下则返回绝对路径。"""
    p = Path(path).resolve()
    try:
        return p.relative_to(workspace_root).as_posix()
    except ValueError:
        return str(p)


def file_sha256(path: Path) -> str:
    """流式计算文件 sha256，保持历史 1MiB 分块行为。"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
