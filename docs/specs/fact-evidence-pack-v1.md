# 事实证据包 v1（R-tool）· 规格

- 状态：🔵 Ready（待 T-193 / T-194 执行第一证明点）
- 任务：`tasks/T-192/PROMPT.md` §3
- 依据：A+ v1.3 方向产品 kill（`docs/reviews/t191-a-plus-verdict-v1.md`）；T-193 事实审计；T-194 fixed-20 + 分流预注册
- 定位：R-tool 只做 **事实 + 检索 + 证据包**；不做方向、不做裁决、不给断语。
- 与方向产品的关系：方向产品 `DISPOSITION: KILLED`；本规格是其保留层（事实/分流/检索）的重新收口，不是复活。

## 0. 一句话

R-tool 接收「一个问题 + 一个盘」，输出一份可回查的 **事实证据包**：盘面事实、关系边、宫位、原文锚点、缺口与不可断言清单。
它**不输出冲/合/穿/刑方向**，**不输出主次裁决/断语**；固定克/生/化/墓只作事实发射。

## 1. 范围

### 1.1 输入

| 输入 | 必填 | 说明 |
|---|---|---|
| 盘 | 是 | 四柱 + 性别，或出生信息；实际排盘只经 `python -m engine.cli` |
| 问题 | 是 | 自然语言问题；域标签 ∈ `{marriage, career, health, wealth, other}`，由预注册问题集给定 |
| 快照 | 否 | `dayun_index` / `liunian_year`；缺省为原局（两者均为 `null`） |
| 预注册 ID | 是（评测时） | 对应 `META/routing-prereg-v1.json` 的 `question_id`；演示可空 |

输入只读。R-tool 不写 `engine/`、答案、测试或任何保护区文件（§5）。

### 1.2 事实来源（唯一）

1. **盘面事实**：`python -m engine.cli all|chart --json`（排盘、十神、藏干、旬空、关系边、墓库、体用、strength 等）。
2. **理论检索**：`python -m tools.query_theory ... --json`（`entry_id` / `source_ref` / 原文行）。
3. **原文核对**：`sources/` 下 `source_ref` 指向的行；引文必须逐字。

不得心算排盘，不得自造干支关系、长生、空亡、神煞、起运；不得用原文反推 engine 未给出的事实边。

### 1.3 输出：证据包 JSON

```json
{
  "schema": "fact-evidence-pack/v1",
  "generated_at": "2026-10-29T20:00:00+08:00",
  "question": {"text": "...", "domain": "marriage", "prereg_id": "RQ-001"},
  "snapshot": {"chart_id": "cf-...", "dayun_index": null, "liunian_year": null},
  "facts": {
    "pillars": {},
    "ten_gods": [],
    "hidden_stems": [],
    "kong_wang": [],
    "tiyong": {},
    "muku": []
  },
  "palaces": [
    {"palace": "day", "addr": "D.b", "role": "夫妻宫", "ten_god": "...", "mapping_rule": "M-01"}
  ],
  "edges": [
    {"edge_id": "e015", "kind": "chong", "members": ["D.b", "H.b"], "scope": "natal",
     "group": null, "completeness": null, "direction": "undetermined",
     "actor": null, "target": null}
  ],
  "fixed_facts": [
    {"class": "克", "actor": "未", "target": "子", "edge_id": null,
     "basis": "engine_fixed_rule", "is_conclusion": false}
  ],
  "theory": [
    {"entry_id": "M1-D-298", "source_ref": "sources/duan/...md:L48",
     "quote": "逐字原文", "applicability": "夫妻宫结构句"}
  ],
  "evidence_items": [
    {"type": "edge", "ref": "e015"},
    {"type": "addr", "ref": "D.b"},
    {"type": "source", "ref": "M1-D-298"}
  ],
  "gaps": ["G2", "G5"],
  "non_claims": ["不判冲的方向", "不判吉凶", "不判应期"],
  "provenance": {"engine_cmd": "...", "theory_cmd": "...", "pack_version": "v1"}
}
```

字段约束：

| 字段 | 约束 |
|---|---|
| `snapshot` | 三字段必填（`null` 也写）；`edge_id` 只在该快照内有效，跨快照引用即错 |
| `palaces` | 每个 `addr` 必须存在于 `engine.cli` 的物理地址；`mapping_rule` 必须来自预注册 |
| `edges` | 只发 `engine.cli` 实际边；`kind` 保留 engine 口径；`members` 与 engine 一致 |
| `fixed_facts` | `class` 只能是 `克/生/化/墓`；`actor/target` 只能来自 engine 固定规则；`is_conclusion` 恒 `false` |
| `theory` | `source_ref` 的 `path:line` 必须可解析；`quote` 必须是该行/行区间的逐字子串 |
| `evidence_items` | 供分流召回计分：每条是宫位、边或 `source_ref` 的可回查引用 |
| `gaps` | 缺什么写什么（§4.2）；不得用猜测填补 |
| `non_claims` | 非空；必须列出本包**没有**断言的事项 |

### 1.4 输出：人读证据单

人读层只允许「事实清单」：

1. 盘面事实（四柱、十神、藏干、旬空、墓库、体用）；
2. 问题命中的宫位/地址；
3. 关系边清单（edge_id、kind、members、snapshot）；
4. 固定克/生/化/墓事实（如适用）；
5. 原文锚点与逐字引文；
6. 缺口与不可断言清单。

人读层不写段落式断语，不套 `templates/report-v7-human.md`（§5.2），不产出「结论/建议/应期」。

## 2. 硬边界：不输出方向、不输出断语

### 2.1 冲 / 合 / 穿 / 刑 / 破：只发边事实

- 输出 `direction = "undetermined"`，`actor = null`，`target = null`；
- 不输出 `mutual` 判断（“两伤/互相”也是方向裁决）；
- 不引用原文行来补单向施力方；`query_theory` 命中只能作为检索结果，不能升级为方向；
- `kind` 保留 engine 的 `chong/he/chuan/xing/po`，但 `kind` 是关系种类，不是方向。

### 2.2 固定克 / 生 / 化 / 墓：只作事实

- 允许发射 `class ∈ {克, 生, 化, 墓}` 的 `actor/target`，但必须标 `basis = "engine_fixed_rule"`、`is_conclusion = false`；
- 不得把固定事实写成「谁胜谁败」「谁克死谁」「用神/忌神」「格局成败」；
- 不得由固定事实推导事件、年份、概率、亲疏或吉凶；
- 固定事实不进入冲/合/穿/刑的边，不改变这些边的 `direction=undetermined`。

### 2.3 禁止输出清单

以下字段/语句在任何输出层都不得出现：

- 动态方向：`actor→target` / `mutual` for `chong/he/chuan/xing/po`；
- 党势方向、岁运引动方向、`party_direction`；
- 主次裁决（主/次、体用胜负）、格局成败、吉凶、应期、事件、概率、置信度结论；
- “必然/一定/说明命主……”等断语式句子；
- 由 R-tool 生成的预测、建议、化解、改运。

### 2.4 类外零发射（定义）

- **类内**：`克 / 生 / 化 / 墓` 四个固定类的方向事实。
- **类外**：`冲 / 合 / 穿 / 刑 / 破` 的方向，党势方向，岁运方向，以及其他任何方向类。
- `out_of_class_emissions` 必须为 **0**；该计数按“方向条目”计，不按边数计。
- 对任意盘、任意问题，R-tool 都不得发射类外方向；fixed-20 验收另加 §3.2 的覆盖要求。

### 2.5 3 张旧卡不进演示

- `docs/demo/single-chart-cards-v1.md` 与 `META/single-chart-cards-v1.json` 已标 `STATUS: ARCHIVED_RESEARCH_ARTIFACT`（`archive/demo/` 原样封存）；
- 3 卡（C1/C2/C3）不得作为 R-tool 演示、测试样例、能力证明或评测输入；
- R-tool 演示只用 T-194 之后的新例子（fixed-20 或新分流问题集），且必须过 §3 门禁。

## 3. 第一证明点（预注册，先冻结后跑）

R-tool 的 Go 只由下面三项共同决定；**三项都过才 Go**，任一不过即 No-Go。
阈值在看结果前冻结；不得事后移动，不得换同卷重跑到过。

### 3.1 事实审计 100%（T-193）

- 样本 ≥20 盘：晚子时（23:00–00:59）≥5、节气交界（交节前后各 1 小时内）≥5、起运边界 ≥5、普通盘 ≥5；四柱/性别/出生地/时间明确。
- 独立来源：`sxtwl` / `lunar_python` 或公开万年历表；写明来源与版本/表名；不得用本项目 engine 作为独立来源。
- 逐字段：年/月/日/时柱、日主、藏干、十神、旬空、起运岁数/交运时间（如适用）；记录 engine 值与独立值。
- **Pass = 差异 0/全部字段**；任何差异列为缺陷并单独报告，不得宣称通过。
- 覆盖必须包含晚子时、节气交界、起运边界三类；缺一类即不通过。

### 3.2 fixed-20 类外零发射（T-194）

- 20 条新盘：克/生/化/墓各 5；只给四柱/性别/`target_relation`（地支端点）；与 dev-20 / holdout-20 / fresh-40 / anchor-60 四重零重叠；无 locator；答案先 hash。
- 门禁：
  1. 每条至少发射 1 条**目标类**方向事实（`克/生/化/墓`），覆盖 20/20；
  2. **`out_of_class_emissions = 0`**（不得发射冲/合/穿/刑/破、党势、岁运方向）；
  3. 同一条不得发射第二个方向类；端点必须落在盲卷 `target_relation` 的端点集合内；
  4. fixed 不得混入 dynamic 分母；不测冲/合/穿/刑。
- 本证明点只数「类外发射」与「目标类覆盖」，不把 fixed 方向的 actor→target 对错计入 gate；
  如其他任务另行评分，不得用其对错放宽零发射门禁。

### 3.3 分流召回预注册（T-194）

- 10–20 个真实问题（婚姻/事业/健康/财运等）；每个问题在看结果前预注册应召回的证据项：宫位、关系边 ID、`source_ref` 范围。
- 召回率 = 实际召回且可回查的预注册证据项 / 预注册证据项总数；只测证据包覆盖，不测方向/断语。
- 阈值写入 `META/routing-prereg-v1.json`：**≥80% pass；<60% kill；60–79% 灰**。
- 与 fixed-20 同一批或新盘均可，但与 anchor-60 及三套 dev 集零重叠；答案/标签 restricted；blind 无 locator。
- 问题→宫位映射必须预注册；运行中不得临时加证据项来抬召回。

### 3.4 Go / No-Go

| 结果 | 处置 |
|---|---|
| 三项全过 | R-tool Go（仅事实 + 分流/检索；仍不输出方向/断语） |
| 事实审计有差异 | No-Go；先修事实，不带缺陷上线 |
| fixed-20 类外 >0 或覆盖 <20/20 | No-Go；不得用“方向更准”补偿 |
| 分流召回 <60% | No-Go；60–79% 只作灰区报告，不宣称通过 |

## 4. 证据、快照与缺口

### 4.1 快照绑定

- 每个证据包只对应一个 `snapshot{chart_id, dayun_index, liunian_year}`；
- `edge_id` 只在同一快照内有效；加岁运会重编号，禁止跨快照混用；
- 多快照问题必须拆成多个证据包，不得合并 edge_id。

### 4.2 缺口（`gaps`）必须显式

至少覆盖：`G2`（动态边无 actor）、`G3`（支 vs 支不建克边）、`G4`（藏干无独立地址）、`G5`（救应未判）、`no_spouse_star`、`muku_open_close`、`suiyun_ten_god`、`boundary_zi_shi`。
缺什么写什么；不得用原文或常识补成确定事实。

### 4.3 可回查性

- 每个宫位/边/原文锚点必须能由 `engine.cli` 输出或 `source_ref` 行独立复核；
- 引文逐字（含 OCR 空格）；不拼接、不改写、不省略到改变语义；
- 第三人只凭证据包 + CLI + 原文即可重推同一事实清单。

## 5. 保护区与呈现边界

### 5.1 保护区文件不改

R-tool 及其任务卡不得修改：

- `AGENTS.md`、`CLAUDE.md`；
- `templates/report-v7-human.md`、`docs/analysis_human_touch.md`；
- `engine/**`、规则、答案、`tests/**`、`pyproject.toml`、`requirements*.txt`；
- `theory/_ir/**` 与 `sources/**` 原文语料（只增不改，改动须走 ingestion-protocol）；
- `META/project-state.json`、`tasks/*/PROMPT.md`。

需要改上述文件时另开卡并取得明确授权；R-tool 只能读。

### 5.2 不套 `report-v7-human`

- R-tool 输出是证据包 JSON + 人读事实清单，不是 v7 报告；
- 不调用 `templates/report-v7-human.md` 的段落结构，不把证据包渲染成“命理报告”；
- `tools/human_touch_linter.py` 不作为 R-tool 的产物门禁（它服务于报告，不服务于证据包）；
- 如未来要出报告，必须另立规格并重新过方向/断语审查。

## 6. 数据与泄漏卫生

1. runner 输入白名单：盲卷 + 本规格 + `engine.cli` + `query_theory` + `sources/` 检索；不得读答案/标签/污染清单。
2. 答案、评分标签、污染清单只在 `archive/adjudication_v1/restricted/`；runner 不可读。
3. 出包前必须：

   ```powershell
   .venv\Scripts\python.exe -m tools.check_bundle_case_ids <bundle.zip|bundle-dir>
   ```

   退出码必须为 0；命中 `A60-/PF-/P1-H/G20` 任一 case_id 即退出 1，禁止交付。
4. `A60-020 / A60-046 / A60-050` 已标 `contaminated`，永久排除出 fixed-20、分流问题集、演示与任何未来盲集。
5. blind 输入不得含 `source_ref`/locator；答案与标签分离存放，先 hash 后跑。

## 7. 非目标

- 不是方向引擎、不是裁决器、不是报告生成器、不是新的理论来源；
- 不复活党势方向，不写 `party-direction-v2`；
- 不把 fixed-20/分流结果包装成“方向能力”；
- 不用 3 张旧卡做能力证明；
- 不修改 A+ v1.3 的历史结论（kill 已定，不重裁）。

## 8. 验收命令（工具齐备后）

```powershell
# 事实入口冒烟
.venv\Scripts\python.exe -m engine.cli all --pillars "庚申 戊寅 壬子 辛丑" --gender 乾 --json

# 理论检索
.venv\Scripts\python.exe -m tools.query_theory --query "夫妻宫 冲" --top-k 5 --json

# 出包泄漏门禁（合成 fixture 由 tasks/T-192/verify.py 验收）
.venv\Scripts\python.exe -m tools.check_bundle_case_ids <bundle>

# 回归
.venv\Scripts\python.exe -m pytest -q
```

事实审计与 fixed-20 的具体命令由 T-193 / T-194 的 `verify.py` 给出；本规格只冻结口径与阈值。
