# 多专家功能域裁判反馈闭环 Phase 2 · Terra 无人值守执行提示词

> 用途：复制本文件全文作为新会话的第一条用户消息，指导 ChatGPT 5.6 Terra（或等价 agent）无人值守完成本任务。目标是让整个任务在**一次对话**内闭环完成；允许拆分子任务（例如"写聚合扫描器"“写 staleness 检测"“补测试"“更新工具索引与路线表"），但子任务只是执行顺序，不需要跨会话交接。
>
> 前置任务：[`plans/parallel-domain-feedback-loop-phase1-terra-kickoff-prompt.md`](parallel-domain-feedback-loop-phase1-terra-kickoff-prompt.md) 已完成并 evidence-bounded freeze。Phase 1 把"statement 反馈 → expert/domain 统计 → 调权提案 → 人工确认 → 写回 `engine/expert-weights.yaml`"这条链路接通，但**真实生产 overlay 目前仍是 `no-feedback-overlay` / `entries: []`**——因为还没有人对真实案例执行过正式 promotion。Phase 2 不重做 Phase 1，只在其基础上补齐可观测性与前置证据，且明确不做生产路由切换。

---

## 0. 背景与真实事实源（先读，不得凭旧摘要推断）

1. [`AGENTS.md`](../AGENTS.md) —— 仓库 AI 调用规则，事实源矩阵与最小上下文原则。
2. [`STATUS.md`](../STATUS.md) 第 3 节与第 6 节：多专家功能域裁判当前仍是"旁路"，Phase 1 反馈闭环已接通但"默认生产 overlay 与主裁判路由未自动切换"。第 6 节 P2 行写着：
   > 在已落地的人工反馈调权闭环之上，完成多专家功能域裁判的主裁判路由与生产默认切换
   
   **这个 P2 行本身描述的是最终目标，不是本任务（Phase 2）要一次做完的范围**——见第 1 节任务边界说明，为什么"主裁判路由与生产默认切换"现在做不了、也不该做。
3. [`engine/contracts/00-OVERVIEW.md`](../engine/contracts/00-OVERVIEW.md) 第一、二节的**迁移红线**（重新读取原文，不要相信复述）：
   > 五派并行主流程未跑出"六大领域 × 十五层判断 × 三段裁判 × 主要事件预测账本"的已归档案例证明物前，不切换正式入口
   
   当前 [`engine/application/pipeline_runner.py`](../engine/application/pipeline_runner.py) 仍是唯一"已落地兼容入口"；[`engine/application/parallel_domain_orchestrator.py`](../engine/application/parallel_domain_orchestrator.py) 的 `analyze_parallel_domains()` 只是通过已 deprecated 的 [`engine/application/dual_engine_adapter.py`](../engine/application/dual_engine_adapter.py)（`analyze_dual_engine`，计划 v6 移除）被 `pipeline_runner.run_pipeline()` 调用，产出挂在 `output.parallel_analysis` 上，**不参与任何最终断语裁决**。这个证明物目前不存在，也没有任何工具在生成它。**因此本任务不做、也不能做"主裁判路由切换"。**
4. Phase 1 交付的真实现状（重新读取源码确认，不要相信本段复述）：
   - [`tools/feedback_ingest.py`](../tools/feedback_ingest.py) 的 `ingest()` 主流程已真正调用 `fanout_to_parallel_feedback()`，把 statement 反馈写入 `engine/logs/expert_domain_feedback.jsonl` 与 `engine/logs/adjudication_accuracy.jsonl`。
   - [`tools/promote_expert_weight_feedback.py`](../tools/promote_expert_weight_feedback.py) 的 `promote_expert_weight_feedback()`（约第 107 行）默认 dry-run，正式写入要求非空 `reviewed_by`，`version` 从 `feedback-overlay-v{N}` 严格递增且拒绝复用，只替换 `engine/expert-weights.yaml` 的 `feedback_overlay` 段落，不改 `weights` 本身。
   - 真实 `engine/expert-weights.yaml` 当前 `feedback_overlay.version == "no-feedback-overlay"`，`entries == []`——因为没有真实反馈样本被正式 promote 过。这是 Phase 1 交付时刻的真实状态，不是 bug。
   - `get_expert_domain_stats()` / `compute_weight_update_proposal()`（[`tools/feedback_ingest.py`](../tools/feedback_ingest.py) 约第 446-513 行）只聚合**当前一次进程内 / 单个 jsonl 文件**的统计，没有任何工具对"多案例累积后的 N_eff 是否已经越过 promotion 门槛"做常态化、只读、可重复运行的报告。
   - Phase 1 交付说明中明确留下两条 Phase 2 候选：（a）跨案例 N_eff 汇总面板；（b）是否要把 promotion 状态纳入类似 [`tools/rule_status_scan.py`](../tools/rule_status_scan.py) 的常规扫描。本任务就是把这两条做实。
5. [`tools/rule_status_scan.py`](../tools/rule_status_scan.py) 是仓库既有的"只读状态扫描器"标准范式：`argparse` 提供 `--format markdown|json` 与 `--check`；`--check` 用于 CI/人工快速判断是否有需要关注的项，但**扫描器本身绝不写任何文件**。重新读取该文件全文（含其 `--check` 的 exit code 语义，约在文件下半部分），本任务新工具必须复用同一套 CLI 风格，不要发明新范式。
6. [`tools/README.md`](../tools/README.md) 的"唯一工具索引"要求：新增可执行工具必须登记，并标注真实调用边界（active/internal/deprecated 等状态约定见文件头）。

不要从 `handoff.md`、旧 plans 文档或本文件之外的任何摘要推断当前实现状态；一切以上述文件的当前源码为准。若发现本节描述与实际源码不一致（例如行号漂移、函数已被改名），以实际源码为准，并在最终交付说明中记录差异。

---

## 1. 任务目标（唯一长任务）

**在不触碰生产路由、不触碰 `production_switch`、不修改 `pipeline_runner.py` / `dual_engine_adapter.py` 的前提下，给"多专家功能域裁判反馈闭环"补上跨案例可观测面板，并把 promotion 前置证据纳入常规化只读扫描。**

必须完成且可验证的两件事：

1. **新增只读聚合扫描器**（建议 `tools/parallel_domain_weight_status_scan.py`）：
   - 读取真实 `engine/logs/expert_domain_feedback.jsonl` 与 `engine/logs/adjudication_accuracy.jsonl`（若文件不存在，视为零样本，不报错崩溃）。
   - 按 `(domain, expert_system)` 聚合**全部历史行**（不是单次 ingest 的增量）的 hits/misses/N_eff/beta_mean/wilson_lower——可复用或对齐 `tools/feedback_ingest.py` 的 `_finalize_expert_stats()` / `get_expert_domain_stats()` 的算法，但要在"跨全部日志行"的口径下重算，不能假设调用者已经把日志过滤好。
   - 读取真实 `engine/expert-weights.yaml` 的 `feedback_overlay`，报告当前 `version` / `entries` 数量 / 每个已有 entry 的 `(domain, expert_system, n_eff)`。
   - 对每个 `(domain, expert_system)`，比较"日志聚合的当前 N_eff"与"overlay 里已记录的 n_eff"：若日志聚合 N_eff 已达到 `min_effective_sample_for_adjustment`（从 canonical YAML 读取，不硬编码）且**尚未出现在 overlay entries 中，或 overlay 中的 n_eff 明显落后于日志聚合值**，则标记为 `pending_promotion_review`（只读标记，不自动做任何写入或建议具体数值）。
   - 提供 `--format markdown|json` 与 `--check`（`--check` 语义：存在 `pending_promotion_review` 项时返回非零 exit code 并打印清单，供人工决定是否要跑 `tools/promote_expert_weight_feedback.py`；没有任何自动 promotion 行为）。
2. **登记与路线表更新**：
   - 在 [`tools/README.md`](../tools/README.md) 登记新工具（active，只读）。
   - 更新 [`STATUS.md`](../STATUS.md) 第 6 节，把原来笼统的 P2 行拆成两行：
     - 一行描述"跨案例 promotion 前置证据可观测（本任务已完成）"；
     - 一行保留"主裁判路由与生产默认切换"作为**未来、需要五派主流程证明物 + 显式用户/架构师授权**的独立后续项，不得暗示本任务已经推进了路由切换本身。
   - 若 [`META/project-state.json`](../META/project-state.json) 中存在合适的既有字段可以如实更新（例如说明 promotion 前置可观测性已落地），可以更新；**不得为了显得"更完成"而发明新的顶层字段或误导性状态值**。若没有合适字段，只在 STATUS.md 中说明即可，不要求必须改 project-state.json。

---

## 2. 强制使用 TDD（本仓库标准要求）

1. 先写一个测试，用**明确标注为测试 fixture 的合成 jsonl 数据**（不要读取或依赖真实 `engine/logs/` 里的任何历史内容），构造至少两个不同 `case_id` 对同一个 `(domain, expert_system)` 的 hit/miss 行，断言聚合器的 N_eff / beta_mean 计算是"跨全部行"而不是"最后一个文件片段"。确认它当前失败（因为聚合器还不存在）。
2. 实现最小聚合函数使其通过（GREEN）。
3. 再写一个测试证明"staleness / pending_promotion_review"判定逻辑：构造一个日志聚合 N_eff 已经越过 `min_effective_sample_for_adjustment`，但 canonical overlay（用临时 profile 文件，不得指向真实 `engine/expert-weights.yaml`）里没有对应 entry 的场景，断言该 `(domain, expert_system)` 被正确标记；再构造一个 overlay 已经反映最新聚合值的场景，断言不被标记。RED → GREEN 各跑一次。
4. 补 CLI 层测试或至少一次手动运行证明 `--format markdown` / `--format json` / `--check` 的 exit code 符合第 1 节约定。
5. 每次 GREEN 后运行相关测试文件确认无回归，最后运行一次更大范围的相关测试集合：
   ```bash
   python -m pytest tests/v1_3_acceptance -q
   python -m pytest tests/test_promote_expert_weight_feedback.py -q
   python -m pytest tests/test_project_metadata.py -q
   python tools/tool_registry.py --check
   ```
   不要求也不建议在本任务内跑全仓 `pytest -q`。

---

## 3. 允许修改的文件范围（写集边界）

允许修改或新增：

- 新文件 `tools/parallel_domain_weight_status_scan.py`（聚合扫描器）
- 新文件 `tests/test_parallel_domain_weight_status_scan.py`（遵循仓库现有习惯：测试放在根 `tests/`，不是 `tests/tools/`——重新确认一次仓库当前是否已出现 `tests/tools/` 目录；若已出现则跟随最新惯例）
- [`tools/README.md`](../tools/README.md)（登记新工具）
- [`STATUS.md`](../STATUS.md) 第 6 节 P2 相关行（拆分为两行，见第 1 节第 2 点）
- [`META/project-state.json`](../META/project-state.json)（仅当存在合适既有字段可如实更新时；不强制）

不允许修改：

- [`engine/application/pipeline_runner.py`](../engine/application/pipeline_runner.py)、[`engine/application/dual_engine_adapter.py`](../engine/application/dual_engine_adapter.py)、[`engine/application/parallel_domain_orchestrator.py`](../engine/application/parallel_domain_orchestrator.py)、[`engine/application/adjudication.py`](../engine/application/adjudication.py)（本任务不做任何裁判逻辑或路由改动）
- 任何 `production_switch` 相关字段或语义
- [`engine/expert-weights.yaml`](../engine/expert-weights.yaml)（本任务只读该文件，绝不写入；写入仍然只能通过 [`tools/promote_expert_weight_feedback.py`](../tools/promote_expert_weight_feedback.py) 的既有正式路径，而这条路径本身不在本任务范围内）
- [`engine/domain-weights.yaml`](../engine/domain-weights.yaml)（legacy four-school matrix，与本任务无关）
- 任何 `engine/f09/`、`tests/f09/`、Task 9-P 相关专项冻结文件、任何 prospective-go 单案制品
- 真实 `engine/logs/expert_domain_feedback.jsonl` / `engine/logs/adjudication_accuracy.jsonl`（本任务只读，绝不清空、改写或用测试数据污染这两个真实文件；所有测试必须用 `tmp_path` 临时文件）
- 不得执行任何 Git 或 GitHub 写操作（本地 `git status`/`git diff` 只读查看不受限，但禁止 commit/push/PR 等任何写操作，除非用户在后续消息中另行明确授权）

---

## 4. 关键设计约束（防止走偏）

1. **本任务绝不是路由切换的"半步"**：不得以任何理由修改 `pipeline_runner.py` 里 `analyze_dual_engine` 的调用方式，也不得让新扫描器的输出被任何生产代码路径读取或消费。新扫描器是纯粹的人工可观测面板，输出只面向运行它的人，不接入 pipeline。
2. **不得伪造或夸大 pending_promotion_review 判定**：判定阈值必须从 canonical `engine/expert-weights.yaml` 的 `constraints.min_effective_sample_for_adjustment` / `feedback_overlay.min_effective_sample_for_adjustment` 读取，不得硬编码一个更容易触发的数字来让测试或输出"看起来有内容"。若真实日志当前为空（Phase 1 交付时确实如此），扫描器对真实文件运行时报告"0 个 pending 项"是正确结果，不是 bug。
3. **不得引入第二个权重事实源**：扫描器的输出只能是终端打印或可选的报告文件（若要落盘，必须是独立命名的报告，例如 `META/parallel-domain-weight-status-report.md`，且需要在 STATUS.md 第 4 节"当前不可硬编码的信息"里检查是否需要补充"该报告内容属于易漂移状态，不得抄进 STATUS.md 正文"的提示——若该章节已有类似规则可复用，不必重复发明）。
4. **不得破坏既有 promotion 测试**：[`tests/test_promote_expert_weight_feedback.py`](../tests/test_promote_expert_weight_feedback.py) 与 [`tests/v1_3_acceptance/test_h3_feedback_parsing.py`](../tests/v1_3_acceptance/test_h3_feedback_parsing.py) 中 Phase 1 已经建立的 RED→GREEN 证据必须保持全绿，跑一遍确认无回归。
5. **CLI 风格必须对齐 `tools/rule_status_scan.py`**：`--format` 取值、`--check` 的退出码含义、markdown 输出的可读性风格，都应参照该文件的既有实现，不要另起一套约定。

---

## 5. 执行步骤建议（子任务拆分，允许在同一会话内顺序推进）

1. **RECOVER**：重新读取本文件第 0 节列出的全部文件，确认行号、函数签名与本文件描述一致；如有漂移，记录差异。额外确认 [`tools/rule_status_scan.py`](../tools/rule_status_scan.py) 中 `--check` 的具体 exit code 实现（读取文件下半部分尚未在本 kickoff 中摘录的代码）。
2. **RED（聚合器）**：写合成多 case 的 jsonl fixture 测试，断言跨行聚合正确，当前失败（函数不存在）。
3. **GREEN（聚合器）**：实现聚合函数与 `--format markdown|json` 输出。
4. **RED（staleness 判定）**：写 overlay-vs-日志聚合的 pending 判定测试，两种场景（该标记 / 不该标记）都要覆盖。
5. **GREEN（staleness 判定）**：实现判定逻辑与 `--check` exit code。
6. **对真实文件跑一次只读验证**：直接运行 `python tools/parallel_domain_weight_status_scan.py --format markdown`（不加任何 mock，读真实 `engine/logs/` 与真实 `engine/expert-weights.yaml`），确认它不崩溃、不报错、如实反映"当前 0 个 pending 项"（因为 Phase 1 交付时真实 overlay 为空）。把这次真实运行的输出摘录写入最终交付说明。
7. **文档收口**：登记 `tools/README.md`，拆分并更新 `STATUS.md` 第 6 节 P2 行，视情况更新 `META/project-state.json`。
8. **回归确认**：运行第 2 节列出的既有测试集合，确认全部通过、无新增失败。
9. **最终交付**：给出简短总结（新增/修改文件清单、RED→GREEN 证据、对真实文件的只读运行结果、STATUS.md 变更摘录、明确写出"主裁判路由与生产默认切换"仍未开始且需要独立授权与证明物）。

---

## 6. STOP 条件（出现任一即停止，不得自行绕过）

- 任务过程中发现"证明五派并行主流程已产出六大领域十五层判断证明物"看起来已经具备条件，因而想顺手把路由切过去——**这不属于本任务授权范围，必须停止并在交付说明中单独标注为需要用户/架构师显式决策的独立事项，不得自行推进**。
- 需要修改 `engine/f09/`、Task 9-P 专项文件、prospective-go 单案制品或任何生产默认路由以完成本任务。
- 需要执行任何 Git/GitHub 写操作才能"完成"任务（不需要；本任务范围内不涉及提交）。
- 现有测试基线本身在改动前就有非预期失败（区分是否是已知的历史 pre-existing 失败之外的新失败）。
- 真实 `engine/logs/*.jsonl` 或 `engine/expert-weights.yaml` 在执行过程中被本任务的任何代码意外写入或清空——必须立即停止，报告具体触发路径，不得静默修复后继续。

出现 STOP 条件时：保留已完成的证据，明确写出触发条件、已完成步骤和建议的下一动作，然后停止，不得强行绕过或臆造数据让测试通过。

---

## 7. 最终交付要求

完成后在同一会话内给出总结，必须包含：

1. 新增/修改文件的完整清单（含新工具路径）；
2. 每一步 TDD 循环的 RED→GREEN 证据（命令 + 关键输出，不需要贴全部日志，但要有失败原因和通过计数）；
3. 对真实 `engine/logs/` 与真实 `engine/expert-weights.yaml` 的只读运行结果摘录（证明扫描器在零样本真实环境下不崩溃、判定正确）；
4. `STATUS.md` 与（如有）`META/project-state.json` 的更新内容摘录；
5. 明确声明：本轮不涉及 Git/GitHub 操作，`LOCAL ONLY / NOT PUSHED`；
6. 明确声明本轮未覆盖、且**明确不属于本任务授权范围**的后续工作：五派并行主流程证明物的定义与产出、主裁判路由切换、`production_switch` 的任何变化——这些是独立的、更大范围的后续任务，需要用户或架构师显式立项与授权，不得由 Terra 在无人值守场景下自行推进。

不得在任一项证据缺失或未新鲜验证时声称任务完成。
