# T-194 BRIEF

## 1. 改动文件

| 文件 | 说明 |
|---|---|
| `META/p1-fixed-20-blind-v1.json` | fixed-20 盲卷（20 条：四柱/性别/层/target_relation；无原文定位、无引文、无答案、无 actor） |
| `META/p1-fixed-20-answers-v1.json` | fixed-20 答案卷（actor→target + quote + quote_line + source_ref + annotation） |
| `META/p1-fixed-20.md` | 策展说明：规模、四重零校验、engine 预检表、清单、sha256、风险、B 复核清单 |
| `META/routing-questions-v1.json` | 分流题库 15 题（婚姻 4 / 事业 4 / 健康 3 / 财运 4），每题预注册宫位/关系边 ID/source_ref 区间；`access.level=restricted` |
| `META/routing-prereg-v1.json` | 预注册：证据类型、匹配规则、recall 指标、阈值（≥0.80 pass / <0.60 kill / 0.60–0.79 灰）、冻结 hash |
| `META/routing-questions-v1.md` | 分流说明：题表、证据口径、阈值、restricted、风险 |
| `tasks/T-194/verify.py` | 只依赖标准库的自检脚本（退出码 0 = 通过） |
| `tasks/T-194/BRIEF.md` | 本文件 |
| `tasks/T-194/STATUS.md` | 执行状态与 Execution Log |

未改：engine / 规则 / 测试 / 保护区 / `META/project-state.json`；未做 git 写。

## 2. 原始输出（现场跑出，非二手）

### 2.1 engine.cli 预检（20/20）

命令：`.venv\Scripts\python.exe -m engine.cli all --pillars "<四柱>" --gender <乾|坤> --json`

| case_id | 四柱 | 性别 | chart_id |
|---|---|---|---|
| F20-001 | 丁亥 庚戌 己巳 庚午 | 乾 | `cf-fee600218b19b441a567` |
| F20-002 | 甲午 丁卯 癸酉 乙卯 | 乾 | `cf-8c92d1b119d0e478e614` |
| F20-003 | 壬子 丙午 乙酉 戊寅 | 乾 | `cf-0dec002f2eece26cac6f` |
| F20-004 | 庚戌 丁亥 丁巳 癸卯 | 乾 | `cf-4594768fd80eba942916` |
| F20-005 | 己卯 丙子 丁未 甲辰 | 乾 | `cf-f8577dedd884fcbd07ec` |
| F20-006 | 乙未 丁亥 乙酉 丙戌 | 乾 | `cf-d40ec8604323278f8275` |
| F20-007 | 癸卯 丁巳 癸丑 癸亥 | 坤 | `cf-e6727a7c7df5e3351fd8` |
| F20-008 | 甲辰 丙寅 甲午 丁卯 | 乾 | `cf-14bfcbffb8e51c3493f4` |
| F20-009 | 戊申 壬戌 甲子 丙寅 | 坤 | `cf-96f4ce6c5f417964893f` |
| F20-010 | 癸巳 甲子 癸卯 癸亥 | 坤 | `cf-6119a39113ff922f390d` |
| F20-011 | 己亥 癸酉 甲寅 甲子 | 坤 | `cf-e371149459d53da99171` |
| F20-012 | 壬午 己酉 甲申 甲子 | 未注明 | `cf-d72f1e0d69bf4feb05f2` |
| F20-013 | 乙未 丁亥 甲午 丙子 | 乾 | `cf-b7ebd2f1a5f4407e4fa3` |
| F20-014 | 丙申 壬辰 丙辰 戊子 | 乾 | `cf-e45885f8f92fc0d4a7e1` |
| F20-015 | 丙午 庚寅 丙辰 庚子 | 乾 | `cf-d0bb0a9999e83c8f037e` |
| F20-016 | 丁未 壬子 甲寅 戊辰 | 乾 | `cf-afc4150ff8a4a7de18b1` |
| F20-017 | 壬子 癸丑 辛酉 乙未 | 乾 | `cf-33d0303052aba71e60ee` |
| F20-018 | 壬子 辛亥 戊午 丙辰 | 乾 | `cf-ba0095d81d3c2e1b8d57` |
| F20-019 | 戊申 丙辰 乙丑 戊寅 | 乾 | `cf-1ac2793af650af3244a6` |
| F20-020 | 辛酉 辛卯 己丑 丙子 | 坤 | `cf-efe9bf699966a8cb15e8` |

结果：**20/20 退出码 0 且返回 chart_id**。

### 2.2 四重零校验

- 四柱：20 条对 golden-20（dev-20）/ holdout-20 / fresh-40 / anchor-60 全部 0 重叠；另对 fresh-40-routing 也 0 重叠。
- 行区间（`L排盘行-L引文行`）：对四套对照集 + fresh-40-routing 的 source 区间**零重叠**；最近一条 dev 区间行距 **6 行**（F20-019 对 P1-H11）。
- 每条两个端点字在四柱地支中**各只出现一次**（20/20），无同字多位歧义。

### 2.3 sha256（先 hash）

| 文件 | sha256 |
|---|---|
| `META/p1-fixed-20-blind-v1.json` | `f7bdf96f7cb8cf58e619384948671d72ae0624205ac1ba9bf237aacb7ed743f5` |
| `META/p1-fixed-20-answers-v1.json` | `09e6e4974ae4f915946c1576a5ad5b263108098871a6d7fd2366d986659231ab` |
| `META/routing-questions-v1.json` | `580dc36a48c1602db909e95daa7ae22aa9ace8e66c334f5681c02276b9d688d4` |
| `META/routing-prereg-v1.json` | `23eba8b3aed740e5a187efcd050ae65df1af09f621a42b1867a47972284b6950` |

### 2.4 分流题库

- 题数 **15**（婚姻 4 / 事业 4 / 健康 3 / 财运 4）；证据项：宫位 35 + 关系边 32 + source_ref 30 = **97 项**。
- 阈值：macro_recall ≥ **0.80** → PASS；< **0.60** → KILL；**0.60–0.79** → GRAY（可重测一次，仍灰记灰）。
- 盘取自 fixed-20 同一批 15 盘（卡允许「同一批或新盘」）。
- 期望边已剔除该盘在 fixed-20 里被考的那一对端点（防串答案）。

### 2.5 自检

`python tasks/T-194/verify.py` → **PASS**（退出码 0）：blind 无答案/定位字段、a-b 与答案一致、引文逐字命中、
source_ref 区间在文件内且与四套对照集零重叠、20 条机制 5/5/5/5、routing 题数与计数一致、题库存量 hash 与 prereg 一致。

## 3. 未完成与风险

1. **未做双人复核**：仅 annotator A；B 由中枢另派。A 不宣称复核完成，复核清单见 `META/p1-fixed-20.md` §8。
2. **T-192 规格缺位**：`docs/specs/fact-evidence-pack-v1.md` 未产出，本卡按 PROMPT.md 执行；routing 的证据项口径由本卡自定并写入 prereg。
3. **1 条未注明性别**：F20-012（《命理指要》表格式命例）；engine 预检按乾跑通。
4. **化的 actor 有裁量**：F20-013「把亥化了」取未→亥；F20-014「原神申,辰都化入子水」只取申→子；F20-015「子水也生寅木有印化官」按化取寅→子。已在 `META/p1-fixed-20.md` §7 标注，供 B 独立判断。
5. **routing 未执行**：只做预注册；召回测需 R 工具落地后由独立 runner 跑。routing 盘与 fixed-20 同批；若上游要求另盘，需 v2。
6. **未跑评分器、未调 A+ 阈值、未做 git 写**。

## 4. 下游须知

- fixed-20 跑卷方只读 `META/p1-fixed-20-blind-v1.json`，**不得读** `META/p1-fixed-20-answers-v1.json`。
- routing 跑卷方只读 `META/routing-questions-v1.json` 的 `question_id/domain/question/chart`，**不得读** `expected_evidence` 与 prereg 的判定表以外的内容。
- 两份 JSON 已 hash 冻结：改题/改区间/改答案须另开 v2，不得原地改后沿用 v1 hash。
- 机制→kind 映射：克=`ke`、生=`sheng`、化=`hua`、墓=`muku`；`expected_direction` 全为 `actor→target`，`mutual` 全 false。
