# PI-285-R3：PI-210 locator amendment 独立复验记录

> `task_id`: PI-285-R3  
> `parent_task_id`: PI-200  
> `mode`: independent ultra-bounded amendment re-acceptance readonly + review record write  
> 裁决日期：2026-07-20（Asia/Shanghai）  
> 唯一裁决：**PASS**

## 1. 独立性与范围

本实例独立于 [`PI-215-R3`](production-implementation-pi-215-r3-source-locator-summary-consistency-remediation.md:1)，不继承其 `COMPLETED` 声明、自检结论或 M-04 closure 主张。复验直接对照 [`PI-285-R2 的 M-04`](production-implementation-pi-285-r2-pi210-locator-amendment-reacceptance.md:50)、[`PI-285-R1 findings`](production-implementation-pi-285-r1-pi210-locator-amendment-acceptance.md:76)、[`PI-210 第 2.2 节`](production-implementation-pi-210-normalized-evidence-model.md:44)、[`PI-210 SourceLocator/SourceBinding schema`](production-implementation-pi-210-normalized-evidence-model.md:260)、[`PI-210 冻结语义不变量`](production-implementation-pi-210-normalized-evidence-model.md:727)、[`PI-215-R2`](production-implementation-pi-215-r2-locator-amendment-remediation.md:1)及 [`PI-215-R3`](production-implementation-pi-215-r3-source-locator-summary-consistency-remediation.md:1)进行限定静态机械核验。

读取范围仅为任务指定文件，并对 [`PI-210`](production-implementation-pi-210-normalized-evidence-model.md:1) 全文执行旧 `SourceLocator` 顶层 version/digest/time 口径的限定静态语义搜索。旧字段名出现在规范性删除、迁移禁令、失败目录或反例时，按其语义归类，不按字符串命中数误判为残留。

本次未修改 [`PI-210`](production-implementation-pi-210-normalized-evidence-model.md:1)、[`PI-215-R2`](production-implementation-pi-215-r2-locator-amendment-remediation.md:1)、[`PI-215-R3`](production-implementation-pi-215-r3-source-locator-summary-consistency-remediation.md:1)或任何其他受验材料；未修改其他契约、PI-300、总控、handoff、代码或测试。唯一写入是本独立复验记录。未实现 resolver，未执行 YAML，未运行测试，未进入后续阶段，未递归委派。

判定严格 fail-closed：任一 High、Medium、关键歧义、关键证据缺失或新回归即为 **BLOCKED**；验收方不替整改材料补隐含结构、映射、parser、canonicalization 或迁移规则。

## 2. M-04 closure

| 核验面 | R2 阻断条件 | R3 机械证据 | 独立裁决 |
|---|---|---|---|
| 第 2.2 节摘要 | 不得把 `SourceLocator` 概括为旧顶层 version 加 optional digest；必须明确 locator 定位字段与必填 binding 分责 | [`第 2.2 节当前摘要`](production-implementation-pi-210-normalized-evidence-model.md:49) 明确 `path`、`object_id`、`field_path` 只负责定位，`SourceLocator` 携带必填 `SourceBinding`；snapshot version、content digest、captured time 仅由 binding 判别分支承载。digest 不再被描述为 frozen/validated locator 的 optional 顶层属性。 | PASS |
| 冻结语义不变量 | 摘要、schema 与核心不变量不得给出竞争结构解释 | [`冻结语义不变量第 10 条`](production-implementation-pi-210-normalized-evidence-model.md:732) 与第 2.2 节同口径：定位字段只定位，version/digest/time 仅由必填 binding 判别分支承载，二者分责、联合验证、互不替代。 | PASS |
| Schema 单一事实源 | `SourceBinding` 必须继续是唯一身份事实源；不得恢复旧顶层字段或双写 | [`SourceLocator`](production-implementation-pi-210-normalized-evidence-model.md:263) 只有定位字段与必填 `binding`；[`SourceBinding`](production-implementation-pi-210-normalized-evidence-model.md:275) 是封闭判别联合；[`单一事实源规则`](production-implementation-pi-210-normalized-evidence-model.md:318) 明确六个非判别身份字段在两个版本化分支中必填且不可为 `null`。 | PASS |
| Migration / fail-closed | 旧值不得被猜测补齐；无法原子迁移必须阻断 | [`删除与 migration 规则`](production-implementation-pi-210-normalized-evidence-model.md:320) 删除旧顶层三字段、禁止 shadow/deprecated 双写及 source/mtime/path/default 补齐；缺字段、digest 形状无效或分支不明时产生非空 `SOURCE_BINDING_MIGRATION_REQUIRED` issue 并 fail closed。[`resolver 失败目录`](production-implementation-pi-210-normalized-evidence-model.md:376) 与 [`resolver 端口`](production-implementation-pi-210-normalized-evidence-model.md:1143) 继续拒绝旧顶层字段。 | PASS |
| `UNVERSIONED_SOURCE` 边界 | 不得用无版本分支绕过 frozen/validated COPY 身份要求 | [`SourceBinding 约束`](production-implementation-pi-210-normalized-evidence-model.md:318) 禁止 `UNVERSIONED_SOURCE` 用于 frozen contract field、immutable JSON snapshot、`FrozenCardFieldRef` 或 `SOURCE_VALIDATED` 字段级 COPY；[`第 2.2 节`](production-implementation-pi-210-normalized-evidence-model.md:49) 与 [`不变量第 10 条`](production-implementation-pi-210-normalized-evidence-model.md:732) 均保留同一 fail-closed 边界。 | PASS |

**M-04 裁决：CLOSED / PASS。** [`PI-215-R3`](production-implementation-pi-215-r3-source-locator-summary-consistency-remediation.md:15) 的改动仅关闭 R2 指定的两处摘要一致性缺口；未改变 schema、dialect、resolver、snapshot、migration 或 F09 业务语义。当前第 2.2 节、冻结语义不变量、schema、migration 与 fail-closed 之间不存在竞争解释。

## 3. PI-285-R1 前四 finding 回归

| Finding | 必须继续成立的 closure 条件 | 当前机械证据 | 回归裁决 |
|---|---|---|---|
| H-01 | locator 可判别承载 Markdown/JSON 联合身份；binding 为单一事实源；legacy 原子迁移并 fail closed | [`SourceLocator.binding`](production-implementation-pi-210-normalized-evidence-model.md:272) 必填；Markdown 与 immutable JSON 分支分别具有必填 schema/snapshot/contract/digest/time 身份，见 [`SourceBinding`](production-implementation-pi-210-normalized-evidence-model.md:275)。[`migration`](production-implementation-pi-210-normalized-evidence-model.md:320)、[`Markdown 联合校验`](production-implementation-pi-210-normalized-evidence-model.md:356)及 [`JSON binding equality`](production-implementation-pi-210-normalized-evidence-model.md:402)均保持原子、逐字段、fail-closed。 | **CLOSED / PASS；无回归** |
| M-01 | 唯一 parser/profile；ATX source-byte identity；card token 精确边界与计数 | [`唯一 profile`](production-implementation-pi-210-normalized-evidence-model.md:330)、[`ATX source-byte 算法`](production-implementation-pi-210-normalized-evidence-model.md:332)及 [`card token 边界、计数与正反例`](production-implementation-pi-210-normalized-evidence-model.md:333)均未改变且仍为单值规则。 | **CLOSED / PASS；无回归** |
| M-02 | COPY 唯一规定 source-span continuation、indent、delimiter、soft/hard break、trim code points 与正反例 | [`label delimiter`](production-implementation-pi-210-normalized-evidence-model.md:334)、[`MDFF_V1_COPY`](production-implementation-pi-210-normalized-evidence-model.md:359)及 [`COPY 正反例`](production-implementation-pi-210-normalized-evidence-model.md:367)继续完整规定首个 leaf paragraph、container prefix、tab stop、LF、hard/soft break、marker 保留及仅 U+0020/U+0009 trim。 | **CLOSED / PASS；无回归** |
| M-03 | DigestRef wire shape 唯一；payload-only JCS；envelope/payload 分离；binding equality | [`snapshot envelope/payload`](production-implementation-pi-210-normalized-evidence-model.md:383)、[`payload-only JCS`](production-implementation-pi-210-normalized-evidence-model.md:398)、[`唯一 DigestRef wire shape`](production-implementation-pi-210-normalized-evidence-model.md:399)及 [`逐字段 equality`](production-implementation-pi-210-normalized-evidence-model.md:402)均未改变。 | **CLOSED / PASS；无回归** |

**前四 finding 统计：4/4 继续 CLOSED/PASS；回归 0。** M-04 摘要整改没有扩大到上述机制，也没有重开 H-01、M-01、M-02 或 M-03。

## 4. 限定全文语义搜索与精确统计

### 4.1 旧口径语义分类

对 [`PI-210`](production-implementation-pi-210-normalized-evidence-model.md:1) 全文进行 `SourceLocator` 与 version/digest/time 并列语义、旧顶层字段名、定位字段与 binding 职责的限定静态搜索，共识别 **5 组相关语义候选**：

1. **新口径摘要 1 组**：[`第 2.2 节`](production-implementation-pi-210-normalized-evidence-model.md:49)，明确必填 binding 与唯一承载关系；合规。
2. **规范性删除/迁移反例 1 组**：[`旧顶层三字段删除规则`](production-implementation-pi-210-normalized-evidence-model.md:320)；字段名出现是为了删除、禁止双写及定义 migration fail-closed，不是残留。
3. **新口径职责说明 1 组**：[`locator/binding 分责`](production-implementation-pi-210-normalized-evidence-model.md:374)，明确 binding 唯一证明并解释 snapshot；合规。
4. **新口径冻结语义不变量 1 组**：[`不变量第 10 条`](production-implementation-pi-210-normalized-evidence-model.md:732)；合规。
5. **新口径机械验收项 1 组**：[`机械验收清单`](production-implementation-pi-210-normalized-evidence-model.md:1242)，明确 binding 唯一事实源和禁止旧顶层双写；合规。

另有 [`失败目录`](production-implementation-pi-210-normalized-evidence-model.md:376)及 [`resolver 端口反例`](production-implementation-pi-210-normalized-evidence-model.md:1143)使用“旧顶层字段”这一反例性概称，语义均为拒绝并返回非空 issue，不构成旧结构许可。

### 4.2 精确统计

- PI-215-R3 声称的目标摘要缺口：**2**。
- 已独立确认修复：**2/2**（第 2.2 节 1 处；冻结语义不变量 1 处）。
- 限定全文相关语义候选组：**5**。
- 合规新口径候选组：**4**。
- 规范性删除/迁移反例候选组：**1**。
- 可解释为旧顶层 version/digest/time 许可的残留：**0**。
- R1 findings 继续关闭：**4/4**。
- High findings：**0**。
- Medium findings：**0**。
- Low findings：**0**。
- Informational findings：**0**。
- Critical ambiguities：**0**。
- Critical evidence gaps：**0**。
- New regressions/residual inconsistencies：**0**。
- FrozenCardFieldRef shape regressions：**0**。
- Snapshot/schema/migration/fail-closed regressions：**0**。

## 5. Tests 与 YAML 执行声明

- Tests executed：**0**。
- YAML executed：**0**。
- Resolver implementations executed：**0**。
- Production commands executed：**0**。
- Snapshots created：**0**。
- Reviewed artifacts modified：**0**。
- New review records written：**1**，即 [`本独立复验记录`](production-implementation-pi-285-r3-pi210-locator-amendment-reacceptance.md:1)。

本裁决仅构成限定文档契约的静态机械复验，不是 runtime、parser、source-span extractor、JCS serializer、digest verifier 或 source resolver 的实现证明。

## 6. 唯一裁决

# PASS

[`PI-215-R3`](production-implementation-pi-215-r3-source-locator-summary-consistency-remediation.md:1) 仅且充分关闭 [`PI-285-R2 的 M-04`](production-implementation-pi-285-r2-pi210-locator-amendment-reacceptance.md:50)：第 2.2 节与冻结语义不变量现均明确 locator 定位字段只负责定位，snapshot version、digest 与 captured time 仅由必填判别式 binding 承载，并与 schema、migration、resolver 及 fail-closed 规则一致。全文限定语义搜索未发现仍许可旧 `SourceLocator` 顶层 version/digest/time 的残留；规范性删除与反例中的旧字段名未被误判。

PI-285-R1 的 H-01、M-01、M-02、M-03 均继续关闭，未发现 High、Medium、关键歧义、关键证据缺失或新回归。依照本轮严格 fail-closed 门槛，本 amendment 通过独立复验。

## 7. 唯一下一动作

**PI-470-R3。**

本 PASS 只解除本次 locator amendment 的独立复验阻断，不代表 resolver 已实现、测试已通过、YAML 已执行、PI-300 已整改或任何后续 gate 已自动通过。