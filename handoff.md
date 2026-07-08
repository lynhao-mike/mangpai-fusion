# HANDOFF · 分层决策系统重构交接

> 写给完全没有当前会话上下文的新会话。
>
> 当前仓库：`f:/综合盲派/mangpai-fusion`
>
> 当前主任务：使用 ponytail + geju 思路，根据 `plans/layered-decision-system.md` 推进“分层命理决策学习系统”重构。

---

## 1. 我们在做什么任务

目标不是继续补旧的“多派融合报告生成器”，而是按 `plans/layered-decision-system.md` 建立一个可追溯、可反馈、可校准的 L0-L9 分层决策系统。

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

1. **geju 方向**：坚决从“多流派综合评分/大杂烩”转向“司法式分层决策链”。
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
| L5 应期概率 | `engine/decision/l5_timing.py` | 已有基础时间窗和概率输出；下一步正准备增强 probability_range |
| L6 冲突仲裁 | `engine/decision/l6_arbitration.py` | 已支持 winner/coexist/unresolved/reject_all |
| L7 报告表达 | `engine/decision/l7_report_view.py` | 已有只读裁判结果的报告视图项 |
| L8 反馈归因 | `engine/decision/l8_feedback_attribution.py` | 已支持 miss/partial/hit 默认归因，并支持 notes/observed_fact 关键词路由到 L4/L7 |
| L9 校准治理 | `engine/decision/l9_calibration.py` | 已支持 review；同一 affected_object_id 反复 3 次会 freeze |
| 编排器 | `engine/decision/orchestrator.py` | 已有内存 DecisionRun 最小闭环 |
| 核心模型 | `engine/decision/models.py` | 已有 DecisionRun 与 L0-L9 数据模型；validate_trace 已覆盖 L0-L9 链路 |

### 2.2 已完成的重要代码改动

#### L3：结构层有否决权

文件：`engine/decision/l3_structure.py`

已完成：

- `claim.confidence <= 0.1` 时 verdict = `reject`。
- 保持最小启发式，没有引入复杂结构审查策略。

测试：`tests/test_decision_mvp.py`

- 新增 `test_l3_structure_can_reject_very_low_confidence_claim()`。

#### L6：仲裁结果不再只有 winner

文件：`engine/decision/l6_arbitration.py`

已完成：

- 单事件：`winner`
- 多事件置信度接近：`coexist`
- 多事件差距较大但未全低：`unresolved`
- 全部极低置信：`reject_all`

测试：`tests/test_decision_mvp.py`

- 新增 `test_l6_arbitration_supports_non_winner_results()`。

#### L9：反复失验对象可 freeze

文件：`engine/decision/l9_calibration.py`

已完成：

- 默认治理动作仍是 `review`。
- 同一 `affected_object_id` 出现 3 条需要人工复核的归因时，动作升级为 `freeze`。

测试：`tests/test_decision_v5_adapter.py`

- 新增 `test_l9_freezes_repeated_review_target()`。

#### DecisionRun：链路校验覆盖 L8/L9

文件：`engine/decision/models.py`

已完成：

- `DecisionRun.validate_trace()` 不只检查 L0-L7，也检查：
  - L8 `FeedbackSignal.report_item_id` 是否绑定 L7 `ReportViewItem.report_item_id`
  - L8 `FeedbackAttribution.feedback_id` 是否绑定 feedback signal
  - L9 `CalibrationAction.evidence_feedback_ids` 是否绑定 feedback signal

测试：`tests/test_decision_mvp.py`

- 新增 `test_decision_run_validate_trace_checks_l8_l9_links()`。

#### L8：反馈 notes/observed_fact 可归因到 L4/L7

文件：`engine/decision/l8_feedback_attribution.py`

已完成：

- 出现 `事件类型` 或 `类型错`：归因 L4 事件落地层。
- 出现 `表达` 或 `太绝对`：归因 L7 报告表达层。
- 原有 miss/partial/hit 逻辑保留。

测试：`tests/test_decision_v5_adapter.py`

- 新增 `test_l8_notes_can_route_to_l4_or_l7()`。

### 2.3 最近一次完整验证结果

最近执行命令：

```bash
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/v5/test_v5_output_linter.py tests/v5/test_render_report_v6.py tests/test_production_service.py tests/test_project_metadata.py -q
```

结果：

```text
40 passed, 1 warning in 59.07s
```

warning 是既有问题：

```text
engine/application/pipeline_runner.py:10: DeprecationWarning: engine.application.dual_engine_adapter is deprecated.
```

这不是本轮重构引入的问题。

---

## 3. 当前卡在哪

当前 todo 停在：**L5 概率区间验收**。

现有提醒列表：

```text
[-] 复核下一计划缺口：L5 概率区间验收
[ ] 最小实现 L5 概率区间随事件置信度派生
[ ] 补充最小测试
[ ] 运行计划验证命令
[ ] verification-before-completion 复核并汇总
```

也就是说，下一轮不要再从 L0/L1/L3/L6/L8/L9 重来；直接看 `engine/decision/l5_timing.py` 和相关测试。

需要检查：

1. `TimingProbability.probability_range` 当前是否只是固定值。
2. 如果固定，需要按 `EventHypothesis.confidence` 派生最小概率区间。
3. 不要让 L5 改写事件内容；L5 只回答时间窗、触发条件、概率区间。

---

## 4. 下一步计划

### Step 1：读 L5 当前实现

优先读取：

- `engine/decision/l5_timing.py`
- `engine/decision/models.py` 中 `TimingProbability` 与 `EventHypothesis`
- `tests/test_decision_mvp.py`

### Step 2：最小实现 probability_range 派生

建议 ponytail 最小规则：

```text
confidence < 0.3  -> "10%-30%"
confidence < 0.6  -> "30%-60%"
else              -> "60%-80%"
```

或根据当前字段风格选择最少改动版本。

注意：

- 不新增配置文件。
- 不新增概率模型类。
- 不新增全局综合评分。
- 不用历史命中率，除非已有现成字段直接可用。

### Step 3：补一个最小测试

在 `tests/test_decision_mvp.py` 或现有 L5 相关测试里加一个测试即可：

- 构造 2-3 个不同 confidence 的 `EventHypothesis`
- 调 `build_timing_probabilities()`
- 断言 `probability_range` 随 confidence 分档变化

### Step 4：跑验证命令

继续使用最近稳定的验证子集：

```bash
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/v5/test_v5_output_linter.py tests/v5/test_render_report_v6.py tests/test_production_service.py tests/test_project_metadata.py -q
```

如果只想先快跑，可先跑：

```bash
python -m pytest tests/test_decision_mvp.py -q
```

但最终完成前必须跑完整子集。

### Step 5：完成后汇总

完成后用 verification-before-completion 原则汇总：

- 改了哪些文件
- 新增哪个测试
- pytest 结果原文
- 明确未做什么

---

## 5. 绝对不要再踩的坑

### 5.1 不要重复加载 skill

本会话里后半段出现过多次重复加载 ponytail/geju 的情况，浪费上下文。新会话只需要按系统规则做一次 skill applicability check；如果 skill 已在上下文中，不要重复加载。

### 5.2 不要写错完成状态

有一次 `attempt_completion` 被中断后，后续继续了任务。新会话必须以文件和测试为准，不要相信上一条自然语言总结已经完整落地。

当前真实状态以这些为准：

- 代码文件实际内容
- 测试文件实际内容
- 最近 pytest 输出 `40 passed, 1 warning`
- 当前 todo 停在 L5 probability_range

### 5.3 不要把 L5 做成新事件生成器

`plans/layered-decision-system.md` 明确红线：

```text
L5 不改写事件内容
L5 不把事业事件改成婚姻事件
L5 不绕过 L4 直接生成事件
```

所以 L5 下一步只改 probability_range，不碰 event_type/concrete_event/landing_path。

### 5.4 不要引入复杂概率模型

当前阶段是“最小证明物”，不是完整应期模型。不要加：

- 新模型类
- 新 YAML 配置
- 新数据库
- 新依赖
- 全局评分器
- 历史命中率统计器

如果需要历史命中率，以后再做。现在只要能证明 L5 概率区间不是固定死值即可。

### 5.5 不要切默认生产入口

`plans/layered-decision-system.md` Phase 1 明确：不切生产入口、不改旧报告、不删除旧 pipeline。

当前决策栈应继续作为旁路/ledger/artifact 存在，不要把 `engine/pipeline.py` 或 `engine/application/pipeline_runner.py` 直接改成强制走 decision stack。

### 5.6 不要回到“大杂烩融合”

禁止新增以下东西：

- 全局综合分
- 固定流派权重
- 所有流派强制发言
- L6 写“综合来看”
- L7 补命理推理
- 把格局、神煞、象法、应期放进同一个评分表

这正是本轮重构要杀掉的旧模型。

### 5.7 不要把旧 warning 当成本轮失败

`engine.application.dual_engine_adapter` 的 deprecation warning 是既有旧兼容问题。只要 pytest exit code 是 0，当前 L5 改动不需要处理它。

---

## 6. 新会话最小启动指令

新会话开始后建议直接执行：

1. 读 `engine/decision/l5_timing.py`
2. 读 `tests/test_decision_mvp.py`
3. 最小改 L5 probability_range 分档
4. 补一个测试
5. 跑完整验证命令
6. 汇总完成

不要重新设计 L0-L9。不要改生产入口。不要新增依赖。
