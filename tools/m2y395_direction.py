"""tools/m2y395_direction.py · T-151：M2-Y-395「夫妻宫被冲，谁制谁」题单重建（不读答案）。

本文件只做三件事：解析出生信息 → 建原局关系图 → 按预注册方向规则给每条「日支冲边」定方向。
它**不读题库的任何答案字段**（验收项：全文件不出现答案字段名字样），答案只在
``tools/m2y395_score.py`` 里并入。``find_trigger_question`` 只把题干与题号传出去，
题目对象（含答案）不出这个函数。

复用与来源（``tools/tiekoulu_eval.py`` 只读 import，未改动该文件）：
  - 解析：``parse_birth``（``tools/tiekoulu_eval.py``:108-136）——ADR-005 口径：优先
    ``line3_true_solar``，失败回退 ``line1_solar``(clock_beijing)，失败必带 reason。
  - 建盘：``analyze_facts(birth_dt=..., gender=...)``，与 ``tools/tiekoulu_eval.py``:291-324
    的 ``build_periods`` 是同一路径。**唯一差异**：``build_periods`` 用 ``if r.get("gender")``
    过滤（:294），本卡不能这么做——284 期里只有 36 期带性别标注。原局关系边只由四柱决定，
    性别只影响大运顺逆（``engine/facts/chart_facts.py``:476-488），故缺性别时用占位「乾」，
    并在每例标 ``gender_basis``；实测 284 期乾/坤两性别的原局边集完全相同
    （``META/m2y395-report-v1.md`` §5.3）。

预注册（``tasks/T-151/PROMPT.md`` §1.2–§1.4，Worker 不得改）：
  触发器  : 原局存在 ``kind=chong`` 的边，且成员含日支地址 ``D.b``（只看原局，``scope=natal``）
  方向    : 对每条冲边的另一支 ``other``，比较**本气五行**（``ZHI_TO_WUXING``）
            ``KE_MAP[wx(D.b)] == wx(other)``  → ``self_controls``（我制对方）
            ``KE_MAP[wx(other)] == wx(D.b)`` → ``other_controls``（对方制我）
            其余（含辰戌、丑未等同五行）      → ``no_ke``（无克，弃权）
  预测    : ``self_controls`` → ``["B"]``；``other_controls`` → ``["C","E"]``；
            ``no_ke`` / ``ambiguous`` → ``[]``
  计数单位: 一条 ``(D.b, other)`` 冲边 = 一例。同期多条冲边产出多例——PROMPT §1.5 的
            78 = 冲边数（不是期数）；期级对照见 ``tools/m2y395_score.py`` 产物与报告 §3.2。

事实来源：
  ``KE_MAP``        ``engine/predicates/types.py``:60-62
  ``ZHI_TO_WUXING`` ``engine/predicates/types.py``:73-79
  ``chong`` 建边    ``engine/facts/relation_graph.py``:210-222（``_CHONG`` 见 :53）

产物：``META/m2y395-cases-v1.json``
用法：``.venv\\Scripts\\python.exe -m tools.m2y395_direction``
退出码：0 = 重建完成；1 = 结构性失败（题库缺失 / 无任何可判定例）。
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import Counter
from typing import Any

from engine.api import analyze_facts
from engine.predicates.types import KE_MAP, ZHI_TO_WUXING
from tools.tiekoulu_eval import GENDER_MAP, parse_birth

ROOT = pathlib.Path(__file__).resolve().parents[1]
BANK = ROOT / "tiekoulu_1507_to_1428.json"
OUT = ROOT / "META" / "m2y395-cases-v1.json"

PROTOCOL_ID = "m2y395-v1"
TASK = "T-151"
TRIGGER_TEXT = "日主婚姻状况"
DAY_ADDR = "D.b"
PLACEHOLDER_GENDER = "乾"

PREDICTION_LETTERS: dict[str, list[str]] = {
    "self_controls": ["B"],
    "other_controls": ["C", "E"],
    "no_ke": [],
    "ambiguous": [],
}
BRANCHES = ("self_controls", "other_controls", "no_ke", "ambiguous")

DEFINITION = (
    "触发器=原局(kind=chong, scope=natal)且成员含 D.b 的边；"
    "方向=按 KE_MAP 比较 D.b 与 other 的本气五行（同五行/无克→no_ke）；"
    "预测=self_controls→B、other_controls→C/E、no_ke/ambiguous→弃权；"
    "计数单位=一条 (D.b, other) 冲边一例"
)

RE_NUM = re.compile(r"(\d+)")
RE_HAS_TIME = re.compile(r"\d{1,2}\s*[时点]\s*\d{1,2}\s*分?")


# ── 解析层 ──────────────────────────────────────────────────────────────

def load_bank() -> list[dict[str, Any]]:
    return json.loads(BANK.read_text(encoding="utf-8"))


def period_number(period: str) -> str:
    m = RE_NUM.search(str(period))
    return m.group(1) if m else ""


def find_trigger_questions(rec: dict[str, Any]) -> list[dict[str, Any]]:
    """只交出题号与题干；题目对象（含答案）不传出本函数。"""
    found: list[dict[str, Any]] = []
    for q in rec.get("questions") or []:
        text = str(q.get("question") or "")
        if TRIGGER_TEXT in text:
            found.append({"q_index": q.get("q_index"), "question": text})
    return found


def classify_parse_failure(rec: dict[str, Any]) -> str:
    """PROMPT §2.1 的四类：格式 / 缺时刻 / 农历转换 / 其他。"""
    info = rec.get("birth_info") or {}
    l1 = str(info.get("line1_solar") or "").strip()
    l3 = str(info.get("line3_true_solar") or "").strip()
    if not l1 and not l3:
        return "缺时刻"
    if not (RE_HAS_TIME.search(l1) or RE_HAS_TIME.search(l3)):
        return "缺时刻"
    if "农历" in l3 and not re.search(r"阳历|真太阳时", l3):
        return "农历转换"
    return "格式"


def classify_chart_failure(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}"
    if "农历" in text or "lunar" in text.lower():
        return "农历转换"
    return "其他"


# ── 方向层 ──────────────────────────────────────────────────────────────

def direction_of(day_wx: str, other_wx: str) -> str:
    """PROMPT §1.3 的三分支（顺序即优先级；五行克序是 5-循环，两条件不会同时成立）。"""
    if KE_MAP.get(day_wx) == other_wx:
        return "self_controls"
    if KE_MAP.get(other_wx) == day_wx:
        return "other_controls"
    return "no_ke"


def day_chong_edges(facts: dict[str, Any], skipped: list[dict[str, Any]],
                    period: str) -> list[dict[str, Any]]:
    """原局里成员含 D.b 的 chong 边，逐条给出方向。非二元边跳过并记录，不静默丢弃。"""
    edges: list[dict[str, Any]] = []
    for e in (facts.get("relations") or {}).get("edges") or []:
        if e.get("kind") != "chong" or e.get("scope") != "natal":
            continue
        members = tuple(e.get("members") or ())
        if DAY_ADDR not in members:
            continue
        if len(members) != 2:  # chong 定义为一对一；异常边记录后跳过
            skipped.append({"period": period, "edge_id": e.get("id"),
                            "reason": f"chong 边成员数 {len(members)} != 2"})
            continue
        i = members.index(DAY_ADDR)
        chars = tuple(e.get("chars") or ())
        day_char, other_char = chars[i], chars[1 - i]
        day_wx, other_wx = ZHI_TO_WUXING[day_char], ZHI_TO_WUXING[other_char]
        edges.append({
            "edge_id": e.get("id"),
            "other": other_char,
            "other_wx": other_wx,
            "direction": direction_of(day_wx, other_wx),
            "day_branch": day_char,
            "day_branch_wx": day_wx,
        })
    return edges


def build_cases(rec: dict[str, Any], parsed: dict[str, Any],
                facts: dict[str, Any], gender_basis: str,
                skipped: list[dict[str, Any]]) -> list[dict[str, Any]]:
    period = rec.get("period")
    edges = day_chong_edges(facts, skipped, period)
    if not edges:
        return []
    no = period_number(period)
    dirs = {e["direction"] for e in edges}
    period_dir = next(iter(dirs)) if len(dirs) == 1 else "ambiguous"
    chart_pillars = facts.get("chart", {}).get("pillars") or []
    pillars = " ".join(p["stem"]["char"] + p["branch"]["char"] for p in chart_pillars)
    day_branch = edges[0]["day_branch"]
    day_wx = edges[0]["day_branch_wx"]
    chong = [{k: e[k] for k in ("edge_id", "other", "other_wx", "direction")} for e in edges]
    cases: list[dict[str, Any]] = []
    for e in edges:
        case_id = (f"tiekoulu-{no}" if len(edges) == 1
                   else f"tiekoulu-{no}#{e['edge_id']}")
        cases.append({
            "case_id": case_id,
            "period": period,
            "period_no": no,
            "pillars": pillars,
            "day_branch": day_branch,
            "day_branch_wx": day_wx,
            "edge_id": e["edge_id"],
            "chong": chong,
            "direction": period_dir,
            "prediction_letters": list(PREDICTION_LETTERS[period_dir]),
            "n_chong_in_period": len(edges),
            "time_basis": parsed["time_basis"],
            "fallback": parsed["fallback"],
            "late_zi": parsed["hour"] == 23,
            "day_boundary_shift": bool(parsed["solar_date"] and parsed["clock_date"]
                                       and parsed["solar_date"] != parsed["clock_date"]),
            "gender_basis": gender_basis,
        })
    return cases


# ── 主流程 ──────────────────────────────────────────────────────────────

def main() -> int:
    if not BANK.exists():
        print(f"[FATAL] 题库缺失：{BANK}", file=sys.stderr)
        return 1
    bank = load_bank()
    parse_failures: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    missing_trigger: list[str] = []
    fallback_periods: list[str] = []
    late_zi: list[str] = []
    day_shift: list[str] = []
    basis_counts: Counter = Counter()
    n_with_q = 0

    for rec in bank:
        period = rec.get("period")
        questions = find_trigger_questions(rec)
        if not questions:
            missing_trigger.append(period)
            continue
        if len(questions) > 1:
            parse_failures.append({
                "period": period, "stage": "题面", "category": "其他",
                "reason": f"题干含「{TRIGGER_TEXT}」的题有 {len(questions)} 道，无法确定唯一题面",
            })
            continue
        n_with_q += 1
        parsed = parse_birth(rec)
        if not parsed["ok"]:
            parse_failures.append({
                "period": period, "stage": "解析",
                "category": classify_parse_failure(rec), "reason": parsed["reason"],
            })
            continue
        gender_cn = rec.get("gender")
        gender = GENDER_MAP.get(gender_cn) if gender_cn else None
        gender_basis = "bank" if gender else "placeholder"
        if gender is None:
            gender = PLACEHOLDER_GENDER
        try:
            facts = analyze_facts(birth_dt=parsed["dt"], gender=gender)
        except Exception as exc:  # noqa: BLE001 - 逐期记录原因，不许吞掉
            parse_failures.append({
                "period": period, "stage": "排盘",
                "category": classify_chart_failure(exc),
                "reason": f"{type(exc).__name__}: {exc}",
            })
            continue
        basis_counts[parsed["time_basis"]] += 1
        if parsed["fallback"]:
            fallback_periods.append(period)
        if parsed["hour"] == 23:
            late_zi.append(period)
        if parsed["solar_date"] and parsed["clock_date"] and parsed["solar_date"] != parsed["clock_date"]:
            day_shift.append(period)
        cases.extend(build_cases(rec, parsed, facts, gender_basis, skipped))

    if not cases:
        print("[FATAL] 没有任何可判定的日支冲边，无法产出题单", file=sys.stderr)
        for f in parse_failures:
            print(f"  {f}", file=sys.stderr)
        return 1

    cases.sort(key=lambda c: (int(c["period_no"]), c["edge_id"]))
    dir_counts = Counter(c["direction"] for c in cases)
    period_dirs: dict[str, str] = {}
    for c in cases:
        period_dirs[c["period"]] = c["direction"]
    period_dir_counts = Counter(period_dirs.values())
    failure_categories = Counter(f["category"] for f in parse_failures)

    payload = {
        "meta": {
            "protocol_id": PROTOCOL_ID,
            "task": TASK,
            "generated_by": "python -m tools.m2y395_direction",
            "data_source": "tiekoulu_1507_to_1428.json",
            "n_periods": len(bank),
            "n_periods_with_trigger_question": n_with_q,
            "n_periods_without_trigger_question": len(missing_trigger),
            "periods_without_trigger_question": missing_trigger,
            "n_parse_failed": len(parse_failures),
            "parse_failures_by_category": dict(sorted(failure_categories.items())),
            "n_cases": len(cases),
            "n_periods_with_chong": len(period_dirs),
            "case_unit": "冲边：一条 (D.b, other) 冲边 = 一例；同期多条冲边产出多例",
            "case_id_scheme": "tiekoulu-<期号>；同期多条冲边时追加 #<edge_id>",
            "direction_counts": {b: dir_counts.get(b, 0) for b in BRANCHES},
            "period_direction_counts": {b: period_dir_counts.get(b, 0) for b in BRANCHES},
            "time_basis": dict(sorted(basis_counts.items())),
            "gender_basis": {"bank": sum(1 for c in cases if c["gender_basis"] == "bank"),
                             "placeholder": sum(1 for c in cases if c["gender_basis"] == "placeholder")},
            "ke_map_source": "engine/predicates/types.py:60-62",
            "zhi_wuxing_source": "engine/predicates/types.py:73-79",
            "chong_edge_source": "engine/facts/relation_graph.py:210-222",
            "parser_source": "tools/tiekoulu_eval.py:108-136 (parse_birth)",
            "definition": DEFINITION,
            "notes": [
                "本文件不读题库答案；答案在 tools/m2y395_score.py 并入",
                "触发只看原局（scope=natal），不含大运/流年/天干冲",
                "缺性别标注的期用占位乾建盘；原局边与性别无关（见报告 §5.3）",
            ],
        },
        "parse_failures": parse_failures,
        "skipped_edges": skipped,
        "flag_periods": {
            "fallback_to_clock": fallback_periods,
            "late_zi": late_zi,
            "day_boundary_shift": day_shift,
        },
        "cases": cases,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("=" * 74)
    print("T-151 · M2-Y-395 题单重建（不读答案）")
    print("=" * 74)
    print(f"题库期数          : {len(bank)}")
    print(f"含婚姻题期数      : {n_with_q}"
          f"（缺题 {len(missing_trigger)} 期{('：' + '、'.join(missing_trigger)) if missing_trigger else ''}）")
    print(f"解析/排盘失败      : {len(parse_failures)}"
          f"（{', '.join(f'{k}={v}' for k, v in sorted(failure_categories.items())) or '无'}）")
    print(f"出生时刻口径      : " + ", ".join(f"{k}={v}" for k, v in sorted(basis_counts.items())))
    print(f"原局日支有冲      : {len(period_dirs)} 期")
    print(f"冲边（=例数）      : {len(cases)}")
    for b in BRANCHES:
        print(f"  {b:15s} : {dir_counts.get(b, 0)}")
    print("-" * 74)
    print(f"产物              : {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
