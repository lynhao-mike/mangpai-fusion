"""Default infrastructure adapters for the application pipeline ports.

These adapters keep existing tool behavior while moving default wiring out of
``tools/`` so application use cases no longer depend on CLI modules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from engine.application.ports import (
    FeedbackIngestPort,
    PipelineAdapters,
    PreflightPort,
    ReportRenderPort,
)
from engine.domain.analysis import AnalysisOutput
from engine.predicates.types import ParsedInput, adapt_parsed


class ToolsPreflightAdapter(PreflightPort):
    """Use the existing tools.preflight parser through the InputParser port."""

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
    """Use the existing Markdown report renderer through the ReportRenderer port."""

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
    """Use the existing feedback loop through the FeedbackIngestor port."""

    def ingest(self, case_id: str) -> object:
        from tools.feedback_loop import ingest_feedback

        return ingest_feedback(case_id)


def default_pipeline_adapters() -> PipelineAdapters:
    """Return the default infrastructure adapters for e2e pipeline execution."""
    return PipelineAdapters(
        preflight=ToolsPreflightAdapter(),
        renderer=ToolsReportRenderAdapter(),
        feedback=ToolsFeedbackIngestAdapter(),
    )
