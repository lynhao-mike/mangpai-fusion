# 跨流派理论切片规范与任派职业变化应期纵切设计

> 状态：已获用户分节批准，待书面复核  
> 日期：2026-07-17  
> 范围：跨流派切片规范、优先级路线图、任付红“职业角色变化应期”首个非杨派 staged 纵切  
> 生产状态：仅设计；不切换默认 registry、pipeline、production rules 或报告入口

---

## 1. 背景与问题

仓库当前同时存在三种口径：

1. 产品入口仍以高德臣、段建业、杨清娟、任付红“四派融合”表述。
2. v5 目标契约采用子平、滴天髓、高德臣、段建业、杨清娟“五派独立命题”。
3. 学派能力评估使用 `ziping / ditiansui / duan / ren / gao / yang` 六个知识来源。

此外，理论目录条目数量与可执行判别能力严重不对称：legacy index、production entries、task-scoped Claim runners 和 executable claim rules 分属不同代际的结构。继续用规则总数代表理论成熟度，会掩盖“条目很多但任务判别器很少”的事实。

另一个 agent 已提交杨派婚姻判别切片设计与实施计划，但尚未落地代码。该工作拥有独立写区，本设计只读借鉴其“局部资格判别、因果家族去重、具名门、fail-closed”原则，不修改或接管杨派实现。

---

## 2. 已核验仓库基线

设计调查时已执行远端同步核验：本地 `main`、本地 `HEAD` 与 `origin/main` 均指向同一提交，ahead/behind 为 `0/0`，工作区干净。

本设计依赖以下当前事实：

- `engine/application/pipeline_runner.py` 仍是 staged fallback / 兼容入口。
- `engine/claims/runner_registry.py` 注册六来源 task runners。
- `engine/v5/ren_runner.py` 已有冲、刑、穿、合、伏吟及大运 fallback 等应期逻辑，但仍是 Python 内嵌判别。
- `engine/decision/l5_timing.py` 当前会为事件无条件生成 MVP 默认时间窗，不可作为任派真实应期证据。
- `theory/production/claim-rules-v1.yaml` 当前没有任派 executable rules。
- 杨派新增成果当前仅为规格与计划：
  - `docs/superpowers/specs/2026-07-17-yang-marriage-discrimination-slice-design.md`
  - `docs/superpowers/plans/2026-07-17-yang-marriage-discrimination-slice.md`

---

## 3. 决策与非目标

### 3.1 选定路径

采用“统一规范先行 + 任派单纵切”路径：

1. 先定义跨流派切片协议、计量口径、状态分层和 G0-G6 门禁。
2. 以任派“职业角色变化应期”完成第一个非杨派 L5 staged 纵切。
3. 用该纵切检验协议，再决定哪些组件值得抽成共享代码。
4. 默认 registry、正式 pipeline、production YAML 与报告入口保持不变。

不采用以下路径：

- 不让多个流派同时各造一套 DTO、状态机与 assembler 后再归一。
- 不在只有杨派设计样本时提前实现大型公共切片框架。
- 不进行全量 legacy 规则机械迁移。

### 3.2 本阶段非目标

- 不修改杨派专属实现与测试路径。
- 不修改公共 Claim、SchoolClaim 或报告 schema。
- 不将任派 staged 纵切注册到默认六来源 registry。
- 不用合成测试结果宣称准确率提升或生产 GO。
- 不让任派重复判断职业变化事件是否成立。
- 不用无真实触发证据的通用默认时间窗冒充任派应期。
- 不把目录条目数当作可执行切片数。

---

## 4. 统一计量与成熟度

### 4.1 两套计数

所有学派能力盘点必须至少分为：

- `catalog_count`：原文、索引或 production entries 的目录条目数。
- `executable_slice_count`：满足本设计最小制品集、进入专用 runner 与冻结验证的可执行切片数。

两者不得相互替代。运行时生命周期数量继续由 `tools/rule_status_scan.py` 获取，不在普通文档长期硬编码。

### 4.2 G0-G5 成熟度概念

- G0：原文材料，无稳定规则身份。
- G1：可追溯索引，有来源锚点但无机器条件。
- G2：声明式 production 条目，有粗 trigger，但条件未完全可执行。
- G3：task-scoped 纯判别器，可产出稳定、可反证结果。
- G4：外置可执行切片，条件、排除、反条件、来源与置信策略可审计。
- G5：有独立样本后验、冻结版本、反馈归因和生产门禁证据。

工程测试通过只能证明 G3/G4 的契约质量，不能自动证明 G5。

---

## 5. 合格理论切片定义

理论切片是“某一知识来源针对一个明确任务，在已声明事实闭包上作出的一个原子、可执行、可反驳、可冻结评估的最小判断单元”。

每个切片必须满足：

1. 单来源，不读取其他流派结论、反馈、标签或旧报告。
2. 单任务，绑定明确 `task_id` 和目标层。
3. 单结论，复合结论拆开。
4. 事实闭包明确，缺事实时 abstain 或 unsupported。
5. 正向条件由白名单谓词求值。
6. exclusions 与 counter conditions 显式。
7. 盘面证据与理论来源均可追溯。
8. 身份稳定，输入顺序不改变 ID 和冻结序列化。
9. 局部语义状态与统一发布状态分层。
10. 只有发布态 `emit` 可以进入目标层 adapter。
11. 高风险命题具有置信封顶和安全文案。
12. 可归因到 school、task、rule、evidence 与版本。

---

## 6. 统一切片协议

本阶段先把协议写成可验证契约，不立即实现公共大框架。

### 6.1 SliceTarget

绑定：

- school namespace
- task ID
- domain
- target layer
- upstream object type
- input contract version
- short school ID 与 long school ID 的显式映射

切片选择器必须声明截断的是 Claim runner 链、V5 链还是 Decision 链，禁止混用对象类型证明错误路径已被截断。

### 6.2 SignalExtractor

只读取：

- 命盘事实账本
- ChartFeatureVector
- 明确获准的上游对象
- 当前切片声明的岁运事实

不得读取 feedback、labels、reports、known facts 或其他流派输出。

### 6.3 EvidenceFamilyReducer

将多个原子信号归并为因果家族：

- 同一原始事实的多个派生字段只贡献一次。
- pair 顺序、别名、摘要与强度字段不增加家族数。
- 多个局部实例可增强家族内部解释，不自动增加独立证据数。
- 无法证明独立时按不独立处理。

### 6.4 GateSpec

每个切片声明：

- 具名必要门
- 具名充分门
- 门的依赖家族
- 合取或析取关系
- input blockers
- gate failures
- routing blockers
- 禁止替代的聚合捷径

通用“信号数达到 N”不得替代具名必要门。

### 6.5 局部语义态与统一发布态

各流派可保留本派语义态，但统一映射为：

- `emit`：允许进入目标层。
- `hold`：有内部观测，但不满足升级资格。
- `abstain`：输入或适用性不足，无法作出该判断。
- `unsupported`：该切片不覆盖此任务。

### 6.6 LayerAdapter

- 只接受 `emit`。
- `hold / abstain / unsupported` 进入 adapter 时必须 fail-fast。
- evidence refs 必须能解析到事实、特征、规则来源或证据对象。
- adapter 不增加判别语义，只做目标层对象组装。

### 6.7 SliceAssembler

统一迁移模式：

1. 从旧输出剥离目标对象。
2. 非目标对象继续通过旧桥。
3. 运行局部切片。
4. 仅在 `emit` 时注入原生目标对象。
5. 合并后拒绝重复 ID。
6. 调用目标层及必要下游层。

默认入口不调用 staged assembler。

---

## 7. 任派首个纵切

### 7.1 任务

任务：职业角色变化应期。

任派只回答：在上游已经成立的职业角色变化事件上，是否存在任派可审计的真实岁运触发，以及可证伪的时间窗口。

任派不回答：命主是否一定换工作、事件本身是否成立、职业变化的结构合法性。

### 7.2 输入契约

必需输入：

- 可追踪的已成立职业角色变化事件。
- 命盘事实与 CFV。
- 当前大运和候选流年事实。
- school/task/version 身份。
- 支持冲、刑、穿、合、伏吟判别的干支关系事实。

若上游事件缺失、身份不可追踪或岁运事实不完整，则不得制造 timing。

### 7.3 原子触发

首切覆盖：

- 冲
- 刑
- 穿
- 合
- 伏吟
- 大运 fallback

每个触发必须成为独立可审计 atom，包含：类型、参与实体、年份/运段、事实引用、来源规则引用与强度/优先级。

### 7.4 家族去重

同一柱关系、同一岁运关系或同一派生事实属于同一家族。关系的镜像表示、重复 pair、多个摘要字段不得重复计入。

### 7.5 任派局部状态

- `timing-ready + emit`：上游事件成立，事实闭包完整，具名应期门通过，有真实可证伪时间窗。
- `insufficient-trigger + hold`：存在相关触发，但缺完整时间闭包或独立确认。
- `abstain`：无相关触发、输入非法、上游事件缺失或适用性不足。
- `unsupported`：任务不是职业角色变化应期。

### 7.6 状态机

1. 校验任务支持范围。
2. 校验上游事件身份。
3. 校验命盘、大运、流年事实闭包。
4. 提取触发原子。
5. 归并证据家族。
6. 计算具名应期门。
7. 门通过则 `timing-ready + emit`。
8. 有相关证据但不完整则 `insufficient-trigger + hold`。
9. 无有效触发或输入不足则 `abstain`。
10. 只有 emit 进入 L5 adapter。

### 7.7 首个证伪点

给定一个已成立的职业角色变化事件，但当前大运/候选流年不存在任派定义的有效冲、刑、穿、合或伏吟触发。

预期：

- 局部状态为 abstain 或 hold，具体取决于是否存在不完整相关证据。
- 发布态不是 emit。
- 目标 L5 对象数为 0。
- 不允许调用通用默认时间窗填补空缺。

### 7.8 L5 输出

L5 timing 必须包含：

- 稳定 timing ID
- 上游 event ID
- 时间窗起止
- 触发类型
- 盘面/岁运证据引用
- 任派规则来源引用
- falsifier
- 适用性和置信依据

时间窗起止倒置、跨度越界、缺触发年份或 evidence ref 不可解析时，构造必须失败。

### 7.9 L6 边界

如专项测试继续到 L6，只证明引用链和接线完整，不宣称任派仲裁能力或准确率提升。L6 的测试结论必须与应期语义验证分开记录。

---

## 8. 原因分类与错误处理

### 8.1 原因分类

- `input_blockers`：非法四柱、缺性别、缺大运/流年、版本不兼容。
- `failed_gates`：具名应期门未通过。
- `routing_blockers`：上游事件缺失、任务不归任派。
- `diagnostic_reasons`：触发了什么、为何 hold、需要什么补证。
- `falsifier`：仅属于已输出 timing 命题。
- `remediation`：用于 abstain，说明需要补充什么事实。

### 8.2 错误策略

- 未知 trigger/operator/source：加载时拒绝。
- 同源重复：reducer 去重并保留审计记录。
- evidence ref 不可解析：adapter 失败。
- 非 emit 进入 adapter：fail-fast。
- 重复 ID：assembler 合并时失败。
- 时间窗非法：构造失败。
- 默认生产入口或 production artifact 发生未授权 diff：G5 失败。
- 杨派路径发生写冲突：本任务停止，不自动合并。

不允许静默降级或自动制造默认结论。

---

## 9. G0-G6 门禁

### G0 规格门

明确目标、非目标、首个证伪点、局部状态、发布状态、来源、输入闭包和目标层。

### G1 纯判别门

只测试 extractor、reducer、具名门和状态机，不接公共下游。

### G2 适配门

仅 emit 可适配；其他状态 fail-closed；证据引用可解析。

### G3 旁路与非目标门

- 不丢上游事件。
- 不重复制造事件。
- 目标必须先从旧桥剥离。
- 稳定 ID。
- 重复引用或身份冲突拒绝。

### G4 L5 门

- 真实触发形成明确时间窗。
- hold/abstain/unsupported 的目标 L5 数量为 0。
- 默认时间窗不能作为兜底。

### G5 冻结与生产隔离门

- 相同输入与输入顺序置换后冻结制品一致。
- 默认 registry、pipeline、production YAML、公共 schema 和报告入口零变化。
- 杨派专属写区零变化。

### G6 生产候选门

G0-G5 通过后仍保持 staged。只有独立冻结样本提供误报、漏报、校准与适用性后验，且另行获批，才可在“保持专用 / staged 并行 / 替换旧规则”中作生产决策。

---

## 10. 测试设计

### 10.1 原子触发测试

每种冲、刑、穿、合、伏吟、大运 fallback 至少包括：

- positive
- negative
- exclusion
- boundary

### 10.2 状态机测试

- 上游事件成立 + 完整事实 + 有效触发 → timing-ready/emit。
- 事件成立但无有效触发 → 无 L5。
- 有相关触发但时间闭包不足 → hold，无 L5。
- 缺上游事件 → abstain。
- 缺大运、缺流年、非法干支 → abstain + remediation。
- 未知任务 → unsupported。

### 10.3 去重与决定性

- pair 顺序反转不改变家族。
- 跨集合重复不增加家族数。
- 多字段同一家族只计一次。
- 输入列表/集合顺序置换后结果与冻结制品一致。
- 相同输入重跑字节等价。

### 10.4 adapter 与 evidence

- emit 成功生成 L5。
- hold/abstain/unsupported 进入 adapter 均失败。
- 每个 evidence ref 可解析到事实、特征、规则来源或证据对象。
- falsifier 仅用于已输出 timing；abstain 使用 remediation。

### 10.5 多候选窗口

多个候选年份必须按显式优先级或规则排序选窗，不依赖输入列表位置。并列时必须使用稳定 tie-breaker。

### 10.6 旁路与隔离

- staged assembler 不进入默认 registry。
- 默认 `run_pipeline()` 签名与行为摘要不变。
- production YAML 字节级不变。
- 报告入口不变。
- 杨派专属路径不变。
- 合成门禁不读取历史报告、反馈、标签或冻结结果。

---

## 11. 最小制品集

每个可执行切片至少包含：

1. 来源定位：path、excerpt、line/anchor、版本或 hash。
2. 外置规则：身份、任务、条件、排除、反条件、结论模板、falsifier、置信依据。
3. 事实适配器。
4. 纯判别器。
5. 不可变局部结果。
6. emit-only adapter。
7. positive/negative/exclusion/boundary 规则测试。
8. 状态机与旁路测试。
9. 冻结制品与确定性证明。
10. 离线评估制品。
11. 生产隔离证明。

缺少任一核心制品，不计入 `executable_slice_count`。

---

## 12. 多 agent 分工与写区

### 12.1 杨派 agent

继续独占其现有计划声明的杨派实现与测试路径。本设计和任派 agent 不读取其未提交工作区状态，不修改其文件，不代替其更新共享状态。

### 12.2 协议 agent

只写跨派规范与路线图，维护两套计数、状态分层、最小制品和 G0-G6 定义。

### 12.3 任派 agent

只写：

- 任派职业变化应期切片实现。
- 任派专用 staged assembler。
- `tests/ren_timing/` 专项测试。
- 任派专用规则或来源映射制品。

不得修改公共 schema、默认 registry、正式 pipeline、杨派路径或共享机器状态。

### 12.4 测试/审计 agent

只写独立契约测试辅助与审计报告，不修改流派实现。

### 12.5 最终集成 owner

最后串行处理共享护栏、状态文件和文档引用。`META/project-state.json`、`tests/test_project_metadata.py`、`tests/test_production_entrypoints_unchanged.py` 等共享文件只能由最终集成 owner 更新。

### 12.6 合并顺序

1. 合并跨派规格。
2. 等杨派 agent 完成独立工作。
3. 实施并验证任派专用纵切。
4. 由集成 owner 处理共享护栏和状态。
5. 再启动下一流派切片。

---

## 13. 跨流派优先级路线图

### P0 统一计量

落地 `catalog_count` 与 `executable_slice_count` 分账，禁止用目录规模代表判别能力。

### P1 任派职业变化应期

完成第一个非杨派 L5 staged 纵切，验证真实岁运触发、emit-only adapter 与冻结隔离。

### P2 子平体系收敛

先统一已有结构/职业任务与 production 库的身份映射，不全量搬迁 933 条目录规则。子平优先验证 L2→L3，而非复制事件切片状态。

### P3 滴天髓任务蒸馏

从调候与气势条目中选择高判别任务，解决目录条目多、task-scoped 能力少的问题。

### P4 杨派扩展

等待现有杨派 agent 完成婚姻判别并接受独立评审后，再考虑婚期、家庭关系或画像任务。本父任务不触碰其写区。

### P5 高派可计算子集

只切可靠可计算的神煞、健康或旁证子集。不可可靠计算的理论保持 G1/G2，不伪造触发事实。

### P6 段派选择性扩展

以现有 executable rules 为样板补高价值缺口，不追求 legacy 条目全迁移。

---

## 14. 完成定义

本阶段“完成”不等于生产上线。完成条件为：

1. 跨派切片规范获批并落盘。
2. 任派 staged 纵切通过 G0-G5。
3. 首个证伪点成立：无真实触发不得生成 L5。
4. 冻结制品可确定性复现。
5. 默认 registry、pipeline、production YAML、公共 schema 和报告入口零变化。
6. 杨派专属写区零冲突。
7. 形成是否进入 G6 的独立证据包，但不自动晋级。
8. GitHub 同步状态在实施开始与结束时分别核验，不在长期文档硬编码 HEAD。

---

## 15. 验收摘要

该方案的成功标准不是新增多少 YAML 条目，而是证明一个非杨派任务可以遵循统一协议完成：

`明确任务 → 事实闭包 → 原子触发 → 家族去重 → 具名门 → 局部状态 → 统一发布态 → emit-only 目标层适配 → 冻结评估 → 生产隔离`。

任派职业变化应期纵切若能在无触发反例上保持 L5 为 0，并在真实触发正例上产出稳定、可证伪、可追溯的时间窗口，即完成本阶段最关键证明。