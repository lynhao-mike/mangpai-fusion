from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

INPUT_FILE = Path("theory/_ir/unified_rule_ir.yaml")

# 语义对立词对（寒热燥湿扶抑生克）
SEMANTIC_OPPOSITES = [
    {"cold": ["寒", "冷", "冬", "水", "金"], "hot": ["热", "暖", "夏", "火", "炎"]},
    {"dry": ["燥", "干", "土"], "wet": ["湿", "润", "水"]},
    {"support": ["扶", "助", "生", "护"], "suppress": ["抑", "克", "制", "泄"]},
    {"strong": ["旺", "强", "有力"], "weak": ["弱", "衰", "无力"]},
]

# 五行生克关系
ELEMENT_CYCLE = {
    "wood": {"generates": "fire", "controls": "earth", "controlled_by": "metal", "generated_by": "water"},
    "fire": {"generates": "earth", "controls": "metal", "controlled_by": "water", "generated_by": "wood"},
    "earth": {"generates": "metal", "controls": "water", "controlled_by": "wood", "generated_by": "fire"},
    "metal": {"generates": "water", "controls": "wood", "controlled_by": "fire", "generated_by": "earth"},
    "water": {"generates": "wood", "controls": "fire", "controlled_by": "earth", "generated_by": "metal"},
}


def load_ir() -> list[dict[str, Any]]:
    data = yaml.safe_load(INPUT_FILE.read_text(encoding="utf-8"))
    return data["rules"]


def get_tag_set(rule: dict[str, Any]) -> set[str]:
    tags = rule.get("semantic_tags", [])
    return {tag.lower() for tag in tags if isinstance(tag, str)}


def get_domain_set(rule: dict[str, Any]) -> set[str]:
    domains = rule.get("domain", [])
    return {d for d in domains if isinstance(d, str)}


def get_element_profile(rule: dict[str, Any]) -> dict[str, int]:
    return rule.get("element_vector", {})


def statement_text(rule: dict[str, Any]) -> str:
    return str(rule.get("statement", "")).lower()


def check_semantic_opposition(rule_a: dict[str, Any], rule_b: dict[str, Any]) -> tuple[bool, str]:
    """检测语义对立：寒/热、燥/湿、扶/抑"""
    text_a = statement_text(rule_a)
    text_b = statement_text(rule_b)
    for pair in SEMANTIC_OPPOSITES:
        keys = list(pair.keys())
        if len(keys) != 2:
            continue
        k1, k2 = keys[0], keys[1]
        words1, words2 = pair[k1], pair[k2]
        has_a_k1 = any(w in text_a for w in words1)
        has_a_k2 = any(w in text_a for w in words2)
        has_b_k1 = any(w in text_b for w in words1)
        has_b_k2 = any(w in text_b for w in words2)
        if (has_a_k1 and has_b_k2) or (has_a_k2 and has_b_k1):
            return True, f"semantic_opposition:{k1}_vs_{k2}"
    return False, ""


def check_element_conflict(rule_a: dict[str, Any], rule_b: dict[str, Any]) -> tuple[bool, str]:
    """检测五行方向冲突（生克制化）"""
    elem_a = get_element_profile(rule_a)
    elem_b = get_element_profile(rule_b)
    active_a = [e for e, v in elem_a.items() if v == 1]
    active_b = [e for e, v in elem_b.items() if v == 1]
    if not active_a or not active_b:
        return False, ""
    for ea in active_a:
        for eb in active_b:
            if ea == eb:
                continue
            rel_a = ELEMENT_CYCLE.get(ea, {})
            if eb == rel_a.get("controls"):
                return True, f"element_conflict:{ea}_controls_{eb}"
            if eb == rel_a.get("controlled_by"):
                return True, f"element_conflict:{ea}_controlled_by_{eb}"
    return False, ""


def check_domain_conflict(rule_a: dict[str, Any], rule_b: dict[str, Any]) -> tuple[bool, str]:
    """检测功能域结论冲突"""
    domains_a = get_domain_set(rule_a)
    domains_b = get_domain_set(rule_b)
    overlap = domains_a & domains_b
    if not overlap:
        return False, ""
    text_a = statement_text(rule_a)
    text_b = statement_text(rule_b)
    conflict_markers = [
        (["吉", "利", "好", "顺", "成", "富", "贵"], ["凶", "害", "差", "阻", "败", "穷", "贱"]),
        (["旺", "强", "有力"], ["弱", "衰", "无力"]),
    ]
    for positive, negative in conflict_markers:
        a_pos = any(m in text_a for m in positive)
        a_neg = any(m in text_a for m in negative)
        b_pos = any(m in text_b for m in positive)
        b_neg = any(m in text_b for m in negative)
        if (a_pos and b_neg) or (a_neg and b_pos):
            return True, f"domain_conclusion_conflict:{','.join(overlap)}"
    return False, ""


def check_support(rule_a: dict[str, Any], rule_b: dict[str, Any]) -> tuple[bool, str]:
    """检测支持/增强关系"""
    domains_a = get_domain_set(rule_a)
    domains_b = get_domain_set(rule_b)
    overlap = domains_a & domains_b
    if not overlap:
        return False, ""
    text_a = statement_text(rule_a)
    text_b = statement_text(rule_b)
    support_markers = ["吉", "利", "好", "顺", "成", "富", "贵", "旺", "强"]
    a_support = sum(1 for m in support_markers if m in text_a)
    b_support = sum(1 for m in support_markers if m in text_b)
    if a_support >= 2 and b_support >= 2:
        return True, f"support:{','.join(overlap)}_共同正向"
    harm_markers = ["凶", "害", "差", "阻", "败", "穷", "贱", "弱", "衰"]
    a_harm = sum(1 for m in harm_markers if m in text_a)
    b_harm = sum(1 for m in harm_markers if m in text_b)
    if a_harm >= 2 and b_harm >= 2:
        return True, f"support:{','.join(overlap)}_共同负向"
    return False, ""


def check_cross_theory_equivalence(rule_a: dict[str, Any], rule_b: dict[str, Any]) -> tuple[bool, str]:
    """检测跨流派等价（不同派系描述同一结构）"""
    if rule_a["theory_id"] == rule_b["theory_id"]:
        return False, ""
    tags_a = get_tag_set(rule_a)
    tags_b = get_tag_set(rule_b)
    tag_overlap = tags_a & tags_b
    if len(tag_overlap) < 2:
        return False, ""
    domains_a = get_domain_set(rule_a)
    domains_b = get_domain_set(rule_b)
    domain_overlap = domains_a & domains_b
    if not domain_overlap:
        return False, ""
    elem_a = get_element_profile(rule_a)
    elem_b = get_element_profile(rule_b)
    elem_match = sum(1 for e in ["wood", "fire", "earth", "metal", "water"] if elem_a.get(e) == elem_b.get(e) and elem_a.get(e) == 1)
    if elem_match >= 2:
        return True, f"cross_theory_equivalence:tag_overlap={len(tag_overlap)},elem_match={elem_match}"
    return False, ""


def check_conditional_dependency(rule_a: dict[str, Any], rule_b: dict[str, Any]) -> tuple[bool, str]:
    """检测条件依赖（A 的触发条件可能依赖 B 的结论）"""
    text_a = statement_text(rule_a)
    text_b = statement_text(rule_b)
    condition_markers = ["当", "若", "如果", "条件", "需", "要", "时", "前提"]
    a_has_condition = any(m in text_a for m in condition_markers)
    if not a_has_condition:
        return False, ""
    domains_b = get_domain_set(rule_b)
    if not domains_b:
        return False, ""
    if any(d in text_a for d in domains_b):
        return True, f"conditional_dependency:rule_a_may_depend_on_{','.join(domains_b)}"
    return False, ""


def check_override(rule_a: dict[str, Any], rule_b: dict[str, Any]) -> tuple[bool, str]:
    """检测覆盖/优先级（特殊格局覆盖普通规则）"""
    text_a = statement_text(rule_a)
    text_b = statement_text(rule_b)
    special_markers = ["特殊", "专旺", "从格", "化格", "例外", "优先", "覆盖"]
    general_markers = ["普通", "一般", "通常", "常规"]
    a_special = any(m in text_a for m in special_markers)
    b_general = any(m in text_b for m in general_markers)
    if a_special and b_general:
        domains_a = get_domain_set(rule_a)
        domains_b = get_domain_set(rule_b)
        if domains_a & domains_b:
            return True, "override:special_overrides_general"
    return False, ""


def build_edges(rules: list[dict[str, Any]], *, max_pairs: int = 50000) -> list[dict[str, Any]]:
    """构建边（限制最大对数防止爆炸）"""
    edges: list[dict[str, Any]] = []
    n = len(rules)
    pairs_checked = 0
    for i in range(n):
        for j in range(i + 1, n):
            if pairs_checked >= max_pairs:
                break
            pairs_checked += 1
            rule_a = rules[i]
            rule_b = rules[j]
            rid_a = rule_a["rule_id"]
            rid_b = rule_b["rule_id"]
            checks = [
                ("conflict", check_semantic_opposition),
                ("conflict", check_element_conflict),
                ("conflict", check_domain_conflict),
                ("support", check_support),
                ("cross_theory_equivalence", check_cross_theory_equivalence),
                ("conditional_dependency", check_conditional_dependency),
                ("override", check_override),
            ]
            for edge_type, check_fn in checks:
                is_related, reason = check_fn(rule_a, rule_b)
                if is_related:
                    weight = 0.8 if "conflict" in edge_type else 0.6
                    edges.append({
                        "from": rid_a,
                        "to": rid_b,
                        "type": edge_type,
                        "weight": weight,
                        "reason": reason,
                    })
        if pairs_checked >= max_pairs:
            break
    return edges


def compute_metrics(rules: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    """计算图谱指标"""
    total_nodes = len(rules)
    total_edges = len(edges)
    edge_type_counter = Counter(e["type"] for e in edges)
    conflict_count = edge_type_counter.get("conflict", 0)
    conflict_ratio = round(conflict_count / total_edges, 4) if total_edges else 0.0
    theory_pairs = set()
    cross_theory_edges = 0
    for e in edges:
        from_rule = next((r for r in rules if r["rule_id"] == e["from"]), None)
        to_rule = next((r for r in rules if r["rule_id"] == e["to"]), None)
        if from_rule and to_rule:
            t1 = from_rule["theory_id"]
            t2 = to_rule["theory_id"]
            if t1 != t2:
                cross_theory_edges += 1
                theory_pairs.add(tuple(sorted([t1, t2])))
    cross_theory_ratio = round(cross_theory_edges / total_edges, 4) if total_edges else 0.0
    node_edge_count: Counter[str] = Counter()
    for e in edges:
        node_edge_count[e["from"]] += 1
        node_edge_count[e["to"]] += 1
    isolated_nodes = [r["rule_id"] for r in rules if node_edge_count[r["rule_id"]] == 0]
    high_conflict_nodes = [
        {"rule_id": rid, "edge_count": count}
        for rid, count in node_edge_count.most_common(20)
        if count >= 5
    ]
    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "edge_type_distribution": dict(edge_type_counter),
        "conflict_ratio": conflict_ratio,
        "cross_theory_edges": cross_theory_edges,
        "cross_theory_edges_ratio": cross_theory_ratio,
        "unique_theory_pairs": len(theory_pairs),
        "isolated_nodes_count": len(isolated_nodes),
        "isolated_nodes_sample": isolated_nodes[:10],
        "high_conflict_nodes": high_conflict_nodes,
    }


def main() -> None:
    rules = load_ir()
    print(f"加载 {len(rules)} 条规则")
    edges = build_edges(rules, max_pairs=50000)
    print(f"生成 {len(edges)} 条边")
    metrics = compute_metrics(rules, edges)
    print(f"图谱指标计算完成")
    out_dir = Path("theory/_ir")
    graph_data = {
        "schema_version": "RuleGraph-2026-06-13",
        "nodes": [{"rule_id": r["rule_id"], "theory_id": r["theory_id"]} for r in rules],
        "edges": edges,
    }
    (out_dir / "rule_graph.yaml").write_text(
        yaml.safe_dump(graph_data, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    (out_dir / "graph_metrics.yaml").write_text(
        yaml.safe_dump({"schema_version": "GraphMetrics-2026-06-13", **metrics}, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    print("Generated theory/_ir/rule_graph.yaml")
    print("Generated theory/_ir/graph_metrics.yaml")


if __name__ == "__main__":
    main()
