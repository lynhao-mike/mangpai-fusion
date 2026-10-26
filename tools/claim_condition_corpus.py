"""tools/claim_condition_corpus.py · 断语在真实案例库上的命中与可对照性。

回答一个具体问题：**这条断语在真实案例里到底有几张盘命中、命中的人里有多少有真实结论？**
没有真实结论，就不存在「自然对照」，任何对比对都只是编译器的单元测试。

用法：python -m tools.claim_condition_corpus
输出：META/claim-condition-corpus-v1.json（含每条断语的命中数、可对照数、结论）
"""
from __future__ import annotations

import json
import pathlib
import re
from collections import Counter

import yaml

from engine.api import analyze_facts, to_jsonable
from engine.claims.condition_ir import build_context, compile_claim, evaluate_claim

ROOT = pathlib.Path(__file__).resolve().parents[1]
PILOT = ROOT / "theory" / "claims" / "conditions-v2" / "pilot-20.yaml"
OUT = ROOT / "META" / "claim-condition-corpus-v1.json"

CASE_RE = re.compile(r"^(C-\d{4}-[A-Za-z0-9]+)-(乾|坤)-((?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4})$")
LABEL_WORDS = {
    "学历": ("学历", "本科", "大专", "高中", "中专", "硕士", "研究生", "大学", "读书"),
    "婚姻": ("婚姻", "结婚", "离婚", "再婚", "复婚", "配偶", "丈夫", "妻子", "未婚"),
    "财富": ("发财", "财富", "收入", "破财", "负债", "生意"),
    "健康": ("健康", "生病", "手术", "住院", "去世"),
    "子女": ("子女", "儿子", "女儿", "流产", "生育"),
    "事业": ("工作", "职业", "事业", "升职", "体制"),
}


def iter_cases():
    for p in sorted((ROOT / "cases").iterdir()):
        m = CASE_RE.match(p.name)
        if m:
            yield p, [m.group(3)[i:i + 2] for i in range(0, 8, 2)], m.group(2)


def feedback_text(case_dir: pathlib.Path) -> str:
    parts = []
    for f in case_dir.rglob("*.md"):
        try:
            parts.append(f.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return "\n".join(parts)


def run() -> dict:
    claims = [c for c in yaml.safe_load(PILOT.read_text(encoding="utf-8"))["claims"]
              if compile_claim(c)["status"] == "compiled"]
    stats = {c["id"]: {"domain": c["domain"], "school": c["school"], "fired": 0,
                       "labelled": 0, "unknown": 0, "total": 0} for c in claims}
    for case_dir, pillars, gender in iter_cases():
        try:
            ctx = build_context(to_jsonable(analyze_facts(pillars=pillars, gender=gender)))
        except Exception:  # noqa: BLE001 - 单盘失败不该中断全库统计
            continue
        text = feedback_text(case_dir)
        for c in claims:
            ev = evaluate_claim(c, ctx)
            s = stats[c["id"]]
            s["total"] += 1
            if ev["value"] is None:
                s["unknown"] += 1
            if ev["state"] == "candidate":
                s["fired"] += 1
                if any(w in text for w in LABEL_WORDS.get(c["domain"], ())):
                    s["labelled"] += 1
    for cid, s in stats.items():
        n = s["fired"]
        s["labelled_rate"] = round(s["labelled"] / n, 3) if n else 0.0
        s["verdict"] = ("可做自然对照" if n >= 10 and s["labelled"] >= 8
                        else "样本不足" if n < 10 else "结论不足")
    payload = {"schema": "claim-condition-corpus/v1", "generated_at": "2026-10-26",
               "claims": stats,
               "totals": {"cases": next(iter(stats.values()))["total"] if stats else 0}}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return payload


if __name__ == "__main__":
    p = run()
    print(f"cases={p['totals']['cases']}")
    print(f"{'claim':12s} {'domain':6s} {'fired':>6s} {'labelled':>9s} {'unknown':>8s}  verdict")
    for cid, s in p["claims"].items():
        print(f"{cid:12s} {s['domain']:6s} {s['fired']:6d} {s['labelled']:9d} {s['unknown']:8d}  {s['verdict']}")
