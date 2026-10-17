"""tools/blind_year_probe.py · 年份清单任务包生成器

解决首轮盲测的核心矛盾
----------------------
首轮断语级覆盖率仅 14.6%：盲断者不知道反馈记录了哪些年份，它按大运推演，
断语落在无记录年份上 → 无法对账。

本工具生成「年份清单任务包」：
- **告知盲断者哪些年份有反馈记录**（只给年份 + 事项域，不给事件内容）
- 要求它对每个年份逐一判断：吉/凶/无大事 + 事项域 + 一句依据
- 真值来自 feedback 原文（answer_key 侧），人工确认后判分

为什么这样不泄露答案
--------------------
告知「2015 年有记录」只泄露"反馈采样位置"，不泄露"那年发生了什么"。
盲断者仍需从盘面推断吉凶——这才是要测的能力。
这比首轮"自由选年份"更公平：所有人被问同一组年份。

产出
----
`.workbuddy-ai/year-probes/<case>/`
- probe.md          题面（盲断者可读）：年份清单 + 作答格式
- answer_key.json   真值（核验者专用）：每年真实事件 + 吉凶分类

CLI
---
    python -m tools.blind_year_probe --from-json .workbuddy-ai/sampled/pilot.json
    python -m tools.blind_year_probe --case <case_id>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "cases"
OUT = ROOT / ".workbuddy-ai" / "year-probes"

_EVENT_ROW = re.compile(r"^\|\s*(\d{4})\s*\|\s*(.+?)\s*\|\s*([^|]*)\|")

# 吉凶分类关键词（与 blind_claim_score 一致）
NEG_KW = ["凶", "破财", "欠债", "离职", "离婚", "病", "伤", "手术", "官非",
          "分手", "辞", "败", "债", "灾", "难"]
POS_KW = ["吉", "升", "结婚", "生子", "买房", "赚", "成果", "奖", "录取",
          "置业", "成", "顺利", "得"]

MATTER_KW = {
    "career": ["工作", "职业", "事业", "升", "岗", "跳", "创业", "单位", "公司", "职", "调动", "辞", "离"],
    "wealth": ["财", "钱", "收入", "赚", "破财", "负债", "投资", "生意", "款", "债"],
    "marriage": ["婚", "恋", "妻", "夫", "对象", "感情", "离婚", "结婚", "分手", "同居"],
    "health": ["病", "医", "手术", "健康", "伤", "住院", "癌", "体检", "痛"],
    "education": ["学", "考", "大学", "毕业", "学历", "升学", "录取", "研"],
    "family": ["父", "母", "子", "女", "兄", "弟", "姐", "妹", "家人", "亲", "产"],
}


def classify(text: str) -> str:
    neg = sum(1 for k in NEG_KW if k in text)
    pos = sum(1 for k in POS_KW if k in text)
    if neg > pos:
        return "negative"
    if pos > neg:
        return "positive"
    return "mixed"


def matters_of(text: str, domains: list[str]) -> list[str]:
    blob = text + " " + " ".join(domains)
    return [m for m, kws in MATTER_KW.items() if any(k in blob for k in kws)]


def load_events(case: str) -> list[dict[str, Any]]:
    p = CASES / case / "feedback.md"
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        m = _EVENT_ROW.match(line.strip())
        if m:
            y, text, dom = m.groups()
            doms = [d.strip() for d in dom.split(",") if d.strip()]
            out.append({
                "year": int(y),
                "text": text.strip(),
                "domains": doms,
                "polarity": classify(text),
                "matters": matters_of(text, doms),
            })
    return sorted(out, key=lambda e: e["year"])


def birth_year(case: str) -> int | None:
    p = CASES / case / "input.md"
    if not p.exists():
        return None
    m = re.search(r'公历:\s*"?(\d{4})', p.read_text(encoding="utf-8-sig", errors="replace"))
    return int(m.group(1)) if m else None


def build(case: str) -> bool:
    events = load_events(case)
    if len(events) < 3:
        print(f"SKIP {case}: 事件不足 3 条")
        return False
    by = birth_year(case)

    # 年份清单 = 有记录年份 + 相邻的空白对照年（每个记录年前后各取 1 个未记录年）
    recorded = sorted({e["year"] for e in events})
    all_years = sorted({e["year"] for e in events} |
                       {y for y in range(min(recorded), max(recorded) + 1)})
    blanks = [y for y in all_years if y not in recorded]

    # 对照年：取每个记录年之后最近的未记录年，最多 4 个
    control = []
    for y in recorded:
        for b in blanks:
            if b == y + 1 and b not in control:
                control.append(b)
                break
        if len(control) >= 4:
            break
    if len(control) < 2:
        # 不足则从全部空白年里补
        for b in blanks:
            if b not in control:
                control.append(b)
            if len(control) >= 3:
                break

    probe_years = sorted(set(recorded) | set(control))

    # ── 题面（不含事件内容）──
    lines = [
        f"# 年份定向判断题 · {case}",
        "",
        "> 本题只给**年份清单**，不给任何事件内容。你要基于盘面推断每个年份的吉凶。",
        "> 这是盲测：你仍然不知道这些年发生了什么。",
        "",
        "## 一、盘面",
        "",
        f"- 出生年：{by if by else '（未提供）'}",
        f"- 需要判断的年份共 {len(probe_years)} 个：{'、'.join(str(y) for y in probe_years)}",
        "",
        "## 二、作答要求（每年必须给出三项）",
        "",
        "1. **吉凶**：`吉` / `凶` / `平`（无重大事件）三选一",
        "2. **事项域**：career / wealth / marriage / health / education / family（可多选；判「平」则填 `-`）",
        "3. **依据**：一句话说明盘面依据（引用边号或干支地址，如 `e014 寅申冲`、`M.b 月支`）",
        "",
        "**禁止骑墙**：不得使用「可能」「或许」「吉凶参半」。必须选一个。",
        "",
        "## 三、输出格式",
        "",
        "```json",
        "{",
        f'  "case_id": "{case}",',
        '  "year_judgments": [',
        '    {"year": 1999, "polarity": "吉", "matters": ["career"], "basis": "e005 寅午半合火局成"',
        "    },",
        "    ...",
        "  ]",
        "}",
        "```",
        "",
        "## 四、注意",
        "",
        "- 清单里既有**发生过大事的年份**，也有**什么也没发生的年份**（对照年）。",
        "  你无法从清单本身判断哪些是哪种——这正是要测的。",
        "- 判「平」同样重要：断准「这年没事」与断准「这年出事」同等计分。",
        "",
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / case).mkdir(exist_ok=True)
    (OUT / case / "probe.md").write_text("\n".join(lines), encoding="utf-8")

    # ── 真值（核验者专用）──
    key = {
        "case_id": case,
        "birth_year": by,
        "probe_years": probe_years,
        "truth": {},
        "notes": [
            "polarity 取自 feedback 事件文本的吉凶关键词分类，需人工复核",
            "对照年（无记录）polarity 记为 'undetermined'：按盲测铁律，"
            "「反馈未提及」不等于「实际未发生」，不得当作「平」的真值；"
            "判分时对照年不计入正确率分母，只统计误报倾向",
        ],
    }
    for y in probe_years:
        evs = [e for e in events if e["year"] == y]
        if evs:
            # 同年多条事件：取第一条非 mixed 的极性，全 mixed 则 mixed
            pols = [e["polarity"] for e in evs]
            pol = next((p for p in pols if p != "mixed"), "mixed")
            matters = sorted({m for e in evs for m in e["matters"]})
            key["truth"][str(y)] = {
                "polarity": pol,
                "matters": matters,
                "events": [e["text"][:80] for e in evs],
                "recorded": True,
            }
        else:
            # 对照年：反馈未记录 ≠ 实际未发生（项目铁律）。
            # 不能把「沉默」当「平稳」的真值——首轮盲测正是栽在这个错误上。
            # 因此对照年真值标 undetermined：判分时不计入正确率分母，
            # 只统计「是否被误判为凶」（误报倾向），这是可观测的。
            key["truth"][str(y)] = {
                "polarity": "undetermined",
                "matters": [],
                "events": [],
                "recorded": False,
            }
    (OUT / case / "answer_key.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OK   {case}: {len(probe_years)} 年（记录年 {len(recorded)} + 对照年 {len(control)}）")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="年份定向判断题生成器")
    ap.add_argument("--case")
    ap.add_argument("--from-json", type=Path)
    args = ap.parse_args(argv)

    cases = []
    if args.case:
        cases = [args.case]
    elif args.from_json:
        cases = [r["case"] for r in json.loads(args.from_json.read_text(encoding="utf-8"))]
    if not cases:
        ap.error("需要 --case 或 --from-json")

    ok = 0
    for c in cases:
        if build(c):
            ok += 1
    print(f"\n生成 {ok}/{len(cases)} 份年份判断题")
    print(f"题面：{OUT}/<case>/probe.md（盲断者可读）")
    print(f"真值：{OUT}/<case>/answer_key.json（核验者专用）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
