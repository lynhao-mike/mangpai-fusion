# G7 更大规模样本外验证报告

> 状态：G7 LOCAL ONLY / NOT PUSHED  
> 关联规格：[`plans/as-of-life-state-g7-larger-sample-case-spec.md`](../plans/as-of-life-state-g7-larger-sample-case-spec.md)  
> 冻结实现：[`engine/asof/`](../engine/asof/)  
> 前序基线：[`reports/as-of-life-state-g6-out-of-sample-validation-report.md`](as-of-life-state-g6-out-of-sample-validation-report.md)

## 1. 结论

**验证通过：两案完整通过、一案部分通过。** 三案均准入，但 C-2026-027 仍因财富主域保持弃权而记为部分通过。

- `C-2026-016-坤-甲子丙子丙戌戊子`：原文藏干干名完整，藏干十神由冻结排盘引擎确定并标注派生来源；2012 学生服务中心与 2020 教师编制事件完成双证据门、三截止点、事实/假设隔离及财富弃权验证。
- `C-2026-026-坤-癸未甲寅壬戌丙午`：准入通过；2020 年入编教师事件完成双证据门、历史截止点回放、事实/假设隔离和财富传播弃权验证。
- `C-2026-027-乾-丁卯壬寅甲午乙丑`：部分通过；可锚定的宽职业窗口完成事业主域回放，卖房反馈不进入事业事实账本，财富传播保持弃权。

三个案例均不要求修改冻结实现。既有 [`engine/asof/`](../engine/asof/) 和已有 [`tests/asof/`](../tests/asof/) 未被修改，未出现需要扩大实现或改写既有测试的模式性缺口，未触发 STOP 条件。

## 2. 本轮新增文件（仅限授权五项）

| 文件 | 用途 |
|---|---|
| [`tests/asof/test_case_2016_out_of_sample.py`](../tests/asof/test_case_2016_out_of_sample.py) | C-2026-016 引擎派生证据、原局、大运、双事件、三截止点、双快照与财富弃权验证 |
| [`tests/asof/test_case_2026_out_of_sample.py`](../tests/asof/test_case_2026_out_of_sample.py) | C-2026-026 原局、大运、事件、三截止点、双快照与财富弃权验证 |
| [`tests/asof/test_case_2027_out_of_sample.py`](../tests/asof/test_case_2027_out_of_sample.py) | C-2026-027 宽窗口锚定、跨运回放、双快照与财富弃权验证 |
| [`plans/as-of-life-state-g7-larger-sample-case-spec.md`](../plans/as-of-life-state-g7-larger-sample-case-spec.md) | 三案例准入裁决、冻结字段、日期语义和验收边界 |
| [`reports/as-of-life-state-g7-larger-sample-validation-report.md`](as-of-life-state-g7-larger-sample-validation-report.md) | 本报告 |

## 3. G7-A：C-2026-016 引擎派生后准入

### 3.1 派生证据链

案例原文显式提供四柱、日主丙、全部藏干干名及气类、四柱主星、起运信息和大运排布。原文没有手写藏干十神，但仓库已有确定性入口 [`get_shishen()`](../engine/predicates/palace.py:148)，特征层也逐项调用该入口处理藏干 [`_ten_god_features()`](../engine/features/chart_feature_vector.py:102)。

冻结派生结果为：癸正官、戊食神、辛正财、丁劫财。每条结构证据同时保存案例原文藏干定位和引擎函数定位，并明确写为“非原文手写事实”；现实反馈不参与十神映射。

### 3.2 原局、大运与双事件

原局冻结 `career-output`、`career-authority`、`career-resource`、`career-wealth` 四个节点，以及 `service-transition`、`service-to-establishment` 两条路径。冻结癸酉运 `2008-01-01` 至 `2017-12-31`、壬申运 `2018-01-01` 至 `2027-12-31`，不从反馈反填大运信号。

两个事业事件通过双证据门：

1. 2012 年换行业并开学生服务中心；
2. 2020 年成功进入教师编制。

对应截止点：

| 截止点 | 事实快照 |
|---|---|
| `2011-12-31` | 无事件，禁止未来信息泄漏 |
| `2012-12-31` | 只有学生服务中心事件 |
| `2020-12-31` | 学生服务中心与教师编制事件 |

两处年末日期均为年份窗口的规范化边界，不是反馈声称的真实发生日。未核验的教师编制候选只能进入物理分离的 `HypothesisState`。

### 3.3 财富传播弃权

2012 entrepreneurship 与既有合成边事件类型相符，但反馈没有核验“经营主体已实际运行”等传播条件，裁决返回 `PROPAGATION_CONDITIONS_NOT_MET`，未写入财富事实状态，也未新增传播边。

## 4. G7-B：C-2026-026 回放结果

### 4.1 原局与大运

原局冻结三个事业承载节点：

- `career-output`：寅藏甲食神，表示教学与知识输出承载；
- `career-authority`：未、午藏己正官，戌藏戊七杀，表示制度职责承载；
- `career-resource`：戌藏辛正印，表示资质与组织承接。

冻结路径 `education-to-establishment`，但不在原局图中预写“已经入编”。丙辰运使用 `2018-01-01` 至 `2027-12-31` 的闭区间，只放大已冻结路径，不从现实履历反填结构。

### 4.2 双证据门和历史截止点

唯一回放事业事件为“2020 年考入乡镇中学并成为在编教师”。反馈只有年份，故冻结窗口 `2020-01-01` 至 `2020-12-31`，以 `2020-12-31` 作为保守归并边界；该日期不是反馈声称的真实发生日。

| 截止点 | 事实快照 |
|---|---|
| `2019-12-31` | 无入编事件，禁止未来信息泄漏 |
| `2020-12-31` | 已核验入编事件进入事实快照 |
| `2026-05-31` | 仍只有入编事件，不因截止日推进发明新事实 |

候选使用白名单内的 `STRONG_ROOT + ACTIVATE_EXISTING`，且同时具有命盘结构证据与原始语料引用。只有反馈核验后才进入 `VerifiedState`；未核验版本只能进入物理分离的 `HypothesisState`。

### 4.3 财富传播弃权

2025 年手机丢失和 2026 年戒指丢失是财物损失反馈，不是事业事件，也不匹配冻结的 promotion 或 entrepreneurship 合成传播边。以 `career_entry` 调用既有边集返回 `NO_EXPLICIT_EDGE`，没有新增“入编→财物损失”传播边。

## 5. G7-C：C-2026-027 部分回放结果

### 5.1 相对时间锚定

职业反馈为“最近 7 年左右开始从事机箱厂设计、绘图、拆图工作”，反馈采集日明确为 `2026-06-01`。由于“左右”不支持精确日期，冻结宽窗口 `2018-01-01` 至 `2020-12-31`，并以 `2020-12-31` 作为保守归并边界。该日期不是命主真实转岗日。

### 5.2 原局、大运和截止点

原局冻结：

- `career-technical-output`：丁伤官、寅藏丙食神；
- `career-applied-resource`：壬偏印、丑藏癸正印；
- `career-institutional-constraint`：丑藏辛正官。

冻结路径 `mechanical-design-specialization`。职业窗口横跨己亥运与戊戌运边界；测试保留两段大运上下文，不把现实职业反填成大运信号。

| 截止点 | 事实快照 |
|---|---|
| `2017-12-31` | 职业窗口尚未开始 |
| `2020-12-31` | 已核验职业专业化事件进入事实快照 |
| `2021-12-31` | 事业事实集合不因卖房反馈而增加资产事件 |

职业候选通过双证据门后，已核验版本进入 `VerifiedState`，未核验版本只进入独立 `HypothesisState`。

### 5.3 财富传播弃权

“2021 年左右卖掉婚房”只作为财富/资产处置反馈存在，不反向抬升职业候选根源等级，也不写入事业事实账本。`career_specialization` 不匹配既有合成边，传播裁决返回 `NO_EXPLICIT_EDGE`；没有创建“技术岗→卖房”或反向传播边。

## 6. 验证命令与结果

### 6.1 G7 定向与隔离验证

| 命令 | 结果 | Exit Code |
|---|---:|---:|
| `python -m pytest tests/asof/test_case_2016_out_of_sample.py -q` | 7 passed | 0 |
| `python -m pytest tests/asof/test_case_2026_out_of_sample.py -q` | 6 passed | 0 |
| `python -m pytest tests/asof/test_case_2027_out_of_sample.py -q` | 6 passed | 0 |
| `python -m pytest tests/asof -q` | 101 passed, 1 skipped, 1 warning | 0 |
| `python -m pytest tests/asof/test_production_isolation.py -q` | 4 passed | 0 |

### 6.2 全仓 sanity 的可审计分组覆盖

原始单命令 `python -m pytest -q` 在执行通道中多次未返回完整最终摘要，其中 `-1` 是执行通道/外部终止状态，不是正常 pytest 失败码，也不作为完成证据。为避免虚报，改用互斥目录分组覆盖整个 [`tests/`](../tests/) 树；各分组均取得 pytest 最终摘要和 exit code。

| 互斥范围 | 结果 | Exit Code |
|---|---:|---:|
| 顶层 `tests/test_*.py` | 392 passed, 2 skipped | 0 |
| `application + claims + decision + evaluation + features + learning` | 856 passed, 2 failed | 1 |
| `tests/f09` | 1172 passed | 0 |
| `tests/r10` | 64 passed | 0 |
| `tests/regression` | 34 passed | 0 |
| `tests/ren_timing` | 50 passed, 1 warning | 0 |
| `tests/tools` | 6 passed | 0 |
| `track_a_smoke` 至 `track_g_smoke` | 46 passed, 2 skipped, 1 warning | 0 |
| `v1_3_acceptance + v2 + v5 + yang_marriage + ziping_career` | 381 passed, 2 skipped, 1 warning | 0 |
| `tests/asof` | 101 passed, 1 skipped, 1 warning | 0 |

按修订后的 as-of 分组替换原分组结果后，全仓互斥分组汇总为 **3102 passed、2 failed、7 skipped**。两个失败均为前序基线已知历史失败：

- [`test_witness_trust_boundary_is_explicitly_documented()`](../tests/evaluation/test_dataset.py:259)
- [`test_handoff_names_first_legal_case_action_and_all_independent_holds()`](../tests/evaluation/test_prospective_gate_workflow.py:346)

没有发现第 3 个失败，未触发 STOP。重复出现的 warning 为 [`pipeline_runner.py`](../engine/application/pipeline_runner.py:11) 导入 deprecated adapter 的非致命弃用警告。

## 7. 生产隔离、零 diff 与工作区说明

- 生产隔离验证通过：as-of 原型未接入默认 registry、pipeline、reports、timing 或 F09；生产入口没有导入 `engine.asof`；公共 schema 未扩展。
- 对冻结实现和已有 as-of 测试执行限定 `git diff` 为零输出。本轮没有对 [`engine/asof/`](../engine/asof/) 或已有 [`tests/asof/`](../tests/asof/) 使用写入操作。
- 仓库基线中 as-of 目录及前序产物本就处于未跟踪状态，因此不能以工作区整体 clean 作为零 diff 证据；只能结合限定 diff、写入记录和最终新增文件清单审计。
- 工作区存在大量本任务开始前的已修改/未跟踪背景文件，均未作为 G7 交付，也未被本轮清理或改写。

## 8. 收口边界

G7 已在冻结实现上完成更大样本验证，不修改生产实现，不新增传播边；只有原文日主与藏干干名完整时才允许冻结引擎确定十神，并将派生证据与原文事实分层保存；规范化日期不写成现实事实。

**G8 未获授权且未启动。** 本轮保持 `LOCAL ONLY / NOT PUSHED`。
