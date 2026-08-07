"""事业域原局承载图。

该模块只表达稳定命盘承载，不读取现实履历，不生成事件，也不计算综合分。
所有业务字段必须携带可定位命盘事实；原始语料引用独立保存，供后续双证据门使用。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """可审计证据定位；``locator`` 必须是非空的稳定位置描述。"""

    source: str
    locator: str
    excerpt: str

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.locator.strip() or not self.excerpt.strip():
            raise ValueError("evidence requires source, locator and excerpt")


@dataclass(frozen=True, slots=True)
class SourceCitation:
    """可定位到原始语料的引用。"""

    source_path: str
    line: int
    excerpt: str

    def __post_init__(self) -> None:
        if not self.source_path.strip() or self.line < 1 or not self.excerpt.strip():
            raise ValueError("citation requires path, positive line and excerpt")


@dataclass(frozen=True, slots=True)
class CapacityNode:
    """原局中可稳定定位的领域功能与承载节点。"""

    node_id: str
    function: str
    chart_evidence: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        if not self.node_id.strip() or not self.function.strip() or not self.chart_evidence:
            raise ValueError("capacity node requires identity, function and chart evidence")


@dataclass(frozen=True, slots=True)
class PathRef:
    """原局允许但不保证在现实中兑现的事业路径。"""

    path_id: str
    function: str
    node_ids: tuple[str, ...]
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        if not self.path_id.strip() or not self.function.strip():
            raise ValueError("path requires identity and function")
        if not self.node_ids or not self.evidence:
            raise ValueError("path requires natal nodes and chart evidence")


@dataclass(frozen=True, slots=True)
class NatalCapacityGraph:
    """事业域稳定原局承载；不等于截止日现实状态。"""

    case_id: str
    schema_version: str
    domain: str
    capacity_nodes: tuple[CapacityNode, ...]
    structural_features: tuple[EvidenceRef, ...]
    vulnerabilities: tuple[EvidenceRef, ...]
    feasible_paths: tuple[PathRef, ...]
    constraints: tuple[EvidenceRef, ...]
    chart_evidence: tuple[EvidenceRef, ...]
    source_citations: tuple[SourceCitation, ...]
    competing_explanations: tuple[str, ...]
    counter_evidence: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        if not self.case_id.strip() or self.schema_version != "asof-prototype-v1":
            raise ValueError("invalid case identity or schema version")
        if self.domain != "career":
            raise ValueError("prototype only supports the career domain")
        node_ids = tuple(node.node_id for node in self.capacity_nodes)
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("capacity node ids must be unique")
        if not self.chart_evidence or not self.source_citations:
            raise ValueError("natal graph requires chart and primary-source evidence")
        if any(node_id not in set(node_ids) for path in self.feasible_paths for node_id in path.node_ids):
            raise ValueError("every path must reference an existing natal node")


def build_natal_capacity_graph(
    *,
    case_id: str,
    capacity_nodes: tuple[CapacityNode, ...],
    structural_features: tuple[EvidenceRef, ...],
    vulnerabilities: tuple[EvidenceRef, ...],
    feasible_paths: tuple[PathRef, ...],
    constraints: tuple[EvidenceRef, ...],
    chart_evidence: tuple[EvidenceRef, ...],
    source_citations: tuple[SourceCitation, ...],
    competing_explanations: tuple[str, ...] = (),
    counter_evidence: tuple[EvidenceRef, ...] = (),
) -> NatalCapacityGraph:
    """从调用方已裁定的结构化命盘信号构造确定性、不可变承载图。

    函数不接受 known facts、现实事件、置信度或岁运完成方式，因而这些信息
    无法反向抬升原局根源等级。输入顺序属于冻结证据的一部分，不在此猜测排序。
    """

    return NatalCapacityGraph(
        case_id=case_id,
        schema_version="asof-prototype-v1",
        domain="career",
        capacity_nodes=capacity_nodes,
        structural_features=structural_features,
        vulnerabilities=vulnerabilities,
        feasible_paths=feasible_paths,
        constraints=constraints,
        chart_evidence=chart_evidence,
        source_citations=source_citations,
        competing_explanations=competing_explanations,
        counter_evidence=counter_evidence,
    )
