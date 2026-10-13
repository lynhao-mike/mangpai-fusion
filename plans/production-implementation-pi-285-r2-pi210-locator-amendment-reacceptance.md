# PI-285-R2：PI-210 locator amendment 独立复验记录

> `task_id`: PI-285-R2  
> `parent_task_id`: PI-200  
> `mode`: independent amendment re-acceptance readonly + review record write  
> 裁决日期：2026-07-20（Asia/Shanghai）  
> 唯一裁决：**BLOCKED**

## 1. 独立性与范围

本实例独立于 [`PI-215-R2`](production-implementation-pi-215-r2-locator-amendment-remediation.md:1)，不继承其 `COMPLETED` 声明、自检结论或 finding closure 主张。复验直接对照 [`PI-285-R1 验收矩阵`](production-implementation-pi-285-r1-pi210-locator-amendment-acceptance.md:29)，机械检查整改后的 [`PI-210 SourceLocator`](production-implementation-pi-210-normalized-evidence-model.md:263)、[`PI-210 resolver 端口`](production-implementation-pi-210-normalized-evidence-model.md:1131)、[`PI-215-R1 修订说明`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:1)、[`PI-215-R2 整改记录`](production-implementation-pi-215-r2-locator-amendment-remediation.md:1)、[`PI-230 身份原则`](production-implementation-pi-230-traceability-binding.md:112)、[`F09 冻结原文`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)、[`PI-300 旧 locator fixture`](production-implementation-pi-300-one-card-vertical-slice-design.md:449)及直接相关既有 G2 记录 [`PI-290-R3`](production-implementation-pi-290-r3-g2-reacceptance.md:1) 与 [`PI-295-R1`](production-implementation-pi-295-r1-g2-amendment-acceptance.md:1)。

本次只读取上述范围并新建本复验记录。未修改 [`PI-210`](production-implementation-pi-210-normalized-evidence-model.md:1)、[`PI-215-R1`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:1)、[`PI-215-R2`](production-implementation-pi-215-r2-locator-amendment-remediation.md:1)、PI-220、PI-230、PI-300、冻结契约、mapping、总控、handoff、代码或测试；未实现 resolver，未创建 snapshot，未执行 YAML，未运行测试，未进入 G5，未递归委派。

按用户确认的严格口径：[`PI-210`](production-implementation-pi-210-normalized-evidence-model.md:1) 内任何仍可解释为旧版 `SourceLocator` 顶层 version/digest/time 语义的残留均计 finding；[`PI-300`](production-implementation-pi-300-one-card-vertical-slice-design.md:449) 的旧 locator 只作为预期未迁移且必须 fail-closed 的回归样本，不要求本任务整改。

判定严格 fail-closed：任一 High、Medium、critical ambiguity、关键证据缺失或新回归即为 **BLOCKED**。验收方不替受验材料补隐含字段、映射、parser、canonicalization 或迁移规则。

## 2. 四 finding closure matrix

| Finding | R1 解除条件 | R2 机械证据 | 独立裁决 |
|---|---|---|---|
| H-01 | locator 必须可判别地承载 Markdown/JSON 的 snapshot、schema、contract、digest、time 联合身份；单一事实源；legacy 原子迁移并 fail closed | [`SourceLocator.binding`](production-implementation-pi-210-normalized-evidence-model.md:272) 是必填 `SourceBinding`；Markdown 与 immutable JSON 是互斥判别分支，各自具有必填 `binding_schema_version`、`source_snapshot_id`、`source_schema_version`、`contract_version`、结构化 `content_digest`、`captured_at`，见 [`SourceBinding`](production-implementation-pi-210-normalized-evidence-model.md:275)。[`单一事实源与 migration`](production-implementation-pi-210-normalized-evidence-model.md:318) 删除旧顶层三字段、禁止双写和从 source/mtime/path/default 补齐，缺字段或分支不明产生非空 `SOURCE_BINDING_MIGRATION_REQUIRED` issue。Markdown 联合校验见 [`resolver 第 7–8 步`](production-implementation-pi-210-normalized-evidence-model.md:356)；JSON binding 与 envelope 五元逐字段相等见 [`snapshot identity`](production-implementation-pi-210-normalized-evidence-model.md:402)。 | **CLOSED / PASS**。原 H-01 的 schema 表达缺口已机械关闭；但 PI-210 前部旧语义摘要形成新的 M-04，不回写为 H-01 未关闭。 |
| M-01 | 唯一 parser/profile；ATX source-byte identity；closing/whitespace；card token 精确边界与计数 | 唯一 profile 固定为 `markdown-source.commonmark-0.31.2-mdff-v1` 与 CommonMark 0.31.2 受支持子集，见 [`profile`](production-implementation-pi-210-normalized-evidence-model.md:330)。ATX opening、separator、optional closing 与 U+0020/U+0009 trim 均按 source bytes 定义，见 [`heading identity`](production-implementation-pi-210-normalized-evidence-model.md:332)。card token 只接受 `F0[1-9]`/`F1[0-2]`，左右不得邻接 ASCII `[A-Za-z0-9_]`，按起始 byte 不重叠计数，并给出 0/1/2 命中正反例，见 [`card identity`](production-implementation-pi-210-normalized-evidence-model.md:333)。 | **CLOSED / PASS**。parser、ATX 和 token 均为单值规则。 |
| M-02 | COPY 必须唯一规定 source-span continuation、indent、delimiter、soft/hard break、trim code points，并给出正反例 | label delimiter 与首个 leaf paragraph范围见 [`label identity`](production-implementation-pi-210-normalized-evidence-model.md:334)；COPY 输入与 continuation membership 见 [`MDFF_V1_COPY 第 1 步`](production-implementation-pi-210-normalized-evidence-model.md:361)；marker、indent columns、tab stop 与 container prefix stripping 见 [`第 2 步`](production-implementation-pi-210-normalized-evidence-model.md:362)；LF、hard-break 判别见 [`第 3 步`](production-implementation-pi-210-normalized-evidence-model.md:363)；soft→U+0020、hard→U+000A 且 marker 保留见 [`第 4 步`](production-implementation-pi-210-normalized-evidence-model.md:364)；trim 集仅 U+0020/U+0009，明确不 trim U+000A/U+00A0/U+3000，见 [`第 5 步`](production-implementation-pi-210-normalized-evidence-model.md:365)；正反例见 [`COPY examples`](production-implementation-pi-210-normalized-evidence-model.md:367)。 | **CLOSED / PASS**。多行 COPY 已定义为单值 source-span bytes 函数。 |
| M-03 | DigestRef 唯一 wire shape；JCS payload 摘要；envelope/payload 分离；binding equality | snapshot schema 将 envelope identity 与 `payload` 分离，见 [`ImmutableJsonSourceSnapshot`](production-implementation-pi-210-normalized-evidence-model.md:383)。唯一摘要输入为 `RFC8785-JCS-UTF8(payload)`，禁止摘要 envelope 或 self-digest 变体，见 [`payload digest`](production-implementation-pi-210-normalized-evidence-model.md:398)。唯一 wire shape 是结构化 `DigestRef`，固定小写 `sha256`、`RFC8785-JCS-UTF8` 与 64 lowercase hex，明确禁止 `sha256:<hex>`、裸 hex、uppercase 或 union，见 [`digest wire shape`](production-implementation-pi-210-normalized-evidence-model.md:399)。binding 与 envelope digest 三字段及其余 identity 逐字段相等，见 [`binding equality`](production-implementation-pi-210-normalized-evidence-model.md:402)。 | **CLOSED / PASS**。digest 表示、摘要输入与 equality 均唯一。 |

**四项统计：4 项 CLOSED/PASS，0 项未关闭。**

## 3. 完整回归矩阵

| # | 回归项 | 机械证据与判断 | 状态 |
|---:|---|---|---|
| 1 | 旧 JSON-like Markdown path unsupported | [`mdff:v1 dialect`](production-implementation-pi-210-normalized-evidence-model.md:336) 明确把 `/cards/F09/reality_hard_gate_and_dual_cards` 与 JSON Pointer 外观判为 `UNSUPPORTED_DIALECT`。[`PI-300 旧 fixture`](production-implementation-pi-300-one-card-vertical-slice-design.md:451) 仍使用该旧 path，故按迁移边界必须失败，不能被兼容猜测。 | PASS |
| 2 | F09 selector 对应原文整体 COPY | canonical selector 见 [`F09 selector`](production-implementation-pi-210-normalized-evidence-model.md:340)，heading 与 label 分别对应 [`F09 heading`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265) 和 [`现实硬门与双卡`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:269)。selector 只取整体原文，不拆六字段，见 [`非拆分规则`](production-implementation-pi-210-normalized-evidence-model.md:344)。 | PASS |
| 3 | heading/card/label 0 或多命中 | 三者均须恰一命中；0 命中与 duplicate/ambiguous 均 `UNRESOLVABLE`，见 [`唯一命中`](production-implementation-pi-210-normalized-evidence-model.md:371)。card token 的精确计数另由 [`card identity`](production-implementation-pi-210-normalized-evidence-model.md:333) 封闭。 | PASS |
| 4 | rename、alias、模糊与内容反推禁止 | label/heading rename、card drift、同值、编辑距离、翻译、slug、alias、邻近位置与从值反推均不得恢复，见 [`漂移规则`](production-implementation-pi-210-normalized-evidence-model.md:372)。 | PASS |
| 5 | Markdown profile/COPY fail-closed | unsupported structure、profile mismatch、ATX/token 边界错误、continuation 歧义、digest/value mismatch 均产生非空 issue 并阻断 PI-220 消费，见 [`失败目录`](production-implementation-pi-210-normalized-evidence-model.md:376)。 | PASS |
| 6 | snapshot actual file/object/pointer | locator 必须指向实际 `.json` 文件；对象为唯一键控 map；field path 只接受对象根 RFC 6901 pointer，见 [`snapshot path/object/pointer`](production-implementation-pi-210-normalized-evidence-model.md:397)。 | PASS |
| 7 | snapshot identity/digest fail-closed | 错分支、identity 任一 mismatch、object/pointer 失败、digest shape/value mismatch、envelope/payload 未分离及 JCS 失败均阻断，见 [`snapshot fail-closed`](production-implementation-pi-210-normalized-evidence-model.md:404)。 | PASS |
| 8 | `FrozenCardFieldRef` 形状与业务语义 | [`FrozenCardFieldRef`](production-implementation-pi-210-normalized-evidence-model.md:459) 仍为 card、contract、version、path、state、value、locator 七字段；binding 由 locator 承载。F09 冻结文本仍是 [`原业务语义`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:267)，amendment 未新增门、竞争、动作或输出语义。 | PASS |
| 9 | PI-230 兼容 | [`PI-230`](production-implementation-pi-230-traceability-binding.md:88) 继续复用 PI-210 规范类型；路径定位、digest 证明、version 解释三责不互代，见 [`身份原则`](production-implementation-pi-230-traceability-binding.md:112)。未发现要求 PI-230 增加竞争 locator schema。 | PASS |
| 10 | PI-210 内所有 `SourceLocator` 示例/接口使用点 | 规范 schema、演示中的三个普通 locator 与一个 Markdown locator 均使用恰一 `binding` 分支，见 [`SourceLocator`](production-implementation-pi-210-normalized-evidence-model.md:263)、[`普通 locator 示例`](production-implementation-pi-210-normalized-evidence-model.md:919)与[`Markdown locator 示例`](production-implementation-pi-210-normalized-evidence-model.md:1025)；resolver 端口只接受 canonical `mdff:v1` 与 `MARKDOWN_CONTRACT`，见 [`resolver interface`](production-implementation-pi-210-normalized-evidence-model.md:1131)。未发现实例继续使用旧顶层三字段。 | PASS |
| 11 | PI-210 内旧语义残留 | [`YAML 非执行边界`](production-implementation-pi-210-normalized-evidence-model.md:44) 仍把 `SourceLocator` 描述为“附录路径、版本和可选内容摘要”，见 [`旧摘要残留`](production-implementation-pi-210-normalized-evidence-model.md:49)。这与 [`SourceBinding 是唯一事实源`](production-implementation-pi-210-normalized-evidence-model.md:318)、冻结/validated COPY 的 digest 必填以及旧顶层 version/digest/time 已删除不一致；读者可把 version/digest 继续解释为 locator 顶层属性，并把 digest 解释为 optional。按本次明确严格口径，该结构语义残留构成 M-04。 | **BLOCKED** |

**回归矩阵统计：11 项；10 项 PASS，1 项 BLOCKED。**

## 4. Findings 与精确统计

### M-04：PI-210 前部仍保留旧版 SourceLocator 的“版本 + 可选摘要”语义

- 级别：**Medium**。
- 类型：**critical ambiguity + new internal-document regression/residual**。
- 直接证据：[`PI-210 第 2.2 节`](production-implementation-pi-210-normalized-evidence-model.md:44) 将 `SourceLocator` 概括为“附录路径、版本和可选内容摘要”，见 [`第 49 行`](production-implementation-pi-210-normalized-evidence-model.md:49)；修订后的规范 schema 则只有 path/object/field 和必填判别式 `binding`，见 [`SourceLocator`](production-implementation-pi-210-normalized-evidence-model.md:263)，并明确 `SourceBinding` 才是 snapshot/version/digest/time 唯一事实源、旧顶层三字段已删除，见 [`唯一事实源与删除规则`](production-implementation-pi-210-normalized-evidence-model.md:318)。
- 机械冲突：前部摘要未说 version/digest 位于 `binding`，且把 content digest 标成 optional；冻结 Markdown/immutable JSON 分支的 digest 实际必填，只有受限的 `UNVERSIONED_SOURCE` 分支不携带版本身份且不得用于 frozen/validated COPY。该摘要因此允许至少两种结构解释：旧顶层可选字段，或新 binding 内分支字段。
- 影响：破坏“breaking change 在 PI-210 文档内部所有接口/使用点一致”的验收条件；实现者若按前部边界构造 locator，可能继续生成已被后文禁止的旧顶层字段或缺 digest locator。后文 fail-closed 能拒绝该实例，但不能消除规范文档自身的结构歧义。
- 解除条件：由与本验收分离的整改任务将该摘要改为与判别式 `SourceBinding` 完全一致的口径，明确 path/object/field 负责定位，binding 是 snapshot/version/digest/time 唯一事实源；不得继续把 frozen/validated locator 的 digest 描述为 optional。整改后须创建新的独立复验。

### 精确统计

- R1 findings mechanically closed：**4/4**（H-01、M-01、M-02、M-03）。
- High findings：**0**。
- Medium findings：**1**（M-04）。
- Low findings：**0**。
- Informational findings：**0**。
- Critical ambiguities：**1**（M-04）。
- Critical evidence gaps：**0**。
- New regressions/residual inconsistencies：**1**（M-04）。
- FrozenCardFieldRef shape regressions：**0**。
- PI-230 compatibility regressions：**0**。
- F09 text/business-semantic regressions：**0**。
- Snapshot fail-closed regressions：**0**。

## 5. Tests 与 YAML 执行声明

- Tests executed：**0**。
- YAML executed：**0**。
- Resolver implementations executed：**0**。
- Production commands executed：**0**。
- Snapshots created：**0**。
- Reviewed artifacts modified：**0**。
- New review records written：**1**，即 [`本独立复验记录`](production-implementation-pi-285-r2-pi210-locator-amendment-reacceptance.md:1)。

本裁决只构成限定文档契约的静态机械复验，不是 runtime、parser、JCS serializer、digest verifier 或 source resolver 的实现证明。

## 6. 唯一裁决

# BLOCKED

PI-285-R1 的 H-01、M-01、M-02、M-03 均已由当前规范机械关闭：判别式 binding 与原子 migration、唯一 CommonMark/parser/token profile、单值 source-span COPY、唯一结构化 DigestRef 与 payload-only JCS 摘要均已形成明确契约；旧 JSON-like path、F09 整体原文 COPY、0/多命中、业务语义、PI-230 兼容和 snapshot fail-closed 也未回归。

但 [`PI-210`](production-implementation-pi-210-normalized-evidence-model.md:49) 内仍有一处可被解释为旧版 `SourceLocator` 顶层“版本 + 可选摘要”的结构语义残留，与后文必填判别式 binding 和旧顶层字段删除规则冲突。该项构成 **1 项 Medium、1 项 critical ambiguity、1 项 new internal-document regression/residual inconsistency**。

依照“任一 High/Medium、critical ambiguity、关键证据缺失或新回归即 BLOCKED”以及“任何旧字段残留造成结构歧义均算 finding”的规则，本 amendment 本轮不通过独立复验。不得以四项原 finding 已关闭覆盖新 finding，也不得由本验收实例自行整改。

## 7. 唯一下一动作

**由与本验收实例分离的整改任务仅处理 M-04；整改完成后创建新的独立 amendment 复验。**

在新的独立复验给出 PASS 前，不得进入 PI-470-R3、PI-300 fixture 整改、G4 复评、resolver 实现、测试、生产接线或 G5。