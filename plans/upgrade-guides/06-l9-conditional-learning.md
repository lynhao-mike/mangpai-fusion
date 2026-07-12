# 升级指导 06 · L9 条件化学习与校准治理

> 文档类型：单模块详细实施指导（供强模型独立执行）
> 服从：[`docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md`](../../docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md) §4.10、§8
> 上游依赖：[`04-l1-learnable-routing.md`](04-l1-learnable-routing.md)（能力后验回流通道）、[`03-evaluation-data-foundation.md`](03-evaluation-data-foundation.md)（反馈观察与任务标签）
> 定位：整个升级飞轮的“学习引擎”——把反馈转成条件化知识，而不是全局拧螺丝
> 前置阅读：[`00-overview-and-sequencing.md`](00-overview-and-sequencing.md)

---

## 1. 目标与非目标

### 1.1 一句话目标

把当前 [`update_confidence()`](../../engine/application/minimal_learning_loop.py) 的**全局线性 alpha/beta 微调**，升级为**条件化学习**：学习信号能更新“在某类命局结构下、某派某类命题的可信度”，并按 N_eff 分级治理决定该信号能否影响生产决策。

### 1.2 必须达成

1. 反馈归因（L8）产出的 `LearningSignal` 能挂载到六维条件身份，而非仅 rule_id / family_id。
2. 学习更新分级：低样本只记录、中样本调适用性后验、成熟样本才动规则先验，高风险领域无论样本量都需人工审批。
3. 所有生产权重更新可追溯、可复现、可回滚；历史运行快照不可被学习改写。
4. 条件化学习的产物直接喂给 [`04`](04-l1-learnable-routing.md) 的 L1 能力后验事实源，形成闭环。

### 1.3 明确非目标

- 不做在线学习服务 / 实时梯度更新（宪法 §12 第一推进单元排除项精神延续）。
- 不引入神经网络或不可解释的黑箱学习器；本层必须保持可审计。
- 不替换 [`engine/evaluation/`](../../engine/evaluation/) 盲测评估框架——本层消费它的产物，不重造它。

---

## 2. as-built 现状（2026-07-12 审计）

| 项 | 现状 | 问题 |
|---|---|---|
| 学习入口 | [`update_confidence()`](../../engine/application/minimal_learning_loop.py) rule/family 两级 | 只有全局线性加减 |
| 参数 | `ALPHA_RULE=0.05` / `BETA_RULE=0.10` 等固定常量 | 无条件、无 N_eff 分级 |
| 归因 | statement→rule→family 映射链存在 | 未挂命局原型 / 任务 / 命题类型六维身份 |
| 治理 | 无分级门禁 | 小样本可直接漂移规则置信度 |
| 回流 | 断开 | 学习结果没有喂给 L1 路由 |

**核心缺陷**：现有学习改的是“规则权重”，学不到“这类结构下这派更可信”的**条件化**知识。这正是宪法 §3.7、§6.2 要求的能力张量的更新引擎缺失。

---

## 3. 接口契约

### 3.1 输入：条件化学习信号

```text
ConditionalLearningSignal
  signal_id
  feedback_observation_id      # 来自 L8 / 03 文档的 FeedbackObservation
  claim_id
  school_id
  rule_id
  task_id
  chart_prototype_id           # 来自 01 文档命局特征向量派生的原型
  claim_type
  time_horizon
  evidence_completeness_band
  verdict                      # hit / miss / partial / no_data
  time_error                   # 时间窗任务的偏差，可空
  feedback_quality             # 来自标签质量分级
  attributable                 # bool，是否能明确归因；false 则不得分摊
```

**硬约束**：`attributable=false` 时禁止把信号平均分摊给所有参与规则（宪法 §4.9 边界、路线 §9.2）。必须标记 `no_data` 或进入人工审查。

### 3.2 输出：分级学习决策

```text
LearningDecision
  target_identity              # 六维条件身份
  update_tier                  # record_only / adjust_applicability / adjust_rule_prior / manual_review
  proposed_delta               # 建议更新量（不一定执行）
  applied                      # bool，是否真正写入生产事实源
  n_eff_before / n_eff_after
  requires_human_approval      # bool
  snapshot_ref                 # 版本冻结引用
  rationale
```

### 3.3 N_eff 分级治理（路线 §9.3）

| 分级 | N_eff 条件 | 允许动作 |
|---|---|---|
| 低样本 | N_eff < 中样本阈值 | 仅记录信号 + 可信区间，不动任何生产决策 |
| 中样本 | 达到中样本阈值 | 可小幅调适用性后验（喂 L1），不改核心规则 |
| 成熟样本 | 达到成熟阈值 | 可调规则先验 + 生产路由，需版本冻结 + 人工复核 |
| 高风险领域 | 任意 N_eff | 重大权重变化一律人工审批 |

具体阈值不在本文写死，由 [`03`](03-evaluation-data-foundation.md) 的真实数据分布在 Phase 2 后确定（路线 §9.3 明确“具体阈值由数据分布确定”）。实现时把阈值放入配置事实源，不得硬编码进执行器。

---

## 4. 任务分解

### T1：条件化学习信号建模
- 在 [`engine/evaluation/models.py`](../../engine/evaluation/models.py) 或新模块定义 `ConditionalLearningSignal` frozen dataclass。
- 复用 01 文档的 `chart_prototype_id`、03 文档的 `FeedbackObservation`。
- 严格校验六维身份非空；`attributable=false` 时禁止携带 proposed_delta。

### T2：归因升级（L8 挂六维身份）
- 扩展现有 statement→rule→family 归因链，追加命局原型 / 任务 / 命题类型 / 时间尺度 / 证据完整度。
- 无法归因时明确产出 `no_data`，不分摊。

### T3：N_eff 分级治理引擎
- 实现纯函数 `decide_learning_tier(signal, current_posterior, thresholds, is_high_risk) -> LearningDecision`。
- 高风险任务集合复用 [`05`](05-l6-staged-arbitration.md) / task catalog 的 high_risk 标记，保持单一事实源。
- 阈值从配置读入，禁止硬编码。

### T4：版本冻结与回滚
- 每次生产权重更新写快照：更新前后 posterior、N_eff、信号来源、时间。
- 历史运行快照只读，学习不得改写（宪法 §8.5、路线 §11.3）。
- 提供回滚路径：任一更新可按 snapshot_ref 撤销。

### T5：回流对接 L1
- 中样本及以上的 `adjust_applicability` 决策写入 [`04`](04-l1-learnable-routing.md) 定义的 school capability registry 事实源。
- 严禁把易变统计塞回 [`engine/expert-weights.yaml`](../../engine/expert-weights.yaml) 或 [`engine/domain-weights.yaml`](../../engine/domain-weights.yaml)（宪法 §11、路线 §14.3）。

### T6：人工裁决队列
- 满足路线 §8.4 条件（反馈矛盾 / 无法归因 / 样本漂移 / 跨领域影响 / 大幅权重变化 / 疑似泄漏）时进入人工队列。
- 队列产物可追溯到 [`META/arbitration-log.md`](../../META/arbitration-log.md) 语义。

---

## 5. 验收标准

### 5.1 规格符合（对照宪法）
- [ ] 学习信号挂六维条件身份，非仅 rule/family（§6.2）
- [ ] `attributable=false` 不分摊（§4.9）
- [ ] N_eff 分级门禁生效，小样本不改核心规则（§8.5 / §4.10 边界）
- [ ] 高风险领域任意样本量均需人工审批（§8.3）
- [ ] 生产更新可追溯、可复现、可回滚（§8.5）
- [ ] 历史运行快照不可被学习改写
- [ ] 学习产物写入独立 capability registry，不塞回静态权重文件（§11）

### 5.2 行为测试（必须覆盖）
- 低样本信号 → `record_only`，生产决策零变化
- 中样本信号 → `adjust_applicability`，写入 L1 registry，不动规则
- 成熟样本信号 → `adjust_rule_prior`，但 `requires_human_approval=true` 且未批准前 `applied=false`
- 高风险任务 + 大 N_eff → 仍需人工审批
- `attributable=false` → 不产生 proposed_delta，不分摊
- 回滚：应用一次更新后按 snapshot_ref 撤销，posterior 回到更新前值
- 历史快照只读：学习流程运行后，历史运行快照字节不变

### 5.3 TDD 要求
- 严格 RED → GREEN；分级门禁与回滚的每条路径都要有失败先行测试。
- 阈值用测试专用配置注入，不依赖生产阈值。

---

## 6. 风险与红线

| 风险 | red flag | 处理 |
|---|---|---|
| 小样本污染生产 | 低 N_eff 直接改规则 | 分级门禁硬拦截 |
| 分摊噪声 | 无法归因仍平均分配 | `no_data` 标记，进人工 |
| 静态权重回灌 | 统计塞回 expert-weights.yaml | 独立 registry，CI 检查禁止路径 |
| 历史改写 | 学习修改旧快照 | 快照只读 + 字节校验测试 |
| 高风险放水 | 灾病领域自动调权 | 无条件人工审批 |
| 阈值硬编码 | 常量写进执行器 | 配置事实源 + 审查 |

---

## 7. 与其他指导文档的边界

- **消费** [`03`](03-evaluation-data-foundation.md) 的 FeedbackObservation 与任务标签、[`01`](01-chart-feature-vector.md) 的命局原型。
- **喂给** [`04`](04-l1-learnable-routing.md) 的能力后验事实源，闭合学习飞轮。
- **不重造** [`engine/evaluation/`](../../engine/evaluation/) 盲测评分——本层是“学”，评估框架是“考”。
- **不触碰** 生产入口切换（那是路线 Phase 5）。

---

## 8. 完成定义

本指导视为完成，当且仅当：

1. 条件化学习信号 + 分级治理 + 版本冻结/回滚全部实现并测试通过；
2. 学习产物能回流 L1 registry 并被路由消费；
3. 高风险与人工裁决红线经测试锁死；
4. 历史快照只读性经字节校验；
5. 全程无静态权重文件回灌、无小样本改核心规则。

达成后，L1 ⇄ L9 ⇄ 评估框架三者构成的学习飞轮首次完整闭环——这是“系统越来越懂什么八字用什么法”的机器实现。
