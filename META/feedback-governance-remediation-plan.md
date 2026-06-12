# P4-2 Feedback Governance Remediation Plan

> 只读分析范围：当前 100 个 Phase-300 案例、`cases/*/feedback.md`、`cases/*/statement_index.json`、`META/feedback-quality-audit.md`、`META/phase-300-calibration-summary.md`、`META/phase-300-calibration.md`。
>
> 本计划不修改 `theory/*`、`engine/*`、`tests/*`、`META/project-state.json`；后续修复应按本文件拆分投放。

## 1. 执行摘要

当前反馈治理尚不能进入稳定规则学习 / Beta posterior 更新。主要原因不是命理规则本身，而是反馈入口、断语索引、反馈格式与映射链路尚未形成可审计闭环。

核心判断：

- `fallback_yaml_trigger` 为 100/100，且已观察原因全部为 `ModuleNotFoundError("No module named 'tools'")`；这是运行环境 / 调用方式阻塞，不应被解释为理论规则失败。
- 100 案例中只有 27 案例有任一反馈信号，73 案例为零反馈；样本代表性不足。
- `partial + unknown = 175/624 = 28.0%`，且语义未完全结构化；直接纳入规则降权会污染基础规则。
- `rule_id -> statement_id -> feedback verdict` 尚未稳定：历史占位、字段名不统一、RF 迁移空 `rule_ids`、部分报告反馈未绑定规则。
- feedback 格式混用 emoji、旧表格、`[y]/[n]/[?]/[skip]`、空 `[ ]`、`pending`，需要统一为 v1.3 标准表。

结论：P4-2 的修复应先治理入口与数据结构，再放开规则学习。优先级顺序为：

1. 修复 Phase-300 fallback 调用环境。
2. 冻结学习口径，禁止把未结构化 `unknown/partial` 直接用于规则更新。
3. 建立反馈 v1.3 标准格式。
4. 回填 `statement_index` 并稳定映射链。
5. 扩充有效反馈覆盖，使 School / Family / Rule Type 达到最低学习门槛。

## 2. fallback_yaml_trigger 原因统计

### 2.1 统计结果

| trigger_mode | case_count | reason_class | observed_reason | count | action |
|---|---:|---|---|---:|---|
| `fallback_yaml_trigger` | 100 | `ModuleNotFoundError` | `ModuleNotFoundError("No module named 'tools'")` | 100 | 修复调用路径 / 模块加载环境 |
| `fallback_yaml_trigger` | 100 | other | 未观察到其他错误原因 | 0 | 暂无 |

### 2.2 判断

这不是规则质量信号，而是 Phase-300 批处理执行环境问题。若在此状态下把 Phase-300 结果当成生产规则表现，会产生两类误判：

- 把 fallback 旁路结果误认为完整 pipeline 结果。
- 把规则覆盖、命中、反馈表现与 Python 模块导入失败混淆。

### 2.3 修复投放规范

- 新增一个独立修复任务：`P4-2-B01-fallback-import-path`。
- 修复目标不是改规则，而是修正运行入口：确保从仓库根目录执行时 `tools` 可 import。
- 修复完成验收：Phase-300 重跑后 `fallback_yaml_trigger = 0`，或至少 fallback 原因不再为 `ModuleNotFoundError("No module named 'tools'")`。
- 修复前禁止使用 Phase-300 fallback 结果做规则 posterior 更新。

## 3. 有效反馈 27 案例分布与覆盖不足

### 3.1 总体反馈信号

| metric | value |
|---|---:|
| total_cases | 100 |
| cases_with_any_feedback_signal | 27 |
| zero_feedback_cases | 73 |
| hit | 340 |
| miss | 109 |
| partial | 94 |
| unknown | 81 |
| total_feedback_signals | 624 |

有效反馈案例不足的主要风险：

- 27% 的案例覆盖不足以支撑分派别、分 Family、分 Rule Type 的稳定学习。
- 73 个零反馈案例只能用于覆盖 / 触发观察，不能用于规则质量判断。
- 当前 `partial` 与 `unknown` 比例过高，进一步降低有效样本量。

### 3.2 有反馈案例清单

| # | case_id | feedback_signal |
|---:|---|---|
| 1 | `C-2026-001-乾-庚申戊寅壬子辛丑` | 有 |
| 2 | `C-2026-002-坤-戊辰丁巳戊辰壬子` | 有 |
| 3 | `C-2026-007-乾-己巳丙子乙卯甲申` | 有 |
| 4 | `C-2026-008-坤-丙寅乙未戊子壬子` | 有 |
| 5 | `C-2026-009-坤-己巳丙子乙卯甲申` | 有 |
| 6 | `C-2026-010-乾-丙戌丁酉甲午丙寅` | 有 |
| 7 | `C-2026-011-乾-戊申丁巳庚寅己卯` | 有 |
| 8 | `C-2026-012-坤-壬戌癸丑丙申壬辰` | 有 |
| 9 | `C-2026-013-乾-乙亥己卯甲辰戊辰` | 有 |
| 10 | `C-2026-014-乾-丙戌庚子乙亥辛巳` | 有 |
| 11 | `C-2026-015-乾-甲寅乙亥丙辰辛卯` | 有 |
| 12 | `C-2026-016-坤-甲子丙子丙戌戊子` | 有 |
| 13 | `C-2026-017-乾-壬戌乙巳庚戌丁亥` | 有 |
| 14 | `C-2026-018-乾-壬申戊申庚辰丁亥` | 有 |
| 15 | `C-2026-019-坤-甲戌丁卯乙卯丁亥` | 有 |
| 16 | `C-2026-021-乾-己巳戊辰甲子癸酉` | 有 |
| 17 | `C-2026-022-坤-丙子戊戌戊戌戊午` | 有 |
| 18 | `C-2026-024-乾-癸亥戊午己巳乙亥` | 有 |
| 19 | `C-2026-025-坤-甲戌癸酉戊寅乙卯` | 有 |
| 20 | `C-2026-028-乾-辛亥甲午辛卯壬辰` | 有 |
| 21 | `C-2026-031-乾-辛卯辛卯庚申乙酉` | 有 |
| 22 | `C-2026-032-乾-癸酉乙卯戊戌甲寅` | 有 |
| 23 | `C-2026-033-坤-戊午己未乙酉丁亥` | 有 |
| 24 | `C-2026-RF000026-乾-庚午戊寅壬寅丙午` | 有 |
| 25 | `C-2026-RF000417-乾-丙寅丙申辛卯丁酉` | 有 |
| 26 | `C-2026-RF000572-乾-辛未丙申庚戌戊子` | 有 |
| 27 | `C-2026-RF000592-乾-丁卯壬寅壬寅戊申` | 有 |

### 3.3 School 覆盖不足

| school | raw_votes | share | risk | remediation |
|---|---:|---:|---|---|
| `tiaohou_ditiansui` | 19662 | 80.9% | 原始票数过度集中，容易主导反馈学习 | 后续学习需设 school lane 或 raw vote cap |
| `ziping` | 4648 | 19.1% | 样本权重不足，若直接按 raw vote 学习会被稀释 | 单独补齐子平有效反馈样本 |

判断：School 层面不是“没有覆盖”，而是 raw vote 和反馈校准权重失衡。修复时应先分派别汇总 posterior，再做跨派融合，避免 `tiaohou_ditiansui` 因触发量大而吞噬 `ziping`。

### 3.4 Rule Type 覆盖不足

| rule_type | raw_votes | share | risk | remediation |
|---|---:|---:|---|---|
| `STRUCTURE` | 11321 | 46.6% | 结构类规则最多，若反馈不足会放大结构偏见 | 需要按格局 / 结构断语单独抽样反馈 |
| `EVENT` | 5473 | 22.5% | 事件类可验证性强，但需与断语绑定 | 优先纳入稳定映射 |
| `GENERAL_PRINCIPLE` | 4663 | 19.2% | 原则类容易泛化，不能用模糊反馈直接学习 | 只接受明确 `y/n` 或强约束 `partial` |
| `TIMING` | 1605 | 6.6% | 应期判断对 partial 敏感，当前时间错占比高 | 建立 `partial_reason=时间错` 专门通道 |
| `ANTI_PATTERN` | 1248 | 5.1% | 负向/反例规则样本少 | 后续回填 miss/skip 样本 |

### 3.5 Family 覆盖不足

当前审计已指出高重复 Family：`FAM-011`、`FAM-018`、`FAM-010`、`FAM-004`。另有 `FAM-UNMAPPED-*` 一类无法稳定归属的触发项。

治理原则：

- 对高重复 Family 建立 family cap，避免单一语义族重复投票。
- 对 `FAM-UNMAPPED-*` 暂不进入规则学习，只进入映射修复队列。
- 每个 Family 至少需要可追溯的 `statement_id` 与反馈 verdict，才能参与 posterior。

## 4. unknown 与 partial 结构化分类

### 4.1 unknown 分类

| target_category | audit_source | count | learning_policy |
|---|---|---:|---|
| 未反馈 | A. 用户未反馈 | 37 | 不作为规则失败；只计入反馈缺口 |
| 空字段 | D. 规则触发但无反馈字段 | 30 | 不作为规则失败；优先修复反馈表字段 |
| 无法映射 | 当前审计未观察到独立计数 | 0 | 若出现，进入 statement/rule mapping 修复队列 |
| 其他 | F. 其他 | 14 | 人工复核后再归类；默认不学习 |
| 合计 | - | 81 | 不直接降权 |

关键规范：`unknown` 默认不是 `miss`，不能直接转为负反馈。只有当人工复核证明“断语已呈现、用户明确否定、但系统未映射”时，才允许转入 `miss` 或 mapping 修复。

### 4.2 partial 分类

| target_category | audit_source | count | learning_policy |
|---|---|---:|---|
| 部分命中 | 当前审计未观察到独立计数 | 0 | 需要新增字段承接 |
| 时间错 | B. 时间错误 | 91 | 对 TIMING / 应期子规则降权或调参，不否定事件规则本身 |
| 强度错 | C. 强度错误 | 3 | 对强弱 / 置信度校准，不否定方向性判断 |
| 多断语 | 当前审计未观察到独立计数 | 0 | 需要拆分 compound statement |
| 领域错 | 当前审计未观察到独立计数 | 0 | 需要新增字段承接 |
| 合计 | - | 94 | 拆分后分通道学习 |

关键规范：`partial` 不能统一当作 0.5。必须拆分原因：

- `时间错`：事件方向可保留，应期规则单独校准。
- `强度错`：方向可保留，置信度 / 等级校准。
- `多断语`：必须拆句，不允许一个 verdict 同时覆盖多个判断。
- `领域错`：领域映射错误，应进入 domain mapping 修复。

## 5. rule_id -> statement_id -> feedback verdict 映射稳定化校验

### 5.1 当前可行性分层

| tier | case_pattern | current_state | can_learn_now | required_fix |
|---|---|---|---|---|
| T0 | 历史 placeholder `statement_index.json` | `statements: []` | 否 | 从报告与 feedback 回填 statement_index |
| T1 | 有 `statement_id` + verdict + `rule_ids` | 字段基本完整 | 有条件 | 统一 verdict 与字段名后可学习 |
| T2 | 有 `statement_id` + verdict，但 rule 映射在 `evidence` 或其他字段 | 字段名不统一 | 否 | 迁移到统一 `rule_ids` |
| T3 | 有 `statement_id` + `rule_ids`，但无明确 verdict | 只能做归因，不能学习 | 否 | 从 feedback.md 绑定 verdict |
| T4 | RF known facts，`rule_ids: []` | 已迁移事实但未归规则 | 否 | 建立 source_raw_id -> rule_id 映射 |
| T5 | `[skip]` / 风险提示 / 非断语项 | 不应更新规则 | 否 | 保留为不可学习样本 |

### 5.2 一一对应目标表结构

后续所有可学习反馈必须形成以下规范表：

| field | required | description |
|---|---|---|
| `case_id` | 是 | 案例 ID |
| `statement_id` | 是 | 报告中单条可验证断语 ID |
| `rule_id` | 是 | 触发该断语的规则 ID；多规则则拆多行 |
| `feedback_verdict` | 是 | 仅允许 `y / n / skip / pending` |
| `partial_reason` | 条件必填 | 当 verdict 由 partial 转换或保留时填写 |
| `unknown_reason` | 条件必填 | 当 verdict 为 pending 或无法判断时填写 |
| `learnable` | 是 | `true/false` |
| `learning_lane` | 是 | `event / timing / strength / domain / non_learning` |

### 5.3 示例映射表

| case_id | statement_id | rule_id | feedback_verdict | learnable | note |
|---|---|---|---|---|---|
| historical-placeholder cases | 无 | 无 | 无 | false | `statement_index.json` 为空，需回填 |
| v1.3-ready cases | 已有 | 已有 | `y/n/skip/?` | conditional | `?` 需改为 `pending`，`skip` 不学习 |
| feedback_state cases | 已有 | 可能在 `evidence` | `hit/strong_hit/pending/partial_hit_adjusted` | conditional | 需归一化为 `y/n/skip/pending` + reason |
| RF migrated known facts | 已有 | 空 | 多为待反馈 / skip | false | 需建立 `source_raw_id -> rule_id` |

### 5.4 稳定化投放规范

- 第一阶段只做字段统一，不做理论规则更新。
- 每个 `statement_id` 只能表达一个可验证判断；复合断语必须拆分。
- 多个 `rule_id` 共同支持一个断语时，落表为多行，但需记录同一 `statement_id`，避免重复计算。
- `skip` 永不进入命中率计算。
- `pending` 只计入反馈缺口，不作为 `unknown` 负样本。
- `partial` 不作为最终 verdict；必须通过 `partial_reason` 转换到具体 learning lane。

## 6. feedback v1.3 格式标准化方案

### 6.1 统一标记

只允许以下四种顶层标记：

| marker | meaning | learning |
|---|---|---|
| `y` | 用户明确确认命中 | 可学习正样本 |
| `n` | 用户明确否定 | 可学习负样本 |
| `skip` | 不适合验证 / 风险提示 / 非断语 / 无关项 | 不学习 |
| `pending` | 未反馈 / 待确认 / 暂无信息 | 不学习，只计反馈缺口 |

禁用：

- `✅ / ❌ / 🟡 / ❓ / ⚠️ / ⏳`
- `[y] / [n] / [?] / [skip]` 作为长期存储格式
- 空 `[ ]`
- `命中 / 未命中 / 部分命中 / 待反馈` 作为唯一机器可读字段
- 同一文件内混用旧表格与新表格

### 6.2 v1.3 标准表

每个 `feedback.md` 至少包含如下机器可读表：

| statement_id | verdict | partial_reason | unknown_reason | evidence_note | reviewer |
|---|---|---|---|---|---|
| `CXXXX-S001` | `y` |  |  | 用户确认具体事实 | manual |
| `CXXXX-S002` | `n` |  |  | 用户否认 | manual |
| `CXXXX-S003` | `pending` |  | `未反馈` | 暂无反馈 | manual |
| `CXXXX-S004` | `skip` |  |  | 风险提示，不参与学习 | system |

约束：

- `verdict` 必填，且只能是 `y/n/skip/pending`。
- `partial_reason` 只允许：`部分命中 / 时间错 / 强度错 / 多断语 / 领域错`。
- `unknown_reason` 只允许：`未反馈 / 空字段 / 无法映射 / 其他`。
- 若 `verdict=y/n`，`statement_id` 必须能在 `statement_index.json` 找到。
- 若 `statement_id` 找不到，verdict 不得进入学习，只能进入 mapping repair queue。

### 6.3 旧格式迁移规则

| old_format | new_verdict | reason_field | note |
|---|---|---|---|
| `✅` / `命中` / `[y]` | `y` | 空 | 需保留原始备注 |
| `❌` / `未命中` / `[n]` | `n` | 空 | 需绑定单条 statement |
| `🟡` / `部分命中` | `pending` 或拆分后 `y/n` | `partial_reason` 必填 | 不允许保留为顶层 verdict |
| `❓` / `[?]` / 空 `[ ]` / `待反馈` | `pending` | `unknown_reason` 必填 | 不学习 |
| `⚠️` / 风险提示 | `skip` | 空 | 不学习 |

## 7. TOP10 阻塞项修复优先级清单

| blocker | repair_target | expected_deliverable | dependency | priority |
|---:|---|---|---|---|
| 1 | 修复 100/100 `fallback_yaml_trigger`，消除 `ModuleNotFoundError("No module named 'tools'")` | `P4-2-B01-fallback-import-path` 修复记录；重跑 Phase-300 后 fallback 归零或原因消失 | 无，最高优先 | HIGH |
| 2 | 将有效反馈案例从 27/100 提升到最低学习门槛 | `P4-2-B02-effective-feedback-backfill-list.md`；零反馈 73 案例补录队列 | B06 feedback 格式标准 | HIGH |
| 3 | 把 `unknown=81`、`partial=94` 拆成可学习 / 不可学习子类 | `P4-2-B03-signal-taxonomy.md`；结构化 reason 字段 | B06 feedback 格式标准 | HIGH |
| 4 | 统一 feedback 格式，禁止 emoji / 旧表 / 空 `[ ]` 混用 | `P4-2-B04-feedback-v1.3-template.md`；批量迁移规则 | 无 | HIGH |
| 5 | 稳定 `rule_id -> statement_id -> feedback verdict` 映射链 | `P4-2-B05-statement-rule-feedback-map.csv`；mapping readiness report | B04 + statement_index 回填 | HIGH |
| 6 | 拆分 `partial` 语义，不再把 partial 当作单一 0.5 权重 | `P4-2-B06-partial-reason-migration.md`；`partial_reason` 字段落地 | B03 | HIGH |
| 7 | 防止 `unknown` 被误当规则失败 | `P4-2-B07-unknown-learning-policy.md`；学习入口过滤规则 | B03 | HIGH |
| 8 | 治理 `tiaohou_ditiansui` raw vote dominance | `P4-2-B08-school-lane-cap.md`；school lane 汇总规则 | B01 + B05 | MEDIUM |
| 9 | 治理高重复 Family 与 `FAM-UNMAPPED-*` | `P4-2-B09-family-cap-and-unmapped-queue.md` | B05 | MEDIUM |
| 10 | 修复 report archive / feedback entry / `statement_index` 缺失或滞后 | `P4-2-B10-case-artifact-completeness-audit.md`；缺失清单 | B04 | MEDIUM |

## 8. 推荐投放顺序

### Wave 1：阻断污染

1. B01 fallback import path。
2. B04 feedback v1.3 template。
3. B07 unknown learning policy。

验收标准：不再把环境错误、未反馈、空字段输入规则学习。

### Wave 2：建立闭环

1. B05 statement-rule-feedback map。
2. B03 signal taxonomy。
3. B06 partial reason migration。
4. B10 artifact completeness audit。

验收标准：每条可学习反馈都能落到 `case_id + statement_id + rule_id + verdict + learnable`。

### Wave 3：扩大样本与校准公平性

1. B02 effective feedback backfill。
2. B08 school lane cap。
3. B09 family cap and unmapped queue。

验收标准：有效反馈样本覆盖 School / Rule Type / Family 的最低门槛，且不会被单一派别或高重复 Family 主导。

## 9. 学习解冻门槛

满足以下全部条件前，不建议开启规则 posterior 自动更新：

| gate | required_state |
|---|---|
| fallback gate | `fallback_yaml_trigger` 不再由 `ModuleNotFoundError("No module named 'tools'")` 触发 |
| feedback gate | 有效反馈案例数至少达到 50/100，且每个重点 Rule Type 有 `y/n` 样本 |
| format gate | 所有新反馈统一使用 v1.3 表；旧 emoji / 空 `[ ]` 不再进入 ingest |
| mapping gate | 可学习反馈 100% 具备 `statement_id -> rule_id -> verdict` |
| unknown gate | `unknown` 必须有 reason，不参与负样本学习 |
| partial gate | `partial` 必须拆入 reason lane，不作为顶层 verdict |
| school gate | school lane 先内部分派别校准，再跨派融合 |
| family gate | 高重复 Family 有 cap；`FAM-UNMAPPED-*` 不学习 |

## 10. 结论

P4-2 的正确修复方向是“反馈治理先于规则学习”。当前最危险的动作是把 fallback 运行结果、未反馈字段、空字段、partial 混合信号直接纳入规则降权。应按 HIGH 优先级先修复 B01/B03/B04/B05/B06/B07，再做样本扩充与派别 / Family 公平性治理。