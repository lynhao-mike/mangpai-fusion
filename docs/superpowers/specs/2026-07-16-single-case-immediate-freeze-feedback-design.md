# 单案当天冻结与即时回顾反馈设计规格

> 状态：已批准方向的设计规格；正式定义两层新门禁，仅定义目标契约，不实施代码或数据流程。
> 日期：2026-07-16
> 适用范围：HOLD 后 prospective Task 3 / Task 4 单案采集链，以及由该链派生的“预测能力候选 GO”与“未来实证 GO”判定。
> 当前门禁：首案即时回顾尚未完成；“预测能力候选 GO”与“未来实证 GO”当前均为 HOLD。本文不授权切换生产入口、修改规则、修改评分公式或创建真实数据制品。

## 1. 背景与决策

当前流程按 10 案成批正式 intake 和冻结，导致首案必须等待其余 9 案，既延长反馈等待，也把单案失败扩大成批级阻塞。目标流程改为：

```text
每案当天正式 intake
→ 每案独立盲包
→ 每案六来源输出冻结
→ 独立 witness 签署并验证
→ 验证通过后，当天释放并收集既往经历与当前现状
→ 高风险事实双审
→ 每累计 10 案只做父制品引用式汇总评分与迭代判断
```

核心决策是采用“单案不可变证据链 + 十案派生汇总 + 两层新门禁”模型：每案独立完成 prediction-first 冻结；10 案边界不再控制 intake、bundle、freeze 或反馈释放，只控制周期性汇总评分、校准诊断和迭代提案。门禁判定按实际累计的唯一合格命主和任务标签计算，不以 cohort 数或“满 10 案”代替阈值。

本文替代现行“批次满 10 案后才正式 intake / freeze / witness”的执行节奏，并正式加入用户批准的“预测能力候选 GO”与“未来实证 GO”。本文不降低现有安全门槛，也不把当天已存在事实重新定义为未来 outcome。现行协议见 [`META/prospective-intake-protocol-v1.md`](../../../META/prospective-intake-protocol-v1.md:1)，现行 Task 3 / Task 4 计划见 [`plans/upgrade-guides/post-gate-action-plan-2026-07-15.md`](../../../plans/upgrade-guides/post-gate-action-plan-2026-07-15.md:314)，2026-07-15 平台 HOLD 与原 30 案门禁事实源见 [`META/six-month-platform-gate-2026-07-15.md`](../../../META/six-month-platform-gate-2026-07-15.md:1) 和 [`META/six-month-platform-gate-2026-07-15.json`](../../../META/six-month-platform-gate-2026-07-15.json:1)。这两个既有门禁制品保持字节与语义不变，不被本文覆盖。

## 2. 目标、非目标与安全不变量

### 2.1 目标

1. 新案在到达当天独立完成正式 intake、盲包、六来源冻结、witness 签署与签名验证。
2. 只有签名验证成功后，才允许收集该案冻结时已经存在的既往经历与当前现状。
3. 对当天反馈建立诚实的证据分类，允许用于 prediction-first immediate retrospective 验证，但不得计入未来观察 outcome。
4. 每案冻结 1 个在 freeze 后三个月内可核验的短期未来问题，为独立的 future observation 账预注册任务、窗口与判定口径。
5. 每 10 个已完成单案仅创建新的汇总制品；汇总通过父制品路径与摘要引用单案制品，不复制后覆盖、不改写父制品。
6. 保持三项高风险任务的独立双审、冲突仲裁与 A 级门槛。
7. 以互不混用的计数器定义“预测能力候选 GO”“未来实证 GO”和 historical baseline。
8. 明确泄漏 STOP、失败恢复、首案迁移和可机械验证的验收标准。

### 2.2 非目标

- 不在本文中实现或修改 [`tools/school_capability_dataset.py`](../../../tools/school_capability_dataset.py:1)、[`tools/school_capability_prospective.py`](../../../tools/school_capability_prospective.py:1)、[`tools/school_capability_review.py`](../../../tools/school_capability_review.py:1) 或测试。
- 不生成真实 intake、盲包、冻结、witness、反馈、标签、评分或规则快照。
- 不设计密钥托管服务，不记录实际密钥、PII、经历正文或健康资料。
- 不把本文的 20 案即时回顾门禁或 10 案未来观察门禁改写为、替代或冲抵原 30 案 historical baseline；原 baseline 的目标 binary ≥20、正负皆有、校准误差严格小于 0.2、竞争样本 ≥5、selection change ≥1、高风险 A 级双审等条件继续按其原事实源解释。
- 不修改 [`run_pipeline()`](../../../engine/application/pipeline_runner.py:1)、[`DEFAULT_RUNNER_REGISTRY`](../../../engine/claims/runner_registry.py:1)、static 默认路由、生产权重或生产规则。

### 2.3 安全不变量

- 预测输入与反馈资料物理隔离；freeze 签名验证前，runner 边界不得接触既往经历、当前现状、反馈、标签、旧报告或 known facts。
- 单案制品一经正式写入即不可覆盖、不可原地追加、不可改名复用。
- 所有派生制品都必须绑定父制品内容摘要；父制品摘要不匹配时拒绝继续。
- 同一命主以稳定 subject identity 去重；改 case ID、改变批次或重复报告不能绕过去重。
- claim / abstain / unsupported 三态全部保留；不得为覆盖率强迫六来源发言。
- 签署与验证是两个门：存在 witness registry 不等于签名已验证。
- 两层新门禁和 historical baseline 使用不同的 `gate_id`、evidence class、完成案计数与任务标签计数；同一条标签不得跨 evidence class 复制计数。
- 任一门禁达到 GO 只允许形成升级提案；不得由采集、评分或报告程序自动切换生产入口。

## 3. 证据分类与可声明边界

### 3.1 三类证据分账

| 分类 | 产生时点 | 事实时间 | 允许用途 | 禁止声明 |
|---|---|---|---|---|
| `prediction_first_immediate_retrospective` | freeze 签名验证后当天收集 | freeze 前已经发生的既往经历，或 freeze 当时已经成立的当前现状 | 即时回顾命中、错误类型、覆盖、可评分任务的 retrospective 校准；保留 prediction-first 时间证据 | 不得称 future outcome、future prospective outcome、观察窗负例或 E3 未来事件验证 |
| `future_observation` | freeze 后预注册观察窗内或窗口结束时收集 | freeze 后新发生或在未来窗口内未发生的事实 | 真正未来 outcome、occurred / not_observed、未来 timing 与 binary 校准 | 不得与即时回顾合并成同一标签，不得用回顾事实补未来负例 |
| `no_data` | 任一账本 | 无法核验、失访、冲突未决或窗口未结束 | 完整性与失败统计 | 不得进入正负例分母，不得当作 not_observed |

### 3.2 当天反馈的精确定义

当天反馈必须标记为 `prediction_first_immediate_retrospective`。它证明的是：系统先对未知于 runner 的事实作出冻结预测，随后才揭示 freeze 前已经存在的事实。它不证明系统预测了 freeze 后发生的事件。

“当前现状”以 freeze 验证时点为界：

- 在 freeze 验证前已经成立，即使当天稍后才被收集，归即时回顾账。
- 在 freeze 验证后才发生，归未来观察账。
- 无法确定发生时间相对 freeze 的先后，标记 `no_data`，不得人工猜测归类。

同一任务可以同时拥有即时回顾记录和未来观察记录，但两者必须是不同制品、不同 evidence class、不同 label identity，并各自引用同一冻结父制品。评分报告必须分栏展示，禁止混算后只给一个 prospective 数字。

### 3.3 三个互不替代的门禁身份

本文把门禁身份固定为三类，名称、计数和结论不得混用：

| `gate_id` | 中文名称 | 证据账本 | 定位 |
|---|---|---|---|
| `prediction_capability_candidate_gate_v1` | 预测能力候选 GO | 仅 `prediction_first_immediate_retrospective` | 新门禁；验证 prediction-first 即时回顾下的候选预测能力，只能形成升级提案 |
| `future_empirical_gate_v1` | 未来实证 GO | 仅 `future_observation` | 新门禁；验证 freeze 后三个月内的短期未来问题，只能形成升级提案 |
| `historical_platform_baseline_2026_07_15` | historical baseline | 按 2026-07-15 正式门禁制品定义 | 原 30 案平台基线；保留原名称、阈值、状态和事实源，不被本文重命名、重算或覆盖 |

“完成案”均指唯一 `subject_id_hash` 对应的合格单案父链完整、freeze verification 为 VERIFIED、未 STOP、对应 evidence class 的 bound label 可评分；招募数、intake 数、冻结数、cohort 成员数、另一 evidence class 的完成数均不能替代。同一命主可以分别为两个新门禁贡献一案，但必须各自满足对应账本的完成定义，且不得把同一事实或同一 label identity 复制到两个门禁。

### 3.4 预测能力候选 GO

`prediction_capability_candidate_gate_v1` 只有在以下条件**同时**满足时才可判为“预测能力候选 GO”，否则为 HOLD；发生泄漏、hash 篡改或角色隔离破坏时按本文 STOP 规则处理：

1. 至少 20 个独立命主完成单案 intake → blind bundle → 六来源 freeze → witness 签署 → freeze verification → `prediction_first_immediate_retrospective` 绑定链。
2. 至少一个可评分任务有 15 条有效即时回顾标签，并且正例数大于 0、反例数大于 0；`no_data`、冲突未决和不可评分标签不计入 15 条。
3. 至少一个满足第 2 条的任务 `calibration_error < 0.2`；必须严格小于，等于 0.2 仍为 HOLD。
4. `marriage.divorce_or_remarriage`、`wealth.debt`、`health.system_risk` 的所有计分标签均由两名不同人类独立复核；两审冲突必须由符合角色隔离要求的第三方仲裁，未决冲突不计分。
5. 至少一个多派竞争任务有不少于 5 条有效竞争记录；竞争记录必须是同案同任务至少两个 school 具有可比较效用，不能由 unsupported、缺失效用或改写 static baseline 制造。
6. `selection_change_count >= 1`，且 `learned_utility >= static_utility`；两项必须基于同一预注册留出比较口径。
7. hash、witness、无泄漏、subject 去重、不可覆盖、三态保留和父制品摘要验证全部通过。

该 GO 是“候选”而非生产授权。判为 GO 时只创建不可变门禁结果与升级提案，不修改 [`run_pipeline()`](../../../engine/application/pipeline_runner.py:1)、[`DEFAULT_RUNNER_REGISTRY`](../../../engine/claims/runner_registry.py:1)、默认 routing mode、生产权重或生产规则。

### 3.5 未来实证 GO

每个进入单案冻结链的命主必须在 freeze 前预注册**恰好 1 个**短期未来问题。该问题必须有唯一 `future_task_id`、明确的 binary 判定、`observation_window.start_at=freeze_at`、不晚于 freeze 后三个月的 `observation_window.end_at`、正例定义、反例定义和可核验来源要求。窗口未结束、失访、时间不明或冲突未决只能记为 `no_data`，不得记反例。

`future_empirical_gate_v1` 只有在以下条件**同时**满足时才可判为“未来实证 GO”，否则为 HOLD；用户批准的“其他门槛不变”在本规格中采用严格口径，不设置无路由竞争豁免：

1. 至少 10 个独立命主完成其预注册短期未来问题的到期观察；每案只以该 1 个问题贡献未来完成案计数。
2. 至少一个同类 `future_task_id` 有 8 条有效未来标签，并且正例数大于 0、反例数大于 0；`no_data` 不计入 8 条。
3. 至少一个满足第 2 条的同类任务 `calibration_error < 0.2`；必须严格小于。
4. 三项高风险任务的未来标签重新执行双人独立复核与冲突第三方仲裁；不得复用即时回顾审查冒充未来审查。
5. 至少一个多派竞争未来任务有不少于 5 条有效竞争记录。
6. `selection_change_count >= 1`，且 `learned_utility >= static_utility`。即使某个未来任务本身没有路由竞争，也不产生 `not_applicable` 豁免；总体门禁在第 5 或第 6 条不足时继续 HOLD。
7. intake、bundle、freeze、未来问题预注册、witness、verification、future observation 和 bound label 的全部 hash 可复算且父链一致；泄漏扫描为 0，角色隔离和 subject 去重通过。

该 GO 同样不自动切生产。判为 GO 时只形成独立升级提案，生产入口继续等待单独批准的契约变更。

### 3.6 historical baseline 隔离与当前状态

原“至少 30 个 prospective 或 E3 案例进入冻结评估链”及其配套门槛保留为 `historical_platform_baseline_2026_07_15`。它不是上述 20 案或 10 案门禁的上位、下位或别名，也不能用 `20 immediate + 10 future = 30` 拼接满足。本文不得覆盖或原地修订 [`META/six-month-platform-gate-2026-07-15.md`](../../../META/six-month-platform-gate-2026-07-15.md:1) 与 [`META/six-month-platform-gate-2026-07-15.json`](../../../META/six-month-platform-gate-2026-07-15.json:1)；未来实现只能创建新的派生门禁制品并引用它们的路径与 SHA-256。

截至本规格修订时，首案只有授权招募记录、`input.md`、preflight PASS 与单案 intake dry-run PASS，尚未完成正式 intake、freeze、witness、verification 或即时回顾。因此，两个新门禁均为 HOLD：

- `prediction_capability_candidate_gate_v1 = HOLD`；
- `future_empirical_gate_v1 = HOLD`；
- `historical_platform_baseline_2026_07_15 = HOLD`，状态继续以原正式门禁制品为准。

任何汇总必须分门禁输出 immediate retrospective 完成数、future observation 完成数、两类各自的正例、反例、`no_data`、校准、竞争、selection change、learned/static utility、高风险审查与 hash/witness/泄漏审计；不得只给一个混合 prospective 数字。

## 4. 单案不可变命名与目录

### 4.1 稳定 case ID

完整 case ID 沿用：

```text
P-GO-YYYY-NNN-{乾|坤}-{四柱}
```

编号在授权入组时分配，失败后不得复用。完整 case ID 是路径身份；`subject_id_hash` 是跨路径去重身份。路径中不加入姓名、联系方式、经历、健康状态或其他 PII。

### 4.2 单案根目录

每案评估制品使用独立根目录：

```text
META/prospective-go/single-cases/<case_id>/
```

建议的正式制品名如下：

```text
<case_id>--intake--v001.json
<case_id>--blind-bundle--v001/
<case_id>--frozen-run--v001.json
<case_id>--witness-freeze--v001.json
<case_id>--freeze-verification--v001.json
<case_id>--future-question-registration--v001.json
<case_id>--immediate-retrospective--unbound--v001.json
<case_id>--high-risk-reviews--v001/
<case_id>--immediate-retrospective--bound--v001.json
<case_id>--reveal-provenance--v001.json
<case_id>--future-observation--unbound--v001.json
<case_id>--future-observation--bound--v001.json
<case_id>--case-completion--v001.json
```

### 4.3 不可变规则

1. `v001` 表示该制品类型的首次正式版本，不表示可覆盖版本。
2. 若操作在正式写入前失败，删除临时 sibling 后仍可重试创建 `v001`。
3. 若正式制品已经存在但随后发现业务错误，不得覆盖；创建 `v002`，显式记录 `supersedes`、`supersedes_sha256`、原因和批准者。旧版本永久保留。
4. bundle 目录必须不存在后才允许创建；内容摘要由白名单相对路径与文件 SHA-256 确定。
5. 每个 JSON 制品都必须包含 `schema_version`、`case_id`、`subject_id_hash`、`created_at`、`artifact_sha256`、直接父制品的 `artifact_path` 与 `artifact_sha256`；摘要计算排除自身 `artifact_sha256` 字段。
6. evidence 制品必须包含 `evidence_class` 和全局唯一 `label_identity`；门禁派生制品必须包含 `gate_id`，不得依赖文件名猜测门禁或证据分类。
7. 单案完成制品只能引用已经验证且状态非 STOP 的父制品，不能把不完整链包装为完成。

## 5. 单案当天状态机与数据流

### 5.1 状态机

```text
RECEIVED
→ INTAKE_REGISTERED
→ BUNDLE_PREPARED
→ FUTURE_QUESTION_REGISTERED
→ SIX_SOURCE_FROZEN
→ WITNESS_SIGNED
→ SIGNATURE_VERIFIED
→ FEEDBACK_RELEASED
→ IMMEDIATE_RETROSPECTIVE_BOUND
→ CASE_COMPLETE_FOR_RETROSPECTIVE

未来观察支线：
FUTURE_QUESTION_REGISTERED
→ OBSERVATION_WINDOW_MATURED
→ FUTURE_OBSERVATION_BOUND
→ CASE_COMPLETE_FOR_FUTURE

任一步发现泄漏 / identity 冲突 / hash 失配
→ STOPPED_CONTAMINATED（终态；不得恢复计分）

非污染的环境或操作失败
→ RECOVERABLE_HOLD（从最后一个已验证不可变父制品派生重试）
```

### 5.2 当天正式 intake

- 每案到达即独立执行正式 intake，不等待 10 案。
- intake 只消费授权后的脱敏预测输入：性别标记、四柱、出生时间、起运、大运、真实逐年流年和预注册任务。
- intake 不得包含经历、现状、反馈、标签、报告或 known facts。
- 单案 intake 必须引用冻结十任务目录和六来源规则快照的精确摘要。
- 每案必须在 freeze 前预注册恰好 1 个三个月内可核验短期未来问题；intake 必须引用 future question registration 的路径与摘要，或在同一原子写入边界内生成并互相绑定二者。
- tasks-by-case 可继续用预注册短槽位解析完整 case ID，但正式 intake 只写当前一个完整 case；未来槽位不会进入该单案制品。
- 所有写操作先 dry-run；dry-run 输出不得写盘。

### 5.3 单案盲包

单案盲包只允许：

```text
intake.json
tasks.json
rule-snapshot.json
future-question.json
bundle-manifest.json
cases/<case_id>/chart.json
```

manifest 必须证明 case 集恰为一个、schools 恰为六来源、评分任务来自 intake 白名单，并且恰有 1 个 future question。原始 `input.md` 不进入 bundle；feedback、labels、report、known facts、旧结论和非白名单文件出现即 STOP。

### 5.4 六来源冻结

冻结步骤只消费已验证的单案 bundle，输出六来源对该案预注册任务的完整三态矩阵。六来源固定为 `ziping`、`ditiansui`、`duan`、`ren`、`gao`、`yang`。冻结制品绑定：

- intake SHA-256；
- bundle SHA-256；
- task catalog SHA-256；
- rule snapshot SHA-256；
- case/task assignments；
- future question registration SHA-256；
- frozen run hash；
- freeze UTC 时间。

任何 timing claim 必须引用真实 `liunian_steps`；缺输入或无触发时 abstain 合法，禁止补造。

### 5.5 独立 witness 签署与验证

witness 必须独立于 intake operator、runner operator、outcome custodian 和高风险 reviewer。每案 registry 记录严格递增的 `registered → prepared → freeze` 三事件段，并分别绑定 input、bundle 与 freeze 摘要。

签署完成后，必须由验证步骤重新读取实际 intake、实际 bundle manifest、实际 frozen run 与 registry，在持有 witness key 的临时本机环境中验证：

1. registry schema 与 hash 链连续；
2. 每个事件 HMAC 有效；
3. 事件 case ID 与当前单案一致；
4. payload 摘要与实际父制品一致；
5. 时间严格满足 registered < prepared < freeze；
6. 当前 registry root 与见证方外部保存的 root 一致。

验证结果写入全新的 freeze verification 制品；只记录验证状态、父摘要、验证时间和 witness 身份引用，不记录密钥。只有 `status=VERIFIED` 才能打开反馈释放门。

### 5.6 反馈释放与当天即时回顾

反馈资料在独立 custody 边界中等待，不得预先放入仓库。释放门通过后才允许 outcome custodian 收集或导入：

- freeze 前已经发生的既往经历；
- freeze 时已经成立的当前现状；
- 每项事实的发生时间或时间范围、来源引用、可核验等级和冲突状态。

unbound immediate retrospective 制品不得含 runner rationale、预测概率或报告文本。它绑定 freeze verification SHA-256，并显式写 `evidence_class=prediction_first_immediate_retrospective`、`fact_cutoff_at=freeze_at`、`collected_after_verification=true`。

反馈释放不是自动生产回灌。评估标签和生产 case 反馈维持不同入口：即时回顾先形成评估制品；若业务另行批准生产反馈摄入，只能经 [`tools/feedback_ingest.py`](../../../tools/feedback_ingest.py:1) 的独立 dry-run / 人工确认流程，且不得改写冻结预测。

### 5.7 三个月短期未来观察

future question registration 必须在 freeze 前写入并进入 blind bundle，至少包含：`schema_version`、`case_id`、`subject_id_hash`、`future_task_id`、`question_text_redacted`、`outcome_type=binary`、`positive_definition`、`negative_definition`、`verification_source_requirements`、`observation_window.start_at`、`observation_window.end_at`、`registered_at`、父制品引用与 `artifact_sha256`。`observation_window.end_at` 必须晚于 freeze 且不超过 freeze 后三个月；每案问题数不等于 1 时 fail-closed。

到期后才允许生成 future observation。每条有效记录必须包含 `evidence_class=future_observation`、独立 `label_identity`、`future_task_id`、`label`、`observed_at`、完整观察窗、来源引用、冲突状态、高风险 review 引用和 freeze / registration 父摘要。`label` 只允许 `occurred`、`not_observed`、`no_data`；只有窗口完整结束且满足预注册反例核验要求时才能写 `not_observed`。

## 6. 反馈释放门禁

门禁采用 fail-closed。以下条件必须全部满足：

- 正式单案 intake 存在且摘要可复算；
- blind bundle 实际文件精确匹配白名单和 manifest；
- frozen run 验证通过，且 case/task/school 网格无缺失、无重复；
- witness registry 三事件完整，HMAC、hash 链和时间顺序验证通过；
- freeze verification 制品为 VERIFIED；
- witness 与 intake / runner / custodian 角色不重叠；
- feedback custody 尚未释放，且仓库扫描无反馈泄漏标记；
- 目标 immediate retrospective 路径不存在；
- 当前案未被标记 STOP。

任一条件不满足时，输出 HOLD 或 STOP 原因，不读取反馈正文，不创建空反馈制品。门禁检查顺序必须保证“验证父制品先于打开反馈文件或请求反馈内容”。

## 7. 高风险婚姻、债务、健康双审

高风险任务固定为：

- `marriage.divorce_or_remarriage`；
- `wealth.debt`；
- `health.system_risk`。

每项高风险即时回顾事实执行以下链：

1. 从 unbound immediate retrospective 生成去预测化 review packet；packet 只含事实、来源、时间和任务定义，并绑定相同 observation / fact packet SHA-256。
2. reviewer A 与 reviewer B 是两名不同的人类，独立签署，不得看预测、对方意见或报告。
3. 两审一致才生成 A 级标签。
4. 两审冲突时保持 HOLD；由与 A/B、intake、runner、custodian 均不同的 adjudicator 仲裁。
5. 两份原始意见和仲裁永久保留；禁止删除冲突样本以改善指标。
6. 健康标签只表达任务目录定义的风险事实，不作医学诊断；婚姻压力不等于离婚/再婚；正常信用消费不等于显著债务。

未来观察账若涉及同三项任务，必须重新基于 future observation packet 双审；不得复用即时回顾的审查结果冒充未来标签。

## 8. 每 10 案汇总、评分与迭代

### 8.1 十案边界

“每 10 案”按连续且不可复用的 intake 序号形成 cohort，例如 001—010、011—020。单案何时 intake / freeze / 反馈不受 cohort 是否满员影响。只有达到 10 个 `CASE_COMPLETE_FOR_RETROSPECTIVE` 且未 STOP 的唯一 subject 后，才允许创建该 cohort 的汇总。

STOP 案保留原编号且不计完成数。为了避免改写 cohort 边界，包含 STOP 案的序号区间仍被记录；汇总 manifest 明确列出 included、stopped 和尚需补充的后续序号。补足到 10 个可用完成案时，使用实际纳入 case ID 的有序集合形成 cohort identity，而不是偷偷替换旧案。

### 8.2 父制品引用

汇总目录使用全新路径：

```text
META/prospective-go/cohorts/cohort-<first>-<last>--<member-set-sha256-prefix>/
```

汇总 manifest 顶层必须记录：

- `schema_version`、`cohort_id`、`created_at`、`artifact_sha256`；
- `gate_ids`，固定显式列出 `prediction_capability_candidate_gate_v1`、`future_empirical_gate_v1`，并以只读引用列出 `historical_platform_baseline_2026_07_15`；
- `member_set_sha256`、`task_catalog_sha256`、`rule_snapshot_sha256`；
- `evidence_classes`、`score_artifacts`、`gate_result_artifacts`；
- historical baseline 两个事实源的仓库相对路径和当次复算 SHA-256，禁止嵌入后改写其内容。

汇总 manifest 对每案只记录：

- case ID 与 subject identity 摘要；
- intake、bundle manifest、future question registration、frozen run、witness、freeze verification、bound immediate feedback、bound future observation、case completion 的仓库相对路径；
- 每个父制品的 SHA-256；
- `evidence_class` 与对应 `label_identity`；
- `retrospective_completion_status` 与 `future_completion_status`，禁止用单一 `completed=true` 混合表达；
- 高风险审查状态及 review / adjudication 父摘要。

汇总不得把父制品复制后当新真相源，不得覆盖、重写或补字段到父制品。读取时逐一复算摘要；任一父制品缺失或漂移，整次汇总 STOP，已有父制品保持不动。

### 8.3 汇总输出

每个十案 cohort 只创建派生制品：

```text
cohort-manifest--v001.json
immediate-retrospective-scores--v001.json
future-observation-scores--v001.json（仅在存在合格未来观察时）
high-risk-audit--v001.json
prediction-capability-candidate-gate--v001.json
future-empirical-gate--v001.json
iteration-proposal--v001.json
cohort-report--v001.md
```

评分必须按 evidence class 分账。没有未来观察时，不创建空 future score；`future-empirical-gate--v001.json` 仍可作为门禁状态制品创建，但必须写 `status=HOLD`、完成数为 0、缺口原因和 `score_artifact=null`，不得伪造空评分。两个门禁结果 JSON 至少包含 `schema_version`、`gate_id`、`status`、`evaluated_at`、`subject_counts`、`task_label_counts`、`positive_counts`、`negative_counts`、`no_data_counts`、`calibration_error_by_task`、`competitive_count_by_task`、`selection_change_count`、`learned_utility`、`static_utility`、`high_risk_review_status`、`hash_audit_status`、`witness_audit_status`、`leakage_audit_status`、`unmet_conditions`、父制品引用与 `artifact_sha256`。阈值必须来自对应 `gate_id` 契约，不允许共享一个含糊的 `prospective_thresholds` 对象。

`cohort-report--v001.md` 必须有三个独立状态区块，标题固定为“预测能力候选 GO”“未来实证 GO”“historical baseline（只读引用）”。每个区块显示所用 evidence class、完成案分子/门槛、同类任务有效标签及正反例、校准误差、竞争数、selection change、learned/static utility、高风险审查、hash/witness/泄漏审计、当前状态和未满足条件。报告不得输出混合完成数，不得把 historical baseline 标成任一新门禁，也不得宣称 GO 已切生产。

iteration proposal 只是只读建议，且只有对应门禁判为 GO 时才能引用该 GO；它不能自动写生产规则、权重、默认路由或历史 snapshot。每个新迭代若获批准，创建新的内容寻址 capability snapshot，并保留 cohort 父摘要；禁止回写本 cohort 预测。

### 8.4 防覆盖规则

- cohort 路径必须不存在。
- 同一 member set + 同一父摘要重复运行应得到相同内容结果；若目标已存在，只允许验证一致，不允许覆盖。
- 父制品更新只能通过新版本产生，因此必须创建新的 cohort 版本或新 member-set identity；旧汇总不变。
- 跨 cohort 总汇总同样只引用 cohort manifest 与摘要，不下钻改写单案。

## 9. 见证人本机临时环境变量

见证密钥只能由独立见证人在其本机临时会话中提供。不得写入命令参数值、shell 历史文本、仓库文件、日志、截图、聊天、CI 配置或制品。

Windows 10 默认 `cmd.exe` 的操作规范：

```bat
set "SCHOOL_CAPABILITY_WITNESS_KEY=<由见证人在本机临时输入的秘密值>"
python -m tools.school_capability_prospective witness-freeze-chain ... --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY --dry-run
python -m tools.school_capability_prospective witness-freeze-chain ... --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY
python -m tools.school_capability_dataset witness-verify ... --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY
set "SCHOOL_CAPABILITY_WITNESS_KEY="
```

要求：

1. 上述占位文本不是实际密钥，设计、测试和文档不得替换为真实值。
2. 使用新开的临时终端；完成签署和验证后立即执行清除命令并关闭终端。
3. 清除后运行不显示值的存在性检查；检查只能报告 SET / NOT SET，不能回显密钥。
4. 密钥不得继承到长期运行服务或 VS Code 全局环境；不得使用系统级持久化设置。
5. registry root 由见证方在仓库外保存；外部记录只含 root、case ID、时间与签署身份引用，不含密钥或 PII。
6. 若怀疑密钥泄漏，立即停止使用该 key，受影响且尚未释放反馈的案例重新由新独立 key 建链；已经释放反馈的案例不得重新包装为清洁预测，按泄漏 STOP 处理。

## 10. 泄漏 STOP

### 10.1 STOP 触发器

以下任一情况令受影响案例 STOP；若无法证明影响边界仅限单案，则整个未评分 cohort STOP：

- freeze verification 前 runner、intake operator 或 blind bundle 接触经历、现状、反馈、标签、旧报告或 known facts；
- feedback 文件、字段、路径标记或正文进入 blind bundle；
- witness 签名无效、事件断链、registry root 回滚或父摘要不匹配；
- freeze 后原地改写 intake、bundle、frozen run 或 witness；
- 重复 subject、历史案例改名或复制命盘冒充新案；
- reviewer packet 包含预测、概率、runner rationale、报告或另一 reviewer 意见；
- 同一人违反角色隔离；
- 密钥泄漏且无法证明泄漏发生在相关签署之后；
- 把即时回顾标成 future outcome，或把 no_data 当负例；
- 为改善指标删除、替换或重冻已知结果案例。

### 10.2 STOP 处置

- 立即关闭反馈释放门和评分入口。
- 写独立 contamination incident，仅含 case ID、触发类型、发现时间、受影响制品摘要和处置，不含 PII / 密钥 / 反馈正文。
- 所有既有制品保持字节不变；不得“清理后继续用”。
- STOP 案不计任何 GO 样本，但保留在招募、失败率和审计分母中。
- 若泄漏边界不确定，采用更大影响边界，不按最乐观解释缩小。

## 11. 失败恢复

| 失败点 | 分类 | 恢复方式 |
|---|---|---|
| dry-run 输入校验失败 | 可恢复 HOLD | 修正尚未正式写入的源输入后重跑；编号不复用 |
| 正式 intake 写入前进程中断 | 可恢复 HOLD | 删除工具产生且未发布的临时 sibling；重新创建同一 v001 |
| intake 已正式存在，bundle 未创建 | 可恢复 HOLD | 复验 intake 摘要，从该父制品创建 bundle |
| bundle 已存在，freeze 失败 | 可恢复 HOLD | 复验 bundle；修复环境后创建 frozen run，不改 bundle |
| frozen run 已存在，witness 未签 | 可恢复 HOLD | 保持反馈封存；独立 witness 后续签署 |
| witness 已签但验证失败 | STOP 或 HOLD | 环境性读取失败为 HOLD；HMAC/hash/root 不一致为 STOP，不得释放反馈 |
| 签名验证通过，反馈收集失败 | 可恢复 HOLD | 保持 VERIFIED 门状态，稍后收集；记录延迟，不伪造空反馈 |
| 反馈已释放后发现预测链错误 | STOP | 不允许重冻或重新签名洗白；该案永久退出清洁评分 |
| 高风险两审冲突 | HOLD | 保留两审，等待独立 adjudicator；不得降级成单审标签 |
| cohort 汇总中父摘要漂移 | STOP 汇总 | 不改父制品；调查漂移，旧 cohort 若存在保持不变 |

恢复原则是从最后一个“已验证、不可变、未污染”的父制品向前派生；任何恢复都不能回到已知反馈之前重新生成预测。

## 12. 与当前 Task 3 / Task 4 及 GO 门禁的兼容

### 12.1 Task 3 语义调整

保留连续真实招募、授权、完整输入、subject 去重、逐年流年和 intake 隔离要求。唯一节奏变化是：

- 从“每 5 案 dry-run、满 10 案正式 intake”改为“每案 dry-run 后当天正式单案 intake”；
- 招募日志仍 append-only；
- 每案 input 仍位于 `cases/<case_id>/input.md`；
- 编号与任务预注册配额保持连续，不按反馈挑案。

### 12.2 Task 4 语义调整

保留 blind whitelist、六来源三态、规则与任务摘要绑定、witness 独立性和先 dry-run 后写入。唯一粒度变化是：

- 从“每 10 案一个 bundle / frozen run / witness registry”改为“每案各自一个 bundle / frozen run / witness registry / verification”；
- 每 10 案只聚合父引用、评分与迭代；
- 单案完成不等待 cohort。

### 12.3 后续 Task、handoff 与行动计划兼容

- 现有高风险 review 契约继续使用，但输入改为 evidence-class 明确的单案 observation packet。
- 后续 reviewed manifest、score 和 L1 adapter 消费 cohort manifest 展开的父引用；不得要求把 prospective frozen run 冒充 historical schema。
- future observation 流程仍可在同一单案根下另账追加新版本制品，但不得修改即时回顾制品。
- [`feedback_ingest.py`](../../../tools/feedback_ingest.py:1) 仍是生产反馈唯一入口；评估制品不自动触发生产学习。
- 后续实施必须更新 [`plans/upgrade-guides/post-gate-action-plan-2026-07-15.md`](../../../plans/upgrade-guides/post-gate-action-plan-2026-07-15.md:314)：Task 3 改为逐案正式 intake，Task 4 改为逐案 bundle / freeze / witness / verification，Task 5 增加每案 1 个三个月内到期 future question，Task 7—10 分别消费两套 gate identity 和阈值，Task 11 将两个新门禁作为独立提案证据并保留 30 案 historical baseline。
- 后续实施必须更新 [`handoff.md`](../../../handoff.md:1)：下一步不再等待首批 10 案才正式 intake，而是先完成首案单案链与即时回顾；同时预注册其 1 个短期未来问题。handoff 必须分别显示两个新门禁的 HOLD 缺口，不能继续只用原 30 案计数描述全部门禁。
- 上述计划与 handoff 更新属于后续实施任务；本子任务只修订本设计文档，不直接修改二者。

### 12.4 两个新门禁与 historical baseline 均继续 HOLD

本设计本身、流程测试通过、首案单案链完成或任一十案 cohort 汇总均不自动构成任何门禁 GO。当前首案即时回顾尚未完成，因此两个新门禁均明确 HOLD。以下保持不变：

- 当前 Task 3 / Task 4 运行状态在真实单案链落地前仍 HOLD；
- `prediction_capability_candidate_gate_v1` 在 20 个独立即时回顾完成案及其余全部条件满足前为 HOLD；
- `future_empirical_gate_v1` 在 10 个独立到期未来观察完成案及其余全部条件满足前为 HOLD；
- `historical_platform_baseline_2026_07_15` 继续按原 30 案正式门禁制品判定，不用两个新门禁的样本相加冲抵；
- 生产默认仍 static，staged 仅评估；
- 真实 future outcome 门槛不能由 immediate retrospective 替代；
- 任一 GO 只允许形成独立升级提案，不在采集、评分或报告流程中直接切入口。

## 13. 首案迁移路径

当前首案只有授权招募记录、`input.md`、preflight PASS 与单案 intake dry-run PASS；正式 intake、future question registration、bundle、freeze、witness、即时回顾、未来观察和报告均不存在。首案即时回顾明确为**未完成**，不能计入任一新门禁。该状态适合无数据重写迁移：

1. 冻结当前首案 `input.md` 的内容摘要并复验没有反馈 / 经历 / 现状标记。
2. 保留原 case ID、招募编号、授权引用和 subject identity；不得重建为另一个“新案”。
3. 为首案预注册恰好 1 个 freeze 后三个月内可核验的短期未来问题，冻结任务、正反例定义、核验来源和观察窗。
4. 使用新单案命名执行 intake dry-run；通过后正式创建首案 `--intake--v001.json`，并绑定 future question registration。
5. 依次创建单案 blind bundle、六来源 frozen run、witness registry，并完成独立签名验证。
6. 在 verification 为 VERIFIED 前，不创建 `feedback.md`、即时回顾、observation、report 或 label。
7. 验证通过后，当天收集既往经历和当前现状，分类固定为 immediate retrospective；预注册未来问题只在观察窗到期后进入独立 future observation 账。
8. 首案完成即时回顾后可计入 `prediction_capability_candidate_gate_v1` 和第一个 10 案 cohort；只有其 future observation 到期且可评分后，才可另计入 `future_empirical_gate_v1`。
9. 现有未提交工作树中的其他文件不得被本设计提交、迁移或清理；实施时必须另行批准计划。

如果审计发现首案在 freeze 前已收集或被 runner 接触经历 / 现状，则不得迁移为清洁 immediate retrospective；该案标记 STOP 或 development-only，并使用下一个连续编号招募真正新案。

## 14. 测试与验收设计

本节只定义未来实现的验收，不创建测试代码。

### 14.1 单案正向链

1. 一个真实格式输入可独立生成正式 intake，不要求 10 案。
2. 每案 freeze 前恰好注册 1 个三个月内到期的 binary future question，窗口与正反例定义可机械验证。
3. bundle 只含六类白名单路径，case 集恰为一，future question 恰为一。
4. 六来源 × 已分配任务形成唯一完整三态矩阵。
5. witness 三事件签署后，使用同一临时环境 key 验证为 VALID。
6. verification 制品生成前，反馈读取函数 / 文件访问未发生。
7. verification 成功后才可创建 immediate retrospective，并正确标记 evidence class 与 cutoff。
8. future observation 只能在预注册窗口到期后创建；`not_observed` 具有完整窗口和核验来源。
9. 两个 evidence class 可引用同一 freeze，但不会合并 label identity、完成案计数或分母。

### 14.2 负向与安全测试

- 单案 bundle 含 feedback、report、known facts、原始 input 或额外文件时拒绝并 STOP。
- intake、bundle、freeze 任一字节变化导致摘要验证失败。
- 错 key、空 key、断链、事件乱序、重复事件、registry root 不符均不能打开反馈门。
- 环境变量缺失时 fail-closed；清除后验证命令不得继续获得 key。
- freeze verification 前尝试打开反馈路径必须失败，并证明未读取正文。
- 重复 subject 即使 case ID 不同也拒绝。
- 已存在目标路径拒绝覆盖；正式错误只能产生 v002 且保留 v001。
- immediate retrospective 被标为 future outcome 时 schema 校验失败。
- future question 缺失、多于 1 个、注册晚于 freeze、窗口超过三个月或缺少正反例定义时 fail-closed。
- 当前现状无法证明早于 freeze 时只能 no_data。
- no_data、未结束观察窗、失访均不能成为 not_observed。
- reviewer 重名、角色重叠、单审、自动 reviewer、packet 含预测、冲突无仲裁均不能生成 A 级。
- 健康 / 婚姻 / 债务即时回顾标签不能复用为未来观察标签。
- STOP 案不能进入 cohort 可评分成员，但必须保留失败审计。

### 14.3 十案聚合测试

- 少于 10 个可用完成案时不创建评分汇总，状态为 HOLD，但单案制品有效。
- 10 个唯一完成案生成稳定 member-set identity。
- cohort manifest 只引用父路径与摘要，不复制或覆盖父制品。
- 任一父摘要漂移导致汇总 STOP。
- immediate 与 future scores 分账；无 future 数据时不创建空 future score。
- 相同父输入重跑内容确定；已存在目标只验证不覆盖。
- iteration proposal 不写生产规则、权重、默认路由或历史 snapshot。

### 14.4 回归与门禁测试

- 当前批量只读制品仍可验证；不静默迁移或覆盖历史 batch。
- Task 3 的预注册短槽位仍唯一解析完整 case ID。
- Task 4 的 bundle hash、freeze hash、witness hash 语义保持兼容。
- `prediction_capability_candidate_gate_v1` 在 19 个独立即时回顾完成案时 HOLD，20 案但无任一任务 15 条有效正反例时 HOLD，`calibration_error == 0.2` 时 HOLD，竞争数 4 时 HOLD，selection change 0 时 HOLD，learned utility 低于 static 时不得 GO。
- `prediction_capability_candidate_gate_v1` 只有 20 案、单任务 15 条正反例、误差严格小于 0.2、高风险双审/仲裁、竞争数至少 5、selection change 至少 1、learned utility 不低于 static 和全部审计同时满足时才输出 GO proposal。
- `future_empirical_gate_v1` 在 9 个到期完成案时 HOLD，10 案但无同类任务 8 条有效正反例时 HOLD，窗口未到期数据不计完成，误差等于 0.2 时 HOLD。
- `future_empirical_gate_v1` 即使同类任务没有路由竞争也不允许 `not_applicable`；竞争数不足 5、selection change 0 或 learned utility 低于 static 均 HOLD。
- `future_empirical_gate_v1` 只有 10 案、同类任务 8 条正反例、误差严格小于 0.2、高风险双审/仲裁、竞争数至少 5、selection change 至少 1、learned utility 不低于 static 和全部审计同时满足时才输出 GO proposal。
- 两个新门禁的计数不得相加满足 historical baseline；`20 immediate + 10 future` 仍不能令 `historical_platform_baseline_2026_07_15` GO。
- 门禁 JSON 缺 `gate_id`、evidence class、分账计数、父摘要或审计状态时 schema 校验失败；cohort manifest 使用单一混合 `completed` 字段时失败。
- 报告必须出现三个固定独立状态区块，不能出现混合 prospective 总数或“已自动切生产”声明。
- 原 [`META/six-month-platform-gate-2026-07-15.md`](../../../META/six-month-platform-gate-2026-07-15.md:1) 与 [`META/six-month-platform-gate-2026-07-15.json`](../../../META/six-month-platform-gate-2026-07-15.json:1) 的 SHA-256 在实施前后保持一致。
- [`run_pipeline()`](../../../engine/application/pipeline_runner.py:1) 与 [`DEFAULT_RUNNER_REGISTRY`](../../../engine/claims/runner_registry.py:1) 的默认行为无变化。
- 全流程不写实际密钥或 PII；日志和异常不回显环境变量值。

### 14.5 设计验收标准

设计实现后，只有同时满足下列条件，单案流程本身才可判“流程 GO”；这不等于平台 GO：

- 单案可在同一天完成 intake → bundle → freeze → witness → verify；
- verify 前反馈不可读，verify 后反馈可释放；
- 即时回顾与未来观察机械分账；
- 三项高风险双审不可绕过；
- 单案与 cohort 均不可覆盖且摘要可复算；
- 泄漏进入 STOP，非污染故障可从最后可信父制品恢复；
- 10 案汇总只引用父制品；
- 两个新门禁可机械独立计算，historical baseline 保持只读隔离；
- 首案即时回顾未完成及两个新门禁 HOLD 的当前状态被诚实输出；
- 任一 GO 只生成升级提案，不自动切生产。

## 15. 运维检查清单

### 单案当天

- [ ] 授权与连续 case ID 已登记，无 PII 入路径。
- [ ] input 仅含预测输入，preflight 与 intake dry-run 通过。
- [ ] 正式单案 intake 已写入全新路径。
- [ ] 单案 bundle 白名单与摘要复验通过。
- [ ] 六来源完整三态冻结通过。
- [ ] 独立 witness 在临时本机会话签署。
- [ ] 使用实际父制品完成签名验证，registry root 已外部锚定。
- [ ] 本机环境变量已清除且未回显。
- [ ] freeze 前已注册恰好 1 个三个月内可核验 future question。
- [ ] 只有 verification=VERIFIED 后才释放反馈。
- [ ] 当天反馈标为 prediction-first immediate retrospective。
- [ ] 高风险事实已进入独立双审或保持 HOLD。
- [ ] future observation 未在窗口到期前创建，no_data 未充当反例。

### 每 10 个完成案

- [ ] 10 个唯一 subject 均有完整单案 completion 父链。
- [ ] STOP 案未计分但保留审计。
- [ ] cohort member set 与全部父 SHA-256 已冻结。
- [ ] immediate / future 分账评分与分账 completion 状态均已生成。
- [ ] 两个新 gate result 分别使用其 `gate_id` 和阈值，historical baseline 仅只读引用。
- [ ] 高风险 A 级与冲突状态单列。
- [ ] 报告分别展示两个新门禁和 historical baseline，不展示混合完成数。
- [ ] iteration 仅为提案，不回写父制品或生产入口。
- [ ] GO / HOLD 按对应正式门禁重新计算，未因“已满 10 案”自动 GO。

## 16. 设计结论

目标架构把不可逆证明点下沉到单案：每个新案当天独立完成短期未来问题预注册、预测冻结和见证验证，随后才揭示 freeze 前既有事实；10 案只承担周期性统计与学习治理，不再阻塞单案证据链。该设计缩短反馈周期，同时通过 evidence class、label identity 与 gate identity 分账，避免把即时回顾伪装成未来 outcome，或把 20 案、10 案与原 30 案 historical baseline 混算。任何未来观察都另建账本、另建标签、另行双审和评分。

截至本规格修订时，首案即时回顾未完成，`prediction_capability_candidate_gate_v1` 与 `future_empirical_gate_v1` 均为 HOLD，原 `historical_platform_baseline_2026_07_15` 也继续按既有正式制品保持 HOLD。未来任一 GO 只形成升级提案，不自动切生产。本文只定义设计，不执行首案迁移、不创建数据制品、不调用实现，也不修改 handoff、行动计划或两个 2026-07-15 门禁事实源。
