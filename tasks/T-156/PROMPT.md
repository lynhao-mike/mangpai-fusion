# T-156 · 反条件语义审计与可证明修复（10 条产品规则）

- 状态：🔵 Ready for Execution
- 优先级：**P0（唯一已证实的规则 bug）**
- 创建：2026-10-28（中枢）
- 依据：T-152 干跑（`META/rule-contract-dryrun-v1.md`）；T-154 裁决
- 前置：T-152 已完成（`57745a4a`）

## 0. 一句话

逐条审计 10 条产品规则的 `counter_conditions`：**与结论原文同阈值矛盾的删掉**、**有独立语义的保留**、**证据不足的不动**。
只改可证明的；`matched` 一个字不改，产品输出零变化。

## 1. 已核实的事实（不要重复验证）

- 若把 `matched` 改为 `triggered and outcome != "fail"`，T-152 干跑会压掉 **641/965（66.4%）**：
  `GAO-HEALTH-MODERATE` 100%、`GAO-HEALTH-HIGH` 100%、`ENTREPRENEURSHIP` 92.3%、
  `GAO-WEALTH` 89.4%、段派婚姻 79.1%、杨派婚姻 60.2%、`ROLE-CHANGE` 64.2%。
- 根因不是「反条件太严」，是反条件大多与正条件**同 fact、同阈值**（正 `>= x`、反 `<= x`）；
  `GAO-HEALTH-MODERATE` 的反条件 `risk_signal_count >= 2` 甚至被正条件 `>= 2 且 <= 2` **逻辑蕴含**。
- **杨派 `sex truthy` 不是 bug**：规则性别中立，`sex` 门的语义是「性别已知」，用来排除缺失；
  `male` / `female` 两个非空字符串同真同假是正确行为。**本卡不许改杨派的 sex 条件。**

## 2. 判定规则（预注册，逐条对原文验证）

对每条规则，读 `conclusion_template` 与 `confidence_basis`，把反条件归入三类之一：

- **(A) 同阈值矛盾 → 删除**：反条件用与正条件相同的 fact，且结论/依据明确写「至少 x / 多项 / 有冲动 / 失衡」= 正条件阈值；
  在阈值点上正反同时成立，反条件与结论**自相矛盾**。
- **(B) 独立反证 → 保留**：反条件用不同 fact，且结论/依据有对应语义（如「信号接近时不输出」「无有效做功路径」）；
  保留并在审计表写明原文依据。
- **(C) 证据不足 → 不动**：不同 fact 但找不到语义依据，或阈值重叠但结论措辞不支持删除；列入「待人类裁决」，**不许猜**。

## 3. 预期分类（必须逐条回原文验证；对不上就改判并说明）

| 规则 | 反条件 | 正条件 | 结论/依据关键句 | 预期 |
|---|---|---|---|---|
| `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | `independent_signal_count <= 2` | `>= 2` | 「**至少**两组独立婚姻事件信号同向」 | **A 删** |
| `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | `independent_signal_count <= 2` | `>= 2` | 「**至少**两类独立婚姻事件信号同向」 | **A 删** |
| `GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1` | `pressure_signal_count <= 2` | `>= 2` | 「债务风险与财富承压信号**复合**出现」 | **A 删**（回原文确认「复合」= 至少 2） |
| `GAO-HEALTH-SYSTEM-RISK-MODERATE-V1` | `risk_signal_count >= 2` | `>= 2` **且** `<= 2` | 「多项原局结构代理同向」 | **A 删**（反条件被正条件逻辑蕴含） |
| `GAO-HEALTH-SYSTEM-RISK-HIGH-V1` | `risk_signal_count <= 3` | `>= 3` | 「多项原局结构代理同向」 | **A 删**（回原文确认「多项」= 至少 3） |
| `DUAN-EVENT-CAREER-PATH-MIXED-V1` | `branch_conflict_intensity <= 0.4` | `>= 0.35` | 「并有**冲动**及有效做功路径」 | **A 删**（若原文是「强冲动」则改判 C） |
| `DUAN-EVENT-WEALTH-DEBT-V1` | `support_drain_imbalance <= 3` | `>= 3` | 「克泄耗**失衡**」 | **A 删** |
| `DUAN-EVENT-CAREER-ROLE-CHANGE-V1` | `branch_conflict_intensity <= 0.34` | 正条件不含该 fact | 「财官事业结构……与**冲动**信号同向」 | **B 留** |
| `DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1` | `employment_score >= 2` | 不含该 fact | 「信号**接近**时不输出」 | **B 留**；92.3% 压制率记为校准风险 |
| `DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1` | `active_path_count <= 0` | 不含该 fact | 「存在有效做功路径」 | **B 留** |

## 4. 要做的事

1. **逐条回原文**：引用 `conclusion_template` / `confidence_basis` 的原句，确认上表；不一致的改判并写明理由。
2. **改 YAML**：只删 A 类的 `counter_conditions`（改成空列表 `[]`）；**不改正条件、不改阈值、不改结论、不改 B 类**。
3. **重跑干跑**：`python -m tools.rule_contract_report` → 新产物 `META/rule-contract-dryrun-v2.{json,md}`（不要覆盖 v1）。
   - A 类规则的 `n_counter` / `n_suppressed_if_flipped` 应为 0；
   - **所有规则的 `n_matched` / `n_triggered` 必须与 v1 逐条相同**（反条件本来就不参与 `matched`）；若有一个不同，停下报告。
4. **审计表**：`META/counter-condition-audit-v1.md`，每条规则一行：类别 / 反条件原文 / 结论原句 / 动作 / 理由。
5. **测试**：新建 `tests/claims/test_counter_conditions.py`：
   - A 类：构造一个「正条件成立 + 旧反条件也成立」的边界上下文 → 修后 `triggered=True`、`outcome="success"`、`matched=True`；
   - B 类：构造反条件成立上下文 → 仍 `outcome="fail"`；
   - 静态：A 类 `counter_conditions == []`；正条件列表与修前逐字相同（用快照断言）。

## 5. File Scope

**允许修改**

- `theory/production/claim-rules-v1.yaml`（**仅** A 类规则的 `counter_conditions`）

**允许新建**

- `META/counter-condition-audit-v1.md`
- `META/rule-contract-dryrun-v2.json`、`META/rule-contract-dryrun-v2.md`
- `tests/claims/test_counter_conditions.py`

**只读**

- `tools/rule_contract_report.py`、`engine/claims/rule_loader.py`
- `META/rule-contract-dryrun-v1.json`（对照）
- `META/timing-eval-set-v1.json`

**禁止**

- 改正条件、阈值、结论、B/C 类反条件、杨派 sex 条件
- 改 `matched`、改 runner、改既有测试、`engine/**`（除只读）、`theory/_ir/`、`sources/`
- `git commit / push / checkout / stash / reset / clean`

## 6. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.rule_contract_report     # 退出码 0，生成 v2
.venv\Scripts\python.exe -m pytest tests/claims/test_counter_conditions.py -q -o addopts="-ra --tb=short"
.venv\Scripts\python.exe -m pytest -q                       # 0 failed，passed >= 1099
```

中枢额外检查：

- 逐条比对 v1 / v2 的 `n_matched` / `n_triggered`：必须完全相同；
- YAML diff 只动 A 类 `counter_conditions`；
- 审计表每条的「结论原句」能在 YAML 里逐字找到；
- 没有把 C 类偷偷删掉。

## 7. 回报格式（`tasks/T-156/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（v2 表 + 测试）
3. **未完成与风险**（改判的规则、C 类待裁决、B 类压制率）
4. **下游须知**（哪些规则仍有反条件、`matched` 未变）

## 8. 禁止

- 不许为了让压制率好看改阈值或删 B 类。
- 不许把「证据不足」的 C 类当 A 类删掉。
- 不许碰杨派 sex 条件（已核实非 bug）。
