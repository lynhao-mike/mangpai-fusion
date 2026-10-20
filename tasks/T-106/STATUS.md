# T-106: 阻止测试污染 manifest — Status

**Status:** 🟢 阶段二完成（方案 A2 已实施，验收 1-5 全绿）
**Current Step:** Step 2 ✅ 完成
**Last Updated:** 2026-10-19
**Iteration:** 2
**Size:** M

> 本卡两阶段均已完成：阶段一只读评估（`BRIEF.md`），阶段二实施（`BRIEF-PHASE2.md`）。

---

### Step 0: 只读评估
**Status:** ✅ Completed

- [x] 读 render_v6_preprod_case 全文
- [x] 找出所有调用点
- [x] 判断每个调用点的期望写入位置
- [x] 评估方案 A/B/C 影响面

---

### Step 1: 等中枢确认
**Status:** ✅ Completed

- [x] 评估结论写入 BRIEF.md
- [x] 中枢确认选型：**方案 A2**（`manifest_root` 为目录根，写 `manifest_root/<case_id>/manifest.json`）

---

### Step 2: 实施（获授权后）
**Status:** ✅ Completed

- [x] 按确认方案改（2 处产品代码 + 4 处测试加参数 + 1 个新增回归测试）
- [x] 验证不再污染（跑完全部套件后 035/036 manifest sha256 不变）
- [x] 存量污染清洗（035/036 各删 5 条 pytest artifact_paths + 1 个对应 run_id）

---

## 验收结果

| # | 命令 | 期望 | 实测 | 结论 |
|---|---|---|---|---|
| 1 | `python -m pytest tests/v5/test_manifest_isolation.py -q -o addopts=""` | exit 0 | 2 passed in 24.78s | ✅ |
| 2 | `python -m pytest tests/r10 -q -o addopts=""` | 仍 4 failed | 4 failed, 60 passed（与 T-104 基线逐条一致） | ✅ |
| 3 | `python -m pytest -q` | exit 0, 229 passed | 229 passed in 12.03s | ✅ |
| 4 | 跑完测试 `git status --porcelain -- cases/` | 无新增改动 | 仅剩清洗本身的 2 行 `M`；两文件 sha256 与跑前一致 | ✅ |
| 5 | 035/036 不含 `pytest-of-Administrator` | 0 行 | 两文件均 0 行，全仓库 `cases/` 无命中 | ✅ |

额外：`python -m pytest tests/v5 -q -o addopts=""` → 130 passed。

---

## 改动清单

**产品代码**
- `engine/v5/preprod.py`：`render_v6_preprod_case` 新增 `manifest_root` 参数（默认 `None` = 旧行为），
  manifest 目标目录解析 + `mkdir`，读回也走目标目录（+16/−2）
- `tools/render_report_v6.py`：`render_case` 新增并透传 `manifest_root`（+11/−4）

**测试（仅加参数，未动断言）**
- `tests/r10/test_r10_ziping_career_acceptance.py:187`、`:389`
- `tests/v5/test_report_reads_l7.py:76`
- `tests/v5/test_render_report_v6.py:47`
- `tests/v5/test_manifest_isolation.py`（新增，2 条回归）

**数据清洗**
- `cases/C-2026-035-.../manifest.json`：run_ids 95→94，active→`run-a579f6371045`，artifact_paths 7→2
- `cases/C-2026-036-.../manifest.json`：run_ids 82→81，active→`run-f3ac71e1d37f`，artifact_paths 7→2

---

## Execution Log

| Timestamp | Action | Outcome |
|---|---|---|
| 2026-10-19 | Task staged | PROMPT.md and STATUS.md created |
| 2026-10-19 | Step 0 只读评估 | 读完 preprod.py 全文；确认 `case_dir = input_file.parent`，manifest 无条件写，`workspace_root` 只影响 `_display_path`。清点 6 个产品调用点（P1-P6）+ 8 组测试调用点（T1-T8） |
| 2026-10-19 | 发现卡外污染点 | `tests/v5/test_render_report_v6.py:47`（T4）用**真实** 036 case，经 `render_case` 污染 036 —— 卡里未列 |
| 2026-10-19 | 方案评估 | A 推荐（默认 None 零回归）；B 证伪；C 无干净接缝、只治标 |
| 2026-10-19 | 中枢确认 | 方案 A2（`manifest_root/<case_id>/manifest.json`） |
| 2026-10-19 | Step 2 产品代码 | `preprod.py` + `tools/render_report_v6.py` 加 `manifest_root`（默认 None 逐字节保持旧行为） |
| 2026-10-19 | Step 2 测试 | 4 处污染点加 `manifest_root=tmp_path`；新增 `test_manifest_isolation.py`（仓库 manifest 字节不变 + 默认行为不变） |
| 2026-10-19 | 回归测试初版修正 | 首版断言「tmp manifest 不含 pytest 字样」不成立（artifact 本就指向 tmp），改为断言 artifact 指向本次报告目录 |
| 2026-10-19 | 存量清洗 | 从 `git show HEAD:` 读出，只删 5 条 pytest artifact_paths + 对应 run_id；先验证 JSON round-trip 逐字节相等再写回 |
| 2026-10-19 | 验收 1-5 | 全部实跑达标；跑完 4 个套件后 035/036 sha256 与跑前一致 |
| 2026-10-19 | 产出 | `tasks/T-106/BRIEF-PHASE2.md` |

---

## Blockers

无。

## 遗留建议

- `render_v6_preprod_cases`（批量入口）未暴露 `manifest_root`：当前无调用方需要，保持最小改动。
- 默认语义仍是「渲染即写回真实 case 目录」（P1-P6 生产契约），不要改；新调用方需要隔离时显式传参。
- 历史提交里 035/036 的污染不追改，本轮只清 HEAD 存量。
