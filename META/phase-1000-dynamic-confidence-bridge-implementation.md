# P5-6 Dynamic Confidence Bridge Implementation

生成时间：2026-06-12

## 1. 实施结论

结论：**Phase-1000 bridge readiness = `BLOCKED`**。

本次已完成 Dynamic Confidence Bridge 的入口接线实现：[`tools/feedback_ingest.py`](../tools/feedback_ingest.py:1) 现在以 [`statement_records.json`](../cases:1) 作为 record-first 学习事实源，替换 legacy [`statement_index.json`](../cases:1) / [`statement_rule_map.json`](../cases:1) fanout 作为 Dynamic Confidence 映射来源。

但当前正式 [`cases/`](../cases:1) 下仍未发现已归档 [`statement_records.json`](../cases:1)，且 Phase-1000 现有 554 rows 初始化副本仍全部 `needs_mapping_repair=true`，因此安全可学习样本为 0。

## 2. 本次改动范围

| 文件 | 改动 | 审计说明 |
|---|---|---|
| [`tools/feedback_ingest.py`](../tools/feedback_ingest.py:1) | 新增 record-first bridge sample gate；fanout 改为读取 [`statement_records.json`](../cases:1) | 允许修改工具层；未直接写权重，未更新 Dynamic Confidence |
| [`META/phase-1000-dynamic-confidence-bridge-implementation.md`](phase-1000-dynamic-confidence-bridge-implementation.md:1) | 新增实施与 readiness 报告 | 仅写审计报告 |

未修改禁止范围：[`theory/`](../theory:1)、[`engine/`](../engine:1)、[`tests/`](../tests:1)、[`META/project-state.json`](project-state.json:1)。当前 `git status` 中这些路径若存在改动，属于本任务开始前已有工作区状态，本次未触碰。

## 3. 生成期事实源：statement_records

生成期事实层现状：[`tools/render_report.py`](../tools/render_report.py:194) 已在报告渲染阶段同步调用 [`engine.statement_runtime.write_statement_records()`](../engine/statement_runtime.py:115)，将 record envelope 写入：

```text
cases/<case_id>/statement_records.json
```

每条 record 目标字段包含：

```text
statement_id
rule_id
family_id
school
canon
rule_type
confidence_snapshot
generated_at
```

本次没有修改 [`engine/statement_runtime.py`](../engine/statement_runtime.py:1)，符合禁止修改 [`engine/`](../engine:1) 的约束。

## 4. feedback ingest fanout 修复

### 4.1 修复前

旧链路：

```text
feedback.md
  -> statement_id
  -> statement_index.json
  -> statement_rule_map.json optional merge
  -> rule_ids
  -> _apply_rule_verdicts
```

问题：

1. [`statement_index.json`](../cases:1) 是展示/索引层，不包含完整 `family_id / school / canon / rule_type` 学习字段。
2. [`statement_rule_map.json`](../cases:1) 是 legacy 旁路映射，不能作为 Dynamic Confidence 学习事实源。
3. 无法在 sample gate 前准确标记 `needs_mapping_repair=true`。

### 4.2 修复后

新链路：

```text
feedback.md
  -> statement_id
  -> statement_records.json
  -> rule_id + family_id + school + canon + rule_type
  -> learning sample gate
  -> existing rule-level fanout audit
```

新增行为：

1. [`tools.feedback_ingest.build_learning_samples()`](../tools/feedback_ingest.py:273) 生成只读 learning samples。
2. sample 只保留 7 字段：`statement_id, rule_id, family_id, school, canon, rule_type, verdict`。
3. 未能 join 到完整 statement record 的 row 标记 `needs_mapping_repair=true`，不纳入学习。
4. `pending / ? / skip / no_data` 类反馈不纳入学习样本。
5. [`tools.feedback_ingest.fanout_to_rules()`](../tools/feedback_ingest.py:338) 改为通过 [`statement_records.json`](../cases:1) fanout。
6. [`tools.feedback_ingest.ingest()`](../tools/feedback_ingest.py:715) 的加载步骤改为 `load_statement_records`，不再合并 legacy [`statement_rule_map.json`](../cases:1)。

## 5. Learning sample gate

样本结构：

```text
statement_id, rule_id, family_id, school, canon, rule_type, verdict
```

纳入条件：

1. `statement_id` 能 join 到 [`statement_records.json`](../cases:1)。
2. `rule_id / family_id / school / canon / rule_type` 均存在且不是 `UNMAPPED*`。
3. `verdict` 不是 pending/no_data 类。
4. 不直接写入权重，不直接更新 Dynamic Confidence。

当前 554 rows 中没有符合条件的安全样本，因此可学习 sample 样例为空：

```json
[]
```

## 6. 554 rows feedback 映射统计

数据源：[`META/phase-1000-dynamic-confidence-init/rule_statement_family_alignment.csv`](phase-1000-dynamic-confidence-init/rule_statement_family_alignment.csv:1)。

| 指标 | 数量 | 占比 |
|---|---:|---:|
| total feedback rows | 554 | 100.00% |
| learnable rows | 0 | 0.00% |
| `needs_mapping_repair=true` | 554 | 100.00% |
| unmapped rows | 554 | 100.00% |
| pending / no_data / skip rows | 337 | 60.83% |
| non-pending rows | 217 | 39.17% |

Readiness 判定：

```text
BLOCKED
```

判定规则：

```text
READY_FOR_BRIDGE if recoverable % > 0
BLOCKED otherwise
```

当前 `recoverable % = 0.00%`，因此为 `BLOCKED`。

## 7. 核心阻塞项

1. 正式 [`cases/`](../cases:1) 下当前没有已归档 [`statement_records.json`](../cases:1)，新 bridge 无可 join 的生产 facts。
2. 554 rows 初始化副本全部 `needs_mapping_repair=true`，不能安全迁移为学习样本。
3. 历史 row 的 `statement_id / rule_id / family_id / school / canon / rule_type` 多为 `UNMAPPED` 或 fallback 生成，不可进入 Dynamic Confidence。
4. 需要重新跑新报告渲染或 pipeline 副本生成流程，让每个 case 形成可追踪的 [`statement_records.json`](../cases:1)。

## 8. 验证记录

已执行：

```text
python -m py_compile tools/feedback_ingest.py
```

结果：通过。

已执行只读导入检查：

```text
python -c "from tools.feedback_ingest import build_learning_samples; print('import-ok', callable(build_learning_samples))"
```

结果：`import-ok True`。

已执行只读统计检查：

```text
python -c "... rule_statement_family_alignment.csv stats ..."
```

结果：554 rows、learnable 0、recoverable 0.00%、readiness `BLOCKED`。

## 9. 清理与审计约束核对

| 约束 | 结果 |
|---|---|
| 删除临时生成脚本或副本 | 未创建临时脚本；无临时副本需删除 |
| 不修改 [`theory/`](../theory:1) | 满足 |
| 不修改 [`engine/`](../engine:1) | 本次满足 |
| 不修改 [`tests/`](../tests:1) | 本次满足 |
| 不修改 [`META/project-state.json`](project-state.json:1) | 满足 |
| 不直接写入权重 | 满足 |
| 不更新 Dynamic Confidence | 满足；只生成 sample gate 与统计 |

## 10. 后续解除阻塞的最小路径

1. 使用现有渲染链路为正式 case 生成 [`statement_records.json`](../cases:1)。
2. 对历史 554 rows 做人工/程序化 mapping repair，清除 `needs_mapping_repair=true`。
3. 使用 [`tools.feedback_ingest.build_learning_samples()`](../tools/feedback_ingest.py:273) 进行 dry-run sample gate。
4. 当 recoverable rows > 0 后，Phase-1000 可进入 `READY_FOR_BRIDGE`。
