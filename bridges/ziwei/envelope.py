"""evidence-envelope/v1：把「旁证不是事实」这条铁律写进数据结构。"""

from __future__ import annotations

from .case_key import CaseKey
from .chart_l1 import chart_fingerprint, summarize_chart

ENVELOPE_VERSION = "evidence-envelope/v1"
NOT_USABLE_AS = ["engine_fact", "theory_source_ref"]
ATTRIBUTION = (
    "紫微斗数开源解读数据集 v4.0（674,976 张命盘 × 13 维） / "
    "https://github.com/Renhuai123/ziwei-doushu / 王多鱼AI"
)

POLICY = (
    "结论层旁证；不得进入 engine.cli 事实层或 tools.query_theory 理论索引；"
    "分歧由 Agent 站队并写明理由，不输出骑墙结论"
)


def build_envelope(case_key: CaseKey, payload: dict, *, config: dict, level: str = "L2") -> dict:
    """由查表器 payload 生成信封。未请求的维度只给字数、不给正文。"""
    if level not in ("L1", "L2"):
        raise ValueError(f"未知 level：{level}（可用 L1 结构化盘面 / L2 解读文本）")

    rec = payload["record"]
    claims = [
        {"dim": dim, "chars": rec["t"].get(dim), "text": text}
        for dim, text in rec["c"].items()
    ]

    return {
        "envelope": ENVELOPE_VERSION,
        "policy": POLICY,
        "case_key": case_key.as_dict(),
        "source_system": "ziwei-doushu",
        "source_kind": "interpretation_text" if level == "L2" else "chart_fact",
        "level": level,
        "dataset": {
            "version": config.get("dataset_version"),
            "content_version": config.get("content_version"),
            "release": f"{config.get('release_repo')}@{config.get('release_tag')}",
            "license": config.get("license"),
            "attribution": config.get("attribution") or ATTRIBUTION,
        },
        "locator": payload["locator"],
        "ziwei_dataset_fields": {
            "minggong_main_star_ms": rec.get("ms"),
            "hour_index": rec.get("h"),
            "gender": rec.get("g"),
            "note": "仅紫微数据集内部字段，在紫微体系内可核对，不构成八字盘面事实",
        },
        "claims": claims,
        "dimensions_available": payload.get("dims_available", []),
        "dimension_chars": rec.get("t", {}),
        "text_chars_total": payload.get("text_chars_total"),
        "alignment_warnings": list(case_key.alignment_warnings),
        "verifiable_by": "ziwei-doushu engine (external system)",
        "not_usable_as": list(NOT_USABLE_AS),
    }


def build_l1_envelope(
    case_key: CaseKey,
    chart: dict,
    assertions: list[dict],
    *,
    config: dict | None = None,
    generator: dict | None = None,
    include_full_chart: bool = False,
) -> dict:
    """L1 结构化盘面信封：紫微体系内核验，但对八字项目仍是旁证。

    与 L2 的关键差别：source_kind=chart_fact、带 verified_within 与断言表；
    not_usable_as 原样保留 —— 外部体系的盘面事实不等于 engine.cli 事实。
    """
    fp = chart_fingerprint(chart)
    gen = dict(generator or {})
    locator = {
        "system": "ziwei-doushu",
        "generator": gen.get("file", "lib/ziwei/algorithm.ts"),
        "function": gen.get("function", "generateChart"),
        "runtime": gen.get("runtime", "node --import tsx"),
        "chart_sha256": fp["sha256"],
        "chart_json_bytes": fp["bytes"],
        "input": gen.get("input", {}),
    }
    matched = sum(1 for a in assertions if a.get("matched") is True)
    failed = sum(1 for a in assertions if a.get("matched") is False)
    unknown = sum(1 for a in assertions if a.get("matched") is None)
    env = {
        "envelope": ENVELOPE_VERSION,
        "policy": POLICY,
        "case_key": case_key.as_dict(),
        "source_system": "ziwei-doushu",
        "source_kind": "chart_fact",
        "level": "L1",
        "verified_within": "ziwei-doushu engine (lib/ziwei/algorithm.ts)",
        "verifiable_by": "ziwei-doushu engine (external system)",
        "dataset": None,
        "generator": {**gen, "license": "MIT (ziwei-doushu code)"},
        "locator": locator,
        "chart_summary": summarize_chart(chart),
        "assertions": assertions,
        "assertion_counts": {"matched": matched, "mismatched": failed, "undetermined": unknown},
        "alignment_warnings": list(case_key.alignment_warnings),
        "not_usable_as": list(NOT_USABLE_AS),
        "attribution": (config or {}).get("attribution") or ATTRIBUTION,
    }
    if include_full_chart:
        env["chart"] = chart
    return env
