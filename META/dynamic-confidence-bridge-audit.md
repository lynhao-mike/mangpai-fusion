# P5-5 Dynamic Confidence Bridge Audit

生成时间：2026-06-12

## 1. 审计结论

结论：**Phase-1000 仍为 `BLOCKED`，尚未达到 `READY_FOR_BRIDGE`。**

核心原因不是 [`statement_record.v1`](META/statement-record-contract-v1.md:1) 的设计字段不够，而是桥接链路尚未把正式反馈入口切到 [`statement_records.json`](cases:1)：

1. 当前仓库正式 [`cases/`](cases/) 下没有任何已归档的 [`statement_records.json`](cases:1) 文件。
2. [`tools.feedback_ingest.ingest()`](tools/feedback_ingest.py:618) 仍优先读取 [`statement_index.json`](cases:1)，并只合并旁路 [`statement_rule_map.json`](cases:1)，没有读取 [`statement_records.json`](cases:1)。
3. [`tools.feedback_ingest.fanout_to_rules()`](tools/feedback_ingest.py:208) 的标准输入仍是 [`statement_index.json`](cases:1) 内的 `rule_ids`，不是 `statement_id -> statement_record -> rule_id`。
4. [`tools.feedback_loop._apply_rule_verdicts()`](tools/feedback_loop.py:635) 仍只消费 `rule_id + verdict + VerdictContext`，没有接收或审计 `family_id / canon / rule_type`。
5. Phase-1000 现有 554 feedback rows 在 [`META/phase-1000-dynamic-confidence-init/rule_statement_family_alignment.csv`](META/phase-1000-dynamic-confidence-init/rule_statement_family_alignment.csv:1) 中仍全部标记 `needs_mapping_repair=true`，严格可学习样本为 0。

因此，P5-4 已完成“生成期 facts layer 设计与测试样例”，但 P5-5 审计显示：**Dynamic Confidence Bridge 还没有完成生产入口接线、case 归档落盘、learning sample 门禁与审计日志链路。**

## 2. 审计范围

本次审计覆盖用户指定范围：

| 范围 | 审计结果 |
|---|---|
| [`statement_records.json`](cases:1) | 正式 [`cases/`](cases/) 中未发现实际落盘文件；仅在 [`META/statement-runtime-implementation-report.md`](META/statement-runtime-implementation-report.md:46) 中有临时样例。 |
| [`tools/feedback_ingest.py`](tools/feedback_ingest.py:1) | 未接入 [`statement_records.json`](cases:1)，仍依赖 [`statement_index.json`](cases:1) / [`statement_rule_map.json`](cases:1)。 |
| [`tools/feedback_loop.py`](tools/feedback_loop.py:1) | 只做 `rule_id` 级 Beta 更新，不保留 `family_id / canon / rule_type` 学习字段。 |
| [`engine/application/*`](engine/application:1) | [`engine/application/recompute.py`](engine/application/recompute.py:163) 的 binding check 仍以 [`statement_index.json`](cases:1) 为准；[`engine/application/artifact_inventory.py`](engine/application/artifact_inventory.py:26) 的 required artifacts 未包含 [`statement_records.json`](cases:1)。 |
| [`META/phase-1000-dynamic-confidence-init/*`](META/phase-1000-dynamic-confidence-init/README.md:1) | 554 rows 的初始化副本仍全部需要 mapping repair。 |

## 3. 检查项 A：feedback 是否可直接定位 `statement_id -> rule_id`

结论：**否。当前仍依赖 [`statement_index.json`](cases:1)，且不能直接从 feedback 进入 [`statement_records.json`](cases:1)。**

证据：

- [`tools.feedback_ingest.ingest()`](tools/feedback_ingest.py:664) 明确读取 [`statement_index.json`](cases:1)。
- [`tools.feedback_ingest.ingest()`](tools/feedback_ingest.py:666) 只读取旁路 [`statement_rule_map.json`](cases:1) 并合并到 index。
- [`tools.feedback_ingest.fanout_to_rules()`](tools/feedback_ingest.py:226) 从 `statement_index.get("statements")` 构造 statement map。
- [`tools.feedback_ingest.fanout_to_rules()`](tools/feedback_ingest.py:245) 从 index item 的 `rule_ids` 取得规则映射。
- [`tools.feedback_ingest.fanout_to_rules()`](tools/feedback_ingest.py:247) 对标准 list schema 缺少 `rule_ids` 时只是跳过规则更新，不改走 [`statement_records.json`](cases:1)。
- [`tools/`](tools/README.md:24) 中反馈入口仍描述为结构化反馈摄入，但实现尚未升级为 record-first。

判定：

| 子项 | 状态 |
|---|---|
| feedback 能解析出 `statement_id` | 部分满足，依赖 [`engine.application.feedback_parser.parse_statement_feedback()`](engine/application/feedback_parser.py:1)。 |
| `statement_id` 直接 join [`statement_records.json`](cases:1) | 不满足。 |
| `statement_id -> rule_id` 不依赖 [`statement_index.json`](cases:1) | 不满足。 |
| legacy fallback 隔离 | 部分满足；无 index 或无结构化 feedback 时会回退 [`tools.feedback_loop.ingest_feedback()`](tools/feedback_loop.py:819)，但未作为 Dynamic Confidence 标准门禁隔离。 |

## 4. 检查项 B：`rule_id` 是否能直接映射 `family_id / school / canon / rule_type`

结论：**在新 runtime builder 的单条 record 内“可以生成”，但映射质量仍是命名规则推导，不是已接入反馈学习链路的稳定 registry。**

证据：

- [`engine.statement_runtime.build_statement_records_envelope()`](engine/statement_runtime.py:55) 会生成 `rule_id / family_id / school / canon / rule_type / confidence_snapshot`。
- [`engine.statement_runtime.resolve_rule_metadata()`](engine/statement_runtime.py:180) 通过命名规则和 evidence metadata 解析元数据。
- [`engine.statement_runtime._family_id_for_rule()`](engine/statement_runtime.py:258) 当前将 `rule_id` 前缀拼成 `FAM-*`，例如报告样例中的 `FAM-M1-D-001`，这与 Phase-1000 family lane 中的 `FAM-001` 等治理 family 不同。
- [`engine.statement_runtime._canon_for_rule()`](engine/statement_runtime.py:289) 和 [`engine.statement_runtime._rule_type_for_rule()`](engine/statement_runtime.py:307) 也是运行期启发式映射。
- [`META/statement-runtime-implementation-report.md`](META/statement-runtime-implementation-report.md:95) 已声明：多规则拆行未完成；[`family_id`](META/statement-runtime-implementation-report.md:96)、`canon`、`rule_type` 当前由 runtime 命名规则解析生成；[`confidence_snapshot`](META/statement-runtime-implementation-report.md:97) 尚未接入 Dynamic Confidence。

判定：

| 子项 | 状态 |
|---|---|
| record 字段存在性 | 设计满足；临时样例 `missing_field_count=0`。 |
| 正式 case 文件存在 | 不满足；正式 [`cases/`](cases/) 下 `statement_records.json` 数量为 0。 |
| `rule_id -> family_id` 映射到 Phase-1000 family lane | 不满足；当前 runtime family 不是 [`META/phase-1000-dynamic-confidence-init/family_lane_mapping.csv`](META/phase-1000-dynamic-confidence-init/family_lane_mapping.csv:1) 的 `FAM-001` 体系。 |
| feedback ingest 可消费这些字段 | 不满足。 |

## 5. 检查项 C：是否已经能够形成 learning sample

目标 learning sample：

```text
statement_id
rule_id
family_id
school
canon
rule_type
verdict
```

结论：**标准 learning sample 尚未在生产入口形成。**

当前实际链路：

```text
feedback.md
  -> parse_statement_feedback
  -> statement_id
  -> statement_index.json / statement_rule_map.json
  -> rule_id
  -> _apply_rule_verdicts
  -> rule hits/misses + confidence_cache
```

缺失链路：

```text
feedback.md
  -> statement_id
  -> statement_records.json
  -> rule_id + family_id + school + canon + rule_type + confidence_snapshot
  -> learning sample gate
  -> dynamic confidence update / audit log
```

关键阻塞：

1. [`tools.feedback_ingest.ingest()`](tools/feedback_ingest.py:618) 没有 record-first join。
2. [`tools.feedback_loop.VerdictContext`](tools/feedback_loop.py:441) 没有 `family_id / canon / rule_type` 字段。
3. [`tools.feedback_loop.RuleUpdate.to_dict()`](tools/feedback_loop.py:424) 审计输出不包含 `family_id / canon / rule_type`。
4. [`engine/application/artifact_inventory.py`](engine/application/artifact_inventory.py:26) 没有把 [`statement_records.json`](cases:1) 加入 production required artifacts。
5. [`engine/application/recompute.py`](engine/application/recompute.py:126) 的 hard gate 仍只检查 [`statement_index.json`](cases:1) 与 feedback binding，不检查 [`statement_records.json`](cases:1)。

## 6. 检查项 D：554 feedback rows 可恢复统计

数据源：[`META/phase-1000-dynamic-confidence-init/rule_statement_family_alignment.csv`](META/phase-1000-dynamic-confidence-init/rule_statement_family_alignment.csv:1)。

运行统计结果：

| 指标 | 数量 | 占比 |
|---|---:|---:|
| total feedback rows | 554 | 100.00% |
| `needs_mapping_repair=true` | 554 | 100.00% |
| `case_fallback=true` | 554 | 100.00% |
| strict learnable rows | 0 | 0.00% |
| non-pending verdict rows | 217 | 39.17% |
| mapped `rule_id` rows | 20 | 3.61% |
| `rule_id=UNMAPPED` rows | 534 | 96.39% |
| unique cases | 100 | - |

verdict 分布：

| verdict | 数量 |
|---|---:|
| `y` | 183 |
| `n` | 34 |
| `pending` | 294 |
| `skip` | 43 |

严格 recoverable 定义：同时满足以下条件：

1. `needs_mapping_repair != true`；
2. `rule_id` 非空且不是 `UNMAPPED`；
3. `statement_id` 非空且不是 `UNMAPPED-*`；
4. `family_ids / school / canon / rule_type` 均非空且不是 `UNMAPPED`；
5. `feedback_verdict` 是可学习 hit/miss 类 verdict。

按该定义：**recoverable = 0 / 554 = 0.00%**。

解释：虽然有 217 条非 pending 反馈、20 条带 `rule_id`，但初始化副本中 554 条全部带 `case_fallback=true` 与 `needs_mapping_repair=true`。这些行不能直接进入 Dynamic Confidence，否则会把 fallback 生成的 `UNMAPPED-*` statement 与不完整 family/canon/rule_type 当成真实学习样本。

## 7. 检查项 E：Phase-1000 状态判定

最终判定：**`BLOCKED`。**

不得标记为 `READY_FOR_BRIDGE`，原因如下：

| Gate | 期望 | 当前状态 | 判定 |
|---|---|---|---|
| artifact 存在 | 正式 case 有 [`statement_records.json`](cases:1) | 0 个正式文件 | FAIL |
| schema 完整 | 每条 record 有完整字段 | 临时样例满足，正式 case 未落盘 | FAIL |
| feedback join | feedback 通过 `statement_id` join record | 仍 join [`statement_index.json`](cases:1) | FAIL |
| rule metadata | `rule_id -> family_id/school/canon/rule_type` 可学习 | runtime 启发式，未接入 Phase-1000 family lane | FAIL |
| learning sample | 形成标准 7 字段 sample | 当前没有 sample builder/gate | FAIL |
| hard gate | production/recompute 缺 record 即失败 | required artifacts 未包含 record | FAIL |
| 554 rows 恢复 | 历史样本可安全恢复 | strict recoverable 0.00% | FAIL |
| legacy 隔离 | fallback 不进入标准 Beta | 现有 fallback 可走旧 `_apply_rule_verdicts` | FAIL |

## 8. 最小解除阻塞条件

Phase-1000 可从 `BLOCKED` 转为 `READY_FOR_BRIDGE` 的最小条件：

1. [`tools.feedback_ingest.ingest()`](tools/feedback_ingest.py:618) 改为优先读取 [`statement_records.json`](cases:1)。
2. 构建 record-first join：`feedback.statement_id -> records[statement_id] -> rule_id/family_id/school/canon/rule_type`。
3. 只有完整 record 能产生 learning sample；legacy [`statement_index.json`](cases:1) / [`statement_rule_map.json`](cases:1) 只能进入 candidate 或 dry-run，不得静默更新标准 Dynamic Confidence。
4. [`tools.feedback_loop.VerdictContext`](tools/feedback_loop.py:441) 或新增 learning sample 数据结构需要保留 `family_id / canon / rule_type`。
5. [`tools.feedback_loop.RuleUpdate.to_dict()`](tools/feedback_loop.py:424) 和 iteration audit 需要记录 `statement_id -> statement_record -> rule_id -> family_id -> school -> canon -> rule_type`。
6. [`engine/application/artifact_inventory.py`](engine/application/artifact_inventory.py:26) 将 [`statement_records.json`](cases:1) 加入 required artifacts。
7. [`engine/application/recompute.py`](engine/application/recompute.py:126) hard gate 增加 record presence、schema completeness、feedback-to-record join check。
8. 至少 2-3 个正式新 case 完成：report render -> [`statement_records.json`](cases:1) 落盘 -> feedback hit/miss -> ingest dry-run -> learning sample 审计。
9. 对 554 历史 rows 保持 repair queue；不因 P5-4 runtime 存在而自动迁移。

## 9. 本次只读限制核对

本次审计未修改以下禁止范围：

- 未修改 [`engine/`](engine/)；
- 未修改 [`theory/`](theory/)；
- 未修改 [`tests/`](tests/)；
- 未修改 [`META/project-state.json`](META/project-state.json:1)；
- 未写入学习结果；
- 未更新权重；
- 仅新增本审计报告 [`META/dynamic-confidence-bridge-audit.md`](META/dynamic-confidence-bridge-audit.md)。
