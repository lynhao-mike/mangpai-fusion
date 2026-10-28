# T-154 · 首条产品断语正确性分数（婚姻两条规则）

- 状态：🔵 Ready for Execution
- 优先级：**P1（T-152 + T-153 已落地）**
- 创建：2026-10-28（中枢）
- 依据：`docs/reviews/verdict-chatgpt6.md` §4.4；T-152 §9；T-153 §9
- 前置：T-152（`triggered` 字段）、T-153（342 例标签）

## 0. 一句话

用 342 例「负面婚姻事件」标签，给两条婚姻产品规则打出**第一个真实正确性分数**。
**只用 `triggered`，不用 `outcome`**——T-152 干跑已证明反条件与正条件同阈值，翻转会压掉 66.4% 的断语（健康两档 100%）。

这是项目唯一判据的第一次落地：**产品断语到底比基线强不强？**

## 1. 预注册（卡内即协议，不得中途改）

### 1.1 规则选择（先写死，不许换）

- `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1`（段派）
- `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1`（杨派）

理由：T-152 干跑里只有这两条既有足够触发（382 例中 153 / 231），又有 T-153 可用的婚姻质量标签。
其他规则要么没有对应结局标签（事业/财富/健康），要么触发太少（段派 `WEALTH-DEBT` 仅 2/382）。**不许因为结果不好换规则。**

### 1.2 样本

- 标签集：`META/marriage-quality-labels-v1.json` 中 `label ∈ {negative, positive}` 的 **342 例**；40 例 `unknown` 排除。
- 敏感性集：剔除 T-153 §9 的 7 例已知误判 → **335 例**；两套都报，结论翻转判「**标签受限**」。

### 1.3 触发与预测

- 规则 `triggered=True` → 预测 **`N`**（negative，即「存在离婚/再婚风险」）。
- 规则 `triggered=False` → **弃权**（不进分母）。
- **不使用 `outcome`**：反条件语义未修好（T-152 §9），用它等于用坏门筛样本；本卡只测正条件。
- 另报 `triggered=True 且 outcome=fail` 的 n 与 accuracy（**仅描述，不判定**），让中枢看到反条件若可用会怎样。

### 1.4 基线与判据

- 基线：**同一 scored 集上的多数类字母**（`baseline_single`），不借用 342 全集的 54.39%。
- 判定词只用三个：**「超过基线」/「未超过基线」/「样本不足」**。
  - `accuracy > baseline` 且 Wilson 95% 下界 > baseline → 超过基线；
  - Wilson 95% 上界 < baseline → 未超过基线；
  - 其余 → 样本不足；
  - `n_scored < 50` → 一律「样本不足」。
- 本卡是**探索性首测**（两条规则同时测），不得写「有效 / 无效」；确证需另一张单规则预注册卡。
- 两条规则分别报，**不许合并、不许只报好的那条**。

## 2. 要做的事

新建 `tools/product_claim_eval.py`：

- 从 `META/timing-eval-set-v1.json` 取 `usable_for_timing=true` 的案例，建盘 + `build_chart_feature_vector`。
  **复用 `tools/rule_contract_report.py` 的建盘/上下文逻辑**（只读 import；不可 import 就复制最小逻辑并注明来源行号，不许改该文件）。
- 对两条规则逐例 `evaluate_rule`，取 `triggered`；并入 T-153 标签；编码 `N` / `P`。
- 用 `engine.claims.metrics.score()`（或 `tools.claim_metric`）出分。
- 预注册协议：每条规则一个 YAML，放 `META/eval-protocols/product-marriage-duan-v1.yaml`、`...-yang-v1.yaml`。
- 产物：
  - `META/product-marriage-score-v1.json`（两规则、两套敏感性、逐例 case_id/triggered/label/prediction）
  - `META/product-marriage-report-v1.md`（方法、表、判定、已知标签噪声）
- 控制台打印两行：`rule | n_triggered | n_scored | accuracy | baseline | wilson | verdict`。

## 3. File Scope

**允许新建**

- `tools/product_claim_eval.py`
- `META/eval-protocols/product-marriage-duan-v1.yaml`
- `META/eval-protocols/product-marriage-yang-v1.yaml`
- `META/product-marriage-score-v1.json`
- `META/product-marriage-report-v1.md`

**只读**

- `META/timing-eval-set-v1.json`、`META/marriage-quality-labels-v1.json`
- `theory/production/claim-rules-v1.yaml`
- `engine/claims/rule_loader.py`、`engine/claims/metrics.py`、`engine/features/**`、`engine/api/**`
- `tools/rule_contract_report.py`、`tools/claim_metric.py`

**禁止**

- 改规则 YAML、改阈值、改 `rule_loader.py`、改 T-152/T-153 产物、改既有测试
- 换规则、合并两条规则、按结果挑案例
- 用 `outcome` 筛样本
- `git commit / push / checkout / stash / reset / clean`

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.product_claim_eval        # 退出码 0，打印两行
.venv\Scripts\python.exe -m pytest -q                       # 0 failed，passed >= 1099
```

中枢额外检查：

- 两条规则各自的 `n_triggered / n_scored / accuracy / baseline / Wilson` 都在 JSON 里；
- 342 与 335 两套都能复跑；
- `git diff theory/production/claim-rules-v1.yaml` 为空；
- 我抽 1 例 triggered、1 例 untriggered 回评测集核对；
- 报告没有出现「有效 / 无效」，只有三档判定词。

## 5. 回报格式（`tasks/T-154/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（两行表 + 两套敏感性）
3. **未完成与风险**（样本量、标签噪声、触发率）
4. **下游须知**（每条规则的判定词；是否触发样本不足）

## 6. 禁止

- 不许为了「让产品看起来行」调阈值、换规则、合并规则。
- 不许把 `outcome` 偷偷当成筛子。
- 不许把「样本不足」写成「超过基线」。

## 7. Amendments（中枢裁决，2026-10-28 23:05）

### 7.1 敏感性集是 **336**，不是 335（中枢笔误）

T-153 §9 的 7 例里，`RF-2026-000947` 的 label 是 `unknown`，**不在 342 内**；从 342 剔除能落进去的 6 例 = **336**。
不许为了凑 335 另挑 1 例。报告与 JSON 必须写明「卡面声明 335、实际 336、差 1 例因 947 不在 342」。

### 7.2 判定口径改为两比例检验（数学原因，不是结果原因）

**退化证明**：本卡的规则是「triggered=True 预测恒为 N，否则弃权」，于是 scored 集 = 触发集。
`accuracy = 触发集负率`；若 N 是 scored 集多数类，`baseline_single` 也等于同一个负率 →
**accuracy 恒等于 baseline**，「超过基线」分支在数学上不可达。这是尺子对单标签规则退化，不是断语好坏。

因此判定改为：

- 比较 `P(negative | triggered)` 与 `P(negative | not triggered)`（同一 342 标签集）。
- 报：两组 n、负率、差值（百分点）、**Newcombe 95% 置信区间**、**Fisher 精确检验双侧 p**。
- 判定词：
  - 差值 95% 置信区间下界 > 0 → **「有区分力」**；
  - 上界 < 0 → **「反向」**；
  - 其余 → **「无差异 / 样本不足」**；
  - 任一组 n < 30 → **「样本不足」**。
- `claim_metric` 的 `accuracy / baseline_single` **仍照报，但只作描述，不作判定**；报告必须写明为什么。
- 只依赖标准库（`math.comb` 可算 Fisher）；**不许新增依赖**。

### 7.3 先看到的数字保留

Worker 已看到的 55.07%（段派 76/138）、52.45%（杨派 107/204）必须保留在报告里，不许删。
新检验的 `not triggered` 组尚未计算，因此这不是「看结果改判据」；改动依据是上面的恒等式，且在最终跑分前登记。
