# T-154 BRIEF · 首条产品断语正确性分数（婚姻两条规则）

- 任务卡：`tasks/T-154/PROMPT.md`（含 §7 Amendments）
- 执行者：子代理 G（2026-10-28）
- 状态：**完成，待中枢验收**（本简报的「通过」不算数，以中枢现场跑出的退出码为准）

## 1. 改动文件

新建：

| 文件 | 说明 |
|---|---|
| `tools/product_claim_eval.py` | 评测器：只读 import `tools/rule_contract_report.py` 的建盘/特征/runner 上下文；只取 `triggered`；主判定用两比例检验（Newcombe CI + Fisher 精确检验，均标准库实现） |
| `META/eval-protocols/product-marriage-duan-v1.yaml` | 段派预注册（卡 §1 + §7 Amendments） |
| `META/eval-protocols/product-marriage-yang-v1.yaml` | 杨派预注册（卡 §1 + §7 Amendments） |
| `META/product-marriage-score-v1.json` | 两规则 × 342/336 × 逐例（`case_id / triggered / outcome / label / prediction_letter`）+ 汇总 |
| `META/product-marriage-report-v1.md` | 方法、两比例检验表、描述性 `claim_metric` 表、反条件描述、标签噪声、判据退化说明 |

修改：

| 文件 | 改动 |
|---|---|
| `tasks/T-154/STATUS.md` | Execution Log 追加一行 |

**未改动（逐项确认）**：

- `git diff theory/production/claim-rules-v1.yaml` **为空**；`git diff engine/claims/rule_loader.py` **为空**。
- 未改阈值、T-152/T-153 产物、既有测试、`pyproject.toml`、`tasks/T-154/PROMPT.md`。
- 未执行任何 `git commit / push / checkout / stash / reset / clean`。
- `git status` 里 `tasks/T-153/PROMPT.md` 的修改是中枢的 335→336 更正；`META/m2y395-v2-*`、`tools/m2y395_*` 是 T-155 并行 Worker 的产物；均非本任务改动。

## 2. 原始输出

### 2.1 `python -m tools.product_claim_eval`（EXIT=0）

```text
T-154 产品断语正确性分数。样本 342 例（382 usable − 40 unknown）；敏感性 336 例（卡面原写 335；947 为 unknown 不在 342）。

[342] 判定：两比例检验（342 例）
rule | trig_n | trig_neg | trig_rate | not_n | not_neg | not_rate | diff_pp | newcombe_ci_pp | fisher_p | verdict
DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1 | 138 | 76 | 0.5507 | 204 | 110 | 0.5392 | +1.15 | [-9.54, 11.72] | 0.9119 | 无差异 / 样本不足
YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | 204 | 107 | 0.5245 | 138 | 79 | 0.5725 | -4.80 | [-15.28, 5.93] | 0.4387 | 无差异 / 样本不足

[336] 判定：两比例检验（敏感性）
rule | trig_n | trig_neg | trig_rate | not_n | not_neg | not_rate | diff_pp | newcombe_ci_pp | fisher_p | verdict
DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1 | 137 | 75 | 0.5474 | 199 | 108 | 0.5427 | +0.47 | [-10.28, 11.13] | 1.0000 | 无差异 / 样本不足
YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | 201 | 105 | 0.5224 | 135 | 78 | 0.5778 | -5.54 | [-16.09, 5.29] | 0.3715 | 无差异 / 样本不足

[342] claim_metric（仅描述，不判定）
rule | n_triggered | n_scored | accuracy | baseline | wilson | （claim_metric 仅描述，不判定）
DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1 | 138 | 138 | 0.5507 | 0.5507 | [0.4675, 0.6312]
YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | 204 | 204 | 0.5245 | 0.5245 | [0.4562, 0.5920]

[336] claim_metric（仅描述，不判定）
rule | n_triggered | n_scored | accuracy | baseline | wilson | （claim_metric 仅描述，不判定）
DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1 | 137 | 137 | 0.5474 | 0.5474 | [0.4639, 0.6284]
YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | 201 | 201 | 0.5224 | 0.5224 | [0.4536, 0.5904]

描述（不判定） outcome=fail 子集：DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1 n=112 accuracy=0.5179
描述（不判定） outcome=fail 子集：YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 n=123 accuracy=0.4715

已写出：META/product-marriage-score-v1.json
已写出：META/product-marriage-report-v1.md
```

### 2.2 `python -m pytest -q`（EXIT=0）

```text
1099 passed, 1 skipped, 1 warning in 99.44s (0:01:39)
EXIT=0
```

`1 skipped` 是 `tests/tools/test_bundle_pii.py` 的既有 T-114 跳（`.workbuddy-ai/make_bundle_v2.py` 缺失），非本任务引入；0 failed。

### 2.3 确定性（两次运行逐字节一致）

```text
product-marriage-score-v1.json  sha256=89e1016ad4db0a52…  equal=True
product-marriage-report-v1.md   sha256=b69f044c6745ea57…  equal=True
```

### 2.4 输入 / 预注册哈希

```text
META/timing-eval-set-v1.json            e7b7f770…b9b4f5
META/marriage-quality-labels-v1.json    59d3764b…b647d6
product-marriage-duan-v1.yaml           1c581da3…f4e59d
product-marriage-yang-v1.yaml           edc00e09…ba153ac
tools/product_claim_eval.py             906986ee…ece07dc4
```

### 2.5 关键数字（卡片要求的两行表 + 两套敏感性）

| 口径 | 规则 | n_triggered | n_scored | 触发组负率 | accuracy | baseline | Wilson 95% | 判定 |
|---|---|---:|---:|---:|---:|---|---|---|
| 342 | 段派婚姻 | 138 | 138 | 55.07%（76/138） | 0.5507 | 0.5507 | [0.4675, 0.6312] | 无差异 / 样本不足 |
| 342 | 杨派婚姻 | 204 | 204 | 52.45%（107/204） | 0.5245 | 0.5245 | [0.4562, 0.5920] | 无差异 / 样本不足 |
| 336 | 段派婚姻 | 137 | 137 | 54.74%（75/137） | 0.5474 | 0.5474 | [0.4639, 0.6284] | 无差异 / 样本不足 |
| 336 | 杨派婚姻 | 201 | 201 | 52.24%（105/201） | 0.5224 | 0.5224 | [0.4536, 0.5904] | 无差异 / 样本不足 |

两套判定**未翻转**。`accuracy / baseline` 只作描述（退化证明见报告 §7）；主判定是两比例检验：

| 口径 | 规则 | 未触发组负率 | 差值（pp） | Newcombe 95% CI（pp） | Fisher 双侧 p | 判定 |
|---|---|---:|---:|---|---:|---|
| 342 | 段派婚姻 | 53.92%（110/204） | +1.15 | [-9.54, 11.72] | 0.9119 | 无差异 / 样本不足 |
| 342 | 杨派婚姻 | 57.25%（79/138） | -4.80 | [-15.28, 5.93] | 0.4387 | 无差异 / 样本不足 |
| 336 | 段派婚姻 | 54.27%（108/199） | +0.47 | [-10.28, 11.13] | 1.0000 | 无差异 / 样本不足 |
| 336 | 杨派婚姻 | 57.78%（78/135） | -5.54 | [-16.09, 5.29] | 0.3715 | 无差异 / 样本不足 |

## 3. 未完成与风险

1. **卡面 335 → 实际 336**：T-153 §9 的 7 例里 `RF-2026-000947` 的 label 是 `unknown`、不在 342；从 342 剔除能落进去的 6 例 = 336。未为凑 335 另挑案例；卡 §7.1 已更正，T-153 §9 也由中枢同步更正。
2. **判定结果**：342 与 336 两套、两条规则全部为「**无差异 / 样本不足**」。触发组与未触发组的负率差：段派 +1.15 pp（336：+0.47）、杨派 −4.80 pp（336：−5.54）；Newcombe CI 均跨 0，Fisher p 均 > 0.4。**不许**写成「超过基线 / 未超过基线」，更不许写成规则成立 / 不成立的终局结论；这是探索性首测，不是确证。
3. **功效有限**：scored 组 n=138/204（336：137/201），差值 CI 宽约 ±10–16 pp。只有很大的组间差异才可能被检出；「无差异 / 样本不足」不等于规则没有方向性，也不等于规则成立。确证需另一张单规则预注册卡。
4. **标签噪声**：7 例已知误判中 6 例在 342（495/560/544/528/845/355），947 不在；敏感性已剔除这 6 例。上游另有 066（positive 实为恋爱）、704（negative 实为抑郁文本）两类噪声；标签是「负面婚姻事件」，不是「已离婚」。
5. **触发率**：段派 138/342 = 40.35%；杨派 204/342 = 59.65%。两组的 n 都 ≥ 30，判定不是被「任一组 n < 30」触发，而是 CI 跨 0。
6. **杨派 `sex` 门控观察（未改规则）**：生产上下文把 `sex` 传为 `male` / `female` 字符串，规则里的 `sex truthy` 条件与 `sex falsy` 排除对两个非空字符串同真同假，实际未按性别门控（女命 82/106 触发、男命 122/236 触发）。本卡沿用 deployed 口径、不改规则，记录供后续规则卡裁决。
7. **`outcome` 只作描述**：段派 `triggered=True 且 outcome=fail` n=112、accuracy=0.5179；杨派 n=123、0.4715。两者都低于各自触发组负率；若用反条件拦截会改变分母，但 T-152 §9 已裁决反条件未修好，本卡不用 `outcome` 筛样或判定。
8. **`claim_metric` 退化**：单标签规则 + 弃权使 `accuracy` 恒等于触发集负率；N 为多数类时 `baseline_single` 是同一负率，`accuracy` 恒等于 `baseline`。因此原「超过基线」判据不可达，按卡 §7.2 只作描述。
9. **建盘 / 结构失败 0 例**：342/342 全部 `n_evaluated`，`n_abstain=0`、`n_missing_answer=0`、`n_not_evaluated=0`。
10. **未新增测试**：T-154 File Scope 不含 `tests/`；验收用评测器两条命令 + 既有 1099 passed。

## 4. 下游须知

- **每条规则的判定词**：段派 `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` =「无差异 / 样本不足」；杨派 `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` =「无差异 / 样本不足」。342 与 336 均同、未翻转。
- **不是「样本不足」因 n < 30**：两组 n 都够；是差值 95% CI 跨 0。下游引用时必须带上「无差异」限定，不得只写「样本不足」暗示样本太小。
- **不要引用旧的「超过基线 / 未超过基线」**：卡 §1.4 的三档判据已被 §7.2 两比例检验替代；`accuracy` 与 `baseline_single` 相等是结构恒等式，不是成绩。
- **敏感性分母是 336，不是 335**。引用时写明「卡面原写 335、实际 336、差 1 例因 947 不在 342」。
- **复现**：`python -m tools.product_claim_eval`；两次运行 JSON/MD 逐字节一致。逐例明细在 `META/product-marriage-score-v1.json`：`rules[].full_342.cases` 342 行、`rules[].sensitivity_336.cases` 336 行（均含 `case_id / triggered / outcome / label / prediction_letter`）。
- **口径**：建盘/特征/runner 上下文只读复用 `tools/rule_contract_report.py`（`_build_ledger`、`_duan_active_path_count`、`_selections`），与 T-152 干跑同源；规则 YAML 与 `rule_loader.py` 零改动。
- **杨派性别门控**：如后续要按性别解读，先修规则契约（`sex truthy/falsy` 对字符串不起作用）；当前分数是「规则 as deployed」的分数。
