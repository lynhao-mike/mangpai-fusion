"""独立命理结构轨：原局承载 + 大运上下文 + 截止日前年度作用。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from engine.asof.daiyun_context import DaiyunStage
from engine.asof.event_candidate import AnnualInteractionTrace
from engine.asof.natal_capacity import NatalCapacityGraph


@dataclass(frozen=True, slots=True)
class StructuralTrack:
    """命理理论依据轨；不保存现实事件核验、影响度或人生状态。"""

    case_id: str
    as_of_date: date
    natal_graph: NatalCapacityGraph
    daiyun_stage: DaiyunStage
    annual_traces: tuple[AnnualInteractionTrace, ...]

    def __post_init__(self) -> None:
        if self.case_id != self.natal_graph.case_id:
            raise ValueError("structural track case id must match natal graph")
        if not (self.daiyun_stage.start_date <= self.as_of_date <= self.daiyun_stage.end_date):
            raise ValueError("as_of_date must fall inside the selected daiyun stage")
        if any(trace.year > self.as_of_date.year for trace in self.annual_traces):
            raise ValueError("structural track cannot contain post-cutoff annual traces")


def build_structural_track(
    *,
    case_id: str,
    as_of_date: date,
    natal_graph: NatalCapacityGraph,
    daiyun_stage: DaiyunStage,
    annual_traces: tuple[AnnualInteractionTrace, ...],
) -> StructuralTrack:
    """确定性构造独立结构轨；不会读取或更新现实状态轨。"""

    eligible = tuple(trace for trace in annual_traces if trace.year <= as_of_date.year)
    return StructuralTrack(case_id, as_of_date, natal_graph, daiyun_stage, eligible)
