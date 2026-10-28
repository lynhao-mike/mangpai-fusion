# T-164 BRIEF · 盘面地址级证据盘点（婚姻域，只读）

- 状态：Worker 完成，待中枢验收
- 任务卡：`tasks/T-164/PROMPT.md`
- 产物：`tools/address_level_evidence_audit.py`、`META/address-level-evidence-audit-v1.json`、`META/address-level-evidence-audit-v1.md`、`tests/tools/test_address_level_evidence_audit.py`

## 1. 改动文件

| 文件 | 类型 | 说明 |
|---|---|---|
| `tools/address_level_evidence_audit.py` | 新建 | 只读审计：382 例扫描 + 12 信号映射 + 3 例地址串 + 缺口 + CLI 回放 |
| `META/address-level-evidence-audit-v1.json` | 新建 | 机器可读盘点（无时间戳，两次运行逐字节一致） |
| `META/address-level-evidence-audit-v1.md` | 新建 | 人读报告（同一份数据的渲染） |
| `tests/tools/test_address_level_evidence_audit.py` | 新建（可选） | 6 条确定性测试：三态分类、地址合法性、actor=None 只落在无向 kind、确定性、CLI 回放 |

未改：`engine/**`、`theory/production/claim-rules-v1.yaml`、`engine/claims/condition_ir/**`、既有测试、T-148/T-153/T-158/T-159 产物。`git status` 只多出上述 4 个未跟踪文件（另见 T-165 并行产物，未触碰）。

## 2. 原始输出

```text
$ .venv\Scripts\python.exe -m tools.address_level_evidence_audit
案件 382（标签 342）；分类 有地址 0 / 只有聚合 11 / 缺失 1
D.b 有边 369；配偶星地址 362；限定版可写 349；actor=None 523/3179
engine.cli 关系边回放：3 例，mismatches=0
已写入 META\address-level-evidence-audit-v1.json / META\address-level-evidence-audit-v1.md
EXIT=0
```

两次运行哈希一致：JSON `5720F018…F839E0F2`、MD `392B7554…F167333A`（完整 sha256 见验收时重算）。

```text
$ .venv\Scripts\python.exe -m pytest -q
1303 passed, 1 skipped, 1 warning in 123.46s   EXIT=0
```

（共享工作树里并行 T-165 也新增了 `tools/timing_feasibility_audit.py` 与其测试，故 1303 含它的用例；本卡只新增 6 条，单跑 `tests/tools/test_address_level_evidence_audit.py` 为 `6 passed`。首次基线为 1288 passed / 1 failed / 1 skipped；该 failed 是 `tests/tools/test_career_role_change_labels.py::test_audit_stale_detection`，单跑通过、复跑全量也通过，属既有跨文件顺序敏感，未改任何测试。）

### 2.1 婚姻信号分类（硬约束 2）

- **有地址 0 条**：没有任何一条规则消费的字段本身带地址。
- **只有聚合 11 条**：D1、D2、D3、D4、Y1、Y2、Y3、Y4、Y5、Y6、Y7。
- **缺失 1 条**：Y8 `spouse_star_basis`（性别→财/官的取用口径，不是盘面证据）。

| 信号 | 分类 | 规则消费 | 今天能写的地址重建 | 真值 / 真值但无地址（382） |
|---|---|---|---|---|
| D1 日支受扰 | 只有聚合 | `chong_pairs`/`xing_hai_pairs` 字对 | D.b 的冲/刑/穿边 | 183 / 0 |
| D2 官杀混杂 | 只有聚合 | `mixed_official_kill` | 官、杀各自地址 | 199 / 0 |
| D3 冲刑并见 | 只有聚合 | 两个布尔求交 | 首条 chong + 首条 xing/chuan 边 | 102 / 0 |
| D4 做功路径数 | 只有聚合 | `active_path_count` | **无**（chain 只有字） | 382 / 382 |
| Y1 夫妻宫受扰 | 只有聚合 | 同 D1 限日支 | D.b 的冲/刑/穿边 | 183 / 0 |
| Y2 配偶星弱 | 只有聚合 | 十神计数 | 配偶星逐字地址 | 76 / 20 |
| Y3 比劫竞争 | 只有聚合 | 比劫计数 ≥3 | 比劫地址（≥3 个） | 288 / 45 |
| Y4 食伤 vs 配偶星 | 只有聚合 | 食伤≥4 且配偶星在 | 食伤地址 + 配偶星地址 | 63 / 0 |
| Y5 女命官杀混杂 | 只有聚合 | 性别 + 混杂 | 官、杀各自地址 | 57 / 0 |
| Y6 宫冲刑复合 | 只有聚合 | 字对基数 | D.b 上不同边的 id 数 | 18 / 0 |
| Y7 独立信号数 | 只有聚合 | 布尔求和 | 无 | —（规则级字段） |
| Y8 配偶星取用口径 | **缺失** | 性别字符串 | 无 | —（规则级字段） |

### 2.2 三例真实盘地址串（可回 `engine.cli relations`）

**RF-2026-000125**（乾，1987-12-18 13:15，clock_beijing，标签 negative，`丁卯 壬子 辛丑 乙未`）

```text
D.b=丑 ←六合— M.b=子（edge e012）
D.b=丑 ←三会— M.b=子（edge e013）
D.b=丑 ←冲— H.b=未（edge e015）
D.b=丑 ←刑— H.b=未（edge e016）
配偶星：H.s=乙 偏财（透干）、Y.b=卯 偏财（本气）、Y.b⊕乙/H.b⊕乙（藏）
配偶星被制：D.b=丑（藏干）偏印 →克→ H.s=乙 偏财（zuogong 制用 canggan_ke，actor=D.b）
伤官制杀：M.s=壬 伤官 →克→ Y.s=丁 七杀（edge e002，zuogong 制用）
写不出：D4 的做功路径无地址；地支克对 4 组无 edge
```

**RF-2026-000438**（坤，1990-02-23 01:48，true_solar，标签 negative，`庚午 戊寅 己未 乙丑`）

```text
D.b=未 ←六合— Y.b=午（edge e009）
D.b=未 ←三会— Y.b=午（edge e010）
D.b=未 ←冲— H.b=丑（edge e013）
D.b=未 ←刑— H.b=丑（edge e014）
配偶星：H.s=乙 七杀（透干）、M.b=寅 正官（本气）、M.b⊕甲/D.b⊕乙（藏）
伤官制官：Y.s=庚 伤官 →克→ H.s=乙 七杀（edge e004，zuogong 制用）
写不出：D4 无地址；寅克未、寅克丑无 edge
```

**RF-2026-000591**（乾，1990-08-17 10:21，true_solar，标签 unknown，`庚午 甲申 甲寅 己巳`）

```text
D.b=寅 ←三合— Y.b=午（edge e011）
D.b=寅 ←冲— M.b=申（edge e013）
D.b=寅 ←刑— M.b=申（edge e014）
D.b=寅 ←穿— H.b=巳（edge e018）
D.b=寅 ←刑— H.b=巳（edge e019）
D.b=寅 ←刑— H.b=巳 / M.b=申（edge e020，三字齐全寅巳申）
比劫夺财：M.s=甲 比肩 →克→ H.s=己 正财（edge e008，zuogong 制用）
宫制财：D.b=寅（藏干）比肩 →克→ H.s=己 正财（canggan_ke）
写不出：4 个 D.b 制用候选 actor=None（冲 e013 / 刑 e014 / 穿 e018 / 刑 e019）→ 写不出「谁作用于谁」
```

三例的 `engine.cli relations` 逐项回放：`mismatches=0`（边 id/kind/members 全等，见 JSON `examples[].edge_evidence` 与 `cli_parity`）。

### 2.3 量化缺口

| 指标 | 382 例 | 342 例 |
|---|---|---|
| D.b 至少一条关系边 | 369 | 330 |
| D.b 有冲/刑/穿 | 183 | 165 |
| 取得到配偶星地址 | 362（透干 202 / 仅藏支 54 / 缺失 20） | 323 |
| 有段派做功候选 | 381 | 341 |
| 有 actor 非空的制用候选 | 378 | 339 |
| 「日主以外」克配偶星的地址 | 171 | 153 |
| D.b 有边且取得到配偶星地址 | 349 | 311 |
| D.b 有冲/刑/穿且取得到配偶星地址 | 173 | 155 |

制用候选 actor=None：**523 / 3179**（全部落在冲/刑/穿/天干冲），其中落在 `D.b` 140 个、落在配偶星地址 218 个，涉及 272 盘。T-149 的 301/56 是它临时探针（36 期 / 1578 对）口径，分母不同，勿直接对比。

地支克地支：原局 880 对、333/382 盘有，事实层**边数 0**。

两套字对一致性：冲 0 例不一致、刑/穿 0 例不一致；三字齐全刑边 4 条（cfv 不建三字组，单列）。

### 2.4 缺口清单（5 条）

| ID | 缺口 | 代码位置 | 优先级 |
|---|---|---|---|
| G1 | 规则输入侧没接地址层（cfv 另判一次，只存字对） | `chart_feature_vector.py:133-157`、`yang_runner.py:39-92`、`duan_runner.py:251-258` | P0（改造既有规则的前置） |
| G2 | 冲/刑/穿/破边无方向，制用候选 actor=None | `structure_check.py:475-478`、`types.py:167-174` | P0 |
| G3 | 地支之间不建克边；宫制星只推支→干；做功路径只存字 | `relation_graph.py:210-258`、`structure_check.py:433-448`、`energy/types.py:100-107` | P1 |
| G4 | 藏干无独立地址；`canggan_ke` 的 via 字被 Agent 视图裁掉 | `types.py:69-74`、`atoms.py:354-357`、`facade.py:99-107` | P1 |
| G5 | 婚姻域无救应/反制事实，`countered_resolved` 无地址承载 | `structure_check.py:30,332-352`、`atoms.py:666-690` | P2 |

### 2.5 结论（预注册口径）

**不够**——按复审要求的完整语义（某宫某神通过冲/合/刑/穿/制/化作用于某宫某神 + 救应三态）：12 个信号 0 个有地址；规则输入侧拿不到任何 `e0xx` 或 `Y/M/D/H`。

**够写限定版**——只读 `relations.edges` + chart 十神 + `duan_zuogong.actor`，可写「D.b 对偶边 + 配偶星地址 + 干/支→干制化」两态规则，覆盖 349/382（收窄到 D.b 有冲/刑/穿为 173/382）。

## 3. 未完成与风险

1. **「有地址 0 条」不等于事实层没有地址**：地址在 `relations.edges` / `duan_zuogong.candidates` 里，是规则不消费。按字面读会误判，报告 §3 已列出 15 类现成地址词汇。
2. **例盘是最大可写性样本**，不是随机样本（选样规则写在 JSON `method.example_selection`）；总体覆盖看 §5.1，不要用 3 例推全体。
3. **`clock_beijing` 117 例未做真太阳时校正**，`true_solar` 265 例按记录原值喂入；引擎不换算，跨时辰的地址可能差一字。本卡不改口径。
4. **cfv 把日干算成「比肩」**（`_ten_god_features` 对全部天干调 `get_shishen`）：Y3 真值 288 例，能写出 ≥3 个比劫地址的只有 243 例，差 45 例正是日干凑数。聚合口径与地址口径的具体分歧，已在报告 §5.1 写明，本卡未改。
5. **T-149 的 301/56 不可直接引用**：本卡按 382 例重算为 523/3179，结论同向（冲/刑/穿一律 actor=None）。
6. **未做**（按卡不越界）：`condition_ir` 46 原子启用、墓库开闭结论、大运/流年引动（T-165）、补任何原语、评分/断语。
7. **首次全量 pytest 出现 1 个既有 flake**（`test_audit_stale_detection`，单跑通过）；复跑全量 1295 passed / 0 failed。若中枢再遇，按既有序敏感处理，不是本卡引入。

## 4. 下游须知

1. **地址 schema 可直接给 T-165 / 单条婚姻规则**：`relations.edges[].id/kind/members/chars` + `chart.pillars[].stem/branch`（addr + ten_god）+ `duan_zuogong.candidates[].actor/members`。同一 `birth_dt` 重跑 edge id 稳定，可用 `python -m engine.cli relations --birth ... --gender ...` 逐项复核。
2. **能写什么**：D.b 的冲/合/刑/穿/破/会（对偶）、配偶星地址（透干/本气/藏干复合串）、干→干与支→干的制化（有 actor）。
3. **不能写什么**：冲/刑/穿的主客方向（G2）、支→支的克（G3）、藏干作为 edge 端点（G4）、救应三态（G5）。
4. **既有两条规则要变地址级，先补 G1**（cfv 输入侧接 `relations.edges`）；新规则可直接读 edges 绕过 G1，但仍受 G2/G3/G5 限制。
5. `duan_zuogong.candidates[].notes` 在 Agent 视图被裁掉，藏干 via 字不可得；不要从 candidates 反推「丑藏辛克乙」。
6. 本卡未改任何产品文件；`META/address-level-evidence-audit-v1.*` 可被 T-165 与本卡后续规则卡直接引用（含 sha256 输入指纹）。
