# T-185 BRIEF · P1 新鲜 40 条盲集（v1）

- 执行者：子代理 AI（策展 / 标注人）
- 任务卡：`tasks/T-185/PROMPT.md`
- 日期：2026-10-29
- 结论：**40 条 / 37 盘 / 8 类 mechanism 全覆盖 / 与两套 dev 零重叠**；另附 **5 条 needs_judgment 路由例**（单列，不进 40 条分母）；门禁 13 passed。

## 1. 改动文件（只新增，未改任何既有文件）

| 文件 | 性质 | 说明 |
|---|---|---|
| `META/p1-fresh-40-v1.json` | 新增 | 盲测输入（40 例，只含 case_id / chart_id / 四柱 / 性别 / source） |
| `META/p1-fresh-40-answers-v1.json` | 新增 | 答案（40 条 relation + 逐字 quote + source_ref + 注） |
| `META/p1-fresh-40-routing-blind-v1.json` | 新增 | 路由例盲测输入（5 例，needs_judgment 用，§9） |
| `META/p1-fresh-40-routing-v1.json` | 新增 | 路由例答案（5 条，`expected_direction="needs_judgment"`，§9） |
| `META/p1-fresh-40-v1.md` | 新增 | 清单 / 盘数 / 类型 / 非 dev 校验 / sha256 / 缺口 / 路由例 |
| `tests/tools/test_p1_fresh_40_schema.py` | 新增 | 13 个用例：分离、对齐、非 dev、逐字、覆盖、冻结、路由 |
| `tasks/T-185/BRIEF.md` | 新增 | 本文件 |
| `tasks/T-185/STATUS.md` | 更新 | 状态与 Execution Log |

未改：`sources/`、`engine/`、规则、既有测试、`PROMPT.md`；未跑 engine；未做任何 git 写操作。

## 2. 原始输出

### 2.1 门禁（唯一命令）

```
$ python -m pytest -q -o addopts="-ra --tb=short" tests/tools/test_p1_fresh_40_schema.py
.............                                                            [100%]
13 passed in 0.19s
```

### 2.2 冻结 hash（写入 `META/p1-fresh-40-v1.md` §0 / §9）

```
p1-fresh-40-v1.json                 13790 bytes  3446c9707e92aa71cbbd60c9e9fb16623f7312e9c4803f5d51c64a78903b6950
p1-fresh-40-answers-v1.json         23958 bytes  478d1a5959016b5c5b1d1f36a9457828ad4a95f7ebe64d2d2a0f252fd0730555
p1-fresh-40-routing-blind-v1.json    2033 bytes  b64f05b79dc5ea2a829d540035bea5b023d66723c9daf77a673f135d6725bf99
p1-fresh-40-routing-v1.json          3968 bytes  d45dcf18a2a0a1a6d3b0a53b9b108f8ab31b1e5a3776dcc9de07f3204b16b504
```

### 2.3 规模与分布（以文件为准，测试逐项核对）

- 40 条；37 张不同盘（≥25 达标）；每盘 ≤2 条（3 张盘各 2 条，其余 34 张各 1 条）。
- mechanism：冲 7 / 合 8 / 穿 6 / 刑 5 / 墓 5 / 克 3 / 生 4 / 化 2（8 类全覆盖）。
- kind：制 16 / 合 5 / 墓 5 / 生 4 / 克 3 / 穿 3 / 化 2 / 冲 1 / 刑 1。
- 性别：乾 29 / 坤 11（全部原书标注，无「未注明」）。
- 来源：6 本书（16 / 19 / 21 / 22 / 23 / 广州讲义）。

### 2.4 非 dev 校验

- 排除对象：`META/golden-20-v1.json`（20 例）+ `META/p1-holdout-v1.json`（20 例），共 40 例。
- 结果：四柱 **0 重合**、source 行区间 **0 重叠**（`test_not_dev_and_not_same_source_lines` 逐条判定）。
- 只读了两套 dev 的 `case_id` / `four_pillars` / `source`；**未打开** `golden-20-answers-v1.json` 与 `p1-holdout-answers-v1.json`。

### 2.5 路由例（WB 追加，单列）

- 5 条 / 5 张新盘：穿制 1 / 合绊 1 / 保护 1 / 制净 1 / Δ=0 1。
- 答案形态：无 `actor`，`expected_direction="needs_judgment"`；只测「是否输出 needs_judgment」与「类型覆盖」，**不记 ok/reversed**，**不进** 40 条方向精度分母。
- 非 dev：与 40 条主集、两套 dev 均不同盘，source 行 0 重叠；**未用** `P1-H02`（癸巳壬戌庚申乙酉）与 `P1-H05`（壬子丙午己巳己巳）。
- 合并盘数 42（主集 37 + 路由 5），维持 ≥25 盘。
- 明细见 `META/p1-fresh-40-v1.md` §9。

## 3. 未完成与风险

1. **克 / 生 / 化 偏少（3 / 4 / 2）**：原书对「克、生、化」的原局方向断言多以十神泛称出现（「官杀克身」「印化杀」），点名到干支的少；点名者多挂在大运流年或 dev 盘上（已按口径排除），故未强行凑均衡。
2. **`化` 的方向口径**：按原文语法取「化者＝印」为 `a`（PF-039 酉印化辰杀、PF-040 子印化申杀）。若下游按引擎 `sheng` 边方向（杀生印）评分，`direction` 可能判 `reversed`；这是口径问题，不是选例问题。
3. **同盘双条 3 组**：PF-003/PF-023、PF-034/PF-038、PF-007/PF-012；按条 n=40，按盘 n=37，统计时建议按 `chart_id` 聚类。
4. **mutual 仅 1 条**：PF-027（丑戌未三刑「三个字都坏了、功就没有了」），`actor=null`，不硬填施力端。
5. **OCR 风险**：quote 只保证与 `sources/duan/*.md` 对应行逐字一致（MinerU 转写，个别字形可能失真），不保证与纸质原书一致。
6. **未收的候选**：穿倒类（22 书「羊刃库穿倒印星子水」、19 书「戌能穿倒酉」、23 书「子未穿为穿倒未土」）、大运类（「行辰运，丑入辰墓」「己未运未戌刑」）、dev 盘（如 22 书闫锡山例 = G20-003、21 书乙未己卯丁丑庚戌 = G20-006、22 书丙午辛卯丁卯壬子 = P1-H03）均主动剔除。
7. **路由例的边界**：`PF-R03`（丙戌 戊戌 辛酉 壬辰）原书是问题条目体、未标性别，记「未注明」；`PF-R04` 的 `mechanism` 记「制」（原文「未制酉」），与主集 8 类机械口径不同，只用于路由统计，不影响主集分布。

## 4. 下游须知

1. **运行人只读** `META/p1-fresh-40-v1.json` 与 `sources/`；`META/p1-fresh-40-answers-v1.json` 运行人不得打开（标注/运行分离）。路由例另读 `META/p1-fresh-40-routing-blind-v1.json`，不得读 `META/p1-fresh-40-routing-v1.json`。
2. 复用 `tools/p1_holdout_eval.py` 时，把每条答案的 `relation` 包成 `core_work_relations: [relation]`（该工具读 `ans["core_work_relations"]`；`category` 缺省为空，不参与本卷口径）；**路由例不要走该工具的方向口径**，单独只统计 needs_judgment。
3. 报分请同时按 `case_id`（40 条）与 `chart_id`（37 盘）各报一次，同盘双条不得当独立样本；路由例只报 needs_judgment 命中率与 5 类覆盖。
4. 冻结：四份 JSON 的 sha256 已写入 `META/p1-fresh-40-v1.md` §0 / §9，`test_frozen_sha256_matches_manifest` 会拦住任何事后改动；如需修订另立 `v2` 并在 `STATUS.md` 记原因。
5. 本卷**未跑 engine**，未提供任何引擎侧数字；P1 分数只能由运行人在自己的会话里产生。
