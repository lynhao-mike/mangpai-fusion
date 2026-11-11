"""八字事实包 × 紫微旁证信封 → 三态对账骨架（cross-check/v1）。

    python -m tools.cross_check --bazi chart.json --ziwei envelope.json --out 对账.md
    python -m tools.cross_check --bazi chart.json --ziwei envelope.json \
        --claims bazi_claims.json --verdicts verdicts.json --json

语义判断属于 Agent，本工具不假装自动裁决：未提供 --verdicts 时
每行状态为 unverifiable（待 Agent 裁决）；分歧必须写明理由，禁用骑墙措辞。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridges.ziwei.envelope import ENVELOPE_VERSION, NOT_USABLE_AS, POLICY  # noqa: E402

VALID_STATUS = ("converged", "divergent", "unverifiable")
BANNED = ("各有道理", "尚难定论", "不宜妄断", "难以定论", "机会与挑战并存", "各有优劣", "说不准")


def _load_json(path: str) -> dict | list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_bazi_meta(facts: dict) -> dict:
    pillars = [p.get("ganzhi") for p in facts.get("pillars", []) if isinstance(p, dict)]
    return {
        "chart_id": facts.get("chart_id"),
        "schema_version": facts.get("schema_version"),
        "profile": facts.get("profile"),
        "input": facts.get("input"),
        "pillars": pillars,
        "boundary_warnings": facts.get("boundary_warnings", []),
    }


def build_report(facts: dict, env: dict, claims: list | None = None, verdicts: dict | None = None) -> dict:
    if env.get("envelope") != ENVELOPE_VERSION:
        raise ValueError(f"不是 {ENVELOPE_VERSION} 信封：{env.get('envelope')!r}")
    if env.get("level") == "L1":
        raise ValueError(
            "三态对账只接受 L2 解读文本；L1 结构化盘面请用 tools.ziwei_chart 的断言核验，"
            "并把结果写进 tools.ziwei_appendix"
        )
    missing = set(NOT_USABLE_AS) - set(env.get("not_usable_as", []))
    if missing:
        raise ValueError(f"信封缺 not_usable_as 约束：{sorted(missing)}")

    claims = claims or []
    by_topic = {c["topic"]: c for c in claims if isinstance(c, dict) and c.get("topic")}
    verdicts = verdicts or {}
    ziwei_text = {c["dim"]: c["text"] for c in env.get("claims", [])}

    rows = []
    for dim in env.get("dimensions_available", []):
        b = by_topic.get(dim, {})
        v = verdicts.get(dim, {})
        status = v.get("status", "unverifiable")
        if status not in VALID_STATUS:
            raise ValueError(f"维度 {dim} 的 status 非法：{status!r}；可用 {VALID_STATUS}")
        reason = str(v.get("reason", "")).strip()
        if reason and any(w in reason for w in BANNED):
            raise ValueError(f"维度 {dim} 的裁决理由含骑墙措辞")
        rows.append({
            "topic": dim,
            "bazi_claim": b.get("text"),
            "bazi_source_ref": b.get("source_ref"),
            "bazi_address": b.get("address"),
            "ziwei_claim": ziwei_text.get(dim),
            "ziwei_locator": env.get("locator"),
            "status": status,
            "verdict_reason": reason or "待 Agent 裁决",
        })

    counts = {s: sum(1 for r in rows if r["status"] == s) for s in VALID_STATUS}
    return {
        "report": "cross-check/v1",
        "policy": POLICY,
        "bazi": extract_bazi_meta(facts),
        "ziwei": {
            "source_system": env.get("source_system"),
            "level": env.get("level"),
            "source_kind": env.get("source_kind"),
            "dataset": env.get("dataset"),
            "locator": env.get("locator"),
            "verifiable_by": env.get("verifiable_by"),
            "not_usable_as": env.get("not_usable_as"),
        },
        "case_key": env.get("case_key"),
        "alignment_warnings": env.get("alignment_warnings", []),
        "rows": rows,
        "counts": counts,
    }


def _cell(value, limit: int = 110) -> str:
    if not value:
        return "—"
    s = str(value).replace("\n", " ").replace("|", "\\|").strip()
    return s if len(s) <= limit else s[:limit] + "…"


def render_markdown(rep: dict) -> str:
    b, z = rep["bazi"], rep["ziwei"]
    ds = z.get("dataset") or {}
    lines = [
        "# 紫微旁证对账表 · cross-check/v1",
        "",
        "> 边界：紫微侧为 L2 解读文本（结论层旁证），不构成八字引擎事实，也不作理论 `source_ref`。",
        "> 三态：**收敛 / 分歧 / 不核验**；分歧须由 Agent 站队并写明理由，禁止骑墙和稀泥。",
        "",
        "## 一、契约核对",
        "",
        "| 项 | 八字事实包 | 紫微旁证信封 |",
        "|---|---|---|",
        f"| 标识 | `chart_id={b['chart_id']}` | `{z['source_system']}` / level `{z['level']}` |",
        f"| 契约 | `{b['schema_version']}` | `{ENVELOPE_VERSION}` |",
        f"| 口径 | profile `{json.dumps(b['profile'], ensure_ascii=False)}` | 内容版本 `{ds.get('content_version')}` |",
        f"| 定位 | 四柱 `{' '.join(p or '' for p in b['pillars'])}` | `{z['locator'].get('shard')}` offset `{z['locator'].get('offset')}` |",
        f"| 禁用 | 唯一事实来源 | `{', '.join(z['not_usable_as'])}` |",
        "",
        "## 二、口径警告（不静默对齐）",
        "",
    ]
    for w in rep["alignment_warnings"]:
        lines.append(f"- `{w}`")
    if b.get("boundary_warnings"):
        lines.append(f"- 引擎 `boundary_warnings`：`{json.dumps(b['boundary_warnings'], ensure_ascii=False)}`")
    lines += [
        "",
        "## 三、结论对账",
        "",
        "| 维度 | 八字侧结论（须带 source_ref） | 紫微侧结论（原文摘要） | 状态 | 裁决理由 |",
        "|---|---|---|---|---|",
    ]
    for r in rep["rows"]:
        bazi_cell = _cell(r["bazi_claim"]) if r["bazi_claim"] else "（未填）"
        ziwei_cell = _cell(r["ziwei_claim"]) if r["ziwei_claim"] else "（未取正文）"
        lines.append(
            f"| {r['topic']} | {bazi_cell} | {ziwei_cell} | "
            f"`{r['status']}` | {_cell(r['verdict_reason'], 160)} |"
        )
    c = rep["counts"]
    lines += [
        "",
        "## 四、统计与下一步",
        "",
        f"收敛 {c['converged']} / 分歧 {c['divergent']} / 不核验 {c['unverifiable']}。",
        "",
        "未提供 `--verdicts` 时全部为 `unverifiable`（骨架状态）；请由 Agent 逐维度补裁决，"
        "并把八字侧结论连同盘面地址与理论条目出处写入 `--claims`。",
        "",
        f"数据署名：{ds.get('attribution')}",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="八字事实包与紫微旁证信封的三态对账")
    ap.add_argument("--bazi", required=True, help="engine.cli chart/all 的 --json 输出文件")
    ap.add_argument("--ziwei", required=True, help="tools.ziwei_lookup --json 的信封文件")
    ap.add_argument("--claims", default=None, help="八字侧结论 JSON 数组（topic/text/source_ref/address）")
    ap.add_argument("--verdicts", default=None, help="Agent 裁决 JSON 对象（topic -> status/reason）")
    ap.add_argument("--out", default=None, help="输出 Markdown 文件")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而非 Markdown")
    args = ap.parse_args(argv)

    try:
        rep = build_report(
            _load_json(args.bazi),
            _load_json(args.ziwei),
            _load_json(args.claims) if args.claims else None,
            _load_json(args.verdicts) if args.verdicts else None,
        )
        text = json.dumps(rep, ensure_ascii=False, indent=2) if args.json else render_markdown(rep)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
            print(f"written: {args.out}")
        else:
            print(text, end="")
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
