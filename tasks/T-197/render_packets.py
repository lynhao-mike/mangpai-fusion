"""T-197 · render META/p0-case-packets-v1.md from META/p0-cards-v1.json.

Read-only over the JSON; no answer files, no engine calls.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

with open(os.path.join(ROOT, "META", "p0-cards-v1.json"), encoding="utf-8") as fh:
    PACK = json.load(fh)

L = []
A = L.append

DOMAIN_CN = {"marriage": "婚", "career": "事业", "health": "健康", "wealth": "财"}
KIND_CN = {
    "chong": "冲",
    "liuhe": "六合",
    "wuhe": "五合",
    "zhi_anhe": "暗合",
    "chuan": "穿",
    "xing": "刑",
    "po": "破",
    "ke": "克",
    "sheng": "生",
    "muku": "墓",
}
DIR_CN = {"actor_target": "actor→target", "mutual": "mutual（对称，不赋向）", "needs_anchor": "needs_anchor（方向未定）"}
GAP_CN = {
    "same_line": "same_line（同句）",
    "same_page": "same_page（同段/邻行，未同句）",
    "doctrine_only": "doctrine_only（只有定义/通用句）",
    "gap": "gap（无定向线索）",
}


A("# P0 案例包 v1（T-197）· 4 例 · A / B1 / B2 / C")
A("")
A(f"- 生成：`{PACK['generated_at']}`；任务：`{PACK['task']}`；JSON：`META/p0-cards-v1.json`")
A("- 用途：给中枢/人类看的**证据包**。每例一页：盘面事实 → 原文锚点 → 方向候选 → 状态/救应候选 → 锚点题 → 引擎校验 → 缺口。")
A("- **本包不做选定**：`selected_option=null`、`anchor_a=[]`、`pending=anchor_q`。人只答**已发生事实**的是非题，不替 Agent 选方向。")
A("")
A("## 0. 一句话")
A("")
A("4 例真实盘（婚/事业/健康/财各 1），每例 3 个方向候选、1–2 个锚点事实题；全部候选过 engine 地址/边/十神/引文校验"
  "（含 20 个植入错误 fixture 全部被拦）。方向候选 12 条：A 3（固定克/生/化/墓）、B1 8、C 1；B2 触发 0，"
  "6 个待答单元（6 个事实题）全部留空。")
A("")
A("## 1. 读取边界（自证）")
A("")
A(f"- 读答案：**{'是' if PACK['isolation']['read_answers'] else '否'}**；读 restricted：**{'是' if PACK['isolation']['read_restricted'] else '否'}**；git 写：无；engine/保护区：未改；评分器：未跑。")
A("- 盲卷只取四柱查重：" + "、".join(f"`{k}` {v}" for k, v in PACK["isolation"]["exclusion_check"]["excluded_sets"].items())
  + f"，归一化后 {PACK['isolation']['exclusion_check']['unique_pillar_sets']} 个四柱集合，与本包 4 盘重叠 **{PACK['isolation']['exclusion_check']['overlap']}**。")
A("- 理论引文不经过检索器摘要，直接回 `sources/` 原文逐字核对（每条 quote 带 `path:Ln`，构建时做子串校验）。")
A("")
A("## 2. 档位口径（中枢 2026-10-30 追加后）")
A("")
A("| 档 | 含义 | 本包处置 |")
A("|---|---|---|")
A("| **A** | 只许固定**克/生/化/墓**；engine 固定规则与原文同向、无竞争候选 | `agent_auto`，无需人 |")
A("| **B1** | 锚点消歧（默认）：候选分歧可由「命主已发生事实」的是非题区分 | 只问事实，不问「你选哪个」 |")
A("| **B2** | 没有任何可观测事实可区分时：专家单选 / 转 needs_anchor，必须带 source+quote | 本包 0 项（见 §3 说明） |")
A("| **C** | 无源（原文未给该方向）或与已冻结规则冲突 | `needs_anchor`，不写断语 |")
A("")
A("> 冲/合/穿/刑/破**一律不得 A**；「原文没写冲突」也不自动升 A。")
A("")
A("## 3. 统计")
A("")
m = PACK["metrics"]
A("| 指标 | 值 |")
A("|---|---|")
A(f"| 例数 / 覆盖域 | {m['case_count']} / {'、'.join(DOMAIN_CN.get(d, d) for d in m['domains'])} |")
A(f"| 方向候选 | {m['direction_candidates']}（A {m['candidate_tiers']['A']} · B1 {m['candidate_tiers']['B1']} · B2 {m['candidate_tiers']['B2']} · C {m['candidate_tiers']['C']}） |")
A(f"| A 档占比 | {m['candidate_tier_share']['A']:.2%}（P0 gate ≥50% → **{m['a_share_vs_p0_gate']['verdict']}**） |")
A(f"| 锚点题（B1） | {m['anchor_questions']} 题 |")
A(f"| B2 专家单选 | {m['b2_expert_decisions']} 项（未触发）；B2 / 全部 B 单元 = {m['b2_share_of_B_units']:.2%} |")
A(f"| 状态候选 / 救应候选 | {m['state_candidates']} / {m['rescue_candidates']} |")
A(f"| 引擎校验失败 | {m['engine_validation_failures']}（候选作废 0） |")
A(f"| 原文/宫位引文逐字校验 | {m['source_palace_quotes']['pass']}/{m['source_palace_quotes']['total']} 通过 |")
A(f"| 植入错误（逐卡 4 类） | {'16/16 全部拦截' if m['seeded_error_pass'] else '有漏'} |")
A(f"| 植入错误 self_test（20 fixture） | {m['self_test']['detected']}/{m['self_test']['total']} → {'pass' if m['self_test']['pass'] else 'fail'} |")
A("")
A("**A 档未达 gate 的原因（留给中枢判）**：本题 4 例的 material edge 是夫妻宫冲/合、财印克、丑午穿/戌刑、官入辰墓+印克伤官。"
  "冲/合/穿不得 A（中枢追加），固定类只剩 3 条（C4 的墓/克/生）；C2 的财制印虽为克，但有年干戊/时干己两组财争同一印，需锚点消歧。")
A("")
A("---")
A("")

for card in PACK["cards"]:
    f = card["facts"]
    cid = card["card_id"]
    A(f"# {cid} · {DOMAIN_CN.get(card['domain'], card['domain'])} · {card['four_pillars']}（{card['gender']}）")
    A("")
    A("| 项 | 值 |")
    A("|---|---|")
    A(f"| 卡档位 | **{card['tier']}** / `decision_by={card['decision_by']}` / `direction_tier={card.get('direction_tier')}` / `pending={card.get('pending')}` |")
    A(f"| tier_reason | {card.get('tier_reason')} |")
    A(f"| chart_id / 日主 | `{f['chart_id']}` / {f['day_master']} |")
    A(f"| 快照 | dayun_index=null，liunian_year=null（原局；四柱输入不起运） |")
    A(f"| 问题 | {card['question']['text']} |")
    A(f"| 问题域 | {card['question']['domain']} |")
    A(f"| 原文出处 | `{card['source']['path']}` {card['source']['locator']} |")
    A(f"| 后续事实（备查，不作预测） | {card['source']['outcome_note']} |")
    A("")
    A("## 0.5) 宫位映射与 material edge")
    A("")
    A("| addr | 角色 | 十神 | 映射 | 依据引文 |")
    A("|---|---|---|---|---|")
    for p_ in card.get("palaces", []):
        bq = p_.get("basis_quote") or {}
        A(f"| `{p_['addr']}` | {p_['role']} | {p_['ten_god']} | {p_['mapping_rule']} | `{bq.get('source_ref')}`「{bq.get('text')}」 |")
    A("")
    A("- material edge（问题命中的边）：")
    for eid, why in (card.get("material_edge_reasons") or {}).items():
        A(f"  - `{eid}`：{why}")
    A("")
    A("## 1) engine 事实（`engine.cli all/relations`）")
    A("")
    A("| 柱 | 干支 | 干(addr/十神) | 支(addr/十神) | 藏干 |")
    A("|---|---|---|---|---|")
    for p in f["pillars"]:
        hid = "、".join(f"{h['c']}{h['q']}({h['g']})" for h in p["branch"]["hidden"])
        A(f"| {p['palace']} | {p['ganzhi']} | {p['stem']['char']} `{p['stem']['addr']}` {p['stem']['ten_god']} | {p['branch']['char']} `{p['branch']['addr']}` {p['branch']['main_ten_god']} | {hid} |")
    A("")
    kd = f["kong_wang"]
    A(f"- 旬空：日旬 {kd.get('by_day_xun')}；年旬 {kd.get('by_year_xun')}；命中 {kd.get('hits')}")
    A(f"- 体用（duan_zuogong.tiyong）：{f['tiyong']}")
    A(f"- 墓库（relations.muku）：{f['muku'] if f['muku'] else '（无）'}")
    A("")
    A("### 关系边（原样引用 edge_id）")
    A("")
    A("| edge_id | kind | members | chars | 距离 | 组/完整度 |")
    A("|---|---|---|---|---|---|")
    for e in f["edges"]:
        grp = e.get("group") or ""
        comp = e.get("completeness") or ""
        A(f"| {e['edge_id']} | {e['kind']} | {e['members']} | {e.get('chars')} | {e.get('distance')} | {grp}/{comp} |")
    A("")
    A(f"- 段派做功候选（`duan_zuogong.candidates`，共 {len(f['duan_candidates'])} 条；下表只列本卡引用到的）：")
    A("")
    A("| mode | members | actor | edge_id |")
    A("|---|---|---|---|")
    used = set()
    used_edges = set()
    for c in card["direction_candidates"]:
        ref = c.get("edge_ref") or {}
        if ref.get("type") == "duan_candidate":
            used.add((ref["mode"], tuple(ref["members"]), ref.get("actor")))
        elif ref.get("type") == "edge":
            used_edges.add(ref["edge_id"])
    rows = [
        c
        for c in f["duan_candidates"]
        if (c.get("mode"), tuple(c.get("members") or []), c.get("actor")) in used
        or (c.get("edge_id") in used_edges)
    ]
    if rows:
        for c in rows:
            A(f"| {c['mode']} | {c['members']} | {c['actor']} | {c.get('edge_id')} |")
    else:
        A("| — | — | — | — |")
    A("")
    A("## 2) 原文锚点")
    A("")
    src = card["source"]
    for pq in src["pillar_quote"]:
        A(f"- 命例四柱：`{pq['source_ref']}`「{pq['text']}」")
    if src.get("outcome_quote"):
        oq = src["outcome_quote"]
        A(f"- 后续事实：`{oq['source_ref']}`「{oq['text']}」")
    A("")
    A("## 3) 方向候选（2–3 条，均不自动选定）")
    A("")
    A("| id | 档 | 类/kind | 方向 | 边 | decisive | conflict_with | 校验 |")
    A("|---|---|---|---|---|---|---|---|")
    for c in card["direction_candidates"]:
        ref = c.get("edge_ref") or {}
        edge = ref.get("edge_id") or f"{ref.get('mode')}({ref.get('members')})"
        A(f"| {c['option_id']} | {c['tier']} | {c['class']}/{c['kind']} | {DIR_CN.get(c['direction_type'])} "
          f"{c['actor'] + '→' + c['target'] if c.get('actor') and c.get('target') else ''} | `{edge}` | "
          f"{c['decisive']} | {c.get('conflict_with')} | {c['engine_validation']['status']} |")
    A("")
    for c in card["direction_candidates"]:
        A(f"### {c['option_id']}（{c['tier']} / `{c['decision_by']}`）")
        A("")
        A(f"- 方向：{DIR_CN.get(c['direction_type'])}"
          + (f"，`{c['actor']}`({c.get('actor_char')}) → `{c['target']}`({c.get('target_char')})" if c.get("actor") else "")
          + (f"，evidence_gap={GAP_CN.get(c['evidence_gap'], c['evidence_gap'])}" if c.get("evidence_gap") else ""))
        A(f"- 依据：{c['basis_text']}")
        if c.get("rule_ref"):
            A(f"- 规则：`{c['rule_ref']}`")
        for q in c.get("quotes") or []:
            A(f"- 引文（{q['role']}）：`{q['source_ref']}`「{q['text']}」")
        ev = c["engine_validation"]["checks"]
        A(f"- 校验：address={ev['address']['status']} · edge={ev['edge']['status']} · ten_god={ev['ten_god']['status']} · quote={ev['quote']['status']}"
          + (f"（{ev['edge'].get('detail')}）" if ev["edge"].get("detail") else ""))
        A("")
    A("## 4) 状态候选 / 救应候选")
    A("")
    A("| id | 层 | 档 | 结果 | 主张 | anchored_by |")
    A("|---|---|---|---|---|---|")
    for s in card["state_candidates"]:
        A(f"| {s['option_id']} | state | {s['tier']} | {s['result']} | {s['state_label']} | {s.get('anchored_by')} |")
    for s in card["rescue_candidates"]:
        A(f"| {s['option_id']} | rescue | {s['tier']} | {s['result']} | {s['label']} | {s.get('anchored_by') or '—'} |")
    A("")
    for s in card["state_candidates"] + card["rescue_candidates"]:
        A(f"- **{s['option_id']}**（{s['tier']}，{s['result']}）：{s['basis_text']}")
        for q in s.get("quotes") or []:
            A(f"  - 引文：`{q['source_ref']}`「{q['text']}」")
    A("")
    A("## 5) 锚点题（只问已发生事实）")
    A("")
    if not card["anchor_q"]:
        A("（本卡无 B1 锚点题；见下方 B2 专家单选。）")
        A("")
    for a in card["anchor_q"]:
        A(f"### {a['qid']} · {a['layer']} · discriminates={a['discriminates']}")
        A("")
        A(f"> {a['text']}")
        A("")
        A(f"- 能区分的原因：{a['discriminator_basis']}")
        A(f"- 规则：`{a['rule_ref']}`；`source_mentions_answer={a['source_mentions_answer']}`；proxy={a['proxy_strength']}")
        y, n = a["if_yes"], a["if_no"]
        A(f"- 答「是」：keep {y['keep']}；eliminate {y['eliminate']}" + (f"；downgrade {y['downgrade']}" if y.get("downgrade") else ""))
        A(f"- 答「否」：keep {n['keep']}；eliminate {n['eliminate']}" + (f"；downgrade {n['downgrade']}" if n.get("downgrade") else ""))
        A(f"- 答不出：`{a['if_unknown']['action']}`，影响 {a['if_unknown']['affected']}")
        A("- **答案（留空，待人类/命主）**：`anchor_a: []`")
        A("")
    ed = card.get("expert_decision") or {}
    if ed.get("required"):
        A(f"### {ed['id']} · B2 专家单选（本卡唯一 B2）")
        A("")
        A(f"> {ed['question']}")
        A("")
        A(f"- 选项：{ed['options']}")
        A(f"- 依据：{ed['basis']}")
        for q in ed.get("quotes") or []:
            A(f"- 引文（{q['role']}）：`{q['source_ref']}`「{q['text']}」")
        A("- **裁决（留空）**：`decision: null`；Agent 不代选。")
        A("")
    A("## 6) 引擎校验")
    A("")
    agg = card["engine_validation"]["aggregate"]
    A("| 校验 | 通过/总数 |")
    A("|---|---|")
    for k in ("address", "edge", "ten_god", "quote"):
        A(f"| {k} | {agg[k]['pass']}/{agg[k]['total']} |")
    A(f"| 原文/宫位引文 | {card['engine_validation']['source_and_palace_quotes']['pass']}/{card['engine_validation']['source_and_palace_quotes']['total']} |")
    A("")
    se = card["engine_validation"]["seeded_error"]
    A(f"植入错误自检：{se['caught']}/{se['tested']} 拦截（`{'pass' if se['pass'] else 'fail'}`）")
    A("")
    for it in se["items"]:
        A(f"- {it['seeded']} → {'拦截' if it['caught'] else '漏过'}（{it['detail']}）")
    A("")
    A("## 7) 缺口与非断言")
    A("")
    A(f"- gaps：{', '.join(card['gaps'])}")
    for nc in card["non_claims"]:
        A(f"- 非断言：{nc}")
    A("")
    A("---")
    A("")

A("# 关键选择清单（交中枢/人类）")
A("")
A("> 只答事实，不选方向。答完由后续卡（T-197b）按每题 `elimination`（yes/no/unknown）机械淘汰候选；答不出→该候选转 `needs_anchor`。")
A("")
A("| 序号 | 卡 | 题号 | 层 | 题目（是/否） | 区分候选 | 答「是」 | 答「否」 |")
A("|---|---|---|---|---|---|---|---|")
i = 0
for card in PACK["cards"]:
    for a in card["anchor_q"]:
        i += 1
        A(f"| {i} | {card['card_id']} | {a['qid']} | {a['layer']} | {a['text']} | {a['discriminates']} | keep {a['if_yes']['keep']} / elim {a['if_yes']['eliminate']} | keep {a['if_no']['keep']} / elim {a['if_no']['eliminate']} |")
for card in PACK["cards"]:
    ed = card.get("expert_decision") or {}
    if ed.get("required"):
        i += 1
        A(f"| {i} | {card['card_id']} | {ed['id']} | B2 | {ed['question']}（专家单选，不是事实题） | — | — | — |")
A("")
A("## 答案回收表（留空）")
A("")
A("| 卡 | 题号 | 答案（是/否/不知道） | 回答人 | 时间 | 备注 |")
A("|---|---|---|---|---|---|")
for card in PACK["cards"]:
    for a in card["anchor_q"]:
        A(f"| {card['card_id']} | {a['qid']} |  |  |  |  |")
for card in PACK["cards"]:
    ed = card.get("expert_decision") or {}
    if ed.get("required"):
        A(f"| {card['card_id']} | {ed['id']}（B2） |  |  |  |  |")
A("")
A("# 第三方重推指引")
A("")
A("1. 盘面事实：按每卡 `provenance.engine_cmd` 重跑，比对 `chart_id`、四柱、十神、edge_id/kind/members。")
A("2. 引文：按 `source_ref`（`path:Ln`）打开原文，逐字比对；本包构建脚本对全部引文做了子串校验（24 条原文/宫位引文 + 每候选引文）。")
A("3. 候选：只看 `basis + quote + decisive + conflict_with + evidence_gap`；冲/合/穿/刑不得 A；无源即 C。")
A("4. 复现构建：`.venv\\Scripts\\python.exe tasks/T-197/build_p0_cards.py`（幂等，仅读 `tasks/T-197/_engine/*.json` 与 `sources/`）。")
A("")
A("# 与 T-196 规格的对齐（analysis-card-v2 / agent-candidate-set/v1）")
A("")
sc = PACK.get("schema_compat") or {}
A(f"- 目标 schema：{sc.get('target')}")
A("- 已映射字段：")
for x in sc.get("mapped_fields") or []:
    A(f"  - {x}")
A("- 扩展（v2 未定义，本包保留）：")
for x in sc.get("extensions") or []:
    A(f"  - {x}")
A("- 未实现（需选定后装配，或按 T-197 禁止代选）：")
for k, v in (sc.get("not_implemented") or {}).items():
    A(f"  - `{k}`：{v}")
A("- 已知口径冲突：")
for x in sc.get("known_conflicts") or []:
    A(f"  - {x}")
A("")
A("# 未完成与风险")
A("")
for g in PACK["known_gaps"]:
    A(f"- {g}")
A("- 本包 4 例的方向候选里，P0-01/P0-03 的『单侧施力』读法都依赖结果句/计数句（evidence_gap=same_page），是否够格作方向依据，需中枢裁。")
A("- 锚点题答案与原文后续事实存在部分可推测性（例：P0-01 原文已写五次婚姻）；本包题目刻意选原文**未写**的事实（原生家庭是否介入、分开后是否仍有往来、收入结构、发病前家庭变故、心脏症状）以降低泄漏。")
A("- P0-04 的『原局富 vs 岁运破』属**成败层**，按 analysis-card-v2 §5.3 不适用方向层 B2，已改为 state 锚点题（AQ1，`source_mentions_answer=true`）；本包 B2=0。")
A("- 本包是 `agent-candidate-set/v1` 的 **pending** 形态（`pending=anchor_q`），不是可交付的 `analysis-card/v2`：v2 的 `t1–t5` / `statement_claims` 须在选定后装配，而 T-197 禁止代选。")
A("")

out = os.path.join(ROOT, "META", "p0-case-packets-v1.md")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(L).rstrip() + "\n")
print("wrote", out, "lines:", len(L))
