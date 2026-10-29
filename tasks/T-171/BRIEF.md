# T-171 BRIEF · Kill List 依赖审计（只读）

- 状态：✅ 交付（Worker W）
- 任务卡：`tasks/T-171/PROMPT.md`
- 产物：`tools/kill_list_dependency_audit.py`、`META/kill-list-dependency-audit-v1.{json,md}`、`tests/tools/test_kill_list_dependency_audit.py`
- 一句话：**6 个硬入口的事实层只碰了 `engine/asof` 一处；真正把 85% 锁死的是活代码 `engine/application` 与门禁测试，不是 481/0。**

---

## 1. 改动文件

**新建（本卡 File Scope 内）**

| 文件 | 说明 |
|---|---|
| `tools/kill_list_dependency_audit.py` | 只读审计：ast import 图 + 运行期 `sys.modules` 探针 + 四类裁决 + 分批顺序；唯一写入是 `META/` 两个产物 |
| `META/kill-list-dependency-audit-v1.json` | 机器可读：343 条目、入边/出边、分类、批次、运行期证据（2.3 MB） |
| `META/kill-list-dependency-audit-v1.md` | 人读报告：四类计数、481/0 清单、分批顺序、风险（137 KB） |
| `tests/tools/test_kill_list_dependency_audit.py` | 9 个确定性/不变量测试（不跑 481 盘探针） |
| `tasks/T-171/BRIEF.md` | 本文件 |
| `tasks/T-171/STATUS.md` | 追加 Execution Log 一行 |

**未改动**：`engine/**`、规则、既有测试、`docs/**`、`pyproject.toml`；没有移动/删除/重命名任何文件；没有 `git commit / push / checkout / stash / reset / clean`。

`git status --porcelain` 只看到 4 个新文件 + 1 个既有未跟踪 zip：

```text
?? META/kill-list-dependency-audit-v1.json
?? META/kill-list-dependency-audit-v1.md
?? mangpai-fusion-offline-04677d2c.zip   ← 本卡之前就在，未碰
?? tests/tools/test_kill_list_dependency_audit.py
?? tools/kill_list_dependency_audit.py
```

---

## 2. 原始输出

### 2.1 审计命令

```powershell
.venv\Scripts\python.exe -m tools.kill_list_dependency_audit
```

```text
Kill List 条目: 343（模块 340）
  安全归档: 194
  有引用（需先改）: 145
  尺子在用: 3
  不可判: 1
一动就破 481/0: 4
批次不变量: 通过 （检查 340 项，违规 0）
481/0 基线: engine_audit cases=481 fails=0 exit=0; relations_audit=全部通过 exit=0; ok=True
  入口 facts: 闭包 22 模块
  入口 api: 闭包 25 模块
  入口 cli: 闭包 26 模块
  入口 engine_audit: 闭包 26 模块
  入口 relations_audit: 闭包 26 模块
  入口 query_theory: 闭包 2 模块
written: META/kill-list-dependency-audit-v1.json
written: META/kill-list-dependency-audit-v1.md
json sha256: 28c43cb41e255d1d1f1740bf310102ff8c050340e0c48d2503f2fe0de6aca41a
```

### 2.2 回归

```powershell
.venv\Scripts\python.exe -m pytest -q
```

```text
1374 passed, 1 skipped, 1 warning in 128.44s (0:02:08)   [exit 0]
```

（全量复跑两次：131.12s / 128.44s，均 `1374 passed, 1 skipped`；skip 是既有的 `tests/tools/test_bundle_pii.py`（T-114 已知项），与本卡无关。1374 含本卡新增 9 个测试；单跑 `tests/tools/test_kill_list_dependency_audit.py` = 9 passed。）

### 2.3 确定性（两次运行字节一致）

```text
run1 json sha256 = 28c43cb41e255d1d1f1740bf310102ff8c050340e0c48d2503f2fe0de6aca41a
run2 json sha256 = 28c43cb41e255d1d1f1740bf310102ff8c050340e0c48d2503f2fe0de6aca41a  ← 同
md   sha256 = BFA563AE470334D9121ABC348B415795161D653B2D436CFC0777FD00A5B1BDA9
```

> 注意：`py_files_scanned=866` 是**工作树快照**。T-170 并行新增了 `tests/tools/test_golden_20_schema.py`，换快照重跑数字会变；同一快照内两次运行一致（已实测）。

### 2.4 四类计数（静态判据）

| 类 | 全部条目 | 仅 .py 模块 | 处置 |
|---|---:|---:|---|
| 安全归档 | 194 | 194 | 无 Kill List 外引用；批次 1 搬 / 被 importer 顺延的进 2c |
| 有引用（需先改） | 145 | 143 | 先改引用方再归档 |
| 尺子在用 | 3 | 3 | 不得归档（要动先改尺子，需人类批准） |
| 不可判 | 1 | 0 | `plans/`（任务卡要求只列不删） |

按依赖顺延后的批次：

| 批 | 内容 | 条目数 |
|---|---|---:|
| 1 | 安全归档（现在就能搬） | **130** |
| 2a | 只被门禁外测试引用 | 37 |
| 2b | 被活代码 / 门禁测试 / 字符串引用 | 108 |
| 2c | 顺序顺延（本身无引用，要跟 importer 一起搬） | 64 |
| 3 | 不可判 | 1 |
| — | 尺子在用（保留） | 3 |

批号满足「先 importer 后 imported」不变量：脚本自检 340 项 0 违规（`summary.invariants.ok=true`）。

### 2.5 关键入边（带行号，全部可在 JSON `items[].imported_by` 复核）

| 入边 | 证据 |
|---|---|
| `engine/facts/chart_facts.py:463` → `engine/asof/qiyun_calculator` | `from engine.asof.qiyun_calculator import calc_qiyun`（函数内**延迟 import**；`--pillars` 不触发，birth/大运路径触发） |
| `engine/facts/chart_facts.py:36/484-486` → `engine/asof` | `QiyunVariant(..., "engine/asof/qiyun_calculator.py")` 出处字符串 + `engine.asof` 包导入 |
| `tests/api/test_facade_zuogong_fields.py:18` → `engine/claims/condition_ir/atoms.py` | `from engine.claims.condition_ir.atoms import build_context, zuogong`（**尺子唯一一处 import Kill List**） |
| `tests/test_project_metadata.py:159-162` → `engine/v5/{domain_report_view,domain_capability_metrics,high_risk_gate,domain_feedback}.py` | `assert (ROOT / rel).is_file()`，归档即红 |
| `tests/test_production_entrypoints_unchanged.py:57` → `theory/production/claim-rules-v1.yaml` | 断言该 yaml 的 sha256 |
| `engine/application/governance_shadow_types.py`（26 条）、`governance_shadow_runner.py`（17 条）→ `engine/governance/*` | 活引擎代码 import 旧治理层 |
| `tools/as_of_session_cli.py`（21 条）→ `engine/asof/*` | 活工具 import 旧 as-of 层 |
| `tools/render_report.py`（19 条）→ `engine/v5/*` | 活工具生成报告仍走 v5 |
| `tests/claims/*` → `engine/v5/{duan,gao,ren,yang,ziping}_runner` + `engine/claims/rule_loader.py` | 门禁测试直接测 v5 runner（改/归档测试即可解） |

### 2.6 「一动就破 481/0」的 4 个模块

判据：① 在 `cli`/`engine_audit`/`relations_audit` 闭包内；② 运行期 `sys.modules` 实际加载。缺一不列。

| 模块 | 最短 import 链 |
|---|---|
| `engine/asof/qiyun_calculator.py` | `engine/facts/__init__.py` ← `engine/facts/chart_facts.py` ← `engine/asof/qiyun_calculator.py` |
| `engine/asof/__init__.py` | `engine/facts/__init__.py` ← `engine/facts/chart_facts.py` ← `engine/asof/__init__.py` |
| `engine/asof/daiyun_context.py` | `… ← engine/asof/__init__.py ← engine/asof/daiyun_context.py` |
| `engine/asof/natal_capacity.py` | `… ← engine/asof/__init__.py ← engine/asof/natal_capacity.py` |

现场基线：`tools.engine_audit` 481 盘 / 0 错（exit 0）；`tools.relations_audit` 全部通过（exit 0）。

---

## 3. 未完成与风险

1. **动态 import 只做到「证据」没有「执行路径证明」**：`importlib.import_module` / `mock.patch` 目标按字符串收集。
   - 2 条门禁动态引用：`engine/decision/chart_prototype.py`、`engine/decision/routing_holdout.py`（`tests/decision/*` 用 `importlib` + `pytest.fail`），已判「有引用（需先改）」而不是「安全」。
   - 其它动态引用（若有）一律「不可判」，未按「没人用」归档。
2. **字符串引用按最保守口径**：`tests/governance/v5_frozen_importers.py` 是 **import 白名单数据**（51 条 v5 路径），列的是「谁 import 了 v5」，不等于运行时读取。本审计把它计为引用，导致约 12 个 v5 模块的「有引用」证据偏保守，人工复核后可降级。反例（出处字符串如 `"engine/asof/qiyun_calculator.py"`）同样会计入，已在 `limitations` 写明。
3. **PEP 695 两个文件用正则兜底**（`engine/governance/structure_catalog_models.py`、`structure_catalog_types.py`，本解释器 3.11 无法 `ast.parse`）。它们的出边是近似值，`items[].parse_mode="regex"` 已标注。
4. **query_theory 无运行期探针**：它会写 `theory/_light_index.json` 缓存，违反本卡只读约束；其静态闭包只有 `tools/theory_content.py`（2 个模块）。
5. **反射取包不在覆盖内**：`getattr(engine, "v5")` 这类写法静态图看不见。
6. **共享工作树**：T-170 并行写文件，审计数字只对同一快照确定；JSON 只对快照内两次运行字节一致。
7. **未跑 `tools.verify_baseline --compare`**：那会再跑一遍全量 pytest + 481 盘，超出本卡「只读 + 自测两条命令」的范围；481/0 已由审计内嵌探针现场复核。
8. **测试夹具**：`tests/*/conftest.py` 在扫描范围内，但 pytest 插件（`-p`）与运行时生成的临时目录不在图内。

**Blockers**：无。

---

## 4. 下游须知

### 4.1 第一批可安全归档（130）

- **117 个脚手架测试**：`tests/asof` 41、`tests/evaluation` 33、`tests/v5` 20、`tests/f09` 18、`tests/governance` 5（`test_school_registry.py`、`test_static_isolation.py`、`test_structure_catalog*.py`、`static_isolation_content.py` —— 都是 pyproject 已注明的红/未入门禁文件）。
- **9 个引擎叶子**：`engine/asof/{blind_baseline,blind_baseline_archive,career_path_classifier,hypothesis_state,structural_track}.py`、`engine/governance/structure_catalog{,_loader_values,_models,_types}.py`（只被同一批或已废测试引用）。
- **4 个已判死工具**：`tools/m2y395_{direction,real_direction,real_score,score}.py`。
- 顺序：**先 tests、再 engine 叶子**（`batches[0].items` 已是拓扑序：importer 在前）。

### 4.2 现在动不了、必须保留

| 模块 | 原因 | 解绑动作 |
|---|---|---|
| `engine/claims/condition_ir/{__init__,atoms,ir}.py` | 尺子 `tests/api/test_facade_zuogong_fields.py:18` 直接 import | 改尺子（需人类批准）或把 `build_context/zuogong` 迁到非 Kill List 层 |
| `engine/asof/{__init__,qiyun_calculator,daiyun_context,natal_capacity}.py` | `engine/facts/chart_facts.py:463` 延迟 import，481/0 运行期实际加载 | **先**把 `calc_qiyun` 从 `engine/asof` 抽到 `engine/facts` 或独立包，**再**归档 asof |
| `tests/governance/` 在 testpaths 的 14 个测试 | 归档=改门禁 | 显式改 `pyproject.toml` testpaths 或目录（需人类批准） |
| `engine/v5/{duan,gao,ren,yang,ziping}_runner.py` 等 | `tests/claims/*` 门禁测试直接测它们 | 同批改/归档 `tests/claims/test_*_runner*.py` |
| `engine/governance/*`、`engine/energy/*`、`engine/picture/*`、`engine/yingqi/*`、`engine/decision/*` | `engine/application/*`（`governance_shadow_runner/types`、`domain_analyzers`、`pipeline_runner`、`integration`、`dual_engine_adapter`）与 `tools/*` 仍在 import | 先改 `engine/application` 与相关 tools，再按批 2 搬 |

### 4.3 建议执行顺序（不在本卡范围，仅建议）

1. 搬批 1（130 个）→ 立刻重跑 `pytest -q` + 本审计。
2. 改 `engine/application/*` 对 `engine/governance|energy|picture|yingqi|decision` 的依赖 → 搬批 2b 对应模块。
3. 处理 `tests/claims`（v5 runner）与 `tests/test_project_metadata.py`（v5 路径断言）、`tests/test_production_entrypoints_unchanged.py`（claim yaml sha256）→ 搬对应模块。
4. 解 `engine/facts/chart_facts.py:463` 的 asof 依赖 → 搬 `engine/asof`（481/0 唯一真正的硬耦合）。
5. 全程禁止 `rm`；只移到 `archive/`，每批后跑 `python -m tools.verify_baseline --compare`。

### 4.4 复现

```powershell
.venv\Scripts\python.exe -m tools.kill_list_dependency_audit            # 写 META 产物（含 481 盘基线探针）
.venv\Scripts\python.exe -m tools.kill_list_dependency_audit --check    # 只打印计数
.venv\Scripts\python.exe -m tools.kill_list_dependency_audit --no-probes # 纯静态图（秒级）
.venv\Scripts\python.exe -m pytest -q
```

