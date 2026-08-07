# PI-590-R7 · G5 实施计划静态复验报告

## 1. 审查身份、范围与执行边界

本报告是一次全新、独立、角色分离的 G5 静态计划复验。审查者不继承 PI-500 编写者或 PI-570 整改者身份，也不采信 PI-570-R6/R7 record 的自述作为关闭证据；所有结论仅依据最终计划文本与 canonical contracts 的可机械定位文本。

### 1.1 审查对象

- 主审对象：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)
- Canonical 事实源：
  - [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md)
  - [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md)
  - [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md)
  - [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md)
- 前置复验基线：
  - [`production-implementation-pi-390-r4-g3-reacceptance.md`](production-implementation-pi-390-r4-g3-reacceptance.md)
  - [`production-implementation-pi-400-r4-g4-technical-rereview.md`](production-implementation-pi-400-r4-g4-technical-rereview.md)
  - [`production-implementation-pi-590-r6-g5-plan-reacceptance.md`](production-implementation-pi-590-r6-g5-plan-reacceptance.md)

### 1.2 明确未执行事项

本轮仅执行静态读取与静态文本搜索。未执行 Python、pytest、collection、任何计划代码、YAML、mapping、Git、CLI 或 PowerShell；未修改 PI-500、canonical plans、总控、handoff、META/G5 或其他文件。因此，本报告不构成实现授权、运行时验证、测试通过证明或 G5 状态更新。

### 1.3 Fail-closed 判定纪律

任一未关闭的 High、Medium、critical ambiguity、key evidence gap、canonical type conflict、frozen semantic conflict、architecture violation 或 relevant regression，均足以使最终结论为 `BLOCKED`。本轮发现一项仍可机械定位的 Medium，因此不得以其余项目关闭抵消该缺陷。

## 2. 机械证据总表

| 核验面 | Canonical / 基线要求 | PI-500 静态证据 | 结果 |
|---|---|---|---|
| `RunTrack` 所有权 | PI-210 是 sole semantic owner | PI-500 将本地声明限定为 exact runtime transcription，并要求 F09 模块导入同一运行时 identity | 关闭 |
| `RunTrack` 值域 | 恰为五值：`PRODUCTION_DEFAULT`、`PARALLEL_DOMAIN`、`STAGED_L6`、`V5_V6_PREPROD`、`MANUAL_IMPORT` | [`RunTrack`](production-implementation-pi-500-r1-f09-implementation-plan.md:101) 逐字转录五值；未发现本地 `Track` alias 或扩展值 | 关闭 |
| Request mode 映射 | `STAGED_AUDIT -> STAGED_L6`；`PREPROD_SHADOW -> V5_V6_PREPROD` | PI-500 仅给出这两条边界映射；request token 未进入 canonical typed field | 关闭 |
| Production-default request | 必须在映射/I/O 前拒绝 | 计划明确要求拒绝 production-default request，不允许借请求模式表达 canonical production track | 关闭 |
| Feedback status | first-match：`INVALID > AMBIGUOUS > UNBOUND > BOUND` | oracle 按该顺序赋值；没有 default `BOUND` | 关闭 |
| Required N/A | protocol-required 维度为 N/A 必须 `UNBOUND` | production statement-required N/A 和 preprod run-required N/A 均保留返回 binding，并断言 `UNBOUND` | 关闭 |
| Allowed N/A | 仅 protocol 明示不适用维度可为 N/A，满足时可 `BOUND` | preprod allowed-N/A fixture 断言 `BOUND` | 关闭 |
| Protocol 推导 | 必须由 pre-call canonical target facts 推导 | binder 调用不接收 fixture protocol；fixture protocol 仅在返回后作为 oracle 比较 | 关闭 |
| T72 | 恰好 old/current，无 current-like 污染 | manifest records 被限定为 `(old_record, current_record)`；测试断言长度 2、顺序、`SUPERSEDED`/`VERIFIED` | 关闭 |
| Trace shape guards | 所有索引前 fail-closed shape guard，并覆盖 malformed input | adapter 对 state/event、trace nodes、statements、card refs、evidence refs 均先检查长度；component tests 覆盖 short/empty malformed cases | 关闭 |
| Component tuple guard | 每个 tuple direct index/nullable dereference 前必须有本地 guard | 两个 `seven_matches` direct index 前缺本地 cardinality assertion | **未关闭（Medium）** |
| `DigestRef.algorithm` | 小写 `sha256` | PI-500 使用小写 token，未见大写或替代拼写 | 关闭 |
| F08/F09 边界 | F08 identity-only；F09 六维且保持 allocation-only、risk-only、strong-primary | PI-500 保留 identity-only 与六维门语义，未见扩权到 F08 决策 | 关闭 |
| State/event identity | source object 与 target identity 必须独立 | T92/T93 场景与断言保持六 event mappings 及 source/target identity 分离 | 关闭 |
| T97 | validator call 前实际改变 mapping count / external termination | T97 mutator 在 validator 前制造真实 cardinality/termination 变化 | 关闭 |
| Scope | production-default 与 F09-only | 计划未扩展到 F09 之外，也未把 request token 写入 canonical production runtime track | 关闭 |

## 3. PI-590-R6 五项 blocker closure

| # | R6 blocker | 静态复验结果 | 关闭状态 |
|---:|---|---|---|
| 1 | typed source/target track input 与 anchor 正交 | source 与 target 分别构造 typed `TrackSourceBinding`；track state 与 anchor mapped/unmapped 分开表达；missing、unparsable、ambiguous、integrity failure 不借删除 anchor 表示 | 已关闭 |
| 2 | T72 恰好 old/current，无 current-like 污染 | inspect/retry 路径均显式约束两条 records；断言 old 为 `SUPERSEDED`、current 为 `VERIFIED`，并断言 tuple 精确相等 | 已关闭 |
| 3 | 31 tests 必须多行、10/10/11、无隐藏 loop/param | 静态枚举得到 trace 10、artifact 10、feedback 11；均为独立顶层多行测试定义；未发现参数化、loop、range、generator、factory、registry 或 table parser 生成测试 | 已关闭 |
| 4 | 每个 tuple index / nullable dereference 前有本地 guard | 大多数索引已加 guard，但 feedback component test 内仍有两个 direct tuple index 缺本地长度断言，见第 7 节 | **未关闭** |
| 5 | trace adapter 所有索引前有 fail-closed shape guard，并有 malformed coverage | adapter 的相关索引前均有 shape/cardinality guard；component tests 构造 short/empty variants 并断言 typed errors | 已关闭 |

R6 五项中第 4 项仍未完全关闭。该结果独立触发 fail-closed `BLOCKED`。

## 4. R7 两项 High closure

### 4.1 High A：canonical `RunTrack`

结论：**关闭**。

机械依据：

1. PI-210 保持 semantic owner；PI-500 只声明 exact runtime transcription。
2. [`RunTrack`](production-implementation-pi-500-r1-f09-implementation-plan.md:101) 仅含五个 canonical 值，没有 `STAGED_AUDIT` 或 `PREPROD_SHADOW`。
3. 静态搜索未发现另一个 `Track` enum、local alias 或扩展 canonical track。
4. `STAGED_AUDIT` 与 `PREPROD_SHADOW` 仅作为 request/boundary token；唯一映射分别落到 `STAGED_L6` 与 `V5_V6_PREPROD`。
5. production-default request 被要求在映射及 I/O 前拒绝。
6. 计划要求各 F09 模块从同一 contracts surface 导入该 enum，并以 identity assertion 防止复制 enum 形成第二 runtime identity。

未发现 canonical typed field 接收 request token 的路径，也未发现第二运行时 enum identity。

### 4.2 High B：`FeedbackBinding.status`

结论：**关闭**。

机械依据：

1. status oracle 显式采用 first-match：`INVALID`，其次 `AMBIGUOUS`，其次 `UNBOUND`，最后仅在所有 BOUND 前提成立时赋值 `BOUND`。
2. oracle 不存在 default `BOUND`；未覆盖到前四类时抛 typed error。
3. production protocol required dimensions 与 preprod protocol required dimensions 分开列举。
4. production statement-required N/A 和 preprod run-required N/A 均实际取得至少一个 returned binding，再断言 status 为 `UNBOUND`，不是由 adapter 空返回提前绕过。
5. preprod protocol 明示不适用的 statement/revision/statement-set 维度为 N/A，并可在其余 required dimensions MATCH 时得到 `BOUND`。
6. binder 调用参数不含 fixture 的 `binding_protocol`；protocol 由调用前 statement target、run target、statement-set 与 manifest anchor 等 canonical facts 唯一决定。fixture protocol 只用于返回后的独立比较。

#### 关于 `allowed_not_applicable_satisfied = all(...)`

该表达式在当前冻结文本下不构成过度约束。PI-230 对 `BOUND` 的文字要求是：所有 protocol-required dimensions 均为 MATCH，且仅该 protocol 明示不适用的维度为 NOT_APPLICABLE。因此，对 allowed-not-applicable indexes 逐项要求 N/A 与 canonical 文字一致；当前没有证据支持这些维度在同一 protocol 下也可任选 MATCH。

## 5. 31 个 component tests 的静态计数

### 5.1 方法

本轮没有执行 collection。计数方法是对 PI-500 最终文本中的顶层多行测试定义逐项静态枚举，并按三个 component 文件区段分组；同时静态搜索参数化装饰器、循环、`range`、generator、factory、registry 与 table-parser 类生成结构。

### 5.2 结果

| Component | 独立顶层多行测试数 | 隐藏生成结构 |
|---|---:|---|
| Trace | 10 | 未发现 |
| Artifact | 10 | 未发现 |
| Feedback | 11 | 未发现 |
| **合计** | **31** | **未发现** |

该结果是计划文本的静态定义计数，不是 pytest collection 证据。

## 6. 五路 104 inventory 的静态计数

### 6.1 方法

本轮没有执行 AST、Python、collection 或 mapping。对最终计划文本采用 T01–T104 的连续编号、首尾、缺号、重复和逐项引用关系检查。连续命中在静态搜索界面可能合并为单个结果块，因此不以搜索工具显示的“结果块数量”作为 inventory 数量，而以可见的连续枚举与逐项关联为准。

### 6.2 五路结果

| Inventory | 静态证据 | 结果 |
|---|---|---:|
| Concrete mutator definitions | [`mutate_t01()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2092) 至 `mutate_t104` 连续定义 | 104 |
| Literal scenario constructors | T01 至 T104 连续 literal constructors | 104 |
| Constructor-to-mutator references | 每个 constructor 显式引用同编号 mutator | 104 |
| Constructor-to-pytest-node references | 每个 constructor 显式携带完整 pytest node | 104 |
| `SCENARIOS` tuple membership | 显式列举 T01 至 T104 | 104 |

额外交叉核验：scenario marker rows 也按 T01–T104 连续列出。该 marker 表作为第六路文本交叉证据，不替代上述五路实现 inventory。

## 7. Findings 明细

### 7.1 High

无未关闭 High。R7 的 `RunTrack` 与 FeedbackBinding status 两项 High 均有足够静态文本证据关闭。

### 7.2 Medium

#### M-1：feedback component test 的两个 tuple direct index 缺本地 cardinality guard

位置：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:2960)

可机械定位的两条表达式：

```python
assert production_required_na.seven_matches[3] == "NOT_APPLICABLE"
assert preprod_required_na.seven_matches[2] == "NOT_APPLICABLE"
```

在各自 direct index 前，计划没有本地断言对应 tuple 至少具有 4 项和 3 项。即使 fixtures 当前以七元 tuple 构造，也不能替代 R6 冻结要求的“每个 tuple index 前有本地 guard”；否则 malformed shape 会先以原生 `IndexError` 破坏 component test 的 fail-closed 可诊断性。

第 2961 行对 `[2:]` 的 slice 不会因短 tuple 产生 `IndexError`，不计为本项 direct-index blocker。

### 7.3 Critical ambiguity

无新增 critical ambiguity。

### 7.4 Key evidence gap

除 M-1 所述本地 guard 缺口外，无新增 key evidence gap。31 tests 和五路 104 inventory 结论仅限静态计划文本，不冒充 collection/runtime 证据。

### 7.5 Canonical type / frozen semantic conflict

未发现新增 canonical type conflict 或 frozen semantic conflict：

- `RunTrack` 五值及唯一 identity 保持一致；
- request mode 未污染 canonical typed fields；
- feedback first-match 与 required/allowed N/A 分界保持一致；
- `sha256` 保持小写；
- F08 identity-only、F09 六维、allocation-only、risk-only、strong-primary 未漂移；
- state/event identity 分离未漂移。

### 7.6 Relevant regression

未发现相对于 PI-390/PI-400 已冻结语义的新增 relevant regression。M-1 属于 R6 已明确要求但仍未完全关闭的 residual defect，而不是已关闭语义的重新回归。

## 8. 最小有界整改面

仅修改 PI-500 中既有 feedback component test，在两个 direct tuple index 前加入本地 cardinality assertions：

```python
assert len(production_required_na.seven_matches) >= 4
assert production_required_na.seven_matches[3] == "NOT_APPLICABLE"
assert len(preprod_required_na.seven_matches) >= 3
assert preprod_required_na.seven_matches[2] == "NOT_APPLICABLE"
```

整改边界：

- 不新增顶层测试；保持 10/10/11 与总数 31 不变；
- 不修改 canonical contracts；
- 不修改 `RunTrack`、request mapping、feedback status 或 protocol semantics；
- 不扩展 F09 scope；
- 不更新 G5；
- 整改后仍需一次新的、独立的静态复验，不能由本报告预先授予 PASS。

## 9. 唯一 Verdict

# BLOCKED

阻断理由：R6 第 4 项“每个 tuple index/nullable dereference 前有本地 guard”仍存在一项 Medium residual defect；依照 fail-closed 判定纪律，任何 Medium 均禁止输出 PASS。其余 R6 closure、R7 两项 High、31 tests、五路 104 inventory 与关键冻结语义的静态证据不能抵消该阻断项。
