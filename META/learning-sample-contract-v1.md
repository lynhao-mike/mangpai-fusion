# P6-1 Learning Sample Contract v1

生成时间：2026-06-13（Asia/Shanghai）

## 1. Contract Name

契约名：`learning_sample.v1`

用途：定义从 [`statement_records.json`](../cases/) 与 [`feedback.md`](../cases/) 生成、供未来 Dynamic Confidence 消费的最小学习样本。

本契约只定义学习输入，不更新权重、不执行学习、不修改生产规则。

## 2. Required Fields

`learning_sample.v1` 必须包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `sample_id` | string | 是 | 样本唯一 ID，建议由 `case_id + statement_id + rule_id + feedback_time` 稳定哈希生成。 |
| `case_id` | string | 是 | 标准 case 目录名。 |
| `statement_id` | string | 是 | 反馈标注指向的断语 ID，必须来自同源 [`statement_records.json`](../cases/)。 |
| `rule_id` | string | 是 | 单条学习样本绑定的生产规则 ID。 |
| `family_id` | string | 是 | 规则家族 ID，用于 family 级去重、聚合与校准。 |
| `school` | string | 是 | 派别 / 专家体系归属。 |
| `canon` | string | 是 | 经典 / 来源 / canon lane。 |
| `rule_type` | string | 是 | 规则类型，用于治理与分层统计。 |
| `verdict` | string | 是 | 反馈裁决，只允许学习型 verdict。 |
| `feedback_time` | string | 是 | 反馈进入学习通道的 UTC ISO-8601 时间。 |
| `confidence_snapshot` | object | 是 | 断语生成时冻结的置信度快照。 |
| `generated_at` | string | 是 | learning sample 生成时间，UTC ISO-8601。 |

## 3. JSON Shape

```json
{
  "schema_version": "learning_sample.v1",
  "sample_id": "LS-...",
  "case_id": "C-YYYY-NNN-乾-四柱",
  "statement_id": "S-...",
  "rule_id": "...",
  "family_id": "FAM-...",
  "school": "...",
  "canon": "...",
  "rule_type": "...",
  "verdict": "hit",
  "feedback_time": "2026-06-13T00:00:00Z",
  "confidence_snapshot": {
    "star": 4,
    "percent": 78.0,
    "posterior_mean": null,
    "sample_n": 0,
    "source": "static_rule"
  },
  "generated_at": "2026-06-13T00:00:00Z"
}
```

## 4. Verdict Mapping

学习样本只接受可学习 verdict：

| feedback annotation | parser verdict | learning verdict | 是否进入学习 |
|---|---|---|---|
| `[y]` | `hit` | `hit` | 是 |
| `[n]` | `miss` | `miss` | 是 |
| `[?]` | `no_data` | 不生成 | 否 |
| `[skip]` | `no_data` | 不生成 | 否 |

`pending`、`no_data`、`skip`、未知标注不得进入 `learning_samples.json` 的可学习数组，但可以进入 readiness diagnostics。

## 5. Field Semantics

### 5.1 `sample_id`

建议生成公式：

```text
LS-<sha256(case_id + "|" + statement_id + "|" + rule_id + "|" + feedback_time)[:16]>
```

要求：

- 同一次 feedback ingest 内稳定；
- 同一 `statement_id + rule_id` 后续重新反馈时，可通过不同 `feedback_time` 形成新事件；
- 若未来要“最后反馈覆盖前反馈”，应在 builder 层明确去重策略，而不是改变本字段语义。

### 5.2 `case_id`

必须等于 case 目录名，例如：

```text
cases/<case_id>/learning_samples.json
```

### 5.3 `statement_id`

必须满足：

1. 来自 [`feedback.md`](../cases/) 的结构化标注；
2. 能在同 case 的 [`statement_records.json`](../cases/) 中找到；
3. 不得是 fallback、UNMAPPED 或人工临时行号。

### 5.4 `rule_id / family_id / school / canon / rule_type`

必须全部从同一条 statement record 继承，不允许从 feedback 文本猜测。

任一字段为空、缺失或以 `UNMAPPED` 开头，则该 feedback row 标记为 `not learnable`。

### 5.5 `confidence_snapshot`

必须来自 statement record 的生成期快照，避免未来 Dynamic Confidence 更新后污染历史样本解释。

最低字段：

- `star`
- `percent`
- `posterior_mean`
- `sample_n`
- `source`

### 5.6 `feedback_time`

来源优先级：

1. feedback 文件内显式时间；
2. ingest / builder 运行时间；
3. 文件 mtime 只能作为诊断字段，不建议作为正式 feedback_time。

### 5.7 `generated_at`

指 `learning_sample_builder` 生成样本的时间，不等于断语生成时间，也不等于反馈发生时间。

## 6. Storage Envelope

[`cases/<case_id>/learning_samples.json`](../cases/) 建议使用 envelope：

```json
{
  "schema_version": "learning_samples.v1",
  "case_id": "C-YYYY-NNN-乾-四柱",
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
    "missing_required_field_rows": 0
  },
  "not_learnable": []
}
```

## 7. Non-Learnable Row Contract

不可学习 row 应保留诊断：

```json
{
  "statement_id": "S-...",
  "verdict": "no_data",
  "reason": "pending_or_no_data",
  "missing_fields": []
}
```

允许 reason：

| reason | 说明 |
|---|---|
| `statement_id_not_found` | feedback 指向的 statement_id 不存在于 record。 |
| `missing_required_fields` | record 缺少学习必需字段。 |
| `unmapped_field` | 字段为 `UNMAPPED` 或 fallback 值。 |
| `pending_or_no_data` | verdict 不是 hit/miss。 |
| `invalid_verdict` | 标注无法映射到学习 verdict。 |

## 8. Boundary Rules

1. 历史 feedback 不自动生成 `learning_sample.v1`。
2. `statement_index.json` 只能作为展示索引和辅助审计，不作为学习事实源。
3. 一条 learning sample 只绑定一个 `rule_id`。
4. 多规则支撑同一可见断语时，必须在 statement record 层拆分，不能在 learning sample 层隐式 fanout。
5. 生成 learning sample 不等于执行 Dynamic Confidence。

## 9. P6-1 判定

契约已定义，但运行时尚未正式落盘 [`learning_samples.json`](../cases/)。因此当前状态为：**CONTRACT_READY / RUNTIME_BLOCKED**。
