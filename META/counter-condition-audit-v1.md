# T-156 · 反条件语义审计表（v1）

- 审计对象：`theory/production/claim-rules-v1.yaml` 的 10 条生产规则
- 判据：`tasks/T-156/PROMPT.md` §2 的 A/B/C 预注册 + 每条规则 `conclusion_template` / `confidence_basis` 原句
- 结果：**A 类 7 条（删反条件）/ B 类 3 条（原文保留）/ C 类 0 条（无待人类裁决项）**
- 硬约束：`matched` 未改；v1 / v2 干跑的 `n_evaluated` / `n_matched` / `n_triggered` **逐条相同**
- 产物：`META/rule-contract-dryrun-v2.{json,md}`（v1 原字节已按 SHA256 还原，未被覆盖）

分类定义（卡面 §2 原文口径）：

| 类 | 判据 | 动作 |
|---|---|---|
| **A** | 反条件用与正条件**相同 fact**，且结论/依据明确把「至少 x / 多项 / 有冲动 / 失衡」写成正条件阈值 → 阈值点上正反同时成立，与结论自相矛盾 | 删除（`counter_conditions: []`） |
| **B** | 反条件用**不同 fact**，且结论/依据有对应语义（「冲动信号同向」「信号接近时不输出」「无有效做功路径」） | 保留原文 |
| **C** | 不同 fact 但找不到语义依据，或阈值重叠但结论措辞不支持删除 | 不动，列待人类裁决（本次 0 条） |

## 1. 汇总

| 类 | 条数 | 规则 |
|---|---:|---|
| A | 7 | `DUAN-EVENT-CAREER-PATH-MIXED-V1`、`DUAN-EVENT-WEALTH-DEBT-V1`、`DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1`、`GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1`、`GAO-HEALTH-SYSTEM-RISK-MODERATE-V1`、`GAO-HEALTH-SYSTEM-RISK-HIGH-V1`、`YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` |
| B | 3 | `DUAN-EVENT-CAREER-ROLE-CHANGE-V1`、`DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1`、`DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1` |
| C | 0 | — |

## 2. 逐条审计表

| 类 | rule_id | 反条件原文 | 结论 / 依据原句（逐字） | 动作 | 理由（阈值证据） |
|---|---|---|---|---|---|
| A | `DUAN-EVENT-CAREER-PATH-MIXED-V1` | `branch_conflict_intensity <= 0.4` | 依据：「官印任职与食伤财经营信号均达到门槛，并有冲动及有效做功路径；单侧信号不足时不输出。」 | 删 | 同 fact：正条件 `branch_conflict_intensity >= 0.35` 即「有冲动」的阈值；重叠区间 `[0.35, 0.4]`，bci=0.35 时正反同真。原文是「有冲动」而非「强冲动」 |
| A | `DUAN-EVENT-WEALTH-DEBT-V1` | `support_drain_imbalance <= 3` | 结论：「段派原局显示财富承压、比劫竞争与做功失衡同向，存在形成显著债务或长期负债的风险。」 | 删 | 同 fact 同阈值：正条件 `>= 3`、反条件 `<= 3`，重叠点 `{3}`；「做功失衡」即正条件阈值 |
| A | `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | `independent_signal_count <= 2` | 结论：「段派原局至少两组独立婚姻事件信号同向，支持一生中存在离婚或再婚事件风险，但不作必然判断。」 | 删 | 同 fact 同阈值：「至少两组」= 正条件 `>= 2`；重叠点 `{2}` |
| A | `GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1` | `pressure_signal_count <= 2` | 依据：「财星达到最低门槛，并至少有两项比劫竞争、克泄耗失衡、支冲突或五行偏枯代理同向；未使用神煞或应期输入。」 | 删 | 同 fact 同阈值：结论的「复合」在依据里量化为「至少有两项」= 正条件 `>= 2`；重叠点 `{2}` |
| A | `GAO-HEALTH-SYSTEM-RISK-MODERATE-V1` | `risk_signal_count >= 2` | 结论：「高派结构风险分层为 moderate：多项原局结构代理同向，仅表示系统性健康风险旁证，不替代专业评估。」 | 删 | 同 fact：正条件是 `>= 2` **且** `<= 2`，反条件被正条件**逻辑蕴含** → 凡正条件成立必 fail（v1 实测 90/90） |
| A | `GAO-HEALTH-SYSTEM-RISK-HIGH-V1` | `risk_signal_count <= 3` | 结论：「高派结构风险分层为 high：多项原局结构代理同向，仅表示较高的系统性健康风险旁证，不替代专业评估。」 | 删 | 同 fact 同阈值：正条件 `>= 3`（high 档起点）、反条件 `<= 3`，重叠点 `{3}`；「多项」在本条即 ≥3 档 |
| A | `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | `independent_signal_count <= 2` | 结论：「杨派原局至少两类独立婚姻事件信号同向，存在离婚或再婚事件风险，但不作必然判断。」 | 删 | 同 fact 同阈值：「至少两类」= 正条件 `>= 2`；重叠点 `{2}`。**未触碰** `sex truthy` 与 `sex falsy` |
| B | `DUAN-EVENT-CAREER-ROLE-CHANGE-V1` | `branch_conflict_intensity <= 0.34` | 结论：「段派原局的财官事业结构与做功、冲动信号同向，支持一生中出现显著岗位、职责或职业角色变化。」 | 留 | 正条件不含 bci（只测 `movement_structure` 为真）；反条件语义（释义，非原文）= 冲动信号不足则不输出，与结论原句「与做功、冲动信号同向」对应 → 独立反证。压制 113/176（64.2%）属校准风险 |
| B | `DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1` | `active_path_count <= 0` | 结论：「段派原局结构支持主要职业路径归为受雇任职。」 | 留 | 正条件不含 `active_path_count`；反条件语义（释义，非原文）= 无有效做功路径即不输出（结构不落地）。依据出处见 §3.10（卡面所引原句不属本条） |
| B | `DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1` | `employment_score >= 2` | 依据：「食伤财经营信号明显高于官印任职信号，并存在有效做功路径；信号接近时不输出。」 | 留 | 正条件不含 `employment_score`；反条件语义（释义）= 任职信号达 2 即视为接近，不输出；对应依据原句「信号接近时不输出」。压制 72/78（92.3%）属校准风险 |

## 3. 逐条证据（阈值与重叠点）

### 3.1 A 类：为什么删

1. **`DUAN-EVENT-CAREER-PATH-MIXED-V1`**：正条件 `branch_conflict_intensity >= 0.35`，反条件 `<= 0.4`。
   依据原文「并有冲动及有效做功路径」把「冲动」写成结论要素，其阈值就是正条件的 `0.35`；
   在 `bci ∈ [0.35, 0.4]` 上「有冲动」与「冲动不足」同时成立 → 自相矛盾。
   卡面提示「若原文是『强冲动』则改判 C」；本条依据原句是「并有冲动及有效做功路径」——
   「冲动」前没有「强」字，故 A 成立。

2. **`DUAN-EVENT-WEALTH-DEBT-V1`**：正 `support_drain_imbalance >= 3`、反 `<= 3`；
   结论「做功失衡」与依据「克泄耗失衡」指的就是这个 ≥3 的结构量，`imbalance = 3` 时正反同真。

3. **`DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1`**：结论「至少两组」+ 依据「至少两项」= 正条件 `>= 2`，
   反条件 `<= 2`；`independent_signal_count = 2`（干跑里 121 例即此点）时正反同真。

4. **`GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1`**：结论说「复合出现」，依据把它量化为「至少有两项」，
   即正条件 `>= 2`；反条件 `<= 2`，`pressure_signal_count = 2`（干跑 84 例）时正反同真。

5. **`GAO-HEALTH-SYSTEM-RISK-MODERATE-V1`**：正条件 `risk_signal_count >= 2` 且 `<= 2`，反条件 `>= 2`
   被正条件**逻辑蕴含**——不是阈值重叠，而是反条件恒真。这也是 v1 里 90/90 全 fail 的原因。

6. **`GAO-HEALTH-SYSTEM-RISK-HIGH-V1`**：正条件 `risk_signal_count >= 3`（high 档起点），反条件 `<= 3`；
   `= 3` 时正反同真。结论「多项原局结构代理同向」在本条对应 ≥3 档（档位由 `>= 3` 划出）；
   即便把「多项」读作「≥2」，3 仍是正条件阈值且被 `<= 3` 覆盖 → 仍矛盾，不改变 A 的判断。

7. **`YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1`**：结论「至少两类」+ 依据「至少两类独立信号同向」= 正条件 `>= 2`，
   反条件 `<= 2`；`= 2`（干跑 139 例）时正反同真。
   **本卡未碰** `{fact: sex, op: truthy, value: true}`：它表示「性别已知」，规则性别中立，
   `male` / `female` 两个非空字符串同真为正确行为；`exclusions` 里的 `{fact: sex, op: falsy}` 同样未动。

### 3.2 B 类：为什么留

8. **`DUAN-EVENT-CAREER-ROLE-CHANGE-V1`**：`branch_conflict_intensity` 出现在 `required_facts` 里但不是正条件
   （正条件只要求 `movement_structure` 为真）；结论「与做功、冲动信号同向」为反条件提供语义：
   `bci <= 0.34` = 冲动信号不足 → 不输出。不同 fact、不构成阈值矛盾 → 保留。
   代价：v1 里 176 条触发中 113 条（64.2%）会被它压掉——这是阈值校准问题，需另卡由人类裁决。

9. **`DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1`**：`employment_score` 不在正条件里（正条件用
   `entrepreneurship_advantage >= 3`）；依据明写「信号接近时不输出」，`employment_score >= 2` 就是
   任职信号已接近的操作化 → 保留。代价：72/78（92.3%）压制率属校准风险。

10. **`DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1`**：`active_path_count` 不在正条件里；反条件语义
    （释义，非原文）= `active_path_count <= 0` 即无有效做功路径 → 结构不落地。
    **依据出处必须写明**：卡面预注册行引的「存在有效做功路径」原句属
    `DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1` 的 `confidence_basis`，不在本条的
    `conclusion_template` / `confidence_basis` 里（可 grep 验证）。本条判 B 的依据是三条旁证：
    ① `active_path_count` 已列入本条 `required_facts`；② 本条 `source_refs` 的 M1-D-009 / §17.3 做功
    条目 `supports` 原文「支持用结构作用关系审计职业路径。」；③ 4 条姊妹规则把同一语义写成正条件
    `{fact: active_path_count, op: gte, value: 1}`。干跑压制 0/77，保留零成本。
    若中枢采用「依据必须本条逐字」的严口径，本条降 **C**（动作不变：保留，不影响 v2 数字）。

### 3.3 C 类：0 条

没有任何规则落进「不同 fact 又找不到语义依据」：3 条非 A 的规则都找到了对应语义（见 §3.2）。
因此本次**没有待人类裁决的删除项**；需要人来定的是 B 类的压制率（校准），不是删不删。

## 4. v1 / v2 干跑对照（同一 382 例语料）

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

- `n_evaluated` 逐条相同（合计 2219），`n_cases=382`、`n_built=382`、`n_build_failed=0` 两版一致。
- 被压掉的 641→185 条 = 只来自 B 类的 3 条规则（113 + 0 + 72），A 类全部归零。
- `matched == triggered` 两版都是 `True`（`matched` 语义未改）。

## 5. 不变式与校验

1. **`matched` 未改**：`engine/claims/rule_loader.py`、runner、`matched=` 表达式一个字未动；
   v1/v2 的 `n_matched` 逐条相同（§4）；`matched == triggered` 仍为 `True`。
2. **正条件 / 阈值 / 结论 / B 类未改**：`git diff theory/production/claim-rules-v1.yaml` 只有 7 处
   （`7 insertions(+), 14 deletions(-)`），全部是 `counter_conditions` 块删除；B 类
   `counter_conditions` 原文保留（`tests/claims/test_counter_conditions.py` 快照断言）。
3. **杨派 `sex` 条件未碰**：`conditions` 的 `sex truthy`、`exclusions` 的 `sex falsy` 均逐字保留在快照里。
4. **原句逐字**：本表 §2/§3 中归到某条规则的 **28** 个结论/依据引用片段，已用脚本对该规则的
   `conclusion_template` / `confidence_basis` 逐条做 `in` 校验，全部命中。
   唯一跨规则的引用是 §3.10 明确标注的「存在有效做功路径」——它属 `ENTREPRENEURSHIP` 的
   `confidence_basis`，用途是指出卡面出处笔误，**不**用于支持本条的 B 判断；
   同段引用的「支持用结构作用关系审计职业路径。」取自同一规则的 `source_refs[].supports`。
5. **测试**：`tests/claims/test_counter_conditions.py`（38 例）固定分类、边界行为与逐字快照。
6. **既有测试的两处重新基线（均由中枢书面裁决，断言强度不变）**：
   - `tests/claims/test_rule_contract.py`：按卡 §9.1 把「正反重叠 → fail」用例改为用
     `dataclasses.replace(rule, counter_conditions=(RuleCondition(...),))` 显式钉住旧反条件，
     三条原断言（`matched_counter_conditions` 非空 / `outcome == "fail"` / `matched is True`）原样保留，
     另加 `assert production_rule.counter_conditions == ()`——测试与生产 YAML 解耦，不是把红改绿。
   - `tests/test_production_entrypoints_unchanged.py`：文件里针对 `claim-rules-v1.yaml` 的
     变更检测器重新基线（`HISTORICAL_SHA256` 那两项未动；只替换哈希值 + 一行 T-156 注释），
     下一次未经授权的 YAML 改动仍会报警。

## 6. 复跑与 v1 保护

`tools/rule_contract_report.py` 第 52–53 行硬编码输出
`META/rule-contract-dryrun-v1.{json,md}`，跑一次就会覆盖 v1。本次流程是：

1. 备份 v1（SHA256 见下）→ 2. 跑 `python -m tools.rule_contract_report` → 3. 把新输出整体复制为
`META/rule-contract-dryrun-v2.{json,md}`（只额外写 `task` / `provenance` / 标题与出处说明，数字未重算）
→ 4. 用备份还原 v1 并校验 SHA256。

| 文件 | SHA256 |
|---|---|
| `META/rule-contract-dryrun-v1.json`（未改） | `E3ED1318CF12E3FF41D3F4C3646414D6DBBB8637544988D34BD2B84A4C5AD10A` |
| `META/rule-contract-dryrun-v1.md`（未改） | `A68311AB55DB4BFD4474258CBB2B4C95541808122D6422765463C4FC4CC1EF7C` |
| `META/rule-contract-dryrun-v2.json` | `4B7B9EA4023CBF962D4D700A7C86FE3587A57A0F1792D87E53BB43596C054015` |
| `META/rule-contract-dryrun-v2.md` | `CAD1CA7C1AF8733A43FD7D41E851F43DB3D8CF3C37FE5FCF8E7A992D846A0B88` |
| 工具原始输出（JSON，v2 的上游） | `1FA11CA4DE826876DA35017077E8C042004539075CFCFFA41E26F024BD4FAC87` |
| 工具原始输出（MD，v2 的上游） | `0F27FD42552584AFCDFDAE778CB3E42FEFB1636EA258C7624057C85B1B94D814` |

连跑两次工具：两次均 `exit code 0`，两次原始输出逐字节一致（上面两个「原始输出」哈希在两次运行中相同）；
随后 v1 两次都被还原成表中的原值，`git status` 对 v1 为空。

**下游复跑 v2 的正确姿势**（在工具加 `--out` 参数之前）：先备份 v1 两个文件 → 跑工具 →
把 `v1` 产物复制成 `v2` → 还原 v1 备份。直接跑工具只会刷新 v1。

## 7. 与卡面预注册表的偏差

| 项 | 卡面预注册 | 本表结论 | 说明 |
|---|---|---|---|
| 7 条 A 类 | A 删 | A 删 | 逐条回原文确认，无改判 |
| `DUAN-EVENT-CAREER-PATH-MIXED-V1` | 「若原文是『强冲动』则改判 C」 | A | 依据原句是「并有冲动及有效做功路径」，「冲动」前无「强」字 |
| `GAO-WEALTH-DEBT-…` | 回原文确认「复合」= 至少 2 | A | 依据明写「至少有两项」 |
| `DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1` | B（依据「存在有效做功路径」） | B（依据出处不同） | 该原句实属 ENTREPRENEURSHIP；判 B 的旁证见 §3.10，严口径可降 C |
| C 类 | 允许存在 | 0 条 | 无「不同 fact 且无语义依据」的规则 |
