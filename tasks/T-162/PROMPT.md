# T-162 · `verify_baseline` 修复：区分「测出 0 分」与「根本没跑起来」

- 状态：🔵 Ready for Execution
- 优先级：**P2（尺子可信度；不涉及产品口径）**
- 创建：2026-10-29（中枢）
- 依据：`docs/handoff-hub-v1.md` §三已知缺陷；ADR-004 红线三
- 前置：无

## 0. 一句话

`verify_baseline` 现在把「pytest 没跑起来」误报成 `pytest_passed: 0`；若此时 `--save`，会把假基线写进
`META/baseline-v1.json`，之后所有 `--compare` 都在跟假基线比。本卡只修这个「0 分 vs 没跑」的歧义。

## 1. 现状（已核实）

- `tools/verify_baseline.py:45-50`：`pytest_passed` / `pytest_failed` 用正则匹配，匹配不到就填 **0**；
  只看 `pytest_rc`，但 `0 passed` 与「没跑起来」在 JSON 里不可区分。
- `--save` 无条件写文件；即使 `pytest_rc != 0` 也照写。
- `regressions()` 直接比较数字，假 0 会被当成「通过数下降」（或写进基线后永远比错）。
- 同类风险：`audit_errors` / `zuogong_charts` 匹配不到时填 `-1`，`relations_ok` 只看 rc；
  本卡优先修 pytest，其余至少加「是否跑起来」标记。

## 2. 修法（预注册）

1. `measure()` 增加字段：
   - `pytest_ran: bool`（进程确实输出了 pytest 结果，或至少 rc==0 且匹配到 `passed`）
   - `pytest_parse_ok: bool`（匹配到 `passed` / `failed` 之一）
   - 匹配不到时 `pytest_passed` / `pytest_failed` 写 **`null`**，不再写 0。
2. `--save` 前置条件：四项工具都必须「跑起来」——
   pytest `pytest_ran=true` 且 `pytest_rc==0`；`audit_rc==0`；`relations_rc==0`；`zuogong_rc==0`。
   否则打印原因并 **退出码 2，不写文件**。
3. `--compare`：若本次 `pytest_ran=false`，打印「pytest 未跑起来，不能与基线比较」并 **退出码 2**；
   不得把 null/未跑当成 0 来算退步。
4. `regressions()` 对 `null` 做防御：old/new 任一侧为 null → 返回明确错误，不做数字比较。
5. **不改动**四项判据本身、不改 `META/baseline-v1.json`、不改 quick 语义。

## 3. 测试（新建 `tests/tools/test_verify_baseline.py`）

用 monkeypatch 替换 `run()`，不真的跑 pytest：

1. `(0, "1246 passed, 1 skipped")` → `pytest_ran=true`、`pytest_passed=1246`；
2. `(1, "")` → `pytest_ran=false`、`pytest_passed is None`；`--save` 退出 2 且**不写文件**；
3. `(1, "3 failed, 10 passed")` → `pytest_ran=true`、passed=10/failed=3；`--save` 退出 2（rc!=0）；
4. 已有基线 + 本次未跑 → `--compare` 退出 2，不报「通过数下降」；
5. 正常 `--save` 后 `--compare` 退出 0。

## 4. File Scope

**允许修改**

- `tools/verify_baseline.py`

**允许新建**

- `tests/tools/test_verify_baseline.py`

**只读**

- `META/baseline-v1.json`（不要改；验收时用真实 `--save` 由中枢决定是否刷新）

**禁止**

- 改四项判据、改 pytest 命令、改 `--quick` 语义
- 改既有测试、`engine/**`、`theory/**`、`sources/**`
- `git commit / push / checkout / stash / reset / clean`

## 5. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest tests/tools/test_verify_baseline.py -q -o addopts="-ra --tb=short"
.venv\Scripts\python.exe -m tools.verify_baseline                 # 真实跑，仍应是 1246 / 0 / ok / 477 / 346
.venv\Scripts\python.exe -m tools.verify_baseline --compare       # 当前基线与真实值可能已不同；只要求不崩、不把「没跑」当 0
.venv\Scripts\python.exe -m pytest -q                             # 0 failed
```

中枢额外检查：

- `--save` 在模拟失败下确实不写文件（测试覆盖）；
- 真实 `verify_baseline` 的四项数字与当前一致（pytest 1246 / audit 0 / relations ok / 477 / 346）；
- 没有把 `-1` 或 `null` 洗成 0。

## 6. 回报格式（`tasks/T-162/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（测试 + 真实四项）
3. **未完成与风险**（其余三项的「没跑起来」标记是否也加）
4. **下游须知**（baseline JSON 新增字段、null 语义）

## 7. 禁止

- 不许把「没跑」写成 0。
- 不许为了让 `--compare` 变绿而改基线文件或改判据。

## 7. Amendments（2026-10-29 00:55）

1. **pytest 汇总行只打印非零计数**：`pytest_parse_ok=true` 时，缺失的一侧按 0 计（如 `1289 passed` → `failed=0`）；
   只有完全解析不到 `passed/failed` 汇总时才写 `null`。否则正常绿色跑会得到 `failed=null`，`--compare` 永远无法比较。
2. 验收数字以现场为准：本次真实跑 **1289 passed**（含并行 T-161/T-164/T-165 新增测试），不是卡上的 1246。
3. 基线文件本卡仍不刷新；等夜间批全部落地后统一刷新。
