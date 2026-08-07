# 五派共同治理 Wave 1 分层验证记录（2026-08-06）

## 1. 记录结论与适用口径

- 验证工作区：`F:\多流派新思路`。
- 权威来源：[`multi-school-governance-wave1-implementation-2026-08-02.md`](multi-school-governance-wave1-implementation-2026-08-02.md) 的 1.8 完成定义与 Task 13；[`multi-school-governance-design-2026-08-02.md`](multi-school-governance-design-2026-08-02.md) 的 15.1 节。
- Task 13 结果：Gate A、B、C、E 均通过；Gate D 的全量命令以退出码 `2` 结束，**不得表述为 Gate D 通过**。
- Gate D 的直接失败是 dirty worktree 中 `tests/test_application_candidates.py:21` 的收集期 `SyntaxError`。后续只读调查证明该修改早于 Wave 1、HEAD 版本可解析且 Wave 1 无该文件所有权，因此分类由 Gate D 首份报告中的“inconclusive”更新为“已确认的修改前既存、与 Wave 1 无关”。
- 排除上述语法阻塞后的全量尝试又定位到未修改的 G001 回归节点反复解析大型 YAML。A-bad/B-good/C-bad 可逆切换确认了机制，并证明相关测试、产品文件和 YAML 均为 Wave 1 前既存且无工作树差异。
- 排除这两个已确认无关的阻塞文件后，剩余套件为 `4195 passed, 7 skipped, 0 failed, 0 errors, 1 warning`，退出码 `0`，耗时 `1260.9s`。
- 权威完成定义第 6 条允许“全量 pytest 通过，**或**所有失败均被证明为修改前已存在且与本波次无关”。现有证据支持采用后一分支；这不等于 exact Gate D pass，也不替代 Task 14 的最终结束审查与批准门。
- 本记录未修改产品、测试、配置或 YAML；也不授权 Wave 2 实现或 Wave 3 函数级规划。

## 2. Git 与运行环境快照

### 2.1 Gate 前 dirty worktree

- 快照命令：`git status --short`。
- 证据：`.omo/evidence/task13-gates-abce/git-status-short.txt`。
- 快照大小：`86,069` bytes；`800` 行，其中 `52` 个 tracked modified、`748` 个 untracked。
- SHA-256：`C6579F1D2DE6A9123ECAB24AFA61110054C0D3A592B97062586C7AB5DDAC77B9`。
- 验证记录编写前于 `2026-08-06T09:40:11.5461732+08:00` 再取只读状态摘要，仍为 `800` 项（`52` modified、`748` untracked）；当时本文件尚不存在。
- 为避免在日期化记录中复制大量无关路径或潜在敏感名称，此处只记统计、哈希和本地证据路径，不内嵌完整状态清单。既有 dirty worktree 未被 reset、checkout、restore、stash 或回退。

### 2.2 关键相关路径状态

- `tests/test_application_candidates.py` 为 tracked modified；当前差异为 `+15/-0`。
- 文件 mtime 为 `2026-08-02T17:22:11.8725934+08:00`，早于 Wave 1 Boulder 创建时间 `2026-08-03T13:14:59.8291462+08:00` 约 19 小时 53 分钟。
- `git show HEAD:tests/test_application_candidates.py` 的内容通过 `ast.parse`；dirty 工作副本稳定复现第 21 行未闭合 `[` 的 `SyntaxError`。
- G001 目标 `tests/regression/test_g_iteration.py`、`tools/feedback_loop.py`、`tools/rule_lifecycle.py` 及六个 `theory/*/index.yaml` 均无工作树差异；其最新提交分别早于 Wave 1 数月。

### 2.3 版本

- Python：`Python 3.14.5`，证据 `.omo/evidence/task13-gates-abce/python-version.txt`。
- pytest：`pytest 8.4.2`，证据 `.omo/evidence/task13-gates-abce/pytest-version.txt`。
- 时区：Asia/Shanghai（所有下列时间均含 `+08:00`）。

## 3. Authority Gate A-E 执行记录

权威计划中的 Gate A-D pytest 命令原文未带 `-p no:cacheprovider`；实际新鲜记录统一追加该参数以禁用 pytest 缓存插件。下表和各命令块均以**实际执行的完整命令**为准。未追加该参数的逐字 A-D 命令没有另行运行，列入第 8 节“未验证项”；不得用推断替代。

| Gate | 开始 | 结束 | 持续时间 | 退出 | passed | skipped | failed | errors | warnings | 结论/失败分类 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| A | 2026-08-05T11:02:32.5104466+08:00 | 2026-08-05T11:03:14.7185202+08:00 | 42.208s | 0 | 212 | 0 | 0 | 0 | 1 | PASS；无失败 |
| B | 2026-08-05T11:03:14.8810084+08:00 | 2026-08-05T11:05:05.8409733+08:00 | 110.960s | 0 | 333 | 0 | 0 | 0 | 1 | PASS；无失败 |
| C | 2026-08-05T11:05:05.8459596+08:00 | 2026-08-05T11:05:10.4327381+08:00 | 4.587s | 0 | 24 | 0 | 0 | 0 | 1 | PASS；无失败 |
| D | 2026-08-05T10:55:41.9426514+08:00 | 2026-08-05T10:56:06.6983474+08:00 | 24.756s | 2 | 0 | 0 | 0 | 1 | **FAIL**；收集期 SyntaxError，后续确认为 Wave 1 前既存且无关 |
| E1 | 2026-08-05T11:05:10.4387235+08:00 | 2026-08-05T11:05:11.9815310+08:00 | 1.543s | 0 | 0（非测试命令） | 0（非测试命令） | 0 | 0 | 0 | PASS；`tool registry check passed` |
| E2 | 2026-08-05T11:05:11.9840355+08:00 | 2026-08-05T11:05:14.5322031+08:00 | 2.548s | 0 | 0（非测试命令） | 0（非测试命令） | 0 | 0 | 0 | PASS；`rule status scan passed` |

Gate A 实际命令：

```text
python -m pytest tests/governance tests/application/test_governance_fact_builder.py tests/application/test_governance_claim_adapters.py tests/application/test_governance_shadow_runner.py -q -p no:cacheprovider
```

Gate B 实际命令：

```text
python -m pytest tests/yang_marriage tests/ren_timing tests/decision/test_staged_arbitration.py tests/predicates/test_ten_god_structures.py tests/test_production_rule_loader.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q -p no:cacheprovider
```

Gate C 实际命令：

```text
python -m pytest tests/test_architecture_dependencies.py tests/test_project_metadata.py -q -p no:cacheprovider
```

Gate D 全量实际命令：

```text
python -m pytest tests/ -q -p no:cacheprovider
```

Gate E authority 命令（逐字执行）：

```text
python tools/tool_registry.py --check
python tools/rule_status_scan.py --check
```

Gate A/B/C 的唯一 warning 均为 `engine/application/pipeline_runner.py:11` 导入已弃用 `engine.application.dual_engine_adapter` 的 `DeprecationWarning`；它不改变退出码。Gate D 也记录 `1` 个 warning，但在收集错误后未进入测试执行。

主证据：`.omo/evidence/task13-gates-abce.md`、`.omo/evidence/task13-gates-abce/results-summary-r2.json`、`.omo/evidence/task13-gate-d-full.md` 及其引用的逐命令日志/metadata。首轮 A/B/C/E wrapper 未可靠记录退出码，因此只保留为 instrumentation 证据，结论只取 r2。

## 4. Gate D 失败归因与补充覆盖

### 4.1 Exact full-surface Gate D：失败，不伪装为通过

- 实际命令：`python -m pytest tests/ -q -p no:cacheprovider`。
- 结果：退出 `2`；`0 passed, 0 skipped, 0 failed, 1 error, 1 warning`。
- 完整失败节点：`ERROR tests/test_application_candidates.py`。
- 首个根因：第 21 行 `SyntaxError: '[' was never closed`，pytest 在 collection 阶段中断。
- 初始 `.omo/evidence/task13-gate-d-full.md` 因当时尚无可信所有权/基线链而诚实标为 `inconclusive`；后续 `.omo/evidence/task13-gate-d-syntax-debug-journal.md` 的稳定哈希、dirty diff、mtime、HEAD parse 与 Wave 1 ledger/ownership 检查将其更新为：**确认 Wave 1 前既存且与 Wave 1 无关**。

### 4.2 仅排除语法阻塞的两次尝试

实际命令：

```text
python -m pytest tests/ -q -p no:cacheprovider --ignore=tests/test_application_candidates.py
```

| 轮次 | 开始 | 结束 | 持续/边界 | 退出 | 最终统计 | 分类 |
|---|---|---|---:|---|---|---|
| primary | 2026-08-05T11:52:14.8758154+08:00 | 2026-08-05T11:57:15.4923911+08:00 | 300.617s / 300s bound | TIMEOUT | 无最终 summary；到 53% | bounded timeout；无失败节点、traceback 或 stderr |
| rerun | 2026-08-05T16:40:47.0672528+08:00 | 2026-08-05T16:55:47.3852959+08:00 | 900.318s / 900s bound | TIMEOUT | 无最终 summary；到 70%，仅观察到 2981 dots、1 skip marker，不能当最终计数 | bounded timeout；无失败节点、traceback 或 stderr |

证据：`.omo/evidence/task13-gate-d-excluding-known.md`。这两次运行不替代 Gate D，也不能声称通过。

### 4.3 G001 YAML repeated-parse A/B/C 强因果证据

固定测试节点：`tests/regression/test_g_iteration.py::test_g001_dry_run_idempotent`；测试和断言在 A/B/C 中不变，monkeypatch 仅存在于内存，`PYTHONDONTWRITEBYTECODE=1`。

| Toggle | 缓存 | 结果 | 持续时间 | 读取/字节 | 观察 |
|---|---|---|---:|---|---|
| A | off | BAD / timeout | 35.019s | 29 reads；10,420,726 bytes | 未产生 pytest 最终 summary |
| B | on，仅内存 Path-keyed cache | GOOD / `1 passed`，pytest exit 0 | 15.922s harness；pytest `1 passed in 15.50s` | 182 logical；6 physical；176 hits；5,814,779 physical bytes | 原断言执行并通过 |
| C | off，fresh interpreter | BAD / timeout | 35.067s | 30 reads；13,218,622 bytes | 缓存移除后同一症状复现 |

结论：`load_rule` / `_locate_rule_in_yaml` 路径对六个多 MB YAML index 的反复未缓存解析是该节点超时的可逆、可复现原因。目标测试、两个直接产品文件及六个 YAML 均未修改，最新提交早于 Wave 1，且反馈/学习写入路径明确不在 Wave 1 范围内。分类：**确认 Wave 1 前既存且与 Wave 1 无关**。该证据只确认机制与归因，不选择或授权永久修复。

证据：`.omo/evidence/task13-g001-yaml-toggle.md`。

### 4.4 Remaining-suite 补充回归

实际完整命令（两个 exact ignore flags）：

```text
python -m pytest tests/ -q -p no:cacheprovider --ignore=tests/test_application_candidates.py --ignore=tests/regression/test_g_iteration.py
```

- 环境：`PYTHONDONTWRITEBYTECODE=1`；timeout bound `2400s`。
- 开始：`2026-08-06T09:08:00.8464292+08:00`。
- 结束：`2026-08-06T09:29:01.7459362+08:00`。
- 持续：`1260.9s`；timed out：`false`；退出码：`0`。
- 统计：`4195 passed, 7 skipped, 0 failed, 0 errors, 1 warning`。
- warning：同一既有 `dual_engine_adapter` deprecation warning。
- 此结果仅证明两个被排除文件以外的 remaining suite；`--ignore=tests/regression/test_g_iteration.py` 排除了整个文件，不得推断该文件中除 G001 外的其他节点已由本命令验证。

证据：`.omo/evidence/task13-gate-d-remaining-suite.md`、`.omo/evidence/task13-gate-d-remaining-suite-pytest-output.txt`、`.omo/evidence/task13-gate-d-remaining-suite-pytest-meta.json`。

## 5. 失败分类汇总

| 表面 | 失败/异常 | 最终分类 | Wave 1 归因 |
|---|---|---|---|
| Gate A/B/C/E | 无 | PASS | 无回归 |
| Gate D exact full-surface | collection `SyntaxError`，exit 2 | pre-existing dirty test edit | 已确认与 Wave 1 无关 |
| Gate D 排除语法文件，300s/900s | 无 summary 的 bounded timeout | G001 repeated uncached YAML parse；经 A/B/C toggle 确认 | 已确认与 Wave 1 无关 |
| Remaining suite | 无失败；7 skipped；1 warning | PASS，exit 0 | 未观察到 Wave 1 回归 |
| DeprecationWarning | `dual_engine_adapter` 已弃用导入 | 非阻塞 warning | 本记录未将其作为失败或修复授权 |

依据完成定义第 6 条，“所有失败均被证明为修改前已存在且与本波次无关”的证据链由以下两项强证据闭合：

1. `test_application_candidates.py` dirty mtime 早于 Wave 1、HEAD parse 成功、当前 `+15/-0` 差异稳定且 Wave 1 ledger 无所有权。
2. 未变更的 G001/YAML 表面通过 A-bad/B-good/C-bad repeated-parse toggle 确认因果，且所有目标路径无 diff、提交日期早于 Wave 1。

## 6. Wave 1 15.1 八项退出门一一映射

| # | 上位设计 15.1 退出门 | 新鲜/关键证据 | Task 13 判定 |
|---:|---|---|---|
| 1 | 公共事实可确定性重建且摘要稳定 | Gate A `212 passed`；`.omo/start-work/artifacts/task1-canonical.txt` 的 fresh-process digest/ID 相等；`.omo/start-work/artifacts/task2-fact-contracts.txt` 与 `task3-fact-builder.txt` | PASS |
| 2 | 五派适配器只能读取公共事实 | Gate A adapter suites；Gate C architecture tests；`.omo/start-work/artifacts/task5-governance-claim.txt`；`.omo/evidence/task12-static-isolation-gate-review.md` | PASS |
| 3 | SchoolClaim 契约通过不可变性和引用完整性测试 | Gate A governance/claim adapter coverage；`.omo/start-work/artifacts/task5-governance-claim.txt` | PASS |
| 4 | 七步仲裁通过顺序无关、幂等和同源折叠测试 | Gate A governance suite；`.omo/start-work/artifacts/task7-arbitration.txt` | PASS |
| 5 | 未知 trigger 已在新路径 fail closed | Gate A governance suite；`.omo/evidence/task9-trigger-boundary-gate-review.md`（focused 14/14 两次、governance 159/159） | PASS |
| 6 | 旧三格局和现有杨婚姻、任应期测试无回归 | Gate B `333 passed, 0 failed, 0 errors`，包含 `yang_marriage`、`ren_timing`、staged arbitration、three structures 与 production loader | PASS |
| 7 | 30 格局目录存在稳定 ID 和兼容映射 | Gate A governance suite；`.omo/evidence/task10-structure-catalog-gate-review.md`（exact plan 25/25、governance 159/159） | PASS |
| 8 | Wave 1 的变更取得新鲜验证证据 | 本记录的 Gate A/B/C/E、Gate D 失败与归因、remaining suite；`.omo/evidence/task13-gates-abce.md` 及全部 Task13 Gate D 证据 | PASS（采用完成定义第 6 条的“既存且无关”分支；exact Gate D 仍为 FAIL） |

退出门映射只说明 Task 13 的证据覆盖；Wave 1 最终关闭、全局评审、调试审计和停止门仍归 Task 14。

## 7. 清理、进程与 pycache 限制

- Gate A/B/C/E scoped subprocess 设置 `PYTHONDONTWRITEBYTECODE=1`，pytest 使用 `-p no:cacheprovider`；记录到的另一个 Python 进程不属于 Task 13 命令，未终止。
- Gate D exact run 后未发现 scoped Python/pytest 进程；按时间筛选的五个 scoped `__pycache__` 目录已由该次证据流程移除，详见 `.omo/evidence/task13-gate-d-full-pycache-cleanup.txt`。
- 两次“仅排除语法文件”运行均由 timeout wrapper 停止 scoped pytest；另一个不属于本任务的 pytest 进程被保留。其 pycache 清理目标虽已枚举，但 `Remove-Item -Recurse` 在执行前被工具安全策略阻止，因此这些目标**未完成清理**，详见 `.omo/evidence/task13-gate-d-excluding-known/cleanup-pycache.txt`。
- Remaining-suite 运行禁用 bytecode 和 pytest cache provider；只停止了一次 owned malformed wrapper，未终止任何 unowned 进程，也未尝试清理不归本任务所有的 cache。
- G001 toggle 没有创建 harness 文件，monkeypatch 随进程消亡，三次均无 scoped toggle Python 残留；既有 `.pyc` 的 June 时间戳未变。机器级进程列表中的无关 pytest 被保留。
- `.omo/evidence/task13-gate-d-syntax-debug-journal.md` 的 Cleanup 段仍写为 `Pending`；应以各具体 run 的 cleanup/process artifacts 和本节限制为准。本记录不宣称机器级全局无 Python 进程、全仓无 `__pycache__`，也不删除用户或其他任务资源。

## 8. 未验证项与剩余风险

- **未验证**：不带 `-p no:cacheprovider` 的 Gate A/B/C/D authority 命令逐字形式；现有动态结果对应第 3 节列出的实际完整命令。
- **未验证/未通过**：exact full-surface Gate D 的成功退出；已知实际结果为 exit `2`，不得改写为 pass。
- **未验证**：对 `tests/test_application_candidates.py` 的修复；本任务无权修改用户 dirty 测试。
- **未验证**：G001 repeated-parse 的永久修复及未缓存路径在无时间边界下的最终完成时间；toggle 只确认原因和归因。
- **未验证**：remaining-suite 命令排除的两个完整测试文件；尤其 `tests/regression/test_g_iteration.py` 中 G001 以外节点不能由 `4195 passed` 推断。
- **未验证**：7 个 skipped 测试在其跳过条件不成立时的行为。
- **未验证**：全仓、机器级 pycache 清空或无关 Python/pytest 进程终止；这些操作超出所有权且可能破坏并行工作。
- **未验证**：Task 14 最终批准、Wave 2/3；未经用户另行批准不得进入。
- 剩余非阻塞风险：同一 `dual_engine_adapter` deprecation warning 仍存在；本任务只记录，不扩大范围修复。

## 9. 证据索引

- `.omo/evidence/task13-gates-abce.md`
- `.omo/evidence/task13-gates-abce/results-summary-r2.json`
- `.omo/evidence/task13-gate-d-full.md`
- `.omo/evidence/task13-gate-d-full-meta-rerun.json`
- `.omo/evidence/task13-gate-d-syntax-debug-journal.md`
- `.omo/evidence/task13-gate-d-excluding-known.md`
- `.omo/evidence/task13-g001-yaml-toggle.md`
- `.omo/evidence/task13-gate-d-remaining-suite.md`
- `.omo/evidence/task13-gate-d-remaining-suite-pytest-meta.json`
- `.omo/start-work/artifacts/task1-canonical.txt`
- `.omo/start-work/artifacts/task2-fact-contracts.txt`
- `.omo/start-work/artifacts/task3-fact-builder.txt`
- `.omo/start-work/artifacts/task5-governance-claim.txt`
- `.omo/start-work/artifacts/task7-arbitration.txt`
- `.omo/evidence/task9-trigger-boundary-gate-review.md`
- `.omo/evidence/task10-structure-catalog-gate-review.md`
- `.omo/evidence/task12-static-isolation-gate-review.md`

本索引全部为工作区内相对路径；记录未复制完整 git 状态或无关进程命令行，未写入凭据、令牌、个人数据或外部系统信息。
