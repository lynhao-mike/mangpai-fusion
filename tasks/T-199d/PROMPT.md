# T-199d · 规则引擎（四数/冲突/弃权/基线）

- 状态：🔵 Ready
- 依据：T-199 主卡；WB/Gemini 裁决
- 前置：`tasks/T-199/PROMPT.md`

## 0. 一句话

实现规则引擎骨架：读 `t199-rules-v1.yaml` + 案例 JSON（训练/留出）→ 输出
`n_labeled / n_fired / n_conflict / n_unoperationalized`、每例 verdict、冲突对、needs_anchor；
**不跑留出**（留出先封，由 T-199e 一次性跑）；不做 git 写。

## 1. 要求

- 纯 stdlib；YAML 可用 `yaml` 或先把规则转 JSON；
- `when` 原子从 `engine.cli` 事实取；缺原子→`unoperationalized`，不触发；
- 同边两规则相反→`needs_anchor(rule_a, rule_b)`；书本 quote 优先级才可解；
- 输出每例 `verdict/reason/fired_rules/conflict_with`；
- 统计四数；报告“开火者精度”“已决覆盖率”；
- 基线：全猜最高频类；
- 不读留出答案；不跑留出；不改 engine/保护区。

## 2. 产物

- `tasks/T-199/run_rules.py`（骨架，可对训练 15 跑）
- `tasks/T-199d/BRIEF.md` + `STATUS.md`
- 不跑 P1/P2；不做 git 写。
