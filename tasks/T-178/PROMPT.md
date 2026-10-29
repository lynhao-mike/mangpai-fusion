# T-178 · 墓 actor 约定审计 + actor 规则表（只读规格）

- 状态：🔵 Ready
- 优先级：**P0（方向召回 5% 的语义根因）**
- 依据：`docs/reviews/p1-baseline-verdict-v1.md`；T-177 基线
- 前置：hold-out 冻结 v2

## 0. 一句话

把 P1-H13–H16 四条「墓用」的 `a/b/actor` 与原文逐条核对，判定是**标注约定反了**还是**引擎 actor 反了**；
同时产出 `actor 规则表`（合/冲/刑/穿/化/墓），每条带 `source_ref`，供修复与 P1 评分共用。
**只写规格/审计，不写代码。**

## 1. 墓用审计（P1-H13–H16）

逐条读 `META/p1-holdout-answers-v1.json` 的 `a/b/kind/mechanism/actor/quote/source_ref` 与原文：

1. 原文说的是「X 入 Y 墓」还是「Y 墓 X」？主语是谁？
2. `a` 是**入库方**还是**库**？`actor` 是主语还是库？
3. 引擎 `relations.muku` / muku 候选的 `actor` 是入库方还是库？
4. 判定：
   - `label_wrong`：标注把库当施力方；给出更正（原文 + 应填 a/b/actor）。
   - `engine_wrong`：引擎 actor 反了；给出应改的方向。
   - `convention_conflict`：原文本身两种读法并存；标为不可入方向分母。
5. 四条逐条结论 + 一个总判定；不改 answers 文件，只在审计报告里给更正建议。

## 2. actor 规则表（`docs/specs/actor-rules-v1.md`）

按关系类给规则，每条带 `source_ref`（path:line）：

| 类 | 规则 | 未知时 |
|---|---|---|
| 合（五合/六合/暗合/干支自合） | 原文有主语（「A 合 B」）才给 actor；对称句给 null | null |
| 冲（六冲/天干冲） | 同上；「A 冲 B」才给 | null |
| 刑 | 同上 | null |
| 穿/害 | 同上 | null |
| 破 | 同上 | null |
| 克 | 施力方是克者；engine `ke` 的 members 顺序 | null |
| 生/化/泄 | 取句法主语；「A 生 B」A 是 actor；化是生的一种 | null |
| 墓 | 先由 §1 定：入库方 vs 库；未定前 null/definition_conflict | null |

要求：
- 不许用五行流向代替句法主语（T-174 复核的 3 条教训）；
- 对称关系不强行赋向；
- 每条规则给一个真实原文例子 + 一个反例；
- 规则表冻结后，`structure_check.py` 只按表实现，不按 case 调。

## 3. 产物

- `META/p1-muku-actor-audit-v1.json` / `.md`：四条审计 + 总判定
- `docs/specs/actor-rules-v1.md`：规则表 + 原文例子
- `tasks/T-178/BRIEF.md` + `STATUS.md`

**禁止**：改 answers/hold-out/engine/规则/测试；写代码；git 写操作。

## 4. 验收（中枢亲自看）

- 四条墓用逐条有原文 quote 与判定；
- 规则表每类有 `source_ref` 和例子；
- 明确回答：P1 方向主分母 16 是否成立；四条墓用是否该剔除/更正；
- 不改任何既有文件。

## 5. 回报

1. 改动文件；2. 四条墓用判定；3. 规则表覆盖/缺口；4. 下游须知（P1 分母是否变、修复按哪条规则）。
