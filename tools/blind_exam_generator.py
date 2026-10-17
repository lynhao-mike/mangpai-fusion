"""tools/blind_exam_generator.py · 标准化盲考题生成器

设计目标（Gemini 4 简报 2026-10-17）
--------------------------------
自由断语对不上账是首轮盲测最大风险。本工具把「自由发挥」改为「标准化必答」：

1. **ground truth 提取**：从 feedback.md 的事件年表读出已知事实（仅生成器使用，
   题目里隐去答案）；
2. **题型生成**：按固定模板生成可严格计分的题目：
   - 学业题（最高学历层次）
   - 事业题（体制内 / 企业管理 / 技术专业 / 独立经商 四选一）
   - 流年对比题（给 2-3 个已过流年，问哪年发生重大变动、性质吉凶）
   - **负样本题**（Gemini 核心贡献）：从平稳期随机取 1-2 个流年，
     问「该年是否发生重大负向变动」——专测「逢冲必断灾」的误报率；
     断稳的流派（子平/滴天髓）在此得分
3. **防逆境聚集**：考题窗口混合顺境年 + 逆境年 + 平稳年，严禁只考求测当年近 2 年
   （求测者多是刚挨了毒打才发帖，近两年凶事概率虚高）
4. **答案冻结**：题目与标准答案同时落盘（answer_key 分离存储，盲断者只看题册）

信息隔离
--------
生成器读取 feedback.md（它是「出题人」角色，不是盲断者）。
产出两个文件：exam.md（题册，无答案）+ answer_key.json（标准答案，核验者用）。
盲断 agent 只允许读 exam.md；answer_key 与 feedback.md 同属禁区。

CLI
---
    python -m tools.blind_exam_generator --case <case_id>
    python -m tools.blind_exam_generator --from-json .workbuddy-ai/sampled/pilot.json
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CASES = ROOT / "cases"
OUT = ROOT / ".workbuddy-ai" / "exams"

_EVENT_ROW = re.compile(r"^\|\s*(\d{4})\s*\|\s*(.+?)\s*\|\s*([^|]*)\|")
_NEG_KWS = ["凶", "破财", "欠债", "离职", "离婚", "病", "伤", "手术", "官非", "分手", "辞"]
_POS_KWS = ["吉", "升", "结婚", "生子", "买房", "赚", "成果", "奖", "录取", "置业"]


def load_events(case_id: str) -> list[dict[str, Any]]:
    p = CASES / case_id / "feedback.md"
    if not p.exists():
        return []
    events = []
    for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        m = _EVENT_ROW.match(line.strip())
        if m:
            year, text, domains = m.groups()
            events.append({
                "year": int(year),
                "text": text.strip(),
                "domains": [d.strip() for d in domains.split(",") if d.strip()],
            })
    return sorted(events, key=lambda e: e["year"])


def birth_year(case_id: str) -> int | None:
    p = CASES / case_id / "input.md"
    if not p.exists():
        return None
    m = re.search(r"公历:\s*\"?(\d{4})", p.read_text(encoding="utf-8-sig", errors="replace"))
    return int(m.group(1)) if m else None


def classify(text: str) -> str:
    neg = sum(1 for k in _NEG_KWS if k in text)
    pos = sum(1 for k in _POS_KWS if k in text)
    if neg > pos:
        return "negative"
    if pos > neg:
        return "positive"
    return "mixed"


def pick_exam_years(events: list[dict[str, Any]], rng: random.Random) -> dict[str, list[int]]:
    """选考题年份：逆境年 + 顺境年 + 平稳年混合，且避开事件年表末端 2 年。

    平稳年 = 事件年表中未提及、且处于事件覆盖跨度内的年份。
    """
    if not events:
        return {}
    years = [e["year"] for e in events]
    lo, hi = min(years), max(years)
    # 排除末端 2 年（防逆境聚集）
    safe_hi = hi - 2
    span = list(range(lo, safe_hi + 1))
    if not span:
        span = list(range(lo, hi + 1))

    adverse = [e["year"] for e in events
               if classify(e["text"]) == "negative" and e["year"] <= safe_hi]
    good = [e["year"] for e in events
            if classify(e["text"]) == "positive" and e["year"] <= safe_hi]
    quiet = [y for y in span if y not in years]

    rng.shuffle(adverse)
    rng.shuffle(good)
    rng.shuffle(quiet)
    return {
        "adverse": adverse[:1] or [],
        "good": good[:1] or [],
        "quiet": quiet[:2],
        "compare_pool": sorted(set(span)),
    }


def gen_questions(case_id: str, rng: random.Random) -> tuple[list[dict], dict] | None:
    events = load_events(case_id)
    if len(events) < 3:
        return None
    by = birth_year(case_id)
    yrs = pick_exam_years(events, rng)
    if not yrs:
        return None

    edu_events = [e for e in events if any(k in e["text"] for k in ["学", "考", "毕业", "研", "录取"])]
    career_events = [e for e in events
                     if any(k in e["text"] for k in ["工作", "职", "创业", "单位", "公司", "经商"])]

    questions = []
    answers = {}
    n = 0

    # Q1 学业（有学历事件才出）
    if edu_events:
        n += 1
        highest = "研究生及以上" if any("研" in e["text"] for e in edu_events) else \
                  "本科" if any("大学" in e["text"] or "本" in e["text"] for e in edu_events) else \
                  "高中/中专"
        questions.append({
            "id": f"q{n}", "type": "education", "matter": "education",
            "question": "判断命主的最高学历层次（四选一）：初中及以下 / 高中或中专 / 大专或本科 / 研究生及以上",
        })
        answers[f"q{n}"] = {"expected": highest, "event_basis": [f"{e['year']}:{e['text'][:30]}" for e in edu_events[:3]]}

    # Q2 事业类型（有职业事件才出）
    if career_events:
        n += 1
        questions.append({
            "id": f"q{n}", "type": "career_type", "matter": "career",
            "question": "判断命主的主要职业类型（四选一）：体制内稳定型 / 企业管理或技术专业型 / 独立经商型 / 自由职业或多重身份型",
        })
        txt = " ".join(e["text"] for e in career_events)
        if any(k in txt for k in ["公务员", "编制", "体制"]):
            exp = "体制内稳定型"
        elif any(k in txt for k in ["创业", "自己", "开店", "生意", "经商"]):
            exp = "独立经商型"
        elif any(k in txt for k in ["跳槽", "换工作", "离职"]):
            exp = "自由职业或多重身份型"
        else:
            exp = "企业管理或技术专业型"
        answers[f"q{n}"] = {"expected": exp, "event_basis": [f"{e['year']}:{e['text'][:30]}" for e in career_events[:3]]}

    # Q3 流年对比（核心题：从对比池抽 3 年，问哪年有重大变动）
    pool = yrs.get("compare_pool") or []
    if len(pool) >= 3:
        n += 1
        chosen = rng.sample(pool, 3)
        # 答案：这三年里事件年表中出现过的、且分类非 mixed 的年份
        ev_by_year = {e["year"]: e for e in events}
        change_year = next((y for y in chosen if y in ev_by_year and classify(ev_by_year[y]["text"]) != "mixed"), None)
        questions.append({
            "id": f"q{n}", "type": "year_compare", "matter": "mixed",
            "question": f"在 {chosen[0]}、{chosen[1]}、{chosen[2]} 三年中，哪一年发生了重大的岗位/财务/家庭变动？变动性质为吉为凶？（若三年均无重大变动，答「均平稳」）",
        })
        if change_year:
            answers[f"q{n}"] = {"expected": f"{change_year}（{classify(ev_by_year[change_year]['text'])}）",
                                "event_basis": [f"{change_year}:{ev_by_year[change_year]['text'][:40]}"]}
        else:
            answers[f"q{n}"] = {"expected": "均平稳", "event_basis": ["三年内事件年表无记录"]}

    # Q4 负样本题（Gemini 核心：测「逢冲必断灾」的误报）
    quiet = yrs.get("quiet") or []
    if quiet:
        n += 1
        qs = "、".join(str(y) for y in quiet)
        questions.append({
            "id": f"q{n}", "type": "negative_control", "matter": "mixed",
            "question": f"判断 {qs} 期间是否发生了重大负向事件（失业/破财/重病/婚变/官非）。"
                        f"若判断会发生，指出具体年份与性质；若判断平稳，明确说「该期平稳无重大负向事件」。",
        })
        # 真相：这些年事件年表无负向记录 = 平稳（True Negative 场景）
        neg_in_quiet = [e["year"] for e in events if e["year"] in quiet and classify(e["text"]) == "negative"]
        answers[f"q{n}"] = {
            "expected": (f"{neg_in_quiet[0]} 有负向事件" if neg_in_quiet else "该期平稳无重大负向事件"),
            "event_basis": [f"{e['year']}:{e['text'][:30]}" for e in events if e["year"] in quiet] or ["事件年表该期无记录"],
            "scoring_note": "答「平稳」且确实平稳 = True Negative 命中（断稳能力得分）；答「有凶」但实际平稳 = 误报（False Positive）",
        }

    return questions, answers


def generate(case_id: str) -> bool:
    # 跨进程确定性种子：hash() 默认带 PYTHONHASHSEED 随机盐，每次进程启动
    # 结果不同，会导致题面漂移、盲断者答的题与 answer_key 不一致。改用
    # hashlib 稳定哈希（同一 case_id 永远同一题目集）。
    import hashlib
    seed = int.from_bytes(hashlib.sha256(case_id.encode("utf-8")).digest()[:4], "big")
    rng = random.Random(seed)  # 案例确定性随机（跨进程稳定）
    result = gen_questions(case_id, rng)
    if result is None:
        print(f"SKIP {case_id}: 事件不足 3 条")
        return False
    questions, answers = result
    if len(questions) < 3:
        print(f"SKIP {case_id}: 仅生成 {len(questions)} 题（<3），跳过")
        return False

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / case_id).mkdir(exist_ok=True)

    exam = [
        f"# 标准化盲考题 · {case_id}",
        "",
        "> 本题册只含盘面与问题，不含任何答案。作答时依据盲断任务包材料（input.md + facts_all.json）。",
        "> 每题必须给出明确选择或明确判断，禁止「可能/大概」类骑墙表述。",
        "",
    ]
    for q in questions:
        exam.append(f"## {q['id']}  [{q['type']}]")
        exam.append("")
        exam.append(q["question"])
        exam.append("")
    (OUT / case_id / "exam.md").write_text("\n".join(exam), encoding="utf-8")

    key = {"case_id": case_id, "question_count": len(questions), "answers": answers}
    (OUT / case_id / "answer_key.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OK   {case_id}: {len(questions)} 题（答案已冻结至 answer_key.json）")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="标准化盲考题生成器（含负样本题）")
    ap.add_argument("--case")
    ap.add_argument("--from-json", type=Path)
    args = ap.parse_args(argv)

    cases = []
    if args.case:
        cases = [args.case]
    elif args.from_json:
        rows = json.loads(args.from_json.read_text(encoding="utf-8"))
        cases = [r["case"] for r in rows]
    if not cases:
        ap.error("需要 --case 或 --from-json")

    ok = 0
    for c in cases:
        if generate(c):
            ok += 1
    print(f"\n生成 {ok}/{len(cases)} 份考题")
    print(f"题册：{OUT}/<case>/exam.md（盲断者可读）")
    print(f"答案：{OUT}/<case>/answer_key.json（盲断者禁区）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
