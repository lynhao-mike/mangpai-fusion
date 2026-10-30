"""T-197 · verify.py — stdlib-only acceptance gate for the P0 card pack.

Checks (exit 0 = pass):
 1. schema/task/format of META/p0-cards-v1.json
 2. 3–5 cards; domains cover marriage / career / health / wealth
 3. every card has tier, decision_by, anchor_q (<=2), anchor_a, provenance, engine_validation
 4. every direction candidate has 2–3 entries per card and basis/source_ref/quote/decisive/conflict_with/tier/decision_by
 5. A-tier candidates are fixed 克/生/化/墓 only (kind ke/sheng/muku); 冲/合/穿/刑/破 never A
 6. every quote is a verbatim substring of the declared `path:Ln` line (re-read from sources/, independent of the builder)
 7. engine_validation reports 0 failures and seeded_error 4/4 caught
 8. the 4 charts have zero overlap with dev-20 / fresh-40 / anchor-60 / holdout-20 / old-3 cards
 9. metrics agree with the cards

T-197d additions (r2) — the gate now also checks reproducibility of the selection layer:
10. anchor_a is complete and source-backed: one entry per anchor_q, answer ∈ {yes,no,unknown},
    answer≠unknown ⇒ answer_source≠not_in_source + a verbatim source_ref/quote; anchor_q.anchor_a must match.
11. [FAIL if selected is non-null while the layer has more than one survivor] selected_option / state_selected
    must equal the single surviving selectable candidate under anchor_a (C-tier never selectable);
    state_selected must equal that candidate's `result`. The card's declared `selection` block must match the recomputation.
12. anchor_a must match the 6-answer table in META/p0-report-v1.md, and the A/B1/C direction-claim counts must
    match both metrics and the report.
Field-consistency invariants that back 10–12 (T-197c D02/D03/D05):
    - every elimination keep/eliminate id must be listed in that question's `discriminates`;
    - every state/rescue candidate's `anchored_by` qid must exist and must discriminate that candidate.

No answer/label files are read. No network. No git.
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

FAILS: list[str] = []
WARNS: list[str] = []

SELECTABLE_TIERS = ("A", "B1", "B2")
ANSWER_VALUES = ("yes", "no", "unknown")
ANSWER_SOURCES = ("source_outcome", "testimony", "not_in_source")


def fail(msg: str) -> None:
    FAILS.append(msg)


def warn(msg: str) -> None:
    WARNS.append(msg)


def ok(msg: str) -> None:
    print("[ok]  " + msg)


_SRC_CACHE: dict[str, list[str]] = {}


def _src_lines(rel: str) -> list[str]:
    if rel not in _SRC_CACHE:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            _SRC_CACHE[rel] = fh.read().split("\n")
    return _SRC_CACHE[rel]


def _split_ref(ref: str):
    """sources/xxx.md:L29 -> (rel, 29). Returns (None, None) when unparsable."""
    if ":" not in (ref or ""):
        return None, None
    rel, line = ref.rsplit(":", 1)
    try:
        return rel, int(line.lstrip("L").split("-")[0])
    except ValueError:
        return None, None


def _verbatim(ref: str, text: str) -> tuple[bool, str]:
    rel, line_no = _split_ref(ref)
    if rel is None:
        return False, f"行号不可解析：{ref}"
    if not rel.startswith("sources/"):
        return False, f"锚点答案必须引 sources/ 原文：{rel}"
    if not os.path.exists(os.path.join(ROOT, rel)):
        return False, f"引文路径不存在：{rel}"
    lines = _src_lines(rel)
    if line_no < 1 or line_no > len(lines):
        return False, f"行号越界：{ref}"
    if not text or text not in lines[line_no - 1]:
        return False, f"引文非逐字：{ref}「{(text or '')[:24]}」"
    return True, "逐字命中该行"


def survivors(card: dict, layer: str, cands: list[dict], answers: dict[str, str]) -> list[str]:
    """Candidates of `layer` that remain selectable under `answers`.

    Rules (mirrors META/p0-cards-v1.json selection_rules):
      - C tier never participates in selection;
      - an unanswered question counts as `unknown`;
      - a layer with no anchor_q keeps all selectable candidates;
      - a candidate is eliminated if any applicable question's row eliminates it.
    """
    eliminated: set[str] = set()
    for q in card.get("anchor_q") or []:
        if q.get("layer") != layer:
            continue
        ans = answers.get(q.get("qid"), "unknown")
        row = None
        for e in q.get("elimination") or []:
            if e.get("answer") == ans:
                row = e
        if row is None:
            continue
        eliminated.update(row.get("eliminates") or [])
    selectable = [x for x in cands if x.get("tier") in SELECTABLE_TIERS]
    return [x["option_id"] for x in selectable if x["option_id"] not in eliminated]


def parse_report() -> dict:
    path = os.path.join(ROOT, "META", "p0-report-v1.md")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    lines = text.split("\n")

    def cells(line: str) -> list[str]:
        return [x.strip() for x in line.strip().strip("|").split("|")]

    answers: dict[tuple[str, str], str] = {}
    card_rows: dict[str, list[str]] = {}
    for ln in lines:
        if re.match(r"^\|\s*\d+\s*\|\s*P0-\d\d\s*\|", ln):
            c = cells(ln)
            answers[(c[1], c[2])] = c[3]
        elif re.match(r"^\|\s*P0-\d\d\s*\|", ln):
            c = cells(ln)
            card_rows[c[0]] = c

    counts = None
    mcounts = re.search(
        r"A=(\d+)\s*/\s*B1=(\d+)\s*/\s*B2=(\d+)\s*/\s*C=(\d+)\s*（合计\s*(\d+)", text
    )
    if mcounts:
        counts = {
            "A": int(mcounts.group(1)),
            "B1": int(mcounts.group(2)),
            "B2": int(mcounts.group(3)),
            "C": int(mcounts.group(4)),
            "total": int(mcounts.group(5)),
        }
    return {"text": text, "answers": answers, "cards": card_rows, "counts": counts}


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
    aq_total = 0
    answer_index: dict[tuple[str, str], str] = {}
    direction_claim_count = {"A": 0, "B1": 0, "B2": 0, "C": 0}
    selection_summary: list[str] = []

    for c in cards:
        cid = c.get("card_id")
        for key in ("tier", "decision_by", "anchor_q", "anchor_a", "provenance", "engine_validation", "facts"):
            if key not in c:
                fail(f"{cid} 缺字段 {key}")
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
            for row in a.get("elimination") or []:
                for oid in (row.get("eliminates") or []) + (row.get("keeps") or []):
                    if oid not in (a.get("discriminates") or []):
                        fail(f"{cid}/{a.get('qid')} elimination 触及未列入 discriminates 的 {oid}")
            txt = a.get("text") or ""
            for compound in ("发生", "产生", "生活", "先生", "生日", "卫生", "生病", "原生", "发病", "生年", "出生", "医生", "生意", "学生", "招生"):
                txt = txt.replace(compound, "")
            banned = [w for w in ("冲", "合", "穿", "刑", "克", "生", "化", "墓") if w in txt]
            if banned:
                fail(f"{cid}/{a.get('qid')} 问题文本含方向词 {banned}")

        # 10 [T-197d] anchor_a 完整 + source-backed ------------------------------
        aa = c.get("anchor_a")
        if not isinstance(aa, list):
            fail(f"{cid} anchor_a 不是列表")
            aa = []
        if [e.get("qid") for e in aa] != [q.get("qid") for q in aqs]:
            fail(f"{cid} anchor_a 与 anchor_q 的题号不一致：{[e.get('qid') for e in aa]} vs {[q.get('qid') for q in aqs]}")
        qmap = {q.get("qid"): q for q in aqs}
        for e in aa:
            qid = e.get("qid")
            ans = e.get("answer")
            src = e.get("answer_source")
            q = qmap.get(qid)
            if q is None:
                fail(f"{cid}/{qid} anchor_a 出现 anchor_q 里没有的题号")
                continue
            answer_index[(cid, qid)] = ans
            if ans not in ANSWER_VALUES:
                fail(f"{cid}/{qid} anchor_a.answer={ans} 非法")
            if src not in ANSWER_SOURCES:
                fail(f"{cid}/{qid} anchor_a.answer_source={src} 非法")
            if ans == "unknown":
                if src != "not_in_source":
                    fail(f"{cid}/{qid} answer=unknown 但 answer_source={src}")
            else:
                if src == "not_in_source":
                    fail(f"{cid}/{qid} answer={ans} 但 answer_source=not_in_source")
                good, detail = _verbatim(e.get("source_ref") or "", e.get("quote") or "")
                if not good:
                    fail(f"{cid}/{qid} 非 unknown 答案必须有逐字原文：{detail}")
                if q.get("source_mentions_answer") is not True and src != "testimony":
                    fail(f"{cid}/{qid} answer={ans} 但该题 source_mentions_answer!=true 且非 testimony")
            if q.get("anchor_a") != ans:
                fail(f"{cid}/{qid} anchor_q.anchor_a={q.get('anchor_a')} 与 anchor_a.answer={ans} 不一致")

        # 11 [T-197d] selected 必须与唯一幸存者一致 ------------------------------
        cands = c.get("direction_candidates") or []
        if not 2 <= len(cands) <= 3:
            fail(f"{cid} 方向候选 {len(cands)} 不在 2–3")
        states = c.get("state_candidates") or []
        answers = {e.get("qid"): e.get("answer") for e in aa}
        d_surv = survivors(c, "direction", cands, answers)
        s_surv = survivors(c, "state", states, answers)

        sel = c.get("selected_option")
        if sel is not None:
            if len(d_surv) != 1:
                fail(f"{cid} selected_option={sel} 非唯一：方向层幸存 {d_surv}（非唯一时不得填）")
            elif d_surv[0] != sel:
                fail(f"{cid} selected_option={sel} ≠ 唯一幸存者 {d_surv[0]}")
        elif len(d_surv) == 1:
            warn(f"{cid} 方向层唯一幸存 {d_surv[0]} 但 selected_option=null（保守，非 fail）")

        st_sel = c.get("state_selected")
        if st_sel is not None:
            if len(s_surv) != 1:
                fail(f"{cid} state_selected={st_sel} 非唯一：状态层幸存 {s_surv}（非唯一时不得填）")
            else:
                target = [x for x in states if x.get("option_id") == s_surv[0]][0]
                if target.get("result") != st_sel:
                    fail(f"{cid} state_selected={st_sel} ≠ 唯一幸存 {s_surv[0]}.result={target.get('result')}")
        elif len(s_surv) == 1:
            warn(f"{cid} 状态层唯一幸存 {s_surv[0]} 但 state_selected=null（保守，非 fail）")

        sb = c.get("selection")
        if not isinstance(sb, dict):
            fail(f"{cid} 缺 selection 复算块")
        else:
            if sb.get("direction_survivors") != d_surv:
                fail(f"{cid} selection.direction_survivors={sb.get('direction_survivors')} ≠ 复算 {d_surv}")
            if sb.get("state_survivors") != s_surv:
                fail(f"{cid} selection.state_survivors={sb.get('state_survivors')} ≠ 复算 {s_surv}")
            if sb.get("selected_option") != sel:
                fail(f"{cid} selection.selected_option={sb.get('selected_option')} ≠ 卡级 {sel}")
            want_claims = [sel] if sel is not None else d_surv
            if (sb.get("selected_claims") or []) != want_claims:
                fail(f"{cid} selection.selected_claims={sb.get('selected_claims')} ≠ 期望 {want_claims}")
            want_mode = "unique" if sel is not None else ("multi_claim" if len(d_surv) > 1 else "needs_anchor")
            if sb.get("mode") != want_mode:
                fail(f"{cid} selection.mode={sb.get('mode')} ≠ 期望 {want_mode}")
        selection_summary.append(
            f"{cid}: dir_survivors={d_surv or '∅'} state_survivors={s_surv or '∅'} "
            f"selected_option={sel!r} state_selected={st_sel!r}"
        )

        # 4–5 candidate structure ----------------------------------------------
        disc = {a.get("qid"): set(a.get("discriminates") or []) for a in aqs}
        for bucket in ("state_candidates", "rescue_candidates"):
            for x in c.get(bucket) or []:
                for qid in x.get("anchored_by") or []:
                    if qid not in disc:
                        fail(f"{cid}/{x.get('option_id')} anchored_by={qid} 不是本卡锚点题（悬空引用）")
                    elif x.get("option_id") not in disc[qid]:
                        fail(f"{cid}/{x.get('option_id')} anchored_by={qid}，但 {qid}.discriminates 不含它"
                             "（锚点题并未区分该候选）")
        for x in cands:
            for k in ("basis", "claim", "source_ref", "quote", "decisive", "conflict_with", "tier", "decision_by", "engine_validation"):
                if k not in x:
                    fail(f"{cid}/{x.get('option_id')} 缺 {k}")
            if not (x.get("quote") or "").strip():
                fail(f"{cid}/{x.get('option_id')} 无 quote")
            if x.get("claim", {}).get("direction") == "actor_to_target":
                if not (x.get("claim", {}).get("actor") and x.get("claim", {}).get("target")):
                    fail(f"{cid}/{x.get('option_id')} actor_to_target 但 actor/target 为空")
            if x.get("tier") in direction_claim_count:
                direction_claim_count[x["tier"]] += 1
            else:
                fail(f"{cid}/{x.get('option_id')} tier={x.get('tier')} 非法")
            if x.get("tier") == "A":
                if x.get("kind") not in ("ke", "sheng", "muku") or x.get("class") not in ("克", "生", "化", "墓"):
                    fail(f"{cid}/{x.get('id')} A 档非固定类 kind={x.get('kind')} class={x.get('class')}")
                if x.get("decision_by") != "agent_auto":
                    fail(f"{cid}/{x.get('id')} A 档 decision_by={x.get('decision_by')}")
            if x.get("kind") in ("chong", "liuhe", "wuhe", "zhi_anhe", "chuan", "xing", "po") and x.get("tier") == "A":
                fail(f"{cid}/{x.get('id')} 对称关系被标 A")

        # 6 quotes ---------------------------------------------------------------
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
            lines = _src_lines(rel)
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
    ok("anchor_a 完整且 source-backed（非 unknown 必带逐字原文）")

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

    # 12 [T-197d] A/B1/C 计数：卡 → metrics → report 三处一致 ------------------
    total_claims = sum(direction_claim_count.values())
    if m.get("candidate_tiers") != direction_claim_count:
        fail(f"metrics.candidate_tiers={m.get('candidate_tiers')} ≠ 逐卡清点 {direction_claim_count}")
    if m.get("direction_candidates") != total_claims:
        fail(f"metrics.direction_candidates={m.get('direction_candidates')} ≠ 逐卡清点 {total_claims}")
    share = m.get("candidate_tier_share") or {}
    for tier, n in direction_claim_count.items():
        got = share.get(tier)
        if not isinstance(got, (int, float)) or abs(got - (n / total_claims if total_claims else 0)) > 1e-4:
            fail(f"metrics.candidate_tier_share[{tier}]={got} ≠ {n}/{total_claims}")
    gate = m.get("a_share_vs_p0_gate") or {}
    if total_claims and abs((gate.get("actual") or -1) - direction_claim_count["A"] / total_claims) > 1e-4:
        fail(f"metrics.a_share_vs_p0_gate.actual={gate.get('actual')} ≠ {direction_claim_count['A']}/{total_claims}")

    rep = parse_report()

    computed = dict(direction_claim_count, total=total_claims)
    if rep["counts"] is None:
        fail("p0-report-v1.md 未找到『A=… / B1=… / B2=… / C=…（合计 …）』计数行")
    elif rep["counts"] != computed:
        fail(f"report 计数 {rep['counts']} ≠ 逐卡清点 {computed}")

    if not rep["answers"]:
        fail("p0-report-v1.md 未解析到答案表（| # | 卡 | 题 | 答案 |）")
    else:
        if rep["answers"] != answer_index:
            only_rep = {k: v for k, v in rep["answers"].items() if answer_index.get(k) != v}
            only_card = {k: v for k, v in answer_index.items() if rep["answers"].get(k) != v}
            fail(f"report 答案表与卡 anchor_a 不一致：report 独有/不同={only_rep} card 独有/不同={only_card}")
        n_unknown = sum(1 for v in answer_index.values() if v == "unknown")
        n_yes = sum(1 for v in answer_index.values() if v == "yes")
        m_ans = m.get("anchor_a_answers") or {}
        if (m_ans.get("unknown"), m_ans.get("yes"), m_ans.get("total")) != (n_unknown, n_yes, len(answer_index)):
            fail(f"metrics.anchor_a_answers={m_ans} ≠ 逐卡清点 unknown={n_unknown} yes={n_yes} total={len(answer_index)}")
        ok(f"anchor_a 与 report §2 一致：{len(answer_index)} 题（unknown {n_unknown} / yes {n_yes}）")

    for c in cards:
        cid = c.get("card_id")
        row = rep["cards"].get(cid)
        if row is None:
            fail(f"p0-report-v1.md §1 缺 {cid} 行")
            continue
        if len(row) < 8:
            fail(f"p0-report-v1.md §1 {cid} 行字段不足：{row}")
            continue
        want = [
            str(c.get("direction_tier")),
            str(c.get("state_tier")),
            "null" if c.get("selected_option") is None else str(c.get("selected_option")),
            "null" if c.get("state_selected") is None else str(c.get("state_selected")),
        ]
        got = row[3:7]
        if got != want:
            fail(f"report §1 {cid} 方向档/状态档/selected 与卡不一致：report={got} card={want}")

    ok(f"计数一致：A={direction_claim_count['A']} B1={direction_claim_count['B1']} "
       f"B2={direction_claim_count['B2']} C={direction_claim_count['C']}（方向 claim 合计 {total_claims}）")
    for line in selection_summary:
        print("      " + line)

    print()
    for w in WARNS:
        print("[warn]", w)
    if FAILS:
        print(f"FAIL {len(FAILS)}:")
        for f in FAILS:
            print("  -", f)
        return 1
    print("PASS: p0 卡片包满足 T-197 + T-197d 验收项"
          "（selected 可复现 / A 仅固定类且按 claim 计数 / anchor_a 与 report 一致 / 引文逐字 / 零排除集重叠）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
