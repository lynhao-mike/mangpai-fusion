# T-117 · 最小对比对（minimal contrastive pair）构造

- 状态：🔵 Ready for Execution
- 优先级：P0（批次 1 的前置，没有它 120 条会一起错）
- 创建：2026-10-26（中枢）
- 依赖：`engine/claims/condition_ir/`、`theory/claims/conditions-v2/pilot-20.yaml`

## 1. 问题

「只改一个字」算不算最小扰动？以「印星空亡 → 学业难成」为例，反例是把空亡改成不空，还是把印星换掉？

**两者都不对**，原因不同：

| 改法 | 实际测到什么 | 为什么不可用 |
|---|---|---|
| 改「空亡」 | 测的是结果原子 | 空亡是派生事实，不能直接改；只能改日柱/年柱，而改日柱会同时改日主 → 全盘十神重算，不是最小扰动 |
| 改「印星」 | 测的是**另一个子句**（有无印星） | 断语因别的原因失效，属错误归因，会污染指标 |

## 2. 定义（可自动验证）

> **最小扰动 = 该断语所引用原子的真值向量，只翻转 1 位，其余位不变。**

```text
atom_vector(chart, claim) = [evaluate(a, chart) for a in atoms_of(claim)]
admissible(pair) = hamming(atom_vector(orig), atom_vector(cf)) == 1
```

不靠感觉，靠汉明距离（Hamming distance）。同时校验：

1. 反例盘必须是合法 60 甲子组合；
2. 日干不得改（改日主 → 所有十神定义变）；
3. 优先改**时支**：不影响日柱旬空与年柱旬空，空亡集保持稳定；
4. 改支时必须**同阴阳**（阳干配阳支、阴干配阴支），否则时柱非法；
5. 新支要保住其它必需原子（例：仍须藏印，使 `hidden_god(印)` 仍为真）。

## 3. 三级对比对

| 级别 | 做法 | 覆盖 | 抓什么 |
|---|---|---|---|
| **A 逻辑层**（合成，全自动） | 在 `ChartContext` 上注入桩事实，翻转单个原子返回值，断言整条断语按布尔逻辑变化 | 100% 原子 | `and/or/not` 写反、否定词丢失 |
| **B 语义层**（真实盘，单字扰动） | 按 §2 定义构造反例盘 | 每条断语的关键原子 | 半截编译、地址绑错（日坐七杀→年柱见七杀） |
| **C 阴性对照** | 取同域另一条断语的正例盘，断言本条不触发 | 每条断语 ≥1 张 | 条件太宽（开火率过高） |

## 4. 指标

| 指标 | 定义 | 门槛 |
|---|---|---|
| `flip_accuracy` | Tier B 中按预期翻转的比例 | ≥90% |
| `inadmissible_rate` | 无法用单字扰动达成汉明距离 1 的比例 | 记录，不设门槛；>30% 说明条件耦合过强，需拆条 |
| `specificity_fp` | Tier C 误触发率 | ≤10% |
| `logic_pass` | Tier A 通过率 | 100% |

## 5. 例外

若断语条件本身就是结构性事实（如「日坐空亡」），反例必须改日柱，此时允许两处改动，标记 `structural_pair`，单独统计，不计入 `inadmissible_rate`。

## 6. 产出

- `theory/claims/contrastive-pairs/pilot-20.yaml`：每对含 `claim_id / atom / orig_chart / counterfactual_chart / expected_flip / hamming / admissible`
- `tools/claim_contrastive_check.py`：自动校验汉明距离、合法性、并输出 `flip_accuracy`
- 报告并入 `META/claim-condition-pilot-v1.md`

## 7. 需要人确认

- 「同阴阳替换」「优先改时支」这两条口径是否符合命理习惯（尤其涉及合冲关系时，改时支可能牵动与年/月的合冲）。
- 哪些原子算「决定结论的关键原子」——建议取 AND 链全部必需原子 + OR 分支各一。
