# T-169 BRIEF · 单盘分析规格 v1（五元组断语卡）

- 执行：子代理（Worker）
- 时间：2026-10-29
- 任务卡：`tasks/T-169/PROMPT.md`
- 中途方向更新：已按中枢 08:5x 消息 + `docs/reviews/external-audit-adjudication-v2.md` §1.1/§7，把「七段报告」改为「**五元组断语卡 + 可选报告外壳**」；3 张盘、判定表、Kill criterion 不变。
- 未跑：`git commit/push/checkout/stash/reset/clean`（按卡禁止）。

---

## 1 · 改动文件

| 文件 | 动作 | 说明 |
|---|---|---|
| `docs/specs/single-chart-analysis-v1.md` | 新建 | 规格主体：五元组定义（§2）、卡 schema（§3）、Linter 规则 L01–L21（§4）、可选报告外壳与段↔卡映射（§5）、判定表（§6）、地址词汇表/缺口（§7）、3 张盘（§8）、待外部审计 9.1–9.12（§9） |
| `META/single-chart-report-skeleton-v1.md` | 新建 | 卡模板（人读块 + JSON 骨架）、岁运卡差异、3 张反例卡、可选报告 8 节、交付前自检（按 L 码） |
| `META/single-chart-cases-v1.json` | 新建 | 3 张盘的事实快照 + `gaps_present` + `card_support` + `suiyun_activation` + `edges_not_in_candidates` + 口径坑 |
| `tasks/T-169/BRIEF.md` | 新建 | 本文件 |
| `tasks/T-169/STATUS.md` | 追加 | Execution Log 一行 |

**未改**：`engine/**`、`theory/**`、规则 YAML、`tests/**`、评测集、`AGENTS.md`、`tasks/T-169/PROMPT.md`。

---

## 2 · 原始输出

### 2.1 3 张盘（均为 `usable_for_timing=true`，来源 `META/timing-eval-set-v1.json`）

| # | case_id | 四柱 | 日主 | 性别 | 出生（引擎输入） | 时刻口径 | 角色 |
|---|---|---|---|---|---|---|---|
| C1 | `RF-2026-000125` | `丁卯 壬子 辛丑 乙未` | 辛 | 乾 | 1987-12-18 13:15:00 | clock_beijing | 结构完整 |
| C2 | `RF-2026-000438` | `庚午 戊寅 己未 乙丑` | 己 | 坤 | 1990-02-23 01:48:00 | true_solar | 配偶星可查 |
| C3 | `RF-2026-000894` | `壬戌 己酉 庚子 戊子` | 庚 | 乾 | 1982-09-14 23:55:00 | clock_beijing | 边界盘 |

**边界理由（C3）**：23:55 晚子时 → `boundary_warnings=[late_zi]` + `variants[axis=zi_shi].alt_value=rollover_23`，`diffs=[["/pillars/2/ganzhi","辛丑"]]`，`alt_chart_id=cf-62995823c069f1deacba`（四柱不唯一）；同时八字无财 = 乾造**无配偶星**（T-165 census `has_spouse_star=false`）；另 D.b/H.b 落年旬空，夫妻宫唯一关系边是 `e009 po`（不在制用候选 kind 清单内）。

### 2.2 逐盘事实摘要（`engine.cli all`，默认快照）

| 项 | C1 `RF-2026-000125` | C2 `RF-2026-000438` | C3 `RF-2026-000894` |
|---|---|---|---|
| 边数 | 16 | 14 | 12 |
| 做功候选 | 17（制用 11 / 生泄用 3 / 合用 2 / 墓用 1） | 13（制用 6 / 化用 1 / 生泄用 2 / 合用 2 / 墓用 2） | 8（制用 2 / 生泄用 4 / 合用 2） |
| `actor` 非空 | 12 | 11 | 6 |
| `actor=None` | 5（`e001` 合、`e007` stem_chong、`e010` 刑、`e012` 合、`e014` 穿） | 2（`e003`、`e012` 均合） | 2（`e011`、`e012` 干支自合） |
| 夫妻宫 D.b 边 | `e012 liuhe` / `e013 sanhui` / `e015 chong` / `e016 xing` | `e009 liuhe` / `e010 sanhui` / `e013 chong` / `e014 xing` | `e009 po`（唯一） |
| 夫妻宫边**不在**候选 | 3 条（`e013/e015/e016`） | **4 条全部** | 1 条（`e009`） |
| 配偶星 | 财 4 地址：`Y.b` 卯 / `Y.b⊕乙` / `H.s` 乙 / `H.b⊕乙` | 官杀 4 地址：`M.b` 寅 / `M.b⊕甲` / `H.s` 乙 / `D.b⊕乙` | **无**（`spouse_star_addrs=[]`） |
| 空亡 | 日旬空 辰巳 / 年旬空 戌亥，无命中 | 日旬空 子丑，命中 `H.b` | 年旬空 子丑，命中 `D.b`、`H.b` |
| 墓库 | `D.b` 丑金库 openers=`e015,e016` binders=`e012`；`H.b` 未木库 openers=`e015,e016` chuan_po=`e014` | `D.b` 未木库 openers=`e013,e014` binders=`e009`；`H.b` 丑金库 openers=`e013,e014` binders=`e012` | `Y.b` 戌火土库：无候选、无 openers、无 binders（空库） |
| 结构 rescuer.met | 3（`e001` / `H.s` / `H.s,Y.s`） | 3（`e003` / `Y.s,M.s` / `e006`） | **0** |
| 结构 breaker.met | 1（`Y.s`） | 2（`Y.s,M.b` / `H.s`） | 2（`e003` / `e001,e003`） |
| `boundary_warnings` | `[]`（`all` 里键被删） | `[]`（同上） | `[late_zi]`（`all` 里出现） |

### 2.3 岁运快照（用于证明「引动边可写」）

| # | 快照 | 边数 | 夫妻宫相关边 |
|---|---|---|---|
| C1 | `--dayun-index 5 --liunian 2026` | 39（原局 16） | `e033 chong[D.b,DY5.b]`、`e034 xing[D.b,DY5.b]`、`e035 chuan[D.b,LN2026.b]` |
| C2 | `--dayun-index 4 --liunian 2026` | 39（原局 14） | `e030 po[D.b,DY4.b]`、`e031 xing[D.b,DY4.b]`、`e032 liuhe[D.b,LN2026.b]`、`e033 sanhui[D.b,LN2026.b]`、`e039 xing[H.b,DY4.b,D.b]` |
| C3 | `--dayun-index 4 --liunian 2026` | 34（原局 12） | `e026 liuhe[D.b,DY4.b]`、`e027 sanhui[D.b,DY4.b]`、`e028 chong[D.b,LN2026.b]` |

**关键实测**：加 `--dayun-index/--liunian` 会**全量重编号**——
- C1：原局 `e012 liuhe[M.b,D.b]` → 岁运快照 `e012 ke[M.s,LN2026.s]`；
- C2：原局 `e009 liuhe[Y.b,D.b]` → 岁运快照 `e009 ke[H.s,M.s]`，原局冲边 `e013` → `e028`。

→ 规格据此定「一卡一快照」（§1.3 铁律 1），Linter `L12` 拦跨快照引用。

### 2.4 自测命令与结果

```text
.venv\Scripts\python.exe -m engine.cli all --birth "1987-12-18 13:15:00" --gender 乾 --json   → rc=0, 17170 B
.venv\Scripts\python.exe -m engine.cli all --birth "1990-02-23 01:48:00" --gender 坤 --json   → rc=0, 15990 B
.venv\Scripts\python.exe -m engine.cli all --birth "1982-09-14 23:55:00" --gender 乾 --json   → rc=0, 12979 B
.venv\Scripts\python.exe -m engine.cli chart --birth "<3 张盘>" --gender <乾|坤> --json        → rc=0（boundary_warnings 逐盘核对）
.venv\Scripts\python.exe -m pytest -q                                                          → 1358 passed, 1 skipped, 1 warning in 113.85s（rc=0）
```

JSON 自校验（PowerShell `ConvertFrom-Json` + 与 CLI 逐项比对）：3 张盘的 `pillars`、`edges`（id/kind/members）、`tiyong` 分组、`candidates.by_mode/total`、`edges_not_in_candidates`、`structures`（structure_id/item_id/status/evidence）、`kongwang.hits`、`muku`（openers/binders/候选数）、`suiyun_activation` 边号 —— **mismatches = 0**。

---

## 3 · 未完成与风险

### 3.1 七段里目前**无法落地址**的部分（按要求单列）

| 段 | 无法落地址的部分 | 缺口 | 规格里的处理 |
|---|---|---|---|
| ② 宾主 | `all` 默认没有 `binzhu` 字段（`compact_for_agent` 削掉 `candidates[].binzhu`），只能按地址位置自判或跑 `--full` | 无硬缺口，但有读取坑 | §2.2/§7.4-2 要求注明来源 |
| ③ 体用 | 「用」组在 C3 为**空**（无财无官杀）；`双属` 择端是判断 | G5 邻域 / 9.4 | §2.2 只要求「择了写理由」 |
| ④ 做功 | 冲/刑/穿/破无主客（C1 3 条、C2 夫妻宫 4 条、C3 1 条 `po`）；支克支无边；`po`/`sanhe`/`sanhui` 不进候选 | G2 / G3 / 9.5 | §2.2 `direction_known=false`；§7.4-4 强制读 edges 全集 |
| ⑤ 成败/救应 | 盲派域无救应事实 → 「逢救应化解」只能写「未判」；「合开墓库」无开/闭结论；C3「空库」 | G5 / muku_open_close | §2.3 `rescue_judged=未判`；§7.3 |
| ⑥ 落事+引动 | 岁运字的十神/体用取不到（`chart` 只有 4 柱，`tiyong` 只有 8 个原局地址） | **suiyun_ten_god** | §2.4 只写边种+地址；`unknowns` 必带 |
| ⑦ 不确定 | C3 四柱不唯一（`late_zi`），任何结论都要声明口径 | boundary_zi_shi | §7.3 |
| ⑤/③（配偶星） | C3 无配偶星 → 配偶星一路全不可写 | no_spouse_star | §7.3 |

### 3.2 规格层面的未完成

1. **Linter 未实现**：本卡只写判据（L01–L21）与输入/输出契约（§4.3），不写代码。是否可直接实现、有无漏判，需实现卡验证。
2. **`M3-R-034` 与引擎冲突未裁决**：原文给了六冲克向（「丑未冲→土冲变虚」），引擎 `actor=None`。v1 取最窄读法「不许用原文补引擎缺口」，已列为待确认 9.12。
3. **C2 的 `破局` 判据用的是 `M1-D-298`**（夫妻宫不能被刑坏/冲破），属**原文判据 + edge basis**，不是结构项（婚姻域无结构，G5）。这条写法是否被接受，需外部审计。
4. **「≥3 张卡」的门槛**沿用 T-169 卡原本的「≥3 条」，未做功效论证（本卡不做统计）。
5. **C3 的 `alt_chart_id` 盘未展开**：`rollover_23` 口径下日柱 `辛丑`，该盘的事实（十神/体用/候选）未采集；若要用需另跑 CLI。

### 3.3 风险

- **风险 1（高）**：`edge_id` 跨快照不稳已被实测（§2.3）。若下游实现不强制 `snapshot` 字段，报告会出现「边号对得上但盘是另一张」的隐蔽错误。
- **风险 2（中）**：三盘都**不能**单独证明「五元组可落地」——它们只证明「事实层够写 ①②⑤，③ 需原文补，④ 有引动边但缺十神」。真正的可落地性要靠 golden-20（T-170）。
- **风险 3（中）**：`M1-D-298`、`M1-D-304`、`M2-Y-395` 三条原文都带吉凶/结局断言（「必离婚」等）；报告只许引结构半句。若判定人不熟，容易把吉凶半句一起搬进 ④。
- **风险 4（低）**：C2 的 `calendar_type_raw=lunar`，`birth_dt` 是 eval set 换算后的公历；若有人用农历原文重排会得到另一张盘。已在 cases JSON 的 `calendar_note` 写明。

---

## 4 · 下游须知

### 4.1 报告/推演器实现需要的事实与原语

| 需要 | 现状 | 处理 |
|---|---|---|
| 地址表（8 地址 + 十神 + 藏干） | 有 | `chart.pillars[]`，藏干写 `addr⊕char` |
| 关系边全集 | 有 | `relations.edges[]`；**不许只用 `candidates`**（实测漏 6/7/7 条） |
| 施力方向 | 部分 | `ke`/`sheng`/`canggan_ke`/`muku` 有 `actor`；冲/刑/穿/破无（G2） |
| 三态依据 | 部分 | `structures[].items[].status/evidence` 只覆盖子平八格；婚姻域要靠原文判据 + edge |
| 岁运引动 | 部分 | 边有、地址有；**十神/体用没有**（`suiyun_ten_god`） |
| 原文锚点 | 有 | `tools.query_theory` 返回 `id/title/statement/source_ref{path,anchor}` |
| 双锚点核对 | 有 | `relations.pair_index`（`relations` 子命令）可做地址→边索引 |

### 4.2 标了「待外部审计确认」的条目（规格 §9，共 13 条）

9.1 合能否开墓库 · 9.2 救应是否化解 · 9.3 宾主第 3/4 层独立锚点 · 9.4 `双属` 是否必须择一 · 9.5 `po` 是否进制用候选 · 9.6 无配偶星盘口径 · 9.7 ⑥ 落事射程 · 9.8 `met` 与「成格」的距离 · 9.9 「岁运引动」算不算预测 · 9.10 卡片粒度与最小卡数 · 9.11 Linter 实现边界 · 9.12 原文克向能否补 `actor=None` · 9.13 「破局」能否只靠「原文判据 + edge」

其中**最影响下游**的四条：9.9（决定 ④ 能不能写「何时引动」）、9.2（决定 ③ 的第三态能不能写「化解」）、9.12（决定 G2 是硬缺口还是可绕过）、**9.13（决定 ③ 的「破局」在婚姻域能不能成立——C2 的示例卡正压在这一条上）**。

### 4.3 判定时先看哪三处

1. **规格 §1.3 铁律**（一卡一快照）——最容易犯、后果最隐蔽。
2. **§7.4-4（候选不是边的全集）**——三张盘的夫妻宫边大半不在候选里。
3. **§6.2/§6.3**（分母定义 + Kill criterion）——避免判定漂移。
