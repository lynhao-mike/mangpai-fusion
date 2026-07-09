# Run-centric proof slice · 2026-07-09

## 结论

本 proof slice 选择 `C-2026-001-乾-庚申戊寅壬子辛丑` 作为正式 case，验证 `plans/geju-system-refactor-architecture-2026-07-08.md` 的 P0：不切默认入口、不大搬目录、不新增 run 模型，用现有 v5/v6 预生产链路证明一次完整 run-centric 分析运行。

## geju 方向判断

- Thesis：长期主对象应是一次可复现、可裁决、可反馈、可升级的 `Run`，而不是工具、报告 Markdown 或 case 目录。
- Trap：旧 `tools/render_report.py` 与报告 Markdown 仍容易被误当成系统核心。
- Clean target：以 `V5RunSnapshot` 作为事实快照，以 `DecisionRun` 作为裁判账本，以 artifact binding 连接报告、case、反馈与预测。
- Staged clean path：保留 legacy facade，先用 `tools/render_report_v6.py` 旁路证明纵切片。

## ponytail 范围控制

本轮只做三件事：

1. 修复 `tools/render_report_v6.py` 直接脚本运行时无法导入 `engine` 的入口问题。
2. 生成并归档一个正式 case 的 v6 preprod artifact bundle。
3. 更新 `tools/README.md`，标清 legacy standard report 与 run-centric preprod 边界。

明确不做：

- 不新增第三套 run 模型。
- 不切默认报告入口。
- 不大搬目录。
- 不重写反馈摄入链。
- 不把 Markdown 报告作为结构化事实源。

## Artifact bundle

| artifact | path |
|---|---|
| report | `reports/C-2026-001-乾-庚申戊寅壬子辛丑-v6-preprod-content-report.md` |
| v5 json | `reports/C-2026-001-乾-庚申戊寅壬子辛丑-v6-preprod-content-report.v5.json` |
| run snapshot | `reports/C-2026-001-乾-庚申戊寅壬子辛丑-v6-preprod-content-report.run.json` |
| decision run | `reports/C-2026-001-乾-庚申戊寅壬子辛丑-v6-preprod-content-report.decision-run.json` |
| feedback attachment | `reports/C-2026-001-乾-庚申戊寅壬子辛丑-v6-preprod-content-report.feedback-attachment.json` |
| case manifest | `cases/C-2026-001-乾-庚申戊寅壬子辛丑/manifest.json` |
| input | `cases/C-2026-001-乾-庚申戊寅壬子辛丑/input.md` |
| feedback | `cases/C-2026-001-乾-庚申戊寅壬子辛丑/feedback.md` |

## Proof checks

- `V5RunSnapshot.from_json()` 可读取 run snapshot。
- `V5RunSnapshot.output_hash_matches()` 为 true。
- `V5FeedbackAttachment.from_json()` 可读取 feedback attachment。
- `V5FeedbackAttachment.validate_targets()` 返回空列表。
- `.decision-run.json` 的 `schema_version` 为 `decision-run-v1`。
- `.decision-run.json` 可由 `.v5.json` 经 `decision_run_from_v5(..., raw_text=v5_output.to_json(indent=None))` 重建，且 `DecisionRun.validate_trace()` 返回空列表。
- `manifest.json` 已绑定 active `run_id` 与 artifact paths。
- run snapshot 的 `canonical_input.source_input` 使用仓库相对路径，不写入本机盘符绝对路径。

## 运行命令与结果

```bash
python tools/render_report_v6.py cases/C-2026-001-乾-庚申戊寅壬子辛丑/input.md --output reports/C-2026-001-乾-庚申戊寅壬子辛丑-v6-preprod-content-report.md
```

结果：exit code 0，生成 report / v5 json / run json / decision run json / feedback attachment json。

```bash
python -m pytest tests/v5/test_render_report_v6.py -q
```

结果：3 passed, 1 warning。

```bash
python -m pytest tests/test_project_metadata.py tests/v5/test_v5_contracts.py tests/v5/test_v5_prediction_feedback.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/v5/test_render_report_v6.py -q && python tools/tool_registry.py --check && python tools/rule_status_scan.py --check
```

结果：122 passed, 1 warning；tool registry check passed；rule status scan passed。

```bash
python -c "...run snapshot / attachment / decision artifact proof..."
```

结果：`output_hash_matches=True`；`feedback_target_issues=[]`；`decision_validate_trace=[]`；`decision_artifact_matches_adapter=True`；`source_input=cases/C-2026-001-乾-庚申戊寅壬子辛丑/input.md`；`active_run_id=run-f5a87bc8cb53`。

## P1 边界更新

`tools/README.md` 已标记：

- `tools/render_report.py` 是 legacy standard report 兼容入口，不承载新增 run-centric 字段。
- `tools/render_report_v6.py` 是 run-centric preprod 证明入口，旁路生成 report / v5 json / run snapshot / decision run / feedback attachment。
- 新报告字段必须先进入 `V5RunSnapshot` / `DecisionRun` 等结构化对象，再由报告视图渲染。

## P2/P3/P4 完成记录（2026-07-09 续）

### P2：反馈闭环绑定 run attachment

- `tools/feedback_ingest.py` 的 `_validate_v5_feedback_attachment()` 现通过 manifest.json 的 artifact_paths 优先发现 reports/ 下的 `.feedback-attachment.json` 与 `.run.json`，再回退 case 目录 glob。
- summary 增加 `target_samples`（claim / prediction / signal 前 3 条），证明反馈命中了 run 结构化对象。
- 路径全部 resolve 后比对，避免 Windows / 中文路径 / POSIX 混合问题。
- 测试新增 `test_v5_feedback_attachment_validation_prefers_manifest_artifacts_outside_case_dir` 覆盖跨目录发现。

### P3：固化 V5RunSnapshot / DecisionRun 关系

- 新增 `engine.decision.v5_adapter.decision_run_from_snapshot()`：从 V5RunSnapshot 派生 DecisionRun，保持 snapshot 是唯一事实源。
- `engine/v5/preprod.py` 写 `.decision-run.json` 改为 `decision_run_from_snapshot(snapshot)`，写前执行 `validate_trace()`。
- `decision_run_from_v5()` 默认 raw_text 从 `repr(output)` 改为 `output.to_json(indent=None)`，脏对象提供最小 fallback。
- 测试新增 `test_decision_run_from_snapshot_matches_v5_output_adapter` 断言等价与 trace 校验。

### P4：工具层瘦身

- `tools/README.md` active 列表由 27 项精简至 21 项。
- 移入 historical：`case_feedback_intake.py`、`case_feedback_promote.py`、`case_feedback_repan_index.py`、`cross_domain_consistency_check.py`、`materials_intake.py`、`recompute_wenzhen_case.py`。
- `python tools/tool_registry.py --check` 通过。

### 后续阶段建议

- 何时切默认报告入口：P0 已成功，可在 v6 preprod 覆盖正式统一报告全部要求后讨论。
- 旧 `engine/pipeline.py` 降级：当前已标 legacy，不删除，等 v6 preprod 完整覆盖后再降级。
- P5 目录迁移：当前无证据证明目录结构阻碍 run-centric 主线，继续不迁移。
