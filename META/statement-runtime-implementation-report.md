# P5-4 Statement Runtime Implementation Report

生成时间：2026-06-12

## 1. 修改文件列表

- `tools/render_report.py`
  - 在 `render_from_output()` 的 Report Render 完成阶段接入 statement runtime artifact 写入。
  - 保持原有 `statement_index.json` 生成逻辑不删除、不降级。
- `tests/track_f_smoke/test_f_render.py`
  - 新增渲染链路验收，验证 `statement_records.json`、`statement_index.json` 共存与必填字段完整性。

## 2. 新增文件列表

- `engine/statement_runtime.py`
  - 新增 statement runtime builder。
  - 生成 `statement_record.v1` envelope。
  - 提供 `write_statement_records()`、`validate_statement_records()`、`validation_summary()`。
- `META/statement-runtime-implementation-report.md`
  - 本实施报告。

## 3. 运行结果

定向测试：

```text
pytest tests/track_f_smoke/test_f_render.py tests/test_project_metadata.py -q
.s..........................                                             [100%]
27 passed, 1 skipped in 11.83s
```

临时样例生成命令在独立临时目录运行，不写入正式 `cases/`：

```text
case_id: C-2026-001-乾-庚申戊寅壬子辛丑
statement_records_generated: 345
missing_field_count: 0
```

新增统计口径：

- 生成案例数：1
- statement 总数：345
- 缺失字段数：0

## 4. 生成样例

```json
{
  "statement_id": "S-001-3baaca",
  "case_id": "C-2026-001-乾-庚申戊寅壬子辛丑",
  "rule_id": "M1-D-001",
  "family_id": "FAM-M1-D-001",
  "school": "段",
  "canon": "duan",
  "rule_type": "runtime_rule",
  "statement_text": "年支支申 ↔ 月支支寅 之 冲 → 作用于用神申(官杀)",
  "confidence_snapshot": {
    "star": 5,
    "percent": 95.0,
    "posterior_mean": null,
    "sample_n": 0,
    "source": "static_rule"
  },
  "generated_at": "2026-06-12T15:11:33Z",
  "source_engine_version": "1.3.1",
  "source_rule_version": "findings-schema:1.4.0"
}
```

落盘 envelope：

```json
{
  "schema_version": "statement_record.v1",
  "case_id": "C-2026-001-乾-庚申戊寅壬子辛丑",
  "generated_at": "2026-06-12T15:11:33Z",
  "statement_records_generated": 345,
  "missing_field_count": 0,
  "records": []
}
```

## 5. 兼容性结果

- `statement_index.json`：继续生成，未删除。
- `statement_records.json`：由 Report Render 阶段自动生成到 `cases/<case_id>/statement_records.json`。
- 展示报告：不展示 `statement_record` 内部字段，不改变报告正文输出结构。
- 学习层：未接入 `feedback_ingest`、`feedback_loop` 或 Dynamic Confidence 更新。
- 权重：未修改 Family Weight、School Weight、Canon Weight。
- 禁止文件：未修改 `theory/*`，未修改 `META/project-state.json`。

## 6. 风险说明

- 当前 v1 facts layer 采用“一条最终输出 statement 对应一条 statement_record”的实现，以满足本阶段 `statement_id` 唯一验收。若未来严格执行“一条多规则 statement 拆多 record”，需要同步调整反馈 join 主键或引入 record-level 子 ID，避免同一 `statement_id` 多行导致唯一性冲突。
- `family_id`、`canon`、`rule_type` 当前由 runtime 命名规则解析生成，不读取或修改权重表。后续若建立正式 rule metadata registry，可替换 resolver，但必须保持不在反馈后反推。
- `confidence_snapshot` 当前冻结静态生成期值，`posterior_mean` 为 `null`、`sample_n` 为 `0`，未接入 Dynamic Confidence，符合本阶段“Facts Layer only”边界。
- 旧案未批量迁移；历史 `statement_index.json` 保持 legacy/candidate/read-only 兼容，不自动进入学习层。
