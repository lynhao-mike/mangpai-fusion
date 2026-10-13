# 高风险领域命题独立安全门禁契约 v1

## 1. 目的与边界

本契约约束六源三领域引擎中的高风险命题外显。门禁是工程证据充分性检查，不是现实准确率验证；门禁通过不得表述为事件真实、预测命中或现实概率成立。

门禁在领域切片完成命题生成之后、结构图构建、三段式仲裁和公开报告之前运行。它不扩充理论规则，不调整静态权重、生产路由或 prospective 协议，也不实现命题反馈闭环。

## 2. 显式注册表

第一版高风险任务白名单固定至少包括：

- `wealth.debt`
- `wealth.major_loss_window`
- `marriage.divorce_or_remarriage`

只有显式注册的 task 受本门禁约束；普通 task 的对象、立场、置信度和编排行为保持不变。注册表代码事实源为 `engine/v5/high_risk_gate.py`。

## 3. 通过条件

同一高风险 task 只有同时满足以下条件才可通过：

1. 至少存在两个独立学派来源的非 timing 支持命题；
2. 计数命题必须是结构或事件支持，不得为 abstain、oppose 或 mixed；
3. 证据列表非空，每条证据必须有非空 `source`、非空公开证据文本，并至少带一个 node reference 或 rule ID；
4. 当前命题必须有明确、非空的 falsifier；
5. 任付红命题和任何 `timing_claim` 均按 timing-only 处理，不计入独立结构/事件来源。

“独立来源”按公开学派身份计数，不按 evidence 条数、rule ID 数或同派多个 claim 重复计数。

## 4. 失败关闭语义

任一条件不满足时：

- 当前高风险命题转换为显式 `abstain`；
- 不生成 `oppose`，也不把失败解释为反面事件成立；
- 保留原置信度对象，不提高 score 或 tier；
- 禁止进入概率层；
- claim metadata 保留原立场、门禁状态、失败原因、独立来源计数、证据完整性、falsifier 状态和 timing-only 排除标记；
- 报告使用保守措辞，显示“需人工复核”和门禁状态。

失败原因枚举至少包括：

- `insufficient_independent_non_timing_sources`
- `incomplete_evidence`
- `missing_falsifier`

## 5. 审计投影

每条高风险 claim 的 `metadata.high_risk_gate` 至少包含：

- `status`: `passed` 或 `failed`
- `reason`
- `task_id`
- `required_independent_source_count`
- `independent_source_count`
- `independent_sources`
- `evidence_complete`
- `falsifier_present`
- `timing_only_excluded`
- `confidence_increased`: 恒为 false
- `requires_human_review`: 恒为 true

run snapshot 的 `metadata.high_risk_gate` 保存注册表版本、注册任务、状态与原因统计及逐 task 来源摘要。能力诊断只读消费 claim metadata 的真实状态，不从 `high_risk=true` 推断门禁结果。

## 6. 报告语义

公开 ViewModel 只投影中文门禁状态、公开失败原因和人工复核要求，不显示 claim ID、evidence ID、rule ID、内部来源路径或推理索引。

报告必须明确：门禁通过仅代表当前工程证据条件满足，不表示现实准确，不表示事件必然发生，也不替代现实资料核验和专业决策。

## 7. 确定性与兼容性

相同输入 claims 必须产生相同顺序、metadata 与 snapshot hash。门禁不得修改普通任务；不得让任付红 timing-only 提升结构支持或置信度；不得改变 prospective 冻结/揭示协议、逐命题报告内部 ID 禁显规则及十八槽位 registration/runtime 分账语义。
