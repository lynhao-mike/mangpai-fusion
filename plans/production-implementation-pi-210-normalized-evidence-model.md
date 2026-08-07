# PI-210 · F01–F12 规范化证据模型

> task_id：PI-210  
> parent_task_id：PI-200  
> 阶段：G2 运行时契约设计  
> 状态：设计产物，不代表 G2 已通过  
> 目标：定义 PI-220 判定接口与 PI-230 追溯绑定共同消费的中立证据结构。  
> 非目标：本文件不实现生产代码，不改变默认行为，不执行证据卡 YAML，不设计具体门算法、优先级、业务规则、卡片判词、G3 或 G5。

---

## 1. 设计结论

PI-210 采用“**规范化证据包 + 三轨账本 + 显式关系图 + 只读冻结卡引用 + 转换追溯**”模型。

核心判断：当前仓库的 production-default、parallel-domain、staged L6 与 v5/v6 preprod 具有不同的 input、finding、claim、decision、statement 与 feedback 语义，不能通过改名或序列化假称已统一。本模型因此是一个**新增的中立交换契约设计**，不是现有任一模型的替代品，也不授予任何适配器判定权。

共同输入被拆成五类对象：

1. `NormalizedEvidencePackage`：单 case、单次规范化快照的顶层包；
2. `EvidenceRecord`：不可混轨的最小证据记录；
3. `EvidenceRelation`：支持、反证、竞争、来源、根源、时序等显式关系；
4. `FunctionCandidate`：F01–F12 候选的证据集合与冻结卡引用，不含胜负或动作；
5. `TransformationRecord`：现有对象到规范化对象的转换账本，供 PI-230 追溯。

PI-220 只能读取这些结构后另行判定；PI-230 只能基于稳定 ID、来源定位器、关系边和转换记录建立审计绑定。二者均不得从自由文本、Markdown 或 YAML 条件反推缺失语义。

---

## 2. 事实源与适用边界

### 2.1 语义优先级

| 层级 | 事实源 | PI-210 用途 |
|---|---|---|
| 1 | `engine/contracts/12-real-world-function-evidence-cards-v1.md` | F01–F12 冻结语义、共同纪律、根源与时序约束的正式事实源 |
| 2 | `mapping/real-world-function-evidence-cards-v1.yaml` | 枚举、字段、卡数据、竞争关系和来源索引的声明性镜像；只允许字段定位与值抄录 |
| 3 | `engine/contracts/01-input-schema.md`、`03-findings-schema.md`、`04-gate-protocol.md`、`07-pipeline-flow.md` | 现有输入、findings、应期和报告链适配边界 |
| 4 | 当前 Python 模型与运行时产物 | 证明现状字段和可追溯能力，不覆盖冻结卡语义 |
| 5 | G1 三份审计 | 证明多轨运行现状、缺口和不得假称统一的边界 |

若机器附录与正式契约发生语义冲突，必须停止该字段的自动规范化并登记问题；不得由适配器自行裁决。

### 2.2 YAML 非执行边界

`mapping/real-world-function-evidence-cards-v1.yaml` 在本模型中只能产生：

- `FrozenCardFieldRef`：稳定字段路径及声明值状态；
- `SourceLocator`：以 `path`、`object_id`、`field_path` 定位来源，并携带必填 `SourceBinding`；snapshot version、content digest 与 captured time 仅由该 binding 的判别分支承载。mapping 不得伪造或补齐 binding；无法提供完整版本身份时只能 fail closed，或在适用的非冻结来源上显式使用 `UNVERSIONED_SOURCE`，且不得据此声称 validated frozen COPY；
- `UnresolvedFieldState`：原样保存卡片的 `null` 与 `unresolved_fields`；
- 声明枚举的值域校验结果。

禁止产生：

- if/else、评分、权重、排序或优先级；
- `necessary_reality_gates` 的自动通过／失败结果；
- `priority_rule`、`conflict_priority` 或文字判词的执行结果；
- 从共同规则或相邻卡推导出的缺省卡字段；
- PI-220 的动作、胜方或输出结论。

---

## 3. 三轨账本

### 3.1 轨道枚举

```text
EvidenceTrack =
  | CHART_STRUCTURE
  | REALITY_FACT
  | UNVERIFIED_HYPOTHESIS
```

| 轨道 | 允许内容 | 禁止内容 |
|---|---|---|
| `CHART_STRUCTURE` | 命盘原始结构、命理特征、流派 finding、原局链、对象／承载／作用方向、根源候选、岁运完成线索 | 把结构推断写成现实已发生事实；把多派同向写成现实验证 |
| `REALITY_FACT` | 命主自报并标明状态的现实事实、已核验事件、职业／学历等状态、观察记录、反馈事实 | 未核验预测、问题、候选事件；由命理结构自动生成的现实事实 |
| `UNVERIFIED_HYPOTHESIS` | 用户提问、待核验陈述、功能候选、事件候选、竞争解释、预测窗口、待确认现实信息 | 被静默升级为 `REALITY_FACT`；被当成冻结卡字段值 |

### 3.2 轨道转换

- 证据记录创建后 `track` 不可原地修改。
- 假设经独立验证后，必须新建 `REALITY_FACT` 记录，并用 `VERIFIES` 关系指向原假设；原假设仍保留。
- 命理结构即使高置信，也不得转换为现实事实。
- 现实事实可以作为结构结论的支持或反证，但不得反向升级根源级别。
- 任何轨道转换均须产生 `TransformationRecord`，并记录验证主体、时点和原始来源。

---

## 4. 字段级 Schema

以下为规范性伪类型。`required` 表示字段键必须存在；允许 `null` 时明确标注。没有写明默认值的字段不得由实现自行补值。

### 4.0 基础引用类型

```text
Timestamp = ISO-8601 string

RunTrack =
  | PRODUCTION_DEFAULT
  | PARALLEL_DOMAIN
  | STAGED_L6
  | V5_V6_PREPROD
  | MANUAL_IMPORT

DigestRef {
  algorithm: registered lowercase ASCII algorithm token required
  canonicalization: registered case-sensitive profile string required
  value: algorithm-specific lowercase ASCII digest required
}

ObjectRef {
  object_type: PACKAGE | EVIDENCE | RELATION | CANDIDATE | SOURCE_OBJECT |
               FINDING | CLAIM | DECISION | STATEMENT | FEEDBACK | CARD_FIELD required
  object_id: string required
  external: boolean required
  source_locator_id: string | null required
}

RelationScope {
  function_id: F01..F12 | null required
  dimension: primary_responsibility | primary_action | direct_object |
             primary_deliverable | primary_uncertainty | stable_input |
             strongest_competing_explanation | null required
}
```

- `external=false` 时 `object_id` 必须解析到当前包内对象，`source_locator_id` 可为 `null`。
- `external=true` 时必须提供 `source_locator_id`，不得只靠自由文本对象名追溯。
- `ObjectRef` 只建立身份引用，不赋予被引用对象任何事实或判定语义。

### 4.1 顶层证据包

```text
NormalizedEvidencePackage {
  schema_version: string required
  package_id: string required
  case_id: string required
  run_context: RunContext required
  contract_binding: ContractBinding required
  evidence_records: list<EvidenceRecord> required
  relations: list<EvidenceRelation> required
  function_candidates: list<FunctionCandidate> required
  transformations: list<TransformationRecord> required
  unresolved_issues: list<NormalizationIssue> required
  integrity: IntegrityState required
  created_at: Timestamp required
}
```

| 字段 | 语义与约束 |
|---|---|
| `schema_version` | 规范化契约自身版本；不得冒充 findings、pipeline 或卡契约版本 |
| `package_id` | 单次规范化快照的稳定唯一 ID；同内容重建的稳定性策略留给实现计划，不在此定义算法 |
| `case_id` | 与来源 case 精确绑定 |
| `run_context` | 明确来源运行轨道和可选 run ID，不把多轨对象合并为同一 run |
| `contract_binding` | 绑定冻结卡契约和声明性附录版本 |
| `evidence_records` | 三轨记录共表；每条记录只能属于一个轨道 |
| `relations` | 只表达关系，不计算关系的判定效果 |
| `function_candidates` | F01–F12 候选输入视图，不含决定结果 |
| `transformations` | 原对象到规范化对象的可审计转换 |
| `unresolved_issues` | 无损转换失败、语义歧义、引用断裂等问题，不允许吞掉 |
| `integrity` | 包级可消费性与断链状态；不是业务判定 |

### 4.2 运行上下文与契约绑定

```text
RunContext {
  source_track: RunTrack required
  source_run_id: string | null required
  source_schema_versions: map<string, string | null> required
  observed_as_of: TemporalPoint | null required
}

ContractBinding {
  semantic_contract_id: real-world-function-evidence-cards-v1 required
  semantic_contract_path: string required
  declarative_appendix_path: string required
  declarative_appendix_schema_version: string | null required
  content_digest: string | null required
  binding_status: VERIFIED | UNVERIFIED | MISMATCH required
}
```

约束：`source_run_id = null` 表示来源轨道没有或未提供 run ID，不得生成伪 run ID。`binding_status = MISMATCH` 时，卡字段相关记录不得进入 PI-220 可消费视图。

### 4.3 最小证据记录

```text
EvidenceRecord {
  evidence_id: string required
  case_id: string required
  track: EvidenceTrack required
  kind: EvidenceKind required
  subject: EvidenceSubject required
  payload: TypedPayload required
  assertion_mode: OBSERVED | REPORTED | DERIVED | DECLARED | PROPOSED required
  polarity: SUPPORTING | COUNTER | NEUTRAL | MIXED required
  verification: VerificationState required
  temporal_scope: TemporalScope required
  sources: nonempty list<SourceLocator> required
  card_field_refs: list<FrozenCardFieldRef> required
  confidence_ref: ConfidenceReference | null required
  source_object_refs: list<ObjectRef> required
  unresolved_fields: list<string> required
  extensions: map<string, opaque-json> required
}
```

#### `EvidenceKind`

```text
EvidenceKind =
  | CHART_FACT
  | STRUCTURAL_FINDING
  | REALITY_STATE
  | REALITY_EVENT
  | USER_QUESTION
  | FUNCTION_HYPOTHESIS
  | EVENT_HYPOTHESIS
  | COMPETING_EXPLANATION
  | COUNTEREVIDENCE
  | ROOT_SIGNAL
  | TIMING_SIGNAL
  | VALIDATION_OBSERVATION
  | SOURCE_DECLARATION
```

`kind` 只描述证据形态，不代表业务结论、门结果或动作。`REALITY_STATE` 与 `REALITY_EVENT` 必须分开；`ROOT_SIGNAL` 与 `TIMING_SIGNAL` 必须分开。

#### `EvidenceSubject`

```text
EvidenceSubject {
  subject_type: CASE | PERSON | FUNCTION | EVENT | STATE | CLAIM | FINDING | STATEMENT | CARD_FIELD required
  subject_id: string required
  function_id: F01..F12 | null required
  domain: string | null required
}
```

`function_id = null` 表示该证据尚未或不能绑定到 F01–F12，不得以 domain 猜测功能 ID。

#### `TypedPayload`

```text
TypedPayload {
  value_type: STRING | NUMBER | BOOLEAN | ENUM | OBJECT | LIST | NULL required
  value: json-scalar-or-structure | null required
  value_schema: string | null required
  raw_value: opaque-json | null required
  language: string | null required
}
```

- `value_type = NULL` 时 `value` 必须为 `null`。
- `raw_value` 用于保留来源原貌；规范化值与原值不同必须记录转换。
- 自由文本只作来源内容，不得从中自动补结构化业务字段，除非适配器明确声明为有损／需人工确认。

### 4.4 来源与验证状态

```text
SourceLocator {
  source_id: string required
  source_type: INPUT_FIELD | FINDING_OBJECT | CLAIM_OBJECT | DECISION_OBJECT |
               STATEMENT_OBJECT | FEEDBACK_OBJECT | FROZEN_CONTRACT_FIELD |
               DECLARATIVE_APPENDIX_FIELD | THEORY_RULE | HUMAN_ATTESTATION |
               TRANSFORMATION_OUTPUT required
  path: string required
  object_id: string | null required
  field_path: string | null required
  binding: SourceBinding required
}

SourceBinding =
  | MarkdownContractSourceBinding {
      binding_kind: MARKDOWN_CONTRACT required
      binding_schema_version: source-binding.markdown.v1 required
      source_snapshot_id: string required
      source_schema_version: markdown-source.commonmark-0.31.2-mdff-v1 required
      contract_version: string required
      content_digest: DigestRef required
      captured_at: RFC3339 timestamp required
    }
  | ImmutableJsonSourceBinding {
      binding_kind: IMMUTABLE_JSON_SNAPSHOT required
      binding_schema_version: source-binding.immutable-json.v1 required
      source_snapshot_id: string required
      source_schema_version: string required
      contract_version: string required
      content_digest: DigestRef required
      captured_at: RFC3339 timestamp required
    }
  | UnversionedSourceBinding {
      binding_kind: UNVERSIONED_SOURCE required
      binding_schema_version: source-binding.unversioned.v1 required
      reason_code: SOURCE_IDENTITY_NOT_VERSIONED required
    }

MarkdownFrozenFieldPath {
  dialect: mdff required
  dialect_version: v1 required
  heading_identity: string required
  card_identity: string required
  original_label: string required
}

VerificationState {
  status: UNVERIFIED | SELF_REPORTED | SOURCE_VALIDATED | HUMAN_VERIFIED |
          SYSTEM_OBSERVED | CONTRADICTED | NOT_APPLICABLE required
  verified_at: Timestamp | null required
  verifier: ObjectRef | null required
  method: string | null required
  contradiction_refs: list<string> required
}
```

`SourceBinding` 是封闭判别联合，也是 source snapshot/version/digest/time 的唯一事实源。`MARKDOWN_CONTRACT` 与 `IMMUTABLE_JSON_SNAPSHOT` 六个非判别身份字段全部必填且不可为 `null`；两分支互斥，字段不得跨分支解释。`UNVERSIONED_SOURCE` 只允许既有非冻结、非 snapshot 来源显式声明“无版本身份”，不得用于 `FROZEN_CONTRACT_FIELD`、不可变 JSON snapshot、`FrozenCardFieldRef` 或任何声称 `SOURCE_VALIDATED` 的字段级 COPY。

旧 `SourceLocator.schema_version`、`SourceLocator.content_digest`、`SourceLocator.captured_at` 自本 amendment 起删除，不保留 shadow/deprecated 双写。迁移必须原子构造恰一个 `binding` 分支：旧值足以形成完整 Markdown 或 JSON 联合身份时逐字段搬入；任一必填身份缺失、旧 `content_digest` 不是可验证的结构化 `DigestRef`、或无法判定分支时，产生非空 `SOURCE_BINDING_MIGRATION_REQUIRED` issue 并 fail closed。禁止同时接受旧顶层字段与新 `binding`，禁止从文件内容、mtime、路径名或 resolver 默认值补齐 locator 声称的 identity。

#### 4.4.1 `mdff:v1` Markdown frozen-field path dialect 与词法 profile

当 `source_type = FROZEN_CONTRACT_FIELD` 且 `path` 指向 Markdown 时，`field_path` 必须使用下列唯一正式语法，`binding.binding_kind` 必须为 `MARKDOWN_CONTRACT`；其他 source type 和 JSON source snapshot 不使用本 dialect：

```text
mdff:v1/heading/<H>/card/<C>/item/<L>
```

`mdff:v1` 唯一注册 parser profile 为 `markdown-source.commonmark-0.31.2-mdff-v1`：块结构以 CommonMark 0.31.2 为规范且只支持 0–3 个 ASCII space 缩进的 ATX heading、`-`／`+`／`*` 无序列表 marker、列表项首个 leaf paragraph 及其 continuation lines；setext heading、HTML、表格、definition list、ordered list、block quote、code block、跨 blank line 的后续 paragraph 和嵌套列表均不在 selector/COPY 子集内。实现库名称或“CommonMark-compatible”声明不能替代该 profile；规范输入若不能产生唯一的上述结构与 source spans，必须 fail closed。

- `<H>` 是卡片所在 ATX heading 的稳定 source identity。对 heading 单行 UTF-8 source bytes：先移除 0–3 个 opening ASCII space、1–6 个 opening `#`，并要求其后为行尾或至少一个 U+0020／U+0009；若非行尾，移除该 opening sequence 后紧邻的全部 U+0020／U+0009。然后仅当剩余 bytes 以“至少一个 U+0020／U+0009 + 一个或多个 `#` + 零个或多个 U+0020／U+0009 + 行尾”结束时，移除该分隔空白、closing `#` sequence 与尾部空白。最后移除所得内容两端全部 U+0020／U+0009；余下 UTF-8 source text 即 `<H>`。opening/closing marker 与被上述步骤消费的空白不属于 `<H>`；其他 inline source 原样保留，不做 inline parse、render 或 entity decode。
- `<C>` 是 `<H>` source text 中按 UTF-8 bytes 扫描得到的唯一 ASCII card token。候选 byte pattern 仅为 `F0[1-9]` 或 `F1[0-2]`；其左、右相邻 byte（若存在）都不得属于 ASCII `[A-Za-z0-9_]`。扫描按候选起始 byte 从左到右计数，不重叠；恰一候选才合法，解码后的 `<C>` 必须与它逐码点相等。`F09`、`[F09]`、`F09：` 各计一个；`XF09`、`F09A`、`F09_`、`F00`、`F13` 均计零；`F09/F10` 计两个并导致 ambiguous card。不得从正文、文件名、主题或 mapping 猜测 card identity。
- `<L>` 是目标直接无序列表项首个 leaf paragraph 中，第一个不属于 CommonMark 0.31.2 code span source range 的 ASCII 冒号 `:` 或全角冒号 `：` 之前的完整 inline source bytes；去除两端全部 U+0020／U+0009 后得到。冒号必须存在。label 不做 render/entity decode，是规范选择器而非 JSON-like field name；不得翻译、snake_case、slugify、同义改写或使用 alias。
- `<H>`、`<C>`、`<L>` 都先按 Unicode NFC 规范化，再对 UTF-8 octet 使用 RFC 3986 percent-encoding；仅 `ALPHA / DIGIT / - . _ ~` 可不转义，十六进制必须大写。`/`、`%`、空格、`#`、`:`、`：` 及所有非 ASCII octet 必须转义。解码失败、非最短 UTF-8、非法 Unicode、非 NFC 输入、小写 percent hex、转义 unreserved 字符或 parse 后重新编码不逐字节等于输入，均为 non-canonical 并 fail closed。
- dialect 名和版本大小写敏感。只有 `mdff:v1` 受支持；`/cards/F09/reality_hard_gate_and_dual_cards`、JSON Pointer 外观、heading slug、数组位置和任意未注册版本均为 `UNSUPPORTED_DIALECT`，不得兼容猜测。

F09 正式示例只证明通用机制可表达当前原文，不改变其业务语义：

```text
mdff:v1/heading/4.9%20F09%20%E8%B5%84%E6%9C%AC%E9%85%8D%E7%BD%AE%E4%B8%8E%E9%A3%8E%E9%99%A9%E6%89%BF%E6%8B%85/card/F09/item/%E7%8E%B0%E5%AE%9E%E7%A1%AC%E9%97%A8%E4%B8%8E%E5%8F%8C%E5%8D%A1
```

该路径选择冻结 Markdown 中“现实硬门与双卡”列表项冒号后的整段原文值；它不把其中资源、对象、配置轴、风险轴、归属、时态拆成六个字段，也不建立 F09 专用解析规则。

#### 4.4.2 Markdown resolver 的确定性步骤

resolver 必须按以下顺序工作，任一步失败即停止，不得 fallback：

1. 校验 `field_path` 的 dialect/version、段数、固定 segment 名、percent-encoding 与 canonical round trip。
2. 读取 `SourceLocator.path` 指向的确切 repository-relative Markdown 文件；`path` 只负责选择 source artifact，不承载对象或字段语义。
3. 严格按 `markdown-source.commonmark-0.31.2-mdff-v1` 识别受支持块与 source spans；不得用 HTML、全文正则、模糊搜索或另一 parser/profile 的 AST 代替。
4. 按 4.4.1 的 source-byte 算法提取 `<H>`，NFC 后逐码点相等匹配且必须恰一命中；再扫描 card token，要求恰一且等于 `<C>`。该 heading 界定的 card object 从此 heading 后开始，到下一个同级或更高层 ATX heading 前结束。
5. 在该 card object 的直接无序列表子项中，仅检查每项首个 leaf paragraph，按 4.4.1 提取 `<L>` 并要求恰一命中；嵌套列表、后续 paragraph 或其他 block 不属于字段值。
6. 对命中 leaf paragraph 执行下述唯一 `MDFF_V1_COPY`，输出 `opaque-json` STRING；空结果是存在的空字符串，不得改成 `null`。
7. 将整个 Markdown artifact 的 UTF-8 bytes 规范为无 BOM、LF 行尾且除此不改内容，以 `DigestRef {algorithm: "sha256", canonicalization: "RAW-UTF8-NO-BOM-LF", value: 64 lowercase hex}` 校验 `binding.content_digest`；同时要求 `binding_schema_version`、`source_snapshot_id`、`source_schema_version`、`contract_version`、`content_digest`、`captured_at` 全部存在且与所读 snapshot 逐字段一致。`captured_at` 必须为带时区 RFC 3339 timestamp，不参与 path 匹配，不得由 mtime 推导。
8. 对 `FrozenCardFieldRef`，要求 `card_id = <C>`、`field_path` 逐字节等于 canonical path、`contract_version = binding.contract_version`，且 `declared_value` 与第 6 步结果按 JSON string value 逐码点相等。只有全部成立才是规范 `COPY`。

`MDFF_V1_COPY` 是以下单值 source-span bytes 函数：

1. 输入只含命中 direct list item 的首个 leaf paragraph。首行起点是首个非 code-span label delimiter 结束后的 byte；continuation membership 只包括同一 leaf paragraph source span 中、无 blank line 分隔的后续 physical line。任何后续 block、child block、nested list 或第二 paragraph 均排除。
2. 列表 marker 只接受 `-`、`+`、`*` 后跟一至四个 indentation columns；tab 仅为判断 columns 按下一个 4-column tab stop 展开。每条 continuation line 必须由 profile 唯一判为该 leaf paragraph成员；从 source 中移除 parser 归属该 paragraph 之前的全部容器前缀 bytes，保留 content start 起的原始 UTF-8 bytes。无法唯一确定 membership 或 content start 即 `UNRESOLVABLE`。
3. 行尾只接受 LF，输入预规范化阶段把 CRLF 逐个改为 LF并拒绝裸 CR；BOM 被拒绝。对每个非末行，在 indentation stripping 后检查行内容：若最后一个 byte 是反斜杠 `\\`，或末尾连续 U+0020 数量至少为二，则该换行是 hard break；否则是 soft break。code span 内的反斜杠或空格也按 source line 末尾位置判定，不做 inline 语义改写。
4. soft break 只把 LF 替换为一个 U+0020；hard break 只把 LF 替换为一个 U+000A。hard-break marker bytes（末尾反斜杠或 U+0020）属于 inline source并原样保留，因此不发生 render。所有其他 inline bytes，包括 backtick、entity source、反斜杠转义、标点、大小写及内部 U+0020／U+0009，逐 byte 保留；不做 entity decode、render、NFC、语义拆分、alias 或业务归一化。
5. 拼接完成后，仅从整个结果开头和结尾移除 U+0020 与 U+0009；没有其他码点属于 v1 trim 集。特别是 U+000A、U+00A0、U+3000 不 trim。剩余合法 UTF-8 bytes 解码为 Unicode string；非法 UTF-8 fail closed。

正例：`- 标签：甲\n  乙` COPY 为 JSON string value `甲 乙`；`- 标签：甲  \n  乙` COPY 为含两个 U+0020 后接 U+000A 的 `甲  \n乙`；`- 标签：甲\\\n  乙` COPY 为反斜杠后接 U+000A 的 `甲\\\n乙`。反例：blank line 后第二 paragraph、四空格 code block、nested list 不属于 COPY；U+00A0 包围值时不得 trim；同一 continuation 可被两个 block 解释时必须阻断而非择一。

#### 4.4.3 唯一命中、漂移与失败状态

- heading、card 或 label 选择器均要求恰一命中；0 命中分别是 missing heading/card/label，多命中分别是 duplicate/ambiguous heading/card/label，全部 `UNRESOLVABLE`。
- label rename 即 identity change：旧 path 必须 0 命中并 fail closed；不得以内容相同、编辑距离、翻译、slug、alias 或邻近位置恢复。新 label 必须产生新 canonical path，并由上游显式迁移引用。
- heading rename、card token 漂移、列表项变为不受支持结构、同名列表项重复或 Markdown parse 歧义均 fail closed。resolver 不裁定业务语义，也不从值反推 label。
- `SourceLocator.path` 选择文件；`object_id` 声明该 source snapshot 内的稳定对象身份并必须等于解码后的 card identity（Markdown v1 即 `<C>`）；`field_path` 在对象内选择声明字段。三者缺一不可、不得互相拼接替代。
- `SourceLocator.binding` 唯一证明并解释 snapshot；其中 digest 证明内容，source/contract/binding version 解释内容，snapshot ID 声明不可变身份，`captured_at` 标记采集。它们不能替代 path/object/field，path 命中也不能替代 binding 联合验证。
- unsupported dialect、profile/version mismatch、ATX closing 或 token 边界不合规、missing/duplicate card、missing/duplicate label、label rename、continuation span 歧义、content/digest mismatch、contract version mismatch、non-canonical path、旧顶层 binding 字段或 `declared_value` mismatch 均产生非空 `NormalizationIssue`，相关 binding 为 `UNRESOLVABLE`，且不得进入 PI-220 可消费视图。

#### 4.4.4 `plans/` immutable JSON source snapshot fixture 最小契约

后续获授权整改可在 `plans/` 下创建实际 fixture，但本 PI-210 amendment 不创建任何 PI-300 具体 snapshot。机械终止条件如下；envelope 与被摘要 payload 固定分离：

```text
ImmutableJsonSourceSnapshot {
  source_snapshot_id: string required
  snapshot_schema_version: string required
  contract_version: string required
  content_digest: DigestRef required
  captured_at: RFC3339 timestamp required
  payload: ImmutableJsonSourcePayload required
}

ImmutableJsonSourcePayload {
  objects: nonempty object-map keyed by object_id required
}
```

1. `SourceLocator.path` 必须指向仓库中实际存在的 `.json` 文件，且 `binding.binding_kind = IMMUTABLE_JSON_SNAPSHOT`；prose、内联样例、未来路径或另一文件中的同形对象不能替代它。
2. 文件必须是 UTF-8、无 BOM、LF、I-JSON 可表示的 JSON envelope。唯一摘要输入是 `RFC8785-JCS-UTF8(payload)`，即只对 `payload` 值做 RFC 8785 JCS 后的 UTF-8 bytes；envelope 的 `source_snapshot_id`、`snapshot_schema_version`、`contract_version`、`content_digest`、`captured_at` 全部外置，不进入摘要 payload，禁止删除字段后再摘要、摘要整个 envelope 或其他 self-digest 变体。
3. `content_digest` 唯一 wire shape 是结构化 `DigestRef {algorithm: "sha256", canonicalization: "RFC8785-JCS-UTF8", value: <64 lowercase hex>}`。`algorithm` 必须逐码点等于小写 `sha256`，`canonicalization` 必须逐码点等于 `RFC8785-JCS-UTF8`，`value` 必须匹配 ASCII `^[0-9a-f]{64}$`；禁止 `sha256:<hex>` 字符串、uppercase hex、裸 hex 或 union branch。
4. `payload.objects` 必须按 `object_id` 建唯一键；locator 的 `object_id` 必须在 map 中恰一命中。对象不得依赖数组位置定位，重复语义对象或 duplicate JSON key 均无效。
5. JSON fixture 的 `field_path` 必须是 RFC 6901 JSON Pointer，从命中对象根开始逐字段定位；每个 `COPY` 来源字段各有一个 pointer，禁止 JSONPath、模糊键、alias 或 whole-object prose 代替逐字段 pointer。空 pointer 只可明确选择整个对象，不能冒充字段级 COPY。
6. `source_snapshot_id + snapshot_schema_version + contract_version + content_digest + captured_at` 构成联合 snapshot identity。`SourceBinding` 中 `source_snapshot_id = envelope.source_snapshot_id`、`source_schema_version = envelope.snapshot_schema_version`、`contract_version = envelope.contract_version`、`content_digest.algorithm/canonicalization/value` 与 envelope 对应三字段分别相等、`captured_at = envelope.captured_at`；必须逐字段相等，不允许字符串转换、摘要重算值替换或任一侧优先。object ID 与 pointer 另行全部一致。
7. snapshot payload、schema、contract、对象或字段任一变化必须产生新的联合 identity；payload 变化必然产生新 digest。不得在原 identity 下覆写；相同联合 identity 只能表示同一 JCS payload。
8. snapshot missing、错误 binding 分支、联合 identity 任一字段 mismatch、object missing/duplicate、pointer missing/ambiguous、unsupported pointer、version/time 缺失、digest shape/value mismatch、envelope/payload 未分离或 JCS 失败均 fail closed；不得以 PI-300 内联 fixture、generic payload、metadata 或目标侧值补足来源。

不变量：

- `track = UNVERIFIED_HYPOTHESIS` 时，`verification.status` 不得是 `HUMAN_VERIFIED` 或 `SYSTEM_OBSERVED`；验证后应新建现实事实记录。
- `verification.status` 不是置信度，不表达结论正确概率。
- `SELF_REPORTED` 不等于 `HUMAN_VERIFIED`；`SOURCE_VALIDATED` 仅说明来源或格式被验证，不等于现实命中。
- `CONTRADICTED` 必须至少有一个 `contradiction_refs`。

### 4.5 时间模型

```text
TemporalScope {
  mode: TIMELESS | POINT | INTERVAL | AS_OF | UNKNOWN required
  point: TemporalPoint | null required
  interval: TemporalInterval | null required
  as_of: TemporalPoint | null required
  source_precision: YEAR | MONTH | DAY | DATETIME | AGE | DAYUN_STEP | TEXTUAL | UNKNOWN required
  calendar: string | null required
  timezone: string | null required
  raw_expression: string | null required
}

TemporalPoint {
  value: string required
  precision: YEAR | MONTH | DAY | DATETIME | AGE | DAYUN_STEP | TEXTUAL required
}

TemporalInterval {
  start: TemporalPoint | null required
  end: TemporalPoint | null required
  start_inclusive: boolean | null required
  end_inclusive: boolean | null required
}
```

规则：

- 单年事实使用 `POINT`，不得自动扩成全年区间。
- 状态截止日使用 `AS_OF`；事件发生点使用 `POINT`；持续事件或窗口使用 `INTERVAL`。
- 开放区间允许 `start` 或 `end` 为 `null`，但边界是否包含不得猜测。
- `UNKNOWN` 不是 `TIMELESS`。
- 原始输入只有年份时不得伪造月日。
- 大运区间、查询窗口、内部预测窗口、回溯截止年和观察窗口必须保留各自来源，不得合并成一个“时间范围”。

### 4.6 冻结卡字段引用与空值保真

```text
SourceFieldState =
  | PRESENT_VALUE
  | EXPLICIT_NULL
  | LISTED_UNRESOLVED
  | BOTH_NULL_AND_UNRESOLVED
  | ABSENT

FrozenCardFieldRef {
  card_id: F01..F12 required
  contract_id: real-world-function-evidence-cards-v1 required
  contract_version: string required
  field_path: string required
  declared_state: SourceFieldState required
  declared_value: opaque-json | null required
  source_locator_id: string required
}

UnresolvedFieldState {
  card_id: F01..F12 required
  field_path: string required
  state: SourceFieldState required
  raw_declared_value: opaque-json | null required
}
```

五种来源字段状态严格分开：

1. `PRESENT_VALUE`：字段存在且有非 null 声明值；
2. `EXPLICIT_NULL`：字段存在，值明确为 `null`，且未列入 `unresolved_fields`；
3. `LISTED_UNRESOLVED`：字段路径列入 `unresolved_fields`，且声明值不为 `null`；
4. `BOTH_NULL_AND_UNRESOLVED`：字段值为 `null` 且同时列入 `unresolved_fields`；
5. `ABSENT`：当前冻结声明中没有该字段，不能解释为 `null` 或未决。

`SourceFieldState` 只记录声明来源事实，不得容纳 evaluator 的 `UNKNOWN`、`MISSING`、`CONFLICT` 或任何门结果。任何适配器均不得把这些状态改成空字符串、false、0、空列表、默认枚举、推导值或 evaluator 状态。

已知需要重点保真的冻结项包括但不限于：

- F06 的 `unified_coverage_scalar` 与 `output_precision`；
- F09、F10 的 `coverage` 与 `output_precision`；
- F12 的 `source_gate`；
- F01–F08 中声明为 `null` 的 `output_precision`。

### 4.7 `validation_timepoints` 与 `output_precision` 分账

```text
FrozenDeclarationRef {
  declaration_id: string required
  declaration_type: OUTPUT_PRECISION | VALIDATION_PLAN required
  card_id: F01..F12 required
  contract_version: string required
  declaration_schema_version: string required
  content_digest: DigestRef required
}

FrozenDeclarationBinding =
  | {
      presence: RESOLVED required
      ref: FrozenDeclarationRef required
    }
  | {
      presence: ABSENT required
      reason_code: DECLARATION_NOT_PRESENT required
    }
  | {
      presence: NOT_APPLICABLE required
      reason_code: DECLARATION_NOT_APPLICABLE required
    }
  | {
      presence: UNAVAILABLE required
      reason_code: DECLARATION_UNREAD | DECLARATION_SOURCE_UNAVAILABLE required
      issue_ids: nonempty list<string> required
    }
  | {
      presence: UNRESOLVABLE required
      attempted_ref: FrozenDeclarationRef required
      reason_code: IDENTITY_MISMATCH | CONTRACT_VERSION_MISMATCH |
                   DECLARATION_SCHEMA_VERSION_MISMATCH | DIGEST_MISMATCH |
                   BROKEN_REFERENCE required
      issue_ids: nonempty list<string> required
    }

ValidationPlanRef {
  ref: FrozenDeclarationRef required
  declared_timepoints: opaque-json required
  declared_state: SourceFieldState required
  source_field_ref: FrozenCardFieldRef required
}

OutputPrecisionRef {
  ref: FrozenDeclarationRef required
  declared_precision: opaque-json | null required
  declared_state: SourceFieldState required
  source_field_ref: FrozenCardFieldRef required
}
```

- `FrozenDeclarationRef` 是 output precision 与 validation plan 跨 PI-210／PI-220／PI-230 的唯一稳定声明引用；`declaration_id` 在对应冻结契约快照内稳定，内容变化必须产生新 `content_digest`，契约或声明 schema 变化必须显式改版，禁止裸字符串跨 artifact 引用。
- `FrozenDeclarationBinding` 是三份设计唯一的声明引用存在性契约。五个 `presence` 分支是封闭、可判别联合：`RESOLVED` 必须且只能携带 `ref`；`ABSENT` 与 `NOT_APPLICABLE` 必须携带各自固定原因且不得携带引用；`UNAVAILABLE` 表达未读取或来源当前不可用；`UNRESOLVABLE` 必须保留实际尝试解析的 `attempted_ref`。后两者必须绑定非空 issue，按 fail-closed 处理。禁止以裸 `null`、空对象、缺字段或默认枚举代替任一分支。
- 声明值状态与引用存在性永久分账。只要冻结 output precision 声明对象存在，绑定就必须为 `RESOLVED` 且 `ref` 非 null，完整保留 `declaration_id`、`declaration_type`、`card_id`、`contract_version`、`declaration_schema_version` 与 `content_digest`；其 `declared_precision=null` 仍是被该引用定位的声明值，绝不允许改写为 `ABSENT`、`NOT_APPLICABLE`、`UNAVAILABLE` 或 `UNRESOLVABLE`。若应解析该声明却无法读取或校验引用，只能进入对应失败分支并阻断消费，不得伪装成值为 null。
- validation plan 按自身冻结上游存在性独立产生绑定：有声明并成功解析时为 `RESOLVED`；确无声明时为 `ABSENT`；只有上游明确声明不适用时才可为 `NOT_APPLICABLE`；未读取／来源不可用与引用断链分别为 `UNAVAILABLE`、`UNRESOLVABLE`。不得根据 output precision 的存在性推导 validation plan，也不得把 validation plan 的 `ABSENT` 套用到 output precision。
- `declared_timepoints` 无损保存 `validation_timepoints` 的声明值；当前 YAML 为标签列表，例如 F09 的 `T0_FACT_FREEZE`、`T1_THEORY_COMPLETION`、`T2_OBSERVATION`，或 F10 的对应冻结标签。类型不把未来合法声明收窄成算法输入。
- `declared_precision` 无损保存冻结 `output_precision` 的完整 YAML 值：可为显式 `null`、T 层标量或任意声明性对象／嵌套对象。因而 F01–F10 的 null、F11 的 `{T0,T1,T2,default_max}` 映射和 F12 的嵌套 `allowed`／`requires`／`fallback` 等结构均逐值保留；不得只抽取 T0/T1/T2 键或共同默认。
- `declared_state` 记录来源字段状态，不解释声明对象中的业务含义。`declared_precision` 为对象不表示它可执行；消费者仍只能精确读取和引用。
- 两类声明具有不同 `declaration_type`、不同 `declaration_id` 和不同来源字段，始终分账；不得共享对象、互相转换或用名称相似性做映射。
- validation label 不得作为 `TemporalPoint` 的实际日期，除非另有独立证据将其绑定到具体时点。

### 4.8 关系图

```text
EvidenceRelation {
  relation_id: string required
  relation_type: RelationType required
  from_ref: ObjectRef required
  to_ref: ObjectRef required
  scope: RelationScope required
  source_refs: nonempty list<string> required
  status: ASSERTED | OBSERVED | PROPOSED | DISPUTED required
  temporal_scope: TemporalScope required
  metadata: map<string, opaque-json> required
}

RelationType =
  | SUPPORTS
  | COUNTERS
  | CONTRADICTS
  | COMPETES_WITH
  | DERIVED_FROM
  | CITES
  | VERIFIES
  | INVALIDATES
  | HAS_ROOT_SIGNAL
  | HAS_TIMING_SIGNAL
  | COMPLETES_AT
  | REFERS_TO_CARD_FIELD
  | MAPS_FROM_SOURCE_OBJECT
```

关系不携带自动效果。例如 `COUNTERS` 不自动让候选失败，`COMPETES_WITH` 不产生胜方，`COMPLETES_AT` 不自动生成事件。

### 4.9 根源与时序证据

```text
RootEvidencePayload {
  vocabulary_scope: COMMON | CARD_SPECIFIC required
  label: STRONG_ROOT | WEAK_ROOT | NO_ROOT | string required
  card_id: F01..F12 | null required
  object_refs: list<string> required
  rationale_source_refs: list<string> required
}

TimingEvidencePayload {
  completion_mode: ACTIVATE_EXISTING | COMPLETE_LATENT | REPAIR_DEFECT |
                   TEMPORARY_SUBSTITUTE | INVALID_COMPLETION required
  target_root_evidence_id: string | null required
  timing_object_refs: list<string> required
}
```

- 共同根源标签与 F09/F10 等卡片专属标签必须通过 `vocabulary_scope` 分开，不能强行折叠。
- 本模型只承载来源已经明确给出的根源／时序信号；不得自行计算根源等级或完成方式。
- `target_root_evidence_id = null` 只表示来源未建立绑定，不得自动绑定到最近记录。
- 冻结约束如 `NO_ROOT` 与某完成方式的配对限制由 PI-220 引用正式契约处理；PI-210 不实现该判断。

### 4.10 功能候选、竞争与反证

```text
FunctionCandidate {
  candidate_id: string required
  case_id: string required
  function_id: F01..F12 required
  status: PROPOSED | EVIDENCE_ATTACHED | INCOMPLETE | DISPUTED required
  card_refs: nonempty list<FrozenCardFieldRef> required
  structure_evidence_ids: list<string> required
  reality_evidence_ids: list<string> required
  hypothesis_evidence_ids: list<string> required
  counterevidence_ids: list<string> required
  root_evidence_ids: list<string> required
  timing_evidence_ids: list<string> required
  competing_candidate_ids: list<string> required
  competition_dimensions: list<CompetitionDimensionRecord> required
  unresolved_fields: list<string> required
}

CompetitionDimensionRecord {
  dimension: primary_responsibility | primary_action | direct_object |
             primary_deliverable | primary_uncertainty | stable_input |
             strongest_competing_explanation required
  evidence_ids: list<string> required
  counterevidence_ids: list<string> required
  comparison_state: UNOBSERVED | PARTIAL | READY_FOR_PI220 | DISPUTED required
}
```

禁止字段：`winner`、`score`、`priority`、`passed`、`decision_action`、`output_text`。这些均不属于 PI-210。

`comparison_state = READY_FOR_PI220` 仅表示该维度的结构引用完整，绝不表示候选已通过任何门。

### 4.11 置信度引用

```text
ConfidenceReference {
  source_model: PRODUCTION_CONFIDENCE | PARALLEL_CONFIDENCE | CLAIM_CONFIDENCE |
                STRUCTURAL_STABILITY | FEEDBACK_VALIDATION | OTHER required
  source_object_ref: ObjectRef required
  raw_snapshot: opaque-json required
  semantic_label: string required
  normalized_numeric_value: number | null required
  normalization_status: NOT_ATTEMPTED | LOSSLESS | LOSSY | UNSUPPORTED required
}
```

本模型不建立新的统一置信度算法。production 双轨置信度、parallel confidence、claim confidence、结构稳定性和反馈验证置信不得混成一个数。只有语义与尺度均被证明等价时才允许 `LOSSLESS`；否则保留原始快照并标注 `LOSSY` 或 `UNSUPPORTED`。

### 4.12 转换与问题账本

```text
TransformationRecord {
  transformation_id: string required
  adapter_id: string required
  adapter_version: string required
  source_object_refs: nonempty list<ObjectRef> required
  target_object_refs: list<ObjectRef> required
  fidelity: LOSSLESS | PARTIAL | LOSSY | UNSUPPORTED required
  field_mappings: list<FieldMapping> required
  dropped_fields: list<string> required
  dropped_object_refs: list<ObjectRef> required
  synthesized_fields: list<string> required
  issues: list<string> required
  transformed_at: Timestamp required
}

FieldMapping {
  source_field_path: string required
  target_field_path: string required
  operation: COPY | RENAME | TYPE_PRESERVING_PARSE | STRUCTURAL_WRAP |
             ENUM_EXACT_MAP | TEXT_PRESERVE | NO_MAP required
  fidelity: LOSSLESS | PARTIAL | LOSSY | UNSUPPORTED required
}

NormalizationIssue {
  issue_id: string required
  severity: INFO | WARNING | BLOCKING required
  code: string required
  object_refs: list<ObjectRef> required
  field_paths: list<string> required
  description: string required
  required_disposition: PRESERVE | EXCLUDE_FROM_PI220 | HUMAN_REVIEW required
}

IntegrityState {
  referential_integrity: VALID | INVALID required
  card_binding_integrity: VALID | INVALID | UNVERIFIED required
  track_separation_integrity: VALID | INVALID required
  pi220_consumable: boolean required
  blocking_issue_ids: list<string> required
}
```

`TransformationRecord` 是 PI-210、PI-220 与 PI-230 唯一规范转换记录契约。`target_object_refs` 允许为空只为表达 `UNSUPPORTED` 或仅发生丢弃的转换，此时必须有非空 `issues`，并在适用时列出 `dropped_object_refs`；其他转换必须至少有一个目标引用。PI-230 通过其版本化 trace node 解析这些 `ObjectRef` 对应快照，不得另建字段竞争的 trace 转换类型。

`synthesized_fields` 原则上必须为空；只允许生成容器级 ID、类型标签和转换元数据，不允许生成业务值。若产生任何业务语义字段，必须视为违规而非普通 `LOSSY` 转换。

---

## 5. 核心不变量

### 5.1 三轨与事实不变量

1. 每条 `EvidenceRecord` 恰好属于一个轨道。
2. 未核验假设不得出现在 `reality_evidence_ids`。
3. 命理结构证据不得被标记为现实观察。
4. 问题、预测和候选事件默认属于未核验假设轨，但“默认”只能由明确的来源类型映射规则声明；无法识别时阻断，不猜测。
5. 现实状态与现实事件不得合并为同一记录。
6. 新验证事实必须新增记录，不得覆盖原假设。

### 5.2 冻结语义不变量

7. 卡字段引用必须包含 `card_id + contract_version + field_path + declared_state`；output precision 与 validation plan 还必须通过 `FrozenDeclarationBinding` 唯一表达引用存在性，`RESOLVED.ref` 通过 `FrozenDeclarationRef` 提供稳定身份、版本与摘要。
8. Markdown 冻结字段只接受 canonical `mdff:v1`，并按 heading/card/original-label 三重结构身份恰一解析；JSON-like whole path、数组位置、模糊文本、alias 或语义猜测均不得兼容。
9. `FrozenCardFieldRef.declared_value` 必须与 resolver 选中原文值的规范 COPY 逐值一致；resolver 不得自行拼接 JSON-like field name、拆分业务维度或从内容反推 selector。
10. `SourceLocator.path`、`object_id`、`field_path` 只负责来源定位；snapshot version、digest 与 `captured_at` 仅由必填 `SourceLocator.binding` 的判别分支承载。定位字段与 binding 联合身份职责分离并联合验证，互不替代；无法形成合法 binding 时必须按既定 migration／`UNVERSIONED_SOURCE` 边界 fail closed，不得声称 validated frozen COPY。
11. 冻结声明存在且声明值为 null 时，引用绑定仍必须为 `RESOLVED`；裸 nullable 引用以及用非 `RESOLVED` 分支代替 explicit-null 值均为结构违规。
12. `UNAVAILABLE` 或 `UNRESOLVABLE` 必须携带非空 issue 并 fail closed；不得发布依赖该声明的输出、建立有效反馈绑定或进入学习。
13. YAML 文本不得成为运行算法。
14. `EXPLICIT_NULL`、`LISTED_UNRESOLVED`、`BOTH_NULL_AND_UNRESOLVED`、`ABSENT`、运行时无证据与 evaluator unknown 不得互换。
15. `unresolved_fields` 必须按卡、按字段原样保存。
16. `validation_timepoints` 与 `output_precision` 永不互映，且冻结 output precision 的标量、null、映射与嵌套对象形状必须逐值保留。
17. 卡片专属根源标签不得强制映射到共同根源枚举。
18. 适配器不得新增 F01–F12 业务判词、门、优先级或默认值。

### 5.3 时间不变量

14. 来源精度只可保留或降级，不可伪造提升。
15. `UNKNOWN` 时间不得改成 `TIMELESS`。
16. `AS_OF` 状态不得改写为事件发生点。
17. 开放区间不得自动闭合。
18. validation label 不等于实际日期或输出精度。

### 5.4 追溯不变量

19. 每条证据至少有一个 `SourceLocator`。
20. 每条关系至少有一个可解析来源引用。
21. 所有对象引用必须在包内存在，或以外部定位器明确声明。
22. 所有非逐值复制的字段都必须出现在 `TransformationRecord.field_mappings`。
23. 丢弃字段必须显式列入 `dropped_fields`；禁止静默丢失。
24. 由 Markdown／自由文本反推的结构化值不得标为 `LOSSLESS`。
25. `statement_index`、`statement_records` 和 v5/v6 feedback attachment 必须作为不同来源对象记录。

### 5.5 判定中立不变量

26. PI-210 模型不得包含候选胜方、门通过、优先级、最终动作或报告判词。
27. `SUPPORTS`、`COUNTERS`、`COMPETES_WITH` 等边仅陈述关系，不携带裁决效果。
28. `FunctionCandidate.status` 只描述证据包完整性，不描述业务成立性。
29. `pi220_consumable` 只表示结构与引用完整，不表示业务门通过。
30. 任何来源中已有的 decision 只能作为“来源决策对象”供追溯，不能倒灌为 PI-210 的新证据事实或预判 PI-220。

---

## 6. 现有模型适配边界

### 6.1 总原则

适配流程固定为：

```text
读取来源对象
  → 逐字段识别原始语义
  → 选择唯一证据轨道
  → 原值包装与来源定位
  → 建立显式关系
  → 登记转换保真度和缺口
  → 完整性检查
  → 生成 PI-220 只读视图或阻断
```

适配器只做：复制、精确枚举映射、类型保持解析、容器包装和引用建立。适配器不做：业务推断、置信度重算、候选裁决、空值补齐、自由文本事实抽取或跨轨合并。

### 6.2 适配矩阵

| 来源模型 | 可适配内容 | 目标轨道／对象 | 保真边界 |
|---|---|---|---|
| `tools.preflight.ParsedInput` / `engine.predicates.types.ParsedInput` | chart、dayun、known_facts、questions、case metadata | chart→结构轨；known facts→现实事实轨；questions→假设轨 | 两层 ParsedInput 字段不完全一致；缺少 warning 或藏干来源时须记录 PARTIAL；不得自动用标准表覆盖来源藏干而不记录 |
| `KnownFact` | year/event/content/type | `REALITY_EVENT` 或 `REALITY_STATE` | 有 year+event 可映射事件；content 型可映射状态；信息不完整时不得猜 kind，需阻断或人工确认 |
| D1–D4 findings / `AnalysisOutput` | Evidence rule refs、结构 finding、gate timing signals、support、final conclusions | 多数进入结构轨；候选事件进入假设轨；已有决策对象仅作来源引用 | 旧 `Evidence` 只有 rule/school/description/weight，不能提供现实验证状态；`FinalConclusion` 不是现实事实 |
| `CrossSchoolConflict` | stance、冲突描述、来源规则 | 竞争关系与来源对象 | 当前 production integration 可能为空；不得把空列表解释为无冲突 |
| parallel `ExpertReading` / `EvidenceItem` | claim、stance、evidence ref、scope、falsifier | 结构轨或假设轨，按原对象类型分开 | `EvidenceItem.strength` 不是统一置信度；`reading.stance=abstain` 不是 PI-220 动作 |
| parallel `AdjudicationResult` / `CrossExpertConflict` | 已有裁决及冲突快照 | 仅来源对象和追溯关系 | 不作为 PI-220 的预先胜方；不得复用其权重为 F01–F12 优先级 |
| `engine.claims.domain.Claim` / `Evidence` | claim、fact refs、feature refs、rule、time window、falsifier | claim 本体进入假设轨；其 evidence 按 refs 分轨 | Claim Evidence 同时引用 fact/feature，必须拆成多条证据或保留复合来源，不得混轨成一条 |
| staged `StageDecision` / `StagedArbitrationResult` | 分段裁决结果和 claim IDs | 仅来源决策对象 | 其 YAML 规则消费者与 F01–F12 YAML 无关；不得迁移算法或权重 |
| `DecisionRun` | chart/context ledgers、claims、verdicts、events、timings、decisions、report、feedback refs | 按 L0–L9 原语义分别适配 | 是 preprod 账本，不等于 production-default；空字符串默认字段不能自动解释为冻结 `null` |
| `SchoolEvidence` / `DomainEvidence` | school evidence、trace、time scope | 结构轨或假设轨 | 已含 support/conflict score 和 normalized confidence，但 PI-210 不复用这些聚合值作为统一事实 |
| `statement_index.json` | statement 到多规则的报告索引 | statement 来源对象与多规则关系 | 不是当前 feedback fanout 事实源 |
| `statement_records.json` | statement 到单一 runtime anchor rule | statement 来源对象与 anchor 关系 | 只保留首条有效 rule；必须登记信息损失，不能冒充完整 evidence chain |
| v5/v6 `V5FeedbackAttachment` | case/run/claim/prediction/signal 绑定 | feedback 来源与对象关系 | 不替代 production statement bridge，也不解锁 production 学习 |

### 6.3 明确不兼容点

以下情况不得自动转换为 PI-220 可消费证据：

- 字段只能从展示 Markdown 反推；
- 来源仅有空字符串，但目标语义需要区分 `null`、absent 与 unresolved；
- 复合 evidence 同时混有现实 fact 和结构 feature，且无法逐项定位；
- confidence 数值缺少其模型、尺度或语义标签；
- 时间字符串无法无损判断 point、interval 或 as-of；
- card field path 不存在或契约版本不匹配；
- statement 只有单 anchor rule，却被要求恢复完整多规则链；
- 已有 decision 被要求直接转为 F01–F12 的 gate 结果。

处理方式只能是：保留原值、登记 `NormalizationIssue`、将相关对象排除出 PI-220 视图或转人工复核。

---

## 7. 转换边界

### 7.1 允许的转换

- 字段逐值复制；
- 中文／英文固定枚举的一对一精确映射，并保留原值；
- 年份整数包装为 `TemporalPoint`；
- 明确的起止年包装为 `TemporalInterval`，边界语义未知时 inclusion 字段保持 `null`；
- 来源对象 ID 包装为 `ObjectRef`；
- 同一来源对象拆为多条不同轨道的证据，前提是每个来源字段均可独立定位；
- 将现有 conflict／counterevidence 关系包装成显式边，但不计算效果。

### 7.2 禁止的转换

- 从命理 finding 生成现实事实；
- 从 question 生成已发生事件；
- 从卡片文字生成 executable predicate；
- 从一个功能卡推导另一个功能卡缺失字段；
- 把空列表解释为“已检查且没有证据”；
- 把 `UNMAPPED`、空字符串、缺字段统一转为 `null`；
- 把 `confidence`、`strength`、`weight`、`support_score` 和反馈命中率统一归一化为同一可信度；
- 把已有 winner／decision 写入 `FunctionCandidate`；
- 把 validation labels 映射为实际时间或输出精度；
- 自动选择“第一条”“最强条”证据作为完整来源链。

---

## 8. 失败安全原则

1. **缺失即显式**：缺字段、断链、版本不匹配全部进入 `NormalizationIssue`。
2. **不确定即保留**：无法判定轨道或类型时保留原对象，不生成猜测记录。
3. **冲突不覆盖**：来源冲突时保留双方证据和 `CONTRADICTS` 关系。
4. **有损即标记**：任何信息压缩都必须标 `PARTIAL` 或 `LOSSY`。
5. **卡绑定失败即阻断**：冻结字段引用无法验证时，相关候选不得进入 PI-220 消费视图。
6. **跨轨污染即整包阻断**：检测到假设被列入现实事实、或结构被标为观察事实时，`pi220_consumable=false`。
7. **引用断裂即局部排除**：无法解析的证据／关系从 PI-220 只读视图排除，但原始包和问题记录保留给 PI-230。
8. **不以空代过**：空证据列表不等于门通过、无竞争、无反证或可弃权。
9. **不以旧决策代新判定**：现有轨道的 decision 只作历史来源，不预填 PI-220 输出。
10. **审计优先于便利**：宁可阻断自动消费，也不通过默认值或语义合并制造表面完整性。

---

## 9. 结构演示示例

> 本例只演示容器、三轨、时间、卡引用和关系。示例值不构成 F01–F12 新业务语义，不表示任何功能成立、门通过、优先级、输出动作或判词。

```yaml
schema_version: normalized-evidence-model.v1-design
package_id: NEP-DEMO-001
case_id: C-DEMO
run_context:
  source_track: MANUAL_IMPORT
  source_run_id: null
  source_schema_versions: {}
  observed_as_of: null
contract_binding:
  semantic_contract_id: real-world-function-evidence-cards-v1
  semantic_contract_path: engine/contracts/12-real-world-function-evidence-cards-v1.md
  declarative_appendix_path: mapping/real-world-function-evidence-cards-v1.yaml
  declarative_appendix_schema_version: null
  content_digest: null
  binding_status: UNVERIFIED
evidence_records:
  - evidence_id: EV-STRUCT-DEMO
    case_id: C-DEMO
    track: CHART_STRUCTURE
    kind: STRUCTURAL_FINDING
    subject:
      subject_type: FUNCTION
      subject_id: FC-DEMO
      function_id: F01
      domain: null
    payload:
      value_type: STRING
      value: 仅为结构占位文本
      value_schema: null
      raw_value: 仅为结构占位文本
      language: zh-CN
    assertion_mode: DERIVED
    polarity: NEUTRAL
    verification:
      status: SOURCE_VALIDATED
      verified_at: null
      verifier: null
      method: 仅验证来源结构
      contradiction_refs: []
    temporal_scope:
      mode: TIMELESS
      point: null
      interval: null
      as_of: null
      source_precision: UNKNOWN
      calendar: null
      timezone: null
      raw_expression: null
    sources:
      - source_id: SRC-FINDING-DEMO
        source_type: FINDING_OBJECT
        path: demo-only
        object_id: FINDING-DEMO
        field_path: value
        binding:
          binding_kind: UNVERSIONED_SOURCE
          binding_schema_version: source-binding.unversioned.v1
          reason_code: SOURCE_IDENTITY_NOT_VERSIONED
    card_field_refs: []
    confidence_ref: null
    source_object_refs: []
    unresolved_fields: []
    extensions: {}
  - evidence_id: EV-REALITY-DEMO
    case_id: C-DEMO
    track: REALITY_FACT
    kind: REALITY_STATE
    subject:
      subject_type: STATE
      subject_id: STATE-DEMO
      function_id: null
      domain: null
    payload:
      value_type: STRING
      value: 仅为现实状态占位文本
      value_schema: null
      raw_value: 仅为现实状态占位文本
      language: zh-CN
    assertion_mode: REPORTED
    polarity: NEUTRAL
    verification:
      status: SELF_REPORTED
      verified_at: null
      verifier: null
      method: null
      contradiction_refs: []
    temporal_scope:
      mode: AS_OF
      point: null
      interval: null
      as_of:
        value: 2026
        precision: YEAR
      source_precision: YEAR
      calendar: gregorian
      timezone: null
      raw_expression: 2026
    sources:
      - source_id: SRC-INPUT-DEMO
        source_type: INPUT_FIELD
        path: demo-only
        object_id: INPUT-DEMO
        field_path: known_facts[0]
        binding:
          binding_kind: UNVERSIONED_SOURCE
          binding_schema_version: source-binding.unversioned.v1
          reason_code: SOURCE_IDENTITY_NOT_VERSIONED
    card_field_refs: []
    confidence_ref: null
    source_object_refs: []
    unresolved_fields: []
    extensions: {}
  - evidence_id: EV-HYP-DEMO
    case_id: C-DEMO
    track: UNVERIFIED_HYPOTHESIS
    kind: FUNCTION_HYPOTHESIS
    subject:
      subject_type: FUNCTION
      subject_id: FC-DEMO
      function_id: F01
      domain: null
    payload:
      value_type: STRING
      value: 仅为候选占位文本
      value_schema: null
      raw_value: 仅为候选占位文本
      language: zh-CN
    assertion_mode: PROPOSED
    polarity: NEUTRAL
    verification:
      status: UNVERIFIED
      verified_at: null
      verifier: null
      method: null
      contradiction_refs: []
    temporal_scope:
      mode: UNKNOWN
      point: null
      interval: null
      as_of: null
      source_precision: UNKNOWN
      calendar: null
      timezone: null
      raw_expression: null
    sources:
      - source_id: SRC-HYP-DEMO
        source_type: CLAIM_OBJECT
        path: demo-only
        object_id: CLAIM-DEMO
        field_path: statement
        binding:
          binding_kind: UNVERSIONED_SOURCE
          binding_schema_version: source-binding.unversioned.v1
          reason_code: SOURCE_IDENTITY_NOT_VERSIONED
      - source_id: SRC-CARD-DEMO
        source_type: FROZEN_CONTRACT_FIELD
        path: engine/contracts/12-real-world-function-evidence-cards-v1.md
        object_id: F01
        field_path: mdff:v1/heading/4.1%20F01%20%E4%B8%93%E4%B8%9A%E6%8A%80%E6%9C%AF%E4%B8%8E%E5%88%A4%E6%96%AD%E8%BE%93%E5%87%BA/card/F01/item/%E8%BE%93%E5%87%BA%E7%B2%BE%E5%BA%A6
        binding:
          binding_kind: MARKDOWN_CONTRACT
          binding_schema_version: source-binding.markdown.v1
          source_snapshot_id: DEMO-UNVERIFIED-CONTRACT-SNAPSHOT
          source_schema_version: markdown-source.commonmark-0.31.2-mdff-v1
          contract_version: v1
          content_digest:
            algorithm: sha256
            canonicalization: RAW-UTF8-NO-BOM-LF
            value: 0000000000000000000000000000000000000000000000000000000000000000
          captured_at: 2026-07-19T00:00:00Z
    card_field_refs:
      - &F01_OUTPUT_PRECISION_REF
        card_id: F01
        contract_id: real-world-function-evidence-cards-v1
        contract_version: v1
        field_path: output_precision
        declared_state: EXPLICIT_NULL
        declared_value: null
        source_locator_id: SRC-CARD-DEMO
    confidence_ref: null
    source_object_refs: []
    unresolved_fields: []
    extensions: {}
relations:
  - relation_id: REL-DEMO
    relation_type: SUPPORTS
    from_ref: {object_type: EVIDENCE, object_id: EV-STRUCT-DEMO, external: false, source_locator_id: null}
    to_ref: {object_type: CANDIDATE, object_id: FC-DEMO, external: false, source_locator_id: null}
    scope: {function_id: F01, dimension: null}
    source_refs: [SRC-FINDING-DEMO]
    status: ASSERTED
    temporal_scope:
      mode: TIMELESS
      point: null
      interval: null
      as_of: null
      source_precision: UNKNOWN
      calendar: null
      timezone: null
      raw_expression: null
    metadata: {}
function_candidates:
  - candidate_id: FC-DEMO
    case_id: C-DEMO
    function_id: F01
    status: INCOMPLETE
    card_refs: [*F01_OUTPUT_PRECISION_REF]
    structure_evidence_ids: [EV-STRUCT-DEMO]
    reality_evidence_ids: [EV-REALITY-DEMO]
    hypothesis_evidence_ids: [EV-HYP-DEMO]
    counterevidence_ids: []
    root_evidence_ids: []
    timing_evidence_ids: []
    competing_candidate_ids: []
    competition_dimensions: []
    unresolved_fields: []
transformations: []
unresolved_issues:
  - issue_id: ISSUE-DEMO
    severity: BLOCKING
    code: CARD_BINDING_UNVERIFIED
    object_refs: []
    field_paths: []
    description: 演示包未验证冻结卡绑定
    required_disposition: EXCLUDE_FROM_PI220
integrity:
  referential_integrity: VALID
  card_binding_integrity: UNVERIFIED
  track_separation_integrity: VALID
  pi220_consumable: false
  blocking_issue_ids: [ISSUE-DEMO]
created_at: 2026-07-19T00:00:00Z
```

示例刻意保持 `pi220_consumable=false`，用于证明“不完整时失败安全”，不表达 F01 的任何业务结论。

---

## 10. PI-220 所需接口点

PI-210 仅定义 PI-220 可依赖的数据读取面，不定义其算法。

### 10.1 候选读取接口

```text
get_candidate(candidate_id) -> FunctionCandidate
list_candidates(case_id, function_ids?) -> list<FunctionCandidate>
```

保证：返回 F01–F12 候选、分轨 evidence IDs、竞争候选、反证、根源和时序引用；不返回预计算胜方或动作。

### 10.2 分轨证据接口

```text
list_evidence(candidate_id, track, kinds?, as_of?) -> list<EvidenceRecord>
list_counterevidence(candidate_id) -> list<EvidenceRecord>
```

保证：PI-220 可分别读取结构、现实、假设，不需要从 payload 文本判断轨道。

### 10.3 冻结卡声明接口

```text
resolve_markdown_frozen_field(locator: SourceLocator, ref: FrozenCardFieldRef)
  -> FrozenFieldObservation | UnresolvableIssue
get_card_field_ref(function_id, field_path) -> FrozenCardFieldRef
get_unresolved_states(function_id) -> list<UnresolvedFieldState>
get_validation_plan_binding(function_id) -> FrozenDeclarationBinding
get_output_precision_binding(function_id) -> FrozenDeclarationBinding
get_frozen_declaration(ref: FrozenDeclarationRef) -> ValidationPlanRef | OutputPrecisionRef
```

`resolve_markdown_frozen_field` 是设计期端口签名，不表示 resolver 已实现。它只接受 canonical `mdff:v1` 与 `MARKDOWN_CONTRACT` binding，执行文件→注册 profile/source spans→heading→card→原文 label→单值 COPY→联合 SourceBinding→declared value 的机械验证；不得执行卡片业务规则。unsupported dialect/profile、0 命中、多命中、label 漂移、continuation 歧义、摘要或联合身份不符、旧顶层 binding 字段、以及 declared value 不符均返回带 issue 的 `UNRESOLVABLE`，绝不猜测或 fallback。

其余保证：只返回冻结声明和状态，不执行卡片规则。两个 declaration getter 均返回完整判别联合，绝不返回裸 `null`。output precision 声明存在且可解析时，`get_output_precision_binding` 必须返回带非 null `FrozenDeclarationRef` 的 `RESOLVED` 分支，即使 `OutputPrecisionRef.declared_precision` 为 explicit null；validation plan 则按自身上游存在性独立返回相应分支。下游通过稳定引用的身份、版本和摘要解析同一不可变声明，不以裸字符串或字段路径猜测目标；`UNAVAILABLE` 与 `UNRESOLVABLE` 均 fail closed。

### 10.4 关系与竞争接口

```text
list_relations(object_id, relation_types?) -> list<EvidenceRelation>
get_competition_dimensions(candidate_id) -> list<CompetitionDimensionRecord>
```

保证：PI-220 能读取比较材料，但需自行依据其正式契约判定。

### 10.5 消费前完整性接口

```text
validate_for_pi220(package_id) -> IntegrityState
```

该接口只检查：ID、轨道、来源、卡绑定、空值保真、引用完整性和阻断问题。不得检查业务门、优先级、胜方或最终动作。

---

## 11. PI-230 所需接口点

### 11.1 对象追溯

```text
trace_to_sources(object_id) -> list<SourceLocator>
trace_transformations(object_id) -> list<TransformationRecord>
```

要求能够从 candidate／evidence／relation 回到：

- 原 input 字段；
- finding／claim／decision 对象及字段；
- statement index 或 statement record；
- feedback attachment；
- 冻结契约字段；
- 理论 rule/source locator。

### 11.2 引用图遍历

```text
incoming_relations(object_id) -> list<EvidenceRelation>
outgoing_relations(object_id) -> list<EvidenceRelation>
```

PI-230 可据此生成来源链、反证链、竞争链、验证链和转换链，但不得从关系链反推新的业务事实。

### 11.3 快照绑定

```text
get_contract_binding(package_id) -> ContractBinding
get_run_context(package_id) -> RunContext
get_integrity_state(package_id) -> IntegrityState
```

要求每次审计明确区分：production-default case、parallel-domain 输出、staged L6 结果、DecisionRun 与手工导入。

### 11.4 statement／feedback 边界

PI-230 必须保留三种不同绑定：

1. `statement_index`：报告 statement 到多规则证据索引；
2. `statement_records`：当前 feedback fanout 使用的单 anchor rule 桥；
3. v5/v6 attachment：run、claim、prediction、signal 级挂载。

任何一种都不得自动替代另外两种。若从多规则链降为单 anchor，转换必须显式标 `LOSSY`。

---

## 12. 可机械验收清单

以下条目用于检查 PI-210 文档设计完整性，不是 G2 自验，也不验证 PI-220 业务算法。

### 12.1 文档范围

- [ ] 只存在本 PI-210 设计产物的新增，不含生产代码改动。
- [ ] 文档明确声明不设计具体门算法、优先级、业务规则、卡片判词、G3 或 G5。
- [ ] 文档没有宣称 G2 已通过。

### 12.2 Schema 覆盖

- [ ] 顶层包包含 evidence、relations、function candidates、transformations、issues、integrity。
- [ ] 每条 evidence 含稳定 ID、case ID、唯一轨道、kind、subject、payload、验证、时间、来源。
- [ ] 三个轨道均有明确定义和污染禁令。
- [ ] 状态与事件有不同 `EvidenceKind`。
- [ ] 根源与时序有不同 payload 和 evidence IDs。
- [ ] competition、counterevidence、root、timing 均可结构化表达。
- [ ] `FunctionCandidate` 不含 winner、score、priority、passed、decision_action 或 output_text。

### 12.3 冻结语义保真

- [ ] 卡引用包含 card ID、契约版本、字段路径、声明状态和值。
- [ ] Markdown frozen field 使用 canonical `mdff:v1` heading/card/original-label 结构身份，且恰一命中。
- [ ] escaping、NFC、percent-encoding、canonical round trip 与 dialect/version 可机械校验。
- [ ] JSON-like whole path、数组位置、模糊匹配、alias、label rename 与 ambiguous Markdown 均 fail closed。
- [ ] resolver 的 source-span 规范 COPY 对 continuation、indent stripping、soft/hard break 与 U+0020/U+0009 trim 是单值函数，并与 `FrozenCardFieldRef.declared_value` 逐值一致。
- [ ] `SourceLocator.binding` 是 snapshot/version/digest/time 的唯一事实源；Markdown 与 JSON 使用互斥非 nullable 分支，旧顶层三字段不得双写。
- [ ] source path/object/field 与 binding 联合身份分责并联合验证，互不替代。
- [ ] `PRESENT_VALUE`、`EXPLICIT_NULL`、`LISTED_UNRESOLVED`、`BOTH_NULL_AND_UNRESOLVED`、`ABSENT` 可机械区分。
- [ ] 来源字段状态与 evaluator 状态使用不同类型且禁止静默折叠。
- [ ] `validation_timepoints` 与 `output_precision` 使用不同类型和不同稳定声明身份。
- [ ] output precision 的 null、标量、映射与嵌套对象形状均可无损表达。
- [ ] F06、F09、F10、F12 的明确未决项被列为重点保真对象。
- [ ] 没有 YAML 执行接口、评分表达式或默认回填规则。

### 12.4 时间与来源

- [ ] 时间支持 timeless、point、interval、as-of、unknown。
- [ ] 时间保留来源精度、开放边界和原始表达。
- [ ] validation label 不被当作日期。
- [ ] 每条证据至少一个来源定位器。
- [ ] 每条关系至少一个来源引用。
- [ ] contract binding 和 source run context 可独立追溯。
- [ ] `plans/` JSON snapshot 必须实际存在、使用 envelope/payload 分离、对象唯一且可用逐字段 JSON Pointer 终止定位。
- [ ] JSON snapshot 只摘要 `RFC8785-JCS-UTF8(payload)`，且 `content_digest` 只接受结构化 sha256 `DigestRef` 与 64 位 lowercase hex。
- [ ] JSON snapshot 五元 identity 在 `SourceBinding` 与 envelope 间逐字段相等；任一 payload/schema/contract 变化产生新 identity，payload 变化产生新 digest。
- [ ] snapshot/object/pointer missing、identity/digest mismatch 或 self-digest shape 均 fail closed，内联 prose 不得代替 external artifact。

### 12.5 转换与失败安全

- [ ] 每种适配映射可标 lossless、partial、lossy、unsupported。
- [ ] dropped fields 与 synthesized fields 可显式列举。
- [ ] 禁止由 Markdown、自由文本或空字符串静默补结构化语义。
- [ ] 卡绑定失败会阻断相关 PI-220 消费。
- [ ] 跨轨污染会令 `pi220_consumable=false`。
- [ ] 引用断裂保留问题记录，不静默删除来源。

### 12.6 现有模型边界

- [ ] production-default、parallel-domain、staged L6、v5/v6 preprod 被明确分账。
- [ ] ParsedInput 两层模型差异被承认。
- [ ] production `Evidence`、parallel `EvidenceItem`、claim `Evidence`、v2 `SchoolEvidence` 不被假称同一协议。
- [ ] 现有 decision 只作来源对象，不预判 PI-220。
- [ ] statement index、statement records、v5/v6 attachment 的职责不被合并。

### 12.7 PI-220／PI-230 接口

- [ ] PI-220 可按 candidate、track、kind、time 读取证据。
- [ ] PI-220 可读取冻结卡字段状态、竞争、反证、根源与时序引用。
- [ ] PI-220 完整性检查不包含业务判定。
- [ ] PI-230 可追到原对象、字段、run、契约和转换记录。
- [ ] PI-230 可区分报告索引、feedback bridge 与 preprod attachment。

---

## 13. 交付边界

本文件完成的是 PI-210 的模型设计：

- 建立三轨分账；
- 定义字段级证据 schema；
- 保持冻结卡字段、`null`、`unresolved_fields`、验证时点与输出精度的独立语义；
- 提供竞争、反证、根源、时序的中立表达；
- 明确现有多套模型的适配与信息损失边界；
- 为 PI-220 和 PI-230 留出只读接口；
- 给出失败安全与机械验收清单。

本文件不完成 PI-220 判定协议、不完成 PI-230 追溯实现、不修改生产路径，也不构成 G2 通过证明。
