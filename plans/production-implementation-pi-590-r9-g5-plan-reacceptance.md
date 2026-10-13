# PI-590-R9 · G5 PI-500 独立计划复验报告

## 1. 身份与边界

- 复验身份：PI-590-R9 G5 新鲜静态复验者；不继承 PI-500 修复声明，也不把 R8 结论当作当前闭合证据。
- 目标：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)。
- finding baseline：[`production-implementation-pi-590-r8-g5-plan-reacceptance.md`](production-implementation-pi-590-r8-g5-plan-reacceptance.md)。
- canonical/frozen comparison：[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md)、[`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md)、[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md)、[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md)。
- 写入边界：仅本报告。
- 明确未执行：Python、pytest、collection、计划片段、YAML、mapping、Git、CLI、PowerShell、实现或运行时验证均未执行；任何静态计数与文本闭合均不等于 parse、collection 或 runtime 证明。

## 2. 方法

1. 重新读取目标计划、R8 finding baseline 与四份 canonical/frozen 计划。
2. 以 canonical 文档为类型所有权和语义事实源，不以 PI-500 的“已修复”记录作为证明。
3. 对 R8 H-1/H-2 做直接文本复核，并特别沿 Python 模块初始化顺序检查 conftest、scenario-data、matrix harness 和 adapter-reachability 的 literal-copy 边界。
4. 对既往闭合面逐项回归：31 个顶层 multiline component tests、五路 T01–T104 静态库存、局部 guards、T72/T92/T93/T97、request→RunTrack、feedback precedence/protocol、digest、F08/F09、六维门、双轴边界、state/event 与 production-default isolation。
5. 使用零缺陷、fail-closed 规则：任一 High、Medium、关键歧义、关键证据缺口、canonical/frozen 冲突、架构/授权冲突或相关回归非零，整体即被阻断；已闭合项不得抵销开放项。

## 3. 机械证据表

| 检查面 | 直接文本证据 | R9 结论 |
|---|---|---|
| 七个 Enum 声明 | PI-500 的七个 Enum 均为合法多行 class body，成员均显式赋值；其中 `RunTrack` 位于目标计划第 107–112 行，其他 canonical enums 紧随其后。 | 闭合 |
| canonical RunTrack 值域 | `PRODUCTION_DEFAULT / PARALLEL_DOMAIN / STAGED_L6 / V5_V6_PREPROD / MANUAL_IMPORT` 五值与 PI-210 一致；全局约束明确 PI-210 sole owner，request mode 不进入 canonical track 字段。 | 闭合 |
| decorator/class 同行 | 修复后的可见声明均为 decorator 与 class 分行；未发现仍保留的同行声明。 | 闭合 |
| Task 10 closed write set | PI-500 第 1087–1091 行明确包含 `tests/f09/test_f09_adapter_reachability.py`，且仅限 `tests/f09` 下测试、fixture、scenario data。 | 闭合 |
| Task 10 commit list | PI-500 第 1165 行 `git add` 列表包含同一路径；随后要求 staged path 全部位于 `tests/f09/`。 | 闭合 |
| 31 个 adapter tests | 目标计划第 2618–3308 行可见 trace=10、artifact=10、feedback=11，共 31 个显式顶层 multiline definitions；未用参数循环或生成器替代。 | 静态闭合；不证明 collection/runtime |
| nullable/index guards | 31-test block 对 nullable observation 与 tuple index 保留同测试内独立 `is not None`/cardinality 前置断言；trace adapter 也保留 pre-index shape guards。 | 静态闭合 |
| 五路 T01–T104 | marker rows、104 concrete mutator definitions、104 literal constructors、104 对应 mutator references、104-element literal `SCENARIOS` tuple 均连续覆盖 T01–T104。 | 静态库存闭合；不证明 AST/collection/runtime |
| T72 | manifest 输入保留 old `SUPERSEDED` 与 current `VERIFIED` 两个独立 identity，且 T72 row 要求 old/new auditable。 | 闭合 |
| T92 | event source 保留六个字段映射：level、change、interval start/end 及两端 inclusive。 | 闭合 |
| T93 | stimulus 交换 state/event source identities，固定 target graph 保持独立，用于拒绝对象/时态错配。 | 闭合 |
| T97 | 显式设置 mapping count=0 且 external termination=false，覆盖 mapping/terminal-edge 不完整。 | 闭合 |
| request→RunTrack | 唯一映射为 `STAGED_AUDIT -> STAGED_L6`、`PREPROD_SHADOW -> V5_V6_PREPROD`；production-default request 在 I/O 前拒绝。 | 闭合 |
| feedback aggregate | 明确按 `INVALID > AMBIGUOUS > UNBOUND > BOUND` first-match；protocol-required N/A 为 unbound，只有 protocol 明确允许的 N/A 才不阻断；source/target track provenance 与 anchor availability 正交。 | 闭合 |
| digest | canonical `DigestRef.algorithm` 构造文字为小写 `sha256`。 | 闭合 |
| F09/F08 与六维门 | F09-only；F08 identity/evidence/relation-only；resource/object/allocation/risk/attribution/tense 六维完整。 | 闭合 |
| axis/result boundary | allocation-only、risk-only 均 limited；只有 allocation+risk dual-axis 可支持 strong-primary scope。 | 闭合 |
| state/event | 独立对象 identity、独立 temporal model、独立 transformations；不得互换。 | 闭合 |
| production-default | opt-in 前置、staged/preprod artifact roots 隔离、production signatures/defaults 不变。 | 静态计划边界闭合；不证明运行时隔离 |
| literal-copy / module loading | conftest 的“完整 scaffolding”复制边界从第 1312 行 imports 开始，到第 2459 行 `mutate_t104` 返回结束；但 `VerticalScenario`、`ScenarioExecution`、`execute_scenario` 仅出现在第 1095–1155 行的早期 interface sketch，未出现在该 conftest literal-copy block；matrix assertion helpers 只有调用，没有定义。 | **开放阻断项** |

## 4. R8 findings closure

### R8 H-1

**部分闭合，但 finding 整体未闭合。**

已直接证明：

- 七个 Enum 的 class body 已改为合法显式赋值；
- canonical `RunTrack` 精确五值；
- decorator/class 同行模式已消除；
- 未发现新的 competing `RunTrack` 类型。

未闭合的同一验收面：

- R8 H-1 还要求 contracts、conftest、scenario-data 和 31-test literal-copy blocks 自包含，且不存在 undefined symbols、import cycle 假设或 hidden helpers。
- PI-500 自己把第 1312–2459 行声明为 `tests/f09/conftest.py` 的完整复制边界，并要求在 scenario-data import 前定义全部可反向导入符号；该边界没有定义 `VerticalScenario`、`ScenarioExecution` 或 `execute_scenario`。
- scenario-data 在第 2470–2485 行从 `tests.f09.conftest` 反向导入 `VerticalScenario` 与 104 mutators；mutators 在反向导入前可被绑定，但 `VerticalScenario` 不在合法 conftest copy boundary 内，因而不存在文本证明的可绑定来源。
- adapter-reachability 在第 2606–2616 行从 conftest 导入 `execute_scenario`，而完整 conftest block 未定义该符号。
- matrix harness 调用 `assert_action_and_state`、`assert_issue`、`assert_basis`、`assert_bindings`、`assert_side_effect_boundary`，目标计划没有给出这些 helper 的定义或合法 import；这与“no hidden helper”硬约束直接冲突。
- 早期 interface sketch 不能自动进入后文明确限定的 literal-copy module boundary。即使实现者自行把 sketch 搬入 conftest，也还缺少该类型所需 `Callable`、matrix 所需 `pytest` 以及五个 assertion helper 的完整、无歧义复制说明。

因此，R8 H-1 的语法子项已修复，但自包含/模块装载子项仍开放，不能宣告 H-1 closure。

### R8 H-2

**闭合。**

- closed write set 已包含 `tests/f09/test_f09_adapter_reachability.py`；
- commit path list 已包含同一路径；
- 授权没有扩到 `tests/f09` 之外；
- 若测试暴露实现缺口，计划要求停止 Task 10 并返回前序 owner 或另开单独授权任务，没有赋予 tests-only task 修改 production 的权限。

## 5. conftest / scenario-data 模块装载复核

计划声称的目标顺序是：

1. Python 初始化 `tests.f09.conftest`；
2. conftest 在导入 scenario-data 前绑定 scenario-data 需要的全部符号；
3. conftest 导入 `tests.f09.data.f09_vertical_scenarios`；
4. scenario-data 从 partially initialized conftest 反向导入 `VerticalScenario` 与 104 mutators；
5. scenario-data 构造 T01–T104 和 `SCENARIOS` 后返回；
6. matrix/reachability modules 使用 conftest exports。

这种 circular import 形状只有在步骤 2 已绑定全部反向导入名时才可能合法。文本能证明 104 mutators 在完整 conftest block 尾部已定义，却不能证明 `VerticalScenario` 已绑定；相反，明确复制边界排除了它。随后 reachability module 所需 `execute_scenario` 也未进入 conftest block。因此：

- 不能接受“complete scaffolding”这一作者声明作为 closure evidence；
- 不能从早期 interface prose 推断实现者应自行拼接哪些片段；
- 不能证明 module-loading path 无 undefined import；
- 不能证明 matrix harness 的承载模块：若把 harness 追加到 conftest，计划未证明其作为 test node 的 collection；若放入 `test_f09_vertical_matrix.py`，又缺少一个完整、明确的该模块 literal-copy/import boundary。

本结论是静态计划缺陷判断，不是实际 ImportError、collection error 或 runtime failure 的执行证据。

## 6. 完整回归矩阵

| 回归面 | 状态 | 边界说明 |
|---|---|---|
| R8 Enum syntax | 已修复 | 仅静态文本 |
| R8 decorator/class layout | 已修复 | 仅静态文本 |
| R8 Task 10 reachability authorization | 已修复 | 仅计划授权，不代表文件已创建 |
| canonical RunTrack one-owner/five-value semantics | 保持 | 未发现 local alias enum |
| 31 tests，10/10/11 | 保持 | 定义库存，不是 collected/passed count |
| local nullable/cardinality guards | 保持 | 未执行 falsifier |
| five T01–T104 inventories | 保持 | 可见 source-text inventory，不是 AST/collection proof |
| T72 | 保持 | old/current identity 语义未回退 |
| T92 | 保持 | 六 event mappings 未回退 |
| T93 | 保持 | state/event 独立性未回退 |
| T97 | 保持 | mapping/termination failure stimulus 未回退 |
| request mapping | 保持 | canonical track 与 request token 分离 |
| feedback precedence/N/A/provenance | 保持 | first-match 与正交性未回退 |
| lowercase sha256 | 保持 | 未发现 canonical constructor 使用替代 token |
| F09-only/F08 identity-only | 保持 | 未扩展 F08 决策职责 |
| six dimensions | 保持 | declaration/member/record 仍要求 bijection |
| allocation/risk/dual-axis boundary | 保持 | strong-primary 仍限 dual-axis |
| state/event separation | 保持 | identity 与 temporal model 仍独立 |
| production-default unchanged | 保持 | 静态 non-goal/guards；无 runtime proof |
| self-contained copy/import boundary | **回归/开放** | 新复制边界修复声明未实际纳入必要 symbols/helpers |

## 7. Findings 分类

### PI590R9-H-01 — Task 10 literal-copy scaffolding 非自包含，模块装载路径无合法文本闭合

**观察事实**

1. 完整 conftest copy boundary 被明确定义为第 1312–2459 行。
2. `VerticalScenario`、`ScenarioExecution`、`execute_scenario` 只出现在边界外的 interface sketch。
3. scenario-data 明确从 conftest 导入 `VerticalScenario`。
4. adapter-reachability 明确从 conftest 导入 `execute_scenario`。
5. matrix harness 调用五个未定义、未导入的 assertion helpers。
6. 计划同时禁止 hidden helper、undeclared dependency 与 implementer inference。

**影响**

- implementation 无法仅依照声明的 literal-copy boundaries 构造自包含模块；
- partially initialized conftest 无文本保证可满足 scenario-data 的 reverse import；
- reachability tests 的 conftest import surface 不完整；
- matrix harness 的目标文件、imports、helpers 与 collection surface 存在关键歧义。

| 必须分类的类别 | 数量 | 说明 |
|---|---:|---|
| High | 1 | 直接击穿 R8 H-1 的 self-contained / undefined-symbol / no-hidden-helper acceptance 条件。 |
| Medium | 0 | 无需另立 Medium；同一原子缺陷已按 High 处理。 |
| critical ambiguity | 1 | interface sketch 是否应并入 conftest、matrix harness 应进入 conftest 还是 test module，均无唯一合法复制指令。 |
| key evidence gap | 1 | 缺少所有 required symbols 在各目标模块中定义或导入的直接文本证明。 |
| canonical/frozen conflict | 0 | 未发现 PI-210/220/230/300 语义本身发生冲突。 |
| architecture/authorization conflict | 1 | 声称 complete/no-hidden-helper 的模块架构与实际复制边界冲突；实现者若自行补片段将越过冻结计划的唯一指令。 |
| relevant regression | 1 | R8 remediation 新增“literal-copy closure”声明，但实际仍留下未绑定符号与承载模块歧义。 |

除 PI590R9-H-01 外，本轮未识别独立的开放 Medium 或 canonical/frozen semantic conflict；但零缺陷门槛已被该 High 单独击穿。

## 8. 唯一最小修复路径

只修订 PI-500 的 Task 10 scaffolding，不修改 canonical plans、production code、tests 或其他文件：

1. 给出唯一、连续、可逐字复制的 `tests/f09/conftest.py` block；在其 scenario-data import 之前显式定义或合法导入 `VerticalScenario`、`ScenarioExecution`、`execute_scenario`，并补齐 `Callable` 等全部 imports。
2. 给出唯一、连续、可逐字复制的 `tests/f09/test_f09_vertical_matrix.py` block；显式导入 `pytest`、`SCENARIOS`、`VerticalScenario`、`execute_scenario` 与所有五个 assertion helpers。
3. 五个 assertion helpers 必须在某个明确目标模块的完整复制边界内逐一定义，或从一个已在 Task 10 closed write set/前序任务中明确拥有它们的模块逐一导入；不得依赖 prose、通配导入或实现者推断。
4. 保持 scenario-data 在 conftest 所有 reverse-import symbols 已绑定后才被导入；逐项列出并验证该反向 import surface。
5. 保持已闭合内容不变：七 Enums、五值 RunTrack、Task 10 四路径授权、31 tests、五路 T01–T104、guards 与全部 frozen semantics。
6. 修订后必须由新的独立 reviewer 重新静态复验；本报告不授权实现、parse、collection、pytest 或 runtime 执行。

这是一个原子修复路径：闭合 Task 10 的三个目标模块及其 import/export ownership；无需改变业务契约或扩大 tests-only 授权。

## 9. 直接证明与未证明边界

### 直接证明

- R8 Enum body 与 decorator/class 语法修复已经体现在目标文本中。
- R8 H-2 的 closed write set、commit list 与 `tests/f09` 窄授权已经体现在目标文本中。
- 31 个 component test definitions 及 10/10/11 分组可从计划文本直接盘点。
- 五路 T01–T104 静态库存和指定 frozen semantics 在计划文本中保持。
- conftest 完整复制边界没有包含 required scenario/harness symbols，且 downstream blocks 明确导入/调用这些 symbols。

### 未证明

- 任何 fenced Python block 可 parse。
- pytest 能导入或 collect 任一 module/node。
- 104 matrix nodes、31 component tests 或 105 expected passes 实际存在于仓库测试文件中。
- 任一 test 通过。
- import cycle 在真实 Python module initialization 中成功。
- production-default 行为在运行时确实不变。
- artifact、trace、feedback、digest、source locator 或 state/event 行为在运行时正确。
- G5 已完成、可冻结或可由本复验者推进到下一 Gate。

## 10. 裁决

# BLOCKED

PI590R9-H-01 使 High、critical ambiguity、key evidence gap、architecture conflict 与 relevant regression 均非零。根据零缺陷 fail-closed 规则，其他闭合面不能抵销该开放 finding。只有父实例可在完成最小修复并取得新的独立静态复验后重新裁决 G5；本报告既不授权修复，也不提供 parse、collection 或 runtime 证明。
