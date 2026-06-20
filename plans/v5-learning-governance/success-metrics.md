# success-metrics.md · v5.0 Learning Governance 成功标准

> 目标：定义 v5.0 Learning Governance System 的可量化成功标准。  
> 原则：成功标准必须验证系统是否成为 Learning System，而不是验证预测功能是否变多。  
> 覆盖维度：Prediction Traceability、Feedback Coverage、Learning Coverage、Calibration Coverage、Weight Governance Coverage。

---

## 1. Thesis

v5.0 成功的标志不是“预测命中率立刻提高”，而是：

> 每一次学习影响未来预测之前，都能证明它来自哪些预测、哪些反馈、哪个数据集、哪次训练、哪次验证、哪次发布，并且可以回滚。

---

## 2. Metric Framework

### 2.1 指标分层

```text
Governance Readiness Metrics
  → Traceability Metrics
  → Coverage Metrics
  → Validation Metrics
  → Release Safety Metrics
  → Learning Outcome Metrics
```

### 2.2 阶段性判断

| 系统等级 | 判定标准 |
|---|---|
| Prediction System | 能输出预测，但反馈不形成受治理学习状态 |
| Partial Learning Loop | 部分反馈可改变未来预测，但链路不可完整审计 |
| Learning System | 预测、反馈、数据集、权重、发布均可追溯、验证、回滚 |
| Self-Evolving Decision System | 系统能自动选择策略、监控漂移、触发安全发布与回滚 |

v5.0 目标是达到 **Learning System**，不是 Self-Evolving Decision System。

---

## 3. Prediction Traceability

### 3.1 核心问题

能否回答：某次预测是在什么模型状态下产生的？

### 3.2 指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| Prediction Registry Coverage | 完成预测中已写入 Prediction Registry 的比例 | ≥ 99% |
| Prediction Version Completeness | prediction record 同时具备 engine / weights / semantic / calibration version 的比例 | ≥ 99% |
| Prediction Artifact Linkage | prediction record 可链接输出 artifact 的比例 | ≥ 95% |
| Analysis Linkage | prediction record 具备 `analysis_id` 的比例 | ≥ 99% |
| Replay Metadata Completeness | 可重放所需 metadata 完整比例 | ≥ 95% |

### 3.3 最低验收门

v5.0 Phase 1 完成时：

- 每次新生产预测必须有 `prediction_id`。
- `prediction_id` 必须能查到：
  - `case_id`
  - `analysis_id`
  - `engine_version`
  - `weights_version`
  - `semantic_version`
  - `calibration_version`

### 3.4 失败判定

如果新预测仍只能通过 [`PredictionOutput.learning_feedback_id`](../../engine/domain/prediction.py:125) 或 report path 追踪，则该指标失败。

---

## 4. Feedback Coverage

### 4.1 核心问题

反馈是否真正绑定到产生它的预测？

### 4.2 指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| Feedback Registry Coverage | 新反馈写入 Feedback Registry 的比例 | ≥ 99% |
| Prediction-bound Feedback Rate | 反馈绑定有效 `prediction_id` 的比例 | ≥ 95% |
| Learning-eligible Feedback Rate | 满足学习准入条件的反馈比例 | 阶段性提升 |
| Legacy Unbound Feedback Rate | 无法绑定 prediction 的历史反馈比例 | 持续下降 |
| Feedback Normalization Success | 反馈结构化标准化成功比例 | ≥ 90% |

### 4.3 必备字段完整率

每条可学习反馈必须包含：

- `feedback_id`
- `prediction_id`
- `actual_outcome`
- `verdict`
- `feedback_source`
- `created_at`

目标完整率：**100%**。

### 4.4 失败判定

如果反馈只绑定 `case_id` 或 `statement_id` 就能进入训练，则该指标失败。

---

## 5. Learning Coverage

### 5.1 核心问题

学习是否经过标准 Dataset，而不是直接从日志训练？

### 5.2 指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| Dataset-mediated Training Rate | 训练任务通过 dataset manifest 启动的比例 | 100% |
| Sample Traceability | dataset sample 可追溯 prediction + feedback 的比例 | 100% |
| Dataset Manifest Completeness | dataset manifest 必填字段完整率 | 100% |
| Exclusion Reason Coverage | 被排除样本具备 exclusion reason 的比例 | 100% |
| Split Contamination Rate | train / validation / test 泄漏率 | 0% |

### 5.3 Dataset 必填指标

每个 dataset manifest 至少记录：

- `dataset_id`
- `dataset_version`
- `created_at`
- `source_prediction_query`
- `source_feedback_query`
- `split_strategy`
- `train_count`
- `validation_count`
- `test_count`
- `excluded_count`
- `schema_version`
- `sha256`

### 5.4 学习范围指标

| 指标 | 说明 |
|---|---|
| Domain Coverage | 各领域样本覆盖比例 |
| Event Coverage | 各事件类型样本覆盖比例 |
| Time Window Coverage | 各应期窗口样本覆盖比例 |
| Version Coverage | 不同 weights_version 预测样本覆盖 |

### 5.5 失败判定

如果 [`batch_rl_backtest.py`](../../tools/batch_rl_backtest.py:1) 或其他训练入口仍可直接扫描 [`cases/`](../../cases/) 并更新权重，则该指标失败。

---

## 6. Calibration Coverage

### 6.1 核心问题

概率校准是否从“被调用”变成“被训练、被验证、被版本化”？

### 6.2 指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| Calibration Version Coverage | 预测记录中包含 calibration_version 的比例 | ≥ 99% |
| Calibration Training Coverage | 有足够样本的领域完成 calibration candidate 的比例 | 阶段性提升 |
| Calibration Validation Coverage | calibration candidate 经过 validation 的比例 | 100% |
| Calibration Production Coverage | production prediction 使用版本化 calibration params 的比例 | ≥ 95% |
| Identity Calibration Rate | 因无参数而退回 identity 的比例 | 持续下降 |

### 6.3 质量指标

| 指标 | 说明 |
|---|---|
| Brier Score | 概率预测整体误差 |
| Expected Calibration Error | 置信区间校准误差 |
| Reliability Curve | 预测概率与实际命中率匹配程度 |
| Domain-level ECE | 分领域校准误差 |

### 6.4 发布门

Calibration candidate 只有满足：

- validation set 样本量达标；
- Brier score 不劣于 production baseline；
- ECE 不劣于 production baseline；
- 无关键领域显著恶化；

才允许成为 production calibration version。

### 6.5 失败判定

如果 production 仍固定加载缺失或默认 [`engine/calibration_params.json`](../../engine/calibration_params.json:1)，且 Prediction Registry 不能记录 calibration version，则该指标失败。

---

## 7. Weight Governance Coverage

### 7.1 核心问题

权重是否从“可覆盖文件”升级为“可治理版本”？

### 7.2 指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| Versioned Weight Usage | production prediction 使用 versioned weights 的比例 | ≥ 99% |
| Candidate Isolation | candidate weights 未被 runtime 读取的比例 | 100% |
| Validation-before-Promotion | promoted weights 有 validation record 的比例 | 100% |
| Rollback Readiness | production version 有 previous pointer 的比例 | 100% |
| Weight Diff Coverage | 新版本有 diff report 的比例 | 100% |
| Direct Overwrite Count | 直接覆盖 production 权重次数 | 0 |

### 7.3 版本完整性

每个 weight version 必须包含：

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

完整率目标：**100%**。

### 7.4 发布门

权重从 candidate 到 production 必须满足：

- validation report 存在；
- validation status = passed；
- promotion decision = approved；
- audit trail 完整；
- production pointer 更新成功；
- rollback pointer 存在。

### 7.5 失败判定

如果 [`save_expert_weights()`](../../engine/infrastructure/weight_repository.py:28) 仍能绕过 Weight Registry 直接改变 production 行为，则该指标失败。

---

## 8. Promotion / Validation Metrics

### 8.1 发布安全指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| Candidate Validation Rate | candidate 进入 validation 的比例 | 100% |
| Failed Candidate Block Rate | validation failed 后未进入 production 的比例 | 100% |
| Promotion Audit Completeness | promotion record 完整比例 | 100% |
| Rollback Test Success | rollback dry-run 成功率 | ≥ 99% |
| Production Activation Traceability | production pointer 可追溯 promotion run 的比例 | 100% |

### 8.2 质量指标

| 指标 | 说明 |
|---|---|
| Overall Hit Rate Delta | candidate vs production baseline |
| Domain Hit Rate Delta | 分领域变化 |
| Regression Count | 退化样本数量 |
| Max Weight Delta | 最大单领域权重变化 |
| Confidence Drift | 置信度分布漂移 |

---

## 9. Learning Audit Trail Coverage

### 9.1 核心问题

系统是否知道自己为什么改变？

### 9.2 指标

| 指标 | 定义 | 目标 |
|---|---|---:|
| Audit Event Coverage | 关键学习动作有 audit event 的比例 | 100% |
| Audit Chain Completeness | promotion 可串起 dataset → candidate → validation → activation 的比例 | 100% |
| Artifact Digest Coverage | audit event 关联 artifact sha256 的比例 | ≥ 95% |
| Actor Attribution | audit event 具备 actor 的比例 | 100% |
| Reason Coverage | promotion / rollback 具备 reason 的比例 | 100% |

### 9.3 必须审计事件

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

---

## 10. Learning System Readiness Score

### 10.1 评分维度

| 维度 | 权重 | 达标定义 |
|---|---:|---|
| Prediction Traceability | 20% | prediction version metadata 完整 |
| Feedback Coverage | 20% | feedback 绑定 prediction |
| Dataset Governance | 20% | 训练只从 dataset 开始 |
| Weight Governance | 20% | 权重版本化 + promotion gate |
| Audit / Rollback | 20% | 全链路审计 + 可回滚 |

### 10.2 等级

| 分数 | 等级 | 说明 |
|---:|---|---|
| 0–39 | Prediction System | 无有效学习治理 |
| 40–69 | Partial Learning Loop | 局部学习可用但不可完整治理 |
| 70–84 | Learning System Candidate | 主要治理链路成立，仍需补覆盖 |
| 85–94 | Learning System | 可追溯、可验证、可回滚、可发布 |
| 95–100 | Self-Evolving Ready | 具备进入自演化系统的治理基础 |

v5.0 成功目标：**≥ 85**。

---

## 11. Minimum Launch Criteria

v5.0 可宣布从 Prediction System 升级为 Learning System 的最低条件：

1. 新预测 Prediction Registry Coverage ≥ 99%。
2. 新反馈 Prediction-bound Feedback Rate ≥ 95%。
3. Dataset-mediated Training Rate = 100%。
4. Validation-before-Promotion = 100%。
5. Direct Overwrite Count = 0。
6. Promotion Audit Completeness = 100%。
7. Rollback dry-run 可成功执行。

---

## 12. Conditions for Self-Evolving Decision System

v5.0 完成后，系统仍只是 Learning System。要进入 Self-Evolving Decision System，还需要额外条件：

### 12.1 自动策略选择

系统能在多个 candidate 策略中自动选择：

- 权重更新策略。
- 校准策略。
- 领域特定策略。
- 保守 / 激进发布策略。

### 12.2 Drift Detection

系统能监控：

- feedback distribution drift。
- domain performance drift。
- calibration drift。
- semantic distribution drift。

### 12.3 Automated Safe Rollback

系统能在 production 指标恶化时自动触发 rollback request 或 rollback action。

### 12.4 Online / Shadow Evaluation

系统能运行：

- shadow candidate。
- A/B comparison。
- canary promotion。
- live safety guardrail。

### 12.5 Human Governance Policy

系统需定义哪些发布可自动，哪些必须人工批准。

---

## 13. Final Success Judgment

v5.0 的成功标准一句话：

> 任何进入未来预测的学习状态，都必须能追溯到 prediction、feedback、dataset、candidate、validation、promotion 与 audit trail。

若只能证明“权重变了”，不能证明“权重为什么能上线”，则 v5.0 不成功。
