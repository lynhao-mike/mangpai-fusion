# PI-285-R1：PI-210 locator amendment 独立验收记录

> 任务：PI-285-R1  
> 父任务：PI-200  
> 性质：独立 amendment acceptance；受验材料只读；仅写本验收记录  
> 裁决日期：2026-07-20（Asia/Shanghai）

## 1. 独立性与范围

本实例独立于 [`PI-215-R1`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:1)，不继承其完成声明或静态自检结论。验收对象是 [`PI-210`](production-implementation-pi-210-normalized-evidence-model.md:260) 中新增的 Markdown frozen-field locator amendment，以及 [`PI-215-R1`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:1) 对该 amendment 的说明记录。

本次直接证据边界为：

1. [`PI-210 来源与验证状态`](production-implementation-pi-210-normalized-evidence-model.md:260)；
2. [`PI-210 resolver 设计期端口`](production-implementation-pi-210-normalized-evidence-model.md:1076)；
3. [`PI-215-R1 amendment 说明`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:1)；
4. [`PI-230 身份原则`](production-implementation-pi-230-traceability-binding.md:112)；
5. [`PI-400-R3 G4 finding 基线`](production-implementation-pi-400-r3-g4-technical-rereview.md:29)；
6. [`F09 冻结原文`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)，特别是 [`现实硬门与双卡`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:269)；
7. [`PI-300 旧 frozen field path`](production-implementation-pi-300-one-card-vertical-slice-design.md:449)；
8. 直接相关既有 G2 验收记录：[`PI-290-R3`](production-implementation-pi-290-r3-g2-reacceptance.md:141) 与 [`PI-295-R1`](production-implementation-pi-295-r1-g2-amendment-acceptance.md:20)。

Git SHA 与提交历史不属于证据边界；本记录只按明确文件与行号裁决，不从历史推断修改事实。当前证据显示 [`FrozenCardFieldRef`](production-implementation-pi-210-normalized-evidence-model.md:415) 仍保持原有七字段形状，amendment 只对其 [`field_path`](production-implementation-pi-210-normalized-evidence-model.md:419) 增加解释；[`PI-230 身份原则`](production-implementation-pi-230-traceability-binding.md:112) 未出现 locator 专用替代 schema；[`F09 原文`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265) 保持不变。该判断不外推为提交历史证明。

本次不修改 [`PI-210`](production-implementation-pi-210-normalized-evidence-model.md:1)、[`PI-215-R1`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:1)、[`PI-220`](production-implementation-pi-220-decision-interface.md:1)、[`PI-230`](production-implementation-pi-230-traceability-binding.md:1)、[`PI-300`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)、冻结契约、mapping、总控、handoff、代码或测试；不实现 resolver，不执行 YAML，不运行测试，不进入 G5，不递归委派。

判定采用严格 fail-closed：任一 High、Medium、关键歧义、关键证据缺失或新回归即为 [`BLOCKED`](production-implementation-pi-400-r3-g4-technical-rereview.md:25)。不得由验收方替 amendment 补充隐含字段、隐含映射、词法规则、parser profile 或 canonicalization 规则。

## 2. 验收矩阵

| # | 验收项 | 机械证据与独立判断 | 状态 |
|---:|---|---|---|
| 1 | dialect 与 version | 正式前缀和固定段为 [`mdff:v1/heading/<H>/card/<C>/item/<L>`](production-implementation-pi-210-normalized-evidence-model.md:299)，名称和版本大小写敏感且只支持 v1，见 [`unsupported 规则`](production-implementation-pi-210-normalized-evidence-model.md:307)。 | PASS |
| 2 | heading identity | [`<H>`](production-implementation-pi-210-normalized-evidence-model.md:303) 绑定 ATX heading 完整原文，不使用 slug、序号位置或语义 alias；但“去掉行首 marker 后的完整原文”与 CommonMark block parse 所产生的 heading content 对可选 closing sequence、前后空白的处理没有给出唯一取值规则，见 M-01。 | BLOCKED |
| 3 | card identity | [`<C>`](production-implementation-pi-210-normalized-evidence-model.md:304) 必须来自 heading 内恰一显式 F01–F12 token且逐码点相等；禁止从正文、文件名、主题或 mapping 推断。但“独立 token”没有定义左右边界、允许分隔符或词法算法，故一般输入不能唯一判断 token 数，见 M-01。 | BLOCKED |
| 4 | label identity | [`<L>`](production-implementation-pi-210-normalized-evidence-model.md:305) 取直接无序列表项中首个非 code-span 冒号前的完整 label，禁止翻译、snake_case、slug、同义改写与 alias。该结构身份和漂移纪律明确。 | PASS |
| 5 | escaping 与 canonical roundtrip | [`NFC + UTF-8 octet + RFC 3986 percent-encoding`](production-implementation-pi-210-normalized-evidence-model.md:306) 规定 unreserved 集、强制大写 hex，并拒绝非法解码、非最短 UTF-8、非 NFC、小写 hex、转义 unreserved 及 roundtrip 不同输入。 | PASS |
| 6 | parse 范围与非位置匹配 | resolver 要求 [`CommonMark-compatible block parse`](production-implementation-pi-210-normalized-evidence-model.md:323)，拒绝 HTML、全文正则、模糊搜索、setext、表格、伪列表与 code block；card object 由同级或更高 heading 截止，label 只在直接列表子项匹配，见 [`对象边界与直接子项`](production-implementation-pi-210-normalized-evidence-model.md:324)。但未注册 CommonMark 版本/profile，并与 heading text 提取规则留下 M-01。 | BLOCKED |
| 7 | 唯一命中与 0/多命中 | heading、card、label 均要求恰一命中；0 命中和多命中均为 [`UNRESOLVABLE`](production-implementation-pi-210-normalized-evidence-model.md:332)，不 fallback。 | PASS |
| 8 | 不依赖位置、模糊、语义或 alias | label/heading rename、card 漂移、同值、编辑距离、翻译、slug、alias、邻近位置和从值反推 label 均不得恢复，见 [`漂移规则`](production-implementation-pi-210-normalized-evidence-model.md:333)。 | PASS |
| 9 | F09 正式 selector 对应原文 | 正式 selector 的 heading 解码为“4.9 F09 资本配置与风险承担”，label 解码为“现实硬门与双卡”，见 [`F09 canonical selector`](production-implementation-pi-210-normalized-evidence-model.md:309)；两者分别精确对应 [`F09 heading`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265) 与 [`F09 列表项`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:269)。当前 F09 正例为一行，不触发 continuation ambiguity。 | PASS |
| 10 | 旧 JSON-like path unsupported | 旧 [`/cards/F09/reality_hard_gate_and_dual_cards`](production-implementation-pi-300-one-card-vertical-slice-design.md:451) 被明确归类为 [`UNSUPPORTED_DIALECT`](production-implementation-pi-210-normalized-evidence-model.md:307)，不得按 JSON Pointer 外观兼容。 | PASS |
| 11 | declared value 规范 COPY | resolver 要取 delimiter 后 inline source 和 continuation lines，禁止渲染、实体解码、语义拆分或归一化，并将结果与 [`FrozenCardFieldRef.declared_value`](production-implementation-pi-210-normalized-evidence-model.md:328) 逐值核对。可是 hard-break 的输出表示、continuation line 的精确归属及“Markdown whitespace”集合没有被唯一规定，导致多行值可能产生多个合法 COPY，见 M-02。 | BLOCKED |
| 12 | path/object/field 职责 | [`path/object_id/field_path`](production-implementation-pi-210-normalized-evidence-model.md:335) 分别选择文件、声明对象身份和选择字段，三者缺一不可且不能拼接替代；Markdown object ID 必须等于 card identity。 | PASS |
| 13 | digest/version/time 职责 | [`content_digest/version/captured_at`](production-implementation-pi-210-normalized-evidence-model.md:336) 分别证明、解释和标记采集；不能替代定位，时间不能取 mtime。职责原则与 [`PI-230`](production-implementation-pi-230-traceability-binding.md:117) 一致。 | PASS |
| 14 | Markdown 联合 binding 可表达性 | resolver 要联合校验 contract/schema version、digest 与 time，并要求 ref contract version 与 locator version binding 一致，见 [`resolver 第 7–8 步`](production-implementation-pi-210-normalized-evidence-model.md:327)。但 [`SourceLocator`](production-implementation-pi-210-normalized-evidence-model.md:263) 只有一个 [`schema_version`](production-implementation-pi-210-normalized-evidence-model.md:272)，没有 contract-version binding 的字段或规范映射，因而该一致性无法机械表达，见 H-01。 | BLOCKED |
| 15 | snapshot actual file 与 canonical JSON | locator 必须指向实际存在的 repository-relative JSON 文件；prose、内联或未来路径不能替代，见 [`actual file 规则`](production-implementation-pi-210-normalized-evidence-model.md:354)。文件格式、JCS bytes、显式算法与 self-digest 排除/外置规则见 [`canonical JSON 规则`](production-implementation-pi-210-normalized-evidence-model.md:355)。 | PASS |
| 16 | snapshot object uniqueness 与 JSON Pointer | [`objects`](production-implementation-pi-210-normalized-evidence-model.md:350) 必须是 object ID 唯一键控的非空 map；禁止数组位置和 duplicate key。字段定位只接受从对象根开始的 RFC 6901 pointer，禁止 JSONPath、模糊键、alias 和 prose，见 [`object/pointer 规则`](production-implementation-pi-210-normalized-evidence-model.md:356)。 | PASS |
| 17 | snapshot 联合 identity | 规范要求 snapshot ID、snapshot schema version、contract version、digest、captured time 构成联合 identity，并要求 locator 与五者、object ID、pointer 全部一致，见 [`联合 identity`](production-implementation-pi-210-normalized-evidence-model.md:358)。但 locator 无 snapshot ID、snapshot schema version 和 contract version 的独立承载字段，也没有从现有字段到五元组的规范映射，故无法机械终止，见 H-01。 | BLOCKED |
| 18 | snapshot change 产生新 identity | 内容、schema、contract、对象或字段任一变化必须产生新 identity 与 digest，禁止同 identity 覆写；相同 identity/digest 只能表示同一 canonical JSON，见 [`immutable change 规则`](production-implementation-pi-210-normalized-evidence-model.md:359)。 | PASS |
| 19 | snapshot digest 表示一致性 | schema 将 [`content_digest`](production-implementation-pi-210-normalized-evidence-model.md:348) 定义为 [`DigestRef`](production-implementation-pi-210-normalized-evidence-model.md:106)，即带 algorithm、canonicalization、value 的结构；紧接规则却要求至少形如 sha256 前缀加小写 hex 的单值串，见 [`digest 文本规则`](production-implementation-pi-210-normalized-evidence-model.md:355)。未定义两者的唯一序列化或等价关系，见 M-03。 | BLOCKED |
| 20 | snapshot fail-closed | snapshot/object/pointer missing 或 duplicate、unsupported pointer、version/time 缺失、digest mismatch、canonical JSON 失败均阻断，不得用 PI-300 内联 fixture、generic payload、metadata 或目标值补足，见 [`snapshot falsifier 规则`](production-implementation-pi-210-normalized-evidence-model.md:360)。 | PASS |
| 21 | FrozenCardFieldRef 形状与 PI-230 兼容 | 当前 [`FrozenCardFieldRef`](production-implementation-pi-210-normalized-evidence-model.md:415) 仍为 card、contract、version、path、state、value、locator 七字段；[`PI-230`](production-implementation-pi-230-traceability-binding.md:90) 仍直接复用上游规范类型，其定位/证明/解释分责与 amendment 一致。未见形状扩张或 PI-230 语义替换；但 H-01 说明现有 locator 形状不足以承载新增联合验证要求。 | PASS WITH BLOCKING DEPENDENCY |
| 22 | F09 文本与业务语义 | amendment 明确 selector 只定位整体原文，不把资源、对象、配置轴、风险轴、归属、时态拆为六字段，见 [`非拆分规则`](production-implementation-pi-210-normalized-evidence-model.md:315)。与 [`F09 冻结文本`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:268) 逐字一致，未新增门、竞争、动作、输出或 evaluator 语义。 | PASS |

**矩阵统计：22 项；15 项 PASS，1 项 PASS WITH BLOCKING DEPENDENCY，6 项 BLOCKED。**

## 3. 指定 falsifier 核验

| Falsifier | 规范结果 | 独立核验 |
|---|---|---|
| 旧 JSON-like whole path | [`UNSUPPORTED_DIALECT`](production-implementation-pi-210-normalized-evidence-model.md:307) | 满足 |
| 未注册版本，例如 v2 | [`UNSUPPORTED_DIALECT`](production-implementation-pi-210-normalized-evidence-model.md:307) | 满足 |
| heading/card/label 0 命中 | 带非空 issue 的 [`UNRESOLVABLE`](production-implementation-pi-210-normalized-evidence-model.md:332) | 满足 |
| heading/card/label 多命中 | ambiguity issue + [`UNRESOLVABLE`](production-implementation-pi-210-normalized-evidence-model.md:332) | 满足，但 card token 边界本身受 M-01 阻断 |
| label 改名但值相同 | 旧 path 0 命中；禁止 fallback，见 [`identity change`](production-implementation-pi-210-normalized-evidence-model.md:333) | 满足 |
| Markdown 无法由 v1 唯一 parse | fail closed，见 [`ambiguous Markdown`](production-implementation-pi-210-normalized-evidence-model.md:334) | 满足，但受支持输入的 profile 边界仍有 M-01 |
| source bytes 与 digest 不同 | issue + [`UNRESOLVABLE`](production-implementation-pi-210-normalized-evidence-model.md:337) | 满足 |
| declared value 与原文不同 | issue + [`UNRESOLVABLE`](production-implementation-pi-210-normalized-evidence-model.md:337) | 失败路径已规定；多行规范值本身受 M-02 阻断 |
| snapshot 文件不存在 | fail closed，见 [`snapshot missing`](production-implementation-pi-210-normalized-evidence-model.md:360) | 满足 |
| object ID 不存在或不唯一 | fail closed，见 [`object missing/duplicate`](production-implementation-pi-210-normalized-evidence-model.md:360) | 满足 |
| JSON Pointer 不存在或不支持 | fail closed，见 [`pointer missing/unsupported`](production-implementation-pi-210-normalized-evidence-model.md:360) | 满足 |
| snapshot canonical digest 不匹配 | fail closed，见 [`digest mismatch`](production-implementation-pi-210-normalized-evidence-model.md:360) | 失败路径已规定；digest 表示受 M-03 阻断 |
| locator 与 snapshot 五元 identity 不同 | 规范要求全部一致，见 [`joint identity`](production-implementation-pi-210-normalized-evidence-model.md:358) | H-01：locator 不能独立表达五元 identity，无法构造完整机械正例或逐项 mismatch falsifier |

## 4. Findings 与精确统计

### H-01：SourceLocator 不能表达 amendment 要求的联合版本与 snapshot identity

- 级别：**High**。
- 类型：**关键歧义 + 关键证据缺失**。
- 证据：[`SourceLocator`](production-implementation-pi-210-normalized-evidence-model.md:263) 仅含 path、object ID、field path、单一 schema version、digest 与 capture time；Markdown resolver 却要求 contract/schema version 与 ref contract version 联合一致，见 [`resolver version binding`](production-implementation-pi-210-normalized-evidence-model.md:327)。JSON snapshot 又要求 locator 匹配 snapshot ID、snapshot schema version、contract version、digest、captured time 五元 identity，见 [`snapshot joint identity`](production-implementation-pi-210-normalized-evidence-model.md:358)。
- 缺口：locator 没有 snapshot ID、snapshot schema version、contract version 的独立字段，也没有定义单一 schema version 如何无损映射这些身份。读取 source 文件内部同名字段只能证明文件自述，不能证明 locator 声称绑定哪个 identity；由 resolver 隐式选择则违反“不替整改方补隐含映射”的验收纪律。
- 影响：Markdown ref 的 contract binding 与 external JSON snapshot 的联合 identity 都不能形成无歧义机械正例；对应 mismatch falsifier 也无法逐项执行。path/object/pointer 命中不能弥补该断点。
- 解除条件：由与本验收分离的整改明确唯一 locator/binding 形状或规范映射，使 locator 能逐项绑定并验证所要求的版本与 snapshot identity；不得仅在 prose 中说“联合一致”。

### M-01：heading/card 的词法身份与 parser profile 未封闭

- 级别：**Medium**。
- 类型：**关键歧义**。
- 证据：[`heading identity`](production-implementation-pi-210-normalized-evidence-model.md:303) 说取去掉行首 marker 后的完整原文 heading text，而 [`resolver parse`](production-implementation-pi-210-normalized-evidence-model.md:323) 要使用未版本化的 CommonMark-compatible parser；[`card identity`](production-implementation-pi-210-normalized-evidence-model.md:304) 依赖未定义的“独立 token”。
- 缺口：未规定 ATX optional closing sequence 与边界空白属于原文 identity 还是 parser content，也未规定 F01–F12 token 的左右边界。不同兼容 parser 或实现可对同一 heading 得到不同 H 或 card-token 数。
- 影响：一般 heading 的 canonical selector、missing/duplicate card 判定与 rename falsifier不唯一。当前 F09 简单 heading 可人工看出目标，不足以证明通用 dialect 无歧义。
- 解除条件：注册唯一 parser/version/profile，并给出 heading source extraction 与 card-token 边界的规范算法及正反例。

### M-02：多行 declared value 的规范 COPY 不是单值函数

- 级别：**Medium**。
- 类型：**关键歧义**。
- 证据：[`resolver COPY`](production-implementation-pi-210-normalized-evidence-model.md:326) 要折叠非 hard-break 换行、保留其他内容并去除两端 Markdown whitespace。
- 缺口：未定义 hard-break 在输出 opaque string 中表示为换行、空格、反斜杠标记、两空格标记还是其他规范值；也未定义“Markdown whitespace”的精确码点集合和 continuation line 归属的唯一 source-span 规则。
- 影响：同一多行列表项可能产生不同 declared value，导致 [`declared_value`](production-implementation-pi-210-normalized-evidence-model.md:421) equality 与 digest-independent COPY 结果不可互操作。当前 F09 单行正例不关闭通用 resolver 缺口。
- 解除条件：把 COPY 定义为对 parser source spans 的完整单值算法，明确 hard/soft break、whitespace 码点和 continuation boundaries，并给出 canonical JSON string 反例。

### M-03：snapshot content digest 的规范形状存在冲突

- 级别：**Medium**。
- 类型：**关键歧义**。
- 证据：snapshot schema 将 [`content_digest`](production-implementation-pi-210-normalized-evidence-model.md:348) 声明为结构化 [`DigestRef`](production-implementation-pi-210-normalized-evidence-model.md:106)；紧邻规则又要求至少使用 sha256 前缀加小写 hex 的单字符串表示，见 [`snapshot digest rule`](production-implementation-pi-210-normalized-evidence-model.md:355)。
- 缺口：没有规定字符串是 DigestRef 的 value、整个 DigestRef 的 wire encoding，还是另一种 union branch；也没有唯一转换规则。
- 影响：两个实现可对同一 JCS bytes 生成不同但各自声称合规的 digest field，联合 identity、self-digest exclusion 与 mismatch falsifier无法互操作。
- 解除条件：选择唯一 wire shape，并明确 algorithm、canonicalization、hex value 和 self-digest exclusion 对该 shape 的处理。

### 精确统计

- High findings：**1**。
- Medium findings：**3**。
- Low findings：**0**。
- Informational findings：**0**。
- Critical ambiguities：**4**（H-01、M-01、M-02、M-03）。
- Critical evidence gaps：**1 类**（H-01 所述 locator 无法承载并证明联合 identity）。
- New regressions：**0**；本次阻断均位于 amendment 新增 locator/snapshot 规范本身。
- FrozenCardFieldRef shape regressions：**0 detected within the stated file-and-line evidence boundary**。
- PI-230 semantic regressions：**0 detected within the stated file-and-line evidence boundary**。
- F09 text/business-semantic regressions：**0**。

## 5. Tests 与 YAML 执行声明

- Tests executed：**0**。
- YAML executed：**0**。
- Resolver implementations executed：**0**。
- Production commands executed：**0**。
- Reviewed artifacts modified：**0**。
- New review records written：**1**，即 [`本独立验收记录`](production-implementation-pi-285-r1-pi210-locator-amendment-acceptance.md:1)。

本裁决是文档契约的静态机械验收，不是 runtime proof；未把 [`PI-215-R1` 的 0 tests 声明](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:162) 当作通过证据。

## 6. 唯一裁决

# BLOCKED

[`PI-215-R1`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:1) 已实质改善旧 JSON-like Markdown path、F09 原文整体定位、NFC/percent canonicalization、0/多命中、alias 禁令、external file/object/pointer 与 fail-closed 失败目录，也未改变冻结 F09 业务语义。然而，amendment 仍存在 **1 项 High、3 项 Medium、4 项关键歧义及 1 类关键证据缺失**：现有 locator 不能表达其自己要求的 contract/snapshot 联合身份，heading/card identity 未完全词法化，多行 COPY 不是唯一函数，snapshot digest wire shape 不唯一。

依照“任一 High/Medium、关键歧义、关键证据缺失即 BLOCKED”和“证据不足即 BLOCKED”的规则，本 amendment 不通过独立验收。该裁决不否定已经满足的条目，也不授权本实例整改受验文件。

## 7. 唯一下一动作

**由与本验收实例分离的整改任务处理 H-01、M-01、M-02、M-03；整改后创建新的独立 amendment 复验。**

在新独立复验给出 PASS 前，不得把本 amendment 解释为 G2 amendment PASS，不得据此关闭 [`G4-H-01`](production-implementation-pi-400-r3-g4-technical-rereview.md:33) 或 [`G4-M-01`](production-implementation-pi-400-r3-g4-technical-rereview.md:34)，不得进入 PI-470-R3、G5、实现或生产接线。