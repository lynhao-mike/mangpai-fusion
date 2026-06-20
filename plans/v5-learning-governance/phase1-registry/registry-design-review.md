# Registry Design Review · v5.0 Phase 1（Registry Layer）

> 范围：仅 Prediction Registry + Feedback Registry 的**设计审查**。
> 红线：不修改预测逻辑、不修改 RL 逻辑、不修改校准逻辑、不修改融合逻辑。
> 状态：设计稿，待审核。完成审查后停止，不进入实现阶段。

---

## 0. 设计目标与不变式

### 0.1 目标

1. 每次 `PredictionOutput` 生成时，自动创建 `prediction_id`，并登记完整运行态版本指纹：
   - `prediction_id`
   - `case_id`
   - `analysis_id`
   - `timestamp`
   - `engine_version`
   - `weights_version`
   - `semantic_version`
   - `calibration_version`
2. 提供 Feedback Registry，使**每条反馈都能绑定 `prediction_id`**。

### 0.2 核心不变式（Invariants）

- **INV-1（非侵入）**：注册失败绝不能影响预测产出。预测主链路保持现状，注册是旁路（side-channel）。
- **INV-2（只增不改）**：本阶段对现有预测/RL/校准/融合代码**零行为修改**，只允许新增旁路写入点与新增可选字段。
- **INV-3（可追踪）**：`prediction_id` 是后续 Feedback / Dataset / Weight 治理的根锚点（root anchor）。
- **INV-4（幂等）**：同一次预测重复登记不产生重复主记录（以 `prediction_id` 为主键）。
- **INV-5（版本如实）**：版本指纹必须反映**该次预测实际使用的运行态**，缺失来源（如 calibration 文件不存在）必须显式记为 `none`/`identity`，禁止伪造。

---

## 1. 现状事实基线（基于真实代码）

| 关注点 | 当前真实情况 | 来源 |
|---|---|---|
| 预测产出实体 | `PredictionOutput` 仅含 `learning_feedback_id`，无 `prediction_id`、无版本字段 | [`engine/domain/prediction.py`](engine/domain/prediction.py:116) |
| 预测构建点 | `build_prediction_output()` 内一次性构造并返回 | [`engine/application/prediction_layer.py`](engine/application/prediction_layer.py:118) |
| 预测调用点 | `pipeline_runner` 在 `timing.step("prediction")` 内调用，`try/except` 隔离，失败置 `None` | [`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py:117) |
| `analysis_id` 来源 | 由 `ProductionAnalysisService.new_analysis_id()` 生成，格式 `AN-<stamp>-<uuid12>` | [`engine/application/production_service.py`](engine/application/production_service.py:239) |
| `analysis_id` 可见性 | **pipeline_runner 内部不可见**：服务层生成 ID 后才调用 pipeline，ID 未下传 | 同上 + [`pipeline_runner.run_pipeline_e2e`](engine/application/pipeline_runner.py:170) |
| `engine_version` | `engine.__version__ = "1.3.1"`（以根 VERSION 为事实源） | [`engine/__init__.py`](engine/__init__.py:7) |
| `weights_version` | `engine/expert-weights.yaml` 顶部 `profile_version: phase-b-v1`（另有 `profile_id`、`updated_at`） | [`engine/expert-weights.yaml`](engine/expert-weights.yaml:1) |
| `calibration_version` | `engine/calibration_params.json` **当前不存在** → 校准退化为恒等（temperature=1.0） | [`prediction_layer._get_calibrator`](engine/application/prediction_layer.py:38)，文件确认不存在 |
| `semantic_version` | `event-semantics.yaml` 未接入生产预测路径（loader 存在但未被消费） | `prediction_signals._DOMAIN_MEANINGS` 硬编码 |
| 现有持久化范式 | `SQLiteAnalysisStore`：`connect()` 上下文管理 + `init_schema()` 幂等建表 + 外键 | [`engine/infrastructure/analysis_store.py`](engine/infrastructure/analysis_store.py:81) |
| 反馈入口 | `feedback.md` 的 `[S-...] [y/n/?/skip]` 标注 → `feedback_ingest` fanout 到 rule-level | [`tools/feedback_ingest.py`](tools/feedback_ingest.py:1) |
| 反馈绑定粒度 | `case_id` + `statement_id`，**无 `prediction_id`** | [`cases/_TEMPLATE/statement_index.json`](cases/_TEMPLATE/statement_index.json:1) |

> 结论：当前没有任何"一次预测"的稳定身份。`learning_feedback_id` 是预测内部生成的反馈位 ID，不等于 `prediction_id`，也不携带版本指纹。

---

## 2. 关键设计决策（Design Decisions）

### DD-1：`prediction_id` 与 `analysis_id` 的关系

- `analysis_id`：一次**分析作业**（生产服务层概念，可能命中缓存、可能 render）。
- `prediction_id`：一次**预测产出**（预测层概念，绑定具体运行态版本）。
- 关系：`prediction_id` **引用** `analysis_id`，而非替代。一个 `analysis_id` 原则上对应一个 `prediction_id`（当前流水线每作业产出一个 `PredictionOutput`）。
- **不复用 `analysis_jobs` 表**作为 Prediction Registry（INV-3）：作业表是运维状态，预测注册是学习治理事实，二者生命周期与语义不同。

### DD-2：`analysis_id` 在预测层不可见 —— 采用「可选注入 + 降级生成」

现状：`pipeline_runner` 看不到服务层的 `analysis_id`。为遵守 INV-1/INV-2，采取**双轨**：

- **首选（注入）**：`run_pipeline_e2e` 增加**可选参数** `analysis_id: str | None = None`，由 `production_service` 在已生成 ID 后下传。默认 `None`，不破坏任何现有调用方。
- **降级（self-id）**：当 `analysis_id is None`（如直接调 pipeline 的脚本/测试），Registry 自行生成一个 `analysis_id="UNBOUND-<uuid>"` 占位，保证 `prediction_id` 仍可创建。

> 该决策只新增可选参数，不改变现有行为，符合 INV-2。是否采用注入轨在实现阶段确认。

### DD-3：版本指纹解析器（Version Resolver）只读、不触发副作用

新增一个**只读** `resolve_model_state()`，集中读取四个版本：

| 字段 | 解析来源 | 缺失/降级值 |
|---|---|---|
| `engine_version` | `engine.__version__` | 必有 |
| `weights_version` | `expert-weights.yaml` 的 `profile_version`（回退 `profile_id`+`updated_at`） | `unknown` |
| `calibration_version` | `engine/calibration_params.json` 存在则取其指纹/`updated_at`，否则 | `identity`（如实反映恒等校准，INV-5） |
| `semantic_version` | 生产路径未接入语义 → 当前实事求是记为 | `hardcoded-builtin`（不伪装成 yaml 版本） |

> Version Resolver **不修改** 校准/融合/RL 逻辑，仅读取它们的事实源文件与常量。

### DD-4：Prediction Registry 写入点 —— 旁路 Hook

- 写入点放在 `pipeline_runner` 成功构造 `PredictionOutput` **之后**、`output.prediction = prediction` 附近，包裹独立 `try/except`，失败仅 `logger.warning`，**不抛出**（INV-1）。
- `build_prediction_output()` 签名可**可选**新增 `prediction_id`/版本字段透传；若不注入，则由旁路 Hook 在产出后补登。两种方案在实现计划文档中给出权衡，本阶段不定稿代码。

### DD-5：Feedback Registry 绑定策略 —— 兼容旧反馈

- 新反馈：要求携带 `prediction_id`（强绑定）。
- 旧反馈（仅有 `case_id`/`statement_id`）：通过 Prediction Registry 按 `case_id` 反查**最近一次** `prediction_id` 进行**软绑定**，并标记 `binding_mode="resolved_by_case"` 以区分强绑定。
- 无法解析时记 `prediction_id=null` + `binding_mode="unbound"`，进入待治理队列，**绝不丢弃**反馈。

### DD-6：存储介质

- 复用 `SQLiteAnalysisStore` 的工程范式（同一 `connect()`/`init_schema()` 模式），但落在**独立 DB 文件** `learning/registries/registry.db`，与 `analysis.db` 物理隔离，避免污染运维库。
- 同步镜像 JSONL（`learning/registries/predictions.jsonl`、`feedback.jsonl`）作为可人读审计副本与跨工具消费源（与现有 `*.jsonl` 审计风格一致）。

---

## 3. 数据契约（Schema 草案）

### 3.1 Prediction Registry 记录

```json
{
  "prediction_id": "PRED-20260620T070500Z-3f2a9c8b",
  "case_id": "C-2026-029-坤-乙亥戊寅辛酉癸巳",
  "analysis_id": "AN-20260620-070500-abc123def456",
  "timestamp": "2026-06-20T07:05:00Z",
  "engine_version": "1.3.1",
  "weights_version": "phase-b-v1",
  "semantic_version": "hardcoded-builtin",
  "calibration_version": "identity",
  "schema_version": "prediction-registry/v1"
}
```

约束：
- `prediction_id` 主键，幂等（INV-4）。
- 八个核心字段全部 NOT NULL（缺失以显式降级值填充，INV-5）。
- `analysis_id` 允许 `UNBOUND-*` 占位（DD-2）。

### 3.2 Feedback Registry 记录

```json
{
  "feedback_id": "FB-20260620T071000Z-9a1b",
  "prediction_id": "PRED-20260620T070500Z-3f2a9c8b",
  "case_id": "C-2026-029-坤-乙亥戊寅辛酉癸巳",
  "statement_id": "S-029-marriage-001",
  "verdict": "hit",
  "actual_outcome": "命主确认 2024 年离婚",
  "feedback_source": "feedback_ingest",
  "binding_mode": "strong",
  "created_at": "2026-06-20T07:10:00Z",
  "schema_version": "feedback-registry/v1"
}
```

约束：
- `feedback_id` 主键。
- `prediction_id` 外键引用 Prediction Registry；允许 `null` 仅当 `binding_mode="unbound"`（DD-5）。
- `binding_mode ∈ {strong, resolved_by_case, unbound}`。
- `verdict` 复用现有语义 `{hit, miss, abstain, no_data}`，不新增反馈语义（不动 RL）。

---

## 4. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 注册写入异常拖垮预测 | 高 | INV-1 旁路 + try/except 吞错只 warning |
| `analysis_id` 不可见导致孤儿预测 | 中 | DD-2 降级 self-id + `UNBOUND-*` 标记 |
| 旧反馈无 `prediction_id` | 中 | DD-5 软绑定 + unbound 队列，不丢数据 |
| 版本指纹伪造/误导 | 中 | INV-5：缺失显式降级（`identity`/`hardcoded-builtin`） |
| 误改预测/RL/校准/融合 | 高（违红线） | INV-2：仅新增可选字段/旁路；下文 migration-impact 逐文件标注"是否触碰行为" |
| SQLite 与运维库耦合 | 中 | DD-6 独立 DB 文件 |

---

## 5. 待审核确认项（Open Questions）

1. **注入轨 vs self-id 轨**：是否允许给 `run_pipeline_e2e` / `build_prediction_output` 增加可选参数下传 `analysis_id`？（DD-2/DD-4）
2. **`weights_version` 取值**：用 `profile_version`（`phase-b-v1`）还是 `profile_id`（含日期，更细）作为主版本字段？
3. **`semantic_version` 命名**：生产路径未接入语义，记 `hardcoded-builtin` 是否符合你对"如实"的期望？
4. **存储形态**：SQLite + JSONL 双写，还是先只做 JSONL（更轻、更易审阅，后续再上 SQLite）？
5. **旧反馈软绑定**：`resolved_by_case` 取"最近一次预测"是否可接受，还是要求人工确认绑定？

> 以上 5 项确认后，再进入实现阶段（registry-implementation-plan.md 的代码落地）。本阶段到此停止。
