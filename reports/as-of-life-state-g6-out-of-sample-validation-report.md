# G6 样本外回放验证报告

> 状态：G6 LOCAL ONLY / NOT PUSHED
> 关联规格：[`plans/as-of-life-state-g6-out-of-sample-case-spec.md`](../plans/as-of-life-state-g6-out-of-sample-case-spec.md)
> 关联基线：[`reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`](as-of-life-state-career-wealth-slice-g0-g5-verification.md)
> 关联审计：[`reports/as-of-life-state-reasoning-audit-2026-07-26.md`](as-of-life-state-reasoning-audit-2026-07-26.md)

## 1. 结论

**部分验证：一案通过、一案跳过。** 不得读作"两案例都通过"。

- `C-2026-024-坤-己巳壬申辛亥壬辰`：排盘含四柱、藏干、十神、起运，证据充分，样本外回放通过。
- `C-2026-022-坤-癸亥庚申戊寅己未`：排盘缺少显式十神/藏干十神字段，按 G6 证据门判定**跳过，证据不足**；未构造原局承载图，未推算补齐。

冻结生产实现 [`engine/asof/`](../engine/asof/) 与既有 G0-G5 测试全程零改动。全仓 sanity 只复现审计报告已知的两个既有失败，未出现第三个失败，未触发任何 STOP 条件。

## 2. 本轮新增文件（仅限授权四项）

| 文件 | 用途 |
|---|---|
| [`tests/asof/test_case_2024_out_of_sample.py`](../tests/asof/test_case_2024_out_of_sample.py) | C-2026-024 样本外回放：原局承载图、两个大运阶段、双证据门候选、三个截止点回放、事实/假设分离、财富弃权 |
| [`tests/asof/test_case_2022_out_of_sample.py`](../tests/asof/test_case_2022_out_of_sample.py) | C-2026-022 证据不足机械核验 + 显式 skip，不推算十神 |
| [`plans/as-of-life-state-g6-out-of-sample-case-spec.md`](../plans/as-of-life-state-g6-out-of-sample-case-spec.md) | 两案例准入裁决、字段冻结、日期规范化说明、验收边界 |
| [`reports/as-of-life-state-g6-out-of-sample-validation-report.md`](as-of-life-state-g6-out-of-sample-validation-report.md) | 本报告 |

无其他文件被创建或修改；未触及 `engine/asof/`、既有 `tests/asof/` G0-G5 文件、冻结规格、G0-G5 验证报告、任何生产文件。

## 3. G6-A：C-2026-024 证据与结果

### 3.1 准入判定

四柱己巳/壬申/辛亥/壬辰、四柱及藏干十神、1996 年起运顺行均在 [`cases/C-2026-024-坤-己巳壬申辛亥壬辰/input.md`](../cases/C-2026-024-坤-己巳壬申辛亥壬辰/input.md) 明确列出，四项必需证据齐全，准入通过。

### 3.2 原局承载图（只读排盘，不读现实履历）

三个承载节点：`career-output`（月柱/时柱伤官）、`career-authority`（年支巳藏正官）、`career-support`（巳申辰均见印星）；冻结可行路径 `education-to-management` 表达"教育输出经组织承接进入基层管理"的原局允许性，附带反向约束（伤官两透而官星仅藏）。

### 3.3 大运阶段（右开区间转闭区间）

| 大运 | 输入区间 | 闭区间结果 | 显式路径变化 |
|---|---|---|---|
| 甲戌 | [2006,2016) | 2006-01-01~2015-12-31 | 开放教育职业入口 |
| 乙亥 | [2016,2026) | 2016-01-01~2025-12-31 | 放大既有输出路径 |

### 3.4 反馈事件与日期规范化（防泄漏边界，非事实日期）

反馈原文只给窗口年份（2014-2015 入职、2024-2025 升校长），冻结使用窗口末日作为归并边界：

| 事件 | 反馈窗口 | 回放归并日期 | 日期语义 |
|---|---|---|---|
| 教师入职 | 2014-01-01~2015-12-31 | 2015-12-31 | 保守规范化边界，非实际入职日 |
| 升职校长 | 2024-01-01~2025-12-31 | 2025-12-31 | 保守规范化边界，非实际升职日 |

测试 [`test_case_2024_window_end_dates_are_normalization_boundaries_not_claimed_fact_dates`](../tests/asof/test_case_2024_out_of_sample.py:301) 对此显式断言。

### 3.5 双证据门与三个截止点

两个事件均为 `STRONG_ROOT + ACTIVATE_EXISTING`（白名单内），命盘证据 + 原始语料引用双证据门通过后，才由反馈证据标记为 `CONFIRMED`；反馈未参与根源判定。

| 截止点 | 事实快照中的事件 |
|---|---|
| 2013-12-31 | 无 |
| 2015-12-31 | 教师入职 |
| 2025-12-31 | 教师入职、升职校长 |

2023-12-31 截止点下，升职候选只能进入 `HypothesisState`，不进入 `verified_event_ids`；两类快照无共享字段（测试机械核验 `not hasattr`）。

### 3.6 财富弃权

复用 G4 冻结的两条合成边（promotion→稳定收入能力提高；entrepreneurship→收入结构变化与资产风险暴露），未创建新边。因案例反馈只有"小康水平"、无"薪酬制度随职级调整"核验事实，调用 [`propagate_career_event_to_wealth`](../engine/asof/wealth_propagation.py:54) 返回 `PROPAGATION_CONDITIONS_NOT_MET`，未写入财富事实状态。

### 3.7 定向测试命令输出

```
python -m pytest tests/asof/test_case_2024_out_of_sample.py -q
......                                                                   [100%]
6 passed in 0.14s
EXIT_CODE:0
```

## 4. G6-B：C-2026-022 跳过裁决与证据

### 4.1 已有字段

四柱癸亥/庚申/戊寅/己未、四支藏干、1990 年起运顺行、事业反馈年份完整（2005/2011/2013-09/2020/2025/2025-12）。

### 4.2 缺失字段

[`cases/C-2026-022-坤-癸亥庚申戊寅己未/input.md`](../cases/C-2026-022-坤-癸亥庚申戊寅己未/input.md) 全文没有"十神:"或"藏干十神:"字段。虽可依日主推算，但 G6 证据门明令禁止自行补算。

### 4.3 裁决

**跳过，证据不足。** 未构造 `NatalCapacityGraph`，未冻结根源等级，未运行事件双证据门。测试只机械核验字段缺失并显式 `pytest.skip`，不产出任何推算结果。

### 4.4 定向测试命令输出

```
python -m pytest tests/asof/test_case_2022_out_of_sample.py -v
tests/asof/test_case_2022_out_of_sample.py::test_case_2022_source_lacks_explicit_ten_god_fields_required_by_g6_gate PASSED
tests/asof/test_case_2022_out_of_sample.py::test_case_2022_out_of_sample_replay_is_skipped_without_deriving_ten_gods SKIPPED
  (G6 evidence gate: case input has four pillars, hidden stems and luck-cycle
   start, but no explicit ten-god or hidden-stem ten-god fields; deriving
   them is forbidden)
1 passed, 1 skipped
```

## 5. G6-C：命令结果汇总表

| 命令 | 结果 | Exit Code |
|---|---|---|
| `python -m pytest tests/asof/test_case_2024_out_of_sample.py -q` | 6 passed | 0 |
| `python -m pytest tests/asof -q`（含新增两文件） | 82 passed, 1 skipped | 0 |
| `python -m pytest tests/asof/test_production_isolation.py -q` | 4 passed | 0 |
| `git diff --stat -- engine/asof tests/asof plans/as-of-life-state-prototype-spec.md reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`（已跟踪路径） | 无输出 | 0 |
| `python -m pytest -q`（全仓 sanity） | 2 failed, 3083 passed, 7 skipped, 1 warning, 1590.27s | 1 |

全仓失败与 G0-G5 基线完全一致，均为审计报告已知项：

- [`tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented`](../tests/evaluation/test_dataset.py:259)
- [`tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds`](../tests/evaluation/test_prospective_gate_workflow.py:346)

未出现第三个失败，未触发 STOP。

## 6. 生产隔离与零 diff 说明

- 生产隔离测试 4 passed：as-of 模块未导入默认 registry/pipeline/reports/timing/F09；生产入口未导入 `engine.asof`；公共 schema 未被扩展。
- 零 diff 限制说明：本仓库基线中 `engine/asof/`、`tests/asof/`、本次新增的 `plans/as-of-life-state-g6-out-of-sample-case-spec.md` 均为 Git 未跟踪路径（仓库尚未对这批 G0-G5/G6 产物做初始提交）。因此"零 diff"只能通过下列方式核验，不能引用 `git status` 的 clean 状态作为证据：
  1. 已跟踪的冻结路径（`plans/as-of-life-state-prototype-spec.md`、`reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md` 等）执行 `git diff` 确认零输出。
  2. 对 `engine/asof/` 九个实现文件与既有九个 G0-G5 测试文件，本轮未执行任何写入工具调用，只执行了 `read_file`；创建的两个测试文件与一个 spec 文件均为全新文件，不涉及既有内容改动。
- 工作区当前 `git status --short` 中除本轮四个新增授权文件外，仍包含此前未提交的既有工作（多个 `plans/production-implementation-*`、`engine/f09/` 等），这些不属于本任务写入范围，原样保留、未做任何改动。

## 7. G7 授权边界

G6 完成后是否进入 G7（生产接线、promotion、字段扩展等）**未获授权**，本轮不执行任何 G7 相关操作。是否启动 G7 需要另行明确授权。
