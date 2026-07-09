# Feedback Attachment Run ID Match Design

## Goal

让 `tools.feedback_ingest._validate_v5_feedback_attachment()` 在同一 case 目录存在多个 `*.run.json` 时，按 `feedback-attachment.json` 中的 `run_id` 精确选择对应 `V5RunSnapshot`，避免误选最新 run snapshot 导致 false mismatch。

## Scope

本阶段只做最小修正：

- 仍然选择最新的 `*.feedback-attachment.json` 作为本次校验对象。
- 先解析 `V5FeedbackAttachment`，读取 `attachment.run_id`。
- 遍历同目录 `*.run.json`，加载 `V5RunSnapshot`，选择 `snapshot.run_id == attachment.run_id` 的文件。
- 若没有匹配的 run snapshot，返回 summary-only 问题，不抛错、不阻断 ingest。
- 保持现有 summary schema 不变。

本阶段不做：

- 不扩展 `V5FeedbackAttachment` schema。
- 不通过 `V5CaseManifest` 查找 artifact binding。
- 不解析 report Markdown。
- 不改变 statement feedback、prediction feedback、Dynamic Confidence 或规则学习逻辑。
- 不新增 service/repository/helper 文件。

## Architecture

继续使用 `tools/feedback_ingest.py` 内的最小 helper。把当前“按 mtime 取最新 run snapshot”改为“两段式选择”：

1. 读取最新 attachment。
2. 用 attachment.run_id 在 run snapshots 中找匹配项。

这不改变 `ingest()` 对 helper 的调用方式，也不改变 `IngestResult.phase_a_learning_summary["v5_feedback_attachment"]` 的结构。

## Data Flow

```text
case_dir
  -> newest *.feedback-attachment.json
  -> V5FeedbackAttachment.from_json()
  -> attachment.run_id
  -> scan *.run.json
  -> V5RunSnapshot.from_json()
  -> first snapshot where snapshot.run_id == attachment.run_id
  -> existing case/run/target validation
  -> existing summary shape
```

## Summary Behavior

保留现有字段：

```json
{
  "status": "ok | missing | invalid | mismatch",
  "attachment_path": "...",
  "run_snapshot_path": "...",
  "case_id": "...",
  "run_id": "...",
  "target_counts": {
    "claims": 0,
    "predictions": 0,
    "signals": 0
  },
  "issues": []
}
```

新增/明确语义：

- attachment 解析失败：`status=invalid`。
- 没有任何 `*.run.json`：`status=missing`，issue 为 `run snapshot not found`。
- 存在 `*.run.json` 但没有任何 `snapshot.run_id == attachment.run_id`：`status=mismatch`，issue 为 `run snapshot for feedback attachment run_id not found: <run_id>`。
- 存在匹配 run snapshot：继续执行既有 `case_id`、`run_id`、target IDs 校验。

## Error Handling

- 单个 run snapshot JSON 无法解析时，跳过该文件并继续扫描其他 `*.run.json`。
- 如果所有 run snapshot 都无法解析且没有匹配，返回 `mismatch` 并把无效文件摘要写入 `issues`。
- 所有错误都只进入 summary，不抛出，不改变 ingest 成败条件。

## Test Plan

扩展 `tests/v1_3_acceptance/test_h3_feedback_parsing.py`：

1. 多 run 场景：较新的 `wrong.run.json` 与 attachment.run_id 不匹配，较旧的 `right.run.json` 匹配；summary 应为 `ok`，`run_snapshot_path` 应等于 right path。
2. 存在 run snapshots 但没有匹配 run_id；summary 应为 `mismatch`，issues 包含 `run snapshot for feedback attachment run_id not found`。
3. 保留既有 helper 与 ingest 测试不变。

## Success Criteria

- 多 run case 不再因最新 snapshot 非目标 run 而产生 false mismatch。
- summary schema 不变。
- 缺少 / 无效 / 不匹配状态仍不阻断 ingest。
- 现有目标验证保持通过。

## Self-Review

- Placeholder scan: 无 `TBD` / `TODO`。
- Internal consistency: 目标、数据流、错误语义都围绕 run_id 精确匹配。
- Scope check: 单一 helper 内部选择策略调整，适合一个实现计划。
- Ambiguity check: no run file、no matching run_id、invalid run file 三种语义已区分。