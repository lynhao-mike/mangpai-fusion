# T-199c · 规则抽取（≤15 条，纯 engine）

- 状态：🔵 Ready
- 依据：T-199 主卡；WB/Gemini 裁决
- 前置：`tasks/T-199/PROMPT.md`

## 0. 一句话

只读 MinerU 22 **理论段/M1-D**，写 **≤15 条**五合/六合规则；
`when` 全是 engine 可观测布尔原子；**不读例题/训练/留出**；不写代码、不做 git 写。

## 1. 规则

- 结论枚举：`化 | 合绊 | 争合不化 | needs_anchor`；
- `when` 仅允许：边 kind、pair、柱位/紧贴、月令五行、化神透干、争合干、克破、同柱；
- 禁文本条件、禁“旺/有力”、禁浮点权重；力量只用 engine 冻结分数/版本；
- 每条带 `source_ref` + 逐字 quote；quote 必须能映射到一条 engine 边/地址，否则不得触发；
- 同边两规则相反→`needs_anchor(rule_a, rule_b)`；书有带 quote 优先级才可解；
- 文本条件只作 provenance；含不可操作化条件的规则标 `unoperationalized`，永不触发。

## 2. 产物

- `META/t199-rules-v1.yaml`（≤15 条）
- `tasks/T-199c/BRIEF.md` + `STATUS.md`
- 不读例题；不跑留出；不做 git 写；不改 engine/保护区。

## 3. 验收

- 规则数 ≤15；每条 quote 逐字、source_ref 合法；
- `when` 原子全在 engine 可观测集合；
- 无文本条件；无浮点权重；
- 与 T-199a 的案例零交集（不拟合案例）。
