# RF 案例补全 · 结论报告（2026-10-17）

## 一、最终数字

| 项 | 数量 |
|---|---|
| `real_cases_990.jsonl` 总记录 | **992** |
| 已有 RF 案例目录（as_of_raw_feedback_paipan 展开） | 443 |
| 本次新增 pillar-only 案例（rf_pillar_intake） | **3** |
| **当前 RF 案例总数** | **446** |
| 始终无法展开 | 546 |

## 二、为什么 546 条无法展开（已逐项诊断）

| 原因 | 数量 | 能否补救 |
|---|---|---|
| 缺 `bazi_raw`（命主未自报四柱） | 540 | ❌ 无四柱则无法排盘，任何"补四柱"都是编造 |
| 缺出生时间（`true_solar_time_raw` / `birth_datetime_raw` 均空） | 549 | ⚠️ 有四柱者可走 pillar-only 口径（本次已收 3 条） |
| 缺性别/乾坤 | 9 | ❌ 性别决定大运顺逆，不能猜 |

**关键结论**：`as_of_raw_feedback_paipan.py` 的 `_is_eligible()` 要求
`quality_grade ∈ {A,B}` + `calendar_type == solar` + 有出生时间 + 有 events。
实测剩余 546 条里，绝大多数是**原始反馈里只描述了事件、没给生辰**的命主求助帖——
它们有真实反馈价值，但没有盘面就无法进入盲测池。

**这与"干净比完整"原则一致**：不猜四柱、不猜性别。446 个干净样本足够建立
第一轮准确率基线；剩余 546 条标记为 `no_chart_available`，仅作为反馈语料存在。

## 三、446 个样本的构成

| 类型 | 数量 | 特征 |
|---|---|---|
| 公历口径（有出生时间） | 443 | 可算起运年份、人元司令，完整岁运 |
| pillar-only（仅四柱） | 3 | 无起运年份、无人元司令，只能条件分支实断 |

## 四、对 P06-T03「真实 prospective cohort 建立」的影响

`META/project-state.json` 的 `domain_prospective real_cohort = not_ready` 的根因
**不是数据不够，而是这批数据从未被引擎跑过**。446 个案例里绝大多数只有
`input.md` + `feedback.md`，没有 `chart/relations/strength/structures` 的实跑结果。

**下一步（blind_ledger 的前置）**：对这 446 个案例跑 `engine.cli all --pillars`
（pillar-only 3 个）与 `--birth`（443 个），落盘引擎事实，才能谈"盲断"与"对账"。

## 五、新增文件

- `tools/rf_pillar_intake.py`：四柱口径案例提取器。与
  `tools/as_of_raw_feedback_paipan.py` 的关系：后者要出生时间，前者专收
  "有四柱无生时"。两者互补，均幂等（拒绝覆盖已存在目录）。
- 每个 pillar-only 案例带 `pillar_only.json` 机器可读标记，声明
  `unavailable: [qiyun, dayun_calendar, siling]`，供下游评测排除
  依赖大运年份/人元司令的断言。
