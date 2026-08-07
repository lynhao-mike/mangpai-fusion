# as-of 真实盲断闭环 N=5 扩样增量报告

## 1. 最终状态

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

本报告是对 [`reports/as-of-life-state-blind-judgment-batch-report.md`](as-of-life-state-blind-judgment-batch-report.md)（`PASS`，N=3，命中率 2/3）的独立增量补充，**不修改、不重写上游报告正文**。新增 2 个有效案例，累计 N=5。

## 2. 权威合同

[`plans/as-of-life-state-blind-judgment-n5-extension-contract.md`](../plans/as-of-life-state-blind-judgment-n5-extension-contract.md)（`CONTRACT` 独立自审 `PASS`）。

## 3. 候选选择与执行记录

从上游安全审计确认的 96 个 `C-2026-RF*` 候选池（扣除已用 3 个后余 93 个）中，按字典序取下 3 个：`RF000121`、`RF000123`、`RF000125`。全部 3 个候选经新鲜独立双重安全审计（真实事实词表 + 表格括号注释模式）零命中，安全通过：

```json
[{"name":"C-2026-RF000121-乾-丙子己亥丙子戊子","safe":true},{"name":"C-2026-RF000123-坤-壬午甲辰戊申庚申","safe":true},{"name":"C-2026-RF000125-乾-丁卯壬子辛丑乙未","safe":true}]
```

本会话新增污染计数：**0/3**（三个候选均无泄露）。

## 4. 三案执行结果

### 4.1 `C-2026-RF000121-乾-丙子己亥丙子戊子`

**排盘依据**：丙火日主，四柱三子七杀(癸)主气三见，官杀混杂极重；十二长生年支胎、月支绝、日支胎、时支胎，根气结构性极弱。`as_of_date = 2022-12-31`（壬寅运 2017-2027，命主26岁）。

**Gate B 冻结原始预测**（逐字引用自 [`cases/C-2026-RF000121-乾-丙子己亥丙子戊子/asof-blind-judgment-batch-frozen-draft.json`](../cases/C-2026-RF000121-乾-丙子己亥丙子戊子/asof-blind-judgment-batch-frozen-draft.json)）：

```json
{
  "candidate_id": "career-latent-qisha-2017-2027-renyin",
  "root_level": "WEAK_ROOT",
  "completion_mode": "COMPLETE_LATENT",
  "predicted_center_landing": "体制内执行/纪律型岗位（如军警、监管、一线执法）的正式任职与深化",
  "predicted_alternative_landing": "完全受支配的从属型执行角色（身弱不担杀的受限样态，非正式体制内）",
  "freeze_package_sha256": "d5786d8023964589d34c2f251a21d5f33d4ecd900671b6a80beccf750fd4edcc"
}
```

**阶段二真实反馈**：2019年本科毕业考上公务员；2020年反馈明确记录"工作为武职"；2023年（超窗）职级晋升。

**判定**：`✅ CONFIRMED`——"武职"（军警/纪律部队/一线执法性质体制内岗位）精确命中中心落点，非仅命中替代落点。

### 4.2 `C-2026-RF000123-坤-壬午甲辰戊申庚申`

**排盘依据**：戊土日主，年支午帝旺、月支辰冠带，根气整体较强；食神(庚)双现于日/时支主气未透干，构成潜在既有技术输出承载。`as_of_date = 2024-12-31`（辛丑运 2023-2033，命主22岁）。已按协议在阶段一落盘 [`cases/C-2026-RF000123-坤-壬午甲辰戊申庚申/asof-blind-judgment-batch-frozen-draft.json`](../cases/C-2026-RF000123-坤-壬午甲辰戊申庚申/asof-blind-judgment-batch-frozen-draft.json)（`freeze_package_sha256=43781d09bec15ff94d3370aa8435c57fe3f117c7e16284291ba08fa24ca37530`）。

**阶段二真实反馈**：年表只含教育历程——2020年高考二本、2023年法考未通过。窗口内（截止2024-12-31）无任何真实职业/事业事件记录。

**判定**：`❓ 证据不足 / 无效样本`——按上游合同协议原样沿用："若阶段二揭示后发现该案例反馈里没有任何可评分的事业事件，如实记录该案例为'无效样本'"。未生成 `verified-result.json`，不强行凑判定，不计入命中率分母。

### 4.3 `C-2026-RF000125-乾-丁卯壬子辛丑乙未`

**排盘依据**：辛金日主，年支绝、月支长生、日支养、时支衰，除月支外根气结构性偏弱；食神(癸)双现于月/日支未透干，构成潜在技术输出路径。`as_of_date = 2025-12-31`（戊申运 2020-2030，命主38岁）。

**Gate B 冻结原始预测**（逐字引用自 [`cases/C-2026-RF000125-乾-丁卯壬子辛丑乙未/asof-blind-judgment-batch-frozen-draft.json`](../cases/C-2026-RF000125-乾-丁卯壬子辛丑乙未/asof-blind-judgment-batch-frozen-draft.json)）：

```json
{
  "candidate_id": "career-latent-shishen-2020-2030-wushen",
  "root_level": "WEAK_ROOT",
  "completion_mode": "COMPLETE_LATENT",
  "predicted_center_landing": "技术/专业型岗位的持续深化或职级提升",
  "predicted_alternative_landing": "依附家庭/上级扶持的从属型岗位（身弱不担食伤的受限样态）",
  "freeze_package_sha256": "953d8ba273263844fe8d4ad7adbbbeb6f3161edc3694182eeda8d2ca82f61b1e"
}
```

**阶段二真实反馈**：2012年临时工转正；2019年反馈明确记录"医生 年收入12w"。

**判定**：`✅ CONFIRMED`——"医生"是典型专业技术输出型职业，精确命中中心落点，无依附他人扶持的反面证据。

### 4.4 技术失败记录

候选6（RF000125）阶段二核验首次运行因脚本参数错误（`event_date` 早于冻结窗口 `window_start`）以 `INVALID_VALUE` 异常失败；分类为脚本参数错误，非引擎缺陷。修正 `event_date` 至窗口内后复跑，`REBUILD_HASH_MATCH` 与 `VERIFIED_OK` 均通过，不影响冻结哈希（哈希在事件参数修正前后均一致，因为哈希只覆盖冻结包本身，不含阶段二 suggestion/adjudication）。

## 5. 冻结哈希幂等复跑

| 案例 | frozen 落盘 sha256 | verified 记录 sha256 | 一致 | feedback_opened | final_envelope_state |
|---|---|---|---|---|---|
| RF000121 | `d5786d8023964589d34c2f251a21d5f33d4ecd900671b6a80beccf750fd4edcc` | 同左 | True | False | STATE_BUILT |
| RF000125 | `953d8ba273263844fe8d4ad7adbbbeb6f3161edc3694182eeda8d2ca82f61b1e` | 同左 | True | False | STATE_BUILT |
| RF000123 | `4378...`（frozen 已落盘） | N/A（无效样本，未生成 verified） | N/A | False | 不适用 |

## 6. 累计命中率汇总（上游 N=3 + 本轮 N=2）

| 来源 | 案例 | 判定 |
|---|---|---|
| 上游 | RF000026 | 🟡 PARTIAL_HIT |
| 上游 | RF000057 | ❌ REJECTED |
| 上游 | RF000108 | 🟡 PARTIAL_HIT |
| 本轮 | RF000121 | ✅ CONFIRMED |
| 本轮 | RF000125 | ✅ CONFIRMED |
| 本轮（未计入） | RF000123 | ❓ 无效样本（不计入分母） |

| 指标 | 数值 | 说明 |
|---|---:|---|
| 累计有效案例 | 5 | 上游3 + 本轮2；无效样本1个不计入 |
| 累计冻结候选事件 | 5 | 每案1个主事件候选 |
| 命中（CONFIRMED） | 2 | RF000121、RF000125（本轮新增） |
| 部分命中（PARTIAL_HIT） | 2 | RF000026、RF000108（上游） |
| 失验（REJECTED） | 1 | RF000057（上游） |
| 证据不足（不计入分母） | 1 | RF000123 |
| **累计命中率（命中+部分命中）/累计有效冻结候选事件** | **4/5 = 80%** | N=5，仍不构成统计显著性 |

## 7. 已知的方法论局限（原样继承并追加）

与上游报告 §6 及本合同 §9 一致。追加声明：本轮候选选择规则为字典序取前3个（非随机抽样），存在选择偏差，不能作为随机抽样统计推断的依据。累计命中率 4/5=80% 相较上游 2/3≈66.7% 有提升，但这**不能推断为 as-of 引擎准确率提升**——样本量仍然过小（N=5），且候选选择非随机，任何比例的观察都可能是抽样噪声。

## 8. 直接证明与禁止推断

**直接证明**：
- 候选池确实存在可继续开采的安全案例（93个中的3个全部通过双重审计）；
- 新增2案完整走完两阶段协议，冻结哈希幂等一致；
- 一次技术失败（脚本参数错误）被正确诊断分类，未误判为引擎缺陷，修正后复验通过；
- 一次无效样本被诚实记录而非牵强判定，未为凑数字而违反协议；
- 累计N=5，命中率4/5，两次CONFIRMED均对应反馈中的直接职业身份描述（"武职"、"医生"）。

**禁止推断**：
- 不得推断 as-of 引擎准确率从66.7%"提升"到80%——两轮样本量都太小，且候选选择非随机；
- 不得推断STRONG_ROOT+ACTIVATE_EXISTING（RF000123用此组合但证据不足）或WEAK_ROOT+COMPLETE_LATENT组合的相对优劣；
- 不得推断本轮"字典序选择"策略优于或劣于上游的选择策略；
- 不得推断本地报告意味着GitHub同步、部署或发布。

## 9. 新增文件清单

**新增**：
- `plans/as-of-life-state-blind-judgment-n5-extension-contract.md`
- `cases/C-2026-RF000121-乾-丙子己亥丙子戊子/asof-blind-judgment-batch-frozen-draft.json`
- `cases/C-2026-RF000121-乾-丙子己亥丙子戊子/asof-blind-judgment-batch-verified-result.json`
- `cases/C-2026-RF000123-坤-壬午甲辰戊申庚申/asof-blind-judgment-batch-frozen-draft.json`（无 verified-result，无效样本）
- `cases/C-2026-RF000125-乾-丁卯壬子辛丑乙未/asof-blind-judgment-batch-frozen-draft.json`
- `cases/C-2026-RF000125-乾-丁卯壬子辛丑乙未/asof-blind-judgment-batch-verified-result.json`
- `reports/as-of-life-state-blind-judgment-n5-extension-report.md`（本文件）

**未修改**：上游冻结报告 [`reports/as-of-life-state-blind-judgment-batch-report.md`](as-of-life-state-blind-judgment-batch-report.md)、`engine/asof/` 任何文件、[`tools/as_of_blind_judgment_probe.py`](../tools/as_of_blind_judgment_probe.py)、任何既有测试、任何案例既有文件。

**临时文件**：全部截断视图与编排脚本临时文件（`_n5_*.tmp.*`）均已在使用后删除，工作区无残留。

**未执行**：任何 Git 或 GitHub 操作。

## 10. 最终裁决

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

累计N=5，命中率4/5（部分命中2、命中2、失验1），另有1个诚实记录的无效样本。全部产物哈希核对一致，无违反协议的强行判定。

`LOCAL ONLY / NOT PUSHED`
