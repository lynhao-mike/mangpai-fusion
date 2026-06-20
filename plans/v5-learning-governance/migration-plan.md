# migration-plan.md · v5.0 Learning Governance 迁移方案

> 目标：将当前 Prediction System + Partial Learning Loop 迁移为 Learning System。  
> 约束：不新增预测功能，不新增流派，不新增神煞，不新增规则；只迁移学习治理结构。  
> 推荐路径：Staged Clean Path，而不是保守补丁或一次性大爆炸重构。

---

## 1. Thesis

v5.0 迁移不能从“改训练算法”开始，必须从“登记事实源”开始。

原因：当前系统最大风险不是模型不会更新，而是更新无法证明、无法复现、无法验证、无法回滚。迁移顺序必须是：

```text
Registry Layer
  → Dataset Layer
  → Weight Governance
  → Learning Release Pipeline
```

---

## 2. Migration Principles

### 2.1 不破坏现有预测

[`run_pipeline()`](../../engine/application/pipeline_runner.py:32)、[`run_pipeline_e2e()`](../../engine/application/pipeline_runner.py:170) 现有预测路径必须继续可用。

### 2.2 先旁路登记，后切换事实源

第一阶段只记录 prediction / feedback，不改变预测结果。

### 2.3 先生成 candidate，不直写 production

任何迁移后的学习输出都先进入 candidate 区，不直接覆盖 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)。

### 2.4 历史数据先标记，不强行清洗成真相

历史 [`cases/`](../../cases/) 与 [`META/`](../../META/) 中的数据可导入 registry，但必须保留来源、置信度与 eligibility。

### 2.5 每阶段有可证伪验收

每个 phase 都必须有明确 falsifier，防止“文档完成但系统未治理”。

---

## 3. Phase 1：Registry Layer

### 3.1 目标

建立 Prediction Registry 与 Feedback Registry，让每次预测与每条反馈成为可追溯对象。

### 3.2 范围

新增治理概念：

- Prediction Registry
- Feedback Registry
- Learning Audit Trail 初版

不做：

- 不训练新权重。
- 不改变 [`build_final_prediction()`](../../engine/application/fusion_engine_v2.py:60) 的预测逻辑。
- 不替换 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)。

### 3.3 设计任务

#### 3.3.1 Prediction Registry 设计

字段必须包含：

- `prediction_id`
- `case_id`
- `analysis_id`
- `timestamp`
- `engine_version`
- `weights_version`
- `semantic_version`
- `calibration_version`

补充字段：

- `input_sha256`
- `prediction_sha256`
- `prediction_artifact_path`
- `status`

#### 3.3.2 Feedback Registry 设计

字段必须包含：

- `feedback_id`
- `prediction_id`
- `actual_outcome`
- `verdict`
- `feedback_source`
- `created_at`

#### 3.3.3 与现有系统接合点

| 当前组件 | Phase 1 接合方式 |
|---|---|
| [`ProductionAnalysisService`](../../engine/application/production_service.py:52) | 可在 submit 完成后登记 prediction |
| [`SQLiteAnalysisStore`](../../engine/infrastructure/analysis_store.py:81) | 复用 SQLite 风格，不混用表职责 |
| [`PredictionOutput`](../../engine/domain/prediction.py:116) | `learning_feedback_id` 迁移为 legacy alias |
| [`feedback_ingest.py`](../../tools/feedback_ingest.py:1) | 输出 feedback record |
| [`feedback_loop.py`](../../tools/feedback_loop.py:1) | 输出 feedback record |

### 3.4 迁移历史数据

历史数据分类：

| 数据来源 | 处理方式 |
|---|---|
| 已有 analysis job | 可生成 `analysis_id` 关联记录 |
| 已有 report artifact | 作为 prediction artifact source |
| `cases/*/feedback.md` | 导入为 feedback source artifact |
| `prediction_feedback.jsonl` | 若无 prediction_id，标记 legacy_unbound |

### 3.5 验收标准

- 新预测可生成唯一 `prediction_id`。
- 新反馈必须绑定 `prediction_id`。
- Registry 可查询：给定 `feedback_id` 找到 `prediction_id`、`case_id`、`weights_version`。
- 无 `prediction_id` 的反馈不能进入 learning eligible 集合。

### 3.6 Falsifier

如果 Phase 1 完成后，反馈仍可不绑定 prediction 而进入学习，则 Phase 1 失败。

---

## 4. Phase 2：Dataset Layer

### 4.1 目标

建立标准 Dataset Builder，禁止训练直接读取反馈日志或 case 目录。

### 4.2 范围

新增：

- `training_set`
- `validation_set`
- `test_set`
- dataset manifest
- sample eligibility policy

不做：

- 不改变权重上线方式。
- 不自动提升生产权重。

### 4.3 设计任务

#### 4.3.1 Dataset Builder 输入

只允许输入：

- Prediction Registry records
- Feedback Registry records
- eligibility policy
- split policy

禁止输入：

- 原始 `feedback.md`。
- 原始 `prediction_feedback.jsonl`。
- 直接扫描 [`cases/`](../../cases/)。

#### 4.3.2 Dataset Manifest

每个 dataset 必须生成：

- `manifest.yaml`
- `samples.jsonl`
- `excluded.jsonl`
- `sha256`

#### 4.3.3 Split 策略

默认策略：

```text
case-level split
  → train 70%
  → validation 20%
  → test 10%
```

约束：

- 同一 `case_id` 不跨 split。
- 同一 `prediction_id` 不跨 split。
- historical feedback 与 live feedback 标记来源。

### 4.4 历史数据处理

| 类别 | 是否可入 dataset | 条件 |
|---|---:|---|
| 新 registry-bound feedback | 是 | prediction_id 完整 |
| legacy feedback with reconstructed prediction | 条件允许 | reconstruction confidence 达标 |
| legacy unbound feedback | 否 | 只能进入 reference pool |
| ambiguous feedback | 否 | 进入 excluded.jsonl |

### 4.5 验收标准

- Dataset Builder 可生成 training / validation / test 三类 dataset。
- 每个 dataset 有 manifest 与样本摘要。
- 每个样本都能追溯到 `prediction_id` 与 `feedback_id`。
- 训练工具不能绕过 dataset manifest。

### 4.6 Falsifier

如果训练仍能直接从 feedback logs 扫描并更新权重，则 Phase 2 失败。

---

## 5. Phase 3：Weight Governance

### 5.1 目标

将权重从可覆盖文件迁移为版本化、可对比、可回滚的治理对象。

### 5.2 范围

新增：

- Weight Registry
- immutable weight versions
- production pointer
- candidate directory
- diff report
- rollback record

### 5.3 当前状态迁移

当前 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 内容迁移为：

```text
learning/weights/versions/v001.yaml
```

并生成：

```text
learning/weights/production.yaml
```

内容示例：

```yaml
active_weights_version: weights/v001
activated_at: '<migration timestamp>'
activated_by: migration-phase-3
previous_weights_version: null
rollback_allowed: false
```

### 5.4 运行态切换策略

#### Stage A：Dual Read

- runtime 仍可读取 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)。
- governance resolver 同时读取 `learning/weights/production.yaml`。
- 两者做一致性校验。

#### Stage B：Governance Read

- runtime 通过 model state resolver 读取 production pointer。
- [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 变为 legacy export。

#### Stage C：Legacy Write 禁止

- [`save_expert_weights()`](../../engine/infrastructure/weight_repository.py:28) 不再直接覆盖 production 事实源。
- 所有更新必须进入 candidate version。

### 5.5 Weight Version 字段

必须包含：

- `weights_version`
- `status`
- `created_at`
- `created_by`
- `source_dataset_id`
- `algorithm_version`
- `base_weights_version`
- `weights`
- `constraints`
- `validation_result_id`
- `promotion_id`
- `sha256`

### 5.6 验收标准

- 可列出所有 weight versions。
- 可对比任意两个 weight versions。
- 可回滚 production pointer。
- candidate 权重不会被 prediction runtime 读取。
- [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 不再是唯一 production truth。

### 5.7 Falsifier

如果权重更新仍通过覆盖 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 完成，Phase 3 失败。

---

## 6. Phase 4：Learning Release Pipeline

### 6.1 目标

建立 candidate → validation → production 的学习发布管线。

### 6.2 范围

新增：

- Candidate training run
- Validation report
- Promotion decision
- Production activation
- Rollback process
- Release audit trail

### 6.3 Pipeline 状态机

```text
candidate_created
  → validation_running
  → validation_passed
  → promotion_approved
  → production_activated
```

失败路径：

```text
candidate_created
  → validation_running
  → validation_failed
  → promotion_rejected
  → archived
```

回滚路径：

```text
production_activated
  → rollback_requested
  → rollback_validated
  → rollback_completed
```

### 6.4 Validation Gates

最低 gates：

| Gate | 说明 |
|---|---|
| sample count gate | 验证集样本量足够 |
| overall quality gate | 总体命中率不低于 baseline |
| domain regression gate | 任一关键领域不能明显退化 |
| calibration gate | Brier / ECE 不恶化 |
| weight delta gate | 单轮权重变化不超过约束 |
| reproducibility gate | 同 dataset + config 可复现 candidate |
| audit completeness gate | audit trail 完整 |

### 6.5 发布结果

Promotion 结果必须是以下之一：

- `approved_and_activated`
- `approved_pending_manual_activation`
- `rejected_validation_failed`
- `rejected_audit_incomplete`
- `rolled_back`

### 6.6 与现有 [`batch_rl_backtest.py`](../../tools/batch_rl_backtest.py:1) 的关系

v5.0 后：

- [`batch_rl_backtest.py`](../../tools/batch_rl_backtest.py:1) 不再允许直接影响 production。
- 它只能产出 candidate training report。
- candidate 必须进入 Weight Registry。
- validation 通过后才能 promotion。

### 6.7 验收标准

- 可以创建 candidate weight version。
- 可以对 candidate 执行 validation。
- validation failed 时 production pointer 不变。
- validation passed 时 promotion 生成完整 audit trail。
- 可以执行 rollback 并追溯原因。

### 6.8 Falsifier

如果 candidate weights 可以绕过 validation 进入 production，Phase 4 失败。

---

## 7. Cross-phase Dependencies

| Phase | 依赖 | 产物 |
|---|---|---|
| Phase 1 | 当前 prediction / feedback entrypoints | Prediction + Feedback Registry |
| Phase 2 | Phase 1 registry | Versioned datasets |
| Phase 3 | Phase 2 dataset versioning | Weight Registry + production pointer |
| Phase 4 | Phase 3 weight versions | Promotion Pipeline + audit trail |

---

## 8. Compatibility Strategy

### 8.1 必须保留的兼容

- 当前报告生成与 case 归档流程。
- 当前 [`tools/feedback_ingest.py`](../../tools/feedback_ingest.py:1) 入口，但输出路径需 registry-aware。
- 当前 [`engine/expert-weights.yaml`](../../engine/expert-weights.yaml:1) 在过渡期可作为 legacy export。

### 8.2 不应保留的兼容

- 训练直接覆盖 production weight。
- 反馈无 prediction_id 仍进入学习。
- 直接扫描 [`cases/`](../../cases/) 构建训练样本。
- 多个文件各自声称是 production weight truth。

---

## 9. Migration Risks

| 风险 | 影响 | 缓解 |
|---|---|---|
| 历史反馈缺 prediction_id | 学习样本减少 | legacy reconstruction + eligibility 标记 |
| 权重事实源双轨 | 预测结果不一致 | dual-read consistency check |
| validation 样本不足 | 无法发布新权重 | 允许 candidate 生成但禁止 promotion |
| 工具绕过治理层 | 形成新隐式状态 | 工具 registry check + 文档禁令 |
| 迁移期目录混乱 | 事实源漂移 | `learning/` 作为唯一运行态学习资产根 |

---

## 10. Go / No-Go Gates

### Phase 1 Go Gate

- 至少一条新预测可登记。
- 至少一条新反馈绑定 prediction_id。

### Phase 2 Go Gate

- 可生成 dataset manifest。
- dataset sample 100% 可追溯 prediction + feedback。

### Phase 3 Go Gate

- [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 可迁移为 `v001`。
- production pointer 可解析为 active weight version。

### Phase 4 Go Gate

- candidate 不能直接上线。
- validation failed 可阻止 promotion。
- promotion / rollback 都有 audit entry。

---

## 11. Final Migration Judgment

推荐采用 **Staged Clean Path**：

1. 先让系统看见自己每次预测和反馈。
2. 再让训练只能使用标准 dataset。
3. 再把权重从可覆盖文件变成不可变版本。
4. 最后用 validation / promotion 决定未来预测能否使用新状态。

这条路径比直接增强 [`batch_rl_backtest.py`](../../tools/batch_rl_backtest.py:1) 慢，但它是从 Partial Learning Loop 进入 Learning System 的必要代价。
