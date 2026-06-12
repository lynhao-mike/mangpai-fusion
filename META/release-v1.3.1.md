# Release v1.3.1

## 新增能力

- Production artifact hard gate：生产分析产物收集要求固定 findings、`statement_index.json`、`statement_rule_map.json`，且 `render=True` 时必须生成 report；缺失任一必需产物会触发 hard fail。
- Dynamic weight logs：新增最小可审计 JSONL 日志模块，支持 schema metadata、writer、loader 与本地大小轮转，并接入 feedback ingest。
- Iteration 链补齐：补生成 `META/iteration-report-002.md`，与 `META/iteration-state.json` 的 `iteration_seq=2`、累计 20 案事实保持一致。

## 修复问题

- 修复生产 artifact 原 soft collect 行为，避免不完整产物进入 completed job 或缓存。
- 将 `statement_rule_map.json` 纳入生产 artifact 必需清单。
- 明确 `blind_expert_adapters` 已废弃且当前仓库无有效引用，消除长期悬空状态。
- 补充 production service 回归测试，覆盖完整 artifact 成功路径与缺失必需 artifact hard fail 路径。

## 测试结果

- `python -m pytest tests/test_production_service.py tests/v1_3_acceptance/test_h3_feedback_parsing.py -q`：21 passed，0 failed。
- `python -m pytest tests/test_project_metadata.py -q`：13 passed，0 failed。
- `python tools/tool_registry.py --check`：passed。
- `python tools/rule_status_scan.py --check`：passed。
- `python -m pytest -q`：346 passed，1 skipped，0 failed。

## 兼容性影响

- 生产分析路径更严格：缺失固定 findings、`statement_index.json`、`statement_rule_map.json` 或 report 时，job 会进入 failed，不再 soft collect。
- 动态权重日志为追加式 JSONL 文件；现有反馈摄入保持向后兼容，缺失或空日志会按空数据处理。
- `blind_expert_adapters` 标记 deprecated，不作为当前生产入口。

## 发布结论

Release Candidate：YES

版本：1.3.1

Tag 条件：需在提交前排除临时/非发布文件，并保证工作区只包含 v1.3.1 必须纳入的文件。
