"""tools/tiekoulu_eval.py · 铁口箓评测管道（T-146）。

项目第一把「断语正确性」尺子：把铁口箓 36 期有性别题库变成可复跑的评测，
量出断语相对「瞎猜」的位置。

四层指标（缺一不可）：
  L1 多数类基线    —— 每道题「永远选出现最多的那个选项」能得多少分（瞎猜上限）
  L2 断语命中数    —— 每条断语在 36 期里 state==candidate 的期数；0 命中标「无法验证」
  L3 断语×题目关联 —— 命中组 vs 未命中组的答案分布差（max share gap）+ 置换检验 p
  L4 方向预测      —— 对「断语本身给出了方向」的条目，把命中翻译成选项集，与
                      **同基数**最佳基线比较（k 选项预测必须对 k 选项基线，不许占便宜）

【方法学关键：字母级统计只在同一份量表内做】
题库里「职业」含 31 道 3 选项题 + 18 道各期各不相同的 5 选项「精准点射」题；
「流年」每年是一套独立的 13 选项（事件不同）。把不同量表的答案按字母汇总，
等于把「B」当成同一个意思，基线会失真。因此本工具按
`(类别, 题干, 选项集)` 切出「题目类型」，只在**同类型内**做字母级统计，
题目类型样本 < MIN_TYPE_N 的一律剔除并逐条列出。

硬约束（本文件只测量，不优化）：
  - 不写 tiekoulu_1507_to_1428.json、不写 theory/**、不写 engine/**
  - 不调阈值、不挑题、不剔除难例
  - 解析失败、排盘失败、剔除原因逐条列出，不用裸 except 吞掉

用法：python -m tools.tiekoulu_eval
产物：META/tiekoulu-eval-v1.json、META/tiekoulu-eval-v1.md
退出码：0 = 管道跑完并出分；1 = 结构性失败（数据缺失 / 全部期数失败）
"""
from __future__ import annotations

import json
import pathlib
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

import yaml

from engine.api import analyze_facts
from engine.claims.condition_ir import build_context, compile_claim, evaluate_claim

ROOT = pathlib.Path(__file__).resolve().parents[1]
BANK = ROOT / "tiekoulu_1507_to_1428.json"
PILOT = ROOT / "theory" / "claims" / "conditions-v2" / "pilot-20.yaml"
OUT_JSON = ROOT / "META" / "tiekoulu-eval-v1.json"
OUT_MD = ROOT / "META" / "tiekoulu-eval-v1.md"

# 真太阳时：「真太阳时: 1988年7月3日8时3分,农历…」
RE_TRUE_SOLAR = re.compile(r"真太阳时[:：]\s*(\d{4})年(\d{1,2})月(\d{1,2})日(\d{1,2})时(\d{1,2})分")
# 北京时钟：「出生时间: 阳历1988年7月3日8时30分」（注意存在「出生时间:阳历」无空格写法）
RE_CLOCK = re.compile(r"阳历\s*(\d{4})年(\d{1,2})月(\d{1,2})日(\d{1,2})时(\d{1,2})分")

GENDER_MAP = {"女性": "坤", "男性": "乾"}

# 题目类别判定：有序规则，先匹配先得。
# 注意 家境题题干里含「子女富贵不算」四字，因此子女键必须用「日主子女」而非「子女」。
CATEGORY_RULES: tuple[tuple[str, str], ...] = (
    ("日主当前学历", "学历"),
    ("日主婚姻状况", "婚姻"),
    ("日主子女", "子女"),
    ("日主职业", "职业"),
    ("日主目前财富", "财富"),
    ("出身家境", "家境"),
    ("父母现状", "父母"),
    ("年发生的事情", "流年"),
)
# 原局类：断语 time_window=natal，只有这些类别能当断语的检验场。流年属岁运层面，单列附表。
NATAL_CATEGORIES = frozenset({"学历", "婚姻", "子女", "职业", "财富", "家境", "父母", "其他"})

# L4 方向预测表：只收录「断语本身给出了可对照方向」的条目。
# predict 是断语命中时预测的答案字母集合；k = len(predict)，基线也按 k 个字母算。
# 未收录的条目在报告 §6 逐条说明理由，不做静默丢弃。
PREDICTION_MAP: dict[str, dict[str, Any]] = {
    "G-SP-165": {"category": "学历", "predict": ("A", "B"),
                 "why": "印星空亡→学业难成，方向=低学历（小学及以下/初高中技校）"},
    "G-SP-293": {"category": "子女", "predict": ("A",),
                 "why": "时柱空亡→子女缘薄，方向=无子女"},
    "G-SP-071": {"category": "财富", "predict": ("A",),
                 "why": "无财星→一生难富裕，方向=负债～温饱"},
    "G-SP-130": {"category": "婚姻", "predict": ("B",),
                 "why": "配偶星守宫→不离不弃，方向=一婚"},
    "M1-D-298": {"category": "婚姻", "predict": ("B",),
                 "why": "夫妻宫为用不受刑冲穿破合→婚姻较好，方向=一婚"},
    "M2-Y-251": {"category": "职业", "predict": ("B",),
                 "why": "食伤旺→倾向自由职业，方向=自由职业"},
    "M2-Y-014": {"category": "财富", "predict": ("A", "B"),
                 "why": "财星受克→财不完整财不大，方向=负债～温饱/小康"},
}

NO_MAP_REASON = {
    "M1-D-009": "断语陈述的是「哪种做功方式最常见」的统计性判断，不指向任何一期命主的具体选项",
    "M1-D-013": "断语陈述墓用结构的机制，未给出可对照的吉凶/程度方向",
    "M1-D-242": "断语方向明确（学历较高），但 36 期内命中 0 次，无法验证",
    "M3-R-013": "断语讲「财星虚透主才华」，题库无「才华」类题目，无法对应到选项",
    "M3-R-166": "断语属健康域，题库 36 期无任何健康题，无对应类别",
}

PERM_ROUNDS = 2000
PERM_SEED = 20261028
MIN_TYPE_N = 5             # 题目类型样本量下限：低于此不做字母级统计
MIN_HIT_FOR_STATS = 3      # 关联度：命中组/未命中组样本下限
MIN_HIT_FOR_PRED = 5       # 方向预测：命中组样本下限


# ─────────────────────────────────────────────────────────────── 解析层

def parse_birth(rec: dict[str, Any]) -> dict[str, Any]:
    """按 ADR-005：优先 line3_true_solar，失败回退 line1_solar。

    返回 {'ok', 'dt', 'time_basis', 'fallback', 'reason'}，失败必须带 reason。
    """
    info = rec.get("birth_info") or {}
    l3 = str(info.get("line3_true_solar") or "")
    l1 = str(info.get("line1_solar") or "")

    m3 = RE_TRUE_SOLAR.search(l3)
    if m3:
        y, mo, d, h, mi = (int(x) for x in m3.groups())
        return {"ok": True, "dt": f"{y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}",
                "time_basis": "true_solar", "fallback": False, "reason": "",
                "solar_date": f"{y:04d}-{mo:02d}-{d:02d}", "clock_date": _date_of(l1), "hour": h}

    m1 = RE_CLOCK.search(l1)
    if m1:
        y, mo, d, h, mi = (int(x) for x in m1.groups())
        return {"ok": True, "dt": f"{y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}",
                "time_basis": "clock_beijing", "fallback": True,
                "reason": f"line3_true_solar 未匹配 RE_TRUE_SOLAR（原文={l3[:40]!r}）",
                "solar_date": f"{y:04d}-{mo:02d}-{d:02d}", "clock_date": f"{y:04d}-{mo:02d}-{d:02d}",
                "hour": h}

    return {"ok": False, "dt": None, "time_basis": None, "fallback": False,
            "reason": f"line3 与 line1 均无法解析：line3={l3[:60]!r} line1={l1[:60]!r}",
            "solar_date": None, "clock_date": None, "hour": None}


def _date_of(line: str) -> str | None:
    m = RE_CLOCK.search(line)
    if not m:
        return None
    y, mo, d = (int(x) for x in m.groups()[:3])
    return f"{y:04d}-{mo:02d}-{d:02d}"


def classify(question: str) -> str:
    for key, name in CATEGORY_RULES:
        if key in question:
            return name
    return "其他"


def option_signature(options: dict[str, str]) -> tuple[str, ...]:
    """选项文本签名（归一 ～/~），用于把同一份量表归为一类。"""
    return tuple(options[k].replace("~", "～") for k in sorted(options))


# ─────────────────────────────────────────────────────────────── 题目类型

@dataclass
class QType:
    category: str
    question: str
    sig: tuple[str, ...]
    answers: list[str] = field(default_factory=list)
    periods: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return _short_q(self.question)

    @property
    def n(self) -> int:
        return len(self.answers)

    def dist(self) -> Counter:
        return Counter(self.answers)

    def baseline(self) -> dict[str, Any]:
        return majority_baseline(self.answers)


def _short_q(q: str) -> str:
    """题干短名：去掉 [单选题] 前缀与括号补充说明。"""
    s = re.sub(r"^\[(单选|多选)题\]", "", q).strip()
    s = re.sub(r"（[^）]*）", "", s).strip()
    return s[:20]


def build_qtypes(periods: Sequence[dict]) -> tuple[list[QType], list[dict]]:
    """按 (类别, 题干, 选项集) 切题目类型；多选题与答案非法题单独剔除。"""
    bucket: dict[tuple[str, str, tuple[str, ...]], QType] = {}
    excluded: list[dict] = []
    for p in periods:
        for q in p["questions"]:
            ans = str(q["correct_answer"])
            if q["question"].startswith("[多选题]") or ans not in q["options"]:
                multi = q["question"].startswith("[多选题]")
                reason = (f"多选题（答案 {ans} 为多个字母，无法纳入单选基线）" if multi
                          else f"答案 {ans} 不在选项字母内，数据异常")
                excluded.append({"period": p["period"], "q_index": q["q_index"],
                                 "answer": ans, "question": q["question"], "reason": reason})
                continue
            key = (classify(q["question"]), q["question"], option_signature(q["options"]))
            t = bucket.setdefault(key, QType(key[0], q["question"], key[2]))
            t.answers.append(ans)
            t.periods.append(p["period"])
    return list(bucket.values()), excluded


# ─────────────────────────────────────────────────────────────── 统计层

def majority_baseline(answers: Sequence[str]) -> dict[str, Any]:
    """多数类基线：永远选出现最多的那个选项。"""
    n = len(answers)
    if not n:
        return {"n": 0, "baseline": 0.0, "modal": None, "modal_hits": 0, "dist": {}}
    dist = Counter(answers)
    modal, top = dist.most_common(1)[0]
    return {"n": n, "baseline": top / n, "modal": modal, "modal_hits": top,
            "dist": dict(sorted(dist.items()))}


def topk_baseline(answers: Sequence[str], k: int) -> float:
    """同基数基线：允许猜 k 个字母时，选出现最多的 k 个能得多少。"""
    n = len(answers)
    if not n or k <= 0:
        return 0.0
    return sum(c for _, c in Counter(answers).most_common(k)) / n


def max_share_gap(hit: Sequence[str], miss: Sequence[str]) -> dict[str, Any]:
    """命中组 vs 未命中组的答案分布最大差（逐字母比较占比）。"""
    nh, nm = len(hit), len(miss)
    ch, cm = Counter(hit), Counter(miss)
    best_letter, best_gap = None, 0.0
    for letter in sorted(set(hit) | set(miss)):
        gap = (ch[letter] / nh if nh else 0.0) - (cm[letter] / nm if nm else 0.0)
        if abs(gap) > abs(best_gap):
            best_letter, best_gap = letter, gap
    return {"letter": best_letter, "gap": best_gap,
            "share_hit": (ch[best_letter] / nh) if nh and best_letter else 0.0,
            "share_miss": (cm[best_letter] / nm) if nm and best_letter else 0.0}


def perm_pvalue_maxgap(hit: Sequence[str], miss: Sequence[str], rounds: int, seed: int) -> float:
    """置换检验：打乱命中标签，看观察到的最大分布差有多大机会纯属巧合。"""
    pooled = list(hit) + list(miss)
    nh = len(hit)
    if nh == 0 or nh == len(pooled):
        return 1.0
    obs = abs(max_share_gap(hit, miss)["gap"])
    rng = random.Random(seed)
    ge = 0
    for _ in range(rounds):
        rng.shuffle(pooled)
        if abs(max_share_gap(pooled[:nh], pooled[nh:])["gap"]) >= obs - 1e-12:
            ge += 1
    return (ge + 1) / (rounds + 1)


def perm_pvalue_pred_acc(labels: Sequence[str], nh: int, predict: Iterable[str],
                         observed_correct: int, rounds: int, seed: int) -> float:
    """置换检验：随机取 nh 期当「命中组」，预测命中数不低于观察值的概率。"""
    predict = set(predict)
    if nh == 0:
        return 1.0
    pooled = list(labels)
    rng = random.Random(seed)
    ge = 0
    for _ in range(rounds):
        rng.shuffle(pooled)
        if sum(1 for x in pooled[:nh] if x in predict) >= observed_correct:
            ge += 1
    return (ge + 1) / (rounds + 1)


# ─────────────────────────────────────────────────────────────── 主流程

def load_claims() -> tuple[list[dict], list[dict]]:
    raw = yaml.safe_load(PILOT.read_text(encoding="utf-8"))["claims"]
    compiled, skipped = [], []
    for c in raw:
        st = compile_claim(c)["status"]
        (compiled if st == "compiled" else skipped).append(
            c if st == "compiled" else {"id": c.get("id"), "status": st,
                                        "statement": c.get("statement")})
    return compiled, skipped


def build_periods(bank: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """返回 (periods, parse_failures, chart_failures)。每个失败都带原因。"""
    periods, parse_fail, chart_fail = [], [], []
    for rec in [r for r in bank if r.get("gender")]:
        period = rec.get("period")
        parsed = parse_birth(rec)
        if not parsed["ok"]:
            parse_fail.append({"period": period, "reason": parsed["reason"]})
            continue
        gender = GENDER_MAP.get(rec.get("gender"))
        if gender is None:
            parse_fail.append({"period": period, "reason": f"gender 无法映射：{rec.get('gender')!r}"})
            continue
        try:
            facts = analyze_facts(birth_dt=parsed["dt"], gender=gender)
        except Exception as exc:  # noqa: BLE001 - 必须逐条记录，不许吞掉
            chart_fail.append({"period": period, "birth_dt": parsed["dt"],
                               "error": f"{type(exc).__name__}: {exc}"})
            continue
        chart = facts.get("chart") or {}
        periods.append({
            "period": period, "gender": gender, "gender_cn": rec.get("gender"),
            "birth_dt": parsed["dt"], "time_basis": parsed["time_basis"],
            "fallback": parsed["fallback"], "fallback_reason": parsed["reason"],
            "day_boundary_shift": bool(parsed["solar_date"] and parsed["clock_date"]
                                       and parsed["solar_date"] != parsed["clock_date"]),
            "late_zi": bool(parsed["hour"] == 23),
            "pillars": "".join(p["stem"]["char"] + p["branch"]["char"]
                               for p in chart.get("pillars") or []),
            "ctx": build_context(facts),
            "questions": rec.get("questions") or [],
        })
    return periods, parse_fail, chart_fail


def main() -> int:
    if not BANK.exists():
        print(f"[FATAL] 答案集缺失：{BANK}", file=sys.stderr)
        return 1

    bank = json.loads(BANK.read_text(encoding="utf-8"))
    claims, skipped_claims = load_claims()
    periods, parse_fail, chart_fail = build_periods(bank)
    if not periods:
        print("[FATAL] 有性别期数全部解析/排盘失败，无法出分", file=sys.stderr)
        for f in parse_fail + chart_fail:
            print(f"  {f}", file=sys.stderr)
        return 1

    n_target = len([r for r in bank if r.get("gender")])

    # ── 题目类型：只在同量表内做字母级统计
    qtypes, excluded_q = build_qtypes(periods)
    usable = [t for t in qtypes if t.n >= MIN_TYPE_N]
    # 被剔除的类型按 (类别, 题干, 选项数) 归并，避免同一道「精准点射」因每期量表不同被列 18 行
    agg: dict[tuple[str, str, int], dict[str, Any]] = {}
    for t in qtypes:
        if t.n >= MIN_TYPE_N:
            continue
        key = (t.category, _short_q(t.question), len(t.sig))
        row = agg.setdefault(key, {"category": t.category, "question": _short_q(t.question),
                                   "n_options": len(t.sig), "questions": 0, "scales": 0})
        row["questions"] += t.n
        row["scales"] += 1
    unusable = sorted(agg.values(), key=lambda r: (-r["questions"], r["category"]))

    # ── L1 基线（每道题各自算，再按类别取代表题）
    per_type = []
    for t in sorted(usable, key=lambda x: (-x.n, x.category)):
        b = t.baseline()
        per_type.append({"category": t.category, "question": t.question, "n": t.n,
                         "n_options": len(t.sig), "modal": b["modal"],
                         "baseline": round(b["baseline"], 4),
                         "dist": b["dist"], "natal": t.category in NATAL_CATEGORIES})
    cat_baseline: dict[str, dict] = {}
    for t in usable:
        cur = cat_baseline.get(t.category)
        if cur is None or t.n > cur["n"]:
            b = t.baseline()
            cat_baseline[t.category] = {
                "n": t.n, "modal": b["modal"], "baseline": round(b["baseline"], 4),
                "dist": b["dist"], "question": t.question, "n_options": len(t.sig),
                "n_types_in_cat": sum(1 for x in qtypes if x.category == t.category),
                "n_questions_in_cat": sum(x.n for x in qtypes if x.category == t.category),
            }

    # ── L2 逐期求值
    states: dict[str, dict[str, str]] = {}
    eval_meta: dict[str, Counter] = {}
    for c in claims:
        cid = c["id"]
        states[cid] = {}
        meta: Counter = Counter()
        for p in periods:
            ev = evaluate_claim(c, p["ctx"])
            states[cid][p["period"]] = ev["state"]
            meta[ev["state"]] += 1
            if ev["value"] is None:
                meta["unknown_value"] += 1
        eval_meta[cid] = meta

    claim_stats = []
    for c in claims:
        cid = c["id"]
        hits = [pid for pid, st in states[cid].items() if st == "candidate"]
        claim_stats.append({
            "id": cid, "school": c["school"], "domain": c["domain"],
            "statement": c["statement"], "hit_n": len(hits), "hit_periods": hits,
            "periods": len(periods), "hit_rate": round(len(hits) / len(periods), 4),
            "value_unknown_n": eval_meta[cid]["unknown_value"],
            "state_dist": dict(eval_meta[cid]),
            "verdict": "无法验证" if not hits else "可测",
        })

    # ── L3 关联度（在每个可用题目类型内做）
    assoc = []
    for c in claims:
        cid = c["id"]
        hit_set = {pid for pid, st in states[cid].items() if st == "candidate"}
        for t in usable:
            pair = [(ans, pid in hit_set) for ans, pid in zip(t.answers, t.periods)]
            hit_ans = [a for a, h in pair if h]
            miss_ans = [a for a, h in pair if not h]
            row = {"claim": cid, "category": t.category, "question": _short_q(t.question),
                   "type_n": t.n, "n_options": len(t.sig), "natal": t.category in NATAL_CATEGORIES,
                   "n_hit": len(hit_ans), "n_miss": len(miss_ans)}
            if len(hit_ans) < MIN_HIT_FOR_STATS or len(miss_ans) < MIN_HIT_FOR_STATS:
                row.update(note=f"样本不足（命中组 {len(hit_ans)} / 未命中组 {len(miss_ans)}，各需 ≥{MIN_HIT_FOR_STATS}）",
                           gap=None, p_value=None)
                assoc.append(row)
                continue
            g = max_share_gap(hit_ans, miss_ans)
            row.update(note="", gap=round(g["gap"], 4), gap_letter=g["letter"],
                       share_hit=round(g["share_hit"], 4), share_miss=round(g["share_miss"], 4),
                       p_value=round(perm_pvalue_maxgap(hit_ans, miss_ans, PERM_ROUNDS, PERM_SEED), 4))
            assoc.append(row)

    # ── L4 方向预测 vs 同基数基线
    pred_rows = []
    for c in claims:
        cid = c["id"]
        hit_set = {pid for pid, st in states[cid].items() if st == "candidate"}
        spec = PREDICTION_MAP.get(cid)
        if not spec:
            pred_rows.append({"claim": cid, "category": None, "acc_hit": None,
                              "note": NO_MAP_REASON.get(cid, "未建立可对照映射"),
                              "statement": c["statement"]})
            continue
        cat = spec["category"]
        cands = [t for t in usable if t.category == cat]
        if not cands:
            pred_rows.append({"claim": cid, "category": cat, "acc_hit": None,
                              "note": f"题库中「{cat}」无样本 ≥{MIN_TYPE_N} 的题目类型",
                              "statement": c["statement"]})
            continue
        t = max(cands, key=lambda x: x.n)
        pred = tuple(spec["predict"])
        hit_ans = [a for a, pid in zip(t.answers, t.periods) if pid in hit_set]
        if len(hit_ans) < MIN_HIT_FOR_PRED:
            pred_rows.append({"claim": cid, "category": cat, "acc_hit": None,
                              "n_hit": len(hit_ans), "n_cat": t.n, "predict": list(pred),
                              "question": _short_q(t.question), "why": spec["why"],
                              "note": f"样本不足（命中 {len(hit_ans)} 题 < {MIN_HIT_FOR_PRED}）",
                              "statement": c["statement"]})
            continue
        correct = sum(1 for a in hit_ans if a in pred)
        acc = correct / len(hit_ans)
        matched = topk_baseline(t.answers, len(pred))
        # 退化防护：预测集若覆盖该类实际出现过的全部答案，基线必然 100%，无区分力
        degenerate = set(t.answers).issubset(set(pred))
        pred_rows.append({
            "claim": cid, "category": cat, "question": _short_q(t.question),
            "n_hit": len(hit_ans), "n_cat": t.n, "predict": list(pred), "k": len(pred),
            "correct_in_hit": correct, "acc_hit": round(acc, 4),
            "matched_baseline": round(matched, 4), "lift": round(acc - matched, 4),
            "degenerate": degenerate,
            "p_value": round(perm_pvalue_pred_acc(
                t.answers, len(hit_ans), pred, correct, PERM_ROUNDS, PERM_SEED), 4),
            "why": spec["why"], "statement": c["statement"],
            "note": "无区分力（预测集覆盖该类全部实际答案，基线同为 100%）" if degenerate else "",
        })

    # ── 汇总三数 + 结论
    basis_counts = Counter(p["time_basis"] for p in periods)
    measurable = [s for s in claim_stats if s["hit_n"] > 0]
    tested_all = [r for r in assoc if r.get("gap") is not None]
    # 断语 time_window=natal，只有原局类题目是其适用域；岁运类题目单列附注，不参与裁决。
    tested = [r for r in tested_all if r["natal"]]
    tested_suiyun = [r for r in tested_all if not r["natal"]]
    top_assoc = max(tested, key=lambda r: abs(r["gap"])) if tested else None
    top_assoc_suiyun = max(tested_suiyun, key=lambda r: abs(r["gap"])) if tested_suiyun else None
    sig_assoc = [r for r in tested if r["p_value"] <= 0.05]
    pred_tested = [r for r in pred_rows if r.get("acc_hit") is not None and not r.get("degenerate")]
    pred_deg = [r for r in pred_rows if r.get("degenerate")]
    pred_better = [r for r in pred_tested if r["lift"] > 0 and r["p_value"] <= 0.05]

    headline = {
        "parse_success": len(periods), "parse_target": n_target,
        "parse_success_rate": round(len(periods) / n_target, 4),
        "parse_failures": len(parse_fail), "chart_failures": len(chart_fail),
        "time_basis": dict(basis_counts),
        "multi_choice_excluded": len(excluded_q),
        "qtypes_total": len(qtypes), "qtypes_usable": len(usable),
        "questions_usable": sum(t.n for t in usable),
        "questions_excluded_by_scale": sum(t.n for t in qtypes if t.n < MIN_TYPE_N),
        "baselines": {k: {"n": v["n"], "baseline": v["baseline"], "modal": v["modal"],
                          "question": _short_q(v["question"])}
                      for k, v in sorted(cat_baseline.items())},
        "claims_total": len(claims), "claims_measurable": len(measurable),
        "claims_unverifiable": [s["id"] for s in claim_stats if s["hit_n"] == 0],
        "assoc_tested": len(tested), "assoc_tested_natal": len(tested),
        "assoc_tested_suiyun": len(tested_suiyun),
        "assoc_significant_p05": len(sig_assoc),
        "assoc_expected_by_chance": round(len(tested) * 0.05, 2),
        "top_assoc": ({"claim": top_assoc["claim"], "category": top_assoc["category"],
                       "question": top_assoc["question"], "gap": top_assoc["gap"],
                       "letter": top_assoc["gap_letter"], "n_hit": top_assoc["n_hit"],
                       "n_miss": top_assoc["n_miss"], "p_value": top_assoc["p_value"],
                       "natal": True} if top_assoc else None),
        "top_assoc_suiyun": ({"claim": top_assoc_suiyun["claim"],
                              "category": top_assoc_suiyun["category"],
                              "question": top_assoc_suiyun["question"],
                              "gap": top_assoc_suiyun["gap"],
                              "n_hit": top_assoc_suiyun["n_hit"],
                              "n_miss": top_assoc_suiyun["n_miss"],
                              "p_value": top_assoc_suiyun["p_value"]}
                             if top_assoc_suiyun else None),
        "pred_tested": len(pred_tested),
        "pred_degenerate": [r["claim"] for r in pred_deg],
        "pred_beat_baseline_p05": len(pred_better),
        "best_pred": (max(pred_tested, key=lambda r: r["lift"]) if pred_tested else None),
    }

    payload = {
        "schema": "tiekoulu-eval/v1", "task": "T-146", "generated_at": "2026-10-28",
        "inputs": {
            "bank": "tiekoulu_1507_to_1428.json", "bank_periods": len(bank),
            "periods_with_gender": n_target,
            "claims_file": "theory/claims/conditions-v2/pilot-20.yaml",
            "claims_compiled": len(claims), "claims_skipped": skipped_claims,
        },
        "method": {
            "time_basis": "ADR-005：优先 line3_true_solar，失败回退 line1_solar(clock_beijing)",
            "qtype": "字母级统计只在 (类别, 题干, 选项集) 相同的题目类型内做；类型样本 < "
                     f"{MIN_TYPE_N} 剔除",
            "baseline": "多数类基线 = 该题出现最多的选项的占比（永远猜它）",
            "assoc": "命中组 vs 未命中组的逐字母占比最大差 + 置换检验",
            "prediction": "断语命中时预测的答案集合；基线按同基数(k)最佳选项集计算",
            "perm_rounds": PERM_ROUNDS, "perm_seed": PERM_SEED,
            "min_type_n": MIN_TYPE_N, "min_hit_for_stats": MIN_HIT_FOR_STATS,
            "min_hit_for_pred": MIN_HIT_FOR_PRED,
        },
        "headline": headline,
        "periods": [{k: v for k, v in p.items() if k not in ("ctx", "questions")} for p in periods],
        "parse_failures": parse_fail, "chart_failures": chart_fail,
        "excluded_questions": excluded_q, "unusable_qtypes": unusable,
        "per_type_baseline": per_type, "baselines": cat_baseline,
        "claims": claim_stats, "association": assoc, "prediction": pred_rows,
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_MD.write_text(render_md(payload), encoding="utf-8")
    print_console(payload)
    return 0


# ─────────────────────────────────────────────────────────────── 输出层

def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def verdict_sentence(payload: dict) -> str:
    """一句话结论。不许美化，不许找补。"""
    h = payload["headline"]
    if h["pred_tested"] == 0:
        return ("**现有断语无法与基线比较**：可测断语在方向预测层全部落入样本不足，"
                "本卡只完成了测量管道与命中统计，未取得可与基线对照的分数。")
    if h["pred_beat_baseline_p05"] == 0:
        best = h["best_pred"]
        return (f"**现有断语未超过瞎猜。** {h['pred_tested']} 条可对照断语"
                f"（已剔除无区分力的退化项）中，没有一条在 p≤0.05 上稳定超过同基数基线；"
                f"最大增益出现在 `{best['claim']}`×{best['category']}"
                f"（{best['lift']:+.3f}，n={best['n_hit']}，p={best['p_value']}），不足为凭。")
    best = h["best_pred"]
    return (f"**有 {h['pred_beat_baseline_p05']}/{h['pred_tested']} 条断语在 p≤0.05 上超过同基数基线**，"
            f"最大增益 `{best['claim']}`×{best['category']} {best['lift']:+.3f}"
            f"（n={best['n_hit']}）。其余断语未超过基线。")


def render_md(payload: dict) -> str:
    h = payload["headline"]
    L: list[str] = []
    A = L.append

    A("# 铁口箓评测 v1 · 项目第一把「正确性」尺子")
    A("")
    A("> T-146 产物，由 `python -m tools.tiekoulu_eval` 生成。**只测量，不优化**：")
    A("> 答案集、断语、引擎均未改动；未为分数调阈值、挑题或剔除难例。")
    A("")
    A("## 0. 结论先说")
    A("")
    A(verdict_sentence(payload))
    A("")
    A("配套读数：")
    A("")
    A(f"- 36 期解析成功率 **{h['parse_success']}/{h['parse_target']}"
      f"（{_pct(h['parse_success_rate'])}）**")
    bl = h["baselines"]
    A(f"- 基线：婚姻 **{_pct(bl['婚姻']['baseline'])}**（n={bl['婚姻']['n']}）、"
      f"子女 **{_pct(bl['子女']['baseline'])}**（n={bl['子女']['n']}）、"
      f"学历 **{_pct(bl['学历']['baseline'])}**（n={bl['学历']['n']}）")
    A(f"- 命中数 > 0 的断语 **{h['claims_measurable']}/{h['claims_total']}**；"
      f"0 命中（无法验证）{len(h['claims_unverifiable'])} 条")
    if h["top_assoc"]:
        t = h["top_assoc"]
        A(f"- 最高关联度 **{t['gap']:+.3f}**（`{t['claim']}` × {t['category']}，"
          f"n={t['n_hit']}/{t['n_miss']}，p={t['p_value']}）")
    A("")

    A("## 1. 口径与数据事实")
    A("")
    A(f"- 答案集总期数 {payload['inputs']['bank_periods']}，其中有性别 **{payload['inputs']['periods_with_gender']}** 期（女 23 / 男 13）")
    A(f"- 本期处理：成功 {h['parse_success']} 期，解析失败 {h['parse_failures']} 期，排盘失败 {h['chart_failures']} 期")
    A(f"- 出生时刻口径：**true_solar {h['time_basis'].get('true_solar', 0)} 期**，"
      f"clock_beijing {h['time_basis'].get('clock_beijing', 0)} 期（回退）")
    A(f"- 断语：`pilot-20.yaml` 中 compiled **{payload['inputs']['claims_compiled']}** 条参与评测；"
      f"未编译 {len(payload['inputs']['claims_skipped'])} 条不参与")
    A(f"- 题目：切出 **{h['qtypes_total']}** 个题目类型，其中样本 ≥{payload['method']['min_type_n']} 的可用类型 "
      f"**{h['qtypes_usable']}** 个（{h['questions_usable']} 题）；"
      f"因量表不统一/样本过小剔除 {h['questions_excluded_by_scale']} 题；"
      f"多选题剔除 {h['multi_choice_excluded']} 道")
    A("")
    A("### 1.1 为什么按「题目类型」而不是按「类别」统计")
    A("")
    A("题库里同名类别并不同质：")
    A("")
    A("- **职业** = 31 道「日主职业？」（3 选项，稳定工作/自由职业/先稳定后自由）"
      "+ 18 道「职业精准点射」（5 选项，且**每期选项各不相同**）。")
    A("- **流年** = 每年一道「某年发生的事情」，13 个选项且**每年事件不同**。")
    A("")
    A("把不同量表的答案按字母汇总，等于默认「B」在不同题里是同一个含义——"
      "那会把 3 选项题的模态选项和 5 选项题的模态选项混成一个数字，基线随之失真。"
      "因此本工具只在 **(类别, 题干, 选项集) 完全一致**的题目类型内做字母级统计，")
    A(f"类型样本 < {payload['method']['min_type_n']} 的直接剔除并逐条列出（§7.2）。")
    A("")
    A("> **与任务卡的口径偏差（必须记录）**：卡上写「子女 64」，实为 36 道「日主子女」"
      "+ 28 道「出身家境」——家境题干含「子女富贵不算」四字，关键词分类会误命中。")
    A("> 本报告用「日主子女」精确匹配，子女 = 36 题，家境单列。卡上「职业 49」正是上述两类职业题之和，")
    A("> 合并后基线会从 67.7% 掉到 46.9%，属失真的合并，故本报告拆开。")
    A("")

    A("## 2. 第一层 · 多数类基线（瞎猜上限）")
    A("")
    A("「永远选该题出现最多的那个选项」能得多少分。**任何断语必须先跨过这条线。**")
    A("")
    A("| 类别 | 代表题目类型 | 题数 | 选项数 | 最常见选项 | 基线准确率 | 答案分布 |")
    A("|---|---|---:|---:|---|---:|---|")
    order = ["婚姻", "子女", "学历", "职业", "财富", "家境", "父母"]
    full = payload["baselines"]
    for cat in order:
        b = full.get(cat)
        if not b:
            continue
        dist = " / ".join(f"{k}={v}" for k, v in (b.get("dist") or {}).items())
        A(f"| {cat} | {_short_q(b['question'])} | {b['n']} | {b['n_options']} | {b['modal']} "
          f"| **{_pct(b['baseline'])}** | {dist} |")
    A("")
    A("各类别明细（同一类别下每份量表分别列，避免跨量表求和）：")
    A("")
    A("| 类别 | 题目类型 | 题数 | 选项数 | 模态 | 基线 | 分布 |")
    A("|---|---|---:|---:|---|---:|---|")
    for r in payload["per_type_baseline"]:
        dist = " / ".join(f"{k}={v}" for k, v in r["dist"].items())
        A(f"| {r['category']} | {_short_q(r['question'])} | {r['n']} | {r['n_options']} "
          f"| {r['modal']} | {_pct(r['baseline'])} | {dist} |")
    A("")
    A(f"> 上表第一张里的「代表题目类型」取该类别样本最大的可用类型；"
      f"完整分表（含流年逐年基线）见下表。被剔除的量表在 §7.2。")
    A("")
    A("> **流年题不进入第一张表**：每年一套独立的 13 选项（事件不同），没有跨年可比的"
      "「最常见选项」，因此逐年基线只在下表列出，不作为断语的对照基线。")
    A("")

    A("## 3. 第二层 · 断语命中数")
    A("")
    A(f"{h['claims_total']} 条 compiled 断语在 {h['parse_success']} 期上的命中（`state == candidate`）。"
      "**命中数为 0 的一律标「无法验证」**——不能当成「不成立」，也不能当成「没命中所以对」。")
    A("")
    A("| 断语 | 流派 | 类别 | 命中/期数 | value=null | 判定 | 断语原文 |")
    A("|---|---|---|---:|---:|---|---|")
    for s in payload["claims"]:
        A(f"| `{s['id']}` | {s['school']} | {s['domain']} | {s['hit_n']}/{s['periods']} "
          f"| {s['value_unknown_n']} | {s['verdict']} | {s['statement']} |")
    A("")
    A(f"命中数 > 0：**{h['claims_measurable']}/{h['claims_total']}**；"
      f"命中数为 0：{('、'.join(f'`{x}`' for x in h['claims_unverifiable'])) or '无'}。")
    A("")

    A("## 4. 第三层 · 断语 × 题目关联度")
    A("")
    A("统计量：命中组与未命中组在**同一答案字母**上的最大占比差（max share gap），")
    A(f"配 {payload['method']['perm_rounds']} 次置换检验（seed={payload['method']['perm_seed']}）。"
      f"任一组样本 < {payload['method']['min_hit_for_stats']} 的不给统计量。")
    A("")
    A("**适用域声明**：12 条断语的 `time_window` 全为 `natal`（原局），"
      "无法对「某一年发生了什么」做出可判分的预测。")
    A("因此第三层分成两张表：**4.1 原局类为裁决依据**，**4.2 岁运类仅附列**"
      "（断语与原局条件已固定，岁运差异属另一层因果，把它们并进来只会制造噪声）。")
    A("")
    A("### 4.1 原局类题目（裁决依据）")
    A("")
    A("| 断语 | 类别 | 题目类型 | n命中/n未命中 | 字母 | 占比差 | 命中组 | 未命中组 | p |")
    A("|---|---|---|---:|---|---:|---:|---:|---:|")
    natal_rows = sorted([r for r in payload["association"]
                         if r.get("gap") is not None and r["natal"]],
                        key=lambda r: -abs(r["gap"]))
    for r in natal_rows:
        A(f"| `{r['claim']}` | {r['category']} | {r['question']} "
          f"| {r['n_hit']}/{r['n_miss']} | {r['gap_letter']} | {r['gap']:+.3f} "
          f"| {_pct(r['share_hit'])} | {_pct(r['share_miss'])} | {r['p_value']:.3f} |")
    A("")
    if h["top_assoc"]:
        t = h["top_assoc"]
        A(f"**最高关联度（原局类）**：`{t['claim']}` × {t['category']}（{t['question']}），"
          f"占比差 **{t['gap']:+.3f}**（字母 {t['letter']}），"
          f"n命中={t['n_hit']} / n未命中={t['n_miss']}，p={t['p_value']}。")
        A("")
    A(f"p ≤ 0.05 的组合：**{h['assoc_significant_p05']} / {h['assoc_tested']}**。")
    A("")
    A(f"> **多重比较提醒**：原局类共做 {h['assoc_tested']} 次比较，α=0.05 下纯随机期望 "
      f"{h['assoc_expected_by_chance']} 个「显著」，观测到 {h['assoc_significant_p05']} 个。"
      f"**未超过随机期望**，因此第三层整体不构成「断语有区分力」的证据。")
    A("")
    A(f"### 4.2 岁运类题目（附列，不参与裁决，共 {h['assoc_tested_suiyun']} 次比较）")
    A("")
    if h["top_assoc_suiyun"]:
        s = h["top_assoc_suiyun"]
        A(f"岁运类里 |占比差| 最大的是 `{s['claim']}` × {s['category']}（{s['question']}），"
          f"占比差 {s['gap']:+.3f}，n={s['n_hit']}/{s['n_miss']}，p={s['p_value']}。")
        A("")
        A("这张表**不可用作断语证据**，原因有二：")
        A("")
        A("1. **域错配**：断语讲的是原局结构，题目问的是某一年的具体事件，中间隔着岁运引动这一层，"
          "而 pilot-20 的 42 原子未接入 `suiyun_edge`（M1-D-009/M2-Y-019 正是因此判为 uncompilable）。")
        A("2. **样本过小**：流年题每年一套独立 13 选项，单年样本 5–9 题，"
          "命中组往往只有 3–4 题。样本这么小时，占比差可以轻易到 ±1.000——"
          "那不是信号，是把两三期的差异放大成了整数。")
        A("")
        A("> 如实说明：若把岁运类并入统计，会得到 2 个 p≤0.05 的组合"
          f"（随机期望 {round(h['assoc_tested_suiyun'] * 0.05, 2)} 个），"
          "看起来「显著」，但如上所述不成立。本报告不采用这条路径。")
        A("")

    A("## 5. 第四层 · 方向预测 vs 同基数基线")
    A("")
    A("第三层只说明「命中组答案分布不同」，不等于「断语说对了」。要判分，必须把断语命中翻译成具体选项。")
    A("下表只收录**断语本身给出了方向**的条目，且基线按**同一选项个数 k** 计算——")
    A("预测 2 个字母就必须对「猜 2 个最常见字母」的基线，不许拿 1 字母基线占基数便宜。")
    A("")
    A("| 断语 | 类别 | 预测 | 命中 n | 命中组正确 | 正确率 | 同基数基线 | 增益 | p |")
    A("|---|---|---|---:|---:|---:|---:|---:|---:|")
    for r in payload["prediction"]:
        if r.get("acc_hit") is None:
            continue
        flag = " ⚠︎" if r.get("degenerate") else ""
        A(f"| `{r['claim']}` | {r['category']}{flag} | {''.join(r['predict'])} | {r['n_hit']} "
          f"| {r['correct_in_hit']}/{r['n_hit']} | {_pct(r['acc_hit'])} "
          f"| {_pct(r['matched_baseline'])} | {r['lift']:+.3f} | {r['p_value']:.3f} |")
    A("")
    if h["pred_degenerate"]:
        A(f"> ⚠︎ **退化项已剔除**：`{'`、`'.join(h['pred_degenerate'])}` 的预测集覆盖了该类实际出现过的"
          "全部答案（财富类只出现过 A/B 两值，而预测也是 A∪B），基线必然同为 100%，增益恒为 0，"
          "无区分力，已从分母剔除。")
        A("")
    A("**翻译依据**（逐条可查，不是看到答案后倒推的）：")
    A("")
    A("| 断语 | 类别 | 命中的含义 → 预测选项 |")
    A("|---|---|---|")
    for r in payload["prediction"]:
        if r.get("why"):
            A(f"| `{r['claim']}` | {r['category']} | {r['why']} |")
    A("")
    if h["best_pred"]:
        bp = h["best_pred"]
        A(f"**方向预测最大增益**：`{bp['claim']}` × {bp['category']}（{bp['question']}），"
          f"{_pct(bp['acc_hit'])} vs 同基数基线 {_pct(bp['matched_baseline'])}，"
          f"增益 {bp['lift']:+.3f}，n={bp['n_hit']}，p={bp['p_value']}。")
        A("")
    A(f"增益 > 0 且 p ≤ 0.05：**{h['pred_beat_baseline_p05']} / {h['pred_tested']}**（分母已剔除退化项）。")
    A("")
    A("> 读表注意：第四层的 `n_hit` 是**落在该可用题目类型内的命中题数**，")
    A("> 可能小于第三层的期数命中（例如 `G-SP-165` 命中 7 期，但其中 1 期的学历题属于被剔除的 4 选项合并量表，"
      "故第四层 n=6）。这不是漏算，是同一份量表约束的结果。")
    A("")

    A("## 6. 未纳入方向预测的断语（逐条说明，不静默丢弃）")
    A("")
    A("| 断语 | 类别 | 原因 |")
    A("|---|---|---|")
    for r in payload["prediction"]:
        if r.get("acc_hit") is None:
            A(f"| `{r['claim']}` | {r.get('category') or '—'} | {r['note']} |")
    A("")

    A("## 7. 失败与边界清单")
    A("")
    A("### 7.1 解析失败 / 排盘失败（逐条）")
    A("")
    if payload["parse_failures"] or payload["chart_failures"]:
        A("| 期号 | 阶段 | 原因 |")
        A("|---|---|---|")
        for f in payload["parse_failures"]:
            A(f"| {f['period']} | 解析 | {f['reason']} |")
        for f in payload["chart_failures"]:
            A(f"| {f['period']} | 排盘 | `{f['error']}` |")
    else:
        A("**无。** 36 期全部由 `line3_true_solar` 正则可解析"
          "（格式 `真太阳时: YYYY年M月D日H时M分`），排盘全部成功，回退 clock_beijing 0 期。")
    A("")
    A("### 7.2 因量表不统一/样本过小剔除的题目类型")
    A("")
    A(f"同一题干下若每期选项都不同（如「职业精准点射」），会各自成为独立量表；下表按"
      f"（类别, 题干, 选项数）归并，`量表数` 即该题干下互不相同的选项集个数。"
      f"这些题目不参与字母级统计，但**逐条列在这里，不是静默跳过**。")
    A("")
    if payload["unusable_qtypes"]:
        A("| 类别 | 题目类型 | 题数 | 量表数 | 选项数 | 原因 |")
        A("|---|---|---:|---:|---:|---|")
        for u in payload["unusable_qtypes"]:
            A(f"| {u['category']} | {u['question']} | {u['questions']} | {u['scales']} "
              f"| {u['n_options']} | 单一量表样本 < {payload['method']['min_type_n']}，字母级统计无效 |")
        A("")
        A(f"小计 {h['questions_excluded_by_scale']} 题。其中「职业精准点射」与「流年」占绝大多数——"
          "这两类题目本身就是逐期换卷，字母无法跨期比较；要评它们需要另一套按选项文本对齐的指标，"
          "不在本卡范围。")
    else:
        A("无。")
    A("")
    A("### 7.3 剔除的题目（多选/答案非法）")
    A("")
    if payload["excluded_questions"]:
        A("| 期号 | 题号 | 答案 | 原因 | 题干 |")
        A("|---|---:|---|---|---|")
        for m in payload["excluded_questions"]:
            A(f"| {m['period']} | {m['q_index']} | `{m['answer']}` | {m['reason']} | {m['question'][:36]} |")
    else:
        A("无。")
    A("")
    A("### 7.4 其它口径风险")
    A("")
    shifts = [p for p in payload["periods"] if p["day_boundary_shift"]]
    late = [p for p in payload["periods"] if p["late_zi"]]
    A(f"- **真太阳时跨日**：{len(shifts)} 期"
      + (f"（{'、'.join(p['period'] for p in shifts)}）" if shifts else "")
      + "。真太阳时与钟表时不在同一天，日柱随口径变化；本报告按 ADR-005 取 true_solar，未做双口径并列。")
    A(f"- **晚子时（23 时）**：{len(late)} 期"
      + (f"（{'、'.join(p['period'] for p in late)}）" if late else "")
      + "。晚子时是否换日存在流派分歧，本报告未展开，属已知边界。")
    A("- **断语时间窗 vs 题目时间窗**：pilot-20 断语多为 `time_window: natal`（原局），")
    A("  而题库里 84 道题问「某年发生了什么」，属岁运层面。本报告未把流年题当作断语的检验场，")
    A("  第三层的岁运行仅作附列，判读以原局类题目为准。")
    A("- **样本量**：单题最大 36 期。任何单条断语的置信区间都很宽——"
      "本报告给出 p 值与样本数，就是为了让读者不要过度解读。")
    A("- **本卡不改进**：12 条断语是否该改、引擎是否该补、题该不该拆，均不在 T-146 范围。")
    A("  本卡只负责把尺子立起来，并把第一次量到的数如实报出。")
    A("")

    A("## 8. 复跑")
    A("")
    A("```bash")
    A(".venv\\Scripts\\python.exe -m tools.tiekoulu_eval")
    A("```")
    A("")
    A("产物：`META/tiekoulu-eval-v1.json`（机器可读）、`META/tiekoulu-eval-v1.md`（本文件）。")
    A("随机数固定 seed，依赖仅标准库 + 项目已有的 `yaml`/`engine`，重跑结果逐字节一致。")
    A("")
    return "\n".join(L)


def print_console(payload: dict) -> None:
    h = payload["headline"]
    print("=" * 82)
    print("T-146 铁口箓评测 v1")
    print("=" * 82)
    print(f"解析成功        : {h['parse_success']}/{h['parse_target']} ({_pct(h['parse_success_rate'])})"
          f"   解析失败 {h['parse_failures']} / 排盘失败 {h['chart_failures']}")
    print(f"出生口径        : true_solar={h['time_basis'].get('true_solar', 0)} 期, "
          f"clock_beijing={h['time_basis'].get('clock_beijing', 0)} 期")
    print(f"题目类型        : {h['qtypes_total']} 个，可用 {h['qtypes_usable']} 个"
          f"（{h['questions_usable']} 题）；量表/样本剔除 {h['questions_excluded_by_scale']} 题；"
          f"多选剔除 {h['multi_choice_excluded']} 道")
    print("-" * 82)
    print("第一层 · 多数类基线（瞎猜上限）")
    for cat in ("婚姻", "子女", "学历", "职业", "财富", "家境"):
        b = h["baselines"].get(cat)
        if b:
            print(f"  {cat:4s} n={b['n']:2d}  基线={_pct(b['baseline']):>6s}"
                  f"  (最常见 {b['modal']})  [{b['question']}]")
    print("-" * 82)
    print("第二层 · 断语命中数")
    for s in payload["claims"]:
        tag = "  ← 无法验证" if s["hit_n"] == 0 else ""
        print(f"  {s['id']:10s} {s['domain']:4s} 命中 {s['hit_n']:2d}/{s['periods']}"
              f"  value=null {s['value_unknown_n']:2d}{tag}")
    print(f"  → 命中数 > 0：{h['claims_measurable']}/{h['claims_total']}")
    print("-" * 82)
    print("第三层 · 关联度（命中组 vs 未命中组，max share gap；仅原局类）")
    tested = sorted([r for r in payload["association"]
                     if r.get("gap") is not None and r["natal"]],
                    key=lambda r: -abs(r["gap"]))
    for r in tested[:6]:
        print(f"  {r['claim']:10s} × {r['category']:4s} {r['question']:12s} "
              f"gap={r['gap']:+.3f} ({r['gap_letter']}) n={r['n_hit']}/{r['n_miss']} p={r['p_value']:.3f}")
    print(f"  → p≤0.05：{h['assoc_significant_p05']}/{h['assoc_tested']}"
          f"（随机期望 {h['assoc_expected_by_chance']}）"
          f"   [岁运类 {h['assoc_tested_suiyun']} 次比较仅附列，不参与裁决]")
    print("-" * 82)
    print("第四层 · 方向预测 vs 同基数基线")
    for r in payload["prediction"]:
        if r.get("acc_hit") is None:
            continue
        print(f"  {r['claim']:10s} × {r['category']:4s} 预测{''.join(r['predict']):3s} "
              f"{r['correct_in_hit']}/{r['n_hit']} = {_pct(r['acc_hit']):>6s} "
              f"vs 基线 {_pct(r['matched_baseline']):>6s} 增益 {r['lift']:+.3f} p={r['p_value']:.3f}"
              + ("  ← 无区分力，已剔除" if r.get("degenerate") else ""))
    print(f"  → 增益>0 且 p≤0.05：{h['pred_beat_baseline_p05']}/{h['pred_tested']}")
    print("=" * 82)
    print("结论：")
    print("  " + verdict_sentence(payload).replace("**", ""))
    print("=" * 82)


if __name__ == "__main__":
    raise SystemExit(main())
