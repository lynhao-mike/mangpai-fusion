# 问真补盘全量重算闭环问题诊断与方案备选

生成时间：2026-06-11

## 1. 结论摘要

当前系统的核心问题不是单个函数缺失，而是“问真补充排盘信息后的案例生命周期”没有被建模为生产级数据事件。

补盘后应触发完整的 recompute lifecycle：

```text
补盘输入规范化
  → 全量重算
  → 跨流派交叉验证
  → 断语分级
  → 置信度动态更新
  → 结论变更追踪
  → 报告重渲染
  → 反馈闭环
```

但现状更接近：

```text
补充 / 修正排盘信息
  → 局部脚本处理
  → 生成或修补报告
  → statement_index / feedback / calibration 未必同步闭环
```

因此，系统存在“报告看似完成，但结构化断语资产未完成”的生产风险。

## 2. 目标功能

用户期望的目标能力是：

1. 所有补充问真八字排盘信息的八字，必须全量重算。
2. 重算结果必须跨流派交叉验证，而非单一路径输出。
3. 每条断语必须分级，支持后续反馈与校准。
4. 置信度必须随反馈、冲突裁决、重算差异动态更新。
5. 补盘前后的结论变化必须可追踪、可解释、可审计。

## 3. 现象与证据

### 3.1 完成态过度依赖报告产物

现有流程中，`reports/` 下报告文件容易被当作完成标志。但对于反馈闭环而言，真正的完成标志应是结构化 artifact：

- `cases/<case_id>/input.md`
- `cases/<case_id>/statement_index.json`
- `cases/<case_id>/feedback.md`
- calibration snapshot
- conclusion diff artifact
- report artifact

如果只产出报告，而 `statement_index.json` 为空或不可绑定反馈，则该案例不应视为完成。

### 3.2 statement_index 可为空壳

已观察到部分案例的 `statement_index.json` 存在 `statements: []` 这类空结构。

这会直接破坏：

- 断语逐条反馈
- 规则命中校准
- 置信度动态更新
- 结论变更 diff
- 回归测试基线

### 3.3 feedback.md 可为手工表格

部分 `feedback.md` 更像人工记录表，而不是机器可解析的断语反馈格式。

这会导致 `tools/feedback_ingest.py` 无法稳定执行自动摄入，因为反馈无法可靠绑定到 statement id 或结构化断语。

### 3.4 repan / fixed / feedback 工具职责分散

当前存在多个与补盘、修正、反馈相关的脚本：

- `tools/case_feedback_repan_index.py`
- `tools/generate_wenzhen_fixed_reports.py`
- `tools/normalize_wenzhen_fixed_cases.py`
- `tools/extract_wenzhen_repan_completed.py`
- `tools/feedback_ingest.py`
- `tools/feedback_loop.py`

这些工具局部有用，但整体缺少一个统一的补盘重算 orchestrator，导致“某一步做了”不等于“闭环完成”。

## 4. 可能问题源排查

从生产调试视角，可能的问题源包括：

1. 输入规范化不足：补盘信息没有统一成为可重跑输入。
2. pipeline 不承担补盘事件：重算没有统一入口。
3. 断语索引生成不强制：报告可生成但 statement_index 可空。
4. 反馈格式不结构化：feedback 无法自动绑定断语。
5. 置信度模型只静态计算：没有接入重算差异与反馈命中。
6. 跨流派验证层不足：缺少 school verdict matrix。
7. 结论变更无 artifact：补盘前后差异无法审计。

压缩后最可能的 1-2 个根因：

1. 缺少统一的补盘重算生命周期模型。
2. 完成标准错误：以报告产物为准，而不是以结构化断语资产和可验证闭环为准。

## 5. 根因判断

根因：系统把“报告产物”当完成标准，而不是把“可追踪、可反馈、可重算、可比较的结构化断语资产”当完成标准。

这导致补盘后的核心链路没有 hard gate：

- 未强制全量重算。
- 未强制生成非空断语索引。
- 未强制跨流派裁决矩阵。
- 未强制置信度 delta。
- 未强制结论变更清单。
- 未强制 feedback 可绑定。

## 6. 高格局目标模型

建议建立唯一事实流：

```text
RepanInput
  → RecomputeJob
  → PipelineRun
  → SchoolVerdictMatrix
  → StatementIndex
  → ConfidenceDelta
  → ConclusionDiff
  → ReportRender
  → FeedbackIngestReady
```

核心 artifact：

| Artifact | 用途 |
|---|---|
| `recompute_manifest.json` | 记录本次补盘重算任务、输入 hash、执行时间、版本 |
| `findings.before.json` | 补盘前结构化 findings 快照 |
| `findings.after.json` | 补盘后结构化 findings 快照 |
| `school_verdict_matrix.json` | 跨流派交叉验证矩阵 |
| `statement_index.json` | 断语索引与分级 |
| `confidence_delta.json` | 置信度变化 |
| `conclusion_diff.json` | 结论变更追踪 |
| `feedback_binding_check.json` | feedback 是否可绑定到断语 |
| `content-report.md` | 最终统一报告 |

## 7. 方案备选

### 方案 A：保守补丁路径

做法：

- 在现有 `tools/case_feedback_repan_index.py` 等脚本中补充字段。
- 对空 `statement_index.json` 增加 warning。
- 在 `feedback_ingest.py` 中兼容更多手工表格格式。
- 对报告末尾增加“补盘已处理”标识。

优点：

- 改动小。
- 对现有脚本影响低。
- 快速缓解部分案例不可摄入问题。

缺点：

- 不能解决生命周期缺失。
- 容易继续产生“报告完成但闭环未完成”。
- warning 不是 hard gate，生产风险仍存在。
- 多脚本职责继续分散。

适用场景：

- 只想短期抢救少量案例。
- 不准备近期重构补盘流程。

结论：不推荐作为主路径，只能做临时止血。

### 方案 B：干净目标路径

做法：

- 新建补盘重算事件模型 `RepanRecomputeJob`。
- 新建统一 CLI：`python -m tools.recompute_wenzhen_case <case_id>`。
- pipeline 输出必须包含 findings、statement index、school verdict matrix、confidence delta、conclusion diff。
- 任何 artifact 缺失都 hard fail。
- 旧的 repan / fixed / normalize 脚本逐步退役或变成内部 helper。

优点：

- 一次性建立正确系统边界。
- 完成态机器可验证。
- 支持批量补盘、回归、审计、反馈校准。
- 能真正满足“全量重算、跨流派验证、断语分级、置信度动态更新、结论变更追踪”。

缺点：

- 初始改动较大。
- 需要定义 artifact schema。
- 需要补测试和迁移旧案例。

适用场景：

- 准备把问真补盘做成长期稳定生产能力。
- 接下来会处理大量案例。

结论：目标模型正确，但建议分阶段落地。

### 方案 C：分阶段干净路径

做法：

第一阶段：建立最小可用 recompute CLI。

- 新增 `tools/recompute_wenzhen_case.py`。
- 输入：case_id。
- 输出：`recompute_manifest.json`、`statement_index.json`、`conclusion_diff.json`、`confidence_delta.json`。
- 对空 `statement_index.json` hard fail。

第二阶段：补跨流派矩阵。

- 新增 `school_verdict_matrix.json`。
- 按流派记录支持、反对、冲突、补充证据。
- 将现有 `mapping/consensus.md`、`mapping/conflicts.md` 等映射纳入验证口径。

第三阶段：接入反馈闭环。

- 将 feedback 解析结果绑定到 statement id。
- 更新 calibration snapshot。
- 生成 confidence delta。

第四阶段：报告重渲染与变更追踪。

- 报告中展示结论变更摘要。
- 内部 artifact 保留完整 diff。
- output linter 校验主要事项、断语等级、置信度、应期。

优点：

- 方向正确。
- 风险可控。
- 每阶段都有可验收产物。
- 不需要一次性删除所有旧脚本。

缺点：

- 需要严格防止阶段一再次变成局部脚本。
- 需要明确最终退役清单。

适用场景：

- 当前仓库最适合。
- 需要兼顾交付速度和系统正确性。

结论：推荐方案。

## 8. 推荐方案

推荐采用方案 C：分阶段干净路径。

核心原则：

1. 补盘是事件，不是报告修补。
2. 全量重算是默认行为，不允许局部跳过。
3. 结构化 artifact 是完成标准，报告只是展示层。
4. statement_index 为空必须 hard fail。
5. 置信度必须可解释地变化，不能只给静态分数。
6. 结论变更必须有 machine-readable diff。

## 9. 不应继续做的事

1. 不要继续只修补 `reports/` 文本。
2. 不要继续允许空 `statement_index.json` 进入完成态。
3. 不要继续把手工 `feedback.md` 当作可靠结构化事实源。
4. 不要继续增加互相绕过的 repan/fixed/normalize 脚本。
5. 不要把跨流派验证降级成报告里的几段文字说明。
6. 不要只在最终报告里写“置信度”，而不保存置信度变化原因。

## 10. 建议新增模块

### 10.1 `tools/recompute_wenzhen_case.py`

统一入口。

职责：

- 读取 case。
- 校验补盘输入。
- 调用 pipeline。
- 生成所有 recompute artifacts。
- 调用报告渲染。
- 执行 hard gate。

### 10.2 `engine/application/recompute.py`

应用层 orchestration。

职责：

- 定义 `RepanRecomputeJob`。
- 定义 `RecomputeResult`。
- 管理 before/after snapshot。
- 协调 pipeline、cross-school、confidence、diff。

### 10.3 `engine/application/school_verdict.py`

跨流派验证矩阵。

职责：

- 聚合高、段、杨、任、子平、调候等流派证据。
- 输出支持 / 反对 / 冲突 / 补充。
- 生成 school verdict matrix。

### 10.4 `engine/application/conclusion_diff.py`

结论变更追踪。

职责：

- 比较补盘前后 findings。
- 标注新增、删除、增强、减弱、冲突解决。
- 给报告和审计使用。

### 10.5 `engine/application/confidence_delta.py`

置信度动态变化。

职责：

- 比较 before/after confidence。
- 接入 feedback 命中。
- 接入跨流派冲突裁决。
- 输出变化原因。

## 11. 验收标准

对任意补盘案例，执行：

```bash
python -m tools.recompute_wenzhen_case <case_id>
```

必须满足：

1. 能全量重跑 pipeline。
2. `statement_index.json` 非空。
3. 每条 statement 有等级、领域、证据链、置信度。
4. 生成 `school_verdict_matrix.json`。
5. 生成 `confidence_delta.json`。
6. 生成 `conclusion_diff.json`。
7. feedback 可绑定到 statement id。
8. 报告可重渲染。
9. output linter 通过。
10. 任一关键 artifact 缺失则命令失败。

## 12. 第一验证点

选择 3 个已有问真补盘案例作为 proof point：

1. 一个已有报告但 statement_index 为空的案例。
2. 一个有 feedback 但无法结构化绑定的案例。
3. 一个补盘前后四柱或关键排盘字段发生变化的案例。

对这 3 个案例执行最小 recompute CLI，验证是否能产出：

- 旧 findings 快照。
- 新 findings 快照。
- 断语等级表。
- 跨流派验证矩阵。
- 置信度 delta。
- 结论变更清单。
- 重渲染报告。

## 13. 反证条件

如果现有主流程已经能稳定做到以下全部事项，则本诊断“生命周期缺失”的判断需要撤回：

1. 补盘后自动生成非空 `statement_index.json`。
2. feedback 能逐条绑定到 statement。
3. calibration snapshot 会因反馈与补盘重算变化。
4. 报告能展示结论变更。
5. 跨流派验证有结构化 artifact。
6. 以上流程有测试覆盖。

当前仓库证据更支持相反判断：局部脚本能生成或修补报告，但缺少生产级全量重算闭环。

## 14. 建议落地顺序

1. 先定义 recompute artifact schema。
2. 新增最小 `tools/recompute_wenzhen_case.py`。
3. 对空 `statement_index.json` 加 hard fail。
4. 增加 `conclusion_diff.json`。
5. 增加 `confidence_delta.json`。
6. 增加 `school_verdict_matrix.json`。
7. 接入 `feedback_ingest.py`。
8. 将旧 repan/fixed/normalize 脚本改为 wrapper 或退役。
9. 增加 3 个 proof point 回归测试。
10. 批量迁移所有问真补盘案例。
