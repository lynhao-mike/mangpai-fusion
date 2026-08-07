# PI-215-R1：Markdown frozen-field locator 最小澄清

> `task_id`: PI-215-R1  
> `parent_task_id`: PI-200/PI-400  
> 用户授权：明确选择 A，授权最小 PI-210 locator 解析契约  
> 结论：`COMPLETED`  
> 性质：设计契约 amendment；待分离实例 PI-285-R1 独立验收

## 1. 目的与授权结论

本次只澄清 [`SourceLocator`](production-implementation-pi-210-normalized-evidence-model.md:263) 与 [`FrozenCardFieldRef`](production-implementation-pi-210-normalized-evidence-model.md:458) 对冻结 Markdown 字段的机械定位语义：新增通用、版本化、fail-closed 的 `mdff:v1` path dialect 及 resolver 契约，并规定后续可在 `plans/` 下创建的不可变 JSON source snapshot fixture 最小终止条件。

本次不实现 resolver，不创建 PI-300 具体 fixture，不执行 YAML，不运行测试，不修改 production-default，不进入 G5。未修改 PI-220、PI-230、PI-300、冻结契约、mapping、总控、handoff、评审记录、代码或测试。

## 2. 问题边界

独立 G4 复评确认两个机械断点：

1. PI-300 使用的 `/cards/F09/reality_hard_gate_and_dual_cards` 具有 JSON-like 外观，但冻结源只有 Markdown heading 下的一条“现实硬门与双卡”列表项；原 PI-210 未定义 path dialect 或 Markdown resolver，见 [`G4-H-01`](production-implementation-pi-400-r3-g4-technical-rereview.md:33)。
2. state/event/outcome locator 指向未实际存在的 external JSON snapshot，导致 path/object/field/schema/digest/time 不能联合终止，逐字段 `LOSSLESS COPY` 无来源侧证明，见 [`G4-M-01`](production-implementation-pi-400-r3-g4-technical-rereview.md:34)。

PI-230 已规定 path 定位、digest 证明、version 解释且不可互换，见 [`来源身份职责`](production-implementation-pi-230-traceability-binding.md:112)。本 amendment 只补 PI-210 的通用 locator 解释，不改变该职责边界。

## 3. Schema 与 path dialect

规范定义集中写入 [`mdff:v1`](production-implementation-pi-210-normalized-evidence-model.md:297)。正式语法为：

```text
mdff:v1/heading/<H>/card/<C>/item/<L>
```

三个 selector 都来自明确 Markdown 结构身份：

- `<H>`：ATX heading 去掉 marker 后的完整原文 heading text；
- `<C>`：heading 中恰一出现的显式 `F01`–`F12` card token；
- `<L>`：直接无序列表项第一个非 code-span 冒号前的完整原文 label。

三者先做 Unicode NFC，再按 UTF-8 octet 进行 RFC 3986 percent-encoding；只有 unreserved octet 不转义，percent hex 必须大写，并要求 parse→canonical encode 的逐字节 round trip。路径不采用 heading slug、数组位置、自然语言语义、模糊匹配、本地 alias、snake_case 字段名或 JSON Pointer 外观。

以下旧路径被正式判定为 `UNSUPPORTED_DIALECT`：

```text
/cards/F09/reality_hard_gate_and_dual_cards
```

F09 当前原文的 canonical selector 是：

```text
mdff:v1/heading/4.9%20F09%20%E8%B5%84%E6%9C%AC%E9%85%8D%E7%BD%AE%E4%B8%8E%E9%A3%8E%E9%99%A9%E6%89%BF%E6%8B%85/card/F09/item/%E7%8E%B0%E5%AE%9E%E7%A1%AC%E9%97%A8%E4%B8%8E%E5%8F%8C%E5%8D%A1
```

该 selector 只定位 [`F09 现实硬门与双卡`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:269) 冒号后的完整原文值，不把六维拆成六个字段，不增加任何 F09 专用业务规则。

### 3.1 PI-215-R2 词法 profile 收紧

PI-215-R2 将唯一 parser profile 注册为 `markdown-source.commonmark-0.31.2-mdff-v1`：只用 CommonMark 0.31.2 的块规则识别 0–3 space 缩进 ATX heading、`-`／`+`／`*` 直接无序列表项及首个 leaf paragraph；setext、ordered list、blockquote、HTML、表格、code block、嵌套列表与跨 blank line paragraph 均不受支持。库实现名或宽泛的 CommonMark-compatible 声明不再构成合规证据。

ATX `<H>` 由 source bytes 唯一提取：移除合法 opening marker 及其分隔 U+0020/U+0009；仅当尾部匹配“分隔 U+0020/U+0009 + closing `#` sequence + 可选 U+0020/U+0009”时移除 closing；最后只 trim U+0020/U+0009。inline source 不 render、不 entity decode。card token 只计边界外不邻接 ASCII `[A-Za-z0-9_]` 的 `F0[1-9]`／`F1[0-2]`，按起始 byte 不重叠计数并要求恰一：`[F09]` 计一，`XF09` 与 `F09_` 计零，`F09/F10` 计二并阻断。

## 4. Resolver 契约

规范 resolver 步骤见 [`Markdown resolver 的确定性步骤`](production-implementation-pi-210-normalized-evidence-model.md:329)：

1. 验证 dialect/version、固定段、escaping 和 canonical round trip；
2. 用 `SourceLocator.path` 读取确切 Markdown artifact，并要求 `binding_kind=MARKDOWN_CONTRACT`；
3. 严格按注册 profile 获取 ATX、direct list item、首个 leaf paragraph 与 source spans；
4. 按 source-byte ATX 算法要求 heading 恰一命中，并按精确 ASCII 边界要求 card token 恰一且等于 `<C>`；
5. original label 必须在该 card object 的直接列表项首个 leaf paragraph 中恰一命中；
6. 对 delimiter 后 source span 执行唯一 `MDFF_V1_COPY`；
7. 联合校验 `SourceBinding` 的 snapshot ID、binding/source/contract version、结构化 digest 与带时区 `captured_at`；
8. 要求 [`FrozenCardFieldRef.declared_value`](production-implementation-pi-210-normalized-evidence-model.md:465) 与 COPY 的 JSON string value 逐码点相等。

resolver 输出只证明声明值复制与来源绑定，不执行门判断，不从值构造 JSON-like field name，也不从 label 或内容推导业务 enum。

### 4.1 `MDFF_V1_COPY` 单值规则

COPY 输入只取命中 direct list item 首个 leaf paragraph：首行从第一个非 code-span `:`／`：` 后开始；continuation 只含同一 leaf paragraph source span、且无 blank line 分隔的后续 physical lines。按 CommonMark 0.31.2 容器归属去除每行 list indentation prefix 后保留全部 inline source bytes；membership 或 content start 不唯一即阻断。

LF 前若内容以反斜杠 byte 结尾，或以至少两个 U+0020 结尾，则为 hard break，唯一输出为 U+000A；否则 soft break 唯一输出 U+0020。hard-break marker bytes 保留，因而两空格 hard break 输出为“两空格 + U+000A”，反斜杠 hard break 输出为“反斜杠 + U+000A”。最终只 trim 整体两端 U+0020/U+0009；U+000A、U+00A0、U+3000 不 trim。inline source、entity source、backtick 与反斜杠转义均不 render/decode。

正例：`甲\n  乙` → `甲 乙`；`甲  \n  乙` → `甲  \n乙`；`甲\\\n  乙` → `甲\\\n乙`。blank line 后 paragraph、nested list、code block 均不属于值；歧义 source span 不允许择一。

## 5. 定位与证明职责边界

- `SourceLocator.path`：选择 source artifact 文件；
- `object_id`：声明 snapshot 内稳定对象身份；Markdown v1 必须等于解码后的 card identity；
- `field_path`：在对象内选择冻结列表字段；
- `binding`：唯一承载 snapshot ID、binding/source/contract version、结构化 `DigestRef` 与 `captured_at`。

`SourceBinding` 是封闭判别联合：Markdown 必须使用非 nullable `MARKDOWN_CONTRACT` 分支，immutable JSON 必须使用非 nullable `IMMUTABLE_JSON_SNAPSHOT` 分支；非版本化普通来源只可使用 `UNVERSIONED_SOURCE`，且不能用于 frozen field 或 validated COPY。旧 locator 顶层 `schema_version/content_digest/captured_at` 删除且禁止双写；旧实例必须原子迁移到一个 binding 分支，缺任一 identity 字段或分支不可判定即 `SOURCE_BINDING_MIGRATION_REQUIRED` 并 fail closed。

path、object、field 与 binding 必须联合一致。digest 不能替代 path，path 命中不能替代 binding，时间不能掩盖内容或版本漂移。

## 6. 唯一命中与 fail-closed 不变量

以下情况全部生成非空 issue、结果为 `UNRESOLVABLE` 或 `UNSUPPORTED_DIALECT`，并阻断相关 PI-220 消费：

- unsupported dialect/version 或 non-canonical escaping；
- missing/duplicate heading 或 card；
- missing/duplicate label；
- label rename、heading rename 或 card token 漂移；
- setext heading、嵌套对象越界、重复字段或 ambiguous Markdown；
- content/digest mismatch、contract/schema version mismatch；
- locator card 与 ref card 不同；
- resolver 选中原文与 `declared_value` 不一致。

label rename 是 identity change。即使值未变化，旧 selector 也必须 0 命中；不得用 alias、编辑距离、翻译、slug、相邻位置或内容相同恢复。新 label 需要新 canonical path 和显式引用迁移。

## 7. Immutable JSON source snapshot fixture 最小约束

规范最小契约见 [`plans/ immutable JSON source snapshot fixture`](production-implementation-pi-210-normalized-evidence-model.md:369)。后续获授权整改可在 `plans/` 创建实际 `.json` fixture，但本任务未创建 PI-300 的 state/event/outcome snapshot。

机械终止条件：

1. locator 的 repository-relative `.json` 文件实际存在且 binding 为 `IMMUTABLE_JSON_SNAPSHOT`；prose 或内联 fixture 不替代文件；
2. 文件固定为 envelope，其中 `payload.objects` 是唯一被摘要 payload；五个 identity 字段全部外置，禁止 self-digest；
3. 摘要输入唯一为 `RFC8785-JCS-UTF8(payload)`；
4. `content_digest` 唯一为结构化 `DigestRef {algorithm: sha256, canonicalization: RFC8785-JCS-UTF8, value: 64 lowercase hex}`，禁止 `sha256:<hex>` 字符串；
5. `payload.objects` 由 `object_id` 唯一键控，禁止数组位置身份与 duplicate JSON key；
6. 每个来源字段使用从对象根开始的 RFC 6901 JSON Pointer，禁止 JSONPath、模糊键、alias 或目标侧 payload 回填；
7. `source_snapshot_id + snapshot_schema_version + contract_version + content_digest + captured_at` 构成联合 identity，binding 与 envelope 对应字段必须逐字段相等；
8. payload/schema/contract/object/field 变化产生新 identity，payload 变化产生新 digest，不得原 identity 覆写；
9. snapshot missing、错误 binding 分支、identity 任一 mismatch、object/pointer 失败、JCS 失败、digest wire shape/value 不符全部 fail closed。

这一定义只规定 fixture 格式与定位要求，不预先决定 PI-300 fixture 的文件名、对象值、业务内容或整改结果。

## 8. Falsifiers

| Falsifier | 必须结果 |
|---|---|
| `/cards/F09/reality_hard_gate_and_dual_cards` 或 `mdff:v2/...` | `UNSUPPORTED_DIALECT` |
| 未注册 parser/profile 或 ATX source spans 不唯一 | `UNRESOLVABLE` + profile issue |
| `## F09 标题 ##` 把 closing `##` 计入 `<H>` | 错误实现；规范 `<H>` 为 `F09 标题` |
| `XF09`／`F09_` 计为 token，或 `F09/F10` 计为一个 | `UNRESOLVABLE` + token-boundary/count issue |
| heading/card/label 0 命中或多命中 | `UNRESOLVABLE` + missing/ambiguity issue |
| label 改名但值相同 | 旧 path 失败；禁止 alias fallback |
| continuation 跨 blank line、进入 nested list/code block 或 membership 不唯一 | `UNRESOLVABLE`；禁止并入 COPY |
| soft break 非 U+0020，hard break 非 U+000A，或 trim U+00A0/U+3000 | COPY mismatch，阻断 |
| source bytes 与 digest 不同或 `declared_value` 与 COPY 不同 | mismatch，阻断 |
| locator 缺 binding、保留旧顶层三字段、binding 分支错误或 identity 任一字段不同 | migration/binding mismatch，阻断 |
| snapshot 文件／object／pointer 不存在、不唯一或不受支持 | resolution failure，阻断 |
| snapshot digest 为 `sha256:<hex>` 字符串、uppercase hex、摘要 envelope 或 identity 在 payload 内 | digest shape/self-digest failure，阻断 |
| binding 与 envelope 五元 identity 任一字段不同 | identity mismatch，阻断 |

## 9. 兼容影响与风险

### 9.1 兼容影响

- PI-210 的 `SourceLocator` 最小收紧：新增必填判别式 `SourceBinding`，删除顶层旧 `schema_version/content_digest/captured_at`；未原子迁移的旧实例 fail closed，不接受双写过渡。
- 既有合法 JSON source locator 继续使用 RFC 6901 JSON Pointer，不改用 `mdff:v1`。
- 旧 JSON-like Markdown whole path 现在明确不兼容，相关 PI-300 fixture 在后续整改迁移前必须 fail closed。
- PI-220 与 PI-230 schema 未修改；PI-220 继续消费已解析的真实 `FrozenCardFieldRef`，PI-230 继续按 path/digest/version 分责追踪。
- production-default、运行时 consumer、renderer、feedback 与 learning 均未改变。

### 9.2 保留风险

1. resolver、已注册 parser profile、source-span COPY、canonical serializer 与 digest verifier均尚未实现；本文不能作为 runtime proof。
2. `mdff:v1` 有意只支持 ATX heading 与直接无序列表项；其他 Markdown 结构必须等待新 dialect/version，不允许当前实现猜测。
3. heading 或 label 原文编辑会改变 path identity；这是 fail-closed 设计结果，迁移必须显式完成。
4. 实际 PI-300 snapshot 尚不存在，G4-M-01 仍须后续整改创建真实 fixture 后才能重新评审。
5. PI-300 尚未迁移正式 `mdff:v1` path；G4-H-01 不由本 amendment 自动关闭。
6. 本 amendment 不能自验，不能宣称 G2 amendment PASS、G4 PASS、实现完成、production readiness 或 G5 解锁。

## 10. 非业务语义变更声明

本次没有修改 [`F09 冻结文本`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)，没有修改资源、对象、配置轴、风险轴、归属、时态、单轴／双轴、state、event、outcome、S1–S3、E1–E3 或任何门、竞争、动作与输出语义。`mdff:v1` 是冻结 Markdown 通用定位机制，不包含 F09 专用 evaluator 或业务 alias。

## 11. 静态一致性检查

只进行了文档静态交叉核对：

- 对照 PI-210 的 source/ref/null/转换边界；
- 对照 [`PI-230 身份原则`](production-implementation-pi-230-traceability-binding.md:112)，确认 path/digest/version 不互代；
- 对照 [`F09 原文`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)，确认 canonical selector 可定位“现实硬门与双卡”完整值且未改文字；
- 对照 [`PI-300 旧 whole path`](production-implementation-pi-300-one-card-vertical-slice-design.md:451)，确认其被明确判为 unsupported；
- 对照 [`PI-300 external fixture 断点`](production-implementation-pi-300-one-card-vertical-slice-design.md:757)，确认实际文件、对象唯一、逐字段 pointer、联合身份及 fail-closed 终止条件均已定义。

**结果：静态一致性检查完成；0 tests executed；0 YAML executed；0 production changes；0 PI-300 fixtures created。**

## 12. 修改文件

1. 修改 [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:260)：增加 `mdff:v1` schema/path dialect、resolver、canonical COPY、职责边界、JSON snapshot 最小约束、接口和机械验收项。
2. 新建 [`production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:1)：记录授权、修订内容、falsifiers、兼容影响、风险与独立验收边界。

## 13. PI-215-R2 后续边界与唯一下一动作

PI-285-R1 已独立裁定 H-01、M-01、M-02、M-03 成立；PI-215-R2 仅按该反馈收紧契约文字和 schema，不自验，不更改 F09 业务语义，也不创建 PI-300 snapshot。旧 PI-300 JSON-like path 继续是 unsupported，且本修订不授权实现或 G5。

**唯一下一动作：PI-285-R2 independent amendment re-acceptance。**

PI-285-R2 必须由与本整改分离的实例执行，逐项机械核对判别式 binding 单一事实源、parser/token profile、source-span COPY、结构化 digest 与 envelope/payload 分离、migration 及全部 falsifiers。在 PI-285-R2 给出 PASS 前，不得把本次 `COMPLETED` 解读为 amendment PASS，不得进入 PI-300 fixture 整改、G4 复评或 G5。