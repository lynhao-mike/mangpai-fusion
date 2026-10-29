# T-170 · Golden-20 教材真盘盲推集（只读策展）

- 状态：🔵 Ready for Execution
- 优先级：**P0（产品是否成立的第一证明点）**
- 创建：2026-10-29（中枢）
- 依据：`docs/reviews/external-audit-adjudication-v2.md` §4–§5
- 前置：无（只读）

## 0. 一句话

从 `sources/` 的教材/案例集中，挑 **20 个有完整大师推演过程**的真实命例，做成
**盲测输入（四柱/性别/大运）与答案（原书推演/成败/应期）物理分离**的两套文件。
**只策展，不写推演器、不评分。**

## 1. 选例标准

- 来源：`sources/duan/`、`sources/yang/`、`sources/ren/`、`sources/ziping/` 中
  带完整「定体用/宾主 → 做功 → 成败/救应 → 应期」推演的命例；优先教材例题。
- 覆盖四类：**制用、化用、墓用、救应**各至少 3 例；其余可互补。
- 每例必须有：四柱、性别、大运序列（起运/顺逆）、原书对主功/成败/应期的明确判断。
- **20 例是目标，不是凑数**：若完整推演不足 20，如实报实际数量与缺口，不许编造/拼接。

## 2. 盲测输入（`META/golden-20-v1.json`）

只含模型可见的信息：

```json
{"case_id":"G20-001","school":"duan","four_pillars":"...","gender":"乾",
 "dayun_start_age":3,"dayun_direction":"顺","dayun":["..."],
 "source":{"path":"sources/duan/...","locator":"..."}}
```

**不得**含原书分析、结论、成败、应期答案；`source` 只留路径/定位，供审计，不含正文。

## 3. 答案（`META/golden-20-answers-v1.json`，与输入物理分离）

每例：

```json
{"case_id":"G20-001",
 "original_analysis":"原书推演原文（可截取关键段）",
 "core_work":"原书点出的主功（如 伤官制杀 / 冲开丑库取财）",
 "role_direction":"体/用/主/宾/actor/target（原书口径）",
 "adjudication":"成局 / 破局 / 逢救应化解（原书口径）",
 "rescue":"救应在哪（原书口径）",
 "timing":"原书点明的应期大运/流年与机制",
 "source_refs":[{"path":"sources/...","line":123,"quote":"..."}]}
```

- 每个字段必须有原文依据；没有明确判断的字段写 `null`，不许补。
- 原文引用保留原字，不改写。

## 4. 产物

- `META/golden-20-v1.json`（盲测输入）
- `META/golden-20-answers-v1.json`（答案，物理分离）
- `META/golden-20-v1.md`（清单、四类覆盖、缺口、选例理由、20 例索引）
- 可选 `tests/tools/test_golden_20_schema.py`（schema/分离性校验，不读答案进输入）

## 5. File Scope

**允许新建**

- `META/golden-20-v1.json`
- `META/golden-20-answers-v1.json`
- `META/golden-20-v1.md`
- `tests/tools/test_golden_20_schema.py`（可选）

**只读**

- `sources/**`、`theory/**`、`tools/query_theory.py`
- `engine/cli.py`（只用于核对四柱/大运，不写推演）

**禁止**

- 改 `sources/`、`theory/`、`engine/**`、规则、评测集、既有测试
- 写推演器/评分/模型；把答案写进盲测输入
- `git commit / push / checkout / stash / reset / clean`

## 6. 验收（中枢亲自看）

1. 20 例（或如实报实际数），四类覆盖可数；
2. 盲测输入**不含** `original_analysis/core_work/adjudication/rescue/timing` 等答案字段；
3. 每个答案字段有 `source_refs`，能回原文；
4. 四柱/大运能用 `engine.cli` 复核（抽查 5 例）；
5. `pytest -q` 不受影响（本卡不写产品代码）。

## 7. 回报格式（`tasks/T-170/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（20 例清单、四类计数、缺口）
3. **未完成与风险**（推演不完整的例、原文锚点缺失）
4. **下游须知**（盲测输入 schema、答案 schema、哪些例只能做弱对照）

## 8. 禁止

- 不许为了凑 20 把「只有断语没有推演」的例塞进来。
- 不许把答案字段泄漏进盲测输入。
- 不许改原文一个字。

## 9. 中枢补充（2026-10-29 09:00，T-169 实测后）

1. **任何 `edge_id` 必须带 `snapshot{chart_id, dayun_index, liunian_year}`**：
   加 `--dayun-index/--liunian` 会全量重编号（C1 `e012` 从 `liuhe[M.b,D.b]` 变
   `ke[M.s,LN2026.s]`，16→39 条）。没有快照就只能写地址，不许写裸边号。
2. **`candidate_id` 与 `relations.edge_id` 两路都给**：`duan_zuogong.candidates` 不是边全集
   （三盘夫妻宫漏 3/4/1 条）。只有 candidate 没有 edge 的，标 `candidate_only`，不得当已成立。
3. 若已生成 JSON，按上面两条补字段；来不及就在 BRIEF 的「风险」列出未带 snapshot 的条目，
   验收按不合格处理。
