# ten-god-structure-production-closure - Work Plan

## TL;DR (For humans)
**What you'll get:** 引擎会形成完整的十神关系图，并对仓库理论库中可证实的 30 个命名结构统一给出“原局状态 + 各步大运变化 + 用户明确指定流年的变化”，兼容 pipeline、V5、统一报告和反馈记录使用同一语义。

**Why this approach:** “完整”由两层闭包保证：底层覆盖十神全部生克关系，上层用受控目录表达经典的流通、制化、取清和破坏结构；原局负责结构本体，大运只能补全、强化、延续或破坏，流年只有显式传入才参与。理论库必须逐条分类，古例和关键词不能直接变成执行规则。

**What it will NOT do:** 不读取 as-of 日期、系统当前年份或自动未来三年；不把传统单格、从格、专旺格、化气格、调候或神煞混入十神关系结构；不切换默认生产入口；不根据反馈自动晋级规则或权重。

**Effort:** XL
**Risk:** High - 30 个命名结构既要共享完整关系图，又有不同的强弱、制化、取清和阻断条件；任何一处把“共现”误当“成立”或把岁运压成原局，都会系统性放大误判。
**Decisions to sanity-check:** “完整”定义为当前仓库语料闭包；首版目录固定 30 个结构，新增语料出现未映射术语时门禁失败；无大运时只给原局；结构反馈进入独立候选账本，暂不进入通用权重学习。

Your next move: 选择直接开始执行，或先做双重高精度 Momus 计划审查。完整执行细节如下。

---

> TL;DR (machine): XL/high-risk; build a complete ten-god relation graph plus a 30-structure corpus-closed catalog, explicit-only cycle overlays, curated theory mapping, strict namespaced activation, dual pipeline/V5 integration, report projection, and isolated feedback calibration without changing the default route.

## Scope
### Must have
- 完整性采用双层定义：底层 `TenGodRelationGraph` 对十神角色及日主的全部有向关系给出 typed edge；上层 `ten-god-structure-catalog-v1` 对仓库当前语料中的命名结构实现零未分类闭包。
- 首版目录固定 30 个结构，按四类组织：流通/护卫 13 个、制化 5 个、取清 3 个、破坏/失衡 9 个。完整 ID 与中文名见 Todo 3；不得以任意十神共现替代目录谓词。
- `食神制杀`、`伤官驾杀`、`杀印相生` 保持向后兼容，但 `TenGodStructureKind` 不再是完整事实源；目录中的稳定 `structure_id` 才是完整清单的唯一事实源。
- 新增共享、不可变、可序列化的 `TenGodRelationGraph`、`TenGodStructureBundle` 和 `StructureAssessment`；`AnalysisOutput`、`V5Output`、`V5RunSnapshot` 均使用命名字段 `ten_god_structures`，V5 hash 必须覆盖关系图摘要和结构 bundle。
- 新增批量入口 `assess_ten_god_structures(parsed, *, requested_years: tuple[int, ...] = ())`；年份规范化为升序去重整数，拒绝 `bool` 与 `1..9999` 之外的值。
- 保留 `assess_ten_god_structure(parsed, kind, *, target_year=None)` 的签名与返回形状，改为批量入口的兼容包装。
- 原局完整但无 `dayun_steps` 时返回 supported 的原局状态、空大运和空流年；四柱缺失或非法时返回 unsupported diagnostic，不生成结构断语或结构 claim。
- 结构目录固定在 `mapping/ten-god-structure-catalog-v1.yaml`；理论映射固定在 `mapping/ten-god-structure-rule-map-v1.yaml`。每个命中结构别名的理论规则都必须被分类为 `general_principle/case_excerpt/explanation/counterexample/out_of_scope`，未分类数必须为 0；仅 `general_principle` 可执行。
- 目录 recipe 只允许受控 operator，不允许 `eval`、动态 Python 或运行时中文语义推断；官杀去留、伤官伤尽、羊刃/劫财/伤官合杀等复杂结构使用显式 specialized evaluator key。
- 生产规则触发器保留仓库当前 11 个 legacy trigger，并增加严格的 `ten_god_structure/<structure_id>` 命名空间；原三个结构 trigger 作为兼容 alias 规范化到目录 ID。未知 trigger 或未知结构 ID 加载失败且运行时未激活。
- 用 typed `RuleActivation` 保存规则、结构、目录类别、层级、phase、取清 resolution、大运干支和起讫年份、显式流年年份及证据 hash；不得再把所有层级压成一个布尔值。
- 兼容 pipeline 与 V5 同时接线，但保持 `engine/pipeline.py` 为当前默认入口，不做产品路由切换。
- 报告只展示自然语言结构、层级、证据、阻断与应期；内部 rule/statement/activation ID 只进入结构化记录。
- `statement_records.json` 增加 `structure_context`；结构反馈写入独立 append-only JSONL 候选账本，重复摄入按稳定 candidate_id 幂等跳过，不进入现有规则 fanout。
- 验证包含十神关系矩阵穷举、30 个目录结构正反例、岁运转换、两个入口集成、序列化/hash、报告泄漏、反馈隔离、理论零未分类门禁和一个只读真实案例 replay。

### Must NOT have (guardrails, anti-slop, scope boundaries)
- 不得读取 `as_of_date`、`date.today().year`、`datetime.now().year`、chart 中的 `current_year` 或任何默认“未来三年”来生成结构流年层；审计时间戳和既有 `analysis_date` 可保留，但不得作为结构语义输入。
- 不得调用 `engine/v5/domain_slices/context.py` 的 as-of 上下文来构建本功能的流年或大运状态。
- 不得把正官格、七杀格、财格、印格、食神格、伤官格、建禄格、阳刃格等单格体系，以及从格、专旺格、化气格、调候、神煞，伪装成本计划的十神关系结构；这些不是当前“完整关系体系”的缺口。
- 不得在首版目录之外临时硬编码第 31 个命名结构；发现新术语时必须进入 inventory 未分类门禁并经过目录版本升级。
- 不得从 `claim`、`excerpt`、标题或中文关键词在运行时推断结构类型；未映射规则不能成为结构规则。
- `case_excerpt`、`explanation`、`counterexample` 均不得 `executable: true`；案例语料只能作为理论证据或反证材料。
- 不得让 V5 继续以 `quantifiable=True` 作为充分触发条件；量化标志不能代替命盘条件。
- 不得把大运补全/强化、流年引动描述为原局成立；不得在无显式年份时输出空壳流年标题或“当前流年”。
- 不得为 30 个结构复制 30 套原局/大运/流年循环；所有结构必须消费同一层级关系图和 cycle overlay。
- 不得自动修改规则状态、置信度、权重、历史 run snapshot、`META/rule-changelog.md` 或人工裁决记录。
- 测试与 replay 不得写入 `cases/`、`reports/`；不得执行全局 `git reset`、`git clean`、`git checkout --` 或覆盖当前脏工作区的用户修改。
- 不得提交、推送或创建 PR；本计划所有 todo 的 Commit 均为 `N`，除非用户后续明确授权。

### Catalog evidence closure
`evidence_mode` 只有三种：`direct`（语料直接表达）、`normalized`（异体/同义术语归一）、`composite`（由同一语料库中两条已证实有向关系组成）。这张表是 30 项目录的证据下限；Todo 4 的 inventory 必须继续分类所有 alias candidate，不能只验证本表。

| structure_id | 展示名 | evidence_mode | 最低语料锚点 |
| --- | --- | --- | --- |
| `officer_generates_seal` | 官印相生 | normalized | `ZP-PROD-20260622-035`, `theory/ziping/index.yaml:1348`（官星生印） |
| `killing_generates_seal` | 杀印相生 | normalized | `ZP-PROD-20260622-040`, `:1542`（印绶化杀）；`ZP-PROD-20260622-359`, `:14596`（煞印相生） |
| `wealth_generates_officer` | 财官相生 | direct | `ZP-PROD-20260622-012`, `:453`（财生官） |
| `wealth_generates_killing` | 财滋杀 | direct | `ZP-PROD-20260622-040`, `:1542`（财生杀） |
| `food_god_generates_wealth` | 食神生财 | direct | `ZP-PROD-20260622-037`, `:1426` |
| `hurting_officer_generates_wealth` | 伤官生财 | normalized | `ZP-PROD-20260622-034`, `:1308`（食伤生财） |
| `hurting_officer_uses_seal` | 伤官配印 | direct | `ZP-PROD-20260622-019`, `:724` |
| `food_god_uses_seal` | 食神配印 | normalized | `ZP-PROD-20260622-479`, `:19482`（食多用印） |
| `seal_protects_officer` | 印绶护官 | direct | `ZP-PROD-20260622-012`, `:453`（印护官） |
| `officer_protects_wealth` | 官星护财 | direct | `ZP-PROD-20260622-034`, `:1308` |
| `output_releases_excellence` | 食伤泄秀 | normalized | `ZP-PROD-20260622-035`, `:1348`（食伤吐秀） |
| `wealth_officer_seal_flow` | 财官印相生 | composite | `ZP-PROD-20260622-012`（财生官）+ `ZP-PROD-20260622-035`（官生印） |
| `output_wealth_officer_flow` | 食伤生财生官 | direct | `ZP-PROD-20260622-474`, `:19275`（伤尽生财、财旺生官） |
| `food_god_controls_killing` | 食神制杀 | direct | `ZP-PROD-20260622-037`, `:1426`; `ZP-PROD-20260622-040`, `:1542` |
| `hurting_officer_controls_killing` | 伤官驾杀 | normalized | `DTS-PROD-20260622-788`, `theory/tiaohou_ditiansui/index.yaml:32776`（伤官敌之） |
| `blade_killing_balanced` | 羊刃驾杀 | normalized | `ZP-PROD-20260622-019`, `:724`（阳刃用官杀制伏）；`DTS-PROD-20260622-788`（羊刃合之） |
| `rob_wealth_combines_killing` | 劫财合杀 | normalized | `DTS-PROD-20260622-374`, `:15477`（败财合杀） |
| `hurting_officer_combines_killing` | 伤官合杀 | direct | `ZP-PROD-20260622-370`, `:15043` |
| `officer_killing_mixed` | 官杀混杂 | direct | `ZP-PROD-20260622-369`, `:14979` |
| `officer_killing_cleared` | 官杀去留取清 | direct | `ZP-PROD-20260622-369/370`, `:14979-15060` |
| `hurting_officer_exhausted` | 伤官伤尽 | direct | `ZP-PROD-20260622-474/476`, `:19275-19371` |
| `hurting_officer_meets_officer` | 伤官见官 | direct | `ZP-PROD-20260622-474`, `:19275` |
| `owl_robs_food` | 枭神夺食 | direct | `ZP-PROD-20260622-037`, `:1426` |
| `wealth_damages_seal` | 财坏印 | normalized | `ZP-PROD-20260622-035`, `:1348`（财星破印） |
| `peers_compete_for_wealth` | 比劫夺财 | normalized | `ZP-PROD-20260622-033`, `:1268`（比肩劫财夺财） |
| `wealth_aids_killing_attack` | 财生杀攻身 | direct | `ZP-PROD-20260622-040`, `:1542` |
| `overcontrolled_killing` | 制杀太过 | direct | `DTS-PROD-20260622-088`, `:3644` |
| `killing_attacks_body` | 官杀攻身 | normalized | `ZP-PROD-20260622-040`, `:1542`（杀旺攻身） |
| `output_overdrains_body` | 食伤泄身太过 | normalized | `ZP-PROD-20260622-018`, `:685`（食神过旺泄身） |
| `excess_seal_blocks_output` | 印旺滞食 | direct | `ZP-PROD-20260622-018`, `:685` |

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD，使用现有 `pytest`；每个 todo 先增加会失败的聚焦测试，再做最小实现使其通过。
- Focused suites: `tests/predicates/`、结构 catalog/inventory/mapping 测试、`tests/test_production_rule_loader.py`、新增的 pipeline/report/feedback 测试、`tests/v5/test_v5_contracts.py`。
- Coverage gates: 十神角色关系矩阵 100% 有 typed relation；30 个目录项各有 natal 成立、潜伏/阻断、岁运转换场景；理论 alias candidate 未分类数为 0；目录、recipe、specialized evaluator 与报告 label 一一对应。
- Regression gate: 聚焦测试通过后运行 `pytest tests/predicates tests/test_ten_god_structure_catalog.py tests/test_ten_god_structure_inventory.py tests/test_production_rule_loader.py tests/v5/test_v5_contracts.py tests/test_project_metadata.py -q`；最终再运行 `pytest tests/ -q`。
- Static gate: `python -m compileall engine tools tests`；若仓库环境提供 Ruff，再运行 `python -m ruff check` 仅限本计划改动路径，Ruff 缺失不得伪报通过。
- Evidence: 每项命令完整输出写入其 todo 中列明的 `.omo/evidence/task-{id}-ten-god-structure-production-closure.txt`；最终四路审查写入各自列明的 F1-F4 证据文件。
- Non-mutation proof: Todo 1 先用 `git status --porcelain=v1 -z --untracked-files=all` 冻结路径级状态，并为所有现有脏文件及 `cases/`、`reports/` 下的全部文件记录 SHA-256；replay 和最终审查必须重算并与 `.omo/evidence/preflight-worktree-baseline.json` 比较，不能用临时 status 相等代替内容未变。输出只能写入 `.omo/evidence/` 或系统临时目录。

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.
- **Wave 1A - 契约门（1，串行）**：先冻结完整性的操作定义、30 项目录、层级状态、激活、报告和反馈契约。
- **Wave 1B - 独立基础件（2、3、11，并行）**：建立关系图/输出 DTO、结构目录和 V5 chart adapter；三项写集互不重叠。
- **Wave 2 - 语料与公共边界（4、5、12，并行）**：建立理论 inventory/map、原局关系图 builder、statement/report 投影契约。
- **Wave 3 - 结构判定（6-8，并行）**：分别实现流通护卫、制化取清、破坏失衡三组 evaluator；共享关系图，不复制岁运循环。
- **Wave 4 - 岁运、规则与反馈内核（9、10、15，并行）**：建立统一 cycle overlay、严格 namespaced activation、隔离反馈候选账本。
- **Wave 5 - 双入口（13、14，并行）**：兼容 pipeline 与 V5 分别接线，保持默认路由不变。
- **Wave 6 - 闭包验收工具（16，串行）**：接入 registry、零未分类门禁和双入口只读 replay。
- **Final verification**：全部 todo 完成后并行执行 F1-F4；任何一路非 APPROVE 均返回对应 todo 修正并重跑全部四路。

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | - | 2, 3, 4, 11, 12 | - |
| 2 | 1 | 5, 6, 7, 8, 9, 10, 12, 13, 14 | 3, 11 |
| 3 | 1 | 4, 6, 7, 8, 9, 10, 12 | 2, 11 |
| 4 | 1, 3 | 10, 16 | 5, 12 |
| 5 | 2 | 6, 7, 8, 9 | 4, 12 |
| 6 | 2, 3, 5 | 9, 10, 13, 14 | 7, 8 |
| 7 | 2, 3, 5 | 9, 10, 13, 14 | 6, 8 |
| 8 | 2, 3, 5 | 9, 10, 13, 14 | 6, 7 |
| 9 | 2, 3, 5, 6, 7, 8 | 13, 14, 16 | 10, 15 |
| 10 | 2, 3, 4, 6, 7, 8 | 13, 14 | 9, 15 |
| 11 | 1 | 14 | 2, 3 |
| 12 | 1, 2, 3 | 13, 14, 15 | 4, 5 |
| 13 | 2, 6, 7, 8, 9, 10, 12 | 16 | 14 |
| 14 | 2, 6, 7, 8, 9, 10, 11, 12 | 16 | 13 |
| 15 | 12 | 16 | 9, 10 |
| 16 | 4, 9, 13, 14, 15 | F1-F4 | - |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [ ] 1. 冻结“完整十神关系体系”契约与边界
  What to do / Must NOT do: 创建（当前不存在）`engine/contracts/22-ten-god-structure-state-v1.md`，把完整性定义为“日主 + 十神共 11 节点、排除 self-edge 的 110 个有向关系位全部可判定 + 当前理论语料 30 项命名目录零未分类”；定义目录四类、原局/大运/显式流年、phase、取清 resolution、强弱/根气/透藏、blocker、序列化、激活、报告和反馈。在 `engine/contracts/00-OVERVIEW.md` 与 `engine/contracts/README.md` 的 21 号契约之后插入 22 号索引。明确传统单格/从格/专旺/化气/调候不属于本契约。执行前生成 `.omo/evidence/preflight-worktree-baseline.json`：用 NUL 分隔 porcelain 输出保存所有现有 modified/untracked 路径的精确状态、文件类型、大小与 SHA-256，并保存 `cases/`、`reports/` 全文件树的路径/类型/大小/SHA-256；同时写入只包含 Todos 1-16 明确列名产品/测试路径及 `.omo/evidence/**` 的 `allowed_pathspecs`。后续任何不在 allowlist 的新增、删除、重命名、状态变化或 hash 变化都必须失败；不得改产品版本。
  Parallelization: Wave 1A | Blocked by: none | Blocks: 2, 3, 4, 11, 12
  References: `engine/contracts/02-predicate-library.md`; `engine/contracts/03-findings-schema.md`; `engine/contracts/07-pipeline-flow.md`; `engine/contracts/10-ziping-fusion-v5.md`; `engine/contracts/21-high-risk-domain-claims-v1.md`; `AGENTS.md` sections 2, 3, 6.
  Acceptance criteria: `pytest tests/test_ten_god_structure_contract.py -q` passes；测试锁定 11 节点/110 有向关系位、30 项目录、四类数量 13/5/3/9、显式年份禁令、零未分类定义和 out-of-scope 清单；baseline JSON 可重新校验所有既有脏文件及 `cases/`、`reports/` 全树，且 allowlist 不包含泛化的仓库根目录、`engine/**`、`tests/**`、`cases/**` 或 `reports/**`。
  QA scenarios: happy: 解析正式契约并与目录预期清单比较、验证 baseline 中每个既有脏文件和 cases/reports 文件 hash；failure: temp 契约删除任一结构、缩减为 10 节点/90 关系位、允许隐式年份、把单格列入目录、篡改 baseline 副本或加入过宽 pathspec 时测试失败。Evidence `.omo/evidence/task-1-ten-god-structure-production-closure.txt`.
  Commit: N | docs(contract): no commit without user authorization

- [ ] 2. 建立完整关系图、结构状态与输出 DTO
  What to do / Must NOT do: 在 `engine/predicates/ten_god_structure_types.py` 增加 immutable `TenGodRoleNode`、`TenGodRelationEdge`、`TenGodRelationGraph`、`StructureDiagnostic`、`StructureAssessment`、`TenGodStructureBundle`；edge 必须记录 source/target、generate/control/same-family/combine 等 typed relation、强度、来源层和证据。保留原三结构 `TenGodStructureKind` 与 `TenGodStructureAssessment` 的兼容包装，但目录 ID 用受校验字符串而非继续扩张 enum。给 `AnalysisOutput`、`V5Output`、`V5RunSnapshot` 增加命名字段并更新 round-trip/hash；旧 payload 缺字段时返回兼容空 bundle。
  Parallelization: Wave 1B | Blocked by: 1 | Blocks: 5-10, 12-14
  References: `engine/predicates/ten_god_structure_types.py:8-48`; `engine/predicates/ten_god_profile.py`; `engine/domain/analysis.py:182-286`; `engine/v5/domain.py:370-470`; `engine/v5/domain.py:651-689`.
  Acceptance criteria: `pytest tests/predicates/test_ten_god_structure_types.py tests/v5/test_v5_contracts.py tests/test_decision_v5_adapter.py tests/v5/test_domain_analysis_orchestrator.py -q` passes；关系图和 30 项 bundle 可无损 round-trip；任何节点、edge、phase、resolution 或年份篡改都会改变 V5 hash；旧 JSON、所有现有 direct constructors、`engine/decision/v5_adapter.py`、`engine/v5/domain_slices/orchestrator.py` 和 `engine/v5/preprod.py` 路径均保持兼容。
  QA scenarios: happy: natal/dayun/two-liunian bundle 通过三个输出 DTO、decision adapter、domain orchestrator 和 preprod snapshot round-trip；failure: unknown relation/structure ID、非法 layer/resolution/year 被拒，旧 payload/旧构造调用可读但不伪造结构。Evidence `.omo/evidence/task-2-ten-god-structure-production-closure.txt`.
  Commit: N | feat(domain): no commit without user authorization

- [ ] 3. 建立 30 项结构目录、别名和受控 recipe schema
  What to do / Must NOT do: 新增 `mapping/ten-god-structure-catalog-v1.yaml` 与 `engine/predicates/ten_god_structure_catalog.py`。流通/护卫 13 项固定为 `officer_generates_seal` 官印相生、`killing_generates_seal` 杀印相生、`wealth_generates_officer` 财官相生、`wealth_generates_killing` 财滋杀、`food_god_generates_wealth` 食神生财、`hurting_officer_generates_wealth` 伤官生财、`hurting_officer_uses_seal` 伤官配印、`food_god_uses_seal` 食神配印、`seal_protects_officer` 印绶护官、`officer_protects_wealth` 官星护财、`output_releases_excellence` 食伤泄秀、`wealth_officer_seal_flow` 财官印相生、`output_wealth_officer_flow` 食伤生财生官。制化 5 项固定为 `food_god_controls_killing` 食神制杀、`hurting_officer_controls_killing` 伤官驾杀、`blade_killing_balanced` 羊刃驾杀、`rob_wealth_combines_killing` 劫财合杀、`hurting_officer_combines_killing` 伤官合杀；羊刃驾杀按“杀刃相制且两者有力”建模，不预设羊刃单向制杀。取清 3 项固定为 `officer_killing_mixed` 官杀混杂、`officer_killing_cleared` 官杀去留取清、`hurting_officer_exhausted` 伤官伤尽。破坏/失衡 9 项固定为 `hurting_officer_meets_officer` 伤官见官、`owl_robs_food` 枭神夺食、`wealth_damages_seal` 财坏印、`peers_compete_for_wealth` 比劫夺财、`wealth_aids_killing_attack` 财生杀攻身、`overcontrolled_killing` 制杀太过、`killing_attacks_body` 官杀攻身、`output_overdrains_body` 食伤泄身太过、`excess_seal_blocks_output` 印旺滞食。每项必须有 aliases、family、evaluator、recipe/specialized key、理论 refs、互斥/优先级。recipe operator 仅允许：`role(role, presence, min_strength, rooted?, exposed?)`（5 个具名 operand）、`edge(source_role, target_role, relation, min_strength)`（4）、`body_strength(one_of)`（1）、`chain(edges)`（2-4 条 edge）、`stem_combine(left_role, right_role, mode)`（3）、`structure_state(structure_id, phase_in)`（2）、`all(items)`/`any(items)`（至少 1）、`not(item)`（恰好 1）。strength 只允许 `weak/balanced/strong/excessive`，不接收任意数值。通用 phase 映射固定为：无 required role=absent；角色存在但 edge/strength 未齐=latent；required 全真且 blocker 假=established；base 曾成立且 blocker 真=disrupted。禁止 eval 和未登记 operator。
  Parallelization: Wave 1B | Blocked by: 1 | Blocks: 4, 6-10, 12
  References: `theory/ziping/index.yaml:453`; `:685`; `:724`; `:1229`; `:1268`; `:1308`; `:1348`; `:1426`; `:1542`; `:14979`; `:19275`; `theory/tiaohou_ditiansui/index.yaml:3644`; `:27336`; `engine/predicates/ten_god_structure_core.py`.
  Acceptance criteria: `pytest tests/test_ten_god_structure_catalog.py -q` passes；目录精确 30 项且四类计数正确；每项 display name/alias 唯一归一化；operator 名称、arity、operand type、strength/phase enum 和 specialized key 全部校验；原三个 trigger alias 指向正确 ID。
  QA scenarios: happy: 正式目录加载并解析中繁体/异体别名如“食神制煞、伤官敌杀、煞印相生、败财合杀”；failure: duplicate alias、未知 operator、错误 arity/operand type/threshold、缺 evaluator、类目计数漂移、第 31 项或不存在 theory ref 均失败。Evidence `.omo/evidence/task-3-ten-god-structure-production-closure.txt`.
  Commit: N | feat(catalog): no commit without user authorization

- [ ] 4. 建立理论术语 inventory 和全量人工分类映射
  What to do / Must NOT do: 新增 `tools/ten_god_structure_inventory.py`、`mapping/ten-god-structure-rule-map-v1.yaml` 与 loader。inventory 仅作离线治理：按目录 aliases 扫描两个 production index，列出每个 candidate rule；映射逐条记录 `rule_id/structure_id/semantic_class/executable/allowed_phases/rationale/source_digest/source_trigger/effective_trigger`，并允许 `out_of_scope`。所有 candidate 必须有人工分类，未分类数为 0；只有 general principle 可 executable，case/explanation/counterexample/out_of_scope 均不可执行。一个 rule 可显式映射多个 structure_id，每个 pair 单独激活。运行时只能读映射，绝不扫描中文；不得批量重写两个 2.5MB+ production index。
  Parallelization: Wave 2 | Blocked by: 1, 3 | Blocks: 10, 16
  References: `theory/ziping/index.yaml`; `theory/tiaohou_ditiansui/index.yaml`; representative rules `ZP-PROD-20260622-012/018/019/032/033/034/035/037/040/369/370/474/476`; `DTS-PROD-20260622-088/657/788`; `engine/application/production_rule_validation.py:17-74`.
  Acceptance criteria: `pytest tests/test_ten_god_structure_inventory.py tests/test_ten_god_structure_rule_map.py -q` passes；`python -m tools.ten_god_structure_inventory --check` exit 0、unclassified=0、missing_rule=0、executable_non_general=0；映射中每个 source digest 与当前规则一致。
  QA scenarios: happy: inventory JSON/Markdown 两种输出稳定且不改 mapping；failure: 新增 temp alias hit 未映射、删除规则、篡改 digest、把 case_excerpt 标 executable 都返回非零。Evidence `.omo/evidence/task-4-ten-god-structure-production-closure.txt`.
  Commit: N | feat(theory-governance): no commit without user authorization

- [ ] 5. 构建原局十神节点和完整有向关系图
  What to do / Must NOT do: 新增 `engine/predicates/ten_god_relation_graph.py`，从现有藏干、透干、根气、旺衰和位置证据构造日主 + 十神节点，并为所有实际节点对计算 generate/control/controlled_by/generated_by/same-family/combine 候选 edge。节点强度必须区分 presence、rooted、exposed、effective_strength，不能用简单计数代替；edge 保留 fact refs。该层只描述事实，不直接命名吉凶结构。
  Parallelization: Wave 2 | Blocked by: 2 | Blocks: 6-9
  References: `engine/predicates/ten_god_profile.py`; `engine/predicates/ten_god_structure_core.py`; `engine/predicates/relations.py`; `engine/predicates/types.py`; `tests/predicates/test_ten_god_structures.py:36-119`.
  Acceptance criteria: `pytest tests/predicates/test_ten_god_relation_graph.py -q` passes；日主 + 十神 11 节点的 110 个非 self 有向关系位每一对都有确定 relation 或显式 none reason；同一命盘重复构图 canonical hash 稳定；藏而无根、透而无根、得根透出强度顺序符合契约。
  QA scenarios: happy: 合成盘覆盖五条相生链和五条相克链；failure: 仅共现但无有效强度的角色不得生成 active edge，缺日主/非法柱返回 unsupported。Evidence `.omo/evidence/task-5-ten-god-structure-production-closure.txt`.
  Commit: N | feat(relation-graph): no commit without user authorization

- [ ] 6. 实现 13 个流通/护卫结构 recipe evaluator
  What to do / Must NOT do: 新增 `engine/predicates/ten_god_structure_recipes.py`，用受控 operator 评估 Todo 3 的 13 个流通/护卫结构。每项必须检查方向、有效强度、根透、日主承载和阻断；复合链要求每条 edge 连续有效。财滋杀必须根据身杀平衡区分 established 与转入 `wealth_aids_killing_attack`；食神配印必须区分正印扶身与枭夺食；食伤泄秀必须要求身旺可泄。
  Parallelization: Wave 3 | Blocked by: 2, 3, 5 | Blocks: 9, 10, 13, 14
  References: `theory/ziping/index.yaml:453,1308,1348,1426,1542`; `theory/tiaohou_ditiansui/index.yaml:27336`; `engine/predicates/ten_god_structure_core.py`; `engine/predicates/ten_god_structure_types.py`.
  Acceptance criteria: `pytest tests/predicates/test_ten_god_structure_flow_recipes.py -q` passes，13 项每项至少一成立、一潜伏、一阻断场景；复合链缺任一 edge 不成立；同一事实不能同时输出互斥的 favorable 与 destructive 结论。
  QA scenarios: happy: 参数化 13 项 fixture 全部命中预期；failure: 纯共现、方向反转、无根、身弱不任、关键 edge 被冲坏分别降为 latent/disrupted。Evidence `.omo/evidence/task-6-ten-god-structure-production-closure.txt`.
  Commit: N | feat(flow-structures): no commit without user authorization

- [ ] 7. 实现 5 个制化和 3 个取清 specialized evaluator
  What to do / Must NOT do: 保留并推广现有三结构强弱/损伤逻辑，在 `engine/predicates/ten_god_structure_specialized.py` 实现食神制杀、伤官驾杀、羊刃驾杀、劫财合杀、伤官合杀，以及官杀混杂、官杀去留取清、伤官伤尽。`officer_killing_cleared` 必须输出 resolution：`remove_officer_keep_killing/remove_killing_keep_officer/combine_officer_keep_killing/combine_killing_keep_officer`；合杀必须验证实际天干合、位置和力量，不得因角色共现判定。伤官伤尽必须同时处理调候例外为 diagnostic，而不是机械“无官即贵”。
  Parallelization: Wave 3 | Blocked by: 2, 3, 5 | Blocks: 9, 10, 13, 14
  References: `engine/predicates/ten_god_structures.py:39-126`; `engine/predicates/ten_god_structure_interactions.py`; `theory/ziping/index.yaml:14979-15060`; `theory/ziping/index.yaml:19275-19482`; `theory/tiaohou_ditiansui/index.yaml:3644`; `:12743`; `:305`; `:688`; `:788`.
  Acceptance criteria: `pytest tests/predicates/test_ten_god_structure_control.py tests/predicates/test_ten_god_structure_clearing.py tests/predicates/test_ten_god_structures.py -q` passes；8 项各有正反例；原三个公开 API 行为向后兼容；官杀混杂与已取清不能同层同时 established。
  QA scenarios: happy: 四种取清 resolution、三种制杀方式和伤官伤尽边界均可复现；failure: 合而不化、制化过度、官杀强弱反转、羊刃无根、调候要求官星时不得误报。Evidence `.omo/evidence/task-7-ten-god-structure-production-closure.txt`.
  Commit: N | feat(control-clearing): no commit without user authorization

- [ ] 8. 实现 9 个破坏/失衡结构和统一 blocker 优先级
  What to do / Must NOT do: 在 `engine/predicates/ten_god_structure_disruptions.py` 实现伤官见官、枭神夺食、财坏印、比劫夺财、财生杀攻身、制杀太过、官杀攻身、食伤泄身太过、印旺滞食。定义 precedence：具体破坏状态优先于同层 favorable statement，但不删除底层事实；例如枭夺食使食神制杀 disrupted，财坏印使官/杀印链 disrupted，制杀太过不能仍报制杀 established。输出 blocker refs 和 strength delta。
  Parallelization: Wave 3 | Blocked by: 2, 3, 5 | Blocks: 9, 10, 13, 14
  References: `theory/ziping/index.yaml:685,1268,1348,1426,1542,19275`; `theory/tiaohou_ditiansui/index.yaml:3644,16189,19203-19267`; `engine/predicates/ten_god_structure_interactions.py`.
  Acceptance criteria: `pytest tests/predicates/test_ten_god_structure_disruptions.py -q` passes；9 项各有成立/不成立边界；所有 favorable catalog 项至少有一个 blocker precedence 测试；无 mutually-exclusive 双重 established。
  QA scenarios: happy: 枭夺食、财坏印、比劫夺财沿依赖图传播到受影响结构；failure: 轻微无根干扰不应强制破坏，破坏源被制伏时结构可恢复为 stable/established。Evidence `.omo/evidence/task-8-ten-god-structure-production-closure.txt`.
  Commit: N | feat(disruptions): no commit without user authorization

- [ ] 9. 对 30 项结构统一叠加大运和显式流年
  What to do / Must NOT do: 重构 `engine/predicates/ten_god_structures.py` 为 orchestration：原局关系图只构建一次；每步大运在原局图上 overlay 一次并批量评估 30 项；每个 requested year 在所属大运图上 overlay 一次。新增 `assess_ten_god_structures()`，年份升序去重；现有单结构/单年份入口投影兼容。phase 只能按契约从 natal 到 completed/enhanced/stable/disrupted，再到 explicit liunian activated/stable/disrupted；不得为每结构重复扫描大运或读取时钟。
  Parallelization: Wave 4 | Blocked by: 2, 3, 5-8 | Blocks: 13, 14, 16
  References: `engine/predicates/ten_god_structures.py:39-126`; `engine/predicates/cycles.py`; `tests/predicates/test_ten_god_structures.py:120-213`; `engine/v5/domain_slices/context.py:20-28`（禁止复用）.
  Acceptance criteria: `pytest tests/predicates/test_ten_god_structure_bundle.py tests/predicates/test_ten_god_structure_cycles.py -q` passes；30 项共享每层单图；`(2030,2026,2026)` 归一化；空年份永远无 liunian；大运补全绝不改写 natal phase。
  QA scenarios: happy: 一个盘同时展示多结构在两步大运、两显式流年的补全/强化/破坏；failure: 年份不在大运范围只给 diagnostic，bool/越界年报错，系统年和输入“当前位置”不影响空年份输出。Evidence `.omo/evidence/task-9-ten-god-structure-production-closure.txt`.
  Commit: N | feat(cycle-overlay): no commit without user authorization

- [ ] 10. 用 namespaced trigger 和 typed RuleActivation 统一生产激活
  What to do / Must NOT do: 定义 `RuleActivation` 与 `ProductionTriggerContext`；`ProductionRuleLibrary.activated_rules()` 返回 rule + activation，旧 `triggered_rules()` 为兼容投影。loader 允许当前 11 个 legacy trigger 和 `ten_god_structure/<catalog-id>`，并把原三个 trigger alias 规范化；对于 executable structure mapping，`effective_trigger` 必须是 namespaced trigger并优先于 production index 中保留审计的 `source_trigger`，未映射规则才继续使用 legacy trigger。修改 `engine/predicates/condition_evaluator.py`，为 production 增加 strict deny-unknown 路径；兼容 pipeline 和 V5 的 production selection 都必须调用同一 `RuleActivation` 服务，V5 不得再让该文件的 legacy `return True` 放行 unknown。未知 namespace/ID、未知 legacy production trigger、未映射规则、非 general principle、phase 不允许都失败关闭。activation 保存 structure_id/family/layer/phase/resolution/dayun/year/evidence hashes。`has_liunian` 仅由 requested years 激活；不得全局改变非生产规则家族行为，不得改写大体积 theory index。
  Parallelization: Wave 4 | Blocked by: 2-4, 6-8 | Blocks: 13, 14
  References: `engine/application/production_rule_models.py:60-176`; `engine/application/production_rule_loader.py:52-91`; `engine/application/production_rule_triggers.py:24-151`; `engine/predicates/condition_evaluator.py:129-165`; `tests/test_production_rule_loader.py:22-109`.
  Acceptance criteria: `pytest tests/test_production_rule_loader.py tests/test_production_rule_activation.py tests/v5/test_ten_god_structure_integration.py -q` passes；30 个合法 namespace trigger 可解析；同规则不同 layer/cycle/year activation identity 稳定且不同；兼容 pipeline 与 V5 对同一组 unknown namespaced/legacy production triggers 都返回未激活。
  QA scenarios: happy: 一个通则映射两个 structure_id 时产生两个独立 activation，namespaced effective trigger 覆盖其 legacy source trigger并保留审计值；failure: case excerpt、digest 漂移、unknown ID、空年份 liunian、未映射 quantifiable rule 均不激活。Evidence `.omo/evidence/task-10-ten-god-structure-production-closure.txt`.
  Commit: N | refactor(rule-activation): no commit without user authorization

- [ ] 11. 新增 V5 命盘到关系图输入的严格 adapter
  What to do / Must NOT do: 新增 `engine/v5/ten_god_structure_adapter.py`，只从四柱和显式 `dayun_steps` 构造 evaluator 输入；requested years 由调用方单独传入。不得读取 chart 的 `current_year/as_of_date/liunian_steps` 或 six-source context。完整四柱无大运返回 natal-only supported；缺失、空白、下划线或非法干支返回 unsupported，不生成 claims。
  Parallelization: Wave 1B | Blocked by: 1 | Blocks: 14
  References: `engine/decision/v5_adapter.py:54-75`; `engine/v5/domain_slices/context.py:20-28`; `tests/test_decision_v5_adapter.py:71-88,143-169`.
  Acceptance criteria: `pytest tests/v5/test_ten_god_structure_adapter.py -q` passes；chart 含 current/as-of/liunian 数据但 requested years 为空时年度请求仍为空；dayun 顺序和区间严格校验。
  QA scenarios: happy: 完整四柱 + 两运 + 两明确年份可适配；failure: 缺时柱、非法干支、重叠大运、隐式年份分别 unsupported/报错且无 claim。Evidence `.omo/evidence/task-11-ten-god-structure-production-closure.txt`.
  Commit: N | feat(v5-adapter): no commit without user authorization

- [ ] 12. 扩展 statement context 和共享报告投影
  What to do / Must NOT do: `engine/statement_runtime.py` 增加严格 `structure_context`：structure_id/family/layer/phase/resolution/dayun/year/activation_key/evidence_hashes；稳定 ID 包含周期身份。新增 `engine/application/ten_god_structure_projection.py`，为报告按四类分组，只展示 active/latent/disrupted 的高信号结构，不把 30 个 absent 项堆进正文；支持无大运、无年份、unsupported。兼容 renderer 与 V5 report view 共用 DTO；output linter 禁止内部 ID/hash 泄漏。
  Parallelization: Wave 2 | Blocked by: 1-3 | Blocks: 13-15
  References: `engine/statement_runtime.py:18-185`; `tools/render_report.py:1779`; `engine/v5/report_view.py`; `tests/v5/test_report_view.py:147-168`; `tests/test_report_template_contract.py:161-170`; AGENTS.md 5.2.
  Acceptance criteria: `pytest tests/test_ten_god_structure_statement_runtime.py tests/test_ten_god_structure_report_projection.py tests/v5/test_report_view.py -q` passes；30 项 label 都可投影；absent 不刷屏；无年份不出现流年小节；内部字段零泄漏。
  QA scenarios: happy: 四类各一成立/破坏结构生成简洁表；failure: liunian 缺 year、cleared 缺 resolution、dayun 缺 range 被拒，故意注入 ID/hash 被 linter 阻断。Evidence `.omo/evidence/task-12-ten-god-structure-production-closure.txt`.
  Commit: N | feat(report-statement): no commit without user authorization

- [ ] 13. 接入兼容 pipeline 而不改变默认入口
  What to do / Must NOT do: 给 `run_pipeline/run_pipeline_e2e/integrate` 增加 keyword-only requested years；每次运行一次生成关系图和 30 项 bundle，注入 `AnalysisOutput`，再用 activated rules 生成带层级 context 的断语和 statement records。同一规则映射多个结构时按 structure_id 分开挂载证据，但展示 statement 使用目录投影而非重复整段原始 rule output。保留 `engine/pipeline.py` 默认入口与旧无参行为；不得从 analysis_date、retrospective 或输入文本取年。
  Parallelization: Wave 5 | Blocked by: 2, 6-10, 12 | Blocks: 16
  References: `engine/application/pipeline_runner.py:33-108`; `engine/application/integration.py:171,286-294`; `engine/domain/analysis.py:182`; `engine/pipeline.py:1-71`.
  Acceptance criteria: `pytest tests/test_ten_god_structure_pipeline.py tests/test_production_rule_loader.py -q` passes；旧调用无年度层，新调用只含请求年份；报告/statement 与 bundle 对 30 项 canonical ID 一致；大运补全不冒充原局。
  QA scenarios: happy: 同盘空年份与 2026 对比只差年度层；failure: monkeypatch 系统年、输入带“当前位置”、retrospective 存在时结构 bundle 不变。Evidence `.omo/evidence/task-13-ten-god-structure-production-closure.txt`.
  Commit: N | feat(pipeline): no commit without user authorization

- [ ] 14. 接入 V5 筛选、输出和 hash 而不做生产切换
  What to do / Must NOT do: 给 V5 claim builders、`run_v5/run_v5_snapshot` 增加 requested years；经 adapter、共享 graph/evaluator、activation service 选规则。V5 production path 不再直接依赖 `condition_evaluator.evaluate_trigger()` 的 fail-open 默认值；必须走 Todo 10 的 strict RuleActivation。`quantifiable` 只允许转 claim，不再是充分触发条件。claim metadata 保存 structure/layer/phase/resolution/cycle/year；输出和 snapshot 持久化 graph 摘要与 bundle并纳入 hash；显式 external claims 仍可覆盖默认 claims，但 bundle 独立计算。
  Parallelization: Wave 5 | Blocked by: 2, 6-12 | Blocks: 16
  References: `engine/v5/runner.py:147-190,1187-1239`; `engine/v5/domain.py:370-470,651-689`; `engine/predicates/condition_evaluator.py:129-165`; `tests/v5/test_v5_contracts.py:196-282`.
  Acceptance criteria: `pytest tests/v5/test_ten_god_structure_integration.py tests/v5/test_v5_contracts.py -q` passes；兼容与 V5 canonical bundle 相等；无 explicit years 无 annual claim；tamper graph/bundle 后 snapshot hash 失败。
  QA scenarios: happy: 四类结构在 natal/dayun/liunian claim metadata 正确；failure: unknown trigger、unmapped quantifiable、incomplete pillars、current_year-only chart 均无结构 claim。Evidence `.omo/evidence/task-14-ten-god-structure-production-closure.txt`.
  Commit: N | feat(v5): no commit without user authorization

- [ ] 15. 建立结构反馈候选账本、隔离 ingest 和只读指标
  What to do / Must NOT do: 新增 `engine/application/ten_god_structure_feedback.py` 和 `tools/ten_god_structure_feedback_status.py`；feedback ingest 发现 structure_context 时写 `META/ten-god-structure-feedback-candidates.jsonl` 并从 generic fanout 排除。维度固定 structure/phase/blocker/timing/resolution，verdict 固定 hit/partial/miss/unknown/skipped；candidate_id 稳定、重复摄入幂等、既有行不改。指标按结构/类/层/维度输出 N 和比例，样本不足不宣称准确率；普通反馈路径不变。
  Parallelization: Wave 4 | Blocked by: 12 | Blocks: 16
  References: `tools/feedback_ingest.py:273-378,925-989`; `engine/application/minimal_learning_loop.py:135-214`; `engine/contracts/05-rule-lifecycle.md`; `engine/contracts/06-confidence-model.md`.
  Acceptance criteria: `pytest tests/test_ten_god_structure_feedback_ledger.py tests/test_ten_god_structure_feedback_ingest.py -q` passes；重复 ingest 文件字节不变；结构反馈不改权重/lifecycle；30 项均可统计但零样本只报 N=0。
  QA scenarios: happy: temp ledger 摄入四类结构和取清 resolution 反馈；failure: 非法 context/verdict、缺 hash、重复 candidate、普通反馈误分流均被测试捕获。Evidence `.omo/evidence/task-15-ten-god-structure-production-closure.txt`.
  Commit: N | feat(feedback): no commit without user authorization

- [ ] 16. 接入目录闭包门禁、工具注册和只读双入口 replay
  What to do / Must NOT do: 新增 `tools/ten_god_structure_replay.py`，支持 compatibility/v5/both、重复 requested year、stdout 或显式输出；拒绝写 `cases/`/`reports/`。在 `tools/tool_registry.py`、`tools/README.md` 注册 inventory/status/replay。建立端到端 gate：目录 30、aliases 全分类、recipe/specialized coverage 30/30、报告 labels 30/30、两个入口 canonical bundle 相等、cases/reports 前后状态不变。
  Parallelization: Wave 6 | Blocked by: 4, 9, 13-15 | Blocks: final verification
  References: `tools/tool_registry.py`; `tools/README.md`; `cases/C-2026-001-乾-庚申戊寅壬子辛丑/input.md`; `tests/test_project_metadata.py`; `AGENTS.md` sections 5.4-5.6.
  Acceptance criteria: `pytest tests/tools/test_ten_god_structure_tools.py tests/integration/test_ten_god_structure_closure.py -q` and `python tools/tool_registry.py --check` pass；closure JSON 明确 `relation_nodes=11/relation_directed_pairs=110/relation_missing=0/catalog=30/evaluated=30/mapped_unclassified=0/report_labels=30`；双入口 bundle hash 一致。
  QA scenarios: happy: 真实 case 只读双入口 replay + 2026/2030 输出到 `.omo/evidence/`；failure: 第 31 项、missing evaluator、unclassified alias、输出指向 cases/reports、两个入口漂移均使 gate 非零。Evidence `.omo/evidence/task-16-ten-god-structure-production-closure.txt`.
  Commit: N | feat(closure-tools): no commit without user authorization

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit: 逐条核对 16 个 todo、30 项目录、关系图全覆盖、零未分类门禁、strict trigger、显式年份与反馈隔离；运行聚焦测试集合并记录 `.omo/evidence/f1-ten-god-structure-production-closure.txt`。Verdict 必须为 APPROVE。
- [ ] F2. Code quality review: 审查目录与代码单一事实源、typed operator 安全、类型边界、序列化兼容、hash 覆盖、每层关系图复用、异常吞噬与 dirty-worktree 合并风险；运行 `python -m compileall engine tools tests` 和全量 `pytest tests/ -q`，记录 `.omo/evidence/f2-ten-god-structure-production-closure.txt`。Verdict 必须为 APPROVE。
- [ ] F3. Real manual QA: 读取 Todo 1 的 `.omo/evidence/preflight-worktree-baseline.json`，先重算 `cases/`、`reports/` 全文件树的路径/类型/大小/SHA-256 并确认与 baseline 完全一致；再运行 `python -m tools.ten_god_structure_replay "cases/C-2026-001-乾-庚申戊寅壬子辛丑/input.md" --engine both --requested-year 2026 --requested-year 2030 --output .omo/evidence/f3-ten-god-structure-replay.json`，随后再次重算并做结构化比较。两个入口 canonical bundle 必须相等，且 replay 前后及相对 preflight baseline 均无 `cases/`/`reports/` 新增、删除、重命名、状态或 hash 变化；单纯比较两次已有大量未跟踪文件的 status 不算证明。证据 `.omo/evidence/f3-ten-god-structure-production-closure.txt`。Verdict 必须为 APPROVE。
- [ ] F4. Scope fidelity: 读取 baseline 中的精确 `allowed_pathspecs`，用 `git status --porcelain=v1 -z --untracked-files=all` 枚举当前全部变化；只把 baseline 后新增或变化且命中 allowlist 的路径归入本计划 diff，对这些明确 pathspec 运行 scoped `git diff --name-status`、`git diff --check` 和未跟踪文件内容校验。逐个重算 baseline 中所有 out-of-scope 脏文件的类型/大小/SHA-256，任何变化或任何 allowlist 外新增/删除/重命名都拒绝 APPROVE；不得用全局 `git diff --name-only` 冒充范围证明。另扫描结构 allowlist 不存在 `as_of_date`、系统年、未来三年推导、动态 eval、运行时中文推断、未登记第 31 项或自动 promotion。证据 `.omo/evidence/f4-ten-god-structure-production-closure.txt`。Verdict 必须为 APPROVE。

## Commit strategy
- 本计划不创建 commit、branch、push 或 PR；工作区已有大量无关修改，执行器只能按 todo 的明确路径编辑和验证。
- 每个 todo 完成时仅记录 scoped diff 与证据，不 stage 文件。用户后续若要求提交，再单独审查 diff 并按独立授权处理。
- 禁止为获得干净状态而 reset/clean/checkout；遇到同文件用户修改时以当前内容为基线做最小 patch。

## Success criteria
- 十神关系图覆盖全部角色对；首版目录精确 30 项，四类计数 13/5/3/9，recipe/specialized evaluator、理论映射、报告 label 和反馈结构均达到 30/30。
- 理论 inventory 对目录 aliases 的 candidate 未分类数为 0；新增语料或术语若未映射会使 gate 失败，不能静默落入执行层。
- 30 个结构在原局、大运、显式流年上的 phase、blocker 和取清 resolution 可区分、可序列化、可追溯，兼容 pipeline 与 V5 的 canonical bundle 完全一致。
- 未传 `requested_years` 时，任何入口都不生成流年结构、流年 activation 或结构流年报告内容；chart/current text/system clock 不能改变这一结果。
- 无大运仅给原局；不完整四柱返回 unsupported 且无结构 claims；大运补全永不标为 natal established。
- 生产规则只通过 11 个 legacy trigger 或受校验的 `ten_god_structure/<catalog-id>` + 显式 mapping + allowed phase 激活；unknown、未映射、案例语料和仅 quantifiable 规则均失败关闭。
- `AnalysisOutput`、`V5Output`、`V5RunSnapshot` round-trip 正确，V5 hash 覆盖关系图摘要与结构 bundle，旧 payload 和原三个公开结构 API 向后兼容。
- 报告呈现结构、层级、证据、blocker 和明确应期且不泄漏内部 ID；statement records 可稳定绑定原局/大运/流年反馈。
- 结构反馈仅追加独立候选账本，重复摄入幂等，不改变规则生命周期、置信度或权重；只读指标明确样本量。
- 每个目录结构至少有成立、潜伏/阻断和岁运转换测试；互斥 favorable/destructive 状态不能同层双重 established。
- 聚焦测试、全量测试、compileall、inventory closure、工具 registry、真实案例双入口 replay 和四路最终审查全部通过；`cases/`、`reports/` 全树与 preflight baseline 的路径/类型/大小/SHA-256 完全一致，且 baseline 中所有范围外脏文件内容未变。
