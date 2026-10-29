# T-175 · P1 hold-out 独立策展（只读）

- 状态：🔵 Ready
- 优先级：**P0（P1 的独立尺子）**
- 依据：`docs/reviews/p1-direction-recall-verdict-v1.md`；独立 Agent 3 周计划
- 前置：无（不得读 33 条标注/结果）

## 0. 一句话

策展 **20 例非名人、非 dev 的段派命例**，每例有原书明确的主功关系（谁对谁、怎么作用）与原文锚点；
盲测输入与答案物理分离，先冻结。**只读，不写推演器、不改代码。**

## 1. 与 dev 集的隔离

- **不得读** `E:\Git hub\mangpai-fusion-rethink\META\golden-20-core-edges-v1.json`、
  `golden-20-core-edge-recall-v1.json`，也不得读 `META/golden-20-answers-v1.json` 的答案字段。
- 可读 `META/golden-20-v1.json` 的 `case_id`/四柱（仅用于排除 dev 20 例）。
- 可读 `META/golden-20-core-edges-v1.json` 的 **case_id 列表**（如需要）以排除；不得读 claims。
- 选例与标注独立完成；不看 33 条结论。

## 2. 选例标准

- 来源：`sources/duan/` 教材/案例集；原文有完整主功关系（制/化/墓/救应之一）的命例。
- **非名人**：原文若出现「中堂/首相/领袖/主席/皇帝/名人/阎命」等身份/结局标签，剔除。
- **非 dev**：不与 `META/golden-20-v1.json` 的 20 例重复（同盘/同四柱/同 source 行）。
- 20 例目标；四类尽量各 ≥3；不足如实报，不凑数。
- 每例至少有 1 条「A 对 B 作用」的原书明确关系，且 `actor` 可由原文确定；
  原文只说「某神旺/某宫动」而无施力方的，不算 P1 可用例。

## 3. 产物

- `META/p1-holdout-v1.json`：盲测输入（case_id/四柱/性别/source；不含答案）
- `META/p1-holdout-answers-v1.json`：每例 `core_work_relations[]`（a/b/kind/actor/quote/source_ref）
- `META/p1-holdout-v1.md`：20 例清单、四类、非名人/非 dev 校验、缺口
- 可选 `tests/tools/test_p1_holdout_schema.py`

## 4. File Scope

**允许新建**：上述 3 个 META 文件 + 可选测试。
**只读**：`sources/duan/`、`theory/`、`META/golden-20-v1.json`（仅 case_id/四柱）、`engine.cli`。
**禁止**：读 33 条 claims/结果答案；改 sources/theory/engine/规则/测试；git 写操作。

## 5. 验收（中枢亲自看）

- 20 例（或如实报实际数）；非名人/非 dev 可核；
- 每例有 ≥1 条原书明确主功关系，actor 可由 quote 支撑；
- 盲测/答案分离；quote 逐字；
- 若 <15 例，明确写「hold-out 不足，P1 不可裁决」。

## 6. 回报

1. 改动文件；2. 原始输出（例数、四类、非名人/非 dev 校验）；3. 风险；4. 下游须知（P1 评分输入/阈值）。
