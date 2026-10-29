# T-195 STATUS

- 状态：🟡 Delivered（2026-10-29，runner 已交产物；待中枢按 R 规格评分）
- 执行者：子代理 AV（未污染）
- 任务卡：`tasks/T-195/PROMPT.md`
- 验收：中枢按 R 规格评分；runner 不自评
- 产物：`META/r-tool-run-v1.json`、`tasks/T-195/run_r_tool.py`、`tasks/T-195/BRIEF.md`
- 摘要：fixed-20 20/20、out_of_class=0；routing 15 包 / 116 证据项；**routing blind_valid=false（见 Blockers）**

## Blockers

1. **routing 非盲**：`META/routing-questions-v1.json` 自称 runner 视图，但文件仍含 `expected_evidence`（restricted）。
   整文件读取后标签进入 runner 上下文 → routing 不可作为盲测入账。需中枢先脱敏（仅 `runner_visible_fields`），
   再由干净会话重跑 `tasks/T-195/run_r_tool.py`。fixed-20 未受影响（未读任何 answers / B 卷 / prereg）。
2. **fixed-20 3 条类不符**（F20-009/013/014）：engine 未对该端点对发出目标类候选，已按 engine 五行表/§4.8/同对力向推得，
   逐条标 `class_rule_mismatch`；其中 F20-013 最弱（沿用同对制用力向）。详见 `BRIEF.md` §3。

## Execution Log

| 时间 | 动作 |
|---|---|
| 22:50 | fixed-20 A/B 18/20；B 卷提交；派 T-195 R 运行 |
| 23:58 | R-tool runner 完成：fixed 20/20、ooc=0（engine_candidate 17 / element_rule 2 / pair_fallback 1）；routing 15 包 116 项；结构自检 ERRORS=0；发现 routing 输入泄漏 restricted 字段，已标 blind_valid=false |
