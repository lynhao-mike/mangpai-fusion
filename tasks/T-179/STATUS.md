# T-179 STATUS

- 状态：🟡 Dispatched（2026-10-29，中枢）
- 执行者：子代理 AC
- 任务卡：`tasks/T-179/PROMPT.md`
- 验收：中枢亲自跑；只在 p1/candidates 分支

## Execution Log

| 时间 | 动作 |
|---|---|
| 13:00 | 中枢建卡并派发；与 T-178（墓/actor 规则）并行；不碰 rethink worktree |
| 13:05 | 子代理 AC 报卡内冲突：去体-体/双属过滤会使 2 条旧断言必红。中枢裁决：**授权反向契约**（改名 + 断言新行为 + 注释 ADR-007 D1 被 T-179 取代），不许删/skip/放宽其他断言；`mode="sheng"` 允许（扩 Literal，members[1]=target）；新增 sheng 仅同柱/邻柱，既有远距离 sheng 不删但报数量/比例/性能，>2 倍则停。继续 |
