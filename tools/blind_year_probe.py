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


_PREFIX_POLARITY = re.compile(r"^\s*(凶|吉)\s*[,，]")


def classify(text: str) -> str:
    """事件文本极性分类。

    优先级设计（首轮判分踩过的坑）：
    1. **命主自报前缀优先**——feedback 事件文本以「凶,」/「吉,」开头，
       这是命主自己给这年定的性。正文关键词只是事件描述，不得翻盘
       （曾因把「吉,出国学习」里的「学习」当负面词计票，判成 negative）。
    2. 前缀缺失时回退关键词计票。
    3. 计票仍不判时记 mixed，不强行二选一。
    """
    m = _PREFIX_POLARITY.match(text)
    if m:
        return "negative" if m.group(1) == "凶" else "positive"
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


def _detect_columns(header_line: str) -> tuple[int, int]:
    """从表头行解析「事实文本列」与「功能域/类型列」的索引。

    feedback.md 存在两种表格式，列序相反：
      格式 A: | 年份 | 已知事实 | 功能域 |   → 文本=1, 域=2
      格式 B: | 年份 | 类型 | 事实摘录 |     → 域=1, 文本=2
    早期版本一律按 A 解析，导致格式 B 案例的「文本」只取到「其他/职业」
    这类类型标签，真值极性分类全废（194/253 事件受影响）。

    匹配优先级（避免同一单元格同时含两类关键词时误判）：
    1. 强特征：含「事实/摘录/事件」→ 文本列；含「功能域/类型/域」→ 域列
    2. 同一格同时命中两类时，按「文本优先」处理（文本列缺失代价远高于域列），
       但记录冲突原因，便于发现异常表头。
    3. 都无法识别 → 退回格式 A 的默认列（1, 2）。

    返回 (text_idx, domain_idx)。
    """
    cells = [c.strip() for c in header_line.strip().strip("|").split("|")]
    text_kw = ("事实", "摘录", "事件", "描述")
    dom_kw = ("功能域", "类型", "域", "类别")

    text_cands, dom_cands = [], []
    for i, c in enumerate(cells):
        hit_text = any(k in c for k in text_kw)
        hit_dom = any(k in c for k in dom_kw)
        if hit_text:
            text_cands.append((i, len(c)))
        if hit_dom:
            dom_cands.append((i, len(c)))

    # 冲突处理：某格同时是两类候选 → 归文本（文本缺失导致真值全废，
    # 域列缺失只影响 matters 统计，代价低得多）
    both = {i for i, _ in text_cands} & {i for i, _ in dom_cands}
    if both:
        dom_cands = [(i, n) for i, n in dom_cands if i not in both]

    text_idx = text_cands[0][0] if text_cands else 1
    dom_idx = dom_cands[0][0] if dom_cands else (2 if text_idx == 1 else 1)
    if dom_idx == text_idx:                      # 兜底：绝不让两列重合
        dom_idx = 2 if text_idx != 2 else 1
    return text_idx, dom_idx


def load_events(case: str) -> list[dict[str, Any]]:
    p = CASES / case / "feedback.md"
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8-sig", errors="replace").splitlines()

    # 先定位表头，确定列序
    text_idx, dom_idx = 1, 2
    for line in lines:
        if "年份" in line and line.strip().startswith("|"):
            text_idx, dom_idx = _detect_columns(line)
            break

    out = []
    for line in lines:
        m = _EVENT_ROW.match(line.strip())
        if not m:
            continue
        y = m.group(1)
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        text = cells[text_idx] if text_idx < len(cells) else m.group(2)
        dom = cells[dom_idx] if dom_idx < len(cells) else m.group(3)
        doms = [d.strip() for d in re.split(r"[,，]", dom) if d.strip()]
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
        "## 二、作答要求（每年必须给出四项）",
        "",
        "1. **领域**：`matters` —— 该年谁被引动、应事落在哪个领域",
        "   （印动=学业/单位名分；禄动=身体；妻/夫星宫动=婚恋；",
        "    杀库动=工作变动；财动=财）**领域判错则该年作废**",
        "2. **运级基调**：`dayun_tone` —— 先用一句话定大运对该年的基调",
        "   （运干贴身克体？运支被穿？运合妻星？），流年只做应期修正",
        "3. **吉凶**：`吉` / `凶` / `平` 三选一",
        "4. **依据**：`basis` —— 盘面依据，**必须用「地址ID＋干支＋关系名」**",
        "   格式（如 `H.b午×LN.b子 冲`、`M.b寅 三合火局 full`），",
        "   **禁用 e### 边号**（边 ID 每次叠加岁运参数即整体重编号，凡引必错位）",
        "",
        "**禁止骑墙**：不得使用「可能」「或许」「吉凶参半」。必须选一个。",
        "",
        "## 二之二、五道前置关（缺一不得下断）",
        "",
        "诊断 4 个低分案例的 21 个错误，**86% 是「规则在库、但删掉前提条件就套断语」**。",
        "规则本身没错、方向也常对，错在跳过了下面五关中的某一关。",
        "逐关自检，任何一关未过就不得输出吉凶：",
        "",
        "**第 1 关 · 领域判定**：这一年究竟「动」在什么事上？",
        "先答领域，再判吉凶。领域错配 → 该年作答作废。",
        "",
        "**第 2 关 · 运级定位**：大运对这个年的基调是什么？",
        "禁止跳过大运、直接从流年干支组合推吉凶。",
        "（诊断发现 RF000244 连续 3 年方向判反，根因就是从不看大运定基调）",
        "",
        "**第 3 关 · 成度三问**：凡引用合局/半合/拱，必须回答：",
        "①是 full / half / gong？②中神是否现、是否空亡？③成局之物为我所用还是攻体？",
        "三问不全，**不得引用「合成=圆满」类规则**。",
        "",
        "**第 4 关 · 倾向规则条件复述**：",
        "引「必凶」类规则时，必须复述该规则原文的**全部前提**并逐条对盘；",
        "引「必吉」类规则时同样。**两侧都是「条件复述不齐＝不得下断」**。",
        "（42 条倾向规则全部命中「删条件套断语」形态）",
        "",
        "**第 5 关 · 漏边反向扫描**：下结论前做一次反向检查：",
        "- 要断**凶** → 是否存在合绊 / 通关 / 合解冲的**救应**？",
        "  （诊断发现多处漏看「巳申先合解寅申冲」这类救应）",
        "- 要断**吉** → 制神/用神是否被合、被克、被合化？",
        "  查 `facts_all.json` 的 `wuhe` 边是否带 `huashen_ke_stems` / `huashen_stem_tou`",
        "",
        "## 二之三、判「平」的条件（收窄）",
        "",
        "答平之前必须**双侧正查**：",
        "① 给出「若判吉的最强证据」",
        "② 给出「若判凶的最强证据」",
        "③ 说明两者为何都不足",
        "",
        "**仅「没看到实质损伤」不构成答平理由。**",
        "盘面有冲刑合会穿/开库/填实/伏吟反吟等引动时，必须给方向。",
        "",
        "## 二之四、常态边不入断",
        "",
        "原局已有的克/冲/穿边（如群劫克财）**不得**作为流年新增凶讯引用，",
        "除非流年对该边有实质加力（透干/填实/引动）。",
        "",
        "## 二之五、库多穿多盘提高门槛",
        "",
        "若原局库 ≥2 或穿 ≥2，凡**吉断**须额外通过「宫库是否被刑冲穿动」检查。",
        "（诊断发现 4 例低分盘动宫库之年 9/10 判反）",
        "",
        "## 三、输出格式",
        "",
        "```json",
        "{",
        f'  "case_id": "{case}",',
        '  "year_judgments": [',
        '    {"year": 1999, "polarity": "吉", "matters": ["career"],',
        '     "dayun_tone": "乙卯运印星贴身，基调偏吉，主名分",',
        '     "basis": "M.b寅 三合火局 full，用神得地；H.b午填实"',
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
        "- 判「平」不是免罪符：**盘面有明确引动时必须判吉或凶**。具体地说，",
        "  若该年被流年/大运与原局构成冲、刑、合、会、穿、开库、填实、",
        "  伏吟、反吟中的任一种，就属于「有引动」，必须给出吉或凶方向；",
        "  只有全局无任何引动（流年干支与原局既不冲刑合会也无生克引动）",
        "  才可判「平」。",
        "- 第 2 批数据显示：真值有明确方向的年份里，有 31 次作答为「平」，",
        "  这在实际判分中等于弃权。请把这当成一次明确的判断，而不是安全选项。",
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
