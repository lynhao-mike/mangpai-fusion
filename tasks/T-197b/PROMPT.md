# T-197b · P0 A 档自动落定 + 6 题回收

- 状态：🔵 Ready（等 6 个事实答案）
- 依据：T-197 4 卡/12 候选；A 3 / B1 8 / C 1
- 前置：`META/p0-cards-v1.json`

## 0. 一句话

A 档 3 条由引擎确定性落定（`engine_fixed`，不需要人）；6 个 B1 事实题由人类/命主回答 yes/no/unknown，
按 `elimination` 机械淘汰；答不出→`needs_anchor`；C 档保持留白。**人不选方向。**

## 1. A 档（3 条，P0-04）

- `selected_option` = 固定类候选；`decision_by=engine_fixed`；`selection_source=agent_auto`；`pending=none`；
- 只对 `direction_tier=A` 且 `provenance=engine_fixed` 生效；B/C 不动。

## 2. 6 题回收

| # | 例 | 题 | yes | no | unknown |
|---|---|---|---|---|---|
| 1 | P0-01 | AQ1 父母/兄弟/原生家庭介入施压 | keep dc1 / elim dc2 | keep dc2 / elim dc1 | 全 elim → needs_anchor |
| 2 | P0-01 | AQ2 与分开配偶仍有联系/经济往来 | keep dc3 / elim dc1,dc2 | keep dc1,dc2 / elim dc3 | 全 elim |
| 3 | P0-02 | AQ1 收入以体制外项目/投资/兼职为主 | keep dc2 / elim dc1 | keep dc1 / elim dc2 | 全 elim |
| 4 | P0-03 | AQ1 妇科病确诊前有婚姻/家庭重大变故 | keep dc1 / elim dc2 | keep dc2 / elim dc1 | 全 elim |
| 5 | P0-03 | AQ2 发病期间有心脏/血压/心慌症状 | keep st2 / elim [] | keep st1 / elim st2 | 全 elim |
| 6 | P0-04 | AQ1 资产被一次性清空 | keep st2 / elim st1 | keep st1 / elim st2 | 全 elim |

## 3. 规则

- 答案只答事实；不解释、不选候选、不补造；
- 一题淘汰后剩余候选若唯一→落定；多个→继续下一题/needs_anchor；
- 两题都 unknown→C；
- 不把锚点事实用于评分（P1 留出组另算）；
- 不改 engine/A+/阈值；不做 git 写；不跑评分器。

## 4. 产物

- `META/p0-cards-v1.json`（A 落定 + 6 答回收 + elimination 结果）
- `META/p0-recovery-v1.md`（逐题结果/剩余候选/needs_anchor）
- `tasks/T-197b/BRIEF.md` + `STATUS.md`
- 第三方重推另卡（T-197c），只凭 CLI+锚点。
