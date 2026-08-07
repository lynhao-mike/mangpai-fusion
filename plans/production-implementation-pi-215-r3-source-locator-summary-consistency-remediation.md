# PI-215-R3：SourceLocator 摘要一致性有界整改记录

> `task_id`: PI-215-R3  
> `parent_task_id`: PI-200/PI-400  
> `mode`: ultra-bounded documentation consistency remediation  
> 结论：`COMPLETED`  
> 性质：仅整改 PI-285-R2 的 M-04；待 PI-285-R3 分离独立复验

## 1. 范围与事实源

本任务只修改 [`PI-210`](production-implementation-pi-210-normalized-evidence-model.md:44) 与 [`PI-215-R2`](production-implementation-pi-215-r2-locator-amendment-remediation.md:74)，并新建本记录。直接依据是 [`PI-285-R2 的 M-04`](production-implementation-pi-285-r2-pi210-locator-amendment-reacceptance.md:50)、[`PI-210 第 2.2 节`](production-implementation-pi-210-normalized-evidence-model.md:44)、[`SourceLocator/SourceBinding 规范`](production-implementation-pi-210-normalized-evidence-model.md:260)及 [`PI-215-R2`](production-implementation-pi-215-r2-locator-amendment-remediation.md:1)。

未修改其他文件；未改变 schema、dialect、resolver、snapshot 契约或 F09 业务语义；未实现、未测试、未执行 YAML、未进入后续阶段、未递归委派。本整改实例不自验。

## 2. M-04 精准修复

1. [`PI-210 第 2.2 节`](production-implementation-pi-210-normalized-evidence-model.md:49) 不再把 `SourceLocator` 概括为“附录路径、版本和可选内容摘要”，改为明确：`path`、`object_id`、`field_path` 只负责来源定位，并携带必填 `SourceBinding`；snapshot version、content digest、captured time 仅由 binding 的判别分支承载。
2. 同一条边界明确禁止 mapping 伪造或补齐 binding；无法提供完整版本身份时只能 fail closed，或仅在适用的非冻结来源上显式使用 `UNVERSIONED_SOURCE`，且不得据此声称 validated frozen COPY。
3. PI-210 全文静态搜索发现 [`冻结语义不变量第 10 条`](production-implementation-pi-210-normalized-evidence-model.md:732) 将 locator 定位字段与 version/digest/time 并列，存在等价旧结构解释；该条已同步改为定位字段与必填 binding 分责、联合验证且互不替代，并保留既定 migration、`UNVERSIONED_SOURCE` 与 fail-closed 边界。
4. [`PI-215-R2`](production-implementation-pi-215-r2-locator-amendment-remediation.md:82) 仅补记 PI-285-R2 后续 M-04 及其独立 R3 整改归属，不改写 R2 对 H-01、M-01、M-02、M-03 的历史记录。

## 3. 静态搜索结果

对 PI-210 全文中 `SourceLocator` 与 version/digest/time 的并列概括、旧顶层字段名及等价语义进行限定静态搜索：

- 命中并整改旧摘要：原第 49 行，共 **1** 处；
- 命中并整改等价并列旧口径：原第 732 行，共 **1** 处；
- `SourceLocator.schema_version`、`SourceLocator.content_digest`、`SourceLocator.captured_at` 的其余命中仅位于 [`删除与 migration 禁令`](production-implementation-pi-210-normalized-evidence-model.md:320)，属于保留的规范性反例，不是旧字段残留；
- `SourceLocator.binding` 单一事实源、resolver 联合验证、snapshot envelope equality、示例与机械验收清单保持新口径；未扩大整改。

## 4. 不变项

本任务没有改变：

- `SourceLocator` 或 `SourceBinding` schema；
- `mdff:v1` dialect、parser profile 或 COPY 规则；
- Markdown resolver 步骤、immutable JSON snapshot envelope/payload 或 digest wire shape；
- migration issue、`UNVERSIONED_SOURCE` 适用范围或 fail-closed 行为；
- F09 的资源、对象、配置轴、风险轴、归属、时态、门、竞争、动作或输出语义。

## 5. 执行声明

- Tests executed：**0**；
- YAML executed：**0**；
- Resolver implementations executed：**0**；
- Production commands executed：**0**；
- 自验：**0**。

## 6. 修改文件与行号

1. [`PI-210 第 2.2 节 SourceLocator 摘要`](production-implementation-pi-210-normalized-evidence-model.md:49)；
2. [`PI-210 冻结语义不变量第 10 条`](production-implementation-pi-210-normalized-evidence-model.md:732)；
3. [`PI-215-R2 后续 finding 补记与下一动作`](production-implementation-pi-215-r2-locator-amendment-remediation.md:82)；
4. 新建 [`本 PI-215-R3 整改记录`](production-implementation-pi-215-r3-source-locator-summary-consistency-remediation.md:1)。

## 7. 唯一下一动作

**PI-285-R3：由与 PI-215-R3 分离的实例执行 independent amendment re-acceptance。**

在 PI-285-R3 给出裁决前，不进入 PI-300 fixture 整改、G4 复评、resolver 实现、测试、生产接线或 G5。