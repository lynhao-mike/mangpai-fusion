# T-151 BRIEF · M2-Y-395 窄口重建与指纹核对

- 执行者：子代理 B
- 任务卡：`tasks/T-151/PROMPT.md`（§1 预注册未改动）
- 结论：**§1.5 指纹逐格复现**（单位＝一条 `(D.b, other)` 冲边＝一例）

## 1. 改动文件

| 文件 | 动作 | 说明 |
|---|---|---|
| `tools/m2y395_direction.py` | 新建 | 解析→建盘→方向；只 import `parse_birth`/`GENDER_MAP`，不读答案 |
| `tools/m2y395_score.py` | 新建 | 按 `period` 并入答案；输出指纹表；不做裁决 |
| `META/m2y395-cases-v1.json` | 生成 | 78 例，**不含答案**（脚本无时间戳，连跑两次 SHA256 一致） |
| `META/m2y395-scored-v1.json` | 生成 | 78 行（59 行计分），含 `answer_letter`/`options`/`correct`/`branch` |
| `META/m2y395-report-v1.md` | 新建 | 数据源/规则/指纹/差异分类/3 例抽查 |
| `tasks/T-151/STATUS.md` | 追加 | 仅追加 Execution Log 一行 |

未改动（只读）：`tools/tiekoulu_eval.py`、`engine/**`、`theory/**`、`sources/**`、既有测试、
`tasks/T-151/PROMPT.md`。未执行任何 `git` 命令。

## 2. 原始输出

### 2.1 `python -m tools.m2y395_direction`（退出码 0）

```text
==========================================================================
T-151 · M2-Y-395 题单重建（不读答案）
==========================================================================
题库期数          : 284
含婚姻题期数      : 283（缺题 1 期：第1454期）
解析/排盘失败      : 0（无）
出生时刻口径      : clock_beijing=11, true_solar=272
原局日支有冲      : 70 期
冲边（=例数）      : 78
  self_controls   : 34
  other_controls  : 25
  no_ke           : 19
  ambiguous       : 0
--------------------------------------------------------------------------
产物              : META\m2y395-cases-v1.json
```

### 2.2 `python -m tools.m2y395_score`（退出码 0）

```text
====================================================================================
T-151 · M2-Y-395 指纹核对（单位：一条 (D.b, other) 冲边 = 一例）
====================================================================================
branch             n    A    B    C    D    E   predict      hits
------------------------------------------------------------------------------------
self_controls     34    9   19    5    1    0   B           19/34
other_controls    25    8   13    2    1    1   C,E          3/25
no_ke             19    1    9    6    2    1   —               —
ambiguous          0    0    0    0    0    0   —               —
------------------------------------------------------------------------------------
合计                78
scored = 59 例（53 期）：命中 22/59 = 37.3%，Wilson95 [26.1%, 50.0%]
B 基线（同一 59 例）：32/59 = 54.2%
------------------------------------------------------------------------------------
按期口径（同一批期折叠成一行，仅作对照，非 PROMPT §1.5 口径）：
  self_controls=29  other_controls=24  no_ke=17  ambiguous=0  合计=70
  scored 53 期：命中 20/53 = 37.7%；B 基线 30/53 = 56.6%
------------------------------------------------------------------------------------
join 失败        : 0
产物            : META\m2y395-scored-v1.json
```

### 2.3 `python -m pytest -q`（退出码 0）

```text
SKIPPED [1] tests\tools\test_bundle_pii.py:34: 本地脱敏脚本缺失：…（T-114 既有 skip）
1066 passed, 1 skipped, 1 warning in 94.57s
```

两次读数：开工时（21:38）**1043 passed, 1 skipped**；全部产物落盘后（21:55）**1066 passed, 1 skipped**
（多出的 23 条来自 T-150 并行新增的 `tests/claims/test_claim_contract.py`，不是本卡加的）。
两次均 0 failed，满足卡面 `passed >= 1043`。

### 2.4 指纹逐格比对（§1.5）

| 分支 | 预期 n | 实测 n | 预期分布 | 实测分布 | 预期命中 | 实测命中 |
|---|---:|---:|---|---|---:|---:|
| `self_controls` | 34 | 34 ✓ | A=9,B=19,C=5,D=1 | 同 ✓ | 19/34 | 19/34 ✓ |
| `other_controls` | 25 | 25 ✓ | A=8,B=13,C=2,D=1,E=1 | 同 ✓ | 3/25 | 3/25 ✓ |
| `no_ke` | 19 | 19 ✓ | A=1,B=9,C=6,D=2,E=1 | 同 ✓ | 弃权 | 弃权 ✓ |
| **合计** | 78 | 78 ✓ | | | 22/59=37.3% | 22/59=37.3% ✓ |
| B 基线 | 32/59=54.2% | 32/59=54.2% ✓ | Wilson [26.1,50.0] | [26.1,50.0] ✓ | | |

## 3. 未完成与风险

### 3.1 解析失败逐类计数

`格式=0 / 缺时刻=0 / 农历转换=0 / 其他=0`，解析失败总数 **0**，排盘失败 **0**。
`parse_failures` 与 `skipped_edges` 两个列表在 cases JSON 里都是空数组（结构保留，失败会带
`stage`+`category`+`reason`，不是 `except: pass`）。

### 3.2 差异分类（PROMPT §1.6）

1. **建盘差异**：无解析失败。**11 期走了 clock_beijing 回退**（第1226/1290/1291/1292/1293/
   1294/1295/1296/1297/1298/1300期）——它们的 `line3` 写成「真太阳时: **阳历**…」，多一个前缀，
   `RE_TRUE_SOLAR` 不匹配。一次性诊断（未进产物）：改用 line3 后 10 期不变，只有
   **第1292期**从 `no_ke` 变为「无冲」→ 78→77、19→18，**59 与 22/59 不变**。
   即 §1.5 只在 `parse_birth`（含回退）口径下成立。
2. **冲边定义差异**：按 §1.2 只取 `kind=chong` + `scope=natal`；未纳入 `stem_chong`、大运/流年、
   刑穿合与「合解冲」。口径一变，78 不能直接复用。
3. **多冲/歧义**：7 期多冲（第1228/1237/1272/1484/1485/1489/1500期），方向全部一致，
   `ambiguous=0`。**78 vs 70 是计数单位差异**：一条冲边一例 → 78；一期一例 → 70。
   §1.5 的 34/25/19 只有按冲边才相加为 78。
4. **题面解析差异**：283 道「日主婚姻状况」题，每期至多 1 道，无歧义；第1454期无此题。
5. **其他**：248 期缺性别标注（用占位「乾」；实测 284 期乾/坤 `relations.edges` 序列全等）；
   晚子时 5 期、跨日 2 期未做双口径并列；题库文件名 `1507_to_1428` 与实际 1224–1507（284 期）不符。

### 3.4 并行改动耦合（重要）

`tools/tiekoulu_eval.py` **正被 T-150 并行修改**（`git status` 显示 `M`；21:39 把 L4 映射表搬到
`META/claim-instrument-map-v1.yaml`，`parse_birth` 与 `_CHONG` 逻辑未动，仅行号整体前移 2 行）。
本卡 `import` 的是该文件的 `parse_birth`/`GENDER_MAP`，因此：

- 本卡数字对应的是 21:43 时的文件状态（`parse_birth` body 与 T-146 版逐字相同）；
- 若 T-150 之后改动 `parse_birth`（正则、优先级、回退规则）或 `analyze_facts` 的建盘路径，
  **78 / 34 / 25 / 19 必须重跑再核**，不能沿用本简报的数字；
- 报告与脚本里的行号引用已按 21:43 状态更新，并以符号名（`parse_birth`/`build_periods`）为主锚。

### 3.5 没做的事

- 没有裁决「克向即制」死没死（卡面明令由中枢判）；
- 没有改 §1.2–§1.4 的规则、没有期号白名单、没有按答案筛选（`m2y395_direction.py` 里
  `grep -i "correct\|answer"` 零命中，`find_trigger_question` 只吐出题号与题干）；
- 没有接 T-150 的尺子，`scored-v1.json` 只存原始计数，未算显著性。

## 4. 下游须知

### 4.1 cases 字段（`META/m2y395-cases-v1.json`）

`meta` / `parse_failures` / `skipped_edges` / `flag_periods` / `cases[78]`。每例字段：

```text
case_id / period / period_no / pillars / day_branch / day_branch_wx / edge_id /
chong[{edge_id, other, other_wx, direction}] / direction / prediction_letters /
n_chong_in_period / time_basis / fallback / late_zi / day_boundary_shift / gender_basis
```

scored-v1.json 每例另有：`branch`、`answer_letter`、`options`、`q_index`、`correct`、
`abstained`，以及 T-150 计分器契约字段 `claim_id`（固定 `M2-Y-395`）、`triggered`（全 true）、
`outcome`（固定 `unknown`，未建模 invalidator，不写 success）。加字段前后指纹逐格一致。

- `case_id`：`tiekoulu-<期号>`；同期多条冲边时 `tiekoulu-<期号>#<edge_id>`（15 例带后缀）。
- `chong` 是该期的**全部** `D.b` 冲边；`edge_id` 才是本例对应的那一条。
- `direction∈{self_controls, other_controls, no_ke, ambiguous}`；`prediction_letters` 已按 §1.4 定死。
- `correct = null` 表示弃权，**不进分母**，不是判错。

### 4.2 哪些期无法判定

- **无婚姻题 → 不产生任何 case**：第1454期。
- **`no_ke`（无克，弃权）19 例**：`tiekoulu-1225`、`1228#e008`、`1228#e011`、`1240`、`1252`、
  `1269`、`1292`、`1309`、`1345`、`1358`、`1359`、`1371`、`1384`、`1398`、`1443`、`1446`、
  `1470`、`1484#e009`、`1484#e011`。
- `ambiguous`：0 例。

### 4.3 计分时必须注意的样本结构

78 行来自 70 期；**59 例 scored 只来自 53 个独立期**（第1237、1272、1485、1489、1500期各多计
1–2 行，共 6 行重复）。若做区间估计/显著性检验，需选口径：题级 59（会低估方差）或期级 53
（命中 20/53 = 37.7%，B 基线 30/53 = 56.6%）。本卡两种都给了数，不选边。

### 4.4 复跑

```bash
.venv\Scripts\python.exe -m tools.m2y395_direction
.venv\Scripts\python.exe -m tools.m2y395_score
```

无随机数、无时间戳；连跑两次两个 JSON 的 SHA256 一致（已实测）。
