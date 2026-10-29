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
| 13:15 | 子代理 AC 报 15KB 冲突：改后 16,427B/27 候选，两条尺寸断言必红。中枢裁决：**不批 A（15→18KB）**，15KB 是护栏；**批 C**（只压缩默认视图 facade，保 edge_id/mode/actor/target/tiyong/members，15KB 断言不改）；压不下去则停，报字节分解由人类决定。继续 |
| 13:18 | 子代理 AC 完成 C：默认视图削 `candidates.ten_gods` / `edges.layer|scope|distance` / `chart` 干支 `wuxing|yinyang`；测试盘 16,428→**14,802 B**（<15,000，尺寸断言未改）；382 盘中位 15,453→15,423、max 21,500→21,298、超 15KB 盘 257→242 |
| 13:20 | 按中枢转达的 T-178 审计追加墓向：墓用候选 `members=(库,入库方)`、`actor=库`，`relations.muku` 不动；新增墓向测试；H13 仍 `no_candidate`（体-体过滤，不在本轮 actor 修复内） |
| 13:24 | 全量验证：`pytest -q` **1425 passed, 1 skipped**（127.10s；基线 1420/139.15s）；`engine_audit` **481/0** exit0；`relations_audit` 全部通过 exit0；`zuogong_probe` 481/481（旧档 477，无下降）；382 盘候选 5,685→9,941（1.75×） |
| 13:26 | commit `4bf238e7`（`p1/candidates`，4 files，+158/−29，未 push）；BRIEF 四字段已写；**未跑 hold-out**；契约变更 3 条测试在 BRIEF §1/§3 单列 |
