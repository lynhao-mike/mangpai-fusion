# T-152 BRIEF · 产品规则契约化：triggered / outcome + 反条件干跑

- 执行者：子代理 E
- 完成时间：2026-10-28 22:26（Asia/Shanghai）
- 任务卡：`tasks/T-152/PROMPT.md`
- 结论：`matched` 一个字未改；10 条规则的 `triggered` / `outcome` 已可求值；干跑 382 例、建盘失败 0、四次运行输出逐字节一致。

## 1. 改动文件

**修改（1）**

- `engine/claims/rule_loader.py`
  - `RuleEvaluationResult` 末尾新增 `triggered: bool = False`、`outcome: str = "unknown"`（带默认值，既有的 5 字段位置参数构造不破）。
  - 新增 `__post_init__` 契约校验：`outcome` 只允许 `success` / `fail` / `unknown`；非 `unknown` 必须 `triggered=True`（违反抛 `ValueError`）。
  - `evaluate_rule` 新增 `triggered` 与 `outcome` 计算；`matched=not failed_conditions and not matched_exclusions` **整行未动**（见 §2.5 diff 摘录）。

**新建（5）**

- `tools/rule_contract_report.py`（干跑工具，退出码 0；不 import 冻结的 `engine.v5`，按 ADR-006 用 `GanZhi.parse + adapt_bazi` 等价重建 `duan_runner.chart_ledger_to_bazi`）
- `tests/claims/test_rule_contract.py`（10 个测试）
- `META/rule-contract-dryrun-v1.json`（全量，含被压掉 case_id，无时间戳）
- `META/rule-contract-dryrun-v1.md`（人读报告）
- 本 `BRIEF.md`

**仅追加**：`tasks/T-152/STATUS.md` 的 Execution Log。

未触碰：`theory/production/claim-rules-v1.yaml`、`engine/v5/**`、`engine/features/**`、`engine/api/**`、既有测试、`pyproject.toml`、`theory/_ir/`、`sources/`、`theory/raw/`；无任何 git 写操作。

## 2. 原始输出

### 2.1 `pytest tests/claims/test_rule_contract.py`（退出码 0）

```text
..........                                                               [100%]
10 passed in 0.44s
```

覆盖：判定表 4 行；真实规则 `PATH-MIXED`（bci=0.35）与 `WEALTH-DEBT`（imbalance=3）正反同时命中 → `triggered=True`、`outcome="fail"`、`matched=True`；exclusion 命中 → `False/unknown`；旧 5 字段构造默认值；`outcome` 白名单与 `fail` 必须 `triggered`；缺 `required_facts` 仍抛 `RuleEvaluationError`。

### 2.2 `python -m tools.rule_contract_report`（退出码 0）

```text
语料：382 例（usable_for_timing=true）；建盘失败 0 例
rule_id                                           eval  trig  cntr  supp  succ
------------------------------------------------------------------------------
DUAN-EVENT-CAREER-ROLE-CHANGE-V1                   382   176   307   113    63
DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1                77    77     0     0    77
DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1          78    78    72    72     6
DUAN-EVENT-CAREER-PATH-MIXED-V1                     47    47     5     5    42
DUAN-EVENT-WEALTH-DEBT-V1                          382     2   318     0     2
DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1          382   153   350   121    32
GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1        382    94   369    84    10
GAO-HEALTH-SYSTEM-RISK-MODERATE-V1                  90    90    90    90     0
GAO-HEALTH-SYSTEM-RISK-HIGH-V1                      17    17    17    17     0
YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1           382   231   290   139    92
------------------------------------------------------------------------------
TOTAL                                             2219   965  1818   641
```

列：`eval=n_evaluated`、`trig=n_triggered`、`cntr=n_counter`、`supp=n_suppressed_if_flipped`、`succ=n_outcome_success`。
`succ = trig - supp` 逐行成立；`matched == triggered` 在 10 条规则上均为 True（`matched` 仍是旧语义）。

两次连跑后 `META/rule-contract-dryrun-v1.json` SHA256 `E3ED1318…5AD10A`、`.md` SHA256 `A68311AB…C1EF7C` 完全一致（无时间戳）。

### 2.3 `python -m pytest -q`（退出码 0）

```text
SKIPPED [1] tests\tools\test_bundle_pii.py:34: 生成脚本缺失（T-114）
1099 passed, 1 skipped, 1 warning in 86.29s
```

说明：该次运行包含并行任务 T-153 已落在工作区的 `tests/tools/test_marriage_quality_labels.py`（+23 例）；本卡新增 10 例。0 failed，skipped 仍为 1。

### 2.4 `git diff --exit-code -- theory/production/claim-rules-v1.yaml`（退出码 0，无输出）

规则文件未被改动。

### 2.5 `matched` 公式未变的 diff 证据

```diff
+    triggered = not failed_conditions and not matched_exclusions
+    # 本卡只新增 triggered / outcome；matched 仍是旧语义，是否翻转另案裁决。
+    if not triggered:
+        outcome = "unknown"
+    elif matched_counters:
+        outcome = "fail"
+    else:
+        outcome = "success"
     return RuleEvaluationResult(
         matched=not failed_conditions and not matched_exclusions,
```

## 3. 未完成与风险

### 3.1 建盘失败

382/382 建盘成功，`build_failures = []`；段派结构（`evaluate_tiyong + evaluate_zuogong`）失败 0 例。工具仍逐例记录失败原因（`stage=build` / `duan_structure` + 异常类型与消息，无 `except: pass`），只是本次为空。

### 3.2 规则覆盖与口径

- 10/10 条生产规则都有数字；但 `n_evaluated` 按「生产 runner 实际会调用 `evaluate_rule` 的盘数」计，因此路径/健康规则小于 382：`PATH-EMPLOYMENT 77`、`PATH-ENTREPRENEURSHIP 78`、`PATH-MIXED 47`、`HEALTH-MODERATE 90`、`HEALTH-HIGH 17`；其余 6 条各 382。这是 runner 的 dispatch 语义，不是漏跑。
- 上下文逐字复刻 `engine/v5/{duan,gao,yang}_runner.py`（含 `predicted_label` 推导、`independent_signal_count` 六信号、高派四强信号）；但为了过 ADR-006 的 v5 冻结门禁，工具不 import v5，`chart_ledger_to_bazi` 用同一套 predicate 原语等价重建。**runner 若改 context，本工具需同步**。
- 独立复算校验（另写脚本、不经本工具）：高派健康信号分布 `{0:95,1:180,2:90,3:17}`、段派婚姻独立信号 `{0:83,1:146,2:121,3:32}`、杨派独立信号 `{0:32,1:119,2:139,3:80,4:12}`，与表内 `trig/supp` 完全对上。

### 3.3 反条件命中最多的规则（本卡核心数字）

按「若反条件生效会被压掉的条数」降序：

| 规则 | 压掉 / 触发 | 压制率 | 反条件原文 |
|---|---:|---:|---|
| `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | 139 / 231 | 60.2% | `independent_signal_count <= 2` |
| `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | 121 / 153 | 79.1% | `independent_signal_count <= 2` |
| `DUAN-EVENT-CAREER-ROLE-CHANGE-V1` | 113 / 176 | 64.2% | `branch_conflict_intensity <= 0.34` |
| `GAO-HEALTH-SYSTEM-RISK-MODERATE-V1` | 90 / 90 | 100% | `risk_signal_count >= 2` |
| `GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1` | 84 / 94 | 89.4% | `pressure_signal_count <= 2` |
| `DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1` | 72 / 78 | 92.3% | `employment_score >= 2` |
| `GAO-HEALTH-SYSTEM-RISK-HIGH-V1` | 17 / 17 | 100% | `risk_signal_count <= 3` |
| `DUAN-EVENT-CAREER-PATH-MIXED-V1` | 5 / 47 | 10.6% | `branch_conflict_intensity <= 0.4` |
| `DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1` | 0 / 77 | 0% | `active_path_count <= 0` |
| `DUAN-EVENT-WEALTH-DEBT-V1` | 0 / 2 | 0% | `support_drain_imbalance <= 3` |

合计 `641 / 965`（66.4%）。若按「反条件命中盘数（含未触发）」看，最多的是 `GAO-WEALTH 369`、`MARRIAGE-DUAN 350`、`WEALTH-DEBT 318`、`ROLE-CHANGE 307`、`YANG 290`——但其中绝大多数是正条件本就没过的盘，对产品无压制意义。

**风险（必须让中枢看到）**：`GAO-HEALTH-MODERATE` 与 `GAO-HEALTH-HIGH` 的触发盘 100% 被反条件覆盖，`ENTREPRENEURSHIP` 92.3%、`GAO-WEALTH` 89.4%、`MARRIAGE` 两派 60–79%。若下一卡直接把 `matched` 翻转成 `triggered and outcome != "fail"`，**641 条生产断语会被压掉**，高派健康分层与段派创业路径几乎归零。这组反条件目前更像「与正条件同阈值的重叠校验」而非独立反证；翻转前应先议阈值（本卡按卡禁止改阈值）。段派 `WEALTH-DEBT` 只触发 2/382，本就极窄，反条件对它无影响。

### 3.4 其他

- `outcome` 的契约校验放进了 `__post_init__`（`ValueError`），属于本卡新增的防御，不改变 loader 既有异常路径。
- 测试 `test_positive_and_counter_overlap_is_triggered_fail_but_still_matched` 显式断言 `matched=True`。下一卡翻转 `matched` 时该断言会红——这是有意的护栏，不要为了让红变绿而删断言；应在下一卡同步改判据。
- 工具未纳入 `pyproject.toml` 的测试命令，未改任何门禁配置。

## 4. 下游须知

1. **语义**：`triggered = conditions 全中且 exclusions 未中`；`outcome`：`triggered 且 counter 命中 → fail`、`triggered 且 counter 未中 → success`、未触发 → `unknown`。`triggered=False` 时 `outcome` 必为 `unknown`（`__post_init__` 强制）。
2. **`matched` 仍是旧语义**（= `not failed_conditions and not matched_exclusions`），当前与 `triggered` 同值；产品输出、runner 行为零变化。是否翻转由下一卡裁决。
3. **复跑**：`python -m tools.rule_contract_report` 每次重算并覆盖 `META/rule-contract-dryrun-v1.{json,md}`；被压掉的 case_id 全量在 JSON 的 `rules[].suppressed_case_ids`，可直接逐例复跑 `evaluate_rule`。
4. **`n_evaluated` 口径**：按 runner dispatch 计（选中的那条规则才计数），不要拿它当「382 例覆盖率」；需要覆盖 382 的横向矩阵需另设口径（未做，避免与 runner 语义漂移）。
5. 干跑工具控制台最多列 20 个 case_id，JSON 全量；两次运行逐字节一致，可安全做 diff 门禁。
