"""T-197 · build p0-cards-v1.json (A / B1 / B2 / C tiers, anchor questions, engine validation).

Deterministic: reads only the four `engine.cli` snapshots saved under tasks/T-197/_engine/
and the cited `sources/` lines. Writes META/p0-cards-v1.json.

No answer files, no scorers, no git writes.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

SRC = {
    "HY": "sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md",
    "JG": "sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md",
    "JB": "sources/duan/MinerU_markdown_疾病_2056043976378220544.md",
    "CG": "sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md",
    "AL": "sources/duan/MinerU_markdown_16.《盲派批命案例集》（263例，74页）段建业_2056045601255776256.md",
}
ACTOR_RULES = "docs/specs/actor-rules-v1.md"
PACK_SPEC = "docs/specs/fact-evidence-pack-v1.md"
AL_L39 = f"{SRC['AL']}:L39"
JB_L9 = f"{SRC['JB']}:L9"

_src_lines: dict[str, list[str]] = {}


def src_lines(key: str) -> list[str]:
    if key not in _src_lines:
        with open(os.path.join(ROOT, SRC[key]), encoding="utf-8") as fh:
            _src_lines[key] = fh.read().split("\n")
    return _src_lines[key]


def load_engine(name: str) -> dict:
    with open(os.path.join(ROOT, "tasks", "T-197", "_engine", name), encoding="utf-8-sig") as fh:
        return json.load(fh)


def q(src: str, line: int, text: str, role: str = "direction_support") -> dict:
    return {"src": src, "line": line, "text": text, "role": role, "source_ref": f"{SRC[src]}:L{line}"}


def pillar_text(src: str, line: int) -> str:
    """Exact pillar text of a case line (strips 乾/坤 prefix and bold markers only)."""
    ln = src_lines(src)[line - 1]
    s = ln
    for pre in ("乾**：", "坤**：", "乾：", "坤：", "乾**", "坤**"):
        if s.startswith(pre):
            s = s[len(pre):]
            break
    return s.strip("*")


def pq(src: str, line: int, role: str = "case_pillars") -> dict:
    return {"src": src, "line": line, "text": pillar_text(src, line), "role": role, "source_ref": f"{SRC[src]}:L{line}"}


# --------------------------------------------------------------------------------------
# engine snapshots
# --------------------------------------------------------------------------------------
ENGINE = {
    "C1": {"all": "c1.json", "rel": "c1_rel.json"},
    "C2": {"all": "c2.json", "rel": "c2_rel.json"},
    "C3": {"all": "c3.json", "rel": "c3_rel.json"},
    "C4": {"all": "c4.json", "rel": "c4_rel.json"},
}
PY = r"E:\Git hub\mangpai-fusion\.venv\Scripts\python.exe"


def brief_facts(allj: dict, relj: dict) -> dict:
    ch = allj["chart"]
    pillars = []
    for p in ch["pillars"]:
        pillars.append(
            {
                "palace": p["palace"],
                "ganzhi": p["ganzhi"],
                "stem": {"addr": p["stem"]["addr"], "char": p["stem"]["char"], "ten_god": p["stem"]["ten_god"]},
                "branch": {
                    "addr": p["branch"]["addr"],
                    "char": p["branch"]["char"],
                    "main_ten_god": p["branch"]["main_ten_god"],
                    "hidden": p["branch"]["hidden"],
                },
            }
        )
    kd = ch.get("kongwang") or {}
    muku = []
    for m in relj.get("muku") or []:
        muku.append(
            {
                "addr": m["addr"],
                "branch": m["branch"],
                "ku_of": m.get("ku_of"),
                "openers": m.get("openers"),
                "chuan_po": m.get("chuan_po"),
                "binders": m.get("binders"),
                "candidates": [
                    {
                        "addr": c.get("addr"),
                        "char": c.get("char"),
                        "effect": (c.get("rule_hits") or [{}])[0].get("effect"),
                        "excluded": c.get("excluded"),
                        "requires_judgment": c.get("requires_judgment"),
                    }
                    for c in (m.get("candidates") or [])
                ],
            }
        )
    edges = []
    for e in relj["edges"]:
        edges.append(
            {
                "edge_id": e["id"],
                "layer": e.get("layer"),
                "kind": e.get("kind"),
                "members": e.get("members"),
                "chars": e.get("chars"),
                "distance": e.get("distance"),
                "between": e.get("between"),
                "group": e.get("group"),
                "completeness": e.get("completeness"),
                "scope": e.get("scope"),
            }
        )
    duan = []
    for c in allj["duan_zuogong"]["candidates"]:
        duan.append({"mode": c.get("mode"), "members": c.get("members"), "actor": c.get("actor"), "edge_id": c.get("edge_id")})
    structures = []
    for s in allj.get("structures") or []:
        structures.append(
            {
                "structure_id": s.get("structure_id"),
                "items": [{"id": i.get("id"), "kind": i.get("kind"), "status": i.get("status")} for i in s.get("items", [])],
            }
        )
    return {
        "chart_id": ch["chart_id"],
        "day_master": ch["day_master"],
        "gender": ch["gender"],
        "profile": ch.get("profile"),
        "four_pillars": " ".join(p["ganzhi"] for p in ch["pillars"]),
        "pillars": pillars,
        "kong_wang": kd,
        "tiyong": allj["duan_zuogong"].get("tiyong"),
        "muku": muku,
        "edges": edges,
        "duan_candidates": duan,
        "structures": structures,
        "camp_counts": allj["strength"].get("camp_counts"),
        "variants": ch.get("variants"),
        "input_limitations": allj.get("input_limitations"),
    }


# --------------------------------------------------------------------------------------
# cards
# --------------------------------------------------------------------------------------
CARDS = [
    {
        "card_id": "P0-01",
        "case_key": "C1",
        "domain": "marriage",
        "gender": "乾",
        "four_pillars": "辛巳 庚寅 甲申 庚午",
        "question": {
            "text": "我婚姻一直不顺，离过几次，现在一个人过；想知道这段命里的婚姻还能不能稳定下来。",
            "domain": "marriage",
            "prereg_id": None,
            "asked_by": "命主",
        },
        "source": {
            "path": SRC["HY"],
            "locator": "L21-L33（案例）；L15-L17、L44-L50（同章判据）",
            "pillar_quote": [pq("HY", 21), pq("HY", 23)],
            "outcome_quote": q("HY", 25, "这个例子记载他有五次婚姻，老婆带子女全跑了，最后还是孤家寡人。", "outcome_background"),
            "outcome_note": "原文后续事实：五次婚姻、配偶带子女离开、无子女留在身边（P0 仅备查，不作预测依据）。",
        },
        "palaces": [
            {"addr": "D.b", "role": "夫妻宫（配偶宫）", "ten_god": "七杀", "mapping_rule": "M-01", "basis_quote": q("HY", 15, "看婚姻的好坏，应以配偶宫为主，配偶星为辅。", "mapping")},
            {"addr": "Y.b", "role": "配偶星（男命财星）藏戊偏财", "ten_god": "食神", "mapping_rule": "M-02", "basis_quote": q("HY", 17, "配偶宫为日主的坐支，配偶星则男命以财星为妻，女命以官杀星当夫，如无则另看：男命再无遁藏，基本可能确定无婚，或克配偶。", "mapping")},
            {"addr": "H.b", "role": "配偶星（男命财星）藏己正财", "ten_god": "伤官", "mapping_rule": "M-02", "basis_quote": q("HY", 17, "配偶宫为日主的坐支，配偶星则男命以财星为妻，女命以官杀星当夫，如无则另看：男命再无遁藏，基本可能确定无婚，或克配偶。", "mapping")},
        ],
        "material_edges": ["e015", "e011"],
        "material_edge_reasons": {"e015": "夫妻宫(M.b寅↔D.b申)相冲——问题直接问婚姻稳定", "e011": "年支巳与夫妻宫申六合——配偶星来源侧，与冲争主线"},
        "direction_candidates": [
            {
                "id": "dc1",
                "layer": "direction",
                "kind": "chong",
                "class": "冲",
                "class_tier": "B_class",
                "tier": "B1",
                "decision_by": "human_anchor",
                "direction_type": "actor_target",
                "actor": "M.b",
                "actor_char": "寅",
                "target": "D.b",
                "target_char": "申",
                "edge_ref": {"type": "edge", "edge_id": "e015", "kind": "chong", "members": ["M.b", "D.b"]},
                "basis": "『夫宫被冲克』是被动句：受方=夫妻宫申；紧接一句『寅申之冲，寅多作用一次』把反复作用的一方指向月支寅（比肩＝月柱父母兄弟宫）。engine 边 e015 为 chong(M.b,D.b)、actor=null，方向由本候选补出。",
                "rule_ref": f"{ACTOR_RULES}:L86-L93",
                "quotes": [
                    q("HY", 29, "为何偏偏要离婚，而不是二奶三奶呢？因夫宫被冲克，处于不稳定状态。", "direction_support"),
                    q("HY", 31, "巳、寅、午，三个老婆，巳申合，巳用了两次，多数一个，而寅申之冲，寅多作用一次，所以总算五个。", "actor_support"),
                ],
                "decisive": False,
                "conflict_with": ["dc2", "dc3"],
                "evidence_gap": "same_page",
                "addrs": ["M.b", "D.b"],
                "ten_god_claims": {"M.b": "比肩", "D.b": "七杀"},
            },
            {
                "id": "dc2",
                "layer": "direction",
                "kind": "chong",
                "class": "冲",
                "class_tier": "B_class",
                "tier": "B1",
                "decision_by": "human_anchor",
                "direction_type": "mutual",
                "actor": None,
                "target": None,
                "edge_ref": {"type": "edge", "edge_id": "e015", "kind": "chong", "members": ["M.b", "D.b"]},
                "basis": "冲为对称关系，actor=null；『寅申之冲』是并列句，『寅多作用一次』是次数统计（计老婆个数），不是及物施受句法，不得据以单向赋向。",
                "rule_ref": f"{ACTOR_RULES}:L34-L42,L86-L93",
                "quotes": [q("HY", 31, "巳、寅、午，三个老婆，巳申合，巳用了两次，多数一个，而寅申之冲，寅多作用一次，所以总算五个。", "direction_support")],
                "decisive": False,
                "conflict_with": ["dc1", "dc3"],
                "evidence_gap": "same_line",
                "addrs": ["M.b", "D.b"],
                "ten_god_claims": {"M.b": "比肩", "D.b": "七杀"},
            },
            {
                "id": "dc3",
                "layer": "direction",
                "kind": "liuhe",
                "class": "合",
                "class_tier": "B_class",
                "tier": "B1",
                "decision_by": "human_anchor",
                "direction_type": "needs_anchor",
                "actor": None,
                "target": None,
                "edge_ref": {"type": "edge", "edge_id": "e011", "kind": "liuhe", "members": ["Y.b", "D.b"]},
                "basis": "同一夫妻宫另有『巳申合』（engine e011 liuhe 巳申）与『巳申破』（e012）。合不赋向；若婚姻主线是年支合夫妻宫而非冲，则施力方不可判（方向留空）。",
                "rule_ref": f"{ACTOR_RULES}:L72-L84",
                "quotes": [q("HY", 31, "巳、寅、午，三个老婆，巳申合，巳用了两次，多数一个，而寅申之冲，寅多作用一次，所以总算五个。", "relation_support")],
                "decisive": False,
                "conflict_with": ["dc1", "dc2"],
                "evidence_gap": "same_line",
                "addrs": ["Y.b", "D.b"],
                "ten_god_claims": {"Y.b": "食神", "D.b": "七杀"},
            },
        ],
        "state_candidates": [
            {
                "id": "st1",
                "layer": "state",
                "label": "夫宫被冲克 → 婚姻不稳、多婚",
                "result": "败",
                "tier": "B1",
                "decision_by": "human_anchor",
                "anchored_by": ["AQ1"],
                "basis": "原文把多婚直接归因于『夫宫被冲克』；且『寅申之冲，寅多作用一次』给出次数层面的解释。",
                "quotes": [
                    q("HY", 29, "为何偏偏要离婚，而不是二奶三奶呢？因夫宫被冲克，处于不稳定状态。", "state_support"),
                    q("HY", 25, "这个例子记载他有五次婚姻，老婆带子女全跑了，最后还是孤家寡人。", "outcome_background"),
                ],
                "conflict_with": ["st3"],
                "decisive": True,
            },
            {
                "id": "st2",
                "layer": "state",
                "label": "副宫多现 → 有婚姻关系的女性多（配偶星伏于副宫之下）",
                "result": "多现",
                "tier": "B1",
                "decision_by": "human_anchor",
                "anchored_by": ["AQ1"],
                "basis": "『申是妻宫，透出庚辛副宫，而副宫下边压着是伤食及财星』——配偶星不在夫妻宫本身而在副宫之下，故主关系多。",
                "quotes": [q("HY", 27, "申是妻宫，透出庚辛副宫，而副宫下边压着是伤食及财星，都是配偶星，表示跟他有婚姻关系的女人多。", "state_support")],
                "conflict_with": [],
                "decisive": False,
            },
            {
                "id": "st3",
                "layer": "state",
                "label": "『夫妻宫为所忌之神，被夫星制之吉者婚姻较好』——本造不满足（反条件）",
                "result": "needs_anchor",
                "tier": "C",
                "decision_by": "needs_anchor",
                "anchored_by": [],
                "basis": "该句给出的是好婚姻条件；本造夫宫七杀为忌且被冲，条件不成立。是否另有救应，原文未给。",
                "quotes": [q("HY", 50, "原局夫妻宫为所忌之神，被夫星制之吉者婚姻较好。", "condition_reference")],
                "conflict_with": ["st1"],
                "decisive": False,
            },
        ],
        "rescue_candidates": [
            {
                "id": "rs1",
                "layer": "rescue",
                "label": "夫妻宫安静条件：不能被刑坏、冲破、穿倒，或六合/暗合他星",
                "result": "needs_anchor",
                "tier": "C",
                "decision_by": "needs_anchor",
                "basis": "该句是『好婚姻的组合』条件式，本造夫妻宫同时被 e015 冲、e011 六合、e012 破，无一满足；原文未给任何救应事实。",
                "quotes": [q("HY", 48, "夫妻宫位要安静，如有用，不能被刑坏，冲破，穿倒，或六合，暗合他星（配偶星以外的星），也不宜杂透，多现。", "condition_reference")],
                "decisive": False,
            }
        ],
        "anchor_q": [
            {
                "id": "AQ1",
                "layer": "direction",
                "targets": ["dc1", "dc2"],
                "text": "你的婚姻破裂过程中，是否出现过『你的父母、兄弟或原生家庭出面介入、施压或替你做主』的具体事实？",
                "answer_type": "fact_yes_no",
                "discriminator_basis": "dc1 把施力方定在月支寅＝父母兄弟宫（家人在前推）；dc2 说两侧同损、没有单一推手。若确有原生家庭反复介入，则单侧施力读法成立；若没有，则对称读法保留。",
                "rule_ref": AL_L39,
                "source_mentions_answer": False,
                "proxy_strength": "medium",
                "if_yes": {"keep": ["dc1"], "eliminate": ["dc2"], "downgrade": []},
                "if_no": {"keep": ["dc2"], "eliminate": ["dc1"], "downgrade": []},
                "if_unknown": {"action": "needs_anchor", "affected": ["dc1", "dc2"]},
            },
            {
                "id": "AQ2",
                "layer": "direction",
                "targets": ["dc1", "dc3"],
                "text": "你与已经分开的配偶，是否至今仍有联系或经济往来（即分开后并没有彻底断干净）？",
                "answer_type": "fact_yes_no",
                "discriminator_basis": "dc3 认为主线是年支巳与夫妻宫申『合』（合而未断）；dc1 认为是冲（推走、断离）。若分开后仍长期有联系/往来，合读法保留；若彻底断绝，冲读法保留。",
                "rule_ref": f"{ACTOR_RULES}:L72-L84",
                "source_mentions_answer": False,
                "proxy_strength": "medium",
                "if_yes": {"keep": ["dc3"], "eliminate": ["dc1", "dc2"], "downgrade": []},
                "if_no": {"keep": ["dc1", "dc2"], "eliminate": ["dc3"], "downgrade": []},
                "if_unknown": {"action": "needs_anchor", "affected": ["dc1", "dc2", "dc3"]},
            },
        ],
        "gaps": ["G2", "G3", "G4", "G5", "no_spouse_star_on_stem", "muku_open_close", "suiyun_ten_god"],
        "non_claims": [
            "不判冲/合的方向，不判吉凶、成败、离婚与否、应期",
            "不把固定边（如 e002 ke）写成结论",
            "不据原文『五次婚姻』反推本盘断语（仅作后续事实备查）",
            "不判救应、不判岁运引动、不判党势",
        ],
    },
    {
        "card_id": "P0-02",
        "case_key": "C2",
        "domain": "career",
        "gender": "乾",
        "four_pillars": "戊戌 癸亥 乙巳 己卯",
        "question": {
            "text": "我在部队/单位里干了多年，想知道还能不能往上走、能走到哪一步。",
            "domain": "career",
            "prereg_id": None,
            "asked_by": "命主",
        },
        "source": {
            "path": SRC["JG"],
            "locator": "L17-L27（案例）；L1-L3（军官判据）",
            "pillar_quote": [pq("JG", 17), pq("JG", 19)],
            "outcome_quote": q("JG", 25, "此人婚姻非常好，一生2个孩子，一儿一女。", "outcome_background"),
            "outcome_note": "原文后续事实：正师级干部、07 年转戊辰运提副军长（P0 仅备查，不作预测依据）。",
        },
        "palaces": [
            {"addr": "M.s", "role": "印星（偏印）＝权/印", "ten_god": "偏印", "mapping_rule": "M-03", "basis_quote": q("AL", 39, "月——一父母、兄弟", "mapping")},
            {"addr": "Y.s", "role": "财星（正财）＝制印之力", "ten_god": "正财", "mapping_rule": "M-04", "basis_quote": q("JG", 27, "解析：八字是财制印得权的官命", "mapping")},
            {"addr": "M.b", "role": "月支（父母兄弟宫）", "ten_god": "正印", "mapping_rule": "M-03", "basis_quote": q("AL", 39, "月——一父母、兄弟", "mapping")},
        ],
        "material_edges": ["e002", "e006"],
        "material_edge_reasons": {"e002": "财制印(戊克癸)：原文判官命的核心机制", "e006": "第二组财制印(己克癸)：同一受印癸的竞争候选"},
        "direction_candidates": [
            {
                "id": "dc1",
                "layer": "direction",
                "kind": "ke",
                "class": "克",
                "class_tier": "A_class",
                "tier": "B1",
                "decision_by": "human_anchor",
                "direction_type": "actor_target",
                "actor": "Y.s",
                "actor_char": "戊",
                "target": "M.s",
                "target_char": "癸",
                "edge_ref": {"type": "edge", "edge_id": "e002", "kind": "ke", "members": ["Y.s", "M.s"]},
                "basis": "engine 固定规则：e002 ke(戊,癸)、actor=Y.s。原文把戊点为『做工的重要的字』并说『见到戊…或印被制』——即戊(正财)制癸(偏印)。",
                "rule_ref": f"{ACTOR_RULES}:L120-L127",
                "quotes": [
                    q("JG", 27, "解析：八字是财制印得权的官命", "direction_support"),
                    q("JG", 27, "戊就是做工的重要的字，见到戊他出现或印被制，或印库出现，官杀被制之年都是提升的应期。", "actor_support"),
                ],
                "decisive": True,
                "conflict_with": ["dc2"],
                "evidence_gap": "same_line",
                "addrs": ["Y.s", "M.s"],
                "ten_god_claims": {"Y.s": "正财", "M.s": "偏印"},
            },
            {
                "id": "dc2",
                "layer": "direction",
                "kind": "ke",
                "class": "克",
                "class_tier": "A_class",
                "tier": "B1",
                "decision_by": "human_anchor",
                "direction_type": "actor_target",
                "actor": "H.s",
                "actor_char": "己",
                "target": "M.s",
                "target_char": "癸",
                "edge_ref": {"type": "edge", "edge_id": "e006", "kind": "ke", "members": ["H.s", "M.s"]},
                "basis": "同盘第二组财克印：e006 ke(己,癸)、actor=H.s。原文只说『财制印』未点名哪一个财；时干己(偏财)同样满足该机制，与 dc1 争同一个受印癸。",
                "rule_ref": f"{ACTOR_RULES}:L120-L127",
                "quotes": [q("JG", 27, "解析：八字是财制印得权的官命", "direction_support")],
                "decisive": False,
                "conflict_with": ["dc1"],
                "evidence_gap": "doctrine_only",
                "addrs": ["H.s", "M.s"],
                "ten_god_claims": {"H.s": "偏财", "M.s": "偏印"},
            },
            {
                "id": "dc3",
                "layer": "direction",
                "kind": "chong",
                "class": "冲",
                "class_tier": "B_class",
                "tier": "C",
                "decision_by": "needs_anchor",
                "direction_type": "needs_anchor",
                "actor": None,
                "target": None,
                "edge_ref": {"type": "edge", "edge_id": "e009", "kind": "chong", "members": ["M.b", "D.b"]},
                "basis": "原局亥(正印)与巳(伤官)相冲（e009），但原文对升迁只给岁运叙述（如『壬申92年是印化官杀生身』），未给本造原局亥巳冲的施动方；同书他造『寅申冲了印换了地方』属于另一造，不能移植。",
                "rule_ref": f"{ACTOR_RULES}:L86-L93",
                "quotes": [q("JG", 27, "壬申92年是印化官杀生身", "absence_evidence")],
                "decisive": False,
                "conflict_with": [],
                "evidence_gap": "gap",
                "addrs": ["M.b", "D.b"],
                "ten_god_claims": {"M.b": "正印", "D.b": "伤官"},
            },
        ],
        "state_candidates": [
            {
                "id": "st1",
                "layer": "state",
                "label": "财制印得权 → 官命",
                "result": "成",
                "tier": "B1",
                "decision_by": "human_anchor",
                "anchored_by": ["AQ1"],
                "basis": "原文直断『八字是财制印得权的官命』，并以戊为工神；engine 亦有 e002 ke(戊,癸)。",
                "quotes": [q("JG", 27, "解析：八字是财制印得权的官命", "state_support")],
                "conflict_with": ["st2"],
                "decisive": True,
            },
            {
                "id": "st2",
                "layer": "state",
                "label": "无伤官制官杀、无比劫羊刃做工 → 仅凭『戌为火药库』补象法才成军官",
                "result": "疑",
                "tier": "B1",
                "decision_by": "human_anchor",
                "anchored_by": ["AQ1"],
                "basis": "原文自陈『很难理解是部队的军官，因为八字无伤官制官杀，也无比劫羊刃做工』，改由戌土火库（火药、枪炮）取象成立。此路与 st1 的财制印并不同源。",
                "quotes": [
                    q("JG", 27, "但很难理解是部队的军官，因为八字无伤官制官杀，也无比劫羊刃做工，但是八字见了戌土火库，又是伤官库做工了", "state_support"),
                    q("JG", 27, "戌本来就是火药、枪炮、炮弹的意思，所以能带火药的字做工了，肯定是军队部队的官了。", "state_support"),
                ],
                "conflict_with": ["st1"],
                "decisive": False,
            },
        ],
        "rescue_candidates": [
            {
                "id": "rs1",
                "layer": "rescue",
                "label": "引擎 structures 救应要件命中：rsc_cai_zhi_xiao / rsc_yin_or_cai（met）",
                "result": "needs_anchor",
                "tier": "C",
                "decision_by": "needs_anchor",
                "basis": "engine.structures 只报『救应要件命中』（ziping_shishen.rsc_cai_zhi_xiao、ziping_shangguan.rsc_yin_or_cai），按规格 §4.2 G5 救应未判，不构成救应结论；原文无对应救应句。",
                "quotes": [],
                "engine_ref": {"source": "engine.cli structures", "items": ["rsc_cai_zhi_xiao", "rsc_yin_or_cai"]},
                "decisive": False,
            }
        ],
        "anchor_q": [
            {
                "id": "AQ1",
                "layer": "direction",
                "targets": ["dc1", "dc2"],
                "text": "你过去十年里，收入的主要来源是否以『体制外的项目、投资或兼职』为主，而不是固定级别的工资？",
                "answer_type": "fact_yes_no",
                "discriminator_basis": "dc1 的施力财是年干戊(正财)、dc2 是时干己(偏财)。『正财↔固定收入、偏财↔外部项目』是十神通则，本包未找到逐字原文，因此只作区分假设，不写成断语；题目问的是收入结构这一已发生事实，据此决定哪一个财在命主身上是活的。",
                "rule_ref": f"{SRC['JG']}:L27，{PACK_SPEC}:L60-L62",
                "source_mentions_answer": False,
                "proxy_strength": "medium",
                "if_yes": {"keep": ["dc2"], "eliminate": ["dc1"], "downgrade": []},
                "if_no": {"keep": ["dc1"], "eliminate": ["dc2"], "downgrade": []},
                "if_unknown": {"action": "needs_anchor", "affected": ["dc1", "dc2"]},
            }
        ],
        "gaps": ["G2", "G3", "G4", "G5", "muku_open_close", "suiyun_ten_god", "binzhu_direction"],
        "non_claims": [
            "不判官职高低、升迁年份、吉凶",
            "不把『财制印』写成必然结论；engine 候选不等于做功成功",
            "不判救应（G5）；不判岁运引动",
        ],
    },
    {
        "card_id": "P0-03",
        "case_key": "C3",
        "domain": "health",
        "gender": "坤",
        "four_pillars": "壬寅 庚戌 己丑 庚午",
        "question": {
            "text": "我这些年身体一直出问题，最担心妇科和大病，想知道根子在哪。",
            "domain": "health",
            "prereg_id": None,
            "asked_by": "命主",
        },
        "source": {
            "path": SRC["JB"],
            "locator": "L135-L141（案例）；L9、L17、L27、L123（同章象法与病性）",
            "pillar_quote": [pq("JB", 135), pq("JB", 137)],
            "outcome_quote": q("JB", 139, "丑午穿，伤了时上禄，午代表女人的身体，丑是伤食的墓，又是阴的象，表示妇科方面的疾病了。实际得了子宫癌，午运丑午穿的应期，得病手术。", "outcome_background"),
            "outcome_note": "原文后续事实：子宫癌、午运手术，后经中医治疗未转移（P0 仅备查，不作预测依据）。",
        },
        "palaces": [
            {"addr": "D.b", "role": "日支（夫妻宫/自身坐支）丑：阴土、伤食之墓", "ten_god": "比肩", "mapping_rule": "M-01", "basis_quote": q("AL", 41, "日——一自己、配偶", "mapping")},
            {"addr": "H.b", "role": "时支午：己土之禄、女体", "ten_god": "偏印", "mapping_rule": "M-05", "basis_quote": q("JB", 139, "丑午穿，伤了时上禄，午代表女人的身体，丑是伤食的墓，又是阴的象，表示妇科方面的疾病了。实际得了子宫癌，午运丑午穿的应期，得病手术。", "mapping")},
            {"addr": "M.b", "role": "月支戌：火土库、劫财", "ten_god": "劫财", "mapping_rule": "M-03", "basis_quote": q("AL", 39, "月——一父母、兄弟", "mapping")},
        ],
        "material_edges": ["e012", "e010"],
        "material_edge_reasons": {"e012": "丑午穿：原文指定的病源", "e010": "丑戌刑：原文用作救应(戌坏丑)"},
        "direction_candidates": [
            {
                "id": "dc1",
                "layer": "direction",
                "kind": "chuan",
                "class": "穿",
                "class_tier": "B_class",
                "tier": "B1",
                "decision_by": "human_anchor",
                "direction_type": "actor_target",
                "actor": "D.b",
                "actor_char": "丑",
                "target": "H.b",
                "target_char": "午",
                "edge_ref": {"type": "edge", "edge_id": "e012", "kind": "chuan", "members": ["D.b", "H.b"]},
                "basis": "『丑午穿，伤了时上禄』先把受方定在时支午（己土之禄、女体），穿的另一端丑（日支/夫妻宫）即施力方。engine e012 chuan actor=null，方向由本候选补出。",
                "rule_ref": f"{ACTOR_RULES}:L104-L110",
                "quotes": [
                    q("JB", 139, "丑午穿，伤了时上禄，午代表女人的身体，丑是伤食的墓，又是阴的象，表示妇科方面的疾病了。实际得了子宫癌，午运丑午穿的应期，得病手术。", "direction_support"),
                    q("JB", 9, "三：关注八字的穿、刑、破，被坏了的字要看代表什么，是不是身体的一部分。", "method_support"),
                ],
                "decisive": False,
                "conflict_with": ["dc2"],
                "evidence_gap": "same_page",
                "addrs": ["D.b", "H.b"],
                "ten_god_claims": {"D.b": "比肩", "H.b": "偏印"},
            },
            {
                "id": "dc2",
                "layer": "direction",
                "kind": "chuan",
                "class": "穿",
                "class_tier": "B_class",
                "tier": "B1",
                "decision_by": "human_anchor",
                "direction_type": "mutual",
                "actor": None,
                "target": None,
                "edge_ref": {"type": "edge", "edge_id": "e012", "kind": "chuan", "members": ["D.b", "H.b"]},
                "basis": "『丑午穿』是并列列举（原文另有『酉戌穿,丑午穿』式并列），对称不赋向；『伤了时上禄』是结果句，只说明受损方，没有给出施动主语。",
                "rule_ref": f"{ACTOR_RULES}:L104-L110",
                "quotes": [q("JB", 139, "丑午穿，伤了时上禄，午代表女人的身体，丑是伤食的墓，又是阴的象，表示妇科方面的疾病了。实际得了子宫癌，午运丑午穿的应期，得病手术。", "direction_support")],
                "decisive": False,
                "conflict_with": ["dc1"],
                "evidence_gap": "same_line",
                "addrs": ["D.b", "H.b"],
                "ten_god_claims": {"D.b": "比肩", "H.b": "偏印"},
            },
            {
                "id": "dc3",
                "layer": "direction",
                "kind": "xing",
                "class": "刑",
                "class_tier": "B_class",
                "tier": "B1",
                "decision_by": "human_anchor",
                "direction_type": "actor_target",
                "actor": "M.b",
                "actor_char": "戌",
                "target": "D.b",
                "target_char": "丑",
                "edge_ref": {"type": "edge", "edge_id": "e010", "kind": "xing", "members": ["M.b", "D.b"]},
                "basis": "原文『命中因有戌坏丑』是主谓宾句：戌为施动主语、丑为受事；engine e010 为 xing(丑戌未 partial)、actor=null。原文用『坏』字，本卡按 engine 既有边 kind=xing 记录，不另造边。",
                "rule_ref": f"{ACTOR_RULES}:L95-L102",
                "quotes": [q("JB", 141, "后经中医治疗，没有转移，治好了，命中因有戌坏丑，否则将过不去午运。", "direction_support")],
                "decisive": True,
                "conflict_with": ["dc1", "dc2"],
                "evidence_gap": "same_line",
                "addrs": ["M.b", "D.b"],
                "ten_god_claims": {"M.b": "劫财", "D.b": "比肩"},
            },
        ],
        "state_candidates": [
            {
                "id": "st1",
                "layer": "state",
                "label": "妇科（子宫癌）：丑＝阴、伤食之墓，午＝女体/禄",
                "result": "病",
                "tier": "B1",
                "decision_by": "human_anchor",
                "anchored_by": ["AQ2"],
                "basis": "原文以丑午穿＋丑为阴/伤食之墓＋午为女体，直指妇科；并记子宫癌、午运手术。",
                "quotes": [
                    q("JB", 139, "丑午穿，伤了时上禄，午代表女人的身体，丑是伤食的墓，又是阴的象，表示妇科方面的疾病了。实际得了子宫癌，午运丑午穿的应期，得病手术。", "state_support"),
                    q("JB", 17, "丑：生殖器、妇科、肛门", "symbol_support"),
                ],
                "conflict_with": ["st2"],
                "decisive": True,
            },
            {
                "id": "st2",
                "layer": "state",
                "label": "心脏/心慌（同章病性：丑午穿主心被伤）",
                "result": "病",
                "tier": "B1",
                "decision_by": "human_anchor",
                "anchored_by": ["AQ2"],
                "basis": "同章病性条把丑午穿读作心脏：『丑午穿--------心是被伤，心慌惊悸』；该读法与本造『午得寅生，旺，所以不得心脏病』的判据互斥，须以事实定夺。",
                "quotes": [
                    q("JB", 123, "丑午穿--------心是被伤，心慌惊悸。", "state_support"),
                    q("JB", 27, "午：心脏、阳亢、血压、神经", "symbol_support"),
                    q("JB", 131, "原局的毛病是丑午穿，午得寅生，旺，所以不得心脏病。", "counter_reading"),
                ],
                "conflict_with": ["st1"],
                "decisive": False,
            },
        ],
        "rescue_candidates": [
            {
                "id": "rs1",
                "layer": "rescue",
                "label": "戌坏丑 → 病源被制，未转移、治好",
                "result": "救",
                "tier": "B1",
                "decision_by": "human_anchor",
                "anchored_by": ["AQ1"],
                "basis": "原文『命中因有戌坏丑，否则将过不去午运』——戌坏丑被当作能过关的原因（救应），与 dc3 同源但用途相反：dc3 是方向，rs1 是救应效果。",
                "quotes": [q("JB", 141, "后经中医治疗，没有转移，治好了，命中因有戌坏丑，否则将过不去午运。", "rescue_support")],
                "decisive": False,
            }
        ],
        "anchor_q": [
            {
                "id": "AQ1",
                "layer": "direction",
                "targets": ["dc1", "dc2"],
                "text": "你的妇科病（或相关手术）确诊之前，是否先发生过『婚姻或家庭重大变故』（分居、离婚、丧偶、家人重病）？",
                "answer_type": "fact_yes_no",
                "discriminator_basis": "dc1 把施力方定在日支丑（夫妻宫）→ 家庭侧先动、病随后；dc2 说两侧同损、无先后。若确有『变故在前、发病在后』的时间顺序，单侧施力读法保留；否则对称读法保留。",
                "rule_ref": f"{ACTOR_RULES}:L104-L110",
                "source_mentions_answer": False,
                "proxy_strength": "medium",
                "if_yes": {"keep": ["dc1"], "eliminate": ["dc2"], "downgrade": []},
                "if_no": {"keep": ["dc2"], "eliminate": ["dc1"], "downgrade": []},
                "if_unknown": {"action": "needs_anchor", "affected": ["dc1", "dc2"]},
            },
            {
                "id": "AQ2",
                "layer": "state",
                "targets": ["st1", "st2"],
                "text": "在那次发病期间，你是否同时出现过心脏、血压或心慌惊悸方面的症状（并被医生记录）？",
                "answer_type": "fact_yes_no",
                "discriminator_basis": "st2 的读法要求心脏侧确有受病记录；st1 的读法要求妇科侧为主。两者在原文中互斥（『午得寅生，旺，所以不得心脏病』），只能由事实定夺。",
                "rule_ref": JB_L9,
                "source_mentions_answer": False,
                "proxy_strength": "high",
                "if_yes": {"keep": ["st2"], "eliminate": [], "downgrade": ["st1"]},
                "if_no": {"keep": ["st1"], "eliminate": ["st2"], "downgrade": []},
                "if_unknown": {"action": "needs_anchor", "affected": ["st1", "st2"]},
            },
        ],
        "gaps": ["G2", "G3", "G4", "G5", "muku_open_close", "suiyun_ten_god", "disease_severity_not_scored"],
        "non_claims": [
            "不判疾病名称、严重程度、生死、应期",
            "不把『丑午穿』直接写成断语；象法条目只是检索依据",
            "不判救应成立（rs1 仅候选）；不判岁运（午运）引动",
        ],
    },
    {
        "card_id": "P0-04",
        "case_key": "C4",
        "domain": "wealth",
        "gender": "乾",
        "four_pillars": "乙巳 己丑 壬辰 辛丑",
        "question": {
            "text": "我的生意和资产做得不小，最担心守不住；我的财到底是从哪来的、能不能守住？",
            "domain": "wealth",
            "prereg_id": None,
            "asked_by": "命主",
        },
        "source": {
            "path": SRC["CG"],
            "locator": "L384-L398（案例）",
            "pillar_quote": [pq("CG", 384), pq("CG", 386)],
            "outcome_quote": q("CG", 394, "行戌运，财库冲入自己发财五年，资产4亿。", "outcome_background"),
            "outcome_note": "原文后续事实：戌运发财五年、资产4亿；乙运坐牢、没收财产、判刑十年（P0 仅备查，不作预测依据）。",
        },
        "palaces": [
            {"addr": "M.b", "role": "月支丑：官星（正官）—财生官、官当财看", "ten_god": "正官", "mapping_rule": "M-06", "basis_quote": q("CG", 392, "原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。", "mapping")},
            {"addr": "D.b", "role": "日支辰：水库/土库，本造『主要功神』", "ten_god": "七杀", "mapping_rule": "M-07", "basis_quote": q("CG", 392, "原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。", "mapping")},
            {"addr": "Y.b", "role": "年支巳：偏财（财源）", "ten_god": "偏财", "mapping_rule": "M-02", "basis_quote": q("CG", 392, "原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。", "mapping")},
        ],
        "material_edges": ["e008", "e004", "e010"],
        "material_edge_reasons": {"e008": "巳丑三合拱(财生官的载体)", "e004": "辛克乙：破坏辰(功神)的克向", "e010": "丑辰破：库被动摇"},
        "direction_candidates": [
            {
                "id": "dc1",
                "layer": "direction",
                "kind": "muku",
                "class": "墓",
                "class_tier": "A_class",
                "tier": "A",
                "decision_by": "agent_auto",
                "direction_type": "actor_target",
                "actor": "D.b",
                "actor_char": "辰",
                "target": "M.b",
                "target_char": "丑",
                "edge_ref": {"type": "duan_candidate", "mode": "墓用", "members": ["D.b", "M.b"], "actor": "D.b"},
                "basis": "engine 墓用候选 (D.b,M.b)、actor=D.b（库收，符合 actor-rules §4.9）。原文『月时丑官都入辰墓』是位移句（按 §4.9 只给位移不给向），但紧接『辰是主要功神』把辰标为主功方；两据合并取库→入库方。",
                "rule_ref": f"{ACTOR_RULES}:L150-L166",
                "quotes": [q("CG", 392, "原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。", "direction_support")],
                "decisive": True,
                "conflict_with": [],
                "evidence_gap": "doctrine_only",
                "addrs": ["D.b", "M.b"],
                "ten_god_claims": {"D.b": "七杀", "M.b": "正官"},
            },
            {
                "id": "dc2",
                "layer": "direction",
                "kind": "ke",
                "class": "克",
                "class_tier": "A_class",
                "tier": "A",
                "decision_by": "agent_auto",
                "direction_type": "actor_target",
                "actor": "H.s",
                "actor_char": "辛",
                "target": "Y.s",
                "target_char": "乙",
                "edge_ref": {"type": "edge", "edge_id": "e004", "kind": "ke", "members": ["H.s", "Y.s"]},
                "basis": "原文『辛克乙等于破坏了辰』是主动句，辛为句法主语；engine e004 ke(辛,乙)、actor=H.s 与之一致。此向用于『守不住』一侧（印克伤官、破坏功神辰）。",
                "rule_ref": f"{ACTOR_RULES}:L120-L127",
                "quotes": [q("CG", 396, "乙酉运之乙运，这里的乙不仅代表年上的乙，也代表辰，乙透干有克无生，辛克乙等于破坏了辰。主凶。", "direction_support")],
                "decisive": True,
                "conflict_with": [],
                "evidence_gap": "same_line",
                "addrs": ["H.s", "Y.s"],
                "ten_god_claims": {"H.s": "正印", "Y.s": "伤官"},
            },
            {
                "id": "dc3",
                "layer": "direction",
                "kind": "sheng",
                "class": "生",
                "class_tier": "A_class",
                "tier": "A",
                "decision_by": "agent_auto",
                "direction_type": "actor_target",
                "actor": "Y.b",
                "actor_char": "巳",
                "target": "M.b",
                "target_char": "丑",
                "edge_ref": {"type": "duan_candidate", "mode": "生泄用", "members": ["Y.b", "M.b"], "actor": "Y.b"},
                "basis": "原文『年上巳生合丑官，财生官』：巳为句法主语、生合为谓语；engine 生泄用候选 (Y.b,M.b)、actor=Y.b 一致。财源=年支巳(偏财)生月支丑(官)。",
                "rule_ref": f"{ACTOR_RULES}:L129-L137",
                "quotes": [q("CG", 392, "原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。", "direction_support")],
                "decisive": True,
                "conflict_with": [],
                "evidence_gap": "same_line",
                "addrs": ["Y.b", "M.b"],
                "ten_god_claims": {"Y.b": "偏财", "M.b": "正官"},
            },
        ],
        "state_candidates": [
            {
                "id": "st1",
                "layer": "state",
                "label": "官入辰墓＋财库冲入 → 富命",
                "result": "成",
                "tier": "B1",
                "decision_by": "human_anchor",
                "anchored_by": ["ED1"],
                "basis": "原局：月时丑官入辰墓、巳生丑官，官当财看，故断富命；岁运戌运冲开财库，五年发财、资产4亿。",
                "quotes": [
                    q("CG", 392, "原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。", "state_support"),
                    q("CG", 394, "行戌运，财库冲入自己发财五年，资产4亿。", "state_support"),
                ],
                "conflict_with": ["st2"],
                "decisive": True,
            },
            {
                "id": "st2",
                "layer": "state",
                "label": "辛克乙破坏辰 → 主凶；乙运坐牢、没收财产",
                "result": "败",
                "tier": "B1",
                "decision_by": "expert_single_choice",
                "anchored_by": ["ED1"],
                "basis": "岁运乙透（代表辰）被辛克、辰被破坏，原文判『主凶』；同运癸未年坐牢、没收财产、判刑十年。",
                "quotes": [
                    q("CG", 396, "乙酉运之乙运，这里的乙不仅代表年上的乙，也代表辰，乙透干有克无生，辛克乙等于破坏了辰。主凶。", "state_support"),
                    q("CG", 398, "癸未年刚入乙运坐牢，因非法集资而没收产财。判刑十年。现已出狱。", "state_support"),
                ],
                "conflict_with": ["st1"],
                "decisive": True,
            },
            {
                "id": "st3",
                "layer": "state",
                "label": "财弱官旺、官当财看（财的定义口径）",
                "result": "needs_anchor",
                "tier": "C",
                "decision_by": "needs_anchor",
                "anchored_by": [],
                "basis": "『官当财看』是本造把官星当财的口径说明；它决定『财』指什么，不回答能否守住，故不单独成断。",
                "quotes": [q("CG", 392, "原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。", "definition_reference")],
                "conflict_with": [],
                "decisive": False,
            },
        ],
        "rescue_candidates": [
            {
                "id": "rs1",
                "layer": "rescue",
                "label": "行戌运，财库冲入自己 → 岁运层面的『开库得财』",
                "result": "应",
                "tier": "C",
                "decision_by": "needs_anchor",
                "basis": "『财库冲入自己』是岁运引动（戌运）而非原局救应；本卡快照 dayun_index=null，按规格 §4.1 不跨快照引用，故只记录为岁运候选、不判。",
                "quotes": [q("CG", 394, "行戌运，财库冲入自己发财五年，资产4亿。", "suiyun_reference")],
                "decisive": False,
            }
        ],
        "anchor_q": [],
        "expert_decision": {
            "id": "ED1",
            "required": True,
            "layer": "state",
            "question": "回答『财能不能守住』时，下列两条证据哪一条优先：原局『官入辰墓＋财库冲入』的富命，还是岁运『辛克乙破坏辰』的破局？",
            "options": [
                "原局富命为主，破局只作应期（先富后破）",
                "岁运破局为主，原局富命只说明曾经（破多富少）",
                "两不可判，保持 needs_anchor",
            ],
            "basis": "两条都有原文直断，且分属原局/岁运两层；本卡不代选（不做方向自动承诺），交专家单选。",
            "quotes": [
                q("CG", 392, "原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。", "option_a"),
                q("CG", 396, "乙酉运之乙运，这里的乙不仅代表年上的乙，也代表辰，乙透干有克无生，辛克乙等于破坏了辰。主凶。", "option_b"),
            ],
            "decision": None,
            "decision_note": "anchor_a / decision 留空，交专家或中枢填写；Agent 不代答。",
        },
        "gaps": ["G2", "G3", "G4", "G5", "muku_open_close", "suiyun_ten_god", "snapshot_dayun_null"],
        "non_claims": [
            "不判财运高低、破财年份、牢狱、生死",
            "不把『富命』或『主凶』择一写成结论（本条交 ED1 专家裁决）",
            "不判岁运引动；不跨快照引用 edge_id",
        ],
    },
]


# --------------------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------------------
class CardValidator:
    def __init__(self, case_key: str):
        self.key = case_key
        self.allj = load_engine(ENGINE[case_key]["all"])
        self.relj = load_engine(ENGINE[case_key]["rel"])
        self.addr_set = set()
        self.tg = {}
        self.hidden = {}
        for p in self.allj["chart"]["pillars"]:
            self.addr_set.add(p["stem"]["addr"])
            self.addr_set.add(p["branch"]["addr"])
            self.tg[p["stem"]["addr"]] = p["stem"]["ten_god"]
            self.tg[p["branch"]["addr"]] = p["branch"]["main_ten_god"]
            self.hidden[p["branch"]["addr"]] = {h["c"]: h["g"] for h in p["branch"]["hidden"]}
        self.edges = {e["id"]: e for e in self.relj["edges"]}
        self.duan = self.allj["duan_zuogong"]["candidates"]

    # -- primitive checks -------------------------------------------------------------
    def check_address(self, addr: str) -> dict:
        ok = addr in self.addr_set
        return {"status": "pass" if ok else "fail", "addr": addr, "detail": "engine 物理地址存在" if ok else "engine 未输出该地址"}

    def check_ten_god(self, addr: str, god: str) -> dict:
        if addr not in self.tg:
            return {"status": "fail", "addr": addr, "claimed": god, "detail": "地址不存在"}
        if self.tg[addr] == god:
            return {"status": "pass", "addr": addr, "claimed": god, "engine": self.tg[addr], "via": "干支本气/透干"}
        if god in self.hidden.get(addr, {}).values():
            return {"status": "pass", "addr": addr, "claimed": god, "engine": self.tg[addr], "via": "藏干十神"}
        return {"status": "fail", "addr": addr, "claimed": god, "engine": self.tg[addr], "detail": "十神不符"}

    def check_edge(self, ref: dict) -> dict:
        if ref["type"] == "edge":
            e = self.edges.get(ref["edge_id"])
            if not e:
                return {"status": "fail", "ref": ref, "detail": "engine relations 无此 edge_id"}
            if e["kind"] != ref["kind"]:
                return {"status": "fail", "ref": ref, "detail": f"kind 不符：engine={e['kind']} claim={ref['kind']}"}
            if set(e["members"]) != set(ref["members"]):
                return {"status": "fail", "ref": ref, "detail": f"members 不符：engine={e['members']} claim={ref['members']}"}
            return {"status": "pass", "ref": ref, "edge_id": e["id"], "kind": e["kind"], "members": e["members"], "engine_actor": None, "detail": "边存在且 kind/members 一致；动态边 actor 由 engine 保持 null"}
        hits = [
            c
            for c in self.duan
            if c.get("mode") == ref["mode"]
            and list(c.get("members") or []) == list(ref["members"])
            and c.get("actor") == ref["actor"]
        ]
        if not hits:
            return {"status": "fail", "ref": ref, "detail": "duan_zuogong 无匹配候选（mode/members/actor）"}
        return {"status": "pass", "ref": ref, "candidate_mode": ref["mode"], "members": ref["members"], "engine_actor": ref["actor"], "detail": "engine 做功候选命中（固定类）"}

    def check_quote(self, quote: dict) -> dict:
        lines = src_lines(quote["src"])
        idx = quote["line"] - 1
        if idx < 0 or idx >= len(lines):
            return {"status": "fail", "source_ref": f"{SRC[quote['src']]}:L{quote['line']}", "detail": "行号越界"}
        ok = quote["text"] in lines[idx]
        return {
            "status": "pass" if ok else "fail",
            "source_ref": f"{SRC[quote['src']]}:L{quote['line']}",
            "detail": "逐字命中该行" if ok else "该行未找到逐字文本",
            "role": quote.get("role"),
        }

    # -- composite --------------------------------------------------------------------
    def validate_item(self, item: dict) -> dict:
        checks = {}
        addrs = item.get("addrs") or []
        addr_res = [self.check_address(a) for a in addrs]
        checks["address"] = {
            "status": "pass" if all(r["status"] == "pass" for r in addr_res) else ("n/a" if not addr_res else "fail"),
            "items": addr_res,
        }
        ref = item.get("edge_ref")
        checks["edge"] = self.check_edge(ref) if ref else {"status": "n/a", "detail": "本项不含边引用"}
        claims = item.get("ten_god_claims") or {}
        tg_res = [self.check_ten_god(a, g) for a, g in claims.items()]
        checks["ten_god"] = {
            "status": "pass" if all(r["status"] == "pass" for r in tg_res) else ("n/a" if not tg_res else "fail"),
            "items": tg_res,
        }
        quotes = item.get("quotes") or []
        qt_res = [self.check_quote(x) for x in quotes]
        checks["quote"] = {
            "status": "pass" if all(r["status"] == "pass" for r in qt_res) else ("n/a" if not qt_res else "fail"),
            "items": qt_res,
        }
        hard = [checks["address"], checks["edge"], checks["ten_god"], checks["quote"]]
        status = "valid" if all(c["status"] in ("pass", "n/a") for c in hard) else "invalid"
        return {"checks": checks, "status": status}

    # -- seeded errors ----------------------------------------------------------------
    def seeded_error_test(self) -> dict:
        results = []
        # 1) fake address
        r = self.check_address("Q.b")
        results.append({"seeded": "fake_address:Q.b", "caught": r["status"] == "fail", "detail": r["detail"]})
        # 2) fake edge id
        r = self.check_edge({"type": "edge", "edge_id": "e999", "kind": "chong", "members": ["M.b", "D.b"]})
        results.append({"seeded": "fake_edge:e999", "caught": r["status"] == "fail", "detail": r["detail"]})
        # 3) wrong ten god on D.b
        wrong = "正印" if self.tg.get("D.b") != "正印" else "偏财"
        r = self.check_ten_god("D.b", wrong)
        results.append({"seeded": f"wrong_ten_god:D.b={wrong}", "caught": r["status"] == "fail", "detail": r.get("detail", "")})
        # 4) tampered quote
        r = self.check_quote({"src": "HY", "line": 15, "text": "看婚姻的好坏，应以配偶宫为主，配偶星为辅。（篡改）"})
        results.append({"seeded": "tampered_quote:HY:L15", "caught": r["status"] == "fail", "detail": r["detail"]})
        return {
            "tested": len(results),
            "caught": sum(1 for x in results if x["caught"]),
            "pass": all(x["caught"] for x in results),
            "items": results,
        }


REL_MAP = {
    "ke": "ke",
    "sheng": "sheng",
    "muku": "muku",
    "chong": "chong",
    "liuhe": "he",
    "wuhe": "he",
    "zhi_anhe": "he",
    "ganzhi_zihe": "he",
    "chuan": "chuan",
    "xing": "xing",
    "po": "po",
}
DIR_MAP = {"actor_target": "actor_to_target", "mutual": "mutual", "needs_anchor": "undetermined"}
STATE_MAP = {"成": "成局", "败": "破局", "救": "逢救应化解"}
WINDOWS = {
    ("P0-01", "AQ1"): "2000-01..2025-12",
    ("P0-01", "AQ2"): "2000-01..2025-12",
    ("P0-02", "AQ1"): "2015-01..2025-12",
    ("P0-03", "AQ1"): "1995-01..2025-12",
    ("P0-03", "AQ2"): "1995-01..2025-12",
    ("P0-04", "AQ1"): "2010-01..2025-12",
}


def to_candidate_set(card: dict) -> None:
    """Rename + derive fields to agent-candidate-set/v1 (T-196 §7) without faking a selection."""
    for bucket in ("direction_candidates", "state_candidates", "rescue_candidates"):
        for it in card.get(bucket, []):
            if "id" in it:
                it["option_id"] = it.pop("id")
    for a in card.get("anchor_q", []):
        if "id" in a:
            a["qid"] = a.pop("id")

    for c in card["direction_candidates"]:
        ref = c.get("edge_ref") or {}
        basis = []
        if ref.get("type") == "edge":
            basis.append({"kind": "engine_edge", "ref": ref["edge_id"], "note": f"{ref['kind']}{ref['members']}"})
        elif ref.get("type") == "duan_candidate":
            basis.append(
                {
                    "kind": "engine_candidate",
                    "ref": "duan_zuogong.candidates",
                    "note": f"{ref['mode']}{ref['members']} actor={ref['actor']}",
                }
            )
        for q in c.get("quotes") or []:
            kind = "source_directive" if q["role"] in ("direction_support", "actor_support", "relation_support") else "source_rule"
            basis.append({"kind": kind, "ref": q["source_ref"], "note": q["role"]})
        c["basis_text"] = c.pop("basis")
        c["basis"] = basis
        c["claim"] = {
            "relation": REL_MAP.get(c["kind"], c["kind"]),
            "direction": DIR_MAP.get(c["direction_type"], "undetermined"),
            "members": list(ref.get("members") or c.get("addrs") or []),
            "actor": c.get("actor"),
            "target": c.get("target"),
        }
        first = (c.get("quotes") or [{}])[0]
        c["source_ref"] = first.get("source_ref")
        c["quote"] = first.get("text")
        c.setdefault("conflict_class", "chuan_zhi" if c.get("evidence_gap") == "chuan_zhi" else None)
        c.setdefault("engine_note", None if ref.get("type") == "edge" else "engine_candidate_no_edge")

    for s in card["state_candidates"]:
        s["state_label"] = s.pop("label")
        s["state"] = STATE_MAP.get(s.get("result"))
        s["basis_text"] = s.pop("basis")
        s["basis"] = [{"kind": "source_rule", "ref": q["source_ref"], "note": q["role"]} for q in s.get("quotes") or []]
        first = (s.get("quotes") or [{}])[0]
        s["source_ref"] = first.get("source_ref")
        s["quote"] = first.get("text")
        s.setdefault("conflict_class", None)
        s.setdefault("engine_note", None)

    for r in card["rescue_candidates"]:
        r["rescuer"] = None
        r["rescued"] = None
        r["status"] = "not_evaluable"
        r["rescue_primitive"] = None
        r["external_audit_id"] = None
        r["basis_text"] = r.pop("basis")
        r["basis"] = [{"kind": "source_rule", "ref": q["source_ref"], "note": q["role"]} for q in r.get("quotes") or []]
        first = (r.get("quotes") or [{}])[0]
        r["source_ref"] = first.get("source_ref")
        r["quote"] = first.get("text")
        r["decisive"] = False

    for a in card.get("anchor_q", []):
        a["answer_type"] = "yes_no"
        a["discriminates"] = a.pop("targets")
        y, n, u = a["if_yes"], a["if_no"], a["if_unknown"]
        a["elimination"] = [
            {"answer": "yes", "eliminates": y.get("eliminate", []), "keeps": y.get("keep", [])},
            {"answer": "no", "eliminates": n.get("eliminate", []), "keeps": n.get("keep", [])},
            {"answer": "unknown", "eliminates": u.get("affected", []), "keeps": []},
        ]
        a["fact_window"] = WINDOWS.get((card["card_id"], a["qid"]), "2015-01..2025-12")
        a["fact_domain"] = card["domain"] if card["domain"] in ("marriage", "career", "health", "wealth") else "other"

    agg = card["engine_validation"]["aggregate"]
    se = card["engine_validation"]["seeded_error"]
    card["engine_validation"]["v2"] = {
        "snapshot": card["snapshot"],
        "address": {"status": "pass" if agg["address"]["pass"] == agg["address"]["total"] else "fail", "checked": agg["address"]["total"], "failures": []},
        "edge": {"status": "pass" if agg["edge"]["pass"] == agg["edge"]["total"] else "fail", "checked": agg["edge"]["total"], "failures": [], "reason": None},
        "ten_god": {"status": "pass" if agg["ten_god"]["pass"] == agg["ten_god"]["total"] else "fail", "checked": agg["ten_god"]["total"], "failures": []},
        "quote": {
            "status": "pass"
            if agg["quote"]["pass"] == agg["quote"]["total"]
            and card["engine_validation"]["source_and_palace_quotes"]["pass"] == card["engine_validation"]["source_and_palace_quotes"]["total"]
            else "fail",
            "checked": agg["quote"]["total"] + card["engine_validation"]["source_and_palace_quotes"]["total"],
            "failures": [],
        },
        "seeded_error": {
            "status": "pass" if se["pass"] else "fail",
            "mode": "card_scan",
            "checked": [x["seeded"] for x in se["items"]],
            "failures": [x["seeded"] for x in se["items"] if not x["caught"]],
        },
        "overall": "pass" if card["engine_validation"]["all_pass"] else "fail",
    }


def main() -> int:
    out_cards = []
    failures = 0
    tier_count = {"A": 0, "B1": 0, "B2": 0, "C": 0}
    anchor_count = 0
    b2_units = 0

    for card in CARDS:
        v = CardValidator(card["case_key"])
        facts = brief_facts(v.allj, v.relj)
        assert facts["chart_id"] and facts["four_pillars"] == card["four_pillars"], (card["card_id"], facts["four_pillars"])

        # snapshot binding + is_conclusion=false on every candidate layer
        card["snapshot"] = {"chart_id": facts["chart_id"], "dayun_index": None, "liunian_year": None}
        for bucket in ("direction_candidates", "state_candidates", "rescue_candidates"):
            for item in card.get(bucket, []):
                item["is_conclusion"] = False

        # validate source/pillar/palace quotes as well
        extra = []
        for x in card["source"].get("pillar_quote", []):
            extra.append({"where": "source.pillar_quote", "quote": x})
        if card["source"].get("outcome_quote"):
            extra.append({"where": "source.outcome_quote", "quote": card["source"]["outcome_quote"]})
        for p in card["palaces"]:
            if p.get("basis_quote"):
                extra.append({"where": f"palaces.{p['addr']}.basis_quote", "quote": p["basis_quote"]})
        card["source_quote_validation"] = [{"where": e["where"], **v.check_quote(e["quote"])} for e in extra]

        # validate every candidate / state / rescue
        for bucket in ("direction_candidates", "state_candidates", "rescue_candidates"):
            for item in card.get(bucket, []):
                res = v.validate_item(item)
                item["engine_validation"] = res
                if res["status"] != "valid":
                    failures += 1
                    print(f"[FAIL] {card['card_id']} {item['id']} -> {json.dumps(res, ensure_ascii=False)[:400]}")

        # card-level aggregate
        agg = {"address": {"total": 0, "pass": 0}, "edge": {"total": 0, "pass": 0}, "ten_god": {"total": 0, "pass": 0}, "quote": {"total": 0, "pass": 0}}
        for bucket in ("direction_candidates", "state_candidates", "rescue_candidates"):
            for item in card.get(bucket, []):
                for k in agg:
                    st = item["engine_validation"]["checks"][k]["status"]
                    if st != "n/a":
                        agg[k]["total"] += 1
                        if st == "pass":
                            agg[k]["pass"] += 1
        seeded = v.seeded_error_test()
        card["engine_validation"] = {
            "aggregate": agg,
            "source_and_palace_quotes": {
                "total": len(card["source_quote_validation"]),
                "pass": sum(1 for x in card["source_quote_validation"] if x["status"] == "pass"),
                "items": card["source_quote_validation"],
            },
            "seeded_error": seeded,
            "invalid_items": [
                f"{b}/{i['id']}"
                for b in ("direction_candidates", "state_candidates", "rescue_candidates")
                for i in card.get(b, [])
                if i["engine_validation"]["status"] != "valid"
            ],
            "all_pass": seeded["pass"]
            and all(x["pass"] == x["total"] for x in agg.values() if x["total"] > 0)
            and all(x["status"] == "pass" for x in card["source_quote_validation"]),
        }
        if not card["engine_validation"]["all_pass"]:
            failures += 1
        for x in card["source_quote_validation"]:
            if x["status"] != "pass":
                print(f"[FAIL-QUOTE] {card['card_id']} {x['where']} {x.get('source_ref')}")

        # tiers / decisions
        cand_tiers = [c["tier"] for c in card["direction_candidates"]]
        for t in cand_tiers:
            tier_count[t] += 1

        # P0-04：原局富 vs 岁运破属成败层，不是方向层 B2（analysis-card-v2 §5.3）；
        # 改为 state 锚点题，expert_decision 置 null。原文已写结局 → 标 source_mentions_answer=true。
        ed = card.get("expert_decision")
        if ed and ed.get("required"):
            card["state_anchor_note"] = {
                "converted_from": "expert_decision(ED1)",
                "reason": "analysis-card-v2 §5.3 的 B2 只用于方向候选之间『无可观测事实可分』；原局富/岁运破属成败层，改按 state 锚点题处理（state_tier=B1）。",
                "previous_options": ed.get("options"),
            }
            card["anchor_q"].append(
                {
                    "id": "AQ1",
                    "layer": "state",
                    "targets": ["st1", "st2"],
                    "text": "你过去是否经历过资产被一次性清空（罚没、没收、强制清算或巨额赔付）？",
                    "answer_type": "fact_yes_no",
                    "discriminator_basis": "st2 的破局读法要求『资产被一次性打掉』这一已发生事实；st1 的富命读法只要求财富曾经形成。若确已清空，破局读法优先；若从未清空，保留富命读法。",
                    "rule_ref": f"{SRC['CG']}:L396-L398",
                    "source_mentions_answer": True,
                    "proxy_strength": "high",
                    "if_yes": {"keep": ["st2"], "eliminate": ["st1"], "downgrade": []},
                    "if_no": {"keep": ["st1"], "eliminate": ["st2"], "downgrade": []},
                    "if_unknown": {"action": "needs_anchor", "affected": ["st1", "st2"]},
                }
            )
        card["expert_decision"] = None

        dir_tier = (
            "A"
            if all(t == "A" for t in cand_tiers)
            else "B1"
            if "B1" in cand_tiers
            else "C"
        )
        card["direction_tier"] = dir_tier
        card["state_tier"] = "B1" if any(a.get("layer") == "state" for a in card["anchor_q"]) else "not_claimed"
        card["rescue_tier"] = "C" if any(r["tier"] == "C" for r in card["rescue_candidates"]) else "not_claimed"
        card["state_scope"] = "not_claimed"
        card["rescue_scope"] = "candidate_only"
        card["card_status"] = "valid"
        card["pending"] = "anchor_q" if card["anchor_q"] else "none"
        card["tier"] = (
            "B1"
            if card["anchor_q"] and dir_tier in ("A", "B1")
            else dir_tier
        )
        card["decision_by"] = {
            "A": "engine_fixed",
            "B1": "anchor_fact",
            "B2": "expert_judgment",
            "C": "needs_anchor",
        }[card["tier"]]
        reason = []
        reason.append({"A": "direction:engine_fixed", "B1": "direction:anchor_conflict", "C": "direction:no_source"}[dir_tier])
        reason.append("state:conflict" if card["state_tier"] == "B1" else "state:not_claimed")
        reason.append("rescue:candidate_only")
        if card["direction_tier"] == "A" and card["tier"] == "B1":
            reason.append("pending:state_anchor")
        card["tier_reason"] = reason
        anchor_count += len(card["anchor_q"])
        card["anchor_a"] = []
        card["anchor_a_note"] = "留空交人类/命主回答；Agent 不代答、不据原文后续事实填写。"
        card["selected_option"] = None
        card["selection_source"] = "needs_anchor"
        card["not_auto_selected"] = True
        card["facts"] = facts
        card["provenance"] = {
            "engine_cmd": f'{PY} -m engine.cli all --pillars "{card["four_pillars"]}" --gender {card["gender"]} --json',
            "engine_relations_cmd": f'{PY} -m engine.cli relations --pillars "{card["four_pillars"]}" --gender {card["gender"]} --json',
            "engine_chart_id": facts["chart_id"],
            "engine_profile": facts["profile"],
            "engine_input_limitations": facts["input_limitations"],
            "theory_cmd": None,
            "quote_source": "直接回原文核对：每条 quote 用 path:Ln 定位并做逐字子串校验（不经过检索器摘要）",
            "source_paths": sorted({SRC[x["src"]] for b in ("source",) for x in card["source"].get("pillar_quote", [])} | {SRC[x["src"]] for b in ("direction_candidates", "state_candidates", "rescue_candidates") for i in card[b] for x in (i.get("quotes") or [])}),
            "built_by": "T-197 P0 agent（子代理会话）",
            "built_at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
        }
        to_candidate_set(card)
        out_cards.append(card)

    # pack-level anchor questions
    all_aq = []
    for c in out_cards:
        for a in c.get("anchor_q", []):
            item = dict(a)
            item["card_id"] = c["card_id"]
            item["answer"] = None
            all_aq.append(item)

    metrics = {
        "case_count": len(out_cards),
        "domains": sorted({c["domain"] for c in out_cards}),
        "direction_candidates": sum(len(c["direction_candidates"]) for c in out_cards),
        "candidate_tiers": {
            "A": sum(1 for c in out_cards for x in c["direction_candidates"] if x["tier"] == "A"),
            "B1": sum(1 for c in out_cards for x in c["direction_candidates"] if x["tier"] == "B1"),
            "B2": sum(1 for c in out_cards for x in c["direction_candidates"] if x["tier"] == "B2"),
            "C": sum(1 for c in out_cards for x in c["direction_candidates"] if x["tier"] == "C"),
        },
        "anchor_questions": anchor_count,
        "b2_expert_decisions": b2_units,
        "state_candidates": sum(len(c["state_candidates"]) for c in out_cards),
        "rescue_candidates": sum(len(c["rescue_candidates"]) for c in out_cards),
        "engine_validation_failures": sum(
            1 for c in out_cards for b in ("direction_candidates", "state_candidates", "rescue_candidates") for i in c[b] if i["engine_validation"]["status"] != "valid"
        ),
        "source_palace_quotes": {
            "total": sum(len(c["source_quote_validation"]) for c in out_cards),
            "pass": sum(1 for c in out_cards for x in c["source_quote_validation"] if x["status"] == "pass"),
        },
        "seeded_error_pass": all(c["engine_validation"]["seeded_error"]["pass"] for c in out_cards),
    }
    total_cand = metrics["direction_candidates"]
    metrics["candidate_tier_share"] = {k: round(v / total_cand, 4) for k, v in metrics["candidate_tiers"].items()}
    b_units = metrics["candidate_tiers"]["B1"] + metrics["candidate_tiers"]["B2"] + anchor_count + b2_units
    metrics["b2_share_of_B_units"] = round(b2_units / b_units, 4) if b_units else 0.0
    metrics["a_share_vs_p0_gate"] = {
        "gate": "A 档自动占比 ≥50%（T-196 卡 §1.1 P0 gate）",
        "actual": metrics["candidate_tier_share"]["A"],
        "verdict": "未达" if metrics["candidate_tier_share"]["A"] < 0.5 else "达标",
        "note": "冲/合/穿/刑不得 A（中枢 2026-10-30 追加），真实婚/事业/健康/财问题的 material edge 多为对称关系或带竞争候选，固定克/生/化/墓仅 3/12。",
    }

    # ---- seeded_error self_test (20 fixtures: 5 addr / 5 edge / 5 ten_god / 5 quote) ----
    validators = [CardValidator(c["case_key"]) for c in CARDS]
    v0 = validators[0]
    self_checked: list[str] = []
    self_fail: list[str] = []
    for a in ["Q.b", "Z.b", "X1.b", "DY9.b", "LN2099.b"]:
        self_checked.append(f"addr:{a}")
        if v0.check_address(a)["status"] != "fail":
            self_fail.append(f"addr:{a}")
    for e in ["e999", "e000", "e100", "e0001", "e20x"]:
        self_checked.append(f"edge:{e}")
        if v0.check_edge({"type": "edge", "edge_id": e, "kind": "chong", "members": ["M.b", "D.b"]})["status"] != "fail":
            self_fail.append(f"edge:{e}")
    pool = ["正印", "偏财", "食神", "七杀", "比肩", "正官"]
    tg_fixtures = [(v, "D.b") for v in validators] + [(validators[0], "M.s")]
    for v, addr in tg_fixtures:
        actual = v.tg.get(addr)
        wrong = next(x for x in pool if x != actual)
        self_checked.append(f"ten_god:{v.key}:{addr}={wrong}")
        if v.check_ten_god(addr, wrong)["status"] != "fail":
            self_fail.append(f"ten_god:{v.key}:{addr}={wrong}")
    for src, line in [("HY", 15), ("HY", 29), ("JG", 27), ("JB", 139), ("CG", 392)]:
        real = src_lines(src)[line - 1]
        tampered = real[: max(10, len(real) // 2)] + "（篡改）"
        self_checked.append(f"quote:{src}:L{line}")
        if v0.check_quote({"src": src, "line": line, "text": tampered})["status"] != "fail":
            self_fail.append(f"quote:{src}:L{line}")
    self_test = {
        "mode": "self_test",
        "checked": self_checked,
        "failures": self_fail,
        "detected": len(self_checked) - len(self_fail),
        "total": len(self_checked),
        "status": "pass" if not self_fail else "fail",
    }
    metrics["self_test"] = {"detected": self_test["detected"], "total": self_test["total"], "pass": self_test["status"] == "pass"}

    schema_compat = {
        "target": "agent-candidate-set/v1（生成器 §7）；选定后装配为 analysis-card/v2",
        "mapped_fields": [
            "option_id / claim{relation,direction,members,actor,target} / basis[{kind,ref,note}] / source_ref / quote / decisive / conflict_with / conflict_class / engine_note",
            "direction_tier / state_tier / rescue_tier / tier / decision_by / card_status / pending",
            "anchor_q{qid,text,fact_window,fact_domain,answer_type=yes_no,discriminates,elimination[yes/no/unknown]} / anchor_a",
            "engine_validation{snapshot,address,edge,ten_god,quote,seeded_error,overall}",
        ],
        "extensions": [
            "claim.direction='undetermined'：v2 枚举只有 actor_to_target|mutual，本包为『合/冲但方向不可判』的候选保留第三值",
            "basis_text：中文依据散文（v2 的 basis 只允许结构项）",
            "state_label：成败候选的原文词（成/败/疑/多现/病/救/应），state 三态另存",
            "facts / palaces / material_edges / material_edge_reasons：证据包层（供第三方重推）",
        ],
        "not_implemented": {
            "selected_option/selected_state/selected_rescue": "T-197 明令不自动选定；pending=anchor_q 前不得填",
            "t1–t5 与 statement/statement_claims": "analysis-card/v2 在选定后才装配；本包是候选集不是成品卡",
            "anchor_a 实体答案": "待人类/命主回答；Agent 不代答",
            "agent_top1": "生成器 §8.2 的 B1 lift 基线，本包未冻结（避免锚定）",
        },
        "known_conflicts": [
            "v2 的 A 档要求 selected_option 已填且 pending=none；T-197 禁止代选 → direction_tier=A 的卡仍保持 selected_option=null",
            "v2 的 C 档也用 selected_option=null + selection_source=needs_anchor；因此『待自动确认的 A』与『无源 C』在本包只能靠 direction_tier/pending 区分",
        ],
    }

    pack = {
        "schema": "p0-cards/v1",
        "task": "T-197",
        "generated_at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
        "repo": r"E:\Git hub\mangpai-fusion",
        "spec_refs": [
            "tasks/T-197/PROMPT.md",
            "docs/specs/fact-evidence-pack-v1.md",
            "docs/specs/actor-rules-v1.md",
            "docs/specs/analysis-card-v2.md（T-196 落盘后据其对字段/枚举）",
            "docs/specs/agent-candidate-generator-v1.md §7（agent-candidate-set/v1 字段）",
            "docs/goals/first-principle-agent-first-v1.md",
        ],
        "tier_scheme": {
            "A": "仅固定克/生/化/墓；engine 固定规则与原文同向、无竞争候选；可 agent_auto。冲/合/穿/刑/破一律不得 A；原文『无冲突』不能自动升 A。",
            "B1": "锚点消歧（默认）：2–3 个候选的分歧可由『命主已发生事实』的是非题区分；只问事实，不让人选方向。",
            "B2": "仅当没有任何可观测事实可区分候选时启用：专家单选或转 needs_anchor，必须带 source/quote；占比单列。",
            "C": "无源（原文未给该方向）、或与已冻结规则冲突 → needs_anchor，不写成断语。",
        },
        "isolation": {
            "read_answers": False,
            "read_restricted": False,
            "files_read": [
                "tasks/T-197/PROMPT.md",
                "docs/specs/fact-evidence-pack-v1.md",
                "docs/specs/actor-rules-v1.md",
                "tasks/T-196/PROMPT.md",
                "tasks/T-196/STATUS.md",
                "META/r-tool-run-v1.json",
                "META/r-tool-run-routing-v1.json",
                "sources/duan/*（引文原文）",
                "engine.cli 输出（tasks/T-197/_engine/*.json）",
                "盲卷/问题卷仅取四柱用于查重：META/p1-fixed-20-blind-v1.json、p1-fresh-40-v1.json、p1-anchor-60-blind-v1.json、p1-holdout-v1.json、single-chart-cases-v1.json",
            ],
            "not_read": [
                "任何 answers / golden / anchor-answers / fresh-answers / holdout-answers 文件",
                "META/p1-system-run*",
                "META/routing-prereg-v1.json 及 routing-questions 的 expected_evidence",
            ],
            "exclusion_check": {
                "method": "把上列盲卷/问题卷的 four_pillars 归一化后与本包 4 盘逐字比对",
                "excluded_sets": {"F20": 20, "PF": 40, "A60": 60, "P1-H": 20, "OLD3": 3},
                "unique_pillar_sets": 133,
                "overlap": 0,
                "note": "旧 3 卡（C1/C2/C3，RF-2026-000125/000438/000894）已并入排除集。",
            },
            "no_git_write": True,
            "no_engine_change": True,
            "no_scorer": True,
        },
        "schema_compat": schema_compat,
        "seeded_error_self_test": self_test,
        "metrics": metrics,
        "cards": out_cards,
        "anchor_questions": all_aq,
        "known_gaps": [
            "T-196 三份规格在本卡生成途中落盘（analysis-card-v2 / agent-candidate-generator-v1 / first-principle-agent-first-v1）；本包已按 agent-candidate-set/v1 改名与补字段，但仍是 pending candidate set（pending=anchor_q），不是可交付的 analysis-card/v2（T-197 明令不选定）。",
            "与 v2 的两处口径冲突：①v2 的 A 档要求 selected_option 已填、pending=none，而 T-197 禁止 Agent 代选 → 本包 direction_tier=A 的卡仍 selected_option=null；②v2 的 C 档要求 selected_option=null 且 selection_source=needs_anchor，与 A 未选状态同形，故本包用 tier/pending 区分『待自动确认的 A』与『无源的 C』。",
            "四柱输入无出生时刻：engine input_limitations 明确不起运/不给大运公历年份；本包全部 dayun_index=null、liunian_year=null。",
            "G5 救应未判：engine.structures 的 rescuer 命中只作要件，不作救应结论。",
            "『寅申之冲，寅多作用一次』的『作用一次』是计数用语，本卡按 same_page 缺口记为方向依据，是否够格由中枢裁。",
            "P0-04 的原局富/岁运破属成败层，按 analysis-card-v2 §5.3 不适用方向层 B2；已改为 state 锚点题（原文已写结局 → source_mentions_answer=true），expert_decision 置 null，本包 B2 = 0。",
        ],
    }

    out_path = os.path.join(ROOT, "META", "p0-cards-v1.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(pack, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print(json.dumps({k: metrics[k] for k in ("case_count", "domains", "direction_candidates", "candidate_tiers", "candidate_tier_share", "anchor_questions", "b2_expert_decisions", "engine_validation_failures", "seeded_error_pass")}, ensure_ascii=False, indent=1))
    print("wrote", out_path)
    print("failures:", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
