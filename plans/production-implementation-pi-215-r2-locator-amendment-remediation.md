# PI-215-R2：locator amendment 有界整改记录

> `task_id`: PI-215-R2  
> `parent_task_id`: PI-200/PI-400  
> `mode`: bounded amendment remediation write  
> 结论：`COMPLETED`  
> 性质：仅整改 PI-285-R1 的 H-01、M-01、M-02、M-03；待 PI-285-R2 分离独立复验

## 1. 范围与事实源

本任务只修改 [`PI-210`](production-implementation-pi-210-normalized-evidence-model.md:260) 与 [`PI-215-R1`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:1)，并新建本记录。直接依据是 [`PI-285-R1 验收矩阵`](production-implementation-pi-285-r1-pi210-locator-amendment-acceptance.md:29)、[`PI-210 resolver 端口`](production-implementation-pi-210-normalized-evidence-model.md:1122)、[`PI-230 身份原则`](production-implementation-pi-230-traceability-binding.md:112)、[`F09 冻结原文`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)及直接相关 G2 记录。

未修改 PI-220、PI-230、PI-300、冻结契约、mapping、总控、handoff、评审记录、代码或测试；未实现 resolver，未创建 snapshot，未执行 YAML，未运行测试，未进入 G5，未递归委派。

## 2. 四项 finding 修复证据

| Finding | 机械封闭内容 | 规范证据 |
|---|---|---|
| H-01 | `SourceLocator` 新增必填、封闭、判别式 `SourceBinding`。Markdown 与 immutable JSON 分支各自携带非 nullable `binding_schema_version + source_snapshot_id + source_schema_version + contract_version + DigestRef + captured_at`；普通无版本来源单独使用受限分支。旧顶层 `schema_version/content_digest/captured_at` 删除，禁止双写；旧实例必须原子迁移，缺字段或分支不明即 fail closed。 | [`SourceLocator/SourceBinding schema`](production-implementation-pi-210-normalized-evidence-model.md:263)、[`单一事实源与 migration`](production-implementation-pi-210-normalized-evidence-model.md:318)、[`联合职责`](production-implementation-pi-210-normalized-evidence-model.md:374) |
| M-01 | 唯一 parser profile 注册为 `markdown-source.commonmark-0.31.2-mdff-v1`，固定 CommonMark 0.31.2 子集；ATX opening、separator、optional closing、尾部空白均按 source bytes 定义；F01–F12 仅按 ASCII pattern、精确左右边界及不重叠起始 byte 计数。 | [`profile 与 ATX/card 词法算法`](production-implementation-pi-210-normalized-evidence-model.md:330)、[`PI-215-R1 profile 摘要`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:54) |
| M-02 | `MDFF_V1_COPY` 只消费 direct list item 首个 leaf paragraph source span；固定 delimiter、continuation membership、container indentation stripping、CRLF/LF、soft break→U+0020、hard break→U+000A、hard-break marker 保留、trim 仅 U+0020/U+0009，并给出正反例。 | [`MDFF_V1_COPY 单值函数`](production-implementation-pi-210-normalized-evidence-model.md:359)、[`COPY 摘要与例子`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:78) |
| M-03 | Immutable JSON 固定 envelope/payload 分离，只摘要 `RFC8785-JCS-UTF8(payload)`；`content_digest` 唯一使用结构化 `DigestRef`，algorithm=`sha256`、canonicalization=`RFC8785-JCS-UTF8`、value 为 64 lowercase hex，禁止 `sha256:<hex>` 字符串；binding 与 envelope 五元 identity 逐字段相等。 | [`snapshot schema 与 digest wire shape`](production-implementation-pi-210-normalized-evidence-model.md:378)、[`snapshot 摘要规则`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:124) |

## 3. Falsifiers 与 migration

以下失败均必须产生非空 issue 并 fail closed：

1. locator 缺 `binding`、仍带旧顶层三字段、同时双写、binding 分支错误、必填 identity 缺失或 locator 与 source identity 任一字段不同；
2. 未注册 parser/profile、ATX closing 被错误计入 `<H>`、`XF09`／`F09_` 被计 token、`F09/F10` 被计为一个；
3. continuation 跨 blank line、进入 nested list/code block、source span membership 不唯一、soft/hard break 输出错误、trim U+00A0/U+3000；
4. JSON digest 使用字符串、uppercase hex、摘要整个 envelope、把 identity 放入 payload、binding 与 envelope digest 三字段或其他 identity 字段不等；
5. 旧 [`/cards/F09/reality_hard_gate_and_dual_cards`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:42) 继续为 `UNSUPPORTED_DIALECT`，不作 JSON Pointer 外观兼容。

完整 falsifier 表见 [`PI-215-R1 修订后 Falsifiers`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:144)。旧 locator migration 不允许从 source 文件、mtime、路径名、默认 profile 或 resolver 推断缺失 identity；不能无损构造一个新分支时，唯一结果是 `SOURCE_BINDING_MIGRATION_REQUIRED`。

## 4. 非业务语义变更与兼容影响

本修订不改变 [`F09 现实硬门与双卡`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:269) 的资源、对象、配置轴、风险轴、归属、时态、单轴／双轴、state/event/outcome、门、竞争、动作或输出语义。selector 仍只定位整体原文值，不拆六字段。

兼容影响：

- `SourceLocator` 是有意的最小 breaking schema 收紧；旧顶层三字段不再接受，避免新旧双写漂移；
- 已有普通非冻结来源可显式迁入 `UNVERSIONED_SOURCE`，但不能借此声称 frozen-field 或 validated COPY；
- Markdown locator 必须声明唯一注册 profile 与完整联合 binding；
- immutable JSON snapshot 若未来创建，必须使用固定 envelope/payload 形状；本任务没有创建任何实际 snapshot；
- PI-300 旧 path 和不存在的 snapshot 状态保持 unsupported/unresolved，本任务不关闭相关 G4 finding。

## 5. 静态验证与执行声明

仅进行了限定文档的静态交叉核对：

- 核对 `SourceLocator` schema、resolver 文字、示例 locator 与机械验收清单不再引用已删除顶层三字段；
- 核对 parser profile、ATX/card token、COPY 与 digest 均只有一个规范输出；
- 核对 `SourceBinding.content_digest` 与 JSON envelope `content_digest` 逐字段使用同一 `DigestRef`；
- 核对 PI-215-R1 的兼容、风险、falsifier 与唯一下一动作已转为 R2 口径；
- 核对 F09 冻结原文未修改、PI-300 旧 path 仍 unsupported。

执行计数：

- Tests executed：**0**；
- YAML executed：**0**；
- Resolver implementations executed：**0**；
- Snapshots created：**0**；
- Production commands executed：**0**。

静态契约修订不构成 runtime proof，也不构成自验或 amendment PASS。

## 6. 修改文件

1. 修改 [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:260)：收紧 binding schema，注册 parser/token profile，定义 source-span COPY，统一 digest wire shape 与 snapshot envelope。
2. 修改 [`production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md`](production-implementation-pi-215-r1-markdown-frozen-field-locator-clarification.md:1)：同步 R2 规范摘要、falsifiers、migration、兼容与复验边界。
3. 新建 [`production-implementation-pi-215-r2-locator-amendment-remediation.md`](production-implementation-pi-215-r2-locator-amendment-remediation.md:1)：记录本次有界整改证据与执行声明。

## 7. 保留风险

1. parser、resolver、source-span 提取、JCS serializer 与 digest verifier 尚未实现；
2. breaking migration 会使所有未显式构造 `SourceBinding` 的旧 locator fail closed，这是消除双写歧义的预期结果；
3. Markdown source 编辑会改变 snapshot/digest，heading 或 label 编辑还会改变 selector identity，必须显式迁移；
4. 没有实际 immutable JSON snapshot，故本文只证明 schema 可机械表达，不证明 PI-300 source 已终止；
5. 本整改实例不得自验，PI-285-R1 的 BLOCKED 不能由本记录自行改写。

## 8. PI-285-R2 后续 finding 补记

[`PI-285-R2`](production-implementation-pi-285-r2-pi210-locator-amendment-reacceptance.md:44) 独立复验确认 H-01、M-01、M-02、M-03 均已关闭，但新增 M-04：PI-210 第 2.2 节仍以“附录路径、版本和可选内容摘要”概括 `SourceLocator`，与必填判别式 `SourceBinding` 的单一事实源规则冲突；全文静态搜索还发现冻结语义不变量第 10 条存在等价并列旧口径。该 finding 不回写为 R2 原四项整改失败，也不由本 R2 记录宣称关闭；其限定整改由 [`PI-215-R3`](production-implementation-pi-215-r3-source-locator-summary-consistency-remediation.md:1) 单独记录。

## 9. 唯一下一动作

**PI-285-R3：由与 PI-215-R3 分离的实例执行 independent amendment re-acceptance。**

在 PI-285-R3 给出 PASS 前，不得进入 PI-300 fixture 整改、G4 复评、resolver 实现、测试、生产接线或 G5。