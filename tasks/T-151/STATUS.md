# T-151 STATUS

- 状态：✅ **已验收**（2026-10-28，中枢亲自复算）
- 执行者：子代理 B
- 任务卡：`tasks/T-151/PROMPT.md`（卡内 §1 即预注册）
- 简报：`tasks/T-151/BRIEF.md`（Worker 写）
- 验收：中枢亲自跑命令并逐格核对指纹

## Execution Log

| 时间 | 动作 |
|---|---|
| 21:35 | 中枢建卡并派发；与 T-150/T-148 File Scope 无重叠 |
| 21:55 | 子代理 B 完成：283 期 → 78 条日支冲边（34/25/19，A–E 分布逐格对上 §1.5；scored 22/59=37.3%，B 基线 32/59=54.2%）；`m2y395_direction`/`m2y395_score` 退出码 0、两次输出哈希一致；`pytest -q` 0 failed（开工 1043 / 收工 1066 passed，多出部分为 T-150 并行新增测试）。产物 5 文件 + BRIEF；未改任何保护区，未执行 git 写操作 |
| 22:00 | 按中枢 21:57 接口补充：`m2y395-scored-v1.json` 每例加 `claim_id=M2-Y-395`、`triggered=true`、`outcome=unknown`（`branch`/`prediction_letters`/`answer_letter` 不变）；重跑后指纹仍 78 / 34 / 25 / 19、22/59，两次输出哈希一致 |
| 22:05 | 中枢复跑 `m2y395_direction`/`m2y395_score`：EXIT=0，78 / 34 / 25 / 19、22/59、B 基线 32/59 全部对上；`grep answer` 零命中 |
| 22:07 | 中枢独立复算（不依赖 Worker 汇总）：边级 59/22/32、期级 53/20/30、70 期 7 期多冲；3 例按 edge_id 回 `engine.cli` 抽查通过 |
| 22:09 | 中枢用 T-150 计分器正式出分：`n_scored=59 / n_correct=22 / accuracy=0.3729 / baseline=0.5424 / wilson=[0.2608,0.5005]`，EXIT=0 |
| 22:10 | 裁决：**方向 alone 被否证**（边级与期级双口径均低于基线）；写着 `docs/reviews/m2y395-verdict-v1.md`；卡 §7 补登计数单位 |
| 22:12 | 中枢提交（仅暂存 T-151 相关文件） |
