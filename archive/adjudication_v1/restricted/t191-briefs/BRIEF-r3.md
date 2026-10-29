# T-191 · BRIEF-r3（未污染 runner r3）

- 生成时间：2026-10-29
- 任务卡：`tasks/T-191/PROMPT.md`
- 产物：`META/p1-system-run-r3.json`（60 条）
- 本轮未跑评分器、未自评、未宣称通过、未做 git 写操作。

## 1. 改动文件

| 文件 | 性质 |
|---|---|
| `META/p1-system-run-r3.json` | 新增（唯一运行产物，60 条） |
| `tasks/T-191/BRIEF-r3.md` | 新增（本文件） |
| `tasks/T-191/STATUS-r3.md` | 新增 |

未修改：盲卷 `META/p1-anchor-60-blind-final-v2.json`、任何 answer/答案文件、`engine/`、阈值、`docs/specs/`。

## 2. 原始输出（可复核）

### 2.1 只读输入（全部在任务卡允许清单内）

1. `tasks/T-191/PROMPT.md`
2. `docs/specs/adjudication-a-plus-v1.md`、`docs/specs/adjudication-a-plus-v1-notes.md`
3. `META/p1-anchor-60-blind-final-v2.json`
4. `python -m engine.cli all --pillars … --gender … --json`：53 个唯一 chart 各跑 1 次（0 报错）
5. `python -m tools.query_theory`：约 50 次检索（duan 学派，`--per-school-cap 0`）
6. `sources/duan/*.md` 与 `theory/raw/duan/*.md`：仅按 rule 引用行定位逐字原文，未检索本批 case 的答案段/命例段

### 2.2 判定口径（所有 case 按同一套规则，逐条落在 `basis` 字段）

| 层/机制 | 方向判定 | basis |
|---|---|---|
| fixed 克 | 克方 → 被克方（engine `zhi_ke` candidate 的 actor 已核） | fixed_wuxing |
| fixed 生 | 生方 → 受生方（engine `sheng(main_qi)` actor） | fixed_wuxing |
| fixed 化 | 印（受生端）→ 官杀（engine `化用` actor；`化以印化七杀`） | fixed_wuxing |
| fixed 墓 | 库 → 入库方（engine `muku` actor；`入墓有二：多而墓之，寅申巳亥见墓入之`） | fixed_wuxing |
| 冲 | 成势方冲对方（`成势的冲才可能冲伤冲去对方`；四库冲按 `金水与湿土成势…木火与燥土成势…` 分库坏向） | party_dominance |
| 穿 | 得势方穿对方（`相克之穿看势在哪里，哪方得势即能穿了对方`） | party_dominance |
| 刑 | 未戌→未刑戌；丑戌→按党势（`丑戌刑灭戌中火，戌旺时灭丑中水`）；寅巳/子卯→原文双向，记 mutual | source_text / party_dominance |
| 合 | 卯戌→`戌绊卯不制` / `卯合戌还制`；巳申→金水/木火势；巳酉→火旺时巳制酉；午未→`仅相生`；子丑、辰酉、亥未→体用/主宾或生克 | source_text / agent_anchor |

### 2.3 计数（脚本核验）

- case 总数 **60/60**，case_id 唯一，无缺字段、无空 quote、a/b 字对与盲卷 `char_a/char_b` 完全一致。
- direction：`actor→target` 47 + `mutual` 3（A60-045 / A60-047 / A60-049）+ `needs_judgment` 10。
- 分层：fixed 10（全部 `成`）；dynamic 40（`needs_judgment` 0 条，无逃票）；ambiguous 10（全部 `needs_judgment`，各带 `conflict_quotes[2]` + `source_ref` + `source_refs[2]`）。
- edge_id：49 条为 engine 真边（`eNNN`）；11 条为 `derived:*`（engine 不为地支克/生/化/墓建边，其 candidate `edge_id=None`，故按 `derived:zhi_ke|sheng(main_qi)|muku` 标注）。
- quote：59 条单引文 + 10 条 ambiguous 各 2 条冲突引文；**全部引文由脚本断言为所引 `line:N` 该行的逐字子串**（不匹配即中止，实跑通过）。
- basis 分布：party_dominance 24 / source_text 23 / fixed_wuxing 10 / agent_anchor 3。
- state 分布：成 26 / 救应 12 / 败 12 / needs_judgment 10（规则见 §4.4）。

## 3. 未完成与风险

1. **未跑评分器、未自评**：本文件不构成通过结论；一致性/聚类/margin 由中枢用 T-189b 计算。
2. **notes 文件披露了 3 条 dynamic 方向**：`adjudication-a-plus-v1-notes.md` §5（任务卡必读项）写明了 A60-046（未→戌）、A60-050（丑→戌）的最终方向与 A60-020 的双书冲突。**A60-046 与 A60-050 并非独立判定**，中枢统计时应按 2 条已知处理；A60-020 我按段派 `戌可以坏辰库` 取 戌→辰，未采用另一书。
3. **11 条 edge_id 为 `derived:*`**：不是伪造边，是 engine 不建地支固定类边的事实（其 candidate 自报 `edge_id=None`）。若评分器要求 edge_id 必须能在关系图中查到，这 11 条会被判缺失。
4. **`state` 为规则派生而非原文判定**：dynamic 用「target 被六合/五合/成局三合绊→救应；actor 被绊→败；否则成」，M1-D-239「被穿的字若有合/墓保护」为据。若答案的 state 口径不同，会整列失配。
5. **高不确定条目**（同规则下两解接近，列出供中枢复核）：A60-015（卯酉，党势给卯→酉，但原文有「卯酉冲一定无功，全废」）、A60-024（巳酉，火旺取巳→酉）、A60-026（辰酉，取酉→辰）、A60-033/034（子未，党势两向相反）、A60-036/038（寅巳生穿，取势方巳→寅）、A60-044（戌→丑，党势压过主宾）、A60-048（丑→戌，党势打平按冬令/柱序）。
6. **3 条 mutual 是推断**：原文同时给出「寅刑巳…；巳刑寅…」「子卯刑…；卯刑子…」双向，故记 mutual；若答案取单向，这 3 条计失配。

## 4. 下游须知

1. **答案合并**：`chart_id`/`four_pillars`/`gender` 需按 `case_id` 从盲卷合并（本文件未重复这些字段）。
2. **a/b 语义**：`direction="actor→target"` 时 `a`=actor、`b`=target；`mutual`/`needs_judgment` 时 `a/b` 保持盲卷 `char_a/char_b` 原序。匹配请按「字对集合 + 方向」双向比对。
3. **ambiguous 字段形状**：`conflict_quotes` 为 2 个逐字字符串（正/反对），`source_ref` 指第 1 条，`source_refs[2]` 与两条引文一一对应（跨文件时用后者）。
4. **`derived:*` 约定**：`derived:zhi_ke`（地支克）、`derived:sheng(main_qi)`（本气生/化）、`derived:muku`（入墓）——对应 engine `duan_zuogong.candidates[].relation_kind`，非关系图边。
5. **禁止事项确认**：未读 `META/p1-anchor-60-*answers*`、`META/p1-anchor-60-B-v1.md`、任何 fresh/holdout/golden answers、`META/p1-system-run*`（含 r1/r2 产物与 BRIEF/STATUS-r1/r2）、dev-20 答案；未跑评分器；未 git 写。

## 5. Blockers

无阻塞。唯一口径风险是 §3.2（notes 已披露 2 条方向）与 §3.3（11 条 derived edge_id），均不阻塞交付。
