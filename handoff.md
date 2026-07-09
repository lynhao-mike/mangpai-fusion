# HANDOFF · 分层决策系统重构交接

> 写给完全没有当前会话上下文的新会话。
>
> 当前仓库：`f:/综合盲派/mangpai-fusion`
>
> 当前主任务：使用 ponytail + geju 思路，根据 `plans/layered-decision-system.md` 推进"分层命理决策学习系统"重构。

---

## 1. 我们在做什么任务

目标不是继续补旧的"多派融合报告生成器"，而是按 `plans/layered-decision-system.md` 建立一个可追溯、可反馈、可校准的 L0-L9 分层决策系统。

核心方向：

```text
事实准确
→ 流派选对
→ 命题独立
→ 结构有审查
→ 事件可验证
→ 应期可证伪
→ 冲突可裁决
→ 报告不失真
→ 反馈可归因
→ 策略可淘汰
```

当前采取的落地策略：

1. **geju 方向**：坚决从"多流派综合评分/大杂烩"转向"司法式分层决策链"。
2. **ponytail 实施**：每轮只补最短闭环，不上复杂抽象、不新增依赖、不切默认生产入口。
3. **验收标准**：每次改动必须有最小测试，跑指定 pytest 子集，不能凭感觉说完成。

---

## 2. 已经完成了什么

### 2.1 已建立/推进的核心模块

当前已有 `engine/decision/` 分层决策栈，主要模块如下：

| 层级 | 文件 | 当前状态 |
|---|---|---|
| L0 输入事实 | `engine/decision/l0_wenzhen.py`、`engine/decision/l0_context.py` | 已有最小问真文本事实账本与上下文账本 |
| L1 流派路由 | `engine/decision/l1_school_router.py` | 已有 rule-based 路由，支持 lead/co_lead/evidence_only/abstain |
| L2 独立命题 | `engine/decision/l2_claims.py` | 已有 SchoolClaim 最小生成 |
| L3 结构审查 | `engine/decision/l3_structure.py` | 已支持 pass/weaken/reject/unknown；极低置信 `confidence <= 0.1` 会 reject |
| L4 事件落地 | `engine/decision/l4_events.py` | 已能从结构 verdict 生成事件假设 |
| L5 应期概率 | `engine/decision/l5_timing.py` | 已有基础时间窗和概率输出；probability_range 已按置信度分档 |
| L6 冲突仲裁 | `engine/decision/l6_arbitration.py` | 已支持 winner/coexist/unresolved/reject_all；按 domain 分组仲裁 |
| L7 报告表达 | `engine/decision/l7_report_view.py` | 已有只读裁判结果的报告视图项；支持多个裁决 |
| L8 反馈归因 | `engine/decision/l8_feedback_attribution.py` | 已覆盖 L0-L7 全部关键词归因路线 |
| L9 校准治理 | `engine/decision/l9_calibration.py` | 已支持 review/freeze；聚合 key 为 (layer, object_id) 不跨层误聚合 |
| 编排器 | `engine/decision/orchestrator.py` | 已有内存 DecisionRun 最小闭环 |
| 核心模型 | `engine/decision/models.py` | 已有 DecisionRun 与 L0-L9 数据模型；validate_trace 已覆盖 L0-L9 链路 |

### 2.2 本轮会话完成的重要代码改动

#### L5：概率区间随事件置信度派生

文件：`engine/decision/l5_timing.py`

已完成：
- 新增 `_probability_range_for_confidence()`：`< 0.3 → (0.1, 0.3)`，`< 0.6 → (0.3, 0.6)`，`≥ 0.6 → (0.6, 0.8)`。
- `build_timing_probabilities()` 改为遍历所有事件，不再只取第一个事件。

测试：`tests/test_decision_mvp.py`
- `test_l5_probability_range_follows_event_confidence()`

#### L7：报告视图支持多个裁决

文件：`engine/decision/l7_report_view.py`

已完成：
- `build_report_items()` 遍历全部裁决；通过 `winner_ids` 或 `competing_event_ids` 匹配正确 timing。

测试：`tests/test_decision_mvp.py`
- `test_l7_report_items_follow_each_arbitration_decision_and_matching_timing()`

#### L3：旁证命题标记 unknown 而非 weaken

文件：`engine/decision/l3_structure.py`

已完成：
- `claim_type in {"event", "timing", "evidence"}` 的命题 verdict = `unknown`。

测试：`tests/test_decision_mvp.py`
- `test_l3_marks_evidence_claim_as_unknown_not_structural_weaken()`

#### L4：evidence-only 旁证不落事件

文件：`engine/decision/l4_events.py`

已完成：
- 事件化只针对 `claim_type == "event"` 且角色非 `evidence_only` 的 claim。
- fallback 兜底只对 `claim_type == "structure"` 生成槽位，不生成旁证事件。

测试：`tests/test_decision_mvp.py`
- `test_l4_does_not_turn_evidence_only_claim_into_event()`
- `test_l4_fallback_does_not_turn_evidence_verdict_into_event()`

#### L2：evidence_only 角色不产出 structure/event/timing 命题

文件：`engine/decision/l2_claims.py`

已完成：
- `role == "evidence_only"` 时，所有非 `evidence` 类型的模板统一降级为 `evidence`，并在 statement 前加"旁证参考"。

测试：`tests/test_decision_mvp.py`
- `test_l2_evidence_only_role_does_not_emit_structure_claim()`
- `test_l2_evidence_only_role_does_not_emit_timing_claim()`
- `test_l2_evidence_only_role_does_not_emit_event_claim()`

#### L6：按 domain 分组仲裁

文件：`engine/decision/l6_arbitration.py`

已完成：
- 先按 `EventHypothesis.domain` 分组，再在每个领域内部执行仲裁。

测试：`tests/test_decision_mvp.py`
- `test_l6_arbitration_groups_events_by_domain()`

#### L8：完整关键词归因路线

文件：`engine/decision/l8_feedback_attribution.py`

已完成：根据 `observed_fact/observed_time/notes` 文本关键词优先归因：

| 关键词 | 归因层 |
|---|---|
| 输入矛盾 / 事实矛盾 / 补充事实 | L0 |
| 流派选错 / 主审连续失验 / 主审失验 | L1 |
| 原命题 / 命题弱 / 命题不成立 | L2 |
| 结构基础 / 结构弱 / 结构不成立 / 结构审查 | L3 |
| 事件类型 / 类型错 | L4 |
| 年份偏差 / 时间偏差 / 时间窗错 / 应期 | L5 |
| 两派冲突 / 选错一方 / 仲裁选错 | L6 |
| 表达 / 太绝对 / 只是倾向 / 报告失真 | L7 |

测试：`tests/test_decision_v5_adapter.py`
- `test_l8_notes_can_route_to_l4_or_l7()`
- `test_l8_input_conflict_notes_route_to_l0()`
- `test_l8_school_routing_failure_notes_route_to_l1()`
- `test_l8_weak_original_claim_notes_route_to_l2()`
- `test_l8_structural_problem_notes_route_to_l3()`
- `test_l8_time_deviation_notes_route_to_l5()`
- `test_l8_arbitration_conflict_notes_route_to_l6()`
- `test_l8_tendency_expression_notes_route_to_l7()`
- `test_l8_batch_keyword_routes()` (批量参数化测试)

#### L9：治理动作改进

文件：`engine/decision/l9_calibration.py`

已完成：
- 聚合 key 从 `affected_object_id` 改为 `(affected_layer, affected_object_id)`，避免跨层误聚合。
- 重复失验同一对象累计 3 条以上生成 freeze；否则 review。
- freeze 只生成 1 条动作，聚合所有 evidence_feedback_ids。

测试：`tests/test_decision_v5_adapter.py`
- `test_l9_freezes_repeated_review_target()`
- `test_l9_keeps_same_target_id_separate_across_layers()`

### 2.3 最近一次完整验证结果

```bash
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/v5/test_v5_output_linter.py tests/v5/test_render_report_v6.py tests/test_production_service.py tests/test_project_metadata.py -q
```

结果：

```text
58 passed, 1 warning in 70.14s (0:01:10)
```

warning 是既有问题：
```text
engine/application/pipeline_runner.py:10: DeprecationWarning: engine.application.dual_engine_adapter is deprecated.
```
这不是本轮重构引入的问题。

---

## 3. 当前卡在哪

L0-L9 决策栈主链路已经稳定，L6/L7/L8/L9 的关键功能已初步铺完。当前没有明显的"卡点"。

剩余可继续的方向（按优先级排序）：

### 方向 A：v5 adapter 跟上决策栈改动（中优先级）
`engine/decision/v5_adapter.py` 中的 `_timings()/_report_items()` 等映射函数可能未同步最新的 L5/L7 改动（probability_range 分档、多裁决遍历）。新会话可检查是否有脱节。

### 方向 B：生产入口集成（低优先级，Phase 1 红线禁止）
决策栈目前是旁路，未接入生产入口。这不是问题，`plans/layered-decision-system.md` Phase 1 明确禁止切换。

### 方向 C：新增更复杂的规则校准策略（低优先级）
L9 目前只做 review/freeze；`upgrade/downgrade/deprecate/split/merge` 等策略未实现。等反馈数据积累后再做。

### 方向 D：更多 L1 路由策略（低优先级）
L1 目前使用固定规则，未接入历史命中率反馈。等 L8 归因数据积累后再做。

---

## 4. 下一步计划

建议新会话按以下顺序操作：

### Step 1：读取当前代码状态
优先读取：
- `engine/decision/l5_timing.py`
- `engine/decision/l6_arbitration.py`
- `engine/decision/l7_report_view.py`
- `engine/decision/l8_feedback_attribution.py`
- `engine/decision/l9_calibration.py`
- `engine/decision/v5_adapter.py`
- `tests/test_decision_mvp.py`
- `tests/test_decision_v5_adapter.py`

### Step 2：检查 v5_adapter 同步状态
检查 `v5_adapter.py`：
- `_timings()` 是否用了 `prediction.probability_range` 还是写死的？
- `_report_items()` 是否遍历多个 decisions？
- 如果不对齐，同步改动。

### Step 3：如果有新反馈数据，扩展 L8 关键词映射
L8 归因目前基于关键词 if/elif，扩展成本极低。新反馈数据产生后，在主文件直接加关键词即可。

### Step 4：运行验证
继续使用当前稳定验证子集：

```bash
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/v5/test_v5_output_linter.py tests/v5/test_render_report_v6.py tests/test_production_service.py tests/test_project_metadata.py -q
```

### Step 5：完成后用 verification-before-completion 汇总
包括：改了哪些文件、新增哪个测试、pytest 结果原文、明确未做什么。

---

## 5. 绝对不要再踩的坑

### 5.1 不要重复加载 skill
本会话里后半段出现过多次重复加载 ponytail/geju 的情况。新会话只需要按系统规则做一次 skill applicability check；如果 skill 已在上下文中，不要重复加载。

### 5.2 不要写错完成状态
当前真实状态以这些为准：
- 代码文件实际内容
- 测试文件实际内容
- 最近 pytest 输出 `58 passed, 1 warning`
- 当前 L0-L9 主链路已经稳定

### 5.3 不要把 L5 做成新事件生成器
`plans/layered-decision-system.md` 明确红线：
```text
L5 不改写事件内容
L5 不把事业事件改成婚姻事件
L5 不绕过 L4 直接生成事件
```

### 5.4 不要引入复杂概率模型
当前阶段是"最小证明物"，不是完整应期模型。不要加新模型类、YAML 配置、数据库、新依赖、全局评分器、历史命中率统计器。

### 5.5 不要切默认生产入口
`plans/layered-decision-system.md` Phase 1 明确：不切生产入口、不改旧报告、不删除旧 pipeline。

### 5.6 不要回到"大杂烩融合"
禁止新增：全局综合分、固定流派权重、所有流派强制发言、L6 写"综合来看"、L7 补命理推理、把格局神煞象法应期放进同一个评分表。

### 5.7 不要把旧 warning 当成本轮失败
`engine.application.dual_engine_adapter` 的 deprecation warning 是既有旧兼容问题。只要 pytest exit code 是 0，当前改动不需要处理它。

### 5.8 不要一轮只改 1 个小缺口
同一模块内可明显并列的多条规则，一次补 3-8 个测试 + 1 次实现。RED 只跑相关最小文件，完整验证只在整批结束时跑一次。汇总压缩到 5 行内。

---

## 6. 新会话最小启动指令

新会话开始后建议直接执行：

1. 读取以上 Step 1 文件列表（尤其 v5_adapter.py 是否同步）。
2. 如果 v5_adapter 已滞后，同步 L5/L7 改动。
3. 如果有新反馈数据，扩展 L8 关键词映射。
4. 跑完整验证命令。
5. 汇总完成。

不要重新设计 L0-L9。不要改生产入口。不要新增依赖。
