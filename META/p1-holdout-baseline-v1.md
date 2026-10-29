# P1 hold-out pre-fix 基线（T-177）

- 生成器：`python -m tools.p1_holdout_eval --holdout META/p1-holdout-v1.json --answers META/p1-holdout-answers-v1.json`
- 输入 sha256：holdout `593f4dbea76a4959550c326eea31a8d9feae895cb9272028813982de96bbf045`；answers `b1075a394dc1954f27e7de1b06b38283174223e223e3d6b17993723bef37762f`（与 `META/p1-holdout-freeze-v1.json` 对照）
- 规模：20 例 / 20 条 `core_work_relations`
- 口径：冻结 hold-out 的全部关系；**不是** dev 33 条，不做跨集比较（freeze `no_comparison_to_dev`）
- 性质：**pre-fix 基线**。三处修复落地后必须整体重跑覆盖本表，本表数字不得当修复后结果引用。

## 1. 主口径（20 条）

| 指标 | 分子/分母 | 百分比 |
|---|---|---|
| 边召回 `edge_recall` | 8/20 | 40.0% |
| 候选召回 `candidate_recall` | 14/20 | 70.0% |
| 方向召回 `directed_recall` | 1/20 | 5.0% |
| 评到（scored） | 20/20 | — |
| 方向分母（actor 非空） | 20 | — |

方向分布（分母 20）：`actor_none` 6、`no_candidate` 1、`no_edge` 5、`ok` 1、`reversed` 7

方向定义：`ok` = 匹配候选的 `actor` 落在 a 端地址；`reversed` = 落在 b 端；`actor_none` = 有候选但 `actor` 空或不在两端；`no_candidate` = 有边无候选；`no_edge` = 边与候选皆无。

## 2. 敏感性：剔除 F28 救应（16 条，H17–H20）

| 指标 | 分子/分母 | 百分比 |
|---|---|---|
| 边召回 | 6/16 | 37.5% |
| 候选召回 | 11/16 | 68.8% |
| 方向召回 | 0/16 | 0.0% |
| 评到（scored） | 16/16 | — |

muku 等价边召回（dev 把 `relations.muku` 入库当成边；**仅敏感性**，不进主口径）：20 条 12/20（60.0%）、16 例 10/16（62.5%）。

## 3. 逐例（20 条）

| case | 类 | a→b | mechanism / kind | 边 | 候选 | 方向 | 说明 |
|---|---|---|---|---|---|---|---|
| `P1-H01` | 制 | 子→午 | 制 / 制 | ✓ | ✓ | actor_none | 边 e011；候选 1 条 actor=null |
| `P1-H02` | 制 | 酉→戌 | 穿 / 制 | ✓ | ✗ | no_candidate | 边 e013；无候选 |
| `P1-H03` | 制 | 丙→辛 | 合 / 制 | ✓ | ✓ | actor_none | 边 e001；候选 1 条 actor=null |
| `P1-H04` | 制 | 巳→申 | 合 / 制 | ✓ | ✓ | actor_none | 边 e008；候选 1 条 actor=null |
| `P1-H05` | 制 | 午→子 | 冲 / 制 | ✓ | ✓ | actor_none | 边 e008；候选 1 条 actor=null |
| `P1-H06` | 制 | 午→酉 | 克 / 制 | ✗ | ✗ | no_edge | 无边；无候选 |
| `P1-H07` | 制 | 戊→子 | 克 / 制 | ✗ | ✗ | no_edge | 无边；无候选 |
| `P1-H08` | 制 | 酉→卯 | 冲 / 制 | ✓ | ✓ | actor_none | 边 e007；候选 1 条 actor=null |
| `P1-H09` | 化 | 巳→卯 | 化 / 化 | ✗ | ✓ | reversed | 无边；候选 3 条 actor=M.b,M.b,M.b |
| `P1-H10` | 化 | 午→寅 | 化 / 化 | ✗ | ✓ | reversed | 无边；候选 3 条 actor=H.b,H.b,H.b |
| `P1-H11` | 化 | 辰→巳 | 化 / 化 | ✗ | ✓ | reversed | 无边；候选 1 条 actor=Y.b |
| `P1-H12` | 化 | 寅→子 | 化 / 化 | ✗ | ✗ | no_edge | 无边；无候选 |
| `P1-H13` | 墓 | 辰→丑 | 墓 / 墓 | ✗ | ✗ | no_edge | 无边；无候选；muku D.b->Y.b,D.b->H.b |
| `P1-H14` | 墓 | 丑→酉 | 墓 / 墓 | ✗ | ✓ | reversed | 无边；候选 2 条 actor=M.b,H.b；muku M.b->D.b,H.b->D.b |
| `P1-H15` | 墓 | 辰→亥 | 墓 / 墓 | ✗ | ✓ | reversed | 无边；候选 2 条 actor=M.b,H.b；muku M.b->D.b,H.b->D.b |
| `P1-H16` | 墓 | 未→寅 | 墓 / 墓 | ✗ | ✓ | reversed | 无边；候选 2 条 actor=M.b,M.b；muku M.b->D.b,M.b->H.b |
| `P1-H17` | 救应 | 己→癸 | 制 / 救应 | ✓ | ✓ | ok | 边 e001；候选 1 条 actor=Y.s |
| `P1-H18` | 救应 | 丁→卯 | 化 / 救应 | ✗ | ✓ | reversed | 无边；候选 1 条 actor=H.b |
| `P1-H19` | 救应 | 午→申 | 克 / 救应 | ✗ | ✗ | no_edge | 无边；无候选 |
| `P1-H20` | 救应 | 己→甲 | 合 / 救应 | ✓ | ✓ | actor_none | 边 e001；候选 1 条 actor=null |

## 4. kind 映射与口径风险

映射表（`mechanism` 是底层机械类型；未登记的 kind/mechanism 一律报错，不静默当不过滤）：

| mechanism | 边 kind | 候选 kind |
|---|---|---|
| 制 | 不过滤 | 不过滤 |
| 合 | liuhe/wuhe | liuhe/wuhe |
| 冲 | chong/stem_chong | chong/stem_chong |
| 刑 | xing | xing |
| 穿 | chuan | chuan |
| 破 | po | po |
| 克 | ke | ke |
| 生 | sheng | sheng |
| 化 | sheng | sheng |
| 墓 | 无 | muku |

风险与歧义（写死口径，改即改尺子）：

1. **`制` 不过滤 kind**：原书只说「制」未说种类时，engine 的 chong/chuan/ke/liuhe 都可能承载；若改判为只认 `ke`，主口径边召回会下降（逐例表里 `kind_filter=any` 的行就是受这条影响的）。
2. **`墓` 不是边**：engine 不建墓边，只有 `relations.muku` 与「墓用」muku 候选。主口径按任务卡 §2.2 只认 `edges`，故 墓 4 例边召回恒为 0；dev 工具的 muku 等价口径见 §2，二者不混算。
3. **`墓` 方向与 dev 相反**：本 hold-out 的 `a` 是库（施力方），engine 墓用候选的 `actor` 是入库方，命中候选时方向为 `reversed`——这是标注约定对立，不是引擎 bug（本版：`P1-H14`、`P1-H15`、`P1-H16`）。
4. **`化` 只能借 `sheng`**：engine 无「化」边；`化` 映射到 sheng 是 dev 同口径的近似，且 sheng 源端在生者一侧，与答案「化者=受生方」的 actor 方向天然相反（本版 `reversed`：`P1-H09`、`P1-H10`、`P1-H11`、`P1-H18`）。
5. **方向只用候选的 actor**：`relations.edges` 无 actor 字段（G2：冲/刑/穿/破不设方向）；故边命中不等于方向可判，方向分母仍按答案 actor 非空计。
6. **地址多解**：单字干支或十神在不同柱重复出现时解析成多个地址，任一组合命中即算；本版逐例多解如下（会抬高召回上限，属必要条件检验）：

- `P1-H06`：b=酉→D.b,M.b
- `P1-H09`：a=巳→D.b,H.b,Y.b
- `P1-H10`：a=午→D.b,M.b,Y.b
- `P1-H13`：a=辰→H.b,Y.b
- `P1-H14`：b=酉→H.b,M.b
- `P1-H15`：b=亥→H.b,M.b
- `P1-H16`：a=未→D.b,H.b
- `P1-H18`：a=丁→H.s,Y.s；b=卯→D.b,H.b
- `P1-H19`：b=申→D.b,Y.b

7. **性别**：H17/H18 原书未注明性别，engine 只认 乾/坤，按乾起盘（`gender_used` 逐例可见）；P1 评的是原局关系，方向召回不依赖性别。

## 5. 复跑

```bash
python -m tools.p1_holdout_eval --holdout META/p1-holdout-v1.json --answers META/p1-holdout-answers-v1.json
python -m tools.p1_holdout_eval ... --json   # stdout 打完整 JSON
```

同一引擎两次运行产物逐字节一致（无时间戳、地址集合排序、case 顺序取 answers 文件顺序）。
