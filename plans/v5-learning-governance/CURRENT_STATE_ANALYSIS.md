# CURRENT_STATE_ANALYSIS.md · v5.0 Learning Governance 当前状态分析

> 角色：Principal AI Architect  
> 目标：基于 v4.2 审计结论，说明当前系统为什么仍是 Prediction System + Partial Learning Loop，而不是完整 Learning System。  
> 范围：只分析当前学习链路、缺失节点、隐式状态、不可验证与不可回滚环节；不提出新增预测能力。

---

## 1. Thesis

当前系统真正缺的不是预测模块，而是 **Learning Governance Backbone**。

v4.2 已经能预测，也能在局部路径上把反馈转成流派权重变化；但系统还没有把“每次预测”“每条反馈”“每个训练集”“每个权重版本”“每次发布”登记为可审计对象。因此它只能被称为 Partial Learning Loop，不能被称为 Learning System。

---

## 2. Confidence

**Confidence：High。**

原因：

- 生产预测路径已由 [`run_pipeline()`](../../engine/application/pipeline_runner.py:32) 进入 prediction step。
- 当前权重运行态仍由单文件 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 承载。
- 当前预测输出 [`PredictionOutput`](../../engine/domain/prediction.py:116) 只有 `learning_feedback_id`，没有完整 prediction registry metadata。
- 现有 [`SQLiteAnalysisStore`](../../engine/infrastructure/analysis_store.py:81) 只登记 analysis job 与 artifact，不登记 prediction-level learning state。

不确定性：未来实现可能已有未纳入主路径的实验文件；本分析以当前主路径和 v4.2 审计结论为准。

---

## 3. 当前学习链路实际状态

### 3.1 理想链路

```text
Prediction
  → Feedback
  → Dataset
  → Training
  → Candidate Weights
  → Validation
  → Promotion
  → Production Weights
  → Future Prediction
```

### 3.2 当前实际链路

```text
run_pipeline / run_pipeline_e2e
  → build_final_prediction
  → build_prediction_output
  → PredictionOutput.learning_feedback_id
  → feedback files / feedback tools
  → minimal_learning_loop.update_school_weights
  → overwrite engine/expert-weights.yaml
  → fusion_engine_v2.load_school_weights
  → future prediction
```

### 3.3 当前链路逐段判定

| 链路段 | 当前状态 | 证据 | 主要问题 |
|---|---|---|---|
| Prediction | 已成立 | [`run_pipeline()`](../../engine/application/pipeline_runner.py:32) 编排预测层 | 没有独立 Prediction Registry |
| Prediction Metadata | 不完整 | [`PredictionOutput`](../../engine/domain/prediction.py:116) 只有 `learning_feedback_id` | 缺 weights / semantic / calibration version |
| Feedback | 部分成立 | [`tools/feedback_ingest.py`](../../tools/feedback_ingest.py:1)、[`tools/feedback_loop.py`](../../tools/feedback_loop.py:1) 是 active entrypoints | 反馈未强制绑定 prediction_id |
| Learning | 部分成立 | [`update_school_weights()`](../../engine/application/minimal_learning_loop.py:284) 可更新 school weight | 直接从反馈/日志进入学习，没有标准 Dataset 层 |
| State Update | 部分成立 | [`save_expert_weights()`](../../engine/infrastructure/weight_repository.py:28) 写入 YAML | 覆盖式写入，无版本 registry |
| Future Prediction | 部分成立 | [`load_school_weights()`](../../engine/infrastructure/weight_repository.py:35) 读权重 | 隐式读当前文件，无法重放某次预测状态 |

---

## 4. 缺失节点

### 4.1 Prediction Registry

缺失内容：

- `prediction_id`
- `case_id`
- `analysis_id`
- `timestamp`
- `engine_version`
- `weights_version`
- `semantic_version`
- `calibration_version`
- prediction payload digest
- output artifact reference

当前影响：

- 反馈无法可靠绑定到“当时那一次预测”。
- 后续训练无法知道样本来自哪个模型状态。
- 无法回答“这个反馈修正的是哪版权重产生的预测”。

### 4.2 Feedback Registry

缺失内容：

- `feedback_id`
- `prediction_id`
- `actual_outcome`
- `verdict`
- `feedback_source`
- `created_at`
- reviewer / source confidence
- normalized feedback artifact reference

当前影响：

- 反馈可以绑定 case 或 statement，但不强制绑定 prediction。
- 同一 case 多次预测后，反馈归属会变得不可判定。
- 学习样本存在污染风险。

### 4.3 Dataset Builder

缺失内容：

- 标准 `training_set`
- 标准 `validation_set`
- 标准 `test_set`
- dataset version
- dataset manifest
- inclusion / exclusion reason

当前影响：

- 学习可能直接从反馈日志或 case 文件训练。
- 无法复现实验。
- 无法比较两次训练结果。
- 无法阻止训练集与验证集泄漏。

### 4.4 Weight Registry

缺失内容：

- 权重版本目录，例如 `weights/v001.yaml`
- production pointer
- candidate pointer
- archived versions
- diff report
- rollback metadata

当前影响：

- [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 是运行态事实源，但更新方式是覆盖式。
- 权重变化不是不可变版本。
- 回滚依赖人工或 Git，而不是系统级能力。

### 4.5 Weight Promotion Pipeline

缺失内容：

```text
candidate → validation → production
```

当前影响：

- 训练结果可以直接影响未来预测。
- 没有指标门阻止坏权重进入 production。
- 没有 holdout validation 的发布门。

### 4.6 Learning Audit Trail

缺失内容：

- training source
- training time
- dataset version
- algorithm version
- candidate weight version
- validation result
- promotion decision
- rollback result

当前影响：

- 无法把某次生产预测的变差追溯到某次学习发布。
- 无法审计“为什么这版权重被允许上线”。

---

## 5. 隐式状态依赖

### 5.1 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)

当前角色：生产权重事实源。

问题：

- 既是 runtime state，又像配置文件。
- 被 [`load_school_weights()`](../../engine/infrastructure/weight_repository.py:35) 隐式读取。
- 被 [`save_expert_weights()`](../../engine/infrastructure/weight_repository.py:28) 覆盖写入。
- 缺 version pointer 和 immutable history。

### 5.2 [`learning_feedback_id`](../../engine/domain/prediction.py:125)

当前角色：反馈关联 ID。

问题：

- 它不是完整 `prediction_id`。
- 不包含版本上下文。
- 不保证被 Feedback Registry 强制使用。

### 5.3 Analysis Store 只覆盖作业，不覆盖学习

[`SQLiteAnalysisStore`](../../engine/infrastructure/analysis_store.py:81) 已有：

- `analysis_jobs`
- `analysis_artifacts`
- `analysis_cache`

但没有：

- `prediction_registry`
- `feedback_registry`
- `dataset_registry`
- `weight_versions`
- `promotion_runs`

### 5.4 Calibration 参数缺运行态版本

[`ProbabilityCalibrator`](../../engine/application/probability_calibrator.py:66) 被调用，但缺少稳定的 `calibration_version` 事实源。

### 5.5 Event Semantic 配置缺生产绑定

[`event-semantics.yaml`](../../theory/prediction_models/event-semantics.yaml:1) 尚未成为生产预测路径事实源，因此也没有 `semantic_version` 的可审计绑定。

---

## 6. 不可验证环节

### 6.1 无法验证某次反馈是否对应某次预测

没有 `feedback.prediction_id` 强约束时，只能用 `case_id`、`statement_id` 或人工上下文猜测。

### 6.2 无法验证某次训练使用了哪些样本

没有 dataset manifest 时，训练来源是“目录扫描结果”，不是版本化数据集。

### 6.3 无法验证权重提升是否真实

没有固定 validation set 时，无法证明 candidate weights 优于 production weights。

### 6.4 无法验证概率校准是否改善

没有 calibration dataset 与 ECE / Brier score 发布门时，校准参数可能只是形式存在。

### 6.5 无法验证未来预测是否使用了指定版本

如果 production 通过读取当前 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 工作，就无法稳定重放历史预测。

---

## 7. 不可回滚环节

### 7.1 权重不可系统级回滚

当前回滚依赖 Git 或手动恢复 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)。缺少：

- previous production version pointer
- rollback command design
- rollback audit entry
- rollback reason

### 7.2 数据集不可回滚

没有 dataset version，训练输入不可回滚。

### 7.3 校准参数不可回滚

缺少 versioned calibration registry。

### 7.4 语义配置不可回滚到预测时版本

缺少 production prediction 对 semantic version 的记录。

---

## 8. Geju 判断：要删除/停止的错误概念

### 应停止

- 直接从反馈日志训练。
- 直接覆盖 production weight 文件。
- 把 `learning_feedback_id` 当作完整 prediction identity。
- 把 analysis job registry 当作 learning registry。
- 把“工具能跑”当作“学习闭环成立”。

### 应重构为

- Prediction 是一等登记对象。
- Feedback 必须绑定 Prediction。
- Dataset 是训练唯一入口。
- Weight 是不可变版本对象。
- Promotion 是从 candidate 到 production 的受控发布。
- Learning Audit Trail 是所有学习动作的事实源。

---

## 9. First Proof Point

v5.0 的第一个可验证证明不是模型变准，而是：

> 任意一条反馈都能追溯到唯一 `prediction_id`，并能查到该预测当时使用的 `engine_version`、`weights_version`、`semantic_version`、`calibration_version`。

若做不到，系统仍不是 Learning System。

---

## 10. Falsifier

如果后续实现发现：

- 反馈无法稳定绑定 prediction_id；或
- training set 仍直接从反馈日志扫描生成且没有 manifest；或
- production 权重仍覆盖写入单一 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)；或
- candidate weights 不经 validation 即进入 production；

则 v5.0 Learning Governance thesis 失败，系统仍停留在 Partial Learning Loop。
