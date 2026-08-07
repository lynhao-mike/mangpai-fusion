# PI-400-R1 · F09 单卡 G4 独立技术评审

> 任务编号：PI-400-R1  
> 父任务：PI-400 / G4  
> 评审日期：2026-07-19  
> 文档性质：独立、只读技术评审；不整改、不实现、不执行测试、不改变生产默认  
> 评审对象：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)

---

## 1. 独立性与实际范围

本评审实例与 PI-300、PI-360-R1／R2／R3 以及 PI-390-R1／R2／R3／R4 分离。PI-390-R4 的历史通过记录只用于回归定位，不替代本次 G4 对冻结语义、对象模型和证伪能力的独立判断。

实际范围严格限定为 F09「资本配置与风险承担」一卡设计：

- 只审查设计，不修改 PI-300、G2 契约、冻结契约、mapping、总控、handoff、代码、测试、案例、数据或生产文件；
- F08 只允许作为 identity-only 的最强竞争解释，不执行第二张卡；
- 不进入 G5，不创建实现计划，不推断用户最终批准；
- `implementation=false`；
- 现有 runtime、renderer、dispatcher、artifact coordinator、feedback fanout 和 production wiring 不作为已实现能力。

本次唯一仓库写入是本评审记录。

---

## 2. 事实源与机械定位

| 事实源 | 本次用途 | 机械证据 |
|---|---|---|
| 冻结 F09 契约 | 业务语义基线 | F09 要求配置位置／风险位置独立核验，资源、对象、配置轴、风险轴、归属、时态分别过门；单轴仅限定成立，双轴才是强主；状态／事件分账；七类有限落点须登记轴、作用、对象、时态，见 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:268) |
| 声明性 mapping | 冻结字段和非执行边界 | 禁止推断缺失字段和执行 YAML，见 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:6)；F09 必要门、状态／事件、验证时点和空精度见 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:444) |
| PI-210 | 三轨、空值、声明 binding | 三轨定义见 [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:68)；显式空值与 unresolved 分账见 [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:336)；声明 binding 封闭联合见 [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:387) |
| PI-220 | gate、参与、竞争、五动作契约 | 门组要求逐门记录，见 [`GateEvaluationSet`](production-implementation-pi-220-decision-interface.md:244) 与 [`GateEvaluationRecord`](production-implementation-pi-220-decision-interface.md:253)；集合 READY 仅表示所有声明门都有完整记录，见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:283)；六角色独立记录见 [`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:319) |
| PI-230 | trace、artifact、feedback、learning、审计 | 跨轨仅允许 AUDIT_ONLY，见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:221)；artifact set 状态见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:555)；能力固定为非实现证明，见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:759) |
| G2 独立复验 | 已接受的通用契约基线 | PI-290-R3 仅接受 G2 契约，不证明 runtime，见 [`production-implementation-pi-290-r3-g2-reacceptance.md`](production-implementation-pi-290-r3-g2-reacceptance.md:1) |
| PI-300 | 当前 G4 被评设计 | 范围和能力边界见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:30)；不变量见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:115)；设计对象和测试矩阵见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:388) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:940) |
| 历史 G3 记录 | 回归检查，不作本次结论替代 | R1 七项发现见 [`production-implementation-pi-390-r1-g3-acceptance.md`](production-implementation-pi-390-r1-g3-acceptance.md:69)；R2 两项发现见 [`production-implementation-pi-390-r2-g3-reacceptance.md`](production-implementation-pi-390-r2-g3-reacceptance.md:60)；R3 gate basis 发现见 [`production-implementation-pi-390-r3-g3-reacceptance.md`](production-implementation-pi-390-r3-g3-reacceptance.md:46)；R4 历史结论见 [`production-implementation-pi-390-r4-g3-reacceptance.md`](production-implementation-pi-390-r4-g3-reacceptance.md:189) |
| 治理事实源 | 当前阶段和授权边界 | G4 进行中、G5 阻断见 [`production-implementation-control.md`](production-implementation-control.md:68)；技术清零后仍须等待用户批准见 [`production-implementation-control.md`](production-implementation-control.md:234)；授权不含 G5 或最终批准见 [`handoff.md`](../handoff.md:98) |

---

## 3. 十域评审矩阵

| # | 评审域 | 独立结果 | 主要证据与判断 |
|---:|---|---|---|
| 1 | 冻结 F09 语义保真 | 阻断 | 文字层正确保留资源、对象、双轴、归属、时态、竞争、根源／应期和 F08 identity-only，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:40)。但规范实例把六个分别过门的维度压成单一 `GATE-F09` 聚合状态，不能机械保存各维独立状态，见 G4-H-01。状态／事件与有限落点也缺少可消费对象和关键证伪用例，见 G4-M-01。 |
| 2 | 声明性边界 | 符合 | YAML 明确不可执行；PI-300 不新增谓词或算法。output precision 保持 explicit null + unresolved 且 binding 为 RESOLVED，validation plan 独立传递，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:392) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:869)。三轨隔离和理论／假设不得满足现实门有明确负例 T13–T14。 |
| 3 | G2 一致性 | 阻断 | 六参与角色、competition/disposition、root/timing、五动作联合、current-result basis 和声明 bindings 均已具体化；但 PI-220 的“门组与逐门记录”及“所有声明门均有结构完整记录”要求未被 F09 gate fixture 忠实实例化，见 G4-H-01。 |
| 4 | 端到端架构兼容 | 有条件符合 | 输入／证据→decision→trace→statement→artifacts→feedback→eligibility 的对象流完整，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:137)。设计明确将现有组件限定为 adapter seams，并承认没有 runtime consumer 或统一 dispatcher，未把设计适配性冒充现有能力。语义对象缺口仍阻止整体技术清零。 |
| 5 | 失败模式 | 有条件符合 | missing、conflict、unknown、引用断裂、重复／冲突重试、跨 result、digest／revision mismatch、partial artifacts、跨轨污染均有 fail-closed 设计，见 T03–T29、T47–T58、T62–T77 及失败注入表 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1033)。但逐维 gate 状态缺失使单维 missing／unknown／conflict 的结构传播不能被充分证伪。 |
| 6 | 测试充分性 | 阻断 | T01–T77 共 77 个设计用例，本评审执行 0 个。它们不是 runtime 证据。现有矩阵能证伪大量结构约束，但 T74–T77只检查聚合 `GATE-F09` 的存在、唯一性、类型和 current-result 域，不能证伪六维逐门记录；也没有状态／事件互不回填和七类有限落点四要素的具体正反测试，见 G4-H-01 与 G4-M-01。 |
| 7 | production-default 兼容 | 符合 | production、staged、preprod 分账，跨轨只允许 AUDIT_ONLY；设计不修改默认入口、默认行为、学习状态或能力声明，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1128)。 |
| 8 | 回滚／幂等／审计 | 符合 | 使用规范 IdempotencyKey，same-key/different-digest 阻断；artifact item 八值状态与 set 聚合状态分账；不假设跨文件事务；成功项不删除、提交后只 supersede；跨轨引用仅审计，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1056)。 |
| 9 | 范围／治理 | 符合 | 仅 F09；F08 无 candidate、disposition、action 或 statement，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:683)。没有生产代码或测试变更，`implementation=false`，G5 仍阻断，未推断用户批准。 |
| 10 | 历史回归 | 有新问题 | R1、R2、R3 的原始对象闭合问题未以原形复现；但为关闭 R3 basis 身份缺失而加入的单一聚合 gate fixture 引入逐维语义不可机械保存的新回归，计 1 个，见 G4-H-01。 |

---

## 4. 详细发现

### G4-H-01 · 六个冻结现实维度被压缩为单一 gate 状态

- **级别：High**
- **性质：冻结语义／核心 G2 gate 契约破坏；关键证据缺失；新回归**
- **证据：**
  1. 冻结 F09 明确要求资源、对象、配置轴、风险轴、归属和时态“分别过门”，单轴仅限定成立、双轴才是强主，见 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:268)。
  2. PI-300 自身也要求“按冻结维度分别保存 evaluator record”，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:211)。
  3. PI-220 将 gate set 定义为逐门 records，并规定 READY 表示所有声明门均有结构完整记录，见 [`GateEvaluationSet`](production-implementation-pi-220-decision-interface.md:244) 与 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:283)。
  4. PI-300 的五个具体场景却各只实例化一个 `gate_definition_ref=FR-F09-REALITY-HARD-GATE`、一个 `gate_record_id=GATE-F09` 和一个聚合 state，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:449)。
  5. CONDITIONAL 场景省略风险证据但将聚合记录标为 SATISFIED，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:478)。该对象无法机械区分“风险轴未成立”“风险轴缺证”“风险轴 unknown”“风险轴 conflict”或“风险轴已评估但不参与单轴结论”。
  6. T74–T77 只验证聚合记录身份，不验证六维各自恰一记录及状态传播，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1017)。
- **影响：**
  - 实现可在保留 `GATE-F09=SATISFIED` 的同时丢失任一冻结维度的独立状态，仍通过当前结构测试；
  - 单轴／双轴强度边界和针对单维的 ASK、HUMAN_REVIEW、ABSTAIN 路径无法由规范对象机械复核；
  - statement basis 只能追到聚合结论，不能证明各必要维度在当前 result 中独立过门；
  - 这不是单纯命名问题，而是冻结语义与核心 gate contract 的信息损失，因此按 High 计。
- **最小有界整改：**
  - 仅在 F09 设计范围内，把六个冻结维度分别实例化为具有独立稳定 ID、冻结定义引用和 `GateEvidenceState` 的 `GateEvaluationRecord`；若保留 `GATE-F09` 作为 basis 聚合身份，必须把它设计为可机械解析且不吞并逐维状态的规范关系／聚合结果，不得替代六条逐门记录；
  - 明确单轴 CONDITIONAL 中另一轴的真实状态及其 issue/path/source-decision 语义；
  - 增加逐维缺失、unknown、conflict、重复、跨 result、理论冒充事实，以及配置单轴／风险单轴／双轴的正反设计测试。

### G4-M-01 · 状态／事件与有限现实落点缺少可消费对象及关键证伪覆盖

- **级别：Medium**
- **性质：关键实现歧义；关键测试覆盖不足**
- **证据：**
  1. 冻结 F09 要求状态证明基准日持续位置、事件证明指定窗口变化，S1–S3 与 E1–E3 独立；七类有限落点均须登记轴、作用、对象和时态，见 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:269) 与 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:272)。
  2. mapping 也分别声明 `state_card` 与 `event_card`，见 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:444)。
  3. PI-300 在理由和不变量中陈述状态／事件分账，但具体规范对象仅展示通用 `semantic_scope="F09 bounded action projection"`、domain 和示例文本，未提供状态卡／事件卡 identity、level、baseline/window 关系或有限落点的 axis/action/object/tense 投影，见 [`StandardStatement`](production-implementation-pi-300-one-card-vertical-slice-design.md:788)。
  4. T01–T77 没有具体测试状态事件互填、历史事件冒充当前状态、事件窗口变化、S/E level 独立性，或七类有限落点缺任一 axis/action/object/tense 的拒绝路径，测试矩阵见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:940)。
- **影响：**
  - 实现者必须自行决定状态／事件和有限落点如何进入 decision、basis 与 statement，存在扩写冻结业务规则或丢失边界字段的风险；
  - 当前 77 个设计用例不能证伪事件回填状态、状态冒充事件，或无界工具／金额／结果被直接输出；
  - 端到端对象流虽完整，但不能证明所有 G4 关键 F09 语义可无损投影。
- **最小有界整改：**
  - 不新增业务规则，仅转录冻结 F09 的 state/event identity、level、as-of/window 及 bounded outcome 四要素到现有 G2 允许的证据、关系、scope 或 statement 结构；如现有 G2 类型无法无损表达，应明确阻断而非本地发明竞争 schema；
  - 增加状态／事件独立正反例，以及有限落点 axis/action/object/tense 缺项和禁止具体工具、金额、结果直出的负例。

---

## 5. 无其他发现

除 G4-H-01 与 G4-M-01 外，本次未发现以下独立问题：

- YAML 被执行、缺失字段被推断、explicit null／unresolved／absent／unknown 被混用；
- validation plan 与 output precision 串线；
- 三证据轨互相升级或跨轨进入生产学习；
- 六 participation role 互补；
- F08 被执行为第二张卡；
- 五动作 payload 判别错配、current-result basis/disposition 回退查找；
- root/timing 互写；
- partial artifact 被当作完整、item/set 状态混账；
- duplicate conflict、revision/digest mismatch 或未知反馈进入学习；
- staged/preprod 改变 production-default；
- runtime 能力、实现完成或 production readiness 越界声明。

“无其他发现”不抵消已记录的 High 与 Medium。

---

## 6. 历史回归矩阵

| 历史 ID | 历史问题 | 本次独立状态 | 当前证据 |
|---|---|---|---|
| H-01 | F08 identity-only 与 competition schema 未闭合 | 未复现 | F09 singleton 合法；F08 只在 evidence/relation/issue/source identity，且禁止 F08 candidate/action/statement，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:613) |
| H-02 | FrozenDeclarationRef 身份字段缺失 | 未复现 | 两声明均有完整六字段身份，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:394) |
| H-03 | feedback／learning 对象被局部重定义 | 未复现 | 三对象采用 PI-230 字段与枚举，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:822) |
| M-01 | StatementSet／StandardStatement 缺 required 字段 | 未按原形复现 | required 结构字段已补齐；本次 G4-M-01 是冻结业务投影和测试覆盖问题，不重复计历史 M-01 |
| M-02 | participation 与 root/timing 被压缩 | 未复现 | 六角色及两账本／检查均独立实例化，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:585) |
| M-03 | 五动作 payload 不可机械验收 | 未按原形复现 | 五个判别分支和 basis 已具体化，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:723) |
| M-04 | feedback 幂等身份不完整 | 未复现 | canonical identity 含 source digest、item IDs、statement revision、policy identity/version，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1080) |
| M-R2-01 | basis/disposition refs 不闭合 | 未按原形复现 | disposition 和 `GATE-F09` identity 均可在 current result 解析；但该 gate record 聚合粒度造成新的 G4-H-01 |
| M-R2-02 | artifact item enum 漂移 | 未复现 | 使用 PI-230 八值 item 状态并与 set 状态分账，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1095) |
| M-R3-01 | `GATE-F09` basis 无当前 result 对象 | 已关闭但产生新回归 | 五场景现有同名 record，解决零匹配；然而以单一聚合状态替代六维逐门记录，形成 G4-H-01 |

回归统计口径：历史问题原形均未重新打开；G4-H-01 是围绕 R3 修复形态发现的 **1 个新回归**，不把同一根因重复计为历史 M-R3-01 reopened。

---

## 7. 测试与验证声明

- PI-300 定义 T01–T77，机械计数为 **77 个设计用例**。
- 本次评审执行测试：**0 个**。
- 本次未运行 pytest、CLI、runtime、renderer、dispatcher、artifact、feedback 或 learning 流程。
- 设计用例、规范对象示例、历史 G3 评审结论均不是 runtime 证据，也不证明实现、生产接线或投产能力。
- 评审采用静态、机械交叉核验：冻结契约 ↔ mapping 声明 ↔ G2 类型／不变量 ↔ PI-300 具体对象 ↔ T01–T77 ↔ 历史发现。

---

## 8. 精确统计

- High：**1**
- Medium：**1**
- critical ambiguity：**0**
- 关键证据缺失：**2 类**
  1. 六个冻结现实维度逐门 evaluator record 与逐维失败安全证据；
  2. 状态／事件及有限落点四要素的可消费投影和关键测试证据。
- 新回归：**1**
- 历史发现原形重新打开：**0**

计数去重说明：G4-H-01 同时造成 gate 语义破坏、单轴状态不可判和相应测试缺口，只计一个 High、一个关键证据缺失类别和一个新回归；G4-M-01 的状态／事件与有限落点共同属于同一“冻结输出边界不可机械投影和证伪”问题，只计一个 Medium 和一个关键证据缺失类别。

---

## 9. 唯一最终裁决

**BLOCKED**

理由：冻结 F09 要求六个现实维度分别过门，但当前五个场景各只保存一个聚合 gate state；同时状态／事件和有限现实落点缺少可消费对象与关键证伪覆盖。合计 1 个 High、1 个 Medium、0 个 critical ambiguity、2 类关键证据缺失、1 个新回归。依据 fail-closed 纪律，任一 High、Medium、关键证据缺失或新回归均禁止技术清零。

---

## 10. 治理建议

1. G4 保持技术阻断状态；不得转为 `REVIEW / AWAITING_USER_APPROVAL`，因为技术问题尚未清零。
2. 仅允许由与本评审分离的有界整改实例处理 G4-H-01 与 G4-M-01；本评审实例不整改、不自验。
3. 整改后必须创建新的独立 G4 复评实例；不得以整改自检、PI-390-R4 或本记录替代复评。
4. `PI-500/G5=BLOCKED`，`implementation=false`；不得创建实现计划、修改生产默认、执行 F08 第二卡或推断用户批准。
5. 技术评审结论不等于用户批准、实现证明、runtime 证据、production readiness 或投产授权。
