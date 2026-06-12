# P4-4B Statement Traceability Design

生成时间：2026-06-12

审计性质：只读设计；除本报告外未修改 [theory/](../theory/)、[engine/](../engine/)、[tests/](../tests/) 或 [META/project-state.json](project-state.json)。

## 0. Executive Finding

P4-4B 的核心结论是：当前动态置信度不能学习，不是反馈数量不足，而是可学习反馈没有形成稳定的断语级因果链。

目标链路：

```text
feedback verdict
  -> statement_id
  -> rule_id
  -> family_id
  -> school
  -> canon
  -> rule_type
```

现状分为两个层面：

| 层面 | 结论 | 证据 |
|---|---|---|
| 全量索引层 | 4797 条 [statement_index.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json) 的目标字段覆盖为 0% | [mapping-recovery-audit](mapping-recovery-audit.md) 第 C 节 |
| 生成器层 | 新渲染器已能写入复数 [rule_ids](../tools/render_report.py) 与 [schools](../tools/render_report.py)，但不是 P4-4B 要求的标准单行学习契约 | [render_report](../tools/render_report.py) |
| 反馈预处理层 | 554 条 feedback rows 中 534 条为 `UNMAPPED`，100 个候选案均有 fallback 标记 | [phase-1000-feedback-preprocess-summary](phase-1000-feedback-preprocess-summary.md) |
| 策略映射层 | Phase-300 的正式学习维度在策略表中存在，但没有被 statement 级稳定承接 | [phase-300-voting-strategy](phase-300-voting-strategy.md) |

因此推荐方向不是继续扩大启发式匹配，而是建立标准 [statement_record](../tools/render_report.py) 契约，并让反馈摄入只消费可证明的映射链。

## 1. 当前断链位置

### 1.1 断链总览

| 链路步骤 | 当前状态 | 断链原因 | 学习风险 |
|---|---|---|---|
| feedback verdict -> statement_id | 部分成立 | Phase-1000 fallback 生成大量 `UNMAPPED-<case>-<line>` 临时断语号 | verdict 不能安全回贴到报告断语 |
| statement_id -> statement_index | 低覆盖 | 554 条反馈中仅 101 条找到 statement | 大量反馈只能进 repair queue |
| statement_index -> rule_id | 严重不足 | P4-4B 目标字段 [rule_id](../META/mapping-recovery-audit.md) 覆盖 0%；部分新索引用 [rule_ids](../tools/render_report.py) 但历史口径未统一 | 规则 posterior 无法更新 |
| rule_id -> family_id | 当前为 0 | 旧式 `M*` 规则不在 Phase-300 策略表；`UNMAPPED` 没有 family | 无法执行 family cap |
| family_id -> school/canon/rule_type | 当前为 0 | statement 层未挂 Phase-300 维度 | school lane 与 canon lane 不能学习 |

### 1.2 生成链路审计

| statement 来源 | 生成位置 | 模板/输出层 | 当前可恢复性 | 说明 |
|---|---|---|---|---|
| 生产规则结论 | [render_report](../tools/render_report.py) 的 `_build_statement_index` 汇总 `production_rule_conclusions` | `production_rules` | HIGH for new renders | evidence 中有规则引用时可直接恢复 [rule_ids](../tools/render_report.py) |
| 共识/互补结论 | [render_report](../tools/render_report.py) 的 `consensus_conclusions` / `complementary_conclusions` | `consensus` / `complementary` | HIGH for new renders | 规则证据来自 evidence；历史报告需重渲染或回填 |
| 应期铁断 | [render_report](../tools/render_report.py) 的 `iron_gates` | `yingqi` | MEDIUM | 可恢复 timing 类 rule，但 year 必须进入 hash 与记录 |
| 高派神煞/健康旁证 | [render_report](../tools/render_report.py) 的 `support_marriage_boosts` / `support_health` | `support_marriage` / `support_health` | MEDIUM | 多为派生规则号，如 `GP-*` / `GH-*`，需要纳入策略或标为 non-learning |
| 并行专家裁判 | [render_report](../tools/render_report.py) 的 `parallel_domain_conclusions` / `parallel_domain_readings` | `parallel_domain_*` | MEDIUM | 有 reading / adjudication 追踪，但需拆出可学习 rule |
| 已知事实迁移 | [promote_wenzhen_pending_analysis_samples](../tools/promote_wenzhen_pending_analysis_samples.py) 的 `_statement_index` | `known_facts_migrated` | LOW | `rule_ids` 固定为空，必须从报告段落或人工桥接恢复 |
| 历史手工标准索引 | 旧 case 目录的 [statement_index.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json) | `summary/status` | LOW | 只有 summary/domain/status，缺规则证据链 |

### 1.3 是否能从生成链路恢复 rule_id

| 类型 | 判断 | 依据 |
|---|---|---|
| 新渲染报告 | 可以，高置信 | [render_report](../tools/render_report.py) 已从 evidence 提取 [rule_ids](../tools/render_report.py) |
| 有旁路映射案 | 可以，高置信 | [feedback_ingest](../tools/feedback_ingest.py) 支持合并 [statement_rule_map.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_rule_map.json) |
| 旧 summary-only 索引 | 不可直接恢复，需模板/文本反匹配 | 旧索引只保留摘要，不保留 analyzer/template/evidence |
| known_facts_migrated | 不可自动恢复到规则，需报告反查或人工裁决 | 迁移工具显式写空 [rule_ids](../tools/promote_wenzhen_pending_analysis_samples.py) |
| Phase-1000 fallback 行 | 不可学习 | fallback statement_id 不是报告真实 statement_id |

## 2. 推荐契约

### 2.1 标准 statement_record

推荐把学习单元从宽松 statement list 升级为一条可审计的 [statement_record](../tools/render_report.py)：

```json
{
  "statement_id": "S-...",
  "case_id": "C-...",
  "statement_text": "可验证断语原文或规范化摘要",
  "domain": "事业/财富/婚姻/健康/应期/综合",
  "output_layer": "production_rules|consensus|complementary|yingqi|parallel_domain|known_facts_migrated",
  "source_analyzer": "production_rules|yingqi|parallel_domain|manual_bridge",
  "source_template": "content-report/v2",
  "rule_id": "DTS-PROD-... or ZP-PROD-...",
  "family_id": "FAM-... or FAM-UNMAPPED-...",
  "school": "ziping|tiaohou_ditiansui|duan|yang|ren|gao|manual_non_learning",
  "canon": "DITIANSUI|DITIANSUI_CHANWEI|QIONGTONG_BAOJIAN|SANMING_TONGHUI|ZIPING_ZHENQUAN|LEGACY_BLIND",
  "rule_type": "STRUCTURE|EVENT|TIMING|GENERAL_PRINCIPLE|ANTI_PATTERN|NON_LEARNING",
  "source_rule_title": "规则标题",
  "confidence_snapshot": {
    "star": 0,
    "percent": 0,
    "posterior_mean": null,
    "sample_n": 0
  },
  "generated_at": "2026-06-12T00:00:00Z",
  "trace_status": "learning_ready|review_required|non_learning|unrecoverable",
  "recovery_confidence": "HIGH|MEDIUM|LOW|UNRECOVERABLE"
}
```

### 2.2 多规则断语拆行规范

一条断语若由多个规则支撑，不应只在一个字段中保留数组。学习表应采用一条 statement 对多条 rule 的拆行结构：

| case_id | statement_id | rule_id | family_id | school | canon | rule_type | verdict | weight_policy |
|---|---|---|---|---|---|---|---|---|
| C-... | S-... | DTS-PROD-... | FAM-004 | tiaohou_ditiansui | DITIANSUI | TIMING | y/n/?/skip | family_cap_before_beta |

保留原始 [statement_index.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json) 作为报告索引，同时新增或派生 `statement_trace_map` 作为学习入口。这样兼容现有报告，不强迫展示层显示内部追踪字段。

### 2.3 字段来源矩阵

| 字段 | 首选来源 | 回退来源 | 不允许来源 |
|---|---|---|---|
| statement_id | 渲染器稳定 hash | 旧索引真实 ID | Phase fallback 临时 ID |
| rule_id | evidence ref / production rule trigger | 人工 [statement_rule_map.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_rule_map.json) | summary 文本臆测 |
| family_id | [phase-300-voting-strategy](phase-300-voting-strategy.md) | family repair queue | 空字符串进入学习 |
| school | [phase-300-voting-strategy](phase-300-voting-strategy.md) | theory rule `expert_system` 映射 | 从中文流派名自由推断 |
| canon | [phase-300-voting-strategy](phase-300-voting-strategy.md) | source/canon mapping audit | 只从报告章节名推断 |
| rule_type | [phase-300-voting-strategy](phase-300-voting-strategy.md) | rule-type audit | 未分类规则直接学习 |
| confidence_snapshot | 生成时的规则置信度对象 | ingest 时读取规则库快照 | 使用摄入后的更新值回填 |

## 3. 兼容性、迁移成本与历史恢复率

| 方案 | 兼容性 | 迁移成本 | 历史恢复率 | 推荐度 |
|---|---|---:|---:|---|
| A. 在现有 [statement_index.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json) 内直接追加字段 | 中 | 中 | 中 | 不推荐作为唯一方案，展示索引与学习索引耦合 |
| B. 保留 statement_index，新增 `statement_trace_map` 派生产物 | 高 | 中 | 高 | 推荐，兼容旧报告与新学习入口 |
| C. 仅依赖 [statement_rule_map.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_rule_map.json) 旁路 | 高 | 低 | 低到中 | 可作为过渡，不足以承接 family/canon/rule_type |
| D. 重跑所有报告以重建 statement_index | 中 | 高 | 中到高 | 适合新渲染链稳定后批量执行 |
| E. 文本反向匹配 summary 到规则模板 | 低 | 高 | 低到中 | 只作为 LOW/人工复核补救 |

推荐采用 B + C 的 staged 方案：短期生成 `statement_trace_map`，同时继续支持历史 [statement_rule_map.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_rule_map.json)；中期新渲染器直接产出 trace map；长期把 trace map 纳入 production artifact hard gate。

## 4. 历史案例恢复方案

### 4.1 恢复等级定义

| 等级 | 判定条件 | 是否进入 Beta 学习 | 处理动作 |
|---|---|---|---|
| HIGH CONFIDENCE | statement_id 命中真实索引，且 rule_id 来自 evidence 或人工旁路映射，且 rule_id 能进入 Phase-300 策略表 | 是 | 生成 statement_record 并拆 rule 行 |
| MEDIUM CONFIDENCE | statement_id 命中真实索引，rule_id 来自旧式 `M*` 或 `GP/GH/MR`，可映射到正式策略或明确 non-learning lane | 暂缓或低权重 | 进入 rule migration queue |
| LOW CONFIDENCE | 只有 statement_text/summary 与规则模板近似，缺触发证据 | 否 | 人工复核后升/降级 |
| UNRECOVERABLE | fallback statement_id、无真实索引命中、无报告段落、无可验证文本 | 否 | 保留反馈但标为 non-learning |

### 4.2 4797 statements 恢复分桶

| 桶 | 估计数量 | 比例 | 依据 |
|---|---:|---:|---|
| HIGH CONFIDENCE | 0 到 24 | 0.00% 到 0.50% | 7 个旁路 map 共约 24 个 statement 可补 rule，但还需 Phase-300 rule_id 对齐 |
| MEDIUM CONFIDENCE | 3707 | 77.28% | 当前扫描发现新索引含复数 `rule_ids` 的 statement，但尚未补 family/canon/rule_type |
| LOW CONFIDENCE | 1076 | 22.43% | 有 summary 但无规则字段，可能通过报告文本或模板弱匹配 |
| UNRECOVERABLE | 14 | 0.29% | 缺 summary 或只有非断语文本，需人工确认或放弃学习 |

注：上述 4797 分桶是全量索引恢复潜力，不等同于 Phase-1000 当前可学习反馈数。Phase-1000 当前反馈漏斗仍以 [mapping-recovery-audit](mapping-recovery-audit.md) 的 554 rows 为准。

### 4.3 554 feedback rows 恢复分桶

| 桶 | 估计数量 | 比例 | 依据 |
|---|---:|---:|---|
| HIGH CONFIDENCE | 0 | 0.00% | 当前 `family/canon found=0`，不能直接进入学习 |
| MEDIUM CONFIDENCE | 20 | 3.61% | 旧式 `M*` rule_id 存在，但不在 Phase-300 策略表 |
| LOW CONFIDENCE | 81 | 14.62% | statement found 但 rule bridge 不完整 |
| UNRECOVERABLE / repair required | 453 | 81.77% | statement_id 未命中或来自 fallback |

修复后上限：明确 y/n 样本最多 217 条可进入学习候选；含 pending 的治理/复核 lane 最多 511 条；仅当 pending 被人工裁决并补齐 rule/family/canon 后，554 条才可能全部进入治理闭环。

## 5. Rule Recovery Strategy

### 5.1 可用反向匹配信号

| 信号 | 可信度 | 说明 |
|---|---|---|
| statement_id hash 输入中的 rule_ids | HIGH | 新渲染链中 statement_id 由 case_id + rule_ids 计算，若有原始 ctx 可重建 |
| evidence_str / report visible rule ids | HIGH | 报告中若展示规则 ID，可直接抽取 |
| [statement_rule_map.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_rule_map.json) | HIGH | 人工旁路映射，适合旧案补桥 |
| summary 与 rule title/模板相似 | LOW | 只能生成候选，不可直接学习 |
| domain/year 与 TIMING 规则模板一致 | MEDIUM | 对应期类有帮助，但需 year 与触发层证据 |
| source_raw_id / known facts | LOW | 事实不是规则断语，需先匹配报告判断 |

### 5.2 反向恢复流程

1. 先修复 Phase-1000 preprocess 执行入口，清除 `ModuleNotFoundError('No module named tools')` fallback。
2. 对每条 feedback row，优先用真实 `case_id + statement_id` 命中 case 目录 [statement_index.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json)。
3. 若命中 statement 且存在 `rule_ids`，展开为多条 statement_record。
4. 若缺 `rule_ids`，读取同目录 [statement_rule_map.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_rule_map.json) 作为高置信旁路。
5. 若仍缺规则，从报告正文抽取可见 rule id；没有 rule id 只生成候选，不进入学习。
6. 将 legacy rule id 映射到 Phase-300 正式 rule id；无法映射者进入 `non_learning_legacy_rule`。
7. 用 [phase-300-voting-strategy](phase-300-voting-strategy.md) 补齐 family_id、school、canon、rule_type。
8. 只允许 trace_status 为 `learning_ready` 且 verdict 为 y/n 的行进入 Beta。

### 5.3 预计可恢复 rule 与 feedback 数

| 阶段 | 可恢复 rule 数 | 可恢复 feedback 数 | 说明 |
|---|---:|---:|---|
| 当前不改代码，仅承认完整链 | 0 | 0 | family/canon/rule_type 仍为 0 |
| 修复 preprocess fallback + 使用真实 statement_id | 待重跑统计 | 最多 101 命中 statement 的反馈 | 先解除 fallback 造成的假 statement_id |
| 加入 statement_rule_map / report rule id 抽取 | 约 24 到 101 条 statement 候选 | 最多 217 条 y/n 候选的一部分 | 取决于报告是否有可见规则证据 |
| 新渲染索引 rule_ids 批量对齐策略表 | 最多 3707 条 statement 候选 | 最多 217 条 y/n 学习候选；511 条 review lane | 需补 family/canon/rule_type |
| 完整人工复核 pending | 不新增规则数，只增加裁决数 | 最多 554 条治理样本 | pending 不自动进 Beta |

## 6. 未来生成规范

### 6.1 生成端规范

| 要求 | 说明 |
|---|---|
| 每条可反馈断语必须有稳定 statement_id | statement_id 不得由行号或 fallback 文本生成 |
| 每条可学习断语必须保存 rule trigger | rule_id 必须来自 analyzer evidence，不得只来自报告摘要 |
| 多规则断语必须拆行学习 | 避免一条反馈重复放大多个 family |
| confidence_snapshot 必须在生成时冻结 | 防止摄入后 posterior 改变历史证据 |
| output_layer 必须显式 | 区分 production_rules、yingqi、parallel_domain、known_facts_migrated |
| non-learning 也要显式标记 | 事实迁移、展示说明、纯旁证不能静默混入学习 |

### 6.2 摄入端规范

| Gate | 规则 |
|---|---|
| statement gate | verdict 的 statement_id 必须命中真实索引或 trace map |
| rule gate | y/n 学习样本必须有 rule_id |
| strategy gate | rule_id 必须能映射到 family_id、school、canon、rule_type |
| verdict gate | 只有 y/n 进入 Beta；pending、skip、partial 进入 review lane |
| family gate | 同 case × family 先 cap，再更新 posterior |
| audit gate | 每次 ingest 输出 repair_reason 分布，不能只输出成功行数 |

## 7. 解除 Phase-1000 阻塞的最小改造

最小改造目标不是“让 554 行全部学习”，而是让所有可学习样本都具备可审计链路。

| 优先级 | 改造 | 解除阻塞贡献 |
|---:|---|---|
| P0 | 修复 Phase-1000 preprocess import / invocation，消除 fallback statement_id | 让 statement found 指标真实可信 |
| P0 | 生成 `statement_trace_map`，字段至少覆盖 statement_id、rule_id、family_id、school、canon、rule_type、generated_at | 建立动态置信度输入契约 |
| P0 | 用 [phase-300-voting-strategy](phase-300-voting-strategy.md) 建立 rule_id -> family/school/canon/type 查表 | 恢复 family cap 与 school lane |
| P1 | 将 legacy `M*` / `GP*` / `GH*` / `MR*` 分流为正式迁移或 non-learning | 防止旧规则污染 Phase-300 |
| P1 | 对已有 [statement_rule_map.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_rule_map.json) 升级到完整 trace map | 快速恢复小批高置信样本 |
| P1 | 重跑 Phase-1000 preprocess，输出 learnable / repair / non-learning 三类队列 | 用漏斗指标验收，而非文件存在验收 |

最低解除条件：

| 指标 | 阈值 |
|---|---:|
| fallback_reason | 0 |
| 非 pending 样本 statement found | >= 90% |
| 非 pending 样本 rule found | >= 80% |
| 非 pending 样本 family/school/canon/rule_type found | >= 80% |
| learnable=true 的 y/n 样本 | >= 80% |
| `UNMAPPED` 进入 Beta | 0 |

## 8. Final Decision

P4-4B 建议：不解除 Phase-1000 阻塞；先落地 statement traceability 契约与恢复队列。

当前最小可行动路径是：保留现有 [statement_index.json](../cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json) 作为报告索引，新增 `statement_trace_map` 作为学习索引；所有动态置信度更新必须从 `feedback verdict -> statement_id -> rule_id -> family_id -> school -> canon -> rule_type` 的完整链通过后才允许进入 Beta。
