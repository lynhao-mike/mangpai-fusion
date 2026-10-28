# T-162 BRIEF · verify_baseline 区分「0 分」与「没跑起来」

- 执行：子代理（2026-10-29 00:50）
- 结论：完成，待中枢亲自重跑验收

## 1. 改动文件

| 文件 | 动作 | 说明 |
|---|---|---|
| `tools/verify_baseline.py` | 修改 | `measure()` 增加 `pytest_ran` / `pytest_parse_ok` 与 `audit_ran` / `relations_ran` / `zuogong_ran`；未跑时 pytest 计数写 `null`；`--save` 四项前置门禁（退出 2 且不写文件）；`--compare` 本次未跑退出 2；`regressions()` 对 `null` 抛 `BaselineError`（退出 2） |
| `tests/tools/test_verify_baseline.py` | 新建 | 8 个测试，monkeypatch 替换 `run()`，不真实跑 pytest |
| `tasks/T-162/BRIEF.md` | 新建 | 本文件 |
| `tasks/T-162/STATUS.md` | 追加 | Execution Log |

未改：`META/baseline-v1.json`（`git status` 未修改）、四项判据、pytest 命令、`--quick` 语义、既有测试、`engine/**`、`theory/**`、`sources/**`。

## 2. 原始输出

### 新测试

```text
tests/tools/test_verify_baseline.py::test_measure_success PASSED         [ 12%]
tests/tools/test_verify_baseline.py::test_measure_empty_output_is_null_not_zero PASSED [ 25%]
tests/tools/test_verify_baseline.py::test_save_refuses_when_pytest_not_ran PASSED [ 37%]
tests/tools/test_verify_baseline.py::test_failed_run_parses_counts_and_blocks_save PASSED [ 50%]
tests/tools/test_verify_baseline.py::test_compare_refuses_when_pytest_not_ran PASSED [ 62%]
tests/tools/test_verify_baseline.py::test_compare_refuses_null_baseline_field PASSED [ 75%]
tests/tools/test_verify_baseline.py::test_save_then_compare_ok PASSED    [ 87%]
tests/tools/test_verify_baseline.py::test_regressions_rejects_null_side PASSED [100%]

8 passed in 0.19s
```

### 真实 `python -m tools.verify_baseline`

```json
{
  "pytest_parse_ok": true,
  "pytest_ran": true,
  "pytest_passed": 1260,
  "pytest_failed": 0,
  "pytest_rc": 0,
  "audit_errors": 0,
  "audit_rc": 0,
  "audit_ran": true,
  "relations_ok": true,
  "relations_rc": 0,
  "relations_ran": true,
  "zuogong_charts": 477,
  "zuogong_ran": true,
  "zuogong_day_branch": 346,
  "zuogong_rc": 0
}
```

计数说明：卡上的 1246 是 T-162 开工前的基数；本次 1260 = 1246 + 本卡新增 8 个测试 + 并行 T-163 新增 6 个测试（`tests/tools/test_rule_contract_report.py`）。其余三项 `audit_errors=0` / `relations_ok=true` / `zuogong_charts=477` / `zuogong_day_branch=346` 与卡一致。

### 真实 `python -m tools.verify_baseline --compare`

```text
（同上 JSON）
【基线未退步】
EXIT=0
```

当前 `META/baseline-v1.json` 仍是旧的 `pytest_passed=1142`，按卡只读未刷新；`--compare` 正常、未把未跑当 0。

### 全量 `python -m pytest -q`

```text
1260 passed, 1 skipped, 1 warning in 122.68s (0:02:02)
```

0 failed；skip 是 AGENTS.md 记录的 `test_bundle_pii` 过渡 skip。

### `--save` 模拟失败 / `--compare` 未跑

- `test_save_refuses_when_pytest_not_ran`：`run()` 对 pytest 返回 `(1, "")` → `--save` 退出 2，临时 baseline 文件不存在（`assert not baseline.exists()`）。
- `test_failed_run_parses_counts_and_blocks_save`：`(1, "3 failed, 10 passed")` → passed=10 / failed=3，`--save` 因 rc!=0 退出 2，文件不存在。
- `test_compare_refuses_when_pytest_not_ran`：已有基线 + 本次 `(1, "")` → `--compare` 退出 2，输出含「pytest 未跑起来，不能与基线比较」，且不含「通过数」下降信息。

另用独立脚本（非 pytest）复核同一路径：

```text
SAVE_FAIL_RC= 2 FILE_EXISTS= False
COMPARE_UNRUN_RC= 2
```

## 3. 未完成与风险

1. **`pytest_failed=0` 的必要推断**：pytest 汇总行只打印非零计数。`pytest_parse_ok=true` 时缺失的一侧按 0 计（如 `1260 passed, 1 skipped` → `pytest_failed=0`），这是汇总行本身的确定含义；只有完全解析不到 passed/failed 汇总（`pytest_parse_ok=false`）时两个计数才写 `null`。若严格按「单个正则匹配不到就 null」，正常绿色跑也会写 `pytest_failed=null`，`--compare` 将永远无法比较（与卡 §3.5 冲突），故采用上述口径。
2. 其余三项只加了「是否跑起来」标记（`audit_ran` / `relations_ran` / `zuogong_ran`）；`--save` 门禁仍按卡要求只检查 `audit_rc` / `relations_rc` / `zuogong_rc == 0`。若工具 rc=0 但输出格式变化导致 `audit_ran=false`，仍可能把 `audit_errors=-1` 写进基线；本卡未扩大范围收紧，建议后续卡处理。
3. `relations_audit` 的 rc=1 既可能是「校验发现问题」也可能是解释器崩溃；marker 用「结论:」输出行区分，但 rc!=0 时 `--save` 一律拒绝（符合卡）。
4. 基线 JSON 会新增 `pytest_ran` / `pytest_parse_ok` / `audit_ran` / `relations_ran` / `zuogong_ran` 字段；旧基线没有这些字段不影响 `--compare`（只读本次测量值）。
5. 本卡未真实执行 `--save`（会改 `META/baseline-v1.json`，硬约束禁止）；写文件行为由 `tmp_path` 测试覆盖。

## 4. 下游须知

- `pytest_passed` / `pytest_failed` 现在可能是 `null`：`pytest_ran=false` 表示「没跑起来」，不是 0；消费方不得 `or 0`。
- `--save` 新增退出码 2：任一工具未跑起来或 rc!=0 时拒绝写文件；`--compare` 新增退出码 2：本次 pytest 未跑、无基线、或基线字段为 `null` 时拒绝比较。
- `--compare` 的退出码 1 仍只表示「指标下降」；退出码 2 表示「尺子不可用」，不要当退步处理。
- 若中枢要刷新基线，请在本卡验收通过后亲自跑 `.venv\Scripts\python.exe -m tools.verify_baseline --save`；刷新后旧基线的 `pytest_passed=1142` 会被真实值替代。
- 新增字段均为测量元数据，四项判据本身未动。

## Blockers

无。
