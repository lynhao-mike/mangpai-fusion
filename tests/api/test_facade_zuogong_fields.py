"""T-140 · facade 事实出口：tiyong / binzhu / distance / actor（ADR-007 D5）。

三件事必须同时成立：
1. `analyze_facts` 是**完整事实**：候选里 tiyong / binzhu / distance / actor 都在，
   且 actor 无方向时是 `null` 而不是「键消失」。
2. `compact_for_agent` 是**Agent 视图**：只削可由保留字段还原的冗余，tiyong / actor 不动。
3. `zuogong` 原子的 target 不再恒等于 `members[-1]`。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from engine.api import analyze_facts
from engine.api.facade import compact_for_agent
from engine.claims.condition_ir.atoms import build_context, zuogong

ROOT = Path(__file__).resolve().parents[2]
KUN = ["癸丑", "癸亥", "辛亥", "癸巳"]
QIAN = ["庚申", "戊寅", "壬子", "辛丑"]


def _kun() -> dict:
    return analyze_facts(pillars=KUN, gender="坤")


# ── 1. 事实视图完整性 ───────────────────────────────────────────────────────

def test_candidates_carry_tiyong_binzhu_distance_and_actor():
    cands = _kun()["duan_zuogong"]["candidates"]
    assert cands
    for cand in cands:
        assert {"tiyong", "binzhu", "distance", "actor"} <= set(cand)
        assert len(cand["tiyong"]) == len(cand["members"])
        assert cand["binzhu"] and all({"layer", "sides", "direction"} <= set(b) for b in cand["binzhu"])


def test_actor_null_is_null_not_missing_key():
    cands = _kun()["duan_zuogong"]["candidates"]
    nulls = [c for c in cands if c["actor"] is None]
    assert nulls, "该盘应有 actor 无方向的候选（刑/合）"
    assert "actor" in nulls[0], "actor 不得被 _compact 删键"
    assert any(isinstance(cand["actor"], str) for cand in cands), "应有带具体地址方向的候选"


# ── 2. Agent 视图：只削可还原字段 ───────────────────────────────────────────

def test_compact_for_agent_drops_only_restorable_fields():
    full = _kun()
    agent = compact_for_agent(full)

    full_cand = full["duan_zuogong"]["candidates"][0]
    agent_cand = agent["duan_zuogong"]["candidates"][0]
    assert {"mode", "tiyong", "actor", "members"} <= set(agent_cand)
    assert {"binzhu", "distance", "ten_gods"} & set(agent_cand) == set()
    if "edge_id" in full_cand:                     # 有边候选必须保留 edge_id
        assert agent_cand["edge_id"] == full_cand["edge_id"]
    assert "tiyong" in full_cand and "ten_gods" in full_cand, "投影不得回改事实视图"

    # ten_gods 可还原：members 地址 → chart.pillars 的干/支本气十神
    gods: dict[str, str] = {}
    for pillar in full["chart"]["pillars"]:
        gods[pillar["stem"]["addr"]] = pillar["stem"]["ten_god"]
        gods[pillar["branch"]["addr"]] = pillar["branch"]["main_ten_god"]
    assert tuple(gods[m] for m in agent_cand["members"]) == tuple(full_cand["ten_gods"])

    assert "nodes" not in agent["relations"]
    assert all(not ({"chars", "between", "layer", "scope", "distance"} & set(e))
               for e in agent["relations"]["edges"])
    assert all({"id", "kind", "members"} <= set(e) for e in agent["relations"]["edges"])
    assert full["relations"]["nodes"], "投影后事实视图仍须保留 nodes"

    # chart 干支的 wuxing/yinyang 可还原：保留 char 与十神字段即可
    for pillar in agent["chart"]["pillars"]:
        assert not ({"wuxing", "yinyang"} & set(pillar["stem"]))
        assert not ({"wuxing", "yinyang"} & set(pillar["branch"]))
        assert {"addr", "char", "ten_god"} <= set(pillar["stem"])
        assert {"addr", "char", "main_ten_god"} <= set(pillar["branch"])


def test_compact_for_agent_does_not_mutate_input():
    full = _kun()
    before = json.dumps(full, ensure_ascii=False, sort_keys=True)
    compact_for_agent(full)
    assert json.dumps(full, ensure_ascii=False, sort_keys=True) == before


# ── 3. CLI 分档：默认 Agent 视图 / --full 完整事实 ───────────────────────────

def _cli(*extra: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, "-m", "engine.cli", "all", "--pillars", " ".join(QIAN), "--gender", "乾", "--json", *extra],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return len(proc.stdout.encode("utf-8")), json.loads(proc.stdout)


def test_cli_full_keeps_facts_default_stays_compact():
    default_bytes, default = _cli()
    full_bytes, full = _cli("--full")

    assert default_bytes < 15_000 < full_bytes
    assert default["duan_zuogong"]["candidates"][0]["tiyong"]
    assert default["duan_zuogong"]["candidates"][0]["actor"] is None or isinstance(
        default["duan_zuogong"]["candidates"][0]["actor"], str
    )
    assert all("binzhu" not in c for c in default["duan_zuogong"]["candidates"])
    assert all("binzhu" in c for c in full["duan_zuogong"]["candidates"])
    assert all("distance" in c for c in full["duan_zuogong"]["candidates"])


# ── 4. zuogong 原子 target 不再回退 members[-1] ─────────────────────────────

def _atom_target(facts: dict, cand: dict) -> str | None:
    ctx = build_context(facts)
    ctx["zuogong"] = [cand]  # 只留一条，确保原子评的就是它
    return zuogong(ctx, {}).bindings.get("T")


def test_zuogong_atom_target_not_always_tail_member():
    facts = _kun()
    # 「用」落在 members[0] 的候选：正官（用）克食神 → target 不再等于 members[-1]
    needle = next(
        c for c in facts["duan_zuogong"]["candidates"]
        if c["tiyong"] == ["用", "双属"] and c["members"][1] == "Y.s" and c["mode"] == "制用"
    )
    assert needle["members"] == ["H.b", "Y.s"]
    assert _atom_target(facts, needle) == "H.b" != needle["members"][-1]

    # 同一候选回到旧形状（tiyong 被削）时，target 必然回退到 members[-1]：证明确实是 tiyong 在起作用
    legacy = {k: v for k, v in needle.items() if k != "tiyong"}
    legacy_facts = {"duan_zuogong": {"tiyong": {}, "candidates": [legacy]}}
    assert _atom_target(legacy_facts, legacy) == "Y.s" == legacy["members"][-1]
