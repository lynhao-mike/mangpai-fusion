# P6-1 Dynamic Confidence Readiness Metric

生成时间：2026-06-13（Asia/Shanghai）

## 1. 目的

定义 `ready_for_learning` 指标，用于判定当前学习通道是否具备 Dynamic Confidence 启动条件。

本指标只读，不更新权重，不执行学习，不修改生产规则。

## 2. 三个硬条件

`ready_for_learning = True` 必须同时满足：

| 条件 | 阈值 | 含义 |
|---|---:|---|
| `learnable_samples >= 50` | 50 | 通过 [`META/learning-sample-contract-v1.md`](learning-sample-contract-v1.md) 的 `learning_sample.v1` 数量下限。 |
| `y + n >= 30` | 30 | hit + miss 实际反馈数下限，避免单一 verdict 偏差。 |
| `pending < 50%` | 50% | `no_data`（含 `?` 与 `skip`）相对 feedback_rows 占比 < 50%。 |

任一不满足，判定为 `BLOCKED`。

## 3. 指标公式

```text
learnable_samples = count(samples.verdict ∈ {hit, miss})
y                 = count(samples.verdict == "hit")
n                 = count(samples.verdict == "miss")
yn                = y + n
pending           = count(feedback.verdict == "no_data")
total_feedback    = count(feedback_rows)
pending_ratio     = pending / total_feedback    # 缺失时定义 pending_ratio = 1
```

## 4. 阈值含义

1. `learnable_samples >= 50`
   - 学习样本太少时，命中估计方差过大，规则级 Beta 与 family 校准不可信。
2. `y + n >= 30`
   - 即便总样本足够，y/n 单边膨胀同样会污染 Beta 后验。
3. `pending < 50%`
   - 大量 `?` 或 `skip` 表示反馈标注质量不足；必须先提升人工反馈质量再启动学习。

## 5. 状态枚举

| 状态 | 含义 | 触发条件 |
|---|---|---|
| `READY_FOR_LEARNING` | 全部三个硬条件满足 | 可进入 Dynamic Confidence 启动演练。 |
| `BLOCKED_SAMPLE_LOW` | learnable_samples 不足 | 等待新案 ingest 或新反馈标注。 |
| `BLOCKED_YN_LOW` | y+n 不足 | 等待命理师补全 hit/miss 标注。 |
| `BLOCKED_PENDING_HIGH` | pending 占比过高 | 等待命理师重标 `?` / `skip` 为 `y` / `n`。 |
| `BLOCKED_MULTIPLE` | 多项不满足 | 按上述优先级从高到低提示。 |

## 6. 指标采集与落盘

输出位置：

```text
META/dynamic-confidence-readiness.json
```

形态（建议）：

```json
{
  "schema_version": "dynamic-confidence-readiness/v0.1",
  "generated_at": "2026-06-13T00:00:00Z",
  "status": "BLOCKED_SAMPLE_LOW",
  "learnable_samples": 0,
  "y": 0,
  "n": 0,
  "yn": 0,
  "pending": 32,
  "total_feedback": 54,
  "pending_ratio": 0.5926,
  "thresholds": {
    "learnable_samples_min": 50,
    "yn_min": 30,
    "pending_max_ratio": 0.5
  },
  "gate_results": {
    "learnable_samples_pass": false,
    "yn_pass": false,
    "pending_pass": false
  },
  "blocking_reasons": [
    "learnable_samples < 50",
    "y + n < 30"
  ]
}
```

## 7. 当前 P6-1 模拟值

只读扫描 [`cases/`](../cases/) 全部 127 个正式 case：

| 指标 | 当前值 | 阈值 | 状态 |
|---|---:|---:|---|
| learnable_samples | 0 | >= 50 | BLOCKED_SAMPLE_LOW |
| y | 0 | - | - |
| n | 0 | - | - |
| y + n | 0 | >= 30 | BLOCKED_YN_LOW |
| pending | 32 | - | - |
| total_feedback | 54 | - | - |
| pending_ratio | 0.5926 | < 0.5 | BLOCKED_PENDING_HIGH |

整体判定：**`BLOCKED_MULTIPLE`**。

阻塞主因：

1. 历史 54 条结构化 feedback 全部未匹配到 [`statement_records.json`](../cases/) → learnable_samples = 0。
2. y + n = 0，远低于 30。
3. pending 占比 59.26%，超过 50% 红线。

## 8. P6-2 启动条件

必须同时满足：

- `learnable_samples >= 50`（来自新案 learning_samples.json）。
- `y + n >= 30`。
- `pending_ratio < 0.5`。
- 至少 3 个新生成案例完成：`report render -> statement_records.json -> feedback.md -> builder -> learning_samples.json`。
