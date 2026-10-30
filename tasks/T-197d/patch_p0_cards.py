"""T-197d · 只改字段一致性/可复现性：在 T-197 产出的 META/p0-cards-v1.json 上打补丁。

不重跑 A+、不改 engine、不改候选的取舍（除 T-197d §2 明令的同源去重）、不做 git 写。
幂等：重复运行结果一致（所有赋值均为绝对值，不依赖旧值）。

用法：.venv\\Scripts\\python.exe tasks/T-197d/patch_p0_cards.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

PACK_PATH = os.path.join(ROOT, "META", "p0-cards-v1.json")

HY = "sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md"
JG = "sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md"
JB = "sources/duan/MinerU_markdown_疾病_2056043976378220544.md"
CG = "sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md"


def _card(pack, cid):
    hits = [c for c in pack["cards"] if c["card_id"] == cid]
    assert len(hits) == 1, cid
    return hits[0]


def _aq(card, qid):
    hits = [q for q in card["anchor_q"] if q["qid"] == qid]
    assert len(hits) == 1, (card["card_id"], qid)
    return hits[0]


def _cand(card, bucket, oid):
    hits = [x for x in card[bucket] if x["option_id"] == oid]
    assert len(hits) == 1, (card["card_id"], bucket, oid)
    return hits[0]


def _answer_entry(qid, layer, answer, answer_source, decision_by, source_ref, quote, note):
    return {
        "qid": qid,
        "layer": layer,
        "answer": answer,
        "answer_source": answer_source,
        "decision_by": decision_by,
        "source_ref": source_ref,
        "quote": quote,
        "note": note,
    }


def _unknown_entry(qid, layer, note):
    return _answer_entry(qid, layer, "unknown", "not_in_source", "needs_anchor", None, None, note)


def _insert_after(mapping, anchor_key, new_items):
    out = {}
    for k, v in mapping.items():
        out[k] = v
        if k == anchor_key:
            out.update(new_items)
    return out


def main() -> int:
    with open(PACK_PATH, encoding="utf-8") as fh:
        pack = json.load(fh)

    # ---------------------------------------------------------------- 顶层元数据
    pack = _insert_after(
        pack,
        "task",
        {
            "revision": {
                "rev": "r2",
                "by": "T-197d",
                "at": "2026-10-30T09:40:00+08:00",
                "scope": "只修字段一致性与可复现性：P0-04 多 A claim 不折叠、P0-03 dc3/rs1 单层登记、P0-01/02 字段与 anchored_by 指向、report 计数统一；不改候选取舍、不改 engine、不跑 P1。",
                "patch_script": "tasks/T-197d/patch_p0_cards.py",
            }
        },
    )

    pack = _insert_after(
        pack,
        "tier_scheme",
        {
            "field_semantics": {
                "layer_tier": {
                    "A": "固定关系（克/生/化/墓），engine 与原文同向；可 agent_auto。A 不表示『多个 A 候选之间可折叠为一个』。",
                    "B1": "锚点消歧：候选分歧可由『命主已发生事实』的是非题区分。",
                    "B2": "仅当没有任何可观测事实可区分候选时：专家单选或 needs_anchor，必须带 source/quote。",
                    "C": "无源、或与已冻结规则冲突 → needs_anchor，不写成断语；C 档在本包等于『不参与选择』。",
                    "not_claimed": "该层不主张档位（没有可用的锚点题），不是 A/B1/B2/C 之外的另一个证据等级。",
                },
                "layer_scope": {
                    "claimed": "该层已由 anchor_a 唯一收敛，并写入该层 selected 字段。",
                    "candidate_only": "候选存在但未唯一收敛（可能已有锚点题、尚无答案）。",
                    "not_claimed": "该层无候选或不主张（P0-04 的 rescue 层）。",
                },
                "tier_vs_scope": "tier 是证据档位，scope 是当前主张状态，两者不是同一维度：state_tier=B1 + state_scope=candidate_only 表示『有 AQ2 可收敛，但尚无答案』，不构成矛盾。",
                "not_auto_selected": "true = 卡级没有自动折叠出的单一 selected_option；不等于该卡没有任何自动结论（A claim 可以各自成立）。",
                "anchor_a": "每题一条，answer ∈ {yes,no,unknown}，answer_source ∈ {source_outcome（原文结局明载）, testimony（命主口述）, not_in_source（原文未载，故记 unknown）}。answer≠unknown 时必须带 source_ref 与 quote，且 quote 为该行逐字子串。",
                "c_tier_never_selected": "C 档本身就是 needs_anchor，不参与任何层的 selected 选择；因此 C 候选可以在无答案时『幸存』，而不会迫使 selected 非空。",
            },
            "selection_rules": {
                "selectable_tiers": ["A", "B1", "B2"],
                "excluded_tiers": ["C"],
                "unknown_default": "anchor_q 无答案时按该题 elimination 的 unknown 行处理；某层没有任何 anchor_q 时，该层全部可参与选择的候选都幸存。",
                "unique_rule": "某层仅当可参与选择的候选在 anchor_a（缺省 unknown）下恰好 1 个幸存时，才允许填该层 selected；否则该层 selected 必须为 null。",
                "selected_must_equal_survivor": "selected_option / state_selected 非空时，必须等于唯一幸存候选；state_selected 必须等于该候选的 result 字段。",
                "multi_claim_rule": "互补的多个 A claim 不折叠为单一 selected_option：卡级 selected_option=null，逐 claim 用 claim_id/claim_selected 记账，A 档按 claim 计数（不是按卡计数）。",
            },
        },
    )

    sc = pack["schema_compat"]
    sc["not_implemented"]["selected_option/selected_state/selected_rescue"] = (
        "按 selection_rules 处理：卡级 selected_option 仅在该层唯一收敛时填；"
        "P0-04 三条 A claim 互补 → selected_option=null + 逐 claim 记账（claim_id/claim_selected）；"
        "selected_state 仅在 state 锚点收敛后填（P0-04 AQ1=yes → st2 唯一 → 败）。"
    )
    sc["not_implemented"]["anchor_a 实体答案"] = (
        "T-197d 起 anchor_a 必须落盘：source-backed 答案（该题 source_mentions_answer=true）带 source_ref+quote 填入；"
        "原文未载的题记 unknown 留空待命主，不由 Agent 代答。见 field_semantics.anchor_a。"
    )
    sc["known_conflicts"] = [
        "v2 的 A 档要求单一 selected_option 已填且 pending=none；本包 A 按 claim 计（P0-04 三条 A claim），卡级 selected_option=null，"
        "以 selected_claims + claim_id 表达『多条 A 同时成立』，与 v2 的单值 selected_option 不同形。",
        "v2 的 C 档也用 selected_option=null + selection_source=needs_anchor；本包 C 候选按 selection_rules 恒不参与选择，"
        "故『待自动确认的多条 A claim』与『无源 C』用 direction_tier / selection.mode 区分，不再靠 pending 区分。",
    ]
    EXTRA_EXTENSIONS = [
        "claim_id / claim_selected / claim_scope：同一层可有多条互补 claim（A 档按 claim 计数）",
        "selected_claims / selected_options：非唯一时记全部幸存 claim，卡级 selected_option 保持 null",
        "selection{mode,unique,direction_survivors,state_survivors}：按 anchor_a 复算的幸存集，供第三方对照",
        "anchor_a[].answer_source / anchor_q[].anchor_a：答案是『原文结局明载』还是『原文未载』必须可区分",
        "state_candidates[].selectable / tier_note：C 档定义口径候选不参与成败选择",
        "dedup[]：同源关系只保留一层的登记记录（含被移除项的完整原记录）",
        "field_semantics / selection_rules：字段语义与选择规则，供 verify 与第三方按同一口径复算",
    ]
    sc["extensions"] = [x for x in sc["extensions"] if x not in EXTRA_EXTENSIONS] + EXTRA_EXTENSIONS

    # ------------------------------------------------------------------ 包级 metrics
    m = pack["metrics"]
    m["direction_candidates"] = 11
    m["direction_candidates_before_dedup"] = 12
    m["candidate_tiers"] = {"A": 3, "B1": 7, "B2": 0, "C": 1}
    m["candidate_tier_share"] = {"A": 0.2727, "B1": 0.6364, "B2": 0.0, "C": 0.0909}
    m["state_candidates"] = 10
    m["state_candidates_selectable"] = 9
    m["anchor_a_answers"] = {"unknown": 5, "yes": 1, "no": 0, "total": 6}
    m["a_claim_share"] = {
        "numerator": 3,
        "denominator": 11,
        "value": 0.2727,
        "basis": "按 claim（方向候选）计数，不按卡计数；去重前分母为 12（3/12=25.0%）",
        "note": "P0-03 的 dc3 与 rs1 同源（L141『戌坏丑』+ e010），按 §2 只保留救应一层，方向分母 12→11。",
    }
    m["a_precision"] = {
        "evaluated": 3,
        "met_tier_definition": 3,
        "value": 1.0,
        "criteria": [
            "kind ∈ {ke,sheng,muku} 且 class ∈ {克,生,化,墓}",
            "engine 边/候选与原文句法同向",
            "与其他 A claim 互补而非竞争（P0-04 dc1 墓/库收、dc2 克/破坏功神、dc3 生/财源生官）",
        ],
        "note": "A 率（3/11）与 A 精度（3/3）是两个指标：率看占比，精度看 A 档自身是否满足三条件。",
    }
    m["a_share_vs_p0_gate"] = {
        "gate": "A 档自动占比 ≥50%（T-196 卡 §1.1 P0 gate）",
        "actual": 0.2727,
        "numerator": 3,
        "denominator": 11,
        "verdict": "未达",
        "note": "按 claim 计：3 个 A claim / 11 个方向 claim = 27.3%（去重前 3/12=25.0%）。冲/合/穿/刑不得 A（中枢 2026-10-30 追加），真实婚/事业/健康/财问题的 material edge 多为对称关系或带竞争候选。",
    }
    m["self_test"] = {
        "detected": 20,
        "total": 20,
        "pass": True,
        "mode": "self_test",
        "scope": "pack 级：addr/edge/ten_god/quote 共 20 项 fixture 的 self_test（不是第三方植入错误）",
        "card_scan": {"cards": 4, "per_card": 4, "detected": 16, "total": 16, "pass": True},
        "note": "report 曾写 16/16、卡写 20/20：两者都被保留但口径不同——16/16 是逐卡 4×4 card_scan，20/20 是包级 fixture self_test。",
    }
    se = pack["seeded_error_self_test"]
    se["scope"] = "pack 级 fixture self_test：addr 5 + edge 5 + ten_god 5 + quote 5 = 20（非第三方植入错误）"
    se["card_scan"] = {"cards": 4, "per_card": 4, "detected": 16, "total": 16, "pass": True,
                       "note": "逐卡 engine_validation.seeded_error：fake_address / fake_edge / wrong_ten_god / tampered_quote 各 1"}

    # ==================================================================== P0-01
    c1 = _card(pack, "P0-01")

    # §3 e015 理由把月支 M.b 写成夫妻宫
    c1["material_edge_reasons"]["e015"] = (
        "月支寅(M.b)↔日支申(D.b)相冲：M.b 是月支（父母兄弟宫），夫妻宫/配偶宫是 D.b；"
        "e015=chong(M.b,D.b)，受方为日支配偶宫。本题直接问婚姻稳定。"
    )

    # §4(D20) outcome_note 与 L33 的转述对齐
    c1["source"]["outcome_note"] = (
        "原文后续事实：五次婚姻、配偶带子女离开、一个孩子也没落着（L33；P0 仅备查，不作预测依据）。"
    )

    # §3 AQ2 的 discriminates 覆盖被消去的 dc2
    q2 = _aq(c1, "AQ2")
    q2["discriminator_basis"] = (
        "dc3 认为主线是年支巳与夫妻宫申『合』（合而未断）；dc1 与 dc2 都落在冲（推走、断离），"
        "只是 dc1 赋单侧施力、dc2 保持对称不赋向。若分开后仍长期有联系/经济往来，则『冲而断离』的两种赋向口径都不成立，只剩合读法；"
        "若彻底断绝，合读法不成立。故 discriminates=[dc1,dc2,dc3]，与 elimination 的消去项完全一致。"
    )
    q2["discriminates"] = ["dc1", "dc2", "dc3"]

    # §3 st1/st2 不得把 direction 层的 AQ1 写成自己的锚点
    for sid in ("st1", "st2"):
        st = _cand(c1, "state_candidates", sid)
        st["anchored_by"] = []
        st["anchored_by_note"] = (
            "本卡没有 state 层锚点题：AQ1/AQ2 均为 direction 层且只区分方向候选，不区分 st1/st2；"
            "故 anchored_by 留空，不改写成 AQ1。"
        )

    # §4 report 的 5 unknown / 1 yes 落进卡 anchor_a
    c1["anchor_q"][0]["anchor_a"] = "unknown"
    c1["anchor_q"][1]["anchor_a"] = "unknown"
    c1["anchor_a"] = [
        _unknown_entry("AQ1", "direction", "原文未载（source_mentions_answer=false）；待命主回答，Agent 不代答。"),
        _unknown_entry("AQ2", "direction", "原文未载（source_mentions_answer=false）；待命主回答，Agent 不代答。"),
    ]
    c1["anchor_a_note"] = (
        "本卡 2 题均记 unknown：原文未载（AQ1/AQ2 的 source_mentions_answer=false），按 report §2 落 unknown 并交命主回答；"
        "Agent 不据原文后续事实代答（原文只写五次婚姻/孤家寡人，不是这两题的事实答案）。"
    )
    c1["state_scope"] = "candidate_only"
    c1["tier_reason"] = ["direction:anchor_conflict", "state:candidate_only", "rescue:candidate_only"]
    c1["selection"] = {
        "mode": "needs_anchor",
        "unique": False,
        "selected_option": None,
        "selected_claims": [],
        "direction_survivors": [],
        "state_survivors": ["st1", "st2"],
        "note": "anchor_a 全 unknown：AQ1 unknown 消 dc1/dc2、AQ2 unknown 消 dc1/dc2/dc3 → 方向层无幸存者；"
                "本卡无 state 锚点题，st1/st2 全部幸存（st3 为 C 档不参与选择）→ state 层不唯一。两层 selected 均 null。",
    }

    # ==================================================================== P0-02
    c2 = _card(pack, "P0-02")
    for sid in ("st1", "st2"):
        st = _cand(c2, "state_candidates", sid)
        st["anchored_by"] = []
        st["anchored_by_note"] = (
            "本卡只有 AQ1 且它是 direction 层（区分 dc1/dc2），不区分 st1/st2；故 anchored_by 留空，不改写成 AQ1。"
        )
    c2["anchor_q"][0]["anchor_a"] = "unknown"
    c2["anchor_a"] = [
        _unknown_entry("AQ1", "direction", "原文未载（source_mentions_answer=false）；窗口 2015-2025 原文未覆盖收入结构；待命主回答。"),
    ]
    c2["anchor_a_note"] = (
        "本卡 1 题记 unknown：原文未载（source_mentions_answer=false），按 report §2 落 unknown 交命主回答；"
        "Agent 不据原文履历代答收入结构。"
    )
    c2["state_scope"] = "candidate_only"
    c2["tier_reason"] = ["direction:anchor_conflict", "state:candidate_only", "rescue:candidate_only"]
    c2["selection"] = {
        "mode": "needs_anchor",
        "unique": False,
        "selected_option": None,
        "selected_claims": [],
        "direction_survivors": [],
        "state_survivors": ["st1", "st2"],
        "note": "AQ1 unknown 消 dc1/dc2；dc3 为 C 档（不参与选择）→ 方向层无幸存者。无 state 锚点题 → st1/st2 全部幸存，state 不唯一。",
    }

    # ==================================================================== P0-03
    c3 = _card(pack, "P0-03")

    # §2 dc3（戌坏丑·方向）与 rs1（戌坏丑·救应）同源：只保留救应一层
    if c3.get("dedup"):
        dedup_rec = c3["dedup"][0]
    else:
        dc3 = _cand(c3, "direction_candidates", "dc3")
        dedup_rec = {
            "removed_id": "dc3",
            "removed_layer": "direction",
            "merged_into": "rs1",
            "kept_layer": "rescue",
            "engine_edge": "e010",
            "source_ref": JB + ":L141",
            "reason": (
                "dc3（xing M.b→D.b『戌坏丑』当疾病方向）与 rs1（戌坏丑→病源被制、过关）同引 L141 同一句、同一条 e010，"
                "属同一关系的两次登记。原文的用法是『否则将过不去午运』＝救应效果，故只保留救应层 rs1，方向层不再计入 dc3，避免双计。"
            ),
            "effect": "方向候选 12→11；dc1/dc2 由 AQ1 完整覆盖，unknown 下两层均无幸存者 → selected 保持 null。",
            "original_record": dc3,
        }
    c3["direction_candidates"] = [x for x in c3["direction_candidates"] if x["option_id"] != "dc3"]
    c3["dedup"] = [dedup_rec]

    # rs1 原写 tier=B1/human_anchor，但本卡无救应锚点题 → 与 rescue_tier=not_claimed 自相矛盾
    rs1 = _cand(c3, "rescue_candidates", "rs1")
    rs1["tier"] = "C"
    rs1["decision_by"] = "needs_anchor"
    rs1["anchored_by"] = []
    rs1["anchored_by_note"] = (
        "本卡没有救应锚点题：AQ1/AQ2 分别只区分 dc1/dc2 与 st1/st2，不区分救应层；"
        "故 anchored_by 留空，不改写成 AQ1（此前写 AQ1 是错误指向）。"
    )
    rs1["basis_text"] = (
        "原文『命中因有戌坏丑，否则将过不去午运』——戌坏丑被当作能过关的原因（救应效果）。"
        "该关系原同时被登记为方向候选 dc3，T-197d 按同源去重并入本层（见 dedup[0]），此处只记救应一层。"
    )
    rs1["tier_note"] = (
        "原文确实记了『戌坏丑』为过关之因，但救应结构（rescue_primitive/rescuer/rescued）未判（G5），"
        "本卡也没有救应锚点题 → 按 C 档 needs_anchor 记录，不写成断语、不写成 B1。"
    )
    c3["rescue_tier"] = "C"

    # §2 AQ2 yes 要 eliminate 而非只 downgrade
    a2 = _aq(c3, "AQ2")
    a2["discriminator_basis"] = (
        "st2 的读法要求心脏侧确有受病记录；st1 的读法要求妇科侧为主。按原文互斥口径"
        "（同章『丑午穿→心是被伤，心慌惊悸』 vs 本造『午得寅生，旺，所以不得心脏病』），"
        "一组症状只能落在一个读法上：yes → 直接消 st1（不是降级），no → 消 st2；unknown → 两读法都无据，均不可选。"
    )
    a2["if_yes"]["eliminate"] = ["st1"]
    a2["if_yes"]["downgrade"] = []
    a2["elimination"] = [
        {"answer": "yes", "eliminates": ["st1"], "keeps": ["st2"]},
        {"answer": "no", "eliminates": ["st2"], "keeps": ["st1"]},
        {"answer": "unknown", "eliminates": ["st1", "st2"], "keeps": []},
    ]

    c3["anchor_q"][0]["anchor_a"] = "unknown"
    c3["anchor_q"][1]["anchor_a"] = "unknown"
    c3["anchor_a"] = [
        _unknown_entry("AQ1", "direction", "原文未载（source_mentions_answer=false）；待命主回答。"),
        _unknown_entry("AQ2", "state", "原文只写子宫癌/手术/中医治好，未写心脏血压症状（source_mentions_answer=false）；待命主回答。"),
    ]
    c3["anchor_a_note"] = (
        "本卡 2 题均记 unknown：原文未载（AQ1/AQ2 的 source_mentions_answer=false），按 report §2 落 unknown 交命主回答；"
        "Agent 不据原文结局代答（原文写的是最后治好，不是这两题的事实答案）。"
    )
    c3["state_scope"] = "candidate_only"
    c3["tier_reason"] = ["direction:anchor_conflict", "state:candidate_only", "rescue:candidate_only"]
    c3["selection"] = {
        "mode": "needs_anchor",
        "unique": False,
        "selected_option": None,
        "selected_claims": [],
        "direction_survivors": [],
        "state_survivors": [],
        "note": "dc3 已按同源去重并入 rs1（方向候选 2 条）；AQ1 unknown 消 dc1/dc2 → 方向层无幸存者。"
                "AQ2 unknown 消 st1/st2 → state 层无幸存者。两层 selected 均 null。",
    }

    # ==================================================================== P0-04
    c4 = _card(pack, "P0-04")

    # §1 三个 A 候选全存活：拆 claim，不折叠成单一 selected_option
    for oid, claim_id in (("dc1", "CLM-C4-01"), ("dc2", "CLM-C4-02"), ("dc3", "CLM-C4-03")):
        x = _cand(c4, "direction_candidates", oid)
        x["claim_id"] = claim_id
        x["claim_selected"] = True
        x["claim_scope"] = "complementary"
        x["claim_note"] = {
            "dc1": "墓用：辰库收丑官（库收）——回答『财在哪里/官当财看』。",
            "dc2": "克：辛克乙破坏功神辰——回答『为何守不住』。",
            "dc3": "生：年支巳生月支丑，财生官——回答『财从哪来』。",
        }[oid]

    c4["selected_option"] = None
    c4["selected_options"] = ["dc1", "dc2", "dc3"]
    c4["selected_claims"] = ["dc1", "dc2", "dc3"]
    c4["selection_source"] = "engine_fixed_multi"
    c4["not_auto_selected"] = True
    c4["decision_by"] = "anchor_fact"
    c4["decision_by_layer"] = {
        "direction": "engine_fixed_multi",
        "state": "anchor_fact",
        "rescue": "needs_anchor",
    }
    c4["selection"] = {
        "mode": "multi_claim",
        "unique": False,
        "selected_option": None,
        "selected_claims": ["dc1", "dc2", "dc3"],
        "direction_survivors": ["dc1", "dc2", "dc3"],
        "state_survivors": ["st2"],
        "state_survivor_result": "败",
        "note": "方向层无锚点题，三条 A claim 全存活且互补（库收/克坏/财源），不是三选一 → 卡级 selected_option=null，"
                "按 claim 记账（A 3/11）。state 层 AQ1=yes 消 st1，仅 st2 幸存 → state_selected=败（=st2.result）。",
    }

    # §1 AQ1 的 source-backed 答案落进 anchor_a
    c4["anchor_q"][0]["anchor_a"] = "yes"
    c4["anchor_q"][0]["fact_window_note"] = (
        "fact_window 约束的是『若改问命主』的自述范围；本卡该题答案是 source_outcome（原文 L398 结局），"
        "原文事件早于窗口下界，故不以窗口过滤原文答案，也不据窗口反推年份。"
    )
    c4["anchor_a"] = [
        _answer_entry(
            "AQ1",
            "state",
            "yes",
            "source_outcome",
            "source_fact",
            CG + ":L398",
            "癸未年刚入乙运坐牢，因非法集资而没收产财。判刑十年。现已出狱。",
            "题目问『资产是否被一次性清空（罚没/没收/强制清算/巨额赔付）』；原文 L398 明载因非法集资没收财产（该题 source_mentions_answer=true），"
            "按原文结局记 yes 并带逐字引文。这是 source-backed 锚点，不是 Agent 代答。",
        )
    ]
    c4["anchor_a_note"] = (
        "本卡唯一答案 AQ1=yes 取自原文结局（L398 明载没收财产，该题 source_mentions_answer=true），带 source_ref+quote 落盘；"
        "原文未载的题才留空交命主。原『留空、不据原文代答』的写法已废止，改为『有源才填、无源记 unknown』，与 state_note 不再冲突。"
    )

    # §1 st1/st2 的 anchored_by 指向实际区分它们的 state 题 AQ1
    for sid in ("st1", "st2"):
        st = _cand(c4, "state_candidates", sid)
        st["anchored_by"] = ["AQ1"]
        st["anchored_by_note"] = "AQ1 是 state 层题（discriminates=[st1,st2]）：yes 消 st1、no 消 st2。"

    st3 = _cand(c4, "state_candidates", "st3")
    st3["selectable"] = False
    st3["tier_note"] = (
        "『财弱官旺、官当财看』是财的定义口径（state=null、result=needs_anchor、tier=C），不是成败状态；"
        "按 selection_rules 的 C 档永不参与选择，故不影响 st1/st2 的唯一性判定。"
    )

    c4["state_anchor_note"] = {
        "converted_from": None,
        "resolved_by": "AQ1",
        "reason": (
            "T-197 曾把『原局富/岁运破』设为 B2 专家单选（ED1）。按 analysis-card-v2 §5.3，B2 只用于方向候选之间『无可观测事实可分』；"
            "原文 L396-L398 已写结局，故改为 state 锚点题并登记为 AQ1（source_mentions_answer=true）。"
            "ED1 不再存在，st1/st2 的 anchored_by 改为 AQ1（此前写 ED1 是悬空引用），expert_decision 保持 null。"
        ),
        "previous_options": [
            "原局富命为主，破局只作应期（先富后破）",
            "岁运破局为主，原局富命只说明曾经（破多富少）",
            "两不可判，保持 needs_anchor",
        ],
    }

    c4["state_scope"] = "claimed"
    c4["pending"] = None
    c4["tier_reason"] = ["direction:engine_fixed_multi", "state:anchor_fact", "rescue:candidate_only"]
    c4["non_claims"] = [
        "不判财运高低、破财年份、牢狱应期",
        "不把『富命』(st1) 作为并列结论：AQ1=yes 已消 st1，state 层取 st2 破局；st1 的原文依据仍保留在 state_candidates 内备查",
        "不判岁运引动；不跨快照引用 edge_id",
        "方向层三条 A claim 互补（库收/克坏/财源），不折叠成单一方向结论",
    ]

    # ------------------------------------------------------------------ 顶层 anchor_questions 镜像
    answer_by_key = {}
    for c in pack["cards"]:
        for e in c["anchor_a"]:
            answer_by_key[(c["card_id"], e["qid"])] = e
    for q in pack["anchor_questions"]:
        e = answer_by_key[(q["card_id"], q["qid"])]
        q["answer"] = e["answer"]
        q["answer_source"] = e["answer_source"]
        q["answer_source_ref"] = e["source_ref"]
        q["answer_quote"] = e["quote"]

    pack["known_gaps"] = [
        "T-196 三份规格在本卡生成途中落盘（analysis-card-v2 / agent-candidate-generator-v1 / first-principle-agent-first-v1）；本包按 agent-candidate-set/v1 改名与补字段，仍是 candidate set，不是成品 analysis-card/v2。",
        "与 v2 的两处口径冲突见 schema_compat.known_conflicts：A 档按 claim 计（非单一 selected_option）；C 档与『多条 A claim 未折叠』用 direction_tier / selection.mode 区分。",
        "四柱输入无出生时刻：engine input_limitations 明确不起运/不给大运公历年份；本包全部 dayun_index=null、liunian_year=null。",
        "G5 救应未判：engine.structures 的 rescuer 命中只作要件，不作救应结论；P0-03 的 rs1 因此记 C/needs_anchor。",
        "『寅申之冲，寅多作用一次』的『作用一次』是计数用语，本卡按 same_page 缺口记为方向依据，是否够格由中枢裁。",
        "P0-04 的原局富/岁运破属成败层，按 analysis-card-v2 §5.3 不适用方向层 B2；已改为 state 锚点题 AQ1，并已由原文 L398 落 yes（source_mentions_answer=true），expert_decision 保持 null、B2 = 0。",
        "P0-03 的 dc3（戌坏丑当疾病方向）与 rs1 同源，按 T-197d §2 只保留救应一层；被移除项的完整记录见 cards[P0-03].dedup[0].original_record。",
    ]

    with open(PACK_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(pack, ensure_ascii=False, indent=2))
    print("patched", PACK_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
