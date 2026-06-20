# Registry Implementation Plan · v5.0 Phase 1（Registry Layer）

> 范围：仅规划 Prediction Registry + Feedback Registry 的实现步骤。
> 红线：不修改预测逻辑、不修改 RL 逻辑、不修改校准逻辑、不修改融合逻辑。
> 状态：设计落地计划，待审核；本文档不是实现提交。

---

## 0. 实施原则

### 0.1 本阶段只允许新增旁路能力

本计划的所有代码落点都必须满足：

1. 预测主链路输入、排序、概率、解释链、应期窗口不变。
2. RL 学习入口、权重更新算法、反馈 fanout 语义不变。
3. 校准器加载与概率校准逻辑不变。
4. 融合器 `build_final_prediction()` 不变。
5. Registry 写入失败只记录 warning，不向上抛出。

### 0.2 最小可落地目标

实现后，每次成功生成 `PredictionOutput` 时，系统自动产生一条 Prediction Registry 记录，至少包含 8 个核心字段：

| 字段 | 实现来源 | 要求 |
|---|---|---|
| `prediction_id` | 新增 ID 生成器 | 必填、主键、全局唯一 |
| `case_id` | `parsed_input.case_id` / pipeline 上下文 | 必填，缺失记 `UNKNOWN` |
| `analysis_id` | 服务层可选注入；缺失时 `UNBOUND-*` | 必填，不阻断 |
| `timestamp` | Registry 创建时 UTC | 必填，ISO-8601 |
| `engine_version` | `engine.__version__` | 必填 |
| `weights_version` | `engine/expert-weights.yaml.profile_version` | 必填，缺失 `unknown` |
| `semantic_version` | 当前生产路径实际状态 | 必填，当前为 `hardcoded-builtin` |
| `calibration_version` | 概率校准参数文件状态 | 必填，当前为 `identity` |

Feedback Registry 实现后，每条反馈记录均具备绑定状态：

- `strong`：反馈明确携带 `prediction_id`。
- `resolved_by_case`：旧反馈通过 `case_id` 反查最近 Prediction Registry 记录。
- `unbound`：无法绑定但不丢弃。

---

## 1. 建议新增文件

### 1.1 领域层

| 文件 | 职责 | 是否影响行为 |
|---|---|---|
| `engine/domain/registry.py` | 定义 `PredictionRegistryRecord`、`FeedbackRegistryRecord`、`ModelStateFingerprint` dataclass | 否 |
| `engine/domain/ids.py` | 增加 `make_prediction_id()`、`make_unbound_analysis_id()`、`make_feedback_registry_id()` | 否，仅新增纯函数 |

### 1.2 应用层

| 文件 | 职责 | 是否影响行为 |
|---|---|---|
| `engine/application/registry_service.py` | 编排版本解析、记录构造、仓储写入；所有异常内部吞掉并 warning | 否，旁路 |
| `engine/application/model_state_resolver.py` | 只读解析版本指纹 | 否，仅读取文件/常量 |

### 1.3 基础设施层

| 文件 | 职责 | 是否影响行为 |
|---|---|---|
| `engine/infrastructure/registry_store.py` | SQLite + JSONL 双写仓储，幂等 upsert | 否，独立库 |

### 1.4 可选测试文件

| 文件 | 覆盖点 |
|---|---|
| `tests/test_registry_ids.py` | ID 格式、唯一性、降级 ID |
| `tests/test_model_state_resolver.py` | 版本解析和缺失降级 |
| `tests/test_registry_store.py` | 建表、幂等写入、反馈外键/绑定模式 |
| `tests/test_registry_sidecar.py` | Registry 异常不影响 pipeline |

---

## 2. 数据结构草案

### 2.1 `ModelStateFingerprint`

```python
@dataclass(frozen=True)
class ModelStateFingerprint:
    engine_version: str
    weights_version: str
    semantic_version: str
    calibration_version: str
```

要求：

- 只保存版本值，不保存权重矩阵、校准参数全文。
- 版本解析失败必须显式降级，不抛出阻断主链路。

### 2.2 `PredictionRegistryRecord`

```python
@dataclass(frozen=True)
class PredictionRegistryRecord:
    prediction_id: str
    case_id: str
    analysis_id: str
    timestamp: str
    engine_version: str
    weights_version: str
    semantic_version: str
    calibration_version: str
    schema_version: str = "prediction-registry/v1"
```

八个核心字段应与用户要求一一对应；`schema_version` 是治理扩展字段，不替代核心字段。

### 2.3 `FeedbackRegistryRecord`

```python
@dataclass(frozen=True)
class FeedbackRegistryRecord:
    feedback_id: str
    prediction_id: str | None
    case_id: str
    statement_id: str
    verdict: str
    actual_outcome: str
    feedback_source: str
    binding_mode: str
    created_at: str
    schema_version: str = "feedback-registry/v1"
```

`binding_mode` 只允许：`strong`、`resolved_by_case`、`unbound`。

---

## 3. ID 协议

### 3.1 `prediction_id`

建议格式：

```text
PRED-YYYYMMDDTHHMMSSZ-<case_hash8>-<uuid6>
```

示例：

```text
PRED-20260620T071500Z-3f2a9c8b-a1b2c3
```

落点：`engine/domain/ids.py`。

理由：

- 该文件已是 statement_id / feedback 正则协议中心。
- 与现有 `_make_feedback_id(case_id)` 的 `hash + timestamp + uuid` 风格一致。
- 不把生成规则散落到 application / infrastructure 层。

### 3.2 `UNBOUND` analysis_id

建议格式：

```text
UNBOUND-YYYYMMDDTHHMMSSZ-<uuid12>
```

语义：pipeline 直接调用、测试或脚本场景没有服务层 `analysis_id` 注入时的显式占位。它不是错误，而是绑定状态事实。

### 3.3 Feedback Registry ID

建议格式：

```text
FB-YYYYMMDDTHHMMSSZ-<case_hash8>-<uuid6>
```

不得复用现有 `learning_feedback_id`，因为后者是预测输出内部反馈位，不是 Feedback Registry 主键。

---

## 4. Version Resolver 计划

新增 `resolve_model_state()`，只读解析：

| 字段 | 解析步骤 | 降级值 |
|---|---|---|
| `engine_version` | `import engine; engine.__version__` | `unknown` |
| `weights_version` | 读取 `engine/expert-weights.yaml`，优先 `profile_version`，再 `profile_id`，再 `updated_at` | `unknown` |
| `semantic_version` | 当前生产预测实际仍使用硬编码 `_DOMAIN_MEANINGS`，因此登记 `hardcoded-builtin` | `hardcoded-builtin` |
| `calibration_version` | 若后续存在 `engine/calibration_params.json`，取文件 hash 或 `updated_at`；当前缺失则登记 `identity` | `identity` |

注意：`engine/calibration.yaml` 是自迭代引擎阈值配置，不是概率校准参数；不得把它当作 `calibration_version` 的主要来源。

---

## 5. Prediction Registry 集成路径

### 5.1 `PredictionOutput` 最小字段扩展

在 `engine/domain/prediction.py` 的 `PredictionOutput` dataclass 增加：

```python
prediction_id: str = ""
```

并在 `to_dict()` 输出该字段。

理由：

- 用户要求每次 `PredictionOutput` 生成时自动创建 `prediction_id`。
- 默认空字符串不破坏旧构造调用。
- Registry 仍保存完整版本指纹，`PredictionOutput` 只携带锚点 ID，避免把治理字段塞满业务对象。

### 5.2 `build_prediction_output()` 生成或接收 ID

推荐方案：在 `build_prediction_output()` 内部生成 `prediction_id`，并把它写入返回对象。

可选签名：

```python
def build_prediction_output(
    final_prediction: FinalPrediction,
    fusion_findings: FusionFindings,
    gate_results: list[GateResult],
    *,
    use_calibration: bool = True,
    parsed_input: Any = None,
    prediction_id: str | None = None,
) -> PredictionOutput:
```

实现原则：

- 如果外部传入 `prediction_id`，使用外部值。
- 如果未传入，基于 `case_id` 自动生成。
- 不改变 event candidates、probability distribution、confidence、time window、explanation chain 的任何计算。

### 5.3 Pipeline 旁路 Hook

在 `engine/application/pipeline_runner.py` 的预测成功分支中：

1. 调用 `build_prediction_output()` 得到 `prediction`。
2. 将 `prediction` 挂载到 `output.prediction`。
3. 独立 `try/except` 调用 `register_prediction_output(...)`。
4. Registry 失败仅 warning，不改变 `prediction` 与 `output`。

伪流程：

```python
prediction = build_prediction_output(...)
output.prediction = prediction
try:
    register_prediction_output(
        prediction=prediction,
        case_id=case_id,
        analysis_id=analysis_id,
    )
except Exception as exc:
    logger.warning("Prediction registry write failed: %s", exc)
```

### 5.4 `analysis_id` 注入

建议给 `run_pipeline()` / `run_pipeline_e2e()` 增加可选参数：

```python
analysis_id: str | None = None
```

服务层 `ProductionAnalysisService` 在已有 `analysis_id` 后调用 pipeline 时传入；其他调用不传仍兼容。

若 `analysis_id is None`，Registry Service 内部生成 `UNBOUND-*`，不可阻断。

---

## 6. Feedback Registry 集成路径

### 6.1 反馈输入兼容

优先支持两种方式：

1. 新版 `feedback.md` 可在元信息区声明：

```markdown
prediction_id: PRED-20260620T071500Z-3f2a9c8b-a1b2c3
```

2. 旧版 `feedback.md` 不声明 `prediction_id`，沿用当前 `[S-...] [y/n/?/skip]` 标注。

### 6.2 `feedback_ingest.py` 旁路登记

在 `tools/feedback_ingest.py` 完成现有解析与学习样本构造后，旁路调用 `register_feedback_entries(...)`：

- 不改变 `build_learning_samples()` 结果。
- 不改变 `fanout_to_rules()` 行为。
- 不改变 `run_learning_update()` 行为。
- Registry 写入失败仅 warning。

### 6.3 绑定策略

| 输入情况 | Registry 行为 | `binding_mode` |
|---|---|---|
| feedback 明确有 `prediction_id` 且 registry 中存在 | 直接绑定 | `strong` |
| feedback 明确有 `prediction_id` 但 registry 中不存在 | 可记录但标记待审，或降级 unbound；实现阶段需定策略 | `unbound` |
| feedback 无 `prediction_id`，case_id 有最近预测 | 绑定最近一条 | `resolved_by_case` |
| feedback 无 `prediction_id`，case_id 无预测 | 保留反馈但不绑定 | `unbound` |

---

## 7. 存储实现计划

### 7.1 文件布局

建议新增目录：

```text
learning/registries/
  registry.db
  predictions.jsonl
  feedback.jsonl
```

`registry.db` 是机器查询主库；JSONL 是审计镜像。

### 7.2 SQLite schema

Prediction 表：

```sql
CREATE TABLE IF NOT EXISTS prediction_registry (
  prediction_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL,
  analysis_id TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  engine_version TEXT NOT NULL,
  weights_version TEXT NOT NULL,
  semantic_version TEXT NOT NULL,
  calibration_version TEXT NOT NULL,
  schema_version TEXT NOT NULL
);
```

Feedback 表：

```sql
CREATE TABLE IF NOT EXISTS feedback_registry (
  feedback_id TEXT PRIMARY KEY,
  prediction_id TEXT,
  case_id TEXT NOT NULL,
  statement_id TEXT NOT NULL,
  verdict TEXT NOT NULL,
  actual_outcome TEXT NOT NULL,
  feedback_source TEXT NOT NULL,
  binding_mode TEXT NOT NULL,
  created_at TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  FOREIGN KEY (prediction_id) REFERENCES prediction_registry(prediction_id)
);
```

索引：

```sql
CREATE INDEX IF NOT EXISTS idx_prediction_registry_case_id
  ON prediction_registry(case_id);

CREATE INDEX IF NOT EXISTS idx_prediction_registry_analysis_id
  ON prediction_registry(analysis_id);

CREATE INDEX IF NOT EXISTS idx_feedback_registry_prediction_id
  ON feedback_registry(prediction_id);

CREATE INDEX IF NOT EXISTS idx_feedback_registry_case_statement
  ON feedback_registry(case_id, statement_id);
```

### 7.3 幂等策略

- Prediction Registry：`prediction_id` 主键，使用 `INSERT OR IGNORE`。
- Feedback Registry：`feedback_id` 主键，使用 `INSERT OR IGNORE`。
- JSONL 镜像：若 SQLite 写入成功且为新记录，再 append，避免重复审计行。

---

## 8. 分阶段实现顺序

### Step 1：领域协议

1. 新增 `engine/domain/registry.py`。
2. 扩展 `engine/domain/ids.py` 的 registry ID 生成函数。
3. 扩展 `PredictionOutput.prediction_id`。

验收：dataclass 可实例化，旧调用不报错。

### Step 2：版本解析器

1. 新增 `engine/application/model_state_resolver.py`。
2. 读取 `engine.__version__`。
3. 读取 `engine/expert-weights.yaml.profile_version`。
4. 如实返回 `semantic_version="hardcoded-builtin"`。
5. 如实返回 `calibration_version="identity"`，除非概率校准参数文件实际存在。

验收：缺失文件不抛异常，返回显式降级值。

### Step 3：仓储

1. 新增 `engine/infrastructure/registry_store.py`。
2. 实现 `init_schema()`。
3. 实现 `save_prediction(record)`。
4. 实现 `save_feedback(record)`。
5. 实现 `find_latest_prediction_by_case(case_id)`。

验收：SQLite 表存在，JSONL 同步写入，重复写入幂等。

### Step 4：Prediction sidecar

1. 在 `build_prediction_output()` 中生成并挂载 `prediction_id`。
2. 在 `pipeline_runner.py` 成功生成 prediction 后旁路登记。
3. 可选注入 `analysis_id`；缺失则 Registry Service 生成 `UNBOUND-*`。

验收：pipeline 输出值与旧逻辑一致，但 `output.prediction.prediction_id` 非空；registry 写失败不影响输出。

### Step 5：Feedback sidecar

1. 在 `feedback_ingest.py` 读取可选 `prediction_id`。
2. 对每条 statement feedback 生成 Feedback Registry 记录。
3. 按强绑定 / case 软绑定 / unbound 规则登记。

验收：旧 feedback 文件仍可 ingest；新增 registry 记录不改变学习结果。

---

## 9. 测试与验收标准

### 9.1 单元测试

| 测试 | 断言 |
|---|---|
| ID 生成 | 格式稳定、连续生成不重复 |
| Version Resolver | 当前仓库返回 `engine_version=1.3.1`、`weights_version=phase-b-v1`、`semantic_version=hardcoded-builtin`、`calibration_version=identity` |
| Store schema | `init_schema()` 可重复调用 |
| Store idempotency | 相同 `prediction_id` 重复写只保留一条 |
| Feedback binding | strong / resolved_by_case / unbound 三态可区分 |
| Sidecar failure | 仓储抛错时 pipeline 不失败 |

### 9.2 回归测试

建议实现阶段至少运行：

```bash
pytest tests/test_phase_a_minimal_learning_loop.py -q
pytest tests/test_production_service.py -q
pytest tests/v1_3_acceptance/test_h6_full_loop.py -q
```

目的：证明 RL、production service、完整反馈闭环未因 Registry sidecar 改变行为。

### 9.3 人工验收

一次真实 pipeline 后应满足：

1. `PredictionOutput.to_dict()` 包含非空 `prediction_id`。
2. `learning/registries/registry.db` 有对应 `prediction_registry` 记录。
3. `learning/registries/predictions.jsonl` 有同样主键记录。
4. 后续 `feedback_ingest` 对该 case 的反馈能产生 `feedback_registry` 记录。
5. 如反馈无 `prediction_id`，绑定模式应为 `resolved_by_case` 或 `unbound`，不可静默丢弃。

---

## 10. 禁止触碰清单

实现阶段不得修改以下函数的算法语义：

| 文件 | 禁止触碰内容 |
|---|---|
| `engine/application/fusion_engine_v2.py` | `build_final_prediction()`、贝叶斯融合、冲突检测 |
| `engine/application/probability_calibrator.py` | `calibrate()`、Platt/temperature scaling、反馈拟合 |
| `engine/application/minimal_learning_loop.py` | `update_confidence()`、`run_learning_update()`、`update_school_weights()` |
| `engine/application/prediction_signals.py` | 三类 prediction signal 抽取逻辑 |
| `tools/feedback_loop.py` | 规则状态推进语义 |

允许的改动仅限新增 registry 调用、可选参数、可选字段、只读解析、独立持久化。

---

## 11. 审核前决策点

实现前建议确认：

1. 是否接受 `PredictionOutput` 只新增 `prediction_id`，完整八字段保存在 Registry，而不全部塞入 `PredictionOutput`。
2. 是否采用 SQLite + JSONL 双写，还是先 JSONL 单写。
3. `weights_version` 是否固定取 `profile_version`，还是组合为 `profile_id@profile_version`。
4. 旧反馈 `resolved_by_case` 是否使用“同 case 最新 prediction”作为默认绑定。
5. `analysis_id` 可选注入是否覆盖 `run_pipeline()` 与 `run_pipeline_e2e()` 两个入口。

本文档完成后不进入实现，等待审核确认。
