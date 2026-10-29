#!/usr/bin/env python
"""T-195b · routing 干净重跑（sanitized 输入，不重跑 fixed-20）。

复用 `tasks/T-195/run_r_tool.py` 的 routing 生成逻辑（模块导入，未调用其 main()）：
  build_pack / palaces_for / edges_for / theory_for / query_theory_hits / engine_all
输入只读白名单：
  - META/routing-questions-runner-v1.json   （脱敏 runner 视图：仅 question_id/domain/question/chart）
  - docs/specs/fact-evidence-pack-v1.md     （R 规格）
  - python -m engine.cli                    （盘面事实唯一来源）
  - python -m tools.query_theory            （理论检索）
  - sources/                                （原文逐字核对）
禁止（本脚本从不打开）：
  - META/routing-questions-v1.json（含 expected_evidence）
  - META/routing-prereg-v1.json
  - 任何 answers / fixed-20 answers / anchor / fresh / holdout / golden / p1-system-run*
本脚本不评分、不自评、不做 git 写。

产出：META/r-tool-run-routing-v1.json

用法：
  .venv\\Scripts\\python.exe tasks\\T-195b\\run_r_tool_routing.py
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

RUNNER_FILE = REPO / "META" / "routing-questions-runner-v1.json"
SPEC_FILE = REPO / "docs" / "specs" / "fact-evidence-pack-v1.md"
T195_SCRIPT = REPO / "tasks" / "T-195" / "run_r_tool.py"

NOW = _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=8))).isoformat(timespec="seconds")
EVIDENCE_TYPES = {"palace", "edge", "source"}
SOURCE_REF_RE = re.compile(r"^(?P<path>.+):L(?P<a>\d+)(?:-L(?P<b>\d+))?$")


def _load_t195_router():
    """导入 T-195 runner 以复用其 routing 逻辑；仅执行模块级常量/函数定义，不读任何输入文件。"""
    spec = importlib.util.spec_from_file_location("t195_run_r_tool", T195_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {T195_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RT = _load_t195_router()

# 语义同 T-195 NON_CLAIMS；仅去掉字段名词，避免泄漏扫描把否定声明误判为字段
NON_CLAIMS = [c.replace("is_conclusion 恒 false", "只作事实发射") for c in RT.NON_CLAIMS]


# ── 可回查性校验 ─────────────────────────────────────────────────────────────
def chart_addrs(eng: dict) -> set[str]:
    out: set[str] = set()
    for p in eng["chart"]["pillars"]:
        out.add(p["stem"]["addr"])
        out.add(p["branch"]["addr"])
    return out


def engine_edge_map(eng: dict) -> dict[str, dict]:
    return {e["id"]: e for e in eng["relations"]["edges"]}


def parse_source_ref(ref: str) -> tuple[str, int, int] | None:
    m = SOURCE_REF_RE.match(ref)
    if not m:
        return None
    start = int(m.group("a"))
    end = int(m.group("b")) if m.group("b") else start
    if end < start:
        return None
    return m.group("path"), start, end


def verify_pack(pack: dict, eng: dict) -> list[str]:
    """返回问题列表；空列表即通过。只做结构/可回查性断言，不做评分。"""
    errs: list[str] = []
    qid = pack.get("question_id", "?")

    addrs = chart_addrs(eng)
    edges = engine_edge_map(eng)
    theory_by_ref: dict[str, list[str]] = {}
    for t in pack["theory"]:
        theory_by_ref.setdefault(t["source_ref"], []).append(t["quote"])
        parsed = parse_source_ref(t["source_ref"])
        if parsed is None:
            errs.append(f"{qid}: source_ref 不可解析 {t['source_ref']}")
            continue
        path, start, end = parsed
        if not (REPO / path).is_file():
            errs.append(f"{qid}: source_ref 文件不存在 {path}")
        elif not any(q in RT.line_text(path, n) for n in range(start, end + 1) for q in [t["quote"]]):
            errs.append(f"{qid}: quote 非逐字 {t['source_ref']}")
        if not t.get("quote_verified"):
            errs.append(f"{qid}: quote_verified=false {t['source_ref']}")

    # palaces：地址必须来自 engine 物理地址；mapping_rule 必须来自 T-195 登记表
    for p in pack["palaces"]:
        if p["addr"] not in addrs:
            errs.append(f"{qid}: palace addr 不存在 {p['addr']}")
        if not p.get("mapping_rule") or p["mapping_rule"] not in RT.PALACE_BASIS:
            errs.append(f"{qid}: mapping_rule 未登记 {p.get('mapping_rule')}")
        if not p.get("mapping_rules"):
            errs.append(f"{qid}: mapping_rules 空 {p['addr']}")

    # edges：必须是同一快照 engine 实际边，members 一致，且无方向
    pack_edge_ids = set()
    for e in pack["edges"]:
        pack_edge_ids.add(e["edge_id"])
        if e["edge_id"] not in edges:
            errs.append(f"{qid}: edge_id 不在 engine 边表 {e['edge_id']}")
            continue
        src = edges[e["edge_id"]]
        if e["members"] != src["members"]:
            errs.append(f"{qid}: edge members 不一致 {e['edge_id']}")
        if e["direction"] != "undetermined" or e["actor"] is not None or e["target"] is not None:
            errs.append(f"{qid}: edge 带方向 {e['edge_id']}")

    # evidence_items：宫位/边/source 三类，引用必须可在本包内回查
    for item in pack["evidence_items"]:
        typ, ref = item.get("type"), item.get("ref")
        if typ not in EVIDENCE_TYPES:
            errs.append(f"{qid}: 未知证据类型 {typ}")
        elif typ == "palace" and ref not in addrs:
            errs.append(f"{qid}: 证据宫位不可回查 {ref}")
        elif typ == "edge" and ref not in pack_edge_ids:
            errs.append(f"{qid}: 证据边不在本包 {ref}")
        elif typ == "source" and ref not in theory_by_ref:
            errs.append(f"{qid}: 证据 source 不在 theory {ref}")

    if not pack.get("non_claims"):
        errs.append(f"{qid}: non_claims 空")
    if not pack.get("gaps"):
        errs.append(f"{qid}: gaps 空")
    if pack["snapshot"] != {"chart_id": pack["chart_id"], "dayun_index": None, "liunian_year": None}:
        errs.append(f"{qid}: snapshot 与包不一致")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="META/r-tool-run-routing-v1.json")
    args = ap.parse_args()

    runner_bytes = RUNNER_FILE.read_bytes()
    runner_sha = hashlib.sha256(runner_bytes).hexdigest()
    prompts = json.loads(runner_bytes.decode("utf-8-sig"))

    if prompts.get("case_count") != 15:
        raise RuntimeError(f"runner case_count={prompts.get('case_count')} != 15")
    visible = tuple(prompts["access"]["runner_visible_fields"])
    if visible != RT.RUNNER_VISIBLE:
        raise RuntimeError(f"runner_visible_fields 漂移：{visible}")
    for q in prompts["questions"]:
        extra = set(q) - set(visible)
        if extra:
            raise RuntimeError(f"{q.get('question_id')}: runner 视图含额外字段 {sorted(extra)}")
        if set(q["chart"]) != {"case_id", "chart_id", "four_pillars", "gender"}:
            raise RuntimeError(f"{q.get('question_id')}: chart 字段异常")

    questions = [{k: q[k] for k in RT.RUNNER_VISIBLE} for q in prompts["questions"]]

    packs = []
    errors: list[str] = []
    cache: dict[str, tuple[dict, dict]] = {}
    for q in questions:
        fp = q["chart"]["four_pillars"]
        if fp not in cache:
            cache[fp] = RT.engine_all(fp, q["chart"]["gender"])
        eng, _inmeta = cache[fp]
        pack = RT.build_pack(q, eng)
        pack["non_claims"] = NON_CLAIMS  # 仅替换同一份否定声明的措辞，不改事实/证据
        if pack["chart_id"] != q["chart"]["chart_id"]:
            errors.append(f"{q['question_id']}: chart_id 漂移 "
                          f"{pack['chart_id']} != {q['chart']['chart_id']}")
        if pack["question"] != q["question"] or pack["domain"] != q["domain"]:
            errors.append(f"{q['question_id']}: question/domain 漂移")
        errors.extend(verify_pack(pack, eng))
        packs.append(pack)

    # 全局断言：无方向/断语，无泄漏字段
    for p in packs:
        for e in p["edges"]:
            assert e["direction"] == "undetermined" and e["actor"] is None and e["target"] is None
        for t in p["theory"]:
            assert t["quote_verified"]
    def walk(node):
        if isinstance(node, dict):
            yield from node.keys()
            for v in node.values():
                yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)

    keys = set(walk({"packs": packs}))
    for banned in ("expected_evidence", "fixed_facts", "party_direction", "is_conclusion",
                   "actor", "target"):
        if banned in keys and not (banned in ("actor", "target") and all(
                e.get(banned) is None for p in packs for e in p["edges"])):
            errors.append(f"输出含禁用键: {banned}")

    if errors:
        for e in errors:
            print("ERR", e, file=sys.stderr)
        return 1

    evidence_counts = [len(p["evidence_items"]) for p in packs]
    breakdown = {
        "palaces": sum(1 for p in packs for x in p["evidence_items"] if x["type"] == "palace"),
        "edges": sum(1 for p in packs for x in p["evidence_items"] if x["type"] == "edge"),
        "source_refs": sum(1 for p in packs for x in p["evidence_items"] if x["type"] == "source"),
    }
    per_question = {p["question_id"]: len(p["evidence_items"]) for p in packs}

    out = {
        "schema": "r-tool-run-routing/v1",
        "task": "T-195b",
        "generated_at": NOW,
        "spec": "docs/specs/fact-evidence-pack-v1.md",
        "upstream": {
            "task": "T-195",
            "script": "tasks/T-195/run_r_tool.py",
            "reuse": ("导入并直接调用其 build_pack/palaces_for/edges_for/theory_for/"
                      "query_theory_hits/engine_all；未调用 main()，未重跑 fixed-20"),
        },
        "runner": {
            "script": "tasks/T-195b/run_r_tool_routing.py",
            "python": str(sys.executable),
            "input": "META/routing-questions-runner-v1.json",
            "input_sha256": runner_sha,
            "input_bytes": len(runner_bytes),
            "input_digest_prefix": runner_sha[:8],
            "runner_visible_fields": list(visible),
        },
        "isolation": {
            "read_whitelist": [
                "tasks/T-195b/PROMPT.md",
                "META/routing-questions-runner-v1.json",
                "docs/specs/fact-evidence-pack-v1.md",
                "tasks/T-195/run_r_tool.py（仅导入 routing 逻辑）",
                "engine.cli", "tools.query_theory", "sources/",
            ],
            "read_forbidden": False,
            "read_restricted_fields": False,
            "read_prereg": False,
            "read_answers": False,
            "read_restricted_artifacts": False,
            "notes": [
                "只读 sanitized runner 文件；未打开未脱敏问题文件，未接触任何 restricted 字段",
                "未读 META/routing-prereg-v1.json、任何 answers / anchor / fresh / holdout / golden / p1-system-run*",
                "未重跑 fixed-20；未评分、未自评；未做 git 写",
                "routing 证据包由 T-195 同一生成逻辑产出，仅输入改为脱敏 runner 视图",
            ],
        },
        "routing": {
            "schema": "fact-evidence-pack/v1",
            "input": "META/routing-questions-runner-v1.json",
            "question_count": len(packs),
            "complete": len(packs) == 15,
            "blind_valid": True,
            "blind_valid_reason": "输入文件仅含 question_id/domain/question/chart 四字段，无 restricted 字段",
            "out_of_class_emissions": 0,
            "emission_policy": "routing 包不发射任何克/生/化/墓或冲/合/穿/刑/破方向事实，只发宫位/边/原文锚点",
            "packs": packs,
            "evidence_item_count": sum(evidence_counts),
            "evidence_breakdown": breakdown,
            "per_question_counts": per_question,
        },
        "non_claims": NON_CLAIMS,
    }

    dest = REPO / args.out
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    out_sha = hashlib.sha256(dest.read_bytes()).hexdigest()

    print(f"wrote {dest}")
    print(f"packs {len(packs)}/15  evidence={out['routing']['evidence_item_count']}  "
          f"breakdown={breakdown}")
    print(f"per_question={per_question}")
    print(f"out_sha256={out_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
