"""tools/m2y395_real_direction.py · T-155：M2-Y-395 v2 方向重建（不读任何答案字段）。

本文件只做三件事：按 ``META/timing-eval-set-v1.json`` 的出生信息建原局 → 取日支
（``D.b``）的 ``kind=chong`` 原局边 → 按预注册方向规则给**每个人**定方向。

**计数单位 = 一个人（case）**：同一人多条冲边只算一例；多条同向取该方向；方向冲突记
``ambiguous``（弃权）。这与 T-151 的「一条冲边一例」不同（``tasks/T-155/PROMPT.md`` §1.1）。

方向判定直接复用 ``tools/m2y395_direction.py`` 的 ``direction_of``（该文件只读、未改动）：

  触发器  : 原局存在 ``kind=chong`` 的边，且成员含日支地址 ``D.b``；只看 ``scope=natal``
  方向    : ``KE_MAP[wx(D.b)] == wx(other)``  → ``self_controls``（我制对方）
            ``KE_MAP[wx(other)] == wx(D.b)`` → ``other_controls``（对方制我）
            其余（含同五行）                  → ``no_ke``（无克，弃权）
  预测    : ``self_controls`` → ``["P"]``；``other_controls`` → ``["N"]``；
            ``no_ke`` / ``ambiguous`` → ``[]``（触发但弃权）；无冲 → 未触发，不计分。

事实来源：
  ``KE_MAP`` / ``ZHI_TO_WUXING``  ``engine/predicates/types.py``:60-79
  ``chong`` 建边                  ``engine/facts/relation_graph.py``:210-222
  方向判定                        ``tools/m2y395_direction.py``:124-130（import，未改）

产物：``META/m2y395-v2-cases.json``
用法：``.venv\\Scripts\\python.exe -m tools.m2y395_real_direction``
退出码：0 = 重建完成；1 = 结构性失败（评测集缺失 / 无任何可判定例）。
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter
from typing import Any

from engine.api import analyze_facts
from engine.predicates.types import ZHI_TO_WUXING
from tools.m2y395_direction import direction_of

ROOT = pathlib.Path(__file__).resolve().parents[1]
TIMING_SET = ROOT / "META" / "timing-eval-set-v1.json"
OUT = ROOT / "META" / "m2y395-v2-cases.json"

PROTOCOL_ID = "m2y395-v2"
TASK = "T-155"
DAY_ADDR = "D.b"
GENDER_BY_CN = {"男": "乾", "女": "坤"}

# 预注册 §1.3：字母 P = 预测「婚姻不差」，N = 预测「负面婚姻事件」。
PREDICTION_LETTERS: dict[str, list[str]] = {
    "self_controls": ["P"],
    "other_controls": ["N"],
    "no_ke": [],
    "ambiguous": [],
    "no_chong": [],
}
DIRECTIONS = ("self_controls", "other_controls", "no_ke", "ambiguous")

DEFINITION = (
    "触发器=原局(kind=chong, scope=natal)且成员含 D.b 的边；"
    "方向=按 KE_MAP 比较 D.b 与 other 的本气五行（同五行/无克→no_ke）；"
    "同一人多条同向冲边→该方向，方向冲突→ambiguous；预测=self_controls→P、"
    "other_controls→N、no_ke/ambiguous→弃权；计数单位=一个人(case)"
)


# ── 建盘层 ──────────────────────────────────────────────────────────────

def load_usable_cases() -> list[dict[str, Any]]:
    """只取 ``usable_for_timing is True`` 的案例；本函数不触碰任何答案文件。"""
    doc = json.loads(TIMING_SET.read_text(encoding="utf-8"))
    cases = doc.get("cases") or []
    return [c for c in cases if c.get("usable_for_timing") is True]


def build_facts(case: dict[str, Any]) -> dict[str, Any]:
    """``birth_dt`` + ``gender``(男→乾/女→坤) 走既有 ``analyze_facts`` 入口。"""
    gender = GENDER_BY_CN.get(str(case.get("gender") or "").strip())
    if gender is None:
        raise ValueError(f"性别无法映射：{case.get('gender')!r}")
    birth_dt = str(case.get("birth_dt") or "").strip()
    if not birth_dt:
        raise ValueError("birth_dt 为空")
    return analyze_facts(birth_dt=birth_dt, gender=gender)


# ── 方向层 ──────────────────────────────────────────────────────────────

def day_chong_edges(facts: dict[str, Any], day_branch: str,
                    case_id: str, skipped: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """原局里成员含 ``D.b`` 的 chong 边，逐条定方向；非二元边跳过并记录，不静默丢弃。"""
    edges: list[dict[str, Any]] = []
    for e in (facts.get("relations") or {}).get("edges") or []:
        if e.get("kind") != "chong" or e.get("scope") != "natal":
            continue
        members = tuple(e.get("members") or ())
        if DAY_ADDR not in members:
            continue
        if len(members) != 2:  # chong 定义为一对一；异常边记录后跳过
            skipped.append({"case_id": case_id, "edge_id": e.get("id"),
                            "reason": f"chong 边成员数 {len(members)} != 2"})
            continue
        i = members.index(DAY_ADDR)
        chars = tuple(e.get("chars") or ())
        if len(chars) != 2:
            skipped.append({"case_id": case_id, "edge_id": e.get("id"),
                            "reason": f"chong 边 chars 数 {len(chars)} != 2"})
            continue
        day_char, other_char = chars[i], chars[1 - i]
        if day_char != day_branch:  # 地址与盘面不一致＝口径漂移，必须显式失败
            skipped.append({"case_id": case_id, "edge_id": e.get("id"),
                            "reason": f"D.b 字 {day_char} != 日支 {day_branch}"})
            continue
        day_wx, other_wx = ZHI_TO_WUXING[day_char], ZHI_TO_WUXING[other_char]
        edges.append({
            "edge_id": e.get("id"),
            "other": other_char,
            "other_wx": other_wx,
            "direction": direction_of(day_wx, other_wx),
        })
    return edges


def aggregate_direction(edges: list[dict[str, Any]]) -> str:
    """同一人多条冲边按方向聚合；方向集合唯一取该方向，否则 ambiguous（与 T-151 同口径）。"""
    dirs = {e["direction"] for e in edges}
    if len(dirs) == 1:
        return next(iter(dirs))
    return "ambiguous"


def build_case(case: dict[str, Any], facts: dict[str, Any],
               skipped: list[dict[str, Any]]) -> dict[str, Any]:
    case_id = str(case["case_id"])
    pillars_raw = (facts.get("chart") or {}).get("pillars") or []
    pillars = " ".join(p["stem"]["char"] + p["branch"]["char"] for p in pillars_raw)
    day_branch = pillars_raw[2]["branch"]["char"] if len(pillars_raw) >= 3 else ""
    edges = day_chong_edges(facts, day_branch, case_id, skipped)
    direction = aggregate_direction(edges) if edges else "no_chong"
    return {
        "case_id": case_id,
        "pillars": pillars,
        "day_branch": day_branch,
        "edges": edges,
        "direction": direction,
        "prediction_letters": list(PREDICTION_LETTERS[direction]),
        "triggered": bool(edges),
        "n_chong_edges": len(edges),
        "birth_dt": case.get("birth_dt"),
        "gender": case.get("gender"),
    }


# ── 主流程 ──────────────────────────────────────────────────────────────

def main() -> int:
    if not TIMING_SET.exists():
        print(f"[FATAL] 评测集缺失：{TIMING_SET}", file=sys.stderr)
        return 1
    usable = load_usable_cases()
    if not usable:
        print("[FATAL] usable_for_timing=true 的案例为 0", file=sys.stderr)
        return 1

    failures: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    for case in usable:
        case_id = str(case.get("case_id"))
        try:
            facts = build_facts(case)
        except Exception as exc:  # noqa: BLE001 - 逐例记录原因，不许吞掉
            failures.append({"case_id": case_id, "stage": "建盘",
                             "reason": f"{type(exc).__name__}: {exc}"})
            continue
        cases.append(build_case(case, facts, skipped))

    cases.sort(key=lambda c: c["case_id"])
    if not cases:
        print("[FATAL] 没有任何建盘成功的案例", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1

    dir_counts = Counter(c["direction"] for c in cases)
    triggered = [c for c in cases if c["triggered"]]
    mixed = sum(1 for c in cases if c["direction"] == "ambiguous"
                and {e["direction"] for e in c["edges"]} & {"no_ke"})
    opposed = dir_counts.get("ambiguous", 0) - mixed
    payload = {
        "meta": {
            "protocol_id": PROTOCOL_ID,
            "task": TASK,
            "generated_by": "python -m tools.m2y395_real_direction",
            "data_source": "META/timing-eval-set-v1.json",
            "n_usable_cases": len(usable),
            "n_built": len(cases),
            "n_build_failed": len(failures),
            "n_triggered": len(triggered),
            "trigger_rate": round(len(triggered) / len(cases), 4),
            "case_unit": "一个人（case）一例；同一人多条冲边只算一例",
            "direction_counts": {d: dir_counts.get(d, 0) for d in DIRECTIONS}
                                | {"no_chong": dir_counts.get("no_chong", 0)},
            "ambiguous_split": {"opposed_self_vs_other": opposed,
                                "mixed_with_no_ke": mixed},
            "n_skipped_edges": len(skipped),
            "ke_map_source": "engine/predicates/types.py:60-62",
            "zhi_wuxing_source": "engine/predicates/types.py:73-79",
            "chong_edge_source": "engine/facts/relation_graph.py:210-222",
            "direction_fn_source": "tools/m2y395_direction.py:124-130 (direction_of，只读复用)",
            "definition": DEFINITION,
            "notes": [
                "本文件不读任何标签/答案文件；标签只在 tools/m2y395_real_score.py 并入",
                "触发只看原局（scope=natal），不含大运/流年/天干冲",
                "建盘入口 engine.api.analyze_facts，性别 男→乾 / 女→坤",
            ],
        },
        "build_failures": failures,
        "skipped_edges": skipped,
        "cases": cases,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("=" * 74)
    print("T-155 · M2-Y-395 v2 方向重建（不读标签）")
    print("=" * 74)
    print(f"可评测案例        : {len(usable)}")
    print(f"建盘成功 / 失败    : {len(cases)} / {len(failures)}")
    print(f"日支有冲（人数）    : {len(triggered)}"
          f"（触发率 {len(triggered) / len(cases):.2%}）")
    for d in DIRECTIONS:
        print(f"  {d:15s} : {dir_counts.get(d, 0)}")
    print(f"  {'no_chong':15s} : {dir_counts.get('no_chong', 0)}")
    print(f"歧义拆分          : 正反相冲 {opposed} / 含 no_ke 混合 {mixed}")
    print(f"跳过的异常冲边    : {len(skipped)}")
    print("-" * 74)
    print(f"产物              : {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
