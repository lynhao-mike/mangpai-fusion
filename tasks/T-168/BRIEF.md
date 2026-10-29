# T-168 BRIEF · 应期事件年份审计（只读）

- 任务卡：`tasks/T-168/PROMPT.md`
- 执行：子代理 T（Worker），2026-10-29
- 复核命令：`.venv\Scripts\python.exe -m tools.timing_event_year_audit`、`.venv\Scripts\python.exe -m pytest -q`

## 1. 改动文件

**新建（4 个，均在卡内 File Scope）**

| 文件 | 说明 |
|---|---|
| `tools/timing_event_year_audit.py` | 只读审计脚本；标准库 only，不 import `engine`，不写任何 year |
| `META/timing-event-year-audit-v1.json` | 逐例分类（382 行）+ 逐事件桶 + 矛盾清单 + 婚姻年份冲突清单 + 20 例 + 可复现剔除名单 |
| `META/timing-event-year-audit-v1.md` | 计数、20 例逐条回原文、剔除名单、矛盾清单、T-165 对账、风险 |
| `tests/tools/test_timing_event_year_audit.py` | 22 条确定性单测（变体识别、四桶、剔除规则、只读不改输入、产物与现场重算一致） |

**更新（2 个）**：`tasks/T-168/BRIEF.md`（本文件）、`tasks/T-168/STATUS.md`（Execution Log 追加一行）。

**未改**：`META/timing-eval-set-v1.json`、`cases/raw_feedback/parsed/real_cases_990.jsonl`、`META/timing-feasibility-audit-v1.json`、`engine/**`、既有测试、任何规则。三个输入在测试里按 sha256 前后比对，确认未被写。

## 2. 原始输出

### 2.1 脚本 stdout（现场跑）

```text
[T-168] cases=382 events=547
[T-168] events_by_bucket={'match': 36, 'no_year_in_text': 398, 'contradiction': 84, 'multi_year': 29, 'other': 0} sum=547
[T-168] cases_by_bucket={'match': 24, 'no_year_in_text': 250, 'contradiction': 81, 'multi_year': 27, 'other': 0} sum=382
[T-168] in_window=393 structural_zero=90 year_from_source=544
[T-168] marriage_conflict=32 cases=31 in_window_cases=20
[T-168] t165_reproduced=True sensitivity_exclude=20
[T-168] wrote META/timing-event-year-audit-v1.json / META/timing-event-year-audit-v1.md
```

```text
.venv\Scripts\python.exe -m pytest -q
1358 passed, 1 skipped, 1 warning (exit 0)
```

（`1 skipped` = 既有 `tests/tools/test_bundle_pii.py` 的 T-114 已知红，不是本轮引入。）

### 2.2 四类计数（例 / 事件，四桶可加）

| 桶 | 事件（547） | 案例（382，取最严重事件） |
|---|---:|---:|
| `match` | 36 | 24 |
| `no_year_in_text` | 398 | 250 |
| `contradiction` | 84 | 81 |
| `multi_year` | 29 | 27 |
| `other`（残余） | 0 | 0 |
| **合计** | **547** | **382** |

### 2.3 矛盾（多口径，别混用）

| 口径 | 事件 | 案例 | 含义 |
|---|---:|---:|---|
| `contradiction` 桶（全窗口） | 84 | 81 | 正文写了年份，但都不是 `event.year` |
| 其中窗口内（20–35） | 61 | 60 | T-165 的「52 例」是 4 位年份口径，本口径更宽 |
| **婚姻年份冲突**（剔除依据） | 32 | 31 | 正文贴着婚姻词的年份不含 `event.year` |
| 其中窗口内 | **20** | **20** | = `sensitivity_exclude` |

### 2.4 可复现剔除名单（脚本算出，20 例）

```text
RF-2026-000010  RF-2026-000126  RF-2026-000188  RF-2026-000247  RF-2026-000279
RF-2026-000350  RF-2026-000391  RF-2026-000448  RF-2026-000466  RF-2026-000653
RF-2026-000684  RF-2026-000712  RF-2026-000728  RF-2026-000753  RF-2026-000754
RF-2026-000758  RF-2026-000769  RF-2026-000841  RF-2026-000859  RF-2026-000964
```

规则（写在 JSON `preregistration.sensitivity_exclude_rule`，脚本按规则现算）：
案例在 20–35 岁窗口内存在 `marriage_conflict == true` 的婚姻事件。`marriage_conflict` =
正文贴着婚姻词（结婚/离婚/相亲/恋爱/分手/对象/老婆…）的年份集合非空，且不含 `event.year`。

放宽口径同时给出（JSON `sensitivity.variant_lists`，不作主名单）：
`in_window_literal_contradiction` 60 例、`in_window_multi_year` 17 例、`any_window_marriage_conflict` 31 例。

### 2.5 20 例审计要点（完整逐条见 MD §3，每条带原文摘录）

抽样确定性：先按变体覆盖各取 1 例（`y4` / `y2` / `y4_range` / `y2_range`；`cn4` 语料为 0），再按桶轮转补到 20，案例不重复。

- `RF-2026-000010`（2011，25 岁）：正文 `2009 年丧父，2017 年结婚`，无任何 2011；紧前记号是区间端点 `2008-2011 年` → 标签年错，剔除。
- `RF-2026-000024`（2014，18 岁）：`2015/2020/2021` 分别对应复读/工作/感情对象；婚姻事实在 2021 → 剔除（窗口外，仅作口径示例）。
- `RF-2026-000061`（2007，18 岁）：正文 `2008 复读、2018 相亲、2019 结婚、2020 生子`，2007 只贴在「高考没考上」上 → 剔除。
- `RF-2026-000063`（2000，16 岁）：第二条婚姻事件正文含 `13 年结婚、16 年离婚`（2 位变体），event.year=2000 是丧父年 → 剔除。
- `RF-2026-000126`（2022，35 岁）：`y2_range` 案例，`08-12 年` 展开为 2008–2012；正文婚姻年份是 `18 年女友分开` → 剔除。
- `RF-2026-000045`（2021，25 岁）：正文只有 2022/2023/2024，均非婚姻事实 → 记 `contradiction` 但不进剔除（无婚姻年份冲突）。
- `RF-2026-000062`（2023，26 岁）：`领结婚证 24 年结的婚` → 2023（领证）与 2024（婚礼）两个婚姻年；表头 2023 支撑标签 → 不剔除。
- `RF-2026-000011`（2016，15 岁）：`no_year_in_text` 代表例，正文无年份，原文表头 `2016 年:` 支撑 → 不剔除。
- `RF-2026-000093` / `RF-2026-000081` / `RF-2026-000086`：`match` 代表例，正文年份与 `event.year` 一致。
- `RF-2026-000101` / `RF-2026-000111` / `RF-2026-000130`：`multi_year` 代表例，正文含标签年 + 别的年份。
- 变体覆盖：`2008 年`（y4，116 条事件）、`08 年`（y2，40 条）、`08-12 年`/`14.15 年`/`20～23 年`（y2_range，4 条）、`2008-2012 年`/`2013-15 年`（y4_range，6 条）；`二〇〇八` 语料 0 条，由单测合成用例证明。

### 2.6 与 T-165 对账（逐字节复现）

| 口径 | T-165 `label_fidelity` | 本审计复现 |
|---|---:|---:|
| `match` | 48 | 48 |
| `mismatch` | 74 | 74 |
| `no_year_in_text` | 425 | 425 |

口径差：T-165 只认 4 位 `19xx/20xx` 且只看正文。本审计加上 `08 年` / 中文数字 / 区间后，
`no_year_in_text` 425 → 398，`mismatch` 74 拆成 `contradiction` 84 + `multi_year` 29 中的相应部分
（识别出新变体年份，部分「无年份」变成矛盾）。两套数不可直接相减。

## 3. 未完成与风险

1. **正文无年份仍占 72.8%（398/547）**：但其中 387 条原文有「年表」表头（`YYYY 年:` / `YYYY 年`），
   只有 3 条连紧前年份记号都找不到。所以「无年份」主要是**正文口径**问题，不是标签凭空捏造。
2. **「其他信息」并入是最大噪声源**：47 条事件正文来自原文 `其他信息：` 块（矛盾 28 条、无年份 17 条、多事件年 2 条）。
   典型如 `RF-2026-000063` 的第二条婚姻事件被整段并到 2000 年。
3. **2 位数年份有歧义**：`08 年` / `13 年` 按最接近 `birth_year+30` 还原，并排除 `未来10 年` / `拍拖 12 年的女友` 等时长语境；
   `18 年后` 这类两可写法仍可能误判（只带 2 位证据的矛盾 14 条）。
4. **四桶是「正文口径」**：`contradiction` 桶包含「正文提到的年份与婚姻无关」的情况（`2015 年生子`、`一直做到 2015 年`），
   所以**不能直接按桶剔除**；主名单另加「正文明写别的婚姻年份」这一限定，见 §2.4。
5. **`multi_year` 不否定标签年**：窗口内 17 例，只说明同段还写了别的年份；不进主名单。
6. **未做**（按卡禁止/不扩大范围）：没有改任何 `year`、没有重排事件、没有评分/建模/建盘；没有修解析器。
   若要根治「其他信息并入」，需要另开卡改 `tools/timing_eval_set.py` 的事件切分。

## 4. 下游须知

- **评测分母不是 382**：292 例窗口内有婚姻事件，90 例结构性零（`cases_with_window_event` / `cases_structurally_zero`）。
- **敏感性分析请用 `sensitivity_exclude`（20 例）**：`META/timing-event-year-audit-v1.json` 的
  `sensitivity.sensitivity_exclude`；主结果 vs 剔除后结果各跑一遍。放宽口径名单在 `sensitivity.variant_lists`。
- **不要用 `no_year_in_text` 当「标签无效」**：398 条里 387 条有年表表头依据，剔除它们等于丢 72% 数据。
- **逐例可追溯**：JSON `cases`（382 行）每例有 `bucket` / `event_years` / `window_buckets` / `marriage_conflicts`；
  矛盾与冲突各有全量清单（含 `source_kind`、`source_year`、`text`）。
- **复现**：脚本无墙钟时间戳，连续三次运行 JSON/MD 逐字节一致；`pytest` 里有「产物 == 现场重算」的守卫测试。
- **谁会被这 20 例影响**：这 20 例的窗口内婚姻标签与正文婚姻年份不符，任何应期模型在这 20 例上的命中都不可信；
  但**不要**据此改标签（本卡只读）。
