# T-177 · P1 hold-out 评分器 + 当前引擎基线（只读）

- 状态：🔵 Ready
- 优先级：**P0（P1 的尺子；不等修复先出基线）**
- 依据：`META/p1-holdout-freeze-v1.json`、`docs/reviews/p1-evidence-freeze-verdict-v1.md`
- 前置：T-175 hold-out 已冻结；T-174 第二复核已验收

## 0. 一句话

把 dev 集的方向召回评分逻辑，落到 **frozen hold-out** 上：解析 `a/b/kind/actor` 到引擎地址，
算边召回、候选召回、方向召回；先在**当前引擎**上跑一次得到 pre-fix 基线，供三处修复后对比。
**只读评分，不改 engine、不改 hold-out。**

## 1. 输入（冻结，不得改）

- `META/p1-holdout-v1.json`（20 例盲测输入）
- `META/p1-holdout-answers-v1.json`（20 条 `core_work_relations`）
- `META/p1-holdout-freeze-v1.json`（哈希/口径）
- `E:\Git hub\mangpai-fusion-rethink\tools\golden_core_edge_recall.py`（dev 评分逻辑，只读参考）
- `E:\Git hub\mangpai-fusion-rethink\META\golden-20-core-edges-v1.json`（dev 标注 schema，只读参考）

## 2. 评分口径（必须与 dev 工具同构）

对每条 `core_work_relations[]`：

1. **解析端点**：`a`/`b` 是十神（或地址）→ 在本盘 `engine.cli` 事实里解析成地址集合；
   一对多时取所有地址组合，任一命中即算。
2. **边召回**：`relations.edges` 中存在一条边，`members` 同时包含 a、b 的地址，`kind` 与答案
   `kind`/`mechanism` 的映射一致（映射表写进评分器注释；合→wuhe/liuhe、冲→chong、刑→xing、
   穿→chuan、破→po、克→ke、生→sheng；同义别名按 hold-out 的 `kind_enum`）。
3. **候选召回**：`duan_zuogong.candidates` 中存在候选 `members` 同时含 a/b、kind 映射一致。
4. **方向召回**：答案 `actor` 非空时，候选/边的 `actor` 必须等于 a 的地址；
   `actor=null` 的答案不计入方向分母（本 hold-out 20/20 都有 actor）。
5. **分母**：20 条主关系；不得用 dev 33 条；不得剔除 F28 主口径；另报 16 例敏感性。
6. 逐例输出：`edge_hit`、`candidate_hit`、`direction` ∈ {ok, reversed, actor_none, no_candidate, no_edge}。

## 3. 产物

- `tools/p1_holdout_eval.py`：CLI `--holdout --answers [--json]`，默认写 `META/p1-holdout-baseline-v1.json` + `.md`
- `tests/tools/test_p1_holdout_eval.py`：合成 fixture（全中/全不中/actor 反/无候选/多地址），不读真实答案做断言
- `META/p1-holdout-baseline-v1.json` / `.md`：当前引擎的 pre-fix 基线
- `tasks/T-177/BRIEF.md` + `STATUS.md`

## 4. File Scope

**允许新建**：上述文件。
**只读**：hold-out、answers、freeze、branch 工具、engine/facts、sources。
**禁止**：改 engine/规则/测试/ hold-out/ answers；改评分口径；用 hold-out 调规则；git 写操作。

## 5. 验收（中枢亲自跑）

- 20 条全部评到；计数可加；
- 边/候选/方向三个召回都有分子分母；
- 两次运行 JSON 逐字节一致；
- 评分器不读 `sources/` 原文（只读答案里的 quote/source_ref 作展示）；
- 不改 engine；`pytest -q` 0 failed；
- 基线数字与“当前引擎”一致，不冒充修复后结果。

## 6. 回报

1. 改动文件；2. 原始输出（edge/candidate/directed 计数与百分比、per-case 失败分解）；3. 风险（kind 映射、地址多解、actor 歧义）；4. 下游须知（修复后如何复跑、哪些 case 对修复最敏感）。
