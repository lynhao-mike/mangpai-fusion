# PI-190-R2 · G1 独立验收裁决

## 1. 裁决摘要

- **验收实例：** PI-190-R2
- **验收对象：** G1 当前架构盘点及 PI-110、PI-120、PI-130 三份持久化审计交付物
- **裁决：`PASS`**
- **裁决含义：** 三份交付物对当前生产默认链、旁路能力、显式 staged/preprod 能力、关键数据模型、持久化边界及已知缺口的盘点完整、准确且可复核，足以关闭 G1 的“现状盘点”工作，并允许在完成相应治理登记后进入 G2 设计。
- **G1 内容阻断项：** 无。
- **非本裁决含义：** 本次 `PASS` 不表示 F01–F12 已实现，不表示现有运行轨道已经统一，也不表示任何 G2/G5 设计或生产改造已获批准。

## 2. 独立性声明与验收口径

本裁决由 PI-190-R2 基于治理标准、三份当前交付物及其直接源码／契约证据独立形成。历史裁决文件仅用于识别治理背景和待核事实，不继承其结论，也不以历史结论替代本次证据抽查。

本次采用严格 fail-closed 口径：

1. 交付物缺少 G1 必需覆盖面、关键结论不可由源码／契约复核，或三份交付物之间存在无法解释的实质矛盾时，裁决必须为 `BLOCKED`。
2. F01–F12 当前未实现、未接线，或统一输入／决策／冲突／反馈协议尚不存在，本身不构成 G1 阻断；G1 的目标是准确盘点现状，而不是提前完成 G2 实现。
3. 只有当“未实现”状态缺乏证据、被错误表述为已实现，或未被登记为后续设计输入时，才构成 G1 缺陷。
4. production-default、production 附挂旁路、显式 staged 和 opt-in preprod 必须分账；任何旁路能力均不得冒充生产默认能力。

验收治理基线来自 [`plans/production-implementation-control.md`](production-implementation-control.md)；历史校准阻断背景来自 [`plans/production-implementation-g1-calibration-blocker.md`](production-implementation-g1-calibration-blocker.md)。本次直接验收的三份交付物为：

- [`plans/production-implementation-pi-110-input-pipeline-audit.md`](production-implementation-pi-110-input-pipeline-audit.md)
- [`plans/production-implementation-pi-120-findings-decision-conflict-audit.md`](production-implementation-pi-120-findings-decision-conflict-audit.md)
- [`plans/production-implementation-pi-130-report-statement-feedback-audit.md`](production-implementation-pi-130-report-statement-feedback-audit.md)

## 3. G1 验收矩阵

| 验收域 | 必须证明的事实 | 独立抽查结果 | 判定 |
|---|---|---|---|
| 治理范围 | G1 是当前架构盘点，产物应包含现状图、可复用组件、缺口、不可触碰边界和源码证据 | 三份审计按输入／管线、findings／decision／conflict、报告／statement／feedback 分域覆盖，并分别登记复用点、缺口、边界和证据索引 | PASS |
| 生产默认入口 | production-default 的真实入口和默认参数必须可定位 | [`ProductionAnalysisService._run_existing_job()`](../engine/application/production_service.py:141) 调用 [`run_pipeline_e2e()`](../engine/application/pipeline_runner.py:174)，默认关闭 self-iteration；v6 preprod 由显式请求开关附加执行 | PASS |
| 输入与管线 | 输入解析、字段传递、候选消费、D1–D4、整合和 findings 落盘必须形成可复核链 | PI-110 对默认 adapters、preflight、两层 ParsedInput、[`run_pipeline()`](../engine/application/pipeline_runner.py:33)、[`integrate()`](../engine/application/integration.py:171) 和 [`_save_findings()`](../engine/infrastructure/findings_repository.py:11) 的链路描述与源码一致 | PASS |
| 输入字段边界 | `questions`、`known_facts` 和时间范围不得被夸大为已统一消费 | [`_extract_candidates()`](../engine/application/candidates.py:7) 实际只遍历带年份且带 event/content 的 known facts；production 请求未提供统一 start/end year 协议。审计准确登记传递与消费的差异 | PASS |
| findings 模型 | production-default 的 findings 类型和落盘位置必须明确 | D1–D4 与 `AnalysisOutput` 由默认链生成并写入 case findings；审计未把旁路模型混入默认 schema | PASS |
| 冲突生产状态 | schema 存在不等于 production-default 已自动产出冲突 | [`integrate()`](../engine/application/integration.py:171) 当前固定返回空 conflicts，并明确由人工／报告层登记、自动语义仲裁另走独立模型；PI-120 正确解释为空 producer，而非“确认无冲突” | PASS |
| 决策与五动作 | 当前是否存在统一 OUTPUT／CONDITIONAL／ASK／ABSTAIN／HUMAN_REVIEW 协议必须准确说明 | PI-120 区分 production、parallel-domain、staged L6、v5/v6 preprod 的局部模型，并确认尚无统一五动作枚举、envelope、producer/consumer contract，尤其没有统一决策语义 ASK | PASS |
| 旁路冲突与裁判 | 可运行的局部能力必须被确认，但不得冒充 production-default | [`run_parallel_domain_analysis()`](../engine/application/parallel_domain_runner.py:86) 确有冲突检测、惩罚、裁判和共识链；PI-120 将其限定为 parallel-domain 局部协议 | PASS |
| staged 分账 | 显式 staged 能力必须保持隔离、不落盘且有独立异常边界 | [`run_parallel()`](../engine/application/staged_parallel_runner.py:124) 显式并跑两条路径、不落盘；[`run_parallel_with_arbitration()`](../engine/application/staged_parallel_runner.py:185) 使用 staged conflict rules。审计边界准确 | PASS |
| preprod 分账 | v5/v6 preprod 必须是 opt-in，且其 DTO/artifacts 不得冒充 production-default | [`render_v6_preprod_case()`](../engine/v5/preprod.py:215) 是默认 pipeline 后的显式附加链，顺序写入自己的多项 artifacts；chart DTO 未统一承载 questions/known facts | PASS |
| 报告渲染 | 标准 renderer、lint 和异常边界必须可定位 | [`render_from_output()`](../tools/render_report.py:188) 调用标准渲染链；[`render()`](../tools/render_report.py:2025) 在返回 Markdown 前执行出口 lint，ERROR 会抛出 guardrail error | PASS |
| statement artifacts | index 与 records 的职责、生成顺序和失败语义必须分清 | [`_build_statement_index()`](../tools/render_report.py:1779) 保存报告追踪信息和多 rule IDs；[`build_statement_records_envelope()`](../engine/statement_runtime.py:70) 生成学习桥 records，当前每条 statement 仅取第一条有效 evidence rule 作为 anchor。报告先完成，artifact 顺序写且失败降级为 warning | PASS |
| production artifact gate | hard gate 与反馈学习事实源是否对齐必须准确披露 | [`REQUIRED_CASE_ARTIFACTS`](../engine/application/artifact_inventory.py:26) 要求 index 和 rule map，但不要求 records；PI-130 正确登记其与 records-only 学习桥的错位 | PASS |
| feedback fanout | legacy index 是否能解锁学习、records 是否为当前事实源必须有代码和测试支持 | [`fanout_to_rules()`](../tools/feedback_ingest.py:346) 消费 statement records 的单 rule anchor；[`test_h3_standard_list_schema_without_rule_ids_is_blocked_from_learning()`](../tests/v1_3_acceptance/test_h3_feedback_parsing.py:160) 与 [`test_h3_statement_records_enable_fanout()`](../tests/v1_3_acceptance/test_h3_feedback_parsing.py:184) 分别覆盖阻断与解锁行为 | PASS |
| 报告到反馈事务边界 | 不得将分步流程表述为单次提交内的原子闭环 | production service 默认 `do_self_iter=False`；renderer artifacts 与 preprod artifacts 均为顺序写，缺少整体事务回滚。PI-130 对非原子、非同 submit 事务的描述准确 | PASS |
| F01–F12 | 必须区分正式契约／声明性数据存在与运行时 consumer 存在 | [`mapping/real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml) 冻结 F01–F12 和五动作词表，并禁止可执行逻辑；[`engine/contracts/12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md) 明确生产实现需另行设计、评审和测试。对 engine/tools Python 的受限静态抽查未定位到完整 mapping 文件或 F01–F12 ID consumer | PASS |
| 缺口归属 | 已知未实现项必须成为 G2 输入，而非被遗漏或伪装为 G1 完成能力 | 三份审计明确登记统一请求上下文、五动作、冲突生产、统一 envelope、statement 原子性、artifact gate 对齐和 F01–F12 runtime consumer 等缺口，且未宣称其已实现 | PASS |
| 跨交付物一致性 | 三份审计不得在默认链、旁路边界或状态判断上互相矛盾 | PI-110、PI-120、PI-130 对 production-default、parallel-domain、staged 和 preprod 的角色划分一致；输入、决策和反馈端的缺口能够首尾对应 | PASS |

**矩阵结论：** 未发现触发 fail-closed 的覆盖缺失、不可复核结论或实质矛盾。

## 4. 运行轨道分账裁决

| 轨道 | 实际入口／核心模型 | 当前能力 | 不得推导出的结论 | 判定 |
|---|---|---|---|---|
| production-default | [`ProductionAnalysisService._run_existing_job()`](../engine/application/production_service.py:141) → [`run_pipeline_e2e()`](../engine/application/pipeline_runner.py:174) → [`run_pipeline()`](../engine/application/pipeline_runner.py:33) → [`integrate()`](../engine/application/integration.py:171) | preflight、D1–D4、AnalysisOutput、findings、标准报告 | 不得称其已有自动 conflict producer、统一五动作、F01–F12 consumer 或自动反馈事务 | 清晰 |
| production 附挂 parallel-domain | [`run_parallel_domain_analysis()`](../engine/application/parallel_domain_runner.py:86) | 多专家 reading、局部 conflict detection、adjudication、consensus | 不得用其局部冲突模型证明 production `AnalysisOutput.conflicts` 已接线 | 清晰 |
| staged L6 | [`run_parallel()`](../engine/application/staged_parallel_runner.py:124)、[`run_parallel_with_arbitration()`](../engine/application/staged_parallel_runner.py:185) | 显式 legacy/Claim 并跑、独立失败边界、staged arbitration | 不得称为默认生产链，不得假定落盘或上下文事实注入 | 清晰 |
| v5/v6 preprod | [`render_v6_preprod_case()`](../engine/v5/preprod.py:215) | opt-in chart DTO、run/decision/report/attachment/manifest artifacts | 不得称为默认输入协议、默认报告或 production findings/statement bridge | 清晰 |

三份交付物没有以“代码存在”替代“生产默认已接线”的证明，也没有把 staged/preprod 的能力合并计入 production-default，因此满足严格分账要求。

## 5. 关键证据抽查结论

### 5.1 输入、管线与持久化

1. production 请求 DTO 只提供输入路径、渲染、强制、模板和 preprod opt-in 等参数；未形成统一 questions/known facts/time-window 请求协议，见 [`SubmitAnalysisRequest`](../engine/application/production_service.py:40)。
2. 默认端到端链在 [`run_pipeline_e2e()`](../engine/application/pipeline_runner.py:174) 内完成 preflight、pipeline、可选 render、可选 self-iteration 和 findings 保存；production service 明确把 self-iteration 关闭。
3. [`_extract_candidates()`](../engine/application/candidates.py:7) 的 docstring 提到 questions，但实现只消费 known facts 的受限子集；PI-110 将其识别为注释／实现漂移，而未据注释夸大能力。
4. [`_save_findings()`](../engine/infrastructure/findings_repository.py:11) 明确写入 D1–D4 和 `analysis_output.json`，使 production findings 的持久化位置可复核。

### 5.2 findings、decision 与 conflict

1. [`integrate()`](../engine/application/integration.py:171) 构造 production `AnalysisOutput`，但 conflicts 固定为空；该事实与 PI-120 的“schema 存在、producer 未接线”判断一致。
2. [`run_parallel_domain_analysis()`](../engine/application/parallel_domain_runner.py:86) 的局部 conflict/adjudication 链真实存在；交付物没有将其偷换为 production integration 能力。
3. staged L6 和 v5/v6 preprod 分别拥有自己的 decision/arbitration 模型，证明当前是多协议并存，而非统一五动作已形成。
4. 当前局部代码中出现的 abstain 或人工裁判语义，不足以构成统一五动作 envelope；PI-120 对“存在局部行为”和“存在统一协议”作了正确区分。

### 5.3 报告、statement 与 feedback

1. 标准报告先渲染并 lint，随后才顺序写 statement records 和 index；artifact 写入异常仅 warning，见 [`render_from_output()`](../tools/render_report.py:188)。因此报告成功不等于反馈桥 artifacts 作为一个事务整体成功。
2. [`build_statement_records_envelope()`](../engine/statement_runtime.py:70) 当前为每个 statement 选择第一条有效 evidence rule 作为唯一 runtime anchor；[`_build_statement_index()`](../tools/render_report.py:1779) 则可保存多个 rule IDs。PI-130 准确区分两者职责。
3. [`fanout_to_rules()`](../tools/feedback_ingest.py:346) 的当前学习桥以 records 为事实源；legacy index 不再单独解锁规则学习。测试证据与代码语义一致。
4. [`collect_analysis_artifacts()`](../engine/application/artifact_inventory.py:40) 所在 production gate 未把 records 纳入 required artifacts，构成已登记的 gate/learning-source 错位，而不是被遗漏的 G1 证据。
5. [`render_v6_preprod_case()`](../engine/v5/preprod.py:215) 顺序写入多个 preprod artifacts，且没有整体原子提交；PI-130 未将 attachment 存在表述为 production feedback learning 已自动接通。

### 5.4 F01–F12

1. [`mapping/real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml) 已冻结 F01–F12、动作词表和恢复纪律，并明确 `executable_logic_allowed: false`。
2. [`engine/contracts/12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md) 明确要求现实／理论、状态／事件、根源／时序和精度／覆盖分账，并要求缺证时弃权或人工复核。
3. 对 [`engine/`](../engine/) 与 [`tools/`](../tools/) 下 Python 源码进行的受限静态检索未发现完整 mapping 文件名或 F01–F12 ID 的运行时消费引用。
4. 因此，最精确的现状表述是：**契约与声明性数据已冻结，但尚未形成可定位的 production runtime consumer 链。** 三份审计均保持了这一表述，没有把 YAML 直接解释为可执行逻辑。

## 6. 三份交付物的一致性检查

| 对照关系 | 一致性结果 |
|---|---|
| PI-110 输入边界 vs PI-120 决策输入 | 一致：当前请求上下文未统一，不能假定后续 decision 已获得 questions、known facts 和统一时间范围 |
| PI-120 冲突模型 vs PI-130 报告消费 | 一致：多套局部 schema 并存，renderer 可展示局部结果不等于 production-default 已有统一 conflict/decision envelope |
| PI-110 默认链 vs PI-130 反馈闭环 | 一致：默认 submit 关闭 self-iteration，报告生成与后续 feedback ingest 分步执行 |
| PI-120 五动作缺口 vs F01–F12 契约词表 | 一致：词表被冻结不等于运行时动作协议已实现 |
| PI-130 records-only bridge vs artifact hard gate | 一致地披露错位：学习事实源是 records，而 production required artifacts 未要求 records |
| 三份审计对 staged/preprod 的定位 | 一致：均视为显式、局部或 opt-in 能力，不计入 production-default 已实现能力 |

未发现三份交付物之间的实质矛盾。个别源码 docstring 或历史功能注释与当前实现存在漂移，但审计文件已经识别并按实现事实裁决，因此不构成交付物矛盾。

[`plans/production-implementation-control.md`](production-implementation-control.md) 仍保留此前待补交付物／待验收状态，属于治理登记尚未由获授权动作更新；它不推翻当前三份交付物已经存在及本次独立证据核验结果。本任务受写入范围限制，不修改总控，也不把总控登记动作伪装为本次已经完成。

## 7. G2 设计输入与 G1 阻断分账

下列事项均已被三份审计准确识别，属于后续 G2 需要处理的设计输入，而不是 G1 现状盘点阻断：

- 统一请求上下文及 questions、known facts、时间范围的消费协议；
- production findings、decision、conflict 的统一 envelope 和 producer/consumer 边界；
- OUTPUT、CONDITIONAL、ASK、ABSTAIN、HUMAN_REVIEW 五动作的统一运行时语义；
- parallel-domain、staged L6、v5/v6 preprod 与 production-default 之间的显式适配边界；
- production 自动 conflict producer 及“空 conflicts”的可信语义；
- 报告、statement records/index 和 required artifacts 的提交与失败语义；
- production artifact hard gate 与 records-only feedback learning source 的对齐；
- statement 多证据关系与当前单 anchor fanout 的处理边界；
- 报告生成、反馈摄入和学习更新之间的事务／幂等边界；
- F01–F12 声明性契约的合规 runtime consumer，且不得把 YAML 直接翻译为未经设计评审的 if/else 算法。

以上清单只确认“设计问题已被完整识别”，不在本裁决中选择方案、定义接口或授权实现。

## 8. 阻断项

### 8.1 G1 内容阻断项

**无。**

未发现以下任一 fail-closed 条件：

- G1 必需领域缺少持久化盘点；
- 核心结论无法定位到源码或正式契约；
- staged/preprod 被冒充为 production-default；
- F01–F12 被错误宣称为已实现；
- 三份交付物存在无法解释的实质矛盾；
- 关键缺口未登记，导致 G2 缺少必要输入。

### 8.2 非内容治理待办

总控中的 G1 状态登记尚未在本任务内更新。该事项是本次权限边界外的治理动作，不改变 PI-190-R2 对 G1 盘点质量的 `PASS`，但在正式启动 G2 前仍应由获授权流程完成状态同步和入口确认。

## 9. 允许与禁止的下一步

### 9.1 允许

1. 将本裁决作为 G1 独立验收证据，提交给有权限的治理动作更新总控状态。
2. 在总控完成状态同步和入口授权后，进入 G2 的设计阶段。
3. G2 以第 7 节列出的现状缺口为输入，重新核对 production-default 与各旁路边界。
4. 后续设计继续以正式契约和声明性 mapping 为事实源，并保持不可执行数据与运行算法分离。

### 9.2 禁止

1. 不得将本次 `PASS` 解读为 G2 或 G5 已完成、已设计或已获实现授权。
2. 不得在总控尚未由获授权动作同步前，借本文件擅自修改生产入口或切换默认轨道。
3. 不得把 parallel-domain、staged L6 或 v5/v6 preprod 的局部能力宣称为 production-default 已接线。
4. 不得把空 conflicts 解释为系统已证明不存在冲突。
5. 不得把 F01–F12 YAML 或机器附录直接翻译成可执行 if/else 逻辑。
6. 不得绕过 statement records 的当前学习桥事实，使用 legacy index 启发式解锁 Dynamic Confidence fanout。
7. 不得把本裁决扩展为对未运行测试的通过声明。

## 10. 自检

- [x] 独立读取治理基线、历史校准背景和三份 G1 交付物。
- [x] 抽查 production-default、parallel-domain、staged L6、v5/v6 preprod 的关键入口和模型边界。
- [x] 覆盖输入／管线、findings／decision／conflict、报告／statement／feedback 三个审计域。
- [x] 核验 F01–F12 为“契约／数据存在，运行时消费链未定位”的状态。
- [x] 区分 G1 证据阻断与 G2 设计输入，未以“尚未实现”错误否决现状盘点。
- [x] 未继承历史 PI-190/PI-195 的裁决结论。
- [x] 未递归委派。
- [x] 未设计 G2 或 G5。
- [x] 未修改总控、handoff、生产代码、测试、契约、mapping 或其他文件。
- [x] 本次静态验收未运行测试，文档未声称测试通过。
- [x] 本次唯一目标写入为 [`plans/production-implementation-pi-190-r2-g1-acceptance.md`](production-implementation-pi-190-r2-g1-acceptance.md)。

## 11. 最终裁决

**`PASS`** — G1 架构盘点完整、准确、边界清晰且证据可复核；无 G1 内容阻断项。允许在获授权治理动作完成总控状态同步后进入 G2 设计，但本裁决本身不包含 G2/G5 设计或生产实现授权。
