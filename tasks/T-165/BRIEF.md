# T-165 BRIEF · 婚姻应期可行性审计（382 例，只读）

- 执行：子代理 Q；完成 2026-10-29
- 任务卡：`tasks/T-165/PROMPT.md`
- 自测：
  - `.venv\Scripts\python.exe -m tools.timing_feasibility_audit` → exit 0
  - `.venv\Scripts\python.exe -m pytest -q` → **1303 passed, 1 skipped, 0 failed**（基线 1289；本卡新增 8 条；其余增量来自并行 T-164 的测试文件）
- 确定性：连续两次运行 JSON sha256 `9af0e158ca141e9391d3b59f3613328da952e774e6c8e544b52dd69d8aed2e67`、MD sha256 `6818bf38f72c7b0c665bc72e38fc494aa56453c2d8bb8ff541dbf13cbc52cdf9`
- 未做任何 `git commit / push / checkout / stash / reset / clean`

## 1. 改动文件

**新建（本卡范围内）**

- `tools/timing_feasibility_audit.py`
- `META/timing-feasibility-audit-v1.json`
- `META/timing-feasibility-audit-v1.md`
- `tests/tools/test_timing_feasibility_audit.py`（8 条，不重跑 6112 个 case-year）

**修改**

- `tasks/T-165/STATUS.md`（仅追加 Execution Log）

**没有改动**：`engine/**`、`theory/**`、`sources/**`、`META/timing-eval-set-v1.json`、`META/timing-baseline-v1.json`、既有测试、`tasks/T-165/PROMPT.md`。

> 工作区里另有 `tasks/T-164/*`、`META/address-level-evidence-audit-v1.*`、`tools/address_level_evidence_audit.py` 等并行任务产物，不是本卡改动。

## 2. 原始输出

### 2.1 382 例覆盖（可加）

| 项 | 数值 |
|---|---|
| 原始记录 / `usable_for_timing` | 411 / **382** |
| `birth_dt` 可解析 / 有性别 / 能建盘 | 382 / 382 / **382**（0 失败） |
| 大运区间齐备 | 382 |
| 每例 20–35 岁可评分年 | **16/16（382 例）**，合计 **6112 case-year** |
| 窗口内有婚姻事件 | **292 例**；无事件 **90 例**（结构性零） |
| 窗口内事件 / 去重事件年 | 393 / 385 |
| 婚姻事件年落在大运区间 | 544/547（区间外 3 条，均在起运前） |
| 大运顺逆与阳男阴女一致 | 382/382（不一致 0） |
| 性别 / 时刻口径 | 男 264、女 118；true_solar 265、clock_beijing 117 |
| 窗口内 16 年跨大运步数 | 2 步 194 例、3 步 188 例 |
| 边界警告 | 39 例至少 1 条（early_zi 17、late_zi 21、near_jie 1） |
| 无配偶星案例 | 20/382 |

**基线口径核对**（卡上 4 个数混用两个口径）：

| 年龄带 | 卡上 | 382 例重算 | 392 例 card |
|---|---|---|---|
| 24–30 | 45.3% | 45.29% | 45.2% |
| 20–30 | 63.1% | 63.09% | 62.5% |
| 22–28 | 48.7% | **49.21%** | 48.7% |
| 26 | 11.2% | **11.78%** | 11.2% |

382 例下应写 22–28 **49.2%**、26 岁 **11.8%**；48.7%/11.2% 是 392 例（未去重、未换算农历）口径。

**标签保真**：547 条事件里 425 条文本无 4 位年份（不可核验）、48 条与文本一致、74 条与文本矛盾；72 例至少 1 条矛盾，其中 52 例的矛盾事件落在 20–35 窗口。

### 2.2 原语矩阵（项级 2 有 / 0 无 / 4 部分；子项 23 有 / 7 无 / 1 部分）

| 项 | 问题 | 结论 | 子项 |
|---|---|---|---|
| P1 | 流年支与日支 `D.b` 冲/合/刑/穿/害 | **有** | 冲、六合、暗合、半合、刑、穿/害 全有 |
| P2 | 大运支与日支 `D.b` 冲/合/刑/穿/害 | **有** | 同上 6 项全有 |
| P3 | 岁运引动配偶星（财/官）所在柱 | **部分** | 识别有、柱位绑定有、单原子**无**、组合可答有、无星语义部分 |
| P4 | 墓库冲开/合开（`chong_kai_muku`） | **部分** | 冲开有、刑开有、年粒度有、合开**无**、空库过滤**无** |
| P5 | 三合/三会合入夫妻宫（`sanhe_with_suiyun`） | **部分** | 完整三合有、三会有、成员判定有、半合**无**、scope 限定**无** |
| P6 | 岁运边稳定 `edge_id` | **部分** | 有 id、单快照确定有、跨年稳定**无**、内容寻址**无** |

每项在 JSON `primitive_matrix.items[].example_objects` 里都有真实案例 + 调用参数 + 返回值/note；这里只摘关键例子：

- **P1 冲**：`RF-2026-000010`，2017 年（31 岁，大运 3·丙戌，流年 丁酉），`suiyun_edge(type=chong, at=D.b, scope=liunian)` → True，边 `e026`。
- **P1 合/害**：2006 年 `liuhe` 边 `e026` 为 True，同一快照 `he_at(at=D.b)` 为 **False**（`he_at` 只扫 natal，见 `atoms.py:256/309`）；2012 年 `卯辰` 穿/害由 `chuan` 边 `e028` 回答。穿=害出处 `sources/tiaohou_ditiansui/滴天髓_part1.md:148「穿，即害也」`。
- **P2**：`RF-2026-000010` 2012 年，大运 3·丙戌 vs `D.b=卯`，`suiyun_edge(type=liuhe, scope=dayun)` → True，`e027`。
- **P3**：`RF-2026-000010` 2015 年，配偶星地址 `M.b` 被流年冲，`e025`；但这是模型层「先按十神找地址再逐地址调 `suiyun_edge`」的组合，没有单原子。20 例无配偶星（如 `RF-2026-000070`）。
- **P4**：2015 年 `丑库（Y.b）` 被流年未冲开（`chong` 边 `e021`）；2006 年被戌刑开（`xing` 边 `e020`）；2008 年丑库被流年子六合（`liuhe` 边 `e019`）合住，`chong_kai_muku` 仍返回 **False**（合开缺口）；2006 年该库 `candidates=0` 仍报冲开（空库缺口）。
- **P5**：2015 年 `亥卯未` 成局（`liunian` 边 `e033`），`sanhe_with_suiyun(zhi_set=卯)` → True。
- **P6**：同一次 as-of 快照内 29 条边 id 两次构建完全一致；但 `(sanhe, D.b/DY2.b)` 在 2006 年是 `e025`、2007 年是 `e024`——**381/382 例**存在同一边跨年 id 变化。

**岁运原子实况**：代码 6 个（`dayun_present`、`liunian_present`、`suiyun_edge`、`sanhe_with_suiyun`、`chong_kai_muku`、`suiyun_arrives`），卡上写 4 个，漏 `dayun_present`、`suiyun_arrives`。6112 case-year 点火率：

- `suiyun_edge(D.b)` True：冲 572/498、六合 542/524、刑 734/766、穿 547/510（依次 dayun/liunian）。
- `sanhe_with_suiyun` True 1127（dayun 520、dayun+liunian 124、liunian 483）；半合触及 `D.b` 的 liunian 有 1010，atom 不认。
- `chong_kai_muku`：传 `year` 1085；不传 `year` 2082（十年恒定）。
- `suiyun_arrives`：`D.s` 925、`D.b` 950。
- 无岁运边 case-year：0（`suiyun_edge` 的 False 是真否定，不是 unknown）。

### 2.3 缺口

| 类别 | ID | 缺口 | 状态 | 影响/处理 |
|---|---|---|---|---|
| 新原语 | G1 | 合开墓库 | 无 | `MUKU_OPENER_KINDS` 只有 chong/xing（`atoms.py:697`）；`MukuFact.binders`（`relation_graph.py:405`）已产出但无 atom 消费 |
| 新原语 | G2 | 跨年稳定 edge_id | 无 | id 是构建序号（`relation_graph.py:154`）；用 `(chart_id, dayun_index, liunian_year, edge_id)` 复合键可解 |
| 工程 | E1 | 年份→大运序号 | 部分 | 无公开 helper，需扫 `cycles.dayun` 的 start/end_year（本审计 5 行） |
| 工程 | E2 | 批量入口/性能 | 有 | 无批量 API；6112 case-year 约 2 ms/个，全量 **27.5 s**，可离线跑 |
| 工程 | E3 | 岁运十神地址 | 部分 | `relations.nodes` 只给 (addr, char)，DY/LN 十神需模型层用 `get_shishen` 现算 |
| 工程 | E4 | 三合/三会 scope | 部分 | `sanhe_with_suiyun` 无 scope 参数，dayun-only 会遮蔽 liunian |
| 数据 | D1 | 事件年份文本可核验性 | 风险 | 425 条无年份、74 条矛盾、52 例窗口内矛盾 |
| 数据 | D2 | 结构性零 | 已知 | 90/382 无窗口内事件，命中率天花板 76.4% |
| 数据 | D3 | 无配偶星 | 已知 | 20/382，P3 规则无参照物 |
| 数据 | D4 | 真太阳时/边界 | 已知 | 117 例 clock_beijing；39 例边界警告 |

**结论：能直接开工**。最小规则集 R1–R4 不需要改 `engine/**`；G1/G2 是非阻断扩展。若预注册坚持 6 项矩阵全覆盖，则等价于「需先补 2 个原语」（合开墓库、稳定 edge_id）——但这不是最小模型的开工前提。

## 3. 未完成与风险

1. **标签噪声是最大风险**：547 条事件只有 48 条能被文本年份核验；74 条与文本年份直接矛盾（如 `RF-2026-000010` 事件年记 2011，文本写「2017 年结婚」）。这会衰减任何模型的效应量。预注册只能把「排除 52 例窗口内矛盾」作为**敏感性分析**，不能事后改成主分析。
2. **90 例结构性零**：20–35 内无婚姻事件，命中率天花板 76.4%；零假设必须逐例 `1-C(16-m_i,K)/C(16,K)`，不能用 K/16。若剔除成 292 例，K=3 功效从 0.919 降到 0.762。
3. **大运顺逆已核**：382/382 与 `is_forward(阳男阴女)` 一致（0 不一致）。但 `chart_from_solar` 的大运步边界来自 lunar-python 精确起运，`qiyun` 另有 `mangpai_rough` 整数起运变体；边界年可能差 1 年，预注册需固定起运口径。
4. **边界/时刻**：117 例 `clock_beijing` 未做真太阳时；39 例有 `early_zi/late_zi/near_jie` 警告，时柱/月柱可能变。预注册需固定 profile 并报告 `variants`。
5. **合开/空库**：`chong_kai_muku` 对「流年六合/三合合住库」返回 False，且不读 `candidates/excluded`，空库也会报冲开；预注册若用 R3，需在模型层加候选过滤或降权。
6. **性能**：单次全量 27.5 s，串行循环 6112 次 graph build；若做参数扫描需并行/缓存，当前没有批量入口。
7. **未做**：没有建盘写入、没有评分/排序、没有生成任何应期预测；预注册只是设计草案，未执行。

## 4. 下游须知

**能否直接开工**：**能**。用现有 `suiyun_edge` + `chong_kai_muku(year=)` + `sanhe_with_suiyun(zhi_set=D.b)`，在模型层组合出 R1–R4；不需要改 `engine/**`。若产品要求「合开墓库」或「跨年稳定 edge_id」，再开小卡补 2 个原语，不阻塞当前最小模型。

**预注册草案要点**（完整版见 `META/timing-feasibility-audit-v1.md` §4）：

- 人群 382 例；候选年 `birth_year+20…+35`，16 年；年龄只用于生成候选年，评分函数签名 `score_year(chart_facts, year, dayun_index)`，**不传 birth_year/age**。
- R1 夫妻宫受流年冲/六合/刑/穿（4 kind 各 +1）；R2 配偶星地址受流年冲/合（每地址 +1）；R3 `chong_kai_muku(year=y)` +1；R4 完整三合/三会含 `D.b` 且 scope 含 liunian +1；R5 `suiyun_arrives` 仅探索。
- **主检验 K=3**：R1 每例只在 3–8 年点火，K=3 恒在正分年内（0 例需零分补齐）；K=5 有 124 例、K=7 有 362 例需补齐，Top-7 退化，只作探索。
- 平局/补齐用 `sha256(case_id|year)` 升序（确定性、与年龄无关）；另报 tie-aware 敏感性。
- 判据：命中率 ≥ null+8pp 且单侧精确二项 p<0.01 为信号；< null+3pp 或 p>0.20 判死。
- 功效：K=3 p0=18.02%、功效 0.919、MDE80 6.75pp；K=5 0.830；K=7 0.795。
- **实务门槛应再加一条**：同宽度最佳静态年龄带（K=3 26.7%、K=5 39.27%、K=7 49.21%）——+8pp 门槛比它低 0.7–2.5pp，只过 +8pp 不等于超过年龄先验。
- 与静态 342 例比：n 只多 +11.7%（CI 窄 5.4%，K=3 功效 0.880→0.919），16 个候选年**不把 n 变成 6112**；真正增益来自同例配对、更锐标签、可显式扣掉年龄先验。
- 敏感性：labeled_292 0.762、排除 52 例矛盾 0.883、female 0.429、clock_beijing 0.406——女命与 clock_beijing 子集单独做功效不足，别在其中做裁决。

**基线引用**：统一用 382 例 `cleaned_reference`（24–30 45.3%、20–30 63.1%、22–28 49.2%、26 岁 11.8%）；卡上的 48.7%/11.2% 是 392 例口径。

**复现**：

```bash
.venv\Scripts\python.exe -m tools.timing_feasibility_audit   # exit 0，重写 JSON/MD，哈希见文首
.venv\Scripts\python.exe -m pytest -q                         # 1303 passed, 1 skipped
```
