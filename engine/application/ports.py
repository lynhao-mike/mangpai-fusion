"""应用层端到端流水线端口定义。

该模块只定义 application 层需要的抽象能力，避免
engine.application.pipeline_runner 直接依赖 tools.* CLI 实现。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, Union

from engine.domain.analysis import AnalysisOutput
from engine.predicates.types import ParsedInput


class PreflightPort(Protocol):
    """input.md → ParsedInput 的解析端口。"""

    def parse(
        self,
        input_md_path: Union[str, Path],
        cases_index_path: Optional[Union[str, Path]] = None,
    ) -> ParsedInput:
        """解析并返回 engine 标准 ParsedInput。"""


class ReportRenderPort(Protocol):
    """AnalysisOutput → Markdown 报告的渲染端口。"""

    def render(
        self,
        output: AnalysisOutput,
        *,
        template_name: str,
        variant: str,
        cases_dir: Optional[Union[str, Path]] = None,
        skip_findings_save: bool = True,
    ) -> str:
        """渲染报告 Markdown。"""


class FeedbackIngestPort(Protocol):
    """反馈摄入 / 自迭代端口。"""

    def ingest(self, case_id: str) -> object:
        """执行一次反馈摄入。"""


@dataclass(frozen=True)
class PipelineAdapters:
    """run_pipeline_e2e 可注入的外部适配器集合。"""

    preflight: Optional[PreflightPort] = None
    renderer: Optional[ReportRenderPort] = None
    feedback: Optional[FeedbackIngestPort] = None
