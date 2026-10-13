# P0 chart-only 命局推断入口源码审计

审计日期：2026-10-07。范围：`engine/claims`、`engine/v5/domain_slices`、相关派别 runner 及直接依赖、契约。按 AGENTS 读取入口文档与项目状态导航；未打开或搜索 cases、reports、predictions、META 真实评估制品或 theory 案例证据，未读取目标命盘现实结果，也未执行会加载这些数据的 pipeline、runner 或测试。本次只新增本文；未修改规则、权重、taxonomy 或生产行为。以下是静态代码结论，不是准确性验证；`engine/asof` 接入设计留给主任务。

最小值得 graft 的现有入口是 **`ziping_runner.generate_claims(chart, features, task)` 的 `structure.overview` 分支**，再并列调用 **`ditiansui_runner.generate_claims()` 的同一任务**。前者已有旺衰与食伤官杀结构判断，后者已有调候极端与五行集中判断；都能从盘面生成非占位 `structure_claim`，并保留事实、特征、规则引用及弃权边界。应保留原始 Claim 列表。若目标还要求正格/从格、用神和病药，已有独立 V5 runner 可复用，但不能把它与任务型入口视为等价实现。

## 入口与输入边界

共同输入：事实账本 [ChartFactLedger](../engine/decision/models.py#L43) → [build_chart_feature_vector](../engine/features/chart_feature_vector.py#L170) → `BlindTask(task_id="structure.overview", ...)`。特征构建至少要求月、日柱；完整四柱为 `full`，仅缺时柱为 `no_hour`，其他残缺为 `partial`。原局结构计算不需要现实经历或岁运；性别、出生时间和司令还参与盘面身份 hash（[chart_feature_vector.py:67](../engine/features/chart_feature_vector.py#L67)）。

下表“无”指已审计函数不消费命主的 `known_facts`、`feedback` 或现实自由文本；生成的说明文字、规则结论模板不等于读取用户现实叙述。它不表示任意传入字典都经过递归防泄漏校验，也不表示导入整套注册表没有规则文件 IO。

| 既有入口／精确定位 | 输入与读取边界 | 实际输出、现实标签与追溯 |
|---|---|---|
| [子平 generate_claims:681](../engine/v5/ziping_runner.py#L681) | 账本、CFV、task；现实输入无；结构分支要求 `full` | `structure.overview` 最多两条：身强/身弱、食伤官杀并见；不直接生成人生结果标签。规则 `ZIPING-STRENGTH-V1`、`ZIPING-OUTPUT-OFFICIAL-V1`，带 fact/feature refs、快照、falsifier，并调用证据校验。另有晚婚、职业变动事件分支，不能混作结构。 |
| [滴天髓 generate_claims:327](../engine/v5/ditiansui_runner.py#L327) | 同上；现实输入无；`partial` 弃权，`no_hour` 可降置信输出 | 气候极端优先，否则五行集中；最多一条结构命题，不产生现实标签。规则 `DITIANSUI-STRUCTURE-CLIMATE-EXTREME-V1` / `DITIANSUI-STRUCTURE-QI-CONCENTRATION-V1`，有月柱/特征引用、快照与校验；条件不满足返回空列表。 |
| [子平 run_ziping_independent:417](../engine/v5/ziping_runner.py#L417) | `chart` 字典及 case_id；消费 `pillars`，部分计算兼容单独干支字段；现实输入无 | 实际输出四条 V5 结构命题：旺衰、格局用神、格局大类、病药（入口 docstring 仍称两条）。有 L3/L5 方向 metadata；不输出就业/创业等现实标签。证据仅源码路径、说明与 `chart:root`，`rule_ids=[]`（[构造器:369](../engine/v5/ziping_runner.py#L369)）。 |
| [滴天髓 run_ditiansui_independent:250](../engine/v5/ditiansui_runner.py#L250) | chart 字典、case_id；四柱、月支、日干；现实输入无 | 两条 V5 结构命题：气势/流通、寒暖燥湿及补救方向。不直接输出现实标签；同样只有源码与根节点引用、空规则 ID（[构造器:204](../engine/v5/ditiansui_runner.py#L204)）。 |
| [段派 generate_claims:264](../engine/v5/duan_runner.py#L264) | 账本、CFV、task；现实输入无；事件要求完整盘面，timing 另需岁运；导入时加载规则 YAML | 输出事件或 timing，**没有 structure.overview 分支**。职业路径直接算出 `employment / entrepreneurship / mixed`（[174](../engine/v5/duan_runner.py#L174)），还有职业变动、债务、离婚/再婚任务。证据有 rule_id、盘面/特征 refs、做功摘要；底层结构可另复用，见下文。 |
| [高派 generate_claims:157](../engine/v5/gao_runner.py#L157) | 账本、CFV、task；现实输入无；导入时加载规则 YAML | 名称虽称“结构旁证”，事件规则类型仍为 `event_claim`；覆盖债务、健康风险及 timing。健康分支直接给 `moderate / high`（[119](../engine/v5/gao_runner.py#L119)）。证据有规则与特征引用；不是现成通用结构命题入口。 |
| [杨派 generate_claims:46](../engine/v5/yang_runner.py#L46) | 性别、完整盘面、CFV、task；现实输入无；导入时加载规则 YAML | 仅离婚/再婚风险事件；性别不明或条件不足为空。规则、性别/日柱/特征引用及信号快照可追溯；不输出结构 Claim。 |
| [任派 generate_claims:177](../engine/v5/ren_runner.py#L177) | 盘面、CFV、流年/大运、task；现实输入无 | 多数任务是带现实事件名称的年度 timing；职业变动另可生成二元 `event_claim`（[121](../engine/v5/ren_runner.py#L121)）。非结构入口；有岁运/原柱引用及代码内规则 ID。段、高 timing 分别见 [duan_timing:285](../engine/v5/duan_timing.py#L285)、[gao_timing:259](../engine/v5/gao_timing.py#L259)。 |

段派已有值得后续 graft 的结构底座：[chart_ledger_to_bazi:43](../engine/v5/duan_runner.py#L43) → [evaluate_tiyong:99](../engine/energy/tiyong.py#L99) / [evaluate_zuogong:522](../engine/energy/zuogong.py#L522)。[内部 _duan_structure:57](../engine/v5/duan_runner.py#L57) 已提取体用数量、有效路径、最强路径分值与类型；它目前是事件规则的中间量，**尚未封装成独立 structure_claim**，不能把该中间量直接称为已完成的段派结构裁决。

证据追溯有两种强度：[validate_claim_evidence:32](../engine/claims/validation.py#L32) 校验盘面身份及引用存在，不校验规则论证真伪、证据完整因果覆盖或现实正确性。段/高/杨通过 [rule_loader:15](../engine/claims/rule_loader.py#L15) 读取固定 `theory/production/claim-rules-v1.yaml`；[source_refs 解析:174](../engine/claims/rule_loader.py#L174) 检查来源路径存在及定位字段，但不核验原文是否支持结论，Claim 本身也不携带完整 source_refs。本次未打开该 YAML 或其来源材料，故仅确认源码支持的追溯机制。

## 编排复用与占位边界

| 位置 | 源码事实及接入含义 |
|---|---|
| [claims/runner_registry:51](../engine/claims/runner_registry.py#L51)；[orchestrator:70](../engine/claims/orchestrator.py#L70) | `structure.overview` 只注册子平、滴天髓；默认 schools 却是 `("ziping", "ren")`，不会自动运行滴天髓。查无 `(school, task)` 或抛 `TaskUnsupported` 时返回 `unsupported`；已覆盖但缺事实/无触发则 `abstain`（[92](../engine/claims/orchestrator.py#L92)）。其他四源的该结构任务属于未实现能力，不是负向结构结论。 |
| [orchestrator:124](../engine/claims/orchestrator.py#L124)；[blind_adapter:64](../engine/claims/blind_adapter.py#L64) | 多 Claim 按 claim_id 最小值只留一条，再转换为 BlindPrediction；这会丢掉子平的另一条结构命题，且不保留完整特征/规则证据对象。该入口适合既定盲评输出，不能直接承担完整结构裁决集合；结构也会被放入 `event_label` 字段，字段名不能解释为现实标签。 |
| [domain_slices/contract:72](../engine/v5/domain_slices/contract.py#L72)；[career/context_to_chart_ledger:61](../engine/v5/domain_slices/career/__init__.py#L61) | context 额外要求出生信息、当前大运及恰好三个未来年份；转换器只构造盘面、岁运账本。纯四柱结构接入无需先绕出生排盘与未来三年上下文。 |
| [career/run_legacy_domain_slice:166](../engine/v5/domain_slices/career/__init__.py#L166)；[adapt_legacy_claim:95](../engine/v5/domain_slices/career/__init__.py#L95) | 切片保留每任务全部 Claim，已有 Claim→V5Claim 适配，携带规则/节点 refs 与快照。但只覆盖 school/domain，未增加领域专属推断。子平事业还调用职业变动事件；滴天髓事业只调结构任务（[208](../engine/v5/domain_slices/career/__init__.py#L208)）。 |
| [wealth:10](../engine/v5/domain_slices/wealth/__init__.py#L10)；[marriage:21](../engine/v5/domain_slices/marriage/__init__.py#L21) | 子平财富、滴天髓财富/婚姻复用同一个 `structure.overview`；只是结构背景换 domain，不能计为独立财富/婚姻规律或同题竞争。子平婚姻是晚婚事件（[marriage:10](../engine/v5/domain_slices/marriage/__init__.py#L10)）。 |
| [build_domain_registry:21](../engine/v5/domain_slices/__init__.py#L21) | 当前生成器表没有杨清娟事业和财富槽位，因此这两格明确 `unsupported`。其他已注册切片也可能运行时 `abstain`。较早 [build_abstain_registry:64](../engine/v5/domain_slices/registry.py#L64) 全部占位；[build_career_registry:264](../engine/v5/domain_slices/career/__init__.py#L264) 的非事业域为 `abstain`，不要当作当前完整注册表。 |
| [domain_slices/orchestrator:57](../engine/v5/domain_slices/orchestrator.py#L57)；[81](../engine/v5/domain_slices/orchestrator.py#L81) | unsupported/abstain 被包装成 `stance=abstain` 的 evidence/timing 占位，异常也转 abstain 并保留 error_type。另一条旧入口 [build_abstain_claims:536](../engine/v5/runner.py#L536) 会生成带 `structure_claim` 类型的子平/滴天髓 stub；故仅按 claim_type 筛选会误收占位。 |

不要把 [build_default_claims:589](../engine/v5/runner.py#L589) 当最小 graft：它拼接独立 runner、生产规则与三派 index 规则；[build_ziping_production_claims:175](../engine/v5/runner.py#L175) 只按 `quantifiable` 选规则、按盘面排序，随后逐条发出支持命题，没有在此处以触发成功过滤；[index loader:386](../engine/v5/runner.py#L386) 还会读取整份 theory 索引。另需注意 [runner_registry:13](../engine/claims/runner_registry.py#L13) 急切导入段/高/杨，触发各模块顶层规则加载；即使只选择结构任务，也不能把“使用注册表”等同“只读盘面内存”。

## 尚未闭合的语义与竞争

1. **结构粒度不足。** 任务型子平只判强弱及十神并见；并见命题明确写“需审查制化与破格”，没有完成制化成败、真从假从、用忌/救应裁决。旺衰条件实际使用生扶差与通根；月令帮扶在此分支仅列入证据/快照（[ziping:697](../engine/v5/ziping_runner.py#L697)）。滴天髓的五行集中也不等于已证明流通或补救成立。不能从这些结构直接推出学历、职业身份、财富等级。
2. **两套子平/滴天髓计算口径并存。** 独立 runner 的轻量权重、字位统计、固定用神映射，与 CFV 分支不同；并用不能计为独立学派复核。独立 runner 对缺失信息仍可能输出 `support` 的“中和/正格/基本平衡”等默认文案（[ziping:91](../engine/v5/ziping_runner.py#L91)、[276](../engine/v5/ziping_runner.py#L276)、[ditiansui:185](../engine/v5/ditiansui_runner.py#L185)），须与有依据的判断区分。
3. **跨派不是同题竞争。** 现有子平强弱、滴天髓气候/集中通常是不同维度，两者均输出 `support`；task 同为 `structure.overview` 不代表互为可比较候选。尚缺明确的同题语义、对立命题与反证关系。领域适配 ID 还未含 public_domain，且未继承原始 claim_id（[career:121](../engine/v5/domain_slices/career/__init__.py#L121)），同一结构换域可能复用 ID；跨域重复不能增加证据独立性。
4. **既有 V5 仲裁不能补足上述竞争。** [arbitrate_claims:904](../engine/v5/runner.py#L904) 以“结构学派或结构类型”收集命题，仍统计 support/oppose；[verdict:841](../engine/v5/runner.py#L841) 取最高置信文本。不同命题同为 support 不代表互相证成；高派事件/timing 也可能因 school 身份进入结构集合。L3/L5 方向约束另依赖独立 runner 的 metadata（[727](../engine/v5/runner.py#L727)），任务型结构 Claim 并未提供同等语义。
5. **证据有引用，不等于有完整证明。** 当前代码内规则 ID 可定位实现，但不自动绑定经核验理论出处；根节点证据更不能冒充逐事实推导。CFV 与输入的身份校验也不是对所有外部传入特征值的重算等值校验。上述缺口应显式保留，不能用现有置信常数遮盖。

推荐交给主任务的最小复用集合：`ChartFactLedger`、`build_chart_feature_vector`、子平/滴天髓两个任务型 `generate_claims`，以及确需 V5 类型时的现有适配逻辑。保留“未支持／条件不足／有效结构命题”的区别；需要更深格局或做功时，复用上述已有独立计算函数并明确证据缺口。本审计不提出 as-of 会话或接入接口设计。

契约边界：[10-ziping-fusion-v5:71](../engine/contracts/10-ziping-fusion-v5.md#L71) 明确命题置信度不等于事件概率；[结构与事件语义:83](../engine/contracts/10-ziping-fusion-v5.md#L83) 分开定义；[21-high-risk-domain-claims-v1:5](../engine/contracts/21-high-risk-domain-claims-v1.md#L5) 明确工程证据门禁不是现实准确率验证。本文未产生盲测成绩、规则晋级意见或生产可用性背书。
