# Task 1 Report: Select run snapshot by attachment.run_id

## 实现内容

- 在 [`tests/v1_3_acceptance/test_h3_feedback_parsing.py`](../../tests/v1_3_acceptance/test_h3_feedback_parsing.py:496) 末尾新增两个回归测试：
  - 多 run case 中即使错误 snapshot 的 mtime 更新，也必须按 [`attachment.run_id`](../../engine/v5/domain.py) 选择匹配的 [`*.run.json`](../../tests/v1_3_acceptance/test_h3_feedback_parsing.py:506)。
  - 找不到匹配 [`run_id`](../../engine/v5/domain.py) 时返回 summary-only mismatch，且 [`run_snapshot_path`](../../tests/v1_3_acceptance/test_h3_feedback_parsing.py:543) 为空。
- 在 [`tools/feedback_ingest.py`](../../tools/feedback_ingest.py:735) 的 [`_validate_v5_feedback_attachment()`](../../tools/feedback_ingest.py:735) 中调整选择顺序：
  - 先读取最新 [`*.feedback-attachment.json`](../../tools/feedback_ingest.py:738) 并解析 [`V5FeedbackAttachment`](../../engine/v5/domain.py)。
  - 再扫描同目录 [`*.run.json`](../../tools/feedback_ingest.py:755)，逐个解析 [`V5RunSnapshot`](../../engine/v5/domain.py)，以 [`snapshot.run_id == attachment.run_id`](../../tools/feedback_ingest.py:777) 为准选择绑定快照。
  - 未找到匹配快照时保持 summary-only mismatch，不阻断 ingest。
  - 无 run snapshot 时 summary 仍保持原 schema，但补充 attachment 中的 [`case_id`](../../tools/feedback_ingest.py:759)、[`run_id`](../../tools/feedback_ingest.py:760) 与 target counts。
  - 对无效 run snapshot 收集 issue，并继续尝试其他候选，不引入新文件/服务/仓储层。

## TDD RED 证据

命令：

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_selects_matching_run_id_in_multi_run_case tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_no_matching_run_id -q
```

结果：

```text
FF [100%]
FAILED tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_selects_matching_run_id_in_multi_run_case
E   AssertionError: assert 'mismatch' == 'ok'
FAILED tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_no_matching_run_id
E   AssertionError: assert '.../wrong.run.json' == ''
2 failed, 1 warning
```

说明：旧实现按 mtime 选择最新 [`wrong.run.json`](../../tests/v1_3_acceptance/test_h3_feedback_parsing.py:507)，导致多 run 场景选错，并在无匹配场景返回错误的 [`run_snapshot_path`](../../tools/feedback_ingest.py:786)。

## GREEN / 回归测试结果

命令：

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_selects_matching_run_id_in_multi_run_case tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_no_matching_run_id -q
```

结果：

```text
.. [100%]
2 passed, 1 warning in 8.78s
```

命令：

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py -q
```

结果：

```text
.................... [100%]
20 passed, 1 warning in 13.06s
```

## 修改文件

- [`tools/feedback_ingest.py`](../../tools/feedback_ingest.py:735)
- [`tests/v1_3_acceptance/test_h3_feedback_parsing.py`](../../tests/v1_3_acceptance/test_h3_feedback_parsing.py:496)
- [`.superpowers/sdd/run-id-task-1-report.md`](run-id-task-1-report.md)

## 自审

- 未扩展 [`V5FeedbackAttachment`](../../engine/v5/domain.py) schema。
- 未使用 [`V5CaseManifest`](../../engine/v5/domain.py) 查 artifact binding。
- 未解析 report Markdown。
- 未改 statement feedback、prediction feedback、Dynamic Confidence、rule-learning 逻辑。
- 未新增 service/repository/helper 文件。
- summary schema 字段保持不变：[`status`](../../tools/feedback_ingest.py:784)、[`attachment_path`](../../tools/feedback_ingest.py:785)、[`run_snapshot_path`](../../tools/feedback_ingest.py:786)、[`case_id`](../../tools/feedback_ingest.py:787)、[`run_id`](../../tools/feedback_ingest.py:788)、[`target_counts`](../../tools/feedback_ingest.py:789)、[`issues`](../../tools/feedback_ingest.py:794)。
- Missing / invalid / mismatch 状态仍是 summary-only，不阻断 ingest。

## 疑虑

- 测试运行存在既有 [`DeprecationWarning`](../../engine/application/pipeline_runner.py:10)：[`engine.application.dual_engine_adapter`](../../engine/application/dual_engine_adapter.py) 已弃用；本任务未处理该警告。
