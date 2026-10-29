# T-180 · 化 actor 约定审计（只读）

- 状态：🔵 Ready
- 优先级：**P0（defined16 里 4 条化的语义根因）**
- 依据：`docs/reviews/p1-postfix-candidates-verdict-v1.md`；T-178 墓审计模板
- 前置：T-179 已合并；hold-out 冻结 v3

## 0. 一句话

对 P1-H09–H12 四条「化」逐条核对 `a/b/actor` 与原文：答案把 `a` 当施力方，引擎 `sheng` 候选把 `b` 当施力方。
判定是 `engine_wrong` / `label_wrong` / `convention_conflict`；并给「化者 vs 被化者」的规则条款。
**只读审计，不改 answers/engine/测试。**

## 1. 输入

- `META/p1-holdout-answers-v1.json` 的 P1-H09–H12
- `META/p1-holdout-postfix-candidates-v1.json` 的对应 candidates（`sheng` actor=b 端）
- `docs/specs/actor-rules-v1.md` §4.8（化）
- `sources/` 原文（按 source_ref）
- `engine/facts/structure_check.py` 的 sheng 候选生成（只读）

## 2. 审计内容

逐条：

1. 原文说「A 化 B」时，A 是**化者**还是**被化者**？谁在施力？
2. 答案 `a`/`actor` 对应哪一端？引擎 `sheng` 的 `actor`（members[0]）对应哪一端？
3. 判定：
   - `engine_wrong`：原文力向与答案一致，引擎 actor 反了；
   - `label_wrong`：答案把被化者当 actor，给出更正；
   - `convention_conflict`：原文两种读法并存，标 `definition_pending`，不进方向失败。
4. 给条款：化的 actor 规则（化者/被化者；官杀→印、合化、从化分别怎么算）；
   每条带 `source_ref` + 正例 + 反例。
5. 明确：4 条化在 P1 方向主分母里该算 ok/reversed/definition_pending 哪一类；冻结 v4 建议。

## 3. 产物

- `META/p1-hua-actor-audit-v1.json` / `.md`
- `docs/specs/actor-rules-v1.md` 的「化」条款修订建议（写进审计 MD，不直接改 spec）
- `tasks/T-180/BRIEF.md` + `STATUS.md`

**禁止**：改 answers/hold-out/engine/规则/测试；写代码；git 写操作。

## 4. 验收（中枢亲自看）

- 四条逐条有 quote + 判定；
- 化者/被化者条款有 source_ref、正例、反例；
- 明确回答：defined16 的 4 化该算 ok/reversed/pending；
- 不改既有文件。

## 5. 回报

1. 四条判定；2. 化条款；3. defined16 是否变、冻结 v4 建议；4. 有没有 Blockers。
