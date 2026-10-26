"""tools/claim_condition_report.py · 断语条件化试点验收（契约 23 §八）。

用法：
    python -m tools.claim_condition_report

做的事：
1. 读 theory/claims/conditions-v2/pilot-20.yaml（20 条真实断语）
2. 逐条编译（compiled / needs_human / uncompilable / reference_only）
3. 在 20 张真实命盘上求值
4. 输出可复现的 JSON + Markdown 报告（META/claim-condition-pilot-v1.*）

只读事实层，不写生产规则、不改权重与路由。
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import Counter
from typing import Any

import yaml

from engine.api import analyze_facts, to_jsonable
from engine.claims.condition_ir import ATOMS, build_context, compile_claim, evaluate_claim

ROOT = pathlib.Path(__file__).resolve().parents[1]
PILOT = ROOT / "theory" / "claims" / "conditions-v2" / "pilot-20.yaml"
OUT_JSON = ROOT / "META" / "claim-condition-pilot-v1.json"
OUT_MD = ROOT / "META" / "claim-condition-pilot-v1.md"
PANEL_SIZE = 20

CASE_RE = re.compile(r"^(C-\d{4}-\d{3})-(乾|坤)-((?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4})$")


def load_claims() -> list[dict]:
    data = yaml.safe_load(PILOT.read_text(encoding="utf-8"))
    return data["claims"]


def pick_panel(limit: int = PANEL_SIZE) -> list[dict[str, Any]]:
    cases = []
    for p in sorted((ROOT / "cases").iterdir()):
        m = CASE_RE.match(p.name)
        if not m:
            continue
        pillars = [m.group(3)[i:i + 2] for i in range(0, 8, 2)]
        cases.append({"case": p.name, "gender": m.group(2), "pillars": pillars})
    if not cases:
        raise SystemExit("cases/ 下没有可解析的命盘")
    step = max(1, len(cases) // limit)
    panel = cases[::step][:limit]
    out = []
    for c in panel:
        try:
            facts = to_jsonable(analyze_facts(pillars=c["pillars"], gender=c["gender"]))
        except Exception as exc:  # noqa: BLE001 - 单盘失败不应中断整批
            print(f"skip {c['case']}: {exc}", file=sys.stderr)
            continue
        out.append({**c, "ctx": build_context(facts)})
    return out


def anchor_check(claim: dict) -> dict:
    ref = claim.get("source_ref") or {}
    path = ROOT / str(ref.get("path", ""))
    line_no = ref.get("line") or 0
    if not path.exists():
        return {"ok": False, "reason": "源文件不存在"}
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not 1 <= line_no <= len(lines):
        return {"ok": False, "reason": "行号越界"}

    found = next((i + 1 for i, l in enumerate(lines) if claim["id"] in l), None)
    if found is None:
        probe = (claim.get("source_quote") or "")[:12]
        lo, hi = max(0, line_no - 7), min(len(lines), line_no + 6)
        if probe:
            found = next((i + 1 for i in range(lo, hi) if probe in lines[i]), None)
    if found is None:
        return {"ok": False, "reason": "文件内找不到 rule_id 或引文",
                "line_text": lines[line_no - 1][:60]}
    return {"ok": True, "match": "rule_id" if claim["id"] in lines[found - 1] else "quote",
            "declared": line_no, "found": found, "drift": abs(found - line_no)}


def run() -> dict:
    claims = load_claims()
    panel = pick_panel()
    compiled = []
    compiles = []
    for c in claims:
        r = compile_claim(c)
        compiles.append(r)
        if r["status"] == "compiled":
            compiled.append(c)

    results: list[dict] = []
    for claim in compiled:
        per_chart = []
        for chart in panel:
            ev = evaluate_claim(claim, chart["ctx"])
            per_chart.append({"case": chart["case"], **ev})
        results.append({"claim_id": claim["id"], "school": claim["school"],
                        "domain": claim["domain"], "per_chart": per_chart})

    pairs = [(r, p) for r in results for p in r["per_chart"]]
    total_pairs = len(pairs)
    decided = [p for _, p in pairs if p["value"] is not None]
    unknown = [p for _, p in pairs if p["value"] is None]
    bound = [r for r in results if any(p["bindings"] for p in r["per_chart"])]
    fired = {r["claim_id"]: sum(1 for p in r["per_chart"] if p["state"] == "candidate") for r in results}
    states = Counter(p["state"] for _, p in pairs)

    signatures = Counter()
    for chart in panel:
        sig = []
        for r in results:
            v = next(p["value"] for p in r["per_chart"] if p["case"] == chart["case"])
            sig.append("T" if v is True else "F" if v is False else "U")
        signatures["".join(sig)] += 1

    unmapped = [c["id"] for c in compiled if (c.get("conditions_v2") or {}).get("unmapped_prose")]
    anchors = [{"id": c["id"], **anchor_check(c)} for c in claims]

    metrics = {
        "claims_total": len(claims),
        "compile_states": dict(Counter(r["status"] for r in compiles)),
        "compiled_claims": [c["id"] for c in compiled],
        "panel_size": len(panel),
        "evaluable_rate": round(len(decided) / total_pairs, 4) if total_pairs else 0.0,
        "address_binding_rate": round(len(bound) / len(compiled), 4) if compiled else 0.0,
        "distinct_pass_sets": len(signatures),
        "pass_set_distribution": dict(signatures),
        "fire_rate": {k: round(v / len(panel), 4) for k, v in fired.items()},
        "state_distribution": dict(states),
        "unknown_rate": round(len(unknown) / total_pairs, 4) if total_pairs else 0.0,
        "unknown_explicit_rate": round(
            sum(1 for p in unknown if p["unknown_facts"]) / len(unknown), 4) if unknown else 1.0,
        "unmapped_prose_claims": unmapped,
        "unmapped_rate": round(len(unmapped) / len(compiled), 4) if compiled else 0.0,
        "anchor_ok_rate": round(sum(1 for a in anchors if a["ok"]) / len(anchors), 4),
        "anchor_exact_rate": round(
            sum(1 for a in anchors if a["ok"] and a.get("drift") == 0) / len(anchors), 4),
        "anchor_failures": [a for a in anchors if not a["ok"]],
        "outlier_claims": [k for k, v in fired.items() if v == 0 or v / len(panel) >= 0.6],
        "atom_count": len(ATOMS),
    }

    payload = {
        "schema": "claim-condition-pilot/v1",
        "generated_at": "2026-10-26",
        "pilot": str(PILOT.relative_to(ROOT)),
        "metrics": metrics,
        "compiles": compiles,
        "claims": results,
        "panel": [{"case": c["case"], "pillars": c["pillars"], "gender": c["gender"]} for c in panel],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_MD.write_text(render_md(payload), encoding="utf-8")
    return payload


def render_md(payload: dict) -> str:
    m = payload["metrics"]
    lines = [
        "# 断语条件化试点报告 v1（pilot-20）",
        "",
        "> 自动生成，勿手改。复现：`python -m tools.claim_condition_report`。",
        f"> 数据：`{payload['pilot']}`；落盘：`META/claim-condition-pilot-v1.json`。",
        "",
        "## 一、结论概览",
        "",
        "| 指标 | 值 | 说明 |",
        "|---|---|---|",
        f"| 断语总数 | {m['claims_total']} | 20 条真实断语 |",
        f"| 编译状态 | {m['compile_states']} | compiled / needs_human / uncompilable / reference_only |",
        f"| 可求值率 | {m['evaluable_rate']} | 已编译断语在面板上给出真/假的比例 |",
        f"| 地址绑定率 | {m['address_binding_rate']} | 至少绑定 1 个地址或关系边的断语比例 |",
        f"| 区分度（通过集合种类） | {m['distinct_pass_sets']} / {len(m['compiled_claims'])} 条 | 理论下限 1，越高越能区分 |",
        f"| 未知率 | {m['unknown_rate']} | 求值为 unknown 的断语×盘 比例 |",
        f"| 未知显性率 | {m['unknown_explicit_rate']} | unknown 是否带原因（契约要求 100%） |",
        f"| 部分编译率 | {m['unmapped_rate']} | 自报 `unmapped_prose` 非空的比例 |",
        f"| 锚点通过率 | {m['anchor_ok_rate']} | 文件内能找到 rule_id 或引文 |",
        f"| 锚点精确率 | {m['anchor_exact_rate']} | 声明的行号与真实行号完全一致 |",
        f"| 原子表规模 | {m['atom_count']} | 契约 23 §四 |",
        "",
        "## 二、异常项（开火率 0 或 ≥60%）",
        "",
        "> 开火率 0 ＝ 条件过严或绑定失效；开火率 ≥60% ＝ 条件过宽（多半漏了限制条件）。这两类必须人工复核。",
        "",
        "| 断语 | 开火率 | 判读 |",
        "|---|---:|---|",
    ]
    for cid in m["outlier_claims"]:
        rate = m["fire_rate"][cid]
        verdict = "过严 / 绑定失效" if rate == 0 else "过宽 / 漏限制条件"
        lines.append(f"| {cid} | {rate} | {verdict} |")
    lines += [
        "",
        "## 三、每条已编译断语的开火率",
        "",
        "| 断语 | 流派 | 域 | 开火率 |",
        "|---|---|---|---:|",
    ]
    for r in payload["claims"]:
        rate = m["fire_rate"].get(r["claim_id"], 0)
        lines.append(f"| {r['claim_id']} | {r['school']} | {r['domain']} | {rate} |")
    if m["anchor_failures"]:
        lines += ["", "## 三、锚点未通过", "", "| 断语 | 原因 | 行文本 |", "|---|---|---|"]
        for a in m["anchor_failures"]:
            lines.append(f"| {a['id']} | {a.get('reason', '')} | {a.get('line_text', '')} |")
    lines += [
        "",
        "## 四、口径与限制",
        "",
        "- 语义支持率为**机械代理**（锚点 + 自报未编译残余），不等于人工语义复核；契约要求的人工抽样 ≥90% 尚未执行。",
        "- 「旺」用计数阈值代理（如食伤 ≥3），阈值是设计取值，非原文数值，需命理师复核。",
        "- 最小对比对（正例/反例盘）尚未构造，5 条指标里最容易掩盖「条件写反 / 半截编译」的那条仍缺。",
        "- 面板取自 cases/ 的 20 张真实盘，只用于区分度，不用于准确率。",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    p = run()
    m = p["metrics"]
    print(json.dumps(m, ensure_ascii=False, indent=1))
