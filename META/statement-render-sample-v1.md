# T-157 · statement 渲染样例 v1（事实值版）

> 本样例用于验证「断语句子 = 结论模板 + 本盘 fact=value」。
> **本版是事实值，不是盘面地址**：`fact` 是 CFV 聚合代理（如 `active_path_count`、
> `pressure_signal_count`、`independent_signal_count`），不是 `four_pillars.day` 之类地址。
> 地址装配另立卡，不在 T-157 范围。
>
> 样例为回归夹具：四柱来自 `ChartFactLedger`，为稳定命中规则，部分 CFV 聚合代理按
> `tests/claims/` 既有夹具口径替换；**不是真实命盘结论，不得当作预测结果引用**。

## 1. 事业 · 段派 `career.role_change`

- 盘：`庚申 戊寅 壬子 辛丑`（乾）
- 规则：`DUAN-EVENT-CAREER-ROLE-CHANGE-V1`
- **before**（模板原文）：
  > 段派原局的财官事业结构与做功、冲动信号同向，支持一生中出现显著岗位、职责或职业角色变化。
- **after**（模板 + 本盘事实）：
  > 段派原局的财官事业结构与做功、冲动信号同向，支持一生中出现显著岗位、职责或职业角色变化。｜本盘依据：active_path_count=3；has_official=True；has_output=True；movement_structure=True；official_count=2；output_count=3

事实值可在 `applicability_snapshot` 逐项对上：`active_path_count=3`、`has_official=true`、
`has_output=true`、`movement_structure=true`、`official_count=2`、`output_count=3`。

## 2. 财富 · 高派 `wealth.debt`

- 盘：`丙午 丙午 丁巳 丙午`（乾）
- 规则：`GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1`
- **before**（模板原文）：
  > 高派结构性旁证显示债务风险与财富承压信号复合出现，但不作必然判断。
- **after**（模板 + 本盘事实）：
  > 高派结构性旁证显示债务风险与财富承压信号复合出现，但不作必然判断。｜本盘依据：pressure_signal_count=4；wealth_exposed=True

事实值可在 `applicability_snapshot` 逐项对上：`pressure_signal_count=4`、`wealth_exposed=true`。

## 3. 婚姻 · 杨派 `marriage.divorce_or_remarriage`

- 盘：`乙丑 己卯 丁酉 辛亥`（坤）
- 规则：`YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1`
- **before**（模板原文）：
  > 杨派原局至少两类独立婚姻事件信号同向，存在离婚或再婚事件风险，但不作必然判断。
- **after**（模板 + 本盘事实）：
  > 杨派原局至少两类独立婚姻事件信号同向，存在离婚或再婚事件风险，但不作必然判断。｜本盘依据：independent_signal_count=5；sex='female'；spouse_star_basis='official'

事实值可在 `applicability_snapshot` 逐项对上：`independent_signal_count=5`、`sex=female`、
`spouse_star_basis=official`。

## 格式约定

- 分隔符固定为 `｜本盘依据：`，模板在前、事实对在后。
- fact 按名称排序，保证同一输入渲染确定。
- 字符串取 `repr` 风格（单引号），浮点保留 4 位（如 `0.5000`）。
- 无任何命中事实时不静默退回模板，而是输出 `｜本盘依据：[no-fact]`。
- 本版事实值来自 runner 的求值 `context`，不改变 `matched`、`confidence`、`evidence`。
