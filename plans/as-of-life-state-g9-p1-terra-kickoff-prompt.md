# G9-P1 · as-of 生产 CLI 别名 · Terra 无人值守执行提示词

> 用途：复制本文件全文作为新会话的第一条用户消息，指导 ChatGPT 5.6 Terra（或等价 agent）无人值守完成 G9-P1-B/C/D。
> 前置：G9-P1-A（CONTRACT）已完成逻辑新鲜独立复核，verdict `PASS`。本提示词不重开 CONTRACT。

---

你正在 mangpai-fusion 仓库执行长任务 **G9-P1：as-of 生产 CLI 别名**。全程无人值守，允许你把任务拆成小步骤逐个完成小目标，但必须在同一个会话内做完 G9-P1-B、G9-P1-C、G9-P1-D 三个 Gate，不等待中途确认，除非触及下方 STOP 条件。

## 0. 强制先读顺序

1. [`AGENTS.md`](../AGENTS.md) —— 仓库 AI 调用规则。
2. [`plans/as-of-life-state-g9-production-promotion-scope-adjudication.md`](as-of-life-state-g9-production-promotion-scope-adjudication.md) —— G9 范围裁决，确认当前选定方案是 P1（保守），且 P2/P3 未被选中、不得越权实现。
3. [`plans/as-of-life-state-g9-p1-production-cli-alias-contract.md`](as-of-life-state-g9-p1-production-cli-alias-contract.md) 全文 —— **唯一冻结合同**。第 2 节写集、第 3 节依赖方向、第 4 节精确行为规格、第 5 节 failure ledger、第 6 节测试选择器、第 7 节 Gate 顺序、第 8 节 CONTRACT PASS 记录，逐条硬性执行，不得自行简化或重新解释。
4. [`tools/as_of_integration.py`](../tools/as_of_integration.py) 全文 —— 被委托的既有薄层，只读参考，不得修改。
5. [`engine/application/production_service.py`](../engine/application/production_service.py) 第 54-75 行 `ProductionAnalysisService.__init__`/`workspace_root` —— 确认默认目录约定，只读参考，不得修改。

不要从其他历史 G0-G8 kickoff 提示词、handoff.md 或旧摘要推断本任务的写集或行为规格；一切以第 3 项合同原文为准。

## 1. 唯一写入白名单（逐字节复制自合同第 2 节）

1. `plans/as-of-life-state-g9-p1-production-cli-alias-contract.md`（只允许在 G9-P1-D 报告完成后按需补记复核结果，不得改写第 1-8 节冻结内容）
2. `tests/asof/test_g9_production_cli_alias.py`
3. `tools/production_as_of_cli.py`
4. `reports/as-of-life-state-g9-p1-production-cli-alias-report.md`

超出以上四个路径的任何修改均为越权，必须立即 STOP。

## 2. 明确禁止修改

- `tools/as_of_integration.py`（含其内部逻辑、默认值、签名）；
- `engine/asof/` 下任何文件；
- `engine/application/production_service.py`、`tools/production_api.py`；
- 既有 `tests/asof/` 下任何既有测试文件；
- G0-G8 全部冻结文档与报告；
- 案例原文、其他任何未在白名单内的路径。

## 3. Gate 顺序与完成条件

### G9-P1-B：TDD RED

1. 创建 [`tests/asof/test_g9_production_cli_alias.py`](../tests/asof/test_g9_production_cli_alias.py)，覆盖合同第 6 节列出的至少 5 类场景（默认目录解析、显式目录透传、成对校验退出码、端到端逐字节一致、静态导入边界检查）。
2. 运行：

```text
python -m pytest tests/asof/test_g9_production_cli_alias.py -q
```

3. 完成条件：因 `tools.production_as_of_cli` 模块不存在而产生的**行为阶段** RED（pytest 完成收集，非 collection error）。记录精确 failed 数、exit code。
4. 若测试 helper 本身有缺陷（如导入路径写错），可在同一 Gate 内修订测试并重新确认 RED 仍因目标模块缺失产生，不得因 helper 缺陷跳过 RED 门禁。

### G9-P1-C：实现 + 验证证据

1. 创建 [`tools/production_as_of_cli.py`](../tools/production_as_of_cli.py)，严格按合同第 4 节实现：CLI 参数与 [`tools.as_of_integration._parser()`](../tools/as_of_integration.py:316) 一致；默认目录解析为唯一行为差异；其余逻辑全部委托 [`tools.as_of_integration`](../tools/as_of_integration.py) 的既有 public 函数，不重新实现第二份拷贝。
2. 依次运行并记录 passed/failed/skipped、exit code：

```text
python -m pytest tests/asof/test_g9_production_cli_alias.py -q
python -m pytest tests/asof -q
python -m pytest tests/asof/test_production_isolation.py -q
git diff -- engine/asof
git diff -- tools/as_of_integration.py
python -m pytest -q
```

3. 完成条件：
   - 专用测试全部 passed；
   - `tests/asof -q` 零新增失败（与 G8 报告记录的既有基线一致：允许既有 1 skipped）；
   - 生产隔离测试 4 passed；
   - `engine/asof` 与 `tools/as_of_integration.py` 两处 diff 均为零输出；
   - 全仓 sanity 只允许两项已知历史失败：
     - `tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented`
     - `tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds`
   - 任何第三项失败立即 STOP，不进入 G9-P1-D。
4. 全仓命令可能运行较久（历史记录约 22 分钟），必须真正等待其退出并取得完整 summary 行，不得在等待中途臆造结果；若终端输出未回传，改用 `.pytest_cache/v/cache/lastfailed` 或重新运行的方式取得新鲜证据，但不得把陈旧缓存当作本轮结论。

### G9-P1-D：报告与最终复核

1. 创建 [`reports/as-of-life-state-g9-p1-production-cli-alias-report.md`](../reports/as-of-life-state-g9-p1-production-cli-alias-report.md)，结构建议参照 [`reports/as-of-life-state-g8-production-integration-report.md`](../reports/as-of-life-state-g8-production-integration-report.md)：验证目标、写集清单、依赖方向、G9-P1-A/B/C 逐项证据（含首次 RED 原始输出）、失败 ledger 对照、`LOCAL ONLY / NOT PUSHED`、G9-P1 之外任何 Gate（含 P2/P3、G10 等）未授权且未启动。
2. 报告创建后，重新执行第 2 步全部命令一次，把新鲜结果回填报告，不得复制创建前的旧结果当作最终证据。
3. 最终收口检查：
   - `git status --short` 只应显示上述四个白名单路径为新增/修改，其余 modified/untracked 视为任务前背景噪音，明确记录、不清理、不覆盖、不归因于本任务；
   - 全仓无 `*.g9p1.tmp` 或等价临时文件残留；
   - 报告结尾声明 `LOCAL ONLY / NOT PUSHED`，且 P2、P3、G10 均未授权且未启动。

## 4. STOP 条件（出现任一即立即停止，不得自行绕过）

- 需要修改 `tools/as_of_integration.py`、`engine/asof/`、`engine/application/production_service.py` 或 `tools/production_api.py`；
- 需要修改任何禁止路径或既有测试；
- G9-P1-B 首次新增测试直接 PASS，未取得有效 RED；
- 全仓 sanity 出现两项已知历史失败之外的第三项失败；
- 需要新增依赖、切换 Python 版本或修改 `pyproject.toml`；
- 任何动作可能修改 GitHub 服务端状态（push、PR、release、远端分支等）；
- 合同文本与本提示词出现你无法用第 0 节权威文件解决的冲突。

出现 STOP 条件时：保留已取得的全部证据（不删除、不覆盖），在会话内明确写出触发的具体条件、已完成的 Gate、以及唯一下一合法动作，然后停止，不要猜测性继续。

## 5. 最终交付要求

完成 G9-P1-D 后，在同一会话内给出总结，必须包含：

1. 四个白名单文件的最终路径；
2. G9-P1-B 首次 RED 的精确 failed 数与 exit code；
3. G9-P1-C 全部验证命令的精确 passed/failed/skipped 数与 exit code（专用测试、`tests/asof`、生产隔离、全仓 sanity）；
4. 两处冻结路径 diff 均为零输出的确认；
5. 报告路径及其"报告后最终新鲜复核"章节的回填结果；
6. `git status --short` 摘要及背景噪音说明；
7. `LOCAL ONLY / NOT PUSHED` 声明；
8. 明确声明 G9-P2、G9-P3、G10（如有）均未授权且未启动。

不得在任一项证据缺失或未新鲜验证时声称任务完成。
