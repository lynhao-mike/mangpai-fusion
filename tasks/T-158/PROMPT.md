# T-158 · 财富 / 健康结局标签 v1（来自 real_cases_990）

- 状态：🔵 Ready for Execution
- 优先级：**P1（补其他域结局标签的第一批）**
- 创建：2026-10-29（中枢）
- 依据：T-154 只测了 2/10 条规则；其余 8 条缺结局标签
- 前置：无

## 0. 一句话

从 `real_cases_990.jsonl` 的 `income` / `health` 事件，造两个二值标签：
**是否有债务事件**、**是否有严重健康事件**。冻结定义、样本量、阳性率、基线；**不打标任何盘面特征**。

## 1. 已核实的数据现状（中枢探针，直接使用）

- 原始 992 条 → 按 `duplicate_key` 去重 **959**；有性别 950；出生日期可解析 952；**出生时刻 947**。
- 事件域（去重后，事件数 / 案例数）：
  - `income` **606 / 377**（没有 `wealth` 域）；polarity：neg 261 / pos 261 / unknown 84。
  - `health` **659 / 453**；polarity：neg 462 / pos 100 / unknown 97。
- 事件 `text` 是长段落，常混多个域、常夹提问；**提问里的关键词不算证据**。
- 产品规则映射：财富规则 → `income`；健康规则 → `health`。

## 2. 标签定义（预注册，不得中途改）

### 2.1 基础集

- 按 `duplicate_key` 去重；`gender ∈ {男, 女}`；`birth_datetime_raw` 可解析出日期。
- `chart_ready = 出生时刻可解析`（用于后续建盘；本卡只标记，不建盘）。
- **标签只来自事件文本与 polarity，不使用任何八字/盘面字段。**

### 2.2 债务标签（`debt`）

- `1`：任一 `income` 事件（非提问）命中债务关键词：
  `负债`、`欠债`、`债务`、`欠款`、`借款`、`贷款`、`信贷`、`破产`、`被骗`、`还债`、`负债累累`、
  `亏损`、`资金链`、`被执行人`。
- `0`：案例有 `income` 事件，但没有任何一条命中上述关键词。
- `null`：案例没有任何 `income` 事件 → 该域排除，**不折入 0**。
- 提问判定：文本含 `？` / `?` / `是否` / `能否` / `请问` / `怎么样` / `吗` / `么` / `呢` 任一 → 整段不作证据。

### 2.3 严重健康标签（`serious_health`）

- `1`：任一 `health` 事件（非提问）命中严重关键词：
  `手术`、`住院`、`ICU`、`抢救`、`病危`、`癌`、`肿瘤`、`重病`、`大病`、`慢性病`、`中风`、
  `心脏病`、`糖尿病`、`肾衰竭`、`化疗`、`放疗`、`瘫痪`、`失明`、`精神病`。
- `0`：案例有 `health` 事件，但没有任何一条命中上述关键词。
- `null`：案例没有任何 `health` 事件 → 该域排除。
- 提问判定同上。

### 2.4 歧义处理

- 同一案例同时有 `1` 和 `0` 证据 → `1` 优先（存在性标签）。
- 关键词误判（如「贷款买房」算不算债务）不现场改定义；在报告 §4 列为已知误差并给出条数，由中枢决定是否出 v2。
- 若 `null` 超过 30%，必须按原因分类（无该域事件 / 全是提问 / 无文本）报数。

## 3. 产物

- `tools/domain_labels_wealth_health.py`（幂等：`python -m tools.domain_labels_wealth_health`）
- `META/domain-labels-wealth-health-v1.json`：
  - `schema`、`definition`、`frozen_at`、`source`（JSONL path + sha256）
  - `counts`：992 / 959 / 950 / 952 / 947；各标签的 `1 / 0 / null`、chart_ready 内的 `1 / 0 / null`
  - `baseline`：各标签在 chart_ready 可用集上的阳性率
  - `cases`：`case_id`（raw_id）、`gender`、`birth_datetime_raw`、`birth_dt`、`time_basis`、
    `chart_ready`、`labels: {debt: 0/1/null, serious_health: 0/1/null}`、`evidence_events`
- `META/domain-labels-wealth-health-v1.md`：漏斗、计数、阳性率、基线、关键词命中、提问排除、**20 例人工抽查**、已知误差
- `tests/tools/test_domain_labels_wealth_health.py`：确定性、提问不误判、`null` 不折叠、**无盘面字段**

复用：`tools/timing_eval_set.py` 的 `parse_clock_datetime`（只读 import），**不许改该文件**。

## 4. 基线

- 在 `chart_ready=true` 且该域标签非 `null` 的案例上，算阳性率与样本量。
- 同时报全基础集（不要求时刻）的阳性率，仅参考。
- 后续 T-160 评分必须用同口径基线。

## 5. File Scope

**允许新建**

- `tools/domain_labels_wealth_health.py`
- `META/domain-labels-wealth-health-v1.json`
- `META/domain-labels-wealth-health-v1.md`
- `tests/tools/test_domain_labels_wealth_health.py`

**只读**

- `cases/raw_feedback/parsed/real_cases_990.jsonl`
- `tools/timing_eval_set.py`、`META/timing-eval-set-v1.json`
- `engine/**`（不建盘）

**禁止**

- 用任何八字/盘面字段打标（泄漏）
- 改 JSONL、T-148/T-153 产物、engine/**、theory/**、sources/**、既有测试
- `git commit / push / checkout / stash / reset / clean`

## 6. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.domain_labels_wealth_health   # 退出码 0
.venv\Scripts\python.exe -m pytest tests/tools/test_domain_labels_wealth_health.py -q -o addopts="-ra --tb=short"
.venv\Scripts\python.exe -m pytest -q                            # 0 failed，passed >= 1142
git status --porcelain cases/                                    # 必须为空
```

中枢额外检查：

- 两次运行 JSON 哈希一致；
- 抽 20 例：提问不被当证据；`null` 不折叠；债务/严重健康的关键词命中可回原文；
- 计数四桶可加（`1+0+null` = 该域案例数）；
- 工具里没有 `engine`/`chart`/`bazi` 等盘面字段（grep）。

## 7. 回报格式（`tasks/T-158/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（漏斗 + 两标签阳性率 + 基线 + 20 例审计）
3. **未完成与风险**（关键词误判、`null` 比例、chart_ready 损失）
4. **下游须知**（标签语义、case_id、哪些案例可建盘）

## 8. 禁止

- 不许用盘面特征打标。
- 不许为了阳性率调关键词；误判列出来，别偷偷修。
- 不许把 `null` 折成 0 或 1。

## 9. Amendments（中枢裁决，2026-10-29 00:40）

### 9.1 `null` 口径

`null` = **无可用证据**（无该域事件 / 全是提问 / 空文本），不折 0、不折 1。卡 §2.2/§2.3 的「无该域事件」是狭义写法，以本节为准；v1 数字保留。

### 9.2 v1 只作审计留档，T-160 不得用 v1 评分

v1 已知误判：health **71/131（54%）**（第三人称 50、非危重手术 19、否定 2）；debt **16/49（33%）**
（第三人称 3、房贷 6、投资亏损 3、应收款 1、公司破产 1、被骗 2、否定 1）。做 v2：

1. **主体过滤**：关键词句含 父母/父亲/母亲/爸/妈/老公/老婆/妻子/丈夫/儿子/女儿/孩子/家人/家属/
   兄弟/姐妹/亲戚/朋友，且无 我/本人/自己 → 排除；主体不明 → `null`，不许猜。
2. **否定过滤**：关键词前 6 字内出现 无/没/没有/未/差点/并非 → 排除。
3. **health 严重度**：删 `手术`、`住院`；保留 抢救/ICU/病危/癌/肿瘤/重病/大病/化疗/放疗/中风/
   心脏病/糖尿病/肾衰竭/瘫痪/失明/精神病；`慢性病` 保留但单列报数。
4. **debt 词表**：删 `亏损`、`被骗`（是损失不是债务）；房贷/购房贷款/按揭 **默认排除**并单列；
   保留 负债/欠债/债务/欠款/借款/还债/资金链/被执行人/破产。
5. v2 写新文件 `META/domain-labels-wealth-health-v2.{json,md}`；v1 不动；重跑 20 例审计 +
   v1/v2 差异表（每条过滤删了多少阳性）。
6. **门槛**：v2 已知误判率仍 >20% → 停，写「标签不适合作裁决」，不再调词，T-160 不启动。
7. 只改标签工具/新文件；不评分、不建盘、不改 v1/JSONL/engine/既有测试。
