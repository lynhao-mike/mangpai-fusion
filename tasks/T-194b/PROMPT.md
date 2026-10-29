# T-194b · fixed-20 独立复核（annotator B）

- 状态：🔵 Ready
- 依据：T-194 A 卷；R-tool fixed gate；双人复核
- 前置：`META/p1-fixed-20-blind-v1.json`（A 已交付）

## 0. 一句话

你是 **annotator B**：只读 fixed-20 盲卷 + `sources/duan/` + `engine.cli`，**独立**标 20 条 fixed（克/生/化/墓各 5）；
**不读 A 的 answers**、不跑评分器、不做 git 写。标完写 B 答案 + hash；中枢对比 A/B。

## 1. 重点复核

- 3 条化字裁量：F20-013（未→亥）、F20-014（申→子）、F20-015（寅→子）；
- F20-012 原书未标乾坤（A 按乾跑通）；B 独立判断；
- 每条端点字唯一、quote 逐字、source_ref 行内可查。

## 2. 产物

- `META/p1-fixed-20-answers-B-v1.json`（20 条）
- `META/p1-fixed-20-B-v1.md`（清单/对齐/预检/hash/notes）
- `tasks/T-194b/BRIEF.md` + `STATUS.md`
- 不跑评分器；不读 A answers；不做 git 写。

## 3. 验收（中枢）

- 20/20、5/5/5/5；B 未读 A answers；
- A/B 逐条 actor；一致率与分歧清单；3 化/1 性别单独列；
- 一致率 <75% 按双人复核规则处理（先列分歧，不静默改 A）。
