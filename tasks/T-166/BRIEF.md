# T-166 BRIEF · 婚姻应期模型 v1（R1–R4，零年龄参数）

- 任务卡：`tasks/T-166/PROMPT.md`
- 执行者：子代理 R（2026-10-29 07:54）
- 复现：`.venv\Scripts\python.exe -m tools.timing_model_v1`（退出码 0；全量约 27s）
- 产物 sha256：`59f3688d26d5d9d888155697a5135dcfd868897ca57ae75f2cb50d5006bbc3f7`（两次运行逐字节一致）

## 1. 改动文件

| 文件 | 类型 | 说明 |
|---|---|---|
| `tools/timing_model_v1.py` | 新建 | R1–R4 打分；`score_year(chart_facts, year, dayun_index) -> int`；只读白名单 4 字段 |
| `META/timing-scores-v1.json` | 新建 | 382 例 × 16 年分数（4.34 MB；sort_keys + indent=2 + LF） |
| `META/eval-protocols/timing-k3-v1.yaml` | 新建 | 预注册协议（11 字段） |
| `tests/tools/test_timing_model_v1.py` | 新建 | 8 个测试（签名/确定性/回 CLI/标签隔离/低正分年/覆盖/协议） |
| `tasks/T-166/BRIEF.md`、`tasks/T-166/STATUS.md` | 更新 | 本简报 + Execution Log |

未改 `engine/**`、规则 YAML、T-148/T-165 产物、既有测试（`git status` 只有一个与本任务无关的离线 zip 与 T-167/T-168 并行产生的文件）。

## 2. 原始输出

模型 stdout（两次运行一致，sha256 相同）：

```json
{"sha256":"59f3688d26d5d9d888155697a5135dcfd868897ca57ae75f2cb50d5006bbc3f7","summary":{"case_years":6112,"cases":382,"flags":{"muku_open_by_he_missing":1188,"no_spouse_star":544},"positive_years_per_case":{"3":2,"4":3,"5":11,"6":21,"7":39,"8":46,"9":58,"10":76,"11":53,"12":44,"13":19,"14":10},"rule_edges":{"R1":2298,"R2":1883,"R3":1085,"R4":658},"score_histogram":{"0":2492,"1":1994,"2":1100,"3":388,"4":124,"5":14},"years_per_case":{"16":382}}}
```

- **覆盖**：382 例 × 16 年 = **6112 case-year**；`population.years_per_case_counts = {"16": 382}`；每例年份 = `birth_year+20 … +35`。
- **正分年分布**（每例正分年数 → 例数）：3→2、4→3、5→11、6→21、7→39、8→46、9→58、10→76、11→53、12→44、13→19、14→10；**最小值 3，无正分年 <3 的真实案例**。
- **分数分布**：0→2492、1→1994、2→1100、3→388、4→124、5→14（0–8 分，实际最高 5）。
- **缺口/flag**：`no_spouse_star` = 544 case-year（= **34 例**，flag 按年重复）；`muku_open_by_he_missing` = **1188 case-year**（R3=0 且流年六合/完整三合/三会合住原局墓库）；`no_dayun_context` = 0。
- **规则边数**：R1 2298（年内按 kind 去重，覆盖 **1930 年**，与 T-165 `r1_years` 1930 一致）、R2 1883（覆盖 1606 年，与 T-165 `r2_broad2_years` 1606 一致）、R3 1085（与 T-165 `chong_kai_muku(year=y)` 1085 完全一致）、R4 658。
- **三个示例年份**（同一实盘 RF-2026-000010，男，1986-01-23 22:30，乙丑 己丑 丁卯 辛亥；均可用 `engine.cli relations --birth … --gender 男 --dayun-index … --liunian … --json` 回查）：

| 年份 | 大运 | score | components | 边（复合键） |
|---|---|---|---|---|
| 2006 | 2 | 2 | r1=1 r2=0 r3=1 r4=0 | R1 `cf-315ca591a176abe9bc2c\|2\|2006\|e026` liuhe liunian D.b+LN2006.b；R3 `…\|e020` xing liunian Y.b+LN2006.b |
| 2008 | 2 | 3 | r1=1 r2=2 r3=0 r4=0 | R1 `…\|2008\|e028` xing D.b+LN2008.b；R2 `…\|e019` liuhe Y.b+LN2008.b；R2 `…\|e023` liuhe M.b+LN2008.b |
| 2015 | 3 | 4 | r1=0 r2=2 r3=1 r4=1 | R2 `…\|2015\|e021` chong Y.b、`…\|e025` chong M.b；R3 `…\|e021` chong 开丑库；R4 `…\|e033` sanhe full H.b+D.b+LN2015.b（亥卯未） |

  2006 的 liuhe e026 / xing e020、2015 的 chong e021 / sanhe e033 与 T-165 P4/P5 例子逐条一致。

- **测试**：`pytest tests/tools/test_timing_model_v1.py -q -o addopts="-ra --tb=short"` → **8 passed in 2.17s**；`pytest -q` → **1336 passed, 1 skipped**（skip 为 AGENTS.md 记录的 `test_bundle_pii.py` 既有跳红；总数含并行 T-167 的测试）。
- **确定性**：连续两次运行文件 SHA-256 相同（`before == after`），JSON 规范形式 `sort_keys + indent=2 + "\n"`。

## 3. 未完成与风险

1. **合开墓库未补**（卡内已知缺口）：`muku_open_by_he_missing` 计 1188 case-year（R3=0 且流年合住墓库），只记录、不加分；若补原语，R3 覆盖会高于 1085。
2. **`no_spouse_star` 口径**：34 例（544/16），比 T-165 的「八字无财/官 20 例」多 14 例。差异全是「配偶星只透天干、地支无地址」的案例；按卡 R2「取其**地支地址**」记 R2=0 + flag，不借天干地址、不猜。34 例名单见产物 `cases[].years[].flags`。
3. **R3 的「冲开」含刑开**：复用卡 §2 指定的 `chong_kai_muku(year=…)`，其 `MUKU_OPENER_KINDS=("chong","xing")`。这是 T-165 已验证口径，未新增规则；1085 与审计完全一致。若中枢只认冲，需另立口径（本卡未授权）。
4. **R4 与 T-165 `sanhe_with_suiyun(any)` 的 1127 不同**：该原子返回**首个**完整局，dayun-only 会遮蔽 liunian；模型直读 `relations.edges`，只计 `completeness=full` 且 `scope ∈ {liunian, dayun+liunian}` 的含 D.b 局 = 658 年。按卡 R4「dayun 不计」。
5. **R1 的 he 只认六合 `liuhe`**，不含暗合/半合/拱局；与 T-165 `RELATION_KINDS` 同口径。
6. **edge_id 跨年不稳**：产物一律用 `(chart_id, dayun_index, liunian_year, edge_id)` 复合键，并写 `edge_key = chart_id|dayun_index|year|edge_id`；不引用裸 id。
7. **正分年 <3 无法用真实盘构造**：R1 三种 kind（chong/liuhe/chuan）必然覆盖 ≥3 个流年，382 例实测最小 3。测试 5 用注入 `score_fn` 的构造例验证「16 年、positive_years=1、不补齐」。
8. **协议冻结信息**：`frozen_at=2026-10-29T07:44:53+08:00`（建卡提交 2a0adc6 时间），`commit=2a0adc6…`；分数 JSON 的 `git_head` 是运行时读 HEAD，若之后有提交，重跑会变（分数本身不变）。
9. **性能**：单流全量约 27s；未做缓存/并行（不必要）。

## 4. 下游须知（T-167 / 中枢）

- **schema**：顶层 `schema / task / protocol_id / frozen_at / git_head / population / rules / cases`；`cases[] = {case_id, birth_year, positive_years, years[]}`；`years[] = {year, score, components{r1,r2,r3,r4}, edges[], flags[]}`。**无 age 字段**；`score == sum(components)`，`components` 与 `edges` 按 `rule` 一一对应。
- **协议路径**：`META/eval-protocols/timing-k3-v1.yaml`（11 字段；`protocol_id=timing-k3-v1`）。
- **Top-K**：模型不取 Top-3；评测器按 `(-score, sha256(case_id|year) 升序)` 排序。真实数据无全 0 例，最小正分年 = 3。
- **无正分年 <3 的案例**；正分年恰为 3 的两例：`RF-2026-000421`、`RF-2026-000871`。
- **34 个 `no_spouse_star` 案例**：R2 恒 0；评测时不要把这 34 例当成事实缺失剔除（卡规定 e=0 计结构性零，这 34 例不是 e=0）。
- **重跑**：`python -m tools.timing_model_v1` 覆盖 `META/timing-scores-v1.json`；若 HEAD 变化，只有 `git_head` 变，分数与 sha 的差异仅限该字段。
- **标签隔离**：模型源码只读 `case_id/birth_dt/gender/birth_year/usable_for_timing`；`grep -E "marriage_events|accuracy|命中率" tools/timing_model_v1.py` = 0（测试里也用拼接 token 自检，文件本身不含字面量）。
