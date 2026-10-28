# T-154 · 首条产品断语正确性分数（婚姻两条规则）

- 任务：`T-154`（`tasks/T-154/PROMPT.md`，含 §7 Amendments）
- 性质：**探索性首测**；本报告只给预注册判定词，不作规则成立/不成立的终局裁决。
- 数据：`META/timing-eval-set-v1.json`（`usable_for_timing=true`，382 例）+ `META/marriage-quality-labels-v1.json`（`label ∈ {negative, positive}`，342 例；unknown 40 例不折入）。
- 触发：`evaluate_rule(...).triggered`。**只用 triggered**；`outcome` 不参与触发、计分与筛样（T-152 §9）。
- 预测：triggered=True → `N`；triggered=False → 弃权（不进 `claim_metric` 分母）。
- 判定（PROMPT §7.2）：两比例检验，比较 `P(negative | triggered)` 与 `P(negative | not triggered)`；差值（百分点）用 **Newcombe 95% CI**，p 值用 **Fisher 精确检验双侧**。
- 判定词：任一组 n < 30 → 样本不足；CI 下界 > 0 → 有区分力；CI 上界 < 0 → 反向；其余 → 无差异 / 样本不足。
- `claim_metric` 的 `accuracy / baseline_single` 仍照报，但**只作描述，不作判定**（退化证明见 §7）。

## 1. 样本与分母

| 项 | 数 |
|---|---:|
| `usable_for_timing=true` | 382 |
| `label ∈ {negative, positive}`（主样本） | 342 |
| negative / positive | 186 / 156 |
| unknown（排除，不折入） | 40 |
| 敏感性集 | 336（卡面原写 335） |

## 2. 主结果：两比例检验（342 例）

| 规则 | 触发组 n / 负 | 触发组负率 | 未触发组 n / 负 | 未触发组负率 | 差值（百分点） | Newcombe 95% CI（pp） | Fisher 双侧 p | 判定 |
|---|---:|---:|---:|---:|---:|---|---:|---|
| `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | 138 / 76 | 0.5507 | 204 / 110 | 0.5392 | +1.15 | [-9.54, 11.72] | 0.9119 | **无差异 / 样本不足** |
| `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | 204 / 107 | 0.5245 | 138 / 79 | 0.5725 | -4.80 | [-15.28, 5.93] | 0.4387 | **无差异 / 样本不足** |

差值 = 触发组负率 − 未触发组负率；正号表示触发组负面婚姻事件更多。

## 3. 敏感性（实际 336 例）

> 卡面声明 335、实际 336、差 1 例因 RF-2026-000947 的 label 是 unknown、不在 342；从 342 剔除能落进去的 6 例 = 336。不许为凑 335 另挑 1 例。

- 剔除的 case_id（6 例）：`RF-2026-000495`、`RF-2026-000560`、`RF-2026-000544`、`RF-2026-000528`、`RF-2026-000845`、`RF-2026-000355`
- 卡面名单中不在 342 的 case_id：`RF-2026-000947`

| 规则 | 触发组 n / 负 | 触发组负率 | 未触发组 n / 负 | 未触发组负率 | 差值（百分点） | Newcombe 95% CI（pp） | Fisher 双侧 p | 判定 |
|---|---:|---:|---:|---:|---:|---|---:|---|
| `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | 137 / 75 | 0.5474 | 199 / 108 | 0.5427 | +0.47 | [-10.28, 11.13] | 1.0000 | **无差异 / 样本不足** |
| `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | 201 / 105 | 0.5224 | 135 / 78 | 0.5778 | -5.54 | [-16.09, 5.29] | 0.3715 | **无差异 / 样本不足** |

两套判定是否翻转：未翻转。

## 4. `claim_metric` 描述（**不判定**）

| 规则 | 样本 | n_triggered | n_scored | accuracy | baseline_single | Wilson 95% |
|---|---|---:|---:|---:|---|---|
| `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | full_342 | 138 | 138 | 0.5507 | 0.5507（N 76/138） | [0.4675, 0.6312] |
| `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | sensitivity_336 | 137 | 137 | 0.5474 | 0.5474（N 75/137） | [0.4639, 0.6284] |
| `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | full_342 | 204 | 204 | 0.5245 | 0.5245（N 107/204） | [0.4562, 0.5920] |
| `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | sensitivity_336 | 201 | 201 | 0.5224 | 0.5224（N 105/201） | [0.4536, 0.5904] |

Worker 在改判据前已看到的两个数保留在此：段派 **55.07%（76/138）**、杨派 **52.45%（107/204）**。它们等于各自 scored 集的负率，也等于 `baseline_single`（N 为多数类），因此不能用于「超过基线」判定。

## 5. 反条件描述（`outcome=fail`；仅描述，不判定）

这些例已 `triggered=True`，仍按 `N` 计入 `claim_metric`；本表只回答「若反条件可用会怎样」，不改变任何判定词。

| 规则 | 样本 | n | n_correct | accuracy | Wilson 95% |
|---|---|---:|---:|---:|---|
| `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | full_342 | 112 | 58 | 0.5179 | [0.4263, 0.6083] |
| `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | sensitivity_336 | 111 | 57 | 0.5135 | [0.4216, 0.6045] |
| `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | full_342 | 123 | 58 | 0.4715 | [0.3855, 0.5593] |
| `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | sensitivity_336 | 120 | 56 | 0.4667 | [0.3798, 0.5556] |

## 6. 已知标签噪声

T-153 §9 保留的 7 例已知误判：

| case_id | 类型 | label | 在 342 |
|---|---|---|---|
| `RF-2026-000495` | 否定语境「未结婚」 | positive | 是 |
| `RF-2026-000560` | 否定语境「未结婚」 | positive | 是 |
| `RF-2026-000544` | 第三人称「父母离婚」 | negative | 是 |
| `RF-2026-000528` | 第三人称 | negative | 是 |
| `RF-2026-000845` | 第三人称 | negative | 是 |
| `RF-2026-000947` | 繁体「離婚」 | unknown | **否**（不在 342） |
| `RF-2026-000355` | 繁体「離婚」 | positive | 是 |

上游已知噪声（T-153 §9）：`RF-2026-000066` 的 positive 实为恋爱；`RF-2026-000704` 的 negative 实为抑郁文本。模型误差不得全算给断语。

## 7. 判据退化与改判说明（PROMPT §7.2）

- 规则是「triggered=True 恒预测 N，否则弃权」，所以 `claim_metric` 的 scored 集 = 触发集，`accuracy` = 触发集负率。
- 当 N 是 scored 集多数类时，`baseline_single` 也是同一个负率 → `accuracy` 恒等于 `baseline`；「超过基线」分支在数学上不可达。
- 这是尺子对单标签规则退化，不是断语好坏。因此主判定改为两比例检验；`accuracy / baseline_single / Wilson` 只作描述。
- 改判据的依据是上述恒等式，且在计算未触发组之前登记（PROMPT §7.3）；不是看到结果后改判据。

## 8. 逐规则口径与触发

### `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1`

- 流派 / 任务：duan / marriage.divorce_or_remarriage
- 正条件：independent_signal_count >= 2；active_path_count >= 1
- 排除条件：evidence_completeness != full
- 反条件：independent_signal_count <= 2
- 342：n_evaluated=342，n_triggered=138，n_scored=138，n_untriggered=204，n_not_evaluated=0，n_abstain=0，n_missing_answer=0，trigger_rate=0.4035
- 336：n_triggered=137，n_untriggered=199，verdict=无差异 / 样本不足

### `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1`

- 流派 / 任务：yang / marriage.divorce_or_remarriage
- 正条件：sex 为真；spouse_star_basis ∈ [wealth, official]；independent_signal_count >= 2
- 排除条件：evidence_completeness != full；sex 为假
- 反条件：independent_signal_count <= 2
- 342：n_evaluated=342，n_triggered=204，n_scored=204，n_untriggered=138，n_not_evaluated=0，n_abstain=0，n_missing_answer=0，trigger_rate=0.5965
- 336：n_triggered=201，n_untriggered=135，verdict=无差异 / 样本不足

### 口径观察（杨派规则，未改规则）

- 生产上下文（`engine/v5/yang_runner.py:94`）把 `sex` 传为 `male` / `female` 字符串；规则里的 `sex truthy` 条件与 `sex falsy` 排除对两个非空字符串同真同假，因此该规则实际未按性别门控（`theory/production/claim-rules-v1.yaml:240-245`）。本卡沿用 deployed 口径、不改规则，仅记录供后续规则卡裁决。

## 9. 复现

```text
.venv\Scripts\python.exe -m tools.product_claim_eval
.venv\Scripts\python.exe -m pytest -q
```

- 逐例明细：`META/product-marriage-score-v1.json`（`full_342.cases` 342 行、`sensitivity_336.cases` 336 行，均含 case_id / triggered / outcome / label / prediction_letter）。
- 预注册：`META/eval-protocols/product-marriage-duan-v1.yaml`、`META/eval-protocols/product-marriage-yang-v1.yaml`。
- 建盘失败 / 段派结构失败：0 例。
- 无时间戳；case 按 case_id 排序；同一输入两次运行逐字节一致。

