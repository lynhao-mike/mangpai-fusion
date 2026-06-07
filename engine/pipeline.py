"""engine/pipeline.py · 兼容外观层。

Clean Architecture 分层后，本模块保留历史公开入口，避免外部调用方修改导入路径。
实际实现已拆分到：
- engine.domain.analysis：领域数据结构
- engine.application.timing：计时与软护栏
- engine.application.integration：D1-D4 结果整合
- engine.application.pipeline_runner：pipeline 用例编排
- engine.infrastructure.findings_repository：findings 文件归档
"""
from __future__ import annotations

import logging

from engine.application.candidates import _extract_candidates
from engine.application.dual_engine_adapter import (
    analyze_dual_engine,
    build_blind_findings,
    build_fusion_findings,
    build_theory_findings,
)
from engine.application.integration import (
    _build_yingqi_table,
    _gate_to_conclusion,
    _infer_industry_path,
    _infer_wealth_framework,
    integrate,
    verify_hash_chain,
)
from engine.application.pipeline_runner import run_pipeline, run_pipeline_e2e
from engine.application.timing import (
    PIPELINE_STEP_NAMES,
    PIPELINE_THRESHOLD_SECONDS,
    PipelineTiming,
    StepTiming,
)
from engine.domain.analysis import (
    AnalysisOutput,
    ConclusionLayer,
    CrossSchoolConflict,
    FinalConclusion,
    Stance,
    _load_retrospective,
)
from engine.domain.dual_engine import BlindFindings, FusionFindings, TheoryFindings
from engine.infrastructure.findings_repository import _save_findings, save_findings

logger = logging.getLogger(__name__)

__all__ = [
    "AnalysisOutput",
    "ConclusionLayer",
    "CrossSchoolConflict",
    "FinalConclusion",
    "PIPELINE_STEP_NAMES",
    "PIPELINE_THRESHOLD_SECONDS",
    "PipelineTiming",
    "Stance",
    "StepTiming",
    "TheoryFindings",
    "BlindFindings",
    "FusionFindings",
    "_build_yingqi_table",
    "_extract_candidates",
    "_gate_to_conclusion",
    "_infer_industry_path",
    "_infer_wealth_framework",
    "_load_retrospective",
    "_save_findings",
    "analyze_dual_engine",
    "build_blind_findings",
    "build_fusion_findings",
    "build_theory_findings",
    "integrate",
    "run_pipeline",
    "run_pipeline_e2e",
    "save_findings",
    "verify_hash_chain",
]
