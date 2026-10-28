# T-157 BRIEF · 断语句子由本盘事实装配

- 执行者：子代理 J
- 完成时间：2026-10-28 23:45（Asia/Shanghai）
- 任务卡：`tasks/T-157/PROMPT.md`

## 1. 改动文件

**实现（3 + 1）**

- `engine/claims/domain.py`：新增 `render_statement(rule, result, context)` 及两个私有格式化/取值助手。
- `engine/v5/gao_runner.py`：保留一次 `evaluate_rule` 结果并传入 `_claim`，`statement` 改由 `render_statement` 生成。
- `engine/v5/duan_runner.py`：四个事件 handler 均保留 `result`，`_claim` 新增 `result` / `context` 参数。
- `engine/v5/yang_runner.py`：保留 `result`，`statement` 改由 `render_statement` 生成。

**新建（2）**

- `tests/claims/test_statement_render.py`（5 个用例）
- `META/statement-render-sample-v1.md`（事业 / 财富 / 婚姻各 1 例 before/after）

**未改**：YAML、阈值、`matched`、claim 逻辑、`tests/governance/**`、v5 allowlist、`theory/_ir/`、`sources/`、`engine/claims/rule_loader.py`。

## 2. 原始输出

### 2.1 T-157 新测试

```text
.venv\Scripts\python.exe -m pytest tests/claims/test_statement_render.py -q -o addopts="-ra --tb=short"
.....                                                                    [100%]
5 passed in 0.16s
```

### 2.2 三例 before / after（真实走三个 runner）

> before = `rule.conclusion_template`；after = `claim.statement`。
> 事实值均可在同一 Claim 的 `applicability_snapshot` 中逐项对上（见每例末尾）。

**① 事业 · duan `career.role_change` · 盘 `庚申 戊寅 壬子 辛丑`（乾）**

- before:
  > 段派原局的财官事业结构与做功、冲动信号同向，支持一生中出现显著岗位、职责或职业角色变化。
- after:
  > 段派原局的财官事业结构与做功、冲动信号同向，支持一生中出现显著岗位、职责或职业角色变化。｜本盘依据：active_path_count=3；has_official=True；has_output=True；movement_structure=True；official_count=2；output_count=3
- 快照核对：`active_path_count=3`、`has_official=True`、`has_output=True`、`movement_structure=True`、`official_count=2`、`output_count=3`。

**② 财富 · gao `wealth.debt` · 盘 `丙午 丙午 丁巳 丙午`（乾）**

- before:
  > 高派结构性旁证显示债务风险与财富承压信号复合出现，但不作必然判断。
- after:
  > 高派结构性旁证显示债务风险与财富承压信号复合出现，但不作必然判断。｜本盘依据：pressure_signal_count=4；wealth_exposed=True
- 快照核对：`pressure_signal_count=4`、`wealth_exposed=True`。

**③ 婚姻 · yang `marriage.divorce_or_remarriage` · 盘 `乙丑 己卯 丁酉 辛亥`（坤）**

- before:
  > 杨派原局至少两类独立婚姻事件信号同向，存在离婚或再婚事件风险，但不作必然判断。
- after:
  > 杨派原局至少两类独立婚姻事件信号同向，存在离婚或再婚事件风险，但不作必然判断。｜本盘依据：independent_signal_count=5；sex='female'；spouse_star_basis='official'
- 快照核对：`independent_signal_count=5`、`sex='female'`、`spouse_star_basis='official'`。

### 2.3 门禁与回归

```text
.venv\Scripts\python.exe -m pytest tests/governance/test_v5_import_freeze.py -q -o addopts="-ra --tb=short"
.....                                                                    [100%]
5 passed in 6.14s
```

```text
.venv\Scripts\python.exe -m pytest -q
3 failed, 1101 passed, 1 skipped, 1 warning in 85.17s (0:01:25)
```

3 个失败**不是 T-157 引入**，全部由并行任务 T-156 在当前共享工作区修改
`theory/production/claim-rules-v1.yaml`（把多条 `counter_conditions` 改为 `[]`）造成：

- `tests/claims/test_rule_contract.py::test_positive_and_counter_overlap_is_triggered_fail_but_still_matched`
  （2 个参数化用例：`DUAN-EVENT-CAREER-PATH-MIXED-V1`、`DUAN-EVENT-WEALTH-DEBT-V1`）
- `tests/test_production_entrypoints_unchanged.py::test_ren_staged_slice_does_not_modify_production_claim_rules`
  （YAML sha256 断言）

T-157 未触碰该 YAML；等 T-156 收口后中枢重跑即可复核。
上述全量结果跑于 2026-10-28 23:44，T-156 之后仍在并行动 `test_rule_contract.py` / 新增
`tests/claims/test_counter_conditions.py` 等；最终门禁以中枢在 T-156 落地后的重跑为准。

`tests/governance` 全量当前为 `17 failed, 166 passed`，失败均为**既有环境/仓库红灯**，
与 T-157 无关：

- `engine/governance/structure_catalog_*.py` 使用 PEP 695（`type X = ...` / `def f[T]`），
  当前 `.venv` 是 Python 3.11.16，`ast.parse` 直接 `SyntaxError`；
- `tests/governance/test_school_registry.py` 的 dataclass `__setattr__` 报错
  `super(type, obj): obj must be an instance or subtype of type`。

v5 冻结门禁本身（`test_v5_import_freeze.py`）5/5 通过，未新增 v5 import、未改 allowlist。

## 3. 未完成与风险

- **既有断言改动：0 处。** 全仓检索 `conclusion_template` 后确认，没有测试断言
  `claim.statement == rule.conclusion_template`；因此不存在需要「加严」的等式断言。
  既有 `"债务风险" in claim.statement`、`"存在离婚或再婚事件风险" in claim.statement`
  等包含式断言保持原样并仍通过，未放宽成 `assert statement`。
- **v5 门禁**：`test_v5_import_freeze.py` 通过；`render_statement` 放在
  `engine/claims/domain.py`，runner 只 `from engine.claims.domain import render_statement`。
- **地址版未做**：本版只装配 runner `context` 里的聚合事实值（`active_path_count` 等），
  不是 `four_pillars.day` 之类盘面地址；地址映射按卡另立任务。
- **`[no-fact]` 落点**：`render_statement` 只返回 `str`，无法回写不可变的 `Evidence.text`；
  无命中事实时把 `[no-fact]` 放在返回的 statement 尾段
  （`模板｜本盘依据：[no-fact]`），保证不静默退回模板。若必须写进 evidence 文本，需另改签名/调用方。
- **并发风险**：T-156 正在改同一共享工作区；BRIEF 中 before/after 以当前 YAML 的模板为准，
  若 T-156 后续改 `conclusion_template`，样例文字需同步重跑。
- **样例口径**：`META/statement-render-sample-v1.md` 的三例是回归夹具（部分 CFV 聚合代理按
  既有测试口径替换），不是真实命盘预测结论。

## 4. 下游须知

- `statement` 结构固定为：
  `{conclusion_template}｜本盘依据：{fact1}={value1}；{fact2}={value2}`
  - fact 只取 `result.matched_conditions`，按 fact 名排序；
  - 去重；字符串 `repr`（单引号）、浮点 4 位、布尔 `True/False`；
  - 无命中事实时为 `{conclusion_template}｜本盘依据：[no-fact]`。
- 三个 runner 现在都是「求值一次 → 用同一 `result` 生成 statement」，`matched` 判定路径未变。
- `render_statement` 入口是 `engine.claims.domain.render_statement`；未加入
  `engine.claims.__init__` 的 `__all__`（避免超出本卡 File Scope）。
- 任何下游若原样展示 `statement`，会看到模板 + 事实值；若需要纯模板，应显式取
  `rule.conclusion_template`，不要截断 statement。
- 样例文件：`META/statement-render-sample-v1.md`。
