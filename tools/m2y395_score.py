"""tools/m2y395_score.py · T-151：并入题库答案并核指纹（本卡唯一读答案的环节）。

方向判定已在 ``tools/m2y395_direction.py`` 里完成，且对答案不可见；本文件只做
「按 ``cases[].period`` 并入答案 → 计数」。按 ``tasks/T-151/PROMPT.md`` §2.2，
这里**不做最终裁决**（「克向即制」是否成立由中枢判），只打印指纹表。

并入字段：``answer_letter`` / ``options`` / ``correct`` / ``branch``：

- ``branch`` = 方向分支（与 ``direction`` 同值，按卡面命名另存一份）
- ``correct`` = 答案字母是否落在 ``prediction_letters`` 内；
  ``no_ke`` / ``ambiguous`` 弃权，记 ``null``（不当作错，也不进分母）

另按 T-150 计分器契约（``engine/claims/metrics.py``）补 ``claim_id``（固定 ``M2-Y-395``）、
``triggered``（78 例全 true——``no_ke`` 是「触发后弃权」不是未触发）、``outcome``（固定
``unknown``，本条未建模 invalidator，不写 success）。

口径提醒：一条 ``(D.b, other)`` 冲边 = 一例。78 例来自 70 期（7 期有多条冲边），
故 59 例 scored 集只对应 53 个**独立**期——题级 59 与期级 53 不可混用，见本文件
``fingerprint.period_level`` 与 ``META/m2y395-report-v1.md`` §3.2。

产物：``META/m2y395-scored-v1.json``
用法：``.venv\\Scripts\\python.exe -m tools.m2y395_score``
退出码：0 = 计分完成；1 = 结构性失败（cases 缺失 / 全部 join 失败）。
"""
from __future__ import annotations

import json
import math
import pathlib
import sys
from collections import Counter
from typing import Any, Sequence

ROOT = pathlib.Path(__file__).resolve().parents[1]
BANK = ROOT / "tiekoulu_1507_to_1428.json"
CASES = ROOT / "META" / "m2y395-cases-v1.json"
OUT = ROOT / "META" / "m2y395-scored-v1.json"

TRIGGER_TEXT = "日主婚姻状况"
CLAIM_ID = "M2-Y-395"
BRANCHES = ("self_controls", "other_controls", "no_ke", "ambiguous")
LETTERS = ("A", "B", "C", "D", "E")
Z95 = 1.959963984540054


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def marriage_answers(bank: Sequence[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """period → {q_index, question, options, answer_letter}；多题/缺题逐条记录。"""
    idx: dict[str, dict[str, Any]] = {}
    problems: list[dict[str, Any]] = []
    for rec in bank:
        period = rec.get("period")
        hits = [q for q in rec.get("questions") or [] if TRIGGER_TEXT in str(q.get("question") or "")]
        if len(hits) != 1:
            problems.append({"period": period, "reason": f"题干含「{TRIGGER_TEXT}」的题有 {len(hits)} 道"})
            continue
        q = hits[0]
        answer = str(q.get("correct_answer"))
        options = q.get("options") or {}
        if answer not in options:
            problems.append({"period": period, "reason": f"答案 {answer!r} 不在选项字母内"})
            continue
        idx[period] = {
            "q_index": q.get("q_index"),
            "question": str(q.get("question") or ""),
            "options": options,
            "answer_letter": answer,
        }
    return idx, problems


def wilson(k: int, n: int, z: float = Z95) -> list[float]:
    """二项比例 Wilson 95% 区间（无连续性校正）。"""
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def profile(rows: Sequence[dict[str, Any]], predict_of: dict[str, list[str]],
            unit: str) -> dict[str, Any]:
    """按分支统计 n / A–E 分布 / 预测字母 / 命中。"""
    out: dict[str, Any] = {"unit": unit, "branches": {}, "total": len(rows)}
    for b in BRANCHES:
        cells = [r for r in rows if r["branch"] == b]
        dist = Counter(r["answer_letter"] for r in cells)
        scored = [r for r in cells if r["correct"] is not None]
        hits = sum(1 for r in scored if r["correct"])
        out["branches"][b] = {
            "n": len(cells),
            "dist": {k: dist.get(k, 0) for k in LETTERS},
            "predict": list(predict_of.get(b, [])),
            "abstain": not predict_of.get(b),
            "scored_n": len(scored),
            "hits": hits,
            "hit_rate": round(hits / len(scored), 4) if scored else None,
        }
    scored = [r for r in rows if r["correct"] is not None]
    hits = sum(1 for r in scored if r["correct"])
    b_hits = sum(1 for r in scored if r["answer_letter"] == "B")
    out["scored"] = {
        "n": len(scored), "hits": hits,
        "hit_rate": round(hits / len(scored), 4) if scored else None,
        "wilson95": wilson(hits, len(scored)),
        "b_baseline": {"letter": "B", "hits": b_hits,
                       "rate": round(b_hits / len(scored), 4) if scored else None},
        "n_distinct_periods": len({r["period"] for r in scored}),
    }
    return out


def period_rows(cases: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """同一期多条冲边折叠成一行（同方向；方向不一致时 direction=ambiguous）。"""
    by_period: dict[str, dict[str, Any]] = {}
    for c in cases:
        by_period.setdefault(c["period"], c)
    return list(by_period.values())


def main() -> int:
    if not CASES.exists():
        print(f"[FATAL] 题单缺失：{CASES}（先跑 python -m tools.m2y395_direction）", file=sys.stderr)
        return 1
    if not BANK.exists():
        print(f"[FATAL] 题库缺失：{BANK}", file=sys.stderr)
        return 1

    cases_payload = load_json(CASES)
    cases: list[dict[str, Any]] = cases_payload.get("cases") or []
    bank = load_json(BANK)
    answers, join_problems = marriage_answers(bank)

    join_failures: list[dict[str, Any]] = []
    scored_cases: list[dict[str, Any]] = []
    for c in cases:
        info = answers.get(c["period"])
        if info is None:
            join_failures.append({"case_id": c["case_id"], "period": c["period"],
                                  "reason": "题库里找不到唯一的「日主婚姻状况」单选题"})
            continue
        answer = info["answer_letter"]
        predict = list(c.get("prediction_letters") or [])
        branch = c.get("direction")
        correct = (answer in predict) if predict else None
        scored_cases.append({
            **c,
            # T-150 计分器契约（engine/claims/metrics.py）：claim_id / branch / triggered / outcome
            "claim_id": CLAIM_ID,
            "branch": branch,
            "triggered": True,      # 78 例全部触发；no_ke 是「触发后弃权」，不是未触发
            "outcome": "unknown",   # 本条未建模 invalidator，不写 success
            "answer_letter": answer,
            "options": info["options"],
            "q_index": info["q_index"],
            "correct": correct,
            "abstained": not predict,
        })

    if not scored_cases:
        print("[FATAL] 所有例都未 join 到答案，无法计分", file=sys.stderr)
        for f in join_failures[:20]:
            print(f"  {f}", file=sys.stderr)
        return 1

    predict_of: dict[str, list[str]] = {b: [] for b in BRANCHES}
    for c in scored_cases:
        predict_of[c["branch"]] = list(c.get("prediction_letters") or [])

    edge_fp = profile(scored_cases, predict_of, "chong_edge")
    per_fp = profile(period_rows(scored_cases), predict_of, "period")

    fingerprint = {
        "edge_level": edge_fp,
        "period_level": per_fp,
        "definition": cases_payload["meta"]["definition"],
        "case_unit": cases_payload["meta"]["case_unit"],
        "n_distinct_periods_total": len({c["period"] for c in scored_cases}),
    }

    payload = {
        "meta": {
            "protocol_id": cases_payload["meta"]["protocol_id"],
            "task": cases_payload["meta"]["task"],
            "generated_by": "python -m tools.m2y395_score",
            "cases_source": "META/m2y395-cases-v1.json",
            "answer_source": f"tiekoulu_1507_to_1428.json（题干含「{TRIGGER_TEXT}」的单选题）",
            "n_cases": len(cases),
            "n_scored_cases": len(scored_cases),
            "n_join_failures": len(join_failures),
            "n_bank_periods": len(bank),
            "n_bank_join_problems": len(join_problems),
            "predictions": {k: list(v) for k, v in predict_of.items()},
            "notes": [
                "correct=null 表示弃权（no_ke/ambiguous），不进分母",
                "一条冲边=一例；59 例 scored 集对应 53 个独立期",
                "claim_id 固定 M2-Y-395；triggered 全 true；outcome 固定 unknown"
                "（未建模 invalidator，不写 success）",
            ],
        },
        "fingerprint": fingerprint,
        "join_failures": join_failures,
        "join_problems": join_problems,
        "cases": scored_cases,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # ── 控制台输出 ──────────────────────────────────────────────────────
    print("=" * 84)
    print("T-151 · M2-Y-395 指纹核对（单位：一条 (D.b, other) 冲边 = 一例）")
    print("=" * 84)
    print(f"{'branch':<16}{'n':>4}{'A':>5}{'B':>5}{'C':>5}{'D':>5}{'E':>5}   "
          f"{'predict':<8}{'hits':>9}")
    print("-" * 84)
    for b in BRANCHES:
        r = edge_fp["branches"][b]
        pred = ",".join(r["predict"]) if r["predict"] else "—"
        hit = f"{r['hits']}/{r['scored_n']}" if r["scored_n"] else "—"
        d = r["dist"]
        print(f"{b:<16}{r['n']:>4}{d['A']:>5}{d['B']:>5}{d['C']:>5}{d['D']:>5}{d['E']:>5}   "
              f"{pred:<8}{hit:>9}")
    print("-" * 84)
    print(f"{'合计':<14}{edge_fp['total']:>6}")
    sc = edge_fp["scored"]
    print(f"scored = {sc['n']} 例（{sc['n_distinct_periods']} 期）："
          f"命中 {sc['hits']}/{sc['n']} = {sc['hit_rate'] * 100:.1f}%，"
          f"Wilson95 [{sc['wilson95'][0] * 100:.1f}%, {sc['wilson95'][1] * 100:.1f}%]")
    print(f"B 基线（同一 {sc['n']} 例）：{sc['b_baseline']['hits']}/{sc['n']} = "
          f"{sc['b_baseline']['rate'] * 100:.1f}%")
    print("-" * 84)
    ps = per_fp["scored"]
    print("按期口径（同一批期折叠成一行，仅作对照，非 PROMPT §1.5 口径）：")
    print("  " + "  ".join(f"{b}={per_fp['branches'][b]['n']}" for b in BRANCHES)
          + f"  合计={per_fp['total']}")
    print(f"  scored {ps['n']} 期：命中 {ps['hits']}/{ps['n']} = {ps['hit_rate'] * 100:.1f}%"
          f"；B 基线 {ps['b_baseline']['hits']}/{ps['n']} = {ps['b_baseline']['rate'] * 100:.1f}%")
    print("-" * 84)
    print(f"join 失败        : {len(join_failures)}")
    print(f"产物            : {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
