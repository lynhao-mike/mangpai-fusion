# T-164 · 盘面地址级证据盘点（婚姻域，只读）

> 产物：`META/address-level-evidence-audit-v1.json` / `.md`；工具：`tools/address_level_evidence_audit.py`。
> 本卡只盘点，不改 `engine/**`、规则 YAML、`condition_ir`、既有测试；不建盘、不评分。

## 0. 一句话

**不够**——针对「某宫某神通过冲/合/刑/穿/制/化作用于某宫某神 + 救应三态」的完整语义：12 个婚姻信号里 0 个有地址、11 个只有聚合、1 个缺失；规则输入侧拿不到任何 e0xx 或 Y/M/D/H。

## 1. 数据与口径

| 项 | 值 |
|---|---|
| 候选案例 | 411 |
| 可用盘（usable_for_timing） | 382 |
| 婚姻质量标签盘（negative+positive） | 342 |
| 性别 | 乾 264 / 坤 118 |
| 时间基准 | clock_beijing 117 / true_solar 265 |

口径：`engine.cli` 把 `birth_dt` 当已校正的本地时间，引擎不做真太阳时换算；`time_basis=true_solar` 的 265 例按记录原值喂入，`clock_beijing` 的 117 例按钟表时间喂入，两者都不再二次校正。地址串只在这一口径下成立。

## 2. 分类结果（每条婚姻信号必须落一个桶）

- **有地址**：0 条
- **只有聚合**：11 条
- **缺失**：1 条

| 信号 | 规则 | 分类 | 方向 | 规则消费的字段 | 地址重建 | 缺口 |
|---|---|---|---|---|---|---|
| `D1_DAY_BRANCH_DISRUPTED`<br>日支受扰（冲/刑/害） | DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1 | **只有聚合** | 部分 | features.chong_pairs / features.xing_hai_pairs（字对，无地址、无边 ID） | 183/382 例可写<br>（真值 183 例，真值但无地址 0 例） | G1,G2 |
| `D2_MIXED_OFFICIAL_KILL`<br>官杀混杂（十神计数） | DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1 | **只有聚合** | 否 | features.mixed_official_kill = bool(ten_god_counts['正官'] and ten_god_counts['七杀']) | 199/382 例可写<br>（真值 199 例，真值但无地址 0 例） | G3,G4 |
| `D3_CHONG_AND_XINGHAI`<br>冲与刑害并见（布尔复合） | DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1 | **只有聚合** | 否 | bool(features.chong_pairs) and bool(features.xing_hai_pairs) | 102/382 例可写<br>（真值 102 例，真值但无地址 0 例） | G1 |
| `D4_ACTIVE_PATH_COUNT`<br>段派做功路径数（active_path_count） | DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1 | **只有聚合** | 否 | len([p for p in evaluate_zuogong(...) if p.layer_count >= 1]) | 0/382 例可写<br>（真值 382 例，真值但无地址 382 例） | G3 |
| `Y1_SPOUSE_PALACE_DISRUPTED`<br>夫妻宫被冲/刑/害 | YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | **只有聚合** | 部分 | features.chong_pairs / features.xing_hai_pairs 中 day_branch 参与的对 | 183/382 例可写<br>（真值 183 例，真值但无地址 0 例） | G1,G2 |
| `Y2_SPOUSE_STAR_WEAK`<br>配偶星弱（数量阈值） | YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | **只有聚合** | 否 | ten_god_counts[正财/偏财 或 正官/七杀] 与 has_wealth/has_official | 362/382 例可写<br>（真值 76 例，真值但无地址 20 例） | G4 |
| `Y3_PEER_COMPETITION`<br>比劫竞争（比劫计数 ≥3） | YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | **只有聚合** | 部分 | ten_god_counts[比肩]+ten_god_counts[劫财] >= 3 | 243/382 例可写<br>（真值 288 例，真值但无地址 45 例） | G1,G3 |
| `Y4_OUTPUT_SPOUSE_CONFLICT`<br>食伤重与配偶星并存 | YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | **只有聚合** | 部分 | 食伤计数 >= 4 且 spouse_present | 360/382 例可写<br>（真值 63 例，真值但无地址 0 例） | G1,G3 |
| `Y5_FEMALE_MIXED_OFFICIAL`<br>女命官杀混杂 | YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | **只有聚合** | 否 | sex == female and features.mixed_official_kill | 57/382 例可写<br>（真值 57 例，真值但无地址 0 例） | G3,G4 |
| `Y6_COMPOUND_PALACE_PAIRS`<br>夫妻宫冲刑复合（≥2 个不同字对） | YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | **只有聚合** | 否 | palace_pair_count >= 2 and palace_chong and palace_xing_hai | 102/382 例可写<br>（真值 18 例，真值但无地址 0 例） | G1 |
| `Y7_INDEPENDENT_SIGNAL_COUNT`<br>独立信号数（规则唯一主条件） | YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | **只有聚合** | 否 | sum(int(v) for v in signals.values()) | 0/382 例可写<br>（真值 —（规则级字段） 例，真值但无地址 — 例） | G1 |
| `Y8_SPOUSE_STAR_BASIS`<br>配偶星取用口径（wealth / official） | YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1 | **缺失** | 否 | spouse_star_basis = 'wealth' if male else 'official' | 0/382 例可写<br>（真值 —（规则级字段） 例，真值但无地址 — 例） | G1 |

「可写」= 用现成事实层能把该信号写成至少一条地址串的盘数（不要求信号为真）；「真值」= 按产品代码复刻的信号真值为真的盘数；「真值但无地址」= 信号真、却拼不出地址串的盘。

## 3. 地址词汇表（当前 API 可直接引用的字段）

| 字段 | 地址级 | 示例 | 覆盖 | 说明 |
|---|---|---|---|---|
| `chart.pillars[].stem.addr / branch.addr` | 是 | 乙@Y.s / 丑@Y.b | 每盘 8 个（4 干 + 4 支） | 唯一物理地址；DY{n}.* 与 LN{year}.* 由 --dayun-index / --liunian 追加 |
| `chart.pillars[].palace` | 是 | year / month / day / hour | 每盘 4 个 | 英文宫位名，与 Y/M/D/H 一一对应；中文「年/月/日/时」只在文档里 |
| `chart.pillars[].stem.ten_god` | 是 | 乙@Y.s = 七杀 | 382/382 盘有 4 个天干十神 | 日干固定为「日主」 |
| `chart.pillars[].branch.main_ten_god` | 是 | 卯@D.b = 偏印 | 382/382 盘有 4 个地支本气十神 | 只取本气；中气/余气见 hidden |
| `chart.pillars[].branch.hidden[]` | **否** | D.b 藏 己(本气,偏印)/癸(中气,食神)/辛(余气,比肩) | 每盘 8–12 个藏干，全部无独立地址 | 只能写 addr⊕char 复合串；见缺口 G4 |
| `relations.edges[]` | 是 | e010 sanhe ['D.b', 'H.b'] | 382/382 盘有边；每盘 6–22 条 | members 是地址；chars 是字；只有 sheng/ke 的 members 有序（from→to） |
| `relations.pair_index` | 是 | M.b\|D.b → [e012, e013] | 仅 `engine.cli relations` 返回；analyze_facts / `all` 裁掉 | 地址对 → 边 ID 的索引，可直接拿地址查边 |
| `relations.muku[]` | 是 | D.b=丑 的 openers=['e015', 'e016'] | 302/382 盘有墓库事实 | 开闭只给边 ID，不给开/闭结论；候选里的 damaged_by_edges 同样是地址级 |
| `duan_zuogong.candidates[].actor / members（structure_check 制用候选）` | 是 | 制用 canggan_ke members=['D.b','H.s'] actor='D.b' | 381/382 盘有候选；actor 只在 ke/sheng/canggan_ke/muku 上非空 | 冲/刑/穿/破/合用候选 actor=None（缺口 G2） |
| `duan_zuogong.tiyong` | 是 | {'D.s': '体', 'D.b': '体', 'M.s': '双属'} | 382/382 盘 8 个地址 | 体用分类是地址属性，不是结论 |
| `structures[].items[].evidence` | 是 | breaker met evidence=['e001'] | 382/382 盘有命中项 | 只覆盖子平八格；婚姻域没有对应结构（缺口 G5） |
| `strength.day_master.roots[]` | 是 | roots[0] addr=D.b hidden_char=辛 qi=余气 | 每盘若干通根项 | 藏干用 addr + hidden_char 两个字段拼，不是独立地址 |
| `shensha.hits[]` | 是 | 桃花 anchor_addr=Y.b target_addr=M.b | 382/382 盘有命中 | 明确区分锚点与目标，是现成的关系型地址词汇，但婚姻两规则不读 |
| `chart.kongwang.hits[]` | 是 | ['D.b', 'day'] | 每盘 0–8 项 | 空亡按旬取，地址级；婚姻规则不读 |
| `condition_ir.atoms.SIGNATURES` | 是 | chong_at: 必需 ('at',)；he_at: ('at',) + ('with_god','exclude_god') | 46/46 原子有地址签名；engine/ 内产品零调用 | 现成的地址级谓词层，未接任何产品规则（本卡不改、不启用） |

## 4. 三例真实盘地址串

### RF-2026-000125 · 乾 · 1987-12-18 13:15:00（clock_beijing；标签 negative）

- 四柱：`丁卯 壬子 辛丑 乙未`；日主 辛；D.b=丑（日支 / 夫妻宫）
- 复现：`python -m engine.cli relations --birth "1987-12-18 13:15:00" --gender 乾 --json`

**日支（夫妻宫）的对偶边**

- `D.b=丑 ←六合— M.b=子（edge e012）`
- `D.b=丑 ←三会— M.b=子（edge e013）`
- `D.b=丑 ←冲— H.b=未（edge e015）`
- `D.b=丑 ←刑— H.b=未（edge e016）`

**配偶星地址**（财（乾））

- `Y.b=卯 偏财（本气）`
- `Y.b⊕乙 偏财（藏-本气）`
- `H.s=乙 偏财（透干）`
- `H.b⊕乙 偏财（藏-余气）`

**配偶星被制**

- `D.b=丑（藏干）偏印 →克→ H.s=乙 偏财（zuogong 制用 canggan_ke，actor=D.b；藏干字未随候选输出，见 G4）`

**伤官制官 / 比劫夺财**

- `M.s=壬 伤官 →克→ Y.s=丁 七杀（edge e002，zuogong 制用）`
- `M.b=子（藏干）食神 →克→ Y.s=丁 七杀（zuogong 制用 canggan_ke，actor=M.b；藏干字未随候选输出，见 G4）`

**写不出来的（本例）**

- D4_ACTIVE_PATH_COUNT 在本例为真，但事实层取不到地址
- 地支克地支无 edge：Y.b=卯 克 D.b=丑、Y.b=卯 克 H.b=未、D.b=丑 克 M.b=子、H.b=未 克 M.b=子

**回 `engine.cli` 对边**

| edge | kind | members | chars | group/completeness |
|---|---|---|---|---|
| e002 | ke | M.s,Y.s | 壬丁 | - / - |
| e012 | liuhe | M.b,D.b | 子丑 | - / - |
| e013 | sanhui | M.b,D.b | 子丑 | 亥子丑 / partial |
| e015 | chong | D.b,H.b | 丑未 | - / - |
| e016 | xing | D.b,H.b | 丑未 | 丑戌未 / partial |

`engine.cli relations` 逐项比对：checked=True，mismatches=0

### RF-2026-000438 · 坤 · 1990-02-23 01:48:00（true_solar；标签 negative）

- 四柱：`庚午 戊寅 己未 乙丑`；日主 己；D.b=未（日支 / 夫妻宫）
- 复现：`python -m engine.cli relations --birth "1990-02-23 01:48:00" --gender 坤 --json`

**日支（夫妻宫）的对偶边**

- `D.b=未 ←六合— Y.b=午（edge e009）`
- `D.b=未 ←三会— Y.b=午（edge e010）`
- `D.b=未 ←冲— H.b=丑（edge e013）`
- `D.b=未 ←刑— H.b=丑（edge e014）`

**配偶星地址**（官杀（坤））

- `M.b=寅 正官（本气）`
- `M.b⊕甲 正官（藏-本气）`
- `D.b⊕乙 七杀（藏-余气）`
- `H.s=乙 七杀（透干）`

**配偶星被制**

- `Y.s=庚 伤官 →克→ H.s=乙 七杀（edge e004，zuogong 制用）`

**伤官制官 / 比劫夺财**

- `Y.s=庚 伤官 →克→ H.s=乙 七杀（edge e004，zuogong 制用）`

**写不出来的（本例）**

- D4_ACTIVE_PATH_COUNT 在本例为真，但事实层取不到地址
- 地支克地支无 edge：M.b=寅 克 D.b=未、M.b=寅 克 H.b=丑

**回 `engine.cli` 对边**

| edge | kind | members | chars | group/completeness |
|---|---|---|---|---|
| e004 | ke | Y.s,H.s | 庚乙 | - / - |
| e009 | liuhe | Y.b,D.b | 午未 | - / - |
| e010 | sanhui | Y.b,D.b | 午未 | 巳午未 / partial |
| e013 | chong | D.b,H.b | 未丑 | - / - |
| e014 | xing | D.b,H.b | 未丑 | 丑戌未 / partial |

`engine.cli relations` 逐项比对：checked=True，mismatches=0

### RF-2026-000591 · 乾 · 1990-08-17 10:21:00（true_solar；标签 unknown（不进 342 分母））

- 四柱：`庚午 甲申 甲寅 己巳`；日主 甲；D.b=寅（日支 / 夫妻宫）
- 复现：`python -m engine.cli relations --birth "1990-08-17 10:21:00" --gender 乾 --json`

**日支（夫妻宫）的对偶边**

- `D.b=寅 ←三合— Y.b=午（edge e011）`
- `D.b=寅 ←冲— M.b=申（edge e013）`
- `D.b=寅 ←刑— M.b=申（edge e014）`
- `D.b=寅 ←穿— H.b=巳（edge e018）`
- `D.b=寅 ←刑— H.b=巳（edge e019）`
- `D.b=寅 ←刑— H.b=巳（edge e020）`
- `D.b=寅 ←刑— M.b=申（edge e020）`

**配偶星地址**（财（乾））

- `Y.b⊕己 正财（藏-中气）`
- `M.b⊕戊 偏财（藏-余气）`
- `D.b⊕戊 偏财（藏-余气）`
- `H.s=己 正财（透干）`
- `H.b⊕戊 偏财（藏-余气）`

**配偶星被制**

- `M.s=甲 比肩 →克→ H.s=己 正财（edge e008，zuogong 制用）`
- `D.b=寅（藏干）比肩 →克→ H.s=己 正财（zuogong 制用 canggan_ke，actor=D.b；藏干字未随候选输出，见 G4）`

**伤官制官 / 比劫夺财**

- `M.s=甲 比肩 →克→ H.s=己 正财（edge e008，zuogong 制用）`
- `D.b=寅（藏干）比肩 →克→ H.s=己 正财（zuogong 制用 canggan_ke，actor=D.b；藏干字未随候选输出，见 G4）`
- `H.b=巳（藏干）食神 →克→ Y.s=庚 七杀（zuogong 制用 canggan_ke，actor=H.b；藏干字未随候选输出，见 G4）`

**写不出来的（本例）**

- D4_ACTIVE_PATH_COUNT 在本例为真，但事实层取不到地址
- D.b 的冲/刑/穿制用候选 4 个 actor=None：写不出「谁作用于谁」
- 地支克地支无 edge：Y.b=午 克 M.b=申、M.b=申 克 D.b=寅、H.b=巳 克 M.b=申

**回 `engine.cli` 对边**

| edge | kind | members | chars | group/completeness |
|---|---|---|---|---|
| e008 | ke | M.s,H.s | 甲己 | - / - |
| e011 | sanhe | Y.b,D.b | 午寅 | 寅午戌 / half_sheng |
| e013 | chong | M.b,D.b | 申寅 | - / - |
| e014 | xing | M.b,D.b | 申寅 | 寅巳申 / partial |
| e018 | chuan | D.b,H.b | 寅巳 | - / - |
| e019 | xing | D.b,H.b | 寅巳 | 寅巳申 / partial |
| e020 | xing | D.b,H.b,M.b | 寅巳申 | 寅巳申 / full |

`engine.cli relations` 逐项比对：checked=True，mismatches=0

## 5. 量化缺口

### 5.1 每盘可取得的地址级证据

| 指标 | 382 例 | 342 例 |
|---|---|---|
| D.b 至少一条关系边 | 369 | 330 |
| D.b 有冲/刑/穿 | 183 | 165 |
| 取得到配偶星地址 | 362 | 323 |
| 配偶星透干 | 202 | 181 |
| 配偶星仅藏支（无透干无本气） | 54 | 48 |
| 取不到任何配偶星地址 | 20 | 19 |
| 有段派做功候选 | 381 | 341 |
| 有 actor 非空的制用候选 | 378 | 339 |
| 有「日主以外克配偶星」的地址 | 171 | 153 |
| D.b 有边且取得到配偶星地址 | 349 | 311 |
| D.b 有冲/刑/穿且取得到配偶星地址（限定版最窄口径） | 173 | 155 |

比劫口径注意：`chart_feature_vector._ten_god_features` 对全部天干调 `get_shishen`，日干因此被计成「比肩」；Y3（比劫≥3）真值 288 例，但能写出 ≥3 个比劫地址的只有 243 例，差 45 例正是「日干凑数」造成的聚合/地址分歧。

### 5.2 制用候选的 actor=None

| 项 | 值 |
|---|---|
| 候选总数（全 mode） | 5685 |
| 按 mode | 制用 3179 / 化用 342 / 合用 719 / 墓用 384 / 生泄用 1061 |
| 制用候选总数 | 3179 |
| 制用候选 actor=None | 523 |
| 其中冲/刑/穿/天干冲 | 523 |
| 按 relation_kind | chong 122 / chuan 116 / stem_chong 191 / xing 94 |
| 落在 D.b 上 | 140 |
| 落在配偶星地址上 | 218 |
| 有制用候选的盘 | 378 |
| 有 actor=None 制用候选的盘 | 272 |
| 有 actor=None 冲/刑/穿制用候选的盘 | 272 |

T-149 记录的 301/56 出自它的临时探针（36 期 / 1578 对）口径；本卡按 382 例应期集重算，分母不同，结论同向：**凡是冲/刑/穿，actor 一律为空**（代码只对 `ke` 设 actor）。

### 5.3 地支克地支：事实层没有边

| 项 | 值 |
|---|---|
| 地支五克对（原局）总数 | 880 |
| 受影响盘数 | 333/382 |
| 事实层「支→支克」边数 | 0 |

### 5.4 两套关系判定的字对一致性（cfv 字对 vs relations.edges 二字边）

| 轴 | 不一致盘数 |
|---|---|
| 冲 | 0 |
| 刑/穿 | 0 |

三字齐全的刑边（寅巳申 / 丑戌未，cfv 不建三字组）共 4 条，单列、不算漂移。字对层面 0 差异说明：问题不在两套表算得不一样，而在规则只拿了字对、丢了地址。

### 5.5 候选原语核查（任务卡 §2.3 点名的三类）

| 原语 | 状态 | 在哪 | 说明 |
|---|---|---|---|
| 十神在支上的地址 | 已有 | `chart.pillars[].branch.main_ten_god（+ hidden[].ten_god）` | 本气十神可直引到 Y.b…H.b；中气/余气只能写 addr⊕char（G4），但地址本身存在。 |
| 墓库开闭 | 半有 | `relations.muku[].openers / binders / chuan_po / candidates[].damaged_by_edges` | 开闭相关的边 ID 有，开/闭结论没有（relation_graph 刻意不判）；「库被冲开」只能写边，不能写结论。 |
| 大运 / 流年引动 | 不在本卡 | `engine.cli --dayun-index / --liunian → DY{n}.s/b、LN{year}.s/b` | 地址形态已存在（scope=dayun/liunian 的边），但应期建模归 T-165，本卡不深挖。 |

## 6. 缺口清单（≤5 条）

| ID | 缺口 | 代码位置 | 优先级 | 是否缺原语 |
|---|---|---|---|---|
| G1 | 规则输入侧没接地址层：婚姻信号与关系图是两套独立的关系判定 | `engine/features/chart_feature_vector.py:133-157（_branch_relations）`<br>`engine/v5/yang_runner.py:39-92（_palace_disruption / signals）`<br>`engine/v5/duan_runner.py:251-258（_marriage_divorce_or_remarriage）` | P0（改造既有规则的前置；新规则可直接读 edges 绕过） | 接线 |
| G2 | 冲/刑/穿/破边无方向，制用候选 actor=None | `engine/facts/structure_check.py:475-478（actor = members[0] if kind == 'ke' else None）`<br>`engine/facts/types.py:167-174（Edge.members 仅 sheng/ke 有序）` | P0 | 是 |
| G3 | 地支之间不建克边；宫制星只推「支→干」，做功路径只存字 | `engine/facts/relation_graph.py:210-258（_branch_pair_edges）`<br>`engine/facts/structure_check.py:433-448（_derived_canggan_ke）`<br>`engine/energy/types.py:100-107（ZuogongPath.chain: list[str]）` | P1 | 是 |
| G4 | 藏干没有独立地址，宫制星丢了 «via» 字 | `engine/facts/types.py:69-74（HiddenStem 只有 char/qi/ten_god）`<br>`engine/claims/condition_ir/atoms.py:354-357（_ten_god_at 只取 main_ten_god）`<br>`engine/api/facade.py:99-107（_compact_zuogong 丢掉 notes）` | P1 | 是 |
| G5 | 婚姻域没有救应/反制事实，三态里的 countered_resolved 无地址承载 | `engine/facts/structure_check.py:30,332-352（仅子平八格有 met/unmet/needs_judgment）`<br>`engine/claims/condition_ir/atoms.py:666-690（structure_rescue 只读八格）` | P2 | 是 |

## 7. 结论

**不够**：针对「某宫某神通过冲/合/刑/穿/制/化作用于某宫某神 + 救应三态」的完整语义：12 个婚姻信号里 0 个有地址、11 个只有聚合、1 个缺失；规则输入侧拿不到任何 e0xx 或 Y/M/D/H。

今天就能写的**限定版**：只读 relations.edges + chart 十神 + duan_zuogong.actor，可写「D.b 对偶边 + 配偶星地址 + 干/支→干制化」两态规则。可写盘数 349/382；收窄到「D.b 有冲/刑/穿」为 173/382。其中能被「日主以外的神」克的配偶星：171 例（只算「日主以外」的神克配偶星；日主克财/官是正常取用，已排除）。

仍写不出来的句子：
- 地支之间的克（比劫夺财 / 伤官制官双方都在支上）——无 edge（G3）
- 冲/刑/穿的主客方向——actor=None（G2）
- 有忌象得救应（countered_resolved）——无救应原语（G5）

要补的原语（按优先级）：
- **P0** G2 冲/刑/穿/破边方向绑定（actor/target）——523/3179 个制用候选 actor=None
- **P0** G5 婚姻域救应/反制事实（counter-edge / rescue）——三态输出里 countered_resolved 目前无地址承载
- **P1** G3 地支克边 + 藏干地址（G4 一并）——支上制/夺与藏干端点当前不可写

接线前置：既有两条规则要变地址级，必须先在 cfv 输入侧接 relations.edges；新规则可直接读 edges 绕过。

## 8. 复现

```bash
.venv\Scripts\python.exe -m tools.address_level_evidence_audit
.venv\Scripts\python.exe -m pytest -q
```

产物不含运行时间戳，两次运行逐字节一致；输入以 sha256 记录。
