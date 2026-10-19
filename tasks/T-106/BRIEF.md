# T-106 BRIEF · 阻止测试污染 `cases/*/manifest.json`

**阶段一（只读评估）结论：推荐方案 A**（新增可选参数 `manifest_root`，默认 `None` 保持现行为；
写入目标为 `manifest_root/<case_id>/manifest.json`）。**方案 B 否决**：它既不修 bug，还会打断 4 处
现有测试并新造污染；**方案 C 不推荐**：当前代码没有可拦截的干净接缝，只能 monkeypatch
`pathlib.Path.write_text` 这种全局危险操作；测试侧「复制 case 到 tmp」是可接受的 C 变体，但只治标。

> 本阶段未执行任何 pytest（跑测试本身就会污染 manifest），全部结论来自源码阅读 +
> `git show HEAD:<path>` 只读对比。仓库基线本来就是 dirty（T-104 遗留 + 035 污染），
> 本轮未新增任何改动，详见 §8。

---

## 1. 函数事实：`render_v6_preprod_case` 四参数关系

`engine/v5/preprod.py:215-306`（`case_dir` 见 `:252`，manifest 写入见 `:293-301`）。

| 名称 | 解析方式 | 影响什么 | 不影响什么 |
|---|---|---|---|
| `input_path` | 相对则拼 `root`，再 `.resolve()`（`:226-229`） | 读 input、**决定 `case_dir = input_file.parent`（`:252`）** | — |
| `workspace_root` | `Path(...).resolve()`（`:225`） | 相对 `input_path` / `template_path` / `reports_dir` 的基准；`_display_path` 的相对化基准（`:191-195`）；`run_v5(..., workspace_root=)` | **不决定 manifest 写入位置** |
| `reports_dir` | 相对则拼 `root`（`:233-237`） | 仅当 `output_path is None` 时决定 `report_file` 目录 | 不影响 `case_dir` / manifest |
| `output_path` | 相对则拼 `root`（`:238-241`） | 显式指定报告路径（其父目录即全部 5 个 artifact 的目录） | 不影响 manifest |
| `template_path` | 相对则拼 `root`（`:230-232`） | 模板读取 | — |

关键事实：

- `manifest_path = case_dir / "manifest.json"`（`:293`），**无条件写**（`:301`），
  存在则 `bind_run`（追加 `run_id`、改写 `active_run_id`、合并 `artifact_paths`），
  不存在则 `from_run_snapshot`。
- `case_dir` 只由 `input_path` 的父目录决定；`workspace_root` 只影响字符串展示（`_display_path`）。
- 因此：**只要 `input_path` 指向真实仓库 case，无论 `reports_dir` / `workspace_root` 怎么传，
  manifest 都写回真实仓库。** 这是当前 bug 的全部机理。
- `case_dir` 还用于 `feedback_path`（`:253`，只读展示）与报告里的相对链接（`:277-278`），
  这些是**读**，与本卡无关；方案 A 不应改动它们。
- 批量入口 `render_v6_preprod_cases`（`:309-332`）把 `workspace_root=root`、`reports_dir=target_dir`
  透传给单案函数，自身不碰 manifest。

---

## 2. 全部调用点清单

「直接」= 直接调用 `render_v6_preprod_case`；「间接」= 经 `render_v6_preprod_cases` /
`tools.render_report_v6.render_case(s)` 到达。

### 2.1 产品代码（生产语义，manifest 应写真实 case 目录）

| # | 调用点 | `workspace_root` | `reports_dir` / `output_path` | manifest 现状落点 | 期望落点 | 判定 |
|---|---|---|---|---|---|---|
| P1 | `engine/v5/preprod.py:325`（`render_v6_preprod_cases` 内） | `root`（调用方给的） | `reports_dir=target_dir` | 各 input 的 `case_dir` | 真实 case 目录（登记运行） | 正确，保持 |
| P2 | `engine/application/production_service.py:166`（`_run_existing_job`） | `self.workspace_root` | `reports_dir=normalized.reports_dir or workspace_root/"reports"` | 真实 case 目录 | 真实 case 目录（生产登记） | 正确，保持 |
| P3 | `tools/render_report_v6.py:40`（`render_case`） | `REPO_ROOT`（硬编码） | `output_path=参数`（可为 `None`，此时报告落 `reports/`） | 真实 case 目录 | 真实 case 目录（CLI 登记） | 正确，保持 |
| P4 | `tools/render_report_v6.py:66`（`render_cases`）→ P1 | `REPO_ROOT` | `output_dir=output_dir or REPO_ROOT/"reports"` | 真实 case 目录 | 真实 case 目录 | 正确，保持 |
| P5 | `tools/render_report_v6.py:86`（CLI 单案）→ P3 | 同上 | `--output` 或默认 | 真实 case 目录 | 真实 case 目录 | 正确，保持 |
| P6 | `tools/render_report_v6.py:94`（CLI 批量）→ P4 | 同上 | `--output-dir` | 真实 case 目录 | 真实 case 目录 | 正确，保持 |

> P2 的下游读者：`tools/feedback_ingest.py:755-775` 会读 `case_dir/manifest.json` 的
> `artifact_paths` 定位 v5 产物（相对路径按 `REPO_ROOT` 解析，候选不存在时回退 glob）。
> 这说明「manifest 属于真实 case 目录」是有消费方的设计契约，A 方案必须保留默认行为。

### 2.2 测试代码

| # | 调用点 | `input_path` | `workspace_root` | `reports_dir` / `output_path` | manifest 现状落点 | 期望落点 | 是否污染 |
|---|---|---|---|---|---|---|---|
| T1 | `tests/r10/test_r10_ziping_career_acceptance.py:183`（`test_falsifier_report_keeps_all_fifteen_judgment_layers`） | 真实 `cases/C-2026-035-.../input.md` | `"."` | `reports_dir=tmp_path` | 仓库 `035/manifest.json` | tmp | **污染 035** |
| T2 | `tests/r10/test_r10_ziping_career_acceptance.py:388`（`test_preprod_builds_r10_run_from_exact_input_text`） | 同上（真实） | `"."` | `reports_dir=tmp_path` | 仓库 `035/manifest.json` | tmp | **污染 035** |
| T3 | `tests/v5/test_report_reads_l7.py:75`（`test_preprod_career_report_matches_l7`） | 真实 `035/input.md` | `"."` | `reports_dir=tmp_path` | 仓库 `035/manifest.json` | tmp | **污染 035** |
| T4 | `tests/v5/test_render_report_v6.py:47`（`test_render_report_v6_includes_marriage_timing_for_c2026036`，经 `tools.render_case`） | **真实** `cases/C-2026-036-.../input.md`（`:44`） | `REPO_ROOT`（P3 硬编码） | `output_path=tmp_path/"c2026036-v6.md"` | 仓库 `036/manifest.json` | tmp | **污染 036（卡里未列，本阶段新发现）** |
| T5 | `tests/v5/test_render_report_v6.py:60` | tmp 拷贝（`_copy_case_input`，`:19-22`，忽略 manifest.json） | `REPO_ROOT` | `output_path=tmp_path/...` | tmp 拷贝目录 | tmp | 否 |
| T6 | `tests/v5/test_render_report_v6.py:133`（`render_cases`） | tmp 拷贝 | `REPO_ROOT` | `output_dir=tmp_path/"batch"` | tmp 拷贝目录 | tmp | 否 |
| T7 | `tests/v5/test_render_report_v6.py:157`（CLI `main`） | tmp 拷贝 | `REPO_ROOT` | `--output tmp_path/...` | tmp 拷贝目录 | tmp | 否 |
| T8 | `tests/v5/test_v5_prediction_feedback.py:28/45/57/72/99/113`（6 处，均经 `render_case`） | tmp 拷贝 | `REPO_ROOT` | `output_path=tmp_path/...` | tmp 拷贝目录 | tmp | 否 |

补充事实：

- T5/T8 里 `test_render_report_v6.py:102-107` **断言** `case_input.parent/"manifest.json"` 存在且
  `active_run_id` 等于本次 run —— 这条断言是方案 B 的直接反证（见 §4.2）。
- `tests/test_production_service.py` 里 3 处 `render_v6_preprod=True`：`:81` 只测 cache key（不渲染）、
  `:185` 只测 `_collect_artifacts`（不渲染）、`:397` 实际渲染但 `workspace_root=tmp_path` 且 case 在
  tmp 下 → manifest 落 tmp，不污染。故 P2 的测试面是干净的。
- `tests/asof/*` 里出现的 `engine.v5.preprod` 只是「禁止导入」清单（如
  `tests/asof/test_future_projection.py:943`），不是调用点。

---

## 3. 污染现状（只读核实，供中枢决策）

- 被 git 跟踪的 manifest 共 **10** 个；其中 **2 个已含 pytest 临时路径**：
  - `cases/C-2026-035-.../manifest.json`：HEAD 里已有 **5 行** `pytest-of-Administrator/...`（来自
    `test_preprod_career_report_mat0`）；工作区又比 HEAD 多 **4 个 run_id**（95 vs 91），
    `active_run_id` 由 `run-666523d21260` 变为 `run-38eaf7f607a7`，`artifact_paths` 全指向
    `pytest-697/test_preprod_builds_r10_run_fr0/...`。
  - `cases/C-2026-036-.../manifest.json`：HEAD 里已有 **5 行** `pytest-of-Administrator/...`
    （来自 `test_render_report_v6_includes0`），即 **T4 的污染已经入库**；工作区与 HEAD 一致。
  - 其余 8 个 manifest 干净（0 行 pytest 路径）。
- 结论：污染不是「跑一次测试才出现」的偶发，**HEAD 已经带着两次测试污染的产物**。阶段二修好写入路径后，
  这 2 个文件的既有污染仍需中枢决定如何清洗（本卡 Do NOT 禁止改 `cases/**/manifest.json`，故只上报不处理）。

---

## 4. 三方案影响面对比

### 4.1 对比表

| 维度 | **A：新增 `manifest_root`（默认 None）** | **B：`workspace_root` 语义扩展** | **C：测试侧 monkeypatch 拦截写入** |
|---|---|---|---|
| 改动点 | `engine/v5/preprod.py`：签名 +1 参数；manifest 目标目录解析 + `mkdir`（约 +8/-2 行）。可选：`tools/render_report_v6.render_case` 透传该参数（+1 参数，默认 None） | 同文件：把 `manifest_path = case_dir/"manifest.json"` 改为跟随 `root`（例如 `root/"cases"/case_id/"manifest.json"`） | 产品代码 0 行；测试侧每个污染点各加一段 patch |
| 影响调用方 | **默认路径零影响**：P1-P6、T5-T8 全部不变；仅显式传参的调用方改变 | **P1/P2/P3 全部改变**：凡 input 不在 `workspace_root/cases/<id>` 下的调用都会改落点 | 只影响被 patch 的测试；其他测试/脚本/CI 继续污染 |
| 回归风险 | 极低（新参数默认不生效）；需保证 `manifest_root` 下目录可创建、读回语义用目标目录 | **高且已可证伪**（见 4.2）：T5/T8 的 manifest 断言会失败，并把 manifest 写进仓库 001；T1-T3 因 `workspace_root="."` 解析为仓库根而**完全不修 bug** | 中：`Path.write_text` 是全局 API，patch 面过宽易误伤；每个新测试要重复 patch，漏一个就继续污染 |
| 向后兼容 | 是（`None` 即旧行为，纯新增） | 否（默认语义改变） | 表面兼容，但把「写 manifest」变成测试私有约定，产品契约未修 |
| 是否根治 | 是（产品层提供隔离能力） | 否（bug 不修，还多一处错位） | 否（治标；新调用方仍会污染） |
| 授权范围 | `engine/v5/preprod.py` + 4 个测试文件（含卡里未列的 T4） | `engine/v5/preprod.py` + 4 个测试文件 + 需重写 T5/T8 的断言 | 4 个测试文件（只改测试，但改动更脏） |
| 失败模式 | 传参写错目录 → 报告与 manifest 分离（可见、可断言） | 生产 manifest 被写去错误 case；测试断言失败；仓库新增污染 | patch 失效（pytest 版本/写法变化）后静默回到污染 |

### 4.2 方案 B 的反证（关键证据，不是推测）

1. **对 T1-T3 无效**：三处都传 `workspace_root="."`，`root = Path(".").resolve()` 就是仓库根。
   若 B 让 manifest 跟随 `root`，落点仍是 `仓库/cases/035/manifest.json` —— **bug 原样保留**。
   若 B 定义成 `root/"manifest.json"`，则会往仓库根写一个全局 manifest，更糟。
2. **对 T5/T8 是回归**：这两组测试用 `tools.render_case`，而 `render_case` 硬编码
   `workspace_root=REPO_ROOT`（`tools/render_report_v6.py:44`）。B 一旦让 manifest 跟随 workspace_root，
   manifest 会从「tmp 拷贝目录」搬到「仓库 `cases/C-2026-001-.../`」：
   - `tests/v5/test_render_report_v6.py:102-103` 会因 tmp 下 manifest 不存在而 `FileNotFoundError`；
   - 同时把**原本隔离良好的 6 个测试**变成新的污染源（001 的 manifest 会被改写）。
3. **对 P2 无语义收益**：生产服务本来就把 input 放在 `workspace_root/cases/<id>` 下，B 的落点与现状相同，
   只是多绕一层字符串推导。

### 4.3 方案 C 的反证

- 当前代码**没有可拦截的接缝**：`case_dir` 是函数内局部变量（`:252`），manifest 写入是
  `manifest_path.write_text(...)`（`:301`），既没有 `_manifest_path()` 之类可替换的钩子，
  也没有注入点。要「不改产品代码」地拦截，只能：
  - patch `pathlib.Path.write_text` 并对路径后缀做守卫 → 影响进程内所有写文件，风险面远大于收益；
  - patch `preprod.V5CaseManifest.from_run_snapshot/bind_run` → 只能改内容，**拦不住写**；
  - 改 cwd → 无效，`input_file` 已 `.resolve()` 成绝对路径。
- 更干净的 C 变体 **C′：测试把 case 目录复制到 `tmp_path` 再渲染**（T5/T8 已在用这个模式，
  `test_render_report_v6.py:19-22`）。它不改产品代码、不 patch 全局 API，但：
  - 每个污染点都要加复制逻辑（4 处，035/036 各 24-25 KB，成本可忽略）；
  - 测试不再覆盖「真实仓库路径渲染」这条路径，manifest 的 `case_path` 变成 tmp 路径；
  - **对未来新增测试/脚本零保护**，同类污染会复发（T4 就是「有人新写了一个用真实 case 的测试」造成的）。

---

## 5. 选型建议

**选 A，形态建议 A2：`manifest_root` 是目录根，写入 `manifest_root/<case_id>/manifest.json`。**

理由（按权重）：

1. **唯一同时满足「修 bug + 零默认回归」的选项**：默认 `None` 时 `manifest_dir = case_dir`，P1-P6 与
   T5-T8 的代码路径逐字节不变，默认门禁（229 passed，`pyproject.toml` 的 testpaths 不含 tests/v5、tests/r10）
   不可能受影响。
2. **B 已被证伪**：既不修 T1-T3，又会打断 T5/T8 并新造 001 污染（§4.2），不符合「除非能证明所有调用方
   都期望这个语义」的准入门槛 —— 现有证据恰好证明**不是**所有调用方都期望。
3. **C/C′ 只治标**：产品契约仍是「渲染即写回仓库」，T4 已经证明新测试会再次踩坑。
4. **A2 优于 A1（`manifest_root/manifest.json`）**：A2 与 `cases/<case_id>/manifest.json` 同构，
   批量渲染/多 case 共用一个 tmp 根时不会互相覆盖；测试侧不需要读 manifest，故不增加断言成本。

**实现要点（阶段二）**：

```python
def render_v6_preprod_case(
    input_path, *, output_path=None, reports_dir=None,
    template_path="templates/report-v6.md", workspace_root=".",
    manifest_root: str | Path | None = None,
) -> tuple[Path, Path]:
    ...
    case_dir = input_file.parent
    if manifest_root is None:
        manifest_dir = case_dir
    else:
        manifest_dir = Path(manifest_root)
        if not manifest_dir.is_absolute():
            manifest_dir = root / manifest_dir
        manifest_dir = manifest_dir / case_id      # A2：与 cases/<case_id>/ 同构
    manifest_dir.mkdir(parents=True, exist_ok=True)  # case_dir 必存在，manifest_root 不一定
    manifest_path = manifest_dir / "manifest.json"
    if manifest_path.exists():                       # 读回也走目标目录，避免把仓库 run_ids 带进 tmp
        manifest = V5CaseManifest.from_json(...).bind_run(snapshot)
    else:
        manifest = V5CaseManifest.from_run_snapshot(
            snapshot, case_path=_display_path(case_dir, workspace_root=root),  # 仍记录 case 真实位置
        )
    manifest_path.write_text(manifest.to_json(), encoding="utf-8")
```

**阶段二测试改动清单（4 处，均在 File Scope 内）**：

1. `tests/r10/test_r10_ziping_career_acceptance.py:183-187` → 加 `manifest_root=tmp_path`
2. `tests/r10/test_r10_ziping_career_acceptance.py:388` → 加 `manifest_root=tmp_path`
3. `tests/v5/test_report_reads_l7.py:75-77` → 加 `manifest_root=tmp_path`
4. `tests/v5/test_render_report_v6.py:47`（**卡里未列，必须补**）→ 二选一：
   - 给 `tools/render_report_v6.render_case` 加透传参数 `manifest_root=None` 后传 `manifest_root=tmp_path`（推荐，产品侧 +1 可选参数，仍向后兼容）；或
   - 改用 `_copy_case_input(tmp_path)` 渲染 tmp 拷贝（零产品改动，但改变该测试覆盖的路径）。

**可选加固（建议但非必需）**：新增 `tests/v5/test_manifest_isolation.py`：用 `manifest_root=tmp_path`
渲染真实 case，断言 `cases/035/manifest.json` 的字节前后不变 —— 把本卡的修复固化成回归测试。

**未决/需中枢决策**：

- 035、036 两个 manifest **在 HEAD 里就带着 pytest 路径**（§3）。修完写入路径后，这 2 个文件的既有污染
  要不要清洗、由谁清洗（本卡 Do NOT 禁止改 `cases/**/manifest.json`，且不能用 `git checkout` 恢复）。
- `render_v6_preprod_cases` 是否也暴露 `manifest_root`（当前批量入口无此需求，建议暂不暴露，保持最小改动）。

---

## 6. 三方案一句话结论

- **A（推荐）**：纯新增、默认不变、能根治；成本是 4 处测试加参数（含卡里漏掉的 T4）。
- **B（否决）**：不修 bug（T1-T3 的 `workspace_root="."` 就是仓库根），并破坏 T5/T8 的隔离与断言。
- **C（不推荐）**：无可拦截接缝，monkeypatch 全局写文件风险大；C′（测试复制 case）可行但只治标。

---

## 7. 只读评估已核对的源码范围

`engine/v5/preprod.py`（全文 332 行）、`engine/v5/domain.py:502-580`（`V5CaseManifest` / `bind_run`）、
`engine/application/production_service.py`、`engine/application/_production_helpers.py`、
`tools/render_report_v6.py`、`tools/feedback_ingest.py:755-775`、
`tests/r10/test_r10_ziping_career_acceptance.py`、`tests/v5/test_report_reads_l7.py`、
`tests/v5/test_render_report_v6.py`、`tests/v5/test_v5_prediction_feedback.py`、
`tests/test_production_service.py`、`pyproject.toml`。
调用点检索方式：`grep -rn "render_v6_preprod_case|render_case\(|render_cases\(" --include=*.py engine tools tests`
（排除 `plans/`、`META/` 中的历史文档引用）。

---

## 8. 只读合规与验证记录

- **未执行** pytest / 渲染命令（会写 manifest，违反阶段一只读）。
- 未修改 `engine/`、`tools/`、`tests/`、`cases/`、`pyproject.toml`；未执行任何 git 写操作。
- 本轮仅新增本文件（`tasks/T-106/BRIEF.md`）并更新 `tasks/T-106/STATUS.md` 的 Step 0 状态。
- 基线（评估前后一致）：

```
$ git status --porcelain            # 8 行，全部是评估前既有
 M AGENTS.md
 M cases/C-2026-035-乾-戊辰癸亥甲戌庚午/manifest.json
 D tasks/.gitkeep
 M tests/r10/test_r10_ziping_career_acceptance.py
?? tasks/T-104/  ?? tasks/T-105/  ?? tasks/T-106/  ?? tasks/_archive/

$ git status --porcelain -- cases/  # 1 行（评估前既有污染，未新增）
 M cases/C-2026-035-乾-戊辰癸亥甲戌庚午/manifest.json
```

> 注：卡里「`git status --porcelain` 无新增改动 / `git diff --stat` 为空」在当前仓库**不可能字面成立**——
> T-104 遗留的测试改动与 035 的既有污染都在。本阶段的实际达标口径是：**评估前后 git 状态逐行一致，
> 无新增条目、无新增 diff 行**。
