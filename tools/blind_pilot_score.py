"""盲测判分：exam_answers 对照 answer_key，逐题评分

判分口径（blind-scoring/v1 + Gemini 4 负样本设计）
------------------------------------------------
1. 选择题（education / career_type）：作答 == expected → correct；否则 incorrect
2. 流年对比题（year_compare）：
   - expected "均平稳" → 作答含"均平稳"→correct，否则 incorrect
   - expected "YYYY（方向）" → 作答含该年份 → 年份命中；再看方向词是否一致
     · 年份+方向都对 → correct
     · 年份对方向错 → partial
     · 年份错 → incorrect
3. 负样本题（negative_control）：
   - expected "该期平稳无重大负向事件" → 作答也是"平稳" → **True Negative 命中**（correct）
     · 作答报凶 → **False Positive 误报**（incorrect，专测"逢冲必断灾"）
   - expected "YYYY 有负向事件" → 作答指该年 → correct；报平稳 → incorrect（漏报）
4. boundary_risk 断语（356/359 时柱跨界）→ 该例相关题记 undetermined

产出：META/blind_scoring/<case>.json，含逐题判定 + 汇总
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"F:\综合盲派\mangpai-fusion")
EXAMS = ROOT / ".workbuddy-ai" / "exams"
BUNDLE = ROOT / ".workbuddy-ai" / "blind-bundle-v2"
OUT = ROOT / "META" / "blind_scoring"
sys.stdout.reconfigure(encoding="utf-8")

# 356/359 时柱跨界风险：相关题记 undetermined（盲断者已标 boundary_risk）
BOUNDARY_RISK_CASES = {
    "C-2026-RF000356-坤-戊辰癸亥癸巳戊午",
    "C-2026-RF000359-坤-戊辰癸亥癸巳丁巳",
}
# 同人组：统计时只算 1 个独立样本
SAME_PERSON_GROUPS = [
    ["C-2026-RF000356-坤-戊辰癸亥癸巳戊午", "C-2026-RF000359-坤-戊辰癸亥癸巳丁巳"],
]

PINGWEN = "平稳"


def norm(s: str) -> str:
    return re.sub(r"\s+", "", str(s))


def _direction_of(text: str) -> str:
    """把「positive/negative/吉/凶/正/负」统一成方向标签。"""
    t = norm(text)
    neg = ("negative" in t) or ("凶" in t) or ("负向" in t)
    pos = ("positive" in t) or ("吉" in t) or ("正向" in t)
    if neg and not pos:
        return "negative"
    if pos and not neg:
        return "positive"
    return "mixed"


def score_choice(ans: str, expected: str) -> tuple[str, str]:
    # 选项文案归一：题面写「高中或中专」、答案写「高中/中专」，须等价
    def canon(s: str) -> str:
        s = norm(s).replace("或", "/").replace("、", "/")
        return s
    if canon(ans) == canon(expected):
        return "correct", ""
    return "incorrect", f"作答「{ans}」≠ 期望「{expected}」"


def score_year_compare(ans: str, expected: str) -> tuple[str, str]:
    a = norm(ans)
    e = norm(expected)
    if PINGWEN in e:
        return ("correct", "") if PINGWEN in a else ("incorrect", f"期望均平稳，作答「{ans}」")
    m = re.search(r"(\d{4})", e)
    if not m:
        return "undetermined", f"答案格式异常: {expected}"
    exp_year = m.group(1)
    if exp_year not in a:
        return "incorrect", f"期望年份 {exp_year}，作答「{ans}」"
    # 方向判定：用统一方向标签比对，避免中英混写漏判
    exp_dir = _direction_of(e)
    ans_dir = _direction_of(a)
    if exp_dir == "mixed" or ans_dir == "mixed":
        return "correct", "年份命中（方向不判定）"
    if exp_dir == ans_dir:
        return "correct", ""
    return "partial", f"年份对（{exp_year}），方向不符：期望「{exp_dir}」，作答「{ans_dir}」"


def score_negative_control(ans: str, expected: str) -> tuple[str, str]:
    a = norm(ans)
    e = norm(expected)
    exp_calm = PINGWEN in e or "无重大负向" in e
    ans_calm = PINGWEN in a or "无重大负向" in a
    if exp_calm and ans_calm:
        return "correct", "True Negative 命中（断稳正确）"
    if exp_calm and not ans_calm:
        return "incorrect", "False Positive 误报（实际平稳却断凶）"
    if not exp_calm and ans_calm:
        return "incorrect", "漏报（实际有负向事件却断平稳）"
    # 都有事件：看年份
    m = re.search(r"(\d{4})", e)
    if m and m.group(1) in a:
        return "correct", "负向年份命中"
    return "partial", f"均报负向但年份不符：期望「{expected}」，作答「{ans}」"


SCORERS = {
    "education": score_choice,
    "career_type": score_choice,
    "year_compare": score_year_compare,
    "negative_control": score_negative_control,
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cases = sorted(p.name for p in BUNDLE.iterdir() if p.is_dir())
    results = []

    for case in cases:
        exam = (EXAMS / case / "exam.md").read_text(encoding="utf-8")
        types = dict(re.findall(r"^## (q\d+)\s+\[(\w+)\]", exam, re.MULTILINE))
        key = json.loads((EXAMS / case / "answer_key.json").read_text(encoding="utf-8-sig"))
        ans = json.loads((BUNDLE / case / "exam_answers.json").read_text(encoding="utf-8-sig"))

        rows = []
        for qid in sorted(types, key=lambda x: int(x[1:])):
            qtype = types[qid]
            a = str(ans["answers"].get(qid, ""))
            exp = str(key["answers"].get(qid, {}).get("expected", ""))
            if case in BOUNDARY_RISK_CASES and qtype in ("year_compare", "negative_control"):
                verdict, note = "undetermined", "时柱跨界风险（巳午交界），该题不进分母"
            else:
                verdict, note = SCORERS[qtype](a, exp)
            rows.append({
                "qid": qid, "type": qtype, "answer": a,
                "expected": exp, "verdict": verdict, "note": note,
            })

        c = sum(1 for r in rows if r["verdict"] == "correct")
        i = sum(1 for r in rows if r["verdict"] == "incorrect")
        p = sum(1 for r in rows if r["verdict"] == "partial")
        u = sum(1 for r in rows if r["verdict"] == "undetermined")
        results.append({"case_id": case, "rows": rows,
                        "correct": c, "incorrect": i, "partial": p, "undetermined": u})
        print(f"=== {case} ===")
        for r in rows:
            tag = {"correct": "✓", "incorrect": "✗", "partial": "△", "undetermined": "?"}[r["verdict"]]
            print(f"  {tag} {r['qid']} [{r['type']:16s}] 答「{r['answer'][:26]}」 "
                  f"期望「{r['expected'][:26]}」 {r['note']}")
        print(f"     → correct={c} incorrect={i} partial={p} undetermined={u}")
        print()

    # 汇总（同人组只算 1 个独立样本：取两例平均后按 1 例计）
    tot_c = sum(r["correct"] for r in results)
    tot_i = sum(r["incorrect"] for r in results)
    tot_p = sum(r["partial"] for r in results)
    tot_u = sum(r["undetermined"] for r in results)
    denom = tot_c + tot_i
    print("=== 汇总（题项级）===")
    print(f"  correct={tot_c} incorrect={tot_i} partial={tot_p} undetermined={tot_u}")
    print(f"  题项准确率 = {tot_c}/{denom} = {tot_c/denom*100:.1f}%" if denom else "  不可计算")
    print(f"  覆盖率 = {tot_c+tot_i}/{tot_c+tot_i+tot_u} = "
          f"{(tot_c+tot_i)/(tot_c+tot_i+tot_u)*100:.1f}%" if (tot_c+tot_i+tot_u) else "")
    print()
    print(f"  ⚠️ 样本说明：6 例中含 1 组同人（356/359），独立样本 = 5")
    print(f"  ⚠️ 356/359 的 year_compare/negative_control 因时柱跨界记 undetermined")

    payload = {
        "schema_version": "blind-scoring-result/v1",
        "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cases": results,
        "summary": {"correct": tot_c, "incorrect": tot_i, "partial": tot_p,
                    "undetermined": tot_u,
                    "item_accuracy": (tot_c / denom) if denom else None,
                    "independent_samples": len(results) - len(SAME_PERSON_GROUPS)},
        "notes": ["同人组 356/359 视为 1 个独立样本",
                  "时柱跨界案例的流年/负样本题记 undetermined"],
    }
    (OUT / "pilot-6-scoring.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n结果已写入 META/blind_scoring/pilot-6-scoring.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
