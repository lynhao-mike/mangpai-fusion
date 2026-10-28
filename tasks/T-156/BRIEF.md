# T-156 BRIEF · 反条件语义审计与可证明修复

- 执行者：子代理 I
- 完成时间：2026-10-28 23:49（Asia/Shanghai）
- 任务卡：`tasks/T-156/PROMPT.md`（含中枢 §9.1–§9.4 裁决）
- 结论：**A 类 7 条删反条件 / B 类 3 条原样保留 / C 类 0 条**；`matched` 未改；
  v1/v2 的 `n_evaluated` / `n_matched` / `n_triggered` **逐条相同**。

## 1. 改动文件

**修改（3）**

1. `theory/production/claim-rules-v1.yaml` —— **只**把 7 条 A 类的 `counter_conditions` 改成 `[]`。
   `git diff --stat` = `7 insertions(+), 14 deletions(-)`，无其他 hunk；新 SHA256
   `14d34deaaf37decaef4be2df76318c9d39202dc645f91f927cefab398f3e6467`（旧 `6396883d…b0bebef`）。
   - A 类：`DUAN-EVENT-CAREER-PATH-MIXED-V1`、`DUAN-EVENT-WEALTH-DEBT-V1`、
     `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1`、`GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1`、
     `GAO-HEALTH-SYSTEM-RISK-MODERATE-V1`、`GAO-HEALTH-SYSTEM-RISK-HIGH-V1`、
     `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1`
   - 未动：正条件、阈值、`exclusions`、`conclusion_template`、`confidence_basis`、B 类反条件、
     杨派 `sex truthy` / `sex falsy`。
2. `tests/claims/test_rule_contract.py` —— 按 §9.1 解耦 2 个参数化用例（+9 / −3）：
   三条原断言（`matched_counter_conditions` 非空、`outcome == "fail"`、`matched is True`）**原样保留**，
   用 `dataclasses.replace(rule, counter_conditions=(RuleCondition(...),))` 显式钉住旧反条件，
   新增 `assert production_rule.counter_conditions == ()`。
   **这是「测试与生产 YAML 解耦」，不是把红改绿**：loader 判定表语义（有反条件→fail）仍被完整测试，
   只是不再寄生在生产 YAML 上；生产状态另由新增断言与 `test_counter_conditions.py` 固定。
3. `tests/test_production_entrypoints_unchanged.py` —— 按 §9.3 只替换哈希值 + 一行注释，
   断言、测试名、函数体不变：`6396883d…b0bebef` → `14d34dea…3e6467`，注释
   `# T-156（2026-10-28）：A 类 counter_conditions 删除；审计见 META/counter-condition-audit-v1.md`。
   这是「变更检测器重新基线」：下一次未经授权的 YAML 改动仍会报警。

**新建（4）**

- `META/counter-condition-audit-v1.md`（10 条逐条审计：类别 / 反条件原文 / 结论原句 / 动作 / 理由 +
  阈值重叠点 + v1/v2 对照 + 复跑说明）
- `META/rule-contract-dryrun-v2.json`、`META/rule-contract-dryrun-v2.md`
- `tests/claims/test_counter_conditions.py`（38 例：分类完整性、A 类边界 success、A 类旧行为 fail、
  B 类仍 fail、A 类清空、B 类原文保留、正条件/排除/结论/依据逐字快照）

**仅追加**：`tasks/T-156/STATUS.md` 的 Execution Log。

未触碰：`META/rule-contract-dryrun-v1.{json,md}`（`git status` 为空，SHA256 与备份一致）、
`engine/**`（只读）、`theory/_ir/`、`sources/`、其它既有测试、`tools/rule_contract_report.py`；
无任何 git 写操作（无 commit / push / checkout / stash / reset / clean）。

## 2. 原始输出

### 2.1 `python -m tools.rule_contract_report`（退出码 0，382 例，建盘失败 0）

```text
语料：382 例（usable_for_timing=true）；建盘失败 0 例
rule_id                                           eval  trig  cntr  supp  succ
------------------------------------------------------------------------------
DUAN-EVENT-CAREER-ROLE-CHANGE-V1                   382   176   307   113    63
DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1                77    77     0     0    77
DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1          78    78    72    72     6
DUAN-EVENT-CAREER-PATH-MIXED-V1                     47    47     0     0    47
DUAN-EVENT-WEALTH-DEBT-V1                          382     2     0     0     2
DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1          382   153     0     0   153
GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1        382    94     0     0    94
GAO-HEALTH-SYSTEM-RISK-MODERATE-V1                  90    90     0     0    90
GAO-HEALTH-SYSTEM-RISK-HIGH-V1                      17    17     0     0    17
YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1           382   231     0     0   231
------------------------------------------------------------------------------
TOTAL                                             2219   965   379   185
```

列：`eval=n_evaluated`、`trig=n_triggered`、`cntr=n_counter`、`supp=n_suppressed_if_flipped`、`succ=n_outcome_success`。
与 v1 的 `trig` 逐条相同（176/77/78/47/2/153/94/90/17/231）；A 类 `cntr`/`supp` 全部归零；
`supp` 只剩 B 类的 113 + 0 + 72 = 185。

复跑证据：连跑两次均 `exit code 0`，原始输出逐字节一致——
JSON `1FA11CA4DE826876DA35017077E8C042004539075CFCFFA41E26F024BD4FAC87`、
MD `0F27FD42552584AFCDFDAE778CB3E42FEFB1636EA258C7624057C85B1B94D814`；
`META/rule-contract-dryrun-v2.json` 的字节来源就是这份原始输出（之后只加了 `task` / `provenance`）。

### 2.2 v1 / v2 逐条对照（`n_matched` / `n_triggered` 必须相同）

| rule_id | 类 | n_matched v1/v2 | n_triggered v1/v2 | n_counter v1→v2 | n_suppressed v1→v2 | n_success v1→v2 |
|---|---|---:|---:|---:|---:|---:|
| `DUAN-EVENT-CAREER-ROLE-CHANGE-V1` | B | 176/176 | 176/176 | 307→307 | 113→113 | 63→63 |
| `DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1` | B | 77/77 | 77/77 | 0→0 | 0→0 | 77→77 |
| `DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1` | B | 78/78 | 78/78 | 72→72 | 72→72 | 6→6 |
| `DUAN-EVENT-CAREER-PATH-MIXED-V1` | A | 47/47 | 47/47 | 5→0 | 5→0 | 42→47 |
| `DUAN-EVENT-WEALTH-DEBT-V1` | A | 2/2 | 2/2 | 318→0 | 0→0 | 2→2 |
| `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | A | 153/153 | 153/153 | 350→0 | 121→0 | 32→153 |
| `GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1` | A | 94/94 | 94/94 | 369→0 | 84→0 | 10→94 |
| `GAO-HEALTH-SYSTEM-RISK-MODERATE-V1` | A | 90/90 | 90/90 | 90→0 | 90→0 | 0→90 |
| `GAO-HEALTH-SYSTEM-RISK-HIGH-V1` | A | 17/17 | 17/17 | 17→0 | 17→0 | 0→17 |
| `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | A | 231/231 | 231/231 | 290→0 | 139→0 | 92→231 |
| **合计** | — | 965/965 | 965/965 | 1818→379 | 641→185 | 324→780 |

校验脚本同时逐条比对 `conditions` / `exclusions` / `school_id` / `task_scope` / `predicted_label` /
`n_evaluated` / `n_exclusion_veto` / `n_condition_unmet`，10 条规则全部相同（退出码 0）。

### 2.3 测试

```text
$ .venv\Scripts\python.exe -m pytest tests/claims/test_counter_conditions.py -q -o addopts="-ra --tb=short"
......................................                                   [100%]
38 passed in 1.58s
[exit code: 0]

$ .venv\Scripts\python.exe -m pytest -q
1142 passed, 1 skipped, 1 warning in 86.66s (0:01:26)
[exit code: 0]
```

skip 仍是 T-114 已知项（`tests/tools/test_bundle_pii.py`）。`1142` 含 T-157 落在工作区的
`tests/claims/test_statement_render.py` 与本卡 +38 例。

### 2.4 v1 干跑未被覆盖（§9.2）

| 文件 | SHA256（与 T-152 备份一致） |
|---|---|
| `META/rule-contract-dryrun-v1.json` | `E3ED1318CF12E3FF41D3F4C3646414D6DBBB8637544988D34BD2B84A4C5AD10A` |
| `META/rule-contract-dryrun-v1.md` | `A68311AB55DB4BFD4474258CBB2B4C95541808122D6422765463C4FC4CC1EF7C` |
| `META/rule-contract-dryrun-v2.json` | `4B7B9EA4023CBF962D4D700A7C86FE3587A57A0F1792D87E53BB43596C054015` |
| `META/rule-contract-dryrun-v2.md` | `CAD1CA7C1AF8733A43FD7D41E851F43DB3D8CF3C37FE5FCF8E7A992D846A0B88` |

`git status --porcelain -- META/rule-contract-dryrun-v1.json META/rule-contract-dryrun-v1.md` 为空。

## 3. 未完成与风险

### 3.1 分类结果与「改判」

- **A 类 7 条（删）**：反条件与正条件同 fact、阈值重叠，阈值点上正反同时成立，与结论/依据自相矛盾。
- **B 类 3 条（留）**：反条件用正条件里没有的 fact，结论/依据有独立语义。
- **C 类 0 条**：3 条非 A 规则都找到了对应语义，本次没有「证据不足、待人类裁决」的删除项。
- 与卡面预注册表的**唯一偏差**：卡面给 `DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1` 的 B 依据句
  「存在有效做功路径」实属 `ENTREPRENEURSHIP` 的 `confidence_basis`，不在本条结论/依据里。
  本条仍判 **B（保留）**，旁证是：① `active_path_count` 已列入本条 `required_facts`；
  ② 本条 `source_refs` 的 M1-D-009 / §17.3 做功 `supports` 原文「支持用结构作用关系审计职业路径。」；
  ③ 4 条姊妹规则把同一语义写成正条件 `active_path_count >= 1`。干跑压制 0/77。
  若中枢采「依据必须本条逐字」的严口径，本条应降 **C**——动作不变（保留），v2 数字不受影响。
- 卡面两处「需回原文确认」已确认：`MIXED` 原文是「并有冲动及有效做功路径」（无「强」字）→ A；
  `GAO-WEALTH` 依据「至少有两项」→ 「复合」= 至少 2 → A。

### 3.2 C 类待裁决：0 条

没有规则被误删：7 条 A 类都能逐字引用结论/依据原句证明「至少 x / 多项 / 有冲动 / 失衡」就是正条件阈值
（逐条引文见 `META/counter-condition-audit-v1.md` §2–§3，28 个片段已用脚本逐字校验命中）。

### 3.3 B 类压制率（校准风险，需另卡裁决，本卡不动）

| 规则 | 反条件 | 压制 / 触发 | 压制率 |
|---|---|---:|---:|
| `DUAN-EVENT-CAREER-ROLE-CHANGE-V1` | `branch_conflict_intensity <= 0.34` | 113 / 176 | 64.2% |
| `DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1` | `employment_score >= 2` | 72 / 78 | 92.3% |
| `DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1` | `active_path_count <= 0` | 0 / 77 | 0% |
| **B 类合计** | — | **185 / 965** | **19.2%**（v1 全量 641/965 = 66.4%） |

产品输出当前零变化（`matched` 未改）；但若后续卡把 `matched` 翻成
`triggered and outcome != "fail"`，这 185 条会被压掉，`ROLE-CHANGE` 与 `ENTREPRENEURSHIP` 首当其冲。
**本卡没有为了让压制率好看去改 B 类阈值。**

### 3.4 验收陷阱：工具硬编码写 v1（必须看）

`tools/rule_contract_report.py:52–53` 把输出路径写死成 `META/rule-contract-dryrun-v1.{json,md}`，
跑一次就会用 v2 数字覆盖 v1——**中枢在验收时跑 `python -m tools.rule_contract_report`，会让
§9.2 的「`git diff` 为空」当场失效**。建议顺序：

1. 先查 `git diff --quiet META/rule-contract-dryrun-v1.json META/rule-contract-dryrun-v1.md`（应为空）；
2. 再跑工具（看退出码 0 与 v2 表）；
3. 跑完还原 v1（`git restore` / `checkout` 属禁止操作，别用）：
   `git show HEAD:META/rule-contract-dryrun-v1.json | Set-Content -Encoding utf8 META/rule-contract-dryrun-v1.json`
   （md 同理），再核对 §2.4 的两个 SHA256。
   本机另有备份：`%TEMP%\t156_v1_backup\`。
4. 根治建议（不在本卡 File Scope）：给工具加 `--out` 参数，或让它按
   `--yaml` 输入写 `v2` 产物。

### 3.5 并行任务

工作区仍有 T-157 的未提交改动（`engine/claims/domain.py`、`engine/v5/*_runner.py`、
`tests/claims/test_statement_render.py`、`META/statement-render-sample-v1.md`）；全量 pytest 1142 例
0 failed 是在这份工作区状态下跑出的。本卡未触碰这些文件。

## 4. 下游须知

1. **仍有反条件的规则只有 3 条**（B 类，语义独立）：`ROLE-CHANGE`（bci ≤ 0.34）、
   `EMPLOYMENT`（active_path_count ≤ 0）、`ENTREPRENEURSHIP`（employment_score ≥ 2）。
   其余 7 条 `counter_conditions == []`，`outcome` 恒 `success`（只要 triggered）。
2. **`matched` 一个字未改**：`matched = conditions 全中且 exclusions 未中`，与反条件无关；
   v1/v2 的 `n_matched` 逐条相同；`matched == triggered` 两版都是 `True`。runner / loader 未动。
3. **A 类规则不再有 outcome=fail 路径**：若下游按 `outcome` 过滤，这 7 条不会再被压；
   若按 `matched` 过滤，行为与 T-152 完全一致。
4. **复跑 v2 的正确姿势**（工具加 `--out` 之前）：备份 v1 两个文件 → 跑工具 → 把 v1 产物复制成
   `META/rule-contract-dryrun-v2.{json,md}` → 还原 v1。直接跑工具只会刷新 v1。
   v2 与工具原样输出相比只多了 `task` / `provenance` / 标题与 3 行出处说明，数字未重算。
5. **护栏**：`tests/claims/test_counter_conditions.py` 快照了 10 条规则的正条件、排除条件、结论、依据
   与 A/B 分类；任何正条件/结论改动、或把 B 类删掉，都会先让这 38 例红。
   `tests/test_production_entrypoints_unchanged.py` 的哈希已重新基线到
   `14d34dea…3e6467`，下一次改 YAML 会红——这是预期行为，不是回归。
6. **新增/改写测试的授权**：`tests/claims/test_rule_contract.py`（§9.1）、
   `tests/test_production_entrypoints_unchanged.py`（§9.3）两处改动均按中枢书面裁决，
   断言强度未降级。
