# Task 1 Report: Add read-only attachment validation helper

## 实现内容

- 在 `tools/feedback_ingest.py` 增加只读 helper：
  - `_empty_v5_attachment_summary(status, *, case_id, issue="")`
  - `_validate_v5_feedback_attachment(case_dir, full_case_id)`
- helper 行为：
  - 查找 case 目录中最新的 `*.feedback-attachment.json` 与 `*.run.json`。
  - 使用 `V5FeedbackAttachment.from_json()` 与 `V5RunSnapshot.from_json()` 读取结构化 JSON。
  - 使用 `V5FeedbackAttachment.validate_targets(snapshot)` 校验 attachment 目标 ID 是否存在于 run snapshot。
  - 汇总 `ok` / `missing` / `invalid` / `mismatch` 状态与 issues。
  - 只返回 summary，不写文件，不解析 report Markdown，不接入 `ingest()` 主流程，不改变学习计数。
- 在 `tests/v1_3_acceptance/test_h3_feedback_parsing.py` 末尾添加 helper 级测试：
  - `test_v5_feedback_attachment_validation_ok`
  - `test_v5_feedback_attachment_validation_missing`
  - `test_v5_feedback_attachment_validation_reports_target_mismatch`

## TDD RED 证据

命令：

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_ok tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_missing tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_target_mismatch -q
```

结果：

```text
FFF [100%]
ImportError: cannot import name '_validate_v5_feedback_attachment' from 'tools.feedback_ingest'
3 failed, 1 warning in 0.80s
```

符合预期：新增测试先因 helper 尚未实现而失败。

## GREEN / 验证证据

### Helper 定点测试

命令：

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_ok tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_missing tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_target_mismatch -q
```

结果：

```text
... [100%]
3 passed, 1 warning in 9.62s
```

### H3 文件回归

命令：

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py -q
```

结果：

```text
................. [100%]
17 passed, 1 warning in 9.09s
```

warning 为既有 `engine.application.dual_engine_adapter` deprecation warning，与本任务无关。

## 修改文件

- `tools/feedback_ingest.py`
- `tests/v1_3_acceptance/test_h3_feedback_parsing.py`
- `.superpowers/sdd/task-1-report.md`

## 自审

- 未解析 report Markdown。
- 未将 attachment 作为规则学习来源。
- 未替换或读取 `statement_records.json` 作为 attachment 学习输入。
- 未接入或阻塞现有 `ingest()` 主流程。
- 未新增独立 service/repository/helper 文件。
- missing / invalid / mismatch 均为 summary-only helper 返回值，不改变 learning counts。
- 实现位置在 `ingest()` 章节前，符合任务要求。
- 测试覆盖 ok、missing、target mismatch 三种核心状态。

## 疑虑

- 仅按任务简报实现 helper 级能力，未添加 invalid payload 与 case_id/run_id mismatch 的测试；实现已包含对应 summary 分支，但未扩展本任务指定测试范围。
- `test_v5_feedback_attachment_validation_ok` 按任务简报导入了 `V5RunSnapshot`，当前测试未直接使用该符号；保持原文以符合简报。
