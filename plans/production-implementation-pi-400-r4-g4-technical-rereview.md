# PI-400-R4 · F09 单卡 G4 独立技术复评

> 任务编号：PI-400-R4  
> 父任务：PI-400 / G4  
> 复评日期：2026-07-20（Asia/Shanghai）  
> 文档性质：独立、只读、fail-closed 技术复评  
> 复评对象：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)  
> 前次 finding 基线：[`production-implementation-pi-400-r3-g4-technical-rereview.md`](production-implementation-pi-400-r3-g4-technical-rereview.md:29)

---

## 1. 独立性、范围与判定纪律

本复评实例独立于 PI-300、PI-470-R3 及既有 PI-400 review/remediation 实例。PI-470-R3 的整改自述不作为验收证据；本结论只依据仓库当前事实源、原始 Markdown/JSON 字节和本次独立机械核验结果。

复评范围严格限定为 F09 单卡静态设计：

- 机械复核 R3 尚开放的 `G4-H-01`、`G4-M-01`；
- 复核 `G4-M-02` 是否持续关闭；
- 对冻结语义、声明性边界、G2 一致性、端到端兼容、失败模式、测试充分性、production-default、回滚/幂等/审计、范围/治理、历史 findings/新回归十域作静态回归；
- F08 只允许 identity-only competition，不执行第二张卡；
- 不修改 PI-300、PI-210、PI-220、PI-230、冻结契约、mapping、control、代码或测试；
- 不执行声明性 YAML，不运行 PI-300 T01–T104，不进入 G5，不声称 runtime 实现或用户批准；
- `implementation=false`；本次唯一仓库写入为本复评记录。

判定采用严格 fail-closed 纪律：任一 High、Medium、critical ambiguity、关键证据缺失、语义/架构边界违反或相关回归均返回 `BLOCKED`。

## 2. 事实源

本次直接核对：

1. [`production-implementation-pi-400-r3-g4-technical-rereview.md`](production-implementation-pi-400-r3-g4-technical-rereview.md:29)：R3 finding 基线；
2. [`production-implementation-pi-285-r3-pi210-locator-amendment-reacceptance.md`](production-implementation-pi-285-r3-pi210-locator-amendment-reacceptance.md:1)：PI-210 locator amendment 的独立接受记录；
3. [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:260)：`SourceLocator`、`SourceBinding`、`mdff:v1`、immutable JSON、RFC6901 与转换契约；
4. [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:1)：member identity、基数/双射、置换 falsifier 与 reason-code registry；
5. [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:84)：全链来源绑定与转换终止边界；用户给出的旧文件名 `production-implementation-pi-230-declarative-mapping.md` 在仓库中不存在，实际 PI-230 事实源为本文件；
6. [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:449)：被评设计；
7. [`production-implementation-pi-300-f09-source-snapshots-v1.json`](production-implementation-pi-300-f09-source-snapshots-v1.json:1)：实际 immutable JSON fixture；
8. [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)：冻结 F09 Markdown 原文。

仓库没有独立的 PI-470-R3 文件；当前 PI-300 第 7.2、7.4、10、18 节承载其有界整改记录。该缺少独立文件的事实不构成证据缺口，因为本复评不采信整改自述，而直接核验最终被评 artifact 和实际来源文件。

---

## 3. 独立机械核验

### 3.1 Markdown 原始字节、摘要与 `mdff:v1`

对 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:1) 读取原始字节后执行 PI-210 的 `RAW-UTF8-NO-BOM-LF` 规范化：

- BOM：无；
- 原文件 CRLF：437 个；bare CR：0；
- 规范化：去 BOM（本文件无）并将 CRLF/CR 转 LF；
- SHA-256 独立重算结果：

```text
30ea0f8b8a91f95bc0a52ff90188740c2cc2282fcab27cd20be70404253d7a2f
```

该值与 PI-300 的结构化 Markdown `DigestRef` 完全一致，见 [`Markdown SourceBinding`](production-implementation-pi-300-one-card-vertical-slice-design.md:454)。其 binding 分支逐字段为：

- `binding_kind=MARKDOWN_CONTRACT`；
- `binding_schema_version=source-binding.markdown.v1`；
- `source_schema_version=markdown-source.commonmark-0.31.2-mdff-v1`；
- `contract_version=real-world-function-evidence-cards-v1`；
- `canonicalization=RAW-UTF8-NO-BOM-LF`；
- digest 为 64 位 lowercase hex；
- path 为实际存在的冻结 Markdown；
- `object_id=F09`。

机械解析 PI-300 selector 得到：

```text
mdff:v1/heading/4.9%20F09%20%E8%B5%84%E6%9C%AC%E9%85%8D%E7%BD%AE%E4%B8%8E%E9%A3%8E%E9%99%A9%E6%89%BF%E6%8B%85/card/F09/item/%E7%8E%B0%E5%AE%9E%E7%A1%AC%E9%97%A8%E4%B8%8E%E5%8F%8C%E5%8D%A1
```

解码后为 heading=`4.9 F09 资本配置与风险承担`、card=`F09`、label=`现实硬门与双卡`。三个 token 经 NFC 和 RFC3986 UTF-8 percent-encoding 重编码后逐字节等于原 selector，故 selector canonical。冻结文件内 heading 命中数为 1、该 heading 下直接列表项命中数为 1。

按 PI-210 `MDFF_V1_COPY` 对冒号后 source span 取值，得到：

```text
资源、对象、配置轴、风险轴、归属和时态分别过门；单轴仅限定成立，双轴才是强主。状态证明基准日持续位置，事件证明指定窗口变化；S1–S3、E1–E3 与动作、资本、责任后果正交。
```

该 COPY 与 PI-300 [`FrozenCardFieldRef.declared_value`](production-implementation-pi-300-one-card-vertical-slice-design.md:467) 逐码点完全相等。被评 PI-300 中已不存在 legacy `/cards/F09/reality_hard_gate_and_dual_cards`。

### 3.2 JSON 唯一键、payload JCS 与联合身份

对 [`production-implementation-pi-300-f09-source-snapshots-v1.json`](production-implementation-pi-300-f09-source-snapshots-v1.json:1) 使用拒绝重复键的 JSON object-pairs parser 解析：所有 envelope、payload 和嵌套对象均无重复 key。

按 PI-210 仅对顶层 `payload` 执行 RFC8785 JCS UTF-8 序列化并计算 SHA-256，独立结果为：

```text
67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7
```

该值同时等于 JSON envelope [`content_digest.value`](production-implementation-pi-300-f09-source-snapshots-v1.json:5) 和 PI-300 [`F09-SOURCE-SNAPSHOT-BINDING`](production-implementation-pi-300-one-card-vertical-slice-design.md:767)。未将 envelope 纳入 digest。

binding 与 envelope 联合身份逐值一致：

| 字段 | 值 | 结果 |
|---|---|---|
| source snapshot | `PI-300-F09-SOURCE-SNAPSHOT-V1` | 一致 |
| source schema / snapshot schema | `reality-fact-source-snapshot.v1` | 一致 |
| contract version | `pi-300-f09-source-snapshots-v1` | 一致 |
| digest algorithm | `sha256` | 一致 |
| canonicalization | `RFC8785-JCS-UTF8` | 一致 |
| digest value | `67517f…f5e7` | 一致 |
| captured time | `2026-07-19T00:00:00Z` | 一致 |

fixture 保持 envelope/payload 分离，identity metadata 不在 payload 内；PI-300 locator 使用 PI-210 的 `IMMUTABLE_JSON_SNAPSHOT` 判别分支和结构化 `DigestRef`，未使用旧顶层 locator identity 双写。

### 3.3 RFC6901 pointer 与 exact field COPY

所有 pointer 均从命中的 source object 根开始解析，13/13 成功：

| Source object | Pointer | 解析值 | PI-300 target |
|---|---|---|---|
| `SOURCE-STATE-1` | `/value/level` | `S2` | `/payload/value/level` |
| `SOURCE-STATE-1` | `/value/position` | `持续承担资本配置职责` | `/payload/value/position` |
| `SOURCE-STATE-1` | `/value/as_of` | `2026-06-30` | `/temporal_scope/as_of/value` |
| `SOURCE-EVENT-1` | `/value/level` | `E2` | `/payload/value/level` |
| `SOURCE-EVENT-1` | `/value/change` | `配置责任范围扩大` | `/payload/value/change` |
| `SOURCE-EVENT-1` | `/value/interval/start` | `2026-04-01` | `/temporal_scope/interval/start/value` |
| `SOURCE-EVENT-1` | `/value/interval/end` | `2026-06-30` | `/temporal_scope/interval/end/value` |
| `SOURCE-EVENT-1` | `/value/interval/start_inclusive` | `true` | `/temporal_scope/interval/start_inclusive` |
| `SOURCE-EVENT-1` | `/value/interval/end_inclusive` | `true` | `/temporal_scope/interval/end_inclusive` |
| `SOURCE-OUTCOME-1` | `/value/axis` | `allocation` | `/payload/value/axis` |
| `SOURCE-OUTCOME-1` | `/value/action` | `重配资本额度` | `/payload/value/action` |
| `SOURCE-OUTCOME-1` | `/value/object` | `经营单元A` | `/payload/value/object` |
| `SOURCE-OUTCOME-1` | `/value/tense` | `current` | `/payload/value/tense` |

上述值与 [`STATE/EVENT/OUTCOME EvidenceRecord`](production-implementation-pi-300-one-card-vertical-slice-design.md:797) 中对应 normalized target 逐值相等。三条转换 [`TR-F09-STATE-1`](production-implementation-pi-300-one-card-vertical-slice-design.md:824)、[`TR-F09-EVENT-1`](production-implementation-pi-300-one-card-vertical-slice-design.md:829)、[`TR-F09-OUTCOME-1`](production-implementation-pi-300-one-card-vertical-slice-design.md:834) 均满足：

- source object ID 命中实际 fixture；
- source locator 终止到同一实际文件；
- 所有 source pointer 可解析；
- operation 均为 `COPY`；
- fidelity 均为 `LOSSLESS`；
- `dropped_fields=[]`；
- `dropped_object_refs=[]`；
- `synthesized_fields=[]`；
- target 值与 source 值逐值相等。

被评 PI-300 中不存在 `cases/CASE-DEMO/source-snapshots.json`。PI-300 明确把 inline prose 标为 non-normative preview，并规定唯一来源终点为实际 JSON fixture，见 [`actual fixture boundary`](production-implementation-pi-300-one-card-vertical-slice-design.md:764)；T99 和失败注入同时拒绝 prose 结构化攻击。

### 3.4 G2 member identity、双射、基数与置换

PI-300 的 [`MDECL-F09-V1`](production-implementation-pi-300-one-card-vertical-slice-design.md:474) 保留六个唯一稳定 member identity：RESOURCE、OBJECT、ALLOCATION、RISK、ATTRIBUTION、TENSE。每个完整 gate fixture 都含六条 records，并通过 `declared_member_id` 与 declarations 形成全双射；去重的 `gate_definition_refs` 恰含一个真实整体 F09 ref。

T74–T81 连续覆盖：全覆盖正例、duplicate/omitted、unknown member、shared-ref inconsistency、declaration version/digest 漂移、evaluation binding mismatch、permutation attack、record reorder invariance，见 [`T74–T81`](production-implementation-pi-300-one-card-vertical-slice-design.md:1104)。未发现 G2 稳定身份、cardinality、full bijection 或 permutation falsifier 回归。

### 3.5 reason code 与测试编号

CONDITIONAL 和 RISK-ONLY 的 evaluator `UNKNOWN` 均使用 `GATE.STATE_UNKNOWN`，见 [`CONDITIONAL UNKNOWN`](production-implementation-pi-300-one-card-vertical-slice-design.md:504) 与 [`RISK-ONLY UNKNOWN`](production-implementation-pi-300-one-card-vertical-slice-design.md:553)。该值命中 PI-220 注册目录；T102 要求 registry hit，T104 拒绝未注册值。未发现替代该状态的未注册 UNKNOWN reason code。

机械提取测试矩阵行并按数值检查：共 104 行、104 个唯一 ID、最小 T01、最大 T104、排序后严格等于 1..104，无缺号、无重复。它们全部是静态设计用例；本次没有创建或执行 runtime test。

---

## 4. R3 findings 关闭矩阵

| Finding | 独立机械结果 | 状态 |
|---|---|---|
| `G4-H-01` | canonical `mdff:v1` 唯一解析到真实 F09 列表项；Markdown digest 独立命中；`MDFF_V1_COPY` 与 `declared_value` exact；legacy path 消失；六 member identity、基数、全双射和置换/reorder falsifier 未回归 | **已关闭** |
| `G4-M-01` | 实际 JSON fixture 存在；唯一键成立；envelope/payload、immutable binding 和结构化 digest 符合 PI-210；payload-only JCS digest 独立命中；13/13 pointers 解析；三个 `LOSSLESS` 转换逐字段终止且值相等；旧 CASE-DEMO path 消失；prose 非来源终点 | **已关闭** |
| `G4-M-02` | `GATE.STATE_UNKNOWN` 仍是设计中两个 UNKNOWN 正例的注册 reason code；T102/T104 保留 registry-hit/未注册拒绝 falsifier | **持续关闭** |

R3 两项开放 finding 已关闭：**2 / 2**。三项历史 finding 当前关闭：**3 / 3**。

---

## 5. 十域静态回归矩阵

| # | 评审域 | 结果 | 独立判断 |
|---:|---|---|---|
| 1 | 冻结语义保真 | **符合** | whole F09 ref 机械命中正式冻结原文；六维、单轴/双轴、state/event 和 bounded outcome 四要素未被改写。 |
| 2 | 声明性边界 | **符合** | 使用已接受的 Markdown/JSON locator 契约；mapping 只作声明引用，未执行 YAML、未新增 evaluator 算法或自然语言编译语义。 |
| 3 | G2 一致性 | **符合** | member declaration/binding、六维基数、全双射、置换/reorder、注册 reason code、来源/转换引用均与 PI-210/220 边界一致。 |
| 4 | 端到端兼容 | **符合（静态设计）** | source→evidence→decision→trace→statement→artifact→feedback→eligibility 结构保持闭合；不把静态闭合声称为 runtime 已实现。 |
| 5 | 失败模式 | **符合** | selector/profile/digest/pointer/object/binding/registry 不匹配均有 fail-closed 负例；prose、metadata、旧路径和降级分支不得补链。 |
| 6 | 测试充分性 | **符合（设计层）** | T01–T104 连续且覆盖正反例；T74–T104 对本轮关键 identity、permutation、source、digest、pointer、LOSSLESS、registry 回归有明确 falsifier。执行数仍为 0。 |
| 7 | production-default 兼容 | **符合** | production/staged/preprod 继续分账，跨轨仅 `AUDIT_ONLY`；没有 production-default 代码或默认行为变更。 |
| 8 | 回滚/幂等/审计 | **符合** | item/set 状态分账、same-key digest 规则、partial write、supersede、feedback eligibility 和不可学习边界未见回归。 |
| 9 | 范围/治理 | **符合** | 仅 F09；F08 identity-only；无实现、无测试执行、无 YAML 执行、无 G5、无用户批准声明。 |
| 10 | 历史 findings/新回归 | **符合** | `G4-H-01`、`G4-M-01` 机械关闭；`G4-M-02` 持续关闭；未发现新的相关 High/Medium、ambiguity、证据缺口或回归。 |

---

## 6. 精确统计与实施状态

- High：**0**
- Medium：**0**
- critical ambiguity：**0**
- 关键证据缺失：**0 类**
- 语义/架构边界违反：**0 类**
- 相关回归：**0 类**
- R3-open findings 已关闭：**2 / 2**
- 历史 findings 当前关闭：**3 / 3**
- 设计测试：**104 defined / 0 executed**
- runtime tests created：**0**
- runtime tests executed：**0**
- implementation：**false**
- production-default behavior change：**无**

机械审查命令只读取文件、解析字节/JSON、计算摘要、解析 selector/pointers 和检查静态测试编号；它们不构成 T01–T104 的执行。

---

## 7. 唯一最终裁决

# PASS

本次技术复评达到 fail-closed 清零条件：High、Medium、critical ambiguity、关键证据缺失、语义/架构边界违反和相关回归均为 0；R3 的两项开放 finding 均有独立机械证据关闭，`G4-M-02` 持续关闭。

该 `PASS` **仅是技术清关**，不是用户批准，不是实现完成，不是 runtime 测试通过，也不授权进入 G5。

父任务只能同步为：

```text
G4=REVIEW / AWAITING_USER_APPROVAL
```

`G5/PI-500` 继续保持 `BLOCKED`；在用户明确批准前，不得编写实现计划、实现生产代码、执行声明性 mapping、运行 PI-300 测试矩阵或改变 production-default。
