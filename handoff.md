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
- 默认 runner registry、正式 pipeline、production claim rules、公共 schema 与报告入口未因任派切片改变。

## 2. 理论切片本轮状态

### 2.1 子平“官杀职业路径受扰资格门”已批准、待实施

- 只读审计、方案选择与设计审批已经完成；新会话不得重复 brainstorming、候选路径比较或规格审批。
- 已批准设计：[`2026-07-17-ziping-career-official-path-disruption-slice-design.md`](docs/superpowers/specs/2026-07-17-ziping-career-official-path-disruption-slice-design.md:1)。
- 已批准 TDD 实施计划：[`2026-07-17-ziping-career-official-path-disruption-slice.md`](docs/superpowers/plans/2026-07-17-ziping-career-official-path-disruption-slice.md:1)。
- 目标任务为 `career.role_change`，task-scoped rule ID 为 `ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1`，来源锚点为 `ZP-PROD-20260622-011` 与 `ZP-PROD-20260622-012`。
- 当前仅有规格与计划；规则 YAML、判别器、adapter、专项测试、冻结制品、状态登记和验证报告均尚未实施。
- 最终合法状态仅为 `staged_verified_production_unchanged`；不得宣称准确率提升、G6 晋级或生产启用。

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

1. **P2 子平职业路径**：收敛子平 task Claim 与 production 库身份，先做一个 L2→L3 staged 纵切，不全量迁移目录规则。
2. **P3 滴天髓调候蒸馏**：从大量调候条目中选一个判别度高、事实闭包明确的结构任务，形成 G3/G4 切片。
3. **杨派续作**：只处理 Git 实查后的未完成任务；与 P2/P3 并行时，杨派写区继续由单一 owner 管理。
4. **G6 生产候选门**：任派与后续切片均需独立冻结样本上的误报、漏报、校准与适用性后验，不能由合成测试自动晋级。

## 4. 新会话提示词

### 4.1 P2 · 子平职业路径（已批准实施版）

```text
你正在 mangpai-fusion 仓库无人值守执行已批准的 P2 子平“官杀职业路径受扰资格门”staged L2→L3 纵切。设计与计划已经批准，不要重复 brainstorming、方案比较、规格编写或等待人工批准；直接按正式计划逐任务实施。

一、启动与事实源
1. 先读取 AGENTS.md、META/project-state.json、docs/superpowers/specs/2026-07-17-ziping-career-official-path-disruption-slice-design.md、docs/superpowers/plans/2026-07-17-ziping-career-official-path-disruption-slice.md、handoff.md。
2. 执行 git fetch --prune origin、git status --short --branch、git rev-list --left-right --count HEAD...origin/main、git log --oneline --decorate -12。
3. 以 Git、正式规格和计划为持久状态；handoff.md 只作短期入口。不要假定固定 HEAD。若工作树含非本任务改动、origin/main 出现无法安全解释的推进、或计划保护路径已有并行修改，立即 fail-closed 停止，不覆盖、不 reset、不 stash、不自动合并。

二、固定目标与边界
- task：career.role_change。
- task-scoped rule ID：ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1。
- production source anchors：ZP-PROD-20260622-011、ZP-PROD-20260622-012；原 production ID 不改写。
- 只做 staged L2→L3；子平只判断结构资格与职业路径结构。
- 禁止制造 EventHypothesis、TimingProbability、默认 lifetime window 或任何任派应期。
- 默认 runner registry、正式 pipeline、production claim-rules、公共 schema、报告入口、既有任派/杨派路径必须零改动。
- 终态只允许 staged_verified_production_unchanged，不得声称准确率提升、生产晋级或 G6 完成。

三、无人值守编排
使用一个顶层 orchestrator，严格按实施计划 Task 1→6 串行执行。每个 Task 使用全新的隔离子任务/子 agent；子任务只能完成当前 Task，不得提前修改后续共享集成文件。不要并发写仓库，也不要无界递归嵌套。若平台不支持子任务，则顶层 agent 自行按同一边界顺序执行。

每个 Task 的强制协议：
1. 从计划读取该 Task 的精确文件清单、测试和提交信息。
2. 复核工作树与最近提交，判断该 Task 是否已完成；若已有对应提交，先重跑该 Task focused tests，成功后跳到下一 Task，禁止重复施工。
3. 严格 TDD：先写/运行 RED，确认因目标能力缺失而失败；再做最小 GREEN；运行计划列出的 focused tests 和必要回归。
4. 执行 git diff --check，并审查 git diff --name-only，确保未触碰保护路径或别的 agent 写区。
5. 每个 Task 单独 commit，使用计划给定的提交信息；记录 commit SHA、RED 证据、GREEN/回归结果。
6. 顶层 orchestrator 在派发下一 Task 前复核该提交的 diff、测试和边界。复核失败时停止，禁止带病继续。
7. Task 6 才能修改共享最终登记/验证文件，包括 theory/executable-slices-v1.yaml、META/project-state.json、reports/ziping-career-structure-slice-g0-g5-verification.md 与 tests/tools/test_theory_slice_status.py。

四、会话耗尽与自动恢复
- Git commit 是唯一进度检查点；禁止把未验证的跨 Task 工作留在工作树。
- 若预计上下文不足，在完成当前 Task 的测试、diff 审查和 commit 后停止；不要半做下一 Task。
- 新 orchestrator 重启时重新执行启动检查，读取计划 Task 1→6，并依据文件、git log 和 focused tests 找到第一个未完成 Task；不要依赖上一会话记忆。
- 已提交 Task 的判断必须同时满足：对应提交/文件存在、工作树无冲突、focused tests 可复现。仅凭 commit message 不算完成。
- 若发现未提交但只属于单一当前 Task 的改动，先审查并复跑 RED/GREEN 证据；无法证明来源与正确性则停止，不擅自删除或接管。

五、自动停止条件
以下任一情况立即 fail-closed，并输出阻塞证据，不猜测修复：合并冲突；非本任务 dirty diff；保护路径变化；origin 推进导致基线不明；RED 未按预期失败；focused/regression test 失败；生产入口/公共 schema/任派/杨派路径出现 diff；需要扩大已批准范围；无法证明 events=0 且 timings=0。

六、完成门
只有 Task 1→6 均有独立提交并复核，计划要求的 focused/回归/隔离测试全部通过，git diff --check 通过，工作树干净，冻结制品确定性成立，catalog_count / production entries / executable_slice_count 分账正确，且生产制品摘要未变，才可报告完成。最终报告必须列出每个 Task 的 commit SHA、测试命令与结果、保护路径核验、未运行或中止的测试；不得把未跑的全量测试表述为通过。不要 push、rebase、merge 或改写历史，除非用户另有明确授权。
```

### 4.2 P3 · 滴天髓调候蒸馏

```text
你正在 mangpai-fusion 仓库执行 P3“滴天髓调候蒸馏”理论切片。先按 AGENTS.md 读取 README.md、META/project-state.json、tools/README.md、engine/README.md、engine/contracts/00-OVERVIEW.md；随后读取 docs/superpowers/specs/2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md、reports/ren-career-timing-slice-g0-g5-verification.md、engine/v5/ditiansui_runner.py、engine/application/production_rule_loader.py、theory/tiaohou_ditiansui/index.yaml、theory/tiaohou_ditiansui/_extracted_rules_summary.md、engine/features/types.py、engine/claims/domain.py 与相关 tests。

先执行 git fetch --prune origin、git status、git rev-list --left-right --count HEAD...origin/main，并核验杨派、任派及可能并行的子平写区；不得自动覆盖并行 agent 改动。

目标：不要迁移全部滴天髓/调候目录条目。先从调候或气势中选择一个事实闭包完整、可计算、可反证的最小结构任务，蒸馏为 staged G3/G4 切片，优先验证 L2→L3，不制造事件与应期。

必须先做只读审计与设计：
1. 对调候、气势、支冲等 trigger 聚类去重，识别 always/散文型条目，禁止把条目总量当能力；
2. 选择一个原子结论，明确冷暖燥湿/气势所需 CFV 字段、输入完整度、正向门、排除门与反条件；
3. 原文进入 source evidence，结论必须短、可评分；
4. 定义局部结构态 supported/weakened/contradicted/abstain，并映射统一发布态；
5. 首个证伪点必须证明“调候描述命中但关键事实不完整或反条件成立时，不得 emit”。

实施使用 TDD：先 RED，再最小 GREEN。建立严格 staged 规则注册、纯 extractor/reducer/discriminator、emit-only L2 adapter、L3 接线与冻结证明。默认 registry、正式 pipeline、production claim-rules、公共 schema、报告入口及现有杨/任/子平写区零改动。通过 G0-G5 后只登记 staged_verified_production_unchanged；独立样本与 G6 审批前不得切生产。

开始时先给出：Git 一致性、滴天髓目录条目与可执行能力差距、候选调候任务 Top 3、2-3 种蒸馏路径及推荐方案；取得批准后再写规格与实施计划。
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
3. [`子平已批准设计`](docs/superpowers/specs/2026-07-17-ziping-career-official-path-disruption-slice-design.md:1)：本次纵切的固定语义与边界。
4. [`子平已批准实施计划`](docs/superpowers/plans/2026-07-17-ziping-career-official-path-disruption-slice.md:1)：Task 1→6 的 TDD、文件、测试和提交清单。
5. [`跨流派理论切片设计`](docs/superpowers/specs/2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md:1)：统一切片定义、状态机与路线图。
6. [`任派 G0-G5 证据包`](reports/ren-career-timing-slice-g0-g5-verification.md:1)：已验证参考实现。
7. [`杨派设计规格`](docs/superpowers/specs/2026-07-17-yang-marriage-discrimination-slice-design.md:1) 与 [`杨派当前实现`](engine/decision/yang_marriage.py:1)：避免重复施工。

[`handoff.md`](handoff.md:1) 自身不列为长期事实源；若与正式制品冲突，以正式制品和 [`META/project-state.json`](META/project-state.json:1) 为准。
