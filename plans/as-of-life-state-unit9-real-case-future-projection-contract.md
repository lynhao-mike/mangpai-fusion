# Unit 9 · 真实案例核验后事业未来投影与财富弃权合同

## 1. 目标与非目标

本 Unit 只验证既有唯一编排入口 [`run_career_session()`](../engine/asof/session_runner.py:53) 在真实案例 `C-2026-024-坤-己巳壬申辛亥壬辰`、截止日 `2025-12-31` 上，复用 Unit8 已冻结并核验的两个事件，补入事业未来候选与财富绑定后满足：

1. 至少一个 [`CareerFutureCandidate`](../engine/asof/future_projection.py:87) 以 Unit9.0 真实运行产生的 active state ID 和 open path ID 为前置条件，被选入 `career_mainline`，最终会话状态为 `PROJECTED`；
2. 两个 [`WealthEventBinding`](../engine/asof/future_projection.py:111) 按 confirmed ledger 顺序精确覆盖两个已核验事件，均使用 `edges=()`；两次财富传播均返回 `NO_EXPLICIT_EDGE`、`changed is False`，且不产生财富事实状态；
3. 2026–2027 待追踪条目不进入任何事业候选、财富绑定、required active state ID 或 required open path ID。

非目标：不伪造 [`WealthPropagationEdge`](../engine/asof/wealth_propagation.py:12)；不验证其他案例；不扩展条件分支准入；不修改 [`engine/asof/`](../engine/asof/)；不把结果外推为生产默认行为变化。

## 2. 授权、写集与保护边界

仅允许创建或修改以下三个本地文件：

1. [`plans/as-of-life-state-unit9-real-case-future-projection-contract.md`](as-of-life-state-unit9-real-case-future-projection-contract.md)；
2. [`tests/asof/test_unit9_real_case_future_state_projection.py`](../tests/asof/test_unit9_real_case_future_state_projection.py)；
3. [`reports/as-of-life-state-unit9-real-case-future-projection-report.md`](../reports/as-of-life-state-unit9-real-case-future-projection-report.md)。

保护项：[`engine/asof/`](../engine/asof/) 全部文件、既有 [`tests/asof/`](../tests/asof/) 文件、[`cases/**/input.md`](../cases/) 与 [`cases/**/feedback.md`](../cases/) 全部只读。禁止任何 Git 命令和任何 GitHub 操作；禁止放宽正确性要求。修复只能调整本合同中的断言范围说明，以及新增测试文件中的原始输入复用方式和零污染断言范围；不得删除零污染检查或重投影调用。完整套件首次发现新增测试旧名称命中既有 Unit4 `*future_projection.py` 文件矩阵后，用户明确追加最小授权：仅把该 Unit9 新测试本地改名为不匹配该 glob 的当前名称，并同步本合同与 Unit9 报告引用；仍不得修改既有测试或产品文件。任何失败必须先归类为 product defect、test defect、contract gap、selector/collection error 或 environment/tool failure。

## 3. Unit9.0 真实运行基线

### 3.1 公开接口与错误码

[`run_career_session()`](../engine/asof/session_runner.py:53) 的未来参数为 `career_candidates: tuple[CareerFutureCandidate, ...] | None = None` 与 `wealth_bindings: tuple[WealthEventBinding, ...] | None = None`。只要任一不为 `None`，即委托 [`project_future_from_state()`](../engine/asof/future_projection.py:249)。

[`FutureProjectionError.CODES`](../engine/asof/future_projection.py:21) 的完整值为：`INVALID_TYPE`、`INVALID_VALUE`、`UNKNOWN_FIELD`、`INVALID_STATE`、`DUPLICATE_ID`、`IDENTITY_MISMATCH`、`LEDGER_MISMATCH`、`STATE_MISMATCH`、`HYPOTHESIS_MISMATCH`、`AMBIGUOUS_PATH_STATE`、`UNKNOWN_STATE_REFERENCE`、`UNKNOWN_PATH_REFERENCE`、`WEALTH_BINDING_MISMATCH`。

### 3.2 只读诊断真实输出

动态加载 Unit8 helper，并以 Unit8 的 `2025-12-31` 用例同构参数调用一次 runner、显式传入 `career_candidates=None` 与 `wealth_bindings=None`。首次诊断因命令从动态模块错误读取未导入的 `VerificationStatus` 而 exit code 1，归类为 environment/tool failure；它已打印前两组值但不作为完整证据。仅修正命令导入后重跑，exit code 0，完整原始值为：

```text
active_state_ids= ('state:career-2014-2015-teacher-entry', 'state:career-2024-2025-school-principal')
path_states= (('education-management-realized', 'open', 'career-2024-2025-school-principal'),)
confirmed_ids= ('career-2014-2015-teacher-entry', 'career-2024-2025-school-principal')
```

这些值是后续输入的唯一 ID 依据。旧盲稿中的 `education-to-management` 不是该真实运行结果的 open path ID，不得成为最终通过版本的 required path。

### 3.3 前置测试与产品三元组基线

`python -m pytest tests/asof -q`：`452 passed, 1 skipped, 1 warning in 2.52s`，exit code 0。

Unit9.0 以相对路径、SHA-256、字节长度、UTC mtime 建立 15 文件基线：

| 文件 | SHA-256 | 长度 | UTC mtime |
|---|---|---:|---|
| `engine/asof/__init__.py` | `e823e161de220edd62978ef6fb445d2fd39f4f064408002ae1d38fb3ed09ed3a` | 644 | `2026-07-26T09:27:31.732289+00:00` |
| `engine/asof/archive_integration.py` | `83fe08691df269a6209fecd3b85cc6b70dff8336d28f8b96e79e468c89e82899` | 9337 | `2026-07-28T08:13:09.620864+00:00` |
| `engine/asof/career_state_builder.py` | `790c07f28786d934a726a813de326f5aafcedf162b75e2306b74d592b9c92918` | 33251 | `2026-07-27T17:14:56.397113+00:00` |
| `engine/asof/consultation_freeze.py` | `12f82f56aa1b04e1af68a8e664dceee10b2bb21610f31051dc64fbc09aecfd27` | 34351 | `2026-07-27T15:49:19.225761+00:00` |
| `engine/asof/daiyun_context.py` | `a78e3c8a5e85c272de18ed4025b71cdb8139120b285646961a8ed0d6796932ca` | 5882 | `2026-07-26T09:27:18.858439+00:00` |
| `engine/asof/event_candidate.py` | `ba7a7cb26ab65f277db7e8a0514264c73b779c7aaf0cf4270512caf581d7ef65` | 7562 | `2026-07-26T09:30:55.887258+00:00` |
| `engine/asof/future_projection.py` | `9b265b6821a79712efdb16c081d48da881138b8dc819d65b290b6b14f6e72311` | 14391 | `2026-07-28T00:11:02.953043+00:00` |
| `engine/asof/natal_capacity.py` | `bb7af611c90545f8870305a1b58388b0375c20284b5bd8584822a3fbfb736c6f` | 4945 | `2026-07-26T09:26:39.843486+00:00` |
| `engine/asof/reality_track.py` | `74d68985e8a37922565e59922f05c4bb08e45b51fa493135eb923a13c7581de7` | 3138 | `2026-07-26T09:33:25.701805+00:00` |
| `engine/asof/reality_translation.py` | `08f5b55ecff673e87ff8fc8dd6fc054b211b3f27473f3468c3f52f6f132bdf8d` | 6464 | `2026-07-26T09:44:23.133493+00:00` |
| `engine/asof/session_contract.py` | `1e2d67b09b20548c9ad728fb52e8ae9810844118dc2320e5b9412410573ae33e` | 15404 | `2026-07-27T14:54:08.393389+00:00` |
| `engine/asof/session_runner.py` | `d076bd76d235e92f22f741178a3966513b5f6291745e9d431ad4fe20419cc08c` | 3626 | `2026-07-28T09:12:14.183975+00:00` |
| `engine/asof/state_ledger.py` | `ea44d41939c0a64f168b516f0bfdbf29816663ab6289cfc4db5b1eaccd3861a0` | 9587 | `2026-07-26T09:34:39.773892+00:00` |
| `engine/asof/structural_track.py` | `01ce342e4921b133c7c95600a5a44f5a8cbe6edce93ae952270a307f0d0008b9` | 1719 | `2026-07-26T09:32:56.278172+00:00` |
| `engine/asof/wealth_propagation.py` | `6f4c56204e4fb4eab06b2efbe0f4f17e86875e703b1555b4bb4e4e5604d00aef` | 3740 | `2026-07-26T09:43:36.123154+00:00` |

## 4. 冻结输入构造

测试复用 Unit8 的 [`_blind_input()`](../tests/asof/test_unit8_real_case_blind_verification.py:75)、[`_build_blind_draft()`](../tests/asof/test_unit8_real_case_blind_verification.py:94)、[`_expected_package()`](../tests/asof/test_unit8_real_case_blind_verification.py:260) 与 [`_build_verification_from_feedback()`](../tests/asof/test_unit8_real_case_blind_verification.py:271)，使用：

- `as_of_date=date(2025, 12, 31)`；
- `session_id="S-20251231T000000Z-00000009"`；
- `daiyun_end=date(2025, 12, 31)`；
- 两个确认事件及顺序严格等于第 3.2 节 `confirmed_ids`。

### 4.1 正例事业候选

冻结一个候选：

- `candidate_id="career-future-education-management-continuity"`；
- `required_active_state_ids=("state:career-2024-2025-school-principal",)`；
- `required_open_path_ids=("education-management-realized",)`；
- identity 与案例、截止日完全一致。

以上 state 与 path 均来自第 3.2 节真实值；path 的真实 status 为 `open`，故候选必须进入 `career_mainline`。

### 4.2 反例事业候选

真实 `path_states` 没有 closed/reduced 路径，因此不得伪造一个 closed path。独立反例候选冻结为：

- `candidate_id="career-future-unverified-2026-2027"`；
- active state 使用真实值；
- `required_open_path_ids=("path:unverified-2026-2027",)`，这是明确不存在于第 3.2 节的路径。

独立调用 [`project_future_from_state()`](../engine/asof/future_projection.py:249) 时必须抛出 `FutureProjectionError` 且 `code == "UNKNOWN_PATH_REFERENCE"`。成功投影调用不得传入此反例，并显式断言成功结果的 `career_mainline` 不含该 ID。

### 4.3 财富绑定

按 `confirmed_ids` 顺序严格构造：

1. `WealthEventBinding(event_id="career-2014-2015-teacher-entry", observed_conditions=(), active_falsifiers=(), edges=())`；
2. `WealthEventBinding(event_id="career-2024-2025-school-principal", observed_conditions=(), active_falsifiers=(), edges=())`。

不得构造任何显式财富边。空边依据 [`propagate_career_event_to_wealth()`](../engine/asof/wealth_propagation.py:54) 必须返回 `NO_EXPLICIT_EDGE`。

## 5. 精确断言清单

成功投影测试必须断言：

1. `result.final_envelope.state is ConsultationState.PROJECTED`；
2. `result.projection is not None`；
3. `career_mainline` 非空，精确等于正例候选 tuple，并不含反例候选 ID；
4. `wealth_decisions` 的 event ID 顺序精确等于 `confirmed_ids`；
5. 两条 decision 均 `reason_code == "NO_EXPLICIT_EDGE"`、`changed is False`、`state is None`、`edge_id is None`；
6. `wealth_states == ()`。

独立反例测试必须断言未知 path 触发 `UNKNOWN_PATH_REFERENCE`，且原始 `STATE_BUILT` 结果未突变。

## 6. 未核验候选零污染

案例反馈中的 `2026` 与 `2027` 两行均为“待追踪”，不得当作现实事实。测试必须专门检查事业候选与财富绑定的**语义字段**，不得检查包含 identity 的完整候选对象 `repr`。候选 identity 必须继续携带真实 `case_id="C-2026-024-坤-己巳壬申辛亥壬辰"` 与截止日；identity 中合法出现的 `2026` 不属于语义污染。

零污染序列化范围精确限定为：候选的 `conclusion`、`required_active_state_ids`、`required_open_path_ids`，以及财富绑定的 `event_id`、`observed_conditions`、`active_falsifiers`、`edges`。该语义 payload：

- 不含 `2026`、`2027`、`待追踪`；
- 不含“事业身份、关系名分、职位规则强化”；
- 不含“现实责任、家庭资产、长期规划压力增加”；
- 不含 `path:unverified-2026-2027` 于成功输入；
- 所有 `required_active_state_ids` 和 `required_open_path_ids` 都只来自第 3.2 节真实运行集合。

反例测试仅用不存在 ID 验证 selector 拒绝，不得将其加入成功输入或作为事实/候选依据。此范围修订只排除非语义 identity 的误报，不删除零污染检查，也不允许任何待追踪文本或 ID 进入上述语义字段。

## 7. Fresh AST 边界

新增测试文件不得直接 import 以下前缀：

```text
engine.pipeline
engine.v5.runner
engine.v5.preprod
tools.render_report
tools.feedback
engine.asof.natal_capacity
engine.asof.structural_track
engine.asof.daiyun_context
```

AST 测试必须枚举新增测试文件顶层 imports 并断言无禁用前缀；该清单对齐 [`test_unit4_import_boundary_paths_error_codes_and_test_matrix()`](../tests/asof/test_future_projection.py:875)。测试允许 import Unit8 测试模块以复用已冻结 helper，但不得复制或重实现 runner 内部状态机。

## 8. TDD RED 与缺口修复边界

首次新增测试的历史 RED 已完成 collection；随后当前实跑为 `2 failed, 2 passed`。两个失败必须分别保留分类：第二次 runner 调用从 `CareerVerificationRecord` 读取不存在的 `.verification`，属于 test defect；零污染检查序列化完整候选 identity，因真实 `case_id` 合法包含 `2026` 而失败，根因是 contract gap，落地表现为 test defect。两者均不是产品缺陷，也不是 collection error。

唯一合法逻辑修复为：保留第一次 runner 调用所使用的原始 `draft`、`verifications`、`suggestions`、`impact_adjudications` 与 `fundamental_adjudication` 并在第二次调用原样复用；按第 6 节只序列化语义字段做零污染断言；正例 required path 使用第 3.2 节真实值 `education-management-realized`。不得删除第二次投影调用、零污染断言或任何正确性要求，不得修改产品代码。

逻辑修复后专用测试为 `4 passed`，但首次完整套件为 `1 failed, 455 passed, 1 skipped, 1 warning`：既有 [`test_unit4_import_boundary_paths_error_codes_and_test_matrix()`](../tests/asof/test_future_projection.py:875) 用 `Path.glob("*future_projection.py")` 建立封闭文件矩阵，旧名称 `test_unit9_real_case_future_projection.py` 被额外收集。该结果归类为 selector/collection error，提供零完整套件行为通过证据；当轮依原 STOP 条件写入 BLOCKED 报告。随后用户明确选择最小修复方案 A：仅将 Unit9 新测试改为当前名称 `test_unit9_real_case_future_state_projection.py`，使其不匹配该 glob；不得修改既有 Unit4 测试、产品代码或测试逻辑。改名使旧 STATIC_REVIEW 与 VERIFY 全部失效，必须重新执行逻辑 fresh review 与完整门禁。

## 9. 验证命令与通过标准

所有命令从仓库根运行，记录 passed、failed、errors、skipped、warning、exit code 与 pytest 末行：

1. `python -m pytest tests/asof/test_unit9_real_case_future_state_projection.py -q`；
2. `python -m pytest tests/asof -q`；
3. `python -m pytest tests/asof/test_production_isolation.py -q`。

第 3 条原样复用 Unit8 合同的生产隔离命令。完整套件相对 `452 passed, 1 skipped` 前置基线只允许增加 Unit9 新增测试实例，不得新增失败或 skipped。随后以第 3.3 节完全相同的相对路径、SHA-256、长度、UTC mtime 方法逐项比对 15 文件，要求 `changed=0`。

报告创建后必须再次执行以上三条命令、AST 检查和产品三元组比对，并只用报告创建后的新鲜结果作最终证据。

## 10. STOP 与失败失效规则

命中以下任一项立即 STOP：任何操作可能产生 GitHub 服务端副作用；只读诊断无法在只读范围内修复；需要修改 [`engine/asof/`](../engine/asof/)；需要把 2026–2027 待追踪条目作为事实才能选中候选；collection error；完整套件出现新增失败；连续两轮 CONTRACT fresh review 均为 REVISE；任何白名单外写入。

任一修复使旧 STATIC_REVIEW 与 VERIFY 失效，必须 fresh review 并精确重跑。collection error 提供零行为证据。

## 11. Fresh review 角色重置与问题

复核者不得继承起草者结论。复核输入仅限本合同第 1–10 节、[`run_career_session()`](../engine/asof/session_runner.py:53) 与 [`project_future_from_state()`](../engine/asof/future_projection.py:249) 的公开签名、Unit9.0 第 3.2 节真实输出、用户授权边界与永久 Git/GitHub 禁令。

复核问题：目标/非目标、写集、真实 selector、成功与反例输入、财富空边、精确断言、待追踪零污染、AST 禁区、RED 修复范围、验证选择器和 STOP 条件是否闭合且无开放选择。复核只能给出 `PASS` 或 `REVISE`；CONTRACT PASS 不证明实现或行为 PASS。

## 12. 直接证明与非推断边界

即使全部测试通过，也只直接证明本案例、该截止日、这两个确认事件、该真实事业 state/path 输入和财富无边弃权行为。不得推断：其他案例有效；生产默认行为变化；财富传播规则本身普遍正确；2026–2027 后续事件具有任何真实性；本地完成等于 GitHub 同步；GitHub 全局状态未被其他主体改变。

状态边界固定为：`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`。

## 13. Unit9.A 旧复核失效记录

原 Fresh review `PASS` 基于“完整候选对象序列化后不得包含 `2026`”和“RED 后只能修正 required path”的旧合同，无法同时容纳真实 case identity 与已复现的第二次 runner 参数构造缺口，自本轮合同修订起失效，不得作为 Unit9.A 当前证据。

## 14. Unit9.A 修订后逻辑新鲜独立复核（已失效）

该轮复核曾确认真实 selector、正反例、财富空边、零污染语义范围、第二次 runner 原始输入复用、AST 禁区、三条验证命令、产品三元组、STOP 与非推断边界闭合，并给出 `PASS`。但它早于首次完整套件 selector/collection error 与测试文件改名，自改名及本合同同步修订起失效，不得作为当前 CONTRACT 或 STATIC_REVIEW 证据。

## 15. Selector 修复后逻辑新鲜独立复核

新审查角色重置，不继承起草者、旧复核者或首次 BLOCKED 报告结论。复核输入限于本合同第 1–13 节、用户对方案 A 的明确授权、改名后的 Unit9 测试、既有 Unit4 文件矩阵断言、公开投影签名、Unit9.0 真实值与永久 Git/GitHub 禁令。

逐项核对结果：当前 Unit9 测试路径不再匹配既有 `*future_projection.py` glob；写集仍只有合同、Unit9 新测试与 Unit9 报告；既有测试和产品文件仍受保护；改名未改变四个 Unit9 测试的输入、断言或导入边界；三条验证命令已指向当前路径；首次 selector/collection error 及证据失效规则被完整保留；真实 selector、正反例、财富空边、零污染、产品三元组、STOP 和非推断边界均无开放选择。

**Fresh review verdict：PASS**。

该 PASS 仅证明修订后合同和静态边界可机械执行，不证明动态验证或最终冻结 PASS。
