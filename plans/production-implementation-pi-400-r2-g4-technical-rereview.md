# PI-400-R2 · F09 单卡 G4 独立技术复评

> 任务编号：PI-400-R2  
> 父任务：PI-400 / G4  
> 复评日期：2026-07-19  
> 文档性质：独立、只读技术复评；不整改、不实现、不执行测试、不改变生产默认  
> 复评对象：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)  
> 前次发现基线：[`production-implementation-pi-400-r1-g4-technical-review.md`](production-implementation-pi-400-r1-g4-technical-review.md:62)

---

## 1. 结论

**BLOCKED**

PI-460-R1 后的 PI-300 已把五个当前结果改为每个结果六条 gate record，并补入场景本地现实参与记录、单轴／双轴 fixture、完整 basis 传播以及 T78–T104；这些改动解决了前次发现所指的“单一聚合 gate state”表面形态，并补足了 state/event/bounded-outcome 的设计级对象和测试清单。

但机械复核仍不能关闭两项历史 finding：

1. `G4-H-01` **未关闭**：六条 [`FrozenCardFieldRef`](production-implementation-pi-210-normalized-evidence-model.md:340) 使用 `/cards/F09/normative_sections/4.9/reality_hard_gate_items/{0..5}`，而正式冻结 Markdown 在 §4.9 只有一条“现实硬门与双卡”列表项，其中以一句话并列六维；冻结源没有声明 `normative_sections`、`reality_hard_gate_items` 或六个子条目对象。PI-300 自行宣布一个“卡片→规范章节→有序条目”对象模型，不能使不存在的正式对象路径变成可机械解析的冻结字段引用。
2. `G4-M-01` **未关闭**：state/event/outcome 虽已投影到 G2 通用对象，但关键 `SRCLOC-*` 只以符号名和“均是完整对象”的断言出现，没有给出可核对的完整 locator 实例及原始结构化来源对象；因此无法机械证明 S/E level 与 bounded outcome 四要素是来源字段的无损复制，而非在 generic [`TypedPayload`](production-implementation-pi-210-normalized-evidence-model.md:245) 中建立本地 F09 业务形状。
3. 新发现一项独立 G2 一致性回归：UNKNOWN gate fixture 使用未登记的 `GATE.EVIDENCE_UNKNOWN`，而 PI-220 最小目录登记的是 `GATE.STATE_UNKNOWN`；扩展 code 又必须具有唯一注册说明和稳定版本。当前设计没有提供该注册证据。

按 fail-closed 纪律，任一 High、Medium、关键证据缺失或新回归均禁止技术 PASS。

---

## 2. 独立性与边界

本复评实例独立于 PI-300、PI-360-R1／R2／R3、PI-460-R1、PI-390-R1／R2／R3／R4 与 PI-400-R1。历史材料只用于定位待关闭 finding 和检查回归，不替代本次机械裁决。

实际范围严格限定为 F09 一卡设计：

- 只读复核冻结 F09、声明性 mapping、G2 契约、PI-300 整改后对象、T01–T104、历史 finding 与治理边界；
- F08 只检查 identity-only competition，不作为第二张卡执行；
- 不修改 PI-300、G2 契约、冻结契约、mapping、治理文件、handoff、代码、测试、案例或生产默认；
- 不执行 YAML，不运行测试，不进入 G5，不创建实现计划，不推断用户批准；
- `implementation=false`；
- 本次唯一仓库写入为本复评记录。

---

## 3. 事实源与机械位置

| 事实源 | 用途 | 机械证据 |
|---|---|---|
| 冻结 F09 Markdown | 六维、单轴／双轴、state/event、有限落点语义基线 | §4.9 在一条列表项中要求资源、对象、配置轴、风险轴、归属、时态分别过门；状态与事件分账见 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)，四要素要求见 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:272) |
| F09 mapping | 声明性字段与禁止执行边界 | `necessary_reality_gates`、state/event card、bounded outcome attributes、空精度见 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:437)；mapping 使用 `allocation_axis_or_risk_axis`，并未提供六个拟制 Markdown 子路径 |
| PI-210 | 引用、来源、payload、转换和失败安全基线 | [`FrozenCardFieldRef`](production-implementation-pi-210-normalized-evidence-model.md:340) 要求稳定 `field_path` 与 locator；冻结字段 getter 依赖给定路径返回正式引用见 [`get_card_field_ref()`](production-implementation-pi-210-normalized-evidence-model.md:1001)；状态与事件、来源及转换使用通用规范对象 |
| PI-220 | gate、参与、动作和 reason code 基线 | gate set／record 要逐门保存；最小 reason code 目录登记 `GATE.STATE_UNKNOWN` 见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:725)，扩展 code 必须进入稳定注册表见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:751) |
| PI-230 | trace、statement、artifact、feedback 与审计基线 | action→trace→statement 必须保留同一当前结果 basis；设计引用不等于实现证明，见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:759) |
| PI-300 整改后设计 | 当前受评对象 | 六 refs 与路径声明见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:451)；六记录 fixtures 见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:474)；source locator 完整性断言见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:737)；T74–T104 见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1044) |
| 前次 G4 | 待关闭 finding 基线 | `G4-H-01` 见 [`production-implementation-pi-400-r1-g4-technical-review.md`](production-implementation-pi-400-r1-g4-technical-review.md:62)；`G4-M-01` 见 [`production-implementation-pi-400-r1-g4-technical-review.md`](production-implementation-pi-400-r1-g4-technical-review.md:83) |
| 治理文件 | 阶段边界 | 技术清零后仍须等待用户批准，且 G5 保持阻断，见 [`production-implementation-control.md`](production-implementation-control.md:234) 与 [`handoff.md`](../handoff.md:98) |

---

## 4. G4-H-01 关闭矩阵

| 必验项 | 整改后证据 | 机械结果 | 裁决 |
|---|---|---|---|
| 每个当前 result 恰有六条独立 gate record | 五个场景及三个轴 fixture 均声明资源→对象→配置→风险→归属→时态六记录，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:474) | 表面满足；不再使用单一聚合 state | 通过此子项 |
| 单维状态独立、其他维不得补强 | CONDITIONAL、ASK、HUMAN_REVIEW 分别保存 UNKNOWN、MISSING、CONFLICT；T79–T81 逐维注入 | 结构意图满足 | 通过此子项 |
| 单轴 limited、双轴 strong-primary | T82–T84 分别覆盖 allocation-only、risk-only、dual-axis | 与冻结文字方向一致；未新增动作优先级 | 通过此子项 |
| participation 与 gate 状态一致 | 五个场景采用本地 `PR-REALITY-X`，T87–T88 检查共享全满足攻击 | 关闭前次共享聚合状态风险 | 通过此子项 |
| action→trace→statement 保留完整六维 basis | 同序 basis 及 T59、T74–T77、T89 | 当前 result 内零／多匹配、错类型、跨结果、漂移均有设计 falsifier | 通过此子项 |
| 六个 definition refs 必须定位正式冻结对象 | PI-300 使用 `/cards/F09/normative_sections/4.9/reality_hard_gate_items/{0..5}` 并自行声明 Markdown 对象模型 | 冻结源只有 §4.9 的单条 Markdown 列表项；没有所称容器和六个子条目。路径不能由正式源对象模型机械解析 | **失败** |
| 不伪装不存在的 mapping/YAML 子键 | PI-300 声称不是 YAML 子键 | 未伪装成 YAML 路径，但改为虚构 Markdown 正式对象路径仍违反 ref/path 真实性要求 | **失败** |
| UNKNOWN reason code 与 G2 注册一致 | fixture 使用 `GATE.EVIDENCE_UNKNOWN` | PI-220 登记值为 `GATE.STATE_UNKNOWN`，未见扩展注册 | **失败** |

**关闭结论：G4-H-01 未关闭。**

六记录、状态传播和测试设计已实质改善，但 gate definition identity 的根基仍不可机械解析。实现若接受这些 refs，必须在冻结契约之外发明路径解析规则；若拒绝这些 refs，则六条 gate records 均失去有效冻结定义绑定。因此本问题仍属于冻结语义和核心 G2 引用契约破坏，按 High 计。

---

## 5. G4-M-01 关闭矩阵

| 必验项 | 整改后证据 | 机械结果 | 裁决 |
|---|---|---|---|
| state/event 身份独立 | `STATE-F09-2026Q2` 与 `EVENT-F09-2026Q2` 使用不同 evidence/subject identities | 满足对象级分离 | 通过此子项 |
| state 使用 AS_OF、event 使用 INTERVAL | 两对象分别声明 `AS_OF` 和 `INTERVAL` | 符合 PI-210 时态语义 | 通过此子项 |
| S level 与 E level 分离 | payload 分别保留 S2 与 E2；T90–T93 检查身份、level 和时态错配 | 设计 falsifier 已补 | 通过此子项 |
| bounded outcome 四要素齐全 | outcome payload 含 axis/action/object/tense；转换声明四个 LOSSLESS COPY | 目标对象形状和转换意图已给出 | 有条件 |
| 不使用 `value_schema`／metadata 变相建 schema | 正例 `value_schema=null`；T99–T100 禁止自由文本无损结构化和本地 schema | 禁令清楚 | 通过设计意图子项 |
| 来源对象与 locator 可机械核对 | 文档仅称所有 `SRCLOC-*` 是完整对象，并展示符号引用；没有逐个完整 [`SourceLocator`](production-implementation-pi-210-normalized-evidence-model.md:266) 实例或原始 source object snapshot | 无法检查 locator 的 path/object/field/digest/time，也无法证明 `/axis` 等字段在来源对象中原生存在 | **失败** |
| TransformationRecord 的 LOSSLESS 可证 | 给出四条 field mapping、无 dropped/synthesized fields | 只有目标侧和映射声明；缺来源侧机械证据，LOSSLESS 结论不可独立验证 | **失败** |
| statement 可解析 state/event/outcome | OUTPUT statement 引用 state/outcome；文字要求 EVENT 用独立 versioned ref | state/outcome 正例可描述；event 主要停留在要求与测试前置，但不单独构成新增 finding | 有条件 |
| 禁止工具、金额、结果直接输出 | T101–T103 | 已补足关键负例 | 通过此子项 |

**关闭结论：G4-M-01 未关闭。**

整改已补齐此前完全缺失的目标对象与 T90–T104，但“来源对象原生具有这些字段”仍是不可核对断言。没有完整、具体、可解析的 source locator/source object 证据，就无法区分无损复制与在 generic OBJECT payload 内本地定义 F09 state/event/outcome 业务形状。按关键实现歧义与关键证据缺失计一个 Medium，不把同一根因重复拆分。

---

## 6. 完整十域回归矩阵

| # | 评审域 | 独立结果 | 主要判断 |
|---:|---|---|---|
| 1 | 冻结语义保真 | **阻断** | 六维、单轴／双轴、state/event、四要素的文字与记录意图已保留；但六 refs 指向冻结源中不存在的正式子对象路径，冻结身份不可成立。 |
| 2 | 声明性边界 | **阻断** | 未执行 YAML、未增加算法；然而自行宣布 Markdown 对象层级实际扩张了冻结声明的可寻址模型，越过只转录正式声明的边界。 |
| 3 | G2 一致性 | **阻断** | gate/participation/basis 大部分与 G2 同构；但虚构 field path、未注册 `GATE.EVIDENCE_UNKNOWN`，以及不可核对的 source locator/LOSSLESS 断言不符合 G2。 |
| 4 | 端到端架构兼容 | **有条件符合** | package→decision→trace→statement→artifact→feedback→eligibility 流程仍完整，且现有组件只称 adapter seam；关键引用和来源证据缺口阻止无损消费。 |
| 5 | 失败模式 | **有条件符合** | missing/unknown/conflict、跨 result、断链、partial、digest/revision、跨轨等均有 fail-closed 设计；未覆盖“冻结 Markdown 路径不存在／对象模型不成立”和未注册 reason code 的明确拒绝路径。 |
| 6 | 测试设计充分性 | **阻断** | T74–T104 显著补强六维和投影 falsifier，但没有测试 formal Markdown path 实际存在、locator 完整对象可解析、reason code 注册命中。104 项均未执行。 |
| 7 | production-default 兼容 | **符合** | 不改变默认入口与行为；production/staged/preprod 分账，跨轨仅 AUDIT_ONLY，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1184)。 |
| 8 | 回滚／幂等／审计 | **符合** | 规范幂等键、same-key/different-digest 阻断、item/set 状态分账、partial 不假回滚、提交后 supersede，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1112)。 |
| 9 | 范围／治理 | **符合** | 仅 F09；F08 保持 identity-only；无实现、测试执行、生产变更或 G5 设计；技术结论不替代用户批准。 |
| 10 | 历史发现／新回归 | **阻断** | 前次两项 finding 均未达到机械关闭；新增两类回归：虚构 formal Markdown path，以及 UNKNOWN reason code 漂移。历史 G3 其他问题未见原形重新打开。 |

---

## 7. Findings

### G4-H-01 · 六维 records 已拆分，但冻结 definition path 不真实

- **级别：High**
- **状态：未关闭**
- **性质：冻结语义绑定失败；核心 G2 ref/path 破坏；关键证据缺失；新回归**
- **机械事实：**冻结 F09 在 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:269) 的一条 Markdown 列表项中并列六维；PI-300 却创建六个 `/reality_hard_gate_items/{0..5}` 路径，并宣告一个源文件未声明的对象模型。
- **影响：**六条记录虽结构独立，却不能证明绑定了六个正式冻结对象；实现只能猜解析或 fail closed，无法满足 [`get_card_field_ref()`](production-implementation-pi-210-normalized-evidence-model.md:1001) 所需的稳定正式路径。

### G4-M-01 · state/event/outcome 目标对象已补，但来源侧无损证据仍不可消费

- **级别：Medium**
- **状态：未关闭**
- **性质：关键实现歧义；关键证据缺失**
- **机械事实：**PI-300 用符号 `SRCLOC-*` 和“均是完整对象”的文字替代具体 locator/source object；四要素的 source field existence、digest 和定位不能独立复核。
- **影响：**无法证明 [`TransformationRecord`](production-implementation-pi-210-normalized-evidence-model.md:570) 的 `LOSSLESS`，也无法排除 generic payload 被用作本地 F09 业务 schema。

### G4-M-02 · UNKNOWN gate reason code 未与 PI-220 注册目录一致

- **级别：Medium**
- **状态：新增**
- **性质：G2 枚举／注册表一致性回归；新回归**
- **机械事实：**PI-300 在 CONDITIONAL 与 risk-only fixture 使用 `GATE.EVIDENCE_UNKNOWN`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:483)；PI-220 登记的是 `GATE.STATE_UNKNOWN`，且扩展 code 必须有稳定注册表条目，见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:728)。
- **影响：**规范 consumer 无法确定应拒绝、映射还是接受该值；静默映射会掩盖契约漂移。

除上述三项外，本复评没有发现新的独立 High／Medium finding。特别是 F08 第二卡执行、YAML 执行、精度默认推断、三轨污染、root/timing 互写、跨轨生产学习、artifact item/set 混账和测试清单冒充 runtime 证据均未复现。

---

## 8. T01–T104 充分性与验证声明

- PI-300 机械连续编号 T01–T104：**104 defined**。
- 本任务与 PI-300 执行测试：**0 executed**。
- 创建 runtime tests：**0**。
- pytest、CLI、YAML evaluator、renderer、dispatcher、artifact、feedback、learning 流程：**均未运行**。
- T78–T89 对六维 record、状态、轴 fixture、参与和 basis 的设计覆盖较前次充分。
- T90–T104 对 state/event、S/E level、四要素缺项、自由文本结构化、`value_schema`、工具／金额／结果和 issue 传播的设计覆盖较前次充分。
- 仍缺三类关键设计 falsifier：
  1. 六个 formal Markdown `field_path` 必须由冻结源真实对象模型逐一解析；
  2. 每个关键 `SourceLocator` 与 source object 字段必须具体实例化并能验证 LOSSLESS；
  3. reason code 必须命中 PI-220 注册表或提供合规稳定扩展注册。
- 设计矩阵、规范示例和历史验收均不是实现、执行或 production-readiness 证据。

---

## 9. 精确统计

- High：**1**
- Medium：**2**
- critical ambiguity：**0**
- 关键证据缺失：**2 类**
  1. 六维 gate definition refs 对正式冻结对象的真实、机械可解析绑定；
  2. state/event/outcome 的完整来源 locator/source object 与 LOSSLESS 来源侧证明。
- 新回归：**2 类**
  1. 通过虚构 formal Markdown object path 绑定六维；
  2. `GATE.EVIDENCE_UNKNOWN` 与 PI-220 注册目录漂移。
- 历史 finding 关闭：**0 / 2**
- 历史 finding 未关闭：**2 / 2**
- 历史 G3 其他 finding 原形重新打开：**0**
- 设计测试：**104 defined / 0 executed**
- implementation：**false**

去重口径：虚构 path 同时导致冻结语义、G2 ref/path 和测试缺口，只计一个 High、一个关键证据缺失类别和一个新回归类别；source locator 缺失与 LOSSLESS 不可证属于同一来源侧机械证据根因，只计一个 Medium 和一个关键证据缺失类别；reason code 漂移是独立 G2 注册问题，单计一个 Medium 和一个新回归类别。

---

## 10. 唯一最终裁决

**BLOCKED**

技术 PASS 所需的 High、Medium、critical ambiguity、关键证据缺失和新回归五项均为零；本次实际为 `1 / 2 / 0 / 2 / 2`，不满足清零条件。

---

## 11. 治理建议与最小有界整改范围

1. G4 保持技术阻断；不得转为 `REVIEW / AWAITING_USER_APPROVAL`，更不得标记 `COMPLETED`。
2. `PI-500/G5=BLOCKED`，`implementation=false`；不得创建实现计划、运行测试、修改生产默认或执行 F08 第二卡。
3. 只允许新的、与本复评分离的有界整改实例处理以下三点，本复评不修复：
   - 在不修改冻结契约的前提下，为六维提供真实可解析的正式冻结引用；若现有冻结对象粒度不能支持六条 [`FrozenCardFieldRef`](production-implementation-pi-210-normalized-evidence-model.md:340)，必须明确 fail closed，不得再次发明 path；
   - 具体实例化关键 source locators 和来源对象字段，使 state/event/outcome 的 COPY fidelity 可机械检查；不能用 `value_schema`、metadata 或 generic payload 代替来源 schema；
   - 把 UNKNOWN gate reason code 与 PI-220 已注册值对齐，或提供满足唯一说明与稳定版本要求的正式注册证据。
4. 整改实例不得自验；完成后必须由新的独立 G4 复评实例重新检查两项历史 finding、三项当前 finding 和完整十域。
5. 技术结论不等于用户批准、实现证明、runtime 证据、production readiness 或投产授权。

---

## 12. 标准返回口径

1. **结论：**`BLOCKED`。
2. **实际范围：**仅 F09 整改后设计的独立 G4 静态复评；F08 identity-only；未进入 G5。
3. **关键证据：**六记录形态和 T78–T104 已补；formal Markdown path 不真实、source-side LOSSLESS 不可核对、UNKNOWN reason code 未注册对齐。
4. **修改文件：**仅 [`production-implementation-pi-400-r2-g4-technical-rereview.md`](production-implementation-pi-400-r2-g4-technical-rereview.md:1)。
5. **验证动作：**冻结契约↔mapping↔PI-210／220／230↔PI-300 对象↔T01–T104↔历史 finding 的静态机械交叉核验；**104 defined / 0 executed**。
6. **剩余不可推断事项：**不存在可从当前证据合法推断的 formal 六子项 Markdown path、完整关键 source locator/source snapshot，或 `GATE.EVIDENCE_UNKNOWN` 稳定注册条目。
7. **唯一下一动作：**由新的独立有界整改实例仅修复本记录列明的三个技术点；整改后再新建独立 G4 复评，G5 继续阻断。
