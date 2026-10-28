# T-153 · 婚姻质量标签 v1（负面婚姻事件）

- 状态：🔵 Ready for Execution
- 优先级：**P0（与 T-152 并行）**
- 创建：2026-10-28（中枢）
- 依据：`docs/reviews/m2y395-verdict-v1.md` §4–§5；T-148 评测集（`482d777b`）
- 前置：T-148 已完成

## 0. 一句话

把「婚姻形态 A–E」换成「有没有负面婚姻事件」的二值标签，冻结定义、样本量、阳性率与基线。**这是 T-154/T-155 的结果变量**；没有它，任何婚姻断语都只能继续测「形态」，等于重复 T-151 的错。

## 1. 数据源与现状

- `META/timing-eval-set-v1.json`：411 例候选，**382 例** `usable_for_timing=true`。
- 每例字段：`case_id`、`gender`、`birth_dt`、`usable_for_timing`、`marriage_events`（含 `year / age / age_plausible / polarity / text`）。
- 事件 polarity 实测（事件数，不是例数）：`unknown=106 / positive=239 / negative=233`。
- **坑**：部分 `text` 是命主提问（例如「……以后婚姻怎么样？」），提问里的「结婚/离婚」**不是结果**，不能当证据。

## 2. 标签定义（预注册，不得中途改）

对每例，按顺序：

1. **negative**：任一婚姻事件 `polarity == "negative"`；或 polarity 为 `unknown` 且**非提问**文本命中负面关键词。
2. **positive**：无 negative，且任一事件 `polarity == "positive"`；或 polarity 为 `unknown` 且非提问文本命中正面关键词。
3. **unknown**：以上都不成立（全是提问 / 中性 / 无证据）→ **排除，不进分母**。
4. **冲突**：negative 优先于 positive。

关键词（必须原样写进产物）：

- 负面：`离婚`、`离异`、`丧偶`、`亡夫`、`亡妻`、`再婚`、`二婚`、`三婚`、`多婚`、`婚变`
- 正面：`结婚`、`成婚`、`登记结婚`、`婚礼`、`一婚`、`婚姻稳定`、`白头`

提问判定（只用于 `polarity == unknown` 的文本）：

- 含 `？` 或 `?`，或含「是否 / 能否 / 请问 / 怎么样 / 吗 / 么 / 呢」，或明显是问句 → **不做关键词证据**。
- 若 polarity 是 `unknown` 之外的值（例如新增取值），按 `unknown` 处理并在报告里列出计数。

## 3. 产物

- `tools/marriage_quality_labels.py`（幂等：`python -m tools.marriage_quality_labels`）
- `META/marriage-quality-labels-v1.json`：
  - `schema` / `definition` / `frozen_at` / `source`（含 T-148 产物路径与 sha256）
  - `counts`：411 全集、382 可评测、negative / positive / unknown / conflict 各多少
  - `baseline`：382 例上的多数类命中率
  - `cases`：`case_id`、`negative`（true/false）、`basis`（polarity / keyword / none）、`evidence_events`（year / age / polarity / text 摘要）
- `META/marriage-quality-labels-v1.md`：审计表（事件 polarity、关键词命中、提问排除、冲突、最终标签、基线）+ 20 例人工抽查
- 可新建 `tests/tools/test_marriage_quality_labels.py`（确定性 + 提问不误判）

**不改** T-148 的冻结基线；只新建与读取。

## 4. 基线

- 在 **382 例可评测集**上算多数类基线：`max(negative, positive) / (negative + positive)`，报百分比与样本量。
- 同时报 411 例全集的标签分布（仅参考）。
- 若 `unknown` 超过 20%，必须按原因分类（提问 / 中性 / 无证据）逐类报数。

## 5. File Scope

**允许新建**

- `tools/marriage_quality_labels.py`
- `META/marriage-quality-labels-v1.json`
- `META/marriage-quality-labels-v1.md`
- `tests/tools/test_marriage_quality_labels.py`（可选）

**只读**

- `META/timing-eval-set-v1.json`
- `cases/raw_feedback/parsed/real_cases_990.jsonl`（仅人工对照抽查）

**禁止**

- 用任何盘面特征打标（泄漏：标签只能来自事件，不能来自八字）
- 改 `META/timing-eval-set-v1.json`、`timing-baseline-v1.json`、JSONL
- `theory/_ir/`、`sources/`、`engine/`、`pyproject.toml`
- `git commit / push / checkout / stash / reset / clean`

## 6. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.marriage_quality_labels     # 退出码 0
.venv\Scripts\python.exe -m pytest -q                         # 0 failed，passed >= 1066
git status --porcelain cases/                                 # 必须为空
```

中枢额外检查：

- 两次运行 JSON 哈希一致；
- 抽 20 例：提问不得被当证据；negative 优先；unknown 不折叠；
- 我另抽 5 例回原始 JSONL 核对事件文本；
- 报告里的 `counts` 四桶相加等于 411 / 382。

## 7. 回报格式（`tasks/T-153/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（计数表 + 基线 + 审计表）
3. **未完成与风险**（unknown 比例、关键词误判、极性缺失）
4. **下游须知**（标签含义、case_id 规则、unknown 怎么处理）

## 8. 禁止

- 不许用盘面特征打标（这是泄漏，不是特征工程）。
- 不许为了「阳性率好看」调关键词。
- 不许把 `unknown` 当 positive 或 negative。

## 9. 中枢裁决（2026-10-28 22:44）

1. **v1 接受**：中枢按卡 §2 规则独立重写一遍，**411/411 逐例一致**；四桶 151/164/48/48（全集）、138/156/40/48（可评测）对上；基线 186/342 = **54.39%**。
2. **7 例可评测误判保留、不改冻结规则**：495/560（否定语境「未结婚」）、544/528/845（第三人称「父母离婚」）、947/355（繁体「離婚」）。
   理由：现场改判就是事后调标签；敏感性测算 53.82%–54.71%，尺子稳定。
3. **下游 T-154/T-155 必须做两套敏感性**：342 全样本 + 剔除已知误判。注意：这 7 例里 `RF-2026-000947` 是 `unknown`、不在 342 内，从 342 只能剔 6 例 → **336**（T-154 卡 §7.1 已更正）。两套结论若翻转，判「**标签不足以裁决**」，不许挑好看的那套。
4. **分母纪律**：标签分母是 **342**（negative+positive），不是 382；40 例 `unknown` 不得折入。382 是应期分母，不是标签分母。
5. **上游噪声已知**：`RF-2026-000066` 的 positive 是「找到对象」、`RF-2026-000704` 的 negative 是抑郁文本。模型误差不得全算给断语。
