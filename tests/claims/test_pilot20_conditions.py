"""tests/claims/test_pilot20_conditions.py · pilot-20 断语条件的回归护栏（T-143）。

守三件事，任何一件失守都说明「只有象没有成败」又回来了：

1. **锚点可核**：`source_refs` / `invalidator_evidence` 里声明的引文，必须能在
   声明的行号上逐字命中（原文只增不改，行号得能对得上）。
2. **成败不丢**：`M1-D-298` / `G-SP-130` 必须有非空 `invalidators`；
   从 partial 转 compiled 的 4 条，`preconditions.all` 里必须挂 `needs_judgment`。
3. **标杆盘不再 rejected**：段派原文判「婚姻好」的 坤造 癸丑 癸亥 辛亥 癸巳
   （`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:58`
   「伤官亥冲巳，夫宫为喜，冲去夫星忌神」），`M1-D-298` 不得再判 rejected。

依据：ADR-007 D10/D11/D12、tasks/T-143/PROMPT.md。
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

from engine.api import analyze_facts, to_jsonable
from engine.claims.condition_ir import build_context, compile_claim, evaluate_claim

ROOT = pathlib.Path(__file__).resolve().parents[2]
PILOT = ROOT / "theory" / "claims" / "conditions-v2" / "pilot-20.yaml"

BENCHMARK_PILLARS = ["癸丑", "癸亥", "辛亥", "癸巳"]
BENCHMARK_GENDER = "坤"
# 段派原文「婚姻好、冲去夫星忌神」的标杆盘：不得判 rejected，只可 candidate / needs_fact
FLIPPED_FROM_PARTIAL = ("M1-D-009", "M1-D-013", "M1-D-242", "M3-R-166")


def _claims() -> dict[str, dict]:
    data = yaml.safe_load(PILOT.read_text(encoding="utf-8"))
    return {c["id"]: c for c in data["claims"]}


def _has_atom(node, name: str) -> bool:
    if not isinstance(node, dict):
        return False
    for key in ("all", "any"):
        if key in node:
            return any(_has_atom(c, name) for c in node[key] or [])
    if "not" in node:
        return _has_atom(node["not"], name)
    return node.get("atom") == name


def _benchmark_ctx() -> dict:
    return build_context(to_jsonable(
        analyze_facts(pillars=BENCHMARK_PILLARS, gender=BENCHMARK_GENDER)))


# ---------------------------------------------------------------- 1. 锚点可核

@pytest.mark.parametrize("claim_id", sorted(_claims()))
def test_declared_quotes_are_verbatim_on_declared_line(claim_id: str):
    """新增/改动的多锚点与失效条件锚点，必须能在原文声明行逐字命中。"""
    claim = _claims()[claim_id]
    spec = claim.get("conditions_v2") or {}
    entries = (claim.get("source_refs") or []) + (spec.get("invalidator_evidence") or [])
    for e in entries:
        if not e.get("quote"):
            continue
        path = ROOT / e["path"]
        assert path.exists(), f"{claim_id}: 源文件不存在 {e['path']}"
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        assert 1 <= e["line"] <= len(lines), f"{claim_id}: 行号越界 {e['path']}:{e['line']}"
        assert e["quote"] in lines[e["line"] - 1], (
            f"{claim_id}: 引文不在声明的行上 —— {e['path']}:{e['line']} 引文={e['quote'][:30]!r}")


# ---------------------------------------------------------------- 2. 成败不丢

@pytest.mark.parametrize("claim_id", ["M1-D-298", "G-SP-130"])
def test_high_value_claims_have_invalidators(claim_id: str):
    """D12：20/20 invalidators 为空＝只有象没有成败，已判定为设计失效。"""
    spec = _claims()[claim_id]["conditions_v2"]
    inv = spec.get("invalidators") or {}
    assert inv.get("any"), f"{claim_id}: invalidators 仍为空"
    assert spec.get("invalidator_evidence"), f"{claim_id}: 缺原文锚点"


@pytest.mark.parametrize("claim_id", FLIPPED_FROM_PARTIAL)
def test_former_partial_claims_mark_unmapped_judgment(claim_id: str):
    """partial → compiled 的前提是：未量化子条件用 needs_judgment 显式挂着，而不是删掉。"""
    claim = _claims()[claim_id]
    assert claim["compile_state"] == "compiled"
    assert compile_claim(claim)["status"] == "compiled"
    pre = (claim.get("conditions_v2") or {}).get("preconditions") or {}
    assert _has_atom(pre, "needs_judgment"), f"{claim_id}: 未挂 needs_judgment"


# ---------------------------------------------------------------- 3. 标杆盘

def test_frame_atom_accepts_dual_role():
    """「夫妻宫有用」≠「日支本气是财官」：frame 必须收进 双属。

    依据 大连面授讲义:4109「坐下为用（财官食伤）就不好」——夫妻宫语境的「用」含食伤；
    事实层把食伤标为 双属。
    """
    frame = _claims()["M1-D-298"]["conditions_v2"]["frame_atom"]
    roles = {c.get("args", {}).get("role") for c in frame.get("any") or []}
    assert {"用", "双属"} <= roles, f"frame_atom 未收进 双属：{roles}"


def test_benchmark_chart_is_not_rejected():
    """坤造 癸丑 癸亥 辛亥 癸巳：原文判婚姻好，M1-D-298 不得判 rejected。"""
    ctx = _benchmark_ctx()
    ev = evaluate_claim(_claims()["M1-D-298"], ctx)
    assert ev["state"] != "rejected", f"标杆盘仍被拒：{ev.get('reason')} / {ev['failed_atoms']}"
    assert ev["state"] in ("candidate", "needs_fact")


def test_benchmark_unknown_carries_reason():
    """unknown 必须显性（契约 23：静默丢弃未知＝引擎替 Agent 定局）。"""
    ev = evaluate_claim(_claims()["M1-D-298"], _benchmark_ctx())
    assert ev["state"] == "needs_fact"
    assert ev["value"] is None
    assert ev["unknown_facts"], "needs_fact 未带原因"
