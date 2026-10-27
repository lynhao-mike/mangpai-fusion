# T-141 STATUS

- 状态：✅ **Done**（待中枢验收）
- 完成时间：2026-10-27
- 执行者：子代理（T-141）
- 任务卡：`tasks/T-141/PROMPT.md`
- 决策依据：`docs/adr/ADR-007-refactor-direction-adjudication.md` D1
- 简报：`tasks/T-141/BRIEF.md`

## 改了什么

| 文件 | 性质 |
|---|---|
| `engine/facts/structure_check.py` | **1 行**（`:382`）：`_crosses` 改为 `{a, b} not in ({"体"}, {"用"}, {"双属"})` |
| `tests/facts/test_structure_check.py` | 1 行改（`test_zuogong_only_crosses_ti_yong` 排除集合补 `{"双属"}`）+ 新增 `test_zuogong_excludes_dual_x_dual` 7 行 |

未改：`_TIYONG` 表本身、`engine/energy/`、`engine/api/facade.py`、`theory/_ir/`、`sources/`、`pyproject.toml`（`git status` 仅上述两文件 + 本卡测量脚本）。无任何 git 破坏性操作。

**没有出现需要改测试维持数字的情况**：新测试在旧实现下必然失败（`甲子 丙寅 丙辰 戊戌`：旧 16 条/含 2 条双属×双属 → 新 14 条/0 条），是有效门禁。

## 验收（中枢请亲自重跑）

```text
.venv\Scripts\python.exe -m pytest -q
→ 227 passed, 1 skipped, EXIT=0        （基线 220 passed）

.venv\Scripts\python.exe -m tools.verify_baseline
→ pytest_passed 227 / failed 0 / audit_errors 0 / relations_ok true /
  zuogong_charts 477 / zuogong_day_branch 346 / EXIT=0

.venv\Scripts\python.exe -m tools.verify_baseline --compare
→ 【基线未退步】 EXIT=0
```

## 481 盘实测（改前 vs 改后，同盘同路径）

| 指标 | 改前 | 改后 | 变化 |
|---|---:|---:|---:|
| 候选总数 | 7527 | 7395 | −132 |
| 制用 | 4210 | 4100 | −110 |
| 化用 | 450 | 450 | 0 |
| 生泄用 | 1462 | 1462 | 0 |
| 合用 | 898 | 898 | 0 |
| 墓用 | 507 | 485 | −22 |
| 「双属×双属」条数 | 132（66 盘） | **0** | −132 |
| `zuogong_charts` | 477 | **477** | **0** |
| `zuogong_day_branch` | 350 | **346** | **−4** |
| 零候选盘 | 0 | 0 | 0 |

被删 132 条按关系种类：`canggan_ke` 49、`xing` 42、`muku` 22、`chong` 19。**无新增候选**。新增/减少的 `ke`/`sheng`/合类均为 0。

## Blockers

无阻塞。一条**待中枢定性**：

- `zuogong_charts` 主指标 477→477 未降（`--compare` 因此判「未退步」），但**次级指标 `zuogong_day_branch` 350→346**。`tools/verify_baseline.py:71-84` 的 `regressions()` 不校验该字段，所以 `--compare` 绿灯**不覆盖**这次下降。下降的 4 盘（C-2026-030 / C-2026-RF000668 / C-2026-RF000175 / C-2026-RF000487）丢失的 `D.b` 宫制星全是「食伤支克食伤干」。按原文（`sources/duan/...开山之作.md:1305-1307`、`:1314`、`:1316`）食伤为中性之物、做功须两端分属体用，应删。我按卡要求未做任何找平。

## Execution Log

- 2026-10-27 14:55 读 `PROMPT.md` 与 ADR-007 D1；核对原文 `sources/duan/...开山之作.md:1305-1307,1314,1316`（卡内标注的 `:1311-1313` 为同段、行号有偏移）。
- 14:56 发现改动已由上一会话落盘（`git diff` 显示 `_crosses` 与测试均已改，`tasks/T-141/` 留有 `.measure_*.json`/`.pytest_*.txt`），无 `BRIEF.md`/`STATUS.md`。改为独立复核而非重做。
- 15:00 首次跑 `.venv\Scripts\python.exe` 遇 uv trampoline `permission denied (os error 5)`（rc=107）；用基础 3.11 + venv site-packages 等价口径完成测量；随后原样命令恢复正常。
- 15:05 写 `_measure_ab.py`：同进程内替换 `structure_check._crosses` 为旧实现，481 盘跑两轮 → 7527/7395，双属 132→0，`zuogong_charts` 477→477、`day_branch` 350→346。
- 15:12 写 `_probe_delta.py`：132 条按 relation_kind 分解（canggan_ke 49 / xing 42 / muku 22 / chong 19），定位丢 `actor=D.b` 的 4 盘。
- 15:18 写 `_examples.py` 取 3 例细节：被删候选的 `binzhu` 三层方向改前全部为「需判断」，与 `_ti_yong_ends` 的 `None` 分支印证自相矛盾。
- 15:22 验证新测试非空转（旧逻辑 16 条含 2 条双属 → 新 14 条含 0 条）；`pytest tests/facts/test_structure_check.py` 15 passed。
- 15:26 原样跑两条验收命令（227 passed / 1 skipped EXIT=0；verify_baseline EXIT=0）+ `--compare`（未退步 EXIT=0）。
- 15:30 检查标杆盘影响：`癸丑 癸亥 辛亥 癸巳` 14→13（删 1 条伤官×伤官 xing），`壬子 乙巳 庚子 壬午` 17→17 不受影响；全 481 盘零候选盘 0→0。
- 15:34 写 `BRIEF.md` 与 `STATUS.md`。
