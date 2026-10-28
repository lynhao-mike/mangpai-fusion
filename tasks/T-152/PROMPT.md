# T-152 · 产品规则契约化：triggered / outcome + 反条件干跑

- 状态：🔵 Ready for Execution
- 优先级：**P0（与 T-153 并行）**
- 创建：2026-10-28（中枢）
- 依据：`docs/reviews/verdict-chatgpt6.md` §4.4；T-150 度量契约（`engine/claims/metrics.py`）
- 前置：T-150 已完成（`6b1ffead`）

## 0. 一句话

把产品断语的 `matched`（一个布尔）拆成 `triggered`（触发）/ `outcome`（结果），让「反条件」第一次有语义；**本卡不改 `matched`、不改产品输出**，只干跑并报「若反条件生效，会压掉多少条」。

## 1. 已核实现状（不要重复验证）

- `engine/claims/rule_loader.py:345-359`：`matched = not failed_conditions and not matched_exclusions`；`matched_counter_conditions` 已经算出来，但**不参与判定**。
- 10 条生产规则在 `theory/production/claim-rules-v1.yaml`；至少 3 条正/反条件阈值重叠：
  - `DUAN-EVENT-CAREER-PATH-MIXED-V1`：正 `branch_conflict_intensity >= 0.35`、反 `<= 0.4`
  - `DUAN-EVENT-WEALTH-DEBT-V1`：正 `support_drain_imbalance >= 3`、反 `<= 3`
  - 婚姻规则 `DUAN-EVENT-MARRIAGE-...`：正 `independent_signal_count >= 2`、反 `<= 2`（以文件为准）
- 产品 runner：`engine/v5/{duan,gao,yang}_runner.py` 调 `evaluate_rule(...).matched`；**本卡不许改 runner**。
- 重叠不再构成「同时成立且不成立」：`triggered=True + outcome=fail` 本来就是「结构成立但被反证」，这正是 T-150 契约要表达的。本卡只是把它算出来，不急着用它拦产品。

## 2. 契约字段（改 `RuleEvaluationResult`）

在 dataclass **末尾**新增两个带默认值的字段（保证既有构造/解包不破）：

- `triggered: bool = False`
- `outcome: str = "unknown"`（只允许 `success` / `fail` / `unknown`）

判定表：

| 情形 | triggered | outcome | matched（本卡保持旧值） |
|---|---|---|---|
| conditions 有未满足 | `False` | `unknown` | `False` |
| exclusions 命中 | `False` | `unknown` | `False` |
| conditions 全中、exclusions 未中、counter 命中 | `True` | `fail` | **`True`**（旧语义，本卡不改） |
| conditions 全中、exclusions 未中、counter 未中 | `True` | `success` | `True` |

硬规则：

1. `outcome="fail"` 只能出现在 `triggered=True`；`triggered=False` 时必须是 `unknown`。
2. **`matched` 一个字都不改**。要不要把它改成 `triggered and outcome != "fail"`，等中枢看完干跑数字另开卡。
3. `required_facts` 缺失仍抛 `RuleEvaluationError`，不许吞、不许当 `unknown`。
4. 不改 `claim-rules-v1.yaml`、不改阈值、不改 runner、不改既有测试断言。

## 3. 干跑工具

新建 `tools/rule_contract_report.py`：

- 语料：`META/timing-eval-set-v1.json` 中 `usable_for_timing=true` 的 **382 例**；用 `birth_dt` + `gender`（男→乾、女→坤）建盘，`engine.features.build_chart_feature_vector` 取特征。
- 若不清楚建盘入口：读 `engine/v5/duan_runner.py`、`engine/features/__init__.py`、`engine/api/`，**不要猜**。
- 对 10 条规则逐条 `evaluate_rule`，报：
  - `n_evaluated` / `n_triggered` / `n_counter` / `n_suppressed_if_flipped`（= triggered 且 counter 命中）
  - 被压掉的 `case_id` 列表（控制台最多 20 个，JSON 全量）
  - 每条规则的正条件 / 反条件原文（人可读）
- 产物：`META/rule-contract-dryrun-v1.json` + `META/rule-contract-dryrun-v1.md`；控制台打印 10 行表。
- 建盘失败逐例列原因，不许 `except: pass`。
- 两次运行输出必须逐字节一致（无时间戳）。

## 4. 测试（新建 `tests/claims/test_rule_contract.py`）

只许新建，**不许改既有测试**。至少覆盖：

1. 判定表 4 行；
2. 正反同时命中的边界向量 → `triggered=True`、`outcome="fail"`、`matched=True`；
3. exclusion 命中 → `triggered=False`、`outcome="unknown"`；
4. 默认值兼容：用旧字段构造 `RuleEvaluationResult` 不破；
5. 缺 `required_facts` 仍抛 `RuleEvaluationError`。

## 5. File Scope

**允许修改**

- `engine/claims/rule_loader.py`

**允许新建**

- `tools/rule_contract_report.py`
- `tests/claims/test_rule_contract.py`
- `META/rule-contract-dryrun-v1.json`
- `META/rule-contract-dryrun-v1.md`

**只读**

- `theory/production/claim-rules-v1.yaml`
- `META/timing-eval-set-v1.json`
- `engine/v5/**`、`engine/features/**`、`engine/api/**`

**禁止**

- 改 `claim-rules-v1.yaml`、改 runner、改既有测试断言
- `theory/_ir/`、`sources/`、`theory/raw/`、`pyproject.toml`
- `git commit / push / checkout / stash / reset / clean`

## 6. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q
# 0 failed；passed >= 1066；skipped 仍为 1

.venv\Scripts\python.exe -m tools.rule_contract_report
# 退出码 0；打印 10 行表

.venv\Scripts\python.exe -m pytest tests/claims/test_rule_contract.py -q -o addopts="-ra --tb=short"
# 全绿
```

中枢额外检查：

- `git diff theory/production/claim-rules-v1.yaml` 为空；
- 读 diff：`matched` 公式未变；
- 干跑两次输出逐字节一致；
- 被压掉的 case_id 可复跑。

## 7. 回报格式（`tasks/T-152/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（三条命令 + 10 行表）
3. **未完成与风险**（建盘失败、规则覆盖、反条件命中最多的规则）
4. **下游须知**（`triggered`/`outcome` 语义；`matched` 仍是旧语义）

## 8. 禁止

- 不许为了让反条件「看起来有用」改阈值。
- 不许在干跑里挑案例、删难例。
- 不许改 `matched`——那是下一张卡、要中枢看完数字再决定。

## 9. 中枢裁决（2026-10-28 22:50）

1. **不翻 `matched`。** 干跑：若把 `matched` 改为 `triggered and outcome != "fail"`，**641/965（66.4%）条生产断语被压掉**：
   `GAO-HEALTH-MODERATE` 100%、`GAO-HEALTH-HIGH` 100%、`ENTREPRENEURSHIP` 92.3%、`GAO-WEALTH` 89.4%、
   段派婚姻 79.1%、杨派婚姻 60.2%。
2. **根因不是「反条件太严」，是反条件与正条件同阈值/同信号**：
   - `GAO-HEALTH-MODERATE`：正条件 `risk_signal_count >= 2` **且** `<= 2`（即 ==2），反条件 `>= 2` → 被正条件逻辑蕴含，必然 100% 命中。
   - `GAO-HEALTH-HIGH`：正 `>=3`、反 `<=3` → 只压「恰好 3」的最弱触发。
   - 段派 / 杨派婚姻：正 `>=2`、反 `<=2` → 只压「恰好 2」。
   - `ENTREPRENEURSHIP`：反 `employment_score >= 2` 过宽，压 92.3%。
   - 真正像「窄重叠」的只有 `CAREER-PATH-MIXED`（5/47）。
3. **结论**：当前反条件不是「独立反证」，而是「弱触发过滤」或「同义反复」。要让它有语义，必须重写为
   「正条件必要前提的否定」或「独立反证」，并给出原文/口径依据；**另立卡**（T-156 候选），不许拍脑袋改阈值。
4. **下游纪律**：`triggered` 可用作 T-154 的触发口径；`outcome` 在反条件重写前**不得**用于产品拦截，也不得用于评分。
