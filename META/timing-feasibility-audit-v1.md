# T-165 · 婚姻应期可行性审计（382 例，只读）

- 任务卡：`tasks/T-165/PROMPT.md`；模式：只读审计，不建模、不评分、不生成应期预测、不改 `engine/**`。
- 数据：`META/timing-eval-set-v1.json`（382 例 `usable_for_timing`）+ `META/timing-baseline-v1.json`（frozen）。
- 复现：`.venv\Scripts\python.exe -m tools.timing_feasibility_audit`（退出码 0；输出 JSON 逐字节可复现）。

## 0. 结论

**能直接开工**。矩阵 6 项中 2 项「有」、4 项「部分」、0 项「无」：suiyun_edge 直接回答夫妻宫的冲/合/刑/穿（含穿=害），chong_kai_muku 回答墓库冲/刑开，sanhe_with_suiyun 回答完整三合/三会含夫妻宫；配偶星柱需在模型层按十神地址组合 suiyun_edge。4 个「部分」项的缺口都可用现有字段组合绕过；其中合开墓库、跨年稳定 edge_id 若要补需新原语，但不阻塞最小规则集 R1–R4。

| 指标 | 数值 |
|---|---|
| 可用案例 | 382/411 |
| 可建盘 | 382/382 |
| 20–35 岁可评分年 | 6112 case-year（每例 16 年） |
| 窗口内有婚姻事件 | 292 例；90 例结构性零 |
| 原语矩阵（项） | 有 2 / 无 0 / 部分 4 |
| 原语矩阵（子项） | 有 23 / 无 7 / 部分 1（共 31） |
| 岁运原子 | 代码 6 个；卡上 4 个；漏 dayun_present, suiyun_arrives |
| 主检验 K | K=3（功效 0.919，MDE80 6.75pp） |
| 判定 | 能直接开工 |

三条硬事实先摆在这里：

1. **大运只有 2–3 个取值**：16 年跨 2 步（194 例）/3 步（188 例），任何只读大运的规则在十年内恒定，不能给 16 个年份排序；排序必须由流年原子驱动。
2. **292/382 例窗口内有事件，90 例没有**：命中率天花板 76.4%；零假设必须逐例算 `1-C(16-m_i,K)/C(16,K)`，不能用 K/16。
3. **标签噪声**：425/547 条事件文本没有年份（不可核验），74 条与文本年份矛盾，52 例的窗口内事件矛盾。

## 1. 案例可用性

| 项 | 数值 |
|---|---|
| 原始记录 / 可用 | 411 / 382 |
| birth_dt 可解析 | 382 |
| 建盘成功 / 失败 | 382 / 0 |
| 大运区间齐备 | 382 |
| 每例可评分年数分布 | {"16": 382} |
| 窗口内事件年数分布 | {"0": 90, "1": 228, "2": 45, "3": 13, "4": 4, "5": 1, "7": 1} |
| 窗口内事件 / 去重事件年 | 393 / 385 |
| 婚姻事件年落在大运区间 | 544/547（区间外 3） |
| 大运顺逆与阳男阴女一致 | 382/382（不一致 0） |
| 性别 | {"女": 118, "男": 264} |
| 质量等级 | {"A": 1, "B": 381} |
| 出生时刻口径 | {"clock_beijing": 117, "true_solar": 265} |
| 边界警告 | {"early_zi": 17, "late_zi": 21, "near_jie": 1}（39 例至少 1 条） |
| 起运年龄 | {"1.0": 65, "10.0": 18, "2.0": 36, "3.0": 43, "4.0": 30, "5.0": 37, "6.0": 32, "7.0": 39, "8.0": 45, "9.0": 37} |
| 出生年范围 | 1966–2008 |
| 无配偶星案例 | 20（例：RF-2026-000070, RF-2026-000111, RF-2026-000118, RF-2026-000143, RF-2026-000245） |

逐例覆盖（382 条）见 JSON `per_case_coverage`：每例的 `pillars`、`scoreable_years`、窗口内事件年、配偶星地址、R1–R4 点火年数。

### 1.1 基线口径核对

卡上四个基线数里有两个是 392 例口径（22–28、26 岁），与 382 例 `cleaned_reference` 不一致：

| 年龄带 | 卡上 | 382 例重算 | cleaned_reference | 392 例 card | 判定 |
|---|---|---|---|---|---|
| age_26 | 11.2% | 11.78% | 11.8% | 11.2% | 卡上用了 392 例口径 |
| age_24_30 | 45.3% | 45.29% | 45.3% | 45.2% | 一致 |
| age_22_28 | 48.7% | 49.21% | 49.2% | 48.7% | 卡上用了 392 例口径 |
| age_20_30 | 63.1% | 63.09% | 63.1% | 62.5% | 一致 |

382 例下 22–28 应为 **49.2%**、26 岁应为 **11.8%**；48.7% / 11.2% 是 392 例（未去重、未换算农历）口径。预注册若引用基线，须统一到 382 例 `cleaned_reference`。

### 1.2 标签保真

| 项 | 计数 |
|---|---|
| 事件总数 | 547（15–50 岁内 534，与 eval set counts.usable_marriage_events 一致） |
| 文本无年份（不可核验） | 425 |
| 事件年与文本年份一致 | 48 |
| 事件年与文本年份矛盾 | 74 |
| 至少 1 条矛盾的案例 | 72 |
| 窗口内事件矛盾的案例 | 52 |
| age_plausible=False 的事件 | 13 |

## 2. 原语矩阵

状态定义：**有**＝单原子/字段直接回答；**部分**＝事实齐备但需调用方组合/过滤，或原子只覆盖部分子形态；**无**＝事实层缺字段/边种，组合也答不了。

| 项 | 问题 | 结论 | 子项 |
|---|---|---|---|
| P1 | 流年支与日支 D.b 是否构成冲/合/刑/穿/害 | 有 | 冲=有、六合=有、地支暗合=有、半合（三合 partial/half/gong）=有、刑=有、穿/害（同六对支）=有 |
| P2 | 大运支与日支 D.b 是否构成冲/合/刑/穿/害 | 有 | 冲=有、六合=有、地支暗合=有、半合=有、刑=有、穿/害=有 |
| P3 | 流年/大运是否引动配偶星（财/官）所在柱 | 部分 | 配偶星识别（十神）=有、配偶星柱位绑定=有、单原子直接回答「引动配偶星柱」=无、组合可答（地址 × suiyun_edge）=有、无配偶星案例的语义=部分 |
| P4 | 墓库是否被冲开/合开（chong_kai_muku 的输入输出） | 部分 | 冲开=有、刑开=有、年粒度（year=y）=有、合开（六合/三合/三会合住库）=无、空库过滤（无候选却报冲开）=无 |
| P5 | 三合/三会是否把夫妻宫合入/合走（sanhe_with_suiyun） | 部分 | 完整三合=有、完整三会=有、夫妻宫成员判定=有、半合/拱局成局=无、scope 限定（流年 vs 大运）=无 |
| P6 | 大运/流年与原局的关系边是否有稳定 edge_id 可引用 | 部分 | 边有 id=有、单快照内确定性=有、跨年稳定=无、内容寻址 id=无 |

项级合计：有 2 / 无 0 / 部分 4；子项合计：有 23 / 无 7 / 部分 1。

### P1 · 流年支与日支 D.b 是否构成冲/合/刑/穿/害

- 结论：**有**
- 说明：六合/暗合可用 suiyun_edge 逐 kind 查询；通用 atoms.py:309 he_at 只扫 natal 边（atoms.py:256 默认 scope=natal），不能回答岁运合，须改用 suiyun_edge。

| 子项 | 状态 | 代码位置 |
|---|---|---|
| 冲 | 有 | `atoms.py:781 suiyun_edge(type=chong, at=D.b, scope=liunian)；边 relation_graph.py:221` |
| 六合 | 有 | `atoms.py:781 suiyun_edge(type=liuhe)；边 relation_graph.py:223` |
| 地支暗合 | 有 | `atoms.py:781 suiyun_edge(type=zhi_anhe)；边 relation_graph.py:235` |
| 半合（三合 partial/half/gong） | 有 | `atoms.py:781 suiyun_edge(type=sanhe)；边 relation_graph.py:244-254` |
| 刑 | 有 | `atoms.py:781 suiyun_edge(type=xing)；边 relation_graph.py:238-243` |
| 穿/害（同六对支） | 有 | `atoms.py:781 suiyun_edge(type=chuan)；边 relation_graph.py:54/225；sources/tiaohou_ditiansui/滴天髓_part1.md:148「穿，即害也」` |

- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2017 年（31 岁，大运 3·丙戌，流年 丁酉）；`suiyun_edge(type=chong, at=D.b, scope=liunian)` → True；chong 边 e026（liunian）
- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2006 年（20 岁，大运 2·丁亥，流年 丙戌）；`suiyun_edge(type=liuhe, at=D.b, scope=liunian)` → True；liuhe 边 e026（liunian）；同一快照 `he_at(at=D.b)` → False（he_at 只扫 natal 边（atoms.py:256/309），看不到这条岁运合）
- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2012 年（26 岁，大运 3·丙戌，流年 壬辰）；`suiyun_edge(type=chuan, at=D.b, scope=liunian)` → True；chuan 边 e028（liunian）；穿=害 出处：sources/tiaohou_ditiansui/滴天髓_part1.md:148「穿，即害也」

### P2 · 大运支与日支 D.b 是否构成冲/合/刑/穿/害

- 结论：**有**
- 说明：大运十年恒定：16 年只跨 2–3 步大运（见 case_census.dayun_steps_in_window），大运原语只能做 decade gate，不能给 16 个年份排序。

| 子项 | 状态 | 代码位置 |
|---|---|---|
| 冲 | 有 | `atoms.py:781 suiyun_edge(type=chong, scope=dayun)` |
| 六合 | 有 | `atoms.py:781 suiyun_edge(type=liuhe, scope=dayun)` |
| 地支暗合 | 有 | `atoms.py:781 suiyun_edge(type=zhi_anhe, scope=dayun)` |
| 半合 | 有 | `atoms.py:781 suiyun_edge(type=sanhe, scope=dayun)` |
| 刑 | 有 | `atoms.py:781 suiyun_edge(type=xing, scope=dayun)` |
| 穿/害 | 有 | `atoms.py:781 suiyun_edge(type=chuan, scope=dayun)` |

- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2012 年（26 岁，大运 3·丙戌，流年 壬辰）；`suiyun_edge(type=liuhe, at=D.b, scope=dayun)` → True；liuhe 边 e027（dayun）
- 真实例子：RF-2026-000030（1985-03-25 00:00:00，乙丑 己卯 癸亥 壬子）；2005 年（20 岁，大运 2·辛巳，流年 乙酉）；`suiyun_edge(type=chong, at=D.b, scope=dayun)` → True；chong 边 e028（dayun）

### P3 · 流年/大运是否引动配偶星（财/官）所在柱

- 结论：**部分**
- 说明：事实齐备但无现成原子；调用方需先按十神找地址，再逐地址调用 suiyun_edge。

| 子项 | 状态 | 代码位置 |
|---|---|---|
| 配偶星识别（十神） | 有 | `atoms.py:37 SPOUSE；chart.pillars[].stem.ten_god / branch.main_ten_god / branch.hidden[].ten_god` |
| 配偶星柱位绑定 | 有 | `chart.pillars[].stem.addr / branch.addr（chart_facts.py:121 natal_addr）` |
| 单原子直接回答「引动配偶星柱」 | 无 | `atoms.py:1095 ATOMS 无此原子；palace_holds/visible_god/hidden_god 只扫原局` |
| 组合可答（地址 × suiyun_edge） | 有 | `atoms.py:781 suiyun_edge(at=配偶星地址, scope=liunian/dayun)，4 种 kind 逐项调用` |
| 无配偶星案例的语义 | 部分 | `atoms.py:37 SPOUSE；20/382 例八字无财/官（十神不现）；需模型层显式返回 unknown，缺统一约定` |

- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2015 年（29 岁，大运 3·丙戌，流年 乙未）；`suiyun_edge(type=chong, at=M.b, scope=liunian)` → True；chong 边 e025（liunian）
- 真实例子：RF-2026-000070（2000-09-11 08:20:00，庚辰 乙酉 壬申 甲辰）；2020 年（20 岁，大运 2·丁亥，流年 庚子）；`spouse_addresses(chart)` → None；命局无配偶星（财 在八字中不现），规则需返回 unknown

### P4 · 墓库是否被冲开/合开（chong_kai_muku 的输入输出）

- 结论：**部分**
- 说明：不传 year 时该原子对同一大运的 10 年返回同一结果（2082 个 case-year 为 True）；传 year 后降到 1085 个，才是流年级信号。

| 子项 | 状态 | 代码位置 |
|---|---|---|
| 冲开 | 有 | `atoms.py:833 chong_kai_muku；MUKU_OPENER_KINDS atoms.py:697` |
| 刑开 | 有 | `atoms.py:833 chong_kai_muku；MUKU_OPENER_KINDS 含 xing` |
| 年粒度（year=y） | 有 | `atoms.py:841-847；传 year 后只认流年节点参与的冲/刑边` |
| 合开（六合/三合/三会合住库） | 无 | `MUKU_OPENER_KINDS 只有 chong/xing；MukuFact.binders（relation_graph.py:405）已产出但无原子消费；muku_open（atoms.py:397）也只认 chong` |
| 空库过滤（无候选却报冲开） | 无 | `atoms.py:848-850 chong_kai_muku 只按 branch 匹配 ctx['muku']，不读 candidates/excluded` |

- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2015 年（29 岁，大运 3·丙戌，流年 乙未）；`chong_kai_muku(year=2015)` → True；丑库（Y.b）被 chong 边 e021（liunian）冲开
- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2006 年（20 岁，大运 2·丁亥，流年 丙戌）；`chong_kai_muku(year=2006)` → True；丑库（Y.b）被 xing 边 e020（liunian）冲开
- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2008 年（22 岁，大运 2·丁亥，流年 戊子）；`chong_kai_muku(year=2008)` → False；墓库未被岁运冲刑触及；库 Y.b（丑）被 liuhe 边 e019（scope=liunian）合住，atom 仍返回 False
- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2006 年（20 岁，大运 2·丁亥，流年 丙戌）；`chong_kai_muku(year=2006)` → True；丑库（Y.b）被 xing 边 e020（liunian）冲开；该库 candidates=0（Y.b 丑），atom 仍报冲开

### P5 · 三合/三会是否把夫妻宫合入/合走（sanhe_with_suiyun）

- 结论：**部分**
- 说明：1127 个 case-year 命中完整局含 D.b，其中 520 个 scope=dayun（十年恒定）；要按年排序必须在模型层直接过滤 relations.edges 的 scope。

| 子项 | 状态 | 代码位置 |
|---|---|---|
| 完整三合 | 有 | `atoms.py:805 sanhe_with_suiyun；completeness=full 由 relation_graph.py:272 产出` |
| 完整三会 | 有 | `atoms.py:805 sanhe_with_suiyun（kind=sanhui）` |
| 夫妻宫成员判定 | 有 | `atoms.py:825 zhi_set 子集判定；传 D.b 单字即成员测试` |
| 半合/拱局成局 | 无 | `atom 要求 completeness=full；半合边存在（relation_graph.py:244-254）但不被认` |
| scope 限定（流年 vs 大运） | 无 | `atoms.py:805 sanhe_with_suiyun 无 scope 参数；返回首个 full 边，dayun-only 会遮蔽 liunian` |

- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2015 年（29 岁，大运 3·丙戌，流年 乙未）；`sanhe_with_suiyun(zhi_set=卯)` → True；亥卯未 成局（liunian）边 e033

### P6 · 大运/流年与原局的关系边是否有稳定 edge_id 可引用

- 结论：**部分**
- 说明：可引用键应为 (chart_id, dayun_index, liunian_year, edge_id) 复合键；单独 edge_id 不可跨年引用。

| 子项 | 状态 | 代码位置 |
|---|---|---|
| 边有 id | 有 | `relation_graph.py:154 f'e{len+1:03d}'；Edge.id types.py:168` |
| 单快照内确定性 | 有 | `relation_graph.py:439 build_relation_graph；同 (chart, dayun_index, liunian_year) 两次构建 id 序列一致` |
| 跨年稳定 | 无 | `relation_graph.py:154 id 是构建序号；381/382 例同一 (kind, members) 边相邻两年 id 不同` |
| 内容寻址 id | 无 | `types.py:168 Edge 无 content_id/hash 字段；id 不随内容哈希` |

- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2006 年（20 岁，大运 2·丁亥，流年 丙戌）；`build_relation_graph(chart, dayun_index, liunian_year) ×2` → True；同一次 as-of 快照内 29 条边的 id 序列完全一致
- 真实例子：RF-2026-000010（1986-01-23 22:30:00，乙丑 己丑 丁卯 辛亥）；2007 年（21 岁，大运 2·丁亥，流年 —（跨年对比））；`同一 (kind,members) 边的 id 跨年对比` → False；同一条 sanhe 边 ['D.b', 'DY2.b'] 在 2006 年为 e025、2007 年为 e024

## 3. 岁运原子实况

代码里 `atoms.py` 的岁运原子共 **6** 个：`dayun_present`, `liunian_present`, `suiyun_edge`, `sanhe_with_suiyun`, `chong_kai_muku`, `suiyun_arrives`；任务卡 §1 写 4 个，漏了 `dayun_present`, `suiyun_arrives`。`suiyun_arrives`（到位）是实质性原语，建议下一张卡把它纳入矩阵。

| 原子 / 参数 | 命中 | 说明 |
|---|---|---|
| suiyun_edge(type=chong, at=D.b, scope=dayun) | 572/6112 | 6112 case-year |
| suiyun_edge(type=chong, at=D.b, scope=liunian) | 498/6112 | 6112 case-year |
| suiyun_edge(type=liuhe, at=D.b, scope=dayun) | 542/6112 | 6112 case-year |
| suiyun_edge(type=liuhe, at=D.b, scope=liunian) | 524/6112 | 6112 case-year |
| suiyun_edge(type=xing, at=D.b, scope=dayun) | 734/6112 | 6112 case-year |
| suiyun_edge(type=xing, at=D.b, scope=liunian) | 766/6112 | 6112 case-year |
| suiyun_edge(type=chuan, at=D.b, scope=dayun) | 547/6112 | 6112 case-year |
| suiyun_edge(type=chuan, at=D.b, scope=liunian) | 510/6112 | 6112 case-year |
| sanhe_with_suiyun(any) | 1127/6112 | scope 分布 {"dayun": 520, "dayun+liunian": 124, "liunian": 483} |
| chong_kai_muku(year=y) | 1085/6112 | 流年触发 |
| chong_kai_muku(无 year) | 2082/6112 | 十年恒定，不能按年区分 |
| liunian_present | 6112/6112 | 恒真 |
| dayun_present | 6112/6112 | 恒真 |
| suiyun_arrives(at=D.s) | 925/6112 | 通禄 |
| suiyun_arrives(at=D.b) | 950/6112 | 原身 |
| 半合边触及 D.b（liunian） | 1010/6112 | sanhe_with_suiyun 不认半合 |
| 无岁运边的 case-year | 0/6112 | 0 表示 False 是真否定 |
| edge id 跨年不稳的案例 | 381/382 | 同一 (kind,members) 相邻两年 id 不同 |

边种全集：`chong, chuan, ganzhi_zihe, ke, liuhe, po, same_qi, sanhe, sanhui, sheng, stem_chong, wuhe, xing, zhi_anhe`。穿/害同一组六对支，引擎以 `chuan` 承载（sources/tiaohou_ditiansui/滴天髓_part1.md:148「穿，即害也」）。

## 4. 预注册设计草案（零年龄参数）

- 人群：382 例 usable_for_timing（T-148 去重 + 农历换算 + 时刻齐备口径）。
- 候选集：每例 birth_year+20 … +35，共 16 年；逐年映射到 facts 的大运序号与流年干支。
- 评分签名：`score_year(chart_facts, year, dayun_index) -> int；birth_year/age 不传入`；年龄只用于候选年生成，评分函数看不到 birth_year。

| 规则 | 名称 | 原子/参数 | 计分 |
|---|---|---|---|
| R1 | 夫妻宫受流年冲/合/刑/穿 | `suiyun_edge({"at": "D.b", "scope": "liunian"})`；type ∈ chong/liuhe/xing/chuan | 每个命中的 kind +1 |
| R2 | 配偶星所在柱受流年冲/合 | `suiyun_edge({"scope": "liunian"})`；type ∈ chong/liuhe | 每个被触及的地址 +1 |
| R3 | 原局墓库被该流年冲/刑开 | `chong_kai_muku({"year": "<candidate_year>"})` | +1 |
| R4 | 夫妻宫进入完整三合/三会（流年参与） | `sanhe_with_suiyun({"zhi_set": "<D.b>"})` | bindings.scope ∈ {liunian, dayun+liunian} 时 +1；dayun 不计 |
| R5 | 岁运到位（探索项，不进主检验） | `suiyun_arrives({"at": "D.s"})` | +1 |

- Top-K：主检验 **K=3**；次要 K=5；探索 K=7。理由：R1 每例只在 3–8 个流年点火（见 per_case_coverage.r1_years），K=3 恒在正分年内，Top-3 完全由规则决定；K=5 有 124 例、K=7 有 362 例正分年不足，需要零分补齐，排序退化为填充。
- 平局：分数相同按 sha256(case_id|year) 升序（确定性、与年龄无关）；另报 tie-aware 敏感性：事件年在同分档且档位>K 时按 K/档位计分。
- 补齐：正分年不足 K 时，按 sha256(case_id|year) 升序补零分年。
- 指标：每例 Top-K 是否覆盖该例窗口内任一婚姻事件年（0/1）；零假设是 逐例 1-C(16-m_i,K)/C(16,K) 的均值（把 90 例结构性零计入）；实务门槛是 同宽度最佳静态年龄带命中率（K=3 为 26.7%，K=5 为 39.27%，K=7 为 49.21%）。
- 判据：命中率 ≥ null+8pp 且 单侧精确二项 p<0.01 算信号；命中率 < null+3pp 或 p>0.20 判死；主检验只用 K=3；K=5 为次要，K=7 仅探索，不作裁决。
- 预注册限制：
  - 不在看到结果后改 K、改窗口、改规则权重。
  - 年龄只用于候选年生成；评分函数不接收 birth_year。
  - 事件年 = 整数年；1 月至立春之间的事件按整数年算流年，存在错一岁/错一柱风险，本数据无月日，无法修正。
  - 382 例中 90 例窗口内无婚姻事件，按 0 计，不剔除。

## 5. 统计功效

单侧精确二项检验，α=0.01；p0 逐例计算（不是 K/16）。

| K | null p0 | 拒绝域临界率 | 卡上 +8pp 率 | 功效@+8pp | MDE80 | 同宽度最佳静态带 | 需零分补齐 |
|---|---|---|---|---|---|---|---|
| 3 | 18.02% | 23.04% | 26.02% | 0.919 | 6.75pp | [25, 27] = 26.7% | 0/382 |
| 5 | 28.78% | 34.55% | 36.78% | 0.830 | 7.72pp | [23, 27] = 39.27% | 124/382 |
| 7 | 38.74% | 44.76% | 46.74% | 0.795 | 8.04pp | [22, 28] = 49.21% | 362/382 |

读法：

- **+8pp 门槛低于同宽度最佳静态年龄带**：K=3 是 26.0% vs 26.7%（差 0.7pp），K=5 是 36.8% vs 39.3%（差 2.5pp），K=7 是 46.7% vs 49.2%（差 2.5pp）。所以「过 +8pp」只证明规则有信号，**不证明超过年龄先验**；预注册应把最佳静态带作为实务门槛，+8pp/p<0.01 只作统计门槛。最佳静态带是在同一批 382 例上选 lo 得到的乐观上界（选择用了结果），因此它是偏严的实务门槛，不是无偏检验。
- K=3 的 p0=18.0%、功效 0.919、MDE 6.75pp；K=5 功效 0.830；K=7 功效 0.795 但 362/382 例正分年不足，Top-7 主要是零分补齐，不能作裁决。
- 90 例窗口内无事件是结构性零：它们在 H0/H1 下都贡献 0，但会把总体 p0 拉低；如果剔除成 292 例，K=3 的 p0 升到 23.6%、功效降到 0.762——**保留 382 例更有力**。

### 5.1 敏感性（K=3）

| 子集 | n | null p0 | 功效@+8pp | MDE80 |
|---|---|---|---|---|
| all_382 | 382 | 18.02% | 0.919 | 6.75pp |
| labeled_292 | 292 | 23.58% | 0.762 | 8.35pp |
| exclude_contradicted | 330 | 17.1% | 0.883 | 7.17pp |
| male | 264 | 18.02% | 0.765 | 8.33pp |
| female | 118 | 18.03% | 0.429 | 12.24pp |
| true_solar | 265 | 18.39% | 0.774 | 8.24pp |
| clock_beijing | 117 | 17.19% | 0.406 | 12.45pp |

### 5.2 与静态 342 例的比较

同 p0、同 +8pp 下，仅样本量差异：

| K | n=382 功效 | n=342 功效 | n=382 MDE80 | n=342 MDE80 | CI 宽度比 342/382 |
|---|---|---|---|---|---|
| 3 | 0.919 | 0.880 | 6.75pp | 7.21pp | 0.9462 |
| 5 | 0.830 | 0.792 | 7.72pp | 8.07pp | 0.9462 |
| 7 | 0.795 | 0.719 | 8.04pp | 8.71pp | 0.9462 |

**为什么 382 例应期设计比静态 342 例更有力**（也说明哪里没有更强）：

1. **同例配对**：每例 16 个候选年共享同一张盘，格局/强弱/性别/出生队列等案例级混杂在例内抵消；静态 342 例是跨案例比较，无法把「盘的特征」与「这批人结婚本来就晚」分开。
2. **标签更锐**：结果从「是否落在某个年龄带」变成「16 个年份里排前 K」，可以直接检验区分度，而不只是边际相关。
3. **年龄先验可被显式扣掉**：同宽度最佳静态带（K=3 26.7%、K=7 49.2%）就是年龄先验的上界；零年龄参数模型必须超过它才算增加信息。静态设计把年龄写进分组，做不到这一步。
4. **样本量只多 +11.7%**：382 vs 342，CI 只窄 5.4%，同效应下功效提升有限（见上表）。16 个候选年**不把 n 变成 6112**——命中指标仍是每例一个 0/1；6112 只是事实计算量。真正的增益来自配对与更锐的标签，不是「16 倍样本」。
5. **代价**：16 选 3 比二分类更难，+8pp 对应的相对提升是 44%（0.18→0.26），而静态带的 +8pp 相对提升更小；所以两边不能直接比「谁的功效高」，只能比「谁能在控制年龄后仍检出信号」。

## 6. 缺口

**结论：能直接开工**。最小规则集 R1–R4 无需改 engine；G1/G2 为非阻断扩展。若预注册坚持 6 项矩阵全覆盖，则等价于「需先补 2 个原语」（合开墓库、稳定 edge_id）。

| 类别 | ID | 缺口 | 状态 | 影响 / 处理 |
|---|---|---|---|---|
| 新原语 | G1 | 合开墓库 | 无 | 无法把「流年六合/三合合住墓库」计入规则；R1/R2 可替代部分信息 |
| 新原语 | G2 | 跨年稳定 edge_id | 无 | 单独 edge_id 不能跨年引用；用 (chart_id, dayun_index, liunian_year, edge_id) 复合键可解 |
| 工程 | E1 | 年份 → 大运序号 | 部分 | engine 要求显式 dayun_index；无公开 helper，需扫 chart.cycles.dayun 的 start/end_year（本审计 5 行实现）。无 API 缺口，但有重复实现风险。 |
| 工程 | E2 | 批量入口与性能 | 有 | 无批量 API；需循环 build_chart + build_relation_graph。实测 6112 个 case-year，每 case-year 约 2 ms（graph + 4 原子），全量约 25–30 s，可离线跑。 |
| 工程 | E3 | 岁运十神地址 | 部分 | relations.nodes 只给 (addr, char)，不给 DY/LN 的十神；需模型层用 engine.predicates.palace.get_shishen 现算（asof 已有同类用法）。 |
| 工程 | E4 | 三合/三会的 scope 过滤 | 部分 | sanhe_with_suiyun 无 scope 参数；dayun-only 完整局会遮蔽 liunian 完整局，模型层需直读 relations.edges。 |
| 数据 | D1 | 事件年份文本可核验性 | 风险 | 547 条事件中 425 条文本无 4 位年份（无法核验）、48 条与文本一致、74 条与文本矛盾；72 例至少 1 条矛盾，其中 52 例矛盾事件落在 20–35 窗口。 标签噪声会衰减效应；预注册需把「排除 52 例」作为敏感性分析，不能事后改成主分析。 |
| 数据 | D2 | 窗口内无事件的结构性零 | 已知 | 90/382 例在 20–35 内无婚姻事件（其中部分事件在 15–19 或 36–50）。 命中率天花板 76.4%；p0 已按逐例 m_i 计算，不能简单用 K/16。 |
| 数据 | D3 | 无配偶星案例 | 已知 | 20/382 例八字无财/官，P3 规则无参照物。 需预注册 unknown 处理（建议该例 R2 记 0 并在报告中标注）。 |
| 数据 | D4 | 真太阳时/边界 | 已知 | 117 例 time_basis=clock_beijing（未做真太阳时）；39 例有边界警告（{"early_zi": 17, "late_zi": 21, "near_jie": 1}）。 时柱/月柱可能变；预注册需固定 profile 口径，并把 variants 作为敏感性。 |

- 阻断项：无。最小规则集 R1–R4 不需要 G1/G2；若预注册坚持 6 项矩阵全覆盖，则等价于「需先补 2 个原语」（G1 合开墓库、G2 稳定 edge_id）。

## 7. 复现与确定性

```bash
.venv\Scripts\python.exe -m tools.timing_feasibility_audit
.venv\Scripts\python.exe -m pytest -q
```

- 脚本单线程、固定案例顺序、JSON `sort_keys`、无时间戳；两次运行应逐字节一致。
- 本报告所有数字均由脚本现场计算；`per_case_coverage` 给出 382 例逐例覆盖，可逐条复核。

