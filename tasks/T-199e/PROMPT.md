# T-199e · 留出封存/第三方（等 a）

- 状态：🔵 Ready（等 T-199a）
- 依据：T-199 主卡；WB/Gemini 裁决
- 前置：`META/t199-cases-holdout-v1.json`

## 0. 一句话

你是第三方：核 T-199a 的 25 留出是否**先封/hash**、四柱是否出现在训练/规则、规则作者是否见过留出；
不写规则、不跑留出、不做 git 写。

## 1. 检查

- 留出 25 的 case_id/四柱/hash；训练 15 与留出零重叠；
- 规则作者（T-199c）是否只读理论段；是否 grep 过例题/留出；
- 留出是否只在最后一次性跑；
- 歧义案例是否单列、是否进分母。

## 2. 产物

- `META/t199-holdout-audit-v1.json`
- `tasks/T-199e/BRIEF.md` + `STATUS.md`
- 不改留出/规则；不做 git 写；不改 engine/保护区。
