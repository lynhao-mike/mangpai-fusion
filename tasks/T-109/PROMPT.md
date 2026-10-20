# T-109 · 查清 `index-new.yaml` 41 条规则的来龙去脉

## Review Level: 1

> 纯只读勘察，零写操作。

## Context（中枢已核实，Worker 无需重复验证）

| 事实 | 值 |
|---|---|
| `theory/ziping/index.yaml` | 933 条，全部 `ZP-PROD-20260622-*` 批次 |
| `theory/ziping/index-new.yaml` | 41 条，全部 `ZP-PROD-20260623-*` 批次，全部 `status: active` |
| 两者重叠 | **0**（按 id / title / claim 三重比对） |
| 能生成 `20260623` 的脚本 | **无**（`grep 20260623 --include=*.py` 零命中） |
| `extract_ziping_production_rules.py:220` | 写死生成 `20260622` 编号 |
| `index-new.yaml` 的 `notes` | 「由旁路候选规则批量提升为正式生产生成规则；所有 candidate 均转为 active，可被默认 pipeline 与双引擎理论层加载。」 |
| 引用它的冻结 case | 5 个：`C-2026-RF000343`、`RF000417`、`RF000441`、`RF000763`、`RF000897` |

**关键矛盾**：`notes` 承诺「可被默认 pipeline 加载」，但构建链根本不读这个文件。**这是设计与实现的脱节。**

## Objective

回答 6 个问题，为「这 41 条该并入还是该废弃」提供决策依据。

## Steps

### Step 1: 41 条完整清单

列出每条的 id、title、topic、domains、trigger、status，按 topic 分组统计。

### Step 2: 与 20260622 批次的语义关系

- 是 20260622 某条的修订版？（比对 title/claim 文本相似度）
- 是完全未覆盖的新主题？
- 还是替代了某条？

用具体例子说明，不要只给结论。

### Step 3: 「旁路候选规则批量提升」的源头

- 搜索 `theory/ziping/_cleaned/`、`theory/_ir/`、`theory/raw/ziping/` 有无 20260623 前身
- 用 `git log --oneline -- theory/ziping/index-new.yaml` 查提交历史
- 用 `git log -1 --format=%B <commit>` 看引入提交的说明
- 判断「提升」是人工做的还是有脚本做的

### Step 4: 5 个 case 的引用明细

逐条列出每个 case 的 locator 及对应的行号范围，并指出该范围覆盖哪几条规则 id。

### Step 5: 并入 index.yaml 的可行性

- id 是否冲突（预期不冲突）
- topic 命名是否与 20260622 一致
- **`conditions.trigger` 用的是英文枚举还是中文？**
  （关键是：能否被 `engine/predicates/condition_evaluator.py` 的
  `evaluate_trigger` 求值。枚举只有 16 个英文名：
  always / has_energy_structure / has_tiaohou_advice / wuxing_imbalanced /
  has_zhi_chong / has_dayun / has_xiaoyun / has_liunian /
  has_suiyun_interaction / has_sanhe_partial / has_sanxing / has_kongwang /
  has_zaisha / has_wealth_picture / has_official_picture / has_marriage_picture）

### Step 6: 构建链改法建议

指出 `tools/extract_ziping_production_rules.py` 里该在哪里、怎么改才能让
`20260623` 批次进入 index.yaml（只给建议，不写代码）。

## File Scope

**只读**：
- `theory/ziping/index.yaml`
- `theory/ziping/index-new.yaml`
- `tools/extract_ziping_production_rules.py`
- `engine/predicates/condition_evaluator.py`（只看 `evaluate_trigger` / `trigger_evidence_status` 的枚举表）
- `cases/C-2026-RF000343|417|441|763|897/asof-blind-freeze.json`
- `theory/ziping/_cleaned/`、`theory/_ir/`、`theory/raw/ziping/`（只读）

**唯一可写**：
- `tasks/T-109/BRIEF.md`（任务卡已由中枢写好，你**不需要**自己写卡）
- `tasks/T-109/STATUS.md`

## Do NOT

- **禁止修改任何文件**（除了上面列的两个 STATUS/BRIEF）
- **禁止执行 `extract_ziping_production_rules.py`**（会重写 index.yaml）
- **禁止执行 `git commit` / `checkout` / `stash` / `reset` / `clean`**
- **禁止运行 `tools/build_indexes.py`**
- 禁止读取 File Scope 之外的文件
- read-only git 操作（log / show / diff）允许

## Completion Criteria

| # | 命令 | 期望 |
|---|---|---|
| 1 | `git status --porcelain` | 除 `tasks/T-109/` 外无新增改动 |
| 2 | `git diff --stat` | 不含 theory/ engine/ cases/ 的改动 |
| 3 | `tasks/T-109/BRIEF.md` 存在 | 6 个问题全部有答案，Step 5 有逐条 trigger 枚举判定表 |
