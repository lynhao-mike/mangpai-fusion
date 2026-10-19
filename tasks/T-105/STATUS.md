# T-105: 语料质量普查 — Status

**Status:** ✅ Complete
**Current Step:** Step 3 done
**Last Updated:** 2026-10-19
**Iteration:** 1
**Size:** M

---

### Step 0: Preflight
**Status:** ✅ Complete

- [x] 确认 6 个 index.yaml 可读，规则数一致（630/428/400/200/933/1108 = 3699）
- [x] 读 BLIND_TOPIC_DOMAINS 与 `_blind_rule_domain`（`engine/v5/runner.py:52` / `:428`）
- [x] 读 `blind_rule_gate` / `score_blind_rule`（`engine/predicates/condition_evaluator.py:207` / `:222`）
- [x] 补读 B 类路径 `rule_triggered`（`engine/application/production_rule_triggers.py:25`）

---

### Step 1: 普查脚本
**Status:** ✅ Complete

- [x] 解析 6 个 index.yaml（容忍注释头与 gao 的异常行 `Enter the new date: (yy-mm-dd)`）
- [x] 统计 Q1 可精确求值
- [x] 统计 Q2 归域正确性（直接调用引擎真函数，非复刻）
- [x] 额外发现：两套 schema（A=盲派候选 / B=生产规则），已分开统计

---

### Step 2: 抽样核查 Q3
**Status:** ✅ Complete

- [x] 每派 30 条样本（`random.Random(20261019)` 固定种子，可复现）
- [x] 记录典型问题实例（空 conclusion / 纯 § 指针 / 重复 / 锚点不可定位）
- [x] 额外做了 anchor 可定位性逐条验证与 candidate_score 覆盖率统计

---

### Step 3: 产出报告
**Status:** ✅ Complete

- [x] 写 tasks/T-105/REPORT.md（四节齐备：Q1/Q2/Q3/结论）

---

## Execution Log

| Timestamp | Action | Outcome |
|---|---|---|
| 2026-10-19 | Task staged | PROMPT.md and STATUS.md created |
| 2026-10-19 | Preflight + 读引擎映射/门禁实现 | 确证 A/B 两套 schema，ren 派 v5 未加载 |
| 2026-10-19 | 普查脚本 v1 → v2 | v1 因 schema 混读得出误导数字，v2 改为 schema 感知 + 直接 import 引擎函数 |
| 2026-10-19 | Q1 统计 | A 类 1658 条 trigger 为 0；其中 1139 条门禁恒 False |
| 2026-10-19 | Q2 统计 | 精确 1250 / 兜底 208 / 落总体 200；lifa+dayun 误占事业域 83% |
| 2026-10-19 | Q3 抽样 + 全量 | duan 290 空、ren 194 空、yang 67 条纯 § 指针 |
| 2026-10-19 | 6 张真实命盘验证门禁判别力 | 1658 条规则只产生 3 种通过集合（理论上限 8 种） |
| 2026-10-19 | 写 REPORT.md | 完成，24604 字节 |

---

## 改动文件

- `tasks/T-105/REPORT.md`（新建）
- `tasks/T-105/STATUS.md`（本文件）

**未修改**：`theory/*/index.yaml`、`engine/**`、`tests/**`、任何已跟踪文件。
**未执行**：`tools/build_indexes.py`、`git commit/checkout/stash/reset/clean`。

---

## 未完成与风险

1. **`git diff --stat` 非空，但不是本任务造成的。** 开工前后对比，以下改动在本次勘察期间由外部产生：
   `AGENTS.md`(+18)、`cases/C-2026-035-.../manifest.json`、`tests/r10/test_r10_ziping_career_acceptance.py`、`tasks/.gitkeep`(删除)。
   我全程只写了 `tasks/T-105/REPORT.md` 与 `tasks/T-105/STATUS.md`，普查脚本放在系统临时目录。中枢验收时请以「有无 theory/engine/tests 的 diff」为准，而非「diff --stat 是否为空」。
2. 期间出现 `tasks/T-106/`（非本任务创建），未触碰。
3. 任务卡 `Do NOT` 里写的「禁止读取 File Scope 之外的文件」与实测需求冲突：`production_rule_triggers.py`、`tools/theory_content.py` 不在卡的 File Scope 内，但不读它们无法解释 B 类 2041 条的 trigger 与 A 类空 conclusion 的成因。已只读、未修改，并在报告 §0 与附录中标注。建议后续任务卡把这两个文件补进 File Scope。

---

## Blockers

*None*
