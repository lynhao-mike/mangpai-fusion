# T-144 STATUS

- 状态：✅ **Done**（待中枢验收）
- 完成时间：2026-10-27
- 执行者：子代理（T-144）
- 任务卡：`tasks/T-144/PROMPT.md`
- 决策依据：`docs/adr/ADR-007-refactor-direction-adjudication.md` D7 / D8 / D9
- 简报：`tasks/T-144/BRIEF.md`

## 改了什么

| 文件 | 性质 |
|---|---|
| `engine/infrastructure/weight_repository.py` | 删两层 `except Exception`，改为 Fail-Closed；`load_school_weights` 委派 `weight_profile_service.load_expert_weight_profile_payload`；保留 `_DEFAULT_SCHOOL_WEIGHTS` 常量 |
| `tests/application/test_weight_repository_fail_closed.py` | **新增** 10 条（5 行为 + 1 常量留存 + 2 AST 静态守卫 + 1 常量无运行时引用 + 1 原始读取缺失） |
| `tests/governance/v5_frozen_importers.py` | **新增** 冻结白名单数据（85 条 + 上限 85 + 2 条不可解析白名单） |
| `tests/governance/test_v5_import_freeze.py` | **新增** 5 条 AST 静态门禁 |
| `tests/track_e_smoke/test_e_negatives_gate.py` | **新增** 1 条适配（`assert main() == 0`）；`test_e_negatives.py` 一行未改 |
| `pyproject.toml` | **仅** `[tool.pytest.ini_options].testpaths`：14 → 26 条 |

未改：`engine/api/facade.py`、`engine/facts/structure_check.py`、`engine/claims/`、`theory/_ir/`、`sources/`、`AGENTS.md`、`addopts`/`markers`/`filterwarnings`/`python_*`。无 git 破坏性操作。

**没有为让门禁变绿删改任何断言**：`tests/governance` 里 4 个文件 17 条预存在的红（解释器版本）**未纳入** `testpaths`，清单与根因见 BRIEF §4.1。

## 卡外环境处置（必须先看）

开工时 `.venv\Scripts\python.exe` 是 uv 生成的 trampoline，任何调用都失败：

```text
error: uv trampoline failed to spawn Python child process
  Caused by: permission denied (os error 5)
```

未删任何文件：旧 `.venv` 整体移到仓库外 `E:\Git hub\_venv-broken-backup-20261027`；
用同一基础解释器（CPython 3.11.16）重建 `.venv` 并复制旧 `Lib/site-packages`。
`.venv/` 在 `.gitignore` 内，git 无改动。

## 验收（中枢请亲自重跑）

```text
.venv\Scripts\python.exe -m pytest -q
→ 959 passed, 1 skipped, 1 warning in 89.18s   EXIT=0
  （T-144 前：227 passed, 1 skipped，collected 228；现 collected 960）

.venv\Scripts\python.exe -m tools.verify_baseline
→ pytest_passed 959 / pytest_failed 0 / pytest_rc 0 / audit_errors 0 /
  audit_rc 0 / relations_ok true / zuogong_charts 477 /
  zuogong_day_branch 346 / zuogong_rc 0        EXIT=0

.venv\Scripts\python.exe -m tools.tool_registry --check
→ tool registry check failed（20 条 UNINDEXED，tools/README.md 未收录）  EXIT=1
  **预存在红，非本卡引入**：本卡未新增/删除任何 tools/*.py，也未改 tools/README.md
```

## 三条自证

1. **权重 Fail-Closed**：`load_school_weights(source_path="engine/__no_such_weights__.yaml")`
   → `FileNotFoundError`；YAML 损坏 → `yaml.ParserError`；`domain="不存在的域"` → `ValueError`。
   正常路径仍返回 `{'ziping': 0.5, 'tiaohou_ditiansui': 0.25, 'blind': 0.25}`。
2. **v5 门禁**：临时 `_tmp_v5_probe.py` 写入 `import engine.v5` → 门禁 `1 failed, 4 passed`；
   删除后 → `5 passed`。命中基线 85（engine 34 / tools 8 / tests 43），白名单 85，上限 85。
3. **门禁扩容**：passed 227 → **959**，collected 228 → **960**，failed 0 → **0**，EXIT 0→0。

## 红灯清单

| 范围 | 条数 | 是否纳入门禁 | 定性 |
|---|---:|---|---|
| `tests/governance/test_structure_catalog.py` | 13 | 否 | 解释器版本：PEP 695，需 CPython ≥3.12（venv 为 3.11.16） |
| `tests/governance/test_structure_catalog_integrity.py` | 2 | 否 | 同上 |
| `tests/governance/test_static_isolation.py` | 2 | 否 | 同上（`ast.parse` 遇 PEP 695） |
| `tests/governance/test_school_registry.py` | 1 | 否 | 解释器版本：frozen+slots 下 property 赋值，实测 3.11/3.12 抛 TypeError、3.14 抛 FrozenInstanceError |
| `tests/r10`（4 文件之一） | 4 | 否（`--ignore`） | 第二阶段定性：疑快照漂移 |
| `tools.tool_registry --check` | 20 | — | tools/README.md 未收录，预存在 |

## 未完成与风险

1. `engine/application/fusion_engine_v2.py:77-80` 仍有 `.get("ziping", 0.42)` 一类隐性默认，
   与刚删掉的静默回落同类；不在本卡 File Scope，**未改**，建议单开卡按 D7 收口。
2. 基础设施层反向依赖应用层（`weight_repository` → `weight_profile_service`），
   是 D7「收口」的直接后果；现有分层门禁不禁止该方向，记录备查。
3. `AGENTS.md` §5「已知红灯」写的 `220 passed` 已过期（现 959），属保护区，**未改**，请中枢同步。
4. `META/baseline-v1.json` 未更新（未跑 `--save`）；其 `zuogong_day_branch=350` 与当前 346 的差异来自
   T-141 未提交的 `structure_check._crosses` 改动，非本卡。
5. 第二阶段建议（`tests/asof` 612 / `f09` 1183 / `v5` 130 / `v1_3_acceptance` 140 / `evaluation` 858
   归入独立慢速门禁；`r10` 先定性）见 BRIEF §5。

## Blockers

- 无阻塞。唯一环境债：`.venv` 是 3.11.16，而仓库已有 3.12+ 语法（PEP 695）与 3.13+/3.14 行为断言，
  导致治理层 4 个文件无法进门禁。升解释器需重装 `sxtwl` 等 3.11 专用二进制，超本卡范围。

## Execution Log

- 2026-10-27 14:54 开卡，读 PROMPT.md + ADR-007 D7/D8/D9；实测 `.venv` trampoline 损坏并重建 venv
- 2026-10-27 15:00 基线 `pytest -q` = 227 passed / 1 skipped（collected 228）
- 2026-10-27 15:05 ① 重写 `weight_repository.py` + 新增 10 条 fail-closed 测试，全绿
- 2026-10-27 15:10 ② 扫描 v5 命中 85 个文件，建白名单 + 5 条 AST 门禁；探针自证红→绿
- 2026-10-27 15:20 ③ 试跑候选套件：866 passed / 17 failed（全在 tests/governance，解释器版本）
- 2026-10-27 15:30 ③ 定稿 `testpaths` 26 条 + track_e 适配文件；全门禁 959 passed / 1 skipped
- 2026-10-27 15:40 跑三条验收命令，写 BRIEF/STATUS
