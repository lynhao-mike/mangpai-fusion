# T-157 · 断语句子由本盘事实装配（statement 不再是模板原文）

- 状态：🔵 Ready for Execution
- 优先级：**P2（产品可信度；不新增预测力）**
- 创建：2026-10-28（中枢）
- 依据：`docs/handoff-hub-v1.md` §七（Gemini 4 指控）；T-152/T-150 契约
- 前置：T-152 已完成（`triggered` / `outcome` 已落地）

## 0. 一句话

三个 v5 runner 现在都写 `statement=rule.conclusion_template`（语料模板原文）。改成
**「结论 + 本盘事实值」**：每条断语必须带本盘算出来的事实，不能再是纯模板句。

## 1. 已核实现状

- `engine/v5/gao_runner.py:63`、`duan_runner.py:126`、`yang_runner.py:126`：`statement=rule.conclusion_template`。
- `Claim.applicability_snapshot` 已含本盘事实（`snapshot` 字典）；`evaluate_rule` 返回 `matched_conditions`。
- 规则的条件 fact 是聚合特征（如 `independent_signal_count`、`branch_conflict_intensity`），
  **不是盘面地址**。本卡 v1 只做「本盘事实值」，**不做**「地址装配」——地址版需要 fact→地址映射，另立卡。

## 2. 设计

新增 `render_statement(rule, result, context) -> str`：

- 放在 `engine/claims/domain.py`（与 `Claim` 同模块，避免新增 v5 import 触发 ADR-006 冻结门禁）。
  若必须新模块，先报告，**不许改治理测试/allowlist**。
- 格式：`{conclusion_template}｜本盘依据：{fact1}={value1}；{fact2}={value2}`
  - 只取 `result.matched_conditions` 里的 fact，从 `context` 取值；
  - 按 fact 名排序，保证确定性；值用 `repr` 风格（字符串加引号、浮点保留 4 位）；
  - 至少一个 `fact=value`；若一个都没有（理论上不会），返回模板 + 在 evidence 文本里加 `[no-fact]` 标记，**不许静默**。
- **不改** `applicability_snapshot`、`confidence`、`evidence`、`matched`。

三个 runner 改成：

```python
result = evaluate_rule(rule, context)
if not result.matched:
    return []
...
statement=render_statement(rule, result, context),
```

其余逻辑一律不动。

## 3. 测试

新建 `tests/claims/test_statement_render.py`：

1. 同一规则、两张不同盘 → `statement` 不同，且各自包含本盘 fact 值；
2. `statement != rule.conclusion_template`；
3. 至少包含一个 `fact=`；
4. 确定性：同一输入两次相同；
5. 缺 fact 时返回模板并带 `[no-fact]` 标记（不静默）。

既有测试若断言 `claim.statement == rule.conclusion_template`：**改成**
「包含 `conclusion_template` 且包含至少一个 fact=value」，**不许**放宽成 `assert statement`。

## 4. 样例

`META/statement-render-sample-v1.md`：3 张盘（事业/财富/婚姻各 1），列 before（模板）与 after（本盘事实），
并注明「本版是事实值，不是盘面地址」。

## 5. File Scope

**允许修改**

- `engine/claims/domain.py`（加 `render_statement`）
- `engine/v5/gao_runner.py`、`engine/v5/duan_runner.py`、`engine/v5/yang_runner.py`
- 既有测试中「断言 statement == template」的那几处（只改断言口径，不放宽）

**允许新建**

- `tests/claims/test_statement_render.py`
- `META/statement-render-sample-v1.md`

**只读**

- `theory/production/claim-rules-v1.yaml`
- `engine/claims/rule_loader.py`、`engine/claims/condition_ir/**`

**禁止**

- 改 YAML、改阈值、改 `matched`、改 claim 逻辑
- 改 `tests/governance/**` 或 v5 allowlist（被门禁拦下就报告，不许绕）
- `theory/_ir/`、`sources/`、`git commit / push / checkout / stash / reset / clean`

## 6. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest tests/claims/test_statement_render.py -q -o addopts="-ra --tb=short"
.venv\Scripts\python.exe -m pytest -q                       # 0 failed，passed >= 1099
.venv\Scripts\python.exe -m pytest tests/governance -q -o addopts="-ra --tb=short"   # v5 门禁
```

中枢额外检查：

- 抽 1 张盘，`statement` 里的事实值能在 `applicability_snapshot` / context 里逐项对上；
- `statement != conclusion_template`；
- 没有改 YAML、没有改 `matched`；
- 既有测试的改动是「加严」不是「放宽」。

## 7. 回报格式（`tasks/T-157/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（命令 + 3 例 before/after）
3. **未完成与风险**（v5 门禁、哪些断言被改、地址版遗留）
4. **下游须知**（statement 结构；事实值不是地址）

## 8. 禁止

- 不许只加一句「本盘」就交差；必须有 `fact=value`。
- 不许把测试从「等于模板」放宽成「非空」。
- 不许动治理门禁或 allowlist。
