# P6-1 Learning Lane Audit

生成时间：2026-06-13（Asia/Shanghai）

## 1. 审计结论

最终判断：**BLOCKED**。

P6-1 的核心学习通道已经出现“生成期 record-first”雏形，但尚未形成完整闭环：

```text
report
  -> statement_records.json
  -> feedback ingest
  -> learning sample
  -> Dynamic Confidence
```

当前连通状态如下：

| 环节 | 当前状态 | 判定 |
|---|---|---|
| report -> statement_records.json | [`tools/render_report.py`](../tools/render_report.py) 调用 [`engine/statement_runtime.py`](../engine/statement_runtime.py) 写入 record；全量正式 case 已存在 [`statement_records.json`](../cases/) | PASS |
| statement_records.json schema | 当前 127 个正式 case 共 17,268 条 record，汇总缺字段数为 0 | PASS |
| feedback.md -> structured feedback | [`engine/application/feedback_parser.py`](../engine/application/feedback_parser.py) 可解析 `[S-...] [y/n/?/skip]` | PASS |
| feedback -> statement_records join | 全量扫描 54 条结构化 feedback 均未映射到 record，mapped=0，unmapped=54 | FAIL |
| learning sample builder | [`tools/feedback_ingest.py`](../tools/feedback_ingest.py) 已有 `build_learning_samples()`，但输出仍是临时 7 字段子集，未落盘到 case 目录 | PARTIAL |
| Dynamic Confidence | 本阶段禁止执行学习；当前入口仍会调用现有规则级 `_apply_rule_verdicts()`，但 learning sample 未成为独立正式输入 | BLOCKED |

## 2. 审计范围

只读审计以下路径：

- [`engine/statement_runtime.py`](../engine/statement_runtime.py)
- [`tools/render_report.py`](../tools/render_report.py)
- [`tools/feedback_ingest.py`](../tools/feedback_ingest.py)
- [`engine/application/feedback_parser.py`](../engine/application/feedback_parser.py)
- [`cases/`](../cases/)
- [`reports/`](../reports/)
- 既有 [`META/`](./) 审计文档

未修改：

- [`theory/`](../theory/)
- [`META/project-state.json`](project-state.json)
- 任何权重、规则或 Dynamic Confidence 状态

## 3. 当前全量状态

只读扫描正式 [`cases/`](../cases/) 目录，排除模板与 raw feedback：

| 指标 | 数量 |
|---|---:|
| 正式 case 数 | 127 |
| 有 report 归档的 case | 46 |
| 有 statement_index.json 的 case | 127 |
| 有 statement_records.json 的 case | 127 |
| statement_records 总数 | 17,268 |
| record 缺字段数 | 0 |
| 结构化 feedback rows | 54 |
| learnable samples | 0 |
| mapped feedback rows | 0 |
| unmapped feedback rows | 54 |
| pending/no_data rows | 32 |

## 4. 链路逐段判断

### 4.1 report -> statement_records.json

[`tools/render_report.py`](../tools/render_report.py) 在渲染报告时调用 [`engine.statement_runtime.write_statement_records()`](../engine/statement_runtime.py)，并同步写入：

- [`cases/<case_id>/statement_records.json`](../cases/)
- [`cases/<case_id>/statement_index.json`](../cases/)

该段已连通。

### 4.2 statement_records.json -> Feedback

record 已存在，但现有反馈标注与 record 的 `statement_id` 仍不匹配。全量 54 条结构化反馈全部落入 `statement_id_not_found_or_incomplete_statement_record`。

原因判断：

1. 历史 feedback 与当前 statement_records 不同源、不同版本。
2. feedback 行中的 `statement_id` 不是新生成 record 的稳定 ID。
3. 历史案例已被 P5-8 判定退出学习通道，本阶段不能把它们强行修复为 learnable sample。

### 4.3 Feedback -> Learning Sample

[`tools.feedback_ingest.build_learning_samples()`](../tools/feedback_ingest.py) 已能按以下门禁生成样本：

```text
feedback.statement_id
  -> statement_records.records[statement_id]
  -> rule_id / family_id / school / canon / rule_type
  -> verdict != no_data
```

但当前输出没有写入 [`cases/<case_id>/learning_samples.json`](../cases/)，且字段尚未达到 `learning_sample.v1` 完整契约。

### 4.4 Learning Sample -> Dynamic Confidence

本阶段禁止执行学习。当前应保持“准备态”：

- 可生成样本；
- 可计算 ready metric；
- 不更新权重；
- 不修改生产规则；
- 不执行 Dynamic Confidence。

## 5. 缺口清单

| 缺口 | 影响 | P6-2 前置要求 |
|---|---|---|
| 新 feedback 与新 statement_records 尚无 live y/n 闭环样本 | learnable_samples=0 | 至少生成新案、填入基于新 report 的 `[S-...] [y/n]` feedback |
| learning sample 未落盘 | Dynamic Confidence 无正式输入制品 | 新增 runtime builder 输出 [`learning_samples.json`](../cases/) |
| `learning_sample.v1` 未固化为运行时契约 | 字段口径可能漂移 | 使用 [`META/learning-sample-contract-v1.md`](learning-sample-contract-v1.md) |
| readiness checker 未实现为工具 | not learnable 原因不可批量审计 | 按 [`META/feedback-readiness-gate.md`](feedback-readiness-gate.md) 实现 checker |
| ready_for_learning 只有设计，未接入 metrics | 无法判断何时启动 Dynamic Confidence | 按 [`META/dynamic-confidence-readiness.md`](dynamic-confidence-readiness.md) 接入只读统计 |

## 6. P6-1 结论

**BLOCKED**。

阻塞原因不是 `statement_records.json` 不存在，而是缺少“新生成案例 + 同源反馈 + learning_samples.json 落盘”的首批 live sample。历史 feedback 明确退出学习通道，因此当前 54 条结构化反馈全部不可作为 Dynamic Confidence 学习样本。

P6-2 启动条件：先按本文后续 5 份契约实现 runtime builder 与 readiness checker，并用新生成案例产生至少 1 个同源 `y/n` learning sample，再进入 Dynamic Confidence 的只读 dry-run 验证。
