# PI-400-R3 · F09 单卡 G4 独立技术复评

> 任务编号：PI-400-R3  
> 父任务：PI-400 / G4  
> 复评日期：2026-07-19  
> 文档性质：独立、只读技术复评；不整改、不实现、不执行测试、不改变生产默认  
> 复评对象：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)  
> 前次 finding 基线：[`production-implementation-pi-400-r2-g4-technical-rereview.md`](production-implementation-pi-400-r2-g4-technical-rereview.md:114)

---

## 1. 独立性、范围与判定纪律

本复评实例独立于 PI-225、PI-295、PI-470-R2 及其自述结论。PI-225 与 PI-295 只用于核对已独立接受的 G2 amendment 表达能力，不替代本次对 PI-300 具体实例的机械验收；其边界也明确说明不会自动关闭 PI-300/G4 finding，见 [`production-implementation-pi-225-r1-shared-gate-member-identity-clarification.md`](production-implementation-pi-225-r1-shared-gate-member-identity-clarification.md:115) 与 [`production-implementation-pi-295-r1-g2-amendment-acceptance.md`](production-implementation-pi-295-r1-g2-amendment-acceptance.md:24)。

实际范围严格限定为 F09 一卡的静态设计复评：

- 机械复核 PI-400-R2 的 `G4-H-01`、`G4-M-01`、`G4-M-02`；
- 完成冻结语义、声明边界、G2、端到端、失败模式、测试、生产默认、回滚/幂等/审计、治理、历史 finding/新回归十域回归；
- F08 仅保持 identity-only competition，不作为第二张卡执行；
- 不修改 PI-300、G2、冻结契约、mapping、control、handoff、代码或测试；
- 不执行 YAML，不运行测试，不进入 G5，不推断 runtime evidence 或用户批准；
- `implementation=false`；本次唯一仓库写入为本复评记录。

判定采用严格 fail-closed 纪律：任一 High、Medium、critical ambiguity、关键证据缺失或新回归均为 `BLOCKED`；证据不足本身即为阻断，不以设计声明、未来测试或整改方自述补证。

---

## 2. 三项 finding 关闭矩阵

| Finding | 必验内容 | PI-470-R2 后的有效改进 | 机械缺口或核验结果 | 状态 |
|---|---|---|---|---|
| `G4-H-01` | 真实整体冻结 ref；显式 member declaration/binding；双射与基数；六维覆盖；置换 falsifier；无虚构 path | PI-300 已改为单一共享 ref，声明六个稳定 member ID、版本、digest 与逐 record immutable binding，见 [`MDECL-F09-V1`](production-implementation-pi-300-one-card-vertical-slice-design.md:467)；五场景及单轴/双轴 fixture 均保留六 records，见 [`GateEvaluationSet`](production-implementation-pi-300-one-card-vertical-slice-design.md:486)；T74–T81 覆盖全双射、基数、binding、置换与重排不变性，见 [`T74`](production-implementation-pi-300-one-card-vertical-slice-design.md:1095)。 | 被共享的 [`FrozenCardFieldRef`](production-implementation-pi-300-one-card-vertical-slice-design.md:460) 使用 `/cards/F09/reality_hard_gate_and_dual_cards`。冻结源只提供一条名为“现实硬门与双卡”的 Markdown 列表项及自然语言值，见 [`F09 现实硬门与双卡`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:269)；未定义该 JSON-like path、path dialect 或 Markdown→字段 resolver。声明性 mapping 的实际键是 `necessary_reality_gates`、`state_card`、`event_card`、`bounded_real_world_outcomes` 等，见 [`F09 mapping`](../mapping/real-world-function-evidence-cards-v1.yaml:437)，也不存在该字段。PI-225 允许共享一个**真实**整体 ref，但不授权 PI-300 创建新的冻结可寻址字段。故成员身份/置换机制已满足，根部 whole ref 仍不可机械解析。 | **未关闭 · High** |
| `G4-M-01` | state/event/outcome 原始 source object；完整 SourceLocator；字段 path、digest/version/time；来源侧可核对的 `LOSSLESS COPY` | PI-300 已内联三个结构化 fixture，见 [`SOURCE-STATE-1`](production-implementation-pi-300-one-card-vertical-slice-design.md:760)、[`SOURCE-EVENT-1`](production-implementation-pi-300-one-card-vertical-slice-design.md:768)、[`SOURCE-OUTCOME-1`](production-implementation-pi-300-one-card-vertical-slice-design.md:779)；逐字段 locator 形状完整，state/event/outcome mappings 分别列出 COPY、无 dropped/synthesized fields，见 [`TR-F09-STATE-1`](production-implementation-pi-300-one-card-vertical-slice-design.md:815)。 | 所有关键 locator 的 `path` 均指向 `cases/CASE-DEMO/source-snapshots.json`，见 [`SRCLOC-STATE-LEVEL`](production-implementation-pi-300-one-card-vertical-slice-design.md:764)，但该快照不在评审证据集中；全仓静态解析仅能在 PI-300 prose fixture 中找到三个对象。Transformation 又把它们标记为 `external:true`，见 [`TR-F09-EVENT-1`](production-implementation-pi-300-one-card-vertical-slice-design.md:820)。因此 locator 不能终止到其声称的 immutable source snapshot，不能核对 path/object/field/digest/version/time 联合身份，也不能独立证明 digest 对应内容及 `LOSSLESS` 来源侧值。内联设计样例不能替代 locator 所指向的外部对象。 | **未关闭 · Medium** |
| `G4-M-02` | 仅使用已注册的 `GATE.STATE_UNKNOWN`，并提供 registry-hit falsifier | CONDITIONAL 与 RISK-ONLY 均已改用 `GATE.STATE_UNKNOWN`，见 [`CONDITIONAL UNKNOWN`](production-implementation-pi-300-one-card-vertical-slice-design.md:503) 与 [`RISK-ONLY UNKNOWN`](production-implementation-pi-300-one-card-vertical-slice-design.md:552)。该值命中 PI-220 注册目录，见 [`reason-code registry`](production-implementation-pi-220-decision-interface.md:787)；T102 要求 registry hit，T104 拒绝未注册 code，见 [`T102`](production-implementation-pi-300-one-card-vertical-slice-design.md:1123)。 | 未发现 `GATE.EVIDENCE_UNKNOWN` 残留；设计值、注册值与负例期望一致。运行命中尚未执行，但本 finding 要求的设计契约一致性已机械满足。 | **已关闭** |

### 2.1 `G4-H-01` 裁决

成员 declaration、record/member 全双射、基数、immutable binding、六维覆盖及 permutation/reorder falsifier 均已补齐；这些改进关闭了原先 `6!` 成员不可区分问题。可是共享机制的前提是一个真实、可解析的整体冻结字段，PI-220 也明确共享不得产生虚构路径，见 [`共享整体 ref 约束`](production-implementation-pi-220-decision-interface.md:317)。

PI-300 在 [`整体 field_path 声明`](production-implementation-pi-300-one-card-vertical-slice-design.md:451) 中把自行命名直接称为“已有整体字段身份”，却未给出冻结源定义或正式 resolver。路径字符串、locator 摘要占位符和 declared value 的正确转录不能自行建立字段身份。故 `G4-H-01` 保持 High/Open。

### 2.2 `G4-M-01` 裁决

本轮不再缺 locator 字段形状，也不再缺 source fixture 的目标形状；剩余根因是 locator 终点不可解析。PI-210 要求 external source object 由 locator 解析，并禁止把自由文本中的结构外观当作字段级 `LOSSLESS` 来源证明，见 [`来源与转换约束`](production-implementation-pi-210-normalized-evidence-model.md:630)。PI-230 规定 path 负责定位、digest 负责证明、version 负责解释，三者不可互换，见 [`来源身份职责`](production-implementation-pi-230-traceability-binding.md:112)。

当前 inline fixture 位于 PI-300，而 locator 指向另一未提供的 JSON snapshot；两者没有可机械验证的 digest/content binding。故来源链在 external immutable snapshot 处断裂，`LOSSLESS` 仍不可独立复核，`G4-M-01` 保持 Medium/Open。

### 2.3 `G4-M-02` 裁决

当前所有 UNKNOWN 正例均使用注册值，并有 registry-hit 与未注册值 fail-closed 的设计 falsifier。该 finding 在设计层关闭；不把 T102/T104 当成已执行 runtime evidence。

---

## 3. 十域静态回归矩阵

| # | 评审域 | 结果 | 独立判断 |
|---:|---|---|---|
| 1 | 冻结语义保真 | **阻断** | 六维、单轴/双轴、state/event 与四要素的文字值已保留；但 whole ref 指向冻结源未定义的 JSON-like field path，冻结字段身份不能成立。 |
| 2 | 声明性边界 | **阻断** | 未执行 YAML、未新增评分或动作算法；但 PI-300 自行建立 Markdown 字段路径，越过“只引用正式冻结声明”的边界。 |
| 3 | G2 一致性 | **阻断** | member declaration/binding、双射、reason code 已与 amendment 对齐；不可解析的 frozen ref 和断裂的 external source locator 仍违反 ref/source 完整性。 |
| 4 | 端到端兼容 | **有条件符合** | package→decision→trace→statement→artifact→feedback→eligibility 结构仍完整；根部 frozen ref 与 source snapshot 不可解析，使合法消费必须 fail closed。 |
| 5 | 失败模式 | **有条件符合** | PI-300 已声明 ref path 不可解析为 `UNRESOLVABLE`、locator 404/digest mismatch 为 source-gate blocking，见 [`失败注入`](production-implementation-pi-300-one-card-vertical-slice-design.md:1144)；当前正例自身却触发这两类失败前提。 |
| 6 | 测试充分性 | **阻断** | T74–T104 的成员、置换、source、LOSSLESS 与 registry falsifier 设计显著补强；T90 的正例前提要求 locator 命中现存 snapshot，见 [`T90`](production-implementation-pi-300-one-card-vertical-slice-design.md:1111)，当前证据不满足。全部 104 项均未执行。 |
| 7 | production-default 兼容 | **符合** | 未修改生产默认行为；staged/preprod 与 production 分账，跨轨仅 AUDIT_ONLY；本复评也未执行任何生产入口。 |
| 8 | 回滚/幂等/审计 | **符合** | item/set 状态分账、same-key/same-digest no-op、same-key/different-digest block、partial 不伪造跨文件回滚、已提交 artifact 以 supersede 保留审计身份，未见本轮回归。 |
| 9 | 范围/治理 | **符合** | 仅 F09；F08 identity-only；无实现、无测试执行、无 production-default 变更、未进入 G5；技术裁决不代替用户批准。 |
| 10 | 历史 findings/新回归 | **阻断** | 三项 R2 finding 中仅 `G4-M-02` 关闭；`G4-H-01` 与 `G4-M-01` 以同一根因类别继续开放。未发现超出这两项开放 finding 的新独立 High/Medium 回归。 |

---

## 4. Findings 与精确统计

### `G4-H-01` · 共享整体 ref 的成员机制成立，但整体 field path 不真实

- 级别：**High**
- 状态：**未关闭**
- 根因：冻结契约未定义 `/cards/F09/reality_hard_gate_and_dual_cards`，也未提供可把 F09 Markdown 列表项解析成该路径的正式对象模型或 resolver。
- 影响：六条 record 虽可按 member identity 唯一区分，却共同绑定到不可解析的 definition ref；consumer 只能发明解析规则或 fail closed。

### `G4-M-01` · source fixture 形状已补，但 external locator 终点不存在于评审证据

- 级别：**Medium**
- 状态：**未关闭**
- 根因：完整 locator 指向未提供的 `cases/CASE-DEMO/source-snapshots.json`，而内联 fixture 位于另一文档；无可机械验证的 path→object→field→digest/content 链。
- 影响：state/event/outcome 的 source fields 与 COPY mappings 只能作为设计意图，不能独立证明 `LOSSLESS`。

### `G4-M-02` · UNKNOWN reason code 与注册目录一致

- 级别：无开放 finding
- 状态：**已关闭**
- 证据：当前值为 `GATE.STATE_UNKNOWN`，且 T102/T104 明确检查 registry hit 与未注册 code 拒绝。

### 精确统计

- High：**1**
- Medium：**1**
- critical ambiguity：**0**
- 关键证据缺失：**2 类**
  1. whole F09 definition ref 对正式冻结字段的真实、机械可解析绑定；
  2. state/event/outcome locator 对 external immutable snapshot 的可解析终点及 digest/content 证明。
- 新独立回归：**0 类**
- PI-400-R2 findings 已关闭：**1 / 3**
- PI-400-R2 findings 未关闭：**2 / 3**
- 历史 G3 其他 finding 原形重新打开：**0**
- 设计测试：**104 defined / 0 executed**
- runtime tests created：**0**
- implementation：**false**

去重口径：whole path 缺失同时影响冻结保真、声明边界、G2 与测试正例，只计一个 High 和一个关键证据缺失类别；external snapshot 不可解析同时使 locator 与 `LOSSLESS` 不可证，只计一个 Medium 和一个关键证据缺失类别；`G4-M-02` 已关闭，不再计 Medium 或回归。两个开放问题均是 R2 finding 的未关闭根因，不另计“新独立回归”。

---

## 5. 设计测试声明

- PI-300 的 T01–T104 连续编号完整：**104 defined**。
- 本复评创建 runtime tests：**0**。
- 本复评执行 tests：**0 executed**。
- pytest、CLI、YAML evaluator、resolver、renderer、dispatcher、artifact、feedback 与 learning 流程：**均未运行**。
- T74–T89 提供 declaration/member/binding、双射/基数、置换、reorder、单轴/双轴、participation 与 basis falsifier。
- T90–T101 提供 source locator、state/event/outcome、字段缺失、identity/digest mismatch、mapping 缺失、free-text 与 bounded-output falsifier。
- T102–T104 提供 registry hit、issue 传播与综合 fail-closed falsifier。
- 上述均是设计用例，不是 resolver 能解析当前路径、snapshot 实际存在、digest 命中或 reason registry 已在 runtime 执行的证据。

---

## 6. 唯一最终裁决

# BLOCKED

技术 PASS 要求 High、Medium、critical ambiguity、关键证据缺失和新回归全部清零；本次为 `1 / 1 / 0 / 2 / 0`，且三项 R2 finding 仅关闭 `1 / 3`，不满足清零条件。

---

## 7. 治理下一步

仅建议启动一个与本复评分离的有界整改实例，分别处理：

1. 使用冻结源已经正式定义、可机械解析的 whole F09 field identity；若当前冻结对象粒度不支持该引用，应明确 fail closed，不得再次以设计 prose 发明 path。
2. 使 state/event/outcome 的 locator 终止于实际存在、不可变且摘要可核对的 source snapshot，并保持字段级 COPY、version、captured time 与 digest/content 联合一致。

整改实例不得自验。整改完成后必须由新的独立 G4 复评实例重新检查三项历史 finding 与完整十域；`G5/PI-500=BLOCKED`，不得进入实现、运行测试、改变 production-default 或把本裁决解释为用户批准。
