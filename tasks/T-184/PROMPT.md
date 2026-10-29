# T-184 · 党势方向预注册 + needs_judgment/mutual schema 规格

- 状态：🔵 Ready
- 优先级：**P0（党势规则必须先 hash，再跑任何盘）**
- 依据：Opus 裁决 2026-10-29；`d01-deep-read.md:216–262`
- 前置：无（只写规格，不写代码）

## 0. 一句话

把“党势定方向”写成一份**可 hash 的预注册规格**：只允许原文序数比较（严格大于），
无比值/权重/浮点；同时定义 `needs_judgment`/`mutual` 的断言 schema。
**不实现、不跑盘、不改 engine。**

## 1. 规格内容

1. **计数口径**（必须先写死，不能跑后改）：
   - 哪些位置计入：透干、本气、中气、余气分别计多少；是否计日主；是否计藏干；
   - 得令：月支本气/中气/余气怎么算；月令是否加权（只允许整序数，不允许浮点）；
   - 相邻/隔位：是否只计相邻，隔柱是否计；同柱干支是否计；
   - 党：火+燥土（戌未）一党；金+水+湿土（辰丑）一党；其他五行怎么归；
   - 只允许“一方严格大于另一方”，打平/接近一律 `needs_judgment`；**不设 4:1/5:2 等比值**。
2. **按关系类的方向规则**（每条带 `source_ref` + 正例 + 反例）：
   - 子午卯酉冲：原文“一方之党大于另一方”；
   - 巳申合：金水有势申制巳 / 木火有势巳制申；午未合不制、仅相生；
   - 辰戌丑未冲库：燥湿土与五行成势，谁坏谁库；
   - 穿制：原文内部冲突（`d01:251–260`），**一律 `needs_judgment`**，引擎不判；
   - 刑：支持 `mutual`（两败），不硬塞单一 actor；戌未刑“两个都坏了”；
   - 克：方向固定，但“制净/制不净”须 `needs_judgment`，不因克边存在就判成局；
   - 合绊/保护/闭气：`needs_judgment`。
3. **断言 schema**（锚定作用断言）：
   - `palace/ten_gods`、`edge_id`、`direction ∈ {actor→target, mutual, needs_judgment}`、
     `basis`（`fixed_wuxing / party_dominance / source_text / agent_anchor`）、
     `state`（成/败/救应/needs_judgment）、`source_ref`、`verbatim_quote`。
4. **预注册文件**：
   - `docs/specs/party-direction-v1.md`（规则正文）
   - `META/party-direction-prereg-v1.json`（sha256、frozen_at、source_refs、计数口径、禁止项）
   - 在该 JSON 里写死：本规格 hash 之后才允许跑盘；跑后不得改。

## 2. 产物

- 上述两个文件
- `tasks/T-184/BRIEF.md` + `STATUS.md`
- 不写代码、不改 engine/hold-out/answers/测试。

## 3. 验收（中枢亲自看）

- 计数口径可复现、无浮点/比值/权重；
- 每条规则有 `source_ref`、正例、反例；
- H02 明确 `needs_judgment`；刑有 `mutual`；
- 规格 hash 写入 JSON；hash 后不得再改正文。

## 4. 禁止

- 不实现党势规则；不跑任何盘；不为 H02/H05 写专用规则；
- 不用“4:1/5:2”之类比值；不用浮点阈值；不碰 engine。
