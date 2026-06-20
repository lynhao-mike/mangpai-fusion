# implementation-roadmap.md · v5.0 Learning Governance 实施路线图

> 目标：把设计落成可执行路线，但本文件不包含代码实现。  
> 约束：不新增预测能力，不新增流派，不新增神煞，不新增规则。  
> 最终目标：从 Prediction System 升级为 Learning System。

---

## 1. Thesis

v5.0 的实施重点不是“让系统更会预测”，而是“让系统知道自己在用哪个学习状态预测，并且能安全改变这个状态”。

路线图必须优先交付：

1. Registry。
2. Dataset。
3. Versioned Weight State。
4. Validation / Promotion。
5. Audit / Rollback。

---

## 2. High-格局 Direction

当前系统已经有预测能力，也有局部权重学习能力。v5.0 不应继续把能力堆在 [`batch_rl_backtest.py`](../../tools/batch_rl_backtest.py:1) 或 [`minimal_learning_loop.py`](../../engine/application/minimal_learning_loop.py:1) 里。

v5.0 应建立一个新边界：

```text
Prediction Runtime
  ↔ Learning Governance Layer
  ↔ Learning Runtime Assets
```

其中：

- Prediction Runtime 只消费 production model state bundle。
- Learning Governance Layer 负责登记、构建数据集、验证、发布、回滚。
- Learning Runtime Assets 保存 registry、dataset、weight versions、promotion records、audit trail。

---

## 3. Implementation Roadmap Overview

| Milestone | 名称 | 目标 | 是否改变预测输出 |
|---|---|---|---:|
| M0 | Architecture Freeze | 固化 v5.0 契约与目录 | 否 |
| M1 | Registry MVP | prediction / feedback 可登记 | 否 |
| M2 | Dataset MVP | 标准 dataset 可生成 | 否 |
| M3 | Weight Registry MVP | 权重可版本化 | 否 / 只读验证 |
| M4 | Promotion MVP | candidate 经验证后发布 | 是，但受控 |
| M5 | Audit & Rollback | 全链路审计与回滚 | 是，但可恢复 |
| M6 | Learning System Gate | 按指标确认升级 | 否 |

---

## 4. M0：Architecture Freeze

### 4.1 目标

确认 v5.0 不解决预测增强，只解决学习治理。

### 4.2 产物

- [`CURRENT_STATE_ANALYSIS.md`](CURRENT_STATE_ANALYSIS.md)
- [`learning-governance-architecture.md`](learning-governance-architecture.md)
- [`proposed-directory-layout.md`](proposed-directory-layout.md)
- [`migration-plan.md`](migration-plan.md)
- [`success-metrics.md`](success-metrics.md)
- [`implementation-roadmap.md`](implementation-roadmap.md)

### 4.3 决策

采用 Staged Clean Path：

```text
Registry → Dataset → Weight Governance → Release Pipeline
```

### 4.4 完成标准

- 设计文档齐备。
- 明确禁止：直接从反馈日志训练、直接覆盖 production weight、candidate 绕过 validation。

---

## 5. M1：Registry MVP

### 5.1 目标

让系统能登记每次预测与每条反馈。

### 5.2 关键设计

新增 registry 概念：

- Prediction Registry。
- Feedback Registry。
- Learning Audit Trail 初版。

### 5.3 接入点

| 当前组件 | 接入动作 |
|---|---|
| [`run_pipeline_e2e()`](../../engine/application/pipeline_runner.py:170) | 预测完成后登记 prediction |
| [`ProductionAnalysisService`](../../engine/application/production_service.py:52) | 使用 `analysis_id` 关联 prediction |
| [`PredictionOutput`](../../engine/domain/prediction.py:116) | 输出 `prediction_id` 或保持 `learning_feedback_id` legacy alias |
| [`feedback_ingest.py`](../../tools/feedback_ingest.py:1) | 写 Feedback Registry |
| [`feedback_loop.py`](../../tools/feedback_loop.py:1) | 写 Feedback Registry |

### 5.4 最小字段

Prediction：

- `prediction_id`
- `case_id`
- `analysis_id`
- `timestamp`
- `engine_version`
- `weights_version`
- `semantic_version`
- `calibration_version`

Feedback：

- `feedback_id`
- `prediction_id`
- `actual_outcome`
- `verdict`
- `feedback_source`
- `created_at`

### 5.5 验收

- 新预测 registry coverage ≥ 99%。
- 新反馈 prediction-bound rate ≥ 95%。
- 无 `prediction_id` 的反馈不能标记为 learning eligible。

---

## 6. M2：Dataset MVP

### 6.1 目标

禁止训练直接读取反馈日志；所有训练通过版本化 dataset。

### 6.2 关键设计

新增：

```text
learning/datasets/
  training_set/
  validation_set/
  test_set/
```

每个 dataset 包含：

- `manifest.yaml`
- `samples.jsonl`
- `excluded.jsonl`

### 6.3 输入

只允许从以下来源生成 dataset：

- Prediction Registry。
- Feedback Registry。
- Eligibility Policy。
- Split Policy。

### 6.4 验收

- Dataset-mediated Training Rate = 100%。
- Sample Traceability = 100%。
- Split Contamination Rate = 0%。

### 6.5 关键禁令

[`batch_rl_backtest.py`](../../tools/batch_rl_backtest.py:1) 不再允许直接扫描 [`cases/`](../../cases/) 并写 production 权重。

---

## 7. M3：Weight Registry MVP

### 7.1 目标

把 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 从可覆盖运行态文件迁移为初始版本。

### 7.2 初始迁移

```text
engine/expert-weights.yaml
  → learning/weights/versions/v001.yaml
```

新增：

```text
learning/weights/production.yaml
```

### 7.3 运行模式

阶段 A：Dual Read。

- 当前 runtime 仍可读 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)。
- resolver 同时读 `learning/weights/production.yaml`。
- 两者一致性校验。

阶段 B：Governance Read。

- runtime 通过 resolver 读 active weight version。
- [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 变成 legacy export。

### 7.4 验收

- Versioned Weight Usage ≥ 99%。
- Direct Overwrite Count = 0。
- Weight Diff Coverage = 100%。
- Rollback Readiness = 100%。

---

## 8. M4：Promotion MVP

### 8.1 目标

建立 candidate → validation → production 的发布门。

### 8.2 状态流

```text
candidate_created
  → validation_running
  → validation_passed
  → promotion_approved
  → production_activated
```

失败流：

```text
candidate_created
  → validation_running
  → validation_failed
  → promotion_rejected
```

### 8.3 Validation Gates

至少包含：

- sample count gate。
- overall hit rate gate。
- domain regression gate。
- Brier / ECE gate。
- max weight delta gate。
- audit completeness gate。

### 8.4 验收

- Validation-before-Promotion = 100%。
- Failed Candidate Block Rate = 100%。
- Promotion Audit Completeness = 100%。

---

## 9. M5：Audit & Rollback

### 9.1 目标

学习状态变化可追溯、可审计、可回滚。

### 9.2 Audit Events

必须记录：

- `prediction_registered`
- `feedback_registered`
- `dataset_built`
- `training_started`
- `training_completed`
- `candidate_created`
- `validation_completed`
- `promotion_approved`
- `promotion_rejected`
- `production_activated`
- `rollback_completed`

### 9.3 Rollback 要求

回滚应更新 production pointer，而不是复制旧 YAML。

### 9.4 验收

- Audit Event Coverage = 100%。
- Promotion 可串起 dataset → candidate → validation → activation。
- Rollback dry-run success ≥ 99%。

---

## 10. M6：Learning System Gate

### 10.1 目标

根据 [`success-metrics.md`](success-metrics.md) 判断系统是否从 Prediction System 升级为 Learning System。

### 10.2 最低通过标准

- Prediction Registry Coverage ≥ 99%。
- Prediction-bound Feedback Rate ≥ 95%。
- Dataset-mediated Training Rate = 100%。
- Validation-before-Promotion = 100%。
- Direct Overwrite Count = 0。
- Promotion Audit Completeness = 100%。
- Rollback dry-run 可成功执行。

### 10.3 评分目标

Learning System Readiness Score ≥ 85。

---

## 11. Work Breakdown by Layer

### 11.1 Domain Layer

设计对象：

- `PredictionRecord`
- `FeedbackRecord`
- `DatasetManifest`
- `WeightVersion`
- `PromotionRun`
- `LearningAuditEvent`
- `ModelStateBundle`

### 11.2 Application Layer

设计用例：

- `register_prediction`
- `register_feedback`
- `build_dataset`
- `train_candidate`
- `validate_candidate`
- `promote_weights`
- `rollback_weights`
- `resolve_model_state`

### 11.3 Infrastructure Layer

设计实现：

- SQLite registry store。
- YAML weight version store。
- Dataset artifact store。
- Audit log store。
- Digest utilities。

### 11.4 Tools Layer

设计入口：

- `learning_registry.py`
- `learning_dataset.py`
- `learning_validate.py`
- `learning_promote.py`
- `learning_rollback.py`
- `learning_audit_report.py`

---

## 12. Recommended Sequencing

### Sprint 1：Registry Contracts

- 定义 registry schema。
- 定义 audit event schema。
- 定义 prediction_id 生成策略。

### Sprint 2：Registry Storage

- 建 SQLite registry。
- 写 prediction / feedback record。
- 导出 JSONL 审计副本。

### Sprint 3：Dataset Builder

- registry join。
- eligibility policy。
- split policy。
- manifest + samples + excluded。

### Sprint 4：Weight Version Store

- 迁移 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 为 v001。
- 建 production pointer。
- 建 diff report。

### Sprint 5：Validation Pipeline

- candidate 训练输出治理化。
- validation metrics。
- promotion decision。

### Sprint 6：Runtime Resolver

- runtime 解析 model state bundle。
- Prediction Registry 记录 production versions。
- legacy path 进入只读导出。

### Sprint 7：Rollback & Audit

- rollback pointer。
- audit trail completeness。
- learning governance report。

---

## 13. What Not To Build in v5.0

- 不新增预测事件类型。
- 不新增神煞。
- 不新增流派。
- 不新增盲派规则。
- 不优化 Bayesian fusion 公式。
- 不把 event semantics 接入生产预测作为 v5.0 核心目标；v5.0 只要求它有 `semantic_version` 可治理。
- 不把 calibration 预测效果优化作为 v5.0 核心目标；v5.0 只要求 calibration params 可版本化、可验证、可发布。

---

## 14. Final Judgment：升级到 Learning System 后还差什么

v5.0 完成后，系统可以从：

```text
Prediction System
```

升级为：

```text
Learning System
```

前提是：

- Prediction Registry 成立。
- Feedback Registry 成立。
- Dataset Builder 成立。
- Weight Registry 成立。
- Promotion Pipeline 成立。
- Learning Audit Trail 成立。

但即使如此，它仍不是：

```text
Self-Evolving Decision System
```

要进入 Self-Evolving Decision System，还需要以下条件：

### 14.1 自动漂移检测

系统能自动识别：

- 领域反馈分布变化。
- 事件命中率漂移。
- 概率校准漂移。
- 权重效果退化。

### 14.2 自动策略比较

系统能同时维护多个 candidate 策略，并在 shadow / validation / canary 中比较。

### 14.3 Shadow Evaluation

新 candidate 在不影响 production 的情况下，对新预测进行影子评估。

### 14.4 Canary Promotion

通过 validation 的版本先进入小流量或限定领域 canary，而不是全量 production。

### 14.5 Safe Auto Rollback

production 指标恶化时，系统能自动触发 rollback request，或在明确策略允许时自动回滚。

### 14.6 Human Approval Policy

定义哪些学习发布可以自动，哪些必须由命理师 / 架构负责人批准。

---

## 15. Roadmap Verdict

推荐执行路线：**Staged Clean Path**。

不推荐 Conservative path，因为它会继续让 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 承担过多职责。

不推荐 Big Bang Clean target，因为当前生产预测与报告流程已经可用，没必要一次性破坏。

v5.0 的第一证明点应是：

> 给定任意一条新反馈，可以追溯到唯一 prediction、唯一 model state bundle、唯一 dataset inclusion decision，并证明它是否有资格影响未来 production 权重。

做到这一点，系统才真正从“会预测”走向“会学习”。
