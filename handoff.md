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

### 2.1 统一规范与任派纵切

- 统一规范：[`2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md`](docs/superpowers/specs/2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md:1)。
- 实施计划：[`2026-07-17-cross-school-slicing-ren-career-timing.md`](docs/superpowers/plans/2026-07-17-cross-school-slicing-ren-career-timing.md:1)。
- 任派规则注册：[`ren-career-timing-rules-v1.yaml`](theory/production/ren-career-timing-rules-v1.yaml:1)。
- 纯判别器：[`ren_career_timing.py`](engine/decision/ren_career_timing.py:1)。
- staged L5 adapter / assembler：[`ren_career_timing_slice.py`](engine/decision/ren_career_timing_slice.py:1)。
- 专项测试：[`tests/ren_timing/`](tests/ren_timing/)；本轮 focused gates 含任派、规则、冻结、生产护栏与杨派专项，共 227 passed、0 failed。
- 全量测试曾运行到 91% 且未出现可见失败，但部分历史评估测试耗时过长，已主动终止；不得将其表述为“全量测试通过”。

### 2.2 杨派 agent 已合入内容

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

### 4.1 P2 · 子平职业路径

```text
你正在 mangpai-fusion 仓库执行 P2“子平职业路径”理论切片。先按 AGENTS.md 读取 README.md、META/project-state.json、tools/README.md、engine/README.md、engine/contracts/00-OVERVIEW.md；随后读取 docs/superpowers/specs/2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md、reports/ren-career-timing-slice-g0-g5-verification.md、engine/v5/ziping_runner.py、engine/application/production_rule_loader.py、theory/ziping/index.yaml、engine/decision/r10_ziping_career.py、engine/claims/domain.py 与相关 tests。

先执行 git fetch --prune origin、git status、git rev-list --left-right --count HEAD...origin/main，并核验杨派与任派现有写区；不得自动覆盖并行 agent 改动。

目标：不要迁移全部子平目录规则。先选一个“职业路径/职业角色变化”的最小高判别任务，建立 production rule ID ↔ task-scoped Claim rule ID 的稳定映射，并完成 staged L2→L3 纵切。子平只负责结构合法性与职业路径结构，不制造任派应期，也不调用默认时间窗。

必须先做只读审计与设计：
1. 区分 catalog_count、production entries、executable_slice_count；
2. 找出子平现有职业相关 runner、production trigger、来源锚点与身份分裂；
3. 定义单任务、单结论、事实闭包、exclusions、counter conditions、falsifier 与 evidence refs；
4. 定义局部结构态 supported/weakened/contradicted/abstain，并映射统一发布态 emit/hold/abstain/unsupported；
5. 首个证伪点必须证明“职业相关粗 trigger 存在，但结构必要门不成立时不得进入 L3 pass”。

实施使用 TDD：先 RED，再最小 GREEN。先做专用 staged 入口与冻结测试；默认 runner registry、正式 pipeline、production claim-rules、公共 schema、报告入口和既有任派/杨派路径零改动。每项任务独立提交并复核。通过 G0-G5 后只登记 staged_verified_production_unchanged，不宣称准确率提升或生产晋级。

开始时先给出：仓库/Git 一致性、子平职业能力现状矩阵、2-3 种切片路径及推荐方案；取得批准后再写规格与实施计划。
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
3. [`跨流派理论切片设计`](docs/superpowers/specs/2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md:1)：统一切片定义、状态机与路线图。
4. [`任派 G0-G5 证据包`](reports/ren-career-timing-slice-g0-g5-verification.md:1)：已验证参考实现。
5. [`杨派设计规格`](docs/superpowers/specs/2026-07-17-yang-marriage-discrimination-slice-design.md:1) 与 [`杨派当前实现`](engine/decision/yang_marriage.py:1)：避免重复施工。
6. 当前任务直接相关的 runner、production loader、理论 index 与专项测试。

[`handoff.md`](handoff.md:1) 自身不列为长期事实源；若与正式制品冲突，以正式制品和 [`META/project-state.json`](META/project-state.json:1) 为准。
