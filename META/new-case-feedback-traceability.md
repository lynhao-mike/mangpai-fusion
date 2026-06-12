# P6-A1 New Case Feedback Traceability Audit

- 审计 ID：P6-A1
- 审计范围：最近 20 个已完成反馈闭环的案例（`META/iteration-state.json` 中 `completed_case_ids`）
- 审计方式：只读（仅读取 `cases/<case_id>/` 与 `reports/` 下文件，未修改 `theory/`、`engine/`、`tests/`、`META/project-state.json`）
- 审计日期：2026-06-12
- 审计脚本：`tools/_audit_p6a1.py`
- 审计原始数据：`META/new-case-feedback-traceability.json`

---

## 1. 审计对象

最近 20 个"反馈已完成"案例（按 `META/iteration-state.json::completed_case_ids`）：

| # | case_id | statement_records.json | records 条数 | 报告 [S-xxxx] | feedback [S-xxxx] |
|---|---|---:|---:|---:|---:|
| 1 | C-2026-001-乾-庚申戊寅壬子辛丑 | ✅ | 0 | 0 | 0 |
| 2 | C-2026-002-坤-壬戌庚戌戊辰丙辰 | ✅ | 0 | 0 | 0 |
| 3 | C-2026-007-乾-乙丑庚辰己丑庚午 | ✅ | 0 | 0 | 0 |
| 4 | C-2026-008-坤-壬申癸卯丁未壬寅 | ✅ | 0 | 0 | 0 |
| 5 | C-2026-009-乾-庚辰乙酉丙申乙未 | ✅ | 0 | 0 | 0 |
| 6 | C-2026-010-坤-甲子丁卯癸卯庚申 | ✅ | 0 | 0 | 0 |
| 7 | C-2026-011-乾-乙丑乙酉丁丑癸卯 | ✅ | 0 | 0 | 0 |
| 8 | C-2026-012-坤-壬戌癸丑丙申壬辰 | ✅ | 0 | 0 | 0 |
| 9 | C-2026-013-坤-壬申甲辰丙辰己丑 | ✅ | 0 | 0 | 0 |
| 10 | C-2026-014-乾-丙戌庚子乙亥辛巳 | ✅ | 126 | 0 | 0 |
| 11 | C-2026-015-乾-甲寅乙亥丙辰辛卯 | ✅ | 111 | 0 | 0 |
| 12 | C-2026-018-坤-乙丑戊寅乙酉乙酉 | ✅ | 0 | 0 | 0 |
| 13 | C-2026-025-坤-辛未乙未甲辰乙亥 | ✅ | 10 | 0 | 10 |
| 14 | C-2026-026-坤-癸未甲寅壬戌丙午 | ✅ | 10 | 0 | 10 |
| 15 | C-2026-RF000345-乾-癸酉乙丑乙卯乙酉 | ✅ | 19 | 0 | 3 |
| 16 | C-2026-RF000441-乾-癸亥己未己未庚午 | ✅ | 18 | 0 | 2 |
| 17 | C-2026-RF000864-乾-己巳丙子乙卯甲申 | ✅ | 18 | 0 | 3 |
| 18 | C-2026-RF000243-坤-己卯己巳戊午丁巳 | ✅ | 16 | 0 | 4 |
| 19 | C-2026-RF000524-坤-己巳丙寅戊戌丁巳 | ✅ | 16 | 0 | 4 |
| 20 | C-2026-032-乾-癸酉乙卯戊戌甲寅 | ✅ | 7 | 0 | 0 |

> 备注：第 13–14、20 行还分别存在 `statement_rule_map.json`；第 10–11、13–20 行还存在 `findings/` 子目录；并非所有 case 都有 `content-report`（V2 单报告），`analyst-report` / `blind-report` / `events` / `career-projection` / `portrait-v2` 等历史/并行报告形态仍散布在 `reports/` 与 case 目录中。

---

## 2. 统计

| 指标 | 数值 |
|---|---:|
| 审计案例数 | 20 |
| `statement_records.json` 存在 | 20 / 20（100%） |
| `statement_records.json::records` 非空 | 10 / 20（50%） |
| `statement_records.json::records` 总条数 | 351 |
| 报告（含 content-report / analyst-report / blind-report / events）含 `[S-xxxx]` | **0 / 20** |
| 报告层 `[S-xxxx]` 总出现次数 | **0** |
| `feedback.md` 含 `[S-xxxx]` 的 case | 7 / 20（35%） |
| `feedback.md` 中 `[S-xxxx]` 总出现次数 | 36 |
| 任意 `.md`（含 analysis / lessons / portrait / career / events）含 `[S-xxxx]` | 7 / 20（与 feedback 重合） |
| `reference coverage` = report_sid_total / sr_total_records | **0 / 351 = 0%** |
| `feedback coverage` = fb_sid_total / sr_total_records | 36 / 351 ≈ 10.3% |
| 跨表 join 可行性 | 仅有 7 个 case 可 join（仅限 `feedback.md ↔ statement_records.json`） |

> 参考基线：最近 20 个"反馈已完成"案例实际可学习的样本，仅来自 7 个 case，且这 7 个 case 的 `[S-xxxx]` 引用完全位于 `feedback.md`，**不位于用户可读报告正文**。

---

## 3. 四个必须回答的问题

### A. 用户是否能看到 statement_id？

**不能。**

- 20 个 case 的用户可读报告（`reports/<case>-content-report.md` / `analyst-report.md` / `blind-report.md` / `events.md` 等）经过全量正则扫描，**0 / 20 含 `[S-xxxx]` 引用**。
- 唯一能看到 `[S-xxxx]` 的位置是：
  - `cases/<case>/analysis.md`（过程稿，含 4 派推理与 statement_index 引用）—— 0 个 case 命中。
  - `cases/<case>/feedback.md`（反馈表）—— 7 / 20 命中。
  - `cases/<case>/statement_index.json`（机器结构）—— 不在用户阅读路径上。
- 按 V2 规范"展示层禁显约束"（`AGENTS.md` §5.2 展示层禁显），**报告正文禁止展示 statement_id**；但这导致用户无法在报告上做精确到句柄的反馈。

### B. 用户是否能够针对 statement_id 反馈？

**不能直接做到。**

- 报告层没有 `[S-xxxx]` 锚点，命主/分析师在阅读报告时拿不到稳定句柄。
- 即便 `feedback.md` 模板已经预留 `[S-xxxx] [y/n/?/skip] ...` 字段（025/026 是范例），这个引用**必须由分析师在 case 内部手工建立**，而不是用户在报告上点选。
- 对 0 个 statement_records 的 10 个 case（C-2026-001/002/007/008/009/010/011/012/013/018），连"分析师手工建立"都没有锚点可言，feedback 仍是自由文本"应验/失验"表（见 `cases/C-2026-001/feedback.md` §二、§三）。
- C-2026-014 / 015 有 126 / 111 条 records 但 feedback.md 没有 `[S-xxxx]` 引用，**结构化判语和反馈完全脱钩**。

### C. feedback 是否能直接 join statement_records？

**部分可以，比例 7 / 20。**

- 7 个 case（025/026/RF000345/RF000441/RF000864/RF000243/RF000524）的 `feedback.md` 写入的 `[S-025-d1a001]`、`[S-RF000345-000cf8]` 等，能与 `statement_records.json::records[*].statement_id` 字符串精确 join。
- 抽样验证：以 `cases/C-2026-025-坤-辛未乙未甲辰乙亥` 为例，feedback 中 `S-025-d1a001` → statement_records 中 `S-025-d1a001`（statement_text="财厚劫透，适合资源整合，忌人情财务混杂"）→ join 成功。
- 但 join 后发现**记录本身质量偏低**：rule_id / family_id / school / canon / rule_type 全部为 `UNMAPPED`，`needs_mapping_repair=true`，`confidence_snapshot` 退化到 `fallback_initial`（star=0, percent=0.0, sample_n=0）。即使 join 成功，落库的也不是可学习的"判语-反馈"对，而是**未对齐规则的占位 statement**。
- 另 13 个 case（包含 014/015 这种 record 数量 100+ 的）feedback 没有 `[S-xxxx]`，**完全无法 join**。

### D. 当前系统是否已经具备产生 learnable sample 的能力？

**不具备，仍 BLOCKED。**

- "可学习样本（learnable sample）"的最小定义 = `(statement_record, feedback_verdict, rule_id, family_id, confidence_delta)` 五元组在生产链路里可被持久化、并能反查回规则。
- 现状：

| 必要条件 | 现状 |
|---|---|
| `statement_records.json` 存在 | ✅ 20 / 20 |
| `statement_records.json::records` 非空 | ⚠️ 10 / 20（50%）；其余 50% 是 `[]` 占位 |
| records 中 `rule_id / family_id / school / canon / rule_type` 已对齐 | ❌ 抽样全部为 `UNMAPPED`，`needs_mapping_repair=true` |
| 报告层出现 `[S-xxxx]` 锚点 | ❌ 0 / 20 |
| `feedback.md` 引用 `[S-xxxx]` | ⚠️ 7 / 20（且集中在 025/026/RF000345/441/864/243/524） |
| `feedback` ↔ `statement_records` 可 join | ⚠️ 7 / 20（受限于上一步） |
| 命主能基于报告句柄给反馈 | ❌ 报告无句柄，命主只看到"应验/失验"表 |
| 反馈能反哺到 rule 校准 | ❌ rule 仍为 `UNMAPPED`、confidence 为 `fallback_initial` |

四项硬性失败：
1. **报告层不展示 `[S-xxxx]`** → 命主无法基于报告做句柄级反馈；
2. **statement_records 中 50% 是空集** → 没有可学习对象；
3. **statement_records 中 rule 元数据为 UNMAPPED** → 即使有反馈也回不到规则；
4. **feedback 引用率 35%** → 多数案例的反馈无法 join。

---

## 4. 结论：BLOCKED

判定：**BLOCKED**。

证据摘要：
- `report_sid_total = 0`（0 / 20 报告含 `[S-xxxx]`）；
- `sr_with_records = 10 / 20`；
- `fb_with_sid = 7 / 20`，且 `fb_sid_total = 36`；
- `reference coverage = 0 / 351 = 0%`；
- `feedback coverage = 36 / 351 ≈ 10.3%`；
- 已 join 案例的 records 抽样 `rule_id = UNMAPPED`，不符合 learnable sample 必要条件。

要解除 BLOCKED，需要至少同时满足（属于 P6 后续子任务，不在本次只读审计范围内）：
1. 报告渲染时输出隐藏式 `[S-xxxx]` 锚点（或同义稳定句柄），命主可读；
2. statement_records 中 50% 空集需要回填（P5-7 migration 标注 `source: P5-7 historical statement record migration` 但 records 仍为 `[]`）；
3. statement_records 中 `rule_id / family_id / school / canon / rule_type` 完成 mapping repair；
4. feedback 模板强制使用 `[S-xxxx]` 引用，且 `tools/feedback_ingest.py` 拒绝不含引用的反馈入库。

---

## 5. 附：与历史审计的关系

- `META/feedback-statement-reference-audit.md`、`META/feedback-statement-join-audit.md` 已记录过类似缺口；本次 P6-A1 在 V2 单报告与"最近 20 个已完成案例"语境下复核，结论与之一致，且新增了"用户报告层句柄可见性"维度（A/B 问）。
- 本审计不修改 `META/project-state.json`、不修改 `theory/` / `engine/` / `tests/`，与限制条款一致。
