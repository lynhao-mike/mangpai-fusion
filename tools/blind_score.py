"""tools/blind_score.py · 规则级独立核验与准确率统计

为什么需要单独一层
------------------
`engine/evaluation/dual_core_blind.compute_rule_review_statistics` 要求
`independent_rule_outcomes` 覆盖**每条 (case, matter, rule_id)**，且
`independent_hit` 是**该规则独立成立的判断**。

这不能用「预测对了就给所有引用规则记命中」来填充——一条最终结论引用三条
规则，命中一次不能分发给三条规则（这是过度归因，会虚高规则命中率）。
所以 `independent_hit` 必须由核验者**逐规则**判断，本工具负责：

1. `template`：从已封存的 rounds 生成待填核验表，把所有规则列全、值留 null；
2. `score`：读表 → 校验无 null、无遗漏 → 转成 `independent_rule_outcomes`
   → 调 `compute_rule_review_statistics` 出规则级统计；
3. `report`：汇总全部已完成核验的案例，输出案例级与规则级两套指标。

三条铁律（与 blind-scoring/v1 一致）
----------------------------------
1. **无法观察的结果不进分母**。`independent_hit` 为 null 视为未核验，
   `score` 直接拒绝计算，而不是当成 False。
2. **反馈未提及 ≠ 事件未发生**。事项级 verdict 用
   `correct / incorrect / undetermined`，不是 hit/miss。
3. **本工具只统计，永不修改规则库**。规则升降由命理师确认。

CLI
---
    python -m tools.blind_score template --case <case_id> --matter career
    python -m tools.blind_score score    --case <case_id> --matter career
    python -m tools.blind_score report
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.evaluation.dual_core_blind import (  # noqa: E402
    compute_rule_review_statistics,
)

SEALS_ROOT = ROOT / "META" / "blind_seals"
SEALS_DIR = SEALS_ROOT / ".dual-core-blind-seals"
VERIFY_DIR = ROOT / "META" / "blind_verification"
MATTERS = ("career", "wealth", "marriage", "health", "education", "family")

VERDICTS = ("correct", "incorrect", "undetermined")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── 封存读取 ────────────────────────────────────────────────────────────────

def load_seals() -> list[dict[str, Any]]:
    """读取全部封存，返回 [{case_id, matter, payload, path}]。

    封存里的 case_id 是复合形式 "{原始case}#{matter}"，这里拆回原案例。
    """
    if not SEALS_DIR.is_dir():
        return []
    out = []
    for f in sorted(SEALS_DIR.glob("*.json")):
        try:
            payload = json.loads(f.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        composite = str(payload.get("case_id") or "")
        if "#" in composite:
            case_id, matter = composite.rsplit("#", 1)
        else:
            case_id, matter = composite, str(payload.get("matter_category") or "")
        out.append({
            "case_id": case_id,
            "matter": matter,
            "payload": payload,
            "path": f,
        })
    return out


def find_seal(case_id: str, matter: str) -> dict[str, Any] | None:
    for s in load_seals():
        if s["case_id"] == case_id and s["matter"] == matter:
            return s
    return None


# ── template ────────────────────────────────────────────────────────────────

def cmd_template(case_id: str, matter: str) -> int:
    seal = find_seal(case_id, matter)
    if seal is None:
        print(f"ERROR: 未找到封存 {case_id}/{matter}", file=sys.stderr)
        return 2

    rounds = seal["payload"].get("rounds") or []
    if not rounds:
        print(f"ERROR: 封存无 rounds", file=sys.stderr)
        return 2
    rnd = rounds[-1]  # 以最终轮为准

    rule_verdicts = []
    seen: set[str] = set()
    for r in rnd.get("applied_rules") or []:
        rid = r.get("rule_id")
        if not rid or rid in seen:
            continue
        seen.add(rid)
        rule_verdicts.append({
            "rule_id": rid,
            "school": r.get("school"),
            "rule_direction": r.get("rule_direction"),
            "rule_statement": r.get("rule_statement"),
            "independent_hit": None,     # ← 核验者必须填 true/false
            "evidence": "",
        })

    template = {
        "schema_version": "blind-verification/v1",
        "case_id": case_id,
        "matter_category": matter,
        "round_index": rnd.get("round_index"),
        "time_scope": rnd.get("time_scope"),
        "round_direction": rnd.get("direction"),
        "round_conclusion": rnd.get("conclusion"),
        "generated_at": _now(),
        "instructions": {
            "matter_verdict": f"填 {list(VERDICTS)} 之一",
            "rule_independent_hit": "逐规则判断：仅凭该规则能否推出 round_conclusion 的方向。"
                                    "能=true，不能或方向相反=false。不确定就保持 null（不得计算）。",
            "note": "反馈未提及某事项时用 undetermined，不得填 incorrect。",
        },
        "matter_verdict": "undetermined",
        "matter_evidence": "",
        "rule_verdicts": rule_verdicts,
    }

    VERIFY_DIR.mkdir(parents=True, exist_ok=True)
    out = VERIFY_DIR / f"{_slug(case_id)}__{matter}.json"
    if out.exists():
        print(f"SKIP: 核验模板已存在 {out.name}（不覆盖，避免冲掉已填内容）")
        return 0
    out.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"OK 模板已生成：{out.relative_to(ROOT)}")
    print(f"   待填规则 {len(rule_verdicts)} 条，事项裁决 1 项")
    for rv in rule_verdicts:
        print(f"     {rv['rule_id']:10s} [{rv['rule_direction']}] {rv['rule_statement'][:42]}")
    return 0


def _slug(case_id: str) -> str:
    import re
    return re.sub(r"[^\w\-.一-龥]", "_", case_id)


# ── score ───────────────────────────────────────────────────────────────────

def _load_verification(case_id: str, matter: str) -> dict[str, Any] | None:
    p = VERIFY_DIR / f"{_slug(case_id)}__{matter}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def cmd_score(case_id: str, matter: str) -> int:
    seal = find_seal(case_id, matter)
    if seal is None:
        print(f"ERROR: 未找到封存 {case_id}/{matter}", file=sys.stderr)
        return 2
    ver = _load_verification(case_id, matter)
    if ver is None:
        print(f"ERROR: 未找到核验表，请先运行 template 再填写", file=sys.stderr)
        return 2

    rounds = seal["payload"].get("rounds") or []
    rnd = rounds[-1]
    expected_rules = {r["rule_id"] for r in (rnd.get("applied_rules") or [])}
    filled = {
        rv["rule_id"]: rv.get("independent_hit")
        for rv in ver.get("rule_verdicts", [])
    }

    missing = expected_rules - set(filled)
    unresolved = [rid for rid, v in filled.items() if v is None]
    if missing:
        print(f"ERROR: 核验表遗漏规则 {sorted(missing)}", file=sys.stderr)
        return 2
    if unresolved:
        print(
            f"REFUSE: 规则 {sorted(unresolved)} 的 independent_hit 仍为 null。\n"
            "无法观察的结果不得计入分母——请逐条判断后再算。",
            file=sys.stderr,
        )
        return 2

    seal_case_id = seal["payload"].get("case_id")  # 复合 ID，与 rounds 一致
    outcomes = [
        {
            "case_id": seal_case_id,
            "matter_category": matter,
            "rule_id": rid,
            "independent_hit": bool(filled[rid]),
        }
        for rid in sorted(expected_rules)
    ]

    try:
        stats = compute_rule_review_statistics(
            rounds=rounds, independent_rule_outcomes=outcomes
        )
    except (ValueError, TypeError) as exc:
        print(f"ERROR: 统计失败 {exc}", file=sys.stderr)
        return 1

    print(f"=== {case_id} / {matter} ===")
    print(f"  事项裁决: {ver.get('matter_verdict')}  ({ver.get('matter_evidence', '')[:50]})")
    print(f"  规则数: {len(expected_rules)}")
    for rid in sorted(expected_rules):
        hit = filled[rid]
        print(f"    {rid:10s} independent_hit={hit}")
    print(f"  规则级统计: {json.dumps(stats, ensure_ascii=False)}")

    # 落盘评分结果
    VERIFY_DIR.mkdir(parents=True, exist_ok=True)
    res = VERIFY_DIR / f"{_slug(case_id)}__{matter}.scored.json"
    res.write_text(json.dumps({
        "case_id": case_id,
        "matter_category": matter,
        "matter_verdict": ver.get("matter_verdict"),
        "independent_rule_outcomes": outcomes,
        "rule_stats": stats,
        "scored_at": _now(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  已写入 {res.relative_to(ROOT)}")
    return 0


# ── report ──────────────────────────────────────────────────────────────────

def cmd_report() -> int:
    scored_files = sorted(VERIFY_DIR.glob("*.scored.json")) if VERIFY_DIR.is_dir() else []
    if not scored_files:
        print("尚无已评分记录。先跑 template → 填写 → score。")
        print("提示：当前 4 例封存的 time_scope 在 2025 年之后，反馈尚未发生，")
        print("      按盲测纪律全部为 undetermined，不应计入准确率分母。")
        return 0

    from collections import Counter
    case_level: Counter = Counter()
    rule_rows: list[dict[str, Any]] = []

    for f in scored_files:
        d = json.loads(f.read_text(encoding="utf-8-sig"))
        case_level[d.get("matter_verdict")] += 1
        rule_rows.append(d)

    correct = case_level["correct"]
    incorrect = case_level["incorrect"]
    undetermined = case_level["undetermined"]
    denom = correct + incorrect

    print("=== 事项级准确率 ===")
    print(f"  correct={correct}  incorrect={incorrect}  undetermined={undetermined}")
    if denom:
        print(f"  准确率 = {correct}/{denom} = {correct/denom*100:.1f}%")
    else:
        print("  准确率 = 不可计算（分母为 0：无可判定项）")

    print()
    print("=== 规则级汇总（逐 case×matter×rule）===")
    agg: dict[str, dict[str, int]] = {}
    for d in rule_rows:
        for o in d.get("independent_rule_outcomes", []):
            s = agg.setdefault(o["rule_id"], {"hit": 0, "miss": 0})
            s["hit" if o["independent_hit"] else "miss"] += 1
    if not agg:
        print("  （无数据）")
    for rid in sorted(agg):
        s = agg[rid]
        n = s["hit"] + s["miss"]
        print(f"  {rid:12s} n={n:3d}  hit={s['hit']:3d}  miss={s['miss']:3d}  "
              f"命中率={s['hit']/n*100:5.1f}%")

    print()
    print("说明：本工具只统计，永不修改规则库。规则升降须命理师确认。")
    return 0


# ── CLI ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m tools.blind_score",
        description="规则级独立核验与盲测准确率统计",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_t = sub.add_parser("template", help="生成待填核验表")
    p_t.add_argument("--case", required=True)
    p_t.add_argument("--matter", required=True, choices=list(MATTERS))

    p_s = sub.add_parser("score", help="校验并计算规则级统计")
    p_s.add_argument("--case", required=True)
    p_s.add_argument("--matter", required=True, choices=list(MATTERS))

    sub.add_parser("report", help="汇总全部已评分记录")

    args = ap.parse_args(argv)
    if args.cmd == "template":
        return cmd_template(args.case, args.matter)
    if args.cmd == "score":
        return cmd_score(args.case, args.matter)
    return cmd_report()


if __name__ == "__main__":
    sys.exit(main())
