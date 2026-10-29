# T-179 · 候选生成修复 v1（体-体/双属 + 柱内/邻柱生；不补支克）

- 状态：🔵 Ready
- 优先级：**P0（候选召回 70% → 提升；不碰 880 支克）**
- 依据：`docs/reviews/p1-baseline-verdict-v1.md`；独立 Agent 三处方案
- 前置：无（与 T-178 并行；T-178 管方向规则，本卡只管候选生成）

## 0. 一句话

在**新分支/worktree** 上只改 `engine/facts/structure_check.py` 两处：
①不再丢体-体/双属-双属关系；②柱内/邻柱「生」进入候选。
**不补 880 支克边**（目标约束），**不改 actor 方向**（归 T-178）。

## 1. 改动范围（只此两处）

1. **去过滤**：候选生成时，不再因为两端都是「体」或「双属」而丢掉关系对；
   保留现有去重、排序、`mode` 语义。
2. **柱内/邻柱生**：在**同柱**或**相邻柱**的地址之间，若五行/十神构成「生」，
   生成 `mode="sheng"` 候选：`actor=生者`、`target=被生者`、`members=[actor,target]`。
   - 只在同柱/相邻柱（年-月、月-日、日-时；含同柱干支）生成；
   - 跨柱远距离不生成（先不扩）；
   - 不生成支克（880）候选；不改 `relations.edges`。
3. **不碰**：排盘、关系图、边 ID、`relations.edges`、`condition_ir`、产品规则、既有断言。

## 2. 实现方式

- 新 worktree：`..\mangpai-fusion-p1cand`，分支 `p1/candidates`，从 `edd79fec` 起。
- **不要**改 `..\mangpai-fusion-rethink`（独立 Agent 的 worktree）。
- 改 `engine/facts/structure_check.py`（必要时同文件内 helper；不改公共类型）。
- 代码必须可回滚：一个 commit 只含这两处 + 测试；不夹带格式/清理。

## 3. 验证

1. `pytest -q`：0 failed；facts/structure 定向测试全过。
2. 481 盘回放：`engine_audit` 481/0；`relations_audit` 全通过。
3. 候选统计：
   - 全 382 盘：`duan_zuogong.candidates` 总数、`sheng` 数、体-体/双属候选数；
   - 三张 T-169 盘（C1/C2/C3）：候选数变化、夫妻宫边是否进候选；
   - 与改前对比表。
4. 新增测试：
   - 体-体关系不再被丢；
   - 同柱/邻柱生生成 `sheng` 且 `actor/target` 正确；
   - 跨柱远距离不生成；
   - 支克 880 仍 0 条（目标约束）。
5. **不跑 hold-out**；hold-out 由中枢在合并后一次性评分。

## 4. 产物

- 分支 `p1/candidates`（worktree `..\mangpai-fusion-p1cand`）上的 commit
- 代码 diff（仅 `structure_check.py` + 测试）
- `tasks/T-179/BRIEF.md`：改动文件、候选统计对比、481/0、测试、风险
- `tasks/T-179/STATUS.md`

## 5. 验收（中枢亲自跑）

- worktree 内 `pytest -q` 0 failed；`engine_audit` 481/0；`relations_audit` 通过；
- `git diff` 只含 `structure_check.py` + 测试；无支克边；
- 候选统计可复现；三张盘的夫妻宫边变化可解释；
- 不 push main；分支/commit 报告。

## 6. 回报

1. 分支/commit；2. 候选统计对比；3. 481/0 与测试；4. 风险（候选爆炸、排序变化、性能）；5. 下游须知（合并顺序、与 T-178 方向规则的接口）。
