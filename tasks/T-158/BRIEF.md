# T-158 BRIEF · 财富 / 健康结局标签 v1（`debt` / `serious_health`）

- 任务卡：`tasks/T-158/PROMPT.md`
- 执行者：子代理 K（Worker）
- 状态：实现完成，自测通过（**验收以中枢现场重跑为准**）
- 定义冻结日：`2026-10-29`（写进产物，不是运行时间戳；两次运行逐字节一致）

## 1. 改动文件

新建（仅 4 个，全部在任务卡 File Scope 内）：

| 文件 | 说明 |
|---|---|
| `tools/domain_labels_wealth_health.py` | 打标器；`python -m tools.domain_labels_wealth_health` 幂等，退出码 0/2/3/4 |
| `META/domain-labels-wealth-health-v1.json` | 944 例逐例标签 + 漏斗计数 + 基线 + 审计（841,659 字节，`payload_sha256` 见产物） |
| `META/domain-labels-wealth-health-v1.md` | 人读报告（漏斗 / 计数 / 阳性率 / 关键词 / 提问排除 / 20 例抽查 / 已知误判） |
| `tests/tools/test_domain_labels_wealth_health.py` | 38 个测试：冻结词表、提问不采证、null 不折叠、1 优先、无盘面字段、确定性、产物与实现一致 |

只读复用：`tools.timing_eval_set.resolve_birth`（内部调用 `parse_clock_datetime`；未改该文件）。
未改：JSONL、T-148/T-153 产物、`engine/**`、`theory/**`、`sources/**`、既有测试、`pyproject.toml`。
未做任何 git 写操作（commit / push / checkout / stash / reset / clean 均未执行）。

## 2. 原始输出

### 2.1 打标器（`.venv\Scripts\python.exe -m tools.domain_labels_wealth_health`，退出码 0）

```text
T-158 domain-labels-wealth-health v1
  source   : cases/raw_feedback/parsed/real_cases_990.jsonl sha256=0c82a0e73cf3… records=992
  funnel   : 992 → 959 → gender=950 date=952 time=947 | base=944 chart_ready=940
  debt           : 1=49 0=287 null=608 (sum=944) | chart_ready 1=49 0=286 null=605 | rate=14.63% n=335
  serious_health : 1=131 0=287 null=526 (sum=944) | chart_ready 1=131 0=286 null=523 | rate=31.41% n=417
  wrote    : META/domain-labels-wealth-health-v1.json sha256=e9da1df473e2…
           : META/domain-labels-wealth-health-v1.md
```

两次运行 `META/domain-labels-wealth-health-v1.json` 的 SHA256 均为
`E9DA1DF473E24866E02C663FB5DBFE3D5CAF251717F42582D4644F1E47985B88`（逐字节一致，MD 同样一致）。

### 2.2 漏斗（与任务卡 §1 完全复现）

| 阶段 | 条数 | 口径 |
|---|---|---|
| 原始记录 | **992** | JSONL 行数 |
| `duplicate_key` 去重 | **959** | 保留首次出现；27 个重复组、移除 33 条 |
| 有性别 | **950** | 在 959 上独立过滤 |
| 出生日期可解析 | **952** | 在 959 上独立过滤 |
| 出生时刻可解析 | **947** | 日期可解析且有时刻 |
| **基础集**（去重 + 性别 + 日期） | **944** | 可打标样本 |
| **chart_ready**（基础集内有时刻） | **940** | 可建盘样本 |

**口径提醒**：950 / 952 / 947 是**三个独立过滤**，不是嵌套漏斗（947 > 944）；三条件交集才是 944。
基础集外 15 例：`missing_gender` 8、`birth_empty` 5、`birth_bad_time` 1、`missing_gender+birth_empty` 1。

### 2.3 标签计数（1 / 0 / null，四桶可加）

| 标签 | 1 | 0 | null | 合计 | chart_ready 1/0/null | 合计 |
|---|---|---|---|---|---|---|
| `debt` | **49** | **287** | **608** | 944 | **49 / 286 / 605** | 940 |
| `serious_health` | **131** | **287** | **526** | 944 | **131 / 286 / 523** | 940 |

可加校验：`debt` 944 = 49+287+608；`serious_health` 944 = 131+287+526（chart_ready 同理）。
`null` 原因：`debt` = 无该域事件 572 + 全是提问 36 + 无文本 0；`serious_health` = 496 + 30 + 0。
事件口径：`income` **606** 事件 / **377** 案例（提问事件 54）；`health` **659** / **453**（提问 45）。
混合证据（1 优先）：`debt` 27 例、`serious_health` 48 例。

### 2.4 阳性率与基线（任务卡 §4）

| 标签 | chart_ready 主口径 n | 1 | 0 | 阳性率 | 全集 n（仅参考） | 阳性率 |
|---|---|---|---|---|---|---|
| `debt` | **335** | 49 | 286 | **14.63%** | 336 | 14.58% |
| `serious_health` | **417** | 131 | 286 | **31.41%** | 418 | 31.34% |

口径：分母 = 该标签非 `null` 的案例，`null` 不进分母。T-160 评分必须用同一口径。

### 2.5 20 例人工抽查（均回 JSONL 核对原文，20/20 与冻结结论一致）

| # | case_id | chart_ready | debt | serious_health | 结论 |
|---|---|---|---|---|---|
| 1 | RF-2026-000001 | 是 | 0 | 1 | 合理：同一事件跨 income/health 域；ICU/抢救/病危为本人事实 |
| 2 | RF-2026-000002 | 是 | null | null | 提问排除：income 整段是提问（「什么时候能发财？」）；health 无事件 |
| 3 | RF-2026-000003 | 否 | null | null | 合理：两域都无事件 → 双 null，未折 0 |
| 4 | RF-2026-000013 | 是 | null | null | 提问排除：health 文本含「肿瘤」但整段提问 → null |
| 5 | RF-2026-000016 | 是 | null | 0 | 合理：health 有证据事件零命中 → 0；debt 无事件 → null |
| 6 | RF-2026-000017 | 否 | 0 | 0 | 合理：只有出生日期（农历换算后），标签照算 |
| 7 | RF-2026-000034 | 是 | 1 | 0 | 合理：贷款过多 + 信用卡还款为本人债务 |
| 8 | RF-2026-000048 | 是 | 1 | null | 存疑：家庭购房贷款被记为债务（§7） |
| 9 | RF-2026-000067 | 是 | null | 1 | 存疑：父亲癌症（且误诊），非本人（§7） |
| 10 | RF-2026-000079 | 是 | null | null | 提问排除：income 含「负债」但带问号 → null |
| 11 | RF-2026-000118 | 是 | 0 | 1 | 合理（偏宽）：骨折内固定手术，严重性可议（§7） |
| 12 | RF-2026-000137 | 是 | 0 | 1 | 存疑：姥姥癌症 / 姥爷脑梗，非本人（§7） |
| 13 | RF-2026-000235 | 是 | null | 1 | 存疑：「健康良好无大病」否定句（§7） |
| 14 | RF-2026-000243 | 是 | 1 | 0 | 存疑：家里贷款买房 + 父亲百万贷款（§7） |
| 15 | RF-2026-000308 | 是 | 0 | 1 | 存疑：「差点住院」未实际发生（§7） |
| 16 | RF-2026-000531 | 是 | 1 | null | 存疑：妈妈被骗，非本人负债（§7） |
| 17 | RF-2026-000572 | 是 | 0 | 1 | 合理：重度抑郁精神科住院为本人事实 |
| 18 | RF-2026-000633 | 是 | 0 | 1 | 存疑：父亲晕倒后开刀手术，非本人（§7） |
| 19 | RF-2026-000681 | 是 | 1 | 1 | 混合：health 本人摔伤抢救；debt 为儿子欠债（§7） |
| 20 | RF-2026-000918 | 是 | 1 | 0 | 存疑：「欠款要不上来」是应收款（§7） |

### 2.6 已知误判条数（人工逐条回原文核查，按卡片保留原判，未改词）

| 标签 | 类型 | 案例数 | 标签影响 |
|---|---|---|---|
| `debt` | 第三人称（家属债务） | 3 | 1 → 0 |
| `debt` | 房贷 / 购房贷款 | 6 | 1 → 0 |
| `debt` | 投资 / 经营亏损 | 3 | 1 → 0 |
| `debt` | 应收款误判（欠款） | 1 | 1 → 0 |
| `debt` | 公司破产（非个人） | 1 | 1 → 0 |
| `debt` | 被骗（损失非负债） | 2 | 1 → 0 |
| `debt` | 否定语境 | 1 | 事件级，不改标签 |
| `serious_health` | 第三人称（家属疾病） | **50** | 1 → 0 |
| `serious_health` | 非危重手术（小手术/微创/骨折/良性结节等） | **19** | 1 → 0 |
| `serious_health` | 否定 / 未发生（「无大病」「差点住院」） | 2 | 1 → 0 |

合计可翻转型误判：`debt` **16/49**、`serious_health` **71/131**。逐例 case_id 与原文摘要见 MD §7。
若仅作参考地剔除上表：`debt` 33/335 = **9.85%**、`serious_health` 60/417 = **14.39%**（**不是**本版标签，仅供中枢决定 v2）。

### 2.7 测试

```text
.venv\Scripts\python.exe -m pytest tests/tools/test_domain_labels_wealth_health.py -q -o addopts="-ra --tb=short"
38 passed in 1.11s

.venv\Scripts\python.exe -m pytest -q
1216 passed, 1 skipped, 1 warning in 103.74s   (exit 0；skip = tests/tools/test_bundle_pii.py 既有 T-114 过渡 skip)
```

说明：首轮全量跑（T-159 的测试文件尚未落盘时）是 `1180 passed, 1 skipped`；现为 `1216 passed`，
差值来自并行任务 T-159 新增的测试，不是本卡改动。本卡自带 38 个测试；扣除后全量仍 ≥ 卡片要求的 1142。

`git status --porcelain cases/` 为空（未动 JSONL）。工具源码 grep `bazi|ganzhi|shishen|dayun|liunian|nayin|shensha|engine|chart`
只命中卡片要求的 `chart_ready` 字段名；JSON 键无任何盘面字段（测试 `test_payload_has_no_chart_fields` 双向守住）。

## 3. 未完成与风险

1. **卡片口径歧义（需中枢确认，本版已按保守口径实现）**：§2.2 / §2.3 字面写 `null` = 「没有任何该域事件」，
   但 §2.4 的 null 原因分类明确列了「全是提问 / 无文本」，且硬约束要求「提问不算证据」「null 不许折成 0」。
   本版把「有该域事件但**没有任何证据事件**（全是提问 / 空文本）」也记 `null`，并单列原因。
   若中枢坚持字面口径（全提问 → 0），替代数字为：
   `debt` 1/0/null = **49/323/572**（chart_ready 49/320/571）；
   `serious_health` = **131/317/496**（chart_ready 131/316/493）。两种口径的 1 完全相同，只影响 0 与 null 的分配。
2. **`null` 占比高但属结构性**：`debt` null 64.41%、`serious_health` 55.72%（>30%，已按卡片要求分原因报数）。
   主因是上游事件域覆盖：944 例里只有 377 例有 `income` 事件、453 例有 `health` 事件（与任务卡 §1 一致），
   不是打标失败。下游若做财富评分，实际可用分母只有 335（chart_ready 且非 null）。
3. **关键词可翻转型误判比例很高**：`serious_health` 71/131 阳性来自已知边界（第三人称 50、非危重手术 19、否定 2）；
   `debt` 16/49（房贷 6、家属 3、亏损 3、被骗 2、应收款 1、公司破产 1）。**未就地改词、未加否定/主体识别**，
   逐例清单在 MD §7，是否出 v2 由中枢决定。
4. **提问规则偏保守**：整段含 `？? 是否 能否 请问 怎么样 吗 么 呢` 任一即不采证（`么` 命中最多，因「什么/怎么/这么」），
   共抑制 8 条 `debt`、10 条 `serious_health` 含关键词的提问事件（MD §5.3 逐条列出）。
   其中如「2011 年结节做手术」这类陈述句被同段提问带掉，相关案例落到 null/0。
5. **chart_ready 损失 4 例**（944 → 940：RF-2026-000003 / 000008 / 000009 / 000017），均只有出生日期；
   这 4 例仍保留标签（3 例两域均 `null`、1 例两域均 `0`，没有一个阳性），只是不能建盘。
6. **`polarity` 不参与判定**：卡片 §2.2 / §2.3 是纯关键词规则，本版只把 polarity 记进证据事件与审计。
   如需「negative 才算债务/重病」的语义，属于规则变更，须另建 v2。
7. **同义重复案例**：如 RF-2026-000286/000287、000461/000462、000667/000668、000989/000990 文本近重复，
   `duplicate_key` 未合并（不同 key），对阳性率有轻微放大；未改去重规则。

## 4. 下游须知

1. **标签语义**：`debt` = 「`income` 域事件文本里出现过债务关键词」；`serious_health` = 「`health` 域事件文本里出现过严重健康关键词」。
   是**结果变量/存在性标签**，不是预测，也不是「命主本人确诊」——第三人称与否定句未过滤（见 §3.3）。
2. **索引**：`case_id` 就是 JSONL 的 `raw_id`（`RF-2026-000XXX`）；`cases[]` 按 `case_id` 升序，944 例。
3. **可用集合**：
   - 打标全集：`counts.base_sample` = **944**；
   - 可建盘：`chart_ready = true` → **940**（另 15 例在 `excluded_records`，含原因）；
   - 评分分母：按标签取 `labels[<key>] != null`，`debt` **335**（chart_ready）/ 336（全集），
     `serious_health` **417** / 418。**必须与 `baseline.<key>.chart_ready` 同口径**。
4. **读取方式**：`cases[].evidence_events` 是逐条域事件审计（`verdict` = `evidence` / `question` / `empty`，
   `matched` 只对 `evidence` 给出），`text` 为压缩空白后 160 字摘要（原文按 `case_id` + `year` 回 JSONL）。
5. **基线（T-160 必须沿用）**：`debt` 14.63%（n=335）、`serious_health` 31.41%（n=417）；
   产物里 `baseline.<key>.chart_ready` 与 `base_reference` 都已冻结。
6. **复现**：`python -m tools.domain_labels_wealth_health`（退出码 0；2 数据源、3 不变量、4 人工核查不符时拒绝落盘）。
   产物无运行时间戳，两次运行 JSON/MD 逐字节一致；`payload_sha256` 在 JSON 末尾。
