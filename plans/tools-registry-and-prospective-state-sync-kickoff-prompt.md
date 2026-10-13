# 工具索引登记 + prospective 首案状态同步 · 无人值守执行提示词

> 本文件只交付一份可直接粘贴给 ChatGPT 5.6 Terra（或等价 agent）的执行提示词；不在本文件内实施该任务。
>
> 来源：2026-07-28 阶段 A 本地仓库调研发现两处纯文档漂移，均已交叉核验实际制品/运行时输出确认为漂移而非缺陷，本任务只做同步登记，不涉及任何业务逻辑或代码变更。

## 使用说明

- 直接把"提示词正文"整段粘贴给 Terra 作为单次会话的完整任务说明。
- 提示词内已包含所有必要事实源路径、已核实结论和验证命令；Terra 不需要重新调研即可开始执行。
- 两个子任务互相独立，可在同一会话内顺序完成，不需要分别授权。

---

## 提示词正文

```text
你正在 mangpai-fusion 仓库执行一个小范围文档同步任务：修复两处已核实的纯文档漂移。这不是实现任务，不涉及任何 engine/ 或 tools/ 下已有工具的逻辑变更，只更新两个 Markdown/JSON 状态文件。

## 背景（已核实，无需重新调查）

### 漂移一：`META/project-state.json` 的 prospective 首案状态落后于实际制品

`META/project-state.json` 的 `single_case_prospective_status` 字段（约第 69-81 行）当前写着：

```json
"immediate_retrospective": "not_completed",
"future_observation": "not_completed"
```

但实际磁盘制品已经存在：

- `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--immediate-retrospective-unbound--v001.json`
- `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--immediate-retrospective-bound--v001.json`
- `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--case-completion--v001.json`

这三份制品已交叉核验：`case-completion` 制品的 `retrospective_completion_status` 字段值为 `"CASE_COMPLETE_FOR_RETROSPECTIVE"`，`future_completion_status` 字段值为 `"PENDING"`。`immediate-retrospective-bound` 制品的四条 facts 均为 `"classification": "no_data"`、`"scorable": false`，`scorable_label_count` 为 0——这是合法的"无可评分标签"结果，不是缺陷。

`future_observation` 保持 `"not_completed"`（或更准确的等价措辞）是**合法的**，因为观察窗口（`observation_window.end_at`）为 `2026-10-17T08:04:23.949068Z`，尚未到期，不得在窗口结束前伪造完成状态。

### 漂移二：两个工具未登记进 `tools/README.md`

运行 `python tools/tool_registry.py --check` 当前返回 exit code 1，精确输出：

```
tool registry check failed:
- UNINDEXED tool exists but is absent from tools/README.md: archive_verified_artifact.py
- UNINDEXED tool exists but is absent from tools/README.md: as_of_session_cli.py
```

`archive_verified_artifact.py`（[`tools/archive_verified_artifact.py`](../tools/archive_verified_artifact.py)）是单用途 verified artifact 归档 CLI，docstring 为"单用途 verified artifact 归档 CLI。"，委托 `engine.archive.archive_verified_artifact()`，接受 `SOURCE --archive-root ARCHIVE_ROOT` 两个参数，是通用归档入口，不专属 as-of。

`as_of_session_cli.py`（[`tools/as_of_session_cli.py`](../tools/as_of_session_cli.py)）是"历史/手动 as-of 事业会话旁路；手动 opt-in，不切换任何生产默认入口。"，公开 `run_and_archive_session()` 与 CLI `main()`，语义上与 `tools/README.md` 现有 historical 章节的 [`as_of_integration.py`](../tools/as_of_integration.py) 属于同一类"手动旁路证明入口"。

## 唯一目标

1. 更新 `META/project-state.json` 的 `single_case_prospective_status`：把 `immediate_retrospective` 从 `"not_completed"` 改为准确反映已有制品的状态（如 `"landed"`，需与该字段其余取值的措辞风格一致，即 `intake`/`future_question_registration`/`blind_bundle`/`immutable_frozen_result` 均使用的过去分词式简短状态词）；`future_observation` 保持表示"仍在等待窗口到期"的状态，不得改写为完成。
2. 在 `tools/README.md` 中为 `archive_verified_artifact.py` 和 `as_of_session_cli.py` 各新增一行登记，登记到与其真实定位相符的章节（`active`/`internal`/`historical` 三选一，禁止臆造更高完成度），使 `python tools/tool_registry.py --check` 从失败变为通过。

## 硬边界（不可协商）

- 只允许修改两个文件：`META/project-state.json`、`tools/README.md`。
- 禁止修改 `tools/archive_verified_artifact.py`、`tools/as_of_session_cli.py`、`tools/tool_registry.py`、`engine/asof/` 或 `engine/archive.py` 的任何逻辑。
- 禁止修改 `META/prospective-go/` 下任何制品文件。
- 禁止执行任何 Git 或 GitHub 操作（本地与远端均不可）。
- 更新 `immediate_retrospective` 前，必须先亲自读取上述三份制品的实际内容，确认字段值与本提示词描述一致；若发现实际内容与本提示词描述不符，停止并如实报告差异，不得强行按本提示词结论改写。
- 不得把 `future_observation` 提前标记为完成，也不得删除或修改观察窗口时间字段。

## 执行流程

### 步骤 1：核实制品（只读）

1. 依次读取本提示词列出的三份 prospective 制品全文，确认：
   - `case-completion` 制品的 `retrospective_completion_status` 与 `future_completion_status` 实际取值；
   - `immediate-retrospective-bound` 制品的 `scorable_label_count` 与四条 facts 的 `classification`/`scorable` 字段；
   - 对应 `future-question-registration` 制品（`META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--future-question-registration--v004.json`）的 `observation_window.end_at`，并与当前真实日期比较，确认窗口是否已到期。
2. 若三份制品的实际内容与本提示词第一节描述不一致，立即停止，如实报告差异，不进入步骤 2。

### 步骤 2：同步 `META/project-state.json`

1. 只修改 `single_case_prospective_status.immediate_retrospective` 的值，改为与该对象内其余字段（`intake`/`future_question_registration`/`blind_bundle`/`immutable_frozen_result`）措辞风格一致的"已完成"状态词。
2. `future_observation` 字段维持表达"未到期/待观察"语义，若原词汇准确则不修改，否则替换为更准确但同样表达"待完成"的词，不得改为完成态。
3. 不修改该 JSON 文件的任何其他字段。

### 步骤 3：登记两个工具

1. 参照 `tools/README.md` 现有各章节的表格格式（工具名链接、用途、调用边界三列），为 `archive_verified_artifact.py` 新增一行；根据其"通用单用途归档 CLI，委托 `engine.archive`"的定位判断应归入 `active` 还是 `internal`（参考同类归档类工具在该文件中的既有归类惯例）。
2. 为 `as_of_session_cli.py` 新增一行，归入 `historical` 章节（与 `as_of_integration.py` 同类，因为它同样是"手动旁路证明入口，未接入默认生产入口"）。
3. 不修改该文件内任何其他既有工具的登记行。

### 步骤 4：验证

运行并记录真实输出与 exit code：

```
python tools/tool_registry.py --check
python tools/rule_status_scan.py --check
```

前者预期从失败变为 `tool registry check passed`、exit code 0；后者预期保持原有通过状态，不因本次改动受影响。

## STOP 条件（命中任一立即停止并汇报，不得继续推进）

- 三份制品实际内容与本提示词描述不一致；
- `tools/tool_registry.py --check` 修复后仍失败，且原因不是登记措辞问题（例如发现该脚本还有其他未预料的校验逻辑）；
- 需要修改本提示词硬边界之外的任何文件才能完成任务；
- 无法确定 `future_observation` 的准确当前语义（例如窗口是否已经到期存在歧义）。

## 完成后的汇报格式

最终回复必须包含：三份制品的实际关键字段核实结果、`META/project-state.json` 修改前后的字段对比、`tools/README.md` 新增两行的实际内容、两条验证命令的真实输出与 exit code。不得省略任何一项，也不得用推测替代真实文件内容或命令输出。
```

---

## 交付边界

本文件本身不实施上述任务，只交付这份提示词与使用说明。
