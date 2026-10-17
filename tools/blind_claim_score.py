"""断语级对账：predictions.json 的 time_scope 断语 vs feedback 事件年表

与考题判分的区别
----------------
考题判分的 answer_key 是启发式生成的（可能把「反馈沉默」当「真值」）。
本脚本直接把盲断者的断语拿到 feedback 原文事件年表里核对：
- 断语 time_scope 内的真实事件 → 可判 correct/incorrect
- 断语 time_scope 内无事件记录 → 记 undetermined（不猜）
这才是 blind-scoring/v1 要求的「无法观察的结果不进分母」。
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"F:\综合盲派\mangpai-fusion")
BUNDLE = ROOT / ".workbuddy-ai" / "blind-bundle-v2"
CASES = ROOT / "cases"
OUT = ROOT / "META" / "blind_scoring"
sys.stdout.reconfigure(encoding="utf-8")

EVENT_ROW = re.compile(r"^\|\s*(\d{4})\s*\|\s*(.+?)\s*\|\s*([^|]*)\|")

# 事项关键词（用于判断某事件是否属该事项域）
MATTER_KW = {
    "career": ["工作", "职业", "事业", "升", "岗", "跳", "创业", "单位", "公司", "职", "调动", "辞", "离"],
    "wealth": ["财", "钱", "收入", "赚", "破财", "负债", "投资", "生意", "款", "债"],
    "marriage": ["婚", "恋", "妻", "夫", "对象", "感情", "离婚", "结婚", "分手", "同居"],
    "health": ["病", "医", "手术", "健康", "伤", "住院", "癌", "体检", "痛"],
    "education": ["学", "考", "大学", "毕业", "学历", "升学", "录取", "研"],
    "family": ["父", "母", "子", "女", "兄", "弟", "姐", "妹", "家人", "亲", "产"],
}
NEG_KW = ["凶", "破财", "欠债", "离职", "离婚", "病", "伤", "手术", "官非", "分手", "辞", "败"]
POS_KW = ["吉", "升", "结婚", "生子", "买房", "赚", "成果", "奖", "录取", "置业", "成"]


def load_events(case: str) -> list[dict]:
    p = CASES / case / "feedback.md"
    if not p.exists():
        return []
    evs = []
    for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        m = EVENT_ROW.match(line.strip())
        if m:
            y, text, dom = m.groups()
            evs.append({"year": int(y), "text": text.strip(),
                        "domains": [d.strip() for d in dom.split(",") if d.strip()]})
    return sorted(evs, key=lambda e: e["year"])


def classify(text: str) -> str:
    neg = sum(1 for k in NEG_KW if k in text)
    pos = sum(1 for k in POS_KW if k in text)
    return "negative" if neg > pos else ("positive" if pos > neg else "mixed")


def scope_years(scope: str) -> tuple[int, int]:
    ys = [int(y) for y in re.findall(r"\d{4}", scope)]
    return (min(ys), max(ys)) if ys else (0, 9999)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cases = sorted(p.name for p in BUNDLE.iterdir() if p.is_dir())
    all_rows = []

    for case in cases:
        pred_p = BUNDLE / case / "predictions.json"
        if not pred_p.exists():
            continue
        pred = json.loads(pred_p.read_text(encoding="utf-8-sig"))
        events = load_events(case)
        rows = []

        for p in pred.get("predictions", []):
            pid = p.get("prediction_id")
            matter = p.get("matter_category", "")
            lo, hi = scope_years(p.get("time_scope", ""))
            direction = p.get("direction", "mixed")

            # 找 time_scope 内、且属该事项域的事件
            matched = []
            for e in events:
                if not (lo <= e["year"] <= hi):
                    continue
                blob = e["text"] + " " + " ".join(e["domains"])
                if any(k in blob for k in MATTER_KW.get(matter, [])):
                    matched.append(e)

            if not matched:
                verdict, note = "undetermined", f"反馈在 {lo}-{hi} 无{matter}事件记录"
            else:
                ev_dirs = [classify(e["text"]) for e in matched]
                if direction in ev_dirs:
                    verdict, note = "correct", f"方向一致：{len(matched)} 条事件"
                elif "mixed" in ev_dirs:
                    verdict, note = "partial", "事件性质不明确"
                else:
                    verdict, note = "incorrect", f"方向不符：断「{direction}」，事件「{ev_dirs}」"

            rows.append({
                "prediction_id": pid, "matter": matter,
                "time_scope": p.get("time_scope"), "direction": direction,
                "prediction": p.get("prediction", "")[:60],
                "matched_events": [f"{e['year']}:{e['text'][:30]}" for e in matched],
                "verdict": verdict, "note": note,
                "rule_ids": [r["rule_id"] for r in p.get("rule_independent", [])],
            })

        c = sum(1 for r in rows if r["verdict"] == "correct")
        i = sum(1 for r in rows if r["verdict"] == "incorrect")
        pa = sum(1 for r in rows if r["verdict"] == "partial")
        u = sum(1 for r in rows if r["verdict"] == "undetermined")
        print(f"=== {case} === 断语 {len(rows)} 条")
        for r in rows:
            tag = {"correct": "✓", "incorrect": "✗", "partial": "△", "undetermined": "?"}[r["verdict"]]
            print(f"  {tag} {r['prediction_id']} [{r['matter']:9s}] {r['time_scope']:10s} "
                  f"断「{r['direction']:8s}」 {r['note'][:38]}")
        print(f"     → correct={c} incorrect={i} partial={pa} undetermined={u}")
        print()
        all_rows.append({"case_id": case, "rows": rows,
                         "correct": c, "incorrect": i, "partial": pa, "undetermined": u})

    tc = sum(r["correct"] for r in all_rows)
    ti = sum(r["incorrect"] for r in all_rows)
    tp = sum(r["partial"] for r in all_rows)
    tu = sum(r["undetermined"] for r in all_rows)
    denom = tc + ti
    print("=== 断语级汇总 ===")
    print(f"  断语总数 {tc+ti+tp+tu}  correct={tc} incorrect={ti} partial={tp} undetermined={tu}")
    print(f"  可判定 {denom} 条，准确率 = {tc}/{denom} = {tc/denom*100:.1f}%" if denom else "  无可判定")
    print(f"  覆盖率 = {denom}/{tc+ti+tp+tu} = {denom/(tc+ti+tp+tu)*100:.1f}%")

    (OUT / "pilot-6-claim-scoring.json").write_text(json.dumps({
        "schema_version": "blind-claim-scoring/v1",
        "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cases": all_rows,
        "summary": {"total": tc + ti + tp + tu, "correct": tc, "incorrect": ti,
                    "partial": tp, "undetermined": tu,
                    "accuracy": (tc / denom) if denom else None},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n已写入 {OUT / 'pilot-6-claim-scoring.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
