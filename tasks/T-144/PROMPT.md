# T-144 · 工程债三件：权重 Fail-Closed + v5 AST 门禁 + 测试门禁扩容

- 状态：🔵 Ready for Execution
- 优先级：P1
- 创建：2026-10-27（中枢）
- 决策依据：ADR-007 D7 / D8 / D9
- **本卡与 T-140 / T-141 / T-142 文件不重叠，可并行**

## 1. 三件事

### ① 权重静默回落 → Fail-Closed（D7）

仓库里有两套读 `engine/expert-weights.yaml` 的实现：

| 文件 | 行为 |
|---|---|
| `engine/application/weight_profile_service.py:70` | **严格**，读失败抛错（正确） |
| `engine/infrastructure/weight_repository.py:24,45` | 两层 `except Exception` **静默回落**到 `_DEFAULT_SCHOOL_WEIGHTS` |

**实测危害**：
```
正常读配置:        {'ziping': 0.5,  'tiaohou_ditiansui': 0.25, 'blind': 0.25}
指向不存在文件后:  {'ziping': 0.42, 'tiaohou_ditiansui': 0.32, 'blind': 0.26}
```
权重决定「哪一派的话更算数」。静默回落 = 裁决配比可能在无人知情下变成出厂值，**报告上看不出任何异常**。

**要求**：
- 删除 `weight_repository.py` 里的两层 `except Exception`，文件缺失 / YAML 损坏 / 请求的 domain 不存在 → **直接抛错**。
- **保留常量名 `_DEFAULT_SCHOOL_WEIGHTS`**：`tests/test_production_entrypoints_unchanged.py:10,50-52` 有导入与相等断言，不得破坏。
- 生产读配置统一收口到 `weight_profile_service.py`。

### ② v5 引用升级为 AST 级静态门禁（D9）

ADR-006 决定 v5 冻结、白名单只减不增。但「写进 AGENTS.md」挡不住。

**要求**：新增门禁测试（放在 `tests/api/` 或 `tests/governance/`，必须在 `testpaths` 内），做两件事：
- 扫描全仓 `.py`（排除 `.venv/`、`.worktrees/`、`_archive/`）里的 `import engine.v5` / `from engine import v5`；
- 断言命中文件集合 ⊆ 冻结白名单；白名单条目数不得增加（新增即红）。

可用范本：`tests/governance/static_isolation_scanner.py`、`tests/f09/test_production_isolation.py`。

**先测准基线**：跑一遍数出当前真实命中数（中枢实测约 97–98 个文件：engine 36 / tools 8–12 / tests 53），白名单照这个快照建。

### ③ 测试门禁分两阶段扩容（D8）

现状：全仓 **303 个 `test_*.py`**，`pyproject.toml` 的 `testpaths` 只覆盖 **14 个**（`tests/facts`、`tests/api`、`tests/predicates` + 6 个 `tests/tools` 文件），`addopts` 又 `--ignore` 了 4 个目录。**289 个（95%）从不参与验收。**

**第一阶段（本卡做）**：把与现行架构直接相关的套件纳入 `testpaths`：
- `tests/claims`、`tests/decision`、`tests/governance`、`tests/application`、`tests/features`
- `tests/tools` 全部（注意 `test_bundle_pii.py` 现在靠 `skip` 遮着，见 T-114）
- 根目录保护测试：`tests/test_production_entrypoints_unchanged.py`、`tests/test_project_metadata.py`、`tests/test_error_policy.py`

**第二阶段（本卡不做，写进 BRIEF 建议）**：`tests/asof`、`tests/f09`、`tests/v5`、`tests/v1_3_acceptance` 归入独立慢速门禁；`tests/r10` 的 4 个失败先查明是快照漂移还是逻辑回归。

**关于 `tests/track_e_smoke/test_e_negatives.py`**：它不是假测试。直接跑 `python tests/track_e_smoke/test_e_negatives.py` 实测 `PASS=8 FAIL=0 EXIT=0`。它第 19 行自述「不依赖 pytest，纯 stdlib」，用 `_Reporter.add()` 计数并以退出码表达结果。**只需要包一层**：
```python
def test_track_e_negatives():
    assert main() == 0
```
就能进 pytest 门禁。**不要重写它的八条断言。**

## 2. 硬约束

- **不许为让门禁变绿而删改任何断言。** 若纳入新测试后出现红，**如实报告红色清单**，由中枢决定是修实现还是该测试本身过期。你可以先分两批提交：只用「本来就绿」的套件扩门禁，红的列清单。
- 不许改 `theory/_ir/`、`sources/`。
- 不许 git 破坏性操作。

## 3. File Scope

- `engine/infrastructure/weight_repository.py`
- `pyproject.toml` 的 `[tool.pytest.ini_options]`（**仅** `testpaths` 与 `addopts`；不得改其它配置）
- 新增门禁测试文件
- 对应测试

**禁止**：改 `engine/api/facade.py`、`engine/facts/structure_check.py`、`engine/claims/`（其它任务在改）。

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m tools.verify_baseline
.venv\Scripts\python.exe -m tools.tool_registry --check
```

**必须自证**：
1. 权重：把配置路径指向不存在的文件，`load_school_weights()` **抛错**而非返回默认值（贴输出）。
2. v5 门禁：故意在临时文件里加一行 `import engine.v5`，pytest **变红**；删掉后恢复绿。
3. 门禁扩容：`pytest -q` 的 collected 数与 passed 数从 220 增加到多少；若有红，列出清单与原因。

## 5. 回报格式

三件事各自改了什么；权重抛错的自证输出；v5 门禁的命中文件数与白名单规模、以及「新增即红」的验证；门禁扩容后 passed/collected 数；**所有红灯清单**（若有）；三条验收命令的数字与退出码。
