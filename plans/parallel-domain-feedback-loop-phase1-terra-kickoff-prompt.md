# 多专家功能域裁判反馈闭环 Phase 1 · Terra 无人值守执行提示词

> 用途：复制本文件全文作为新会话的第一条用户消息，指导 ChatGPT 5.6 Terra（或等价 agent）无人值守完成本任务。目标是让整个任务在**一次对话**内闭环完成；允许拆分子任务（例如"接线 fanout"“写 promotion 工具”“补测试”“更新状态文档"），但子任务只是执行顺序，不需要跨会话交接。

---

## 0. 背景与真实事实源（先读，不得凭旧摘要推断）

1. [`AGENTS.md`](../AGENTS.md) —— 仓库 AI 调用规则，事实源矩阵与最小上下文原则。
2. [`STATUS.md`](../STATUS.md) 第 6 节路线表中 P2 项：
   > 将多专家功能域裁判从旁路升级为反馈可动态调权的主裁判层 —— [`engine/application/parallel_domain_orchestrator.py`](../engine/application/parallel_domain_orchestrator.py)、[`tests/test_parallel_domain_orchestrator.py`](../tests/test_parallel_domain_orchestrator.py)
3. [`META/project-state.json`](../META/project-state.json) 中：
   ```json
   "dynamic_feedback_weighting": "landed_proposal_confirmed_overlay"
   ```
   这个状态目前**不准确**：`feedback_overlay` 机制本身已实现（`engine/domain/weighting.py` 的 `FeedbackOverlay`），但从真实案例反馈到该 overlay 之间的链路没有接通。本任务完成后必须重新核实并如实更正这个字段。
4. 核心代码事实（已核实，请重新读取源码确认，不要相信本段复述）：
   - [`tools/feedback_ingest.py`](../tools/feedback_ingest.py) 中 `fanout_to_parallel_feedback()`（约第 383 行）把 statement-level 反馈写入 `expert_domain_feedback.jsonl` 与 `adjudication_accuracy.jsonl`；`get_expert_domain_stats()`（约第 446 行）聚合成 Beta/Wilson 统计；`compute_weight_update_proposal()`（约第 471 行）从统计生成调权提案，明确标注 `requires_human_review: True`，且函数注释写着"不自动写入任何 YAML"。
   - 但 `ingest()` 主流程（约第 980 行）目前是：
     ```python
     with timing.step("fanout"):
         rule_verdicts, unknown_sids = fanout_to_rules(feedbacks, statement_records)
         parallel_feedback_counts = {"expert_feedback_rows": 0, "adjudication_feedback_rows": 0}
     ```
     `fanout_to_parallel_feedback()` 根本没有被调用；`parallel_feedback_counts` 是死代码硬编码的全零占位符。
   - [`engine/expert-weights.yaml`](../engine/expert-weights.yaml) 的 `feedback_overlay.entries` 永远是 `[]`；`FeedbackOverlay.entries_for()` 在无 entry 时 `modulation_for()` 恒返回 `1.0`（见 [`engine/domain/weighting.py`](../engine/domain/weighting.py) 第 125-142 行），即裁判权重从未真正被反馈调整过。
   - 已存在的单测 [`tests/v1_3_acceptance/test_h3_feedback_parsing.py`](../tests/v1_3_acceptance/test_h3_feedback_parsing.py) 的 `test_h3_parallel_feedback_fanout_stats_and_weight_proposal` 直接调用 `fanout_to_parallel_feedback()`，绕过了 `ingest()` 主流程，所以现有测试不会暴露"主流程未接线"这个缺口。
   - [`tests/test_parallel_domain_models.py`](../tests/test_parallel_domain_models.py) 已经证明 `WeightProfileService` / `build_weight_profile()` 能正确消费一个手工构造的 `feedback_overlay`；缺的只是"如何从真实反馈生成这个 overlay 并写回 YAML"这一段。

不要从 `handoff.md`、旧 plans 文档或本文件之外的任何摘要推断当前实现状态；一切以上述文件的当前源码为准。若发现本节描述与实际源码不一致（例如行号漂移、函数已被改名），以实际源码为准，并在最终交付说明中记录差异。

---

## 1. 任务目标（唯一长任务）

**把"statement 反馈 → expert/domain 统计 → 调权提案 → 人工确认 → 写回 `engine/expert-weights.yaml`"这条链路真正接通，且全程可追溯、可回滚、不破坏现有生产默认行为。**

必须完成且可验证的三件事：

1. **接线 fanout**：`tools/feedback_ingest.ingest()` 的主流程必须真正调用 `fanout_to_parallel_feedback()`，用真实的 `statement_index.json`（或等价可用的 statement 元数据来源）驱动，而不是硬编码 `{0, 0}`。
2. **新增 promotion 工具**：一个新的、独立的、`create-only`/显式版本递增的工具（建议 `tools/promote_expert_weight_feedback.py`），把 `compute_weight_update_proposal()` 的提案转成 `engine/expert-weights.yaml` 的 `feedback_overlay` 段落，且：
   - 默认 `--dry-run`，只打印将要写入的 diff，不动文件；
   - 正式写入前必须要求显式 `--reviewed-by <人类姓名>` 或等价参数，且写入后的 `feedback_overlay.status`（或等价字段）必须标注为已人工确认，不能是自动状态；
   - 不允许静默覆盖已存在的 `feedback_overlay.version`；每次 promotion 必须生成新的、单调的 `version` 标识；
   - 保留原 profile 与新 profile 的可读 diff（终端输出即可，不强制落盘新文件，除非你认为落盘更符合仓库既有审计习惯——若落盘，必须新建文件，不得覆盖 `engine/expert-weights.yaml` 本身之外再造一份竞争事实源）。
3. **端到端回归测试**：新增至少一个测试，证明"真实 case 的 feedback.md → ingest() → expert_domain_feedback.jsonl 有新行 → compute_weight_update_proposal 产出提案 → promotion 工具 dry-run 展示 diff → 正式执行后 engine/expert-weights.yaml 的 feedback_overlay 实际变化 → WeightProfileService 用新 overlay 算出的权重确实偏离默认先验"，形成完整证据链，而不是分段验证。

---

## 2. 强制使用 TDD（本仓库标准要求）

对每一个非平凡行为改动，先写失败测试，观察其为预期原因失败，再写最小实现代码使其通过，然后重构。具体到本任务：

1. 先写一个测试证明当前 `ingest()` 不会产生 `expert_feedback_rows > 0`（即锁定当前的缺陷行为，RED）。
2. 实现接线后重跑该测试，确认变绿（GREEN）。
3. 为 promotion 工具的 dry-run / 正式写入 / 拒绝覆盖既有 version 分别写测试，遵循同样的 RED → GREEN 循环。
4. 每次 GREEN 后运行相关测试文件确认无回归，最后运行一次更大范围的相关测试集合（不要求也不建议在本任务内跑全仓 `pytest -q`，除非你认为有必要且时间可控——全仓约 20 分钟）。

---

## 3. 允许修改的文件范围（写集边界）

允许修改或新增：

- [`tools/feedback_ingest.py`](../tools/feedback_ingest.py)（接线 fanout 到主流程）
- 新文件 `tools/promote_expert_weight_feedback.py`（promotion 工具）
- [`engine/expert-weights.yaml`](../engine/expert-weights.yaml)（仅通过 promotion 工具的正式执行路径写入，不得手工编辑跳过工具）
- 新增/修改测试文件，例如 `tests/v1_3_acceptance/test_h3_feedback_parsing.py`、新建 `tests/tools/test_promote_expert_weight_feedback.py`（若 `tests/tools/` 不存在，检查现有测试目录习惯，放到合适位置，例如根 `tests/`）
- [`STATUS.md`](../STATUS.md) 第 6 节该 P2 行的状态描述（如任务完成，更新为已落地或部分落地，并写清剩余缺口）
- [`META/project-state.json`](../META/project-state.json) 中 `dynamic_feedback_weighting` 字段（按实际完成情况如实更正，不得写"landed"如果只是部分落地）
- 若需要，`tools/README.md` 补充新工具的索引条目（仓库要求"唯一工具索引"，新增可执行工具必须登记）

不允许修改：

- 任何 `engine/f09/`、`tests/f09/`、Task 9-P 相关九份专项冻结文件（与本任务无关，禁止触碰）
- 任何 prospective-go 单案制品（与本任务无关）
- 任何生产默认路由、`production_switch`、`engine/domain-weights.yaml`（legacy four-school matrix，与本任务的 `engine/expert-weights.yaml` 是不同事实源，不得混淆或迁移）
- 不得执行任何 Git 或 GitHub 操作（本地 `git status`/`git diff` 只读查看不受限，但禁止 commit/push/PR 等任何写操作，除非用户在后续消息中另行明确授权）

---

## 4. 关键设计约束（防止走偏）

1. **不得引入静默默认权重变化**：接线 fanout 之后，只要 promotion 工具没有被人正式执行过，`engine/expert-weights.yaml` 的行为必须与接线前完全一致（`modulation_for()` 恒为 1.0）。这是回归测试的核心断言之一。
2. **人工确认是硬门**：promotion 工具正式写入必须要求某种不可省略的人工确认信号（参数、环境变量或交互式确认均可，但不能是"默认自动 yes"）。这是仓库既有 `compute_weight_update_proposal()` docstring 明确写的"不自动写入"精神的延续，不得违反。
3. **不得伪造 n_eff 或反馈计数**：不要为了让测试通过而构造假的高样本量反馈；测试 fixture 中的样本量应该真实反映"低样本保守策略"（仓库已有 `min_effective_sample_for_adjustment` 概念），并验证低样本时 `low_sample_max_delta` 生效、不会因为一两条反馈就把权重猛拉。
4. **不得破坏现有 91 项通过的相关测试**：至少要重跑 `tests/v1_3_acceptance/`、`tests/test_parallel_domain_models.py`、`tests/test_parallel_domain_orchestrator.py`、`tests/evaluation/`（若涉及）确认无回归。命令示例（Windows cmd.exe，工作目录为仓库根目录）：
   ```bash
   python -m pytest tests/v1_3_acceptance -q
   python -m pytest tests/test_parallel_domain_models.py tests/test_parallel_domain_orchestrator.py -q
   ```
5. **statement_index 来源的现实性**：`fanout_to_parallel_feedback()` 需要的 `statement_index` 结构（含 `parallel_domain_adjudication` / `parallel_domain_reading` 相关字段）目前由 [`tools/render_report.py`](../tools/render_report.py) 的 `_build_statement_index()`（约第 1779 行）生成并落盘为 `cases/<case_id>/statement_index.json`。接线时必须让 `ingest()` 读取这份真实落盘文件（若存在），而不是重新发明一套输入格式。如果某个 case 目录下没有 `parallel_domain_adjudication` 相关 statement（例如老案例、或未接线并行域分析的案例），fanout 结果应为 `{0, 0}`，这是正确行为，不是 bug——测试时务必构造一个**确实含有并行域 statement** 的 case fixture，否则无法证明接线生效。

---

## 5. 执行步骤建议（子任务拆分，允许在同一会话内顺序推进）

1. **RECOVER**：重新读取本文件第 0 节列出的全部文件，确认行号、函数签名与本文件描述一致；如有漂移，记录差异。
2. **RED（fanout 接线）**：写一个使用真实/接近真实 case fixture（含 `statement_index.json` 里的 `parallel_domain_adjudication` 段）的测试，调用 `ingest()`，断言 `expert_domain_feedback.jsonl` 产生了新行，或 `IngestResult`/`diff.notes` 中包含非零的 parallel feedback 计数。确认它当前失败（因为硬编码 `{0,0}`）。
3. **GREEN（fanout 接线）**：修改 `ingest()`，读取该 case 的 statement 元数据（复用已有 `_statement_map`/`statement_records` 或读取落盘的 `statement_index.json`，视哪个更贴合现有调用链），调用 `fanout_to_parallel_feedback()`，把返回的真实计数赋给 `parallel_feedback_counts`。重跑测试确认通过。
4. **RED（promotion 工具骨架）**：为新工具写测试：dry-run 不写文件、正式模式缺少人工确认参数时报错拒绝、正式模式带确认参数时正确修改 `feedback_overlay`、且 version 单调递增、且不会重复写同一个 version。
5. **GREEN（promotion 工具实现）**：实现 `tools/promote_expert_weight_feedback.py`，读取 `get_expert_domain_stats()` / `compute_weight_update_proposal()` 的结果（可通过导入函数或调用其 CLI，视现有 CLI 结构决定），生成新的 `feedback_overlay` 字典，用现有 YAML 读写工具（检查仓库是否已有 `_write` 风格的 create-only/safe write helper 可复用，例如 `tools/school_capability_dataset.py` 里的 `_write()`，评估是否适合搬到 `engine/expert-weights.yaml` 场景；若不适合，写一个局部安全写函数即可，不必求全局统一）落盘。
6. **端到端回归测试**：串联 3、5 的产物，写一个覆盖"before promotion 权重==默认先验，after promotion 权重发生预期方向的偏移"的测试。
7. **回归确认**：运行第 4 节列出的既有测试集合，确认全部通过、无新增失败。
8. **文档收口**：更新 `STATUS.md` 的 P2 行与 `META/project-state.json` 的 `dynamic_feedback_weighting` 字段为准确状态；若新增了 `tools/promote_expert_weight_feedback.py`，检查 `tools/README.md` 是否要求登记，若要求则登记。
9. **最终交付**：给出简短总结（新增/修改文件清单、测试证据即命令与通过计数、明确写出本轮未覆盖或延后的部分，例如"跨案例聚合的 N_eff 阈值调优""是否要接入 `tools/rule_status_scan.py` 一类的可观测面板"等，留给 Phase 2）。

---

## 6. STOP 条件（出现任一即停止，不得自行绕过）

- 发现 `statement_index.json` 的真实 schema 与本文件第 4 节第 5 点描述不一致，且无法确定正确的读取方式；
- 需要修改 `engine/f09/`、Task 9-P 专项文件、prospective-go 单案制品或任何生产默认路由以完成本任务；
- 需要执行任何 Git/GitHub 写操作才能"完成"任务（不需要；本任务范围内不涉及提交）；
- 现有测试基线本身在改动前就有非预期失败（区分是否是已知的两个历史 pre-existing sanity 失败之外的新失败）；
- 无法在不静默改变生产默认行为（`modulation_for()` 在无 promotion 时必须仍为 1.0）的前提下完成接线。

出现 STOP 条件时：保留已完成的证据，明确写出触发条件、已完成步骤和建议的下一动作，然后停止，不得强行绕过或臆造数据让测试通过。

---

## 7. 最终交付要求

完成后在同一会话内给出总结，必须包含：

1. 新增/修改文件的完整清单（含新工具路径）；
2. 每一步 TDD 循环的 RED→GREEN 证据（命令 + 关键输出，不需要贴全部日志，但要有失败原因和通过计数）；
3. 端到端证据链的最终验证结果（权重确实从默认先验偏移的具体数字对比）；
4. `STATUS.md` 与 `META/project-state.json` 的更新内容摘录；
5. 明确声明：本轮不涉及 Git/GitHub 操作，`LOCAL ONLY / NOT PUSHED`；
6. 明确声明本轮未覆盖的后续工作（Phase 2 候选，例如跨案例 N_eff 汇总面板、是否需要把 promotion 纳入 `tools/rule_status_scan.py` 一类的常规扫描）。

不得在任一项证据缺失或未新鲜验证时声称任务完成。
