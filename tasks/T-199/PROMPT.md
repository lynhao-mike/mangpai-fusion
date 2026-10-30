# T-199 · 合化/合绊 窄实验（段建业 22；≤15 规则；40 例 15/25）

- 状态：🔵 Ready（重定向；冲/263 版作废）
- 依据：WB/Gemini 裁决 + 中枢合成（2026-10-30）
- 前置：main `a062b544`

## 0. 一句话

只做一个决策：**五合/六合的形态判定**（合化 / 合绊 / 争合不化 / needs_anchor）；
只读段建业《盲派初级命理学》（MinerU 22）理论段；用 **≤15 条纯 engine 布尔原子规则**；
40 例（15 训练 / 25 留出，留出先封），留出 ≥80% 已决 + 覆盖率 ≥70% + 优于最高频基线 +20pp。

## 1. 范围（冻结）

- 决策：五合/六合形态，枚举 `化 | 合绊 | 争合不化 | needs_anchor`；
- 不碰：冲的胜负、党势、旺衰、宾主、取象；
- 书：《盲派初级命理学》（MinerU 22）；M1-D 规则条目；
- 样本：40 例，15 训练 / 25 留出；留出先封、hash；规则作者只见训练/理论段；
- 规则：≤15 条；纯 engine 可观测布尔原子；禁文本条件、禁浮点权重；
- 通过：留出 25 例上，已决样本复现作者结论 ≥80%，已决覆盖率 ≥70%，优于“全猜最高频类”基线 +20pp；
- 停：两轮不到即停；若显式结论案例 <15 条，换决策/换书一次；不调阈值、不删案例、不换留出。

## 2. Schema

```yaml
id: H-001
when:            # 全 engine 可观测布尔原子
  edge_kind: wuhe
  pair: [丙, 辛]
  month_branch_wuxing: ...
  huashen_stem_tou: true|false
  competing_stem: ...
  adjacent: true|false
  ke_po: ...
then:
  verdict: 化 | 合绊 | 争合不化 | needs_anchor
  reason: ...
source_ref: sources/duan/MinerU_markdown_22:...
quote: "逐字原文"
scope: ...
```

- 文本条件只作 provenance，不进 `when`；含不可操作化文本条件的规则标 `unoperationalized`，永不触发、只披露；
- 同边两规则相反 → `needs_anchor(rule_a, rule_b)`；书本自带 quote 优先级才可解；
- **needs_anchor 在已决案例上记 miss**，防弃权刷精度；另报“开火者精度”；
- 覆盖率：`n_labeled / n_fired / n_conflict / n_unoperationalized` 四数逐跑公布。

## 3. 标签

- 只抽作者**明文**“合化/合绊/争合不合”句；沉默者排除并计数；
- 双人独立抽取 + 第三人裁歧；κ≥0.85；
- 歧义/两可 → `ambiguous_holdout` 单列，不进分母；
- 留出 25 例在写规则前由第三人切分并 hash；训练 15 只用于规则复核，不用于“一例一规则”；
- 禁为拟合训练案例临时造规则；规则只从理论段/M1-D 导出；
- OCR 噪声先校字（“官位/末食”等）。

## 4. 产物

- `META/t199-cases-train-v1.json`（15）
- `META/t199-cases-holdout-v1.json`（25，sealed+hash）
- `META/t199-rules-v1.yaml`（≤15）
- `tasks/T-199/run_rules.py`（四数/conflict/needs_anchor）
- `META/t199-report-v1.md`（留出精度、覆盖率、基线、κ、歧义）
- `tasks/T-199/BRIEF.md` + `STATUS.md`

## 5. 验收

- 25 留出只跑一次；≥80% 已决、覆盖率 ≥70%、优于基线 +20pp；
- 训练 15 上规则复现 ≥80%；
- κ≥0.85；歧义率 ≤20%；
- 两轮不到即停；不改阈值/不删案例/不换留出；
- P1 卡冻结 R01；P2 不碰；不改 engine/保护区/旧卡/旧 timing。
