"""engine/api/facade.py · 无状态事实 SDK。

以 engine.facts 四层确定性底座为唯一入口；不调用 run_pipeline / run_v5。
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Sequence

from engine.facts.chart_facts import ChartInputError, chart_from_pillars, chart_from_solar
from engine.facts.relation_graph import build_relation_graph
from engine.facts.shensha import build_shensha_facts
from engine.facts.strength_facts import build_strength_facts
from engine.facts.structure_check import (
    build_duan_zuogong_candidates,
    check_structures,
    tiyong_view,
)
from engine.facts.types import ChartFacts


def to_jsonable(obj: Any) -> Any:
    """通用 dataclass → JSON 原生类型（dict / list / 标量）。"""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj


def _short_ref(ref: str) -> str:
    """长路径压成 文件名:行号。"""
    if not isinstance(ref, str) or "/" not in ref.replace("\\", "/"):
        return ref
    path, sep, loc = ref.replace("\\", "/").rpartition(":")
    name = path.rsplit("/", 1)[-1]
    return f"{name}:{loc}" if sep else name


def _compact(
    obj: Any,
    *,
    drop_keys: frozenset[str] = frozenset(),
    keep_null_keys: frozenset[str] = frozenset(),
) -> Any:
    """去掉空值、缩短出处，把 analyze_facts 压进 15KB。

    keep_null_keys 里的键即使值为 None 也保留（输出 null），供下游按键取值。
    """
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if key in drop_keys or key in {"raw_excerpt", "method_note", "rule"}:
                continue
            if key == "source_tags" and isinstance(value, (list, tuple)):
                value = [item.get("tag", item) if isinstance(item, dict) else item for item in value]
            if key in {"source_ref", "source_refs"}:
                value = [_short_ref(x) for x in value] if isinstance(value, (list, tuple)) else _short_ref(value)
            if key == "hidden" and isinstance(value, (list, tuple)):
                value = [
                    {"c": h.get("char"), "q": h.get("qi"), "g": h.get("ten_god")}
                    if isinstance(h, dict) else h for h in value
                ]
            if key == "rule_hits" and isinstance(value, (list, tuple)):
                value = [
                    {"e": h.get("effect"), "r": _short_ref(h.get("source_ref", ""))}
                    if isinstance(h, dict) else h for h in value
                ]
            compact = _compact(value, drop_keys=drop_keys, keep_null_keys=keep_null_keys)
            if compact in (None, [], {}) and key not in keep_null_keys:
                continue
            out[key] = compact
        return out
    if isinstance(obj, (list, tuple)):
        return [_compact(item, drop_keys=drop_keys, keep_null_keys=keep_null_keys) for item in obj]
    return obj


def _compact_structures(structures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for spec in structures:
        items = [
            {k: v for k, v in item.items() if k in {"id", "kind", "status", "evidence"} and v not in (None, [])}
            for item in spec.get("items", [])
            if item.get("status") != "unmet"
        ]
        if not items:
            continue
        # ponytail: 只留核对结果；中文名可从 structure_id 还原
        out.append({"structure_id": spec["structure_id"], "items": items})
    return out


def _compact_zuogong(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # ponytail: chars/source_refs/notes 仍不发给 Agent；tiyong 是 zuogong 原子判 target 的输入，必须保留
    keep = ("mode", "relation_kind", "edge_id", "members", "ten_gods",
            "tiyong", "actor", "binzhu", "distance")
    # actor 无方向时为 null，仍保留键，供下游 cand["actor"] 直接取
    return [
        {k: cand.get(k) for k in keep if k == "actor" or cand.get(k) not in (None, [], ())}
        for cand in candidates
    ]


# Agent 视图削掉的字段：全部可由保留字段唯一还原，需要原件时用 `engine.cli all --full`
_AGENT_OMIT_CANDIDATE_KEYS = frozenset({"binzhu", "distance"})
_AGENT_OMIT_EDGE_KEYS = frozenset({"chars", "between"})
_AGENT_OMIT_RELATION_KEYS = frozenset({"nodes"})


def compact_for_agent(payload: dict[str, Any]) -> dict[str, Any]:
    """Agent 视图：把可还原的冗余从事实视图里投影掉，守住 CLI 的 15KB 上下文预算。

    投影掉的字段及还原方式：
    - candidates.binzhu：由 (addr, layer) 唯一决定（chart_facts.binzhu_side 纯函数）
    - candidates.distance：由 members 的柱序差决定
    - relations.nodes：addr → 字，见 chart.pillars[].stem/branch.char
    - relations.edges[].chars / between：由 members 查 chart / 柱序得

    tiyong / actor 不削：前者是 zuogong 原子判 target 的输入，后者要走 null 语义。
    """
    out = dict(payload)
    duan = payload.get("duan_zuogong")
    if isinstance(duan, dict) and isinstance(duan.get("candidates"), list):
        out["duan_zuogong"] = {
            **duan,
            "candidates": [
                {k: v for k, v in cand.items() if k not in _AGENT_OMIT_CANDIDATE_KEYS}
                if isinstance(cand, dict) else cand
                for cand in duan["candidates"]
            ],
        }
    relations = payload.get("relations")
    if isinstance(relations, dict):
        projected = {k: v for k, v in relations.items() if k not in _AGENT_OMIT_RELATION_KEYS}
        if isinstance(relations.get("edges"), list):
            projected["edges"] = [
                {k: v for k, v in edge.items() if k not in _AGENT_OMIT_EDGE_KEYS}
                if isinstance(edge, dict) else edge
                for edge in relations["edges"]
            ]
        out["relations"] = projected
    return out


def _parse_dt(value: str) -> datetime:
    text = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ChartInputError(f"无法解析出生时间：{value!r}") from exc
    if dt.tzinfo is not None:
        raise ChartInputError("dt 必须是已校正的无时区 datetime")
    return dt


def _parse_pillars(pillars: Sequence[str] | str) -> list[str]:
    if isinstance(pillars, str):
        parts = pillars.split()
    else:
        parts = [str(p).strip() for p in pillars]
        if len(parts) == 1 and " " in parts[0]:
            parts = parts[0].split()
    return parts


def build_chart(
    birth_dt: str | None = None,
    pillars: Sequence[str] | None = None,
    gender: str = "乾",
    dayun: Sequence[str] | None = None,
    birth_year: int | None = None,
) -> ChartFacts:
    """公历时刻或四柱 → ChartFacts。二者必须且只能提供一个。"""
    if (birth_dt is None) == (pillars is None):
        raise ChartInputError("必须且只能提供 birth_dt 或 pillars 之一")
    if birth_dt is not None:
        if dayun is not None:
            raise ChartInputError("公历排盘不接受外部 dayun，由起运推算")
        return chart_from_solar(_parse_dt(birth_dt), gender)
    return chart_from_pillars(
        _parse_pillars(pillars),  # type: ignore[arg-type]
        gender,
        dayun=dayun,
        dayun_start_year=birth_year,
    )


def analyze_facts(
    birth_dt: str | None = None,
    pillars: Sequence[str] | None = None,
    gender: str = "乾",
    dayun: Sequence[str] | None = None,
    birth_year: int | None = None,
    dayun_index: int | None = None,
    liunian_year: int | None = None,
) -> dict[str, Any]:
    """一次性组装四层事实 + 神煞 + 子平八格 + 段派做功候选。"""
    chart = build_chart(birth_dt, pillars, gender, dayun, birth_year)
    graph = build_relation_graph(chart, dayun_index=dayun_index, liunian_year=liunian_year)
    strength = build_strength_facts(chart)
    payload = {
        "chart": to_jsonable(chart),
        "relations": to_jsonable(graph),
        "strength": to_jsonable(strength),
        "shensha": to_jsonable(build_shensha_facts(chart)),
        "structures": _compact_structures(to_jsonable(check_structures(chart, graph, strength))),
        "duan_zuogong": {
            "tiyong": tiyong_view(chart),
            "candidates": _compact_zuogong(to_jsonable(build_duan_zuogong_candidates(chart, graph))),
        },
    }
    # ponytail: 顶层 chart 已含 profile / chart_id；pair_index 可由 edges 还原
    cycles = payload["chart"].get("cycles") or {}
    if isinstance(cycles.get("dayun"), list):
        cycles["dayun"] = cycles["dayun"][:8]
    for key in ("profile", "schema_version", "chart_id", "pair_index"):
        payload["relations"].pop(key, None)
        payload["strength"].pop(key, None)
    payload["chart"].pop("schema_version", None)
    return _compact(payload, keep_null_keys=frozenset({"actor"}))


__all__ = ["analyze_facts", "build_chart", "compact_for_agent", "to_jsonable"]
