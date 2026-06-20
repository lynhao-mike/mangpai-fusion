# Migration Impact Analysis · v5.0 Phase 1（Registry Layer）

> 范围：仅分析 Prediction Registry + Feedback Registry 的迁移影响。
> 红线：不修改预测逻辑、不修改 RL 逻辑、不修改校准逻辑、不修改融合逻辑。
> 状态：设计期影响评估，待审核；本文档不执行迁移。

---

## 0. 结论摘要

v5.0 Phase 1 的迁移性质是**旁路治理能力新增**，不是预测系统重构。

核心结论：

1. 对现有预测结果：应为零行为变化。
2. 对现有反馈学习：应为零行为变化。
3. 对现有报告生成：无强制变化。
4. 对现有案例目录：无立即批量改写要求。
5. 对未来审计能力：新增“预测事件 → 反馈事件”的稳定链路。

最小迁移策略：

- 新预测：自动登记 `prediction_id` 与八字段版本指纹。
- 新反馈：优先强绑定 `prediction_id`。
- 旧反馈：通过 `case_id` 最近预测软绑定；无法绑定则保留为 `unbound`。
- 历史数据：不强制回填；如需回填，单独作为后续 Phase 1.5/Phase 2 迁移任务。

---

## 1. 影响对象总览

| 对象 | 影响类型 | 是否必须迁移 | 行为风险 | 说明 |
|---|---|---:|---:|---|
| `PredictionOutput` | 新增可选 `prediction_id` 字段 | 是 | 低 | 默认空值兼容旧构造；新流程自动填充 |
| Pipeline runner | 新增旁路 registry hook | 是 | 低 | 独立 try/except，不改变预测失败/成功语义 |
| Production service | 可选注入 `analysis_id` | 可选但建议 | 低 | 不注入也可用 `UNBOUND-*` 降级 |
| Feedback ingest | 新增旁路 feedback registry 写入 | 是 | 中低 | 不改变 learning samples / fanout / update |
| SQLite 存储 | 新增独立 registry DB | 是 | 低 | 与 `analysis.db` 物理隔离 |
| JSONL 审计 | 新增镜像文件 | 是 | 低 | append-only，可删除重建 |
| 历史 cases | 不批量改写 | 否 | 低 | 旧反馈软绑定或 unbound |
| 报告模板 | 可不变 | 否 | 低 | `prediction_id` 可作为后续报告脚注增强 |

---

## 2. 文件级影响矩阵

### 2.1 必需新增文件

| 文件 | 迁移影响 | 回滚方式 |
|---|---|---|
| `engine/domain/registry.py` | 新增 registry dataclass，不影响旧 import | 删除文件并移除引用 |
| `engine/application/model_state_resolver.py` | 新增只读版本解析器 | 删除文件并移除 registry service 引用 |
| `engine/application/registry_service.py` | 新增旁路编排服务 | 禁用 hook 或删除引用 |
| `engine/infrastructure/registry_store.py` | 新增独立存储 | 删除 registry DB/JSONL 与引用 |
| `tests/test_registry_ids.py` | 新增测试 | 删除测试 |
| `tests/test_model_state_resolver.py` | 新增测试 | 删除测试 |
| `tests/test_registry_store.py` | 新增测试 | 删除测试 |
| `tests/test_registry_sidecar.py` | 新增测试 | 删除测试 |

### 2.2 必需轻改文件

| 文件 | 计划改动 | 是否触碰核心行为 | 风险控制 |
|---|---|---:|---|
| `engine/domain/ids.py` | 新增 registry ID 生成函数 | 否 | 纯函数新增，旧函数不改 |
| `engine/domain/prediction.py` | `PredictionOutput` 新增 `prediction_id: str = ""` 与 `to_dict()` 输出 | 否 | 默认值兼容旧调用 |
| `engine/application/prediction_layer.py` | `build_prediction_output()` 生成/透传 `prediction_id` | 否 | 不改候选、概率、置信度、窗口、解释链计算 |
| `engine/application/pipeline_runner.py` | 成功生成 prediction 后旁路登记 | 否 | registry try/except 隔离 |
| `tools/feedback_ingest.py` | 反馈解析后旁路登记 Feedback Registry | 否 | learning update 原路径不变 |

### 2.3 可选轻改文件

| 文件 | 可选改动 | 不做的后果 |
|---|---|---|
| `engine/application/production_service.py` | 将已生成 `analysis_id` 注入 pipeline | Registry 使用 `UNBOUND-*`，仍可用但链路较弱 |
| `templates/feedback.md` | 增加可选 `prediction_id` 元信息位 | 新反馈仍可 case 软绑定，但不是强绑定 |
| `templates/feedback-v2.md` | 同上 | 同上 |
| `tools/README.md` | 登记 registry 工具/说明 | 工具发现性较差，但不影响运行 |

### 2.4 禁止修改行为文件

| 文件 | 禁止修改原因 | 允许的唯一例外 |
|---|---|---|
| `engine/application/fusion_engine_v2.py` | 融合逻辑红线 | 无 |
| `engine/application/probability_calibrator.py` | 校准逻辑红线 | 无 |
| `engine/application/minimal_learning_loop.py` | RL/学习逻辑红线 | 无，除非未来单独批准 |
| `engine/application/prediction_signals.py` | 预测信号逻辑红线 | 无 |
| `tools/feedback_loop.py` | 规则生命周期推进红线 | 无 |

---

## 3. 数据迁移影响

### 3.1 新增数据目录

建议新增：

```text
learning/registries/
  registry.db
  predictions.jsonl
  feedback.jsonl
```

影响：

- 需要在运行时确保目录可创建。
- 不影响 `cases/`、`reports/`、`META/` 现有结构。
- 不污染 `engine/logs/` 的现有权重/准确率日志。

### 3.2 SQLite schema 迁移

这是新库初始建表，不是旧库 schema migration。

影响：

- 不需要迁移 `analysis_store.py` 的 `analysis_jobs`、`analysis_artifacts`、`analysis_cache`。
- 不需要给现有 `analysis.db` 加表。
- 可通过删除 `learning/registries/registry.db` 完全回滚 registry 存储。

### 3.3 JSONL 审计副本

影响：

- Append-only，便于审计。
- 如果与 SQLite 不一致，SQLite 是查询主库，JSONL 是审计镜像。
- 重建策略：可从 SQLite 导出重建 JSONL；不建议反向覆盖 SQLite。

---

## 4. 历史数据兼容策略

### 4.1 历史预测

现状：历史 `PredictionOutput` 没有 `prediction_id`，也没有八字段版本指纹。

策略：

- 不伪造历史预测版本指纹。
- 不批量修改旧报告。
- 如后续确需回填，只能标记 `migration_source="backfill"` 与 `fingerprint_confidence="low"`，不得与原生 registry 记录混淆。

### 4.2 历史反馈

现状：历史反馈主要绑定 `case_id` + `statement_id`，没有 `prediction_id`。

策略：

| 情况 | 处理 |
|---|---|
| case 后续已有新预测 registry | 软绑定最新预测，`binding_mode="resolved_by_case"` |
| case 没有 registry 记录 | 登记为 `prediction_id=null`，`binding_mode="unbound"` |
| 人工确认可对应某次预测 | 后续治理工具可改为强绑定，但 Phase 1 不实现批量人工校正 |

### 4.3 旧工具兼容

所有旧工具如果不读取 registry，应继续可运行。

Registry 仅新增写入，不应成为旧工具必需依赖。特别是：

- `tools/feedback_ingest.py`：registry 失败不能影响 ingest 返回码。
- `tools/batch_review.py`：不应因 registry 缺失而失败。
- `tools/batch_rl_backtest.py`：Phase 1 不强制接入 registry。

---

## 5. 行为不变性分析

### 5.1 预测行为

不变项：

- `extract_ziping_signal()` 输出不变。
- `extract_dtt_signal()` 输出不变。
- `extract_mp_signal()` 输出不变。
- `build_final_prediction()` 输出不变。
- `build_prediction_output()` 中原有 `event_candidates`、`probability_distribution`、`time_window`、`confidence_score`、`explanation_chain` 计算不变。

新增项：

- `prediction_id` 字段。
- Registry sidecar 写入。

验证方式：

1. 固定输入，对比 registry 前后 `event_candidates` 与 `probability_distribution`。
2. 模拟 registry store 抛异常，pipeline 仍返回原预测输出。

### 5.2 RL 行为

不变项：

- `build_learning_samples()` 输出不变。
- `fanout_to_rules()` 输出不变。
- `run_learning_update()` 输入输出不变。
- `update_school_weights()` 算法不变。

新增项：

- 对解析出的 feedback 条目做 registry sidecar 登记。

验证方式：

1. 对同一 `feedback.md`，比较 registry 前后的 learning sample 数量与内容。
2. 比较权重更新 proposal 或 state diff 是否一致。

### 5.3 校准行为

不变项：

- `ProbabilityCalibrator.load()` 不变。
- `ProbabilityCalibrator.calibrate()` 不变。
- `prediction_layer._get_calibrator()` 不变。

新增项：

- `model_state_resolver` 只读识别当前校准版本，当前缺失概率校准参数时登记 `identity`。

风险：

- 不得误用 `engine/calibration.yaml` 作为概率校准参数版本。该文件是自迭代引擎阈值配置，不代表概率校准模型。

### 5.4 融合行为

不变项：

- 贝叶斯组合不变。
- 冲突检测不变。
- 最终候选事件排序不变。

新增项：无。

---

## 6. 失败模式与回滚

### 6.1 Registry 写入失败

预期行为：

- 记录 warning。
- pipeline / feedback ingest 继续成功。
- 不重试阻塞主流程。

可能原因：

- `learning/registries/` 无写权限。
- SQLite 文件锁。
- JSONL 写入失败。
- schema 初始化失败。

回滚：

- 禁用 registry hook。
- 删除或忽略 `learning/registries/`。
- 不需要修改历史 case/report。

### 6.2 Version Resolver 失败

预期行为：

- 返回显式降级值。
- 不抛出阻断。

降级映射：

| 字段 | 降级值 |
|---|---|
| `engine_version` | `unknown` |
| `weights_version` | `unknown` |
| `semantic_version` | `hardcoded-builtin` |
| `calibration_version` | `identity` |

### 6.3 Feedback 绑定失败

预期行为：

- 反馈不丢弃。
- 登记 `prediction_id=null`。
- 标记 `binding_mode="unbound"`。

回滚：

- Feedback Registry 可独立清空重建。
- 现有 learning state 不受影响。

---

## 7. 安全边界

### 7.1 不新增训练/学习触发

Prediction Registry 与 Feedback Registry 只记录事实，不触发：

- 权重更新。
- 规则晋升/降级。
- 校准参数拟合。
- 语义模型调整。

### 7.2 不改变用户报告内容

Phase 1 不要求报告展示 `prediction_id`。如后续需要，可在报告尾部增加审计脚注，但不属于本阶段。

### 7.3 不将 registry 作为在线必需依赖

即使 registry 不可写，系统仍必须能产出预测与摄入反馈。

---

## 8. 验收清单

实现阶段完成后，迁移影响验收应至少满足：

- [ ] 旧 pipeline 调用不传 `analysis_id` 仍成功。
- [ ] 生产服务传入 `analysis_id` 后 registry 记录能引用真实分析作业 ID。
- [ ] 每次新 `PredictionOutput` 含非空 `prediction_id`。
- [ ] Prediction Registry 记录包含八个核心字段且均非空。
- [ ] Registry 存储异常不改变 pipeline 返回。
- [ ] 旧 `feedback.md` 不含 `prediction_id` 仍可 ingest。
- [ ] 新 `feedback.md` 含 `prediction_id` 时可强绑定。
- [ ] 无法绑定的反馈以 `unbound` 保存，不丢弃。
- [ ] RL 权重更新测试前后输出一致。
- [ ] 融合/校准相关测试前后输出一致。

---

## 9. 是否需要历史回填

本阶段建议结论：**不做历史回填**。

原因：

1. 历史预测缺少当时的完整运行态版本指纹，强行回填会制造假精确性。
2. 用户要求 Phase 1 是 Registry Layer，不是历史数据治理。
3. 新 registry 的价值从上线后的每次预测开始自然积累。
4. 旧反馈可通过 `resolved_by_case` / `unbound` 保留，不阻断学习闭环。

如后续必须回填，应单独立项：

- `historical-prediction-backfill-plan.md`
- `legacy-feedback-binding-audit.md`
- `registry-backfill-quality-report.md`

这些不属于本阶段交付。

---

## 10. 最终迁移判断

v5.0 Phase 1 Registry Layer 可以作为**低侵入、可回滚、强审计增量**实施。

实施风险主要不在预测算法，而在工程边界：

- sidecar 必须彻底失败隔离。
- version resolver 必须如实降级，不伪造版本。
- feedback binding 必须区分强绑定、软绑定、未绑定。
- 历史回填必须延后，避免污染新 registry 的事实精度。

建议审核通过后的实施顺序：先 Prediction Registry，后 Feedback Registry；先 JSONL/SQLite 基础写入，后接入生产服务 `analysis_id` 注入；最后再补模板与工具索引说明。

本文档完成后停止，不进入第二阶段开发。
