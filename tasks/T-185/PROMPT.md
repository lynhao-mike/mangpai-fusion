# T-185 · 40 条新鲜断言盲集（≥25 盘、≤2/盘）

- 状态：🔵 Ready
- 优先级：**P0（系统级盲测的唯一有效卷）**
- 依据：Opus 裁决 2026-10-29；`sources/duan/`
- 前置：无（只策展，不跑 engine）

## 0. 一句话

从 `sources/duan/` 里策展 **40 条原书明确方向的作用断言**，至少来自 **25 张不同的盘**，
每盘最多 2 条；标注人与运行人分离，答案先 hash；**不得使用 dev-20 的案例/答案**。

## 1. 选例标准

- 来源：`sources/duan/` 段派讲义/案例；原文明确写出“谁对谁、什么关系、方向”。
- 40 条，≥25 张盘，≤2 条/盘（避免同盘相关性虚胖 n）。
- 排除 dev-20 的 20 例（同盘/同四柱/同 source 行都不行）。
- 关系类型覆盖：克/生/化/墓/冲/合/穿/刑；穿制有争议的例不要选（或标 `ambiguous`，不进主集）。
- 每条：`case_id`、四柱、性别、`relation{a,b,kind,mechanism,actor,mutual?}`、`quote`、`source_ref`。
- 刑的两败例用 `mutual=true`，不硬填 actor。
- 标注人（写答案）与运行人（跑系统）必须是不同 Agent；运行人不得看答案。

## 2. 产物

- `META/p1-fresh-40-v1.json`：盲测输入（只含四柱/性别/来源，不含答案）
- `META/p1-fresh-40-answers-v1.json`：40 条答案（含 actor/mutual/quote/source_ref）
- `META/p1-fresh-40-v1.md`：清单、盘数、类型分布、非 dev 校验、hash、缺口
- 可选 `tests/tools/test_p1_fresh_40_schema.py`

## 3. 验证

- 40 条、≥25 盘、≤2/盘；
- 与 dev-20 四柱/案例/source 行零重叠；
- 盲测输入不含答案字段；答案 quote 逐字；
- 两份 JSON 先算 sha256 并写入 MD；之后不得改。

## 4. 禁止

- 不用 dev-20 的案例/答案；不跑 engine；不改 sources/engine/规则/测试；
- 不为了让某条规则通过而选例；穿制争议例不进主集。
- 不做 git 写操作。
