# Feedback Attachment Ingest Design

## Goal

让 `tools.feedback_ingest.ingest()` 在摄入反馈时消费 `feedback-attachment.json`，但只做只读校验与摘要记录，不改变现有 statement feedback、prediction feedback、Dynamic Confidence 或规则学习逻辑。

## Scope

本阶段只做最小职责：

- 在 case 目录中查找 `*.feedback-attachment.json`。
- 根据 attachment 中的 artifact binding 或同目录文件查找对应 `*.run.json`。
- 加载 `V5FeedbackAttachment` 与 `V5RunSnapshot`。
- 校验 `case_id`、`run_id`、claim target IDs、prediction target IDs、signal target IDs。
- 把校验结果写入 `IngestResult.phase_a_learning_summary["v5_feedback_attachment"]`。

本阶段不做：

- 不解析 report Markdown。
- 不把 attachment 作为规则学习事实源。
- 不替代 `statement_records.json`。
- 不阻断现有 ingest 主流程。
- 不新增独立 service/repository/helper 文件。

## Architecture

采用最小内联路径：在 `tools/feedback_ingest.py` 内新增一个小型只读 helper，例如 `_validate_v5_feedback_attachment(case_dir, full_case_id)`，由 `ingest()` 调用。

该 helper 只依赖标准库 `json/pathlib` 与现有 `engine.v5.domain` 契约：

- `V5FeedbackAttachment.from_json()`
- `V5RunSnapshot.from_json()`
- `V5FeedbackAttachment.validate_targets()`

这保持 operations 层的职责为编排与校验，不把领域真相沉淀进 `tools/`。

## Data Flow

```text
cases/<case_id>/feedback.md
  -> tools.feedback_ingest.ingest()
  -> existing statement/prediction parsing unchanged
  -> optional feedback attachment validation
       *.feedback-attachment.json
       *.run.json
       V5FeedbackAttachment.validate_targets(snapshot)
  -> IngestResult.phase_a_learning_summary.v5_feedback_attachment
```

## Summary Shape

`phase_a_learning_summary["v5_feedback_attachment"]` 使用稳定字典：

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

语义：

- `ok`：attachment 与 run snapshot 均存在且校验通过。
- `missing`：没有 attachment 或没有 run snapshot；不阻断 ingest。
- `invalid`：JSON 无法解析或 schema 无法加载；不阻断 ingest，只记录 issue。
- `mismatch`：case/run/target 校验失败；不阻断 ingest，只记录 issue。

## Error Handling

- 找不到 `feedback-attachment.json`：返回 `status=missing`。
- 找不到 `run.json`：返回 `status=missing`，保留 attachment 路径。
- JSON 解析失败：返回 `status=invalid`，issue 写异常摘要。
- `case_id` 不匹配：返回 `status=mismatch`。
- `run_id` 不匹配：返回 `status=mismatch`。
- target ID 不存在：复用 `V5FeedbackAttachment.validate_targets()` 返回的 issue，状态为 `mismatch`。

所有错误都只进入 summary，不抛出，不改变原有 ingest 成败条件。

## Test Plan

新增或扩展 `tests/v1_3_acceptance/test_h3_feedback_parsing.py`，覆盖纯 helper 与 ingest summary：

1. 有 attachment + run snapshot 且完全匹配 → `status=ok`，target counts 正确。
2. 无 attachment → `status=missing`，现有 ingest dry-run 行为不变。
3. attachment target 缺失 → `status=mismatch`，issues 包含缺失 target。
4. run_id 不匹配 → `status=mismatch`。

优先用 `tmp_path` + monkeypatch `tools.feedback_loop.CASES_DIR` / `tools.feedback_ingest.find_case_dir` 的既有测试风格，避免污染真实 `cases/`。

## Success Criteria

- `python -m tools.feedback_ingest <case_id> --dry-run --json` 的 JSON 输出中可看到 `phase_a_learning_summary.v5_feedback_attachment`。
- 缺少 attachment 的旧 case 仍可摄入，不报错。
- 存在 attachment 的 v5/v6 case 能记录 run-centric 校验结果。
- 现有学习与规则更新计数不因本功能改变。

## Self-Review

- Placeholder scan: 无 `TBD` / `TODO` / 未定义步骤。
- Internal consistency: scope、architecture、data flow 都限定为只读校验与 summary 写入。
- Scope check: 单一入口、单一 helper、单一 summary 字段，适合一个 implementation plan。
- Ambiguity check: missing / invalid / mismatch / ok 状态语义已明确。