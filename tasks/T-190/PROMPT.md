# T-190 · anchor-60 策展（annotator A）

- 状态：🔵 Ready
- 依据：`docs/specs/adjudication-a-plus-v1.md` §1/§6；Gemini v5/WB v4/Opus v6
- 前置：main `fd4188aa`

## 0. 一句话

策展 **anchor-60**：10 fixed（克/生/化/墓）+ 40 dynamic（只冲/合/穿/刑）+ 10 ambiguous；
≥30 盘、≤2/盘；与 golden-20/holdout-20/fresh-40 四柱+原文行区间**三重零重叠**；
无 source locator；engine.cli 预检；双人复核（你是 A，B 由中枢另派）；答案先 hash。

## 1. 选例

- 来源：`sources/duan/` 原书；每条原文明写 actor 或明写两坏。
- dynamic 40：只收冲/合/穿/刑；**不收**克/生/化/墓（fixed 10 单列）；
- fixed 10：克/生/化/墓各至少 2，固定方向明确；
- ambiguous 10：穿制源冲突/合绊/闭气/真均势；expected_direction=needs_judgment，附 `conflict_quotes[2]`（正反逐字）；
- 排除：golden-20、holdout-20、fresh-40（含 routing）的四柱/案例/source 行；旧 fresh-40 的 PF-003/023/025 错标不复用；
- 每条过 `engine.cli` 合法排盘（防 PF-040 甲日甲寅时）。

## 2. 格式

- 盲卷 `META/p1-anchor-60-blind-v1.json`：case_id/chart_id/four_pillars/gender/layer/target_relation{addr_a,addr_b,char_a,char_b,mechanism}；**无 source.path/locator、无答案**。
- 答案 `META/p1-anchor-60-answers-v1.json`：relation{actor/mutual/expected_direction}、quote、source_ref；ambiguous 带 conflict_quotes[2]。
- MD `META/p1-anchor-60-v1.md`：清单/盘数/类型/三重零校验/engine.cli 预检/hash/缺口。
- 可选 schema 测试。

## 3. 验证

- 10/40/10、≥30 盘、≤2/盘；四柱/source 行与三套 dev 零重叠；
- 盲卷无答案/locator；每条 quote 逐字；engine.cli 全过；
- 两份 JSON sha256 写入 MD，之后不得改。

## 4. 禁止

- 不用 dev-20/holdout-20/fresh-40 的答案/案例；不把 fixed 混进 dynamic；不跑 engine 评分；
- 不为某规则选例；不做 git 写操作；ambiguous 不得硬给 actor。
