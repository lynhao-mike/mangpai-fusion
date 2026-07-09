# Task 2 Report: Attach validation summary to ingest result without changing learning logic

## 实现内容

- 在 `tools/feedback_ingest.py` 的 `ingest()` 中，在解析 `case_dir` 与 `full_case_id` 后调用已有 helper：
  - `_validate_v5_feedback_attachment(case_dir, full_case_id)`
- 在 `ingest()` 的 early-return 分支中，将 `v5_feedback_attachment` 挂入 `IngestResult.phase_a_learning_summary`。
- 在 `ingest()` 的 normal 分支中，将 `v5_feedback_attachment` 挂入合并后的 `phase_a_learning_summary`。
- 未修改以下学习逻辑与计数字段：
  - `feedback_count`
  - `rule_count`
  - `learning_sample_count`
  - `_apply_rule_verdicts()` 调用行为
  - `statement_records.json` 规则学习事实源
- 未解析 report Markdown。
- 未将 attachment 用作 rule-learning source。
- 未新增 service/repository/helper 文件。

## TDD RED 证据

先按 brief 在 `tests/v1_3_acceptance/test_h3_feedback_parsing.py` 添加 ingest 级测试：

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning -q
```

结果：失败，符合预期。

```text
FAILED tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning
E   KeyError: 'v5_feedback_attachment'
1 failed, 1 warning in 11.38s
```

## TDD GREEN 证据

接入 `v5_feedback_attachment` summary 后运行同一测试：

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning -q
```

结果：通过。

```text
1 passed, 1 warning in 12.81s
```

## 回归测试

运行完整 H3 feedback parsing acceptance 文件：

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py -q
```

结果：通过。

```text
18 passed, 1 warning in 12.42s
```

警告为既有 `engine.application.dual_engine_adapter` deprecation warning，与本任务无关。

## 修改文件

- `tools/feedback_ingest.py`
- `tests/v1_3_acceptance/test_h3_feedback_parsing.py`
- `.superpowers/sdd/task-2-report.md`

## 自审

- early-return 分支覆盖：无 `statement_records.json` / 无可学习映射时，仍返回 `skipped_no_index=True` 与 `learning_sample_count=0`，仅在 summary 中展示 attachment 校验状态。
- normal 分支覆盖：保留原 `phase_a_learning_summary` 内容，追加 `v5_prediction_feedback` 与 `v5_feedback_attachment`。
- summary-only 约束满足：attachment 校验结果不参与 fanout、不参与 learning samples、不影响规则更新与计数。
- 没有实现 Task 3。

## 疑虑 / concerns

- brief 提供的测试字符串与 pillars 是 mojibake 文本；按原文执行，测试可通过。
- 工作区已有未跟踪的 `.superpowers/sdd/progress.md`、`.superpowers/sdd/task-1-brief.md`、`.superpowers/sdd/task-1-review-package.md`、`.superpowers/sdd/task-2-brief.md`，非本任务创建，提交时未纳入。