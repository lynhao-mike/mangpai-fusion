# T-191 · STATUS-r3

- 状态：🟢 Delivered（未评分；评分由中枢用 T-189b 执行）
- Runner：r3（未污染，独立上下文）
- 产物：`META/p1-system-run-r3.json`（60 条）、`tasks/T-191/BRIEF-r3.md`
- 依据：`tasks/T-191/PROMPT.md`；`docs/specs/adjudication-a-plus-v1.md` v1.3 + notes；盲卷 `META/p1-anchor-60-blind-final-v2.json`

## 交付数字（脚本核验，非自评）

| 项 | 值 |
|---|---|
| 总条数 | 60/60（fixed 10 + dynamic 40 + ambiguous 10） |
| dynamic 中 needs_judgment | 0（无逃票） |
| mutual | 3（A60-045 / A60-047 / A60-049） |
| ambiguous needs_judgment | 10/10，均带 `conflict_quotes[2]` + `source_ref` |
| edge_id | 49 engine 真边 + 11 `derived:*`（engine 无该固定类边） |
| quote 缺失 | 0（全部为所引 `line:N` 的逐字子串，脚本断言通过） |
| 是否读到答案 | **否**（未读 answers / B-v1 / fresh / holdout / golden / p1-system-run / dev-20） |
| 评分器 | 未运行 |
| git 写操作 | 无 |

## 规则口径（摘要）

- fixed 克/生/化/墓：取 engine `duan_zuogong.candidates` 的 actor（`zhi_ke` / `sheng(main_qi)` / `化用` / `muku`）。
- dynamic 冲/穿：党势（段派「成势的冲才能冲伤冲去」「得势方穿对方」）；刑：未刑戌、丑戌按势、寅巳/子卯记 mutual；合：卯戌「绊/制」、巳申/巳酉/午未按原文条件，其余按体用/主宾。
- ambiguous：全部 `needs_judgment`，正反两条逐字冲突引文。

## Blockers / 风险

1. notes §5 已披露 A60-020/046/050 方向 → **A60-046、A60-050 非独立判定**，中枢统计时须扣除。
2. 11 条 `edge_id` 为 `derived:*`（engine 不建地支克/生/化/墓边），非伪造边。
3. `state` 为规则派生（合绊/救应），若答案口径不同会整列失配。
4. 7 条高不确定方向（A60-015/024/026/033/034/036/038/044/048）已在 BRIEF §3.5 列出。

## Execution Log

- 2026-10-29 · r3：读卡与规格 → 53 chart `engine.cli` 事实提取 → ~50 次 `query_theory` → 逐 case 判定 + 逐字引文断言 → 写 `META/p1-system-run-r3.json`（60/60）→ 写 BRIEF-r3 / STATUS-r3。未跑评分器、未自评、无 git 写。
