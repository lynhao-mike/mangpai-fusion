# T-106 · 阻止测试污染 `cases/*/manifest.json`

## Review Level: 3

> 定级理由：改动落在 `engine/v5/preprod.py`（产品代码），且涉及**路径解析语义**。
> 改错会让所有调用方（CLI、报告链、测试）行为漂移，属于不可逆风险区。
> 必须独立评审，不得自测自过。

## Context（中枢只读勘察已确证，Worker 无需重复勘察）

**现象：** 跑 `tests/r10` 会改写 `cases/C-2026-035-乾-戊辰癸亥甲戌庚午/manifest.json`，
追加新的 `run_id`、改写 `active_run_id`、把 `artifact_paths` 指向 pytest 临时目录。

**根因链（已核实 2026-10-19）：**

1. `engine/v5/preprod.py:293-301` 的 `render_v6_preprod_case` **无条件**把运行结果
   写回 `case_dir / "manifest.json"`：

   ```python
   manifest_path = case_dir / "manifest.json"
   if manifest_path.exists():
       manifest = V5CaseManifest.from_json(...).bind_run(snapshot)
   else:
       manifest = V5CaseManifest.from_run_snapshot(...)
   manifest_path.write_text(manifest.to_json(), encoding="utf-8")
   ```

   **这是设计意图**——`render_v6_preprod_case` 的职责之一就是登记运行。

2. `case_dir` 由 `input_file` 的父目录决定；而 `workspace_root` 只影响
   `_display_path`（用于生成相对路径字符串），**不影响写入位置**。

3. 测试调用时传 `workspace_root="."`：

   ```python
   render_v6_preprod_case(
       "cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md",
       reports_dir=tmp_path,      # ← 报告已隔离到 tmp
       workspace_root=".",        # ← 但 manifest 写回真实仓库
   )
   ```

   **矛盾点**：`reports_dir=tmp_path` 说明测试本意是要隔离副作用，
   但 manifest 这条路径没被隔离。

**受影响的测试（已确认）：**
- `tests/r10/test_r10_ziping_career_acceptance.py:183`、`:388`
- `tests/v5/test_report_reads_l7.py:75`

**受影响的 manifest（已确认 10 个被 git 跟踪）：**
`git ls-files 'cases/**/manifest.json'` → 10 个，与磁盘上的 10 个一致。

## Objective

让 `render_v6_preprod_case` 的 manifest 写入**尊重隔离意图**：当调用方已把
`reports_dir` 指向临时目录时，manifest 不应写回仓库内的 `cases/`。

## 方案选项（Worker 需先评估，在 BRIEF 里说明选型理由）

**方案 A：新增可选参数 `manifest_root`（推荐先评估）**
- 默认 `None` 时保持现有行为（向后兼容）
- 调用方显式传 `manifest_root=tmp_path` 时，manifest 写到该目录
- 优点：不改默认行为，零回归风险；测试只需加一个参数
- 缺点：测试要改（属保护区，需授权）

**方案 B：`workspace_root` 语义扩展**
- 让 manifest 写入跟随 `workspace_root`
- 风险：**会改变所有现有调用方的行为**，包括 CLI 和报告链
- 除非能证明所有调用方都期望这个语义，否则不采用

**方案 C：测试侧用 monkeypatch 拦截写入**
- 不改产品代码，只改测试
- 缺点：治标不治本，其他测试/脚本仍会污染

**Worker 必须先只读评估 A/B/C，说明各自影响面，再等中枢确认。不要直接动手。**

## File Scope

**阶段一（只读评估）**：不改任何文件，只产出评估结论。

**阶段二（获授权后）**：
- `engine/v5/preprod.py`（若选 A 或 B）
- `tests/r10/test_r10_ziping_career_acceptance.py`、`tests/v5/test_report_reads_l7.py`（若选 A 或 C）

**只读参考**：
- `engine/v5/domain.py`（`V5CaseManifest` 定义，`bind_run` 在 534 行）
- `pyproject.toml`（确认 r10/v5 是否在 testpaths 内）

## Steps

### Step 0: 只读评估（本卡第一阶段）

- [ ] 读 `render_v6_preprod_case` 全文，确认 `case_dir` / `workspace_root` /
      `reports_dir` 三者关系
- [ ] 找出**所有**调用 `render_v6_preprod_case` 的地方（含 engine/、tools/、tests/）
- [ ] 对每个调用点判断：它期望 manifest 写到哪里？
- [ ] 评估方案 A/B/C 的影响面，给出选型建议

### Step 1: 等中枢确认选型

- [ ] 把评估结论写进 BRIEF.md，等中枢回复

### Step 2: 实施（获授权后）

- [ ] 按确认的方案改
- [ ] 验证不再污染

## Completion Criteria

**阶段一（本卡当前只要求完成这一步）：**

| # | 命令 | 期望 |
|---|---|---|
| 1 | `git status --porcelain` | **无新增改动**（只读评估） |
| 2 | `git diff --stat` | **空** |
| 3 | `tasks/T-106/BRIEF.md` 存在 | 含全部调用点清单 + 三方案影响面 + 选型建议 |

**阶段二（获授权后追加）：**

| # | 命令 | 期望 |
|---|---|---|
| 4 | 跑 `python -m pytest tests/r10 tests/v5 -q -o addopts=""` | 完成后 `git status --porcelain -- cases/` **为空** |
| 5 | `python -m pytest -q` | **exit 0**，229 passed（默认门禁不回归） |

## Do NOT

- **阶段一禁止修改任何文件**——只读评估
- **禁止用 `git checkout` 恢复污染**（违反执行规则 3）；如需恢复用 `git show HEAD:<path>` 重写
- **禁止修改 `cases/**/manifest.json`**——那是数据不是代码
- **禁止修改任何测试的断言**
- **禁止执行 `git commit` / `checkout` / `stash` / `reset` / `clean`**
- **禁止选方案 B 而不论证**——它改变所有调用方行为，必须有充分证据
- 禁止读取 File Scope 之外的文件

## Deliverables

- `tasks/T-106/BRIEF.md`：调用点清单、三方案影响面对比、选型建议
- 更新 `tasks/T-106/STATUS.md`
