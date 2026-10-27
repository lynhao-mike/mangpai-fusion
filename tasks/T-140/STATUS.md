# T-140 STATUS

- 状态：✅ **Done**（待中枢验收）
- 完成时间：2026-10-27
- 执行者：子代理（T-140）
- 任务卡：`tasks/T-140/PROMPT.md`（含 §4.0 中枢两次追加裁决，最终口径＝**事实视图 / Agent 视图分离**）
- 简报：`tasks/T-140/BRIEF.md`

## 改了什么

| 文件 | 性质 |
|---|---|
| `engine/api/facade.py` | `_compact` 加 `keep_null_keys`；`_compact_zuogong` 白名单扩到 tiyong/actor/binzhu/distance 且 actor 恒保留键；新增 `compact_for_agent()`；`analyze_facts` 返回完整事实 |
| `engine/cli.py` | `all` 默认套 Agent 投影；新增 `--full` |
| `tests/api/test_facade_zuogong_fields.py` | 新增 6 条回归 |

未改：`engine/facts/`、`theory/_ir/`、`sources/`、`pyproject.toml`、`tests/api/test_engine_reset_regression.py`（`git diff` 为空）。无任何 git 破坏性操作。

## 验收（中枢请亲自重跑）

```text
.venv\Scripts\python.exe -m pytest -q
→ 226 passed, 1 skipped, EXIT=0   （基线 220 passed）

.venv\Scripts\python.exe -m tools.verify_baseline
→ pytest_passed 226 / pytest_failed 0 / audit_errors 0 / relations_ok true /
  zuogong_charts 477 / EXIT=0     （四项不降）
```

## Execution Log

- 2026-10-27 11:40 读卡 + ADR-007 D5，复现 `tiyong` 被 facade 丢掉 → target 恒等于 `members[-1]`（14/14）。
- 11:50 按原卡实现后实测 CLI 18 556 B，撞穿 `test_cli_all_json_under_15kb`（15 000）→ 按卡内「停卡报告」规则上报，未自行放宽断言。
- 11:57 中枢裁决①「binzhu 改紧凑」；实测任何 binzhu 表示法（含不发 binzhu＝15 554 B）均无法进 15 000 → 二次上报。
- 12:00 中枢裁决②「事实视图与 Agent 视图分离，15 000 不许动」→ 按此实现：`analyze_facts` 完整、`cli all` 默认投影、`--full` 全量。
- 12:01 `pytest -q` 226 passed / 1 skipped（EXIT 0）；`tools.verify_baseline` 四项不降（EXIT 0）；默认输出 14 864 B、`--full` 18 556 B；15KB 测试文件零改动。

## Blockers

无阻塞。有三条**待中枢裁决/知会**事项，详见 BRIEF §7：

1. Agent 视图余量仅 136 B（14 864 / 15 000），建议单开卡收口预算与投影白名单。
2. 投影清单超出中枢点名的 `binzhu`：另加 `distance` + `relations.nodes` + `edges.chars` + `edges.between`（均纯函数可还原），否则压不进预算；请复核口径。
3. `atoms.py:487` 的 target 语义仍不准（「用」＝官杀时 target 会等于 actor），超出本卡 File Scope，需另开卡。

## 已知影响下游

`engine.cli all` 默认输出不再含 `relations.nodes` / `edges[].chars` / `edges[].between` / `candidates[].binzhu` / `candidates[].distance`。`tools/rf_facts_hydrate.py` 若仍需要「全量事实」，应改用 `--full`（本卡未改 `tools/`）。
