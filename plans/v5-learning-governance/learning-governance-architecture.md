# learning-governance-architecture.md · v5.0 Learning Governance Layer

> 目标：把 mangpai-fusion 从 Prediction System 升级为 Learning System。  
> 原则：不增强预测能力，不新增流派，不新增神煞，不新增规则；只建立学习治理层。  
> 核心命题：学习系统的最小充分条件不是“能更新权重”，而是“每次学习状态变化都可追溯、可验证、可回滚、可发布”。

---

## 1. Thesis

v5.0 应建立独立的 **Learning Governance Layer**，作为 prediction pipeline 与 learning pipeline 之间的治理边界。

它不负责断命、不负责新增预测逻辑；它只回答六个问题：

1. 哪一次预测产生了什么输出？
2. 哪一条反馈对应哪一次预测？
3. 哪些反馈被纳入了哪个训练数据集？
4. 训练产生了哪个 candidate weight version？
5. candidate 是否通过 validation？
6. 哪个版本被 promotion 到 production，并可如何回滚？

---

## 2. Non-negotiable Principles

### 2.1 Prediction First-class

每次预测必须登记为一等对象。不能只依赖 [`AnalysisJobRecord`](../../engine/infrastructure/analysis_store.py:39)，因为 analysis job 不等于 prediction event。

### 2.2 Feedback Must Bind Prediction

所有可学习反馈必须绑定 `prediction_id`。不能只绑定 `case_id`、`statement_id` 或报告路径。

### 2.3 Dataset Is the Only Training Input

训练不能直接从反馈日志、case 目录或 JSONL 扫描结果开始。训练必须从版本化 dataset manifest 开始。

### 2.4 Weights Are Immutable Versions

禁止把 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 当作可覆盖的生产事实源。权重必须成为不可变版本对象。

### 2.5 Promotion Is a Gate, Not a Copy

candidate weights 不能直接进入 production。必须经过 validation gate。

### 2.6 Audit Trail Is Mandatory

每次训练、验证、发布、回滚都必须有 audit entry。

---

## 3. High-level Architecture

```text
Production Prediction Pipeline
  ├─ run_pipeline / run_pipeline_e2e
  ├─ build_final_prediction
  ├─ build_prediction_output
  └─ Prediction Registry  ← records every prediction + model state versions

Feedback Intake Pipeline
  ├─ feedback_ingest / feedback_loop / batch_review
  └─ Feedback Registry    ← feedback must bind prediction_id

Learning Governance Pipeline
  ├─ Dataset Builder      ← creates training/validation/test datasets
  ├─ Training Runner      ← produces candidate weights/calibration params
  ├─ Weight Registry      ← immutable versioned state
  ├─ Promotion Pipeline   ← candidate → validation → production
  └─ Learning Audit Trail ← all decisions and results

Future Prediction
  └─ Production Version Resolver
       ├─ weights_version
       ├─ semantic_version
       └─ calibration_version
```

---

## 4. Component 1：Prediction Registry

### 4.1 职责

Prediction Registry 记录每一次生产预测，是学习闭环的源头。

它不是报告存档，不是 case 目录，不是 analysis job cache。它是“某一模型状态对某一输入产生某一预测”的不可变登记。

### 4.2 必需字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `prediction_id` | string | 是 | 全局唯一预测 ID |
| `case_id` | string | 是 | 关联 case |
| `analysis_id` | string | 是 | 关联 [`AnalysisJobRecord.analysis_id`](../../engine/infrastructure/analysis_store.py:43) |
| `timestamp` | ISO datetime | 是 | 预测完成时间 |
| `engine_version` | string | 是 | 来自 [`engine.__version__`](../../engine/__init__.py:1) |
| `weights_version` | string | 是 | 本次预测使用的 production weights version |
| `semantic_version` | string | 是 | 本次预测使用的 event semantics version |
| `calibration_version` | string | 是 | 本次预测使用的 calibration params version |
| `input_sha256` | string | 是 | 输入摘要 |
| `prediction_sha256` | string | 是 | 预测输出摘要 |
| `prediction_artifact_path` | string | 否 | 预测 JSON / report artifact |
| `status` | enum | 是 | `created` / `completed` / `invalidated` |

### 4.3 推荐扩展字段

| 字段 | 说明 |
|---|---|
| `model_state_bundle_id` | 将 weights / semantics / calibration 聚合成一个运行态版本包 |
| `domain_hint` | 本次预测主要领域 |
| `event_count` | 候选事件数量 |
| `time_window_digest` | 时间窗摘要 |
| `confidence_score` | 输出总置信度 |
| `created_by` | pipeline / batch / manual |

### 4.4 状态机

```text
created
  → completed
  → invalidated
```

说明：

- `created`：预测开始登记。
- `completed`：预测输出与版本信息完整。
- `invalidated`：发现输入、版本或输出不可用于学习。

### 4.5 与现有系统关系

- 可复用 [`SQLiteAnalysisStore`](../../engine/infrastructure/analysis_store.py:81) 的 SQLite 基础设施，但不应混入 `analysis_jobs` 表。
- 应新增独立 `prediction_registry` 概念。
- [`PredictionOutput.learning_feedback_id`](../../engine/domain/prediction.py:125) 应降级为 legacy alias 或迁移为 `prediction_id`。

---

## 5. Component 2：Feedback Registry

### 5.1 职责

Feedback Registry 是所有可学习反馈的唯一入口。任何反馈若没有绑定 `prediction_id`，只能作为人工参考，不能进入训练集。

### 5.2 必需字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `feedback_id` | string | 是 | 全局唯一反馈 ID |
| `prediction_id` | string | 是 | 必须引用 Prediction Registry |
| `actual_outcome` | string / object | 是 | 实际结果，可结构化 |
| `verdict` | enum | 是 | `y` / `n` / `partial` / `skip` |
| `feedback_source` | enum/string | 是 | user / analyst / batch_review / historical |
| `created_at` | ISO datetime | 是 | 反馈创建时间 |

### 5.3 推荐扩展字段

| 字段 | 说明 |
|---|---|
| `case_id` | 冗余索引，必须与 prediction record 一致 |
| `reviewer_id` | 人工审核者 |
| `source_confidence` | 反馈来源可信度 |
| `normalized_payload` | 标准化反馈内容 |
| `raw_feedback_path` | 原始反馈文件 |
| `normalization_version` | 标准化规则版本 |
| `learning_eligibility` | eligible / excluded |
| `exclusion_reason` | 不进入学习的原因 |

### 5.4 学习准入规则

反馈进入 Dataset Builder 前必须满足：

1. `prediction_id` 存在且可解析。
2. 对应 prediction status 是 `completed`。
3. verdict 在允许集合内。
4. actual outcome 足够结构化。
5. prediction 使用的版本上下文完整。
6. 未被标记为 duplicate / ambiguous / contaminated。

### 5.5 与现有系统关系

- 现有 [`normalize_feedback_entry()`](../../engine/application/minimal_learning_loop.py:38) 可作为历史反馈标准化参考。
- 现有 active feedback entrypoints：[`feedback_ingest.py`](../../tools/feedback_ingest.py:1)、[`feedback_loop.py`](../../tools/feedback_loop.py:1)、[`batch_review.py`](../../tools/batch_review.py:1) 应在 v5.0 迁移后写入 Feedback Registry。
- 没有 `prediction_id` 的历史反馈应进入 `legacy_unbound_feedback`，不可直接训练。

---

## 6. Component 3：Dataset Builder

### 6.1 职责

Dataset Builder 将 Prediction Registry 与 Feedback Registry join 后，生成版本化标准数据集。

**禁止直接从反馈日志训练。**

### 6.2 数据集类型

```text
datasets/
  training_set/
  validation_set/
  test_set/
```

### 6.3 Dataset Manifest 字段

| 字段 | 说明 |
|---|---|
| `dataset_id` | 数据集 ID |
| `dataset_version` | 版本号 |
| `created_at` | 创建时间 |
| `source_prediction_query` | prediction 选择条件 |
| `source_feedback_query` | feedback 选择条件 |
| `split_strategy` | train / validation / test 切分策略 |
| `train_count` | 训练样本数 |
| `validation_count` | 验证样本数 |
| `test_count` | 测试样本数 |
| `excluded_count` | 排除样本数 |
| `exclusion_summary` | 排除原因汇总 |
| `schema_version` | dataset schema |
| `sha256` | manifest 摘要 |

### 6.4 样本字段

| 字段 | 说明 |
|---|---|
| `sample_id` | 样本 ID |
| `prediction_id` | 预测 ID |
| `feedback_id` | 反馈 ID |
| `case_id` | case |
| `domain` | 领域 |
| `event_candidate` | 事件候选 |
| `raw_probability` | 原始概率 |
| `calibrated_probability` | 校准概率 |
| `time_window` | 应期窗口 |
| `weights_version` | 预测时权重版本 |
| `semantic_version` | 预测时语义版本 |
| `calibration_version` | 预测时校准版本 |
| `actual_outcome` | 实际结果 |
| `verdict` | y / n / partial / skip |

### 6.5 Split 原则

- 同一 `case_id` 不应跨 train / validation / test 泄漏。
- 同一 `prediction_id` 不应出现在多个 split。
- validation/test 必须冻结，不能随训练自动漂移。
- historical feedback 必须标记来源，不能与 live feedback 混同。

---

## 7. Component 4：Weight Registry

### 7.1 职责

Weight Registry 版本化管理所有权重，替代覆盖式 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)。

### 7.2 禁止事项

- 禁止直接覆盖 production weight。
- 禁止没有版本号的权重进入 prediction runtime。
- 禁止 candidate 权重绕过 validation。
- 禁止只有 Git 历史、没有系统内 registry。

### 7.3 设计目录

```text
learning/weights/
  registry.yaml
  production.yaml
  versions/
    v001.yaml
    v002.yaml
    v003.yaml
  candidates/
    cand-20260620-001.yaml
  diffs/
    v001-to-v002.md
  rollbacks/
    rollback-20260620-001.md
```

### 7.4 Version 文件字段

| 字段 | 说明 |
|---|---|
| `weights_version` | 例如 `weights/v001` |
| `status` | candidate / validated / production / archived / rolled_back |
| `created_at` | 创建时间 |
| `created_by` | training job |
| `source_dataset_id` | 来源数据集 |
| `algorithm_version` | 学习算法版本 |
| `base_weights_version` | 基准版本 |
| `weights` | 分领域流派权重 |
| `constraints` | 权重约束 |
| `validation_result_id` | 验证结果 |
| `promotion_id` | 发布记录 |
| `sha256` | 文件摘要 |

### 7.5 Production Pointer

`production.yaml` 只允许保存指针，不保存权重正文：

```yaml
active_weights_version: weights/v003
activated_at: '2026-06-20T00:00:00Z'
activated_by: promotion-run-20260620-001
previous_weights_version: weights/v002
rollback_allowed: true
```

### 7.6 回滚要求

回滚不是复制旧文件，而是更新 production pointer，并写 audit entry。

---

## 8. Component 5：Weight Promotion Pipeline

### 8.1 职责

把训练结果从 candidate 安全推进到 production。

```text
candidate → validation → production
```

### 8.2 Candidate Stage

输入：

- dataset version
- base weights version
- algorithm version
- training config

输出：

- candidate weights version
- training report
- diff against base

禁止：candidate 直接被 runtime 读取。

### 8.3 Validation Stage

验证指标至少包含：

- hit rate
- domain-level hit rate
- Brier score
- Expected Calibration Error
- max per-domain weight delta
- regression count
- sample coverage

通过门示例：

| Gate | 最低要求 |
|---|---|
| validation sample count | 不低于预设阈值 |
| overall hit rate | 不低于 production baseline |
| domain regression | 关键领域不得显著下降 |
| max weight delta | 不超过约束 |
| calibration error | 不得恶化 |

### 8.4 Production Stage

只有 validation 通过后：

1. candidate 标记为 `validated`。
2. 写入 promotion record。
3. 更新 production pointer。
4. 生成 audit trail。
5. 下次预测通过 resolver 读取新 production version。

### 8.5 Rejection Stage

validation 未通过时：

- candidate 保留为 rejected。
- 不更新 production pointer。
- 保存失败原因。
- 可生成 next-training recommendation，但不能自动上线。

---

## 9. Component 6：Learning Audit Trail

### 9.1 职责

Learning Audit Trail 是所有学习行为的不可变历史。

### 9.2 必须记录

用户要求的五项必须记录：

1. 训练来源。
2. 训练时间。
3. 训练数据集。
4. 验证结果。
5. 发布结果。

### 9.3 Audit Event 类型

| Event | 说明 |
|---|---|
| `prediction_registered` | 预测登记完成 |
| `feedback_registered` | 反馈登记完成 |
| `dataset_built` | 数据集生成 |
| `training_started` | 训练开始 |
| `training_completed` | 训练完成 |
| `candidate_created` | candidate 权重生成 |
| `validation_completed` | 验证完成 |
| `promotion_approved` | 发布批准 |
| `promotion_rejected` | 发布拒绝 |
| `production_activated` | production pointer 切换 |
| `rollback_completed` | 回滚完成 |

### 9.4 Audit Event 字段

| 字段 | 说明 |
|---|---|
| `audit_id` | 审计事件 ID |
| `event_type` | 事件类型 |
| `timestamp` | 时间 |
| `actor` | pipeline / user / reviewer |
| `entity_type` | prediction / feedback / dataset / weight / promotion |
| `entity_id` | 实体 ID |
| `before_state` | 变更前摘要 |
| `after_state` | 变更后摘要 |
| `reason` | 变更原因 |
| `artifact_paths` | 相关文件 |
| `sha256` | 审计事件摘要 |

---

## 10. Version Resolver

### 10.1 职责

Prediction runtime 不应直接读取 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)。它应通过 Version Resolver 获取当前 production model state bundle。

### 10.2 Model State Bundle

```yaml
model_state_bundle_id: msb-20260620-001
engine_version: 1.3.1
weights_version: weights/v003
semantic_version: semantics/v002
calibration_version: calibration/v004
activated_at: '2026-06-20T00:00:00Z'
source_promotion_id: promotion-run-20260620-001
```

### 10.3 好处

- 每次预测可记录完整版本上下文。
- 历史预测可重放。
- 反馈可归因到准确模型状态。
- 学习效果可按版本比较。

---

## 11. Clean Architecture 边界

### Domain Layer

只定义治理概念：

- `PredictionRecord`
- `FeedbackRecord`
- `DatasetManifest`
- `WeightVersion`
- `PromotionRun`
- `LearningAuditEvent`

不得依赖 SQLite、YAML、文件路径实现。

### Application Layer

定义用例：

- `register_prediction`
- `register_feedback`
- `build_dataset`
- `create_candidate_weights`
- `validate_candidate_weights`
- `promote_weights`
- `rollback_weights`
- `resolve_production_state`

### Infrastructure Layer

实现存储：

- SQLite registry store
- YAML weight version store
- artifact writer
- digest calculator

### Tools Layer

命令入口：

- dataset build CLI
- validation CLI
- promotion CLI
- rollback CLI
- audit report CLI

---

## 12. Options

| Option | 描述 | 优点 | 缺点 | Verdict |
|---|---|---|---|---|
| Conservative path | 在现有 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 上追加 version 字段 | 改动小 | 仍是单文件覆盖，治理弱 | 不推荐 |
| Clean target | 建立完整 registry + immutable weight versions + promotion gate | 架构正确，可审计可回滚 | 初始迁移成本高 | 推荐目标 |
| Staged clean path | 先 registry，再 dataset，再 weight governance，再 promotion | 风险可控，能逐步证明 | 需要纪律，不能半途停在兼容层 | 推荐实施路径 |

---

## 13. What Not To Do

- 不要新增预测规则来掩盖学习治理不足。
- 不要把 [`learning_feedback_id`](../../engine/domain/prediction.py:125) 继续扩展成万能字段。
- 不要让训练工具继续扫描 `cases/` 并直接更新生产权重。
- 不要用 Git 历史替代 Weight Registry。
- 不要让 validation report 只是文档；它必须决定 promotion 是否通过。
- 不要为了兼容旧流程保留两条可写 production weight 路径。

---

## 14. First Proof Point

最小证明：

1. 一次 prediction 生成 `prediction_id`。
2. Prediction Registry 记录 `weights_version`、`semantic_version`、`calibration_version`。
3. 一条 feedback 必须绑定该 `prediction_id`。
4. Dataset Builder 生成一个 dataset manifest。
5. Training 产生 candidate weight。
6. Validation 未通过时 production pointer 不变。

做到这 6 点，系统开始从 Prediction System 进入 Learning System。

---

## 15. Falsifier

如果 v5.0 实施后仍存在以下任一情况，则架构目标失败：

- 反馈不绑定 `prediction_id` 也能进入训练。
- 训练可以绕过 dataset manifest。
- candidate weights 可以绕过 validation 进入 production。
- production runtime 仍直接读取并依赖可覆盖的 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)。
- 无法从一次预测追溯到当时使用的 weights / semantics / calibration 版本。

---

## 16. Final Architecture Judgment

v5.0 Learning Governance Layer 的本质是：

> 把学习从“文件副作用”升级为“受治理的版本状态机”。

它不解决“怎么断得更准”的问题；它解决“系统如何知道自己为什么变准或变差，并且能安全地发布或回滚”的问题。
