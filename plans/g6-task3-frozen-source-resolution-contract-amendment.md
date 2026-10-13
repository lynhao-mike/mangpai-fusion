# G6 Task 3 · 冻结来源解析合同修订

> 状态：`CONTRACT_DRAFT_FOR_INDEPENDENT_REVIEW`
>
> 日期：2026-07-24（Asia/Shanghai）
>
> 权威范围：本文件仅补充 G6 Task 3 的公共接口归属、不可变 JSON envelope 形状与失败模型。它不改写冻结业务语义，不授权测试或实现，也不改变任何既有文件。

## 1. 适用范围与优先级

本修订针对 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) 中的 Task 3，并依赖：

- [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md) 第 4.4 节的 `SourceLocator`、Markdown `mdff:v1` 与 immutable JSON snapshot 规则；
- [`engine/f09/contracts.py`](../engine/f09/contracts.py) 中 `DigestRef`、`SourceLocator`、`MarkdownContractSourceBinding` 与 `ImmutableJsonSourceBinding` 的既有 owner；
- [`engine/f09/errors.py`](../engine/f09/errors.py) 中既有的 `F09SourceError` typed exception owner；
- [`production-implementation-pi-300-f09-source-snapshots-v1.json`](production-implementation-pi-300-f09-source-snapshots-v1.json) 的 envelope fixture。

冲突时，冻结业务语义仍以 PI-210 与正式契约为准；本文件只消除 Task 3 Python API 的机械可复制性缺口。不得把它解释为修改 `SourceLocator`、`SourceBinding`、`DigestRef` 或 Task 1 的既有公共类型。

## 2. 明确非目标与保护边界

本修订不：

1. 不修改或重定义 [`engine/f09/contracts.py`](../engine/f09/contracts.py) 已有的 `FrozenFieldObservation`；该类型服务于 frozen contract read port，与本 Task 3 的 source-copy DTO 不同，二者不得互换或合并。
2. 不要求在 [`engine/f09/contracts.py`](../engine/f09/contracts.py) 新增任何类型。
3. 不修改 Markdown/JSON parser、source fixture、测试、生产默认入口、YAML/mapping、feedback、learning 或后续 Task。
4. 不授权运行 RED、GREEN、回归或任何 Task 3 命令。
5. 不授权 Git 操作或任何 GitHub 操作。

用户已明确保护的预存文件均保持只读；本修订本身不构成对其修改许可。

## 3. 公共类型的唯一 owner 与导入规则

### 3.1 `FrozenFieldObservation`

Task 3 source-copy DTO 的唯一 canonical owner 是 [`engine/f09/markdown_source.py`](../engine/f09/markdown_source.py)。其精确公共形状为：

```python
@dataclass(frozen=True)
class FrozenFieldObservation:
    ref: str
    copied_value: object
    locator: SourceLocator
    transformation: Literal["MDFF_V1_COPY", "LOSSLESS_COPY"]
```

规则：

- [`engine/f09/json_source.py`](../engine/f09/json_source.py) 必须从 [`engine/f09/markdown_source.py`](../engine/f09/markdown_source.py) 导入此运行时同一类型；不得声明副本、TypeAlias 替代物或结构相同但 identity 不同的 dataclass。
- Markdown resolver 返回 `transformation="MDFF_V1_COPY"`；JSON resolver 返回 `transformation="LOSSLESS_COPY"`。
- `ref` 是 resolver 所使用的 canonical source reference：Markdown 为传入且已验证的 `mdff:v1` ref；JSON 为 `"{object_id}#{field_path}"`。
- 该 DTO 仅描述已成功完成的 source COPY。失败不返回部分 observation、`None`、`UNRESOLVABLE` sentinel 或 issue-bearing result union。

### 3.2 `ImmutableSnapshotEnvelope`

`ImmutableSnapshotEnvelope` 的唯一 canonical owner 是 [`engine/f09/json_source.py`](../engine/f09/json_source.py)，不得定义于 [`engine/f09/contracts.py`](../engine/f09/contracts.py)、Markdown resolver 或调用方。其精确形状为：

```python
@dataclass(frozen=True)
class ImmutableSnapshotEnvelope:
    source_snapshot_id: str
    snapshot_schema_version: str
    contract_version: str
    content_digest: DigestRef
    captured_at: str
    payload: dict[str, JcsValue]
    source_path: str
```

字段语义：

- 前五项严格对应 PI-210 `ImmutableJsonSourceSnapshot` 的联合 identity，顺序为 `source_snapshot_id / snapshot_schema_version / contract_version / content_digest / captured_at`。
- `payload` 是经过 `parse_bounded_jcs()` 成功解析的根 `payload` 值，运行时必须为 exact `dict[str, JcsValue]`；其摘要唯一是 `bounded_jcs_sha256(payload)`，不得对 envelope 摘要。
- `source_path` 是本次成功读取的 `Path` 的字符串表示，仅用于严格比较 `SourceLocator.path`；它不属于 snapshot identity，也不得由 locator、mtime、文件名或调用者补造。
- `ImmutableJsonSourceBinding.source_schema_version` 必须与 envelope 的 `snapshot_schema_version` 逐字段相等；其余 identity 字段与 binding 逐字段相等。二者不以字符串转换、摘要重算替换或任一侧优先。
- 本 DTO 是 PI-210 规范 `ImmutableJsonSourceSnapshot` 的 Task 3 runtime materialization；它不是新的独立 source-binding 分支，也不替代 `ImmutableJsonSourceBinding`。

## 4. 单一失败模型

Task 3 的四个公共 resolver API：

```python
resolve_markdown_frozen_field(...)
load_snapshot(...)
resolve_json_pointer(...)
resolve_snapshot_field(...)
```

采用唯一失败通道：所有 resolver/parse/identity/selector/pointer failure 都必须抛出 [`F09SourceError`](../engine/f09/errors.py)。成功时才返回其声明的成功值；不得返回 `IntegrityIssue`、`DetectedIssue`、`UNRESOLVABLE` binding、`None`、部分结果、裸 `ValueError`/`TypeError`/`OSError` 或未包装的 Task 2 `F09ContractError`。

每个 `F09SourceError` 必须：

- `issue_code` 为稳定、非空且可断言的错误码；
- `field_path` 为失败输入的 source-relative 或 API-relative定位；
- `diagnostic` 为字符串；
- 终止当前解析，不执行 fallback、模糊匹配、alias、默认值或二次来源读取。

PI-210 所说的 issue-bearing `UNRESOLVABLE` 是上层 declaration/binding 消费层的状态表达；Task 3 resolver 是其 fail-closed typed-exception producer。后续 consumer 如要构造 `UNRESOLVABLE`，必须捕获 `F09SourceError` 并在自身合同中保留该 exception 的 `issue_code` 与 `field_path`；Task 3 不直接构造 declaration binding。

## 5. 机械失败映射

| 失败族 | 必须失败的公开 API | `F09SourceError.issue_code` |
|---|---|---|
| Markdown 路径不可读、BOM、bare CR、非法 UTF-8 或非规范编码 | `resolve_markdown_frozen_field` | 分别为 `MARKDOWN.SOURCE_UNAVAILABLE`、`MARKDOWN.BOM_FORBIDDEN`、`MARKDOWN.BARE_CR`、`MARKDOWN.NONCANONICAL_ENCODING` |
| Markdown dialect/version、segment、percent encoding 或 canonical round trip 非法 | `resolve_markdown_frozen_field` | `MARKDOWN.SELECTOR_NONCANONICAL` |
| 不支持的 Markdown profile 或不能唯一产生受支持 profile/source span | `resolve_markdown_frozen_field` | `MARKDOWN.PROFILE_UNSUPPORTED` |
| heading 缺失 / 多重命中 | `resolve_markdown_frozen_field` | 分别为 `MARKDOWN.HEADING_UNRESOLVED` / `MARKDOWN.HEADING_NONUNIQUE` |
| card token 缺失、漂移或多重命中 | `resolve_markdown_frozen_field` | 分别为 `MARKDOWN.CARD_UNRESOLVED` / `MARKDOWN.CARD_NONUNIQUE` |
| label 缺失、rename 或多重命中 | `resolve_markdown_frozen_field` | 分别为 `MARKDOWN.LABEL_UNRESOLVED` / `MARKDOWN.LABEL_NONUNIQUE` |
| continuation membership、content start 或 copy span 无法唯一确定 | `resolve_markdown_frozen_field` | `MARKDOWN.SOURCE_SPAN_AMBIGUOUS` |
| locator、binding 分支或 source ID/type/object ID/field path 无效 | `resolve_markdown_frozen_field` | `MARKDOWN.LOCATOR_INVALID` 或 `MARKDOWN.BINDING_INVALID` |
| binding 六字段、expected digest、contract version 或 declared-value 发生 identity drift | `resolve_markdown_frozen_field` | `MARKDOWN.IDENTITY_MISMATCH`；只有已读取 artifact 的摘要值与 binding 或 expected digest 不等时为 `MARKDOWN.DIGEST_MISMATCH` |
| JSON 路径不可读、snapshot envelope 形状/identity 非法、payload 非对象、JCS parse failure | `load_snapshot` | `JSON.SOURCE_UNAVAILABLE`、`JSON.SNAPSHOT_IDENTITY_INVALID`，或从 Task 2 parse failure 转译的同一 `issue_code` |
| JSON payload digest 漂移 | `load_snapshot` | `JSON.PAYLOAD_DIGEST_MISMATCH` |
| JSON Pointer 语法非法、`~` escape 非法或路径未解析 | `resolve_json_pointer` | `JSON.POINTER_NONCANONICAL` 或 `JSON.POINTER_UNRESOLVED` |
| snapshot 参数、locator/binding/path/identity/source-type/object-id/field-path/source-id 不合法或不匹配 | `resolve_snapshot_field` | `JSON.SNAPSHOT_INVALID`、`JSON.LOCATOR_INVALID`、`JSON.SNAPSHOT_PATH_MISMATCH`、`JSON.SNAPSHOT_IDENTITY_MISMATCH` 或 `JSON.OBJECT_UNRESOLVED` |

此表为 Task 3 Markdown failure 的封闭代码表。实现和 RED tests 必须逐项使用所列代码；不得用通用 `MARKDOWN.SELECTOR_UNRESOLVED` 合并 heading/card/label，不得新增未列 `MARKDOWN.*` failure code，也不得为了补齐代码而扩大 Task 3 行为。

## 6. 接口间不变量

1. `load_snapshot()` 只读一次给定路径、仅接受 bounded JCS parser 的成功结果，并只摘要 `payload`。
2. `resolve_snapshot_field()` 只消费已经成功返回的 `ImmutableSnapshotEnvelope`；不读文件、不重解析、不重摘要。
3. `resolve_json_pointer()` 从传入 root 开始解析；Task 3 JSON field resolution 将命中 object 作为 root，因此 fixture 指针保持 `/value/...`。
4. Markdown resolver 仅接受 `MarkdownContractSourceBinding`；JSON resolver 仅接受 `ImmutableJsonSourceBinding`。交叉 binding 必须以 `F09SourceError` fail closed。
5. 不得将 Markdown 与 JSON source identity、object ID、selector、payload 或 observation 混用。

## 7. 重新准入所需的独立 CONTRACT 审查问题

独立 reviewer 必须以新鲜只读上下文逐项裁决：

1. source-copy `FrozenFieldObservation` 是否有且只有 [`engine/f09/markdown_source.py`](../engine/f09/markdown_source.py) 作为 runtime owner，且与 [`engine/f09/contracts.py`](../engine/f09/contracts.py) 的同名既有类型明确隔离；
2. `ImmutableSnapshotEnvelope` 的 owner、七字段、payload-only digest、五字段 identity 与 `ImmutableJsonSourceBinding` 的关系是否完整且无新增 authority；
3. 四个 Task 3 public API 是否都以 `F09SourceError` 作为唯一失败通道，且 PI-210 `UNRESOLVABLE` 的上层转换责任是否清晰；
4. 本修订是否没有修改或授权修改受保护的 Task 3 实现、测试和原计划文件；
5. 是否仍缺少会导致 RED 测试或最小实现不可机械复制的 High/Medium 合同缺口。

只有独立 CONTRACT review 给出 `PASS`，才可重新计算是否存在后续 RED 测试授权；本文件不自行授予该权限。
