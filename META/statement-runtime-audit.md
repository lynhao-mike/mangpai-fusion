# P5-2 Statement Record Runtime Audit

> 审计时间：2026-06-12T13:59:54Z  
> 审计性质：只读审计；未修改 [engine/](engine/)、[theory/](theory/)、[tests/](tests/) 或 [META/project-state.json](META/project-state.json)。  
> 契约基准：[META/statement-record-contract-v1.md](META/statement-record-contract-v1.md:13)。

## 1. Runtime Status

**PARTIAL**

当前生产链路已经具备稳定 [statement_id](META/statement-record-contract-v1.md:152) 与 [statement_index.json](cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json) 输出，并且反馈摄入可按 [statement_id](META/statement-record-contract-v1.md:152) 读取索引后 fanout 到规则。但标准 [statement_record](META/statement-record-contract-v1.md:13) 本体尚未作为生产运行产物生成，也没有在报告生成、反馈摄入、动态置信度更新中作为唯一学习事实源被消费。

结论分层：

| 层级 | 状态 | 说明 |
|---|---|---|
| [statement_id](META/statement-record-contract-v1.md:152) 生成 | PARTIAL | [tools/render_report.py](tools/render_report.py:1257) 会从渲染上下文生成 [statement_index.json](cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json)，部分条目带 [rule_ids](tools/render_report.py:1298)。 |
| [statement_record](META/statement-record-contract-v1.md:13) 生成 | NOT_IMPLEMENTED | 未发现标准对象、存储文件或写入模块；现有索引缺 [family_id](META/statement-record-contract-v1.md:155)、[canon](META/statement-record-contract-v1.md:157)、[rule_type](META/statement-record-contract-v1.md:158)、[confidence_snapshot](META/statement-record-contract-v1.md:160)、[generated_at](META/statement-record-contract-v1.md:161)。 |
| 反馈引用 [statement_id](META/statement-record-contract-v1.md:152) | PARTIAL | [tools/feedback_ingest.py](tools/feedback_ingest.py:659) 能解析反馈标注并读取 [statement_index.json](tools/feedback_ingest.py:664)。 |
| [statement_id](META/statement-record-contract-v1.md:152) -> [rule_id](META/statement-record-contract-v1.md:154) | PARTIAL | [tools/feedback_ingest.py](tools/feedback_ingest.py:704) 仍消费 [statement_index.json](tools/feedback_ingest.py:664) 和可选 [statement_rule_map.json](engine/application/artifact_inventory.py:26)，不是消费 [statement_record](META/statement-record-contract-v1.md:13)。 |
| dynamic confidence 消费 | PARTIAL | 规则级更新依赖 [tools.feedback_ingest.fanout_to_rules()](tools/feedback_ingest.py:214) 从 [statement_index.json](tools/feedback_ingest.py:226) 反查 [rule_ids](tools/feedback_ingest.py:245)，仍未直接读取 [statement_record](META/statement-record-contract-v1.md:13)。 |

## 2. 运行统计

只读扫描范围：[cases/**/statement_index.json](cases/) 与同目录 [feedback.md](cases/C-2026-026-坤-癸未甲寅壬戌丙午/feedback.md)。

| 指标 | 数量 |
|---|---:|
| [statement_index.json](cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json) 文件数 | 1010 |
| JSON 解析失败文件 | 0 |
| statement 条目数 | 4858 |
| 已生成标准 [statement_record](META/statement-record-contract-v1.md:13) 数量 | 0 |
| 可视为缺失标准 [statement_record](META/statement-record-contract-v1.md:13) 数量 | 4858 |
| 单数字段 [rule_id](META/statement-record-contract-v1.md:154) 覆盖 | 0 |
| 列表字段 [rule_ids](tools/render_report.py:1298) 覆盖 | 3768 |
| 反馈中 [statement_id](META/statement-record-contract-v1.md:152) 标注数 | 54 |
| 反馈 [statement_id](META/statement-record-contract-v1.md:152) 可命中索引数 | 54 |
| 命中后可取得规则映射数 | 10 |

必需字段缺失统计：

| 字段 | 缺失数量 | 说明 |
|---|---:|---|
| [statement_id](META/statement-record-contract-v1.md:152) | 61 | 少量历史条目仍无稳定断语 ID。 |
| [rule_id](META/statement-record-contract-v1.md:154) | 4858 | 标准单规则字段完全未落地；现有多为 [rule_ids](tools/render_report.py:1298) 列表。 |
| [family_id](META/statement-record-contract-v1.md:155) | 4858 | 未在生成期解析规则家族。 |
| [school](META/statement-record-contract-v1.md:156) | 4858 | 标准单字段未落地；现有多为 [schools](tools/render_report.py:1299) 列表。 |
| [canon](META/statement-record-contract-v1.md:157) | 4858 | 未在生成期冻结来源典籍或规范口径。 |
| [rule_type](META/statement-record-contract-v1.md:158) | 4858 | 未在生成期解析规则类型。 |
| [confidence_snapshot](META/statement-record-contract-v1.md:160) | 4858 | 未冻结生成时置信度快照。 |
| [generated_at](META/statement-record-contract-v1.md:161) | 4858 | 未记录 UTC 生成时间。 |

## 3. 链路核验

### A. statement_record 是否实际生成

未通过。

- [tools/render_report.py](tools/render_report.py:1257) 的实际产物是 [statement_index.json](cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json)，行结构为 [statement_id](META/statement-record-contract-v1.md:152)、domain、summary、status、section、[rule_ids](tools/render_report.py:1298)、schools 等展示/反馈索引字段。
- 未发现生成期将单条断语拆成一条或多条 [statement_record](META/statement-record-contract-v1.md:13) 的 factory、writer 或 artifact。
- 未发现字段链 [rule_id](META/statement-record-contract-v1.md:154) -> [family_id](META/statement-record-contract-v1.md:155) -> [school](META/statement-record-contract-v1.md:156) -> [canon](META/statement-record-contract-v1.md:157) -> [rule_type](META/statement-record-contract-v1.md:158) 在报告生成期被强制解析。

### B. rule trigger -> statement_record -> report -> feedback

未形成标准全链路。

现有链路是：

rule trigger / evidence -> [statement_index.json](tools/render_report.py:1257) -> report feedback anchor -> [feedback.md](tools/feedback_ingest.py:655) -> [statement_index.json](tools/feedback_ingest.py:664) -> [rule_ids](tools/feedback_ingest.py:245)

契约要求的链路应是：

rule trigger -> [statement_record](META/statement-record-contract-v1.md:13) -> compatible [statement_index.json](META/statement-record-contract-v1.md:223) -> report -> feedback -> [statement_record](META/statement-record-contract-v1.md:234) -> dynamic confidence

断点：生产报告链路没有 [statement_record](META/statement-record-contract-v1.md:13) 层，因此 feedback 到 rule 的学习链路仍依赖展示索引或旁路 [statement_rule_map.json](engine/application/artifact_inventory.py:26)。

### C. feedback 是否能直接引用 statement_id

部分通过。

- [tools/feedback_ingest.py](tools/feedback_ingest.py:659) 可以从 [feedback.md](tools/feedback_ingest.py:655) 解析 [statement_id](META/statement-record-contract-v1.md:152) 标注。
- 本次扫描中 54 条反馈 [statement_id](META/statement-record-contract-v1.md:152) 全部命中同案 [statement_index.json](cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json)。
- 只有 10 条反馈命中后具备规则映射，说明 [feedback](tools/feedback_ingest.py:659) -> [statement_id](META/statement-record-contract-v1.md:152) 已存在，但 [statement_id](META/statement-record-contract-v1.md:152) -> [rule_id](META/statement-record-contract-v1.md:154) 不稳定。

### D. dynamic confidence 是否可直接消费 statement_record

未通过。

- [tools.feedback_ingest.fanout_to_rules()](tools/feedback_ingest.py:214) 的输入仍是 [statement_index.json](tools/feedback_ingest.py:226)。
- [tools.feedback_ingest.fanout_to_rules()](tools/feedback_ingest.py:245) 从索引条目读取 [rule_ids](tools/render_report.py:1298)，没有读取标准 [statement_record](META/statement-record-contract-v1.md:13)。
- [tools/feedback_ingest.py](tools/feedback_ingest.py:715) 明确允许标准索引不承载规则映射，此时只登记反馈、不触发规则置信度更新。
- 因此 dynamic confidence 仍需要通过 [statement_index.json](tools/feedback_ingest.py:664) 或 [statement_rule_map.json](engine/application/artifact_inventory.py:26) 反推，不满足契约中直接消费 [statement_record](META/statement-record-contract-v1.md:13) 的要求。

## 4. 缺失文件

| 缺失文件 / artifact | 当前影响 |
|---|---|
| cases 每案标准 statement record artifact | 无法证明每条反馈断语对应一条规范 [statement_record](META/statement-record-contract-v1.md:13)。 |
| cases 每案 statement trace map 或 record envelope | 无法稳定承接 [statement_id](META/statement-record-contract-v1.md:152) -> [rule_id](META/statement-record-contract-v1.md:154) -> [family_id](META/statement-record-contract-v1.md:155)。 |
| 生产级 statement record schema 校验输出 | 缺字段不会 hard fail，只会退化为索引或旁路映射。 |
| dynamic confidence learning input artifact | 反馈摄入后没有标准化学习输入表来证明完整字段链。 |

说明：[engine/application/artifact_inventory.py](engine/application/artifact_inventory.py:26) 当前 hard gate 要求 [statement_index.json](engine/application/artifact_inventory.py:27) 与 [statement_rule_map.json](engine/application/artifact_inventory.py:28)，但未要求 [statement_record](META/statement-record-contract-v1.md:13) artifact。

## 5. 缺失模块

| 缺失模块 | 当前替代物 | 风险 |
|---|---|---|
| statement record builder / factory | [tools/render_report.py](tools/render_report.py:1257) 的 statement index builder | 只生成索引，不拆分多规则学习记录。 |
| rule metadata resolver | [tools/feedback_ingest.py](tools/feedback_ingest.py:245) 后置读取 [rule_ids](tools/render_report.py:1298) | [family_id](META/statement-record-contract-v1.md:155)、[canon](META/statement-record-contract-v1.md:157)、[rule_type](META/statement-record-contract-v1.md:158) 缺失。 |
| confidence snapshot freezer | 报告上下文中的 star / pct 零散字段 | 无生成时冻结快照，后续 posterior 存在时间穿越风险。 |
| statement record storage writer | [statement_index.json](tools/render_report.py:1257) 写入 | 展示索引与学习索引耦合。 |
| statement record validator / hard gate | [tools/output_linter.py](tools/output_linter.py:707) 对并行域索引做局部校验 | 无契约级字段完整性校验。 |
| dynamic confidence record consumer | [tools.feedback_ingest.fanout_to_rules()](tools/feedback_ingest.py:214) | 仍从 [statement_index.json](tools/feedback_ingest.py:226) 反查，不是直接消费记录。 |

## 6. 缺失字段

标准 [statement_record](META/statement-record-contract-v1.md:13) 要求生成期字段完整。当前 [statement_index.json](cases/C-2026-026-坤-癸未甲寅壬戌丙午/statement_index.json) 中缺失：

| 字段 | 当前状态 | 最小要求 |
|---|---|---|
| [rule_id](META/statement-record-contract-v1.md:154) | 0 / 4858 | 每条可学习记录必须单规则拆行。 |
| [family_id](META/statement-record-contract-v1.md:155) | 0 / 4858 | 必须在生成期从规则元数据解析。 |
| [school](META/statement-record-contract-v1.md:156) | 0 / 4858 | 必须使用标准单字段；列表 [schools](tools/render_report.py:1299) 不能替代单条学习记录。 |
| [canon](META/statement-record-contract-v1.md:157) | 0 / 4858 | 必须冻结来源体系。 |
| [rule_type](META/statement-record-contract-v1.md:158) | 0 / 4858 | 必须支持后续 rule type 权重与治理。 |
| [confidence_snapshot](META/statement-record-contract-v1.md:160) | 0 / 4858 | 必须记录 star、percent、posterior_mean、source 等生成时快照。 |
| [generated_at](META/statement-record-contract-v1.md:161) | 0 / 4858 | 必须为 UTC ISO-8601。 |

## 7. 最小落地方案

1. 在报告生成期新增 [statement_record](META/statement-record-contract-v1.md:13) builder：从 rule trigger / evidence 进入，不从报告文本反推。
2. 保留 [statement_index.json](tools/render_report.py:1257) 作为展示索引，但每个可反馈 [statement_id](META/statement-record-contract-v1.md:152) 必须能 join 到一条或多条 [statement_record](META/statement-record-contract-v1.md:13)。
3. 对多规则支撑断语按 [rule_id](META/statement-record-contract-v1.md:154) 拆成多条记录，每条记录绑定一个 [family_id](META/statement-record-contract-v1.md:155)。
4. 新增规则元数据解析层：生成期填充 [family_id](META/statement-record-contract-v1.md:155)、[school](META/statement-record-contract-v1.md:156)、[canon](META/statement-record-contract-v1.md:157)、[rule_type](META/statement-record-contract-v1.md:158)。
5. 在生成期冻结 [confidence_snapshot](META/statement-record-contract-v1.md:160) 与 [generated_at](META/statement-record-contract-v1.md:161)，禁止反馈后回填。
6. 修改反馈摄入路径，使 [tools.feedback_ingest.fanout_to_rules()](tools/feedback_ingest.py:214) 先消费 [statement_record](META/statement-record-contract-v1.md:13)，仅对 legacy case 回退 [statement_index.json](tools/feedback_ingest.py:226) / [statement_rule_map.json](engine/application/artifact_inventory.py:26)。
7. 在生产 artifact hard gate 加入 [statement_record](META/statement-record-contract-v1.md:13) artifact 和 schema 校验；缺字段即学习链路 fail，不得静默降级为动态置信度样本。

## 8. 预计工作量

| 工作项 | 估算 |
|---|---:|
| statement record builder 与 schema validator | 0.5-1 天 |
| rule metadata resolver 接入 | 1-2 天 |
| report generation pipeline 写入 record artifact | 0.5-1 天 |
| feedback ingest 改为优先消费 record | 0.5-1 天 |
| dynamic confidence 输入门禁与审计日志 | 1 天 |
| 回归测试与 2-3 个新案例验收 | 1 天 |
| 合计 | 4-7 人日 |

## 9. 审计结论

[statement-record-contract-v1](META/statement-record-contract-v1.md:13) 尚未在生产运行链真正完整落地。当前系统处于 PARTIAL：报告和反馈链路已有 [statement_id](META/statement-record-contract-v1.md:152) 与 [statement_index.json](tools/render_report.py:1257)，但学习事实单元仍不是标准 [statement_record](META/statement-record-contract-v1.md:13)。动态置信度仍依赖 [statement_index.json](tools/feedback_ingest.py:226) / [statement_rule_map.json](engine/application/artifact_inventory.py:26) 反推 [rule_id](META/statement-record-contract-v1.md:154)，缺少 [family_id](META/statement-record-contract-v1.md:155)、[canon](META/statement-record-contract-v1.md:157)、[rule_type](META/statement-record-contract-v1.md:158)、[confidence_snapshot](META/statement-record-contract-v1.md:160)、[generated_at](META/statement-record-contract-v1.md:161) 的生成期硬约束，因此尚不满足 READY。