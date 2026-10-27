# T-144 BRIEF · 工程债三件：权重 Fail-Closed + v5 AST 门禁 + 测试门禁扩容

- 状态：✅ **Done**（待中枢验收）
- 完成时间：2026-10-27
- 执行者：子代理（T-144）
- 任务卡：`tasks/T-144/PROMPT.md`
- 决策依据：`docs/adr/ADR-007-refactor-direction-adjudication.md` D7 / D8 / D9

## 0. ⚠️ 先说一件卡外的事实：`.venv\Scripts\python.exe` 开工时是坏的

开卡第一条命令就失败，**与 T-144 改动无关**，但不修就一条验收命令也跑不了：

```text
.venv\Scripts\python.exe -m pytest -q
→ error: uv trampoline failed to spawn Python child process
  Caused by: permission denied (os error 5)
```

- 该 `python.exe` 是 **uv 生成的 trampoline**（47 KB），指向
  `…\uv\python\cpython-3.11-windows-x86_64-none`；基础解释器本身可用，但 trampoline 在
  这个路径下 spawn 子进程恒失败（`cmd`、沙箱内外、绝对路径调用都一样）。
- 处置：**不删任何东西**——把旧 `.venv` 整体改名为
  `E:\Git hub\_venv-broken-backup-20261027`（移到仓库外，不进 git），
  用同一个基础解释器新建 `.venv`（3.11.16）并把旧 `Lib/site-packages` 全量复制进去。
  现在 `.venv\Scripts\python.exe` 正常工作，`pytest 9.1.1 / yaml / lunar_python / sxtwl` 齐全。
- `.venv/` 在 `.gitignore` 内，**未产生任何 git 改动**。

## 1. 三件事各自改了什么

| # | 文件 | 性质 |
|---|---|---|
| ① | `engine/infrastructure/weight_repository.py` | **重写 66 行**：删掉两层 `except Exception`；`load_school_weights` 改为委派严格实现 `weight_profile_service.load_expert_weight_profile_payload`；保留 `_DEFAULT_SCHOOL_WEIGHTS` 常量（不再被任何函数引用） |
| ① | `tests/application/test_weight_repository_fail_closed.py` | **新增 10 条**：缺失文件 / YAML 损坏 / domain 缺失 / 缺流派 / 原始读取缺失 5 条行为断言 + 常量留存 + 2 条 AST 静态守卫 + 「常量不得在函数体内出现」 |
| ② | `tests/governance/v5_frozen_importers.py` | **新增**：85 条冻结白名单快照 + 上限 85 + 2 个「不可解析文件」白名单 |
| ② | `tests/governance/test_v5_import_freeze.py` | **新增 5 条**：命中 ⊆ 白名单 / 条目数不增 / 白名单文件仍存在 / 无新增免检盲区 / 扫描器自检（含 `.venv` 排除与别名导入） |
| ③ | `pyproject.toml` | **仅 `[tool.pytest.ini_options].testpaths`**：14 → 26 条（8 个目录 + 18 个单文件）。`addopts`、`markers`、`filterwarnings`、`python_*` 全部未动 |
| ③ | `tests/track_e_smoke/test_e_negatives_gate.py` | **新增 1 条**：`assert main() == 0`。**`test_e_negatives.py` 一行未改** |

**未改**：`engine/api/facade.py`、`engine/facts/structure_check.py`、`engine/claims/`、
`theory/_ir/`、`sources/`、`AGENTS.md`、`templates/`。无任何 git 破坏性操作。

### ③ 的一个卡外发现（必须说明）

卡里建议「在 `test_e_negatives.py` 里包一层 `def test_track_e_negatives(): assert main() == 0`」。
**直接这么做会让门禁爆 8 个 error**：该文件的 8 个函数都叫 `test_E00x(...)`，形参是
`(rep: _Reporter, tmp: Path)` 这种普通参数而不是 fixture；一旦该文件进 `testpaths`，
pytest 会按 `python_functions = ["test_*"]` 逐个收走并报 `fixture 'rep' not found`
（这正是 T-131 那份「假测试」误判的机制来源）。
所以改为**同目录新开一个适配文件**调用对方唯一公共入口 `main()`——8 条断言零改动，
结果等价。`pyproject.toml` 里也只写了适配文件路径，不写目录（否则会把原文件一并收走）。

## 2. 自证输出

### 2.1 权重 Fail-Closed（配置路径指向不存在的文件 → 抛错）

```text
[正常]     {'blind': 0.25, 'ziping': 0.5, 'tiaohou_ditiansui': 0.25}      ← 事业域真实权重
[缺失文件] RAISED FileNotFoundError -> [Errno 2] No such file or directory:
           'E:\\Git hub\\mangpai-fusion\\engine\\__no_such_weigh…'
[YAML损坏] RAISED ParserError -> while parsing a flow sequence …
[domain缺失] RAISED ValueError -> expert-weights.yaml 未定义权重 domain='不存在的域'；
           已知 domain：['事业', '健康', '婚姻', '学业', '性格', '财运']
```

对照卡里的实测危害：旧实现这三条全部返回 `{'ziping': 0.42, 'tiaohou_ditiansui': 0.32, 'blind': 0.26}`。

### 2.2 v5 门禁（临时加一行 → 红；删掉 → 绿）

```text
$ printf 'import engine.v5\n' > _tmp_v5_probe.py
$ pytest tests/governance/test_v5_import_freeze.py -q
F....
FAILED test_v5_importers_are_within_frozen_whitelist
E   AssertionError: 检测到白名单外的 engine.v5 引用 —— ADR-006 已冻结 v5，禁止新增依赖：
E       _tmp_v5_probe.py
E    修法：删掉该 import…；不得把新文件加进 tests/governance/v5_frozen_importers.py。
1 failed, 4 passed

$ rm _tmp_v5_probe.py && pytest tests/governance/test_v5_import_freeze.py -q
5 passed
```

**基线命中数（实测，AST 级）**：`85` 个文件 —— engine 34 / tools 8 / tests 43。
白名单规模 = 85 = 命中数，上限 `FROZEN_IMPORTER_COUNT_MAX = 85`，**新增即红**（三条同时挡：
集合 ⊆ 白名单、条目数 ≤ 85、扫描器自检必须真能抓到）。

> 与卡里「约 97–98」的差异：那 97–98 里含 `pytest-of-Administrator/pytest-5x/…/bad_labels.py`
> 这类 **pytest tmp_path 生成的临时文件**（随时新增，收进白名单会让门禁抖动）与 `.omo/` 产物目录，
> 另有 3 个带 BOM 的测试文件（`test_production_service.py` / `test_project_metadata.py` /
> `tests/v1_3_acceptance/test_h{1,2}_*.py`）用 `encoding="utf-8"` 读会解析失败——
> 门禁改用 `utf-8-sig` 后它们正常解析，且都不含 v5 引用。排除规则：点开头目录、`pytest-of-*`、
> `_archive`、`__pycache__`、`node_modules`。

### 2.3 门禁扩容

| 指标 | T-144 前 | T-144 后 |
|---|---:|---:|
| `pytest -q` collected | 228 | **960** |
| passed | 227 | **959** |
| skipped | 1 | 1（`test_bundle_pii.py`，T-114 已知） |
| failed | 0 | **0** |
| 退出码 | 0 | **0** |
| `testpaths` 条目 | 14 | 26 |
| 覆盖 `test_*.py` 文件 | 14 | 87（全仓 307） |

## 3. 验收命令（中枢请亲自重跑）

```text
.venv\Scripts\python.exe -m pytest -q
→ 959 passed, 1 skipped, 1 warning in 89.18s   EXIT=0

.venv\Scripts\python.exe -m tools.verify_baseline
→ pytest_passed 959 / pytest_failed 0 / pytest_rc 0 / audit_errors 0 / audit_rc 0 /
  relations_ok true / zuogong_charts 477 / zuogong_day_branch 346 / zuogong_rc 0   EXIT=0

.venv\Scripts\python.exe -m tools.tool_registry --check
→ 【红】tool registry check failed … EXIT=1   ← 预存在，非本卡引入，见 §5.3
```

> 复现提示：`pytest` 不要放后台跑。后台运行时 sandbox 的 safe-delete 守卫会拦截 pytest
> 清理 `%TEMP%\pytest-of-Administrator\...`（单次 410 个文件），进程被截断、`EXIT=1`
> 且不打印汇总行——那是环境假红，前台跑即为 `EXIT=0`。

## 4. 红灯清单（本卡**没有**为了变绿删改任何断言）

### 4.1 已测出的预存在红：`tests/governance` 4 个文件 17 条 —— **未纳入 testpaths**

```text
tests/governance/test_structure_catalog.py              13 条   解释器版本（PEP 695）
tests/governance/test_structure_catalog_integrity.py     2 条   解释器版本（PEP 695）
tests/governance/test_static_isolation.py                2 条   解释器版本（PEP 695）
tests/governance/test_school_registry.py                 1 条   解释器版本（frozen+slots）
```

根因（已实测，不是猜测）：

1. **PEP 695**：`engine/governance/structure_catalog_types.py:21` 用 `type X = …`、
   `structure_catalog_models.py:178` 用 `def _require_tuple[T](…)`，**3.12+ 才支持**。
   `.venv` 是 **CPython 3.11.16**，`ast.parse` 与 import 都直接 SyntaxError。
2. **frozen + slots + property 赋值**：`test_school_registry.py` 断言
   `pytest.raises(FrozenInstanceError)`，实测：

   ```text
   3.11.16 → TypeError : super(type, obj): obj must be an instance or subtype of type
   3.12.14 → TypeError : super(type, obj): obj must be an instance or subtype of type
   3.14.7  → FrozenInstanceError : cannot assign to field 'pid'
   ```

   即该断言要 **CPython ≥ 3.13/3.14** 才成立。

**判断**：四条都不是本卡改出来的，也不是逻辑回归，是**仓库已要求 Python ≥ 3.12（这一条还要求 ≥3.13），
而 `.venv` 停在 3.11.16**。处理这类红的正确姿势是升解释器，**不是**改断言，也不是永久屏蔽。
本卡按卡的指示「只用本来就绿的套件扩门禁」，故 `testpaths` 里逐个列出 14 个绿的治理层文件，
不写目录。**升 venv 到 3.12/3.14 后请把这 4 个文件补进 `testpaths`**（升解释器涉及 `sxtwl`
等 3.11 专用 `.pyd`，超本卡范围，未擅自做）。

### 4.2 `tests/r10`：4 条红（第二阶段再定性，本卡未纳入）

```text
tests/r10: 4 failed, 60 passed  （42.96s）
FAILED test_falsifier_career_information_is_not_thinner_than_r6
FAILED test_career_l7_text_is_serialized_verbatim
FAILED test_falsifier_career_l7_structures_all_r6_school_evidence_losslessly
FAILED test_falsifier_career_report_columns_and_conflict_disappear_without_l7
```

四条都在 `test_r10_ziping_career_acceptance.py`，名字全是 `falsifier_*` / 与 L7 结构相关——
像**快照漂移**（r10 冻结时的输出结构已变）而非逻辑回归，但本卡未做定性，留第二阶段。

## 5. 第二阶段建议（卡说不做，只写建议）

1. **慢速门禁**：`tests/asof`（612 例）、`tests/f09`（1183 例）、`tests/v5`（130 例）、
   `tests/v1_3_acceptance`（140 例）、外加 `tests/evaluation`（858 例，现被 `--ignore`）
   建议统一挂到独立命令（如 `pytest -m slow` 或单独脚本 + CI 定时任务），**不删、不阻塞日常**。
   这五个目录合计 2923 例，是日常门禁的 3 倍体量，硬塞进 `testpaths` 会让单次验收从 90s 涨到数分钟。
2. **`tests/r10`**：先判「快照漂移 vs 逻辑回归」。做法：跑 `test_r10_ziping_career_acceptance.py`
   的四个 falsifier，把实际 L7 结构与冻结快照 diff；如果只是字段增减，改快照；如果是 L7 结构
   真的丢了证据，那是逻辑回归，要修实现。
3. **`AGENTS.md` §5 的「已知红灯」已过期**：那里写「默认门禁恢复为 220 passed, 1 skipped」，
   现为 959 passed / 1 skipped；且「只有 14 个 path 有效」的描述也不再成立。
   `AGENTS.md` 属保护区（仅中枢可写），**我没有改**，请中枢同步。
4. `tools/blind_candidate_pick.py` 仍在打印 `python .workbuddy-ai/make_bundle_v2.py …`（T-114 遗留），
   与本卡无关，仅提示。

## 6. 未完成与风险

1. **`engine/application/fusion_engine_v2.py:77-80` 还有一层隐性默认**：
   `weights.get("ziping", 0.42)` / `weights.get("tiaohou_ditiansui", 0.32)` / `weights.get("blind", 0.26)`。
   `load_school_weights` 现在恒返回三键，所以这三处目前是死代码；但**它和刚删掉的静默回落是同一类后门**，
   任何人再动 `load_school_weights` 的返回形状就会复活出厂值。该文件不在本卡 File Scope，**未改**，
   建议单开一卡按 D7 一并收口（把 `.get` 换成 `[...]` 或断言三键齐全）。
2. **`load_expert_weights()` 保留了「原始 mapping」语义**（`minimal_learning_loop` 要靠它回写整份 YAML）。
   它已改为 Fail-Closed，但**不做 schema 校验**（校验在 `load_school_weights` 那条路上）。
   即「学习回路读到的文件」与「runtime 用的权重」走两次解析，理论上存在读到不同版本的窗口
   （同一进程内极小）。若中枢要求彻底单点，可让学习回路也走 payload。
3. **基础设施层反向依赖应用层**：`weight_repository`（infrastructure）现在 import
   `engine.application.weight_profile_service`。这是 D7「生产读配置统一收口到严格实现」的直接后果，
   现有 `tests/test_architecture_dependencies.py` 只禁止 domain/governance/application 向外，
   **不禁止 infrastructure → application**，所以门禁是绿的；但这属于分层例外，记录在此备查。
   （`engine/application/__init__.py` 是懒加载，无循环导入、也不会拉进 `engine.f09`，
   `tests/f09/test_production_isolation.py` 三条断言仍绿。）
4. **基线尺子口径**：`tools/verify_baseline --compare` 只校验 `zuogong_charts`，不校验
   `zuogong_day_branch`（T-141 BRIEF §7 已指出）。`META/baseline-v1.json` 存的 `pytest_passed`
   还是 220，本卡把真实值拉到 959，但**没有 `--save`**（写基线是中枢动作，且当前 `zuogong_day_branch`
   346 vs 存的 350 是 T-141 的 `_crosses` 改动，见下）。
5. **`zuogong_day_branch` 350 → 346 与 T-144 无关**：本卡 diff 只碰 `weight_repository.py` +
   `pyproject.toml` + 4 个新测试；工作区里同时挂着 **T-141 未提交的 `structure_check._crosses` 改动**
   （`git status` 可见），`tools/zuogong_probe.py` 走 `engine.api.analyze_facts` → `engine.facts`，
   正是 T-141 的改动链。T-141 BRIEF 已自行报告「477→477，day_branch 350→346，请中枢裁决」。

## 7. 下游须知

- **新增引用 `engine.v5` 会立刻让日常门禁变红**（`tests/governance/test_v5_import_freeze.py`）。
  要加白名单 = 同时改 `FROZEN_V5_IMPORTERS` 与 `FROZEN_IMPORTER_COUNT_MAX`，**两个都动才能过**，
  是有意设计的摩擦（ADR-006：只减不增）。
- **新增 `tests/` 下的测试文件默认不会被跑**：`testpaths` 是显式清单。想让新测试进日常门禁，
  要么放进上面 8 个目录之一，要么显式加进 `testpaths`。
- **不要把 `tests/governance` 目录整体写进 `testpaths`**，否则会重新拉起 §4.1 的 17 条解释器版本红。
- 权重路径一旦配错，现在会**大声炸**（`FileNotFoundError` / `ParserError` / `ValueError`），
  不再静默给 `{0.42, 0.32, 0.26}`。下游若在测试里 mock 过权重文件缺失，需要改成期待抛错。
