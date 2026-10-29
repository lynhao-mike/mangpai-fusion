# T-176 · 3 张真实盘五元组卡（pre-P1 当前能力）

- 状态：🔵 Ready
- 优先级：**P0（让人类尽快看到当前能力 + 缺口）**
- 依据：`docs/specs/single-chart-analysis-v1.md`；`META/single-chart-cases-v1.json`
- 前置：T-169

## 0. 一句话

用当前事实层，对 C1/C2/C3 三张真实盘各出一张**五元组断语卡**；
方向未知就写 `direction_known=false`，救应未判就写 `未判`，缺口照实写。
**这是 pre-P1 能力展示，不是 P1 证明。**

## 1. 三张盘

`META/single-chart-cases-v1.json`：
- C1 `RF-2026-000125` 丁卯 壬子 辛丑 乙未（乾，结构完整）
- C2 `RF-2026-000438` 庚午 戊寅 己未 乙丑（坤，配偶星可查）
- C3 `RF-2026-000894` 壬戌 己酉 庚子 戊子（乾，边界）

## 2. 每张卡必须

1. ① 原局象：宫位 + 十神 + 边 `edge_id`/members；
2. ② 体用宾主：`tiyong` + `direction`；`actor=None` 时 `direction_known=false`、`actor/target=null`；
3. ③ 三态：成局/破局/逢救应化解之一；依据只能 `structure_item` 或 `edge`；
   救应一律 `rescue_judged=未判`（G5），不许写「化解」；
4. ④ 落事：1–2 句结构→人事形态；**不得出现年份/年龄/概率/事件**；
5. ⑤ 双锚点：edge id + 原文 `path:line`；
6. `unknowns`：引用 T-169 §7.3 的缺口 ID（G2/G3/G4/G5/muku_open_close/no_spouse_star/boundary_zi_shi/suiyun_ten_god）。

## 3. 产物

- `docs/demo/single-chart-cards-v1.md`：三张卡（人读）
- `META/single-chart-cards-v1.json`：三张卡（机器）
- 每卡标 `pre_p1: true`；文首写「当前能力展示，非 P1 验证」。

## 4. File Scope

**允许新建**：上述 2 个文件。
**只读**：`META/single-chart-cases-v1.json`、`engine.cli`、`docs/specs/single-chart-analysis-v1.md`、`sources/`。
**禁止**：改 engine/规则/测试/案例 JSON；写预测/年份/事件；git 写操作。

## 5. 验收（中枢亲自看）

- 3 张卡；每张五元组字段齐；
- 每个地址/边能回 `engine.cli`；`actor=None` 的边没有编造主客；
- 没有年份/概率/事件；救应写「未判」；
- 文首标明 pre-P1，不冒充已验证。

## 6. 回报

1. 改动文件；2. 原始输出（3 卡、每卡地址/边数、direction_known 计数）；3. 风险；4. 下游须知（哪些卡在 P1 修复后应重跑）。
