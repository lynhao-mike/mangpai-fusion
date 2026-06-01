"""tools 层到 engine.application.ports 的默认适配器。

该模块位于 tools/，用于把 CLI/文件工作流实现注入 application 层。
engine.application 不应直接 import 本模块；调用方在需要 e2e 默认行为时显式构造。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from engine.application.ports import FeedbackIngestPort, PipelineAdapters, PreflightPort, ReportRenderPort
from engine.domain.analysis import AnalysisOutput
from engine.predicates.types import ParsedInput, adapt_parsed


class ToolsPreflightAdapter(PreflightPort):
    """使用 tools.preflight.parse 的 input.md 解析适配器。"""

    def parse(
        self,
        input_md_path: Union[str, Path],
        cases_index_path: Optional[Union[str, Path]] = None,
    ) -> ParsedInput:
        from tools.preflight import parse as preflight_parse

        parsed_raw = preflight_parse(
            Path(input_md_path),
            Path(cases_index_path) if cases_index_path else None,
        )
        return adapt_parsed(parsed_raw)


class ToolsReportRenderAdapter(ReportRenderPort):
    """使用 tools.render_report.render_from_output 的报告渲染适配器。"""

    def render(
        self,
        output: AnalysisOutput,
        *,
        template_name: str,
        variant: str,
        cases_dir: Optional[Union[str, Path]] = None,
        skip_findings_save: bool = True,
    ) -> str:
        from tools.render_report import render_from_output

        return render_from_output(
            output,
            template_name=template_name,
            variant=variant,  # type: ignore[arg-type]
            cases_dir=cases_dir,
            skip_findings_save=skip_findings_save,
        )


class ToolsFeedbackIngestAdapter(FeedbackIngestPort):
    """使用 tools.feedback_loop.ingest_feedback 的反馈摄入适配器。"""

    def ingest(self, case_id: str) -> object:
        from tools.feedback_loop import ingest_feedback

        return ingest_feedback(case_id)


def default_pipeline_adapters() -> PipelineAdapters:
    """返回 e2e 流水线默认 tools 适配器集合。"""
    return PipelineAdapters(
        preflight=ToolsPreflightAdapter(),
        renderer=ToolsReportRenderAdapter(),
        feedback=ToolsFeedbackIngestAdapter(),
    )
