# T-182 · P1 评分器口径同步（artifact 标签 + 墓/化注释 + fixture）

- 状态：🔵 Ready
- 优先级：**P0（正式 P1 前必须洗尺）**
- 依据：T-180 R3/R4；T-181 化向修复
- 前置：T-181 已合并（main `ba688aec`）

## 0. 一句话

只改评分器与测试：给产物加 `artifact` 标签、把墓/化注释与 fixture 同步到 T-178/T-180 的新约定。
**不改评分逻辑、不改 hold-out、不跑正式 P1、不碰 engine。**

## 1. 改动

1. `tools/p1_holdout_eval.py`
   - 新增 `--artifact-label`（默认 `pre_fix_baseline`）；写进 JSON 的 `artifact` 与控制台标题。
   - 正式 P1 用 `--artifact-label official_p1`；postfix 诊断用 `post_fix_candidates` / `post_fix_hua`。
   - 注释同步：
     - 墓：T-178 4/4 engine_wrong；引擎墓用候选应为 `(库,入库方)`、`actor=库`；T-179 已修。
     - 化：T-180 4/4 engine_wrong；化=被化者→化者，化者=受生端；T-181 已修 H09–H11，H12 known_gap。
   - 不改 kind 映射、不改 `_direction` 逻辑、不改分母。
2. `tests/tools/test_p1_holdout_eval.py`
   - 墓 fixture 改为新约定：candidate `(库,入库方)`、`actor=库`，期望 `ok`（不再断言 `reversed`）。
   - 新增化 fixture：`mode=化用`、`actor=化者`，期望 `ok`；H12 财→杀标 `known_gap`（不扩类）。
   - 新增 `--artifact-label` 测试：默认/自定义写入 JSON；控制台标题同步。
   - 不改断言换绿；契约变更在 BRIEF 单列。

## 2. 验证

- `pytest tests/tools/test_p1_holdout_eval.py -q` 0 failed；
- 合成 fixture 断言：墓 ok、化 ok、H12 reversed/known_gap、artifact label；
- **不跑真实 hold-out**（正式 P1 由中枢一次性跑）；
- 不改 engine/规则/hold-out/answers。

## 3. 产物

- `tools/p1_holdout_eval.py`、`tests/tools/test_p1_holdout_eval.py`
- `tasks/T-182/BRIEF.md` + `STATUS.md`
- 分支 `p1/ruler`（worktree `..\mangpai-fusion-ruler`，从 main `ba688aec` 起）；不 push main。

## 4. 禁止

- 不改评分逻辑/分母/阈值；不改 hold-out/answers；不跑真实 P1；不碰 engine。
- 不删/skip/放宽既有断言；契约变更按反向契约并单列。
