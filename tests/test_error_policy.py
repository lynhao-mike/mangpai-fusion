"""tests/test_error_policy.py · C 方案回归测试

验证 run_pipeline_e2e() 的 error_policy 参数行为：

| ID     | 场景                                  | tolerant 期望       | strict 期望         |
|--------|---------------------------------------|---------------------|---------------------|
| EP-001 | renderer.render() 抛出 RuntimeError   | 仅 warning，正常返回 | 异常向上传播         |
| EP-002 | findings 落盘失败（_save_findings 抛） | 仅 warning，正常返回 | 异常向上传播         |
| EP-003 | self_iter.ingest() 抛出 RuntimeError  | 仅 warning，正常返回 | 异常向上传播         |
| EP-004 | ProductionAnalysisService 使用 strict | render 失败 → job.status == "failed" |

作者：C 方案实施
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Union
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.application.pipeline_runner import run_pipeline_e2e
from engine.application.ports import PipelineAdapters
from engine.domain.analysis import AnalysisOutput
from engine.predicates.types import ParsedInput


# ---------------------------------------------------------------------------
# 辅助：构造最小 mock ParsedInput 与 AnalysisOutput
# ---------------------------------------------------------------------------

def _make_mock_parsed() -> MagicMock:
    """返回满足 run_pipeline() 最低要求的 ParsedInput mock。"""
    parsed = MagicMock(spec=ParsedInput)
    parsed.case_id = "C-TEST-EP-001"
    return parsed


def _make_mock_output(case_id: str = "C-TEST-EP-001") -> MagicMock:
    """返回满足 run_pipeline_e2e 后续步骤最低要求的 AnalysisOutput mock。"""
    output = MagicMock(spec=AnalysisOutput)
    output.case_id = case_id
    return output


# ---------------------------------------------------------------------------
# EP-001 · renderer 失败
# ---------------------------------------------------------------------------

class _FailingRenderer:
    """render() 永远抛出 RuntimeError 的 stub。"""

    def render(
        self,
        output: AnalysisOutput,
        *,
        template_name: str,
        variant: str,
        cases_dir: Optional[Union[str, Path]] = None,
        skip_findings_save: bool = True,
    ) -> str:
        raise RuntimeError("EP-001: 模拟 renderer 失败")


class _OkPreflight:
    """parse() 返回 mock ParsedInput 的 stub。"""

    def parse(
        self,
        input_md_path: Union[str, Path],
        cases_index_path: Optional[Union[str, Path]] = None,
    ) -> ParsedInput:
        return _make_mock_parsed()


def _make_adapters_with_failing_renderer() -> PipelineAdapters:
    return PipelineAdapters(
        preflight=_OkPreflight(),
        renderer=_FailingRenderer(),
        feedback=None,
    )


@pytest.mark.parametrize("input_path", ["cases/C-TEST-EP-001/input.md"])
def test_ep001_tolerant_renderer_failure_only_warns(
    input_path: str, tmp_path: Path
) -> None:
    """EP-001-tolerant：renderer 失败时 tolerant 模式仅 warning，不抛异常。"""
    adapters = _make_adapters_with_failing_renderer()

    with (
        patch(
            "engine.application.pipeline_runner.run_pipeline",
            return_value=_make_mock_output(),
        ),
        patch(
            "engine.application.pipeline_runner._save_findings",
            return_value=tmp_path,
        ),
        patch(
            "engine.application.pipeline_runner.PipelineTiming.write_to",
        ),
    ):
        # tolerant 模式：不应抛出任何异常
        output, timing = run_pipeline_e2e(
            input_path,
            do_render=True,
            adapters=adapters,
            error_policy="tolerant",
        )
    # 正常返回 output
    assert output is not None


@pytest.mark.parametrize("input_path", ["cases/C-TEST-EP-001/input.md"])
def test_ep001_strict_renderer_failure_raises(
    input_path: str, tmp_path: Path
) -> None:
    """EP-001-strict：renderer 失败时 strict 模式直接抛出异常。"""
    adapters = _make_adapters_with_failing_renderer()

    with (
        patch(
            "engine.application.pipeline_runner.run_pipeline",
            return_value=_make_mock_output(),
        ),
        patch(
            "engine.application.pipeline_runner._save_findings",
            return_value=tmp_path,
        ),
        patch(
            "engine.application.pipeline_runner.PipelineTiming.write_to",
        ),
        pytest.raises(RuntimeError, match="EP-001"),
    ):
        run_pipeline_e2e(
            input_path,
            do_render=True,
            adapters=adapters,
            error_policy="strict",
        )


# ---------------------------------------------------------------------------
# EP-002 · findings 落盘失败
# ---------------------------------------------------------------------------

class _OkRenderer:
    def render(self, output, *, template_name, variant, cases_dir=None, skip_findings_save=True) -> str:
        return "# mock report"


def _make_adapters_ok_renderer() -> PipelineAdapters:
    return PipelineAdapters(
        preflight=_OkPreflight(),
        renderer=_OkRenderer(),
        feedback=None,
    )


@pytest.mark.parametrize("input_path", ["cases/C-TEST-EP-002/input.md"])
def test_ep002_tolerant_findings_failure_only_warns(
    input_path: str, tmp_path: Path
) -> None:
    """EP-002-tolerant：findings 落盘失败时 tolerant 模式仅 warning，不抛异常。"""
    adapters = _make_adapters_ok_renderer()

    with (
        patch(
            "engine.application.pipeline_runner.run_pipeline",
            return_value=_make_mock_output("C-TEST-EP-002"),
        ),
        patch(
            "engine.application.pipeline_runner._save_findings",
            side_effect=OSError("EP-002: 模拟 findings 落盘失败"),
        ),
    ):
        output, timing = run_pipeline_e2e(
            input_path,
            do_render=True,
            adapters=adapters,
            error_policy="tolerant",
        )
    assert output is not None


@pytest.mark.parametrize("input_path", ["cases/C-TEST-EP-002/input.md"])
def test_ep002_strict_findings_failure_raises(
    input_path: str, tmp_path: Path
) -> None:
    """EP-002-strict：findings 落盘失败时 strict 模式直接抛出异常。"""
    adapters = _make_adapters_ok_renderer()

    with (
        patch(
            "engine.application.pipeline_runner.run_pipeline",
            return_value=_make_mock_output("C-TEST-EP-002"),
        ),
        patch(
            "engine.application.pipeline_runner._save_findings",
            side_effect=OSError("EP-002: 模拟 findings 落盘失败"),
        ),
        pytest.raises(OSError, match="EP-002"),
    ):
        run_pipeline_e2e(
            input_path,
            do_render=True,
            adapters=adapters,
            error_policy="strict",
        )


# ---------------------------------------------------------------------------
# EP-003 · self_iter 失败
# ---------------------------------------------------------------------------

class _FailingFeedback:
    def ingest(self, case_id: str) -> object:
        raise RuntimeError("EP-003: 模拟 self_iter 失败")


def _make_adapters_failing_feedback() -> PipelineAdapters:
    return PipelineAdapters(
        preflight=_OkPreflight(),
        renderer=None,
        feedback=_FailingFeedback(),
    )


@pytest.mark.parametrize("input_path", ["cases/C-TEST-EP-003/input.md"])
def test_ep003_tolerant_self_iter_failure_only_warns(
    input_path: str, tmp_path: Path
) -> None:
    """EP-003-tolerant：self_iter 失败时 tolerant 模式仅 warning，不抛异常。"""
    adapters = _make_adapters_failing_feedback()

    with (
        patch(
            "engine.application.pipeline_runner.run_pipeline",
            return_value=_make_mock_output("C-TEST-EP-003"),
        ),
        patch(
            "engine.application.pipeline_runner._save_findings",
            return_value=tmp_path,
        ),
        patch(
            "engine.application.pipeline_runner.PipelineTiming.write_to",
        ),
    ):
        output, timing = run_pipeline_e2e(
            input_path,
            do_self_iter=True,
            adapters=adapters,
            error_policy="tolerant",
        )
    assert output is not None


@pytest.mark.parametrize("input_path", ["cases/C-TEST-EP-003/input.md"])
def test_ep003_strict_self_iter_failure_raises(
    input_path: str, tmp_path: Path
) -> None:
    """EP-003-strict：self_iter 失败时 strict 模式直接抛出异常。"""
    adapters = _make_adapters_failing_feedback()

    with (
        patch(
            "engine.application.pipeline_runner.run_pipeline",
            return_value=_make_mock_output("C-TEST-EP-003"),
        ),
        patch(
            "engine.application.pipeline_runner._save_findings",
            return_value=tmp_path,
        ),
        patch(
            "engine.application.pipeline_runner.PipelineTiming.write_to",
        ),
        pytest.raises(RuntimeError, match="EP-003"),
    ):
        run_pipeline_e2e(
            input_path,
            do_self_iter=True,
            adapters=adapters,
            error_policy="strict",
        )


# ---------------------------------------------------------------------------
# EP-004 · ProductionAnalysisService 使用 strict → render 失败 → job.status == "failed"
# ---------------------------------------------------------------------------

def test_ep004_production_service_strict_render_failure_marks_job_failed(
    tmp_path: Path,
) -> None:
    """EP-004：ProductionAnalysisService 调用 strict 模式；renderer 失败时
    job 状态应为 'failed'，而非 'completed'。
    """
    from engine.application.production_service import (
        ProductionAnalysisService,
        SubmitAnalysisRequest,
    )
    from engine.infrastructure.analysis_store import SQLiteAnalysisStore

    db_path = tmp_path / "test.db"
    store = SQLiteAnalysisStore(db_path)
    # 将 workspace_root 设为 tmp_path，使路径校验通过
    svc = ProductionAnalysisService(store=store, workspace_root=tmp_path)

    # 构造一个最小 input.md（preflight 会失败，但我们 patch 掉整个 run_pipeline_e2e）
    input_md = tmp_path / "input.md"
    input_md.write_text("# mock input", encoding="utf-8")

    request = SubmitAnalysisRequest(input_path=str(input_md))

    # patch run_pipeline_e2e 使其抛出 RuntimeError（模拟 strict 模式下 render 失败）
    with patch(
        "engine.application.production_service.run_pipeline_e2e",
        side_effect=RuntimeError("EP-004: strict render 失败"),
    ):
        job = svc.submit(request)

    assert job["status"] == "failed", (
        f"EP-004: 期望 job.status='failed'，实际得到 '{job['status']}'"
    )
    assert "EP-004" in job.get("error", ""), (
        f"EP-004: 期望 error 字段包含 'EP-004'，实际得到 '{job.get('error')}'"
    )
