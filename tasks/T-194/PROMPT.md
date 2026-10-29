# T-194 · fixed-20 盲门 + 分流预注册/新盲集

- 状态：🔵 Ready
- 依据：R-tool 第一证明点；WB 的 fixed-20、Opus 的 routing recall
- 前置：main `186d2833`；T-192 R 规格

## 0. 一句话

建 **fixed-20** 盲门（只克/生/化/墓，20 条）与 **分流问题集/预注册**；
与 dev-20/holdout-20/fresh-40/anchor-60 四重零重叠；无 locator；双人复核；先 hash。
不测方向、不测冲合穿刑。

## 1. fixed-20

- 20 条 fixed（克/生/化/墓各 5），新盘；只给四柱/性别/target_relation（地支端点）；
- 答案：actor→target、source_ref、quote；engine.cli 预检；
- 盲卷无 source/locator/答案；答案先 hash；标注 A/B 双人复核（B 由中枢另派或本卡 A + 复核清单）。

## 2. 分流问题集/预注册

- 10–20 个真实问题（婚姻/事业/健康/财运等），每个问题预注册“应召回的证据项”：
  宫位、关系边 ID、source_ref 范围；
- 只测证据包覆盖（召回率），不测方向/断语；
- 阈值写入 `META/routing-prereg-v1.json`：召回 ≥80% 为 pass，<60% kill，60–79% 灰；
- 与 fixed-20 同一批或新盘；零重叠；答案/标签 restricted。

## 3. 产物

- `META/p1-fixed-20-blind-v1.json` / `-answers-v1.json` / `.md`（hash）
- `META/routing-questions-v1.json` / `routing-prereg-v1.json` / `.md`
- `tasks/T-194/BRIEF.md` + `STATUS.md`；不跑评分器；不做 git 写。

## 4. 禁止

- 不测方向/冲合穿刑；不把 fixed 混进 dynamic；不留 locator；不用 dev-20/fresh-40 案例；
- 不调 A+ 阈值；不为通过选例。
