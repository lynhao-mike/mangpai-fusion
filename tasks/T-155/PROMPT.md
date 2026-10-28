# T-155 · M2-Y-395 v2：换「婚姻质量」标签重测方向

- 状态：🔵 Ready for Execution
- 优先级：**P1（与 T-152 并行）**
- 创建：2026-10-28（中枢）
- 依据：`docs/reviews/m2y395-verdict-v1.md` §4–§5；T-153 标签 v1；T-151 方向规则
- 前置：T-151（`37f500fb`）、T-153（已完成）

## 0. 一句话

用 T-153 的 **342 例「负面婚姻事件」标签**，把 T-151 的「夫妻宫被冲，谁制谁」重跑一遍。**只回答一件事：上次否证是「标签错」还是「假设错」。** 不建四态、不接产品。

## 1. 预注册（卡内即协议，不得中途改）

### 1.1 总体

- 标签集：`META/marriage-quality-labels-v1.json` 中 `label ∈ {negative, positive}` 的 **342 例**（40 例 unknown 排除）。
- **计数单位 = 一个人（case）**，不是冲边。同一个人多条冲边只算一例；方向冲突记 `ambiguous`（弃权）。
- 敏感性集：从 342 剔除 T-153 §9 中落在 342 内的 6 例已知误判（947 是 `unknown`、不在 342）→ **336 例**。
  实测这 6 例均未触发（无日支冲），scored 集不变；该敏感性只证明「判定不依赖这 6 例」，不能检验 scored 内标签噪声。

### 1.2 触发器与方向

与 T-151 相同（原文锚点：`d01-deep-read.md`、`21.大连…:701`）：

- 触发器：原局存在 `kind=chong` 的边且成员含日支 `D.b`；只看 `scope=natal`。
- 方向：`KE_MAP[wx(D.b)] == wx(other)` → `self_controls`；`KE_MAP[wx(other)] == wx(D.b)` → `other_controls`；其余（含同五行）→ `no_ke`。
- 同一人多条同向冲边 → 该方向；方向冲突 → `ambiguous`；无冲 → 未触发。

### 1.3 预测与编码（用 T-150 计分器）

- `self_controls`（我制）→ 预测「婚姻不差」→ 字母 **`P`**（negative=false）。
- `other_controls`（被制）→ 预测「负面婚姻事件」→ 字母 **`N`**（negative=true）。
- `no_ke` / `ambiguous` → 弃权（`prediction_letters: []`，`triggered: true`）。
- 无冲 → `triggered: false`，不计分。

用 `tools/claim_metric` 计分：`answer_letter` 由标签映射（negative=true → `N`，false → `P`）。

### 1.4 基线与判据（预注册）

- 基线：**同一 scored 集上的多数类字母**（`baseline_single`），不借用 342 全集的 54.39%。
- 判据：Wilson 95% 置信区间。
  - 上界 < 基线 → 「方向 alone」在新标签上**仍被否证**；
  - 下界 > 基线 → 方向有信号（上次否证可能是标签伪影）；
  - 其余 → **样本不足**，不得宣布有效。
- **硬门槛：`n_scored < 50` 一律判「样本不足」**，不管区间怎么落。
- 两套敏感性（342 与 336）结论若翻转 → 判「**标签不足以裁决**」。

## 2. 要做的事

### 2.1 方向（不读标签）

新建 `tools/m2y395_real_direction.py`：

- 从 `META/timing-eval-set-v1.json` 取 `usable_for_timing=true` 的案例，用 `birth_dt` + `gender`（男→乾、女→坤）建盘（`engine.api` / `engine.v5` 既有入口；不要猜）。
- 对每人取 `relations.edges` 中 `kind=chong` 且成员含 `D.b` 的边，按 §1.2 判方向；多人多边按人聚合。
- **本模块不得出现 `negative` / `label` / `marriage-quality` 字样**（中枢会 grep）；标签只在 2.2 并入。
- 产出 `META/m2y395-v2-cases.json`：`case_id`、`pillars`、`day_branch`、`edges`、`direction`、`prediction_letters`、`triggered`。
- 建盘失败逐例列原因。

### 2.2 并入标签并计分

新建 `tools/m2y395_real_score.py`：

- 按 `case_id` 并入 T-153 的标签，产出 `META/m2y395-v2-scored.json`（加 `answer_letter`、`label`、`branch`、`claim_id="M2-Y-395"`、`outcome="unknown"`）。
- 用 `META/eval-protocols/m2y395-v2.yaml`（按 `META/eval-protocol-v1.md` 的 11 字段写）跑 `python -m tools.claim_metric`。
- 报：`n_total / n_triggered / n_scored / n_abstain / n_self / n_other / n_no_ke / accuracy / baseline / wilson_ci`；342 与 336 两套都报。
- 产出 `META/m2y395-v2-report.md`：预注册、触发率、两套敏感性、判定（只写「否证 / 有信号 / 样本不足 / 标签不足以裁决」）。

## 3. File Scope

**允许新建**

- `tools/m2y395_real_direction.py`
- `tools/m2y395_real_score.py`
- `META/eval-protocols/m2y395-v2.yaml`
- `META/m2y395-v2-cases.json`
- `META/m2y395-v2-scored.json`
- `META/m2y395-v2-report.md`

**只读**

- `META/timing-eval-set-v1.json`
- `META/marriage-quality-labels-v1.json`
- `engine/facts/**`、`engine/api/**`、`engine/predicates/types.py`
- `tools/m2y395_direction.py`（复用方向逻辑，不许改）

**禁止**

- 改 T-153 标签、T-148 评测集、T-151 产物、`engine/**`、`theory/**`、`sources/**`、既有测试
- 方向模块读标签；按标签挑案例；为凑结论改方向规则
- `git commit / push / checkout / stash / reset / clean`

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.m2y395_real_direction   # 退出码 0
.venv\Scripts\python.exe -m tools.m2y395_real_score       # 退出码 0，打印两套敏感性
.venv\Scripts\python.exe -m tools.claim_metric --protocol META/eval-protocols/m2y395-v2.yaml \
  --cases META/m2y395-v2-scored.json                      # 退出码 0
.venv\Scripts\python.exe -m pytest -q                     # 0 failed，passed >= 1099
```

中枢额外检查：

- `grep -E "negative|label|marriage-quality" tools/m2y395_real_direction.py` → 0 命中；
- 抽查 3 人：日支、冲边 ID、方向、标签逐项核对；
- 342 与 336 两套数字都能复跑；
- 若 `n_scored < 50`，报告必须写「样本不足」，不许写「有效/无效」。

## 5. 回报格式（`tasks/T-155/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（三条命令 + 两套敏感性表）
3. **未完成与风险**（触发率低、建盘失败、标签噪声）
4. **下游须知**（判定是「否证 / 有信号 / 样本不足 / 标签不足以裁决」中的哪一个）

## 6. 禁止

- 不许为了「让方向活过来」改 §1.2 的规则或挑案例。
- 不许把 40 例 unknown 折进分母。
- 不许把「样本不足」写成「有效」。
