"""engine.facts · 盘面事实层（ChartFacts + RelationGraph）。

只输出客观事实、带位置的关系拓扑与带出处的标签；不输出定性结论或分数。
"""
from engine.facts.chart_facts import (
    ChartInputError,
    binzhu_side,
    chart_from_pillars,
    chart_from_solar,
)
from engine.facts.relation_graph import build_relation_graph, edge_by_id, edges_between, muku_at
from engine.facts.strength_facts import build_strength_facts
from engine.facts.types import ChartFacts, ProfileSet, RelationGraph, StrengthFacts

__all__ = [
    "ChartFacts",
    "ChartInputError",
    "ProfileSet",
    "RelationGraph",
    "StrengthFacts",
    "binzhu_side",
    "build_relation_graph",
    "build_strength_facts",
    "chart_from_pillars",
    "chart_from_solar",
    "edge_by_id",
    "edges_between",
    "muku_at",
]
