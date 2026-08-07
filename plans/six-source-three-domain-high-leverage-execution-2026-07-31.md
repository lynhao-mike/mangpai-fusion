# 六源三领域五项高杠杆任务实施计划

**目标：** 在不虚构现实准确率、不自动改写生产规则或权重的前提下，依次交付三领域前瞻盲测治理、命理师逐命题报告、十八槽位能力诊断、高风险安全门禁和命题级反馈闭环，使六源三领域引擎从“可运行”进入“可验证、可审计、可安全改进”。

**范围与风险：** 本计划跨越评估制品、报告 ViewModel、批量统计、安全策略和反馈持久化五个模块。最高风险是标签泄漏、把历史回放冒充 prospective、把双轨置信度误称为现实概率、高风险结论证据不足仍外显，以及小样本反馈自动污染生产规则。计划不扩充理论规则、不切换生产默认入口、不建设 HTTP API、不自动修改静态权重、生产规则或历史快照。

**架构/顺序：**

1. 先冻结 prospective cohort 契约和评分协议；后续报告、统计与反馈都绑定同一 run/claim 身份。
2. 在结构化 snapshot 上建立命理师报告 ViewModel；禁止从 Markdown 反推状态。
3. 基于 snapshot 和切片审计建立覆盖诊断；其结果为高风险门禁阈值和后续规则投资提供证据。
4. 在 runner 之后、仲裁和报告之前执行高风险门禁，失败关闭为 abstain，不制造反对命题。
5. 反馈仅绑定不可变 run/claim，产出只读校准候选；任何生产 promotion 继续要求独立人工审批与既有治理入口。

**固定决策：**

- prospective 正式基线要求 30–50 个真正未见案例；仓库内只能交付协议、工具、模板和 not-ready 状态，不能伪造尚未到达的真人样本或完成成绩。
- cohort 必须先冻结预测、后揭示标签；历史案例仅可标记 development replay。
- `production_ready` 在 prospective 门禁通过前保持 false。
- 高风险任务至少包括 `wealth.debt`、`wealth.major_loss_window`、`marriage.divorce_or_remarriage`。
- 任付红仍为 timing-only，不能提升 structure arbitration。
- 命理师报告禁止展示 claim ID、evidence ID、statement ID 和内部推理索引。
- 反馈工具不得修改 `theory/`、静态权重、生产路由或历史 run snapshot。

## 任务 1：三领域 prospective 盲测基线

- **文件：** 新增 `engine/evaluation/domain_prospective.py`；新增 `tools/domain_prospective_cohort.py`；新增 `tests/evaluation/test_domain_prospective.py` 与 `tests/tools/test_domain_prospective_cohort.py`；新增契约文档 `engine/contracts/20-domain-prospective-evaluation-v1.md`；更新 `tools/README.md`、`engine/contracts/00-OVERVIEW.md`。
- **边界：** 复用现有 `DomainAnalysisRequest`、`V5RunSnapshot` 和稳定 hash；intake 只允许出生输入、截止日和任务范围，不允许 feedback、labels、report、known facts；冻结制品 create-only；标签揭示必须引用冻结制品 hash；评分按 domain/task/claim 分账并保留 abstain。
- **实现：** 提供 `intake / freeze / reveal / score / status` 的最小 CLI；定义 cohort manifest、frozen prediction、revealed labels 和 score receipt；严格区分 prospective 与 historical；无真实样本时稳定返回 not-ready 和 production false。
- **验证：** 测试泄漏字段拒绝、重复身份拒绝、冻结后不可覆盖、hash 篡改拒绝、先 reveal 后 freeze 拒绝、少于 30 案 not-ready、每领域指标可重算且 abstain 不被当作命中。
- **完成：** 仓库具备可执行的真人新案采集和冻结协议；没有真实 30–50 案时明确报告 not-ready，不生成虚假准确率结论。

## 任务 2：命理师逐命题报告工作台

- **文件：** 修改 `engine/v5/domain_analysis_report.py`；必要时新增 `engine/v5/domain_report_view.py`；修改 `tools/domain_analysis_cli.py`；更新 `tests/v5/test_domain_analysis_report.py`、`tests/tools/test_domain_analysis_cli.py`。
- **边界：** 新字段先进入结构化 ViewModel；报告只显示学派中文名、领域、判断、证据文本、支持/反对/弃权、置信度、应期、反证条件和风险提示；内部 ID 一律禁显；仍是一份 Markdown 报告。
- **实现：** 按领域生成融合结论、六源逐命题卡、冲突摘要、弃权原因和时间窗；高风险命题突出“需人工复核”，但不把置信度解释为现实概率；保留当前报告 hash 审计。
- **验证：** golden/snapshot 测试覆盖有命题、冲突、abstain、unsupported、timing-only、高风险和内部 ID 禁显；报告继续通过 `output_linter`，篡改审计继续失败关闭。
- **完成：** 命理师能从单份报告追溯每条判断的来源证据、冲突、应期和反证条件，无需读取 JSON 或内部索引。

## 任务 3：十八槽位能力覆盖与弃权诊断

- **文件：** 新增 `engine/v5/domain_capability_metrics.py`；新增 `tools/domain_capability_status.py`；新增 `tests/v5/test_domain_capability_metrics.py` 与 `tests/tools/test_domain_capability_status.py`；更新 `tools/README.md`。
- **边界：** 只读消费一个或多个 `*.run.json`；registration capability 与 runtime coverage 分账；不得写规则、权重或路由；易漂移数字只通过运行时扫描输出，不写入稳定文档。
- **实现：** 输出 JSON/Markdown，按 school/domain/task 聚合 implemented/abstain/unsupported、命题数、证据完整率、冲突率、应期覆盖率、高风险门禁结果和 abstain reason taxonomy；支持 `--check` 校验快照完整性。
- **验证：** 覆盖十八槽位恒等式、重复 run 去重、损坏 hash 拒绝、registration/runtime 不混淆、零分母稳定输出、JSON 与 Markdown 同源。
- **完成：** 可以从真实运行快照明确看出能力缺口和弃权根因，并形成下一批规则建设的可审计优先级输入。

## 任务 4：高风险命题独立安全门禁

- **文件：** 新增 `engine/v5/high_risk_gate.py`；修改 `engine/v5/domain_slices/orchestrator.py` 或仲裁前置编排边界；修改 `engine/v5/domain_analysis_report.py`；新增 `tests/v5/test_high_risk_gate.py` 并补充 orchestrator/report 测试；新增契约 `engine/contracts/21-high-risk-domain-claims-v1.md`。
- **边界：** 门禁在命题生成后、仲裁和报告前运行；失败时将高风险命题降为显式 abstain 并保留审计原因，不生成 oppose；至少要求两个独立结构/事件证据来源，单一 timing 来源不算结构支持；不得提高任何置信度。
- **实现：** 定义高风险任务注册表、独立来源计数、最低证据完整度、保守措辞和强制 falsifier；门禁结果写入 claim/snapshot metadata 供报告和能力扫描读取。
- **验证：** 单源弱信号失败关闭、双源独立证据通过、任付红 timing-only 不提升结构、falsifier 缺失失败、普通任务行为不变、确定性输出。
- **完成：** 债务、重大损失、离婚/再婚等命题没有足够独立证据时不会作为肯定判断进入仲裁和报告。

## 任务 5：命题级结构化反馈与只读校准候选

- **文件：** 新增 `engine/v5/domain_feedback.py`；新增 `tools/domain_feedback.py`；新增 `tests/v5/test_domain_feedback.py` 与 `tests/tools/test_domain_feedback.py`；新增模板 `templates/domain-claim-feedback.json`；更新 `tools/README.md` 和 `META/project-state.json`。
- **边界：** 反馈状态限定为 accepted/rejected/partial/unknown/timing_deviation；必须绑定 run hash、claim ID 和原始 claim hash；反馈文件 create-only；聚合只产生 calibration candidates，不修改生产规则、权重、路由或历史快照。
- **实现：** 提供 `prepare / ingest / status / candidates`；校验目标 claim 存在且未被篡改；按 school/domain/task/claim_type 聚合误差和应期偏差；候选包含证据数、支持/反对计数、风险级别和人工 review 要求。
- **验证：** 孤儿反馈拒绝、错误 run hash 拒绝、重复反馈拒绝、unknown 不计命中、partial 与 timing deviation 独立分账、高风险候选强制人工 review、输出不触碰生产文件。
- **完成：** 每条真实使用反馈都可追溯到冻结命题，并能生成只读差错归因和人工校准候选包。

## 集成、文档与最终证据门禁

- **文件：** 更新 `engine/README.md`、`tools/README.md`、`META/project-state.json`、`tests/test_project_metadata.py`；视需要更新 `STATUS.md`，但不得硬编码易漂移统计。
- **验证顺序：** 每项任务先运行专项测试；每项交付后运行相邻 v5/CLI/metadata 回归；五项完成后运行工具注册表校验、metadata 测试和全仓测试。完成声明必须引用最新命令、退出码和 passed/failed 摘要。
- **状态语义：** 工程门禁通过可标记各能力 landed；prospective 真人样本未达到门槛时准确率基线仍为 not-ready，`production_ready=false`。

## 子任务编排

五项任务存在强顺序依赖，不并行派发。每轮只启动一个边界清晰的 Code 子任务：读取本计划和直接相关文件，测试先行实现该交付，运行专项验证，返回修改文件、测试证据和未决风险。父任务审核成功后再启动下一项。最终另启独立验证/审查子任务检查跨任务契约和全仓回归。

## 风险与回退

- **真实样本不可制造：** 任务 1 的代码和协议完成不等于 cohort 完成；状态保持 not-ready，等待真人新案。
- **schema 漂移：** 新制品均使用独立 schema_version；读取器拒绝未知版本，不原地改写旧快照。
- **报告泄漏：** ViewModel 白名单渲染，出口 linter 和内部 ID 测试双重防线。
- **门禁误伤：** 高风险注册表采用显式白名单，普通任务不受影响；必要时可回退到上一版编排，但不能绕过高风险报告提示。
- **反馈污染：** 反馈与候选存放于独立制品目录；任何自动 production mutation 视为验收失败。
