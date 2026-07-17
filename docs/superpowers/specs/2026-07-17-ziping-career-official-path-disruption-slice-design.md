# 子平职业路径“官杀路径受扰资格门”staged L2→L3 纵切设计

> 状态：设计已获用户批准，待书面复核  
> 日期：2026-07-17  
> 范围：P2 子平职业路径最小高判别切片  
> 任务：`career.role_change`  
> 目标层：staged L2→L3  
> 生产状态：设计阶段；默认 registry、正式 pipeline、production claim-rules、公共 schema、报告入口与既有任派/杨派路径保持不变

---

## 1. 目的

本设计不迁移子平目录的全部 933 条 production entries，而是选择一个最小、原子、可反驳的职业路径任务，证明以下纵切链成立：

```text
production 来源锚点
  → 稳定 production rule ID ↔ task-scoped rule ID 映射
  → 冻结事实闭包
  → 官杀职业路径受扰资格判别
  → 局部结构态
  → 统一发布态
  → emit-only L2 Claim
  → 专用 L3 结构合法性裁决
```

首要证明不是“子平预测更准”，而是：**职业相关粗 trigger 即使存在，只要结构必要门不成立，就不得进入 L3 pass。**

本切片只负责原局结构合法性与职业路径结构，不生成任派应期，不读取岁运，不调用默认时间窗。

---

## 2. 已核验基线

### 2.1 Git 与并行写区

设计调查开始时已执行：

- `git fetch --prune origin`
- `git status`
- `git rev-list --left-right --count HEAD...origin/main`

调查时本地 `HEAD`、本地 `main` 与 `origin/main` 一致，ahead/behind 为 `0/0`，工作区干净。Git HEAD 属于易漂移运行时信息，不在本设计长期硬编码。

杨派现有专属写区包括：

- `engine/decision/yang_marriage.py`
- `engine/decision/yang_marriage_claims.py`
- `tests/yang_marriage/`

任派现有专属写区包括：

- `engine/decision/ren_career_timing.py`
- `engine/decision/ren_career_timing_slice.py`
- `engine/decision/ren_timing_rules.py`
- `theory/production/ren-career-timing-rules-v1.yaml`
- `tests/ren_timing/`

本设计不修改、覆盖或自动合并上述路径。实施前后都必须重新核验工作区与远端差异。

### 2.2 三套计数必须分账

| 计数 | 当前值 | 含义 |
|---|---:|---|
| `catalog_count` | 933 | `theory/ziping/index.yaml` 的目录条目数 |
| production entries | 933 | 默认 production loader 可加载的 active 条目数 |
| 事业域 production entries | 820 | `domains` 含“事业”的 production 条目数 |
| `executable_slice_count` | 0 | 已进入 executable slice manifest 且具备完整冻结验证制品的子平切片数 |

`catalog_count` 与 production entries 在当前子平目录数值相同，但语义不同；二者都不能替代 `executable_slice_count`。

### 2.3 现有能力与缺口

1. `engine/v5/ziping_runner.py` 已能生成旺衰、格局用神、格局类型、病药及 `career.role_change` 粗事件 Claim。
2. 现有职业变动粗 trigger 包括官杀混杂、食伤官杀并见、伤官见官和地支冲突强度。
3. 现有 task-scoped Claim 使用内嵌规则 ID `ZIPING-ROLE-CHANGE-V1`，但没有映射到 `theory/ziping/index.yaml` 的 production rule ID。
4. V5 独立结构命题证据来源主要指向 Python runner，`rule_ids` 为空，理论来源链不完整。
5. `engine/decision/r10_ziping_career.py` 当前按“子平 + 总体/事业域”整体选取目标，范围大于本切片的单任务边界。
6. 通用 L3 对 `structure_claim` 主要按 confidence 阈值映射 pass/weaken，尚不能证明任务专属必要门。
7. R10 后续仍调用通用 timing builder；本切片必须在专用 L3 截止，禁止进入该路径。

---

## 3. 设计决策

采用“官杀职业路径受扰资格门”作为首个子平 executable slice。

### 3.1 单任务

- `task_id`：`career.role_change`
- domain：`事业`
- school：短 ID `ziping`，长 ID 显式映射到现有系统使用的子平身份
- target layer：L3
- input contract：命盘事实账本 + `cfv-v1` + 本切片规则映射
- time horizon：原局结构；无时间窗

### 3.2 单结论

本切片只回答：

> 官杀所代表的组织、职责或任职路径，是否因食伤介入且通过结构必要门，而形成可发布的“职业角色变化结构”。

本切片不回答：

- 是否一定换工作；
- 何年换工作；
- 是否升职或降职；
- 具体行业、单位性质或收入变化；
- 任派岁运触发是否成立；
- 现实事件是否已经发生。

### 3.3 来源锚点

首切只选两个 production 来源锚点：

1. `ZP-PROD-20260622-011`：用神纯杂；官格财印相生为纯，伤官或七杀混杂为杂。
2. `ZP-PROD-20260622-012`：用神格局高低；财生官、印护官为顺接，伤官破官、七杀混官为逆向。

两个锚点共同支持“官杀路径的支持结构、干扰结构与反条件”，但不直接等于任务结论。

首切不使用以下大复合条目作为主规则：

- `ZP-PROD-20260622-363`：时上偏官涉及时柱、身强、制伏轻重、根气及行运。
- `ZP-PROD-20260622-474`：伤官格涉及伤尽、财印取用、身旺与多种例外。

它们可在后续独立切片中处理，不能扩张本切片事实闭包。

---

## 4. 稳定规则身份映射

### 4.1 映射

```text
production_rule_ids:
  - ZP-PROD-20260622-011
  - ZP-PROD-20260622-012

task_rule_id:
  ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1
```

这是“多个 production 来源锚点 → 一个 task-scoped 原子规则”的显式映射，不修改原 production ID，不把 task rule 写回 933 条目录，不沿用含义过宽的 `ZIPING-ROLE-CHANGE-V1`。

### 4.2 映射约束

映射制品必须：

- 使用严格、版本化 schema；
- 固定 school、task、domain、target layer 和 claim type；
- 列出每个 production rule ID 的来源 path、locator、excerpt 或 digest；
- 声明正向条件、必要门、exclusions、counter conditions、结论、falsifier 与 confidence basis；
- 拒绝未知字段、重复 ID、缺失来源、未知 operator 和空引用；
- 加载后不可变；
- 输入顺序变化不改变规范化映射与冻结 hash。

production rule ID 是来源身份；task rule ID 是执行身份。Claim ID 继续由 school、task、chart signature 与 task rule ID 确定性生成，不得用可读 statement 内容生成身份。

---

## 5. 事实闭包

### 5.1 允许事实

本切片仅允许读取：

- `ChartFactLedger` 的四柱、命盘身份与完整性事实；
- `ChartFeatureVector` 的 evidence completeness；
- 十神计数：正官、七杀、食神、伤官、正财、偏财、正印、偏印；
- `mixed_official_kill`；
- 已由当前命盘确定性生成的格局 profile：`geju_type`、`favor_shishen`、`avoid_shishen`；
- 原局关系强度，且只能作为诊断旁证，不能替代必要门；
- 本切片显式加载的规则映射。

### 5.2 禁止事实

不得读取：

- 大运、流年、候选年份与任派 trigger；
- 任派、杨派或其他流派的结论；
- feedback、labels、reports、known facts；
- 默认 L5 时间窗；
- 既有冻结结果作为当前判别输入；
- production picture trigger 的布尔结果作为结构资格替代物。

### 5.3 完整性

以下任一情况进入 `abstain`：

- CFV evidence completeness 不是 full；
- 十神必要字段缺失或类型非法；
- 命盘身份不可追踪；
- 格局 profile 被声明为必要但缺失；
- production 来源映射不可解析。

---

## 6. 信号与证据家族

### 6.1 原子信号

- `official_present`：正官 + 七杀大于 0。
- `output_present`：食神 + 伤官大于 0。
- `direct_hurting_official`：伤官与正官同时存在。
- `output_official_coexistence`：食伤与官杀同时存在。
- `mixed_official_kill`：正官、七杀混杂信号。
- `wealth_supports_official`：财星对官杀路径构成支持反条件。
- `seal_protects_official`：印星对官杀路径构成保护反条件。
- `geju_favors_official_or_seal`：格局 favor 支持官印路径。
- `geju_avoids_output`：格局 avoid 明确排斥食伤路径。
- `ambient_branch_conflict`：原局支冲突，仅作诊断旁证。

### 6.2 证据家族

原子信号归并为：

1. `official_path_anchor`
2. `output_interference`
3. `official_path_protection`
4. `geju_direction`
5. `ambient_movement_context`

同一十神计数派生出的布尔值、摘要和强度属于同一家族，不重复增加独立证据数。`mixed_official_kill` 不得同时冒充官杀锚点和食伤干扰。地支冲突不能冒充官杀锚点或食伤干扰。

每个家族必须保留：

- family key；
- matched 状态；
- fact refs；
- feature refs；
- production rule refs；
- reason codes；
- 可读诊断说明。

---

## 7. 具名门与判别规则

### 7.1 必要门

#### `complete_fact_closure`

所需命盘、CFV、十神与格局事实完整合法。

#### `official_path_anchor`

正官或七杀结构真实存在。`has_official_picture=true`、事业域命中或地支冲突不能替代该门。

#### `output_interference_present`

食神或伤官真实存在，并与官杀同时进入当前任务事实闭包。只有官杀混杂或只有地支冲突不能替代该门。

#### `structure_qualification`

至少存在一个明确干扰结构：

- 伤官与正官同见；或
- 食伤与官杀并见，且格局方向没有明确排斥该解释。

“粗 trigger 数量达到 N”不能替代此门。

### 7.2 反条件

以下反条件必须被审计：

- 财星支持官杀路径；
- 印星保护官杀路径；
- 格局 favor 明确支持官印；
- 格局 avoid 明确排斥食伤；
- 只有官杀混杂但无食伤干扰；
- 只有环境冲动但无职业结构锚点。

反条件分为：

- `protective`：降低为 weakened；
- `contradictory`：明确推翻正向受扰解释，进入 contradicted。

首版不以简单总分抵消具名门。必要门未过时，任何分数都不能升级。

### 7.3 exclusions

- 非 `career.role_change` 任务；
- 事实闭包不完整；
- 无官杀结构；
- 无食伤介入；
- 只有 production 粗 trigger；
- 只有地支冲突强度；
- 规则来源不可解析；
- 输入包含岁运或其他流派结论并试图参与判别。

---

## 8. 状态模型

### 8.1 局部结构态

- `supported`：全部必要门通过，存在合格官杀—食伤干扰结构，反条件不足以推翻。
- `weakened`：观察到部分相关结构，但保护反条件显著，或尚不足以支持发布。
- `contradicted`：格局方向与财印护官证据明确反驳“官杀路径受扰”解释。
- `abstain`：事实闭包不足、输入非法或不适用。

未知任务不进入局部命理判别，直接发布为 `unsupported`。

### 8.2 统一发布态

| 局部态 | 发布态 | L2 Claim | L3 pass |
|---|---|---:|---:|
| `supported` | `emit` | 1 | 1，前提是专用 L3 再校验通过 |
| `weakened` | `hold` | 0 | 0 |
| `contradicted` | `hold` | 0 | 0 |
| `abstain` | `abstain` | 0 | 0 |
| 不支持任务 | `unsupported` | 0 | 0 |

`contradicted` 映射到 `hold`，因为统一发布协议没有独立 contradicted 发布态；反证必须保留在局部制品，不得被丢弃或转成正向 oppose Claim。

---

## 9. L2 与 L3 边界

### 9.1 emit-only L2 adapter

adapter 只接受 `supported + emit`。其他状态进入 adapter 必须 fail-fast 或返回明确零输出，二者在实现计划中选定一种并冻结测试；不得静默构造低置信 Claim。

输出 Claim：

- `school_id=ziping`
- `task_id=career.role_change`
- `claim_type=structure_claim`
- 无 `time_window`
- rule ID 使用 `ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1`
- evidence 同时包含 family、fact、feature 与 production rule refs
- statement 只表达结构倾向，不表达必然事件
- falsifier 不含年份

### 9.2 专用 L3 adapter

本切片不得依赖通用 L3 的 confidence 阈值来证明资格。专用 L3 必须重新校验：

- Claim 来自本 task rule；
- publication state 为 emit；
- 全部必要 family refs 存在且可解析；
- production rule mapping 完整；
- 无 time window；
- 没有 routing blocker 或 exclusion；
- L2 Claim ID 与映射身份稳定。

只有全部满足时生成一个 `StructuralVerdict(verdict="pass")`。任何缺失都不得 pass。

### 9.3 截断边界

staged 入口到 L3 为止：

```text
Chart + CFV
  → local discrimination
  → emit-only L2 Claim
  → dedicated L3 verdict
  → freeze
  → STOP
```

禁止调用：

- `build_event_hypotheses()`
- `build_timing_probabilities()`
- 任派 timing slice
- 默认报告渲染

因此本切片不会制造任派应期，也不会生成 `1900–2100 lifetime` 或 MVP 默认时间窗。

---

## 10. 首个证伪点

### 10.1 构造

准备一个完整命盘上下文，使：

- production 粗 trigger `has_official_picture=true` 可被独立观察；
- 官杀计数大于 0；
- 但食伤为 0，导致 `output_interference_present` 必要门失败；

或准备第二个变体：

- 官杀与食伤均存在；
- 但财印护官和格局方向形成明确 contradictory 反条件。

### 10.2 预期

第一变体：

- 局部态为 `weakened`；
- 发布态为 `hold`；
- L2 Claim 数为 0；
- L3 pass 数为 0。

第二变体：

- 局部态为 `contradicted`；
- 发布态为 `hold`；
- L2 Claim 数为 0；
- L3 pass 数为 0。

两者都必须证明：

- 粗 trigger 存在不等于结构合法；
- confidence 或信号总数不能绕过具名必要门；
- 不生成 EventHypothesis；
- 不生成 TimingProbability；
- 不调用默认时间窗。

---

## 11. 专用 staged 入口

设计一个仅供专项测试与离线冻结调用的入口，职责为：

1. 校验 task 与输入合同；
2. 加载子平职业专用映射制品；
3. 从 Chart + CFV 提取事实；
4. 归并证据家族；
5. 执行局部判别；
6. 仅 emit 时构造 L2 Claim；
7. 仅合格 Claim 构造 L3 pass；
8. 生成确定性冻结制品；
9. 在 L3 截止。

该入口不得注册到 `engine/claims/runner_registry.py`，不得被正式 pipeline 或 preprod 报告入口自动调用。

---

## 12. 冻结制品

冻结制品至少包含：

- schema version；
- school/task/domain/target layer；
- input contract version；
- chart signature；
- production ↔ task rule mapping digest；
- 规范化事实闭包摘要；
- 证据家族；
- gate 结果；
- local state；
- publication state；
- L2 Claim（如有）；
- L3 verdict（如有）；
- exclusions、counter conditions 与 diagnostic reasons；
- 明确的 `timing_objects=[]` 或等价隔离证明；
- freeze hash。

相同输入重跑、映射输入顺序变化、十神映射键顺序变化和 evidence refs 输入顺序变化后，规范化冻结字节必须一致。

---

## 13. TDD 与测试门禁

实施必须先 RED，再最小 GREEN。每项任务独立提交并复核。

### G0 规格与来源门

- 单任务、单结论、事实闭包、exclusions、counter conditions、falsifier 和 evidence refs 明确。
- production ↔ task rule ID 映射稳定且来源可解析。

### G1 纯判别门

至少覆盖：

- supported positive；
- 无官杀 negative；
- 粗 trigger 有、食伤门无的首个证伪点；
- 财印护官 contradictory；
- incomplete exclusion；
- 门槛 boundary；
- 未知任务 unsupported。

### G2 L2 adapter 门

- 仅 supported/emit 生成一个无时间窗的 structure Claim；
- hold/abstain/unsupported 生成零 Claim或 fail-fast；
- evidence refs 全部可解析；
- production rule refs 和 task rule ID 同时存在；
- Claim ID 稳定。

### G3 L3 门

- 专用 L3 只接受本 task rule 的 emit Claim；
- 首个证伪点 L3 pass 数为 0；
- 缺必要 family、缺来源映射、身份冲突、重复 ID 均拒绝；
- 不以 confidence 阈值替代结构门。

### G4 确定性与截断门

- 相同输入重跑字节等价；
- 输入顺序置换后冻结 hash 相同；
- EventHypothesis 数为 0；
- TimingProbability 数为 0；
- 不导入或调用默认 timing builder。

### G5 生产隔离门

以下路径必须零变化：

- 默认 runner registry；
- 正式 pipeline；
- `theory/production/claim-rules-v1.yaml`；
- 公共 Claim / SchoolClaim / StructuralVerdict schema；
- 报告入口；
- 既有任派与杨派专属路径。

同时运行既有 focused regression，确保杨派、任派、claims、R10 与 production entrypoint 护栏不退化。

### G6 生产候选门

不在本阶段。G0-G5 通过后仅登记：

`staged_verified_production_unchanged`

不得宣称：

- 准确率提升；
- 子平职业能力已生产晋级；
- 933 条 production entries 已迁移；
- 可替换现有 runner；
- 可用于正式报告。

进入 G6 需要独立冻结样本上的误报、漏报、校准、适用性后验与另行审批。

---

## 14. 计划实施写区

规格复核通过后，实施计划应优先使用新的专用路径，例如：

- 子平职业映射 / staged 规则制品；
- 子平职业局部判别器；
- emit-only L2/L3 staged assembler；
- `tests/ziping_career/`；
- 独立验证报告。

具体文件名由实施计划冻结。除最终集成 owner 另行批准外，不修改共享 manifest、机器状态或生产入口。

若实施期间发现并行 agent 已修改拟写路径，必须停止并重新审计，不得自动覆盖或合并。

---

## 15. 错误策略

- 未知字段、operator、rule ID、source ref：加载失败。
- 缺必要事实或类型不兼容：`abstain`，并给 remediation。
- 必要门失败：`weakened/hold`，不得输出低置信 Claim。
- 反条件明确推翻：`contradicted/hold`，保留反证审计。
- 非 emit 进入 adapter：fail-closed。
- evidence ref 不可解析：构造失败。
- 重复 Claim ID 或 verdict ID：合并失败。
- 任意 time window 出现在本切片对象中：测试失败。
- 默认 registry、pipeline、production claim-rules、公共 schema、报告入口或任派/杨派路径发生未授权 diff：G5 失败。

不允许静默降级、默认填充或借用通用时间窗。

---

## 16. 完成定义

本切片只有同时满足以下条件才算 staged 完成：

1. 规格与实施计划获批；
2. TDD RED 证据先于 GREEN；
3. production ↔ task rule ID 映射稳定且可审计；
4. 首个证伪点证明粗 trigger 不能绕过结构必要门；
5. supported/emit 可形成唯一 L2 Claim 与唯一 L3 pass；
6. 其他局部态的 L2 Claim 和 L3 pass 均为 0；
7. 无 EventHypothesis、无 TimingProbability、无默认时间窗调用；
8. 冻结制品确定性通过；
9. 默认生产入口与并行流派路径零变化；
10. G0-G5 验证报告只登记 `staged_verified_production_unchanged`；
11. 每项实施任务独立提交并复核；
12. 实施结束重新执行 Git 一致性与并行写区核验。

---

## 17. 验收摘要

本设计的关键证明链是：

```text
官杀相关 production 粗 trigger
  ≠ 官杀职业路径受扰结构成立

只有：
完整事实闭包
  + 官杀路径锚点
  + 食伤介入
  + 结构资格门
  + 反条件未推翻
  → supported / emit
  → task-scoped L2 structure Claim
  → 专用 L3 pass
```

该链路在 L3 截止。子平负责结构合法性与职业路径结构，任派继续独占真实应期职责。