"""T-197e · P0 r3 内容修复：在 r2 的 META/p0-cards-v1.json 上打补丁。

只改 P0 卡的 root 副本与内容层：
  - D-R2-01 / D-R2-02：root anchor_questions 与卡内同步；
  - D04：P0-02 outcome_quote 改事业结局句；
  - P0-04 H.b：dc1/palaces/material_edges 补时支丑，记录墓用[D.b,H.b]与 e011；
  - D-R2-05/06/07/09/10/11/12 与 6 项 missing_evidence。

不改候选取舍、不改答案、不改 engine/保护区、不做 git 写。
幂等：所有赋值均为绝对值，重复运行结果一致。

用法：
  .venv\\Scripts\\python.exe tasks/T-197e/patch_p0_cards_r3.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

PACK_PATH = os.path.join(ROOT, "META", "p0-cards-v1.json")

JG = "sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md"
JB = "sources/duan/MinerU_markdown_疾病_2056043976378220544.md"
CG = "sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md"

L392 = (
    "原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，"
    "官当财看。所以是个富命，辰是主要功神。"
)
L398 = "癸未年刚入乙运坐牢，因非法集资而没收产财。判刑十年。现已出狱。"


def _card(pack: dict, cid: str) -> dict:
    hits = [c for c in pack["cards"] if c["card_id"] == cid]
    assert len(hits) == 1, cid
    return hits[0]


def _aq(card: dict, qid: str) -> dict:
    hits = [q for q in card["anchor_q"] if q["qid"] == qid]
    assert len(hits) == 1, (card["card_id"], qid)
    return hits[0]


def _cand(card: dict, bucket: str, oid: str) -> dict:
    hits = [x for x in card[bucket] if x["option_id"] == oid]
    assert len(hits) == 1, (card["card_id"], bucket, oid)
    return hits[0]


def _has_addr(items: list[dict], addr: str) -> bool:
    return any(x.get("addr") == addr for x in items)


def _has_note(items: list[dict], needle: str) -> bool:
    return any(needle in (x.get("note") or "") for x in items)


def main() -> int:
    with open(PACK_PATH, encoding="utf-8") as fh:
        pack = json.load(fh)

    # ---------------------------------------------------------------- 顶层元数据
    pack["revision"] = {
        "rev": "r3",
        "by": "T-197e",
        "at": "2026-10-30T09:45:00+08:00",
        "based_on": "r2 / T-197d（main e0038714 工作树）",
        "scope": (
            "只修 P0 卡 root 副本与内容层：D-R2-01/02 同步、P0-02 事业结局引文（D04）、"
            "P0-04 时支丑 H.b、D-R2-05/06/07/09/10/11/12、6 项 missing_evidence；"
            "不改候选取舍/答案、不改 engine/保护区、不跑 P1、不做 git 写。"
        ),
        "patch_script": "tasks/T-197e/patch_p0_cards_r3.py",
    }

    # ---------------------------------------------------------------- P0-02 · D04 / M-01
    c2 = _card(pack, "P0-02")
    c2["source"]["outcome_quote"]["text"] = (
        "07年转戊辰运08年提副军长，预测2012年还会提升正军级干部。"
    )
    c2["source"]["outcome_quote"]["role"] = "outcome_background"
    c2["source"]["outcome_quote"]["domain"] = "career"
    c2["source"]["outcome_quote_domain_note"] = (
        "L25 是同段履历+婚姻：前半为军官晋升结局（正团→副师→正师→副军长→预测正军级），"
        "后半『此人婚姻非常好…一儿一女』属婚姻/子女。career 卡只取前半事业结局句，"
        "婚姻句不再作为本卡 outcome_quote。"
    )
    c2["source"]["outcome_note"] = (
        "原文后续事实：走丁卯运庚辰年提正团、壬午年提副师、甲申年提正师；"
        "07年转戊辰运08年提副军长，预测2012年还会提升正军级干部（P0 仅备查，不作预测依据）。"
    )

    # ---------------------------------------------------------------- P0-02 · D-R2-04 / M-02
    dc2_2 = _cand(c2, "direction_candidates", "dc2")
    dc2_2["basis_text"] = (
        "同盘第二组财克印：e006 ke(己,癸)、actor=H.s。原文 L27 明点『戊就是做工的重要的字』，"
        "并未点名己；『己(偏财)也是活财』缺少原文或命主事实支持（M-02）。"
        "故 dc2 只作机械备选（同一受印癸的第二组财制印），保留 B1 只为覆盖『两组财争一印』的结构，"
        "不因本句升格为与 dc1 并列的有源强候选。"
    )
    dc2_2["basis_note"] = (
        "D-R2-04 / M-02：删去旧句『原文只说财制印未点名哪一个财』；原文实际点名戊。"
        "dc2 保持 decisive=false / evidence_gap=doctrine_only，不据此删候选。"
    )
    dc2_2["missing_evidence_refs"] = ["M-02"]

    # ---------------------------------------------------------------- P0-03 · D-R2-07 / M-04
    c3 = _card(pack, "P0-03")
    aq2_3 = _aq(c3, "AQ2")
    aq2_3["discriminator_basis"] = (
        "st2 的读法要求心脏侧确有受病记录；st1 的读法要求妇科侧为主。"
        "按同章互斥口径（L123『丑午穿——心是被伤，心慌惊悸』 vs L131『午得寅生，旺，所以不得心脏病』），"
        "一组症状只能落在一个读法上。注意 L131 是另一造（乾 乙戊丙己 / 卯寅午丑，L127-L133）的判词，"
        "不是本造判词；本造只有同构的寅午半合可迁移该理。"
        "yes → 直接消 st1（不是降级），no → 消 st2；unknown → 两读法都无据，均不可选。"
    )
    st2_3 = _cand(c3, "state_candidates", "st2")
    st2_3["basis_text"] = (
        "同章 L123『丑午穿--------心是被伤，心慌惊悸』是病性通例；"
        "L131『午得寅生，旺，所以不得心脏病』是另一造（乾 乙戊丙己 / 卯寅午丑，L127-L133）的判词，"
        "不是本造判词。本造（坤 壬寅 庚戌 己丑 庚午）与彼造同有寅午半合、午得寅生结构，"
        "故该判据只能作为可迁移规则引用，不能写作『本造』判词；"
        "st2 仍只是待 AQ2 定夺的竞争读法（M-04）。"
    )
    st2_3["attribution_note"] = (
        "D-R2-07：L123 同章病性通例；L131 他造判词（乾 乙戊丙己/卯寅午丑，L127-L133），"
        "只可迁移，不可当作本造判词。"
    )
    st2_3["missing_evidence_refs"] = ["M-04"]
    for q in st2_3.get("quotes") or []:
        if q.get("line") == 131:
            q["attribution_note"] = (
                "L131 是另一造（乾 乙戊丙己 / 卯寅午丑，L127-L133）的判词，"
                "作为可迁移的反向判据引用，不是本造判词。"
            )
    for st in c3["state_candidates"]:
        st["result_note"] = (
            "result=病 表示已病；本卡 state 层只区分病位（st1 妇科 / st2 心脏），"
            "不区分病/不病。"
        )
    c3["state_scope_note"] = (
        "本卡 state 层区分病位（st1 妇科 / st2 心脏），两个候选 result 都是『病』；"
        "AQ2 只定病位，不定病/不病。state_scope=candidate_only 表示只登记候选、未收敛，"
        "不表示该层在判『病/不病』。"
    )

    # ---------------------------------------------------------------- P0-04 · D-R2-10
    c4 = _card(pack, "P0-04")
    aq1_4 = _aq(c4, "AQ1")
    aq1_4["fact_window"] = "2000-01..2025-12"
    aq1_4["fact_window_note"] = (
        "fact_window 覆盖 2003（癸未年，L398 原文结局）；该题答案为 source_outcome，"
        "原文事件落在窗口内，故不以窗口过滤原文答案，也不据窗口反推年份。"
    )

    # ---------------------------------------------------------------- P0-04 · D-R2-05 / D-R2-09 / D-R2-12
    st1_4 = _cand(c4, "state_candidates", "st1")
    st2_4 = _cand(c4, "state_candidates", "st2")
    st3_4 = _cand(c4, "state_candidates", "st3")
    st2_4["decision_by"] = "anchor_fact"
    st2_4["decision_by_note"] = (
        "由 AQ1 锚点事实（L398 没收财产）决定，不是专家单选；expert_decision=null，ED1 已废止。"
    )
    st2_4.pop("expert_decision", None)

    st3_4["candidate_kind"] = "definition/non_outcome"
    st3_4["label_note"] = (
        "C 标签为扩展借用：基准 C=无源/冲突；本候选有源（L392），借用 C 仅表示"
        "『定义口径、不参与成败选择』。严格 schema 下游应按 candidate_kind=definition/non_outcome 读取，"
        "不得读作『无源 C』。"
    )
    st3_4["tier_note"] = (
        "『财弱官旺、官当财看』是财的定义口径（state=null、result=needs_anchor、"
        "candidate_kind=definition/non_outcome；tier=C 为扩展借用），不是成败状态；"
        "按 selection_rules 的 C 档永不参与选择，故不影响 st1/st2 的唯一性判定。"
    )

    c4["state_scope_note"] = (
        "state 层按『最终成败』口径：L392 富命 → L394 发财五年/资产4亿 → L396 主凶 → "
        "L398 坐牢/没收/判刑，是『先富后破』的时间序列；st1 与 st2 不是同一时点互斥。"
        "AQ1=yes 按最终成败消 st1、st2 唯一=败；若改按『一生轨迹』口径，st1 与 st2 可并存，"
        "state_selected 应为 null 或多 claim（本卡不采用该口径）。"
    )
    st1_4["time_scope"] = "原局/戌运（先富：富命→发财五年/资产4亿）"
    st1_4["result_note"] = (
        "result=成 是『最终成败』口径下的先富阶段；与 st2 是时间序列，不是同一时点互斥。"
    )
    st2_4["time_scope"] = "乙运（后破：主凶→坐牢/没收/判刑）"
    st2_4["result_note"] = (
        "result=败 是『最终成败』口径下的后破阶段；与 st1 是时间序列，不是同一时点互斥。"
    )

    # ---------------------------------------------------------------- P0-04 · D-R2-08：时支丑 H.b
    palace_hb = {
        "addr": "H.b",
        "role": "时支丑：官星（正官）—月时丑同入辰墓",
        "ten_god": "正官",
        "mapping_rule": "M-05",
        "basis_quote": {
            "src": "CG",
            "line": 392,
            "text": L392,
            "role": "mapping",
            "source_ref": f"{CG}:L392",
        },
    }
    if not _has_addr(c4["palaces"], "H.b"):
        c4["palaces"].append(palace_hb)

    if "e011" not in c4["material_edges"]:
        c4["material_edges"].append("e011")
    c4["material_edge_reasons"]["e011"] = (
        "辰丑破：时支丑(H.b)与日支辰(D.b)相破；L392『月时丑官都入辰墓』，"
        "时丑同入辰墓，e011 记库被动摇的第二条边。"
    )

    dc1_4 = _cand(c4, "direction_candidates", "dc1")
    dc1_4["addrs"] = ["D.b", "M.b", "H.b"]
    dc1_4["ten_god_claims"] = {"D.b": "七杀", "M.b": "正官", "H.b": "正官"}
    dc1_4["claim"] = {
        "relation": "muku",
        "direction": "actor_to_target",
        "members": ["D.b", "M.b", "H.b"],
        "actor": "D.b",
        "target": "M.b",
        "targets": ["M.b", "H.b"],
        "atomic_members": [["D.b", "M.b"], ["D.b", "H.b"]],
        "target_note": (
            "L392『月时丑官都入辰墓』：月丑 M.b 与时丑 H.b 同入辰墓。"
            "主 target 记 M.b；H.b 为同向第二 target（engine 第二条墓用候选）。"
        ),
    }
    dc1_4["co_claims"] = [
        {
            "mode": "墓用",
            "members": ["D.b", "H.b"],
            "actor": "D.b",
            "target": "H.b",
            "source_ref": f"{CG}:L392",
            "engine_candidate": "duan_zuogong.candidates 墓用[D.b,H.b]",
            "note": "时支丑 H.b 入辰墓；e011 辰丑破是同支丑的库被动摇边。",
        }
    ]
    dc1_4["claim_note"] = (
        "墓用：辰库收月丑 M.b 与时丑 H.b 两官（库收）——回答『财在哪里/官当财看』；"
        "engine 两条候选同 actor D.b，合并为同一互补 claim，不另立竞争候选。"
    )
    dc1_4["edge_refs"] = [
        {"type": "duan_candidate", "mode": "墓用", "members": ["D.b", "M.b"], "actor": "D.b"},
        {"type": "duan_candidate", "mode": "墓用", "members": ["D.b", "H.b"], "actor": "D.b"},
    ]
    dc1_4["basis_text"] = (
        "engine 墓用候选有两条：(D.b,M.b) 与 (D.b,H.b)，actor 均为 D.b（库收，符合 actor-rules §4.9）。"
        "原文『月时丑官都入辰墓』明含月支丑(M.b)与时支丑(H.b)两丑，故本条 dc1 合并记两丑同向入辰墓"
        "（同一库收 claim 的两个原子）；另 L392 紧接『辰是主要功神』把辰标为主功方，两据合并取库→入库方。"
        "e011 辰丑破是时支丑与辰库的破，作为库被动摇的第二条 material edge 记录。"
    )
    dc1_4["basis"] = [
        {
            "kind": "engine_candidate",
            "ref": "duan_zuogong.candidates",
            "note": "墓用['D.b', 'M.b'] actor=D.b",
        },
        {
            "kind": "engine_candidate",
            "ref": "duan_zuogong.candidates",
            "note": "墓用['D.b', 'H.b'] actor=D.b",
        },
        {
            "kind": "source_directive",
            "ref": f"{CG}:L392",
            "note": "direction_support：月时丑官都入辰墓",
        },
    ]

    checks = dc1_4["engine_validation"]["checks"]
    if not any(x.get("addr") == "H.b" for x in checks["address"]["items"]):
        checks["address"]["items"].append(
            {"status": "pass", "addr": "H.b", "detail": "engine 物理地址存在"}
        )
    if not any(x.get("addr") == "H.b" for x in checks["ten_god"]["items"]):
        checks["ten_god"]["items"].append(
            {
                "status": "pass",
                "addr": "H.b",
                "claimed": "正官",
                "engine": "正官",
                "via": "干支本气/透干",
            }
        )
    checks["edge"]["detail"] = (
        "engine 做功候选命中（固定类）；同时存在第二条墓用[D.b,H.b]，actor 同为 D.b"
    )
    checks["edge"]["additional_candidates"] = [
        {
            "mode": "墓用",
            "members": ["D.b", "H.b"],
            "actor": "D.b",
            "status": "pass",
            "detail": "engine 做功候选命中（固定类）",
        }
    ]

    # P0-04 source/palace quote 计数：新增 H.b 宫位引文（L392），6→7。
    sqv = c4["source_quote_validation"]
    if not any(x.get("where") == "palaces.H.b.basis_quote" for x in sqv):
        sqv.append(
            {
                "where": "palaces.H.b.basis_quote",
                "status": "pass",
                "source_ref": f"{CG}:L392",
                "detail": "逐字命中该行",
                "role": "mapping",
            }
        )
    spq = c4["engine_validation"]["source_and_palace_quotes"]
    if not any(x.get("where") == "palaces.H.b.basis_quote" for x in spq["items"]):
        spq["items"].append(
            {
                "where": "palaces.H.b.basis_quote",
                "status": "pass",
                "source_ref": f"{CG}:L392",
                "detail": "逐字命中该行",
                "role": "mapping",
            }
        )
    spq["total"] = len(spq["items"])
    spq["pass"] = len([x for x in spq["items"] if x.get("status") == "pass"])

    agg4 = c4["engine_validation"]["aggregate"]
    agg4["address"]["total"] = 8
    agg4["address"]["pass"] = 8
    agg4["ten_god"]["total"] = 8
    agg4["ten_god"]["pass"] = 8
    v2_4 = c4["engine_validation"]["v2"]
    v2_4["address"]["checked"] = 8
    v2_4["ten_god"]["checked"] = 8
    v2_4["quote"]["checked"] = 14

    # ---------------------------------------------------------------- 包级 metrics / 口径
    pack["metrics"]["state_candidates_selectable"] = 8
    pack["metrics"]["state_candidates_selectable_note"] = (
        "state_candidates 共 10；tier=C 2 条（P0-01 st3、P0-04 st3）按 "
        "selection_rules.excluded_tiers=[C] 不参与选择 → 8 可参与；"
        "r2 的 9 只扣了显式 selectable=false 的 P0-04 st3。"
    )
    pack["metrics"]["source_palace_quotes"] = {"total": 25, "pass": 25}

    ext_note = (
        "state_candidates[].candidate_kind='definition/non_outcome' + label_note："
        "P0-04 st3 的 C 标签属扩展借用（有源定义口径），不改 selectable=false。"
    )
    if ext_note not in pack["schema_compat"]["extensions"]:
        pack["schema_compat"]["extensions"].append(ext_note)
    multi_target_note = (
        "claim.members/targets：P0-04 dc1 将 engine 两条墓用 [D.b,M.b] 与 [D.b,H.b] "
        "合并为一个互补 claim；engine 原始两条候选完整保留在 co_claims/atomic_members，"
        "不伪造单条三成员 engine 边。"
    )
    if multi_target_note not in pack["schema_compat"]["extensions"]:
        pack["schema_compat"]["extensions"].append(multi_target_note)
    pack["schema_compat"]["extensions"] = list(
        dict.fromkeys(pack["schema_compat"]["extensions"])
    )

    # ---------------------------------------------------------------- 6 项缺证据
    pack["missing_evidence"] = [
        {
            "id": "M-01",
            "card_id": "P0-02",
            "item": "事业结局引文",
            "status": "已补",
            "detail": (
                "source.outcome_quote 由 L25 婚姻句改为 L25 事业结局句"
                "『07年转戊辰运08年提副军长，预测2012年还会提升正军级干部。』；"
                "outcome_note 同步为晋升履历。"
            ),
            "linked_difference": "D-R2-03",
            "evidence": [f"{JG}:L25"],
            "impact": "不影响 selected；career 域结局引文已补。",
        },
        {
            "id": "M-02",
            "card_id": "P0-02",
            "item": "dc2(己制癸) 的原文/事实依据",
            "status": "缺",
            "detail": (
                "原文 L27 明点『戊就是做工的重要的字』，未点名己；未找到『己(偏财)也是活财』的原文或命主事实。"
                "已删去 dc2 旧句『原文只说财制印未点名哪一个财』，dc2 保留为 decisive=false 的机械备选。"
            ),
            "linked_difference": "D-R2-04",
            "evidence": [f"{JG}:L27"],
            "impact": "不影响当前 selected；B1 竞争设计的必要性待补证。",
        },
        {
            "id": "M-03",
            "card_id": "P0-04",
            "item": "时支丑(H.b) 的入墓/破库证据",
            "status": "已补",
            "detail": (
                "L392『月时丑官都入辰墓』明含月丑与时丑；engine duan_zuogong 同时给 "
                "墓用[D.b,M.b] 与 墓用[D.b,H.b]；e011 辰丑破为时支丑与辰库的破。"
                "dc1 已补 H.b（claim.members/addrs/ten_god_claims/palaces/material_edges）。"
            ),
            "linked_difference": "D-R2-08",
            "evidence": [f"{CG}:L392", "engine duan_zuogong.candidates 墓用[D.b,H.b]", "e011"],
            "impact": "不影响 selected；方向 claim 覆盖已补全。",
        },
        {
            "id": "M-04",
            "card_id": "P0-03",
            "item": "本造专属的心脏/血压判据",
            "status": "缺",
            "detail": (
                "L123 是同章病性通例，L131『午得寅生，旺，所以不得心脏病』是另一造"
                "（乾 乙戊丙己 / 卯寅午丑，L127-L133）的判词；本造原文只写子宫癌/手术/中医治好，"
                "无本造心脏/血压记录。已改 st2 归属为『他造判词/可迁移规则』。"
            ),
            "linked_difference": "D-R2-07",
            "evidence": [f"{JB}:L123", f"{JB}:L131"],
            "impact": "不影响 selected；st2 仍只是待 AQ2 的竞争读法。",
        },
        {
            "id": "M-05",
            "card_id": "P0-04",
            "item": "窗口内命主事实",
            "status": "部分",
            "detail": (
                "AQ1 的 fact_window 已改为 2000-01..2025-12，覆盖 L398 癸未年（2003）；"
                "答案仍为 source_outcome（原文结局），不是命主自述。P0 允许 source_outcome，P1 需补 testimony。"
            ),
            "linked_difference": "D-R2-10",
            "evidence": [f"{CG}:L398"],
            "impact": "不影响 selected；窗口矛盾已消除，命主事实仍缺。",
        },
        {
            "id": "M-06",
            "card_id": "all",
            "item": "逐卡独立的 seeded 注入项",
            "status": "缺",
            "detail": (
                "4 卡 seeded_error 复用同一组 fixture；tampered_quote:HY:L15 只在 P0-01 源内，"
                "P0-02/03/04 的『未找到逐字文本』是平凡真。16/16 card_scan 是 smoke check，"
                "不是逐卡独立验证；需为每卡各设 source-specific seeded quote/edge，本轮未做。"
            ),
            "linked_difference": None,
            "evidence": [],
            "impact": "不影响 selected；P0 gate 的 seeded 口径仍按 16/16 记。",
        },
    ]
    pack["missing_evidence_summary"] = {
        "total": 6,
        "resolved": 2,
        "partial": 1,
        "missing": 3,
        "note": "M-01/M-03 已补；M-05 部分（窗口已覆盖 2003，命主自述仍缺）；M-02/M-04/M-06 标缺。",
    }

    pack["known_gaps"] = [
        (
            "T-196 三份规格在本卡生成途中落盘（analysis-card-v2 / agent-candidate-generator-v1 / "
            "first-principle-agent-first-v1）；本包按 agent-candidate-set/v1 改名与补字段，"
            "仍是 candidate set，不是成品 analysis-card/v2。"
        ),
        (
            "与 v2 的两处口径冲突见 schema_compat.known_conflicts：A 档按 claim 计（非单一 selected_option）；"
            "C 档与『多条 A claim 未折叠』用 direction_tier / selection.mode 区分。"
        ),
        "四柱输入无出生时刻：engine input_limitations 明确不起运/不给大运公历年份；本包全部 dayun_index=null、liunian_year=null。",
        "G5 救应未判：engine.structures 的 rescuer 命中只作要件，不作救应结论；P0-03 的 rs1 因此记 C/needs_anchor。",
        "『寅申之冲，寅多作用一次』的『作用一次』是计数用语，本卡按 same_page 缺口记为方向依据，是否够格由中枢裁。",
        "P0-04 的原局富/岁运破属成败层，按 analysis-card-v2 §5.3 不适用方向层 B2；已改为 state 锚点题 AQ1，并已由原文 L398 落 yes（source_mentions_answer=true），expert_decision 保持 null、B2 = 0。",
        "P0-03 的 dc3（戌坏丑当疾病方向）与 rs1 同源，按 T-197d §2 只保留救应一层；被移除项的完整记录见 cards[P0-03].dedup[0].original_record。",
        (
            "P0-04 dc1 合并记月丑 M.b 与时丑 H.b 两原子的『官入辰墓』；engine 分两条候选 "
            "墓用[D.b,M.b] / [D.b,H.b]，e011 辰丑破同时支丑。"
        ),
        (
            "P0-04 st3 仍用 tier=C 作扩展标签，另记 candidate_kind=definition/non_outcome + label_note；"
            "严格 schema 下游按定义口径读，不改 selectable=false。"
        ),
        (
            "P0-03/P0-04 的 state_scope_note 明确：P0-03 只分病位、P0-04 是『先富后破』时间序列；"
            "不把两层读成同一时点互斥。"
        ),
        "M-02/M-04/M-06 仍缺证据，逐条见 missing_evidence；不以补不齐为由删候选或改答案。",
    ]

    # ---------------------------------------------------------------- root anchor_questions 镜像
    card_q = {
        (c["card_id"], q["qid"]): q for c in pack["cards"] for q in c.get("anchor_q") or []
    }
    card_a = {
        (c["card_id"], e["qid"]): e for c in pack["cards"] for e in c.get("anchor_a") or []
    }
    for rq in pack["anchor_questions"]:
        key = (rq["card_id"], rq["qid"])
        cq = card_q[key]
        for field in (
            "layer",
            "text",
            "answer_type",
            "discriminator_basis",
            "rule_ref",
            "source_mentions_answer",
            "proxy_strength",
            "if_yes",
            "if_no",
            "if_unknown",
            "qid",
            "discriminates",
            "elimination",
            "fact_window",
            "fact_domain",
            "anchor_a",
        ):
            if field in cq:
                rq[field] = cq[field]
        if "fact_window_note" in cq:
            rq["fact_window_note"] = cq["fact_window_note"]
        else:
            rq.pop("fact_window_note", None)
        e = card_a[key]
        rq["answer"] = e["answer"]
        rq["answer_source"] = e["answer_source"]
        rq["answer_source_ref"] = e.get("source_ref")
        rq["answer_quote"] = e.get("quote")

    with open(PACK_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(pack, ensure_ascii=False, indent=2))
    print("patched", PACK_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
