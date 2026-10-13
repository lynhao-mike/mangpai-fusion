# PI-590-R8 · G5 实施计划最终静态复验报告

## 1. 审查身份、范围与边界

本报告是一次全新、独立、角色分离、fail-closed 的 G5 静态复验。结论以 canonical plans 与最终 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) 正文为证据；[`production-implementation-pi-590-r6-g5-plan-reacceptance.md`](production-implementation-pi-590-r6-g5-plan-reacceptance.md)、[`production-implementation-pi-590-r7-g5-plan-reacceptance.md`](production-implementation-pi-590-r7-g5-plan-reacceptance.md) 及 PI-500 尾部 remediation records 仅作为待复验 claims / finding baseline，不作为关闭证据。

### 1.1 审查对象

- Canonical 事实源：
  - [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md)
  - [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md)
  - [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md)
  - [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md)
- 前置技术基线：
  - [`production-implementation-pi-390-r4-g3-reacceptance.md`](production-implementation-pi-390-r4-g3-reacceptance.md)
  - [`production-implementation-pi-400-r4-g4-technical-rereview.md`](production-implementation-pi-400-r4-g4-technical-rereview.md)
- Claims / finding baseline：
  - [`production-implementation-pi-590-r6-g5-plan-reacceptance.md`](production-implementation-pi-590-r6-g5-plan-reacceptance.md)
  - [`production-implementation-pi-590-r7-g5-plan-reacceptance.md`](production-implementation-pi-590-r7-g5-plan-reacceptance.md)
- 主审对象：
  - [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)

### 1.2 明确未执行事项

本轮只进行了静态读取、静态文本搜索和本报告写入。未执行 Python、pytest、test collection、计划中的 Python 片段、YAML、mapping、Git、CLI 或 PowerShell；未修改 PI-500、canonical plans、R6/R7、总控、handoff 或其他文件。

因此，本报告只裁定计划文本能否通过 G5 静态接受，不构成运行证明、测试通过证明、实现授权、生产授权或自动完成 G5。

### 1.3 判定纪律

任一未关闭的 High、Medium、critical ambiguity、key evidence gap、canonical conflict、frozen semantic conflict、architecture violation 或 relevant regression，均强制唯一 verdict 为 BLOCKED。通过项不得抵消阻断项。

## 2. 执行摘要

R7 唯一 Medium 已按正文机械证据关闭：两个指定的 tuple direct indexes 前均已有准确、本地的长度断言，同函数其余 direct indexes 与 nullable member accesses 也有相应本地 guards。

R6 的五个 closure surfaces、R7 的两个旧 High、31 个 component tests、五路 T01–T104 inventory，以及 T72/T92/T93/T97、lowercase digest、F08/F09 边界等冻结语义，均获得了正向静态证据。

但是，本轮独立复验发现两个新的确定性 High：

1. PI-500 声称可直接实现或逐字复制的 fenced Python 接口包含不可用的 Enum 定义与非法 decorator/class 同行语法，破坏静态可复制性。
2. Task 10 的 closed write set 与后文强制要求创建的 31-test 文件互相冲突，不存在同时满足两项要求的合规实施路径。

任一 High 已足以单独触发 fail-closed BLOCKED。

## 3. 机械证据总表

| 核验面 | 要求 | PI-500 独立静态证据 | 结论 |
|---|---|---|---|
| R7 指定 tuple guard 1 | direct index 前有本地长度 guard | [`production_required_na.seven_matches[3]`](production-implementation-pi-500-r1-f09-implementation-plan.md:2961) 前有至少四项的本地断言 | 关闭 |
| R7 指定 tuple guard 2 | direct index 前有本地长度 guard | [`preprod_required_na.seven_matches[2]`](production-implementation-pi-500-r1-f09-implementation-plan.md:3011) 前有至少三项的本地断言 | 关闭 |
| 同函数其余 tuple indexes | 每个 direct index 前 fail closed | feedback item、manifest record、binding 的 index 前均有独立 cardinality assertion；slice 不误计为 direct index | 关闭 |
| 同函数 nullable accesses | member access 前有本地 non-null guard | submission 与 input manifest 均在 dereference 前分别断言非空 | 关闭 |
| Typed source/target track | typed facts 与 anchor availability 正交 | source/target 分别构造 typed binding；anchor 只控制 manifest record availability | 关闭 |
| T72 | 恰为 old/current 两记录 | [`manifest_records`](production-implementation-pi-500-r1-f09-implementation-plan.md:1688) 在 supersedes 分支取 old/current pair；component test 断言长度、顺序与状态 | 关闭 |
| 31 component tests | trace 10、artifact 10、feedback 11；顶层、多行、无隐藏生成 | 从首个 trace test 到末个 feedback test 静态枚举为 10/10/11；scope 内无参数化、循环、range、generator、registry、factory 或 table parser | 关闭 |
| Component guards | 全部 tuple index / nullable access 有本地 guard | 完整阅读 31-test block，未发现 residual unguarded direct index 或 nullable dereference | 关闭 |
| Trace pre-index | 所有索引前 shape guard | state fields、event fields、trace nodes、statements、card refs、evidence refs 均先检查 cardinality | 关闭 |
| Trace malformed coverage | malformed shape 必须 fail closed | short state/event 与 empty node/statement/card/evidence refs 各有 typed error 断言 | 关闭 |
| Canonical RunTrack 值域 | PI-210 sole-owner，精确五值 | 文本列出五个 canonical 名称，request token 不进入 canonical field；但其 runtime transcription 写法不可执行 | **语义值域关闭；静态复制 High** |
| Request mapping | 只允许两条边界映射 | Task 9 只声明 STAGED_AUDIT 到 STAGED_L6、PREPROD_SHADOW 到 V5_V6_PREPROD；production-default request 在 I/O 前拒绝 | 关闭 |
| Feedback aggregate | INVALID > AMBIGUOUS > UNBOUND > BOUND | oracle 使用显式 first-match，穷尽失败时抛 typed error，无 default BOUND | 关闭 |
| Required/allowed N/A | required N/A 为 UNBOUND；仅 allowed N/A 可满足 | protocol table分别列 required 与 allowed-not-applicable indexes；component tests覆盖 required/allowed 分支 | 关闭 |
| Protocol provenance | 来自 pre-call canonical target facts | binder call 不接收 fixture protocol；source/target binding 与 manifest/statement facts在调用前构造 | 关闭 |
| 五路 104 inventory | 每路精确 104，无重复、遗漏、错号 | mutator、constructor、同号 reference、complete pytest node、SCENARIOS membership 均连续 T01–T104 | 关闭 |
| T92 | 六 event mappings | adapter 显式形成六路 event mappings，未并入三路 state mappings | 关闭 |
| T93 | state/event identity 分账 | mutator 交换 source identities，validator graph 可观察 mismatch | 关闭 |
| T97 | mapping missing / external termination | mutator 在 validator 调用前置 mapping count 为零且 termination 为 false | 关闭 |
| Digest algorithm | lowercase sha256 | 可见 DigestRef constructors 的 algorithm literals 均为 lowercase sha256 | 关闭 |
| F08/F09 scope | F08 identity-only；F09 六维 | F08 仅作为竞争 identity reference；F09 保持六 gate dimensions | 关闭 |
| Outcome boundary | allocation-only、risk-only；strong-primary 仅双轴 | 单轴与双轴路径分账，未见借 F09 扩张结果域 | 关闭 |
| State/event | state 与 event 独立建模 | 三路 state mappings 与六路 event mappings 独立，identity 和时间语义不混写 | 关闭 |
| Production isolation | production-default unchanged；F09-only | opt-in 前校验、disabled zero-I/O、正常 production entrypoints 不引入 F09 | 关闭 |
| Python 静态可复制性 | fenced interfaces 能按计划落入模块 | 七个 Enum 使用无赋值裸名称；六个 dataclass decorator 与 class 同行 | **High，未关闭** |
| Task 10 write boundary | 必需产物必须全部位于 closed write set | closed write set 未包含后文强制要求的 adapter reachability test 文件 | **High，未关闭** |

## 4. R7 唯一 Medium 的独立复验

### 4.1 两个指定 direct indexes

第一个位置的顺序为：先断言 [`len(production_required_na.seven_matches) >= 4`](production-implementation-pi-500-r1-f09-implementation-plan.md:2960)，再读取 [`production_required_na.seven_matches[3]`](production-implementation-pi-500-r1-f09-implementation-plan.md:2961)。

第二个位置的顺序为：先断言 [`len(preprod_required_na.seven_matches) >= 3`](production-implementation-pi-500-r1-f09-implementation-plan.md:3010)，再读取 [`preprod_required_na.seven_matches[2]`](production-implementation-pi-500-r1-f09-implementation-plan.md:3011)。

两项 guard 均与目标 tuple 相同、位于同一 test、紧邻目标访问之前，满足准确且本地的要求。

### 4.2 同函数其余 tuple indexes

静态逐项检查覆盖：

- submission feedback item 的首项访问；
- input manifest record 的首项访问；
- baseline、mutation 与三种 N/A observation 的 binding 首项访问。

每项 direct index 前均有对应 tuple 的独立长度断言。[`preprod_allowed_na.seven_matches[2:]`](production-implementation-pi-500-r1-f09-implementation-plan.md:2968) 是 slice，不会因 tuple 少于三项产生原生 IndexError，不属于本项 direct-index blocker。

### 4.3 同函数 nullable accesses

baseline 与 mutation 的 submission、input manifest 均在 member dereference 前有各自非空断言。未发现先访问 nullable member、后补 guard 的顺序错误。

**结论：R7 唯一 Medium 已关闭。**

## 5. PI-590-R6 五项 blocker closure

| # | R6 surface | 独立静态观察 | 状态 |
|---:|---|---|---|
| 1 | typed source/target track facts 与 anchor availability 正交 | source 与 target 分别由 typed track fact 构造；source/target state 不通过删 anchor 表达；anchor availability 仅改变 manifest records | 已关闭 |
| 2 | T72 恰为 old/current | supersedes 分支不再拼接 lifecycle 与 selected records；inspect/retry tests 均约束两条记录、顺序和状态 | 已关闭 |
| 3 | 31 个 multiline tests 精确 10/10/11 且无 hidden generation | 静态定义数为 31；全部为显式顶层多行 definitions；component scope 内无动态测试生成 | 已关闭 |
| 4 | 全部 tuple indexes / nullable accesses 有 local guards | R7 指定两处已补 guard；其余 component test direct indexes 与 nullable accesses 也有本地 guards | 已关闭 |
| 5 | trace adapter pre-index fail closed 且有 malformed coverage | 六类 shape checks 在索引前返回 typed observation；component tests覆盖全部六类 malformed input | 已关闭 |

R6 五项在本轮主审正文中均有关闭证据；该结果不抵消第 9 节的新 High findings。

## 6. R7 两项 High closure

### 6.1 Canonical RunTrack 语义面

PI-210 保持 sole semantic owner。PI-500 的边界文本仅列五个 canonical 值；STAGED_AUDIT 与 PREPROD_SHADOW 只作为 request modes，并通过唯一一组映射进入 STAGED_L6 与 V5_V6_PREPROD。production-default request 被要求在 I/O 前拒绝，未见 request token 写入 canonical typed fields，也未见第二组冲突映射或第二个有意扩展的 runtime identity。

因此，R7 所关注的所有权、值域、request boundary 和 identity 污染问题在语义设计层关闭。

但是，[`class RunTrack(str, Enum)`](production-implementation-pi-500-r1-f09-implementation-plan.md:102) 的具体 Python transcription 不可用。这是本轮新发现的静态复制 High，不得用“语义值名正确”替代“实现文本可复制”。

### 6.2 FeedbackBinding aggregate 与 protocol

静态正文显示：

1. aggregate oracle 按 INVALID、AMBIGUOUS、UNBOUND、BOUND 的 first-match 顺序判断；
2. 没有 default BOUND，未穷尽时抛 typed error；
3. production 与 preproduction protocol 各自显式列出 required 和 allowed-not-applicable dimensions；
4. required N/A 路径得到 returned binding 后再断言 UNBOUND，不由空返回绕过；
5. allowed N/A 在其他 required dimensions 满足时可 BOUND；
6. binder 调用不接收 fixture protocol，protocol 由 pre-call statement、run、track binding、statement set 与 manifest anchor 等 canonical target facts推导。

**结论：R7 两项旧 High 的语义 blocker 均关闭。**

## 7. 31 个 component tests 的静态计数与 guard 方法

### 7.1 计数方法

未执行 pytest collection。对 PI-500 的 “Thirty-one literal adapter component tests” fenced scope 逐项枚举顶层多行 test definitions，并按显式 trace、artifact、feedback 分区计数；同时在该 scope 内检查参数化 decorator、循环、range、generator、动态 ID、registry、factory、table parser 与共享 catch-all 结构。

### 7.2 结果

| Component | 首尾机械边界 | 顶层多行 definitions | Hidden generation |
|---|---|---:|---|
| Trace | [`test_trace_statement_set_complete_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2528) 至 [`test_trace_issue_propagation_ids_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2696) | 10 | 未发现 |
| Artifact | [`test_artifact_records_write_outcome_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2714) 至 [`test_artifact_retry_payload_digest_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2883) | 10 | 未发现 |
| Feedback | [`test_feedback_target_statement_id_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2898) 至 [`test_feedback_eligibility_complete_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:3216) | 11 | 未发现 |
| **合计** | — | **31** | **未发现** |

这只是静态 definitions count，不是 collectability 或 runtime pass 证据。

### 7.3 Guard 检查方法

对 31 个函数逐项检查两类风险：

- 每个 direct tuple index 的同函数前置 cardinality assertion；
- 每个 nullable member dereference 的同函数前置 non-null assertion。

trace adapter 另行检查所有 production pre-index branches，而不是只看 tests。结果未发现 R7 guard 修复之外的 residual guard 缺口。

## 8. 五路 T01–T104 inventory 与冻结语义

### 8.1 计数方法

未执行 AST、Python、mapping 或 collection。采用纯文本机械检查：

1. 确认每路首项为 T01、末项为 T104；
2. 沿连续编号逐项检查缺号与重复；
3. 对每个 constructor 比对 test ID、同号 mutator reference 与 pytest node suffix；
4. 对 literal SCENARIOS tuple 检查 T01–T104 成员连续性；
5. 不以搜索工具对连续匹配合并后的“结果块数量”作为计数。

### 8.2 五路结果

| Inventory | 首尾证据 | 数量 | 重复 | 遗漏 | 错号 / 错引用 |
|---|---|---:|---:|---:|---:|
| Concrete mutator definitions | [`mutate_t01()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2092) 至 [`mutate_t104()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2399) | 104 | 0 | 0 | 0 |
| Literal constructors | [`T01 = VerticalScenario(...)`](production-implementation-pi-500-r1-f09-implementation-plan.md:2412) 至 [`T104 = VerticalScenario(...)`](production-implementation-pi-500-r1-f09-implementation-plan.md:2515) | 104 | 0 | 0 | 0 |
| Constructor-to-mutator references | 每个 TNN constructor 引用同号 [`mutate_tNN()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2412) | 104 | 0 | 0 | 0 |
| Complete pytest nodes | 每个 constructor 包含完整 file、test function 与同号 parameter ID；末项见 [`T104 pytest_node`](production-implementation-pi-500-r1-f09-implementation-plan.md:2515) | 104 | 0 | 0 | 0 |
| Literal SCENARIOS entries | [`SCENARIOS`](production-implementation-pi-500-r1-f09-implementation-plan.md:2517) 显式列举 T01–T104 | 104 | 0 | 0 | 0 |

Marker-scoped scenario table同样连续列出 T01–T104，作为第六路文本交叉证据，但不替代上述五路 executable inventory。

### 8.3 关键冻结语义

- T72：[`mutate_t72()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2306) 指定 supersedes revision；artifact adapter 形成 old/current 两记录，未追加 current-like record。
- T92：[`mutate_t92()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2354) 提供六个 event fields；adapter 显式形成六路 event mappings。
- T93：[`mutate_t93()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2364) 交换 state/event object identities，使 mismatch 在 validator 前真实存在。
- T97：[`mutate_t97()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2382) 将 field mapping count 设为零并关闭 external-source termination，使缺映射/缺终止在调用前真实存在。
- DigestRef constructors 使用 lowercase sha256；未见 uppercase 或替代 algorithm token。
- F08 维持 identity-only；F09 保持六维、allocation-only、risk-only，strong-primary 只在双轴满足时成立。
- state 与 event 分账，production-default unchanged，实施 scope 保持 F09-only。

## 9. Findings 分类

### 9.1 High

#### H-1：fenced Python interface 不具备静态可复制性

PI-500 明确称 Task 1 的实现是 PI-210 五值的 “exact runtime transcription”，并把接口置于 Python fenced block，目标文件为 contracts module。但是七个 Enum declarations 从 [`class RunTrack(str, Enum)`](production-implementation-pi-500-r1-f09-implementation-plan.md:102) 到 [`class ArtifactSetState(str, Enum)`](production-implementation-pi-500-r1-f09-implementation-plan.md:108) 都以分号分隔裸名称，未给成员赋值。

这种类体不会建立预期 Enum members；类体求值第一个未定义裸名称时即失败。因此，它既不是五成员 RunTrack 的可用 runtime transcription，也不能作为可导入契约模块逐字复制。

此外，以下六个 declarations 把 decorator 与 class 放在同一物理行：

- [`FrozenFieldObservation`](production-implementation-pi-500-r1-f09-implementation-plan.md:260)
- [`IdempotencyKey`](production-implementation-pi-500-r1-f09-implementation-plan.md:860)
- [`ArtifactSetManifest`](production-implementation-pi-500-r1-f09-implementation-plan.md:890)
- [`F09RunRequest`](production-implementation-pi-500-r1-f09-implementation-plan.md:1016)
- [`F09Observation`](production-implementation-pi-500-r1-f09-implementation-plan.md:1017)
- [`F09RunResult`](production-implementation-pi-500-r1-f09-implementation-plan.md:1018)

Python decorator grammar 要求被装饰的 class 位于后续逻辑行；当前写法不能按所示文本解析为有效 declaration。

影响面不是排版偏好，而是 Task 1 canonical contracts、Task 3 frozen observation、Task 7 artifact identities 和 Task 9 application DTOs 的语法、导入与 runtime identity 均无法按计划落地。该缺陷确定、可机械定位，并直接阻断静态计划接受。

#### H-2：Task 10 closed write set 与必需 31-test 文件冲突

Task 10 的 closed write set 只允许：

- [`tests/f09/test_f09_vertical_matrix.py`](production-implementation-pi-500-r1-f09-implementation-plan.md:1036)
- [`tests/f09/conftest.py`](production-implementation-pi-500-r1-f09-implementation-plan.md:1037)
- 可选 [`tests/f09/data/f09_vertical_scenarios.py`](production-implementation-pi-500-r1-f09-implementation-plan.md:1038)

其 commit path list 再次只列这三个路径，见 [`Task 10 Step 8`](production-implementation-pi-500-r1-f09-implementation-plan.md:1112)。

但是，后文又强制要求把 31 个 definitions 逐字复制到第四个文件 [`tests/f09/test_f09_adapter_reachability.py`](production-implementation-pi-500-r1-f09-implementation-plan.md:2524)。

若遵守 closed write set，就不能创建必需 component-test 文件；若创建该文件，就违反 closed write set。正文没有给第四个文件独立 task owner、授权边界或 closed-set amendment。因此不存在同时满足两项强制要求的合规实施路径，构成确定性 architecture / authorization conflict。

### 9.2 Medium

无独立未关闭 Medium。R7 的 guard Medium 已由准确、本地 assertions 关闭。

### 9.3 Critical ambiguity

H-1 与 H-2 已有确定性正文证据，不需要降格为 ambiguity。另有一个不改变 verdict 的可复制边界歧义：若所谓 “literal copy” 只指 declaration body 而允许实施者自行补 import / module scaffolding，则多个 fenced scopes 的自足性标准不清；若指完整模块逐字复制，则可见 imports 不足。由于 H-1 的语法/runtime 失败和 H-2 的 write-set 冲突已独立成立，本项不作为唯一阻断依据。

### 9.4 Key evidence gap

计划文本不能证明几个 literal-copy scopes 自足：scenario-data block 未展示全部 imports，31-test block 也未展示 module import scaffolding。该缺口不影响 31/104 静态计数，但进一步阻止将计划文本视为可直接收集或可执行证明。

### 9.5 Canonical / frozen semantic conflict

除 H-1 的不可用 runtime transcription 外，未发现值域层面的新增 canonical drift：五个 RunTrack 名称、feedback first-match、required/allowed N/A、T72、T92/T93/T97、lowercase sha256、F08/F09 边界、六维、双轴 strong-primary、state/event 分账均保持冻结语义。

### 9.6 Relevant regression

R7 guard 缺陷未回归。新阻断项属于此前报告未裁出的静态可复制性与任务授权边界缺陷，而非已关闭 guard 的再次失败。

## 10. 最小有界整改面

本报告不修改 PI-500。要解除当前阻断，后续整改至少需要：

1. 将七个 Enum declarations 改为有效且值明确的成员赋值，同时保持 PI-210 sole ownership、精确五值和单一 runtime identity；
2. 将六个 decorator/class 同行 declarations 改为合法的多行 decorator + class 形式；
3. 为各 literal-copy module补齐明确 imports / scaffolding，或把“逐字复制”的精确边界写清；
4. 修正 Task 10 closed write set：要么明确纳入 adapter reachability test 文件，要么给该文件独立、前置、封闭的 authorized task；
5. 不改变 31 个 tests 的 10/10/11 分组，不改变五路 104 inventory，不弱化 guards，不漂移任何 canonical / frozen semantics；
6. 整改后必须由新的独立 reviewer 再做一次静态复验，不能由本报告预先授予 PASS。

## 11. 唯一 Verdict

# BLOCKED

阻断理由：PI-500 存在两个未关闭 High。其一，多个被表述为 exact runtime transcription / literal implementation 的 fenced Python declarations 不能形成有效、可导入的 Python contracts；其二，Task 10 的 closed write set 与必需的 31-test 文件路径互相冲突，不存在合规实施路径。依照 fail-closed 纪律，任一 High 已足以禁止 PASS。

R7 唯一 Medium、R6 五项、R7 两项旧 High、31-test 静态计数、五路 104 inventory 和关键冻结语义的关闭证据均不能抵消上述阻断项。