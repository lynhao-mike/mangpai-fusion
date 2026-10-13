# Unit 9 · 真实案例核验后事业未来投影与财富弃权报告

## 1. 结论状态

- 当前 Gate：Unit9.D EVIDENCE_REVIEW / FREEZE。
- 最终裁决：`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。
- 首次完整 as-of 套件的 `BLOCKED` 结果继续作为失败历史保留，不作为最终行为 PASS 证据。
- 用户选择最小方案 A 后，仅将 Unit9 新测试改名为 [`test_unit9_real_case_future_state_projection.py`](../tests/asof/test_unit9_real_case_future_state_projection.py)；未修改既有 Unit4 测试、产品文件或测试逻辑。
- 报告更新后的逻辑 fresh STATIC_REVIEW、三条 pytest 命令和 15 文件产品三元组均取得新鲜 PASS；独立证据复核允许有界冻结。
- 状态边界：`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`。

## 2. 验证目标与范围

本 Unit 只验证既有唯一编排入口 [`run_career_session()`](../engine/asof/session_runner.py:53) 在真实案例 `C-2026-024-坤-己巳壬申辛亥壬辰`、截止日 `2025-12-31` 上，复用两个已确认事业事件后：

1. 使用真实 active state 与真实 open path 的 [`CareerFutureCandidate`](../engine/asof/future_projection.py:87) 进入事业主线，使最终状态到达 `PROJECTED`；
2. 两个 [`WealthEventBinding`](../engine/asof/future_projection.py:111) 均使用 `edges=()`，传播结果均为 `NO_EXPLICIT_EDGE`、`changed=False`，且不产生财富状态；
3. 2026–2027 待追踪内容不污染候选语义、财富绑定语义或 required IDs，同时允许候选 identity 携带真实 case ID。

冻结合同为 [`plans/as-of-life-state-unit9-real-case-future-projection-contract.md`](../plans/as-of-life-state-unit9-real-case-future-projection-contract.md)。

## 3. 授权写集与保护边界

唯一允许写入的三个当前路径：

1. [`plans/as-of-life-state-unit9-real-case-future-projection-contract.md`](../plans/as-of-life-state-unit9-real-case-future-projection-contract.md)：修订零污染范围、selector 恢复边界与 fresh review；
2. [`tests/asof/test_unit9_real_case_future_state_projection.py`](../tests/asof/test_unit9_real_case_future_state_projection.py)：保留四个 Unit9 测试逻辑，仅从旧名称本地改名以避开既有 `*future_projection.py` glob；
3. [`reports/as-of-life-state-unit9-real-case-future-projection-report.md`](as-of-life-state-unit9-real-case-future-projection-report.md)：保留失败历史并持续写入恢复证据。

保护边界：[`engine/asof/`](../engine/asof/) 全部产品文件、其他既有测试、案例输入与反馈均只读。未执行任何 Git 命令，也未执行任何 GitHub-mutating operation。改名通过本地文件系统完成，旧测试路径已不存在、当前路径存在。

## 4. 合同修订前后对比

| 项目 | 修订前 | 修订后 | 正确性影响 |
|---|---|---|---|
| 零污染检查对象 | 对完整候选与财富绑定对象执行 `repr`，因此真实 `case_id` 中合法的 `2026` 必然触发失败 | 精确限定为候选 `conclusion`、`required_active_state_ids`、`required_open_path_ids`，以及财富绑定 `event_id`、`observed_conditions`、`active_falsifiers`、`edges` | 未删除零污染检查；只排除 identity 误报，待追踪文本和 ID 仍全部禁止进入语义字段 |
| 第二次 runner 输入 | 从第一次结果的 `CareerVerificationRecord` 反推 `.verification` | 保留第一次调用使用的原始 `draft`、`verifications`、`suggestions`、`impact_adjudications`、`fundamental_adjudication` 并原样复用 | 保留第二次重投影调用，不改变产品行为要求 |
| 正例 open path | 测试默认残留旧盲稿路径 `education-to-management` | 使用真实运行值 `education-management-realized` | 收紧到真实 selector，不放宽断言 |
| 测试文件 selector | 旧名称以 `future_projection.py` 结尾，被既有 Unit4 `Path.glob("*future_projection.py")` 收集 | 用户授权后改为 [`test_unit9_real_case_future_state_projection.py`](../tests/asof/test_unit9_real_case_future_state_projection.py)，不再匹配该 glob | 只改变 Unit9 新测试文件名，不修改测试逻辑、既有测试或产品代码 |
| fresh review | 零污染修订后的旧 `PASS` 早于 selector 失败与改名 | 两轮旧 PASS 均失效；selector 修复后逻辑 fresh review 为 `PASS` | 当前 PASS 只证明合同与静态边界可执行，不证明动态行为通过 |

## 5. 冻结真实运行值与行为矩阵

Unit9 基线与专用测试实际执行所核验的值为：

```text
active_state_ids=('state:career-2014-2015-teacher-entry', 'state:career-2024-2025-school-principal')
path_states=(('education-management-realized', 'open', 'career-2024-2025-school-principal'),)
confirmed_ids=('career-2014-2015-teacher-entry', 'career-2024-2025-school-principal')
```

专用测试通过直接证明：

- 正例候选精确进入 `career_mainline`，最终状态为 `PROJECTED`；
- 财富 decision 的 event ID 顺序精确等于上述 `confirmed_ids`；
- 两条 decision 均为 `NO_EXPLICIT_EDGE`、`changed is False`、`state is None`、`edge_id is None`；
- `wealth_states == ()`；
- 未知路径反例得到 `UNKNOWN_PATH_REFERENCE`，原始 `STATE_BUILT` 结果未突变；
- 语义 payload 不含 `2026`、`2027`、`待追踪`、两条待追踪描述或 `path:unverified-2026-2027`，required IDs 只来自真实运行集合。

## 6. RED 到 GREEN 失败分类账本

| 顺序 | 事件 | 分类 | 原始结果 | 处置与证据边界 |
|---|---|---|---|---|
| 1 | 原始 Unit9 专用测试 | test defect | `CareerVerificationRecord` 无 `.verification`；完整对象 payload 污染断言失败；末行 `2 failed, 2 passed in 0.45s`，exit code 1 | 第一项改为复用第一次调用原始输入；第二项按修订合同只检查语义字段；不是产品缺陷 |
| 2 | 零污染合同范围 | contract gap | 真实 case identity 必含 `C-2026-024...`，与完整对象不得含 `2026` 不可同时满足 | 收窄检查对象而不降低语义零污染要求；旧合同 PASS 失效，新鲜复核 PASS |
| 3 | 部分补丁工具反馈 | environment/tool failure | 编辑工具报告部分 diff 无法应用，但同时报告文件已修改 | 只读重读目标文件，确认所有目标块均完整落地；该工具反馈不作为行为 PASS |
| 4 | 修复后专用测试 | GREEN | `4 passed in 0.15s`，exit code 0 | 仅证明改名前 Unit9 四个专用实例通过；改名后须重跑 |
| 5 | 首次 Unit9.C 完整 as-of 套件 | selector-collection error | 旧 Unit9 文件名命中既有 Unit4 `Path.glob("*future_projection.py")` 封闭矩阵；末行 `1 failed, 455 passed, 1 skipped, 1 warning in 2.36s`，exit code 1 | 当轮按 STOP 写入 BLOCKED；collection/selector 失败提供零完整套件行为通过证据 |
| 6 | 用户授权方案 A | bounded local repair | 只允许把 Unit9 新测试改名为不匹配 glob 的名称，保持零触碰既有文件 | 本地移动成功：旧路径不存在、当前路径存在；旧 STATIC_REVIEW 与 VERIFY 失效，等待全量新鲜复验 |

失败历史未被删除、覆盖或提升为 PASS 证据。

## 7. Unit9.C 验证证据

### 7.1 首次验证与失效证据

工作目录均为仓库根。以下是真实历史命令结果；因后续改名，均不得作为最终新鲜证据：

| 命令 | pytest 末行 | Exit code | 裁决 |
|---|---|---:|---|
| `python -m pytest tests/asof/test_unit9_real_case_future_projection.py -q`（历史旧路径） | `4 passed in 0.14s` | 0 | 历史局部 PASS / 已失效 |
| `python -m pytest tests/asof -q` | `1 failed, 455 passed, 1 skipped, 1 warning in 2.36s` | 1 | FAIL / STOP |
| `python -m pytest tests/asof/test_production_isolation.py -q` | `4 passed, 1 warning in 0.54s` | 0 | 局部 PASS |

完整套件唯一失败原文核心：

```text
test_unit4_import_boundary_paths_error_codes_and_test_matrix
Extra items in the left set:
  'tests/asof/test_unit9_real_case_future_projection.py'
```

失败位置为既有 [`test_unit4_import_boundary_paths_error_codes_and_test_matrix()`](../tests/asof/test_future_projection.py:875) 的静态文件矩阵断言。该测试对 [`engine/asof/`](../engine/asof/) 与 [`tests/asof/`](../tests/asof/) 执行 `Path.glob("*future_projection.py")`，旧 Unit9 文件名因此成为允许集合之外的第三个路径；失败与 Unit9 的具体 import 内容无关。当轮该原因虽明确，但超出原两项修复授权，故按 STOP 条件不得自行扩大范围。用户后续明确选择方案 A 后，才执行最小本地改名。

### 7.2 Selector 修复后的报告前新鲜验证

改名、合同同步和逻辑 fresh STATIC_REVIEW 完成后，从仓库根精确重跑：

| 命令 | pytest 末行 | Exit code | 裁决 |
|---|---|---:|---|
| `python -m pytest tests/asof/test_unit9_real_case_future_state_projection.py -q` | `4 passed in 0.30s` | 0 | PASS |
| `python -m pytest tests/asof -q` | `456 passed, 1 skipped, 1 warning in 4.58s` | 0 | PASS |
| `python -m pytest tests/asof/test_production_isolation.py -q` | `4 passed, 1 warning in 0.56s` | 0 | PASS |

完整套件相对 Unit9.0 基线只增加四个 Unit9 实例，未新增失败或 skipped；既有一个 skipped 的原始原因保持不变。该组结果证明 selector 改名后当前实现具备报告准入资格，但报告更新会使其不再是最终 fresh evidence，故仍须报告后精确重跑。

## 8. 产品三元组核验

RECOVER 时递归枚举 [`engine/asof/`](../engine/asof/) 的 15 个产品文件，并按相对路径、SHA-256、字节长度、UTC mtime 与合同基线逐项比较。首次报告前解析命令的正则错误导致 `AssertionError: 0`、exit code 1，归类为 environment/tool failure，提供零三元组证据；第二次逐行命令虽 exit code 0，但终端未回传预期汇总，也不提升为完整证据。第三次使用单行解析器重跑，真实可见汇总为：

```text
files=15
changed=0
verdict=PASS
changed_paths=()
exit code=0
```

因此报告前直接证明这 15 个本地产品文件与任务开始基线完全一致。该证据不证明其他路径或外部系统没有变化；报告更新后仍须再次比较，才能形成最终 fresh evidence。

## 9. 最终冻结矩阵

| 检查项 | 状态 | 证据 |
|---|---|---|
| selector 修复后合同 fresh review | PASS | 审查角色重置；当前名称不匹配既有 glob；写集与保护边界闭合 |
| 报告后 fresh STATIC_REVIEW | PASS | 旧路径不存在、新路径存在、Unit4 glob 不含新路径、AST 禁用导入为 0、当前文档引用一致；exit code 0 |
| 报告后 Unit9 专用测试 | PASS | `4 passed in 0.18s`，exit code 0 |
| 报告后完整 `tests/asof` | PASS | `456 passed, 1 skipped, 1 warning in 2.96s`，exit code 0 |
| 报告后生产隔离测试 | PASS | `4 passed, 1 warning in 5.02s`，exit code 0 |
| 报告后产品文件零变更 | PASS | files=15、changed=0、changed_paths=()、exit code 0 |
| Evidence review | PASS | 新审查角色只使用冻结合同与上述 fresh evidence；失败历史未被删除或提升 |
| Evidence-bounded freeze | PASS | 直接证明与非推断边界闭合 |

## 10. 失败与无效证据账本

- 原始 `2 failed, 2 passed` 是两个已知测试/合同缺口的有效复现，不证明产品缺陷。
- 编辑工具部分应用提示是 environment/tool failure；其后只读重读可确认文件状态，但不替代测试。
- 首次完整套件 `1 failed` 是 selector/collection error，提供零完整套件行为通过证据；它不会因后续修复而从历史中删除。
- 三元组第一次解析到 0 行和第二次无可见汇总均不是有效三元组证据；只有第三次明确输出 `files=15 / changed=0` 的结果可用。
- 报告前专用测试、完整套件、生产隔离和产品三元组均通过，但报告更新后会失去最终新鲜性，不能直接替代报告后复验。
- 产品 `changed=0` 只证明 15 个产品文件未变化，不能使行为 Gate 自动通过。

## 11. 报告后新鲜验证

本报告已包含 selector 修复、首次失败历史和报告前证据后，再次从仓库根执行最终门禁：

| 检查 | 真实末行或汇总 | Exit code |
|---|---|---:|
| 路径、Unit4 glob、AST 禁区、当前文档引用 | `STATIC_REVIEW=PASS` | 0 |
| `python -m pytest tests/asof/test_unit9_real_case_future_state_projection.py -q` | `4 passed in 0.18s` | 0 |
| `python -m pytest tests/asof -q` | `456 passed, 1 skipped, 1 warning in 2.96s` | 0 |
| `python -m pytest tests/asof/test_production_isolation.py -q` | `4 passed, 1 warning in 5.02s` | 0 |
| 产品 SHA-256、字节长度、UTC mtime | `files=15; changed=0; verdict=PASS; changed_paths=()` | 0 |

## 12. Fresh EVIDENCE_REVIEW

审查角色重置，不继承实现者、STATIC_REVIEW 或此前 BLOCKED 报告的裁决。审查输入仅为冻结合同、用户方案 A 授权、报告后 fresh STATIC_REVIEW、三条 pytest 原始末行/exit code、产品三元组汇总和完整失败账本。

审查结论：合同 fresh PASS；改名与文档同步在精确写集内；STATIC_REVIEW fresh PASS；专用行为、完整回归、生产隔离与产品零变更均 fresh PASS；唯一 skipped 与前置基线一致；首次 selector 失败和工具失败均保留且未冒充成功证据；不存在 Git/GitHub 操作证据或白名单外修复。因此 EVIDENCE_REVIEW verdict 为 `PASS`，具备有界冻结资格。

## 13. 直接证明与非推断边界

本 Unit 直接证明且仅证明：

- 对案例 `C-2026-024-坤-己巳壬申辛亥壬辰`、截止日 `2025-12-31`，真实 active state IDs、真实 open path 和两个 confirmed IDs 可使正例事业候选进入 `career_mainline`，会话达到 `PROJECTED`；
- 两个 confirmed event 的空边财富绑定均返回 `NO_EXPLICIT_EDGE`、`changed=False`，且不产生财富状态；
- 指定的 2026–2027 待追踪内容未进入候选/绑定语义字段或 required IDs，真实 case identity 中合法的 `2026` 不被误判；
- 当前 Unit9 测试文件名不再命中既有 Unit4 `*future_projection.py` 文件矩阵；
- 合同列出的 15 个本地产品文件与 Unit9.0 基线的 SHA-256、长度、UTC mtime 完全一致。

不得推断：其他案例、其他截止点或一般财富传播规则有效；2026–2027 待追踪内容具有任何真实性；生产默认行为发生变化；其他仓库路径或外部系统没有变化；本地完成等于 GitHub 同步、PR、合并、部署或发布；GitHub 全局状态未被其他主体改变。

本受控会话只能声明：未执行任何 Git 命令；未执行任何 GitHub-mutating operation；三个白名单交付路径保持本地。

## 14. 最终裁决

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

首次 `BLOCKED` 原因及命令结果已完整保留。最终冻结依据是报告更新后的新鲜静态、专用、全量、生产隔离与产品三元组证据，而不是首次失败前后的局部结果。

LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION。
