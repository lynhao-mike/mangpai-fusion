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

1. 对每个新案，在反馈填写前自动生成并冻结受限任务预测。
2. 后续反馈只追加 revealed labels，并绑定 frozen hash。
3. 累积到至少 5 个同六维身份样本后首次观察 posterior；少于 5 保持 HOLD。
4. 人工只处理冲突来源、高风险标签和自动映射低置信项；低歧义年份事件自动摄入。
5. 达到 ≥30 个 prospective 案例后，才把阶段 03 从数据准备完成提升为真实能力基线完成。

## 风险

- 当前 30 案只能训练/开发，不能证明泛化准确度。
- provisional chart prototype 尚未接入指导 01 的可计算特征向量。
- 指导 02 未完成前，引擎命题能力仍可能为空；评估人的手写命题没有意义。
