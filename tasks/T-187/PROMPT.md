# T-187 · 系统级盲测运行（fresh-40 + routing，引擎+Agent）

- 状态：🔵 Ready
- 优先级：**P0（主证明点）**
- 依据：`docs/specs/party-direction-v1.md`、T-185 fresh-40、T-186 评分器
- 前置：main `eaa2e651`；T-183/185/186 已合并

## 0. 一句话

你是**未污染的系统级运行 Agent**：只拿 40 条盲测输入 + 5 条 routing 盲测 + `engine.cli` + `query_theory`，
按 T-184 规则输出锚定作用断言。**不看答案、不看 routing 答案、不看 dev-20、不看原书 case-specific 分析段。**
评分由中枢用 T-186 一次性执行；你不得自评、不得调规则。

## 1. 输入（只许读这些）

- `META/p1-fresh-40-v1.json`（40 条盲测：四柱/性别/来源；不含答案）
- `META/p1-fresh-40-routing-blind-v1.json`（5 条 routing：四柱/性别；不含答案）
- `engine.cli`（每盘 `all --pillars ... --gender ... --json`）
- `python -m tools.query_theory`（通用理论检索）
- `docs/specs/party-direction-v1.md`（计数口径/R1–R8/needs_judgment/mutual）

**禁止读**：`META/p1-fresh-40-answers-v1.json`、`META/p1-fresh-40-routing-v1.json`、
`META/p1-holdout-*`、`META/golden-20-*`；不得打开 `sources/` 中与 case 对应的原书分析段。
若命令/文件意外读到答案，立即停止并在 BRIEF 报告。

## 2. 输出

`META/p1-system-run-v1.json`，每条：

```json
{"case_id":"PF-001","a":"D.b","b":"H.b","kind":"制","direction":"actor→target",
 "edge_id":"e013","basis":"fixed_wuxing|party_dominance|source_text|agent_anchor",
 "state":"成|败|救应|needs_judgment","source_ref":"...","verbatim_quote":"..."}
```

- `direction` ∈ `"actor→target"` / `"mutual"` / `"needs_judgment"`；`a` = 自报施力端，`b` = 受力端；
  `actor→target` 意为 `a→b`；`mutual` 时 `a`/`b` 填两端，`direction="mutual"`。
- routing 5 条：`direction="needs_judgment"`；不得硬给 actor。
- 穿/合绊/保护/制净/党势 Δ=0：`needs_judgment`；刑：`mutual`（或按 T-184 例外）；
- 固定克/生/化/墓：按引擎事实给 actor；冲/合：按 T-184 整数党势，Δ≠0 才给方向；
- 每条必须有 `edge_id`（能取到）、`source_ref`、`verbatim_quote`；取不到就 `needs_judgment` + 说明。

## 3. 纪律

- **不读答案/不读 dev-20/不读 case 原文分析**；不用答案反推；
- 不调阈值/比值/权重/浮点；不为 H02/H05 写专用规则；
- 不写产品代码、不改 engine/规则/测试/hold-out；不 git 写操作；
- 允许在 `%TEMP%` 写一次性只读取数脚本（不提交），用于按 T-184 算整数党势；脚本不得读答案。
- 45 条全做；缺一条写 `missing` 并在 BRIEF 说明。

## 4. 产物

- `META/p1-system-run-v1.json`
- `tasks/T-187/BRIEF.md`（四字段：改动文件/原始输出/未完成与风险/下游须知）
- `tasks/T-187/STATUS.md` 追加 Execution Log

## 5. 验收（中枢亲自跑）

- 45 条 case_id 与盲测输入一一对应；
- 方向枚举合法；routing 5 条为 needs_judgment；
- 每条 edge_id/source_ref/quote 可查；无答案文件读取；
- 中枢用 T-186 评分器跑一次：`p1_assertion_eval --answers ... --routing ... --system-output ... --dev20-veto passed`；
- **你不得自评、不得宣称通过**。
