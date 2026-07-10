# 分层 L0-L9 架构实施缺口调查报告

> 调查日期：2026-07-10  
> 调查对象：`reports/C-2026-035-乾-戊辰癸亥甲戌庚午-v6-preprod-content-report.decision-run.json`  
> 方法：对比 `plans/layered-decision-system.md` 设计目标与 decision-run.json 实际数据  
> 本文档是调查事实记录，不包含重构结论——结论由 claude-fable-5 给出。

---

## 1. 当前已符合的层（验证通过）

| 层 | 关键字段 | 实际计数 / 状态 | 结论 |
|---|---|---|---|
| L0 | `chart_ledger.four_pillars`, `raw_payload.raw_hash`, `chart_ledger.raw_source_hash` | 四柱完整，hash 已绑定 | ✅ 符合 |
| L1 | `school_applicability` 6 条，含 role/score/reasons/falsifier | ziping:lead, ditiansui:lead, duan:lead, yang:co_lead, ren:evidence_only, gao:evidence_only | ✅ 结构符合，见缺口 1 |
| L2 | `school_claims` | 330 条，含 school/domain/claim_type/confidence/falsifier | ✅ 符合 |
| L3 | `structural_verdicts` | 330 条：pass 287 / weaken 41 / reject 0 | ✅ 结构符合，见缺口 2 |
| L5 | `timing_probabilities` | 5 条，绑定 event_id，含 probability_range | ✅ 符合 |
| L6 | `arbitration_decisions` | 5 条：事业 winner / 财富 winner / 婚姻 winner / 健康 winner / 学业 unresolved | ✅ 结构符合 |
| L7 | `report_items` | 5 条，绑定 decision_id | ✅ 结构符合，见缺口 4 |
| L8 | `feedback_signals`, `feedback_attributions` | 各 5 条，verdict 全为 unknown（等真实反馈） | ✅ 符合 |
| L9 | `calibration_actions` | 0 条（无 miss → 正确不产生动作） | ✅ 符合 |

---

## 2. 缺口 1：L1 无 abstain，dayun_steps 解析路径 gap

### 设计预期
- ren_fuhong（任付红）在无大运节点时应被路由为 abstain。
- gao_dechen（高德臣）在神煞信号弱时也应考虑降为 abstain 或 evidence_only。

### 实际状态
- `decision-run.json` 中 `chart_ledger.dayun_steps = []`（空列表）。
- 路由器 [`l1_school_router.route_schools()`](../../../engine/decision/l1_school_router.py:52) 以 `has_dayun = bool(chart.dayun_steps)` 判断，空列表 → `has_dayun=False` → ren_fuhong 降为 `evidence_only` 而非 `abstain`。

### 根因代码位置
1. **v5.json 的 chart 字段**：包含 `dayun_summary`（文字汇总字符串）但不包含 `dayun_steps`（结构化列表）。
   - `chart.get("dayun_steps")` 返回 `None`。
   - 见 [`engine/decision/v5_adapter.py:64`](../../../engine/decision/v5_adapter.py:64)：`dayun_steps=list(chart.get("dayun_steps") or [])`。
2. **v5 runner 产出 chart 时**：只写入 `dayun_summary`（拼成字符串），未写入结构化 `dayun_steps` 列表。
3. 结果：L1 路由器因拿不到大运步，无法正确判断 ren_fuhong 是否有授权。

### 缺口影响
- ren_fuhong 虽降为 evidence_only，但它仍然发了命题（330 条中有它的命题）。
- 缺口不影响 validate_trace 通过，但影响"什么时候用任派"的学习准确性。

---

## 3. 缺口 2：L3 结构审查是通道而非否决关口（0 reject）

### 设计预期
- L3 应有真正的否决权，能 reject 孤证、神煞孤断、无根断语。
- reject 后，下层 L4/L5 不应消费这些命题。

### 实际状态
- 330 条 verdict：pass 287 / weaken 41 / **reject 0**。
- L3 当前只对 `claim.confidence <= 0.1` 才 reject。
- 所有 330 条命题的 confidence 均 > 0.1，所以无一被 reject。

### 根因代码位置
[`engine/decision/l3_structure.py:20`](../../../engine/decision/l3_structure.py:20)：
```python
verdict = "pass" if claim.claim_type == "structure" and claim.confidence >= 0.5 else "weaken"
if claim.confidence <= 0.1:
    verdict = "reject"
```

L3 的 reject 条件只有一个：`confidence <= 0.1`，而 v5 命题的默认 confidence 均在 0.35–0.9 之间，永远不会触发 reject。

L3 没有实现设计要求的"命局结构基础审查"（如检查日主旺衰、用神是否成立、神煞是否孤证），只是做了 confidence 阈值过滤，属于占位实现。

---

## 4. 缺口 3：L4 事件类型全为 v5_prediction 占位符

### 设计预期
- EventHypothesis.event_type 应为具体事件类型（如"升迁/换岗/结婚/破财/手术"等）。
- L4 应从通过 L3 审查的结构命题中推导现实事件。

### 实际状态
- 5 条 EventHypothesis 的 event_type 全为 `"v5_prediction"`。

### 根因代码位置
[`engine/decision/v5_adapter.py:139`](../../../engine/decision/v5_adapter.py:139)：
```python
events.append(
    EventHypothesis(
        ...
        event_type="v5_prediction",   # ← 硬编码占位符
        ...
    )
)
```

v5_adapter 的 `_events()` 直接把 v5 预测账本（PredictionLedger）的每条 prediction 转为 L4 事件，跳过了"从 L3 结构命题推导具体事件类型"这一步。这是迁移过渡的妥协，不是正式 L4。

独立的 MVP L4（[`engine/decision/l4_events.py`](../../../engine/decision/l4_events.py)）实现使用了"可反馈现实事件"和"待具体化事件"作为 event_type，同样是占位符。

---

## 5. 缺口 4：报告 Markdown 与 L7 ReportViewItem 分离

### 设计预期
- 报告中每一条结论应能通过 report_item_id 追溯到 L7 ReportViewItem → L6 decision → L4 event → L3 verdict → L2 claim → L1 applicability → L0 chart。
- 报告层不补推理，只消费 L7 裁判结果。

### 实际状态
- decision-run.json 中只有 **5 条 L7 ReportViewItem**（每个域一条）。
- 报告 Markdown 有大量"15 层判断表"（每个域 15 行），这些内容**没有 report_item_id**。
- 报告 Markdown 与 decision-run 是**并列的独立产物**，互不知道对方。

### 根因代码位置
[`engine/v5/preprod.py:242–284`](../../../engine/v5/preprod.py:242)：
```python
# 两条独立路径并列：
report_md = render_report_v6_from_output(output, ...)   # ← 从 V5Output 渲染 Markdown
decision_run = decision_run_from_snapshot(snapshot)      # ← 从 snapshot 派生 DecisionRun
```

报告 Markdown 由 [`engine/v5/report_view.render_report_v6_from_output()`](../../../engine/v5/report_view.py:304) 从 V5Output + templates/report-v6.md 渲染，只用简单的 `{{ key }}` 占位符替换，直接消费 v5 claims/arbitration/predictions，完全绕过了 L7 链路。

---

## 6. 总结：现有系统与设计目标的距离

| 问题 | 根因文件 | 是真实命理推理问题还是架构配管问题 |
|---|---|---|
| dayun_steps 空（L1 路由失准） | `engine/v5/runner.py` 产出 chart 时未写 `dayun_steps` 列表 | 配管问题：数据格式转换 gap |
| L3 无 reject（审查是通道） | `engine/decision/l3_structure.py` 只用 confidence<=0.1 才 reject | 架构问题：L3 是占位实现，未接入真实命局结构审查 |
| L4 event_type 为占位符 | `engine/decision/v5_adapter.py` 硬编码 `event_type="v5_prediction"` | 架构问题：v5_adapter 的迁移妥协，L4 未从命题推导事件类型 |
| 报告 Markdown 与 L7 分离 | `engine/v5/preprod.py` 两条独立路径并列 | 架构问题：报告渲染未走 L7 链路，而是直接消费 V5Output |

---

**本文档只记录代码事实，不含重构结论。请切换到 claude-fable-5 模型后给出重构方向与优先级判断。**
