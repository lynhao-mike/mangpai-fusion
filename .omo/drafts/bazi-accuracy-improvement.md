---
slug: bazi-accuracy-improvement
status: superseded
intent: unclear
pending-action: none
approach: superseded by direct theory-library-driven engine refactor
---

# Draft: bazi-accuracy-improvement

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->

| id | outcome | status | evidence path |
|---|---|---|---|
| intake | 收集命盘与 as-of 日期，不含现实答案或反馈 | active | `engine/evaluation/domain_prospective.py:289` |
| blind-freeze | 生成不可变快照、声明、哈希，冻结后禁止补写答案 | active | `engine/evaluation/domain_prospective.py:335` |
| minimal-reveal | 只核验冻结声明，保留 hit/miss/pending/unknown | active | `engine/evaluation/domain_prospective.py:395` |
| scoring | 按声明和领域输出独立指标，不合并成单一命中率 | active | `tools/as_of_verdict_stats.py:35` |
| verified-state | 核验后仅更新事业域现实状态；跨域传播必须有显式边 | active | `plans/as-of-life-state-reasoning-design-2026-07-18.md:454` |
| governance | 产出可审计证据、样本状态、回滚记录；不自动升生产 | active | `engine/contracts/20-domain-prospective-evaluation-v1.md:128` |
| production | 现有默认 pipeline、规则、权重、路由保持不变 | active | `engine/application/production_service.py:154` |
| wealth/marriage expansion | 三领域协议之外的全域准确度扩展 | deferred | `engine/contracts/20-domain-prospective-evaluation-v1.md:1` |

## Open assumptions (announced defaults)
<!-- Intent is UNCLEAR: research resolves ambiguity, defaults are adopted (not asked), and each is surfaced in the plan's human TL;DR for veto. -->
<!-- assumption | adopted default | rationale | reversible? -->

| assumption | adopted default | rationale | reversible? |
|---|---|---|---|
| “前瞻/盲断”的含义 | 采用 as-of 日期前的盲态冻结，立即做最小现实核验；不把它解释成必须等待多年才有结果 | 先验证认识论闭环，符合仓库现有 as-of 设计 | yes |
| 首个功能域 | 事业域优先，单个真实成人案例；财富只允许通过显式传播边进入 | 当前 prospective 契约仅覆盖 career/wealth/marriage，先控制范围 | yes |
| 准确度基线 | 冻结当前 `run_pipeline` / 既有报告输出作为对照，不以已知答案下的“报告吻合度”作为证明 | AGENTS 明确禁止已知答案自证 | yes |
| 评分口径 | 保留 `CENTER_HIT`、`ALTERNATIVE_HIT`、`MISS`、`TAXONOMY_GAP`、`ABSTAIN` 独立统计，并单列 unknown/pending | 避免把替代命中、词典缺口和拒答混成准确率 | yes |
| 样本门槛 | 少于 30 个 genuine prospective scored cases 固定 `not_ready`；单案例只作为流程验证，不能宣称统计结论 | 现有 domain prospective contract 的硬门槛 | yes |
| 校准方式 | 第一阶段只生成离线校准候选和审计证据，不自动写入规则、专家权重、路由或默认报告模板 | 降低反馈泄漏和错误 promotion 风险 | yes |
| 失败处理 | 证据不足、分支不可收敛或事件表达过宽时允许 `ABSTAIN`；分类不覆盖时记录 `TAXONOMY_GAP` | 保持可诚实拒答和可修订分类 | yes |

## Findings (cited - path:lines)

- 现有 prospective 组件已经实现严格 intake、freeze、reveal 结构；`build_intake` 位于 `engine/evaluation/domain_prospective.py:289`，`freeze_snapshot` 位于 `:335`，`reveal_labels` 位于 `:395`，可以作为第一阶段的协议基础。
- 现有 prospective 评估的真实 cohort 当前是 `not_ready`，且硬门槛是至少 30 个 genuine prospective cases；证据见 `engine/evaluation/domain_prospective.py:27`、`:538`、`engine/contracts/20-domain-prospective-evaluation-v1.md:128-151` 和 `META/project-state.json:53-72`。
- `tools/as_of_verdict_stats.py:35` 已定义 `CENTER_HIT`、`ALTERNATIVE_HIT`、`MISS`、`TAXONOMY_GAP`、`ABSTAIN` 五类 verdict；该模型不应改造成一个合并命中率。
- 当前生产服务仍以既有 pipeline 为默认入口，且 `do_self_iter=False`，见 `engine/application/production_service.py:154`；因此准确度试验应与生产路径隔离。
- as-of 设计要求现实状态在核验后才改变，并强调不能用已知答案下的报告吻合度证明盲断能力，见 `plans/as-of-life-state-reasoning-design-2026-07-18.md:454` 及 AGENTS.md 第 6 节。
- 代码库已有反馈摄入、领域反馈和专家权重扫描，但它们写入面不同；将反馈摄入直接连接到生产校准会把评估和学习混在一起，需在第一阶段明确隔离。

## Decisions (with rationale)

1. 先做一个“事业域单案例盲验证”闭环，验证数据契约、泄漏门禁、人工核验和评分产物；不先扩充理论规则。
2. 每条声明必须在冻结时带有证据链、可证伪条件、现实翻译和时间窗；核验问题只能用于判断冻结声明，不能在核验后补造新声明。
3. 报告输出仍可作为被测基线，但“准确度提升”只由冻结声明和核验结果衡量。报告文字质量、理论派别数量和已知答案下的相似度不计入命中率。
4. 只有在真实 prospective 样本达到契约门槛，并完成人工治理、独立三态统计和生产隔离审计后，才讨论任何校准或 promotion；第一阶段不改变默认生产行为。

## Scope IN

- 建立/补齐 career-first as-of intake、freeze、最小核验、reveal、score、status 的端到端离线流程。
- 对反馈、known facts、occupation、reality status、prediction 等字段执行递归拒绝和冻结前泄漏测试。
- 生成每条声明、每个领域和每个案例的独立评分、未知/待定覆盖率、ABSTAIN 率与 taxonomy gap 记录。
- 产出 VerifiedState 的事业域最小更新，以及财富传播所需的显式边检查；无边时不得跨域更新。
- 用现有生产入口不变测试证明规则、权重、路由、默认报告产物没有被试验流程修改。
- 为后续真实 cohort 留下可复现的 artifact/hash、人工裁决和回滚记录。

## Scope OUT (Must NOT have)

- 不新增或重写子平、滴天髓、盲派规则，不调整规则权重，不做“命中率高所以自动升权”。
- 不切换生产 pipeline、专家主裁判路由、v6 preprod 默认开关或自迭代入口。
- 不把历史案例或已含 feedback/known_facts 的资料冒充 genuine prospective 样本。
- 不将 career/wealth/marriage 三领域结果外推为学业、健康、性格等全系统准确率。
- 不把 `CENTER_HIT` 与 `ALTERNATIVE_HIT` 合并成一个总分，不把 `TAXONOMY_GAP` 或 `ABSTAIN` 强行计为命中/失误。
- 不在核验后新增预测声明来提高命中数，不生成第二份用户报告或改变当前报告归档约束。

## Open questions

- 执行时由命理师提供一个可核验的真实成人案例及 as-of 日期；没有该输入时只能完成协议/fixture 测试，不能产生真实准确度结论。
- 需要用户确认第一阶段是否接受“事业域单案例闭环”作为提高准确度的最小切片；若需要全域，则必须扩大范围和验收成本，不能沿用当前三领域门槛直接代称全系统。
- 真实案例的核验问答由人工命理师确认，系统只负责冻结、记录、评分和审计，不替人工判断现实事实。

## Approval gate
status: superseded
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->

Superseded by user direction: do not use an as-of date or prospective verification workflow; edit the engine directly from the corpus and theory libraries.
