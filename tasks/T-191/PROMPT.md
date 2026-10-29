# T-191 · anchor-60 final v2 三次未污染盲跑

- 状态：🔵 Ready
- 依据：A+ v1.3；`META/p1-anchor-60-blind-final-v2.json`；T-189b 评分器
- 前置：final v2 hash `cc88d10e…`；T-189b 已合并

## 0. 一句话

3 个未污染 runner 各跑一次 60 条（10 fixed +40 dynamic +10 ambiguous），只读盲卷 + `engine.cli` + `query_theory` + A+ 规格；
**不读答案、不读 dev-20/holdout/fresh/golden、不跑评分器、不写 git**。
输出 `META/p1-system-run-r1.json` / `r2` / `r3`；中枢用 T-189b 一次性评分 + 3 次一致率。

## 1. 输入（只许）

- `META/p1-anchor-60-blind-final-v2.json`（60 条；无 source/locator/答案）
- `docs/specs/adjudication-a-plus-v1.md` + `adjudication-a-plus-v1-notes.md`
- `python -m engine.cli all --pillars ... --gender ... --json`
- `python -m tools.query_theory ...`
- `sources/duan/`（只作理论检索；不得检索本批 case 的答案段）

**禁止**：`META/p1-anchor-60-*answers*`、任何 fresh/holdout/golden answers、`META/p1-system-run*`、dev-20 答案。
若意外读到答案，立即停并在 BRIEF 报告。

## 2. 输出

每条：
```json
{"case_id":"A60-001","a":"未","b":"子","kind":"克","direction":"actor→target",
 "edge_id":"...","basis":"fixed_wuxing|party_dominance|source_text|agent_anchor",
 "state":"成|败|救应|needs_judgment","source_ref":"...","verbatim_quote":"..."}
```
- fixed：必须 actor→target；
- dynamic：必须 actor→target 或 mutual；**不得用 needs_judgment 逃票**；
- ambiguous：`direction="needs_judgment"`，附 `conflict_quotes[2]`（正反逐字）+ `source_ref`；
- 60/60；缺一条写 `missing` 并说明；不写评分/结论。

## 3. 三个 runner

- r1 / r2 / r3 各一个独立子代理；读同一盲卷、同一 prompt；不共享中间产物；
- 输出 `META/p1-system-run-r1.json` / `r2` / `r3`；
- 3 次方向一致率由 T-189b 计算；<90% 按 A+ kill。

## 4. 禁止

- 不读 answers/dev；不跑评分器；不改盲卷/答案/engine/阈值；不做 git 写操作；
- 不宣称通过；不自评。
