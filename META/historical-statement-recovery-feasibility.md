# P4-4C Historical Statement Recovery Feasibility Audit

生成时间：2026-06-12

## 1. 审计结论

**推荐：OPTION-C 为主，OPTION-B 仅作一次性高置信度迁移辅助；不推荐 OPTION-A。**

历史 `statement_index.json` 中确实存在大量由当前规则模板生成的语句，说明“语句文本 → 规则模板”在存量案例层面有较强可追溯性。但这不等于能直接恢复动态学习样本：当前 217 条非 pending 反馈中，按现有 `rule_statement_verdict_map.csv` 逐行核对，能自动恢复到 Phase-300 `*-PROD-*` 规则元数据的反馈行为 0。

因此，历史 statements 值得作为审计证据与人工回填候选池保留，不值得全量自动恢复为学习样本。后续生产应从新的 `statement_record` 契约开始，历史数据只迁移 exact match 且可人工验收的高置信度子集。

## 2. 输入与范围

本次审计只读扫描以下事实源：

- `cases/**/statement_index.json`
- `theory/**/*.yaml` 中的 `output.statement`
- `META/phase-300-voting-strategy.md`
- `META/mapping-recovery-audit.md`
- `META/statement-traceability-design.md`
- `META/phase-1000-feedback-preprocess/rule_statement_verdict_map.csv`

未修改以下路径：

- `theory/*`
- `engine/*`
- `tests/*`
- `META/project-state.json`

## 3. A. Statement 与模板统计

| 指标 | 数量 | 说明 |
|---|---:|---|
| 历史 statement 总数 | 4,797 | 来自全部 `cases/**/statement_index.json` |
| 唯一 statement_id 数 | 1,644 | 历史 ID 存在跨案例复用 |
| 唯一 statement text 数 | 1,592 | 大量文本重复，符合模板生成特征 |
| 规则 output template 数 | 624 | 来自 `theory/**/*.yaml` 的 `output.statement` |
| 唯一 output text 数 | 624 | 当前规则模板文本无重复 |
| 带直接 rule_ids 的 statement 数 | 3,707 | 历史索引已有直接规则引用 |
| 直接 rule_id 引用条目数 | 15,884 | 多规则挂载很常见 |
| 直接唯一 rule_id 数 | 416 | 包含 Phase-300 与旧式规则 ID |

判断：历史 statement 很大比例来源于规则模板，尤其是 3,282 条 exact match。问题不在“是否像模板”，而在“能否稳定恢复到当前学习契约所需的 rule_id / family_id / school / canon / rule_type”。

## 4. B. Text ↔ Template 四级匹配

匹配对象：

- 左侧：历史 statement text。
- 右侧：规则模板 `output.statement`。

匹配级别：

| 级别 | 本次实现口径 | 结果 | 可学习性判断 |
|---|---|---:|---|
| exact | 文本完全一致 | 3,282 | 可作为高置信候选 |
| normalized exact | 去空白并统一常见中英文标点 | 0 额外新增 | 无额外收益 |
| fuzzy | `SequenceMatcher >= 0.92`，且排除 exact/normalized | 0 额外新增 | 本轮无收益 |
| semantic | 不做自动语义归并 | 0 自动新增 | 只允许人工 review，不得自动学习 |

说明：semantic match 在命理语句中风险较高。相似文本可能共享句式但裁决条件不同，若自动归并，会把条件、触发域、应期或派别证据错误挂到同一规则上。

## 5. C. Recovery Funnel

| 漏斗阶段 | statement 数 | 相对总量 | 备注 |
|---|---:|---:|---|
| 全部 historical statements | 4,797 | 100.0% | 扫描基数 |
| exact match | 3,282 | 68.4% | 可回到当前 `output.statement` 模板 |
| normalized exact extra | 0 | 0.0% | 规范化无新增 |
| fuzzy extra | 0 | 0.0% | 阈值 0.92 无新增 |
| semantic auto extra | 0 | 0.0% | 不建议自动归并 |
| unrecoverable / non-template | 1,515 | 31.6% | 包括人工事实、旧报告摘要、旧派别规则与不可判定语句 |

文本层面结论：68.4% 的历史 statements 可以 exact 对齐模板。

学习层面结论：exact 对齐模板不能自动解决反馈映射，因为反馈表里的 217 条非 pending 行大多是 `UNMAPPED` 或旧式规则 ID，不直接指向这些 exact-matched statement。

## 6. D. 可恢复元数据统计

Phase-300 策略表中正式 `*-PROD-*` 规则行：312。

| 来源口径 | 可恢复 rule_id | 可恢复 family_id | 可恢复 school | 可恢复 canon | 可恢复 rule_type |
|---|---:|---:|---:|---:|---:|
| 直接 rule_ids | 312 | 20 | 2 | 5 | 5 |
| exact template match | 312 | 20 | 2 | 5 | 5 |
| normalized extra | 0 | 0 | 0 | 0 | 0 |
| fuzzy extra | 0 | 0 | 0 | 0 | 0 |
| 任一来源合并 | 312 | 20 | 2 | 5 | 5 |

补充观察：

- 416 个直接唯一 rule_id 中，312 个能对齐 Phase-300 策略表。
- 无法对齐的直接 rule_id 主要是旧式或旁证型 ID，例如 `M*`、`GP-*`、`GH-*`、`MR-*`、`G-SHENSHA-*` 等。
- 可恢复 school 只有 2 个，说明历史模板恢复覆盖不到完整五派/多派策略空间。
- 可恢复 canon 为 5 个，低于策略表总 canon 覆盖，说明历史 exact 模板集中在部分经典来源。

## 7. E. 217 个可学习样本增量估算

基线来自 `META/phase-1000-feedback-preprocess/rule_statement_verdict_map.csv`：

| 指标 | 数量 |
|---|---:|
| feedback rows 总数 | 554 |
| 非 pending 的 y/n 行 | 217 |
| 当前 learnable=true | 12 |
| y | 183 |
| n | 34 |
| pending | 294 |
| skip | 43 |
| 非 pending 且 rule_id 为 Phase-300 `*-PROD-*` | 0 |
| 非 pending 且 statement_id 可由历史索引恢复到 Phase-300 | 0 |

三种情景估算：

| 情景 | 可学习样本估算 | 增量 | 条件 |
|---|---:|---:|---|
| Worst case | 12 | +0 | 只承认当前 `learnable=true`，不做历史修复 |
| Expected case | 12 | +0 | 本轮自动 exact/normalized/fuzzy 均无法把 217 行反馈恢复为 Phase-300 学习样本 |
| Best case | 217 | +205 | 需要人工逐条重标 205 条非 learnable y/n 反馈，补齐 `statement_id -> rule_id -> family/school/canon/rule_type`，不是自动恢复结果 |

重要判定：如果要求“自动恢复后增加到多少”，答案是仍为 12；如果允许“人工重标并回填契约”，理论上最多到 217。

## 8. F. 方案裁决

| 方案 | 判断 | 原因 |
|---|---|---|
| OPTION-A：恢复历史 statements | 不推荐 | 4,797 条中 3,282 条可 exact 对齐模板，但反馈行级可学习增量为 0；全量恢复会制造虚假确定性 |
| OPTION-B：仅恢复部分高置信度 statements | 有条件采用 | 仅适合迁移 exact match 且能人工核验反馈指向的子集，不应自动进入学习 |
| OPTION-C：放弃历史自动恢复，从新 `statement_record` 契约开始 | 推荐 | 最小风险，直接解决未来反馈链路，不继续用文本匹配弥补契约缺失 |

最终推荐：

1. 生产链路立即切换到新 `statement_record` 契约。
2. 历史 statements 不做全量恢复。
3. 建立一次性 `historical_statement_trace_map` 候选表时，只纳入 exact match 的 3,282 条，并标记为 `candidate_only`。
4. 对 217 条非 pending 反馈，若业务上必须扩大样本，只做人工重标，不做 semantic 自动归并。
5. Phase-1000 学习入口只接受完整字段链：`feedback verdict -> statement_id -> rule_id -> family_id -> school -> canon -> rule_type`。

## 9. 审计后续动作

建议后续拆成两个独立任务：

1. 新增生产期 `statement_record` 落库/导出契约，确保新报告天然携带 rule trace。
2. 若仍要利用历史反馈，单独建立人工 review pack，只处理 217 条 y/n 反馈，不处理全部 4,797 条 statements。
