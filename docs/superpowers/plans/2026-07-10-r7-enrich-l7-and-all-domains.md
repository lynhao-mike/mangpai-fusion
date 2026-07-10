# R7 执行计划：加厚 L7 ViewModel 并全域改读 L7

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 先让 L7 ReportViewItem 的 display_text 携带各派依据（不再是单薄的一句 reason），再把 v6 报告其余五域（学业/财富/婚姻/健康，事业 R6 已完成）全部改读 L7，收尾双轨期。

**Architecture:** R6 已让"事业"域读 L7 并证明可行。但 L7 display_text 目前是 `f"{decision.domain}：{decision.reason}"`（[`v5_adapter.py:220`](../../../engine/decision/v5_adapter.py:220)），信息量少于旧 v5 渲染。R7 分两步：(1) 让 [`_report_items`](../../../engine/decision/v5_adapter.py:208) 能访问 school_claims，把各域五派命题摘要聚合进 display_text 与 evidence_summary；(2) 把 [`report_view.py`](../../../engine/v5/report_view.py:264) 的事业单域覆盖扩展为 DOMAINS 全域覆盖。

**Tech Stack:** Python 3、pytest。纯内存数据流，无外部依赖、无 IO 新增。

## Global Constraints

- 事实源以 [`AGENTS.md`](../../../AGENTS.md) 为准；方向以 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) §18 Phase R6 与 [`plans/l0-l9-refactor-geju-judgment-2026-07-10.md`](../../../plans/l0-l9-refactor-geju-judgment-2026-07-10.md) 为准。
- **缺省零回归**：不传 report_items 时报告输出与改动前逐字一致。用现有 v5 报告测试守护。
- L7 加厚只允许**聚合已有的 L2 claim / L6 decision 信息**，不新增命理推理、不改 L1-L6 逻辑、不改 DecisionRun schema。
- 展示层禁显约束（见 AGENTS.md §5.2）：display_text 里**不得**出现 claim_id / decision_id / statement_id / 结构图编号等内部 ID。只聚合可读文本（流派名、依据摘要、支持条数）。
- 不修复 L3 无 reject / L4 event_type 占位——那是 R8+ 与 L3 命局建模的独立工作。
- 每个任务结束跑绿相关测试；Windows cmd.exe：命令用 `&&` 串联，不用 `sed`/`grep`/`cat`；提交信息用中文。

## 背景事实（执行前必读，已实测确认）

1. C-2026-035 五域 L7 display_text 域归类均正确（事业→事业…），前缀正确。当前文本统一为："X：高德臣、段建业、杨清娟参与事件落地；结构约束来自：结构裁决（N条支持）…"，信息量少于旧 v5 五派分列渲染。
2. [`_report_items(case_id, decisions, timings)`](../../../engine/decision/v5_adapter.py:208) 当前签名**不含 claims**，故 L7 拿不到五派命题——这是 display_text 单薄的根因。
3. `display_text = f"{decision.domain}：{decision.reason}"`，见 [`v5_adapter.py:220`](../../../engine/decision/v5_adapter.py:220)。`decision.reason` 来自 v5 arbitration。
4. [`decision_run_from_v5`](../../../engine/decision/v5_adapter.py:229) 在第 238 行已算出 `claims`（list[SchoolClaim]），调用 `_report_items` 时可一并传入。
5. R6 已在 [`report_view.py`](../../../engine/v5/report_view.py:264) 落地事业单域覆盖（264-267 行），并有 `for domain in DOMAINS` 循环（258 行）与 `DOMAINS = ("学业","事业","财富","婚姻","健康")`（17 行）。
6. SchoolClaim 字段：`school / domain / statement / confidence`（见 [`models.py`](../../../engine/decision/models.py:115)）；SCHOOLS 中文名映射见 [`report_view.py:18`](../../../engine/v5/report_view.py:18)。

---

### Task 1: _report_items 接收 claims，按域聚合五派依据进 L7（TDD）

**Files:**
- Modify: `engine/decision/v5_adapter.py`
- Test: `tests/v5/test_report_reads_l7.py`（追加）

**Interfaces:**
- 改 `_report_items(case_id, decisions, timings, claims)` — 末尾加 `claims: list[SchoolClaim]` 参数。
- L7 display_text 从 `f"{domain}：{reason}"` 增强为：`f"{domain}：{reason}｜参与流派：{各派名}｜依据：{每派一句 statement 摘要}"`，其中依据只取该 domain 下、confidence 最高的每派一条 statement，截断到合理长度；不含任何内部 ID。
- evidence_summary 从固定文案改为 `f"本域共 {n} 条流派命题参与结构裁决。"`。

- [ ] **Step 1: 写失败测试**

在 [`tests/v5/test_report_reads_l7.py`](../../../tests/v5/test_report_reads_l7.py) 末尾追加：

```python
def test_report_items_display_text_carries_school_evidence():
    from engine.decision.v5_adapter import _report_items
    from engine.decision.models import ArbitrationDecision, SchoolClaim, TimingProbability

    decisions = [
        ArbitrationDecision(
            decision_id="d-career", domain="事业", competing_event_ids=["e1"],
            result="winner", winner_ids=["e1"], reason="事业裁决",
        )
    ]
    claims = [
        SchoolClaim(claim_id="c1", school="ziping", role_granted_by_l1="lead", domain="事业",
                    claim_type="structure", statement="正印格用食伤", confidence=0.8),
        SchoolClaim(claim_id="c2", school="duan_jianye", role_granted_by_l1="lead", domain="事业",
                    claim_type="event", statement="做功制用明显", confidence=0.7),
    ]
    items = _report_items("C-T", decisions, [], claims)
    assert items, "应产出至少一条 report item"
    text = items[0].display_text
    assert "事业" in text
    assert "正印格用食伤" in text or "做功制用明显" in text
    # 不得泄露内部 ID
    assert "c1" not in text and "d-career" not in text
    assert items[0].evidence_summary


def test_report_items_default_domain_without_claims_still_works():
    from engine.decision.v5_adapter import _report_items
    from engine.decision.models import ArbitrationDecision

    decisions = [
        ArbitrationDecision(
            decision_id="d-x", domain="健康", competing_event_ids=["e1"],
            result="winner", winner_ids=["e1"], reason="健康裁决",
        )
    ]
    items = _report_items("C-T", decisions, [], [])
    assert items and "健康" in items[0].display_text
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/v5/test_report_reads_l7.py::test_report_items_display_text_carries_school_evidence -v`
Expected: FAIL（`_report_items` 目前只接受 3 个参数 → TypeError）。

- [ ] **Step 3: 改 _report_items 实现**

在 [`engine/decision/v5_adapter.py`](../../../engine/decision/v5_adapter.py:208) 把 `_report_items` 改为：

```python
_SCHOOL_ZH = {
    "ziping": "子平类",
    "ditiansui": "滴天髓类",
    "gao_dechen": "高德臣",
    "duan_jianye": "段建业",
    "yang_qingjuan": "杨清娟",
    "ren_fuhong": "任付红",
}


def _domain_evidence(domain: str, claims: list[SchoolClaim]) -> tuple[list[str], list[str], int]:
    """聚合某域下各派最高置信命题：返回(参与流派中文名, 每派一句依据摘要, 命题条数)。"""

    domain_claims = [c for c in claims if c.domain == domain and c.statement]
    best_by_school: dict[str, SchoolClaim] = {}
    for c in domain_claims:
        cur = best_by_school.get(c.school)
        if cur is None or c.confidence > cur.confidence:
            best_by_school[c.school] = c
    schools_zh: list[str] = []
    evidences: list[str] = []
    for school, claim in best_by_school.items():
        schools_zh.append(_SCHOOL_ZH.get(school, school))
        snippet = claim.statement.strip().replace("\n", " ")
        if len(snippet) > 40:
            snippet = snippet[:40] + "…"
        evidences.append(f"{_SCHOOL_ZH.get(school, school)}：{snippet}")
    return schools_zh, evidences, len(domain_claims)


def _report_items(
    case_id: str,
    decisions: list[ArbitrationDecision],
    timings: list[TimingProbability],
    claims: list[SchoolClaim],
) -> list[ReportViewItem]:
    timing_by_domain = {timing.event_id: timing for timing in timings}
    items: list[ReportViewItem] = []
    for decision in decisions:
        event_ids = decision.rejected_ids if decision.result == "reject_all" else decision.winner_ids or decision.competing_event_ids
        schools_zh, evidences, n_claims = _domain_evidence(decision.domain, claims)
        base = f"{decision.domain}：{decision.reason}"
        if schools_zh:
            base += "｜参与流派：" + "、".join(schools_zh)
        if evidences:
            base += "｜依据：" + "；".join(evidences)
        for idx, event_id in enumerate(event_ids, start=1):
            timing = timing_by_domain.get(event_id)
            items.append(
                ReportViewItem(
                    report_item_id=_stable_id("drv", case_id, decision.decision_id, idx),
                    decision_id=decision.decision_id,
                    prediction_id=timing.prediction_id if timing else "",
                    display_text=base,
                    confidence_display="迁移期，以 v5 置信度为准",
                    evidence_summary=f"本域共 {n_claims} 条流派命题参与结构裁决。" if n_claims else "L7 读取 v5→decision 适配后的 L6/L5 结果。",
                    feedback_prompt="按预测账本反馈命中、失验、半命中或跳过。",
                )
            )
    return items
```

- [ ] **Step 4: 更新 _report_items 调用点**

在 [`decision_run_from_v5`](../../../engine/decision/v5_adapter.py:229) 找到 `_report_items(...)` 的调用（在 `decisions` 与 `timings` 算好之后），补上 `claims` 实参：

```python
    report_items = _report_items(case_id, decisions, timings, claims)
```

> 用 search 确认调用行的确切写法；`claims` 变量在第 238 行已存在，直接传入。

- [ ] **Step 5: 运行确认通过**

Run: `python -m pytest tests/v5/test_report_reads_l7.py -v`
Expected: 全部 PASS（含 R6 已有测试 + 本 Task 两条新测试）。

- [ ] **Step 6: decision 回归**

Run: `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q`
Expected: 全绿。若 `_report_items` 调用点在别处也存在（用 search 确认），一并补 claims 参数。

- [ ] **Step 7: 提交**

```bash
git add engine/decision/v5_adapter.py tests/v5/test_report_reads_l7.py && git commit -m "feat: L7 report_items 聚合各派依据进 display_text，加厚 ViewModel"
```

---

### Task 2: report_view 全域改读 L7（TDD）

**Files:**
- Modify: `engine/v5/report_view.py`
- Test: `tests/v5/test_report_reads_l7.py`（追加）

**Interfaces:**
- 把 [`report_view.py:264`](../../../engine/v5/report_view.py:264) 的事业单域覆盖，改为对 DOMAINS 全域循环覆盖：每个域若能从 L7 取到文本，则覆盖 `context[f"{域}裁决结论"]` 与 `context[f"{域}共识结论"]`；取不到则保持旧值（该域零回归）。

- [ ] **Step 1: 写失败测试**

在 [`tests/v5/test_report_reads_l7.py`](../../../tests/v5/test_report_reads_l7.py) 末尾追加：

```python
def test_context_all_domains_use_l7_when_provided():
    from engine.v5 import run_v5
    from engine.v5.report_view import build_report_v6_context

    output = run_v5({"case_id": "C-TEST-R7", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    template_text = "{{ 事业裁决结论 }}|{{ 健康裁决结论 }}|{{ 财富裁决结论 }}"

    report_items = [
        {"report_item_id": "r1", "decision_id": "d-c", "display_text": "事业：L7事业。"},
        {"report_item_id": "r2", "decision_id": "d-h", "display_text": "健康：L7健康。"},
        {"report_item_id": "r3", "decision_id": "d-w", "display_text": "财富：L7财富。"},
    ]
    decisions = [
        {"decision_id": "d-c", "domain": "事业"},
        {"decision_id": "d-h", "domain": "健康"},
        {"decision_id": "d-w", "domain": "财富"},
    ]
    ctx = build_report_v6_context(
        output, template_text=template_text,
        report_items=report_items, arbitration_decisions=decisions,
    )
    assert ctx["事业裁决结论"] == "事业：L7事业。"
    assert ctx["健康裁决结论"] == "健康：L7健康。"
    assert ctx["财富裁决结论"] == "财富：L7财富。"


def test_context_domain_without_l7_keeps_default():
    from engine.v5 import run_v5
    from engine.v5.report_view import build_report_v6_context

    output = run_v5({"case_id": "C-TEST-R7-PART", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    template_text = "{{ 婚姻裁决结论 }}"

    # 只提供事业的 L7，婚姻无 → 婚姻保持默认
    report_items = [{"report_item_id": "r1", "decision_id": "d-c", "display_text": "事业：L7事业。"}]
    decisions = [{"decision_id": "d-c", "domain": "事业"}]
    default_ctx = build_report_v6_context(output, template_text=template_text)
    l7_ctx = build_report_v6_context(
        output, template_text=template_text,
        report_items=report_items, arbitration_decisions=decisions,
    )
    assert l7_ctx["婚姻裁决结论"] == default_ctx["婚姻裁决结论"]
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/v5/test_report_reads_l7.py::test_context_all_domains_use_l7_when_provided -v`
Expected: FAIL（当前只覆盖事业，健康/财富仍是旧值）。

- [ ] **Step 3: 把事业单域覆盖改为全域循环**

在 [`engine/v5/report_view.py`](../../../engine/v5/report_view.py:264) 找到 R6 的事业单域覆盖：

```python
    l7_career = _l7_conclusion_for_domain("事业", report_items or [], arbitration_decisions or [])
    if l7_career:
        context["事业裁决结论"] = l7_career
        context["事业共识结论"] = l7_career
```

替换为全域循环：

```python
    for _domain in DOMAINS:
        _l7_text = _l7_conclusion_for_domain(_domain, report_items or [], arbitration_decisions or [])
        if _l7_text:
            context[f"{_domain}裁决结论"] = _l7_text
            context[f"{_domain}共识结论"] = _l7_text
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/v5/test_report_reads_l7.py -v`
Expected: 全部 PASS。

- [ ] **Step 5: 零回归验证**

Run: `python -m pytest tests/v5/test_render_report_v6.py tests/v5/test_v5_contracts.py -q`
Expected: 全绿。缺省（不传 report_items）时 DOMAINS 循环内 `_l7_text` 恒为 None，不覆盖任何域，行为不变。

- [ ] **Step 6: 提交**

```bash
git add engine/v5/report_view.py tests/v5/test_report_reads_l7.py && git commit -m "feat: 报告全域改读 L7 裁决结论，缺省零回归"
```

---

### Task 3: 重跑 C-2026-035 验证全域 + 文档状态更新

**Files:**
- Modify: `plans/layered-decision-system.md`

**Interfaces:**
- Produces: §18 Phase R6 状态更新为"全域已读 L7、L7 已加厚（含各派依据）"。

- [ ] **Step 1: 重跑真实 case**

Run: `python tools/render_report_v6.py cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md --output-dir reports`
Expected: 退出码 0。

- [ ] **Step 2: 验证五域报告文本均来自 L7 且含各派依据**

Run:
```bash
python -c "import json,pathlib,sys; base='reports/C-2026-035-乾-戊辰癸亥甲戌庚午-v6-preprod-content-report'; d=json.loads(pathlib.Path(base+'.decision-run.json').read_text(encoding='utf-8')); r=pathlib.Path(base+'.md').read_text(encoding='utf-8'); dom={x['decision_id']:x['domain'] for x in d['arbitration_decisions']}; texts={dom.get(ri['decision_id']):ri['display_text'] for ri in d['report_items']}; missing=[k for k in ('事业','财富','婚姻','健康','学业') if k in texts and texts[k] not in r]; has_evidence=any('依据：' in t for t in texts.values()); sys.exit(0 if not missing and has_evidence else 1)"
```
Expected: 退出码 0（五域 L7 文本都进了报告，且 display_text 含"依据："各派摘要）。

- [ ] **Step 3: 更新 Phase R6 状态**

在 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) §18 Phase R6 的状态行更新为：

```markdown
> 状态：全域已落地（学业/事业/财富/婚姻/健康五域报告裁决结论均改读 L7 ReportViewItem；L7 display_text 已加厚，聚合各派最高置信依据；缺省零回归，见 tests/v5/test_report_reads_l7.py）。北极星仍是 v5 runner 下沉为 L2、L3 接真实命局审查、L4 从结构推导事件类型。
```

- [ ] **Step 4: 提交**

```bash
git add plans/layered-decision-system.md && git commit -m "docs: 标记 R6/R7 报告全域读 L7 且 L7 已加厚"
```

---

## 验收总清单（全部完成后执行一次）

- [ ] `python -m pytest tests/v5/test_report_reads_l7.py tests/v5/test_render_report_v6.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q` 全绿。
- [ ] 不传 report_items 时报告输出与改动前逐字一致（缺省零回归）。
- [ ] 重跑 C-2026-035 后，五域报告裁决文本均来自 decision-run.json 对应域的 L7 display_text。
- [ ] L7 display_text 含"参与流派"与"依据：<各派摘要>"，且不含 claim_id / decision_id 等内部 ID。
- [ ] [`report_view.py`](../../../engine/v5/report_view.py) 与 [`v5_adapter.py`](../../../engine/decision/v5_adapter.py) 未新增文件 IO、未 import tools。

## 证伪口径（对照架构 §18 R6）

- 若加厚后 display_text 出现内部 ID（claim_id/decision_id），违反 AGENTS.md §5.2 展示层禁显约束，必须回到 Task 1 只聚合可读文本。
- 若全域读 L7 后，某域报告结论与旧 v5 渲染语义矛盾（不是同一裁决两种说法，而是结论相反），说明 V5Output 与 DecisionRun 该域已语义漂移，须先对齐再继续。
- R7 只让报告"读"分层链，**不**改 L3 审查 / L4 事件推导 / v5 runner 下沉——那些是 R8+ 与 L3 命局建模的独立工作。L7 目前仍是"聚合 v5 命题"，真正的"从结构推导事件类型"仍未做。

## Self-Review 记录

- Spec 覆盖：R7 目标（加厚 L7 + 全域读 L7）由 Task 1（_report_items 聚合各派依据）+ Task 2（DOMAINS 全域覆盖）+ Task 3（真实 case 验证）覆盖。
- Placeholder 扫描：无 TBD；每个代码步骤给完整可粘贴代码；仅 Task 1 Step 4 / Task 2 Step 3 要求先 search 确认调用点（已标注）。
- 类型一致：`_report_items(case_id, decisions, timings, claims)` 新签名在实现与调用点一致；`_domain_evidence` 返回三元组与 `_report_items` 消费一致；`_l7_conclusion_for_domain` 复用 R6 已有函数，签名不变。
- 已知风险显式化：缺省零回归（Task 1 Step 6 + Task 2 Step 5 + 验收）、展示层禁显 ID（Global Constraints + 证伪口径 + Task 1 测试断言）、不碰 L3/L4/runner 下沉（证伪口径）。
- 已实测确认：五域 L7 域归类正确；display_text 单薄根因是 `_report_items` 拿不到 claims；report_view 已有 DOMAINS 循环与事业单域覆盖可扩展。
