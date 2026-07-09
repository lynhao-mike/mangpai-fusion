# HANDOFF · 分层决策系统重构交接（2026-07-09 更新）

> 写给完全没有当前会话上下文的新会话。
>
> 当前仓库：`f:/综合盲派/mangpai-fusion`
>
> 当前主任务：使用 ponytail + geju 思路，根据 `plans/layered-decision-system.md` 推进"分层命理决策学习系统"重构。阶段目标：L0-L9 主链路稳定、链路校验完整、脏数据鲁棒。
>
> 当前产品版本：1.3.1（[`VERSION`](VERSION)），项目阶段：`v1.4-schema-and-reporting-convergence-plus-production-rules`（[`META/project-state.json`](META/project-state.json)），这与产品版本不同，不要混淆。

---

## 1. 我们在做什么任务

目标不是继续补旧的"多派融合报告生成器"，而是按 [`plans/layered-decision-system.md`](plans/layered-decision-system.md) 建立一个可追溯、可反馈、可校准的 **L0-L9 分层决策系统**。

核心方向：

```text
事实准确 → 流派选对 → 命题独立 → 结构有审查 → 事件可验证
→ 应期可证伪 → 冲突可裁决 → 报告不失真 → 反馈可归因 → 策略可淘汰
```

当前采取的落地策略：

1. **geju 方向**：坚决从"多流派综合评分/大杂烩"转向"司法式分层决策链"。
2. **ponytail 实施**：每轮只补最短闭环，不上复杂抽象、不新增依赖、不切默认生产入口。
3. **验收标准**：每次改动必须有最小测试（TDD Red-Green），跑指定 pytest 子集，不准凭感觉说完成。

---

## 2. 已经完成了什么

### 2.1 已建立/推进的核心模块

当前已有 `engine/decision/` 分层决策栈，主要模块如下：

| 层级 | 文件 | 当前状态 |
|---|---|---|
| L0 输入事实 | [`engine/decision/l0_wenzhen.py`](engine/decision/l0_wenzhen.py)、[`engine/decision/l0_context.py`](engine/decision/l0_context.py) | 解析问真文本、记录缺失字段、保留未知区块、上下文文本 strip；空值与 `_` 一致按缺失处理 |
| L1 流派路由 | [`engine/decision/l1_school_router.py`](engine/decision/l1_school_router.py) | rule-based 路由，支持 lead/co_lead/evidence_only/abstain；支持健康同义词；四柱不完整时非 abstain 降级为 evidence_only |
| L2 独立命题 | [`engine/decision/l2_claims.py`](engine/decision/l2_claims.py) | SchoolClaim 最小生成；evidence_only 角色降级；未知 school 跳过 |
| L3 结构审查 | [`engine/decision/l3_structure.py`](engine/decision/l3_structure.py) | pass/weaken/reject/unknown；reject 保留原始置信度 |
| L4 事件落地 | [`engine/decision/l4_events.py`](engine/decision/l4_events.py) | 只落地通过/削弱结构 verdict 且同领域的 event claim；支持"总体"结构回退 |
| L5 应期概率 | [`engine/decision/l5_timing.py`](engine/decision/l5_timing.py) | 概率按置信度三档分箱；空 event_id 不生成 timing |
| L6 冲突仲裁 | [`engine/decision/l6_arbitration.py`](engine/decision/l6_arbitration.py) | winner/coexist/unresolved/reject_all；按 domain 分组；空 domain 事件跳过 |
| L7 报告表达 | [`engine/decision/l7_report_view.py`](engine/decision/l7_report_view.py) | 只读裁判结果；遍历多个 winner/rejected 事件；reject_all 使用 rejected_ids；空 competing decision 跳过 |
| L8 反馈归因 | [`engine/decision/l8_feedback_attribution.py`](engine/decision/l8_feedback_attribution.py) | 关键词 if/elif 归因到 L0-L7；空 report_item_id 不生成 signal；skipped 留在 L8 |
| L9 校准治理 | [`engine/decision/l9_calibration.py`](engine/decision/l9_calibration.py) | review/freeze；同 target reason 合并；evidence_feedback_ids 稳定排序；空 target_id 跳过 |
| 编排器 | [`engine/decision/orchestrator.py`](engine/decision/orchestrator.py) | 内存 DecisionRun 最小闭环 |
| 核心模型 | [`engine/decision/models.py`](engine/decision/models.py) | DecisionRun + L0-L9 数据模型；`validate_trace()` 覆盖 L0-L9 全部非空/存在性/语义/范围校验 |
| v5 迁移桥 | [`engine/decision/v5_adapter.py`](engine/decision/v5_adapter.py) | V5Output → DecisionRun 映射；过滤空 school/claim_id/prediction_id/domain；空 case_id fallback；四柱缺失字段记录 |

### 2.2 本轮会话完成的核心改动（2026-07-09 批次）

本轮进行了约 **8 个批次、50+ 个验收/实现** 的增量迭代。以下是按批次汇总：

| 批次 | 涉及模块 | 内容 |
|---|---|---|
| 1 | v5_adapter, L8 | adapter 同步验收 + L8 新增关键词 + 多裁决报告项映射 |
| 2 | L7 | coexist 裁决每个 winner 各自绑定 L5 timing 反馈点 |
| 3 | models | validate_trace 校验 L6 结果 ID 与 L7 timing 归属 |
| 4 | v5_adapter | winner_ids 全部保留 competing events；report_items 遍历所有 event |
| 5 | L4 | 无 pass/weaken verdict 的 event claim 不落事件 |
| 6 | v5_adapter | 无 claim 来源时 adapter 不崩溃、不生成 orphan event |
| 7 | models, L9, L8 | validate_trace 全链路语义校验（L6 结果子集、L5 概率范围、L8/L9 归因治理语义） |
| 8 | L1, L2, L3, L4, L5, L6 | 批量 7 项：四柱降级、健康同义词、未知 school 跳过、reject 置信度、同领域结构、空 event_id/domain 跳过 |
| 9 | models, v5_adapter | 批次 6 项：validate_trace 必填 ID/domain、v5 adapter 脏数据过滤 |
| 10 | L7, L8, L9 | 批次 6 项：reject_all 使用 rejected_ids、空 report_item_id 跳过、sort evidence_feedback_ids、reason 合并 |
| 11 | L0 | 空值按缺失、缺失 section 补子字段、context strip、captured_at 锁住 |
| 12 | models, v5_adapter, L9 | 批次 6 项：run_id/case_id/schema_version 校验、L9 action_id/target_id、to_dict 键集合、case_id fallback、四柱缺失记录 |

### 2.3 最近一次完整验证结果

```bash
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q
```

结果：

```text
68 passed, 1 warning in 10.12s
```

完整验证命令（含 v5 相关测试，耗时较长）：

```bash
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/v5/test_v5_output_linter.py tests/v5/test_render_report_v6.py tests/test_production_service.py tests/test_project_metadata.py -q
```

结果：

```text
96 passed, 1 warning in 82.48s (0:01:22)
```

warning 是既有问题：

```text
engine/application/pipeline_runner.py:10: DeprecationWarning: engine.application.dual_engine_adapter is deprecated.
```

这不是本轮重构引入的问题。

---

## 3. 当前卡在哪

L0-L9 决策栈主链路已经稳定，**链路校验层（validate_trace）覆盖了全层语义**。当前没有明显的"卡点"。

剩余可继续的方向（按优先级排序）：

### 方向 A：v5 adapter 下一步同步（中优先级）
`engine/decision/v5_adapter.py` 本轮的主要同步已完成（概率区间、多裁决、脏数据过滤），但以下可继续：
- `_report_items()` 与主链路 [`build_report_items()`](engine/decision/l7_report_view.py:15) 共享 `reject_all` 使用 `rejected_ids` 的行为——当前 adapter 的 `_decisions()` 不生成 `reject_all` 结果。
- L8/L9 管线对接：当前 adapter 的 `_feedback_signals` / `_calibration_actions` 由通用 `build_feedback_attributions` / `build_calibration_actions` 完成，已验证通过。

### 方向 B：生产入口集成（低优先级，Phase 1 红线禁止）
决策栈目前是旁路，未接入生产入口。`[plans/layered-decision-system.md` Phase 1 明确禁止切换。

### 方向 C：新增更复杂的规则校准策略（低优先级）
L9 目前只做 review/freeze；`upgrade/downgrade/deprecate/split/merge` 等策略未实现。等反馈数据积累后再做。

### 方向 D：更多 L1 路由策略（低优先级）
L1 目前使用固定规则，未接入历史命中率反馈。等 L8 归因数据积累后再做。

---

## 4. 下一步计划

建议新会话按以下顺序操作：

### Step 1：读取当前代码状态

优先读取以下文件，这是事实源，不要从旧 handoff 推断：

- [`engine/decision/models.py`](engine/decision/models.py)（核心数据契约与 `validate_trace`）
- [`engine/decision/l7_report_view.py`](engine/decision/l7_report_view.py)（L7 报告层）
- [`engine/decision/l8_feedback_attribution.py`](engine/decision/l8_feedback_attribution.py)（L8 归因）
- [`engine/decision/l9_calibration.py`](engine/decision/l9_calibration.py)（L9 治理）
- [`engine/decision/v5_adapter.py`](engine/decision/v5_adapter.py)（迁移桥）
- [`tests/test_decision_mvp.py`](tests/test_decision_mvp.py)（决策栈测试——当前 45 个测试）
- [`tests/test_decision_v5_adapter.py`](tests/test_decision_v5_adapter.py)（adapter 测试——当前 23 个测试）
- [`AGENTS.md`](AGENTS.md)（仓库规则入口）

### Step 2：检查 validate_trace 的通告

当前 [`validate_trace()`](engine/decision/models.py:320) 已有 30+ 条校验。如果未来新增 L0 字段或 L1-L9 struct 字段，应先补 `validate_trace` 校验 + 测试，再补生成逻辑。

### Step 3：如果有新反馈数据，扩展 L8 关键词映射

L8 归因目前基于关键词 if/elif，扩展成本极低。新反馈数据产生后，在 [`engine/decision/l8_feedback_attribution.py`](engine/decision/l8_feedback_attribution.py:25) 直接加关键词即可。当前支持：

| 关键词 | 归因层 |
|---|---|
| 输入矛盾/事实矛盾/补充事实/事实录入错 | L0 |
| 流派选错/流派不适用/主审连续失验/主审失验 | L1 |
| 原命题/命题弱/命题不成立 | L2 |
| 结构基础/结构弱/结构不成立/结构审查 | L3 |
| 事件类型/类型错/事件落点错 | L4 |
| 年份偏差/月份偏差/时间偏差/时间窗错/应期 | L5 |
| 两派冲突/选错一方/仲裁选错 | L6 |
| 表达/太绝对/只是倾向/实际只是倾向/报告失真/措辞过满 | L7 |

### Step 4：运行验证

继续使用当前稳定验证子集：

```bash
# 快速验证（决策栈相关 68 个测试）
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q

# 完整验证（含 v5 兼容层，96 个测试，~80s）
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/v5/test_v5_output_linter.py tests/v5/test_render_report_v6.py tests/test_production_service.py tests/test_project_metadata.py -q
```

### Step 5：完成后用 verification-before-completion 汇总

包括：改了哪些文件、新增哪个测试、pytest 结果原文、明确未做什么。**没有验证输出不得声称完成**。

---

## 5. 绝对不要再踩的坑

### 5.1 不要重复加载 skill
新会话只需要按系统规则做一次 skill applicability check；如果 skill 已在上下文中，不要重复加载。

### 5.2 不要写错完成状态
当前真实状态以这些为准：
- 代码文件实际内容
- 测试文件实际内容
- 最近 pytest 输出 `68 passed, 1 warning`（决策栈）/ `96 passed, 1 warning`（完整）
- 当前 L0-L9 主链路已稳定，`validate_trace` 已覆盖全链路

### 5.3 不要把 L5 做成新事件生成器
[`plans/layered-decision-system.md`](plans/layered-decision-system.md) 明确红线：
```text
L5 不改写事件内容
L5 不把事业事件改成婚姻事件
L5 不绕过 L4 直接生成事件
```

### 5.4 不要引入复杂概率模型
当前阶段是"最小证明物"，不是完整应期模型。不要加新模型类、YAML 配置、数据库、新依赖、全局评分器、历史命中率统计器。

### 5.5 不要切默认生产入口
[`plans/layered-decision-system.md`](plans/layered-decision-system.md) Phase 1 明确：不切生产入口、不改旧报告、不删除旧 pipeline。

### 5.6 不要回到"大杂烩融合"
禁止新增：全局综合分、固定流派权重、所有流派强制发言、L6 写"综合来看"、L7 补命理推理、把格局神煞象法应期放进同一个评分表。

### 5.7 不要把旧 warning 当成本轮失败
`engine.application.dual_engine_adapter` 的 deprecation warning 是既有旧兼容问题。只要 pytest exit code 是 0，当前改动不需要处理它。

### 5.8 不要一轮只改 1 个小缺口
同一模块内可明显并列的多条规则，一次补 3-8 个测试 + 1 次实现。RED 只跑相关最小文件，完整验证只在整批结束时跑一次。汇总压缩到 5 行内。

### 5.9 不要跳过 TDD Red-Green 循环
任何改动必须先写测试、确认失败、再实现、确认通过。测试立刻通过的说明测试没锁住正确行为。

### 5.10 不要假设旧 HANDOFF 状态准确
不要从计划文件或历史会话记录推断代码状态。唯一事实源是文件系统中的当前代码文件和测试输出。

### 5.11 ponytail 对重复加载的容忍
同一个会话中 ponytail/geju/brainstorming 等 skill 只应加载一次。不要在每个工具调用前重复加载。

---

## 6. 新会话最小启动指令

新会话开始后建议直接执行：

1. 读取上面 Step 1 文件列表（以原文为准）。
2. 运行快速验证命令确认基线：`python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q`。
3. 识别下一个最小缺口：检查 `validate_trace` 覆盖了哪些校验、哪些生成策略还有未锁住的行为。
4. 按 TDD 模式：写测试（RED）→ 最小实现（GREEN）→ 运行相关文件 → 完整验证。
5. 本文件只保留短期下一步，一旦产生实质性代码改动，覆盖本文件作为新 handoff。

--- 

**更新时间**：2026-07-09  
**最近验证**：96 passed, 1 warning in 82.48s
