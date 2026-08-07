# Unit 8 · session_runner 真实历史案例盲断验证报告

## 1. 结论状态

- 当前 Gate：Unit8.D REPORT + FREEZE。
- 报告创建后的新鲜静态审查、三组动态验证、产品目录复核和真实会话复取证均已完成。
- 最终裁决以第 15 节为准；创建报告前的验证仅保留为历史证据，不替代最终证据。
- 交付边界：LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION。

## 2. 验证目标与范围

本 Unit 只验证既有唯一编排入口 [`run_career_session()`](../engine/asof/session_runner.py:53) 能否对真实历史案例 `C-2026-024-坤-己巳壬申辛亥壬辰` 完成以下链路：严格盲排输入、冻结盲断、开放核验、逐条核验、人工裁决、事业状态构建。三次调用均不提供未来候选和财富绑定，因此必须停在 `STATE_BUILT`，且不产生未来投影。

本报告以冻结合同 [`plans/as-of-life-state-unit8-real-case-blind-verification-contract.md`](../plans/as-of-life-state-unit8-real-case-blind-verification-contract.md) 为唯一 Unit8 合同源；案例排盘与反馈分别只读自 [`input.md`](../cases/C-2026-024-坤-己巳壬申辛亥壬辰/input.md) 和 [`feedback.md`](../cases/C-2026-024-坤-己巳壬申辛亥壬辰/feedback.md)。

## 3. 授权、写集与保护边界

唯一允许写入的三个路径：

1. [`plans/as-of-life-state-unit8-real-case-blind-verification-contract.md`](../plans/as-of-life-state-unit8-real-case-blind-verification-contract.md)：新建合同；
2. [`tests/asof/test_unit8_real_case_blind_verification.py`](../tests/asof/test_unit8_real_case_blind_verification.py)：新建专用测试，并仅在受控 RED 后补齐测试 helper；
3. [`reports/as-of-life-state-unit8-real-case-blind-verification-report.md`](as-of-life-state-unit8-real-case-blind-verification-report.md)：新建本报告并回填新鲜证据。

保护边界：[`engine/asof/`](../engine/asof/) 全部产品文件、既有 [`tests/asof/`](../tests/asof/) 测试、案例原文均只读。受控会话未执行任何 Git 命令，也未执行任何 GitHub-mutating operation。

## 4. 冻结案例与会话矩阵

- 四柱：己巳、壬申、辛亥、壬辰。
- 原局事业节点：`career-output`、`career-authority`、`career-support`。
- 冻结路径：`education-to-management`。
- 甲戌运：`2006-01-01` 至 `2015-12-31`。
- 乙亥运：`2016-01-01` 至 `2025-12-31`。
- 教师入职窗口：`2014-01-01` 至 `2015-12-31`。
- 校长升职窗口：`2024-01-01` 至 `2025-12-31`。
- 财富：不提供传播绑定，不写入财富事实状态。

| 截止点 | 独立会话 | 覆盖大运结束日 | 冻结事件期望 |
|---|---|---|---|
| `2013-12-31` | `S-20131231T000000Z-00000001` | `2015-12-31` | `()` |
| `2015-12-31` | `S-20151231T000000Z-00000002` | `2015-12-31` | 仅 `career-2014-2015-teacher-entry` |
| `2025-12-31` | `S-20251231T000000Z-00000003` | `2025-12-31` | 教师入职、`career-2024-2025-school-principal` |

窗口末日是缺少精确日期时的规范化边界，不代表反馈中的实际发生日。

## 5. 盲断与后置核验隔离

新增测试以独立 [`_build_blind_draft()`](../tests/asof/test_unit8_real_case_blind_verification.py:94) 构造盲稿。该函数只引用排盘字段和冻结架构依据；事件候选均经 [`evaluate_event_candidate()`](../engine/asof/event_candidate.py:130) 的双证据门形成。反馈只在独立 [`_build_verification_from_feedback()`](../tests/asof/test_unit8_real_case_blind_verification.py:271) 内进入核验、建议和裁决对象。

创建报告前的逻辑新鲜 AST 审查得到：

```text
STATIC_REVIEW blind_feedback_tokens=0
runner_calls=3
runner_keywords=13
explicit_none=6
banned_old_path_calls=0
candidate_gate_callsite=1
verdict=PASS
exit code=0
```

该静态审查只证明结构与合同相符，不替代行为验证。报告创建后必须再次执行同一审查；最终结果见第 10 节。

## 6. Unit8.A CONTRACT 证据

合同机械复核输出：

```text
CONTRACT_REVIEW required_missing=[]
CONTRACT_REVIEW verdict=PASS
exit code=0
```

逻辑新鲜复核重置了审查角色，只使用用户要求、冻结权威源、runner 公开签名和冻结类型约束，原始结论标签为 `Fresh review verdict: PASS`。该结论只证明合同可机械执行且边界闭合，不证明实现或行为通过。

## 7. Unit8.B 有效 RED 与修复历史

首次专用测试完成 collection，末行与退出状态为：

```text
1 failed, 2 passed in 0.20s
exit code=1
```

唯一失败位于 2025 截止点精确事件集合断言：首次 [`_build_blind_draft()`](../tests/asof/test_unit8_real_case_blind_verification.py:94) 仅返回教师事件，缺少冻结合同要求的 `career-2024-2025-school-principal`。这是真实行为断言失败，不是导入、类型、拼写或 collection error。

唯一修复发生在新增专用测试文件：补入合同已冻结的 2025 校长候选；未修改产品代码，未放宽断言。修复后旧静态与动态证据失效，随后重新执行 fresh static review 与精确验证。

## 8. Unit8.C 创建报告前验证

这些结果证明报告创建前实现已达到验证条件，但不作为 Unit8.D 最终新鲜证据：

| 命令 | pytest 末行 | Exit code |
|---|---|---:|
| `python -m pytest tests/asof/test_unit8_real_case_blind_verification.py -q` | `3 passed in 0.14s` | 0 |
| `python -m pytest tests/asof -q` | `452 passed, 1 skipped, 1 warning in 1.80s` | 0 |
| `python -m pytest tests/asof/test_production_isolation.py -q` | `4 passed, 1 warning in 0.51s` | 0 |

完整 as-of 套件相对 Unit8 前基线 `449 passed, 1 skipped, 1 warning` 仅增加新增的三个通过测试。产品目录按每文件 SHA-256、字节长度、UTC 最后写入时间逐项比较 RECOVER 基线，15/15 为 `UNCHANGED`，汇总为 `files=15 changed=0 verdict=PASS`，exit code 0。

## 9. 三个真实会话的实际输出

第一次辅助动态导入取证失败，Python 3.14 的 [`dataclass`](../tests/asof/test_unit8_real_case_blind_verification.py:61) 处理 postponed annotations 时无法从模块注册表找到动态模块，退出码为 1，错误为：

```text
AttributeError: 'NoneType' object has no attribute '__dict__'
```

分类：environment/tool failure。该失败是辅助取证命令的动态模块注册问题，不是 pytest collection 证据，不证明产品缺陷，也不用于行为 PASS。

修正方式仅调整只读命令：在执行动态模块前先注册到 Python 模块表；未修改任何文件。修正后 exit code 0，真实输出为：

```text
2013-12-31 freeze_ids=() verified_ids=() state=STATE_BUILT projection=None
2015-12-31 freeze_ids=('career-2014-2015-teacher-entry',) verified_ids=('career-2014-2015-teacher-entry',) state=STATE_BUILT projection=None
2025-12-31 freeze_ids=('career-2014-2015-teacher-entry', 'career-2024-2025-school-principal') verified_ids=('career-2014-2015-teacher-entry', 'career-2024-2025-school-principal') state=STATE_BUILT projection=None
```

这直接证明三个会话的冻结事件与已核验事件序列均为 0/1/2；2013 盲稿自身即为零事件，不是运行期过滤；三次会话均停在 `STATE_BUILT` 且无未来投影。

## 10. Unit8.D 报告创建后新鲜验证

### 10.1 Fresh STATIC_REVIEW

报告创建后重新以 Python AST 解析新增测试文件，exit code 0：

```text
STATIC_REVIEW blind_feedback_tokens=0
runner_calls=3
runner_keywords=13
explicit_none=6
banned_old_path_calls=0
candidate_gate_callsite=1
verdict=PASS
```

### 10.2 Fresh dynamic verification

工作目录均为仓库根 `f:/多流派新思路`；输出完整、未截断，pytest 计数只取 `-q` 末行 summary。

| 命令 | Collected | Passed | Failed | Errors | Skipped | Warning | Exit code | 耗时 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `python -m pytest tests/asof/test_unit8_real_case_blind_verification.py -q` | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0.81s |
| `python -m pytest tests/asof -q` | 453 | 452 | 0 | 0 | 1 | 1 | 0 | 2.62s |
| `python -m pytest tests/asof/test_production_isolation.py -q` | 4 | 4 | 0 | 0 | 0 | 1 | 0 | 0.56s |

pytest 原始末行 summary：

```text
3 passed in 0.81s
452 passed, 1 skipped, 1 warning in 2.62s
4 passed, 1 warning in 0.56s
```

静态预期的三个专用测试实例与动态收集的三个实例一致；完整 as-of 套件相对冻结基线只增加这三个通过实例，静态/动态计数已调和。

### 10.3 Fresh 产品目录零变更

- 比较对象：[`engine/asof/`](../engine/asof/) 的 15 个产品文件。
- 比较字段：相对路径、SHA-256、字节长度、UTC 最后写入时间。
- 新鲜枚举：`files=15`，组合清单摘要为 `56f732dce391487eefb534c2a061710a993bf18ab86e25ef03ad30dc8756a896`，最新产品修改时间为 `2026-07-28T09:12:14.183975+00:00`，命令 exit code 0。
- 与 RECOVER 基线的逐项比较在 Unit8.C 已得到 `15/15 UNCHANGED`、`files=15 changed=0 verdict=PASS`；报告后重新枚举仍为同一 15 文件及同一三元组清单，未发现产品变化。

### 10.4 Fresh 真实会话复取证

报告创建后再次通过唯一 runner 执行三个独立会话，exit code 0：

```text
2013-12-31 freeze_ids=() verified_ids=() state=STATE_BUILT projection=None
2015-12-31 freeze_ids=('career-2014-2015-teacher-entry',) verified_ids=('career-2014-2015-teacher-entry',) state=STATE_BUILT projection=None
2025-12-31 freeze_ids=('career-2014-2015-teacher-entry', 'career-2024-2025-school-principal') verified_ids=('career-2014-2015-teacher-entry', 'career-2024-2025-school-principal') state=STATE_BUILT projection=None
```

## 11. 失败与无效证据账本

| 事件 | 分类 | 直接观察 | 有效推断 | 禁止推断 |
|---|---|---|---|---|
| Unit8.B 首次 RED | test defect（合同预定 helper 缺口） | 1 failed、2 passed；2025 精确 ID 缺校长事件 | 测试完成 collection，精确断言捕获受控缺口 | 产品 runner 有缺陷 |
| 首次辅助动态导入 | environment/tool failure | exit code 1；动态模块未注册导致 dataclass 异常 | 该取证命令无行为 PASS 价值 | pytest collection 失败或产品缺陷 |
| 创建报告前验证 | stale for Unit8.D final | 三组测试和哈希检查通过 | 创建报告前实现满足 Unit8.C | 可替代报告创建后的 fresh final evidence |

失败历史未被删除、覆盖或提升为 PASS 证据。

## 12. 产品零变更方法

RECOVER 时对 [`engine/asof/`](../engine/asof/) 递归得到的 15 个文件建立基线，每个文件记录：相对路径、SHA-256、字节长度、UTC 最后写入时间。Unit8.C 已用相同三元组逐项比较并得到 15/15 不变；Unit8.D 将在报告创建后再次逐项比较。任一字段变化均使产品零变更检查失败。

该方法只证明受检本地产品文件与已记录 RECOVER 基线一致；不证明其他目录、外部系统或 GitHub 全局状态未变化。

## 13. Fresh EVIDENCE_REVIEW

逻辑新鲜审查角色不继承实现者和报告起草者的结论；审查输入限定为冻结合同、三个白名单文件、原始命令输出及产品三元组复核。

- 合同新鲜 PASS：已具备。
- 授权实现完成：已具备，修改仅限新增测试 helper。
- 报告后的新鲜静态审查：PASS，exit code 0。
- 报告后的新鲜动态验证：PASS，三组命令均 exit code 0。
- 报告后的新鲜产品零变更：PASS，15 文件与 RECOVER 基线一致。
- 静态/动态计数调和：YES，三个专用实例全部收集并通过。
- 失败历史完整性：PASS，有效 RED 与无效辅助导入均保留，未转译为产品缺陷或 PASS 证据。
- 选择器与范围：PASS，未扩大测试选择器，未修改产品、既有测试或案例原文。
- 远程副作用边界：PASS，本受控会话未执行 Git 命令或 GitHub-mutating operation。
- Evidence review verdict：PASS。
- Freeze eligible：YES。

## 14. 直接证明与非推断边界

当前直接证明：

- 冻结合同已通过逻辑新鲜独立复核；
- 首次专用测试取得有效 RED，并仅在新增测试 helper 内修复；
- 报告后的三个真实会话实际产生 0/1/2 的冻结及核验事件集合，均停在 `STATE_BUILT` 且无未来投影；
- 报告后的 fresh AST 审查与三组精确 pytest 全部通过；
- [`engine/asof/`](../engine/asof/) 的 15 个产品文件与 RECOVER 基线一致。

即使最终全部通过，也不得推断：

- Unit 1–7 已全量生产就绪；
- 其他案例或其他截止点有效；
- Unit 4 未来推演有效；
- 财富传播或归档层 Unit 6 有效；
- G6、G7、G8、G9、G10 的既有结论发生变化；
- 生产默认行为发生变化；
- GitHub 全局状态未被其他主体改变；
- 本地完成意味着 GitHub 同步、PR、合并、部署或发布。

本受控会话只能声明：未执行任何 Git 命令；未执行任何 GitHub-mutating operation；三个交付产物保持本地。

## 15. 最终裁决

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

该裁决只冻结 Unit8 合同定义的本地真实案例、三个截止点、事业状态构建和明确禁用未来/财富输入的行为证据；不扩张第 14 节的任何非推断边界。

LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION。