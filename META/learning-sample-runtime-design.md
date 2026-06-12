# P6-1 Learning Sample Runtime Builder Design

生成时间：2026-06-13（Asia/Shanghai）

## 1. 目的

设计 `learning_sample_builder` 的运行期形态：

- 输入：[`cases/<case_id>/statement_records.json`](../cases/) 与 [`cases/<case_id>/feedback.md`](../cases/)。
- 输出：[`cases/<case_id>/learning_samples.json`](../cases/)。
- 行为：只生成学习样本；不更新权重、不执行 Dynamic Confidence、不修改生产规则。

## 2. 设计原则

1. **record-first**：以 [`statement_records.json`](../cases/) 为唯一学习事实源；legacy [`statement_index.json`](../cases/) 与 [`statement_rule_map.json`](../cases/) 只用于诊断与审计。
2. **schema 严格**：输出符合 [`META/learning-sample-contract-v1.md`](learning-sample-contract-v1.md)。
3. **dry-run 优先**：默认 `dry_run=True`，不写盘；只有 `--commit` 显式开启才落盘。
4. **单 case 单文件**：每个 case 目录独立落盘，文件名固定为 `learning_samples.json`。
5. **不读迭代状态**：本 builder 不更新 [`META/iteration-state.json`](iteration-state.json)、不触发 iteration_report。
6. **可重复执行**：同一 (case, statement_id, rule_id, feedback_time) 重跑应保持稳定 sample_id。

## 3. 输入接口

### 3.1 命令行

```text
python -m tools.learning_sample_builder <case_id> [--dry-run] [--commit]
```

- `case_id`：必填，case 目录名或唯一前缀。
- `--dry-run`：默认行为；不写 learning_samples.json，只输出 diagnostics。
- `--commit`：允许落盘；无此标志时永远不写。

### 3.2 依赖输入

| 路径 | 用途 | 缺失时行为 |
|---|---|---|
| `cases/<case_id>/input.md` | 校验 case 存在；不读取 | 缺失：直接拒绝运行 |
| `cases/<case_id>/statement_records.json` | 主学习事实源 | 缺失：返回 `no_records`，`samples=0` |
| `cases/<case_id>/feedback.md` | 反馈标注来源 | 缺失：返回 `no_feedback`，`samples=0` |

### 3.3 解析器

复用 [`engine.application.feedback_parser.parse_statement_feedback()`](../engine/application/feedback_parser.py) 解析 `[S-...] [y/n/?/skip]`。

## 4. 输出接口

### 4.1 落盘路径

```text
cases/<case_id>/learning_samples.json
```

### 4.2 envelope

```json
{
  "schema_version": "learning_samples.v1",
  "case_id": "C-2026-XXX-乾-四柱",
  "generated_at": "2026-06-13T00:00:00Z",
  "source_files": {
    "statement_records": "statement_records.json",
    "feedback": "feedback.md"
  },
  "samples": [],
  "diagnostics": {
    "feedback_rows": 0,
    "learnable_samples": 0,
    "not_learnable_rows": 0,
    "pending_rows": 0,
    "missing_required_field_rows": 0,
    "unmapped_field_rows": 0
  },
  "not_learnable": []
}
```

### 4.3 CLI 文本输出

```text
learning_sample_builder
  case_id: C-2026-XXX-乾-四柱
  dry_run: true
  feedback_rows: 12
  learnable_samples: 8
  not_learnable_rows: 4
  pending_rows: 2
  missing_required_field_rows: 1
  unmapped_field_rows: 1
  output: cases/<case_id>/learning_samples.json (not written, dry-run)
```

## 5. 内部流程

```text
1. resolve_case_dir(case_id)
2. read statement_records.json
3. read feedback.md
4. parse_statement_feedback(feedback_text)
5. for each feedback row:
     a. find record = statement_records[statement_id]
     b. check required fields (rule_id/family_id/school/canon/rule_type)
     c. check verdict ∈ {hit, miss}
     d. if all pass:
          build learning_sample.v1 row
          add to samples[]
        else:
          build not_learnable row with reason
          add to not_learnable[]
6. compute diagnostics counters
7. if --commit and dry_run=False:
     write envelope to cases/<case_id>/learning_samples.json
8. return BuildResult
```

## 6. 关键数据形态

### 6.1 BuildResult

```python
@dataclass
class BuildResult:
    case_id: str
    dry_run: bool
    feedback_rows: int
    learnable_samples: int
    not_learnable_rows: int
    pending_rows: int
    missing_required_field_rows: int
    unmapped_field_rows: int
    samples: list[dict]
    not_learnable: list[dict]
    output_path: str | None
    error_message: str | None = None
```

### 6.2 learning_sample.v1 字段映射

| sample 字段 | 来源 |
|---|---|
| `sample_id` | `LS-<sha256(case_id|statement_id|rule_id|feedback_time)[:16]>` |
| `case_id` | 输入 case 目录名 |
| `statement_id` | feedback row |
| `rule_id` | statement_records.records[statement_id].rule_id |
| `family_id` | statement_records.records[statement_id].family_id |
| `school` | statement_records.records[statement_id].school |
| `canon` | statement_records.records[statement_id].canon |
| `rule_type` | statement_records.records[statement_id].rule_type |
| `verdict` | `hit` / `miss`（与 parser verdict 一致） |
| `feedback_time` | feedback 标注时间或 builder 运行时间 |
| `confidence_snapshot` | statement_records.records[statement_id].confidence_snapshot |
| `generated_at` | builder 当前时间 |

### 6.3 not_learnable row

```json
{
  "statement_id": "S-...",
  "verdict": "no_data",
  "annotation": "?",
  "reason": "pending_or_no_data",
  "missing_fields": ["family_id"]
}
```

reason 取值见 [`META/learning-sample-contract-v1.md`](learning-sample-contract-v1.md) § 7。

## 7. 失败与边界

| 场景 | 行为 |
|---|---|
| 缺失 statement_records.json | 终止；返回 `no_records` 错误。 |
| statement_records 缺字段 | 该 record 标记为 `not_learnable`；不影响其它 record。 |
| 缺失 feedback.md | 终止；返回 `no_feedback` 错误。 |
| verdict = `no_data` | 不进入 samples；进入 not_learnable。 |
| 同一 statement_id 多次反馈 | 保留全部样本；sample_id 仍按 feedback_time 区分。 |
| 与 [`tools/feedback_ingest.py`](../tools/feedback_ingest.py) 冲突 | builder 不触发 `_apply_rule_verdicts`；保证学习样本与现有规则级更新互不耦合。 |
| 跨 case 批量 | 本阶段不支持；如需批量，未来由 `tools/learning_sample_batch.py` 调用本 builder。 |

## 8. 与其它工具的关系

| 工具 | 关系 |
|---|---|
| [`tools/feedback_ingest.py`](../tools/feedback_ingest.py) | 仍负责规则级 `_apply_rule_verdicts` 与 iteration 计数；不修改。 |
| [`tools/render_report.py`](../tools/render_report.py) | 仍负责 `statement_records.json` 与 `statement_index.json` 落盘；不修改。 |
| [`tools/feedback_readiness_check.py`](../tools/feedback_readiness_check.py)（待 P6-2 实现） | 读取本 builder 的输出做 `not_learnable` 分类审计。 |
| [`tools/learning_readiness_metric.py`](../tools/learning_readiness_metric.py)（待 P6-2 实现） | 聚合 `learnable_samples` / `y+n` / `pending` 计算 ready_for_learning。 |

## 9. 安全约束

1. builder 默认拒绝 `--commit`，必须显式开启。
2. builder 不写 `feedback.md`、不写 `statement_records.json`、不写 `statement_index.json`。
3. builder 不调用 [`tools/feedback_loop._apply_rule_verdicts()`](../tools/feedback_loop.py)。
4. builder 不修改 [`META/iteration-state.json`](iteration-state.json)、[`META/project-state.json`](project-state.json)。
5. builder 错误信息不得包含 verdict 计数以外的 statistics，以避免被当作学习结果引用。
