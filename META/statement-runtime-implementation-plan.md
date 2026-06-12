# P5-3 Statement Runtime Implementation Plan

生成时间：2026-06-12

设计性质：只读实施方案；本文件只定义 `statement_record` 正式落地路径，不实现代码，不修改 `engine/*`、`theory/*`、`tests/*` 或 `META/project-state.json`。

## 0. Executive Decision

P5-3 推荐把 `statement_record` 插入到“规则触发 / evidence 汇聚之后、报告渲染完成之前”的生产链路中，由报告生成链的 statement runtime builder 统一生成，并以每案 artifact `cases/<case_id>/statement_records.json` 落盘。

唯一推荐链路：

```text
rule trigger / evidence
  -> resolve rule metadata
  -> build statement_record
  -> freeze confidence_snapshot
  -> derive statement_index.json
  -> render report
  -> collect feedback verdict
  -> feedback joins statement_record
  -> dynamic confidence update
```

关键裁决：

- `statement_record` 是未来动态置信度学习的唯一标准事实源。
- `statement_index.json` 保留为报告展示索引与反馈锚点，不再承担学习事实源职责。
- 旧案保持只读；新案开始生成标准 `statement_record`。
- Phase-1000 解除 BLOCKED 的前提不是反馈数量，而是反馈到规则元数据的正向链路完整且可硬校验。

## 1. Audit Findings

| 审计对象 | 当前状态 | 证据 | 影响 |
|---|---|---|---|
| 当前 statement 生成 | `tools/render_report.py` 生成 `statement_index.json` | `render_from_output()` 在渲染后落盘索引；`_build_statement_index()` 汇总 ctx 中的可反馈断语 | 已有反馈锚点，但不是标准学习记录 |
| `statement_id` | 已存在 | `engine/domain/ids.py` 提供 `compute_statement_id()`；渲染器使用 evidence refs / rule ids 生成稳定 ID | 可作为反馈 join key |
| `statement_record` | 运行产物为 0 | `META/statement-runtime-audit.md` 记录标准 `statement_record` count = 0 | 学习链路缺最小事实单元 |
| feedback pipeline | 读取 `feedback.md` + `statement_index.json` + 可选 `statement_rule_map.json` | `tools/feedback_ingest.py` 的 `fanout_to_rules()` 从索引读取 `rule_ids` | 仍是展示索引反推规则 |
| dynamic confidence | 规则更新在 `tools/feedback_loop.py` 内按 `rule_id` 重算 Beta | `feedback_ingest.ingest()` fanout 后调用规则级更新 | 当前输入不具备 family/canon/rule_type 完整链 |
| production artifact gate | hard-gate `statement_index.json` 与 `statement_rule_map.json` | `engine/application/artifact_inventory.py` 的 `REQUIRED_CASE_ARTIFACTS` | 尚未 gate `statement_records.json` |
| pipeline orchestration | D1-D4 -> integrate -> render -> self_iter | `engine/application/pipeline_runner.py` 文档化步骤 | 最佳插入点应在 integrate/render 边界，而不是反馈后补 |

## A. statement_record 应该由哪个模块生成

### A.1 当前实际生成 statement 的模块

当前实际生成可反馈 statement 的模块是 `tools/render_report.py`：

1. `render_from_output()` 调用 `render()` 生成统一报告，并捕获渲染上下文。
2. `_build_statement_index(ctx, case_id)` 从 `zuogong_paths`、`production_rule_conclusions`、`consensus_conclusions`、`complementary_conclusions`、`iron_gates`、`support_*`、`parallel_domain_*` 等 ctx 列表收集断语。
3. 每条索引记录写入 `statement_id`、`domain`、`summary`、`status`、`section`、`rule_ids`、`schools`，并落盘为 `cases/<case_id>/statement_index.json`。

因此现状不是“引擎层没有断语”，而是断语只在报告索引层被宽松表达，没有形成标准单规则学习记录。

### A.2 最佳插入点

最佳插入点是：

```text
AnalysisOutput / render ctx 已形成
  -> statement runtime builder 读取 rule trigger / evidence / ctx
  -> 生成 statement_records.json
  -> 派生 statement_index.json
  -> 渲染并输出报告
```

更精确地说，P5-3 应把生成职责放在“report pipeline 的 statement runtime builder”中，而不是继续把 `_build_statement_index()` 作为唯一源头。该 builder 应被 `render_from_output()` 或其上游 adapter 调用，但其输入必须来自结构化 evidence / rule trigger / AnalysisOutput，而不是从报告 Markdown 文本反向解析。

### A.3 为什么

1. `statement_record` 需要在生成期冻结 `rule_id`、`family_id`、`school`、`canon`、`rule_type`、`confidence_snapshot`、`generated_at`，这些字段只有在规则触发和 evidence 汇聚阶段最可靠。
2. `tools/render_report.py` 已经是当前 statement_index 写入点，接入成本最低，且天然知道哪些断语会成为反馈锚点。
3. `engine/application/pipeline_runner.py` 的顺序是 integrate 后 render，说明插入在 render 边界不会破坏 D1-D4 领域引擎职责。
4. 如果放到 feedback ingest 阶段，会把“生成时事实”变成“反馈后补事实”，导致 confidence snapshot 时间穿越。
5. 如果只在 export 阶段生成，会只能看到展示文本和索引摘要，无法可靠拆分多规则断语。

## B. 生成时机比较

| 方案 | 位置 | 优点 | 缺点 | 判断 |
|---|---|---|---|---|
| 方案1：Rule Trigger 后立即生成 | 单条规则触发时立刻写 `statement_record` | 元数据最完整，能冻结真实 rule confidence | 太早；很多断语要经过共识、互补、冲突裁判、并行专家裁决后才决定是否输出，容易生成未展示或被裁掉的记录 | 不作为单独最终方案 |
| 方案2：Report Render 阶段生成 | AnalysisOutput / ctx 已形成、Markdown 输出前生成记录 | 同时拥有结构化 evidence 与最终展示断语；可保证每个反馈锚点都有记录；可由 record 派生 index | 需要重构现有 `_build_statement_index()` 的职责边界 | 推荐 |
| 方案3：Report Export 阶段生成 | 报告 Markdown / 文件写出后再生成 | 对现有渲染侵入最低 | 只能从文本或最终索引反推，无法可靠补齐 family/canon/rule_type/confidence_snapshot | 不推荐 |

推荐方案：方案2，Report Render 阶段生成。

推荐口径不是“从报告文本生成”，而是在报告渲染阶段、报告文本输出前，由结构化 ctx / evidence 生成 `statement_record`，再从 `statement_record` 派生 `statement_index.json`。这样既避免 Rule Trigger 太早造成未展示记录，也避免 Report Export 太晚造成反推。

## C. 存储位置比较

| 方案 | 路径 | 优点 | 缺点 | 判断 |
|---|---|---|---|---|
| case 目录 | `cases/<case_id>/statement_records.json` | 与 `input.md`、`feedback.md`、`statement_index.json` 同域；便于人工审计、反馈 join、case 归档、迁移；符合现有文件制工作流 | 单案文件会增长，需要 schema 校验和 hash gate | 推荐作为 P5-3 主落点 |
| artifact 目录 | 如 `cases/<case_id>/findings/statement_records.json` 或独立 artifacts | 更接近机器产物，便于 production job 编目 | 反馈人员和现有工具默认读 case 根目录；会造成学习入口与反馈文件分离 | 可作为镜像或 inventory 记录，不作唯一源 |
| 未来数据库扩展 | SQLite / job store / future DB table | 查询与批量学习效率高；适合大规模 posterior 统计 | 当前系统事实源仍以 case 文件为主；过早 DB 化会增加迁移和一致性成本 | 作为后续索引层，不作 P5-3 首发事实源 |

推荐：首发落在 `cases/<case_id>/statement_records.json`，同时允许 production artifact inventory 记录该文件的 sha256。未来数据库只做派生索引或缓存，不能取代每案文件事实源。

建议 envelope：

```json
{
  "schema_version": "statement_record.v1",
  "case_id": "C-YYYY-NNN-乾-四柱",
  "generated_at": "2026-06-12T00:00:00Z",
  "records": []
}
```

每条 `records[]` 内部仍以 `META/statement-record-contract-v1.md` 定义的 `statement_record.v1` 为规范单元。

## D. 现有 4858 条 statement 兼容策略

| 方案 | 内容 | 优点 | 风险 | 判断 |
|---|---|---|---|---|
| OPTION-A：全部忽略 | 历史 4858 条 statement 不迁移、不参与学习 | 最简单，无错误学习风险 | 浪费已有反馈；不能解释旧案状态；不利于审计连续性 | 不推荐 |
| OPTION-B：迁移生成 candidate statement_record | 对历史 statement 批量生成候选 record | 可保留历史资产；对 exact match 子集有潜在价值 | 历史索引缺 `family_id`、`canon`、`rule_type`、`confidence_snapshot`；自动迁移会制造虚假确定性 | 仅作人工 review 辅助，不作主路径 |
| OPTION-C：旧案保持只读，新案开始生成 | 历史 case 保持 legacy/candidate/review lane；新 case 生产期生成标准 record | 最小风险；不污染 Beta；与 P5-1/P5-2 审计结论一致；能最快打通未来闭环 | 历史反馈需要单独人工修复队列 | 推荐 |

推荐：OPTION-C。

执行口径：

1. 旧案的 `statement_index.json` 保持只读兼容，反馈摄入可继续登记 verdict，但没有完整 `statement_record` 时不得进入标准 dynamic confidence 学习。
2. 旧案若有明确业务价值，可另建 migration candidate / review pack，仅 exact match 且人工验收后的子集允许生成 migrated record。
3. 新案从 P5-3 实施后必须原生生成 `statement_records.json`，并由它派生 `statement_index.json`。
4. 现有 4858 条 statement 不做全量自动迁移；它们是审计证据，不是自动学习样本。

## E. 动态置信度接入方案

唯一推荐：未来动态置信度读取 `statement_record`，不读取 `statement_index.json` 作为学习事实源。

标准学习输入链：

```text
feedback.md verdict
  -> statement_id
  -> cases/<case_id>/statement_records.json
  -> rule_id
  -> family_id
  -> school
  -> canon
  -> rule_type
  -> tools/feedback_loop.py rule-level Beta update
```

`statement_index.json` 的未来职责：

- 报告展示索引。
- 反馈标注锚点。
- legacy fallback 兼容入口。
- 人工审阅时快速定位报告断语。

`statement_index.json` 不应继续承担：

- 标准学习事实源。
- `rule_id` 反推来源。
- family/canon/rule_type 的补字段容器。
- confidence snapshot 的生成后回填位置。

过渡策略：

1. `feedback_ingest` 优先读取 `statement_records.json`。
2. 若不存在 record，则进入 legacy path：读取 `statement_index.json` / `statement_rule_map.json`，只登记反馈或进入 candidate review，不自动进入标准 Beta。
3. dynamic confidence 更新日志必须能输出完整链路：`case_id`、`statement_id`、`rule_id`、`family_id`、`school`、`canon`、`rule_type`、`verdict`、`confidence_snapshot`。

## F. Phase-1000 解除 BLOCKED 条件

Phase-1000 可以解除 `BLOCKED` 的条件应定义为“新反馈样本可安全进入动态学习”，而不是“历史反馈全部修复”。

必须全部满足：

| 条件 | 验收口径 | 不满足时状态 |
|---|---|---|
| 1. 生产生成 | 新 case 运行报告 pipeline 后必有 `cases/<case_id>/statement_records.json` | 仍为 BLOCKED |
| 2. schema 完整 | 每条 record 满足 `statement_record.v1` 必填字段，缺 `rule_id/family_id/school/canon/rule_type/confidence_snapshot/generated_at` 即失败 | 仍为 BLOCKED |
| 3. 单规则拆行 | 多规则支撑断语拆成多条 record，每条只绑定一个 `rule_id` 与一个 `family_id` | 仍为 BLOCKED |
| 4. index 派生兼容 | `statement_index.json` 可由 records 或同源 ctx 派生，反馈中的 `statement_id` 能 join 到 records | 仍为 BLOCKED |
| 5. feedback ingest 优先消费 record | `feedback.md` verdict 不再通过展示索引反推标准学习字段 | 仍为 BLOCKED |
| 6. dynamic confidence 输入门禁 | 只有完整 record 链路进入 Beta 更新；legacy/fallback/candidate 不得静默学习 | 仍为 BLOCKED |
| 7. artifact hard gate | production artifact inventory / recompute gate 要求 record artifact，并在缺失时 fail | 仍为 BLOCKED |
| 8. 审计日志 | 每次规则置信度更新可追踪到 `feedback verdict -> statement_id -> statement_record -> rule_id -> family_id -> school -> canon -> rule_type` | 仍为 BLOCKED |
| 9. 新案验收样本 | 至少 2-3 个新 case 完成 report -> feedback -> ingest dry-run / real-run，能证明 hit/miss 均按 record 更新 | 仍为 BLOCKED |
| 10. legacy 隔离 | 旧 4858 条 statement 未迁移部分明确标为 legacy/read-only/candidate，不进入标准学习入口 | 仍为 BLOCKED |

解除 BLOCKED 的最小证明点：

```text
new case
  -> statement_records.json generated
  -> feedback.md marks one hit and one miss by statement_id
  -> ingest joins records, not statement_index
  -> rule-level update log shows full metadata chain
  -> no legacy fallback row enters Beta silently
```

可接受的未完成项：

- 历史 4858 条 statement 尚未迁移。
- 数据库索引尚未建立。
- 部分 old case 仍只能 feedback 登记、不能学习。

不可接受的未完成项：

- 新 case 仍只生成 `statement_index.json`。
- dynamic confidence 仍从 `statement_index.json` / `statement_rule_map.json` 反推标准学习字段。
- `confidence_snapshot` 在反馈后回填。
- 无法证明 `rule_id -> family_id -> school -> canon -> rule_type`。

## 7. Implementation Phasing

虽然本任务不实现代码，正式落地建议按以下阶段拆分：

| 阶段 | 目标 | 输出 | 是否解除 Phase-1000 |
|---|---|---|---|
| P5-3A | 新增 statement runtime builder 设计/接口 | builder 输入输出契约、schema validator 设计 | 否 |
| P5-3B | 报告生成期写 `statement_records.json` | 新 case artifact + index 派生 | 否 |
| P5-3C | feedback ingest 优先消费 records | record join、legacy fallback 隔离 | 否 |
| P5-3D | dynamic confidence 门禁接入 | 完整链路才更新 Beta，日志可审计 | 可候选解除 |
| P5-3E | production hard gate / recompute gate 接入 | record artifact 必需、schema fail-fast | 可正式解除 |
| P5-3F | 历史 candidate review pack | 旧案 exact/manual 子集候选迁移 | 非解除前提 |

## 8. Risks and Guardrails

| 风险 | 说明 | 护栏 |
|---|---|---|
| 展示索引与学习索引耦合 | 继续在 `statement_index.json` 加字段会让展示层承担学习语义 | record 为事实源，index 为派生产物 |
| 多规则反馈放大 | 一条断语多个 rule_id 若不拆行，会重复放大 family 更新 | record 单规则拆行，family cap 在 Beta 前执行 |
| confidence 时间穿越 | 反馈后再读取当前规则库作为生成时置信度 | 生成时冻结 `confidence_snapshot` |
| legacy 静默学习 | 旧索引字段不完整却进入 Beta | legacy path 只登记或 candidate review，不进标准学习 |
| report export 反推 | 从 Markdown 文本恢复 rule metadata | 禁止作为主路径，只允许人工审计辅助 |

## 9. Final Recommendation

P5-3 最终方案：

1. `statement_record` 由 report pipeline 的 statement runtime builder 生成，插入点在结构化 evidence / AnalysisOutput 已形成、报告文本输出前。
2. 生成时机选择 Report Render 阶段；不是 Rule Trigger 立刻落盘，也不是 Report Export 后反推。
3. 存储位置选择 `cases/<case_id>/statement_records.json`，artifact inventory 只记录和 hard-gate 该文件。
4. 历史 4858 条 statement 采用 OPTION-C：旧案只读，新案原生生成；OPTION-B 仅作为人工 candidate migration。
5. 动态置信度唯一标准输入改为 `statement_record`；`statement_index.json` 只作展示/反馈锚点与 legacy fallback。
6. Phase-1000 解除 BLOCKED 的标准是新案全链路可证明、record schema hard-gate、feedback ingest 与 dynamic confidence 均不再依赖展示索引反推。
