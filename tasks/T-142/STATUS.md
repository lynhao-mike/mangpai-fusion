# T-142 STATUS

- 状态：✅ **Done**（待中枢验收）
- 完成时间：2026-10-27
- 执行者：子代理（T-142）
- 任务卡：`tasks/T-142/PROMPT.md`
- 决策依据：`docs/adr/ADR-007-refactor-direction-adjudication.md` D3 / D5 / D12
- 简报：`tasks/T-142/BRIEF.md`

## 改了什么

| 文件 | 性质 |
|---|---|
| `engine/claims/condition_ir/atoms.py` | ① 新增 `_edges(ctx, scope="natal")`，9 个关系原子统一走它，`edge` 增 `scope?`；② `HE_KINDS` 收窄为 `("liuhe","zhi_anhe")` + `_is_he_edge()` + `exclude_god?`；③ `binzhu` 由恒 `unknown` 改为读事实（候选 `binzhu` 读数 / `binzhu_side` 回落），参数 `layer, side?, at?`；④ 新增 `lu_at(gan?, at?)`，禄表从 `chart_facts._LU` 导入；⑤ 新增 `needs_judgment(reason)` 恒 unknown；⑥ `ATOMS` 42 → 44，`SIGNATURES` 同步 |
| `engine/claims/condition_ir/ir.py` | **仅 `_label`**：支持 `all` / `any` / `not` 递归展开，输出 `all[...]` / `any[...]` / `not(...)`，无 `atom` 时给 `<无原子:键名>`，不再出现 `?()` |
| `engine/contracts/23-claim-condition-protocol-v1.md` | 原子表 42 → 44、版本 `v1.1`；§四 加岁运隔离总则；§4.2 补 `scope` / `exclude_god`；新增 §4.2.1 `he_at` 合口径（逐 kind 判据 + 原文行号 + `full` 待裁定）；§4.4 `binzhu` 签名与事实来源；新增 §4.7 禄与显式未知；§6.2 42 → 44；§九 新增 §9.1 变更登记 5 行 |
| `tests/claims/test_condition_ir_atoms.py` | 新增 35 条回归（六件事各有门禁，含 3 个「改前必然失败」的判据） |

未改：`engine/api/facade.py`（T-140）、`engine/facts/**`（T-141）、`theory/claims/**`（T-143）、`theory/_ir/`、`sources/`、`pyproject.toml`。`git status` 只有上述 3 个源文件 + 1 个测试 + 本卡 3 个测量脚本。无任何 git 破坏性操作（未 commit / push / checkout / stash / reset）。

## 验收（中枢请亲自重跑）

```text
.venv\Scripts\python.exe -m pytest -q
→ 994 passed, 1 skipped, 1 warning, EXIT=0      （改动前同命令 959 passed；+35 为本卡新增）
  注：T-144 已把门禁从 226 档扩到 994 档，与 T-140/T-141 简报的 226/227 不可直接比。

.venv\Scripts\python.exe -m tools.verify_baseline
→ pytest_passed 994 / failed 0 / audit_errors 0 / relations_ok true /
  zuogong_charts 477 / zuogong_day_branch 346 / EXIT=0

.venv\Scripts\python.exe -m tools.verify_baseline --compare
→ 【基线未退步】 EXIT=0
```

## 关键数字

| 指标 | 改前 | 改后 |
|---|---:|---:|
| `he_at(D.b)` 481 盘命中 | 412（85.7%） | **182（37.8%）** |
| kind 明细（首条命中） | liuhe 70 / zhi_anhe 48 / sanhe 155 / sanhui 134 / ganzhi_zihe 5 | liuhe 109 / zhi_anhe 73 |
| `M1-D-298` candidate（481 盘） | 6 | **39** |
| `M1-D-298` rejected（481 盘） | 467 | 364 |
| `ATOMS` | 42 | **44** |

## Execution Log

- 2026-10-27 16:45 前置核对：T-140/T-141 均 Done；`facade.py:102` keep 含 `tiyong`、`structure_check._crosses` 已排除 `双属` → 通过。
- 16:55 读卡 + ADR-007 D3/D5/D12 + 契约 23 + `relation_graph` scope 实现。实测 `he_at(D.b)` 基线 412/481 与卡内 kind 明细逐项吻合，未发现卡与代码不符。
- 17:05 实现 ①②③④⑤ + `_label`；`ATOMS` 先改契约再改断言。
- 17:20 新增 35 条测试；首轮 3 红（`failed` 列表重复标签的断言写法、空亡盘取址错误），修的是**测试写法**而非放宽判据：把「精确等值」改为「包含 + 无 `?()`」，并把未知节点换成确定的真节点。
- 17:35 `pytest -q` 994 passed / 1 skipped（EXIT 0）；`verify_baseline` 四项不降（EXIT 0）；`--compare` 基线未退步。
- 17:45 写 BRIEF / STATUS；3 个测量脚本入库（`_measure_he_at.py` / `_measure_claim_298.py` / `_proofs.py`）。

## Blockers

无阻塞。有 7 条**待中枢裁定 / 知会**事项，详见 `BRIEF.md` §6，其中最需要拍板的两条：

1. **完整三合/三会（`full`）是否算「被合」**：原文（段·婚姻专辑:48、任·r05-r07:490）只举六合与暗合，无据支持完整局；当前**保持排除**并已写进契约 §4.2.1「待裁定」。
2. **`ir.py` 失败列表重复同一标签**（既有缺陷，`failed + out.failed + [_label(child)]`）：本卡对 `ir.py` 只有「仅 `_label`」授权，未改，仅登记。
