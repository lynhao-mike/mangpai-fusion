# proposed-directory-layout.md · v5.0 Learning Governance 目录结构设计

> 目标：为 v5.0 Learning Governance System 设计符合 Clean Architecture 的目录结构。  
> 约束：不新增预测功能，不新增规则；只规划治理层目录、文件职责与迁移边界。  
> 当前基础：已有 [`engine/domain/`](../../engine/domain/)、[`engine/application/`](../../engine/application/)、[`engine/infrastructure/`](../../engine/infrastructure/)、[`tools/`](../../tools/)、[`META/`](../../META/)、[`cases/`](../../cases/) 等目录。

---

## 1. Thesis

v5.0 不应把学习治理继续塞进 [`META/`](../../META/)、[`cases/`](../../cases/) 或单个 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)。

正确方向是：

> **代码契约进入 `engine/` 的 Clean Architecture 分层；运行态学习资产进入独立 `learning/`；人类审计与计划继续保留在 `plans/` / `META/`。**

---

## 2. Target Top-level Layout

```text
mangpai-fusion/
  engine/
    domain/
      learning_governance/
    application/
      learning_governance/
    infrastructure/
      learning_governance/
    contracts/
      learning-governance/

  learning/
    registries/
    datasets/
    weights/
    calibration/
    semantics/
    promotions/
    audits/
    reports/

  tools/
    learning_registry.py
    learning_dataset.py
    learning_validate.py
    learning_promote.py
    learning_rollback.py
    learning_audit_report.py

  plans/
    v5-learning-governance/

  META/
    learning-governance-status.md
```

---

## 3. `engine/domain/learning_governance/`

### 3.1 职责

定义学习治理领域实体与状态机，不依赖 SQLite、YAML、路径、CLI。

### 3.2 建议文件

```text
engine/domain/learning_governance/
  __init__.py
  prediction_record.py
  feedback_record.py
  dataset_manifest.py
  weight_version.py
  promotion_run.py
  audit_event.py
  model_state_bundle.py
  enums.py
```

### 3.3 实体职责

| 文件 | 职责 |
|---|---|
| `prediction_record.py` | 定义 Prediction Registry 记录 |
| `feedback_record.py` | 定义 Feedback Registry 记录 |
| `dataset_manifest.py` | 定义 Dataset Manifest 与 split metadata |
| `weight_version.py` | 定义 immutable weight version 元数据 |
| `promotion_run.py` | 定义 candidate → validation → production 状态机 |
| `audit_event.py` | 定义 Learning Audit Trail 事件 |
| `model_state_bundle.py` | 定义 runtime 使用的版本组合 |
| `enums.py` | 状态枚举与 verdict 枚举 |

### 3.4 禁止事项

- 不读取 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1)。
- 不访问 [`cases/`](../../cases/)。
- 不写 SQLite。
- 不调用训练工具。

---

## 4. `engine/application/learning_governance/`

### 4.1 职责

定义用例编排，是系统从 Prediction System 升级为 Learning System 的核心应用层。

### 4.2 建议文件

```text
engine/application/learning_governance/
  __init__.py
  register_prediction.py
  register_feedback.py
  build_dataset.py
  train_candidate.py
  validate_candidate.py
  promote_weights.py
  rollback_weights.py
  resolve_model_state.py
  generate_audit_report.py
  policies.py
```

### 4.3 用例说明

| 文件 | 用例 |
|---|---|
| `register_prediction.py` | 生产预测完成后写 Prediction Registry |
| `register_feedback.py` | 反馈摄入后写 Feedback Registry |
| `build_dataset.py` | 从 registry join 生成 dataset manifest |
| `train_candidate.py` | 基于标准 dataset 产出 candidate weights |
| `validate_candidate.py` | 对 candidate 运行 validation gate |
| `promote_weights.py` | validation 通过后切 production pointer |
| `rollback_weights.py` | 将 production pointer 回滚到指定版本 |
| `resolve_model_state.py` | 为预测 runtime 解析 production model state bundle |
| `generate_audit_report.py` | 生成学习审计报告 |
| `policies.py` | validation / promotion / eligibility 策略 |

### 4.4 与现有应用层关系

| 当前文件 | v5.0 关系 |
|---|---|
| [`pipeline_runner.py`](../../engine/application/pipeline_runner.py:1) | 在预测完成后调用 `register_prediction` |
| [`minimal_learning_loop.py`](../../engine/application/minimal_learning_loop.py:1) | 保留历史学习逻辑，但被治理用例包裹 |
| [`probability_calibrator.py`](../../engine/application/probability_calibrator.py:1) | 后续由 calibration registry 管理版本 |
| [`event_semantics_loader.py`](../../engine/application/event_semantics_loader.py:1) | 后续由 semantic version 进入 model state bundle |

---

## 5. `engine/infrastructure/learning_governance/`

### 5.1 职责

实现 registry、artifact、YAML 版本、digest 与 SQLite 存储。

### 5.2 建议文件

```text
engine/infrastructure/learning_governance/
  __init__.py
  registry_store.py
  sqlite_learning_store.py
  weight_version_store.py
  dataset_artifact_store.py
  audit_log_store.py
  model_state_resolver.py
  digest.py
```

### 5.3 存储说明

| 文件 | 职责 |
|---|---|
| `registry_store.py` | 抽象接口 |
| `sqlite_learning_store.py` | SQLite 表实现 |
| `weight_version_store.py` | 管理 `learning/weights/` |
| `dataset_artifact_store.py` | 管理 `learning/datasets/` |
| `audit_log_store.py` | 管理 audit events |
| `model_state_resolver.py` | 读取 production pointers |
| `digest.py` | sha256 / canonical JSON 摘要 |

### 5.4 与现有 [`SQLiteAnalysisStore`](../../engine/infrastructure/analysis_store.py:81) 的关系

推荐：不要修改 [`SQLiteAnalysisStore`](../../engine/infrastructure/analysis_store.py:81) 的职责边界。

可复用：

- SQLite 连接风格。
- artifact record 风格。
- schema 初始化模式。

不应复用：

- `analysis_jobs` 作为 prediction registry。
- `analysis_cache` 作为 model state cache。

---

## 6. `engine/contracts/learning-governance/`

### 6.1 职责

定义机器可读或人类可读契约，供测试、工具、agent 对齐。

### 6.2 建议文件

```text
engine/contracts/learning-governance/
  00-OVERVIEW.md
  01-prediction-registry.md
  02-feedback-registry.md
  03-dataset-contract.md
  04-weight-version-contract.md
  05-promotion-pipeline.md
  06-audit-trail.md
  schemas/
    prediction-record.schema.json
    feedback-record.schema.json
    dataset-manifest.schema.json
    weight-version.schema.json
    promotion-run.schema.json
    audit-event.schema.json
```

---

## 7. `learning/` Runtime Asset Layout

### 7.1 总览

```text
learning/
  README.md
  registries/
  datasets/
  weights/
  calibration/
  semantics/
  promotions/
  audits/
  reports/
```

[`learning/`](../../learning/) 是 v5.0 新增的学习运行态资产根目录。它不同于 [`META/`](../../META/)：

- [`META/`](../../META/)：项目状态、历史审计、人类治理文档。
- [`learning/`](../../learning/)：机器可读学习状态、数据集、版本、发布记录。

---

## 8. `learning/registries/`

```text
learning/registries/
  learning.sqlite
  exports/
    prediction-registry-YYYYMMDD.jsonl
    feedback-registry-YYYYMMDD.jsonl
```

职责：

- 存放 Prediction Registry 与 Feedback Registry 的 SQLite 主库。
- 支持导出 JSONL 以便审计与备份。

建议表：

- `prediction_records`
- `feedback_records`
- `dataset_records`
- `weight_version_records`
- `promotion_runs`
- `audit_events`

---

## 9. `learning/datasets/`

```text
learning/datasets/
  registry.yaml
  training_set/
    ds-train-20260620-001/
      manifest.yaml
      samples.jsonl
      excluded.jsonl
  validation_set/
    ds-val-20260620-001/
      manifest.yaml
      samples.jsonl
  test_set/
    ds-test-20260620-001/
      manifest.yaml
      samples.jsonl
```

职责：

- 保存标准训练、验证、测试数据集。
- 每个 dataset 目录必须有 manifest。
- 训练只能读取 dataset，不允许扫描原始 feedback logs。

---

## 10. `learning/weights/`

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

职责：

- 不可变权重版本。
- production pointer。
- candidate 管理。
- diff 与 rollback 记录。

迁移原则：

- 当前 [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 迁移为 `learning/weights/versions/v001.yaml`。
- [`expert-weights.yaml`](../../engine/expert-weights.yaml:1) 后续只能作为 legacy export 或 runtime compatibility pointer，不再作为主事实源。

---

## 11. `learning/calibration/`

```text
learning/calibration/
  registry.yaml
  production.yaml
  versions/
    cal-v001.json
    cal-v002.json
  candidates/
    cal-cand-20260620-001.json
  validation/
    cal-val-20260620-001.md
```

职责：

- 版本化 [`ProbabilityCalibrator`](../../engine/application/probability_calibrator.py:66) 参数。
- 记录 calibration dataset 与 validation metrics。
- 替代固定 [`engine/calibration_params.json`](../../engine/calibration_params.json:1) 的隐式路径依赖。

---

## 12. `learning/semantics/`

```text
learning/semantics/
  registry.yaml
  production.yaml
  versions/
    sem-v001.yaml
    sem-v002.yaml
  candidates/
    sem-cand-20260620-001.yaml
  diffs/
    sem-v001-to-sem-v002.md
```

职责：

- 版本化事件语义配置。
- 对接当前 [`event-semantics.yaml`](../../theory/prediction_models/event-semantics.yaml:1)。
- 为 Prediction Registry 提供 `semantic_version`。

注意：v5.0 只治理版本，不新增事件语义规则。

---

## 13. `learning/promotions/`

```text
learning/promotions/
  promotion-run-20260620-001/
    request.yaml
    validation-report.md
    decision.yaml
    activation.yaml
  promotion-run-20260620-002/
    request.yaml
    validation-report.md
    decision.yaml
```

职责：

- 记录 candidate → validation → production 的发布过程。
- 未通过 validation 的 promotion 也必须保留。

---

## 14. `learning/audits/`

```text
learning/audits/
  audit-events.jsonl
  daily/
    2026-06-20.jsonl
  snapshots/
    learning-state-20260620.yaml
```

职责：

- 不可变审计事件。
- 每日切片。
- 学习状态快照。

---

## 15. `learning/reports/`

```text
learning/reports/
  validation/
    validation-20260620-001.md
  promotion/
    promotion-summary-20260620-001.md
  coverage/
    learning-coverage-20260620.md
  drift/
    drift-report-20260620.md
```

职责：

- 人类可读学习治理报告。
- 不作为机器事实源。

---

## 16. `tools/` CLI Layout

### 16.1 建议新增工具

```text
tools/
  learning_registry.py
  learning_dataset.py
  learning_validate.py
  learning_promote.py
  learning_rollback.py
  learning_audit_report.py
```

### 16.2 工具职责

| 工具 | 职责 |
|---|---|
| `learning_registry.py` | registry 初始化、导出、检查 |
| `learning_dataset.py` | 构建 training / validation / test dataset |
| `learning_validate.py` | 验证 candidate weights / calibration |
| `learning_promote.py` | promotion request 与 activation |
| `learning_rollback.py` | production pointer 回滚 |
| `learning_audit_report.py` | 生成审计报告 |

### 16.3 与现有工具关系

| 当前工具 | v5.0 定位 |
|---|---|
| [`feedback_ingest.py`](../../tools/feedback_ingest.py:1) | feedback registry writer 的上游入口 |
| [`feedback_loop.py`](../../tools/feedback_loop.py:1) | 迁移为 registry-aware learning entrypoint |
| [`batch_rl_backtest.py`](../../tools/batch_rl_backtest.py:1) | 降级为 candidate training runner，不可直接写 production |
| [`output_linter.py`](../../tools/output_linter.py:1) | 保持报告输出校验职责 |
| [`calibrate.py`](../../tools/calibrate.py:1) | 仍保持 deprecated，不作为 v5.0 入口 |

---

## 17. `META/` 与 `plans/` 边界

### 17.1 [`plans/`](../../plans/)

保存设计与迁移方案：

```text
plans/v5-learning-governance/
  CURRENT_STATE_ANALYSIS.md
  learning-governance-architecture.md
  proposed-directory-layout.md
  migration-plan.md
  success-metrics.md
  implementation-roadmap.md
```

### 17.2 [`META/`](../../META/)

保存项目级状态与人工治理摘要：

```text
META/
  learning-governance-status.md
  learning-release-log.md
```

禁止：把机器可读权重版本、dataset samples、registry DB 放入 [`META/`](../../META/)。

---

## 18. Migration Mapping

| 当前资产 | 目标位置 | 说明 |
|---|---|---|
| [`engine/expert-weights.yaml`](../../engine/expert-weights.yaml:1) | `learning/weights/versions/v001.yaml` | 初始 production weight version |
| [`engine/calibration_params.json`](../../engine/calibration_params.json:1) | `learning/calibration/versions/cal-v001.json` | 若存在则迁移；不存在则生成 empty baseline |
| [`theory/prediction_models/event-semantics.yaml`](../../theory/prediction_models/event-semantics.yaml:1) | `learning/semantics/versions/sem-v001.yaml` | 治理副本，不新增语义 |
| [`analysis_jobs`](../../engine/infrastructure/analysis_store.py:108) | `prediction_records.analysis_id` 外键参考 | 不直接替代 prediction registry |
| [`cases/*/feedback.md`](../../cases/README.md:1) | Feedback Registry source artifact | 先登记，后判定 eligibility |
| [`cases/*/prediction_feedback.jsonl`](../../cases/README.md:1) | legacy import source | 未绑定 prediction_id 的标记为 legacy |

---

## 19. Directory Maturity Milestones

### M1：Registry Skeleton

- `learning/registries/learning.sqlite`
- prediction / feedback records 可写入。

### M2：Dataset Artifacts

- `learning/datasets/*/manifest.yaml`
- `samples.jsonl`
- `excluded.jsonl`

### M3：Weight Versions

- `learning/weights/versions/v001.yaml`
- `learning/weights/production.yaml`

### M4：Promotion Artifacts

- `learning/promotions/*/validation-report.md`
- `decision.yaml`
- `activation.yaml`

### M5：Audit Completeness

- `learning/audits/audit-events.jsonl`
- daily snapshots。

---

## 20. Final Layout Judgment

v5.0 的目录结构必须体现一个原则：

> 预测代码、学习治理代码、机器学习状态、人类审计文档必须分离。

如果继续把权重、反馈、训练、发布都散落在 [`cases/`](../../cases/)、[`META/`](../../META/)、[`engine/`](../../engine/) 单文件中，系统即使“能学习”，也无法成为可治理的 Learning System。
