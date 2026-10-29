#!/usr/bin/env python
"""T-195b · routing 证据包独立结构核验（只依赖标准库 + engine.cli）。

不导入生成器、不读 expected_evidence / prereg / answers；不做召回评分、不判方向。
逐项复核 META/r-tool-run-routing-v1.json：
  - 15/15 题、chart_id 与 sanitized runner 一致、snapshot 三字段齐全；
  - 宫位地址/关系边 ID 可由 engine.cli 同快照复核；
  - 每条 theory 的 source_ref 可解析、quote 为原文行区间逐字子串；
  - evidence_items 三类引用全部可在本包内回查；
  - 无方向（direction=undetermined / actor=target=null）、无预期/答案字段。

退出码 0 = 结构核验通过。
用法：
  .venv\\Scripts\\python.exe tasks\\T-195b\\verify_pack.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PY = sys.executable
OUT = REPO / "META" / "r-tool-run-routing-v1.json"
RUNNER = REPO / "META" / "routing-questions-runner-v1.json"
PALACE_RULES = {f"M-0{i}" for i in range(1, 9)}
SOURCE_REF_RE = re.compile(r"^(?P<path>.+):L(?P<a>\d+)(?:-L(?P<b>\d+))?$")
FORBIDDEN_KEYS = {"expected_evidence", "fixed_facts", "party_direction", "is_conclusion", "mutual"}

errs: list[str] = []


def err(msg: str) -> None:
    errs.append(msg)


def engine(pillars: str, gender: str) -> dict:
    p = subprocess.run([PY, "-m", "engine.cli", "all", "--pillars", pillars,
                        "--gender", gender, "--json"], cwd=str(REPO), capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", "replace")[:300])
    return json.loads(p.stdout.decode("utf-8-sig"))


def lines(rel: str) -> list[str]:
    return (REPO / rel).read_text(encoding="utf-8").splitlines()


def walk(node):
    if isinstance(node, dict):
        yield from node.keys()
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


def main() -> int:
    data = json.loads(OUT.read_text(encoding="utf-8"))
    runner = json.loads(RUNNER.read_text(encoding="utf-8"))
    packs = data["routing"]["packs"]
    by_qid = {q["question_id"]: q for q in runner["questions"]}

    if data.get("task") != "T-195b":
        err("task != T-195b")
    if data["routing"].get("question_count") != 15 or len(packs) != 15:
        err(f"pack count {len(packs)} != 15")
    if {p["question_id"] for p in packs} != set(by_qid):
        err("question_id 集合与 sanitized runner 不一致")
    if data["routing"].get("out_of_class_emissions") != 0:
        err("out_of_class_emissions != 0")
    if data["runner"].get("input_sha256") != __import__("hashlib").sha256(RUNNER.read_bytes()).hexdigest():
        err("input_sha256 与当前 sanitized runner 不一致")

    banned = set(walk(packs)) & FORBIDDEN_KEYS
    if banned:
        err(f"包含禁用键: {sorted(banned)}")

    for pack in packs:
        qid = pack["question_id"]
        q = by_qid[qid]
        if pack["chart_id"] != q["chart"]["chart_id"] or pack["case_id"] != q["chart"]["case_id"]:
            err(f"{qid}: chart_id/case_id 漂移")
        if pack["snapshot"] != {"chart_id": pack["chart_id"], "dayun_index": None,
                                "liunian_year": None}:
            err(f"{qid}: snapshot 非原局三字段")
        if not pack["non_claims"] or not pack["gaps"]:
            err(f"{qid}: non_claims/gaps 为空")

        eng = engine(q["chart"]["four_pillars"], q["chart"]["gender"])
        if eng["chart"]["chart_id"] != pack["chart_id"]:
            err(f"{qid}: engine chart_id 不一致")
        ganzhi = [p["ganzhi"] for p in eng["chart"]["pillars"]]
        if [p["ganzhi"] for p in pack["facts"]["pillars"]] != ganzhi:
            err(f"{qid}: facts.pillars 与 engine 不一致")
        if pack["facts"]["day_master"] != eng["chart"]["day_master"]:
            err(f"{qid}: day_master 不一致")

        addrs = set()
        for p in eng["chart"]["pillars"]:
            addrs.add(p["stem"]["addr"])
            addrs.add(p["branch"]["addr"])
        e_map = {e["id"]: e for e in eng["relations"]["edges"]}

        for pal in pack["palaces"]:
            if pal["addr"] not in addrs:
                err(f"{qid}: palace {pal['addr']} 非 engine 地址")
            if pal["mapping_rule"] not in PALACE_RULES:
                err(f"{qid}: mapping_rule {pal['mapping_rule']} 未登记")

        pack_edges = set()
        for e in pack["edges"]:
            pack_edges.add(e["edge_id"])
            if e["edge_id"] not in e_map:
                err(f"{qid}: edge {e['edge_id']} 不在 engine 边表")
                continue
            src = e_map[e["edge_id"]]
            if e["members"] != src["members"] or e["kind"] != src["kind"]:
                err(f"{qid}: edge {e['edge_id']} 与 engine 不一致")
            if e["scope"] != "natal":
                err(f"{qid}: edge scope != natal")
            if e["direction"] != "undetermined" or e["actor"] is not None or e["target"] is not None:
                err(f"{qid}: edge {e['edge_id']} 带方向")

        theory_refs = set()
        for t in pack["theory"]:
            theory_refs.add(t["source_ref"])
            m = SOURCE_REF_RE.match(t["source_ref"])
            if not m:
                err(f"{qid}: source_ref 不可解析 {t['source_ref']}")
                continue
            path, a, b = m.group("path"), int(m.group("a")), int(m.group("b") or m.group("a"))
            if not (REPO / path).is_file():
                err(f"{qid}: source 文件不存在 {path}")
                continue
            body = lines(path)
            if not (1 <= a <= b <= len(body)):
                err(f"{qid}: 行区间越界 {t['source_ref']}")
                continue
            if not any(t["quote"] in ln for ln in body[a - 1:b]):
                err(f"{qid}: quote 非逐字 {t['source_ref']}")
            if not t.get("quote_verified"):
                err(f"{qid}: quote_verified=false")

        counts = {"palace": 0, "edge": 0, "source": 0}
        for item in pack["evidence_items"]:
            typ, ref = item.get("type"), item.get("ref")
            if typ not in counts:
                err(f"{qid}: 未知证据类型 {typ}")
                continue
            counts[typ] += 1
            if typ == "palace" and ref not in addrs:
                err(f"{qid}: 证据宫位不可回查 {ref}")
            if typ == "edge" and ref not in pack_edges:
                err(f"{qid}: 证据边不在本包 {ref}")
            if typ == "source" and ref not in theory_refs:
                err(f"{qid}: 证据 source 不在本包 {ref}")

    total = sum(len(p["evidence_items"]) for p in packs)
    if total != data["routing"]["evidence_item_count"]:
        err(f"evidence_item_count {data['routing']['evidence_item_count']} != {total}")

    print(f"packs={len(packs)} evidence={total} "
          f"breakdown={data['routing']['evidence_breakdown']}")
    if errs:
        for e in errs:
            print("FAIL", e)
        return 1
    print("PASS: 15/15 packs, evidence items resolvable, quotes verbatim, no direction")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
