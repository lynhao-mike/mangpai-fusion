# 多专家功能域反馈闭环 Phase 3 · 工具索引漂移收口 + Phase 2 Evidence-Bounded Freeze · Terra 无人值守执行提示词

> 用途：复制本文件全文作为新会话的第一条用户消息，指导 ChatGPT 5.6 Terra（或等价 agent）无人值守完成本任务。目标是让整个任务在**一次对话**内闭环完成；允许拆分子任务（例如"分类两个未登记工具""补登记""重跑注册检查""补跑 Phase 2 最终 Gate""写收口报告"），但子任务只是执行顺序，不需要跨会话交接。

---

## 0. 背景：为什么会有本任务（先读，不得凭旧摘要推断）

1. [`plans/parallel-domain-feedback-loop-phase2-terra-kickoff-prompt.md`](parallel-domain-feedback-loop-phase2-terra-kickoff-prompt.md) 已执行完毕：新增只读扫描器 [`tools/parallel_domain_weight_status_scan.py`](../tools/parallel_domain_weight_status_scan.py)、synthetic fixture 测试 [`tests/test_parallel_domain_weight_status_scan.py`](../tests/test_parallel_domain_weight_status_scan.py)，并在 [`tools/README.md`](../tools/README.md)、[`STATUS.md`](../STATUS.md)、[`META/project-state.json`](../META/project-state.json) 完成限定收口。TDD 全绿，真实 `engine/logs/` 与 `engine/expert-weights.yaml` 只读运行结果为零样本、`pending_promotion_review_count=0`，退出码 0。
2. Phase 2 收尾时运行 `python tools/tool_registry.py --check`，返回**非零退出码**，输出：
   ```text
   tool registry check failed:
   - UNINDEXED tool exists but is absent from tools/README.md: as_of_integration.py
   - UNINDEXED tool exists but is absent from tools/README.md: production_as_of_cli.py
   ```
3. 经核对，[`tools/as_of_integration.py`](../tools/as_of_integration.py) 与 [`tools/production_as_of_cli.py`](../tools/production_as_of_cli.py) 是 **G8 / G9-P1（as-of life state）任务的历史交付物**，早于 Phase 2 会话已存在于仓库，只是从未被登记进 [`tools/README.md`](../tools/README.md)。这是 **pre-existing 基线漂移**，不是 Phase 2 新增代码造成的问题。Phase 2 依据本仓库 [`long-project-local-controller`](../.roo/skills/long-project-local-controller/SKILL.md) 治理规则中的 STOP 条件（"现有测试基线本身在改动前就有非预期失败"）正确停止，未越权顺手修复，也未把 Phase 2 工作声明为完整冻结。
4. 因此 Phase 2 停在：**4 组指定回归全绿**，但 **`tool_registry.py --check` 未过**，导致 Phase 2 最后两步（新鲜静态审查、evidence-bounded freeze）尚未执行。本任务（Phase 3）就是把这个漂移按正确的历史事实修复，并把 Phase 2 的收尾 Gate 补完。

不要从 handoff.md、旧 plans 摘要或本文件之外的复述推断当前实现状态；一切以下列文件的当前源码 / 当前登记表为准。

---

## 1. 任务目标（唯一长任务）

**在不触碰任何生产逻辑、不改写 as-of 相关模块内部行为的前提下，把两个 pre-existing 未登记工具按其真实历史定位补登记进 `tools/README.md`，使 `tools/tool_registry.py --check` 回到 PASS；然后为 Phase 2 交付的并行域权重状态扫描器补做被 STOP 阻断的最终 Gate（新鲜独立静态审查 + 证据复核 + evidence-bounded freeze），并输出一份收口报告。**

必须完成且可验证的三件事：

1. **正确分类并登记两个工具**：
   - 读取 [`plans/as-of-life-state-g8-production-integration-spec.md`](as-of-life-state-g8-production-integration-spec.md)（或仓库内实际存在的 G8 契约/报告文件，若文件名有漂移以实际存在文件为准）与 [`plans/as-of-life-state-g9-p1-production-cli-alias-contract.md`](as-of-life-state-g9-p1-production-cli-alias-contract.md)，确认这两个工具在设计上的真实定位：是否已切换为默认生产入口，还是仍为 staged / 对照验证入口。
   - 根据 [`tools/README.md`](../tools/README.md) 文件头的状态约定（active / internal / deprecated / historical / missing）以及 [`tools/tool_registry.py`](../tools/tool_registry.py) 的 `STATUS_HEADINGS` 定义，把 [`as_of_integration.py`](../tools/as_of_integration.py) 与 [`production_as_of_cli.py`](../tools/production_as_of_cli.py) 各自登记到**与其真实定位相符**的章节，并如实描述调用边界（例如：是否只被生产目录约定 CLI 消费、是否已被任何默认 pipeline 引用、是否仍是旁路证明入口）。
   - **禁止臆造更高完成度**：如果 G8/G9-P1 文档明确写着"未切换默认生产入口""staged"，登记文案必须保留这个限定，不得把它们写成看起来已经默认接入生产的入口。
2. **验证注册表回到 PASS**：
   ```bash
   python tools/tool_registry.py --format markdown
   python tools/tool_registry.py --check
   ```
   `--check` 必须返回 0，且不产生新的 unindexed / 漂移条目。
3. **补做 Phase 2 被阻断的最终 Gate**：
   - 对 [`tools/parallel_domain_weight_status_scan.py`](../tools/parallel_domain_weight_status_scan.py) 与 [`tests/test_parallel_domain_weight_status_scan.py`](../tests/test_parallel_domain_weight_status_scan.py) 执行一次**逻辑新鲜**的独立静态审查（重新以 fresh reviewer 视角读一遍源码与测试，不得直接采信 Phase 2 会话内的自我评估），确认：只读、无生产路由耦合、聚合口径与 pending 判定逻辑与 Phase 2 CONTRACT 描述一致。
   - 重跑 Phase 2 指定的完整回归集合一次（见下方第 5 节），连同新修复的 `tool_registry --check`，取得同一批次的新鲜证据。
   - 若全部证据满足 Phase 2 CONTRACT 的完成条件，给出：
     ```text
     PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE
     ```
     并明确写出"直接证明的范围"与"不得推断的范围"（例如：证明了扫描器在当前真实日志零样本下不崩溃且逻辑正确，未证明真实反馈样本积累后 pending 判定在大样本下的表现，因为真实样本目前仍是零）。
   - 若发现任何新问题（不止是登记表漂移），必须停止并报告，不得为了"显得已经完成"而略过。

---

## 2. 写集边界（严格遵守，超出即 STOP）

允许修改或新增：

- [`tools/README.md`](../tools/README.md)（仅新增/修正 [`as_of_integration.py`](../tools/as_of_integration.py) 与 [`production_as_of_cli.py`](../tools/production_as_of_cli.py) 的登记行，不得改动其他已有工具的登记内容）
- 新文件 `reports/parallel-domain-feedback-loop-phase3-registry-closure-report.md`（收口报告）
- 若在核对 G8/G9-P1 文档时发现这两个工具此前确实"计划登记但遗漏"，可在对应历史 plans/reports 文件**追加**一行"已于 Phase 3 补登记"式的只读追溯说明（**不得**改写这些文件中已冻结的第 1-8 节或类似正文结构）

不允许修改：

- [`tools/as_of_integration.py`](../tools/as_of_integration.py)、[`tools/production_as_of_cli.py`](../tools/production_as_of_cli.py) 的任何逻辑、签名、默认值
- [`engine/asof/`](../engine/asof/) 下任何文件
- [`tools/parallel_domain_weight_status_scan.py`](../tools/parallel_domain_weight_status_scan.py)、[`tests/test_parallel_domain_weight_status_scan.py`](../tests/test_parallel_domain_weight_status_scan.py) 的行为逻辑（Gate 3 只做审查与验证，不得顺手"优化"或重构）
- [`engine/application/pipeline_runner.py`](../engine/application/pipeline_runner.py)、[`engine/application/dual_engine_adapter.py`](../engine/application/dual_engine_adapter.py)、[`engine/application/parallel_domain_orchestrator.py`](../engine/application/parallel_domain_orchestrator.py)、[`engine/application/adjudication.py`](../engine/application/adjudication.py)
- [`engine/expert-weights.yaml`](../engine/expert-weights.yaml)、[`engine/domain-weights.yaml`](../engine/domain-weights.yaml)
- 任何 `production_switch` 相关字段或语义
- 真实 `engine/logs/*.jsonl`（本任务不涉及反馈摄入，不得写入或清空）
- 任何 G0-G10、Task 9-P、F09、prospective-go 专项冻结文档的第 1-8 节 / 正文结构
- 不得执行任何 Git 或 GitHub 写操作（本地 `git status` / `git diff` 只读查看不受限；禁止 commit / push / PR 等任何写操作，除非用户在后续消息中另行明确授权）

---

## 3. 关键设计约束（防止走偏）

1. **登记不是重新设计**：本任务只做"如实描述现状"的文档登记，不得借机重新讨论 as-of 生命周期任务是否该切换默认生产入口——那是 G8/G9-P1/G10 系列的范围，本任务不得扩权触碰。
2. **不得把 pending Gate 强行判定为 PASS**：如果重新独立审查发现 Phase 2 扫描器存在此前未察觉的逻辑缺陷（哪怕很小），必须先修（在 Phase 2 原写集范围内）、重新走 RED→GREEN，再进入 freeze；不得带着已知缺陷宣称 freeze。
3. **fresh review 必须真正"新鲜"**：审查者视角要显式重置——重新读一遍 [`tools/parallel_domain_weight_status_scan.py`](../tools/parallel_domain_weight_status_scan.py) 全文与 [`tests/test_parallel_domain_weight_status_scan.py`](../tests/test_parallel_domain_weight_status_scan.py) 全文，逐条对照 Phase 2 kickoff 提示词第 1、4 节的约束，而不是直接照抄 Phase 2 会话总结当作审查结论。
4. **CLI 风格与调用边界一致性**：登记文案应参照 [`tools/README.md`](../tools/README.md) 中其它 as-of 相关或历史工具的现有措辞风格，不发明新的状态词。

---

## 4. 执行步骤建议（子任务拆分，允许在同一会话内顺序推进）

1. **RECOVER**：重新读取 [`tools/README.md`](../tools/README.md) 当前登记表全文、[`tools/tool_registry.py`](../tools/tool_registry.py) 的状态定义与 `--check` 逻辑、[`tools/as_of_integration.py`](../tools/as_of_integration.py) 与 [`tools/production_as_of_cli.py`](../tools/production_as_of_cli.py) 全文 docstring、以及仓库内实际存在的 G8/G9-P1 相关 plans 文件（先用文件列表确认真实文件名，不假设本文件第 0 节引用的路径一定精确无漂移）。
2. **分类判定**：基于 G8/G9-P1 文档的真实措辞，判定两个工具应登记为 active（若已有独立可运行的对照入口定位）还是 historical/internal（若仍是纯 staged 证明物）；记录判定依据的原文引用。
3. **登记修改**：在 [`tools/README.md`](../tools/README.md) 对应章节插入两行登记，措辞包含真实调用边界（是否被 `production_service.py` 或任何默认 pipeline 引用——需要实际 grep 确认，不得凭猜测）。
4. **验证注册表**：
   ```bash
   python tools/tool_registry.py --format markdown
   python tools/tool_registry.py --check
   ```
   确认 `--check` 返回 0。
5. **fresh 静态审查**：按第 1 节第 3 点重新审查 Phase 2 扫描器与测试。
6. **重跑 Phase 2 回归集合**（与 Phase 2 kickoff 提示词第 2 节一致，新增本次修复的注册检查）：
   ```bash
   python -m pytest tests/test_parallel_domain_weight_status_scan.py -q
   python -m pytest tests/v1_3_acceptance -q
   python -m pytest tests/test_promote_expert_weight_feedback.py -q
   python -m pytest tests/test_project_metadata.py -q
   python tools/tool_registry.py --check
   ```
7. **真实只读复核**（新鲜重跑，不复用 Phase 2 会话里的旧输出）：
   ```bash
   python tools/parallel_domain_weight_status_scan.py --format markdown
   python tools/parallel_domain_weight_status_scan.py --format json
   python tools/parallel_domain_weight_status_scan.py --check
   ```
8. **写收口报告** `reports/parallel-domain-feedback-loop-phase3-registry-closure-report.md`，包含：注册表漂移的根因说明与登记依据引用、Gate 4-7 的新鲜命令与关键输出、最终 freeze 判定与"直接证明 / 不得推断"边界。
9. **最终交付**：给出简短总结（修改/新增文件清单、注册表 PASS 证据、fresh review 结论、回归全绿证据、freeze 判定、明确声明 as-of 生产路由与主裁判路由切换均仍未开始且不属于本任务范围）。

---

## 5. STOP 条件（出现任一即停止，不得自行绕过）

- 判定两个工具的真实定位时发现 G8/G9-P1 文档本身存在冲突或缺失，无法确定其应登记为哪个状态——必须停止并列出冲突点，请求人工裁决，不得自行选一个"看起来对"的状态。
- fresh 审查发现 Phase 2 扫描器存在此前未察觉的逻辑缺陷、写集越界或与 CONTRACT 不符——必须停止、如实记录缺陷，不得静默修复后继续声称"本轮无问题"。
- 重跑回归集合出现任何 Phase 2 报告中没有记录过的新失败——必须停止并分类（产品缺陷 / 测试缺陷 / 环境问题），不得强行让测试通过。
- 需要修改 [`tools/as_of_integration.py`](../tools/as_of_integration.py)、[`tools/production_as_of_cli.py`](../tools/production_as_of_cli.py) 或 [`engine/asof/`](../engine/asof/) 的任何逻辑才能让 `--check` 通过——说明问题不是单纯登记漂移，必须停止并报告，不得越权改动这些冻结模块。
- 需要执行任何 Git/GitHub 写操作才能"完成"任务（不需要；本任务范围内不涉及提交）。
- 真实 `engine/logs/*.jsonl` 或 `engine/expert-weights.yaml` 在执行过程中被本任务的任何代码意外写入或清空——必须立即停止，报告具体触发路径，不得静默修复后继续。

出现 STOP 条件时：保留已完成的证据，明确写出触发条件、已完成步骤和建议的下一动作，然后停止，不得强行绕过或臆造数据让判定通过。

---

## 6. 最终交付要求

完成后在同一会话内给出总结，必须包含：

1. 新增/修改文件的完整清单（含收口报告路径）；
2. 两个工具的分类判定依据（引用 G8/G9-P1 文档原文或实际 grep 结果，不得凭空断言）；
3. `tool_registry.py --check` 修复前后的对比（修复前非零 exit code + 具体报错，修复后 0）；
4. fresh 静态审查的具体结论（逐条对照 Phase 2 CONTRACT 约束，不是笼统"看起来没问题"）；
5. 重跑回归集合的新鲜通过计数（不复用旧数字）；
6. 最终 freeze 判定：`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE` 或明确说明为何仍不能 freeze；若 PASS，必须写清"直接证明的范围"与"不得推断的范围"；
7. 明确声明：本轮不涉及 Git/GitHub 操作，`LOCAL ONLY / NOT PUSHED`；
8. 明确声明本轮未覆盖、且**明确不属于本任务授权范围**的后续工作：as-of 生命周期任务是否切换默认生产入口（G8/G9-P1/G10 系列范围）、多专家功能域裁判的主裁判路由切换、`production_switch` 的任何变化——这些仍需用户或架构师显式立项与授权。

不得在任一项证据缺失或未新鲜验证时声称任务完成。
