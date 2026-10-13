# Unit 10 · 真实案例显式财富传播边证据有界冻结报告

## 1. 结论

**PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE**

本地状态：`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`。

本受控会话没有执行 Git、GitHub API、GitHub CLI、MCP 远程写入或其他 GitHub-mutating operation。该陈述不证明其他主体或仓库远端整体未发生变化。

## 2. 冻结目标与范围

冻结合同为 [`as-of-life-state-unit10-real-case-explicit-wealth-propagation-contract.md`](../plans/as-of-life-state-unit10-real-case-explicit-wealth-propagation-contract.md)。测试实现为 [`test_unit10_real_case_explicit_wealth_propagation.py`](../tests/asof/test_unit10_real_case_explicit_wealth_propagation.py)。

唯一目标案例为 `C-2026-RF000475-坤-戊辰辛酉己巳乙丑`。唯一因果依据是 [`feedback.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/feedback.md:34) 的 2023 原文：

> 因为公司没有适合人选，我被迫升岗级，换岗位，工作内容少，加了工资，配了助理

冻结边字段：

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

`Persistence.INSTANT` 是最弱持久性；“未加工资”是逻辑否定形式，只定义反例门禁，不声称真实发生。

## 3. 实现事实

新增测试共 5 个静态实例：

1. 真实反馈正例经完整 [`run_career_session()`](../engine/asof/session_runner.py:53) 编排；
2. 缺少“加了工资”条件的反例；
3. 激活“未加工资” falsifier 的反例；
4. 未核验内容仅针对 candidate/binding 语义字段做零污染检查；
5. AST 顶层 import 与文件名 selector 边界检查。

四项 confirmed ledger 事件按源顺序精确由 bindings 覆盖：2014、2017、2018、2023。前三项使用空边并返回 `NO_EXPLICIT_EDGE`；仅 2023 绑定真实显式边。

正例直接断言：

```text
verified_event = True（由投影入口对 confirmed ledger 事件传入）
edge.verified = True
reason_code = WEALTH_STATE_PROPAGATED
changed = True
state is not None
edge_id is not None
state.domain = wealth
state.value = 加了工资
state.verified = True
```

反例分别直接断言：

```text
PROPAGATION_CONDITIONS_NOT_MET
PROPAGATION_FALSIFIED
```

## 4. TDD 与失败历史

失败历史被保留，不以最终 GREEN 覆盖：

| 顺序 | 直接观察 | 分类 | 根因 | 最小修复 | 证据边界 |
|---:|---|---|---|---|---|
| 1 | 专用测试 `4 failed, 1 passed`；候选返回 `MISSING_PRIMARY_SOURCE_EVIDENCE` | test defect | 新测试传入空 `source_citations`，而 [`evaluate_event_candidate()`](../engine/asof/event_candidate.py:163) 要求非空 primary source citation | 仅在新增测试中加入目标 [`input.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/input.md:40) 的真实四柱与大运 citation | collection 正常，但四项行为测试尚未进入财富传播逻辑 |
| 2 | 专用测试仍为 `4 failed, 1 passed`；`turning-point suggestion requires a path change` | test defect | 新测试把 2018/2023 标为 `TURNING_POINT`，却按合同禁止虚构 open path | 仅在新增测试中降为 `ImpactLevel.MAJOR`，不虚构 path | 仍未形成财富传播 PASS 证据 |
| 3 | 修复后专用测试 `5 passed` | current behavior evidence 的前置 GREEN | 两项测试构造缺口已消除 | 无产品代码修改 | 后续仍需 fresh STATIC_REVIEW 与完整 VERIFY |
| 4 | 首次三元组脚本无输出但 exit 0 | environment/tool evidence 不完整 | Windows 终端未回显该长命令输出 | 不将其用于最终裁决，改用可回显检查 | 只证明命令进程返回 0，不证明预期计数 |
| 5 | 三元组诊断误报 24 changed | test/diagnostic defect | 手工 epoch 换算错误 | 改用 ISO 时间比较诊断 | 不证明文件真实改变 |
| 6 | SHA/字节检查误报 1 changed | baseline transcription defect | 摘要中的 `test_case_2022_out_of_sample.py` SHA 仅 62 位，不可能是合法 SHA-256；重新读取文件得到 64 位值，字节与 UTC mtime 与 RECOVER 基线一致 | 用原文件直接观测补全缺失字符后重跑 | 该误报不作为白名单外写入证据 |
| 7 | 最终三元组检查 `changed=0` | current protection evidence | 24 个既有文件 SHA-256/字节一致；UTC mtime 单独复核一致 | 无修复 | 仅覆盖合同指定 24 个既有测试文件与新增文件集合 |

所有修复都只修改本 Unit 白名单中的合同或新增测试；未修改 [`engine/asof/`](../engine/asof/) 或任何既有 [`tests/asof/`](../tests/asof/) 文件。

## 5. Fresh STATIC_REVIEW

逻辑 fresh reviewer 重置实现者假设后重新读取合同和新增测试，结果：

```text
STATIC_REVIEW=PASS
test_instances=5
forbidden_imports=[]
filename=test_unit10_real_case_explicit_wealth_propagation.py
exit code=0
```

审查确认：

- 文件名不以 `future_projection.py` 结尾，不命中 Unit4 的封闭 glob；
- 顶层 imports 不含合同禁区；
- 四事件顺序与 binding 全覆盖一致；
- 正例、条件缺失反例、falsifier 反例存在精确断言；
- 零污染检查只序列化语义字段；
- 未嵌入远程或 GitHub 操作。

STATIC_REVIEW PASS 仅证明结构与合同边界通过，不单独证明行为。

## 6. VERIFY 证据账本

工作目录均为仓库根 `f:/多流派新思路`；命令均为 local-only，未包含网络、Git 或 GitHub 副作用。

### 6.1 Unit10 专用测试

命令：

```text
python -m pytest tests/asof/test_unit10_real_case_explicit_wealth_propagation.py -q
```

结果：

```text
..... [100%]
5 passed in 0.21s
exit code=0
```

计数：collected 5、passed 5、failed 0、errors 0、skipped 0、warnings 0。静态预期 5，动态收集 5，差值 0，`Reconciled: YES`。

### 6.2 完整 `tests/asof`

命令：

```text
python -m pytest tests/asof -q
```

末行与关键输出：

```text
SKIPPED [1] tests\asof\test_case_2022_out_of_sample.py:32: G6 evidence gate: case input has four pillars, hidden stems and luck-cycle start, but no explicit ten-god or hidden-stem ten-god fields; deriving them is forbidden
461 passed, 1 skipped, 1 warning in 2.17s
exit code=0
```

计数：collected 462、passed 461、failed 0、errors 0、skipped 1、warnings 1。相对写入前基线 `456 passed, 1 skipped, 1 warning`，只增加本 Unit 的 5 个测试实例；skipped 数量与原因不变。

warning 原文为 [`pipeline_runner.py`](../engine/application/pipeline_runner.py:11) 的既有 `DeprecationWarning`，已记录，未偷换为无 warning。

### 6.3 Production isolation

命令：

```text
python -m pytest tests/asof/test_production_isolation.py -q
```

结果：

```text
.... [100%]
4 passed, 1 warning in 0.49s
exit code=0
```

计数：collected 4、passed 4、failed 0、errors 0、skipped 0、warnings 1。

### 6.4 既有测试文件三元组保护

最终可回显 SHA-256/字节检查：

```text
baseline_files=24; changed=0; missing=0; unexpected_new=0
changed_paths=[]; missing_paths=[]; unexpected_paths=[]
exit code=0
```

UTC mtime 逐项直接读取并与 RECOVER 表比较，24 项均在 Windows 文件时间显示精度内一致。新增文件集合精确为 [`test_unit10_real_case_explicit_wealth_propagation.py`](../tests/asof/test_unit10_real_case_explicit_wealth_propagation.py)。

## 7. Fresh EVIDENCE_REVIEW

逻辑 fresh Evidence Reviewer 仅使用冻结合同、fresh STATIC_REVIEW、最新 VERIFY、失败历史和三元组结果，输出：

```text
EVIDENCE_REVIEW=PASS
five_static_instances=True
positive_reason=True
condition_counterexample=True
falsifier_counterexample=True
exact_binding_coverage=True
semantic_only_payload=True
no_full_object_payload=True
source_verified=True
static_expected=5; dynamic_collected=5; difference=0; reconciled=YES
exit code=0
```

证据有效性裁决：

- CONTRACT fresh PASS：有效；
- IMPLEMENT：仅限白名单文件，产品代码与既有测试只读；
- STATIC_REVIEW fresh PASS：有效；
- 三项 pytest：均在最后一次相关代码/合同变更和 fresh STATIC_REVIEW 后执行，输出完整、exit 0；
- 三元组保护：最终计数有效；中间无输出或误报运行仅保留为历史，不用于 PASS；
- 静态/动态计数：5/5，已调和；
- Freeze eligible：`YES`。

## 8. 直接证明

当前有效证据只直接证明：

1. 目标真实案例的 2014、2017、2018、2023 四项反馈事件可构成按源顺序核验的 confirmed ledger，并由 wealth bindings 精确覆盖。
2. 基于 2023 原文“升岗级 / 换岗位 / 加了工资”的 `verified=True` 显式边，在 source event 已核验、边已核验、三个 required conditions 全满足且没有 active falsifier 时，返回 `WEALTH_STATE_PROPAGATED` 并写入值为“加了工资”的 verified wealth state。
3. 缺少“加了工资”条件时精确返回 `PROPAGATION_CONDITIONS_NOT_MET`，不写 wealth state。
4. 激活逻辑否定 falsifier“未加工资”时精确返回 `PROPAGATION_FALSIFIED`，不写 wealth state。
5. 2014、2017、2018 在没有显式边时均返回 `NO_EXPLICIT_EDGE`。
6. 本 Unit 的 5 个专用测试通过；完整 `tests/asof` 为 461 passed、1 个既有 skipped、1 个既有 warning；production isolation 为 4 passed、1 warning。
7. 合同指定的 24 个既有 `tests/asof` 文件未发生 SHA-256、字节长度或 UTC mtime 变化，且没有白名单外新增顶层测试文件。

## 9. 不得推断

本冻结不得扩展为：

- 其他案例、其他事业事件类型或一般财富传播规律；
- 加薪金额、加薪制度、长期持续性、永久收入能力或精确生效日期；
- “未加工资”在真实案例中发生过；
- 2014/2017/2018 具有本 Unit 未定义的事业→财富显式边；
- 生产默认入口已经采用该真实边；
- 完整产品系统、性能、安全、可移植性或仓库外环境均正确；
- Unit10 冻结等于整个 as-of 项目完成；
- GitHub 同步、PR、merge、部署或发布已经发生；
- 仅因本会话未执行远程 mutation 就推断 GitHub 整体完全未变。

## 10. 交付文件

1. [`as-of-life-state-unit10-real-case-explicit-wealth-propagation-contract.md`](../plans/as-of-life-state-unit10-real-case-explicit-wealth-propagation-contract.md)
2. [`test_unit10_real_case_explicit_wealth_propagation.py`](../tests/asof/test_unit10_real_case_explicit_wealth_propagation.py)
3. [`as-of-life-state-unit10-real-case-explicit-wealth-propagation-report.md`](as-of-life-state-unit10-real-case-explicit-wealth-propagation-report.md)

## 11. HANDOFF · 2026-07-28 Unit10 Evidence-Gated Handoff

### Authority and Scope

- 权威优先级：用户明确决定 > [`AGENTS.md`](../AGENTS.md) 与 [`project-state.json`](../META/project-state.json) > 工具直接观察 > 标注推断。
- 持久化目的：按用户白名单把 Unit10 冻结证据与恢复状态写入本报告末尾。
- 精确写集：上述三个交付文件；本 HANDOFF 只写本报告。
- 保护项：[`engine/asof/`](../engine/asof/)、既有 [`tests/asof/`](../tests/asof/)、案例 input/feedback 全部只读。
- GitHub service-side mutation：永久禁止。

### Bounded Status

- Unit：Unit10 · 真实案例显式财富传播边闭环。
- Current stage：`HANDOFF`。
- Final verdict：`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。
- 直接证明与不得推断：见本报告第 8、9 节。
- Remote publication：`LOCAL ONLY / NOT PUSHED`。

### Evidence Chain

- CONTRACT fresh review：PASS。
- IMPLEMENT：完成；仅白名单内最小测试/合同修复。
- STATIC_REVIEW：PASS，5 个静态实例、0 forbidden imports。
- VERIFY：专用 `5 passed`；完整 `461 passed, 1 skipped, 1 warning`；production isolation `4 passed, 1 warning`；三元组 `24/0/0/0`。
- Failure/repair history：完整保留于第 4 节。
- EVIDENCE_REVIEW：PASS；静态/动态 `5/5`，Freeze eligible `YES`。

### Controller State

| Unit | Goal | Current stage | Verdict | Blocker | Next legal action |
|---|---|---|---|---|---|
| Unit10 | 真实案例显式财富传播边闭环 | HANDOFF persisted | PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE | 无 | 保持冻结；仅在 reopening condition 命中时重开 |

### Current Stop Point

- 最后完成的合法动作：把冻结报告和 HANDOFF 持久化到本 Unit 白名单报告。
- 停止原因：Unit10 的证据门禁与治理闭环已完成；无权自动开始其他 Unit。
- Open blocker：无。
- Local Git identifiers：无；本受控会话未执行 Git 操作。
- GitHub actions performed by this controlled session：无 GitHub-mutating operation。

### Reopening Conditions

仅在以下任一条件出现时重开 Unit10：

1. 三个交付文件之一被修改；
2. 目标 [`feedback.md`](../cases/C-2026-RF000475-坤-戊辰辛酉己巳乙丑/feedback.md:34) 或相关公开接口发生变化；
3. 指定测试或完整 `tests/asof` 出现新增失败、error 或 skipped；
4. 既有 24 文件保护账本出现变化；
5. 发现当前直接证明或非推断边界有证据错误。

### Unique Next Legal Action

**保持 Unit10 本地证据有界冻结，不执行任何后续实现、Git、GitHub、部署或远程同步操作。** 新工作必须由新的明确目标与独立 Gate 链启动；本 HANDOFF 不授予该权限。
