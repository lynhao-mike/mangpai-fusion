# Unit 10 · 真实案例显式财富传播边合同

## 1. 目标与证据缺口

本 Unit 的唯一目标是：在真实案例 `C-2026-RF000475-坤-戊辰辛酉己巳乙丑` 的真实反馈原文上，使用既有公开接口 [`run_career_session()`](../engine/asof/session_runner.py:53)、[`CareerFutureCandidate`](../engine/asof/future_projection.py:87)、[`WealthEventBinding`](../engine/asof/future_projection.py:111)、[`project_future_from_state()`](../engine/asof/future_projection.py:249)、[`WealthPropagationEdge`](../engine/asof/wealth_propagation.py:12) 与 [`propagate_career_event_to_wealth()`](../engine/asof/wealth_propagation.py:54)，证明一条 `verified=True` 的真实来源事业→财富显式传播边可以通过正向门禁，并且在条件缺失或反证激活时拒绝传播。

真实因果依据唯一锁定为 [`feedback.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/feedback.md:34) 原文：

> 2023，因为公司没有适合人选，我被迫升岗级，换岗位，工作内容少，加了工资，配了助理

非目标：不修改任何产品代码；不把 2014/2017/2018 事件扩展为显式财富边；不验证一般财富传播规律；不改变生产默认入口；不推断反馈中不存在的制度、金额、延迟或持久期限；不执行 Git 或 GitHub 操作。

## 2. Controller 状态、授权与保护边界

### 2.1 状态表

| Unit | Goal | Depends on | Current stage | Verdict | Evidence boundary | Blocker | Next legal action |
|---|---|---|---|---|---|---|---|
| Unit10 | 真实案例显式财富传播边闭环 | Unit8/Unit9 已有公开 helper 与投影边界 | CONTRACT | 待 fresh review | 仅本合同冻结的单案、四事件与显式边 | 无 | fresh CONTRACT review |

事实源优先级：用户本轮明确决定（`USER_DECISION`）> [`AGENTS.md`](../AGENTS.md) 与 [`META/project-state.json`](../META/project-state.json)（`PROJECT_STATE`）> 只读工具输出（`TOOL_OBSERVATION`）> 明示推断（`INFERENCE`）。

### 2.2 本地授权包

- `read`：仓库入口、目标案例、`engine/asof/` 公开实现、既有 `tests/asof/` 与 Unit8/Unit9 合同/报告；目的仅为 RECOVER、设计、review 与证据核验。
- `modify`：仅以下三个路径，且只为本 Unit 合同、测试与报告：
  1. [`plans/as-of-life-state-unit10-real-case-explicit-wealth-propagation-contract.md`](as-of-life-state-unit10-real-case-explicit-wealth-propagation-contract.md)；
  2. [`tests/asof/test_unit10_real_case_explicit_wealth_propagation.py`](../tests/asof/test_unit10_real_case_explicit_wealth_propagation.py)；
  3. [`reports/as-of-life-state-unit10-real-case-explicit-wealth-propagation-report.md`](../reports/as-of-life-state-unit10-real-case-explicit-wealth-propagation-report.md)。
- `command/test`：仅本合同列出的本地静态检查、pytest 与三元组命令；工作目录固定为仓库根。
- `delete`、`local Git`、`GitHub/remote read`：未授予且本 Unit 不需要。
- `handoff write`：仅允许把 HANDOFF 记录写入上述 Unit10 报告末尾，不得修改仓库通用 handoff 或状态源。

保护项：[`engine/asof/`](../engine/asof/) 全部文件、所有既有 [`tests/asof/`](../tests/asof/) 文件、[`cases/**/input.md`](../cases/) 与 [`cases/**/feedback.md`](../cases/) 只读；禁止历史改写。任何 GitHub 服务端 mutation 永久禁止；副作用不确定即 `BLOCKED`，不测试、不申请授权。

## 3. RECOVER 基线

### 3.1 权威素材与接口事实

- [`input.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/input.md:28) 明确 `quality_grade: B`，[`input.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/input.md:30) 明确 `calibration_status: ready_for_standard_analysis`。
- 四柱为戊辰、辛酉、己巳、乙丑；2019–2029 为丁巳大运，均只从 [`input.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/input.md:40) 与 [`input.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/input.md:101) 读取。
- [`project_future_from_state()`](../engine/asof/future_projection.py:266) 要求 `wealth_bindings` 的 event IDs 按 confirmed ledger 源顺序精确全覆盖，否则返回 `WEALTH_BINDING_MISMATCH`。
- [`propagate_career_event_to_wealth()`](../engine/asof/wealth_propagation.py:66) 依次执行显式边匹配、required conditions、falsifier、source verification、edge verification 门禁；成功精确返回 `WEALTH_STATE_PROPAGATED`。

### 3.2 写入前行为基线

从仓库根运行 `python -m pytest tests/asof -q`：

```text
456 passed, 1 skipped, 1 warning in 4.75s
exit code=0
```

唯一 skipped 原因原文：

```text
SKIPPED [1] tests\asof\test_case_2022_out_of_sample.py:32: G6 evidence gate: case input has four pillars, hidden stems and luck-cycle start, but no explicit ten-god or hidden-stem ten-god fields; deriving them is forbidden
```

### 3.3 既有测试文件三元组基线

RECOVER 时只枚举 [`tests/asof/`](../tests/asof/) 顶层已有普通文件，记录相对路径、SHA-256、字节长度、UTC mtime。基线共 24 个文件；完整值来自当轮受控命令输出。最终比较规则不是要求目录完全无新增，而是：

1. 这 24 个既有路径必须全部仍存在；
2. 每个路径的 SHA-256、字节长度、UTC mtime 必须与 RECOVER 输出逐项相等；
3. 新增路径只能是 [`test_unit10_real_case_explicit_wealth_propagation.py`](../tests/asof/test_unit10_real_case_explicit_wealth_propagation.py)；
4. 输出必须为 `baseline_files=24`、`changed=0`、`missing=0`、`unexpected_new=0`。

## 4. INVENTORY

目标案例中与本 Unit 事业/财富传播相关的全部候选事件如下：

| 源顺序 | event_id | 年份 | 反馈原文摘要 | ledger 决策 | binding 决策 |
|---:|---|---:|---|---|---|
| 1 | `career-2014-liked-professional-low-pay` | 2014 | 进专业对口且喜欢的单位，但工资低 | confirmed | 精确覆盖，`edges=()` |
| 2 | `career-2017-left-for-lower-pay` | 2017 | 离职去不喜欢的单位，工资更低 | confirmed | 精确覆盖，`edges=()` |
| 3 | `career-2018-state-owned-double-pay` | 2018 | 去国企，工资翻倍 | confirmed | 精确覆盖，`edges=()` |
| 4 | `career-2023-forced-promotion-raise` | 2023 | 被迫升岗级、换岗位、加了工资、配助理 | confirmed；唯一目标 | 精确覆盖，唯一显式边 |

选择四项全部进入 confirmed ledger 的理由是：它们均位于真实反馈“已知事实年表”，且都直接描述职业状态及工资结果。此选择避免 [`WEALTH_BINDING_MISMATCH`](../engine/asof/future_projection.py:274) 漏覆盖。2014/2017/2018 的工资事实只用于核验各自事业事件，不据此新增本 Unit 范围外的显式传播边。

## 5. ADMISSION 与最小范围

唯一 admitted 目标是 2023 事件 `career-2023-forced-promotion-raise`。2014/2017/2018 仅维持 confirmed ledger 与空边 binding，复用 Unit9 已证明的 `NO_EXPLICIT_EDGE` 语义，防止范围膨胀。

四个事件按源年表顺序构造冻结候选并后置核验。测试可以复用 Unit8 已公开的冻结/核验构造模式和类型，但不得复制或重实现 [`run_career_session()`](../engine/asof/session_runner.py:53) 内部状态机。盲稿使用目标 [`input.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/input.md:40) 的真实四柱/大运作 chart evidence，落点与核验仅使用目标 [`feedback.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/feedback.md:30) 至 [`feedback.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/feedback.md:34) 的真实职业/工资措辞。

事业未来候选仅用于满足公开 runner 的未来投影入口与验证零污染边界：它只能引用运行后真实 active state IDs；`required_open_path_ids=()`，避免虚构反馈中不存在的开放路径；结论只表述“已核验职业现实状态作为后续事业推演起点”，不作具体未来预测。

## 6. 2023 真实显式财富传播边

冻结边：

```text
edge_id = real-2023-promotion-role-change-to-pay-raise
source_event_type = promotion
required_conditions = (升岗级, 换岗位, 加了工资)
target_state = 加了工资
delay_days = 0
persistence = INSTANT
falsifiers = (未加工资,)
verified = True
```

非推断说明：

- `required_conditions` 三项逐字来自 [`feedback.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/feedback.md:34)。
- `target_state="加了工资"` 直接复用原文，不改写成“稳定收入能力提高”等更强结论。
- `delay_days=0` 仅表达同一条 2023 事实记录未提供可分离延迟；不得推断具体日期。
- `Persistence.INSTANT` 是最弱持久性，不声称加薪永久持续。
- `falsifiers=("未加工资",)` 是原文条件“加了工资”的精确逻辑否定，仅用于反例门禁，不声称该反事实真实发生。

正例 2023 binding 必须精确为：

```text
observed_conditions = (升岗级, 换岗位, 加了工资)
active_falsifiers = ()
edges = (上述真实边,)
```

## 7. 精确行为断言

### 7.1 正例

经 [`run_career_session()`](../engine/asof/session_runner.py:53) 完整运行后必须断言：

1. 四个 confirmed IDs 与四个 binding IDs 按第 4 节顺序精确相等；
2. 最终 envelope 状态为 `PROJECTED`，projection 非空；
3. 事业未来候选进入 `career_mainline`；
4. 前三条 wealth decision 均为 `NO_EXPLICIT_EDGE`、`changed is False`、`state is None`、`edge_id is None`；
5. 2023 decision 为 `reason_code == "WEALTH_STATE_PROPAGATED"`、`changed is True`、`state is not None`、`edge_id is not None`，并精确等于真实 edge ID；
6. 2023 state 的 `domain == "wealth"`、`value == "加了工资"`、`source_event_id` 等于 2023 event ID、`verified is True`；
7. `wealth_states` 精确只包含该 2023 state。

### 7.2 条件缺失反例

基于同一个 `STATE_BUILT` 结果调用 [`project_future_from_state()`](../engine/asof/future_projection.py:249)，保持四项 binding 全覆盖，但 2023 `observed_conditions=("升岗级", "换岗位")`，缺少 required condition“加了工资”。必须断言 2023 decision：

- `changed is False`；
- `reason_code == "PROPAGATION_CONDITIONS_NOT_MET"`；
- `state is None`；
- `edge_id` 精确等于真实 edge ID；
- `wealth_states == ()`，原 `STATE_BUILT` 结果未突变。

### 7.3 active falsifier 反例

可额外保持完整 observed conditions，并令 `active_falsifiers=("未加工资",)`。必须精确得到 `PROPAGATION_FALSIFIED`、`changed is False`、`state is None`。此反例只证明边不是永远命中，不得冒充真实案例事实。

## 8. 未核验/待追踪内容零污染

污染检查只序列化以下语义字段：

- candidate：`conclusion`、`required_active_state_ids`、`required_open_path_ids`；
- binding：`event_id`、`observed_conditions`、`active_falsifiers`、`edges` 的 `edge_id`、`source_event_type`、`target_state`、`required_conditions`、`falsifiers`、`verified`、`delay_days`、`persistence`、`short_term_days`。

不得对包含真实 case identity 或日期的完整对象做污染检查。成功语义 payload 不得含 `待追踪`、`2024待核验`、`2025待核验`、`2026待核验`、`2027待核验`。真实边的声明性 `falsifiers=("未加工资",)` 必须保留以定义门禁，但成功 binding 的 `active_falsifiers` 必须为空；“未加工资”只允许作为边定义和独立 falsifier 反例输入，不得冒充成功路径中的已发生事实。candidate required IDs 必须只来自当轮真实运行 state/path 集合。

## 9. AST import 与 selector 边界

新增文件名固定为 [`test_unit10_real_case_explicit_wealth_propagation.py`](../tests/asof/test_unit10_real_case_explicit_wealth_propagation.py)，不得以 `future_projection.py` 结尾，因此不得命中既有 [`test_unit4_import_boundary_paths_error_codes_and_test_matrix()`](../tests/asof/test_future_projection.py:875) 的 `Path.glob("*future_projection.py")` 封闭矩阵。

新增测试顶层 import 禁止包含以下前缀：

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

测试必须 AST 解析自身顶层 import 并断言禁区为空。允许 import 目标公开 as-of 接口、基础数据类型，以及 Unit8 helper 模块中不依赖目标案例事实的公开构造类型；不得直接 import 上述禁区。

## 10. 实现与 TDD 边界

先创建测试文件并执行专用测试形成 RED；若 RED 是预期的测试构造缺口，只允许在新增测试文件内做最小修复。任何异常先归类为：`product defect`、`test defect`、`contract gap`、`selector-collection error`、`environment-tool failure`、`authorization-overreach risk`、`remote-side-effect risk`。

若真实反馈措辞不能通过现有产品校验，归类为 `product defect`，禁止修改或放宽 [`engine/asof/`](../engine/asof/)；在合同与报告记录并 STOP。测试构造错误或合同遗漏可在本 Unit 白名单内最小修复；每次修复使旧 STATIC_REVIEW 与 VERIFY 失效。

## 11. STATIC_REVIEW 清单

逻辑 fresh reviewer 只接收本合同、用户写集/保护边界、目标 input/feedback 相关行、新增测试与公开接口，重置实现者假设后检查：

1. 只有三个白名单路径被写；
2. 既有测试与产品文件未修改；
3. 四事件顺序、confirmed ledger 与 binding 全覆盖一致；
4. 2023 required conditions/target/falsifier 可追溯且没有更强推断；
5. 正例、条件缺失反例、active falsifier 反例均精确断言；
6. 零污染仅检查语义字段；
7. 文件名不命中 Unit4 glob，顶层 imports 不含禁区；
8. 静态测试实例数与预期一致；
9. 未执行或嵌入任何远程/GitHub 操作。

裁决只能是 `PASS`、`REVISE`、`BLOCKED` 或 `AUTHORIZATION_REQUIRED`。STATIC_REVIEW PASS 不证明行为 PASS。

## 12. VERIFY 命令与通过标准

从仓库根依次运行并记录 passed、failed、errors、skipped、warning、exit code 与末行原文：

1. `python -m pytest tests/asof/test_unit10_real_case_explicit_wealth_propagation.py -q`；
2. `python -m pytest tests/asof -q`；
3. `python -m pytest tests/asof/test_production_isolation.py -q`；
4. 以 RECOVER 同方法比较 24 个既有 [`tests/asof/`](../tests/asof/) 文件的相对路径、SHA-256、字节长度与 UTC mtime，并确认新增文件集合精确等于 Unit10 测试路径。

完整套件相对基线只允许增加本 Unit 新测试实例；不得新增 failed、errors 或 skipped。既有 skipped 必须仍为 1 且原因不变。warning 必须记录，不将 warning 偷换为无 warning。三元组要求 `changed=0`、`missing=0`、`unexpected_new=0`。

报告写入会使报告本身变化，但不会使测试证据失效；最终报告必须记录当轮末尾最新 VERIFY 摘要。若测试/合同在报告后再次修改，则必须重新 STATIC_REVIEW 并精确重跑受影响验证。

## 13. STOP 条件

命中任一项立即停止并精确记录：

- 任何操作可能产生 GitHub 服务端副作用；
- 需要修改 [`engine/asof/`](../engine/asof/) 才能通过；
- 需要虚构目标 [`feedback.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/feedback.md:34) 或 [`input.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/input.md:170) 不存在的事实；
- 出现 collection error，且该结果提供零行为证据；
- 完整 [`tests/asof/`](../tests/asof/) 相对基线新增失败、errors 或 skipped；
- 同一 Gate 连续两轮 `REVISE`，触发 Sub-Contract Revision Loop；循环仍不通过则上报用户；
- 任一白名单外文件被写；
- 授权越界或远程副作用风险。

## 14. EVIDENCE_REVIEW、FREEZE 与非推断边界

Fresh Evidence Reviewer 只使用冻结合同、fresh STATIC_REVIEW、完整 VERIFY ledger、失败/修复历史与三元组结果，分别判定证据有效性、当前/历史证据、动态计数与静态实例是否一致，以及结论是否越界。

全部 Gate 满足后，FREEZE 状态只能写为：

```text
PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE
```

直接证明范围仅限：目标案例四项真实反馈事件构成的 confirmed ledger；2023 “升岗级 / 换岗位 / 加了工资”显式边在完整条件下传播“加了工资”财富状态；缺条件或激活逻辑否定 falsifier 时拒绝传播；2014/2017/2018 空边弃权；指定测试与既有文件保护结果。

不得推断：其他案例、其他事件类型、一般财富规律、加薪金额、长期持续性、精确日期、生产默认行为、完整产品系统无回归、仓库外或 GitHub 全局状态。本受控会话最多声明“未执行任何 GitHub-mutating operation”，不能证明其他主体未改变 GitHub。

状态边界固定为：`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`。

## 15. HANDOFF 规则

HANDOFF 仅写入 Unit10 报告末尾，记录：Unit/Gate、最终 verdict、三个交付文件、最新有效 VERIFY 摘要、失败历史、保护边界、直接证明/不得推断、重新打开条件与唯一下一合法动作。不得修改 [`handoff.md`](../handoff.md) 或创建平行状态源。

## 16. 逻辑 fresh CONTRACT review 题目

复核者不得继承起草者结论。输入仅限第 1–15 节、用户原始任务、目标案例相关行、公开接口签名和永久 GitHub 禁令。逐项测试目标唯一性、四事件 inventory/admission、边字段追溯、binding 全覆盖、正反例、零污染、AST/文件 selector、验证命令、三元组、STOP 与非推断边界。CONTRACT PASS 只表示合同可机械执行，不证明实现或行为正确。
