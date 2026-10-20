# T-106 BRIEF · 阶段二（方案 A2 实施）

**结论：PASS** — 方案 A2 已按中枢确认口径落地；4 处测试调用点加 `manifest_root=tmp_path`，
新增回归测试 `tests/v5/test_manifest_isolation.py`，035/036 存量污染已按「只删 pytest 条目」清洗。
验收 1-5 全部实跑达标（详见 §5）。

> 本轮所有结论均来自实跑，非推断。跑完 4 个套件（默认门禁 / tests/r10 / tests/v5 / 新增回归）
> 之后，035 与 036 的 manifest **sha256 逐字节不变**（§5.4）。

---

## 1. 产品代码改动（2 处）

### 1.1 `engine/v5/preprod.py`（+16/−2）

`render_v6_preprod_case` 签名新增 `manifest_root: str | Path | None = None`（关键字专用，排在最后，
不影响任何位置参数调用），manifest 目标目录解析改为：

```python
if manifest_root is None:
    manifest_dir = case_dir
else:
    manifest_dir = Path(manifest_root)
    if not manifest_dir.is_absolute():
        manifest_dir = root / manifest_dir
    manifest_dir = manifest_dir / case_id      # A2：与 cases/<case_id>/ 同构
manifest_dir.mkdir(parents=True, exist_ok=True)
manifest_path = manifest_dir / "manifest.json"
```

三个要点：

1. **默认逐字节保持现行为**：`manifest_root is None` 时 `manifest_dir = case_dir`，
   与原 `manifest_path = case_dir / "manifest.json"` 完全等价；新增的 `mkdir` 对已存在的
   `case_dir` 是 no-op（`exist_ok=True`）。
2. **读回也走目标目录**：`manifest_path.exists()` 判断与 `from_json` 读取都在 `manifest_dir` 下，
   因此不会把仓库里的 90+ 个历史 `run_ids` 带进 tmp，也不会触发 `bind_run` 的 case_id 校验失败。
3. **`case_path` 仍记录真实位置**：`from_run_snapshot(case_path=_display_path(case_dir, workspace_root=root))`
   未改动，写入 tmp 的 manifest 里 `case_path` 仍是 `cases/<case_id>`。

### 1.2 `tools/render_report_v6.py`（+11/−4）

`render_case` 新增同名可选参数并透传给 `render_v6_preprod_case(..., manifest_root=manifest_root)`。
默认 `None` → CLI 生产语义不变（P3/P5 仍写真实 case 目录）。`render_cases` / CLI 入口未暴露该参数
（批量入口当前无需求，保持最小改动，与 BRIEF §5「未决」的建议一致）。

---

## 2. 测试改动（4 处，仅加参数，未动任何断言）

| # | 位置 | 改动 |
|---|---|---|
| T1 | `tests/r10/test_r10_ziping_career_acceptance.py:187` | `render_v6_preprod_case(..., manifest_root=tmp_path)` |
| T2 | `tests/r10/test_r10_ziping_career_acceptance.py:389` | 同上（折行以适配行长） |
| T3 | `tests/v5/test_report_reads_l7.py:76` | 同上 |
| T4 | `tests/v5/test_render_report_v6.py:47` | `render_case(..., manifest_root=tmp_path)` |

T5-T8（tmp 拷贝路径）未改：它们本就把 case 复制到 tmp，manifest 落 tmp 拷贝目录，无污染。

---

## 3. 新增回归测试 `tests/v5/test_manifest_isolation.py`

两条测试（2 passed）：

1. `test_render_with_manifest_root_leaves_repo_manifest_untouched`
   - 渲染前取 `cases/035/manifest.json` 的 `read_bytes()`；
   - 用 `manifest_root=tmp_path/"manifests"` 渲染真实 case；
   - 断言仓库 manifest **字节完全不变**；
   - 断言 `tmp/manifests/<case_id>/manifest.json` 存在、`case_id` 正确、`run_ids` 只有 1 条、
     `case_path == "cases/<case_id>"`（真实位置）；
   - 断言 `artifact_paths["report"]` 指向本次 tmp 报告目录、`artifact_paths["input"]` 仍是仓库相对路径。
2. `test_manifest_root_default_keeps_writing_to_case_dir`
   - 把 035 拷到 tmp（忽略 manifest.json），**不传** `manifest_root` 渲染；
   - 断言 manifest 写回拷贝的 case 目录 —— 固化「默认行为不变」这一契约。

> 注：初版曾加过「tmp manifest 内不含 `pytest-of-Administrator` 字样」的断言，实测不成立且不该成立
> ——`artifact_paths` 本来就该指向本次运行的实际产物路径（在 pytest tmp 下）。已改为断言
> 「artifact 指向本次报告目录」，这才是隔离的真正判据。

---

## 4. 存量污染清洗（独立步骤）

### 4.1 口径与实现

- 用 `git show HEAD:<path>` 读出 HEAD 版本（**未用 `git checkout`**，符合执行规则 3）；
- 只删两样东西：`artifact_paths` 中值含 `pytest-of-Administrator` 的条目，以及写下这些条目的 `run_id`；
- `case_path`、`run_ids` 其余全部成员、`input` / `feedback` 两个真实条目、`metadata` 全部原样保留；
- 写回用 `json.dumps(..., ensure_ascii=False, indent=2)` —— 已先验证该序列化对两个 HEAD 原文
  **逐字节 round-trip 相等**（035: 3589→3589，036: 3097→3097），故 diff 里只有真正的删改行。

### 4.2 为什么连 run_id 一起删

`run_id` 由 `sha256(case_id|schema_version|output_hash)` 派生（`engine/v5/domain.py:415-416`），
与报告路径无关；而 `artifact_paths` 是 `bind_run` 每次**整键覆盖**的。
HEAD 里那 5 个 pytest 路径正是 `active_run_id` 这次运行写下的，两者是同一事件的产物：

- 035：`active_run_id` 由 `run-666523d21260`（干净，指向 `reports/`）变成 `run-38eaf7f607a7`（pytest）；
- 036：`active_run_id` 由 `run-60e7088aeef4`（干净，指向 `reports/`）变成 `run-ee90e88159f1`（pytest）。

保留这些 run_id 会留下「有 run_id 但无任何 artifact 指向它」的悬空登记；且这两个 run_id
在全仓库（除 manifest 自身）**无任何引用**（`grep -rl` 已验证）。故一并删除，
`active_run_id` 回退到剩余最后一条真实 run_id。

### 4.3 清洗结果

| case | run_ids | active_run_id | artifact_paths | pytest 行 |
|---|---|---|---|---|
| 035 | 95 → **94** | `run-38eaf7f607a7` → **`run-a579f6371045`** | 7 → **2**（input/feedback） | 5 → **0** |
| 036 | 82 → **81** | `run-ee90e88159f1` → **`run-f3ac71e1d37f`** | 7 → **2**（input/feedback） | 5 → **0** |

`git diff --numstat -- cases/`：两个文件各 `+2/−8`（删 5 条 pytest 路径 + 1 个 run_id + 改 1 行 active_run_id；
加 1 条 run_ids 收尾逗号变化 + 1 行新 active_run_id）。**没有整文件覆盖**。

### 4.4 影响面核对

`tools/feedback_ingest.py:755-775` 是 manifest `artifact_paths` 的唯一消费方：读不到对应键时返回 `None`，
随后回退到 `case_dir.glob(pattern)` 按 mtime 找产物（`_v5_artifact_candidates`）。
删掉指向不存在 tmp 目录的条目**不会让任何读取方退化**——这些路径本来就不存在（pytest tmp 早已销毁），
删后行为等价于「manifest 无该键」，回退分支照常工作。

---

## 5. 验收实跑记录

### 5.1 验收 1 — 新增回归

```text
$ python -m pytest tests/v5/test_manifest_isolation.py -q -o addopts=""
2 passed in 24.78s          → exit 0 ✅
```

### 5.2 验收 2 — tests/r10 不回归

```text
$ python -m pytest tests/r10 -q -o addopts=""
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_falsifier_career_information_is_not_thinner_than_r6
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_career_l7_text_is_serialized_verbatim
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_falsifier_career_l7_structures_all_r6_school_evidence_losslessly
FAILED tests/r10/test_r10_ziping_career_acceptance.py::test_falsifier_career_report_columns_and_conflict_disappear_without_l7
4 failed, 60 passed in 45.24s    → ✅ 仍 4 failed（与 T-104 基线逐条一致，未变成 5）
```

这 4 条是 T-104 遗留的 R6 基线问题（事业 L2 依据数量 264<270、`待接入` 占位符未填），与本卡无关。

### 5.3 验收 3 — 默认门禁

```text
$ python -m pytest -q
229 passed in 12.03s          → exit 0 ✅
```

### 5.4 验收 4 — 跑完测试 cases/ 无新增改动

跑完全部 4 个套件后对 035/036 取 sha256，与跑前快照**逐字节相同**：

```text
05bab83801071b4068126e99df8e3ef5e8620847182dddc6b6c813a4924e3835 *cases/C-2026-035-.../manifest.json
cf6f2c479968ef4982682b9cc84598e9dd896c353ba5a8cc09ce9e43a20be3bc *cases/C-2026-036-.../manifest.json
```

`git status --porcelain -- cases/` 仅剩本轮清洗带来的 2 行 `M`（预期内，是清洗本身），
**无任何测试产生的新增改动**。✅

### 5.5 验收 5 — 污染标记清零

```text
$ grep -c "pytest-of-Administrator" cases/C-2026-035-.../manifest.json   → 0
$ grep -c "pytest-of-Administrator" cases/C-2026-036-.../manifest.json   → 0
```

全仓库 `grep -rl "pytest-of-Administrator" cases/` 无输出。✅

### 5.6 额外回归 — tests/v5

```text
$ python -m pytest tests/v5 -q -o addopts=""
130 passed, 1 warning in 207.46s   → ✅（含新增 2 条；warning 是既有的 dual_engine_adapter 弃用提示）
```

---

## 6. 改动清单（本轮全部）

| 文件 | 类型 | 行数 |
|---|---|---|
| `engine/v5/preprod.py` | 产品 | +16 / −2 |
| `tools/render_report_v6.py` | 产品 | +11 / −4 |
| `tests/r10/test_r10_ziping_career_acceptance.py` | 测试（加参数） | +5 / −1 |
| `tests/v5/test_report_reads_l7.py` | 测试（加参数） | +1 / −1 |
| `tests/v5/test_render_report_v6.py` | 测试（加参数） | +1 / −1 |
| `tests/v5/test_manifest_isolation.py` | 测试（新增） | +81 |
| `cases/C-2026-035-.../manifest.json` | 数据清洗 | +2 / −8 |
| `cases/C-2026-036-.../manifest.json` | 数据清洗 | +2 / −8 |
| `tasks/T-106/BRIEF-PHASE2.md` | 文档（新增） | — |
| `tasks/T-106/STATUS.md` | 文档（更新） | — |

**未触碰**：`BLIND_TOPIC_DOMAINS`、`condition_evaluator.py`（属 T-108）、任何测试断言、
`pyproject.toml`、`engine/v5/domain.py`。

> 工作区里另有 `.gitignore` 修改与 `theory/_light_index.json` 等删除，以及 `tasks/T-107/`、
> `tasks/T-108/` 两个未跟踪目录 —— 均为其他任务（T-107）在并行进行，**不是本轮改动**，未触碰。

---

## 7. 遗留与建议

1. **`render_v6_preprod_cases`（批量）未暴露 `manifest_root`**。当前无调用方需要；若将来批量渲染
   也要隔离，只需同样透传一个参数即可（单案函数已支持）。
2. **默认语义仍是「渲染即写回真实 case 目录」**，这是 P1-P6 的生产契约，不要改。
   新增调用方若需要隔离副作用，请显式传 `manifest_root`。
3. **`cases/*/manifest.json` 在 HEAD 里已长期被测试污染**（035 自 `f32f9b42`、036 自 `3074fa76` 起
   每个提交都在追加 pytest run_id）。本轮清洗只清当前 HEAD 的存量；历史提交里的污染不追改。
