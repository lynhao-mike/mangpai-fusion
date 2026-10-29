# T-190b · anchor-60 独立复核（annotator B）

- 状态：🔵 Ready
- 依据：A+ v1.3 §6 双人复核；T-190 A 卷
- 前置：`META/p1-anchor-60-blind-v1.json`（A 已交付，B 未做）

## 0. 一句话

你是 **annotator B**：只读盲卷 + `sources/duan/` + A+ 规格 + `engine.cli`，**独立**标 60 条；
**不读 A 的 answers**、不读 dev-20/holdout/fresh 的答案、不跑评分器/runner、不做 git 写操作。
标完写 B 答案 + hash；中枢对比 A/B，一致率 <75% 按 A+ v1.3 判“裁决器”定位不成立。

## 1. 输入

- `META/p1-anchor-60-blind-v1.json`（60 条：case_id/chart_id/四柱/gender/layer/target_relation）
- `sources/duan/` 原书
- `docs/specs/adjudication-a-plus-v1.md`
- `python -m engine.cli all --pillars ... --gender ... --json`
- **禁止**：`META/p1-anchor-60-answers-v1.json`、`META/p1-fresh-40-answers-v1.json`、`META/p1-holdout-answers*`、`META/golden-20-answers*`、`META/p1-system-run-v1.json`。

## 2. 独立标注

- fixed 10：克/生/化/墓；给 actor→target；写 `relation.kind/mechanism/actor/target/expected_direction`。
- dynamic 40：冲/合/穿/刑；给 actor→target 或 mutual（两伤刑）；写 `quote`/`source_ref`。
- ambiguous 10：`expected_direction="needs_judgment"`；`conflict_quotes[2]`（互异）+ `source_texts[2]`（逐字整行 + source_ref）。
- 8 条原书未标乾/坤：按原文能定的填；仍不能定就写 `gender="未注明"` 并在 notes 说明；不要编造。
- 发现 A 卷的 target_relation 与原文不符：标 `disputed=true` + 理由；不要改盲卷。
- 每条答案带 `case_id/layer/relation/quote/source_ref/annotation`；ambiguous 另带 `conflict_quotes`/`source_texts`。

## 3. 产物

- `META/p1-anchor-60-answers-B-v1.json`（60 条）
- `META/p1-anchor-60-B-v1.md`（清单/与盲卷对齐/engine 预检/hash/notes/disputed 清单）
- `tasks/T-190b/BRIEF.md` + `STATUS.md`
- sha256 写入 MD；不跑评分器；不做 git 写操作。

## 4. 验收（中枢）

- 60/60、10/40/10；盲卷 case_id 一一对应；B 未读 A 答案；
- engine.cli 预检；ambiguous 双引文/ source_texts 行内；
- 中枢比较 A/B：一致率、disputed 清单；<75% kill。
