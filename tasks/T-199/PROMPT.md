# T-199 · 冲的胜负/方向 窄实验（段建业 263 例）

- 状态：🔵 Ready
- 依据：Opus 裁决（2026-10-30）；A+ kill；R-tool pass；P0 gate 过
- 前置：main `d295ecd7`

## 0. 一句话

只做一个决策：**原局单冲“谁去”**；只读段建业《盲派批命案例集》263 例；
抽 30 例（训练 20 / 留出 10，留出先封），写 30–50 条**可执行规则**，用**规则引擎**跑；
留出 ≥8/10 且覆盖率 ≥70% 才算形式化成立；两轮不到即停。

## 1. 范围（冻结）

- 决策：冲的胜负/方向（谁去），不碰合化/旺衰/党势/宾主/取象；
- 书：段建业《盲派批命案例集》263 例；不跨书；
- 样本：30 例，训练 20 / 留出 10；留出先封、规则后写；
- 通过：留出 ≥8/10 且覆盖率 ≥70%；
- 停线：两轮不到 80% 即停，不调阈值、不删案例、不换留出；
- 周期：4 周；P1 冻结在 R01，不并行；P2 不碰。

## 2. 抽取

- 只抽作者**显式冲句**：“冲去/冲坏/冲不解/冲起/冲散”等；
- 禁止由“离婚/发财/升职”反推冲的方向；反推即泄漏；
- 双人独立抽取（人+Agent 或两次 Agent）+ 人工裁决；记 κ，<0.8 重抽；
- 歧义（“或”、需岁运补足、原局无单冲）→ `excluded_ambiguous`，不入分母；歧义率 >20% 判书/决策错；
- OCR 噪声（“官位”“末食”等）先校字；每例保留 `source_ref` + 逐字 quote；
- 留出 10 例的四柱不得出现在规则举例/训练集中。

## 3. 规则 schema

```yaml
id: C-001
when:
  pair: [子, 午]
  positions: [Y.b, D.b]
  adjacent: true
  edge_id: e007
  ten_gods: ...
  month_order: ...
  roots: ...
  strength_version: "engine@<hash>"
then:
  verdict: 子去 | 午去 | 两伤 | needs_anchor
  reason: ...
except: []
specificity: 3
source_ref: sources/duan/...:L123
quote: "逐字原文"
```

- `when` 全部 engine 可观测；禁止“旺/有力/气势”等文本词；
- 力量只用 engine 冻结分数/版本；
- quote 必须能映射到一条 engine 边/地址；映射不上→规则不得触发，只产 `needs_anchor`；
- 同一冲边两条规则相反→`conflict` + `conflict_with[]`；按预注册 `specificity` 消解；消不掉→`needs_anchor`。

## 4. 产物

- `META/t199-cases-train-v1.json`（20）
- `META/t199-cases-holdout-v1.json`（10，先封，hash）
- `META/t199-rules-v1.yaml`（30–50 条）
- `tasks/T-199/run_rules.py`（规则引擎/冲突/覆盖）
- `META/t199-report-v1.md`（留出 8/10、覆盖率、κ、歧义、conflict）
- `tasks/T-199/BRIEF.md` + `STATUS.md`

## 5. 验收

- 留出 10 例只跑一次；≥8/10 且覆盖率 ≥70%；
- 训练 20 例规则复现 ≥80%；
- κ≥0.8；歧义率 ≤20%；
- 两轮不到即停；不改阈值/不删案例/不换留出；
- 不碰 P1/P2/engine/保护区/旧卡/旧 timing。
