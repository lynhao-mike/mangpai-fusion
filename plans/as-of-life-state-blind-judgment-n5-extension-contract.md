# as-of 真实盲断闭环 N=5 扩样合同

> 状态：CONTRACT，独立自审 PASS 后方可进入 IMPLEMENT。
> 触发场景：自主发现长任务 Low-End 调研候选 B（用户指定顺序"先 B 后 E"）。
> 上游冻结报告：[`reports/as-of-life-state-blind-judgment-batch-report.md`](../reports/as-of-life-state-blind-judgment-batch-report.md)（`PASS/COMPLETE — EVIDENCE-BOUNDED FREEZE`，N=3，命中率 2/3，**本合同不重开该报告**）。

## 1. 唯一目标

在不修改上游冻结报告正文的前提下，从已验证安全的 96 个 `C-2026-RF*` / `yaml_key` 候选池（93 个未使用）中，再选出并完整走完两阶段协议（阶段一冻结→阶段二核验）的 **2 个新增独立有效案例**，使累计有效案例从 N=3 提升到 **N=5**，并产出一份独立的增量报告，把新增 2 案的结果与上游 3 案的结果合并计算累计命中率。

## 2. 权威输入与只读依赖

1. [`reports/as-of-life-state-blind-judgment-batch-report.md`](../reports/as-of-life-state-blind-judgment-batch-report.md)（上游冻结事实：已用候选 ID、命中率 2/3、污染记录，只读，不修改）。
2. [`tools/as_of_blind_judgment_probe.py`](../tools/as_of_blind_judgment_probe.py) 的 `truncate_blind_section()`（只读依赖，本合同不修改）。
3. `engine.asof` 公共 API：`natal_capacity`、`daiyun_context`、`event_candidate`、`consultation_freeze`、`reality_translation`、`session_contract`、`session_runner`、`career_state_builder`、`state_ledger`（只读依赖，本合同不修改）。
4. 上游合同的 §6.6 根源×完成方式白名单（[`plans/as-of-life-state-blind-judgment-first-proof-point-contract.md`](as-of-life-state-blind-judgment-first-proof-point-contract.md) §6，原样沿用）。

## 3. 候选池与排除清单

### 3.1 永久排除（继承上游全部记录）

上游报告已排除的 13 个案例 + 本会话已触碰的全部 Mang.pai 池（007/008/009/010/011/012/017）+ 已使用的 3 个 RF 案例（RF000026/RF000057/RF000108）**全部继续排除**，不得重复使用。

### 3.2 新候选池

上游安全审计已确认的 96 个 `C-2026-RF*` / `yaml_key` 候选中，扣除已用 3 个，剩余 93 个为本合同候选池。本合同从中一次性预冻结 **3 个新候选**（目标 2 个有效 + 1 个污染/无效缓冲），选择规则：按案例 ID 字典序取排除已用后的下 3 个（`RF000121`、`RF000123`、`RF000125`），不得凭主观偏好挑选。

## 4. 两个不可逆阶段（原样沿用上游协议）

阶段一（冻结盲断）与阶段二（揭示核验）的执行顺序、`feedback_opened` 时序要求、哈希幂等验证要求，与 [`as-of-life-state-blind-judgment-first-proof-point-contract.md`](as-of-life-state-blind-judgment-first-proof-point-contract.md) §5 完全一致，不重新定义。

## 5. 写集白名单

只允许新增：

1. 每个新案例：`cases/<case_id>/asof-blind-judgment-batch-frozen-draft.json`
2. 每个新案例：`cases/<case_id>/asof-blind-judgment-batch-verified-result.json`
3. `reports/as-of-life-state-blind-judgment-n5-extension-report.md`（本任务唯一新报告，独立于上游报告，不修改上游报告正文）
4. 截断/安全审计临时文件（`.tmp.md`/`.tmp.py`/`.tmp.txt`），使用后立即删除

**禁止修改**：上游冻结报告 [`reports/as-of-life-state-blind-judgment-batch-report.md`](../reports/as-of-life-state-blind-judgment-batch-report.md)、`engine/asof/` 任何文件、[`tools/as_of_blind_judgment_probe.py`](../tools/as_of_blind_judgment_probe.py)、任何既有测试、任何案例既有的 `input.md`/`feedback.md`/`statement_index.json`、`handoff.md`。

## 6. 污染处理规则（沿用上游协议）

同一会话累计污染 3 次触发硬停止；若在 3 个预冻结新候选中遇到污染，按上游协议记录后可换用候选池中的下一个候选（字典序继续，不超过污染预算）。

## 7. Gate 执行顺序

- **Gate ADMISSION**：已完成，见本任务 High-End 阶段记录，`PASS`。
- **Gate 格局判断**：已完成，`PASS`。
- **Gate CONTRACT**：本文件；完成后做逻辑新鲜独立自审。
- **Gate IMPLEMENT**：对 3 个预冻结候选逐个执行两阶段协议，直到累计新增 2 个有效案例或候选池耗尽。
- **Gate STATIC_REVIEW**：核对每案的 `feedback_opened=false` 时序、白名单组合、写集合规。
- **Gate VERIFY**：对全部新增案例做冻结哈希幂等复跑，记录真实命令输出。
- **Gate EVIDENCE_REVIEW**：逻辑新鲜独立核对累计命中率计算、禁止推断边界。
- **Gate FREEZE**：产出独立增量报告，最终裁决二选一。

## 8. STOP 条件

- 污染预算耗尽（3 次）且新增有效案例 < 2；
- 需要修改 `engine/asof/` 或上游冻结报告才能完成；
- 需要执行任何 Git/GitHub 操作。

## 9. 已知的方法论局限（原样继承）

与上游报告 §6 完全一致：单会话自我执行的"先冻结后揭示"协议无法被加密学证明；小样本统计（N=5）仍不构成统计显著性。本合同额外声明：候选选择规则（字典序取前 3 个）本身不是随机抽样，不能消除选择偏差；若未来需要更严谨的统计推断，应改用真随机抽样协议。

## 10. 最终裁决的两种可能取值

- `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`（累计有效案例 N≥5，命中率以分数呈现）；
- `BLOCKED — <具体原因>`（候选池在污染预算内未能产出足够新增有效案例）。

## 11. 逻辑新鲜独立自审

- 目标唯一且可判定（N=3→N=5，明确数字）：**PASS**。
- 写集白名单与上游报告解耦，不构成"重开冻结报告"：**PASS**。
- 候选选择规则客观、可复现（字典序），不依赖主观判断：**PASS**。
- Gate 顺序与上游协议一致，未引入新的未定义步骤：**PASS**。
- STOP 条件明确，不存在无限重试风险：**PASS**。

**本合同自审结论：`PASS`，进入 IMPLEMENT。**

`LOCAL ONLY / NOT PUSHED`
