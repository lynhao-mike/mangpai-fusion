# handoff · 短期下一步

> 本文件只服务当前/下一次 session 的短期交接，不作为版本、规则数量、N_eff、flagged/deprecated 清单的长期事实源。长期入口见 [`AGENTS.md`](AGENTS.md)，稳定状态见 [`STATUS.md`](STATUS.md)，机器状态见 [`META/project-state.json`](META/project-state.json)。

---

## 0. 最新交接 · 滴天髓调候派候选规则抽取（geju 最大安全吞吐）

> 更新时间：2026-06-13。此节优先级高于下方旧交接；当前任务是让新对话继续 `sources/tiaohou_ditiansui/` → `theory/tiaohou_ditiansui/index.yaml` 的候选调候规则提取/规格化工作。规则扩表已进入清洁目标区间，后续必须优先从未覆盖原文句群、反馈反证缺口或规则族合并规格出发，禁止靠薄改写继续堆数量。

### 0.1 当前状态

- 唯一输出目标：[`theory/tiaohou_ditiansui/index.yaml`](theory/tiaohou_ditiansui/index.yaml)。
- 当前已校验规则数：460 条。
- 最新有效规则 ID：`TIAOHOU-DTS-CAND-460`。
- 下一条若继续追加，应从 `TIAOHOU-DTS-CAND-461` 开始。
- 最近一次独立校验结果：`OK 460 rules TIAOHOU-DTS-CAND-460`。
- 最近四批追加摘要：第十四批 `296-345` 共 50 条；第十五批 `346-390` 共 45 条；第十六批 `391-430` 共 40 条；第十七批 `431-460` 共 30 条。
- 临时追加脚本 `tools/_append_tiaohou_batch14.py` 至 `tools/_append_tiaohou_batch17.py` 均已执行、校验并删除，当前不应遗留临时工具文件。

### 0.2 用户指定候选规则规格

规则文件使用顶层 YAML 列表，每项形如：

```yaml
- Rule:
    id: TIAOHOU-DTS-CAND-461
    school: tiaohou_ditiansui
    canon: 滴天髓调候派
    rule_type:
      - STRUCTURE | EVENT | TIMING | GENERAL_PRINCIPLE | ANTI_PATTERN
    statement: 可被反馈验证为对或错的条件化断语
    trigger_conditions:
      - 至少两个触发条件
    adjustment_mechanism:
      - 条件化增强/减弱/失效机制
    prediction_target:
      - 事业 / 财运 / 婚姻 / 健康 / 性格 / 应期
    evidence:
      - extracted_from_text
    confidence_init: 0.50
```

硬约束：

- 必须保持 `school: tiaohou_ditiansui`、`canon: 滴天髓调候派`、`confidence_init: 0.50`。
- `statement` 必须可失败、可反馈校准，不能写成不可证伪的泛化格言。
- 每条规则必须有 `trigger_conditions`，且至少 2 个条件。
- 每条规则必须有非空 `adjustment_mechanism`、`prediction_target`、`evidence`。
- 禁止在 YAML 内写注释、解释性散文或会话记录。
- 避免“可能 / 一般 / 通常”等弱化词；用明确条件和失效条件控制置信边界。
- 用户规格优先于仓库生产规则 schema；此文件当前是候选抽取规格，不要按生产规则 schema 强行改写。

### 0.3 下一轮推荐路线

1. 先确认当前文件仍为 460 条且末尾 ID 正确：

```cmd
python -c "exec('from pathlib import Path\nimport yaml\ndata=yaml.safe_load(Path(\"theory/tiaohou_ditiansui/index.yaml\").read_text(encoding=\"utf-8\"))\nprint(len(data), data[-1][\"Rule\"][\"id\"])')"
```

2. 若继续扩表，只从 `TIAOHOU-DTS-CAND-461` 起追加，并优先检查：
   - `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md`：体用、源流、通关、方局、墓库刑冲是否还有未覆盖原文句群。
   - `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md`：清浊真假是否还有可验证的拆分缺口。
   - `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md`：夫妻、子女、父母、兄弟是否还有宫星同动与岁运应期缺口。
   - `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part7.md`：疾病、性情是否还有五行偏枯与寒暖燥湿触发缺口。
   - `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md`：岁运、贞元是否还有运年触发和反证条件缺口。
3. 若找不到明确未覆盖原文句群，应暂停扩表，转入“规则族合并/重复审查/规格定稿”，重点审查相邻规则是否只是同义拆分。
4. 第十七批以后新增规则必须通过更高门槛：每条都要能说明它覆盖了哪类原文或反馈空白，而不是复述既有 460 条。

### 0.4 追加与校验工作流

推荐继续沿用临时脚本模式，但脚本执行后必须删除：

1. 新建 `tools/_append_tiaohou_batch18.py`。
2. 读取 [`theory/tiaohou_ditiansui/index.yaml`](theory/tiaohou_ditiansui/index.yaml)，先校验旧计数 `460` 与 ID 顺序。
3. 用 `R(...)` 构造 `NEW_RULES`，从 `TIAOHOU-DTS-CAND-461` 顺序编号。
4. 追加后校验新计数、字段完整性、ID 唯一性、`trigger_conditions` 长度、固定字段值。
5. 使用 `yaml.safe_dump(..., allow_unicode=True, sort_keys=False, width=1000)` 写回。
6. 独立运行一次校验命令；Windows `cmd.exe` 下如中文输出乱码，不影响 UTF-8 文件本身，但校验命令里可用 Unicode 转义规避终端编码问题。
7. 校验通过后删除临时脚本，避免污染 [`tools/README.md`](tools/README.md) 与 [`tools/tool_registry.py`](tools/tool_registry.py)。

### 0.5 当前质量判断

- 先前估算的清洁候选规则目标区间约为 430-520 条，理想控制在 450±30；当前 460 条已经进入理想区间。
- 继续“最大安全吞吐”不等于继续追求大批量；下一轮更适合小批量高确信扩表，或直接做重复审查与规格定稿。
- 可继续新增的优先级：原文未覆盖句群 > 反馈反证缺口 > 明确规则族边界补丁 > 同义规则合并规格。
- 禁止新增低价值变体：只替换预测域、只改五行名、只把同一机制换句话说，均应合并而不是追加。

---

## 1. 历史交接 · 问真补盘全量重算闭环（方案 C 第一/二阶段）

> 更新时间：2026-06-11。此节优先级高于下方旧交接；本轮已完成“问真补盘不是轻量回填，而是全量重算 + 硬门禁 + 可审计产物”的方案 C 第一/二阶段落地。下方 Top30 交接保留历史上下文，不再作为当前下一步判断依据。

### 0.1 本轮已完成

- 已形成诊断与方案备选文档：[`META/wenzhen-recompute-diagnosis-2026-06-11.md`](META/wenzhen-recompute-diagnosis-2026-06-11.md)。核心判断：补盘反馈闭环必须重跑真实 pipeline，不允许仅靠旧 `analysis_output.json` 或局部字段补写制造“已更新”假象。
- 新增应用层重算编排：[`engine/application/recompute.py`](engine/application/recompute.py)，统一执行 preflight、真实 pipeline、statement index hard gate、前后 findings 快照、跨流派矩阵、结论 diff、置信度 delta、反馈绑定检查与 manifest 写入。
- 新增跨流派裁判审计产物模块：
  - [`engine/application/school_verdict.py`](engine/application/school_verdict.py)：生成 `school_verdict_matrix.json`。
  - [`engine/application/conclusion_diff.py`](engine/application/conclusion_diff.py)：生成 `conclusion_diff.json`。
  - [`engine/application/confidence_delta.py`](engine/application/confidence_delta.py)：生成 `confidence_delta.json`。
- 新增 CLI：[`tools/recompute_wenzhen_case.py`](tools/recompute_wenzhen_case.py)，支持按 case id 或 `input.md` 路径执行：

```bash
python -m tools.recompute_wenzhen_case C-2026-XXX-乾-四柱 --json
python -m tools.recompute_wenzhen_case cases/C-2026-XXX-乾-四柱/input.md --json
```

- CLI 默认启用 statement index 硬门禁：若 [`statement_index.json`](cases/) 缺失或 `statements` 为空，返回码为 `2`，状态为 `hard_gate_failed`；仅调试时可使用 `--allow-empty-statement-index`。
- 已将重算能力暴露到应用层公共入口：[`engine/application/__init__.py`](engine/application/__init__.py) 导出 `RecomputeRequest`、`RecomputeResult`、`RecomputeHardGateError`、`recompute_wenzhen_case()`。
- 已增强 `feedback_binding_check.json`：复用 [`tools/feedback_ingest.py`](tools/feedback_ingest.py) 的 `parse_statement_feedback()`，识别结构化 `[S-...] [y/n/?/skip]` 反馈数量、已绑定断语、未知 statement id，并写入 `recompute_manifest.json` 的 hard gate 摘要。
- 新增回归测试：[`tests/test_wenzhen_recompute.py`](tests/test_wenzhen_recompute.py)，覆盖 artifact 写入、statement index hard gate、CLI 失败码、应用层公共导出、合法 statement id 反馈解析与未知 statement 识别。

### 0.2 新增/更新的重算产物约定

一次成功重算会在 case 目录生成或更新以下审计产物：

- `findings.before.json`
- `findings.after.json`
- `school_verdict_matrix.json`
- `conclusion_diff.json`
- `confidence_delta.json`
- `feedback_binding_check.json`
- `recompute_manifest.json`

同时要求 pipeline 产出非空 [`statement_index.json`](cases/)；统一内容报告仍按既有 pipeline/report 流程输出到 [`reports/`](reports/)。

### 0.3 验证状态

已通过：

```bash
pytest tests/test_wenzhen_recompute.py -q
pytest tests/test_production_service.py -q
python -m tools.recompute_wenzhen_case --help
python -m compileall engine/application/conclusion_diff.py engine/application/confidence_delta.py engine/application/school_verdict.py engine/application/recompute.py tools/recompute_wenzhen_case.py tests/test_wenzhen_recompute.py
python -m compileall engine/application/__init__.py engine/application/recompute.py tests/test_wenzhen_recompute.py
```

关键结果：

- 重算聚焦测试：`4 passed`。
- 生产服务相邻测试：`6 passed`。
- CLI 帮助命令可正常加载。
- 编译检查通过。

### 0.4 当前工作区预期变更

- [`META/wenzhen-recompute-diagnosis-2026-06-11.md`](META/wenzhen-recompute-diagnosis-2026-06-11.md)：诊断与方案备选文档。
- [`engine/application/recompute.py`](engine/application/recompute.py)：全量重算应用层入口。
- [`engine/application/school_verdict.py`](engine/application/school_verdict.py)：跨流派矩阵构建。
- [`engine/application/conclusion_diff.py`](engine/application/conclusion_diff.py)：结论变化追踪。
- [`engine/application/confidence_delta.py`](engine/application/confidence_delta.py)：置信度变化追踪。
- [`engine/application/__init__.py`](engine/application/__init__.py)：公共导出更新。
- [`tools/recompute_wenzhen_case.py`](tools/recompute_wenzhen_case.py)：重算 CLI。
- [`tests/test_wenzhen_recompute.py`](tests/test_wenzhen_recompute.py)：重算闭环回归测试。
- [`handoff.md`](handoff.md)：本交接更新。

### 0.5 下一步建议

1. 将 [`tools/recompute_wenzhen_case.py`](tools/recompute_wenzhen_case.py) 登记到 [`tools/README.md`](tools/README.md) 与 [`tools/tool_registry.py`](tools/tool_registry.py)，标记为 active 工具，并运行 `python tools/tool_registry.py --check`。
2. 选择 1 个已归档问真 RF case 做真实重算试运行，优先用 `--json` 保存输出；若硬门禁失败，先修 pipeline/render 的 `statement_index.json` 生成，不要关闭 hard gate。
3. 真实试运行后检查 `feedback_binding_check.json`：若存在 `unknown_structured_statement_ids`，说明 [`feedback.md`](templates/feedback.md) 中标注的 statement id 与最新 [`statement_index.json`](cases/) 不匹配，需人工重绑。
4. 若要批量补跑 Top30，不要直接批量执行；先抽样验证 1-3 案，再新增批量 wrapper，并要求每案都有 `recompute_manifest.json`。
5. 后续若把重算纳入反馈摄入前置流程，应让 [`tools/feedback_ingest.py`](tools/feedback_ingest.py) 或批处理工具读取 `recompute_manifest.json`，拒绝 statement index 不完整或反馈绑定不一致的 case。

### 0.6 禁止误用提醒

- 不要用旧 `findings/analysis_output.json` 代替全量重算结果。
- 不要把 `--allow-empty-statement-index` 用在正式补盘闭环；它只适合调试。
- 不要只看报告文本是否生成；必须检查 `recompute_manifest.json` 与 `feedback_binding_check.json`。
- 不要把未知 statement id 静默丢弃；应保留在 `unknown_structured_statement_ids` 中交给人工重绑。

---

## 1. 历史交接 · 问真 Top30 转案、报告与工具索引维护

> 更新时间：2026-06-09。此节优先级高于下方旧交接；问真 Top30 已完成 OCR 修正、正式转案、命理师报告生成与工具索引漂移修复。下方旧节保留历史上下文，不再作为当前下一步判断依据。

### 0.1 本轮已完成

- 已完成问真 Top30 中 4 个 OCR 阻塞样本的人工确认修正：`王→壬`、`西→酉`。
- 已重新运行 review gate、staging manifest、promotion preflight，Top30 OCR 队列已清零。
- 已将 4 个原 OCR 阻塞样本转为正式 case：
  - `C-2026-RF000771-乾-癸亥壬戌壬午庚子`
  - `C-2026-RF000551-乾-壬戌丙午甲申丁卯`
  - `C-2026-RF000894-乾-壬戌己酉庚子戊子`
  - `C-2026-RF000684-坤-己巳丙子戊申戊午`
- 已为上述 4 案生成命理师内部报告：
  - [`reports/C-2026-RF000771-乾-癸亥壬戌壬午庚子-analyst-report.md`](reports/C-2026-RF000771-乾-癸亥壬戌壬午庚子-analyst-report.md)
  - [`reports/C-2026-RF000551-乾-壬戌丙午甲申丁卯-analyst-report.md`](reports/C-2026-RF000551-乾-壬戌丙午甲申丁卯-analyst-report.md)
  - [`reports/C-2026-RF000894-乾-壬戌己酉庚子戊子-analyst-report.md`](reports/C-2026-RF000894-乾-壬戌己酉庚子戊子-analyst-report.md)
  - [`reports/C-2026-RF000684-坤-己巳丙子戊申戊午-analyst-report.md`](reports/C-2026-RF000684-坤-己巳丙子戊申戊午-analyst-report.md)
- 已修复应期候选事件 domain 归一化：[`engine/application/candidates.py`](engine/application/candidates.py) 将 `子女`、`父母`、`亲属`、`兄弟姐妹` 等映射为 D3 gate 支持的 `六亲`。
- 已新增候选事件回归测试：[`tests/test_application_candidates.py`](tests/test_application_candidates.py)。
- 已删除临时报表渲染脚本 `tools/_tmp_render_existing_wenzhen_reports.py`。
- 已修复工具索引漂移：[`tools/README.md`](tools/README.md) historical 表新增 11 个问真批处理/迁移辅助工具，`python tools/tool_registry.py --check` 已通过。
- 已完成问真 Top30 全量 case/report 互链核查，并为 30 个 RF 正式 case 的 `analysis.md` 补充命理师报告反向归档链接；临时核查脚本已删除，未纳入工具索引。
- 已评估 Top30 feedback 批量摄入准备状态：30 个 RF case 均有 `feedback.md`，但当前均未包含 `[S-...] [y/n/?/skip]` 标注；5 个 RF case 已在 `iteration-state` 中计为 completed，Top30 本轮不执行正式摄入。
- 已为 30 个 RF case 的 `feedback.md` 更新关联报告路径，将“待生成”改为对应 `reports/*-analyst-report.md`，并更新断语反馈占位说明，提示后续手动补 `[S-...]` 标注后再摄入。

### 0.2 验证状态

已通过：

```bash
python -m pytest tests/test_project_metadata.py tests/test_application_candidates.py -q
python -m pytest tests/ -q
python tools/tool_registry.py --check
python tools/rule_status_scan.py --check
```

关键结果：

- 元数据 + 候选事件测试：`14 passed`。
- 全量测试：`290 passed, 1 skipped`。
- 工具索引：`tool registry check passed`。
- 规则状态扫描：`rule status scan passed`。
- 4 份新报告经 [`tools/output_linter.py`](tools/output_linter.py) 定向校验无 ERROR，仅有既有 WARN。
- 4 份新报告经 [`tools/check_archive_links.py`](tools/check_archive_links.py) 定向归档链接校验：`targeted archive links ok`。
- Top30 全量 RF analyst report ↔ case 互链核查：`rf_analyst_reports 30`，`errors 0`。
- 提交前关键校验已复跑：`python tools/tool_registry.py --check`、`python tools/rule_status_scan.py --check`、`python -m pytest tests/test_project_metadata.py tests/test_application_candidates.py -q`，结果分别为通过、通过、`14 passed`。
- Top30 feedback readiness：`rf_cases 30`、`completed_rf 5`、`missing_feedback 0`、`with_annotations 0`、`without_annotations 30`、`pending_annotated 0`。
- `python -m tools.batch_review --strict-v13 --dry-run --json` 已通过；当前 strict v1.3 pending 为非 Top30 的 2 案，dry-run 结果 `input 2`、`success 2`、`failure 0`、`rule_updates 20`。
- Top30 提交前质量复核已通过：`rf_reports 30`、`rf_case_ids 30`、`unique_case_ids 30`、`strict_v13_annotated_feedback 0`、`errors 0`、`warnings 0`；临时复核脚本已删除。

### 0.3 当前工作区状态

当前预期变更：

- [`tools/README.md`](tools/README.md)：补登记问真批处理/迁移辅助工具。
- 30 个 `cases/C-2026-RF*/analysis.md`：补充 `## 四、归档互链` 与对应 `reports/*-analyst-report.md` 反向链接。
- 30 个 `cases/C-2026-RF*/feedback.md`：更新关联报告链接与断语反馈占位说明。
- [`handoff.md`](handoff.md)：记录 Top30 全量互链核查、feedback readiness、dry-run 与提交前校验结果。

报告、case 与候选事件归一化相关变更已经在当前工作区状态中体现；全量测试会改写 C-2026-001 findings 运行时产物，已用 `git checkout -- cases/C-2026-001-乾-庚申戊寅壬子辛丑/findings/analysis_output.json cases/C-2026-001-乾-庚申戊寅壬子辛丑/findings/timing.json` 恢复。

### 0.4 下一步建议

1. 若继续维护问真 Top30，需先把命理师报告中的断语反馈位复制/整理到各 `feedback.md` 并人工标注 `[y]` / `[n]` / `[?]` / `[skip]`；当前 Top30 不具备 strict v1.3 批量摄入条件。
2. 旧问真 dry-run 叙述已归档精简；后续不要再按旧 OCR 阻塞/首批 dry-run 流程推进 Top30。
3. 若准备提交变更，先运行：

```bash
git status --short --untracked-files=all
python tools/tool_registry.py --check
python tools/rule_status_scan.py --check
python -m pytest tests/test_project_metadata.py tests/test_application_candidates.py -q
```

---

## 2. 历史交接 · 多流派并行功能域与裁判模型

> 更新时间：2026-06-08。此节优先级高于下方旧的问真转案短期交接；下方内容保留为历史上下文，除非用户明确要求继续问真转案，否则下一位 agent 应先接续本节。

### 0.1 本轮已完成

本轮根据“多流派并行功能域分析与裁判模型”方案，采用最小补丁方式对现有 v1.5 旁路实现做了加固，没有从零重建模型，也没有覆盖既有契约。

已完成改动：

- 加固 [`run_parallel_domain_analysis()`](engine/application/parallel_domain_runner.py)：每个 analyzer 调用都会拿到独立 [`DomainAnalysisContext`](engine/application/domain_analyzers.py) 副本，避免共享 `base_context` 污染。
- 加固异常隔离：单个 analyzer 抛异常时，runner 会转成显式 abstain reading，不影响同域其他专家或后续领域。
- 扩展 [`DomainAnalyzer`](engine/application/domain_analyzers.py)：新增 `is_wired()` 协议，并在 [`DomainAnalyzerRegistry`](engine/application/domain_analyzers.py) 上提供 wiring 状态查询。
- 新增模块级 [`get_wiring_status()`](engine/application/domain_analyzers.py)，返回默认 6 域 × 3 专家体系的 `wired` / `abstain_only` 状态。
- 扩展 [`tools/feedback_ingest.py`](tools/feedback_ingest.py)：新增 parallel-domain statement 反馈 fanout，到 reading / adjudication 级 JSONL 日志。
- 新增日志目标：[`engine/logs/expert_domain_feedback.jsonl`](engine/logs/expert_domain_feedback.jsonl) 与 [`engine/logs/adjudication_accuracy.jsonl`](engine/logs/adjudication_accuracy.jsonl)。这两个文件按需追加生成；当前不要求已存在。
- 新增 [`get_expert_domain_stats()`](tools/feedback_ingest.py) 聚合 expert × domain 命中 / 失验、`n_eff`、Beta mean、Wilson lower bound。
- 新增 [`compute_weight_update_proposal()`](tools/feedback_ingest.py) 生成动态权重调整提案；只返回 proposal，不自动修改任何 YAML 权重源。
- 扩展测试：[`tests/test_parallel_domain_runner.py`](tests/test_parallel_domain_runner.py) 与 [`tests/v1_3_acceptance/test_h3_feedback_parsing.py`](tests/v1_3_acceptance/test_h3_feedback_parsing.py)。

验证已通过：

```bash
python -m pytest tests/test_parallel_domain_runner.py tests/v1_3_acceptance/test_h3_feedback_parsing.py -q
```

结果：`13 passed in 0.27s`。

### 0.2 本轮触碰文件

- [`engine/application/parallel_domain_runner.py`](engine/application/parallel_domain_runner.py)
- [`engine/application/domain_analyzers.py`](engine/application/domain_analyzers.py)
- [`tools/feedback_ingest.py`](tools/feedback_ingest.py)
- [`tests/test_parallel_domain_runner.py`](tests/test_parallel_domain_runner.py)
- [`tests/v1_3_acceptance/test_h3_feedback_parsing.py`](tests/v1_3_acceptance/test_h3_feedback_parsing.py)
- [`handoff.md`](handoff.md)

未触碰：

- [`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py)
- [`engine/energy/`](engine/energy/)
- [`engine/picture/`](engine/picture/)
- [`engine/yingqi/`](engine/yingqi/)
- [`engine/pangzheng/`](engine/pangzheng/)

### 0.3 下一位 agent 应继续做什么

用户会把完整计划和执行方案一起发给下一位 agent。下一位 agent 不要按“从零创建阶段 1-A / 1-B”执行，因为当前仓库已经存在并行域模型、runner、orchestrator、adjudication、statement index 与测试骨架。

建议下一步按以下顺序继续：

1. 先读取 [`META/project-state.json`](META/project-state.json)、[`engine/domain/parallel.py`](engine/domain/parallel.py)、[`engine/application/adjudication.py`](engine/application/adjudication.py)、[`engine/application/domain_analyzers.py`](engine/application/domain_analyzers.py)、[`engine/application/parallel_domain_runner.py`](engine/application/parallel_domain_runner.py)、[`tools/feedback_ingest.py`](tools/feedback_ingest.py)。
2. 运行一次最小验证：`python -m pytest tests/test_parallel_domain_runner.py tests/v1_3_acceptance/test_h3_feedback_parsing.py -q`。
3. 继续补动态权重闭环的“读取/应用 proposal”层：可以新增人工确认后的 `apply_weight_update_proposal()`，但必须保持默认不自动写权重。
4. 若要接入裁判实时权重，优先在 [`engine/application/adjudication.py`](engine/application/adjudication.py) 支持可注入 feedback overlay / `WeightProfile`，不要替换现有 review draft prior profile。
5. 扩展测试覆盖：proposal 应用前后权重归一化、`n_eff < 5` 只警告不调整、`n_eff >= 10` 才允许较大调整、连续 miss 触发降权 proposal。
6. 如需面向 CLI 暴露统计，可以考虑给 [`tools/feedback_ingest.py`](tools/feedback_ingest.py) 增加只读参数，例如 `--expert-domain-stats` / `--weight-proposal`；不要默认在 ingest 后自动改权重。
7. 最后再考虑是否更新 [`META/project-state.json`](META/project-state.json) 中 `v1_5_status.dynamic_feedback_weighting`；只有当 proposal + 人工应用 + 测试闭环都完成后，才可从 `pending` 改为更准确状态。

### 0.4 下一位 agent 必须遵守的约束

- 不要覆盖 [`engine/domain/parallel.py`](engine/domain/parallel.py)；只能做兼容性增补。
- 内部专家枚举继续使用 `blind` / `ziping` / `tiaohou_ditiansui`，中文只在报告层展示。
- 功能域继续使用现有 `财运` / `事业` / `婚姻` / `健康` / `性格` / `学业`。
- 不要修改 [`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py)。
- 不要修改 D1-D4 核心目录：[`engine/energy/`](engine/energy/)、[`engine/picture/`](engine/picture/)、[`engine/yingqi/`](engine/yingqi/)、[`engine/pangzheng/`](engine/pangzheng/)。
- 不要让任一专家 analyzer 读取其他专家中间态；跨专家信息只能通过 [`ExpertReading`](engine/domain/parallel.py) 进入裁判。
- 动态权重默认只产出 proposal 和日志；未经人工确认，不得自动改 prior profile 或 YAML 权重文件。

### 0.5 可直接发给下一位 agent 的开场指令

```text
请先读取 handoff.md 的“0. 最新交接 · 多流派并行功能域与裁判模型”。我会把完整计划和执行方案一并发给你，但不要按从零创建文件执行；当前仓库已存在 v1.5 并行域模型、runner、orchestrator、adjudication、statement index 与测试骨架。请在现有实现基础上继续最小补丁：先复跑 python -m pytest tests/test_parallel_domain_runner.py tests/v1_3_acceptance/test_h3_feedback_parsing.py -q，然后继续补动态反馈权重闭环的 proposal 应用与测试。不要修改 engine/application/pipeline_runner.py，不要修改 D1-D4 核心目录，不要自动改权重 YAML。
```

---

## 3. 历史交接 · 问真 dry-run 流程归档说明

> 以下旧 dry-run 叙述已归档精简。当前事实以本文件顶部“0. 最新交接 · 问真 Top30 转案、报告与工具索引维护”为准：Top30 已完成 OCR 修正、正式转案、报告生成、case/report 互链与 feedback readiness 核查。不要再按旧流程判断为“仍有 4 个 OCR 阻塞样本”或“尚未创建正式 case”。

历史上下文仅保留用于追溯：

- 问真排盘补录阶段曾从男女优先索引抽取 98 个完整样本，并生成 Top30 审阅包。
- 旧阶段曾有 4 个 OCR 阻塞 raw_id：`RF-2026-000771`、`RF-2026-000551`、`RF-2026-000894`、`RF-2026-000684`；这些样本已在最新交接中完成修正并转正式 case。
- 旧阶段曾有 26 个非阻塞 staging 候选与首批 5 案 dry-run promotion plan；当前 Top30 已进入正式 case/report 归档状态，不应再要求“先确认首批 5 案再创建 case”。
- 相关历史产物仍可按需查阅：[`cases/raw_feedback/parsed/wenzhen_repan_top30_review.md`](cases/raw_feedback/parsed/wenzhen_repan_top30_review.md)、[`cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.jsonl`](cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.jsonl)、[`cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_preflight-summary.json`](cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_preflight-summary.json)、[`cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.md`](cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.md)。

当前后续如继续问真 Top30，只做两类工作：

1. 给 30 个 RF case 的 [`feedback.md`](cases/) 人工补充 `[S-...] [y/n/?/skip]` 后，再运行 strict v1.3 feedback ingest / batch review。
2. 或对已归档的 30 份 [`reports/*-analyst-report.md`](reports/) 与 30 个 [`cases/C-2026-RF*/`](cases/) 做提交前质量核查。

---

## 7. 禁止误用提醒

- 不要从 [`handoff.md`](handoff.md) 推断长期版本状态；版本看 [`VERSION`](VERSION)，机器状态看 [`META/project-state.json`](META/project-state.json)。
- 不要把 `current_phase` 当产品版本。
- 不要使用 deprecated 的 [`tools/calibrate.py`](tools/calibrate.py) 作为新反馈入口。
- 不要只生成报告或分析而不归档 case；正式案例必须能被后续 [`tools/feedback_ingest.py`](tools/feedback_ingest.py) / [`tools/feedback_loop.py`](tools/feedback_loop.py) 追踪。
- 不要在报告标题或 case id 中遗漏乾/坤。
