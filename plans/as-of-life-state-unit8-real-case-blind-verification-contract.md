# Unit 8 · session_runner 真实历史案例盲断验证合同

## 1. Gate 与授权边界

- Gate：Unit8.A CONTRACT。
- 目标：只验证既有 `run_career_session()` 能以真实历史案例完成“严格排盘输入 → 冻结盲断 → 开放核验 → 逐条核验 → 人工裁决 → 事业状态构建”。
- 本地写入白名单仅为：
  1. `plans/as-of-life-state-unit8-real-case-blind-verification-contract.md`；
  2. `tests/asof/test_unit8_real_case_blind_verification.py`；
  3. `reports/as-of-life-state-unit8-real-case-blind-verification-report.md`。
- 保护项：`engine/asof/**`、既有 `tests/asof/**`、`cases/**/input.md`、`cases/**/feedback.md` 均只读。
- 永久禁止：任何 Git 命令、任何 GitHub 操作、任何生产默认行为变更。
- 前置测试基线：`python -m pytest tests/asof -q` 在仓库根运行，exit code 0，`449 passed, 1 skipped, 1 warning in 2.92s`。
- 产品代码基线：任务开始时已对 `engine/asof/` 的 15 个文件逐一记录 SHA-256、长度与 UTC 最后写入时间；Unit8.C 与 Unit8.D 均须用同一方法复核。

## 2. RECOVER 基线声明

案例 `C-2026-024-坤-己巳壬申辛亥壬辰` 的四柱为己巳、壬申、辛亥、壬辰；本合同只复用既有冻结解释：原局事业节点为 `career-output`、`career-authority`、`career-support`，可行路径为 `education-to-management`，不得重解释或扩写。

冻结大运与事件窗口如下：

| 类型 | 冻结值 |
|---|---|
| 甲戌运 | `2006-01-01` 至 `2015-12-31` |
| 乙亥运 | `2016-01-01` 至 `2025-12-31` |
| 教师入职候选窗口 | `2014-01-01` 至 `2015-12-31`；回放归并日 `2015-12-31` |
| 校长升职候选窗口 | `2024-01-01` 至 `2025-12-31`；回放归并日 `2025-12-31` |
| 截止点 | `2013-12-31`、`2015-12-31`、`2025-12-31` |
| 截止点事件集合 | 依次为 `()`、仅教师入职、教师入职与校长升职 |
| 财富 | 不提供传播绑定；不得写入财富事实状态 |

窗口末日只是无精确日条件下的保守规范化边界，不得陈述为命主反馈的实际发生日。

## 3. 三个独立会话

每个截止点使用独立会话且各调用一次 `run_career_session()`：

| `as_of_date` | `session_id` | `daiyun_end` |
|---|---|---|
| `2013-12-31` | `S-20131231T000000Z-00000001` | `2015-12-31` |
| `2015-12-31` | `S-20151231T000000Z-00000002` | `2015-12-31` |
| `2025-12-31` | `S-20251231T000000Z-00000003` | `2025-12-31` |

`daiyun_end` 必须由覆盖截止日的大运阶段结束日推导，不得使用系统当前日期或自行发明日期。三次调用均显式传入 `career_candidates=None`、`wealth_bindings=None`，因此最终状态必须停在 `ConsultationState.STATE_BUILT`，`projection is None`。

## 4. 盲断草案构造冻结

新增测试模块必须定义独立函数 `_build_blind_draft(as_of_date)`。该函数只能使用案例输入中的四柱、藏干、十神、大运与既有冻结源引用，完成以下对象构造：

1. `NatalCapacityGraph`：包含三个冻结节点和 `education-to-management` 路径；
2. 两个 `DaiyunStage`：甲戌开放教育职业入口，乙亥放大既有教育输出路径；
3. 每个事件的 `AnnualInteractionTrace`；
4. 每个事件必须经 `evaluate_event_candidate()` 形成 `LifeEventCandidate`，不得直接实例化候选绕过双证据门；
5. 每个候选均冻结为 `RootLevel.STRONG_ROOT`、`CompletionMode.ACTIVATE_EXISTING`、`ExtensionBoundary.CROSS_DAIYUN_ELIGIBLE`；
6. 每个候选形成 `FrozenLandingSet` 与 `FrozenCareerEvent`；
7. 至少一个 `FrozenCareerFundamental`，其窗口不得越过相应截止日；
8. 返回 `CareerBlindDraft`。

盲稿事件集合严格为：

- `2013-12-31`：`CareerBlindDraft.events == ()`；
- `2015-12-31`：只含 `career-2014-2015-teacher-entry`；
- `2025-12-31`：依序含 `career-2014-2015-teacher-entry`、`career-2024-2025-school-principal`。

落点冻结如下，均保留替代假设和反证条件，不把反馈中的确切履历写成无替代的唯一落点：

| 事件 | center | alternative | direction | falsifier |
|---|---|---|---|---|
| 教师入职 | 教育系统内的岗位承接 | 语言与知识输出型稳定岗位 | `career_entry` | 截止窗口末仍未进入稳定职业 |
| 校长升职 | 教育系统内的管理职责提升 | 教育系统内职责扩大但职级未变 | `authority_up` | 截止窗口末职责层级未提升 |

`_build_blind_draft` 的函数体源码中不得出现：

- `feedback.md` 路径或任何含 `feedback`（大小写不敏感）的字符串/属性访问链；
- 反馈原文“入职小学语文教师，实际教英语”“升职为校长”；
- 反馈日期 `2026-05-30`；
- 从案例 `known_facts` 区域取得的字段。

盲断证据只允许引用 `input.md` 的排盘段落（四柱第 31–36 行、四柱明细第 39–75 行、大运第 79–93 行、藏干第 97–112 行）及冻结架构源引用；不得引用 `input.md` 第 145 行后的 known facts。

## 5. 严格盲排输入

新增测试必须从上述排盘字段构造 `BlindChartInput`：性别为坤，四柱及藏干为己巳（丙庚戊）、壬申（庚壬戊）、辛亥（壬甲）、壬辰（戊乙癸），长生依次为死、帝旺、沐浴、墓。大运使用输入表的连续右开区间，至少覆盖三个截止点；序号必须从 1 连续，且相邻阶段日期连续。

## 6. 后置核验构造冻结

新增测试模块必须定义独立函数 `_build_verification_from_feedback(package, as_of_date)`。反馈内容只允许在此函数内进入以下对象：

- 每个冻结事件恰有一个 `VerificationInput`，verdict 为 `CONFIRMED`，实际落点等于该事件冻结 center；
- 每个冻结事件恰有一个 `CareerImpactSuggestion`；
- 每个冻结事件恰有一个 `CareerImpactAdjudication`；
- 每个会话恰有一个 `CareerFundamentalAdjudication`。

事件后置现实值冻结如下：

| 事件 | 反馈摘录 | 影响 | 持续期 | 范围 | 状态值 | 路径变化 |
|---|---|---|---|---|---|---|
| 教师入职 | `2014-2015 年入职小学语文教师，实际教英语` | `MAJOR` | `CROSS_DAIYUN` | `PRIMARY_DOMAIN` | `入职小学教师，实际教英语` | 无 |
| 校长升职 | `2024-2025 年升职为校长` | `TURNING_POINT` | `CROSS_DAIYUN` | `PRIMARY_DOMAIN` | `升职为校长` | 打开 `education-management-realized` |

零事件截止点 `2013-12-31` 的 `verifications`、`suggestions`、`impact_adjudications` 必须均为 `()`。所有核验对象中的 freeze digest 必须来自与 runner 本次输入完全同构、同 identity 的预期冻结包；不得使用另一会话的 digest。

## 7. 调用顺序与禁止重实现

三个测试分别直接调用一次 `run_career_session()`，且仅通过其公开关键字参数传入本合同对象。测试不得自行复制 runner 内部的状态迁移、核验记录、裁决或状态构建逻辑；预计算 digest 只允许构造同构 `CareerFreezePackage` 并调用公开 canonical hash API，不得提前执行完整会话状态机。

三处调用的关键字参数集合必须严格等于：

`session_schema_version, case_id, as_of_date, session_id, blind_input, draft, verifications, suggestions, impact_adjudications, fundamental_adjudication, daiyun_end, career_candidates, wealth_bindings`。

## 8. 断言最小集

每个测试必须至少精确断言：

1. `result.final_envelope.state is ConsultationState.STATE_BUILT`；
2. `result.projection is None`；
3. `result.freeze_package.events` 的 candidate ID 序列等于该截止点冻结事件集合；
4. `result.state_result.verified_state.verified_event_ids` 精确等于该截止点冻结事件集合。

另对 `2013-12-31` 明确断言 `result.freeze_package.events == ()`，直接证明盲断草案没有未来事件，而不是运行期过滤后才隐藏。

期望 ID：

- `2013-12-31`：`()`；
- `2015-12-31`：`("career-2014-2015-teacher-entry",)`；
- `2025-12-31`：`("career-2014-2015-teacher-entry", "career-2024-2025-school-principal")`。

## 9. Unit8.B RED 冻结方式

首次新增测试必须完成 collection，并以真实断言差异失败。为避免伪造产品缺陷，RED 只允许来自新增测试 helper 尚未补齐的 2025 校长候选：首次版本的 `_build_blind_draft(date(2025, 12, 31))` 暂只返回教师入职事件，而 2025 测试仍按第 8 节精确期望两个事件。预期为 1 failed、其余截止点 passed、exit code 1，失败应位于精确事件集合断言，不得是导入、拼写、类型或 collection error。

RED 后的唯一合法实现动作：只在新增测试文件中补齐已冻结的校长候选，使 helper 满足第 4 节；不得修改产品代码或放宽断言。修复使既有 STATIC_REVIEW/VERIFY 失效，必须重新 fresh review 与 exact rerun。

若首次专用测试全部 PASS、发生 collection error，或失败不是上述真实事件集合差异，立即 STOP 并归类，不进入 Unit8.C。

## 10. STATIC_REVIEW

使用 Python `ast` 解析新增测试文件，至少检查：

1. `_build_blind_draft` 唯一定义存在；
2. 该函数体所有字符串常量、名称和属性访问链拼接后的文本中均不含大小写不敏感的 `feedback`；
3. 该函数体不含两条反馈确切结果原文与反馈日期；
4. 存在三个 `run_career_session()` 调用点；
5. 每个调用点关键字集合严格等于第 7 节集合，且 `career_candidates`、`wealth_bindings` 均为显式 `None`；
6. 测试不导入或调用 `build_verified_state`、`adjudicate_career_verifications`、`build_career_states`、`record_career_verification`；
7. `evaluate_event_candidate()` 用于构造每个事件候选；
8. 没有修改或重实现 Unit1–7 内部校验逻辑。

STATIC_REVIEW 只证明结构符合合同，不替代行为验证。

## 11. VERIFY 命令与通过标准

所有命令从仓库根 `f:/多流派新思路` 运行，记录命令、cwd、passed/failed/errors/skipped、exit code、耗时。pytest 只认 `-q` 末行 summary。

Unit8.C 依次执行：

1. `python -m pytest tests/asof/test_unit8_real_case_blind_verification.py -q`；
2. `python -m pytest tests/asof -q`；
3. `python -m pytest tests/asof/test_production_isolation.py -q`。

通过标准：

- 专用测试全部通过；
- 完整 as-of 套件相对 `449 passed, 1 skipped` 基线只增加新增测试的 passed 数，不新增失败；
- 生产隔离为 `4 passed`；
- `engine/asof/` 15 个文件的 SHA-256、长度与 UTC 最后写入时间逐项与 RECOVER 基线一致。

报告创建后，Unit8.D 必须重新执行上述三条命令与产品目录哈希检查，并只把这次新鲜结果作为最终证据。collection error 为零行为证据，立即 STOP。

## 12. STOP 条件

命中任一项立即停止并保留已有证据：

- 需要修改 `engine/asof/**`、既有 `tests/asof/**` 或案例原文；
- 首次新增测试直接全部 PASS；
- collection error、选择器扩大或环境失败；
- 完整 as-of 套件出现本任务新增测试之外的新增失败；
- 发现 runner 或依赖存在真实产品缺陷；
- 合同与权威源存在无法消解的冲突；
- 任一操作可能触达 Git 或 GitHub；
- 任一写入超出三个白名单路径。

唯一允许的失败分类：product defect、test defect、contract gap、selector/collection error、environment/tool failure、authorization-overreach risk、remote-side-effect risk。

## 13. 报告与非推断边界

最终报告必须包含：目标、写集、三个截止点、盲断/核验分离的 AST 证据、Unit8-A/B/C 原始证据、首次 RED、三个实际 verified ID 序列、产品目录零变更、新鲜 final rerun、唯一裁决与 `LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`。

即使全部通过，也不得推断：

- Unit 1–7 已全量生产就绪；
- 其他案例或其他截止点有效；
- Unit 4 未来推演有效；
- 财富传播或归档层（Unit 6）有效；
- G6/G7/G8/G9/G10 结论发生变化；
- 生产默认行为发生变化；
- GitHub 全局状态未被其他主体改变。

本受控会话只能声明：未执行任何 Git 命令；未执行任何 GitHub-mutating operation；全部产物保持本地。

## 14. 逻辑新鲜独立复核

复核角色已重置，不继承起草者结论；复核输入限定为本合同第 1–13 节、用户 Unit8 提示词、G6 第 2 节冻结规范、会话 runner 公开签名与冻结类型约束。

逐项复核：

- 案例、四柱、两段大运、两个事件窗口、三个截止点和财富弃权与权威源一致；
- 三会话 ID 合法且独立，`daiyun_end` 均来自覆盖截止日的大运结束日；
- 盲稿 helper 的输入域、防反馈泄漏与精确事件集合均已关闭选择；
- 核验 helper 是唯一反馈进入点，零事件 tuple 规则明确；
- 三处 runner 调用、最终 `STATE_BUILT`、未来输入 `None` 与精确 ID 断言已冻结；
- RED 是新增测试 helper 的受控缺口，不伪装产品缺陷，修复范围仅限新增测试文件；
- STATIC_REVIEW、三条动态验证、产品目录哈希检查、fresh rerun 与失败失效规则完整；
- 写集、STOP、Git/GitHub 禁令和 non-inference boundaries 无开放选择。

**Fresh review verdict：PASS**。

直接证据边界：合同可被机械执行，并与已读取权威源一致。禁止外推：合同 PASS 不证明实现或行为 PASS，不授权任何白名单外修改，不构成 Unit8 完成。
