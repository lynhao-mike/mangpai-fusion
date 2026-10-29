# T-184 STATUS

- 状态：✅ **已验收**（2026-10-29 15:10，中枢；hash 后正文未改）
- 执行者：子代理 AH
- 任务卡：`tasks/T-184/PROMPT.md`
- 验收：中枢亲自看；只写规格，不写代码
- Blockers：**无**

## 交付物

| 文件 | 类型 | bytes | sha256 |
|---|---|---:|---|
| `docs/specs/party-direction-v1.md` | 新建（588 行） | 37,767 | `922ede83d9f3af340162edf39ed924f2959c23fab5f682934189bb02523cbc2c` |
| `META/party-direction-prereg-v1.json` | 新建（390 行） | 28,474 | `243f80ba05b3a2c3eddbec7afe28499d00dd9b1ce55b8d7e34e67b0a35dd36e7` |
| `tasks/T-184/BRIEF.md` | 新建 | — | — |
| `tasks/T-184/STATUS.md` | 更新（本文件） | — | — |

- JSON 内 `spec_sha256` = `922ede83…c2c`，与正文重算一致 → **hash 后正文未改**。
- `frozen_at` = `2026-10-29T15:03:27+08:00`。
- 校验：35 条结构化 `source_refs` + 30 处 md 内联「path:line + quote」全部逐字命中，**0 miss**；JSON 无浮点对象；合成算例 V1a（F4/W5/Δ−1）、V1b（F4/W4/Δ0）求和通过。详见 `BRIEF.md` §2。

## 口径要点（验收时先看这四条）

1. **计数**：A 天干位 + B 地支本气位 + C 中余气**同字**透干位 + D 得令（唯一 `+1`）；八位同权，日主/同柱/邻隔均不加成；中气与余气同权；天干戊己中立。
2. **判定**：`Δ = n_F − n_W`；`Δ ≥ +1` 火党严格大于、`Δ ≤ −1` 金水党严格大于、`Δ = 0` → `needs_judgment`。**无比值、无浮点、无第二破平**。
3. **穿制**：一律 `needs_judgment`（`21:L2425` vs `21:L3717` vs `22:L2980` 三方冲突，且「很强大的力量」不可整数化）；**H02 落此条**，答案层 `actor=酉` 不改。
4. **刑**：默认 `mutual`（`22:L2870` 戌未刑两个都坏了）；唯一例外是两字 `丑戌刑` 按党势（`22:L2868`）。

## Execution Log

| 时间 | 动作 |
|---|---|
| 14:50 | 中枢建卡并派发；与 T-183/T-185 并行 |
| 14:47–14:52 | 读卡 + `d01:216–262` + 两份 actor 审计 + `actor-rules-v1.md`；定位 `22/21/19/16/26/28` 原文行并逐字核对 |
| 14:52–14:56 | 写 `docs/specs/party-direction-v1.md`（§1 冻结纪律 / §2 计数口径 / §3 R1–R7 / §4 schema / §5 下游 / §6 覆盖 / §7 禁止 / §8 缺口 / §9 变更 / §10 自检） |
| 14:56 | 首算 md sha256 `31191717…`，写 `META/party-direction-prereg-v1.json` |
| 14:57–15:00 | 校验发现 2 处引用错误（`S13` 实为 `23:L2179`；`22:L426` 带省略号），修正后重算 md sha256 `922ede83…` 并同步 JSON |
| 15:03 | 冻结：`frozen_at=2026-10-29T15:03:27+08:00`；两次重算 83 checks / 0 fails / 30 inline quotes，正文未再改 |
| 15:05 | 写 `BRIEF.md` + 更新本 `STATUS.md`；send_message 回报中枢 |
| 15:10 | 中枢验收：`922ede83…` / `243f80ba…` 与文件一致；35 refs + 30 quotes；无浮点/比值/权重（正文只在禁止项提及）；R4 穿=needs_judgment、R5 刑=mutual、Δ=0=needs_judgment。**H05 决定：接受 Δ=0 → needs_judgment 进主口径，记 needs_judgment 率/覆盖率，不记 ok/reversed。** 提交 |

## 未做 / 风险

- **未实现、未跑盘、未改 engine/hold-out/answers/测试**（卡面要求）。H05 的 `n_F/n_W` 刻意不预写。
- 已知缺口 G1–G8 已逐条写进规格 §8 与 JSON `known_gaps`（水木党未实现、寅申巳亥冲未赋向、`22:L430` 默认未采用、三刑齐不赋向、穿制未整数化、中余气同权、天干土中立、`state` 依赖标注人）。
- 工作区既有脏文件 `META/p1-holdout-baseline-v1.{json,md}`（mtime 14:02:40，早于本卡会话）与 T-185 的 `META/p1-fresh-40-*` 均非本卡产生。
- 唯一需中枢拍板：H05 若 `Δ=0`，是否接受 `needs_judgment` 进主口径（规格 §6.3 已给三落点，默认如实记）。
