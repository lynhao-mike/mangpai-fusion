"""tools/blind_year_score.py · 年份定向判断题判分

判分口径（修正版，解决首轮两个致命缺陷）
------------------------------------
1. **记录年**（feedback 有事件）：真值极性来自事件文本关键词分类。
   作答极性一致 → correct；相反 → incorrect；mixed → partial。
   事项域命中 +0.5 加权（可选，暂只记不判）。
2. **对照年**（feedback 无记录）：真值 = `undetermined`。
   **不判对错、不进分母**——因为「反馈未提及 ≠ 未发生」。
   只统计「误报率」：盲断者对这些年断「凶」的比例。
   这是可观测的倾向指标（测「逢冲必断灾」），不是准确率。
3. 覆盖率 = 有作答的年 / 全部待判年。

产出：META/blind_scoring/year-probe-scoring.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBES = ROOT / ".workbuddy-ai" / "year-probes"
OUT = ROOT / "META" / "blind_scoring"

POLARITY_MAP = {"吉": "positive", "凶": "negative", "平": "neutral"}
NEG_SYNONYMS = {"negative", "凶", "负向", "不利"}
POS_SYNONYMS = {"positive", "吉", "正向", "有利"}
NEU_SYNONYMS = {"neutral", "平", "无", "平稳", "无大事"}


def canon_polarity(v: str) -> str:
    v = str(v).strip()
    if v in POLARITY_MAP:
        return POLARITY_MAP[v]
    low = v.lower()
    if low in NEG_SYNONYMS or any(k in v for k in ("凶", "负", "不利")):
        return "negative"
    if low in POS_SYNONYMS or any(k in v for k in ("吉", "正", "有利")):
        return "positive"
    if low in NEU_SYNONYMS or any(k in v for k in ("平", "无")):
        return "neutral"
    return "unknown"


def score_case(case: str) -> dict | None:
    probe_dir = PROBES / case
    key_p = probe_dir / "answer_key.json"
    ans_p = probe_dir / "year_judgments.json"
    if not key_p.exists():
        return None
    key = json.loads(key_p.read_text(encoding="utf-8-sig"))
    if not ans_p.exists():
        return {"case_id": case, "status": "no_answer", "probe_years": len(key["probe_years"])}
    ans = json.loads(ans_p.read_text(encoding="utf-8-sig"))

    judgments = {int(j["year"]): j for j in ans.get("year_judgments", [])}
    rows = []
    for y in key["probe_years"]:
        truth = key["truth"][str(y)]
        j = judgments.get(y)
        got = canon_polarity(j.get("polarity", "")) if j else "missing"
        exp = truth["polarity"]

        if exp == "undetermined":
            # 对照年：不进分母，只记误报倾向
            verdict = "undetermined"
            note = "对照年（反馈无记录），不计对错"
            if got == "negative":
                note = "⚠️ 误报倾向：对无记录年断凶"
        elif got == "missing":
            verdict, note = "undetermined", "未作答"
        elif got == exp:
            verdict, note = "correct", ""
        elif exp == "mixed" or got == "neutral":
            verdict, note = "partial", f"期望 {exp}，作答 {got}"
        else:
            verdict, note = "incorrect", f"期望 {exp}，作答 {got}"

        rows.append({
            "year": y, "recorded": truth["recorded"],
            "expected": exp, "got": got, "verdict": verdict, "note": note,
            "basis": (j or {}).get("basis", "")[:60],
            "real_events": [e[:50] for e in truth.get("events", [])],
        })

    c = sum(1 for r in rows if r["verdict"] == "correct")
    i = sum(1 for r in rows if r["verdict"] == "incorrect")
    p = sum(1 for r in rows if r["verdict"] == "partial")
    u = sum(1 for r in rows if r["verdict"] == "undetermined")
    # 对照年误报统计
    controls = [r for r in rows if not r["recorded"]]
    false_pos = sum(1 for r in controls if r["got"] == "negative")
    return {
        "case_id": case, "rows": rows,
        "correct": c, "incorrect": i, "partial": p, "undetermined": u,
        "control_years": len(controls), "control_false_positive": false_pos,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="年份定向判断题判分")
    ap.add_argument("--case")
    args = ap.parse_args(argv)

    cases = [args.case] if args.case else sorted(
        p.name for p in PROBES.iterdir() if p.is_dir()
    )
    results = [r for r in (score_case(c) for c in cases) if r]

    OUT.mkdir(parents=True, exist_ok=True)
    tc = ti = tp = tu = 0
    tctrl = tfp = 0
    for r in results:
        print(f"=== {r['case_id']} ===")
        if r.get("status") == "no_answer":
            print(f"  ⏸ 未作答（待判 {r['probe_years']} 年）")
            print()
            continue
        for row in r["rows"]:
            tag = {"correct": "✓", "incorrect": "✗",
                   "partial": "△", "undetermined": "?"}[row["verdict"]]
            print(f"  {tag} {row['year']} [{'记录' if row['recorded'] else '对照'}] "
                  f"期望 {row['expected']:12s} 作答 {row['got']:10s} {row['note']}")
        print(f"     → correct={r['correct']} incorrect={r['incorrect']} "
              f"partial={r['partial']} undetermined={r['undetermined']}  "
              f"对照年误报 {r['control_false_positive']}/{r['control_years']}")
        print()
        tc += r["correct"]; ti += r["incorrect"]
        tp += r["partial"]; tu += r["undetermined"]
        tctrl += r["control_years"]; tfp += r["control_false_positive"]

    denom = tc + ti
    print("=== 汇总 ===")
    print(f"  记录年：correct={tc} incorrect={ti} partial={tp} undetermined={tu}")
    if denom:
        print(f"  准确率 = {tc}/{denom} = {tc/denom*100:.1f}%")
    else:
        print("  准确率 = 不可计算（暂无记录年作答）")
    if tctrl:
        print(f"  对照年误报率 = {tfp}/{tctrl} = {tfp/tctrl*100:.1f}%"
              f"（断凶倾向；非准确率）")

    payload = {
        "schema_version": "year-probe-scoring/v1",
        "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cases": results,
        "summary": {
            "recorded_correct": tc, "recorded_incorrect": ti,
            "recorded_partial": tp, "recorded_undetermined": tu,
            "accuracy": (tc / denom) if denom else None,
            "control_years": tctrl, "control_false_positive": tfp,
            "control_false_positive_rate": (tfp / tctrl) if tctrl else None,
        },
        "notes": [
            "对照年真值为 undetermined（反馈未提及≠未发生），不进准确率分母",
            "对照年只统计误报倾向，用于测「逢冲必断灾」",
        ],
    }
    (OUT / "year-probe-scoring.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n已写入 {OUT / 'year-probe-scoring.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
