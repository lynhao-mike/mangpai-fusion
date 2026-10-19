# T-106: 阻止测试污染 manifest — Status

**Status:** 🟡 阶段一完成，等待中枢确认选型
**Current Step:** Step 0 ✅ 完成 / Step 1 等待中枢回复
**Last Updated:** 2026-10-19
**Iteration:** 1
**Size:** M

> ⚠️ 本卡分两阶段。**阶段一只读评估**，不得修改任何文件。
> 阶段二需中枢确认方案后才授权。

---

### Step 0: 只读评估
**Status:** ✅ Completed

- [x] 读 render_v6_preprod_case 全文
- [x] 找出所有调用点
- [x] 判断每个调用点的期望写入位置
- [x] 评估方案 A/B/C 影响面

---

### Step 1: 等中枢确认
**Status:** 🔵 In Progress（评估结论已写入 BRIEF.md，已发回中枢）

- [x] 评估结论写入 BRIEF.md
- [ ] 等中枢回复选型

---

### Step 2: 实施（获授权后）
**Status:** ⬜ Not Started

- [ ] 按确认方案改
- [ ] 验证不再污染

---

## Execution Log

| Timestamp | Action | Outcome |
|---|---|---|
| 2026-10-19 | Task staged | PROMPT.md and STATUS.md created |
| 2026-10-19 | Step 0 只读评估 | 读完 preprod.py 全文；确认 `case_dir = input_file.parent`（:252），manifest 无条件写（:293-301），`workspace_root` 只影响 `_display_path`。清点 6 个产品调用点（P1-P6）+ 8 组测试调用点（T1-T8） |
| 2026-10-19 | 发现卡外污染点 | `tests/v5/test_render_report_v6.py:47`（T4）用**真实** 036 case + `output_path=tmp_path`，经 `render_case`（`workspace_root=REPO_ROOT`）污染 036 —— 卡里未列 |
| 2026-10-19 | 发现 HEAD 已带污染 | 035、036 的 manifest 在 HEAD 里各有 5 行 pytest 临时路径（035 来自 `test_preprod_career_report_mat0`，036 来自 `test_render_report_v6_includes0`） |
| 2026-10-19 | 方案评估 | A 推荐（默认 None 零回归）；B 证伪（T1-T3 的 `workspace_root="."` 即仓库根 → 不修 bug，且会打断 T5/T8 的 manifest 断言并新造 001 污染）；C 无干净接缝、只治标 |
| 2026-10-19 | 产出 | `tasks/T-106/BRIEF.md`（调用点清单 + 三方案对比表 + 选型建议 + 阶段二改动清单） |

---

## Blockers

- **待中枢确认选型**（阶段二授权）。推荐方案 A（`manifest_root`，默认 None）。
- **待中枢决策**：035、036 两个 manifest 在 HEAD 里已含 pytest 临时路径，修完写入路径后是否需要清洗、
  由谁清洗（本卡禁止改 `cases/**/manifest.json`，且禁止 `git checkout` 恢复）。
