# T-153 BRIEF · 婚姻质量标签 v1（负面婚姻事件）

- 任务卡：`tasks/T-153/PROMPT.md`
- 执行者：子代理 F（2026-10-28）
- 状态：**完成，待中枢验收**（本简报的「通过」不算数，以中枢现场跑出的退出码为准）

## 1. 改动文件

新建：

| 文件 | 说明 |
|---|---|
| `tools/marriage_quality_labels.py` | 打标工具（幂等，`python -m tools.marriage_quality_labels`） |
| `META/marriage-quality-labels-v1.json` | 411 例逐例标签 + 计数 + 基线（425,446 B） |
| `META/marriage-quality-labels-v1.md` | 审计报告（计数 / 关键词 / 提问 / 冲突 / 8 例已知误判 / 20 例抽查） |
| `tests/tools/test_marriage_quality_labels.py` | 23 项测试（提问不误判、negative 优先、unknown 不折叠、无泄漏、冻结数字、确定性） |

修改：

| 文件 | 改动 |
|---|---|
| `tasks/T-153/STATUS.md` | Execution Log 追加一行 |

**未改动**（逐项确认）：`META/timing-eval-set-v1.json`、`META/timing-baseline-v1.json`、`cases/raw_feedback/parsed/real_cases_990.jsonl`、`engine/**`、`theory/**`、`sources/**`、既有测试、`pyproject.toml`、`tasks/T-153/PROMPT.md`。未执行任何 `git commit/push/checkout/stash/reset/clean`。

> `git status` 里另有 `docs/dispatch/README.md`、`engine/claims/rule_loader.py`、`META/rule-contract-dryrun-v1.*`、`tests/claims/test_rule_contract.py`、`tools/rule_contract_report.py` —— 是 T-152 并行 Worker 的改动，与本任务无关，我未触碰。

## 2. 原始输出

### 2.1 工具运行（退出码 0）

```text
T-153 marriage-quality-labels v1
  eval_set : META/timing-eval-set-v1.json sha256=e7b7f770b521… cases=411 usable=382
  all      : negative=151 positive=164 unknown=48 conflict=48 sum=411 | final negative=199
  usable   : negative=138 positive=156 unknown=40 conflict=48 sum=382 | final negative=186 positive=156 unknown=40 (10.47%)
  baseline : n=342 majority=negative hits=186 rate=54.39%
  wrote    : META/marriage-quality-labels-v1.json sha256=59d3764b7d57…
           : META/marriage-quality-labels-v1.md
EXIT=0
```

两次运行哈希（文件级）：

```text
json_sha256=59d3764b7d574e543242575fe3f26e131083249ed36946640ea1c498099118d8
md_sha256  =e839a6a06dc081b8231529028012827a21d6d3f280146ba08d1c97bcd55a78d6
payload_sha256 (JSON 内字段) = 9874960c9b502f7bfb501dd3d17515bb8804ecb269e3f98a23b647d6eb2aaf82
第 1 次 vs 第 2 次：json equal=True，md equal=True（逐字节）
```

### 2.2 pytest

```text
tests/tools/test_marriage_quality_labels.py ........ 23 passed in 0.60s
python -m pytest -q ................................ 1099 passed, 1 skipped, 1 warning in 97.95s
```

`1 skipped` 是 `tests/tools/test_bundle_pii.py` 的既有 T-114 跳（`.workbuddy-ai/make_bundle_v2.py` 缺失），非本任务引入。0 failed，passed 1099 >= 1066。

### 2.3 `git status --porcelain cases/`

```text
（空输出，退出码 0）
```

### 2.4 计数（互斥四桶，相加 = 411 / 382）

| 桶 | 411 全集 | 382 可评测 |
|---|---:|---:|
| negative（纯负证据） | 151 | 138 |
| positive | 164 | 156 |
| unknown（排除，不进分母） | 48 | 40 |
| conflict（负正并存，negative 优先） | 48 | 48 |
| **合计** | **411** | **382** |

最终标签（conflict 计入 negative）：**411** negative `199` / positive `164` / unknown `48`；**382** negative `186` / positive `156` / unknown `40`。

事件层：578 条婚姻事件 / 547 条属可评测例；polarity `negative=233`、`positive=239`、`unknown=106`（任务卡实测值一致），三值之外 `0`。可评测例内 `219 / 232 / 96`。

### 2.5 基线（382 例可评测集）

| 项 | 值 |
|---|---|
| 分母（negative + positive） | **342** |
| negative / positive | 186 / 156 |
| unknown（排除） | 40 |
| 多数类 | negative |
| 命中 | 186 |
| **多数类命中率** | **54.39%** |

411 全集参考分布（仅参考）：分母 363，negative 199，positive 164，unknown 48，命中率 **54.82%**。

### 2.6 unknown 主因分类（案例级）

| 原因 | 411 全集 | 382 可评测 | 定义 |
|---|---:|---:|---|
| question | 22 | **16** | 全部有文本事件均为提问 |
| neutral | 26 | **24** | 存在非提问、无关键词命中的文本 |
| no_evidence | 0 | 0 | 无婚姻事件或事件文本为空 |

unknown 占比：全集 **11.68%**，可评测 **10.47%**（< 20%，分类仍按要求给出）。

### 2.7 关键词 / 提问审计

非提问 unknown 文本的关键词命中（事件数，全集）：负面 17 条 = `离婚` 11 + `离异` 3 + `二婚` 2 + `再婚` 1；正面 30 条 = `结婚` 29 + `婚礼` 1。其余 9 个负面词、5 个正面词命中 0。

提问标记命中（unknown 事件，可多选）：`么` 21、`怎么样` 9、`？` 9、`能否` 5、`是否` 4、`吗` 3、`请问` 2、`?` 1、`呢` 1。

提问规则抑制了关键词证据：**14 例**（可评测 11 例）。其中 11 例因此落在 unknown（`010/038/050/207/259/346/347/653/902/009/545`），另 3 例（`342/375/684`）仍由其它事件定标。

判定依据分布（全集）：negative polarity 191 + keyword 8；positive polarity 148 + keyword 16。（可评测：178+8 / 141+15。）

### 2.8 20 例人工抽查（逐例回 JSONL 核对）

抽查方式：按 `raw_id` 回 `cases/raw_feedback/parsed/real_cases_990.jsonl`，比对 `marriage_events` 的 `year / polarity / text`。

```text
RF-2026-000010 events=1 match=True      RF-2026-000259 events=1 match=True
RF-2026-000038 events=1 match=True      RF-2026-000207 events=1 match=True
RF-2026-000050 events=1 match=True      RF-2026-000495 events=1 match=True
RF-2026-000902 events=1 match=True      RF-2026-000560 events=1 match=True
RF-2026-000509 events=1 match=True      RF-2026-000354 events=4 match=True
RF-2026-000372 events=2 match=True      RF-2026-000063 events=1 match=True
RF-2026-000845 events=1 match=True      RF-2026-000528 events=2 match=True
RF-2026-000544 events=1 match=True      RF-2026-000728 events=1 match=True
RF-2026-000947 events=1 match=True      RF-2026-000355 events=2 match=True
RF-2026-000081 events=1 match=True      RF-2026-000066 events=1 match=True
MISMATCH=0
```

结论（详见 `META/marriage-quality-labels-v1.md` §8）：

| 类别 | 案例 | 标签 | 结论 |
|---|---|---|---|
| 提问 | 010 / 038 / 050 / 902 | unknown | 合理（提问不采证） |
| 提问抑制陈述 | 259（「老公起诉离婚」）/ 207（「结婚…婚后一子」） | unknown | **存疑**：偏保守 |
| 否定语境 | 495（「一直没结婚…婚礼不顺」）/ 560（「且未结婚」）/ 509（「未结婚」，不可评测） | positive | **存疑**：误判 |
| 冲突 | 354 / 372 / 063 / 845 / 528 | negative | 前 3 例合理；845/528 **存疑**（第三人称） |
| 第三人称 | 544（「父母离婚」） | negative | **存疑** |
| 纯关键词 | 728（「2004 离婚…2006 二婚…2020 二离」） | negative | 合理 |
| 繁体漏判 | 947（「2020 離婚」）/ 355（「離過婚(2021)」） | unknown / positive | **存疑** |
| 纯极性 | 081（negative「婚姻很累」）/ 066（positive「找到对象」） | negative / positive | 合理（066 的上游事件实为恋爱，域偏宽） |

### 2.9 敏感性估算（**非**产物口径，仅供中枢裁决）

只把 §2.8 的存疑例按语义改判、重算 382 分母：

| 情景 | negative | positive | unknown | 分母 | 基线 |
|---|---:|---:|---:|---:|---:|
| 冻结口径 | 186 | 156 | 40 | 342 | 54.39% |
| A 否定语境（495/560 → unknown） | 186 | 154 | 42 | 340 | 54.71% |
| B 第三人称（544/528→unknown，845→positive） | 183 | 157 | 42 | 340 | 53.82% |
| C 繁体补词（947→negative，355→negative） | 188 | 155 | 39 | 343 | 54.81% |
| A+B+C | 185 | 154 | 43 | 339 | 54.57% |

**基线在所有情景下都在 53.8%–54.8%**：多数类基线对这批关键词误判不敏感，可以放心用作 T-154/T-155 的比较尺子。

## 3. 未完成与风险

1. **unknown 比例**：可评测 10.47%（40/382），低于任务卡 20% 的关注线；主因是 neutral 24 + question 16。没有折叠成 positive/negative。
2. **关键词误判（8 例已知，规则本身边界，非实现 bug）**：
   - 否定语境：「未结婚/没结婚」含「结婚」→ `495/560` 判 positive（`509` 不可评测）。这是「关键词子串」与「否定语义」的冲突。
   - 第三人称：「父母离婚/父母离异/再婚对象」→ `544/845/528` 判 negative；`845` 按语义应为 positive。
   - 繁体漏判：`離婚/離過婚` 未命中简体词 → `947` unknown、`355` positive（按语义都应为 negative）。
   - 按任务卡 §2 预注册规则**未就地修正**，全部在 MD §7 列明，敏感性见 §2.9。
3. **「么」字面规则**：21 条 unknown 事件因「什么/怎么」被判提问，其中 `375/684` 的陈述式「结婚」被抑制（另有事件定标，不影响最终标签）。这个方向的误差只让 unknown 变多，不会把提问当证据；未放宽。
4. **极性缺失 / 上游噪声**：106 条 unknown polarity 事件已逐条判定；三值之外取值 0 条。另有上游问题（非本任务可改）：`704` 的 2020 negative 事件文本是「复读/抑郁」，`066` 的 positive 事件是「找到对象」（恋爱），说明 T-148 的婚姻域事件极性来自事件整段而非婚姻本身，会给 negative/positive 带噪。
5. **`frozen_at` 是定义冻结日（2026-10-28），不是运行时间戳**。任务卡要求「两次运行逐字节一致」，故刻意不写运行时间；JSON 内 `frozen_at_note` 已注明。若中枢要真实生成时间，需要放宽确定性要求并另建 v2。
6. **未验证**：本任务没有模型/预测，只有标签；`payload_sha256` 只覆盖本 JSON 自身，不覆盖 MD。

## 4. 下游须知（T-154/T-155 用）

- **标签含义**：`label == "negative"` = 该例存在负面婚姻事件（极性 negative，或非提问文本命中负面关键词）。它**不是**「已离婚」的同义词，也不等于婚姻质量评分；`positive` 只表示存在婚姻成立/稳定的正面证据。
- **字段**：`cases[]` = `case_id / usable_for_timing / label / negative(bool) / basis(polarity|keyword|none) / conflict / unknown_reason / events_total / events_question / events_empty_text / negative_evidence / positive_evidence / evidence_events`。`evidence_events` 带 `year/age/polarity/text(80 字摘要)/source/matched`，可直接回溯。
- **case_id**：就是 JSONL 的 `raw_id`（`RF-2026-XXXXXX`），可直接 join 原语料；`cases` 按 `case_id` 升序。
- **怎么取分母**：先 `usable_for_timing == true`（382），再丢掉 `label == "unknown"`（40）→ 342。**未知不许折叠**；`unknown` 若要单列，按 `unknown_reason` 分 question/neutral/no_evidence。
- **计数口径坑**：`counts.usable.negative = 138` 是「纯负证据」桶，不含 conflict；`counts.final.usable.negative = 186` 才是最终标签（=138+48）。基线 186/342 用的是后者。四桶相加校验只对 `counts.all/usable` 成立。
- **冲突**：48 例（可评测同样是 48）按 negative 优先。若要「干净标签」，过滤 `conflict == false` 后剩 138 negative / 156 positive（可评测 294 例）。
- **基线**：多数类 negative，**54.39%（186/342）**。T-154/T-155 的任何模型必须在这 342 例上打赢这个数才算有信息。
- **复现**：`python -m tools.marriage_quality_labels`；不要手改 JSON/MD。数据或规则变更须另建 v2 并写清规则差异（本版 `status=frozen`、`immutable=true`）。
- **泄漏红线**：标签只来自 `marriage_events`，不含任何盘面/八字字段；特征侧不得反向使用本文件里的任何关键词命中细节来构造标签。
