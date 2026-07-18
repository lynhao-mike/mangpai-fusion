# HANDOFF · 短期交接

> 更新时间：2026-07-17（Asia/Shanghai）
>
> 本文件仅记录下一步与新会话提示词，不是长期事实源；当前状态以正式制品与 [`META/project-state.json`](META/project-state.json:1) 为准。易漂移的 HEAD、规则数量与生命周期数量均在运行时查询，不在本文固化。

## 1. 当前结论

- `prediction_capability_candidate_gate_v1 = HOLD`。
- `future_empirical_gate_v1 = HOLD`。
- `historical_platform_baseline_2026_07_15 = HOLD`。
- 生产默认仍为 static routing；staged 仅用于并跑和离线评估，`production_switch=false`，不得据此修改生产入口、规则或权重。
- 跨流派理论能力已改为 `catalog_count` 与 `executable_slice_count` 分账；运行入口见 [`theory_slice_status.py`](tools/theory_slice_status.py:1)，清单见 [`executable-slices-v1.yaml`](theory/executable-slices-v1.yaml:1)。
- 任派“职业角色变化应期”已通过 G0-G5，状态为 `staged_verified_production_unchanged`；证据包见 [`ren-career-timing-slice-g0-g5-verification.md`](reports/ren-career-timing-slice-g0-g5-verification.md:1)。
- 子平“官杀职业路径受扰资格门”已通过 G0-G5，状态为 `staged_verified_production_unchanged`；证据包见 [`ziping-career-structure-slice-g0-g5-verification.md`](reports/ziping-career-structure-slice-g0-g5-verification.md:1)。
- 默认 runner registry、正式 pipeline、production claim rules、公共 schema、报告入口及既有任派/杨派路径未因子平切片改变。

## 2. 理论切片本轮状态

### 2.1 子平“官杀职业路径受扰资格门”已完成 staged G0-G5

- 已批准设计：[`2026-07-17-ziping-career-official-path-disruption-slice-design.md`](docs/superpowers/specs/2026-07-17-ziping-career-official-path-disruption-slice-design.md:1)。
- 已执行 TDD 计划：[`2026-07-17-ziping-career-official-path-disruption-slice.md`](docs/superpowers/plans/2026-07-17-ziping-career-official-path-disruption-slice.md:1)。
- 目标任务为 `career.role_change`，task-scoped rule ID 为 `ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1`，production 来源锚点保持 `ZP-PROD-20260622-011` 与 `ZP-PROD-20260622-012`。
- 已落地严格映射、纯判别器、emit-only L2、专用 L3、确定性冻结、生产隔离测试、切片登记及 G0-G5 验证报告。
- 首证伪点已证明：粗官杀 trigger 存在但食伤必要门失败时，L2=0、L3=0、events=0、timings=0。
- 最新完成门 focused/regression/隔离集合为 298 passed、0 failed、0 skipped、1 个既有弃用 warning；未运行仓库全量测试，不得表述为全量通过。
- 子平计数分账为 `catalog_count=933`、production entries=933、`executable_slice_count=1`。
- 合法终态仅为 `staged_verified_production_unchanged`；G6 未进入，不代表准确率提升、生产晋级或可用于正式报告。

### 2.2 统一规范与任派纵切

- 统一规范：[`2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md`](docs/superpowers/specs/2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md:1)。
- 实施计划：[`2026-07-17-cross-school-slicing-ren-career-timing.md`](docs/superpowers/plans/2026-07-17-cross-school-slicing-ren-career-timing.md:1)。
- 任派规则注册：[`ren-career-timing-rules-v1.yaml`](theory/production/ren-career-timing-rules-v1.yaml:1)。
- 纯判别器：[`ren_career_timing.py`](engine/decision/ren_career_timing.py:1)。
- staged L5 adapter / assembler：[`ren_career_timing_slice.py`](engine/decision/ren_career_timing_slice.py:1)。
- 专项测试：[`tests/ren_timing/`](tests/ren_timing/)；本轮 focused gates 含任派、规则、冻结、生产护栏与杨派专项，共 227 passed、0 failed。
- 全量测试曾运行到 91% 且未出现可见失败，但部分历史评估测试耗时过长，已主动终止；不得将其表述为“全量测试通过”。

### 2.3 杨派 agent 已合入内容

杨派婚姻判别分支已通过远端 PR 合入当前 `main`，本轮复核 [`tests/yang_marriage/`](tests/yang_marriage/) 为 80 passed、0 failed。

已落地：

- 不可变三态判别与证据家族：[`yang_marriage.py`](engine/decision/yang_marriage.py:1)。
- event-only L2 SchoolClaim adapter：[`yang_marriage_claims.py`](engine/decision/yang_marriage_claims.py:1)。
- 专项 fixture 与领域、家族、adapter 测试：[`tests/yang_marriage/`](tests/yang_marriage/)。

当前边界：

- 已完成原始信号、家族去重、具名 A+B 门、矛盾信号 fail-closed、结构证据绑定与 event-only claim adapter。
- 尚不得仅凭这些专项测试宣称默认 pipeline 已切换、production YAML 已替换或报告出口已改用新切片。
- 新会话若继续杨派，先对照 [`杨派设计规格`](docs/superpowers/specs/2026-07-17-yang-marriage-discrimination-slice-design.md:1) 与 [`杨派实施计划`](docs/superpowers/plans/2026-07-17-yang-marriage-discrimination-slice.md:1)，按 Git 实际差异确认剩余 staged assembler、旁路隔离、共享门禁与状态登记任务；不得重复实现已合入部分。

## 3. 下一阶段优先级

1. **P3 滴天髓调候蒸馏**：先做只读审计与设计，从大量调候/气势条目中选择一个判别度高、事实闭包明确、可反驳的最小结构任务；批准后再实施 staged L2→L3，不全量迁移目录。
2. **杨派续作**：只处理 Git 实查后的未完成任务；与 P3 并行时，杨派、任派及子平写区继续由单一 owner 管理。
3. **G6 生产候选门**：任派、子平及后续切片均需独立冻结样本上的误报、漏报、校准与适用性后验，不能由合成测试自动晋级。
4. **首案即时回顾**：如业务事实已可收集，按既有 prospective 链执行 freeze 前事实收集、双审/仲裁、bind 与 completion，不与理论切片混写。

## 4. 新会话提示词

### 4.1 P3 · 滴天髓调候蒸馏（下一推荐会话）

```text
你正在 mangpai-fusion 仓库执行 P3“滴天髓调候蒸馏”理论切片。P2 子平“官杀职业路径受扰资格门”已经完成 staged G0-G5，状态为 staged_verified_production_unchanged；不得重复实施、扩写或接入生产。当前任务只做 P3 的只读审计、候选任务比较与设计审批，未获批准前不要写生产代码、测试或共享登记文件。

一、启动与事实源
1. 依次读取 AGENTS.md、META/project-state.json、handoff.md、docs/superpowers/specs/2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md、reports/ren-career-timing-slice-g0-g5-verification.md、reports/ziping-career-structure-slice-g0-g5-verification.md。
2. 再读取 engine/v5/ditiansui_runner.py、engine/application/production_rule_loader.py、theory/tiaohou_ditiansui/index.yaml、theory/tiaohou_ditiansui/_extracted_rules_summary.md、engine/features/types.py、engine/claims/domain.py、theory/executable-slices-v1.yaml 与直接相关 tests。
3. 执行 git fetch --prune origin、git status --short --branch、git rev-list --left-right --count HEAD...origin/main、git log --oneline --decorate -12。
4. 以 Git 和正式制品为持久状态，handoff.md 仅作短期入口。若存在 dirty diff、合并冲突、无法解释的远端推进，或杨派/任派/子平保护路径已有并行修改，立即 fail-closed；不覆盖、不 reset、不 stash、不自动合并。

二、固定边界
- 不迁移全部滴天髓/调候目录条目，不把 catalog_count 当 executable capability。
- 只选择一个事实闭包完整、可计算、可反驳的最小结构任务，优先 staged L2→L3。
- 不生成 EventHypothesis、TimingProbability、默认 lifetime window 或任何流派应期。
- 默认 runner registry、正式 pipeline、production claim-rules、公共 schema、报告入口以及杨派、任派、子平现有 staged 写区必须零改动。
- 未经独立批准不得进入实施；未来即使通过 G0-G5，也只能登记 staged_verified_production_unchanged，不得声称准确率提升、G6 完成或生产晋级。

三、只读审计交付
1. 对调候、气势、支冲等 production/catalog 条目聚类去重，识别 always trigger、散文型条目、复合规则与来源可解析性。
2. 盘点当前 runner、production loader、CFV 与 claim 层能够真实消费的事实，明确 catalog_count、production entries、executable_slice_count 三类计数。
3. 给出候选原子任务 Top 3。每个候选必须列明：原文锚点、task ID、单一结论、事实闭包、正向必要门、exclusions、counter conditions、首个 falsifier、目标层、与既有切片的写区冲突。
4. 给出 2-3 种蒸馏路径及推荐方案，明确为什么推荐项判别度更高、事实闭包更小、生产隔离更容易证明。
5. 形成设计草案：局部态 supported/weakened/contradicted/abstain、统一发布态、evidence family 去重、emit-only adapter、专用 L3、冻结确定性与 G0-G5 门禁。

四、停止条件与输出
- 审计阶段禁止提交实现代码；如需持久化，只能在用户批准后另行编写正式设计与实施计划。
- 发现事实字段不足、来源 ID 不稳定、候选必须依赖岁运/反馈/报告、或需要修改保护路径时，明确标记阻塞，不要扩大范围。
- 本会话先输出：Git 一致性、能力差距、候选 Top 3、方案比较、推荐方案、首证伪点和待批准决策；等待用户明确批准后再写规格与 TDD 实施计划。
```

## 5. 首案当前状态与下一动作

首案：[`P-GO-2026-001-坤-壬戌己酉乙卯丁亥`](META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/)

- [`v004 immutable frozen run`](META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--frozen-run--v004.json:1) 已存在。
- [`feedback-release v001`](META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--feedback-release--v001.json:1) 已存在且为 `RELEASED`；不要重复执行 release。
- 下一合法业务链：基于 [`prospective-immediate-retrospective-v1.json`](templates/prospective-immediate-retrospective-v1.json:1) 收集 freeze 前事实 → 高风险双审/冲突仲裁 → bind → completion。
- freeze 后才发生的事实进入独立 future observation 账，不得混入即时回顾。

## 6. 新会话最小必读

1. [`AGENTS.md`](AGENTS.md:1)：仓库规则与事实源矩阵。
2. [`META/project-state.json`](META/project-state.json:1)：当前机器状态。
3. [`跨流派理论切片设计`](docs/superpowers/specs/2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md:1)：统一切片定义、状态机与路线图。
4. [`子平 G0-G5 证据包`](reports/ziping-career-structure-slice-g0-g5-verification.md:1)：刚完成的 staged L2→L3 参考实现与生产隔离证据。
5. [`任派 G0-G5 证据包`](reports/ren-career-timing-slice-g0-g5-verification.md:1)：已验证的 staged timing 参考实现。
6. [`滴天髓/调候目录`](theory/tiaohou_ditiansui/index.yaml:1) 与 [`提取摘要`](theory/tiaohou_ditiansui/_extracted_rules_summary.md:1)：P3 审计对象。
7. [`滴天髓 runner`](engine/v5/ditiansui_runner.py:1) 与 [`production loader`](engine/application/production_rule_loader.py:1)：当前可执行能力与目录加载边界。
8. [`杨派设计规格`](docs/superpowers/specs/2026-07-17-yang-marriage-discrimination-slice-design.md:1) 与 [`杨派当前实现`](engine/decision/yang_marriage.py:1)：保护既有写区并避免重复施工。

[`handoff.md`](handoff.md:1) 自身不列为长期事实源；若与正式制品冲突，以正式制品和 [`META/project-state.json`](META/project-state.json:1) 为准。
