# 评估数据地基盘点摘要（2026-07-12）

## 判定

**HOLD — 数据地基已形成开发基线，但尚不具备真实盲测能力基线。**

原因不是标签数量不足，而是历史 990 案采用“先有真实经历反馈、后补排盘与生成报告”的 feedback-first 流程。它们可用于开发、错误分类与标注协议验证，不得伪装成预测先行的历史盲测。

## 本轮产物

- 全量正式 case inventory：133 案。
- 原始启发式 audit 分布：development_only 62、not_scorable 31、manual_review 40。
- 合并保守资格策略后的 inventory 分布：development_only 102、not_scorable 31、blind eligible 0。
- 从正式 RF case 中选取 30 案，全部保留为 development_only。
- 结构化低歧义事件标签：30 案，仅在原始事件文本明确含入职、离职、辞职、调动、转行、升职、失业、创业等职业谓词时映射到 career.change_window。
- 每条标签均记录 source、observed_at、confidence_grade、quantifiable、conflict_state、reviewer。
- 标签来源只引用 raw feedback source，不读取系统报告结论。

## 自动化策略

为降低人工成本，首轮只抽取带明确年份的已发生事件窗口；未知不转负例，高风险与画像任务不自动标注。自动 reviewer 标识仅代表规则化抽取器，不冒充人工复核。

## 为什么没有强行跑出 posterior

现有正式 runner 尚不能在不读取历史反馈的前提下，对这批 feedback-first 案例生成符合 task catalog 的独立盲输出。手写输出会把“人的答案”伪装成“引擎能力”，因此本轮不制造冻结预测、不生成虚假 posterior。

## 提高准确度的最小后续路径

1. 对每个新案，在反馈填写前使用 `prospective-intake` 登记，并用 `prepare-blind` 只复制 input、tasks、rule snapshot 到隔离目录。
2. 引擎输出经保守 adapter 转为三态输出；没有显式 task 语义绑定时只允许 abstain/unsupported，不把宽泛领域判断冒充精确事件。
3. 使用现有 baseline CLI 冻结输出；后续反馈只追加 revealed labels，并绑定 frozen hash。
4. 累积到至少 5 个同六维身份样本后首次观察 posterior；少于 5 保持 HOLD。
5. 人工只处理冲突来源、高风险标签和自动映射低置信项；低歧义年份事件自动摄入。
6. 达到 ≥30 个真实 prospective 案例后，才把阶段 03 从数据准备完成提升为真实能力基线完成。

## 2026-07-13 阻断复核

- 全仓 inventory：133 案，blind eligible 为 0。
- `predictions/` 只有 1 个案例候选，且缺初始不可变 hash、同日已有历史反馈，不能保守计入盲测。
- 历史 Top30 与 990 案均为 feedback-first，逐案 provenance 已记录 `feedback_predates_system_prediction`。
- 因此“≥30 真实盲测/前瞻案例”当前无法通过代码或并行任务补造；强行将历史反馈改名为 blind 会构成标签泄漏。
- 已落地可执行采集基础设施：reviewed manifest、evaluation config、GO/HOLD/INVALID validate、freeze 后 bind-labels、prospective intake、blind bundle 白名单隔离、保守 BlindSchoolOutput adapter。
- **阶段状态仍为 HOLD（真实样本采集阻断），不是代码失败。**

## Known Limitations（待有真实样本时修复）

1. `_report()` 出口未绑定 witness 链：当前 report 从 scores `artifact_digest` 验证内部一致性，但 `artifact_digest` 是本地无密钥校验，不能抵御完全替换所有制品后刷新 digest 的攻击。待有真实 prospective 样本时，`_report()` 应重新验证 scores provenance 与 witness registry，而不仅依赖 manifest 内容校验。
2. `render_capability_report()` N_eff 门槛按"全部 posterior < 5"判断；待有 ≥1 posterior 时，应改为每个被发布切片均须达标。
3. score weight 若缺失则静默默认 1.0；有实际输出时应要求精确覆盖 frozen outputs。
4. prospective `blind_candidate` 允许 `has_existing_report=true`；有实际 prospective 样本时应拒绝（已有报告的 case 不能是真正的前瞻盲测）。

## 2026-07-14 历史隔离批次更新

- 输入与反馈改为两个独立文档：先读取并冻结 `cases/shuru-input.md`，冻结后才读取 `cases/fankui-feedback.md`。
- 输入共 65 节；发现 1 组重复命盘，保留资料更完整者后得到 64 个独立案例。
- 使用完整 19 项任务目录、2 个已接入流派冻结 2432 个三态输出；freeze hash 已验证，冻结制品不含来源 URL、反馈文本或报告文本。
- 从冻结后揭示的反馈中保守抽取 66 条低歧义标签，覆盖 39 个独立案例；每条均含 source、observed_at、confidence_grade、quantifiable、conflict_state、reviewer。
- 39 份逐案 `school-capability-labels.json` 已归档；reviewed manifest 已通过严格 schema 校验。
- 能力覆盖为 claim 58、abstain 262、unsupported 2112。20 个六维 posterior 切片均为覆盖切片，最大 N_eff=0；当前没有可概率评分 claim。
- 第一份历史隔离能力基线已生成，门禁结论仍为 **HOLD**。本轮完成了数据与评估全链，但未满足“非空有效能力后验”硬门槛。
- 该批次只能称 `historical_blind_candidate`；论坛反馈早已客观存在，不能冒充真实 prospective 新案。

## 风险

- 当前历史隔离批次可以评估任务覆盖与克制行为，不能证明前瞻泛化准确度。
- provisional chart prototype 尚未接入指导 01 的可计算特征向量。
- 当前 L2 只有子平结构任务产生 claim；二元概率任务没有 claim，无法形成有效能力样本量。
