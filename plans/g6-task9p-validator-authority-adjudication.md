浩哥

# Task 9-P/P-1 上游 Validator Authority 裁决

> **裁决性质**：本文件是 P-1 两项 High blocker 的唯一上游 authority。它冻结 authority 边界与 failure precedence，不是生产实现授权，也不替代后续对 [`plans/g6-task9p-prerequisite-authority-contract.md`](g6-task9p-prerequisite-authority-contract.md) 的有界修订。
>
> **Gate：PASS**。此 PASS 仅表示本 adjudication 已形成可引用 authority，并且只解锁 P-1 合同修订；它不解锁 P-1 implementation，不授权修改 production/tests，不改变 Task 9-P 其他前置条件或总 Gate。

## 1. 目标与裁决范围

本裁决只解决以下上游问题：

1. [`validate_statement_projection()`](../engine/f09/trace.py:874) 经 [`_card_source_ref_valid()`](../engine/f09/trace.py:453) 与 [`_authoritative_card_source_ref()`](../engine/f09/trace.py:421) 读取 repository 固定文件时，P-1 builder 的 filesystem authority 边界。
2. P-1 exact top-level guards、Task 6 validator、P-1-exclusive checks 之间唯一的 failure precedence、异常 ownership 与 issue 映射。
3. 对后续 P-1 合同补齐 [`FrozenDeclarationRef`](../engine/f09/contracts.py:492) nested material，以及重构 negative ledger 的强制约束。
4. 上述裁决对 P-1 closed write set 的影响。

本裁决不实现 [`build_artifact_operation_authority()`](../engine/f09/artifacts.py)，不修改 Task 6 owner，不修改既有合同、production、tests 或 PI-500，也不批准 P-1 implementation。

---

## 2. 规范性术语

- **builder**：后续 P-1 合同将定义的 [`build_artifact_operation_authority()`](../engine/f09/artifacts.py)。
- **validator**：Task 6 已冻结的 [`validate_statement_projection()`](../engine/f09/trace.py:874)。
- **direct I/O**：builder 本体或任何 P-1-owned helper 直接调用 filesystem、环境变量、工作目录、网络、时钟、随机源或其他 ambient authority。
- **transitive I/O**：builder 恰好一次调用 validator 后，由 validator 的既有 Task 6 call graph 执行的 repository fixed-file reads。
- **strict success**：返回对象的运行时类型恰为 [`ProjectionValidationResult`](../engine/f09/trace.py:188)，且 `valid is True`，且 `detected_issues == ()`。
- **typed validator exception**：validator 抛出的任何现有 [`F09Error`](../engine/f09/errors.py:4) 实例，包括其既有子类。
- **P-1-exclusive check**：validator strict success 后仍无法由 Task 6 success predicate推出、且只服务 artifact authority material 构造的检查。它不得复制 validator predicate、检测顺序或 issue ownership。

---

## 3. Authority clauses

### AC-01：Filesystem authority 唯一选择为 A1

A1 是唯一合法方向：承认 [`validate_statement_projection()`](../engine/f09/trace.py:874) 对 repository 固定文件的读取属于 Task 6 frozen canonical authority。

A2 被明确排除。P-1 不得新增 source authority input/port，不得修改 validator signature，不得修改 [`engine/f09/trace.py`](../engine/f09/trace.py)，也不得以 P-1 名义重开 Task 6 owner。

### AC-02：唯一允许的 transitive I/O 例外

builder 可以且只能通过对 [`validate_statement_projection()`](../engine/f09/trace.py:874) 的恰好一次调用，间接触发 Task 6 frozen validator 的 fixed-file reads。该 transitive I/O 是“builder 无 direct I/O / 无 builder-owned ambient authority”规则的唯一例外。

因此，后续 P-1 合同不得再声称 builder 的完整 call graph 绝对无 I/O；必须改写为：

- builder 本体无 direct I/O；
- P-1-owned helper call graph 无 direct I/O；
- 唯一 transitive I/O 是 frozen validator 的 repository fixed-file authority verification；
- builder 不拥有、不选择、不注入、不替换、不缓存这些 filesystem authorities。

### AC-03：固定 authority 文件集合

validator transitive reads 只允许落在以下两个既有固定文件：

1. [`engine/contracts/12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md)
2. [`mapping/real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml)

该集合为 closed set。P-1 不得扩大路径集合，不得提供替代 root，不得依赖调用者当前工作目录，不得追加 retry、fallback、glob、目录扫描或其他读取。

### AC-04：读取次数与短路语义

后续测试必须通过 spy 隔离 builder-owned 与 validator-owned reads，并证明：

- validator 外的 builder/P-1 helper 没有 read；
- 所有 observed reads 都属于 validator 调用期间，且目标只可能是 AC-03 的固定文件；
- strict-success path 对每个固定文件各读取一次；
- invalid/exception path 保留 [`_card_source_ref_valid()`](../engine/f09/trace.py:453) 既有布尔短路顺序，因此 observed reads 可以是固定集合的顺序前缀；
- 不得把“所有失败路径都必须读取两个文件”写成断言；
- 任何路径均不得重试或重复调用 validator。

### AC-05：Task 6 owner 不变

以下 semantics 继续由 Task 6 独占：

- authoritative source-ref verification；
- projection graph consistency；
- malformed projection 的既有 typed exception；
- coherent invalid projection 的 [`ProjectionValidationResult`](../engine/f09/trace.py:188)；
- validator 内部 detection order；
- validator-owned issue code 与 field path。

P-1 不得复制、前移、重新命名或覆盖这些 semantics。

### AC-06：失败时不产生 authority material

任一 guard failure、validator exception、validator invalid/unexpected result，或 P-1-exclusive check failure，都必须 fail closed：

- 不返回 [`ArtifactOperationAuthority`](../engine/f09/artifacts.py)；
- 不开始 projection canonicalization；
- 不计算 artifact projection digest；
- 不构造 idempotency key；
- 不执行 write、filesystem probe 或其他 side effect。

---

## 4. 选择 A1 的理由

### 4.1 Production 事实

[`_authoritative_card_source_ref()`](../engine/f09/trace.py:421) 根据 [`engine/f09/trace.py`](../engine/f09/trace.py) 所在 repository root 定位 AC-03 两个固定文件，并使用 `Path.read_bytes()` 计算 `RAW-BYTES` SHA-256。随后 [`_card_source_ref_valid()`](../engine/f09/trace.py:453) 将 caller ref 与该 authoritative ref 作相等性比较。

因此，filesystem authority 是 validator 当前 production semantics 的组成部分，不是测试夹具偶然引入的行为。

### 4.2 与 Task 6 freeze 的兼容性

A1 保持以下 frozen surface 不变：

- [`validate_statement_projection()`](../engine/f09/trace.py:874) signature 不变；
- [`_authoritative_card_source_ref()`](../engine/f09/trace.py:421) owner 不变；
- [`_card_source_ref_valid()`](../engine/f09/trace.py:453) source authority comparison 不变；
- Task 6 的 typed exception、returned-invalid 与 detection order 不变；
- [`tests/f09/test_trace_contract.py`](../tests/f09/test_trace_contract.py) 仅作为 frozen behavior 的佐证，不被提升为 authority。

A2 则必须改变 validator authority input model 或 signature，并牵动 Task 6 production/tests。当前没有证据要求重开 Task 6；按既有 freeze 与最小变更原则，A2 对 P-1 非法。

### 4.3 最小 ownership 解释

A1 不把 filesystem authority 转移给 P-1。它只承认 builder 调用 frozen validator 时会产生一个既有、封闭、可 spy 的 transitive effect。固定文件选择、读取顺序与 equality predicate 仍完全属于 Task 6。

---

## 5. Failure precedence 唯一裁决

采用 **minimal validator-first**；完整 preflight-first 被排除。P-1 只能先做 exact top-level type guards，不得在 validator 前执行 nested shape、identity、source-ref、digest、declaration、statement member 或 card predicate。

### 5.1 唯一检测顺序

1. 按 builder signature 顺序执行六个 exact top-level type guards。
2. 六个 guards 全部成功后，以同一批对象和 refs 调用 validator 恰好一次。
3. validator 抛 typed exception时立即原样传播。
4. validator 正常返回时，先执行 exact return type guard，再执行 strict-success guard。
5. 只有 strict success 后，才执行 P-1-exclusive checks。
6. 所有 P-1-exclusive checks 成功后，才开始 artifact projection material canonicalization、digest 与 key 构造。

不得重排，不得 second validation，不得 retry，不得调用 local validator substitute。

### 5.2 Failure precedence table

| Phase | 条件 | Owner | 结果 | `issue_code` | `field_path` | Validator 调用次数 | 后续阶段 |
|---|---|---|---|---|---|---:|---|
| G1 | `package` 运行时类型不恰为预期 canonical class | P-1 | 抛 [`F09ContractError`](../engine/f09/errors.py:24) | `ARTIFACT.AUTHORITY_INVALID` | `/artifact_authority/package` | 0 | 停止 |
| G2 | `decision` 运行时类型不恰为预期 canonical class | P-1 | 抛 [`F09ContractError`](../engine/f09/errors.py:24) | `ARTIFACT.AUTHORITY_INVALID` | `/artifact_authority/decision` | 0 | 停止 |
| G3 | `trace` 运行时类型不恰为 [`TraceEnvelope`](../engine/f09/trace.py:110) | P-1 | 抛 [`F09ContractError`](../engine/f09/errors.py:24) | `ARTIFACT.AUTHORITY_INVALID` | `/artifact_authority/trace` | 0 | 停止 |
| G4 | `statement_set` 运行时类型不恰为 [`StatementSet`](../engine/f09/trace.py:173) | P-1 | 抛 [`F09ContractError`](../engine/f09/errors.py:24) | `ARTIFACT.AUTHORITY_INVALID` | `/artifact_authority/statement_set` | 0 | 停止 |
| G5 | `normative_contract_ref` 运行时类型不恰为 [`VersionedObjectRef`](../engine/f09/trace.py:52) | P-1 | 抛 [`F09ContractError`](../engine/f09/errors.py:24) | `ARTIFACT.AUTHORITY_INVALID` | `/artifact_authority/normative_contract_ref` | 0 | 停止 |
| G6 | `machine_appendix_ref` 运行时类型不恰为 [`VersionedObjectRef`](../engine/f09/trace.py:52) | P-1 | 抛 [`F09ContractError`](../engine/f09/errors.py:24) | `ARTIFACT.AUTHORITY_INVALID` | `/artifact_authority/machine_appendix_ref` | 0 | 停止 |
| V1 | validator 抛任一现有 [`F09Error`](../engine/f09/errors.py:4) | Task 6 | 同一异常对象原样传播；不包装、不改 code/path/diagnostic | validator-owned | validator-owned | 1 | 停止 |
| V2 | validator 抛非 [`F09Error`](../engine/f09/errors.py:4) 异常 | 原异常源 | 原样传播；P-1 不把未知故障伪装成 projection invalid | 原异常语义 | 原异常语义 | 1 | 停止 |
| V3 | validator 返回对象的运行时类型不恰为 [`ProjectionValidationResult`](../engine/f09/trace.py:188)，含 subclass | P-1 wrapper | 抛 [`F09IntegrityError`](../engine/f09/errors.py:21) | `ARTIFACT.PROJECTION_VALIDATION_FAILED` | `/artifact_authority/projection_validation` | 1 | 停止 |
| V4 | exact result，但 `valid is not True` | P-1 wrapper | 抛 [`F09IntegrityError`](../engine/f09/errors.py:21) | `ARTIFACT.PROJECTION_VALIDATION_FAILED` | `/artifact_authority/projection_validation` | 1 | 停止 |
| V5 | exact result，`valid is True`，但 `detected_issues != ()` | P-1 wrapper | 抛 [`F09IntegrityError`](../engine/f09/errors.py:21) | `ARTIFACT.PROJECTION_VALIDATION_FAILED` | `/artifact_authority/projection_validation` | 1 | 停止 |
| V6 | exact result 的 success fields 呈现任何不能满足 strict-success predicate 的值，包括 malformed issue collection | P-1 wrapper | 抛 [`F09IntegrityError`](../engine/f09/errors.py:21) | `ARTIFACT.PROJECTION_VALIDATION_FAILED` | `/artifact_authority/projection_validation` | 1 | 停止 |
| P1 | strict success 后某项 P-1-exclusive check 失败 | P-1 | 仅允许后续 P-1 合同为可达且非 validator-covered 的 predicate 冻结专属 typed failure | P-1-contract-owned | P-1-contract-owned | 1 | 停止 |
| C1 | strict success 且全部 P-1-exclusive checks 成功 | P-1 | 开始 canonicalization 并构造 authority | 不适用 | 不适用 | 1 | 继续 |

### 5.3 Exact top-level guard 规则

“exact”表示运行时类型 identity 必须等于合同指定 class；subclass、duck type、protocol-compatible substitute 均失败。guards 只可读取对象的运行时类型，不得解引用 nested fields。

后续 P-1 合同必须把 `package` 与 `decision` 的 exact canonical class 名称及其来源链接写全；在此之前不得实现这两个 guards。

### 5.4 Validator 调用规则

validator 调用必须满足：

- 参数 identity 与通过 guards 的六个 caller objects/refs 一致；
- positional/keyword placement 与 [`validate_statement_projection()`](../engine/f09/trace.py:874) frozen signature 一致；
- 调用恰好一次；
- 无预调用 nested validation；
- 无异常后 retry；
- 无 invalid result 后 retry；
- 无 strict success 后 second validation。

### 5.5 Typed exception propagation

validator 抛出的任何现有 [`F09Error`](../engine/f09/errors.py:4) 必须原样传播，具体包括：

- exception object identity 不变；
- exception class 不变；
- `issue_code` 不变；
- `field_path` 不变；
- `diagnostic` 不变；
- 不增加 wrapper；
- 不继续 P-1-exclusive checks。

这保留 Task 6 对 malformed graph 的既有 ownership 和 detection order。

### 5.6 Invalid result 与 unexpected return shape

以下情况全部由 P-1 wrapper 统一映射，不再承诺 builder-specific nested failures：

- exact result 且 `valid is False`；
- exact result 且 `valid` 不是 singleton `True`；
- exact result 且 issues 非空；
- exact result 但 success fields 不能满足 strict-success predicate；
- 返回 `None`、tuple、mapping、其他 object；
- 返回 [`ProjectionValidationResult`](../engine/f09/trace.py:188) subclass。

统一异常为：

- class：[`F09IntegrityError`](../engine/f09/errors.py:21)
- `issue_code`：`ARTIFACT.PROJECTION_VALIDATION_FAILED`
- `field_path`：`/artifact_authority/projection_validation`
- `diagnostic`：后续合同必须冻结一个固定、非语义、非数据派生字符串；不得包含 validator issue dump、对象 repr、路径、文件内容或其他 ambient data。

### 5.7 Validator issue preservation

当前 [`F09Error`](../engine/f09/errors.py:4) 只有 `issue_code`、`field_path` 与 `diagnostic`，没有 structured immutable details 字段。因此，本裁决禁止 P-1：

- 发明 `details` 或 `detected_issues` 属性；
- 修改 [`engine/f09/errors.py`](../engine/f09/errors.py)；
- 把 issues stringify 后塞入 `diagnostic`；
- parse、排序、去重、重写或重新拥有 validator issues。

validator returned issues 可以仅作为 builder 局部 strict-success 判定输入存在；wrapper exception 不保存其 structured copy。若未来需要 structured immutable issue preservation，必须另立公共 error-contract 前置任务，不能由 P-1 自行扩展。

### 5.8 删除不可达 builder-specific failure 承诺

后续 P-1 合同必须删除所有已经被 validator 覆盖、因 validator-first 而不可达的 builder-specific failure code/path，包括但不限于 projection graph 中的：

- case/result/track identity drift；
- trace/statement/member identity drift；
- source-ref authority drift；
- digest/shape malformed；
- declaration binding drift；
- card identity/source/evaluator-state drift；
- Task 6 已拥有的 cardinality、provenance 与 detection-order predicates。

只有能证明“validator strict success 仍不蕴含，且为 artifact authority material 所独有”的检查，才可进入 P-1 failure table。证明义务属于后续合同修订者；没有可达性证明的条目必须删除。

---

## 6. P-1-exclusive checks 的边界

后续合同必须逐项给出 P-1-exclusive predicate 的：

- consumed material；
- 为什么 validator strict success 不蕴含该 predicate；
- failure owner；
- exact typed failure；
- detection phase；
- canonicalization 是否尚未开始；
- 独立 negative evidence。

允许候选仅限 artifact authority 自身材料，例如 artifact role/schema/material completeness、projection serialization closure、artifact digest/key construction prerequisites。候选不是自动批准项；凡触及 Task 6 projection validity 的 predicate 均必须删除。

---

## 7. `FrozenDeclarationRef` 后续合同强制约束

后续对 [`plans/g6-task9p-prerequisite-authority-contract.md`](g6-task9p-prerequisite-authority-contract.md) 的有界修订必须完整冻结 [`FrozenDeclarationRef`](../engine/f09/contracts.py:492) 的 exact nested material，不得仅引用 variant 名称或写“全部字段”。

### 7.1 Exact field order

每个 [`FrozenDeclarationRef`](../engine/f09/contracts.py:492) material 必须按以下顺序显式序列化：

1. `declaration_id`
2. `declaration_type`
3. `card_id`
4. `contract_version`
5. `declaration_schema_version`
6. `content_digest`

其中 `content_digest` 必须递归展开为 [`DigestRef`](../engine/f09/contracts.py:77) exact field order：

1. `algorithm`
2. `canonicalization`
3. `value`

### 7.2 Binding variant closure

后续合同必须逐个冻结以下 closed variants 的 exact key set、field order 与 nested material：

- [`ResolvedDeclarationBinding`](../engine/f09/contracts.py:507)：其 `ref` 必须展开完整 [`FrozenDeclarationRef`](../engine/f09/contracts.py:492) material；
- [`AbsentDeclarationBinding`](../engine/f09/contracts.py:517)；
- [`NotApplicableDeclarationBinding`](../engine/f09/contracts.py:525)；
- [`UnavailableDeclarationBinding`](../engine/f09/contracts.py:533)；
- [`UnresolvableDeclarationBinding`](../engine/f09/contracts.py:546)：其 `attempted_ref` 必须展开完整 [`FrozenDeclarationRef`](../engine/f09/contracts.py:492) material。

不得使用 reflective `asdict`、开放 mapping、运行时字段枚举或“沿用 dataclass 当前字段”的隐式规则替代 exact material freeze。

---

## 8. Negative ledger 后续合同强制分类

后续 P-1 合同必须把每个 negative 条目唯一归入以下一种类别，并为每项显式定义 `seam` 与 `expected phase`。

| 分类 | 定义 | 合法 seam | Expected phase |
|---|---|---|---|
| `INPUT` | 通过 public builder surface 提交的 caller-controlled 反例 | builder public call boundary | G1–G6，或 validator strict success 后经可达性证明的 P1-exclusive phase |
| `STRUCTURAL_MUTANT` | 对 collaborator return、frozen object graph 或内部边界作定点 mutation，用于证明 fail-closed | validator seam 或明确的 P-1 helper seam | V3–V6，或已证明的 P1-exclusive phase |
| `ORACLE` | 独立重算 canonical bytes、digest、key、closed schema 或 source predicate，不能复用 production helper | test-owned independent oracle | C1 后的 material assertion；不得改变 production detection order |
| `SIDE_EFFECT` | 证明调用次数、read 集合、无 direct I/O、无 canonicalization-on-failure、无 write 等 effect boundary | spy/mock/AST 或受控 filesystem seam | 与目标 effect 最早可能出现的 phase 对齐 |

每个 ledger item 还必须包含：

- 唯一 ID；
- category；
- target predicate；
- mutation/input；
- seam；
- expected phase；
- expected owner；
- expected exception/result；
- expected issue code/path，若适用；
- validator call count；
- canonicalization call count；
- observed filesystem-read constraint，若适用。

同一条目不得同时承担 input case、structural mutant、oracle 与 side-effect probe。需要证明多个维度时必须拆成多个条目。

---

## 9. Write-set effect

选择 A1 后，P-1 implementation closed write set保持不变，仅允许：

1. [`engine/f09/artifacts.py`](../engine/f09/artifacts.py)
2. [`tests/f09/test_artifact_lifecycle.py`](../tests/f09/test_artifact_lifecycle.py)

明确禁止扩展到：

- [`engine/f09/trace.py`](../engine/f09/trace.py)
- [`engine/f09/contracts.py`](../engine/f09/contracts.py)
- [`engine/f09/errors.py`](../engine/f09/errors.py)
- [`tests/f09/test_trace_contract.py`](../tests/f09/test_trace_contract.py)
- [`plans/production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)

本 adjudication 自身的唯一写集是本文件 [`plans/g6-task9p-validator-authority-adjudication.md`](g6-task9p-validator-authority-adjudication.md)。

---

## 10. P-1 blocker reconciliation

| Rereview finding | Severity | 本裁决处理 | 状态 |
|---|---|---|---|
| validator 存在 ambient repository filesystem authority，与“builder 绝对无 I/O”冲突 | High | AC-01 至 AC-05 唯一选择 A1；把 frozen validator fixed-file reads 定义为唯一 transitive I/O 例外，同时继续禁止 builder/P-1 helper direct I/O | CLOSED BY AUTHORITY |
| validator-first 截获 malformed/identity drift，builder-specific code/path 不可达 | High | 第 5 节冻结 minimal validator-first、typed exception 原样传播、invalid/unexpected result 统一 wrapper，并要求删除 validator-covered failure 承诺 | CLOSED BY AUTHORITY |
| [`FrozenDeclarationRef`](../engine/f09/contracts.py:492) nested material 未完整冻结 | Medium | 第 7 节给出后续合同 mandatory exact material/order/variant closure | DEFERRED TO BOUNDED CONTRACT REVISION；不得跳过 |
| negative matrix 混淆 input、mutant、oracle、side-effect | Medium | 第 8 节冻结四分类及逐项 seam/phase 要求 | DEFERRED TO BOUNDED CONTRACT REVISION；不得跳过 |

两个 High blocker 已由本文件形成唯一上游 authority；两个 Medium 不阻止 adjudication Gate 为 PASS，但继续阻止未修订的 P-1 合同获得 implementation-ready 状态。

---

## 11. Gate

### Adjudication Gate：PASS

PASS 的精确定义：

- A1/A2 已唯一裁决为 A1；
- transitive I/O authority 边界已冻结；
- failure precedence 与 ownership 已唯一冻结；
- typed exception、invalid result、unexpected return shape、issue preservation、wrapper field path 与检测顺序均已裁决；
- write-set effect 已冻结；
- 两项 Medium 已转换为后续合同 mandatory constraints；
- 本文件可作为 P-1 合同修订的上游引用 authority。

PASS 明确不表示：

- P-1 prerequisite contract 已修订；
- P-1 implementation 已解锁；
- production/tests 可修改；
- Task 9-P 总 Gate 通过；
- P-2 或任何其他 prerequisite 已完成；
- 允许修改 Task 6 owner。

在后续 P-1 合同完成有界修订并通过 fresh rereview 前，P-1 implementation 仍为 **BLOCKED**。

---

## 12. 证据边界

本裁决基于静态读取，authority 与佐证边界如下：

### 12.1 Authority inputs

- 当前 P-1 prerequisite authority contract：[`plans/g6-task9p-prerequisite-authority-contract.md`](g6-task9p-prerequisite-authority-contract.md)
- Task 6 validator 与 source-ref helpers：[`engine/f09/trace.py`](../engine/f09/trace.py)
- canonical refs/declarations：[`engine/f09/contracts.py`](../engine/f09/contracts.py)
- existing error shape：[`engine/f09/errors.py`](../engine/f09/errors.py)
- P-1 future owner module与既有 I/O context：[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)
- Task 6/PI-500 freeze context：[`plans/production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)

### 12.2 Corroborating evidence only

- [`tests/f09/test_trace_contract.py`](../tests/f09/test_trace_contract.py) 只用于确认 frozen behavior、issue pair 与 detection order 的既有测试覆盖；测试不是 authority，不得由测试反向创造 production contract。

### 12.3 未执行事项

本 adjudication 不以动态执行结果作证据。编制期间不运行 Python、pytest 或 Git，不执行 GitHub mutation，不修改 production/tests/既有合同/PI-500。

### 12.4 非裁决事项

本文件不裁决：

- P-1 projection schema 的全部字段值；
- P-1-exclusive failure table 的最终条目集合；
- wrapper `diagnostic` 的最终固定字符串；
- P-2；
- Task 9-P implementation readiness。

这些事项必须在本 authority 约束下由后续 P-1 合同有界修订完成；实现者不得自行补全。

---

## 13. 后续 P-1 合同修订验收清单

- [ ] 明确引用本 adjudication 为 filesystem authority 与 failure precedence 的唯一上游来源。
- [ ] 将“builder 无 I/O”改写为“无 direct I/O，唯一允许 frozen validator transitive fixed-file reads”。
- [ ] 明确 AC-03 closed file set 与 AC-04 short-circuit-aware spy 规则。
- [ ] 冻结六个 exact top-level canonical classes、signature order、对应 field paths。
- [ ] 冻结 validator 恰好一次调用及 same-object identity。
- [ ] 冻结 typed [`F09Error`](../engine/f09/errors.py:4) 原样传播。
- [ ] 将 invalid 与 unexpected return 统一映射为 `ARTIFACT.PROJECTION_VALIDATION_FAILED` 和 `/artifact_authority/projection_validation`。
- [ ] 冻结一个固定 wrapper `diagnostic`，且不携带 validator issues 或 ambient data。
- [ ] 删除 validator-covered builder-specific nested failures。
- [ ] 对每个保留的 P-1-exclusive check 提供 strict-success 后可达性证明。
- [ ] 补齐第 7 节全部 declaration nested material。
- [ ] 按第 8 节重建 negative ledger，每项唯一 category、seam、expected phase。
- [ ] 保持 P-1 implementation closed write set不变。
- [ ] 明确 revised contract 仍需 fresh rereview，且在通过前不授权 implementation。

---

## 14. 唯一下一动作

对 [`plans/g6-task9p-prerequisite-authority-contract.md`](g6-task9p-prerequisite-authority-contract.md) 发起一个**独立、仅限合同文档的 bounded revision**：完整吸收本文件 AC-01 至 AC-06、第 5 节 failure precedence、第 7 节 declaration material 与第 8 节 negative ledger 约束；完成后提交 fresh rereview。除此之外不得开始 P-1 implementation，不得修改 production/tests/Task 6 owner/PI-500。