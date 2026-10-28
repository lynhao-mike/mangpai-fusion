# M2-Y-395 v2 · 「夫妻宫被冲，谁制谁」换「婚姻质量」标签重测报告

- 协议：`m2y395-v2`（claim `M2-Y-395`，冻结 `2026-10-28T22:34:00+08:00`，commit `3c49d91d`）
- 任务：T-155；生成：`python -m tools.m2y395_real_score`（确定性，无运行时间戳）
- 回答的唯一问题：T-151 的否证，是**标签错**还是**假设错**。

## 1. 预注册（卡内 §1，跑分前冻结）

- **触发器**：原局（relations.edges 中 scope=natal、kind=chong）存在成员含日支地址 D.b 的边，即「夫妻宫被冲」。计数单位 = 一个人（case）：同一人多条冲边只算一例，多条同向取该方向，方向冲突（self_controls 与 other_controls 并存，或含 no_ke 的混合）记 ambiguous。无冲的 case 记 triggered=false，不进分母。
- **方向**：「夫妻宫被冲，谁制谁」：对本气五行比较，KE_MAP[wx(D.b)] == wx(other) → self_controls（我制对方）；KE_MAP[wx(other)] == wx(D.b) → other_controls（对方制我）；其余（含同五行）→ no_ke。判定函数复用 tools/m2y395_direction.py 的 direction_of（只读，未改）；KE_MAP/ZHI_TO_WUXING 取自 engine/predicates/types.py:60-79。方向来自盘面与五行克序，不追认答案、不按标签挑案例。
- **预测**：`self_controls` → `P`（婚姻不差）；`other_controls` → `N`（负面婚姻事件）；`no_ke` / `ambiguous` → 弃权（`prediction_letters: []`）；无冲 → 未触发。
- **标签映射**：`negative` → `N`，`positive` → `P`；`unknown` 40 例不折入分母。
- **基线**：baseline_single：同一 scored 集上出现最多的单个字母的命中率（并列按字母序）。不借用 342 全集的 54.39%（多数类随 scored 集变化，必须在本集上重算）。
- **判据**：先看样本量：n_scored < 50 一律判「样本不足」，不论区间如何落。否则按 Wilson 95% 区间判定：上界 < baseline_single → 「否证」（方向 alone 在新标签上仍被否证）；下界 > baseline_single → 「有信号」；其余 → 「样本不足」，不得宣布有效。342 与敏感性两套结论若翻转 → 判「标签不足以裁决」。baseline_same_k 仅作乐观参考，不参与判定。

## 2. 数据与触发

- 方向源：`META/timing-eval-set-v1.json` 中 `usable_for_timing=true` 的 **382** 例，全部建盘成功（失败 0）。
- 日支有冲（按人计）：**67 / 382 = 17.54%**。
- 方向分布：self_controls 20、other_controls 28、no_ke 19、ambiguous 0、no_chong 315。
- 标签分母：342（negative 186 / positive 156），40 例 unknown 不计。

## 3. 342 例全集

| 指标 | 值 |
|---|---|
| n_total | 342 |
| n_triggered | 60 |
| n_scored | 43 |
| n_correct | 23 |
| n_abstain | 17 |
| n_not_triggered | 282 |
| n_self（触发人数） | 20 |
| n_other（触发人数） | 23 |
| n_no_ke（弃权） | 17 |
| n_ambiguous（弃权） | 0 |
| accuracy | 0.5349 |
| baseline_single | N / 0.5814 |
| baseline_same_k（乐观参考） | 0.5814 |
| wilson_ci_95 | [0.3892, 0.6749] |

| branch | correct / n | accuracy |
|---|---|---|
| no_chong | 0 / 0 | n/a |
| no_ke | 0 / 0 | n/a |
| other_controls | 14 / 23 | 0.6087 |
| self_controls | 9 / 20 | 0.4500 |

## 4. 敏感性集（剔除 T-153 §9 的 7 例已知误判）

- 剔除名单 7 例，**在本集内命中 6 例** → n_total = **336**。
- 口径差异（如实记录）：卡内 §1.1 写「7 例 → 335」，该算式假定 7 例都在 342 内；其中 `RF-2026-000947` 的标签是 `unknown`（neutral），本就不在 342 分母里，因此按名单剔除后是 **336** 例，不是 335。不得为凑 335 另挑一例。
- 命中名单的 6 例中，触发 **0** 例：sensitivity 的 scored 集与 342 全集完全一致（43 例）。故这套敏感性只能证明「判定不依赖这 6 例」；它对 scored 集内的标签噪声不构成检验。

| 指标 | 342 全集 | 敏感性集 |
|---|---:|---:|
| n_total | 342 | 336 |
| n_triggered | 60 | 60 |
| n_scored | 43 | 43 |
| n_correct | 23 | 23 |
| n_abstain | 17 | 17 |
| n_self | 20 | 20 |
| n_other | 23 | 23 |
| n_no_ke | 17 | 17 |
| n_ambiguous | 0 | 0 |
| accuracy | 0.5349 | 0.5349 |
| baseline_single | 0.5814 (N) | 0.5814 (N) |
| wilson_ci_95 | [0.3892, 0.6749] | [0.3892, 0.6749] |

## 5. 判定（四选一：否证 / 有信号 / 样本不足 / 标签不足以裁决）

- 342 全集：**样本不足** —— n_scored=43 < 50（硬门槛，不看区间）
- 敏感性集：**样本不足** —— n_scored=43 < 50（硬门槛，不看区间）
- **最终判定：样本不足** —— 两套一致：n_scored=43 < 50（硬门槛，不看区间）

补充观察（**不改变上面的判定**，仅记录点估计方向）：

- 整体 accuracy 0.5349 **低于**同集基线 N 的 0.5814；self_controls 分支 9/20，other_controls 分支 14/23。
- 也就是说，没有任何「方向有信号」的迹象；但预注册的「否证」要求 Wilson **上界** (0.6749) 低于基线，实际未满足，故不得升级为「否证」，只能按硬门槛判「样本不足」。

## 6. 风险与边界

1. **样本量**：scored 集只有 43 例（硬门槛 50）。Wilson 区间 [0.3892, 0.6749] 宽到跨过基线，任何方向的结论都不成立；本报告只能写「样本不足」，不能写成「有效/无效」。
2. **触发率低**：按人计只有 17.54% 的人日支有冲，342 集内触发 60 人，其中 17 人 no_ke 弃权、0 人 ambiguous；方向规则能裁决的面很窄。
3. **标签噪声**：T-153 为关键词/极性标签，已知 7 例误判保留未改；敏感性集的作用是证明结论不依赖这 7 例，不是把噪声洗掉（且名单内命中的 6 例均未触发，scored 集不变）。
4. **计数单位变更**：T-151 以冲边为一例，本报告以人一例。两者不可直接比 accuracy，只能比「方向本身是否被否证」这一判断。
5. **不追认答案**：方向只由 `KE_MAP` 与本气五行决定，未读标签、未按标签挑案例、未为结论改规则。

## 7. 复跑

```bash
.venv\Scripts\python.exe -m tools.m2y395_real_direction
.venv\Scripts\python.exe -m tools.m2y395_real_score
.venv\Scripts\python.exe -m tools.claim_metric --protocol META/eval-protocols/m2y395-v2.yaml --cases META/m2y395-v2-scored.json
```

- 输入指纹（342 全集，`score()` 的 input_sha256）：`461863bd219f5c40099769964c9c084903732e6a8d9e0fa29bc46917e395deca`
- 输入指纹（敏感性集）：`02477ab8452e625d80b5be75421637ef192bf28d96ac33fa44fc028450b95f91`
