from dataclasses import FrozenInstanceError
import inspect

import pytest

from engine.asof.natal_capacity import (
    CapacityNode,
    EvidenceRef,
    PathRef,
    SourceCitation,
    build_natal_capacity_graph,
)


CASE_ID = "C-2026-028-乾-壬戌癸卯壬子乙巳"


def _inputs() -> dict[str, object]:
    officer = EvidenceRef(
        source=f"cases/{CASE_ID}/input.md",
        locator="藏干.年支[戊]",
        excerpt="戊/七杀",
    )
    output = EvidenceRef(
        source=f"cases/{CASE_ID}/input.md",
        locator="四柱.时柱",
        excerpt="乙巳/伤官",
    )
    node = CapacityNode("career-authority", "career_authority", (officer,))
    path = PathRef("organization-responsibility", "responsibility_growth", (node.node_id,), (officer, output))
    citation = SourceCitation(
        "sources/gao/2018弟子班_大运流年篇_55页.md",
        139,
        "后天组合原局无根源，力量很小",
    )
    return {
        "case_id": CASE_ID,
        "capacity_nodes": (node,),
        "structural_features": (officer, output),
        "vulnerabilities": (output,),
        "feasible_paths": (path,),
        "constraints": (officer,),
        "chart_evidence": (officer, output),
        "source_citations": (citation,),
        "competing_explanations": ("输出结构也可能表现为教学而非行政权责",),
        "counter_evidence": (output,),
    }


def test_same_inputs_produce_field_equal_immutable_graphs() -> None:
    first = build_natal_capacity_graph(**_inputs())  # type: ignore[arg-type]
    second = build_natal_capacity_graph(**_inputs())  # type: ignore[arg-type]
    assert first == second
    assert first.capacity_nodes == second.capacity_nodes
    assert first.feasible_paths == second.feasible_paths
    assert isinstance(first.capacity_nodes, tuple)
    assert isinstance(first.chart_evidence, tuple)
    with pytest.raises(FrozenInstanceError):
        first.domain = "wealth"  # type: ignore[misc]


def test_every_enabled_business_field_is_traceable() -> None:
    graph = build_natal_capacity_graph(**_inputs())  # type: ignore[arg-type]
    assert graph.domain == "career"
    assert all(node.chart_evidence for node in graph.capacity_nodes)
    assert all(path.evidence and path.node_ids for path in graph.feasible_paths)
    assert graph.structural_features
    assert graph.vulnerabilities
    assert graph.constraints
    assert graph.chart_evidence
    assert all(ref.source and ref.locator and ref.excerpt for ref in graph.chart_evidence)
    assert all(c.source_path and c.line > 0 and c.excerpt for c in graph.source_citations)
    assert graph.competing_explanations
    assert graph.counter_evidence


def test_path_cannot_reference_an_unknown_natal_node() -> None:
    values = _inputs()
    evidence = values["chart_evidence"][0]  # type: ignore[index]
    values["feasible_paths"] = (PathRef("bad", "responsibility_growth", ("missing",), (evidence,)),)
    with pytest.raises(ValueError, match="existing natal node"):
        build_natal_capacity_graph(**values)  # type: ignore[arg-type]


def test_builder_surface_cannot_receive_reality_or_scores() -> None:
    names = set(inspect.signature(build_natal_capacity_graph).parameters)
    forbidden = {"known_facts", "events", "event_outcome", "confidence", "score", "weight", "completion_mode"}
    assert names.isdisjoint(forbidden)
