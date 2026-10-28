# T-163 BRIEF · `rule_contract_report` 加 `--out-prefix`

- 任务卡：`tasks/T-163/PROMPT.md`
- 状态：实现与自测完成，待中枢验收
- 先说结论：工具只加参数与路径处理，统计逻辑 0 行改动（diff 可查）。**tmp 前缀产物数值与 v1 不一致、与 v2 逐条一致**，原因见 §3.1；v1 本身零改动。

## 1. 改动文件

| 文件 | 改动 |
|---|---|
| `tools/rule_contract_report.py` | +71 / −12。新增 `argparse` 的 `--out-prefix`（默认 `META/rule-contract-dryrun-v1`）；相对前缀按仓库根解析；实际写 `<prefix>.json` 与 `<prefix>.md`；控制台打印实际写出的两个路径；前缀目录不存在 → 退出码 2 且不写；只写成功一个文件（或写出异常）→ 退出码 2。`_evaluate_corpus` / `_build_payload` / `_print_table` / `_render_markdown` 等统计与表格函数未改。 |
| `tests/tools/test_rule_contract_report.py`（新建） | 6 个测试：tmp 前缀写两个文件（真实运行）、两次真实运行逐字节一致、默认前缀仍为 v1 且解析到 `META/rule-contract-dryrun-v1.{json,md}`、默认调用（monkeypatch 到 tmp）写 v1 文件名、目录不存在退出 2 且不建目录不写文件、只写成功一个文件退出 2。 |

未触碰：`META/rule-contract-dryrun-v1.{json,md}`、`META/rule-contract-dryrun-v2.{json,md}`、规则 YAML、`engine/**`、`theory/**`、`sources/**`、既有测试。工作区里其他并行任务的改动（如 `tools/verify_baseline.py`、career-role 标签产物）与本任务无关，未触碰。

## 2. 原始输出

### 2.1 新测试（本次任务验收命令）

```text
> .venv\Scripts\python.exe -m pytest tests/tools/test_rule_contract_report.py -q -o addopts="-ra --tb=short"
......                                                                   [100%]
6 passed in 29.48s
PYTEST_EXIT=0
```

### 2.2 tmp 前缀实跑

```text
> .venv\Scripts\python.exe -m tools.rule_contract_report --out-prefix "$env:TEMP\t163-dryrun"
...
已写出：C:\Users\Administrator\AppData\Local\Temp\t163-dryrun.json
已写出：C:\Users\Administrator\AppData\Local\Temp\t163-dryrun.md
EXIT=0
14653 C:\Users\Administrator\AppData\Local\Temp\t163-dryrun.json
7665  C:\Users\Administrator\AppData\Local\Temp\t163-dryrun.md
```

### 2.3 两次独立运行逐字节一致

两次不同前缀（`$env:TEMP\t163-worker-dryrun-a` 与 `$env:TEMP\t163-dryrun`）的产物 SHA256 相同：

```text
json_equal=True  1FA11CA4DE826876DA35017077E8C042004539075CFCFFA41E26F024BD4FAC87
md_equal=True    0F27FD42552584AFCDFDAE778CB3E42FEFB1636EA258C7624057C85B1B94D814
```

### 2.4 v1 零改动

```text
> git status --porcelain META/rule-contract-dryrun-v1.json META/rule-contract-dryrun-v1.md
（空，exit 0）

> git diff --quiet -- META/rule-contract-dryrun-v1.json META/rule-contract-dryrun-v1.md
DIFF_EXIT=0
```

SHA256（与 T-156 记录的基线一致）：

```text
JSON E3ED1318CF12E3FF41D3F4C3646414D6DBBB8637544988D34BD2B84A4C5AD10A
MD   A68311AB55DB4BFD4474258CBB2B4C95541808122D6422765463C4FC4CC1EF7C
```

### 2.5 目录不存在 → 退出码 2 且不写

```text
> .venv\Scripts\python.exe -m tools.rule_contract_report --out-prefix "$env:TEMP\t163-no-such-dir\dryrun"
错误：输出目录不存在：C:\Users\Administrator\AppData\Local\Temp\t163-no-such-dir
EXIT=2
DIR_EXISTS=False
```

### 2.6 全量回归

```text
> .venv\Scripts\python.exe -m pytest -q
1260 passed, 1 skipped, 1 warning in 122.56s (0:02:02)
PYTEST_EXIT=0
```

（1 skipped 是 `tests/tools/test_bundle_pii.py` 的已知 T-114 过渡 skip，非本任务引入。）

## 3. 未完成与风险

### 3.1 任务卡 §5「写出的 JSON 数值与 v1 完全一致」与仓库现状冲突（重要）

实测新工具 tmp 产物与各版本对照：

| 版本 | totals（evaluated / triggered / counter / suppressed_if_flipped） | 与新 tmp 产物 |
|---|---|---|
| 新 tmp 产物 | 2219 / 965 / **379 / 185** | — |
| `META/rule-contract-dryrun-v2.json` | 2219 / 965 / **379 / 185** | 逐条规则数值完全一致 |
| `META/rule-contract-dryrun-v1.json` | 2219 / 965 / **1818 / 641** | 7 条规则不同 |

原因：v1 生成于 T-156 修复规则反条件**之前**；T-156 修 YAML 后重跑得到的就是 v2 的数值（T-156 STATUS/BRIEF 有记录）。本任务对统计、规则读取、表格输出零改动，所以当前 YAML 下任何一次运行都只能得到 v2 数值，不可能得到 v1 的 1818/641。

v1 与新产物逐条差异（仅列变化规则）：

```text
DUAN-EVENT-CAREER-PATH-MIXED-V1:            n_counter 5→0,  n_suppressed 5→0,  outcome_success 42→47, outcome_fail 5→0
DUAN-EVENT-WEALTH-DEBT-V1:                  n_counter 318→0
DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1:  n_counter 350→0, n_suppressed 121→0, outcome_success 32→153, outcome_fail 121→0
GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1:n_counter 369→0, n_suppressed 84→0,  outcome_success 10→94,  outcome_fail 84→0
GAO-HEALTH-SYSTEM-RISK-MODERATE-V1:          n_counter 90→0,  n_suppressed 90→0,  outcome_success 0→90,  outcome_fail 90→0
GAO-HEALTH-SYSTEM-RISK-HIGH-V1:              n_counter 17→0,  n_suppressed 17→0,  outcome_success 0→17,  outcome_fail 17→0
YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1:    n_counter 290→0, n_suppressed 139→0, outcome_success 92→231, outcome_fail 139→0
```

（上表箭头为「v1 → 新产物」；`n_evaluated` / `n_matched` / `n_triggered` 全部规则一致。）

**给中枢的验收建议**：不要用 v1 数值做「一致」判据，否则会误判。等价且安全的判法是
「同一条新命令跑两次（不同 tmp 前缀）逐字节一致」（见 §2.3），或「新产物数值与 v2 逐条一致」。
若确实要证明「改前改后数值不变」，应在备份 v1 后跑旧版本对照并二进制还原，而不是拿 v1 当基线。

### 3.2 其它风险

- **默认调用未在本仓库实跑**：默认前缀会覆盖 v1，卡明确禁止。已用「解析默认值 + monkeypatch 默认前缀到 tmp 跑 `main([])`」覆盖，行为不变；中枢如需实跑请先备份 v1 并按 SHA256 还原。
- **只写成功一个文件时不回滚**：写出失败会保留已成功的那一个文件，只保证退出码 2（卡未要求删除半成品）。
- **默认值仍非必填**：保持兼容是卡的要求；其它工具是否也有硬编码输出路径，本卡未扩大范围排查。
- 工作区有并行任务未提交改动，`git status` 会比本任务文件多；本任务只改了 §1 列出的两个文件。

## 4. 下游须知

- 参数：`--out-prefix <prefix>`，**不带扩展名**；实际写 `<prefix>.json` / `<prefix>.md`。
- 相对路径按**仓库根**解析（`--out-prefix META/rule-contract-dryrun-v3` → `<repo>/META/...`）；也接受绝对路径（如 `$env:TEMP\...`）。
- 默认（不带参数）仍写 `META/rule-contract-dryrun-v1.{json,md}`，控制台文案与旧版一致。
- 退出码：`0` 成功；`2` = 前缀目录不存在（不写、不建目录）/ 写出失败 / 只写成功一个文件。
- 生成 v3 时直接加 `--out-prefix META/rule-contract-dryrun-v3`，不再需要「备份 v1 → 跑 → 还原」。
- 数值口径以当前 YAML 为准：新产物与 `META/rule-contract-dryrun-v2.json` 逐条一致，不是 v1。
