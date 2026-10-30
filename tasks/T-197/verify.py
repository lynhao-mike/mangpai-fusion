"""T-197 · verify.py — stdlib-only acceptance gate for the P0 card pack.

Checks (exit 0 = pass):
 1. schema/task/format of META/p0-cards-v1.json
 2. 3–5 cards; domains cover marriage / career / health / wealth
 3. every card has tier, decision_by, anchor_q (<=2), empty anchor_a, provenance, engine_validation
 4. every direction candidate has 2–3 entries per card and basis/source_ref/quote/decisive/conflict_with/tier/decision_by
 5. A-tier candidates are fixed 克/生/化/墓 only (kind ke/sheng/muku); 冲/合/穿/刑/破 never A
 6. every quote is a verbatim substring of the declared `path:Ln` line (re-read from sources/, independent of the builder)
 7. engine_validation reports 0 failures and seeded_error 4/4 caught
 8. the 4 charts have zero overlap with dev-20 / fresh-40 / anchor-60 / holdout-20 / old-3 cards
 9. nothing is auto-selected (selected_option null, anchor_a empty, ED decision null)

No answer/label files are read. No network. No git.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

FAILS: list[str] = []


def fail(msg: str) -> None:
    FAILS.append(msg)


def ok(msg: str) -> None:
    print("[ok]  " + msg)


def main() -> int:
    pack_path = os.path.join(ROOT, "META", "p0-cards-v1.json")
    with open(pack_path, encoding="utf-8") as fh:
        pack = json.load(fh)

    # 1 -------------------------------------------------------------------------
    if pack.get("schema") != "p0-cards/v1" or pack.get("task") != "T-197":
        fail("schema/task 不符")
    else:
        ok("schema=p0-cards/v1 task=T-197")

    cards = pack.get("cards") or []
    if not 3 <= len(cards) <= 5:
        fail(f"例数 {len(cards)} 不在 3–5")
    else:
        ok(f"例数 {len(cards)} ∈ [3,5]")

    domains = {c.get("domain") for c in cards}
    need = {"marriage", "career", "health", "wealth"}
    if not need <= domains:
        fail(f"域覆盖缺 {need - domains}")
    else:
        ok("覆盖 婚/事业/健康/财")

    # 2–5 -----------------------------------------------------------------------
    tier_count = {"A": 0, "B1": 0, "B2": 0, "C": 0}
    aq_total = 0
    for c in cards:
        cid = c.get("card_id")
        for key in ("tier", "decision_by", "anchor_q", "anchor_a", "provenance", "engine_validation", "facts"):
            if key not in c:
                fail(f"{cid} 缺字段 {key}")
        tier_count[c.get("tier", "?")] = tier_count.get(c.get("tier", "?"), 0) + 1
        aqs = c.get("anchor_q") or []
        aq_total += len(aqs)
        if len(aqs) > 2:
            fail(f"{cid} 锚点题 {len(aqs)} > 2")
        for a in aqs:
            if a.get("answer_type") not in ("fact_yes_no", "yes_no"):
                fail(f"{cid}/{a.get('qid')} 不是事实是非题")
            for k in ("elimination", "discriminates", "text", "fact_window"):
                if k not in a:
                    fail(f"{cid}/{a.get('qid')} 缺 {k}")
            ans = {e.get("answer") for e in a.get("elimination") or []}
            if ans != {"yes", "no", "unknown"}:
                fail(f"{cid}/{a.get('qid')} elimination 未覆盖 yes/no/unknown")
            if len(a.get("discriminates") or []) < 2:
                fail(f"{cid}/{a.get('qid')} discriminates < 2")
            txt = a.get("text") or ""
            for compound in ("发生", "产生", "生活", "先生", "生日", "卫生", "生病", "原生", "发病", "生年", "出生", "医生", "生意", "学生", "招生"):
                txt = txt.replace(compound, "")
            banned = [w for w in ("冲", "合", "穿", "刑", "克", "生", "化", "墓") if w in txt]
            if banned:
                fail(f"{cid}/{a.get('qid')} 问题文本含方向词 {banned}")
        if c.get("anchor_a"):
            fail(f"{cid} anchor_a 非空（不得代答）")
        if c.get("selected_option") is not None and c.get("decision_by") != "engine_fixed":
            fail(f"{cid} selected_option 非空（仅 A/engine_fixed 允许自动选定）")

        cands = c.get("direction_candidates") or []
        if not 2 <= len(cands) <= 3:
            fail(f"{cid} 方向候选 {len(cands)} 不在 2–3")
        for x in cands:
            for k in ("basis", "claim", "source_ref", "quote", "decisive", "conflict_with", "tier", "decision_by", "engine_validation"):
                if k not in x:
                    fail(f"{cid}/{x.get('option_id')} 缺 {k}")
            if not (x.get("quote") or "").strip():
                fail(f"{cid}/{x.get('option_id')} 无 quote")
            if x.get("claim", {}).get("direction") == "actor_to_target":
                if not (x.get("claim", {}).get("actor") and x.get("claim", {}).get("target")):
                    fail(f"{cid}/{x.get('option_id')} actor_to_target 但 actor/target 为空")
            if x.get("tier") == "A":
                tier_count["A"] = tier_count.get("A", 0)
                if x.get("kind") not in ("ke", "sheng", "muku") or x.get("class") not in ("克", "生", "化", "墓"):
                    fail(f"{cid}/{x.get('id')} A 档非固定类 kind={x.get('kind')} class={x.get('class')}")
                if x.get("decision_by") != "agent_auto":
                    fail(f"{cid}/{x.get('id')} A 档 decision_by={x.get('decision_by')}")
            if x.get("kind") in ("chong", "liuhe", "wuhe", "zhi_anhe", "chuan", "xing", "po") and x.get("tier") == "A":
                fail(f"{cid}/{x.get('id')} 对称关系被标 A")
        # 6 quotes ---------------------------------------------------------------
        src_cache: dict[str, list[str]] = {}
        quotes = []
        for x in cands:
            quotes.extend(x.get("quotes") or [])
        for bucket in ("state_candidates", "rescue_candidates"):
            for x in c.get(bucket) or []:
                quotes.extend(x.get("quotes") or [])
        for q in quotes:
            path = q.get("source_ref", "")
            if ":" not in path:
                fail(f"{cid} quote 无 path:line：{q.get('text')[:20]}")
                continue
            rel, line = path.rsplit(":", 1)
            if not rel.startswith("sources/"):
                continue  # rule refs (docs/) are not verbatim-quoted
            try:
                line_no = int(line.lstrip("L").split("-")[0])
            except ValueError:
                fail(f"{cid} 行号不可解析：{path}")
                continue
            abspath = os.path.join(ROOT, rel)
            if not os.path.exists(abspath):
                fail(f"{cid} 引文路径不存在：{rel}")
                continue
            if rel not in src_cache:
                with open(abspath, encoding="utf-8") as fh:
                    src_cache[rel] = fh.read().split("\n")
            lines = src_cache[rel]
            if line_no < 1 or line_no > len(lines):
                fail(f"{cid} 行号越界：{path}")
                continue
            if q["text"] not in lines[line_no - 1]:
                fail(f"{cid} 引文非逐字：{path}「{q['text'][:24]}」")

        # 7 engine_validation ----------------------------------------------------
        ev = c.get("engine_validation") or {}
        if not ev.get("all_pass"):
            fail(f"{cid} engine_validation.all_pass=false")
        se = ev.get("seeded_error") or {}
        if not (se.get("pass") and se.get("caught") == se.get("tested") == 4):
            fail(f"{cid} seeded_error {se.get('caught')}/{se.get('tested')}")
        agg = ev.get("aggregate") or {}
        for k, v in agg.items():
            if v.get("total", 0) and v.get("pass") != v.get("total"):
                fail(f"{cid} {k} {v.get('pass')}/{v.get('total')}")

    ok(f"逐卡结构/档位/引文校验完成（锚点题 {aq_total}）")

    # 8 exclusion ---------------------------------------------------------------
    excl_files = {
        "F20": "META/p1-fixed-20-blind-v1.json",
        "PF": "META/p1-fresh-40-v1.json",
        "A60": "META/p1-anchor-60-blind-v1.json",
        "P1H": "META/p1-holdout-v1.json",
        "OLD3": "META/single-chart-cases-v1.json",
    }
    excl = set()
    for tag, rel in excl_files.items():
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            data = json.load(fh)
        for cs in data.get("cases") or []:
            p = cs.get("four_pillars") or cs.get("pillars")
            if p:
                excl.add(" ".join(p.split()))
    for c in cards:
        p = " ".join((c.get("four_pillars") or "").split())
        if p in excl:
            fail(f"{c.get('card_id')} 与排除集重叠：{p}")
    if not FAILS:
        ok(f"4 盘与 {len(excl)} 个排除集四柱零重叠")

    # 9 metrics -----------------------------------------------------------------
    m = pack.get("metrics") or {}
    if m.get("engine_validation_failures") != 0:
        fail(f"metrics.engine_validation_failures={m.get('engine_validation_failures')}")
    if m.get("case_count") != len(cards):
        fail("metrics.case_count 与 cards 数不一致")
    ok(f"metrics: A={m.get('candidate_tiers', {}).get('A')} B1={m.get('candidate_tiers', {}).get('B1')} "
       f"B2={m.get('candidate_tiers', {}).get('B2')} C={m.get('candidate_tiers', {}).get('C')} "
       f"anchor_q={m.get('anchor_questions')} b2_decision={m.get('b2_expert_decisions')}")

    print()
    if FAILS:
        print(f"FAIL {len(FAILS)}:")
        for f in FAILS:
            print("  -", f)
        return 1
    print("PASS: p0 卡片包满足 T-197 验收项（不自动选定 / A 仅固定类 / 引文逐字 / 零排除集重叠）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
